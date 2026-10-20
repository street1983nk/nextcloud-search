# Messung: granite-embedding-97m-multilingual-r2 gegen multilingual-e5-small (Plan 35-03, STR-02)

Stand: 2026-10-19. Dieser Bericht beantwortet, ob Findling in v1.6 das
Einbettungsmodell von `intfloat/multilingual-e5-small` auf
`ibm-granite/granite-embedding-97m-multilingual-r2` wechseln soll. Bis Plan
35-11 trägt er nur Regel und Methode; die Abschnitte ab 8 (Ergebnisse) entstehen
in 35-09 bis 35-11. Die Regel steht hier, bevor eine einzige Zahl gemessen ist
(D-35-07), und sie wird nach dem ersten Lauf nicht mehr geändert.

## 1. Entscheidungsregel (vor der Messung festgelegt)

granite wird für v1.6 empfohlen, wenn alle vier Bedingungen erfüllt sind:

1. **(a) Deutsch, Paarvergleich.** Auf `testdata/semantik/de.jsonl` ist die
   ausgelieferte Kombination (int8-Modell, int8-Vektoren) von granite im
   Paarvergleich gegen dieselbe Kombination von e5 nicht schlechter, und der
   Vorzeichentest über die bewegten Fälle (Fälle mit verschiedenem Rang; Fälle
   mit gleichem Rang zählen nicht) zeigt eine Verbesserung auf dem
   Signifikanzniveau 0,05, einseitig. Ausgewiesen werden die Zahl der Fälle nach
   vorn und nach hinten, der p-Wert und dazu der gepaarte t-Wert der
   Reziprokränge.
2. **(b) Keine Sprache bricht ein.** Keine der drei Sprachen (Deutsch, Englisch,
   Französisch) zeigt mehr als 5 Prozent relativen MRR-Rückgang von granite
   gegen e5, gemessen an der ausgelieferten Kombination. Das ist die D-02-Grenze
   aus `docs/measurements/2026-09-05-modellqualitaet/`.
3. **(c) Speicher auf arm64.** Die anon-Spitze von Laden plus erster Charge
   (`RssAnon` und cgroup `memory.peak`) bleibt auf arm64 unter der
   2-GiB-Containergrenze, und zwar mit mindestens dem Abstand zur Grenze, den
   e5 im selben Lauf hat, abzüglich höchstens 256 MiB.
4. **(d) Antwortzeit auf arm64.** Die Einzelanfrage auf arm64 bleibt kalt unter
   der Decke von 1,5 s.

Sonst lautet das Verdikt "kein Wechsel" oder "Wechsel nur mit Bedingung", jeweils
mit Begründung je verfehlter Bedingung. Erfüllt das Ergebnis die Regel nicht
eindeutig (etwa ein p-Wert genau an der Schwelle oder eine Bedingung, die nur auf
einer Architektur gemessen werden konnte), wird nichts still gewählt: dann steht
eine Owner-Frage im Bericht.

## 2. Feste Fälle

Die Anfragen und Abschnitte stehen fest, bevor gemessen wird (D-35-06, D-35-07).
Es sind die drei Dateien unter `testdata/semantik/`, mit der Wortüberschneidungsregel
aus `backend/tests/test_model_quality.py` (kein Inhaltswort der Anfrage steht im
eigenen Abschnitt). Die Prüfsummen gelten für die Dateien im Repositorium (LF
als Zeilenende), Stand dieses Commits:

| Datei | Fälle | sha256 |
|---|---:|---|
| `de.jsonl` | 120 | `700c74d2c40d30ad26ad2cbd0ad8567a4b51346ea2b7f570abe884a0811e4f51` |
| `en.jsonl` | 42 | `95173d6e92d324a28f38b59122e7803a9fc84f7228325e42bb60d6f16bde0631` |
| `fr.jsonl` | 120 | `d5ef6d1c84256dc840c1b9832c180b2972304f078846c8846ef6558171a089a3` |

Nachrechnen: `git show HEAD:testdata/semantik/de.jsonl | sha256sum` (der Blob
im Repositorium, nicht die Arbeitskopie, die unter Windows CRLF tragen kann).

Das deutsche Set ist für diese Messung von 42 auf 120 Fälle gewachsen (D-35-10,
`testdata/semantik/README.md`, Abschnitt "Erweiterung Oktober 2026"). e5 wird
**im selben Lauf** neu gemessen; die Zahlen vom September sind keine
Vergleichsbasis der Qualität, weil damals onnxruntime 1.29.0 und ein anderes
Image liefen (heute 1.31.0) und das deutsche Set nur 42 Fälle trug (Pitfall 14).
Sie dienen höchstens als Plausibilität.

**Stichprobe für den Durchsatz.** Grundlage ist der Lastkorpus aus
`scripts/dev/build_load_corpus.py --seed phase5`. Aus der bytewise sortierten
Liste seiner relativen Pfade werden mit `random.Random("granite-35").sample(pfade, 500)`
genau **500 Dokumente** gezogen. Die Dateiliste wird samt sha256 je Datei unter
`rohdaten/` abgelegt und committet, bevor der erste Durchsatzlauf startet.

## 3. Modellfassungen

| Modell | Datei | Herkunft | Prüfung |
|---|---|---|---|
| e5, ausgeliefert | `model.onnx` (int8), 118.101.091 Byte, sha256 `8da4c9ba0ad59f58e8566839425d7fd6339d31414d0ce5cba2d7d0afb75dd8b6` | aus dem ausgelieferten Image mit `docker create` und `docker cp` nach außen kopiert, Ablesweg wie `docs/measurements/2026-09-06-vektordistanzen/` | gleich `MODEL_SHA256` in `.github/workflows/integration.yml`; vor jedem Lauf neu gerechnet |
| granite, fp32 | `onnx/model.onnx`, 390.004.608 Byte, sha256 `68e592b160673d30250824c1116bc6ab33f70efb22b97c9e1d7ce1e69c1c9d70` | `ibm-granite/granite-embedding-97m-multilingual-r2`, Revision `835ad14087e140460703cf0fae09f97d469d65c2` | sha256 nach dem Download gegen diesen Wert; Abweichung bricht ab |
| granite, int8 (eigener Build) | Ausgabe von `scripts/dev/quantize_model.py` | aus dem fp32 der Revision oben | Größenfenster, sha256, zweiter Lauf byte-gleich |
| granite, IBM-int8 | `onnx/model_quint8_avx2.onnx`, 98.247.878 Byte | dieselbe Revision | nur zusätzlicher Vergleichspunkt, keine Entscheidungsgrundlage |

**Größenfenster des int8-Builds.** Der Aufruf setzt ein eigenes Fenster:

```bash
cd backend && uv run --group quantize python ../scripts/dev/quantize_model.py \
  --input <granite-fp32>/model.onnx --output <granite-int8>/model.onnx \
  --min-bytes 85000000 --max-bytes 110000000
```

Begründung: Das Standardfenster des Skripts (100.000.000 bis 136.314.880 Byte)
ist auf e5 gerechnet, dessen Einbettungstabelle 81,7 Prozent der Parameter
trägt. Bei granite sind es 180.000 x 384 = 69,1 Mio. von 97,4 Mio. Parametern,
rund 71 Prozent; ein vollständig quantisiertes Modell liegt bei etwa
390.004.608 / 4 = 97,5 Mio. Byte und damit unter der e5-Untergrenze
(Pitfall 10). Eine fp32 gebliebene Tabelle läge bei rund 300 MB und weit über
110.000.000. Die Standardwerte des Skripts bleiben unverändert, sie sichern das
ausgelieferte e5. Reproduzierbarkeit: zwei Läufe des Builds müssen byte-gleiche
Dateien ergeben (gleiche sha256), wie 2026-09-05 für e5.

**Lizenz.** granite steht laut Modellkarte unter Apache-2.0; im Repositorium der
Revision liegt keine LICENSE-Datei. Für eine Auslieferung wäre der Lizenztext
wie bei e5 selbst beizulegen (siehe Abschnitt 5).

## 4. Messgrößen und Kommandozeilen

**Qualität** per `scripts/dev/model_quality.py`, je Sprache und je Modell,
Kennzahlen Recall@1, Recall@5, MRR, dazu `--per-case` für den Paarvergleich:

```bash
# e5, ausgeliefert
uv run python ../scripts/dev/model_quality.py --model <e5>/model.onnx --tokenizer <e5> \
  --dataset ../testdata/semantik/de.jsonl --prefixes on --pooling mean --vector-dtype int8 --per-case
# granite, eigener int8-Build
uv run python ../scripts/dev/model_quality.py --model <granite-int8>/model.onnx --tokenizer <granite> \
  --dataset ../testdata/semantik/de.jsonl --prefixes off --pooling cls --vector-dtype int8 --per-case
```

- Der Schalter `--pooling {mean,cls}` kommt in 35-09 (Standard `mean`, damit
  alte Läufe gleich bleiben). granite läuft immer mit `--pooling cls --prefixes off`,
  e5 mit `--pooling mean --prefixes on` (Pitfall 11).
- **Positivkontrolle:** granite mit `--pooling mean` muss messbar schlechter
  abschneiden als mit `cls`; sonst greift der Schalter nicht, und der Lauf zählt
  nicht.
- Sequenzlänge 512 für beide Modelle, wie im Produkt. granite bei 1024 erscheint
  nur als getrennte Zusatzzeile und geht nicht in die Regel ein (Pitfall 13).
- Das Pad-Token liest das Messwerkzeug aus `tokenizer_config.json` des
  jeweiligen Modells (granite: `<|endoftext|>`, id 179935), nicht aus einer
  e5-festen Annahme (Pitfall 12).
- Alle Qualitätsläufe mit `--network none`.

**Latenz amd64** auf dem Entwicklungsrechner, strikt seriell (D-35-11): im
ausgelieferten Image mit eingehängtem Modellordner,
`docker run --rm --network none --cpuset-cpus 2,3 -v <modell>:/model:ro <image> python -m findling.embed.bench --mode tokens-per-second`,
zwei Threads, Browser geschlossen, keine Parallellast. Dazu die
Einzelanfrage-Latenz über den Suchpfad, p50 und p95, kalt (erste Anfrage nach
Containerstart) und warm (nach zehn Vorläufen). Unter rund 4 GB freiem
Speicher wird nicht gemessen; die freie Speichermenge steht in jeder Rohdatei.

**arm64** auf einer nackten m7g.large (D-35-05) mit Kernel-Grenze `mem=4G`,
Container `--memory 2g`, gleiche Befehle wie amd64. Speicher nach der Methode
aus `docs/measurements/2026-09-fp32-speicher/`, Abschnitt 3: `RssAnon` vor dem
Laden, nach dem Anlegen der Sitzung und nach der ersten Charge, dazu cgroup
`memory.peak` des Containers.

**Neu-Einbettungsdauer** als Hochrechnung, nicht als Volllauf (Pitfall 16):
Dokumente je Minute auf der Stichprobe aus Abschnitt 2, Chunking je
Modell-Tokenizer mit der 1024-Token-Kappe, hochgerechnet auf 52.111 Dokumente.
Bezug für e5 bleibt der gekoppelte Volllauf von 26 h 37 min
(`docs/measurements/2026-09-vergleichsmessung-m7g/`, Abschnitt 7); die Annahme
der Hochrechnung (lineare Skalierung über die Dokumentzahl) wird ausgewiesen.

**Image-Zuwachs** aus den Dateigrößen: unkomprimiert und per
`gzip -c <datei> | wc -c` je zugefügter Datei (Modell, Tokenizer, Konfiguration,
Lizenztext).

## 5. Pflichtpunkte vom 10.10.

- Image-Zuwachs, wenn beide Modelle im Image liegen.
- Dauer der Neu-Einbettung auf der 4-GB-ARM-Box.
- Bewertung des Vorschlags "Neuinstallation Standard granite, Bestand optional
  per Opt-in mit Rückweg", einzeln an diesen Stellen:
  - zwei Modelle im Image und eine eigene Lizenzdatei für granite (wie
    `COPYING.multilingual-e5-small`), samt `THIRD-PARTY.md` und dem zugehörigen
    Test;
  - Embedding-Marke und Drift: die Marke trägt den Modellnamen, ein Wechsel löst
    heute "alles neu einbetten" aus, und während der Neu-Einbettung sind
    e5-Bestand und granite-Anfrage nicht vergleichbar;
  - zweite `vectors.db` je Modell und atomarer Wechsel, Rückweg durch Behalten
    der alten Datei (Platzbedarf je Chunk ausweisen);
  - Chunker und Pad-Token, weil ein anderer Tokenizer andere Chunkgrenzen bringt; Pooling und
    Präfixe im Modell-Wrapper sind heute e5-fest;
  - Distanzriegel und die Ähnlich-Schwelle `SIMILAR_CEILING` aus STR-01 neu
    kalibrieren, weil beide nur für e5 gemessen sind.

## 6. Kostendeckel der Box

Rechenblatt nach `docs/runbook-messbox.md`, Abschnitt 2. Satz der m7g.large:
**0,0978 USD je Stunde netto**, gelesen am 19.10.2026 um 16:20Z aus der
öffentlichen Preiskarte EU (Frankfurt), Linux On Demand (Veröffentlichung der
Karte 2026-10-15T19:13:16Z), dieselbe Quelle, die `scripts/ops/aws_box.sh prices`
nennt, und derselbe Wert wie der dort festgeschriebene Satz. Dazu die öffentliche
IPv4-Adresse mit 0,005 USD je Stunde und die 40-GB-gp3-Systemplatte mit
40 x 0,0952 / 730 = 0,005216 USD je Stunde. Ein Datenvolume entfällt, die Box
braucht weder Korpus-Snapshot noch Nextcloud.

| Posten | Planwert | Untergrenze (Ist früherer Anfahrten) |
|---|---:|---:|
| Handaufbau nackte Box (Security Group, Schlüssel, Instanz, `mem=4G`, Docker) | 1 h 00 min | 0 h 12 min (v1.3), 0 h 40 min (v1.2) |
| Image und Modellordner übertragen, sha256 prüfen | 0 h 30 min | nie gemessen |
| Latenz und Speicher, beide Modelle, seriell | 1 h 00 min | nie gemessen |
| Durchsatz auf der Stichprobe, beide Modelle | 1 h 00 min | nie gemessen |
| Gegenproben, Rohdaten sichern, Abbau | 0 h 30 min | 0 h 05 min (v1.2) |
| **Summe** | **4 h 00 min** | |

```
Satz            = 0,0978 + 0,005 + 0,005216 = 0,108016 USD je Stunde
Deckel (USD)    = 4,00 h x 0,108016 USD/h x 1,30 = 0,5617 USD, aufgerundet 0,60 USD
Deckel (h)      = 4,00 h x 1,30 = 5,2 h (nur Anzeige)
```

Die Reserve von 30 Prozent folgt D-28-01. Freigegeben wird die Box erst am
Checkpoint in 35-10, mit dem dann erneut gelesenen Satz.

## 7. Owner-Abnahme der Regel

Owner-Abnahme: 19.10.2026, "Regel abgenommen"

Abgenommen ohne Änderung: die Regel (a) bis (d) aus Abschnitt 1, die Methode,
die Stichprobe (500 Dokumente, Seed `granite-35`), der Kostendeckel (5,2 h,
0,60 USD) und das deutsche Testset mit 120 Fällen. Ab dem ersten Lauf in 35-09
ist die Regel eingefroren.

Vorgelegt wurden die vier Bedingungen aus Abschnitt 1, das Rechenblatt aus
Abschnitt 6 und zehn zufällig gezogene neue deutsche Fälle (de-99, de-79, de-57,
de-90, de-83, de-72, de-116, de-111, de-85, de-54). Die Ziehung:

```bash
sed -n '43,120p' testdata/semantik/de.jsonl \
  | shuf -n 10 --random-source=<(yes granite-35-03)
```

## Abweichungen vom Rezept (Plan 35-09)

Regel und Methode oben bleiben unverändert. Wo ein Lauf nicht genau wie
beschrieben ging, steht es hier mit Grund. Ablauf: `skripte/00-ablauf.md`,
Rohdaten: `rohdaten/`.

1. **Tokenizer-Prüfsumme.** Abschnitt 3 nennt nur die sha256 des fp32-Modells.
   `tokenizer.json` ist deshalb gegen Größe und Anfang und Ende der Prüfsumme
   aus der Recherche von 35-03 (25.301.672 Byte, `4f2842d5...582f`) und gegen
   die LFS-Prüfsumme geprüft, die der Hub im Kopf `x-linked-etag` mitschickt.
   Der volle Wert steht in `rohdaten/01-artefakte.txt`.
2. **onnxruntime im ausgelieferten Image.** Abschnitt 2 nennt für heute
   onnxruntime 1.31.0; das ausgelieferte Image 1.4.3 trägt 1.30.0, erst
   `backend/uv.lock` pinnt 1.31.0. Die Qualitätsläufe (Schritt 3) laufen wie
   vorgeschrieben im ausgelieferten Image mit `--network none`. Die Gegenprobe
   `skripte/03b-gegenprobe-ort131.sh` fährt die int8-Läufe beider Modelle in
   allen drei Sprachen noch einmal mit 1.31.0 aus dem Lockfile (über `uv run`,
   offline): alle Ränge je Fall sind gleich (`rohdaten/03b-gegenprobe-ort131.txt`).
3. **granite bei 1024 Token.** Das Messwerkzeug hat die Sequenzlänge fest auf
   512 (`MAX_SEQUENCE_TOKENS`), einen Schalter dafür gibt es nicht. Die
   Zusatzzeile bei 1024 fehlt deshalb; sie geht ohnehin nicht in die Regel ein.
4. **Annahme A2 gilt.** `quantize_dynamic` läuft auf dem ModernBERT-Graphen
   durch, beide Läufe liegen im Fenster und sind byte-gleich
   (`rohdaten/02-int8.txt`). Die IBM-Datei `onnx/model_quint8_avx2.onnx` ist
   trotzdem als zusätzlicher Vergleichspunkt mitgemessen, wie in Abschnitt 3
   vorgesehen, ohne Gewicht für die Regel.
5. **Einzelanfrage nicht über den Suchpfad.** Der Modell-Wrapper des Produkts
   ist e5-fest (Mittelwert-Pooling, Präfixe, Pad-Token `<pad>`); granite liefe
   dort nur mit einer Codeänderung (Pitfall 12), und Plan 35-09 ändert keinen
   Produktcode. Die Einzelanfrage beider Modelle misst deshalb
   `skripte/04-anfrage-latenz.py` mit onnxruntime direkt, im ausgelieferten
   Image, mit gleichem Tokenizer-Umgang und gleichen Sitzungsoptionen. Kalt
   heißt: Tokenizer und Sitzung laden plus erste Anfrage in einem frischen
   Container (fünf Starts je Modell); warm heißt: 100 Anfragen aus `de.jsonl`
   nach zehn Vorläufen. Der Durchsatz läuft unverändert über
   `findling.embed.bench --mode tokens-per-second`.
6. **Freier Speicher bei der Latenz.** Abschnitt 4 verlangt rund 4 GB frei.
   Der Windows-Host hatte vor Schritt 4 rund 3,0 GB frei (Rest belegt durch den
   laufenden Entwicklungsstapel, der nicht angehalten werden durfte); die
   Docker-VM, in der gemessen wurde, hatte 6,2 GB verfügbar und keinen
   Swap-Verbrauch. Beide Werte stehen vor jedem Block in
   `rohdaten/04-latenz-amd64.txt`. Die Abbruchgrenze von 1 GB aus D-35-11 war
   nie erreicht. Die Windows-Auslagerungsdatei ist immer teilweise belegt; als
   Swap zählt deshalb nur ihr Wachstum während eines Schritts.
7. **Image-Zuwachs ohne Probe-Image.** Kein Probe-Build wegen des Speichers;
   der Zuwachs kommt aus den Dateigrößen. Für den Lizenztext steht
   `backend/docker/licenses/COPYING.sqlite-vec` (Apache-2.0-Volltext), weil die
   Revision keine LICENSE-Datei trägt.

## Abweichungen vom Rezept (Plan 35-10)

1. **Stichprobe ohne Volllauf des Korpus.** `skripte/06-stichprobe.py` geht die
   Schleife von `build_load_corpus.py --seed phase5` nach, zieht aber nur die
   Namen und schreibt nur die 500 gezogenen Dateien; jede Datei hängt allein an
   Seed, Kategorie und Laufnummer und ist byte-gleich mit dem Volllauf. Hinweis:
   der Bestand der Septembermessung (52.111 Dokumente) wurde mit dem Seed
   `phase5-full` gebaut; Abschnitt 2 legt `phase5` fest, und dabei bleibt es.
   Die Verteilung der Formate ist bei beiden Seeds dieselbe.
2. **Text einmal auf dem Entwicklungsrechner.** Der Text der Stichprobe
   (darunter 100 Scans über die OCR-Spur) ist mit `skripte/07-text.sh` im
   ausgelieferten Image ohne Netz extrahiert und als eine Datei auf die Box
   gebracht (sha256 in `rohdaten/07-text.txt`, geprüft von
   `10-box-aufbau.sh pruefen`). Der Text hängt nicht am Einbettungsmodell; auf
   der Box laufen nur Chunking und Einbettung, und Dokumente je Minute meinen
   deshalb "Einbettung allein", wie der e5-Bezug von rund 170 je Minute.
3. **Deckel in USD.** Das Rechenblatt nennt den Deckel netto in USD wie
   `aws_box.sh`, ohne Umrechnung in Euro, weil kein Kurs gelesen wurde und der
   Owner den Deckel in USD abgenommen hat (Abschnitt 7).
4. **Abbau im zweiten Anlauf.** Die aus der Sitzung exportierten Zugangsdaten
   liefen nach rund 20 Minuten ab; der erste Abbauversuch (04:42Z) beendete
   nichts, und die erste Fassung von `skripte/19-abbau.sh` zählte die
   gescheiterten Gegenproben als null. Das Skript prüft seitdem die Sitzung vor
   dem Abbau und bricht bei einer gescheiterten Gegenprobe ab. Der zweite
   Anlauf beendete die Instanz um 04:43:36Z; eine unabhängige Gegenprobe über
   das Profil belegt null Instanzen, Volumes, Adressen und Schlüssel
   (`rohdaten/08-abbau-boxen.txt`). Schlusskosten 0,0362 USD gegen den Deckel
   von 0,60 USD (`rohdaten/90-kosten.txt`).
5. **Laufzeit weit unter dem Plan.** Box-Zeit 20 min 07 s statt geplanter
   4 h; die Messungen selbst liefen wie in `skripte/00-ablauf.md`, der
   Durchsatz mit zwei Läufen je Modell.
