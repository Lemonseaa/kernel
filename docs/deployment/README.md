# OPC-OS Deployment

V1.0 production-ready deployment with Docker.

## 5-Minute Start

```bash
cd <your-path>/OPC-OS
cp .env.example .env
docker-compose build
docker-compose up -d
docker-compose ps
docker-compose logs opc-os
```

The default service uses SQLite at `/app/data/opc_os.db` inside the container and persists it through
the `opc-os-data` Docker volume.

## What Runs

- `opc-os`: long-lived OPC-OS process with health checks.
- `redis`: optional service enabled with `docker-compose --profile redis up -d`.

## Verify

```bash
docker-compose ps
docker-compose exec opc-os python -m unittest discover -s tests -v
docker-compose exec opc-os python scripts/health_check.py
```

Use `docker-compose logs opc-os` when health is not green.

## Files

- [docker.md](docker.md): Docker build and runtime guide.
- [config.md](config.md): environment variable reference.
- [ha.md](ha.md): multi-instance and failover guide.
- [ops.md](ops.md): operations and troubleshooting.
- [production-readiness.md](production-readiness.md): final validation checklist.
