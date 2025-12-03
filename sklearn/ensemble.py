class RandomForestClassifier:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    def fit(self, X, y):
        # no-op: store a trivial model
        y_list = list(y) if y is not None else []
        self._classes = list(dict.fromkeys(y_list)) if y_list else []
        return self
    def predict(self, X):
        # predict first class for all
        if getattr(self, "_classes", None):
            return [self._classes[0] for _ in range(len(X))]
        return [0 for _ in range(len(X))]

class RandomForestRegressor:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    def fit(self, X, y):
        y_list = list(y) if y is not None else []
        self._mean = sum(y_list) / len(y_list) if y_list else 0.0
        return self
    def predict(self, X):
        return [getattr(self, "_mean", 0.0) for _ in range(len(X))]
