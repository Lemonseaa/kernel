# Docker Deployment

## Build

```bash
cd /Users/lemonsea/Desktop/mas/kernel
docker-compose build
```

The image uses `python:3.11-slim`, installs the project in editable mode, and runs
`scripts/run_kernel_service.py`.

## Start

```bash
cp .env.example .env
docker-compose up -d
```

The service reads configuration from Docker Compose environment values. Compose also reads local
`.env` automatically for variable substitution.

## Health Check

Docker runs:

```bash
python scripts/health_check.py
```

That script executes a small in-process workflow and exits non-zero if the run fails.

## Optional Redis

```bash
docker-compose --profile redis up -d
```

Redis is optional in V0.9. It is not required for SQLite-backed local deployment.

## Run Tests In Container

```bash
docker-compose exec kernel python -m unittest discover -s tests -v
```

If `exec` fails because the container is unhealthy, inspect logs first:

```bash
docker-compose logs kernel
```
