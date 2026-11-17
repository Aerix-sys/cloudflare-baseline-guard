"""CLI for a small, read-only Cloudflare zone audit."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


SETTING_IDS = ("always_use_https", "ssl", "min_tls_version", "tls_1_3")


def fetch_settings(zone_id: str, token: str) -> dict:
    if not zone_id or not token:
        raise ValueError("zone ID and API token are required")
    settings = {}
    for setting_id in SETTING_IDS:
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/settings/{setting_id}"
        request = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.load(response)
        if payload.get("success") is not True or not isinstance(payload.get("result"), dict):
            raise ValueError(f"Cloudflare returned an invalid result for {setting_id}")
        result = payload["result"]
        if result.get("id") != setting_id or "value" not in result:
            raise ValueError(f"Cloudflare returned an unexpected setting for {setting_id}")
        settings[setting_id] = result["value"]
    return settings


def evaluate(settings: dict) -> list[dict]:
    version = settings.get("min_tls_version")
    try:
        tls_ok = float(version) >= 1.2
    except (TypeError, ValueError):
        tls_ok = False
    checks = (
        ("HTTPS redirect", "always_use_https", settings.get("always_use_https") == "on", "on"),
        ("Origin TLS", "ssl", settings.get("ssl") == "strict", "strict"),
        ("Minimum TLS", "min_tls_version", tls_ok, "1.2 or newer"),
        ("TLS 1.3", "tls_1_3", settings.get("tls_1_3") == "on", "on (without 0-RTT)"),
    )
    return [
        {"check": name, "setting": key, "status": "PASS" if passed else "FAIL", "expected": expected,
         "actual": settings.get(key, "missing")}
        for name, key, passed, expected in checks
    ]


def markdown_report(results: list[dict], source: str) -> str:
    lines = ["# Cloudflare security baseline", "", f"Source: `{source}`", "",
             "| Check | Status | Expected | Actual |", "|---|---|---|---|"]
    for result in results:
        cells = [result[key] for key in ("check", "status", "expected", "actual")]
        safe = [str(cell).replace("|", "\\|").replace("\n", " ") for cell in cells]
        lines.append("| " + " | ".join(safe) + " |")
    lines += ["", f"Result: **{sum(r['status'] == 'PASS' for r in results)}/{len(results)} passed**", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Audit Cloudflare zone settings without changing them")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--fixture", type=Path, help="JSON file with setting IDs as keys")
    source.add_argument("--zone-id", help="Cloudflare zone ID; requires CF_API_TOKEN")
    parser.add_argument("--report", type=Path, help="Write a Markdown report")
    args = parser.parse_args(argv)
    try:
        if args.fixture:
            settings = json.loads(args.fixture.read_text(encoding="utf-8"))
            if not isinstance(settings, dict):
                raise ValueError("fixture must be a JSON object")
            source_name = args.fixture.name
        else:
            token = os.environ.get("CF_API_TOKEN", "")
            settings = fetch_settings(args.zone_id, token)
            source_name = "Cloudflare API"
        report = markdown_report(evaluate(settings), source_name)
        print(report)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(report, encoding="utf-8")
        return 0 if all(r["status"] == "PASS" for r in evaluate(settings)) else 1
    except (OSError, ValueError, json.JSONDecodeError, urllib.error.URLError) as error:
        print(f"Audit error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
