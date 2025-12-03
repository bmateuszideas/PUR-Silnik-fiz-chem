import traceback
import sys

def main():
    try:
        from fastapi.testclient import TestClient  # type: ignore
        from src.pur_mold_twin.service.app import app  # type: ignore
        print("IMPORT_OK")
    except Exception:
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
