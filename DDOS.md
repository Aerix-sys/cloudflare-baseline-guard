# DDoS defense lab

The dashboard offers two JSON fixtures and a read-only audit of a real Cloudflare zone. The live audit reads zone status, DNS proxy flags, rate limiting rules, and bot management settings. It infers edge mitigation from an active zone and proxied web records. It cannot verify origin isolation or prove resistance to an attack.

## Layered architecture

```text
Visitors → Cloudflare proxied DNS → automatic DDoS mitigation → targeted rate limit → web app
                                                                    ↓
                                                        origin accepts only trusted traffic
```

| Control | Why it matters | Portfolio evidence |
|---|---|---|
| Active Cloudflare zone and proxied web DNS | Traffic must pass through Cloudflare for its edge protection to apply | Zone/DNS screenshot with addresses redacted |
| Restrict direct access to origin | Attackers should not bypass the edge by connecting to origin IP | Firewall/Tunnel configuration and a safe reachability check |
| Automatic Cloudflare DDoS mitigation | Cloudflare provides this on all plans for proxied traffic | Official product docs and zone analytics |
| Rate limit on sensitive endpoints | Protect login and expensive API routes from application-layer abuse | Rule definition, test request, and false-positive review |
| Local resource bounds | Limit work per client and concurrent audits after edge filtering | `limits.py`, server timeout/body cap, unit tests |

The Cloudflare Free plan includes a limited number of rate limiting rules; check the current plan limits before configuring one. In a real deployment, choose the most expensive or abuse-prone path and set a threshold based on normal traffic. Start with observation, test legitimate users and automated clients, then enable a challenge or block action. Do not apply a blanket low threshold to the whole site.

Bot Fight Mode can add protection for some sites, but it may challenge legitimate API and mobile clients and cannot be scoped to a path on Free. Treat it as a decision after reviewing traffic, not a mandatory pass/fail control.

## Live audit

Run `PYTHONPATH=src python3 -m cfguard.live --zone-id "$CF_ZONE_ID" --hostname www.example.com`. Add more `--hostname` flags as needed. A `PASS` for edge protection means the selected web DNS records are proxied and the zone is active; it is a configuration inference, not an attack test. A `WARN` means an optional rate limiting or bot control is absent. `UNKNOWN` means evidence is missing, inaccessible, or cannot be determined from the API. Review every rule expression and threshold manually. See [DOMAIN_SETUP.md](DOMAIN_SETUP.md) for setup.

## Local app hardening

The demo dashboard binds only to `127.0.0.1`. Its audit endpoint limits request bodies to 1 KiB, uses a 5-second socket timeout, allows 30 audit requests per minute per client, and permits two concurrent audits. These controls protect this small local process from accidental or local overuse. They cannot absorb an Internet-scale DDoS attack; that requires an upstream edge and a properly isolated origin.

## References

- [Cloudflare DDoS protection](https://developers.cloudflare.com/ddos-protection/about/)
- [Cloudflare DNS proxy status](https://developers.cloudflare.com/dns/proxy-status/)
- [Protect your origin server](https://developers.cloudflare.com/fundamentals/security/protect-your-origin-server/)
- [Rate limiting rules](https://developers.cloudflare.com/waf/rate-limiting-rules/)
- [Bot Fight Mode considerations](https://developers.cloudflare.com/bots/get-started/bot-fight-mode/)
