from __future__ import annotations

import logging
import time
from collections import Counter
from vk_checker.models import ProcessingStats

logger = logging.getLogger(__name__)


class StatsReporter:
    def __init__(self, total: int, interval: int, stats: ProcessingStats, error_spike_threshold: float = 0.2) -> None:
        self.total = total
        self.interval = interval
        self.stats = stats
        self.started = time.monotonic()
        self.error_spike_threshold = error_spike_threshold
        self._last_errors = 0
        self._last_processed = 0

    def maybe_report(self) -> None:
        if self.stats.processed and self.stats.processed % self.interval == 0:
            self.report()

    def report(self) -> None:
        elapsed = max(time.monotonic() - self.started, 1)
        self.stats.total_seconds = elapsed
        rate = self.stats.processed / elapsed
        remaining = max(self.total - self.stats.processed, 0)
        eta = remaining / rate if rate else 0
        candidate_share = self.stats.candidates / self.stats.processed if self.stats.processed else 0
        error_share = self.stats.errors / self.stats.processed if self.stats.processed else 0
        avg_seconds = elapsed / self.stats.processed if self.stats.processed else 0
        logger.info(
            "Quality: processed=%s/%s candidates=%s candidate_share=%.2f high=%s medium=%s low=%s error_share=%.2f avg_score=%.2f avg_sec=%.2f eta_min=%.1f",
            self.stats.processed, self.total, self.stats.candidates, candidate_share, self.stats.high_probability,
            self.stats.medium_probability, self.stats.low_probability, error_share, self.stats.average_score, avg_seconds, eta / 60,
        )
        delta_processed = self.stats.processed - self._last_processed
        delta_errors = self.stats.errors - self._last_errors
        if delta_processed and delta_errors / delta_processed >= self.error_spike_threshold:
            logger.warning("Error rate spike detected: %.2f over last %s rows. VK layout or access restrictions may have changed.", delta_errors / delta_processed, delta_processed)
        self._last_processed = self.stats.processed
        self._last_errors = self.stats.errors


def print_stats(records: list, positive_counter: Counter[str], negative_counter: Counter[str]) -> str:
    total = len(records)
    candidates = sum(1 for r in records if r.heuristic and r.heuristic.candidate_class.value in {"A", "B"})
    scores = [r.heuristic.score for r in records if r.heuristic]
    lines = [
        f"Total communities: {total}",
        f"Candidates: {candidates}",
        f"Candidate percent: {(candidates / total * 100) if total else 0:.2f}%",
        f"Average score: {(sum(scores) / len(scores)) if scores else 0:.2f}",
        "Top positive words:",
        *[f"  {word}: {count}" for word, count in positive_counter.most_common(100)],
        "Top negative words:",
        *[f"  {word}: {count}" for word, count in negative_counter.most_common(100)],
    ]
    return "\n".join(lines)
