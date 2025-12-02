# Agent Instructions - PUR-MOLD-TWIN

Ten plik czyta kazdy agent / Copilot / Codex przed wykonaniem jakichkolwiek dzialan w repo.

## 1. Kontekst obowiazkowy
1. Przeczytaj w calosci:
   - `copilot_update_project_playbook.md` (workflow aktualizacji i zasady merge),
   - `readme.md`, `standards.md`, `docs/STRUCTURE.md`, `README_VERS.md`,
   - `todo1.md` (oraz `todo2.md`, jesli dotyczy biezacego zakresu prac),
   - `py_lib.md` (stack Pythona, biblioteki, Python 3.14),
   - przy fizyce/solverze: `docs/MODEL_OVERVIEW.md`, `docs/CALIBRATION.md`,
   - przy logach/ML: `docs/ML_LOGGING.md`,
   - przy use-case: `docs/USE_CASES.md`.
2. Przy danych referencyjnych: sprawdz `todo1.md` i odpowiednie sekcje README.
3. Asystent AI wspolpracujacy z autorem ma zakaz wprowadzania zmian w plikach z punktu 1 bez jawnego polecenia.

## 2. Ogolne zasady pracy agenta
1. **Python 3.14** jest obowiazkowy. Sprawdz `python -V` lub `py -3.14 -V`.
2. **UTF-8**: nie zapisuj plikow w innym kodowaniu, nie wstawiaj dziwnych znakow.
3. **Szanuj instrukcje**: kazda zmiana jest powiazana z zadaniem z `todo1.md`. W razie watpliwosci pytaj.
4. **Biblioteki**: instalujemy tylko to, co w `py_lib.md`. Core produkcyjny = `numpy`, `scipy` (solve_ivp), `pydantic`, `pint`, `ruamel.yaml`, `typer`, `pandas`; ML/backendy specjalne (scikit-learn, SUNDIALS, JAX, Cantera/ChemPy) są extras i trafiają do projektu dopiero po uzgodnieniu. Dev-only (`pytest`, `pytest-cov`, `mypy`, `ruff`, `black`) instalujemy wyłącznie dla potrzeb testów/CI.
5. **Brak zmian systemowych**: nie modyfikuj PATH ani globalnych ustawien poza Pythonem 3.14 (juz gotowe).

## 3. Workflow
1. Zanim zaczniesz kodowanie:
   - przeczytaj `README.md`, `todo1.md`, `py_lib.md`,
   - zidentyfikuj odpowiednie sekcje TODO,
   - zaplanuj zmiany (plan tool lub komentarz).
2. Kazda zmiana kodu:
   - uzasadnij w opisie (commit lub notatka),
   - zostaw tylko niezbedne komentarze,
   - dopisz wpis w `admin/TODO1_PKT{n}_changelog.md` (data, lista plikow, krotki cel).
3. Testy:
   - domyslnie `pytest` (jezeli zestaw istnieje),
   - jezeli brak, dopisz notatke jak testowales (np. `python -m ...`).
4. Po zakonczeniu pracy:
   - sprawdz `git status`,
   - upewnij sie, ze README/TODO sa spojne,
   - poinformuj o brakach lub zalozeniach.

## 4. Zakazane dzialania
- Nie instaluj dodatkowych interpreterow Pythona ani nie zmieniaj wersji.
- Nie tworz nowych branchy bez prosby.
- Nie usuwaj dokumentow (README, todo1, py_lib, standards, docs/USE_CASES) - mozna je aktualizowac, ale nie kasowac.
- Nie dodawaj binarek, logow, dumpow; repo musi byc lekkie.

## 5. Gdy cos jest niejasne
1. Zapytaj w komentarzu/issue zamiast zgadywac.
2. Jezeli pomiary lub biblioteki sa niejasne - zaznacz to w TODO lub notatce.
3. W razie bledow narzedziowych (np. brak biblioteki spoza `py_lib.md`) - zatrzymaj sie i zglos to.

Po przeczytaniu tego pliku agent moze przejsc do pracy. Jezeli zobaczysz sprzecznosci w instrukcjach, najpierw je wyjasnij, zamiast wprowadzac ryzykowne zmiany.

## 6. Changelog i niepowodzenia
- Dla kazdego punktu TODO1 istnieje osobny plik `admin/TODO1_PKT{n}_changelog.md`. Po zakonczonej pracy nad danym punktem dopisz tam nowy wpis (data, lista plikow, cel zmiany).
- Jezeli nie mozesz zrealizowac kroku (np. biblioteka w interpreterze nie uruchamia sie, brak zasobow, brak dostepu), wpisz to w changelogu i NIE podawaj wymyslonych wynikow.
- Ten sam problem zaznacz od razu w `todo1.md` przy odpowiadajacym podpunkcie (dodaj linie `> Problem: ...`). Task pozostaje otwarty dopoki wpisany problem nie zostanie rozwiazany.

## 7. TODO2 - Productization & Quality
1. **Boot-up (kolejnosc lektury)**: przed praca nad `todo2.md` przeczytaj kolejno `agent_instructions.md`, `copilot_update_project_playbook.md`, `standards.md`, `readme.md`, `README_VERS.md`, `docs/STRUCTURE.md`, `py_lib.md`, `todo1.md`, `todo2.md`, a nastepnie – zalezenie od zakresu – `docs/MODEL_OVERVIEW.md`, `docs/CALIBRATION.md`, `docs/ML_LOGGING.md`, `docs/USE_CASES.md`. Nie edytuj tych plikow dopoki uzytkownik nie da jawnego pozwolenia.
2. **Interpretacja `todo2.md`**:
   - kazdy bullet `- [ ] ...` to oddzielny cykl pracy Copilota,
   - sekcja `N` korzysta z changelogu `admin/TODO2_PKTN_changelog.md`; jezeli go brakuje, utworz na wzor istniejacych,
   - prace wykonuj tylko na plikach wskazanych w bullecie i ich bezposrednich zaleznosciach.
3. **Pętla dla pojedynczego bulletu** – stosuj dokladnie ponizsze kroki:
   1. *Analiza*: otworz wszystkie wymienione pliki, podsumuj stan i zidentyfikuj wymagane zmiany.
   2. *Plan*: wypisz konkretne kroki (pliki, zmiany API/CLI, testy). Plan musi byc zgodny z tym dokumentem, playbookiem, standardami i `py_lib.md`.
   3. *Implementacja*: modyfikuj tylko potrzebne pliki; przestrzegaj konwencji z `standards.md` i zasady "najpierw czytasz, potem piszesz".
   4. *Testy*: uruchom odpowiednie `pytest tests/...`, a jezeli nie mozna – jawnie to napisz wraz z przyczyna; nie wymyslaj wynikow.
   5. *Changelog TODO2*: dopisz wpis do `admin/TODO2_PKTN_changelog.md` (data, lista plikow, opis, status `OK` lub `BLOCKED` + powod).
   6. *Status bulletu*: w odpowiedzi tekstowej zaznacz `DONE` (mozna odhaczyc) albo `BLOCKED` wraz z brakujacymi elementami.
4. **Raportowanie**: kazda odpowiedz ma zawierac sekcje `Context`, `Plan`, `Changes`, `Tests`, `Changelog`, `Status`, opisujace odpowiednio prace nad jednym bullet'em TODO2.
