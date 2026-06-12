# Configuration

LoopHarness V0.9 supports zero-code startup through `.env` and process environment variables.

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
| `LOOP_HARNESS_DB_PATH` | `loop_harness.db` | SQLite database path. Docker defaults to `/app/data/loop_harness.db`. |
| `LOOP_HARNESS_DEFAULT_PROVIDER` | `minimax` | Default provider: currently `minimax` or `openai`. |
| `LOOP_HARNESS_DRY_RUN` | `false` | Use dry-run provider and simulated tool behavior. |
| `LOOP_HARNESS_MINIMAX_API_KEY` | empty | MiniMax API key. |
| `LOOP_HARNESS_MINIMAX_MODEL` | `MiniMax-M2.7-highspeed` | MiniMax model name. |
| `LOOP_HARNESS_MINIMAX_BASE_URL` | `https://api.minimax.chat/v1` | MiniMax API base URL. |
| `LOOP_HARNESS_MINIMAX_TIMEOUT_SECONDS` | unset | MiniMax timeout. |
| `LOOP_HARNESS_MINIMAX_MAX_RETRIES` | unset | MiniMax retry count. |
| `LOOP_HARNESS_OPENAI_API_KEY` | empty | OpenAI-compatible API key. |
| `LOOP_HARNESS_OPENAI_MODEL` | `gpt-4.1-mini` | OpenAI-compatible model name. |
| `LOOP_HARNESS_OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible API base URL. |
| `LOOP_HARNESS_OPENAI_TIMEOUT_SECONDS` | unset | OpenAI-compatible timeout. |
| `LOOP_HARNESS_OPENAI_MAX_RETRIES` | unset | OpenAI-compatible retry count. |
| `LOOP_HARNESS_MAX_CONCURRENCY` | `1` | Workflow concurrency limit. |
| `LOOP_HARNESS_LLM_CACHE_ENABLED` | `true` | Enable prompt/model response cache. |
| `LOOP_HARNESS_LLM_CACHE_MAX_SIZE` | `128` | Maximum cached LLM responses. |
| `LOOP_HARNESS_LLM_CACHE_TTL_SECONDS` | `300` | Cache TTL in seconds. |
| `LOOP_HARNESS_SLOW_TASK_THRESHOLD_SECONDS` | `5` | Slow-task alert threshold. |
| `LOOP_HARNESS_SERVICE_HEARTBEAT_SECONDS` | `30` | Container heartbeat log interval. |
| `LOOP_HARNESS_REDIS_PORT` | `6379` | Optional Redis host port when profile is enabled. |

## LLM Provider Scope

Current implementation is MVP-level:

```
1. MiniMax native provider
2. OpenAI-compatible provider
3. Provider selection via env
4. Basic timeout / retry / cache
```

This does not yet mean LoopHarness has a full model vendor console.

Most providers can be connected through the OpenAI-compatible path by setting:

```
LOOP_HARNESS_DEFAULT_PROVIDER=openai
LOOP_HARNESS_OPENAI_BASE_URL=<provider-compatible-base-url>
LOOP_HARNESS_OPENAI_API_KEY=<provider-api-key>
LOOP_HARNESS_OPENAI_MODEL=<provider-model-name>
```

Examples of providers that may use this path:

```
OpenAI, DeepSeek, Qwen/DashScope, Kimi/Moonshot, Zhipu,
SiliconFlow, OpenRouter, Ollama/LM Studio, Together, Fireworks, Groq
```

The previous LLM Provider Console plan is frozen. LoopHarness should not become a full provider platform.

For now, provider configuration stays intentionally simple:

- use OpenAI-compatible endpoints where possible
- use `.env` for local configuration
- only add provider metadata required by the Evidence Adapter path
- prefer LiteLLM/OpenRouter-style external routing instead of rebuilding provider infrastructure

If a future evidence workflow needs richer model routing, add the smallest configuration needed for that workflow only.

## Example

```bash
cp .env.example .env
sed -i.bak 's/LOOP_HARNESS_DEFAULT_PROVIDER=minimax/LOOP_HARNESS_DEFAULT_PROVIDER=openai/' .env
docker-compose up -d
```
