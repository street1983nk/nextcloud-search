# Runbook der Messbox

Dieses Runbook beschreibt, wie die Messbox aus dem Korpus-Snapshot wieder
entsteht, wie der Kostendeckel einer Anfahrt vor der ersten Kommandozeile
gerechnet wird und woran eine Anfahrt abgebrochen wird, bevor sie nennenswert
Geld kostet.

**Geheimnisregel, verbindlich.** Diese Datei liegt im öffentlichen
Repositorium. Dateipfade und Variablennamen stehen hier, Werte nicht: keine
IP-Adressen, keine lebenden Instanz- oder Volumekennungen, keine Inhalte von
Passwortdateien, keine Kontokennung. Wo ein Wert in einen Befehl gehört, steht
ein Platzhalter in spitzen Klammern und daneben ein Satz, woher der Wert kommt.
Die Snapshotkennung `snap-03f1d1d9ad9262704` ist davon ausgenommen und steht im
Klartext: sie steht bereits in mehreren committeten Dateien dieses
Repositoriums, und ohne Zugang zu dem Konto, dem sie gehört, ist sie nutzlos.

**Zur Schreibweise der Überschriften.** Die Abschnittsüberschriften sind bewusst
ohne Umlaute geschrieben, weil Prüfungen und Verweise auf sie zeigen. Der
Fließtext dieser Datei benutzt durchgehend echte Umlaute.

---

## 1. Wofuer dieses Runbook gilt und wofuer nicht

**Der Hauptpfad ist der Wiederaufbau aus dem Snapshot
`snap-03f1d1d9ad9262704`** (Entscheid D-09). Dieser Pfad wird in Phase 15 zum
ersten Mal vollzogen. Alles, was hier steht, ist aus den Skripten und den
Berichten der bisherigen Läufe zusammengetragen und lesend geprüft; gefahren
worden ist die Kette als Ganzes noch nie. Wo ein einzelner Schritt nicht einmal
trocken geprüft werden konnte, sagt das der Schritt selbst.

**Der Neuaufbau von null steht hier nur als Verweis.** Er wird nicht
ausgearbeitet, weil ungeprüfter Text in einem Runbook Ballast ist, der im Ernst
gelesen und geglaubt wird. Wer ihn braucht, liest die drei Messberichte, die
ihn wirklich gefahren haben:

- `docs/measurements/2026-09-04-volllauf-m7g/README.md` (Erstaufbau der Box und
  Erzeugung des Lastkorpus)
- `docs/measurements/2026-09-05-semantiklauf-m7g/README.md` (Neuaufsatz mit
  Semantikspur, mit eigenem Verzeichnis `skripte/`)
- `docs/measurements/2026-09-vergleichsmessung-m7g/README.md` samt
  `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/00-ablauf.md`
  (der Lauf, dessen Zahlen dieses Runbook als Planwerte benutzt)

### 1.1 Der Umfangsschock: die Box ist abgebaut, nicht geparkt

Seit dem 11.09.2026 gibt es die Maschine nicht mehr. Plan 11-12 hat Instanz,
Datenträger, Security Group und die Zustandsdatei `box.env` vollständig
abgebaut; der A-Record `loadtest.infranode.dev` zeigt seither ins Leere. Unter
`${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}/` liegt nur noch
`systemplatte-2026-09/` mit `home-ubuntu-work.tar.gz` und
`vergleichsmessung-nebendateien.tar.gz`. Es gibt keine `box.env`.

Das ist kein Randbefund, sondern bestimmt die Reihenfolge dieses Runbooks: es
beginnt mit dem Handaufbau der Maschine und nicht mit `aws_box.sh start`. Ohne
Zustandsdatei verhalten sich die neun Unterbefehle von `scripts/ops/aws_box.sh`
so:

| Unterbefehl | Zustand ohne `box.env` |
|---|---|
| `volume`, `restore`, `stop`, `start`, `snapshot` | `require_state` bricht ab: "no state file at ..." |
| `destroy` | `require_state`, und zusätzlich `FINDLING_STATE_BACKUP` als Pflichtpfad |
| `status` | liest weich und fällt auf die Suche nach dem Tag zurück |
| `create` | verweigert grundsätzlich und druckt nur das Rezept |
| `prices` | läuft, er braucht keine Box |

### 1.2 Was im Snapshot liegt

Der Snapshot ist die Aufnahme des Datenträgers, der auf der Box als
`/mnt/findling` hing (ext4, per UUID mit `nofail` in der fstab). Darin:

- die Docker-`data-root` und die containerd-Wurzel
- die lokale Registry der Box (`localhost:5000`) mit den Messabbildern
- `ncdata`, darin `lasttest/files/loadtest` mit den 50.000 Lastdateien
- der Tantivy-Index und die Vektorablage, im Zustand nach dem Lauf vom
  10.09.2026: 52.111 Dokumente
- Belegung 35 GB von 59 GB, `FullSnapshotSizeInBytes` rund 55,4 GB geschriebene
  Blöcke, also die 51,6 GiB, die der Abbaubericht nennt

### 1.3 Was NICHT im Snapshot liegt

Alles, was auf der Systemplatte lag, und alles, was am Betriebssystem
eingestellt war:

- die Systemplatte insgesamt (40 GB gp3, `DeleteOnTermination=true`, mit der
  Instanz gelöscht)
- `/home/ubuntu/work` samt `.pw/`; gesichert als `home-ubuntu-work.tar.gz`
  ausserhalb des Arbeitsbaums, siehe Abschnitt 3
- die Konfiguration des Docker-Daemon, die die `data-root` überhaupt erst auf
  `/mnt/findling` zeigen lässt
- der Grub-Drop-in mit `mem=4G`, die fstab-Zeile und der `/etc/hosts`-Pin

Ein Wiederaufbau ist daher: Maschine bauen, Systemplatte herrichten, Docker mit
der richtigen `data-root` konfigurieren, bevor er startet, Volume aus dem
Snapshot anhängen und mounten, die Sicherung der Systemplatte zurückspielen,
A-Record setzen, den Container bewaffnen und die harte Speichergrenze neu
setzen. Die nummerierten Blöcke in Abschnitt 4 gehen genau diesen Weg.

---

## 2. Das Deckel-Rechenblatt

Dieser Abschnitt steht vor der ersten Kommandozeile, und das ist Absicht
(Entscheid D-05). Vor jeder Anfahrt wird der Deckel aus den zuletzt gemessenen
Posten neu gerechnet, nicht aus einer erinnerten Summe. Der Owner bekommt damit
am Phase-15-Checkpoint eine belegte Zahlbasis statt einer Zahl.

### 2.1 Zeitposten

Die Spalte "Ist (Phase 15)" bleibt leer. Sie wird während der Anfahrt gefüllt,
und der nächste Lauf rechnet gegen die gefüllte Spalte statt gegen die
Planwerte.

| Posten | Planwert | Quelle | Ist (Phase 15) |
|---|---|---|---|
| Handaufbau der Maschine (Security Group, Schlüssel, Instanz, `mem=4G`, Neustart) | **2 h 30 min, Schätzung** | nirgends gemessen, Annahme A8 der Phasenrecherche, ausdrücklich als Schätzung geführt | |
| Wiederaufbau aus dem Snapshot und Rüstzeit (Volume, Mount, Docker, Rückspielung, A-Record, Bewaffnung) | 1 h 30 min | Anfahrt und Vormessungen v1.1 waren 38 min bei bestehender Box; der Aufschlag ist der Wiederaufbau und ist geschätzt | |
| Volllauf beide Spuren bis zum letzten Vektor | **26 h 37 min** | v1.1, Abschnitt 7 des Berichts, gemessen | |
| Untersuchung der vier regressiven Laststufen, je ein Entscheid | 1 h 30 min | neu in v1.2, geschätzt | |
| Wiederaufwärm-Messung der Entladung in vier Ausprägungen (warm und kalt, je mit und ohne Seitencache) | 2 h 00 min | neu in v1.2, geschätzt | |
| Sprachfall-Messung mit der neuen Messgrösse, inklusive Erstvollzug des Skripts | 1 h 00 min | neu in v1.2, geschätzt | |
| Abbau und Endmessungen (Gegenproben vor dem Abbau, Snapshot, `destroy`, Tag-Sweep) | 1 h 00 min | v1.1 Abschnitt 17 und der Abbaulauf vom 11.09.2026 | |
| **Summe der Planwerte** | **36 h 07 min** | Addition der Zeilen darüber | |

**Der Planwert des Volllaufs nimmt keine Verbesserung vorweg.** Ob der
Top-up-Fix den Lauf verkürzt, ist genau die Frage, die dieser Lauf beantworten
soll. Als Planwert gilt deshalb 26 h 37 min und nicht ein erhoffter kleinerer
Wert. Genau dieser Fehler hat den Deckel des v1.1-Laufs gerissen: geplant waren
rund 19 Stunden, gebraucht wurden 26 h 37 min.

### 2.2 Posten, die guenstiger werden

| Posten | Wirkung |
|---|---|
| Erzeugung und Hochladen des Lastkorpus (50.000 Dateien) | entfällt vollständig, der Korpus kommt aus dem Snapshot. In v1.0 und v1.1 war das ein eigener, mehrstündiger Block |

### 2.3 Kostensaetze

Sechs gepinnte Sätze, alle netto in USD. `scripts/ops/aws_box.sh prices` druckt
sie mitsamt ihrer Herkunft; der einzige API-Aufruf dieses Unterbefehls ist
`describe-instance-types` und ist kostenlos.

| Satz | Wert |
|---|---|
| laufend gesamt | **0,115841 USD je Stunde** |
| davon Box `m7g.large` | 0,097800 USD je Stunde |
| davon Speicher gp3 (100 GB) | 0,013041 USD je Stunde |
| davon öffentliche IPv4-Adresse | 0,005000 USD je Stunde |
| angehalten | 0,3130 USD je Tag |
| Snapshot, dauerhaft | 2,79 bis 2,99 USD je Monat |

**Die Preisliste wird bewusst nicht heruntergeladen.** Die regionale Liste ist
über ein Gigabyte gross; ein Werkzeug, das sie zieht, sobald jemand "prices"
tippt, ist eine Falle. Die Sätze sind in `scripts/ops/aws_box.sh` gepinnt, der
Befehl, der sie reproduziert, steht in `cmd_prices`, und die Abfrage stammt vom
2026-09-04.

Die Snapshotkosten laufen weiter, ob eine Anfahrt stattfindet oder nicht. Sie
gehören daher **nicht** in den Stundendeckel einer Anfahrt, sondern in die
Monatsrechnung; sie stehen hier, damit niemand sie für den Deckel hält.

### 2.4 Die Deckel-Geschichte, in drei Zeilen

| Wann | Deckel | Was geschah |
|---|---|---|
| Owner am 09.09.2026 | 30 h / 3,50 USD | der ursprüngliche Deckel |
| 2026-09-10 um 15:20Z | gerissen | angehoben auf 34 h / 4,00 USD, vor den Nachmessungen |
| Ende des Laufs | verbraucht **31,05 h / 3,5969 USD** | gegen den angehobenen Deckel nicht gerissen |

**Der Deckel ist schon einmal gerissen.** Das ist der Grund, warum dieses
Rechenblatt existiert und warum es vor der ersten Kommandozeile steht.

### 2.5 Der Rechenweg

```
Deckel (Stunden) = Summe der Zeitposten aus 2.1 x (1 + Zuschlag)
Deckel (USD)     = Deckel (Stunden) x 0,115841 USD je Stunde
```

Mit den Planwerten dieser Fassung, Zuschlag 15 Prozent für Erstvollzug und
Unvorhergesehenes:

```
36,12 h x 1,15 = 41,54 h, aufgerundet 42 h
42 h x 0,115841 USD/h = 4,8653 USD, aufgerundet 4,90 USD
```

**Empfehlung für Phase 15: 42 Stunden und 4,90 USD netto.** Die Untergrenze ist
31 h und 3,59 USD, weil genau so viel der v1.1-Lauf mit weniger Arbeitsumfang
verbraucht hat; ein Vorschlag darunter ist rechnerisch schon gerissen, bevor er
ausgesprochen ist.

### 2.6 Wohin die Schlusszahlen VOR dem Abbau geschrieben werden

`aws_box.sh destroy` löscht `box.env`. Danach existiert die Kosten- und
Schadenshistorie der Box nur noch in einer committeten Rohdatei. Das ist am
11.09.2026 bereits eingetreten, und die heutige Abwesenheit von `box.env` ist
der Beleg dafür. Vor dem Abbau werden deshalb `BOX_LAST_UPTIME_HOURS`,
`BOX_LAST_UPTIME_COST_USD`, der freigegebene Deckel und die Differenz in die
Rohdatei des laufenden Messverzeichnisses geschrieben und committet, nach dem
Muster von `docs/measurements/2026-09-werkzeugfixe/rohdaten/07-snapshot-und-abbau.txt`,
Abschnitt 5.

**Die Freigabe selbst fällt nicht hier.** Dieses Rechenblatt liefert die Zahl;
freigegeben wird sie vom Owner am Checkpoint der Phase 15, mit Datum und
Deckel.

---

## 3. Vorbedingungen ohne Box-Zeit

Diese Liste wird vollständig abgearbeitet, **bevor** die erste kostenpflichtige
Ressource entsteht. Jede Zeile kostet null Box-Minuten, und jede Zeile hat
schon einmal eine Anfahrt Zeit gekostet, weil sie erst auf der Box aufgefallen
ist.

| Nr | Vorbedingung | Prüfung | Warum vorher |
|---|---|---|---|
| 1 | **Laufnummer eines grünen `integration.yml`-Laufs** als `CI_LAUF` | `gh run list --workflow=integration.yml --status success --limit 1` | Ohne Laufnummer bricht die Sprachfall-Messung vor dem ersten Fall ab. Die Aussage des Laufs hängt an der Messung mit eigenem Index, und die fährt in CI |
| 2 | **Die Sicherung der Systemplatte** liegt ausserhalb des Arbeitsbaums: `${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}/systemplatte-2026-09/home-ubuntu-work.tar.gz` | Datei vorhanden, sha256 gegen `07-snapshot-und-abbau.txt` Abschnitt 4 | Diese Datei trägt die Passwortdateien der Konten `admin` und `lasttest`. Sie gehört in kein Repositorium, und sie ist im Snapshot nicht enthalten |
| 3 | **Die AWS-Anmeldung** liegt als Datei ausserhalb des Arbeitsbaums und setzt genau zwei Variablen: `AWS_ACCESS_KEY_ID` und `AWS_SECRET_ACCESS_KEY` | die beiden Namen sind gesetzt, die Werte erscheinen in keinem Argument und in keinem Protokoll | `aws_box.sh` liest sie ausschliesslich aus der Umgebung. Ein Wert in einem Argument steht in der Prozessliste und in der Shell-Historie |
| 4 | **Die lesende Snapshot-Probe** ist gefahren und stimmt mit der erwarteten Ausgabe überein | `aws ec2 describe-snapshots --region eu-central-1 --snapshot-ids snap-03f1d1d9ad9262704`, Erwartung in `docs/measurements/2026-09-v12-messung/rohdaten/01-aws-lesende-proben.txt` Abschnitt 1: `State completed`, `Progress 100%`, `VolumeSize 60` | Ein Volume aus einem unfertigen Snapshot hat fehlende Blöcke, und nichts sagt das, bis etwas sie liest. Die Probe ist lesend und kostenlos |
| 5 | **Das Tag des Snapshots** ist gelesen: `purpose=findling-corpus-keep` | `aws ec2 describe-tags --region eu-central-1 --filters "Name=resource-id,Values=snap-03f1d1d9ad9262704"`, Erwartung ebenda Abschnitt 2 | Ein Volume aus diesem Snapshot erbt dieses Tag und entginge damit dem Tag-Sweep des Abbaus. `aws_box.sh restore` taggt pflichtmässig um und liest zurück |
| 6 | **Die Werkzeuge auf der Entwicklungsmaschine**: AWS CLI v2, `gh`, `python3`, `uv` | `aws --version`, `gh --version`, `python3 -V`, `uv --version` | `aws_box.sh` bricht sonst in `require_tools` ab, und zwar erst, nachdem die Anfahrt begonnen hat |
| 7 | **`jq` auf der Box**, sobald sie steht | `ssh ... 'jq --version'` | Ohne `jq` endet der Sprachfall-Lauf mit Rückgabewert 18, und zwar mitten in der bezahlten Zeit |
| 8 | **Der Zugang zur DNS-Verwaltung** für den A-Record `loadtest.infranode.dev` liegt vor | Anmeldung am Verwalter der Zone geprüft | Der Record zeigt seit dem 11.09.2026 ins Leere. Wer ihn erst während der Anfahrt sucht, bezahlt die Suche |
| 9 | **Das Deckel-Rechenblatt aus Abschnitt 2 ist neu gerechnet** und vom Owner mit Datum freigegeben | eine Zeile `Anfahrt freigegeben: <Datum>, Deckel <h> h / <USD> USD` im Bericht des Laufs, geschrieben **vor** der ersten Minute | Eine Anfahrt ohne Deckel ist eine offene Rechnung. Der Abbau der Box ist ein eigener Entscheid und nicht Teil dieser Freigabe |

**Keine dieser neun Zeilen braucht eine laufende Box.** Wer eine von ihnen auf
später verschiebt, verschiebt sie in die bezahlte Zeit.

---

## 4. Aufbau, in nummerierten Bloecken

Jeder Block hat dieselbe Form: eine Überschrift mit Nummer und Zweck, ein
Kommandoblock zum Kopieren, und darunter eine Zeile `Erwartete Ausgabe` mit
dem, was zu sehen sein muss. Wo die erwartete Ausgabe in Phase 12 nicht trocken
geprüft werden konnte, steht statt einer Gewissheit die Marke
`in Phase 15 erstmals vollzogen`; sie bedeutet, dass die Ausgabe aus einem
Skript oder einem früheren Bericht abgeleitet und nicht gegen diese Kette
gefahren ist.

**Die Platzhalter dieses Abschnitts**, damit kein Wert in dieser öffentlichen
Datei steht:

| Platzhalter | Woher der Wert kommt |
|---|---|
| `<eigene-adresse>/32` | die eigene öffentliche Adresse, genau ein Wirt, nicht ein Netz |
| `<ganzes-netz>` | die CIDR-Schreibweise für das gesamte Internet: vier Nullen, Präfixlänge null |
| `<vpc>`, `<sg>`, `<subnetz>` | aus der Antwort des jeweils vorigen Blocks |
| `<box>` | der SSH-Zielname der Maschine, aus der eigenen SSH-Konfiguration |
| `<uuid>` | aus `blkid` des Datenträgers, siehe Block 7 |

### Die wiederkehrenden Handgriffe, die `aws_box.sh start` NICHT erledigt

Diese Tabelle gilt nicht nur für den Erstaufbau, sondern nach **jedem**
Maschinenstart. `aws_box.sh start` weckt die Instanz, liest die neue öffentliche
Adresse und zieht die SSH-Regel der Security Group nach; alles Übrige bleibt
offen und nennt sich selbst.

| Offener Punkt | Handgriff | Warum |
|---|---|---|
| A-Record `loadtest.infranode.dev` | auf die neue Adresse setzen. Rückfall 1: den `/etc/hosts`-Pin nach JEDEM Maschinenneustart neu aus `docker inspect` des Apache-Containers bilden. Rückfall 2: mit `curl --resolve` arbeiten | Ein Neustart verteilt die Adressen der Docker-Brücke neu. Der Apache ist einmal von einer Brückenadresse auf eine andere gewandert, und der alte Pin liess den Poller 300 Sekunden ins Backoff laufen |
| Der Container ist nach einem Maschinenstart nicht bewaffnet (DI-05-36) | `occ app_api:app:disable findling_backend`, danach `occ app_api:app:enable findling_backend` | Der Beweis der Bewaffnung ist ein GEZÄHLTER Poller-Durchgang im Protokoll und kein abgelesener Zustand. Ein abgelesener Zustand war schon einmal grün, während nichts lief |
| Die harte Speichergrenze ist nach jeder Registrierung weg | `docker update --memory=2g --memory-swap=2g`, danach `memory.max` und `memory.swap.max` AUS DER CGROUP zurücklesen | Die Registrierung baut den Container neu und verliert die Grenze. Ohne sie misst der Lauf eine andere Maschine als v1.1 |
| Nur EINE Nextcloud auf dem Docker-Dienst | `docker ps` zählt, und zwar VOR dem ersten `--rm-data` | Der Volumenname einer ExApp folgt allein aus ihrer App-Kennung. Am 07.09.2026 hat eine zweite, frische Nextcloud mit `app_api:app:unregister --rm-data` das Messvolumen der ERSTEN gelöscht |
| Git für Windows schreibt Pfadargumente um | in jedem neuen Skript, das von dieser Maschine gegen die Box oder gegen die AWS-API läuft, die Pfadumschreibung für den eigenen Prozess abschalten, so wie `aws_box.sh` es tut | Aus `/dev/sdf` wurde ein Windows-Pfad unterhalb des Git-Installationsverzeichnisses. Der Aufruf lief durch und meinte etwas anderes, als er sagte |

---

### Block 1: Security Group anlegen

```sh
aws ec2 create-security-group --region eu-central-1 \
    --group-name findling-loadtest \
    --description "findling load test" --vpc-id <vpc>

aws ec2 authorize-security-group-ingress --region eu-central-1 \
    --group-id <sg> \
    --ip-permissions \
    'IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=<eigene-adresse>/32}]' \
    'IpProtocol=tcp,FromPort=80,ToPort=80,IpRanges=[{CidrIp=<ganzes-netz>}]' \
    'IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges=[{CidrIp=<ganzes-netz>}]' \
    'IpProtocol=udp,FromPort=443,ToPort=443,IpRanges=[{CidrIp=<ganzes-netz>}]'
```

SSH steht ausschliesslich auf genau einer Adresse mit Präfixlänge 32, und zwar
auf der des Owners. Die drei übrigen Regeln sind die einzigen, die offen sind.
**UDP 443 ist neu gegenüber dem Rezept in `cmd_create`** und stammt aus DI-05-35:
der Apache des AIO-Abbilds kündigt HTTP/3 über einen Alt-Svc-Kopf an, und ohne
UDP 443 laufen Klienten, die dem Kopf folgen, in eine Zeitüberschreitung, bevor
sie auf TCP zurückfallen.

`Erwartete Ausgabe`: `create-security-group` liefert ein Feld `GroupId`, das ab
hier `<sg>` ist; `authorize-security-group-ingress` liefert `"Return": true`
und vier `SecurityGroupRules`-Einträge, davon einer mit `"IpProtocol": "udp"`.
Marke: `in Phase 15 erstmals vollzogen`.

### Block 2: Schluesselpaar anlegen

```sh
aws ec2 create-key-pair --region eu-central-1 \
    --key-name findling-loadtest \
    --query KeyMaterial --output text > ~/.ssh/findling-loadtest
chmod 600 ~/.ssh/findling-loadtest
```

Der private Teil verlässt die Maschine nie, die ihn erzeugt hat. Er gehört in
kein Repositorium, in keine Sicherung, die irgendwohin synchronisiert, und in
keinen Kommandozeilenparameter.

`Erwartete Ausgabe`: die Datei `~/.ssh/findling-loadtest` beginnt mit
`-----BEGIN RSA PRIVATE KEY-----` beziehungsweise
`-----BEGIN OPENSSH PRIVATE KEY-----` und ist grösser als null Byte; `ls -l`
zeigt Rechte `-rw-------`. Marke: `in Phase 15 erstmals vollzogen`.

### Block 3: Instanz erzeugen

```sh
aws ec2 run-instances --region eu-central-1 \
    --image-id ami-0e79e661e73ddfac9 \
    --instance-type m7g.large \
    --key-name findling-loadtest \
    --security-group-ids <sg> \
    --subnet-id <subnetz> \
    --block-device-mappings \
    'DeviceName=/dev/sda1,Ebs={VolumeSize=40,VolumeType=gp3,DeleteOnTermination=true}' \
    --tag-specifications \
    'ResourceType=instance,Tags=[{Key=Name,Value=findling-loadtest},{Key=purpose,Value=findling-phase5}]'
```

Das Abbild ist arm64, der Typ ist `m7g.large` (Entscheid D-06, Vergleichbarkeit
mit Baseline und v1.1), das Subnetz liegt in `eu-central-1c`, weil der
Datenträger aus Block 6 nur in seiner eigenen Zone angehängt werden kann. Die
Systemplatte hat 40 GB und `DeleteOnTermination=true`: sie steht für die
40 GB der Hetzner-Maschine, die dieser Lauf vergleichen soll, und sie ist
bewusst flüchtig, weil nichts Dauerhaftes auf ihr liegen darf.

`Erwartete Ausgabe`: `Instances[0].InstanceId` und `Instances[0].Placement.AvailabilityZone`
mit dem Wert `eu-central-1c`; `aws ec2 wait instance-running` kehrt ohne
Ausgabe zurück. Marke: `in Phase 15 erstmals vollzogen`.

### Block 4: box.env NEU schreiben

```sh
mkdir -p "${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}"
umask 077
cat >> "${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}/box.env" <<'ENDE'
BOX_INSTANCE_ID=<instanz-id aus Block 3>
BOX_SECURITY_GROUP=<sg aus Block 1>
ENDE
```

Die Zustandsdatei liegt **ausserhalb des Arbeitsbaums**, unter
`${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}/box.env`. Die Begründung
steht im Skript selbst: eine Zustandsdatei im Repositorium ist ein unachtsames
`git add` von einem öffentlichen Commit entfernt.

Von Hand geschrieben werden genau zwei Felder, weil die Maschine von Hand
entsteht: `BOX_INSTANCE_ID` (ohne sie bricht `require_state` ab) und
`BOX_SECURITY_GROUP` (ohne sie brechen `start` und `destroy` ab). Alle übrigen
Felder schreibt `aws_box.sh` selbst und immer anhängend, nie überschreibend:
`VOLUME_ID`, `VOLUME_NAME`, `VOLUME_SIZE_GB`, `VOLUME_TYPE`,
`VOLUME_CREATED_ISO`, `VOLUME_FROM_SNAPSHOT` aus `volume` und `restore`;
`BOX_IP`, `BOX_STARTED_ISO`, `BOX_SSH_FROM` aus `start`; `BOX_STOPPED_ISO`,
`BOX_LAST_UPTIME_HOURS`, `BOX_LAST_UPTIME_COST_USD`,
`BOX_PARKED_COST_USD_PER_DAY` aus `stop`; `CORPUS_SNAPSHOT_ID` aus `snapshot`.

`Erwartete Ausgabe`: `scripts/ops/aws_box.sh status` meldet den Zustand der
Instanz aus der API statt "no state file at ...". Marke:
`in Phase 15 erstmals vollzogen`.

### Block 5: Harte Speichergrenze mem=4G

```sh
ssh <box> "echo 'GRUB_CMDLINE_LINUX_DEFAULT=\"\$GRUB_CMDLINE_LINUX_DEFAULT mem=4G\"' \
    | sudo tee /etc/default/grub.d/99-mem4g.cfg"
ssh <box> 'sudo update-grub && sudo reboot'
# nach dem Neustart:
ssh <box> 'free -h; nproc; uname -m; cat /proc/cmdline'
```

Der Drop-in **erweitert** die bestehende `GRUB_CMDLINE_LINUX_DEFAULT`, er
ersetzt sie nicht. Eine ersetzende Zeile nimmt der Maschine Konsolen- und
Netzparameter, die beim nächsten Start gebraucht werden.

`Erwartete Ausgabe`: `free -h` zeigt `3.9Gi` als Gesamtspeicher, `nproc` sagt
`2`, `uname -m` sagt `aarch64`, und `/proc/cmdline` enthält `mem=4G`. Diese drei
Zahlen sind aus dem Rezept in `cmd_create` übernommen und in drei früheren
Läufen so gemessen worden.

### Block 6: Volume aus dem Snapshot

```sh
scripts/ops/aws_box.sh restore
# oder, gegen eine andere Aufnahme:
scripts/ops/aws_box.sh restore <snapshot-id>
```

Der Unterbefehl liest den Snapshot, bevor er irgendetwas erzeugt, bestellt ein
Volume von 60 GB in der Zone der Box, taggt es pflichtmässig von
`purpose=findling-corpus-keep` auf `purpose=findling-phase5` um, liest die Tags
zurück und hängt es an. Ohne das Umtaggen überlebte das Volume den Tag-Sweep des
Abbaus und würde weiter berechnet, ohne dass jemand danach sucht.

`Erwartete Ausgabe`: der Kopf der Antwort steht in
`docs/measurements/2026-09-v12-messung/rohdaten/01-aws-lesende-proben.txt`,
Abschnitt 1, und lautet `State completed`, `Progress 100%`, `VolumeSize 60`,
`Encrypted false`, dazu `Description` mit den 52111 Dokumenten und
`VolumeId <Kennung des Ursprungsvolumes, siehe dieselbe Rohdatei>`. Danach
folgen die Zeilen `tags of ... after the retagging: ... purpose=findling-phase5`,
`waiting for volume ... to become available`, `attaching ...` und
`this subcommand ends at the attach`. Der lesende Teil ist am 14.09.2026 so
gefahren worden; der erzeugende Teil trägt die Marke
`in Phase 15 erstmals vollzogen`.

### Block 7: Datentraeger mounten

```sh
ssh <box> 'lsblk -b -o NAME,SIZE,TYPE'          # den 60-GB-Datentraeger finden
ssh <box> 'sudo blkid /dev/nvme?n1'             # dessen UUID ablesen
ssh <box> 'sudo mkdir -p /mnt/findling'
ssh <box> "echo 'UUID=<uuid> /mnt/findling ext4 defaults,nofail 0 2' | sudo tee -a /etc/fstab"
ssh <box> 'sudo mount -a && df -h /mnt/findling'
```

**Der Datenträger wird über seine GRÖSSE gefunden und über seine UUID
gemountet, nie über seinen Namen.** Nitro-Instanzen ignorieren den Gerätenamen,
den die API bekommt (`/dev/sdf`), und zeigen den Datenträger als
`/dev/nvme?n1` in der Reihenfolge des Anhängens. Ein fstab-Eintrag über den
Namen zeigt nach dem nächsten Neustart auf ein anderes Gerät oder ins Leere.
`nofail` steht in der Zeile, weil eine Maschine, die wegen eines fehlenden
Datenträgers nicht mehr hochkommt, nur noch über die serielle Konsole
erreichbar ist.

`Erwartete Ausgabe`: `lsblk` zeigt genau einen Datenträger mit rund 60 GB neben
der 40-GB-Systemplatte; `df -h /mnt/findling` meldet 59G Gesamtgrösse und
rund 35G belegt, und `ls /mnt/findling` zeigt `docker` und `ncdata`. Die Zahlen
stammen aus `docs/measurements/2026-09-werkzeugfixe/rohdaten/07-snapshot-und-abbau.txt`,
Abschnitt 4. Marke: `in Phase 15 erstmals vollzogen`.

### Block 8: Docker-data-root, BEVOR der Daemon startet

```sh
ssh <box> 'sudo systemctl stop docker docker.socket containerd || true'
ssh <box> "printf '%s\n' '{ \"data-root\": \"/mnt/findling/docker\" }' \
    | sudo tee /etc/docker/daemon.json"
ssh <box> 'sudo systemctl start docker && docker info | grep -i "docker root dir"'
```

**Die Reihenfolge ist die ganze Aussage dieses Blocks.** Startet der Daemon
einmal ohne diese Datei, legt er seine Wurzel auf der Systemplatte an, zieht
dort Abbilder hin und füllt eine 40-GB-Platte, während die 60 GB daneben
ungenutzt bleiben. Der Snapshot trägt die `data-root` und die
containerd-Wurzel; sie sind nur brauchbar, wenn der Daemon von Anfang an dort
hinsieht.

`Erwartete Ausgabe`: `docker info` meldet `Docker Root Dir: /mnt/findling/docker`,
und `curl -s localhost:5000/v2/_catalog` antwortet
`{"repositories":["findling_backend"]}`, also die lokale Registry aus dem
Snapshot. Marke: `in Phase 15 erstmals vollzogen`.

### Block 9: Systemplatte zurueckspielen

```sh
scp "${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}/systemplatte-2026-09/home-ubuntu-work.tar.gz" \
    <box>:/tmp/
ssh <box> 'cd /home/ubuntu && tar xzf /tmp/home-ubuntu-work.tar.gz && rm /tmp/home-ubuntu-work.tar.gz'
ssh <box> 'find /home/ubuntu/work -type f | wc -l; du -sh /home/ubuntu/work'
```

**Diese Datei trägt die Passwortdateien der Konten `admin` und `lasttest`.** Sie
bleibt ausserhalb des Arbeitsbaums und wird nicht committet; eine Aufnahme ins
Repositorium setzt eine eigene Durchsicht auf Geheimnisse voraus, die nicht
Gegenstand dieses Runbooks ist. Die Kopie auf der Box wird nach dem Auspacken
gelöscht, damit sie nicht in einer späteren Aufnahme landet.

`Erwartete Ausgabe`: 435 Einträge und rund 3.971.065 Byte in der Sicherung,
sha256 wie in `07-snapshot-und-abbau.txt`, Abschnitt 4 vermerkt; nach dem
Auspacken zeigt `/home/ubuntu/work` rund 91 MB. Marke:
`in Phase 15 erstmals vollzogen`.

### Block 10: A-Record setzen

```sh
# beim Verwalter der Zone: loadtest.infranode.dev auf die neue Adresse setzen
dig +short loadtest.infranode.dev
# Rueckfall 1, nach JEDEM Maschinenneustart neu zu bilden:
ssh <box> "docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' nextcloud-aio-apache"
ssh <box> 'sudo sed -i "/loadtest.infranode.dev/d" /etc/hosts'
# dann die frisch gelesene Adresse mit dem Namen in /etc/hosts eintragen
# Rueckfall 2, ganz ohne Namensdienst:
curl --resolve 'loadtest.infranode.dev:443:<adresse>' https://loadtest.infranode.dev/status.php
```

Der Record zeigt seit dem Abbau ins Leere. Rückfall 1 ist **kein einmaliger
Handgriff**: jeder Maschinenneustart verteilt die Adressen der Docker-Brücke
neu, und ein alter Pin hat den Poller schon einmal 300 Sekunden ins Backoff
laufen lassen. Rückfall 2 kommt ohne jede Datei aus und ist der Weg, wenn der
Namensdienst noch nicht durchgereicht ist.

`Erwartete Ausgabe`: `dig +short` liefert genau eine Adresse, und zwar die der
neuen Instanz; `curl` gegen `status.php` antwortet mit HTTP 200 und einem JSON,
das `"installed":true` enthält. Marke: `in Phase 15 erstmals vollzogen`.

### Block 11: Bewaffnung nach DI-05-36

```sh
ssh <box> 'sudo docker exec --user www-data nextcloud-aio-nextcloud \
    php occ app_api:app:disable findling_backend'
ssh <box> 'sudo docker exec --user www-data nextcloud-aio-nextcloud \
    php occ app_api:app:enable findling_backend'
ssh <box> 'docker logs --since 5m nc_app_findling_backend 2>&1 | grep -c "poll"'
```

Nach einem Maschinenstart ist der Container registriert, aber nicht bewaffnet:
er läuft, und der Poller holt sich nichts. Das Paar `disable` und `enable`
stellt die Bewaffnung her.

`Erwartete Ausgabe`: die Zählung im dritten Aufruf ist grösser als null, also
ein GEZÄHLTER Poller-Durchgang im Protokoll. Ein abgelesener Zustand wie
`app_api:app:list` zählt hier ausdrücklich nicht als Beweis; er war schon einmal
grün, während nichts lief. Marke: `in Phase 15 erstmals vollzogen`.

### Block 12: Harte Speichergrenze des Containers

```sh
ssh <box> 'docker update --memory=2g --memory-swap=2g nc_app_findling_backend'
ssh <box> 'docker exec nc_app_findling_backend cat /sys/fs/cgroup/memory.max'
ssh <box> 'docker exec nc_app_findling_backend cat /sys/fs/cgroup/memory.swap.max'
```

Die Grenze wird **aus der cgroup** zurückgelesen und nicht aus der Antwort von
`docker update` oder aus `docker inspect`. Jede Registrierung baut den Container
neu und nimmt die Grenze mit; dieser Block gehört daher hinter Block 11 und
nicht davor.

`Erwartete Ausgabe`: `memory.max` meldet `2147483648`, und `memory.swap.max`
meldet ebenfalls `2147483648`. Jede andere Zahl bedeutet, dass die Messung auf
einer anderen Maschine läuft als v1.1.

### Block 13: Nur EINE Nextcloud auf dem Docker-Dienst

```sh
ssh <box> 'docker ps --format "{{.Names}}" | grep -c nextcloud-aio-nextcloud'
ssh <box> 'docker volume ls --format "{{.Name}}" | grep findling'
```

Diese Zählung steht **vor** dem ersten `--rm-data` und wird unmittelbar davor
wiederholt. Der Volumenname einer ExApp folgt allein aus ihrer App-Kennung: am
07.09.2026 hat eine zweite, frische Nextcloud am selben Docker-Dienst mit
`app_api:app:unregister --rm-data` das Messvolumen der ERSTEN Instanz gelöscht.
Kein Installationslauf, kein Fremdtest, keine zweite Instanz auf dieser
Maschine, solange gemessen wird.

`Erwartete Ausgabe`: die Zählung liefert genau `1`. Liefert sie mehr, wird
nichts weiter getan, bis geklärt ist, welche Instanz die Messinstanz ist.

---

## 5. Zustandspruefung mit Abbruchbedingung

Dies ist der eine Block, der eine Anfahrt beendet, bevor sie nennenswert Geld
kostet. Er steht nach dem Aufbau und vor jeder Messung.

```sh
ssh <box> 'sudo docker exec --user www-data nextcloud-aio-nextcloud \
    php occ findling:index'
ssh <box> 'free -h; nproc; uname -m'
```

Die Abbruchzeile, wörtlich aus
`docs/measurements/2026-09-werkzeugfixe/skripte/00-ablauf.md`, Schritt 2:

> Der Index ist intakt und die Box ist die, gegen die Phase 10 gemessen hat:
> **52.111 indexiert, 37 übersprungen, 0 fehlgeschlagen**, 3.9Gi, 2 Kerne,
> aarch64. Stimmt das nicht, endet die Anfahrt hier.

Die Ablesestellen, jede einzeln:

| Grösse | Ablesestelle | Sollwert |
|---|---|---|
| indexiert | `occ findling:index` | 52.111 |
| übersprungen | `occ findling:index` | 37 |
| fehlgeschlagen | `occ findling:index` | 0 |
| Gesamtspeicher | `free -h` | 3.9Gi |
| Kerne | `nproc` | 2 |
| Rechnerarchitektur | `uname -m` | aarch64 |

`Erwartete Ausgabe`: alle sechs Zeilen stimmen. Weicht eine einzige ab, geht der
Ist-Stand in die Rohdatei des Laufs, die Anfahrt endet, und der Owner
entscheidet neu. Unter einem Deckel dieser Grössenordnung wird kein Index neu
aufgebaut.

### 5.1 Die Resume-Falle, und warum sie ein Abbruchpfad ist

**Der Snapshot trägt den FERTIGEN Index.** Wer ihn einspielt und danach einen
"Volllauf" anstösst, misst einen Resume über rund 52.000 fertige Zeilen und
meldet eine grandiose Verbesserung, die es nie gegeben hat. Der Snapshot ist als
Korpusquelle gedacht, er trägt aber Korpus UND Index.

Der Nullstand wird deshalb **vor** dem Anstoss mit Zahlen belegt, nach dem
Muster von `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/93-nullstand.sh`:
Inhalt des Datenträgers, Zeilenstände in `oc_findling_file_state`, die Marken in
`meta`, die Ausgabe von `occ findling:index`, danach `findling:index --restart -n`
und die Wartefrist.

**Das ist ein Abbruchpfad und keine Empfehlung.** Zeigt die Ablesung nach dem
Zurücksetzen keinen Nullstand, wird nicht angestossen. Das Warnzeichen während
des Laufs ist ein Durchsatz, der in den ersten Minuten unplausibel hoch liegt;
er ist beim v1.1-Lauf auch deshalb eine Untergrenze geblieben, weil beim Anstoss
bereits 1.653 Dateien im Index lagen.

---

## 6. Vergleichbarkeitsbedingungen, protokollpflichtig

Jede der fünf Grössen dieses Abschnitts wird vor dem Lauf **abgelesen** und
nicht erinnert. Ein Lauf, dem eine davon fehlt, gilt als unvollständig: die
Zahlen daneben sind dann nicht falsch, sie sind unbelegt, und für einen
Vergleich ist das dasselbe.

| Groesse | Woher sie kommt | Warum sie protokollpflichtig ist | Sollwert |
|---|---|---|---|
| Zeilenstände der Zustandstabelle (indexiert, übersprungen, fehlgeschlagen) | `occ findling:index`, abgelesen in Abschnitt 5 | Der Snapshot trägt den FERTIGEN Index. Wer ihn einspielt und danach einen "Volllauf" anstösst, misst einen Resume über rund 52.000 fertige Zeilen statt eines Neubaus. Beim v1.1-Anstoss lagen bereits 1.653 Dateien im Index, und genau deshalb ist dessen Durchsatz eine Untergrenze | **52.111** indexiert, **37** übersprungen, **0** fehlgeschlagen |
| Cron-Intervall der Instanz | `./97-cron-vorpruefung.sh vorher`, Pflichtzeile `cron-intervall-ist` | Der Takt stand in v1.1 nominal auf fünf Minuten und lieferte effektiv rund alle zwölf. Das hat 5,85 h von 26,6 h ohne Arbeitsvorrat erzeugt, gegen eine Baseline von 0,10 h | **300** Sekunden, Toleranz zehn Prozent, also 270 bis 330 s |
| Instanztyp und harte Containergrenze | Typ aus `aws_box.sh status`, Grenze aus der cgroup: `memory.max` und `memory.swap.max`, siehe Block 12 | Ein anderer Instanztyp misst eine andere Maschine. Die Speichergrenze geht bei jeder Registrierung verloren, weil sie den Container neu baut; ohne sie läuft die Messung auf einer Maschine, die v1.1 nie hatte | **m7g.large** (D-06) und **2147483648** in beiden cgroup-Feldern |
| Zeit seit dem letzten Containerstart | `docker inspect --format '{{.State.StartedAt}}' nc_app_findling_backend`, dazu der Abstand zur ersten Messung | Der Seitencache des Wirts hat die Kaltstart-Reproduktion vom 10.09.2026 vollständig erklärt: 1.838 ms gegen 1.598 ms, weil der letzte Start einmal 29 h und einmal Minuten zurücklag. Ohne diese Zeile ist eine Kaltstartzahl nicht einzuordnen | kein Sollwert. Abgelesen und protokolliert werden der Zeitstempel und der Abstand in Stunden |
| Werkzeugstand als Baumhash | `40b-baumhash.sh`, es vergleicht das Abbild gegen den Arbeitsbaum und schreibt `rohdaten/40b-baumhash.txt` | Ein korrigiertes Lastwerkzeug macht die v1.1-Stufenzahlen unvergleichbar. Der Baumhash ist der Beweis, der aufgelöste Abbild-Digest nur die Notiz daneben (Befund L-05 der Phase 11) | kein Sollwert. Abgelesen wird `baumhash-gleich` mit dem Hash selbst; steht dort `nein`, hält der Lauf an |

### 6.1 Das Cron-Intervall ist Pflichtfeld

**Drei Zeilen des Konfigurationszweiges gehören in jedes Messprotokoll**, und
sie kommen aus `./97-cron-vorpruefung.sh vorher`: `cron-modus-ist`,
`cron-intervall-quelle` und `cron-intervall-ist`. Die dritte ist die
Pflichtzeile. Fehlt sie, weil keine der drei Quellen den Takt nennen konnte,
endet der Schritt mit Rückgabewert **25**; weicht der gelesene Wert um mehr als
zehn Prozent vom Soll ab, endet er mit **26**.

**Eine Checkliste allein reicht dafür nicht.** Menschliche Schritte werden
vergessen, und genau das war die v1.1-Falle: das Intervall stand in keiner
Ausgabe, also hat niemand bemerkt, dass es nicht stimmte, bis der Lauf vorbei
war. Deshalb ist die Bedingung im Skript durchgesetzt und nicht in diesem
Runbook (D-07, D-08). Dieses Runbook sagt nur, dass sie im Protokoll stehen
muss.

### 6.2 Konfiguration reicht nicht, die Wirkung gehoert dazu

**Sechs Zeilen des Wirkungszweiges gehören daneben**, aus
`./97-cron-vorpruefung.sh waehrend`: `scheiben-erkannt`, `scheibenabstand-min`,
`scheibenabstand-median`, `scheibenabstand-max`, `vorrat-null-in` und
`ablesereihe-intervall`.

**Warum die Konfiguration nicht genügt:** der v1.1-Befund war eine Diskrepanz
zwischen Takt und Wirkung, nominal fünf Minuten gegen effektiv rund zwölf. Ein
Vorprüfschritt, der nur `backgroundjobs_mode`, den Cron-Container oder die
crontab liest, hätte am 10.09.2026 grün gemeldet, während der Befund vorlag.
Gemessen wird deshalb der tatsächliche Abstand zwischen zwei Zulaufscheiben,
mit dem Deckel 420 Sekunden und den Rückgabewerten **27** (keine Zahl) und
**28** (über dem Deckel).

**Das Protokoll muss benennen, WELCHE Ablesereihe die Prozentzahl liefert.** In
v1.1 haben zwei Reihen zwei verschiedene Prozentzahlen für denselben Sachverhalt
erzeugt: 194 von 812 Lesungen in `docs/performance.md` gegen 62 von 325 Lesungen
in der Rohdatei desselben Laufs, also rund 24 gegen 19 Prozent. Welcher Reihe
welcher Beobachter zugrunde liegt, ist plausibel, aber nicht belegt (Annahme
A1). Die Zeile `ablesereihe-intervall` steht genau deshalb neben der Zahl: eine
Prozentzahl ohne ihre Reihe ist Scheingenauigkeit.

### 6.3 Der Korpus und das Lastwerkzeug

**Der Volllauf läuft gegen den Vollkorpus mit 52.111 Dokumenten** (D-04). Er ist
damit direkt vergleichbar mit der v1.0-Baseline und mit dem v1.1-Lauf. Ein
Teilkorpus-Werkzeug gibt es in diesem Milestone ausdrücklich nicht: es würde
Box-Zeit sparen und dafür die einzige Grösse aufgeben, um derentwillen die
Anfahrt stattfindet. Wer Kosten sparen will, kürzt an anderer Stelle.

**Die Zielinstanz bleibt m7g.large** (D-06, ARM). Sie ist die Maschine der
Baseline und des v1.1-Laufs; ARM-Alternativen bei anderen Anbietern sind
weiterhin nicht beschaffbar.

**`scripts/ops/search_load.py` wird nicht mehr angefasst.** Das Lastwerkzeug ist
seit dem 10.09.2026 gefixt und geeicht. Jede weitere Änderung daran macht die
Stufenzahlen dieser Anfahrt gegen die von v1.1 unvergleichbar, und dann misst
die Anfahrt das Werkzeug statt des Erzeugnisses.

---

## 7. Messreihenfolge mit Abbruchpfaden

Die Reihenfolge ist bindend, und jeder Schritt nennt, woran er abbricht. Sie
steht im Gleichschritt mit
`docs/measurements/2026-09-v12-messung/skripte/00-ablauf.md`; dessen fünf
Schrittnummern stehen unten in Klammern.

| Nr | Schritt | Werkzeug | Rohdatei | Abbruchpfad |
|---|---|---|---|---|
| 1 | Zustandsprüfung und Nullstandsbeleg (00-ablauf Schritt 1) | `occ findling:index`, `free -h`, `nproc`, `uname -m`, danach das Muster von `93-nullstand.sh` und `findling:index --restart -n` | `rohdaten/04-bestand-vor-der-messung.txt`, `rohdaten/93-nullstand.txt` | kein Rückgabewert, sondern die Abbruchzeile aus Abschnitt 5: stimmen 52.111 / 37 / 0 / 3.9Gi / 2 / aarch64 nicht, endet die Anfahrt hier. Zeigt die Ablesung nach dem Zurücksetzen keinen Nullstand, wird nicht angestossen |
| 2 | Cron-Konfigurationszweig, vor jedem Messblock (00-ablauf Schritt 2) | `./97-cron-vorpruefung.sh vorher` | `rohdaten/97-cron-vorpruefung-vorher.txt` | **25** keine Quelle lesbar, **26** Intervall weicht vom Soll ab |
| 3 | Bestandsvorlauf der Sonde (00-ablauf Schritt 3) | `73-bestand-sonde.py`, per `docker cp` in den Container, gefahren als Abschnitt 0 von `98c-sprachfaelle.sh` | Abschnitt 0 in `rohdaten/05-sprachfaelle.txt` | **19** die Bestandsmessung im Container konnte nicht fahren. Der Abbruch kommt vor dem Hochladen der 39 Dateien |
| 4 | Anstoss des Volllaufs gegen den Vollkorpus | Muster `96-volllauf.sh` mit dem Beobachter `96b-waechter.sh` | `rohdaten/96-volllauf.csv`, `rohdaten/96b-waechter.txt` | kein eigener Rückgabewert. Der Abbruch dieses Schritts liegt vor ihm, im Nullstandsbeleg von Schritt 1, und neben ihm, im Wirkungszweig von Schritt 5 |
| 5 | Cron-Wirkungszweig, mit dem Volllauf gestartet und neben ihm laufend (00-ablauf Schritt 5) | `./97-cron-vorpruefung.sh waehrend` | `rohdaten/97-cron-vorpruefung-waehrend.txt` | **27** weniger als zwei Scheiben oder keine Zahl, **28** Scheibenabstand über 420 Sekunden |
| 6 | Laststufen 1, 4, 8, 12 und 16, mit je einem Entscheid zu den vier regressiven Stufen (Befund L-04 der Phase 11) | Muster `95-spitze.sh` und `97-nebenlaeufigkeit.sh` über `scripts/ops/search_load.py`, unverändert | `rohdaten/95-*.json`, `rohdaten/95-*.csv` | kein Rückgabewert. Eine Stufe ohne Antwortzahlen wird als solche protokolliert und nicht geschätzt; abgebrochene Aufrufe zählen nicht als beantwortet (DI-10-01) |
| 7 | Sprachfall-Lauf mit Abschnitt 3b (00-ablauf Schritt 4) | `CI_LAUF=<laufnummer> ./98c-sprachfaelle.sh`, mit der zweiten Sondenfahrt nach Upload und Indexierung | `rohdaten/05-sprachfaelle.txt` | **15**, **16**, **17**, **18**, **22**, **23** und **24**, siehe die Tabelle darunter |
| 8 | Wiederaufwärm-Messung der Entladung in vier Ausprägungen, A/B über den MEM-01-Schalter | Muster `95b-kaltstart-reproduktion`, der Schalter selbst entsteht in Phase 14 | `rohdaten/95b-wiederaufwaermen-*.txt` | kein Rückgabewert. Vorbedingung ist die protokollierte Zeit seit dem letzten Containerstart aus Abschnitt 6; ohne sie ist der Vergleich warm gegen kalt unbelegt |
| 9 | Endmessungen und Gegenproben, vor jedem zerstörenden Schritt | Muster `90-bestand.sh` und `96-vektorbestand`, dazu die Kostenzeilen aus `box.env` | `rohdaten/90-bestand.txt`, `rohdaten/96-vektorbestand.txt`, `rohdaten/93-kosten-und-verbleib.txt` | kein Rückgabewert. Dieser Schritt ist die Vorbedingung von Abschnitt 8: was hier nicht erhoben ist, ist nach dem Abbau nicht mehr erhebbar |

**Zur Zählung:** `00-ablauf.md` nummeriert die fünf Schritte, die die zwei
Messwerkzeuge und die eine Messbedingung beweisen. Diese Tabelle nummeriert die
Anfahrt als Ganzes und ordnet nach dem Zeitpunkt des Starts. Deshalb steht der
Wirkungszweig hier vor dem Sprachfall-Lauf: beide laufen neben dem Volllauf,
aber der Wirkungszweig wird mit ihm gestartet. Werkzeuge, Rohdateien und
Rückgabewerte sind in beiden Dateien dieselben.

### 7.1 Die Rueckgabewerte, vollstaendig

| Bedingung | Wo sie greift | Folge |
|---|---|---|
| Der Upload hat nicht 39 Dateien geliefert | Schritt 7 | Rückgabewert 15 (unvollständiger Upload) |
| Der Arbeitsvorrat war am Rundendeckel noch nicht leer | Schritt 7 | Rückgabewert 16 für den nicht geleerten Vorrat. Die Fälle 8 bis 10 hängen an der OCR-Spur; dieser Block ist abbrechbar und keine Vorbedingung des Berichts |
| Mindestens ein MESSBARER Fall war rot | Schritt 7 | Rückgabewert 17 für den roten Fall. Nicht messbare Fälle zählen hier ausdrücklich nicht mit |
| `jq` liegt nicht auf dieser Box | Schritt 7 | Rückgabewert 18 für das fehlende Werkzeug. Die Vorbedingung dazu steht in Abschnitt 3, Zeile 7, weil dieser Abbruch sonst in der bezahlten Zeit fällt |
| Die Vorprüfung des Fremdbestands konnte nicht gefahren werden | Schritt 3, Abschnitt 0 des Skripts | Rückgabewert 19 für die nicht gefahrene Sonde. Der Abbruch kommt vor dem Hochladen der 39 Dateien |
| `CI_LAUF` trägt keine Laufnummer | Schritt 7, vor dem ersten Fall | Rückgabewert 22 für die fehlende Laufnummer. Die Vorbedingung dazu steht in Abschnitt 3, Zeile 1 |
| Kein einziger Fall war messbar | Schritt 7 | Rückgabewert 23 für den durchweg nicht messbaren Lauf. Ein Lauf, in dem jeder Begriff im Fremdbestand ertrinkt, ist eine Aussage über die Instanz und keine über die Sprachkette |
| Abschnitt 3b konnte keine Datei-Kennungen erheben | Schritt 7, zwischen Indexierung und Fällen | Rückgabewert 24 für die fehlenden Ränge. Ohne sie hiessen alle zehn Fälle nicht messbar, und zwar aus dem falschen Grund |
| Die Cron-Konfiguration war auf keiner bekannten Quelle lesbar | Schritt 2, unterhalb der Pipeline | Rückgabewert 25 für das unlesbare Intervall. Ein Lauf ohne protokolliertes Intervall gilt als unvollständig (D-07) |
| Das gelesene Intervall weicht vom Soll ab | Schritt 2, unterhalb der Pipeline | Rückgabewert 26 für die verfehlte Messbedingung. Sie ist dann nicht hergestellt, und der Laufzeitvergleich wäre unbelegt |
| Der Wirkungszweig wurde nicht gefahren oder nicht protokolliert | Schritt 5, unterhalb der Pipeline | Rückgabewert 27 für den Zweig ohne Zahl. Weniger als zwei erkannte Scheiben ergeben keinen Abstand, und ein Wirkungszweig ohne Zahl ist kein Protokoll |
| Der gemessene Scheibenabstand liegt ueber dem Deckel | Schritt 5, unterhalb der Pipeline | Rückgabewert 28 für den gerissenen Deckel von 420 Sekunden. Das ist ein Befund und keine Störung: die Anfahrt hält hier, statt eine unvergleichbare Laufzeit zu erzeugen |

Alle vier neuen Abbrüche stehen **unterhalb** der `tee`-Pipeline ihres Skripts:
der Rückgabewert einer Pipeline gehört zu `tee`, und ein Abbruch innerhalb des
Blocks verliesse nur die Subshell. Die Verweigerung wäre dann eine Zeile in
einer Rohdatei, die niemand liest.

**Während der bezahlten Anfahrt wird kein Werkzeug mehr geändert.** Ein Skript,
das während seines eigenen Laufs nachgebessert wird, macht jede Zahl daneben
unbelegt. Fällt ein Werkzeug auf, wird der Befund notiert und der Lauf zu Ende
gefahren oder abgebrochen; die Korrektur gehört in die Zeit nach dem Abbau.
