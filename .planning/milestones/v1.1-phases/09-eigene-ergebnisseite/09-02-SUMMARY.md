---
phase: 09-eigene-ergebnisseite
plan: 02
subsystem: testing
tags: [gate, php-attributes, security-regression, textual-scan, pytest]

# Dependency graph
requires:
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: "Gate B mit der zweiten Routenklasse admin und Gate C mit den vier Scannern ueber die drei Admin-Dateien"
provides:
  - "Dritte Routenklasse userpage in Gate B, erkannt an der Attributkombination der Methode"
  - "Pflichtattribute NoAdminRequired und NoCSRFRequired fuer die neue Klasse, halbe Absenkungen bleiben rot"
  - "Waechter test_the_admin_class_did_not_get_softer ueber die vier unveraenderten Admin-Verbote"
  - "Selbst armierende Anti-Vakuitaets-Schranke: 13, sobald php/lib/Controller/PageController.php existiert"
  - "Gate C verbietet insertAdjacentHTML, document.write und IInAppSearch, je mit Selbsttest"
affects: [09-04, 09-05, 09-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Routenklasse an der Attributkombination der Methode, nie am Dateinamen"
    - "Pflichtattribute statt gekuerzter Verbotsliste, damit die strengere Klasse unangetastet bleibt"
    - "Selbst armierende Ratsche: die Schranke steigt, sobald die Datei existiert, die sie meint"

key-files:
  created: []
  modified:
    - backend/tests/test_php_trust_boundary.py
    - backend/tests/test_admin_ui_contract.py

key-decisions:
  - "Die Anti-Vakuitaets-Schranke steht als 13 im Text, wird aber erst verlangt, wenn PageController.php auf der Platte liegt: ein festes >= 13 haette den Baum zwischen Plan 09-02 und 09-04 rot stehen lassen, also genau den Zustand erzeugt, dessentwegen das Gate vor dem Controller kommt"
  - "Die beiden bestehenden Admin-Selbsttests fuer NoAdminRequired und NoCSRFRequired pruefen jetzt die neue Pflichtmeldung statt der Admin-Meldung, weil ihre Muster per Definition in die dritte Klasse fallen; beide bleiben rot, nur die Begruendung wechselt"
  - "Zusaetzlicher Test test_a_route_that_mixes_the_two_old_classes_stays_admin haelt die alte Mischregel und die Erreichbarkeit der ersten beiden Admin-Verbote"
  - "Der IInAppSearch-Scan liegt in Gate C statt in einem vierten Gate, weil er dieselbe Bauart hat: eine Zeichenkette, die nicht vorkommen darf"

patterns-established:
  - "Pflicht-Attributliste (USER_PAGE_REQUIRED) als Gegenstueck zur Verbotsliste: eine Klasse wird durch Tragen betreten, nicht durch Weglassen"
  - "Jeder neue Scan bekommt eine eigene Anti-Vakuitaets-Klausel, die auch die gelesene Dateiliste prueft"

requirements-completed: [UI-03]

# Metrics
duration: 26min
completed: 2026-09-09
---

# Phase 9 Plan 02: Gate B und Gate C lernen die neue Seite Summary

**Gate B kennt seit diesem Plan drei Routenklassen, erkennt die neue Nutzerseite an der Attributkombination FrontpageRoute plus NoAdminRequired plus NoCSRFRequired und laesst die vier Admin-Verbote woertlich unangetastet; Gate C verbietet zusaetzlich insertAdjacentHTML, document.write und IInAppSearch.**

## Performance

- **Duration:** 26 min
- **Started:** 2026-09-08T23:19:00Z
- **Completed:** 2026-09-08T23:45:00Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Die dritte Routenklasse `userpage` existiert, bevor der erste `PageController` gebaut wird: Plan 09-04 kann die Route anlegen, ohne dass der Baum zwischendurch rot steht.
- `FORBIDDEN_ON_ADMIN_ROUTE` steht unveraendert bei seinen vier Eintraegen und ist jetzt selbst gegen einen Test gehalten, der bei jeder Kuerzung rot wird (T-09-04).
- Eine halb abgesenkte Admin-Route hat keinen Weg in die lockere Klasse: `USER_PAGE_REQUIRED` macht beide Absenkungsattribute zur Pflicht, ein einzelnes Attribut ergibt eine unvollstaendige Nutzerseite und eine Meldung (T-09-14).
- Drei textliche Verbote, die heute schon erfuellt sind, sind ab jetzt Gates statt Saetze in einem Dokument, jedes mit sauberem und schmutzigem Muster (T-09-16).
- `_sources()` von Gate C ist unangetastet und traegt den Kommentar, der Plan 09-06 die Erweiterung uebergibt und Pitfall 4 benennt.

## Task Commits

1. **Task 1: Die dritte Routenklasse userpage in Gate B** , `843dbe1` (test)
2. **Task 2: Die Selbsttests der neuen Klasse** , `afa995e` (test)
3. **Task 3: Drei textliche Verbote in Gate C** , `974ff2b` (test)

## Files Created/Modified

- `backend/tests/test_php_trust_boundary.py` , dritte Routenklasse `userpage` mit `USER_PAGE_REQUIRED` und `FORBIDDEN_ON_USER_PAGE_ROUTE`, dritter Zweig in `scan_source`, sauberes Muster `_USER_PAGE` plus vier schmutzige Ableitungen, Waechter ueber die Admin-Verbote, selbst armierende Schranke 12 nach 13
- `backend/tests/test_admin_ui_contract.py` , zwei neue Skriptverbote in `scan_script`, neuer Scan `scan_app_php_sources` ueber `php/lib/**/*.php` mit eigener Anti-Vakuitaets-Klausel, drei neue Selbsttests, Kommentar an `_sources()`

## Decisions Made

- **Die Schranke armiert sich selbst.** `assert len(routes) >= 13` steht woertlich im Gate, aber hinter `if PAGE_CONTROLLER.is_file()`. Der Baum hat heute zwoelf Routen; eine unbedingte 13 haette dieses Gate von Plan 09-02 bis Plan 09-04 rot stehen lassen, also genau den Zustand hergestellt, dessentwegen die Klasse vor dem Controller kommt. Sobald `php/lib/Controller/PageController.php` existiert, steht die Ratsche bei 13 und eine verlorene Seitenroute ist ein roter Test.
- **Die Klassenerkennung schlaegt die Mischregel nicht.** Eine Methode mit `ApiRoute` **und** `FrontpageRoute` bleibt `admin`, auch wenn sie ein Absenkungsattribut traegt. Ohne diese Reihenfolge waere die neue Klasse der Weg an der Admin-Liste vorbei: ein `FrontpageRoute` plus `NoCSRFRequired` auf eine ExApp-Route geheftet, und die strengere Regel schwiege.
- **Der `IInAppSearch`-Scan liegt in Gate C.** Er prueft nicht die drei Seitendateien, sondern `php/lib/**/*.php`, hat aber dieselbe Bauart wie alles andere in dieser Datei: eine Zeichenkette, die nicht vorkommen darf. Ein vierter Gate haette dieselben zehn Zeilen in einer neuen Datei wiederholt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Die Anti-Vakuitaets-Schranke musste sich selbst armieren**

- **Found during:** Task 1
- **Issue:** Der Plan verlangt gleichzeitig `assert len(routes) >= 13` und einen gruenen `pytest`-Lauf. Der Baum deklariert heute genau zwoelf Routen, die dreizehnte kommt erst mit dem `PageController` aus Plan 09-04. Beides zusammen ist woertlich nicht erfuellbar.
- **Fix:** Die Zeile steht woertlich im Gate, aber hinter `if PAGE_CONTROLLER.is_file()`, mit `else: assert len(routes) >= 12` und einem Kommentarblock, der die Konstruktion begruendet. Damit gilt die Akzeptanzpruefung (`grep -n 'assert len(routes) >= 13'` findet genau eine Zeile) und der Baum bleibt gruen, bis die Route wirklich da ist.
- **Files modified:** backend/tests/test_php_trust_boundary.py
- **Verification:** `pytest -q tests/test_php_trust_boundary.py` gruen, `grep -n 'assert len(routes) >= 13'` findet genau eine Zeile
- **Committed in:** `843dbe1`

**2. [Rule 1 - Bug] Zwei bestehende Admin-Selbsttests pruefen die falsche Meldung**

- **Found during:** Task 1
- **Issue:** `_admin_route_carrying("NoAdminRequired")` und `_admin_route_carrying("NoCSRFRequired")` fallen mit der neuen Erkennung per Definition in die dritte Klasse. Beide Muster bleiben rot, aber die Meldung nennt jetzt das fehlende Pflichtattribut statt des verbotenen. Die beiden Tests behaupteten den alten Wortlaut und wurden rot.
- **Fix:** Beide Tests pruefen jetzt die tatsaechlich greifende Regel und tragen einen Kommentar, der sagt, welche es ist und warum die Route trotzdem nie gruen wird. Die Schutzwirkung ist unveraendert: je genau eine Meldung.
- **Files modified:** backend/tests/test_php_trust_boundary.py
- **Verification:** `pytest -q tests/test_php_trust_boundary.py` gruen, beide Faelle melden je genau einen Verstoss
- **Committed in:** `843dbe1`

**3. [Rule 2 - Missing Critical] Test fuer die Mischung der beiden alten Klassen**

- **Found during:** Task 1
- **Issue:** Nach der Umstellung koennen die Eintraege `NoAdminRequired` und `NoCSRFRequired` von `FORBIDDEN_ON_ADMIN_ROUTE` nur noch fuer eine Route feuern, die beide Routenattribute traegt. Ohne Test waere die Mischregel eine unbelegte Behauptung und die beiden Eintraege waeren praktisch tot.
- **Fix:** `test_a_route_that_mixes_the_two_old_classes_stays_admin` baut ein Muster mit `ApiRoute` und `FrontpageRoute` plus `NoAdminRequired` und prueft `kind == "admin"` sowie die Admin-Meldung.
- **Files modified:** backend/tests/test_php_trust_boundary.py
- **Verification:** Test gruen; die Admin-Verbotsliste ist damit weiterhin erreichbar und nicht nur deklariert
- **Committed in:** `843dbe1`

**4. [Rule 3 - Blocking] Die Mutationsprobe des Plans erzeugt einen Syntaxfehler statt eines roten Tests**

- **Found during:** Task 2
- **Issue:** Das im Plan genannte `sed -i 's/NoCSRFRequired", EXAPP_ATTRIBUTE)/EXAPP_ATTRIBUTE)/'` laesst das oeffnende Anfuehrungszeichen von `"NoCSRFRequired"` stehen. Die Datei ist danach nicht mehr parsbar, der Lauf bricht beim Einsammeln ab, und der Waechter wird nie ausgefuehrt.
- **Fix:** Die Probe wurde mit einer sauberen Mutation der ganzen Zeile gefahren (`FORBIDDEN_ON_ADMIN_ROUTE` auf drei Eintraege gekuerzt). Ergebnis: `1 failed, 20 passed`, und der einzige rote Test ist `test_the_admin_class_did_not_get_softer`. Danach wurde die Aenderung mit `git checkout --` auf die Datei verworfen, der Lauf steht wieder bei `21 passed`.
- **Files modified:** keine (Probe verworfen)
- **Verification:** `git status --short` leer nach der Probe, Testlauf wieder gruen
- **Committed in:** nicht committet, reine Verifikation

**5. [Rule 3 - Blocking] ruff ISC004 an der neuen Meldung**

- **Found during:** Task 3
- **Issue:** Die zweiteilige Meldung von `scan_app_php_sources` stand unverklammert in einer Listenliteral und wurde von `ruff check` als implizite Verkettung in einer Sammlung gemeldet.
- **Fix:** Klammern um die Verkettung.
- **Files modified:** backend/tests/test_admin_ui_contract.py
- **Verification:** `ruff check .` und `ruff format --check .` gruen
- **Committed in:** `974ff2b`

---

**Total deviations:** 5 auto-fixed (2 Bug/Missing-Critical, 3 Blocking)
**Impact on plan:** Kein Scope-Zuwachs. Die vier Admin-Verbote stehen woertlich unveraendert, alle Aenderungen bleiben in den zwei Dateien der `files_modified`. Die einzige inhaltliche Abweichung ist die selbst armierende Schranke, und sie ist die einzige Lesart, unter der die beiden Akzeptanzkriterien des Plans gleichzeitig erfuellbar sind.

## Issues Encountered

- Der Worktree hat keine eigene `.venv`. Alle Laeufe (`pytest`, `ruff`, `pyright`, `vulture`) liefen mit dem Interpreter aus `backend/.venv` des Hauptcheckouts, aber mit dem Arbeitsverzeichnis im Worktree, so dass `REPO_ROOT` und `CONTROLLER_ROOT` auf den Worktree-Baum zeigen. Fuer `pyright` war zusaetzlich `--pythonpath` noetig, sonst meldet es 185 nicht aufloesbare Importe, die reine Umgebungsartefakte sind.
- Beide Testdateien haben CRLF-Zeilenenden. Die Patches wurden ueber `Path.read_text`/`write_text` gefahren, was die Enden auf dieser Maschine erhaelt; `file` bestaetigt CRLF nach jedem Schritt.

## Verification

- `pytest -q tests/test_php_trust_boundary.py`: 21 passed (vorher 14)
- `pytest -q tests/test_admin_ui_contract.py`: 31 passed (vorher 26)
- `pytest -q tests/` (voller Backend-Lauf): 1761 passed, 15 skipped
- `ruff check .`, `ruff format --check .` (117 Dateien), `vulture src tests --min-confidence 80`: gruen
- `pyright --pythonpath <venv> tests/test_php_trust_boundary.py tests/test_admin_ui_contract.py`: 0 errors
- `grep -rn "IInAppSearch" php/ backend/src/`: kein Treffer
- Mutationsprobe: gekuerzte `FORBIDDEN_ON_ADMIN_ROUTE` macht genau `test_the_admin_class_did_not_get_softer` rot
- Keine PHP-Datei angefasst, `php -l` unberuehrt

## Threat Flags

Keine. Die Aenderungen liegen ausschliesslich in zwei Testdateien und erweitern die Pruefflaeche, statt eine zu schaffen. Der in diesem Plan bearbeitete Vertrag deckt T-09-04, T-09-14, T-09-06, T-09-15 und T-09-16 des Threat Models ab; der CSRF-Threat T-09-09 aus Plan 09-04 wird ueber das Pflichtattribut `NoCSRFRequired` der neuen Klasse erzwungen.

## Known Stubs

Keine.

## User Setup Required

None , no external service configuration required.

## Next Phase Readiness

- Plan 09-04 kann `php/lib/Controller/PageController.php` mit `FrontpageRoute`, `NoAdminRequired` und `NoCSRFRequired` anlegen, ohne Gate B zu brechen. Mit dem Anlegen der Datei armiert sich die Schranke automatisch auf 13; sollte Plan 09-04 den Controller anders benennen, muss `PAGE_CONTROLLER` in `test_php_trust_boundary.py` mitgezogen werden.
- Plan 09-06 erweitert `_sources()` von Gate C um `search.php`, `search.css` und `search.js`; der Kommentar an `_sources()` nennt die Bedingung und warnt vor dem Mitziehen der drei Admin-Sondertests.
- Die drei neuen Verbote sind ab sofort scharf: `search.js` darf weder `insertAdjacentHTML` noch `document.write` verwenden, sobald es in `_sources()` steht, und `IInAppSearch` ist bereits jetzt in jeder PHP-Datei der App verboten.

## Self-Check: PASSED

- `backend/tests/test_php_trust_boundary.py` vorhanden
- `backend/tests/test_admin_ui_contract.py` vorhanden
- `.planning/phases/09-eigene-ergebnisseite/09-02-SUMMARY.md` vorhanden
- Commits `843dbe1`, `afa995e`, `974ff2b` in `git log` vorhanden

---
*Phase: 09-eigene-ergebnisseite*
*Completed: 2026-09-09*
