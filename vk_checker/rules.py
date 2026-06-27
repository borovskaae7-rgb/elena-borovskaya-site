from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import yaml
from vk_checker.models import CandidateClass, CommunityData, ExtractedSignals, HeuristicResult

PHONE_RE = re.compile(r"(?:(?:\+?7|8)[\s\-\(\)]*)?\d{3}[\s\-\)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
URL_RE = re.compile(r"https?://[^\s<>()\]\[{}\"']+", re.IGNORECASE)


@dataclass(frozen=True)
class PatternRule:
    name: str
    pattern: str
    weight: int


@dataclass(frozen=True)
class HeuristicRules:
    high_threshold: int
    medium_threshold: int
    positive_keywords: dict[str, int] = field(default_factory=dict)
    negative_keywords: dict[str, int] = field(default_factory=dict)
    required_patterns: list[PatternRule] = field(default_factory=list)
    forbidden_patterns: list[PatternRule] = field(default_factory=list)

    @classmethod
    def load(cls, path: str) -> "HeuristicRules":
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        thresholds = raw.get("thresholds", {})
        positive = {str(k): int(v) for k, v in (raw.get("positive_keywords") or {}).items()}
        positive.update({str(k): int(v) for k, v in (raw.get("very_positive_keywords") or {}).items()})
        negative = {str(k): int(v) for k, v in (raw.get("negative_keywords") or {}).items()}
        negative.update({str(k): int(v) for k, v in (raw.get("very_negative_keywords") or {}).items()})
        required = []
        for section in ("required_patterns", "regex_patterns", "phone_patterns", "telegram_patterns", "whatsapp_patterns", "email_patterns", "landing_patterns", "social_patterns"):
            required.extend(_patterns(raw.get(section) or {}))
        return cls(
            high_threshold=int(thresholds.get("high", 8)),
            medium_threshold=int(thresholds.get("medium", 3)),
            positive_keywords=positive,
            negative_keywords=negative,
            required_patterns=required,
            forbidden_patterns=_patterns(raw.get("forbidden_patterns") or {}),
        )


def _patterns(raw: dict[str, Any]) -> list[PatternRule]:
    return [PatternRule(name=str(name), pattern=str(value["pattern"]), weight=int(value["weight"])) for name, value in raw.items()]


class HeuristicScorer:
    def __init__(self, rules: HeuristicRules) -> None:
        self.rules = rules
        self.positive_counter: Counter[str] = Counter()
        self.negative_counter: Counter[str] = Counter()

    def evaluate(self, data: CommunityData) -> HeuristicResult:
        text = data.compact_text(max_chars=50_000)
        lowered = text.lower()
        signals = extract_signals(data)
        score = 0
        matched_positive: list[str] = []
        matched_negative: list[str] = []
        matched_patterns: list[str] = []

        for keyword, weight in self.rules.positive_keywords.items():
            if keyword.lower() in lowered:
                score += weight
                matched_positive.append(keyword)
                self.positive_counter[keyword] += 1
        for keyword, weight in self.rules.negative_keywords.items():
            if keyword.lower() in lowered:
                score += weight
                matched_negative.append(keyword)
                self.negative_counter[keyword] += 1
        for rule in self.rules.required_patterns:
            if re.search(rule.pattern, lowered, flags=re.IGNORECASE):
                score += rule.weight
                matched_patterns.append(rule.name)
                self.positive_counter[rule.name] += 1
        for rule in self.rules.forbidden_patterns:
            if re.search(rule.pattern, lowered, flags=re.IGNORECASE):
                score += rule.weight
                matched_patterns.append(rule.name)
                self.negative_counter[rule.name] += 1

        if score >= self.rules.high_threshold:
            candidate_class = CandidateClass.HIGH
        elif score >= self.rules.medium_threshold:
            candidate_class = CandidateClass.MEDIUM
        else:
            candidate_class = CandidateClass.LOW

        return HeuristicResult(
            score=score,
            candidate_class=candidate_class,
            matched_positive_keywords=matched_positive,
            matched_negative_keywords=matched_negative,
            matched_patterns=matched_patterns,
            collected_text_size=len(text),
            signals=signals,
        )


def extract_signals(data: CommunityData) -> ExtractedSignals:
    text = data.compact_text(max_chars=100_000)
    links = list(dict.fromkeys(data.links + URL_RE.findall(text)))
    external = [link for link in links if "vk.com" not in link.lower()]
    telegram = [item for item in links if "t.me/" in item.lower() or "telegram" in item.lower()]
    whatsapp = [item for item in links if "wa.me/" in item.lower() or "whatsapp" in item.lower()]
    return ExtractedSignals(
        phones=sorted(set(PHONE_RE.findall(text))),
        emails=sorted(set(EMAIL_RE.findall(text))),
        site=external[0] if external else "",
        telegram_mentions=sorted(set(telegram + re.findall(r"@\w{4,}", text))),
        whatsapp_mentions=sorted(set(whatsapp)),
        course_mentions=_context(text, r"курс\w*"),
        education_mentions=_context(text, r"обуч\w*"),
        webinar_mentions=_context(text, r"вебинар\w*"),
        mentorship_mentions=_context(text, r"наставнич\w*|наставник\w*"),
        consultation_mentions=_context(text, r"консультац\w*"),
        marathon_mentions=_context(text, r"марафон\w*"),
        intensive_mentions=_context(text, r"интенсив\w*"),
        external_links=sorted(set(external)),
    )


def _context(text: str, pattern: str, limit: int = 20) -> list[str]:
    result: list[str] = []
    for match in re.finditer(pattern, text, flags=re.IGNORECASE):
        start = max(match.start() - 80, 0)
        end = min(match.end() + 80, len(text))
        value = " ".join(text[start:end].split())
        if value not in result:
            result.append(value)
        if len(result) >= limit:
            break
    return result
