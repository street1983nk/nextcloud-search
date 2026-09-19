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
| **NEU: Abbildwechsel auf den v1.2-Stand** (Pull per Digest, PHP-Hälfte, Registrierung, harte Grenze, Baumhash) | **1 h 00 min** | Muster `92-wechsel.sh`, geschätzt; Annahme A2 der Phasenrecherche. Im Rechenblatt des Standes vom 16.09.2026 fehlte dieser Posten vollständig | |
| Volllauf beide Spuren bis zum letzten Vektor | **26 h 37 min** | v1.1, Abschnitt 7 des Berichts, gemessen | |
| **NEU: MEM-02-Block** (Grundlast vor und nach dem Indexlauf, Freigabe abwarten, `rss_sampler`) | **0 h 45 min** | MEM-02 ist in keiner Zeile des bisherigen Rechenblatts enthalten, Annahme A3 der Phasenrecherche | |
| Untersuchung der vier regressiven Laststufen, je ein Entscheid | 1 h 30 min | neu in v1.2, geschätzt | |
| **NEU: Filter- und Sortierblock** (Sortierung auf grossem Bestand, Blättern unter Filter) | **1 h 30 min** | Owner-Entscheid vom 19.09.2026 (D-01, `15-CONTEXT.md`), der 1 bis 2 h nennt; als Planwert gilt die Mitte | |
| Wiederaufwärm-Messung der Entladung in vier Ausprägungen (warm und kalt, je mit und ohne Seitencache) | 2 h 00 min | neu in v1.2, geschätzt | |
| Sprachfall-Messung mit der neuen Messgrösse, inklusive Erstvollzug des Skripts | 1 h 00 min | neu in v1.2, geschätzt | |
| Abbau und Endmessungen (Gegenproben vor dem Abbau, Snapshot, `destroy`, Tag-Sweep) | 1 h 00 min | v1.1 Abschnitt 17 und der Abbaulauf vom 11.09.2026 | |
| **Summe der Planwerte** | **39 h 22 min** | Addition der zehn Zeilen darüber: 2:30 + 1:30 + 1:00 + 26:37 + 0:45 + 1:30 + 1:30 + 2:00 + 1:00 + 1:00 = 2.362 Minuten | |

**Der Planwert des Volllaufs nimmt keine Verbesserung vorweg.** Ob der
Top-up-Fix den Lauf verkürzt, ist genau die Frage, die dieser Lauf beantworten
soll. Als Planwert gilt deshalb 26 h 37 min und nicht ein erhoffter kleinerer
Wert. Genau dieser Fehler hat den Deckel des v1.1-Laufs gerissen: geplant waren
rund 19 Stunden, gebraucht wurden 26 h 37 min.

**Die verkürzte Ruhezeit kürzt den Deckel nicht.** Der Owner hat am 19.09.2026
entschieden, dass die Entlade-Messungen des Schrittes 8 die Frist klein stellen,
also 60 bis 120 Sekunden statt der 900 Sekunden des Vorschlagswerts (D-02,
`15-CONTEXT.md`). Der Planwert der Wiederaufwärm-Messung bleibt trotzdem bei
2 h 00 min. Ein Planwert, der eine Verbesserung vorwegnimmt, ist genau der
Fehler, der den v1.1-Deckel gerissen hat; die gesparte Wartezeit ist deshalb
ausgewiesene Reserve und kein gekürzter Posten.

**Die Verkürzung ist eine begründungspflichtige Abweichung und keine stille
Praxis.** Sie wird im Protokoll mit ihrem Grund genannt, und der Grund ist
derselbe Mechanismus bei einem Bruchteil der Box-Zeit: gemessen wird, was nach
Ablauf der Frist geschieht, und nicht, wie lang die Frist ist. Der
Vorschlagswert 900 s selbst bleibt anderswo eine gekennzeichnete Schätzung
(Owner-Entscheid aus 14-12). Dieser Lauf belegt ihn nicht und widerlegt ihn
nicht, und ein Protokoll, das die Abweichung ohne ihren Grund führt, macht aus
einem Entscheid eine Gewohnheit.

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

**Die Sätze sind vom 04.09.2026 und werden am Anfahrtstag ein zweites Mal
gelesen**, wieder über `scripts/ops/aws_box.sh prices`. Das kostet keine
Box-Minute und keinen Cent: der einzige API-Aufruf dieses Unterbefehls ist
`describe-instance-types`, und der ist kostenlos (Annahme A1 der
Phasenrecherche). Die gepinnten Werte selbst bleiben bis dahin unverändert.
Weicht die zweite Lesung ab, geht die Abweichung in die Rohdatei des Laufs, und
der Deckel wird vor der ersten Kommandozeile neu gerechnet statt nachträglich
erklärt.

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
39,37 h x 1,15 = 45,27 h, aufgerundet 46 h
46 h x 0,115841 USD/h = 5,3287 USD, aufgerundet 5,40 USD
```

**Empfehlung für Phase 15: 46 Stunden und 5,40 USD netto.** Die Untergrenze ist
unverändert 31 h und 3,59 USD, weil genau so viel der v1.1-Lauf mit weniger
Arbeitsumfang verbraucht hat; ein Vorschlag darunter ist rechnerisch schon
gerissen, bevor er ausgesprochen ist.

| Stand | Stunden | USD netto | Was darin steckt |
|---|---:|---:|---|
| Untergrenze | 31 h | 3,59 USD | der Verbrauch des v1.1-Laufs bei kleinerem Arbeitsumfang |
| Vorgängerstand (16.09.2026) | 42 h | 4,90 USD | ohne Abbildwechsel, ohne MEM-02-Block, ohne Filter- und Sortierblock |
| **Empfehlung (19.09.2026)** | **46 h** | **5,40 USD** | mit allen drei Nachtragsposten aus 2.1 |

**Der Vorgängerstand bleibt stehen.** Eine Zahl, die über Nacht von 42 auf 46
wächst und deren Vorgänger gelöscht ist, sieht aus wie ein Aufschlag. Die
Differenz von vier Stunden ist keiner: sie ist die Summe dreier Posten, die die
Anfahrt ohnehin fährt und die im alten Rechenblatt schlicht fehlten. Wer die
Zahl prüft, liest die drei Zeilen mit der Marke **NEU** in 2.1 und rechnet die
Summe nach.

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

**Nachtrag: `dig` liegt auf der Entwicklungsmaschine nicht vor.** Die erste Zeile
dieses Blocks läuft dort ins Leere, und zwar mit "command not found" statt mit
einer leeren Antwort, was zwei sehr verschiedene Dinge sind. Die Rückfälle sind
`nslookup loadtest.infranode.dev` und `curl --resolve` aus dem Block oben; beide
sind vorhanden. Auf der Box selbst wird geprüft, was dort auch liegt. Der Befund
gehört in Abschnitt 3 und nicht in die bezahlte Zeit: ein fehlendes Werkzeug,
das erst auf der Box auffällt, kostet Box-Minuten für eine Installation.

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

### Block 13b: Abbildwechsel auf den v1.2-Stand

**Warum dieser Block existiert.** Der Snapshot trägt die lokale Registry der Box
mit dem Abbild vom 10.09.2026. Ein Volllauf gegen dieses Abbild misst einen
Container **ohne Top-up-Route, ohne die Filter aus Phase 13 und ohne den
Entladeschalter aus Phase 14**. Erfolgskriterium 2 dieser Phase wäre damit
unerfüllbar, weil das alte Abbild genau den Fix nicht kennt, dessen Wirkung
belegt werden soll, und Erfolgskriterium 5 ebenso, weil es den MEM-01-Schalter
misst, den nur der neue Stand trägt. Block 8 prüft heute allein, dass die
Registry aus dem Snapshot antwortet, und nicht, welchen Stand sie führt. Dieser
Block schliesst die Lücke, und er schliesst sie **vor** der Zustandsprüfung aus
Abschnitt 5.

**Was gewechselt wird** (D-04, `15-CONTEXT.md`): das aktuelle
Multi-arch-Release-Abbild des Phase-14-Abschlusses, **per Digest gezogen und
nicht über den Zeiger `:dev`**. `:dev` wandert, jeder grüne Lauf der
Abbildstrecke schiebt ihn weiter, und ein Bericht, der ihn nennt, nennt keinen
Stand. Der aufgelöste Digest wird im Protokoll genannt; der Beweis der
Identität bleibt der Baumhash aus Abschnitt 6 und nicht der Digest.

```sh
# auf der Box, im Laufverzeichnis der Anfahrt
cd <checkout>/docs/measurements/2026-09-v12-messung/skripte
ABBILD_DIGEST="sha256:<digest>" ./92b-wechsel.sh
```

`<digest>` sind die 64 Hexziffern des Release-Abbilds des Phase-14-Abschlusses;
sie werden vor der Anfahrt aus der Abbildstrecke abgelesen und stehen als Zeile
in der Rohdatei, nicht in dieser Datei. `<checkout>` ist der Arbeitsbaum auf der
Box aus Block 9.

`ABBILD_DIGEST` ist die **einzige Pflichtangabe** und hat mit Absicht keinen
Vorgabewert: fehlt sie oder ist sie leer, endet das Werkzeug mit **2** und der
Benutzung auf stderr, bevor eine Rohdatei entsteht. Das Abbild selbst wird
daraus zusammengesetzt (`ABBILD_REPO@ABBILD_DIGEST`) und ist deshalb keine
zweite Stellschraube: ein eigenes `IMAGE` neben einem eigenen Digest wäre genau
der Fall, in dem der Baumhash ein anderes Abbild prüft als die Registrierung
darunter fährt.

**Die Abhängigkeitskette ist nicht frei wählbar**, und sie steht wörtlich im
Kopf von `92b-wechsel.sh`:

1. **Zuerst die PHP-Hälfte.** Ihr Verzeichnis unter `custom_apps` **muss**
   `findling` heissen. Unter jedem anderen Namen findet der Klassenlader nichts,
   der Suchanbieter bleibt unsichtbar, und es gibt **nirgends** eine
   Fehlermeldung, die das sagt.
2. **Danach die Registrierung** der ExApp. Sie baut den Container neu.
3. **Danach die harte Grenze**, weil die Registrierung sie wegwirft. Sie wird
   **aus der cgroup** zurückgelesen und nicht aus der Antwort von `docker update`
   oder aus `docker inspect`, mit **2147483648** in beiden Feldern
   (`memory.max` und `memory.swap.max`), wie in Block 12.
4. **Daneben die Stellung des Entladeschalters**, die aus demselben Grund
   verloren geht: `FINDLING_EMBED_IDLE_RELEASE_SECONDS` reist als
   Umgebungsvariable der ExApp und wird nach der Registrierung neu abgelesen,
   nach der Pflichtzeile aus Abschnitt 6.4. Für den Wirkungsbeleg steht sie auf
   `0`.

**`unregister --rm-data` läuft vor dem Indexaufbau und nie danach**, und nie
ohne die Zählung der laufenden Nextcloud-Instanzen unmittelbar davor (Block 13).
Der Volumenname einer ExApp folgt allein aus ihrer App-Kennung: am 07.09.2026
hat eine zweite Nextcloud am selben Docker-Dienst mit diesem Schalter das
Messvolumen der ersten gelöscht. Nach dem Indexaufbau ist derselbe Schalter der
Verlust des Messgegenstands.

**Das Werkzeug** ist `92b-wechsel.sh` im Laufverzeichnis
`docs/measurements/2026-09-v12-messung/skripte/`, seine Rohdatei ist
`rohdaten/92b-wechsel.txt`, und es bricht mit fünf eigenen Rückgabewerten ab:

| Wert | Bedingung |
|---|---|
| **2** | `ABBILD_DIGEST` fehlt, ist leer oder trägt nicht die Gestalt `sha256:<hex>`, oder das Werkzeug wurde mit einem Argument gerufen |
| **36** | der Baumhash fehlt, ist nicht dreifach verankert oder meldet `baumhash-gleich nein`; **oder** der Container läuft nach der Registrierung auf einer anderen Abbildkennung als der geprüften |
| **37** | mehr als eine Nextcloud läuft an diesem Docker-Dienst, oder die Zählung war nicht lesbar |
| **38** | der Arbeitsbaum ist nicht sauber |
| **39** | die harte Grenze hat nicht gegriffen, die cgroup meldet nicht 2147483648 |

Der zweite Fall von **36** ist der Preis dafür, dass AppAPI
`registry/image:tag` zusammensetzt und keinen Digest kennt: registriert wird
über einen Tag, und ein Tag ist wieder ein wandernder Zeiger. Das Werkzeug legt
das per Digest gezogene Abbild vorher lokal auf genau diesen Tag und liest nach
der Registrierung die Abbildkennung **aus dem Container** zurück. Weichen die
beiden ab, misst der Lauf einen anderen Stand als den geprüften, und das ist
derselbe unbelegte Stand wie ein fehlender Baumhash.

`Erwartete Ausgabe`: der aufgelöste Digest steht in der Rohdatei, das
PHP-Verzeichnis heisst `findling` und ist eingeschaltet, beide cgroup-Felder
melden `2147483648`, und `40b-baumhash.sh` meldet `baumhash-gleich ja`. Marke:
`in Phase 15 erstmals vollzogen`.

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

Jede der sechs Grössen dieses Abschnitts wird vor dem Lauf **abgelesen** und
nicht erinnert. Ein Lauf, dem eine davon fehlt, gilt als unvollständig: die
Zahlen daneben sind dann nicht falsch, sie sind unbelegt, und für einen
Vergleich ist das dasselbe.

| Groesse | Woher sie kommt | Warum sie protokollpflichtig ist | Sollwert |
|---|---|---|---|
| Zeilenstände der Zustandstabelle (indexiert, übersprungen, fehlgeschlagen) | `occ findling:index`, abgelesen in Abschnitt 5 | Der Snapshot trägt den FERTIGEN Index. Wer ihn einspielt und danach einen "Volllauf" anstösst, misst einen Resume über rund 52.000 fertige Zeilen statt eines Neubaus. Beim v1.1-Anstoss lagen bereits 1.653 Dateien im Index, und genau deshalb ist dessen Durchsatz eine Untergrenze | **52.111** indexiert, **37** übersprungen, **0** fehlgeschlagen |
| Cron-Intervall der Instanz | `./97-cron-vorpruefung.sh vorher`, Pflichtzeile `cron-intervall-ist` | Der Takt stand in v1.1 nominal auf fünf Minuten und lieferte effektiv rund alle zwölf. Das hat 5,85 h von 26,6 h ohne Arbeitsvorrat erzeugt, gegen eine Baseline von 0,10 h | **300** Sekunden, Toleranz zehn Prozent, also 270 bis 330 s |
| Instanztyp und harte Containergrenze | Typ aus `aws_box.sh status`, Grenze aus der cgroup: `memory.max` und `memory.swap.max`, siehe Block 12 | Ein anderer Instanztyp misst eine andere Maschine. Die Speichergrenze geht bei jeder Registrierung verloren, weil sie den Container neu baut; ohne sie läuft die Messung auf einer Maschine, die v1.1 nie hatte | **m7g.large** (D-06) und **2147483648** in beiden cgroup-Feldern |
| Zeit seit dem letzten Containerstart | `docker inspect --format '{{.State.StartedAt}}' nc_app_findling_backend`, dazu der Abstand zur ersten Messung | Der Seitencache des Wirts hat die Kaltstart-Reproduktion vom 10.09.2026 vollständig erklärt: 1.838 ms gegen 1.598 ms, weil der letzte Start einmal 29 h und einmal Minuten zurücklag. Ohne diese Zeile ist eine Kaltstartzahl nicht einzuordnen | kein Sollwert. Abgelesen und protokolliert werden der Zeitstempel und der Abstand in Stunden |
| Werkzeugstand als Baumhash | `40b-baumhash.sh`, es vergleicht das Abbild gegen den Arbeitsbaum und schreibt `rohdaten/40b-baumhash.txt` | Ein korrigiertes Lastwerkzeug macht die v1.1-Stufenzahlen unvergleichbar. Der Baumhash ist der Beweis, der aufgelöste Abbild-Digest nur die Notiz daneben (Befund L-05 der Phase 11). Das gilt auch für den Digest des Abbildwechsels aus Block 13b: er wird protokolliert, aber er belegt nichts, weil der Pfadfilter der Abbildstrecke bis in `backend/**` reicht und schon ein neuer Testdatei-Commit den Digest bewegt, ohne eine Zeile des Abbilds zu ändern | kein Sollwert. Abgelesen wird `baumhash-gleich` mit dem Hash selbst; steht dort `nein`, hält der Lauf an |
| Stellung des Entladeschalters `FINDLING_EMBED_IDLE_RELEASE_SECONDS` | aus der Umgebung des Containers: `docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' nc_app_findling_backend`, gefiltert auf den Variablennamen, je Messschritt neu abgelesen | Die A/B-Messung der Wiederaufwärm-Kosten aus Schritt 8 ist genau der Vergleich zweier Stellungen dieser Variablen. Eine Zahl ohne ihre Stellung ist keine Hälfte des Vergleichs, weil sie nicht sagt, zu welchem Ast sie gehört. Die Stellung geht ausserdem bei jeder Registrierung verloren, wie die harte Speichergrenze | kein Sollwert. Abgelesen wird der Wert je Messschritt; die Schritte 1 bis 7 und 9 laufen auf **0**, Schritt 8 fährt beide Stellungen |

**Der Abbildwechsel und `baumhash-gleich` widersprechen sich nicht.** Gewechselt
wird **einmal**, in Block 13b, vor der ersten Messung, und dieser eine Vorgang
ist genau der, der `baumhash-gleich ja` überhaupt erst herstellt: er bringt das
Abbild der Box auf den Stand des Arbeitsbaums. Ab der ersten Messung gilt die
Bedingung dieser Tabelle wieder unverändert. Steht dort später `nein`, hält der
Lauf an. Die Reihenfolge lautet also: **wechseln, Baumhash lesen, messen**, und
nur in dieser Richtung. Ein Abbildwechsel während der laufenden Messreihe ist
kein Nachtrag, sondern ein zweiter Messgegenstand unter dem Namen des ersten;
die Zahlen davor und danach gehören dann in zwei Berichte und nicht in eine
Spalte.

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

### 6.4 Die Stellung des Entladeschalters ist Pflichtfeld

**Eine Zeile je Messschritt**, mit dem Namen der Variablen und ihrem Wert, nach
dem Muster der Pflichtzeile `cron-intervall-ist` aus 6.1:
`entladeschalter-ist=<sekunden>`. Fehlt sie für einen Messschritt, gilt der Lauf
als unvollständig, und zwar nach derselben Regel wie ein Lauf ohne
Cron-Intervall: die Zahlen daneben sind dann nicht falsch, sie sind unbelegt.

**Warum das eine Pflichtzeile ist und keine Bemerkung.** Seit MEM-01 entscheidet
diese eine Variable, ob der Container die Gewichte im Leerlauf freigibt. Die
A/B-Messung der Wiederaufwärm-Kosten aus Schritt 8 ist genau der Vergleich
zweier Stellungen dieser Variablen. Zwei Zahlen mit ihren Stellungen sind ein
Vergleich; zwei Zahlen ohne sie sind zwei Zahlen, und keine davon ist die Hälfte
des Vergleichs, weil keine sagt, zu welchem Ast sie gehört.

**Der Fehler wäre auch nicht sichtbar.** Ein Container mit eingeschaltetem
Schalter antwortet auf jede Suche mit HTTP 200. Er antwortet nach einer
Ruhephase nur ohne semantische Seite, und das steht in den Trefferzahlen und
nicht in der Fehlerspalte. Eine falsch erinnerte Stellung fällt in keiner
Fehlerzeile auf, sondern erst beim Auswerten, wenn die Box abgebaut ist.

**Die Stellung geht bei jeder Registrierung verloren.** Sie reist als
Umgebungsvariable der ExApp, und jede Registrierung baut den Container neu,
genau wie bei der harten Speichergrenze aus Block 12. Nach jeder Registrierung
wird sie deshalb neu abgelesen und nicht erinnert.

**Der Messcontainer des `one_load`-Gates hat den Schalter auf `0`.** Das
Werkzeug `findling.tools.one_load` gibt in seiner vierten Phase selbst frei und
lädt über eine zweite echte Suchrunde nach. Steht der Schalter in diesem
Container auf einem Wert ungleich `0`, weist `query_may_load()` die zweite Runde
zurück, das warme Fenster zeigt null Ladevorgänge, und das Werkzeug meldet einen
Befund, den es nicht gibt. Für diesen einen Lauf gilt `0` und nichts sonst.

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
| 6b | Filter- und Sortierblock: Sortierung auf grossem Bestand, Blättern unter Filter (D-01, Owner-Entscheid vom 19.09.2026) | `99c-filter-sortierung.sh` | `rohdaten/99c-filter-sortierung.txt` | **34** und **35**, siehe die Tabelle in 7.1 |
| 7 | Sprachfall-Lauf mit Abschnitt 3b (00-ablauf Schritt 4) | `CI_LAUF=<laufnummer> ./98c-sprachfaelle.sh`, mit der zweiten Sondenfahrt nach Upload und Indexierung | `rohdaten/05-sprachfaelle.txt` | **15**, **16**, **17**, **18**, **22**, **23** und **24**, siehe die Tabelle darunter |
| 8 | Wiederaufwärm-Kosten, A/B über den MEM-01-Schalter, in vier Ausprägungen (Abschnitt 7.2) | `95b-wiederaufwaermen.sh`; der Schalter steht seit Phase 14, und `95b-kaltstart-reproduktion` ist die Herkunft des Musters, eine Rohdatei von Hand und kein Werkzeug | `rohdaten/95b-wiederaufwaermen-*.txt` | **29**, **30** und **31**, siehe Abschnitt 7.2. Vorbedingung bleibt die protokollierte Zeit seit dem letzten Containerstart aus Abschnitt 6; ohne sie ist der Vergleich warm gegen kalt unbelegt |
| 8b | MEM-02: Rückkehr zur Grundlast nach einem Indexlauf, Grundlast vor und nach dem Lauf, Freigabe abgewartet | `94b-grundlast-rueckkehr.sh` über `scripts/ops/rss_sampler.sh` und `scripts/ops/rss_digest.py` | `rohdaten/94b-grundlast-rueckkehr.txt` | **31**, **32** und **33**, siehe die Tabelle in 7.1 |
| 9 | Endmessungen und Gegenproben, vor jedem zerstörenden Schritt | Muster `90-bestand.sh` und `96-vektorbestand`, dazu die Kostenzeilen aus `box.env` | `rohdaten/90-bestand.txt`, `rohdaten/96-vektorbestand.txt`, `rohdaten/93-kosten-und-verbleib.txt` | kein Rückgabewert. Dieser Schritt ist die Vorbedingung von Abschnitt 8: was hier nicht erhoben ist, ist nach dem Abbau nicht mehr erhebbar |

**Zur Zählung:** `00-ablauf.md` nummeriert die fünf Schritte, die die zwei
Messwerkzeuge und die eine Messbedingung beweisen. Diese Tabelle nummeriert die
Anfahrt als Ganzes und ordnet nach dem Zeitpunkt des Starts. Deshalb steht der
Wirkungszweig hier vor dem Sprachfall-Lauf: beide laufen neben dem Volllauf,
aber der Wirkungszweig wird mit ihm gestartet. Werkzeuge, Rohdateien und
Rückgabewerte sind in beiden Dateien dieselben.

**Warum 6b dort steht, wo es steht.** Der Filter- und Sortierblock misst gegen
den vollen Bestand, genau wie die Laststufen, und er findet den Container von
ihnen bereits aufgewärmt vor. Vor Schritt 6 gefahren, kostete er eine zweite
Aufwärmung und mässe einen anderen Bestand als die Stufen daneben.

**Warum 8b hinter 8 steht.** Der MEM-02-Block wartet auf eine Freigabe. Schritt
8 stellt die Frist ohnehin klein und fährt beide Stellungen des Schalters; 8b
setzt darauf auf, statt eine zweite Ruhephase zu bezahlen. Seine Messgrösse ist
`Rückkehr zur Grundlast nach einem Indexlauf` und ausdrücklich nicht "Grundlast
minus X": gefragt ist, ob beide Speicherhalter nach Ablauf der Frist wieder frei
sind, und nicht, um wie viel eine Zahl gefallen ist.

**Die Nummern der Rückgabewerte folgen dem Katalog und nicht der Reihenfolge.**
6b bricht mit 34 und 35 ab, 8b mit 31 bis 33, obwohl 6b zuerst läuft. Die Werte
sind in der Reihenfolge vergeben, in der die Werkzeuge entstanden sind, und eine
einmal vergebene Zahl wird nicht umgehängt: eine Rohdatei aus einem früheren
Lauf soll auch später noch lesbar bleiben.

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
| Die Grundlast vor dem Indexlauf wurde nicht abgetastet | Schritt 8b, vor dem Anstoss | Rückgabewert **32** für den fehlenden Bezugswert. Eine Rückkehr ohne den Wert, zu dem zurückgekehrt wird, ist keine Messgrösse, sondern eine Zahl |
| Der Container wurde zwischen den beiden Abtastungen neu gebaut | Schritt 8b, zwischen den Abtastungen | Rückgabewert **33** für die unterbrochene Reihe. Ein neu gebauter Container startet auf seiner Grundlast, und die Differenz beider Abtastungen wäre dann ein Neustart und keine Freigabe |
| Die Sortierung lief gegen einen Bestand, der noch wuchs | Schritt 6b, vor der ersten Stufe | Rückgabewert **34** für den unfertigen Bestand. Die Endzahl des Volllaufs muss stehen, sonst misst die Sortierung zwei verschiedene Bestände unter einer Zahl |
| Eine Filter- oder Sortierstufe lieferte keine Antwortzahlen, oder zwei aufeinander folgende Seiten trugen dieselbe Datei-Kennung | Schritt 6b | Rückgabewert **35** für die unbrauchbare Stufe. Ein Blättern, das eine Kennung zweimal ausliefert, ist ein Befund über die Seitenroute und keine Sortierzahl |
| Der Baumhash fehlt, ist nicht dreifach verankert oder meldet `baumhash-gleich nein`, oder der Container läuft nach der Registrierung auf einer anderen Abbildkennung als der geprüften | Block 13b, vor der ersten Messung und noch einmal unmittelbar danach | Rückgabewert **36** für den unbelegten Stand. Jede Zahl danach gehörte zu einem Zustand, den niemand benennen kann |
| Mehr als eine Nextcloud läuft an diesem Docker-Dienst | Block 13b, vor `unregister --rm-data` | Rückgabewert **37** für die zweite Instanz. Der Volumenname folgt allein aus der App-Kennung; am 07.09.2026 hat genau das ein Messvolumen gekostet |
| Der Arbeitsbaum auf der Box ist nicht sauber | Block 13b, vor dem Pull | Rückgabewert **38** für den veränderten Baum. Ein Baumhash gegen einen veränderten Arbeitsbaum belegt nichts |
| Die harte Grenze hat die Registrierung nicht überlebt | Block 13b, nach der Registrierung | Rückgabewert **39** für die verfehlte Grenze. Gelesen wird aus der cgroup, erwartet werden 2147483648 in beiden Feldern; jede andere Zahl misst eine andere Maschine als v1.1 |

Alle vier neuen Abbrüche stehen **unterhalb** der `tee`-Pipeline ihres Skripts:
der Rückgabewert einer Pipeline gehört zu `tee`, und ein Abbruch innerhalb des
Blocks verliesse nur die Subshell. Die Verweigerung wäre dann eine Zeile in
einer Rohdatei, die niemand liest.

**Während der bezahlten Anfahrt wird kein Werkzeug mehr geändert.** Ein Skript,
das während seines eigenen Laufs nachgebessert wird, macht jede Zahl daneben
unbelegt. Fällt ein Werkzeug auf, wird der Befund notiert und der Lauf zu Ende
gefahren oder abgebrochen; die Korrektur gehört in die Zeit nach dem Abbau.

### 7.2 Der Messschritt Wiederaufwaerm-Kosten, A/B

Der Schritt 8 dieser Tabelle misst, was die Entladung aus MEM-01 an
Nachladezeit kostet, und er misst es als Vergleich zweier Stellungen des
Schalters. Vier Ausprägungen, und die Reihenfolge ist bindend, weil jede
Messung den Seitencache des Wirts wärmt und eine einmal gewärmte Kaltmessung
nicht wiederholbar ist, ohne den Cache erneut zu leeren:

| Nr | `FINDLING_EMBED_IDLE_RELEASE_SECONDS` | Seitencache | Was gemessen wird |
|---|---|---|---|
| 1 | Vorschlagswert | kalt, Cache des Wirts vorher geleert | die Ruhezeit wird abgewartet, dann eine Suche: die Antwortzeit der degradierten Suche und die Dauer des Nachwärmens daneben |
| 2 | Vorschlagswert | warm | dieselbe Messung, die Ruhezeit erneut abgewartet, ohne Leeren des Caches |
| 3 | `0` | kalt, Cache des Wirts vorher geleert | der Bezugswert ohne Entladung, nach dem Muster `95b-kaltstart-reproduktion` |
| 4 | `0` | warm | derselbe Bezugswert ohne Leeren des Caches |

Der Vorschlagswert kommt aus der Beschreibung der Variablen in
`backend/appinfo/info.xml` und wird im Protokoll mit seinem Wert genannt, nicht
mit dem Wort. Jeder Wechsel der Stellung baut den Container neu: danach werden
die harte Speichergrenze aus Block 12 und die Pflichtzeile aus 6.4 neu
abgelesen, beide, und nicht erinnert.

**Die Frist dieser Messung ist verkürzt** (D-02, Owner-Entscheid vom
19.09.2026): die Ausprägungen 1 und 2 stellen
`FINDLING_EMBED_IDLE_RELEASE_SECONDS` auf 60 bis 120 Sekunden statt auf den
Vorschlagswert 900 s. Gemessen wird, was nach Ablauf der Frist geschieht, und
nicht, wie lang die Frist ist; der Mechanismus ist derselbe, und die Ersparnis
sind Stunden Box-Zeit. Die Abweichung vom Vorschlagswert wird im Protokoll **mit
ihrem Grund** genannt, und der Vorschlagswert 900 s bleibt anderswo eine
gekennzeichnete Schätzung. Der Wert, der tatsächlich stand, steht in der
Pflichtzeile aus 6.4.

**Was "kalt" heisst, als Befehl.** Zwei der vier Ausprägungen verlangen einen
geleerten Seitencache des Wirts. Gemeint ist genau das hier, **auf dem Wirt und
nicht im Container**:

```sh
sync
echo 3 | sudo tee /proc/sys/vm/drop_caches
free -h
```

`sync` schreibt die schmutzigen Seiten zurück, damit nichts Ungeschriebenes
verworfen wird; der Wert `3` verwirft Seitencache, Dentries und Inodes; `free -h`
ist die Rückleseprobe, und ihre Ausgabe gehört in die Rohdatei. Im Container
gefahren tut derselbe Befehl entweder nichts oder etwas anderes: `/proc/sys` ist
dort nicht beschreibbar, und der Cache, um den es geht, gehört ohnehin dem Wirt.

**Die Nebenwirkung, im Klartext.** Das Leeren verwirft auch den mmap-Cache des
Tantivy-Index. Die kalte Suche misst damit **beide Hälften kalt**, die Semantik
und den Volltext, und nicht allein das Nachladen der Gewichte. Das ist die
gewollte schlechtere Hälfte der Wahrheit: sie ist der Fall, den ein Nutzer nach
einem Neustart der Box wirklich bekommt. Sie muss im Bericht dastehen, sonst
liest sich eine Zahl als Wiederaufwärmkosten, die zum Teil Indexkosten sind.

**Die Warnschwelle.** Unterscheiden sich zwei Kaltmessungen um mehr als fünf
Prozent, ist die Bedingung nicht hergestellt. Dann wird nicht gemittelt und nicht
weitergefahren, sondern der Cache erneut geleert und die Messung wiederholt. Das
Rauschband dieser Box liegt unter fünf Prozent; alles darüber ist ein Zustand
und kein Rauschen.

**Kalt wird hergestellt und nicht bewahrt.** Die Bestandssonde (Schritt 3) fährt
über die Diagnose-Route und wärmt den Container, und die Laststufen (Schritt 6)
laden das Modell absichtlich vor der Reihe. Beide liegen vor Schritt 8, und
beide sind nicht verschiebbar. Die Kaltmessungen des Schrittes 8 laufen deshalb
**nach Schritt 6 und 7**, und jede von ihnen beginnt mit einem
**Containerneustart und dem geleerten Wirtscache**. Die Reihenfolge innerhalb des
Schrittes bleibt unverändert bindend: erst 1 und 3 kalt, danach 2 und 4 warm.

**Ein Aufruf der Diagnose-Route (`ranked_sides`) LAEDT das Modell. Vor einer
Kaltmessung darf sie deshalb nicht aufgerufen werden.**

Das ist kein Fehler dieser Route, sondern ihr Entwurf: sie ist seit Phase 12 das
Werkzeug der Fremdbestands-Vorprüfung (MESS-04, Schritt 3 dieser Tabelle), sie
trägt keine 1,5-Sekunden-Decke und sie ist keine Nutzerroute, also fragt sie
nicht, ob sie laden darf, und lädt. Die Zeile und ihre Begründung stehen in
`backend/src/findling/api/diagnose.py` unmittelbar über dem Aufruf von
`ranked_sides`. Wer die Fremdbestands-Vorprüfung fahren will, fährt sie **nach**
den Kaltmessungen 1 und 3 oder nimmt den Aufwärmeffekt ins Protokoll. Der
Abbruch dafür ist Rückgabewert **30**, und er ist einer: eine aufgewärmte
Kaltmessung wird nicht geschätzt und nicht herausgerechnet, sie wird nach einer
erneuten Ruhephase wiederholt.

**Die zweite Hälfte derselben Falle.** Nach einer Entladung meldet die
Diagnose-Route eine vollständige semantische Seite, weil sie lädt; die
Nutzerrouten melden im selben Moment eine leere, weil sie unter dem Schalter
nicht laden dürfen. Wer die zwei verwechselt, misst zwei verschiedene Dinge und
nennt sie eine Zahl. Die Regel daraus: ob die semantische Seite steht, wird an
der Nutzerroute abgelesen und nie an der Diagnose-Route. Die Diagnose-Route
beantwortet, ob der Bestand zu einer Zeile etwas hergibt, und nicht, was ein
Nutzer in diesem Moment bekommen würde.

**Der Ast mit eingeschaltetem Schalter braucht den Beleg, dass entladen wurde.**
Abgelesen wird das am Zustand `unloaded` der Statusseite und am Entladezähler
des Containers. Bleiben beide aus, misst der Ast das Nachwärmen von etwas, das
nie losgelassen wurde; der Abbruch dafür ist Rückgabewert **31**.

Die drei neuen Abbrüche setzen den Katalog dieses Laufverzeichnisses bei **29**
fort, und sie stehen wie die vier aus 6.1 und 6.2 **unterhalb** der
`tee`-Pipeline ihres Skripts, aus demselben Grund: der Rückgabewert einer
Pipeline gehört zu `tee`.

| Bedingung | Wo sie greift | Folge |
|---|---|---|
| Die Stellung des Entladeschalters war fuer einen Messschritt nicht ablesbar | Schritt 8, und vor jedem anderen Messblock | Rückgabewert **29** für die fehlende Pflichtzeile. Ein Lauf ohne protokollierte Stellung gilt als unvollständig, wie einer ohne Cron-Intervall (Abschnitt 6.4) |
| Vor einer Kaltmessung wurde die Diagnose-Route gerufen | Schritt 8, vor Ausprägung 1 oder 3 | Rückgabewert **30** für den aufgewärmten Container. Die Messung wird wiederholt oder mit dem Aufwärmeffekt im Protokoll gefahren, nie herausgerechnet |
| Der Ast mit eingeschaltetem Schalter hat keine Entladung erlebt | Schritt 8, Ausprägung 1 und 2 | Rückgabewert **31** für die ausgebliebene Freigabe. Kein `unloaded`, kein Entladezähler über null, also keine Wiederaufwärmzahl |

---

## 8. Abbau-Checkliste

**Die Reihenfolge ist Teil der Aussage.** Erst erheben, dann sichern, dann
prüfen, dann zerstören, danach nachsehen. Ein `destroy`, das vor einem Schritt
steht, der noch Zahlen erhebt, ist das Warnzeichen: was nach dem Abbau fehlt,
fehlt endgültig, und der Abbau vom 11.09.2026 ist der Beleg, dass das nicht
theoretisch ist.

Die Platzhalter aus Abschnitt 4 gelten weiter. `<instanz>`, `<volume>` und
`<sg>` stehen für die Kennungen der laufenden Box und kommen aus `box.env`
beziehungsweise aus `aws_box.sh status`.

### Schritt 1: Endmessungen und Gegenproben, VOR jedem zerstoerenden Schritt

```sh
ssh <box> 'sudo docker exec --user www-data nextcloud-aio-nextcloud \
    php occ findling:index'
ssh <box> 'docker exec nc_app_findling_backend cat /sys/fs/cgroup/memory.max'
ssh <box> 'docker exec nc_app_findling_backend cat /sys/fs/cgroup/memory.peak'
```

Zuletzt erhoben wird alles, was an der laufenden Maschine hängt und danach nicht
mehr erhebbar ist: die Schlussstände von `occ findling:index` (indexiert,
übersprungen, fehlgeschlagen), der Vektorbestand, die Spitzenwerte der cgroup,
die Gegenproben der Laststufen, die Protokollblöcke beider Cron-Zweige und der
Baumhash des gemessenen Abbilds. Nach dem Abbau gibt es dafür keine zweite
Gelegenheit, und eine nachgereichte Zahl wäre eine Schätzung.

`Erwartete Ausgabe`: die Schlussstände stehen in den Rohdateien des
Messverzeichnisses und sind committet. Marke: `in Phase 15 erstmals vollzogen`.

### Schritt 2: Die Kosten- und Schadenshistorie fortschreiben

```sh
cat "${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}/box.env" \
    >> docs/measurements/<laufverzeichnis>/rohdaten/<nr>-abbau.txt
git add docs/measurements/<laufverzeichnis>/rohdaten/<nr>-abbau.txt
```

`box.env` trägt die einzige Kosten- und Schadenshistorie dieser Box: jede
Anhalte- und Startzeit mit Laufdauer und Kosten, den Schadensbericht vom
07.09.2026, in dem eine zweite Nextcloud am selben Docker-Dienst das Messvolumen
der ersten gelöscht hat, und den DI-05-36-Befund. `destroy` löscht die Datei im
letzten Schritt. Sie wandert deshalb VOR dem Abbau in eine committete Rohdatei
und geht vor dem Abbau auf `origin`, nicht danach. Geheimnisse gehören dabei
nicht mit: Adressen und Kennungen werden beim Übernehmen durch Platzhalter
ersetzt, wie es die Geheimnisregel im Kopf dieser Datei verlangt.

`Erwartete Ausgabe`: die Rohdatei enthält alle `BOX_`- und `VOLUME_`-Zeilen der
Zustandsdatei und den Schlusssatz mit verbrauchten Stunden, verbrauchten USD,
freigegebenem Deckel und Differenz. Marke: `in Phase 15 erstmals vollzogen`.

### Schritt 3: Box anhalten und den Snapshot ziehen

```sh
scripts/ops/aws_box.sh stop
scripts/ops/aws_box.sh snapshot
```

**Der gestoppte Zustand ist Vorbedingung und keine Notiz.** Ein Snapshot eines
angehängten, gerade beschriebenen Datenträgers ist absturzkonsistent und nichts
weiter; bei angehaltener Instanz ist das Dateisystem ruhig und die Kopie sauber.
`cmd_snapshot` bricht ab, wenn die Instanz nicht `stopped` ist, und zwar im
Moment der Erzeugung, denn das ist der Moment, in dem der Inhalt festliegt. Ein
kaputter Snapshot sieht bis zur Wiederherstellung genau wie ein guter aus.

`Erwartete Ausgabe`: `stop` meldet die Laufzeit und die Kosten dieser Laufzeit
und hängt sie an `box.env` an; `snapshot` meldet eine Snapshotkennung und das
Tag `purpose=findling-corpus-keep`. Beleg des Laufs vom 11.09.2026:
`docs/measurements/2026-09-werkzeugfixe/rohdaten/07-snapshot-und-abbau.txt`,
Abschnitte 0 und 1.

### Schritt 4: Snapshot unabhaengig nachlesen, nicht dem Waiter glauben

```sh
scripts/ops/aws_box.sh snapshot <snapshotkennung>
```

Mit einer Kennung als Argument erzeugt der Unterbefehl **nichts**. Er liest
zurück, prüft, dass der Snapshot zum Datenträger dieser Box gehört, und schreibt
das Ergebnis in die Zustandsdatei. Sechs Felder gehören in die Rohdatei:
`State`, `Progress`, `VolumeSize`, `VolumeId`, `StartTime` und `Encrypted`.

**Der Waiter der CLI gibt nach zehn Minuten auf, und das ist kein Fehler.** Am
11.09.2026 stand der Snapshot dieser Box zu diesem Zeitpunkt bei 8 Prozent und
brauchte insgesamt rund 52 Minuten. Ein zweiter Aufruf ohne Kennung wäre ein
zweiter Snapshot und eine zweite Rechnung gewesen; deshalb gibt es die Form mit
Argument. Der Waiter sagt nur, dass die API aufgehört hat, `pending` zu
antworten; die Nachlese sagt, was der Snapshot ist.

`Erwartete Ausgabe`: `State completed`, `Progress 100%`, `VolumeSize 60 GB`,
`VolumeId` gleich dem Datenträger dieser Box, `Encrypted False`, dazu die
Startzeit. Belegt am 11.09.2026, Abschnitt 2 derselben Rohdatei.

### Schritt 5: Sicherung von box.env anlegen und den Pfad benennen

```sh
cp "${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}/box.env" \
   "${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}/box.env.vor-abbau"
export FINDLING_STATE_BACKUP="${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}/box.env.vor-abbau"
```

`cmd_destroy` verlangt `FINDLING_STATE_BACKUP` als Pfad, die benannte Datei muss
existieren und sie muss Inhalt haben. Alle drei Prüfungen stehen VOR dem ersten
zerstörenden Aufruf und nicht hinter ihm: eine Verweigerung, die erst nach der
Terminierung fällt, kommt für die Historie zu spät (T-11-53). Die Sicherung ist
damit eine Vorbedingung und keine Gewohnheit.

`Erwartete Ausgabe`: `destroy` meldet als erste Zeile, dass die Historie dieser
Box in der benannten Datei gesichert ist. Fehlt der Pfad, existiert die Datei
nicht oder ist sie leer, endet der Unterbefehl, ohne irgendetwas zu löschen.

### Schritt 6: Der Abbau selbst

```sh
scripts/ops/aws_box.sh destroy
```

Der Unterbefehl terminiert die Instanz, löscht danach den Datenträger und
zuletzt die Security Group; die Reihenfolge ist zwingend, weil ein benutzter
Datenträger nicht löschbar ist und ein Abhängen unter laufendem Schreibzugriff
das Dateisystem beschädigt. Danach liest er alle drei Ressourcen zurück: eine
terminierte Instanz antwortet noch bis zu einer Stunde, deshalb gilt
`state=terminated` als Beweis; Datenträger und Gruppe gelten erst mit
`InvalidVolume.NotFound` beziehungsweise `InvalidGroup.NotFound` als weg. Was
sich nicht lesen lässt, zählt als noch vorhanden.

`Erwartete Ausgabe`: drei Zeilen "is gone, verified against the api" und
Rückgabewert 0. Bleibt etwas übrig, bleibt auch die Zustandsdatei stehen, damit
ein zweiter Lauf sie benutzen kann. Belegt am 11.09.2026 mit vier
Nichtexistenz-Nachweisen, den beiden Datenträgern eingeschlossen.

### Schritt 7: Tag-Sweep ueber die Regionen, ueber BEIDE Tagwerte

```sh
aws ec2 describe-tags --region eu-central-1 \
    --filters "Name=tag:purpose,Values=findling-phase5"
aws ec2 describe-tags --region eu-central-1 \
    --filters "Name=tag:purpose,Values=findling-corpus-keep"
```

**Warum zwei Suchen und nicht eine.** Der Sweep von `cmd_destroy` sucht nach
`purpose=findling-phase5`; der Keep-Tag `findling-corpus-keep` ist genau dafür
erfunden worden, dieser Suche zu entgehen, damit der Snapshot den Abbau nicht rot
enden lässt. Ein aus dem Snapshot erzeugter Datenträger erbt diesen Tag und
entginge damit demselben Sweep, also der Suche, die verhindern soll, dass eine
Ressource unbemerkt weiterläuft. Seit Plan 12-03 taggt `aws_box.sh restore` einen
solchen Datenträger pflichtmässig auf `findling-phase5` um und liest das Tag
zurück; der Sweep prüft es trotzdem unabhängig davon, weil ein von Hand
erzeugter Datenträger dieselbe Falle hätte.

**Ein Tag-Treffer ist ein Hinweis und kein Urteil.** Die Tag-Abfrage antwortet
aus einem nachlaufenden Verzeichnis: am 11.09.2026 meldete sie beide Datenträger
als Überbleibsel, während die API für beide `InvalidVolume.NotFound` antwortete.
Jeder Treffer wird deshalb nach seiner Art zurückgelesen, und nur was noch
antwortet, zählt als Überbleibsel.

`Erwartete Ausgabe`: die erste Suche liefert höchstens die gerade terminierte
Instanz, deren Tags noch bis zu einer Stunde nachhängen. Die zweite liefert genau
einen Treffer, den Korpus-Snapshot, und dieser Treffer ist zugleich der Beweis,
dass er den Abbau überlebt hat.

### Schritt 8: Kostenueberblick nach dem Abbau

```sh
aws ec2 describe-instances --region eu-central-1 \
    --filters "Name=instance-state-name,Values=pending,running,stopping,stopped"
aws ec2 describe-volumes --region eu-central-1
aws ec2 describe-snapshots --region eu-central-1 --owner-ids self
aws ec2 describe-addresses --region eu-central-1
```

Nach einer zerstörenden Handlung wird der Kostenstand **erhoben und nicht
behauptet**, und zwar über alle freigeschalteten Regionen, nicht nur über die
eine, in der gearbeitet wurde. Daneben gehört die Schlussrechnung der Anfahrt:
verbrauchte Stunden und USD aus `box.env` gegen den vom Owner freigegebenen
Deckel, mit der Differenz in einer eigenen Zeile.

`Erwartete Ausgabe`: keine laufende oder angehaltene Instanz, kein Datenträger,
keine Elastic IP, keine eigene AMI, **genau ein Snapshot**. Das Schlüsselpaar und
die Default-Gruppe der VPC bleiben bestehen und kosten nichts. Belegt am
11.09.2026 über 17 Regionen.

### Schritt 9: Was bewusst stehen bleibt

Der Korpus-Snapshot `snap-03f1d1d9ad9262704` bleibt. Er kostet **2,79 bis 2,99
USD je Monat**, gerechnet aus 51,6 GiB geschriebener Blöcke und dem öffentlichen
Satz je GB-Monat, gegen 9,39 USD je Monat für die angehaltene Box. Er ist die
Grundlage jeder weiteren Anfahrt, und ohne ihn kostet der Wiederaufbau des
Korpus wieder mehrere Stunden Box-Zeit.

Die Wiedervorlage steht nach v1.2 an: löschen oder auf eine günstigere
Speicherklasse legen. Solange darüber nicht entschieden ist, läuft dieser Posten
weiter, ob eine Anfahrt stattfindet oder nicht, und gehört deshalb in die
Monatsrechnung und nicht in den Deckel einer Anfahrt.

---

## 9. Kostenfuehrung

### 9.1 Die Felder der Zustandsdatei

| Feld | Wann es geschrieben wird | Wer es schreibt |
|---|---|---|
| `BOX_INSTANCE_ID` | nach dem Anlegen der Instanz, einmalig | von Hand. `aws_box.sh create` legt nichts an, es druckt nur das Rezept |
| `BOX_SECURITY_GROUP` | nach dem Anlegen der Security Group, einmalig | von Hand, aus der Antwort von `create-security-group`. `start` braucht das Feld, um die SSH-Regel nachzuziehen |
| `VOLUME_ID` | beim Anlegen des Datenträgers | `aws_box.sh volume`, und beim Wiederaufbau `aws_box.sh restore` |
| `VOLUME_NAME` | zusammen mit `VOLUME_ID` | dieselben beiden Unterbefehle, aus der gepinnten Konstante |
| `VOLUME_SIZE_GB` | zusammen mit `VOLUME_ID` | dieselben beiden Unterbefehle |
| `VOLUME_TYPE` | zusammen mit `VOLUME_ID` | dieselben beiden Unterbefehle |
| `VOLUME_CREATED_ISO` | zusammen mit `VOLUME_ID` | dieselben beiden Unterbefehle, als UTC-Zeitstempel |
| `VOLUME_FROM_SNAPSHOT` | nur auf dem Wiederaufbaupfad | `aws_box.sh restore`. Das Feld sagt, dass dieser Datenträger aus einem Snapshot stammt und den Keep-Tag geerbt hatte |
| `CORPUS_SNAPSHOT_ID` | beim Ziehen oder Nachlesen des Snapshots | `aws_box.sh snapshot`, zusammen mit `CORPUS_SNAPSHOT_ISO` und der vollständigen Nachlese als Kommentarblock |
| `BOX_LAST_UPTIME_COST_USD` | bei jedem Anhalten | `aws_box.sh stop`, aus den gepinnten Sätzen mal der gemessenen Laufzeit |
| `BOX_LAST_UPTIME_HOURS` | bei jedem Anhalten | `aws_box.sh stop`, gelesen VOR dem Aufruf, der die Instanz parkt |
| `BOX_PARKED_COST_USD_PER_DAY` | bei jedem Anhalten | `aws_box.sh stop`. Der Unterbefehl summiert die geparkten Tage ausdrücklich nicht auf |
| `BOX_STOPPED_ISO`, `BOX_STARTED_ISO`, `BOX_IP` | bei jedem Anhalten und jedem Start | `aws_box.sh stop` und `aws_box.sh start`. `BOX_IP` ist nach einem Stopp veraltet, weil ein Stopp die öffentliche Adresse freigibt |

Die Datei wird **angehängt und nicht überschrieben**, und sie entsteht unter
`umask 077`. Jeder Block trägt eine Kommentarzeile mit Zeitstempel darüber, und
deshalb ist die Datei zugleich die Chronik der Box.

### 9.2 Wo die Zustandsdatei liegt, und warum dort

`${FINDLING_LOADTEST_DIR:-$HOME/.findling-loadtest}/box.env`, also ausserhalb
des Arbeitsbaums. Der Grund ist nicht Ordnung, sondern Abstand: eine
Zustandsdatei im Repositorium ist von einem unachtsamen `git add` genau einen
Handgriff von einem öffentlichen Commit entfernt, und sie trägt Adressen,
Ressourcenkennungen und die Chronik des Kontos. Derselbe Grund gilt für die
AWS-Anmeldung und für die Sicherung der Systemplatte (Abschnitt 3, Zeilen 2 und
3).

Für den Weg in das Repositorium gibt es genau einen Pfad, und er führt über
Schritt 2 der Abbau-Checkliste: übernehmen, Werte durch Platzhalter ersetzen,
committen.

### 9.3 Der Rueckfluss ins Deckel-Rechenblatt

Die Spalte "Ist (Phase 15)" in Abschnitt 2.1 wird während und nach der Anfahrt
gefüllt, Posten für Posten, aus den Zeitstempeln der Rohdateien und aus
`BOX_LAST_UPTIME_HOURS`. Die nächste Anfahrt rechnet ihren Deckel dann aus den
zuletzt GEMESSENEN Posten statt aus den heutigen Schätzungen; die Zeile
"Handaufbau der Maschine" verliert dabei als erste ihren Schätzcharakter.

Das ist der Kreis, den D-05 verlangt: gemessene Posten ergeben den nächsten
Deckel, der nächste Lauf misst sie erneut, und keine Zahl dieses Rechenblatts
stammt aus einer Erinnerung. Zum Rückfluss gehört auch die ehrliche Zeile, wenn
der Deckel gerissen ist, mit der Differenz und dem Grund; die Deckel-Geschichte
in Abschnitt 2.4 führt genau solche Zeilen.

### 9.4 Was dieses Runbook nicht leisten kann

**Der Snapshot-Pfad ist bis zum Erstvollzug in Phase 15 ungefahren.** Die
Wiederherstellung eines Datenträgers aus `snap-03f1d1d9ad9262704`, sein
Einhängen, die Rückspielung der Systemplatte und der gesamte Abbau als Kette
sind aus Skripten, Rohdaten früherer Läufe und lesenden Proben zusammengetragen,
aber nie als Ganzes durchlaufen worden.

Jeder Block, der die Marke `in Phase 15 erstmals vollzogen` trägt, wird dort zum
ersten Mal wörtlich validiert. Nach dem Erstvollzug werden die erwarteten
Ausgaben durch die tatsächlichen ersetzt, und wo die tatsächliche Ausgabe von der
erwarteten abweicht, bleibt die Abweichung als eigene Zeile stehen, statt
stillschweigend überschrieben zu werden. Ein Runbook, das seine eigenen Irrtümer
löscht, lehrt beim zweiten Mal dasselbe wie beim ersten.
