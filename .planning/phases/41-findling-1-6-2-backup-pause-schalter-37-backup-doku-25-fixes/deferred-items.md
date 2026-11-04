# Phase 41: Deferred Items

## Aus 41-04 (Volltestsuite, erste Hälfte)

- **tests/test_extract_edge_paths.py::test_the_file_travel_path_writes_in_exactly_the_pinned_places rot seit 41-03.**
  `Poller.reopen_after_backup()` (Commit 6dbfac39) ruft `asyncio.to_thread(self._track.open, ...)`, das Gate zählt das als neuen Schreibort `worker/poller.py: open`. 41-04 hat poller.py nicht angefasst (`git diff c77337f2 -- backend/src/findling/worker/poller.py` leer), daher nicht in diesem Plan behoben.
  Vorschlag: `EXPECTED_TRAVEL_PATH_WRITES` um den Eintrag mit Begründung ergänzen (der Track öffnet nach einem Backup dieselbe vectors.db wieder, die `_open()` sonst öffnet; kein neuer Pfad aus einer Queue-Zeile), oder das Öffnen in eine Methode verlagern, die das Gate schon kennt. Spätestens vor 41-08 (CI-Beleg) erledigen.

  **ERLEDIGT nach 41-04:** Eintrag mit Begründung in `EXPECTED_TRAVEL_PATH_WRITES` ergänzt (Orchestrator-Fix, test_extract_edge_paths.py 21 passed).

## Aus 41-09 (Audit 1.6.2), für v1.7

Belege und Proben in 41-AUDIT.md und backend/tests/test_phase41_audit.py. Die
gepinnten Proben der LOW werden mit dem Fix rot und sind dann umzudrehen.

- **F-41A-01 (LOW):** `GuardWatch.note_shutdown_begins()` schreibt beim Stopp eines pausierten Containers zwei leere Meta-Zeilen in state.db, vorbei an `suspend_persist`. Fix: nicht schreiben, solange die Pause hält oder keine Marke gesetzt ist. Probe `test_p_f_41a_01_...`. Owner entscheidet in 41-10, ob schon 1.6.2.
- **F-41A-02 (LOW):** `Reconcile.run(once=True)` prüft den Hold vor `await self._catchup_mark()` und setzt `in_flight` erst danach; ein Pausen-Eintritt in dieser Lücke sagt "paused", danach schreibt `rewind_reconcile_walk`. Fix: `in_flight` vor dem Lesen setzen oder Hold danach erneut prüfen. Probe `test_p_f_41a_02_...`.
- **F-41A-03 (LOW, Owner-Punkt 41-10):** Ohne Companion bleibt der Container still auf "unknown", die D-17-Zeile kommt nie, der Koordinator liest 240 mal je Stunde ohne Rückzugsleiter. Vorschlag v1.7: einmalige WARNING-Zeile nach drei unlesbaren Lesungen in unknown, Leiter wie `RETREAT_MAX_SECONDS`.
- **F-41A-04 (LOW):** `ProbeRun.recover`/`_sweep` und `EmbeddingTrack._procure` fragen die Pause nicht; Sweep löscht fp32-Gewichte und schreibt eine Meta-Zeile, ein laufender Abruf schreibt `.part` in `models/`. Fix: Sweep wartet auf `not wants_pause()`, `_writers_rest` wartet auf einen laufenden Abruf. Probe `test_p_f_41a_04_...`.
