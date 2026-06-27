from __future__ import annotations

import logging
from urllib.parse import urljoin
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential
from vk_checker.browser import human_delay
from vk_checker.config import ScrapingConfig
from vk_checker.rate_limit import AsyncRateLimiter
from vk_checker.models import CommunityData

logger = logging.getLogger(__name__)


async def _texts(page: Page, selectors: list[str], limit: int = 20) -> list[str]:
    seen: list[str] = []
    for selector in selectors:
        loc = page.locator(selector)
        try:
            count = min(await loc.count(), limit)
            for i in range(count):
                text = (await loc.nth(i).inner_text(timeout=2500)).strip()
                if text and text not in seen:
                    seen.append(text)
        except PlaywrightTimeoutError:
            logger.debug("Selector timed out: %s", selector)
    return seen


async def _first_text(page: Page, selectors: list[str]) -> str:
    for selector in selectors:
        loc = page.locator(selector).first
        try:
            if await loc.count():
                tag = await loc.evaluate("el => el.tagName.toLowerCase()", timeout=2500)
                if tag == "meta":
                    text = (await loc.get_attribute("content", timeout=2500) or "").strip()
                else:
                    text = (await loc.inner_text(timeout=2500)).strip()
                if text:
                    return text
        except PlaywrightTimeoutError:
            continue
    return ""


class VKScraper:
    def __init__(self, config: ScrapingConfig, limiter: AsyncRateLimiter | None = None) -> None:
        self.config = config
        self.limiter = limiter

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=12), reraise=True)
    async def scrape(self, page: Page, url: str) -> CommunityData:
        logger.info("Scraping %s", url)
        if self.limiter:
            await self.limiter.wait()
        page.set_default_navigation_timeout(self.config.navigation_timeout_ms)
        await page.goto(url, wait_until="domcontentloaded")
        try:
            await page.wait_for_load_state("networkidle", timeout=min(self.config.navigation_timeout_ms, 15_000))
        except PlaywrightTimeoutError:
            logger.debug("Network idle timed out for %s; continuing with DOM content", url)
        await page.locator("body").wait_for(state="attached", timeout=10_000)
        await human_delay(page)
        await page.mouse.wheel(0, 900)
        await human_delay(page, 300, 900)

        title = await _first_text(page, ["h1", "[class*='page_name']", "[class*='group_name']", "[data-testid*='group-title']", "meta[property='og:title']"])
        if not title:
            title = await page.title()
        description = await _first_text(page, ["[class*='group_description']", "[class*='page_description']", "[data-testid*='description']", "meta[property='og:description']", "meta[name='description']"])
        status = await _first_text(page, ["[class*='current_text']", "[class*='status']"])
        address = await _first_text(page, ["[class*='address']", "[data-testid*='address']"])
        activity = await _first_text(page, ["[class*='group_activity']", "[class*='page_category']"])
        subscribers = await _first_text(page, ["[class*='page_counter']", "[class*='followers']", "[class*='subscribers']"])

        menu_selectors = ["nav a", "[class*='menu'] a", "[class*='Tabs'] a"]
        menu = await _texts(page, menu_selectors, 30)
        menu_links: list[str] = []
        for selector in menu_selectors:
            for href in await page.locator(f"{selector}[href]").evaluate_all("els => els.map(a => a.href).filter(Boolean)"):
                if str(href) not in menu_links:
                    menu_links.append(str(href))
        contacts = "\n".join(await _texts(page, ["[class*='contacts']", "[data-testid*='contacts']"], 10))
        action_buttons = await _texts(page, ["button", "[role='button']", "[class*='Button']"], 30)
        links = []
        for href in await page.locator("a[href]").evaluate_all("els => els.map(a => a.href).filter(Boolean)"):
            absolute = urljoin(url, str(href))
            if absolute not in links:
                links.append(absolute)
            if len(links) >= self.config.max_links:
                break

        posts = await _texts(page, ["[class*='post_text']", "[data-testid*='post']", "article"], self.config.max_posts + 3)
        pinned_post = posts[0] if posts else ""
        recent_posts = posts[1:self.config.max_posts + 1] if len(posts) > 1 else posts[: self.config.max_posts]
        services = "\n".join(await _texts(page, ["[class*='services']", "[data-testid*='services']"], 10))
        products = "\n".join(await _texts(page, ["[class*='market']", "[class*='goods']", "[data-testid*='market']"], 10))

        data = CommunityData(
            url=url, final_url=page.url, title=title, description=description, status=status, address=address, menu=menu,
            menu_links=menu_links, links=links, pinned_post=pinned_post, recent_posts=recent_posts, services=services,
            products=products, contacts=contacts, action_buttons=action_buttons, activity=activity,
            subscribers=subscribers,
        )
        if len(data.compact_text()) > self.config.max_text_chars:
            data.description = data.description[: self.config.max_text_chars]
        return data
