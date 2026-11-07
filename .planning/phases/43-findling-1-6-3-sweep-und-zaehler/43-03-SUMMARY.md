---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 03
subsystem: backend/store
tags: [coverage, issue-25, d-43-07, d-43-09, d-43-11, d-43-14, doc-key]
requires:
  - 43-16 (files.doc_key, Sentinel '', Index files_storage_doc_key)
provides:
  - "repo.coverage_counts(state_db, vectors_db, mounted, groups) -> CoverageCounts"
  - "CoverageCounts(documents, embedded_documents, judged_documents, documents_by_group, judged_by_group, documents_by_storage, judged_by_storage, doc_keys_missing)"
  - "Store.counts() ohne Tombstones"
  - "backend/tests/fixtures/coverage_topology.json mit expected und expected.php (für 43-04 und 43-05)"
affects:
  - 43-04 (Route /coverage)
  - 43-05 (PHP-Nenner pro Gruppe, Paritätstest)
tech-stack:
  added: []
  patterns:
    - "eine read-only Abfrage, alle drei Zahlen und alle Teile in einem Durchlauf (MAX je Schlüssel, GROUP BY grp bzw. storage_id)"
    - "Listen nur über json_each(?1)/json_each(?2), Ausdrücke als Modulkonstanten, Schablone per format nur mit Konstanten"
key-files:
  created:
    - backend/tests/fixtures/coverage_topology.json
    - backend/tests/test_coverage_counts.py
  modified:
    - backend/src/findling/store/repo.py
    - backend/tests/test_store_repo.py
    - backend/tests/test_measurement_scripts.py
    - backend/tests/test_embedding_track.py
    - backend/tests/test_phase40_audit.py
decisions:
  - "Ein Durchlauf statt drei Abfragen je Zahl: drei Statements brauchten 2,3 bis 2,5 s auf 188.600 Zeilen, einer 1,1 s (Ziel unter 1,5 s)"
  - "doc_keys_missing zählt nur lebende Zeilen eingebundener Gruppenmitglieder mit doc_key NULL; Zeilen eines Einzelspeichers ohne Schlüssel zählen als Dokument und halten nichts auf"
  - "Ein Speicher in zwei Gruppen (direkter Aufruf ohne Route) gehört zur ersten Gruppe (MIN(grp)); die Route lehnt das ohnehin mit 422 ab (43-04)"
  - "Fehlt vectors.db, wird nichts angehängt, embedded = 0, Warnzeile ohne Pfad"
  - "by_storage enthält nur Werte > 0, by_group immer eine Zahl je angefragter Gruppe"
metrics:
  duration: "ca. 85 min (davon ca. 19 min Volltestsuite)"
  completed: 2026-11-07
  tasks: 2
  files: 7
---

# Phase 43 Plan 03: Zählung pro Dokument in der Store-Schicht Summary

`coverage_counts` zählt jedes Dokument eingebundener Speicher genau einmal: in einer Freigabegruppe über (Gruppe, doc_key), sonst je Zeile; dazu `embedded` und `judged` und die Teile pro Gruppe und pro Einzelspeicher, in einer read-only Abfrage. `Store.counts()` zählt keine Tombstones mehr.

## Umsetzung

- `_COVERAGE_SQL`: CTEs `listed` (Mountliste ohne IDs < 1), `member` (eingebundene Gruppenmitglieder mit Gruppenindex), `single` (übrige eingebundene Speicher), alle `MATERIALIZED`, Join `CROSS JOIN files f INDEXED BY files_storage`, `deleted_at IS NULL`. Gruppen: innere Gruppierung je (grp, Schlüssel) mit `MAX(<Ausdruck>)`, Schlüssel = doc_key, Sentinel '' als `'#' || file_id`, NULL sammelt sich unter dem Schlüssel NULL und zählt nur als `doc_keys_missing`. Einzelspeicher: `SUM(<Ausdruck>)` je Zeile.
- Ausdrücke als Modulkonstanten: documents `state='indexed'`; embedded zusätzlich `EXISTS vec.chunks` (ohne vectors.db die Konstante `0`); judged `NOT (skipped AND reason IN (mime_not_allowed, excluded, gone))`, too_large bleibt drin.
- Parameter nur gebunden: `json.dumps` der sortierten Listen in ?1 (Gruppen) und ?2 (Mountliste). Verbindung `mode=ro`, `query_only`, Vektor-DB `mode=ro` angehängt und im finally wieder gelöst. Rückgabe nur ganze Zahlen und Speicher-IDs.
- Docstring nennt D-43-14 (doc_key statt files.path, Fall A1) und warum documents <= judged je Gruppe die Quote mit der PHP-Klammer max(PHP_g, judged_g + phpOnly_g) unter 100 % hält.
- `Store.counts()`: `_COUNTS_SQL` mit `WHERE deleted_at IS NULL`.

### Aufrufer von counts() (Prüfung vor der Änderung)

- `api/status.py:733` (`_of`, Feld `indexed`/`skipped`/`failed` von /status): soll Tombstones nicht zählen, genau der Fehler aus 43-RESEARCH Befund 3 (auch eine Companion 1.6.2 sieht die Zahl nach einem Löschen sofort sinken).
- `tools/index_status.py:155` (Diagnosewerkzeug): zeigt Zustände lebender Dateien; Tombstones sind dort kein Zustand.
- `worker/poller.py:545` (leerer Index, aber indexierte Urteile -> Generation hoch): ein Index, der nur noch gelöschte Dateien hielt, braucht keinen Neuaufbau. Kein Aufrufer braucht Tombstones.

## Fixture

`backend/tests/fixtures/coverage_topology.json` (ASCII, englische Schlüssel): Gruppe 0 "Daten" (11, 12, 13, verschiedene Sicht), Gruppe 1 "Archiv" (21, 22), Einzelspeicher 31, 32, 33 (leer), 41 nicht eingebunden, eine Zeile mit storage_id 0. Fälle: A1 (Weiterteilung an einen alphabetisch früheren Leser, `Shared/...` statt `Daten/...`, gleicher doc_key), zwei Einhängepunkte, Dokument nur im kleinsten Mitglied, gleiche Datei auf zwei Freigaben (zählt je Gruppe), Tombstones, Sentinel '', NULL-Schlüssel auf einem Einzelspeicher, alle Urteilsarten, B1 (abgelehnter Typ auf 41), Variante `backfill_open` (zwei Mitgliederzeilen ohne Schlüssel). `expected` und `expected.php` von Hand gezählt, jede Zahl mit `derivation`; `expected.php` enthält scanStats je Speicher, refusedPerStorage, PHP-only-Zeilen (u1 für alle Mitglieder unlesbar, st1 stuck, g1 gone mit, g2/g3 gone ohne filecache-Zeile, N1, 41 nicht eingebunden), phpOnly je Gruppe/Einzelspeicher, groupParts, Nenner je Teil (Gruppe 0 gewinnt die Container-Seite 11 > 9, Gruppe 1 die PHP-Seite 9 > 5; globales max gäbe 27 statt 30), Nenner 30, Zähler 13, notReadable 5, Quote 43, Vektorquote 16.

## TDD

- RED 59be0046: ImportError für `coverage_counts`, `test_counts_leave_a_tombstone_out` rot.
- GREEN a7a5d163: tests/test_coverage_counts.py 20 passed (Fixture gegen Hand-Wahrheit, Summen = Teile, documents <= judged je Teil, A1 einmal, zwei Einhängepunkte einmal, Positivkontrolle "gleicher Leserpfad, zwei interne Pfade = zwei Dokumente", NULL-Variante, Sentinel als eigenes Dokument, leere Mountliste, nicht eingebundenes Mitglied, IDs 0/-1, nicht eingebundener Speicher mit Positivkontrolle, fehlende vectors.db, keine Schreibzugriffe, nur Zahlen, drei Zufallstopologien mit festem Seed und 200 Zeilen gegen reine Python-Mengenrechnung).

## Zeitmessung (T-43-08)

Skript im Scratchpad, 188.600 Zeilen (165.000 in 22 Gruppenmitgliedern, 3 Gruppen, 23.600 auf 300 Einzelspeichern, Pfade 70 bis 90 Zeichen, 70 % der indexierten mit Chunks), Windows-Laptop: drei Statements je Zahl 2,3 bis 2,5 s, umgesetzter Einzeldurchlauf 1,11 bis 1,13 s für alle Zahlen samt `doc_keys_missing` (Ergebnisse identisch: 147.487 / 103.232 / 188.592). Plan: `SEARCH f USING INDEX files_storage (storage_id=?)`, `USE TEMP B-TREE FOR GROUP BY`, `SEARCH c USING COVERING INDEX chunks_file`.

## Gates und Tests

- ruff check: All checks passed; ruff format --check: 251 files already formatted; pyright (latest): 0 errors; vulture: leer.
- Plan-verify-Satz plus Nachbarn (coverage_counts, store_repo, status_endpoint, status_leave_out, measurement_scripts, diagnose_endpoint, index_status, poller): 1144 passed, 1 skipped.
- Volltestsuite mit den --ignore aus 40-01 (3,4 GB frei): `test_[a-m]*` 3295 passed, 43 skipped; `test_[n-r]*` 1982 passed, 278 skipped; `test_[s-z]*` 1566 passed, 10 skipped.
- Baumhash PACKAGE: 82 Dateien (unverändert), 91a917c4... -> cdd2a8e28fe9c6552b57d24fe7a792af69a3e0f0459354b3fb6072fdd3ca1d7c. Zweimal gerechnet: Rezept 40b-baumhash.py und unabhängig `find | LC_ALL=C sort | tr -d '\r' | sha256sum`, beide cdd2a8e2; Positivkontrolle derselben Pipeline über `git archive HEAD` vor dem Schritt: 91a917c4. PHP-Paare unberührt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Performance-Ziel] Ein Durchlauf statt drei Abfragen**
- **Found during:** Task 2, Zeitmessung
- **Issue:** Die Plan-Form (gemeinsame Schablone, eine Abfrage je Zahl, plus eine für die fehlenden Schlüssel) brauchte 2,3 bis 2,5 s, Ziel war unter 1,5 s.
- **Fix:** Eine Abfrage mit drei konstanten Ausdrücken (`MAX` je Schlüssel in der Gruppe, `SUM` je Einzelspeicher) und `SUM(doc_key IS NULL)`; Ausdrücke bleiben Modulkonstanten, Schablone wird nur mit Konstanten formatiert (T-43-07 unverändert). 1,1 s.
- **Commit:** a7a5d163

**2. [Rule 3 - Blocking] ruff S608**
- String-Verkettung der CTE mit dem Rumpf löste S608 aus; die CTE steht jetzt als `{sets}`-Platzhalter in der Schablone (Muster `_EMBEDDED_IN_STORAGES_SQL.format`).

**3. [Rule 3 - Blocking] Zwei Tests hielten Tombstones in counts() fest (nicht in files_modified)**
- `tests/test_phase40_audit.py::test_b6_f_40_06_a_tombstone_stays_in_indexed_and_out_of_indexed_left_out` hielt die in Phase 40 akzeptierte Asymmetrie F-40-06 fest; umbenannt in `test_b6_f_40_06_a_tombstone_is_out_of_indexed_and_out_of_indexed_left_out`, erwartet jetzt indexed 4 statt 5 (Docstring: in 43-03 geschlossen). Der alte Name bleibt als Archiv in 40-AUDIT.md.
- `tests/test_embedding_track.py::test_a_deleted_document_does_not_hold_the_mark_back_for_ever`: `counts()["indexed"]` 2 -> 1, Kommentar nachgezogen; die eigentliche Aussage (Bedingung liest indexed_alive) bleibt.

**4. Form**
- Fixture ohne `embeddedByGroup`/`embeddedByStorage` als Schlüssel (CoverageCounts trägt sie laut Plan nicht); die Herleitung der Vektorzahl steht in `derivation`.
- `S311`-noqa für `random.Random(seed)` im Test (Muster test_phase33_audit.py).

## Hinweis für 43-05 (Befund, nicht hier behoben)

- `findling_file_state` hält laut FileStateService nur skipped/failed, nie `indexed` ("this side never writes indexed"). Die N1-Bedingung aus 43-05 (`NOT EXISTS` über findling_file_state der Mitglieder mit Urteil, das nicht PHP-only ist) sieht ein im Container indexiertes Mitglied deshalb nicht. 43-05 sollte N1 über den Dateicache formulieren: kein Mitglied hat für denselben internen Pfad eine filecache-Zeile OHNE PHP-only-Urteil (LEFT JOIN findling_file_state, über `fc.path_hash`). Die Fixture beschreibt N1 bereits so ("member 11 holds the same internal path without a PHP-only verdict").

## Known Stubs

Keine.

## Self-Check: PASSED

- backend/tests/fixtures/coverage_topology.json, backend/tests/test_coverage_counts.py vorhanden; `def coverage_counts`, `INDEXED BY files_storage`, `deleted_at IS NULL` in repo.py gefunden.
- Commits 59be0046 (test) und a7a5d163 (feat) im Log, Autor street1983nk <k.cherif@outlook.de>, kein Trailer, 0 Treffer für closes/fixes/resolves #N, keine Löschungen.
