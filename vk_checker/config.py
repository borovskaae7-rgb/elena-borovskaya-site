from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any
import yaml
from dotenv import load_dotenv


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _yaml(path: str = "config.yaml") -> dict[str, Any]:
    file = Path(path)
    if not file.exists():
        return {}
    with file.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _get(data: dict[str, Any], dotted: str, default: Any) -> Any:
    current: Any = data
    for key in dotted.split("."):
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


@dataclass(frozen=True)
class ProjectConfig:
    batch_size: int = 200
    progress_interval: int = 1000
    artifacts_dir: str = "artifacts"
    cache_path: str = ".vk_checker_cache.sqlite3"
    checkpoint_path: str = "checkpoint.json"
    checkpoint_interval: int = 100
    export_dir: str = "exports"


@dataclass(frozen=True)
class ScrapingConfig:
    navigation_timeout_ms: int = 30_000
    max_links: int = 80
    max_posts: int = 5
    max_text_chars: int = 8000


@dataclass(frozen=True)
class RateLimitsConfig:
    playwright_rpm: int = 120
    google_sheets_rpm: int = 60
    jitter_ms: int = 350


@dataclass(frozen=True)
class MonitoringConfig:
    error_spike_threshold: float = 0.2


@dataclass(frozen=True)
class PrefilterConfig:
    rules_path: str = "prefilter_rules.yaml"


@dataclass(frozen=True)
class Settings:
    google_sheet_id: str
    google_service_account: str
    headless: bool
    max_concurrent: int
    vk_storage_state: str
    input_sheet_name: str
    input_column: str
    start_row: int
    request_timeout: int
    log_level: str
    project: ProjectConfig
    scraping: ScrapingConfig
    prefilter: PrefilterConfig
    rate_limits: RateLimitsConfig
    monitoring: MonitoringConfig

    @classmethod
    def load(cls, config_path: str = "config.yaml") -> "Settings":
        load_dotenv()
        raw = _yaml(config_path)
        required = ["GOOGLE_SHEET_ID", "GOOGLE_SERVICE_ACCOUNT"]
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
        return cls(
            google_sheet_id=os.environ["GOOGLE_SHEET_ID"],
            google_service_account=os.environ["GOOGLE_SERVICE_ACCOUNT"],
            headless=_bool(os.getenv("HEADLESS"), False),
            max_concurrent=max(1, int(os.getenv("MAX_CONCURRENT", "2"))),
            vk_storage_state=os.getenv("VK_STORAGE_STATE", ".vk-profile"),
            input_sheet_name=os.getenv("INPUT_SHEET_NAME", "Лист1"),
            input_column=os.getenv("INPUT_COLUMN", "A").upper(),
            start_row=max(1, int(os.getenv("START_ROW", "2"))),
            request_timeout=max(10, int(os.getenv("REQUEST_TIMEOUT", "60"))),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            project=ProjectConfig(**_get(raw, "project", {})),
            scraping=ScrapingConfig(**_get(raw, "scraping", {})),
            prefilter=PrefilterConfig(**_get(raw, "prefilter", {})),
            rate_limits=RateLimitsConfig(**_get(raw, "rate_limits", {})),
            monitoring=MonitoringConfig(**_get(raw, "monitoring", {})),
        )

    @property
    def profile_dir(self) -> Path:
        return Path(self.vk_storage_state)
