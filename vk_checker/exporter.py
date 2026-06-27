from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
from vk_checker.models import CandidateClass, ExportRecord, ProcessingStats


class Exporter:
    def __init__(self, output_dir: str) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, records: list[ExportRecord], stats: ProcessingStats) -> None:
        df = self._records_frame(records)
        df.to_csv(self.output_dir / "results.csv", index=False)
        df.to_excel(self.output_dir / "results.xlsx", index=False)
        errors = df[df["status"] == "error"] if not df.empty and "status" in df else pd.DataFrame()
        errors.to_csv(self.output_dir / "errors.csv", index=False)
        for candidate_class, stem in [(CandidateClass.HIGH, "high_probability"), (CandidateClass.MEDIUM, "medium_probability"), (CandidateClass.LOW, "low_probability")]:
            group = df[df["candidate_class"] == candidate_class.value] if not df.empty and "candidate_class" in df else pd.DataFrame()
            group.to_csv(self.output_dir / f"{stem}.csv", index=False)
            group.to_excel(self.output_dir / f"{stem}.xlsx", index=False)
        (self.output_dir / "statistics.json").write_text(stats.model_dump_json(indent=2), encoding="utf-8")

    def export_candidates(self, records: list[ExportRecord]) -> Path:
        df = self._records_frame(records)
        candidates = df[df["candidate_class"].isin([CandidateClass.HIGH.value, CandidateClass.MEDIUM.value])] if not df.empty else pd.DataFrame()
        path = self.output_dir / "candidates_for_bothelp.csv"
        candidates.to_csv(path, index=False)
        return path

    def export_dry_run(self, record: ExportRecord) -> None:
        dry_dir = self.output_dir / "dry_run"
        dry_dir.mkdir(parents=True, exist_ok=True)
        path = dry_dir / f"row_{record.row_number}.json"
        path.write_text(json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")

    def _records_frame(self, records: list[ExportRecord]) -> pd.DataFrame:
        rows = []
        for record in records:
            scraped = record.scraped
            heuristic = record.heuristic
            signals = heuristic.signals if heuristic else None
            rows.append({
                "row_number": record.row_number,
                "url": record.url,
                "status": record.status,
                "title": scraped.title if scraped else "",
                "description": scraped.description if scraped else "",
                "subscribers": scraped.subscribers if scraped else "",
                "score": heuristic.score if heuristic else "",
                "candidate_class": heuristic.candidate_class.value if heuristic else "",
                "matched_positive_keywords": ", ".join(heuristic.matched_positive_keywords) if heuristic else "",
                "matched_negative_keywords": ", ".join(heuristic.matched_negative_keywords) if heuristic else "",
                "collected_text_size": heuristic.collected_text_size if heuristic else 0,
                "phones": ", ".join(signals.phones) if signals else "",
                "emails": ", ".join(signals.emails) if signals else "",
                "site": signals.site if signals else "",
                "telegram_mentions": ", ".join(signals.telegram_mentions) if signals else "",
                "whatsapp_mentions": ", ".join(signals.whatsapp_mentions) if signals else "",
                "external_links": ", ".join(signals.external_links) if signals else "",
                "course_mentions": " | ".join(signals.course_mentions) if signals else "",
                "education_mentions": " | ".join(signals.education_mentions) if signals else "",
                "webinar_mentions": " | ".join(signals.webinar_mentions) if signals else "",
                "mentorship_mentions": " | ".join(signals.mentorship_mentions) if signals else "",
                "consultation_mentions": " | ".join(signals.consultation_mentions) if signals else "",
                "marathon_mentions": " | ".join(signals.marathon_mentions) if signals else "",
                "intensive_mentions": " | ".join(signals.intensive_mentions) if signals else "",
                "pinned_post": scraped.pinned_post if scraped else "",
                "recent_posts": " | ".join(scraped.recent_posts) if scraped else "",
                "contacts": scraped.contacts if scraped else "",
                "services": scraped.services if scraped else "",
                "products": scraped.products if scraped else "",
                "error": record.error,
            })
        return pd.DataFrame(rows)
