# Der Messbericht: was Findling auf einer 4-GB-ARM-Box braucht

Diese Seite beantwortet die Frage, die ein Selfhoster wirklich hat, bevor er eine
Suche auf seinen Server lässt: passt das noch neben mein Nextcloud, oder holt mir
der Kernel in der dritten Nacht den Container weg. Sie ist deshalb für zwei Leser
geschrieben. Für den Betreiber, der wissen will, ob seine kleinste Maschine
reicht, und der eine Zahl erst glaubt, wenn er weiß, wie sie zustande kam. Und
für den Entwickler, der in einem Jahr eine Zahl aus dieser Seite neben eine
andere aus dem Docker-Client legt, die doppelt so hoch ist, und der sonst
annehmen müsste, eine der beiden sei falsch.

Der Aufbau ist Absicht: erst die Umgebung, dann die Methode, dann die Grenzen,
und erst danach Zahlen. Eine Methode, die nach den Ergebnissen geschrieben wird,
passt immer zu ihnen.

## Stand dieses Berichts

| Abschnitt | Zustand | Stand |
|---|---|---|
| Umgebung und Kosten | aus der Konto-API abgefragt | 2026-09-03 |
| Methode | steht | 2026-09-03 |
| Grenzen | steht | 2026-09-03 |
| Grenzwert für den Spitzenwert | festgelegt | 2026-09-03 |
| AIO-Grundlast ohne Findling | FEHLT NOCH | siehe unten |
| Findling im Volllauf, 50.000 Dateien | FEHLT NOCH | Pläne 05-12 und 05-14 |
| Störfall-Drills | FEHLT NOCH | Plan 05-14 |

Die drei fehlenden Abschnitte sind hier ausdrücklich als fehlend benannt und
nicht ausgelassen. Was fehlt, ist bis heute nicht gemessen worden, und die
Ursache steht im nächsten Abschnitt: die Zielhardware war am 03.09.2026 bei
Hetzner in keiner Region zu mieten.

## Die Umgebung

### Die Zielhardware

| Posten | Wert |
|---|---|
| Server | Hetzner CAX11, Ampere ARM |
| Architektur | arm64 |
| Kerne | 2 vCPU, geteilt |
| Arbeitsspeicher | 4 GB |
| Systemplatte | 40 GB |
| Zusatzplatte | Volume, 50 GB, ext4 |
| Region | hel1, Helsinki |
| Betriebssystem | Ubuntu 24.04 LTS, arm64 |
| Nextcloud | All-in-One über HaRP, Postgres aus dem AIO-Paket |
| Inbegriffener Verkehr | 20 TB je Monat |

Die 50 GB kommen nicht aus Bequemlichkeit dazu: der Lastkorpus wiegt 20,12 GB,
daneben liegen der Index und die Abbilder der Container, und 40 GB Systemplatte
wären damit voll. Das Docker-Datenverzeichnis und das Nextcloud-Datenverzeichnis
liegen deshalb beide auf dem Volume, und zwar bevor AIO zum ersten Mal startet:
`NEXTCLOUD_DATADIR` lässt sich nach der Installation nicht mehr ändern.

### Was die Umgebung kostet

Abgefragt am 03.09.2026 um 10:48 UTC gegen `/v1/pricing` und `/v1/server_types`
dieses Kontos, also nicht aus einer Preisliste im Netz. Alle Werte brutto, der
Mehrwertsteuersatz des Kontos beträgt 19 Prozent.

| Posten | je Stunde | je Monat |
|---|---|---|
| CAX11 in hel1 | 0,011424 EUR | 7,1281 EUR |
| Volume, 50 GB | 0,004662 EUR | 3,4034 EUR |
| Primäre IPv4 | 0,000952 EUR | 0,5950 EUR |
| Summe | 0,017038 EUR | 11,1265 EUR |

Zwei Dinge daran sind leicht zu übersehen. Der Preis je GB und Monat des Volumes
wird oft mit 0,057 EUR angegeben; das ist der Nettowert, brutto sind es
0,068068 EUR. Und die öffentliche Adresse steht seit 2024 als eigener Posten auf
der Rechnung. Sie macht gegen eine Box für gut einen Cent je Stunde rund acht
Prozent aus, weshalb `scripts/ops/hetzner_box.sh status` sie mitrechnet.

Ein Lauf über zwei Tage kostet damit rund 0,82 EUR. Die Miete endet mit dem Test:
die Löschung der Box ist ein Pflichtschritt und kein Aufräumen bei Gelegenheit,
denn eine vergessene Box ist eine öffentlich erreichbare Nextcloud mit
Admin-Zugang und eine monatliche Rechnung.

### Warum hier noch keine Messung steht

Am 03.09.2026 waren alle vier ARM-Typen des Anbieters in allen drei europäischen
Regionen ohne Bestand:

```
name     cores  memory   disk arch     price per month, gross     in stock
cax11        2      4 G    40 G arm      7.1281000000000000         nowhere
cax21        4      8 G    80 G arm      12.4831000000000000        nowhere
cax31        8     16 G   160 G arm      24.9781000000000000        nowhere
cax41       16     32 G   320 G arm      48.7781000000000000        nowhere
```

Die x86-Typen desselben Kontos waren zur selben Minute verfügbar, es handelt sich
also nicht um eine Sperre des Kontos, sondern um die Knappheit der ARM-Maschinen.

Diese Stelle ist auch für den nächsten Leser eine Falle, und deshalb steht sie
hier: die API beantwortet den Erzeugungsversuch mit `invalid_input: unsupported
location for server type`. Die Meldung nennt die Region und meint den Bestand.
Sie erscheint für jede Region und sogar ohne Regionsangabe, und sie hat nichts
mit dem Aufruf zu tun. Die Wahrheit steht am Server-Typ selbst, im Feld
`locations[].available`. `scripts/ops/hetzner_box.sh` liest seit diesem Bericht
genau dieses Feld, bevor es etwas anlegt, und `prices` zeigt den Bestand in einer
eigenen Spalte.

## Die Methode

### Was gemessen wird, und warum ausgerechnet das

Gemessen wird `anon` aus `memory.stat` der cgroup des jeweiligen Containers, und
die Begründung dafür ist dieselbe, die im Kopf von `scripts/ops/rss_sampler.sh`
steht:

`anon` ist die Menge Speicher in anonymen Abbildungen, also genau der Haldenanteil,
den `INDEX_WORKERS=1`, der Schreibpuffer von Tantivy und tesseract erzeugen.
`memory.current` und `memory.peak` zählen den Dateicache dazu, und der
Tantivy-Index ist eine Abbildung einer Datei im Speicher, also landet jeder
gelesene Indexblock im Dateicache derselben cgroup. Auf einem Korpus von 20 GB ist
dieser Cache der größte Einzelposten der Zahl, und er ist vollständig
zurückforderbar, weshalb eine Store-Aussage aus `memory.peak` die Anwendung
schlechter darstellen würde, als sie ist. Aufgezeichnet werden beide trotzdem,
denn der erste Leser, der den Docker-Client nach dem Speicher des Containers
fragt, bekommt eine Zahl auf Basis von `memory.current` und soll diesen
Unterschied erklärt finden statt versteckt.

### Womit gemessen wird

`scripts/ops/rss_sampler.sh` liest die cgroup-Dateien selbst, im Abstand von fünf
Sekunden, und schreibt eine Zeile je Messpunkt mit `timestamp`, `anon`, `file`,
`slab`, `current` und `peak`. Jede Zeile trägt das feste Präfix `findling-rss`,
damit sich die Messung aus einem Protokoll herausfiltern lässt, das auch alles
andere enthält:

```
grep '^findling-rss ' run.log | cut -d' ' -f2- > rss.csv
```

Die Abschlusszeile nennt den höchsten beobachteten `anon`-Wert, den finalen
`memory.peak`, den Inhalt von `memory.events` und das Feld `.State.OOMKilled` des
Containers. Diese vier zusammen sind der Beweis, dass es keinen Speichertod gab.
Eine Textsuche nach "Killed" im Protokoll ist dieser Beweis ausdrücklich nicht:
sie findet den Fall nicht, in dem ein Kindprozess der cgroup gestorben ist.

Der Sampler schreibt lieber nichts als Nullen. Eine Reihe Nullen in einem Bericht
sieht aus wie eine Messung, und das ist schlimmer als eine fehlende Datei.

### Der Grenzwert, gegen den geprüft wird

Bestanden heißt: der Volllauf über 50.000 Dateien läuft ohne Speichertod durch,
UND der höchste `anon`-Wert des Findling-Containers bleibt unter **2,0 GB**.

Die Zahl ist eine Festlegung und keine Messung, deshalb hier ihre Rechnung. Die
Box hat 4 GB. Die ungünstigste gleichzeitige Lage der Findling-Posten liegt nach
der Vorabrechnung bei 1,6 bis 1,7 GB. Daneben muss die AIO-Grundlast Platz haben,
für die 0,7 bis 1,1 GB veranschlagt sind, und darüber noch etwas Luft für den
Seitencache und den Kernel selbst. 2,0 GB lassen der Grundlast im schlechtesten
Fall knapp zwei GB und liegen damit unter der Größenordnung von 2,5 GB, die als
Rahmen vorgegeben war. Das ist Absicht: 2,5 GB wären neben einer Grundlast von
1,1 GB auf einer 4-GB-Box keine Zusage, sondern eine Wette.

Der Sampler fällt dieses Urteil nicht selbst. Er nennt Zahlen, und der Vergleich
mit dem Grenzwert steht hier.

## Die Grenzen dieses Berichts

Die Regel dieses Repositories lautet, zu jeder Aussage ihre Grenze zu nennen.
Für diesen Bericht sind das sechs:

1. **Eine Box ist keine Aussage über alle Boxen.** Gemessen wird auf einer
   einzelnen gemieteten CAX11. Geteilte Kerne bedeuten wechselnde Nachbarn, und
   eine andere 4-GB-Maschine mit anderer Platte kann andere Laufzeiten liefern.
   Übertragbar ist der Speicherverlauf, nicht die Uhr.
2. **`anon` ist nicht das, was der Docker-Client anzeigt.** Wer die Zahl dieses
   Berichts neben dessen Anzeige legt, wird eine deutlich höhere finden. Der
   Unterschied ist der Dateicache des Index, er ist zurückforderbar, und der
   Grund für diese Wahl steht oben.
3. **Der OCR-Anteil wird auf ARM gemessen und nicht hochgerechnet.** Bis diese
   Messung vorliegt, ist jede Angabe zur Laufzeit des Volllaufs eine Schätzung.
4. **Die Grundlast hängt an der Auswahl der optionalen AIO-Container.** Gemessen
   wird mit genau einem zugeschalteten Container, HaRP, weil Findling ihn
   braucht. Wer Talk, Collabora, Imaginary oder die Volltextsuche dazuschaltet,
   verschiebt die Grundlast und damit den Abstand zum Grenzwert.
5. **Der Korpus ist synthetisch.** 50.000 Dateien aus einem Seed, in der
   Verteilung echter Bestände, aber ohne ein einziges echtes Dokument. Das ist
   für die Speicherfrage die bessere Wahl, weil der Lauf reproduzierbar bleibt;
   für Aussagen über Trefferqualität taugt er nicht.
6. **Das Zertifikat.** Der Lauf verwendet eine echte Subdomain, damit AIO ein
   gültiges Zertifikat bekommt. Sollte stattdessen der Rückfall
   `SKIP_DOMAIN_VALIDATION` mit einem selbstsignierten Zertifikat nötig werden,
   steht das hier, zusammen mit dem Satz, was damit nicht bewiesen ist.

## Die AIO-Grundlast ohne Findling

FEHLT NOCH. Diese Zahl ist der Bezugspunkt des ganzen Berichts, denn ohne sie
sagt eine Findling-Kurve nichts darüber, ob die Box insgesamt reicht.

Gemessen wird sie, bevor Findling die Maschine zum ersten Mal anfasst: mindestens
dreißig Minuten mit demselben Sampler, über alle laufenden AIO-Container, mit
einer Phase im Leerlauf und einer Phase mit einer Handvoll gewöhnlicher Aufrufe
der Weboberfläche. Ergebnis sind die Summe der `anon`-Werte über die Container
und der höchste beobachtete Stand, dazu die Liste der Container, die dabei
liefen. Nach dem Zuschalten von HaRP wird kurz nachgemessen, damit der Beitrag
dieses einen Containers getrennt ausgewiesen ist.

Bis dahin gilt die Vorabrechnung von 0,7 bis 1,1 GB, und sie ist ausdrücklich
geschätzt und nicht gemessen.

## Findling im Volllauf

FEHLT NOCH. Hier stehen später die Kurve über den Lauf, der höchste `anon`-Wert,
der Vergleich mit dem Grenzwert von 2,0 GB, die Laufzeit, der OCR-Anteil und der
Beweis, dass kein Speichertod stattgefunden hat.

## Die Störfall-Drills

FEHLT NOCH. Vorgesehen sind drei: ein Abschuss des Containers mitten im OCR-Lauf
mit anschließendem Neustart, eine Probe mit abgeschaltetem Backend, und eine fast
volle Platte.

## Reproduzieren

```sh
# Preise und Bestand des eigenen Kontos, ohne Nebenwirkung
HCLOUD_TOKEN=... scripts/ops/hetzner_box.sh prices

# Box und Volume anlegen, Zustand außerhalb des Arbeitsbaums
HCLOUD_TOKEN=... scripts/ops/hetzner_box.sh create

# Zustand, Laufzeit und die bisherigen Kosten aus der Konto-API
HCLOUD_TOKEN=... scripts/ops/hetzner_box.sh status

# Speicher eines Containers messen, fünf Sekunden Abstand
scripts/ops/rss_sampler.sh "$(docker ps --filter name=findling_backend --format '{{.Names}}')" 5 rss.csv

# Am Ende jedes Ausgangs, auch des unerwarteten
HCLOUD_TOKEN=... scripts/ops/hetzner_box.sh destroy
```

Der Lastkorpus entsteht aus einem Seed und ist damit Jahre später nachbaubar:

```sh
python scripts/dev/build_load_corpus.py --seed phase5-full --files 50000 --out /mnt/corpus
```

Der Trockenlauf mit 500 Dateien verwendet den Seed `phase5-dry` und hat die
Listen-Prüfsumme
`cac56ed1801efb3e691b28088c363c84d8941670394f5fed95ab19359b17d530`.
