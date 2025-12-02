# Copilot: Playbook aktualizacji projektu PUR-MOLD-TWIN

Ten plik mówi **dokładnie, jak masz aktualizować projekt** jako asystent/Copilot. Nie wolno Ci "nadpisać na pałę" istniejących plików. Zawsze najpierw analizujesz stan repo, potem planujesz zmiany, dopiero na końcu edytujesz.

---

## 0. Zasady ogólne (must-follow)

1. **Najpierw czytasz, potem piszesz.**
   - Nie generujesz od zera nowego `readme.md`, `standards.md` itd.
   - Zawsze pracujesz na tym, co jest w repo, traktując to jak materiał do edycji / mergowania.

2. **Kod i dokumentacja to źródła równorzędne, ale:**
   - jeśli coś jest sprzeczne:
     - **stan kodu traktuj jako prawdę operacyjną**,
     - ale zamiast "przykrawać" docs na siłę, **wyraźnie opisz konflikt i proponowany merge**.

3. **Żadnych dużych podmian bloków tekstu bez powodu.**
   - Jeśli zmiana ma >10–15 wierszy w kluczowym pliku (`readme.md`, `MODEL_OVERVIEW`, `standards`, `STRUCTURE`):
     - spróbuj utrzymać istniejącą strukturę sekcji,
     - zmieniaj minimalny konieczny fragment,
     - zachowuj sensowną historię (nagłówki, kolejność sekcji).

4. **Zawsze myśl "diffem".**
   - Twoim celem jest wygenerowanie takich zmian, które wyglądają jak mądry PR:
     - jasne, punktowe modyfikacje,
     - zachowana czytelność,
     - zero zbędnych roszad typu zmiana formatowania bez powodu.

5. **Nie tworzysz nowej wizji projektu.**
   - Twoje zadanie to: doprowadzić dokumentację i strukturę do spójności z istniejącą wizją (ustaloną w plikach), a nie wymyślać projekt od nowa.

---

## 1. Onboarding przed jakąkolwiek zmianą

Zanim zmodyfikujesz **cokolwiek** w projekcie:

1. Przeczytaj i zrozum kolejno:
   1. `readme.md`
   2. `standards.md`
   3. `docs/STRUCTURE.md`
   4. `docs/MODEL_OVERVIEW.md`
   5. `docs/USE_CASES.md`
   6. `docs/CALIBRATION.md`
   7. `docs/ML_LOGGING.md`
   8. `README_VERS.md`
   9. `todo1.md`
   10. `todo2.md` (jesli jest aktywny zakres kolejnej fazy)
   11. `py_lib.md`

2. Zbuduj sobie wewnętrzną mapę:
   - jaki jest **cel projektu**,
   - jaka jest **architektura** (core, optimizer, material_db, cli),
   - jakie są **kluczowe kryteria jakości** (demold, p_max, rho, defekty),
   - który plik za co odpowiada.

3. Zanotuj (mentalnie lub w komentarzu do commita):
   - jakie są **sprzeczności** między tymi plikami,
   - które pliki wymagają aktualizacji w pierwszej kolejności.

Bez tego kroku **nie wolno** Ci wprowadzać zmian.

---

## 2. Ogólny workflow aktualizacji projektowych plików `.md`

Kiedy masz już pełen obraz, każdą większą zmianę wykonuj według tego schematu:

1. **Identyfikacja problemu**
   - Zadaj sobie wprost pytanie:
     - *"Co jest nie tak / czego brakuje w tym konkretnym pliku?"*
   - Przykłady:
     - `readme.md` nie opisuje aktualnego statusu (mamy już MVP 0D, optimizer i testy, ale README twierdzi, że jesteśmy na etapie koncepcji).
     - `MODEL_OVERVIEW.md` ma inne nazwy pól niż dataclasses w kodzie.
     - `STRUCTURE.md` opisuje inny układ katalogów niż faktycznie w repo.

2. **Zebranie kontekstu do merge`a**
   - Zanim zaczniesz pisać nową treść:
     - wyszukaj w pozostałych `.md`, czy temat już jest gdzieś opisany,
     - sprawdź, jakie założenia były wcześniej (np. w starszych wpisach w `README_VERS.md`).

3. **Propozycja rozwiązania w głowie (lub na boku)**
   - Zanim dotkniesz pliku, ułóż sobie krótko:
     - co chcesz dopisać,
     - co chcesz zmienić,
     - czego absolutnie nie chcesz ruszać (np. istniejące listy use-case’ów, jeśli są nadal aktualne).

4. **Edycja minimalno-rozsądna**
   - Zmieniaj najmniejszą konieczną liczbę linii, która:
     - przywraca spójność,
     - nie niszczy struktury dokumentu,
     - nie usuwa informacji, które są nadal prawdziwe.

5. **Sprawdzenie spójności po zmianie**
   - Po każdej większej edycji:
     - upewnij się, że inne dokumenty nie zostały logicznie "złamane" (np. USE_CASES nie przeczą MODEL_OVERVIEW),
     - jeśli tak – wpisz do planu kolejną zmianę/aktualizację tamtych plików.

---

## 3. Specyficzne zasady dla kluczowych plików

### 3.1. `readme.md`

Cel:
- ma opisywać **aktualny stan projektu** (MVP, co działa, jakie są główne komponenty, jak odpalić),
- oraz **kierunek krótkoterminowy** (Next steps na poziomie kilku głównych punktów).

Zasady edycji:

1. Nie nadpisuj całego README.
   - Zachowaj istniejące sekcje, jeśli są nadal merytorycznie poprawne.
   - Aktualizuj tylko to, co jest faktycznie nieaktualne (np. sekcję „Status”).

2. Zanim dodasz nową sekcję:
   - sprawdź, czy podobna treść nie istnieje w `MODEL_OVERVIEW` albo `STRUCTURE`.
   - Jeśli tak – w README raczej **linkuj/skrótowo streszczaj**, zamiast kopiować całe fragmenty.

3. Jeśli zmieniasz opis statusu:
   - upewnij się, że jest zgodny z ostatnim wpisem w `README_VERS.md`.
   - jeśli nie – dopisz tam nowy wpis.

4. Dodając instrukcję dla asystenta/Copilota:
   - nie usuwaj istniejących instrukcji, tylko dodaj sekcję typu
     „Jak ma pracować asystent / Copilot w tym repo”.

### 3.2. `standards.md`

Cel:
- jest źródłem prawdy o **nazewnictwie**, **jednostkach**, **stylu**.

Zasady edycji:

1. Najpierw sprawdź kod:
   - jakie nazwy faktycznie są używane (np. `T_polyol_in_C`, `p_max_allowable_bar`),
   - jak wyglądają struktury katalogów.

2. Jeśli kod łamie obecne standardy:
   - nie zmieniaj od razu kodu,
   - najpierw zaktualizuj `standards.md`, wyraźnie dopisując wyjątki lub nową regułę.

3. Nie kasuj starych zasad, jeśli są nadal używane w części repo.
   - dopisz sekcję "legacy" albo komentarz, że dana konwencja jest używana w starszych modułach.

### 3.3. `docs/MODEL_OVERVIEW.md`

Cel:
- canonicalny opis modelu fiz-chem, wejść/wyjść i głównych założeń.

Zasady edycji:

1. Nie zmieniaj definicji modelu, jeśli kod jeszcze tak nie działa.
   - jeśli chcesz zmienić zachowanie solvera, przygotuj **najpierw** plan zmian w kodzie, a MODEL_OVERVIEW zaktualizuj dopiero, gdy implementacja będzie spójna.

2. Jeśli nazwy pól różnią się od kodu (np. `T_polyol_in` vs `T_polyol_in_C`):
   - zaktualizuj dokument tak, by:
     - zawierał **dokładne nazwy z kodu**,
     - opcjonalnie zachował "nazwę koncepcyjną" w opisie.

3. Dodając nowe zjawisko/model (np. bardziej szczegółowy model pentanu):
   - dodaj osobną, jasno nazwaną podsekcję,
   - nie mieszaj nowych założeń z pierwotnym MVP bez oznaczenia.

### 3.4. `docs/STRUCTURE.md`

Cel:
- pokazuje docelową i aktualną strukturę projektu.

Zasady edycji:

1. Nie opisuj w STRUCTURE modułów, których **w ogóle nie ma** i nie ma dla nich planu w TODO.
   - jeśli coś jest "wizją na przyszłość", wyraźnie oznacz to jako "planned" / "future".

2. Jeśli struktura katalogów się zmieniła:
   - najpierw zaktualizuj STRUCTURE,
   - potem dostosuj inne dokumenty (README, CALIBRATION, ML_LOGGING) do nowego układu.

### 3.5. `docs/USE_CASES.md`

Cel:
- realne lub kalibracyjne scenariusze użycia,
- nie marketing.

Zasady edycji:

1. Nie usuwaj istniejących use-case’ów, chyba że są **wprost błędne**.
   - jeśli po prostu się „zestarzały”, dopisz notkę, że odnoszą się do poprzedniej wersji modelu.

2. Jeśli dodajesz nową funkcję (np. nowe KPI, tryb pracy CLI):
   - dołóż do USE_CASES nowy scenariusz, który pokazuje sens tej funkcji.

3. Liczby (czasy, ciśnienia, gęstości):
   - traktuj jako target kalibracyjny,
   - jeśli aktualny solver ich nie osiąga, zaznacz to w dokumencie zamiast "upiększać" wyniki.

### 3.6. `docs/CALIBRATION.md` i `docs/ML_LOGGING.md`

Zasady wspólne:

1. Najpierw przejrzyj, jakie skrypty / moduły realnie istnieją w `src/`.
   - nie opisuj pipeline’u, którego nie ma.

2. Jeśli zmieniasz format danych (np. CSV → Parquet, inne nazwy kolumn):
   - najpierw dopisz to tutaj,
   - potem zmień kod, tak żeby wszystko było zgodne.

---

## 4. Jak podejść do konfliktów między dokumentami

Często `readme.md`, `MODEL_OVERVIEW.md` i `USE_CASES.md` będą mówiły **trochę różne rzeczy**. Twoje zadanie:

1. **Zidentyfikuj konflikt** – nazwij go wprost, np.:
   - README mówi, że projekt jest na etapie koncepcji,
   - ale MODEL_OVERVIEW + tests sugerują, że mamy działający MVP.

2. **Zaproponuj spójny stan docelowy**, np.:
   - wszędzie opisujemy projekt jako "MVP 0D + optimizer, bez pełnej kalibracji".

3. **Wyznacz plik wiodący dla danego tematu**, np.:
   - status projektu → `README_VERS.md` + sekcja statusu w `readme.md`.
   - fizyka modelu → `MODEL_OVERVIEW`.
   - architektura repo → `STRUCTURE`.

4. **Dopiero potem** edytuj poszczególne pliki tak, by zgadzały się z wybranym stanem.

Nie wolno Ci zrobić tak, że jeden z dokumentów będzie opisywał starą rzeczywistość "bo tak wygodniej".

---

## 5. Współpraca z TODO (`todo1.md`, `todo2.md` lub kolejne)

1. Zanim stworzysz nowe zadanie:
   - sprawdź, czy podobne już nie istnieje.

2. Jeśli jakiś punkt TODO jest niejasny lub sprzeczny z aktualnym kodem:
   - nie dopisuj "swojej wersji" w innym miejscu,
   - zamiast tego doprecyzuj istniejący punkt TODO i zaktualizuj dokumentację.

3. Każda większa aktualizacja dokumentacji ramowej (README, MODEL_OVERVIEW, STRUCTURE, CALIBRATION, ML_LOGGING):
   - powinna mieć odzwierciedlenie w TODO:
     - albo jako nowy task,
     - albo jako odhaczenie istniejącego.

---

## 6. Kiedy powinieneś się zatrzymać

Jako Copilot/asystent **musisz się zatrzymać** i wrócić do użytkownika, jeśli:

1. Proponowana zmiana wymagałaby:
   - całkowitego przepisania kluczowego pliku `.md` od zera,
   - zmiany podstawowych założeń fizycznych modelu.

2. Widzisz, że istniejące dokumenty są tak niespójne, że nie da się ich rozsądnie zmergować bez decyzji właściciela projektu.

3. Nie jesteś w stanie jednoznacznie ustalić, które źródło (kod vs dokumentacja) jest nowsze/bardziej obowiązujące.

W takiej sytuacji:
- wypisz jasno konflikty,
- zaproponuj 1–2 warianty kierunku zmian,
- poproś użytkownika/właściciela projektu o decyzję.

---

## 7. Minimalny standard po aktualizacji

Po wprowadzeniu zmian w dokumentacji ramowej projektu:

1. `readme.md` powinno:
   - poprawnie opisywać **aktualny stan** (MVP, co działa),
   - zawierać sekcję dla asystenta/Copilota z instrukcją pracy.

2. `standards.md` musi być zgodne z realnym kodem w kwestii:
   - nazewnictwa temperatur/ciśnień,
   - struktury katalogów,
   - głównych konwencji.

3. `docs/MODEL_OVERVIEW.md`, `docs/STRUCTURE.md`, `docs/USE_CASES.md`, `docs/CALIBRATION.md`, `docs/ML_LOGGING.md`:
   - nie mogą sobie nawzajem jawnie przeczyć,
   - muszą używać tych samych nazw pól i modułów, co kod.

4. `README_VERS.md`:
   - ma wpis odzwierciedlający ostatnie większe zmiany.

Jeśli tego nie osiągniesz, Twoja praca jako Copilota jest niedokończona.
---

## 8. TODO2 - Productization & Quality workflow

1. **Boot-up**: przed praca nad zadaniem z 	odo2.md przeczytaj w podanej kolejnosci gent_instructions.md, copilot_update_project_playbook.md, standards.md, eadme.md, README_VERS.md, docs/STRUCTURE.md, py_lib.md, 	odo1.md, 	odo2.md, a nastepnie � zalezne od zakresu � docs/MODEL_OVERVIEW.md, docs/CALIBRATION.md, docs/ML_LOGGING.md, docs/USE_CASES.md. Nie wprowadzaj zmian w tych plikach bez jawnego polecenia.
2. **Interpretacja listy**:
   - jeden bullet - [ ] ... w 	odo2.md = jeden pelny cykl pracy Copilota,
   - sekcja N korzysta z changelogu dmin/TODO2_PKTN_changelog.md; jezeli go brakuje, utworz go wedlug istniejacych wzorcow,
   - pracuj tylko na plikach wymienionych w bullecie i ich bezposrednich zaleznosciach.
3. **Pftla wykonawcza dla pojedynczego bulletu**:
   1. *Analiza*: otworz wszystkie wskazane pliki, opisz aktualny stan i brakujace elementy.
   2. *Plan*: spisz kroki (jakie pliki, jakie zmiany API/CLI, jakie testy) w zgodzie z tym playbookiem, gent_instructions.md, standards.md i py_lib.md.
   3. *Implementacja*: zmieniaj tylko niezbedne pliki; stosuj minimalne, zrozumiale diffy i aktualne standardy nazewnictwa.
   4. *Testy*: uruchom odpowiednie pytest tests/.... Jezeli testu nie da sie wykonac, jawnie opisz przyczyne i nie zakladaj sukcesu.
   5. *Changelog TODO2*: dopisz wpis (data + lista plikow + opis + status OK/BLOCKED (z powodem)) do dmin/TODO2_PKTN_changelog.md.
   6. *Status bulletu*: w odpowiedzi komunikuj DONE (mozna odhaczyc) lub BLOCKED (czego brakuje).
4. **Raportowanie**: kazda odpowiedz dotyczaca TODO2 musi zawierac sekcje Context, Plan, Changes, Tests, Changelog, Status.
