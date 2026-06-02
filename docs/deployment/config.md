# Configuration

Kernel V0.9 supports zero-code startup through `.env` and process environment variables.

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
| `KERNEL_DB_PATH` | `kernel.db` | SQLite database path. Docker defaults to `/app/data/kernel.db`. |
| `KERNEL_DEFAULT_PROVIDER` | `minimax` | Default provider: `minimax` or `openai`. |
| `KERNEL_DRY_RUN` | `false` | Use dry-run provider and simulated tool behavior. |
| `KERNEL_MINIMAX_API_KEY` | empty | MiniMax API key. |
| `KERNEL_MINIMAX_MODEL` | `MiniMax-M2.7-highspeed` | MiniMax model name. |
| `KERNEL_MINIMAX_BASE_URL` | `https://api.minimax.chat/v1` | MiniMax API base URL. |
| `KERNEL_MINIMAX_TIMEOUT_SECONDS` | unset | MiniMax timeout. |
| `KERNEL_MINIMAX_MAX_RETRIES` | unset | MiniMax retry count. |
| `KERNEL_OPENAI_API_KEY` | empty | OpenAI-compatible API key. |
| `KERNEL_OPENAI_MODEL` | `gpt-4.1-mini` | OpenAI-compatible model name. |
| `KERNEL_OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible API base URL. |
| `KERNEL_OPENAI_TIMEOUT_SECONDS` | unset | OpenAI-compatible timeout. |
| `KERNEL_OPENAI_MAX_RETRIES` | unset | OpenAI-compatible retry count. |
| `KERNEL_MAX_CONCURRENCY` | `1` | Workflow concurrency limit. |
| `KERNEL_LLM_CACHE_ENABLED` | `true` | Enable prompt/model response cache. |
| `KERNEL_LLM_CACHE_MAX_SIZE` | `128` | Maximum cached LLM responses. |
| `KERNEL_LLM_CACHE_TTL_SECONDS` | `300` | Cache TTL in seconds. |
| `KERNEL_SLOW_TASK_THRESHOLD_SECONDS` | `5` | Slow-task alert threshold. |
| `KERNEL_SERVICE_HEARTBEAT_SECONDS` | `30` | Container heartbeat log interval. |
| `KERNEL_REDIS_PORT` | `6379` | Optional Redis host port when profile is enabled. |

## Example

```bash
cp .env.example .env
sed -i.bak 's/KERNEL_DEFAULT_PROVIDER=minimax/KERNEL_DEFAULT_PROVIDER=openai/' .env
docker-compose up -d
```
