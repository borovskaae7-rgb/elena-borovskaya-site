from __future__ import annotations

import random
from pathlib import Path
from playwright.async_api import BrowserContext, Page, Playwright, async_playwright


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


class BrowserManager:
    def __init__(self, profile_dir: Path, headless: bool) -> None:
        self.profile_dir = profile_dir
        self.headless = headless
        self.playwright: Playwright | None = None
        self.context: BrowserContext | None = None

    async def __aenter__(self) -> "BrowserManager":
        self.playwright = await async_playwright().start()
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.profile_dir),
            headless=self.headless,
            user_agent=USER_AGENT,
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            viewport={"width": 1366, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        self.context.set_default_timeout(30_000)
        return self

    async def __aexit__(self, *_: object) -> None:
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()

    async def new_page(self) -> Page:
        if not self.context:
            raise RuntimeError("Browser context is not started")
        page = await self.context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return page


async def human_delay(page: Page, minimum_ms: int = 450, maximum_ms: int = 1800) -> None:
    await page.wait_for_timeout(random.randint(minimum_ms, maximum_ms))
