# Phase 41: Deferred Items

## Aus 41-04 (Volltestsuite, erste Hälfte)

- **tests/test_extract_edge_paths.py::test_the_file_travel_path_writes_in_exactly_the_pinned_places rot seit 41-03.**
  `Poller.reopen_after_backup()` (Commit 6dbfac39) ruft `asyncio.to_thread(self._track.open, ...)`, das Gate zählt das als neuen Schreibort `worker/poller.py: open`. 41-04 hat poller.py nicht angefasst (`git diff c77337f2 -- backend/src/findling/worker/poller.py` leer), daher nicht in diesem Plan behoben.
  Vorschlag: `EXPECTED_TRAVEL_PATH_WRITES` um den Eintrag mit Begründung ergänzen (der Track öffnet nach einem Backup dieselbe vectors.db wieder, die `_open()` sonst öffnet; kein neuer Pfad aus einer Queue-Zeile), oder das Öffnen in eine Methode verlagern, die das Gate schon kennt. Spätestens vor 41-08 (CI-Beleg) erledigen.
