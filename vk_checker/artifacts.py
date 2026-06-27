from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from playwright.async_api import Page


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9а-яА-Я_.-]+", "_", value).strip("_")
    return cleaned[:120] or "page"


async def save_error_artifacts(page: Page, artifacts_dir: str, row_number: int, url: str) -> tuple[str, str]:
    root = Path(artifacts_dir) / "errors"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = root / f"row_{row_number}_{stamp}_{safe_name(url)}"
    html_path = base.with_suffix(".html")
    png_path = base.with_suffix(".png")
    html = await page.content()
    html_path.write_text(html, encoding="utf-8")
    await page.screenshot(path=str(png_path), full_page=True)
    return str(html_path), str(png_path)
