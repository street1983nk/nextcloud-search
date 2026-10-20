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

## 8. Umgebung der Läufe

Alle Läufe nutzen dasselbe ausgelieferte Image `ghcr.io/street1983nk/findling_backend:1.4.3`,
Index-Digest `sha256:036eb67e3e1144bc371142e18fcbfe94327b2a6edbfc0d1aea2f32d93302fc6d`
(`rohdaten/01-artefakte.txt`, `rohdaten/01-vorbedingungen.txt` Abschnitt 4).

| | amd64 (Entwicklungsrechner) | arm64 (Messbox) |
|---|---|---|
| Rechner | Intel Core i5-1335U, 12 logische Kerne, gemessen auf `--cpuset-cpus 2,3` | m7g.large (Graviton3, CPU part 0xd40), 2 Kerne |
| Speicher | Docker-VM 7.972.040 kB, davon 6,2 GB verfügbar, kein Swap-Verbrauch | Kernel-Kappe `mem=4G`, MemTotal 3.989.432 kB, kein Swap |
| Container | `--network none`, 2 Threads | `--network none`, `--memory 2g --memory-swap 2g`, aus der cgroup zurückgelesen: `memory.max` 2147483648, `memory.swap.max` 0 |
| System | Docker Desktop unter Windows 11 | Ubuntu 24.04 arm64 (Abbild 20260904), Kernel 7.0.0-1012-aws, Docker 29.1.3 |
| Manifest | linux/amd64 `sha256:3d48d9854efa3208685cabd90c286ee5ad9aec699ef65a1d9540324decff905c` | linux/arm64 `sha256:317c4db4d5f5278b6ab4f8da084613102fa86718a1e2d5d915a22889cd353a04` |
| Laufzeit im Image | Python 3.13.15, SQLite 3.46.1, onnxruntime 1.30.0 | gleich |
| Rohdaten | `04-latenz-amd64.txt`, `03-qualitaet-*.txt` | `03-aufbau-arm.txt`, `11-arm-latenz.txt` |

Die Modelldateien sind auf beiden Rechnern gegen dieselben sha256 geprüft:
e5 int8 `8da4c9ba...8b6`, granite int8 `704c1ebc...e22` (`rohdaten/03-aufbau-arm.txt`,
Block 6). Die Qualitätsläufe liefen auf amd64 im Image; die Gegenprobe mit
onnxruntime 1.31.0 aus `backend/uv.lock` ergibt in allen drei Sprachen für jeden
Fall denselben Rang (`rohdaten/03b-gegenprobe-ort131.txt`, Abweichung 17.1 Punkt 2).

## 9. Trefferqualität

Sequenzlänge 512, int8-Vektoren, e5 mit `--pooling mean --prefixes on`, granite
mit `--pooling cls --prefixes off`. Die ausgelieferte Kombination ist jeweils die
int8-Zeile; nur sie geht in die Regel ein. Rohdaten: `rohdaten/03-qualitaet-<modell>-<fassung>-<sprache>.txt`.

**Deutsch (`de.jsonl`, 120 Fälle)**

| Modell | Fassung | Fälle | Recall@1 | Recall@5 | MRR | Rohdatei |
|---|---|---:|---:|---:|---:|---|
| e5 | int8 (ausgeliefert) | 120 | 0,2917 | 0,5917 | 0,4428 | `03-qualitaet-e5-int8-de.txt` |
| granite | int8, eigener Build | 120 | 0,4000 | 0,6750 | 0,5279 | `03-qualitaet-granite-int8-de.txt` |
| e5 | fp32 | 120 | 0,3167 | 0,6750 | 0,4807 | `03-qualitaet-e5-fp32-de.txt` |
| granite | fp32 | 120 | 0,5083 | 0,7917 | 0,6422 | `03-qualitaet-granite-fp32-de.txt` |
| granite | IBM-int8 (nur Vergleich) | 120 | 0,3500 | 0,7000 | 0,5051 | `03-qualitaet-granite-ibmint8-de.txt` |

**Englisch (`en.jsonl`, 42 Fälle)**

| Modell | Fassung | Fälle | Recall@1 | Recall@5 | MRR | Rohdatei |
|---|---|---:|---:|---:|---:|---|
| e5 | int8 (ausgeliefert) | 42 | 0,3333 | 0,7143 | 0,5010 | `03-qualitaet-e5-int8-en.txt` |
| granite | int8, eigener Build | 42 | 0,3810 | 0,7857 | 0,5515 | `03-qualitaet-granite-int8-en.txt` |
| e5 | fp32 | 42 | 0,2619 | 0,7143 | 0,4647 | `03-qualitaet-e5-fp32-en.txt` |
| granite | fp32 | 42 | 0,3571 | 0,8810 | 0,5796 | `03-qualitaet-granite-fp32-en.txt` |
| granite | IBM-int8 (nur Vergleich) | 42 | 0,4048 | 0,7381 | 0,5668 | `03-qualitaet-granite-ibmint8-en.txt` |

**Französisch (`fr.jsonl`, 120 Fälle)**

| Modell | Fassung | Fälle | Recall@1 | Recall@5 | MRR | Rohdatei |
|---|---|---:|---:|---:|---:|---|
| e5 | int8 (ausgeliefert) | 120 | 0,1583 | 0,3417 | 0,2604 | `03-qualitaet-e5-int8-fr.txt` |
| granite | int8, eigener Build | 120 | 0,1917 | 0,5250 | 0,3397 | `03-qualitaet-granite-int8-fr.txt` |
| e5 | fp32 | 120 | 0,1667 | 0,3833 | 0,2870 | `03-qualitaet-e5-fp32-fr.txt` |
| granite | fp32 | 120 | 0,3250 | 0,6417 | 0,4658 | `03-qualitaet-granite-fp32-fr.txt` |
| granite | IBM-int8 (nur Vergleich) | 120 | 0,2167 | 0,5500 | 0,3662 | `03-qualitaet-granite-ibmint8-fr.txt` |

**Positivkontrolle** (granite int8, `--pooling mean` gegen `cls`, MRR,
`rohdaten/03-positivkontrolle.txt`): Deutsch 0,3582 gegen 0,5279, Englisch
0,4981 gegen 0,5515, Französisch 0,3148 gegen 0,3397. `mean` ist überall
schlechter, der Schalter greift, die Läufe zählen.

**granite bei 1024 Token:** nicht gemessen, das Werkzeug hat keinen
Längenschalter (Abweichung 17.1 Punkt 3); die Zeile ginge ohnehin nicht in die
Regel ein.

**Plausibilität:** e5 fp32 auf Englisch (0,4647) und Französisch (0,2870) trifft
die Septemberzahlen aus `docs/measurements/2026-09-05-modellqualitaet/`.

Auffällig: Der Abstand zwischen fp32 und int8 ist bei granite viel größer als bei
e5. Auf Deutsch verliert e5 durch int8 0,0379 MRR, granite 0,1143; auf
Französisch e5 0,0266, granite 0,1261. Die Quantisierung kostet granite rund drei
Viertel seines fp32-Vorsprungs.

## 10. Paarvergleich

Ausgewertet mit `skripte/20-paarvergleich.py` aus den Rängen je Fall der
Rohdaten von Schritt 3, Ergebnis in `rohdaten/20-paarvergleich.txt`. "Nach vorn"
heißt: granite setzt den richtigen Abschnitt auf einen kleineren Rang als e5.
Fälle mit gleichem Rang zählen nicht. Der p-Wert ist der exakte einseitige
Vorzeichentest, P(X >= nach vorn) bei X ~ Bin(bewegt; 0,5). Der t-Wert der
Reziprokränge steht wie in Regel (a) verlangt daneben und entscheidet nichts.

**Ausgelieferte Kombination (int8 gegen int8), geht in die Regel ein**

| Sprache | Fälle | gleich | bewegt | nach vorn | nach hinten | p (einseitig) | t (Reziprokränge) | MRR e5 | MRR granite | relativ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Deutsch | 120 | 22 | 98 | 56 | 42 | 0,0944 | 2,028 | 0,4428 | 0,5279 | +19,21 % |
| Englisch | 42 | 9 | 33 | 18 | 15 | 0,364 | 0,792 | 0,5010 | 0,5515 | +10,07 % |
| Französisch | 120 | 13 | 107 | 73 | 34 | 0,000103 | 2,268 | 0,2604 | 0,3397 | +30,48 % |

**Zusatzzeilen ohne Gewicht für die Regel**

| Sprache | Paar | bewegt | nach vorn | nach hinten | p (einseitig) | relativ MRR |
|---|---|---:|---:|---:|---:|---:|
| Deutsch | fp32 gegen fp32 | 77 | 54 | 23 | 0,000269 | +33,60 % |
| Englisch | fp32 gegen fp32 | 33 | 22 | 11 | 0,0401 | +24,72 % |
| Französisch | fp32 gegen fp32 | 106 | 79 | 27 | 2,16e-07 | +62,27 % |
| Deutsch | e5 int8 gegen granite IBM-int8 | 92 | 50 | 42 | 0,233 | +14,06 % |
| Englisch | e5 int8 gegen granite IBM-int8 | 33 | 18 | 15 | 0,364 | +13,14 % |
| Französisch | e5 int8 gegen granite IBM-int8 | 108 | 71 | 37 | 0,000691 | +40,64 % |

Gegenprobe auf Deutsch, unabhängig vom Skript: Die Spalten "per case" beider
Rohdateien sind per `tr`, `sort` und `join` zusammengeführt und mit `awk`
gezählt (120 Fälle, 56 nach vorn, 42 nach hinten, 22 gleich), der p-Wert ist mit
`awk` über Logarithmen der Binomialkoeffizienten nachgerechnet (0,0944). Beide
Wege geben dieselben Zahlen.

## 11. Eigener int8-Build

Rohdaten: `rohdaten/02-int8.txt`, `rohdaten/01-artefakte.txt`, `rohdaten/05-image-zuwachs.txt`.

| Datei | Byte | sha256 |
|---|---:|---|
| granite fp32, Revision `835ad140` | 390.004.608 | `68e592b160673d30250824c1116bc6ab33f70efb22b97c9e1d7ce1e69c1c9d70` (gleich Abschnitt 3 und Hub) |
| granite int8, eigener Build, Lauf a | 97.858.099 | `704c1ebca5fbb7cd83ced41827658ac4c9990c64f7f2874d22b78044e5022e22` |
| granite int8, eigener Build, Lauf b | 97.858.099 | `704c1ebca5fbb7cd83ced41827658ac4c9990c64f7f2874d22b78044e5022e22` |
| granite IBM-int8 `model_quint8_avx2.onnx` | 98.247.878 | `a6022dd8220ea6f6595562a1328ee216f4a94faa55362f2f4747c80f1e78772e` (gleich Hub) |

- Beide Läufe liegen im Fenster 85.000.000 bis 110.000.000 Byte (Verhältnis
  3,99 zu 1) und sind laut `cmp` byte-gleich.
- **Befund A2:** Die Annahme A2 hält, `quantize_dynamic` läuft auf dem
  ModernBERT-Graphen durch. Die einzige Meldung ist eine Warnung zu einem
  Tensor `/Unsqueeze_6_output_0` vom Typ int64, der nicht quantisiert wird.
- **Vergleich mit der IBM-Datei:** Der eigene Build schlägt die IBM-Datei auf
  Deutsch (MRR 0,5279 gegen 0,5051), die IBM-Datei liegt auf Englisch (0,5668
  gegen 0,5515) und Französisch (0,3662 gegen 0,3397) vorn (Abschnitt 9). Den
  Vorzeichentest auf Deutsch besteht keine der beiden (Abschnitt 10). Die
  IBM-Datei ist nach ihrem Namen auf AVX2 zugeschnitten und für arm64 nicht
  gedacht; sie bleibt ein Vergleichspunkt.

## 12. Latenz und Durchsatz

Durchsatz über `findling.embed.bench --mode tokens-per-second` (Charge 8 x 512
Token, 20 Runden, 2 Threads). Einzelanfrage über `skripte/04-anfrage-latenz.py`
(Abweichung 17.1 Punkt 5): kalt heißt Tokenizer und Sitzung laden plus erste
Anfrage in einem frischen Container, fünf Starts je Modell; warm heißt 100
Anfragen aus `de.jsonl` nach zehn Vorläufen, angegeben ist der Median der fünf
Starts.

| Rechner | Modell | Token/s p50 | Token/s p95 | kalt p50 | kalt max | warm p50 | warm p95 | Rohdatei |
|---|---|---:|---:|---:|---:|---:|---:|---|
| amd64 | e5 int8 | 3624,2 | 2670,6 | 1368,1 ms | 1778,7 ms | 3,19 ms | 4,04 ms | `04-latenz-amd64.txt` |
| amd64 | granite int8 | 2880,8 | 2584,0 | 1370,6 ms | 1888,9 ms | 4,19 ms | 5,25 ms | `04-latenz-amd64.txt` |
| arm64 | e5 int8 | 3459,1 | 3446,5 | 751,4 ms | 758,3 ms | 4,65 ms | 5,42 ms | `11-arm-latenz.txt` |
| arm64 | granite int8 | 3023,3 | 2992,1 | 1065,3 ms | 1071,2 ms | 5,45 ms | 6,50 ms | `11-arm-latenz.txt` |

- granite ist im Durchsatz auf amd64 20,5 Prozent und auf arm64 12,6 Prozent
  langsamer als e5.
- Kalt dominiert das Laden: auf arm64 kostet granite rund 310 ms mehr (load
  rund 1059 gegen 746 ms im Median); die erste Anfrage selbst liegt bei 6,5 gegen 5,3 ms.
- Auf amd64 überschreiten beide Modelle die Decke von 1,5 s in einzelnen kalten
  Starts (e5 einmal mit 1778,7 ms, granite zweimal mit 1547,4 und 1888,9 ms); der
  Entwicklungsrechner streut stark. Die Regel (d) misst auf arm64, dort streuen
  die fünf Starts um weniger als 15 ms.

## 13. Arbeitsspeicher

arm64, Methode aus `docs/measurements/2026-09-fp32-speicher/` Abschnitt 3,
Charge 8 x 512 Token, 2 Threads, Arena aus, drei Läufe je Modell, Median
(`rohdaten/12-arm-speicher.txt`). Grenze 2 GiB = 2.147.483.648 Byte.

| Stufe | e5 int8 | granite int8 |
|---|---:|---:|
| `RssAnon` Start | 10.784 kB | 10.788 kB |
| `RssAnon` nach Bibliotheken | 24.080 kB | 24.076 kB |
| `RssAnon` nach Tokenizer | 311.044 kB | 237.268 kB |
| `RssAnon` nach Sitzung | 443.760 kB | 304.792 kB |
| `RssAnon` nach erster Charge | 445.832 kB (435,4 MiB) | 331.792 kB (324,0 MiB) |
| `RssAnon` nach sechster Charge | 457.868 kB | 332.188 kB |
| cgroup `memory.peak` | 716.947.456 B (683,7 MiB) | 676.896.768 B (645,5 MiB) |
| Abstand `memory.peak` zur Grenze | 1364,3 MiB | 1402,5 MiB |
| Abstand `RssAnon` erste Charge zur Grenze | 1612,6 MiB | 1724,0 MiB |

Im Durchsatzlauf über 500 Dokumente (`rohdaten/13-arm-durchsatz.txt`, Charge 2,
Median zweier Läufe) liegt `memory.peak` bei e5 bei 1.150.597.120 B (1097,3 MiB,
Abstand 950,7 MiB) und bei granite bei 618.407.936 B (589,8 MiB, Abstand
1458,2 MiB). Die Regel (c) misst Laden plus erste Charge; der Durchsatzlauf steht
nur zur Einordnung hier. granite braucht in jeder Stufe weniger Speicher, vor
allem weil sein Tokenizer kleiner ist (180.000 statt 250.002 Einträge) und die
Sitzung um rund 65 MB leichter.

## 14. Image-Zuwachs bei zwei Modellen

Aus den Dateigrößen, kein Probe-Image (Abweichung 17.1 Punkt 7,
`rohdaten/05-image-zuwachs.txt`):

| Datei | unkomprimiert Byte | gzip Byte |
|---|---:|---:|
| `model.onnx` (eigener int8-Build) | 97.858.099 | 67.103.762 |
| `tokenizer.json` | 25.301.672 | 4.016.312 |
| `tokenizer_config.json` | 12.860 | 914 |
| `special_tokens_map.json` | 871 | 192 |
| `config.json` | 1.216 | 530 |
| `1_Pooling/config.json` | 313 | 158 |
| Lizenztext Apache-2.0 (vertreten durch `COPYING.sqlite-vec`) | 11.132 | 3.980 |
| **Zuwachs granite** | **123.186.163** | **71.125.848** |
| e5 heute (Modell, Tokenizer, Konfiguration) | 135.185.084 | 83.087.883 |
| **Summe beider Modelle** | **258.371.247** | **154.213.731** |

Liegen beide Modelle im Image, wächst es um 123,2 MB unkomprimiert und 71,1 MB
gzip, das Modellgepäck verdoppelt sich ungefähr. Bei einem Ersatz statt einer
Ergänzung würde das Image um mindestens 12,0 MB unkomprimiert und 12,0 MB gzip
kleiner (die e5-Summe oben enthält `sentencepiece.bpe.model` und den Lizenztext
nicht).

## 15. Dauer der Neu-Einbettung auf der 4-GB-ARM-Box

Hochrechnung, kein Volllauf (Pitfall 16): `skripte/14-hochrechnung.py` aus dem
Durchsatz auf der Stichprobe von 500 Dokumenten (`rohdaten/13-arm-durchsatz.txt`,
zwei Läufe je Modell), Ergebnis in `rohdaten/14-hochrechnung.txt`. Chunking je
Modell-Tokenizer mit der 1024-Token-Kappe, Chunks zu 510 Token, Charge 2.

| | e5 int8 | granite int8 |
|---|---:|---:|
| Dokumente je Minute (Einbettung allein, Median) | 195,39 | 165,68 |
| Chunks je Dokument | 2,818 | 2,844 |
| Chunks hochgerechnet auf 52.111 Dokumente | 146.849 | 148.204 |
| **Neu-Einbettung 52.111 Dokumente, Einbettung allein** | **4 h 26 min** | **5 h 14 min** |
| gekoppelt (erste Indexierung mit OCR daneben) | 26 h 37 min (Bezug September) | 31 h 23 min (Obergrenze, skaliert) |

Annahmen, wie in `rohdaten/14-hochrechnung.txt` ausgewiesen:

1. Linear in der Dokumentzahl; die Chunks je Dokument der Stichprobe gelten für
   den Bestand.
2. Einbettung allein: Nach einem Modellwechsel bleibt der extrahierte Text im
   Volltextindex, weder Extraktion noch OCR fallen erneut an. Ein Prozess, zwei
   Threads, Box sonst leer, `--memory 2g`.
3. Der gekoppelte Septemberlauf ist ein anderer Fall; er steht mit dem
   Verhältnis der Einbettungsraten (1,179) skaliert daneben, als Obergrenze für
   den Fall, dass die Einbettung die langsamere Spur ist.

e5-Bezug: Diese Messung sieht e5 bei 195,39 Dokumenten je Minute, 115 Prozent der
rund 170 aus `docs/measurements/2026-09-vergleichsmessung-m7g/` Abschnitt 7. Der
Unterschied passt zum Messaufbau (Text vorher extrahiert, keine Nextcloud auf der
Box).

## 16. Kosten und Verbleib

Aus `rohdaten/90-kosten.txt` und `rohdaten/08-abbau-boxen.txt`:

- Bezahlte Zeit von LaunchTime 04:23:29Z bis Terminate 04:43:36Z: 20 min 07 s
  (0,3353 h).
- Satz 0,108016 USD je Stunde (Abschnitt 6), Kosten **0,0362 USD netto**, 6,0
  Prozent des Deckels von 0,60 USD und 6,4 Prozent der 5,2 h.
- Abbruchgrenze (80 Prozent, 4 h 10 min) nie erreicht.
- Verbleib: Instanz beendet ("User initiated"), Systemplatte mit der Instanz
  gelöscht, Security Group und Schlüsselpaar gelöscht. Die unabhängige
  Gegenprobe über das Profil zählt null laufende Instanzen, null Volumes, null
  Adressen und null Schlüsselpaare in der Region. Es ist kein Snapshot entstanden.

## 17. Abweichungen

Alle Abweichungen vom Rezept aus 35-09 und 35-10 stehen unten unverändert, wie
sie in den Plänen geschrieben wurden; 17.3 ergänzt die Auswertung.

### 17.1 Abweichungen vom Rezept (Plan 35-09)

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

### 17.2 Abweichungen vom Rezept (Plan 35-10)

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

### 17.3 Abweichungen der Auswertung (Plan 35-11)

1. **Abweichungsblöcke verschoben.** Die beiden Blöcke 17.1 und 17.2 standen
   zuvor ohne Nummer direkt hinter Abschnitt 7. Sie sind wortgleich unter
   Abschnitt 17 gerückt, damit die Ergebnisse in der Reihenfolge des Plans
   stehen. Die Abschnitte 1 bis 7 sind unverändert.
2. **Zusatzzeilen im Paarvergleich.** Neben dem Paar der ausgelieferten
   Kombination wertet `20-paarvergleich.py` auch fp32 gegen fp32 und e5 int8
   gegen granite IBM-int8 aus. Diese Zeilen stehen getrennt und gehen nicht in
   die Regel ein (Abschnitt 10).
3. **Rein lokale Auswertung.** Kein neuer Modelllauf, kein Zugriff auf die Box
   oder das Konto; alle Zahlen dieses Plans kommen aus den Rohdaten von 35-09
   und 35-10.
