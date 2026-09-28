---
phase: 26-n-ocr-slots-und-speicherw-chter
plan: 09
subsystem: worker/poller
tags: [ocr-slots, guard, throttle, child-kill, solo-retry, unclean-end, PAR-02, PAR-03]
requires:
  - "26-01: ChildKilled(engine)"
  - "26-03: guard.throttled_slots, report_child_kill, note_slots, note_confirmation, META_MULTI_SLOT_PASS/CHOSEN"
  - "26-06: Staffel unter N Slots, _scan/_judge_scan, SlotGate/SlotPool"
provides:
  - "Poller(headroom=memory_guard.headroom_bytes): Drossel je Runde vor dem Zeilenbeschnitt"
  - "guard.note_confirmation nach jeder Profilabfrage (Rückweg D-26-04)"
  - "multi_slot_pass / multi_slot_chosen in state.db während jeder Mehr-Slot-Staffel, danach leer"
  - "Kill-Meldung an den Wächter plus Solo-Wiederholung hinter der Barriere; zweiter Tod allein = failed(out_of_memory)"
  - "Log-Zeile pass finished ... slots=%d throttled=%d"
affects: [26-10, 26-11, 26-12]
tech-stack:
  added: []
  patterns:
    - "Enum _OnKill (VERDICT/RAISE/OUT_OF_MEMORY) als Schalter durch _handle/_read_the_scan/_scan/_extract_on_the_pool"
    - "Sentinel _Killed(job) aus der OCR-Task statt Verdikt"
    - "Merker per write_meta auf der Autocommit-Verbindung, Löschen im finally mit geschluckter sqlite3.Error"
key-files:
  created: []
  modified:
    - backend/src/findling/worker/poller.py
    - backend/tests/test_poller.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Die Drossel liest headroom nur bei Ziel >= 2; Sparsam fragt nie (Zähler-Test)"
  - "throttled in der Log-Zeile kommt aus guard.snapshot() (slots_in_force < slots_target), nicht aus min(allowed, OCR-Zeilen)"
  - "Solo-Lauf geht für OCR- und content-Zeilen einheitlich über _handle(on_kill=OUT_OF_MEMORY); läuft vor den embed-Zeilen, damit OCR und Einbettung nie überlappen"
  - "Der Solo-Lauf meldet keinen Kill, die erste Meldung reicht (eine Meldung je Datei)"
  - "Scheitert das Löschen des Merkers, wird gewarnt und geschluckt: ein stehengebliebener Merker kostet beim nächsten Start eine Absenkung (sichere Richtung), eine Maskierung der eigentlichen Ausnahme wäre schlimmer"
  - "Schreiben des Merkers scheitert: sqlite3.Error läuft in den vorhandenen Store-Fehler-Pfad von run_once (Zeilen zurück, Pause), bevor irgendetwas extrahiert wurde"
  - "sandbox.py-Rennfenster NICHT gefixt, sandbox.py steht nicht in der Dateiliste (Merker übernommen, siehe Deferred)"
metrics:
  duration: "ca. 40 min"
  completed: 2026-09-29
  tasks: 2
  files: 3
---

# Phase 26 Plan 09: Drossel, Kill-Meldung und Solo-Wiederholung Summary

Der Poller schneidet die Slots jeder Staffel mit Ziel >= 2 auf den freien Speicher zu (235 MiB je weiterem Slot plus Reserve, unlesbar = ein Slot). Ein von außen gekilltes Kind kostet unter N Slots keine Datei mehr: Meldung an den Wächter, kein Verdikt, Solo-Lauf hinter der Barriere, erst ein zweiter Tod allein ergibt failed(out_of_memory). Während einer Mehr-Slot-Staffel steht `multi_slot_pass` dauerhaft in state.db. Nach jeder Profilabfrage läuft der Token-Abgleich des Rückwegs.

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Drossel je Runde, Token-Abgleich und Mehr-Slot-Merker | a73d3cd1 |
| 2 | Kill-Meldung und Solo-Wiederholung statt Dateiverlust, Pin neu gemessen | 45a66013 |

## Was gebaut wurde

- **Drossel (D-26-02):** `_keep_what_the_slots_finish` liest bei Ziel >= 2 `await asyncio.to_thread(self._headroom)`, rechnet `guard.throttled_slots(target, headroom)` und meldet `guard.note_slots(target, allowed)`. Zeilenbeschnitt und Slotzahl rechnen mit `allowed`. Kein Kind wird für die Drossel gekillt.
- **Rückweg (D-26-04):** `guard.note_confirmation(choice.confirmed, choice.profile)` direkt nach `note_chosen_precision`.
- **Merker (D-26-16, D-26-01):** `_mark_the_multi_slot_pass` schreibt die wirksame Stufe und das gewählte Profil ("" ohne Wahl) vor der ersten Task. Die Verbindung läuft in Autocommit, damit ist jeder Wert beim Rückkehren dauerhaft. `_clear_the_multi_slot_pass` leert den Merker im finally, also nach Barriere und Solo-Lauf und auch bei Abbruch, Gateway-/Plattenfehler und Cancel.
- **Kill-Politik:** `_OnKill.VERDICT` (serieller Pfad, altes Verdikt ohne Meldung), `RAISE` (Mehr-Slot-Pfad), `OUT_OF_MEMORY` (Solo). `_scan_in_a_slot` fängt ChildKilled, meldet und liefert `_Killed(job)`. Content-Zeilen im Mehr-Slot-Pfad ebenso. Hinter der Barriere: `set_limit(1)`, Solo-Lauf je gekilltem Job in Anspruchsreihenfolge, danach die embed-Zeilen. `_GatewayDown`/`_DiskTight` im Solo-Lauf führen wie überall zu `_abort`.
- **Moduldoc** Schritt 1 nennt Drossel, Solo-Wiederholung und Merker.
- **Pin:** `PACKAGE_TREE_HASH_TODAY` = 0bbc4cb3... über den eigenen Baum (66 Dateien, nur poller.py geändert), Ledger-Kommentar mit Hinweis auf die Nachmessung nach dem Merge von Welle 4.

## Tests

- Task 1: Drossel 4 -> 3 bei 3 x 235 MiB (6 Zeilen behalten, snapshot 4/3/throttled, Log `slots=3 throttled=1`), headroom None -> 1 Slot und 2 Zeilen, Sparsam fragt headroom nie (Zähler 0), Token passt -> Kappe weg, fremder Token -> Kappe bleibt, anderes Profil -> Kappe weg, Merker über zweite Verbindung während der Extraktion sichtbar und danach leer, Merker auch nach Gateway-Abbruch leer, serieller Pfad schreibt ihn nie.
- Task 2: gekillter Scan (engine False/True) läuft allein erneut und ist genau einmal indexiert, `take_child_kills() == 1`, keine failed-Einträge; zweiter Tod -> `out_of_memory` und genau eine Meldung, keine dritte Extraktion; gekillte content-Zeile ebenso; Solo-Lauf mit Gate-Limit 1, eine Extraktion zur Zeit, Anspruchsreihenfolge; Sparsam behält corrupt/ocr_failed ohne Meldung.
- Bestehender Log-Test prüft jetzt `slots=2 throttled=0`. `_slot_poller` bekommt standardmäßig reichlich headroom, damit die 26-06-Tests unverändert gelten.

## Verifikation

- Volle Suite (Windows): 3861 passed, 20 skipped, beide Pin-Tests grün.
- ruff check, ruff format --check, pyright latest (Windows und `--pythonplatform Linux`) mit 0 Fehlern, vulture sauber.
- Akzeptanz-Greps: `throttled_slots(` 1, `note_confirmation(` 1, `META_MULTI_SLOT_PASS` 2, `throttled=%d` 1, `report_child_kill()` 2, `Reason.OUT_OF_MEMORY` 1, `set_limit(1)` 1.
- `git diff --stat -- php backend/src/findling/main.py backend/src/findling/worker/watch.py` ist leer.

## Deviations from Plan

Keine inhaltlichen. Hinweis: Der alte Übergangstest `test_a_killed_child_keeps_its_verdict_of_before_phase_26_for_now` (slots 1 und 2) ist planmäßig ersetzt durch einen reinen Sparsam-Test plus die neuen Mehr-Slot-Tests.

### TDD-Hinweis

Beide Tasks sind `tdd="true"`. Tests und Implementierung sind je Task in einem gemeinsamen feat-Commit gelandet, nicht als getrennte RED/GREEN-Commits (wie in 26-06). Gegen den alten Stand wären sie rot: kein `headroom`-Parameter, kein Merker, ChildKilled unter N Slots ergab failed(corrupt/ocr_failed).

## Deferred Issues

- **Rennfenster in `sandbox.py` `_start_child` (Merker aus 26-04/26-06), weiterhin offen:** sandbox.py steht nicht in der Dateiliste dieses Plans. Korrekter Fix laut 26-06: `_halted` vor `process.start()` zurücksetzen, nach dem Zuweisen von `self._process` erneut prüfen und bei gesetztem Flag sofort `_kill_child_tree`. Übergabe an 26-11 oder den Code-Review. Relevanz steigt mit diesem Plan leicht: ein fälschlich stehengebliebenes Flag würde einen echten Kill als failed(corrupt) statt als ChildKilled lesen und damit die Solo-Wiederholung umgehen.
- **Abgebrochene Tasks lassen ihr Kind zu Ende laufen** (aus 26-06, unverändert): betrifft nur Shutdown/Abbruch.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche. T-26-29 (einmal Solo, zweiter Tod = out_of_memory, Test mit 5 geplanten Kills zeigt genau 2 Extraktionen), T-26-30 (kein Verdikt beim ersten Kill, Tests), T-26-31 (Drossel je Runde, unlesbar = ein Slot, Tests) und T-26-32 (Merker vor der ersten Task, zweite Verbindung im Test) sind umgesetzt.

## Self-Check: PASSED

- FOUND: backend/src/findling/worker/poller.py, backend/tests/test_poller.py, backend/tests/test_measurement_scripts.py
- FOUND: a73d3cd1, 45a66013
