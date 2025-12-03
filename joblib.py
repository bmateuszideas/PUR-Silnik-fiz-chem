import pickle
from pathlib import Path

def dump(obj, path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('wb') as f:
        pickle.dump(obj, f)

def load(path):
    with open(path, 'rb') as f:
        return pickle.load(f)
