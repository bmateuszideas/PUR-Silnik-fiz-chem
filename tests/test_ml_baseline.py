import types

import pytest

from pur_mold_twin.ml import baseline


def test_build_baseline_models_raises_when_sklearn_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(baseline, "RandomForestClassifier", None)
    monkeypatch.setattr(baseline, "RandomForestRegressor", None)

    with pytest.raises(ImportError):
        baseline.build_baseline_models()


def test_build_baseline_models_with_dummy_classes(monkeypatch: pytest.MonkeyPatch) -> None:
    class _DummyEstimator:
        def __init__(self, *args, **kwargs):
            self.init_args = args
            self.init_kwargs = kwargs

    dummy_module = types.SimpleNamespace(RandomForestClassifier=_DummyEstimator, RandomForestRegressor=_DummyEstimator)
    monkeypatch.setattr(baseline, "RandomForestClassifier", dummy_module.RandomForestClassifier)
    monkeypatch.setattr(baseline, "RandomForestRegressor", dummy_module.RandomForestRegressor)

    models = baseline.build_baseline_models()

    assert isinstance(models.defect_classifier, _DummyEstimator)
    assert isinstance(models.defect_risk_regressor, _DummyEstimator)
