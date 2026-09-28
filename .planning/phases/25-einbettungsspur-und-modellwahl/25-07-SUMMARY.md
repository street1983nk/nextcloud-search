---
phase: 25-einbettungsspur-und-modellwahl
plan: 07
subsystem: worker
tags: [embedding-track, refactor, sqlite, wal, tantivy, PAR-01]
requires: ["25-02", "25-05"]
provides:
  - "findling.worker.embedding.EmbeddingTrack: open(wire=)/close, busy, ready, lock, needs_vectors, embed_row, keep_the_vector_stock_in_step, release_cutter"
  - "findling.worker.embedding: EMBED_*, VECTOR_BACKLOG_BAND, BACKLOG_START, Chunker, PassageEmbedder, acl_users, hand_over"
  - "findling.index.writer: stored_body(index, schema, file_id), free_bytes(directory), disk_is_tight(directory, min_free_bytes)"
  - "IndexBatchWriter.index und IndexBatchWriter.directory (Properties)"
affects:
  - backend/src/findling/worker/poller.py (delegiert Zeile, Marke, Cutter an self._track)
  - backend/src/findling/tools/one_load.py (liest die Verdrahtung über poller._track)
tech-stack:
  added: []
  patterns:
    - "Spur-Eigentümer mit eigenen SQLite-Verbindungen und eigenem Index-Lese-Handle"
    - "Konstruktor ohne I/O, open() im Thread, injizierte Objekte werden nicht geschlossen"
key-files:
  created:
    - backend/src/findling/worker/embedding.py
    - backend/tests/test_track_connections.py
  modified:
    - backend/src/findling/worker/poller.py
    - backend/src/findling/index/writer.py
    - backend/src/findling/tools/one_load.py
    - backend/tests/test_index_writer.py
    - backend/tests/test_embedding_track.py
    - backend/tests/test_poller.py
    - backend/tests/test_embed_engine.py
    - backend/tests/test_one_load.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Poller.busy = gehaltene Zeilen ODER Zeile im Track; Poller.release_cutter prüft zuerst das eigene busy und delegiert dann"
  - "Der Poller behält eine eigene vectors.db-Verbindung für den Löschpfad (_open_the_delete_stock), der Track öffnet eine zweite für seine Schreibvorgänge"
  - "Injizierter Writer gibt seinen Index und sein Verzeichnis als Lese-Handle an den Track (Tests); in Produktion öffnet der Track den Index selbst, nur wenn das Verzeichnis existiert"
  - "stand_down schließt den Track (Index-Handle und eigene Verbindungen), _open öffnet ihn hinter dem frischen Writer neu"
  - "marks_stamped wird nicht an den Track gereicht: der Markenschritt ruft es heute nicht, ein ungenutzter Parameter wäre toter Code"
metrics:
  duration: "ca. 70 min"
  completed: 2026-09-28
  tasks: 3
  files: 11
requirements: [PAR-01]
---

# Phase 25 Plan 07: Einbettungsspur als eigener Eigentümer Summary

Verhaltensgleicher Refactor: `EmbeddingTrack` in `worker/embedding.py` besitzt Cutter, Einbettung einer Zeile, Vektor-Marke, Driftkette und Bänder, liest den Text über einen eigenen Index-Lese-Handle mit der freien Funktion `stored_body` und schreibt über eigene state.db- und vectors.db-Verbindungen; der Poller delegiert unter `async with self._track.lock`.

## Umsetzung je Task

**Task 1: freie Leser in index/writer.py**
- `stored_body(index, schema, file_id)`, `free_bytes(directory)`, `disk_is_tight(directory, min_free_bytes)` als Modulfunktionen, Docstrings (U64-Term, T-06-36) mitgezogen; die Methoden delegieren.
- Tests: Gleichheit Funktion/Methode, Lesen über einen nie beschriebenen Handle, Plattenboden gegen das übergebene Verzeichnis, Methode delegiert mit dem Index-Verzeichnis, AST-Prüfung "kein writer im Rumpf".

**Task 2: EmbeddingTrack**
- Umzug nach der Tabelle in 25-PATTERNS.md: `needs_vectors`, `embed_row` (Zählung der Zeilen in Arbeit, Rumpf `_embed`), `_wire_the_second_track` (Teil von `open`), `_build_the_cutter`, `release_cutter`, `_cutter_cooling_down`, `_embed_ready`, `keep_the_vector_stock_in_step` bis `_next_backlog_band`.
- Die drei Pflichtänderungen: Plattenboden über `disk_is_tight(index_dir, min_free_bytes)`, `replace_acl` über die Track-Verbindung, Text über `stored_body(index, index.schema, file_id)`.
- `open(wire=)`: state.db nur, wenn vorhanden (Muster `reconcile._open_state`), vectors.db über `open_vectors`, Index-Handle nur bei existierendem Verzeichnis. `close()` gibt nur eigene Verbindungen ab.
- Poller: `self._track`, Einbettung und Markenschritt unter `self._track.lock`, `busy`/`release_cutter` delegieren, `stand_down` und `aclose` schließen den Track, `_hand_over` und `_acl_users` als Modulfunktionen `hand_over`/`acl_users` in embedding.py.
- Neue Tests: Einbettung mit `_writer = None`, `busy` während einer Track-Zeile, Einbettung unter der Track-Sperre im Durchlauf, Delegation von `release_cutter`, Quelltextprüfung ohne Writer-Zugriff und ohne api-Import.

**Task 3: Verbindungen und Pins**
- `test_track_connections.py`: Identität der Verbindungen (state.db, vectors.db), zwei Schreiber auf state.db (200 ms BEGIN IMMEDIATE gegen `replace_acl`) und auf vectors.db (gegen `replace_chunks`) mit Barriere und 5-s-Deckel, keine Anlage einer fehlenden state.db.
- `PACKAGE_FILES_TODAY = 61`, `PACKAGE_TREE_HASH_TODAY = ce67c2d2...e39a01` über den Worktree-Baum gemessen. Der Orchestrator misst nach dem Merge der Welle 3 neu (25-06 fügt parallel zwei src-Dateien hinzu).

## Verifikation

- `uv run pytest -q`: 3552 passed, 15 skipped
- ruff check, ruff format --check, pyright (PYRIGHT_PYTHON_FORCE_VERSION=latest, 0 Fehler), vulture `src tests --min-confidence 80`: grün
- `git diff --stat -- php backend/src/findling/main.py`: leer
- Akzeptanz-Greps: `^def stored_body(` 1, `^def disk_is_tight(` 1, `class EmbeddingTrack` 1, alte Methoden im Poller 0, `_writer_or_die`/`.writer(` in embedding.py 0, `self._track.lock` im Poller 2, api-Import 0, `PACKAGE_FILES_TODAY = 61` 1

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Tests außerhalb der Dateiliste griffen auf verschobene Interna zu**
- **Gefunden in:** Task 2
- **Problem:** `test_embed_engine.py`, `test_one_load.py` und `src/findling/tools/one_load.py` riefen `Poller._wire_the_second_track`/`_build_the_cutter` bzw. patchten `poller_module.open_tokenizer` usw.
- **Fix:** Zugriffspfade auf `poller._track` und Monkeypatches auf `findling.worker.embedding` umgestellt; keine Aussage geändert.
- **Commit:** a6a5a21

**2. [Rule 3 - Blocking] Zugriffspfade in den bestehenden Tests**
- **Problem:** Die Tests lesen private Felder (`_chunker`, `_model`, `_cutter_absent`, `_embed_ready`, ...) am Poller; der Plan erlaubte nur Importpfade.
- **Fix:** Zugriff über `poller._track.<feld>` statt Proxy-Properties am Poller (die wären toter Code nur für Tests). Die Quelltext-Tests zu `release_cutter`, `_embed` und `open_tokenizer(` lesen jetzt `embedding.py`. Der Tight-Disk-Test patcht `embedding_module.disk_is_tight` statt `writer.disk_is_tight`, weil genau diese Stelle laut Plan umziehen musste. Die AST-Prüfung `test_stored_body_builds_its_term_through_the_schema` prüft die Modulfunktion (Term aus dem Parameter `schema`).
- **Commit:** ab51f8c, a6a5a21

**3. [Rule 2 - Missing] Lese-Handle für injizierte Writer**
- **Problem:** Tests injizieren einen Writer auf einem Verzeichnis außerhalb von `settings().index_dir`; ein Track mit eigenem Handle auf dem Settings-Verzeichnis läse dort nichts.
- **Fix:** `IndexBatchWriter.index` und `.directory` als Properties; der Poller gibt beide bei injiziertem Writer an den Track (Lese-Handle ohne zweiten Writer-Lock).
- **Commit:** a6a5a21

**4. Log-Zeile ohne das Wort "path"**
- Die neue debug-Zeile in `_open_the_delete_stock` hätte die Gate-Regel T-02-107 (`test_no_log_call_names_a_path...`) verletzt und wurde umformuliert.

### Nicht übernommen
- `marks_stamped` als Track-Parameter: der Markenschritt ruft den Callback heute nicht; ein ungenutzter Parameter würde vulture (100 %) auslösen und hätte kein Verhalten.

## TDD Gate Compliance

- Task 1: test ab51f8c -> feat 532a9ca
- Task 2: Refactor-Commit a6a5a21 (Typ `refactor`, bestehende Tests als Sicherheitsnetz, neue Verhaltenstests im selben Commit; kein separater RED-Commit, weil die Tests auf die neue Klasse zeigen und vorher nicht kompilierbar wären)
- Task 3: Tests d2aeae9 gegen die bereits umgesetzte Verdrahtung (Nachweis-Tests, kein neues Verhalten)

## Commits

| Task | Typ | Hash | Nachricht |
|------|-----|------|-----------|
| 1 | test | ab51f8c | add failing tests for stored_body and the disk floor as module functions |
| 1 | feat | 532a9ca | stored_body and the disk floor as module functions, methods delegate |
| 2 | refactor | a6a5a21 | the embedding track as its own owner with its own connections |
| 3 | test | d2aeae9 | own connections of the track and two writers under WAL; pins |

## Hinweise für Folgepläne

- Plan 25-09 kann `embed_row` und `keep_the_vector_stock_in_step` von einem zweiten Treiber aus unter `track.lock` rufen; `busy` zählt Zeilen unabhängig vom Treiber.
- Der Track öffnet seinen Index-Handle nur, wenn das Verzeichnis existiert; `embed_row` ohne Handle wirft `RuntimeError` (nur möglich, wenn `open` vor der Writer-Anlage liefe).
- Der Pin-Hash muss nach dem Merge von 25-06 (zwei neue src-Dateien) neu gemessen werden.

## Self-Check: PASSED

- FOUND: backend/src/findling/worker/embedding.py
- FOUND: backend/tests/test_track_connections.py
- FOUND: ab51f8c, 532a9ca, a6a5a21, d2aeae9
