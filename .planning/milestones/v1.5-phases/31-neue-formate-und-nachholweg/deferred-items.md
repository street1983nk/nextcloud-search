# Phase 31: zurückgestellte Punkte außerhalb des Plans

## Aus Plan 31-15 (Audit)

- `backend/src/findling/worker/embedding.py:1159` liest den Cursor der
  Vektor-Nachholung mit demselben Muster wie L-31-01
  (`int(cursor) if cursor.isdigit() else 0`). Ein von Hand veränderter Wert
  mit hochgestellten Ziffern wirft `ValueError`, eine Zahl über 2^63 einen
  `OverflowError` aus SQLite. Vor Phase 31 entstanden und nicht Teil des
  Phasen-Diffs; der Fix in `worker/recheck.py` (`resume_after`) ist die
  Vorlage. Kandidat für den Launch-Korpus der Phase 36.
