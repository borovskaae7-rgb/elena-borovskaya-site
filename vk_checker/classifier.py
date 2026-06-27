from __future__ import annotations

from abc import ABC, abstractmethod
from vk_checker.models import CommunityData, HeuristicResult


class BaseClassifier(ABC):
    """Optional integration point for future AI classifiers such as BotHelp AI."""

    @abstractmethod
    async def classify(self, data: CommunityData, heuristic: HeuristicResult) -> HeuristicResult:
        """Return an enriched result. The default project pipeline does not call AI."""


class NoopClassifier(BaseClassifier):
    async def classify(self, data: CommunityData, heuristic: HeuristicResult) -> HeuristicResult:
        return heuristic
