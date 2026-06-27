from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    google_sheet_id: str
    google_service_account: str
    headless: bool
    max_concurrent: int
    model: str
    vk_storage_state: str
    input_sheet_name: str
    input_column: str
    start_row: int
    openai_rpm: int
    request_timeout: int
    log_level: str

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv()
        required = ["OPENAI_API_KEY", "GOOGLE_SHEET_ID", "GOOGLE_SERVICE_ACCOUNT"]
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
        return cls(
            openai_api_key=os.environ["OPENAI_API_KEY"],
            google_sheet_id=os.environ["GOOGLE_SHEET_ID"],
            google_service_account=os.environ["GOOGLE_SERVICE_ACCOUNT"],
            headless=_bool(os.getenv("HEADLESS"), False),
            max_concurrent=max(1, int(os.getenv("MAX_CONCURRENT", "2"))),
            model=os.getenv("MODEL", "gpt-4.1-mini"),
            vk_storage_state=os.getenv("VK_STORAGE_STATE", ".vk-profile"),
            input_sheet_name=os.getenv("INPUT_SHEET_NAME", "Лист1"),
            input_column=os.getenv("INPUT_COLUMN", "A").upper(),
            start_row=max(1, int(os.getenv("START_ROW", "2"))),
            openai_rpm=max(1, int(os.getenv("OPENAI_RPM", "60"))),
            request_timeout=max(10, int(os.getenv("REQUEST_TIMEOUT", "60"))),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

    @property
    def profile_dir(self) -> Path:
        return Path(self.vk_storage_state)
