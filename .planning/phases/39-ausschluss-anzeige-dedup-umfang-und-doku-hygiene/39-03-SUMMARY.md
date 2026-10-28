---
phase: 39-ausschluss-anzeige-dedup-umfang-und-doku-hygiene
plan: 03
subsystem: extract-store-hygiene
tags: [review-infos, archive, odf, office, vanished-storages, pillow, docs-02]
requires:
  - 36-REVIEW.md IN-01 bis IN-06
  - 39-01 (Paket-Baumhash 5f4d6d18..., repo.py-Stand)
provides:
  - archive._ZIP_TRAVERSAL (Final-Konstante neben _ZIP_RATIO, _ZIP_OVERLAP)
  - archive.too_many_entries(path) als einziger Zaehl-Helfer fuer ODF und OOXML
  - drop_orphan_bookmarks raeumt verwaiste vanished_storages-Stempel
  - 39-IN-ENTSCHEIDE.md (Entscheid je IN-01..IN-06)
affects:
  - 39-04 (Paket-Baumhash jetzt 9c6fb4a1...)
  - 40 (Audit-Gate liest 39-IN-ENTSCHEIDE.md)
tech-stack:
  added: []
  patterns:
    - "gemeinsamer Helfer im Modul, das Zaehlung und Ausnahmen besitzt; Aufrufer importieren per from-import"
key-files:
  created:
    - .planning/phases/39-ausschluss-anzeige-dedup-umfang-und-doku-hygiene/39-IN-ENTSCHEIDE.md
  modified:
    - backend/src/findling/extract/archive.py
    - backend/src/findling/extract/odf.py
    - backend/src/findling/extract/office.py
    - backend/src/findling/extract/image.py
    - backend/src/findling/extract/sandbox.py
    - backend/src/findling/store/repo.py
    - backend/tests/test_extract_archive.py
    - backend/tests/test_extract_signatures.py
    - backend/tests/test_store_vanished.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "IN-01 bis IN-05 fix in v1.6 (IN-02, IN-05 nur Kommentar), IN-06 accept: grobe Obergrenze dokumentiert, Folge nur die Urteilsklasse einer feindlichen Datei"
  - "too_many_entries oeffentlich in archive.py; odf.py und office.py brauchen den Modulimport archive nicht mehr"
  - "IN-01-Test liest CLOSED_DETAILS aus test_phase36_audit, die ausgeschriebene Liste von 36-WORTLAUT A3"
metrics:
  duration: "ca. 20 min"
  completed: 2026-10-28
  tasks: 2
  commits: 3
---

# Phase 39 Plan 03: IN-01 bis IN-06 der Phase-36-Review entschieden Summary

Fuenf INFO-Befunde der Phase-36-Review sind behoben (Konstante _ZIP_TRAVERSAL, ein gemeinsamer too_many_entries-Helfer in archive.py, Aufraeumen verwaister vanished_storages-Stempel, zwei klaerende Kommentare zur Pillow-Kopflesung und zur Ein-Thread-Invariante), IN-06 ist mit Begruendung akzeptiert; alles steht in 39-IN-ENTSCHEIDE.md.

## Commits

| Task | Commit | Inhalt |
|---|---|---|
| 1 RED | e6ebf240 | test_store_vanished.py: zwei IN-04-Tests (verwaister Stempel faellt mit den verwaisten Lesezeichen, verwaister Stempel allein faellt auch ohne Lesezeichen), beide rot |
| 1 GREEN | d27256bf | IN-01, IN-03, IN-04 Code; IN-02, IN-05 Kommentare; IN-01-Test; Gate in test_extract_signatures.py umgestellt; PACKAGE_TREE_HASH_TODAY bewegt (gleicher Commit wie backend/src) |
| 2 | d26c3579 | 39-IN-ENTSCHEIDE.md |

## Verify-Ergebnisse (lokal, 28.10.2026, kein Docker)

- Plan-verify: `uv run pytest tests/test_store_vanished.py tests/test_extract_archive.py tests/test_extract_signatures.py tests/test_phase31_audit.py tests/test_phase36_audit.py tests/test_phase36_hostile_corpus.py tests/test_measurement_scripts.py` gruen (vor dem Hash-Nachzug 931 passed, 1 erwarteter Fehlschlag am Baumhash)
- Erweiterter Satz inklusive test_extract_documents, test_load_corpus, test_model_probe, test_sandbox, test_reconcile, test_reconcile_vanished, test_store_repo, test_image_heic, test_extract_edge_paths: 1374 passed, 12 skipped
- Paket-Baumhash unabhaengig mit find, sort, tr und sha256sum nachgerechnet: 80 Dateien, `9c6fb4a1634eb0fdce332681e8f1b6993292d3b7f036216dc209a3552839ae7e`, gleich dem Rezept 40b-baumhash.py; PHP-Paar unveraendert
- ruff check src tests, ruff format --check src tests: gruen; pyright (PYRIGHT_PYTHON_FORCE_VERSION=latest): 0 errors; vulture (Konfiguration und --min-confidence 80 src tests): kein Fund
- Akzeptanz-greps: `_ZIP_TRAVERSAL` 2 Treffer in archive.py, `OverLimit("zip_traversal")` 0, `def _too_many_entries` in odf.py und office.py je 0, `def too_many_entries` in archive.py 1, `_FORGET_STORAGE_VANISHED_SQL` innerhalb drop_orphan_bookmarks (repo.py Zeile 1548), `archive.too_many_entries` 2 Treffer im Signatur-Test, `_too_many_entries` dort nur in der hasattr-Pruefung; 39-IN-ENTSCHEIDE.md hat 6 IN-Zeilen

## Umgestelltes Quelltext-Gate

test_extract_signatures.py::test_every_reader_counts_before_it_opens_the_package (W4-Revision des Plans): liest jetzt `inspect.getsource(archive.too_many_entries)` (enthaelt count_central_directory, kein `ZipFile(`), prueft fuer odf und office `not hasattr(module, "_too_many_entries")`, `module.too_many_entries is archive.too_many_entries` und den from-import im Quelltext, und haelt die Reihenfolge `too_many_entries(path)` vor `ZipFile(` in odf.extract_odf und office._refused_before_the_loader. Der Teil zu extract_docx/pptx/xlsx ist unveraendert. Kein weiteres Gate aus 31/36-Audit fiel aus; die S4-Probe in test_phase36_audit loest `OverLimit(_ZIP_TRAVERSAL)` ueber die Modul-Strings auf und bleibt gruen.

## Deviations from Plan

None - plan executed exactly as written. Kleine Ergaenzung im Rahmen von IN-04: die fruehe Rueckkehr von drop_orphan_bookmarks bezieht die Stempel mit ein, damit ein verwaister Stempel ohne verwaiste Lesezeichen nicht uebersprungen wird (eigener Test).

## Hinweis Nebenlaeufigkeit

Zwischen RED- und GREEN-Commit hat eine Parallel-Session 0ca8c635 (docs(38)) auf main gelegt; kein Dateikonflikt.

## Self-Check: PASSED

- 39-IN-ENTSCHEIDE.md vorhanden, Commits e6ebf240, d27256bf, d26c3579 im Log
