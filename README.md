# Distributed URL Shortener

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-API-000000?logo=flask)](https://flask.palletsprojects.com/)
[![Redis](https://img.shields.io/badge/Redis-Cache-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Storage-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Production-style URL shortener: **Redis** for hot-path redirects, **PostgreSQL** for durability & analytics, orchestrated with **Docker Compose**.

---

## Features

- Create short links (`POST /shorten`)
- Fast redirect with cache-aside pattern
- Click analytics (`GET /stats/<code>`)
- Custom aliases
- Optional link expiration
- DB init with retry (container startup friendly)
- Fully containerized services

## Architecture

```text
Client
  │
  ▼
Flask API  ──cache hit──▶ Redis ──▶ 302 Redirect
  │              │
  │           miss│
  ▼              ▼
PostgreSQL ◀── populate cache
  (URL map + clicks + expiry)
```

| Component | Role |
|-----------|------|
| Flask | REST API + redirect handler |
| Redis | Low-latency short_code → URL |
| PostgreSQL | Source of truth + analytics |
| Docker Compose | Local multi-service runtime |

## Tech stack

- **Backend:** Python, Flask, Flask-SQLAlchemy, flask-cors  
- **Data:** PostgreSQL, Redis  
- **Ops:** Docker, Docker Compose  

## Project structure

```text
Distributed-URL-Shortener/
├── Dockerfile
├── docker-compose.yml
├── app/
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   └── requirements.txt
├── .github/workflows/ci.yml
├── .gitignore
├── LICENSE
└── README.md
```

## Run with Docker (recommended)

```bash
git clone https://github.com/mirza-zain-dev/Distributed-URL-Shortener.git
cd Distributed-URL-Shortener
docker compose up --build
```

API: `http://localhost:5050`

### Environment (compose defaults)

| Variable | Example |
|----------|---------|
| `DATABASE_URL` | `postgresql://postgres:postgres@db:5432/urlshortener` |
| `REDIS_URL` | `redis://redis:6379/0` |

## API

### Create short URL

```bash
curl -X POST http://localhost:5050/shorten \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://example.com/very/long/path",
    "custom_alias": "docs",
    "expires_in_days": 30
  }'
```

### Redirect

```bash
curl -i http://localhost:5050/<short_code>
```

### Stats

```bash
curl http://localhost:5050/stats/<short_code>
```

## Engineering highlights

- **Cache-aside** reads: Redis first, DB fallback, then backfill  
- **Collision-safe** short code generation  
- **Expiry** enforced on read path  
- **Click counters** persisted in PostgreSQL  
- Startup **DB retry loop** for compose race conditions  

## Roadmap

- [ ] Rate limiting & auth for write API  
- [ ] Horizontal API replicas behind a load balancer  
- [ ] Metrics (Prometheus) + structured logging  
- [ ] Soft-delete & admin audit trail  

## License

MIT — see [LICENSE](LICENSE).

## Author

**Mirza Zain** · [GitHub](https://github.com/mirza-zain-dev)
