# Die Fremdinstallation, von Hand auf einer frischen Instanz

Diese Seite ist das Protokoll eines Laufs und die Liste dessen, was er nicht
abdeckt. Sie beantwortet die eine Frage, die keine CI beantworten kann: was
passiert, wenn jemand Findling auf einer Nextcloud installiert, die noch nie
eine Zeile davon gesehen hat, und danach nichts weiter tut.

Der Unterschied zu `deploy-harp.yml` ist keine Kleinigkeit. Der Job dort geht
denselben Weg, über vier Serverfassungen und bei jedem Lauf, und er ist der
belastbare Teil. Was er nicht hat, ist die frische Instanz, die ein Selfhoster
aufsetzt, mit ihrem eigenen Takt und ohne die Abkürzungen, die ein Testjob sich
leistet. Genau dafür gibt es `scripts/dev/aio_install_check.sh` und diese Seite.

Der Leitsatz ist derselbe wie in `docs/uninstall.md`: jede Aussage nennt auch
ihre Grenze, und jede Abweichung vom Weg der CI steht hier als Befund und nicht
als Fussnote. Der ganze Zweck dieses Laufs ist, das zu finden, was die CI sich
erspart.

## 1. Der Lauf vom 06.09.2026, amd64

### Die Umgebung

| Was | Wert |
|---|---|
| Wirt | Windows 11, Docker Desktop 4.76.0, Docker Engine 29.5.2, WSL2-Kern 6.6.87.2, 12 CPUs, 7,6 GiB |
| Nextcloud | 34.0.3, Abbild `nextcloud:34.0.3-apache`, SQLite |
| Weg | docker compose, drei Dienste: Nextcloud, HaRP, ein Frontproxy (`nginx:1.27-alpine`) |
| Architektur | amd64, Pull mit `--platform linux/amd64` |
| Port | **8097**. Der in `06.1-CONTEXT.md` vorgesehene Port 8090 war zur Laufzeit von einer anderen Instanz belegt. Port 8080 gehört der MCP-Sitzung und wurde nicht angefasst. |
| AppAPI | 34.0.0, mit dem Server ausgeliefert |
| HaRP | `ghcr.io/nextcloud/nextcloud-appapi-harp`, festgenagelt auf `sha256:603fdf5c...`, dieselbe Zeichenkette wie in `deploy-harp.yml` |
| Deploy-Daemon | `harp_proxy_compose`, `docker-install`, HaRP an `harp:8780`, `nextcloud_url` auf den Frontproxy |
| Companion-Archiv | `findling.tar.gz`, Fassung 1.0.0, SHA-256 `50bfa1fcd2290223912ace81c9e33b91db86eac7a66a5f2c7ed6c27b98f61ef6` |
| Backend-Archiv | `findling_backend.tar.gz`, Fassung 1.0.0, SHA-256 `eb96ebed6a7a68d828bc4be761553b9b2a115ccff49e6ea36566f4f303d5f359` |
| Abbild | `ghcr.io/street1983nk/findling_backend:dev`, Digest `sha256:239a98193b6c556025ff891a08448b1a1ccf2abdfbcad16b544fbef82557698e` |
| Nutzer | `admin` für die Verwaltungsseite, `testuser` ohne Rechte für Hochladen und Suche |

Der Lauf begann um 21:42:44 UTC und endete um 21:52:41 UTC, also knapp zehn
Minuten für beide Hälften einschliesslich der sechs Deinstallations-Zusagen.

### Annahme A6: der anonyme Pull

**Bestätigt.** Vor der Installation und mit einem leeren Zugangsdatenspeicher
(`DOCKER_CONFIG` auf ein eigenes leeres Verzeichnis) beantwortet ghcr.io den
Pull ohne jede Anmeldung:

```
pulled anonymously: ghcr.io/street1983nk/findling_backend@sha256:239a98193b6c...
```

Danach hat der Lauf die lokale Kopie entfernt, damit der Deploy-Daemon das
Abbild selbst holen muss. Er hat es geholt: der laufende Container trägt
`ghcr.io/street1983nk/findling_backend:dev` und keine Adresse einer lokalen
Registry.

Zwei Anmerkungen zur Reichweite dieser Bestätigung. Erstens gilt sie für den
beweglichen Tag `dev`, nicht für `1.0.0`, siehe Befund 1. Zweitens hat sich der
Digest zwischen zwei Läufen desselben Abends geändert (`sha256:458ade54...` um
20:58 UTC, `sha256:239a9819...` um 21:34 UTC); `dev` ist ein beweglicher Tag und
verhält sich hier genau so.

### Der Zero-Config-Nachweis, als Zahlenreihe

Zwischen der fertigen Installation und dem ersten Inhaltstreffer wurde nichts
eingestellt. Die Datei kam als gewöhnlicher Nutzer über WebDAV in dessen
Heimatverzeichnis (HTTP 201), gesucht wurde über die gewöhnliche OCS-Route mit
einem erfundenen Wort, das in keinem Wörterbuch und in keiner Skelettdatei
steht.

| Messpunkt | Zeitstempel (UTC) | Deckungsgrad | indexiert von indexierbar |
|---|---|---|---|
| vor der ersten Cron-Runde | 21:49:55 | unbekannt | 0 von 0 |
| nach Cron-Runde 1 | 21:50:07 | 0 Prozent | 0 von 100 |
| nach Cron-Runde 2, Treffer | 21:50:19 | 54 Prozent | 54 von 99 |

**Der Treffer kam nach zwei Cron-Runden.** Der Deckungsgrad ist dabei von einer
Instanz ohne jede Zahl auf 54 Prozent gestiegen, ohne dass jemand etwas
konfiguriert hat.

Die Frist, gegen die gemessen wurde, ist ausdrücklich keine geratene
Sekundenzahl. Sie zählt **Cron-Runden**, weil der Systemcron der Instanz die
langsamste beteiligte Uhr ist; das ist die Lehre aus 06-11, wo eine Gegenprobe
einen gesunden Lauf um 52 Sekunden zu früh für tot erklärte. Das Budget waren
acht Runden, gebraucht wurden zwei. Ein Systemcron im Fünf-Minuten-Takt hätte
für dasselbe Ergebnis rund **600 Sekunden** gebraucht; die 26 Sekunden Uhrzeit
dieses Laufs sind die Uhr des Laufs und nicht die einer Instanz.

Der Hintergrundjob-Modus dieser Instanz meldet `cron`. Ein Cron-Dienst läuft im
Abbild `nextcloud:34.0.3-apache` aber nicht mit, deshalb hat das Skript
`php -f cron.php` gerufen, also denselben Befehl, den ein Systemcron ausführt.
Das ist der Mechanismus und keine Abkürzung, und die Umrechnung in Cron-Zeit
oben hält den Unterschied sichtbar.

**Zwischen Installation und Treffer lief kein einziger occ-Aufruf.** Die Liste
ist nicht aus der Erinnerung geschrieben, sondern von einem Aufzeichner: jeder
occ-Aufruf des Laufs geht durch eine Funktion, die vor dem Ausführen
protokolliert. Bis zur fertigen Installation waren es zehn Aufrufe:

```
1  occ status                     6  occ integrity:check-app findling
2  occ app:list                   7  occ integrity:check-app findling
3  occ app_api:app:list           8  occ integrity:check-app findling
4  occ config:app:get core backgroundjobs_mode
5  occ app:enable findling        9  occ app_api:app:register findling_backend ... --wait-finish
                                 10  occ app_api:app:list
```

Danach: nichts. Nicht `occ findling:index`, nicht `occ background-job:worker`,
kein `occ config:app:set`.

### Der Integritätsbeweis der Companion-Hälfte

`occ integrity:check-app findling` antwortet auf der frischen Instanz **leer**,
und leer ist das saubere Urteil. Dass diese Antwort etwas bedeutet, zeigt die
Gegenprobe im selben Lauf: eine einzige angehängte Zeile in
`lib/AppInfo/Application.php` kippt das Urteil auf `INVALID_HASH`, und nach dem
Zurücknehmen der Zeile ist die Antwort wieder leer. Die dritte Prüfung ist die
gegen den stillen Durchlauf: die Ausgabe darf das Wort `skipping` nicht
enthalten, denn eine App ohne `appinfo/signature.json` wird übersprungen und
antwortet trotzdem mit 0.

Die Routenliste kam ebenfalls aus dem Archiv: die `info.xml`, mit der
registriert wurde, trägt fünf `route`-Elemente, und AppAPI liest sie zur
Installationszeit von dort.

### Die sechs Deinstallations-Feststellungen

Wortgleich mit den sechs Feststellungen aus `deploy-harp.yml`, damit CI und
frische Instanz einen Massstab haben und nicht zwei.

| # | Feststellung | Ergebnis auf dieser Instanz |
|---|---|---|
| 1 | Ohne Kennzeichen bleibt das Volume | `container gone, volume nc_app_findling_backend_data kept` |
| 2 | Der Weg zurück: eine zweite Registrierung nimmt dasselbe Volume | `registered again as nc_app_findling_backend on the kept volume nc_app_findling_backend_data` |
| 3 | Mit `--rm-data` verschwindet das Volume | `container and volume nc_app_findling_backend_data both gone` |
| 4 | Ein Abschalten ohne Absicht räumt nichts | vorher drei Tabellen und 7 Einstellungen, danach dieselben drei Tabellen und 8 Einstellungen |
| 5 | Ein Entfernen mit Absicht räumt vollständig | `after the remove with intent: tables [], settings 0`, und `custom_apps/findling` ist fort |
| 6 | Der Container ohne Companion zieht sich zurück | `container nc_app_findling_backend is Up About a minute, retreat announced, 2 new warning or error lines` |

Die Zahl der Einstellungen steigt bei Feststellung 4 von 7 auf 8, und das ist
kein Fehler: der Uninstall-Schritt zählt seinen eigenen Aufruf mit, wie es
`docs/uninstall.md` ganz oben misst. Es verschwindet nichts, es kommt eine Zahl
dazu.

Feststellung 5 hat auf dieser Instanz eine Aussage mehr als in der CI: die
entfernte Companion-App ist die, die das Archiv geliefert hat, samt ihrer
`appinfo/signature.json`. Ein Rückstand des Archivs wäre genau hier sichtbar
geworden, und es gab keinen.

## 2. Die Befunde: wo dieser Lauf vom Weg der CI abweicht

### Befund 1: Der Tag `1.0.0` existiert noch nicht

Das Archiv nennt `ghcr.io/street1983nk/findling_backend:1.0.0`, und die
Registry antwortet darauf mit 404: `docker.yml` veröffentlicht die
Versionsfassung erst auf einem `v`-Tag und sonst nur `dev` und die Commit-SHA.
Der Lauf ist deshalb gegen `dev` gefahren, mit **genau einer** ersetzten Zeile
in der `info.xml`, geprüft als Zwei-Zeilen-Unterschied; Registry, Abbildname und
der Routenblock kamen unverändert aus dem Archiv.

Das ist dieselbe Regel, die `deploy-harp.yml` auf einem Zweig anwendet, und es
ist eine Aussage über den Zeitpunkt und nicht über den Weg: **erst der Lauf nach
dem Release-Tag fährt den Weg vollständig.** Bis dahin ist der Teil "der Tag,
den das Archiv nennt, existiert" ungeprüft.

### Befund 2: Die Code-Signatur trägt eine Ersatzidentität

`docs/certificates.md` verbietet den Release-Schlüssel ausserhalb von
`release.yml`. Ein Lauf von Hand kann also keine Store-Signatur herstellen. Wie
in der CI wurde deshalb eine Wegwerf-CA mit einem Blattzertifikat `CN=findling`
erzeugt und die CA an `resources/codesigning/root.crt` der Instanz angehängt.

Was das belegt: dass das Archiv eine Signatur über genau die Dateiliste trägt,
die es ausliefert, dass die Instanz jede Datei neu hasht, und dass ein einziges
verändertes Byte das Urteil kippt. Was es nicht belegt: die Herkunft des
Zertifikats. Diese Hälfte gehört `release.yml`.

### Befund 3: `root.crt` endet ohne Zeilenumbruch, und ein `cat` klebt zwei Zertifikate zusammen

Der teuerste Befund des Abends, und er erklärt einen roten CI-Schritt.

Die von Nextcloud ausgelieferte Datei `resources/codesigning/root.crt` endet
**nicht** mit einem Zeilenumbruch. Wer ein weiteres Zertifikat mit `cat ... >>`
anhängt, bekommt deshalb diese Zeile:

```
-----END CERTIFICATE----------BEGIN CERTIFICATE-----
```

`Checker::splitCerts()` zerlegt die Datei mit einem Muster, das auf diese
verklebte Zeile nicht passt. Das angehängte Zertifikat wird damit nie als CA
geladen, und die Prüfung endet mit

```
OC\IntegrityCheck\Exceptions\InvalidSignatureException: Certificate is not valid.
```

Die Falle daran ist die Absicherung, die man naheliegenderweise davorsetzt: eine
Zählung von `BEGIN CERTIFICATE` findet auch in der verklebten Zeile einen
Treffer mehr und meldet Erfolg. Die Prüfung, die trägt, zählt die Zeilen, die
**nur** aus dem Marker bestehen, also mit Zeilenanfang und Zeilenende. Die
Abhilfe ist ein Zeilenumbruch vor dem Anhängen.

Für diesen Lauf ist der Befund behoben, und der Integritätsbeweis oben ist mit
der reparierten Datei entstanden.

### Befund 4: Ohne einen Frontproxy wartet die Registrierung ewig

`app_api:app:register --wait-finish` kehrte in den ersten Anläufen nicht zurück,
während daneben ein gesunder Container lief. Im Containerprotokoll steht der
Grund:

```
NextcloudException: [404] Not Found <request: PUT /ocs/v1.php/apps/app_api/ex-app/status>
```

Das Feld `nextcloud_url` des Daemons wird von AppAPI zweimal benutzt und in
entgegengesetzte Richtungen: `resolveExAppUrl` baut daraus
`{nextcloud_url}/exapps/{appId}` und muss HaRP erreichen, und derselbe Wert wird
dem Container als `NEXTCLOUD_URL` gegeben und muss Nextcloud erreichen. HaRP
beantwortet nur Pfade mit `/exapps/{appId}`, also kann der Container seinen
Initialisierungsstand nicht melden, und die Registrierung wartet auf einen
Status, der nie kommt.

Die Abhilfe ist die Topologie einer echten Instanz: **eine** Adresse vor
Nextcloud und HaRP, die `/exapps/` in den Tunnel und alles andere an den Server
weiterreicht. All-in-one bringt genau das mit, ein Apache tut es mit einem
`location`-Block, und `deploy-harp.yml` stellt in der CI ein nginx davor. Dieser
Lauf hat es genauso gemacht.

Das ist zugleich ein Befund an der Dokumentation: der Abschnitt "Der
Store-Installationsweg lokal" in `docs/dev-setup.md` beschreibt die
compose-Einrichtung ohne diesen Frontproxy und trägt `http://harp:8780` als
`nextcloud_url`. Wer diese Anleitung heute befolgt, läuft in eine hängende
Registrierung. Nachgezogen ist die Anleitung in dieser Phase **nicht**; das ist
als Befund benannt und nicht behoben.

### Befund 5: Ein Archiv aus einem Windows-Arbeitsbaum ist nicht dasselbe Archiv

Die beiden Archive dieses Laufs wurden nach den Regeln von
`scripts/release/store-archive.sh` gebaut, aber auf einem Wirt, dessen
Arbeitsbaum wegen `core.autocrlf=true` CRLF-Zeilenenden trägt. Das Archiv trägt
sie damit ebenfalls, während dieselben Dateien im Repository und in der CI LF
tragen. Für die Auslieferung heisst das: **die Release-Archive entstehen in
`release.yml` und nirgendwo sonst.** Ein von Hand auf einem Windows-Rechner
gebautes Archiv ist byteweise ein anderes Paket, und jede Datei in seiner
Signatur hat einen anderen Hash.

Inhaltlich hat dieser Unterschied den Lauf nicht gestört: die Signatur ist in
sich stimmig, AppAPI liest die XML-Datei mit beiden Zeilenenden, und der
Inhaltsnachweis von `store-archive.sh` lief für beide Archive durch.

### Befund 6: Das Abbild lag schon auf dem Wirt

Auf einem Entwicklungsrechner liegt das Abbild oft schon da, und dann könnte der
Deploy-Daemon es lokal finden und die Registry nie anfassen. Der Lauf hat es
deshalb nach dem anonymen Pull gelöscht (`--rmi-local-image`), damit der Daemon
selbst ziehen muss. Ohne diesen Schalter meldet das Skript den Umstand als
Befund, statt den Unterschied zwischen "Weg belegt" und "Weg angenommen"
verschwinden zu lassen.

### Befund 7: Der Wirt ist Windows, und das rechnet Pfade um

Die Shell, die Git unter Windows mitbringt, schreibt Argumente um, die wie
Unix-Pfade aussehen, bevor sie ein natives Programm erreichen. Aus
`/var/www/html` wird ein Windows-Verzeichnis, aus `/CN=...` ein Laufwerkspfad.
Der Lauf setzt deshalb `MSYS2_ARG_CONV_EXCL` auf die Pfade, die dem **Container**
gehören. Das ist eine Eigenschaft dieses Wirts und keine des Installationswegs;
auf der ARM-Box und auf jedem Linux-Wirt entfällt es.

## 3. Was nicht abgedeckt ist

Diese Liste ist der zweite Zweck dieser Seite. Sie nennt je Punkt, was fehlt,
warum es fehlt, was ein Nutzer daraus für sich ableiten kann, und welche
Entscheidung dahintersteht.

### Der Federated Share

Der Federated Share ist nicht getestet. Ein föderierter Zugriff braucht eine
zweite Nextcloud mit einer Vertrauensbeziehung und einen zweiten Datenbestand,
und dieser Aufbau ist für das Erstrelease bewusst nicht gefahren worden
(Entscheidung E-H6 vom 06.09.2026). Die Rechtegrenze ist davon nicht berührt:
auch für föderierte Freigaben entscheidet der finale Recheck in der
Companion-App, welcher Treffer einen Nutzer erreicht. Belegt ist dieser Pfad
nicht, und das Federated-Szenario ist Kandidat für v1.x.

### Das Upgrade von einem älteren Bestand

Ein Upgrade von einer älteren Fassung mit einer echten Datenbank-Migration ist
nicht gefahren, und für ein Erstrelease kann es das auch nicht sein: es gibt
keinen älteren Bestand. Was ein Nutzer daraus ableiten kann: die Zusage, dass
ein Update den Index nicht wegwirft, ist für v1.0 eine Zusage über die Zukunft
und kein Beweis über heute. Die Fassungs- und Lockstep-Mechanik, die dieses
Versprechen tragen soll, ist an anderer Stelle geprüft (`deploy-harp.yml`,
Fassungssprung; `backend/tests/test_lockstep_versions.py`), der gelebte
Umstiegspfad einer bestehenden Installation ist es nicht.

### Der Weg über die Weboberfläche

Dieser Lauf ruft ausschliesslich occ. Die ExApps-Verwaltungsoberfläche von
AppAPI, über die ein Admin dieselbe Installation klickt, ist nicht angefasst
worden, und der Schalter "Daten löschen" der App-Verwaltung von Nextcloud 32 und
33 bleibt aus demselben Grund ungemessen wie in `docs/uninstall.md`,
Abschnitt 5. Was ein Nutzer daraus ableiten kann: die Befehlszeile ist belegt,
die Oberfläche ist die Bauart von AppAPI und Nextcloud und nicht die von
Findling.

### arm64: gefahren am 07.09.2026, siehe Abschnitt 5

**arm64 ist keine Lücke dieser Seite.** Der Owner hat am 06.09.2026 mit
Entscheidung **E-H5** Option A gewählt: der Installationsweg wird auch auf arm64
gefahren, im selben Anlauf der Box wie die Nachmessung von Plan 06.1-18. Der Lauf
ist erfolgt, und sein Protokoll steht unten in Abschnitt 5, mit dem einen Punkt,
in dem er von E-H5 abweicht, und mit der Begründung dafür.

Kriterium 3 der ROADMAP behält damit seinen Umfang; die einzige Änderung daran
folgt aus E-H1 und betrifft nur die Fassungsspanne (NC 33 bis 35 statt 32 bis
35), vollzogen in Plan 06.1-19.

## 4. Wie dieser Lauf zu wiederholen ist

```
FINDLING_ADMIN_PASS=PASSWORT \
FINDLING_USER_PASS=PASSWORT \
  scripts/dev/aio_install_check.sh \
  --url http://localhost:8097 \
  --admin admin \
  --user testuser \
  --exec "docker exec -i -u www-data -w /var/www/html findling-store-nc" \
  --companion dist/findling.tar.gz \
  --backend dist/findling_backend.tar.gz \
  --version 1.0.0 \
  --daemon harp_proxy_compose \
  --cron-driver script --cron-interval 300 --cron-rounds 8 \
  --rmi-local-image \
  --db-tables-cmd "docker exec -i findling-store-nc php /tmp/tables.php"
```

`--help` beschreibt jede Option. Solange kein `v1.0.0`-Tag steht, braucht der
Lauf zusätzlich `--substitute-tag dev`, und das ist Befund 1.

Die beiden Passwörter sind Umgebungsvariablen und keine Argumente, und das
Skript weist ein `--admin` oder `--user` mit Doppelpunkt ab. Ein Argument
steht so lange in der Prozessliste der Maschine, wie der Lauf dauert, und der
dauert hier fast eine Stunde; dort hat das Sicherheitsaudit aus Plan 06.1-17
die Passwörter gefunden (DI-06.1-18).

Was der Lauf voraussetzt und selbst nicht herstellt: eine frische Instanz, einen
Deploy-Daemon, die beiden Archive und die Vertrauenskette für ihre Signatur. Er
baut nichts und er holt nichts aus einem Arbeitsbaum, und genau das ist der
Grund, warum sein Ergebnis über eine Store-Installation etwas aussagt.

## 5. Der Lauf vom 07.09.2026, arm64

Dieser Abschnitt ist die zweite Hälfte von Entscheidung E-H5. Er ist bewusst in
derselben Ordnung geschrieben wie Abschnitt 1, damit die beiden Läufe
gegeneinander gehalten werden können statt nur nebeneinander zu stehen.

### Die Umgebung

| Was | Wert |
|---|---|
| Wirt | AWS m7g.large, 2 vCPU Graviton3, `aarch64`, Ubuntu 24.04, auf 4 GB begrenzt, Instanz `i-06b1d913f5c6f669b` |
| Nextcloud | 34.0.3.2, Abbild `nextcloud:34.0.3-apache`, SQLite |
| Weg | docker, drei Dienste: Nextcloud, HaRP, ein nginx-Frontproxy |
| Architektur | **arm64**, jeder Pull mit `--platform linux/arm64`, zurückgelesen: `nextcloud arch=arm64`, `harp arch=arm64` |
| Port | 8097, derselbe wie im amd64-Lauf |
| AppAPI | 34.0.0, mit dem Server ausgeliefert |
| HaRP | `ghcr.io/nextcloud/nextcloud-appapi-harp:release`, arm64 |
| Deploy-Daemon | `harp_arm64`, `docker-install`, HaRP an `findling-arm64-harp:8780`, `nextcloud_url` auf den Frontproxy |
| Companion-Archiv | `findling.tar.gz`, Fassung 1.0.0, SHA-256 `09963ad6bcc1d12cdc66ac76a4a1939583ff88a40d9f3f22a9e2cfec4039c65d` |
| Backend-Archiv | `findling_backend.tar.gz`, Fassung 1.0.0, SHA-256 `b22d38e1f2462c7f0c19dfbe4b62a3f220644246f8c7c479092ca680b53ac5f3` |
| Abbild | `ghcr.io/street1983nk/findling_backend:dev`, Digest `sha256:00111fd090f437a00678f6fc0a562807a5ad0b35082db235ea52ee86c63454c9` |
| Nutzer | `admin` für alles; ein zweiter Nutzer war für diesen Lauf nicht vorgesehen |
| Hintergrundjobs | `unset`, was Nextcloud als `ajax` liest, deshalb `--cron-driver script` mit 300 s Takt |

Der Lauf begann um 06:42:02 UTC und endete um 06:46:55 UTC, also **4 min 51 s**
für beide Hälften einschliesslich der sechs Deinstallations-Zusagen. Der
amd64-Lauf brauchte 9 min 57 s; der Unterschied ist der Zero-Config-Nachweis, der
hier nach einer Cron-Runde traf statt nach zwei.

Protokoll und Vorbereitung im Rohzustand:
[`rohdaten/81-arm64-lauf.txt`](measurements/2026-09-nachmessung-m7g/rohdaten/81-arm64-lauf.txt)
und
[`rohdaten/80-arm64-vorbereiten.txt`](measurements/2026-09-nachmessung-m7g/rohdaten/80-arm64-vorbereiten.txt),
beide unter `docs/measurements/2026-09-nachmessung-m7g/`. Die zwei Skripte stehen
daneben unter `skripte/80-arm64-vorbereiten.sh` und `skripte/81-arm64-lauf.sh`.

### Die Abweichung von E-H5, und warum sie so entschieden wurde

**E-H5 sagt `--flavour aio --aio-image-tag latest-arm64`. Gefahren wurde
`--flavour compose --platform linux/arm64`.** Das ist eine Abweichung, sie ist
bewusst, und hier sind ihre drei Gründe:

1. **Vergleichbarkeit, und das ist der Grund, den das Abnahmekriterium nennt.**
   Der amd64-Lauf ist über `--flavour compose` auf einer
   `nextcloud:34.0.3-apache`-Instanz gefahren, nicht über all-in-one. Ein
   arm64-Lauf über all-in-one hätte gegen einen amd64-Lauf über compose
   gestanden, und die beiden Protokolle hätten sich in zwei Dingen gleichzeitig
   unterschieden. Dieser Lauf unterscheidet sich in genau einem: der
   Architektur.
2. **Der Speicher der Box.** Auf der Box läuft bereits eine vollständige
   all-in-one-Installation mit dem Messkorpus, und sie muss stehen bleiben, weil
   die Box nach diesem Plan angehalten und für die v1.1-Messung erhalten wird
   (D-H3). Eine zweite all-in-one-Familie mit eigenem Mastercontainer,
   Datenbank, Redis und notify-push hätte auf 3,8 GiB neben der ersten nicht
   Platz gefunden, und die erste abzureissen hätte den Bestand riskiert, der die
   Grundlage der Nachmessung ist.
3. **Was all-in-one auf arm64 betrifft, ist ohnehin belegt.** Die Box fährt seit
   Plan 05-21 all-in-one auf arm64, und die Messreihen dieser Phase und der
   vorigen sind darauf entstanden. Was **nicht** belegt war, ist der
   Installationsweg aus dem Store auf arm64, und der hängt an Nextcloud, AppAPI,
   HaRP und den beiden Archiven, nicht am Abbild-Tag von all-in-one.

**Was damit nicht abgedeckt ist, ausdrücklich:** das all-in-one-Abbild
`latest-arm64` als Installationsweg, also die Weboberfläche der
ExApps-Verwaltung von all-in-one auf arm64. Wer diese Lücke schliessen will,
braucht eine eigene Box; das Skript trägt den Schalter dafür und dieser Lauf hat
ihn nicht benutzt.

### Annahme A6: der anonyme Pull, auf arm64

**Bestätigt.** Mit einem leeren Zugangsdatenspeicher, vor jeder Installation:

```
docker configuration directory /tmp/tmp.7ogR696TBN/docker-anonymous, contents:
pulled anonymously: ghcr.io/street1983nk/findling_backend@sha256:00111fd090f437a00678f6fc0a562807a5ad0b35082db235ea52ee86c63454c9
the local copy is gone, the deploy daemon has to pull it again
```

Der Digest ist zeichengleich mit dem, den die Nachmessung gemessen hat. Der Tag
`1.0.0` existiert weiterhin nicht (Befund 1 gilt unverändert), also lief der
Lauf mit `--substitute-tag dev`, und das Skript hat die Ersetzung protokolliert
und gezeigt, dass sie genau eine Zeile geändert hat.

### Der Zero-Config-Nachweis, als Zahlenreihe

| Zeitpunkt | Runde | Deckungsgrad | indexiert | eingebettet |
|---|---|---|---|---|
| 06:42:53Z | 0, vor der ersten Cron-Runde | unbekannt | 0 von 0 indexierbar | 0 |
| 06:44:46Z | 1 | unbekannt | 1 von 0 indexierbar | 1 |

```
content hit after 1 cron rounds, 113s of wall clock, which is 300s of system cron time
occ calls between the installation and the hit:
none, which is what zero config means
```

Die Installation war nach **10 occ-Aufrufen** vollständig, und zwischen dem
letzten davon und dem Inhaltstreffer stand **kein einziger**. Die zehn sind im
Protokoll einzeln aufgezählt, damit die Null nachprüfbar ist.

Der Treffer ist ein echter Inhaltstreffer und kein Namenstreffer: gesucht wurde
das Wort `florpel`, das nur im Inhalt der Datei steht, und die Antwort der
OCS-Route nennt `subline: The findling zero config proof word is florpel` mit
`highlights [[39,46]]`.

**Eine Auffälligkeit, die genannt und nicht geglättet wird.** Die Spalte
"indexierbar" steht in beiden Zeilen auf 0, während "indexiert" auf 1 springt,
also steht der Deckungsgrad als "unbekannt" statt als Prozentzahl da. Der Grund
ist die frische Instanz: der Crawl-Zähler, aus dem der Nenner kommt, hatte noch
keinen Durchgang über einen nennenswerten Bestand hinter sich, denn es gab genau
eine Datei. Der amd64-Lauf hatte hundert Dateien und deshalb die Reihe 0 von 0,
dann 0 von 100, dann 54 von 99. Für die Frage dieses Laufs ist das ohne
Bedeutung, und es ist kein Befund am Produkt, sondern die Folge eines Bestands
von einer Datei.

### Der Integritätsbeweis der Companion-Hälfte, auf arm64

Dieselben drei Prüfungen wie im amd64-Lauf, dieselbe Gegenprobe:

```
occ integrity:check-app findling: empty answer, verdict clean
tamper probe: one altered line, verdict INVALID_HASH, exit 1
restored: empty answer, verdict clean again
```

Die Gegenprobe ist der Teil, der zählt: eine angehängte Zeile in
`lib/AppInfo/Application.php` kippt das Urteil auf `INVALID_HASH` mit erwartetem
und tatsächlichem Hash, und nach dem Zurücknehmen ist die Antwort wieder leer.
Ein Integritätsurteil, das nicht rot werden kann, beweist nichts.

Die Code-Signatur trägt wie im amd64-Lauf eine Ersatzidentität (Befund 2): eine
Wegwerf-CA mit einem Blattzertifikat `CN=findling`, angehängt an
`resources/codesigning/root.crt` der Instanz, **mit** dem Zeilenumbruch davor,
den Befund 3 verlangt. Die Zählung mit Zeilenanker ergab danach 3 Zertifikate in
der Datei, also die zwei ausgelieferten plus die eigene.

### Die sechs Deinstallations-Feststellungen, auf arm64

| Zusage | Ergebnis | Dauer |
|---|---|---|
| 1. `unregister` ohne Schalter behält den Datenspeicher | Container weg, Volumen `nc_app_findling_backend_data` erhalten | 2 s |
| 2. Eine zweite Registrierung nimmt dasselbe Volumen auf | erneut registriert auf dem erhaltenen Volumen | 34 s |
| 3. `unregister --rm-data` entfernt das Volumen | Container und Volumen beide weg | 5 s |
| 4. Ein `disable` ohne Absicht behält Tabellen und Einstellungen | Tabellen vor und nach dem `disable` identisch (drei), Einstellungen 7 auf 8 | 1 s |
| 5. Ein `remove` mit Absicht räumt Tabellen und Einstellungen | danach keine Tabelle, keine Einstellung, kein Verzeichnis | 35 s |
| 6. Der Container ohne Companion tritt zurück | Container lebt, Rückzug angekündigt, drei neue Warn- oder Fehlerzeilen | 50 s |

**Alle sechs halten.** Zusage 4 und 5 sind hier mit der Tabellenhälfte gefahren
und nicht als "nicht durchgeführt" gemeldet: dem Lauf wurde ein Befehl
mitgegeben, der die `oc_findling_*`-Tabellen über PDO aus der SQLite-Datei
aufzählt, weil `sqlite3` in diesem Abbild nicht installiert ist.

Die Absichtsanzeige von `findling:purge` hat dabei ihre volle Liste gezeigt: drei
Hintergrundjobs, drei Tabellen, fünf Migrationseinträge und zehn gespeicherte
Einstellungen, und danach war alles auf null.

### Die Befunde dieses Laufs

| Befund | Was |
|---|---|
| **arm64-1** | HaRP scheitert im Container an `update-ca-certificates`: `cannot create /etc/ssl/certs/ca-certificates.crt.new: Permission denied`, Exit 2. Der Grund ist, dass das Abbild nicht als `root` läuft. Der Lauf ist dadurch **nicht** gescheitert, weder hier noch auf der AIO-Instanz derselben Box, wo dieselbe Zeile seit Tagen steht. Was dadurch nicht passiert: eine eigene CA der Instanz landet nicht im Vertrauensspeicher des Containers. Für eine Instanz mit selbst ausgestelltem Zertifikat kann das der Unterschied zwischen erreichbar und nicht erreichbar sein, und das ist ungemessen. |
| **arm64-2** | Befund 4 des amd64-Laufs gilt wörtlich auch hier und hat diesen Lauf einmal gekostet: ohne eine `location /exapps/`-Regel im Frontproxy antwortet Nextcloud selbst mit 404, AppAPI meldet `heartbeat check failed`, und `register --wait-finish` läuft in seine Grenze. Der erste Anlauf um 06:25 ist genau daran gescheitert. Die Regel gehört in jede Anleitung, die diesen Weg beschreibt; `docs/dev-setup.md` hat sie weiterhin nicht, und das bleibt der offene Teil von Befund 4. |
| **arm64-3** | Der `frpc`-Aufbau gelingt erst im zweiten Anlauf des Container-Starts. Der erste meldet `/certs/frp exists but client.crt, client.key or ca.crt is not readable by uid 1000`, konfiguriert den Tunnel ohne Client-Zertifikat und bekommt `connect to server error: EOF`; der Vorgang wird beendet (`status 143`), und der nächste Start findet die Zertifikate lesbar und baut den Tunnel mit gegenseitigem TLS auf. Das kostet rund eine halbe Sekunde und ist eine Zeitabhängigkeit zwischen HaRP und dem Container, nicht ein Fehler des Containers. Sie ist hier festgehalten, weil sie auf einer langsameren Maschine länger dauern könnte. |

### Was der arm64-Lauf gegenüber dem amd64-Lauf zeigt

| Was | amd64, 06.09.2026 | arm64, 07.09.2026 |
|---|---|---|
| Anonymer Pull (A6) | bestätigt | bestätigt, derselbe Weg, anderer Digest |
| Integritätsurteil und Gegenprobe | leer, kippt, wieder leer | leer, kippt, wieder leer |
| Routen aus dem Archiv | 5 | 5 |
| occ-Aufrufe bis zur fertigen Installation | 10 | 10 |
| occ-Aufrufe zwischen Installation und Treffer | 0 | 0 |
| Erster Inhaltstreffer | nach 2 Cron-Runden | nach 1 Cron-Runde |
| Deinstallations-Zusagen | 6 von 6 | 6 von 6 |
| Gesamtdauer | 9 min 57 s | 4 min 51 s |

**Keine einzige Feststellung des amd64-Laufs kippt auf arm64.** Die Architektur
ist an dieser Stelle kein Unterschied, und das ist die Aussage, die Kriterium 3
der ROADMAP gebraucht hat.
