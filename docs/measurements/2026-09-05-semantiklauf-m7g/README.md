# Der Volllauf mit Semantik auf der 4-GB-ARM-Box

**Stand: der Lauf laeuft.** Dieser Bericht wird waehrend des Laufs geschrieben
und nach seinem Ende vervollstaendigt. Was hier steht, ist gemessen; was fehlt,
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

## Was noch fehlt

Diese Abschnitte werden nach dem Ende des Laufs gefuellt, aus den Rohdaten, die
die Beobachter gerade schreiben:

- **anon-Spitze ueber den ganzen Lauf**, dazu getrennt die Spitze der OCR-Phase
  und die der Embedding-Phase. Die Trennung ist der Beleg fuer IDX-08.
- **`memory.events`, alle Zaehler**, nach dem Lauf und vor jedem Eingriff.
- **Dauer je Spur**, aus dem Zeitstempelverlauf des Statusbeobachters: Volltext
  und OCR bis zum letzten Verdikt, Einbettung bis zum letzten Vektor.
- **Byte je Dokument, gemessen**, gegen die in Plan 06-04 gerechnete Zahl.
- **`memory.current` gegen `anon` waehrend einer Suchlast**, damit der
  Dateicache-Posten mit beiden Zahlen dasteht und nicht mit der guenstigeren.
- **p95 einer Nutzersuche waehrend des Nachlaufs**, gegen 2,5 Sekunden.
- **Verdikte gegen die Verteilung des Generators**, Endung fuer Endung.

### Eine Einschraenkung, die vorab benannt gehoert

`memory.peak` der cgroup liess sich auf diesem Kernel nicht zuruecksetzen
(`echo 0 > memory.peak` bleibt wirkungslos). Der Wert traegt deshalb die
Vorbereitungsmessungen dieses Berichts mit, insbesondere den Diagnoseprozess,
der die Gewichte geladen hat: vor dem Anstoss des Laufs stand er bereits bei
2.043.817.984 Byte. **Die tragende Zahl dieses Berichts ist `anon` aus der
Messreihe des Samplers**, wie in 05-21, und nicht `memory.peak`. Wo `peak`
vorkommt, steht diese Einschraenkung daneben.

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
