---
phase: 03-aktualit-t-und-ocr
plan: 12
subsystem: worker
tags: [reconcile, etag, sqlite, asyncio, queue, python, idx-04, idx-05]

# Dependency graph
requires:
  - phase: 03-11
    provides: "FileList.mounts() und FileList.page(); final-Kennzeichen und SliceResult.complete als Vertrag"
  - phase: 03-07
    provides: "POST /queues/documents/requeue, der Schreibweg für beide Auftragsarten"
  - phase: 03-03
    provides: "kind=delete im Poller: drop_document, forget_acl, tombstone in einem Zweig"
  - phase: 02-indexkern-und-volltextsuche
    provides: "store/repo.py als einziges SQL-Modul, worker/poller.py als Strukturvorbild, ein Index-Schreiber je Prozess"
provides:
  - "backend/src/findling/worker/reconcile.py: Reconcile mit run_once() und run(stop_event), Ruhe-Gate, Takt, Mount-Walk"
  - "Store.gone_in_range: Löschbestimmung mit oberer Grenze, die nur ein final-Kennzeichen fallen lässt"
  - "Store.known_etags: bandweiser Versionsmarken-Abgleich, Grabsteine bleiben draußen"
  - "Store.reconcile_cursor, set_reconcile_cursor, reconcile_state: Lesezeichen je Mount und Zyklusstand"
  - "Tabelle reconcile in schema.sql, CREATE TABLE IF NOT EXISTS, ohne SCHEMA_VERSION-Anhebung"
  - "Fünf FINDLING_RECONCILE_*-Variablen in config.py und backend/appinfo/info.xml"
  - "docs/reconcile.md: Existenzgrund, Cursor-Ausnahme, Takt, Wartungsfenster-Falle, Abnahmetest"
affects: [03-13, 03-14, 04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reparaturtask neben dem Poller: eigene Task, eigenes Stop-Ereignis, gefangene Ausnahmen, nur Typname im Log"
    - "Zwei Gates vor jeder Arbeit: Ruhe-Gate gegen die Queue, Takt gegen die eigene Uhr und die Zeitstempel"
    - "Aus einer Abwesenheit folgt nur etwas innerhalb bestätigter Grenzen: obere Grenze, complete, Transportfehler"
    - "Findungen wandern vor dem Lesezeichen; ein Abbruch dazwischen kostet eine Scheibe"

key-files:
  created:
    - backend/src/findling/worker/reconcile.py
    - backend/tests/test_reconcile.py
    - docs/reconcile.md
  modified:
    - backend/src/findling/store/schema.sql
    - backend/src/findling/store/repo.py
    - backend/src/findling/config.py
    - backend/src/findling/main.py
    - backend/appinfo/info.xml
    - backend/tests/test_store_repo.py
    - backend/tests/test_lifecycle.py

key-decisions:
  - "Der Abgleich schreibt nie in den Index: er erzeugt content- und delete-Aufträge, die Zweige des Pollers erledigen sie. Damit existiert der Löschweg genau einmal und es gibt keinen zweiten Tantivy-Schreiber"
  - "Das Ruhe-Gate wird vor jeder einzelnen Scheibe erneut geprüft, nicht nur einmal je Runde: eine Runde, die auf einer ruhigen Instanz startet und in den Arbeitstag läuft, muss aufhören können"
  - "Ein unlesbarer Queue-Zähler ist keine ruhige Queue, sondern ein Abbruch der Runde"
  - "Ein gescheiterter Requeue bewegt das Lesezeichen nicht: sonst fielen die Findungen dieser Scheibe bis zum nächsten Zyklus unter den Tisch, auf der Vorgabe-Kadenz also einen Tag lang"
  - "Der Takt hat zwei Sonderfälle: eine abgebrochene Runde ist sofort fällig, und nach der doppelten Mindestpause läuft der Zyklus unabhängig von der Stunde, damit eine nur tagsüber laufende Box die Garantie nicht verliert"
  - "Der Abgleich legt die Zustandsdatenbank nie an. Nur der Poller sät die Versionsmarken; fehlt die Datei, meldet die Runde no_state und tut nichts"
  - "present wird in Python verglichen statt bandweise in SQL (siehe Abweichung 1); die Bandtechnik sitzt stattdessen in known_etags, wo sie gebraucht wird"
  - "FINDLING_RECONCILE_HOUR bekommt einen eigenen Leser, weil der vorhandene Zahlenleser die Null ablehnt und Mitternacht die erste Stunde ist, die ein Admin einträgt"

patterns-established:
  - "Zweite Schreibverbindung auf state.db: erlaubt unter WAL, in open_store benannt und begrenzt, niemals eine geteilte Verbindung zwischen zwei Tasks"
  - "Guard-Schicht um eine Nebentask im lifespan: die Task darf enden, der Prozess und die Haupttask nicht"

requirements-completed: [IDX-04, IDX-05]

# Metrics
duration: 55min
completed: 2026-09-01
---

# Phase 3 Plan 12: Der ETag-Abgleich Summary

**Der Abgleich als Container-Pull: eine zweite asyncio-Task, die die Dateiliste seitenweise liest, gegen die eigene files-Tabelle vergleicht und Abweichungen als content- und delete-Aufträge in die Warteschlange gibt, mit Ruhe-Gate vor jeder Scheibe, Tageskadenz gegen die eigene Uhr und einem Lesezeichen, dessen Verlust eine Wiederholung kostet und nie Arbeit.**

## Performance

- **Duration:** 55 min
- **Started:** 2026-09-01T13:05:00Z
- **Completed:** 2026-09-01T14:00:00Z
- **Tasks:** 3, jeder als TDD-Zyklus in zwei Commits
- **Files modified:** 10 (3 neu, 7 geändert)

## Accomplishments

- Nach einem einzigen Abgleichzyklus ist der Index korrekt, auch wenn kein einziges Ereignis angekommen ist (D-02). Der Zyklus findet unbekannte Dateien, abweichende ETags und Dateien, die es nicht mehr gibt, und reicht alle drei über denselben Requeue-Weg weiter.
- Eine Datei, die in Nextcloud nicht mehr existiert, verschwindet aus Index und Vorfilter, ohne dass irgendjemand ein Ereignis geliefert hat (IDX-05). Sie geht dabei durch den Löschzweig aus Plan 03-03, nicht an ihm vorbei.
- Der Abgleich setzt aus, solange die Queue nicht ruhig ist (D-03), und zwar vor jeder einzelnen Scheibe. Eine Runde, die mittags in einen OCR-Rückstau läuft, hört dort auf, wo sie gerade steht.
- Ein Abbruch mitten im Abgleich kostet eine Wiederholung und nie Arbeit: der Transportfehler, der gescheiterte Requeue und das gefallene Ruhe-Gate lassen das Lesezeichen alle dort stehen, wo die letzte abgeschlossene Scheibe es hingesetzt hat. Der Wiederaufnahmetest fährt genau diesen Fall.
- Der Suchpfad merkt nichts davon. Die Reparatur ist eine eigene Task mit eigenem Stop-Ereignis, ihre Ausnahmen werden zweifach gefangen (in der Runde und über der Schleife), und ein Test stellt eine Suche gegen einen laufenden Abgleich.
- Es gibt weiterhin genau einen Index-Schreiber im Prozess. Ein Grep-Gate im Test belegt, dass in `reconcile.py` weder `open_index` noch ein Writer-Typ vorkommt.

## Task Commits

1. **Task 1: Löschbestimmung und Abgleich-Cursor im Store** - `2ed789b` (test, RED) und `4978d54` (feat, GREEN)
2. **Task 2: Der Abgleichlauf** - `c3f12d2` (test, RED) und `41ccbc7` (feat, GREEN)
3. **Task 3: Der Abgleich im Lebenszyklus des Containers** - `fca67bf` (test, RED) und `2b801f3` (feat, GREEN)

Ein REFACTOR-Schritt war in keinem der drei Zyklen nötig: die GREEN-Fassung ist jeweils die, die auch nach Ruff, Ruff-Format, Pyright und Vulture unverändert bleibt.

## Files Created/Modified

- `backend/src/findling/worker/reconcile.py` (neu, 23 kB) - `Reconcile` mit `run_once()` und `run(stop_event)`, lazy geöffneten Ressourcen, `RoundResult`, sechs Rundenzuständen und Backoff-Verdopplung. Der Modul-Docstring trägt die drei Aussagen, die später niemand rekonstruieren kann: warum es den Abgleich gibt, warum sein Cursor hier liegt, warum er nichts in den Index schreibt.
- `backend/src/findling/store/schema.sql` - Tabelle `reconcile(storage_id, after_file_id, started_at, finished_at)` mit `CREATE TABLE IF NOT EXISTS`. Der Kommentar darüber erklärt, warum das kein Widerspruch zum Kopfkommentar ist: hier steht ein Lesezeichen, kein Arbeitsvorrat.
- `backend/src/findling/store/repo.py` - `gone_in_range`, `known_etags`, `reconcile_cursor`, `set_reconcile_cursor`, `reconcile_state`, dazu `ReconcileCursor` und `ReconcileState`. Der Docstring von `open_store` benennt jetzt die zweite Schreibverbindung und ihre Grenzen.
- `backend/src/findling/config.py` - fünf `FINDLING_RECONCILE_*`-Variablen, dazu `_hour_from_environment` für die Stunde, weil der vorhandene Leser die Null ablehnt.
- `backend/appinfo/info.xml` - dieselben fünf Variablen als Admin-Einstellungen, mit deutschsprachig gedachten, englisch geschriebenen Beschreibungen im Muster des OCR-Blocks.
- `backend/src/findling/main.py` - zweite Task im `lifespan`, `active_reconcile()`, `_guarded_reconcile()`, gemeinsame Armierung über den `enabled_handler`, geordnetes Ende nach dem yield.
- `backend/tests/test_reconcile.py` (neu) - 16 Tests gegen eine echte Zustandsdatenbank und Attrappen für Nextcloud.
- `backend/tests/test_store_repo.py` - 16 Tests für die neuen Abfragen, darunter der final-Fall, der Grabstein-Fall und die Bandaufteilung über die Trace-Rückrufe.
- `backend/tests/test_lifecycle.py` - 6 Tests für die zweite Task, darunter Abschaltfall, Unabhängigkeit vom Poller und eine Suche gegen einen laufenden Abgleich.
- `docs/reconcile.md` (neu, 173 Zeilen) - deutsche Prosa mit echten Umlauten und ohne Em-Dashes.

## Decisions Made

- **Reihenfolge der beiden Gates: Ruhe zuerst, Takt danach.** Der Plan verlangt "Ruhe-Gate zuerst und nicht zuletzt". Das kostet je Tick einen `stats`-Aufruf, auch wenn der Takt gar nicht fällig ist. Bei einem Tick von 300 Sekunden ist das vernachlässigbar, und die Alternative hätte den Abnahmetest für das Ruhe-Gate von der Tageszeit abhängig gemacht.
- **Der Takt hat eine Ausweichregel.** Bevorzugte Stunde allein hätte bedeutet, dass eine Box, die nur tagsüber läuft, den Abgleich nie ausführt. Nach der doppelten Mindestpause läuft er deshalb unabhängig von der Stunde. Das steht als Absatz in `docs/reconcile.md` und als Kommentar an `_is_due`.
- **`_local_hour` und `clock` sind injizierbar.** Sonst hinge jeder Kadenztest an der Zeitzone der Maschine, auf der er läuft.
- **`set_reconcile_cursor` nimmt einen Zeitstempel entgegen.** Der Lauf reicht seine eigene Uhr durch, sonst mischten sich Testuhr und `time.time()` und der Kadenztest wäre nicht deterministisch.
- **Eine leere Seite ohne final-Kennzeichen beendet den Mount.** Der Cursor bewegt sich dabei nicht, und ohne diesen Zweig liefe die Scheifenschleife endlos. Es kostet eine Wiederholung im nächsten Zyklus.
- **`ROUND_NO_STATE` statt eines Fehlers.** Ohne Zustandsdatenbank kennt der Container keine Datei; es gibt nichts zu vergleichen und vor allem nichts, was in einer Seite fehlen könnte.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `present` wird in Python verglichen, die Bandtechnik sitzt in `known_etags`**

- **Found during:** Task 1
- **Issue:** Der Plan verlangt, die `present`-Menge bandweise in SQL zu vergleichen. Das ist mit `NOT IN` nicht korrekt komponierbar: eine Datei fehlt nur dann, wenn sie in *allen* Bändern fehlt, und eine bandweise `NOT IN`-Abfrage liefert die Vereinigung statt des Durchschnitts. Umgesetzt wie beschrieben wäre jede Datei, die nicht im ersten Band steht, als gelöscht gemeldet worden.
- **Fix:** `gone_in_range` folgt Beispiel 3 der Recherche und filtert die Bereichsabfrage gegen ein Python-Set. Die Bereichsabfrage liefert ohnehin genau die fraglichen Zeilen, und die Menge erreicht die Datenbank nie, es gibt also gar keine Platzhaltergrenze zu beachten. Die vom Plan verlangte Bandtechnik mit interpolierter Platzhalterzahl und `noqa`-Kommentar sitzt stattdessen in `known_etags`, wo eine Seite von bis zu 2000 Datei-Ids tatsächlich in die Abfrage geht. Der Grund steht als Absatz im Docstring von `gone_in_range`.
- **Files modified:** backend/src/findling/store/repo.py
- **Verification:** `test_gone_in_range_*` (sechs Fälle) und `test_known_etags_splits_a_long_list_into_bands` über die Trace-Rückrufe; das Abnahmekriterium "keine Wertinterpolation in SQL" ist erfüllt, beide f-String-Abfragen der Datei interpolieren nur Platzhalterzahlen.
- **Committed in:** `4978d54`

**2. [Rule 2 - Missing Critical] Ein eigener Leser für die Stunde**

- **Found during:** Task 2
- **Issue:** `_int_from_environment` lehnt jeden Wert unter 1 ab. `FINDLING_RECONCILE_HOUR=0` wäre also mit einer Warnung auf die Vorgabe 2 zurückgefallen, und Mitternacht ist die erste Stunde, die ein Admin für ein Wartungsfenster einträgt. Ein stillschweigend ignorierter Wert in einem Admin-Formular ist genau die Klasse, die `config.py` an anderer Stelle ausdrücklich vermeidet.
- **Fix:** `_hour_from_environment` mit `RECONCILE_HOUR_RANGE = (0, 23)`, im Muster der übrigen Leser: unbrauchbare Eingabe warnt mit dem Namen der Variablen und degradiert auf die Vorgabe. Der bestehende Leser bleibt unverändert, weil seine Ablehnung der Null dort richtig ist.
- **Files modified:** backend/src/findling/config.py
- **Verification:** `uv run python -m pytest tests/test_config.py -q` grün, keine Änderung an bestehendem Verhalten.
- **Committed in:** `41ccbc7`

**3. [Rule 2 - Missing Critical] Der Docstring von `open_store` benennt die zweite Schreibverbindung**

- **Found during:** Task 2
- **Issue:** Der Docstring behauptete "There is exactly one of these connections in a running container, held by the poller". Mit dem Abgleich stimmt das nicht mehr, und ein falscher Docstring an dieser Stelle ist gefährlicher als gar keiner: der nächste Leser hätte entweder die zweite Verbindung für einen Fehler gehalten oder, schlimmer, die Verbindung des Pollers geteilt. `BEGIN IMMEDIATE` ist verbindungsgebunden, zwei Transaktionen darauf wären ein echtes Problem.
- **Fix:** Der Absatz nennt jetzt beide Verbindungen, warum zwei unter WAL sicher sind, warum eine geteilte es nicht wäre, und dass der zweite Aufrufer die Datenbank niemals anlegen darf, weil sonst die Versionsmarken als unbekannt festgeschrieben würden (Bug-Audit H1).
- **Files modified:** backend/src/findling/store/repo.py
- **Verification:** `_open_state()` in `reconcile.py` legt die Datei nicht an und meldet `None`, wenn sie fehlt; `run_once` antwortet dann mit `ROUND_NO_STATE`.
- **Committed in:** `41ccbc7`

**4. [Rule 2 - Missing Critical] `test_an_incomplete_page_never_produces_a_deletion`**

- **Found during:** Task 2
- **Issue:** Die acht Behauptungen des Plans decken den Vertragspunkt aus Plan 03-11 nicht ab, obwohl er in dieser Phase die teuerste Fehlerklasse ist: eine Seite mit verworfener Zeile sieht an genau der Stelle wie eine Löschung aus, an der der Abgleich löscht.
- **Fix:** Ein neunter Test plus der Zweig `if not page.complete: return []` in `_missing_of`, mit dem Grund als Docstring.
- **Files modified:** backend/src/findling/worker/reconcile.py, backend/tests/test_reconcile.py
- **Verification:** `test_an_incomplete_page_never_produces_a_deletion`
- **Committed in:** `c3f12d2` (Test) und `41ccbc7` (Zweig)

---

**Total deviations:** 4 auto-fixed (1 Bug, 3 fehlende kritische Funktionalität)
**Impact on plan:** Keine Umfangsänderung. Abweichung 1 ist eine Korrektur an einer Anweisung, die so umgesetzt Dokumente gelöscht hätte; die übrigen drei sind Härtung und Dokumentationswahrheit an derselben Stelle.

## Issues Encountered

- Der Grep für das Log-Verbot (`LOGGER\.[a-z]+\(.*(path|name|title)`) trifft auch `type(error).__name__` in derselben Zeile, wie es im Poller steht. In `reconcile.py` und in `main.py` steht der Typname deshalb auf einer eigenen Zeile in einer lokalen Variablen. Das ist kein Kosmetikzwang, sondern hält das Gate scharf, statt es aufzuweichen.
- Der Abnahmebefehl des Plans lautet `uv run pytest`. Ausgeführt wurde nach der Projektregel aus `CLAUDE.md` durchgehend `uv run python -m pytest`.

## Verification

- `uv run python -m pytest -q`: **640 passed, 6 skipped** (vorher 634 passed, 6 skipped)
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright` (0 errors), `uv run vulture src tests --min-confidence 80`: alle Exit 0
- Abnahme-Greps Task 1: `CREATE TABLE IF NOT EXISTS reconcile` 1, `def gone_in_range` 1, `test_gone_in_range_respects_the_page_end` 1, `test_gone_in_range_ignores_already_deleted_files` 1; die beiden f-String-Abfragen in `repo.py` interpolieren ausschließlich Platzhalterzahlen und tragen den `noqa: S608`-Kommentar
- Abnahme-Greps Task 2: `def run_once` 1, `open_index|IndexBatchWriter|IndexWriter` 0, `cursor` 4, `idempotent` 1, `test_reconcile_resumes_at_the_cursor` 1, `test_reconcile_does_nothing_while_the_queue_is_busy` 1, Log-mit-Pfad 0 Treffer; das Ruhe-Gate steht in Zeile 259 und 309, der erste Seitenabruf in Zeile 316
- Abnahme-Greps Task 3: `reconcile` in `main.py` 14, `test_reconcile_task_is_not_started_when_disabled` 1, `test_failing_reconcile_does_not_stop_the_poller` 1
- `docs/reconcile.md`: 173 Zeilen, `maintenance_window_start` 2 Treffer, Em-Dashes 0, En-Dashes 0, Umlaut-Zeilen 66, ASCII-Ersatzschreibungen 0
- Ein Lauf gegen eine Attrappe mit drei Abweichungen erzeugt genau drei Aufträge in den richtigen Arten: abgedeckt durch `test_reconcile_hands_an_unknown_file_to_the_content_track`, `test_reconcile_hands_a_file_with_a_moved_etag_to_the_content_track` und `test_reconcile_hands_a_file_that_is_gone_to_the_delete_track`
- Kein Commit dieses Plans löscht eine verfolgte Datei (geprüft mit `git diff --diff-filter=D` über alle sechs Commits)

## Known Stubs

Keine. Jede in diesem Plan gebaute Funktion ist verdrahtet und wird von einem Test gefahren.

## Threat Flags

Keine über den `<threat_model>` des Plans hinausgehende Angriffsfläche. Neue Netzwerkflächen entstehen nicht: der Abgleich benutzt ausschließlich die beiden Leserouten aus 03-11 und den Requeue-Schreibweg aus 03-07, und die Schreib-Allowlist bleibt bei drei Einträgen. T-03-1201 bis T-03-1206 sind wie geplant umgesetzt:

| Threat | Umsetzung |
|---|---|
| T-03-1201 | Obere Grenze aus dem final-Kennzeichen, `complete`-Veto, Transportfehler ohne Cursorsprung |
| T-03-1202 | Ruhe-Gate vor jeder Scheibe, Mindestpause zwischen Zyklen, Seitengröße und Pause dazwischen |
| T-03-1203 | Grep-Gate belegt: kein Index-Schreiber in `reconcile.py`; Löschungen laufen als Aufträge |
| T-03-1204 | Unverändert Sache des Paritäts-Gates aus Plan 03-10 |
| T-03-1205 | Log ausschließlich mit Zählern, Grep-Gate im Test |
| T-03-1206 | Eigene Task, gefangene Ausnahmen in der Runde und über der Schleife, zwei Tests |

## User Setup Required

None. Alle fünf neuen Variablen haben Vorgaben, die ohne Zutun richtig sind. Ein Admin, der `maintenance_window_start` gesetzt hat, sollte `FINDLING_RECONCILE_HOUR` darauf abstimmen; das steht in `docs/reconcile.md` und ist ein Hinweis, keine Pflicht.

## Next Phase Readiness

- Der Integrationsschritt für den Abnahmetest IDX-04 (Ereignisse blockiert, ein Zyklus, Index korrekt) ist beschrieben, aber nicht gebaut. Er gehört nach `.github/workflows/integration.yml` neben den bestehenden Ende-zu-Ende-Job; `docs/reconcile.md` führt die drei Schritte wörtlich auf.
- Phase 4 kann `RoundResult` unverändert auf die Statusseite legen: Zustand, Mounts, Scheiben, gesehene, veraltete und fehlende Dateien, alles Zähler ohne Pfad.
- Die Tabelle `reconcile` ist per `CREATE TABLE IF NOT EXISTS` gekommen, ohne `SCHEMA_VERSION`-Anhebung. Eine bestehende Installation braucht keinen Reindex.

## Self-Check: PASSED

Alle drei neuen Dateien liegen auf der Platte (`backend/src/findling/worker/reconcile.py`, `backend/tests/test_reconcile.py`, `docs/reconcile.md`), alle sechs Commits stehen auf `worktree-agent-03-12`, und kein Commit dieses Plans löscht eine verfolgte Datei.

---
*Phase: 03-aktualit-t-und-ocr*
*Completed: 2026-09-01*
