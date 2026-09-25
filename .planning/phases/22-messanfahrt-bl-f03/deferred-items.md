# Phase 22: zurückgestellte Befunde

## Aus 22-06 (Generalprobe)

- **v1.2-Rohdatei 94b-grundlast-rueckkehr.txt: `abtastreihe-spitze-mb=11142026092103`.** Derselbe Leserfehler, den 94c in 5d97688 behoben hat: `awk -F:` nahm alle Ziffern des Feldes bis in den Zeitstempel. Gemeint sind 1.114 MB (Zeile `total, peak:` von rss_digest.py in derselben Datei). 94b ist gefahren und prüfsummengeschützt, die Rohdatei bleibt; der v1.2-Bericht zitiert den Wert nicht. Wer ihn zitiert, liest 1.114 MB.
- **92d Phase B ungeprobt** (occ upgrade, unregister ohne --rm-data, Registrierung über HaRP, Bestandstor): lokal nicht fahrbar, weil am Docker-Dienst drei Nextcloud-Instanzen laufen und das Tor 37 richtig hält. Owner-Frage am Checkpoint 22-06/22-07.
- **Weg b: 92c läuft vor jedem occ upgrade.** Risiko aus 22-05, lokal nicht probbar; Owner-Frage am Checkpoint 22-07 (Weg-Wahl).

## Aus 22-02

- **92c-wechsel.sh (und damit die Vorlage von 92d): ein unerwarteter Abbruch im Phase-B-Block endet mit 0.** Bricht ein Befehl innerhalb von `{ ... } 2>&1 | tee "$ZIEL"` unter `set -eu` ab, verlässt er nur die Subshell; die Verweigerungen unterhalb der Pipeline finden keine Arbeitsdatei und das Werkzeug meldet `92C-WECHSEL-FERTIG` mit 0. Das ist dieselbe Klasse wie L-03, nur für jeden anderen Befehl des Blocks. In 92d ist die Folge durch das fail-closed Bestandstor abgefangen (fehlt die Marke `bestand-bestanden`, endet 92d mit 41), in 92e durch die Endmarke `block-durchgelaufen` (sonst 43). 92c selbst bleibt unverändert, weil es eine Nachfolgefassung mit eigenem Wächter ist; ein Fix gehört in eine eventuelle 92c-Nachfolge nach der Anfahrt.
