from __future__ import annotations

import asyncio
import json
import logging
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from vk_checker.models import ClassificationResult, CommunityData
from vk_checker.prompt import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, rpm: int) -> None:
        self.delay = 60 / rpm
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def wait(self) -> None:
        async with self._lock:
            loop = asyncio.get_running_loop()
            now = loop.time()
            wait_for = self.delay - (now - self._last)
            if wait_for > 0:
                await asyncio.sleep(wait_for)
            self._last = loop.time()


class OpenAIClassifier:
    def __init__(self, api_key: str, model: str, rpm: int, timeout: int) -> None:
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        self.limiter = RateLimiter(rpm)

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=30), retry=retry_if_exception_type(Exception), reraise=True)
    async def classify(self, data: CommunityData) -> ClassificationResult:
        await self.limiter.wait()
        logger.info("Classifying %s", data.url)
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": build_user_prompt(data)}],
            response_format={"type": "json_object"},
            temperature=0,
        )
        content = response.choices[0].message.content or "{}"
        return ClassificationResult.model_validate(json.loads(content))
