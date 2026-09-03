# Grundlast von Nextcloud AIO ohne Findling, Generalprobe cpx22

Rohdaten zu dem Abschnitt "Die AIO-Grundlast ohne Findling" in
`docs/performance.md`. Sie liegen hier, weil die Box, auf der sie entstanden
sind, nach dem Test gelöscht wird und eine Zahl ohne ihre Messreihe eine
Behauptung ist.

**Gemessen:** 2026-09-03T17:34:23Z bis 2026-09-03T18:04:37Z, dreißig Minuten und
vierzehn Sekunden, 361 Messpunkte je Container im Abstand von fünf Sekunden.

**Maschine:** Hetzner cpx22 in hel1, x86_64, 2 vCPU, 4 GB, Ubuntu 24.04,
cgroup v2, Nextcloud 33.0.8 aus All-in-One, PostgreSQL 18.6. Findling war zu
diesem Zeitpunkt nicht installiert, HaRP nicht zugeschaltet, und kein einziger
optionaler Container war aktiv.

**Drei Phasen:** zwölf Minuten Leerlauf, sechs Minuten mit 29 Runden
gewöhnlicher Aufrufe der Weboberfläche, zwölf Minuten Leerlauf.

**Spalten:** `timestamp,anon,file,slab,current,peak`, alle Angaben in Bytes,
gelesen aus `memory.stat` und `memory.current` der cgroup des jeweiligen
Containers. Die letzte Zeile jeder Datei ist die Abschlusszeile des Samplers mit
dem höchsten `anon`-Wert, dem finalen `memory.peak`, dem Inhalt von
`memory.events` und dem Feld `.State.OOMKilled` des Containers.

Warum `anon` und nicht `peak` die Wahrheit ist, steht im Kopf von
`scripts/ops/rss_sampler.sh` und in `docs/performance.md`.

**Erzeugt mit:**

```sh
scripts/ops/rss_sampler.sh <container> 5 <container>.csv
```

**Ergebnis in einem Satz:** die Summe über alle sechs Container liegt im Mittel
bei 224 MB und im gleichzeitigen Höchststand bei 290 MB, ohne einen einzigen
Eintrag in `memory.events` und ohne Speichertod.

## Die zweite Messung, mit HaRP

Unter `mit-harp/` liegt eine zweite, kürzere Reihe: 2026-09-03T18:12:20Z bis
18:22:43Z, zehn Minuten, sieben Container, 124 Messpunkte je Container, nachdem
HaRP als einziger optionaler Container zugeschaltet und alle Container einmal
neu gestartet wurden. Sie beantwortet genau eine Frage, nämlich was HaRP selbst
wiegt: 54 MB im Mittel, 55 MB im Höchststand, über zehn Minuten praktisch
konstant.

Die Summen der beiden Reihen sind ausdrücklich **nicht** vergleichbar. Die
zweite ist kürzer, hat keine Aufrufphase und lief direkt nach einem Neustart.
Vergleichbar ist allein die eigene Spalte von HaRP.

Diese Zahlen gelten für x86. Für ARM wird neu gemessen, nicht umgerechnet.
