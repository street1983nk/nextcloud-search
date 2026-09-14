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
