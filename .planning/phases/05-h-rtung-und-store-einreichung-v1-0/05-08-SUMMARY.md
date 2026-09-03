---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 08
subsystem: infra
tags: [harp, appapi, github-actions, uninstall, nextcloud-32, nextcloud-35, migrations, backoff, poller]

# Dependency graph
requires:
  - phase: 05-01
    provides: den Job deploy-harp mit Installations- und Laufbeweis, die Composite Action ohne ExApp-Registrierung
  - phase: 05-02
    provides: die Absichtsmarke, occ findling:purge und die Messung, dass Nextcloud den Uninstall-Schritt beim Disable ausfuehrt
  - phase: 05-04
    provides: den Poller in seinem aktuellen Stand samt Testaufbau
provides:
  - "Vollstaendiger Lebenszyklus in CI: Installation, Lauf und Deinstallation ueber Nextcloud 32, 33, 34 und 35, gruen gemessen"
  - "Sechs Feststellungen mit eigener Fehlermeldung, jede so gebaut, dass eine leere Ausgabe rot ist"
  - "Belegte Betriebsaussage zu --rm-data: ohne Kennzeichen bleibt das Volume, mit Kennzeichen verschwindet es"
  - "Belegte Betriebsaussage zur Nextcloud-Haelfte: Disable ohne Absicht raeumt nichts, Remove mit Absicht raeumt vollstaendig"
  - "Rueckzug des Containers ohne Companion: eigene Backoff-Leiter bis 300 s, eine Zeile beim Eintritt, danach Ruhe"
  - "Findling laesst sich wieder auf Nextcloud 32 einschalten (BOOLEAN NOT NULL)"
  - "Die HaRP-Topologie fuer CI: eine Adresse bedient Nextcloud und /exapps"
affects: [05-10 ARM- und AIO-Lauf, 05-11 Statusseite, 05-01 lokaler compose-Stack, PKG-03, PKG-04]

# Tech tracking
tech-stack:
  added:
    - nginx:1.27-alpine als Frontproxy im Job (eine Adresse fuer Nextcloud und /exapps)
  patterns:
    - "Bereitschaft wird an dem Aufruf gemessen, den der Anrufer als erstes macht, nicht an einem TCP-Handschlag"
    - "Feststellungen als eigene Schritte, jede mit eigener Fehlermeldung, leere Ausgabe ist rot"
    - "Namen aus dem Installationsschritt in GITHUB_ENV, damit eine Suche ohne Filternamen nicht gruen wird"
    - "Zwei getrennte Wartezeit-Leitern im Poller: leere Warteschlange gegen nicht antwortende Warteschlange"

key-files:
  created: []
  modified:
    - .github/workflows/deploy-harp.yml
    - docs/uninstall.md
    - backend/src/findling/worker/poller.py
    - backend/tests/test_poller.py
    - backend/src/findling/nc/queue.py
    - php/lib/Migration/Version001000Date20260816000000.php
    - php/lib/Migration/Version001000Date20260901000000.php
    - .planning/phases/05-h-rtung-und-store-einreichung-v1-0/deferred-items.md

key-decisions:
  - "Die Matrix ist eine include-Liste, damit jede Serverversion ihre PHP-Untergrenze traegt: 8.2 fuer 32 bis 34, 8.3 fuer 35"
  - "continue-on-error haengt an einem Matrixfeld tolerate-failure und ist ausschliesslich am NC-35-Eintrag gesetzt, mit Abschaltbedingung im Kommentar"
  - "Das Backend-Image wird je Matrixeintrag gebaut statt einmal und geteilt, weil 60 s Bau billiger sind als 390 MB Artefaktverkehr"
  - "nextcloud_url der Daemon-Registrierung ist ein Frontproxy, weil AppAPI dasselbe Feld fuer die ExApp-Adresse und fuer NEXTCLOUD_URL benutzt"
  - "Der Rueckzug hat eine eigene Leiter bis RETREAT_MAX_SECONDS (300 s) und faengt bei jedem Ausfall wieder bei 15 s an, weil er eine andere Frage stellt als eine leere Warteschlange"
  - "DocumentQueue.claim protokolliert auf debug, weil der Aufrufer die Durchgaenge zaehlt und die Protokollregel besitzt"
  - "Die Tabellen- und Einstellungszahlen kommen aus der Testdatenbank und nicht aus occ, weil ein gescheiterter occ-Aufruf wie ein sauberes Ergebnis aussieht"

patterns-established:
  - "Negativprobe als eigener Wegwerf-Zweig: die verletzte Fassung laeuft in CI rot, der Arbeitszweig bleibt unberuehrt"
  - "Jede Messung im Kommentar mit Lauf-Nummer, damit der naechste Leser die Quelle hat und nicht die Behauptung"

requirements-completed: [PKG-03, PKG-04]

# Metrics
duration: ca. 3h
completed: 2026-09-03
---

# Phase 5 Plan 08: Lebenszyklus ueber vier Serverversionen Summary

**Installation, Lauf und Deinstallation laufen gruen ueber Nextcloud 32, 33, 34 und 35, mit sechs Feststellungen statt Behauptungen: das Index-Volume bleibt ohne Kennzeichen und verschwindet mit `--rm-data`, ein Disable ohne Absicht laesst Tabellen und Einstellungen unberuehrt, ein Remove mit Absicht raeumt sie auf null, und der Container ohne Companion zieht sich mit wachsender Wartezeit zurueck, statt das Protokoll zu fluten. Auf dem Weg dahin fanden sich vier Defekte, die es ohne diesen Job nicht ins Licht geschafft haetten, darunter einer, der Findling auf Nextcloud 32 ueberhaupt nicht startbar machte.**

## Performance

- **Duration:** ca. 3 h (mit einer Unterbrechung durch ein Session-Limit)
- **Tasks:** 3 von 3
- **Commits:** 13
- **Files modified:** 8
- **CI-Laufzeit des Ergebnisses:** 3 m 47 s bis 4 m 29 s je Matrixeintrag, vier Eintraege parallel

## Accomplishments

- **Der Lebenszyklus ist vollstaendig und gemessen.** Lauf `33757405755` und der Wiederholungslauf `33757967523` sind auf allen vier Serverversionen gruen. Jeder Lauf protokolliert dieselben sieben Zeilen; hier die von Nextcloud 32:

  ```
  container gone, volume nc_app_findling_backend_data kept
  registered again as nc_app_findling_backend on the kept volume nc_app_findling_backend_data
  container and volume nc_app_findling_backend_data both gone
  before the disable: tables [oc_findling_file_state oc_findling_queue oc_findling_scan_stats], settings 4
  after the disable:  tables [oc_findling_file_state oc_findling_queue oc_findling_scan_stats], settings 5
  after the remove with intent: tables [], settings 0
  container nc_app_findling_backend is Up About a minute, retreat announced, 2 new warning or error lines
  ```

- **Die Negativprobe wurde gefahren und war rot.** Auf einem Wegwerf-Zweig (`worktree-agent-05-08-negative`, Lauf `33757987864`, Zweig danach geloescht) wurde nur die Zeile `occ findling:purge --arm --no-interaction` entfernt. Feststellungen 1 bis 4 blieben gruen, Feststellung 5 wurde rot mit `the remove with intent left tables behind: [oc_findling_file_state oc_findling_queue oc_findling_scan_stats]`. Das Gate misst also, was es zu messen behauptet.

- **Der Rueckzug des Containers ist im Protokoll sichtbar**, gemessen im selben Lauf:

  ```
  WARNING:findling.worker.poller:the queue did not answer, next attempt in 15 s
  WARNING:findling.worker.poller:the queue did not answer, next attempt in 30 s
  WARNING:findling.worker.poller:the queue has not answered for 3 passes, backing off to at most one
    attempt every 300 s; the Nextcloud half looks removed and the container keeps answering searches
  ```

  Danach nichts mehr. Der Container lief zu diesem Zeitpunkt seit ueber einer Minute ohne Companion weiter.

- **Vier Defekte gefunden und behoben**, alle vier nur sichtbar, weil dieser Job zum ersten Mal auf einem Runner und ueber vier Serverversionen lief. Zwei davon (NC 32 und die Init-Rueckmeldung) sind Produktfehler und keine CI-Eigenheiten. Siehe Deviations.

## Task Commits

1. **Vorab, CI-Fix: Bereitschaftspruefung von HaRP** , `97863e4` (fix)
2. **Task 1: Uninstall-Strecke mit fuenf Feststellungen plus Doku** , `e56613c` (feat)
3. **Task 2: Matrix ueber vier Serverversionen** , `d5435d0` (feat)
4. **Task 3 RED: fehlschlagende Tests fuer den Rueckzug** , `c11a952` (test)
5. **Task 3 GREEN: Rueckzug im Poller, sechste Feststellung, Doku** , `d815f24` (feat)
6. **Deviation: Findling laesst sich wieder auf NC 32 einschalten** , `07b816c` (fix)
7. **Deviation: HaRP auf dem Host-Netz** , `1ba2b57` (fix)
8. **Deviation: eine Adresse fuer Nextcloud und /exapps** , `e6f93d8` (fix)
9. **Deviation: die Testinstanz bindet alle Schnittstellen** , `f3e1eb7` (fix)
10. **Deviation: die Datenbanksonde sucht die sqlite-Datei** , `a8612ed` (fix)
11. **Deviation: die Sonden warten auf eine Sperre** , `10daedc` (fix)
12. **timeout-minutes nach der gemessenen Laufzeit** , `41b68ce` (chore)
13. **Doku mit dem gemessenen Lauf plus zwei Deferred Items** , `e37f522` (docs)

## Files Created/Modified

- `.github/workflows/deploy-harp.yml` , Matrix ueber 32, 33, 34, 35 mit eigener PHP-Version je Eintrag; Frontproxy-Schritt; sechs Uninstall-Feststellungen als eigene Schritte; Datenbanksonde mit Dialektpruefung und Busy-Timeout; Aufraeumschritt nimmt Proxy und ExApp-Container mit
- `docs/uninstall.md` , neuer Abschnitt 5 mit den sechs Feststellungen, dem Protokollauszug des gemessenen Laufs und den zwei ausdruecklichen Nicht-Aussagen; Abschnitt 4 mit dem gemessenen Rueckzugsverhalten und der Begruendung der Obergrenze; drei alte "offener Punkt"-Stellen ersetzt
- `backend/src/findling/worker/poller.py` , `RETREAT_AFTER_ROUNDS`, `RETREAT_MAX_SECONDS`, `_retreat()` und `_recovered()`; die Protokollregel des Rueckzugs
- `backend/tests/test_poller.py` , sieben neue Faelle fuer die sechs Verhaltensweisen
- `backend/src/findling/nc/queue.py` , `claim()` protokolliert auf debug statt warning, mit Begruendung
- `php/lib/Migration/Version001000Date20260816000000.php` , `is_update` nullable
- `php/lib/Migration/Version001000Date20260901000000.php` , `dirty` nullable
- `.planning/phases/05-.../deferred-items.md` , DI-05-07 und DI-05-08

## Decisions Made

- **Die Matrix haengt an diesem Job und nicht an `integration.yml`.** So steht es im Plan, und die Messung stuetzt es: vier Eintraege kosten hier 4,5 Minuten und dort ein Vielfaches.
- **`continue-on-error` ueber ein Matrixfeld.** GitHub kennt kein `continue-on-error` je include-Eintrag; der Ausdruck `${{ matrix.tolerate-failure }}` am Job ist der kanonische Weg, und das Feld steht nur am NC-35-Eintrag. Faktisch war der Eintrag in beiden gruenen Laeufen gruen, das Zugestaendnis wurde also nicht gebraucht.
- **Der Rueckzug bekommt eine eigene Leiter.** Ein Fehlschlag der Warteschlange setzt die Wartezeit auf den Startwert und verdoppelt von dort bis 300 s, unabhaengig davon, wo die Leiter der leeren Warteschlange gerade stand. Zwei Fragen, zwei Leitern: "gibt es Arbeit" und "gibt es meinen Anrufer noch". Das macht den Zustand ausserdem in CI in unter einer Minute messbar statt in bis zu sechs.
- **Die Protokollhoheit liegt beim Poller.** `DocumentQueue.claim` weiss nur von einem Aufruf, der Poller zaehlt die Durchgaenge. Deshalb ist die Zeile dort auf debug gefallen und die beiden Zeilen des Pollers sind an ihre Stelle getreten. Ohne das waere "keine Zeile je Versuch" nicht einloesbar gewesen.
- **Der Frontproxy statt eines Verzichts auf `--wait-finish`.** Der bequeme Ausweg waere gewesen, den Handschlag nicht mehr synchron zu machen. Das haette den Defekt versteckt, den der Job gerade gefunden hat, und die Aussage "die Installation laeuft durch" in "die Installation faengt an" verwandelt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Findling liess sich auf Nextcloud 32 nicht einschalten**

- **Found during:** Task 2, erster Matrixlauf
- **Issue:** `occ app:enable findling` starb auf stable32 mit `Column "oc_findling_queue"."is_update" is type Bool and also NotNull, so it can not store "false"`. Nextcloud 32 verbietet in `MigrationService::ensureOracleConstraints` jede BOOLEAN-Spalte mit NotNull; in 33, 34 und 35 gibt es die Pruefung nicht mehr. Beide `info.xml` nennen `min-version="32"`, die App war dort also seit vier Phasen nicht installierbar, und kein bestehendes Gate konnte das sehen, weil alle auf stable34 liefen.
- **Fix:** `is_update` und `dirty` sind nullable, beide behalten ihren Vorgabewert `false`, sodass ein Insert ohne die Spalte weiterhin `false` schreibt und nie NULL. Keine zusaetzliche Migration noetig: die Pruefung greift beim Anlegen, und eine NC-32-Instanz kann es nur als Neuinstallation geben.
- **Files modified:** `php/lib/Migration/Version001000Date20260816000000.php`, `php/lib/Migration/Version001000Date20260901000000.php`
- **Verification:** stable32 gruen in Lauf `33757405755`, dazu `Integration` und `PHP and store metadata gates` gruen auf demselben Zweig.
- **Committed in:** `07b816c`

**2. [Rule 1 - Bug] Die Bereitschaftspruefung von HaRP war wertlos**

- **Found during:** vor Task 1, aus dem uebernommenen Fehlschlag `33743374344`
- **Issue:** Der Job wartete mit einem TCP-Handschlag auf Port 8780. Den beantwortet der Portweiterleiter von Docker, sobald der Container existiert, also lange bevor HAProxy im Container den Port bindet. Der Lauf ging an dieser Stelle gruen und scheiterte 0,84 s spaeter mit `Connection refused` beim Image-Pull. Lokal gegen das gepinnte Image nachgestellt: TCP antwortet in der ersten Sekunde, die Docker-Route nach drei bis vier Sekunden.
- **Fix:** Die Pruefung ist jetzt der Aufruf, den AppAPI als erstes macht: `GET /exapps/app_api/v1.44/_ping` durch HaRP, mit `harp-shared-key` und `docker-engine-port`, und erst ein 200 gilt. Das belegt HAProxy, den Agenten, den frp-Server und den Tunnel zum Docker-Socket in einem Aufruf.
- **Files modified:** `.github/workflows/deploy-harp.yml`
- **Verification:** Der Schritt braucht seither 6 bis 7 s und der Pull gelingt.
- **Committed in:** `97863e4`

**3. [Rule 1 - Bug] Der Container konnte seinen Init-Status nie melden**

- **Found during:** Task 2, zweiter und dritter Matrixlauf
- **Issue:** Zwei Befunde nacheinander. Erstens erreichte HaRP Nextcloud nicht (`Cannot connect to host localhost:8080`), weil `NC_INSTANCE_URL` in das Netzwerk-Namespace des HaRP-Containers zeigte. Zweitens, und das ist der eigentliche Fehler: das Daemon-Feld `nextcloud_url` wird von AppAPI doppelt benutzt, als Basis der ExApp-Adresse (`{nextcloud_url}/exapps/{appId}`) und als `NEXTCLOUD_URL` des Containers. HaRP bedient aber nur Pfade mit `/exapps` darin, also antwortete `PUT /ocs/v1.php/apps/app_api/ex-app/status` mit 404, und `occ app_api:app:register --wait-finish` wartete auf genau diesen Status, bis der Schritt nach zehn Minuten abbrach, waehrend Container und Suche gesund waren.
- **Fix:** HaRP laeuft auf dem Host-Netz, und ein nginx auf Port 8090 leitet `/exapps` an HaRP und alles andere an Nextcloud. `nextcloud_url` ist diese eine Adresse, was der Topologie entspricht, fuer die HaRP gebaut ist. Beide Richtungen werden geprueft, bevor irgendetwas registriert wird.
- **Files modified:** `.github/workflows/deploy-harp.yml`
- **Verification:** `ExApp findling_backend successfully registered` und alle sechs Feststellungen in `33757405755`. Der lokale compose-Stack hat dieselbe Luecke und ist als DI-05-07 vermerkt.
- **Committed in:** `1ba2b57`, `e6f93d8`

**4. [Rule 3 - Blocking] Der Frontproxy erreichte Nextcloud nicht**

- **Found during:** Task 2, vierter Matrixlauf
- **Issue:** Der eingebaute PHP-Server bindet die erste Adresse, auf die `localhost` zeigt, und das ist auf diesem Runner-Image `::1`. curl findet die Instanz trotzdem, nginx nicht: 502 mit `connect() failed (111: Connection refused) upstream 127.0.0.1:8080`.
- **Fix:** Der Job uebergibt `nextcloud-host: '0.0.0.0'` an die Composite Action. Genau dafuer gibt es den Eingang, und er traegt die beiden noetigen trusted domains gleich mit ein. Die Action selbst blieb unangetastet.
- **Files modified:** `.github/workflows/deploy-harp.yml`
- **Verification:** Die Sonde des Proxy-Schritts meldet seither beide Haelften mit 200.
- **Committed in:** `f3e1eb7`

**5. [Rule 3 - Blocking] Die Datenbanksonde starb still**

- **Found during:** Task 1, fuenfter Matrixlauf
- **Issue:** `occ config:system:get dbname` gibt nichts aus und endet mit 1, wenn der Schluessel nicht in der `config.php` steht, und eine sqlite-Installation schreibt ihn nicht. Unter `set -e` starb der Schritt an dieser einen Zeile, ohne eine einzige Meldung.
- **Fix:** Die Datei wird unter dem Datenverzeichnis gesucht statt aus zwei Schluesseln gebaut, und wird sie nicht gefunden, ist das ein Fehler mit Meldung und einem `ls` daneben.
- **Files modified:** `.github/workflows/deploy-harp.yml`
- **Verification:** `database /home/runner/.../data/owncloud.db, dialect sqlite3` im Protokoll aller vier Eintraege.
- **Committed in:** `a8612ed`

**6. [Rule 1 - Bug] Die Datenbanksonde stolperte ueber eine Schreibsperre**

- **Found during:** Task 1, fuenfter Matrixlauf, nur auf Nextcloud 32
- **Issue:** `Error: in prepare, database is locked (5)`. Der ExApp-Container laeuft neben diesen Lesevorgaengen, Nextcloud schreibt fuer ihn in dieselbe sqlite-Datei, und die drei anderen Versionen lasen zufaellig zwischen zwei Schreibvorgaengen. Ein Gate, das an der Zeitplanung des Runners haengt, ist kein Gate.
- **Fix:** Jede Abfrage traegt `.timeout 30000`, aus einem Rennen wird ein Warten.
- **Files modified:** `.github/workflows/deploy-harp.yml`
- **Verification:** alle vier Eintraege gruen in `33757405755` und noch einmal in `33757967523`.
- **Committed in:** `10daedc`

### Additions outside the plan's file list

**7. [Rule 2 - Missing Critical] `DocumentQueue.claim` protokolliert auf debug**

- **Issue:** Verhaltensweise 2 des Plans verlangt, dass der Container in der Rueckzugslage "nicht je Versuch eine Fehlerzeile" schreibt. Die Zeile kam aber aus `nc/queue.py`, einmal je Aufruf, und der Poller konnte sie nicht unterdruecken.
- **Fix:** Die Zeile ist auf `debug` gefallen, mit der Begruendung daneben, und der Poller schreibt an ihrer Stelle: eine Zeile je Fehlschlag unterhalb der Schwelle (wie bisher von aussen), eine Zeile beim Eintritt in den Rueckzug, danach nichts.
- **Files modified:** `backend/src/findling/nc/queue.py`
- **Verification:** Das Protokoll des Containers im gemessenen Lauf enthaelt genau drei Zeilen, siehe oben. `nc/queue.py` steht in keiner `files_modified` dieser Phase, ein Konflikt in der Welle entsteht also nicht.
- **Committed in:** `d815f24`

---

**Total deviations:** 7 auto-fixed (4 Bugs, 2 Blocker, 1 fehlende kritische Angabe)
**Impact on plan:** Ohne Nummer 1 waere die Zusage "laeuft auf Nextcloud 32" falsch gewesen, ohne 2 bis 5 waere der Job nie durchgelaufen, und ohne 6 waere er ein Wuerfelspiel. Kein Zuwachs am Funktionsumfang: eine neue Zeile Produktcode gibt es nur im Poller, alles andere sind Korrekturen und Jobschritte.

## Issues Encountered

- **Der Beweis brauchte sechs CI-Laeufe.** Jeder davon hat genau einen Befund geliefert, weil jeder Schritt seine eigene Fehlermeldung traegt. Die Reihenfolge der Befunde steht in den Deviations; sie ist die Reihenfolge, in der die Kette laenger wurde.
- **`--wait-finish` versteckt seinen Zustand.** Der Befehl schreibt `deployed successfully`, bevor er auf den Init-Status wartet. Wer die Zeile sieht und den Befehl abbricht, haelt eine haengende Installation fuer eine gelungene. Genau das ist in Plan 05-01 lokal passiert, siehe DI-05-07.
- **Assertion 4 zeigt 4 Einstellungen vorher und 5 nachher.** Das ist kein Rueckstand, sondern der Zaehler `purge_step_calls` aus Plan 05-02, der seinen eigenen Aufruf mitschreibt. In `docs/uninstall.md` steht der Satz dazu, damit die Zahl niemanden erschreckt.

## Known Stubs

Keine.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: network | `.github/workflows/deploy-harp.yml` | Der Job faehrt jetzt einen Frontproxy (nginx) auf Port 8090, der Nextcloud und HaRP unter einer Adresse zusammenfasst, und HaRP laeuft im Host-Netz statt mit veroeffentlichten Ports. Beides betrifft ausschliesslich den Wegwerf-Runner und keine Auslieferung, aber es ist eine Netzform, die das Threat-Register des Plans nicht kannte. Der Proxy leitet unveraendert weiter und terminiert kein TLS. |
| threat_flag: schema | `php/lib/Migration/Version001000Date20260816000000.php`, `php/lib/Migration/Version001000Date20260901000000.php` | Zwei Spalten sind nicht mehr NOT NULL. Die Vorgabewerte bleiben, alle Schreiber setzen beide Spalten, und ein NULL kann daher nur durch einen fremden Schreiber in die Tabelle kommen. Wer die Tabellen kuenftig liest, sollte `dirty = true` und nicht `dirty != false` fragen. |

## User Setup Required

Keine.

## Next Phase Readiness

- **Erfolgskriterium 3 der Phase ist fuer die CI-Haelfte erfuellt:** beide Apps installieren, laufen und deinstallieren sauber ueber HaRP, auf Nextcloud 32, 33, 34 und 35, mit Volume- und Tabellenbeweis und mit einer gefahrenen Negativprobe.
- **Plan 05-10 (ARM und AIO)** muss DI-05-07 lesen, bevor die Miet-Box laeuft: `nextcloud_url` ist dort die Adresse von Nextcloud hinter dem Apache von all-in-one und ausdruecklich nicht die von HaRP. Dieselbe Verwechslung kostet dort einen Tag.
- **Plan 05-11 (Statusseite)** bekommt mit DI-05-08 den Rueckzug als sichtbaren Betriebszustand angeboten.
- **Plan 05-01s lokaler Stack** hat die Luecke aus DI-05-07 noch; der Weg dort endet bis dahin in einem haengenden `--wait-finish`.
- **Blocker:** keiner.

## Offene Verifikation

- **Der Beweis haengt an einem Zweig, den es nach dem Merge nicht mehr gibt.** Die gruenen Laeufe `33757405755` und `33757967523` liefen auf `worktree-agent-05-08`, der zu diesem Zweck nach origin geschoben wurde; nach dem Merge laeuft derselbe Job auf `main` erneut, weil er Push-Trigger auf `backend/**`, `php/appinfo/**` und seinen eigenen Pfad hat. Dieser erste Lauf auf `main` ist anzusehen, so wie DI-05-01 es fuer den vorigen Stand verlangt hat. Erwartet wird derselbe gruene Verlauf: die vier Eintraege sind seit dem letzten Commit an der Datei unveraendert, und `41b68ce` (der Stand mit `timeout-minutes: 15`) ist genau der Stand, der gruen gemessen wurde. Der Zweig `worktree-agent-05-08` bleibt bis zum Merge auf origin stehen, danach kann er geloescht werden.
- **Nicht gemessen bleibt die Weboberflaeche** (der Schalter "Daten loeschen" in NC 32 und 33) und die Entfernung des Container-Images, beides ausdruecklich und begruendet in `docs/uninstall.md`, Abschnitt 5.

## Self-Check: PASSED

Alle acht genannten Dateien liegen im Worktree, alle dreizehn Commits sind in der Historie von `worktree-agent-05-08`, der Arbeitsbaum ist sauber, und `.planning/STATE.md` sowie `.planning/ROADMAP.md` sind in dieser Zweigspanne unveraendert. Lokale Gates zum Abschluss: `pytest` 877 passed / 11 skipped, `ruff check`, `ruff format --check`, `pyright` (0 errors) und `vulture` ohne Funde, `actionlint` 1.7.12 ohne Beanstandung.

---
*Phase: 05-h-rtung-und-store-einreichung-v1-0*
*Completed: 2026-09-03*
