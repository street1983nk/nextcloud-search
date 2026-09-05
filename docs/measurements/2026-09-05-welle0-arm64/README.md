# Welle 0 der Phase 6: die drei Vormessungen A, B und C

Drei Zahlen tragen jede Entscheidung dieser Phase, und bis zu diesem Bericht
waren alle drei geschätzt: wie viele Zeichen ein deutsches Token hat (A1), wie
viele Token je Sekunde das quantisierte Modell auf zwei geteilten Kernen
liefert (A2 und A3), und wie lange ein voller brute-force-Scan über eine
`vec0`-Tabelle dauert (der Boden unter A4 und unter der Wahl zwischen int8,
Bit-Vektoren und usearch). D-18 verlangt, dass sie vor jeder Schemafestlegung
laufen; Erfolgskriterium 4 verlangt für Messung C ausdrücklich mindestens
50.000 synthetische Dokumente, also 100.000 Chunks bei dem Zwei-Chunk-Deckel
aus D-01.

Das Messwerkzeug liegt als `backend/src/findling/embed/bench.py` im Repository
und gibt ausschließlich Zahlen aus: kein Wort aus einem Dokument, kein
Dateiname, und zu jeder Zahl die Architektur und die Zahl der sichtbaren CPUs
(T-06-06, T-06-07).

> **Nachtrag 05.09.2026.** Der Abschnitt unmittelbar unter dieser Zeile ist der
> Stand vor dem arm64-Lauf und bleibt unverändert stehen, weil er die Grundlage
> der D-04-Schwellen ist. Die native aarch64-Zahl liegt inzwischen vor: sie steht
> mit dem D-04-Verdikt und der Owner-Abnahme im Abschnitt
> [Nachtrag 05.09.2026: die aarch64-Spalte](#nachtrag-05092026-die-aarch64-spalte-und-was-sie-an-d-04-macht)
> am Ende dieser Datei. **D-04 greift nicht.**

## Der Stand dieses Berichts, zuerst und ohne Beschönigung

**Alle Zahlen unten sind auf x86_64 gemessen. Die native aarch64-Zahl fehlt
noch, und für Messung B ist genau sie die Zahl, an der die Phase hängt.**

Warum: die Messungen gehören laut Plan auf die nativen arm64-Läufer von GitHub.
Der Arbeitsablauf dafür ist geschrieben und liegt als
`.github/workflows/measure.yml` im Repository, aber `workflow_dispatch` setzt
voraus, dass die Datei im Standardzweig steht. Der Ausführende dieses Plans darf
nicht pushen; der erste Lauf ist deshalb die Aufgabe des Owners, und dieser
Bericht bekommt danach seine zweite Spalte.

Was statt dessen belegt ist, und es ist mehr als nichts:

| Messung | Architekturabhängig? | Stand |
|---|---|---|
| A, Zeichen je Token | **nein**, ein Tokenizer ist eine Tabellensuche und liefert auf jeder Maschine dieselben Token | **abgeschlossen.** A1 ist ersetzt |
| B, Token je Sekunde | **ja, stark** | x86-Zahl liegt vor, aarch64 offen. Der Bericht rechnet daraus einen Faktor aus, ab dem D-04 greift, statt eine ARM-Zahl zu erfinden |
| C, Scan-Latenz | **ja**, speicherbandbreitengebunden | x86-Zahl liegt vor, aarch64 offen. Die Aussage int8 gegen bit und kalt gegen warm ist ein Verhältnis und überlebt den Architekturwechsel eher als der Absolutwert |

Eine emulierte arm64-Zahl steht hier bewusst **nicht**. Das Abbild
`findling-sem-probe:arm64` aus Plan 06-01 existiert auf derselben Maschine, und
eine Messung darin wäre in wenigen Minuten zu haben. Sie wäre wertlos und
gefährlich zugleich: QEMU emuliert den Befehlssatz und ist dabei um ein
Vielfaches langsamer, eine so gewonnene Zahl für Messung B sähe nach einem
katastrophalen Ausfall aus und würde D-04 ohne Anlass auslösen. Das ist genau
der Fall, gegen den T-06-09 in diesem Plan steht.

## Die Umgebung dieser Messung

| Angabe | Wert |
|---|---|
| Datum | 2026-09-05 |
| Maschine | x86_64, 13th Gen Intel Core i5-1335U, Docker Desktop 29.5.2 unter Windows 11 |
| Kern der Docker-VM | 6.6.87.2-microsoft-standard-WSL2 |
| Abbild | `findling-sem-probe:local`, lokaler Bau aus `backend/Dockerfile` |
| Abbildkennung | `sha256:c9bb41d65746c584480ad05569445a2c36c6f347543f983d42416cedb02bfef9` |
| Python im Abbild | 3.13.15 |
| SQLite im Abbild | 3.46.1 |
| Erweiterung | `/usr/local/lib/findling/vec0.so`, sqlite-vec 0.1.9 |
| Modell | `/usr/local/share/findling/model`, multilingual-e5-small int8, 118.101.091 Byte |
| Tokenizer-Vokabular | 250.002 Einträge |
| Kerne für B und C | zwei, hart gepinnt mit `--cpuset-cpus 0,1` |
| Netzwerk | in jedem Lauf abgeklemmt (`--network none`) |

Die Abbildkennung ist **dieselbe**, unter der die Proben A12 und A13 in
`docs/measurements/2026-09-05-welle0-proben/README.md` gelaufen sind. Es ist
kein Registry-Digest: dieses Abbild wurde nie veröffentlicht.

**Ein Vorbehalt, der dazugehört.** Das Abbild stammt aus Plan 06-01 und kennt
`findling.embed.bench` noch nicht. Das Modul wurde als schreibgeschützter
Bind-Mount in die virtuelle Umgebung des Abbilds eingehängt. Gemessen wurden
also das Modell, der Tokenizer, die Erweiterung, CPython und SQLite **des
Abbilds**, und das Messmodul kam aus dem Arbeitsbaum. Im Arbeitsablauf entfällt
dieser Umweg: `measure.yml` zieht `:dev` aus der Registry, prüft in einem
eigenen Schritt, dass das Abbild das Werkzeug selbst trägt, und bricht sonst mit
einer benannten Meldung ab.

**Zwei gepinnte Kerne sind nicht dieselben zwei Kerne wie auf der Zielbox.**
`--cpuset-cpus 0,1` bindet hier zwei Leistungskerne eines Notebook-Prozessors,
die Zielbox hat zwei **geteilte** vCPU. Die x86-Zahl unten ist deshalb eher
optimistisch als repräsentativ, und zwar auch gegenüber einer x86-Zielbox wie
der cpx22 aus dem Volllauf.

## Die Kommandozeilen

```bash
# Messung A, dreimal, drei verschiedene Sorten Deutsch
docker run --rm --network none \
    -v "$PWD/backend/src/findling/embed:/app/.venv/lib/python3.13/site-packages/findling/embed:ro" \
    -v "$PWD/testdata:/testdata:ro" \
    --entrypoint python findling-sem-probe:local \
    -m findling.embed.bench --mode chars-per-token --text-dir /testdata/corpus

docker run --rm --network none \
    -v "$PWD/backend/src/findling/embed:/app/.venv/lib/python3.13/site-packages/findling/embed:ro" \
    -v "$PWD/.planning/phases/06-semantische-suche:/prose:ro" \
    --entrypoint python findling-sem-probe:local \
    -m findling.embed.bench --mode chars-per-token --text-dir /prose

docker run --rm --network none \
    -v "$PWD/backend/src/findling/embed:/app/.venv/lib/python3.13/site-packages/findling/embed:ro" \
    --entrypoint python findling-sem-probe:local \
    -m findling.embed.bench --mode chars-per-token --text-dir /usr/share/dict/ngerman

# Messung B, viermal, die vier RAM-Hebel aus 06-RESEARCH.md 3.6 gegeneinander
for combo in "2 256" "2 512" "8 256" "8 512"; do
    set -- $combo
    docker run --rm --network none --cpuset-cpus 0,1 \
        -v "$PWD/backend/src/findling/embed:/app/.venv/lib/python3.13/site-packages/findling/embed:ro" \
        --entrypoint python findling-sem-probe:local \
        -m findling.embed.bench --mode tokens-per-second --batch "$1" --sequence "$2" --threads 2
done

# Messung C, zweimal, je ein Speichertyp, warm und kalt ueber derselben Fuellung
for kind in int8 bit; do
    docker run --rm --network none --privileged --user 0 --cpuset-cpus 0,1 \
        -v "$PWD/backend/src/findling/embed:/app/.venv/lib/python3.13/site-packages/findling/embed:ro" \
        --entrypoint python findling-sem-probe:local \
        -m findling.embed.bench --mode scan-latency --vector-type "$kind" \
        --cache both --sizes 50000,100000,250000,1000000 --queries 100
done
```

`--privileged --user 0` steht nur an Messung C und nur wegen der kalten Reihe:
`/proc/sys/vm/drop_caches` ist root und in einem gewöhnlichen Container nur
lesbar. Ohne die zwei Flaggen meldet das Werkzeug `cold_not_enforced` und die
kalte Spalte wird unzitierbar, was richtiges Verhalten und ein verlorener Lauf
ist.

## Messung A: Zeichen je Token

**Ersetzt A1: "3,5 Zeichen je Token für Deutsch mit dem XLM-R-Tokenizer,
Bandbreite 3,0 bis 4,0."**

| Textsorte | Dateien | Zeichen | Token | **Zeichen je Token** |
|---|---|---|---|---|
| Deutsche Prosa (Planungsunterlagen dieser Phase) | 17 | 454.563 | 137.968 | **3,2947** |
| Referenzkorpus `testdata/corpus` (gemischt DE/EN) | 3 | 659 | 163 | 4,0429 |
| Wortliste `/usr/share/dict/ngerman` | 1 | 1.000.000 | 247.204 | 4,0452 |

**Die Antwort auf A1 lautet 3,29 für laufende deutsche Prosa und 4,05 für
reines Vokabular.** Die Schätzung 3,5 lag zwischen beiden Werten und innerhalb
der angegebenen Bandbreite 3,0 bis 4,0, aber sie war für keinen der beiden
Fälle richtig, und die zwei Fälle liegen 23 Prozent auseinander.

Warum die zwei Zahlen so weit auseinanderliegen, und warum das keine Streuung
ist: eine Wortliste enthält keine Funktionswörter. Deutsche Prosa besteht zu
einem großen Teil aus `der`, `die`, `und`, `in`, `zu`, `von`, und ein
SentencePiece-Vokabular mit 250.002 Einträgen hat für jedes davon genau ein
Token. Kurze Wörter drücken den Quotienten, lange Komposita heben ihn. Die
Wortliste ist also nicht die schlechtere Messung, sie ist die Messung an einem
anderen Text.

**Welche der beiden Zahlen wo gilt**, und das ist für die Ableitungen unten
entscheidend: der Lastkorpus aus Phase 5, aus dem die gemessenen 27.067 Zeichen
je Dokument stammen, erzeugt seine Prosa aus einer deutschen Wortliste
(`scripts/dev/build_load_corpus.py`). Für alles, was von den 1.355.205.169
gemessenen Zeichen ausgeht, gilt deshalb 4,05. Für einen echten Bestand gilt
3,29. Beide Rechnungen stehen unten nebeneinander.

**Zwei Kontrollen, damit die Zahl nicht auf einem Artefakt sitzt.** Erstens: die
Wortliste steht Wort für Zeile, also ist knapp jedes elfte Zeichen ein
Zeilenumbruch. Die Gegenprobe mit allen Umbrüchen durch Leerzeichen ersetzt
ergibt **exakt dieselbe** Tokenzahl (247.204), SentencePiece behandelt beide
gleich; der Quotient ist also nicht durch Umbrüche aufgebläht. Zweitens: der
Referenzkorpus liefert 4,04 statt der 3,29 der Prosa, weil er 659 Zeichen groß
ist und zur Hälfte aus englischen Erklärsätzen und aus Extremkomposita wie
`Straßenbaubeitragssatzung` besteht. Er ist als Stichprobe zu klein, um zitiert
zu werden, und steht hier, weil er die Zahl aus `testdata/` ist, die der Plan
verlangt.

Die Sonderzeichen sind abgeschaltet (`add_special_tokens=False`). Der echte
Kodierer setzt `<s>` und `</s>` je Aufruf, und die mitzuzählen würde den
Quotienten davon abhängig machen, wie der Text zufällig auf Dateien verteilt
war.

## Messung B: Token je Sekunde

**Ersetzt A2 ("30 bis 100 GFLOP/s effektiv auf 2 geteilten Ampere-Kernen") und
A3 ("800 bis 2.000 Token je Sekunde").**

Zwei gepinnte Kerne, `intra_op_num_threads=2`, 20 gemessene Runden je
Kombination, eine verworfene Warmlaufrunde davor. Volle Sequenzen ohne
Auffüllung.

| Charge | Sequenz | Token je Runde | p50 ms | p95 ms | **Token/s bei p50** | Token/s bei p95 |
|---|---|---|---|---|---|---|
| 2 | 256 | 512 | 89,8 | 131,9 | **5.700** | 3.881 |
| 2 | 512 | 1.024 | 296,7 | 401,2 | **3.451** | 2.553 |
| 8 | 256 | 2.048 | 447,8 | 547,4 | **4.573** | 3.741 |
| 8 | 512 | 4.096 | 1.250,6 | 1.486,0 | **3.275** | 2.756 |

Die Token/s neben p95 ist die **langsame**, nicht die schnelle: p95 ist die
langsame Runde, und ein Durchsatz, der von seinem besten Moment aus zitiert
wird, wäre die schmeichelhafteste und nutzloseste Zahl dieses Berichts.

**Die Schätzung war um den Faktor 2 bis 7 zu pessimistisch.** A3 nannte 800 bis
2.000 Token je Sekunde; gemessen sind 3.275 bis 5.700 auf zwei x86-Kernen.

Drei Befunde, die aus der Vierertabelle fallen und für Plan 06-05 unmittelbar
verwertbar sind:

1. **Die Sequenzlänge kostet mehr als die Chargengröße einbringt.** Von 512 auf
   256 Token steigt der Durchsatz bei gleicher Charge um 40 Prozent (8/512:
   3.275, 8/256: 4.573). Das ist die quadratische Aufmerksamkeitsmatrix, und
   Hebel 5 aus 06-RESEARCH.md 3.6 ist damit nicht mehr "leicht positiv", sondern
   der stärkste der vier gemessenen Hebel.
2. **Charge 2 ist schneller als Charge 8, nicht langsamer.** Bei Sequenz 256:
   5.700 gegen 4.573 Token/s. Hebel 4 senkt laut Recherche die Aktivierungsspitze
   von 150 bis 300 MB auf 40 bis 80 MB und sollte den Durchsatz "leicht" senken.
   Er senkt ihn nicht, er hebt ihn um ein Viertel. Die Kombination Charge 2,
   Sequenz 256 ist damit **gleichzeitig** die sparsamste und die schnellste der
   vier, was ein seltener Fall ist und in 06-05 gegengeprüft gehört.
3. Die Streuung zwischen p50 und p95 liegt bei 19 bis 47 Prozent. Auf einer
   Maschine, auf der sonst nichts läuft, ist das viel, und es ist der Grund,
   warum die Ableitung unten mit p50 **und** p95 rechnet.

**Was diese Zahl nicht enthält:** den Python-Aufwand von fastembed um die
Sitzung herum. Gemessen wurde onnxruntime direkt, weil Chargengröße und
Sequenzlänge genau die zwei Hebel sind, um die es hier geht, und fastembed beide
selbst wählt. Der ausgelassene Aufwand ist eine Kosten je Charge und keine je
Token; bei Charge 8 zu Sequenz 512 wären das ein paar Millisekunden auf 1.250.

## Messung C: Scan-Latenz gegen Chunk-Anzahl

**Der Boden unter A4 und unter der Wahl zwischen int8, Bit-Vektoren und
usearch.** k = 50, 384 Dimensionen, deterministische Vektoren aus festem
Startwert, 100 Abfragen je Größe und Cachezustand, zwei gepinnte Kerne.

**int8, 384 Byte je Vektor**

| Chunks | Gelesene Byte | warm p50 | warm p95 | kalt p50 | kalt p95 |
|---|---|---|---|---|---|
| 50.000 | 19,2 MB | 18,9 ms | 22,1 ms | 50,8 ms | 71,8 ms |
| **100.000** | **38,4 MB** | **34,3 ms** | **42,6 ms** | **81,4 ms** | **107,8 ms** |
| 250.000 | 96,0 MB | 87,4 ms | 106,0 ms | 202,1 ms | **372,7 ms** |
| 1.000.000 | 384,0 MB | 338,5 ms | **463,1 ms** | 784,6 ms | **1.021,1 ms** |

**bit, 48 Byte je Vektor**

| Chunks | Gelesene Byte | warm p50 | warm p95 | kalt p50 | kalt p95 |
|---|---|---|---|---|---|
| 50.000 | 2,4 MB | 3,1 ms | 3,6 ms | 8,9 ms | 16,1 ms |
| **100.000** | **4,8 MB** | **6,6 ms** | **7,6 ms** | **15,8 ms** | **26,0 ms** |
| 250.000 | 12,0 MB | 17,2 ms | 20,8 ms | 45,0 ms | 75,6 ms |
| 1.000.000 | 48,0 MB | 63,7 ms | 71,2 ms | 162,8 ms | 221,7 ms |

Fett gesetzt sind die Zeile, die Erfolgskriterium 4 verlangt (100.000 Chunks),
und jeder Wert über dem vorgeschlagenen Abbruchkriterium von **300 ms p95 je
Runde** aus 06-RESEARCH.md 2.2.

**Kalt heißt hier kalt für jede einzelne Abfrage.** Der Seitencache wird vor
jeder der 100 Abfragen verworfen und die Verbindung neu geöffnet. Einmal am
Anfang zu verwerfen und dann hundertmal zu messen ergäbe eine kalte und
neunundneunzig warme Abfragen, und der p50 davon wäre eine warme Zahl mit
kaltem Etikett (T-06-09). Das Verwerfen ist in jedem der 800 Fälle gelungen
(`cache_dropped=true`); der Lauf trägt keine einzige `cold_not_enforced`-Zeile.

Vier Befunde:

1. **Der Scan ist linear, und zwar sauber.** int8 warm: 18,9 / 34,3 / 87,4 /
   338,5 ms für 50k / 100k / 250k / 1M. Die Verdopplung der Chunkzahl verdoppelt
   die Zeit. Das ist die erwartete brute-force-Kurve und heißt zugleich, dass
   die Zahlen zwischen den Stützstellen interpolierbar sind.
2. **Bei 384 MB je Abfrage liegt der Durchsatz bei rund 1,13 GB/s warm.** Der
   Scan ist speicherbandbreitengebunden und nicht rechengebunden. Deshalb ist
   diese Messung die von den dreien, deren aarch64-Zahl am ehesten in derselben
   Größenordnung liegen wird, und deshalb ist sie zugleich die, bei der ein
   Verhältnis (int8 zu bit, kalt zu warm) belastbarer ist als der Absolutwert.
3. **Bit-Vektoren bringen Faktor 5,3, nicht Faktor 8 bis 20.** Gemessen bei 1M
   warm: 338,5 gegen 63,7 ms. Der Platzgewinn ist der volle Faktor 8 (384 gegen
   48 Byte), der Zeitgewinn ist es nicht; Hamming über popcount ist billiger als
   ein Skalarprodukt, aber der Vorsprung wird von der Fixkostenseite der Abfrage
   aufgezehrt. Die Schätzung aus 06-RESEARCH.md 2.3 war zu optimistisch.
4. **Die 250.000er-Schwelle aus `research/STACK.md` ist der Größenordnung nach
   bestätigt, und es ist die kalte Spalte, die sie reißt.** Warm hält int8 bei
   250.000 mit 106 ms noch bequem; kalt liegt derselbe Punkt bei 372,7 ms und
   damit über dem Abbruchkriterium. Wer die Schwelle nur warm prüft, findet sie
   erst bei 1.000.000.

## Die drei Ableitungen

### Ableitung 1: Chunkzahl bei dem 1.024-Token-Deckel

Gemessene Eingangsgröße: 1.355.205.169 Zeichen über 50.068 Dokumente, also
**27.067 Zeichen je Dokument** (`docs/performance.md`, Volllauf 04.09.2026).

| Grundlage | Zeichen je Token | Token je Dokument | 1.024 Token entsprechen | Anteil eines Dokuments |
|---|---|---|---|---|
| Wortliste (= Lastkorpus) | 4,0452 | 6.691 | 4.142 Zeichen | **15,3 %** |
| Prosa (= echter Bestand) | 3,2947 | 8.215 | 3.374 Zeichen | **12,5 %** |
| Schätzung A1 | 3,5 | 7.734 | 3.584 Zeichen | 13,2 % |

**Der Befund, der die Rechnung dieser Phase vereinfacht: unter dem Deckel aus
D-01 entscheidet A1 die Laufzeit nicht mehr.** Ein durchschnittliches Dokument
trägt 6.691 bis 8.215 Token, der Deckel liegt bei 1.024, und beide Werte liegen
weit darüber. Jedes durchschnittliche Dokument läuft also gegen den Deckel, und
die eingebettete Tokenmenge ist

    50.068 Dokumente x 1.024 Token = 51.269.632 Token

und das **unabhängig davon**, welche der drei Zahlen oben stimmt. Es ist eine
Obergrenze und keine Punktzahl: Dokumente unter 1.024 Token bringen weniger ein,
und wie viele davon im Bestand liegen, ist nicht gemessen.

Chunkzahl bei 512 Token je Chunk, also zwei Chunks je gedeckeltem Dokument:

    50.068 Dokumente x 2 Chunks = 100.136 Chunks

Das ist die Zahl aus Erfolgskriterium 4 auf 136 Chunks genau, und die
scan-latency-Reihe deckt sie mit der Stützstelle 100.000 und mit dem Zehnfachen
darüber ab.

**Was A1 statt der Laufzeit entscheidet, ist die Abdeckungszusage aus D-17b.**
Die semantische Suche deckt den Anfang jedes Dokuments ab, und dieser Anfang ist
gemessen **12,5 Prozent** eines durchschnittlichen Dokuments bei echter Prosa
(3.374 von 27.067 Zeichen), nicht 13,2 wie geschätzt. Der Store-Text sollte den
Anteil nennen, nicht die Tokenzahl: 1.024 Token sagen niemandem etwas, "der
Anfang, etwa eine Seite Text" sagt es.

### Ableitung 2: Dauer der Embedding-Zweitspur

Zu rechnen ist die gedeckelte Menge aus Ableitung 1 gegen den gemessenen
Durchsatz. Beide Enden der Vierertabelle stehen hier, weil die Wahl von Charge
und Sequenz in Plan 06-05 fällt und nicht hier.

**Gedeckelt (D-01, 51,27 Mio Token), auf zwei x86-Kernen:**

| Kombination | Token/s | Dauer |
|---|---|---|
| Charge 8, Sequenz 512, p50 | 3.275 | **4 h 21 min** |
| Charge 8, Sequenz 512, p95 | 2.756 | 5 h 10 min |
| Charge 2, Sequenz 256, p50 | 5.700 | **2 h 30 min** |
| Charge 2, Sequenz 256, p95 | 3.881 | 3 h 40 min |

**Ungedeckelt, zum Vergleich und weil der Deckel eine aufdrehbare Einstellung
ist:**

| Grundlage | Token gesamt | bei 3.275 Token/s | bei 5.700 Token/s |
|---|---|---|---|
| Prosa (3,2947) | 411,3 Mio | 34,9 h | 20,0 h |
| Wortliste (4,0452) | 335,0 Mio | 28,4 h | 16,3 h |

Die Recherche schätzte für den ungedeckelten Lauf **54 bis 180 Stunden** und für
den gedeckelten **7 bis 24 Stunden**. Gemessen auf x86: ungedeckelt 16 bis 35
Stunden, gedeckelt 2,5 bis 5 Stunden.

**Und jetzt die ehrliche Hälfte.** Diese Zahlen stehen auf zwei
Leistungskernen eines x86-Notebooks. Die Zielhardware ist eine ARM-Box mit zwei
geteilten vCPU. Ein Faktor zwischen den beiden ist in diesem Repository
**nirgends gemessen**: der Volllauf aus Phase 5 lief auf der x86-Generalprobe
cpx22, weil zu diesem Zeitpunkt keine ARM-Maschine beschaffbar war
(`docs/performance.md`, "Warum die ARM-Maschine fehlt"). Einen Faktor zu raten
wäre genau die Sorte Zahl, die dieser Bericht ersetzen soll.

Was sich statt dessen sagen lässt, und was für die Entscheidung genügt: **der
Faktor, ab dem der gedeckelte Erstindex über einem Tag liegt und D-04 greift.**

| Kombination | x86-Dauer | ARM müsste langsamer sein als |
|---|---|---|
| Charge 8, Sequenz 512 | 4 h 21 min | **Faktor 5,5** |
| Charge 2, Sequenz 256 | 2 h 30 min | **Faktor 9,6** |

Der Lauf von `measure.yml` auf `ubuntu-24.04-arm` liefert genau diesen Faktor,
und er ist die einzige noch fehlende Zahl dieser Welle.

### Ableitung 3: Vektoranteil je Nutzersuche

Der Maßstab steht im eigenen Code: `php/lib/Search/Provider.php` führt
`BUDGET_NANOSECONDS = 2_500_000_000` (Z. 57) und `MAX_ROUNDS = 3` (Z. 65). Eine
Nutzersuche kann drei Container-Runden auslösen, und jede enthielte einen
Vektorscan. Das vorgeschlagene Abbruchkriterium aus 06-RESEARCH.md 2.2 ist
300 ms p95 **je Runde**.

Bei der Chunkzahl aus Ableitung 1 (100.136, gerechnet mit der Stützstelle
100.000):

| Speichertyp | Cachezustand | p95 je Runde | gegen 300 ms | drei Runden | Anteil an 2,5 s |
|---|---|---|---|---|---|
| int8 | warm | 42,6 ms | 14 % | 127,7 ms | **5,1 %** |
| int8 | kalt | 107,8 ms | 36 % | 323,3 ms | **12,9 %** |
| bit | warm | 7,6 ms | 3 % | 22,9 ms | 0,9 % |
| bit | kalt | 26,0 ms | 9 % | 78,0 ms | 3,1 % |

**int8 mit brute force hält das Budget bei der Chunkzahl dieser Phase mit
Abstand**, warm um den Faktor 7, kalt um den Faktor 2,8. Bit-Vektoren werden bei
dieser Größe nicht gebraucht, und D-10 (nicht bauen, nur dokumentieren) bleibt
damit die richtige Entscheidung.

Wo es kippt, und das gehört in denselben Absatz, weil der Deckel aus D-01 eine
aufdrehbare Einstellung ist:

| Chunks | int8 warm p95 | int8 kalt p95 | Urteil |
|---|---|---|---|
| 100.000 | 42,6 ms | 107,8 ms | beide gut |
| 250.000 | 106,0 ms | 372,7 ms | **kalt gerissen** |
| 1.000.000 | 463,1 ms | 1.021,1 ms | **beide gerissen** |

Ein Betreiber, der den Deckel auf volles Embedding aufdreht, landet bei rund
einer Million Chunks und reißt das Budget mit int8 auch warm. Bit-Vektoren
halten dieselbe Million kalt bei 221,7 ms und damit unter dem Kriterium. Das ist
das Argument dafür, den Abstraktionsschnitt aus D-08 wirklich zu bauen, und
zugleich der Beleg dafür, dass er in dieser Phase nicht durchschritten werden
muss.

## Was diese Messung nicht beantwortet

- **Die native aarch64-Zahl**, siehe oben. Sie ist die einzige offene Größe.
- **Den Qualitätsverlust von Bit-Vektoren** für e5-small auf Deutsch. Er ist
  nach wie vor nicht belegt, und dieser Bericht misst Zeit und Platz, nicht
  Trefferqualität. Falls die Wahl zwischen int8 und bit je fällt, ist sie
  deshalb eine Owner-Entscheidung und keine Umsetzungsfrage.
- **Die RAM-Spitze beim Einbetten.** A5 (150 bis 300 MB bei Charge 8 zu 512
  Token) bleibt eine Schätzung. Messung B misst Zeit, nicht Speicher; die
  Spitze gehört an den Lasttest der Zweitspur.
- **Wie viele Dokumente unter 1.024 Token liegen.** Ableitung 1 ist deshalb eine
  Obergrenze.
- **Ob `vec0` mit Metadaten- und Partitionsspalten schneller oder langsamer
  wird** (A8). Gemessen wurde eine nackte Vektortabelle.

## Die Rohdaten

Im Verzeichnis `raw/` neben dieser Datei, eine Datei je Lauf, unverändert so,
wie das Werkzeug sie geschrieben hat:

| Datei | Lauf |
|---|---|
| `amd64-machine.txt` | Maschine, Abbildkennung, Fassungen |
| `amd64-chars-per-token-corpus.txt` | A über `testdata/corpus` |
| `amd64-chars-per-token-prosa.txt` | A über die deutschen Planungsunterlagen dieser Phase |
| `amd64-chars-per-token-wordlist.txt` | A über `/usr/share/dict/ngerman` |
| `amd64-tokens-per-second-b2-s256.txt` | B, Charge 2, Sequenz 256 |
| `amd64-tokens-per-second-b2-s512.txt` | B, Charge 2, Sequenz 512 |
| `amd64-tokens-per-second-b8-s256.txt` | B, Charge 8, Sequenz 256 |
| `amd64-tokens-per-second-b8-s512.txt` | B, Charge 8, Sequenz 512 |
| `amd64-scan-latency-int8.txt` | C, int8, warm und kalt, vier Größen |
| `amd64-scan-latency-bit.txt` | C, bit, warm und kalt, vier Größen |

Der Lauf auf nativer aarch64-Hardware legt seine Dateien unter denselben Namen
mit dem Präfix `arm64-` daneben. `measure.yml` erzeugt sie als Artefakt
`welle0-arm64`.

## Nachtrag 05.09.2026: die aarch64-Spalte, und was sie an D-04 macht

Die oben als offen bezeichnete Zahl liegt vor. Sie stammt aus dem ersten Lauf
von `.github/workflows/measure.yml`, ausgelöst als `workflow_dispatch` auf
`main`:

| Angabe | Wert |
|---|---|
| Lauf | [33946845859](https://github.com/street1983nk/nextcloud-search/actions/runs/33946845859) |
| Datum | 2026-09-05, 05:18 UTC |
| Commit | `8d108a3ad68453884376f70c8685a9c8d3392ba4` |
| Jobs | "Wave 0 on arm64 (target)" und "Wave 0 on amd64 (comparison)", beide erfolgreich |
| Abbild | `ghcr.io/street1983nk/findling_backend:dev` |
| Abbildkennung | `sha256:86cf2fcddb96bd608a761d6b46e5eaa87e15d46e731af9b911f83407f1f54b45` |

Die Kennung benennt das **Mehrarchitektur-Manifest**, nicht eine der beiden
Hälften; beide Läufer melden sie deshalb gleichlautend, und jeder hat daraus
seine eigene Architektur gezogen. Es ist ausdrücklich nicht das Abbild, unter dem
die x86-Zahlen weiter oben gelaufen sind (`findling-sem-probe:local`,
`sha256:c9bb41d6...`). Beide stammen aus demselben `backend/Dockerfile`, aber
gemessen wurde nicht zweimal dasselbe Artefakt, und das gehört vor jede Zahl in
diesem Nachtrag.

### Die beiden neuen Maschinen

| Angabe | arm64 (die Aussage) | amd64 (der Vergleich) |
|---|---|---|
| Läufer | `ubuntu-24.04-arm` | `ubuntu-24.04` |
| Architektur | aarch64 | x86_64 |
| Prozessor | ARM Neoverse-N2, 4 Kerne, 1 Faden je Kern | AMD EPYC 9V74 (80-Kerner), 4 sichtbare Kerne |
| Cache | L2 4 MiB, L3 128 MiB | siehe `raw/runner-amd64-machine.txt` |
| Kern | 6.17.0-1022-azure | 6.17.0-1022-azure |
| RAM | 15.947 MB | siehe Rohdaten |
| Kerne für B und C | zwei, `--cpuset-cpus 0,1`, `--threads 2` | ebenso |
| Netzwerk | in jedem Lauf abgeklemmt | ebenso |

**Drei Vergleichsbasen, und der Nachtrag sagt zu jeder Zahl, welche gilt.**
Erstens das x86-Notebook von weiter oben: es ist die Basis, auf der die
D-04-Schwellen 5,5 und 9,6 ausgerechnet wurden, und deshalb ist es die Basis,
gegen die das Verdikt fällt. Zweitens der arm64-Läufer: die Zielarchitektur.
Drittens der amd64-Läufer: dieselbe Infrastruktur, dasselbe Abbild, derselbe Tag,
und damit der einzige saubere Architekturvergleich dieses Berichts, weil sich
zwischen ihm und dem arm64-Lauf außer dem Befehlssatz nichts unterscheidet.

**Der Vorbehalt, der bleibt und der wichtiger ist als alle drei.** Auch der
arm64-Läufer ist **nicht die Zielbox**. Er stellt vier dedizierte
Neoverse-N2-Kerne, von denen zwei gepinnt wurden; die Zielbox hat zwei
**geteilte** vCPU. Die Zahlen unten sind gegenüber der Zielbox eher optimistisch,
genau wie die x86-Zahlen weiter oben es gegenüber der cpx22 waren. Was sie
belastbar macht, ist nicht ihre Nähe zur Zielbox, sondern der Abstand zur
D-04-Schwelle, und der ist unten beziffert.

### Messung A auf aarch64: die Architekturunabhängigkeit ist jetzt belegt

| Textsorte | Dateien | Zeichen | Token | Zeichen je Token arm64 | amd64-Läufer | x86-Notebook |
|---|---|---|---|---|---|---|
| Deutsche Prosa (Planungsunterlagen dieser Phase) | 18 | 469.513 | 142.396 | **3,2972** | 3,2972 | 3,2947 |
| Referenzkorpus `testdata/corpus` | 3 | 659 | 163 | 4,0429 | 4,0429 | 4,0429 |
| Wortliste `/usr/share/dict/ngerman` | 1 | 1.000.000 | 247.204 | 4,0452 | 4,0452 | 4,0452 |

**Die Tokenzahlen sind zwischen aarch64 und x86_64 bitgleich**, in allen drei
Fällen und auf das letzte Token genau: 142.396, 163, 247.204. Die Behauptung "ein
Tokenizer ist eine Tabellensuche und liefert auf jeder Maschine dieselben Token"
ist damit keine Behauptung mehr, sondern der billigstmögliche Beweis, den ein
gleiches Zahlenpaar hergibt.

Die Prosa-Zeile weicht gegenüber dem x86-Notebook um 0,08 Prozent ab (3,2972
statt 3,2947), und der Grund steht in der Dateizahl: 18 statt 17
Planungsdateien. Zwischen der lokalen Messung und dem Lauf auf `8d108a3` ist eine
Datei dazugekommen. Das ist ein anderer Text und keine andere Maschine.

**Ableitung 1 ändert sich dadurch nicht.** Mit 3,2972 statt 3,2947 trägt ein
durchschnittliches Dokument 8.209 statt 8.215 Token, und 1.024 Token entsprechen
3.376 statt 3.374 Zeichen. Der Abdeckungsanteil aus D-17b bleibt bei **12,5
Prozent**, die Chunkzahl bleibt bei 100.136, und der Befund, dass unter dem
Deckel aus D-01 die Zahl A1 die Laufzeit nicht mehr entscheidet, bleibt
unberührt.

### Messung B auf aarch64: die Zahl, an der die Phase hing

| Charge | Sequenz | Token je Runde | p50 ms | p95 ms | **Token/s bei p50** | Token/s bei p95 |
|---|---|---|---|---|---|---|
| 2 | 256 | 512 | 107,9 | 108,3 | **4.745** | 4.728 |
| 2 | 512 | 1.024 | 281,4 | 285,9 | **3.640** | 3.581 |
| 8 | 256 | 2.048 | 425,8 | 428,8 | **4.809** | 4.776 |
| 8 | 512 | 4.096 | 1.163,8 | 1.191,8 | **3.519** | 3.437 |

Zwei Dinge fallen sofort auf, und beide sind für Plan 06-05 verwertbar.

**Erstens: die Streuung ist auf dem Läufer verschwunden.** Zwischen p50 und p95
liegen hier 0,4 bis 2,4 Prozent, auf dem Notebook waren es 19 bis 47. Befund 3
des Abschnitts "Messung B" oben war also kein Merkmal der Rechenlast, sondern
eines der Maschine, auf der sie lief. Für die Ableitung heißt das, dass p50 und
p95 auf dem Läufer praktisch dieselbe Aussage tragen; die Rechnung unten führt
trotzdem beide, weil die Zielbox mit ihren geteilten vCPU eher dem Notebook
gleichen wird als dem Läufer.

**Zweitens: Befund 2 von oben hält auf ARM nicht.** Auf dem Notebook war Charge 2
bei Sequenz 256 um ein Viertel schneller als Charge 8 (5.700 gegen 4.573). Auf
aarch64 sind die beiden praktisch gleich, mit einem Vorsprung von 1,3 Prozent für
Charge 8 (4.809 gegen 4.745). Die Aussage "Charge 2 ist gleichzeitig die
sparsamste und die schnellste" wird damit zu "Charge 2 ist die sparsamste und
kostet auf der Zielarchitektur keine messbare Zeit", was für die Entscheidung in
06-05 die bequemere Lage ist, aber eine andere Begründung braucht als die
Notebook-Zahl. Befund 1 dagegen hält unverändert: von 512 auf 256 Token steigt
der Durchsatz bei Charge 8 um 37 Prozent (3.519 auf 4.809), auf dem Notebook
waren es 40.

### Der gemessene Faktor zwischen x86 und ARM

| Kombination | x86-Notebook | **arm64-Läufer** | amd64-Läufer | Faktor Notebook/ARM | Faktor amd64-Läufer/ARM |
|---|---|---|---|---|---|
| Charge 2, Sequenz 256 | 5.700 | **4.745** | 2.516 | **1,20** | 0,53 |
| Charge 2, Sequenz 512 | 3.451 | **3.640** | 2.112 | **0,95** | 0,58 |
| Charge 8, Sequenz 256 | 4.573 | **4.809** | 2.493 | **0,95** | 0,52 |
| Charge 8, Sequenz 512 | 3.275 | **3.519** | 2.082 | **0,93** | 0,59 |

Alle Werte sind Token je Sekunde bei p50. Ein Faktor größer als 1 heißt "ARM ist
langsamer".

**Der höchste gemessene Faktor ist 1,20**, und er steht bei genau der
Kombination, deren D-04-Schwelle mit 9,6 die höchste ist. In drei von vier
Kombinationen ist ARM nicht langsamer, sondern schneller.

Gegen den amd64-Läufer, also im einzigen Vergleich, in dem sich außer dem
Befehlssatz nichts unterscheidet, ist der Neoverse-N2 **um den Faktor 1,69 bis
1,93 schneller** als der EPYC 9V74. Das ist kein Wunder und auch kein
Messfehler: der EPYC ist ein 80-Kerner, dessen vier sichtbare Kerne auf einem
geteilten Sockel sitzen, und das ONNX-Runtime-Backend findet auf Neoverse-N2 mit
`i8mm` und `bf16` genau die Befehle vor, die ein int8-Modell braucht (siehe die
Flaggenliste in `raw/arm64-machine.txt`).

### Das D-04-Verdikt

D-04 lautet: fällt Messung B so aus, dass selbst der 1.024-Token-Deckel über
einem Tag liegt, entscheidet der Owner über den potion-Notausgang.

Die gedeckelte Tokenmenge aus Ableitung 1 (50.068 Dokumente mal 1.024 Token =
51.269.632 Token) gegen die vier gemessenen aarch64-Durchsätze:

| Kombination | Token/s p50 | **Dauer bei p50** | Token/s p95 | Dauer bei p95 |
|---|---|---|---|---|
| Charge 8, Sequenz 512 | 3.519 | **4 h 03 min** | 3.437 | 4 h 09 min |
| Charge 2, Sequenz 512 | 3.640 | **3 h 55 min** | 3.581 | 3 h 59 min |
| Charge 2, Sequenz 256 | 4.745 | **3 h 00 min** | 4.728 | 3 h 01 min |
| Charge 8, Sequenz 256 | 4.809 | **2 h 58 min** | 4.776 | 2 h 59 min |

> **Verdikt: D-04 greift nicht.** Der höchste gemessene x86/ARM-Faktor ist
> **1,20** (Charge 2, Sequenz 256) und liegt damit unter beiden Schwellen dieses
> Berichts, 5,5 für Charge 8 zu Sequenz 512 und 9,6 für Charge 2 zu Sequenz 256.
> In den drei übrigen Kombinationen liegt der Faktor bei 0,93 bis 0,95, also
> unter 1. Der gedeckelte Erstindex dauert auf nativer aarch64-Hardware **2 h 58
> min bis 4 h 09 min** statt der von der Recherche geschätzten 7 bis 24 Stunden.
> Der potion-Notausgang bleibt zu, die Phase läuft mit e5-small und dem
> 1.024-Token-Deckel weiter.

Dieselbe Aussage von der anderen Seite, weil ein Verdikt seine Reserve nennen
soll: die Zielbox dürfte gegenüber dem arm64-Läufer **um den Faktor 5,9
langsamer** sein (Charge 8, Sequenz 512) beziehungsweise **um den Faktor 8,0**
(Charge 2, Sequenz 256), bevor der gedeckelte Erstindex die 24 Stunden reißt.
Dass zwei gepinnte Neoverse-N2-Kerne schneller sind als zwei geteilte vCPU einer
kleinen Box, ist sicher; dass sie um mehr als das Sechsfache schneller sind, ist
es nicht. Der Abstand trägt die Entscheidung, die Nähe der Maschine zur Zielbox
trägt sie nicht.

**Was das Verdikt nicht sagt.** Es sagt nichts über die Dauer auf der Zielbox in
Stunden, und der Store-Text nach D-17a darf die 2 h 58 min bis 4 h 09 min deshalb
nicht als Zusage tragen. Es sagt nur, dass die Größe, an der die Phase hängen
könnte, sie nicht zum Kippen bringt.

### Messung C auf aarch64

**int8, 384 Byte je Vektor**

| Chunks | Gelesene Byte | warm p50 | warm p95 | kalt p50 | kalt p95 |
|---|---|---|---|---|---|
| 50.000 | 19,2 MB | 18,4 ms | 18,6 ms | 41,6 ms | 79,4 ms |
| **100.000** | **38,4 MB** | **37,5 ms** | **37,8 ms** | **92,0 ms** | **153,5 ms** |
| 250.000 | 96,0 MB | 93,1 ms | 93,6 ms | 240,1 ms | 251,1 ms |
| 1.000.000 | 384,0 MB | 347,5 ms | **348,4 ms** | 975,3 ms | **989,0 ms** |

**bit, 48 Byte je Vektor**

| Chunks | Gelesene Byte | warm p50 | warm p95 | kalt p50 | kalt p95 |
|---|---|---|---|---|---|
| 50.000 | 2,4 MB | 2,4 ms | 2,4 ms | 8,1 ms | 18,6 ms |
| **100.000** | **4,8 MB** | **4,8 ms** | **4,9 ms** | **13,5 ms** | **24,6 ms** |
| 250.000 | 12,0 MB | 12,6 ms | 12,9 ms | 34,0 ms | 75,7 ms |
| 1.000.000 | 48,0 MB | 52,5 ms | 52,8 ms | 162,2 ms | 211,5 ms |

Fett wie oben: die Zeile aus Erfolgskriterium 4 und jeder Wert über dem
Abbruchkriterium von 300 ms p95 je Runde. Das Verwerfen des Seitencaches ist auch
in diesem Lauf in jedem Fall gelungen, in beiden Speichertypen und auf beiden
Läufern: keine der vier `scan-latency`-Rohdateien trägt eine
`cold_not_enforced`-Zeile, und der Schritt "Say whether the cold series was
really cold" ist ohne Warnung durchgelaufen.

Vier Befunde im Abgleich mit der x86-Reihe oben:

1. **Der Befund "speicherbandbreitengebunden" ist bestätigt, und zwar
   überraschend genau.** Warm bei 1M rechnet der arm64-Läufer 384 MB in 347,5 ms,
   also **1,11 GB/s**; das Notebook lag bei 1,13 GB/s. Zwei völlig verschiedene
   Maschinen, zwei verschiedene Befehlssätze, derselbe Durchsatz auf zwei
   Nachkommastellen genau. Der amd64-Läufer fällt mit 0,66 GB/s deutlich dahinter
   zurück, was denselben geteilten Sockel meint wie bei Messung B.
2. **Die Linearität hält.** int8 warm: 18,4 / 37,5 / 93,1 / 347,5 ms für 50k /
   100k / 250k / 1M. Die Verdopplung der Chunkzahl verdoppelt die Zeit, die
   Stützstellen bleiben interpolierbar.
3. **Bit bringt auf ARM Faktor 6,6 statt 5,3**, gemessen bei 1M warm (347,5 gegen
   52,5 ms). Näher an der Schätzung aus 06-RESEARCH.md 2.3 als die
   Notebook-Zahl, aber immer noch nicht die dort genannten 8 bis 20. Der Befund
   "der Platzgewinn ist der volle Faktor 8, der Zeitgewinn ist es nicht" bleibt
   richtig.
4. **Die 250.000er-Schwelle fällt auf den beiden Maschinen verschieden aus, und
   das ist die einzige Stelle, an der sich die zwei Reihen widersprechen.** Auf
   dem Notebook riss der kalte Punkt bei 250.000 mit 372,7 ms das Kriterium; auf
   dem arm64-Läufer hält er mit 251,1 ms. Der Unterschied liegt nicht im
   Prozessor, sondern in der Platte: der Läufer hat eine NVMe-SSD, das Notebook
   eine WSL2-Datei darauf. **Die vorsichtige Lesart bleibt deshalb die aus dem
   Hauptteil**: 250.000 Chunks sind der Grenzpunkt, und eine von zwei gemessenen
   Maschinen reißt ihn kalt. Die Aussage für diese Phase ist davon nicht
   betroffen, weil sie bei 100.136 Chunks liegt.

### Ableitung 3 auf aarch64: Vektoranteil je Nutzersuche

Bei der Chunkzahl aus Ableitung 1 (100.136, gerechnet mit der Stützstelle
100.000), gegen `BUDGET_NANOSECONDS = 2_500_000_000` und `MAX_ROUNDS = 3`:

| Speichertyp | Cachezustand | p95 je Runde | gegen 300 ms | drei Runden | Anteil an 2,5 s |
|---|---|---|---|---|---|
| int8 | warm | 37,8 ms | 13 % | 113,3 ms | **4,5 %** |
| int8 | kalt | 153,5 ms | 51 % | 460,6 ms | **18,4 %** |
| bit | warm | 4,9 ms | 2 % | 14,8 ms | 0,6 % |
| bit | kalt | 24,6 ms | 8 % | 73,8 ms | 3,0 % |

**int8 mit brute force hält das Budget auch auf der Zielarchitektur**, warm um
den Faktor 7,9, kalt um den Faktor 2,0. Der kalte Fall ist auf ARM enger als auf
dem Notebook (51 statt 36 Prozent des Kriteriums), und zwar wegen der höheren
Streuung der kalten Reihe auf dem Läufer: der kalte p95 bei 100.000 liegt bei
153,5 ms, der schlechteste Einzelfall bei 566,0 ms. Ein Ausreißer unter hundert
Abfragen ist kein p95, aber er gehört genannt, weil er zeigt, wo die kalte Spalte
ihre Unruhe hat.

D-10 (Bit-Vektoren nicht bauen, nur dokumentieren) bleibt damit auch nach der
ARM-Messung die richtige Entscheidung, und der Abstraktionsschnitt aus D-08
bleibt aus demselben Grund richtig wie oben: bei einer Million Chunks reißt int8
auch auf ARM warm (348,4 ms), und bit hält dieselbe Million kalt bei 211,5 ms.

### Die Owner-Abnahme

**Am 05.09.2026 hat der Owner diesen Bericht abgenommen mit der Entscheidung
"weiter wie geplant" (Checkpoint Task 3 aus 06-02-PLAN.md, Variante 3a).** Die
Phase läuft mit e5-small und dem 1.024-Token-Deckel weiter, Plan 06-04 zurrt das
Schema fest. Der potion-Notausgang aus D-04 wurde nicht gezogen und D-04 selbst
nicht angetastet; die Regel bleibt so stehen, wie sie in 06-CONTEXT.md steht, und
dieser Bericht ist der Beleg, dass ihre Bedingung nicht eingetreten ist.

Die zweite Frage des Checkpoints (bleibt der Vektoranteil unter 300 ms p95 je
Runde?) ist mit 37,8 ms warm und 153,5 ms kalt bei der Chunkzahl dieser Phase
beantwortet. Die Wahl zwischen int8 und Bit-Vektoren wird damit nicht zur
Owner-Entscheidung, weil sie nicht gestellt werden muss.

### Die Rohdaten des Nachtrags

Im selben Verzeichnis `raw/`, unverändert so, wie das Werkzeug sie geschrieben
hat, mit den Präfixen `arm64-` für die Aussage und `runner-amd64-` für den
Vergleich. Das Präfix `runner-` unterscheidet den amd64-Läufer von den
bestehenden `amd64-`-Dateien, die vom lokalen x86-Notebook stammen und ein
anderes Abbild gemessen haben:

| Datei | Lauf |
|---|---|
| `arm64-machine.txt` | Maschine, Abbildkennung, `lscpu`, `free -m` |
| `arm64-chars-per-token-corpus.txt` | A über `testdata/corpus` |
| `arm64-chars-per-token-prosa.txt` | A über die deutschen Planungsunterlagen dieser Phase |
| `arm64-chars-per-token-wordlist.txt` | A über `/usr/share/dict/ngerman` |
| `arm64-tokens-per-second-b2-s256.txt` | B, Charge 2, Sequenz 256 |
| `arm64-tokens-per-second-b2-s512.txt` | B, Charge 2, Sequenz 512 |
| `arm64-tokens-per-second-b8-s256.txt` | B, Charge 8, Sequenz 256 |
| `arm64-tokens-per-second-b8-s512.txt` | B, Charge 8, Sequenz 512 |
| `arm64-scan-latency-int8.txt` | C, int8, warm und kalt, vier Größen |
| `arm64-scan-latency-bit.txt` | C, bit, warm und kalt, vier Größen |
| `runner-amd64-*.txt` | dieselben zehn Läufe auf `ubuntu-24.04` |

Die Kommandozeilen stehen nicht noch einmal hier, weil sie in diesem Fall keine
Handeingabe sind: sie stehen als Schritte "A, characters per token", "B, tokens
per second" und "C, scan latency" in `.github/workflows/measure.yml` bei Commit
`8d108a3`, und sie sind bis auf die Bind-Mount-Pfade dieselben wie die oben
abgedruckten.

### Was auch nach diesem Nachtrag offen bleibt

- **Die Zahl auf der Zielbox selbst.** Der arm64-Läufer hat dedizierte Kerne, die
  Zielbox hat geteilte vCPU. Beziffert ist der Abstand nicht, gedeckt ist er
  durch die Reserve von Faktor 5,9 bis 8,0 bis zur D-04-Schwelle.
- **Die RAM-Spitze beim Einbetten** (A5). Unverändert eine Schätzung; Messung B
  misst Zeit, nicht Speicher.
- **Der Qualitätsverlust von Bit-Vektoren** für e5-small auf Deutsch. Unverändert
  nicht belegt, und dieser Nachtrag misst wie der Hauptteil Zeit und Platz.
- **Wie viele Dokumente unter 1.024 Token liegen.** Ableitung 1 bleibt eine
  Obergrenze.
- **Ob `vec0` mit Metadaten- und Partitionsspalten schneller oder langsamer
  wird** (A8). Gemessen wurde auch hier eine nackte Vektortabelle.
