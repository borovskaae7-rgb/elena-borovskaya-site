from vk_checker.models import CandidateClass, CommunityData
from vk_checker.rules import HeuristicRules, HeuristicScorer, PatternRule


def test_heuristic_scores_high_candidate():
    rules = HeuristicRules(high_threshold=8, medium_threshold=3, positive_keywords={"курс": 5, "школа": 6}, negative_keywords={"кафе": -10})
    result = HeuristicScorer(rules).evaluate(CommunityData(url="https://vk.com/a", title="Школа", description="курс"))
    assert result.score == 11
    assert result.candidate_class == CandidateClass.HIGH
    assert result.matched_positive_keywords == ["курс", "школа"]


def test_heuristic_scores_low_negative_candidate():
    rules = HeuristicRules(high_threshold=8, medium_threshold=3, positive_keywords={"курс": 5}, negative_keywords={"кафе": -10})
    result = HeuristicScorer(rules).evaluate(CommunityData(url="https://vk.com/a", title="кафе"))
    assert result.score == -10
    assert result.candidate_class == CandidateClass.LOW
    assert result.matched_negative_keywords == ["кафе"]


def test_heuristic_patterns_add_score():
    rules = HeuristicRules(high_threshold=8, medium_threshold=3, required_patterns=[PatternRule("telegram", r"t\.me/", 3)])
    result = HeuristicScorer(rules).evaluate(CommunityData(url="https://vk.com/a", links=["https://t.me/example"]))
    assert result.score == 3
    assert result.candidate_class == CandidateClass.MEDIUM
