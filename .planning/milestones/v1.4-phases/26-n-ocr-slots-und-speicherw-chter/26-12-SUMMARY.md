---
phase: 26-n-ocr-slots-und-speicherw-chter
plan: 12
subsystem: ops/measurement, ci, docs
tags: [slot-ladder, measure.yml, SC3, PAR-02, PAR-03, docs]
requires:
  - "26-09: Poller(..., ocr_slots, headroom, pool) und run_once mit Staffel"
  - "26-10: Wächter, Rückweg per Token, Statusblock guard"
provides:
  - "scripts/ops/slot_ladder.py: Messleiter über den echten Poller (--slots, --rounds, --scan-dir, --mode poller|embed)"
  - "measure.yml Job slots: A2 Leiter-Korpus, G Leiter 1/2/4, H Faktor gegen 1,05, I Einbettungs-Nebenzahl"
  - "docs/profiles.md Abschnitt Speicherwächter (Phase 26), docs/ocr.md Lease-Rechnung, docs/admin-page.md Wächterzeilen"
affects: [26-14, 28]
tech-stack:
  added: []
  patterns:
    - "Messwerkzeug im Stil von ocr_slot_probe.py: findling und pypdfium2 erst in Funktionen, Ausgabe nur Zahlen"
    - "Fake-Warteschlange mit Companion-Semantik (Limit, Byte-Budget, unlock an die Spitze)"
    - "Faktor-Schritt mit fester Schwelle und 'unbestimmt' plus exit 1, wie F4"
key-files:
  created:
    - scripts/ops/slot_ladder.py
    - backend/tests/test_slot_ladder.py
  modified:
    - .github/workflows/measure.yml
    - docs/profiles.md
    - docs/ocr.md
    - docs/admin-page.md
decisions:
  - "Eigenes Werkzeug slot_ladder.py statt Umbau von ocr_slot_probe.py, damit die W4-Rohkurve vergleichbar bleibt"
  - "Ein SlotPool je Stufe über alle Runden, Kinder vor Runde 1 mit je einer ungezeiteten Extraktion des kleinsten Scans angewärmt; state.db, Index und Poller je Runde frisch"
  - "Fake-Warteschlange beachtet Limit und Byte-Budget des Pollers und zählt gekappte Ansprüche als byte_capped_claims (Pitfall 11)"
  - "Job-Timeout des Jobs slots von 40 auf 75 Minuten angehoben, weil die Leiter rund 48 Seiten je Runde x 3 Runden x 3 Stufen dazulegt"
  - "--scan-dir ist laut Plan in beiden Modi Pflicht; der embed-Modus liest nichts daraus (in der Hilfe vermerkt)"
metrics:
  duration: "ca. 55 min"
  completed: 2026-09-29
  tasks: 2
  files: 6
---

# Phase 26 Plan 12: Messleiter und Doku der Phase Summary

Messleiter `slot_ladder.py` fährt den echten `Poller.run_once` mit 1, 2 oder 4 festgesetzten Slots über einen synthetischen Scan-Korpus, dazu Einbettungs-Nebenzahl embed_slots 1 gegen 2; in `measure.yml` steht der Job slots bereit (Korpus, Leiter auf cpuset 0 / 0,1 / 0-3, Faktor je Stufe gegen 1,05 mit "unbestimmt" und exit 1); Doku zu Wächter, Rückweg per occ, Lease-Rechnung über Zeilen je Slot und den Wächterzeilen der Adminseite.

## Tasks

| Task | Name | Commit | Dateien |
| ---- | ---- | ------ | ------- |
| 1 | slot_ladder.py mit Poller-Leiter und Einbettungs-Nebenzahl | 86c77c67 | scripts/ops/slot_ladder.py, backend/tests/test_slot_ladder.py |
| 2 | measure.yml-Schritte und Doku der Phase | f230c290 | .github/workflows/measure.yml, docs/profiles.md, docs/ocr.md, docs/admin-page.md |

## Was entstand

- **Werkzeug:** je Runde frische `state.db` und frischer Index, `Poller(..., ocr_slots=S, headroom=lambda: None if S == 1 else 64 GiB, pool=<geteilt>)`, `run_once` bis die Fake-Warteschlange leer ist. Gezählt werden Seiten der Scans, die `indexed` ohne Grund endeten (Seitenzahl per pypdfium2); jeder andere Scan zählt als `failed`, dann wird der Median "unbestimmt" und der Exit-Code 1. Ausgabe: `arch`, `cpus_visible`, `slots`, `scans`, eine `round ...`-Zeile je Runde, `byte_capped_claims`, `pages_per_second_median`.
- **Nebenzahl:** `--mode embed` lädt die int8-Engine des Abbilds (`shared_model()`) einmal, bettet 64 feste Passagen als 8 Zeilen zu 8 ein, seriell und mit 2 Threads, abwechselnd je Runde; Ausgabe `embed_slots <n> passages_per_second <X>`.
- **Tests (7):** Argumente (Pflicht, Grenzen 1..16, Modi), Rundenzeile, Median und "unbestimmt", embed-Ausgabe, keine Datei-/Verzeichnisnamen und kein Text in stdout/stderr (markantes tmp-Verzeichnis), Laden ohne findling-Import im frischen Interpreter plus AST-Prüfung, Fake-Warteschlange (Byte-Kappe, unlock an die Spitze, Quittung, requeue, pending).
- **measure.yml:** A2 baut 16 einseitige und 4 achtseitige Scans mit Seed `phase-26-ladder`, Größe und sha256 nach `ladder-corpus.txt`; G fährt die Leiter nach `ladder-slots-{1,2,4}.txt`; H schreibt `ladder-factor.txt` (Stufe 1->2 und 2->4, "Zugewinn" über 1,05, sonst "im Rauschen", Gesamtfaktor 1->4) oder "ladder unbestimmt" und exit 1; I schreibt `ladder-embed.txt` und scheitert nie. G, H, I laufen mit `if: !cancelled()`. Action-Pins und bestehende Schritte unverändert.
- **Doku:** Faktenlisten mit echten Umlauten, ohne Em- und En-Dashes; Verweis auf Phase 28 für die AWS-Matrix (D-26-10).

## Verifikation

- `tests/test_slot_ladder.py`: 7 passed; ruff check, ruff format --check, pyright (latest), vulture: grün
- `tests/test_workflow_pins.py tests/test_public_artifacts.py`: 69 passed
- Vollsuite `uv run pytest -q`: 3887 passed, 20 skipped (die Baumhash-Pins blieben grün, kein Deselect nötig)
- Akzeptanz-Greps: `slot_ladder.py --slots` in measure.yml 1, `1.05|1,05` 3, `profile_confirmed` in profiles.md 1, `OCR_ROWS_PER_SLOT|2 Zeilen je Slot` in ocr.md 2, `Phase 28` in profiles.md 1, `ocr_slots=` im Werkzeug 1, findling-Importe auf Modulebene 0; keine Dashes in den Doku-Dateien
- `git diff --stat 46572f4 HEAD -- backend/src php`: leer
- YAML geparst (Schrittliste geprüft), awk-Kerne des Faktor-Schritts mit gestellten Dateien geprüft (Zugewinn / im Rauschen / Fehlrunde / "unbestimmt" nicht numerisch)
- **Lokaler Rauchtest (x86, Docker, kein CI-Beleg):** altes Abbild `findling_backend:dev` mit dem aktuellen `backend/src` per PYTHONPATH darübergelegt, 4 Scans (5 Seiten): Slots 1 = 0,173 Seiten/s, Slots 2 = 0,340 Seiten/s, alle Scans indexiert, `failed 0`; embed 1 = 30,0, embed 2 = 54,7 Passagen/s. Belegt nur die Verdrahtung, keine Messzahl.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Job-Timeout des Jobs slots angehoben**
- **Found during:** Task 2
- **Issue:** Der Job hatte 40 Minuten für die W4-Schritte; die Leiter legt rund 48 Seiten x (3 Runden + Anwärmen) x 3 Stufen dazu und hätte den Deckel gerissen.
- **Fix:** `timeout-minutes: 75` mit Kommentar; die Regel "jeder Job hat timeout-minutes" bleibt erfüllt.
- **Files modified:** .github/workflows/measure.yml
- **Commit:** f230c290

Sonst wie geplant.

## Known Stubs

Keine.

## Threat Flags

Keine neuen Flächen über das Register hinaus: T-26-40 (keine Pin-Änderung, test_workflow_pins grün), T-26-41 (synthetische Scans, `--network none`, Ausgabe ohne Pfade und Texte, getestet), T-26-42 (feste Schwelle 1,05, "unbestimmt" plus exit 1, Rohdaten als Artefakt).

## Offen für 26-14

- Messlauf auf dem arm64-Runner erst nach Push und manuellem Start von `measure.yml` (Abbild `dev` muss den Phase-26-Poller tragen); Rohdaten nach `docs/measurements/2026-09-slot-leiter-ci/`, Nachtrag in `docs/performance.md`.

## Self-Check: PASSED

- FOUND: scripts/ops/slot_ladder.py, backend/tests/test_slot_ladder.py, .github/workflows/measure.yml, docs/profiles.md, docs/ocr.md, docs/admin-page.md
- FOUND: 86c77c67, f230c290
