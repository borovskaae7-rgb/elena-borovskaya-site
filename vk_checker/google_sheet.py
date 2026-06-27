from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from tenacity import retry, stop_after_attempt, wait_exponential
from vk_checker.models import ClassificationResult, SheetRow

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
RESULT_HEADERS = ["Инфобизнес", "Категория", "Подкатегория", "Уверенность", "Причина", "Последняя проверка"]


def _credentials(source: str) -> Credentials:
    if Path(source).exists():
        return Credentials.from_service_account_file(source, scopes=SCOPES)
    return Credentials.from_service_account_info(json.loads(source), scopes=SCOPES)


class GoogleSheetClient:
    def __init__(self, sheet_id: str, service_account: str, sheet_name: str, input_column: str, start_row: int) -> None:
        self.sheet_id = sheet_id
        self.sheet_name = sheet_name
        self.input_column = input_column
        self.start_row = start_row
        self.service = build("sheets", "v4", credentials=_credentials(service_account), cache_discovery=False)
        self.values = self.service.spreadsheets().values()

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=20), reraise=True)
    def ensure_headers(self) -> None:
        existing = self.values.get(spreadsheetId=self.sheet_id, range=f"{self.sheet_name}!1:1").execute().get("values", [[]])[0]
        updated = list(existing)
        changed = False
        for header in RESULT_HEADERS:
            if header not in updated:
                updated.append(header)
                changed = True
        if changed:
            self.values.update(
                spreadsheetId=self.sheet_id,
                range=f"{self.sheet_name}!1:1",
                valueInputOption="RAW",
                body={"values": [updated]},
            ).execute()

    def _headers(self) -> list[str]:
        self.ensure_headers()
        return self.values.get(spreadsheetId=self.sheet_id, range=f"{self.sheet_name}!1:1").execute().get("values", [[]])[0]

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=20), reraise=True)
    def pending_rows(self) -> list[SheetRow]:
        headers = self._headers()
        checked_idx = headers.index("Последняя проверка")
        rng = f"{self.sheet_name}!A{self.start_row}:{_col(max(checked_idx + 1, 1))}"
        rows = self.values.get(spreadsheetId=self.sheet_id, range=rng).execute().get("values", [])
        pending: list[SheetRow] = []
        for offset, row in enumerate(rows, start=self.start_row):
            url = row[0].strip() if row else ""
            checked = row[checked_idx].strip() if len(row) > checked_idx else ""
            if url and not checked:
                pending.append(SheetRow(row_number=offset, url=url))
        logger.info("Loaded %s pending rows", len(pending))
        return pending

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=20), reraise=True)
    def write_result(self, row_number: int, result: ClassificationResult) -> None:
        headers = self._headers()
        start_col = headers.index("Инфобизнес") + 1
        end_col = headers.index("Последняя проверка") + 1
        values: list[Any] = [
            "Да" if result.is_infobiz else "Нет",
            result.category,
            result.subcategory,
            result.confidence,
            result.reason,
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
        ]
        self.values.update(
            spreadsheetId=self.sheet_id,
            range=f"{self.sheet_name}!{_col(start_col)}{row_number}:{_col(end_col)}{row_number}",
            valueInputOption="RAW",
            body={"values": [values]},
        ).execute()


def _col(number: int) -> str:
    result = ""
    while number:
        number, rem = divmod(number - 1, 26)
        result = chr(65 + rem) + result
    return result
