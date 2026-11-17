# Cloudflare security baseline

Source: `Demo: insecure`

| Check | Status | Expected | Actual |
|---|---|---|---|
| HTTPS redirect | FAIL | on | off |
| Origin TLS | FAIL | strict | flexible |
| Minimum TLS | FAIL | 1.2 or newer | 1.0 |
| TLS 1.3 | FAIL | on (without 0-RTT) | off |

Result: **0/4 passed**
