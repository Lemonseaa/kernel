# Configuration

OPCOS V0.9 supports zero-code startup through `.env` and process environment variables.

## Loading Order

1. Values from `.env`.
2. Process environment variables override `.env`.
3. Code defaults are used when neither is set.

## Required For Local Docker

No value is strictly required for the deterministic fallback provider behavior. For real provider
calls, configure the selected provider API key.

## Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPC_OS_DB_PATH` | `opc_os.db` | SQLite database path. Docker defaults to `/app/data/opc_os.db`. |
| `OPC_OS_DEFAULT_PROVIDER` | `minimax` | Default provider: `minimax` or `openai`. |
| `OPC_OS_DRY_RUN` | `false` | Use dry-run provider and simulated tool behavior. |
| `OPC_OS_MINIMAX_API_KEY` | empty | MiniMax API key. |
| `OPC_OS_MINIMAX_MODEL` | `MiniMax-M2.7-highspeed` | MiniMax model name. |
| `OPC_OS_MINIMAX_BASE_URL` | `https://api.minimax.chat/v1` | MiniMax API base URL. |
| `OPC_OS_MINIMAX_TIMEOUT_SECONDS` | unset | MiniMax timeout. |
| `OPC_OS_MINIMAX_MAX_RETRIES` | unset | MiniMax retry count. |
| `OPC_OS_OPENAI_API_KEY` | empty | OpenAI-compatible API key. |
| `OPC_OS_OPENAI_MODEL` | `gpt-4.1-mini` | OpenAI-compatible model name. |
| `OPC_OS_OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible API base URL. |
| `OPC_OS_OPENAI_TIMEOUT_SECONDS` | unset | OpenAI-compatible timeout. |
| `OPC_OS_OPENAI_MAX_RETRIES` | unset | OpenAI-compatible retry count. |
| `OPC_OS_MAX_CONCURRENCY` | `1` | Workflow concurrency limit. |
| `OPC_OS_LLM_CACHE_ENABLED` | `true` | Enable prompt/model response cache. |
| `OPC_OS_LLM_CACHE_MAX_SIZE` | `128` | Maximum cached LLM responses. |
| `OPC_OS_LLM_CACHE_TTL_SECONDS` | `300` | Cache TTL in seconds. |
| `OPC_OS_SLOW_TASK_THRESHOLD_SECONDS` | `5` | Slow-task alert threshold. |
| `OPC_OS_SERVICE_HEARTBEAT_SECONDS` | `30` | Container heartbeat log interval. |
| `OPC_OS_HA_ENABLED` | `false` | Enable lease-based HA manager. |
| `OPC_OS_INSTANCE_ID` | generated id | Stable instance id for HA leases. |
| `OPC_OS_HA_LEASE_TTL_SECONDS` | `30` | Primary lease TTL. |
| `OPC_OS_HA_HEARTBEAT_SECONDS` | `10` | Heartbeat interval for HA service loops. |
| `OPC_OS_LB_PORT` | `8080` | Optional HA load balancer host port. |
| `OPC_OS_REDIS_PORT` | `6379` | Optional Redis host port when profile is enabled. |

## Example

```bash
cp .env.example .env
sed -i.bak 's/OPC_OS_DEFAULT_PROVIDER=minimax/OPC_OS_DEFAULT_PROVIDER=openai/' .env
docker-compose up -d
```
