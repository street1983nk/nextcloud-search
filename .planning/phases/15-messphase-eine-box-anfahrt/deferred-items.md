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
- **Nachtrag 2026-09-20:** Der Lauf zum Commit des Plans 15-06 (f650c10,
  35471225104) ist gruen geworden, derselbe Auftrag `search-parity
  (stable34, 8.2)` samt Login-Schritt bestanden. Zwischen 15-04 (gruen) und
  15-06 (gruen) liegen nur Mess-Skripte, deren Tests und Doku, nichts an
  Anmeldung oder Suchparitaet; der Fehlschlag 35470079862 ist damit beidseitig
  eingerahmt und als Einzelfall einzuordnen. CI_LAUF-Kandidat ist jetzt
  35471225104 (Nachtrag in rohdaten/02-vorbedingungen.txt); die zweite Holung
  unmittelbar vor Schritt 7 bleibt Pflicht.

---

## Das gesperrte Wort unter `docs/` (Befund L-10, 2026-09-21)

- **Gefunden bei:** der Durchsicht des Plans 15-16 ueber `docs/performance.md`,
  danach mit einer zweiten, weiteren Suche ueber das ganze Verzeichnis
  nachgeprueft. Genau diese zweite Suche hat den Befund erst richtig gemacht.
- **Was:** Das in oeffentlichen Artefakten gesperrte Wort (Stamm "arch" plus
  "iv") steht **116 mal in 17 Dateien** unter `docs/`. Die Formen: 60 mal
  "archive", 17 mal "archives", 38 mal "archiv", dazu "Archivstufe" (4),
  "Archiven" (4), "Archivs" (2), "Archivordner" und "Archiveintraege". Rund 50
  Vorkommen sind deutsche Formen und damit von der Regel getroffen; die
  englischen sind technische Bezeichner (`tar archive`, `SnapshotArchiveStorage`,
  der Text der `info.xml`).
- **Auch in dieser Phase:** `docs/measurements/2026-09-v12-messung/rohdaten/03-aufbau.txt`,
  Zeile 145, in einem deutschen Satz. Das ist kein Altbestand, sondern am
  20.09.2026 geschrieben worden.
- **Warum nicht hier gefixt:** Erstens ist eine gefahrene Rohdatei Teil des
  Belegs und wird nach der Anfahrt nicht mehr redigiert; dieselbe Regel, aus der
  der Pruefsummen-Waechter aus 15-15 folgt. Zweitens schreibt Task 1 des Plans
  15-16 ausschliesslich Nachtraege, und seine Abnahmebedingung lautet, dass
  `git diff` nur Ergaenzungen zeigt. Drittens waeren 50 Stellen in 17 Dateien
  eine eigene Aufgabe und keine Nebenwirkung.
- **Wo es hingehoert:** Phase 16, in die Durchsicht der oeffentlichen Texte vor
  der Store-Einreichung, und zwar mit einem Gate statt mit einer Durchsicht: die
  Regel ist heute nirgends geprueft, und deshalb ist sie 116 mal unbemerkt
  geblieben. Die Rohdaten der bisherigen Anfahrten bleiben ausgenommen.

---

## Kennungen und oeffentliche Adressen unter `docs/` (Befund M-02, 2026-09-21)

- **Gefunden bei:** der Geheimnis-Gegenprobe des Phasenaudits, als sie ein
  zweites Mal gefahren wurde, diesmal ueber das ganze Verzeichnis `docs/` statt
  nur ueber die 80 committeten Dateien der Phase 15.
- **Was:** In **18 Dateien 58 Werte** der Art, die die Regel verbietet: eine
  Instanzkennung, zwei Volumekennungen, eine Security-Group-Kennung und rund
  zwanzig oeffentliche IPv4-Adressen, darunter die der Box und die des Owners.
  Die Werte stehen hier nicht; eine Liste an dieser Stelle waere die
  neunzehnte Datei.
- **Woher:** aus den Phasen 5 bis 12. **Keiner stammt aus Phase 15.** Eine der
  Dateien liegt im Laufverzeichnis dieser Anfahrt
  (`docs/measurements/2026-09-v12-messung/rohdaten/01-aws-lesende-proben.txt`),
  ist aber am 18.09.2026 mit Plan 12-03 committet worden.
- **Wie schwer:** gering im Schaden, real in der Regel. Alle bezeichneten
  Ressourcen sind abgebaut und gegen die API als abgebaut zurueckgelesen, die
  Adressen sind dynamisch vergeben und laengst neu vergeben.
- **Warum nicht hier gefixt:** Plan 15-16 schreibt zwei Dokumente fort und legt
  ein Audit an; er fasst keine Rohdatei einer frueheren Phase an. Eine
  nachtraeglich redigierte Rohdatei ist kein Beleg mehr, und die Historie
  behaelt die Werte ohnehin.
- **Die eigentliche Luecke, und sie ist die Aufgabe:** die Geheimnisregel ist in
  diesem Projekt nirgends als Gate gefahren, sondern je Plan als Suche ueber die
  Dateien, die der Plan selbst nennt. Wer eine Datei nicht nennt, prueft sie
  nicht.
- **Wo es hingehoert:** Phase 16. Vorschlag: die acht Familien der Gegenprobe
  (PEM-Kopf, SSH-Material, AWS-Zugangskennungen, uebrige Ressourcenkennungen,
  Rechnernamen, Schluesselwort-mit-Wert, IPv6, base64-Bloecke ab 40 Zeichen,
  dazu das Muster der Umsetzung) als Testfall ueber `docs/` fahren, mit einer
  benannten Ausnahmeliste fuer die Altbestaende, die nicht mehr redigiert
  werden. Ein Gate mit Ausnahmeliste ist ehrlicher als eine Regel ohne Gate.
