# Rohdaten der AIO-Grundlast, ARM-Box m7g.large

Die Messung, aus der `docs/performance.md` seine ARM-Spalte im Abschnitt "Die
AIO-Grundlast ohne Findling" zieht, dazu der Beitrag von HaRP und die Preise, aus
denen die Kostenzeile dieses Laufs gerechnet wird. Sie liegt hier, weil die
Maschine gelöscht wird: eine Zahl im Bericht ohne die Reihe, aus der sie stammt,
ist eine Behauptung, und niemand kann sie nachrechnen, sobald die Box weg ist.

**Diese Zahlen sind die des ARM-Laufs und erben keine von der x86-Generalprobe.**
Sie stehen im Bericht neben deren Zahlen und nicht an ihrer Stelle.

## Die Maschine

| Angabe | Wert |
|---|---|
| Maschine | AWS `m7g.large`, 2 vCPU AWS Graviton3, 2,6 GHz, `i-06b1d913f5c6f669b` |
| Architektur | arm64, `uname -m` sagt `aarch64` |
| Arbeitsspeicher | 8 GB laut Typ, **vom Kernel auf 4 GB gedeckelt**; `free -h` sagt 3.9Gi, `free -m` 3958 |
| Der Deckel | `mem=4G`, als Drop-in `/etc/default/grub.d/99-mem4g.cfg`, der `GRUB_CMDLINE_LINUX_DEFAULT` erweitert und die Konsolenparameter des Cloud-Abbilds stehen lässt |
| Kerne | `nproc` sagt 2 |
| Ort | `eu-central-1c`, Frankfurt |
| Systemplatte | 40 GB gp3, 3000 IOPS, 125 MB/s |
| Datenträger | 60 GB gp3, ext4, `/mnt/findling`, 3000 IOPS, 125 MB/s |
| Betriebssystem | Ubuntu 24.04.4 LTS, Kernel `7.0.0-1012-aws` |
| cgroup | v2 |
| Docker | 29.8.0, containerd 2.3.4, Snapshotter `overlayfs` |
| Nextcloud | 33.0.8.2, All-in-One, PostgreSQL, AppAPI 33.0.0 |
| Domäne | `loadtest.infranode.dev`, echtes Let's-Encrypt-Zertifikat |

Warum eine AWS-Maschine und nicht die CAX11 der Entscheidung D-01: bei Hetzner
war am 03. und am 04.09. kein einziger ARM-Typ in einer europäischen Region zu
mieten, und das Telefonat des Betreibers mit dem Anbieter am 04.09. hat ergeben,
dass die Knappheit Monate läuft. Die Ersatzmaschine ist als CAX11-Äquivalent
gewählt: zwei Kerne, vier Gigabyte einschließlich Seitencache, 40 GB
Systemplatte, arm64. Der Speicherdeckel ist der Kern dieser Parität, denn
gemessen wird der Abstand zur Decke.

## Die Dateien

| Datei | Was drinsteht |
|---|---|
| `nextcloud-aio-*.csv` | die sechs Messreihen der Grundlast, je 331 Messpunkte im Abstand von 5 s, mit der Abschlusszeile des Samplers |
| `mit-harp/nextcloud-aio-*.csv` | dieselben sechs plus HaRP, je 124 Messpunkte, die Nachmessung über zehn Minuten |
| `preise-ec2-roh.csv` | 195 Zeilen der öffentlichen Preisliste für `m7g.large` und `gp3` in `eu-central-1`, gefiltert auf `OnDemand`, unverändert |
| `preise-ipv4-roh.csv` | die zwei Zeilen für die öffentliche IPv4-Adresse aus der Preisliste von AmazonVPC |

## Die Spalten der Messreihen

`timestamp,anon,file,slab,current,peak`, alle Speicherangaben in Byte, gelesen
aus `memory.stat` und `memory.peak` der cgroup des Containers. Warum `anon` und
nicht `memory.current` die Zahl des Berichts ist, steht im Methodenteil von
`docs/performance.md` und im Kopf von `scripts/ops/rss_sampler.sh`.

Jede Zeile trägt das Präfix `findling-rss`, damit sich die Messung aus einem
Protokoll herausfiltern lässt, das auch anderes enthält.

Eine Kleinigkeit, die beim Vergleich mit der Generalprobe auffällt: die
Abschlusszeilen dieses Laufs führen in `memory.events` **sieben** Zähler statt
sechs. Neu ist `sock_throttled`, den der Kernel 7.0 mitbringt. Er steht wie die
anderen sechs auf null.

## Die drei Phasen der Grundlast

| Phase | Zeitraum |
|---|---|
| Leerlauf | 2026-09-04T15:40:05Z bis 15:52:09Z |
| unter Aufrufen, 29 Runden | 15:52:10Z bis 15:55:39Z |
| Leerlauf | 15:55:40Z bis 16:07:37Z |

Eine Runde ist: Anmeldeseite, `status.php`, Nutzerabfrage über OCS, `PROPFIND`
auf das Wurzelverzeichnis, Dateiansicht, Übersicht, dazu eine kleine Datei
hochladen und wieder löschen. Dieselben Aufrufe wie in der Generalprobe und
dieselbe Zahl von Runden; die Aufrufphase dauert hier 3 min 29 s statt 6 min,
weil zwischen den Runden nur fünf Sekunden Pause liegen. Verglichen wird der
gleichzeitige Höchststand und nicht die Dauer.

## Die Zahlen, die daraus in den Bericht gehen

| Größe | Wert |
|---|---|
| Summe `anon` im Mittel, sechs Container | 193 MB |
| Summe `anon` im gleichzeitigen Höchststand | **260 MB**, um 15:54:21Z |
| obere Schranke, Summe der sechs Maxima | 264 MB |
| Beitrag von HaRP, eigene Spalte | **53 MB** |
| Speichertod | keiner, `oom_killed=false` in allen dreizehn Abschlusszeilen |
| `memory.events` | alle sieben Zähler null, in allen dreizehn Abschlusszeilen |

Die Summe wird je Zeitpunkt gebildet und erst danach ihr Höchstwert genommen:
was die Box tragen muss, ist der gleichzeitige Stand und nicht die Summe von
sechs Maxima, die zu verschiedenen Minuten aufgetreten sind. Der Abstand
zwischen beiden ist hier vier MB.

## Nachbauen

```sh
# Grundlast: ein Sampler je Container, fuenf Sekunden Abstand
scripts/ops/rss_sampler.sh nextcloud-aio-nextcloud 5 nextcloud-aio-nextcloud.csv

# Verdichten, mit den Phasengrenzen als Argumenten. Genau dieses Werkzeug hat
# die Zahlen der Tabelle oben erzeugt, deshalb liegt es im Repository und nicht
# in einer Shell-Historie
scripts/ops/rss_digest.py <verzeichnis> 2026-09-04T15:52:10Z 2026-09-04T15:55:40Z

# Preise, ein einziger Durchlauf des oeffentlichen Preisverzeichnisses
curl -sS https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/eu-central-1/index.csv \
  | grep -E 'm7g[.]large|VolumeUsage[.]gp3' | grep OnDemand
```

Die Preisquellen namentlich, damit die Kostenzeile nachprüfbar bleibt: die
Preisliste von AmazonEC2 für `eu-central-1` in der Fassung `20260903195206`,
wirksam ab 2026-09-01, und die von AmazonVPC in der Fassung `20260831092232`.
Abgefragt am 2026-09-04. Daraus die drei Sätze, alle netto in USD:

| Posten | Satz |
|---|---|
| `m7g.large`, On Demand, Linux | 0,0978 USD je Stunde |
| `gp3`, bereitgestellter Speicher | 0,0952 USD je GB und Monat |
| öffentliche IPv4, in Benutzung | 0,0050 USD je Stunde |

Netto-USD sind **nicht** dasselbe Maß wie die Brutto-EUR der Hetzner-Tabelle im
Bericht. Der Bericht sagt das, statt beide in einen Vergleich zu stellen, den
keine von ihnen trägt.
