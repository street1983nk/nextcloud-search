# Phase 44: zurückgestellte Befunde außerhalb des Planumfangs

## Aus 44-02 (21.11.2026)

- `backend/tests/test_store_metadata.py::test_the_store_listing_document_avoids_the_blocked_term_counting_every_line` ist auf dem Stand vor 44-02 (b5b202e3) bereits rot: docs/store-listing.md enthält den gesperrten Begriff der Owner-Wortregel (E-H2). Die Datei wurde zuletzt in 24c04abd (16.11.2026) geändert, 44-02 berührt sie nicht. Nicht behoben (Scope); vor dem Push in 44-09 klären, sonst ist python.yml rot.
  - **Erledigt 21.11.2026** (Owner-Entscheid E-10 "Umformulieren"): beide Stellen im 1.6.5-Abschnitt umformuliert, Test unverändert, test_store_metadata.py 150 passed; Commit 1d6236f2.
