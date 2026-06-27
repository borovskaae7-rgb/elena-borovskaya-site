from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from tenacity import retry, stop_after_attempt, wait_exponential
from vk_checker.models import HeuristicResult, RowStatus, SheetRow
from vk_checker.rate_limit import LimitConfig, SyncRateLimiter

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
RESULT_HEADERS = [
    "Score",
    "Matched positive keywords",
    "Matched negative keywords",
    "Candidate class",
    "Collected text size",
    "Последняя проверка",
    "Статус",
    "Ошибка",
]


def _credentials(source: str) -> Credentials:
    if Path(source).exists():
        return Credentials.from_service_account_file(source, scopes=SCOPES)
    return Credentials.from_service_account_info(json.loads(source), scopes=SCOPES)


class GoogleSheetClient:
    def __init__(self, sheet_id: str, service_account: str, sheet_name: str, input_column: str, start_row: int, rpm: int = 60, jitter_ms: int = 350) -> None:
        self.sheet_id = sheet_id
        self.sheet_name = sheet_name
        self.input_column = input_column
        self.start_row = start_row
        self.limiter = SyncRateLimiter(LimitConfig(rpm=rpm, jitter_ms=jitter_ms))
        self.service = build("sheets", "v4", credentials=_credentials(service_account), cache_discovery=False)
        self.values = self.service.spreadsheets().values()

    def _execute(self, request: Any) -> Any:
        self.limiter.wait()
        return request.execute()

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=20), reraise=True)
    def ensure_headers(self) -> None:
        existing = self._execute(self.values.get(spreadsheetId=self.sheet_id, range=f"{self.sheet_name}!1:1")).get("values", [[]])[0]
        updated = list(existing)
        changed = False
        for header in RESULT_HEADERS:
            if header not in updated:
                updated.append(header)
                changed = True
        if changed:
            self._execute(self.values.update(spreadsheetId=self.sheet_id, range=f"{self.sheet_name}!1:1", valueInputOption="RAW", body={"values": [updated]}))

    def _headers(self) -> list[str]:
        self.ensure_headers()
        return self._execute(self.values.get(spreadsheetId=self.sheet_id, range=f"{self.sheet_name}!1:1")).get("values", [[]])[0]

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=20), reraise=True)
    def input_rows(self, start_row: int | None = None, end_row: int | None = None, checkpoint_row: int = 0) -> list[SheetRow]:
        first = max(start_row or self.start_row, self.start_row, checkpoint_row + 1 if checkpoint_row else self.start_row)
        last = end_row or ""
        rng = f"{self.sheet_name}!A{first}:A{last}"
        raw_rows = self._execute(self.values.get(spreadsheetId=self.sheet_id, range=rng)).get("values", [])
        return [SheetRow(row_number=offset, url=row[0].strip()) for offset, row in enumerate(raw_rows, start=first) if row and row[0].strip()]

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=20), reraise=True)
    def rows(self, start_row: int | None = None, end_row: int | None = None, retry_errors: bool = False, resume: bool = True, checkpoint_row: int = 0) -> list[SheetRow]:
        headers = self._headers()
        checked_idx = headers.index("Последняя проверка")
        status_idx = headers.index("Статус")
        first = max(start_row or self.start_row, self.start_row, checkpoint_row + 1 if checkpoint_row else self.start_row)
        last = end_row or ""
        rng = f"{self.sheet_name}!A{first}:{_col(max(status_idx + 1, checked_idx + 1, 1))}{last}"
        raw_rows = self._execute(self.values.get(spreadsheetId=self.sheet_id, range=rng)).get("values", [])
        result: list[SheetRow] = []
        for offset, row in enumerate(raw_rows, start=first):
            url = row[0].strip() if row else ""
            if not url:
                continue
            checked = row[checked_idx].strip() if len(row) > checked_idx else ""
            status = row[status_idx].strip().lower() if len(row) > status_idx else ""
            if retry_errors:
                if status == RowStatus.ERROR.value:
                    result.append(SheetRow(row_number=offset, url=url, status=RowStatus.ERROR))
                continue
            if resume and checked:
                continue
            if status != RowStatus.DONE.value:
                result.append(SheetRow(row_number=offset, url=url))
        logger.info("Loaded %s rows for processing", len(result))
        return result

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=20), reraise=True)
    def write_result(self, row_number: int, result: HeuristicResult) -> None:
        headers = self._headers()
        start_col = headers.index("Score") + 1
        end_col = headers.index("Ошибка") + 1
        values: list[Any] = [
            result.score,
            ", ".join(result.matched_positive_keywords),
            ", ".join(result.matched_negative_keywords),
            result.candidate_class.value,
            result.collected_text_size,
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
            RowStatus.DONE.value,
            "",
        ]
        self._execute(self.values.update(spreadsheetId=self.sheet_id, range=f"{self.sheet_name}!{_col(start_col)}{row_number}:{_col(end_col)}{row_number}", valueInputOption="RAW", body={"values": [values]}))

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=20), reraise=True)
    def write_error(self, row_number: int, message: str) -> None:
        headers = self._headers()
        status_col = headers.index("Статус") + 1
        error_col = headers.index("Ошибка") + 1
        self._execute(self.values.update(spreadsheetId=self.sheet_id, range=f"{self.sheet_name}!{_col(status_col)}{row_number}:{_col(error_col)}{row_number}", valueInputOption="RAW", body={"values": [[RowStatus.ERROR.value, message[:2000]]]}))


def _col(number: int) -> str:
    result = ""
    while number:
        number, rem = divmod(number - 1, 26)
        result = chr(65 + rem) + result
    return result
