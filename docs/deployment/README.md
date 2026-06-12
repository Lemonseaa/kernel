# Loop Harness Deployment

> Product direction is defined in [../BLUEPRINT.md](../BLUEPRINT.md). This deployment folder only documents how to run the current codebase.

V1.0 production-ready deployment with Docker.

## 5-Minute Start

```bash
cd <your-path>/loop-harness
cp .env.example .env
docker-compose build
docker-compose up -d
docker-compose ps
docker-compose logs loopharness
```

The default service uses SQLite at `/app/data/loop_harness.db` inside the container and persists it through
the `loopharness-data` Docker volume.

## What Runs

- `loopharness`: long-lived Loop Harness process with health checks.
- `redis`: optional service enabled with `docker-compose --profile redis up -d`.

## Verify

```bash
docker-compose ps
docker-compose exec loopharness python -m unittest discover -s tests -v
docker-compose exec loopharness python scripts/ops/health_check.py
```

Use `docker-compose logs loopharness` when health is not green.

## Files

- [docker.md](docker.md): Docker build and runtime guide.
- [config.md](config.md): environment variable reference.
- [ha.md](ha.md): multi-instance and failover guide.
- [ops.md](ops.md): operations and troubleshooting.
- [production-readiness.md](production-readiness.md): final validation checklist.
