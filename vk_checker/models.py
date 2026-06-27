from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from pydantic import BaseModel, Field


class RowStatus(StrEnum):
    PENDING = "pending"
    DONE = "done"
    ERROR = "error"


class CandidateClass(StrEnum):
    HIGH = "A"
    MEDIUM = "B"
    LOW = "C"


class CommunityData(BaseModel):
    url: str
    final_url: str = ""
    title: str = ""
    description: str = ""
    status: str = ""
    address: str = ""
    menu: list[str] = Field(default_factory=list)
    menu_links: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    pinned_post: str = ""
    recent_posts: list[str] = Field(default_factory=list)
    services: str = ""
    products: str = ""
    contacts: str = ""
    action_buttons: list[str] = Field(default_factory=list)
    activity: str = ""
    subscribers: str = ""
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def compact_text(self, max_chars: int = 8000) -> str:
        parts = [
            self.title,
            self.description,
            self.status,
            self.activity,
            self.address,
            " ".join(self.menu),
            " ".join(self.menu_links),
            " ".join(self.links),
            self.pinned_post,
            " ".join(self.recent_posts),
            self.services,
            self.products,
            self.contacts,
            " ".join(self.action_buttons),
        ]
        return "\n".join(part.strip() for part in parts if part and part.strip())[:max_chars]


class ExtractedSignals(BaseModel):
    phones: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)
    site: str = ""
    telegram_mentions: list[str] = Field(default_factory=list)
    whatsapp_mentions: list[str] = Field(default_factory=list)
    course_mentions: list[str] = Field(default_factory=list)
    education_mentions: list[str] = Field(default_factory=list)
    webinar_mentions: list[str] = Field(default_factory=list)
    mentorship_mentions: list[str] = Field(default_factory=list)
    consultation_mentions: list[str] = Field(default_factory=list)
    marathon_mentions: list[str] = Field(default_factory=list)
    intensive_mentions: list[str] = Field(default_factory=list)
    external_links: list[str] = Field(default_factory=list)


class HeuristicResult(BaseModel):
    score: int = 0
    candidate_class: CandidateClass = CandidateClass.LOW
    matched_positive_keywords: list[str] = Field(default_factory=list)
    matched_negative_keywords: list[str] = Field(default_factory=list)
    matched_patterns: list[str] = Field(default_factory=list)
    collected_text_size: int = 0
    signals: ExtractedSignals = Field(default_factory=ExtractedSignals)


class SheetRow(BaseModel):
    row_number: int
    url: str
    status: RowStatus = RowStatus.PENDING


class ExportRecord(BaseModel):
    row_number: int
    url: str
    status: str
    scraped: CommunityData | None = None
    heuristic: HeuristicResult | None = None
    error: str = ""


class ProcessingStats(BaseModel):
    processed: int = 0
    high_probability: int = 0
    medium_probability: int = 0
    low_probability: int = 0
    errors: int = 0
    total_score: int = 0
    total_seconds: float = 0.0
    last_row: int = 0

    @property
    def candidates(self) -> int:
        return self.high_probability + self.medium_probability

    @property
    def average_score(self) -> float:
        scored = self.high_probability + self.medium_probability + self.low_probability
        return self.total_score / scored if scored else 0.0
