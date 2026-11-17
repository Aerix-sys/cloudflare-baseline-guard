# Cloudflare security baseline

Source: `Demo: ddos_insecure`

| Check | Status | Expected | Actual |
|---|---|---|---|
| Зона активна | PASS | Домен обслуживается Cloudflare | да |
| Веб-DNS проксируется | FAIL | HTTP/HTTPS идёт через Cloudflare | нет / не подтверждено |
| Origin закрыт от прямых запросов | FAIL | Прямой доступ к серверу ограничен | нет / не подтверждено |
| Автоматическая DDoS-защита | FAIL | Защита Cloudflare применяется к трафику | нет / не подтверждено |
| Лимит для чувствительных путей | FAIL | Установлен лимит для входа/API | нет / не подтверждено |

Result: **1/5 passed**
