import importlib

modules = ['pandas','sklearn','joblib','sklearn.ensemble']
for m in modules:
    try:
        mod = importlib.import_module(m)
        print(m, 'OK', getattr(mod, '__version__', 'no-version'))
    except Exception as e:
        print(m, 'ERROR', type(e).__name__, e)
