# Phase 45: Findling 1.7.0 - Pattern Map

**Mapped:** 2026-11-22
**Files analyzed:** 27 (neu oder geändert)
**Analogs found:** 26 / 27
**Quellen:** 45-CONTEXT.md (D-45-01 bis D-45-16), 45-UI-SPEC.md (approved), REQUIREMENTS.md (KAT-03, KAT-04, EXCL-04 bis EXCL-06, STORE-03, STORE-04, REL-07). Kein RESEARCH.md (bewusst schlank).

Alle Zeilennummern beziehen sich auf den Stand vom 22.11.2026 (vor dem Merge von PR #56 und #57). Nach dem Merge von PR #57 verschieben sich die Zeilen in `php/js/admin.js` leicht.

---

## Die bestehende Ausschluss-Pipeline (Vorlage für EXCL-04)

So fließt heute der Hauptschalter "Index external storage" bis zur Löschung im Index. Der Ausschluss je Speicher muss exakt diese Kette benutzen, nur mit einer zusätzlichen Filterstufe:

| Schritt | Datei:Zeilen | Was passiert |
|---------|--------------|--------------|
| 1. Formular | `php/templates/admin.php:1587-1591` | Checkbox `#findling-rules-external-storage` |
| 2. Script sendet | `php/js/admin.js:1542-1548` | `send(ROUTE_RULES, { ..., indexExternalStorage: checked(...), ... })` |
| 3. Route | `php/lib/Controller/SettingsController.php:359-486` | `saveRules(...)`: validate alles, dann `settingsService->save()`, `exclusionService->save()`, `savePatterns()`; Antwort mit `rules` |
| 4. Speichern | `php/lib/Service/SettingsService.php:849-877` | `setValueBool(KEY_INDEX_EXTERNAL_STORAGE)`, danach `markScanStale()` |
| 5. Mountliste | `php/lib/Service/StorageService.php:283-311` | `providers()` nimmt `EXTERNAL_STORAGE_MOUNT_PROVIDER` nur bei Schalter an; `getMounts()` ist die EINE Mountliste (Gate in `backend/tests/test_exclusion_path_space.py:147-155, 454`) |
| 6. Events | `php/lib/Service/StorageService.php:411-422` | `isIndexedStorage()` liest `getMounts()`, also wirkt ein Filter in `getMounts()` automatisch auf Listener und Crawl |
| 7. Abwahl melden | `php/lib/Service/StorageService.php:461-495, 1140-1185` | `classifyAbsent()` -> `deselected()`: Storage existiert, nur ein abgeschalteter Provider trägt ihn, und `isIndexedStorage()` ist false |
| 8. Python löscht | `backend/src/findling/worker/reconcile.py:986-1012` | `files.gone_storages(absent)`; `deselected` ohne Gnadenfrist -> `_hand_over` Delete-Orders -> `store.forget_storage` (D-36-14) |
| 9. Wiederzulassen | keine Aktion | Storage taucht wieder in `getMounts()` auf, nächster regulärer Abgleich indexiert nach (D-45-05) |

**Folgerung für den Planer:** Python braucht für EXCL-04 keine Änderung (Python kennt nur storage_id, CONTEXT "Established Patterns"). Die Arbeit liegt in PHP: `getMounts()` filtert die storage_ids ausgeschlossener Admin-Mounts heraus, und `deselected()` meldet sie, auch wenn der Hauptschalter AN ist.

---

## File Classification

| Neue/geänderte Datei | Rolle | Data Flow | Closest Analog | Match |
|----------------------|-------|-----------|----------------|-------|
| `php/lib/Service/SettingsService.php` | service (config) | CRUD appconfig | eigene Keys `KEY_EXCLUSION_PATTERNS` (Z. 59-67), `storedArray()` (Z. 901-911) | exact |
| `php/lib/Service/StorageService.php` | service | DB-Lesung, Mountliste | eigene `deselected()` (Z. 1140-1185), `resolveHashed()` (Z. 882-961) | exact |
| `php/lib/Service/ExclusionService.php` | service (Validierung) | request-response | eigene `validate()` (Z. 379-417), `newPrefixes()` (Z. 486-504), `prefixes()` defensiv (Z. 236-312) | exact |
| `php/lib/Controller/SettingsController.php` | controller | request-response | eigene `saveRules()` (Z. 359-486), `previewRules()` (Z. 259-304), `listOf()` (Z. 572-578), `ruleSet()` (Z. 546-554) | exact |
| `php/lib/Service/AdminViewService.php` | service (View) | transform | eigene `rules()` (Z. 1257-1280) | exact |
| ggf. neu: `php/lib/Service/ExternalMountService.php` (Liste der Admin-Mounts) | service | DB-Lesung | `ParallelSearchService.php` (App-Erkennung, ganze Datei) + `StorageService::resolveHashed()` (Z. 919-938) | role-match |
| `php/templates/admin.php` | template | server-render | Ordner-/Musterliste Z. 1478-1545, Schalter Z. 1582-1591, Bestätigung Z. 1637-1649, Fehler-Maps Z. 1031-1050 | exact |
| `php/js/admin.js` | Vanilla-JS | event-driven | `setupPatternList()` Z. 1253-1291, `confirmNewExclusions()` Z. 1371-1456, `saveRules()` Z. 1503-1570, `applyRules()` Z. 1597-1645, `locale()` Z. 142-146 | exact |
| `php/css/admin.css` | stylesheet | n/a | `.findling-rules__row` Z. 419-425, `.findling-rules__toggle` Z. 487-497, `.findling-rules__error` Z. 502-506, Warnpaar Z. 76-79 / 189-199 | exact |
| `php/l10n/*.js` + `*.json` (8 Sprachen = 16 Dateien, plus `zh_TW.js/json` nach PR #56) | l10n | static | bestehende Einträge, z. B. `de.json:231`, `de.js:232` | exact |
| `php/tests/Unit/ExclusionServiceTest.php` | test | unit | eigene `refusals()` Z. 175-220, `testStoredPrefixesStayByteForByteAndAStarInThemIsLiteral` Z. 370-381 | exact |
| `php/tests/Unit/StorageServiceTest.php` | test | unit (Fake-DB) | eigene Fake-DB Z. 103-269, `testDeletedAndSwitchedOffStoragesAreToldApart` Z. 353-366 | exact |
| `php/tests/Unit/SettingsControllerTest.php` | test | unit | eigene Z. 209-289 (`saveRules`-Tests, DataProvider `everyRuleThatCanChange`) | exact |
| `php/tests/Unit/SettingsServiceTest.php` | test | unit | eigene Z. 367-389 | exact |
| `php/tests/Unit/AdminViewServiceTest.php` | test | unit | eigene `rules()`-Tests | exact |
| `backend/tests/test_admin_ui_contract.py` | test (Gate) | static scan | eigene Z. 2891-2904, 3590-3677, 4692-4851, 603-619 | exact |
| `backend/tests/test_exclusion_path_space.py` | test (Gate) | static scan | eigene Z. 144-155, 454, 571-580 | exact |
| `backend/tests/test_store_metadata.py` | test (Gate) | static scan | eigene README-Scans Z. 1828-1852, 1955-1962, 2340-2344 | exact |
| `.github/workflows/integration.yml` | CI | e2e | Schritte "M-32-02" Z. 2947-2989 und Z. 3114-3135 | exact |
| `php/appinfo/info.xml`, `backend/appinfo/info.xml` | config (Store-Text, Version) | static | eigene `<description>` Z. 36-152 (php), `<version>` Z. 179; backend `<version>` Z. 193, `<image-tag>` Z. 294 | exact |
| `README.md`, `README.en.md`, `README.fr.md` | doc | static | eigene Abschnitte "Unterstützte Dateitypen" (Z. 44), "Messwerte" (Z. 122) | exact |
| `docs/language-analyzers.md` | doc | static | Abschnitt `### Known limitations (short list, HART-05)` | exact |
| `docs/store-listing.md` | doc (Entwurf + Abnahme) | static | `# Entwurf v1.6.4 (12.11.2026)` Z. 3178-3211, `# Entwurf v1.6.3 (Gesamttext), abgenommen am ...` Z. 2888 | exact |
| `docs/admin-page.md` | doc | static | `## Die vier Schalter` Z. 630, `### Abgelehnte Eingaben` Z. 843 | exact |
| `CHANGELOG.md`, `CHANGELOG.de.md`, `CHANGELOG.fr.md`, `PRODUCT.md` | doc | static | `## [1.6.5] - 2026-11-16` Z. 9-14 | exact |
| optional: Test Digest-Gleichheit zizmor/actionlint | test (Gate) | static scan | `backend/tests/test_php_supply_chain_gates.py`, Pins in `scripts/dev/php_gates_docker.sh:66-67` | role-match |
| Store-Text-Längenmessung an 2 bis 3 Vergleichs-Apps | Recherche | n/a | keine | no analog |

---

## Pattern Assignments

### `php/lib/Service/SettingsService.php` (service, CRUD appconfig)

**Analog:** eigene Datei.

**Neuer Key, Muster der Musterliste** (Z. 59-70): eigener Key, fehlender Key liest sich als leere Liste, daher keine Migration:
```php
	 * The wildcard patterns of D-30-01, a list of their own next to the
	 * prefixes. ... A missing key reads as an empty list, so no
	 * migration exists for it.
	 */
	public const KEY_EXCLUSION_PATTERNS = 'exclusion_patterns';
	public const KEY_MAX_FILE_BYTES = 'max_file_bytes';
	public const KEY_INDEX_TEAM_FOLDERS = 'index_team_folders';
	public const KEY_INDEX_EXTERNAL_STORAGE = 'index_external_storage';
```
Vorschlag (Claude's Discretion): `public const KEY_EXCLUDED_EXTERNAL_MOUNTS = 'excluded_external_mounts';` als JSON-Array von int (D-45-01/02: ausgeschlossene IDs, Opt-out).

**Getter neben dem Schalter** (Z. 546-557):
```php
	public function indexExternalStorage(): bool {
		return $this->appConfig->getValueBool(Application::APP_ID, self::KEY_INDEX_EXTERNAL_STORAGE, false);
	}
```
Der Getter der Liste muss defensiv lesen (occ ist Zweitzugang), Muster `ExclusionService::prefixes()` Z. 241-257:
```php
		try {
			$stored = $this->appConfig->getValueArray(Application::APP_ID, SettingsService::KEY_EXCLUSIONS, []);
		} catch (AppConfigTypeConflictException) {
			$this->logger->warning(
				'Findling: stored exclusion entries are not usable folder paths, so they are neither in force nor shown',
				['unusable' => 1, 'inForce' => 0],
			);
			$this->cached = [];
			return $this->cached;
		}
```
Nur positive ints übernehmen (Muster `classifyAbsent()` Z. 462-469: `is_int($id) && $id > 0`, dedupliziert, sortiert). Logzeilen nur Zähler, nie Werte (T-04-51, `reject()` Z. 921-927).

**save() alles oder nichts** (Z. 849-877): neuer Wert wird mit den anderen geschrieben, danach `markScanStale()` (Z. 871-874). Der Kommentar "The four keys of D-08" (Z. 14-20, 49-56) wird zu "five"; das ist eine Klassenaussage, die mitgezogen werden muss.

---

### `php/lib/Service/StorageService.php` (service, Mountliste + Abwahl)

**Analog:** eigene Datei.

**Filter in der EINEN Mountliste** (Z. 309-311):
```php
	public function getMounts(): iterable {
		return $this->fileAccess->getDistinctMounts($this->providers(), true);
	}
```
Gate: `backend/tests/test_exclusion_path_space.py:154-155` verlangt, dass `getDistinctMounts(` nur mit `$this->providers()` als erstem Argument aufgerufen wird und nur an einer Stelle (Test Z. 454 `test_the_app_holds_exactly_one_mount_list`). Also: Aufruf unverändert lassen und das Ergebnis danach filtern (storage_ids der ausgeschlossenen Admin-Mounts herausnehmen). `getDistinctMounts` liefert nur `storage_id, root_id, overridden_root`, keine mount_id; die Abbildung mount_id -> storage_id braucht eine eigene Abfrage auf `oc_mounts`.

**Abfrage oc_mounts nach mount_id, gebändert und mit Zeilenprüfung** (Z. 885-908):
```php
		foreach (array_chunk(array_keys($hashed), self::ABSENT_LOOKUP_BAND) as $band) {
			$qb = $this->db->getQueryBuilder();
			$qb->select('storage_id', 'user_id', 'mount_id', 'mount_provider_class')
				->from('mounts')
				->where($qb->expr()->in('storage_id', $qb->createNamedParameter($band, IQueryBuilder::PARAM_INT_ARRAY)))
				->andWhere($qb->expr()->eq('mount_provider_class', $qb->createNamedParameter(self::EXTERNAL_STORAGE_MOUNT_PROVIDER, IQueryBuilder::PARAM_STR)))
				->andWhere($qb->expr()->isNotNull('mount_id'));

			$result = $qb->executeQuery();
			try {
				while (is_array($row = $result->fetch())) {
					...
					if (... || (string)($row['mount_provider_class'] ?? '') !== self::EXTERNAL_STORAGE_MOUNT_PROVIDER) {
						continue;
					}
```
Für den Filter: `where in('mount_id', $excludedIds)` statt `storage_id`. Wichtig: ein Admin-Mount mit Nutzer-Anmeldedaten hat eine storage_id je Nutzer (Kommentar Z. 500-508), also alle storage_ids eines mount_id nehmen. Ein Storage, den zusätzlich ein nicht ausgeschlossener Mount trägt (zweiter Admin-Mount oder persönlicher Mount), darf nicht verschwinden; Muster dafür ist die Gegenprüfung in `deselected()` über `isIndexedStorage()` (Z. 1176-1181).

**Abwahl melden** (Z. 1140-1152): heute frühes Return, wenn kein Schalter aus ist:
```php
	private function deselected(array $existing): array {
		$switchedOff = [];
		if (!$this->settingsService->indexTeamFolders()) {
			$switchedOff[] = self::TEAM_FOLDER_MOUNT_PROVIDER;
		}
		if (!$this->settingsService->indexExternalStorage()) {
			$switchedOff[] = self::EXTERNAL_STORAGE_MOUNT_PROVIDER;
		}

		$existing = array_values(array_filter($existing, static fn (int $storageId): bool => $storageId > 0));
		if ($switchedOff === [] || $existing === []) {
			return [];
		}
```
Muss erweitert werden: bei Schalter AN und nicht leerer Ausschlussliste die storage_ids der ausgeschlossenen mount_ids ebenfalls als deselected melden (nur wenn `!isIndexedStorage()`, Z. 1176-1181). Sonst nehmen sie die Gnadenfrist-Straße (30 Tage) statt "sofort" (D-45-05). Test `testAStorageOfASwitchThatIsOnIsNeverDeselected` (StorageServiceTest Z. 368-378) fixiert heute "Schalter an -> oc_mounts wird nicht gefragt" (`assertSame([['storages', 4]], $this->bands)`); der Test bleibt für leere Ausschlussliste gültig, für nicht leere braucht es einen neuen.

**Klassen-Docblock** (Z. 27-43): "Which mounts are looked at ... default of two switches" um den Ausschluss je Mount ergänzen; Konstante `EXTERNAL_STORAGE_MOUNT_PROVIDER` (Z. 90) wiederverwenden, nie zweites Literal (Gate `test_the_two_mount_switches_are_read_and_the_external_entry_is_live`, Z. 571-580).

**Gelöschte Mounts** (D-45-06): Ein ausgeschlossener mount_id ohne Zeile in `oc_mounts`/`oc_external_mounts` liefert einfach keine storage_id; kein Fehler, kein Log mit Wert. Muster: `resolveHashed()` überspringt unbekannte Zeilen still (Z. 899-902).

---

### `php/lib/Service/ExclusionService.php` (service, Validierung) EXCL-06

**Analog:** eigene Datei.

**Fehlercodes** (Z. 118-128, 147-156):
```php
	public const FIELD_EXCLUSIONS = 'exclusions';
	public const ERROR_EMPTY = 'empty';
	public const ERROR_TOO_LONG = 'too_long';
	public const ERROR_TRAVERSAL = 'traversal';
	public const ERROR_DUPLICATE = 'duplicate';
	public const ERROR_TOO_MANY = 'too_many';
	...
	public const ERROR_NO_WILDCARD = 'no_wildcard';
```
Neu: `public const ERROR_WILDCARD = 'wildcard';` (UI-SPEC Abschnitt 4). Die Zeichen stehen schon als `private const STAR = '*'; private const ANY = '?';` (Z. 159-160), wiederverwenden.

**validate() Schleife** (Z. 379-417), hier einhängen:
```php
		$seen = [];
		foreach ($prefixes as $entry) {
			if (!is_string($entry) || trim($entry) === '') {
				$errors[] = self::ERROR_EMPTY;
				continue;
			}
			if (strlen($entry) > self::MAX_PREFIX_LENGTH) {
				$errors[] = self::ERROR_TOO_LONG;
				continue;
			}

			$normalised = $this->normalise($entry);
			if ($normalised === null) {
				$errors[] = self::ERROR_TRAVERSAL;
				continue;
			}
			...
```
**Falle "dulden":** `validate()` bekommt bei jedem Speichern die GANZE Liste, inklusive gespeicherter Alt-Einträge (Controller Z. 373). UI-SPEC empfiehlt "alte dulden, neue ablehnen". Dann darf `wildcard` nur für Einträge greifen, die nicht in `prefixes()` stehen; Muster dafür ist `newPrefixes()` (Z. 486-504: `in_array($normalised, $this->prefixes(), true)`). Ohne diese Unterscheidung sperrt das Upgrade jeden Admin mit einem Alt-Eintrag `a*b` aus dem Speichern aus. Test-Anker für den Bestand: `testStoredPrefixesStayByteForByteAndAStarInThemIsLiteral` (ExclusionServiceTest Z. 370-381) muss grün bleiben.

**normalisePattern() bleibt unverändert** (Z. 828-830), nur der Satz zu `no_wildcard` ändert sich (Template/JS/Kataloge):
```php
		if (!str_contains($value, self::STAR) && !str_contains($value, self::ANY)) {
			return [null, self::ERROR_NO_WILDCARD];
		}
```

**Grenzen** (Z. 88, 144): `MAX_PREFIXES = 64`, `MAX_PATTERNS = 32`; für den Zähler NICHT neu definieren, sie fließen schon über `AdminViewService::rules()` und `data-max-entries` ins Template.

---

### `php/lib/Controller/SettingsController.php` (controller, request-response)

**Analog:** eigene Datei.

**Route-Signatur** (Z. 359-366), neuer Parameter hinten anhängen, als `mixed` und über `listOf()` geprüft (H-33-01, Z. 556-578):
```php
	#[\OCP\AppFramework\Http\Attribute\FrontpageRoute(verb: 'POST', url: '/admin/rules')]
	public function saveRules(
		mixed $exclusions = [],
		int $maxFileBytes = 0,
		bool $indexTeamFolders = true,
		bool $indexExternalStorage = false,
		mixed $exclusionPatterns = [],
	): DataResponse {
		[$list, $listShape] = self::listOf($exclusions);
		[$patterns, $patternShape] = self::listOf($exclusionPatterns);
```
Keine neue Route: `test_php_trust_boundary.py` zählt die Attribut-Zeilen (Docblock Z. 45-55), `php/tests/route-security.json:88-91` listet die Route mit `"attributes": []`. Das Attribut nie in Prosa nennen.

**Validieren vor Schreiben, Fehler als Codes unter Feldnamen** (Z. 370-396), **Schreibreihenfolge mit Prüfung der Antworten** (Z. 420-452), **ruleSet für den Änderungshinweis** (Z. 546-554): neue Liste muss in `ruleSet()` aufgenommen werden, sonst zählt ein Speicher-Ausschluss nicht als Regeländerung (Test `everyRuleThatCanChange`, SettingsControllerTest Z. 245-271).

**Logzeilen nur Zähler** (Z. 380-384):
```php
			$this->logger->warning('Findling: refused a set of rules that did not validate', [
				'fields' => count($fieldErrors),
				'exclusions' => count($listErrors),
				'exclusionPatterns' => count($patternErrors),
			]);
```

**Vorschau** (Z. 259-304): Erweiterung für "neu ausgeschlossene Speicher" optional (UI-SPEC offene Frage 3). Muster `newPatterns` ohne Zahl (Z. 290). Eine Zahl je Speicher nur, wenn billig; sonst Variante ohne Zahl.

---

### `php/lib/Service/AdminViewService.php` (service, transform)

**Analog:** eigene `rules()` (Z. 1257-1280):
```php
	public function rules(): array {
		return [
			'exclusions' => $this->exclusionService->prefixes(),
			'exclusionPatterns' => $this->exclusionService->patterns(),
			'maxPrefixes' => ExclusionService::MAX_PREFIXES,
			'maxPrefixLength' => ExclusionService::MAX_PREFIX_LENGTH,
			'maxPatterns' => ExclusionService::MAX_PATTERNS,
			'maxPatternLength' => ExclusionService::MAX_PATTERN_LENGTH,
			'maxFileBytes' => $this->settingsService->maxFileBytes(),
			'maxFileBytesCeiling' => $this->settingsService->containerCap(),
			'indexTeamFolders' => $this->settingsService->indexTeamFolders(),
			'indexExternalStorage' => $this->settingsService->indexExternalStorage(),
			'cleanupLatencyHours' => self::RECONCILE_INTERVAL_HOURS,
			'restartCommand' => self::RESTART_COMMAND,
		];
	}
```
Phpdoc-Shape (Z. 1257-1264) mitziehen.

**Achtung Transport:** `rules()` steckt in `overview()` (Z. 864), das alle 5 s gepollt wird und als Initial State `bootstrap` base64 ins HTML geht (`php/lib/Settings/Admin.php:56-58`). Mountpunkte und Typen sind Admin-Daten wie die Präfixe (die dort schon stehen), aber die Liste kann lang sein. Planer entscheidet: `excludedMounts` (IDs) in `rules()`, die volle Mountliste nur fürs Template (eigener Key im Template-Array) oder ebenfalls in `rules()`. Bei `rules()` gelten Gate `test_every_new_status_key_has_exactly_one_line_in_the_service` (test_admin_ui_contract Z. 2416) und Typprüfungen.

---

### Neu (optional): Lesen der Admin-Mounts (service, DB-Lesung)

**Analog A, App aktiv?** `php/lib/Service/ParallelSearchService.php` (ganze Datei, 52 Zeilen):
```php
final class ParallelSearchService {
	public const APP_IDS = ['fulltextsearch', 'files_fulltextsearch'];

	public function __construct(
		private IAppManager $appManager,
	) {
	}

	public function active(): bool {
		foreach (self::APP_IDS as $appId) {
			if ($this->appManager->isEnabledForAnyone($appId)) {
				return true;
			}
		}
		return false;
	}
}
```
Für "files_external nicht aktiviert" (UI-SPEC Zustand) `isEnabledForAnyone('files_external')`; Docblock Z. 23-30 begründet, warum nicht `isEnabledForUser`/`isInstalled`.

**Analog B, Tabelle lesen:** `StorageService::resolveHashed()` Z. 919-938 (`oc_external_mounts`, gebändert, `closeCursor` im `finally`). Für die Liste: `mount_id, mount_point, storage_backend` und nur Admin-Mounts (Spalte `type`, Admin = 1, persönlich = 2; vor Nutzung an NC 33 bis 35 prüfen, D-45-03). Alternative über die files_external-API (`GlobalStoragesService`, liefert Backend-Anzeigenamen wie "SMB/CIFS") gibt es im Code noch nicht; dann muss die App weich ausfallen, wenn files_external fehlt. Der UI-SPEC verlangt den Anzeigenamen des Backends, Rückfall auf die Kennung (`storage_backend`).

Sortierung nach Mountpunkt mit Collator der Nutzersprache, Gleichstand nach ID (UI-SPEC 1). Kein Mountpunkt, keine ID in Logzeilen.

---

### `php/templates/admin.php` (template, server-render)

**Analog:** eigene Datei.

**Daten aus `$rules` ziehen** (Z. 1009-1021, 1067-1068):
```php
$rules = is_array($_['rules'] ?? null) ? $_['rules'] : [];
$prefixes = is_array($rules['exclusions'] ?? null) ? $rules['exclusions'] : [];
...
$maxPrefixes = $whole($rules['maxPrefixes'] ?? 0);
...
$externalStorage = ($rules['indexExternalStorage'] ?? false) === true;
```

**Fehler-Maps, die das JS wortgleich führen muss** (Z. 1031-1050):
```php
$folderErrorSentences = [
	'empty' => $l->t('Enter a folder path.'),
	'too_long' => $l->t('A folder path may be at most %s bytes long.', [$count($maxPrefixLength)]),
	'too_many' => $l->t('At most %s folders can be excluded.', [$count($maxPrefixes)]),
	'duplicate' => $l->t('This path is already excluded.'),
	'traversal' => $l->t('The entry must not contain . or .. as a folder name.'),
];
$patternErrorSentences = [
	...
	'no_wildcard' => $l->t('This entry has no * or ?. Add it under "Excluded folders" instead.'),
];
```
Neu: `'wildcard' => $l->t('Folders take no * or ?. For a pattern like Archiv* use "Excluded patterns".')` in der Ordner-Map; `no_wildcard` bekommt den neuen Wortlaut aus UI-SPEC (alter Schlüssel verschwindet aus allen Katalogen).

**Liste mit Zeilen, rein serverseitig** (Z. 1483-1494), Vorlage für die Speicherliste und für die Markierung alter Einträge:
```php
	<ul class="findling-rules__list" id="findling-rules-list" aria-labelledby="findling-rules-exclusions-label">
		<?php foreach ($prefixes as $prefix) {
			$prefix = is_string($prefix) ? $prefix : '';
			?>
			<li class="findling-rules__row">
				<span class="findling-path findling-rules__prefix"><?php p($prefix); ?></span>
				<button type="button" class="findling-rules__remove" aria-label="<?php p($l->t('Remove exclusion %s', [$prefix])); ?>">
```
Markierung (UI-SPEC 5): in derselben `li` ein `<p class="findling-rules__row-warning">` mit `$alertIcon`-SVG (Z. 349, Einbindung wie Z. 1639). Achtung: `currentEntries()` im JS liest `.findling-rules__prefix` (admin.js Z. 1020-1031), der Warnsatz darf diese Klasse nicht tragen.

**Feld mit Grenzen als data-Attribut** (Z. 1496-1502): `data-max-entries="<?php p((string)$maxPrefixes); ?>"`. Zähler `#findling-rules-slots` direkt nach `.findling-rules__add` und vor `#findling-rules-new-error` (UI-SPEC 3); Musterliste analog nach Z. 1544.

**Checkbox-Paar** (Z. 1587-1591):
```php
	<div class="findling-rules__toggle">
		<input type="checkbox" class="checkbox" id="findling-rules-external-storage" name="indexExternalStorage"<?php if ($externalStorage) { ?> checked<?php } ?>>
		<label for="findling-rules-external-storage"><?php p($l->t('Index external storage')); ?></label>
	</div>
	<p class="settings-hint" id="findling-rules-external-help"><?php p($l->t('External storage can be slow or charged per request. Indexing reads every file once.')); ?></p>
```
Die `fieldset#findling-rules-mounts` gehört zwischen Z. 1591 und `#findling-rules-effect` (Z. 1593). `disabled` am fieldset serverseitig setzen, wenn `$externalStorage` false (D-45-04).

**Bestätigungszeile mit Platzhalter-Schnitt** (Z. 1642):
```php
				<span class="findling-rules__confirm-line" id="findling-rules-confirm-patterns" hidden><span id="findling-rules-confirm-patterns-before"></span><code class="findling-path" id="findling-rules-confirm-patterns-value"></code><span id="findling-rules-confirm-patterns-after"></span></span>
```
Neue Zeile `findling-rules-confirm-mounts` exakt in diesem Bau dahinter.

**Ansage-Region** für Zähler bei 1 und 0: Vorbild `<span class="hidden-visually" id="findling-profile-announce" role="status" aria-live="polite"></span>` (Z. 1463).

**Gate-Anker:** Neue Sätze müssen im Bereich zwischen `RULES_TEMPLATE_START = " * Block five: the four things an admin may change."` (Template Z. 986) und dem Profilblock bzw. ab `<div id="findling-rules" class="section">` stehen, sonst sieht sie der Katalog-Gate nicht (test_admin_ui_contract Z. 3590-3616). Keine `style`-Attribute, keine Inline-Skripte, nur `p()`.

---

### `php/js/admin.js` (Vanilla-JS, event-driven)

**Analog:** eigene Datei. Kein Markup bauen (Gate C, Kopfkommentar Z. 11-18); Speicherliste wird nur gelesen und umgeschaltet, nicht geklont.

**Locale (PR #57 und root.lang-Nit, KAT-04)** (Z. 142-146), heute:
```js
  function locale () {
    const root = document.documentElement
    const own = (root.dataset.locale || '').replace('_', '-')
    return own || root.lang || 'en'
  }
```
`replace('_', '-')` ersetzt nur den ersten Unterstrich (`zh_Hant_TW` -> `zh-Hant_TW`), und `root.lang` geht ohne Umschreibung durch. Die Korrektur kommt aus PR #57; der root.lang-Nit als eigener Commit (D-45-11).

**Fehler-Map im JS, wortgleich zum Template** (Z. 1053-1077): `wildcard` in `folderErrorSentences()` ergänzen, `no_wildcard` neu formulieren. Gate `test_both_halves_name_every_refusal_code_of_both_lists_alike` vergleicht beide Hälften.

**Lokale Vorprüfung beim Hinzufügen** (Muster `setupPatternList()` Z. 1258-1285):
```js
      add.addEventListener('click', function () {
        const value = field.value.trim()
        const patterns = currentPatterns()
        const maxLength = boundOf(PATTERN_FIELD, 'data-max-length')
        const maxEntries = boundOf(PATTERN_FIELD, 'data-max-entries')
        let code = ''
        if (value === '') {
          code = 'empty'
        } else if (patterns.indexOf(value) !== -1) {
          code = 'duplicate'
        } else if (maxLength > 0 && Array.from(value.normalize('NFC')).length > maxLength) {
          code = 'too_long'
        } else if (maxEntries > 0 && patterns.length >= maxEntries) {
          code = 'too_many'
        }
        if (code !== '') {
          fieldError(PATTERN_ERROR, PATTERN_FIELD, refusalSentence(code, patternErrorSentences(), PATTERN_FIELD))
          return
        }
```
`setupExclusionList()` (Z. 1198-1227) prüft heute nur `empty` und `duplicate` mit festen Sätzen; auf dieses Code-Muster umstellen und `wildcard` (`value.indexOf('*') !== -1 || value.indexOf('?') !== -1`) sowie `too_many` ergänzen. UI-SPEC 4: Eingabe NICHT leeren, Feld `aria-invalid="true"`; `fieldError()` (Z. 1141-1148) setzt heute kein `aria-invalid`, das ist zu ergänzen und bei `clearFieldError()` zurückzunehmen.

**Zähler aktualisieren:** an den Stellen, wo heute `refreshEmptyState()` läuft (Z. 1042-1045, aufgerufen in Add, `removeRow()` Z. 1230-1241 und `applyRules()` Z. 1623/1642). Zahlen über `numbers.format` (Z. 148), Grenze über `boundOf(fieldId, 'data-max-entries')` (Z. 1085-1089). Platzhalter-Ersatz wie Z. 1517-1518 (`.replace('%1$s', ...).replace('%2$s', ...)`).

**Bestätigung, Satz am Platzhalter schneiden** (Z. 1434-1441):
```js
    const cut = patternSentence.indexOf('%s')
    text('findling-rules-confirm-patterns-before', cut === -1 ? patternSentence : patternSentence.slice(0, cut))
    text('findling-rules-confirm-patterns-value', addedPatterns.join(', '))
    text('findling-rules-confirm-patterns-after', cut === -1 ? '' : patternSentence.slice(cut + 2))
    shown('findling-rules-confirm-patterns', addedPatterns.length > 0)
```
Für Speicher identisch mit `findling-rules-confirm-mounts-*`; Einzahl/Mehrzahl über zwei Schlüssel wie Z. 1434-1436. "Neu ausgeschlossen" bestimmen wie `newPatternsOf()` (Z. 1316-1320) gegen einen Stand `inForceMounts`, der in `setupRules()` (Z. 1661-1664) und `applyRules()` gesetzt wird. Auslöser in `saveRules()` Z. 1528 erweitern (nur wenn Hauptschalter an, UI-SPEC 2). "Keep files indexed" setzt die betroffenen Haken zurück: in `dismissConfirmation()` (Z. 1474-1480) bzw. eigenem Cancel-Handler.

**Senden** (Z. 1542-1548): neues Feld ans Ende hängen. Gate `test_the_script_sends_the_pattern_list_and_cuts_the_confirmation_around_it` (test_admin_ui_contract Z. 4825-4837) prüft die exakte Schlüsselreihenfolge und muss mitgezogen werden.

**Hauptschalter sperrt fieldset ohne Neuladen:** Change-Handler am `#findling-rules-external-storage`; `#findling-rules input` löst bereits `touched` aus (Z. 1697-1702), die Mount-Checkboxen sind damit automatisch "ungespeichert".

**Gate-Anker:** neue `t('findling', ...)`-Aufrufe müssen zwischen `" * Block five, the four rules, and the one part of this page that writes."` (Z. 997) und `' * Block "Performance profile" (plan 27-12'` (Z. 1706) stehen. Kein `n()` in diesem Block (Gate Z. 3608-3611 verbietet Plural), daher drei getrennte Zählerschlüssel wie im UI-SPEC.

---

### `php/css/admin.css` (stylesheet)

**Analog:** eigene Datei, Block "the rules and limits" ab Z. 399.

Zeile (Z. 419-425) und Checkbox-Paar (Z. 487-497):
```css
.findling-rules__row {
	display: flex;
	align-items: center;
	gap: calc(var(--default-grid-baseline) * 2);
	min-height: var(--default-clickable-area);
	border-bottom: 1px solid var(--color-border);
}
.findling-rules__toggle label {
	display: flex;
	align-items: center;
	min-height: var(--default-clickable-area);
}
```
Gedämpfte Angabe wie `.findling-rules__unit` (Z. 479-482, dort noch `13px`, neu `var(--font-size-small)` laut UI-SPEC). Warnfarbe als Paar wie `.findling-banner--warning` (Z. 76-79) und Icon wie `.findling-chip--skipped svg { color: var(--color-element-warning); }` (Z. 196-199), aber ohne Fläche (UI-SPEC 5). Fehlerzeile `.findling-rules__error` (Z. 502-506). Abstand zweiter Bestätigungszeile über bestehende Regel Z. 537-539 (gilt für jede weitere `confirm-line` automatisch). `@media (pointer: coarse)` für 44 px (Muster: Gate `COARSE_QUERY`, test_admin_ui_contract Z. 1399). Gates: keine Hex-/rgb-Farben, kein `outline: none` (Z. 360-362).

---

### `php/l10n/*.js` und `*.json` (l10n, static)

**Analog:** bestehende Einträge, Format `de.json`:
```json
{
    "translations": {
        "This entry has no * or ?. Add it under \"Excluded folders\" instead.": "Dieser Eintrag enthält weder * noch ?. Ihn stattdessen unter \"Ausgeschlossene Ordner\" eintragen.",
```
und `de.js` (gleiche Paare in `OC.L10N.register("findling", { ... }, "nplurals=2; plural=(n != 1);");`). Kein Extraktor, beide Hälften von Hand, Gate `test_the_two_translation_files_carry_the_same_keys` (Z. 3695-3718) und `test_the_two_halves_of_every_language_carry_the_same_values` (Z. 4154).

**Pflichten pro neuem Schlüssel:**
- in jeder Datei (heute 16, nach PR #56 18 mit `zh_TW.js/json`); `test_every_sentence_of_the_rules_block_is_in_every_catalogue` (Z. 3619-3677) findet fehlende Sätze, die Anti-Vakuum-Liste Z. 3652 nennt den alten `no_wildcard`-Satz wörtlich und muss auf den neuen umgestellt werden.
- `"ID %s"` ist in jeder Sprache gleich dem Schlüssel; dafür braucht jede Sprache einen Eintrag in `VALUES_THAT_MAY_EQUAL_THEIR_KEY` (Z. 603 ff., Muster `"%1$s (ID %2$s)"` Z. 614), inklusive zh_TW.
- Platzhalter-Parität (Gate `test_no_catalogue_value_loses_or_invents_a_placeholder`, Z. 4279), kein `%` ohne Direktive, kein `|` (Z. 997-1003).
- de und de_DE wortgleich (Z. 3721).
- Ortsangaben "Excluded patterns"/"Excluded folders" in Anführungszeichen wie im Bestand `\"...\"`.
- Umlaut-Audit (D-45-10), Sprachregeln je Sprache in `docs/l10n-*.md`.

---

### `php/tests/Unit/ExclusionServiceTest.php` (test, unit)

**Analog:** eigene `refusals()`/`testARefusedEntryEarnsItsCodeAndNotItsValue` (Z. 175-212), dort für `validatePatterns()`; für Ordner dasselbe mit `validate()`:
```php
	#[DataProvider('refusals')]
	public function testARefusedEntryEarnsItsCodeAndNotItsValue(string $value, string $code): void {
		$service = $this->service();
		$answer = $service->validatePatterns([$value]);
		self::assertSame([$code], $answer);
		self::assertNotContains($value, $answer);
		...
		foreach ($this->logLines as $line) {
			...
			self::assertNotContains($value, $line['context']);
		}
	}
```
Fälle: `Archiv*` neu -> `wildcard`; `a*b` gespeichert und erneut gesendet -> kein Fehler (dulden); Kontrollfall ohne Stern -> `[]`. Service-Fabrik `service(array $prefixes, ?array $patterns)` Z. 58-101 stellt gespeicherte Liste bereit.

---

### `php/tests/Unit/StorageServiceTest.php` (test, unit, Fake-DB)

**Analog:** eigene Fake-DB (Z. 103-242) beantwortet `mounts`, `external_mounts`, `external_config` aus Zeilenlisten; `service(bool $teamFolders, bool $external)` (Z. 244-269) baut `SettingsService` echt über gemockte `IAppConfig`. Neuer Parameter für die Ausschlussliste über `getValueArray`-Callback analog Z. 246-252. Achtung: Der Fake unterscheidet `mounts`-Abfragen heute nach String-Array vs. Skalar (Z. 192-206); eine neue Abfrage nach `mount_id` braucht dort einen dritten Zweig. `getDistinctMounts` liefert `$this->listed` (Z. 107-120).

Vorbild-Test (Z. 353-366):
```php
	public function testDeletedAndSwitchedOffStoragesAreToldApart(): void {
		$this->storages = [7, 9, 40];
		$this->mounts = [
			['storage_id' => 9, 'mount_provider_class' => self::EXTERNAL],
			['storage_id' => 40, 'mount_provider_class' => self::HOME],
		];
		$answer = $this->service(external: false)->classifyAbsent([14, 15, 7, 9]);
		self::assertSame(['gone' => [14, 15], 'deselected' => [9]], $answer);
		self::assertSame($this->opened, $this->closed, 'every cursor is closed');
	}
```
Neue Fälle: Schalter an + mount_id ausgeschlossen -> storage deselected und nicht in `getMounts()`; zweiter Nutzer-Storage desselben mount_id ebenfalls; Storage, den ein nicht ausgeschlossener Mount mitträgt, bleibt; gelöschter mount_id in der Liste -> kein Fehler (D-45-06); Logs ohne Werte (`assertNoLogCarries`, Z. 339-349).

---

### `php/tests/Unit/SettingsControllerTest.php` / `SettingsServiceTest.php` / `AdminViewServiceTest.php`

**Analog:** `testAPrefixAndAPatternAreBothSavedAndThePrefixListStaysByteForByte` (SettingsControllerTest Z. 209-231) prüft Antwort und geschriebene Werte; `everyRuleThatCanChange` (Z. 245-271) braucht einen Fall "ein Speicher ausgeschlossen". Alle bestehenden `saveRules(...)`-Aufrufe sind positional (Z. 212 bis 453); ein neuer letzter Parameter mit Default bricht sie nicht. Nicht-Liste wird über `listOf()` als `empty` abgewiesen (Tests Z. 381-416 als Vorbild). `testSavingTheRulesMarksTheScanStale` (SettingsServiceTest Z. 367-376) zeigt die `save()`-Eingabe.

---

### `backend/tests/test_admin_ui_contract.py` (Gate, static scan)

Stellen, die durch diese Phase rot werden, wenn sie nicht mitgezogen werden:

| Zeile | Was | Anpassung |
|-------|-----|-----------|
| 2891-2904 | `EXPECTED_CATALOGUE_NAMES`, `len(names) == 16` | kommt mit PR #56 (zh_TW); nicht doppelt anfassen |
| 530-556 | `PLURAL_FORM_OF`, `FORM_COUNT_OF` | zh_TW-Eintrag kommt mit PR #56 |
| 603 ff. | `VALUES_THAT_MAY_EQUAL_THEIR_KEY` | `"ID %s"` in jeder Sprache |
| 3632-3668 | Anti-Vakuum-Liste des Regelblocks | alten `no_wildcard`-Satz ersetzen, neue Sätze (Zähler, Speicherliste, `wildcard`) aufnehmen |
| 4718-4730 | `prefix_validation_codes()` liest den Rumpf von `validate()` | neuer Code `wildcard` erscheint automatisch |
| 4757-4767 | `patternErrorSentences` muss ALLE `ERROR_*`-Konstanten abdecken (`set(exclusion_error_codes(service).values())`) | ein neues `ERROR_WILDCARD` macht den Gate rot, außer die Musterliste bekommt einen Satz oder die Menge schließt reine Ordnercodes aus; bewusst entscheiden |
| 4813-4814 | `len(...) == 11`, Ordnercodes genau fünf | auf neue Zahlen setzen |
| 4825-4837 | Schlüsselreihenfolge von `send(ROUTE_RULES, {...})` | neuen Schlüssel anhängen |

Gegenprobe nie mit dem Muster der Umsetzung (Owner-Regel); Vorbild für Selbsttests mit Clean-Sample und Fehl-Sample: Z. 1897-1933 und 4936.

---

### `backend/tests/test_exclusion_path_space.py` (Gate)

Unverändert lassen, aber Umsetzung daran ausrichten: genau ein `getDistinctMounts($this->providers(), true)` (Z. 144-155, 454, Clean-Sample Z. 613-620). Optional neuer Gate, dass `getMounts()` den Mount-Ausschluss anwendet, im Stil von `test_the_two_mount_switches_are_read_and_the_external_entry_is_live` (Z. 571-580: `statements(...)` und `any(... in line ...)`).

---

### `.github/workflows/integration.yml` (CI, e2e)

**Analog:** Schritte "M-32-02" (Z. 2947-2970 Aufbau, Z. 3114-3135 Zyklus 3):
```yaml
            created=$(./occ files_external:create "/e${n}" local null::null \
              -c "datadir=${{ runner.temp }}/m3202/e${n}")
            config_id=$(awk '/created with id/ { print $NF }' <<< "${created}")
            ...
            echo "E${n}_MOUNT=${config_id}" >> m3202.env
```
```yaml
      - name: "M-32-02: cycle 3, the switch for external storage goes off, E1 goes at once"
        run: |
          . ./m3202-lib.sh
          . ./m3202.env
          ./occ config:app:set findling index_external_storage --value=0 --type=boolean
          cycle m3202-cycle3.txt
          drain
          table
          expect_rows "${E1_STORAGE}" E1 0 "the switched off external storage kept its documents"
          expect_unstamped "${E1_STORAGE}" E1 "the switched off external storage got a grace stamp instead of going at once"
```
Neuer Zyklus VOR dem Abschalten (Schalter an): einen Mount per `occ config:app:set findling <key> --value='[<E_MOUNT>]' --type=array` ausschließen, `expect_rows ... 0` und `expect_unstamped`, Kontroll-Mount und keep36 unverändert; danach Ausschluss zurücknehmen und Nachindexierung beim nächsten Abgleich prüfen. Die config_ids stehen schon in `m3202.env`. Fehlerausgabe-Schritt Z. 3137-3147 um die neue Zyklusdatei ergänzen.

---

### `php/appinfo/info.xml`, `backend/appinfo/info.xml` (Store-Text, Version)

**Analog:** eigene `<description>`-Blöcke (php Z. 36-152; backend analog ab Z. 96). Kern bleibt (D-45-14): Datenschutz-Satz (`PRIVACY_MARKERS`, test_store_metadata Z. 207), Connector-Satz (Z. 403, php Z. 59/98/137), Umstiegs-Link (php Z. 50/89/128), neu Link auf die GitHub-Doku. Raus: Messzahl (Z. 69/108/147), "Known limitations" (Z. 52-57 usw.), Formatliste (Z. 61-65 usw.), Share-Satz, "Similar documents" (Z. 41/80/119).

Version: php `<version>` Z. 179, backend `<version>` Z. 193 und `<image-tag>` Z. 294, plus `blob/v1.6.5`-Links in allen sechs Beschreibungen auf `v1.7.0`. Gate `backend/tests/test_lockstep_versions.py` (Z. 159) und `docker.yml` vergleichen alle drei.

Ablauf (D-45-13, Owner-Regel "Produkttexte = Faktenliste, Entwurf vor Release zeigen"): Entwurf als neuer Abschnitt in `docs/store-listing.md` nach Muster `# Entwurf v1.6.4 (12.11.2026): ...` (Z. 3178-3211) mit Teilen je App und Sprache wie `# Entwurf v1.5.0 (Gesamttext), abgenommen am 20.10.2026` (Z. 2320-2622, Teile 1 bis 8); Überschrift erst nach Freigabe mit "abgenommen am TT.MM.JJJJ" (Regex `APPROVAL_DATE`, test_store_metadata Z. 542).

---

### `backend/tests/test_store_metadata.py` (Gate, STORE-04)

Diese Tests prüfen heute die Pflichtinhalte IN den info.xml und werden mit kurzen Store-Texten rot:

| Test (Zeile) | Prüft heute | Umzug nach |
|--------------|-------------|------------|
| `test_the_measured_figure_stands_in_every_language_of_the_companion_half` (1855), `..._backend_half` (1864), `test_every_store_description_carries_exactly_one_measured_figure` (1872) | 730.2 MB in jeder Beschreibung | READMEs; README-Gates existieren schon: `test_the_measured_sentence_stands_in_the_readme` (1828-1852) |
| `test_every_description_carries_the_five_known_limitations_under_its_heading` (1908), `test_the_english_known_limitations_..._verbatim_in_the_doc` (1919), `test_the_language_line_stands_right_before_the_limitations_in_all_six_descriptions` (1932) | 5 Grenzen in jeder Beschreibung | READMEs in drei Sprachen bzw. `docs/language-analyzers.md` (`LANGUAGE_ANALYZERS_HEADING`, Z. 468) |
| `test_every_description_names_the_formats_of_1_5_in_its_file_type_list` (1945), `test_every_file_type_list_stands_in_the_draft_of_phase_31_character_for_character` (1976) | Formatliste | `test_every_readme_names_the_formats_of_1_5_in_its_file_type_section` (1955-1962) existiert schon |
| `test_the_share_sentence_stands_once_in_all_three_languages_of_both_halves` (2316), `test_the_german_companion_description_carries_the_owner_sentence_character_for_character` (2331) | Share-Satz | `test_the_share_sentence_stands_in_the_readme_of_its_language` (2340-2344) existiert schon |
| `test_the_connector_sentence_stands_once_...` (1885), Privacy (2936) | Kern | bleibt in info.xml |

Muster für README-Scan (Z. 2340-2344):
```python
def test_the_share_sentence_stands_in_the_readme_of_its_language() -> None:
    for readme, language in ((README, DEFAULT_LANGUAGE), (README_DE, "de"), (README_FR, "fr")):
        assert collapse(readme.read_text(encoding="utf-8")).count(SHARE_SENTENCES[language]) == 1, readme.name
```
Neu nötig: "Similar documents" und die 5 Grenzen als README-Gate (READMEs haben "Ähnliche Dokumente" schon: README.md Z. 34, README.en.md Z. 33, README.fr.md Z. 36; "Bekannte Grenzen" fehlt in allen drei READMEs). Die Selbsttests der umgezogenen Scanner (z. B. Z. 2283-2290, 2383-2398, 2457-2496) auf README-Quellen umstellen statt löschen.

---

### `CHANGELOG.md`, `CHANGELOG.de.md`, `CHANGELOG.fr.md`, `PRODUCT.md` (doc)

**Analog:** `CHANGELOG.md` Z. 7-14:
```markdown
## [Unreleased]

## [1.6.5] - 2026-11-16

### Security

- Dependency update in the backend: opentelemetry-api 1.45.1 to 1.45.2
  (CVE-2026-126360). No functional changes.
```
Abschnitt `## [1.7.0] - <Datum>` mit `### Added` (Ausschluss je Speicher #45, freie Plätze, Traditional Chinese #56) und `### Fixed` (Locale #57, Meldungen). Keine "closes/fixes" vor Issue-Nummern (D-45-16). Gate `backend/tests/test_changelog_translations.py` hält die drei Sprachen zusammen. PRODUCT.md nennt die Sprache zh_TW (KAT-03), eigener Commit (D-45-11).

---

## Shared Patterns

### Nur Zähler und Codes in Logs und Antworten
**Source:** `php/lib/Service/SettingsService.php:913-927`, `ExclusionService.php:118-122`
**Apply to:** alle PHP-Änderungen
```php
	private function reject(): void {
		$this->rejected++;
		$this->logger->warning(
			'Findling: refused a settings value that is outside its range',
			['rejected' => $this->rejected],
		);
	}
```
Kein Mountpunkt, kein Pfad, keine mount_id-Liste im Log. Antworten tragen Codes, nie Eingabewerte (Ausnahme mit Begründung: `newPrefixes` in der Vorschau, Controller Z. 233-239).

### Defensiv lesen (occ ist Zweitzugang)
**Source:** `ExclusionService::prefixes()` Z. 236-312
**Apply to:** jeder neue appconfig-Lesepfad (Ausschlussliste der Mounts)
`AppConfigTypeConflictException` fangen, unbrauchbare Einträge zählen und verwerfen, Ergebnis pro Request cachen und nicht länger (D-08).

### Alles oder nichts beim Speichern
**Source:** `SettingsController::saveRules()` Z. 370-452
**Apply to:** Erweiterung von POST /admin/rules
Erst alle Teile validieren, dann in fester Reihenfolge schreiben, jede `save()`-Antwort prüfen, bei Fehler `'saved' => false` mit Codes je Feld und Satz "The rules were not saved." (Englisch, vom JS übersetzt).

### Script baut kein Markup, Template rendert alle Zustände
**Source:** `php/js/admin.js:1-24`, `php/templates/admin.php:1000-1008`
**Apply to:** Speicherliste, Zähler, Markierung, Bestätigung
Nur `text()`, `shown()`, `setAttribute`, `disabled`, `checked`; Werte nur als Textknoten. Übersetzte Sätze mit Werten am Platzhalter schneiden (admin.js Z. 1437-1440), Funktions-Replacements gegen `$&` (Z. 1173-1176, 1411-1418).

### Nextcloud-Stilmittel
**Source:** `php/css/admin.css:399-586`, `DESIGN.md`
**Apply to:** alle CSS-Zusätze
Nur `--color-*`, `calc(var(--default-grid-baseline) * n)`, `--default-clickable-area`, `--font-size-small`; Fläche und `-text` als Paar; Gates in test_admin_ui_contract Z. 360-372 (Farbliterale, `outline: none`, `style=`, Emoji, Gedankenstriche).

### Gates lokal grün
**Source:** `scripts/dev/php_gates_docker.sh` (Psalm-Taint, php-cs-fixer, zizmor, actionlint; Image-Pins Z. 66-67), `scripts/dev/phpunit_docker.sh`, Python: ruff-Vollsatz, pyright basic (`PYRIGHT_PYTHON_FORCE_VERSION=latest`), vulture
**Apply to:** jeder Plan. 44-SECURITY.md: Digests doppelt in `.github/workflows/workflow-lint.yml` und `php_gates_docker.sh`; ein Gleichheits-Test darf in die Härtung (Deferred-Hinweis), Vorbild für Workflow-Text-Gates: `backend/tests/test_php_supply_chain_gates.py` (Clean-Sample plus Fehl-Samples, Z. 167-229).

### Keine Migration für neue appconfig-Keys
**Source:** Kommentar `KEY_EXCLUSION_PATTERNS` (SettingsService Z. 59-66), `KEY_PAUSED`-Test (SettingsServiceTest Z. 380-384)
**Apply to:** Ausschlussliste der Mounts. Fehlender Key = leere Liste = alle Admin-Mounts drin (Opt-out, D-45-02). Upgrade ab 1.6.5 damit ohne Datenbankschritt; `MigrationSelfContainedTest.php` bleibt unberührt.

---

## No Analog Found

| Datei / Aufgabe | Rolle | Data Flow | Grund |
|-----------------|-------|-----------|-------|
| Anzeigename des files_external-Backends ("SMB/CIFS") | service | Lesung | Der Code liest `oc_external_mounts.storage_backend` nur als Kennung (`smb`, `sftp`); eine Nutzung der files_external-PHP-API (`GlobalStoragesService`, `BackendService`) gibt es noch nicht. Rückfall auf die Kennung ist laut UI-SPEC erlaubt. |
| Längenmessung Store-Text an 2 bis 3 Vergleichs-Apps (D-45-14) | Recherche | n/a | Keine Vorlage im Repo; Ergebnis gehört in den Entwurfsabschnitt von `docs/store-listing.md`. |

---

## Offene Punkte für den Planer (aus der Kartierung, nicht blockierend)

1. `ERROR_WILDCARD` als neue öffentliche Konstante kollidiert mit dem Gate, das `patternErrorSentences` gegen ALLE `ERROR_*`-Konstanten prüft (test_admin_ui_contract Z. 4766, 4813). Entweder Gate auf "Codes von `validatePatterns`/`normalisePattern`" einschränken (analog `prefix_validation_codes`) oder Musterliste mit Satz versehen. Ersteres ist sachlich richtig.
2. "Dulden" alter Ordnereinträge mit * oder ? setzt in `validate()` den Vergleich gegen `prefixes()` voraus (siehe ExclusionService oben).
3. `deselected()` meldet heute nichts, wenn beide Schalter an sind; ohne Erweiterung landen ausgeschlossene Speicher in der 30-Tage-Gnadenfrist statt "sofort" (D-45-05).
4. Mountliste in `rules()` reist im 5-s-Poll und im Initial State mit; bewusst entscheiden.
5. PR #56/#57 zuerst mergen (D-45-11), dann bauen: PR #56 ändert die Katalog-Gates (Z. 2891-2904, 530-556), PR #57 `locale()`.

## Metadata

**Analog search scope:** `php/lib/**`, `php/templates/admin.php`, `php/js/admin.js`, `php/css/admin.css`, `php/l10n/`, `php/tests/**`, `php/appinfo/`, `backend/src/findling/worker/reconcile.py`, `backend/tests/test_admin_ui_contract.py`, `test_exclusion_path_space.py`, `test_store_metadata.py`, `test_lockstep_versions.py`, `.github/workflows/integration.yml`, `scripts/dev/`, `docs/store-listing.md`, `README*.md`, `CHANGELOG.md`
**Files scanned:** ca. 30
**Pattern extraction date:** 2026-11-22
