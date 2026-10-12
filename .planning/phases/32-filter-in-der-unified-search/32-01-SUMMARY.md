---
phase: 32-filter-in-der-unified-search
plan: 01
subsystem: PHP-Companion (SearchFilters, PageController, Search\Provider), Backend-Tests (Parität, /search)
tags: [usrch-01, usrch-03, d-32-03, d-32-07, unified-search, filter-definition]
requires:
  - phase: 13
    provides: "Wire-Weg der Typgruppen: SearchFilters::TYPES, ExAppService, types im Backend, TYPE_GROUPS"
provides:
  - "SearchFilters::typesFrom(), der eine Parser der Typgruppen für Ergebnisseite und Dialog, mit MAX_TYPES_LENGTH 200"
  - "Provider deklariert den Custom Filter types (FilterDefinition, TYPE_STRING), liest ihn still, reicht die Gruppen an run() und an die Tür 'Alle Ergebnisse'"
  - "Paritätstest der sechs Gruppennamen über PHP TYPES, /search, /snippets, /diagnose und TYPE_GROUPS"
  - "Backend-Beleg: POST /search mit types [] liefert dieselben Kandidaten wie ohne Feld; 422 für unbekannte Gruppen bleibt"
affects: [32-02 Ordnerfilter, 32-04 Plugin, 32-06 deploy-harp und Doku, 32-08 Audit]
tech-stack:
  added: []
  patterns: ["Custom Filter mit FilterDefinition im IFilteringProvider; Leser typesOf() im Stil von titleOnly()"]
key-files:
  created:
    - backend/tests/test_type_vocabulary_parity.py
    - php/tests/Unit/SearchFiltersTest.php
    - .planning/phases/32-filter-in-der-unified-search/deferred-items.md
  modified:
    - php/lib/Service/SearchFilters.php
    - php/lib/Controller/PageController.php
    - php/lib/Search/Provider.php
    - php/tests/Unit/ProviderTest.php
    - backend/tests/test_search_endpoint.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "FilterDefinition types exklusiv (Konstruktor-Standard): SearchComposer stable34 legt eine Custom-Definition nur unter der ID des deklarierenden Providers ab, andere Provider verwerfen den Namen als unbekannt, die Exklusivprüfung erreicht nur Findling; Wahl dokumentiert, ohne Wirkung auf andere Apps"
  - "typesFrom() trimmt nur Leerzeichen und Tab (nicht PHPs Standard-trim mit NUL und Zeilenumbruch), damit 'pdf\\0' wie im Plan verlangt keine Gruppe ergibt; gilt damit auch für die Ergebnisseite (Verengung, keine Erweiterung)"
  - "MAX_TYPES_LENGTH 200 Byte, geprüft vor dem Split; sechs Namen mit Kommas sind 52 Byte"
  - "Tür trägt types in TYPES-Reihenfolge; Datum bleibt draußen wie bisher"
metrics:
  duration: "ca. 50 min, davon ca. 12 min lokaler Volltestlauf und ca. 25 min CI"
  completed: 2026-10-12
  tasks: 2
  files: 8
---

# Phase 32 Plan 01: Typfilter serverseitig Summary

Der Findling-Provider deklariert den Custom Filter `types` (FilterDefinition, string), liest ihn über den gemeinsamen Parser `SearchFilters::typesFrom()` still auf die geschlossene Menge der sechs Gruppen herunter und reicht die Gruppen an den bestehenden Wire-Weg und an die Tür "Alle Ergebnisse" weiter. PageController liest seinen Adressparameter über denselben Parser. Ein Paritätstest hält die sechs Namen an fünf Stellen gleich, ein Endpoint-Test belegt "leere Liste gleich fehlendes Feld". D-05 ist sichtbar aufgehoben (D-32-07).

## Commit

- `ed2908fc` feat(32-01): the findling provider declares the type filter of the unified search (Task 1 und 2 in einem Commit, wie im Plan vorgegeben), gepusht auf origin/main zusammen mit den Planungs-Commits 5a6e1c0d, 21f10cec, a632a35c.

## Task 1: Backend-Hälfte von Kriterium 3

- `backend/tests/test_type_vocabulary_parity.py`: Leser `php_type_groups()` (Kommentare entfernt, Rückgabe Liste oder None), Vergleich `parity_findings()` mit Befundzeilen; Modelle über `typing.get_args` bzw. `typing.get_type_hints(read_diagnosis, include_extras=True)`, nicht per Regex. Fünf Selbsttests mit Negativ- bzw. Positivkontrolle: Kommentarnamen zählen nicht, vertauschte Reihenfolge, siebter Name, fehlende Konstante (nie Gleichstand), umbenannte Gruppe im Container.
- `test_search_endpoint.py::test_an_empty_group_list_behaves_like_no_filter_at_all`: gleiche IDs in gleicher Reihenfolge, Korpus nachweislich mit pdf und docx (gerade und ungerade IDs). `test_an_unknown_group_name_is_refused_and_never_ignored` unverändert (422).
- Gegenproben (beide rot gesehen, danach `git diff --stat src` leer):
  - `sed -i 's/^    "images": ("jpg"/    "pictures": ("jpg"/' src/findling/query/rewrite.py && uv run python -m pytest -q tests/test_type_vocabulary_parity.py` ergab `1 failed, 5 passed` (Parität rot), zurück per `git checkout`.
  - `sed -i "s/'images', 'text'\];/'images', 'text', 'videos'];/" ../php/lib/Service/SearchFilters.php` ergab `2 failed, 4 passed` (Parität rot, zusätzlich der relative Umbenennungs-Selbsttest), zurück per `git checkout`.
  - `min_length=1` an `SearchRequest.types` (sed auf `src/findling/api/search.py`), `uv run python -m pytest -q tests/test_search_endpoint.py -k empty_group` ergab `assert 422 == 200`, zurück per `git checkout`.

## Task 2: Parser, FilterDefinition, Tür, D-05 umgedreht

- `SearchFilters::typesFrom(string): list<string>` und `MAX_TYPES_LENGTH = 200`; Klassenkommentar nennt den einen Parser beider Leser.
- `PageController::typeGroups()` ruft nur noch `SearchFilters::typesFrom($raw)`; keine eigene explode-Schleife mehr.
- `Provider`: `FILTER_TYPES = 'types'`, `getSupportedFilters()` mit fünf Namen, `getCustomFilters()` mit genau `new FilterDefinition(self::FILTER_TYPES, FilterDefinition::TYPE_STRING)`, `typesOf()` (Nicht-String ergibt `[]`), `search()` übergibt die Gruppen als erstes Argument von `SearchFilters`, Sortierung bleibt `SORT_DEFAULT`, `entryPoint()` hängt `types` an, wenn nicht leer. Kommentare zu D-05 umgeschrieben, Warnung vor Namen ohne Definition erhalten. Keine neue Logzeile.
- Tests: neue `SearchFiltersTest.php` (16 Fälle inkl. Datenanbieter mit neun Werten ohne Gruppe, 5000-Zeichen-Wert mit `pdf,` am Anfang, Grenze bei genau 200 Byte, `pdf,videos` ergibt `['pdf']`). ProviderTest: `testTheProviderDefinesNoFilterOfItsOwn` umgedreht zu `testTheProviderDefinesExactlyTheTypeFilterOfItsOwn`, `testTheDialogNeverCarriesATypeGroupOrASortMode` umgedreht zu `testTheDialogCarriesATypeGroupButNeverASortMode`, beide mit Vermerk D-32-07; Fall bei :531 erwartet fünf Namen; neu: jeder Nicht-Kernname hat eine Definition (T-32-02), `pdf` erreicht run(), Typ plus Datum (D-32-02), zehn Werte ohne Gruppe ergeben `SearchFilters::none()` (Strings und falsche Typen), Tür mit `types=pdf%2Cimages`, Tür ohne types-Parameter bei unbekanntem Wert.
- Baumhash im selben Commit: `PHP_FILES_TODAY` 92 auf 93, `PHP_TREE_HASH_TODAY` 3154299545d8f8c2554fc5f844c0a399c14479416ea99cb09d2c924c62c81053, Journalabsatz "Plan 32-01".

### PHP-Rot (TDD-Nachweis)

Lokal kein PHPUnit; Nachweis über Textprüfung plus grünen CI-Lauf: die neuen Fälle rufen `SearchFilters::typesFrom`, `Provider::FILTER_TYPES` und erwarten `types` in `getSupportedFilters()` bzw. eine Definition in `getCustomFilters()`, die vor dem Commit nicht existierten (Aufruf einer unbekannten Methode bzw. Konstante und `assertSame` gegen vier Namen und `[]`). PHPUnit-Zahl stieg von 598 (Lauf 38264572714, 31-14) auf 620 (Lauf 38309357692), genau die 22 neuen Fälle (16 SearchFiltersTest, 6 ProviderTest). Zusätzlich lokal per Docker-Image php:8.3-cli: `php -l` über alle fünf PHP-Dateien sauber und `typesFrom` über die elf Planwerte mit den erwarteten Ergebnissen.

## Gates und CI

- Lokal aus backend/ mit PYTHONUTF8=1: `pytest` 5586 passed, 30 skipped; `ruff check` und `ruff format --check` grün; `PYRIGHT_PYTHON_FORCE_VERSION=latest pyright` 0 Fehler; `vulture src tests --min-confidence 80` ohne Befund; `git diff --stat backend/src` leer.
- CI auf ed2908fc, jeweils mit `gh run watch <id> --exit-status`:
  - php.yml 38309357692: grün (PHPUnit 620 Tests).
  - python.yml 38309357739: Versuch 1 rot durch einen Flake ohne Bezug zum Plan (siehe Abweichungen), Versuch 2 grün.
  - integration.yml 38309357675: grün; die Providerliste eines echten Nextcloud stable34 meldet für findling `"types":"string"` neben den vier Kernfiltern, die Liste aller Apps bleibt gültig.
  - deploy-harp.yml 38309357673: grün; `declared_filters` vor dem Upgrade "since term title-only until" (1.4.2), danach "since term title-only types until". Keine Erwartung in deploy-harp musste angepasst werden (die Strecke vergleicht die Filterliste nicht über das Upgrade).
  - Außerdem grün: Resilience 38309357694, Security scans 38309357734, Multi-arch image 38309357723, OpenSSF Scorecard 38309357703.

## Deviations from Plan

### Auto-fixed Issues

None im Code. Präzisierung:

**1. [Rule 1 - Bug] Plan-Verhalten "pdf\0 ergibt []" verlangte eine andere trim-Regel als die alte Seite**
- **Found during:** Task 2
- **Issue:** Die wörtlich übernommene Logik `strtolower(trim($part))` entfernt NUL und Zeilenumbrüche, `"pdf\0"` hätte `['pdf']` ergeben.
- **Fix:** `trim($part, " \t")`; ein NUL oder Zeilenumbruch am Namen ist ein gebauter Wert und ergibt keine Gruppe. Gilt auch für die Ergebnisseite (Verengung); alle PageControllerTest-Fälle zu `types` blieben unverändert grün.
- **Files modified:** php/lib/Service/SearchFilters.php
- **Commit:** ed2908fc

### Flake außerhalb des Umfangs (nicht behoben)

- python.yml 38309357739 Versuch 1: `test_main_lifespan.py::test_the_status_answer_is_the_same_with_and_without_the_one_time_task` vergleicht zwei Statusantworten inklusive des Live-Werts `profile.memoryAvailableBytes` (Differenz rund 229 KB). Kein Bezug zu 32-01; in `deferred-items.md` eingetragen, Job neu gestartet (Versuch 2 grün). Zusicherung nicht angefasst.

## Threat Flags

Keine neue Fläche außerhalb des Threat Models: T-32-01 (Parser mit geschlossener Menge, Längengrenze, Nicht-String ergibt `[]`), T-32-02 (Test jeder Nicht-Kernname hat eine Definition, integration und deploy-harp lesen die Filterkarte), T-32-03 (Paritätstest mit Selbsttests), T-32-04 (keine Logzeile mit Filterwert) sind umgesetzt.

## Hinweise für Folgepläne

- Der Files-Provider des Kerns deklariert eigene Filter `type` und `mime` (string). `types` ist davon verschieden; das Plugin (32-04) muss den Namen `types` genau so schicken.
- USRCH-01 und USRCH-03 bleiben in REQUIREMENTS.md offen (Abhaken erst nach 32-07 bzw. 32-06).

## Self-Check: PASSED

- Dateien vorhanden: backend/tests/test_type_vocabulary_parity.py, php/tests/Unit/SearchFiltersTest.php, deferred-items.md.
- Commit ed2908fc in `git log` und auf origin/main.
- Akzeptanz-Greps: `new FilterDefinition(self::FILTER_TYPES, FilterDefinition::TYPE_STRING` 1 Treffer; alte Testnamen 0 Treffer; `D-32-07` in ProviderTest 2 Treffer; `explode(',', $raw)` in PageController 0 Treffer; `def test_an_empty_group_list_behaves_like_no_filter_at_all` und `status_code == 422` in test_search_endpoint.py vorhanden.
