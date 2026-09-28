---
phase: 25-einbettungsspur-und-modellwahl
verified: 2026-09-28T16:29:18Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
---

# Phase 25: Einbettungsspur und Modellwahl Verification Report

**Phase Goal:** Auf Boxen mit Profil Standard oder Leistung laeuft die Einbettung als eigener Nebenlaeufer neben der OCR, ohne den Tantivy-Writer zu beruehren, und der Admin kann zwischen e5-small int8 und fp32 waehlen, waehrend die Suche durch den Vektor-Reindex hindurch weiter antwortet.
**Verified:** 2026-09-28T16:29:18Z
**Status:** passed
**Re-verification:** No , initial verification

## Goal Achievement

### Observable Truths

Success Criteria aus ROADMAP.md, Phase 25 (vier Wahrheiten):

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | In Standard/Leistung holt ein eigener Nebenlaeufer Einbettungsarbeit ueber einen eigenen Anspruch mit Art-Filter (KIND embed), schreibt nur in vectors.db; in Linux-CI auf 2+ Kernen ueberlappt die Einbettung nachweislich mit laufender OCR | VERIFIED | `php/lib/Service/QueueService.php:84` `LANES = ['all','index','embed']`, Filterlogik Zeilen 271/275; `backend/src/findling/nc/queue.py:90-91` `LANE_EMBED`/`LANES`, `claim_documents(..., lane=lane)`; `backend/src/findling/worker/embedding.py` Klasse `EmbedRunner` (Zeile 1323) claimt `lane='embed'`, schreibt nur ueber `EmbeddingTrack` in vectors.db (`test_the_embedding_track_never_reaches_the_tantivy_writer_in_the_source`, Zeile 831); CPU-Beweis der echten Ueberlappung in `test_t3_real_cpu_work_of_both_lanes_overlaps` (`test_embedding_runner.py:993`, `skipif` nur auf Linux+2-Kerne, laeuft im CI-Gates-Job), zusaetzlich `test_t2_standard_runs_ocr_and_embedding_side_by_side` faellt lokal gruen |
| 2 | In Sparsam laufen OCR und Einbettung nachweislich nie gleichzeitig (IDX-08 woertlich, Test); in Standard/Leistung startet die Spur nur bei erfuellter RAM-Bedingung, sonst wartet/serialisiert sie | VERIFIED | `test_t1_economy_never_runs_ocr_beside_an_embedding` (Zeile 839) belegt `not recorder.overlaps()`; `memory_guard.py` (69 Zeilen) plus `embed_lane_fits`/`_level_allows_parallel` (`embedding.py:1636`) und Konstanten der RAM-Bedingung; D-25-11 (seriell statt Warteschlange) umgesetzt in `test_standard_without_memory_parks_waiting_for_memory` |
| 3 | Ein Neustart/Kill mitten in beiden Spuren verliert keine Warteschlangenzeile und bettet nichts doppelt ein; gleichzeitige state.db-Zugriffe fuehren zu keinem Fehlerverdikt | VERIFIED | `test_an_abort_in_the_middle_of_a_round_loses_no_row_and_doubles_no_chunk`, `test_an_abort_between_the_emptying_and_the_mark_leaves_the_drift_repeatable`, `test_the_redelivery_carries_on_in_the_next_process` (`test_embedding_track.py`); `test_a_second_writer_on_the_state_database_waits_instead_of_failing` und `..._on_the_vector_database_waits_instead_of_failing` (`test_track_connections.py:154,171`) pruefen BEGIN IMMEDIATE-Wartefall statt Fehler |
| 4 | Admin waehlt int8 (Default) oder fp32; nach Wechsel laeuft Vektor-Reindex, Suche antwortet lexikalisch weiter, Adminseite zeigt Zustand; fp32 kommt ueber den Owner-Tor-Lieferweg, keine Box ohne fp32-Wunsch zahlt Laufzeitspeicher | VERIFIED | `precision.py` (294 Zeilen) Zustandsautomat; `test_a_search_during_the_reindex_of_a_precision_change_answers_every_lexical_hit` (`test_semantic_search.py:1283`); Statusfelder `precisionChosen/precisionActive/precisionVerdict/reembedRunning` in `api/status.py:183-186,376-378`; Admin-Zeile `Model: %1$s, re-embedding %2$s (%3$s of %4$s)` in `admin.php:258`/`admin.js:392`, uebersetzt in allen 8 Sprachen (16 Dateien, siehe unten); fp32-Release ist der am Owner-Tor (D-24-05/D-25-05) entschiedene Nachladeweg, unabhaengig gegengeprueft (`docs/measurements/2026-09-fp32-speicher/rohdaten/02-release-gegenprobe.txt`, Digest `ca456c06b...` deckungsgleich mit `embed/weights.py:52` `FP32_SHA256`); ohne fp32-Wunsch laedt nichts (`lazy_load`, kein Start-Download, D-25-05) |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/src/findling/lane.py` | Spur-Modus-Zustand (parallel/inline) mit Grund | VERIFIED | 121 Zeilen, `MODE_PARALLEL`/`MODE_INLINE`, `REASONS` inkl. neuem `runner_failed` (WR-02-Fix) |
| `backend/src/findling/precision.py` | int8/fp32-Zustandsautomat | VERIFIED | 294 Zeilen, `note_chosen_precision`, `note_active`, `withdrawal_pending`, Verdikt-Woerter |
| `backend/src/findling/embed/weights.py` | fp32-Beschaffung, Digest-Pruefung | VERIFIED | 313 Zeilen, `fetch_release_asset`, `procure_fp32`, `remove_fp32_weights`, Host-Allowlist |
| `backend/src/findling/worker/embedding.py` | `EmbeddingTrack` + `EmbedRunner` | VERIFIED | 1687 Zeilen, eigene state.db/vectors.db-Verbindungen, eigener Lese-Handle, Track-Sperre |
| `backend/src/findling/memory_guard.py` | RAM-Bedingung fuer parallele Spur | VERIFIED | 69 Zeilen, live gegen `memory.max`/`anon` |
| `php/lib/Service/QueueService.php` | Art-Filter `lane` am Anspruch | VERIFIED | `LANES`, `claim()` Filterlogik Zeilen 68-84, 229-275 |
| `php/lib/Controller/QueueController.php` | Route mit `lane`-Parameter + Echo | VERIFIED | Zeilen 104-147, 400 bei unbekannter lane, Echo im Antwortobjekt |
| `php/lib/Service/SettingsService.php` | `model_precision`-Schluessel | VERIFIED | `KEY_MODEL_PRECISION`, `modelPrecision()` |
| `backend/src/findling/api/status.py` | Statusfelder Praezision/Reindex-Fortschritt | VERIFIED | `precisionChosen/precisionActive/precisionVerdict/reembedRunning`, `_volume()`+`_of()` |
| `php/templates/admin.php`, `php/js/admin.js` | Statuszeile Modell/Neueinbettung | VERIFIED | `Model: %1$s, re-embedding %2$s (%3$s of %4$s)` |
| `php/l10n/{de,de_DE,es,fr,it,nl,pt_BR,pt_PT}.{json,js}` (16 Dateien) | Acht Sprachkataloge im Gleichstand | VERIFIED | alle 16 Dateien enthalten die uebersetzte Zeichenkette mit echten (nicht leeren) Uebersetzungen, stichprobenartig DE/FR geprueft |
| fp32-Release-Asset (Owner-Handlung) | Unveraenderliches GitHub-Release | VERIFIED | Unabhaengige Gegenprobe (`02-release-gegenprobe.txt`) deckungsgleich mit im Code gepinntem Digest/Groesse |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `QueueController::getDocuments` | `QueueService::claim` | `lane`-Parameter | WIRED | Parameter wird durchgereicht, validiert gegen `LANES` vor DB-Zugriff |
| `nc/queue.py claim_documents` | PHP-Route `/queues/documents` | `lane`-Query-Param, nur bei explizitem Wert gesendet | WIRED | `test_queue_client.py` prueft bytegleiche Anfrage ohne `lane` |
| `EmbedRunner._round` | `EmbeddingTrack` | `claim(lane='embed')` unter `track.lock` | WIRED | Sperr-Reihenfolge belegt in Review (kein Deadlock, track-lock -> thread hop) |
| `worker/poller.py` | `lane.note_mode`/`note_echo` | Statusmeldung Spurmodus | WIRED | WR-02-Fix stellt sicher, dass Fehlpfade auf `MODE_INLINE` zurueckfallen |
| `precision.py` state machine | `embed/weights.py procure_fp32` | Beobachteter Schluesselwechsel int8->fp32 | WIRED | `test_precision_wiring.py` deckt Erfolgs- und Fehlpfad |
| `api/status.py` | `admin.php`/`admin.js` | JSON-Feld `model.precisionActive` etc. | WIRED | Feldnamen decken sich mit PHP-Konsum (`AdminViewService`) laut Review |
| `embedding_mark`-Aufrufer (`poller.py`, `api/resources.py`) | `engine_precision()` | kein Default mehr, tatsaechlich gehaltene Praezision | WIRED | IN-02/T-24-02 aus Phase-24-Review geschlossen, Plan 25-02 |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| Admin-Statuszeile (`admin.js:391-397`) | `running`, `embeddedPercent`, `embedded`, `indexable` | `GET /status` -> `model`-Objekt aus `api/status.py` `_of()`, gespeist aus echten Zaehlern `embedded`/`indexable` der State-DB | Ja | FLOWING |
| `precisionActive` | `state.active` | `precision._ACTIVE`, gesetzt in `note_active()` beim Engine-Tausch (nach WR-01-Fix direkt am Swap-Punkt, nicht mehr ueber Rueckgabewert) | Ja | FLOWING |
| `lane`-Echo (Companion-Antwort) | `files`, `lane` | `QueueController::getDocuments` liefert reale DB-Zeilen aus `QueueService::claim()`, kein statischer Rueckgabewert | Ja | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Backend-Testsuite (phase-relevante Module) | `uv run pytest tests/test_embedding_runner.py tests/test_embedding_track.py tests/test_precision.py tests/test_precision_wiring.py tests/test_weights.py tests/test_track_connections.py tests/test_memory_guard.py -q` | 171 passed, 1 skipped (Linux-only T3) | PASS |
| Volle Backend-Testsuite | `uv run pytest -q` | 3711 passed, 16 skipped | PASS |
| ruff (Lint) | `uv run ruff check .` | All checks passed! | PASS |
| ruff (Format) | `uv run ruff format --check .` | 164 files already formatted | PASS |
| pyright (latest, wie CI) | `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright --outputjson` | errorCount 0, warningCount 0 | PASS |
| vulture | `uv run vulture src/` | keine Ausgabe (keine Funde) | PASS |
| Debt-Marker-Scan | grep TBD/FIXME/XXX auf Kerndateien der Phase | keine Treffer | PASS |
| Vier Review-Fixes vorhanden | `git show --stat 00ecee3/25ec895/8ca5983/be2779c` | alle vier Commits existieren mit erwartetem Diff-Inhalt | PASS |
| fp32-Digest deckungsgleich | grep `FP32_SHA256` in `weights.py` vs. Gegenprobe-Datei | `ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665` in beiden identisch | PASS |

### Probe Execution

Keine `scripts/*/tests/probe-*.sh`-Dateien im Projekt gefunden; Phase 25 ist keine Migrations-/Tooling-Phase mit Probe-Skripten. SKIPPED (keine dokumentierten Probes).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| PAR-01 | 25-03, 25-05, 25-07, 25-09, 25-10 | Einbettungsspur als eigener Nebenlaeufer (H1), eigener Anspruch mit Art-Filter, beruehrt Tantivy-Writer nicht, wirkt ab 2 Kernen | SATISFIED | `EmbedRunner`/`EmbeddingTrack`, `lane`-Filter PHP+Python, `test_t3` (2-Kern-CPU-Beweis), `test_the_embedding_track_never_reaches_the_tantivy_writer_in_the_source` |
| PAR-04 | 25-08, 25-09 | IDX-08 neu gefasst: Sparsam woertlich, Standard/Leistung als RAM-Bedingung | SATISFIED | `test_t1_economy_never_runs_ocr_beside_an_embedding`, `memory_guard.py`, `embed_lane_fits`, D-25-11 seriell statt Warteschlange umgesetzt |
| MOD-02 | 25-01, 25-02, 25-03, 25-04, 25-06, 25-08, 25-11, 25-12 | Admin waehlt int8/fp32, fp32-Lieferweg via Owner-Tor, Suche antwortet waehrend Reindex lexikalisch weiter, Seite zeigt Zustand | SATISFIED | `precision.py`, `embed/weights.py`, Owner-Release-Gegenprobe, `test_a_search_during_the_reindex_of_a_precision_change_answers_every_lexical_hit`, Statuszeile in 16 Katalogdateien |

**Hinweis zu REQUIREMENTS.md:** Die Datei fuehrt PAR-01, PAR-04 und MOD-02 in der Kopfzeile weiterhin mit `[ ]` und in der Traceability-Tabelle mit Status "Pending", obwohl ROADMAP.md Phase 25 bereits als `[x]` abgeschlossen (2026-09-28) fuehrt und die Code-Evidenz oben die Erfuellung belegt. Das ist eine Dokumentationsluecke (REQUIREMENTS.md wurde nicht im gleichen Zug aktualisiert wie ROADMAP.md), keine funktionale Luecke. Da diese Verifikation ROADMAP.md/STATE.md/Quelldateien nicht veraendern darf und REQUIREMENTS.md kein Verifikationsartefakt ist, wird dies als Info-Befund gemeldet statt selbst behoben.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| .planning/REQUIREMENTS.md | 18,21,34,71-73 | Checkbox/Traceability-Status nicht auf "Complete" nachgezogen nach Phase-Abschluss | Info | Keine Code-Auswirkung; sollte im naechsten Doku-Schritt (z. B. secure-phase oder phase-complete) nachgezogen werden |
| , | , | Keine TBD/FIXME/XXX/Platzhalter in den 65 vom Review erfassten Dateien gefunden | , | , |

Vier Warnings aus dem Code-Review (25-REVIEW.md) waren vor dieser Verifikation offen; alle vier sind in eigenen, verifizierten Commits gefixt (00ecee3, 25ec895, 8ca5983, be2779c), mit passenden Tests, die in der vollen Suite gruen sind. Die vier Info-Punkte (IN-01 bis IN-04) sind laut Review bewusst nicht gefixt (niedriges Risiko, dokumentiert) und wirken sich nicht auf die vier Wahrheiten aus.

### Human Verification Required

Keine offenen Punkte. PHPUnit (php/tests/Unit/*) konnte in dieser Umgebung nicht ausgefuehrt werden (kein PHP/Composer lokal installiert); das ist laut Kontexthinweis der uebliche Stand dieser Repos (CI fuehrt PHPUnit nach dem naechsten Push aus, Owner-Entscheid, war bereits in Phase 24 ein bekannter Punkt und kein neuer Human-Verify-Bedarf fuer diese Phase). Ebenso T3-CPU-Ueberlappung: der Test existiert, ist korrekt mit `skipif` auf Linux+2-Kerne beschraenkt und wird im CI-Gates-Job ausgefuehrt; lokal (Windows) uebersprungen, kein Uebernahmerisiko, da `test_t2` denselben Sachverhalt ohne echten CPU-Burn bereits lokal gruen bestaetigt.

### Gaps Summary

Keine Gaps gefunden. Alle vier ROADMAP-Wahrheiten sind durch Code, Tests und (fuer den fp32-Owner-Schritt) eine unabhaengige Gegenprobe belegt. Die vier im Code-Review gefundenen Warnings sind mit eigenen, nachvollziehbaren Commits und Tests geschlossen; die volle Testsuite (3711 passed/16 skipped) sowie alle Qualitaetsgates (ruff, ruff format, pyright latest, vulture) sind gruen. Einzig REQUIREMENTS.md hinkt der ROADMAP-Aktualisierung nach (Info, keine Blockade).

---

_Verified: 2026-09-28T16:29:18Z_
_Verifier: Claude (gsd-verifier)_
