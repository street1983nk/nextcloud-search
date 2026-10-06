---
phase: 26-n-ocr-slots-und-speicherw-chter
plan: 07
subsystem: worker/embedding
tags: [embedding, concurrency, profile, D-25-12, PAR-02]
requires: ["26-01", "26-02", "26-03", "26-05"]
provides:
  - "EmbedRunner._work mit asyncio.Semaphore(embed_slots): Leistung 2, Standard 1 Zeile gleichzeitig"
  - "EmbeddingTrack._chunk_lock (threading.Lock) um Chunker und Cutter-Bau"
  - "EmbeddingTrack._write_lock (asyncio.Lock) um replace_acl, replace_chunks und Präzisions-Startzustand"
affects: [26-06, 26-12]
tech-stack:
  added: []
  patterns: ["Semaphore je Runde innerhalb der Track-Sperre", "Barriere per asyncio.gather(return_exceptions=True) mit _abort-Semantik danach"]
key-files:
  created: []
  modified:
    - backend/src/findling/worker/embedding.py
    - backend/src/findling/config.py
    - backend/tests/test_embedding_track.py
    - backend/tests/test_embedding_runner.py
decisions:
  - "Cutter-Bau läuft ebenfalls unter _chunk_lock, damit zwei gleichzeitige Zeilen die 544,3 MB nicht doppelt laden"
  - "Präzisions-Startzustand (_prepare_the_precision) läuft unter _write_lock, weil er die state.db liest und die Engine tauschen kann"
  - "Nach dem ersten Fehler einer Zeile startet keine weitere Zeile der Runde; laufende enden, danach _abort oder Weiterwurf an run()"
  - "idle-Guard der Engine (_in_flight-Zähler) und _rows_in_work unverändert; Abdeckung per Test mit echtem EmbeddingModel-Wrapper belegt"
metrics:
  duration: "ca. 45 min"
  completed: 2026-09-28
  tasks: 2
  files: 4
---

# Phase 26 Plan 07: embed_slots im Einbettungs-Läufer wirksam Summary

Der EmbedRunner bettet im Profil Leistung bis zu zwei Zeilen einer Runde nebenläufig ein (Standard eine), abgesichert durch eine threading.Lock um Chunker und Cutter-Bau und eine asyncio.Lock um alle SQLite-Aufrufe der Spur; Sparsam bleibt inline und seriell (IDX-08).

## Tasks

| Task | Name | Commits |
|------|------|---------|
| 1 | Sperren um Chunker und Schreibaufrufe der Spur | 7c2ac617 (test), 866335ff (feat) |
| 2 | EmbedRunner bettet bis zu embed_slots Zeilen nebenläufig ein | 49288a83 (test), 7e6cbff7 (feat) |

## Was gebaut wurde

- `EmbeddingTrack.__init__`: `self._chunk_lock = threading.Lock()`, `self._write_lock = asyncio.Lock()` mit Begründung (tokenizers#1726, BEGIN IMMEDIATE je Verbindung, onnxruntime Run() aus mehreren Threads zugesagt).
- `_embed`: Chunker über `_cut_alone` (unter `_chunk_lock`) in `asyncio.to_thread`; `replace_acl` und `replace_chunks` je unter `async with self._write_lock`; Engine-Aufrufe ungesperrt.
- `EmbedRunner._work`: je embed-Zeile eine Task hinter `asyncio.Semaphore(max(1, profile.snapshot().resolution.values.embed_slots))`, alles innerhalb der Track-Sperre. Jede Task prüft nach Slot-Erhalt die Stufe (Sparsam: nicht starten) und ob eine frühere Zeile scheiterte. Barriere per `gather(return_exceptions=True)`; `sqlite3.Error`/`_DiskTight` führt zu unlock aller gehaltenen Zeilen, Backoff, kein Verdikt; andere Ausnahmen gehen an `run()`; CancelledError bricht alle Tasks ab und reist weiter.
- Klassendoc und `config.py`-Kommentar zu `PROFILE_*_EMBED_SLOTS` aktualisiert (Werte unverändert: 1 / 2).

## Tests

- Track (4 neu): zwei gleichzeitige Zeilen mit echter state.db und vectors.db (RED zeigte genau `sqlite3.OperationalError` bei BEGIN IMMEDIATE); Chunker-Peak 1; Schreib-Peak 1 über replace_acl und replace_chunks; idle-Guard von Cutter und echtem EmbeddingModel gibt erst nach beiden Zeilen frei.
- Runner (4 neu, 1 umgestellt): Leistung Peak 2 bei 6 Zeilen à 0,2 s, alle quittiert; Standard Peak 1; Sparsam mitten in der Leistungs-Runde startet keine neue Zeile, Rest per unlock; SQLite-Fehler in einer von zwei Zeilen gibt alle vier Zeilen zurück, Cooldown gesetzt. Sparsam-Parken ohne claim bleibt durch `test_economy_parks_without_a_claim` belegt.
- Hinweis TDD: Der idle-Guard-Test und der SQLite-Abbruchtest waren schon vor der Umsetzung grün; beides ist gewollt (Bestätigung unveränderter Semantik laut Plan).

## Verifikation

- `pytest` (mit --deselect des Python-Baumhash-Pins): 3792 passed, 18 skipped, 1 failed. Der eine Fehlschlag ist `test_the_recipe_reproduces_the_tree_hash_of_the_php_half`, ebenfalls ein Pin-Test; `php/` ist in diesem Plan unverändert (`git diff --stat` leer), Pin-Eigentümer der Welle ist 26-04, Neumessung in 26-06. Nicht angefasst.
- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture: grün.
- `git diff --stat -- backend/src/findling/worker/poller.py php`: leer.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Kritisch] Cutter-Bau unter der Chunker-Sperre**
- Found during: Task 1
- Issue: `_build_the_cutter` war nur "sequentiell durch Konstruktion"; zwei gleichzeitige erste Zeilen hätten Tokenizer und Splitter doppelt gebaut (2 x 544,3 MB auf der Zielbox).
- Fix: neue Hülle `_build_the_cutter_once` ruft den Bau unter `_chunk_lock`; der zweite Aufrufer findet beide Felder gesetzt. Docstring angepasst.
- Commit: 866335ff

**2. [Rule 2 - Kritisch] Präzisions-Startzustand unter der Schreibsperre**
- Found during: Task 1
- Issue: `_prepare_the_precision` liest die state.db und kann die Engine tauschen; zwei Zeilen hätten das gleichzeitig auf derselben Verbindung getan.
- Fix: Aufruf in `_embed` unter `async with self._write_lock` (daher 3 statt 2 Vorkommen im Grep).
- Commit: 866335ff

## Threat Flags

Keine neue Angriffsfläche; T-26-23/24/25 wie geplant mitigiert und per Test belegt.

## Self-Check: PASSED
