---
phase: 02-indexkern-und-volltextsuche
plan: 04
subsystem: php-companion
tags: [crawl, mounts, ifileaccess, cursor, background-jobs, repair-step, occ, zero-config, idx-01, idx-06]

# Dependency graph
requires:
  - phase: 02-03
    provides: "QueueService::enqueue mit ICacheEntry-Signatur, FileStateService als einziger Schreiber der Zustandstabelle"
provides:
  - "StorageService: die einzige Stelle mit Mount- und Dateiaufzaehlung, ausschliesslich ueber IFileAccess"
  - "Mount-Allowlist: User-Homes und Team Folders an, External Storage kommentiert aus"
  - "Dokument-Allowlist als numerische Mimetype-IDs, Filterung in der Abfrage statt hinter dem Transfer"
  - "SchedulerJob: Mountliste zu einem Crawl-Job je Mount, plus Zeitstempel des letzten Job-Laufs"
  - "StorageCrawlJob: Cursor last_file_id im Jobargument, 50-MB-Deckel als skipped(too_large), Selbstnachplanung"
  - "AppInstallStep: Erstindex startet beim Install von selbst, genau einmal, wirft nie"
  - "occ findling:index mit --status (Vorgabe) und --restart"
affects: [02-07, 02-10, 02-14, phase-03-events, phase-04-statusseite]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Kein Kompatibilitaetszweig unterhalb der deklarierten min-version: die Versionsuntergrenze ist der Gegenwert fuer weggelassenen Code"
    - "Der Crawl-Cursor lebt im Jobargument und damit in der Nextcloud-Datenbank, nie im Prozessspeicher und nie im Container"
    - "Zwei Deckel je Durchgang, Stueckzahl und Wanduhr, danach Selbstnachplanung statt eines langen Laufs"
    - "IMimeTypeLoader::exists vor getId, weil getId unbekannte Typen anlegt und ein Lesen sonst schreibt"
    - "PHP-Klassennamen in der info.xml stehen ohne umgebenden Zeilenumbruch, das Schemamuster erlaubt keinen"
    - "Zerstoerende occ-Optionen sind nie die Vorgabe und fragen am interaktiven Terminal nach"

key-files:
  created:
    - php/lib/Service/StorageService.php
    - php/lib/BackgroundJobs/SchedulerJob.php
    - php/lib/BackgroundJobs/StorageCrawlJob.php
    - php/lib/Repair/AppInstallStep.php
    - php/lib/Command/IndexCommand.php
  modified:
    - php/appinfo/info.xml

key-decisions:
  - "QueuedJob entfernt sich laut Basisklasse selbst aus der Jobliste, bevor run() laeuft: der Bauplan verlangt das Verhalten, ein zusaetzlicher remove()-Aufruf waere Doppelarbeit und wurde stattdessen kommentiert"
  - "IMimeTypeLoader::exists() vor getId(): getId legt einen unbekannten Mimetype in der Datenbank an, ein Aufzaehlungsdienst darf beim Lesen nichts schreiben"
  - "Der Cursor wandert auch fuer zu grosse Dateien weiter, sonst bekaeme jede folgende Scheibe dieselbe Datei erneut"
  - "--restart raeumt haengengebliebene Crawl-Jobs weg, bevor es den Planer neu einreiht: sonst laufen zwei Crawls je Mount, einer mit altem Cursor und einer von vorn"
  - "--status ist die Vorgabe des occ-Kommandos, --restart braucht die ausdrueckliche Option und am interaktiven Terminal eine Bestaetigung (Vertrauensgrenze des Bedrohungsregisters)"
  - "root_id statt overridden_root geht in die Queue-Zeile: overridden_root ist die Crawl-Startmarke, root_id die Identitaet des Mounts"
  - "repair-steps und commands stehen je auf einer Zeile, weil das Schemamuster fuer PHP-Klassennamen keinen umgebenden Leerraum erlaubt"

patterns-established:
  - "Ein Repair-Step faengt jeden Fehler ab und nennt im Log den Handgriff, der ihn ersetzt"
  - "Merkmarke in der App-Config statt Idempotenz-Annahme: Install-Steps laufen bei jedem Aktivieren erneut"
  - "Logzeilen tragen Zaehler, Storage-Kennung und Cursor, nie einen Pfad oder Dateinamen"

requirements-completed: [IDX-01, IDX-06]

# Metrics
duration: 34 min
completed: 2026-08-31
---

# Phase 2 Plan 04: Crawl je Mount mit Cursor in der Datenbank Summary

**Der Erstindex startet beim Install von selbst, laeuft Mount fuer Mount ueber die 32er-Aufzaehlungs-API, traegt seine Fortschrittsmarke im Jobargument und verbucht jede zu grosse Datei sichtbar, statt sie zu uebergehen.**

## Performance

- **Duration:** 34 min
- **Started:** 2026-08-31T21:25:00Z
- **Completed:** 2026-08-31T21:59:00Z
- **Tasks:** 3
- **Files created:** 5, **modified:** 1

## Accomplishments

- `StorageService` ist die einzige Stelle der App, die Mounts und Dateien aufzaehlt, und sie tut das ausschliesslich ueber `IFileAccess`. Es gibt keine handgeschriebene Abfrage gegen den Dateicache und keinen zweiten Codepfad fuer aeltere Server: `min-version 32` ist die Gegenleistung fuer rund 150 nicht geschriebene Zeilen Dialektpflege, und der Klassenkommentar sagt das so.
- Die Mount-Allowlist steht woertlich wie im Research. External Storage ist als kommentierte Zeile mit Begruendung erhalten geblieben, damit der Schalter aus Phase 4 (ADM-04) an derselben Stelle entsteht, an der die Auslassung steht.
- `onlyUserFilesMounts = true` biegt den Home-Root auf den `files`-Ordner um. Papierkorb und Versionen tauchen dadurch gar nicht erst auf, das ist die Streichung einer ganzen Klasse falscher Indexeintraege statt einer Nachfilterung.
- Die Dokument-Allowlist wird in numerische Mimetype-IDs uebersetzt und reist in die Abfrage. Unbekannte Typen fallen heraus, statt angelegt zu werden.
- `SchedulerJob` macht aus der Mountliste je einen `StorageCrawlJob` und schreibt den Zeitstempel "ein Job dieser App lief" in die App-Config. Das ist die Datenerhebung fuer die Cron-Diagnose der Phase 4.
- `StorageCrawlJob` liest eine Scheibe von hoechstens 2000 Eintraegen oder 30 Sekunden, fuehrt `last_file_id` fort und plant seinen eigenen Nachfolger. Kommt nichts mehr, plant er nicht nach: das ist die einzige Art, wie der Crawl endet.
- Der 50-MB-Deckel erzeugt `skipped(too_large)` ueber den `FileStateService`, also einen sichtbaren Endzustand vor jedem Byteabruf.
- `AppInstallStep` reiht den Planer beim ersten Install ein, merkt sich das und faengt jeden Fehler ab. Ein Repair-Step, der wirft, nimmt die Installation der App mit, und "die Suchapp installiert sich nicht" ist das schlechtere Ergebnis als "der Erstindex muss von Hand gestartet werden".
- `occ findling:index` zeigt die Zaehler und den letzten Job-Lauf; `--restart` ist die ausdrueckliche Option und fragt am interaktiven Terminal nach.
- `info.xml` registriert beides, steht auf `0.2.0` und erklaert in der Store-Beschreibung, dass der Erstindex einen laufenden Cron braucht.

## Task Commits

1. **Task 1: StorageService, die einzige Stelle mit Mount- und Dateiaufzaehlung** - `c66ffba` (feat)
2. **Task 2: Planer- und Crawl-Job mit Cursor in der Jobliste und sichtbarem Groessendeckel** - `37655fa` (feat)
3. **Task 3: Auto-Start beim Install, occ-Notfallhebel und Registrierung in info.xml** - `540141a` (feat)

## Files Created/Modified

- `php/lib/Service/StorageService.php` - `getMounts`, `getFilesInMount`, `getAllowedMimeIds`; `MOUNT_PROVIDERS` und `ALLOWED_MIMETYPES` als Konstanten, IDs einmal je Prozess aufgeloest
- `php/lib/BackgroundJobs/SchedulerJob.php` - ein Crawl-Job je Mount, `LAST_JOB_RUN` als oeffentliche Konfigurationsschluessel-Konstante
- `php/lib/BackgroundJobs/StorageCrawlJob.php` - `BATCH_SIZE = 2000`, `MAX_SECONDS = 30`, `INTERVAL = 5`, `MAX_SIZE = 50 MB`; Cursorfortschreibung mit dem IDX-02-Kommentar an genau dieser Zeile
- `php/lib/Repair/AppInstallStep.php` - `FIRST_INDEX_SCHEDULED`, `IRepairStep::run` vollstaendig in einem `try`
- `php/lib/Command/IndexCommand.php` - `findling:index` mit `--status` (Vorgabe) und `--restart` inklusive Bestaetigung und Aufraeumen alter Crawl-Jobs
- `php/appinfo/info.xml` - `repair-steps`, `commands`, Version `0.2.0` mit Kopplungskommentar, Cron-Erwartung in der Store-Beschreibung

## Decisions Made

- **Kein zusaetzliches `remove()` in den Jobs.** `OCP\BackgroundJob\QueuedJob::start()` ruft `removeById()` bzw. `remove()`, bevor `run()` ueberhaupt beginnt (Quellcode `stable32` geprueft). Der Bauplan verlangt das Verhalten "entfernt sich selbst aus der Jobliste"; es ist vorhanden, ein eigener Aufruf waere ein zweiter Loeschversuch auf eine schon geloeschte Zeile. Stattdessen steht die Zusicherung als Kommentar in beiden Jobklassen, damit niemand sie fuer vergessen haelt.
- **`IMimeTypeLoader::exists()` vor `getId()`.** Der Docblock von `getId` sagt ausdruecklich "adding the mimetype to the DB if it does not exist". Ohne die Vorpruefung wuerde ein reiner Aufzaehlungsdienst bei jedem Start bis zu dreizehn Zeilen in die Mimetype-Tabelle schreiben, nur um sie danach als Filter zu benutzen, der garantiert nichts trifft.
- **Der Cursor wandert auch fuer uebersprungene Dateien.** Eine 4-GB-Datei, deren ID den Cursor nicht bewegt, waere in jeder folgenden Scheibe wieder der erste Treffer. `max($lastFileId, $entry->getId())` steht deshalb vor der Deckelpruefung.
- **`root_id` in die Queue-Zeile, `overridden_root` in die Abfrage.** Beide Werte reisen im Jobargument. `overridden_root` ist die umgebogene Startmarke der Aufzaehlung, also eine Eigenschaft des Crawls; `root_id` ist die Identitaet des Mounts und damit das, was die Queue-Zeile ueber ihre Herkunft aussagen soll.
- **`--status` ist die Vorgabe.** Die Vertrauensgrenze des Bedrohungsregisters sagt, ein Wiederaufbau darf nicht versehentlich ausloesbar sein. Ein Kommando, das ohne Argumente liest, kann nicht versehentlich schreiben; die Bestaetigung am interaktiven Terminal ist die zweite Sperre und faellt unter `--no-interaction` bewusst weg, damit CI und Support skripten koennen.
- **Beide Registrierungsbloecke einzeilig.** Das Schemamuster fuer `php-class` ist `[a-zA-Z_][0-9a-zA-Z_]*(\\[a-zA-Z_][0-9a-zA-Z_]*)*` ohne Leerraumtoleranz, und `xs:string` bewahrt Leerraum. Ein eingerueckter Klassenname auf eigener Zeile faellt durch `xmllint --schema`. Lokal am echten Store-Weg gemessen, nicht angenommen.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] `--restart` raeumt alte Crawl-Jobs weg**

- **Found during:** Task 3
- **Issue:** Der Bauplan beschreibt `--restart` als "Merkmarke loeschen, SchedulerJob neu einreihen". Damit blieben die vorhandenen `StorageCrawlJob`-Eintraege stehen, jeder mit dem Cursor seines Mounts. Nach einem Neustart liefen dann zwei Crawls je Mount: der alte ab der Mitte und der neue von vorn. Das verdoppelt die Last des Erstindex genau in dem Moment, in dem ein Admin ihn neu startet, weil etwas nicht stimmt.
- **Fix:** `restart()` ruft `IJobList::remove(StorageCrawlJob::class)` und `remove(SchedulerJob::class)` ohne Argument, bevor der Planer neu eingereiht wird. Das Einreihen bleibt idempotent, weil der Unique-Index auf `file_id` aus Plan 02-03 die Deduplizierung traegt.
- **Files modified:** php/lib/Command/IndexCommand.php
- **Verification:** `php -l` sauber, Abnahmekriterien von Task 3 unveraendert bestanden.
- **Committed in:** `540141a`

**2. [Rule 2 - Missing critical functionality] Bestaetigung vor dem Neustart**

- **Found during:** Task 3
- **Issue:** Das Bedrohungsregister fuehrt "occ-Kommando zum Admin" als Vertrauensgrenze mit der Begruendung, ein Wiederaufbau sei teuer und duerfe nicht versehentlich ausloesbar sein. Der Bauplan nennt dafuer keine Massnahme.
- **Fix:** `--status` ist die Vorgabe, wenn keine Option gesetzt ist; `--restart` fragt am interaktiven Terminal nach und laeuft unter `--no-interaction` durch, damit CI und Skripte nicht haengen.
- **Files modified:** php/lib/Command/IndexCommand.php
- **Verification:** `php -l` sauber.
- **Committed in:** `540141a`

**3. [Rule 1 - Bug] Argumentpruefung im Crawl-Job**

- **Found during:** Task 2
- **Issue:** Das Codebeispiel des Research castet die drei Argumente ungeprueft. Ein Jobargument, das einen Mount nennt, den es nicht mehr gibt, oder das durch eine spaetere Schemaaenderung unvollstaendig ist, wuerde eine leere Aufzaehlung liefern und sich trotzdem nicht neu planen, im schlechteren Fall aber gegen `storage_id = 0` laufen. Ein Job, der sich gegen einen nicht existierenden Mount endlos nachplant, ist genau die Fehlerklasse, die der Erstindex nicht haben darf.
- **Fix:** `storage_id` und `overridden_root` werden auf `> 0` geprueft; sonst eine Warnung mit der Storage-Kennung und Abbruch ohne Nachplanung.
- **Files modified:** php/lib/BackgroundJobs/StorageCrawlJob.php
- **Verification:** `php -l` sauber, Abnahmekriterien von Task 2 unveraendert bestanden.
- **Committed in:** `37655fa`

**4. [Rule 2] Zeitstempel des Job-Laufs auch im Crawl-Job**

- **Found during:** Task 2
- **Issue:** Der Bauplan verlangt den Zeitstempel nur im `SchedulerJob`. Der laeuft aber genau einmal. Nach zwei Wochen Erstindex stuende in der Datenbank weiterhin der Zeitpunkt der Installation, und die Cron-Diagnose der Phase 4 wuerde einen laufenden Cron als tot melden.
- **Fix:** `StorageCrawlJob` schreibt denselben Schluessel am Ende jeder Scheibe. Der Schluessel ist eine oeffentliche Konstante des `SchedulerJob`, es gibt also weiterhin genau eine Definition.
- **Files modified:** php/lib/BackgroundJobs/StorageCrawlJob.php
- **Verification:** Grep-Gate `setValueInt` im `SchedulerJob` unveraendert bei 1.
- **Committed in:** `37655fa`

**5. [Rule 3 - Blocking] `php.yml` ist im Worktree nicht auswertbar, Ersatzpruefung lokal**

- **Found during:** alle drei Tasks
- **Issue:** Jedes Task hat als letztes Abnahmekriterium `gh run list --workflow=php.yml --limit 1 --json conclusion` mit dem Wert `success`. Dieser Executor laeuft in einem Worktree und pusht nicht; ohne Push gibt es keinen Lauf, und der letzte vorhandene Lauf gehoert zu fremdem Code. Auf der Entwicklungsmaschine gibt es weder PHP noch `xsltproc` oder `xmllint`. Projektregel: dokumentieren, nicht simulieren.
- **Fix:** **Beide** Jobs von `php.yml` wurden lokal identisch nachgestellt, nicht nur der Lint wie in Plan 02-03. Job `lint`: `docker run --rm php:8.2-cli` mit exakt dem Kommando des Workflows und exakt der Version der CI (PHP 8.2), Ergebnis nach jedem Task 12 Dateien ohne Syntaxfehler. Job `app-metadata`: `docker run --rm debian:trixie-slim` mit `xsltproc` und `xmllint`, `pre-info.xslt` und `info.xsd` vom **selben gepinnten Commit** `5c4373d7d026a8f7c7838cc9990fecaf19e8e682` wie im Workflow, ueber beide `info.xml`. Ergebnis: `- validates` fuer `php/appinfo/info.xml` und fuer `backend/appinfo/info.xml`. Das normalisierte Dokument wurde ausgedruckt und zeigt `repair-steps` und `commands` unveraendert. Das Hilfsverzeichnis wurde vor dem Commit wieder entfernt.
- **Files modified:** keine
- **Verification:** **Offen bis zum Orchestrator-Push.** Danach mit `gh run list --workflow=php.yml --limit 1 --json conclusion -q '.[0].conclusion'` den Wert `success` bestaetigen.
- **Committed in:** keiner (Pruefschritt)

---

**Total deviations:** 5 auto-fixed (1 Bug, 3 fehlende Notwendigkeiten, 1 blockierendes CI-Kriterium)

## Acceptance Criteria

| Kriterium | Soll | Ist |
|---|---|---|
| `getDistinctMounts` in StorageService | 1 | 1 |
| `getByAncestorInStorage` in StorageService | 1 | 1 |
| `getMountsOld\|getFilesInMountOld\|isFileAccessAvailable` | 0 | 0 |
| `Files_External` in StorageService, auskommentiert | 1 | 1, Zeile 50, `// 'OCA\Files_External\Config\ConfigAdapter'` |
| `GroupFolders` in StorageService | >= 1 | 1 |
| `SELECT \|oc_filecache` in StorageService | 0 | 0 |
| `scheduleAfter` in StorageCrawlJob | >= 1 | 1 |
| `last_file_id` in StorageCrawlJob | >= 3 | 3 |
| `too_large` in StorageCrawlJob | >= 1 | 1 |
| `StorageCrawlJob` in SchedulerJob | >= 1 | 1 |
| `setAppValue\|setValueInt\|setValueString` in SchedulerJob | >= 1 | 1 |
| Logaufruf mit Pfad in `php/lib/BackgroundJobs/*.php` | 0 Treffer | 0 Treffer |
| `repair-steps` in info.xml | 1 | 1 |
| `<commands>` in info.xml | 1 | 1 |
| `<version>0.2.0</version>` | 1 | 1 |
| `xml.etree.ElementTree.parse(info.xml)` | Exit 0 | Exit 0 |
| `background job\|cron` in info.xml (case-insensitive) | >= 1 | 4 |
| `IAppConfig\|getAppValue\|getValueString` in AppInstallStep | >= 1 | 2 |
| `php -l` ueber `php/lib` und `php/appinfo` | sauber | 12 Dateien, 0 Fehler |
| Store-Weg `xsltproc pre-info.xslt \| xmllint --schema info.xsd` | validates | beide info.xml `validates` |

Verification-Block des Plans:

| Punkt | Ergebnis |
|---|---|
| php.yml gruen inklusive XSD-Validierung | lokal an beiden Jobs nachgestellt und bestanden, CI-Bestaetigung nach dem Push (Deviation 5) |
| Kein Kompatibilitaetszweig fuer Server unter 32 | `grep -rE 'getMountsOld\|getFilesInMountOld\|isFileAccessAvailable\|version_compare' php/lib php/appinfo` ohne Treffer |
| Version steht auf 0.2.0 | ja |

## Known Stubs

Keine. Alle fuenf Klassen sind vollstaendig implementiert. Was fehlt, fehlt planmaessig:

- Niemand holt die eingereihten Zeilen bisher ab. Der Poller ist Plan 02-10.
- Die Anzeige des Cron-Zeitstempels ist Phase 4; die Erhebung entsteht hier, weil ein Zeitstempel sich nicht rueckwirkend rekonstruieren laesst.
- External Storage bleibt ausgeschlossen, bis ADM-04 in Phase 4 den Schalter baut. Die Zeile steht kommentiert an ihrem Platz.
- Die ExApp-`info.xml` steht weiterhin auf `0.1.0`; die Versionskopplung zieht laut Bauplan in Plan 02-07 nach.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat-Registers. Die sechs mitigierten Eintraege sind umgesetzt:

| Threat ID | Umsetzung |
|-----------|-----------|
| T-02-41 (Information Disclosure) | `MOUNT_PROVIDERS` enthaelt nur Home- und Team-Folder-Provider; External Storage ist auskommentiert und die Auslassung ist mit Begruendung kommentiert |
| T-02-42 (Information Disclosure) | `getDistinctMounts(..., true)`; Papierkorb und Versionen werden nicht aufgezaehlt |
| T-02-43 (Information Disclosure) | `getByAncestorInStorage(..., endToEndEncrypted: false, serverSideEncrypted: true)` |
| T-02-44 (Denial of Service) | `BATCH_SIZE = 2000` und `MAX_SECONDS = 30` je Durchgang, danach `scheduleAfter` mit `INTERVAL = 5` |
| T-02-45 (Denial of Service) | `AppInstallStep::run` liegt vollstaendig in einem `try`, faengt `\Throwable`, loggt und nennt im `IOutput::warning` den Ersatzhandgriff |
| T-02-46 (Denial of Service) | `MAX_SIZE = 50 MB` greift beim Einreihen, also vor jedem Byteabruf, und erzeugt `skipped(too_large)` statt eines stillen Uebergehens |

## User Setup Required

None. Der Repair-Step laeuft beim naechsten Aktivieren bzw. `occ upgrade` und reiht den Planer ein. Wer den Erstindex sofort sehen will, nimmt die deterministischen Anstoesse aus dem Research:

```
occ background-job:worker 'OCA\Findling\BackgroundJobs\SchedulerJob'   --once
occ background-job:worker 'OCA\Findling\BackgroundJobs\StorageCrawlJob' --stop-after 120
occ findling:index --status
```

## Next Phase Readiness

- **Bereit fuer 02-10 (Poller):** Die Queue fuellt sich jetzt tatsaechlich. Der Poller findet Zeilen vor, sobald der Cron einmal gelaufen ist.
- **Bereit fuer 02-07:** Die ExApp-`info.xml` muss auf `0.2.0` nachziehen, der Kopplungskommentar steht in `php/appinfo/info.xml`.
- **Offen fuer 02-14:** Der Abnahmetest "docker kill mitten im Erstindex, Neustart, Fortsetzung" hat mit `last_file_id` im Jobargument jetzt seine PHP-Haelfte. Der Nachweis gehoert in die CI der Verifikationsplaene.
- **Offen fuer Phase 4:** `findling.last_job_run` in der App-Config ist die Datenbasis der Cron-Diagnose, `findling.first_index_scheduled` die Merkmarke des Erstindex.
- **Hinweis fuer den Orchestrator:** Nach dem Push den ersten `php.yml`-Lauf bestaetigen (Deviation 5). Die PHP-Haelfte ist weiterhin ohne Unit-Tests (`docs/testing.md`); die dort gefuehrte Liste waechst mit diesem Plan um mindestens zwei Verhaltensweisen: "eine zu grosse Datei wird nicht eingereiht, erhaelt aber skipped(too_large)" und "ein Crawl-Job ohne Treffer plant sich nicht nach".

## Self-Check: PASSED

- Alle fuenf angelegten Dateien auf der Platte vorhanden, die geaenderte ebenfalls.
- Alle drei Commits im Log: `c66ffba`, `37655fa`, `540141a`.
- Keine ungewollte Loeschung: `git diff --diff-filter=D HEAD~1 HEAD` nach jedem Commit leer.
- Arbeitsverzeichnis nach Task 3 sauber, das Hilfsverzeichnis der Store-Validierung wurde vor dem Commit entfernt.
- Keine Aenderung an STATE.md, ROADMAP.md oder REQUIREMENTS.md.
- Branch durchgehend `gsd/agent-02-04`, Basis `dd98d8a`.

---
*Phase: 02-indexkern-und-volltextsuche*
*Completed: 2026-08-31*
