---
phase: 02-indexkern-und-volltextsuche
plan: 03
subsystem: php-companion
tags: [pull-queue, migration, qbmapper, zeilensperre, upsert, ocs, exapp, rueckkanal, idx-06]

# Dependency graph
requires:
  - phase: 01-05
    provides: "OCSController-Muster, ExApp-Bindung und EX-APP-ID-Vergleich aus dem Content-Gateway"
provides:
  - "Tabelle findling_queue mit Eindeutigkeit auf file_id als Deduplizierung"
  - "Tabelle findling_file_state als einziger Wahrheitsort fuer skipped und failed"
  - "QueueMapper: Zeilensperre als bedingtes UPDATE, LOCK_TIMEOUT 900 s, Byte-Budget im Stapel"
  - "QueueService: Source-Objekte mit userIds und fetchAs, Aufgabe bei drei erfolglosen Zustellungen"
  - "FileStateService: geschlossene Liste aus 3 Zustaenden und 16 Gruenden, einziger Schreiber der Zustandstabelle"
  - "Vier ExApp-gebundene OCS-Endpunkte: holen, quittieren, entsperren, zaehlen"
affects: [02-04, 02-10, 02-14, phase-03-events, phase-04-statusseite]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Upsert als Konfliktzweig: insert, REASON_UNIQUE_CONSTRAINT_VIOLATION fangen, dann update, statt einer Upsert-Klausel eines Dialekts"
    - "Zeilensperre ausschliesslich als bedingtes UPDATE mit wiederholter Frei-Bedingung im WHERE, kein SELECT-Lock"
    - "Zeitvergleiche der Sperre in UTC, damit die Sommerzeitumstellung keine Sperre verlaengert oder verkuerzt"
    - "Attribute voll qualifiziert am Methodenkopf, damit Grep-Gates Attribute zaehlen und nicht Importe"
    - "Geschlossene Wertelisten als oeffentliche Konstanten des schreibenden Service, gegen die der Controller validiert"

key-files:
  created:
    - php/lib/Migration/Version001000Date20260816000000.php
    - php/lib/Db/QueueFile.php
    - php/lib/Db/QueueMapper.php
    - php/lib/Service/QueueService.php
    - php/lib/Service/FileStateService.php
    - php/lib/Controller/QueueController.php
  modified:
    - php/appinfo/routes.php

key-decisions:
  - "Upsert als Konfliktzweig statt als Upsert-Klausel: der oeffentliche IQueryBuilder von Nextcloud hat keine Upsert-Methode, die ueber SQLite, MariaDB und PostgreSQL nachweislich gleich traegt; REASON_UNIQUE_CONSTRAINT_VIOLATION ist dialektneutral und seit NC 21 oeffentlich. Plan 02-14 weist das Verhalten gegen einen zweiten Dialekt nach, der Fix bliebe lokal"
  - "Die Metadaten des Source-Objekts kommen aus dem Node im Kontext von fetchAs (getUserFolder + getFirstNodeById), nicht aus IFileAccess: dasselbe Muster wie im Content-Gateway aus Phase 1, und die Nutzerliste wird ohnehin gebraucht"
  - "retries wird beim Zuteilen hochgezaehlt, nicht beim Quittieren: die Zustellung IST der Versuch, und nur so ist repeatedly_stuck ueberhaupt messbar"
  - "enqueue erneuert zusaetzlich size, nicht nur is_update und locked_at: das Byte-Budget des naechsten Stapels wird aus dieser Spalte gerechnet, eine geaenderte Datei hat eine andere Groesse"
  - "Der Konfliktzweig laesst retries bewusst stehen: eine Zeile, die durch wiederholte Aenderungen zurueckkommt, muss ihren Endzustand trotzdem erreichen koennen"
  - "acknowledge liegt im QueueService, nicht im Controller: die Transaktion umschliesst Zustandsschreiben und Loeschen, und der Controller bleibt reine Grenzpruefung"
  - "Der EX-APP-ID-Vergleich aus dem Content-Gateway wird auf alle vier Endpunkte uebernommen (Rule 2): das Attribut beweist nur, dass irgendeine ExApp ruft"
  - "Malformte Listen werden abgelehnt statt gefiltert: eine teilweise angenommene Quittung liesse den Worker glauben, Zeilen seien weg, die noch da sind"

patterns-established:
  - "Kein Select vor einem Insert: Eindeutigkeit im Index, Konflikt fangen, Konflikt aufloesen"
  - "Nie ein roher Eingabewert im Log; verworfene Werte werden nur gezaehlt"
  - "Ein Endpunkt, eine Grenze: n, max_bytes und Listenlaenge werden am Controller hart geklemmt, nie im Service"

requirements-completed: [IDX-03, IDX-06, COMP-04]

# Metrics
duration: 26 min
completed: 2026-08-31
---

# Phase 2 Plan 03: Pull-Queue auf der Nextcloud-Seite Summary

**Zwei App-eigene Tabellen, eine Zeilensperre, die ein bedingtes UPDATE ist und nach 15 Minuten von selbst verfaellt, und vier ExApp-gebundene Endpunkte, ueber die der Container Arbeit holt, quittiert, zurueckgibt und dabei meldet, was er nicht verarbeiten konnte.**

## Performance

- **Duration:** 26 min
- **Started:** 2026-08-31T19:10:00Z
- **Completed:** 2026-08-31T19:36:00Z
- **Tasks:** 3
- **Files created:** 6, **modified:** 1

## Accomplishments

- `findling_queue` und `findling_file_state` entstehen in einer Migration, deren Klassenname zeichengleich mit dem Dateinamen ist, beide hinter `hasTable()`, damit ein zweiter Lauf folgenlos bleibt.
- Die Deduplizierung ist der Unique-Index auf `file_id`, und sie ist als solche kommentiert. `QueueMapper::enqueue()` faengt den Konflikt und loest ihn in ein UPDATE auf; es gibt in dieser App keinen Select vor einem Insert.
- Die Zeilensperre ist ein UPDATE, das die Frei-Bedingung im WHERE wiederholt. Nur ein `executeStatement() >= 1` gewinnt die Zeile, also bekommen zwei gleichzeitige Abholer nie dieselbe. Kein `SELECT`-Lock, keine dialektspezifische Klausel.
- `LOCK_TIMEOUT` ist eine benannte Konstante mit 900 Sekunden, mit der Begruendung im Kommentar. Weder die Zahl des Vorbilds noch eine Sperrklausel stehen irgendwo in der Datei.
- Der Stapel hat zwei Deckel: Stueckzahl und Byte-Budget, und er liefert trotzdem garantiert mindestens eine Zeile, sonst blockierte eine einzelne grosse Datei den Lauf fuer immer.
- Das Source-Objekt traegt Metadaten und keinen Inhalt, dazu `userIds` als ACL-Nutzlast und `fetchAs` als Abrufkontext, getrennt gehalten mit dem Kommentar, warum das zwei verschiedene Fragen sind.
- Die Nutzerliste kommt je Datei aus dem Mount-Cache. Die bekannte Optimierung ist als aufgeschobene Entscheidung fuer Phase 5 im Code benannt, nicht ausgelassen.
- `FileStateService` ist der einzige Schreiber der Zustandstabelle und prueft Zustand und Grund gegen eine geschlossene Liste aus 3 und 16 Eintraegen. Freier Text, und damit ein Dateiname als Grund, ist strukturell unmoeglich.
- Alle vier Endpunkte tragen die ExApp-Bindung, die CSRF-Ausnahme und ihre Route als voll qualifiziertes Attribut; die Grep-Gates zaehlen exakt 4/4/4.

## Task Commits

1. **Task 1: Migration, Entitaet und die Zeilensperre im Mapper** - `e408f0d` (feat)
2. **Task 2: QueueService mit Source-Objekten und FileStateService als Rueckkanal** - `bbbab83` (feat)
3. **Task 3: Vier ExApp-gebundene OCS-Endpunkte inklusive Rueckkanal** - `f74eea7` (feat)

## Files Created/Modified

- `php/lib/Migration/Version001000Date20260816000000.php` - beide Tabellen, Existenzpruefung, Kommentare am Unique-Index und an `is_update`
- `php/lib/Db/QueueFile.php` - Entitaet, `addType` fuer die fuenf Integer-Spalten und den Bool; `lockedAt` bewusst ohne registrierten Typ, weil die Sperre nur in der Datenbank verglichen wird
- `php/lib/Db/QueueMapper.php` - `enqueue`, `claimBatch`, `findByIds`, `acknowledge`, `unlock`, `bumpRetries`, `countScheduled`, `countRunning`; `LOCK_TIMEOUT = 900`
- `php/lib/Service/QueueService.php` - `claim`, `enqueue`, `acknowledge`, `unlock`, `stats`; Source-Aufbau, `skipped(gone)`-Pfad, Aufgabe bei `MAX_ATTEMPTS = 3`
- `php/lib/Service/FileStateService.php` - `record`, `counts`, `STATES`, `REASONS`; Upsert auf den Primaerschluessel, Verworfenes wird nur gezaehlt
- `php/lib/Controller/QueueController.php` - vier Endpunkte, harte Grenzen, Fremd-ExApp-Abweisung, Rueckkanal im DELETE
- `php/appinfo/routes.php` - Kommentar richtiggestellt: es sind jetzt fuenf Attribut-Routen, nicht nur das Gateway

## Decisions Made

- **Upsert als Konfliktzweig.** Der Plan liess `IQueryBuilder::insertOrUpdate` "bzw. den Konfliktzweig" zu. Der oeffentliche `IQueryBuilder` von Nextcloud hat keine Upsert-Methode, deren Verhalten ueber die drei Zieldialekte belegt waere; `OCP\DB\Exception::REASON_UNIQUE_CONSTRAINT_VIOLATION` ist seit NC 21 oeffentlich und dialektneutral. Der Kommentar an der Methode nennt Plan 02-14 als Nachweisstelle, wie im Bauplan gefordert.
- **Metadaten aus dem Node, nicht aus dem File-Cache.** `getUserFolder($fetchAs)->getFirstNodeById($fileId)` ist genau das Muster, das der Content-Gateway aus Phase 1 bereits benutzt und das in `integration.yml` durchgemessen ist. Die Nutzerliste muss ohnehin aufgeloest werden, also kostet der Node nichts zusaetzlich an Entscheidungen, und `IFileAccess::getByFileId` bleibt eine unbelegte Annahme, die nicht noetig ist.
- **`retries` zaehlt Zustellungen, nicht Fehlschlaege.** Nur so ist "dreimal gesperrt, nie quittiert" ueberhaupt beobachtbar. Der Zaehler wird in der Datenbank erhoeht (`retries + 1`), nicht gelesen, erhoeht und zurueckgeschrieben, sonst gingen Erhoehungen bei zwei Abholern verloren.
- **UTC fuer Sperrzeiten.** Geschrieben und verglichen wird in derselben Zone. Eine lokale Zone springt zweimal im Jahr um eine Stunde, was jede offene Sperre genau einmal unbemerkt verlaengerte oder verkuerzte.
- **`acknowledge` im Service statt im Controller.** Die Transaktion muss Zustandsschreiben und Loeschen umschliessen; im Controller haette das den Mapper und die Datenbankverbindung in die Grenzschicht geholt. Der Controller macht jetzt nur Grenzpruefung und delegiert, der Schluessel-Link Controller -> QueueService bleibt genau wie im Bauplan.
- **Abweisen statt Filtern bei malformten Listen.** Eine still gefilterte Quittung liesse den Worker glauben, Zeilen seien entfernt, die noch in der Queue stehen; die naechste Zustellung waere dann eine Doppelverarbeitung ohne Fehlermeldung.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] EX-APP-ID-Vergleich auf allen vier Endpunkten**
- **Found during:** Task 3
- **Issue:** Das ExApp-Attribut beantwortet "ist der Aufrufer eine registrierte ExApp", nicht "ist er unsere". Ohne Vergleich koennte jedes andere Backend der Instanz den Arbeitsvorrat leerraeumen oder Zustaende fuer Dateien schreiben, die es nie gesehen hat. Der Bauplan nennt den Vergleich nicht, das Bedrohungsregister verlangt ihn aber (T-02-31), und der Content-Gateway aus Phase 1 macht es bereits so.
- **Fix:** `rejectForeignCaller()` als privater Wachposten, in jedem der vier Endpunkte die erste Anweisung; Antwort 403 mit derselben Formulierung wie im Gateway.
- **Files modified:** php/lib/Controller/QueueController.php
- **Verification:** Grep-Gates unveraendert bei 4/4/4, `php -l` sauber.
- **Committed in:** `f74eea7`

**2. [Rule 1 - Bug] Falscher Kommentar in `php/appinfo/routes.php`**
- **Found during:** Task 3
- **Issue:** Die Datei behauptete "die einzige Route dieser App ist der Content-Gateway". Ab diesem Commit sind es fuenf. Ein falscher Kommentar an genau der Stelle, an der jemand nach den Routen sucht, ist teurer als kein Kommentar.
- **Fix:** Satz auf "der Content-Gateway und die vier Queue-Endpunkte" umgestellt, Begruendung fuer die leeren Arrays unveraendert.
- **Files modified:** php/appinfo/routes.php
- **Verification:** `php -l` sauber, beide Arrays weiterhin leer.
- **Committed in:** `f74eea7`

**3. [Rule 2] Zwei Methoden mehr als im Bauplan aufgezaehlt**
- **Found during:** Task 2 und Task 3
- **Issue:** Der Rueckkanal braucht die Uebersetzung von der Queue-ID zur file_id, bevor die Zeile geloescht wird; danach ist die Verbindung weg. Ausserdem braucht der Unlock-Endpunkt einen Weg durch den Service.
- **Fix:** `QueueMapper::findByIds()` und `QueueService::acknowledge()` bzw. `QueueService::unlock()` ergaenzt. Alles im Bauplan genannte existiert unveraendert daneben.
- **Files modified:** php/lib/Db/QueueMapper.php, php/lib/Service/QueueService.php
- **Verification:** Alle Abnahmekriterien der Tasks 1 bis 3 bestanden.
- **Committed in:** `bbbab83`, `f74eea7`

**4. [Rule 3 - Blocking] `php.yml` ist im Worktree nicht auswertbar, Ersatzpruefung lokal**
- **Found during:** alle drei Tasks
- **Issue:** Jedes der drei Tasks hat als letztes Abnahmekriterium `gh run list --workflow=php.yml --limit 1 --json conclusion` mit dem Wert `success`. Dieser Executor laeuft in einem Worktree und darf nicht pushen; ohne Push gibt es keinen Lauf, und der letzte vorhandene Lauf gehoert zu fremdem Code. Laut Projektregel wird so etwas dokumentiert, nicht simuliert. Auf der Entwicklungsmaschine gibt es zudem kein PHP (`php: command not found`), so wie in `php.yml` selbst festgehalten.
- **Fix:** Der Lint-Job wurde lokal identisch nachgestellt: `docker run --rm php:8.2-cli` mit exakt dem Kommando des Workflows (`find php/lib php/appinfo -name '*.php' -print0 | xargs -0 -n1 php -l`) und exakt der Version der CI (PHP 8.2). Ergebnis nach jedem Task: acht Dateien, kein Syntaxfehler. Der zweite Job (`app-metadata`) ist nicht betroffen, weil keine `info.xml` angefasst wurde.
- **Files modified:** keine
- **Verification:** **Offen bis zum Orchestrator-Push.** Danach mit `gh run list --workflow=php.yml --limit 1 --json conclusion -q '.[0].conclusion'` den Wert `success` bestaetigen.
- **Committed in:** keiner (Pruefschritt)

---

**Total deviations:** 4 auto-fixed (1 Bug, 2 fehlende Notwendigkeiten, 1 blockierendes CI-Kriterium)

## Acceptance Criteria

Alle dateibezogenen Kriterien der drei Tasks wurden ausgefuehrt und bestanden:

| Kriterium | Soll | Ist |
|---|---|---|
| `createTable('findling_queue')` | 1 | 1 |
| `createTable('findling_file_state')` | 1 | 1 |
| `findling_q_fileid` | 1 | 1 |
| `addColumn('update'` | 0 | 0 |
| `LOCK_TIMEOUT` im Mapper | >= 2 | 4 |
| `86400|FOR UPDATE` im Mapper | 0 | 0 |
| Klassenname == Dateiname | ja | `Version001000Date20260816000000` |
| `getMountsForFileId` im QueueService | 1 | 1 |
| `getMountsForStorageId` im QueueService | 0 | 0 |
| `Phase 5` im QueueService | >= 1 | 1 |
| `fetchAs` / `maxBytes` | >= 1 / >= 2 | 4 / 2 |
| Gruende im FileStateService | >= 2 | 4 |
| Logaufruf mit Pfad in `php/lib/Service/*.php` | 0 | 0 |
| `ExAppRequired` / `ApiRoute` / `NoCSRFRequired` | 4 / 4 / 4 | 4 / 4 / 4 |
| `queues/documents` | >= 4 | 8 |
| `failed` im Controller | >= 2 | 5 |
| `fopen|->put(|->touch(` im Controller | 0 | 0 |
| `php -l` ueber `php/lib` und `php/appinfo` | sauber | 8 Dateien, 0 Fehler |

## Known Stubs

Keine. Alle sechs Klassen sind vollstaendig implementiert. Was noch fehlt, fehlt planmaessig und liegt in anderen Plaenen:

- Niemand ruft `QueueService::enqueue()` bisher auf. Der Crawl ist Plan 02-04, und die Signatur nimmt bereits den `ICacheEntry`, den er liefern wird.
- Niemand holt bisher einen Stapel ab. Der Poller ist Plan 02-10, zusammen mit der benannten Ausnahme fuer Gate A ueber die beiden Schreibpfade.
- Der `is_update`-Fall ist implementiert, aber sein Dialektnachweis steht aus (Plan 02-14, offene Frage 4 des Research).

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat-Registers des Plans. Die sieben mitigierten Eintraege sind umgesetzt:

| Threat ID | Umsetzung |
|-----------|-----------|
| T-02-31 (Elevation of Privilege) | ExApp-Attribut an allen vier Methoden, per Grep-Gate gezaehlt, dazu der EX-APP-ID-Vergleich aus Deviation 1 |
| T-02-32 (Information Disclosure) | Antwort traegt Metadaten und keinen Inhalt; kein Logaufruf mit Pfad oder Dateiname, nur Zaehler und Grundcodes |
| T-02-33 (Denial of Service) | `LOCK_TIMEOUT = 900` statt eines Tages, dazu der Unlock-Endpunkt |
| T-02-34 (Denial of Service) | `max_bytes` neben der Stueckzahl, garantiert mindestens eine Zeile; Vorgabe 32 Dateien oder 64 MB |
| T-02-35 (Tampering) | Keine Node-Schreiboperation in den neuen Klassen; Grep-Gate gegen `fopen`, `put` und `touch` bestanden |
| T-02-36 (Denial of Service) | `n` auf 1..256 geklemmt, `max_bytes` auf 1 MB..1 GB, Listen auf 1000 Eintraege, alles auf Integer geprueft |
| T-02-37 (Tampering) | Grund gegen `FileStateService::REASONS` geprueft, im Controller und noch einmal im Service; die Spalte ist 32 Zeichen lang, in die kein Pfad passt |

## User Setup Required

None. Die Migration laeuft beim naechsten `occ upgrade` bzw. beim Aktivieren der App; die App-Version 0.1.0 deckt `Version001000...` ab.

## Next Phase Readiness

- **Bereit fuer 02-04 (Crawl):** `QueueService::enqueue(ICacheEntry, storageId, rootId, isUpdate = false)` steht, der 50-MB-Deckel und `skipped(too_large)` gehoeren dorthin und sind im Kommentar an der Methode als dortige Aufgabe benannt.
- **Bereit fuer 02-10 (Poller):** Das Protokoll steht vollstaendig, inklusive der beiden Schreibpfade, die dort in `OCS_WRITE_ALLOWLIST` aufgenommen werden muessen: `/ocs/v2.php/apps/findling/queues/documents` und `/ocs/v2.php/apps/findling/queues/documents/unlock`. Der Klassenkommentar des Controllers haelt die Bedrohungsmodell-Notiz dafuer bereit.
- **Offen fuer 02-14:** Der Konfliktzweig von `enqueue` und `FileStateService::record` braucht den Dialektnachweis gegen MariaDB. Beide benutzen dasselbe Muster, ein Nachweis deckt beide.
- **Hinweis fuer den Orchestrator:** Nach dem Push den ersten `php.yml`-Lauf bestaetigen (Deviation 4). Ausserdem ist die PHP-Haelfte weiterhin ohne Unit-Tests, wie in `docs/testing.md` festgehalten; die neun dort genannten Verhaltensweisen wachsen mit dieser Queue um mindestens zwei: "zwei gleichzeitige Abholer bekommen nie dieselbe Zeile" und "eine abgelaufene Sperre gibt die Zeile frei".

## Self-Check: PASSED

- Alle sechs angelegten Dateien auf der Platte vorhanden, die geaenderte ebenfalls.
- Alle drei Commits im Log: `e408f0d`, `bbbab83`, `f74eea7`.
- Keine ungewollte Loeschung: `git diff --diff-filter=D HEAD~1 HEAD` nach jedem Commit leer.
- Arbeitsverzeichnis sauber, keine unbeobachteten Dateien.
- Keine Aenderung an STATE.md, ROADMAP.md oder REQUIREMENTS.md.

---
*Phase: 02-indexkern-und-volltextsuche*
*Completed: 2026-08-31*
