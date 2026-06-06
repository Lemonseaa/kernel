# Configuration

CheckpointAI V0.9 supports zero-code startup through `.env` and process environment variables.

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
| `CHECKPOINT_AI_DB_PATH` | `checkpoint_ai.db` | SQLite database path. Docker defaults to `/app/data/checkpoint_ai.db`. |
| `CHECKPOINT_AI_DEFAULT_PROVIDER` | `minimax` | Default provider: currently `minimax` or `openai`. |
| `CHECKPOINT_AI_DRY_RUN` | `false` | Use dry-run provider and simulated tool behavior. |
| `CHECKPOINT_AI_MINIMAX_API_KEY` | empty | MiniMax API key. |
| `CHECKPOINT_AI_MINIMAX_MODEL` | `MiniMax-M2.7-highspeed` | MiniMax model name. |
| `CHECKPOINT_AI_MINIMAX_BASE_URL` | `https://api.minimax.chat/v1` | MiniMax API base URL. |
| `CHECKPOINT_AI_MINIMAX_TIMEOUT_SECONDS` | unset | MiniMax timeout. |
| `CHECKPOINT_AI_MINIMAX_MAX_RETRIES` | unset | MiniMax retry count. |
| `CHECKPOINT_AI_OPENAI_API_KEY` | empty | OpenAI-compatible API key. |
| `CHECKPOINT_AI_OPENAI_MODEL` | `gpt-4.1-mini` | OpenAI-compatible model name. |
| `CHECKPOINT_AI_OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible API base URL. |
| `CHECKPOINT_AI_OPENAI_TIMEOUT_SECONDS` | unset | OpenAI-compatible timeout. |
| `CHECKPOINT_AI_OPENAI_MAX_RETRIES` | unset | OpenAI-compatible retry count. |
| `CHECKPOINT_AI_MAX_CONCURRENCY` | `1` | Workflow concurrency limit. |
| `CHECKPOINT_AI_LLM_CACHE_ENABLED` | `true` | Enable prompt/model response cache. |
| `CHECKPOINT_AI_LLM_CACHE_MAX_SIZE` | `128` | Maximum cached LLM responses. |
| `CHECKPOINT_AI_LLM_CACHE_TTL_SECONDS` | `300` | Cache TTL in seconds. |

## LLM Provider Scope

Current implementation is MVP-level:

```
1. MiniMax native provider
2. OpenAI-compatible provider
3. Provider selection via env
4. Basic timeout / retry / cache
```

This does not yet mean CheckpointAI has a full model vendor console.

Most providers can be connected through the OpenAI-compatible path by setting:

```
CHECKPOINT_AI_DEFAULT_PROVIDER=openai
CHECKPOINT_AI_OPENAI_BASE_URL=<provider-compatible-base-url>
CHECKPOINT_AI_OPENAI_API_KEY=<provider-api-key>
CHECKPOINT_AI_OPENAI_MODEL=<provider-model-name>
```

Examples of providers that may use this path:

```
OpenAI, DeepSeek, Qwen/DashScope, Kimi/Moonshot, Zhipu,
SiliconFlow, OpenRouter, Ollama/LM Studio, Together, Fireworks, Groq
```

V7.9 will add a proper LLM Provider Console:

- provider records
- model records
- role-based model routing
- provider health checks
- masked API keys
- provider/model cost summaries

Until that is implemented, use `.env` for provider configuration.
| `CHECKPOINT_AI_SLOW_TASK_THRESHOLD_SECONDS` | `5` | Slow-task alert threshold. |
| `CHECKPOINT_AI_SERVICE_HEARTBEAT_SECONDS` | `30` | Container heartbeat log interval. |
| `CHECKPOINT_AI_HA_ENABLED` | `false` | Enable lease-based HA manager. |
| `CHECKPOINT_AI_INSTANCE_ID` | generated id | Stable instance id for HA leases. |
| `CHECKPOINT_AI_HA_LEASE_TTL_SECONDS` | `30` | Primary lease TTL. |
| `CHECKPOINT_AI_HA_HEARTBEAT_SECONDS` | `10` | Heartbeat interval for HA service loops. |
| `CHECKPOINT_AI_LB_PORT` | `8080` | Optional HA load balancer host port. |
| `CHECKPOINT_AI_REDIS_PORT` | `6379` | Optional Redis host port when profile is enabled. |

## Example

```bash
cp .env.example .env
sed -i.bak 's/CHECKPOINT_AI_DEFAULT_PROVIDER=minimax/CHECKPOINT_AI_DEFAULT_PROVIDER=openai/' .env
docker-compose up -d
```
