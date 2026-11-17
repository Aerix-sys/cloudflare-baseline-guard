# Three-minute demonstration

This is a self-contained demo. It needs Python 3.10+ and no Cloudflare account.

## Reproduce the evidence

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m cfguard.demo --output demo-reports
PYTHONPATH=src python3 -m cfguard.web
```

Open `http://127.0.0.1:8765`.

## Suggested walkthrough

1. **Baseline, 30 seconds:** Click **Безопасный пример**. Show four passes. Explain that the policy is explicit and read-only.
2. **Finding, 45 seconds:** Click **Показать проблемы**. Show failed HTTPS redirect, origin TLS, minimum TLS, and TLS 1.3. Download the Markdown report.
3. **DDoS architecture, 60 seconds:** Click **Найти слабые места**. Explain that an active zone alone does not protect an unproxied web endpoint or a directly reachable origin. Click **Защищённый пример** to compare.
4. **DevSecOps, 45 seconds:** Show `tests/`, `.github/workflows/audit.yml`, and generated `demo-reports/`. Explain that the CI job is offline and the live job is an explicit opt-in.

## Expected results

| Scenario | Passing checks |
|---|---:|
| Secure TLS/HTTPS | 4/4 |
| Insecure TLS/HTTPS | 0/4 |
| Protected DDoS architecture sample | 5/5 |
| Exposed DDoS architecture sample | 1/5 |

The DDoS results are evaluations of sample JSON, not measurements of real attack resistance.
