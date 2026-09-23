# Zurueckgestellte Befunde, Phase 17

Befunde, die waehrend der Ausfuehrung auffielen, aber ausserhalb des Auftrags
des jeweiligen Plans liegen. Nicht gefixt, nur festgehalten.

## Aus Plan 17-08 (2026-09-23)

### 1. Der `pyright: ignore` an `TANTIVY_VERSION` ist sachlich ueberfluessig geworden

- **Ort:** `backend/src/findling/index/open.py`, Zeilen 61 bis 66
- **Befund:** Der Kommentar begruendet das `# pyright: ignore[reportAttributeAccessIssue]`
  damit, dass "the type stub shipped with tantivy 0.26.0 does not declare the
  attribute". Mit 0.26.2 stimmt das nicht mehr: `tantivy/tantivy.pyi` deklariert
  in Zeile 714 `__version__: str`. Die Unterdrueckung und die halbe Begruendung
  daneben sind damit gegenstandslos.
- **Warum nicht gefixt:** Zweierlei. Erstens meldet ihn niemand, und genau daran
  hat Plan 17-08 die Entfernung geknuepft: `uv run ruff check` und
  `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright` sind beide ohne Befund,
  weil `typeCheckingMode = "basic"` `reportUnnecessaryTypeIgnoreComment` nicht
  einschaltet. Zweitens liegt die Datei unter `backend/src/findling/`, und jede
  Bewegung dort zieht `PACKAGE_TREE_HASH_TODAY` in
  `backend/tests/test_measurement_scripts.py` nach, was in einer Welle mit
  mehreren Worktrees einen vermeidbaren Konflikt erzeugt.
- **Empfehlung:** In einem Plan der naechsten Phase zusammen mit einer ohnehin
  faelligen Aenderung an den Paketquellen erledigen, dann faellt der Baumhash
  nur einmal an.

### 2. Drei Versionsangaben in `THIRD-PARTY.md` sind aelter als ihr Pin

- **Ort:** `THIRD-PARTY.md`, Zeilen 141, 145, 147
- **Befund:** `pypdf` steht auf 6.16.1, gepinnt ist 6.19.0; `striprtf` steht auf
  0.0.32, gepinnt ist 0.0.33; `lxml` steht auf 6.1.1, gepinnt ist 6.1.3. Die
  Lizenzangaben sind davon nicht betroffen.
- **Warum nicht gefixt:** Der Befund ist aelter als dieser Plan und hat mit dem
  tantivy-Sprung nichts zu tun. Plan 17-08 fasst in dieser Tabelle nur die
  tantivy-Zeile an.
- **Empfehlung:** Ein Test, der die Tabelle gegen `backend/pyproject.toml`
  haelt, waere billiger als jede weitere Handpflege. Das Muster dafuer steht in
  `backend/tests/test_lockstep_versions.py`.
