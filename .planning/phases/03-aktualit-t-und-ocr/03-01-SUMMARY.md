---
phase: 03-aktualit-t-und-ocr
plan: 01
subsystem: database
tags: [nextcloud, php, event-listener, queue, migration, doctrine]

# Dependency graph
requires:
  - phase: 02-indexkern-und-volltextsuche
    provides: Pull-Queue (QueueMapper, QueueService), Mount- und Mimetype-Grenzen (StorageService), Endzustaende (FileStateService)
provides:
  - "kind-Spalte in findling_queue plus Index findling_q_kind (kind, locked_at, id)"
  - "QueueMapper::KINDS als geschlossene Liste der fuenf Job-Arten"
  - "Sperrfrist je Job-Art (LOCK_TIMEOUTS), 1800 s fuer ocr"
  - "Aufwertungsregel beim Enqueue-Konflikt: nie Abwertung, delete absorbierend, content wirft ocr nicht zurueck"
  - "Claim je Art in fester Reihenfolge acl, delete, metadata, content, ocr mit eigener Batchgroesse"
  - "Feld kind im Quellobjekt und ein einziger Verzweigungspunkt in describe()"
  - "FileEventListener als einziger Ereignisweg fuer neue und geaenderte Dateien"
  - "StorageService::isIndexedStorage als Mount-Gate fuer Ereignisse"
  - "QueueService::enqueueFile als Einreihweg fuer Knoten-Aufrufer"
affects: [03-02 Rename, 03-03 Delete, 03-04 Share und Subtree, 03-05 OCR-Deckel, 03-07 requeueAs und QueueController, 03-12 ETag-Abgleich]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Job-Art als Spalte, Prioritaet als Claim-Reihenfolge statt als Sortierspalte"
    - "Deckel je Job-Art als benannte Konstante (LOCK_TIMEOUTS, KIND_BATCH)"
    - "Ein Listener, typisierte Ereignisse, Registrierung in register() statt boot()"

key-files:
  created:
    - php/lib/Migration/Version001000Date20260902000000.php
    - php/lib/Listener/FileEventListener.php
  modified:
    - php/lib/Db/QueueMapper.php
    - php/lib/Db/QueueFile.php
    - php/lib/Service/QueueService.php
    - php/lib/Service/StorageService.php
    - php/lib/AppInfo/Application.php

key-decisions:
  - "Prioritaet als Schleife ueber KINDS im Claim, keine Prioritaetsspalte: eine Spalte in ORDER BY haette findling_q_free und findling_q_kind entwertet"
  - "Aufwertung als eigenes bedingtes UPDATE mit einer Liste der ueberholten Arten, nicht als CASE-Ausdruck"
  - "refreshExisting rechnet mit der laengsten Sperrfrist, weil es die Zeile nicht liest: lieber eine freie Zeile faelschlich als dirty markieren als die Sperre einer laufenden Zeile loeschen (Bug H4)"
  - "countScheduled und countRunning zaehlen je Art, weil der Ablauf einer Sperre seit dieser Phase kein gemeinsamer Zeitpunkt mehr ist"
  - "Byte- und Zeilendeckel werden ueber die Arten hinweg verbraucht, aber keine Art wird uebersprungen, weil claimBatch immer die erste Zeile liefert (sonst verhungert die OCR-Spur)"
  - "Der Listener nutzt getMountPoint()->getNumericStorageId()/getStorageRootId(), weil FileInfo::getData() erst ab Nextcloud 34 existiert und die App ab 32 laeuft"

patterns-established:
  - "Job-Arten: KINDS ist die einzige Wahrheit, jede neue Art braucht Rang, Sperrfrist und Batchgroesse in derselben Aenderung"
  - "Ereignisweg: ein Listener, vier Ereignisklassen in einer Schleife in register(), drei Fragen vor dem Einreihen (Datei, Mimetype, Mount)"
  - "Listener-Rumpf vollstaendig in try/catch ueber Throwable, geloggt wird nur der Fehlertypname"

requirements-completed: [COMP-03]

# Metrics
duration: 25min
completed: 2026-09-01
---

# Phase 3 Plan 01: Ereignisweg und Job-Art in der Queue Summary

**Die Pull-Queue kennt fuenf Job-Arten mit eigener Sperrfrist und fester Ausgabereihenfolge, und ein einziger Nextcloud-Listener stellt neue und geaenderte Dateien binnen Sekunden hinein.**

## Performance

- **Duration:** rund 25 min
- **Started:** 2026-09-01T07:25Z
- **Completed:** 2026-09-01T07:52Z
- **Tasks:** 3
- **Files modified:** 7 (2 neu, 5 geaendert)

## Accomplishments

- Migration `Version001000Date20260902000000` fuegt die Spalte `kind` (notnull, Default `content`) und den Index `findling_q_kind (kind, locked_at, id)` hinzu, beides mit `hasColumn`/`hasIndex` geschuetzt; `findling_q_free` bleibt fuer die Frage ohne Art.
- `QueueMapper` traegt die geschlossene Liste `KINDS`, die Rangordnung `KIND_RANK` (acl 0 < metadata 1 < content 2 = ocr 2 < delete 3), die Abbildung `LOCK_TIMEOUTS` (900 s, `ocr` 1800 s) und filtert Kandidatenabfrage wie Claim nach Art.
- `QueueService::claim` fragt die Arten in der Reihenfolge acl, delete, metadata, content, ocr, jede mit eigener Batchgroesse (`KIND_BATCH`: 128/128/64/32/2); eine Rechteaenderung ueberholt damit jeden Inhaltsrueckstau.
- `FileEventListener` nimmt `NodeCreatedEvent`, `NodeWrittenEvent`, `NodeTouchedEvent` und `NodeCopiedEvent` entgegen und reiht sie als `content` ein, nach drei Fragen: Datei statt Ordner, Mimetype aus der Crawl-Allowlist, Mount aus `StorageService::getMounts`.
- Die Registrierung steht als Schleife in `Application::register()`, nicht in `boot()`, und es gibt keinen zweiten Ereignisweg ueber AppAPI.

## Task Commits

Jeder Task wurde einzeln committet:

1. **Task 1: Migration und Job-Art in der Queue** , `a10f1dd` (feat)
2. **Task 2: Claim in fester Reihenfolge und Job-Art im Quellobjekt** , `0f4e4d2` (feat)
3. **Task 3: Der eine Ereignisweg fuer neue und geaenderte Dateien** , `9d9d096` (feat)

**Plan-Metadaten:** dieses SUMMARY (docs-Commit im selben Branch)

## Files Created/Modified

- `php/lib/Migration/Version001000Date20260902000000.php` , neu: Spalte `kind`, Index `findling_q_kind`, Sicherheitsnetz fuer leere Werte in `postSchemaChange`.
- `php/lib/Db/QueueMapper.php` , Job-Arten, Rangordnung, Sperrfrist je Art, `kind` in `enqueue`, `claimBatch` je Art, Zaehler je Art, `lockCutoff($now, $seconds)`.
- `php/lib/Db/QueueFile.php` , Eigenschaft `kind`, ohne die `Entity::fromRow` beim Claim ueber die neue Spalte werfen wuerde.
- `php/lib/Service/QueueService.php` , Claim-Schleife ueber `KINDS`, `KIND_BATCH`, gemeinsamer Byte- und Zeilendeckel, Feld `kind` im Quellobjekt, `enqueueFile` fuer Knoten-Aufrufer.
- `php/lib/Service/StorageService.php` , `isIndexedStorage(int $storageId): bool`, einmal je Anfrage aufgeloest.
- `php/lib/Listener/FileEventListener.php` , neu: der eine Ereignisweg, vollstaendig in try/catch, Log nur mit Fehlertypname.
- `php/lib/AppInfo/Application.php` , Registrierung der vier Ereignisklassen in `register()`.

## Decisions Made

- **Reihenfolge statt Prioritaetsspalte.** D-04 wird zu einer Schleife im Claim. Eine Spalte in `ORDER BY` haette beide Indizes der Queue entwertet und einen dritten gebraucht.
- **Aufwertung als eigenes Statement.** `refreshExisting` schickt ein `UPDATE ... SET kind = ? WHERE file_id = ? AND kind IN (ueberholte Arten)`. Die Regel ist damit lesbar und die Datenbank entscheidet weiterhin das Rennen.
- **Laengste Sperrfrist im Konfliktzweig.** `refreshExisting` kennt die Art der vorhandenen Zeile nicht. Die konservative Richtung markiert hoechstens eine freie Zeile als dirty (der naechste Claim raeumt die Marke ab), die andere Richtung wuerde die Sperre einer laufenden Zeile loeschen, also Bug H4 der Phase-2-Pruefung wiederbeleben.
- **Zaehler je Art.** Sonst meldet die Statusseite eine OCR-Zeile als wartend, waehrend der Claim sie noch nicht herausgibt.
- **Keine Aushungerung der OCR-Spur.** Der Bytedeckel wird ueber die Arten hinweg verbraucht, aber keine Art wird uebersprungen: `claimBatch` liefert immer mindestens eine Zeile, und genau diese Untergrenze haelt die nachlaufende Spur aus D-07 am Leben.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Entity `QueueFile` um die Spalte `kind` erweitert**
- **Found during:** Task 1 (Migration und Job-Art)
- **Issue:** `claimBatch` liest die Zeilen mit `SELECT *` und `findEntities`. `Entity::fromRow` ruft fuer jede Spalte den Setter und wirft `BadFunctionCallException`, wenn die Eigenschaft fehlt. Ohne diese Ergaenzung waere jeder Claim nach der Migration mit einer Ausnahme gestorben, und Task 2 braucht `getKind()` ohnehin.
- **Fix:** Eigenschaft `protected string $kind = QueueMapper::KIND_CONTENT;` plus `@method`-Anmerkungen, mit Begruendung im Kommentar.
- **Files modified:** `php/lib/Db/QueueFile.php`
- **Verification:** `php -l` gruen, `getKind()` wird in `QueueService::describe` genutzt.
- **Committed in:** `a10f1dd`

**2. [Rule 3 - Blocking] `QueueService::enqueueFile` als zweiter Einreihweg**
- **Found during:** Task 3 (Ereignisweg)
- **Issue:** `QueueService::enqueue` verlangt ein `ICacheEntry`. Ein Ereignis liefert ein `OCP\Files\Node`; der Cache-Eintrag dahinter ist erst ueber `FileInfo::getData()` erreichbar, und das gibt es erst seit Nextcloud 34, waehrend die App min-version 32 fuehrt. Der Listener haette sonst den Eintrag ueber den internen Pfad nachschlagen muessen, also eine Abfrage je Schreibvorgang der Instanz.
- **Fix:** `enqueueFile(int $fileId, int $storageId, int $rootId, int $size, bool $isUpdate, string $kind = content)`; das bestehende `enqueue(ICacheEntry ...)` delegiert dorthin, der Schluessel-Link Listener zu QueueService bleibt `enqueue`-benannt.
- **Files modified:** `php/lib/Service/QueueService.php`
- **Verification:** `php -l` gruen; `enqueue` ruft `enqueueFile`, der Crawl-Pfad ist unveraendert.
- **Committed in:** `9d9d096`

**3. [Rule 2 - Missing Critical] Groessendeckel auch im Listener**
- **Found during:** Task 3 (Ereignisweg)
- **Issue:** Der Crawl weigert sich, Dateien ueber `StorageCrawlJob::MAX_SIZE` (50 MB) einzureihen, und schreibt `skipped(too_large)`. Der Listener haette denselben Deckel umgangen: ein 2-GB-Upload waere als Queue-Zeile im Container gelandet, auf der 4-GB-Zielhardware. Zusaetzlich waere die Datei ohne Endzustand einfach nicht im Index, also genau die stille Auslassung, die IDX-06 verbietet.
- **Fix:** Dieselbe Konstante, derselbe Endzustand ueber `FileStateService::record($fileId, 'skipped', 'too_large')`.
- **Files modified:** `php/lib/Listener/FileEventListener.php`
- **Verification:** `php -l` gruen; Konstante und Reason-Code stammen aus den bestehenden geschlossenen Listen.
- **Committed in:** `9d9d096`

**4. [Rule 1 - Bug] Zaehler `countScheduled` und `countRunning` je Art**
- **Found during:** Task 1 (Migration und Job-Art)
- **Issue:** `lockCutoff` bekommt die Sekunden jetzt als Argument. Mit einem einzigen Wert haetten die Zaehler eine OCR-Zeile schon nach 900 s als wartend gemeldet, waehrend der Claim sie bis 1800 s nicht herausgibt: die Statusseite der Phase 4 zeigte Arbeit an, die niemand nehmen kann.
- **Fix:** Beide Zaehler summieren ueber `KINDS` mit der Sperrfrist der jeweiligen Art; die Abfragen bedient der neue Index direkt.
- **Files modified:** `php/lib/Db/QueueMapper.php`
- **Verification:** `php -l` gruen; die Bedingung `freeRowCondition` bleibt die einzige Definition von "frei".
- **Committed in:** `a10f1dd`

---

**Total deviations:** 4 auto-fixed (2 Bugs, 1 blockierend, 1 fehlende kritische Funktion)
**Impact on plan:** Alle vier sind Folgen der geplanten Aenderung selbst, keine Ausweitung des Umfangs. Ohne 1 waere der Claim nach der Migration nicht mehr lauffaehig gewesen.

## Issues Encountered

- **Kein PHP auf der Entwicklungsmaschine** (in `docs/testing.md` dokumentiert). Der Syntaxcheck lief stattdessen ueber den laufenden Test-Container: `docker exec -i findling-nextcloud php -l < DATEI`, fuer alle 20 PHP-Dateien der App fehlerfrei. Die CI prueft dieselbe Menge gegen PHP 8.2.
- **Abnahme-Grep `grep -c 'catch (\Throwable'`**: unter Git Bash frisst die MSYS-Schicht die Rueckstriche, der Ausdruck liefert dort 0. Mit `grep -cF 'catch (\Throwable'` liefert dieselbe Datei 1, das Kriterium ist also erfuellt; unter Linux (CI) greift der Ausdruck aus dem Plan unveraendert.
- **Sichtprobe im Test-Nextcloud steht aus.** Der laufende Container `findling-nextcloud` bedient den Hauptcheckout; ein Deploy dieses Branch-Standes waere waehrend der parallelen Ausfuehrung von Plan 03-05 in den gemeinsamen Container hinein gegangen. Upload einer Datei, Zeile mit `kind=content` und der zweite Upload ohne zweite Zeile gehoeren damit in den Integrationslauf der Phase.

## Known Stubs

Keine. Was dieser Plan bewusst nicht baut, ist im Code als Anker mit Plannummer benannt und nicht als leerer Rueckgabewert:

- `QueueService::describe` hat einen dokumentierten Verzweigungspunkt fuer `delete` (Plan 03-03) und `acl` (Plan 03-04); heute nimmt jede Art denselben Weg, was korrekt ist, solange nur create und write in die Queue gelangen.
- `requeueAs` (Plan 03-07) fehlt absichtlich; der Weg `content -> ocr` existiert deshalb noch nicht.
- Rename, Delete und Share sind nicht abonniert, weil ihr Gegenstueck im Container fehlt.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Bedrohungsmodells des Plans. Der Listener schreibt ausschliesslich in `findling_queue` und `findling_file_state`, trifft keine Rechteentscheidung (T-03-101), filtert vor dem Einreihen nach Mimetype und Mount (T-03-102, T-03-106), kann die Nutzeraktion nicht abbrechen (T-03-104) und loggt weder Pfad noch Namen (T-03-105). Die Claim-Reihenfolge ist die Massnahme zu T-03-103.

## User Setup Required

Keine. Die Migration laeuft beim naechsten App-Upgrade mit; die Versionsnummer in `php/appinfo/info.xml` (heute 0.2.0) hebt der Release-Schritt der Phase, nicht dieser Plan.

## Next Phase Readiness

- Die Struktur, an der die Plaene 03-02 bis 03-04 haengen, steht: Job-Art in Spalte, Quellobjekt und Claim, plus der Verzweigungspunkt in `describe`.
- Offen und bewusst so: `QueueController` validiert eingehende Arten noch nicht gegen `KINDS` (Plan 03-07), und der Container liest das Feld `kind` noch nicht (Plan 03-05 und folgende). Eine Zeile mit einer anderen Art als `content` kann daher heute noch nicht entstehen, ausser durch die Aufwertungsregel selbst.
- Die Sichtprobe aus dem Verifikationsblock des Plans gehoert in den Integrationslauf.

## Self-Check

- `php/lib/Migration/Version001000Date20260902000000.php` FOUND
- `php/lib/Listener/FileEventListener.php` FOUND
- `php/lib/Db/QueueMapper.php`, `php/lib/Db/QueueFile.php`, `php/lib/Service/QueueService.php`, `php/lib/Service/StorageService.php`, `php/lib/AppInfo/Application.php` FOUND
- Commits `a10f1dd`, `0f4e4d2`, `9d9d096` FOUND auf `worktree-agent-03-01`
- `php -l` ueber alle 20 PHP-Dateien der App: fehlerfrei

## Self-Check: PASSED

---
*Phase: 03-aktualit-t-und-ocr*
*Completed: 2026-09-01*
