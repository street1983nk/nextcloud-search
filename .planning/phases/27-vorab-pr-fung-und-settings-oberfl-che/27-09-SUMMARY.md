---
phase: 27-vorab-pr-fung-und-settings-oberfl-che
plan: 09
subsystem: worker
tags: [probe, pruef-01, sc3, fp32, ocr, orchestrator]
requires:
  - phase: 27-02
    provides: probe.py (Codes, judge, judge_run, Tore, Snapshot, hold)
  - phase: 27-03
    provides: SlotPool.shed_idle
  - phase: 27-05
    provides: Poller/EmbedRunner hold_for_probe, release_probe_hold, pass_in_flight, parked
  - phase: 27-06
    provides: model_probe.measure
provides:
  - "worker/probe_run.ProbeRun: start, restore, recover, close, task"
  - "PollerLike, RunnerLike, PoolLike, ModelMeasureFn als Protokolle, START_STARTED, RECOVER_RETRY_SECONDS"
affects: [27-11]
tech-stack:
  added: []
  patterns: ["Kinder-Wartezeiten in eigenen Daemon-Threads über concurrent.futures.Future plus asyncio.wrap_future, nie im Default-Executor", "Kontrollfluss-Ausnahme _Ended trägt das Verdikt eines Schritts"]
key-files:
  created:
    - backend/src/findling/worker/probe_run.py
    - backend/tests/test_probe_run.py
  modified: []
key-decisions:
  - "embed_slots im Konstruktor ist ein Leser der laufenden Embed-Slots; pending zählt nur den Zuwachs Ziel minus laufend, wie beim Writer-Heap (die Aktivierungen der laufenden Lanes bleiben in der onnxruntime-Arena, auch geparkt)"
  - "fp32-Anteil nie doppelt: bei Wechsel auf fp32 steht er in model_extra (gemessen, mindestens FP32_EXTRA_BYTES), pending bekommt fp32=True nur, wenn fp32 schon wirkt und die Engine entladen ist"
  - "Abgelegte fp32-Datei mit falschem Digest ist nofit digest_mismatch und bleibt liegen, kein Download über die Datei des Admins"
  - "Bei fits bleibt die Marke probe_fp32_fetched = 1, damit recover nach einem Neustart eine nie aktivierte Datei wegräumt, wenn der Schlüssel dann int8 sagt"
  - "recover prüft vor jedem Schritt die Probe-Id in meta; eine spätere Probe besitzt die Marke dann und recover endet ohne Löschen"
  - "Zusätzliche Konstruktor-Parameter mit Default (scan, pause/download/measure/sample_seconds, min_free_bytes) für verkürzte Deckel in Tests; die Pflichtschnittstelle für 27-11 bleibt unverändert"
requirements-completed: [PRUEF-01]
metrics:
  duration: "ca. 70 min"
  completed: 2026-09-29
  tasks: 2
  files: 2
---

# Phase 27 Plan 09: Probe-Orchestrator Summary

`ProbeRun` fährt die Vorab-Prüfung als einzelnen Hintergrund-Task in der Schrittfolge pause, download/digest, model, ocr_one, calc, ocr_n, cleanup, mit drei Deckeln (Pause, Download, Messung), Vorab-Toren vor jedem Kind, Freigabe der Pause im finally und Neustart-Verhalten über state.db.

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Gerüst, Einzelflug, Pause, Download, Aufräumen, Persistenz, Neustart | 5205aa53 |
| 2 | Messteil: Modell-Kinder, OCR-Stichproben, Rechnung, N-Lauf unter einem Deckel (Tests) | 10cb8e08 |
| - | Freigabe direkt im finally, Moduldoc ohne Symbolnamen | 5eb68787 |

## Belege

- `release_probe_hold`: Zeilen 445 und 446 von probe_run.py, beide im `finally:` von `_run` (Zeile 443), dazu `probe.release()`.
- `begin_procurement|multi_slot_pass|.silence(|.arm(`: 0; `secrets.token_hex(8)`: 1; `run_in_executor(None`: 0; `first_slot_admitted|model_child_admitted`: 2; PROBE_MEASURE/DOWNLOAD/PAUSE_SECONDS je 3; `judge(` vorhanden.
- test_probe_run.py: 54 passed, 1 skipped (Windows); zusammen mit test_probe.py und test_sandbox.py 126 passed, 7 skipped; dreimal wiederholt stabil.
- Volle Suite: 4057 passed, 25 skipped, Baumhash-Pin bewusst abgewählt.
- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture sauber.

## Unter Windows geskippt, im Linux-Abbild nachgefahren

- `test_a_real_child_reads_the_scan_page` (Linux plus tesseract). Nachgefahren im Abbild `localhost:5055/findling_backend:latB` mit `--network none`, Worktree read-only gemountet, gleiches Skript wie der Test: echter `ExtractionWorker` auf der mitgelieferten Scanseite, Ziel economy/int8, Verdikt fits, Schritt cleanup, Ergebnis indexed mit 1593 Zeichen, erste Wörter "Gemeinde Musterhausen Vorlage für den Gemeinderat". Das Abbild hat kein pytest, daher Skript statt Testlauf; das Skript wurde danach gelöscht.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Korrektheit] fp32-Anteil nicht doppelt in pending und model_extra**
- **Found during:** Task 2
- **Issue:** Der Plantext setzt `fp32 = Ziel fp32 und nicht aktiv` in pending_load_bytes und zugleich model_extra in judge; bei entladener Engine zählte FP32_EXTRA_BYTES damit zweimal, was judge ausdrücklich verbietet.
- **Fix:** Beim Wechsel trägt nur model_extra den Mehrbedarf; pending bekommt fp32=True nur, wenn fp32 schon wirkt. judge_run bekommt pending plus model_extra.
- **Commit:** 5205aa53

**2. [Rule 2 - Korrektheit] Abgelegte Datei mit falschem Digest**
- **Found during:** Task 1
- **Issue:** Der Plan beschreibt nur die gültige abgelegte Datei; procure_fp32 würde eine ungültige per os.replace überschreiben, also eine Admin-Datei ersetzen.
- **Fix:** Liegt eine Datei, läuft nur der Schritt digest; ungültig ergibt nofit digest_mismatch, die Datei bleibt (D-27-17).
- **Commit:** 5205aa53

### Weitere Abweichungen

- TDD: Task 1 als ein Commit mit Tests und Umsetzung; der Messteil lag bereits im Modul des Task-1-Commits, Task 2 brachte die Tests des Messteils (RED-Gate für Task 2 nicht getrennt belegbar).
- Ein kleiner Nachcommit (5eb68787) zieht die beiden Freigaben direkt ins finally, damit das Akzeptanzkriterium wörtlich erfüllt ist.

## Hinweise für 27-11

- Pflichtparameter: poller, runner, pool, models_dir, fetch, rebuild_may_start, engine_loaded, cutter_built, embed_slots (je Callable außer den Objekten); state_path, persist, headroom, worker_factory, model_measure, hardware, clock, wall_clock haben Defaults.
- `start(profile, precision)` erwartet geprüfte Werte; fremde Werte wirft probe.begin als ValueError (der Router antwortet vorher 422).
- `recover(read_choice)` läuft als eigener Task; `close()` beendet ihn über das interne Closed-Event.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche über T-27-26 bis T-27-30 hinaus. Die Probe schreibt nur eigene meta-Schlüssel, lädt nur über procure_fp32 (feste URL, Digest, Länge) und loggt nur Codes und Typnamen.

## Offene Punkte für den Orchestrator

- `test_the_recipe_reproduces_the_tree_hash_of_the_python_package` wird rot sein, weil worker/probe_run.py eine neue Paketdatei ist. Pin laut Auftrag nicht angefasst.

## Self-Check: PASSED

- FOUND: backend/src/findling/worker/probe_run.py, backend/tests/test_probe_run.py
- FOUND: 5205aa53, 10cb8e08, 5eb68787
