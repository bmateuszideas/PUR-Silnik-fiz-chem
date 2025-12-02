# TODO - PUR-MOLD-TWIN

Lista zadan dla Core Engine i Process Optimizer (MVP i kolejne fazy). Wszystko w UTF-8.

> Notatka: po kazdej pracy nad konkretnym punktem TODO1 dopisz wpis do odpowiadajacego `admin/TODO1_PKT{n}_changelog.md` (data, lista zmodyfikowanych plikow, krotki opis celu). Jezeli nie mozesz wykonac kroku, nie zgaduj wyniku - opisz problem w tym samym changelogu i dodaj pod danym podpunktem linie `> Problem: ...` do czasu rozwiazania.

## 1. Definicja modelu i wymagania
- [x] Sformalizowac liste zjawisk (chemia, cieplo, ekspansja, cisnienie, odpowietrzniki, twardosc, demold). -> `docs/MODEL_OVERVIEW.md`
- [x] Zdefiniowac pelna specyfikacje I/O (nazwy, jednostki, zakresy). -> `docs/MODEL_OVERVIEW.md`
- [x] Ustalic progi jakosci: `alpha_demold_min`, `H_demold_min`, `H_24h_min`, zakres `rho_moulded`, `defect_risk_max`. -> `docs/MODEL_OVERVIEW.md`
- [x] Ustalic ograniczenia procesowe: `p_max_allowable_bar`, `t_cycle_max`. -> `docs/MODEL_OVERVIEW.md`
- [x] Ustalic kryteria dokladnosci MVP: dopuszczalne bledy `t_demold_opt`, `rho_moulded`, `p_max`. -> `docs/MODEL_OVERVIEW.md`
- [x] Potwierdzic stosowany stack/biblioteki wg `py_lib.md` (Python 3.14). -> `docs/MODEL_OVERVIEW.md`

## 2. Material DB
- [x] Zaprojektowac strukture danych na materialy (poliole, izo, gazy, parametry mechaniczne). -> `src/pur_mold_twin/material_db/models.py`
- [x] Wybrac 1-2 realne systemy do form (z pentanem lub bez) z TDS. -> `configs/systems/system_R1.yaml`, `configs/systems/system_M1.yaml`
- [x] Wypelnic Material DB: `OH_number`, `%NCO`, `density`, `viscosity`, `water_pct`, `pentane_pct`, `cream/gel/rise/tack_free`, `rho_free_rise_target`, `rho_moulded_target`, `H_24h_target`. -> `configs/systems/*`

## 3. Core Engine - MVP 0D (chemia, cieplo, ekspansja CO2)
- [x] Model kinetyczny `alpha(t)` (Arrhenius/empiryczny), parametry do kalibracji, powiazanie z czasami cream/gel/rise. -> `src/pur_mold_twin/core/mvp0d.py`
- [x] Bilans ciepla: zrodlo reakcyjne, pojemnosc cieplna pianki i formy, uproszczona wymiana z otoczeniem. -> `src/pur_mold_twin/core/mvp0d.py`
- [x] Ekspansja CO2: mole CO2 -> objetosc gazu; kalibracja do `rho_free_rise` / `rho_moulded`. -> `src/pur_mold_twin/core/mvp0d.py`
- [x] Polaczenie `alpha(t)`, `T(t)`, `rho(t)`; wyznaczenie `t_demold_min/max` dla prostych progow. -> `src/pur_mold_twin/core/mvp0d.py`
- [x] Wprowadzenie `mixing_eff` jako proxy jednorodnosci (wplyw na rozrzut lokalny). -> `src/pur_mold_twin/core/mvp0d.py`

## 4. Wilgotnosc i efektywna woda
- [x] Zdefiniowac `water_eff`: `water_from_polyol` + skladnik z `RH_ambient`. -> `src/pur_mold_twin/core/mvp0d.py`
- [x] Powiazac `water_eff` z generacja CO2 oraz wplywem na gestosc i ryzyko defektow (`water_risk_score`, nowe wyniki). -> `src/pur_mold_twin/core/mvp0d.py`, `docs/*`

## 5. Pentan i model cisnienia
- [x] Model odparowania pentanu (cisnienie pary vs T/p, podzial ciekla/gazowa faza w czasie). -> `src/pur_mold_twin/core/mvp0d.py`
- [x] Powietrze startowe: objetosc wnetki, cisnienie poczatkowe. -> `src/pur_mold_twin/core/mvp0d.py`
- [x] Modele cisnienia: `p_air(t)`, `p_CO2(t)`, `p_pentane(t)`, `p_total(t)`. -> `src/pur_mold_twin/core/mvp0d.py`, `readme.md`, `docs/MODEL_OVERVIEW.md`, `docs/USE_CASES.md`
- [x] Powiazanie `p_total(t)` z `p_max_allowable_bar` i flagami bezpieczenstwa (SAFE / NEAR_LIMIT / OVER_LIMIT). -> `src/pur_mold_twin/core/mvp0d.py`, `docs/*`

## 6. Odpowietrzniki i `vent_eff(t)`
- [x] Struktura `Vent`: polozenie, wymiary, przepustowosc bazowa. -> `src/pur_mold_twin/core/mvp0d.py`
- [x] Model `vent_eff(t)`: zaleznosc od czasu/frontu/lokalnej `alpha`, spadek 1 -> 0 przy zalepianiu kanalu. -> `src/pur_mold_twin/core/mvp0d.py`
- [x] Przeplyw gazu przez venty: funkcja `vent_eff(t)`, roznicy cisnien i parametrow kanalu. -> `src/pur_mold_twin/core/mvp0d.py`
- [x] Kryterium zamkniecia (np. `vent_eff < 0.1`). -> `src/pur_mold_twin/core/mvp0d.py`, `docs/USE_CASES.md`

> Paczka (a) = paragrafy 5-6 (uzupelnione powyzej). Paczka (b) obejmie kolejne prace nad paragrafami 7-8 (`twardosc/demold + diagnostyka`).

## 7. Jakosc, twardosc, demold
- [x] Funkcja `H = f(alpha, rho)`; wybor modelu startowego, parametry do kalibracji. -> `src/pur_mold_twin/core/mvp0d.py`
- [x] Definicje `H_demold`/`alpha_demold`, `H_24h`/`alpha_24h`. -> `src/pur_mold_twin/core/mvp0d.py`, `docs/*`
- [x] Logika demold: liczenie `t_demold_min`, `t_demold_max`, `t_demold_opt`, bufory bezpieczenstwa. -> `src/pur_mold_twin/core/mvp0d.py`

## 8. Diagnoza i reguly QC (bez ML)
- [x] Spis typowych defektow i przyczyn (baza wiedzy) -> heurystyki `diagnostics`. -> `src/pur_mold_twin/core/mvp0d.py`
- [x] Reguly: zimne komponenty/forma, za duzo/za malo wody (`water_eff` + `water_risk_score`), niska `mixing_eff`, `vent_eff` spada za szybko, demold za wczesnie/pozno. -> `src/pur_mold_twin/core/mvp0d.py`, `docs/USE_CASES.md`
- [x] Wynik: lista ostrzezen + przypisane `defect_risk` (`quality_status`). -> `src/pur_mold_twin/core/mvp0d.py`, `readme.md`, `docs/MODEL_OVERVIEW.md`

> Paczka (b) = paragrafy 7-8 (powyzsze). Dalsze prace przechodza do paragrafow 9+.

## 9. Process Optimizer - definicja problemu
- [x] Zmienne decyzyjne: min/max dla `T_polyol_in`, `T_iso_in`, `T_mold_init`, zakres `t_demold`, dopuszczalne korekty `pentane_pct`/`water_pct`. -> `src/pur_mold_twin/optimizer/search.py`
- [x] Ograniczenia: `p_max <= p_max_allowable_bar`, `alpha_demold >= alpha_demold_min`, `H_demold >= H_demold_min`, `H_24h >= H_24h_min`, `rho_moulded` w `[rho_min, rho_max]`, `t_demold <= t_cycle_max`, `defect_risk <= defect_risk_max`. -> `src/pur_mold_twin/optimizer/constraints.py`
- [x] Funkcje celu: minimalizacja `t_demold`; drugorzednie minimalizacja `p_max`, wrazliwosc na RH. -> `src/pur_mold_twin/optimizer/search.py`

## 10. Process Optimizer - implementacja
- [x] Wybrac podejscie: grid/random search na start; docelowo `scipy.optimize`/`pyomo`/inny solver. -> `src/pur_mold_twin/optimizer/search.py`
- [x] Petla: generacja kandydatow, wywolanie Core Engine, filtracja constraints, wybor najlepszego wg funkcji celu. -> `src/pur_mold_twin/optimizer/search.py`
- [x] Raportowanie: nowe nastawy; przewidywane `p_max`, `t_demold`, `H`, `rho`; podsumowanie poprawy vs wejscie operatora. -> `src/pur_mold_twin/optimizer/search.py`, `readme.md`, `docs/USE_CASES.md`

> Paczka (c) = paragrafy 9-10 (Process Optimizer spec + implementacja) zrealizowane wspolnie dla spojnosci API i dokumentacji.

## 11. Kalibracja i walidacja
- [x] Format danych doswiadczalnych: `T_core(t)`, `T_mold(t)`, `p(t)`, `rho_moulded`, `H_demold`, `H_24h`, typ defektow. -> `docs/CALIBRATION.md`
- [x] Procedury kalibracji: kinetyka vs cream/gel/rise; cieplne vs T(t); pentan/venty vs p(t). -> `docs/CALIBRATION.md`
- [x] Walidacja MVP: policzyc bledy vs dane; sprawdzic, czy mieszcza sie w zalozonych progach. -> `docs/CALIBRATION.md`

> Paczka (d) = paragraf 11 (kalibracja/walidacja). Dokument referencyjny: `docs/CALIBRATION.md`.

## 12. ML i logi z hali (pozniej)
- [x] Zaprojektowac schemat logow procesu pod ML. -> `docs/ML_LOGGING.md`
- [x] Zdefiniowac featury (roznice symulacja vs rzeczywistosc, kluczowe parametry procesu). -> `docs/ML_LOGGING.md`
- [x] Zaplanowac modele: klasyfikacja defektow; regresja `defect_risk`; wsparcie diagnozy. -> `docs/ML_LOGGING.md`

## 13. Dokumentacja i standardy
- [x] Utrzymac pliki w UTF-8; stosowac konwencje nazewnictwa/jednostek/struktury repo (`standards.md`).
- [x] README ma odzwierciedlac aktualny zakres (Core Engine + Process Optimizer).
- [x] Use cases w docs: co najmniej jeden prosty (symulacja) i jeden problematyczny z optymalizacja.
- [x] Dokument biblioteki: `py_lib.md` jako referencja stacku na kolejne fazy.
