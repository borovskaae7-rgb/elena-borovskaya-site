import pytest
from vk_checker.classifier import NoopClassifier
from vk_checker.models import CommunityData, HeuristicResult


@pytest.mark.asyncio
async def test_noop_classifier_interface_returns_heuristic():
    result = HeuristicResult(score=1)
    assert await NoopClassifier().classify(CommunityData(url="https://vk.com/a"), result) is result
