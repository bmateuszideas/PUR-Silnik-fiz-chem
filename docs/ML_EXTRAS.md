ML extras — instalacja
======================

Ten dokument wyjaśnia jak zainstalować opcjonalne pakiety ML wykorzystywane przez projekt.

Dlaczego: niektóre testy oraz funkcje treningu/inferencji wymagają `scikit-learn` i `joblib`. Projekt działa bez nich, ale jeżeli chcesz uruchomić ML testy lokalnie lub w CI, wykonaj poniższe kroki.

Szybka instalacja (PowerShell):

```powershell
pip install scikit-learn joblib
```

W CI:

- Dodaj krok instalacji powyższych pakietów przed uruchomieniem testów lub użyj obrazu środowiskowego, który już zawiera te pakiety.
- Alternatywnie trzymaj testy ML oznaczone jako "optional/skip" i uruchamiaj je tylko w dedykowanym jobie (np. `ml`), aby ograniczyć czas i zależności dla podstawowego pipeline'u.

Uwagi:

- `scikit-learn` dostarcza gotowe modele i narzędzia ML (RandomForest, LogisticRegression itp.).
- `joblib` jest używane do serializacji modeli i cache'owania. Można stosować alternatywy, ale są to standardowe dependency dla sk-learn.

Jeśli chcesz, mogę teraz spróbować zainstalować te pakiety w tym środowisku i uruchomić testy, aby potwierdzić, że skip zniknie.

CLI i manifest modeli
---------------------

Nowe narzędzie treningowe (`train_baseline.py`) zapisuje dodatkowe metadane dotyczące wytrenowanych artefaktów do pliku `models/manifest.json`. Poniżej znajdziesz opis dostępnych opcji CLI oraz schematu manifestu.

- Flagi CLI:
  - `--model-version`: jawna wersja modelu (np. `1.0.0`). Wartość jest zapisywana w manifestrze jako `version`.
  - `--seed`: wartość ziarna losowości używana do powtarzalnego treningu. Zapisana jako `training_seed` w manifestrze.

- Co zapisuje manifest (`models/manifest.json`):
  - `version`: wersja modelu (string). Pochodzi z `--model-version` lub domyślna wersja generowana przez skrypt.
  - `created`: znacznik czasu utworzenia modelu w formacie ISO (UTC, z informacją o strefie czasowej), np. `2025-12-03T12:34:56+00:00`.
  - `git_sha`: opcjonalny skrót commita (`git rev-parse --short HEAD`) — jeśli repo jest dostępne w środowisku treningowym.
  - `requirements_hash`: opcjonalny SHA256 pliku `pyproject.toml` (lub innego pliku zależności), przydatny do śledzenia środowiska zależności.
  - `sha256`: SHA256 artefaktu modelu (plików zapisywanych w `models/`), używany do weryfikacji integralności.
  - `training_seed`: wartość z `--seed`, jeśli została podana.
  - `dataset_fingerprint`: SHA256 pliku cech (np. pliku `features.parquet`) użyty do treningu; pomaga powiązać model z danymi treningowymi.

Przykładowy wpis w `models/manifest.json`:

```json
{
  "models": [
    {
      "name": "baseline_rf",
      "version": "1.0.0",
      "created": "2025-12-03T12:34:56+00:00",
      "git_sha": "a1b2c3d",
      "requirements_hash": "e3b0c44298fc1c149afbf4c8996fb924...",
      "sha256": "d2d2f3...",
      "training_seed": 42,
      "dataset_fingerprint": "9f86d081884c7d659a2feaa0c55ad015..."
    }
  ]
}
```

Jak generować `dataset_fingerprint` i `sha256`:

- `dataset_fingerprint` to po prostu SHA256 pliku zawierającego cechy (np. `features.parquet`). Przykład w PowerShell:

```powershell
Get-FileHash .\data\features.parquet -Algorithm SHA256 | Select-Object -ExpandProperty Hash
```

`sha256` modelu to SHA256 pliku artefaktu zapisanego w katalogu `models/`; można go obliczyć analogicznie, np. `Get-FileHash models\baseline_rf.joblib -Algorithm SHA256`.

Integracja z inferencją i testami:

- `src/pur_mold_twin/ml/inference.py` odczytuje `models/manifest.json` (jeśli istnieje) i dołącza metadane manifestu do wyników predykcji. Skrypt porównuje też wartość `sha256` z manifestu z rzeczywistym SHA256 pliku modelu i dołącza pola pomocnicze (`sha256_match`, `sha256_actual`) do metadanych.

Uwagi praktyczne:

- Manifest ułatwia śledzenie pochodzenia modeli w testach i produkcji — upewnij się, że pipeline treningowy zapisuje plik `models/manifest.json` wraz z artefaktami.
- W CI dodano krok wysyłki wyników pokrycia do Codecov (`Upload coverage to Codecov`). Jeśli repozytorium jest prywatne, dodaj sekret `CODECOV_TOKEN` w ustawieniach repo przed oczekiwaniem na raporty w Codecov.

Jeśli chcesz, mogę dodatkowo zaktualizować fragment README lub dodać krótką pomoc CLI (przykłady użycia) do `docs/`.
