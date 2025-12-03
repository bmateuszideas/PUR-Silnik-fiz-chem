Tytuł: <krótki, rzeczowy tytuł PR-a>

## Krótki opis
- 2–3 zdania podsumowania, co zostało zmienione i dlaczego (ton neutralny, techniczny).

## Zakres zmian (pliki/obszary)
- Wypunktuj najważniejsze zmiany z odniesieniem do plików/katalogów.
- Zachowaj strukturę istniejących sekcji i minimalny diff (zgodnie z `copilot_update_project_playbook.md`).

## Motywacja i kontekst
- Dlaczego zmiana jest potrzebna? Czy rozwiązuje konkretny błąd, zadłużenie techniczne, czy uzupełnia dokumentację?
- Jeśli istnieją powiązane decyzje projektowe, odnieś się do nich.

## Testy
- Wypisz wszystkie wykonane testy wraz z poleceniami (np. `pytest tests/test_etl.py`).
- Jeśli testy są pominięte, wyjaśnij powód i wpływ na ryzyko regresji.

## Ryzyka / wpływ na regresję
- Opisz potencjalne regresje, ograniczenia lub obszary wymagające dodatkowej weryfikacji.
- Zaznacz, czy zmiana wymaga konfiguracji środowiska (np. dodatkowe zależności, zmiany w danych).

## Uwagi dla reviewerów
- Opcjonalne wskazówki ułatwiające review (np. kolejność przeglądu, szczególne scenariusze do sprawdzenia).

## Checklist przed merge
- [ ] Zmiany są zgodne z aktualną strukturą i wizją repozytorium (zob. `copilot_update_project_playbook.md`).
- [ ] Testy pokrywają główne ścieżki użycia lub opisano, dlaczego są pominięte.
- [ ] Zidentyfikowano i opisano ryzyka/regresje.
