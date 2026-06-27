import pandas as pd
from vk_checker.validation import compute_metrics, sample_rows


def test_sample_rows_is_deterministic():
    rows = list(range(20))
    assert sample_rows(rows, 5, seed=42) == sample_rows(rows, 5, seed=42)


def test_compute_metrics_binary_candidates():
    df = pd.DataFrame([
        {"candidate_class": "A", "Human verdict": "Да"},
        {"candidate_class": "B", "Human verdict": "Нет"},
        {"candidate_class": "C", "Human verdict": "Да"},
        {"candidate_class": "C", "Human verdict": "Нет"},
        {"candidate_class": "A", "Human verdict": "Не уверен"},
    ])
    metrics = compute_metrics(df)
    assert metrics.tp == 1
    assert metrics.fp == 1
    assert metrics.fn == 1
    assert metrics.tn == 1
    assert metrics.uncertain == 1
    assert metrics.precision == 0.5
    assert metrics.recall == 0.5
    assert metrics.f1 == 0.5
    assert metrics.accuracy == 0.5
