"""
Optional baseline models for defect risk/defect classification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:  # optional dependency
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    RandomForestClassifier = None
    RandomForestRegressor = None


@dataclass
class BaselineModels:
    defect_classifier: Optional[object]
    defect_risk_regressor: Optional[object]


def build_baseline_models() -> BaselineModels:
    if RandomForestClassifier is None or RandomForestRegressor is None:
        raise ImportError("scikit-learn not installed; install with pur-mold-twin[ml]")
    clf = RandomForestClassifier(n_estimators=50, random_state=0)
    reg = RandomForestRegressor(n_estimators=50, random_state=0)
    return BaselineModels(defect_classifier=clf, defect_risk_regressor=reg)
