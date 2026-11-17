# Cloudflare security baseline

Source: `Demo: secure`

| Check | Status | Expected | Actual |
|---|---|---|---|
| HTTPS redirect | PASS | on | on |
| Origin TLS | PASS | strict | strict |
| Minimum TLS | PASS | 1.2 or newer | 1.2 |
| TLS 1.3 | PASS | on (without 0-RTT) | on |

Result: **4/4 passed**
