# Phase 41: Deferred Items

## Aus 41-04 (Volltestsuite, erste Hälfte)

- **tests/test_extract_edge_paths.py::test_the_file_travel_path_writes_in_exactly_the_pinned_places rot seit 41-03.**
  `Poller.reopen_after_backup()` (Commit 6dbfac39) ruft `asyncio.to_thread(self._track.open, ...)`, das Gate zählt das als neuen Schreibort `worker/poller.py: open`. 41-04 hat poller.py nicht angefasst (`git diff c77337f2 -- backend/src/findling/worker/poller.py` leer), daher nicht in diesem Plan behoben.
  Vorschlag: `EXPECTED_TRAVEL_PATH_WRITES` um den Eintrag mit Begründung ergänzen (der Track öffnet nach einem Backup dieselbe vectors.db wieder, die `_open()` sonst öffnet; kein neuer Pfad aus einer Queue-Zeile), oder das Öffnen in eine Methode verlagern, die das Gate schon kennt. Spätestens vor 41-08 (CI-Beleg) erledigen.

  **ERLEDIGT nach 41-04:** Eintrag mit Begründung in `EXPECTED_TRAVEL_PATH_WRITES` ergänzt (Orchestrator-Fix, test_extract_edge_paths.py 21 passed).

## Aus 41-09 (Audit 1.6.2), für v1.7

Belege und Proben in 41-AUDIT.md und backend/tests/test_phase41_audit.py. Die
gepinnten Proben der LOW werden mit dem Fix rot und sind dann umzudrehen.

- **ERLEDIGT F-41A-01 (LOW):** `GuardWatch.note_shutdown_begins()` schreibt beim Stopp eines pausierten Containers zwei leere Meta-Zeilen in state.db, vorbei an `suspend_persist`. Fix: nicht schreiben, solange die Pause hält oder keine Marke gesetzt ist. Probe `test_p_f_41a_01_...`. Owner entscheidet in 41-10, ob schon 1.6.2.
- **ERLEDIGT F-41A-02 (LOW):** `Reconcile.run(once=True)` prüft den Hold vor `await self._catchup_mark()` und setzt `in_flight` erst danach; ein Pausen-Eintritt in dieser Lücke sagt "paused", danach schreibt `rewind_reconcile_walk`. Fix: `in_flight` vor dem Lesen setzen oder Hold danach erneut prüfen. Probe `test_p_f_41a_02_...`.
- **ERLEDIGT F-41A-03 (LOW, Owner-Punkt 41-10):** Ohne Companion bleibt der Container still auf "unknown", die D-17-Zeile kommt nie, der Koordinator liest 240 mal je Stunde ohne Rückzugsleiter. Vorschlag v1.7: einmalige WARNING-Zeile nach drei unlesbaren Lesungen in unknown, Leiter wie `RETREAT_MAX_SECONDS`.
- **ERLEDIGT F-41A-04 (LOW):** `ProbeRun.recover`/`_sweep` und `EmbeddingTrack._procure` fragen die Pause nicht; Sweep löscht fp32-Gewichte und schreibt eine Meta-Zeile, ein laufender Abruf schreibt `.part` in `models/`. Fix: Sweep wartet auf `not wants_pause()`, `_writers_rest` wartet auf einen laufenden Abruf. Probe `test_p_f_41a_04_...`.

  **ERLEDIGT 04.11.2026 (Owner-Entscheid: Fix vor 1.6.2):** F-41A-01 in b0c10754, F-41A-02 in c8fa6d98, F-41A-03 in 6b9d0995 (WARNING nach drei unlesbaren Lesungen, Leiter bis 300 s, INFO bei Rückkehr; Zustand unverändert nach D-41-19), F-41A-04 in efdca684. Proben umgedreht mit Positivkontrolle, Nachaudit in 41-AUDIT.md, neuer audited_head efdca6840ee89b3373d9706b0e3c94039c4ef8d4.

## Aus 41-10 (CI auf dem Tag-Kopf ba098b00), für v1.7

- **Flake im Harness "Store upgrade 2b", Schritt 5 (deploy-harp.yml):** HaRP deploy 41856594365, Versuch 1, nur das Bein stable34 auf ubuntu-24.04 rot mit "short=1 accepted=1 stayed-short-twice=0 and 1 queue row(s)". Die drei Logzeilen stimmen; die Schleife bricht ab, sobald state.db "indexed/" meldet, und zählt die Queue-Zeile im selben Augenblick, bevor das freigegebene Image v1.5.0 (UPGRADE_FROM_TAG) die Zeile nach dem Commit entfernt ("pass finished" erscheint 20 ms nach der Fehlerzeile). Kein Produktcode betroffen: Code-Diff 5dc1aa12..ba098b00 leer, dasselbe Bein war auf fea4c535 grün. Vorgehen 1.6.2: nur das rote Bein neu gestartet (`gh run rerun --failed`), kein Workflow-Patch vor dem Tag (er verschöbe den Tag-Kopf). Vorschlag v1.7: in Schritt 5 auf `left = 0` mit derselben Frist warten, statt einmal zu zählen.

## Aus der Verifikation 41, für v1.7

- Test, der nach Status paused einen festgeschriebenen Tantivy-Index nachweist (Verifikation 41, Punkt Zu prüfen)
