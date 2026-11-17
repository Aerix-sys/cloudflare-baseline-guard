# Security model

## Assets and trust boundaries

- The Cloudflare API token can read zone settings. It is supplied through an environment variable and is never written to the report.
- The zone configuration is retrieved over HTTPS from the Cloudflare API.
- GitHub Actions uses an environment secret only in the manually triggered live job. Pull requests run against fixtures.
- The web app listens only on `127.0.0.1` and checks Host, Origin, and a per-server request token before running an audit. It does not accept a Cloudflare token from the browser.
- The audit endpoint bounds body size, socket wait time, per-client request rate, and concurrent audit work.

## Threats and controls

| Threat | Control | Evidence |
|---|---|---|
| Token exposed in repository | Environment variable and GitHub secret; `.env` ignored | No credential in source or fixtures |
| Untrusted pull request reads token | Live job runs only on `workflow_dispatch` in a named environment | Workflow condition |
| Incorrect API response leads to false pass | Check `success`, result shape, setting ID, and missing values | Unit tests |
| Insecure configuration goes unnoticed | Nonzero exit code for failed checks | Insecure fixture and CI |
| Auditor changes production settings | GET requests only | `fetch_settings` implementation |
| Browser request is forged from another site | Host, Origin, and CSRF checks | `test_http_audit_and_csrf` |
| Local audit endpoint receives excessive requests | Rate limit, concurrency cap, short socket timeout | `test_rate_limit_resets_after_window` and server code |

## Limits

The live audit checks four zone settings only. The DDoS readiness demo evaluates manually supplied fixtures and does not inspect DNS records, WAF rules, origin behavior, or account permissions. A passing result does not prove the application or origin is secure. The live audit has not been verified against a user account in this repository.
