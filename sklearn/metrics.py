from __future__ import annotations

from typing import Iterable

def mean_absolute_error(y_true: Iterable[float], y_pred: Iterable[float]) -> float:
    y_true = list(y_true)
    y_pred = list(y_pred)
    if not y_true:
        return 0.0
    return sum(abs(a - b) for a, b in zip(y_true, y_pred)) / len(y_true)

def f1_score(y_true: Iterable[int], y_pred: Iterable[int]) -> float:
    # simple binary F1 for labels {0,1}
    y_true = list(y_true)
    y_pred = list(y_pred)
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    if tp == 0:
        return 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)
