# High Availability

V1.0 adds lease-based high availability primitives and a multi-instance Docker Compose shape.

## What HA Means In V1.0

- Instances share state through the same SQLite database path.
- Each instance has a `KERNEL_INSTANCE_ID`.
- `HAManager` uses a primary lease with TTL.
- A backup instance can acquire primary when the current primary lease expires.
- Docker Compose includes a secondary instance and an optional Nginx load balancer profile.

This is an MVP HA model for OPC Kernel operations. It is not a cross-region HA system.

## Configuration

```bash
KERNEL_HA_ENABLED=true
KERNEL_INSTANCE_ID=kernel-primary
KERNEL_HA_LEASE_TTL_SECONDS=30
KERNEL_HA_HEARTBEAT_SECONDS=10
```

## Start Multi-Instance Deployment

```bash
docker-compose --profile ha up -d
docker-compose ps
```

Services:

- `kernel`: primary candidate.
- `kernel-secondary`: backup candidate.
- `kernel-lb`: optional Nginx load balancer on port `8080`.

## Failover Behavior

1. Primary acquires the lease.
2. Backup sees an active primary and remains backup.
3. If primary stops and the lease expires, backup can acquire primary.
4. The current primary is visible through `HAManager.status()`.

## Verify Locally Without Docker

```bash
python -m unittest tests.test_ha -v
```
