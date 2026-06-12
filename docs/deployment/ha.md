# High Availability

LoopHarness no longer ships an internal HA manager.

HA is an external deployment responsibility because the product direction is an Evidence Harness, not a durable workflow platform.

## Recommended Approach

Use infrastructure that already solves process supervision and failover:

```text
Docker / systemd / platform restart policy
reverse proxy or load balancer
managed database or external durable workflow system when needed
Temporal only if durable orchestration becomes a real requirement
```

## Current Docker Shape

`docker-compose.yml` runs one LoopHarness service with a restart policy and health check.

```bash
docker compose up -d
docker compose ps
python scripts/ops/health_check.py
```

## Boundary

Do not rebuild primary leases, leader election, or cross-region failover inside LoopHarness unless the Evidence Harness path proves it needs durable workflow execution.

