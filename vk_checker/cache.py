from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from threading import Lock
from vk_checker.models import CommunityData, HeuristicResult


class ResultCache:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self._lock = Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True) if self.path.parent != Path(".") else None
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS results (url TEXT PRIMARY KEY, content_hash TEXT NOT NULL, result_json TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_results_hash ON results(content_hash)")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=30)

    @staticmethod
    def content_hash(data: CommunityData) -> str:
        payload = data.model_dump(mode="json", exclude={"scraped_at"}, exclude_none=True)
        normalized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def get(self, url: str, content_hash: str) -> HeuristicResult | None:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT result_json FROM results WHERE url=? AND content_hash=?", (url, content_hash)).fetchone()
        if not row:
            return None
        return HeuristicResult.model_validate_json(row[0])

    def set(self, url: str, content_hash: str, result: HeuristicResult) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO results(url, content_hash, result_json, updated_at) VALUES(?,?,?,CURRENT_TIMESTAMP) "
                "ON CONFLICT(url) DO UPDATE SET content_hash=excluded.content_hash, result_json=excluded.result_json, updated_at=CURRENT_TIMESTAMP",
                (url, content_hash, result.model_dump_json()),
            )

    def count(self) -> int:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM results").fetchone()
        return int(row[0]) if row else 0
