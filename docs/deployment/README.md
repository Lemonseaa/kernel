# Kernel Deployment

V0.9 focuses on a small production-friendly deployment path: copy `.env.example`, start Docker
Compose, and verify health.

## 5-Minute Start

```bash
cd /Users/lemonsea/Desktop/mas/kernel
cp .env.example .env
docker-compose build
docker-compose up -d
docker-compose ps
docker-compose logs kernel
```

The default service uses SQLite at `/app/data/kernel.db` inside the container and persists it through
the `kernel-data` Docker volume.

## What Runs

- `kernel`: long-lived Kernel process with health checks.
- `redis`: optional service enabled with `docker-compose --profile redis up -d`.

V0.9 does not implement HA failover. Redis is included only as an optional deployment building block
for later versions.

## Verify

```bash
docker-compose ps
docker-compose exec kernel python -m unittest discover -s tests -v
docker-compose exec kernel python scripts/health_check.py
```

Use `docker-compose logs kernel` when health is not green.

## Files

- [docker.md](docker.md): Docker build and runtime guide.
- [config.md](config.md): environment variable reference.
- [ops.md](ops.md): operations and troubleshooting.
