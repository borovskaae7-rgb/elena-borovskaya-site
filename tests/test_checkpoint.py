from vk_checker.checkpoint import CheckpointManager
from vk_checker.models import ProcessingStats


def test_checkpoint_roundtrip(tmp_path):
    manager = CheckpointManager(str(tmp_path / "checkpoint.json"), every=1)
    stats = ProcessingStats(processed=10, total_score=12)
    manager.save(last_row=42, stats=stats, cache_entries=7)
    state = manager.load()
    assert state.last_row == 42
    assert state.cache_entries == 7
    assert state.stats["processed"] == 10
