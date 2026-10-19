# Der Ablauf des granite-Vergleichs, in seiner Reihenfolge

Diese Datei ist der Ablaufplan des Verzeichnisses
`docs/measurements/2026-10-granite-vergleich/`. Regel und Methode stehen im
README (Abschnitte 1 bis 7, vom Owner am 19.10.2026 abgenommen) und werden hier
nicht wiederholt. Wer den Lauf ein zweites Mal fahren will, ruft die Skripte in
der genannten Reihenfolge, strikt seriell, ohne Browser und ohne andere Last.

Vorweg, weil es den ganzen Rest trägt:

- **Kein Maschinenpfad im Skript.** Ziele kommen per Umgebungsvariable
  (`WORK`, `E5_DIR`, `IMAGE`) und liegen außerhalb des Repositoriums. Keine
  Modelldatei wird committet.
- **Freier Speicher vor jedem Schritt** steht in der Rohdatei. Unter rund
  1 GB frei oder bei Swap bricht der Lauf ab (D-35-11), und es wird nicht auf
  eine andere Maschine ausgewichen.

| Schritt | Plan | Skript | Rohdatei | Inhalt |
|---:|---|---|---|---|
| 1 | 35-09 | `01-artefakte.sh` | `rohdaten/01-artefakte.txt` | granite der Revision `835ad140` holen, sha256 von fp32 und Tokenizer gegen README Abschnitt 3; e5 aus dem ausgelieferten Image, sha256 gegen `MODEL_SHA256` |
| 2 | 35-09 | `02-int8.sh` | `rohdaten/02-int8.txt` | zwei Läufe von `quantize_model.py` mit Fenster 85.000.000 bis 110.000.000, Größe, sha256, `cmp` |
| 3 | 35-09 | `03-qualitaet.sh` | `rohdaten/03-qualitaet-<modell>-<fassung>-<sprache>.txt`, `rohdaten/03-positivkontrolle.txt` | `model_quality.py` für e5 (mean, Präfixe an) und granite (cls, Präfixe aus), int8 und fp32, de, en, fr, `--per-case`; Positivkontrolle granite int8 mit mean |
| 4 | 35-09 | `04-latenz-amd64.sh` | `rohdaten/04-latenz-amd64.txt` | Token je Sekunde, Einzelanfrage kalt und warm (p50, p95) für e5 int8 und granite int8, zwei Kerne, zwei Threads, ohne Netz |
| 5 | 35-09 | `05-image-zuwachs.sh` | `rohdaten/05-image-zuwachs.txt` | Größe unkomprimiert und gzip je Datei eines zweiten Modells, Summe |
| 6 | 35-10 | folgt in 35-10 | `rohdaten/06-*` | Stichprobe 500 Dokumente (Seed `granite-35`) samt sha256 je Datei, vor dem ersten Durchsatzlauf |
| 7 | 35-10 | folgt in 35-10 | `rohdaten/07-*` | arm64 (m7g.large, `mem=4G`, `--memory 2g`): Speicher und Latenz beider Modelle |
| 8 | 35-10 | folgt in 35-10 | `rohdaten/08-*` | arm64: Durchsatz auf der Stichprobe, Hochrechnung der Neu-Einbettung |
| 9 | 35-11 | keins | README ab Abschnitt 8 | Tabellen, Paarvergleich, Vorzeichentest, Verdikt nach der Regel |

Die Schritte 1 bis 5 laufen auf dem Entwicklungsrechner (amd64), die
Schritte 6 bis 8 auf der Box (Freigabe am Checkpoint in 35-10).
