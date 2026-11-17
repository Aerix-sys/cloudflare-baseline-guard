# Connect a real Cloudflare zone

A Cloudflare zone needs a domain you control. The portfolio demo works without one. A domain registration has a recurring cost; check the price and renewal price before buying. The Cloudflare Free plan can host a zone, but a domain registration is separate.

1. Register a domain in [Cloudflare Registrar](https://developers.cloudflare.com/registrar/get-started/register-domain/) or another registrar. If you already own one, add it to Cloudflare and [change its nameservers](https://developers.cloudflare.com/dns/zone-setups/full-setup/setup/). Wait until the zone status is **Active**.
2. Add an `A`, `AAAA`, or `CNAME` record for the web hostname you want to audit. Set it to **Proxied** (orange cloud). Point it to a real web application or origin you control. A DNS record alone is not proof of a protected application.
3. In the Cloudflare dashboard, copy the 32-character **Zone ID** from the zone overview. Create a token limited to this zone with **Zone Read**, **Zone Settings Read**, **DNS Read**, **Zone WAF Read**, and **Bot Management Read** permissions. The last two let the auditor inspect rate limiting and bot configuration. An unavailable feature or denied optional permission appears as `UNKNOWN`, not a pass. Never commit the token.
4. In a local terminal, set `CF_ZONE_ID` and `CF_API_TOKEN`, then run the commands below. Add `--hostname www.example.com` for each web hostname to check; otherwise the apex is checked.

```sh
export CF_ZONE_ID='your-32-character-zone-id'
export CF_API_TOKEN='your-scoped-token'
PYTHONPATH=src python3 -m cfguard --zone-id "$CF_ZONE_ID" --report tls-report.md
PYTHONPATH=src python3 -m cfguard.live --zone-id "$CF_ZONE_ID" --hostname www.example.com --report ddos-report.md
```

Run the dashboard from the same terminal with `PYTHONPATH=src python3 -m cfguard.web`. For additional hostnames in the dashboard, set `CF_HOSTNAMES=example.com,www.example.com` before starting it.

The DDoS audit verifies configuration evidence, not resistance to a live attack. Confirm origin isolation using your firewall, Cloudflare Tunnel, or authenticated origin access; review normal traffic before enabling rate limits. Do not run an attack test against shared infrastructure.
