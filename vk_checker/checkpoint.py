from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from vk_checker.models import ProcessingStats


@dataclass(frozen=True)
class CheckpointState:
    last_row: int = 0
    cache_entries: int = 0
    stats: dict[str, Any] | None = None


class CheckpointManager:
    def __init__(self, path: str, every: int) -> None:
        self.path = Path(path)
        self.every = max(every, 1)
        self.path.parent.mkdir(parents=True, exist_ok=True) if self.path.parent != Path(".") else None

    def load(self) -> CheckpointState:
        if not self.path.exists():
            return CheckpointState()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return CheckpointState(last_row=int(data.get("last_row", 0)), cache_entries=int(data.get("cache_entries", 0)), stats=data.get("stats"))

    def maybe_save(self, processed: int, last_row: int, stats: ProcessingStats, cache_entries: int) -> None:
        if processed and processed % self.every == 0:
            self.save(last_row, stats, cache_entries)

    def save(self, last_row: int, stats: ProcessingStats, cache_entries: int) -> None:
        payload = {"last_row": last_row, "stats": stats.model_dump(), "cache_entries": cache_entries}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)
