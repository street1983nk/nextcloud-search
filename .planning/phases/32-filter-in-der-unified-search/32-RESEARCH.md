# Phase 32: Filter in der Unified Search - Research

**Researched:** 2026-10-12
**Domain:** Nextcloud Unified Search (IFilteringProvider, Frontend-Plugin-API), PHP-Companion `SearchService`, Rechtegrenze
**Confidence:** HIGH für Server- und Frontend-Mechanik (Quelltext stable33/34/35 gelesen), MEDIUM für die Trefferquote des Ordnerfilters (nicht gemessen)

## User Constraints (geerbt, kein 32-CONTEXT.md vorhanden)

Für Phase 32 gibt es noch kein CONTEXT.md. Bindend sind die geerbten Entscheide:

- **D-30-08 Schema-Einmaligkeit:** Phase 30 war der einzige Schemaschritt (SCHEMA_VERSION 3). Phase 32 ändert weder Schema noch Indexmarken. Prüfzeile A5 aus 30-03 ("Ordnerfilter über files.path, kein Schemafeld").
- **D-31-05 ZIP im Typfilter:** ZIP-Treffer gehören zu keiner der sechs Typgruppen und erscheinen nur ohne Typfilter (dokumentiert in `docs/search-filters.md`).
- **D-05 (v1.2) wird durch USRCH-01 aufgehoben:** Bisher galt "Dateityp und Sortierung nur auf der Ergebnisseite, getCustomFilters() bleibt leer" (`php/lib/Search/Provider.php:163-178`, Test `ProviderTest::testTheProviderDefinesNoFilterOfItsOwn` Zeile 547 und `testTheDialogNeverCarriesATypeGroupOrASortMode` Zeile 655). Der Plan muss diese Umkehr ausdrücklich vollziehen, nicht still.
- **Projektregeln:** Rechteprüfung nur in PHP über `getFirstNodeById` (CLAUDE.md "Nutzerrechte im Python-Index nachbauen" verboten), Quality-Gates lokal grün vor Commit, nach der Phase Security-, Bug- und Performance-Audit, Owner-Abnahme von UI gemeinsam per Playwright, Commits als street1983nk ohne Claude-Trailer.

**Deferred (nicht in dieser Phase):** Sortierung im Dialog, Ordnerfilter auf der eigenen Ergebnisseite, Kombination Typ plus Ordner in einem Chip (siehe Offene Fragen).

## Project Constraints (from CLAUDE.md)

- Code Englisch, deutsche Prosa mit echten Umlauten, keine Em- oder En-Dashes, keine Emojis.
- Rechte nur in PHP über `getFirstNodeById`; kein Rechtemodell im Python-Index.
- Python-Gates (ruff-Vollsatz, pyright basic, vulture) lokal grün vor Commit; PHP-Gates laufen in CI (`php.yml`, kein lokales PHP).
- NC-Fenster 33 bis 35 (`php/appinfo/info.xml:258`); jede Mechanik muss auf allen drei Zweigen tragen.
- Kein Schritt an Schema oder Indexmarken (D-30-08).
- Nach der Phase Security-, Bug- und Performance-Audit; UI-Abnahme mit dem Owner per Playwright.
- Kurze Produkttexte; ein neuer Store- oder README-Satz zum Filter geht als Entwurf an den Owner (REL-05).

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| USRCH-01 | Typfilter (sechs Gruppen) über einen Custom Filter des Findling-Providers | Wire-Weg existiert schon vollständig (`SearchFilters::TYPES` → `ExAppService` → `types` im Backend → Filterklausel). Neu: FilterDefinition `types` plus sichtbare Einträge über `OCA.UnifiedSearch.registerFilterAction` (die einzige sichtbare Filter-UI für Apps in NC 33 bis 35) |
| USRCH-02 | Ordnerfilter (Pfadpräfix inkl. Unterordner), Rechtegrenze bleibt finaler PHP-Recheck | Komplett in PHP: Ordner aus dem Nutzerordner auflösen, billige Reduktion über die schon geladenen `IFileAccess`-Einträge und die Mountliste, autoritative Prüfung über `$ordner->getFirstNodeById()` (gleiche Mechanik wie `$userFolder->getFirstNodeById()`). Kein Backend- und kein Schemaeingriff. Annahme A5 aus Phase 30 trägt NICHT (siehe Befund 3) |
| USRCH-03 | Unbekannte/leere/manipulierte Werte werden ignoriert | Provider parst still auf die geschlossene Menge, Ordner wird bei jedem Fehler ignoriert. Grenze: ein leerer Parameterwert wird vom Nextcloud-Kern mit HTTP 400 abgewiesen, bevor Findling gefragt wird (Befund 5) |
</phase_requirements>

## Summary

Die wichtigste Erkenntnis: **Custom FilterDefinitions erzeugen in der Unified Search von NC 33, 34 und 35 keinerlei sichtbare Oberfläche.** Das Frontend rendert genau drei Filter (Places/Type-Menü, Datum, Person) und schickt aus eigener Kraft nur `since`, `until` und `person` mit (`UnifiedSearchModal.vue` stable33:518-555, stable35:1066-1090). Ein Provider kann keine Auswahlliste (Enum) deklarieren; die Typen sind `bool, int, float, string, strings, datetime, person, nc-user, nc-group` (`FilterDefinition.php` stable33:23-63). Sichtbar wird ein App-Filter nur über die Frontend-Plugin-API `window.OCA.UnifiedSearch.registerFilterAction({id, appId, searchFrom, label, icon, callback})` (`core/src/unified-search.ts:46` in stable33 und stable35) plus das Event `nextcloud:unified-search:add-filter` mit `filterParams`, die als Query-Parameter (`extraQueries`) an `/ocs/v2.php/search/providers/{searchFrom}/search` gehen. Genau so baut die Files-App ihren Filter "In folder" (`apps/files/src/plugins/search/folderSearch.ts`). Phase 32 braucht deshalb zwei Hälften: serverseitig FilterDefinitions `types` und `folder` (sonst wirft der Kern bei unbekanntem Namen weg bzw. bei deklariertem, aber undefiniertem Namen die ganze Providerliste), clientseitig ein kleines Vanilla-JS-Plugin, das auf jeder Seite geladen wird.

Die zweite Erkenntnis betrifft den Ordnerfilter: `files.path` in `state.db` ist **relativ zum Nutzerordner des einen fetchAs-Nutzers** (`QueueService.php:838` und `:904`), bei Abgleich-Zeilen ohne Pfad sogar leer (`repo.py:500-505`), und im Tantivy-Index nur gespeichert, nicht indexiert (`index/schema.py:164`). Für Freigabe-Empfänger, umbenannte Shares und Gruppenordner sieht derselbe Pfad pro Nutzer anders aus. Ein Backend-Vorfilter über `files.path` wäre also für jeden zweiten Nutzer falsch. Annahme A5 (30-03-SUMMARY) war in der Aussage "kein Schemafeld nötig" richtig, in der Begründung aber nicht: Der Ordnerfilter gehört nach PHP. Dort ist er billig, weil `SearchService::reduceIds()` die Cache-Einträge jeder Kandidatenseite ohnehin in einer Abfrage lädt (`SearchService.php:551-580`) und die Mountliste des Nutzers schon einmal pro Lauf holt (`:588-603`).

Die dritte: Fail-open ist auf PHP-Seite vollständig erreichbar, im Backend ist die geltende Arbeitsteilung "Container lehnt ab (422), PHP fällt still zurück" dokumentiert und getestet (`test_search_endpoint.py:441-453`). Empfehlung: Arbeitsteilung beibehalten und Kriterium 3 auf Backendseite über einen Paritätstest (PHP-Menge gleich Backend-Literal gleich `TYPE_GROUPS`-Schlüssel) plus "leere Liste gleich fehlendes Feld" belegen.

**Primary recommendation:** FilterDefinitions `types` und `folder` (beide `TYPE_STRING`) im Provider, ein Vanilla-Plugin `php/js/unified-search.js` mit sechs Typ-Einträgen und einem Ordner-Eintrag (OC.dialogs.filepicker), Ordnerlogik ausschließlich in `SearchService` (Reduktion plus `$ordner->getFirstNodeById`), kein Backend-, kein Schema-, kein Wire-Eingriff.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Sichtbare Filtereinträge, Ordnerauswahl | Browser (Vanilla-JS-Plugin) | Nextcloud-Core-Frontend | Nur `registerFilterAction` erzeugt sichtbare Filter; Core hat kein Rendering für Custom Filters |
| Annahme und Typprüfung der Query-Parameter | Nextcloud-Core (`SearchComposer`) | PHP-Companion (`Provider`) | Core baut `IFilter` nur für deklarierte Namen, Provider normalisiert still |
| Typgruppen-Filter | Backend (Tantivy-Filterklausel über `ext`) | PHP (geschlossene Menge) | Besteht schon für die Ergebnisseite, keine Änderung |
| Ordnerfilter | PHP-Companion (`SearchService`) | , | Pfade sind nutzerabhängig; nur PHP sieht den Nutzerbaum; Backend kennt nur den Pfad eines Nutzers |
| Rechtegrenze | PHP-Companion (`getFirstNodeById`) | , | Unverändert, einzige Autorität |

## Standard Stack

Keine neuen Pakete. Alles aus vorhandenen OCP-APIs und dem Core-Frontend.

### Core (verifiziert am Quelltext)
| API | Seit | Zweck | Quelle |
|-----|------|-------|--------|
| `OCP\Search\IFilteringProvider::getSupportedFilters/getCustomFilters` | NC 28 | Filter deklarieren | `lib/public/Search/IFilteringProvider.php` [VERIFIED: nextcloud/server stable33/35] |
| `OCP\Search\FilterDefinition(name, TYPE_STRING)` | NC 28 | Definition `types`, `folder` | `FilterDefinition.php` stable33:73-81, Name-Regex `/[-0-9a-z]+/Au` |
| `window.OCA.UnifiedSearch.registerFilterAction` | NC 28+ (in 33, 34, 35 identisch) | Sichtbarer Eintrag im Places-/Type-Menü | `core/src/unified-search.ts:46` [VERIFIED] |
| Event `nextcloud:unified-search:add-filter` über `window._nc_event_bus` | Core-Frontend | `filterParams` an den Chip hängen | `UnifiedSearchModal.vue` stable33:472, 828-845; stable35:855, 1365-1380; Bus-Global aus `@nextcloud/event-bus` `lib/index.ts` [VERIFIED: GitHub nextcloud-libraries] |
| `OC.dialogs.filepicker(...)` | deprecated seit 27.1.0, in 33 und 35 vorhanden | Ordnerauswahl ohne Bundler | `core/src/OC/dialogs.js` stable33:224, stable35:222 [VERIFIED] |
| `OCP\AppFramework\Http\Events\BeforeTemplateRenderedEvent::isLoggedIn()` | NC 20 | Skript auf jeder angemeldeten Seite laden | dispatcht von `AdditionalScriptsMiddleware` für jede `TemplateResponse` [VERIFIED stable35] |
| `OCP\Util::addScript`, `OCP\Util::addTranslations` | alt | Skript und l10n auf fremden Seiten | `lib/public/Util.php` stable33:147, 221 |
| `OCP\Files\Folder::getFirstNodeById(int)` | NC 29 | Autoritative Prüfung im Unterbaum | Implementierung `= $this->root->getFirstNodeByIdInPath($id, $this->getPath())` (`lib/private/Files/Node/Folder.php` stable35:354-356) |
| `OCP\Files\Cache\IFileAccess::getByFileId(s)` | NC 29 | Rohkoordinaten (storage, internal path) | schon in `SearchService` injiziert (`:116`, `:564`) |
| `OCP\Files\Config\ICachedMountInfo::getMountPoint/getStorageId/getRootInternalPath` | NC 9/11 | Unter-Mounts im gewählten Ordner | schon geladen in `storageIdsOfUser()` |

### Alternatives Considered
| Statt | Möglich | Warum nicht |
|-------|---------|-------------|
| Plugin-Einträge im Menü | nur FilterDefinitions | Unsichtbar in 33 bis 35; nur per handgebauter OCS-URL nutzbar. Erfüllt "in der Unified Search wählen" nicht |
| PHP-Ordnerfilter | Backend-Vorfilter über `files.path` (A5) | Falsch für Share-Empfänger, Gruppenordner, umbenannte Shares; leer bei Abgleich-Zeilen |
| PHP-Ordnerfilter | Backend-Filter über `file_id`-Erlaubnisliste (Tantivy `file_id` ist indexed+fast, `schema.py:150`) | Kein Schemaschritt nötig, aber neues Wire-Feld (extra=forbid, Lockstep, Versionsbindung) und Teilbaum-Aufzählung pro Tastendruck. Nur als Nachrüstung, falls die Messung (Pitfall 4) Lücken zeigt |
| Eigener Dialog für Typ+Ordner | sechs plus ein Menüeintrag | Eigenes `<dialog>` kollidiert mit dem Fokus-Trap des NcModal der Suche; `OC.dialogs.filepicker` nutzt den gemeinsamen Trap-Stapel von `@nextcloud/dialogs` und ist sicher |
| Name `folder` | `path` wie Files | Files' `path` ist ein LIKE-Präfix ohne Trennzeichen (`FilesSearchProvider.php` stable33:150: `/Doc` trifft `/Documents`); eigener Name vermeidet falsche Gleichsetzung |
| Name `types` | `type` wie Files | Files' `type` ist ein Mimetyp-Präfix (`image`), andere Vokabel. `types` ist zugleich der Adressparameter der Ergebnisseite (`PageController.php:391`) |

**Installation:** keine.

## Package Legitimacy Audit

Diese Phase installiert keine externen Pakete (weder composer noch uv noch npm). slopcheck nicht ausgeführt, nicht nötig.

**Packages removed:** keine. **Packages flagged:** keine.

## Architecture Patterns

### System Architecture Diagram

```
Nutzer öffnet Unified Search (jede Seite)
   │
   ├─ Seite geladen: BeforeTemplateRenderedEvent(isLoggedIn) ──► Util::addScript('findling','unified-search') + addTranslations
   │                                                              │
   │                         DOMContentLoaded: OCA.UnifiedSearch vorhanden? ── nein ──► nichts (Legacy-Suche)
   │                                                              │ ja
   │                         registerFilterAction × 7 (6 Typen, 1 Ordner), appId findling, searchFrom findling
   │
   ├─ Klick auf Menüeintrag ──► Core: callback(apply) ──► Core: Chip in filteredProviders
   │                                │
   │                                └─ setTimeout 0 / Ordnerwahl ──► emit add-filter {id, filterParams:{types|folder}}
   │                                                                  │
   │                         Core: provider.extraParams = filterParams, debounce 300 ms
   │
   └─► GET /ocs/v2.php/search/providers/findling/search?term=..&types=pdf | &folder=/Projekte
          │
          Core SearchComposer.buildFilterList: nur deklarierte Namen ──► StringFilter (leer ⇒ HTTP 400!)
          │
          Provider::search: types ⇒ SearchFilters::TYPES ∩ Werte (still), folder ⇒ bereinigter Pfad oder null
          │
          SearchService::run
             ├─ Ordner auflösen: $userFolder->get(pfad) instanceof Folder? sonst Filter ignorieren
             ├─ Koordinaten: IFileAccess(ordner-id) + Unter-Mounts aus der Mountliste
             ├─ Runde: ExAppService::searchCandidates (Body unverändert, types wie bisher, KEIN folder)
             ├─ reduceIds: Cache-Einträge der Seite ⇒ außerhalb des Ordners verworfen ohne Recheck
             └─ Recheck: ($ordner ?? $userFolder)->getFirstNodeById(id) ⇒ readableNode ⇒ Treffer
          │
          SearchResult (paginated/complete), Tür "Alle Ergebnisse" mit types, ohne folder
```

### Recommended Project Structure
```
php/
├── js/unified-search.js              # NEU: Vanilla-Plugin, kein Bundler (Projektregel wie search.js/admin.js)
├── lib/Listener/LoadUnifiedSearchFiltersListener.php   # NEU: BeforeTemplateRenderedEvent
├── lib/AppInfo/Application.php       # registerEventListener ergänzen
├── lib/Search/Provider.php           # types/folder deklarieren und lesen, Tür mit types
├── lib/Service/SearchFilters.php     # Feld ?string $folder, gemeinsamer Typ-Parser
├── lib/Service/SearchService.php     # Ordnerumfang, Reduktion, Recheck im Unterbaum
├── lib/Controller/PageController.php # typeGroups() auf gemeinsamen Parser umstellen
├── l10n/*.js|*.json                  # 16 Dateien, neue Zeichenketten
└── tests/Unit/{Provider,SearchService,ExAppService}Test.php
backend/tests/test_type_vocabulary_parity.py   # NEU: PHP TYPES == Literal == TYPE_GROUPS
docs/search-filters.md                         # Abschnitt "In the unified search"
.github/workflows/deploy-harp.yml              # OCS-Probe mit types/folder auf 33/34/35
```

### Pattern 1: Filter deklarieren (Server)
```php
// Quelle: SearchComposer.php stable35:130-163, 276-285
#[\Override]
public function getSupportedFilters(): array {
	return [
		IFilter::BUILTIN_TERM, IFilter::BUILTIN_TITLE_ONLY,
		IFilter::BUILTIN_SINCE, IFilter::BUILTIN_UNTIL,
		self::FILTER_TYPES, self::FILTER_FOLDER,   // 'types', 'folder'
	];
}

#[\Override]
public function getCustomFilters(): array {
	return [
		new FilterDefinition(self::FILTER_TYPES, FilterDefinition::TYPE_STRING),
		new FilterDefinition(self::FILTER_FOLDER, FilterDefinition::TYPE_STRING),
	];
}
```
Regeln aus dem Kern: Jeder Name in `getSupportedFilters` braucht eine Definition, sonst `InvalidArgumentException('Invalid filter ...')` in `loadFilters()` (stable35:144-148) und damit ein Fehler der ganzen Providerliste, nicht nur von Findling. Custom-Namen kollidieren nur mit den sieben Kernnamen (`term, since, until, title-only, person, places, provider`, stable35:75-83), nicht mit Namen anderer Provider (Definitionen sind pro Provider, `registerCustomFilter` stable35:152-163). `types` und `folder` sind frei.

### Pattern 2: Werte still lesen (Provider)
```php
// Gleiches Muster wie titleOnly()/epochOf() in Provider.php:295-325
private function typesOf(ISearchQuery $query): array {
	$value = $query->getFilter(self::FILTER_TYPES)?->get();
	return is_string($value) ? SearchFilters::typesFrom($value) : [];   // Parser aus PageController::typeGroups() herausgezogen
}

private function folderOf(ISearchQuery $query): ?string {
	$value = $query->getFilter(self::FILTER_FOLDER)?->get();
	if (!is_string($value) || strlen($value) > self::MAX_FOLDER_LENGTH || preg_match('/[\x00-\x1F\x7F]/', $value)) {
		return null;
	}
	$path = '/' . trim($value, '/');
	return $path === '/' ? null : $path;   // Wurzel = kein Filter
}
```

### Pattern 3: Ordnerumfang in SearchService
```php
// Auflösen einmal pro Lauf, jeder Fehler = Filter ignoriert (Kriterium 3)
$scope = null;
if ($filters->folder !== null) {
	try {
		$node = $userFolder->get($filters->folder);      // wirft bei '..', fehlend, keine Rechte
		$scope = $node instanceof Folder && $node->isReadable() ? $node : null;
	} catch (\Throwable) {
		$scope = null;                                  // nie den Pfad loggen
	}
}

// Recheck: dieselbe Mechanik, engerer Wurzelpfad (Folder.php stable35:354-356)
$node = self::readableNode(($scope ?? $userFolder)->getFirstNodeById($candidate['fileId']));
```
Ohne Ordner bleibt der Aufruf byte-gleich `readableFile($userFolder, $id)` (Regressionstest). `($scope)->getFirstNodeById` löst auch den Fall, dass dieselbe Datei über zwei Pfade sichtbar ist (eigener Speicher plus Share): `$userFolder->getFirstNodeById` könnte den Pfad außerhalb liefern, `isSubNode` danach würde den Treffer fälschlich verwerfen.

### Pattern 4: Billige Reduktion im Ordner (keine zusätzliche Abfrage pro Seite)
```php
// Koordinaten einmal pro Lauf
$root = $this->fileAccess->getByFileId($scope->getId());          // (storageId, Rohpfad im oc_filecache)
$coords = [[$root->getStorageId(), $root->getPath()]];
$prefix = $scope->getPath() . '/';                                 // '/alice/files/Projekte/'
foreach ($mounts as $mount) {                                      // aus storageIdsOfUser(), schon geladen
	if (str_starts_with($mount->getMountPoint(), $prefix)) {
		$coords[] = [$mount->getStorageId(), $mount->getRootInternalPath()];
	}
}
// in reduceIds: Eintrag ist drin, wenn storageId passt und (root === '' || path === root || str_starts_with(path, root . '/'))
```
Alle Vergleiche im selben Rohpfadraum (`oc_filecache.path`), der auch für Gruppenordner (Jail auf `__groupfolders/<id>`) und Shares (Quellspeicher) stimmt. Die Reduktion bleibt Beschleuniger, nie Grenze: Liefert sie `null`, entscheidet allein der Recheck im Unterbaum.

### Pattern 5: Frontend-Plugin (Vanilla, kein Bundler)
```javascript
// Quelle Mechanik: folderSearch.ts (Files), UnifiedSearchModal.vue stable33:674-704 und 828-845
'use strict'
document.addEventListener('DOMContentLoaded', () => {
	const api = window.OCA && window.OCA.UnifiedSearch
	if (!api || typeof api.registerFilterAction !== 'function') {
		return   // Legacy-Suche (unified_search.enabled) oder API fehlt: still nichts
	}
	const emit = (detail) => setTimeout(() => window._nc_event_bus?.emit('nextcloud:unified-search:add-filter', detail), 0)
	for (const [group, label] of TYPE_ENTRIES) {          // sechs Einträge, Reihenfolge = SearchFilters::TYPES
		const id = 'findling-type-' + group
		api.registerFilterAction({
			id, appId: 'findling', searchFrom: 'findling', label, icon: OC.imagePath('findling', 'app'),
			// IMMER senden, auch bei apply === false: der Kern entfernt einen erneut
			// geklickten Chip und legt ihn ohne extraParams neu an (Pitfall 2)
			callback: () => emit({ id, appId: 'findling', searchFrom: 'findling', filterUpdateText: label, filterParams: { types: group } }),
		})
	}
	// Ordner: OC.dialogs.filepicker(title, cb, false, ['httpd/unix-directory'], true,
	//   OC.dialogs.FILEPICKER_TYPE_CHOOSE, '/', { allowDirectoryChooser: true })
	// cb bekommt den nutzerrelativen Pfad, '/' für die Wurzel ⇒ filterParams: {} (nie leerer String)
})
```

### Anti-Patterns to Avoid
- **Ordnerfilter über `files.path` im Backend:** Pfad eines einzigen Nutzers, siehe Befund 3.
- **Ordnerwert ins Backend schicken:** `SearchRequest` hat `extra="forbid"` (`api/search.py:87`); ein neues Feld ohne Gegenstück wird 422 und damit eine leere Gruppe. `ExAppService` baut den Body aus expliziten Schlüsseln (`:460-469`), das muss so bleiben.
- **Emit direkt im callback:** Der Kern ruft `callback` vor dem `push` in `filteredProviders` auf (stable33:679-702, stable35:1217-1240); ein synchrones Emit findet keinen Chip und geht verloren.
- **Plugin-ID gleich `findling`:** kollidiert mit der Provider-ID in `existingFilterIndex`/`providers.findIndex`. IDs `findling-type-<gruppe>` und `findling-folder`.
- **Eigenes `<dialog>` im offenen Such-Modal:** Fokus-Trap des NcModal zieht den Fokus zurück.
- **Pfad oder Suchbegriff im Log:** Projektregel, nur Codes und Typnamen.

## Don't Hand-Roll

| Problem | Nicht bauen | Stattdessen | Warum |
|---------|-------------|-------------|-------|
| Ordnerauswahl | eigener Baum-Browser | `OC.dialogs.filepicker` mit `httpd/unix-directory` | Rechte, Shares, Gruppenordner, Fokus-Trap, Barrierefreiheit gelöst |
| Unterbaum-Rechteprüfung | Pfadvergleich als Grenze | `$ordner->getFirstNodeById()` | identisch zum heutigen Recheck, nur engerer Wurzelpfad |
| Pfadnormalisierung / `..` | eigener Normalisierer | `Folder::get()` (normalisiert, lehnt ungültige Pfade mit Exception ab) | gleiche Regeln wie die Files-App |
| Typvokabular | zweite Tabelle in PHP oder JS | `SearchFilters::TYPES` (PHP), `TYPE_GROUPS` (Backend), Parität per Test | Projektregel "eine Vokabel" (`SearchFilters.php:28-33`) |
| Event-Bus | eigenes CustomEvent | `window._nc_event_bus.emit` (globaler SimpleBus von `@nextcloud/event-bus`) | der Core abonniert genau dort |

## Common Pitfalls

### Pitfall 1: Custom Filter ohne Plugin ist unsichtbar
**What goes wrong:** Nur `getCustomFilters()` befüllt, nichts erscheint im Dialog. **Why:** Das Frontend kennt nur date/person/provider (stable33:538-553, stable35:1083-1088). **How to avoid:** Plugin-Skript ist Pflichtteil von USRCH-01/02. **Warning signs:** `/ocs/v2.php/search/providers` listet `types`, die UI nicht.

### Pitfall 2: Chip verliert den Filter beim zweiten Klick
**What goes wrong:** Ein schon aktiver Eintrag wird erneut gewählt; der Kern entfernt den Chip und legt eine frische Kopie ohne `extraParams` an (stable33:692-701), die Suche läuft ungefiltert unter dem Label "PDF". **How to avoid:** Typ-Callbacks senden immer; Ordner-Callback merkt sich den letzten Ordner im Modulzustand und sendet ihn bei `apply === false` erneut. **Warning signs:** Playwright-Abnahme: Eintrag zweimal klicken, Trefferliste prüfen.

### Pitfall 3: Leere Werte enden im Kern mit HTTP 400
**What goes wrong:** `?folder=` oder `?types=` erzeugt `StringFilter('')`, das wirft (`lib/private/Search/Filter/StringFilter.php`), der Controller antwortet 400 (`UnifiedSearchController.php` stable35:107-111). Findling wird nie gefragt. Array-Werte (`types[]=pdf`) treffen auf `buildFilter(string $name, string $value)` (stable35:305) und sind ebenfalls nicht unter Findlings Kontrolle. **How to avoid:** Plugin sendet nie einen leeren String (Wurzel = kein Parameter). Kriterium 3 für "leer" auf die Werte beziehen, die den Provider erreichen; Verhalten des Kerns dokumentieren. **Owner-Frage**, siehe Offene Fragen 1.

### Pitfall 4: Enger Ordner, leere erste Seite
**What goes wrong:** Heute prüft ein Dialoglauf bei `limit` 5 höchstens 3 Runden × 20 Kandidaten (`fetchLimit` `SearchService.php:243`, M4-Deckel) und 10 Rechecks. Liegen die Treffer im gewählten Ordner tiefer im Ranking, bleibt die Gruppe leer, und `Provider::search` gibt bei `hits === []` ein `complete([])` zurück (`Provider.php:218-236`), auch wenn mehr da wäre. **How to avoid:** Im Ordnermodus kostet ein verworfener Kandidat keinen Recheck; dort `fetchLimit` auf `MAX_LIMIT` (100) heben und Runden innerhalb des 2,5-s-Budgets erhöhen (Vorschlag 6, bleibt unter `MAX_CONTAINER_OFFSET` 1200). Begründung im M4-Kommentar ergänzen. Messaufgabe im Plan: Ordner mit 1 Prozent Trefferanteil. **Warning signs:** "keine Treffer" im Dialog, Ergebnisseite findet welche.

### Pitfall 5: Skript nur auf der Files-Seite
**What goes wrong:** Files lädt sein Plugin nur über das eigene Event `LoadSearchPlugins` (`ViewController.php` stable35:199). Wer daran hängt, hat den Filter nur in Files. **How to avoid:** `BeforeTemplateRenderedEvent` mit `isLoggedIn()`, dazu `Util::addTranslations('findling')`, sonst zeigt `t()` auf fremden Seiten Englisch.

### Pitfall 6: Mehrere Findling-Chips = mehrere Gruppen
**What goes wrong:** Jeder Plugin-Chip wird einzeln mit seinen eigenen `extraParams` abgefragt (stable33:510-518, stable35:1055-1059). PDF plus Ordner ergibt zwei Gruppen, nicht die Schnittmenge. **How to avoid:** Als Grenze dokumentieren; Kombination nur über Datum (Kernfilter, wird pro Gruppe mitgeschickt) möglich. Siehe Offene Fragen 2.

### Pitfall 7: Gate-Ketten
- PHP-Baumhash: jede `*.php`-Änderung unter `php/` bewegt `PHP_TREE_HASH_TODAY`/`PHP_FILES_TODAY` (`backend/tests/test_measurement_scripts.py:839-840`) samt Journal-Kommentar; neue Dateien zählen mit.
- l10n: neue Zeichenketten in 16 Katalogdateien (8 Sprachen × `.js`/`.json`), Katalog-Gates in `test_admin_ui_contract.py` (Sie-Form im Deutschen).
- `ProviderTest` Zeile 547 und 655 werden umgedreht, nicht gelöscht.
- PHPUnit läuft nur gegen stable34 (`php.yml` `SERVER_VERSION: stable34`); 33 und 35 nur über deploy-harp.

### Pitfall 8: Legacy-Suche und künftige API-Änderung
`OC.dialogs.filepicker` ist seit 27.1.0 deprecated; mit `unified_search.enabled` lädt der Kern die Legacy-Suche ohne Plugin-API (`TemplateLayout.php` stable35:89-96). Plugin muss beides per Feature-Erkennung überspringen, ohne Fehler.

## Code Examples
Siehe Pattern 1 bis 5. Ergänzend, die Tür im Provider:
```php
// Provider::entryPoint: types mitgeben (Seite zeigt sie als Chips), folder bewusst nicht (Seite hat keinen Ordnerfilter)
['query' => $term] + ($titleOnly ? ['names' => '1'] : []) + ($types !== [] ? ['types' => implode(',', $types)] : [])
```

## State of the Art

| Alt | Aktuell | Wann | Wirkung |
|-----|---------|------|---------|
| Places-Menü | Menü heißt "Type" (`UnifiedSearchModal.vue` stable35:52), gleiche Plugin-API | NC 35 | Typ-Einträge passen dort sprachlich besser |
| `find()` pro Provider | `buildCategoryParams` plus Controller, gleiche `extraQueries` | NC 35 | Paging behält die Filter (stable35:1056 Kommentar) |
| `OC.dialogs.filepicker` | `@nextcloud/dialogs` getFilePickerBuilder | deprecated 27.1.0, nicht entfernt in 35 | ohne Bundler nur der Legacy-Wrapper erreichbar |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `oc_filecache`-Rohpfade aus `IFileAccess` und `ICachedMountInfo::getRootInternalPath()` liegen im selben Raum, auch für Gruppenordner (groupfolders 21) und externe Speicher | Pattern 4 | Reduktion verwirft zu viel oder zu wenig; Korrektheit bleibt (Recheck im Unterbaum), nur Trefferquote leidet. Im Plan mit Gruppenordner und Share testen [ASSUMED] |
| A2 | Sechs Runden × 100 Kandidaten passen warm ins 2,5-s-Budget | Pitfall 4 | Gruppe bricht am Budget ab, weniger Treffer. Messen [ASSUMED] |
| A3 | `window._nc_event_bus` ist zum Klickzeitpunkt der globale SimpleBus | Pattern 5 | Emit verpufft; Feature-Erkennung plus Playwright-Abnahme deckt es auf [ASSUMED, Quelle Bibliothek gelesen] |
| A4 | `Folder::get()` wirft bei `..`-Segmenten | Pattern 3 | Traversal bliebe trotzdem ohne Wirkung, weil der Recheck im (dann falschen) Unterbaum des Nutzers läuft; nie fremde Dateien [ASSUMED] |

## Open Questions (RESOLVED)

1. **Kriterium 3 und leere Parameter (Owner)**
   - Bekannt: Leere Strings und Arrays weist der Kern mit 400 ab, bevor Findling läuft; das Plugin sendet nie leer.
   - Empfehlung: Kriterium 3 lesen als "jeder Wert, der den Provider erreicht"; Kernverhalten in `docs/search-filters.md` und als Regressionsprobe (Status 400 erwartet) festhalten.
   - RESOLVED: D-32-01 (leere Werte weist der Kern mit 400 ab; Probe in 32-06, Doku in docs/search-filters.md)
2. **Typ plus Ordner gleichzeitig (Owner)**
   - Bekannt: Getrennte Chips ergeben getrennte Gruppen. Ein kombinierter Dialog bräuchte eigene Modal-UI.
   - Empfehlung: nicht in Phase 32; als Grenze dokumentieren, Kombination Typ plus Datum und Ordner plus Datum funktioniert.
   - RESOLVED: D-32-02 (Typ und Ordner als getrennte Gruppen, Grenze dokumentiert)
3. **Backend-Hälfte von Kriterium 3 (Owner, kurz)**
   - Bekannt: Container lehnt unbekannte Gruppen mit 422 ab, bewusst und getestet.
   - Empfehlung: so lassen; Backend-Beleg = Paritätstest plus "leere Liste gleich fehlendes Feld".
   - RESOLVED: D-32-03 (Container-422 bleibt, Backend-Beleg über Paritätstest)
4. **Label-Wortlaut der sieben Einträge** (de/en/fr): Entwurf im Plan, Owner sieht ihn bei der Playwright-Abnahme.
   - RESOLVED: D-32-04 (Wortlaut-Abnahme per Playwright in 32-07)

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker | Dev-Nextcloud, HaRP | ja | 29.5.2 | , |
| Dev-Nextcloud | Playwright-Abnahme | ja (`findling-nextcloud`, `findling-harp-nextcloud`) | 34.0.3 | 33/35 nur in CI |
| uv | Backend-Gates | ja | 0.11.7 | , |
| PHP lokal | PHPUnit | nein | , | CI `php.yml` (stable34) |
| node | optional JS-Syntaxcheck (`node --check`) | ja | 22.21.0 | , |
| gh | CI-Läufe | ja | 2.92.0 | , |

## Validation Architecture
Übersprungen (`workflow.nyquist_validation: false`). Teststrategie trotzdem für den Planer:
- **PHPUnit (`php/tests/Unit`)**: Provider deklariert sechs Namen und zwei gültige Definitionen (Konstruktion wirft nicht, Namen nicht in den sieben Kernnamen); `types` Parser (`pdf`, `PDF, images`, `videos`, `,,,`, überlang, Nicht-String) ⇒ kanonische Liste oder leer; `folder` (`/`, Steuerzeichen, überlang) ⇒ null; SearchService: Ordnermodus verwirft außerhalb ohne Recheck, Recheck über `$scope->getFirstNodeById`, ohne Ordner exakt `$userFolder->getFirstNodeById`, manipulierter/fehlender/Datei-Ordner ⇒ identische Treffer wie ohne Filter; ExAppService: Body enthält nie `folder`.
- **pytest**: neuer Paritätstest PHP `SearchFilters::TYPES` (aus Quelltext gelesen, wie `test_allowlist_parity.py`) == `SearchRequest.types`-Literal == `TYPE_GROUPS`-Schlüssel; `types: []` liefert dieselben Kandidaten wie ohne Feld; Vertragstest über `php/js/unified-search.js` (sechs IDs in TYPES-Reihenfolge, Feature-Erkennung, `setTimeout`, kein leerer Wert, kein `console.log`).
- **deploy-harp (33/34/35)**: `/ocs/v2.php/search/providers` enthält bei `findling` `"types":"string","folder":"string"`; OCS-Suche mit `&types=pdf` liefert nur PDF-Saat, `&folder=/<Saatordner>` nur Dateien darunter, `&types=videos` und `&folder=/gibtsnicht` dieselben IDs wie ohne Filter, `&folder=` Status 400 (Kernverhalten belegt).
- **Playwright mit Owner** auf der Dev-Instanz: Menüeinträge sichtbar, Chip, Ordnerwahl, Doppelklick-Fall, Tür trägt `types`.

## Security Domain

| ASVS | Applies | Control |
|------|---------|---------|
| V4 Access Control | ja | einziger Recheck `getFirstNodeById`, im Ordnermodus auf dem Unterbaum des eigenen Nutzerordners; Reduktion nie Grenze |
| V5 Input Validation | ja | geschlossene Menge für `types`, Längen- und Steuerzeichengrenze plus `Folder::get()` für `folder`, Fehler ⇒ ignorieren |
| V7 Logging | ja | keine Pfade, keine Suchbegriffe in Logs |
| V2/V3/V6 | nein | unverändert |

| Muster | STRIDE | Gegenmaßnahme |
|--------|--------|---------------|
| Pfad-Traversal im `folder` | Elevation | `Folder::get` relativ zum Nutzerordner, Recheck im Unterbaum, nie ein Pfad außerhalb `/uid/files` |
| Existenz-Orakel über fremde Ordner | Information Disclosure | nicht auflösbarer Ordner ⇒ gleiche Antwort wie ohne Filter |
| Neues Wire-Feld schleust Werte in den Query-Builder | Tampering | kein neues Feld; `types` bleibt Literal-Menge mit `extra=forbid` |
| Skript auf jeder Seite | Tampering | statische Datei, CSP-Nonce durch `Util::addScript`, kein `innerHTML`, kein Eval |

## Sources

### Primary (HIGH)
- nextcloud/server stable33/stable34/stable35 (raw.githubusercontent, 2026-10-12): `lib/private/Search/SearchComposer.php`, `lib/public/Search/FilterDefinition.php`, `lib/private/Search/FilterFactory.php`, `lib/private/Search/Filter/StringFilter.php`, `core/Controller/UnifiedSearchController.php`, `core/src/components/UnifiedSearch/UnifiedSearchModal.vue`, `core/src/unified-search.ts`, `core/src/store/unified-search-external-filters.js`, `core/src/services/UnifiedSearchService.js`, `core/src/OC/dialogs.js`, `apps/files/src/plugins/search/folderSearch.ts`, `apps/files/lib/Search/FilesSearchProvider.php`, `apps/files/lib/Listener/LoadSearchPluginsListener.php`, `lib/private/Files/Node/Folder.php`, `lib/public/Files/Cache/IFileAccess.php`, `lib/public/Files/Config/ICachedMountInfo.php`, `lib/private/AppFramework/Middleware/AdditionalScriptsMiddleware.php`, `lib/private/TemplateLayout.php`
- nextcloud-libraries/nextcloud-event-bus `lib/index.ts` (globaler Bus)
- Repo: `php/lib/Search/Provider.php`, `php/lib/Service/{SearchFilters,SearchService,ExAppService,QueueService}.php`, `php/lib/Controller/PageController.php`, `backend/src/findling/api/search.py`, `query/rewrite.py`, `store/schema.sql`, `store/repo.py`, `index/schema.py`, Tests und Workflows wie zitiert

### Secondary / Tertiary
- keine

## Metadata
**Confidence breakdown:** Server/Frontend-Mechanik HIGH (Quelltext aller drei Zweige), PHP-Ordnerdesign HIGH für Korrektheit, MEDIUM für Trefferquote (A1, A2 ungemessen), Pitfalls HIGH.
**Research date:** 2026-10-12. **Valid until:** 2026-11-12 (Frontend der Unified Search wird in 35 aktiv umgebaut; vor dem Bau stable35 erneut auf `registerFilterAction` prüfen).
