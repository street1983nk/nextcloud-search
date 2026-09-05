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

Bestand gab es nicht. Am 04.09.2026 war `cax11` erneut in keiner Region zu
haben, zwei Erzeugungsversuche wurden abgewiesen, und ein Telefonat des
Betreibers mit dem Anbieter am selben Tag hat ergeben, dass die Knappheit
Monate läuft. Diese Auskunft schlägt jede Lesung der API. Der ARM-Lauf ist
deshalb auf eine Maschine eines anderen Anbieters umgezogen, ausgewählt als
CAX11-Äquivalent und nicht als etwas Besseres.

| | Generalprobe | ARM-Lauf |
|---|---|---|
| Maschine | Hetzner cpx22, x86 | AWS m7g.large, arm64, Speicher auf 4 GB gedeckelt |
| Zustand | gelaufen 2026-09-03 bis 04, Box abgebaut | läuft seit 2026-09-04 |
| Umfang | vollständig | **vollständig, alles noch einmal** |
| AIO über HaRP, Grundlast, Volllauf, Störfälle | ja | ja, auf eigener Hardware |
| Trägt die Store-Aussage | **nein** | ja |

### Warum eine m7g.large als CAX11 gilt, und woran das hängt

Die Zielmaschine der Entscheidung D-01 ist eine CAX11: zwei Kerne, 4 GB, 40 GB
Systemplatte, arm64. Die Ersatzmaschine ist nach genau diesen vier Größen
gewählt, und bei einer davon musste nachgeholfen werden.

| Größe | CAX11 | m7g.large | gleich? |
|---|---|---|---|
| Architektur | arm64, Ampere Altra | arm64, AWS Graviton3 | ja, beides aarch64 |
| Kerne | 2 vCPU, geteilt | 2 vCPU | ja |
| Arbeitsspeicher | 4 GB | 8 GB laut Typ, **vom Kernel auf 4 GB gedeckelt** | ja, nach dem Deckel |
| Systemplatte | 40 GB | 40 GB gp3 | ja, mit einem Unterschied, siehe unten |

Der Deckel ist der Kern dieser Parität und keine Kosmetik. Gemessen wird in
diesem Bericht der **Abstand zur Decke**: der Seitencache des Index, die Halde
von tesseract und die Grundlast von AIO streiten sich um genau den Speicher, der
nicht da ist. Eine Messung auf 8 GB sagt über eine 4-GB-Box nichts, auch wenn
die Kurve gleich aussieht, weil der Kernel unter Druck andere Entscheidungen
trifft.

Gesetzt ist der Deckel als Kernelparameter, in einer eigenen Datei und nicht
durch Überschreiben der Zeile des Cloud-Abbilds:

```
/etc/default/grub.d/99-mem4g.cfg
GRUB_CMDLINE_LINUX_DEFAULT="$GRUB_CMDLINE_LINUX_DEFAULT mem=4G"
```

Die Erweiterung statt der Ersetzung ist Absicht: die Konsolenparameter des
Abbilds müssen stehen bleiben, sonst verliert die Maschine ihre serielle
Ausgabe, und das merkt man erst, wenn man sie braucht. Drei Zahlen sind vor
jedem Lauf gegengelesen und stehen in jeder Messreihe dieses Berichts:

```
free -h   ->  3.9Gi        (free -m sagt 3958)
nproc     ->  2
uname -m  ->  aarch64
```

Was mit dem Umzug **nicht** gleich bleibt, und wo es im Bericht auftaucht: der
Datenträger. Die Systemplatte der CAX11 ist lokaler NVMe-Speicher ohne
ausgewiesene Grenze, die der Ersatzmaschine ist ein Netzwerkdatenträger vom Typ
gp3 mit 3000 IOPS und 125 MB/s. Diese Drosselung ist die eine Größe, in der die
Ersatzmaschine schlechter ist als das Original, und sie trifft ausgerechnet den
Posten, der in diesem Lauf die Uhr bestimmt: das Lesen von 20 GB Korpus und das
Schreiben des Index. Wo eine Laufzeit genannt wird, steht sie deshalb dabei.

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
gekennzeichnet, und die ARM-Zeile daneben als **ARM m7g.large**. Beide bleiben
stehen; die Generalprobe wird nicht durch die schärfere Messung ersetzt, weil
zwei Reihen auf zwei Architekturen mehr sagen als eine.

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
| Vorbereitung des Volllaufs, Generalprobe cpx22 | Abbild nachgerechnet, geräumt, Korpus erzeugt | 2026-09-04 |
| Härtungsprobe unter harter Grenze | gefahren, 2 GB, `memory.events` durchgehend null | 2026-09-04 |
| **Findling im Volllauf, 50.000 Dateien, Generalprobe cpx22** | **gemessen, 428,6 MB Spitze, 10 h 14 min, kein Speichertod** | 2026-09-04 |
| Störfall-Drills, Generalprobe cpx22 | alle drei durchgespielt, mit ihren Grenzen, einer mit Nachtrag | 2026-09-04 |
| Kosten des Tests | aus den Preisen dieses Kontos, 0,82 EUR brutto | 2026-09-04 |
| Abbau der Generalprobe cpx22 | durchgeführt, Server, Volume und Firewall gegen die API geprüft | 2026-09-04 |
| Parität der Ersatzmaschine | gesetzt und gegengelesen, `mem=4G`, drei Zahlen | 2026-09-04 |
| Einrichtung der ARM-Box, m7g.large | durchgeführt und belegt, samt Gegenprobe des containerd-Funds | 2026-09-04 |
| **AIO-Grundlast, ARM m7g.large** | **gemessen, 260 MB gleichzeitiger Höchststand** | 2026-09-04 |
| **Beitrag von HaRP, ARM m7g.large** | **gemessen, 53 MB** | 2026-09-04 |
| Codestand des ARM-Laufs | Baumhash beider Hälften nachgerechnet, Abbild auf der Box gebaut | 2026-09-04 |
| Korpus des ARM-Laufs | erzeugt, 50.000 Dateien, 20.208.046.426 Byte, Prüfsumme im Bericht | 2026-09-04 |
| **Findling im Volllauf, 50.000 Dateien, ARM m7g.large** | **gemessen, 422,2 MB Spitze, 12 h 48 min, kein Speichertod, 0 Fehlschläge** | 2026-09-05 |
| Störfall-Drills, ARM m7g.large | alle drei durchgespielt, dazu ein vierter mit dem Neustart der Maschine | 2026-09-05 |
| Zusatzmessung INDEX_WORKERS=2 | gemessen, A/B über 200 Scans, Wegwerf-Abbild | 2026-09-05 |
| Kosten des ARM-Laufs | gerechnet, aus Laufzeit und belegten Sätzen | 2026-09-05 |
| Abbau der ARM-Box | steht aus, er gehört dem Betreiber nach der Abnahme dieses Berichts | offen |

Was fehlt, ist hier ausdrücklich als fehlend benannt und nicht ausgelassen.

## Die Umgebung

### Die beiden Maschinen

| Posten | Generalprobe cpx22 | ARM-Lauf m7g.large |
|---|---|---|
| Architektur | x86_64 | arm64, AWS Graviton3, 2,6 GHz |
| Kerne | 2 vCPU, geteilt | 2 vCPU |
| Arbeitsspeicher | 4 GB (3814 MB nutzbar) | 8 GB laut Typ, per `mem=4G` gedeckelt (3958 MB nutzbar) |
| Systemplatte | 80 GB (76 GB nutzbar) | 40 GB gp3, 3000 IOPS, 125 MB/s (38 GB nutzbar) |
| Zusatzplatte | Volume, 50 GB, ext4 | Volume, 60 GB gp3, ext4, 3000 IOPS, 125 MB/s |
| Region | hel1, Helsinki | eu-central-1c, Frankfurt |
| Betriebssystem | Ubuntu 24.04 LTS, Kernel 6.8.0 | Ubuntu 24.04.4 LTS, Kernel 7.0.0-1012-aws |
| cgroup | v2 | v2 |
| Docker | 28er Reihe mit containerd-Snapshotter | 29.8.0, containerd 2.3.4, overlayfs |
| Nextcloud | 33.0.8, All-in-One, PostgreSQL 18.6 | 33.0.8, All-in-One, PostgreSQL, AppAPI 33.0.0 |

Zwei Unterschiede zählen über die Architektur hinaus, und beide gehen zulasten
der ARM-Maschine, was für eine Store-Aussage die richtige Richtung ist.

**Erstens die Systemplatte.** Die Generalprobe hat 76 GB, die ARM-Maschine 40,
genau wie die CAX11. Der Platzdruck, gegen den die Einrichtung unten abgesichert
wird, ist auf der Generalprobe also **milder als im Ernstfall**. Wer die
Reihenfolge dort schludert, merkt es nicht; auf 40 GB läuft die Platte voll.

**Zweitens die Drosselung dieser 40 GB.** Beide Datenträger der ARM-Maschine
sind Netzwerkspeicher vom Typ gp3, und der bringt je Datenträger 3000 IOPS und
125 MB/s mit. Das ist kein theoretischer Deckel: 20 GB Korpus einmal zu lesen
sind bei 125 MB/s knapp drei Minuten reine Übertragungszeit, und die Schreiblast
des Index kommt dazu. Die Systemplatte der CAX11 ist dagegen lokaler
NVMe-Speicher, für den der Anbieter keine Grenze ausweist. Wo dieser Bericht
Laufzeiten nennt, ist das die eine Stelle, an der die Ersatzmaschine die Zahl
nach oben treibt statt nach unten. Für die Speicherfrage, um die es hier geht,
ändert sie nichts.

Die 60 GB Volume kommen nicht aus Bequemlichkeit dazu: der Lastkorpus wiegt
20,12 GB, daneben liegen der Index, das Datenverzeichnis von Nextcloud und die
Abbilder von neun Containern. Zehn GB mehr als in der Generalprobe, weil dort
die Systemplatte die Hälfte davon mitgetragen hat.

### Die Reihenfolge der Einrichtung, und die Falle darin

Drei Dinge müssen auf dem Volume liegen, und zwei davon lassen sich später nicht
mehr verschieben. Die Reihenfolge ist deshalb keine Empfehlung.

1. **Volume einbinden.** Hetzner hängt es mit `automount` selbst ein und schreibt
   den Eintrag in die `fstab`, mit `nofail`. Auf der ARM-Box ist das ein
   Handgriff mehr, und einer, bei dem der naheliegende Weg falsch ist: der
   angeforderte Gerätename (`/dev/sdf`) erscheint auf einer Nitro-Instanz nicht.
   Die Datenträger heißen dort `/dev/nvme?n1` in der Reihenfolge ihres
   Anschlusses, und diese Reihenfolge ist über einen Neustart hinweg nicht
   zugesagt. Gefunden wird der Datenträger deshalb an seiner Größe, formatiert
   mit ext4 und in die `fstab` **per UUID** eingetragen, ebenfalls mit `nofail`:

   ```
   UUID=34959bdb-9d29-46d7-9cbc-f94440e3b89a /mnt/findling ext4 defaults,nofail,x-systemd.device-timeout=10 0 2
   ```

   Ein Eintrag über den Gerätenamen wäre der Fehler, der beim ersten Neustart
   auffällt, und zwar als Nextcloud ohne Datenverzeichnis.
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
Abbild lässt die Systemplatte bei 0 KB und das Volume um 104 KB wachsen. Auf
einer Maschine mit 40 GB Systemplatte wäre der ursprüngliche Zustand nicht
kosmetisch gewesen: die Abbilder von AIO, Postgres, Apache, HaRP und Findling
zusammen hätten die Systemplatte neben Betriebssystem und Protokollen ernsthaft
gefüllt, und das wäre als Fehler von Findling erschienen.

**Auf der ARM-Box ist derselbe Fund noch einmal gemessen worden, in der
umgekehrten Richtung, weil dort die Abhilfe vor dem ersten Abbild stand.** Der
Ablauf war: `data-root` in `/etc/docker/daemon.json` vor der Installation des
Pakets, dann die Installation, dann die Dienste anhalten, `containerd config
default` erzeugen und darin die Wurzel auf das Volume setzen, dann starten. Erst
danach der erste `docker pull`. Die Gegenprobe steht in Zahlen:

| | Generalprobe, ohne die containerd-Zeile | ARM-Box, mit ihr |
|---|---|---|
| Zuwachs Systemplatte nach dem ersten Pull | 400 MB | **4 KB** |
| Zuwachs Volume | nichts | **375 MB** |
| Was `docker info` meldete | das Volume | das Volume |

Ein Detail für den nächsten Leser, weil es eine Viertelstunde gekostet hat: die
Vorgabedatei von containerd 2.3 trägt `version = 4`, und ihr Wurzelfeld ist eine
Zeile, die man ersetzen muss und nicht anhängen darf. Eine selbstgeschriebene
Minimaldatei mit nur der Wurzel darin ist der falsche Weg, weil die Fassung des
Formats dann fehlt; `containerd config default` als Ausgangspunkt ist der
richtige.

Und ein zweites, weil es dieselbe Viertelstunde gekostet hat: `daemon.json`
wurde beim ersten Versuch über eine Kette aus Anführungszeichen geschrieben, die
den Weg über ssh nicht überlebt hat. In der Datei stand danach `{n`, und
`dockerd` sagte dazu "invalid JSON: invalid character 'n' looking for beginning
of object key string". Seitdem reist jedes Skript dieses Laufs als Datei und
nicht als Zeichenkette.

### Was die Umgebung kostet

Die beiden Läufe liegen bei verschiedenen Anbietern, und ihre Kostentabellen
sind deshalb **nicht ineinander umzurechnen**. Die eine ist in Brutto-Euro aus
der Konto-API, die andere in Netto-Dollar aus einer öffentlichen Preisliste. Sie
stehen hier getrennt, mit ihrer Quelle, und dieser Bericht bildet daraus
ausdrücklich keine Vergleichszahl.

#### Die Generalprobe, Hetzner

Abgefragt am 03.09.2026 um 10:48 UTC gegen `/v1/pricing` und `/v1/server_types`
dieses Kontos, also nicht aus einer Preisliste im Netz. Alle Werte brutto, der
Mehrwertsteuersatz des Kontos beträgt 19 Prozent.

| Posten | je Stunde | je Monat |
|---|---|---|
| cpx22 in hel1, Generalprobe | 0,037128 EUR | 23,1931 EUR |
| CAX11 in hel1, nie gemietet | 0,011424 EUR | 7,1281 EUR |
| Volume, 50 GB | 0,004662 EUR | 3,4034 EUR |
| Primäre IPv4 | 0,000952 EUR | 0,5950 EUR |
| Summe Generalprobe | 0,042742 EUR | 27,1915 EUR |

Die CAX11-Zeile bleibt stehen, obwohl diese Maschine nie zustande kam: sie ist
die Zahl, an der sich der Preis der Ersatzmaschine messen lässt.

Zwei Dinge daran sind leicht zu übersehen. Der Preis je GB und Monat des Volumes
wird oft mit 0,057 EUR angegeben; das ist der Nettowert, brutto sind es
0,068068 EUR. Und die öffentliche Adresse steht seit 2024 als eigener Posten auf
der Rechnung. Sie macht gegen eine Box für gut einen Cent je Stunde rund acht
Prozent aus, weshalb `scripts/ops/hetzner_box.sh status` sie mitrechnet.

#### Der ARM-Lauf, AWS

Hier kommen die Sätze **nicht** aus der Konto-API, und der Grund gehört dazu:
der Zugang dieses Laufs trägt `AmazonEC2FullAccess` und sonst nichts, also fehlt
ihm `pricing:GetProducts`. Die Antwort auf die Preisfrage ist ein
`AccessDeniedException`, der den Nutzer und die Aktion nennt. Genommen sind die
Sätze deshalb aus der öffentlichen Preisliste desselben Anbieters, die ohne
Anmeldung erreichbar ist, gefiltert am 04.09.2026 aus der Fassung
`20260903195206` für `eu-central-1` (AmazonEC2, wirksam ab 01.09.) und
`20260831092232` (AmazonVPC). Die gefilterten Zeilen liegen unverändert in
`docs/measurements/2026-09-04-grundlast-m7g/`. Alle Werte **netto in USD**.

| Posten | je Stunde | je Monat |
|---|---|---|
| m7g.large in eu-central-1, On Demand, Linux | 0,097800 USD | 71,394 USD |
| Systemplatte, 40 GB gp3 | 0,005216 USD | 3,808 USD |
| Datenträger, 60 GB gp3 | 0,007824 USD | 5,712 USD |
| öffentliche IPv4, in Benutzung | 0,005000 USD | 3,650 USD |
| **Summe ARM-Lauf** | **0,115840 USD** | **84,564 USD** |

Die Monatszahlen sind mit 730 Stunden gerechnet, so wie der Anbieter seine
Monatspreise für Speicher ausweist.

Drei Anmerkungen, die eine Kostenzeile ohne sie schöner aussehen ließen als sie
ist. Erstens: die Ersatzmaschine kostet je Stunde rund das Achtfache der CAX11,
für die sie einsteht. Das ist der Preis der Verfügbarkeit, und er war dem
Betreiber die Messung wert, weil die Alternative kein Lauf gewesen wäre.
Zweitens: gp3 bringt 3000 IOPS und 125 MB/s je Datenträger ohne Aufpreis mit,
und dieser Lauf bleibt in beiden Grenzen, also kommt für Ein- und Ausgaben nichts
dazu. Drittens: die öffentliche Adresse ist seit dem 01.02.2024 ein eigener
Posten, genau wie bei Hetzner seit 2024. Sie macht hier rund vier Prozent aus,
und `scripts/ops/aws_box.sh status` rechnet sie mit, wenn die Box wirklich eine
trägt. Der Grund für diese Sorgfalt steht ein paar Zeilen weiter oben in der
Hetzner-Tabelle: dort hat genau dieser Posten den Lauf einmal um acht Prozent zu
niedrig gerechnet.

Die Endkosten dieses Laufs stehen am Ende des Berichts. Sie sind **gerechnet und
nicht abgelesen**, aus der Laufzeit und den Sätzen oben, denn dem Zugang dieses
Laufs fehlt auch der Blick auf die Abrechnung. Für eine Maschine, deren Laufzeit
auf die Sekunde bekannt ist, ist das Produkt genauer als ein Abrechnungsposten,
der Tage später erscheint.

Die Miete endet mit dem Test: die Löschung der Box ist ein Pflichtschritt und
kein Aufräumen bei Gelegenheit, denn eine vergessene Box ist eine öffentlich
erreichbare Nextcloud mit Admin-Zugang und eine monatliche Rechnung. Abgeräumt
werden drei Ressourcen, nicht zwei: Box, Volume und die Firewall. Die Firewall
kostet nichts, und genau deshalb ist sie die, die stehen bleibt.

### Warum die ARM-Maschine nicht von diesem Anbieter kommt

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

#### Am 04.09. noch einmal, und dann eine Entscheidung

Der Tag darauf sah gleich aus. `cax11` stand in allen drei Regionen weiter auf
nicht verfügbar, und zwei echte Erzeugungsversuche, `hel1` und `nbg1`, wurden
mit derselben irreführenden Meldung abgewiesen. Es wurde dabei nichts angelegt;
die Suche nach dem Kennzeichen `purpose=findling-phase5` blieb über Server,
Volumes und Firewalls leer.

Dazu ein Widerspruch in der API selbst, der eine Stunde gekostet hätte:
`/datacenters` führte `cax11` zur selben Minute als verfügbar in `hel1-dc2` und
`nbg1-dc3`. Diese Auskunft ist falsch, und sie ist falsch, weil dieser Endpunkt
auf dem Weg nach draußen ist: das Feld `datacenter` eines Erzeugungsaufrufs ist
seit dem 16.12.2025 abgeschafft und antwortet mit "datacenter is deprecated and
cannot be used anymore". Ein Endpunkt, auf dessen Auskunft man nicht mehr handeln
kann, wird nicht gepflegt. `scripts/ops/hetzner_box.sh` fragt ihn seither
weiterhin, aber nur zu einem Zweck: den Widerspruch zu melden, statt dem
fröhlicheren Teil der API zu glauben.

Den Ausschlag gegeben hat keine API, sondern ein Telefonat. Der Betreiber hat am
04.09. beim Anbieter angerufen, und die Auskunft lautet, dass die ARM-Knappheit
Monate läuft. Damit war die Wahl nicht mehr "warten oder messen", sondern
"anderswo messen oder nicht messen", und der Store-Termin dieser Phase
entscheidet diese Frage. Die Ersatzmaschine ist oben beschrieben, samt dem
Speicherdeckel, der sie zur CAX11 macht.

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
   einzelnen gemieteten m7g.large, die als CAX11-Äquivalent geführt wird.
   Wechselnde Nachbarn und ein anderer Datenträger können andere Laufzeiten
   liefern. Übertragbar ist der Speicherverlauf, nicht die Uhr. Und die Parität
   gilt für die vier Größen, an denen sie geprüft ist: Architektur, Kerne,
   nutzbarer Speicher einschließlich Seitencache, Größe der Systemplatte. Sie
   gilt ausdrücklich **nicht** für die Geschwindigkeit dieser Platte, die hier
   gedrosselt und dort lokal ist, und nicht für den Kern selbst: ein Graviton3
   ist kein Ampere Altra.
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
| **ARM m7g.large** | **193 MB** | **260 MB** | **ja** |

Die ARM-Zahlen stammen aus einer eigenen Messung nach demselben Muster und sind
keine umgerechneten. Sie liegen rund zehn Prozent unter den x86-Zahlen, und der
Bericht deutet diesen Abstand ausdrücklich **nicht**: die beiden Läufe
unterscheiden sich in Architektur, Kernel und Serverfassung zugleich, und die
Grundlast von AIO ist nicht der Gegenstand dieses Berichts. Was zählt, ist die
Zahl selbst, denn sie ist der Sockel, auf dem das Findling-Budget steht.

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

Die Zahlen dieses Abschnitts gelten für x86. Auf ARM ist die Grundlast neu
gemessen und nicht umgerechnet; der Abschnitt darunter nennt sie.

### Dieselbe Messung auf ARM

Dreißig Minuten nach demselben Muster, 2026-09-04T15:40:05Z bis 16:07:37Z, ein
eigener Sampler je Container im Abstand von fünf Sekunden, 331 Messpunkte je
Container, dieselben drei Phasen und dieselben 29 Runden gewöhnlicher Aufrufe.
Gelaufen sind auch hier genau sechs Container und kein siebter.

| Container | höchster `anon`-Stand |
|---|---|
| nextcloud-aio-nextcloud | 164 MB |
| nextcloud-aio-mastercontainer | 46 MB |
| nextcloud-aio-apache | 37 MB |
| nextcloud-aio-database | 11 MB |
| nextcloud-aio-redis | 4 MB |
| nextcloud-aio-notify-push | 1 MB |

Die Summe je Zeitpunkt ergibt 193 MB im Mittel und **260 MB im gleichzeitigen
Höchststand**, um 15:54:21Z, also in der Aufrufphase. Die theoretische obere
Schranke, die Summe der sechs Maxima, liegt bei 264 MB: vier MB darüber, die
Zahl hängt also auch hier nicht an der Art der Summenbildung.

Nach Phasen getrennt:

| Phase | Mittel | höchster Stand |
|---|---|---|
| Leerlauf, 12 min | 192 MB | 195 MB |
| unter Aufrufen, 29 Runden | 207 MB | 260 MB |
| Leerlauf, 12 min | 190 MB | 193 MB |

Auch hier stammt der Ausschlag aus der Aufrufphase und fast vollständig aus dem
Nextcloud-Container. Die Aufrufphase dauerte 3 min 29 s statt der sechs Minuten
der Generalprobe, weil zwischen den Runden nur fünf Sekunden Pause liegen; die
Zahl der Runden ist dieselbe, und verglichen wird der gleichzeitige Höchststand
und nicht die Dauer.

Alle sechs Abschlusszeilen melden `oom_killed=false`, und `memory.events` steht
in jedem Zähler auf null. Dieser Lauf führt dort **sieben** Zähler statt sechs:
der Kernel 7.0 bringt `sock_throttled` mit, und der steht wie die anderen auf
null.

Die Rohdaten liegen unter `docs/measurements/2026-09-04-grundlast-m7g/`.

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

#### Derselbe Beitrag auf ARM, und diesmal ist der Vergleich zulässig

Zehn Minuten über alle sieben Container, 124 Messpunkte je Container,
2026-09-04T16:18:57Z bis 16:29:13Z.

| Container | `anon` im Mittel | höchster Stand |
|---|---|---|
| **nextcloud-aio-harp** | **53 MB** | **53 MB** |
| nextcloud-aio-nextcloud | 89 MB | 90 MB |
| alle sieben zusammen, je Zeitpunkt | 231 MB | 234 MB |

**53 MB**, und ebenso flach wie auf x86: über zehn Minuten liegt zwischen
niedrigstem und höchstem Stand weniger als ein MB.

Bei der Generalprobe stand an dieser Stelle die Warnung, dass die beiden Summen
nicht zu vergleichen sind, weil die zweite Messung nach einem Neustart aller
Container lief. Hier ist es umgekehrt, und das ist ein Nebenprodukt eines Fundes
über AIO: das Anhaken von HaRP hat nur den HaRP-Container angelegt und die
anderen sechs unberührt weiterlaufen lassen. Deren PHP-Arbeiter waren also
dieselben, und der Abstand zwischen 234 MB mit HaRP und dem gleichzeitigen Stand
ohne ihn ist wirklich HaRP.

Für die Budgetrechnung des ARM-Laufs: Grundlast 260 MB plus HaRP 53 MB, also
rund **313 MB**. Neben dem Grenzwert von 2,0 GB für Findling bleiben auf der
gedeckelten 4-GB-Box damit rund 1,6 GB für Kernel und Seitencache.

Die Rohdaten liegen unter
`docs/measurements/2026-09-04-grundlast-m7g/mit-harp/`.

#### Ein Fund über AIO, der eine Stunde kosten kann

Das Anhaken von HaRP legt den HaRP-Container an, und das genügt nicht. Die App
`app_api`, ohne die es keine ExApp gibt, wird vom Startskript des
Nextcloud-Containers installiert, und dieses Skript läuft nur beim Start eines
Containers. Nach dem Anhaken stand deshalb ein gesunder HaRP-Container neben
einer Nextcloud, die das Wort `app_api` nicht kannte:

```
occ app_api:daemon:list
There are no commands defined in the "app_api" namespace.
```

Die Abhilfe ist ein Stopp und ein Start über die Schnittstelle von AIO, danach
ist `app_api` da (hier 33.0.0) und der Daemon `harp_aio` registriert. Wer
stattdessen nach einem `occ app:install app_api` greift, umgeht den Weg, den AIO
selbst geht, und bekommt eine Instanz, die anders aussieht als die eines
Nutzers.

Und zwei Dinge über die Anmeldung an dieser Schnittstelle, weil sie zusammen
eine Viertelstunde gekostet haben. Erstens: `GET /api/auth/getlogin` antwortet
mit 302 bei richtigem **und** bei falschem Token, im Fehlerfall nach fünf
Sekunden Strafschlaf. Der Statuscode ist also kein Beweis für eine Sitzung;
geprüft wird sie, indem man eine Seite holt, die nur angemeldet 200 liefert.
Zweitens: AIO würfelt diesen Token bei jedem Containerstart neu und schreibt ihn
in seine Konfiguration, während die Umgebung eines Containers, der nicht neu
gestartet wurde, den alten Wert behält. Die Konfiguration ist die Quelle, nicht
die Umgebung.

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
| **gemessener Spitzenwert `anon`** | 381 MB | **422,2 MB** (ARM), 428,6 MB (Generalprobe) | eine Messung. Der Wert des ARM-Volllaufs ist die Zahl der Store-Aussage. |
| **`memory.peak`** | 455 MB | **970,9 MB** (ARM), 957,7 MB (Generalprobe) | dieselbe cgroup, anderer Maßstab: hier zählt der Dateicache mit. |

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

## Die Vorbereitung des Volllaufs

Zwischen dem Trockenlauf und dem Volllauf liegen vier Schritte. Keiner von ihnen
ist eine Formalie, jeder hat seinen Grund im Trockenlauf, und sie stehen hier,
weil ein Bericht, der nur die Messung zeigt, nicht sagt, woran sie entstanden
ist.

### Erstens: das Abbild trägt die Korrektur, und das ist nachgerechnet

Der Trockenlauf hat einen Fehler gefunden, der jede Tabellendatei unindexierbar
machte. Ein Volllauf gegen ein Abbild ohne diese Korrektur würde dreizehn Stunden
lang den falschen Pfad messen, und zwar für jede fünfte Datei des Korpus. Der
Name eines Kennzeichens ist als Beleg dafür zu wenig, denn ein Kennzeichen kann
jeder vergeben. Nachgerechnet wird deshalb der Inhalt: über jede Python-Datei des
Pakets, auf Zeilenenden vereinheitlicht, weil der Arbeitsbaum auf Windows liegt
und das Abbild auf Linux gebaut ist.

```python
h = hashlib.sha256()
for p in sorted(root.rglob("*.py")):
    data = p.read_bytes().replace(b"\r\n", b"\n")
    h.update(p.relative_to(root).as_posix().encode() + b"\0"
             + hashlib.sha256(data).hexdigest().encode() + b"\n")
```

| Ort | Dateien | Baumhash |
|---|---|---|
| Arbeitsbaum, `backend/src/findling` | 44 | `f305ac09adeae37ede6e210311c32ef2cf2b5d9b7d870409d7b550785046954e` |
| Abbild, `/app/.venv/lib/python3.13/site-packages/findling` | 44 | `f305ac09adeae37ede6e210311c32ef2cf2b5d9b7d870409d7b550785046954e` |

Dieselbe Zahl, also derselbe Code. Zusätzlich gelesen und im Abbild vorgefunden:
die Stelle selbst, `with Path(path).open("rb") as stream` in `extract_xlsx`,
samt der Begründung, die im Arbeitsbaum daneben steht.

| Angabe | Wert |
|---|---|
| Abbild | `localhost:5000/findling_backend:05-12-fix` |
| Kennung des Abbilds | `sha256:00c457bf48a2c531a5bbd8ff0fa589dc861216e57c84746189aaefd9b2d4c19b` |
| erzeugt | 2026-09-03T19:19:38Z, auf der Box gebaut |
| Größe | 138.520.962 Byte |

Warum nicht neu gebaut wurde: zwischen dem Stand, aus dem dieses Abbild entstand,
und dem Stand dieses Berichts liegt keine einzige Änderung unter `backend/`,
`php/` oder `docker/`. Ein neuer Bau ergäbe denselben Inhalt, und der Baumhash
oben sagt genau das, nur ohne die Bauzeit. Der Preis dieser Wahl steht dennoch
in der Rechnung: dieses Abbild ist auf der Messmaschine entstanden und existiert
nur dort, im Unterschied zu dem gezogenen Abbild des ersten Trockenlaufs, das
über seinen Digest in der Registry festgenagelt ist. Der Baumhash ist der
Ausgleich dafür, denn er ist aus dem Arbeitsbaum jederzeit nachrechenbar, auch
wenn die Maschine längst gelöscht ist.

### Zweitens: der Volllauf startet auf einem leeren Index

Drei Dinge aus dem Trockenlauf hätten die Zahlen des Volllaufs verfälscht, und
alle drei sind vorher weggeräumt.

| Was | Warum es weg musste | Wie |
|---|---|---|
| die 500 Dateien des Trockenlaufs | sie zählen sonst im Nenner des Deckungsgrads mit und tauchen in jeder Verdiktzählung wieder auf | von der Platte gelöscht, danach `occ files:scan lasttest`, das 500 Entfernungen meldet |
| 49 Zeilen in `oc_findling_file_state`, davon 32 veraltete `failed(corrupt)` | genau der Befund DI-05-21: eine erfolgreich nachindexierte Datei räumt ihre alte Fehlerzeile nicht weg, der Fehlerbericht des Volllaufs trüge also 32 Zeilen über Dateien, die es nicht mehr gibt | `TRUNCATE oc_findling_queue, oc_findling_file_state, oc_findling_scan_stats` |
| der Index des Trockenlaufs, 587 Dokumente | ein Lauf, der auf einem halb gefüllten Index beginnt, misst nicht, was eine frische Installation misst, und genau darüber wird die Store-Aussage getroffen | `occ app_api:app:unregister findling_backend --rm-data`, danach neu registrieren |

Der dritte Schritt ist der einschneidendste und der wichtigste. `--rm-data`
löscht den Datenspeicher der ExApp, also Index und Zustandsdatenbank des
Containers. Was danach läuft, ist die Lage eines Betreibers am ersten Tag: leerer
Index, voller Bestand. Nebenbei ist das die zweite Beobachtung der Zusage aus
D-16 auf AIO, diesmal in ihrer anderen Richtung: 05-12 hat belegt, dass ein
Abmelden ohne `--rm-data` die Daten stehen lässt, hier ist belegt, dass ein
Abmelden mit `--rm-data` sie nimmt.

### Drittens: der Korpus des Volllaufs

Erzeugt wurde er auf derselben Weise wie der Trockenlauf-Korpus, also im Abbild
der ExApp und nicht im System-Python der Box, und aus demselben Grund: Pillow
liegt dort in der gepinnten Fassung, und es kommt kein Paket auf die Messmaschine,
das nicht ohnehin im Container läuft (T-05-SC).

```
build_load_corpus: seed=phase5-full files=50000 bytes=20208046426
  checksum=c03a880323171d29c5278ed350db277291e39d256e95d5a8654dd4a6c244a274
```

| Angabe | Wert |
|---|---|
| Seed | `phase5-full` |
| Umgebung | Abbild `localhost:5000/findling_backend:05-12-fix`, Pillow 12.3.0 |
| Dateien | 50.000 |
| Gesamtgröße | 20.208.046.426 Byte, also 20,2 GB |
| Listen-Prüfsumme | `c03a880323171d29c5278ed350db277291e39d256e95d5a8654dd4a6c244a274` |
| Beginn | 2026-09-03T19:44:54Z |
| Ende | 2026-09-03T20:13:09Z |
| Dauer der Erzeugung | 1695 s, also 28 Minuten 15 Sekunden |
| Durchsatz | rund 417 Dateien und 140 MB je Minute, durchgehend an einem Kern |

Die Verteilung, wie der Generator sie meldet, und daneben die Gegenprobe von der
Platte, weil eine Zählung, die nur ihre eigene Quelle befragt, nichts prüft:

| Kategorie | Dateien | Anteil | Gegenprobe an den Dateiendungen |
|---|---|---|---|
| einseitige Scans | 9.916 | 19,8 Prozent | zusammen 32.552 `.pdf` |
| mehrseitige Scans | 100 | 0,2 Prozent | (dieselben 32.552) |
| Text-PDF | 22.536 | 45,1 Prozent | (dieselben 32.552) |
| OOXML | 10.016 | 20,0 Prozent | 3.345 `.xlsx`, 3.344 `.pptx`, 3.327 `.docx` |
| OpenDocument | 5.008 | 10,0 Prozent | 2.504 `.odt`, 2.504 `.ods` |
| reiner Text | 2.304 | 4,6 Prozent | 781 `.txt`, 775 `.md`, 748 `.csv` |
| Bild | 100 | 0,2 Prozent | 27 `.webp`, 27 `.jpg`, 23 `.tif`, 23 `.png` |
| über dem Größendeckel | 20 | 0,04 Prozent | 20 `.csv` über 50 MB, zusammen 1.119.433.236 Byte |
| **Summe** | **50.000** | | **50.000 Dateien auf der Platte** |

Beide Zählungen gehen auf. Der OCR-Anteil des Korpus liegt bei 20,0 Prozent,
also genau dort, wo D-02 ihn verlangt, und die 20 Dateien über dem Deckel sind
die Gruppe, die am Ende als `too_large` wieder auftauchen muss; sie sind der
einzige Posten, dessen Verdikt der Generator vorher kennt.

Die Dateien liegen flach in einem Verzeichnis. `occ files:scan lasttest` hat sie
in 42 Sekunden aufgenommen, und `oc_filecache` führt danach genau 50.000 Zeilen
unter `files/loadtest/`.

| Größe | Vor dem Korpus | Nach dem Korpus |
|---|---|---|
| belegt auf dem Volume | 6,2 GB | 26 GB |
| frei auf dem Volume | 41 GB | 22 GB |

22 GB frei sind reichlich für einen Index, der nach der Hochrechnung des
Trockenlaufs rund 700 MB wiegt, und sie sind vor allem weit von den 500 MB
entfernt, ab denen der Container `paused_low_disk` meldet. Der Lauf pausiert also
nicht aus Versehen; der Störfall wird später ausdrücklich herbeigeführt.

### Viertens: die harte Grenze, nach der letzten Registrierung

Der Befund aus 05-12 lautet: jede Registrierung legt einen neuen Container an,
und der kommt ohne Grenze. Die Grenze gehört deshalb ans Ende der Vorbereitung
und nicht an ihren Anfang. Gesetzt wurde sie mit dem Befehl aus 05-12,
wortwörtlich, und danach an zwei Stellen gegengeprüft: beim Docker-Client und im
cgroup selbst.

```sh
docker update --memory=2g --memory-swap=2g nc_app_findling_backend
```

```
docker inspect  Memory=2147483648 MemorySwap=2147483648
                Image=localhost:5000/findling_backend:05-12-fix
memory.max      2147483648
memory.swap.max 0
```

`memory.swap.max 0` ist die Angabe, auf die es ankommt: ein Lauf, der sich nur
durch Auslagern unter der Grenze hält, hätte mit der Zusage nichts zu tun.

Eine Kleinigkeit, die eine Viertelstunde gekostet hat und deshalb hier steht:
`occ app_api:app:register --info-xml` liest den Pfad **im Nextcloud-Container**
und nicht auf dem Wirt, denn dort läuft `occ`. Ein Pfad des Wirtes endet mit
`Failed to read info.xml`, und zwar nachdem die alte Registrierung bereits
entfernt ist. Die Datei gehört also vorher mit `docker cp` hinein.

### Der Beginn des Laufs

| Angabe | Wert |
|---|---|
| Beginn | 2026-09-03T23:13:11Z |
| Vorrat | 50.000 Dateien des Korpus plus 104 des Bestands |
| Index zu Beginn | leer, Datenspeicher neu angelegt |
| Zustandstabellen zu Beginn | leer |
| Sampler | `rss_sampler.sh nc_app_findling_backend 5`, Abstand 5 Sekunden |
| Beobachter der Statusseite | alle 5 Minuten eine vollständige Aufnahme von `/apps/findling/admin/overview` |

## Findling im Volllauf

| Lauf | höchster `anon` | unter 2,0 GB | Laufzeit | OCR-Anteil | Speichertod |
|---|---|---|---|---|---|
| Generalprobe cpx22 | **428,6 MB** (449.441.792 Byte) | ja, 20,9 Prozent davon | 10 h 14 min 14 s | 10.134 von 50.104 Dateien | nein, `oom_kill 0` und `OOMKilled false` |
| **ARM m7g.large** | **422,2 MB** (442.695.680 Byte) | **ja, 20,6 Prozent davon** | 12 h 48 min 47 s | 10.125 von 50.049 Dateien | nein, `oom_kill 0` und `OOMKilled false` |

Die Zeile, die in die Store-Beschreibung geht, ist die zweite. Die erste steht
daneben, weil ein Vergleich der beiden mehr über das Verhalten der Anwendung
verrät als jede von beiden allein, und weil sie zuerst da ist.

### Was der Lauf gemessen hat

| Größe | Wert |
|---|---|
| Crawl eingereiht | 2026-09-03T23:13:11Z |
| erstes Verdikt | 2026-09-03T23:18:51Z |
| letztes Verdikt | 2026-09-04T09:27:25Z |
| Dauer vom Anstoß bis zum letzten Verdikt | 36.854 s, also 10 h 14 min 14 s |
| Arbeitsvorrat | 50.104 Dateien: die 50.000 des Korpus und 104 des Bestands |
| indexiert | 50.068 |
| fehlgeschlagen | **0** |
| übersprungen | 36: `too_large` 20, `empty_text` 14, `image_not_ocrable` 2 |
| ohne Verdikt | keine, 50.068 plus 36 sind genau 50.104 |
| mit OCR | 10.134 Dateien |
| Durchsatz | 1,36 Dateien je Sekunde über den ganzen Lauf |
| Textzeichen im Index | 1.355.205.169, davon 37.407.953 aus der OCR-Spur |
| Zeilen in der ACL-Tabelle | 50.068, also genau eine je indexiertem Dokument |

Die Verdikte gegen die Verteilung, die der Generator gemeldet hat, Kategorie für
Kategorie:

| Erzeugt | Anzahl | Erwartetes Verdikt | Gemessen |
|---|---|---|---|
| über dem Größendeckel | 20 | `skipped(too_large)` | **20**, die Zahl stimmt auf die Datei |
| einseitige Scans | 9.916 | indexiert über die OCR-Spur | in den 10.134 mit `ocr_used` enthalten |
| mehrseitige Scans | 100 | indexiert über die OCR-Spur, 8 Seiten je Datei | ebenda |
| Bilder | 100 | indexiert über die OCR-Spur | ebenda |
| Text-PDF, OOXML, OpenDocument, reiner Text | 39.864 | indexiert über die Textspur | in den 39.970 ohne `ocr_used` enthalten |
| aus dem Bestand der Instanz | 104 | gemischt | 14 `empty_text` und 2 `image_not_ocrable` stammen von hier, aus Vorlagen ohne Text und den Beispielfotos |

Der einzige Posten, dessen Verdikt vorher feststand, ist der Größendeckel, und er
stimmt: 20 erzeugt, 20 als `too_large` beurteilt.

Die OCR-Zahl geht ebenfalls auf. Der Generator hat 9.916 einseitige Scans, 100
mehrseitige und 100 Bilder geschrieben, zusammen 10.116 Dateien ohne Textinhalt;
gemessen sind 10.134 mit `ocr_used`. Die 18 Dateien Unterschied stammen aus dem
Bestand der Instanz, nämlich aus den Beispielfotos, die Nextcloud jedem neuen
Nutzer mitgibt.

Und der Befund des Trockenlaufs ist auf hundertfacher Menge erledigt: dort endeten
alle 32 Tabellen als "Datei beschädigt", hier sind alle 3.345 `.xlsx` indexiert
und die Gruppe `corrupt` kommt in keiner der 130 Aufnahmen der Statusseite vor.
Das ist die Wirkung der Korrektur aus 05-12.

### Der OOM-Beweis, vierteilig

Ein Text, der "kein OOM" behauptet, weil im Protokoll kein "Killed" steht, findet
den Fall nicht, in dem ein Kindprozess der cgroup getötet wurde. Deshalb vier
Belege statt einem, alle am 2026-09-04T10:02:50Z erhoben, also nach dem Lauf und
vor jedem Eingriff:

```
--- memory.events ---           --- memory.events.local ---
low             0               low             0
high            0               high            0
max             0               max             0
oom             0               oom             0
oom_kill        0               oom_kill        0
oom_group_kill  0               oom_group_kill  0

--- docker inspect ---
OOMKilled=false Status=running ExitCode=0 RestartCount=0
Memory=2147483648 MemorySwap=2147483648

--- die harte Grenze, wie der Kernel sie führt ---
memory.max      2147483648

--- die Abschlusszeile des Samplers ---
findling-rss summary samples=7782 max_anon=449441792 peak=1004195840
  events=[low=0 high=0 max=0 oom=0 oom_kill=0 oom_group_kill=0] oom_killed=false
```

| Teil | Aussage |
|---|---|
| `memory.events` und `memory.events.local` | Der Kernel hat in dieser cgroup nie an die Grenze angeschlagen. Nicht nur `oom_kill` steht auf null, auch `max` und `high`: die Grenze wurde in 36.854 Sekunden **kein einziges Mal** berührt. |
| `docker inspect .State.OOMKilled` | `false`, dazu `RestartCount 0` und `ExitCode 0`: der Container, der gemessen wurde, ist derselbe, der gestartet wurde. |
| höchster `anon` aus der CSV | **449.441.792 Byte, also 428,6 MB**, erreicht am 2026-09-03T23:38:51Z, 26 Minuten nach dem Anstoß. Das ist die Zahl der Store-Aussage. |
| `memory.peak` und der Dateicache | **1.004.195.840 Byte, also 957,7 MB.** Der Abstand von 529 MB ist der Seitencache des Index, der als Datei in den Speicher abgebildet wird. Am Ende des Laufs standen `anon 251.699.200`, `file 92.176.384` und `slab 10.088.896` nebeneinander. |

Warum die Store-Zahl aus `anon` kommt, steht im Abschnitt "Drei Zahlen, die nicht
dasselbe sind" oben. Der Volllauf belegt die Begründung jetzt mit Zahlen statt mit
einer Erwartung: `memory.peak` liegt beim 2,2fachen von `anon`, und der ganze
Unterschied ist zurückforderbarer Cache, den der Kernel unter Druck hergibt, ohne
dass ein Prozess davon etwas merkt. Eine Store-Aussage aus `memory.peak` würde die
Anwendung um mehr als das Doppelte schlechter darstellen, als sie ist.

**Der Grenzwert war 2,0 GB, gemessen sind 428,6 MB, das sind 20,9 Prozent.** Der
Lauf besteht.

Eine Einschränkung, die zur Härtungsprobe gehört und deshalb hier steht:
`memory.swap.max` stand unmittelbar nach dem Setzen der Grenze auf `0` und am Ende
des Laufs auf `max`. Was die Aussage trägt, ist nicht diese Datei, sondern die
Maschine: sie hat überhaupt keinen Auslagerungsbereich (`free -m` meldet
durchgehend `Swap 0 0 0`), es konnte also in keinem Augenblick ausgelagert werden.
`memory.max` stand über den ganzen Lauf unverändert auf 2.147.483.648.

### Die Kurve

7.782 Messpunkte im Abstand von fünf Sekunden, vom Start des Samplers um
2026-09-03T23:13:02Z bis zu seinem geordneten Ende um 2026-09-04T10:03:29Z. Der
Bericht führt sie verdichtet, die Rohdaten liegen als CSV unter
`docs/measurements/2026-09-04-volllauf-cpx22/volllauf.csv`, weil die Maschine
gelöscht wird und eine Zahl ohne ihre Reihe eine Behauptung ist.

| Stunde (UTC) | Messpunkte | `anon` Minimum | `anon` Median | `anon` Spitze | `memory.peak` am Ende der Stunde |
|---|---|---|---|---|---|
| 09-03 23 | 562 | 108 MB | 245 MB | **429 MB** | 829 MB |
| 09-04 00 | 719 | 173 MB | 255 MB | 391 MB | 958 MB |
| 09-04 01 | 717 | 176 MB | 334 MB | 423 MB | 958 MB |
| 09-04 02 | 718 | 192 MB | 360 MB | 376 MB | 958 MB |
| 09-04 03 | 718 | 180 MB | 361 MB | 406 MB | 958 MB |
| 09-04 04 | 717 | 235 MB | 361 MB | 422 MB | 958 MB |
| 09-04 05 | 718 | 213 MB | 362 MB | 423 MB | 958 MB |
| 09-04 06 | 718 | 210 MB | 363 MB | 424 MB | 958 MB |
| 09-04 07 | 717 | 183 MB | 364 MB | 426 MB | 958 MB |
| 09-04 08 | 718 | 183 MB | 364 MB | 425 MB | 958 MB |
| 09-04 09 | 718 | 183 MB | 240 MB | 426 MB | 958 MB |
| 09-04 10 | 42 | 240 MB | 240 MB | 240 MB | 958 MB |

Drei Dinge, die man an dieser Reihe sieht und an einer einzelnen Zahl nicht.

Erstens: **die Spitze fällt in die erste halbe Stunde und wird danach nie wieder
erreicht.** Sie liegt dort, wo die Textspur unter Volllast lief und der
Schreibpuffer seine ersten großen Vereinigungsläufe fuhr. Die acht Stunden reiner
OCR-Arbeit danach kosten weniger Speicher, nicht mehr.

Zweitens: **die Kurve steigt nicht.** Der Median liegt in jeder Stunde zwischen
240 und 364 MB, obwohl der Index von null auf 726 MB und der Bestand von null auf
50.000 Dokumente wächst. Ein Speicherleck über zehn Stunden hätte hier eine
Steigung, und es gibt keine.

Drittens: **`memory.peak` steht ab der zweiten Stunde still.** Der Wert ist ein
Höchststand seit dem Start und wird von 958 MB nie mehr überschritten, obwohl er
den Dateicache mitzählt: der Kernel hält den Cache dieser cgroup von selbst weit
unter der Grenze, ohne dass er dazu räumen musste (`memory.events` low und high
stehen auf null).

### Die Prognose, und wo sie danebenlag

| Posten | Prognose 05-12 | Gemessen | Abweichung |
|---|---|---|---|
| Textspur, rund 40.000 Dateien | 0,43 s je Datei, 4,8 h | rund 0,19 s je Datei, 2,2 h | die Prognose war mehr als doppelt so hoch |
| OCR-Spur, 10.134 Dateien | 2,80 s je Seite, 8,3 h | 3,16 s je Datei, rund 7,9 h | die Prognose war knapp richtig |
| **Summe** | **13,1 h** | **10,2 h** | **22 Prozent schneller** |

Die 3,16 s je OCR-Datei sind sauber getrennt gemessen und nicht abgeleitet: von
2026-09-04T01:43Z an lief nur noch die OCR-Spur, und in den 27.808 Sekunden bis
zum Ende kamen 8.788 Dokumente dazu. Sie enthalten Abholung, Rasterung, tesseract
und Indexschreibung, während die 2,80 s der Prognose nur tesseract waren; unter
diesem Vorbehalt lag die Prognose des Trockenlaufs für den teuersten Posten des
Laufs richtig.

Der Fehler steckt in der Textspur, und er hat einen benennbaren Grund: die 0,43 s
je Datei stammten aus den ersten 170 Sekunden des Trockenlaufs, also aus einem
Anlauf, in dem der Container seine Wortliste lädt, den Kompositum-Automaten baut
und die Warteschlange erst gefüllt wird. Über 40.000 Dateien verteilt sich dieser
Anlauf auf nichts. **Eine Prognose aus dem Anfang eines kurzen Laufs überschätzt
den Dauerbetrieb**, und zwar hier um den Faktor zwei.

Was das für den ARM-Lauf heißt: die Steuergröße ist die OCR-Spur, sie macht 77
Prozent der gemessenen Laufzeit aus. Kostet tesseract auf dem Ampere-Kern das
Zweifache, werden aus 7,9 h rund 15,8 h und aus der Summe rund 18 h. Beim
Dreifachen sind es rund 26 h. Die Spanne bleibt bis zum ARM-Lauf offen, aber sie
ist jetzt an einer gemessenen und nicht mehr an einer geschätzten Zahl aufgehängt.

### Die Größe des Index

| Größe | Wert |
|---|---|
| Index nach dem Lauf | 761.374.910 Byte bei 50.068 Dokumenten |
| je Dokument | 15.207 Byte |
| Korpus auf der Platte | 20.208.046.426 Byte |
| Index gegen Korpus | 3,8 Prozent |
| Hochrechnung des Trockenlaufs | rund 707 MB |
| Abweichung der Hochrechnung | 2,7 Prozent |

Die Hochrechnung aus 587 Dokumenten hat den Index über 50.068 Dokumente auf 2,7
Prozent genau getroffen. Das ist mehr Glück als Methode, aber es sagt etwas über
die Sache: die Indexgröße wächst linear mit dem Text und nicht mit dem Bestand,
und der Text je Dokument ist in einem erzeugten Korpus eben konstant. Die Fußnote
aus dem Trockenlauf gilt unverändert und gehört zu jeder Verwendung dieser Zahl:
ein echter Bestand mit demselben Byteumfang trägt mehr Text und erzeugt einen
größeren Index. Phase 3 hatte 3 bis 6 GB veranschlagt.

### Die Statusseite über den ganzen Lauf

130 Aufnahmen im Abstand von fünf Minuten, keine einzige davon fehlgeschlagen, von
2026-09-03T23:13:08Z bis 2026-09-04T10:01:28Z. Die verdichtete Reihe liegt unter
`docs/measurements/2026-09-04-volllauf-cpx22/statusseite.csv`. Elf davon, weil der
Plan drei verlangt und eine Auswahl von drei sich immer aussuchen lässt:

| Zeitpunkt | Zustand | eingereiht | Dokumente | Deckungsgrad | Index |
|---|---|---|---|---|---|
| 23:13:08Z | `idle` | 0 | 0 | noch keiner | 2.254 Byte |
| 23:18:09Z | `running` | 549 | 0 | noch keiner | 2.254 Byte |
| 23:43:18Z | `running` | 2.110 | 7.886 | 78 Prozent, vorläufig | 141 MB |
| 00:43:38Z | `running` | 6.316 | 27.669 | 81 Prozent, vorläufig | 501 MB |
| 01:43:57Z | `running` | 8.786 | 41.280 | 82 Prozent, endgültig | 741 MB |
| 03:44:33Z | **`stalled`** | 6.464 | 43.602 | 87 Prozent | 746 MB |
| 05:45:08Z | **`stalled`** | 4.208 | 45.858 | 91 Prozent | 751 MB |
| 07:45:45Z | **`stalled`** | 1.954 | 48.112 | 96 Prozent | 757 MB |
| 09:16:14Z | **`stalled`** | 222 | 49.844 | 99 Prozent | 761 MB |
| 09:36:20Z | `idle` | 0 | 50.068 | 99 Prozent | 761 MB |
| 10:01:28Z | `idle` | 0 | 50.068 | 99 Prozent | 761 MB |

Das Unauffällige zuerst, weil eine Liste, die nur Auffälliges enthält, nicht sagt,
wie weit geschaut wurde. Über alle 130 Aufnahmen hinweg gilt: `failed` steht
durchgehend auf null, `backendReachable` durchgehend auf wahr, der
Versionsgleichstand durchgehend auf `match`, `lowDisk` durchgehend auf falsch, die
Dokumentzahl wächst monoton, und die ACL-Zeilen sind in jeder einzelnen Aufnahme
genau so viele wie die Dokumente. Der Deckungsgrad wächst monoton von 78 auf 99
Prozent und wird nie über hundert; die Kachel meldet ihn bis 01:43Z ausdrücklich
als vorläufig, weil noch nicht jeder Mount durchlaufen war, und danach nicht mehr.

Und jetzt das Auffällige.

**Die Seite behauptet acht Stunden lang, die Indexierung komme nicht voran,
während sie 6.500 Dokumente indexiert.** Von 02:01Z bis 09:27Z steht `runState`
auf `stalled`, und die Seite zeigt den Satz "Indexing has not progressed for %s.
Background jobs may not be running." Die Zeitspanne darin wächst bis auf über acht
Stunden.

Der Grund ist keine Störung, sondern eine Regel, die für diesen Lauf nicht gebaut
war. `AdminViewService::runState` liest `stalled`, wenn Arbeit wartet und der
letzte Hintergrundauftrag **dieser App** länger als 1800 Sekunden zurückliegt. Der
Crawl war um 01:30:49Z fertig, danach hatte diese App keinen Hintergrundauftrag
mehr auszuführen, und der Zeitstempel stand still. Der Container arbeitete
weiter, aber er quittiert über OCS und nicht über einen Hintergrundauftrag, also
sieht ihn diese Regel nicht.

Auf einer gewöhnlichen Instanz fällt das nicht auf, weil der Crawl und die
Inhaltsarbeit ungefähr gleichzeitig enden. Auf einer 4-GB-Box mit 20 Prozent Scans
ist der OCR-Nachlauf **die Mehrheit der Laufzeit**, und genau dort steht die
falsche Anschuldigung. Notiert als DI-05-22, nicht behoben: welche Größe `stalled`
messen soll, ist eine Entscheidung über die Bedeutung der Kachel und keine Zeile
in einer Datei.

Zwei kleinere Beobachtungen aus derselben Reihe:

- Die Restzeitschätzung fällt schon um 01:43Z auf null, während noch acht Stunden
  Arbeit vor dem Container liegen. Sichtbar wird sie dabei nicht: sobald jeder
  Mount durchlaufen ist, rendert die Seite den Vorabschätzungsblock nicht mehr.
  Die Zahl ist also falsch und wird nicht gezeigt, was in dieser Reihenfolge das
  kleinere Übel ist, aber es heißt auch, dass die Seite für den längsten Abschnitt
  des Laufs keine Restzeit mehr anbietet.
- Der Deckungsgrad bleibt bei 99 Prozent stehen, obwohl der Lauf fertig ist, und
  die Zahl dahinter ist richtig gerechnet: der Nenner lautet 50.084 und nicht
  50.104, weil die 20 Dateien über dem Größendeckel ausdrücklich herausgenommen
  sind (`deliberatelyLeftOut`), während die 16 übrigen Übersprungenen drin
  bleiben. 50.068 von 50.084 sind 99,97 Prozent, und die Kachel rundet ab. Es
  stimmt also und sieht trotzdem nach einem Rest aus, der noch kommt.

## Der ARM-Volllauf: dieselbe Messung auf der Zielarchitektur

Dies ist die Messung, aus der die Store-Aussage kommt. Sie erbt keine Zahl aus
der Generalprobe: derselbe Korpus, dieselbe harte Grenze, dieselben Beobachter,
neu gefahren auf arm64 mit dem Abbild, das die drei Korrekturen aus 05-20 trägt.
Die Rohdaten liegen unter `docs/measurements/2026-09-04-volllauf-m7g/`.

### Der Beginn, und der Fehlstart davor

| Angabe | Wert |
|---|---|
| App eingeschaltet | 2026-09-04T17:29:50Z |
| erster Hintergrundauftrag, Crawl beginnt | 2026-09-04T17:32:26Z |
| erstes Verdikt | 2026-09-04T17:46:36Z |
| letztes Verdikt | 2026-09-05T06:35:23Z |
| Dauer vom ersten bis zum letzten Verdikt | 46.127 s, also 12 h 48 min 47 s |
| Arbeitsvorrat | 50.049 Dateien: 50.000 des Korpus und 49 des Bestands |
| Sampler | `rss_sampler.sh nc_app_findling_backend 5`, 9.622 Messpunkte |
| Beobachter der Statusseite | 161 vollständige Aufnahmen im Abstand von 5 Minuten |

Zwischen dem Einschalten und dem ersten Verdikt liegen siebzehn Minuten, und
davon sind vierzehn ein Fehlstart, der in `00-start.txt` steht: die
Warteschlange füllte sich bis auf 4.048 Zeilen, während der Container keine
einzige davon abholte. Ursache war ein `docker restart` bei der Prüfung des
HTTP/3-Wegs kurz zuvor, und die Folge davon ist der Befund, der weiter unten als
Drill 1b eine eigene Messung bekommt: ein Containerstart, der nicht von AppAPI
kommt, hinterlässt einen Container, der Suchen beantwortet und nie wieder
indexiert. Behoben wurde er mit `occ app_api:app:disable` und `enable`, und ab
17:46:40Z lief der Lauf wirklich.

### Was der Lauf gemessen hat

| Größe | Wert |
|---|---|
| indexiert | **50.021** |
| fehlgeschlagen | **0** |
| übersprungen | 28: `too_large` 20, `empty_text` 7, `image_not_ocrable` 1 |
| ohne Verdikt | keine, 50.021 plus 28 sind genau 50.049 |
| mit OCR | 10.125 Dateien, davon 10.117 indexiert und 8 übersprungen |
| Durchsatz | 1,09 Dateien je Sekunde über den ganzen Lauf |
| Textzeichen im Index | 1.354.887.410, davon 37.407.860 aus der OCR-Spur |
| Zeilen in der ACL-Tabelle | 50.021, also genau eine je indexiertem Dokument |
| Dokumente im Tantivy-Index | 50.021, dieselbe Zahl noch einmal |
| Index nach dem Lauf | 761.082.220 Byte, 15.215 Byte je Dokument, 3,77 Prozent des Korpus |
| Versionsgleichstand | `match`, 1.0.0 auf beiden Seiten, `reindexRequired` falsch |

Über den ganzen Lauf hat der Container **fünf** Zeilen auf Warnstufe
geschrieben und keine einzige auf Fehlerstufe. Vier davon stehen zwischen
17:23:08Z und 17:23:55Z, also bevor die App überhaupt eingeschaltet war: drei
sind die geordnete Rückstufung eines Containers, dessen Gegenstelle noch nicht
existiert ("next attempt in 15 s", "in 30 s", dann "at most one attempt every
300 s"), und die vierte ist der gescheiterte Aufstieg auf HTTP/3 aus DI-05-35.
Die fünfte ist die einzige Warnung aus dreizehn Stunden Arbeit, und sie bekommt
weiter unten einen eigenen Absatz.

### Die Verdikte gegen die Verteilung des Generators, Endung für Endung

Die Generalprobe hat diese Gegenrechnung auf der Ebene der Kategorien geführt.
Hier steht sie auf der Ebene der Dateiendungen, weil sie dort vollständig
aufgeht und keine Sammelzeile mehr braucht.

| Endung | Korpus, von der Platte gezählt | Textspur | OCR-Spur | übersprungen | Bestand der Instanz |
|---|---|---|---|---|---|
| `.pdf` | 32.552 | 22.539 | 10.016 | 0 | 3 |
| `.xlsx` | 3.345 | 3.345 | 0 | 0 | 0 |
| `.pptx` | 3.344 | 3.344 | 0 | 0 | 0 |
| `.docx` | 3.327 | 3.328 | 0 | 0 | 1 |
| `.odt` | 2.504 | 2.515 | 0 | 0 | 11 |
| `.ods` | 2.504 | 2.510 | 0 | 0 | 6 |
| `.odp` | 0 | 11 | 0 | 0 | 11 |
| `.txt` | 781 | 781 | 0 | 0 | 0 |
| `.md` | 775 | 783 | 0 | 0 | 8 |
| `.csv` | 768 | 748 | 0 | **20** | 0 |
| `.jpg` | 27 | 0 | 28 | **7** | 8 |
| `.webp` | 27 | 0 | 27 | 0 | 0 |
| `.png` | 23 | 0 | 23 | **1** | 1 |
| `.tif` | 23 | 0 | 23 | 0 | 0 |

Vier Aussagen stehen in dieser Tabelle, und jede einzelne ist der Grund, warum
sie so ausführlich ist.

**Erstens: der Größendeckel stimmt auf die Datei.** Der Generator hat 20 Dateien
über 50 MB geschrieben, alle mit der Endung `.csv`, und genau 20 `.csv` sind als
`too_large` beurteilt. Die 768 erzeugten `.csv` minus 20 sind die 748 der
Textspur.

**Zweitens: keine einzige Datei ist auf der falschen Spur gelandet.** Der
Generator hat 9.916 einseitige und 100 mehrseitige Scans geschrieben, zusammen
10.016 PDF ohne Textebene, und exakt 10.016 PDF sind über die OCR-Spur
gegangen. Die 22.536 Text-PDF mit ihrem einen gescannten Anhang sind sämtlich
auf der Textspur geblieben. Das ist die Zusage, die `build_load_corpus.py` im
Kommentar an `build_text_pdf` gibt ("far below the share at which
findling.extract.pdf declares a whole document scanned"), und sie hält auf
22.536 Dateien.

**Drittens: alle 100 Bilder des Korpus wurden gelesen.** 27 `.jpg`, 27 `.webp`,
23 `.png` und 23 `.tif`, jedes über tesseract, keines übersprungen.

**Viertens: die acht Ausnahmen sind sämtlich Bestand und nicht Korpus.** Die
sieben `empty_text` sind die Beispielfotos, die Nextcloud jedem neuen Konto
mitgibt, und das eine `image_not_ocrable` ist das Nextcloud-Logo. Das sind
Bilder ohne Schrift, und "kein Text darin" ist über sie das richtige Urteil.
Rechnet man den Bestand zusammen, kommen 41 indexierte und 8 übersprungene
Dateien heraus, zusammen 49, und genau 49 Dateien führt die Crawl-Statistik für
diesen Speicher. Vom Korpus selbst sind 49.980 von 50.000 indexiert, und die
fehlenden 20 sind der Größendeckel.

### Der OOM-Beweis, vierteilig

Alle Teile am 2026-09-05T06:54:19Z erhoben, also nach dem Lauf und vor jedem
Eingriff.

```
--- 1. memory.events und memory.events.local, jeder Zaehler ---
low             0        high            0        max             0
oom             0        oom_kill        0        oom_group_kill  0
sock_throttled  14865

--- 2. memory.peak, memory.max, memory.current ---
memory.peak     1018101760
memory.max      2147483648
memory.current   430878720

--- 3. memory.stat, die Posten dahinter ---
anon 228569088   file 182521856   kernel 19779584   slab 18295416
anon_thp 0       pgfault 402002127   pgmajfault 6058

--- 4. der Container selbst ---
OOMKilled=false Status=running ExitCode=0 RestartCount=0
StartedAt=2026-09-04T17:46:29Z Memory=2147483648 MemorySwap=2147483648

--- die Abschlusszeile des Samplers ---
findling-rss summary samples=9421 max_anon=442695680 peak=1018101760
  events=[low=0 high=0 max=0 oom=0 oom_kill=0 oom_group_kill=0 sock_throttled=14865]
  oom_killed=false
```

| Teil | Aussage |
|---|---|
| `memory.events` und `memory.events.local` | Der Kernel hat in dieser cgroup nie an die Grenze angeschlagen. Nicht nur `oom_kill` steht auf null, auch `max` und `high`: die Grenze wurde in 46.127 Sekunden **kein einziges Mal** berührt. |
| `docker inspect .State.OOMKilled` | `false`, dazu `RestartCount 0` und `ExitCode 0`: der Container, der gemessen wurde, ist derselbe, der gestartet wurde. |
| höchster `anon` aus der CSV | **442.695.680 Byte, also 422,2 MB**, erreicht am 2026-09-04T18:22:11Z, 36 Minuten nach dem ersten Verdikt. Das ist die Zahl der Store-Aussage. |
| `memory.peak` und der Dateicache | **1.018.101.760 Byte, also 970,9 MB**, erstmals erreicht um 18:27:07Z und danach nie überschritten. Der Abstand von 549 MB ist der Seitencache des Index. Am Ende des Laufs standen `anon 228.569.088`, `file 182.521.856` und `slab 18.295.416` nebeneinander. |

**Der Grenzwert war 2,0 GB, gemessen sind 422,2 MB, das sind 20,6 Prozent. Der
Lauf besteht.** Das ist der Satz, der in die Store-Beschreibung geht, und er ist
auf der Architektur gemessen, für die er gilt.

Zum siebten Zähler, weil ein weggelassener Zähler schlimmer ist als ein
erklärter: `sock_throttled` steht auf dem Kernel dieser Box (7.0.0-1012-aws) neu
in `memory.events` und gehört nicht zu den sechs, die einen Speichertod
anzeigen. Er zählt, wie oft die Zuteilung von Puffern für Netzverbindungen
innerhalb dieser cgroup gebremst wurde; der Container hat in dreizehn Stunden
gut fünfzigtausend Dateien über HTTPS abgeholt. Der Kernel der Generalprobe
(6.8) kennt den Zähler nicht, weshalb er dort in keiner Tabelle steht. Was er
nicht bedeutet, steht daneben: `max` und `high` sind null, es wurde also nie
zurückgefordert, und `failed` ist über den ganzen Lauf null geblieben. Der
Zähler hat den Lauf nichts gekostet, was messbar gewesen wäre.

### Die Kurve

9.622 Messpunkte im Abstand von fünf Sekunden, vom Start des Samplers um
2026-09-04T17:29:42Z bis zu seinem geordneten Ende um 2026-09-05T06:54:14Z.

| Stunde (UTC) | Messpunkte | `anon` Minimum | `anon` Median | `anon` Spitze | `memory.peak` am Ende der Stunde |
|---|---|---|---|---|---|
| 09-04 17 | 346 | 59 MB | 59 MB | 222 MB | 534 MB |
| 09-04 18 | 718 | 147 MB | 226 MB | **422 MB** | 971 MB |
| 09-04 19 | 719 | 155 MB | 287 MB | 415 MB | 971 MB |
| 09-04 20 | 719 | 169 MB | 329 MB | 346 MB | 971 MB |
| 09-04 21 | 719 | 162 MB | 331 MB | 391 MB | 971 MB |
| 09-04 22 | 719 | 199 MB | 333 MB | 392 MB | 971 MB |
| 09-04 23 | 719 | 207 MB | 334 MB | 378 MB | 971 MB |
| 09-05 00 | 718 | 207 MB | 333 MB | 394 MB | 971 MB |
| 09-05 01 | 719 | 191 MB | 335 MB | 394 MB | 971 MB |
| 09-05 02 | 719 | 209 MB | 335 MB | 394 MB | 971 MB |
| 09-05 03 | 719 | 210 MB | 336 MB | 395 MB | 971 MB |
| 09-05 04 | 719 | 155 MB | 336 MB | 395 MB | 971 MB |
| 09-05 05 | 719 | 164 MB | 336 MB | 397 MB | 971 MB |
| 09-05 06 | 650 | 174 MB | 322 MB | 356 MB | 971 MB |

Dieselben drei Beobachtungen wie auf x86, und dass sie sich auf einer anderen
Architektur wiederholen, ist der eigentliche Wert dieser Tabelle.

Erstens: **die Spitze fällt in die erste Stunde und wird danach nie wieder
erreicht.** Sie liegt um 18:22Z, dort wo die Textspur unter Volllast lief und
der Schreibpuffer seine ersten großen Vereinigungsläufe fuhr. Die elf Stunden
reiner OCR-Arbeit danach kosten weniger Speicher, nicht mehr.

Zweitens: **die Kurve steigt nicht.** Der Median liegt ab der dritten Stunde
zwischen 322 und 336 MB und bewegt sich über neun Stunden um vierzehn Megabyte,
während der Index von null auf 726 MB und der Bestand von null auf 50.021
Dokumente wächst. Ein Speicherleck über dreizehn Stunden hätte hier eine
Steigung, und es gibt keine.

Drittens: **`memory.peak` steht ab der zweiten Stunde still**, bei 971 MB,
obwohl er den Dateicache mitzählt. Der Kernel hält den Cache dieser cgroup von
selbst weit unter der Grenze, ohne dazu räumen zu müssen: `low` und `high` in
`memory.events` stehen auf null.

### Die beiden Spuren, getrennt gemessen

Die Trennung ist nicht gerechnet, sondern abgelesen: von 19:40:38Z an trägt jede
weitere indexierte Datei das Kennzeichen `ocr_used`, die Textspur war zu diesem
Zeitpunkt leer.

| Abschnitt | Zeitraum | Dauer | Verdikte | je Verdikt |
|---|---|---|---|---|
| Textspur und Crawl | 17:46:36Z bis 19:40:38Z | 6.842 s | 40.524, davon 39.904 über die Textspur und 620 über die OCR-Spur | 0,169 s |
| reine OCR-Spur | 19:40:38Z bis 06:35:23Z | 39.285 s | 9.525, davon 9.505 über die OCR-Spur | **4,133 s je OCR-Datei** |

Die 20 Verdikte des zweiten Abschnitts, die nicht aus der OCR-Spur stammen, sind
die `too_large`-Dateien: der Abgleich um 06:31Z hat sie noch einmal
vorgelegt, und sie sind noch einmal an ihrer Größe abgewiesen worden, ohne dass
ein Byte von ihnen gelesen wurde. Sie kosten also nichts, was in dieser Tabelle
sichtbar wäre.

Der zweite Wert ist die einzige Zahl dieses Laufs, die man ohne Rechnung mit der
Generalprobe vergleichen kann, und der Vergleich ist unangenehm ehrlich:

| Posten | Generalprobe cpx22 (x86) | ARM m7g.large (arm64) | Verhältnis |
|---|---|---|---|
| je Datei der OCR-Spur | 3,16 s | 4,13 s | ARM braucht 31 Prozent länger |
| Laufzeit des ganzen Laufs | 10 h 14 min | 12 h 49 min | ARM braucht 25 Prozent länger |
| höchster `anon` | 428,6 MB | 422,2 MB | ARM braucht 1,5 Prozent weniger |

**Die Zielhardware ist langsamer und nicht hungriger.** Für einen Bericht, der
eine Speicheraussage tragen soll, ist das genau die richtige Richtung: die Zahl,
die in die Store-Beschreibung geht, wird auf der schwächeren Maschine nicht
größer. Die Laufzeit dagegen wird es, und der Anteil daran, der auf die
Architektur entfällt, lässt sich hier nicht von dem trennen, der auf den
gedrosselten Netzspeicher entfällt. Der Bericht sagt deshalb nicht "ARM ist 31
Prozent langsamer", sondern: **diese Maschine hat für diesen Korpus 12 h 49 min
gebraucht.**

Eine Kernzahl steht in dieser Tabelle bewusst nicht, und der Grund ist ein
Widerspruch in diesem Repository, den dieser Lauf gefunden hat. Die Tabelle der
beiden Maschinen weiter oben führt für die cpx22 zwei Kerne, ebenso die READMEs
der Grundlast- und der Trockenlauf-Messung; die README der Volllauf-Messung
führt drei. Ein `nproc` von dieser Maschine ist nirgends aufgeschrieben, und die
Maschine ist gelöscht, also lässt sich der Widerspruch nicht mehr durch eine
Messung entscheiden. Solange das so ist, trägt keine Aussage dieses Berichts
eine Kernzahl der Generalprobe. Notiert als DI-05-39.

### Die eine Warnung aus dreizehn Stunden, und was sie gekostet hat

```
2026-09-05T06:05:42Z WARNING:findling.nc.queue:could not acknowledge a batch of 2 rows
```

Der Container hatte zwei Dokumente in den Index geschrieben und kam beim
Quittieren nicht durch. Der Weg dieser beiden Zeilen danach steht vollständig in
der Zustandsdatenbank: die Sperre lief nach dreißig Minuten ab, die Nextcloud-
Hälfte gab sie erneut aus, und der Container hat sie um 06:34:41Z ein zweites
Mal beurteilt, mit `attempts = 3`.

| Auslieferungen | Dateien | was das ist |
|---|---|---|
| 1 | 39.924 | die Textspur: einmal abgeholt, einmal beurteilt |
| 2 | 10.123 | die OCR-Spur: die Übergabe von der Inhalts- an die OCR-Spur ist die zweite Auslieferung derselben Zeile |
| 3 | **2** | die beiden Zeilen aus der verlorenen Quittung |

Was daraus **nicht** geworden ist: ein Fehlschlag, ein Verlust, ein doppelter
Eintrag. `failed` steht auf null, die 50.021 ACL-Zeilen sind genau so viele wie
die Dokumente im Index, und der Deckel von drei Auslieferungen wurde von genau
zwei Zeilen erreicht und von keiner überschritten. Das ist die Zusage "mindestens
einmal ausliefern, höchstens einmal indexieren", unter Last und ungeplant
geprüft.

### Die Statusseite über den ganzen Lauf, und die Korrektur aus 05-20

Hier ist der schwerste Befund der Generalprobe zu prüfen: dort behauptete die
Verwaltungsseite acht Stunden lang Stillstand, während der Container 6.500
Dokumente schrieb. Über die 161 Aufnahmen dieses Laufs:

| Zustand | Aufnahmen |
|---|---|
| `running` | 156 |
| `idle` | 4, davon 3 nach dem letzten Verdikt |
| **`stalled`** | **0** |
| ohne Antwort | 1, die erste, vor dem Einschalten der App |

Der höchste `stalledFor`-Wert während der Arbeit beträgt **87 Sekunden**. Die
Zahl, die ihn tragen könnte, steht daneben: der letzte Hintergrundauftrag dieser
App lief um 2026-09-04T19:42:26Z, in der letzten arbeitenden Aufnahme war er
39.160 Sekunden alt, also **10 Stunden und 53 Minuten**. Genau diese knapp elf
Stunden hätte die Seite vor 05-20 als Stillstand ausgewiesen, und sie hat es
nicht getan, weil der gewachsene `indexed`-Zähler des Containers jetzt als
Bewegung zählt.

**Der Befund aus 05-14 ist damit im Feld erledigt, auf demselben Korpus und
einem noch längeren OCR-Nachlauf als dem, der ihn erzeugt hat.** Wo die Regel
ihre Grenze hat, steht bei Drill 1b, und diese Grenze ist gewollt.

Fünf Aufnahmen aus derselben Reihe, damit die Auswahl nicht nur aus Höhepunkten
besteht:

| Zeitpunkt | Zustand | eingereiht | laufend | Dokumente | Deckungsgrad |
|---|---|---|---|---|---|
| 2026-09-04T17:38:53Z | `running` | 2.048 | 0 | 0 | noch keiner |
| 2026-09-04T19:19:03Z | `running` | 8.705 | 32 | 33.288 | vorläufig |
| 2026-09-04T22:39:23Z | `running` | 6.905 | 2 | 43.114 | endgültig |
| 2026-09-05T03:39:50Z | `running` | 2.531 | 2 | 47.488 | endgültig |
| 2026-09-05T06:50:07Z | `idle` | 0 | 0 | 50.021 | 99 Prozent |

Über alle Aufnahmen hinweg gilt außerdem: `failed` durchgehend null,
`backendReachable` durchgehend wahr, `lowDisk` durchgehend falsch, der
Versionsgleichstand durchgehend `match`, die Dokumentzahl monoton wachsend, und
die ACL-Zeilen in jeder einzelnen Aufnahme genau so viele wie die Dokumente.

Der Deckungsgrad steht am Ende auf 99 Prozent, und die Rechnung dahinter ist
dieselbe wie auf x86: der Nenner ist 50.029 statt 50.049, weil die 20 Dateien
über dem Größendeckel ausdrücklich herausgenommen sind, während die acht
übrigen Übersprungenen drin bleiben. 50.021 von 50.029 sind 99,98 Prozent, und
die Kachel rundet ab.

## Die Störfall-Drills

Drei Störfälle, auf derselben Maschine, mit demselben Index von 50.068 Dokumenten
hinter sich, jeder mit Ausgangszustand, Eingriff, Beobachtung, Wiederherstellung
und mit dem Satz, den er ausdrücklich **nicht** beweist. Der Unterschied zu den
gleichnamigen Aufträgen in CI ist der Gegenstand: dort ein leerer Index und ein
Korpus von 33 Dateien, hier 20 GB und eine Maschine, die seit zwölf Stunden
arbeitet.

Für den Kill-Drill und den Platten-Drill wird Arbeit gebraucht, die im Augenblick
des Eingriffs läuft. Der Volllauf war zu diesem Zeitpunkt fertig, also entstand
ein eigener, kurzer Vorrat: 300 der einseitigen Scans des Korpus, kopiert und über
WebDAV als der Nutzer `lasttest` hochgeladen, also auf demselben Weg, auf dem ein
Mensch Dateien in seine Nextcloud legt. Sie laufen sämtlich über die OCR-Spur,
womit der Eingriff sicher in die OCR-Arbeit fällt und nicht daneben.

### Drill 1: `docker kill` mitten im OCR-Lauf

**Ausgangszustand, 2026-09-04T10:12:43Z.** Der Container arbeitet den Vorrat ab.

```
files gesamt     50.260      (50.104 aus dem Volllauf plus 156 neue Zeilen)
indexed          50.090
acl              50.090
Warteschlange       146      davon 13 an den Arbeiter übergeben
```

**Eingriff, 2026-09-04T10:12:44Z.**

```
docker kill nc_app_findling_backend
Status=exited ExitCode=137 OOMKilled=false FinishedAt=2026-09-04T10:12:44.890Z
```

**Beobachtung 1: der naheliegende Handgriff hilft nicht.** Was ein Verwalter als
erstes tut, ist `docker start`, und das Ergebnis sieht aus wie ein Erfolg: der
Container läuft, sein Protokoll meldet den vollständigen Start, die Wortliste wird
geladen, uvicorn horcht. Die Warteschlange bewegt sich trotzdem nicht. Über eine
Minute blieb `indexed` auf 50.090 stehen, während der Vorrat von 191 auf 235 Zeilen
wuchs, weil die Uploads weiterliefen.

Die Ursache liegt nicht dort, wo Plan 05-12 sie vermutet hat. Das Protokoll meldet
zwar `HP_SHARED_KEY is not set, no HaRP tunnel is opened`, aber dieser Satz steht
auch nach einer geglückten Neuregistrierung im Protokoll, und die Suche
funktioniert in beiden Fällen. Der Unterschied ist ein anderer:
`findling.main.enabled_handler` bewaffnet Poller und Vergleichslauf, und dieser
Handler wird von AppAPI über `PUT /enabled` gerufen, also bei der Registrierung.
Ein `docker start` ruft ihn nicht. **Der Container bedient danach jede Anfrage von
außen und arbeitet von sich aus nichts ab.** Das ist die richtige Bauart, denn ein
abgeschaltetes Backend, das weiter Arbeit einsammelt, ist der Klassiker aus der
Integrationsliste; auf einer Box wird daraus aber ein Container, der gesund
aussieht und stillsteht.

**Wiederherstellung.** Der Weg ist die Neuregistrierung ohne `--rm-data`:

```
occ app_api:app:unregister findling_backend        # ohne --rm-data
docker volume ls --filter name=findling_backend    # nc_app_findling_backend_data, unangetastet
occ app_api:app:register findling_backend harp_aio --info-xml /tmp/info-fix.xml --wait-finish
docker update --memory=2g --memory-swap=2g nc_app_findling_backend
```

| Größe | Wert |
|---|---|
| Dauer der Neuregistrierung | 5 s |
| erstes neues Dokument danach | nach weiteren 6 s, um 10:15:10Z |
| **Zeit bis zur Wiederaufnahme auf dem richtigen Weg** | **11 s** |
| Zeit bis zur Wiederaufnahme mit dem Umweg über `docker start` | 146 s |
| Datenspeicher | erhalten, der Index der 50.090 Dokumente steht unverändert |
| harte Grenze nach der Neuregistrierung | wieder gesetzt, `Memory=2147483648` |

**Beobachtung 2: was der Abschuss gekostet hat.** Endabrechnung um
2026-09-04T10:45:08Z, nachdem die Warteschlange leer war:

| Prüfung | Ergebnis |
|---|---|
| Zeilen insgesamt | 50.404, also genau 50.104 plus die 300 des Vorrats |
| doppelte `file_id` | 0 |
| doppelte Pfade unter `drill/` | 0 |
| ACL-Zeilen gegen Dokumente | 50.366 gegen 50.366, gleich |
| vom Vorrat indexiert | 298 von 300 |
| **nicht fertig geworden** | **2 von 300** |

Der Index hat den Abschuss also ohne Verlust und ohne Doppelung überstanden, und
zwei Dateien haben ihn nicht überstanden. Beide Fälle gehören in den Bericht, weil
sie verschiedene Dinge über die Zustandsmarke sagen.

Der erste Fall heilt von selbst. Zwei Zeilen waren in der Sekunde des Abschusses
als OCR-Auftrag gesperrt, mit dem Zeichen des toten Containers. Die Sperre eines
OCR-Auftrags gilt 1800 Sekunden (`QueueMapper::LOCK_TIMEOUTS`, mit der Begründung,
dass zwei OCR-Läufe unter der Deckelkaskade bis zu 1200 s dauern dürfen). Um
10:42:43Z lief sie ab, der Container holte beide Zeilen, und um 10:44:42Z waren
sie indexiert, mit `attempts 2` und `ocr_used 1`. **Die Fortsetzung an der
Zustandsmarke ist damit auf echter Hardware belegt**, mit einer halben Stunde
Verzögerung, die keine Störung ist, sondern der Preis dafür, dass eine lange
laufende OCR-Arbeit nicht fälschlich für tot erklärt wird.

Der zweite Fall heilt nicht von selbst, und er gehört, wie sich später
herausstellte, gar nicht diesem Drill. Zwei Dateien, `drill/d037.pdf` und
`drill/d038.pdf`, stehen auf `skipped(no_text_layer)` mit `attempts 1` und
`ocr_used 0`, und die Nextcloud-Seite führt sie als `failed(repeatedly_stuck)`.
Der erste Verdacht fiel auf den Abschuss, weil er zeitlich davorlag. Die
Nachmessung in Drill 3 hat ihn entlastet: dort entstanden **30 solcher
Abschreibungen ohne jeden Abschuss**, und ihre Zahl war beide Male genau die Zahl
der Zeilen, die im Augenblick der Plattenpause unterwegs waren. Der Hergang und
seine Folgen stehen deshalb unten bei Drill 3, wo sie hingehören.

Für diesen Drill bleibt damit die schlichtere Bilanz: **der Abschuss selbst hat
keine einzige Datei gekostet.** Seine 13 unterwegs befindlichen Zeilen kamen
entweder über die gewöhnliche Wiederholung zurück oder, im Fall der beiden
OCR-Aufträge, nach dem Ablauf ihrer Sperre.

**Was dieser Drill nicht beweist.** Er sagt nichts über einen Abschuss **während
eines Schreibvorgangs im Index**. Getroffen wurde die Verarbeitungskette, nicht
ein laufender Commit des Schreibpuffers; ob ein Abschuss zwischen zwei Segmenten
eines Vereinigungslaufs ebenso ausgeht, steht hier nicht. Er sagt außerdem nichts
über einen Abschuss während des nächtlichen Vergleichslaufs, der eine eigene
Zustandsmarke führt.

### Drill 2: das Backend ist weg

**Ausgangszustand, 2026-09-04T10:45:44Z.** Eine Suche des Nutzers `lasttest` nach
`Zahlungseingang` liefert über OCS HTTP 200 mit fünf Treffern, jeder mit
Textausschnitt aus dem Dateiinhalt.

**Eingriff, 2026-09-04T10:45:46Z.** `docker stop nc_app_findling_backend`, der
Container endet geordnet mit `ExitCode 0`.

**Beobachtung.** Dieselbe Suche, dreimal in derselben angemeldeten Sitzung:

| Versuch | Antwort | Treffer | Dauer |
|---|---|---|---|
| 1 | HTTP 200 | 0 | 1560 ms |
| 2 | HTTP 200 | 0 | 1605 ms |
| 3 | HTTP 200 | 0 | 1612 ms |
| Gegenprobe: die native Dateisuche derselben Sitzung | HTTP 200 | 5 | 113 ms |

Kein Fehler, keine hängende Suche, keine leere Seite: der Anbieter meldet sich mit
seinem Namen "File contents" und null Treffern zurück, und die übrigen Anbieter
der Unified Search arbeiten unbeeinflusst weiter. Die 1,6 Sekunden sind das harte
Zeitlimit, das die Begleit-App dem Aufruf mitgibt; sie sind der Preis dieser
Degradierung und werden bei jeder Suche fällig, solange das Backend fehlt.

Die Verwaltungsseite nennt den Zustand, und zwar genau einen. Von den fünf Bannern
der Seite trägt nach dem Stopp nur eines kein `hidden`:

```
findling-banner-unreachable        SICHTBAR
findling-banner-lockstep           verborgen
findling-banner-stale              verborgen
findling-banner-lowdisk            verborgen
findling-banner-reindex            verborgen
```

Der Text lautet "The Findling backend does not answer. The numbers below are the
last ones this app recorded." `backendReachable` steht auf falsch, und die Seite
zeigt weiter die zuletzt festgehaltenen Zahlen, statt Nullen zu behaupten.

**Wiederherstellung, und der Unterschied zwischen Lesen und Schreiben.** Ein
`docker start` genügt für die Suche: 22 Sekunden später liefert dieselbe Anfrage
wieder fünf Treffer in 442 ms, ohne jeden weiteren Eingriff. Für die Indexierung
genügt er nicht, und das wurde eigens nachgeprüft, weil der Befund dem ersten
Drill widerspricht, wenn man ihn nicht trennt: eine einzelne neu hochgeladene
Datei blieb nach dem `docker start` drei Minuten lang unangetastet in der
Warteschlange liegen, und das Protokoll zeigt in dieser Zeit `/status`, `/search`
und `/snippets` mit 200, aber keinen einzigen Durchgang des Pollers. Nach der
Neuregistrierung war dieselbe Zeile in 20 Sekunden abgearbeitet.

| Weg zurück | Suche | Indexierung |
|---|---|---|
| `docker start` | wieder da nach 22 s | bleibt aus |
| Neuregistrierung ohne `--rm-data` | wieder da | wieder da nach 20 s |

**Was dieser Drill nicht beweist.** Er sagt nichts über ein Backend, das
**langsam** ist statt stumm. Ein gestoppter Container antwortet sofort mit einem
Verbindungsfehler, ein überlasteter lässt das Zeitlimit von zwei Sekunden
auslaufen, und nur der zweite Fall verlangsamt die Unified Search wirklich; dieser
Zweig ist in CI abgedeckt ("Backend hängt") und hier nicht. Er sagt außerdem
nichts über die Suche eines Nutzers, der noch nie gesucht hat, während das Backend
fehlt: die Begleit-App merkt sich die Version des Containers aus dem letzten
Statusabruf, und diese Gedächtnisstelle wurde hier nicht geleert.

### Drill 3: die Platte wird knapp

**Ausgangszustand, 2026-09-04T10:15:40Z.** Der Container arbeitet den Rest des
Vorrats ab, 21.797.539.840 Byte sind frei, `indexed` steht auf 50.102.

**Eingriff.** Der Schwellwert des Containers ist `MIN_FREE_BYTES = 524.288.000`,
also 500 MB. Verknappt wird mit einer einzigen großen Datei außerhalb der App:

```sh
fallocate -l 21378109440 /mnt/HC_Volume_106785477/BALLAST
```

Das Ziel sind bewusst rund 400 MB Rest und nicht null. Der Schwellwert der App
wird damit sicher unterschritten, die Platte selbst läuft aber nie voll, und die
PostgreSQL-Datenbank derselben Instanz, die auf demselben Dateisystem liegt,
gerät in keinem Augenblick in Gefahr. Eine Probe, die nebenbei die Datenbank der
Messmaschine beschädigt, misst am Ende etwas anderes als sie sollte.

**Beobachtung, innerhalb von 90 Sekunden.** Das Protokoll des Containers:

```
WARNING:findling.index.writer:index commit paused, free space is below the
        configured floor of 524288000 byte
WARNING:findling.worker.poller:index paused, free space below the floor,
        2 rows handed back
```

| Prüfung | Ergebnis |
|---|---|
| `lowDisk` in `/status` | wahr |
| `diskFreeBytes` | 419.762.176 |
| `spaceWarning` der Vorabschätzung | wahr |
| `indexed` über 60 Sekunden | 50.102, unverändert |
| Warteschlange | wächst wieder, die belegten Zeilen werden zurückgegeben |
| Banner `findling-banner-lowdisk` | ohne `hidden`, also sichtbar |
| Text des Banners | "Little disk space left. Indexing is paused so the index stays intact. Search keeps working." |
| abgebrochene oder fehlgeschlagene Dateien | keine |

Der Unterschied, auf den es ankommt: die Zeilen werden **zurückgegeben** und nicht
als Fehlschlag beurteilt. Die Indexierung pausiert, sie bricht nicht ab, und im
Protokoll steht der Grund im Klartext samt der Zahl, gegen die geprüft wurde.

**Wiederherstellung, 2026-09-04T10:19:06Z.** Der Ballast wird gelöscht.

| Größe | Wert |
|---|---|
| Dauer der Pause | rund 3 Minuten 25 Sekunden |
| bis der Lauf weiterläuft | 42 s nach dem Freigeben, ohne jeden Eingriff |
| `indexed` danach | 50.104, der Lauf setzt fort, wo er stand |
| `lowDisk` danach | falsch, `diskFreeBytes` wieder 21.797.584.896 |
| Verlust | keiner, keine Datei doppelt |

### Drill 3, Nachtrag: die Suche während der Pause, und was die Pause wirklich kostet

Der erste Durchgang liess eine Zusage offen. Das Banner sagt "Indexing is paused so
the index stays intact. Search keeps working", und während der Pause war nicht
gesucht worden. Also ein zweiter Durchgang, mit demselben Eingriff und einem
grösseren Vorrat: 60 frische Kopien einseitiger Scans, über WebDAV hochgeladen,
30 davon im Augenblick der Verknappung beim Arbeiter.

**Die erste Hälfte der Zusage stimmt.** Während `lowDisk` wahr war, die
Indexierung pausierte und 420.040.704 Byte frei waren:

| Suchbegriff | Antwort | Treffer | Dauer |
|---|---|---|---|
| `Zahlungseingang` | HTTP 200 | 5 | 114 ms |
| `Bauleitplanung` | HTTP 200 | 5 | 136 ms |
| `Instandhaltung` | HTTP 200 | 5 | 149 ms |

Jeder Treffer mit Titel und Textausschnitt, in der gewohnten Zeit, gegen einen
Index von 50.366 Dokumenten. Die Suche liest den Index über eine
Speicherabbildung und braucht dafür keinen freien Platz; die Zusage ist damit
belegt und nicht mehr nur plausibel.

**Die zweite Hälfte stimmt nicht.** "The index stays intact" ist wahr, aber es ist
nicht die ganze Rechnung. Nach der Pause fehlten von den 60 Dateien 30:

| Von 60 hochgeladenen Dateien | Anzahl |
|---|---|
| indexiert | 30 |
| als `failed(repeatedly_stuck)` abgeschrieben, nie an den Container übergeben | 28 |
| als `failed(repeatedly_stuck)` abgeschrieben, im Container auf `no_text_layer` stehengeblieben | 2 |

Die Zahl 30 ist keine zufällige. Sie ist genau die Zahl der Zeilen, die beim
Beginn der Pause an den Arbeiter übergeben waren, und im ersten Durchgang dieses
Drills waren es genau 2 von 2. Der Mechanismus steht im Quelltext beider Hälften
und ist nachlesbar:

1. `QueueMapper` zählt die Wiederholungen **bei der Ausgabe** hoch, mit dem
   Kommentar "Handing a row out is the attempt, so retries is counted here".
2. Der Container gibt bei knapper Platte die ganze Ladung zurück, ohne sie zu
   beurteilen: "index paused, free space below the floor, 30 rows handed back".
3. Der nächste Durchgang des Pollers holt dieselben Zeilen wieder, zählt wieder
   hoch, und gibt sie wieder zurück. Ein Durchgang dauert wenige Sekunden.
4. `QueueService::MAX_DELIVERIES` steht auf 3. Nach vier Ausgaben, also nach
   **rund zwanzig Sekunden Plattenknappheit**, schreibt die Nextcloud-Seite die
   Zeile als `failed(repeatedly_stuck)` ab und gibt sie nicht mehr aus.

Die Pause verbraucht also das Wiederholungsbudget genau der Dateien, die sie
schützen soll. Drei Zurückgaben im Protokoll haben gereicht; die Pause dauerte
hundert Sekunden, und die Abschreibung war nach einem Fünftel davon vollzogen.

Was das für einen Betreiber heisst, ist unangenehm konkret: **eine volle Platte,
die eine halbe Minute besteht, kostet den gesamten Arbeitsvorrat, der in diesem
Moment unterwegs ist**, und die Oberfläche sagt in derselben Minute, es sei nur
pausiert. Die Dateien sind nicht unbemerkt weg, sie stehen namentlich in der
Fehlerliste, und `occ findling:index --restart` fängt sie wieder ein. Aber der
nächtliche Vergleich holt sie ausdrücklich nicht zurück, denn `repeatedly_stuck`
ist genau das Verdikt, mit dem eine aufgegebene Datei vom Vergleich ausgenommen
wird.

Notiert als DI-05-23, nicht behoben. Die Abhilfe ist keine Zeile: eine Rückgabe
wegen Plattenknappheit ist kein Fehlversuch der Datei, sie müsste also entweder
die Wiederholung nicht belasten oder den Vorrat gar nicht erst ausgeben, solange
die Platte knapp ist. Beides ändert die Bedeutung von `retries`, beides berührt
beide Hälften, und die zweite Variante berührt zusätzlich die Frage, woran der
Poller vor dem Holen erkennt, dass er nicht schreiben kann.

**Was dieser Drill nicht beweist.** Er sagt nichts über eine Platte, die
**zwischen zwei Schreibvorgängen** eines einzelnen Commits voll wird: geprüft wird
der freie Platz vor dem Commit, und der Fall, in dem er währenddessen ausgeht,
liegt hinter dieser Prüfung. Er sagt außerdem nichts über einen Datenträger, der
tatsächlich auf null läuft, denn hier blieben beide Male rund 400 MB übrig, damit
die Datenbank derselben Instanz nicht in Mitleidenschaft gezogen wird.

## Dieselben Drills auf ARM, und die Prüfung der drei Korrekturen

Am 2026-09-05, unmittelbar nach dem ARM-Volllauf, auf derselben Maschine und mit
demselben Index von rund 51.400 Dokumenten dahinter. Der Vorrat für die Eingriffe
kam auf demselben Weg wie auf x86: 1.500 Dateien mit dem Seed
`phase5-drill-arm`, über WebDAV als der Nutzer `lasttest` hochgeladen, alle 1.500
mit HTTP 201 angenommen. Davon sind 297 einseitige Scans, die über die OCR-Spur
laufen, womit jeder Eingriff sicher in die OCR-Arbeit fällt.

Der Zweck dieser Wiederholung ist nicht die Wiederholung. Zwischen den x86-Drills
und diesen liegt Plan 05-20, und jeder der drei Drills prüft eine seiner drei
Korrekturen an der Stelle, an der sie entstanden ist.

### Drill 1 auf ARM: `docker kill` mitten in der OCR-Arbeit

**Ausgangszustand, 2026-09-05T08:16:22Z.** 160 Zeilen im Vorrat, davon 2 an den
Arbeiter übergeben, 51.401 Dokumente im Index, `RestartPolicy` des Containers
`unless-stopped`.

**Eingriff.**

```
docker kill nc_app_findling_backend
Status=exited ExitCode=137 OOMKilled=false FinishedAt=2026-09-05T08:16:22.909Z
```

**Der Vorrat unmittelbar danach:** 160 Zeilen, 2 ausgeliefert, höchste
Auslieferungszahl 1. Der harte Abschuss hat nichts abgeschrieben und nichts
verloren.

**Wiederherstellung, Versuch 1: `docker start`.** Das ist der naheliegende Griff,
und er tut nicht, was er zu tun scheint:

```
Status=running Memory=2147483648 RestartCount=0
INFO:findling:findling backend starting, binding mode: tcp 0.0.0.0:23000
INFO:findling.index.wordlist:constituent list read from the volume, 276496 entries
INFO:     Application startup complete.
```

Der Container läuft, seine harte Grenze steht noch, und er beantwortet Suchen:
HTTP 200, fünf Treffer, 759 ms. Der `indexed`-Zähler blieb in 122 Sekunden
Beobachtung auf 51.401 stehen, und das Protokoll zeigt in dieser Zeit keinen
einzigen Durchgang des Pollers. **Das ist DI-05-36, hier zum ersten Mal
absichtlich ausgelöst und gemessen.**

**Wiederherstellung, Versuch 2: der Weg über AppAPI.**

```
occ app_api:app:disable findling_backend
occ app_api:app:enable  findling_backend
```

Drei Sekunden für beide Befehle, die erste neue Datei zehn Sekunden später,
`Memory` weiterhin 2.147.483.648. Die Statusseite meldet unmittelbar danach
`runState running`, `backendReachable true`, 154 wartende und 4 laufende Zeilen.

### Drill 1b auf ARM: die ganze Maschine startet neu

Diesen Drill gab es auf x86 nicht, und er ist der wichtigste der vier, weil er
den Produktivfall von DI-05-36 misst. Ein `docker kill` von Hand macht jemand,
der weiß, was er tut. Ein Neustart der Maschine passiert bei jedem
Kernel-Update, und danach startet Docker den Container nach seiner Regel
`unless-stopped` von selbst wieder.

**Eingriff, 2026-09-05T08:20:48Z:** `systemctl reboot`.

**Nach dem Neustart, 08:22:14Z:** alle neun Container sind zurück, der
Findling-Container trägt dieselbe Kennung wie vorher, `RestartCount 0`, und
`Memory=2147483648 MemorySwap=2147483648`. **Die harte Grenze überlebt einen
Neustart der Maschine**, weil sie in der HostConfig des Containers steht und
nicht im laufenden Prozess. Das ist eine Zusage mehr, als der Bericht bisher
machen konnte.

**Die Beobachtung, und ein Messfehler auf dem Weg dorthin.** Der erste Durchgang
dieses Drills hat "der Poller arbeitet wieder, von selbst" gemeldet, und das war
falsch. Der Vergleichswert stammte aus einer Aufnahme rund dreißig Sekunden vor
dem Herunterfahren, und in diesen dreißig Sekunden hatte der Container noch zwei
Dateien fertig gemacht. Der Zähler stand danach von selbst höher, ohne dass nach
dem Neustart irgendetwas geschehen wäre. Der Fehler steht hier, weil er lehrreich
ist: **ein Zustand, der zum falschen Zeitpunkt abgelesen wurde, sieht aus wie
eine Bewegung.** Gemessen wurde deshalb neu, an einer Größe, die diesen Fehler
nicht machen kann, nämlich an der Zahl der Durchgänge des Pollers im Protokoll,
gezählt ab dem Start des Containers.

```
Container gestartet 2026-09-05T08:21:14Z
Durchgaenge des Pollers seit dem Start: 0        (nach 5 min)
T+ 60s  Durchgaenge 0  indexed 51433  Vorrat 130
T+120s  Durchgaenge 0  indexed 51433  Vorrat 130
T+181s  Durchgaenge 0  indexed 51433  Vorrat 130
T+241s  Durchgaenge 0  indexed 51433  Vorrat 130
T+301s  Durchgaenge 0  indexed 51433  Vorrat 130
```

**Zehn Minuten, kein einziger Durchgang, 130 Zeilen Vorrat, und der Container
beantwortet in derselben Zeit Suchen mit fünf Treffern.** DI-05-36 trifft also
auch den Neustart der Maschine, und dort trifft er härter als beim `docker
start`: es hat niemand etwas falsch gemacht, es hat nur niemand etwas getan.

**Und die Verwaltungsseite sagt es nicht.** In genau dieser Lage meldet sie:

```
runState running   stalledFor 0   backendReachable True
scheduled 126      running 4      failed 0
```

Das ist die Grenze der Korrektur aus 05-20, und sie ist gewollt. Das
Stillstands-Urteil nimmt die **spätere** von zwei Bewegungen, damit ein langer
OCR-Nachlauf nicht als Stillstand gilt; solange die Hintergrundaufträge von
Nextcloud laufen, ist eine der beiden Bewegungen immer frisch. Die Regel kann
"beide Hälften stehen" erkennen und "nur die Container-Hälfte steht" nicht.
Beides zugleich geht mit dieser einen Zahl nicht, und der Bericht sagt lieber,
wo die Kachel blind ist, als so zu tun, als sei sie es nicht. Notiert als
DI-05-38, der Anzeige-Hälfte von DI-05-36: wer den einen behebt, macht den
anderen fast gegenstandslos, und wer ihn nicht behebt, braucht den anderen
dringend.

**Wiederherstellung.** `occ app_api:app:disable` und `enable`, drei Sekunden,
erste neue Datei nach zehn Sekunden, `Memory` unverändert.

**Was der Neustart nebenbei geprüft hat.** Unmittelbar vor dem Herunterfahren
steht im Protokoll `could not acknowledge a batch of 2 rows`: das geordnete
Herunterfahren hat die Quittung nicht mehr durchgebracht. Danach ist die höchste
Auslieferungszahl im Vorrat weiterhin 1, und abgeschrieben wurde nichts. Genau
dafür ist die Rückgabe aus 05-20 gebaut.

### Drill 2 auf ARM: das Backend ist weg

**Ausgangszustand, 2026-09-05T08:32:15Z.** Suche mit Backend: HTTP 200, fünf
Treffer, 426 ms.

**Eingriff:** `docker stop`, `Status=exited ExitCode=0`.

**Die Suche ohne Backend, dreimal:**

```
Versuch 1: HTTP 200, Treffer 0, 1833 ms, name='File contents'
Versuch 2: HTTP 200, Treffer 0, 1821 ms
Versuch 3: HTTP 200, Treffer 0, 1817 ms
```

Keine Fehlerseite, kein Abbruch, kein Zeitüberschreitungsfehler beim Nutzer: der
Anbieter meldet sich mit null Treffern. Die Dateisuche von Nextcloud in derselben
Sitzung antwortet weiter mit HTTP 200 in 418 ms, die Instanz ist also heil.

**Die Verwaltungsseite ohne Backend:**

```
backendReachable False   indexedDisplay 51433   backend.indexed 0   note ''
findling-banner-unreachable        SICHTBAR
findling-banner-lockstep           verborgen
findling-banner-stale              verborgen
findling-banner-lowdisk            verborgen
findling-banner-reindex            verborgen
Satz 'The Findling backend does not answer' in der Seite: True
```

Genau ein Banner, und es ist das richtige. Die Seite zeigt den zuletzt bekannten
Bestand von 51.433 Dokumenten weiter an und erfindet keine Zahl.

**Wiederherstellung** über AppAPI, 29 Sekunden (der Container muss dafür erst
gestartet werden), Suche danach wieder 436 ms mit fünf Treffern, Vorrat läuft
weiter.

### Drill 3 auf ARM: die Platte wird knapp, und die Prüfung der Rückgabe

Dies ist der Drill, für den Plan 05-20 geschrieben wurde. Auf x86 endeten hier 32
Zeilen als `failed(repeatedly_stuck)`, ohne dass sie je jemand bearbeitet hatte:
jede Rückgabe zählte als Fehlversuch, und nach drei Rückgaben war die Zeile
abgeschrieben. Seit 05-20 gibt `QueueMapper::unlock` die Auslieferung mit der
Zeile zusammen zurück.

Die Probe ist deshalb absichtlich streng: die Pause wird **fünf Minuten**
gehalten. Bei einem Durchgang alle fünf Sekunden wäre ein Budget von drei
Auslieferungen nach fünfzehn Sekunden verbraucht, also zwanzigfach.

**Ausgangszustand, 2026-09-05T08:34:05Z.** 31.087.046.656 Byte frei, 112 Zeilen
im Vorrat, 6 Auslieferungen über alle Zeilen, höchste 1, nichts abgeschrieben.

**Verknappung:** `fallocate` über 30.687.308.800 Byte, danach 382 MB frei, also
unter dem Boden von 524.288.000 Byte.

**Was der Container tut:**

```
WARNING:findling.index.writer:index commit paused, free space is below the
        configured floor of 524288000 byte
WARNING:findling.worker.poller:index paused, free space below the floor,
        2 rows handed back
```

Zehn solche Paare in fünf Minuten. Und die Zahl, um die es geht:

| Zeitpunkt | Vorrat | Auslieferungen gesamt | höchste | abgeschrieben |
|---|---|---|---|---|
| vor der Verknappung | 112 | 6 | 1 | keine |
| T+60 s | 110 | 4 | 1 | keine |
| T+120 s | 110 | 4 | 1 | keine |
| T+180 s | 110 | 4 | 1 | keine |
| T+240 s | 110 | 4 | 1 | keine |
| T+300 s | 110 | 4 | 1 | keine |
| nach der Wiederherstellung | 108 | 6 | 1 | **keine** |

**Zehn Rückgaben, und die höchste Auslieferungszahl steht unverändert auf eins.**
Der Vorrat ist vollständig erhalten, kein einziges `failed(repeatedly_stuck)`.
Auf x86 waren es an dieser Stelle 32 abgeschriebene Zeilen. Der Befund aus 05-14
ist damit im Feld erledigt.

**Die Verwaltungsseite während der Pause:**

```
lowDisk True   diskFreeBytes 400154624   scheduled 106   running 4   failed 0
Banner findling-banner-lowdisk: SICHTBAR
Satz 'Little disk space left'                          in der Seite: True
Satz 'Indexing is paused so the index stays intact'    in der Seite: True
```

**Die Suche während der Pause:** zweimal HTTP 200 mit fünf Treffern, 381 ms und
387 ms. Ein pausierter Index ist ein vollständig benutzbarer Index, und das ist
die zweite Hälfte der Zusage, die auf dem Banner steht.

**Wiederherstellung.** Der Ballast geht um 08:39:09Z weg, 31 GB sind wieder frei,
und der Lauf geht **nach 91 Sekunden ohne jeden Eingriff** weiter. Die 91
Sekunden sind die Rückstufung des Pollers: er fragt nach mehreren
Fehlversuchen seltener nach, und der nächste Termin lag eben dort.

### Die drei Korrekturen aus 05-20, abgelesen

| Korrektur | Wo sie geprüft wurde | Ergebnis |
|---|---|---|
| Eine Rückgabe kostet keine Auslieferung | Drill 3, fünf Minuten Plattenpause, zehn Rückgaben | höchste Auslieferungszahl unverändert 1, **null** abgeschriebene Zeilen (x86: 32) |
| Der Abgleich heilt die verlorene Übergabe | der Volllauf selbst, Abgleich um 06:31Z | nicht ausgelöst, weil es nichts zu heilen gab: `seen=50049 stale=20 missing=0 given_up=0`, am Ende null Zeilen mit `no_text_layer` und null Fehlschläge. Siehe den Absatz darunter. |
| Die Statusseite wirft keinen Stillstand vor | der Volllauf, elf Stunden OCR-Nachlauf | **null** Aufnahmen mit `stalled`, höchster `stalledFor` 87 s, während der letzte Hintergrundauftrag 10 h 53 min alt war (x86: acht Stunden `stalled`) |

Zur mittleren Zeile, weil "nicht ausgelöst" leicht als "nicht geprüft"
gelesen wird und beides nicht dasselbe ist. Der Heilungszweig repariert ein Paar
aus `skipped(no_text_layer)` hier und `failed(repeatedly_stuck)` dort. Damit
dieses Paar entsteht, muss eine Quittung genau zwischen Textspur und OCR-Spur
verlorengehen **und** die Zeile danach abgeschrieben werden. Der ARM-Lauf hat
zwar eine verlorene Quittung erlebt, aber die Abschreibung ist ausgeblieben,
weil die Rückgabe aus derselben Korrektur die Auslieferung zurückgibt. Die
beiden Korrekturen greifen also ineinander: **die erste sorgt dafür, dass die
zweite seltener gebraucht wird.** Der Zweig selbst hängt an den sechs Tests aus
05-20 und nicht an dieser Messung; was diese Messung dazu beiträgt, ist der
Nachweis, dass der Zustand, den er repariert, unter dreizehn Stunden Volllast
nicht ein einziges Mal entstanden ist.

## Die Zusatzmessung: was ein zweiter Indexarbeiter bringt

Der Betreiber hat am 04.09. eine Zusatzmessung `INDEX_WORKERS=2` freigegeben.
Sie ist gefahren, und ihr Ergebnis ist ein anderes als erwartet: **die Frage
hat eine Antwort im Quelltext, und die Messung kann sie nicht geben.** Der
Abschnitt steht trotzdem vollständig hier, samt der Messung, denn eine Messung,
die nichts findet, ist ein Befund und keine Lücke.

### Der Aufbau

`backend/src/findling/config.py` legt `INDEX_WORKERS = 1` fest und sagt daneben
ausdrücklich, dass die Zahl keine Stellschraube ist und mit Absicht keine
Umgebungsvariable liest, "so that making it one is a code change somebody has to
defend in review". Ein `backend/tests/test_config.py` hält genau das fest.
Gemessen wurde deshalb in einem **Wegwerf-Abbild**, das nur auf der Box
existiert und mit ihr gelöscht wird:

```
FROM localhost:5000/findling_backend:05-21-arm
USER root
COPY patch.py /tmp/patch.py
RUN /app/.venv/bin/python /tmp/patch.py && rm /tmp/patch.py
USER 1000:1000
```

`patch.py` ersetzt genau eine Zeichenkette und bricht ab, wenn sie nicht genau
einmal vorkommt. Der Beweis, dass sonst nichts anders ist, ist ein Baumhash über
die Python-Dateien des Pakets, einmal mit und einmal ohne `config.py`:

| Abbild | Baumhash aller Python-Dateien | derselbe Hash ohne `config.py` |
|---|---|---|
| `05-21-arm` | `775a1559bb67fe04...` | `fa390f3addee6ba8...` |
| `05-21-arm-wegwerf-workers2` | `2e02e7852b538713...` | `fa390f3addee6ba8...` |

Gleiche zweite Spalte, verschiedene erste: der Unterschied liegt in `config.py`
und in keiner anderen Datei. Der Arbeitsbaum wurde nicht angefasst, dort steht
`INDEX_WORKERS` unverändert auf 1.

Ein Detail am Rande, das eine Viertelstunde gekostet hat und für jeden gilt, der
in diesem Abbild etwas mit `sed` sucht: **die Python-Dateien im Abbild tragen
CRLF**, weil der Arbeitsbaum von Windows kommt und als tar auf die Box gereicht
wurde. Ein Muster mit `$` am Zeilenende findet dort nichts. Deshalb macht
`patch.py` die Ersetzung auf Bytes.

### Der A/B-Aufbau

Zweihundert einseitige Scans aus dem Drill-Korpus, in Runde A in den Ordner
`workersA` und in Runde B derselbe Byteinhalt in den Ordner `workersB`
hochgeladen. Zwei Ordner und nicht zweimal derselbe, weil der schnelle Weg von
`is_unchanged` an der `file_id` hängt: dieselbe Datei ein zweites Mal
hochgeladen wäre in einer Sekunde als unverändert quittiert und hätte nichts
gemessen. Beide Runden liefen auf leerem Arbeitsvorrat, gegen denselben Index
von rund 51.700 Dokumenten, unter derselben harten Grenze, mit einem eigenen
Sampler.

| Größe | Runde A, `INDEX_WORKERS = 1` | Runde B, `INDEX_WORKERS = 2` | Unterschied |
|---|---|---|---|
| Dateien | 200, alle über die OCR-Spur | 200, alle über die OCR-Spur | keiner |
| Spanne erstes bis letztes Verdikt | **802 s** | **799 s** | 0,4 Prozent |
| je Datei | 4,01 s | 4,00 s | 0,4 Prozent |
| höchster `anon` | 357.408.768 Byte (340,9 MB) | 339.382.272 Byte (323,7 MB) | 5,0 Prozent |
| `memory.peak` | 458.264.576 Byte (437,0 MB) | 392.949.760 Byte (374,7 MB) | 14,2 Prozent |
| Textzeichen gewonnen | 692.486 | 692.486 | **keiner, auf das Zeichen** |
| `memory.events` | alle sechs null | alle sechs null | keiner |

### Was daraus folgt, und warum es kein Messfehler ist

Der Unterschied zwischen den beiden Runden ist null, und zwar nicht "klein",
sondern der Länge nach null: die identische Zeichenzahl zeigt, dass beide Runden
exakt dieselbe Arbeit getan haben, und die drei Sekunden Unterschied auf 800 sind
das Rauschen dieser Maschine.

Der Grund steht im Quelltext, und die Suche danach ist kurz:

```
$ grep -rn INDEX_WORKERS backend/src/findling --include=*.py
backend/src/findling/config.py:57:INDEX_WORKERS = 1
backend/src/findling/extract/text.py:75:# ... and INDEX_WORKERS is 1, so a crafted ...
backend/src/findling/nc/client.py:101:# INDEX_WORKERS at one that is exactly one mebibyte ...
```

**Eine Definition und zwei Kommentare. Keine einzige Stelle liest den Wert.**
Die Reihenfolge der Arbeit steht nicht an dieser Konstante, sondern in der Form
des Pollers: ein einziger Nebenläufer, und in ihm die Schleife
`for job in claim.jobs`, die eine Datei nach der anderen holt, auspackt,
extrahiert und an den Schreibpuffer übergibt. Das Protokoll zeigt es in beiden
Runden gleich, `claimed=2 indexed=2` je Durchgang.

`INDEX_WORKERS` ist damit kein Schalter, sondern eine **Zusage in Schriftform**:
die Zahl steht dort, damit jemand, der die Serialität aufheben will, sie
anfassen und im Review begründen muss. Der Test daneben bewacht genau diese
Eigenschaft. Das ist eine sinnvolle Konstruktion, und sie hat einen Preis, den
diese Messung sichtbar gemacht hat: **wer die Konstante hochsetzt, bekommt kein
schnelleres Programm, sondern ein Programm, das über sich etwas Falsches sagt.**

Damit ist die Frage des Betreibers beantwortet, nur anders als gedacht:

| Frage | Antwort |
|---|---|
| Was bringt ein zweiter Arbeiter der OCR-Spur? | Unbekannt, denn es gibt keinen zweiten Arbeiter zum Einschalten. Ihn zu bauen wäre eine Produktänderung: die Schleife in `poller.py` müsste nebenläufig werden, mit allem, was daran hängt (Schreibpuffer, Sperrfristen, Speicherspitzen zweier gleichzeitiger OCR-Läufe). |
| Was kostet er den Speicher? | Gerechnet, nicht gemessen: OCR steht bei 300 bis 600 MB je 300-dpi-Seite. Zwei gleichzeitige Läufe kämen zu den gemessenen 422 MB Spitze hinzu, und die Rechnung des Grenzwerts oben (3958 MB nutzbar, 345 MB Grundlast, 2048 MB Deckel) verträgt das nicht ohne den Deckel anzuheben. |
| Lohnt sich die Frage überhaupt? | Auf zwei Kernen sehr begrenzt. Die OCR-Spur ist rechengebunden; tesseract nutzt auf dieser Maschine bereits beide Kerne für eine Seite. |

Was diese Messung dennoch geliefert hat, und es ist nicht wenig: **eine
Wiederholbarkeitszahl für die OCR-Spur.** Zweimal dieselben 200 Scans, mit einer
Neuregistrierung des Containers dazwischen, ergeben 802 s und 799 s. Wer die
4,13 s je OCR-Datei aus dem Volllauf gegen die 4,01 s dieser Runden hält, sieht
denselben Wert, und der Unterschied ist die Textspur, die im Volllauf
danebenlief.

Notiert als DI-05-37: dass `INDEX_WORKERS` nichts steuert, ist im Quelltext
nicht falsch beschrieben, aber es steht auch nirgends. Ein Leser, der die Zeile
findet, hält sie für einen Schalter.

## Was der Test gekostet hat

### Die Generalprobe, Hetzner

Die letzte Abfrage vor dem Abbau, am 2026-09-04T11:22:59Z, also nach dem
Volllauf, nach allen Drills und nach dem Nachtrag:

| Posten | Wert |
|---|---|
| Laufzeit der Box | 19,2 Stunden, von 2026-09-03T16:10:50Z bis 2026-09-04T11:23:18Z |
| Preis der Box, cpx22 in `hel1` | 0,0371 EUR je Stunde, brutto |
| Preis des Volumes, 50 GB | 0,0047 EUR je Stunde, brutto |
| Preis der öffentlichen Adresse | 0,0010 EUR je Stunde, brutto |
| **Gesamtkosten des Tests** | **0,82 EUR, brutto** |
| Monatspreis, wäre sie stehen geblieben | 23,19 EUR Box, 3,40 EUR Volume, 0,59 EUR Adresse |

Woher die Zahl kommt, gehört dazu, weil "aus der Konto-API" zweierlei heißen
kann. Die drei Stundenpreise sind live aus der Preisliste dieses Kontos gelesen,
für genau diesen Servertyp und genau diesen Ort, und mit der Laufzeit
multipliziert, die die API für diesen Server führt. Es ist also der Bruttowert
dieses Kontos und nicht ein Posten von einer Rechnung; eine Rechnung gibt es zum
Zeitpunkt dieser Zeile noch nicht. Die Adresse steht ausdrücklich mit in der
Summe: sie macht acht Prozent aus, und wer sie weglässt, rechnet den Test
billiger, als er war.

Zum Vergleich, weil es die Größenordnung einordnet: die 0,82 EUR sind ungefähr
der Preis eines belegten Brötchens und decken einen Volllauf über 50.000 Dateien,
drei Störfall-Drills und alle Vorarbeiten ab.

### Der ARM-Lauf, AWS

Diese Zahl ist **gerechnet und nicht abgelesen**, aus der Laufzeit und den
Sätzen aus dem Abschnitt "Was die Umgebung kostet". Der Grund steht dort: dem
Zugang dieses Laufs fehlt `pricing:GetProducts` und der Blick auf die
Abrechnung. Für eine Maschine, deren Startzeit die API auf die Sekunde führt,
ist das Produkt genauer als ein Abrechnungsposten, der Tage später erscheint.

Zwei Laufzeiten und nicht eine, weil das Volume zwei Stunden nach der Instanz
entstanden ist und ein gemeinsamer Zeitraum die Zahl zu hoch rechnen würde.

| Posten | Laufzeit | Satz je Stunde | Kosten |
|---|---|---|---|
| m7g.large, `eu-central-1c` | 20,1997 h | 0,097800 USD | 1,9755 USD |
| Systemplatte, 40 GB gp3 | 20,1997 h | 0,005216 USD | 0,1054 USD |
| öffentliche IPv4 | 20,1997 h | 0,005000 USD | 0,1010 USD |
| Datenträger, 60 GB gp3 | 17,9797 h | 0,007824 USD | 0,1407 USD |
| **Summe bis zum Ende der Messungen** | | | **2,3226 USD, netto** |

Die Zeiten: die Instanz läuft seit 2026-09-04T13:12:28Z (`LaunchTime` aus
`describe-instances`), das Volume seit 2026-09-04T15:25:40Z, und die letzte
Messung dieses Berichts endete am 2026-09-05T09:24:27Z.

**Diese Summe ist ein Zwischenstand und keine Endabrechnung.** Die Box läuft
weiter, bis der Betreiber diesen Bericht abgenommen und über ihren Verbleib
entschieden hat; das ist eine Festlegung dieses Plans und keine Nachlässigkeit.
Jede weitere Stunde kostet 0,1158 USD, jeder weitere Tag 2,78 USD.

Drei Einordnungen dazu.

**Der Volllauf selbst kostet 1,48 USD.** 12 h 49 min zum vollen Stundensatz,
also gut die Hälfte der Summe. Die andere Hälfte ist Einrichtung, Korpusbau,
Drills und Zusatzmessung.

**Der Vergleich mit der Generalprobe ist keiner.** 0,82 EUR brutto bei Hetzner
gegen 2,32 USD netto bei AWS, für unterschiedlich lange Läufe auf
unterschiedlicher Hardware in unterschiedlichen Währungen mit
unterschiedlicher Steuerbehandlung. Der Bericht bildet daraus ausdrücklich keine
Vergleichszahl. Was sich sagen lässt: **die Ersatzmaschine ist rund achtmal so
teuer je Stunde wie die CAX11, für die sie einsteht**, und der Volllauf hat auf
ihr 25 Prozent länger gedauert. Beides zusammen macht den Preis der
Verfügbarkeit aus, und die Alternative wäre kein Lauf gewesen.

**Auch diese Summe ist klein gegen das, was sie trägt.** 2,32 USD decken den
gesamten Messteil der Store-Aussage auf der Zielarchitektur: 50.000 Dateien,
20 GB, vier Störfall-Drills und eine Zusatzmessung.

### Der Abbau der Generalprobe

Gelaufen am 2026-09-04T11:23:18Z mit `sh scripts/ops/hetzner_box.sh destroy`, in
zwei Aufrufen.

```
hetzner_box: detaching volume 106785477
hetzner_box: deleting volume 106785477
hetzner_box: deleting server 164459278
hetzner_box: deleting firewall 11569745
hetzner_box: the firewall was not deleted: resource_in_use: firewall with ID
             11569745 is still in use
hetzner_box: server 164459278 is gone, verified against the API
hetzner_box: volume 106785477 is gone, verified against the API
hetzner_box: firewall 11569745 is still there
hetzner_box: something is left over. Find it by label: purpose=findling-phase5
hetzner_box: the state file stays, so a second destroy can use it
```

Der zweite Aufruf, zwanzig Sekunden später:

```
hetzner_box: server 164459278 is gone, verified against the API
hetzner_box: volume 106785477 is gone, verified against the API
hetzner_box: firewall 11569745 is gone, verified against the API
hetzner_box: every resource of this run is gone and the state file is removed
```

Dass zwei Aufrufe nötig waren, ist die Bauart und kein Mangel: die Bindung einer
Firewall an einen Server löst sich erst, nachdem der Server wirklich weg ist, und
das Skript behandelt jede Antwort, die es nicht als `not_found` lesen kann,
ausdrücklich als "steht noch da". Ein Skript, das eine Ressource für gelöscht
erklärt, weil die API etwas Unverständliches geantwortet hat, wäre genau das
Risiko, gegen das dieser Abschnitt geschrieben ist.

Die Gegenprobe, unabhängig vom Skript, unmittelbar danach:

| Abfrage | Antwort |
|---|---|
| `/servers?label_selector=purpose=findling-phase5` | 0 Treffer |
| `/volumes?label_selector=purpose=findling-phase5` | 0 Treffer |
| `/firewalls?label_selector=purpose=findling-phase5` | 0 Treffer |
| `/floating_ips?label_selector=purpose=findling-phase5` | 0 Treffer |
| `/primary_ips?label_selector=purpose=findling-phase5` | 0 Treffer |
| `ssh root@62.238.114.125` | `Connection timed out` |
| Zustandsdatei des Werkzeugs | entfernt |

Damit ist der Auftrag aus D-01 erfüllt: keine Ressource dieses Kontos trägt das
Kennzeichen dieser Phase mehr, und die öffentliche Nextcloud mit Verwalterzugang,
die einen Tag lang im Netz stand, ist weg. Offen bleibt genau eine Spur außerhalb
dieses Kontos, und sie gehört nicht diesem Skript: der DNS-Eintrag
`loadtest.infranode.dev` zeigt auf eine Adresse, die es nicht mehr gibt, und wird
gesondert entfernt.

**Was mit dem Abbau unwiederbringlich weg ist:** das Abbild
`localhost:5000/findling_backend:05-12-fix`, das auf dieser Maschine gebaut wurde,
der Korpus aus 50.000 Dateien, der Index aus 50.396 Dokumenten und die
Zustandsdatenbank. Nachbaubar bleibt alles davon: der Codestand über den Baumhash,
der Korpus über Seed und Abbild, und die Messungen über die Rohdaten unter
`docs/measurements/2026-09-04-volllauf-cpx22/`. Was nicht nachbaubar ist, ist eine
Nachmessung an genau dieser Maschine; deshalb stand die Frage danach vor dem
Abbau und nicht danach.

### Der Verbleib der ARM-Box, und warum er offen ist

Die ARM-Box **steht noch**, mit ihrem Korpus, ihrem Index und beiden Abbildern.
Das ist eine Festlegung dieses Plans: der Abbau läuft erst nach der Abnahme
dieses Berichts durch den Betreiber, weil eine Nachmessung an genau dieser
Maschine nach dem Abbau nicht mehr möglich ist und eine Frage an die Zahlen
dieses Berichts genau so eine Nachmessung braucht.

Zur Entscheidung selbst gehört eine Angabe, die außerhalb dieses Plans liegt:
**Phase 6 braucht für den Semantik-Volllauf wieder eine ARM-Box**, und dieselbe
Knappheit, die diesen Lauf von Hetzner zu AWS getrieben hat, gilt weiter. Damit
stehen drei Wege offen statt zwei, und der mittlere ist neu:

| Weg | Was er kostet | Was er wert ist |
|---|---|---|
| stehen lassen | 2,78 USD je Tag | die Box ist sofort da, mit Korpus und Index; und sie ist eine öffentlich erreichbare Nextcloud mit Verwalterzugang, die niemand beaufsichtigt |
| **anhalten** (`stop-instances`) | nur die Datenträger, rund 0,31 USD je Tag | Korpus, Index und beide Abbilder bleiben; die Adresse wechselt beim nächsten Start, `box.env` und der DNS-Eintrag sind nachzuziehen |
| abbauen (`destroy`) | nichts mehr | Korpus (43 min Erzeugung), Index (12 h 49 min) und die auf der Box gebauten Abbilder sind weg und müssen für Phase 6 neu entstehen |

Der Bericht empfiehlt den mittleren Weg. Er nimmt die beiden Kosten weg, auf die
es ankommt, nämlich den Stundensatz der Instanz und das offene Netz, und er
erhält die zwölfeinhalb Stunden Rechenzeit, die im Index stecken. Die
Entscheidung trifft der Betreiber, nicht dieser Bericht.

Was beim Anhalten zu wissen ist, damit es nicht später überrascht: eine
angehaltene Instanz gibt ihre öffentliche Adresse zurück, `3.65.24.222` ist
danach nicht mehr diese Box, und der Eintrag `loadtest.infranode.dev` zeigt
dann auf eine fremde Adresse. Er gehört also mit dem Anhalten entfernt und beim
nächsten Start neu gesetzt.

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
| Volllauf | `phase5-full` | Abbild `localhost:5000/findling_backend:05-12-fix`, Pillow 12.3.0 | 50.000 | 20.208.046.426 | `c03a880323171d29c5278ed350db277291e39d256e95d5a8654dd4a6c244a274` |
| ARM-Volllauf | `phase5-full` | Abbild `localhost:5000/findling_backend:05-21-arm`, arm64 | 50.000 | 20.208.046.426 | `bcbef9b2cb067c2200df2a4a2e89408f690710983117d4e78328024046098a72` |
| ARM-Drills | `phase5-drill-arm` | dasselbe Abbild | 1.500 | 634.499.870 | `19558722e6af8c5f847f70cfd2d1b91b89952b183ed0331ba8101890fbacb048` |

Warum es zwei Prüfsummen für denselben Seed des Trockenlaufs gibt und welche
wofür gilt, steht oben im Abschnitt zum Trockenlauf. Die vierte Zeile ist der
Beleg für dieselbe Aussage auf voller Größe: **gleicher Seed, gleiche Bytezahl
auf das Byte, andere Prüfsumme**, weil die Schriftrasterung auf arm64 anders
ausfällt als auf x86. Wer eine Prüfsumme dieses Berichts nachrechnet, braucht
also nicht nur den Seed und das Abbild, sondern auch die Architektur.

Die ARM-Box wird mit demselben Muster bedient, nur gegen den anderen Anbieter:

```sh
# Preise dieses Kontos und der Bestand, ohne Nebenwirkung
AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... scripts/ops/aws_box.sh prices

# Zustand, Laufzeit und die bisherigen Kosten
AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... scripts/ops/aws_box.sh status

# Am Ende jedes Ausgangs, auch des unerwarteten
AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... scripts/ops/aws_box.sh destroy
```
