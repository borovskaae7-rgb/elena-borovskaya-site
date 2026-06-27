from __future__ import annotations

from datetime import datetime, timezone
from pydantic import BaseModel, Field, HttpUrl, field_validator


class CommunityData(BaseModel):
    url: str
    title: str = ""
    description: str = ""
    status: str = ""
    address: str = ""
    menu: list[str] = Field(default_factory=list)
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


class ClassificationResult(BaseModel):
    is_infobiz: bool
    category: str
    confidence: float = Field(ge=0, le=1)
    reason: str
    subcategory: str = ""
    offers: list[str] = Field(default_factory=list)

    @field_validator("category")
    @classmethod
    def non_empty_category(cls, value: str) -> str:
        return value.strip() or "Не относится"


class SheetRow(BaseModel):
    row_number: int
    url: str
