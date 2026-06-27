from __future__ import annotations

import html
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import pandas as pd
from vk_checker.models import CandidateClass, ExportRecord

VALIDATION_COLUMNS = [
    "url", "title", "description", "score", "candidate_class", "matched_positive_keywords",
    "matched_negative_keywords", "Human verdict",
]


@dataclass(frozen=True)
class QualityMetrics:
    total_labeled: int
    tp: int
    fp: int
    tn: int
    fn: int
    uncertain: int
    precision: float
    recall: float
    f1: float
    accuracy: float


def sample_rows(rows: list, count: int, seed: int | None = None) -> list:
    if count >= len(rows):
        return rows
    rng = random.Random(seed)
    return rng.sample(rows, count)


def records_to_validation_xlsx(records: list[ExportRecord], path: str) -> None:
    rows = []
    for record in records:
        scraped = record.scraped
        heuristic = record.heuristic
        rows.append({
            "url": record.url,
            "title": scraped.title if scraped else "",
            "description": scraped.description if scraped else "",
            "score": heuristic.score if heuristic else 0,
            "candidate_class": heuristic.candidate_class.value if heuristic else CandidateClass.LOW.value,
            "matched_positive_keywords": ", ".join(heuristic.matched_positive_keywords) if heuristic else "",
            "matched_negative_keywords": ", ".join(heuristic.matched_negative_keywords) if heuristic else "",
            "Human verdict": "",
        })
    df = pd.DataFrame(rows, columns=VALIDATION_COLUMNS)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output, index=False)


def validation_has_verdicts(path: str) -> bool:
    df = pd.read_excel(path).fillna("")
    if "Human verdict" not in df:
        return False
    return df["Human verdict"].astype(str).str.strip().ne("").any()


def analyze_validation_xlsx(path: str, report_path: str) -> QualityMetrics:
    df = pd.read_excel(path).fillna("")
    metrics = compute_metrics(df)
    recommendations = build_recommendations(df)
    write_quality_report(df, metrics, recommendations, report_path)
    return metrics


def compute_metrics(df: pd.DataFrame) -> QualityMetrics:
    tp = fp = tn = fn = uncertain = 0
    for _, row in df.iterrows():
        verdict = str(row.get("Human verdict", "")).strip().lower()
        predicted = str(row.get("candidate_class", "C")).strip().upper() in {"A", "B"}
        if verdict in {"не уверен", "неуверен", "?", "uncertain"}:
            uncertain += 1
            continue
        if verdict not in {"да", "нет", "yes", "no"}:
            continue
        actual = verdict in {"да", "yes"}
        if predicted and actual:
            tp += 1
        elif predicted and not actual:
            fp += 1
        elif not predicted and actual:
            fn += 1
        else:
            tn += 1
    labeled = tp + fp + tn + fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / labeled if labeled else 0.0
    return QualityMetrics(labeled, tp, fp, tn, fn, uncertain, precision, recall, f1, accuracy)


def build_recommendations(df: pd.DataFrame) -> dict[str, list[str]]:
    false_positive = _error_rows(df, predicted_positive=True, actual_positive=False)
    false_negative = _error_rows(df, predicted_positive=False, actual_positive=True)
    fp_pos = _counter(false_positive, "matched_positive_keywords")
    fp_neg = _counter(false_positive, "matched_negative_keywords")
    fn_pos = _counter(false_negative, "matched_positive_keywords")
    fn_text: Counter[str] = Counter()
    for _, row in false_negative.iterrows():
        for token in _tokens(f"{row.get('title', '')} {row.get('description', '')}"):
            fn_text[token] += 1
    return {
        "false_positive": [
            "Понизить веса или перенести в negative для частых FP positive-слов: " + _top(fp_pos),
            "Усилить отрицательные веса, если FP содержит: " + _top(fp_neg),
            "Проверить правила, которые дают A/B при низком score-margin около порога.",
        ],
        "false_negative": [
            "Добавить или повысить веса частых FN слов из текста: " + _top(fn_text),
            "Проверить, почему не сработали positive keywords: " + _top(fn_pos),
            "Добавить regex для формулировок записи/набора, встречающихся в FN.",
        ],
    }


def write_quality_report(df: pd.DataFrame, metrics: QualityMetrics, recommendations: dict[str, list[str]], path: str) -> None:
    score_values = [float(v) for v in df.get("score", pd.Series(dtype=float)).fillna(0).tolist()]
    class_counts = Counter(str(v).upper() for v in df.get("candidate_class", pd.Series(dtype=str)).fillna("C").tolist())
    fp = _error_rows(df, predicted_positive=True, actual_positive=False)
    fn = _error_rows(df, predicted_positive=False, actual_positive=True)
    body = f"""
<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>VK rules quality report</title>
<style>body{{font-family:Arial,sans-serif;margin:32px;color:#172033}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.card{{padding:16px;border:1px solid #dde3ee;border-radius:12px;background:#f8fafc}}table{{border-collapse:collapse;width:100%;margin:16px 0}}td,th{{border:1px solid #dde3ee;padding:8px;text-align:left}}.bad{{color:#b42318}}.good{{color:#027a48}}pre{{white-space:pre-wrap;background:#f6f8fa;padding:12px;border-radius:8px}}</style></head><body>
<h1>Quality report</h1>
<div class="cards">
{_card('Precision', metrics.precision)}{_card('Recall', metrics.recall)}{_card('F1', metrics.f1)}{_card('Accuracy', metrics.accuracy)}
</div>
<h2>Summary</h2>
<ul><li>Total labeled: {metrics.total_labeled}</li><li>Uncertain: {metrics.uncertain}</li><li>False positive: {metrics.fp}</li><li>False negative: {metrics.fn}</li></ul>
<h2>Confusion Matrix</h2>{_confusion_table(metrics)}
<h2>Candidate classes</h2>{_bar_svg(class_counts)}
<h2>Score distribution</h2>{_hist_svg(score_values)}
<h2>False Positive: top matched positive rules</h2><pre>{html.escape(_top(_counter(fp, 'matched_positive_keywords'), 30))}</pre>
<h2>False Negative: top words from title/description</h2><pre>{html.escape(_top_text(fn, 50))}</pre>
<h2>Recommendations</h2><h3>False Positive</h3><ul>{''.join(f'<li>{html.escape(x)}</li>' for x in recommendations['false_positive'])}</ul><h3>False Negative</h3><ul>{''.join(f'<li>{html.escape(x)}</li>' for x in recommendations['false_negative'])}</ul>
</body></html>
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(body, encoding="utf-8")


def _error_rows(df: pd.DataFrame, predicted_positive: bool, actual_positive: bool) -> pd.DataFrame:
    if df.empty:
        return df
    verdict = df["Human verdict"].astype(str).str.strip().str.lower()
    actual = verdict.isin(["да", "yes"])
    labeled = verdict.isin(["да", "нет", "yes", "no"])
    predicted = df["candidate_class"].astype(str).str.upper().isin(["A", "B"])
    return df[labeled & (predicted == predicted_positive) & (actual == actual_positive)]


def _counter(df: pd.DataFrame, column: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    if df.empty or column not in df:
        return counter
    for value in df[column].fillna(""):
        for item in str(value).split(","):
            item = item.strip()
            if item:
                counter[item] += 1
    return counter


def _tokens(text: str) -> Iterable[str]:
    for token in "".join(ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in text).split():
        if len(token) >= 4:
            yield token


def _top(counter: Counter[str], limit: int = 20) -> str:
    return ", ".join(f"{word} ({count})" for word, count in counter.most_common(limit)) or "нет данных"


def _top_text(df: pd.DataFrame, limit: int = 50) -> str:
    counter: Counter[str] = Counter()
    for _, row in df.iterrows():
        counter.update(_tokens(f"{row.get('title', '')} {row.get('description', '')}"))
    return _top(counter, limit)


def _card(title: str, value: float) -> str:
    return f'<div class="card"><strong>{html.escape(title)}</strong><br><span>{value:.3f}</span></div>'


def _confusion_table(m: QualityMetrics) -> str:
    return f"<table><tr><th></th><th>Actual yes</th><th>Actual no</th></tr><tr><th>Predicted candidate</th><td>{m.tp}</td><td class='bad'>{m.fp}</td></tr><tr><th>Predicted non-candidate</th><td class='bad'>{m.fn}</td><td>{m.tn}</td></tr></table>"


def _bar_svg(counts: Counter[str]) -> str:
    labels = ["A", "B", "C"]
    max_count = max([counts.get(label, 0) for label in labels] + [1])
    bars = []
    for idx, label in enumerate(labels):
        value = counts.get(label, 0)
        width = int(value / max_count * 360)
        y = 30 + idx * 35
        bars.append(f"<text x='0' y='{y + 14}'>{label}</text><rect x='40' y='{y}' width='{width}' height='22' fill='#2e90fa'/><text x='{50 + width}' y='{y + 15}'>{value}</text>")
    return f"<svg width='520' height='150'>{''.join(bars)}</svg>"


def _hist_svg(values: list[float]) -> str:
    if not values:
        return "<p>Нет данных</p>"
    buckets = Counter(int(v // 5) * 5 for v in values)
    keys = sorted(buckets)
    max_count = max(buckets.values())
    bars = []
    for idx, key in enumerate(keys[:30]):
        height = int(buckets[key] / max_count * 120)
        x = 25 + idx * 18
        y = 140 - height
        bars.append(f"<rect x='{x}' y='{y}' width='12' height='{height}' fill='#12b76a'/><text x='{x}' y='155' font-size='9' transform='rotate(45 {x},155)'>{key}</text>")
    return f"<svg width='640' height='190'>{''.join(bars)}</svg>"
