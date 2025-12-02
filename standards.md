# STANDARDS - PUR-MOLD-TWIN

Zasady dla Core Engine i Process Optimizer: jezyk, kodowanie, nazewnictwo, jednostki, struktura repo i use case w `docs/USE_CASES.md`. Wszystko w UTF-8.

## 1. Jezyk i kodowanie
- Kod, nazwy zmiennych/klas, dokumentacja: angielski (opcjonalnie polski bez znakow specjalnych).
- Pliki tekstowe (.py, .md, .yml itd.): UTF-8.

## 2. Nazewnictwo
- Zmienne/funkcje: `snake_case` (np. `alpha_demold`, `p_max`, `defect_risk`, `t_demold_opt`).
- Klasy/typy: `PascalCase` (np. `MaterialSystem`, `ProcessConditions`, `SimulationResult`).
- Stale: `UPPER_SNAKE_CASE`.
- Prefixy (spojne w Core Engine i Process Optimizer):
  - `T_` - temperatura (K wewnetrznie), np. `T_polyol_in`, `T_mold_init`.
  - `p_` - cisnienie (Pa wewnetrznie), np. `p_max`, `p_CO2`.
  - `rho_` - gestosc (kg/m3), np. `rho_moulded`.
  - `alpha_` - stopien utwardzenia (0-1), np. `alpha_demold`.
  - `m_` - masa (kg), np. `m_polyol`, `m_iso`.
  - `n_` - liczba moli (mol), np. `n_CO2`, `n_pentane_gas`.
  - `H_` - twardosc (Shore), np. `H_demold`, `H_24h`.
  - `RH_` - wilgotnosc wzgledna, np. `RH_ambient`.
- Nie dopisujemy jednostek w nazwach (`_C`, `_bar`); jednostki opisane nizej.

## 3. Jednostki (wewnatrz modelu)
- Temperatura: K (wejscie moze byc w C, konwertujemy na starcie).
- Cisnienie: Pa (wyjscie mozna prezentowac w bar).
- Masa: kg.
- Gestosc: kg/m3.
- Czas: s.
- RH: 0-1 (wejscie moze byc w %, konwersja na ulamek).
- Zasada: wszystko, co wchodzi do rownan, ma jednostki SI.

## 4. Struktura repo
- Kod (Core Engine + Process Optimizer + raporty): `src/pur_mold_twin/`
- Testy: `tests/` (m.in. `test_core_simulation.py`, `test_optimizer.py`, `test_cli.py`, `test_calibration*`, `test_etl.py`, `test_reporting.py`)
- Dokumentacja:
  - `agent_instructions.md`, `copilot_update_project_playbook.md`
  - `README.md`, `README_VERS.md`
  - `todo1.md` (oraz `todo2.md`, jesli aktywne)
  - `standards.md` (ten plik, root),
  - `docs/MODEL_OVERVIEW.md` (opis fizyki/chemii),
  - `docs/USE_CASES.md` (scenariusze uzycia),
  - `docs/CALIBRATION.md` (workflow kalibracji/walidacji),
  - `docs/ML_LOGGING.md` (logi procesowe i plan ML).
- Administracja:
  - `admin/TODO1_PKT{n}_changelog.md` / `admin/TODO2_PKT{n}_changelog.md` - wpisy agenta (data, lista plikow, opis celu) dla kazdego podpunktu TODO.
- Brak losowych skryptow w root; kod produkcyjny w `src/pur_mold_twin/`.
- Dane pomiarowe/ML: przechowuj lokalnie w `data/calibration/` i `data/ml/` (patrz `.gitignore`); repo trzyma tylko metadane/skrypty.
- Packaging/CI: konfiguracja w `pyproject.toml` (dependencies + extras, entry-point `pur-mold-twin`), workflow CI w `.github/workflows/ci.yml` uruchamia `pytest`.

## 6. Mapowanie nazw pola (wejscie vs solver)
- `T_polyol_in` → `T_polyol_in_C` (wejscie w °C, wewnetrznie K)
- `T_iso_in` → `T_iso_in_C`
- `T_mold_init` → `T_mold_init_C`
- `T_ambient` → `T_ambient_C`
- `p_max` (koncept) → `p_max_allowable_bar` (wejscie w bar, wewnetrznie Pa)

## 5. Use cases (`docs/USE_CASES.md`)
Plik musi zawierac co najmniej dwa scenariusze utrzymywane w zgodzie z API i zakresem:

1. **Use case 1 - podstawowa symulacja (Core Engine)**
   - Wejscie: wybor systemu z Material DB (`MaterialSystem`), `T_polyol_in`, `T_iso_in`, `T_mold_init`, `T_ambient`, `RH_ambient`, `m_polyol`, `m_iso`, `NCO_OH_index`, parametry formy, progi jakosci (`alpha_demold_min`, `H_demold_min`, zakres `rho_moulded`).
   - Wyjscie: profile `alpha(t)`, `T_core(t)`, `T_mold(t)`, `rho(t)`, `p_total(t)`, `vent_eff(t)`; `t_demold_min/max/opt`; `p_max`, `quality_status`, `pressure_status`, `defect_risk`; lista ostrzezen/diagnoz.

2. **Use case 2 - problematyczne ustawienia + Process Optimizer**
   - Wejscie: suboptymalne nastawy (niskie temperatury, wysoka RH, pentan wg TDS, typowy `t_demold`).
   - Core Engine: zbyt niskie `alpha_demold` / `H_demold`, `rho_moulded` poza zakresem, `p_max > p_max_allowable`, wysokie `defect_risk` z diagnozami (temperatury, RH, vent, pentan).
   - Process Optimizer: zmienne (`T_polyol_in`, `T_iso_in`, `T_mold_init`, `t_demold`, ew. `pentane_pct`), constraints (`p_max`, `alpha_demold`, `H`, `rho`, `t_cycle_max`, `defect_risk_max`), funkcja celu (min `t_demold`, drugorzednie min `p_max` i wrazliwosc na RH).
   - Wyjscie: nowy zestaw nastaw (temperatury, `t_demold`, korekta `pentane_pct`), prognozowane `p_max`, `H_demold`, `H_24h`, `rho_moulded`, `defect_risk`, opis poprawy.
