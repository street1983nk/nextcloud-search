---
phase: 29-h-rtung-und-store-einreichung-1-4-0
plan: 05
subsystem: worker/poller, nc/client
tags: [sidecar, system_file, short-read, D-29-02, D-29-04, D-29-05, "#18", "#22"]
requires: [29-01]
provides:
  - "_is_sidecar(name) als Modulfunktion in worker/poller.py (für 29-09 wiederverwendbar)"
  - "ShortRead in nc/client.py, expected-Parameter in fetch_file_stream/_stream_file"
affects: [29-09]
tech-stack:
  added: []
  patterns: ["Ausnahme je Datei nach dem Muster FileTooLargeError", "Zeile ohne Verdikt im Lease-Modell"]
key-files:
  created: []
  modified:
    - backend/src/findling/worker/poller.py
    - backend/src/findling/nc/client.py
    - backend/tests/test_poller.py
    - backend/tests/test_gateway_client.py
    - backend/tests/test_measurement_scripts.py
    - backend/tests/slots_kill_harness.py
    - backend/tests/test_embedding_runner.py
    - backend/tests/test_embedding_track.py
    - backend/tests/test_precision_wiring.py
decisions:
  - "Sidecar-Skip nimmt einen früher indexierten Eintrag aktiv aus Index, Vektoren und Präfilter (drop_document + forget_acl), weil ein skipped-Urteil allein nichts entfernt"
  - "Zweimal kurz: Zeile wird NICHT per unlock freigegeben (unlock erstattet die Lieferung, Endlosschleife T-29-15), sondern läuft in den Lock-Timeout; die nächste Ausgabe zählt, repeatedly_stuck bleibt erreichbar"
  - "Der sofortige zweite Download liegt in _fetch_file, damit Inhalts- und OCR-Zweig (seriell und mehrere Slots) dieselbe Regel haben"
metrics:
  duration: "ca. 45 min"
  completed: 2026-10-06
---

# Phase 29 Plan 05: Sidecar-Skip und Download-Größenprüfung Summary

._*- und ~$*-Dateien werden vor dem ersten Byte als skipped(system_file) verbucht und verlassen den Index; ein abgeschnittener Download (ShortRead) wird sofort einmal wiederholt und bleibt sonst ohne Verdikt, nie corrupt.

## Tasks

| Task | Name | Commits |
|------|------|---------|
| 1 | Sidecar-Skip vor judge | a22dbdd3 (RED), f511a4d8 (GREEN) |
| 2 | Download-Größenprüfung mit ShortRead, Pins | 9a485ac0 (RED), 3a3e9af5 (GREEN) |

## Was gebaut wurde

- `poller._is_sidecar(name)`: `name.startswith(("._", "~$"))` auf dem Basisnamen (`PurePosixPath(job.path).name`, Fallback `job.title`), kein SQL-LIKE (LIKE-Zahl in poller.py weiter 0).
- Skip in `_handle` nach den Kind-Zweigen (delete, acl, metadata, ocr, embed) und vor `judge`; neue Methode `_drop_a_sidecar` (drop_document + forget_acl, ohne Tombstone).
- `client.ShortRead`; `_stream_file(..., *, expected)` wirft bei `expected > 0 and written < expected` mit Meldung `file id N ended at W of E bytes`; `fetch_file_stream(..., expected=0)` reicht durch, der Poller übergibt `job.size`.
- `_fetch_file` = zwei Versuche über `_fetch_once`; `except ShortRead` vor `except Exception` (kein `_GatewayDown`, Pass läuft weiter).
- ShortRead-Zweige in `_handle`, `_read_the_scan` und `_scan_in_a_slot` (liefert None, wird hinter der Barriere übersprungen). Log nur „download of one file stayed short twice, handing the row back unjudged“ ohne Pfad, Name oder file id.
- Pin `PACKAGE_TREE_HASH_TODAY` = `0e149a74...16cc27` (eine Messung über 24784b59 plus beide Tasks), `PACKAGE_FILES_TODAY` bleibt 71.

## Tests

- Sidecar: ._, ~$, Fallback title, fünf Negativkontrollen (.hidden, a._b, x~$y, _x, Ordner ._Ordner), Übergang indexed zu skipped (Index leer, acl_rows 0), Delete-Job eines Sidecars bleibt Löschung, Unit-Test `_is_sidecar`.
- Client: kurz wirft ShortRead mit exakter Meldung; expected 0/-1 prüft nicht; länger als expected ist kein ShortRead.
- Poller: kurz dann voll wird indexiert und expected = job.size kommt an; zweimal kurz: kein Verdikt, kein unlock, keine skips, nächste Datei des Passes indexiert, Log ohne Pfad/Titel/ID; OCR seriell und unter zwei Slots ohne Verdikt.
- Volle Suite: 4490 passed, 25 skipped. ruff, ruff format, pyright (latest) 0 Fehler, vulture sauber.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Korrektheit] Sidecar verlässt den Index aktiv**
- **Found during:** Task 1 (Lesepflicht: skipped-Urteil entfernt nichts aus Tantivy, Vektoren oder ACL)
- **Fix:** `_drop_a_sidecar` mit dem bestehenden Löschpfad (`drop_document`, `forget_acl`), wie im Plan als Fallback vorgesehen
- **Commit:** f511a4d8

**2. [Rule 1 - Bug-Vermeidung] Kein unlock bei zweimal kurz**
- **Found during:** Task 2
- **Issue:** Das Muster „row handed back unjudged“ (`QueueMapper::unlock`) erstattet die Lieferung (`retries - 1`); eine immer abgeschnittene Datei käme so nie bei repeatedly_stuck an (T-29-15).
- **Fix:** Zeile weder in done noch failed und nicht entsperrt; sie läuft in den Lock-Timeout, die nächste Ausgabe zählt. Test sichert `queue.unlocked == []` zu.
- **Commit:** 3a3e9af5

**3. [Rule 3 - Blocker] Fetch-Doubles in vier weiteren Testdateien**
- **Issue:** Der Poller übergibt `expected=` an `self._fetch`; die Doubles in `slots_kill_harness.py`, `test_embedding_runner.py`, `test_embedding_track.py`, `test_precision_wiring.py` kannten das Keyword nicht.
- **Fix:** `expected: int = 0` ergänzt und verworfen, Verhalten unverändert.
- **Commit:** 3a3e9af5

**4. [Umfang] ShortRead auch im OCR-Zweig**
- `_scan` nutzt `_fetch_file` ebenfalls; ohne Zweig hätte ShortRead dort den Pass mit einer Ausnahme beendet. Gleiche Regel wie im Inhaltszweig, zwei Tests.

## Hinweise

- Task-1-Commit f511a4d8 enthält noch den alten Pin; der Baumhash wurde wie vorgegeben nur einmal am Ende gemessen (Commit 3a3e9af5). Zwischen den beiden Commits ist `test_the_recipe_reproduces_the_tree_hash_of_the_python_package` rot.
- Wartezeit nach zweimal kurz = Lock-Timeout der Queue; dafür bleibt die Aufgabegrenze intakt.
- Ein eigenes Verdikt `truncated` wurde nicht gebaut (deferred).

## Self-Check: PASSED

- FOUND: backend/src/findling/worker/poller.py (`def _is_sidecar`, `except ShortRead`)
- FOUND: backend/src/findling/nc/client.py (`class ShortRead`)
- FOUND: a22dbdd3, f511a4d8, 9a485ac0, 3a3e9af5
