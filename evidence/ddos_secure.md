# Cloudflare security baseline

Source: `Demo: ddos_secure`

| Check | Status | Expected | Actual |
|---|---|---|---|
| Зона активна | PASS | Домен обслуживается Cloudflare | да |
| Веб-DNS проксируется | PASS | HTTP/HTTPS идёт через Cloudflare | да |
| Origin закрыт от прямых запросов | PASS | Прямой доступ к серверу ограничен | да |
| Автоматическая DDoS-защита | PASS | Защита Cloudflare применяется к трафику | да |
| Лимит для чувствительных путей | PASS | Установлен лимит для входа/API | да |

Result: **5/5 passed**
