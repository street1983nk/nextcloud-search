---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 07
subsystem: search
tags: [lockstep, versionierung, appapi, admin-ui, degradation, dev-tooling, textgate]

# Dependency graph
requires:
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: die Statusseite mit ihrem Zustandsmuster, ExAppService::adminGet und die Antwortform von GET /status
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: 05-01, dessen Composite Action die App-Version schon aus der info.xml liest statt aus einem Vorgabewert
provides:
  - appVersion in GET /status, aus der von AppAPI gesetzten Umgebungsvariablen
  - ExAppService::lockstep und ExAppService::driftOnRecord, die Major-Minor-Pruefung von D-11
  - leeres Suchergebnis mit Logmeldung statt stummer Treffer bei Versionsdrift
  - benannter Zustand in Block 1 der Admin-Seite, mit beiden gemeldeten Versionsnummern
  - backend/tests/test_lockstep_versions.py als Gate ueber beide info.xml und den image-tag
  - register-exapp.sh registriert alle Routen der info.xml und startet einen veralteten Host-Prozess neu
affects: [05-17 Versionsbump auf das Store-Erstrelease, PKG-05, DI-04-01, DI-04-02]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Ein Vergleich zwischen den beiden Haelften wird auf der Antwort gefuehrt, die der Aufrufer schon hat, nie mit einem zweiten Roundtrip
    - Ein Wert von jenseits der Vertrauensgrenze wird gegen ein Muster geprueft, bevor er verglichen oder angezeigt wird; was nicht passt, ist unbekannt und nie ein Verdikt
    - Ein Bannertext, den das Skript schreiben muss, bekommt eine eigene Id am Textknoten, damit textContent das Symbol nicht mitloescht
    - Eine Liste, die zwei Orte gleich halten muessen, wird an einem Ort gelesen und am anderen gebaut, nicht zweimal geschrieben

key-files:
  created:
    - backend/tests/test_lockstep_versions.py
  modified:
    - backend/src/findling/api/status.py
    - backend/tests/test_status_endpoint.py
    - scripts/dev/register-exapp.sh
    - php/lib/Service/ExAppService.php
    - php/lib/Search/Provider.php
    - php/lib/Service/AdminViewService.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/l10n/de.json
    - php/l10n/de.js

key-decisions:
  - "Die Version des Containers kommt aus APP_VERSION und wird pro Aufruf aus der Umgebung gelesen, nicht aus dem lru_cached settings(): APP_VERSION gehoert AppAPI, nicht der FINDLING_-Konfiguration dieser App"
  - "Patch-Stellen werden ausdruecklich nicht verglichen; das Protokoll aendert sich mit Minor, und eine Patch-Pruefung wuerde jeden Hotfix einer Haelfte zu einer Instanz ohne Suche machen"
  - "Ein fehlendes, leeres oder formwidriges appVersion ist unknown und nie drift, damit ein aelterer Container die Suche nicht abschaltet (T-05-27)"
  - "Der Suchweg liest die zuletzt gemerkte Containerversion aus appconfig statt einen eigenen Statusabruf zu bezahlen; die Folge (Wirkung erst nach dem ersten Seitenaufruf) ist als DI-05-07-B festgehalten"
  - "Der Zustand auf der Seite ist ein weiterer Eintrag der bestehenden Bannerliste, kein neuer Mechanismus; geschaltet ueber das vorhandene hidden-Attribut"
  - "Das Gate fordert keine bestimmte Versionsnummer, sondern Gleichheit und die Form der Store-XSD"

patterns-established:
  - "Nachweise fuer eine Wave im Worktree: eigener Compose-Stack aus einer Wegwerf-Kopie mit eigenem Projektnamen, eigenem Containernamen, eigenem Port und absolutem Bind auf das Worktree, danach down -v"
  - "Ein CLI-Probe-Skript im Container (base.php plus IUserSession::setUser) fuehrt den echten Dienst und rendert die echte Vorlage, ohne einen Browserlogin zu brauchen"

requirements-completed: [PKG-05]

# Metrics
duration: 60min
completed: 2026-09-03
---

# Phase 5 Plan 07: Lockstep der beiden Haelften Summary

**Beide Haelften nennen jetzt ihre Version, die PHP-Haelfte vergleicht Major und Minor exakt, und eine Drift fuehrt zu einem leeren Suchergebnis mit Meldung plus einem benannten Zustand auf der Statusseite statt zu stummen Treffern. Live nachgestellt: mit Backend 0.4.0 neben Companion 0.3.0 liefert dieselbe Suche 0 statt 1 Treffer, und nach dem Zuruecksetzen kommt der Treffer ohne weiteren Eingriff wieder.**

## Performance

- **Duration:** ca. 60 min
- **Started:** 2026-09-03T12:10:00Z
- **Completed:** 2026-09-03T13:10:00Z
- **Tasks:** 3 von 3
- **Files modified:** 11 (1 neu, 10 geaendert)

## Accomplishments

- `GET /status` meldet `appVersion` aus der von AppAPI gesetzten Umgebungsvariablen, auch fuer einen Container ohne Zustandsdatenbank, und getrennt von `indexVersion` und `analyzerVersion`.
- Die Lockstep-Pruefung von D-11 liegt in `ExAppService`, ohne zusaetzlichen Roundtrip: sie arbeitet auf der Statusantwort, die die Admin-Seite ohnehin holt, und vergleicht Major und Minor exakt gegen `IAppManager::getAppVersion('findling')`.
- Bei erkannter Drift antwortet die Suche mit einem leeren Ergebnis und einer Warnung, die beide Versionsnummern nennt; die Admin-Seite zeigt den Zustand als Banner in Block 1, mit beiden gemeldeten Nummern und genau einer Abhilfe.
- Das Dev-Skript registriert alle fuenf Routen aus `backend/appinfo/info.xml` mit ihren Verben und Zugriffsstufen und startet einen Host-Prozess neu, dessen Version oder Routenliste nicht zu den Quellen passt (DI-04-01 und DI-04-02 erledigt).
- `backend/tests/test_lockstep_versions.py` haelt beide `<version>` und den `<image-tag>` zusammen, ohne eine Zahl festzuschreiben.

## Task Commits

1. **Task 1 RED: die vier Faelle des Versionsfeldes** - `f6e5ae7` (test)
2. **Task 1 GREEN: appVersion in GET /status** - `a833ace` (feat)
3. **Task 1: Routen und Neustarterkennung im Dev-Skript** - `84dd622` (feat)
4. **Task 2: Drift leert die Suche und bekommt einen Namen auf der Seite** - `ee7436c` (feat)
5. **Task 3: Gate ueber die drei Versionsangaben** - `17e6f0b` (test)

## Files Created/Modified

- `backend/src/findling/api/status.py` - Feld `appVersion` mit Vorgabewert der leeren Zeichenkette, gesetzt in `_volume()` und im Zweig mit Zustandsdatenbank namentlich weitergereicht; Helfer `_app_version()` liest `APP_VERSION` pro Aufruf aus der Umgebung, mit der Begruendung, warum der Wert nicht in das zwischengespeicherte `settings()` gehoert.
- `backend/tests/test_status_endpoint.py` - `appVersion` im als Ganzes geprueften Feldsatz, dazu vier Faelle: Wert aus der Umgebung, Wert ohne Zustandsdatenbank, Unabhaengigkeit von den beiden Indexmarken, und die vollstaendige Feldmenge mit leerer Zeichenkette bei fehlender Variablen (dieser eine ueber `report()`, weil die AppAPI-Middleware pro Anfrage selbst ein Sitzungsobjekt baut, das `APP_VERSION` braucht; der Grund steht im Test).
- `scripts/dev/register-exapp.sh` - Version und Routenliste aus der `info.xml` (awk-Parser mit der Abbildung PUBLIC 0, USER 1, ADMIN 2), Abbruch bei unbekannter Stufe und bei einem Parse, der weniger Routen findet als die Datei deklariert; `stale_reason()` fragt den laufenden Prozess signiert nach `/status` und probt jede deklarierte Route auf 404; `stop_backend()` als eigene Funktion fuer beide Wege; Kopfkommentar mit dem Vorbehalt zur Idempotenz.
- `php/lib/Service/ExAppService.php` - `lockstep()`, `driftOnRecord()`, `ownVersion()`, `versionOrNothing()`, `majorMinor()`, `rememberBackendVersion()`, die Konstanten der drei Verdikte, der appconfig-Schluessel und das Versionsmuster; `IAppConfig` im Konstruktor.
- `php/lib/Search/Provider.php` - der Zweig fuer die erkannte Drift direkt nach der Leerabfrage: Warnung mit beiden Nummern, leeres `SearchResult::complete`, keine Ausnahme.
- `php/lib/Service/AdminViewService.php` - `'lockstep' => $this->exAppService->lockstep($answer)` im Ueberblick, plus zwei Dokumentationsstellen (Abweichung, siehe unten).
- `php/templates/admin.php` - der neue Banner in der bestehenden Bannerliste, der Zustand aus `$_['lockstep']`, und eine abgeleitete Id am Textknoten jedes Banners.
- `php/js/admin.js` - Satz schreiben, dann `shown()`, plus `lockstep.state` und `lockstep.container` im Fingerabdruck der Poll-Schleife.
- `php/l10n/de.json`, `php/l10n/de.js` - die deutsche Fassung des neuen Satzes, echte Umlaute, in beiden Dateien identisch (je 140 Schluessel, maschinell verglichen).
- `backend/tests/test_lockstep_versions.py` (neu) - 223 Zeilen: drei Gleichheiten, die Form der Store-XSD, eine Antivakuitaetsklausel und fuenf Selbsttests.

## Decisions Made

- **`APP_VERSION` wird pro Aufruf aus der Umgebung gelesen.** `settings()` ist die Konfiguration dieser App, jeder Name darin beginnt mit `FINDLING_`, und der Wert ist einmal pro Prozess zwischengespeichert. `APP_VERSION` gehoert zu den vier Variablen, die AppAPI selbst setzt und die auch die Clientbibliothek pro Anfrage liest; ein zwischengespeicherter Wert waere ausserdem der falsche, sobald AppAPI den Container mit einer neuen Version neu startet.
- **Patch wird nicht verglichen, und der Kommentar sagt warum.** Gemessen im Probelauf: `0.3.0` gegen `0.3.9` ist `match`, `0.3.0` gegen `0.4.0` ist `drift`.
- **Was keine Version ist, ist unbekannt.** Ein Muster (drei Zahlengruppen, optionale Vorabkennung) entscheidet, bevor verglichen oder angezeigt wird. Gemessen: leerer String, Prosa und ein Wert mit Markup ergeben alle `unknown` mit leerem Containerfeld, also erreicht nichts Ungeprueftes die Seite. Das ist gleichzeitig die Antwort auf T-05-27.
- **Der Suchweg liest den gemerkten Wert.** `/status` fragt in dieser App genau ein Ort, die Admin-Seite. Ein Statusabruf pro Suche waere ein Roundtrip pro Tastendruck der Unified Search. Die Folge ist gemessen und als DI-05-07-B festgehalten: vor dem ersten Statusabruf sucht die Instanz wie bisher.
- **Kein neuer Bannermechanismus.** Der Zustand ist ein weiterer Eintrag der Liste aus Plan 04-03 und wird ueber `hidden` geschaltet. Damit die Poll-Schleife den Satz mit den beiden Nummern schreiben kann, ohne das Symbol im selben Absatz zu loeschen, traegt der Textknoten jedes Banners jetzt eine aus der Banner-Id abgeleitete Id.
- **Das Gate fordert Gleichheit, keine Zahl.** Und es meldet die Form vor der Differenz: ein Wert, der keine Version ist, wird als das gemeldet und nicht zusaetzlich als Unterschied, weil zwei Zeilen fuer eine Ursache den Leser einen zweiten Defekt suchen lassen.

## Nachgestellte Drift, protokolliert

Auf einem eigenen, isolierten Stack (Wegwerf-Kopie von `scripts/dev/compose.yaml`
mit Projektname `findling-wt0507`, Container `findling-wt0507-nc`, Port 8097 und
absolutem Bind auf das `php` dieses Worktrees; Host-Prozess auf Port 10099, weil
10035 dem Alltagsstack des Owners gehoert). Nextcloud 34.0.3, `app_api` aus dem
Image, `findling 0.3.0 enabled` aus diesem Worktree, ExApp registriert mit genau
der Routen-JSON, die das geaenderte Dev-Skript baut.

1. **Backend mit `APP_VERSION=0.4.0`, Companion 0.3.0, noch kein Statusabruf.**
   `GET /ocs/v2.php/search/providers/findling/search?term=findling-canary` ->
   HTTP 200, ocs 200, **1 Treffer** (`findling-canary`, Unterzeile aus dem
   Container). Das ist die Kontrolle: die Suche kann in diesem Aufbau treffen.
2. **Erster Aufruf der Statusseite** (echter `AdminViewService::overview()` im
   Container, mit gesetzter Nutzersitzung):
   `lockstep: {"state":"drift","companion":"0.3.0","container":"0.4.0"}`,
   `backendReachable: true`. Die echte Vorlage, mit genau diesem Ueberblick
   gerendert, liefert
   `<p class="findling-banner findling-banner--error" id="findling-banner-lockstep">`
   **ohne** `hidden` und darin den Satz mit beiden Nummern.
3. **Dieselbe Suche danach:** HTTP 200, ocs 200, **0 Treffer**. Im
   `nextcloud.log` steht als Warnung
   `Findling: the two halves report different versions, answering with no hits`
   mit `{"companion": "0.3.0", "backend": "0.4.0"}`.
4. **Version zurueckgestellt** (Host-Prozess mit `APP_VERSION=0.3.0` neu
   gestartet, sonst nichts angefasst): naechster Seitenaufruf meldet
   `{"state":"match","companion":"0.3.0","container":"0.3.0"}`, der Banner
   traegt wieder `hidden`, und dieselbe Suche liefert **wieder 1 Treffer**.
5. **Alle Zweige des Verdikts**, gegen den echten Dienst im echten Nextcloud:
   `null` (Container stumm), fehlendes Feld, leerer String, Prosa und ein Wert
   mit Markup ergeben je `unknown` mit leerem Containerfeld; `0.3.9` ergibt
   `match`; `0.4.0` ergibt `drift` und wird von `driftOnRecord()` aufgegriffen;
   `0.3.0` raeumt es wieder ab.

Der Stack wurde danach vollstaendig entfernt (`docker compose down -v`, Volume
und Netz weg, Host-Prozess beendet, Probe-Skripte geloescht). Der Alltagsstack
`findling-nextcloud` des Owners und der HaRP-Stack `findling-wt0508-harp` der
Nachbarwelle liefen die ganze Zeit unberuehrt weiter und laufen weiter.

## Verifikation des Dev-Skripts, protokolliert

Gegen einen echten Host-Prozess auf Port 10099, mit den Funktionen aus dem
Skript selbst (per `sed` herausgeloest, nicht nachgebaut):

- `/status` signiert abgefragt: `"appVersion":"0.3.0"` in der Antwort eines
  Containers ohne Zustandsdatenbank.
- Routenprobe: `search -> 405`, `snippets -> 405`, `status -> 200`,
  `rates -> 200`, `diagnose -> 422`, `nosuchroute -> 404`. Ein 405 ist ein
  montierter Pfad, ein 404 ist keiner.
- `stale_reason()`: leer bei passender Version; `it reports the version 0.3.0
  and the sources say 0.4.0` bei fremder Minor; `the declared route
  brandnewroute is not mounted in it` bei einer Route, die es nicht gibt;
  `it does not answer its status route ...` bei falschem Geheimnis.
- Parser: 5 Routen mit den richtigen Verben und Stufen aus der echten
  `info.xml`; eine erfundene Zugriffsstufe bricht mit `unknown access level
  SUPERUSER` ab; ein Parse, der eine Route verliert, bricht mit `declares 5
  routes and 4 could be read` ab.
- `sh -n scripts/dev/register-exapp.sh` fehlerfrei, kein CR, keine Dashes.

## Verifikation des Gates, protokolliert

`php/appinfo/info.xml` wurde voruebergehend auf `0.4.0` gesetzt: der Test wird
rot mit `the version in php/appinfo/info.xml is '0.4.0' and the version in
backend/appinfo/info.xml is '0.3.0'`. Danach mit
`git checkout -- php/appinfo/info.xml` zurueckgestellt; `git status` sauber.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `php/lib/Service/AdminViewService.php` musste mitgeaendert werden**
- **Found during:** Task 2, beim Verdrahten des Seitenzustands
- **Issue:** Der Plan nennt `admin.php` und `admin.js` als Orte des neuen Zustands, aber die Seite bekommt ihre Daten ausschliesslich aus `AdminViewService::overview()`. `backend()` baut die Antwort des Containers Feld fuer Feld neu und traegt `appVersion` nicht mit, also erreicht ohne eine Aenderung dort weder die Vorlage noch das Skript jemals ein Verdikt. Die Datei steht nicht in `files_modified` des Plans.
- **Fix:** Eine Zeile im Rueckgabewert (`'lockstep' => $this->exAppService->lockstep($answer)`), die `@return`-Annotation um den Schluessel ergaenzt und ein Aufzaehlungspunkt im Klassenkommentar, der sagt, warum dieser Wert weder zu `backend` noch zu den Zaehlern gehoert. `backend()` bleibt bei seinen siebzehn Feldern, also aendert sich nichts an der bestehenden Form.
- **Files modified:** `php/lib/Service/AdminViewService.php`
- **Verification:** Live gemessen (siehe oben), `php -l` sauber, Gate B und Gate C gruen.
- **Committed in:** `ee7436c`
- **Konfliktrisiko in der Welle:** die Aenderung liegt in einer Zeile des Rueckgabearrays und zwei Kommentarstellen; kein anderer Plan dieser Welle ist laut Plan-Kopf an `AdminViewService.php`.

**2. [Rule 2 - Missing Critical] Das Versionsmuster als Vertrauensgrenze**
- **Found during:** Task 2, beim Schreiben des Bannertexts
- **Issue:** Der Plan verlangt, `appVersion` zu lesen und anzuzeigen. Der Wert kommt aus dem Container, also von jenseits der Vertrauensgrenze, und die Seite hat fuer ihn keine der bestehenden Reinigungen (`counter()` ist fuer Zahlen, `text()` fuer die zwei benannten Freitextfelder). Ohne eine Pruefung waere die erste Anzeige eines Containerstrings auf dieser Seite ohne Form gewesen.
- **Fix:** `VERSION_PATTERN` in `ExAppService`; was nicht passt, wird zur leeren Zeichenkette und damit zu `unknown`. Damit ist die Anzeige auf drei Zahlengruppen plus optionale Vorabkennung begrenzt, und die Drift-Entscheidung kann nicht von einem formwidrigen Wert ausgeloest werden.
- **Files modified:** `php/lib/Service/ExAppService.php`
- **Verification:** Probelauf im echten Nextcloud mit Prosa und mit `0.4.0<script>alert(1)</script>`: beide `unknown`, Containerfeld leer.
- **Committed in:** `ee7436c`

**3. [Rule 2 - Missing Critical] Der Suchweg braucht eine Quelle fuer die Containerversion**
- **Found during:** Task 2, beim Umsetzen des leeren Suchergebnisses
- **Issue:** Der Plan verlangt die Pruefung "ohne zusaetzlichen Roundtrip" und zugleich eine Folge im Suchweg. Der Suchweg ruft `/status` aber nie auf, und es gibt in der PHP-Haelfte keinen Poller, der es taete.
- **Fix:** `ExAppService` merkt die zuletzt gemeldete Containerversion in appconfig (eigener Schluessel, geschrieben nur bei Aenderung, nach dem Muster von `SettingsService::rememberContainerCap`), und `driftOnRecord()` liest sie. `IAppConfig` ist dafuer neu im Konstruktor.
- **Files modified:** `php/lib/Service/ExAppService.php`
- **Verification:** Live gemessen (Schritte 1 bis 4 oben), inklusive des Zustands vor dem ersten Statusabruf.
- **Committed in:** `ee7436c`
- **Offen bleibt:** die zeitliche Luecke, festgehalten als DI-05-07-B.

**4. [Rule 2 - Missing Critical] Id am Textknoten jedes Banners**
- **Found during:** Task 2, beim Schreiben des Skriptteils
- **Issue:** Der Bannerabsatz enthaelt Symbol und Text. `textContent` auf dem Absatz haette das Symbol geloescht; das Skript darf kein Markup bauen (Gate C), also brauchte der Text einen eigenen Knoten mit Id.
- **Fix:** Der Textknoten jedes Banners traegt jetzt `id="<banner-id>-text"`, aus der vorhandenen Id abgeleitet statt als Sonderfall fuer einen Banner.
- **Files modified:** `php/templates/admin.php`
- **Verification:** Gate C gruen (`innerHTML` weiterhin 0 Treffer), gerendertes Markup live geprueft.
- **Committed in:** `ee7436c`

---

**Total deviations:** 4 auto-fixed (1 blockierend, 3 fehlende kritische Teile)
**Impact on plan:** Ohne die erste haette die Admin-Seite den Zustand nie zu sehen bekommen, ohne die dritte haette die Suche nie degradiert. Beides sind Verdrahtungen, keine Richtungsaenderungen; die Entscheidungen des Plans (kein Roundtrip, kein neuer Bannermechanismus, kein Fehler bei Drift) sind unveraendert umgesetzt.

## Issues Encountered

- **Der Browserlogin per curl scheiterte** (303 zurueck auf `/login`, auch nach `occ user:resetpassword`). Statt weiter daran zu arbeiten wurde die Seite ueber ein CLI-Probe-Skript im Container gerendert (`base.php`, `IUserSession::setUser('admin')`, echte `TemplateResponse`), was den echten Dienst und die echte Vorlage ausfuehrt. Der Sichttest im Browser bleibt damit offen, siehe unten.
- **`docker compose exec` im Git-Bash braucht `MSYS_NO_PATHCONV=1`** fuer einen Pfad im Container, sonst wird `/tmp/probe.php` in einen Windows-Pfad umgeschrieben und die Datei ist "not found".
- **Der Alltagsstack laesst sich aus einem Worktree nicht zweitverwenden** (fester Projekt- und Containername): festgehalten als DI-05-07-A.

## Offene Verifikation

- **Der volle Lauf von `scripts/dev/register-exapp.sh`** ist nicht belegt. Sein `COMPOSE_FILE` zeigt auf `scripts/dev/compose.yaml`, deren Projektname mit dem laufenden Stack des Haupt-Checkouts kollidiert; ein Aufruf haette `occ` im fremden Stack ausgefuehrt (DI-05-07-A). Ersatzbelege: beide neuen Teile des Skripts (Parser und Neustarterkennung) sind einzeln gegen einen echten Backend-Prozess gelaufen, `sh -n` ist sauber, und die Routen-JSON, die der Parser baut, ist genau die, mit der die ExApp im Beweislauf oben registriert wurde. Was dadurch nicht abgedeckt ist: die beiden `occ`-Aufrufe der Registrierung im Zusammenspiel mit der Neustarterkennung, also der zweite Aufruf direkt nach dem ersten.
- **Der Sichttest der Seite im Browser** (Farbe, Platz, Dunkelmodus, deutsche Fassung im Kontext) ist nicht gemacht; das gerenderte Markup und die deutsche Zeichenkette sind maschinell geprueft. Das ist die uebliche Grenze des Textgates C und gehoert zum menschlichen Designcheck der Phase.

## Known Stubs

Keine.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: trust-boundary | `php/lib/Service/ExAppService.php` | Erstmals wird eine Zeichenkette des Containers zu einer Entscheidungsgrundlage der Suche (Drift ja oder nein) und zugleich auf der Admin-Seite angezeigt. Bewertung: T-05-25 des Plan-Registers benennt genau das und akzeptiert es, weil `appVersion` aus der Umgebung von AppAPI stammt und die tragende Grenze der signierte AppAPI-Weg plus `rejectForeignCaller` bleibt. Zusaetzlich eingezogen: das Versionsmuster, das alles andere zu `unknown` macht, und die Richtung fail-open (ein Container, der nichts oder Unsinn sagt, schaltet die Suche nicht ab). |
| threat_flag: state | `php/lib/Service/ExAppService.php` | Neuer appconfig-Schluessel `backend_app_version` unter der App `findling`. Er haelt keine Nutzerdaten, wird nur bei Aenderung geschrieben und ist der einzige Weg, auf dem der Suchweg von einer Drift erfaehrt. Ein Admin mit `occ config:app:set` kann ihn setzen und damit die Suche dieser Instanz leer schalten; das ist dieselbe Macht, die `occ app:disable` ohnehin gibt. |

## User Setup Required

Keine.

## Next Phase Readiness

- **Plan 05-17 (Bump auf das Store-Erstrelease)** hat jetzt ein Gate, das beim Bump mitlaeuft: `backend/tests/test_lockstep_versions.py` wird rot, sobald eine der drei Angaben stehen bleibt. Es fordert keine Zahl, also muss an ihm nichts geaendert werden.
- **Die Integrationsjobs** uebergeben `APP_VERSION` seit Plan 05-01 aus der `info.xml`; der neue Vergleich hat damit in CI dieselben Werte auf beiden Seiten. Die Stellen in `integration.yml` und `resilience.yml`, die `APP_VERSION=0.1.0` von Hand exportieren, betreffen Containerlaeufe ohne Companion und sind fuer die Pruefung ohne Bedeutung, weil dort keine PHP-Haelfte vergleicht.
- **Blocker:** keiner.

---
*Phase: 05-h-rtung-und-store-einreichung-v1-0*
*Completed: 2026-09-03*
