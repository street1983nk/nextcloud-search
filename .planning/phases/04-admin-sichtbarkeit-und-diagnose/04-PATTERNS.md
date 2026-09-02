# Phase 4: Admin-Sichtbarkeit und Diagnose - Pattern Map

**Mapped:** 2026-09-02
**Files analyzed:** 34 (21 PHP, 8 Python, 4 Test, 1 CI)
**Analogs found:** 27 / 34

Alle Zeilennummern sind am 02.09.2026 gegen den Arbeitsbaum geprüft. Wo eine Datei geändert wird, ist der Analog die Datei selbst (Selbst-Analog): das Muster steht schon darin und muss verlängert, nicht erfunden werden.

---

## File Classification

### PHP Companion (`php/`)

| Neue/geänderte Datei | Rolle | Datenfluss | Nächster Analog | Güte |
|---|---|---|---|---|
| `php/lib/Settings/Section.php` (neu) | provider (OCP-Interface) | request-response | `php/lib/Search/Provider.php` | partial (nur Interface-Form) |
| `php/lib/Settings/Admin.php` (neu) | provider (OCP-Interface) | request-response | `php/lib/Search/Provider.php` + RESEARCH Beispiel 1 | partial |
| `php/templates/admin.php` (neu) | view/template | request-response | **kein Analog** (Verzeichnis existiert nicht) | none |
| `php/js/admin.js` (neu) | client script | request-response (Polling) | **kein Analog** | none |
| `php/css/admin.css` (neu) | style | -- | **kein Analog** | none |
| `php/img/app-dark.svg` (neu) | asset | -- | **kein Analog** | none |
| `php/l10n/de.json` + `de.js` (neu) | i18n data | -- | **kein Analog** | none |
| `php/lib/Controller/SettingsController.php` (neu) | controller | request-response | `php/lib/Controller/ReconcileController.php` | role-match, Guard **invertiert** |
| `php/lib/Service/AdminViewService.php` (neu) | service (Aggregation) | request-response | `php/lib/Command/IndexCommand.php::status()` + `QueueService::stats()` | role-match |
| `php/lib/Service/PathResolverService.php` (neu) | service (Lookup) | transform | `php/lib/Search/Provider.php` (mountCache/getUserFolder) + `GatewayController::getFileContents` | exact (Flow), role-match |
| `php/lib/Service/ExclusionService.php` (neu) | service (Regel + Räumung) | CRUD + batch-enqueue | `php/lib/Service/StorageService.php` (`isIndexedStorage`-Cache) + `SubtreeExpandJob` | role-match |
| `php/lib/Service/ScanStatsService.php` (neu) | service/repository | CRUD | `php/lib/Service/FileStateService.php` | exact |
| `php/lib/Service/SettingsService.php` (neu) | service (config) | CRUD | `StorageCrawlJob.php:151` + `IndexCommand.php:92-98,115` (IAppConfig-Nutzung) | partial |
| `php/lib/Service/FileStateService.php` (geändert) | service/repository | CRUD | Selbst-Analog: `counts()` (Z. 161-180) | exact |
| `php/lib/Service/StorageService.php` (geändert) | service | batch | Selbst-Analog: `MOUNT_PROVIDERS` (Z. 46-51), `getFilesInMount` (Z. 195-205) | exact |
| `php/lib/BackgroundJobs/StorageCrawlJob.php` (geändert) | job | batch | Selbst-Analog + `SubtreeExpandJob.php` | exact |
| `php/lib/Listener/FileEventListener.php` (geändert) | listener | event-driven | Selbst-Analog: Z. 347-374 | exact |
| `php/lib/Migration/Version001000Date2026...php` (neu) | migration | schema | `Version001000Date20260816000000.php` (createTable) + `Version001000Date20260902000000.php` (addIndex + postSchemaChange) | exact |
| `php/appinfo/info.xml` (geändert) | config | -- | Selbst-Analog: Z. 44-57 (`repair-steps`/`commands`) | exact |
| `php/lib/Command/DiagnoseCommand.php` (optional) | command | request-response | `php/lib/Command/IndexCommand.php` | exact |
| Räumung nach neuem Ausschluss | -- | batch | `SubtreeExpandJob` mit `kind=KIND_DELETE` (**keine neue Datei**) | exact |

### Backend Container (`backend/`)

| Neue/geänderte Datei | Rolle | Datenfluss | Nächster Analog | Güte |
|---|---|---|---|---|
| `backend/src/findling/api/diagnose.py` (neu) | controller/route | request-response | `backend/src/findling/api/status.py` | exact |
| `backend/src/findling/api/rates.py` (neu) | controller/route | request-response | `backend/src/findling/api/status.py` | exact |
| `backend/src/findling/api/status.py` (geändert) | controller/route | request-response | Selbst-Analog | exact |
| `backend/src/findling/store/repo.py` (geändert) | repository | CRUD | Selbst-Analog: `counts()`/`reasons_by_state()`/`file_row()` (Z. 523-554) | exact |
| `backend/src/findling/store/schema.sql` (geändert, Index auf `indexed_at`) | schema | -- | Selbst-Analog | exact |
| `backend/src/findling/extract/errors.py` (geändert) | model (Enum) | -- | Selbst-Analog: `Reason` + `STATE_REASONS` (Z. 46-110) | exact |
| `backend/src/findling/main.py` (geändert) | wiring | -- | Selbst-Analog: Z. 30-32, 242-244 | exact |
| `backend/appinfo/info.xml` (geändert) | config | -- | Selbst-Analog: `<route>status` (Z. 107-112) | exact |

### Tests und CI

| Neue/geänderte Datei | Rolle | Datenfluss | Nächster Analog | Güte |
|---|---|---|---|---|
| `backend/tests/test_php_trust_boundary.py` (geändert) | test (statische Quellanalyse) | -- | Selbst-Analog + `test_readonly_gate.py` | exact |
| `backend/tests/test_diagnose_endpoint.py` (neu) | test (HTTP) | request-response | `backend/tests/test_status_endpoint.py` | exact |
| `backend/tests/test_rates_endpoint.py` (neu) | test (HTTP) | request-response | `backend/tests/test_status_endpoint.py` | exact |
| `backend/tests/test_store_repo.py` (geändert) | test | -- | Selbst-Analog | exact |
| `backend/tests/test_extract_errors.py` | test (Paritäts-Gate) | -- | unverändert, muss grün bleiben (Z. 134-158) | -- |
| `.github/workflows/php.yml` (geändert) | CI config | -- | Selbst-Analog: Z. 63-64 (`php -l`), Z. 110-118 (Routen-Assertion als Vorbild für `<settings>`) | exact |

---

## Pattern Assignments

### `php/lib/Controller/SettingsController.php` (controller, request-response)

**Analog:** `php/lib/Controller/ReconcileController.php`

Der Analog ist rollengleich (nur lesende Routen, DataResponse, Fehlerbehandlung), aber der Guard ist **umzudrehen**. Das ist die einzige Stelle der Phase, an der ein Muster bewusst nicht kopiert wird, und Gate B muss das mitlernen (siehe Shared Patterns / Gate B).

**Imports-Muster** (`ReconcileController.php:1-13`):
```php
<?php

declare(strict_types=1);

namespace OCA\Findling\Controller;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\StorageService;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\OCSController;
use OCP\IRequest;
use Psr\Log\LoggerInterface;
```

**Konstruktor-Muster** (`ReconcileController.php:66-72`):
```php
	public function __construct(
		IRequest $request,
		private StorageService $storageService,
		private LoggerInterface $logger,
	) {
		parent::__construct(Application::APP_ID, $request);
	}
```

**Attribut-Muster der Route** (`ReconcileController.php:84-91`) -- das ist die Form, die Gate B textuell zählt, immer vollqualifiziert und ohne `use`-Zeile:
```php
	#[\OCP\AppFramework\Http\Attribute\ExAppRequired]
	#[\OCP\AppFramework\Http\Attribute\NoCSRFRequired]
	#[\OCP\AppFramework\Http\Attribute\ApiRoute(verb: 'GET', url: '/mounts')]
	public function mounts(): DataResponse {
		$foreign = $this->rejectForeignCaller();
		if ($foreign !== null) {
			return $foreign;
		}
```

**Was für die Admin-Routen ANDERS ist (RESEARCH Pitfall 7 und 10, Security-Tabelle):**
- **kein** `ExAppRequired` (sonst kommt der Browser des Admins nicht hin und jeder Fremd-Container schon)
- **kein** `NoCSRFRequired`, **kein** `NoAdminRequired`, **kein** `PublicPage`
- **kein** `rejectForeignCaller()` als erste Anweisung (es gibt keinen ExApp-Aufrufer)
- Die Schutzwirkung ist der Default von `SecurityMiddleware`: angemeldet + `isAdminUser()` + CSRF. Weniger Code ist hier die strengere Variante.
- Vollqualifizierte Attributschreibweise **beibehalten**, weil `test_the_gate_sees_every_route_the_sources_declare` Attributzeilen zählt und eine `use`-Zeile das Gate bricht.

**Eingabe-Klemmung statt Ablehnung** (`ReconcileController.php:155`), für Pagination der Fehlerliste:
```php
		$size = max(1, min(self::MAX_SLICE, $limit));
		$cursor = max(0, $after);
```

**Eingabe-Ablehnung, wenn der Wert nichts benennt** (`ReconcileController.php:151-153`):
```php
		if ($storage <= 0 || $root <= 0) {
			return $this->badMount();
		}
```

**Error-Handling-Muster** (`ReconcileController.php:102-111`) -- statischer Satz nach außen, Exception nur im `exception`-Feld, nie eine Bibliotheksmeldung im Log:
```php
		} catch (\Throwable $e) {
			$this->logger->error('Findling: could not list the mounts', ['exception' => $e]);
			return new DataResponse(['error' => 'Mount list is not available.'], Http::STATUS_INTERNAL_SERVER_ERROR);
		}
```

**Nicht loggen, was der Aufrufer geschrieben hat** (`ReconcileController.php:214-221`) -- gilt wörtlich für die Diagnose-Eingabe (Pfad!):
```php
	private function badMount(): DataResponse {
		$this->logger->warning('Findling: rejected a slice request without a usable mount');

		return new DataResponse(
			['error' => 'Malformed mount reference.'],
			Http::STATUS_BAD_REQUEST,
		);
	}
```

---

### `php/lib/Service/PathResolverService.php` (service, transform)

**Analoge:** `php/lib/Search/Provider.php` (Mount-Cache und Nutzerordner in einer Klasse, mit Kostendisziplin), `php/lib/Controller/GatewayController.php:61-108` (der `NoUserException`-Zweig)

**Dependency-Muster** (`Provider.php:86-95`) -- genau die drei Dienste, die die Diagnose braucht, sind hier schon injiziert:
```php
	public function __construct(
		private IL10N $l10n,
		private IURLGenerator $urlGenerator,
		private ExAppService $exApp,
		private IRootFolder $rootFolder,
		private IUserMountCache $mountCache,
		private IFileAccess $fileAccess,
		private LoggerInterface $logger,
	) {
	}
```

**Mount-Cache-Muster mit Ausfalltoleranz** (`Provider.php:426-432`):
```php
	private function storageIdsOfUser(IUser $user): array {
		try {
			$mounts = $this->mountCache->getMountsForUser($user);
		} catch (\Throwable $e) {
			$this->logger->debug('Findling: mount list unavailable, skipping the cheap reduction', ['exception' => $e]);
			return [];
		}
```
Für Phase 4 ist der Aufruf `getMountsForFileId($fileId)` statt `getMountsForUser`, die Form (try/catch/degradieren, `debug`-Level, kein Pfad im Log) bleibt.

**Nutzerordner auflösen, jeder Fehler gefangen** (`Provider.php:168-175`):
```php
		try {
			$userFolder = $this->rootFolder->getUserFolder($uid);
		} catch (\Throwable $e) {
			// Every failure is caught on purpose. getUserFolder() signals a
			// missing user with a class from the private namespace of the
			// server and a missing home directory with a different one again;
```

**Nicht-Existenz und Nicht-Sichtbarkeit geben dieselbe Antwort** (`GatewayController.php:68-96`) -- das ist die Vorlage für "Unter diesem Pfad liegt keine Datei, und keine Datei hat diese ID":
```php
			$file = $this->rootFolder->getUserFolder($userId)->getFirstNodeById($fileId);
			// Not visible to this user and not existing at all deliberately give
			// the same answer, so the gateway cannot be used to probe for files
			// the user is not allowed to see.
			if (!$file || !$file instanceof File) {
				return new DataResponse(['error' => 'Node is not a file or could not be found.'], Http::STATUS_NOT_FOUND);
			}
...
		} catch (\OC\User\NoUserException) {
			// Word for word the answer of the not-found branch above, on purpose.
			$this->logger->debug('Findling: content gateway asked for a user that does not exist');
			return new DataResponse(['error' => 'Node is not a file or could not be found.'], Http::STATUS_NOT_FOUND);
```

**Der fertige Zielcode für `describe()`** steht als Beispiel 3 in `04-RESEARCH.md:836-916` und ist gegen `UserMountCache.php:373-413` verifiziert. Der Planner soll ihn übernehmen, nicht neu erfinden.

---

### `php/lib/Service/ScanStatsService.php` (service/repository, CRUD)

**Analog:** `php/lib/Service/FileStateService.php`

**Tabellenkonstante + geschlossene Listen als `public const`** (`FileStateService.php:30-44`):
```php
class FileStateService {
	public const TABLE_NAME = 'findling_file_state';

	/** @var list<string> */
	public const STATES = [
		'indexed',
		'skipped',
		'failed',
	];
```

**Upsert-Muster: erst UPDATE, dann `insertIgnoreConflict`, zwei Versuche** (`FileStateService.php:128-152`) -- exakt die Form, die der idempotente Scan-Zähler braucht (RESEARCH Muster 5, Variante (a): Zeile bei `last_file_id === 0` zurücksetzen, danach addieren):
```php
		for ($attempt = 0; $attempt < 2; $attempt++) {
			$update = $this->db->getQueryBuilder();
			$update->update(self::TABLE_NAME)
				->set('state', $update->createNamedParameter($state, IQueryBuilder::PARAM_STR))
				->set('updated_at', $update->createNamedParameter($now, IQueryBuilder::PARAM_DATE))
				->where($update->expr()->eq('file_id', $update->createNamedParameter($fileId, IQueryBuilder::PARAM_INT)));
			if ($update->executeStatement() >= 1) {
				return true;
			}

			$inserted = $this->db->insertIgnoreConflict(self::TABLE_NAME, [
				'file_id' => $fileId,
				'state' => $state,
				'reason' => $reason,
				'updated_at' => $now->format('Y-m-d H:i:s'),
			]);
			if ($inserted > 0) {
				return true;
			}
		}
```
Begründung im Docblock nicht wegkürzen: `insertIgnoreConflict` statt insert-und-fangen, weil eine gefangene Constraint-Verletzung auf PostgreSQL die ganze Transaktion abbricht (bug audit M7). Der Crawl schreibt innerhalb einer Transaktionsbande (`TX_BAND`), also gilt das hier genauso.

**Vollständige Zeile mit Nullen statt spärlicher Antwort** (`FileStateService.php:161-180`) -- die Form für die neuen Leser `reasonsByState()`, `page()`, `forFile()`:
```php
	public function counts(): array {
		$counts = array_fill_keys(self::STATES, 0);

		$qb = $this->db->getQueryBuilder();
		$qb->select('state')
			->selectAlias($qb->func()->count('*'), 'total')
			->from(self::TABLE_NAME)
			->groupBy('state');

		$result = $qb->executeQuery();
		while (($row = $result->fetch()) !== false) {
			$state = (string)($row['state'] ?? '');
			if (array_key_exists($state, $counts)) {
				$counts[$state] = (int)($row['total'] ?? 0);
			}
		}
		$result->closeCursor();

		return $counts;
	}
```
`closeCursor()` gehört dazu. `array_fill_keys` über die geschlossene Liste ist der Grund, warum "nichts fehlgeschlagen" und "der Zähler ist kaputt" unterscheidbar bleiben; `reasonsByState()` muss dasselbe für die Gründe tun (leere Map je Zustand, nie fehlender Schlüssel).

**Ablehnung zählen, den abgelehnten Wert nie loggen** (`FileStateService.php:182-188`) -- Vorlage für die Validierung der Ausschluss-Präfixe:
```php
	private function reject(): void {
		$this->rejected++;
		$this->logger->warning(
			'Findling: rejected a file state that is not in the closed list',
			['rejected' => $this->rejected],
		);
	}
```

---

### `php/lib/Migration/Version001000Date2026...php` (migration, schema)

**Analoge:** `Version001000Date20260816000000.php` (Tabelle anlegen), `Version001000Date20260902000000.php` (Index nachziehen + `postSchemaChange`)

**Tabelle anlegen, guarded** (`Version001000Date20260816000000.php:39-50,92-116`):
```php
	public function changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper {
		/** @var ISchemaWrapper $schema */
		$schema = $schemaClosure();
		$changed = false;

		if (!$schema->hasTable('findling_queue')) {
			$table = $schema->createTable('findling_queue');
			$table->addColumn('id', Types::BIGINT, ['autoincrement' => true, 'notnull' => true, 'length' => 64]);
			$table->addColumn('file_id', Types::BIGINT, ['notnull' => true, 'length' => 64]);
			...
			$table->setPrimaryKey(['file_id'], 'findling_fs_id');
			$table->addIndex(['state'], 'findling_fs_state');
			$changed = true;
		}

		return $changed ? $schema : null;
	}
```

**Index auf eine bestehende Tabelle nachziehen** (`Version001000Date20260902000000.php:55-85`) -- exakt das Muster für den `(state, updated_at)`-Index auf `findling_file_state` (RESEARCH Pitfall 12):
```php
		$schema = $schemaClosure();
		if (!$schema->hasTable('findling_queue')) {
			return null;
		}

		$table = $schema->getTable('findling_queue');
		$changed = false;

		if (!$table->hasIndex('findling_q_kind')) {
			$table->addIndex(['kind', 'locked_at', 'id'], 'findling_q_kind');
			$changed = true;
		}

		return $changed ? $schema : null;
```

**Harte Regeln aus beiden Docblocks, die in die neue Migration gehören:**
- "The class name and the file name have to be identical to the character." Ein Mismatch heißt: die Migration läuft nie, ohne Fehler irgendwo.
- Jede Änderung `hasTable`/`hasColumn`/`hasIndex`-geschützt, damit ein zweiter Lauf ein No-op ist.
- Index-Namen ≤ 30 Zeichen und mit `findling_`-Präfix, Vorbild `findling_fs_state`, `findling_q_kind`.
- Spaltenlängen als Leck-Schutz begründen (`reason` ist 32 Zeichen lang, "no path fits in 32 characters").

---

### `backend/src/findling/api/diagnose.py` und `rates.py` (route, request-response)

**Analog:** `backend/src/findling/api/status.py` (128 Zeilen, ganz gelesen; die neue Route ist strukturgleich)

**Modul-Docstring als Privacy-Vertrag** (`status.py:1-24`, gekürzt) -- der Ton und die Struktur sind der Vertrag, nicht Dekoration:
```python
"""GET /status: what this container has done, counted, and nothing beyond that.

Everything here is a number, a version mark or a flag. No file name, no location,
no search term, ever. An admin page is a place where such a value is easy to add
"just for support" and impossible to take back...

A missing state database is not a server error. It is what an installation looks
like for the first few minutes, and the honest answer to it is zeros plus a line
saying so. This route is declared with access level ADMIN in appinfo/info.xml...
"""
```
Für `diagnose.py` liegt der fertige, an dieses Muster angelehnte Docstring in `04-RESEARCH.md:920-935`. **Ergänzung, die dort schon steht:** der Satz in `status.py`, `access_level ADMIN` sei "where that decision is enforced", ist für den `exAppRequest`-Weg falsch (Pitfall 10) und wird in dieser Phase präzisiert.

**Imports und Modulkonstanten** (`status.py:26-42`):
```python
import asyncio
import logging

from fastapi import APIRouter
from pydantic import BaseModel

from findling.api import resources
from findling.config import settings
from findling.store.repo import Store, open_read_only

LOGGER = logging.getLogger("findling.api.status")

ROUTER = APIRouter()

# Both notes name a state of this container and never a location on disk.
NO_STATE_YET = "no state database yet, the first indexing pass has not finished"
STATE_UNREADABLE = "the state database exists but could not be opened"
```

**Response-Modell: jedes Feld mit Default** (`status.py:45-64`):
```python
class StatusResponse(BaseModel):
    """The operating state of one container.

    Every field defaults, so the answer for a container that has nothing yet is
    the same shape as the answer for one that has been running for a month. A
    status output whose fields come and go cannot be read by a page that has to
    render both.
    """

    indexed: int = 0
    skipped: int = 0
    failed: int = 0
    ...
    note: str = ""
```

**Read-only-Verbindung, pro Aufruf geöffnet, nie roh** (`status.py:104-123`) -- die neue Route kopiert das Gerüst eins zu eins:
```python
def report() -> StatusResponse:
    """The state of this container. Runs in a worker thread, never raises."""
    resolved = settings()
    if not resolved.state_db.is_file():
        return StatusResponse(note=NO_STATE_YET, lowDisk=resources.low_disk())

    try:
        store = open_read_only(resolved.state_db)
    except OSError as error:
        LOGGER.warning("the state database could not be opened, an %s", type(error).__name__)
        return StatusResponse(note=STATE_UNREADABLE, lowDisk=resources.low_disk())

    try:
        return _of(store)
    finally:
        # Opened per call rather than kept: this route is asked rarely, by one
        # admin page, and a connection of its own is always current without a
        # cache anybody has to invalidate.
        store.close()
```
Beachte: `LOGGER.warning` loggt nur den **Typnamen** der Exception, nicht die Meldung (die enthielte den Pfad).

**Route-Deklaration, Arbeit im Worker-Thread** (`status.py:125-128`):
```python
@ROUTER.get("/status")
async def read_status() -> StatusResponse:
    """Answer with the counters and the version marks of this container."""
    return await asyncio.to_thread(report)
```

**Feldweiser Aufbau, nie Row-Spread** -- für `diagnose.py` zwingend, weil `files` `path` und `title` trägt. Muster in `status.py:87-101` (`_of`) und wörtlich ausformuliert in `04-RESEARCH.md:986-1000`.

**Kein zweites Zählwerk:** `_of()` liest `store.counts()`, `store.acl_totals()`, `store.read_meta()` und rechnet nichts nach. `diagnose.py` liest `store.file_row(file_id)`, `rates.py` liest einen neuen `throughput()`-Leser in `repo.py`.

**Wiring** (`main.py:30-32` und `242-244`) -- zwei Zeilen je neuer Route:
```python
from findling.api.status import ROUTER as STATUS_ROUTER
...
APP.include_router(STATUS_ROUTER)
```

**Routen-Deklaration** (`backend/appinfo/info.xml:107-112`) -- Vorlage für `diagnose` und `rates`:
```xml
			<route>
				<url>status</url>
				<verb>GET</verb>
				<access_level>ADMIN</access_level>
				<headers_to_exclude>[]</headers_to_exclude>
				<bruteforce_protection>[401]</bruteforce_protection>
			</route>
```
Version und `<image-tag>` liegen bei `0.2.0` (`backend/appinfo/info.xml:44,63`) und müssen mit `php/appinfo/info.xml:32` **gemeinsam** angehoben werden.

---

### `backend/src/findling/store/repo.py` (repository, CRUD) -- geändert

**Selbst-Analog.** Die drei Leser, an die sich `throughput()`, `index_bytes()` und der erweiterte Grund-Report anlehnen (`repo.py:523-554`):
```python
    def file_row(self, file_id: int) -> dict[str, Any] | None:
        """The whole row for one file, or None when it has never been judged."""
        cursor = self._conn.execute("SELECT * FROM files WHERE file_id = ?", (file_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return {column[0]: value for column, value in zip(cursor.description, row, strict=True)}

    def counts(self) -> dict[str, int]:
        """Files per state, always all three keys, zeros included."""
        counters = dict.fromkeys(STATE_REASONS, 0)
        for state, total in self._conn.execute("SELECT state, COUNT(*) FROM files GROUP BY state"):
            counters[str(state)] = int(total)
        return counters

    def reasons_by_state(self) -> dict[str, dict[str | None, int]]:
        """The breakdown phase 4 builds its error list from."""
        breakdown: dict[str, dict[str | None, int]] = {state: {} for state in STATE_REASONS}
        for state, reason, total in self._conn.execute(
            "SELECT state, reason, COUNT(*) FROM files GROUP BY state, reason"
        ):
            breakdown.setdefault(str(state), {})[reason] = int(total)
        return breakdown
```
`reasons_by_state()` existiert bereits und ist im Docstring als Quelle der Phase-4-Fehlerliste deklariert. Sie ist **nicht** neu zu bauen.

**Freier Platz und Verzeichnisgröße** (`api/resources.py:110-127`) -- die Behandlung eines nicht messbaren Volumes ist schon da und gilt auch für `indexBytes`:
```python
def low_disk() -> bool:
    directory = _existing_directory(settings().index_dir)
    if directory is None:
        return False
    try:
        return shutil.disk_usage(directory).free < settings().min_free_bytes
    except OSError:
        # Not measurable is not the same as low, and a container whose volume
        # cannot be stated is going to fail louder elsewhere.
        LOGGER.warning("free space of the volume could not be read")
        return False
```

---

### `backend/src/findling/extract/errors.py` (model) -- geändert: `Reason.EXCLUDED`

**Selbst-Analog** (`errors.py:46-96`):
```python
class Reason(StrEnum):
    """Why a file ended up in its state.

    English identifiers because they are code; the German labels of the admin
    page are built in phase 4 from these values. A reason is never composed at
    runtime and never carries a path, a file name or an exception message
    (T-02-56): the code is the whole message.
    """

    # skipped, the deliberate decisions
    TOO_LARGE = "too_large"
    MIME_NOT_ALLOWED = "mime_not_allowed"
    ...

STATE_REASONS: Final[Mapping[State, frozenset[Reason | None]]] = {
    State.INDEXED: frozenset({None, Reason.TRUNCATED}),
    State.SKIPPED: frozenset(
        {
            Reason.TOO_LARGE,
            ...
        }
    ),
```

**Drei Listen, ein Commit** (Pitfall 13). Der neue Grund `excluded` muss gleichzeitig in:
1. `php/lib/Service/FileStateService.php:60-83` (`const REASONS`, im `// skipped`-Block)
2. `backend/src/findling/extract/errors.py:46-96` (`Reason.EXCLUDED` + `STATE_REASONS[State.SKIPPED]`)
3. `backend/src/findling/store/repo.py:115-143` (`STATE_REASONS["skipped"]`)

Das prüfende Gate (`test_extract_errors.py:134-158`) liest die PHP-Konstante per Regex aus der Datei:
```python
def _php_reasons() -> set[str]:
    """The REASONS constant of the PHP companion, read out of its source file."""
    source = PHP_FILE_STATE_SERVICE.read_text(encoding="utf-8")
    block = re.search(r"const REASONS = \[(.*?)\];", source, re.DOTALL)
    assert block is not None, "the REASONS constant is no longer where this test looks for it"
    return set(re.findall(r"'([a-z_]+)'", block.group(1)))
```
Konsequenz für den Plan: die Schreibweise `const REASONS = [` und einfach gequotete, kleingeschriebene Codes bleiben unangetastet, sonst bricht das Gate am Regex und nicht an der Sache.

---

### `php/lib/BackgroundJobs/StorageCrawlJob.php` (job, batch) -- geändert

**Selbst-Analog.** Die Stelle, an der Cap, Ausschluss-Test und Scan-Zähler hineingehören (`StorageCrawlJob.php:109-149`):
```php
			foreach ($this->storageService->getFilesInMount($storageId, $overriddenRoot, $lastFileId, self::BATCH_SIZE) as $entry) {
				$lastFileId = max($lastFileId, $entry->getId());
				$seen++;

				$size = $entry->getSize();
				if ($size > self::MAX_SIZE) {
					$this->fileStateService->record($entry->getId(), 'skipped', 'too_large');
					$skipped++;
				} else {
					$this->queueService->enqueue($entry, $storageId, $rootId);
					$queued++;
				}

				if (++$band >= self::TX_BAND) {
					$this->db->commit();
					$this->db->beginTransaction();
					$band = 0;
				}

				if ($this->time->getTime() >= $deadline) {
					break;
				}
			}
			$this->db->commit();
		} catch (\Throwable $e) {
			$this->db->rollBack();
			throw $e;
		}
```

**Der Cap als Konstante mit Phase-4-Kommentar** (`StorageCrawlJob.php:52-59`) -- bleibt als **Default** stehen, `SettingsService` liefert den geltenden Wert:
```php
	/**
	 * 50 MB, the extraction cap of the zero config guard rails. A file above it
	 * is not queued and not silently dropped either: it gets an end state with
	 * a reason, because the diagnosis of phase 4 reads exactly that table...
	 */
	public const MAX_SIZE = 50 * 1024 * 1024;
```

**Nach jedem Lauf die Cron-Marke setzen** (`StorageCrawlJob.php:151`, identisch in `SubtreeExpandJob.php:181`) -- die Zahl, die die Statusseite als "laufen die Hintergrundaufträge" zeigt:
```php
		$this->appConfig->setValueInt(Application::APP_ID, SchedulerJob::LAST_JOB_RUN, $this->time->getTime());
```

**Terminierungsbedingung als Anker für `finished_at`** (`StorageCrawlJob.php:153-161`) -- genau hier bekommt `findling_scan_stats.finished_at` seinen Wert:
```php
		if ($seen === 0) {
			// Nothing behind the cursor any more, so this mount is done and
			// gets no successor. This is the only way the crawl terminates.
			$this->logger->info('Findling: finished crawling a mount', [
				'storage_id' => $storageId,
				'cursor' => $lastFileId,
			]);
			return;
		}
```

**Bänderungs-Muster für die Räumung** (`SubtreeExpandJob.php:39-90`) -- `EXPANDABLE_KINDS` enthält `KIND_DELETE` bereits, es ist wirklich nur ein Aufruf:
```php
	public const BATCH_SIZE = 250;
	private const MAX_SECONDS = 30;
	private const INTERVAL = 5;
	private const TX_BAND = 250;

	/** @var list<string> */
	private const EXPANDABLE_KINDS = [
		QueueMapper::KIND_ACL,
		QueueMapper::KIND_DELETE,
	];
```
Anstoß aus `ExclusionService`: `$this->jobList->add(SubtreeExpandJob::class, ['storage_id' => ..., 'root_id' => ..., 'ancestor_id' => <Ordner-fileid>, 'kind' => QueueMapper::KIND_DELETE, 'last_file_id' => 0])`. `IJobList::add` dedupliziert über das Argument (`Version001000Date20260816000000.php:74-80` erklärt dieselbe Idempotenz-Denkweise für die Queue).

---

### `php/lib/Listener/FileEventListener.php` (listener, event-driven) -- geändert

**Selbst-Analog** (`FileEventListener.php:340-374`) -- die Stelle, an der Cap und Ausschluss-Test greifen müssen, und die Stelle, an der Pitfall 4 zuschlägt (zwei Pfadräume):
```php
		$mount = $node->getMountPoint();
		$storageId = (int)$mount->getNumericStorageId();
		$rootId = (int)$mount->getStorageRootId();
		if ($storageId <= 0 || $rootId <= 0) {
			return;
		}

		// 3. A mount this app indexes...
		if (!$this->storageService->isIndexedStorage($storageId)) {
			return;
		}

		$size = (int)$node->getSize();
		if (!$isDeletion && $size > StorageCrawlJob::MAX_SIZE) {
			// The same ceiling and the same end state as the crawl...
			// The second exception for a deletion...
			$this->fileStateService->record($fileId, 'skipped', 'too_large');
			return;
		}

		$this->queueService->enqueueFile($fileId, $storageId, $rootId, $isDeletion ? 0 : $size, $isUpdate, $kind);
```
`getStorageRootId()` liegt hier bereits vor -- das ist der Wert, mit dem der mount-relative Pfad gebildet wird (RESEARCH Pitfall 4). Der Ausschluss-Test gehört **zwischen** Zeile 354 und 356, in denselben Helfer, den der Crawl ruft. Die Ausnahme für Löschungen gilt auch für den Ausschluss: ein `excluded`-Verdikt über eine gelöschte Datei würde die Löschung verwerfen.

---

### `php/lib/Service/StorageService.php` (service, batch) -- geändert

**Selbst-Analog.** Die Konstante, die zum Schalter wird, samt ihres eigenen ADM-04-Kommentars (`StorageService.php:30-51`):
```php
	/**
	 * Which mounts the crawl walks.
	 * ...It becomes a switch in phase 4 (ADM-04),
	 * which is why the line stays here instead of being deleted.
	 * @var list<string>
	 */
	private const MOUNT_PROVIDERS = [
		'OC\Files\Mount\LocalHomeMountProvider',   // user home, file backend
		'OC\Files\Mount\ObjectHomeMountProvider',  // user home, object storage backend
		'OCA\GroupFolders\Mount\MountProvider',    // Team Folders
		// 'OCA\Files_External\Config\ConfigAdapter' -- external storage, off by default
	];
```

**Eine Quelle für "welche Mounts sind drin"** (`StorageService.php:142-174`) -- `getMounts()` und `isIndexedStorage()` müssen dieselbe, jetzt konfigurierte Liste sehen; der Docblock warnt namentlich vor genau dem Fehler, den ADM-04 auslösen kann:
```php
	public function getMounts(): iterable {
		return $this->fileAccess->getDistinctMounts(self::MOUNT_PROVIDERS, true);
	}
	...
	public function isIndexedStorage(int $storageId): bool {
		if ($this->indexedStorages === null) {
			$storages = [];
			foreach ($this->getMounts() as $mount) {
				$storages[(int)$mount['storage_id']] = true;
			}
			$this->indexedStorages = $storages;
		}
		return isset($this->indexedStorages[$storageId]);
	}
```

**Per-Request-Cache-Muster** (`StorageService.php:105-121`) -- die Form für den Ausschluss-Präfix-Cache in `ExclusionService`; `IAppConfig` cached selbst pro Request, ein Feld-Cache mit derselben Lebensdauer ist erlaubt, ein längerer wäre falsch (RESEARCH Muster 10):
```php
	/** @var list<int>|null */
	private ?array $mimeIds = null;

	/** @var array<int, true>|null */
	private ?array $indexedStorages = null;
```

**Getrennte Projektion, gemeinsame Abfrage** (`StorageService.php:207-241`) -- `getFileSlice` baut auf `getFilesInMount` auf, damit Crawl und Reconcile dieselben Dateien sehen. Der Ausschluss muss deshalb in `getFilesInMount` greifen, nicht in `getFileSlice`, sonst räumt der Reconcile jede Nacht die Differenz.

---

### `php/lib/Service/AdminViewService.php` (service, Aggregation)

**Analoge:** `php/lib/Command/IndexCommand.php:101-129` (`status()`), `php/lib/Service/QueueService.php:304-313` (`stats()`)

**Der bestehende Aggregator derselben Zahlen** (`IndexCommand.php:101-121`) -- inklusive der Fallunterscheidung, die auf der Seite als "Die Indexierung kommt seit %s nicht voran" erscheint:
```php
	private function status(OutputInterface $output): void {
		$queue = $this->queueService->stats();
		$states = $this->fileStateService->counts();
		...
		$lastRun = $this->appConfig->getValueInt(Application::APP_ID, SchedulerJob::LAST_JOB_RUN);
		if ($lastRun === 0) {
			// The one failure mode that looks like a broken app but is a
			// broken setup: with the default AJAX cron the background jobs
			// only run while somebody is using the web interface.
			$output->writeln('<comment>No background job of this app has run yet. Check the cron setting of this instance.</comment>');
			return;
		}
```

**Queue-Zahlen direkt aus dem Service, nicht über HTTP** (`QueueService.php:304-313`):
```php
	/**
	 * @return array{scheduled:int, running:int, failed:int}
	 */
	public function stats(): array {
		return [
			'scheduled' => $this->queueMapper->countScheduled(),
			'running' => $this->queueMapper->countRunning(),
			'failed' => $this->fileStateService->counts()['failed'] ?? 0,
		];
	}
```
Die Queue-Route trägt `ExAppRequired`; `AdminViewService` ruft den Service, nie die Route.

---

### `php/lib/Settings/Section.php` und `Admin.php` (provider, request-response)

**Kein bestehender Analog:** `php/lib/Settings/` existiert nicht. Der Struktur-Analog für "eine Klasse, die ein OCP-Interface implementiert und aus der App registriert wird" ist `php/lib/Search/Provider.php`.

**Klassenform** (`Provider.php:43`, `AppInfo/Application.php:15-27`):
```php
final class Provider implements IFilteringProvider {
```
```php
class Application extends App implements IBootstrap {
	public const APP_ID = 'findling';
	public const BACKEND_APP_ID = 'findling_backend';
```
`Application::APP_ID` ist der Section-`getID()` und damit die URL `/settings/admin/findling`.

**Konflikt, den der Planner entscheiden muss:** `Provider.php:102` benutzt `#[\Override]`:
```php
	#[\Override]
	public function getName(): string {
		return $this->l10n->t('File contents');
	}
```
`04-RESEARCH.md` (State of the Art, Deprecated-Liste) empfiehlt, `#[\Override]` **nicht** zu benutzen, weil es PHP 8.3 ist und `info.xml` 8.2 deklariert. Der Bestand benutzt es trotzdem, und `php -l` mit PHP 8.2 (`php.yml:51,64`) ist grün, weil ein unbekanntes Attribut erst bei Reflexion aufgelöst wird. Beide Wege sind vertretbar; **eine** Entscheidung treffen und in den Docblock schreiben, statt zwei Schreibweisen im Baum zu haben.

**Registrierung NICHT im Code:** `Application::register()` (`Application.php:35-84`) registriert Search-Provider und Listener. Für Settings gibt es kein `registerSettings()`; die Klassen kommen in `php/appinfo/info.xml`. Vorlage für den Block ist die bestehende Einzeiler-Konvention (`php/appinfo/info.xml:44-57`):
```xml
	<!--
		The two blocks below sit in the order the store schema prescribes...
		Each of them is written on one line on purpose. The
		schema pattern for a PHP class name allows no surrounding whitespace, so
		an indented class name on its own line fails the validation.
	-->
	<repair-steps><install><step>OCA\Findling\Repair\AppInstallStep</step></install></repair-steps>
	<commands><command>OCA\Findling\Command\IndexCommand</command></commands>
```
Der neue Block gehört nach `<commands>` und in derselben Einzeiler-Form:
`<settings><admin>OCA\Findling\Settings\Admin</admin><admin-section>OCA\Findling\Settings\Section</admin-section></settings>`

**Fertige Zielklassen** stehen in `04-RESEARCH.md:688-773` (Beispiel 1) und sind gegen `stable32`/`stable34` verifiziert. `IIconSection`, nie `ISection` (Pitfall 5).

---

### `php/templates/admin.php`, `php/js/admin.js`, `php/css/admin.css`, `php/l10n/de.json`

**Kein Analog im Repo.** Es gibt heute kein Template, kein JS, kein CSS und kein `l10n/`. Der Planner nimmt:
- `04-RESEARCH.md:777-832` (Beispiel 2: Template mit `Util::addScript`/`addStyle`, Initial-State-Leser, `ask()` mit frischem `requesttoken`)
- `04-UI-SPEC.md` als verbindlichen Vertrag für Markup, Blöcke, Copy, SVG-Pfaddaten, Zustands-Chips und Interaktionen

**Projektregeln, die für diese vier Dateien besonders greifen:**
- Quellstrings englisch durch `$l->t()`, deutsche Texte in `l10n/de.json` (RESEARCH Open Question 3, UI-SPEC Copy-Tabelle)
- Pfade sind Nutzerdaten: im Template `p()`, nie `print_unescaped`; im JS `textContent`, nie `innerHTML`
- kein Inline-`<script>` (CSP), kein Hexwert im CSS, keine Emojis, keine Em-Dashes
- `php.yml:64` muss `php/templates` mitprüfen, sonst fällt ein Syntaxfehler erst im Browser auf (Pitfall 11)

---

### `php/lib/Command/DiagnoseCommand.php` (optional, command)

**Analog:** `php/lib/Command/IndexCommand.php` -- exakt: Namensraum, `Command`-Basisklasse, `configure()`/`execute()`, Ausgabe über `sprintf` mit `%-20s`-Spalten, Registrierung als Einzeiler in `info.xml:57`.

```php
	protected function configure(): void {
		$this
			->setName('findling:index')
			->setDescription('Show the state of the Findling index, or start it over')
			->addOption(
				'status',
				null,
				InputOption::VALUE_NONE,
				'Show the counters of the work stock. This is the default.',
			);
	}

	protected function execute(InputInterface $input, OutputInterface $output): int {
		...
		return Command::SUCCESS;
	}
```

---

### `backend/tests/test_diagnose_endpoint.py` / `test_rates_endpoint.py` (test)

**Analog:** `backend/tests/test_status_endpoint.py` (194 Zeilen, ganz gelesen)

**Kopf und Feldmenge als Ganzes** (`test_status_endpoint.py:16-48`) -- der Feldmengen-Test ist die Privacy-Sperre, nicht Kosmetik:
```python
pytestmark = pytest.mark.usefixtures("appapi_environment")

Sign = Callable[[str], dict[str, str]]

STATUS_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "api" / "status.py"

FIELDS = {
    "indexed",
    "skipped",
    ...
    "note",
}
```

**Die fünf Tests, die jede neue Route braucht** (`test_status_endpoint.py`):
```python
def test_the_answer_carries_the_counters_the_versions_and_nothing_else(...):
    assert set(answer) == FIELDS

def test_the_answer_carries_no_path_no_file_name_and_no_search_term(...):
    for value in answer.values():
        if isinstance(value, str):
            assert "/" not in value
            assert "Akte" not in value

def test_without_a_state_database_the_answer_is_zeros_and_a_note(...):
    assert set(answer) == FIELDS
    assert answer["note"] != ""

def test_a_request_without_any_appapi_header_is_unauthorized(client: TestClient) -> None:
    response = client.get("/status")
    assert response.status_code == 401

def test_the_status_module_opens_the_state_read_only() -> None:
    source = STATUS_SOURCE.read_text(encoding="utf-8")
    assert "open_read_only" in source
    assert "open_store" not in source

def test_asking_for_the_status_changes_nothing(...):
    before = database.read_bytes()
    _status(client, sign("admin"))
    assert database.read_bytes() == before
```

**Die Routen-Montage-Assertion** (`test_status_endpoint.py:163-171`) muss mitwachsen, mit der Begründung, warum sie über OpenAPI und nicht über `APP.routes` fragt:
```python
def test_all_three_routes_are_mounted() -> None:
    paths = set(APP.openapi()["paths"])
    assert {"/search", "/snippets", "/status"} <= paths
```

---

## Shared Patterns

### Gate B erweitern (nicht umgehen)

**Quelle:** `backend/tests/test_php_trust_boundary.py` (272 Zeilen, ganz gelesen)
**Anwenden auf:** dieselbe Arbeit, die `SettingsController.php` anlegt

Heute kennt das Gate genau eine Routenklasse (`test_php_trust_boundary.py:122-147`):
```python
def scan_source(relative_path: str, source: str) -> list[str]:
    for route in routes_of(relative_path, source):
        attributes = _attributes_above(lines, route.line - 1)
        if not any(EXAPP_ATTRIBUTE in attribute for attribute in attributes):
            violations.append(
                f"{route.file}:{route.line}: {route.method}() is a route without {EXAPP_ATTRIBUTE}, "
                "so any browser session reaches it"
            )

        statement = _first_statement(lines, _body_start(lines, route.line - 1))
        if GUARD_CALL not in statement:
            violations.append(...)
```

Und es fordert zusätzlich (`test_php_trust_boundary.py:164-187`):
```python
    assert len(routes) == mentions
    # Eight today: five on the queue, two on the reconcile, one on the content
    # gateway. A lower number means the parser lost something.
    assert len(routes) >= 8
...
def test_every_controller_of_the_app_carries_at_least_one_route() -> None:
    unrouted = [name for name, source in _controller_sources() if not routes_of(name, source)]
    assert unrouted == []
```

Ein Admin-Controller verletzt das in beide Richtungen. Erweiterung nach RESEARCH Pitfall 7: zwei Klassen (`ExAppRequired` + `rejectForeignCaller` **oder** Admin-Route ohne jedes Attribut), für die Admin-Klasse die Verschärfung "kein `NoAdminRequired`, kein `PublicPage`, kein `NoCSRFRequired`, kein `ExAppRequired`", die `>= 8` anheben, und neue Selbsttests im bestehenden Stil.

**Der Selbsttest-Stil, der zu kopieren ist** (`test_php_trust_boundary.py:192-239`) -- Textprobe als Modulkonstante plus je ein Test pro Bruchart plus ein Gegenbeispiel:
```python
_GUARDED = """<?php

class ExampleController extends OCSController {
\t/**
\t * A docblock, so that the attribute walk has a wall to stop at.
\t */
\t#[\\OCP\\AppFramework\\Http\\Attribute\\ExAppRequired]
...
"""

def test_a_fully_guarded_route_is_clean() -> None:
    # The counter sample of the two below. Without it a gate that reported every
    # route as broken would also pass both failure tests.
    assert scan_source("ExampleController.php", _GUARDED) == []
```

### Die Schreib-Allowlist bleibt bei drei Einträgen

**Quelle:** `backend/tests/test_readonly_gate.py:190-214`
**Anwenden auf:** jeden Plan-Task, der über eine Räumung nachdenkt
```python
# This is the third and, on today's understanding, the last write this container
# needs... A fourth entry has to argue for itself against
# test_write_allowlist_has_exactly_three_entries, which is the point of that test.
OCS_WRITE_ALLOWLIST: frozenset[str] = frozenset(
    {
        "/ocs/v2.php/apps/findling/queues/documents",
        "/ocs/v2.php/apps/findling/queues/documents/unlock",
        "/ocs/v2.php/apps/findling/queues/documents/requeue",
    }
)
```
Phase 4 braucht keinen vierten Eintrag: die Räumung wird PHP-seitig über `SubtreeExpandJob` eingereiht (RESEARCH Muster 9). Ein Plan, der eine schreibende Container-Route vorschlägt, ist an dieser Stelle falsch.

### Aufruf des Containers aus PHP

**Quelle:** `php/lib/Service/ExAppService.php:252-347`
**Anwenden auf:** `AdminViewService` (Status, Diagnose, Raten)

```php
	private function call(string $path, string $userId, array $body, float $secondsLeft = self::REQUEST_TIMEOUT_SECONDS): ?array {
		$timeout = min(self::REQUEST_TIMEOUT_SECONDS, $secondsLeft);
		...
		// info.xml has no way to declare an app to app dependency, so the bond
		// to app_api is a runtime check.
		if (!$this->appManager->isEnabledForUser('app_api', $user)) {
			$this->logger->info('Findling: app_api is not enabled, returning no results');
			return null;
		}

		try {
			$appApi = \OCP\Server::get(\OCA\AppAPI\PublicFunctions::class);
		} catch (ContainerExceptionInterface|NotFoundExceptionInterface) {
			$this->logger->info('Findling: AppAPI public functions unavailable');
			return null;
		}

		$response = $appApi->exAppRequest(
			Application::BACKEND_APP_ID,
			$path,
			$userId,
			'POST',
			$body,
			['timeout' => $timeout],
		);

		// Case 1 first, always. AppAPI catches every transport exception and
		// hands back an array...
		if (is_array($response)) {
			$this->logger->warning('Findling: backend unreachable', [...]);
			return null;
		}

		// Case 2. AppAPI hard sets http_errors to false, so 4xx and 5xx arrive
		// as an ordinary response object instead of throwing.
		if ($response->getStatusCode() >= 400) { ... return null; }

		// Case 3. A 2xx does not promise a body that parses...
		$responseBody = $response->getBody();
		if (!is_string($responseBody) || strlen($responseBody) > self::MAX_BODY_BYTES) { ... return null; }

		// Case 4.
		$decoded = json_decode($responseBody, true);
		if (!is_array($decoded)) { ... return null; }

		return $decoded;
	}
```

Die vier Fälle sind **vollständig zu übernehmen**. Für Phase 4 ändert sich nur:
- `'GET'` statt `'POST'`, Parameter als `$params` (AppAPI hängt sie per `http_build_query` an)
- der Timeout darf länger sein als die 1.5 s der Suche, aber nicht viel (RESEARCH Beispiel 5 schlägt 2.0 s vor)
- der Kommentar bei `is_array($response)` sagt heute "phase 4 builds the status page out of exactly this signal and owns the aggregation then" (`ExAppService.php:305-307`). Genau das passiert jetzt: die Seite sagt "Container nicht erreichbar" statt "nicht indexiert".

### Log-Regel des Projekts

**Quellen:** `ReconcileController.php:102-111`, `GatewayController.php:97-107`, `StorageCrawlJob.php:26-28`, `FileStateService.php:85-92`
**Anwenden auf:** jede neue Klasse dieser Phase

- Log-Meldung ist ein **statischer** Satz, die Exception reist im Feld `['exception' => $e]` (Nextcloud rendert sie unter dem Log-Level des Admins).
- Nie ein Pfad, ein Dateiname oder eine Bibliotheksmeldung im Log. Zähler, Storage-Id, Cursor, Grundcode: das reicht, um einen Lauf zu verfolgen.
- Ein abgelehnter Eingabewert wird **nicht** geloggt, nur gezählt (`FileStateService::reject()`), weil genau in diesem Feld ein Dateiname ankommt.
- Level: `error` für einen kaputten Zustand, `warning` für einen abgelehnten Aufruf oder einen unerreichbaren Container, `info`/`debug` für Verlauf.

### Docblock-Vertrag statt Kommentarlosigkeit

Jede gelesene Datei dieses Repos erklärt im Klassen- oder Modul-Docblock, **warum** sie so gebaut ist und welche Alternative bewusst verworfen wurde (`FileStateService.php:12-28`, `StorageService.php:12-28`, `status.py:1-24`, `SubtreeExpandJob.php:18-37`). Das ist die stärkste Konvention des Projekts. Neue Dateien der Phase 4 ohne diesen Absatz fallen aus dem Baum heraus, auch wenn kein Gate sie ablehnt. Besonders zu bedienen:

- `FileStateService.php:15-18` behauptet heute: "die Statusseite der Phase 4 liest diese Tabelle und **fragt nie den Container**". `status.py:3` behauptet: "Phase 4 builds the admin page; **this is where its numbers come from**". Die beiden widersprechen sich (RESEARCH Pitfall 3). Die Aufteilung (`skipped`/`failed`/Fehlerliste aus PHP, `indexed`/`docs`/`aclRows`/Versionsmarken/Platz/Durchsatz aus dem Container) muss in **beide** Docblocks geschrieben werden. Sonst ist die erste Support-Frage die Differenz.
- `StorageService.php:36-38` und `:152-153` nennen ADM-04 namentlich und sagen, was passiert, wenn es zwei Providerlisten gibt. Diese Kommentare werden beim Umbau aktualisiert, nicht gelöscht.

### CI-Assertion für eine Store-Normalisierung

**Quelle:** `.github/workflows/php.yml:110-118`
**Anwenden auf:** den `<settings>`-Block (RESEARCH Pitfall 9)
```yaml
      - name: State the routes finding explicitly
        run: |
          normalised=$(xsltproc "${RUNNER_TEMP}/pre-info.xslt" backend/appinfo/info.xml)
          if echo "$normalised" | grep -q '<routes>'; then
            echo "pre-info.xslt kept the routes block; the assumption behind the packaging step changed"
            exit 1
          fi
          echo "pre-info.xslt dropped the routes block as expected, so the release archive must carry info.xml unchanged"
```
Der Zwillingsschritt prüft, dass der normalisierte `<settings>`-Block **leer** ist, mit derselben Begründungszeile. Und `php.yml:64` bekommt `php/templates`:
```yaml
      - name: Syntax check every PHP file
        run: find php/lib php/appinfo -name '*.php' -print0 | xargs -0 -n1 php -l
```

---

## No Analog Found

| Datei | Rolle | Datenfluss | Grund |
|---|---|---|---|
| `php/templates/admin.php` | view | request-response | Es gibt kein `php/templates/`. Vorlage: `04-RESEARCH.md:777-795` (Beispiel 2) + `04-UI-SPEC.md` (Blockaufbau, Copy, SVG) |
| `php/js/admin.js` | client script | request-response | Es gibt kein JS im Repo, kein `package.json`, kein Build (D-02). Vorlage: `04-RESEARCH.md:797-832` (Initial-State-Leser, frischer `requesttoken`) + UI-SPEC Interaktionsvertrag |
| `php/css/admin.css` | style | -- | Kein CSS im Repo. Vorlage: UI-SPEC (nur `var(--...)`, kein Hexwert, `<progress>`-Höhe als einzige Überschreibung) |
| `php/img/app-dark.svg` | asset | -- | Kein `php/img/`. Vorlage: UI-SPEC "Design System" (MDI, Apache-2.0, Eintrag in `THIRD-PARTY.md` mit Commit-Hash) |
| `php/l10n/de.json`, `php/l10n/de.js` | i18n data | -- | Kein `l10n/` im Repo. Format: `{"translations": {...}, "pluralForm": "nplurals=2; plural=(n != 1);"}`; `Util::addScript` lädt `l10n/<lang>.js` automatisch und ignoriert eine fehlende Datei still |
| `php/lib/Settings/Section.php` | provider | request-response | Kein `php/lib/Settings/`. Struktur-Analog `Search/Provider.php` (siehe oben), Zielcode `04-RESEARCH.md:688-731` |
| `php/lib/Settings/Admin.php` | provider | request-response | dito, Zielcode `04-RESEARCH.md:733-773` |

Für alle sieben gilt: der Planner referenziert RESEARCH/UI-SPEC als Quelle, **nicht** ein Nextcloud-Tutorial. Insbesondere ist `ISection` in NC 32-34 nicht vorhanden (Pitfall 5) und `OCP.InitialState.loadState()` seit NC 18 deprecated (UI-SPEC).

---

## Konflikte, die der Planner auflösen muss

1. **`#[\Override]`:** Bestand benutzt es (`Search/Provider.php:102`), RESEARCH rät davon ab (PHP 8.3 gegen deklarierte 8.2). Eine Entscheidung, dokumentiert im Docblock der neuen Settings-Klassen.
2. **Zwei Docblocks widersprechen sich über die Quelle von `skipped`/`failed`** (`FileStateService.php:15-18` gegen `status.py:3`). Auflösung ist Teil der Arbeit, nicht Beiwerk (Pitfall 3).
3. **`status.py:20-23` behauptet, `access_level ADMIN` sei der durchsetzende Ort.** Für den `exAppRequest`-Weg stimmt das nicht (Pitfall 10); der Satz wird in dieser Phase präzisiert.
4. **Gate B muss in derselben Arbeit erweitert werden, die den Controller anlegt.** Zwei getrennte Tasks lassen den Baum zwischendurch rot.
5. **`excluded` in drei Dateien in einem Task** (Pitfall 13), sonst produziert `FileStateService::record` stillschweigend eine Datei ohne Verdikt.

---

## Metadata

**Analog search scope:** `php/lib/**` (alle 25 PHP-Dateien gelistet, 12 gelesen), `php/appinfo/`, `backend/src/findling/api/`, `backend/src/findling/store/`, `backend/src/findling/extract/`, `backend/appinfo/`, `backend/tests/` (30 Dateien gelistet, 4 gelesen), `.github/workflows/`
**Files scanned:** 61 gelistet, 21 gelesen (12 vollständig, 9 in gezielten Abschnitten)
**Pattern extraction date:** 2026-09-02
