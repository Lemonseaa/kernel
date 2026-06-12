# Operations

## Daily Commands

```bash
docker-compose ps
docker-compose logs loopharness
docker-compose exec loopharness ./loopharness status
docker-compose exec loopharness ./loopharness health
docker-compose exec loopharness ./loopharness run list
docker-compose exec loopharness ./loopharness bl list
```

## Restart

```bash
docker-compose restart loopharness
```

SQLite state is stored in the `loopharness-data` volume, so a normal restart does not remove state.

## Backup SQLite

```bash
docker-compose exec loopharness python - <<'PY'
from pathlib import Path
import shutil

src = Path('/app/data/loop_harness.db')
dst = Path('/app/data/loop_harness.backup.db')
if src.exists():
    shutil.copy2(src, dst)
    print(dst)
else:
    print('database not found')
PY
```

## Troubleshooting

### Container exits immediately

Run:

```bash
docker-compose logs loopharness
```

Common causes:

- Invalid numeric env value such as `LOOP_HARNESS_MAX_CONCURRENCY=abc`.
- SQLite path points to an unwritable directory.
- Image was built from stale files. Rebuild with `docker-compose build --no-cache`.

### Health check is unhealthy

Run:

```bash
docker-compose exec loopharness python scripts/ops/health_check.py
```

The script prints the failed run state when the lightweight workflow cannot complete.

### Provider calls do not use my key

Check:

```bash
docker-compose exec loopharness env | grep LOOP_HARNESS_
```

Environment variables override `.env`. If a shell export exists, it can override the value you expect
Compose to read.

### Redis is not running

Redis is optional. Start it explicitly:

```bash
docker-compose --profile redis up -d
```

V0.9 does not require Redis for normal operation.
