# Operations

## Daily Commands

```bash
docker-compose ps
docker-compose logs opc-os
docker-compose exec opc-os ./opc-os status
docker-compose exec opc-os ./opc-os health
docker-compose exec opc-os ./opc-os run list
docker-compose exec opc-os ./opc-os bl list
```

## Restart

```bash
docker-compose restart opc-os
```

SQLite state is stored in the `opc-os-data` volume, so a normal restart does not remove state.

## Backup SQLite

```bash
docker-compose exec opc-os python - <<'PY'
from pathlib import Path
import shutil

src = Path('/app/data/opc_os.db')
dst = Path('/app/data/opc_os.backup.db')
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
docker-compose logs opc-os
```

Common causes:

- Invalid numeric env value such as `OPC_OS_MAX_CONCURRENCY=abc`.
- SQLite path points to an unwritable directory.
- Image was built from stale files. Rebuild with `docker-compose build --no-cache`.

### Health check is unhealthy

Run:

```bash
docker-compose exec opc-os python scripts/health_check.py
```

The script prints the failed run state when the lightweight workflow cannot complete.

### Provider calls do not use my key

Check:

```bash
docker-compose exec opc-os env | grep OPC_OS_
```

Environment variables override `.env`. If a shell export exists, it can override the value you expect
Compose to read.

### Redis is not running

Redis is optional. Start it explicitly:

```bash
docker-compose --profile redis up -d
```

V0.9 does not require Redis for normal operation.
