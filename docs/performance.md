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

## Zwei Läufe, und warum

Dieser Bericht führt zwei Messreihen, und das ist keine Gründlichkeit um ihrer
selbst willen, sondern die Folge einer Knappheit. Am 03.09.2026 war bei Hetzner
keine einzige ARM-Maschine zu mieten, in keiner der drei europäischen Regionen.
Der Betreiber hat daraufhin entschieden, beides zu tun: die **Generalprobe** läuft
sofort auf der x86-Maschine gleicher Größe, und der **vollständige Lauf** wird auf
ARM wiederholt, sobald es wieder Bestand gibt.

| | Generalprobe | ARM-Lauf |
|---|---|---|
| Maschine | Hetzner cpx22, x86 | Hetzner CAX11, arm64 |
| Zustand | läuft seit 2026-09-03 | wartet auf Bestand |
| Umfang | vollständig | **vollständig, alles noch einmal** |
| AIO über HaRP, Grundlast, Volllauf, Störfälle | ja | ja, auf eigener Hardware |
| Trägt die Store-Aussage | **nein** | ja |

Die entscheidende Zeile ist die dritte. Der ARM-Lauf ist keine Nachlese, die sich
ein paar Zahlen aus der Generalprobe borgt, sondern derselbe Lauf noch einmal,
vollständig: eigene Grundlast, eigener Volllauf über 50.000 Dateien, eigene
Störfall-Drills, eigener OCR-Faktor. Nichts an der Store-Aussage wird von der
x86-Maschine geerbt.

Wofür die Generalprobe dann gut ist, wenn sie nichts vererbt: sie entschärft den
Weg. Die Reihenfolge der Einrichtung, der Umgang mit dem Zertifikat, die Auswahl
der optionalen Container, die Handgriffe des HaRP-Wegs, die Form der
Störfall-Drills, das alles wird hier einmal durchgespielt und die Fehler darin
fallen hier auf statt dort. Der ARM-Bestand ist knapp und kann jederzeit wieder
verschwinden; wenn er kommt, soll das Fenster für die Messung draufgehen und
nicht für Einrichtungsfehler. Schon der erste Tag hat drei Fehler zutage
gefördert, die den ARM-Lauf Stunden gekostet hätten, darunter einen, der die
40-GB-Systemplatte der CAX11 vollgeschrieben hätte.

Der zweite Nutzen ist der Vergleich selbst. Zwei Messreihen derselben Anwendung
auf zwei Architekturen sagen mehr über ihr Verhalten als eine von beiden allein.

Wo in diesem Bericht x86-Zahlen stehen, sind sie als **Generalprobe cpx22**
gekennzeichnet, und die ARM-Zeile daneben steht so lange auf ausstehend.

## Stand dieses Berichts

| Abschnitt | Zustand | Stand |
|---|---|---|
| Umgebung und Kosten, beide Maschinen | aus der Konto-API abgefragt | 2026-09-03 |
| Reihenfolge der Einrichtung | auf der Generalprobe durchgeführt und belegt | 2026-09-03 |
| Zertifikat und Abschottung | auf der Generalprobe belegt | 2026-09-03 |
| Methode | steht | 2026-09-03 |
| Grenzen | steht | 2026-09-03 |
| Grenzwert für den Spitzenwert | festgelegt, 2,0 GB, aus gemessenen Größen hergeleitet | 2026-09-03 |
| AIO-Grundlast, Generalprobe cpx22 | gemessen, 290 MB Höchststand | 2026-09-03 |
| Beitrag von HaRP, Generalprobe cpx22 | gemessen, 55 MB | 2026-09-03 |
| Installation auf der Box, Generalprobe cpx22 | durchgeführt und belegt | 2026-09-03 |
| Trockenlauf 500 Dateien, Generalprobe cpx22 | gemessen, 381 MB Spitze, 7 min 38 s | 2026-09-03 |
| OCR-Faktor, Generalprobe cpx22 | gemessen, 2517 ms je Seite | 2026-09-03 |
| Laufzeitprognose des Volllaufs, x86 | gerechnet aus gemessenen Posten, rund 13 h | 2026-09-03 |
| AIO-Grundlast, ARM | FEHLT NOCH | wartet auf Bestand |
| Härtungsprobe unter harter Grenze | Befehl belegt und beschrieben, Lauf steht aus | 2026-09-03 |
| Findling im Volllauf, 50.000 Dateien | FEHLT NOCH | Plan 05-14 |
| Störfall-Drills | FEHLT NOCH | Plan 05-14 |

Was fehlt, ist hier ausdrücklich als fehlend benannt und nicht ausgelassen.

## Die Umgebung

### Die beiden Maschinen

| Posten | Generalprobe cpx22 | ARM-Lauf CAX11 |
|---|---|---|
| Architektur | x86_64 | arm64, Ampere |
| Kerne | 2 vCPU, geteilt | 2 vCPU, geteilt |
| Arbeitsspeicher | 4 GB (3814 MB nutzbar) | 4 GB |
| Systemplatte | 80 GB (76 GB nutzbar) | 40 GB |
| Zusatzplatte | Volume, 50 GB, ext4 | Volume, 50 GB, ext4 |
| Region | hel1, Helsinki | hel1, Helsinki |
| Betriebssystem | Ubuntu 24.04 LTS, Kernel 6.8.0 | Ubuntu 24.04 LTS |
| cgroup | v2 | v2 |
| Nextcloud | 33.0.8, All-in-One, PostgreSQL 18.6 | ausstehend |
| Inbegriffener Verkehr | 20 TB je Monat | 20 TB je Monat |

Der Unterschied, der über die Architektur hinaus zählt, steht in der Zeile
Systemplatte: die Generalprobe hat 76 GB, die ARM-Zielmaschine nur 40. Der
Platzdruck, gegen den die Einrichtung unten abgesichert wird, ist auf der
Generalprobe also **milder als im Ernstfall**. Wer die Reihenfolge dort schludert,
merkt es nicht; auf der CAX11 läuft die Platte voll.

Die 50 GB Volume kommen nicht aus Bequemlichkeit dazu: der Lastkorpus wiegt
20,12 GB, daneben liegen der Index und die Abbilder der Container.

### Die Reihenfolge der Einrichtung, und die Falle darin

Drei Dinge müssen auf dem Volume liegen, und zwei davon lassen sich später nicht
mehr verschieben. Die Reihenfolge ist deshalb keine Empfehlung.

1. **Volume einbinden.** Hetzner hängt es mit `automount` selbst ein und schreibt
   den Eintrag in die `fstab`, mit `nofail`.
2. **Das Datenverzeichnis von Docker auf das Volume, vor dem ersten Abbild.**
   `/etc/docker/daemon.json` mit `data-root` wird geschrieben, bevor das Paket
   installiert wird, denn die Installation startet den Dienst selbst.
3. **Das Wurzelverzeichnis von containerd ebenfalls.** Diese Zeile ist neu, und
   sie ist der Fund der Generalprobe. Siehe unten.
4. **`NEXTCLOUD_DATADIR` auf das Volume, vor dem ersten Start von AIO.** Danach
   ist der Wert nicht mehr änderbar.

Zu Punkt 3, weil es teuer wäre, das erst im Volllauf zu bemerken: seit Docker 29
werden Abbilder nicht mehr im Datenverzeichnis von Docker abgelegt, sondern über
den containerd-Snapshotter, und der hat sein eigenes Wurzelverzeichnis unter
`/var/lib/containerd`. `data-root` allein genügt also nicht mehr. Gemessen auf
der Generalprobe: nach dem ersten `docker pull` wuchs die Systemplatte um
400 MB, das Volume um nichts, während `docker info` unbeirrt das Volume als
`Docker Root Dir` meldete.

```
Storage Driver: overlayfs
 driver-type: io.containerd.snapshotter.v1
Docker Root Dir: /mnt/HC_Volume_106785477/docker
373M   /var/lib/containerd
216K   /mnt/HC_Volume_106785477/docker
```

Die Abhilfe ist eine Zeile in `/etc/containerd/config.toml`:

```toml
root = "/mnt/HC_Volume_<id>/containerd"
```

Danach liegen die 373 MB auf dem Volume, und eine Gegenprobe mit einem frischen
Abbild lässt die Systemplatte bei 0 KB und das Volume um 104 KB wachsen. Auf der
CAX11 mit ihren 40 GB wäre der ursprüngliche Zustand nicht kosmetisch gewesen:
die Abbilder von AIO, Postgres, Apache, HaRP und Findling zusammen hätten die
Systemplatte neben Betriebssystem und Protokollen ernsthaft gefüllt, und das
wäre als Fehler von Findling erschienen.

### Was die Umgebung kostet

Abgefragt am 03.09.2026 um 10:48 UTC gegen `/v1/pricing` und `/v1/server_types`
dieses Kontos, also nicht aus einer Preisliste im Netz. Alle Werte brutto, der
Mehrwertsteuersatz des Kontos beträgt 19 Prozent.

| Posten | je Stunde | je Monat |
|---|---|---|
| cpx22 in hel1, Generalprobe | 0,037128 EUR | 23,1931 EUR |
| CAX11 in hel1, ARM-Lauf | 0,011424 EUR | 7,1281 EUR |
| Volume, 50 GB | 0,004662 EUR | 3,4034 EUR |
| Primäre IPv4 | 0,000952 EUR | 0,5950 EUR |
| Summe Generalprobe | 0,042742 EUR | 27,1915 EUR |
| Summe ARM-Lauf | 0,017038 EUR | 11,1265 EUR |

Die Generalprobe kostet also gut das Dreifache der Zielmaschine je Stunde. Das
ist der Preis dafür, dass die günstigen geteilten Linien ausverkauft sind, und er
war dem Betreiber die Sache wert: zwei Tage Generalprobe liegen bei rund 2,05 EUR.

Zwei Dinge daran sind leicht zu übersehen. Der Preis je GB und Monat des Volumes
wird oft mit 0,057 EUR angegeben; das ist der Nettowert, brutto sind es
0,068068 EUR. Und die öffentliche Adresse steht seit 2024 als eigener Posten auf
der Rechnung. Sie macht gegen eine Box für gut einen Cent je Stunde rund acht
Prozent aus, weshalb `scripts/ops/hetzner_box.sh status` sie mitrechnet.

Die Miete endet mit dem Test: die Löschung der Box ist ein Pflichtschritt und
kein Aufräumen bei Gelegenheit, denn eine vergessene Box ist eine öffentlich
erreichbare Nextcloud mit Admin-Zugang und eine monatliche Rechnung. Abgeräumt
werden drei Ressourcen, nicht zwei: Box, Volume und die Firewall. Die Firewall
kostet nichts, und genau deshalb ist sie die, die stehen bleibt.

### Warum die ARM-Maschine fehlt

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
eigenen Spalte. Auch die billigen x86-Typen `cx23` bis `cx53` waren zur selben
Minute überall ausverkauft; knapp waren die günstigen geteilten Linien insgesamt.

### Was AIO ungefragt mitbringt

Die Auswahl der optionalen Container entscheidet über die Grundlast, gegen die
später gemessen wird, und deshalb ist die Ausgangslage der Oberfläche eine
Stolperstelle: **drei optionale Container sind ab Werk angehakt**, und eine
Bürosuite ist ab Werk ausgewählt.

| Vorgabe | Zustand vor der Änderung | für diese Messung |
|---|---|---|
| Imaginary | angehakt | aus |
| Talk | angehakt | aus |
| Whiteboard | angehakt | aus |
| Bürosuite | eurooffice ausgewählt | keine |
| HaRP | aus | wird nach der Grundlast zugeschaltet |

Wer die Oberfläche durchklickt und nur den einen Haken setzt, den er sucht,
misst also gegen eine Grundlast mit vier zusätzlichen Containern und merkt es
nicht. Für diesen Bericht sind alle vier abgewählt worden, bevor die Container
zum ersten Mal gestartet sind; die Konfiguration von AIO trägt danach keinen
einzigen Schalter auf `true`.

Gemessen wird also über genau diese fünf Container: Mastercontainer, Apache,
Nextcloud, Postgres, Redis und notify-push. HaRP kommt nach der Grundlastmessung
dazu, damit sein Beitrag getrennt ausgewiesen werden kann.

### Das Zertifikat ist echt

Der Rückfall `SKIP_DOMAIN_VALIDATION` wurde nicht gebraucht und ist nicht
gesetzt. Die Domäne zeigt per A-Satz auf die Box, DNS-only und nicht über einen
Proxy, AIO hat die Domänenprüfung bestanden und sich über ACME ein Zertifikat
geholt:

```
Aussteller:  Let's Encrypt
gueltig bis: Oct 18 2026
GET https://loadtest.infranode.dev/status.php -> HTTP 200
{"installed":true,"maintenance":false,"needsDbUpgrade":false,
 "version":"33.0.8.2","versionstring":"33.0.8","productname":"Nextcloud"}
```

Damit gilt für diesen Lauf die Aussage, die mit einem selbstsignierten
Zertifikat nicht zu haben gewesen wäre: die TLS-Prüfungen der Container laufen
gegen ein Zertifikat, dem sie wirklich vertrauen, und nicht ins Leere.

### Die Oberfläche von AIO ist von außen nicht erreichbar

Der Filter sitzt außerhalb der Maschine, als Firewall des Anbieters, und das ist
kein Geschmacksurteil: Docker schreibt seine veröffentlichten Ports unmittelbar
in iptables und geht dabei an `ufw` vorbei. Eine `ufw`-Regel gegen Port 8080
würde also melden, der Port sei zu, während er offen ist.

Gemessen von einer fremden Adresse, zweimal: einmal bevor überhaupt etwas
lauschte, und einmal mit laufendem AIO.

| Port | vor dem Start | mit laufendem AIO |
|---|---|---|
| 22 | offen | offen |
| 80 | abgelehnt (RST) | abgelehnt (RST) |
| 443 | abgelehnt (RST) | **offen** |
| 8080 | verworfen | verworfen |
| 8443 | verworfen | verworfen |
| 3478 | verworfen | verworfen |
| 9000 | verworfen | verworfen |

Der Unterschied zwischen abgelehnt und verworfen ist hier der ganze Beweis.
Abgelehnt heißt, das Paket kam bis zur Maschine und fand niemanden vor;
verworfen heißt, es kam gar nicht erst an. Port 443 wechselt von abgelehnt zu
offen, weil dort jetzt Nextcloud steht. Die Oberfläche von AIO auf 8080 und 8443
bleibt in beiden Messungen unerreichbar, obwohl auf 8080 seit dem Start etwas
lauscht. Der Mastercontainer ist zusätzlich nur an `127.0.0.1` gebunden:

```
LISTEN 0 4096 127.0.0.1:8080 0.0.0.0:*  users:(("docker-proxy",...))
```

Port 3478 und 9000 stehen mit in der Liste, weil Talk abgeschaltet bleibt und
niemand später glauben soll, das sei vergessen worden. Erreicht wird die
Oberfläche von AIO ausschließlich durch einen SSH-Tunnel.

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

Die Zahl ist eine Festlegung und keine Messung. Ihre vollständige Herleitung aus
den inzwischen gemessenen Eingangsgrößen steht weiter unten im eigenen Abschnitt
"Der Grenzwert, jetzt aus gemessenen Größen", zusammen mit der Härtungsprobe und
mit dem, was passiert, wenn sie greift. In Kurzform: die Box hat 3814 MB nutzbar,
die gemessene Grundlast von AIO und HaRP nimmt 345 MB davon, die ungünstigste
gerechnete Lage der Findling-Posten liegt bei 1,6 bis 1,7 GB, und 2,0 GB lassen
neben all dem noch 1421 MB für Kernel und Seitencache. 2,5 GB, die als
Größenordnung im Raum standen, ließen 909 MB und wären damit keine Zusage,
sondern eine Wette.

Der Sampler fällt dieses Urteil nicht selbst. Er nennt Zahlen, und der Vergleich
mit dem Grenzwert steht hier.

## Die Grenzen dieses Berichts

Die Regel dieses Repositories lautet, zu jeder Aussage ihre Grenze zu nennen.
Für diesen Bericht sind das sieben:

0. **Die Zahlen der Generalprobe gelten nicht für ARM, keine einzige.** Sie
   stammen von einer x86-Maschine, und zwar von einer mit doppelt so großer
   Systemplatte. Der Speicherverlauf eines Prozesses hängt an Seitengröße,
   Allokator und den Bibliotheken der Architektur, und der OCR-Faktor hängt
   daran besonders. Deshalb wird auf ARM nicht nachgemessen, sondern der ganze
   Lauf wiederholt, Grundlast und Volllauf und Störfälle. Jede Zeile dieses
   Berichts, die eine Zahl der Generalprobe nennt, ist als solche gekennzeichnet,
   und die ARM-Zeile daneben bleibt leer, bis sie gemessen ist.
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

Diese Zahl ist der Bezugspunkt des ganzen Berichts, denn ohne sie sagt eine
Findling-Kurve nichts darüber, ob die Box insgesamt reicht. Gemessen wird sie,
bevor Findling die Maschine zum ersten Mal anfasst.

| Lauf | Summe `anon` im Mittel | höchster Stand | ohne Speichertod |
|---|---|---|---|
| Generalprobe cpx22 | 224 MB | **290 MB** | ja |
| ARM CAX11 | FEHLT NOCH | FEHLT NOCH | FEHLT NOCH |

### Wie die Zahl entstanden ist

Dreißig Minuten und vierzehn Sekunden, von 2026-09-03T17:34:23Z bis
2026-09-03T18:04:37Z, ein eigener Sampler je Container im Abstand von fünf
Sekunden, 361 Messpunkte je Container. Drei Phasen: zwölf Minuten Leerlauf,
sechs Minuten mit 29 Runden gewöhnlicher Aufrufe (Anmeldeseite, `status.php`,
Nutzerabfrage über OCS, `PROPFIND` auf das Wurzelverzeichnis, Dateiansicht,
Übersicht, dazu je Runde eine kleine Datei hochladen und wieder löschen), dann
zwölf Minuten Leerlauf.

Gelaufen sind dabei genau sechs Container und kein siebter:

| Container | höchster `anon`-Stand |
|---|---|
| nextcloud-aio-nextcloud | 190 MB |
| nextcloud-aio-mastercontainer | 47 MB |
| nextcloud-aio-apache | 47 MB |
| nextcloud-aio-database (PostgreSQL 18.6) | 12 MB |
| nextcloud-aio-redis | 4 MB |
| nextcloud-aio-notify-push | 1 MB |

Die Summe wird je Zeitpunkt gebildet und erst danach ihr Höchstwert genommen,
denn was die Box tragen muss, ist der gleichzeitige Stand und nicht die Summe
von sechs Maxima, die zu verschiedenen Minuten aufgetreten sind. Zur Einordnung
steht diese theoretische obere Schranke trotzdem daneben: sie liegt bei 301 MB,
also nur elf MB über dem gemessenen gleichzeitigen Höchststand. Die Zahl ist
damit belastbar und hängt nicht an der Art der Summenbildung.

Nach Phasen getrennt:

| Phase | Mittel | höchster Stand |
|---|---|---|
| Leerlauf | 223 MB | 233 MB |
| unter Aufrufen | 227 MB | 290 MB |

Der Ausschlag auf 290 MB stammt aus der Aufrufphase und fast vollständig aus dem
Nextcloud-Container, also aus den PHP-Arbeitern, die eine Anfrage bedienen. Im
Leerlauf fällt der Stand innerhalb weniger Minuten wieder auf gut 220 MB.

Alle sechs Abschlusszeilen melden `oom_killed=false` und `memory.events` in allen
sechs Zählern auf null. Es gab also nicht nur keinen Speichertod, es gab auch
keinen einzigen Fall, in dem die Grenze überhaupt berührt wurde.

### Die Vorabrechnung war zu pessimistisch, und um welchen Faktor

Angenommen waren 0,7 bis 1,1 GB. Gemessen sind 290 MB im Höchststand, also rund
ein Drittel des unteren Endes der Schätzung. Das ist eine gute Nachricht mit
einer Fußnote, und die Fußnote ist wichtig genug für einen eigenen Absatz.

Beide Zahlen müssen mit demselben Maß genommen sein, sonst vergleicht man nichts.
Der Maßstab dieses Berichts ist `anon`, und mit ihm sind es 290 MB. Nimmt man
stattdessen `memory.current`, also die Zahl, die der Docker-Client anzeigt, dann
liegen dieselben sechs Container im Mittel bei **1353 MB**, denn dort zählt der
Dateicache mit. Wer also die geschätzten 0,7 bis 1,1 GB im Sinne von
`memory.current` gemeint hat, lag richtig, und wer sie im Sinne des tatsächlich
belegten Speichers gemeint hat, lag um den Faktor drei bis vier zu hoch.

Für die Budgetrechnung zählt der zweite Maßstab, weil der Dateicache
zurückforderbar ist: gerät die Maschine unter Druck, gibt der Kernel diese
1063 MB Differenz her, ohne dass ein Prozess etwas davon merkt. Neben den 290 MB
Grundlast bleiben auf einer 4-GB-Box also gut 3,5 GB, und der Grenzwert von
2,0 GB für Findling hat mehr Luft als angenommen.

Die Zahlen dieses Abschnitts gelten für x86. Auf ARM wird die Grundlast neu
gemessen, nicht umgerechnet.

### Der Beitrag von HaRP

HaRP ist der einzige optionale Container, den Findling braucht, und er wurde
deshalb erst nach der Messung oben zugeschaltet. Zehn Minuten Nachmessung über
alle sieben Container, 124 Messpunkte je Container, 2026-09-03T18:12:20Z bis
18:22:43Z:

| Container | `anon` im Mittel | höchster Stand |
|---|---|---|
| **nextcloud-aio-harp** | **54 MB** | **55 MB** |
| nextcloud-aio-nextcloud | 91 MB | 92 MB |
| nextcloud-aio-harp und die sechs anderen zusammen | 233 MB | 236 MB |

Der Beitrag von HaRP sind also rund **55 MB**, und er ist bemerkenswert flach:
zwischen niedrigstem und höchstem Stand liegen über zehn Minuten zwei MB.

Was hier ausdrücklich **nicht** steht, ist ein Vergleich der beiden Summen. Die
236 MB dieser Messung sind nicht kleiner als die 290 MB von oben, weil HaRP
Speicher spart, sondern weil diese Messung zehn Minuten statt dreißig dauerte,
keine Aufrufphase hatte und direkt nach einem Neustart aller Container lief, als
die PHP-Arbeiter von Nextcloud noch frisch waren (92 MB statt 190 MB). Zwei
Messungen mit verschiedenem Aufbau nebeneinanderzustellen und die Differenz zu
deuten, wäre genau die Art von Zahl, gegen die dieser Bericht geschrieben ist.

Belastbar ist die eigene Spalte von HaRP. Für die Budgetrechnung gilt daher
konservativ: Grundlast 290 MB plus HaRP 55 MB, also rund **345 MB**, neben denen
Findling seine 2,0 GB haben darf. Auf einer 4-GB-Box bleibt damit rund ein
weiteres Gigabyte ungenutzt.

Die Rohdaten beider Messungen liegen unter
`docs/measurements/2026-09-03-grundlast-cpx22/`.

### Der HaRP-Weg von AIO, und warum die Warnung aus 05-01 hier nicht greift

AppAPI hat den Daemon selbst registriert, ohne einen einzigen `occ`-Aufruf:

```
| Def | Name     | Display name | Deploy ID      | Protocol | Host                    | NC Url                         | Is HaRP |
| *   | harp_aio | AIO HaRP     | docker-install | http     | nextcloud-aio-harp:8780 | https://loadtest.infranode.dev | yes     |
```

In der Zeile steckt eine Stelle, die aus Phase 5 als Fehler bekannt ist. Beim
Aufbau mit docker-compose führte genau dieses Feld `NC Url` mit der Adresse von
Nextcloud statt der von HaRP zu `heartbeat check failed`, weil AppAPI die Adresse
einer ExApp als `{nextcloud_url}/exapps/{appId}` bildet und HaRP dort der
Eingang ist.

Unter AIO ist der Eingang aber nicht HaRP, sondern Apache, und Apache reicht
`/exapps` an HaRP durch. Nachgewiesen, bevor die erste ExApp installiert wird:

```
GET https://loadtest.infranode.dev/exapps/          -> HTTP 404, text/plain, 13 Byte
GET https://loadtest.infranode.dev/gibtesnicht      -> HTTP 404, text/html, Nextcloud-Seite
```

Die schlichte Textantwort kommt von HaRP, die HTML-Seite von Nextcloud. Die
Weiterleitung steht also, und die Registrierung, die AIO selbst vorgenommen hat,
ist unter AIO richtig. Sie darf nicht nach dem compose-Muster "korrigiert"
werden.

## Installation auf der Box

Dieser Abschnitt beantwortet vor allen Zahlen die Frage, ohne die keine Zahl
etwas wert ist: **welcher Codestand wurde gemessen, und wie kam er auf die
Maschine.**

### Welcher Codestand

`backend/appinfo/info.xml` nennt als Abbild `ghcr.io/street1983nk/findling_backend`
mit dem Kennzeichen `0.3.0`. Dieses Kennzeichen existiert in der Registry nicht:

```
docker manifest inspect ghcr.io/street1983nk/findling_backend:0.3.0
manifest unknown
```

Das ist kein Mangel, sondern die Folge von D-26: der Freigabe-Tag `v1.0.0` wird
erst am Ende der Phase gesetzt, und `docker.yml` legt das Abbild unter dem
Kennzeichen der Freigabe erst dann ab. Was die Registry heute führt, ist ein
Kennzeichen je Commit. Der Stand, gegen den diese Phase misst, ist deshalb
namentlich zu haben:

| Angabe | Wert |
|---|---|
| Commit des Arbeitsbaums | `5c82598a4b793e77834b494861ddbf13d4671f22` |
| gezogenes Kennzeichen | derselbe Commit, als Kennzeichen des Abbilds |
| Digest des Index | `sha256:bb8f17e7d18df86b410308ee06bb2a6935dbbd183f0c6fcd032ab1ef17234544` |
| Digest der Ebene amd64 | `sha256:308ff23621bdd13dae0cd345f5c39e651bddfd3578dcd1409af4e3dd2eb82dd2` |
| Digest der Ebene arm64 | `sha256:eb1798dcab0125a0b967cdb2898c8be3ed887cf8357a51a9673714d8c19b3ad1` |
| Weg | gezogen, nicht auf der Box gebaut |

Der Index trägt beide Architekturen, also zieht der ARM-Lauf später aus
demselben Index seine eigene Hälfte, und die Aussage "derselbe Codestand auf
beiden Maschinen" ist dann keine Behauptung, sondern derselbe Digest.

Gebaut wurde auf der Box nichts. Das ist die bessere Wahl, solange es geht: ein
auf der Messmaschine gebautes Abbild ist ein Stand, den nur diese Maschine
kennt, und die Maschine wird gelöscht.

### Wie das Abbild registriert wurde, ohne die Quelldatei anzufassen

Nur das Kennzeichen des Abbilds musste ersetzt werden, Registry und Abbildname
blieben, wie sie sind. Die Ersetzung läuft in eine Datei außerhalb des
Arbeitsbaums, nach dem Muster des CI-Auftrags:

```sh
sed -e "s|<image-tag>[^<]*</image-tag>|<image-tag>${TAG}</image-tag>|" \
    backend/appinfo/info.xml > /root/findling/info-box.xml
```

Die Quelldatei bleibt unberührt, und das ist eine Abnahmebedingung und keine
Absichtserklärung: `git status --porcelain backend/appinfo/info.xml` ist nach dem
ganzen Lauf leer.

Registriert wird gegen den Daemon, den AppAPI unter AIO **selbst** angelegt hat.
Kein `app_api:daemon:register`, keine Korrektur an seiner `NC Url`, aus dem
Grund, der im Abschnitt darüber steht:

```sh
occ app_api:app:register findling_backend harp_aio \
    --info-xml /tmp/info-box.xml --wait-finish
ExApp findling_backend deployed successfully.
ExApp findling_backend successfully registered.
```

Beim ersten Versuch, ohne einen einzigen Fehlschlag. Der Weg, den Plan 05-01
gegen docker-compose mühsam freigeräumt hat, ist unter AIO genau ein Befehl.

### Die drei Feststellungen, hier auf der Box

Dieselben drei, die der CI-Auftrag `deploy-harp` trifft, damit ein leeres
Ergebnis nicht als Erfolg durchgeht:

```
docker ps --filter name=findling_backend
nc_app_findling_backend  ghcr.io/street1983nk/findling_backend:5c82598a4b79...  Up

docker volume ls --filter name=findling_backend
nc_app_findling_backend_data

occ app_api:app:list
findling_backend (Findling Backend): 0.3.0 [enabled]
```

| Angabe | Wert |
|---|---|
| Container der ExApp | `nc_app_findling_backend` |
| Datenspeicher | `nc_app_findling_backend_data` |
| Daemon | `harp_aio`, von AppAPI selbst angelegt |
| Container insgesamt | acht: die sieben von AIO plus dieser |

Der Containername ist die Angabe, die der Sampler braucht, und deshalb steht er
hier und nicht nur im Protokoll.

### Die Begleit-App

Auf AIO gibt es keinen Arbeitsbaum, in den sich eine App legen ließe, und der
App Store scheidet aus, weil dort noch nichts liegt. Der Weg ist deshalb der
Datenspeicher des Nextcloud-Containers:

```sh
docker cp php nextcloud-aio-nextcloud:/var/www/html/custom_apps/findling
docker exec nextcloud-aio-nextcloud chown -R 33:33 /var/www/html/custom_apps/findling
occ app:enable findling
findling 0.3.0 enabled
```

Das Verzeichnis heißt `findling` und nicht anders, weil der Klassenlader von
Nextcloud sonst nichts findet und der Suchanbieter unsichtbar bleibt, ohne
Fehlermeldung. `custom_apps` liegt in einem Docker-Volume, überlebt also einen
Neustart der Container; die 33 ist die Nutzerkennung von `www-data` in den
AIO-Abbildern.

### Was auf dieser Box anders ist als in CI: PostgreSQL

```
occ config:system:get dbtype   -> pgsql
select version()               -> PostgreSQL 18.6 on x86_64-pc-linux-musl
Nextcloud                      -> 33.0.8.2
```

Das ist der erste Lauf dieses Projekts auf PostgreSQL. Jede Zahl der Statusseite
wurde deshalb einzeln gegen einen erwarteten Wert gehalten, siehe unten.

### Die Suche antwortet, zweimal

Beide Wege wurden gegangen, weil sie verschiedene Dinge belegen. Sechs kleine
Textdateien liegen im Verzeichnis `probe` eines gewöhnlichen Nutzers, nicht des
Verwalters, damit die Nutzerkennung in der Antwort nicht mit der des Installateurs
verwechselt werden kann.

**Über die OCS-Route**, mit einfacher Anmeldung, so wie ein Klient sie ruft:

```
GET /ocs/v2.php/search/providers/findling/search?term=findlingprobe
HTTP 200, 5 Treffer
  vermerk-1.txt bis vermerk-5.txt, jeweils mit Textausschnitt und Fundstellen
```

**Über die Weboberfläche**, also mit einer echten angemeldeten Sitzung samt
Anfragemarke, was genau der Aufruf ist, den die Suchleiste selbst macht:

```
POST /login  (Sitzung), danach derselbe Suchaufruf mit requesttoken
HTTP 200, 5 Treffer
```

Der Textausschnitt in der Antwort stammt aus dem Inhalt der Datei und nicht aus
ihrem Namen, also hat der Container gelesen und nicht der Dateibaum geraten.
Damit ist D-04 belegt: auf dieser Box liefert eine Suche einen Treffer aus einem
Container, den der AIO-HaRP-Daemon erzeugt hat.

Eine Fußnote zur Sitzung, weil sie eine halbe Stunde gekostet hat und der
nächste Leser sie geschenkt bekommen soll: eine Anmeldung über `/login` ohne
`Origin`-Kopfzeile beantwortet Nextcloud mit `loginErrors: ["invalidOrigin"]`,
und zwar mit HTTP 200 und der Anmeldeseite als Antwort. Wer nur den Statuscode
prüft, hält das für eine geglückte Anmeldung und rätselt danach über 401 auf
jedem folgenden Aufruf.

### Die Statusseite unter PostgreSQL, Kachel für Kachel

Aufgerufen als Verwalter über `/apps/findling/admin/overview`, also über
dieselbe Route, aus der die Seite ihre Zahlen zieht. Bestand zu diesem
Zeitpunkt: 104 Dateien in zwei Nutzerverzeichnissen.

| Kachel | Wert | erwartet | Beurteilung |
|---|---|---|---|
| Erreichbarkeit des Containers | ja | ja | wie erwartet |
| Versionsgleichstand | `match`, 0.3.0 gegen 0.3.0 | Gleichstand | wie erwartet |
| indexiert, Zählung Nextcloud | 0 | 0 | wie erwartet und ausdrücklich so dokumentiert: das Endverdikt "indexiert" zählt der Container, nicht die Nextcloud-Seite |
| indexiert, Anzeige | 88 | 88 | wie erwartet |
| übersprungen | 16 | 16 | wie erwartet |
| fehlgeschlagen | 0 | 0 | wie erwartet |
| Deckungsgrad | 88 von 104, 84 Prozent | 84 Prozent | wie erwartet: 88 plus 16 ergibt genau die 104 des Bestands |
| Mounts | 2 von 2 fertig | 2 | wie erwartet |
| Fehlerliste | `empty_text` 14, `image_not_ocrable` 2 | zwei Gruppen | wie erwartet: die 14 leeren sind Vorlagen und Verzeichnisdateien ohne Text, die zwei Bilder sind die Beispielfotos von Nextcloud |
| Indexgröße | 795.701 Byte | Größenordnung | plausibel für 88 kleine Dokumente |
| freier Platz | 44,6 GB von 52,5 GB | Volume | richtig: die Kachel liest das Volume und nicht die Systemplatte |
| Neuaufbau nötig | nein | nein | wie erwartet |
| Wortlisten-Prüfsumme | `b1f64012...` | gesetzt | wie erwartet |
| gemessene OCR-Zeit | leer | leer | wie erwartet: bis hierher lief keine einzige OCR-Seite |

Keine Kachel weicht ab. **Der erste PostgreSQL-Lauf dieses Projekts hat keinen
Dialektfehler zutage gefördert**, weder beim Anlegen der drei Tabellen noch beim
Zählen über sie.

Drei Beobachtungen, die keine Kachel falsch machen, aber notiert gehören:

1. **Ein Nutzer, der nach dem ersten Durchgang angelegt wird, fehlt zunächst im
   Nenner.** Direkt nach dem Anlegen des zweiten Nutzers stand der Deckungsgrad
   auf 88 von 49, also über hundert Prozent und auf hundert gedeckelt: der
   Durchgang hatte nur den einen Mount gesehen, den es beim Start gab, während
   die Dateien des neuen Nutzers über den Vergleichslauf trotzdem in den Index
   kamen. Nach `occ findling:index --restart` stimmen Zähler und Nenner. Der
   Zustand ist vorübergehend und heilt spätestens mit dem nächtlichen Vergleich,
   er sieht aber für die Dauer wie ein Zählfehler aus. Notiert als DI-05-20.
2. **`occ findling:index --restart` fragt nach und tut ohne `-n` nichts.** Die
   Rückfrage ist richtig, der Befehl liest jedes Dokument neu. In einem Skript
   ohne `--no-interaction` bleibt sie unbeantwortet, der Befehl endet mit
   "Nothing was changed", und der Aufrufer denkt, der Neuaufbau laufe.
3. **`occ files:scan --path=...` meldet auf einem Nutzerverzeichnis, das noch nie
   vollständig durchsucht wurde, `Error during scan: mkdir(): File exists`.** Das
   ist Nextcloud und nicht Findling: der Teilbaum wird gescannt, bevor das
   Grundgerüst des Nutzers angelegt ist. Ein vorheriges `occ files:scan <nutzer>`
   räumt es aus. Für den Volllauf heißt das: erst den Nutzer einmal ganz
   durchsuchen, dann den Korpus einwerfen.

## Der Trockenlauf: 500 Dateien, bevor 50.000 laufen

Dieser Abschnitt ist der Grund, aus dem der Volllauf noch nicht gelaufen ist.
Die Laufzeitrechnung der Recherche stand auf einer geschätzten Zahl, es war der
erste PostgreSQL-Lauf des Projekts, und ein Fehler, der nach zwanzig Stunden
zuschlägt, kostet den ganzen Lauf. Also erst zwanzig Minuten.

Er hat sich in der ersten davon bezahlt gemacht: **jede Tabellendatei der
Instanz war unindexierbar**, und das wäre in einem Volllauf über 50.000 Dateien
als eine Zahl im Fehlerbericht untergegangen. Siehe unten.

### Der Korpus, und eine Prüfsumme, die an ihre Umgebung gebunden ist

```
build_load_corpus: seed=phase5-dry files=500 bytes=246452632
  checksum=afe5de552ae9cdf7a515326e7d0787a9133b4dfef3c08e75f41f9ad5db95a5d0
```

| Kategorie | Dateien | Anteil |
|---|---|---|
| einseitige Scans | 99 | 19,8 Prozent |
| mehrseitiger Scan | 1 | 0,2 Prozent |
| Text-PDF | 225 | 45,0 Prozent |
| OOXML (docx, xlsx, pptx) | 100 | 20,0 Prozent |
| OpenDocument (odt, ods) | 50 | 10,0 Prozent |
| reiner Text (txt, md, csv) | 23 | 4,6 Prozent |
| Bild | 1 | 0,2 Prozent |
| über dem Größendeckel | 1 | 0,2 Prozent |

Der Korpus entsteht auf der Box und wird nicht über die Leitung geschoben, und
er entsteht **im Abbild der ExApp** und nicht im System-Python der Box: dort
liegt Pillow in der gepinnten Fassung, und es kommt kein einziges Paket auf die
Maschine, das nicht ohnehin im Container läuft. 17 Sekunden für 500 Dateien und
246 MB.

Dabei ist etwas aufgefallen, das in den Bericht gehört, weil es eine Zusage
einschränkt. Plan 05-05 hat für denselben Seed `phase5-dry` die Prüfsumme
`cac56ed1...` bei 245.695.552 Byte protokolliert. Im Container sind es
`afe5de55...` bei 246.452.632 Byte, und zwei Läufe hintereinander liefern dort
beide Male dieselbe. **Der Seed reproduziert den Korpus also innerhalb einer
Umgebung und nicht über Umgebungen hinweg.** Die Ursache liegt in der
Bildseite: die Scans werden gerendert, und Schriftrasterung und Kompression
hängen an den Fassungen der Bibliotheken.

| Größe | Entwicklungsrechner (05-05) | Abbild auf der Box |
|---|---|---|
| Prüfsumme | `cac56ed1...` | `afe5de55...` |
| Bytes | 245.695.552 | 246.452.632 |
| Unterschied | | 757.080 Byte, 0,31 Prozent |
| Pillow | Fassung des Arbeitsbaums | 12.3.0 |
| FreeType | Fassung des Betriebssystems | 2.14.3 |
| zlib | | 1.3.1 |

Die Zusage aus 05-05 bleibt damit gültig, aber sie lautet genauer: reproduzierbar
ist das Paar aus Seed **und** Abbild, und das Abbild ist über seinen Digest
festgenagelt. Für den Volllauf ist deshalb der Digest oben die zweite Hälfte der
Angabe, und der Prüfsummenvergleich gilt nur gegen einen Lauf im selben Abbild.

### Der Befund, der diesen ganzen Plan bezahlt: keine Tabelle wurde indexiert

Nach dem Lauf standen 32 Dateien auf `failed(corrupt)`, und zwar genau die 32
`.xlsx` des Korpus. Kein anderes Format war betroffen, und der Fehler lag nicht
an den erzeugten Dateien:

```
openpyxl.load_workbook("/tmp/job-42.part", read_only=True, data_only=True)
InvalidFileException: openpyxl does not support .part file format, please check
you can open it with Excel first. Supported formats are: .xlsx,.xlsm,.xltx,.xltm
```

openpyxl prüft die Dateiendung, bevor es ein einziges Byte liest. Der Poller
übergibt der Extraktion aber nie den Namen aus Nextcloud, sondern seine
Zwischendatei `job-<Warteschlangen-Id>.part`. Die Ausnahme wandert durch die
allgemeine Übersetzung in `extract/errors.py` und wird zu `failed(corrupt)`, also
zu "Datei beschädigt" auf der Statusseite. python-docx und python-pptx öffnen ihr
Paket am Inhalt und sind deshalb nicht betroffen.

Das war keine Eigenheit dieses Korpus. **Jede Tabellendatei jeder Instanz war
davon betroffen**, seit es die Zwischendatei gibt, und keine der 47 Prüfungen des
Dateiformats hat es gesehen, weil jede von ihnen ihre Testdatei unter dem Namen
ihres Formats angelegt hat.

Behoben, indem der Lader einen offenen Datenstrom statt eines Pfades bekommt: ein
Datenstrom trägt keinen Namen, an dem sich prüfen ließe. Der neue Testfall legt
docx, pptx und xlsx unter dem Namen `job-4711.part` an, also unter dem Namen, den
der Poller wirklich übergibt.

Belegt auf der Box, nicht nur in der Suite: nach einem auf der Maschine gebauten
Abbild mit der Korrektur meldet der Container 587 indexierte Dokumente und **null
Fehlschläge**, alle 32 Tabellen tragen `indexed`, und eine Suche nach einem Wort
aus einer Tabellenzelle liefert die Tabelle unter ihren Treffern.

### Was der Lauf gemessen hat

| Größe | Wert |
|---|---|
| Beginn | 2026-09-03T18:58:31Z |
| Ende, letzter Index | 2026-09-03T19:06:09Z |
| Dauer | 458 s, also 7 Minuten 38 Sekunden |
| Arbeitsvorrat | 603 Zeilen: die 500 des Korpus und 103 aus dem Bestand |
| indexiert | 555 |
| fehlgeschlagen | 32, alle `corrupt`, alle Tabellen, Ursache oben |
| übersprungen | 17: `empty_text` 14, `image_not_ocrable` 2, `too_large` 1 |
| ohne Verdikt | keine |

Die Verteilung der Verdikte passt zur Erzeugung, mit genau einer benannten
Abweichung: die 32 Tabellen hätten indexiert werden müssen und waren der Befund
oben. Die 17 Übersprungenen sind erwartet: `too_large` ist die eine Datei über
dem Größendeckel, die der Generator absichtlich schreibt, die 14 `empty_text` und
2 `image_not_ocrable` stammen aus dem Altbestand der Instanz (Vorlagen ohne Text
und die Beispielfotos von Nextcloud) und nicht aus dem Korpus.

### Der OCR-Faktor auf dieser Maschine, und was er nicht sagt

Zwei Messungen, weil eine allein sich nicht prüfen ließe.

**Aus dem Lauf selbst**, über die Zeitstempel der Zustandsdatenbank des
Containers, eingegrenzt auf das Zeitfenster des Trockenlaufs:

| Spur | Dokumente | Spanne | je Dokument |
|---|---|---|---|
| OCR | 101 | 288 s | **2,85 s** |
| Text | 366 | Indexschreibung in 43 s | siehe unten |

**Direkt, nach dem Muster von Messung 3 aus `docs/ocr.md`**, damit die Zahl mit
der dortigen Laptopzahl vergleichbar ist. Dieselbe Befehlszeile, dieselbe
Auflösung, dieselbe Seitengeometrie, dreimal:

```
Seite 2480x3509, Graustufen, 300 dpi, aus einer Scan-PDF des Korpus
tesseract - - -l deu+eng --oem 1 --psm 3 -c tessedit_do_invert=0
OMP_THREAD_LIMIT=1
2594 ms, 2477 ms, 2517 ms  ->  Median 2517 ms
Rasterung der Seite allein: 276 ms
```

| Bezug | Laptop (docs/ocr.md) | cpx22 | Faktor |
|---|---|---|---|
| je Seite | 1984 ms | 2517 ms | 1,27 |
| Zeichen auf der Seite | 2340 | 3427 | 1,46 |
| je 1000 Zeichen | 848 ms | 734 ms | **0,87** |

Und damit zu dem Satz, der hier wichtiger ist als die Zahl: **der Faktor 1,27 ist
kein Hardwarefaktor.** Die Seite des Lastkorpus trägt 46 Prozent mehr Zeichen als
die Seite aus `docs/ocr.md`, und tesseract kostet die Zeichen und nicht die
Fläche. Auf den Zeicheninhalt bezogen ist der geteilte x86-Kern der Miet-Box
sogar etwas schneller als der Laptopkern.

Was damit ersetzt ist: die Rechnung der Recherche hat für tesseract 4,5 s je
Seite und 1 s für die Rasterung angenommen. Gemessen sind 2,52 s und 0,28 s, also
zusammen **2,80 s je Seite statt 5,5 s**. Der Wert deckt sich mit den 2,85 s je
OCR-Dokument aus dem Lauf, was beide Messungen gegeneinander bestätigt.

Was damit **nicht** ersetzt ist: die Zahl für ARM. Sie ist unverändert
ungemessen, und sie ist die einzige, die die Store-Aussage tragen wird.

### Die Prognose für den Volllauf, mit gemessenen statt geschätzten Posten

Dieselbe Tabellenform wie in der Recherche, nur ohne die Marke ASSUMED:

| Posten | Menge | gemessen | Summe |
|---|---|---|---|
| einseitige Scans | 9.900 Seiten | 2,80 s je Seite | 27.720 s = 7,7 h |
| mehrseitige Scans | 100 Dateien zu 8 Seiten | 2,80 s je Seite | 2.240 s = 0,6 h |
| Textdateien | 40.000 | 0,43 s je Datei | 17.200 s = 4,8 h |
| **Summe** | | | **rund 13 h** |

Die 0,43 s je Textdatei sind der einzige abgeleitete Posten der Tabelle: die
Indexschreibung selbst läuft in Stapeln, ihre Zeitstempel taugen deshalb nicht
als Zeitmessung je Datei. Genommen ist stattdessen die Textphase des Laufs als
Ganzes, also 170 s vom Beginn bis zum ersten OCR-Dokument, für rund 400 Dateien
samt Durchgang, Abholung und Quittierung.

Gegenprobe ohne jede Aufteilung: 500 Dateien in 458 s sind 0,92 s je Datei, und
der Trockenlauf hat mit 20 Prozent genau den OCR-Anteil des Volllaufs. Linear
hochgerechnet sind das 12,8 h. Die beiden Wege liegen 2 Prozent auseinander.

**Die Rechnung der Recherche lag bei 18 bis 20 h, gemessen sind rund 13 h.** Der
Unterschied kommt fast vollständig aus dem OCR-Posten, dessen Sekundenwert
halbiert wurde.

Und die Einschränkung, die diese Prognose wertlos machen würde, wenn sie nicht
dabeistünde: **sie gilt für x86.** Kostet tesseract auf dem Ampere-Kern das
Zweifache, werden aus 8,3 h OCR 16,6 h und aus der Summe rund 21 h; beim
Dreifachen sind es rund 30 h. Genau diese Spanne war der Grund, den Faktor zu
messen, und sie bleibt bis zum ARM-Lauf offen. Sollte sie zwei Tage deutlich
übersteigen, ist die Steuergröße die OCR-Menge und nicht die Verteilung: die
Verteilung zu ändern hieße, die Aussage zu ändern. Die Frage gehört dann dem
Betreiber vorgelegt und nicht stillschweigend beantwortet.

### Speicher

| Größe | Lauf 1 (Abbild vom Commit-Kennzeichen) | Lauf 2 (Abbild mit der Korrektur) |
|---|---|---|
| höchster `anon` | **381 MB** (400.003.072 Byte) | 262 MB (274.288.640 Byte) |
| `memory.peak` | 455 MB | 339 MB |
| `memory.events` | alle sechs Zähler 0 | alle sechs Zähler 0 |
| `.State.OOMKilled` | false | false |
| Messpunkte | 146 | 40 |

Der Grenzwert des Berichts liegt bei 2,0 GB. Der Trockenlauf hat davon 19
Prozent gebraucht. Das ist kein Freibrief für den Volllauf: der Korpus hier trägt
genau einen mehrseitigen Scan und keine Datei nahe am Größendeckel von 50 MB,
und beides sind die Fälle, an denen der Spitzenwert hängt. Aber er sagt, dass die
Grundlast des Containers samt Kompositum-Automat und Schreibpuffer bei rund
250 bis 300 MB liegt und die Spitze eines gewöhnlichen Dokuments daran wenig
ändert.

Die Rohdaten liegen unter `docs/measurements/2026-09-03-trockenlauf-cpx22/`.

### Die Größe des Index

| Größe | Wert |
|---|---|
| Index nach dem Lauf | 8.298.442 Byte bei 587 Dokumenten |
| je Dokument | 14.137 Byte |
| Korpus auf der Platte | 246.452.632 Byte |
| Index gegen Korpus | 3,4 Prozent |
| hochgerechnet auf 50.000 Dokumente | rund 707 MB |

Phase 3 hat den Index des Volllaufs mit 3 bis 6 GB veranschlagt. Gemessen wird er
rund ein Fünftel des unteren Endes dieser Schätzung. Der Grund ist kein Kunststück
der Anwendung, sondern der Korpus: seine Dateien wiegen viel und tragen wenig
Text, weil ihr Bytegewicht aus einer unkomprimierten Scan-Anlage kommt und nicht
aus Prosa (05-05). Ein echter Bestand mit demselben Byteumfang trägt mehr Text
und erzeugt einen größeren Index. Die Zahl gehört deshalb mit dieser Fußnote in
den Bericht und nicht ohne sie.

### Der Blick auf PostgreSQL, ausdrücklich

Der Perf-Befund M7 aus Phase 2 lautet: `record()` innerhalb einer offenen
Transaktion bricht auf PostgreSQL die **ganze** Transaktion ab, die Quittierung
schlägt fehl, und die Warteschlange wird nie leer. Behoben wurde er damals über
eine Umstellung auf UPDATE-first, aber nie auf PostgreSQL ausprobiert.

Dieser Lauf ist die Probe, und er ist eine schärfere, als eine geplante gewesen
wäre: die 32 Fehlschläge oben sind genau der Pfad, den M7 benennt, nämlich ein
`record()` mit Grundcode innerhalb der Quittierungstransaktion, 32 Mal, verteilt
über acht Durchgänge.

| Prüfung | Ergebnis |
|---|---|
| `oc_findling_queue` nach dem Lauf | 0 Zeilen |
| hängendes Ack | keines, jeder Durchgang endete mit einer Quittierung |
| `current transaction is aborted` im PostgreSQL-Protokoll | kein einziges Vorkommen |
| Perf-M7 | auf PostgreSQL belegt behoben |
| Anlegen der drei Tabellen, Zähler über sie, Fehlerliste, Deckungsgrad | ohne Dialektfehler |

Das einzige `ERROR:` im Datenbankprotokoll des ganzen Tages stammt aus einer
Abfrage dieser Untersuchung selbst, nach einer Spalte, die es nicht gibt.

### Die Statusseite unter Last

Beobachtet vor dem Lauf, dreimal während des Laufs und danach. Notiert ist auch
das Unauffällige, weil eine Liste, die nur Auffälliges enthält, nicht sagt, wie
weit geschaut wurde.

- Der Deckungsgrad wächst monoton und bleibt in seinen Grenzen: 84 Prozent vor
  dem Lauf, 92 Prozent danach, 97 Prozent nach der Korrektur. Zähler und Nenner
  gehen jederzeit auf.
- Die Fehlerliste zeigt die vier Gruppen mit anklickbaren Beispielpfaden, die
  Gruppe `corrupt` erscheint mit dem Lauf und verschwindet nicht wieder, siehe
  den Befund unten.
- Der Arbeitsvorrat zählt herunter, ohne zwischendurch zu wachsen, und "an den
  Arbeiter übergeben" steht nie über der Stapelgröße.
- Der Versionsgleichstand steht durchgehend auf `match`, auch während der
  Container neu gestartet wurde.
- Die Kachel für den freien Platz liest das Volume und nicht die Systemplatte,
  also 44,3 GB frei von 52,5 GB. Auf einer Box, deren Datenverzeichnis
  woanders liegt als das Betriebssystem, ist das der Unterschied zwischen einer
  richtigen und einer beruhigenden Zahl.
- Die Kachel "gemessene OCR-Zeit" bleibt leer, und das ist beabsichtigt: die
  Schätzung erlischt, sobald der erste Durchgang fertig ist, weil es dann nichts
  mehr zu schätzen gibt.
- **Ein Fehlschlag von gestern bleibt in der Fehlerliste stehen, auch wenn die
  Datei heute indexiert ist.** Nach der Korrektur meldet der Container 587
  indexiert und 0 fehlgeschlagen, die Nextcloud-Seite weiterhin 32
  fehlgeschlagen, und `occ findling:diagnose` nennt für eine dieser Dateien
  "Datei beschädigt", während dieselbe Datei über die Suche zu finden ist. Der
  Grund steht in der Quittierung: erfolgreiche Dateien schreiben nichts in die
  Zustandstabelle, also räumen sie ihre alte Zeile auch nicht weg. Beide Zahlen
  stehen nebeneinander auf der Seite, ein aufmerksamer Verwalter sieht den
  Widerspruch also, aber die Fehlerliste ist so lange falsch, bis jemand sie
  räumt. Notiert als DI-05-21.

## Der Grenzwert, jetzt aus gemessenen Größen

Der Abschnitt "Der Grenzwert, gegen den geprüft wird" oben im Methodenteil nennt
die Zahl. Hier steht ihre Herleitung, und sie steht bewusst **hier**, nach den
Messungen und vor dem Volllauf: der Grenzwert wird festgelegt, bevor der Lauf
beginnt, dessen Ergebnis er beurteilt. Ein Grenzwert, der nach dem Ergebnis
entsteht, beurteilt nichts.

### Die Rechnung

Drei der vier Eingangsgrößen sind inzwischen gemessen und nicht mehr geschätzt:

| Eingangsgröße | Wert | Herkunft |
|---|---|---|
| Arbeitsspeicher der Box | 3814 MB nutzbar von 4 GB | `free -m` auf der Maschine |
| AIO-Grundlast einschließlich HaRP | 345 MB (290 plus 55) | **gemessen**, Plan 05-10, oben im Bericht |
| ungünstigste gleichzeitige Lage der Findling-Posten | 1,6 bis 1,7 GB | gerechnet aus den Projektkonstanten, nicht gemessen |
| Spitzenwert des Trockenlaufs | 381 MB | **gemessen**, Abschnitt oben |

Daraus:

```
3814 MB nutzbar
-  345 MB gemessene Grundlast von AIO und HaRP
- 2048 MB Grenzwert für Findling
= 1421 MB für Kernel, Seitencache und alles Übrige
```

Der Grenzwert muss zwei Bedingungen erfüllen, und beide sind erfüllt:

1. **Er liegt über dem, was Findling braucht, mit Luft.** 2048 MB sind das
   1,2fache der ungünstigsten gerechneten Lage von 1700 MB und das 5,4fache des
   im Trockenlauf gemessenen Spitzenwerts. Die Luft ist nicht großzügig, sie ist
   nötig: der Volllauf bringt 100 mehrseitige Scans und Dateien bis an den
   Größendeckel von 50 MB, und beides fehlt im Trockenlauf.
2. **Er lässt neben sich Platz.** 1421 MB für Kernel und Seitencache sind auf
   einer Maschine, deren Index als Datei in den Speicher abgebildet wird,
   kein Rest, sondern ein Arbeitsmittel: je mehr Index im Seitencache liegt,
   desto schneller antwortet die Suche.

Die Empfehlung der Recherche lautete 2,0 GB, und die Rechnung bestätigt sie, also
bleibt es dabei. **Der Grenzwert ist 2,0 GB, also 2.147.483.648 Byte, für den
höchsten `anon`-Wert des Findling-Containers.**

Was 2,5 GB bedeutet hätten, weil die Zahl als Größenordnung im Raum stand:
`3814 - 2560 - 345 = 909 MB` für alles Übrige. Das ist weniger, als der
Seitencache eines 20-GB-Korpus gern hätte, und es ist der Bereich, in dem der
Kernel anfängt zu räumen statt zu arbeiten. Nach der Messung der Grundlast ist
die Entscheidung für 2,0 GB bequemer als vorher gedacht: die Grundlast war mit
0,7 bis 1,1 GB veranschlagt und liegt bei 0,345 GB.

### Drei Zahlen, die nicht dasselbe sind

Diese Trennung ist der Kern des Abschnitts, denn ohne sie rechnet der erste
Leser, der `docker stats` aufruft, andere Zahlen nach und hält den Bericht für
falsch.

| Zahl | Trockenlauf | Volllauf | Was sie ist |
|---|---|---|---|
| **Grenzwert** | 2,0 GB | 2,0 GB | eine Festlegung. Der Volllauf besteht oder besteht nicht gegen sie. Sie wird nicht gemessen und sie ändert sich nicht mit dem Ergebnis. |
| **gemessener Spitzenwert `anon`** | 381 MB | FEHLT NOCH | eine Messung. Der Wert des ARM-Volllaufs wird die Zahl der Store-Aussage. |
| **`memory.peak`** | 455 MB | FEHLT NOCH | dieselbe cgroup, anderer Maßstab: hier zählt der Dateicache mit. |

Warum die Store-Zahl aus `anon` kommt und nicht aus `memory.peak`: der Index ist
eine in den Speicher abgebildete Datei, also landet jeder gelesene Indexblock im
Dateicache derselben cgroup. Dieser Cache ist vollständig zurückforderbar, der
Kernel gibt ihn unter Druck her, und kein Prozess merkt etwas davon. Eine
Store-Aussage aus `memory.peak` würde die Anwendung also schlechter darstellen,
als sie ist, und zwar umso schlechter, je größer der Bestand des Betreibers ist.
Im Trockenlauf sind das 74 MB Unterschied, in der Grundlastmessung von 05-10
waren es über die AIO-Container 1063 MB.

Aufgezeichnet werden beide, und beide stehen in jeder Tabelle nebeneinander. Der
Docker-Client zeigt eine Zahl auf Basis von `memory.current`, also die höhere.
Wer sie neben die Zahl dieses Berichts legt, soll den Unterschied erklärt finden
statt versteckt.

### Die Härtungsprobe: der Volllauf läuft unter einer harten Grenze

Ein beobachteter Spitzenwert ist eine Momentaufnahme. Er sagt, dass die
Anwendung in den 146 Augenblicken, in denen gemessen wurde, unter der Zahl lag.
Ein Lauf, der unter einer vom Kernel durchgesetzten Grenze durchläuft, sagt
etwas anderes: dass sie in **keinem** Augenblick überschritten wurde, auch nicht
zwischen zwei Messpunkten. Das ist ein Satz, den man in eine Store-Beschreibung
schreiben kann.

AppAPI kennt `resourceLimits.memory` nur im Deploy-Config eines Daemons und nicht
als Option von `occ`, deshalb ist der Weg der Docker-Client. Der Befehl steht
hier wortwörtlich, damit Plan 05-14 ihn nicht neu erfindet:

```sh
docker update --memory=2g --memory-swap=2g nc_app_findling_backend
```

Auf dieser Box am 2026-09-03 ausprobiert, mit dem Ergebnis:

```
memory.max      2147483648
memory.swap.max 0
docker inspect  Memory=2147483648 MemorySwap=2147483648
Status          Up, der Container läuft weiter
```

`--memory-swap` auf denselben Wert heißt: kein Swap. Ohne diese Angabe bekäme der
Container die doppelte Menge als Swap-Budget, und ein Lauf, der sich nur durch
Auslagern unter der Grenze hält, hätte mit der Zusage nichts zu tun.

Drei Dinge, die beim Setzen zu wissen sind:

1. **Die Grenze lässt sich mit `docker update` nicht wieder abnehmen.**
   `--memory=0` tut nichts und `--memory=-1` wird abgewiesen (beides hier
   ausprobiert). Wer sie loswerden will, muss den Container neu erzeugen lassen,
   also `occ app_api:app:unregister findling_backend` ohne `--rm-data` und
   danach wieder registrieren. Der Datenspeicher bleibt dabei erhalten.
2. **Sie überlebt keine Neuerzeugung des Containers.** Jede Registrierung legt
   einen neuen Container an, und der kommt ohne Grenze. Sie gehört deshalb
   gesetzt, nachdem zum letzten Mal registriert wurde, und vor dem Start des
   Laufs mit `docker inspect` gegengeprüft.
3. **`memory.max` begrenzt `memory.current` und nicht `anon`**, zählt also den
   Dateicache mit. Die Probe ist damit **strenger** als der Grenzwert, den sie
   prüft. Das ist Absicht und kein Versehen: der Cache ist zurückforderbar, der
   Kernel räumt ihn, bevor er tötet, und ein Lauf, der unter dieser Grenze
   durchkommt, hat `anon` erst recht darunter gehalten.

### Wenn die harte Grenze greift

Dann tötet der Kernel den Container. `memory.events` zählt `oom_kill` hoch,
`.State.OOMKilled` steht auf `true`, und die Abschlusszeile des Samplers nennt
beides. **Das ist dann das Ergebnis des Laufs und kein Betriebsunfall**, und es
ist genau die Aussage, für die die Probe gefahren wird. Ein solcher Volllauf ist
nicht wiederholbar, bis eine der drei Antworten gewählt ist:

| Antwort | Was sie kostet | Wann sie richtig ist |
|---|---|---|
| **Grenzwert anheben**, mit Begründung im Bericht | Die Store-Aussage wird schwächer, und auf einer 4-GB-Box wird es eng: über 2,5 GB ist die Rechnung oben nicht mehr zu halten. | Wenn der Spitzenwert knapp und nachvollziehbar über der Grenze liegt und die Rechnung oben mit der gemessenen Grundlast noch aufgeht. |
| **Stellschraube senken** | Ein kleinerer Schreibpuffer bedeutet mehr Segmente und mehr Vereinigungsläufe, weniger DPI bedeutet schlechtere Erkennung. | Wenn der Spitzenwert an einem benannten Posten hängt: `FINDLING_WRITER_HEAP_BYTES` (50 MB), `FINDLING_BATCH_MAX_BYTES` (64 MB), `FINDLING_OCR_DPI` (300), `FINDLING_OCR_MAX_PAGES` (30), `FINDLING_MAX_CELLS` (200.000). `INDEX_WORKERS` steht bereits auf 1 und ist keine Reserve mehr. |
| **OCR-Menge des Korpus senken** | Die Aussage ändert sich, denn OCR ist die Steuergröße des ganzen Laufs. | Nur nach einer Entscheidung des Betreibers. Sie darf nicht stillschweigend fallen, weil sie aus "50.000 Dateien mit 20 Prozent Scans" etwas anderes macht. |

Was in keinem der drei Fälle passiert: die Verteilung des Korpus wird nicht
angepasst, bis die Zahl stimmt. Das wäre keine Messung mehr.

### Zusammengefasst, in einer Zeile

**Der Volllauf besteht, wenn er ohne Speichertod durchläuft und der höchste
`anon`-Wert des Findling-Containers unter 2,0 GB bleibt, gefahren unter
`docker update --memory=2g --memory-swap=2g`.**

## Findling im Volllauf

| Lauf | höchster `anon` | unter 2,0 GB | Laufzeit | OCR-Anteil | Speichertod |
|---|---|---|---|---|---|
| Generalprobe cpx22 | FEHLT NOCH | FEHLT NOCH | FEHLT NOCH | FEHLT NOCH | FEHLT NOCH |
| ARM CAX11 | FEHLT NOCH | FEHLT NOCH | FEHLT NOCH | FEHLT NOCH | FEHLT NOCH |

Die Zeile, die in die Store-Beschreibung geht, ist die zweite. Die erste steht
daneben, weil ein Vergleich der beiden mehr über das Verhalten der Anwendung
verrät als jede von beiden allein, und weil sie zuerst da ist.

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

Der Lastkorpus entsteht aus einem Seed und ist damit Jahre später nachbaubar,
solange dieselbe Umgebung dazu genannt wird:

```sh
# im Abbild der ExApp, weil dort Pillow in der gepinnten Fassung liegt und die
# Prüfsumme an der Rasterung der Schrift hängt
docker run --rm --user 0:0 --entrypoint python3 \
  -v <repo>/scripts:/w/scripts:ro -v <repo>/testdata:/w/testdata:ro \
  -v /mnt/corpus:/out \
  ghcr.io/street1983nk/findling_backend@sha256:bb8f17e7d18df86b410308ee06bb2a6935dbbd183f0c6fcd032ab1ef17234544 \
  /w/scripts/dev/build_load_corpus.py --seed phase5-full --files 50000 --out /out
```

Zwei Seeds und zwei Prüfsummen, jede mit der Umgebung, in der sie gilt:

| Lauf | Seed | Umgebung | Dateien | Bytes | Listen-Prüfsumme |
|---|---|---|---|---|---|
| Trockenlauf | `phase5-dry` | Abbild der ExApp, Pillow 12.3.0 | 500 | 246.452.632 | `afe5de552ae9cdf7a515326e7d0787a9133b4dfef3c08e75f41f9ad5db95a5d0` |
| Trockenlauf | `phase5-dry` | Entwicklungsrechner, Plan 05-05 | 500 | 245.695.552 | `cac56ed1801efb3e691b28088c363c84d8941670394f5fed95ab19359b17d530` |
| Volllauf | `phase5-full` | offen | 50.000 | offen | offen |

Warum es zwei sind und welche wofür gilt, steht oben im Abschnitt zum
Trockenlauf.
