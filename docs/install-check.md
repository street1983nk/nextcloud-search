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

**Eine Warnung, bevor die frische Instanz entsteht:** hängt sie am selben
Docker-Dienst wie eine Instanz, deren Bestand gebraucht wird, dann teilen sich
beide das Datenvolume der ExApp, und die Deinstallations-Feststellungen dieses
Laufs nehmen den Index der anderen Instanz mit. Warum das so ist und was
dagegen hilft, steht in `docs/uninstall.md`, Abschnitt "Zwei Instanzen an einem
Docker-Dienst teilen das Volume".

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
| **arm64-2** | Befund 4 des amd64-Laufs gilt wörtlich auch hier und hat diesen Lauf einmal gekostet: ohne eine `location /exapps/`-Regel im Frontproxy antwortet Nextcloud selbst mit 404, AppAPI meldet `heartbeat check failed`, und `register --wait-finish` läuft in seine Grenze. Der erste Anlauf um 06:25 ist genau daran gescheitert. **Richtigstellung vom 07.09.2026, nachgetragen bei der Abnahme:** dieser Befund hat in seiner ersten Fassung behauptet, `docs/dev-setup.md` trage die Regel weiterhin nicht. Das war falsch. Der Abschnitt "Eine Adresse vor Nextcloud und HaRP" steht dort seit Plan 06.1-22, mit derselben Begründung über die zwei Verwendungen von `nextcloud_url` und mit der `location /exapps/`-Regel als Konfiguration (`docs/dev-setup.md`, Abschnitt ab Zeile 346). Der dokumentarische Teil von Befund 4 ist damit **geschlossen** und war es schon, als dieser Lauf fuhr; die Anleitung stand im Basisstand dieses Plans, und ein Blick hinein hätte den Anlauf um 06:25 verhindert. Was bleibt, ist die Feststellung, dass die Regel nötig ist, und sie ist hier ein zweites Mal belegt. |
| **arm64-4** | **Der schwerste Befund dieses Laufs, und er hat Daten gekostet.** Zusage 3 fuehrt `app_api:app:unregister --rm-data` aus. Der Name des Volumens leitet sich **allein aus der App-Kennung** ab (`nc_app_findling_backend_data`), und beide Nextcloud-Instanzen dieser Box hingen am **selben Docker-Dienst**. Der Lauf hat damit um 06:46Z das Volumen der **anderen**, produktiv genutzten Instanz gelöscht: `state.db`, `vectors.db`, den 785 MB grossen Tantivy-Index und die Wortliste des Messkorpus. Details, Schadensumfang und Wiederaufsatz stehen im Messbericht der Nachmessung. **Was das für jeden Betreiber bedeutet:** wer eine zweite Nextcloud zum Ausprobieren neben einer echten betreibt und beide am selben Docker-Dienst hängen lässt, kann mit einer Deinstallation in der Testinstanz den Datenbestand der echten löschen. Das ist kein Fehler dieser App und keiner dieses Skripts: der Volumenname ist eine Festlegung von AppAPI, und `--rm-data` tut genau, was es ankündigt. Es ist eine Falle der Topologie, sie ist hier zum ersten Mal ausgelöst worden, und sie gehört in jede Anleitung, die einen Testlauf neben einer echten Instanz beschreibt. |
| **arm64-5** | Nach dem Verlust des Volumens durch arm64-4 blieb in der **anderen** Instanz eine AppAPI-Zeile ohne Container zurück. `app_api:app:unregister` scheitert dann mit `Failed to remove ExApp findling_backend` und nennt in seinem Hinweis selbst die Abhilfe: `--force`. Damit liess sich die Instanz sauber neu aufsetzen. Der Hinweis von AppAPI ist an dieser Stelle gut, und er ist hier festgehalten, weil ein Verwalter, der einen ExApp-Container von Hand entfernt hat, in genau dieselbe Lage kommt. |
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

## 6. Die Sichtprobe des Owners vom 07.09.2026 (D-H5)

Dieser Abschnitt ist das Protokoll des Abnahmegates der Phase 06.1. Die beiden
Läufe oben sind Fahrpläne, die eine Maschine abgeht. Dieser Schritt stellt die
Frage, die kein Gate stellt: sieht das aus wie etwas, das man installieren will,
und tut es, was es verspricht.

### Die Archive: aus dem Probelauf, nicht aus dem Arbeitsbaum

Das ist der Kern von D-H5, deshalb steht es zuerst.

| Was | Wert |
|---|---|
| Probelauf | `release.yml` über `workflow_dispatch`, Lauf `34116531030`, Zweig `main` bei Stand `94420f7`, gestartet am 07.09.2026 um 11:35 UTC |
| Erzeugtes Release | **keines**. `create_release` stand auf seiner Vorgabe `false`, und der Release-Schritt verlangt zusätzlich einen `v`-Tag (T-05-77) |
| Companion-Archiv | `findling.tar.gz`, 234090 Bytes, SHA-256 `5f83ea92c15ce0ab5657d97c8c9aa2e86ea810c79dd4e446f8482c7ac7ba2bc3` |
| Backend-Archiv | `findling_backend.tar.gz`, 29112 Bytes, SHA-256 `8ea9a88f3bc57d956694627c6fac84b241c8e2d5aa22386d08e5bc61ac1303cc` |
| Signaturdateien | `findling.tar.gz.sig` und `findling_backend.tar.gz.sig`, je 684 Bytes |

**Was dieser Lauf gegenüber dem 06.09. neu belegt, und es ist die eine Hälfte,
die keine CI belegen kann:** die Code-Signatur trägt hier **keine
Ersatzidentität**. Das Zertifikat in `findling/appinfo/signature.json` lautet

```
subject: CN=findling
issuer:  CN=Nextcloud Code Signing Intermediate Authority, O=Nextcloud GmbH,
         ST=Baden-Wuerttemberg, C=DE
gueltig: 19.08.2026 bis 24.11.2036
```

Die frische Instanz hat es gegen die `resources/codesigning/root.crt` geprüft,
die Nextcloud 34.0.3 selbst mitbringt, **ohne dass an dieser Datei etwas
angehängt wurde**. Befund 3 des amd64-Laufs entfällt damit für diesen Lauf, und
Befund 2 ebenfalls: `occ integrity:check-app findling` antwortet leer, also
sauber, und eine einzige geänderte Zeile in `lib/AppInfo/Application.php` kippt
das Urteil auf `INVALID_HASH`. Danach ist die Datei zurückgestellt und das Urteil
wieder sauber.

### Die Instanz

| Was | Wert |
|---|---|
| Wirt | Windows 11, Docker Engine 29.5.2, WSL2, **12 CPUs** |
| Nextcloud | 34.0.3.2, Abbild `nextcloud:34.0.3-apache`, SQLite |
| Weg | docker compose, drei Dienste: Nextcloud, HaRP, ein Frontproxy (`nginx:1.27-alpine`) |
| Port | **8097**. 8090 trägt den Alltagsstack dieser Maschine, 8080 gehört einer anderen Sitzung; beide sind unberührt |
| AppAPI | 34.0.0, mit dem Server ausgeliefert |
| HaRP | `ghcr.io/nextcloud/nextcloud-appapi-harp`, festgenagelt auf `sha256:603fdf5c...`, dieselbe Zeichenkette wie in `deploy-harp.yml` |
| Deploy-Daemon | `harp_sicht_compose`, `docker-install`, HaRP an `harp:8780`, `nextcloud_url` auf den Frontproxy |
| Abbild | `ghcr.io/street1983nk/findling_backend:dev`, Digest `sha256:f32af191ca87ff1dbe071c6c545300619f2a8e7ef8e9aeda9b193ebe8a6bcc79` |
| Konten | `admin` für die Verwaltungsseite, `testuser` für Hochladen und Suchen |
| Lockstep | `match`, Companion 1.0.0, Container 1.0.0 |

Die **zwölf CPUs des Wirts** stehen nicht aus Ordnungsliebe in dieser Tabelle.
Sie sind die Ursache des Befundes 8 weiter unten, und sie sind der Grund, warum
dieser Befund fünf Phasen lang unentdeckt blieb.

### Zwei Instanzen, und warum es zwei sein mussten

Es sind zwei Instanzen nacheinander entstanden, jede aus einem leeren
Docker-Zustand (`compose down -v`, danach `compose up`).

1. **Die Fahrplan-Instanz.** Auf ihr lief `scripts/dev/aio_install_check.sh`
   vollständig: Vorprüfung, anonymer Pull, Companion aus dem Archiv samt
   Fälschungsprobe, ExApp aus dem Archiv, Zero-Config-Nachweis und **alle sechs
   Deinstallations-Zusagen**. Ergebnis: `SUMMARY: all six uninstall promises hold
   on this instance`. Protokoll: `.dev/sichtprobe/install-check-sichtprobe.log`.
2. **Die Instanz des Owners.** Auf ihr laufen nur die Schritte 2 und 3 desselben
   Fahrplans, wörtlich in ihren Befehlen. Die Deinstallations-Zusagen sind hier
   bewusst **nicht** wiederholt: sie reissen die Installation ab und bauen sie
   wieder auf, und eine abgerissene und wieder aufgebaute Instanz ist nicht die
   Instanz, nach der D-H5 fragt.

Vor der Installation ist geprüft und nicht angenommen worden, dass kein anderes
`nc_app_findling_backend_data`-Volume auf dieser Maschine existiert. Es existiert
keines: der Alltagsstack auf Port 8090 läuft über `manual-install` und legt kein
ExApp-Volume an. Das ist die Warnung aus `docs/uninstall.md`, Abschnitt "Zwei
Instanzen an einem Docker-Dienst teilen das Volume", und sie ist hier abgehakt
statt überlesen.

### Der Zero-Config-Nachweis, als Zahlenreihe

Auf der Fahrplan-Instanz, mit `--cron-driver script` und 300 s Takt:

| Runde | Zeit | Deckung |
|---|---|---|
| 0, vor der ersten Cron-Runde | 12:00:38Z | indexed 0, embedded 0 |
| 1 | 12:01:19Z | indexed 41, embedded 41 |

**Inhaltstreffer nach einer Cron-Runde, 42 s Wanduhr.** Zwischen dem Ende der
Installation und dem ersten Treffer: `occ calls between the installation and the
hit: none, which is what zero config means`. Zehn occ-Aufrufe brauchte die
Installation, danach keiner.

### Die fünf Dokumente, die der Owner durchsucht

Nicht aus dem Referenzkorpus, und das ist Absicht: dessen Dateien heissen
`09-bescheid.pdf` bis `39-...` und zehn von ihnen sind absichtlich beschädigt,
weil der Fehlerweg das ist, worauf dieses Projekt geprüft wird. Eine Sichtprobe
braucht das Gegenteil. Erzeugt von
`.dev/sichtprobe/stack/build_sichtprobe_docs.py`, jedes Dokument erfunden, kein
Name und keine Adresse darin echt.

Jedes Suchwort steht **nur im Inhalt** und in keinem Dateinamen. Ein Wort, das
auch im Namen stünde, ergäbe einen Treffer der Dateiliste und keinen dieser App.

| Datei | Art | Suchwort | Gefunden am 07.09. |
|---|---|---|---|
| `protokoll-hausversammlung.txt` | Klartext | `Fahrradstellplatzsatzung` | **ja**, mit Auszug |
| `angebot-heizungstausch.pdf` | PDF mit Textschicht | `Heizlastberechnung` | **ja**, mit Auszug |
| `scan-bescheid.pdf` | PDF **ohne** Textschicht, ein Bild einer Seite | `Zweitwohnungsteuer` | **ja**, mit Auszug, also über OCR |
| `2026-04-mietvertrag.docx` | DOCX | `Winterdienstpauschale` | **nein**, siehe Befund 8 |
| `nebenkosten-2025.xlsx` | XLSX | `Grundsteuermessbetrag` | **nein**, siehe Befund 8 |

Der Scan ist mit `pypdfium2` gegengeprüft: er liefert **0 Textzeichen**, die
Textschicht-Datei 345. Der Treffer auf dem Scan kann also nur aus der
Texterkennung kommen und aus nichts anderem.

Die Deckung am Ende, aus der Verwaltungsseite gelesen:

```
coverage: indexed 85 von 100 indexierbar, 85 Prozent, embedded 83
skipped 16: empty_text 14 (die Beispielfotos), image_not_ocrable 2
failed  4: corrupt 4 (siehe Befund 8)
indexBytes 743426, runState idle, backendReachable true
```

### Die Gastnutzer-Probe

Gefahren auf derselben Instanz, vor dem Hochladen der fünf Dokumente, weil die
Probe den Index ausdrücklich antreibt und die Zero-Config-Aussage über die
Dokumente des Owners eine Aussage über den gewöhnlichen Cron-Weg bleiben soll.
Ergebnis: **bestanden**, vier Vergleiche, `guests` 4.9.0. Der Vorab-Vergleich des
Eigentümers ist neu und schliesst DI-06.1-17. Die Einzelheiten stehen in
`docs/testing.md`, Abschnitt "The guest user probe".

### Befund 8: Jedes Office-Dokument meldet sich als beschädigt, ab genügend CPU-Kernen

**Der wichtigste Fund dieser Phase, und genau der Fund, für den D-H5 existiert.**
Er ist von keinem Test und von keiner Messung dieser oder der vier vorigen Phasen
gesehen worden.

**Was zu sehen ist:** Auf einer frischen Nextcloud melden
`2026-04-mietvertrag.docx` und `nebenkosten-2025.xlsx` den Endzustand `failed`,
Grund `corrupt`, Beschriftung "File damaged". Und nicht nur die beiden: **auch
`Documents/Welcome to Nextcloud Hub.docx`, das Nextcloud selbst mitbringt.** Das
Erste, was ein Selfhoster nach der Installation auf der Verwaltungsseite sieht,
ist also eine Fehlergruppe über sein eigenes Willkommensdokument.

**Die Ursache, gemessen und nicht erschlossen:**

1. `findling/extract/office.py` importiert `openpyxl` auf Modulebene.
2. `openpyxl.compat.numbers` importiert `numpy` bedingungslos.
3. `numpy` lädt OpenBLAS.
4. OpenBLAS startet **einen Arbeitsthread je CPU**, hier also zwölf.
5. Jeder dieser Threads will einen Stapel im Adressraum, den
   `_limit_address_space` unmittelbar davor über `RLIMIT_AS` auf 512 MB begrenzt
   hat. `pthread_create` scheitert.
6. Der `numpy`-Import bricht mitten drin ab, und `dispatch` bildet die unbekannte
   Ausnahme auf `failed(corrupt)` ab.

Der Container hat es selbst protokolliert, und OpenBLAS nennt darin seine eigene
Abhilfe:

```
OpenBLAS blas_thread_init: pthread_create failed for thread 10 of 12:
  Resource temporarily unavailable
OpenBLAS blas_thread_init: ensure that your address space and process count
  limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS
```

Nachgestellt in drei Stufen, jede im laufenden Container:

| Stufe | Ergebnis |
|---|---|
| `office.extract_docx` direkt, ohne Prozessgrenze | `indexed`, 495 Zeichen |
| `extract_guarded` mit `RLIMIT_AS` 512 MB | `failed(corrupt)`, 0 Zeichen |
| `import numpy` unter `RLIMIT_AS` 512 MB mit `OPENBLAS_NUM_THREADS=1` | Import gelingt, danach `indexed`, 495 Zeichen |

**Warum es fünf Phasen überlebt hat:** die Threadzahl folgt der CPU-Zahl. Auf der
Messbox mit zwei vCPU und auf einem Runner mit vier passen die Stapel unter die
Grenze, also ist jeder Test und jede Messung grün geblieben, während derselbe
Code auf einer gewöhnlichen Entwicklermaschine und auf jedem selbst gehosteten
Server mit genügend Kernen scheitert. Kein Gate war falsch; die Maschinen waren
zu klein, um die Grenze zu erreichen.

**Der Fix** steht im Repository und ist am laufenden Container bewiesen:
`_pin_native_thread_pools()` in `findling/extract/sandbox.py` setzt
`OPENBLAS_NUM_THREADS`, `OMP_NUM_THREADS`, `MKL_NUM_THREADS` und
`NUMEXPR_NUM_THREADS` auf 1, **nach** der Adressraumgrenze und **vor** dem Import
des Dispatchers, weil diese Variablen beim Initialisieren der Bibliothek gelesen
werden. Drei Tests in `backend/tests/test_sandbox.py` halten ihn: die Variablen,
die Reihenfolge, und ein DOCX über den echten Kindprozess. Der dritte trägt seine
eigene Grenze im Text: er ist nur auf einer Maschine mit genügend Kernen eine
Ratsche, und genau deshalb prüfen die ersten zwei den Mechanismus statt des
Ergebnisses.

**Was der Owner auf dieser Instanz sieht, und warum:** der Fix liegt im Quellcode
und **nicht im veröffentlichten Abbild**. Das Abbild
`ghcr.io/street1983nk/findling_backend:dev` entsteht in `docker.yml` beim Push auf
`main`, also erst nach dem Merge dieses Plans. Die Instanz des Owners läuft
deshalb bewusst auf dem **unveränderten** Abbild: sie zeigt, was das
veröffentlichte Abbild heute tut, und nicht, was der Arbeitsbaum kann. Ein von
Hand in den Container kopierter Fix hätte die Sichtprobe zu einer Probe über
einen Arbeitsbaum gemacht, und das ist genau das, was D-H5 ausschliesst. Der
Container ist nach der Nachstellung aus dem Abbild neu erzeugt worden;
`docker diff` zeigt am Paket `findling` keine einzige Änderung.

### Was diese Sichtprobe nicht abdeckt

Die Liste in Abschnitt 3 gilt unverändert weiter. Dazu kommen zwei Punkte, die
nur diesen Lauf betreffen:

1. **Der Tag `1.0.0` existiert noch nicht.** Wie im amd64-Lauf ist gegen `dev`
   installiert worden, mit genau einer ersetzten Zeile in der `info.xml` des
   Archivs. Befund 1 gilt fort: erst der Lauf nach dem Release-Tag geht den Weg
   vollständig.
2. **Die beiden `info.xml`-Änderungen dieses Plans sind in diesen Archiven nicht
   enthalten.** Der Probelauf lief auf `main` bei `94420f7`, also vor der
   Umstellung der Lizenz auf `AGPL-3.0-or-later` und vor der verankerten
   Routenform `^/<name>$`. Die Archive tragen nachweislich noch
   `<licence>agpl</licence>` und die nackten Routennamen. Beide Änderungen
   berühren nichts auf dem Weg, den der Owner besieht: die Lizenz ist
   Store-Metadatum, und der Routenblock regiert allein den unsignierten
   Direktzugriff, den kein Teil des Produkts benutzt (DI-06.1-13). Der Ort, an dem
   die verankerte Form gemessen wird, ist der `deploy-harp`-Job des CI-Laufs nach
   dem Merge; bis dahin ist "der Block passt jetzt zu dem, was er nennt" eine
   Aussage über einen regulären Ausdruck und keine Messung.

### APPSTORE_TOKEN: rotiert am 07.09.2026 um 11:01:21Z

Pflichtpunkt 8 der Launch-Haertung, und er ist erledigt, bevor irgendetwas
eingereicht wird. Das Token stand einmal im Gespraech und war damit im Umlauf.
Der Betreiber hat es am 07.09.2026 ersetzt und das alte widerrufen; ein
ersetztes Token, das noch gilt, waere kein rotiertes Token.

Nachgeprueft und nicht geglaubt: `gh secret list` fuehrt `APPSTORE_TOKEN` mit
dem Zeitstempel `2026-09-07T11:01:21Z`, also mit dem Zeitpunkt der Rotation und
nicht mit einem aelteren. Der Wert selbst existiert ausschliesslich im
Secret-Store von GitHub und steht in keinem Artefakt dieses Repositories, auch
nicht in einer Zusammenfassung.

### Wie diese Sichtprobe zu wiederholen ist

Die Skripte liegen unter `.dev/sichtprobe/stack/` und sind nicht Teil der
Auslieferung:

| Datei | Aufgabe |
|---|---|
| `compose.yaml` | die drei Dienste, ohne jeden Bind in einen Arbeitsbaum |
| `exapps-proxy.conf` | der Frontproxy, `/exapps/` in den Tunnel, alles andere an den Server |
| `prepare.sh` | Erstlauf-Assistent aus, `testuser`, `guests`, Deploy-Daemon, Tabellenleser |
| `run-install-check.sh` | der vollständige Fahrplan aus `scripts/dev/aio_install_check.sh` |
| `install-for-owner.sh` | nur die Schritte 2 und 3, für die Instanz des Owners |
| `build_sichtprobe_docs.py` | die fünf deutschen Dokumente |
| `upload-docs.sh` | die Dokumente über WebDAV als `testuser` |
| `run-guest-parity.sh` | die Gastnutzer-Probe |
| `drive-cron.sh` | `cron.php` in Runden, mit einer Zahlenreihe je Runde |

Jedes Passwort steht in `.env` und in keiner Argumentliste (DI-06.1-18).
`MSYS2_ARG_CONV_EXCL` nennt in jedem dieser Skripte genau die Pfade, die dem
Container gehören, und nicht `*`: eine pauschale Ausnahme lässt die
Konfigurationsdateien scheitern, die das native curl dieses Wirts unter `/tmp`
der Shell liest. Befund 7 gilt hier zweimal, und die zweite Ausprägung
(`path=/...` als Optionswert) hat einen Lauf der Gastnutzer-Probe gekostet.

## 7. Die Wiederholung am neuen Abbild, 07.09.2026 (Weg B des Owners)

Der Owner hat am Checkpoint Weg **B** gewählt: erst das neue Abbild, dann die
Sichtprobe. Die Phase wird also auf dem Zustand abgenommen, den der Fix wirklich
erreicht hat, und nicht auf einem, der ihn nur im Quellcode hat. Dieser Abschnitt
ist das Protokoll dieser zweiten Runde.

### Was sich zwischen den beiden Runden geändert hat

| Was | Runde 1 (Abschnitt 6) | Runde 2 |
|---|---|---|
| Merge | offen | `main` bei `569f0a6`, konfliktfrei |
| Laufzeit-Abbild | `sha256:f32af191...`, ohne den Fix | neu gebaut von `docker.yml`, gezogen als `sha256:025ced73...` |
| Companion-Archiv | `findling.tar.gz` 234090 B, SHA-256 `5f83ea92...` | 234349 B, SHA-256 `1540dce4232e5313ca8d4c774246af3ea6e493c879783fc1f64f1b300e1fdaed` |
| Backend-Archiv | 29112 B, SHA-256 `8ea9a88f...` | 29604 B, SHA-256 `52c4bcff9f480e6e6417242b1e2e4512c1fd299cb954f7bd033c2e01920a0dbe` |
| Probelauf | `34116531030` auf `94420f7` | `34127041571` auf `569f0a6`, ebenfalls ohne Release |
| Lizenz im Archiv | `agpl` | **`AGPL-3.0-or-later`** |
| Routen im Archiv | nackte Namen | **`^/search$` bis `^/diagnose$`** |

Damit ist die zweite Nichtabdeckung aus Abschnitt 6 erledigt: die Instanz trägt
jetzt genau die beiden `info.xml`-Änderungen dieses Plans, und die Sichtprobe
findet auf dem Zustand statt, der eingereicht wird.

Das alte Abbild ist vor der Neuinstallation lokal gelöscht worden
(`docker rmi`, bestätigt mit dem Digest `f32af191...`), damit der Deploy-Daemon
das neue selbst ziehen muss und nicht eine liegengebliebene Kopie benutzt. Der
Fix ist im laufenden Container nachgezählt: `_pin_native_thread_pools` kommt in
`sandbox.py` des Containers zweimal vor, als Funktion und als Aufruf.

Beide Hälften sind ersetzt, nicht nur der Container. Die Companion-Hälfte ist
abgeschaltet, das Verzeichnis entfernt, aus dem neuen Archiv entpackt und wieder
eingeschaltet; `occ integrity:check-app findling` antwortet danach wieder leer,
also sauber. Bewusst kein `occ app:remove`: das räumt Tabellen und Einstellungen
(Deinstallations-Zusage 5), und hier ging es um einen neuen Bau auf einer
laufenden Instanz und nicht um eine Erstinstallation. Die Aussage über die
Erstinstallation steht in Abschnitt 6 und bleibt dort.

Der Index ist mit `occ findling:index --restart` neu aufgebaut, dem Befehl, den
die Verwaltungsseite selbst als `rules.restartCommand` nennt. Das ist ein
getriebener Schritt und keine Zero-Config-Aussage: ohne ihn wären die Urteile des
alten Baus stehen geblieben, einschliesslich der vier `corrupt`, die diese Runde
widerlegen soll.

### Kontrollergebnis 1: die Suche

`occ findling:index --restart`, danach `cron.php` in Runden. Die Zahlenreihe, je
Runde ein Treffer pro Suchwort:

| Runde | Zeit | Warteschlange | Gefunden |
|---|---|---|---|
| 1 | 13:26:39Z | 0 | 0 von 5 |
| 2 | 13:27:04Z | 103 | 0 von 5 |
| 3 | 13:27:34Z | 93 | 4 von 5 |
| 4 | 13:28:31Z | 15 | 4 von 5 |
| 5 | 13:28:55Z | 0 | **5 von 5** |

| Suchwort | Datei | Runde 1 (altes Abbild) | Runde 2 (neues Abbild) |
|---|---|---|---|
| `Winterdienstpauschale` | `2026-04-mietvertrag.docx` | **kein Treffer** | **1 Treffer** |
| `Grundsteuermessbetrag` | `nebenkosten-2025.xlsx` | **kein Treffer** | **1 Treffer** |
| `Fahrradstellplatzsatzung` | `protokoll-hausversammlung.txt` | 1 Treffer | 1 Treffer |
| `Heizlastberechnung` | `angebot-heizungstausch.pdf` | 1 Treffer | 1 Treffer |
| `Zweitwohnungsteuer` | `scan-bescheid.pdf` (OCR) | 1 Treffer | 1 Treffer |

**Befund 8 ist damit am veröffentlichten Abbild widerlegt.** Die beiden
Office-Dokumente, die vorher "File damaged" meldeten, sind über ihren Inhalt
findbar, und die drei Wege, die schon vorher trugen, tragen weiter.

### Kontrollergebnis 2: die Verwaltungsseite

| Zahl | Runde 1 | Runde 2 |
|---|---|---|
| indexiert | 85 | **87** |
| indexierbar | 100 | 103 |
| Deckung | 85 Prozent | 84 Prozent |
| eingebettet | 83 | **87** |
| übersprungen | 16 | 16 |
| **fehlgeschlagen (Container)** | **4** | **0** |
| Fehlergründe des Containers | `corrupt 4` | **keine** |
| Indexgrösse | 743.426 Byte | 851.188 Byte |
| Lockstep | `match`, 1.0.0 / 1.0.0 | `match`, 1.0.0 / 1.0.0 |

Die Deckung sinkt um einen Prozentpunkt und steigt in absoluten Zahlen, und beides
ist richtig: der Nenner ist von 100 auf 103 gewachsen, weil die Markerdateien der
Gastnutzer-Probe und ihr Gastkonto zwischen den Runden entstanden und wieder
entfernt wurden. `87 von 103` sind 84,5 Prozent.

**Die Gruppe "4 beschädigte Dateien" steht auf der Seite weiter, und das ist der
nächste Befund.**

### Befund 9: ein einmal gefälltes Fehlurteil der PHP-Hälfte wird von einem späteren Erfolg nicht widerrufen

**Was zu sehen ist:** Die Zähler oben sagen `fehlgeschlagen 0`, die Fehlergruppe
darunter sagt `File damaged, 4`. Beide Zahlen kommen aus verschiedenen Hälften:
die Zähler aus dem Container, die Gruppen aus `oc_findling_file_state` der
PHP-Hälfte. Die Einzelabfrage bestätigt es:

```
GET /apps/findling/admin/diagnose?ref=183
  path      2026-04-mietvertrag.docx
  state     failed
  reason    corrupt
  checkedAt 1788783247   (12:14:07Z, also aus dem alten Bau)
```

Die Datei ist zu diesem Zeitpunkt über ihren Inhalt findbar. Der Zeitstempel der
Zeile ist der alte; der erfolgreiche Lauf um 13:28Z hat sie nicht angefasst.

**Warum es so gebaut ist:** Die PHP-Hälfte schreibt `indexed` bewusst nie, das
sagt `occ findling:index` selbst ("indexed is counted by the backend container
and never written here"). Sie hält nur die Endzustände `skipped` und `failed`.
Eine Zeile, die einmal `failed` sagt, hat damit niemanden, der sie widerruft.

**Was daran mildert:** Die vier Zeilen sind als `resolved` markiert, und
`rules.cleanupLatencyHours` steht auf 24. Die Aufräumung entfernt sie also
spätestens nach einem Tag. Was nicht geprüft ist: ob diese Aufräumung eine Zeile
auch dann entfernt, wenn die Datei noch existiert und inzwischen erfolgreich
indexiert ist, oder nur dann, wenn sie verschwunden ist.

**Warum es hier nicht behoben wird:** Die Abhilfe liegt in der PHP-Hälfte und ist
eine Verhaltensänderung: entweder meldet der Container die erfolgreichen
Dateikennungen zurück, damit die PHP-Hälfte die Zeile löschen kann, oder die
Zeile fällt schon beim Wiedereinreihen einer Datei, weil ihr Endzustand dann
nicht mehr aktuell ist. Das ist die zweite Möglichkeit und die kleinere, aber
beide sind mehr als ein Fix am Rand einer Abnahme. Der Befund ist deshalb
benannt, nicht stillschweigend behoben.

**Was ein Nutzer davon merkt:** Wer die Abhilfe befolgt, die die Seite selbst
nennt ("Check the file outside of Nextcloud and upload it again"), findet die
Datei danach über die Suche und liest auf der Verwaltungsseite weiter, sie sei
beschädigt. Auf der Seite, deren Aufgabe die Diagnose ist, ist das die falsche
Aussage.

### Befund 10: die Routenprüfung der CI war nicht falsch, ihre Erwartung war alt

Der `deploy-harp`-Lauf nach dem Merge (`34126702669`) war auf allen drei Zeilen
rot, und der Ort war genau der, den dieser Plan als Beweisort benannt hatte.
Gemessen hat er das Richtige:

```
oc_ex_apps_routes after the archive registration:
  ^/diagnose$:GET:2 ^/rates$:GET:2 ^/search$:POST:1 ^/snippets$:POST:1 ^/status$:GET:2
```

Das ist die verankerte Form, aus dem Archiv gelesen und von AppAPI in die Tabelle
geschrieben, also **die Bestätigung, dass die Umstellung ankommt**. Rot war der
Schritt, weil die erwartete Zeichenkette daneben noch die nackten Namen trug: sie
steht als Literal im Workflow, und dieser Plan hat sie beim Umstellen der Routen
nicht mitgezogen.

Der Fix ist mehr als das Nachziehen des Literals, weil ein einzelnes Literal
genau diese Verwechslung nicht auffangen kann. Der Schritt stellt jetzt zwei
Fragen:

1. Stimmt die Tabelle mit dem überein, was das Archiv erklärt? Die Erwartung wird
   dafür aus dem eben installierten Archiv gelesen. Das ist die Frage, für die der
   Schritt gebaut wurde.
2. Erklärt das Archiv genau die fünf geprüften Routen? Das bleibt ein Literal,
   damit eine sechste Route oder eine gelockerte Zugriffsstufe eine Entscheidung
   bleibt, die auch hier getroffen werden muss.

Beide Richtungen sind vor dem Commit an echten Archiven durchgespielt: das Archiv
des gemergten `main` trifft, das ältere mit den nackten Namen fällt durch.

**Was noch offen ist:** die Bestätigung, dass der Schritt danach grün läuft. Sie
kann nur aus dem nächsten `deploy-harp`-Lauf kommen, also nach dem Merge dieser
Runde. Bis dahin ist der Beweis der verankerten Routenform vollständig für "die
Form kommt in der Tabelle an" und offen für "der Job ist darüber grün".

### Befund 11: die Instanz war für Menschen unbenutzbar, während jede API-Prüfung grün war

Gefunden, als der Owner sich anmeldete: nach dem Login leitete Nextcloud den
Browser auf Port 80 um, und er sah `ERR_CONNECTION_REFUSED`. Gleichzeitig
antworteten die Suche, die Verwaltungsseite und jede Prüfung dieses Protokolls,
weil sie über Basic Authentication laufen und die vollständige Adresse in jeder
Anfrage mitführen.

Die Ursache liegt nicht bei Findling und nicht bei
`scripts/dev/aio_install_check.sh`, sondern im Aufbau: das Server-Abbild lässt
`overwrite.cli.url` auf `http://localhost` **ohne Port** stehen, wenn die
compose-Datei `OVERWRITECLIURL` nicht setzt, und ein Browser folgt genau dieser
Adresse. Auf der Instanz stehen jetzt `overwrite.cli.url`,
`overwritehost` und `overwriteprotocol` auf `localhost:8097`; das ist eine
Einstellung des Testbetts und berührt keine Findling-Datei.

Zwei Stellen sind trotzdem nachgezogen, weil ein Lauf, der grün ist und dessen
Instanz kein Mensch benutzen kann, genau die Form von Befund ist, die diese Phase
beseitigen soll:

- `scripts/dev/aio_install_check.sh` liest in der Vorprüfung
  `overwrite.cli.url` und meldet einen **Befund**, wenn er nicht zu `--url` passt.
  Ausdruecklich kein Abbruch: eine Instanz, die nur über API gefahren wird, ist so
  zulässig eingerichtet, und die Abhilfe gehört dem, der sie aufgesetzt hat.
- der Wegwerf-Stack der Sichtprobe setzt `OVERWRITECLIURL`, `OVERWRITEHOST` und
  `OVERWRITEPROTOCOL` aus dem Port, damit dieselbe Falle sich nicht wiederholt.

### Die Abnahme, 07.09.2026

**Der Owner hat die Launch-Haertung abgenommen.** Der Wortlaut, zitiert und nicht
zusammengefasst:

> ok abgenommen weiter der rest wie deine empfehlung

Damit ist **D-H5 erfuellt**: der Owner hat auf einer frisch installierten
Nextcloud, die beide Haelften ueber den Store-Weg aus den Release-Archiven
bekommen hat, selbst gesucht und gefunden. Er hat die Treffer der fuenf Suchwoerter
einschliesslich der beiden Office-Dokumente und die Verwaltungsseite im Browser
gesehen, in der zweiten Runde und damit auf dem Abbild, das den Fix des Befundes 8
wirklich traegt. Die Bildschirmaufnahmen liegen beim Orchestrator.

Zwei Punkte hat er im selben Zug mitentschieden, und beide sind damit von der
Abnahme gedeckt statt Nacharbeit hinter ihr:

| Punkt | Entscheidung |
|---|---|
| Befund 9, das stehengebliebene `failed`-Urteil der PHP-Haelfte | wird **vor der Abgabe** behoben, in einem eigenen Plan |
| Die Regressionsluecke, durch die Befund 8 fuenf Phasen fiel (kein Integrationsjob fuehrt ein Office-Dokument ueber den bewachten Pfad auf einer vielkernigen Maschine) | wird **vor der Abgabe** geschlossen, im selben Plan |

Beides legt der Orchestrator als Plan 06.1-24 an. Erst danach beginnt Plan 06-12,
die gebuendelte Abgabe des Erstrelease.

Die Instanz auf Port 8097 bleibt zunaechst stehen, damit der Owner weiter
ausprobieren kann; ihr Abbau ist Sache des Orchestrators und nicht dieses Plans.
