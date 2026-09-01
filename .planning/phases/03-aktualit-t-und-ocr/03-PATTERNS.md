# Phase 3: Aktualität und OCR - Pattern Map

**Mapped:** 2026-09-01
**Files analyzed:** 37 (13 neu, 24 geändert)
**Analogs found:** 34 / 37 (3 ohne Analog)

Alle Prosa hier ist deutsch, alle Code-Auszüge sind unverändert aus dem Repo und daher englisch. Zeilennummern beziehen sich auf den Stand vom 2026-09-01.

---

## File Classification

### PHP-Companion (`php/`)

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Match |
|----------------------|-------|------------|-----------------|-------|
| `php/lib/Listener/FileEventListener.php` (NEU) | listener | event-driven | keins (siehe "No Analog Found") | none |
| `php/lib/Listener/ShareEventListener.php` (NEU) | listener | event-driven | keins | none |
| `php/lib/BackgroundJobs/SubtreeExpandJob.php` (NEU) | background job (QueuedJob) | batch | `php/lib/BackgroundJobs/StorageCrawlJob.php` | exact |
| `php/lib/BackgroundJobs/ReconcileScheduleJob.php` (NEU) | background job (TimedJob) | scheduled/batch | `php/lib/BackgroundJobs/SchedulerJob.php` | role-match |
| `php/lib/Controller/ReconcileController.php` (NEU) | controller | request-response (nur lesend) | `php/lib/Controller/GatewayController.php` | exact |
| `php/lib/Migration/Version001000Date2026MMDD000000.php` (NEU) | migration | schema | `php/lib/Migration/Version001000Date20260901000000.php` | exact |
| `php/lib/AppInfo/Application.php` (MOD) | config/bootstrap | registration | sich selbst, Zeilen 27-34 | exact |
| `php/lib/Db/QueueMapper.php` (MOD: `kind`, `claimBatch(kind)`, `requeueAs()`, `LOCK_TIMEOUT` je Art) | mapper | CRUD | sich selbst, Zeilen 82-231 | exact |
| `php/lib/Service/QueueService.php` (MOD: `describe()` je Job-Art) | service | request-response | sich selbst, Zeilen 200-246 | exact |
| `php/lib/Service/FileStateService.php` (MOD: 3 neue REASONS) | service | CRUD | sich selbst, Zeilen 52-72 | exact |
| `php/lib/Service/StorageService.php` (MOD: Bild-Mimetypes, Slice-Query) | service | batch/read | sich selbst, Zeilen 64-140 | exact |
| `php/lib/Controller/QueueController.php` (MOD: `requeue()`) | controller | request-response | sich selbst, Zeilen 168-190 | exact |
| `php/lib/Repair/AppInstallStep.php` (MOD: Abgleich-Job registrieren) | config | one-shot | sich selbst, Zeilen 51-66 | exact |

### Container (`backend/`)

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Match |
|----------------------|-------|------------|-----------------|-------|
| `backend/src/findling/extract/ocr.py` (NEU) | extractor/utility | transform + Subprozess | `backend/src/findling/extract/pdf.py` | role-match |
| `backend/src/findling/extract/raster.py` (NEU) | utility | transform (C-Ressourcen) | `backend/src/findling/extract/pdf.py::_page_text` | exact |
| `backend/src/findling/extract/image.py` (NEU, optional; Pillow-Deckel) | utility | transform | `backend/src/findling/extract/pdf.py` | role-match |
| `backend/src/findling/worker/reconcile.py` (NEU) | worker | batch/pull | `backend/src/findling/worker/poller.py` | exact |
| `backend/src/findling/nc/files.py` (NEU, Client-Schale für `/files/slice`) | client-adapter | pull/pagination | `backend/src/findling/nc/queue.py` | exact |
| `backend/src/findling/extract/dispatch.py` (MOD: `Route.OCR`, Bild-Mimetypes) | dispatcher | routing | sich selbst, Zeilen 44-92, 139-167 | exact |
| `backend/src/findling/extract/errors.py` (MOD: 3 neue Reasons) | model/taxonomy | - | sich selbst, Zeilen 46-105 | exact |
| `backend/src/findling/extract/pdf.py` (MOD: `_MIN_CHARS_PER_PAGE` nachmessen) | extractor | transform | sich selbst, Zeilen 38-59 | exact |
| `backend/src/findling/extract/sandbox.py` (MOD: Timeout je Job) | infra/process guard | request-response über Pipe | sich selbst, Zeilen 196-282 | exact |
| `backend/src/findling/index/writer.py` (MOD: `stored_body()`, `drop_document()`) | index writer | CRUD | sich selbst, Zeilen 176-210 | exact |
| `backend/src/findling/store/repo.py` (MOD: etag, tombstone, `gone_in_range`, Cursor) | repository | CRUD | sich selbst, Zeilen 122-163, 315-364, 439-499 | exact |
| `backend/src/findling/store/schema.sql` (MOD: nur Indizes, keine Spalten) | schema | - | sich selbst | exact |
| `backend/src/findling/worker/poller.py` (MOD: Dispatch nach `kind`) | worker | pull/request-response | sich selbst, Zeilen 355-474 | exact |
| `backend/src/findling/nc/queue.py` (MOD: `kind` in `QueueJob`, `_job()` je Art) | client-adapter | pull | sich selbst, Zeilen 52-84, 171-208 | exact |
| `backend/src/findling/nc/client.py` (MOD: `files_slice()`, `requeue_documents()`) | client | request-response | sich selbst, Zeilen 293-361 | exact |
| `backend/src/findling/config.py` (MOD: `FINDLING_OCR_*`) | config | - | sich selbst, Zeilen 100-137, 229-247, 264-277 | exact |
| `backend/appinfo/info.xml` (MOD: OCR-Env-Variablen) | config | - | sich selbst, Zeilen 123-141 | exact |
| `backend/Dockerfile` (MOD: tesseract-apt-Block) | build config | - | sich selbst, Zeilen 92-110 (`wngerman`) | exact |
| `backend/pyproject.toml` (MOD: pillow direkt pinnen) | build config | - | sich selbst | exact |
| `THIRD-PARTY.md` (MOD) | docs | - | sich selbst (wngerman-Absatz) | exact |

### Tests, Korpus, CI, Doku

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Match |
|----------------------|-------|------------|-----------------|-------|
| `backend/tests/test_readonly_gate.py` (MOD: `OCS_WRITE_ALLOWLIST` + Reason-Parität PHP) | test/gate | statisch (AST) | sich selbst, Zeilen 62-74, 173-178 | exact |
| `backend/tests/test_ocr.py` (NEU) | test | - | `backend/tests/test_extract_documents.py` | role-match |
| `backend/tests/test_reconcile.py` (NEU) | test | - | `backend/tests/test_poller.py` | exact |
| `backend/tests/test_queue_client.py` (MOD: `kind`-Felder) | test | - | sich selbst | exact |
| `backend/tests/test_store_repo.py` (MOD: tombstone, gone_in_range) | test | - | sich selbst | exact |
| `scripts/dev/build_corpus.py` (MOD: DACH-/Scan-/Bild-Korpus) | tool | file-I/O | sich selbst, Zeilen 1-32 | exact (mit Bruch, s.u.) |
| `.github/workflows/integration.yml` (MOD: Gate B + Verdikt-Zähler, Events-blockiert-Test) | CI | - | sich selbst | exact |
| `docs/german-analyzer.md`, `docs/ocr.md` (NEU/MOD) | docs | - | `docs/german-analyzer.md` (Grenzen-Abschnitt) | exact |

---

## Pattern Assignments

### `php/lib/BackgroundJobs/SubtreeExpandJob.php` (QueuedJob, batch)

**Analog:** `php/lib/BackgroundJobs/StorageCrawlJob.php` — deckungsgleich in Aufgabe (Teilbaum in Bändern auflösen, eigenen Nachfolger planen).

**Konstanten-Block als Muster** (`StorageCrawlJob.php:31-68`) — Bandgrösse, Wanduhr-Deckel, Nachfolger-Intervall, Transaktionsband; jede Konstante trägt ihre Begründung:

```php
	public const BATCH_SIZE = 2000;
	private const MAX_SECONDS = 30;
	private const INTERVAL = 5;
	private const TX_BAND = 250;
```

Für den Teilbaum-Job sind laut Recherche Bänder von 250 und 30 s Wanduhr gesetzt; die Konstantenform (public/private + Kommentar mit Messung) ist zu übernehmen.

**Argument-Validierung und Selbstabbruch** (`StorageCrawlJob.php:83-94`):

```php
	protected function run($argument): void {
		$storageId = (int)($argument['storage_id'] ?? 0);
		$rootId = (int)($argument['root_id'] ?? 0);
		$overriddenRoot = (int)($argument['overridden_root'] ?? 0);
		$lastFileId = (int)($argument['last_file_id'] ?? 0);

		if ($storageId <= 0 || $overriddenRoot <= 0) {
			// A malformed argument would otherwise reschedule itself forever
			// against a mount that does not exist.
			$this->logger->warning('Findling: dropped a crawl job without a usable mount', ['storage_id' => $storageId]);
			return;
		}
```

**Transaktionsband plus Cursor plus Zeitdeckel** (`StorageCrawlJob.php:107-149`) — das Herzstück, das der Teilbaum-Job 1:1 spiegelt (nur mit `kind=acl`-Enqueue statt Grössenprüfung):

```php
		$this->db->beginTransaction();
		try {
			foreach ($this->storageService->getFilesInMount($storageId, $overriddenRoot, $lastFileId, self::BATCH_SIZE) as $entry) {
				$lastFileId = max($lastFileId, $entry->getId());
				$seen++;
				...
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

**Terminierung und Nachfolgerplanung** (`StorageCrawlJob.php:153-175`):

```php
		if ($seen === 0) {
			// Nothing behind the cursor any more, so this mount is done and
			// gets no successor. This is the only way the crawl terminates.
			$this->logger->info('Findling: finished crawling a mount', [...]);
			return;
		}
		...
		$this->jobList->scheduleAfter(self::class, $this->time->getTime() + self::INTERVAL, [
			'storage_id' => $storageId,
			...
			'last_file_id' => $lastFileId,
		]);
```

**Log-Regel (gilt für alle neuen PHP-Klassen):** `StorageCrawlJob.php:26-28` — "Nothing here logs a path or a file name. Counters, the storage id and the cursor are enough".

---

### `php/lib/BackgroundJobs/ReconcileScheduleJob.php` (TimedJob, scheduled)

**Analog:** `php/lib/BackgroundJobs/SchedulerJob.php` (role-match: QueuedJob statt TimedJob, aber identische Aufgabe "plant Arbeit, arbeitet nicht selbst").

**Trennung planen/arbeiten** (`SchedulerJob.php:15-26`) — der Satz, den der Abgleich-Job wörtlich erben soll:

```php
 * It does no work itself, which
 * is deliberate: enumerating mounts is cheap and bounded, walking them is
 * neither, and mixing the two would put an unbounded amount of work into a
 * single cron slot.
```

**Konstante für den Zeitstempel im IAppConfig** (`SchedulerJob.php:28-38`) — dasselbe Muster trägt das 24-Stunden-Gate aus Pitfall 5:

```php
	public const LAST_JOB_RUN = 'last_job_run';
```

**Schreiben in die App-Konfiguration am Ende des Laufs** (`SchedulerJob.php:63-65`):

```php
		$this->appConfig->setValueInt(Application::APP_ID, self::LAST_JOB_RUN, $this->time->getTime());
		$this->logger->info('Findling: scheduled the crawl of every mount', ['mounts' => $mounts]);
```

**Was der TimedJob zusätzlich braucht** (aus RESEARCH Beispiel 5, kein Repo-Analog): `parent::__construct($time); $this->setInterval(3600); $this->setTimeSensitivity(IJob::TIME_INSENSITIVE);` — plus das eigene 24-Stunden-Gate, weil `maintenance_window_start` per Default aus ist.

**Registrierung des neuen Jobs:** `php/lib/Repair/AppInstallStep.php:51-66` — inklusive der Marke im AppConfig und dem "wirft nie"-Vertrag:

```php
	public function run(IOutput $output): void {
		try {
			if ($this->appConfig->getValueBool(Application::APP_ID, self::FIRST_INDEX_SCHEDULED)) {
				$output->info('Findling has already scheduled its first index, leaving it alone.');
				return;
			}

			$this->jobList->add(SchedulerJob::class);
			$this->appConfig->setValueBool(Application::APP_ID, self::FIRST_INDEX_SCHEDULED, true);
			...
		} catch (\Throwable $e) {
			$this->logger->error('Findling: could not schedule the first index during the installation', ['exception' => $e]);
			$output->warning('Findling could not schedule its first index. Run "occ findling:index --restart" to start it by hand.');
		}
	}
```

---

### `php/lib/Controller/ReconcileController.php` (controller, nur lesend)

**Analog:** `php/lib/Controller/GatewayController.php` (exakt: einzige bestehende reine Lese-Route der ExApp-Grenze), ergänzt um die Validierungs-Helfer aus `QueueController.php`.

**Attribut-Trias, ausgeschrieben** (`GatewayController.php:50-52`) — der Kommentar darüber erklärt, warum voll qualifiziert:

```php
	#[\OCP\AppFramework\Http\Attribute\ExAppRequired]
	#[NoCSRFRequired]
	#[ApiRoute(verb: 'GET', url: '/files/{fileId}')]
	public function getFileContents(int $fileId, string $userId): DataResponse|StreamResponse {
```

Achtung: `QueueController` schreibt alle drei Attribute voll qualifiziert (`QueueController.php:81-83`), weil ein Grep-Gate sie so zählt. Für neue Routen gilt die `QueueController`-Schreibweise, nicht die gemischte des Gateways.

**Fremde ExApp abweisen** (`QueueController.php:227-239`) — als private Methode, in jeder neuen Controller-Methode als erste Zeile aufzurufen:

```php
	private function rejectForeignCaller(): ?DataResponse {
		$callerAppId = $this->request->getHeader('EX-APP-ID');
		if ($callerAppId === Application::BACKEND_APP_ID) {
			return null;
		}

		$this->logger->warning('Findling: queue called by a foreign ExApp', ['app' => $callerAppId]);

		return new DataResponse(
			['error' => 'This route is reserved for the Findling backend.'],
			Http::STATUS_FORBIDDEN,
		);
	}
```

**Grenzen als Konstanten, nicht als Vorschläge** (`QueueController.php:38-60`) — für `limit` und `after` der Slice-Route zu spiegeln:

```php
	private const DEFAULT_BATCH_FILES = 32;
	private const DEFAULT_BATCH_BYTES = 67108864;
	private const MAX_BATCH_FILES = 256;
	private const MIN_BATCH_BYTES = 1048576;
	private const MAX_BATCH_BYTES = 1073741824;
	private const MAX_LIST_LENGTH = 1000;
```

und die Klemmung (`QueueController.php:90-91`):

```php
		$limit = max(1, min(self::MAX_BATCH_FILES, $n));
		$budget = max(self::MIN_BATCH_BYTES, min(self::MAX_BATCH_BYTES, $max_bytes));
```

**Fehlerbehandlung je Methode** (`QueueController.php:93-98`) — try/catch um den Service, `getMessage()` im Log (Sec-L6 dieser Phase prüft genau diese Zeile), generische Meldung nach aussen:

```php
		try {
			$files = $this->queueService->claim($limit, $budget);
		} catch (\Throwable $e) {
			$this->logger->error('Findling: could not hand out a batch: ' . $e->getMessage(), ['exception' => $e]);
			return new DataResponse(['error' => 'Queue is not available.'], Http::STATUS_INTERNAL_SERVER_ERROR);
		}
```

**Kein Eintrag in `routes.php`** (`php/appinfo/routes.php:5-13`): beide Arrays bleiben leer, jede Route wird per `ApiRoute`-Attribut deklariert.

---

### `php/lib/Controller/QueueController.php` (MOD, `requeue()`)

**Analog:** `unlockDocuments()` in derselben Datei (`QueueController.php:168-190`) — gleiche Form, gleiche Reihenfolge, gleiche Rückgabe:

```php
	#[\OCP\AppFramework\Http\Attribute\ExAppRequired]
	#[\OCP\AppFramework\Http\Attribute\NoCSRFRequired]
	#[\OCP\AppFramework\Http\Attribute\ApiRoute(verb: 'POST', url: '/queues/documents/unlock')]
	public function unlockDocuments(array $ids = []): DataResponse {
		$foreign = $this->rejectForeignCaller();
		if ($foreign !== null) {
			return $foreign;
		}

		$queueIds = $this->intList($ids);
		if ($queueIds === null) {
			return $this->badList();
		}

		try {
			$released = $this->queueService->unlock($queueIds);
		} catch (\Throwable $e) {
			$this->logger->error('Findling: could not release a batch: ' . $e->getMessage(), ['exception' => $e]);
			return new DataResponse(['error' => 'Queue is not available.'], Http::STATUS_INTERNAL_SERVER_ERROR);
		}

		return new DataResponse(['released' => $released]);
	}
```

**Eingabevalidierung als geschlossene Liste** (`QueueController.php:251-300`): `intList()` für die fileIds, und für den neuen Parameter `kind` exakt das Muster von `failureList()`, das den Reason gegen `FileStateService::REASONS` prüft:

```php
			$id = $this->queueId($entry['queueId'] ?? null);
			$reason = $entry['reason'] ?? null;
			if ($id === null || !is_string($reason) || !in_array($reason, FileStateService::REASONS, true)) {
				return null;
			}
```

`kind` muss genauso gegen eine geschlossene Konstantenliste (`QueueMapper::KINDS`) geprüft werden, nicht gegen ein Regex.

**Nicht vergessen:** die neue Schreibroute braucht einen Eintrag in `OCS_WRITE_ALLOWLIST` (siehe Shared Patterns), und der Klassen-Docstring `QueueController.php:16-36` nennt heute "zwei Schreibpfade" — der Satz wird auf drei geändert.

---

### `php/lib/Db/QueueMapper.php` (MOD: `kind`, Claim je Art, `requeueAs()`)

**Analog:** die Datei selbst. Drei Muster sind zu erhalten.

**Idempotentes Enqueue mit zwei Versuchen** (`QueueMapper.php:82-112`) — die neue Signatur bekommt `kind` dazu, die Struktur bleibt:

```php
		for ($attempt = 0; $attempt < 2; $attempt++) {
			$inserted = $this->db->insertIgnoreConflict(self::TABLE_NAME, [
				'file_id' => $fileId,
				'storage_id' => $storageId,
				'root_id' => $rootId,
				'is_update' => $isUpdate ? 1 : 0,
				'size' => $size,
				'locked_at' => $this->freeMark()->format('Y-m-d H:i:s'),
			]);
			if ($inserted > 0) {
				return;
			}

			if ($this->refreshExisting($fileId, $size, $isUpdate)) {
				return;
			}
		}

		throw new \RuntimeException('the queue row for this file keeps appearing and disappearing');
```

Die Zusammenführungsregel "Aufwertung, nie Abwertung" (`acl < metadata < content|ocr`, `delete` absorbierend) gehört in `refreshExisting()` (`QueueMapper.php:129-152`), also in den Konfliktzweig, nicht in `enqueue()`.

**Bedingtes UPDATE als Claim, plus Token** (`QueueMapper.php:165-231`) — die `kind`-Filterung kommt in die Kandidatenabfrage UND in die Claim-Bedingung, `freeRowCondition()` bleibt die einzige Definition von "frei":

```php
		$candidates = $this->db->getQueryBuilder();
		$candidates->select('id', 'size')
			->from(self::TABLE_NAME)
			->where($this->freeRowCondition($candidates, $cutoff))
			->orderBy('id', 'ASC')
			->setMaxResults($limit);
		...
		$token = bin2hex(random_bytes(16));
		$claim = $this->db->getQueryBuilder();
		$claim->update(self::TABLE_NAME)
			->set('locked_at', $claim->createNamedParameter($now, IQueryBuilder::PARAM_DATE))
			->set('claim_token', $claim->createNamedParameter($token))
			->set('dirty', $claim->createNamedParameter(false, IQueryBuilder::PARAM_BOOL))
			->set('retries', $claim->createFunction('retries + 1'))
			->where($claim->expr()->in('id', $claim->createNamedParameter($wanted, IQueryBuilder::PARAM_INT_ARRAY)))
			->andWhere($this->freeRowCondition($claim, $cutoff));
```

**`LOCK_TIMEOUT` je Job-Art** — die Konstante sagt heute selbst voraus, dass diese Phase sie anfasst (`QueueMapper.php:36-50`):

```php
	 * Fifteen minutes, and this number is the whole reason this constant exists.
	 * ... OCR in phase 3 raises this value or splits it per kind of job.
	public const LOCK_TIMEOUT = 900;
```

Aus einer Konstante wird eine Abbildung `kind -> Sekunden`; `lockCutoff()` (`QueueMapper.php:387-391`) bekommt den Wert als Argument statt aus der Konstante.

**Bandweises Schreiben** (`QueueMapper.php:52-57, 272-298`) — `requeueAs()` verarbeitet seine ID-Liste in denselben `DELETE_BAND`-Bändern und setzt dabei `retries = 0` zurück (Pitfall 11).

---

### `php/lib/Service/QueueService.php` (MOD: `describe()` je Job-Art)

**Analog:** die Datei selbst, `describe()` (`QueueService.php:194-246`). Die heutige Fassung ist genau die Stelle, an der Löschungen still verschwinden (Pitfall 3), und die zwei Felder `userIds`/`fetchAs` sind der Kommentar, der beim Umbau erhalten bleiben muss:

```php
	private function describe(QueueFile $row): ?array {
		$fileId = $row->getFileId();

		$userIds = $this->usersFor($fileId);
		if ($userIds === []) {
			return null;
		}

		// Two different questions, and therefore two fields. userIds is the
		// access payload ... fetchAs is the single user in whose context the bytes are
		// read. ... collapsing them into one field is how a
		// prefilter silently turns into a permission model.
		$fetchAs = $userIds[0];
		...
		return [
			'fileId' => $fileId,
			'storageId' => $row->getStorageId(),
			...
			'etag' => $node->getEtag(),
			'userIds' => $userIds,
			'fetchAs' => $fetchAs,
			'isUpdate' => $row->getIsUpdate(),
		];
	}
```

Der `etag`-Eintrag trägt bereits den Kommentar "so that the reconcile of phase 3 does not have to change the shape of this object" (`QueueService.php:238-241`) — die Form bleibt also, es kommt `kind` dazu und je Art ein früher Rückgabezweig VOR `usersFor()`.

**Claim-Schleife mit Give-up-Regel** (`QueueService.php:59-93`) — der Rahmen, in den die Reihenfolge acl -> delete -> metadata -> content -> ocr als äussere Schleife eingezogen wird:

```php
		foreach ($this->queueMapper->claimBatch($limit, $maxBytes) as $row) {
			if ($row->getRetries() > self::MAX_ATTEMPTS) {
				$this->finish($row, 'failed', 'repeatedly_stuck');
				$givenUp++;
				continue;
			}

			$source = $this->describe($row);
			if ($source === null) {
				$this->finish($row, 'skipped', 'gone');
				$gone++;
				continue;
			}

			$sources[$row->getId()] = $source;
		}
```

**Transaktion um die Quittung** (`QueueService.php:143-163`) — unverändert das Muster für jeden neuen Mehrfachschreiber:

```php
		$this->db->beginTransaction();
		try {
			...
			$acknowledged = $this->queueMapper->acknowledge($allIds);
			$this->db->commit();
		} catch (\Throwable $e) {
			$this->db->rollBack();
			throw $e;
		}
```

---

### `php/lib/Migration/Version001000Date2026MMDD000000.php` (NEU)

**Analog:** `php/lib/Migration/Version001000Date20260901000000.php` — vollständig, inklusive der Warnung zum Dateinamen.

**Namensregel** (`Version001000Date20260901000000.php:39-43`):

```php
 * The class name and the file name have to be identical to the character.
 * Nextcloud loads migrations by file name and instantiates the class of the
 * same name; a mismatch means the migration is silently never executed, with no
 * error anywhere.
```

**Geschützte Schemaänderung, Rückgabe nur bei Änderung** (`Version001000Date20260901000000.php:50-91`):

```php
	public function changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper {
		/** @var ISchemaWrapper $schema */
		$schema = $schemaClosure();
		if (!$schema->hasTable('findling_queue')) {
			return null;
		}

		$table = $schema->getTable('findling_queue');
		$changed = false;

		if (!$table->hasColumn('dirty')) {
			$table->addColumn('dirty', Types::BOOLEAN, ['notnull' => true, 'default' => false]);
			$changed = true;
		}
		...
		return $changed ? $schema : null;
	}
```

Für `kind`: `Types::STRING`, `['notnull' => true, 'default' => 'content', 'length' => 16]`, dazu ein Index, der zur neuen Claim-Abfrage passt (Muster `findling_q_free` auf `['locked_at','id']`, hier also `['kind','locked_at','id']`).

**Datenumschrift im `postSchemaChange`** (`Version001000Date20260901000000.php:93-104`) — falls Altzeilen umgeschrieben werden müssen:

```php
	public function postSchemaChange(IOutput $output, Closure $schemaClosure, array $options): void {
		$qb = $this->db->getQueryBuilder();
		$qb->update('findling_queue')
			->set('locked_at', $qb->createNamedParameter(new \DateTime('@0'), IQueryBuilder::PARAM_DATE))
			->where($qb->expr()->isNull('locked_at'));
		$qb->executeStatement();
	}
```

---

### `php/lib/Service/FileStateService.php` und `StorageService.php` (MOD)

**Reason-Liste** (`FileStateService.php:46-72`) — die drei neuen Codes `image_not_ocrable`, `ocr_failed`, `ocr_unavailable` werden in denselben kommentierten Blöcken einsortiert:

```php
	public const REASONS = [
		// indexed
		'truncated',
		// skipped
		'too_large',
		...
		'no_text_layer',
		...
		// failed
		'empty_file',
		...
	];
```

**Mimetype-Allowlist mit Begründung** (`StorageService.php:53-78`) — die Bildtypen kommen hier dazu, und der Kommentar muss die Entscheidung gegen HEIC/BMP/GIF tragen:

```php
	public const ALLOWED_MIMETYPES = [
		'application/pdf',
		...
		'application/rtf',
		'text/rtf',
	];
```

**Slice-Abfrage** (`StorageService.php:110-140`) — `getFilesInMount()` liefert bereits genau die Seite, die `GET /files/slice` braucht; die Reconcile-Route ruft dieselbe Methode statt einer eigenen:

```php
	public function getFilesInMount(int $storageId, int $overriddenRoot, int $lastFileId, int $batchSize): iterable {
		return $this->fileAccess->getByAncestorInStorage(
			$storageId,
			$overriddenRoot,
			$lastFileId,
			$batchSize,
			$this->getAllowedMimeIds(),
			false,
			true,
		);
	}
```

Der Kommentar zu den beiden Booleans (E2E-verschlüsselt nein, serverseitig verschlüsselt ja) bleibt gültig und ist beim Kopieren mitzunehmen.

---

### `backend/src/findling/extract/ocr.py` (NEU: extractor, transform + Subprozess)

**Analog:** `backend/src/findling/extract/pdf.py` (Struktur, Verdikt-Rückgabe, C-Ressourcen), plus `sandbox.py` für die Subprozess-Disziplin.

**Modul-Docstring, der die Entscheidungen trägt** (`pdf.py:1-26`) — dieselbe Form: was wird in welcher Reihenfolge gefragt, warum, und der Nur-Lesen-Satz am Ende:

```python
"""PDF text, with the encryption question answered before pdfium opens anything.
...
Like every module of this package, this one never writes: it opens documents for
reading, and the original file is not touched even on the error path (IDX-07).
"""
```

**Verdikte statt Exceptions, Reason aus der geschlossenen Liste** (`pdf.py:62-109`):

```python
def extract_pdf(path: str) -> ExtractionOutcome:
    """The text of a PDF, or the verdict that says why there is none.

    Defined at module level so it can be pickled into the extraction child; a
    closure or a method would not survive the process boundary of plan 02-05.
    """
    ...
    if protected:
        return ExtractionOutcome.skipped(Reason.ENCRYPTED)

    cap = config.settings().max_pdf_pages
    ...
    if len(text.strip()) < _MIN_CHARS_PER_PAGE * max(read_pages, 1):
        # Deliberately not failed and not empty_text. This is the OCR queue.
        return ExtractionOutcome.skipped(Reason.NO_TEXT_LAYER)

    outcome = cap_text(text)
    if page_count > cap:
        # The page cap cut the document just as the character cap would have, so
        # it produces the same visible state instead of a quiet half document.
        return ExtractionOutcome.indexed(outcome.text, truncated=True)
    return outcome
```

Die letzten vier Zeilen sind das Muster für D-08: Deckel gerissen -> `indexed(..., truncated=True)`, nicht `skipped`.

**Der Deckel als kommentierte Zahl mit Messung** (`pdf.py:38-59`) — jeder neue OCR-Deckel bekommt genau so einen Block, inklusive der Angabe, woran gemessen wurde:

```python
# Assumption A2 of the phase research, and the softest number here.
#
# The research proposes "under 100 characters in the whole document". That number
# cannot be used as written: the reference corpus file with a real text layer
# carries 63 characters, ...
_MIN_CHARS_PER_PAGE = 25
```

Diese Zahl selbst ist in dieser Phase neu zu messen; der Kommentar fordert es ausdrücklich ein ("Phase 3 adjusts this number with measurements against real documents").

**Subprozess mit Deadline im Kind:** kein Repo-Analog für `subprocess.run`, aber die begründende Stelle steht in `sandbox.py:1-14` (warum `signal.alarm` und `concurrent.futures` hier nicht gehen) und in `sandbox.py:91-107`:

```python
def _kill_child_tree(process: SpawnProcess) -> None:
    """Kill the child together with everything it may have spawned.

    The child made itself a session leader, so its process group id is its own
    pid and the group kill reaches a hung grandchild too.
    """
```

Das ist der bereits gebaute Halt für den tesseract-Enkel; `ocr.py` darf ihn nicht umgehen (kein Bibliotheks-Binding).

---

### `backend/src/findling/extract/raster.py` (NEU: utility, transform)

**Analog:** `pdf.py::_page_text` (`pdf.py:112-126`) — das verschachtelte `finally` ist das Muster für jede pdfium-Ressource, und die Rasterung fügt nur `bitmap` als dritte Ebene hinzu:

```python
def _page_text(document: pypdfium2.PdfDocument, number: int) -> str:
    """One page of text, with both C objects released even when the page raises.

    The nesting is the point: whatever happens inside, the text page is closed
    before the page and the page is closed before the caller sees the exception.
    """
    page = document[number]
    try:
        textpage = page.get_textpage()
        try:
            return textpage.get_text_bounded()
        finally:
            textpage.close()
    finally:
        page.close()
```

Die Begründung dafür steht in `pdf.py:11-15`: "over an initial index of 100000 files inside a container with 4 GB of RAM it is a leak that ends the process, and the error path is exactly where closing gets forgotten."

**Dokument öffnen mit Fehlerübersetzung** (`pdf.py:84-97`):

```python
    try:
        document = pypdfium2.PdfDocument(path)
    except pypdfium2.PdfiumError:
        return ExtractionOutcome.failed(Reason.CORRUPT)

    try:
        page_count = len(document)
        read_pages = min(page_count, cap)
        parts = [_page_text(document, number) for number in range(read_pages)]
    except pypdfium2.PdfiumError:
        return ExtractionOutcome.failed(Reason.CORRUPT)
    finally:
        document.close()
```

---

### `backend/src/findling/extract/dispatch.py` (MOD: `Route.OCR`, Bildtypen)

**Analog:** die Datei selbst.

**Route-Enum und Allowlist** (`dispatch.py:44-74`):

```python
class Route(StrEnum):
    """The extractor a file is handed to once it passed the allowlist."""

    PDF = "pdf"
    DOCX = "docx"
    ...

ALLOWED_MIMETYPES: Final[Mapping[str, Route]] = {
    "application/pdf": Route.PDF,
    ...
    "text/csv": Route.PLAIN,
}
```

Der Modul-Docstring sagt heute noch "Pictures need OCR to mean anything. Phase 3 adds that path, and until then a picture is honestly reported as unsupported" (`dispatch.py:15-17`) — dieser Absatz wird in derselben Änderung umgeschrieben, sonst lügt er.

**Reihenfolge der Urteile ist Bedeutung, nicht Geschmack** (`dispatch.py:77-92`) — die Bild-Plausibilitätsprüfung aus D-05 reiht sich hier ein, nicht im Extraktor:

```python
def judge(mime: str, size: int) -> Route | ExtractionOutcome:
    """Decide before the first byte: a route to follow, or a finished verdict.

    The order is meaning, not taste. The type comes first because it says what a
    file is, ... Emptiness comes before the size cap because a
    zero byte file is a failure and not a decision.
    """
```

**Lazy import je Route** (`dispatch.py:139-167`) — der OCR-Zweig importiert `ocr`/`raster` erst im `case`, aus demselben Grund (Recycling alle 200 Dateien):

```python
    match route:
        case Route.PDF:
            from findling.extract import pdf

            return pdf.extract_pdf(path)
```

**Doppelte Allowlist:** `dispatch.py:24-26` benennt die Doppelung mit `StorageService::ALLOWED_MIMETYPES` ausdrücklich als gewollt ("this is the line that still holds on the day somebody raises the cap on one side only"). Pitfall 13 verlangt zusätzlich ein CI-Gate, das beide Listen vergleicht.

---

### `backend/src/findling/extract/errors.py` (MOD: 3 neue Reasons)

**Analog:** die Datei selbst. Drei Stellen ändern sich in einer Änderung, plus die PHP-Liste.

**Enum-Blöcke nach State sortiert** (`errors.py:46-75`):

```python
class Reason(StrEnum):
    # indexed
    TRUNCATED = "truncated"

    # skipped, the deliberate decisions
    TOO_LARGE = "too_large"
    ...
    NO_TEXT_LAYER = "no_text_layer"
    ...
    # failed, the things we wanted to do and could not
    EMPTY_FILE = "empty_file"
    ...
```

**Die geschlossene Paar-Tabelle** (`errors.py:78-105`) — wortgleich in `store/repo.py:94-119` zu spiegeln:

```python
STATE_REASONS: Final[Mapping[State, frozenset[Reason | None]]] = {
    State.INDEXED: frozenset({None, Reason.TRUNCATED}),
    State.SKIPPED: frozenset(
        {
            Reason.TOO_LARGE,
            ...
            Reason.NO_TEXT_LAYER,  # the bridge to phase 3: these are the OCR candidates
            ...
        }
    ),
```

Der Kommentar `# the bridge to phase 3` steht an beiden Stellen und wird in dieser Phase zur Beschreibung des tatsächlichen Übergangs.

**Ausnahme-Tabelle mit voll qualifizierten Klassennamen** (`errors.py:108-130`) — falls Pillow-Ausnahmen (`PIL.Image.DecompressionBombError`) aufgenommen werden, gehören sie hierher, mit dem Kommentar-Muster darüber:

```python
_EXCEPTION_REASONS: Final[Mapping[str, Reason]] = {
    "builtins.MemoryError": Reason.OUT_OF_MEMORY,
    "zipfile.BadZipFile": Reason.CORRUPT,
    ...
}
```

Warnung aus demselben Block (`errors.py:117-122`): ein Eintrag, dessen Reason nicht zu `failed` gehört, wirft im Fehlerhandler eine `ValueError`. `image_not_ocrable` ist `skipped` und darf daher NICHT in diese Tabelle.

---

### `backend/src/findling/extract/sandbox.py` (MOD: Timeout je Job)

**Analog:** die Datei selbst.

**Heute Timeout je Worker** (`sandbox.py:196-206`) — genau die Signatur, die für zwei Deadlines aufgebrochen werden muss:

```python
    def __init__(self, *, max_files: int | None = None, timeout_seconds: float | None = None) -> None:
        resolved = config.settings()
        self._max_files = resolved.extract_worker_max_files if max_files is None else max_files
        self._timeout_seconds = (
            float(resolved.extract_timeout_seconds) if timeout_seconds is None else float(timeout_seconds)
        )
```

**Die Stelle, die den Wert benutzt** (`sandbox.py:242-271`) — `_ask` bekommt den Timeout als Argument; die drei Recycling-Regel-Kommentare bleiben unverändert:

```python
    def _ask(self, job: tuple[object, ...]) -> object:
        """Send one job, wait for the answer with a deadline, judge what comes back."""
        ...
        if not pipe.poll(self._timeout_seconds):
            # Recycling rule 2: over the deadline. Only a kill ends a hung C
            # extension, and after it the process is gone by definition.
            _kill_child_tree(process)
            process.join(_JOIN_GRACE_SECONDS)
            self._recycle()
            return ExtractionOutcome.failed(Reason.TIMEOUT)
```

**Die Vorbereitung für tesseract steht schon da** (`sandbox.py:156-163`) — nichts daran ändern, nur nutzen:

```python
    if sys.platform != "win32":
        # Its own session, so a kill can take the whole process group with it.
        # Today the child spawns nothing; phase 3 runs tesseract, and a hung
        # grandchild that survives the kill would hold the worker slot forever
        # (security audit L3).
        os.setsid()
    _shed_secrets()
    _limit_address_space(address_space_bytes)
```

**Fassade mit einem Worker je Prozess** (`sandbox.py:317-330`) — falls eine `ocr_guarded()`-Fassade dazukommt, teilt sie sich denselben `_WORKER`, sonst verdoppelt sich der Speicher-Peak:

```python
_WORKER: ExtractionWorker | None = None


def extract_guarded(path: str, mime: str, size: int) -> ExtractionOutcome:
    ...
    global _WORKER
    if _WORKER is None:
        _WORKER = ExtractionWorker()
    return _WORKER.run(path, mime, size)
```

---

### `backend/src/findling/index/writer.py` (MOD: `stored_body()`, `drop_document()`)

**Analog:** `IndexBatchWriter.add` (`writer.py:176-210`) — die Löschung per `Query.term_query` ist genau der Mechanismus, den D-10 braucht:

```python
    def add(self, record: IndexRecord) -> None:
        """Write one file into the pending batch, replacing an earlier version.
        ...
        """
        writer = self._require_open()
        # Through the schema, so the term carries the type of the field. The
        # deletion by term name takes the value as it comes and builds an I64
        # term, which never matches the U64 key and deletes nothing at all; see
        # the module docstring for the measurement. Deletes apply to documents
        # with a lower opstamp only, so the insert right below survives this.
        writer.delete_documents_by_query(Query.term_query(self._schema, FIELD_FILE_ID, record.file_id))
```

**Der I64/U64-Gotcha im Modul-Docstring** (`writer.py:34-48`) — vor dem Bau des Löschpfads zu lesen, sonst löscht `drop_document` still nichts:

```
    file_id as unsigned, delete by term  -> 2 documents after the second write
    file_id as integer,  delete by term  -> 1 document
    file_id as unsigned, delete by query -> 1 document
```

**Namensverbot:** die Methode darf nicht `delete`, `move`, `copy` oder `trash` heissen — Gate A prüft diese Bezeichner in jedem Modul (`backend/tests/test_readonly_gate.py:62-74`). `drop_document`, `forget`, `purge` sind frei.

**`body_de` ist die einzige gespeicherte Textkopie** (`writer.py:199-205`) — das ist die Grundlage für den Metadaten-Job ohne Download:

```python
        # body_de is the only stored copy of the text in the whole system, so it
        # carries the content whatever the language setting says. The setting
        # decides about the second, index only pipeline: with FINDLING_LANGUAGES
        # set to de the English field stays empty and the index shrinks by it.
        document.add_text(FIELD_BODY_DE, record.body)
```

**Der Datensatz, der neu gebaut wird** (`writer.py:85-102` und `poller.py:655-666`):

```python
def _record_of(job: QueueJob, outcome: ExtractionOutcome) -> IndexRecord:
    """The document as the index takes it."""
    return IndexRecord(
        file_id=job.file_id,
        storage_id=job.storage_id,
        name=job.title,
        title=job.title,
        path=job.path,
        ext=extension_of(job.title),
        body=outcome.text,
        mtime=job.mtime,
    )
```

Der Metadaten-Job baut denselben Record, nur mit `body=stored_body(file_id)`.

---

### `backend/src/findling/store/repo.py` (MOD: etag, tombstone, `gone_in_range`, Cursor)

**Analog:** die Datei selbst.

**SQL als benannte Konstante mit Begründungskommentar** (`repo.py:122-163`):

```python
# One upsert for both cases. A second attempt on the same file overwrites the
# verdict and the metadata, because the crawl may have handed over a moved or
# renamed file, and raises attempts, which is the only counter that must survive
# the overwrite.
_RECORD_SQL: Final = """
INSERT INTO files (file_id, storage_id, root_id, path, title, mime, size, mtime,
                   content_hash, text_chars, state, reason, attempts, indexed_at, index_version)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
ON CONFLICT(file_id) DO UPDATE SET
    ...
"""
```

Jedes neue SQL (`_GONE_IN_RANGE_SQL`, `_TOMBSTONE_SQL`) folgt dieser Form: Modulkonstante, `Final`, Kommentar darüber.

**Die Tombstone-Vorbereitung existiert bereits** (`repo.py:147-153`):

```python
# deleted_at is NULL throughout phase 2. The condition is here so that the phase 3
# tombstone cannot make a deleted file look unchanged and therefore untouchable.
_IS_UNCHANGED_SQL: Final = """
SELECT 1 FROM files
 WHERE file_id = ? AND content_hash = ? AND state = 'indexed'
   AND index_version = ? AND deleted_at IS NULL
"""
```

Ebenso das Schema: `etag`, `ocr_used`, `deleted_at` stehen schon in `backend/src/findling/store/schema.sql` mit dem Kommentar "phase 3 fills it" / "phase 3 tombstone, stays NULL". **Es ist keine Spaltenmigration nötig**, nur Schreiben.

**Validierung vor der Transaktion** (`repo.py:315-363`):

```python
        allowed = STATE_REASONS.get(state)
        if allowed is None:
            raise ValueError(f"unknown state {state!r}, expected one of {sorted(STATE_REASONS)}")
        if reason not in allowed:
            raise ValueError(f"reason {reason!r} does not belong to state {state!r}")

        with self._transaction():
            self._conn.execute(_RECORD_SQL, (...))
```

**Explizite Transaktion** (`repo.py:304-313`):

```python
    @contextmanager
    def _transaction(self) -> Iterator[None]:
        """One explicit transaction. Validation belongs before it, never inside."""
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self._conn.execute("ROLLBACK")
            raise
        self._conn.execute("COMMIT")
```

**ACL-Räumung, deklarativ statt inkrementell** (`repo.py:439-451, 490-499`) — der Unshare-Pfad aus D-04 ruft `replace_acl(file_id, [])`, der Löschpfad `forget_acl`:

```python
    def replace_acl(self, file_id: int, uids: Iterable[str]) -> None:
        """Write the permissions of one file as a whole, never as a change.

        DELETE followed by INSERT in one transaction. The crawl and the events
        both transport the target state, so a delivery that gets lost costs one
        round of staleness and repairs itself with the next one.
        """
        rows = [(uid, file_id) for uid in dict.fromkeys(uids)]
        with self._transaction():
            self._conn.execute("DELETE FROM acl WHERE file_id = ?", (file_id,))
            self._conn.executemany("INSERT INTO acl (uid, file_id) VALUES (?, ?)", rows)
```

**Bandweise IN-Abfragen mit `# noqa: S608`-Muster** (`repo.py:471-488`) — für die `present`-Menge des Abgleichs:

```python
        for start in range(0, len(file_ids), _ACL_BAND):
            band = file_ids[start : start + _ACL_BAND]
            placeholders = ",".join("?" * len(band))
            rows = self._conn.execute(
                # The parameters are placeholders, all of them. Only their number
                # is interpolated, and it is a count this function computed.
                f"SELECT file_id FROM acl WHERE uid = ? AND file_id IN ({placeholders})",  # noqa: S608
                (uid, *band),
            )
```

**Mirror-Muster für den Abgleich-Cursor** (`repo.py:429-437`) — `record_mount` ist die Vorlage; für den Reconcile-Cursor gilt der umgekehrte Satz (der Container besitzt ihn), und der gehört ausdrücklich in den Docstring:

```python
    def record_mount(self, storage_id: int, root_id: int, cursor: int, files_seen: int) -> None:
        """Mirror the crawl progress of one mount for the status display.

        A mirror and nothing more. The original of the cursor is the last file id
        in the argument of the next crawl job in Nextcloud, so losing this table
        loses a number on a page and not a single document.
        """
```

---

### `backend/src/findling/worker/poller.py` (MOD: Dispatch nach Job-Art)

**Analog:** die Datei selbst.

**Die vier Schritte einer Runde, mit den Kommentaren, die die Reihenfolge begründen** (`poller.py:355-425`) — der `kind`-Dispatch kommt in Schritt 1, die Schritte 2 bis 4 bleiben:

```python
        # 1. Per file: judge, read the bytes into scratch, extract, hand over to
        #    the writer. An abort anywhere in here costs nothing: the rows are
        #    still locked in Nextcloud and run in again after the lock timeout.
        for job in claim.jobs:
            try:
                counted = await self._handle(job, done, failed, verdicts)
            except _GatewayDown:
                return await self._abort(queue, len(claim.jobs))
            unchanged += counted

        # 2. The commit. From here the index is durable, and this is the earliest
        #    moment at which a verdict may be written down.
        flush = await asyncio.to_thread(self._writer_or_die().flush)
        ...
        # 3. The verdicts and the permissions, per file replace_acl then record().
        await asyncio.to_thread(self._record_verdicts, verdicts)

        # 4. The acknowledgement, the last step by construction.
        ack = await queue.acknowledge(done, failed)
```

**`_handle` als Verzweigungspunkt** (`poller.py:429-474`) — `acl`/`delete` verlassen vor `_fetch_file`, `metadata` vor `is_unchanged`, `ocr` nach der Textlayer-Prüfung:

```python
    async def _handle(self, job, done, failed, verdicts) -> int:
        """Take one job as far as the writer. Returns 1 when it needed no work."""
        route = judge(job.mime, job.size)
        if isinstance(route, ExtractionOutcome):
            # Decided before the first byte. ...
            self._collect(job, route, done, failed, verdicts)
            return 0
        ...
        try:
            if await asyncio.to_thread(self._store_or_die().is_unchanged, job.file_id, read.content_hash):
                done.append(job.queue_id)
                return 1
            outcome = await asyncio.to_thread(self._extract, str(read.path), job.mime, read.size)
        finally:
            # The scratch file holds user content. Leaving one behind is a
            # disclosure, and leaving one behind per job fills the volume.
            _discard(read.path)
```

Die Zeile `is_unchanged` ist Pitfall 2: ein Rename als `content`-Job läuft genau hier ins Leere.

**Jeder blockierende Aufruf über `asyncio.to_thread`** (durchgängig, z. B. `poller.py:387, 397, 462, 465, 508`) — die ruff-Gruppe ASYNC ist im Poller scharf. Auch das Öffnen der Scratch-Datei geht durch einen Thread (`poller.py:501-520`), was der Perf-Punkt M1 dieser Phase weiterführt:

```python
        handle = await asyncio.to_thread(scratch.open, "wb")
```

**Verdikte einsortieren** (`poller.py:522-542`) — `_collect` bleibt die einzige Stelle, die entscheidet, ob eine Zeile in `done` oder `failed` landet:

```python
        verdicts.append(_Verdict(job=job, outcome=outcome, content_hash=content_hash))
        if outcome.state is State.FAILED and outcome.reason is not None:
            failed[job.queue_id] = str(outcome.reason)
            return
        done.append(job.queue_id)
```

**Rechte vor Verdikt** (`poller.py:544-569`) — die Reihenfolge ist begründet und gilt auch für ACL-Jobs; Pitfall 4 verlangt zusätzlich, dass ein reiner ACL-Job NICHT über `store.record()` läuft (sonst zählt `attempts` hoch und das Verdikt wird überschrieben).

**Abbruch ohne Verdikt** (`poller.py:594-611`) — Muster für jeden neuen Fehlerzweig des Abgleichs:

```python
    async def _abort(self, queue, claimed, *, state=ROUND_GATEWAY_UNAVAILABLE) -> RoundResult:
        """End the pass without a commit, a verdict or an acknowledgement.
        ...
        """
        await queue.unlock(sorted(self._held))
        self._held.clear()
        self._back_off()
        return RoundResult(state, claimed=claimed)
```

**Backoff** (`poller.py:623-629`) — der Abgleich-Worker bekommt dieselbe Verdopplungslogik:

```python
    def _back_off(self) -> None:
        """Grow the pause: from the configured start, doubling up to the cap."""
        self._cooldown = min(self._cooldown * 2, self._cooldown_max) if self._cooldown else self._cooldown_start
```

**Ausnahmen fangen und nur den Typnamen loggen** (`poller.py:343-352`):

```python
            except Exception as error:
                # The type name and nothing else. A traceback here would carry
                # whatever a library put into its message, and the extraction
                # path is full of libraries that put a file name there.
                LOGGER.error("indexing pass ended in an unexpected %s", type(error).__name__)
                self._back_off()
```

---

### `backend/src/findling/worker/reconcile.py` (NEU: worker, batch/pull)

**Analog:** `poller.py` (Struktur: Klasse mit lazy geöffneten Ressourcen, `run(stop_event)` plus `run_once()`, `RoundResult`-Dataclass, Backoff, `_open()`).

**Lazy-Öffnen der Ressourcen** (`poller.py:573-592`) — der Abgleich teilt sich Store und Client, öffnet aber keinen zweiten Index-Writer (tantivy-Lock!):

```python
    def _open(self) -> DocumentQueue:
        """Build the client, the connection pool and the resources exactly once.

        One client for the whole run. A client per file would pay a connection
        setup per file and, on the PHP side, a Nextcloud bootstrap including the
        signature check; ...
        """
        if self._queue is not None:
            return self._queue
        ...
```

Warnung aus `writer.py:1-7`: es existiert genau ein `IndexWriter` im Prozess. Der Abgleich muss den des Pollers benutzen oder seine Löschungen über die Queue laufen lassen.

**Nichts im Konstruktor öffnen** (`poller.py:632-639`):

```python
def default_poller() -> Poller:
    """The poller of the running container; its resources open on the first pass.

    Nothing is opened here. The lifespan builds this object while the backend may
    still be disabled, and a container that opened the index writer at that point
    would hold the tantivy lock without ever indexing anything.
    """
    return Poller()
```

**Ruhe-Gate (D-03):** die Zahlen kommen aus `queue.stats()` (`nc/queue.py:290-303`), die den `scheduled`-Wert bereits liefert.

---

### `backend/src/findling/nc/files.py` (NEU) und `nc/queue.py` (MOD)

**Analog:** `backend/src/findling/nc/queue.py` — vollständig. Der Modul-Docstring nennt die drei Regeln, die für jede neue Client-Schale gelten (`nc/queue.py:1-32`):

```
**It builds jobs out of source objects and refuses the ones it cannot use.**
**It turns transport failures into results.**
**It creates no client, ever.**
```

und den Satz, der die Datei-Trennung begründet: "invariant 1 of the read-only gate allows both in ``nc/client.py`` alone" — `nc/files.py` darf also weder `httpx` noch `nc_py_api` importieren.

**Feldweise Validierung mit Typprüfern** (`nc/queue.py:118-208`):

```python
def _positive_int(value: object) -> int | None:
    """A positive whole number, or None. Accepts the string form OCS may deliver.

    ``bool`` is rejected explicitly: it is a subclass of ``int`` in Python, and
    ``True`` would otherwise pass as the queue row id 1.
    """
```

```python
def _job(queue_id_raw: object, source: object) -> QueueJob | None:
    ...
    if file_id is None or size is None or not mime or not user_ids or not fetch_as:
        return None
```

Diese eine Zeile ist Pitfall 3 und 4: für `kind=delete` und `kind=acl` darf sie nicht mehr pauschal verwerfen. Die Änderung ist minimal, die Begründung gehört als Kommentar daneben.

**Jede Transportstörung wird ein Wert, nie eine Ausnahme** (`nc/queue.py:217-249`):

```python
        try:
            answer = await claim_documents(self._nc, limit=limit, max_bytes=max_bytes)
        except Exception:
            # Deliberately every exception. The Nextcloud library raises its own
            # type for an OCS verdict, the HTTP client underneath raises several
            # more for a connection that never happened, and this module may
            # import neither of them to name their classes.
            LOGGER.warning("could not take a batch from the queue, backing off")
            return ClaimResult(unavailable=True)
```

**Verworfene Einträge nur zählen, nie ausgeben** (`nc/queue.py:245-249`):

```python
        if discarded:
            # A count and nothing else. The entry that was refused is exactly the
            # kind of value a file name arrives in (T-02-107).
            LOGGER.warning("discarded %d unusable queue entries", discarded)
```

**Neue OCS-Aufrufe in `nc/client.py`** (`nc/client.py:293-361`) — Pfad als Stringliteral am Aufrufort, nicht als Konstante (das Gate liest ihn als `ast.Constant`):

```python
async def unlock_documents(nc: AsyncNextcloudApp, *, ids: Sequence[int]) -> object:
    """Hand rows back unprocessed, the graceful half of a shutdown.
    ...
    """
    return await nc._session.ocs(
        "POST",
        "/ocs/v2.php/apps/findling/queues/documents/unlock",
        json={"ids": list(ids)},
    )
```

Der Kommentarblock darüber (`nc/client.py:~305-325`) sagt es ausdrücklich: "The path is a string literal inside the call, and it has to stay one. ... Lifting these four paths into module constants would look tidier and would leave the gate with 'an unknown path'."

---

### `backend/src/findling/config.py` (MOD: `FINDLING_OCR_*`)

**Analog:** die Datei selbst.

**Konstante mit Messung im Kommentar** (`config.py:100-127`) — jeder neue OCR-Deckel wird so geschrieben:

```python
# Wall clock budget of one extraction, enforced by Process.join(timeout) followed
# by kill(). Only kill() reliably ends a hung C extension.
EXTRACT_TIMEOUT_SECONDS = 120

# 512 MB address space for the extraction child, via RLIMIT_AS. Measured: 300 MB
# already produces MemoryError inside the child, so this leaves headroom while
# still bounding a runaway document.
EXTRACT_ADDRESS_SPACE_BYTES = 536_870_912
```

**Fehlerhafte Umgebung degradiert auf den Default, wirft nie** (`config.py:229-247`):

```python
def _int_from_environment(name: str, default: int) -> int:
    """Read a positive whole number, falling back to the measured default.

    Every failure path is the same: warn with the name of the variable and use
    the default. Raising here would turn one wrong character in an admin form
    into a container that will not start, on a machine with no operator watching.
    """
```

**Allowlist-Prüfung für Textwerte** (`config.py:264-287`) — genau das Muster für `FINDLING_OCR_LANGUAGES` (Pitfall 7):

```python
def _languages() -> tuple[str, ...]:
    """Return the active language fields, in schema order.

    An empty or unrecognisable list keeps both fields. ...
    """
    requested = {part.strip().lower() for part in os.environ.get("FINDLING_LANGUAGES", "").split(",")}
    kept = tuple(language for language in DEFAULT_LANGUAGES if language in requested)
    if kept:
        return kept
    if requested - {""}:
        LOGGER.warning("FINDLING_LANGUAGES names no supported language, falling back to the built in default")
    return DEFAULT_LANGUAGES
```

**Eingefrorene Settings** (`config.py:193-227`) — jedes neue Feld kommt in die `Settings`-Dataclass und in `settings()`; die Dataclass ist `frozen=True, slots=True`.

**Jede neue Variable auch in `backend/appinfo/info.xml`** (Zeilen 123-141), im Muster:

```xml
			<variable>
				<name>FINDLING_LANGUAGES</name>
				<display-name>Index languages</display-name>
				<description>Comma separated, currently de and en. ...</description>
				<default>de,en</default>
			</variable>
```

---

### `backend/Dockerfile` (MOD: tesseract)

**Analog:** der `wngerman`-Block (`backend/Dockerfile:92-110`) — Version pinnen, apt-Listen löschen, Existenz der Daten UND der Lizenz fail-closed prüfen, Lizenz an einen stabilen Ort kopieren:

```dockerfile
# GPL-2+ obligation: the licence text has to travel with the image, not only with
# the repository, because the image is what is distributed. slim images drop most
# of /usr/share/doc (path-exclude in /etc/dpkg/dpkg.cfg.d), so the file is copied
# to a stable place of ours. Both tests below are the fail closed half: an image
# without the data or without its licence must not be built at all. THIRD-PARTY.md
# carries the same statement for readers of the repository.
RUN apt-get update \
    && apt-get install -y --no-install-recommends wngerman=20161207-15 \
    && rm -rf /var/lib/apt/lists/* \
    && test -s /usr/share/dict/ngerman \
    && test -s /usr/share/doc/wngerman/copyright \
    && install -D -m 0444 /usr/share/doc/wngerman/copyright \
        /usr/local/share/findling/COPYING.wngerman
```

Abweichung, die der Plan festhalten muss: `tesseract-ocr` ist architekturabhängig (`5.5.0-1` amd64, `5.5.0-1+b1` arm64), ein harter Pin bricht den arm64-Bau. Die Sprachpakete (`Architecture: all`) dürfen hart gepinnt werden. Zusätzliche fail-closed-Prüfung analog: `tesseract --list-langs` muss `deu` und `eng` zeigen.

---

### `scripts/dev/build_corpus.py` (MOD: DACH-Korpus)

**Analog:** die Datei selbst (`build_corpus.py:1-32`). Zwei Regeln aus dem Docstring gelten weiter, eine bricht:

```python
"""Rebuild the reference corpus under testdata/corpus from scratch.

The corpus is committed as binary test data, but it is not hand made: every file
comes out of this script, ...
Standard library only, no third party writer, because a corpus that needs a
dependency to exist is a corpus that rots.
...
Two files are broken on purpose. ... the error path is where the predecessor app
(files_fulltextsearch_tesseract) destroyed user data.
...
Real umlauts in the German strings below are deliberate, exactly as in the
office part that has carried them since phase 1: an ASCII spelling would test the
one case that cannot go wrong.
"""
```

**Der Bruch:** gerenderter Text im Bild geht nicht mit der Standardbibliothek. Pitfall 12 verlangt stattdessen `fonts-dejavu-core` in gepinnter Version im selben Basis-Image plus notierten Digest der erzeugten Datei. Das ist eine bewusste Abweichung vom "Standard library only"-Satz und muss dort im Docstring dokumentiert werden, sonst liest es sich wie ein Versehen.

**Zweite Regel, die bleibt** (`build_corpus.py:20-27`): jeder Suchbegriff, den die Integrationsprüfung behauptet, steht in genau einer Korpusdatei. Für D-09 heisst das: "Strasse" nur im Schweizer Dokument, "Jänner" nur im österreichischen.

---

### Tests

**Analog für Extraktor-Tests:** `backend/tests/test_extract_documents.py` (echte Korpusdateien, echte Verdikte).

**Analog für Worker-Tests:** `backend/tests/test_poller.py` (`test_poller.py:1-27`) — echter Index, echte Zustandsdatenbank, Fakes nur für Nextcloud, und der Docstring benennt, was der Test beweist:

```python
"""The one indexing task, against a real index, a real state database and fakes
for everything that would otherwise need a Nextcloud.

The order commit, state, acknowledgement is the subject of this file. It is not a
convention: it is the only arrangement in which every possible moment of an abort
is harmless. ...

The extractor injected here is the real dispatcher, not a stub. It runs in this
process instead of in the guarded child, which keeps the tests fast while the
verdicts, the reasons and the character cap stay the real ones.
"""
```

**Analog für Fixtures:** `backend/tests/conftest.py:1-19` — echtes Volumen, echter AppAPI-Header, keine Attrappen.

---

## Shared Patterns

### 1. Verdikte statt Exceptions über jede Prozess- und Sprachgrenze
**Quelle:** `backend/src/findling/extract/errors.py:133-197`
**Gilt für:** ocr.py, raster.py, image.py, dispatch.py, poller.py, reconcile.py

```python
@dataclass(frozen=True, slots=True)
class ExtractionOutcome:
    """One judged file: a state, its reason, and the text if there is any.

    Frozen because a verdict that can be edited after the fact is a verdict two
    call sites disagree about. Built through the three classmethods rather than
    directly, so that the pair is validated in one place and a caller cannot
    accidentally attach text to a failure.
    """
    ...
    @classmethod
    def indexed(cls, text: str, *, truncated: bool = False) -> ExtractionOutcome: ...
    @classmethod
    def skipped(cls, reason: Reason) -> ExtractionOutcome: ...
    @classmethod
    def failed(cls, reason: Reason) -> ExtractionOutcome: ...
```

### 2. Ein neuer Reason braucht drei (jetzt vier) Orte in derselben Änderung
**Quellen:** `backend/src/findling/extract/errors.py:78-105`, `backend/src/findling/store/repo.py:94-119`, `php/lib/Service/FileStateService.php:52-72`
**Gilt für:** jeden Plan, der ein neues Verdikt einführt (`image_not_ocrable`, `ocr_failed`, `ocr_unavailable`)

Die beiden Python-Listen werden bereits von einem Test verglichen (`errors.py:11-15`):

```
**The same list lives in findling/store/repo.py as STATE_REASONS.** Whoever adds
a pair here has to add it there in the same commit. Two lists that drift apart
break the return channel to Nextcloud silently: this side produces a verdict the
store refuses to write, and the file ends up with no verdict at all.
```

Für die PHP-Liste gibt es kein Gate. Das neue Gate (Python-Test, der die PHP-Konstante per Regex liest) gehört zu Sec-L4 in denselben Plan.

### 3. Kein Log trägt einen Pfad, einen Dateinamen oder eine Bibliotheksmeldung
**Quellen:** `php/lib/BackgroundJobs/StorageCrawlJob.php:26-28`, `php/lib/Service/QueueService.php:24-26`, `backend/src/findling/worker/poller.py:348-351`, `backend/src/findling/nc/queue.py:245-248`
**Gilt für:** alle neuen Dateien, besonders `ocr.py` (tesseract schreibt Dateinamen und inhaltsnahe Warnungen nach stderr; stderr wird eingesammelt und verworfen, nie geloggt)

```python
                LOGGER.error("indexing pass ended in an unexpected %s", type(error).__name__)
```

Ausnahme mit Regel: PHP-Controller loggen `$e->getMessage()` (`QueueController.php:96`) — genau diese Zeilen sind Sec-L6 dieser Phase und werden geprüft.

### 4. Gate A: verbotene Bezeichner und die Schreib-Allowlist
**Quelle:** `backend/tests/test_readonly_gate.py:62-74` und `:173-178`
**Gilt für:** jede neue Python-Datei und jede neue OCS-Schreibroute

```python
FORBIDDEN_IDENTIFIERS = frozenset(
    {
        "set_user",
        "upload",
        "upload_stream",
        "delete",
        "move",
        "copy",
        "mkdir",
        "makedirs",
        "trash",
    }
)
```

```python
OCS_WRITE_ALLOWLIST: frozenset[str] = frozenset(
    {
        "/ocs/v2.php/apps/findling/queues/documents",
        "/ocs/v2.php/apps/findling/queues/documents/unlock",
    }
)
```

Der Requeue-Pfad braucht hier einen dritten Eintrag, und laut Modul-Docstring in eigenem Schritt und eigenem Commit, mit benannter Bedrohung, Aussage über die erreichbaren Tabellen und Negativtest. `GET /files/slice` braucht keinen Eintrag (nur schreibende Methoden werden bewertet).

### 5. ExApp-Vertrauensgrenze in jeder neuen Controller-Methode
**Quelle:** `php/lib/Controller/QueueController.php:216-239`, `php/lib/Controller/GatewayController.php:54-75`
**Gilt für:** `ReconcileController`, `QueueController::requeue()`

Drei Attribute voll qualifiziert plus `rejectForeignCaller()` als erste Anweisung. `ExAppRequired` beantwortet "ist das eine registrierte ExApp", nicht "ist das UNSERE ExApp".

### 6. Fortschritt in der Datenbank, nie im Prozessspeicher
**Quellen:** `php/lib/BackgroundJobs/StorageCrawlJob.php:113-120`, `backend/src/findling/store/repo.py:429-437`
**Gilt für:** `SubtreeExpandJob`, `ReconcileScheduleJob`, `reconcile.py`

```php
				// This assignment is the PHP half of IDX-02. The cursor lives in
				// the job argument and therefore in the Nextcloud database, ...
				// a docker kill in the middle of the first index costs the current
				// slice and nothing else
				$lastFileId = max($lastFileId, $entry->getId());
```

Der Abgleich-Cursor bricht diese Regel bewusst (er liegt in `state.db`); die Begründung "reine, idempotente Reparatur" gehört als Absatz in den Modul-Docstring von `reconcile.py`.

### 7. Idempotenz statt Select-vor-Insert
**Quellen:** `php/lib/Db/QueueMapper.php:83-92`, `php/lib/Service/FileStateService.php:109-116`, `backend/src/findling/store/repo.py:122-145`
**Gilt für:** jeder neue Schreibpfad in beiden Datenbanken

```php
			// insertIgnoreConflict rather than insert-and-catch, and that is a
			// transaction property, not taste: on PostgreSQL a caught constraint
			// violation still aborts the surrounding transaction
```

### 8. Deckel als benannte Konstante mit Messung, nie als Literal in der Abfrage
**Quellen:** `php/lib/Db/QueueMapper.php:36-50`, `php/lib/BackgroundJobs/StorageCrawlJob.php:31-68`, `backend/src/findling/config.py:100-137`, `backend/src/findling/extract/pdf.py:38-59`
**Gilt für:** alle OCR-Deckel (Seiten, Sekunden je Seite, weiche Gesamtdeadline, harte Deadline, Bild-Plausibilität)

```php
	 * It is a named constant because the number standing directly in the query
	 * is the documented warning sign for exactly this defect.
```

### 9. Doppelte Allowlists werden absichtlich doppelt geführt und per Gate verglichen
**Quellen:** `backend/src/findling/extract/dispatch.py:24-26`, `php/lib/Service/StorageService.php:53-78`
**Gilt für:** die Bild-Mimetypes aus D-05

---

## No Analog Found

| Datei | Rolle | Datenfluss | Grund |
|-------|-------|------------|-------|
| `php/lib/Listener/FileEventListener.php` | listener | event-driven | Die App hat heute keinen einzigen `IEventListener`. `Application::register()` registriert nur `registerSearchProvider` (`Application.php:32-34`). Der Planer nutzt RESEARCH Beispiel 1 (verifizierte Klassenliste `OCP\Files\Events\Node\*`, Registrierung in `register()`, nie in `boot()`) als Vorlage und übernimmt aus `StorageCrawlJob` nur den Enqueue-Aufruf und die Log-Regel. |
| `php/lib/Listener/ShareEventListener.php` | listener | event-driven | Dito, zusätzlich `OCP\Share\Events\*`. Kein Vorbild im Repo für die Auflösung `IShare -> fileId`. |
| `backend/src/findling/extract/ocr.py` (Subprozess-Teil) | utility | Subprozess-Aufruf | Es gibt im ganzen Repo keinen `subprocess`-Aufruf. Das Prozess-Management-Vorbild ist `sandbox.py` (multiprocessing, `killpg`, Deadline), aber `subprocess.run(input=..., timeout=..., env=...)` ist neu. RESEARCH Beispiel 4 ist die Vorlage; die Regeln daraus (Argumentliste statt `shell=True`, `OMP_THREAD_LIMIT=1`, stderr einsammeln und verwerfen) sind zwingend. |

Teil-Analoga für die Listener, die der Planer trotzdem heranziehen soll:
- Registrierungsort und der Grund dafür: `php/lib/AppInfo/Application.php:27-34` ("Registering it in boot() fails silently: no error, no entry in the provider list").
- Enqueue-Aufruf: `php/lib/BackgroundJobs/StorageCrawlJob.php:128-132`.
- Verzweigung "Datei sofort, Ordner als Job": `php/lib/BackgroundJobs/SchedulerJob.php:50-61` (planen statt arbeiten).

---

## Metadata

**Analog search scope:** `php/lib/**`, `php/appinfo/**`, `backend/src/findling/**`, `backend/tests/**`, `backend/Dockerfile`, `backend/appinfo/info.xml`, `scripts/dev/**`, `docs/**`, `.github/workflows/**`
**Files scanned:** 18 PHP-Klassen, 37 Python-Module, 24 Testdateien, 5 Workflows (per Verzeichnislisting und Zeilenzählung), davon 21 Dateien vollständig oder in gezielten Abschnitten gelesen
**Projekt-Skills:** keine (`CLAUDE.md` meldet ausdrücklich "No project skills found")
**Pattern extraction date:** 2026-09-01
