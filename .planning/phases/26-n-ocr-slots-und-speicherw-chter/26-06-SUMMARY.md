---
phase: 26-n-ocr-slots-und-speicherw-chter
plan: 06
subsystem: worker/poller, nc/queue
tags: [ocr-slots, poller, barrier, unlock, parity, PAR-02, PAR-03]
requires:
  - "26-01: ChildKilled(engine)"
  - "26-02: KIND_BATCH_INDEX_LANE[ocr] = 32, 'confirmed' in der Profilantwort"
  - "26-03: ocr_rows_to_keep, OCR_ROWS_PER_SLOT, OCR_CLAIM_BATCH_INDEX_LANE"
  - "26-04: SlotPool, SlotGate, threadsicherer IndexBatchWriter"
provides:
  - "Poller(extract=None, pool=None, ocr_slots=None); eigener Pool wird in aclose() geschlossen"
  - "Poller._keep_what_the_slots_finish: Zeilenbeschnitt mit sofortigem unlock, Slots = min(Ziel, gelieferte OCR-Zeilen)"
  - "Poller._read_in_slots: OCR-Tasks, serielle Restzeilen, embed nach der Barriere"
  - "Poller._scan (ohne Store) / _judge_scan (Loop-Thread) / _extract_on_the_pool"
  - "CompanionChoice.confirmed (32 Hex oder None)"
  - "Paritätstests KIND_BATCH_INDEX_LANE und confirmed gegen PHP-Quelltext"
affects: [26-09, 26-10, 26-11, 26-12]
tech-stack:
  added: []
  patterns:
    - "asyncio.create_task je OCR-Zeile unter async with gate.slot(), Barriere per gather(return_exceptions=True)"
    - "Abbruch-Ausnahmen (_GatewayDown/_DiskTight) erst nach der Barriere, erste in Anspruchsreihenfolge"
    - "Text wird direkt nach writer.add verworfen, damit wartende Ergebnisse keinen Text halten (perf M2)"
key-files:
  created: []
  modified:
    - backend/src/findling/worker/poller.py
    - backend/src/findling/nc/queue.py
    - backend/src/findling/config.py
    - backend/tests/test_poller.py
    - backend/tests/test_queue_client.py
    - backend/tests/test_config.py
    - backend/tests/test_profile_wire.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Gate-Limit wird in jedem Durchlauf gesetzt (auch auf 1), nicht nur bei slots >= 2; die content-Extraktion läuft immer unter einem Gate-Slot"
  - "Bei einem Gateway-/Plattenfehler wird die Barriere abgewartet statt die Tasks abzubrechen, damit kein Kind dieses Durchlaufs noch arbeitet, wenn die Zeilen zurückgehen"
  - "Andere Task-Ausnahmen werden nach der Barriere geworfen (erste in Anspruchsreihenfolge), wie bisher im seriellen Pfad"
  - "Scheitert das unlock des Überschusses, bleiben die Zeilen im Durchlauf (heutiges Verhalten)"
  - "RoundResult.claimed und die Log-Zeile zählen die behaltenen Zeilen"
  - "Sandbox-Rennfenster aus 26-04 NICHT gefixt (sandbox.py nicht in der Dateiliste, einfacher Tausch wäre nicht korrekt), siehe Deferred"
metrics:
  duration: "ca. 55 min"
  completed: 2026-09-29
  tasks: 2
  files: 8
---

# Phase 26 Plan 06: Staffel unter N Slots Summary

Der Poller liest die OCR-Zeilen einer Staffel jetzt auf bis zu N Kindern des SlotPool gleichzeitig: 2 Zeilen je Slot behalten, Überschuss per unlock zurück, bevor ein Kind startet, Barriere vor dem einen Commit. Die Reihenfolge Commit, Verdikte, Übergabe, Quittung bleibt, Sparsam liest seriell wie bisher. Dazu kommt `CompanionChoice.confirmed`, und die Companion-Werte beider Lanes sind gegen den PHP-Quelltext gepinnt.

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | confirmed in CompanionChoice und Paritätstests | ac34b7fb |
| 2 | Staffel unter N Slots mit Zeilenbeschnitt, Tasks und Barriere, Pin neu gemessen | 673ccdb0 |

## Was gebaut wurde

- **nc/queue.py:** `CompanionChoice.confirmed: str | None` (Default None, damit 1.3-Fakes weiter passen). Geprüft wird mit `_TOKEN_PATTERN = re.compile(r"[0-9a-f]{32}")` per `fullmatch`. Der Fehlerpfad liefert alle drei Felder None.
- **worker/poller.py:**
  - Konstruktor: `extract=None`, `pool=None`, `ocr_slots=None`. Default ist `SlotPool(PROFILE_PERFORMANCE_OCR_SLOTS_MAX)` (faul, Sparsam startet ein Kind), `SlotGate(1)`. `aclose()` schließt nur einen selbst gebauten Pool.
  - `run_once`: `_keep_what_the_slots_finish` nimmt Ziel = `ocr_slots` oder `profile_snapshot().resolution.values.ocr_slots` und rechnet `ocr_rows_to_keep(n, Ziel, hard_deadline + 60)`. Der Überschuss geht per `unlock` zurück, verlässt bei ok `_held` und `jobs`. Slots = `max(1, min(Ziel, behaltene OCR-Zeilen))`.
  - `_work`: setzt das Gate-Limit. Bei slots >= 2 läuft `_read_in_slots`, sonst die unveränderte serielle Schleife. Die Schritte 2 bis 4 sind unverändert, die Log-Zeile hat zusätzlich `slots=%d`.
  - `_read_in_slots`: OCR-Zeilen laufen als Tasks (`_scan_in_a_slot`), content/acl/delete/metadata seriell in Anspruchsreihenfolge, embed-Zeilen erst nach der Barriere. Abbruch-Ausnahmen kommen nach der Barriere. CancelledError bricht alle Tasks ab und wird weitergereicht.
  - `_read_the_scan` ist aufgeteilt in `_scan` (fetch, Extraktion mit Route.OCR und langer Frist, `_discard`, `pool.call(writer.add, _record_of(...))`, ohne Store-Zugriff) und `_judge_scan` (embedding-Übergabe, `_collect(..., ocr_used=True)`).
  - `_extract_on_the_pool`: jede Extraktion (auch content) läuft über `self._pool.call`. ChildKilled wird übergangsweise abgebildet: engine True ergibt failed(ocr_failed), sonst failed(corrupt).
  - Moduldoc Schritt 1 und der Profil-Kommentar in run_once sind aktualisiert.
- **config.py:** Der veraltete Kommentar "parity test follows with plan 26-06" ist ersetzt.
- **Tests:**
  - test_queue_client: 11 neue Fälle (Token gültig, 8 kaputte Formen, Feld fehlt, 2 Fehlerpfade).
  - test_config: Parität `KIND_BATCH_INDEX_LANE[KIND_OCR] == 32` plus Rot-Probe.
  - test_profile_wire: Parität für Namen und Token-Form von confirmed.
  - test_poller: 14 neue Fälle für alle zehn Behavior-Punkte plus Pool-Schließen. Der Off-Loop-Test prüft jetzt `self._pool.call(self._extract` statt `to_thread`.
- **Pin:** `PACKAGE_TREE_HASH_TODAY` = fbd506eb... mit Ledger-Kommentar. `PACKAGE_FILES_TODAY` bleibt 66 (gemessen). Die PHP-Pins sind unverändert.

## Verifikation

- Volle Suite (Windows): 3849 passed, 20 skipped, beide Pin-Tests grün.
- ruff check, ruff format --check, pyright latest (Windows und `--pythonplatform Linux`) mit 0 Fehlern, vulture sauber.
- Die Slot-Tests liefen dreimal hintereinander grün.
- Akzeptanz-Greps: `ocr_rows_to_keep(` 1, `self._gate.slot()` 3, `asyncio.to_thread(self._extract` 0, "Nothing below reads the value yet" 0, `slots=%d` 1, `confirmed: str | None` 1, `KIND_BATCH_INDEX_LANE` in test_config >= 2.
- `git diff --stat -- php backend/src/findling/main.py backend/src/findling/worker/embedding.py` ist leer.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierend] Off-Loop-Grep-Test an die Pool-Ausführung angepasst**
- **Found during:** Task 2
- **Issue:** `test_the_blocking_work_runs_off_the_event_loop` verlangte `to_thread` in der Zeile mit `self._extract`. Das widerspricht der Planvorgabe (Pool-Executor, Pitfall 5).
- **Fix:** Der Test prüft jetzt `self._pool.call(self._extract` und `self._pool.call(self._writer_or_die().add`, außerdem, dass `to_thread(self._extract` fehlt. flush, add (seriell) und `_record_verdicts` bleiben auf `to_thread` gepinnt.
- **Commit:** 673ccdb0

**2. [Rule 2 - Performance] Text direkt nach writer.add verworfen**
- **Found during:** Task 2
- **Issue:** Bis zu 32 Scan-Ergebnisse warten an der Barriere. Mit Text im `_ScanResult` hielte das 32 Texte bis zum Urteil (perf audit M2).
- **Fix:** `_scan` gibt `replace(outcome, text="")` zurück. `text_chars` bleibt erhalten, darauf verlässt sich die Übergabe an die Einbettung.
- **Commit:** 673ccdb0

**3. [Rule 3 - Gate] ruff S105 auf die Test-Token-Konstante**
- Umbenannt in `_CONFIRMATION` mit Kommentar, statt ein noqa zu setzen.

### TDD-Hinweis

Beide Tasks sind `tdd="true"`. Die Tests entstanden in derselben Sitzung wie die Implementierung und sind je Task in einem gemeinsamen feat-Commit gelandet, nicht als getrennte RED/GREEN-Commits. Rot sind sie gegen den alten Stand trotzdem: kein unlock-Beschnitt, kein `ocr_slots`-Parameter, kein `confirmed`-Feld.

## Deferred Issues

- **Rennfenster in `sandbox.py` `_start_child` (Befund aus 26-04), bewusst nicht gefixt, Review-Merker für 26-09 oder den Code-Review:** Der vorgeschlagene reine Tausch (`_halted = False` vor `self._process = process`) reicht nicht. Ein `halt()` im Fenster fände dann `self._process` noch als None, würde nichts töten, und das Kind liefe trotz Pool-Schließen seinen Auftrag zu Ende. Außerdem bliebe das Flag stehen, sodass ein späterer echter OOM-Kill als failed(corrupt) statt als ChildKilled gelesen würde. Korrekt wäre: das Flag vor `process.start()` zurücksetzen und nach dem Zuweisen von `self._process` erneut prüfen, bei gesetztem Flag sofort `_kill_child_tree`. `sandbox.py` steht nicht in der Dateiliste dieses Plans, deshalb nur dokumentiert.
- **Abgebrochene Tasks lassen ihr Kind zu Ende laufen** (CancelledError-Pfad): Der Executor-Thread wartet weiter auf das Kind, das Gate ist schon frei. Das betrifft nur Shutdown und Abbruch, `SlotPool.close()` beendet die Kinder dort. Relevant für 26-09/26-11, falls ein Abbruch mitten im Betrieb möglich wird.

## Known Stubs

Keine. Der ChildKilled-Übergang (altes Verdikt statt Solo-Wiederholung) ist laut Objective beabsichtigt und wird von 26-09 ersetzt.

## Threat Flags

Keine neue Angriffsfläche. T-26-18 (Beschnitt plus Test "unlock vor der ersten Extraktion"), T-26-19 (Upsert unter Writer-Sperre, Test "alle 8 genau einmal", ein flush), T-26-20 (`_scan` ohne Store, `_judge_scan` und `_record_verdicts` im Loop-Thread nach der Barriere), T-26-21 (fullmatch 32 Kleinbuchstaben-Hex, 8 kaputte Formen getestet) und T-26-22 (nur `slots=%d`, Grep-Test grün, neuer Test ohne Titel und Pfad in den Zeilen) sind umgesetzt.

## Self-Check: PASSED

- FOUND: backend/src/findling/worker/poller.py, backend/src/findling/nc/queue.py
- FOUND: ac34b7fb, 673ccdb0
