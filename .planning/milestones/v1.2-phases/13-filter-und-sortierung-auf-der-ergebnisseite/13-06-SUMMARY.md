---
phase: 13-filter-und-sortierung-auf-der-ergebnisseite
plan: 06
subsystem: php-companion
tags: [unified-search, ifilteringprovider, datumsfilter, since, until, filt-03, d-05]

requires:
  - phase: 13-filter-und-sortierung-auf-der-ergebnisseite
    plan: 04
    provides: "SearchFilters mit TYPES, SORTS, SORT_DEFAULT, EPOCH_MAX, none(), hasAny()"
  - phase: 13-filter-und-sortierung-auf-der-ergebnisseite
    plan: 05
    provides: "SearchService::run(IUser, string, bool, int, SearchCaps, SearchFilters)"
provides:
  - "getSupportedFilters() meldet BUILTIN_TERM, BUILTIN_TITLE_ONLY, BUILTIN_SINCE, BUILTIN_UNTIL"
  - "Provider::epochOf(): ein Datumsfilter als Unix-Epoche, jeder fremdartige Wert still als nicht gesetzt"
  - "Provider::epochWithin(): beide Grenzen geklemmt auf 0 bis SearchFilters::EPOCH_MAX"
  - "Provider::search() übergibt ein SearchFilters mit since und until statt SearchFilters::none()"
  - "Elf Testfälle über Deklaration, Umrechnung, kaputten Wert, Klemmen und die leeren Felder des Dialogs"
affects: [13-07, 13-09, 13-12]

tech-stack:
  added: []
  patterns:
    - "Ein Wert aus fremdem Code wird über seine Klasse geprüft und sonst als nicht gesetzt gelesen, nie als Ausnahme (Form von titleOnly())"
    - "Eine Grenze wird geklemmt und nie abgelehnt, gegen dieselbe Konstante, die auch die andere Hälfte kennt"
    - "Ein Testdoppel, das Filter nach Namen ausliefert, statt für jeden Namen denselben Wert zurückzugeben"

key-files:
  created: []
  modified:
    - php/lib/Search/Provider.php
    - php/tests/Unit/ProviderTest.php
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "epochOf() bleibt frei von Arithmetik, das Klemmen sitzt in epochWithin(): zwei Fragen, zwei Methoden, und das Klemmen ist damit unabhängig von der Herkunft des Wertes prüfbar"
  - "epochWithin() ist die zweite Stelle mit derselben Klemmung wie ExAppService, nicht eine geteilte Hilfsmethode: die Konstante ist geteilt, nicht der Aufrufweg, und der Provider klemmt vor der Weitergabe statt sich darauf zu verlassen, dass jemand weiter unten es noch tut"
  - "Die Adresse zur Ergebnisseite trägt die Datumsgrenzen des Dialogs bewusst nicht mit, und der Grund steht als Absatz an entryPoint(): die Seite hätte für so eine Grenze keinen Chip, der Nutzer säße vor weniger Treffern ohne sichtbare Ursache"
  - "getCustomFilters() bleibt leer und hat jetzt seinen Grund im eigenen Docstring statt nur im Nachbardocstring von getAlternateIds()"

patterns-established:
  - "filteredQuery(): ein ISearchQuery-Doppel, dessen getFilter() eine Namenskarte liest, so dass Datumsgrenze und Namensschalter unabhängig gesetzt werden können"
  - "filtersOf(): Gegenstück zu capsOf(), fängt das übergebene SearchFilters ab; die Datumsfälle behaupten ausschließlich an diesem Objekt"

requirements-completed: []  # FILT-03 trägt noch 13-07 und 13-09

duration: 30min
completed: 2026-09-17
---

# Phase 13 Plan 06: Der Datumsfilter des Unified-Search-Dialogs Summary

**Der Provider deklariert `BUILTIN_SINCE` und `BUILTIN_UNTIL` und beachtet sie, womit Findling nicht mehr aus dem Dialog verschwindet, sobald jemand ein Datum setzt; ein fremdartiger Filterwert gilt still als nicht gesetzt, beide Grenzen werden auf `0` bis `EPOCH_MAX` geklemmt, und Typgruppe wie Sortierung bleiben ausdrücklich draußen.**

## Performance

- **Duration:** 30 min
- **Tasks:** 2 (plus eine Abweichung)
- **Files modified:** 3 (keine neu)

## Accomplishments

- `getSupportedFilters()` meldet vier Namen in stabiler Reihenfolge: `BUILTIN_TERM`, `BUILTIN_TITLE_ONLY`, `BUILTIN_SINCE`, `BUILTIN_UNTIL`. Der bestehende Docstring über die Wirkung eines fehlenden Eintrags ist um den Datumsfall fortgeschrieben: bis zu diesem Plan verschwand Findling bei gesetztem Datum aus dem Dialog, entweder weil die Oberfläche die Filterliste je Provider liest und diesen nicht mehr fragte, oder weil seine Gruppe in dem HTTP 400 endete, mit dem ein nicht deklarierter exklusiver Filter beantwortet wird. Beides sah für den Nutzer gleich aus.
- `epochOf(ISearchQuery, string): ?int` liest einen der beiden Datumsfilter wörtlich nach der Form von `titleOnly()`: Filter holen, bei `null` mit `null` antworten, den Wert nur als Epoche lesen, wenn er ein `\DateTimeImmutable` ist, sonst `null`. Der Docstring nennt beide Gründe: ein Defekt drüben kostet die Grenze und nie die Suche, und `getTimestamp()` ist zeitzonenfrei und damit direkt gegen `mtime` vergleichbar, weshalb dieser Pfad im Gegensatz zu den Schnellbereichen der eigenen Seite keine Zeitzone braucht.
- `epochWithin(?int): ?int` klemmt auf `0` bis `SearchFilters::EPOCH_MAX`, mit demselben Satz und derselben Konstante wie `ExAppService`: oberhalb von `SEARCH_MTIME_MAX` antwortet der Container mit 422, und ein 422 kommt hier als leere Gruppe an, die wie "nichts gefunden" aussieht.
- `search()` baut daraus ein `SearchFilters` mit leeren Typgruppen, `SORT_DEFAULT` und den zwei geklemmten Grenzen und übergibt es an `SearchService::run`. Der Kommentar darüber sagt, dass die zwei leeren Felder Absicht sind und keine offene Baustelle.
- `getCustomFilters()` ist unverändert leer und hat jetzt einen eigenen Docstring mit dem Grund (D-05): ein Name ohne `FilterDefinition` macht die Providerliste des ganzen Dialogs kaputt, also leben Dateityp und Sortierung in v1.2 ausschließlich auf der eigenen Seite.
- Die `resourceUrl` in die Ergebnisseite ist unverändert, und die Auslassung ist als Entscheidung lesbar: ein Absatz an `entryPoint()` sagt, dass die Tür auf Seite eins einer nicht eingegrenzten Suche führt und warum eine mitgereichte Grenze ohne passenden Chip schlechter wäre als keine.
- Elf neue Testfälle in `ProviderTest.php`, dazu zwei Hilfsverfahren. Der bestehende Fall über die Filterliste ist fortgeschrieben statt verdoppelt.

## Task Commits

Jeder Task wurde einzeln committet:

1. **Task 1: Deklaration und defensives Lesen der beiden Datumsfilter** - `3cf3044` (feat)
2. **Task 2: Testfälle für Deklaration, Umrechnung und den kaputten Wert** - `476fa5b` (test)
3. **Abweichung: Baumhash der PHP-Hälfte nachziehen** - `486d30f` (test)

## Files Created/Modified

- `php/lib/Search/Provider.php` - vier statt zwei Filternamen mit fortgeschriebenem Docstring, `epochOf()`, `epochWithin()`, das `SearchFilters` in `search()`, der Grund an `getCustomFilters()`, der Absatz über die ausgelassenen Grenzen an `entryPoint()`
- `php/tests/Unit/ProviderTest.php` - `filteredQuery()`, `filtersOf()`, elf Fälle, der bestehende Filterlisten-Fall fortgeschrieben
- `backend/tests/test_measurement_scripts.py` - `PHP_TREE_HASH_TODAY` nachgezogen, mit Begründungsabsatz

## Decisions Made

- **Lesen und Klemmen sind zwei Methoden.** `epochOf()` beantwortet "was hat der Dialog gesagt", `epochWithin()` beantwortet "was darf davon über die Prozessgrenze". Zusammengelegt wäre ein Fall über das Klemmen immer auch ein Fall über das Lesen gewesen, und der Testfall mit dem absurd großen Datum hätte nicht mehr sagen können, welche der beiden Fragen ihn beantwortet.
- **Der Provider klemmt selbst, obwohl `ExAppService` es ohnehin noch einmal tut.** Der Plan verlangt es, und der Grund trägt: die Klemmung dort schützt den Rumpf an der Prozessgrenze, die Klemmung hier schützt das Wertobjekt, das durch `SearchService` reist. Geteilt ist die Konstante, nicht der Aufrufweg; eine gemeinsame Hilfsmethode hätte eine Abhängigkeit zwischen zwei Klassen erzeugt, die sonst nur ein Wertobjekt teilen.
- **Der bestehende Fall über die Filterliste ist fortgeschrieben, nicht verdoppelt.** Zwei Fälle über dieselbe Liste hätten beim nächsten Namen beide angefasst werden müssen, und der ältere wäre der sein, den jemand übersieht.
- **Ein Testdoppel, das Filter nach Namen ausliefert.** Das bestehende `query()` liefert für jeden Namen denselben Filter, was für den Namensschalter reichte, aber für "Datum gesetzt, Namensschalter nicht" nicht mehr. `filteredQuery()` steht daneben statt an seiner Stelle, damit kein bestehender Fall angefasst werden musste.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierend] Der Baumhash der PHP-Hälfte war nach Task 2 rot**

- **Found during:** Gesamtlauf der Backend-Suite nach Task 2
- **Issue:** `test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_php_half` hält Anzahl und sha256 über alle PHP-Dateien unter `php/`. Dieselbe Mechanik wie in 13-01, 13-03, 13-04 und 13-05, und der Plan nennt sie nicht.
- **Fix:** `PHP_TREE_HASH_TODAY = b7a029cc...`; `PHP_FILES_TODAY` bleibt bei 64, weil keine Datei hinzukam und keine wegfiel. Darüber der vorgeschriebene Begründungsabsatz mit Datum, Plan und den zwei Dateien, deren Bytes sich geändert haben. Die Messwertkonstanten des Laufs vom 09.09.2026 bleiben unberührt.
- **Files modified:** backend/tests/test_measurement_scripts.py
- **Verification:** `uv run pytest tests/test_measurement_scripts.py -q` = 228 passed
- **Committed in:** `486d30f`

### Präzisierungen gegenüber dem Plantext

**2. [Rule 2 - Fehlender Fall] Der "bestehende Fall über `getCustomFilters()`" gab es nicht**

- **Found during:** Task 2
- **Issue:** Die Akzeptanzkriterien zu Task 2 verlangen, dass "der bestehende Fall über `getCustomFilters()` unverändert grün" bleibt. In `ProviderTest.php` stand kein solcher Fall; die Methode war überhaupt nicht behauptet.
- **Fix:** Der Fall wurde angelegt (`testTheProviderDefinesNoFilterOfItsOwn`). Die Zusage von D-05 ist damit belegt statt vorausgesetzt, und die leere Liste ist gegen ein späteres Einschmuggeln eines eigenen Filternamens bewacht, was der Zweck war, den der Plantext dem angeblich bestehenden Fall zugeschrieben hat.
- **Files modified:** php/tests/Unit/ProviderTest.php
- **Committed in:** `476fa5b`

---

**Total deviations:** 2 auto-fixed (1 blockierend, 1 fehlender Fall)
**Impact on plan:** Kein Scope Creep. Alle Zusagen des Plans sind belegt, eine davon durch einen Fall, den der Plan als schon vorhanden annahm.

## Issues Encountered

- **`php -l` konnte an diesem Arbeitsplatz nicht laufen.** Es gibt kein lokales PHP, und der in 13-04 und 13-05 verwendete Weg über den Container `php:8.2-cli` steht nicht zur Verfügung: die Docker-Engine läuft nicht (`npipe:////./pipe/dockerDesktopLinuxEngine` nicht erreichbar). Das Verifikationsskript des Plans ist darauf vorbereitet (`command -v php >/dev/null 2>&1 && php -l "$f" || true`). Ersatzweise wurde eine Klammerbilanz über beide Dateien gezogen (Blöcke, Klammern, eckige Klammern je 0 nach Abzug von Kommentaren und Zeichenketten) und der Diff Zeile für Zeile gegengelesen. Der maßgebliche Nachweis ist der Job "php -l over the companion app" in `php.yml`, der `php/lib` abdeckt, und der PHPUnit-Job für die Testdatei.
- **Die Testdateien tragen CRLF** (Gotcha aus 13-05). Alle Änderungen wurden mit ausdrücklichem `newline='\r\n'` geschrieben; die Dateien sind nach wie vor rein CRLF und rein ASCII, es gibt keinen Massen-Diff.

## Known Stubs

Keine. Was fehlt, ist die zweite Hälfte von FILT-03, die dieser Plan ausdrücklich nicht baut: `since` und `until` aus der Adresse der eigenen Seite (13-07) und ihre Anzeige als Chip samt Zurücksetzen (13-09). Die Datumsgrenzen des Dialogs reisen bewusst nicht in die Adresse der Ergebnisseite, und der Grund steht an `entryPoint()`.

## Threat Flags

Keine neue Oberfläche außerhalb des `<threat_model>` des Plans. Keine neue Route, keine neue Log-Zeile, kein neuer Weg über die Rechtegrenze.

| Threat | Stand |
|---|---|
| T-13-27 (Filterwert falscher Klasse) | mitigiert: `epochOf()` prüft die Klasse; ein Fall über fünf Werte falscher Art (Zeichenkette, Zahl, `null`, Wahrheitswert, Objekt) |
| T-13-28 (absurde Datumsgrenze) | mitigiert: `epochWithin()` klemmt, zwei Fälle (oberhalb `EPOCH_MAX`, negativ) |
| T-13-29 (kaputte Providerliste) | mitigiert: `getCustomFilters()` leer, jetzt mit eigenem Fall |
| T-13-30 (Umgehung der Rechtegrenze) | unverändert akzeptiert: derselbe `SearchService::run`, kein neuer Zweig |
| T-13-31 (Log mit Suchbegriff oder Datum) | mitigiert: keine neue Log-Zeile in der Datei |
| T-13-SC (Paketinstallation) | kein Paket installiert |

## Gates

| Gate | Ergebnis |
|---|---|
| `php -l` php/lib/Search/Provider.php | NICHT gelaufen: kein lokales PHP, Docker-Engine aus; CI-Job `php -l` deckt `php/lib` ab |
| `php -l` php/tests/Unit/ProviderTest.php | NICHT gelaufen, gleicher Grund; Ersatz: Klammerbilanz 0/0/0 über beide Dateien |
| PHPUnit | NICHT gelaufen: CI-only, die Suite braucht eine Auscheckung von nextcloud/server als Autoload-Raum |
| Verifikationsskript Task 1 (`BUILTIN_SINCE`, `BUILTIN_UNTIL`, `epochOf`, `new SearchFilters`) | GRUEN |
| Verifikationsskript Task 2 (`BUILTIN_SINCE`, `BUILTIN_UNTIL`, `DateTimeImmutable` im Test) | GRUEN |
| `uv run pytest tests/test_php_trust_boundary.py tests/test_php_acl_boundary.py -q` | 29 passed |
| `uv run pytest tests/test_measurement_scripts.py -q` | 228 passed |
| `uv run pytest -q` (ganze Backend-Suite) | 2120 passed, 15 skipped |
| `uv run ruff check tests/test_measurement_scripts.py` | All checks passed |
| `uv run ruff format --check tests/test_measurement_scripts.py` | already formatted |
| Zeichensatz beider PHP-Dateien | rein CRLF, rein ASCII (keine Umlaute im Code) |
| Vokabular-Gate (gesperrtes Wort in den neuen Zeilen) | 0 Treffer |

## User Setup Required

Keine. Kein Paket, kein Schema, kein Reindex.

## Next Phase Readiness

- Plan 13-07 baut den `SearchFilters` der eigenen Seite aus der Adresse und übergibt ihn in `PageController::outcome()`. Die Klemmung dort kann `SearchFilters::EPOCH_MAX` genauso lesen wie `epochWithin()` hier; der Unterschied ist die Zeitzone, die die Schnellbereiche brauchen und dieser Pfad nicht (13-RESEARCH Befund 10).
- Plan 13-09 zeigt die gesetzten Grenzen als Chip und bietet das Zurücksetzen an; `SearchFilters::hasAny()` ist die Stelle, an der diese Anzeige entscheidet, ob sie überhaupt erscheint.
- FILT-03 ist NICHT als erfüllt markiert: die Hälfte auf der Ergebnisseite liegt in 13-07 und 13-09.
- STATE.md und ROADMAP.md wurden nicht angefasst (Worktree-Modus); der Orchestrator zieht sie nach dem Merge zentral nach.

## Self-Check: PASSED

- `php/lib/Search/Provider.php` FOUND (enthält `IFilter::BUILTIN_SINCE`, `IFilter::BUILTIN_UNTIL`, `epochOf`, `epochWithin`, `new SearchFilters`)
- `php/tests/Unit/ProviderTest.php` FOUND (enthält `BUILTIN_SINCE`, `BUILTIN_UNTIL`, `DateTimeImmutable`, `getCustomFilters`)
- `backend/tests/test_measurement_scripts.py` FOUND (`PHP_TREE_HASH_TODAY = b7a029cc...`)
- Commit `3cf3044` FOUND
- Commit `476fa5b` FOUND
- Commit `486d30f` FOUND
- Automatisierte Verifikation aus Task 1 und Task 2: beide GRUEN
