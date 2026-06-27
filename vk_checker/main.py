from __future__ import annotations

import asyncio
import logging
from vk_checker.browser import BrowserManager
from vk_checker.classifier import OpenAIClassifier
from vk_checker.config import Settings
from vk_checker.google_sheet import GoogleSheetClient
from vk_checker.logger import setup_logging
from vk_checker.scraper import VKScraper

logger = logging.getLogger(__name__)


async def process_row(row, browser: BrowserManager, scraper: VKScraper, classifier: OpenAIClassifier, sheet: GoogleSheetClient, semaphore: asyncio.Semaphore) -> None:
    async with semaphore:
        page = await browser.new_page()
        try:
            data = await scraper.scrape(page, row.url)
            result = await classifier.classify(data)
            await asyncio.to_thread(sheet.write_result, row.row_number, result)
            logger.info("Row %s processed: %s", row.row_number, result.category)
        except Exception:
            logger.exception("Failed to process row %s url %s", row.row_number, row.url)
        finally:
            await page.close()


async def run() -> None:
    settings = Settings.load()
    setup_logging(settings.log_level)
    sheet = GoogleSheetClient(settings.google_sheet_id, settings.google_service_account, settings.input_sheet_name, settings.input_column, settings.start_row)
    await asyncio.to_thread(sheet.ensure_headers)
    rows = await asyncio.to_thread(sheet.pending_rows)
    classifier = OpenAIClassifier(settings.openai_api_key, settings.model, settings.openai_rpm, settings.request_timeout)
    scraper = VKScraper()
    semaphore = asyncio.Semaphore(settings.max_concurrent)
    async with BrowserManager(settings.profile_dir, settings.headless) as browser:
        tasks = [process_row(row, browser, scraper, classifier, sheet, semaphore) for row in rows]
        for batch_start in range(0, len(tasks), max(settings.max_concurrent * 10, 10)):
            await asyncio.gather(*tasks[batch_start:batch_start + max(settings.max_concurrent * 10, 10)])


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
