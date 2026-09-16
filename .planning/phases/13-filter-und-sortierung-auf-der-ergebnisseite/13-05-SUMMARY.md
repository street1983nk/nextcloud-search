---
phase: 13-filter-und-sortierung-auf-der-ergebnisseite
plan: 05
subsystem: php-companion
tags: [searchservice, approvedhit, mtime, rechtegrenze, zweistufenprotokoll, filt-01, filt-02, filt-05]

requires:
  - phase: 13-filter-und-sortierung-auf-der-ergebnisseite
    plan: 04
    provides: "SearchFilters, ExAppService::searchCandidates(..., SearchFilters, ...), ::snippets(..., SearchFilters, ...)"
provides:
  - "ApprovedHit.mtime: das fünfte Feld, aus dem bestätigten Knoten und nie aus der Containerantwort"
  - "SearchService::run(IUser, string, bool, int, SearchCaps, SearchFilters): die Filter als benanntes Objekt in der Signatur"
  - "Die Weitergabe an beide Containeraufrufe über genau einen Weg"
  - "Acht Testfälle über Weitergabe, Herkunft des Datums und den unveränderten Recheck"
affects: [13-06, 13-07, 13-08, 13-09]

tech-stack:
  added: []
  patterns:
    - "Ein Feld, das die Anzeige erreicht, wird hinter der Rechtegrenze gelesen und nie davor"
    - "Ein neuer Parameter am Ende einer Signatur bricht keinen Rückruf: PHP nimmt überzählige Argumente an einer Closure hin, anders als ein Parameter, der in die Mitte geschoben wird"

key-files:
  created: []
  modified:
    - php/lib/Service/ApprovedHit.php
    - php/lib/Service/SearchService.php
    - php/lib/Controller/PageController.php
    - php/lib/Search/Provider.php
    - php/tests/Unit/SearchServiceTest.php
    - php/tests/Unit/ProviderTest.php
    - php/tests/Unit/PageControllerTest.php
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "mtime bleibt ein Pflichtargument von ApprovedHit; der Preis sind elf mechanisch nachgezogene Testliterale, der Gegenwert ist, dass ein vergessener Aufrufer nicht wie einer ohne Datum aussieht"
  - "Der Filter wird auf der PHP-Seite kein zweites Mal angewendet, und der Grund steht als Absatz am @param von run()"
  - "Der neue Parameter steht am Ende der run-Signatur, weil dort kein Vorgabewert im Weg ist und weil überzählige Argumente an den bestehenden Test-Rückrufen folgenlos bleiben"
  - "Ein Kommentar in SearchService nennt die Leseprüfung ab jetzt beim Wort statt beim Methodennamen, damit die Zählung der Rechtegrenze im Text so bleibt, wie sie war"

patterns-established:
  - "Ein Fall über die Herkunft eines Wertes wird mit zwei absichtlich verschiedenen Zahlen gebaut und behauptet zusätzlich, dass sie verschieden sind"

requirements-completed: []  # FILT-01, FILT-02 und FILT-05 tragen noch 13-06 bis 13-09 und 13-12

duration: 25min
completed: 2026-09-16
---

# Phase 13 Plan 05: Filter durch SearchService, Datum aus dem bestätigten Knoten Summary

**`run()` nimmt die Filter als benanntes Objekt und reicht genau dieses Objekt an beide Containeraufrufe weiter, das Änderungsdatum eines Treffers wird hinter der Rechtegrenze am bestätigten Knoten gelesen statt aus der Containerantwort übernommen, und die Rechtegrenze selbst ist in Zahl, Reihenfolge und Ort unverändert.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-09-16T19:05:00Z
- **Completed:** 2026-09-16T19:30:00Z
- **Tasks:** 3
- **Files modified:** 8 (keine neu)

## Accomplishments

- `ApprovedHit` trägt fünf `public readonly`-Felder. Das fünfte heißt `mtime`, ist die Unix-Epoche in Sekunden und hat seine Begründung in derselben Datei wie das Feld: `filterCandidates()` verwirft das `mtime` des Containers, weil alles vor dem Recheck ein Vorschlag ist, und ein Zeitstempel aus dem Index wäre zusätzlich älter als der Knoten. Die Zählung in der Prosa ist von drei auf vier nachgezogen, und die Kanarienvogel-Ausnahme ist um den einen Satz erweitert, der für das neue Feld gilt.
- `SearchService::run` hat die Signatur `(IUser $user, string $term, bool $titleOnly, int $startCursor, SearchCaps $caps, SearchFilters $filters)`. Der `@param`-Absatz sagt nicht nur, was das Argument ist, sondern was mit ihm ausdrücklich nicht geschieht: der Filter wirkt vor dem Vorfilter des Containers, und ihn hinter dem Recheck noch einmal anzuwenden würde aus jeder Seite eine Stichprobe machen und eine zweite Stelle an der Rechtegrenze eröffnen (T-13-23).
- Beide Containeraufrufe bekommen dasselbe Objekt. Über der Kandidatenstelle steht, dass der Sortiermodus nur dort wirkt, weil der Ausschnittsaufruf nach benannten `fileIds` fragt und eine Antwort auf eine Namensliste keine Reihenfolge kennt; die Auswahl des Rumpfes bleibt Sache von `ExAppService` (FILT-02).
- Das Datum wird mit `(int)$node->getMTime()` gelesen, in derselben Reihe wie Name, Pfad und Mimetyp und ausdrücklich hinter der Typprüfung und hinter der Leseprüfung. Der Kanarienvogel-Zweig übergibt `0` mit einem Satz dazu, warum dort kein Datum entstehen darf.
- `getFirstNodeById` steht weiterhin genau einmal in der Datei, die Leseprüfung ebenso. `test_php_acl_boundary.py` und `test_php_trust_boundary.py` sind grün (29 Fälle), es kam keine Route und keine zweite Aufrufstelle hinzu.
- Acht neue Testfälle in `SearchServiceTest.php`: drei über die Weitergabe (Kandidatenaufruf, Ausschnittsaufruf, der ungefilterte Fall), einer über die Herkunft des Datums mit zwei absichtlich verschiedenen Zahlen, und vier Rand- und Negativpfade (nicht auflösbarer Knoten ohne Ersatzdatum, nicht lesbarer Knoten dessen Datum nie gelesen wird, Kanarienvogel mit `mtime` 0, leere Kandidatenliste unter gesetztem Filter).
- Die beiden Aufrufer sind als Zwischenstufe nachgezogen und an beiden Stellen kommentiert: `PageController::outcome()` und `Provider::search()` reichen `SearchFilters::none()` weiter, mit dem Verweis auf 13-07 beziehungsweise 13-06.

## Task Commits

Jeder Task wurde einzeln committet:

1. **Task 1: Das fünfte Feld an ApprovedHit** - `97d56a8` (feat)
2. **Task 2: run(SearchFilters), das Datum aus dem Knoten und beide Containeraufrufe** - `f21c68f` (feat)
3. **Task 3: Testfälle für Weitergabe, Herkunft des Datums und den unveränderten Recheck** - `d2f7664` (test)
4. **Abweichung: Baumhash der PHP-Hälfte nachziehen** - `0cb21ca` (test)

## Files Created/Modified

- `php/lib/Service/ApprovedHit.php` - das fünfte Feld, der fortgeschriebene Klassen-Docstring, die erweiterte Kanarienvogel-Ausnahme
- `php/lib/Service/SearchService.php` - die Signatur, der `@param`-Absatz über das Nicht-noch-einmal-Anwenden, `$filters` an beiden Aufrufen, `(int)$node->getMTime()` am bestätigten Knoten, `0` im Kanarienvogel-Zweig
- `php/lib/Controller/PageController.php` - Import und `SearchFilters::none()` als kommentierte Zwischenstufe für 13-07
- `php/lib/Search/Provider.php` - dasselbe für 13-06, mit dem Hinweis, warum Typgruppe und Sortierung nicht in den Dialog gehören
- `php/tests/Unit/SearchServiceTest.php` - acht neue Fälle, zwei Hilfsverfahren, `readableFile` um ein Änderungsdatum erweitert, 26 bestehende `run`-Aufrufe um das sechste Argument ergänzt
- `php/tests/Unit/ProviderTest.php` - neun `ApprovedHit`-Literale um ihr fünftes Feld ergänzt
- `php/tests/Unit/PageControllerTest.php` - zwei `ApprovedHit`-Literale um ihr fünftes Feld ergänzt
- `backend/tests/test_measurement_scripts.py` - `PHP_TREE_HASH_TODAY` nachgezogen, mit Begründungsabsatz

## Decisions Made

- **`mtime` ist ein Pflichtargument von `ApprovedHit` geblieben.** Ein Vorgabewert `0` hätte elf Testliterale unberührt gelassen, aber `0` heißt in diesem Feld "es gibt keinen Knoten", und ein Aufrufer, der das Datum schlicht vergisst, sähe damit aus wie der Kanarienvogel. Das ist dasselbe Argument, mit dem 13-04 `SearchFilters` ohne Vorgabewert geführt hat. Der Preis ist mechanisch und einmalig, der Gegenwert gilt für jeden künftigen Aufrufer.
- **Der neue Parameter steht am Ende der `run`-Signatur, und das ist hier ohne Nebenwirkung.** In 13-04 musste das Argument in die Mitte, weil zwei Uhrwerte mit Vorgabewert am Ende standen; `run()` hat keine. Wichtiger noch: der Parameter steht hinter allen Positionen, die die bestehenden Rückrufe in `ProviderTest` und `PageControllerTest` typisiert deklarieren. PHP nimmt überzählige Argumente an einer Closure hin, also bleiben diese Rückrufe unverändert lauffähig, während ein in die Mitte geschobener Parameter dort dieselben TypeErrors erzeugt hätte wie in 13-04.
- **Ein Kommentar nennt die Leseprüfung beim Wort und nicht beim Methodennamen.** Der neue Absatz über der Trefferzeile sollte sagen, hinter welcher Frage das Datum gelesen wird. Mit dem Methodennamen im Text wäre die reine Textzählung von `isReadable` in dieser Datei von zwei auf drei gestiegen. Der maßgebliche Wächter (`test_php_acl_boundary.py`) entfernt Kommentare vor dem Zählen und wäre grün geblieben, aber eine Datei, in der eine naive Zählung etwas anderes sagt als die Zählung des Gates, lädt zu genau dem Missverständnis ein, gegen das das Gate gebaut ist.
- **Der Filter wird auf der PHP-Seite nicht noch einmal angewendet, und das steht jetzt geschrieben.** Ohne den Satz ist die naheliegende spätere Ergänzung ein zweiter Schnitt hinter dem Recheck, und der hätte zwei Folgen: die Seitengröße wäre nicht mehr die Seitengröße, und es gäbe eine zweite Stelle, an der über Sichtbarkeit entschieden wird.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierend] Elf `ApprovedHit`-Literale und 26 `run`-Aufrufe in drei Testdateien**

- **Found during:** Task 2
- **Issue:** Das fünfte Pflichtfeld an `ApprovedHit` und der sechste Pflichtparameter an `run()` machen jeden bestehenden Aufruf zu einem `ArgumentCountError`. Betroffen sind neben `SearchServiceTest.php` (im Plan genannt) auch `ProviderTest.php` und `PageControllerTest.php` mit je einer Handvoll `ApprovedHit`-Literalen; beide stehen nicht in `files_modified` des Plans.
- **Fix:** Mechanisch und byteweise (die drei Dateien tragen CRLF, siehe Gotcha unten): 26 `run`-Aufrufe bekommen `SearchFilters::none()`, elf Literale bekommen `0` als fünftes Feld. Keine Behauptung, keine Erwartung und kein Fall wurde dabei geändert. `0` ist an diesen Stellen auch inhaltlich richtig: der Dialog zeigt nie ein Datum, und die Seitenfälle sagen nichts über eines.
- **Files modified:** php/tests/Unit/SearchServiceTest.php, php/tests/Unit/ProviderTest.php, php/tests/Unit/PageControllerTest.php
- **Verification:** `php -l` über alle drei grün; die Fälle selbst laufen in CI
- **Committed in:** `f21c68f`

**2. [Rule 1 - Fehler im Verifikationsskript des Plans] Die Zählung von `isReadable` konnte nie 1 ergeben**

- **Found during:** Task 2
- **Issue:** Das Verifikationsskript zu Task 2 verlangt `grep -c 'isReadable' php/lib/Service/SearchService.php` gleich 1. Am Baum vor diesem Plan waren es 2, weil ein Kommentar im Rundenkopf die Methode namentlich nennt ("isReadable() below stays the one and only permission decision"). Das Skript wäre also schon vor jeder Änderung rot gewesen.
- **Fix:** Die Zusage, auf die es dem Plan ankommt, ist belegt und unverändert: genau eine Aufrufstelle von `getFirstNodeById` (Textzählung 1) und genau eine Leseprüfung (Textzählung 2, davon ein Kommentar, unverändert gegenüber dem Stand vor diesem Plan). Der neue Kommentar wurde umformuliert, damit diese Zahl nicht wächst. Der maßgebliche Nachweis ist `test_php_acl_boundary.py`, das mit entfernten Kommentaren und Zeichenketten zählt und grün ist.
- **Files modified:** php/lib/Service/SearchService.php
- **Verification:** `uv run pytest tests/test_php_acl_boundary.py tests/test_php_trust_boundary.py -q` = 29 passed
- **Committed in:** `f21c68f`

**3. [Rule 3 - Blockierend] Der Baumhash der PHP-Hälfte war nach Task 3 rot**

- **Found during:** Gesamtlauf der Backend-Suite nach Task 3
- **Issue:** `test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_php_half` hält Anzahl und sha256 über alle PHP-Dateien unter `php/`. Dieselbe Mechanik wie in 13-01, 13-03 und 13-04.
- **Fix:** `PHP_TREE_HASH_TODAY = da750308...`; `PHP_FILES_TODAY` bleibt bei 64, weil keine Datei hinzukam und keine wegfiel. Darüber der vorgeschriebene Begründungsabsatz mit Datum, Plan und den sieben Dateien, deren Bytes sich geändert haben. Die Messwertkonstanten des Laufs vom 09.09.2026 bleiben unberührt.
- **Files modified:** backend/tests/test_measurement_scripts.py
- **Verification:** `uv run python -m pytest tests/test_measurement_scripts.py -q` = 228 passed
- **Committed in:** `0cb21ca`

---

**Total deviations:** 3 auto-fixed (2 blockierend, 1 Fehler in einem Verifikationsskript des Plans)
**Impact on plan:** Kein Scope Creep. Alle Zusagen des Plans sind belegt; eine Prüfbedingung ist gegenüber dem Plantext präzisiert, weil der Plantext an dieser Stelle gegen den tatsächlichen Baum stand.

## Issues Encountered

Keine offenen. Zwei Punkte wurden gegengeprüft statt angenommen:

- Ob die typisierten Rückrufe in `ProviderTest` und `PageControllerTest` das neue Argument aushalten. Sie halten es aus, weil es am Ende der Liste steht und PHP überzählige Argumente an einer Closure hinnimmt; in 13-04 war genau das anders, weil dort in die Mitte eingefügt wurde.
- Ob `php -l` an diesem Arbeitsplatz überhaupt läuft. Es läuft, über das offizielle Image `php:8.2-cli`, wie 13-04 es etabliert hat.

**Gotcha für Nachfolger:** die drei PHP-Testdateien tragen CRLF. Mechanische Änderungen daran laufen byteweise (`rb` lesen, `rb` schreiben), sonst entsteht ein Massen-Diff über die ganze Datei statt der zwei Zeilen, um die es geht.

## Known Stubs

Keine im Sinne von Platzhaltern in der Anzeige. Was noch fehlt, ist die Hälfte, die dieser Plan ausdrücklich nicht baut: beide Aufrufer reichen weiterhin `SearchFilters::none()` weiter, jeweils mit einem Kommentar, der den Nachfolgeplan benennt (13-06 für die zwei Datumsfilter des Dialogs, 13-07 für den Filter aus der Adresse der eigenen Seite). Das Feld `ApprovedHit::$mtime` hat bis 13-09 keinen Leser in der Anzeige; es ist die Nahtstelle für die Datumszeile unter Sortierung (D-04) und kein toter Code, weil es an jedem Treffer entsteht und in vier Testfällen behauptet wird.

## Threat Flags

Keine neue Oberfläche außerhalb des `<threat_model>` des Plans. Keine neue Route, kein neuer Weg über die Prozessgrenze, kein zusätzliches Feld aus der Container-Antwort. T-13-22 ist durch die Herkunft am Knoten plus den Fall mit zwei verschiedenen Zahlen erledigt, T-13-23 durch die unveränderte Rechtegrenze und den Docstring-Absatz, T-13-24 durch den Fall, der die Reihenfolge über ein nie gelesenes `getMTime()` festhält, T-13-25 durch das Ausbleiben jeder neuen Log-Zeile, T-13-26 durch das Ausbleiben jeder Route (`test_php_trust_boundary.py` grün).

## Gates

| Gate | Ergebnis |
|---|---|
| `php -l` php/lib/Service/ApprovedHit.php (über `php:8.2-cli`) | No syntax errors detected |
| `php -l` php/lib/Service/SearchService.php | No syntax errors detected |
| `php -l` php/lib/Controller/PageController.php | No syntax errors detected |
| `php -l` php/lib/Search/Provider.php | No syntax errors detected |
| `php -l` php/tests/Unit/SearchServiceTest.php | No syntax errors detected |
| `php -l` php/tests/Unit/ProviderTest.php | No syntax errors detected |
| `php -l` php/tests/Unit/PageControllerTest.php | No syntax errors detected |
| PHPUnit | NICHT gelaufen: CI-only, die Suite braucht eine Auscheckung von nextcloud/server als Autoload-Raum (php/tests/bootstrap.php); der Job "PHPUnit over the companion app" in php.yml führt sie |
| `uv run pytest tests/test_php_acl_boundary.py tests/test_php_trust_boundary.py -q` | 29 passed |
| `uv run python -m pytest -q` (ganze Backend-Suite) | 2120 passed, 15 skipped |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` (122 Dateien) | already formatted |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| Verifikationsskript Task 1 (`mtime`-Feld, `filterCandidates` im Docstring) | GRUEN |
| Verifikationsskript Task 2 (`SearchFilters $filters`, `getMTime`, `getFirstNodeById` genau einmal) | GRUEN (die `isReadable`-Zählung siehe Abweichung 2) |
| Verifikationsskript Task 3 (`SearchFilters` und `getMTime` im Test) | GRUEN |
| Vokabular-Gate (gesperrtes Wort in den neuen Zeilen) | 0 Treffer |

## User Setup Required

Keine. Kein Paket installiert, kein Schema, kein Reindex. Der herangezogene Docker-Container `php:8.2-cli` ist ein Werkzeug des Gates und keine Abhängigkeit des Projekts.

## Next Phase Readiness

- Plan 13-06 kann in `Provider::search()` die zwei Datumsfilter des Dialogs lesen und statt `SearchFilters::none()` ein Objekt mit `since` und `until` bauen; die Stelle ist kommentiert, und `getCustomFilters()` bleibt dabei leer.
- Plan 13-07 baut den `SearchFilters` der eigenen Seite aus der Adresse und übergibt ihn an derselben Stelle in `PageController::outcome()`. Die Prüfung mit stillem Rückfall gehört dorthin: der Container lehnt einen unbekannten Gruppen- oder Sortiernamen mit 422 ab, und `SearchFilters::TYPES`, `::SORTS` und `::EPOCH_MAX` sind die Listen, gegen die geprüft wird.
- Plan 13-09 liest `ApprovedHit::$mtime` für die Datumszeile unter `sort=newest|oldest` (D-04). Der Wert ist die rohe Unix-Epoche; die Formatierung ist `OCP\IDateTimeFormatter::formatDate`, und die Zeile existiert unter `relevance` gar nicht. Für einen Treffer mit `fileId` 0 ist der Wert 0, und ein Aufrufer, der eine Datumszeile baut, liest die Kennung zuerst.
- FILT-01, FILT-02 und FILT-05 sind ausdrücklich NICHT als erfüllt markiert: sie tragen noch 13-06 bis 13-09 und 13-12.

## Self-Check: PASSED

- `php/lib/Service/ApprovedHit.php` FOUND (enthält `public readonly int $mtime` und `filterCandidates`)
- `php/lib/Service/SearchService.php` FOUND (enthält `SearchFilters $filters` und `getMTime`, `getFirstNodeById` genau einmal)
- `php/lib/Controller/PageController.php` FOUND (enthält `SearchFilters::none()`)
- `php/lib/Search/Provider.php` FOUND (enthält `SearchFilters::none()`)
- `php/tests/Unit/SearchServiceTest.php` FOUND (enthält `SearchFilters` und `getMTime`)
- `php/tests/Unit/ProviderTest.php` FOUND
- `php/tests/Unit/PageControllerTest.php` FOUND
- `backend/tests/test_measurement_scripts.py` FOUND
- Commit `97d56a8` FOUND
- Commit `f21c68f` FOUND
- Commit `d2f7664` FOUND
- Commit `0cb21ca` FOUND
- Automatisierte Verifikation aus Task 1, 2 und 3: alle GRUEN

---
*Phase: 13-filter-und-sortierung-auf-der-ergebnisseite*
*Completed: 2026-09-16*
