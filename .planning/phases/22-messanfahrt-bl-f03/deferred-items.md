# Phase 22: zurückgestellte Befunde

## Aus 22-02

- **92c-wechsel.sh (und damit die Vorlage von 92d): ein unerwarteter Abbruch im Phase-B-Block endet mit 0.** Bricht ein Befehl innerhalb von `{ ... } 2>&1 | tee "$ZIEL"` unter `set -eu` ab, verlässt er nur die Subshell; die Verweigerungen unterhalb der Pipeline finden keine Arbeitsdatei und das Werkzeug meldet `92C-WECHSEL-FERTIG` mit 0. Das ist dieselbe Klasse wie L-03, nur für jeden anderen Befehl des Blocks. In 92d ist die Folge durch das fail-closed Bestandstor abgefangen (fehlt die Marke `bestand-bestanden`, endet 92d mit 41), in 92e durch die Endmarke `block-durchgelaufen` (sonst 43). 92c selbst bleibt unverändert, weil es eine Nachfolgefassung mit eigenem Wächter ist; ein Fix gehört in eine eventuelle 92c-Nachfolge nach der Anfahrt.
