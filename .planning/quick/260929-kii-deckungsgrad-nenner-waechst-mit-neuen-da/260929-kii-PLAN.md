---
phase: quick-260929-kii
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - php/lib/Service/ScanStatsService.php
  - php/lib/BackgroundJobs/StorageCrawlJob.php
  - php/lib/BackgroundJobs/ScanRecountJob.php
  - php/lib/Service/CrawlAdvanceService.php
  - php/lib/Service/SettingsService.php
  - php/lib/Service/PurgeService.php
  - php/lib/Listener/FileEventListener.php
  - php/appinfo/info.xml
  - php/tests/Unit/StorageCrawlJobTest.php
  - php/tests/Unit/ScanRecountJobTest.php
  - php/tests/Unit/CrawlAdvanceServiceTest.php
  - php/tests/Unit/SettingsServiceTest.php
  - php/lib/Service/AdminViewService.php
  - php/tests/Unit/AdminViewServiceTest.php
  - php/templates/admin.php
  - php/js/admin.js
  - php/l10n/de.json
  - php/l10n/de.js
  - php/l10n/de_DE.json
  - php/l10n/de_DE.js
  - php/l10n/fr.json
  - php/l10n/fr.js
  - php/l10n/es.json
  - php/l10n/es.js
  - php/l10n/it.json
  - php/l10n/it.js
  - php/l10n/nl.json
  - php/l10n/nl.js
  - php/l10n/pt_PT.json
  - php/l10n/pt_PT.js
  - php/l10n/pt_BR.json
  - php/l10n/pt_BR.js
  - backend/tests/test_admin_ui_contract.py
  - backend/tests/test_measurement_scripts.py
  - docs/admin-page.md
  - docs/l10n-catalogues.md
  - docs/l10n-french.md
  - docs/l10n-spanish.md
  - docs/l10n-italian.md
  - docs/l10n-dutch.md
  - docs/l10n-portuguese.md
autonomous: true
requirements: [ADM-01]

must_haves:
  truths:
    - "Nach dem Abschluss des Crawls wird der Nenner jedes Mounts periodisch neu gezählt (Nachzählung), sodass neue, gelöschte, verschobene, zu große und ausgeschlossene Dateien im Nenner korrekt stehen"
    - "Die Nachzählung ersetzt die Zähler eines Mounts (Zuweisung, nie Addition) und kann daher nicht doppelt zählen; sie läuft nie gleichzeitig mit einem echten Crawl und überschreibt nie die Zeile eines laufenden Crawls"
    - "Die Nachzählung nutzt dieselbe Abfrage (StorageService::getFilesInMount) und dieselbe Einzelentscheidung (Ausschluss vor Cap) wie der Crawl, es gibt keine zweite Regeldefinition und keine handgeschriebene filecache-Abfrage"
    - "Auf einer ruhigen Instanz kostet die Nachzählung höchstens einen Durchlauf je 24 h; nach Dateiereignissen oder Regeländerungen startet sie beim nächsten Lauf des TimedJobs (Intervall 15 min)"
    - "Ist der Zähler größer als der Nenner (Zeitfenster bis zur nächsten Nachzählung), zeigt die Seite keine Prozentzahl, keinen Bruch 'X von Y' mit X > Y und nicht den Satz 'Backend antwortet nicht', sondern einen eigenen Satz in allen 8 Sprachen"
    - "Auf dem Harness zeigt die Seite nach der Nachzählung einen Nenner >= indexed (oder, im Zeitfenster, den ehrlichen Satz)"
  artifacts:
    - path: "php/lib/BackgroundJobs/ScanRecountJob.php"
      provides: "TimedJob, plant die Nachzählung je Mount, wenn fällig"
      contains: "class ScanRecountJob extends TimedJob"
    - path: "php/lib/BackgroundJobs/StorageCrawlJob.php"
      provides: "Zählmodus 'recount' neben dem Crawl, gemeinsame Einzelentscheidung"
      contains: "recount"
    - path: "php/lib/Service/ScanStatsService.php"
      provides: "replaceStorage(): absolute Zähler eines durchgezählten Mounts"
      contains: "public function replaceStorage("
    - path: "php/lib/Service/AdminViewService.php"
      provides: "coverageShare() liefert null bei counted > indexable, coverage.recounting"
      contains: "'recounting'"
    - path: "php/appinfo/info.xml"
      provides: "Registrierung des TimedJobs"
      contains: "<background-jobs><job>OCA\\Findling\\BackgroundJobs\\ScanRecountJob</job></background-jobs>"
    - path: "php/tests/Unit/ScanRecountJobTest.php"
      provides: "Fälligkeit, Sperre gegen laufende Crawls, ein Kettenstart je Mount"
  key_links:
    - from: "php/lib/BackgroundJobs/ScanRecountJob.php"
      to: "StorageCrawlJob (mode recount)"
      via: "IJobList::add je Mount aus StorageService::getMounts()"
      pattern: "'mode' => 'recount'"
    - from: "php/lib/BackgroundJobs/StorageCrawlJob.php"
      to: "ScanStatsService::replaceStorage"
      via: "Terminierungszweig des Zählmodus"
      pattern: "replaceStorage\\("
    - from: "php/lib/Listener/FileEventListener.php"
      to: "SettingsService::markScanStale"
      via: "Aufruf nach der Mount-Frage in queue() und in den Ordnerzweigen"
      pattern: "markScanStale\\("
    - from: "php/lib/Service/CrawlAdvanceService.php"
      to: "StorageCrawlJob-Argument mode"
      via: "Nachzählkette ist keine Arbeit, auf die der Container wartet"
      pattern: "recount"
    - from: "php/js/admin.js"
      to: "coverage.recounting"
      via: "coverageBlock() und Render-Signatur"
      pattern: "coverage\\.recounting"
---

<objective>
Den Nenner des Deckungsgrads über die Lebenszeit der Instanz korrekt halten und den Fall "Zähler größer Nenner" auf der Seite ehrlich behandeln (Altfehler seit v1.0 ADM-01, Owner-Entscheid 29.09.2026: eigener Fix jetzt, vor dem Push von Phase 27).

Befund: `findling_scan_stats` wird genau einmal je Storage gefüllt (beginStorage bei Cursor 0, finishStorage am Ende, Neustart nur über `occ findling:index --restart`). Dateien, die danach entstehen, indexiert der Listener, der Nenner wächst nie. Harness: "607 von 587 indexierbaren Dateien sind durchsuchbar", 100 Prozent.

## Gewählter Weg und Begründung (Option c: Nachzählung im Zählmodus des Crawls)

Ein TimedJob `ScanRecountJob` (Intervall 15 min) startet, wenn fällig, je Mount eine Kette von `StorageCrawlJob` mit `mode => recount`. Diese Kette läuft dieselbe Abfrage (`StorageService::getFilesInMount`) mit derselben Einzelentscheidung (Ausschluss vor Cap) wie der Crawl, stellt nichts in die Warteschlange, schreibt keine Urteile, trägt ihre sechs Zwischensummen im Jobargument (wie der Crawl seinen Cursor) und ersetzt am Ende die Zeile des Mounts in einer Anweisung (`ScanStatsService::replaceStorage`). Fällig ist die Nachzählung, wenn der Listener oder das Speichern der Regeln die Instanz als geändert markiert hat, und sonst spätestens nach 24 h.

Verworfen, mit Grund:
- (a) Inkrement-Buchhaltung im Listener: jede Ereignisart hat eine eigene Drift-Quelle (Created plus Written für dieselbe neue Datei, Copied bei Ordnern, Umbenennen in oder aus einem Ausschluss, Überschreiben über den Cap oder mit anderem Mimetype, Ordner-Löschen und Wiederherstellen als Teilbaum, `occ files:scan` und externe Änderungen ganz ohne Ereignis). Drift summiert sich für immer und korrigiert sich nie. Dazu ein Schreibvorgang je Nutzerschreiben in der Transaktion des Uploads.
- (b) COUNT über filecache: `StorageService` hält fest, dass es in dieser App keine handgeschriebene filecache-Abfrage gibt (IFileAccess hat keine Zählmethode), und Cap sowie Ausschluss lassen sich nur je Eintrag über `ExclusionService` entscheiden; eine SQL-Nachbildung wäre die zweite Regeldefinition, die `test_exclusion_path_space.py` verbietet.
- (c) hat kein Drift-Risiko (jede Nachzählung ist eine vollständige Messung), keine Mehrfachzählung (Zuweisung statt Addition), keine offenen Transaktionen (nur Lesen plus eine Schlussanweisung), und die Kosten sind ein Metadaten-Durchlauf je Mount, auf ruhigen Instanzen höchstens einmal täglich: bei 1 Mio. Dateien rund 500 Seiten zu je 2000 Einträgen, dieselbe Abfrage, die der nächtliche Reconcile ohnehin blättert, ohne jeden Schreibzugriff je Datei.

Das Zeitfenster zwischen einer Änderung und der nächsten Nachzählung bleibt (höchstens 15 min plus Laufzeit). Darin kann indexed > indexable auftreten; die Seite zeigt dann keine Prozentzahl und keinen unmöglichen Bruch, sondern einen neuen Katalogsatz in allen 16 Dateien.

Bewusst NICHT in diesem Plan: Zeilen von Mounts, die aus der Mount-Liste verschwunden sind (gelöschter Nutzer, abgeschalteter Schalter), werden nicht gelöscht. Der Container behält deren Dokumente nach heutigem Stand (der Reconcile läuft nur über gelistete Mounts), Zähler und Nenner bleiben so zueinander konsistent; ein Löschen hier würde indexed > indexable auf Dauer erzeugen. Das wird in docs/admin-page.md als Grenze benannt.

Output: TimedJob plus Zählmodus plus Schlussanweisung, Stale-Markierung, ehrliche Anzeige, Katalogsatz in 8 Sprachen, Doku, nachgemessene PHP-Baumhash-Pins, Live-Beleg auf dem Harness.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@./CLAUDE.md
@docs/admin-page.md
@php/lib/BackgroundJobs/StorageCrawlJob.php
@php/lib/Service/ScanStatsService.php
@php/lib/Service/StorageService.php
@php/lib/Listener/FileEventListener.php
@php/lib/Service/CrawlAdvanceService.php

Projektregeln, die hier greifen:
- PHP lokal nur `php -l` (im Harness-Container `findling-harp-nextcloud` oder per Wegwerf-Docker `php:8.3-cli`); PHPUnit läuft erst in CI, die Tests werden trotzdem vollständig geschrieben.
- K6: Companion-Änderungen reisen mit Release 1.4.0; KEIN Versionssprung in info.xml in diesem Plan. Bestehende Installationen registrieren den TimedJob beim Update auf 1.4.0 (Nextcloud liest `<background-jobs>` bei Installation und Update).
- Code, Kommentare und Log-Zeilen Englisch im Stil der Dateien (lange erklärende Docblocks, die das Warum sagen); keine Pfade, Dateinamen oder Mimetypes in Log-Zeilen, nur Zahlen und Storage-Id.
- Deutsche Prosa (docs, Katalogwerte) mit echten Umlauten; keine Em- oder En-Dashes in irgendeiner Datei; keine Emojis.
- Python-Gates: ruff (Vollregelsatz) plus ruff format --check, pyright mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, vulture, pytest, alles über `uv run --directory backend`.
- Commits als `git -c user.name=street1983nk -c user.email=k.cherif@outlook.de commit ...`, ohne Claude-Trailer. Nicht pushen.

<interfaces>
Bestehende Verträge (aus dem Baum gelesen, keine Erkundung nötig):

ScanStatsService (php/lib/Service/ScanStatsService.php):
- const TABLE_NAME = 'findling_scan_stats'; COUNTERS = files_seen, bytes_seen, ocr_candidates, pdf_seen, over_cap, excluded (Spalten) plus cursor_file_id, finished_at, updated_at, storage_id
- beginStorage(int $storageId): void, add(int $storageId, int $filesSeen, int $bytesSeen, int $ocrCandidates, int $pdfSeen, int $overCap, int $excluded, int $cursorFileId): void, finishStorage(int $storageId, int $cursorFileId): void, totals(): array{filesSeen..., mountsTotal, mountsFinished}, forStorage(int $storageId): ?array{storageId, filesSeen, bytesSeen, ocrCandidates, pdfSeen, overCap, excluded, cursorFileId, finished:bool}
- Upsert-Muster: update zuerst, bei 0 Zeilen insertIgnoreConflict (nie insert plus catch, PostgreSQL-Transaktionsabbruch), zwei Versuche.

StorageCrawlJob (php/lib/BackgroundJobs/StorageCrawlJob.php), QueuedJob:
- consts BATCH_SIZE = 2000, MAX_SECONDS = 30, INTERVAL = 5, LOCK_NAME = 'findling/crawl-slice', TX_BAND = 250, OCR_CERTAIN_MIMETYPES
- static budgetSeconds(mixed $argument): int
- run($argument): Argument storage_id, root_id, overridden_root, last_file_id (plus optional budget_seconds vom Top-up); Lock-Verlust plant den Nachfolger mit genau diesen vier Schlüsseln (Test testALostLockCrawlsNothingAndReschedulesTheCanonicalArgument)
- crawlSlice(): Cursor 0 -> beginStorage; je Eintrag: Ausschluss (exclusionService->isExcluded(exclusionService->mountRelativePath($entry->getPath(), $mountRoot))) VOR Cap ($size > settingsService->maxFileBytes()); Band-Zähler; seen === 0 -> finishStorage, sonst scheduleAfter Nachfolger

CrawlAdvanceService::advance(): führt die erste StorageCrawlJob-Zeile aus (getJobsIterator(StorageCrawlJob::class, 1, 0)) und meldet pending, solange eine Zeile existiert.

SettingsService: besitzt alle appconfig-Schlüssel (KEY_*-Konstanten), schreibt nur bei geänderten Werten (Muster rememberIndexedCount), save(array $input) speichert Cap, beide Schalter, Ausschlüsse.

FileEventListener::queue(): Fragen 1 Datei, 2 Mimetype (nicht bei Löschung), Mount (isIndexedStorage), 4 Ausschluss, 5 Cap; expandFolder() nach isIndexedStorage; queueRename() Ordnerzweig -> expandMovedFolder() (gleicher Mount -> return).

AdminViewService: overview() rechnet $indexable = filesSeen - overCap - excluded - refusedByType genau einmal; coverage() ruft self::coverageShare() genau zweimal (Gate in test_admin_ui_contract.py: 1 Deklaration, 2 Aufrufe); coverageShare(int $counted, int $indexable, bool $available): ?int liefert heute 100 bei counted > indexable (PHPUnit testAFigureIsNeverNegativeAndNeverAboveAHundred prüft coverageShare(300, 200) === 100).

Template/JS: admin.php Zeilen 231 bis 237 ($hasDenominator, $hasFraction, $hasEmbeddedFraction), Absätze findling-coverage-figure/-bar/-subline/-unknown/-leftout/-provisional, findling-semantic-unknown; admin.js coverageBlock(), semanticBlock(), Render-Signatur (Array mit coverage.*-Werten, join('|')).
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Nachzählung im Zählmodus des Crawls, TimedJob, Stale-Markierung</name>
  <files>php/lib/Service/ScanStatsService.php, php/lib/BackgroundJobs/StorageCrawlJob.php, php/lib/BackgroundJobs/ScanRecountJob.php, php/lib/Service/CrawlAdvanceService.php, php/lib/Service/SettingsService.php, php/lib/Service/PurgeService.php, php/lib/Listener/FileEventListener.php, php/appinfo/info.xml, php/tests/Unit/StorageCrawlJobTest.php, php/tests/Unit/ScanRecountJobTest.php, php/tests/Unit/CrawlAdvanceServiceTest.php, php/tests/Unit/SettingsServiceTest.php</files>
  <behavior>
    - StorageCrawlJob mit mode recount: ruft nie beginStorage, add, finishStorage, enqueue oder record; ruft am Ende (Seite ohne Einträge) genau einmal replaceStorage mit den Summen aller Seiten und dem letzten Cursor; schreibt LAST_JOB_RUN nicht.
    - StorageCrawlJob mit mode recount und einer Zeile finished=false (ein echter Crawl zählt diesen Mount): kein Durchlauf, kein Nachfolger, kein replaceStorage.
    - StorageCrawlJob mit mode recount und Budget-Ende vor dem Ende des Mounts: scheduleAfter mit storage_id, root_id, overridden_root, neuem last_file_id, mode recount und den sechs fortgeschriebenen Summen.
    - Lock-Verlust im Crawl-Modus plant weiterhin exakt die vier kanonischen Schlüssel (bestehender Test bleibt grün); im Zählmodus trägt der Nachfolger zusätzlich mode und die sechs Summen unverändert.
    - Ausgeschlossene Datei zählt excluded (auch über dem Cap), Datei über dem Cap zählt over_cap, sonst indexierbar; files_seen, bytes_seen, ocr_candidates, pdf_seen wie im Crawl: dieselbe private Methode in beiden Modi.
    - ScanRecountJob: tut nichts, solange irgendeine StorageCrawlJob-Zeile existiert; tut nichts, wenn nicht markiert und die letzte Nachzählung jünger als 24 h ist; sonst beginRecount(now) und je Mount aus getMounts() genau ein jobList->add(StorageCrawlJob::class, [storage_id, root_id, overridden_root, last_file_id 0, mode recount, sechs Summen 0]).
    - CrawlAdvanceService: steht an erster Stelle eine Zeile mit mode recount, antwortet es ran=false, pending=false und führt nichts aus.
    - SettingsService: markScanStale() schreibt nur, wenn der Wert noch 0 ist; scanRecountDue(now) ist wahr bei Markierung oder bei 24 h seit der letzten Nachzählung (auch bei nie gelaufener); beginRecount(now) setzt die Markierung auf 0 und die Zeit auf now; save() markiert.
  </behavior>
  <action>
Tests zuerst (RED in CI; lokal nur Syntax): Fälle aus behavior in StorageCrawlJobTest (neue Methoden neben den beiden bestehenden, gleiche runJob-Hilfe und Konstruktor-Doubles), neuer ScanRecountJobTest (Muster von StorageCrawlJobTest: ITimeFactory-, IJobList-, StorageService-, SettingsService-, LoggerInterface-Doubles; run über eine Hilfsmethode wie runJob), CrawlAdvanceServiceTest und SettingsServiceTest erweitern.

ScanStatsService: neue Methode replaceStorage(int $storageId, array $counters, int $cursorFileId): void, $counters mit den sechs Spaltennamen als Schlüssel (fehlend = 0, negativ auf 0 geklemmt), Zurückweisung bei storageId <= 0 über reject(). Eine UPDATE-Anweisung setzt alle sechs Zähler ABSOLUT (Zuweisung, keine func()->add), cursor_file_id, finished_at = now, updated_at = now, WHERE storage_id = ? AND finished_at IS NOT NULL. Bei 0 Zeilen: forStorage() fragen; existiert eine Zeile, nichts tun (entweder zählt ein echter Crawl diesen Mount, dessen Zeile nicht überschrieben werden darf, oder die Werte waren in derselben Sekunde schon identisch); existiert keine (neuer Mount, etwa ein neuer Nutzer, den der einmalige SchedulerJob nie gesehen hat), insertIgnoreConflict mit den Werten und finished_at. Den Klassen-Docblock ehrlich nachziehen: die Tabelle schreibt der Crawl und sein Zählmodus, und der Zählmodus ist KEIN zweiter Durchlauf mit eigenen Regeln, sondern derselbe Job mit derselben Abfrage und derselben Einzelentscheidung, der ersetzt statt addiert; der Absatz "why it is a reset rather than a cursor comparison" bleibt, ergänzt um die Zuweisung.

StorageCrawlJob: Konstante MODE_RECOUNT = 'recount' und ein Argument-Schlüssel 'mode'. run() liest mode; ungültige Werte zählen als Crawl. Die Lock-Verlust-Neuplanung bildet ihr Argument über eine private Hilfe, die im Crawl-Modus exakt die vier Schlüssel liefert und im Zählmodus zusätzlich mode und die sechs Summen (jeder Wert per (int) und max(0) aus dem Argument). Die Einzelentscheidung (Ausschluss vor Cap, mit dem einen isExcluded/mountRelativePath-Aufruf dieser Datei) und das Zählen der Sichtung (files_seen, bytes_seen, ocr_candidates über OCR_CERTAIN_MIMETYPES, pdf_seen, over_cap, excluded) in private Methoden ziehen, die crawlSlice und die neue recountSlice beide nutzen; crawlSlice verhält sich danach byte-gleich wie heute (Band, Transaktionen, record too_large, enqueue, add je Band, finishStorage bei seen === 0). recountSlice(budget, storageId, rootId, overriddenRoot, lastFileId, summen): (1) forStorage(); Zeile vorhanden und finished false -> debug-Log mit storage_id, return ohne Nachfolger. (2) cap und mountRoot einmal lesen wie im Crawl. (3) Seiten zu BATCH_SIZE blättern, je Eintrag Cursor vorrücken und zählen, Deadline nur ZWISCHEN den Seiten prüfen (keine Schreibzugriffe, eine Seite ist schnell, Cursor bleibt seitenrein). (4) Liefert eine Seite 0 Einträge: replaceStorage und info-Log 'Findling: recounted a mount' mit storage_id und files_seen, kein Nachfolger. (5) Sonst scheduleAfter(INTERVAL) mit Nachfolger-Argument. Keine Transaktion, kein beginStorage, kein LAST_JOB_RUN (der Wert ist der Bewegungsmesser der Indexierung für stalledFor, eine Zählung ist keine Indexbewegung; im Kommentar so begründen). Den Klassen-Docblock ("the only one there will ever be") ehrlich ergänzen: der Zählmodus ist dieselbe Arbeit ohne Warteschlange, damit bleibt es eine Abfrage und eine Regel.

ScanRecountJob (neu, php/lib/BackgroundJobs/ScanRecountJob.php): extends OCP\BackgroundJob\TimedJob, Konstruktor ITimeFactory, IJobList, StorageService, SettingsService, LoggerInterface; setInterval(15 * 60). run(): (1) läuft irgendeine StorageCrawlJob-Zeile (getJobsIterator(StorageCrawlJob::class, 1, 0) nicht leer: ein Crawl oder eine Nachzählung ist unterwegs) -> return. (2) !settingsService->scanRecountDue(now) -> return. (3) settingsService->beginRecount(now) VOR dem Planen (Ereignisse während des Durchlaufs markieren erneut und lösen die nächste Runde aus). (4) je Mount aus storageService->getMounts() jobList->add(StorageCrawlJob::class, Argument wie oben). (5) info-Log mit der Zahl der Mounts. Docblock: warum TimedJob, warum 15 min und 24 h (Kosten auf großen Instanzen gegen Zeitfenster), warum keine Zeilen verschwundener Mounts gelöscht werden (siehe objective). In info.xml genau eine Zeile `<background-jobs><job>OCA\Findling\BackgroundJobs\ScanRecountJob</job></background-jobs>` zwischen `</dependencies>` und dem Kommentar vor `<repair-steps>` (Schema-Reihenfolge laut dem Kommentar in Zeile 243 bis 247; der Kommentar spricht von "The two blocks below", auf drei Blöcke ziehen und den neuen Block in einem Absatz begründen). Keine Versionsänderung. PurgeService::JOBS um ScanRecountJob::class ergänzen und die Zahl im Docblock ("The three background jobs") nachziehen.

CrawlAdvanceService::advance(): vor dem Ausführen das Argument der ersten Zeile prüfen; mode === StorageCrawlJob::MODE_RECOUNT -> ['ran' => false, 'pending' => false] ohne remove und ohne start. Begründung im Kommentar: eine Nachzählung stellt nichts in die Warteschlange, der hungrige Container hat darauf nicht zu warten, und Crawl- und Nachzählzeilen bestehen nie nebeneinander (ScanRecountJob plant nur ohne Crawlzeilen, occ findling:index --restart entfernt alle StorageCrawlJob-Zeilen).

SettingsService: zwei Schlüssel KEY_SCAN_STALE_SINCE = 'scan_stale_since' (int, 0 = nicht markiert) und KEY_SCAN_RECOUNTED_AT = 'scan_recounted_at' (int), Konstante RECOUNT_FLOOR_SECONDS = 86400; Methoden markScanStale(): void (liest getValueInt, schreibt setValueInt(time) nur bei 0, damit ein Schreiben je Ereignis ein gecachter Lesezugriff bleibt; Zeitquelle ITimeFactory, falls schon injiziert, sonst time() nicht verwenden, sondern ITimeFactory in den Konstruktor aufnehmen und DI prüfen), scanRecountDue(int $now): bool, beginRecount(int $now): void. save() ruft markScanStale() nach dem Speichern auf (Cap, Schalter und Ausschlüsse ändern den Nenner).

FileEventListener: settingsService->markScanStale() an genau drei Stellen: in queue() direkt nach der Mount-Frage 3 (deckt Anlegen, Schreiben, Kopieren, Umbenennen von Dateien, Löschen, Wiederherstellen, Ausschluss und Cap ab), in expandFolder() nach isIndexedStorage (Ordner löschen, wiederherstellen, über Mountgrenzen verschieben), und in expandMovedFolder() VOR der Rückkehr bei gleichem Mount, aber nur wenn storageService->isIndexedStorage(storageId) wahr ist (ein Ordner, der innerhalb des Mounts in oder aus einem Ausschluss wandert, ändert excluded). Alles bleibt im bestehenden try-Block von handle(); Kommentar: warum hier markiert und nicht gezählt (Verweis auf die Drift-Begründung im Docblock von ScanRecountJob).

Die bestehende Regel bleibt: Neustart über occ findling:index --restart entfernt StorageCrawlJob-Zeilen und damit auch laufende Nachzählketten, IndexCommand braucht keine Änderung.
  </action>
  <verify>
    <automated>for f in lib/Service/ScanStatsService.php lib/BackgroundJobs/StorageCrawlJob.php lib/BackgroundJobs/ScanRecountJob.php lib/Service/CrawlAdvanceService.php lib/Service/SettingsService.php lib/Service/PurgeService.php lib/Listener/FileEventListener.php tests/Unit/StorageCrawlJobTest.php tests/Unit/ScanRecountJobTest.php tests/Unit/CrawlAdvanceServiceTest.php tests/Unit/SettingsServiceTest.php; do docker exec findling-harp-nextcloud php -l /var/www/html/custom_apps/findling/$f || exit 1; done && uv run --directory backend pytest tests/test_exclusion_path_space.py tests/test_store_metadata.py tests/test_php_trust_boundary.py -q</automated>
  </verify>
  <done>Alle PHP-Dateien syntaktisch sauber (php -l; den Mount-Pfad der App im Container vorher mit `docker exec findling-harp-nextcloud ls /var/www/html/custom_apps /var/www/html/apps` bestätigen und die Schleife anpassen), die Gates zu Ausschluss-Pfadraum, Store-Metadaten und Vertrauensgrenze grün, PHPUnit-Fälle aus behavior geschrieben. Commit `fix(quick-260929-kii): recount the coverage denominator after the crawl`.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Ehrliche Anzeige bei Zähler größer Nenner, Katalogsatz in 16 Dateien</name>
  <files>php/lib/Service/AdminViewService.php, php/tests/Unit/AdminViewServiceTest.php, php/templates/admin.php, php/js/admin.js, php/l10n/*.json, php/l10n/*.js (alle 16), backend/tests/test_admin_ui_contract.py, docs/l10n-catalogues.md, docs/l10n-french.md, docs/l10n-spanish.md, docs/l10n-italian.md, docs/l10n-dutch.md, docs/l10n-portuguese.md</files>
  <behavior>
    - coverageShare(300, 200, true) ist null (vorher 100); coverageShare(200, 200, true) bleibt 100, (199, 200) bleibt 99, (-5, 200) bleibt 0.
    - coverage() liefert 'recounting' => true genau dann, wenn Backend erreichbar, indexable > 0 und indexed > indexable; dann percent null und embeddedPercent null.
    - Seite bei recounting: kein Prozentwert, kein Balken, keine Zeile "X von Y", nicht der Satz "backend does not answer", im semantischen Block nicht der Satz "semantic share cannot be worked out"; stattdessen Absatz findling-coverage-recounting mit dem neuen Satz; "Deliberately left out" und "Provisional" unverändert.
  </behavior>
  <action>
AdminViewService: coverageShare() bekommt eine dritte Null-Bedingung `$counted > $indexable` (Docblock: kein ehrlicher Anteil, wenn mehr gezählt als als indexierbar gemessen wurde; das ist das Zeitfenster bis zur nächsten Nachzählung von ScanRecountJob und nie 100 Prozent). Die Zahl der Aufrufe bleibt zwei (Gate). coverage() berechnet `$recounting` einmal wie in behavior und gibt es als Schlüssel 'recounting' zurück; Rückgabe-Typannotation und Docblock nachziehen. PHPUnit: den Fall 300/200 aus testAFigureIsNeverNegativeAndNeverAboveAHundred in den Null-Datenlieferanten von testWithoutAnHonestFigureTheAnswerIsNullAndNotNought verschieben (Testname bleibt sinnvoll: "never above a hundred" gilt weiter), dazu ein Test auf coverage.recounting über overview(), falls die bestehenden overview-Tests ein Muster dafür haben, sonst über coverageShare allein.

Neuer Katalogsatz (Schlüssel englisch, ein Platzhalter %s = Zahl der durchsuchbaren Dateien), exakt so in alle 16 Dateien, .json und .js je Sprache wertgleich:
- Schlüssel: `%s files are searchable. Files were added since the last count, so the share is shown again once they have been counted.`
- de und de_DE: `%s Dateien sind durchsuchbar. Seit der letzten Zählung sind Dateien dazugekommen, der Anteil erscheint wieder, sobald sie mitgezählt sind.`
- fr: `%s fichiers peuvent être trouvés par la recherche. Des fichiers ont été ajoutés depuis le dernier comptage, la part s'affichera de nouveau dès qu'ils auront été comptés.`
- es: `%s archivos se pueden encontrar con la búsqueda. Desde el último recuento se han añadido archivos; la proporción volverá a mostrarse en cuanto se hayan contado.`
- it: `%s file si possono trovare con la ricerca. Dall'ultimo conteggio sono stati aggiunti dei file, la quota verrà mostrata di nuovo appena saranno stati contati.`
- nl: `%s bestanden zijn doorzoekbaar. Sinds de laatste telling zijn er bestanden bijgekomen; het aandeel verschijnt weer zodra ze zijn meegeteld.`
- pt_PT: `%s ficheiros podem ser encontrados pela pesquisa. Foram adicionados ficheiros desde a última contagem; a percentagem volta a ser mostrada assim que forem contados.`
- pt_BR: `%s arquivos podem ser encontrados pela pesquisa. Arquivos foram adicionados desde a última contagem; a porcentagem volta a aparecer assim que forem contados.`
Einfügen an der Stelle neben "%1$s of %2$s indexable files are searchable" in jeder Datei, Formatierung der Nachbarzeilen übernehmen. In test_admin_ui_contract.py die harte Zahl in Zeile 3090 von 287 auf 288 heben und den Kommentar darüber um "one of quick task 260929-kii (the recount sentence)" ergänzen. docs/l10n-catalogues.md: datierte Notiz "Nachgezählt am 29.09.2026, Quick-Task 260929-kii" im Stil der vorhandenen mit 288 Schlüsseln (Pluralzahl aus de.json zählen, nicht abschreiben) und dem Satz, wofür der neue Schlüssel steht. Die fünf Sprachdokumente bekommen je eine Tabellenzeile im Format ihrer Zeile für "Provisional figure, ..." (pt-Dokument mit vier Spalten).

Template admin.php: `$recounting = ($coverage['recounting'] ?? false) === true;` neben $provisional; neuer Absatz `<p class="settings-hint" id="findling-coverage-recounting">` direkt nach findling-coverage-subline, hidden außer bei $hasDenominator && $recounting, Text über p($l->t(neuer Schlüssel, [$count($searchable)])); findling-coverage-unknown zusätzlich hidden bei $recounting; findling-semantic-unknown zusätzlich hidden bei $recounting. admin.js: coverage.recounting in die Render-Signatur (neben coverage.percent), in coverageBlock() den Text für findling-coverage-recounting mit numbers.format(searchable) setzen und `shown('findling-coverage-recounting', hasDenominator && coverage.recounting === true)`, findling-coverage-unknown nur bei hasDenominator && !hasFraction && coverage.recounting !== true; semanticBlock() bekommt die Information (drittes Argument erweitern oder coverage.recounting direkt lesen) und blendet findling-semantic-unknown bei recounting aus. Text vor Sichtbarkeit setzen, wie die Datei es vorschreibt. Keine neue Markup-Erzeugung im Script.
  </action>
  <verify>
    <automated>docker exec findling-harp-nextcloud sh -c 'cd /var/www/html/custom_apps/findling && php -l lib/Service/AdminViewService.php && php -l templates/admin.php && php -l tests/Unit/AdminViewServiceTest.php' && uv run --directory backend pytest tests/test_admin_ui_contract.py tests/test_public_artifacts.py -q</automated>
  </verify>
  <done>Kontrakt- und Artefakt-Gates grün (inklusive Schlüsselgleichstand über 16 Dateien, Platzhalter, keine Dashes, Wertgleichheit .json/.js, Zahl 288), php -l sauber, PHPUnit-Fall 300/200 als null geschrieben. Commit `fix(quick-260929-kii): no share and no impossible fraction while the count is behind`.</done>
</task>

<task type="auto">
  <name>Task 3: Doku, Baumhash-Pins, volle Gates, Live-Beleg auf dem Harness</name>
  <files>docs/admin-page.md, backend/tests/test_measurement_scripts.py</files>
  <action>
docs/admin-page.md, Abschnitt "Der Deckungsgrad und sein Nenner": den Satz "Alle drei Zahlen kommen also aus derselben Arbeit wie der Zähler und nie aus einer zweiten Abfrage" behalten und präzisieren (die Nachzählung ist dieselbe Abfrage und dieselbe Regel). Neuer Unterabschnitt "Wie der Nenner aktuell bleibt": der Crawl zählt einmal; danach zählt ScanRecountJob je Mount neu (alle 15 min geprüft, fällig nach Dateiereignissen oder gespeicherten Regeln, sonst täglich), die Nachzählung ersetzt die Zahlen statt sie zu addieren, sie läuft nie neben einem Crawl; gelöschte, verschobene, zu große und ausgeschlossene Dateien fallen dadurch richtig heraus, neue kommen hinzu, neue Mounts (neue Nutzer) bekommen ihre Zeile. Grenze: Zeilen verschwundener Mounts bleiben stehen, mit Begründung aus dem objective. Neuer Absatz für den Fall Zähler größer Nenner mit dem deutschen Wortlaut des neuen Satzes und der Begründung "eine Zahl über 100 Prozent oder ein Bruch 607 von 587 sieht wie ein Defekt aus"; die Regel "bei 99 stehen, solange eine Datei fehlt" bleibt und gilt jetzt auch umgekehrt: nie 100, solange mehr gezählt als gemessen ist. Hinweis, dass bestehende Installationen den TimedJob mit dem Update auf 1.4.0 registrieren. Echte Umlaute, keine Dashes.

Baumhash-Pins: das Rezept `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/40b-baumhash.py` über `php` mit Muster `**/*.php` laufen lassen (Aufruf wie run_the_recipe in test_measurement_scripts.py: `uv run --directory backend python ../docs/measurements/2026-09-vergleichsmessung-m7g/skripte/40b-baumhash.py ../php "**/*.php"`), PHP_FILES_TODAY (erwartet 82: ScanRecountJob.php und ScanRecountJobTest.php kamen, keine ging) und PHP_TREE_HASH_TODAY auf die gemessenen Werte setzen, mit einem Absatz im Stil der Datei direkt über den Konstanten ("Measured again on 2026-09-29 by quick task 260929-kii: two files came, ..., the bytes of ... changed; no file went, so PHP_FILES_TODAY moves to 82."). Die Python-Hälfte (PACKAGE_*) nur anfassen, wenn unter backend/src/findling etwas geändert wurde (in diesem Plan nicht vorgesehen; nachmessen und bestätigen, dass der Wert unverändert ist).

Volle Gates: `uv run --directory backend ruff check .`, `uv run --directory backend ruff format --check .`, `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run --directory backend pyright`, `uv run --directory backend vulture` (mit der im Repo konfigurierten Aufrufform, siehe CI-Workflow unter .github/workflows), `uv run --directory backend pytest -q`. Alles grün vor dem Commit; ein Befund wird gefixt, nicht weggeschaltet.

Live-Beleg auf dem Harness (http://localhost:8096, Container findling-harp-nextcloud, App per Bind-Mount aus php/, SQLite, opcache revalidiert nach 60 s; nach den Dateiänderungen 60 s warten): (1) Vorher-Zahlen festhalten: Zeilen von oc_findling_scan_stats per `docker exec -u www-data findling-harp-nextcloud php -r` mit PDO auf die SQLite-Datei aus config.php (nur SELECT), dazu indexed/docs des Containers wie im Befund. (2) Den TimedJob einmalig registrieren, da die installierte Version 1.3.0 ist und info.xml erst beim Update gelesen wird: `docker exec -u www-data -w /var/www/html findling-harp-nextcloud php -r 'require "lib/base.php"; \OCP\Server::get(\OCP\BackgroundJob\IJobList::class)->add(\OCA\Findling\BackgroundJobs\ScanRecountJob::class);'`. (3) `php occ background-job:list --class='OCA\Findling\BackgroundJobs\ScanRecountJob'` für die Id, dann `php occ background-job:execute <id> --force-execute`; danach die entstandenen StorageCrawlJob-Zeilen (mode recount) mit `background-job:list --class='OCA\Findling\BackgroundJobs\StorageCrawlJob'` und `background-job:execute <id> --force-execute` abarbeiten, bis keine mehr da ist. (4) Nachher-Zeilen von oc_findling_scan_stats: files_seen deutlich über 588 und plausibel zur Zahl der zugelassenen Dateien, finished_at gesetzt. (5) Admin-Seite http://localhost:8096/settings/admin/findling per Playwright wie im Live-Lauf von 27-15 öffnen: Nenner >= indexed und Prozent plausibel; ist in der Zwischenzeit indexed größer (Uploads laufen), muss der neue Satz statt Prozentwert und Bruch stehen. (6) Gegenprobe des ehrlichen Pfads: eine neue zugelassene Datei hochladen (WebDAV per curl mit den Harness-Zugangsdaten), warten bis indexed steigt, Seite zeigt dann entweder den korrekten Bruch oder den neuen Satz, nie "X von Y" mit X > Y. Die Zahlen vor und nach mit Uhrzeit ins SUMMARY. Den registrierten Job auf dem Harness stehen lassen (er ist ab 1.4.0 ohnehin registriert).
  </action>
  <verify>
    <automated>uv run --directory backend ruff check . && uv run --directory backend ruff format --check . && uv run --directory backend pytest -q && uv run --directory backend pytest tests/test_measurement_scripts.py -q -k "php_half"</automated>
  </verify>
  <done>Volle Python-Suite und alle Gates (ruff, format, pyright latest, vulture) grün; PHP_FILES_TODAY und PHP_TREE_HASH_TODAY nachgemessen mit Begründungskommentar; admin-page.md beschreibt Nachzählung, Zeitfenster und Grenze; Live-Beleg mit Vorher/Nachher-Zahlen von scan_stats und Seitenzustand im SUMMARY. Commit `docs(quick-260929-kii): recount of the denominator, tree hash measured again`. Kein Push.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Cron/Top-up -> StorageCrawlJob | Jobargumente aus oc_jobs steuern Cursor und Zwischensummen |
| Nutzerschreiben -> FileEventListener | jede Dateioperation der Instanz läuft durch handle() |
| Admin-Seite -> Browser | Zahlen und Sätze aus dem Server im DOM |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-kii-01 | Denial of Service | ScanRecountJob / Zählmodus auf großen Instanzen | mitigate | Nachzählung nur ohne laufenden Crawl, nur bei Markierung oder nach 24 h, Wall-Clock-Budget je Scheibe (budgetSeconds, höchstens 30 s), gemeinsamer LOCK_NAME, keine Schreibzugriffe je Datei |
| T-kii-02 | Denial of Service | FileEventListener::markScanStale im Upload-Pfad | mitigate | gecachter getValueInt, Schreiben nur beim Übergang 0 -> Zeit, alles im bestehenden try-Block, eine Ausnahme bricht nie den Upload |
| T-kii-03 | Tampering | Zwischensummen im Jobargument | accept | oc_jobs ist nur für DB-Admins schreibbar; Werte werden per (int) und max(0) geklemmt; die nächste Nachzählung ersetzt jede verfälschte Zahl |
| T-kii-04 | Tampering (Integrität der Zahl) | replaceStorage gegen laufenden Crawl | mitigate | WHERE finished_at IS NOT NULL plus Abbruch der Kette bei finished=false, sodass eine Nachzählung nie die Zeile eines laufenden Crawls überschreibt |
| T-kii-05 | Information Disclosure | Log-Zeilen des Zählmodus und des TimedJobs | mitigate | nur storage_id, Zahlen und Anzahl Mounts, keine Pfade, Namen oder Mimetypes (Regel T-04-19) |
| T-kii-06 | Information Disclosure / Spoofing | neuer Satz im DOM | mitigate | Ausgabe über p() und t() mit escapter Zahl; JS setzt nur Text, kein Markup; Gate test_no_catalogue_value_can_break_the_page |
</threat_model>

<verification>
- php -l aller geänderten und neuen PHP-Dateien sauber.
- `uv run --directory backend pytest -q` vollständig grün, dazu ruff, ruff format --check, pyright (latest), vulture.
- grep-Gates: `grep -c "self::coverageShare(" php/lib/Service/AdminViewService.php` = 2; `grep -v '^\s*\*' php/lib/BackgroundJobs/StorageCrawlJob.php | grep -c "isExcluded("` = 1; `grep -c "ScanRecountJob" php/appinfo/info.xml` >= 1.
- Live: scan_stats nach der Nachzählung mit files_seen passend zum Bestand; Seite zeigt nie X > Y.
</verification>

<success_criteria>
- Der Nenner folgt dem Bestand: nach der Nachzählung entspricht indexierbar auf dem Harness dem gezählten zugelassenen Bestand (>= indexed), statt bei 587 stehen zu bleiben.
- Kein Pfad der Seite zeigt mehr 100 Prozent oder einen Bruch mit Zähler größer Nenner; im Zeitfenster steht der neue Satz in der Sprache des Admins.
- Keine zweite Regeldefinition, keine handgeschriebene filecache-Abfrage, keine Inkrement-Buchhaltung.
- PHP-Baumhash-Pins nachgemessen, alle Gates grün, drei Commits als street1983nk, nichts gepusht.
</success_criteria>

<output>
Create `.planning/quick/260929-kii-deckungsgrad-nenner-waechst-mit-neuen-da/260929-kii-SUMMARY.md` when done (mit Vorher/Nachher-Zahlen des Live-Belegs).
</output>
