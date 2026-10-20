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
| 6 | 35-10 | `06-stichprobe.py` | `rohdaten/06-stichprobe.txt` | Stichprobe 500 Dokumente (Seed `granite-35`) aus dem Lastkorpus `--seed phase5`, nur die 500 gezogenen Dateien geschrieben, sha256 je Datei, vor dem ersten Durchsatzlauf |
| 7 | 35-10 | `07-text.sh`, `07-text.py` | `rohdaten/07-text.txt` | Text der Stichprobe einmal im ausgelieferten Image (Extraktor und OCR-Spur des Produkts), ohne Netz; nur Name, Zustand, Zeichen und sha256 je Datei in der Rohdatei |
| - | 35-10 | keins | `rohdaten/01-vorbedingungen.txt`, `rohdaten/02-rechenblatt-freigabe.txt` | Konto, Kontingent, laufende Instanzen, arm64-Manifest, Modell-sha256; Sätze, Laufzeit je Posten, Deckel, Abbruchregel, Owner-Freigabe |
| 10 | 35-10 | `10-box-aufbau.sh kappe\|docker\|pruefen` | `rohdaten/03-aufbau-arm.txt` | auf der Box: `mem=4G`, Neustart, Docker, Image per Digest, sha256 aller hochgeladenen Dateien |
| 11 | 35-10 | `11-arm-latenz.sh` | `rohdaten/11-arm-latenz.txt` | auf der Box: Token je Sekunde, Einzelanfrage kalt und warm, `--memory 2g`, Grenze aus der cgroup zurückgelesen |
| 12 | 35-10 | `12-arm-speicher.sh`, `12-arm-speicher.py` | `rohdaten/12-arm-speicher.txt` | auf der Box: `RssAnon` vor und nach Tokenizer, Sitzung, erster Charge, `memory.peak` |
| 13 | 35-10 | `13-arm-durchsatz.sh`, `13-arm-durchsatz.py` | `rohdaten/13-arm-durchsatz.txt` | auf der Box: Chunking je Modell-Tokenizer mit 1024-Token-Kappe und Einbettung der Stichprobe, Dokumente/min, Chunks/Dokument |
| 14 | 35-10 | `14-hochrechnung.py` | `rohdaten/14-hochrechnung.txt` | Hochrechnung auf 52.111 Dokumente, Annahmen ausgewiesen, e5-Bezug September daneben |
| 19 | 35-10 | `19-abbau.sh` | `rohdaten/08-abbau-boxen.txt`, `rohdaten/90-kosten.txt` | Abbau über `scripts/ops/aws_box.sh destroy`, Gegenproben gegen die API, Schlusskosten gegen den Deckel |
| 20 | 35-11 | keins | README ab Abschnitt 8 | Tabellen, Paarvergleich, Vorzeichentest, Verdikt nach der Regel |

Die Schritte 1 bis 7 laufen auf dem Entwicklungsrechner (amd64), die
Schritte 10 bis 13 auf der Box (Freigabe am Checkpoint in 35-10), 14 und 19
wieder auf dem Entwicklungsrechner.
