# Project status

## Implemented

- Local dashboard and CLI for four live TLS/HTTPS zone settings.
- Read-only live DDoS posture audit: zone status, proxied DNS for selected hosts, inferred edge protection, active rate limiting rules, and bot settings.
- Explicit `UNKNOWN` for origin isolation and data the token cannot access.
- Offline DDoS architecture fixtures, deterministic reports, unit and HTTP integration tests.
- Pinned GitHub Actions verification; live audit is manually triggered with a scoped token.
- Security model, case study, demo guide, and [domain onboarding](DOMAIN_SETUP.md).
- Public static demo at https://cloudflare-baseline-guard.pages.dev/.

## Real-world validation

No real zone is connected yet. The API client is tested with mocked responses, but a production zone and origin are needed to validate Cloudflare behavior and complete the origin-isolation check.
