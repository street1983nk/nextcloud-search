# Die Vergleichsmessung auf der 4-GB-ARM-Box, 09. und 10.09.2026

Dieser Bericht stellt den Lauf vom 09./10.09.2026 Zeile für Zeile neben den
Semantiklauf vom 05.09.2026 (kurz **06-11**, der Stand, auf dem v1.0 ruht) und
neben die Nachmessung vom 07.09.2026. Wo eine dritte Grundlinie etwas
hinzufügt, steht der Lauf **05-21** ohne Semantik als eigene Spalte daneben.

Er folgt der Abschnittsfolge des v1.0-Berichts
(`docs/measurements/2026-09-05-semantiklauf-m7g/README.md`) und der
Vergleichsform der Nachmessung
(`docs/measurements/2026-09-nachmessung-m7g/README.md`): Posten, Grundlinie,
dieser Lauf, Differenz.

Vier Regeln gelten in jedem Abschnitt, und sie sind der Grund, warum dieser
Bericht länger ist als der Lauf schön:

1. **Jede Zahl nennt ihre Rohdatei.** Eine Zahl, die in keiner Rohdatei unter
   `rohdaten/` steht, kommt hier nicht vor; fehlt sie, steht da, dass sie fehlt.
2. **Keine Zahl ist gerundet, geglättet oder von einem Ausreißer befreit.**
   Das höchste Einzelmaximum der Seitenroute steht mit 0,825 s so da, wie es
   gemessen wurde.
3. **Eine Erwartung ist als Erwartung beschriftet, eine Messung als Messung.**
   Die Spalte "Erwartung v1.1" der Recherche (118 bis 150 MB Grundlast) ist eine
   Rechnung aus der amd64-Nachmessung und wird nur als solche genannt.
4. **Eine Zahl ohne Entsprechung in 06-11 ist eine Erstmessung und keine
   Vergleichszeile.** Das Wort ERSTMESSUNG steht dann als Beschriftung im
   Abschnitt. Das betrifft die Abschnitte 9, 10, 11 und 12.

Das Kernaussage-Blatt `00-kernaussage.md` ist die kurze Fassung dieses Berichts,
und der Owner hat seine vier Kernzahlen am 10.09.2026 abgenommen. Wo dieser
Bericht und das Blatt sich unterscheiden, gilt die Rohdatei.

---

## 1. Die Umgebung, und der Beweis des gemessenen Standes

| Posten | 06-11 | Nachmessung 07.09. | **dieser Lauf** | Rohdatei |
|---|---|---|---|---|
| Instanz | `i-06b1d913f5c6f669b`, AWS `m7g.large` | dieselbe | **dieselbe** | `rohdaten/90-bestand.txt` |
| Architektur | `aarch64`, nativ | dieselbe | **dieselbe, 2 Kerne** | `rohdaten/90-bestand.txt` |
| Maschinenspeicher | 4 GB, `mem=4G` aus `/proc/cmdline` | derselbe | **derselbe, zurückgelesen** | `rohdaten/90-bestand.txt` |
| harte Containergrenze | 2.147.483.648 Byte | dieselbe | **dieselbe, aus der cgroup zurückgelesen** | `rohdaten/94-grundlast.txt` |
| Nextcloud-Instanzen auf dem Docker-Dienst | nicht gezählt | nicht gezählt | **1, zweimal gezählt** | `rohdaten/90-bestand.txt`, `rohdaten/92-wechsel.txt` |
| Abbild | `ghcr.io/street1983nk/findling_backend:dev` | dasselbe | **dasselbe, gezogen und nicht auf der Box gebaut** | `rohdaten/92-wechsel.txt` |

**Der Digest, und der Befund an ihm.** Gemessen wurde
`sha256:78ab61d8a5ae4a0c68a1b0b04d2e4f2a96cd8c494325c7562a5d3c435f0be207`,
arm64, erzeugt am 2026-09-08T19:48:32Z. Plan 10-02 hatte
`sha256:eed6a5fc...` (Manifestindex) und `sha256:ae58d930...` (arm64-Hälfte)
aufgeschrieben. `92-wechsel.sh` schreibt dazu die Zeile `digest-gleich nein`
und benennt den Grund selbst: `:dev` ist ein wandernder Zeiger, und der
Pfadfilter von `docker.yml` greift nach `backend/**`, also verschiebt ein
Commit, der nur eine Testdatei hinzufügt, diese Zeichenkette, ohne das Abbild
inhaltlich zu ändern. **Der Befund steht hier statt in einer Fußnote, und die
Feststellung, die entscheidet, ist der Baumhash.**

**Die drei Baumhashes, die den Stand belegen** (`rohdaten/40b-baumhash.txt`):

| Was | Dateien | Baumhash |
|---|---|---|
| das Paket **im Abbild** | 54 | `6c47cd219c430bccc9d5d57b1de1d2ff9f8672fa4f42b1160d0a31efb9367476` |
| das Paket **im Arbeitsbaum** | 54 | `6c47cd219c430bccc9d5d57b1de1d2ff9f8672fa4f42b1160d0a31efb9367476` |
| die **PHP-Hälfte** im Arbeitsbaum | 58 | `4a4c6f62598e2db036c0f75bf4dc6c7040c9fdafe4fb36798a8f09bb7509d9ed` |

Urteilszeile: `baumhash-gleich ja`. Das Abbild trägt Byte für Byte dasselbe
Paket wie der Arbeitsbaum, aus dem dieser Bericht geschrieben ist.

**Warum dieser Beweis in beiden Vorläuferberichten leer geblieben ist.** Sowohl
06-11 als auch die Nachmessung haben die Gleichheit des Codestandes behauptet
und dabei eine leere Rohdatei hinterlassen. Der Grund ist eine einzige fehlende
Option: `40-abbild.sh` rief `docker run` ohne `-i`, also bekam der
Baumhash-Rechner im Container seinen Quelltext nie über die Standardeingabe und
schrieb nichts. Dieser Lauf hat das Skript in `40b-baumhash.sh` neu gefasst und
den Abbruchpfad daran gehängt: weniger als drei `baumhash:`-Zeilen, und
`92-wechsel.sh` endet mit 3 statt weiterzulaufen.

**Was der Prüfpfad von `docker.yml` ist, und was er nicht ist.** `docker.yml`
prüft Manifest und Provenance des gebauten Abbilds. Das ist ein **Prüfpfad**.
Es ist **keine** GitHub-Artefakt-Attestierung und damit keine Signatur des
Abbilds im Sinne einer kryptographisch nachweisbaren Herkunftskette. Dieser
Bericht behauptet über das Abbild nichts, was über den Baumhash und den
Prüfpfad hinausgeht.

---

## 2. Der Korpus, und dass es noch dieselben Bytes sind

Kriterium 1 verlangt "mit dem vorhandenen v1.0-Korpus". Die Feststellung lief
**vor** dem Indexaufbau, weil ein Fehlbefund danach 26 Stunden gekostet hätte
(`rohdaten/91-korpus.txt`).

| Posten | erwartet (v1.0) | **gemessen** | Urteil |
|---|---|---|---|
| Dateien | 50.000 | **50.000** | gleich |
| Byte | 20.208.046.426 | **20.208.046.426** | gleich |
| Listen-Prüfsumme | `bcbef9b2cb067c2200df2a4a2e89408f690710983117d4e78328024046098a72` | **dieselbe** | gleich |

Urteilszeile: `korpus-gleich ja`. Gerechnet wurde mit dem Rezept des
Semantiklaufs (`44-korpus-pruefsumme.py`) und nicht mit einem nachgebauten. Die
x86-Prüfsumme `c03a8803...` ist ausdrücklich **nicht** der Wert, gegen den diese
Box verglichen wird; die Rohdatei sagt das selbst.

---

## 3. Der Wiederaufsatz: warum beide Hälften auf null mussten

Am 07.09.2026 hat eine zweite, frische Nextcloud am selben Docker-Dienst mit
`app_api:app:unregister --rm-data` das Messvolumen der **ersten** Instanz
entfernt. Der Volumenname einer ExApp folgt allein aus ihrer App-Kennung, und
zwei Instanzen teilen sich damit denselben Namen. Der Index war weg, die
Rohdaten waren gerettet, weil sie um 06:23Z committet waren und das Volumen um
06:46Z fiel.

Daraus folgt für diesen Lauf dreierlei, und alles drei ist belegt:

- **`--rm-data` war hier Absicht und lief vor dem Indexaufbau**, nicht danach
  (`rohdaten/93-nullstand.txt`). Der Lauf startet auf einem Nullstand, der mit
  Zahlen belegt ist: Volumeninhalt, `oc_findling_file_state`, die Marken in
  `meta`, die Ausgabe von `occ findling:index`.
- **Auf der Box lief genau eine Nextcloud**, und zwar zweimal gezählt: einmal
  vor jedem Eingriff (`rohdaten/90-bestand.txt`, `nextcloud-einzahl ja`) und
  einmal unmittelbar vor dem `--rm-data` (`rohdaten/92-wechsel.txt`,
  `nextcloud-instanzen 1`). Beide Skripte brechen bei mehr als einer mit 5 ab.
- **Der Startpunkt des Laufs war nicht null**, und das ist der Vorbehalt, der
  jede Laufzeitzahl dieses Berichts begleitet: beim Anstoß standen
  `vorrat=2040 indexed=1653 embedded=264`
  (`skripte/00-ablauf.md`, Abschnitt 0). Grund: Schritt 3 schaltet die PHP-App
  ein, der Poller begann sofort zu arbeiten. Für die Grundlast in Schritt 5 ist
  die App wieder abgeschaltet und der Container neu gestartet worden, damit
  "Modell nie geladen, noch keine Suche" auch stimmt.

---

## 4. Die Kernaussage, in der Form aus D-H2

> **Der Indexaufbau über 52.111 Dokumente hat unter einer harten Grenze von
> 2 GiB keinen einzigen Prozess das Leben gekostet. Die drei Schadenszähler
> `oom`, `oom_kill` und `oom_group_kill` stehen je auf null, die anon-Spitze des
> ganzen Laufs lag bei 1.764,2 MB, gemessen am 2026-09-10 um 08:12:24Z, und der
> Zähler `max` steht auf 21.939.**

**Was `max` bedeutet, in einem Satz:** der Dateicache des Tantivy-Index lag
gegen die Grenze an, der Kernel hat ihn 21.939 mal zurückgedrängt, und kein
Prozess wurde dabei getötet. Der Zähler wird hier weder verschwiegen noch
wegerklärt.

| Größe | 06-11 (v1.0) | Nachmessung 07.09. | **dieser Lauf** | Differenz zu 06-11 | Rohdatei |
|---|---|---|---|---|---|
| `oom` | 0 | 0 | **0** | 0 | `rohdaten/07-oom-beweis.txt` |
| `oom_kill` | 0 | 0 | **0** | 0 | `rohdaten/07-oom-beweis.txt` |
| `oom_group_kill` | 0 | 0 | **0** | 0 | `rohdaten/07-oom-beweis.txt` |
| `OOMKilled`, `RestartCount` | false, 0 | false, 0 | **false, 0** | gleich | `rohdaten/07-oom-beweis.txt` |
| höchster `anon` des Laufs | 1.837,8 MB (05:34:05Z) | 1.812,7 MB (05:55:53Z) | **1.764,2 MB (2026-09-10T08:12:24Z)** | **minus 73,6 MB** | `rohdaten/00-ende.txt`, aus `rohdaten/96-volllauf.csv` |
| `memory.events max` | **2.796** | 0 | **21.939** | **plus 19.143** | `rohdaten/07-oom-beweis.txt` |
| `memory.peak` | 2.147.741.696 Byte | 1.990,3 MB | **2.147.483.648 Byte, gleich der harten Grenze** | an der Grenze | `rohdaten/07-oom-beweis.txt` |
| `memory.current`-Spitze | 2.048,0 MB | 1.219,8 MB | **2.048,0 MB** | 0,0 MB | `rohdaten/00-ende.txt` |
| `sock_throttled` | 3.044 | 0 | **1.997** | minus 1.047 | `rohdaten/07-oom-beweis.txt` |
| harte Grenze | 2147483648 | dieselbe | **dieselbe, nach dem Neustart zurückgelesen** | gleich | `rohdaten/95-spitze-nachher.txt` |

**Der Beweis ist vor jedem Eingriff erhoben.** `07-oom-beweis.txt` trägt vier
Ablesungen: zwei vom Wächter am Ende beider Spuren (13:04:57Z und 13:05:11Z),
eine dritte am 10.09. um 13:48:08Z als erste Handlung der Nachmessungen, und
eine vierte um 14:46:22Z nach allen Messungen. Der bewusste Neustart des
Containers fand um 14:04:38Z statt, also nach den ersten drei.

**Ein Nebenbefund, der zu `max` gehört und ihn einordnet:** nach dem Neustart,
über alle vier Messblöcke des 10.09. hinweg, steht `max` auf **0**
(`rohdaten/07-oom-beweis.txt`, vierte Ablesung). Der Zähler gehört zum
Indexaufbau und nicht zum Suchbetrieb.

---

## 5. Die Grundlast, aufgeschlüsselt, neben der aus 06-11 und der Nachmessung

Dies ist **MESS-01**. Gemessen an einem Container, der über AppAPI gestartet
und bewaffnet wurde, dessen Modell in diesem Start nie geladen war und der noch
keine Suche gesehen hat (`rohdaten/94-grundlast.txt`, Teil A).

### 5.1 Grob, nach `52-woher-die-grundlast.py`

| Posten | 06-11 | Nachmessung 07.09. | 05-21 (ohne Semantik) | **dieser Lauf** | Differenz zu 06-11 |
|---|---|---|---|---|---|
| anon im Leerlauf, Modell nie geladen | 691,8 MB | 693,4 MB | 58,7 MB | **103,2 MB** (108.199.936 Byte) | **minus 588,6 MB** |
| `memory.current` daneben | | | | **115,2 MB** (120.745.984 Byte) | |
| `memory.peak` dieses Starts | | | | **131,0 MB** (137.326.592 Byte) | |

**Die gerechnete Erwartung lag bei 118 bis 150 MB** (Annahme A5 der Recherche,
eine Rechnung aus der amd64-Nachmessung und keine Messung). Der gemessene Wert
liegt darunter. Die Rohdatei schreibt dazu die Zeile
`grundlast-erwartung getroffen: 103.2 MB liegt unter der Schwelle`.

### 5.2 Fein, in den fünf benannten Posten, neben der nativen arm64-Spalte aus Plan 10-02

`rohdaten/94-grundlast.txt`, Teil D, gegen
`docs/measurements/2026-09-grundlast-fein/rohdaten/01-grundlast-fein-arm64.txt`
(Lauf 34325000302, Runner `ubuntu-24.04-arm`, nativ).

| Posten | arm64 nativ (Plan 10-02) | **dieser Lauf, auf der Box** | Differenz |
|---|---:|---:|---:|
| 11a-tokenizers-modul-importiert | 4,2 MB | **4,0 MB** | minus 0,2 MB |
| 11b-erste-tokenizer-instanz | 265,2 MB | **264,9 MB** | minus 0,3 MB |
| 12a-splitter-gebaut | 273,4 MB | **273,1 MB** | minus 0,3 MB |
| 12b-erster-chunkerlauf-2 | 0,9 MB | **0,8 MB** | minus 0,1 MB |
| 12c-zweiter-chunkerlauf-2 | 0,0 MB | **0,0 MB** | 0,0 MB |
| **Summe der fünf Posten** | **543,7 MB** | **542,8 MB** | **minus 0,9 MB** |
| Grundlinie, Schritt 00 | 13,0 MB | **12,8 MB** | minus 0,2 MB |

Zwei ARM-Maschinen, die über 544 MB weniger als ein Megabyte auseinanderliegen:
das ist so nah, wie zwei Läufe desselben Vorgangs kommen. Die Rohdatei trägt die
Zeile `erwartung-fein-arm64 543,7 MB over five items, base line 13,0 MB` selbst
mit, damit die Erwartung neben der Messung steht und nicht dahinter.

Die übrigen Schritte derselben Reihe, damit die Aufschlüsselung vollständig ist:
`06-poller-importiert` plus 40,2 MB, `09-wortliste-gelesen-276496` plus
21,9 MB, `10-deutscher-automat-gebaut` plus 41,9 MB,
`14-erste-einbettung-gewichte-geladen` plus 398,7 MB,
`15-lange-einbettung-aktivierungen` plus 27,1 MB, der informative Schritt 16
(zweite Tokenizer-Instanz) plus 223,3 MB.

### 5.3 Wo der Unterschied anfällt, und wo nicht

**Ausschließlich in der Grundlast.** Er trägt nicht in die Suchphase und nicht
in die Gesamtspitze durch, und beides ist gemessen:

- **Die erste Suche kostet dieselben Gewichte wie vorher.** `anon` steigt von
  103,2 auf 518,2 MB, also um **plus 415,0 MB**, gegen plus 422,3 MB in der
  Nachmessung (`rohdaten/95-spitze-vorher.txt`).
- **Die Gesamtspitze sinkt nur um 73,6 MB**, von 1.837,8 auf 1.764,2 MB
  (`rohdaten/00-ende.txt`), obwohl die Grundlast um 588,6 MB gesunken ist. Wer
  52.111 Dokumente indexiert, bezahlt die Spitze woanders.

---

## 6. Die anon-Spitze, getrennt nach Phase, mit dem Zeitpunkt

Gerechnet über `scripts/ops/rss_digest.py` auf `rohdaten/96-volllauf.csv`, mit
Phasengrenzen aus `rohdaten/96-statusseite.jsonl` und `rohdaten/96b-waechter.txt`.
Die Grenzen sind gemessen und nicht geschätzt. `anon` und `memory.current`
stehen nebeneinander, weil der Tantivy-Index ein mmap ist und `anon` ihn nicht
zählt (`rohdaten/00-ende.txt`).

| Phase | Zeitfenster | Aufnahmen | mittel `anon` | höchster `anon` | höchster `memory.current` |
|---|---|---:|---:|---|---|
| A, Anlauf, vor der ersten semantischen Suche | 09.09. 09:58:22Z bis 10:04:29Z | 74 | 614,5 MB | 1.479,4 MB um 10:04:22Z | 1.540,7 MB um 10:04:22Z |
| B, die erste semantische Suche des Laufs | 09.09. 10:04:30Z bis 10:04:59Z | 6 | 1.574,4 MB | 1.623,0 MB um 10:04:52Z | 1.701,1 MB um 10:04:52Z |
| C, OCR, Indexierung und Einbettung gekoppelt | 09.09. 10:05:00Z bis 10.09. 12:39:56Z | 19.102 | 1.583,0 MB | **1.764,2 MB um 10.09. 08:12:24Z** | **2.048,0 MB um 09.09. 17:44:47Z** |
| D, Nachlauf, beide Spuren durch | 10.09. 12:39:57Z bis 13:05:02Z | 301 | 1.521,5 MB | 1.521,5 MB um 12:39:59Z | 1.751,5 MB um 13:05:02Z |
| **GESAMT** | | **19.483** | **1.578,4 MB** | **1.764,2 MB** | **2.048,0 MB** |

Der Vergleich, jede Zahl neben ihrer Entsprechung:

| Posten | 06-11 | Nachmessung 07.09. | 05-21 (ohne Semantik) | **dieser Lauf** | Differenz zu 06-11 |
|---|---|---|---|---|---|
| höchster `anon` des ganzen Laufs | 1.837,8 MB, 05:34:05Z | 1.812,7 MB, 05:55:53Z | 422,2 MB | **1.764,2 MB, 08:12:24Z** | **minus 73,6 MB** |
| Phase der ersten semantischen Suche | 1.837,8 MB | 1.125,2 MB | entfällt | **1.623,0 MB** | minus 214,8 MB |
| Phase mit OCR | 1.562,7 MB | 1.812,7 MB | | **1.764,2 MB** | plus 201,5 MB |
| `memory.current`-Spitze | 2.048,0 MB | 1.219,8 MB | | **2.048,0 MB** | 0,0 MB |

**Der Besitzer der Spitze hat gewechselt, und zwar in dieselbe Richtung wie in
der Nachmessung.** In 06-11 lag die Spitze in der Phase der ersten semantischen
Suche, hier liegt sie in der OCR-Phase. Die Phase der ersten Suche liegt mit
1.623,0 MB deutlich unter den 1.837,8 MB von 06-11, aber deutlich über den
1.125,2 MB der Nachmessung. Der Grund für den Unterschied zur Nachmessung steht
im Aufbau: dort lief die erste Suche auf einer ruhenden Instanz, hier fällt sie
mitten in eine laufende Indexierung.

---

## 7. Laufzeit beider Spuren, neben 06-11 und 05-21

`rohdaten/00-ende.txt`, gerechnet aus `rohdaten/96-volllauf-start.txt`,
`rohdaten/96-statusseite.jsonl` und `rohdaten/96b-waechter.txt`.

| Marke | Zeitpunkt | Quelle |
|---|---|---|
| Anstoß des Volllaufs | 2026-09-09T09:58:42Z | `rohdaten/96-volllauf-start.txt` |
| Letzte Runde mit Arbeit | 2026-09-10T12:34:57Z, Runde 319, `vorrat=31` | `rohdaten/96b-waechter.txt` |
| Erste Lesung `indexed=embedded=52111` | 2026-09-10T12:36:03Z | `rohdaten/96-statusseite.jsonl` |
| Ende beider Spuren erkannt | 2026-09-10T13:04:57Z, nach fünf stillen Runden | `rohdaten/96b-waechter.txt` |
| `00-FERTIG` geschrieben | 2026-09-10T13:05:11Z | `rohdaten/00-FERTIG` |

| Posten | 06-11 | 05-21 (ohne Semantik) | **dieser Lauf** | Differenz zu 06-11 |
|---|---|---|---|---|
| erste Spur allein (Volltext plus OCR) | 18 h 04 min | 12 h 49 min | **nicht messbar, die Spuren liefen gekoppelt** | keine Zeile |
| beide Spuren bis zum letzten Vektor | **18 h 56 min** | entfällt | **26 h 37 min 21 s** | **plus 40,6 Prozent** |
| Obergrenze, gegen die grobe Marke | | | 26 h 41 min 15 s | |
| bis `00-FERTIG` (mit 25 min Stillebestätigung) | | | 27 h 06 min 29 s | |
| Indexierung über den ganzen Lauf | 45,7 je Minute | | **31,6 je Minute** | minus 30,9 Prozent |
| Einbettung neben der OCR | rund 43 je Minute | | **32,5 je Minute** | minus 24,4 Prozent |
| Einbettung allein, nach der ersten Spur | rund 170 je Minute | | **kommt nicht vor** | entfällt |

**Warum die erste Spur allein nicht messbar ist, und das ist selbst der
Befund.** Eine Phasengrenze "Übergang der Spuren" gibt es in diesem Lauf nicht.
Die Einbettung hat ab Wächterrunde 20 zur Indexierung aufgeschlossen und ist bis
zum Ende höchstens einige hundert Dokumente zurückgeblieben: der Abstand
`indexed` minus `embedded` über alle 812 Lesungen liegt bei höchstens 1.399, im
Mittel bei 158 und am Ende bei 0.

**Der Durchsatz fällt nicht schleichend ab.** In Stundenblöcken steht er vom
09.09. 11:00Z bis 10.09. 09:00Z auf einer Geraden bei 34 je Minute (Indexierung
33,5 bis 34,6, Median 34,1; Einbettung 31,2 bis 34,2, Median 32,9). Erst die
letzten drei Blöcke fallen (30,9, dann 22,7, dann 8,5), und das ist der Auslauf.
**Speicherdruck als Erklärung ist damit ausgeschlossen**, denn der würde mit der
Zeit wachsen.

**Die Ursache der Mehrlaufzeit ist eingegrenzt, aber nicht bewiesen.** Der
Kandidat, den die Daten stützen, ist die **Kopplung der Spuren**: beide wurden
gleichzeitig und um denselben Faktor langsamer, der Durchsatz war über 22 Stunden
stabil, und ein Nachlauf mit 170 Dokumenten je Minute kommt nicht vor. Der
zweite Kandidat aus Plan 10-05, die **Zulauf-Lücken** (`vorrat=0` in 62 von 325
Lesungen), bleibt daneben stehen; er erklärt eine Wartezeit, aber nicht, warum
beide Spuren im Gleichschritt langsamer wurden. Welcher der beiden trägt,
entscheidet eine Messung, die dieser Lauf nicht vorsieht.

**Der Untergrenzen-Vorbehalt gehört an jede dieser Zahlen.** Beim Anstoß lagen
1.653 Dateien schon im Index (Abschnitt 3). Ein Lauf von null hätte länger
gebraucht, und die 26 h 37 min sind deshalb eine **Untergrenze**.

---

## 8. Die Suchlast und die Nebenläufigkeitszusage

Dies ist die p95-Hälfte von **MESS-02**. Fünf Stufen, zehn Runden je Stufe, 410
Anfragen, über die OCS-Route und damit über den finalen PHP-Recheck
(`rohdaten/97-nebenlaeufigkeit.txt`, `rohdaten/97-stufe-<n>.json`), gefahren am
10.09. zwischen 13:48:32Z und 13:52:05Z.

| Nebenläufigkeit | Anfragen | `fail` | p50 | p95 06-11 | **p95 dieser Lauf** | Differenz | max | `anon` MB | `memory.current` MB | Budget 2.500 ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 10 | 0 | 375,8 | **481,6** | **464,3** | **minus 3,6 %** | 464,3 | 1.521,5 | 1.752,3 | gehalten |
| 4 | 40 | 0 | 920,4 | 1.009,4 | **1.068,0** | **plus 5,8 %** | 1.089,5 | 1.521,5 | 1.685,9 | gehalten |
| 8 | 80 | 0 | 1.803,9 | **1.915,0** | **2.125,5** | **plus 11,0 %** | 2.202,1 | 1.521,5 | 1.663,2 | gehalten |
| 12 | 120 | 0 | 2.758,3 | 3.045,4 | **3.453,4** | **plus 13,4 %** | 3.619,6 | 1.521,5 | 1.609,5 | gerissen |
| 16 | 160 | 0 | 4.045,3 | 3.782,7 | **4.446,2** | **plus 17,5 %** | 4.507,0 | 1.521,8 | 1.631,7 | gerissen |

Zum Vergleich die zwei Suchlastproben aus 06-11, die nicht in dieser Reihe
liegen, aber dieselbe Route messen: im Nachlauf bei laufender zweiter Spur p95
**1.129,0 ms**, nach dem Lauf auf vollem Vektorbestand p95 **524,0 ms**
(`docs/measurements/2026-09-05-semantiklauf-m7g/README.md`, Abschnitt "Die Suche
bleibt benutzbar"). Die Entsprechung dieses Laufs auf demselben Weg steht in
`rohdaten/96-suchlast-nachlauf.json` und `rohdaten/96-suchlast-danach.json`.

### 8.1 Die Zusage, die daraus folgt

**Die Zusage steht weiter auf Stufe 8, und sie wird nicht gesetzt, sondern aus
der Reihe abgelesen.** 2.125,5 ms sind **85,0 Prozent** des Budgets von
2.500 ms, gegen 76,6 Prozent in der Grundlinie. **Die Reserve schrumpft von
585,0 auf 374,5 ms.** Stufe 12 reißt das Budget mit 3.453,4 ms, wie schon in
06-11 mit 3.045,4 ms.

**Der Vorbehalt, der dazugehört:** die Unified Search fragt alle Provider
gleichzeitig. Die Zusage "acht gleichzeitige Suchende" beschreibt deshalb nicht
nur diese App, sondern auch den PHP-Prozesspool der Instanz, der bei acht
parallelen Unified-Search-Anfragen mehr als acht Prozesse beschäftigt. Eine
Instanz mit knappem Pool erreicht die Zusage nicht, und das liegt dann nicht an
dieser Messung.

### 8.2 `anon` und `memory.current` je Stufe

`anon` steht über alle fünf Stufen bei 1.521,5 bis 1.521,8 MB und **wächst mit
der Nebenläufigkeit nicht**. `memory.current` fällt von 1.752,3 auf 1.631,7 MB,
weil der Kernel den Dateicache unter Last zurückdrängt. Der Abstand zwischen
beiden liegt bei 110 bis 231 MB, in derselben Größenordnung wie die rund 86 MB
der Nachmessung. `memory.events` steht vor der Reihe und nach jeder Stufe
unverändert auf `max 21939` und `sock_throttled 1997`; die Reihe hat den Zähler
nicht bewegt.

### 8.3 Ein Werkzeugbefund, der diese Reihe betrifft

Stufe 16 dieser Reihe trägt **17 abgebrochene Containeraufrufe bei gemeldeten
`failures: 0`**. Der Befund ist bei der Kaltstart-Reproduktion abgefallen und
steht in Abschnitt 9.3; er ist hier genannt, damit niemand die 4.446,2 ms der
Stufe 16 liest, ohne ihn zu kennen. **Die Stufen 1 bis 12 sind davon nicht
berührt, und die Zusage steht auf Stufe 8.**

---

## 9. Die erste Suche nach einem Containerstart, unter Nebenläufigkeit

Dies ist **DI-07-02**. **ERSTMESSUNG auf vollem Vektorbestand:** weder 06-11
noch die Nachmessung hat den Kaltstart auf einer Instanz mit 146.171 Vektoren
gemessen. Der Vorwert aus Plan 07-01 stammt von einem **leeren** Bestand und
steht deshalb als Einordnung da, nicht als Vergleichszeile.

### 9.1 Die gemessene Reihe

| Größe | Vorwert | **dieser Lauf** | Rohdatei |
|---|---|---|---|
| Kaltstart über OCS, eine Anfrage, **leerer** Bestand, 09.09. | **1.332,1 ms** (Plan 07-01) | **1.550,4 ms**, Marge minus 50,4 ms | `rohdaten/95-spitze-vorher.txt` |
| Kaltstart über OCS, eine Anfrage, **voller** Bestand, 10.09. 14:05:17Z | | **1.838,4 ms**, Marge minus 338,4 ms | `rohdaten/95-spitze-nachher.txt` |
| Abstand zum Vorwert 07-01 | | 506,3 ms | `rohdaten/95-spitze-nachher.txt` |

Die drei Reproduktionsdurchgänge des 10.09., je mit einem eigenen Neustart
(`rohdaten/95b-kaltstart-reproduktion.txt`,
`rohdaten/95c-kaltstart-reproduktion-teil2.txt`):

| Durchgang | Begriff | Kaltstart | Marge zu 1,5 s | Treffer | warm danach |
|---|---|---:|---:|---:|---|
| 1 | Bescheid | 1.598 ms | minus 98 ms | **6** | 560 bis 566 ms |
| 2 | Vertrag beenden | 1.805 ms | minus 305 ms | **6** | 662 bis 674 ms |
| 3 | Kuendigung | 2.468 ms | minus 968 ms | **6** | 553 bis 565 ms |

### 9.2 Die Methodik-Korrektur, ohne die keine dieser Zahlen richtig gelesen wird

**Die gemessenen Dauern sind die Dauer der ganzen OCS-Anfrage. Die Decke von
1.501 ms gilt nur für den inneren Containeraufruf.** Diese Unterscheidung fehlte
allen bisherigen Kaltstartzahlen dieses Projekts, und sie gehört als Korrektur
in den Bericht und nicht in eine Fußnote.

Daraus folgt zweierlei:

- **Eine Gesamtdauer über 1,5 s beweist keinen Abbruch.** Die drei
  Reproduktionsdurchgänge liegen bei 1.598 bis 2.468 ms und liefern **je sechs
  Treffer**. Der innere Aufruf blieb unter der Decke, weil der Seitencache des
  Wirts die Modellgewichte der vorigen Starts noch hielt.
- **Eine Gesamtdauer unter 1,5 s beweist auch nicht das Gegenteil.**

**Die eine Null-Treffer-Anfrage ist trotzdem belegt, und zwar im
Nextcloud-Protokoll.** Um `2026-09-10T14:05:17Z`, dem Zeitpunkt der
Kaltstartmessung, mit dem Begriff `Vertrag beenden`, den `search_load.py` bei
einer Runde als `TERMS[0]` stellt, steht dort:

```
app_api:  cURL error 28: Operation timed out after 1501 milliseconds
          with 0 bytes received ... /exapps/findling_backend/search
findling: Findling: backend unreachable
```

Um 14:05:17Z lag der letzte Containerstart 29 Stunden zurück, der Seitencache
war kalt. **Der Abbruch ist also real, und er ist reproduzierbar nur bei kaltem
Wirtscache.** Die Reproduktion mit warmem Cache widerlegt ihn nicht, sie grenzt
ihn ein.

### 9.3 Der Befund, der bei dieser Reproduktion abgefallen ist, und er ist der größere

Dasselbe Protokoll zählt zwischen `13:51:11Z` und `13:51:42Z` **siebzehn
abgebrochene Containeraufrufe**. Dieses Fenster ist **Stufe 16 der
Nebenläufigkeitsreihe** (13:50:59Z bis 13:51:42Z), und
`rohdaten/97-stufe-16.json` meldet `"failures": 0` für 160 Anfragen. Die Route
antwortet bei einem abgebrochenen Containeraufruf mit HTTP 200 und einer
Ergebnisgruppe ohne Containerteil, also zählt das Lastwerkzeug sie als
beantwortet.

Der Fingerabdruck steht in den Trefferzahlen:

| Stufe | Anfragen | `failures` | Treffer | Treffer je Anfrage | Abbrüche im Fenster |
|---:|---:|---:|---:|---:|---:|
| 1 | 10 | 0 | 54 | 5,40 | 0 |
| 4 | 40 | 0 | 216 | 5,40 | 0 |
| 8 | 80 | 0 | 420 | 5,25 | 0 |
| 12 | 120 | 0 | 577 | 4,81 | 0 |
| 16 | 160 | 0 | 666 | **4,16** | **17** |

**Für 10,6 Prozent der Anfragen der Stufe 16 hat die gemessene Antwortzeit nicht
die Zeit einer vollständigen Antwort gemessen.** Die 4.446,2 ms der Stufe 16
sind damit eher zu günstig als zu schlecht. **Dies ist ein Befund über das
Messwerkzeug und nicht über das Erzeugnis**, und er ist als DI-10-01 in
`.planning/phases/10-vergleichsmessung-auf-der-aws-box/deferred-items.md`
festgehalten. Die Stufen 1 bis 12 tragen keine Abbrüche, die Zusage auf Stufe 8
steht.

### 9.4 Was daraus für DI-07-02 folgt

Der Befund wird **nicht** in diesem Bericht entschieden. Die Marge ist auf
vollem Bestand negativ (minus 338,4 ms an der Gesamtdauer), der Abbruch ist bei
kaltem Wirtscache belegt, und eine höhere Decke lässt jeden Nutzer bei jeder
Suche länger warten, weil die Unified Search auf jeden Provider wartet. **Der
Befund geht mit seinen Zahlen an Phase 11**, und die Übergabe steht in
`.planning/phases/07-gemeinsame-embedding-engine/deferred-items.md`.

---

## 10. Wie oft der Rechteabgleich mehr als eine Runde dreht

Dies ist **DI-07-03**. **ERSTMESSUNG:** die Rundenzählung ist in keinem der
beiden Vorläuferberichte gefahren worden.

| Fall | Runden je Suche | Containeraufrufe je Suche | Treffer | p50 | p95 | Budget 2.500 ms | Rohdatei |
|---|---:|---:|---:|---:|---:|---|---|
| 1, der Alltag | **1,0** | **1,9** (10 Kandidaten-, 9 Snippetaufrufe) | 54 | 589,4 ms | **683,6 ms** | Marge 1.816,4 ms | `rohdaten/99b-runden-alltag.txt` |
| 2, provozierter Driftfall | 1,0 | 1,0 (10 Kandidaten-, 0 Snippetaufrufe) | 0 | 444,2 ms | 681,6 ms | Marge 1.818,4 ms | `rohdaten/99b-runden-drift.txt` |

### 10.1 Wie Fall 1 hergestellt wurde

Das Konto, das **alle** Dateien besitzt, zehn Suchen, 40 geteilte Dateien. Der
Recheck entfernt nichts, die Schleife über `MAX_ROUNDS = 3` dreht genau eine
Runde. Gezählt wurden die Containeraufrufe im Protokoll (`POST /search` und
`POST /snippets`), nicht ein abgelesener Zustand. Die Berechtigungskette wurde
dabei nicht angefasst: keine Zeile in `Provider.php`, kein zweiter Recheck, kein
Weg um den Vorfilter herum.

### 10.2 Wie Fall 2 hergestellt wurde, und warum seine Zahl nicht trägt

Ein eigenes Konto `driftfall` wurde angelegt, 20 Freigaben wurden gesetzt, zwei
gezählte Poller-Durchgänge abgewartet, die Kontrolle vor der Rücknahme lieferte
**vier Treffer** (`rechte-aufgenommen ja`). Dann wurden die Freigaben um
14:14:14Z zurückgenommen, **ohne dem Poller Zeit zu geben**, und sofort gefragt.

Das Skript liest das Ergebnis **dreiwertig**, und es schreibt die drei Lesarten
selbst in die Rohdatei:

- Treffer > 0 nach der Rücknahme: der Recheck hat nicht entfernt, die Freigabe
  war noch wirksam, **dies ist nicht der Driftfall**.
- Treffer = 0 **und** mehr als eine Runde je Suche: **der Driftfall ist
  erzeugt**.
- Treffer = 0 **und** eine Runde je Suche: der Vorfilter wusste schon Bescheid,
  die Drift war zu kurz, **und die Zahl ist keine Aussage über die Schleife**.

Gemessen wurde der dritte Fall. **Der Driftfall wurde also nicht erzeugt. Die
Alltagszahl trägt, die Driftzahl nicht.** Eine Zahl aus einem provozierten
Zustand als Alltagszahl zu berichten wäre schlimmer als keine Zahl.

### 10.3 Was die Rundenzahl 1,0 an anderer Stelle bedeutet

Sie ist die zweite Hälfte des Befundes aus Abschnitt 12: **die Schleife holt
keine zweite Runde nach, auch dann nicht, wenn der Recheck alle Kandidaten der
ersten Runde verworfen hat.** Ein Nutzer mit wenigen Dateien neben einem großen
Fremdbestand bekommt dann eine leere Liste statt seiner Datei.

---

## 11. Die Ergebnisseite auf der Zielhardware, gegen 2026-09-seitenbudget

**ERSTMESSUNG und keine Vergleichszeile.** Der Seitenbudget-Bericht vom
06.09.2026 hat auf einer Instanz **ohne** `vectors.db` gemessen. Die Folge ist
im Code sichtbar: `one_round()` prüft `side.vectors is not None`, und ohne
Vektorspeicher fällt der teuerste Teil des Vorfilters ersatzlos weg. Diese
Instanz hat einen Vektorbestand, also misst diese Reihe eine andere Sache
(`rohdaten/99-seitenroute.txt`, vier Reihen à 20 Wiederholungen plus 5
Aufwärmanfragen, Rangregel ohne Interpolation, Begriff `Bescheid+Antrag`).

| Reihe | Anmeldeweg | min | p50 | **p95** | max | Vorwert ohne Vektoren | Decke 1,5 s | Budget 3,0 s |
|---|---|---:|---:|---:|---:|---:|---|---|
| A, erste Seite | Sitzung | 0,324 s | 0,328 s | **0,332 s** | 0,445 s | **0,122 s** | Marge 1,168 s | Marge 2,668 s |
| B, erste Seite | Basic-Auth | 0,750 s | 0,763 s | **0,775 s** | 0,780 s | 0,445 s | Marge 0,725 s | Marge 2,225 s |
| C, tiefe Seite (Seite 3) | Sitzung | 0,326 s | 0,329 s | **0,333 s** | 0,338 s | **0,122 s** | Marge 1,167 s | Marge 2,667 s |
| D, Dialogweg, `limit=100` | Basic-Auth | 0,734 s | 0,747 s | **0,769 s** | 0,825 s | 0,538 s | Marge 0,731 s | Marge 2,231 s |

Alle 80 Anfragen kamen mit HTTP 200 zurück. **Kein Ausreißer wurde entfernt.**
Das höchste Maximum steht bei Reihe D mit 0,825 s, das auffälligste bei Reihe A
mit 0,445 s gegen einen p95 von 0,332 s.

**Der Preis des Anmeldewegs, Differenz A gegen B am p95: 0,443 s.** Auf der
Vergleichsinstanz waren es 0,318 s. Kein angemeldeter Nutzer bezahlt ihn; er
gehört der Passwortprüfung von Basic-Auth und nicht der Seite.

**Eine Ungenauigkeit in der Kopfzeile der Rohdatei, die hier korrigiert wird.**
`99-seitenroute.txt` schreibt "diese Instanz HAT eine vectors.db mit 145.854
Vektoren". **145.854** ist die Chunk-Zahl aus 06-11; diese Instanz trägt
**146.171** Chunks (`rohdaten/48-vektorbestand.txt`). Die Aussage der Kopfzeile
bleibt richtig, die Zahl darin ist aus dem Vorlauf übernommen. Die Rohdatei
bleibt unverändert, und die Korrektur steht hier.

### 11.1 Die Entscheidung über T-09-29

T-09-29 aus Phase 9 (DoS, voller Vektorscan je Anzeigeseite) wurde mit
`accept` geschlossen, und die Begründung lautete, dass die Zahlen fehlen. **Sie
liegen jetzt vor, und die Begründung hält, aber aus einem anderen Grund als
damals angenommen.**

- Die tiefe Seite (Reihe C, Seite 3) kostet **0,333 s** und damit praktisch
  dasselbe wie die erste Seite (Reihe A, 0,332 s). **Die Seitentiefe kostet
  nichts**, weil der Vektorscan einmal je Anfrage läuft und nicht je Seite.
- Der Dialogweg mit `limit=100` kostet **0,769 s** gegen 0,775 s der ersten
  Seite auf demselben Anmeldeweg. **Auch die Trefferzahl kostet nichts
  Nennenswertes.**
- Der Abstand zur Aufrufdecke von 1,5 s beträgt im schlechtesten Fall
  **0,725 s**, der zum Seitenbudget von 3,0 s **2,225 s**.

**Entscheidung: `accept` bleibt, jetzt mit Zahlen statt mit ihrer Abwesenheit.**
Der Vektorscan über 146.171 Chunks kostet auf dieser Hardware rund 0,21 s
gegenüber einer Instanz ohne Vektoren, und er skaliert nicht mit der
Seitentiefe. Der Auditbericht dieser Phase trägt die Entscheidung mit derselben
Begründung.

---

## 12. Die zehn deutschen Sprachfälle, auf der Box

Dies ist die zweite Hälfte von **MESS-02**. **ERSTMESSUNG mit
Mess-Setup-Vorbehalt:** für diese zehn Fälle gibt es **keine v1.0-Entsprechung
auf dieser Box**. Weder der Semantiklauf vom 05.09. noch die Nachmessung vom
07.09. hat sie gefahren.

### 12.1 Die Bilanz, wie sie gemessen wurde

**`sprachfaelle bestanden 6 von 10`, vier rote Fälle, neun rote Zusicherungen**
(`rohdaten/98-sprachfaelle.txt`).

| Fall | Was die Zusicherung verlangt | Was geschah |
|---|---|---|
| 1 | ein Kompositum über einen seiner Bestandteile gesucht bringt genau eine Datei | leere Trefferliste, vier Zusicherungen rot |
| 2 | `Frist` bringt genau die Kündigung zurück | leere Trefferliste, zwei Zusicherungen rot |
| 4 | der Singular findet den Plural | leere Trefferliste, zwei Zusicherungen rot |
| 6 | das Wort, das in zwei Dateien steht, bringt zwei Dateien | genau eine Datei, `09-bescheid.pdf` |

**Der Befund ist reproduziert und kein Messfehler.** Er wurde zweimal gefahren,
um Fallstrick 11 auszuschließen: Erstlauf 14:19:12Z bis 14:25:37Z
(`rohdaten/98-sprachfaelle-erstlauf.txt`), Wiederholung 14:35:02Z bis 14:41:27Z
(`rohdaten/98-sprachfaelle.txt`). Beide Läufe kommen auf dieselben 6 von 10,
dieselben vier Fälle, dieselben neun Zusicherungen. Der Erstlauf ist nicht
überschrieben worden.

**Der zweite Beleg, den das Skript nicht selbst feststellen konnte.** Die
Rohdatei schreibt `ci-beleg: der letzte gruene integration.yml-Lauf ist
unbekannt`. Nachgetragen: der letzte grüne Lauf von `integration.yml` vor dieser
Messung ist **Lauf 34339346666** auf `main`, Commit
`0dd007d3b20c1185e93b38d4e071e4ec086f2ea2`, abgeschlossen am
2026-09-09T10:16:38Z. Er misst dieselben zehn Fälle grün, aber auf amd64 gegen
eine frische Instanz mit dem PHP-Entwicklungsserver; hier laufen sie auf arm64
gegen eine All-in-One-Instanz mit vollem Vektorbestand. **Gleich ist die
Aussage, nicht die Umgebung.**

### 12.2 Die Diagnose, und sie ändert die Deutung dieser Bilanz grundlegend

Der Owner hat am 10.09. entschieden, die roten Befunde nachzumessen, solange die
Box läuft. Das Ergebnis steht in `rohdaten/98b-sprachfaelle-diagnose.txt`.

**Die deutsche Analysekette tut, was sie soll, und das ist gemessen.**
`Grundstücksverkehrsgenehmigung` wird zu `grundstuck`, `verkehr`, `genehm`, die
Anfrage `Genehmigung` wird zu `genehm`, und beide teilen dieses Token. Dasselbe
gilt für `Kündigungsfrist` gegen `Frist` und für `Verträge` gegen `Vertrag`.
Alle drei Tokens stehen im Feld `body_de` des Index mit Dokumenten daran, und
jede der vier Suchen liefert **im Index** zehn Treffer.

**Die Dateien liegen nachweislich im Index.** Der Referenzkorpus des
Sprachfall-Kontos ist vollständig verarbeitet: 26 indexiert, 7 übersprungen, 6
fehlgeschlagen, zusammen die 39 hochgeladenen Dateien. Die drei Dateien der
Fälle 1, 2 und 4 stehen als `indexed` in `state.db`, mit 123, 148 und 132
Zeichen. Die sechs Fehlschläge sind die absichtlich kaputten Dateien des Korpus
(Nullbytes, abgeschnittener Trailer, Seitenbaum-Zyklus und drei weitere), also
erwartete Fälle.

**Der Grund ist die Kandidatenliste, und der Messaufbau hat ihn erzeugt.** Die
zehn Treffer gehören samt und sonders dem Lasttest-Konto mit seinen 52.111
Dokumenten und keiner dem Konto, das gefragt hat. Für `Genehmigung`, `Frist` und
`Vertrag` kommt unter den ersten **zweitausend** Kandidaten keine einzige Datei
des fragenden Kontos vor; für `Bescheid` steht sie auf **Rang 1.925 von 2.000**.
Der Vorfilter rankt über den ganzen Index, der Recheck filtert erst danach auf
das Erlaubte, und dann ist nichts mehr übrig. Die sechs grünen Fälle sind genau
die, deren Begriffe im Lastkorpus selten sind: `Mueller` hat im ganzen Index
einen einzigen Treffer, und das ist die eigene Datei.

**Es ist also kein Sprachdefekt.** Das ist Fallstrick 3 in einer Form, die der
Skriptkopf nicht abdeckt: er führt den eigenen Nutzer ein, weil der Lastkorpus
dieselben Wörter trägt, aber **ein eigener Nutzer trennt die Berechtigung und
nicht den Index**. Der 52.111er-Lastkorpus trägt dieselben Tokens tausendfach.

### 12.3 Was trotzdem ein Befund über das Erzeugnis ist

Auf einer Instanz mit großem Fremdbestand findet ein Nutzer mit wenigen Dateien
seine eigenen nicht, sobald seine Begriffe im Fremdbestand häufig sind, und er
bekommt dabei keine Fehlermeldung, sondern eine leere Liste. Die Rundenzählung
aus Abschnitt 10 zeigt, dass die Schleife keine zweite Runde nachholt (1,0 Runde
je Suche), obwohl der Recheck alle Kandidaten der ersten verworfen hat. **Dieser
Befund gehört zu DI-07-03 und ist an Phase 11 übergeben.**

**Die Bilanz 6 von 10 bleibt stehen, weil sie gemessen ist. Sie ist aber keine
Aussage über die Sprachverarbeitung von v1.1 und wird in diesem Bericht nicht
als eine geführt.**

---

## 13. `memory.events`, vollständig, an jeder Ablesestelle

Die Liste der Ablesestellen steht in `skripte/00-ablauf.md`, Abschnitt 3. **Alle
vierzehn sind gefahren worden.** An jeder wird **vor** dem Eingriff gelesen, der
an der Stelle stattfindet; wer nach dem Aufräumen liest, misst das Aufräumen und
nicht den Lauf.

| Nr | Ablesestelle | Zeitpunkt | `max` | `oom` / `oom_kill` / `oom_group_kill` | `sock_throttled` | Rohdatei |
|---:|---|---|---:|---|---:|---|
| 1 | vor jedem Eingriff, als Nullpunkt | 09.09. 09:26:49Z | 0 | 0 / 0 / 0 | 0 | `rohdaten/90-bestand.txt` |
| 2 | nach Registrierung und harter Grenze | 09.09. 09:32Z | 0 | 0 / 0 / 0 | 0 | `rohdaten/92-wechsel.txt` |
| 3 | vor `findling:index --restart` | 09.09. 09:37Z | 0 | 0 / 0 / 0 | 0 | `rohdaten/93-nullstand.txt` |
| 4 | vor Teil A der Grundlast | 09.09. 09:42:02Z | 0 | 0 / 0 / 0 | 0 | `rohdaten/94-grundlast.txt` |
| 5 | nach Teil B, C und D | 09.09. 09:42:14Z | 0 | 0 / 0 / 0 | 0 | `rohdaten/94-grundlast.txt` |
| 6 | vor der ersten Suche, Rolle `vorher` | 09.09. 09:43:39Z | 0 | 0 / 0 / 0 | 0 | `rohdaten/95-spitze-vorher.txt` |
| 7 | nach der ersten Suche und je Stufe, Rolle `vorher` | 09.09. 09:43:47Z bis 09:44Z | 0 | 0 / 0 / 0 | 0 | `rohdaten/95-spitze-vorher.txt` |
| 8 | vor dem Anstoß des Volllaufs | 09.09. 09:58Z | 0 | 0 / 0 / 0 | 0 | `rohdaten/96-volllauf-start.txt` |
| 9 | Übergang der Spuren und nach der Suchlastprobe im Nachlauf | 09./10.09. | siehe Datei | 0 / 0 / 0 | siehe Datei | `rohdaten/96b-waechter.txt` |
| 10 | Ende beider Spuren, **vor jedem Eingriff** | 10.09. 13:04:57Z | **21.939** | **0 / 0 / 0** | 1.997 | `rohdaten/96-oom-beweis.txt`, `rohdaten/07-oom-beweis.txt` |
| 11 | vor der Nebenläufigkeitsreihe und nach jeder ihrer fünf Stufen | 10.09. 13:48:32Z bis 13:52:05Z | 21.939 (unverändert über alle sechs Lesungen) | 0 / 0 / 0 | 1.997 | `rohdaten/97-nebenlaeufigkeit.txt` |
| 12 | vor der ersten Suche, Rolle `nachher`, nach dem bewussten Neustart | 10.09. 14:04:39Z | **0** | 0 / 0 / 0 | 0 | `rohdaten/95-spitze-nachher.txt` |
| 13 | Ende des Wächters, nach den Nachlaufschritten | 10.09. 13:05:11Z | 21.939 | 0 / 0 / 0 | 1.997 | `rohdaten/96-oom-beweis.txt`, `rohdaten/07-oom-beweis.txt` |
| 14 | nach den vier Messblöcken des 10.09. | 10.09. 14:46:22Z | **0** | 0 / 0 / 0 | 0 | `rohdaten/07-oom-beweis.txt` |

Zwei Lesarten dieser Tabelle, die der Bericht ausdrücklich trennt:

- **`max` steht während des ganzen Indexaufbaus auf 21.939 und danach auf 0.**
  Der Zähler wird von einem Containerneustart zurückgesetzt; die 0 an Stelle 12
  und 14 ist deshalb kein Beweis dafür, dass der Suchbetrieb den Kernel nicht
  belastet, sondern dafür, dass er es zwischen 14:04:39Z und 14:46:22Z nicht
  getan hat. Diese 42 Minuten enthalten alle vier Messblöcke des 10.09.
- **`memory.peak` an Stelle 14 steht bei 1.889.603.584 Byte**, also 258 MB unter
  der harten Grenze, obwohl er während des Indexaufbaus exakt an ihr lag.

---

## 14. Byte je Dokument, gemessen gegen gerechnet

`rohdaten/48-vektorbestand.txt` und `rohdaten/96-vektorbestand.txt`, gelesen bei
leerem Arbeitsvorrat, **vor** jedem Neustart und vor jedem Abbau.

| Größe | 06-11 | **dieser Lauf** | Differenz |
|---|---:|---:|---:|
| indexiert / übersprungen / fehlgeschlagen | **51.961** / 37 / 0 | **52.111** / 37 / 0 | plus 150 / 0 / 0 |
| Chunks | **145.854** | **146.171** | plus 317 |
| Chunks je Dokument | 2,807 | **2,805** | minus 0,002 |
| `vectors.db` plus WAL | 68.642.504 Byte | **68.695.896 Byte** | plus 53.392 Byte |
| Byte je Dokument (Vektorspeicher) | **1.321,0** | **1.318,3** | minus 2,7 |
| Tantivy-Index | 785.308.851 Byte | **786.506.160 Byte** | plus 1.197.309 Byte |
| Byte je Dokument (Tantivy) | **15.113** | **15.093** | minus 20 |
| Vektoranteil am Tantivy | 8,74 Prozent | **8,73 Prozent** | minus 0,01 |
| Zeichen im Korpus | 1.397.354.875 | **1.397.874.090** | plus 519.215 |
| `state.db` | | 16.330.752 Byte | |
| Wörterbuch (`dict`) | | 3.284.251 Byte | |

**Gerechnet gegen gemessen, und die Rechnung steht als Rechnung da.** Aus den
beiden gemessenen Zahlen 68.695.896 Byte und 146.171 Chunks folgt **470,0 Byte
je Chunk**; aus 786.506.160 Byte und 1.397.874.090 Zeichen folgt **0,563 Byte
Tantivy je Zeichen**. Beide Quotienten sind hier gerechnet und nicht gemessen,
und beide liegen innerhalb eines Promille neben denselben Quotienten aus 06-11
(469,9 Byte je Chunk, 0,562 Byte je Zeichen). **Der Speicherbedarf je Dokument
hat sich zwischen v1.0 und diesem Stand nicht verändert.**

---

## 15. Verdikte und der Endungsvergleich als Gegenprobe

### 15.1 Der Endungsvergleich

**Er stimmt in beiden Hälften überein:** 13 Endungen, Generator gleich Bestand,
**genau eine benannte Abweichung**, nämlich 20 `csv` mit `skipped:too_large` aus
der Kategorie `oversize` (`rohdaten/66-generator-endungen.json`, lokal aus dem
Samen gerechnet, gegen `rohdaten/68-bestand-endungen.json`, über `state.db` auf
der Box).

### 15.2 Der Verdikt-Versatz plus 34 aus Plan 10-05, vollständig aufgeklärt

`rohdaten/48-vektorbestand.txt`, Teil 4. `state.db` führt **52.148 Zeilen** auf
zwei Speichern: 52.099 im Baum des Lasttest-Kontos und 49 in einem zweiten
Speicher, dem Willkommenspaket eines zweiten Kontos, das der Dateizähler von
Plan 10-05 nicht durchlaufen hat.

Im Lasttest-Baum liegen 64 Skelettdateien, davon tragen 49 ein Verdikt; die
übrigen 15 sind 10 `.whiteboard`, 4 `.odg` und 1 `.mp4`, also Endungen, die
nicht eingereiht werden.

**Die Rechnung: 52.114 minus 15 plus 49 ergibt 52.148, und der Versatz plus 34
ist genau 49 minus 15.** Der Versatz ist in beiden Läufen derselbe und keine
Änderung dieses Stands.

### 15.3 Die exakte Klärung von 52.111 gegen 51.961

52.111 minus 150 ergibt 51.961, also genau den Bestand aus 06-11. Die 150
zusätzlichen Dateien sind der Drill-Ordner vom 07.09., der auf der Box liegen
geblieben ist. Der Korpus selbst ist unverändert (Abschnitt 2), der Bestand ist
es um diese 150 Dateien nicht. **Der Mehrbestand von 0,29 Prozent erklärt die
40,6 Prozent Mehrlaufzeit aus Abschnitt 7 nicht.**

Der Bestand gegen die Zahl des Dateizählers: 52.111 indexiert plus 37
übersprungen gleich 52.148 Verdikte, und das ist genau die Zeilenzahl aus
Abschnitt 15.2. Die beiden Wege kommen auf dieselbe Zahl.

---

## 16. Was nicht abgedeckt ist

Dieser Abschnitt ist keine Entschuldigung, sondern eine Liste. Jeder Punkt
nennt, wohin er gehört.

1. **Die Aktivierungsspitze der Einbettung als eigene Zahl** (A5 der Phase 6).
   Teil B von `rohdaten/94-grundlast.txt` misst `aktivierungen_kb 486460` in
   einem Prozess, der nur die Gewichte hält. Was eine lange Einbettung neben
   einer laufenden OCR unter Speicherdruck kostet, ist in diesem Lauf nicht
   getrennt gemessen. Gehört zu einer Messung mit Instrumentierung im Container.
2. **Die amd64-Entsprechung dieses Laufs.** Alle Zahlen dieses Berichts sind
   arm64-Zahlen. Ein amd64-Volllauf über denselben Korpus existiert nicht und
   ist auch nicht geplant.
3. **Die erste Spur allein.** Nicht messbar, weil die Spuren gekoppelt liefen
   (Abschnitt 7). Eine getrennte Messung braucht einen Lauf, der die Einbettung
   erst nach der Indexierung anstößt.
4. **Welcher der beiden Kandidaten die Mehrlaufzeit trägt** (Kopplung der Spuren
   gegen Zulauf-Lücken). Abschnitt 7 grenzt ein, entscheidet aber nicht.
5. **Die Sprachfälle gegen einen Korpus ohne Fremdbestand.** Der Messaufbau hat
   den Befund erzeugt (Abschnitt 12). Eine Messung, die die Sprachverarbeitung
   auf dieser Box wirklich prüft, braucht ein Konto, dessen Begriffe im
   Fremdbestand selten sind, oder eine Instanz ohne Lastkorpus.
6. **Der provozierte Driftfall.** Nicht erzeugbar in der gefahrenen Form
   (Abschnitt 10.2). DI-07-03 bekommt damit nur eine seiner zwei Zahlen
   belastbar.
7. **Die wahre Zahl der Fehlschläge der Stufe 16.** Bekannt sind 17 Abbrüche im
   Protokollfenster; ob jede davon genau einer Anfrage entspricht, ist nicht
   nachgemessen (Abschnitt 9.3).
8. **Der Kaltstart bei kaltem Wirtscache, als Reihe.** Es gibt genau **eine**
   solche Messung (14:05:17Z). Die drei Reproduktionen liefen mit warmem Cache.
9. **Der Abbau der Box.** Der Owner hat am 10.09. auf "nur anhalten" entschieden
   (Abschnitt 17). Der Abbau braucht einen eigenen Plan in Phase 11.
10. **Der Nachzug der Zahlen in `README.md` und `docs/store-listing.md`.** Nach
    außen sichtbarer Text, Kurztext-Regel, geht als Entwurf an den Owner. Gehört
    mit der Store-Text-Abnahme in Phase 11 (REL-01).

---

## 17. Kosten und Verbleib der Box

Dies ist **Kriterium 4** (`rohdaten/93-kosten-und-verbleib.txt`, abgefragt über
`scripts/ops/aws_box.sh status`).

| Größe | Wert | Quelle |
|---|---|---|
| Instanz | `i-06b1d913f5c6f669b`, `m7g.large`, `eu-central-1c` | `aws_box.sh status` |
| Datenträger | `vol-0f3bea6ca1dab68ab` 40 G gp3, `vol-04c5b59fe9417babd` 60 G gp3 | dieselbe |
| Box angefahren | **2026-09-09T09:19:50Z** | `rohdaten/89-anfahrt.txt` |
| Stand der Abrechnung in diesem Bericht | 2026-09-10T15:52Z | `rohdaten/93-kosten-und-verbleib.txt` |
| Laufzeit bis dahin | **30,4 Stunden** | dieselbe |
| Kosten bis dahin | **3,53 USD netto** | dieselbe, aus der API |
| Satz laufend | 0,115841 USD je Stunde (0,097800 Box, 0,013041 Speicher, 0,005000 Adresse) | `aws_box.sh prices` |
| **Abfragedatum der Preise** | **2026-09-04**, seither gepinnt | dieselbe |
| Satz angehalten | 0,3130 USD je Tag | `box.env`, `BOX_PARKED_COST_USD_PER_DAY` |
| Kostendeckel, ursprünglich | **30 Stunden und 3,50 USD**, Owner-Freigabe 09.09. | `rohdaten/89-anfahrt.txt` |
| Kostendeckel, angehoben | **34 Stunden und 4,00 USD**, Owner am 2026-09-10, greift 2026-09-10T19:20Z | `rohdaten/93-kosten-und-verbleib.txt` |

**Der ursprüngliche Deckel ist gerissen**, und zwar am 2026-09-10 um 15:20Z. Der
Owner hat ihn vor Beginn der Nachmessungen auf 34 Stunden und 4,00 USD
angehoben.

**Wo die Zeit hingegangen ist:** nicht in die Messungen, sondern in den
Indexaufbau. Der Volllauf brauchte 26 h 37 min statt der erwarteten rund
19 Stunden, also 7 h 37 min mehr als geplant. Die Anfahrt und die Messungen vor
dem Lauf kosteten 38 Minuten, alle Messungen nach dem Lauf einschließlich der
beiden vom Owner entschiedenen Nachmessungen rund 2 h 50 min. **Der Deckel ist
an der Laufzeit des Indexaufbaus gerissen, und die ist selbst einer der Befunde
dieses Berichts (Abschnitt 19, Punkt 2).**

### 17.1 Der Verbleib, nach dem Entscheid des Owners vom 2026-09-10

| Frage | Antwort des Owners, wörtlich | Datum |
|---|---|---|
| Abbau der Box | "NUR ANHALTEN, kein Abbau (0,3130 USD/Tag geparkt akzeptiert). Abbau ist ein eigener Entscheid in Phase 11." | 2026-09-10 |
| Zeitpunkt des Anhaltens | "die Box LAEUFT WEITER BIS ZUR BERICHTSABNAHME (10-07)." | 2026-09-10 |

**Der Stoppzeitpunkt der Box.** Der Owner hat den Bericht am **2026-09-10**
abgenommen; danach ist `scripts/ops/aws_box.sh stop` gefahren worden, und nicht
`aws ec2 stop-instances`, weil nur der Unterbefehl Zeitpunkt, Laufzeit und
Kosten in die Zustandsdatei schreibt.

| Größe | Wert |
|---|---|
| `BOX_STOPPED_ISO` | **2026-09-10T16:22:50Z** |
| `BOX_LAST_UPTIME_HOURS` | **31.05** |
| `BOX_LAST_UPTIME_COST_USD` | **3.5969** |
| `BOX_PARKED_COST_USD_PER_DAY` | 0,3130, gilt unverändert |

**Die Feststellung des gestoppten Zustands stammt aus der API und nicht aus der
Erinnerung:** abgefragt um **2026-09-10T16:23:15Z** über `aws_box.sh status`,
Ergebnis `stopped`, nicht `running`. Eine gestoppte Instanz behält ihre
`LaunchTime`, also sind die Stunden, die `status` seither zählt, ausdrücklich
**keine** Laufzeit; die Abschlusszahlen stehen in der Tabelle darüber.

**Gegen den angehobenen Deckel: 31,05 von 34 Stunden und 3,5969 von 4,00 USD.
Er ist nicht gerissen.** Der ursprüngliche Deckel von 30 Stunden und 3,50 USD
war es, am 2026-09-10 um 15:20Z, und der Owner hatte ihn vorher angehoben.

Die harte Linie, die daneben stand und nicht gebraucht wurde: **erreicht die
Box den angehobenen Deckel, wird sie angehalten**, unabhängig davon, ob der
Bericht abgenommen ist. Alle Rohdaten waren committet, und der Bericht brauchte
die Box nicht. Die Abnahme kam vor dem Deckel, also ist die Linie nicht
gezogen worden.

**Der Verbleib: angehalten, nicht abgebaut.** Beide Datenträger bleiben, mit
Korpus, beiden Indizes und den Abbildern. Ein Stop gibt die öffentliche Adresse
zurück, also sind `BOX_IP` in `box.env` und der A-Record
`loadtest.infranode.dev` bis zum nächsten Start veraltet, und der Container
muss beim nächsten Start über AppAPI neu bewaffnet werden (DI-05-36). Der
ausführliche Nachtrag steht in `rohdaten/93-kosten-und-verbleib.txt`,
Abschnitt 7.

---

## 18. Die Skripte und die Rohdaten

Alle Skripte liegen unter `skripte/`, alle Rohdaten unter `rohdaten/`, und
`skripte/00-ablauf.md` ist die Datei, aus der Kriterium 4 seinen Satz
"wiederholbar beschrieben" bezieht: Abschnitt 2 nennt die geplante Reihenfolge,
Abschnitt 2b nennt, was am 09. und 10.09. wirklich gefahren wurde, mit jeder
Abweichung und ihrem Grund.

### 18.1 Die Skripte

| Skript | Was es tut | Herkunft |
|---|---|---|
| `90-bestand.sh` | Zustand der Box vor jedem Eingriff, `memory.events` ungelesen, `mem=4G`, Zahl der Nextcloud-Instanzen | neu in dieser Phase |
| `91-korpus.sh` | Korpus-Prüfsumme gegen v1.0, Urteilszeile, Abbruch vor dem Indexaufbau | ruft das Rezept `44-korpus-pruefsumme.py` **wortgleich** aus 06-11 |
| `92-wechsel.sh` | Abbild ziehen, Digest festhalten, Baumhash rufen, PHP-Hälfte einspielen, Registrierung, harte Grenze zurücklesen | neu in dieser Phase |
| `40b-baumhash.sh`, `40b-baumhash.py` | Baumhash des Pakets im Abbild gegen den Arbeitsbaum, drei Hashes | Neufassung von `40-abbild.sh`, dessen fehlendes `-i` den Beweis in beiden Vorläufern leer ließ |
| `93-nullstand.sh` | Nullstand mit Zahlen belegen, `findling:index --restart -n`, Wartefrist | neu in dieser Phase |
| `94-grundlast.sh` | MESS-01, vier Teile A bis D | Teil C ruft `52-woher-die-grundlast.py` **wortgleich** aus 06-11, Teil D ruft `01-grundlast-fein.py` **wortgleich** aus Plan 10-02 |
| `95-spitze.sh` | die erste Suche als Ereignis, in zwei Rollen `vorher` und `nachher`, mit dem bewussten Neustart und dem erzwungenen OOM-Beweis davor | neu in dieser Phase |
| `96-volllauf.sh`, `96b-waechter.sh` | der Volllauf, Sampler, Statusbeobachter, Wächter mit Rundendeckel 340, `00-FERTIG` als Vertrag | neu in dieser Phase, Sampler aus `scripts/ops/rss_sampler.sh` |
| `97-nebenlaeufigkeit.sh` | die p95-Reihe über fünf Stufen | neu in dieser Phase |
| `98-sprachfaelle.sh` | die zehn Sprachfälle über OCS, eigener Nutzer, WebDAV-Upload | neu in dieser Phase |
| `99-seitenroute.sh` | die Anzeigeseite, vier Reihen, beide Anmeldewege getrennt | Rangregel aus Abschnitt 2 des Seitenbudget-Berichts, **wortgleich** |
| `99b-runden.sh` | die Rundenzählung, zwei Fälle | neu in dieser Phase |

### 18.2 Die zwei Änderungen, die Kriterium 4 tragen

**Erstens: `search_load.py` statt `45-suchlast.py`.** Der Semantiklauf hat seine
Suchlast mit `45-suchlast.py` gefahren, und dessen Helfermodul liegt nicht im
Repository. Ein Bericht, dessen Lastzahlen aus einem Skript kommen, das niemand
nachfahren kann, erfüllt "wiederholbar beschrieben" nicht. Alle Lastzahlen
dieses Berichts kommen aus `backend/tests/tools/search_load.py`, das im
Repository liegt, getestet ist und sein Passwort über `--password-env` mit dem
**Namen** der Umgebungsvariablen nimmt statt über ein Argument.

**Zweitens: der Statusbeobachter liegt mit diesem Lauf zum ersten Mal im
Repository.** Er schreibt `rohdaten/96-statusseite.jsonl` mit 812 Lesungen im
120-Sekunden-Takt, und ohne ihn gäbe es weder die Phasengrenzen aus Abschnitt 6
noch die Durchsatzkurve aus Abschnitt 7.

### 18.3 Die zwei Skriptfehler, die während des Laufs korrigiert wurden

Der `occ`-Wrapper in `99b-runden.sh` und in `98-sprachfaelle.sh` reichte
`OC_PASS` an nichts weiter, weil `sudo` die Umgebung räumt und `docker exec`
keine weitergibt. Fall 2 der Rundenzählung bekam deshalb kein Konto. **Beide
Fassungen unter `skripte/` sind die gefahrenen, mit einem Satz im Kopf.** Fall 1
war vom Fehler nicht betroffen und lief in beiden Durchgängen gleich.

### 18.4 Die Rohdaten

Jede Datei mit einem Satz, was sie trägt. Sie sind **unverändert** committet;
keine ist geglättet, keine trägt ein Geheimnis.

| Rohdatei | Was sie trägt |
|---|---|
| `rohdaten/89-anfahrt.txt` | Anfahrt, Adresse, Owner-Freigabe des ursprünglichen Deckels |
| `rohdaten/90-bestand.txt` | Zustand der Box vor jedem Eingriff, Ablesestelle 1 |
| `rohdaten/91-korpus.txt` | Korpus-Prüfsumme, Urteil `korpus-gleich ja` |
| `rohdaten/92-wechsel.txt`, `rohdaten/92-info-box.xml` | Abbildwechsel, Digest-Befund, Registrierung, harte Grenze |
| `rohdaten/40b-baumhash.txt` | die drei Baumhashes, Urteil `baumhash-gleich ja` |
| `rohdaten/93-nullstand.txt` | der Nullstand mit Zahlen, Ablesestelle 3 |
| `rohdaten/94-grundlast.txt` | MESS-01, Teile A bis D, Ablesestellen 4 und 5 |
| `rohdaten/95-spitze-vorher.txt`, `rohdaten/95-vorher*.json`, `rohdaten/95-vorher.csv`, `rohdaten/95-spitze-vorher.txt` | die erste Suche auf leerem Bestand, Kaltstart 1.550,4 ms |
| `rohdaten/95-spitze-nachher.txt`, `rohdaten/95-nachher*.json`, `rohdaten/95-nachher.csv` | Kaltstart auf vollem Bestand, 1.838,4 ms, Ablesestelle 12 |
| `rohdaten/95b-kaltstart-reproduktion.txt`, `rohdaten/95c-kaltstart-reproduktion-teil2.txt` | die drei Reproduktionsdurchgänge und der Werkzeugbefund der Stufe 16 |
| `rohdaten/96-volllauf-start.txt`, `rohdaten/96-volllauf.csv` | Anstoß und 19.483 Sampler-Aufnahmen |
| `rohdaten/96-statusseite.jsonl` | 812 Lesungen der Statusseite im 120-Sekunden-Takt |
| `rohdaten/96b-waechter.txt`, `rohdaten/96b-waechter.log`, `rohdaten/96-sampler.log` | der Wächter über 320 Runden und die Protokolle der Beobachter |
| `rohdaten/96-oom-beweis.txt`, `rohdaten/07-oom-beweis.txt` | die vier Ablesungen des Schadensbeweises, Stellen 10, 13 und 14 |
| `rohdaten/96-suchlast-nachlauf.json`, `rohdaten/96-suchlast-danach.json` | die zwei Suchlastproben des Wächters |
| `rohdaten/96-vektorbestand.txt`, `rohdaten/48-vektorbestand.txt` | Chunks, Dokumente, Byte je Dokument, Verdikte, der aufgeklärte Versatz |
| `rohdaten/00-FERTIG`, `rohdaten/00-ende.txt` | der Vertrag des Wächters und die Auswertung von Laufzeit, Durchsatz und Spitzen |
| `rohdaten/97-nebenlaeufigkeit.txt`, `rohdaten/97-nebenlaeufigkeit.csv`, `rohdaten/97-stufe-<n>.json` | die p95-Reihe, Ablesestelle 11, die vier `regression stufe`-Zeilen |
| `rohdaten/98-sprachfaelle-erstlauf.txt`, `rohdaten/98-sprachfaelle.txt` | die zehn Sprachfälle, zweimal gefahren |
| `rohdaten/98b-sprachfaelle-diagnose.txt` | die Diagnose, die zeigt, dass es kein Sprachdefekt ist |
| `rohdaten/99-seitenroute.txt`, `rohdaten/99-reihe-a.txt` bis `rohdaten/99-reihe-d.txt` | die Seitenroute, vier Reihen, je ein unbearbeiteter Wert pro Zeile |
| `rohdaten/99b-runden.txt`, `rohdaten/99b-runden-alltag.txt`, `rohdaten/99b-runden-drift.txt`, `rohdaten/99b-fall*.json` | die Rundenzählung, beide Fälle getrennt |
| `rohdaten/66-generator-endungen.json`, `rohdaten/68-bestand-endungen.json` | der Endungsvergleich, Generator gegen Bestand |
| `rohdaten/93-kosten-und-verbleib.txt` | Laufzeit, Kosten, beide Deckel, der Owner-Entscheid |
| `rohdaten/99-ntfy-watch.log` | die Meldekette im Wartemodus |

**Zwei Rohdateien tragen Namen, die kein Skript vergibt.** `00-ende.txt` und
`48-vektorbestand.txt` sind Auswertungen; ihre Kopfzeile nennt jeweils, woraus
sie gerechnet sind. `99b-runden-alltag.txt` und `99b-runden-drift.txt` sind
unveränderte Auszüge aus `99b-runden.txt`.

---

## 19. Was dieser Lauf nicht besser gemacht hat

Dieser Abschnitt ist Pflicht und steht in eigener Überschrift, nicht als
Nebensatz in einer Tabellenzeile. Jede Zeile kommt aus einer Rohdatei dieses
Verzeichnisses.

### 19.1 Die Suchlatenz ist auf vier von fünf Stufen schlechter geworden

Alle vier über dem Rauschband von fünf Prozent: Stufe 4 plus 5,8, Stufe 8 plus
11,0, Stufe 12 plus 13,4, Stufe 16 plus 17,5 Prozent. Die Zusage auf Stufe 8
hält, **aber ihre Reserve fällt von 585,0 auf 374,5 ms**
(`rohdaten/97-nebenlaeufigkeit.txt`, vier `regression stufe`-Zeilen).

### 19.2 Der Lauf hat 40,6 Prozent länger gebraucht, und über der Owner-Erwartung

26 h 37 min gegen 18 h 56 min, bei einem Mehrbestand von 0,29 Prozent. **Die
Owner-Erwartung lag bei 22 bis 26 Stunden Gesamtlaufzeit der Box; allein der
Indexaufbau hat sie überschritten.** Der Vorbehalt zieht in dieselbe Richtung:
beim Anstoß lagen 1.653 Dateien schon im Index, ein Lauf von null hätte länger
gebraucht (`rohdaten/00-ende.txt`).

### 19.3 Der Durchsatz ist auf beiden Spuren gefallen

Gleichzeitig und um denselben Faktor: Indexierung 31,6 gegen 45,7 je Minute
(minus 30,9 Prozent), Einbettung 32,5 gegen rund 43 je Minute (minus
24,4 Prozent). Der Nachlauf mit rund 170 Dokumenten je Minute, der in 06-11 die
letzten 52 Minuten trug, kommt nicht mehr vor (`rohdaten/00-ende.txt`).

### 19.4 Der Kaltstart reißt die Aufrufdecke deutlicher als vorher

1.838,4 ms gegen eine Decke von 1.500 ms, Marge minus 338,4 ms, gegen plus
167,9 ms in Plan 07-01. Die eine gemessene Anfrage brachte null Treffer, und das
Nextcloud-Protokoll belegt den `cURL error 28` im inneren Aufruf
(`rohdaten/95-spitze-nachher.txt`, `rohdaten/95c-kaltstart-reproduktion-teil2.txt`).
Auch auf **leerem** Bestand lag die Marge schon bei minus 50,4 ms
(`rohdaten/95-spitze-vorher.txt`).

### 19.5 Ein Nutzer mit wenigen Dateien findet sie neben einem großen Fremdbestand nicht

Und er bekommt dabei keine Fehlermeldung, sondern eine leere Liste. Für drei von
vier geprüften Begriffen kommt seine Datei unter den ersten 2.000 Kandidaten
nicht vor, weil der Vorfilter über den ganzen Index rankt und der Recheck erst
danach filtert. Die Schleife holt keine zweite Runde nach (1,0 Runde je Suche,
gemessen). Das ist der Befund hinter den vier roten Sprachfällen, und er gehört
zu DI-07-03 (`rohdaten/98b-sprachfaelle-diagnose.txt`,
`rohdaten/99b-runden-alltag.txt`).

### 19.6 `memory.events max` ist von 2.796 auf 21.939 gestiegen

Also um das 7,8-fache, und `memory.peak` hat die harte Grenze exakt erreicht
statt sie wie in der Nachmessung um 157 MB zu unterschreiten. Kein Prozess wurde
getötet, aber der Kernel hat deutlich häufiger zurückgedrängt
(`rohdaten/07-oom-beweis.txt`).

### 19.7 Die `memory.current`-Spitze ist mit 2.048,0 MB genauso hoch wie in 06-11

Obwohl die Grundlast um 588,6 MB gesunken ist. **Die Ersparnis der Grundlast
trägt nicht in die Spitze durch** (`rohdaten/00-ende.txt`).

### 19.8 Der provozierte Driftfall ließ sich nicht herstellen

DI-07-03 bekommt damit nur eine seiner zwei Zahlen belastbar
(`rohdaten/99b-runden-drift.txt`).

### 19.9 Zwei Messskripte waren fehlerhaft und mussten während des Laufs korrigiert werden

Der `occ`-Wrapper in `99b-runden.sh` und `98-sprachfaelle.sh` reichte `OC_PASS`
an nichts weiter (Abschnitt 18.3).

### 19.10 Das Lastwerkzeug meldet null Fehlschläge, wo siebzehn Containeraufrufe abgebrochen sind

In Stufe 16 der Reihe stehen im Nextcloud-Protokoll 17 Abbrüche mit
`cURL error 28` bei 160 Anfragen, während `rohdaten/97-stufe-16.json`
`"failures": 0` schreibt. Die Route antwortet bei einem abgebrochenen
Containeraufruf mit HTTP 200 und ohne Containerteil. Der Fingerabdruck steht in
den Trefferzahlen: 5,40 je Anfrage auf den Stufen 1 und 4, nur 4,16 auf Stufe
16. **Ein Messwerkzeug, das einen Ausfall als Erfolg zählt, ist der
unangenehmere Befund von beiden**
(`rohdaten/95c-kaltstart-reproduktion-teil2.txt`).

### 19.11 Der Digest von `:dev` war nicht der aufgeschriebene

Plan 10-02 hatte einen anderen Digest festgehalten, `92-wechsel.sh` schreibt
`digest-gleich nein`. Der Stand ist über den Baumhash trotzdem belegt
(Abschnitt 1), aber ein aufgeschriebener Digest, der nicht mehr stimmt, ist eine
Feststellung, die man beim nächsten Mal nicht mehr machen kann
(`rohdaten/92-wechsel.txt`).

### 19.12 Der Kostendeckel ist gerissen

Der ursprüngliche Deckel von 30 Stunden und 3,50 USD ist am 2026-09-10 um
15:20Z erreicht worden und musste vom Owner auf 34 Stunden und 4,00 USD
angehoben werden (`rohdaten/93-kosten-und-verbleib.txt`).

### 19.13 Was besser wurde, damit der Abschnitt nicht schief steht

Die Grundlast um **588,6 MB**, die Gesamtspitze um **73,6 MB**, Stufe 1 der
Lastreihe um **3,6 Prozent**, `sock_throttled` von 3.044 auf 1.997, und die drei
Schadenszähler stehen zum dritten Mal in Folge auf null. Der Speicherbedarf je
Dokument ist unverändert (Abschnitt 14), und der Korpus, der Codestand und die
Verdikte sind gegengeprüft (Abschnitte 2, 1 und 15).
