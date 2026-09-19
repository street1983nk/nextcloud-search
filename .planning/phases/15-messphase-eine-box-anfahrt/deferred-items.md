# Zurueckgestellte Punkte der Phase 15

Punkte, die waehrend der Ausfuehrung aufgefallen sind, aber ausserhalb des
Umfangs des jeweiligen Plans liegen. Sie werden hier notiert statt gefixt, damit
ein Plan nicht die Fehler eines anderen Bereichs mitnimmt.

## 1. Der Suchparitaets-Lauf faellt am Login des Kontos `minimal` aus

- **Gefunden in:** Plan 15-07, Vorbedingung 1 (Laufnummer eines gruenen
  `integration.yml`-Laufs)
- **Datum:** 2026-09-19
- **Lauf:** 35470079862, Push auf `main` zum Commit des Plans 15-05
- **Auftrag:** `search-parity (stable34, 8.2)`
- **Schritt:** "Log every account in and keep its session"
- **Meldung:** `the login of minimal was refused, so every page answer of this
  account would be a login form`
- **Warum nicht hier gefixt:** Der Fehlschlag liegt in der Suchparitaet und
  beruehrt kein Werkzeug des Laufverzeichnisses
  `docs/measurements/2026-09-v12-messung/`. Plan 15-07 schreibt zwei Dokumente
  und aendert keine Zeile, die diesen Auftrag betreffen koennte.
- **Wirkung auf die Anfahrt:** Der letzte gruene Lauf ist damit
  **35469147833** (Commit des Plans 15-04) und gehoert nicht zum Kopf des
  Zweiges. Die Ablaufdatei verlangt ohnehin, die Laufnummer unmittelbar vor
  Schritt 7 ein zweites Mal zu holen; solange kein gruener Lauf zum gemessenen
  Stand existiert, belegt der `ci-beleg` des Sprachfall-Laufs einen aelteren
  Baum als den gefahrenen.
- **Wo es hingehoert:** vor die Anfahrt, spaetestens in die Sitzung des
  Checkpoints 15-08. Zuerst ist zu klaeren, ob der Fehlschlag sporadisch ist
  (ein zweiter Lauf desselben Commits genuegt dafuer) oder ob das Konto
  `minimal` seit Phase 13 anders angelegt wird.
- **Vorgeschichte, die dazugehoert:** derselbe Schritt hat schon einmal einen
  Befund getragen. `parity-login-probe-404` steht seit dem 11.09.2026 in den
  zurueckgestellten Punkten der STATE-Datei, dort mit dem Vermerk, dass der Fix
  `d604880` gemerged und gruen ist und nur der Sitzungsstatus nie auf erledigt
  gesetzt wurde. Der heutige Fehlschlag ist ein anderer Ast derselben Funktion:
  damals antwortete die Ergebnisseite mit 404, heute wird die Anmeldung selbst
  verweigert. Wer den Punkt aufnimmt, liest beide nebeneinander, bevor er einen
  fuer sporadisch erklaert.
