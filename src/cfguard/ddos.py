"""Educational DDoS readiness policy for a Cloudflare-protected web app."""


DDOS_CONTROLS = (
    ("Зона активна", "zone_active", "Домен обслуживается Cloudflare"),
    ("Веб-DNS проксируется", "web_dns_proxied", "HTTP/HTTPS идёт через Cloudflare"),
    ("Origin закрыт от прямых запросов", "origin_restricted", "Прямой доступ к серверу ограничен"),
    ("Автоматическая DDoS-защита", "edge_ddos_active", "Защита Cloudflare применяется к трафику"),
    ("Лимит для чувствительных путей", "sensitive_path_rate_limit", "Установлен лимит для входа/API"),
)


def evaluate_ddos(profile: dict) -> list[dict]:
    """Evaluate a manually supplied architecture profile, not a live zone."""
    return [
        {
            "check": name,
            "setting": key,
            "status": "PASS" if profile.get(key) is True else "FAIL",
            "expected": expected,
            "actual": "да" if profile.get(key) is True else "нет / не подтверждено",
        }
        for name, key, expected in DDOS_CONTROLS
    ]
