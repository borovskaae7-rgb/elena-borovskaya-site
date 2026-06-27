from __future__ import annotations

import logging
from urllib.parse import urljoin
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential
from vk_checker.browser import human_delay
from vk_checker.models import CommunityData

logger = logging.getLogger(__name__)


async def _texts(page: Page, selectors: list[str], limit: int = 20) -> list[str]:
    seen: list[str] = []
    for selector in selectors:
        loc = page.locator(selector)
        count = min(await loc.count(), limit)
        for i in range(count):
            text = (await loc.nth(i).inner_text()).strip()
            if text and text not in seen:
                seen.append(text)
    return seen


async def _first_text(page: Page, selectors: list[str]) -> str:
    for selector in selectors:
        loc = page.locator(selector).first
        try:
            if await loc.count():
                text = (await loc.inner_text(timeout=3000)).strip()
                if text:
                    return text
        except PlaywrightTimeoutError:
            continue
    return ""


class VKScraper:
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=12), reraise=True)
    async def scrape(self, page: Page, url: str) -> CommunityData:
        logger.info("Scraping %s", url)
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle", timeout=20_000)
        await human_delay(page)
        await page.mouse.wheel(0, 900)
        await human_delay(page, 300, 900)

        title = await _first_text(page, ["h1", "[class*='page_name']", "[class*='group_name']", "[data-testid*='group-title']"])
        description = await _first_text(page, ["[class*='group_description']", "[class*='page_description']", "[data-testid*='description']"])
        status = await _first_text(page, ["[class*='current_text']", "[class*='status']"])
        address = await _first_text(page, ["[class*='address']", "[data-testid*='address']"])
        activity = await _first_text(page, ["[class*='group_activity']", "[class*='page_category']"])
        subscribers = await _first_text(page, ["[class*='page_counter']", "[class*='followers']", "[class*='subscribers']"])

        menu = await _texts(page, ["nav a", "[class*='menu'] a", "[class*='Tabs'] a"], 30)
        contacts = "\n".join(await _texts(page, ["[class*='contacts']", "[data-testid*='contacts']"], 10))
        action_buttons = await _texts(page, ["button", "[role='button']", "[class*='Button']"], 30)
        links = []
        for href in await page.locator("a[href]").evaluate_all("els => els.map(a => a.href).filter(Boolean)"):
            absolute = urljoin(url, str(href))
            if absolute not in links:
                links.append(absolute)
            if len(links) >= 120:
                break

        posts = await _texts(page, ["[class*='post_text']", "[data-testid*='post']", "article"], 8)
        pinned_post = posts[0] if posts else ""
        recent_posts = posts[1:6] if len(posts) > 1 else posts[:5]
        services = "\n".join(await _texts(page, ["[class*='services']", "[data-testid*='services']"], 10))
        products = "\n".join(await _texts(page, ["[class*='market']", "[class*='goods']", "[data-testid*='market']"], 10))

        return CommunityData(
            url=url, title=title, description=description, status=status, address=address, menu=menu,
            links=links, pinned_post=pinned_post, recent_posts=recent_posts, services=services,
            products=products, contacts=contacts, action_buttons=action_buttons, activity=activity,
            subscribers=subscribers,
        )
