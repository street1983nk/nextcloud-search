---
phase: 13-filter-und-sortierung-auf-der-ergebnisseite
plan: 04
subsystem: php-companion
tags: [wertobjekt, searchfilters, rumpfbau, klemm-disziplin, filt-01, filt-02, filt-03]

requires:
  - phase: 13-filter-und-sortierung-auf-der-ergebnisseite
    plan: 03
    provides: "SearchRequest.types/.sort/.since/.until, SnippetsRequest ohne sort, SEARCH_MTIME_MAX"
provides:
  - "SearchFilters: das eine benannte Wertobjekt fuer Filter und Sortierung in der PHP-Haelfte"
  - "SearchFilters::TYPES, ::SORTS, ::SORT_DEFAULT, ::EPOCH_MAX als geschlossene Wertelisten"
  - "SearchFilters::none() und ::hasAny() fuer Dialogfall, Zuruecksetzen-Link (D-06) und Filter-Leerzustand (D-07)"
  - "ExAppService::searchCandidates(..., SearchFilters $filters, ...) legt types, sort, since und until in den /search-Rumpf"
  - "ExAppService::snippets(..., SearchFilters $filters, ...) legt types, since und until in den /snippets-Rumpf, nie sort"
  - "typeGroupsWithin und epochWithin: Klemm-Disziplin in derselben Reihe wie MIN_LIMIT/MAX_LIMIT"
affects: [13-05, 13-06, 13-07, 13-08, 13-09]

tech-stack:
  added: []
  patterns:
    - "Ein Pflichtargument steht vor den Argumenten mit Vorgabewert, weil PHP seit 8.0 die andere Reihenfolge abkuendigt"
    - "Eine Allowlist wird durchlaufen statt abgefragt: Filterung, Doppelfreiheit, Laengengrenze und Reihenfolge entstehen dann baulich"
    - "Ein Wert in seiner Vorgabe wird nicht in den Rumpf geschrieben, damit die ungefilterte Anfrage byteweise dieselbe bleibt"

key-files:
  created:
    - php/lib/Service/SearchFilters.php
  modified:
    - php/lib/Service/ExAppService.php
    - php/lib/Service/SearchService.php
    - php/tests/Unit/ExAppServiceTest.php
    - php/tests/Unit/SearchServiceTest.php
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "SearchFilters bekommt eine none()-Fabrik, obwohl das Vorbild SearchCaps ausdruecklich keine hat; die Abweichung steht begruendet im Klassen-Docstring"
  - "Der neue Parameter steht vor den beiden Uhrwerten statt am Ende der Liste, weil ein Pflichtargument hinter einem optionalen seit PHP 8.0 abgekuendigt ist"
  - "typeGroupsWithin laeuft ueber die geschlossene Menge und nicht ueber die Eingabe, damit unbekannter Name, Dublette, Ueberlaenge und Reihenfolge baulich erledigt sind"
  - "php -l laeuft auf dieser Maschine ueber das offizielle Docker-Image php:8.2-cli, PHPUnit bleibt CI-only"

patterns-established:
  - "Ein neues Pflichtargument an einer Methode mit Uhrwerten wird vor die Uhrwerte gesetzt, nicht hinter sie"

requirements-completed: []  # FILT-01, FILT-02 und FILT-03 tragen noch 13-05 bis 13-09

duration: 47min
completed: 2026-09-16
---

# Phase 13 Plan 04: SearchFilters und die zwei Rümpfe an den Container Summary

**Filter und Sortierung haben in der PHP-Hälfte ab jetzt einen Namen: ein `readonly`-Wertobjekt mit vier Feldern und geschlossenen Wertelisten, zwei Container-Rümpfe, die genau die Felder tragen, die sie tragen dürfen, und eine Klemm-Disziplin, unter der ein von Hand gebautes Lesezeichen eine Antwort erzeugt statt einer Fehlerseite.**

## Performance

- **Duration:** 47 min
- **Started:** 2026-09-16T20:18:00Z
- **Completed:** 2026-09-16T21:05:00Z
- **Tasks:** 3
- **Files modified:** 6 (1 neu, 5 geändert)

## Accomplishments

- `php/lib/Service/SearchFilters.php` (135 Zeilen) ist die Heimat der vier Werte: `types` als `list<string>`, `sort`, `since` und `until`. Konstruktor-Promotion mit `public readonly`, nach der Bauform von `SearchCaps`, und im Klassen-Docstring die drei Sätze, die ein späterer Leser sonst raten müsste: warum es ein Objekt ist, warum es anders als `SearchCaps` eine Fabrik hat, und was es ausdrücklich nicht tut.
- Die vier Klassenkonstanten tragen ihre Begründung wie `MIN_LIMIT`/`MAX_LIMIT` es vormachen. `TYPES` führt die sechs Gruppennamen in der Reihenfolge der Oberfläche, `SORTS` die drei Modi, `SORT_DEFAULT` den Wert `relevance`, und `EPOCH_MAX` dieselbe Zahl wie `SEARCH_MTIME_MAX` im Container, samt dem Satz, warum beide Hälften dieselbe Obergrenze führen müssen.
- `none()` gibt dem Zustand "nichts eingegrenzt" einen Namen, `hasAny()` ist die eine Stelle, an der später der Zurücksetzen-Link (D-06) und der Filter-Leerzustand (D-07) entscheiden. Die Sortierung zählt nicht mit, und der Docstring sagt warum: ein Sortiermodus nimmt nichts weg.
- Die Datei enthält keine einzige Dateiendung. Die Abbildung von Gruppe auf Endung lebt weiterhin allein in `query/rewrite.py::TYPE_GROUPS`; ein zweites Vokabular wäre genau der Bruch, den 13-RESEARCH verbietet.
- `ExAppService::searchCandidates` und `::snippets` nehmen je ein `SearchFilters` ohne Vorgabewert. Der `/search`-Rumpf kann `types`, `sort`, `since` und `until` tragen, der `/snippets`-Rumpf `types`, `since` und `until` und an keiner Stelle den Sortiermodus; über der Stelle steht die Begründung samt Verweis auf die benannte Ausnahme im Gleichstands-Gate.
- Ein Wert in seiner Vorgabe wird nicht geschrieben. Eine ungefilterte Suche schickt damit byteweise die Anfrage, die sie vor dieser Phase war, und ein echter Wert geht nicht zwischen vier Konstanten unter.
- `typeGroupsWithin` läuft über die geschlossene Menge statt über die Eingabe. Unbekannter Name (T-13-17), Dublette, Überlänge (T-13-18) und die Reihenfolge der Oberfläche sind damit baulich erledigt und nicht vier einzeln vergessbare Prüfungen. `epochWithin` klemmt auf 0 bis `EPOCH_MAX`; nichts wird abgelehnt und nichts wirft.
- `filterCandidates()` ist inhaltlich unverändert und lässt weiterhin ausschließlich `fileId` durch. Ein neuer Absatz im Docstring hält fest, dass auch diese Phase nichts weiter durchreicht und das Änderungsdatum deshalb aus dem bestätigten Knoten kommt (Plan 13-05), nie aus der Antwort des Containers (T-13-20).
- Vierzehn neue Testfälle in `ExAppServiceTest.php` behaupten je über den abgefangenen Rumpf, nicht über die Absicht des Aufrufers: vier Happy-Path-Fälle, neun Rand- und Negativpfade und der Fall, der FILT-02 auf der PHP-Seite hält.

## Task Commits

Jeder Task wurde einzeln committet:

1. **Task 1: Das Wertobjekt SearchFilters** - `8fe3d32` (feat)
2. **Task 2: Die zwei Rümpfe an den Container, mit Klemm-Disziplin** - `d69c7b1` (feat)
3. **Task 3: Testfälle über den tatsächlich abgeschickten Rumpf** - `edfa8d8` (test)
4. **Abweichung: Baumhash der PHP-Hälfte nachziehen** - `f6d9e13` (test)

## Files Created/Modified

- `php/lib/Service/SearchFilters.php` (neu, 135 Zeilen) - das Wertobjekt mit vier Feldern, vier Konstanten, `none()` und `hasAny()`
- `php/lib/Service/ExAppService.php` - beide Signaturen, beide Rümpfe, `typeGroupsWithin`, `epochWithin`, der neue Absatz im Docstring von `filterCandidates`
- `php/lib/Service/SearchService.php` - die zwei Aufrufstellen reichen vorerst `SearchFilters::none()` weiter (Zwischenstufe, siehe unten)
- `php/tests/Unit/ExAppServiceTest.php` - vierzehn neue Fälle in einem eigenen Abschnitt, zwei Hilfsverfahren für den abgefangenen Rumpf, sieben bestehende Aufrufe um das neue Pflichtargument ergänzt
- `php/tests/Unit/SearchServiceTest.php` - drei Rückrufsignaturen mechanisch nachgezogen, ein Import
- `backend/tests/test_measurement_scripts.py` - `PHP_FILES_TODAY` und `PHP_TREE_HASH_TODAY` nachgezogen, mit Begründungsabsatz

## Decisions Made

- **Der neue Parameter steht vor den beiden Uhrwerten und nicht am Ende der Liste.** Der Plantext verlangt beides: "am Ende der Liste" und "ohne Vorgabewert". Beides zusammen geht nicht, weil `$secondsLeft` und `$ceilingSeconds` Vorgabewerte tragen und ein Pflichtargument hinter einem optionalen seit PHP 8.0 abgekündigt ist. Die Zusage, auf die es dem Plan ankommt, bleibt unverletzt: es gibt keinen Vorgabewert, also kann ein vergessener Aufrufer nicht aussehen wie einer ohne Filter. Die Stelle ist zudem die sachlich richtige, weil dort die Argumente stehen, die sagen, was gefragt wird, und nicht die beiden, die sagen, wie lange dieser Aufrufer wartet. Die Begründung steht als `@param`-Zeile an beiden Methoden.
- **`typeGroupsWithin` läuft über die geschlossene Menge, nicht über die Eingabe.** Der Plan beschreibt vier Schritte (filtern, doppelfrei machen, auf sechs kürzen, `array_values`). Ein Durchlauf über `SearchFilters::TYPES` leistet alle vier als Eigenschaft der Laufrichtung und liefert zusätzlich die Reihenfolge der Oberfläche, die Task 3 ohnehin einfordert. Vier Prüfungen, die einzeln vergessen werden können, sind damit eine Schleife, die nichts vergessen kann.
- **`none()` trotz des Vorbilds ohne Fabrik.** `SearchCaps` verweigert eine Vorgabe mit einem guten Argument ("a default is a number nobody has to think about"). Hier ist "nichts eingegrenzt" keine bequeme Zahl, sondern ein benannter Zustand des Produkts: der Dialog hat keine Chips, und jeder Aufrufer ohne Eingrenzung ist in demselben Zustand. Die Abweichung steht im Klassen-Docstring, sonst liest der nächste Leser sie als Nachlässigkeit.
- **Die Zwischenstufe in `SearchService` ist als solche markiert.** Beide Aufrufstellen reichen `SearchFilters::none()` weiter, damit der Baum am Ende dieses Plans lauffähig bleibt. Über der Stelle steht, dass Plan 13-05 `run()` sein eigenes `SearchFilters`-Argument gibt; ohne diesen Satz sieht die Zeile in vier Wochen aus wie eine Entscheidung.
- **`php -l` ist auf dieser Maschine doch möglich.** 13-RESEARCH hält fest, dass lokal kein PHP vorhanden ist, und leitet daraus ab, dass die Syntax erst in CI belegt wird. Docker ist vorhanden, und das offizielle Image `php:8.2-cli` führt dieselbe Version wie der Lint-Job in `.github/workflows/php.yml`. Alle vier geänderten PHP-Dateien sind damit lokal syntaxgeprüft, vor dem Commit statt danach. PHPUnit bleibt CI-only, weil diese Suite eine Auscheckung von nextcloud/server als Autoload-Raum braucht.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierend] Ein Pflichtargument am Ende der Parameterliste ist seit PHP 8.0 abgekündigt**

- **Found during:** Task 2
- **Issue:** Der Plan verlangt `SearchFilters $filters` "am Ende der Liste" und "ohne Vorgabewert". Beide Methoden enden auf `$secondsLeft` und `$ceilingSeconds`, die je einen Vorgabewert tragen. Ein Pflichtargument dahinter ist die Konstellation, die PHP 8.0 abgekündigt hat ("Optional parameter declared before required parameter"), und die Companion-App erklärt `php >= 8.2`.
- **Fix:** Das Argument steht in beiden Signaturen hinter `$titleOnly` und vor den beiden Uhrwerten, weiterhin ohne Vorgabewert. Die `@param`-Zeile nennt beide Gründe, den technischen und den inhaltlichen.
- **Files modified:** php/lib/Service/ExAppService.php
- **Verification:** `php -l` über `php:8.2-cli` grün und ohne Abkündigungsmeldung
- **Committed in:** `d69c7b1`

**2. [Rule 3 - Blockierend] Drei Rückrufsignaturen in SearchServiceTest hätten mit einem TypeError geendet**

- **Found during:** Task 2
- **Issue:** `SearchServiceTest.php` doppelt die beiden Containeraufrufe mit `willReturnCallback` und typisierten Positionsparametern. Ein an sechster Stelle eingeschobenes Argument hätte in drei dieser Rückrufe ein `SearchFilters` auf einen `float`-Parameter gelegt, was ein TypeError ist und nicht ein roter Testfall. Die Datei steht nicht in `files_modified` des Plans.
- **Fix:** Die drei Signaturen führen den neuen Parameter an derselben Stelle wie die Methode. Sonst wurde an der Datei nichts geändert; keine Behauptung, keine Erwartung, kein Fall.
- **Files modified:** php/tests/Unit/SearchServiceTest.php
- **Verification:** `php -l` grün; die Fälle selbst laufen in CI
- **Committed in:** `d69c7b1`

**3. [Rule 3 - Blockierend] Der Baumhash der PHP-Hälfte war nach Task 3 rot**

- **Found during:** Gesamtlauf der Backend-Suite nach Task 3
- **Issue:** `test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_php_half` hält Anzahl und sha256 über alle PHP-Dateien unter `php/`. Dieselbe Mechanik wie der Paket-Baumhash in 13-01 und 13-03, diesmal auf der PHP-Seite: `SearchFilters.php` ist eine Datei mehr (63 auf 64), vier weitere haben ihre Bytes geändert.
- **Fix:** `PHP_FILES_TODAY = 64` und `PHP_TREE_HASH_TODAY = fd8bd9de...`, darüber der vorgeschriebene Begründungsabsatz mit Datum, Plan und den fünf betroffenen Dateien. Die beiden Messwertkonstanten `PHP_FILES` und `PHP_TREE_HASH` der Messung vom 09.09.2026 bleiben unberührt, wie ihr eigener Kommentar es verlangt.
- **Files modified:** backend/tests/test_measurement_scripts.py
- **Verification:** `uv run python -m pytest tests/test_measurement_scripts.py -q` = 228 passed
- **Committed in:** `f6d9e13`

---

**Total deviations:** 3 auto-fixed (alle drei blockierend, keine Erweiterung des Umfangs)
**Impact on plan:** Kein Scope Creep. Die Zusagen des Plans sind unverändert belegt; eine davon (die Stelle des Parameters) ist gegenüber dem Plantext präzisiert, weil der Plantext an dieser Stelle mit PHP unvereinbar war.

## Issues Encountered

Keine offenen. Ein Punkt wurde gegengeprüft statt angenommen: ob die Verifikationsskripte des Plans die Schlüssel wirklich im Rumpf und nicht in einem Hilfsverfahren sehen. Sie lesen ein Fenster von 600 Zeichen hinter dem Pfadliteral, also stehen die vier Schlüssel bewusst im Aufruf selbst und nicht in einer weiter unten gebauten Abbildung.

## Known Stubs

Keine. Was fehlt, ist kein Platzhalter, sondern die Hälfte, die dieser Plan ausdrücklich nicht baut: `SearchService::run` nimmt noch keine Filter entgegen und reicht deshalb `SearchFilters::none()` weiter. Die Zeile ist an beiden Aufrufstellen als Zwischenstufe von 13-04 kommentiert und trägt den Verweis auf 13-05. `hasAny()` hat in diesem Plan noch keinen Leser; es ist die Nahtstelle für D-06 und D-07 in 13-09, nicht toter Code in der PHP-Laufzeit (PHP kennt kein vulture-Gate, und die Methode steht in der Zusagenliste des Plans).

## Threat Flags

Keine neue Oberfläche außerhalb des `<threat_model>` des Plans. Keine neue Route, kein zweiter Kanal, kein zusätzliches Feld aus der Container-Antwort. T-13-17 und T-13-18 sind durch die Laufrichtung von `typeGroupsWithin` erledigt, T-13-19 durch `epochWithin`, T-13-20 durch das unveränderte `filterCandidates()`, T-13-21 durch das Ausbleiben jeder neuen Route (`test_php_trust_boundary.py` grün).

## Gates

| Gate | Ergebnis |
|---|---|
| `php -l` php/lib/Service/SearchFilters.php (über `php:8.2-cli`) | No syntax errors detected |
| `php -l` php/lib/Service/ExAppService.php | No syntax errors detected |
| `php -l` php/lib/Service/SearchService.php | No syntax errors detected |
| `php -l` php/tests/Unit/ExAppServiceTest.php | No syntax errors detected |
| `php -l` php/tests/Unit/SearchServiceTest.php | No syntax errors detected |
| PHPUnit | CI-only (die Suite braucht eine Auscheckung von nextcloud/server als Autoload-Raum, siehe php/tests/bootstrap.php); der Job "PHPUnit over the companion app" in php.yml führt sie |
| `uv run pytest tests/test_php_acl_boundary.py tests/test_php_trust_boundary.py -q` | 29 passed |
| `uv run python -m pytest -q` (ganze Backend-Suite) | 2120 passed, 15 skipped |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` (122 Dateien) | already formatted |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run vulture src tests --min-confidence 80` | keine Meldung |
| Verifikationsskript Task 1 (Klasse, readonly, none, hasAny, keine Dateiendung) | GRUEN |
| Verifikationsskript Task 2 (vier Schlüssel am /search-Rumpf, kein Sortierschlüssel am /snippets-Rumpf) | GRUEN |
| Vokabular-Gate (gesperrtes Wort in den neuen Zeichenketten) | 0 Treffer |

## User Setup Required

Keine. Kein Paket installiert, kein Schema, kein Reindex. Der herangezogene Docker-Container `php:8.2-cli` ist ein Werkzeug des Gates und keine Abhängigkeit des Projekts.

## Next Phase Readiness

- Plan 13-05 kann `SearchService::run` sein eigenes `SearchFilters`-Argument geben und es an beiden Aufrufstellen statt `SearchFilters::none()` weiterreichen; beide Stellen sind kommentiert und stehen nebeneinander.
- Das Änderungsdatum kommt in 13-05 aus `$node->getMTime()` am bestätigten Knoten. `filterCandidates()` bleibt dabei unverändert, und der Docstring sagt das jetzt ausdrücklich; wer dort ein `mtime` durchreichen will, liest zuerst den Grund.
- Plan 13-07 baut den `SearchFilters` der Seite aus der Adresse. Das Objekt prüft nichts und wirft nichts: die geschlossene Prüfung mit stillem Rückfall gehört in den `PageController`, und `SearchFilters::TYPES`, `::SORTS` und `::EPOCH_MAX` sind die Listen, gegen die dort geprüft wird. Der Container lehnt einen unbekannten Wert weiterhin mit 422 ab; die Klemmung in `ExAppService` ist die zweite Schranke, nicht die erste.
- Plan 13-09 liest `hasAny()` für den Zurücksetzen-Link (D-06) und den Filter-Leerzustand (D-07). Die Sortierung zählt dort nicht mit, und der Docstring der Methode hält fest, warum.
- FILT-01, FILT-02 und FILT-03 sind ausdrücklich NICHT als erfüllt markiert: alle drei tragen noch 13-05 bis 13-09.

## Self-Check: PASSED

- `php/lib/Service/SearchFilters.php` FOUND (135 Zeilen, `min_lines: 60` erfüllt, enthält `final class SearchFilters`, `public readonly`, `none()`, `hasAny()`, `presentations`, keine Dateiendung)
- `php/lib/Service/ExAppService.php` FOUND (enthält `SearchFilters`, `'types'` am /search-Rumpf, kein Sortierschlüssel am /snippets-Rumpf)
- `php/lib/Service/SearchService.php` FOUND (enthält `SearchFilters::none()` an beiden Aufrufstellen)
- `php/tests/Unit/ExAppServiceTest.php` FOUND (enthält `SearchFilters`, `sort`, `snippets`)
- `php/tests/Unit/SearchServiceTest.php` FOUND
- `backend/tests/test_measurement_scripts.py` FOUND
- Commit `8fe3d32` FOUND
- Commit `d69c7b1` FOUND
- Commit `edfa8d8` FOUND
- Commit `f6d9e13` FOUND
- Automatisierte Verifikation aus Task 1, 2 und 3: alle GRUEN

---
*Phase: 13-filter-und-sortierung-auf-der-ergebnisseite*
*Completed: 2026-09-16*
