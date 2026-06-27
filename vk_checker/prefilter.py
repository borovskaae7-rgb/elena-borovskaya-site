from __future__ import annotations

from vk_checker.models import CommunityData, HeuristicResult
from vk_checker.rules import HeuristicScorer


def evaluate_heuristics(data: CommunityData, scorer: HeuristicScorer) -> HeuristicResult:
    return scorer.evaluate(data)
