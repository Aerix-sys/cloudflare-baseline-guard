"""Generate deterministic, offline evidence for the portfolio demo."""

import argparse
from pathlib import Path

from .web import audit


MODES = ("secure", "insecure", "ddos_secure", "ddos_insecure")


def generate(output: Path) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    paths = []
    for mode in MODES:
        result = audit(mode)
        path = output / f"{mode}.md"
        path.write_text(result["report"], encoding="utf-8")
        paths.append(path)
    return paths


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate offline demo reports")
    parser.add_argument("--output", type=Path, default=Path("demo-reports"))
    args = parser.parse_args(argv)
    for path in generate(args.output):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
