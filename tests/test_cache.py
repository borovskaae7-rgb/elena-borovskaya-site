from vk_checker.cache import ResultCache
from vk_checker.models import CandidateClass, CommunityData, HeuristicResult


def test_cache_hit_only_same_content(tmp_path):
    cache = ResultCache(str(tmp_path / "cache.sqlite3"))
    data = CommunityData(url="https://vk.com/a", title="Школа")
    digest = cache.content_hash(data)
    result = HeuristicResult(score=10, candidate_class=CandidateClass.HIGH, matched_positive_keywords=["школа"])
    cache.set(data.url, digest, result)
    assert cache.get(data.url, digest).candidate_class == CandidateClass.HIGH

    changed = CommunityData(url="https://vk.com/a", title="Магазин")
    assert cache.get(changed.url, cache.content_hash(changed)) is None
