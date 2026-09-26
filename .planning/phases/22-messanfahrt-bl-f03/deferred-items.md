# Phase 22: zurückgestellte Befunde

## Aus 22-07 (Owner-Entscheide)

- **Sprachfall-Eigenrang der dismax-Regel hat in 98d keine eigene Zeile.** Die beschlossene Regel (00-ablauf.md Abschnitt 6, Bedingung 2) liest den Rang der eigenen Datei jedes Sprachfalls aus den Zeilen `anfrage <nr> spitze <form>` der Anfragen 11 bis 20 (Spitze 10). 98d kennt die Kennung der eigenen Datei nicht; die Zuordnung Kennung zu Datei macht der Bericht aus dem Bestand der Box. Liegen die Sprachfall-Dateien nicht im Snapshot (98b lud sie am 10.09., der Snapshot entstand am 11.09.; P0 zeigt es), ist keine zuzuordnen, und der Entscheid heißt nach der Regel `nicht entschieden`. Für 22-08: in P0 festhalten, ob die Dateien des Kontos der Sprachfälle im Bestand stehen; 98d wird nicht geändert.

## Aus 22-06 (Generalprobe)

- **v1.2-Rohdatei 94b-grundlast-rueckkehr.txt: `abtastreihe-spitze-mb=11142026092103`.** Derselbe Leserfehler, den 94c in 5d97688 behoben hat: `awk -F:` nahm alle Ziffern des Feldes bis in den Zeitstempel. Gemeint sind 1.114 MB (Zeile `total, peak:` von rss_digest.py in derselben Datei). 94b ist gefahren und prüfsummengeschützt, die Rohdatei bleibt; der v1.2-Bericht zitiert den Wert nicht. Wer ihn zitiert, liest 1.114 MB.
- ~~**92d Phase B ungeprobt**~~ **erledigt 26.09.** (Owner-Option B, eigener CI-Lauf): `probe-92d.yml` Lauf 2 (36217297257) grün, v1.1.0 auf den Baum mit echtem App-Update, Volumen und Bestand bleiben, Gegenprobe 41. Befund behoben in bbf929e (occ upgrade 3 zählt als gelungen).
- **Versionssprung auf 1.3.0 fehlt noch im Baum** (beide info.xml tragen 1.2.0, Sprung gehört zu Phase 23). Folge für die Anfahrt: 92d installiert die PHP-Hälfte als 1.2.0; die Migration `Version001300Date20260924000000` (entfernt nur den gemerkten Backend-Versionsschlüssel) läuft auf der Box erst mit dem Sprung. Kein Messgegenstand hängt daran; nur zur Kenntnis.
- **Weg b: 92c läuft vor jedem occ upgrade.** Risiko aus 22-05, lokal nicht probbar; Owner-Frage am Checkpoint 22-07 (Weg-Wahl).

## Aus 22-02

- **92c-wechsel.sh (und damit die Vorlage von 92d): ein unerwarteter Abbruch im Phase-B-Block endet mit 0.** Bricht ein Befehl innerhalb von `{ ... } 2>&1 | tee "$ZIEL"` unter `set -eu` ab, verlässt er nur die Subshell; die Verweigerungen unterhalb der Pipeline finden keine Arbeitsdatei und das Werkzeug meldet `92C-WECHSEL-FERTIG` mit 0. Das ist dieselbe Klasse wie L-03, nur für jeden anderen Befehl des Blocks. In 92d ist die Folge durch das fail-closed Bestandstor abgefangen (fehlt die Marke `bestand-bestanden`, endet 92d mit 41), in 92e durch die Endmarke `block-durchgelaufen` (sonst 43). 92c selbst bleibt unverändert, weil es eine Nachfolgefassung mit eigenem Wächter ist; ein Fix gehört in eine eventuelle 92c-Nachfolge nach der Anfahrt.

## Aus 22-10

- **Leerer Kaltstart geklärt, Nachfreigabe braucht eine Wahl des Weges.** Ursache: Die erste hybride Suche nach Neustart lädt bei `FINDLING_EMBED_IDLE_RELEASE_SECONDS=0` die Modellgewichte selbst (`query_may_load`) und reißt den PHP-Deckel von 1,5 s (m01-Kaltstartzeilen `innerMs 1505` bis `1596` gegen `ceilingMs 1500.0`), HTTP 200 mit leerer Gruppe. Das ist der bekannte Vorfall vom 10.09.2026, der allgemeine Fall steht als Backlog-Punkt. Eine unveränderte 95c-Nachmessung liefert wieder 0 Treffer. Owner-Wahl vor jeder Nachfreigabe (README 6.11): (a) Schalter an, (b) einwortiger Begriff, (c) erst Produktfix. Nicht in 22-10 gefixt: Das wäre eine Änderung am ausgelieferten Verhalten bei jedem Containerstart, also ein Owner-Entscheid.
