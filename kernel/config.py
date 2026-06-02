"""Kernel configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any

from kernel.dryrun import DryRunProvider
from kernel.llm import LLMProvider, MiniMaxProvider, OpenAIProvider


@dataclass(slots=True)
class KernelConfig:
    """Configuration for kernel services."""

    providers: dict[str, dict[str, Any]] = field(default_factory=dict)
    default_provider: str = "minimax"
    dry_run: bool = False
    sqlite_path: str = "kernel.db"
    max_concurrency: int = 1
    llm_cache_enabled: bool = True
    llm_cache_max_size: int = 128
    llm_cache_ttl_seconds: float = 300.0
    slow_task_threshold_seconds: float = 5.0

    @classmethod
    def from_env(cls, env_path: str | Path = ".env") -> KernelConfig:
        """Build config from a .env file and process environment."""

        values = _load_env_file(Path(env_path))
        values.update(os.environ)
        default_provider = values.get("KERNEL_DEFAULT_PROVIDER", "minimax").lower()
        providers: dict[str, dict[str, Any]] = {}
        minimax_config = _provider_config(values, "MINIMAX")
        openai_config = _provider_config(values, "OPENAI")
        if minimax_config:
            providers["minimax"] = minimax_config
        if openai_config:
            providers["openai"] = openai_config
        return cls(
            providers=providers,
            default_provider=default_provider,
            dry_run=_bool_value(values.get("KERNEL_DRY_RUN"), default=False),
            sqlite_path=values.get("KERNEL_DB_PATH", "kernel.db"),
            max_concurrency=_int_value(values.get("KERNEL_MAX_CONCURRENCY"), default=1),
            llm_cache_enabled=_bool_value(values.get("KERNEL_LLM_CACHE_ENABLED"), default=True),
            llm_cache_max_size=_int_value(values.get("KERNEL_LLM_CACHE_MAX_SIZE"), default=128),
            llm_cache_ttl_seconds=_float_value(
                values.get("KERNEL_LLM_CACHE_TTL_SECONDS"),
                default=300.0,
            ),
            slow_task_threshold_seconds=_float_value(
                values.get("KERNEL_SLOW_TASK_THRESHOLD_SECONDS"),
                default=5.0,
            ),
        )

    @property
    def llm_provider(self) -> LLMProvider:
        """Build the configured default LLM provider."""

        if self.dry_run:
            return DryRunProvider(model="dryrun")
        config = dict(self.providers.get(self.default_provider, {}))
        if self.default_provider == "minimax":
            return MiniMaxProvider(**config)
        if self.default_provider == "openai":
            return OpenAIProvider(**config)
        raise ValueError(f"Unsupported provider: {self.default_provider}")


def _load_env_file(env_path: Path) -> dict[str, str]:
    """Read a simple KEY=VALUE .env file without external dependencies."""

    if not env_path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = _strip_quotes(value.strip())
    return values


def _strip_quotes(value: str) -> str:
    """Remove matching single or double quotes from a value."""

    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _provider_config(values: dict[str, str], provider: str) -> dict[str, Any]:
    """Build one provider configuration from environment values."""

    prefix = f"KERNEL_{provider}_"
    mapping = {
        "API_KEY": "api_key",
        "MODEL": "model",
        "BASE_URL": "base_url",
        "TIMEOUT_SECONDS": "timeout_seconds",
        "MAX_RETRIES": "max_retries",
    }
    config: dict[str, Any] = {}
    for env_suffix, config_key in mapping.items():
        value = values.get(f"{prefix}{env_suffix}")
        if value is None or value == "":
            continue
        if config_key == "timeout_seconds":
            config[config_key] = _float_value(value, default=0.0)
        elif config_key == "max_retries":
            config[config_key] = _int_value(value, default=0)
        else:
            config[config_key] = value
    return config


def _bool_value(value: str | None, default: bool) -> bool:
    """Parse a boolean environment value."""

    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_value(value: str | None, default: int) -> int:
    """Parse an integer environment value with fallback."""

    if value is None or value == "":
        return default
    return int(value)


def _float_value(value: str | None, default: float) -> float:
    """Parse a float environment value with fallback."""

    if value is None or value == "":
        return default
    return float(value)
