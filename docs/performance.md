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
| Grenzwert für den Spitzenwert | festgelegt | 2026-09-03 |
| AIO-Grundlast, Generalprobe cpx22 | gemessen, 290 MB Höchststand | 2026-09-03 |
| Beitrag von HaRP, Generalprobe cpx22 | gemessen, 55 MB | 2026-09-03 |
| Installation auf der Box, Generalprobe cpx22 | durchgeführt und belegt | 2026-09-03 |
| AIO-Grundlast, ARM | FEHLT NOCH | wartet auf Bestand |
| Findling im Volllauf, 50.000 Dateien | FEHLT NOCH | Pläne 05-12 und 05-14 |
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

Der Lastkorpus entsteht aus einem Seed und ist damit Jahre später nachbaubar:

```sh
python scripts/dev/build_load_corpus.py --seed phase5-full --files 50000 --out /mnt/corpus
```

Der Trockenlauf mit 500 Dateien verwendet den Seed `phase5-dry` und hat die
Listen-Prüfsumme
`cac56ed1801efb3e691b28088c363c84d8941670394f5fed95ab19359b17d530`.
