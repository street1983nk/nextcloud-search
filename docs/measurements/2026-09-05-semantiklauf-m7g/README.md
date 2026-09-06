# Der Volllauf mit Semantik auf der 4-GB-ARM-Box

**Stand: der Lauf ist durch, Ende erkannt am 06.09. um 06:15:09Z, Bericht
vollstaendig bis auf den Endungsvergleich, siehe unten.** Er wurde waehrend des
Laufs begonnen und nach seinem Ende aus den Rohdaten vervollstaendigt. Was hier steht, ist gemessen; was fehlt,
ist als fehlend benannt und nicht durch eine Hochrechnung ersetzt.

Messreihe zu Plan 06-11, Erfolgskriterium 5 der Phase 6. Der Vergleichslauf ohne
Semantik ist [`2026-09-04-volllauf-m7g`](../2026-09-04-volllauf-m7g/README.md),
dieselbe Box, derselbe Korpus, dasselbe Verfahren.

## Die Umgebung

| Angabe | Wert |
|---|---|
| Anbieter, Typ | AWS EC2, `m7g.large`, `eu-central-1c` |
| Architektur | aarch64, 2 vCPU (Graviton3) |
| Arbeitsspeicher | auf 4 GB begrenzt, `mem=4G` ueber `/etc/default/grub.d/99-mem4g.cfg` |
| Datentraeger | 60 GB gp3 als `/mnt/findling`, Docker- und containerd-Wurzel darauf |
| Nextcloud | AIO, Zugang ueber HaRP, `loadtest.infranode.dev` |
| Abbild der ExApp | `localhost:5000/findling_backend:06-11-arm`, auf der Box gebaut |
| Harte Grenze | `docker update --memory=2g --memory-swap=2g`, vom Kernel durchgesetzt |
| Kosten | 0,1158 USD je Stunde, laufend |

### Welcher Stand gemessen wird

Der Beweis ist nicht das Kennzeichen des Abbilds, denn ein Kennzeichen kann
jeder vergeben. Er ist ein Hash ueber jede Python-Datei des Pakets, mit
normalisierten Zeilenenden, einmal im Abbild und einmal im Arbeitsbaum
gerechnet, und die zwei muessen gleich sein.

| Groesse | Wert |
|---|---|
| Commit des Arbeitsbaums | `80f95a53b1c53e3ffde02c649a9a8c153771e5e5` |
| Baumhash `backend/src/findling`, im Abbild | `c83b5d7f743122c4be922078db879cad31d0bf23afc79fcbcdd0e57e91544d03` |
| Baumhash `backend/src/findling`, im Arbeitsbaum | `c83b5d7f743122c4be922078db879cad31d0bf23afc79fcbcdd0e57e91544d03` |
| Dateien im Paket | 50 |
| Baumhash `php` | `008f91238450a12edee010afe780f67a92221f5270d38b3589e88b27dfc0e35c`, 45 Dateien |

Rohdaten: [`40-abbild.log`](40-abbild.log).

### Dass die Semantik wirklich im Abbild ist, und nicht nur ihr Quelltext

| Pruefung | Ergebnis |
|---|---|
| Modellverzeichnis | `/usr/local/share/findling/model`, sechs Dateien, 137 MB |
| sha256 der int8-Datei | `8da4c9ba0ad59f58e8566839425d7fd6339d31414d0ce5cba2d7d0afb75dd8b6` |
| dieselbe Pruefsumme in Plan 06-03 | ja, [`2026-09-05-modellqualitaet`](../2026-09-05-modellqualitaet/README.md) |
| `vec0.so` | `/usr/local/lib/findling/vec0.so`, geladen, `vec_version` meldet `v0.1.9` |
| Einbettung ohne Netzwerk | `docker run --network none`, `available: true`, 384 Dimensionen |
| `HF_HUB_OFFLINE` | `1` |

Die Pruefsumme ist dieselbe, die Plan 06-03 dreimal gemessen und die der
Integrationslauf seit `f8acbb4` vergleicht. Sie steht hier zum vierten Mal und
diesmal auf der Zielhardware.

## Der Korpus

Der Korpus wurde **nicht neu gebaut**. Es sind dieselben 50.000 Dateien, die
Plan 05-21 gemessen hat; sie liegen seit dem 03.09. auf demselben Datentraeger.
Was zu zeigen war, ist, dass es noch dieselben Bytes sind, und dafuer wurde die
Listen-Pruefsumme mit der Regel des Generators nachgerechnet: sha256 ueber die
sortierten Zeilen `name,groesse,sha256`.

| Angabe | Gemessen am 05.09. | In `docs/performance.md` gefuehrt |
|---|---|---|
| Dateien | 50.000 | 50.000 |
| Bytes | 20.208.046.426 | 20.208.046.426 |
| Listen-Pruefsumme | `bcbef9b2cb067c2200df2a4a2e89408f690710983117d4e78328024046098a72` | dieselbe, Zeile "ARM-Volllauf" |

**Kein Befund.** Die Zahlen dieses Laufs sind mit denen aus Phase 5
vergleichbar, und das ist nachgerechnet und nicht angenommen. Rohdaten:
[`44-korpus.log`](44-korpus.log), Werkzeug:
[`skripte/44-korpus-pruefsumme.py`](skripte/44-korpus-pruefsumme.py).

Zu beachten beim Nachrechnen: die x86-Zeile derselben Tabelle nennt
`c03a8803...`. Gleicher Seed, gleiche Bytezahl, andere Pruefsumme, weil die
Schriftrasterung auf arm64 anders ausfaellt. Der Vergleichswert fuer diesen Lauf
ist die ARM-Zeile.

## DI-05-36: die Bewaffnung, bewiesen statt angenommen

Der gefaehrlichste Zustand dieser Box hat kein Warnzeichen. Ein Container, den
die Neustartregel von Docker hochbringt statt AppAPI, beantwortet Suchen und
indexiert nie wieder, und die Verwaltungsseite kann genau das nicht anzeigen
(DI-05-38). Beim Start der Box am 05.09. lag genau dieser Zustand vor:

```
docker logs nc_app_findling_backend --since <boot> | grep -c 'pass finished'
0
```

Null Durchgaenge des Pollers, bei einem Container, der seit dem Hochfahren
laeuft. Die Bewaffnung ist die Registrierung ueber AppAPI, und sie hinterlaesst
eine Spur, die man zaehlen kann:

```
INFO:findling:findling backend enabled
INFO:     172.18.0.6:51124 - "PUT /enabled?enabled=1 HTTP/1.1" 200 OK
WARNING:findling.worker.poller:the queue did not answer, next attempt in 15 s
```

Die dritte Zeile ist der Beweis und nicht die erste. Ein bewaffneter Poller
**fragt**, auch wenn niemand antwortet; der unbewaffnete fragt nicht. Zum
Zeitpunkt dieser Aufnahme war die PHP-Haelfte absichtlich abgeschaltet, also war
die richtige Antwort "keine Antwort", und sie kam nach 15, 30 und 300 Sekunden
wieder. Der Poller lebt.

Der zweite Teil des Beweises ist gezaehlte Arbeit. Neun Minuten nach dem Anstoss
des Laufs:

```
Durchgaenge des Pollers seit dem Start dieses Containers: 14
pass finished, claimed=32 indexed=32 skipped=0 failed=0 requeued=32 embedded=0 committed=32
pass finished, claimed=32 indexed=21 skipped=11 failed=0 requeued=32 embedded=0 committed=21
```

Vierzehn Durchgaenge gegen null im unbewaffneten Zustand, an derselben Zahl
gemessen. `requeued=32` ist die zweite Spur: jedes indexierte Dokument reist als
`embed`-Zeile weiter, und `embedded=0` ist an dieser Stelle richtig, weil
`embed` in der Reihenfolge der Arten zuletzt kommt und erst drankommt, wenn
keine Inhaltszeile mehr wartet.

Rohdaten: [`41-neuaufsatz.log`](41-neuaufsatz.log), [`00-start.txt`](00-start.txt).

## Der Neuaufsatz, und warum beide Haelften auf null mussten

Der Index von Plan 05-21 stand noch, mit 51.961 Dokumenten. Der Container
erkennt eine unveraenderte Datei an ihrer `file_id` und ueberspringt sie, also
haette ein Lauf gegen diesen Bestand die OCR-Spitze nie erzeugt, und genau sie
ist die eine Zahl, gegen die die Embedding-Spitze zu halten ist (IDX-08).

| Schritt | Wirkung |
|---|---|
| `occ findling:purge --now` | Tabellen, Hintergrundauftraege und Einstellungen der PHP-Haelfte |
| `occ app_api:app:unregister findling_backend --rm-data` | Container und Datenspeicher, also `state.db`, Tantivy-Index und `vectors.db` |
| `occ app_api:app:register ... --wait-finish` | der neue Container, ueber AppAPI, also bewaffnet |
| `docker update --memory=2g --memory-swap=2g` | die harte Grenze, die eine Registrierung nicht ueberlebt |

`memory.events` unmittelbar vor dem Lauf: alle sieben Zaehler auf null.

## Die Grundlast, und der Befund, der beim Scharfstellen dazwischenkam

Vor dem Lauf wurde die Grundlinie erhoben, so wie Plan 05-21 sie erhoben hat:
der Container laeuft, die PHP-Haelfte ist aus, keine Datei ist angefasst.

| Lauf | Abbild | anon im Leerlauf |
|---|---|---|
| 05-21, Volltext und OCR | `05-21-arm` | **58,7 MB** (erste Zeile von `volllauf.csv`) |
| 06-11, mit Semantik | `06-11-arm` | **691,8 MB** |

Das ist das Elffache, bevor eine einzige Datei angefasst wurde, und es ist die
Sorte Zahl, die man nicht in einen Bericht schreibt, ohne zu wissen, was sie
erzeugt. Zwei Erklaerungen waren moeglich: die Semantik kostet diese Grundlast,
oder der Unterschied liegt am Zustand des Datentraegers, weil 05-21 gegen ein
leeres Volumen startete und dieser Lauf gegen eines, in dem die Wortliste
bereits liegt.

### Das A/B, das die beiden unterscheidet

Abbild gewechselt, Zustand gehalten: dasselbe Volumen, dasselbe Nextcloud, nur
das alte Abbild ohne Semantik, danach zurueck.

| Runde | Abbild | anon im Leerlauf |
|---|---|---|
| A | `06-11-arm`, mit Semantik | 688,0 MB |
| B | `05-21-arm`, ohne Semantik | **93,5 MB** |
| A2, Gegenprobe | `06-11-arm` | 690,2 MB |

Beide Abbilder lesen dieselbe Wortliste mit 276.496 Eintraegen und bauen
denselben deutschen Automaten; das Protokoll zeigt es fuer beide Runden. Der
Unterschied ist das Abbild. **Die Semantik kostet rund 595 MB Grundlast, bevor
sie ein einziges Dokument einbettet.** Die 35 MB zwischen den 58,7 MB von 05-21
und den 93,5 MB von Runde B sind der Zustandsunterschied, den die zweite
Erklaerung vermutet hat; er ist real und er ist klein.

Rohdaten: [`51-ab-grundlinie.txt`](51-ab-grundlinie.txt),
[`50-grundlinie-woher.txt`](50-grundlinie-woher.txt).

### Wem die 595 MB gehoeren, Schritt fuer Schritt

Der Start wurde in der Reihenfolge nachgegangen, in der der Container ihn geht,
und `VmRSS` nach jedem Schritt gelesen. Die Differenz zweier Zeilen ist damit
der Preis genau einer Sache.

| Schritt | RSS danach | Zuwachs |
|---|---|---|
| leerer Prozess | 13,1 MB | |
| Module bis `findling.main` importiert | 111,3 MB | +98,2 MB |
| Wortliste gelesen, 276.496 Eintraege | 133,2 MB | +21,9 MB |
| deutscher Automat gebaut | 133,2 MB | +42,0 MB |
| **Tokenizer gelesen** (`tokenizer.json`, 17 MB) | **401,9 MB** | **+268,8 MB** |
| **Chunker gebaut und gefahren** (`make_splitter`) | **674,7 MB** | **+272,8 MB** |
| Modellobjekt gebaut (lazy, ohne Gewichte) | 674,7 MB | +0,0 MB |
| **erste Einbettung, Gewichte geladen** | **1.071,8 MB** | **+397,1 MB** |
| lange Einbettung, Aktivierungen | 1.098,2 MB | +26,4 MB |

Zwei Zahlen tragen die Grundlast, und keine von beiden ist das Modell: der
Tokenizer mit 268,8 MB und der Schneider mit 272,8 MB, zusammen 541,6 MB. Das
Modellobjekt selbst kostet null, solange nichts eingebettet wird, genau wie
`lazy_load` es verspricht.

Rohdaten: [`52-woher-die-grundlast.txt`](52-woher-die-grundlast.txt).

### Die Dauerlast der Modellgewichte, als eigene Zahl

Das ist der Posten, den die Formulierung "nie gleichzeitig" aus IDX-08 nicht
abdeckt. `INDEX_WORKERS=1` haelt die Aktivierungen des Einbettens von der
OCR-Spitze fern, aber die geladenen Gewichte liegen weiter im Speicher, waehrend
die OCR-Spitze entsteht.

| Posten | Wert | Woher |
|---|---|---|
| Gewichte, geladen bei der ersten Einbettung | 397,1 MB | Schritt 13 auf 14 |
| Aktivierungen einer langen Anfrage obendrauf | 26,4 MB | Schritt 14 auf 15 |
| Tokenizer und Schneider, Dauerlast ohne Modell | 541,6 MB | Schritt 10 auf 12 |

Rohdaten: [`49-modellgrundlast.txt`](49-modellgrundlast.txt).

## Das Ergebnis, aus den Rohdaten nach dem Lauf

### Beide Spuren sind durch, ohne OOM und ohne Neustart

| Ereignis (UTC) | Zeitpunkt | Quelle |
|---|---|---|
| Anstoss | 05.09. 10:47:54Z | `00-start.txt` |
| erster Vektor | vor 10:59:49Z (32 eingebettet) | `statusseite.jsonl` |
| erste Spur fertig (51.961 indexiert) | 06.09. zwischen 04:50:57Z und 04:52:58Z | `statusseite.jsonl` |
| zweite Spur fertig (51.961 eingebettet) | 06.09. zwischen 05:43:10Z und 05:45:10Z | `statusseite.jsonl` |
| Ende erkannt, Abschluss gestartet | 06.09. 06:15:09Z | `00-ende.txt` |
| Weckdatei geschrieben, ntfy http=200 | 06.09. 06:20:32Z | `00-FERTIG`, `99-ntfy-watch.log` |

| Dauer | Wert | Vergleich 05-21 (ohne Semantik) |
|---|---|---|
| erste Spur, Volltext und OCR, mit Einbettung nebenher | **18 h 04 min** (auf 2 min genau) | 12 h 49 min |
| beide Spuren bis zum letzten Vektor | **18 h 56 min** | |
| Einbettung neben der OCR | rund 43 Dokumente je Minute | |
| Einbettung allein, nach dem Ende der ersten Spur | rund 170 Dokumente je Minute | |

Die erste Spur ist mit der Semantik nebenher um 5 h 15 min laenger geworden,
das sind 41 Prozent, weil `INDEX_WORKERS=1` beide Spuren durch denselben
Arbeiter zieht und jede `embed`-Zeile OCR-Zeit kostet. Der Nachlauf der zweiten
Spur nach der ersten war mit 52 Minuten kurz, weil sie den groessten Teil der
Arbeit schon parallel erledigt hatte.

### memory.events und die Spitzen, vor jedem Eingriff erhoben

`07-oom-beweis.txt`, geschrieben 06:15:32Z vom Waechter, bevor irgendetwas
angefasst wurde:

| Zaehler | Wert |
|---|---|
| low, high | 0, 0 |
| **max** | **2796** |
| oom, oom_kill, oom_group_kill | **0, 0, 0** |
| sock_throttled | 3044 |
| OOMKilled, RestartCount | false, 0; `StartedAt` unveraendert 05.09. 10:44:39Z |
| memory.max / memory.peak / memory.current am Ende | 2.147.483.648 / 2.147.741.696 (Vorbehalt oben) / 2.030.563.328 |

Die Reihe des Samplers (`semantiklauf.csv`, 13.983 Aufnahmen im Abstand von
5 s), geteilt an der Grenze der ersten Spur (04:52Z):

| Groesse | ganzer Lauf | Phase A: Volltext, OCR, Einbettung nebenher | Phase B: nur Einbettung (ab 04:52Z) |
|---|---|---|---|
| Aufnahmen | 13.981 | 12.994 | 987 |
| **anon-Spitze** | **1.837,8 MB** um 05:34:05Z | 1.562,7 MB um 01:49:29Z | **1.837,8 MB** um 05:34:05Z |
| memory.current-Spitze | 2.048,0 MB um 05:15:11Z | 2.047,9 MB um 05.09. 11:46:16Z | 2.048,0 MB um 05:15:11Z |
| Aufnahmen mit current >= 2.140 MB, also an der Grenze | 61 (5,1 min) | 2 | 59 (4,9 min) |

**Kriterium 5, Teil 1 (anon-Spitze unter 2,0 GB): erfuellt, 1.837,8 MB.**
**Kriterium 5, Teil 2 (memory.events mit lauter Nullen): nicht erfuellt, `max`
steht bei 2796.** Die drei Zaehler, die einen Schaden anzeigen (oom, oom_kill,
oom_group_kill), stehen auf null, der Container hat den ganzen Lauf ohne
Neustart durchgehalten, und beide Spuren sind vollstaendig. `max` zaehlt, wie
oft die cgroup an ihrer harten Grenze zurueckfordern musste; hier war es der
Dateicache des Index (`file` bis 359 MB), der bei einem `anon` von 1,5 bis
1,8 GB gegen die 2 GB anlag. Das ist kein Fehler des Containers, aber es ist auch
keine Null, und die Formulierung des Kriteriums hat die Null verlangt. Der
Bericht rechnet es deshalb als **nicht erfuellt** und legt die Bewertung dem
Betreiber vor, mit dem Vorschlag, das Kriterium fuer die Store-Aussage auf die
drei Schadenszaehler und die anon-Spitze zu stellen und `max` als Kennzahl mit
auszuweisen. Was `max` wirklich sagt: der Container laeuft auf dieser Box mit
rund 210 MB Abstand zur harten Grenze, und das ist wenig.

### Der Befund, der die Spitze erklaert: die Suche laedt ein zweites Modell

Die anon-Spitze liegt nicht in der OCR-Phase, gegen die IDX-08 sie halten
wollte, sondern in Phase B, und sie beginnt auf die Sekunde mit der
Suchlastprobe: `anon >= 1.700 MB` zum ersten Mal um **05:15:11Z**, die Probe
startete 05:15:09Z. Vorher stand `anon` seit Stunden zwischen 1.450 und
1.563 MB, danach bis zum Ende des Laufs nie mehr darunter, und `memory.current`
ging in derselben Sekunde an die Grenze. Von den 2796 `max`-Ereignissen fielen
1292 in die letzte Stunde nach der Probe (1504 standen um 05:12Z).

Die Ursache steht im Code und ist Absicht: `EmbeddingModel` ist "not a module
level singleton", der Arbeiter der zweiten Spur baut in `worker/poller.py` seine
Instanz, und die Leseseite baut in `api/resources.py` eine zweite, beide im
selben Prozess (`findling.main`, 1.755,6 MB RSS nach dem Lauf; der
Spawn-Kindprozess traegt 69 MB). Die erste Suche mit semantischem Anteil laedt
Tokenizer und onnxruntime-Sitzung ein zweites Mal, und der Preis bleibt liegen:
**gemessen +276 MB dauerhaft** (1.562,7 nach 1.837,8 MB, Spitze), rund 1.750 MB
noch eine Stunde spaeter im Leerlauf. Dazu liest die Suchseite bei der ersten
Anfrage die Wortliste erneut (`constituent list read from the volume` um
05:15Z; `build_artifact` in `index/wordlist.py` hat keinen Cache). **Korrektur
06.09., Research zu Phase 06.1:** der deutsche Zerlegungsautomat selbst wird NICHT
zweimal gebaut, `_CACHED_GERMAN` in `index/analyzer.py` ist ein prozessweiter
Cache mit Zaehler und Test. Doppelt liegen Tokenizer und onnxruntime-Sitzung,
dazu das zweite Lesen der Wortliste (21,9 MB laut Aufschluesselung), nicht die
42 MB des Automaten. Die erste Fassung dieses Absatzes hatte die Log-Zeile als
Automatenbeweis gelesen.

Das ist der wichtigste Befund dieses Laufs fuer die Haertung vor der Abgabe:
ein Container, der indexiert UND gesucht wird, was der Normalfall jeder
Installation ist, traegt zwei Saetze Modellgewichte und Tokenizer. Eine
gemeinsame Engine fuer beide Seiten, oder ein Entladen der Suchseite nach
Leerlauf, spart auf dieser Box einen dreistelligen MB-Betrag gegen eine harte
Grenze, an der 210 MB uebrig sind. Aufgenommen fuer die Launch-Haertungsphase
(Owner-Regel 06.09.), kein Fix in diesem Plan.

### Die Suche bleibt benutzbar, waehrend und nach dem Lauf

Beide Proben mit `45-suchlast.py`, je 30 echte Nutzersuchen ueber die OCS-Route
(`File contents`, gemischt lexikalisch und umschreibend), Budget 2.500 ms aus
`Provider.php`:

| Probe | Zeitpunkt | p50 | **p95** | max | haelt |
|---|---|---|---|---|---|
| im Nachlauf, zweite Spur laeuft (Vorrat 4.775) | 06.09. 05:15Z | 735,5 ms | **1.129,0 ms** | 2.065 ms | ja |
| nach dem Lauf, voller Vektorbestand | 06.09. 06:15Z | 478,5 ms | **524,0 ms** | 525 ms | ja |

Rohdaten: `46-suchlast-nachlauf.json`, `47-suchlast-danach.json`. Der Vektorscan
lief bei jeder semantischen Anfrage an seinen eigenen Deckel (`the vector scan
hit its own ceiling and answered a truncated neighbour list`), also mit
gekappter Nachbarliste, wie fuer 145.854 Vektoren im Brute-Force-Pfad zu
erwarten; die Antwortzeit haelt trotzdem mit Abstand.

`memory.current` gegen `anon` waehrend der Suchlast nach dem Lauf: vor der Probe
1.833,6 MB anon bei 2.019,2 MB current, waehrend der Probe hoechstens 1.748,7 MB
anon bei 1.936,5 MB current. Der Dateicache-Posten des Vektorscans steht damit
mit beiden Zahlen da; er ist klein (64 MB Vektordatei) gegen den des
Tantivy-Index.

### Byte je Dokument, gemessen gegen gerechnet

`48-vektorbestand.txt`, gemessen im Container nach dem Lauf, Datei und WAL
zusammen (die erste Messung des Waechters scheiterte an einem Spaltennamen im
Skript, `verdict` statt `state`; korrigiert und um 06:39:49Z nachgemessen, am
unveraenderten Container):

| Groesse | Wert |
|---|---|
| `vectors.db` + WAL | 64.098.304 + 4.544.200 = 68.642.504 Byte |
| Chunks | 145.854, also 2,807 je Dokument |
| Dokumente mit Vektor | 51.961 (alle indexierten) |
| **Byte je Dokument** | **1.321,0** |
| in Plan 06-04 gemessen (kleiner Korpus) / geschaetzt | 876,0 / 864 |
| Tantivy-Index | 785.308.851 Byte, 15.113 Byte je Dokument |
| Vektoren im Verhaeltnis zum Index | 8,74 Prozent |
| Zeichen im Korpus | 1.397.354.875 |

Die gemessene Zahl liegt 51 Prozent ueber der aus 06-04. Der Unterschied
kommt aus den Chunks je Dokument: 2,807 hier gegen den Zwei-Chunk-Deckel, mit
dem 06-04 gerechnet hat. Fuer die Store-Aussage gilt die grosse Zahl.

### Verdikte, und was offen bleibt

| Verdikt | Anzahl | Grund |
|---|---|---|
| indexed | 51.961 | |
| skipped | 37 | 21 too_large, 14 empty_text, 2 image_not_ocrable |
| failed | **0** | |

Derselbe Bestand wie der Index aus 05-21 (51.961 Dokumente). Der Vergleich der
Verdikte gegen die Verteilung des Generators, Endung fuer Endung, ist **nicht
gemacht**; er braucht die Endungstabelle des Generators neben `state.db` und
gehoert in die Abnahme oder die Haertungsphase. Er steht hier als fehlend und
nicht als erledigt.

### Kosten und Verbleib der Box

Die Box laeuft weiter, 0,1158 USD je Stunde, bis der Betreiber den Bericht
abnimmt ("bericht abgenommen, box abbauen", Plan 06-11 Task 4). Der Container
ist seit dem Lauf unangetastet, damit der Betreiber die Verwaltungsseite und die
cgroup selbst ansehen kann.

## Der Anstoss, und die Gegenprobe, die zu frueh kam

| Zeitpunkt (UTC) | Ereignis |
|---|---|
| 2026-09-05T10:47:54Z | `occ app:enable findling`, die App ist an, die Beobachter laufen seit 10:47:44Z |
| 10:51:52Z | erster Hintergrundauftrag der App |
| 10:53:55Z | Gegenprobe des Skripts: Vorrat 0, Urteil **PRUEFUNG ROT** |
| 10:54:47Z | Vorrat 549 |
| 10:56:19Z | erster Anspruch beim Arbeiter, 32 Zeilen |
| 10:56:40Z | acht Durchgaenge, die ersten Verdikte |

Die Gegenprobe des Skripts hat den Lauf fuer tot erklaert, und sie lag um
**52 Sekunden** daneben. Die sechs Minuten Wartezeit waren aus dem Rueckzug des
Pollers hergeleitet (bis zu 300 s, nachdem die PHP-Haelfte zwischen `purge` und
`enable` weg war), aber der Crawl haengt an einer zweiten Uhr: AIO ruft
`cron.php` alle fuenf Minuten, und der erste Auftrag reiht noch nichts ein.
Zwischen dem ersten und dem zweiten Auftrag lag der Zeitpunkt der Gegenprobe.

Das Urteil steht unveraendert in [`00-start.txt`](00-start.txt), mit dem
Nachtrag darunter, der es widerlegt. Es steht dort, weil ein Skript, das den
Lauf fuer tot erklaert, waehrend er anlaeuft, beim naechsten Mal wieder so
urteilen wird, und weil die Lehre allgemein ist: eine Wartefrist muss gegen die
langsamste beteiligte Uhr bemessen sein und nicht gegen die, an die man gerade
gedacht hat.

## Die Korrektur waehrend des Laufs, am Morgen des 06.09.

Der Waechter hat die Nacht durchgehalten und dabei in jeder Runde dieselbe
falsche Zahl protokolliert: `indexed=0 embedded=0`, waehrend der Container
laengst bei 47.000 Vektoren stand. Ursache ist `42c-lesen.py`, das beide Zahlen
auf der obersten Ebene der Aufnahme gesucht hat; dort steht `indexed` der
PHP-Haelfte, das per Bauart 0 bleibt, und `embedded` gar nicht. Beide leben
unter `backend`. Zwei Folgen, beide um 05:12Z beim ersten Blick des Morgens
gefunden:

1. Die Suchlastprobe im Nachlauf (Bedingung `embedded > 200`) ist nie
   gefahren. Sie wurde um 05:15:09Z von Hand gestartet, mit demselben Skript
   `45-suchlast.py`, waehrend die zweite Spur noch lief (Vorrat 4.775, 47.186
   von 51.961 eingebettet). Ergebnis in `46-suchlast-nachlauf.json`:
   30 Suchen, p50 735,5 ms, p95 **1.129,0 ms**, max 2.065 ms, Budget 2.500 ms,
   haelt.
2. Das Ende haette der Waechter nie erkannt (`SUCHLAST_GEFAHREN` blieb 0), er
   waere erst am Deckel von 340 Runden, rund neun Stunden nach dem echten Ende,
   in den Abschluss gelaufen. Der Leser wurde auf der Box gepatcht (Original als
   `42c-lesen.py.orig`), der alte Waechter per PID beendet und als
   `42b-wachter-neu.sh` mit `SUCHLAST_GEFAHREN=1` neu gestartet. Der neue
   Waechter las in Runde 1 richtig: `vorrat=4775 indexed=51961 embedded=47186`.

Der Lauf selbst war zu keinem Zeitpunkt betroffen; Sampler und Statusbeobachter
liefen unveraendert weiter. Die Korrektur steht auf der Box in
`42e-korrektur.txt` und im Waechterlog mit Zeitstempel. Die Fassung von
`42c-lesen.py` unter `skripte/` ist die korrigierte.

**Lehre:** ein Waechter, der eine Zahl in jeder Runde protokolliert, muss beim
Scharfstellen einmal gegen eine bekannte Zahl gelesen werden. `embedded=0` in
Runde 10, neun Minuten nach 14 Poller-Durchgaengen mit `requeued=32`, war zu
sehen gewesen. Die 52 Sekunden der Gegenprobe weiter oben und diese Zeile sind
dieselbe Lehre in zwei Kleidern: die Pruefung des Laufs gehoert selbst geprueft.

### Zwischenstand der Nacht, gelesen um 05:13Z

| Groesse | Wert |
|---|---|
| Volltext und OCR | fertig, 51.961 indexiert, 0 fehlgeschlagen, 37 uebersprungen (21 too_large, 14 empty_text, 2 image_not_ocrable) |
| Einbettung | 46.853 von 51.961, Vorrat 5.103, rund 170 je Minute seit die erste Spur frei ist |
| anon-Spitze bisher | 1.562,7 MB um 01:49:29Z |
| memory.current-Spitze | 2.047,9 MB um 11:46:16Z am 05.09., an der harten Grenze |
| memory.events | low 0, high 0, **max 1504**, oom 0, oom_kill 0, oom_group_kill 0 |
| Container | RestartCount 0, OOMKilled false, StartedAt unveraendert 10:44:39Z |

`max 1504` ist kein OOM und kein Neustart, aber es ist auch keine Null: die
cgroup hat 1.504-mal an der harten Grenze zurueckfordern muessen, waehrend
`memory.current` mit dem Dateicache des Index an den 2 GB anlag. Was das fuer
Kriterium 5 ("memory.events mit lauter Nullen") bedeutet, entscheidet die
Abnahme nach dem Ende des Laufs, mit den vollstaendigen Reihen; der Befund wird
hier nicht kleingeredet.

## Die Beobachter

| Datei | Was darin steht | Abstand |
|---|---|---|
| `semantiklauf.csv` | Zeitstempel, anon, file, slab, current, peak der cgroup | 5 s |
| `statusseite.jsonl` | die Verwaltungsseite, ohne Namenstraeger, mit `indexed` und `embedded` | 120 s |
| `42b-wachter.log` | die Runden des Waechters, mit beiden Spuren getrennt | 300 s |
| `99-ntfy-watch.log` | die Sendeversuche der Meldekette, mit ihrem HTTP-Code | 300 s |

Der Statusbeobachter nimmt alle 120 Sekunden auf und nicht alle 300 wie in
05-21. Aus seiner Reihe kommt die Grenze zwischen den beiden Spuren, und eine
Phasendauer, die auf fuenf Minuten genau ist, waere eine Schaetzung mit
Nachkommastelle.

### Die Meldekette meldet nicht, und das steht hier statt nirgends

`https://ntfy.infranode.dev/infranode-alerts-f43ceefc1193` hat am 04.09. den
Abschluss des Volltextlaufs gemeldet und antwortet am 05.09. von derselben Box
mit **HTTP 403**:

```
{"code":40301,"http":403,"error":"forbidden"}
```

Der Server selbst ist erreichbar (die Wurzel antwortet mit 200), das Thema
verweigert die Annahme. Die Box hat beim Neustart eine neue oeffentliche Adresse
bekommen; das Ziel gehoert zu einer fremden Infrastruktur und wurde deshalb
nicht angefasst. Zwei Folgen, und beide sind Absicht:

1. Der Waechter sendet weiter und **protokolliert den HTTP-Code jedes Versuchs**.
   Eine Meldekette, die still nicht meldet, ist schlimmer als keine, weil man
   sich auf sie verlaesst.
2. Der eigentliche Vertrag ist eine Datei: `00-FERTIG` im Laufverzeichnis, mit
   Zeitpunkt, Dauer und Weckwort. Sie liegt im Dateisystem und haengt an keinem
   fremden Dienst.

## Die Skripte

Alle Skripte dieses Laufs liegen unter [`skripte/`](skripte/), in der
Reihenfolge ihrer Nummern. Sie sind englisch kommentiert, wie der uebrige Code
dieses Projekts, und jedes sagt in seinem Kopf, warum es tut, was es tut.
