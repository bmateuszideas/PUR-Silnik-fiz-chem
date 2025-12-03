import traceback

for name in ['pandas', 'sklearn.metrics', 'joblib']:
    try:
        __import__(name)
        print(f"Imported {name} OK")
    except Exception as e:
        print(f"Failed to import {name}: {type(e).__name__}: {e}")
        traceback.print_exc()
