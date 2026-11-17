# Case study: Cloudflare Baseline Guard

## Problem

A team can enable Cloudflare but still leave individual controls inconsistent. Reviewers need a repeatable way to see which settings match a chosen security baseline and why a DDoS design needs more than an on/off switch.

## Goal and scope

Build a small, low-cost DevSecOps portfolio project using Python, GitHub Actions, and Cloudflare APIs. The deliverable is a local dashboard, a CLI, offline demonstration data, automated tests, and a read-only live audit path. No real domain is needed for the demonstration.

## Architecture

```mermaid
flowchart LR
    U[Browser on localhost] -->|same-origin POST + CSRF token| W[Python dashboard]
    W --> P[Policy evaluator]
    P --> F[Offline fixtures]
    W -->|optional GET requests| C[Cloudflare zone, DNS, WAF and bot APIs]
    E[Scoped token in environment] --> W
    G[GitHub Actions] --> T[Tests + offline reports]
```

The local server binds to `127.0.0.1`. The Cloudflare token stays in the server environment. The browser receives findings, never the token. Live TLS mode reads four zone settings. Live DDoS mode reads zone, DNS, rate limiting, and bot configuration. A zone-scoped token needs the corresponding read permissions; neither mode updates a zone.

## Security decisions

| Decision | Reason | Evidence |
|---|---|---|
| Fail closed for missing or malformed settings | An incomplete API response must not look compliant | Unit tests and exit code 2 |
| No live credentials in PR CI | Pull request code must not receive the token | Fixture-only `verify` job |
| Manual opt-in live job | Prevent an unconfigured manual run from failing the portfolio pipeline | `workflow_dispatch` boolean input |
| Local-only UI with Host, Origin and CSRF checks | Avoid accidental cross-site use of the local audit endpoint | HTTP integration test |
| Bound local work | Limit accidental overload of the small process | Body cap, socket timeout, rate limit, two audit slots |

## DDoS design

The DDoS page provides both an architecture exercise and a live zone audit. The sample profiles check five assertions: zone activation, proxied web DNS, origin isolation, edge mitigation, and a sensitive-path rate limit. A passing sample does not prove a real site is protected. The live audit checks zone, DNS, rate limiting and bot settings via API, while origin firewall/Tunnel configuration and normal-traffic tests still require manual evidence. See [DDOS.md](DDOS.md).

## Validation

Run `PYTHONPATH=src python3 -m unittest discover -s tests -v` for unit and HTTP integration tests. Run `PYTHONPATH=src python3 -m cfguard.demo --output demo-reports` to produce four deterministic reports. The CI workflow repeats these steps and uploads the reports as a build artifact.

## Outcome and limits

The project provides a reproducible local demonstration with no cloud charges. It does not run a live DDoS test or inspect a real zone in the offline demo. The live API paths support TLS/HTTPS and DDoS posture checks, but have only been tested with mocked API responses because no real zone is connected. Origin isolation and actual attack resistance cannot be established from these API checks.
