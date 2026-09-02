# Phase 4: Admin-Sichtbarkeit und Diagnose - Research

**Researched:** 2026-09-02
**Domain:** Nextcloud Admin-Settings (NC 32-34), PHP-Companion-App, ExApp-Statusrouten, Deckungsgrad-/Diagnose-Aggregation
**Confidence:** HIGH für die Nextcloud-Mechanik und die Vertragslage im eigenen Code, MEDIUM für die Schätz-Heuristik, LOW für absolute Dauer-Zahlen auf ARM

## Summary

Phase 4 baut keine neue Indexfähigkeit, sie baut eine Lese-Sicht plus vier Schalter. Die technische Kernfrage ist deshalb nicht "wie geht Nextcloud-Settings", sondern **wo die Wahrheit über eine Datei liegt**. Die Antwort im bestehenden Code ist unangenehm, aber eindeutig: sie liegt an drei Orten. `findling_queue` (PHP) weiß, was wartet und was gerade läuft. `findling_file_state` (PHP) weiß, was übersprungen oder gescheitert ist, und zwar mit Grund, und überlebt einen ausgeschalteten Container. Die `files`-Tabelle im Container weiß, was indexiert ist, ob OCR gelaufen ist und ob ein Grabstein liegt. Kein einzelner Ort kann Erfolgskriterium 2 beantworten. Die Pro-Datei-Diagnose ist deshalb eine **Zusammenführung mit fester Vorrangregel**, kein einziger Datenbankzugriff, und genau diese Vorrangregel ist die wichtigste Entscheidung der Phase.

Die zweite Kernerkenntnis: **keiner der vier ADM-04-Schalter braucht einen Transportweg in den Container.** Ordner-Ausschlüsse, Größen-Cap, Team Folders und External Storage werden alle vier an der PHP-Quelle durchgesetzt (Crawl, Event-Listener, `StorageService::MOUNT_PROVIDERS`, Reconcile-Slice). Der Container erfährt die Wirkung automatisch, weil er seine Arbeit ausschließlich aus PHP-Antworten zieht: `GET /mounts`, `GET /files/slice`, `GET /queues/documents`. Der in CONTEXT.md unter Claude's Discretion gestellte Punkt "Transportweg der Settings von PHP zum Container" hat damit die Antwort "kein Transport". Die einzige Ausnahme ist der Größen-Cap, weil der Container ihn ein zweites Mal durchsetzt (`nc/client.py`, `extract/dispatch.py`) und ein PHP-Wert oberhalb von `FINDLING_MAX_FILE_BYTES` wirkungslos wäre. Dafür gibt es eine klare Lösung: klemmen und anzeigen.

Die dritte Erkenntnis betrifft ein Gate: `backend/tests/test_php_trust_boundary.py` (Gate B) fordert für **jede** Methode in `php/lib/Controller/*.php` mit einem `ApiRoute`-Attribut zusätzlich `ExAppRequired` und `rejectForeignCaller()` als erste Anweisung, und es fordert außerdem, dass jeder Controller mindestens eine Route trägt. Ein neuer Admin-Controller verletzt dieses Gate in beiden Richtungen. Gate B muss in derselben Arbeit erweitert werden, die den Controller anlegt, um zwei Routenklassen zu unterscheiden. Das ist keine Aufweichung, sondern eine Verschärfung: die Admin-Klasse muss beweisen, dass sie **kein** `NoAdminRequired`, `PublicPage` oder `NoCSRFRequired` trägt.

**Primary recommendation:** Eine Settings-Section plus eine `ISettings`-Klasse über `<settings>` in `php/appinfo/info.xml` (nach `<commands>`), ein `templates/admin.php` mit `Util::addScript` und `IInitialState` für den Erstbefüllung, ein `js/admin.js` in Vanilla-JS, das über `document.head.dataset.requesttoken` gegen einen admin-only PHP-Controller pollt. Der Controller ist der einzige Ort, der beide Datenbanken und den Container zusammenführt. Die Schätzung entsteht aus Zählern, die der bestehende Crawl mitschreibt, und kalibriert Dauer und Platzbedarf am laufenden Lauf statt an geratenen Konstanten.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**UI-Ort und Technik**
- **D-01:** Die Admin-Seite lebt als eigene Sektion "Findling" in den Nextcloud-Verwaltungseinstellungen, registriert von der PHP-Companion-App (ISettings + Section). Der PHP-Controller proxied die Zahlen der ExApp (/status plus neue Diagnose-/Schätz-Routen). KEINE eigene ExApp-UI (kein ui.top_menu), kein zweites UI-Universum.
- **D-02:** Frontend ist Vanilla JS + PHP-Template + Nextcloud-CSS. KEIN npm/Build-Step im Companion-Repo (bleibt reines PHP). Umfang der Seite: Zahlen, Tabelle, Formulare; das trägt ohne Framework.

**Fehlerliste und Pro-Datei-Diagnose**
- **D-03:** Der Privacy-Grundsatz aus status.py bleibt Vertragsbestandteil: der Container liefert nur fileids, Zustände, Gründe und Zahlen, NIE Dateinamen oder Pfade. Die PHP-Seite löst fileid zu Pfad zur Anzeigezeit auf (Besitzersicht); die Fehlerliste zeigt dem Admin lesbare Pfade.
- **D-04:** Die Diagnose-Eingabe (ADM-02) akzeptiert Pfad ODER fileid in einem Feld; zusätzlich verlinkt jeder Fehlerlisten-Eintrag direkt in die Diagnose. Grund-Taxonomie = bestehende Verdikt-Reasons beidseitig gespiegelt (FileStateService::REASONS), inklusive `indexed(truncated)` aus Phase-3-D-08; neuer Grund `excluded` für D-06.

**Vorab-Schätzung**
- **D-05:** Kein Bestätigungs-Gate: der Erstindex startet weiter von selbst (Zero-Config-Kernversprechen). Die Schätzung entsteht als schneller Metadaten-Scan VOR der ersten Extraktion (Anzahl + Größe aus der NC-Dateiliste, OCR-Anteil per MIME-/Textlayer-Heuristik, Dauer aus den gemessenen Phase-3-Raten, Platzbedarf) und steht ab Minute 1 informativ auf der Statusseite, aktualisiert sich mit dem Fortschritt.

**Toggle-Mechanik**
- **D-06:** Ordner-Ausschlüsse sind Pfad-Präfixe (Liste von Ordner-Pfaden, Präfix-Match). BEWUSST keine Glob-/Regex-Muster: erklärbar, kein Fehlbedienungsrisiko bei der Zero-Config-Zielgruppe. Ausgeschlossene Dateien erscheinen in der Diagnose mit Grund `excluded`, nicht stumm.
- **D-07:** Ein neuer Ausschluss räumt Bestand AKTIV: der nächste Lauf/Reconcile entfernt Inhalte und ACL-Einträge unter dem Präfix aus dem Index. Der Index spiegelt die Regeln immer; keine Geisterinhalte. Mechanik konsistent mit der Unshare-/Lösch-Räumung aus Phase 3.
- **D-08:** Toggle-Satz genau nach ADM-04: Ordner-Ausschlüsse, Größen-Cap (heute FINDLING_MAX_FILE_BYTES), Team Folders an/aus (Default AN), External Storage an/aus (Default AUS). Gespeichert PHP-seitig (appconfig); der Container übernimmt die Werte beim nächsten Lauf ("der nächste Lauf hält sich daran"), kein Live-Neustartzwang.

### Claude's Discretion

- Transportweg der Settings von PHP zum Container (Mitgabe beim Queue-Poll vs. eigener Config-Endpunkt) und Cache-/Invalidierungsmechanik.
- Details der Schätz-Heuristik (OCR-Anteil, Raten) und die Aktualisierungs-Kadenz der Statusseite (Polling-Intervall der UI).
- Fehlerlisten-Pagination, Sortierung, Obergrenzen (MAX_LIST_LENGTH-Gotcha aus CR-01 beachten).
- Zuschnitt der neuen ExApp-Routen (Diagnose per fileid, estimate) und deren Response-Schemas; ADMIN-Access-Level in info.xml wie bei /status.
- Ob ein occ-Kommando als Zweitzugang zur Diagnose dazukommt (nice-to-have, kein Muss).

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope. (Betriebsthema außerhalb der Phase, am 02.09. direkt erledigt: Dependabot-PRs #4/#5 gemergt, GitHub-Ruleset protect-main aktiv.)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ADM-01 | Statusseite: Indexfortschritt, Deckungsgrad (indexierte vs. indexierbare Dateien), Fehlerliste | Architektur-Muster 1 (Drei-Quellen-Aggregation), Muster 2 (Deckungsgrad-Definition), Muster 6 (Statusseiten-Rendering ohne Build-Step); Zahlenquellen in "Standard Stack" Tabelle "Datenquellen"; Pitfall 3 (zwei Zählwerke für skipped/failed), Pitfall 8 (kein created_at in findling_queue) |
| ADM-02 | Pro-Datei-Diagnose mit Grund | Muster 1 (Vorrangregel über drei Quellen), Muster 3 (fileid -> Pfad über IUserMountCache, ohne Admin-Leseberechtigung), Muster 4 (Pfad -> fileid), Code-Beispiel 3 und 4; Pitfall 1 (`mime_not_allowed` wird nie geschrieben, muss live berechnet werden), Pitfall 6 (Grabstein bedeutet nicht `gone`) |
| ADM-03 | Vorab-Schätzung vor dem Erstindex | Muster 5 (Crawl schreibt Scan-Zähler mit, keine zweite Wanderung), Muster 7 (Selbstkalibrierung von Dauer und Platzbedarf); gemessene Raten in "Standard Stack" Tabelle "Gemessene Raten"; Open Question 2 (Kriterium 3 sagt "VOR dem Erstindex", D-05 sagt "ab Minute 1") |
| ADM-04 | Ausschluss-Regeln und Toggles | Muster 8 (alle vier Schalter greifen PHP-seitig, kein Transport in den Container), Muster 9 (Räumung über SubtreeExpandJob kind=delete plus Reconcile als Netz), Muster 10 (appconfig plus optionaler Config-Lexicon); Pitfall 2 (Container setzt den Größen-Cap ein zweites Mal durch), Pitfall 4 (Ausschluss-Pfadraum muss für Crawl und Event-Listener identisch sein), Open Question 1 (Pfadraum der Ausschlüsse) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

Actionable directives, die der Planner prüfen muss:

| Direktive | Quelle | Konsequenz für Phase 4 |
|---|---|---|
| Sprache: Code und README Englisch, Projektkommunikation Deutsch; keine Em-Dashes; echte Umlaute nur in deutscher Prosa, nie in Code | CLAUDE.md Constraints | PHP-Klassennamen, Methodennamen, Kommentare und Code-Docblocks Englisch. Admin-UI-Strings: siehe Open Question 3. ASCII-Bezeichner überall. |
| Qualitätsgates: ruff-Vollregelsatz, pyright basic, vulture, CI-Gates, lokal grün vor Commit | CLAUDE.md Constraints | Neue Backend-Module (`api/diagnose.py`, `api/estimate.py`) müssen ruff-, pyright- und vulture-clean sein. Ein ungenutztes Enum-Mitglied `Reason.EXCLUDED` ist durch `STATE_REASONS` referenziert und damit vulture-sicher. |
| Security/Privacy: Berechtigungs-Durchgriff strikt; keine Inhalte verlassen den Server; kein Telemetrie-Phoning | CLAUDE.md Constraints | Die Diagnose zeigt Metadaten und Verdikte, NIE Dateiinhalt und NIE ein Snippet. Snippets bleiben an SRCH-02 gebunden (nur nach bestandenem Recheck). |
| Nextcloud-Fenster min-version 32, max-version 35 | CLAUDE.md Stack | `OCP\Settings\ISection` existiert in NC 32-34 nicht mehr. Nur `IIconSection` verwenden. Siehe Pitfall 5. |
| PHP >= 8.2 | php/composer.json, info.xml | `#[\Override]` (PHP 8.3) NICHT verwenden, obwohl der Nextcloud-Kern es benutzt. |
| Eigenes Rechtemodell in Python: nie | CLAUDE.md What NOT to Use | Die Diagnose entscheidet keine Berechtigung. Sie ist admin-only und liest Metadaten; das ist keine Suche und braucht keinen Recheck. |
| GSD-Workflow: keine direkten Repo-Edits außerhalb eines GSD-Kommandos | CLAUDE.md Workflow | Betrifft die Ausführung, nicht die Recherche. |
| Statusseite: eine Seite, wenige Schalter, alles Weitere hinter "Erweitert" | .planning/research/PITFALLS.md:399 | Kein Formular mit 20 Optionen. Genau die vier Schalter aus D-08, nichts darüber. |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Statusseite rendern (HTML, Labels, Tabelle) | Frontend Server (PHP-Template) | — | Kein Build-Step (D-02); Nextcloud rendert das Template in die Settings-Seite. |
| Zahlen abholen und aktualisieren | Browser / Client (Vanilla JS) | Frontend Server (IInitialState für den ersten Aufschlag) | Erstbefüllung ohne Netzrunde, Aktualisierung per Polling. |
| Aggregation der Zahlen aus drei Quellen | API / Backend (PHP-Controller + Service) | — | Nur PHP sieht beide Datenbanken und den Container. Eine Aggregation im Browser wäre drei Requests und eine vierte Wahrheit. |
| fileid -> Pfad, Pfad -> fileid | API / Backend (PHP) | — | D-03: der Container darf keinen Pfad ausliefern. Nur Nextcloud kennt Mounts und Besitzer. |
| Verdikte `skipped`/`failed` mit Grund | Database / Storage (`findling_file_state`, Nextcloud-DB) | Container-`files`-Tabelle (zweite Kopie) | Überlebt einen ausgeschalteten Container (QueueController-Docblock). |
| Verdikt `indexed` und `indexed(truncated)`, `ocr_used`, Grabstein | Database / Storage (Container-`state.db`) | — | PHP schreibt niemals `indexed`; siehe ReconcileController-Docblock. |
| Wartend / laufend | Database / Storage (`findling_queue`) | — | Der Arbeitsvorrat liegt in Nextcloud (IDX-03). |
| Index-Dokumentzahl, Versionsmarken, freier Platz, Indexgröße | API / Backend (Container, `GET /status`) | — | Nur der Container sieht das Volume und den Tantivy-Index. |
| Deckungsgrad-Nenner (indexierbare Dateien) | Database / Storage (Nextcloud filecache über `IFileAccess`) | Frontend Server (Crawl-Job als Zähler) | Die Dateiliste ist die Wahrheit; PITFALLS.md:44. |
| Schalterwerte speichern | Database / Storage (`oc_appconfig`) | — | D-08. |
| Schalter durchsetzen (Ausschluss, Cap, Mounts) | API / Backend (PHP: Crawl, Event-Listener, StorageService) | Container (Cap ein zweites Mal, Verteidigung in der Tiefe) | Siehe Muster 8. |
| Bestand räumen nach neuem Ausschluss | API / Backend (PHP: SubtreeExpandJob kind=delete) | Container (Poller `_forget`), Reconcile als Netz | D-07, wiederverwendet Phase-3-Mechanik unverändert. |

## Standard Stack

### Core

Phase 4 installiert **keine** neuen Bibliotheken. Der Stack sind Nextcloud-Server-Schnittstellen, alle im deklarierten Fenster NC 32-34 vorhanden.

| Schnittstelle | Verfügbar seit | Zweck | Warum das der Standard ist |
|---|---|---|---|
| `<settings><admin>` / `<admin-section>` in `appinfo/info.xml` | seit NC 20 | Registrierung der Settings-Klassen | `OCP\AppFramework\Bootstrap\IRegistrationContext` hat KEIN `registerSettings()`. `AppManager::loadApp()` liest die Klassen aus `info.xml` und ruft `ISettingsManager::registerSetting('admin', ...)`. [VERIFIED: nextcloud/server stable34 lib/private/App/AppManager.php:514-524] |
| `OCP\Settings\ISettings` | @since 9.1 | `getForm(): TemplateResponse`, `getSection(): ?string`, `getPriority(): int` | Die einzige Schnittstelle, die ein Formular in eine Verwaltungssektion einhängt. [VERIFIED: lib/public/Settings/ISettings.php] |
| `OCP\Settings\IIconSection` | @since 12 | `getID()`, `getName()`, `getPriority()`, `getIcon()` | Eigene Sektion "Findling" in der Settings-Navigation. **`ISection` existiert in NC 30-34 nicht.** [VERIFIED: GitHub contents API, lib/public/Settings auf stable32/33/34] |
| `OCP\AppFramework\Http\TemplateResponse` mit `RENDER_AS_BLANK` (`''`) | @since 20 | Rendert nur den Formularkörper, nicht ein volles Layout | Kernmuster von `apps/updatenotification`. [VERIFIED: lib/public/AppFramework/Http/TemplateResponse.php:34] |
| `OCP\AppFramework\Services\IInitialState` | @since 20.0.0 | `provideInitialState(key, data)` | Erstbefüllung ohne Netzrunde. Landet als `<input type="hidden" id="initial-state-findling-<key>" value="<base64(json)>">`. [VERIFIED: core/templates/layout.initial-state.php + lib/private/InitialStateService.php:118-129, identisch auf stable32 und stable34] |
| `OCP\Util::addScript($app, $file)` | @since 4.0.0 | Lädt `<app>/js/<file>.mjs`, Fallback `<app>/js/<file>.js` | Kein Bundler nötig. Der Aufruf gehört ins Template, nicht in `getForm()`. [VERIFIED: lib/public/Util.php:128 + lib/private/Template/JSResourceLocator.php `appendScriptIfExist`] |
| `document.head.dataset.requesttoken` (JS) | NC 32-34 | CSRF-Token für `fetch` | `core/src/OC/requesttoken.ts` liest genau dieses Attribut; der Servercheck liest den Header `requesttoken`. [VERIFIED: core/src/OC/requesttoken.ts + lib/private/AppFramework/Http/Request.php:459-464] |
| `OCP\IAppConfig` mit `getValueArray`/`setValueArray`, `getValueInt`, `getValueBool` | NC 29+ | Speicher der vier Schalter | Typisierte appconfig-Zugriffe, bereits im Projekt benutzt (`SchedulerJob::LAST_JOB_RUN`). [VERIFIED: lib/public/IAppConfig.php stable32] |
| `OCP\Files\Config\IUserMountCache::getMountsForFileId($fileId, ?$user)` | @since 9.0.0, `$user` @since 12 | fileid -> Besitzer + anzeigbarer Pfad | Reine DB-Abfrage über `oc_mounts` JOIN `oc_filecache`. Kein Dateisystem-Setup, keine Berechtigungsprüfung, funktioniert für Dateien, die der Admin selbst nicht sieht. [VERIFIED: lib/private/Files/Config/UserMountCache.php:373-413 + CachedMountFileInfo::getPath()] |
| `OCP\Files\Cache\IFileAccess::getByFileIds(array $ids)` | @since 29.0.0 | Stapel-Abfrage: existiert die Datei, MIME, Größe, internal path | Ein Query für die ganze Fehlerlisten-Seite statt N. [VERIFIED: lib/public/Files/Cache/IFileAccess.php:67] |
| `OCA\AppAPI\PublicFunctions::exAppRequest(...)` mit `method='GET'` | AppAPI 3.x | Ruf der Container-Routen | Bei `GET` werden `$params` per `http_build_query` an die URL gehängt; Default-Timeout 3 s. [VERIFIED: nextcloud/app_api lib/Service/AppAPIService.php prepareRequestToExApp] |

### Supporting

| Schnittstelle | Verfügbar seit | Zweck | Wann verwenden |
|---|---|---|---|
| `OCP\Config\Lexicon\ILexicon` + `Entry`, `IRegistrationContext::registerConfigLexicon()` | @since 31.0.0 | Typisierte appconfig-Schlüssel mit Default und Beschreibung, sichtbar in `occ config:app:*` | Optional, passt gut zu D-08: die vier Schlüssel bekommen einen deklarierten Typ und einen Default an einer Stelle. [VERIFIED: lib/public/Config/Lexicon auf stable32, IRegistrationContext.php:449] |
| `#[\OCP\AppFramework\Http\Attribute\FrontpageRoute]` bzw. `ApiRoute` | NC 32+ | Routen des Admin-Controllers | Siehe Pitfall 7: die Attributwahl entscheidet, ob Gate B die Route sieht. |
| `#[\OCP\AppFramework\Http\Attribute\AuthorizedAdminSetting(settings: Admin::class)]` | NC 27+ | Erlaubt delegierten Admins die Seite | Nur wenn Admin-Delegation gewollt ist; ohne das Attribut ist die Route strikt admin-only. |
| `OCP\Settings\IDeclarativeSettingsForm` | NC 29+ (in NC 32-34 vorhanden) | Formular ohne eigenes JS, Werte automatisch in appconfig | **Nicht verwenden** für Phase 4: kann keine Tabelle und keine berechneten Zahlen rendern. Als Alternative dokumentiert. |
| `shutil.disk_usage` (Python stdlib) | — | Freier und gesamter Platz des Volumes | Bereits in `api/resources.py:110-127` benutzt; die Statusseite braucht die Rohzahlen zusätzlich zum Boolean `lowDisk`. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `ISettings` + Vanilla JS | `IDeclarativeSettingsForm` | Deklarative Settings rendern die vier Schalter komplett ohne JS und ohne Template und schreiben appconfig selbst. Sie können aber keine Zahlen, keine Tabelle und keine Diagnose-Eingabe. Ein gemischter Ansatz (Schalter deklarativ, Status als ISettings) wäre zwei Formulare in einer Sektion und zwei Speicherpfade. D-01/D-02 sind gesetzt; das bleibt eine Notiz. |
| `IUserMountCache::getMountsForFileId` | `IRootFolder::getUserFolder($uid)->getFirstNodeById($id)` | Die Node-Variante braucht den Besitzer schon vorher und richtet dessen Dateisystem ein (teuer, und der Grund für den Ordner-Cache in `QueueService::claim`). Der Mount-Cache liefert Besitzer und Pfad in einer Abfrage. Node-Variante nur dort, wo man wirklich einen Node braucht (Pfad-Eingabe, siehe Muster 4). |
| Eigener Estimate-Job | Zähler im bestehenden `StorageCrawlJob` | Ein eigener Job wandert die Dateiliste ein zweites Mal. Der Crawl sieht jede Datei schon, samt `getSize()` und `getMimeType()`. Ein eigener Job ist nur dann besser, wenn die Schätzung wirklich VOR dem ersten Enqueue vollständig sein muss (Open Question 2). |
| Dauer aus gemessenen Konstanten | Selbstkalibrierung am laufenden Lauf | Die Konstanten sind auf einem amd64-Laptopkern gemessen; die ARM-Zahlen stehen laut STATE.md noch aus (Phase 5). Eine Hochrechnung aus `indexed_at`-Zeitstempeln des eigenen Laufs braucht keine Hardware-Annahme. Konstanten bleiben als Startwert für Minute 1. |
| Polling der Statusseite | Server-Sent Events / Notifications | SSE hält eine PHP-Verbindung offen; auf einem Instanzchen mit wenigen PHP-Workern ist das der Grund, warum sonst nichts mehr antwortet. Polling mit 5-10 s ist für eine Admin-Seite, die selten offen ist, das Richtige. |

**Installation:**

```bash
# Keine. Phase 4 fügt keine Abhängigkeit hinzu:
# PHP: nur OCP-Schnittstellen, php/composer.json bleibt unveraendert
# Python: nur stdlib + das bereits gepinnte FastAPI/pydantic
# JS: kein npm, kein package.json (D-02)
```

**Version verification:** Nicht anwendbar, weil kein Paket installiert wird. Die Nextcloud-Schnittstellen wurden gegen die Branches `stable32`, `stable33` und `stable34` von `nextcloud/server` sowie gegen `main` von `nextcloud/app_api` und `nextcloud/appstore` geprüft (Datum 2026-09-02, siehe Sources).

### Datenquellen der Statusseite

| Zahl | Quelle | Wer hält sie | Vorhanden? |
|---|---|---|---|
| `indexed` | Container `GET /status` -> `Store.counts()` | `state.db` `files.state='indexed'` | ja |
| `indexed(truncated)` | Container `Store.reasons_by_state()` | `state.db` | ja, aber **nicht** in `StatusResponse` -> Feld ergänzen |
| `skipped`, `failed` pro Grund | PHP `FileStateService` (Erweiterung: `reasonsByState()`) und/oder Container `reasons_by_state()` | beide | PHP hat nur `counts()` pro Zustand, keine Grund-Aufschlüsselung -> ergänzen |
| `docs` (Tantivy-Dokumentzahl) | Container `GET /status` | Tantivy-Index | ja |
| `aclRows` | Container `GET /status` | `state.db` `acl` | ja |
| `scheduled`, `running` | PHP `QueueService::stats()` (heute nur über die ExApp-Route erreichbar) | `findling_queue` | ja, aber die Route trägt `ExAppRequired` -> Service direkt aufrufen, nicht über HTTP |
| `indexVersion`, `analyzerVersion`, `wordlistHash`, `reindexRequired` | Container `GET /status` | `state.db` `meta` | ja |
| `lowDisk` | Container `GET /status` | `shutil.disk_usage` | ja, als Boolean; freie/gesamte Bytes -> ergänzen |
| Indexgröße auf Platte | — | Container-Volume | **fehlt** -> `du` über `index_dir` in `/status` ergänzen (Basis für den Platzbedarf, Muster 7) |
| Letzter Job-Lauf (`last_job_run`) | PHP `appconfig` | `oc_appconfig` | ja, wird von `SchedulerJob`, `StorageCrawlJob` und `SubtreeExpandJob` geschrieben |
| Indexierbare Dateien (Deckungsgrad-Nenner) | — | Nextcloud `filecache` | **fehlt** -> Scan-Zähler, Muster 5 |
| Alter des ältesten wartenden Eintrags | — | `findling_queue` | **nicht möglich**, die Tabelle hat kein `created_at`. Siehe Pitfall 8 |

### Gemessene Raten (Basis für die Dauer-Schätzung)

| Größe | Wert | Bedingungen | Quelle | Konfidenz |
|---|---|---|---|---|
| OCR je Seite, Median | 1984 ms | A4, 300 dpi, `OMP_THREAD_LIMIT=1`, amd64-Laptopkern, 2026-09-01, im Auslieferungs-Image gemessen | `docs/ocr.md` Messung 3 | HIGH für amd64, LOW als ARM-Vorhersage |
| OCR je Seite ohne `OMP_THREAD_LIMIT` | 2424 ms | dieselbe Seite | `docs/ocr.md` Messung 3 | HIGH |
| Seitendeckel je OCR-Dokument | 30 | `FINDLING_OCR_MAX_PAGES` | `backend/src/findling/config.py:220` | HIGH |
| Obergrenze OCR-Job | 600 s (Default), harte Grenze +60 s | `FINDLING_OCR_JOB_SECONDS` | `config.py:231,239` | HIGH |
| Prozessbehandlung, 100.000 Dateien | 2,89 h bei einem Kind je Datei gegen 0,006 h bei recyceltem Kind | amd64 | `.planning/phases/02-indexkern-und-volltextsuche/02-05-SUMMARY.md:106` | HIGH für amd64 |
| Suche gegen ruhenden Index, p95 | 0,196 ms | 200 Suchen je Lauf | `config.py:86-97` | HIGH |
| Dominanter Kostenanteil im Erstindex | HTTP-Abruf der Bytes je Datei | mehrfach im Code als Begründung genannt | `QueueService::usersFor`-Docblock, `02-RESEARCH.md:684` | **nicht gemessen**, siehe Assumptions Log A2 |
| Extraktions-Timeout je Datei | 120 s | `EXTRACT_TIMEOUT_SECONDS` | `config.py:103` | HIGH |
| ARM-Faktor gegen amd64 | unbekannt | Messlauf steht in Phase 5 aus | `.planning/STATE.md` Blockers | LOW |

## Package Legitimacy Audit

**Nicht anwendbar.** Phase 4 installiert kein externes Paket in keinem der drei Ökosysteme:

- **npm:** D-02 schließt einen Build-Step aus. Es entsteht kein `package.json`.
- **PyPI:** Die neuen Backend-Routen brauchen nur FastAPI, pydantic und die stdlib, alle bereits in `backend/pyproject.toml` gepinnt.
- **Packagist:** `php/composer.json` hat als einzige Anforderung `php: >=8.2` und bekommt keine weitere. Alle verwendeten Klassen liegen im `OCP`-Namensraum des Servers.

`slopcheck` ist auf der Entwicklungsmaschine vorhanden (`/c/Users/Student/.local/bin/slopcheck`) und wurde nicht aufgerufen, weil es keine Kandidaten gibt. Sollte der Plan wider Erwarten ein Paket einführen, muss vor dem Install `slopcheck install <pkg> --json` laufen und das Ergebnis hier nachgetragen werden.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
   Admin-Browser
        |
        |  (1) GET /settings/admin/findling
        v
+---------------------------------------------------------------+
| Nextcloud Settings-Seite                                      |
|   AppManager liest php/appinfo/info.xml <settings>            |
|   -> Section::getID() = "findling"                            |
|   -> Admin::getForm() : TemplateResponse(..., RENDER_AS_BLANK)|
|        |                                                      |
|        +-- IInitialState::provideInitialState("bootstrap", ..)|
|        +-- templates/admin.php -> Util::addScript('findling', |
|                                                    'admin')   |
+---------------------------------------------------------------+
        |
        |  HTML + <input id="initial-state-findling-bootstrap">
        |  + <head data-requesttoken="...">  + js/admin.js
        v
   Admin-Browser (Vanilla JS)
        |
        |  (2) fetch(..., headers: {requesttoken})   alle 5-10 s
        |      GET  overview      GET  diagnose?ref=...
        |      POST settings
        v
+---------------------------------------------------------------+
| SettingsController  (admin-only, CSRF-pflichtig)              |
|   kein NoAdminRequired, kein NoCSRFRequired, kein PublicPage  |
+---------------------------------------------------------------+
        |                    |                     |
        | (3a)               | (3b)                | (3c)
        v                    v                     v
+----------------+  +------------------+  +----------------------+
| AdminViewSvc   |  | PathResolver     |  | ExAppService         |
| (Aggregation,  |  | IUserMountCache  |  | exAppRequest(GET)    |
|  Vorrangregel) |  | IFileAccess      |  | timeout kurz         |
+----------------+  +------------------+  +----------------------+
   |        |                                       |
   |        |                                       | (4) GET /status
   |        |                                       |     GET /diagnose?fileId=
   |        |                                       |     GET /rates
   v        v                                       v
+---------------+  +------------------+   +--------------------------+
| findling_     |  | findling_        |   | ExApp-Container          |
| queue         |  | file_state       |   |  state.db  files/acl/    |
| wartet/laeuft |  | skipped/failed   |   |            meta/mounts   |
| (NC-DB)       |  | + Gruende (NC-DB)|   |  Tantivy-Index (docs)    |
+---------------+  +------------------+   |  Volume (freier Platz)   |
        ^                   ^             +--------------------------+
        |                   |                        ^
        | (5) enqueue       | (5) record             | (6) claim / slice / mounts
        |     kind=delete   |     skipped(excluded)  |     (Container zieht,
        |                   |                        |      PHP schiebt nie)
+---------------------------------------------------------------+
| Schreibpfad der Schalter                                      |
|  POST settings -> IAppConfig  (4 Schluessel)                  |
|     |                                                         |
|     +--> neuer Ausschluss: SubtreeExpandJob(kind=delete)       |
|     |     -> Poller._forget: drop_document + forget_acl        |
|     |                        + tombstone                       |
|     +--> Crawl / Event-Listener / StorageService::getMounts()  |
|           lesen die Schluessel beim naechsten Lauf             |
+---------------------------------------------------------------+
```

Der Fluss des Hauptfalls, an den Pfeilen ablesbar: Der Admin öffnet die Sektion (1). Nextcloud rendert Template plus Skript plus Erstzahlen. Das Skript pollt den Controller (2). Der Controller fragt drei Quellen (3a-3c), wobei nur 3c das Netz verlässt (4). Beim Speichern der Schalter schreibt der Controller appconfig und plant im Fall eines neuen Ausschlusses Löschaufträge in die Queue (5), die der Container in seiner nächsten Runde selbst abholt (6).

### Component Responsibilities

| Datei (neu oder geändert) | Verantwortung |
|---|---|
| `php/appinfo/info.xml` | `<settings>`-Block nach `<commands>`; Version bleibt synchron zur ExApp-info.xml |
| `php/lib/Settings/Section.php` (neu) | `IIconSection`: id `findling`, Name, Priorität, Icon |
| `php/lib/Settings/Admin.php` (neu) | `ISettings::getForm()`: `IInitialState` befüllen, `TemplateResponse(..., RENDER_AS_BLANK)` |
| `php/templates/admin.php` (neu) | `Util::addScript`, `Util::addStyle`, statisches Markup mit `$l->t()`-Labels |
| `php/js/admin.js` (neu) | Erstzahlen aus dem Initial-State lesen, Polling, Formular-Submit, Diagnose-Eingabe |
| `php/css/admin.css` (neu, optional) | Nur was Nextcloud-CSS nicht schon liefert |
| `php/img/app-dark.svg` (neu) | Icon der Sektion |
| `php/lib/Controller/SettingsController.php` (neu) | Admin-only Routen: `overview`, `diagnose`, `saveSettings` |
| `php/lib/Service/AdminViewService.php` (neu) | Aggregation und Vorrangregel; die einzige Stelle, die die drei Quellen zusammenführt |
| `php/lib/Service/PathResolverService.php` (neu) | fileid -> Pfad (Mount-Cache), Pfad -> fileid (Node), Stapelauflösung |
| `php/lib/Service/ExclusionService.php` (neu) | Präfixliste lesen/schreiben/normalisieren, `isExcluded()` für Crawl und Listener, Räumung anstoßen |
| `php/lib/Service/ScanStatsService.php` (neu) | Scan-Zähler je Storage lesen/schreiben (Deckungsgrad-Nenner + Schätzung) |
| `php/lib/Service/SettingsService.php` (neu) | appconfig-Zugriff auf die vier Schlüssel, Validierung, Klemmung des Caps |
| `php/lib/Service/FileStateService.php` (geändert) | `excluded` in `REASONS`; neue Leser: `reasonsByState()`, `page($state, $limit, $offset)`, `forFile($fileId)` |
| `php/lib/Service/StorageService.php` (geändert) | `MOUNT_PROVIDERS` wird schaltbar; `getFilesInMount`/`getFileSlice` respektieren Ausschlüsse |
| `php/lib/BackgroundJobs/StorageCrawlJob.php` (geändert) | Größen-Cap aus appconfig, Ausschluss-Test, Scan-Zähler mitschreiben |
| `php/lib/Listener/FileEventListener.php` (geändert) | Größen-Cap aus appconfig, Ausschluss-Test (derselbe Helfer wie der Crawl) |
| `php/lib/Migration/Version001000Date2026....php` (neu) | Tabelle `findling_scan_stats`; optional Index `(state, updated_at)` auf `findling_file_state` |
| `backend/appinfo/info.xml` (geändert) | Neue Routen `diagnose` und `rates` mit `access_level ADMIN` |
| `backend/src/findling/api/status.py` (geändert) | Felder ergänzen: `truncated`, `reasons`, `diskFreeBytes`, `diskTotalBytes`, `indexBytes` |
| `backend/src/findling/api/diagnose.py` (neu) | `GET /diagnose?fileId=` -> Zustand, Grund, `ocrUsed`, `indexedAt`, `attempts`, `deletedAt`. **Nie** `path`, **nie** `title` |
| `backend/src/findling/api/rates.py` (neu) | `GET /rates` -> Dokumente je Stunde der letzten Fenster, getrennt OCR und Text, Bytes je Dokument |
| `backend/src/findling/store/repo.py` (geändert) | `STATE_REASONS` um `excluded`; `throughput()`-Leser über `indexed_at`; `index_bytes()` |
| `backend/src/findling/extract/errors.py` (geändert) | `Reason.EXCLUDED` und Aufnahme in `STATE_REASONS` |
| `backend/tests/test_php_trust_boundary.py` (geändert) | Zweite Routenklasse "admin" mit eigenen Selbsttests |
| `.github/workflows/php.yml` (geändert) | `php -l` auch über `php/templates`; Assertion zum geleerten `<settings>`-Block |

### Recommended Project Structure

```
php/
├── appinfo/
│   ├── info.xml            # <settings> nach <commands>
│   └── routes.php          # bleibt leer, Attribute an den Methoden
├── css/
│   └── admin.css           # minimal, Nextcloud-CSS traegt den Rest
├── img/
│   └── app-dark.svg        # Icon der Settings-Sektion
├── js/
│   └── admin.js            # Vanilla, kein Modul-Bundler
├── lib/
│   ├── Controller/
│   │   └── SettingsController.php   # admin-only, CSRF-pflichtig
│   ├── Settings/
│   │   ├── Admin.php
│   │   └── Section.php
│   └── Service/            # Aggregation, Pfade, Ausschluesse, Scan-Zaehler
└── templates/
    └── admin.php
```

### Pattern 1: Die Vorrangregel der Pro-Datei-Diagnose (ADM-02)

**What:** Eine Datei hat ihren Zustand an bis zu drei Orten und an keinem vollständig. Die Diagnose fragt in einer festen Reihenfolge und die erste Antwort gewinnt.

**When to use:** Für jede Antwort auf "warum ist diese Datei (nicht) auffindbar", inklusive der Fehlerliste, die nur eine vorgefilterte Sicht derselben Funktion ist.

**Warum eine Vorrangregel und nicht eine Zusammenfassung:** Die drei Quellen widersprechen sich legitim. Eine Datei kann in `findling_file_state` als `failed(ocr_failed)` stehen und gleichzeitig eine wartende Queue-Zeile haben, weil der Reconcile sie neu vorgelegt hat. Ohne Reihenfolge zeigt die Seite beides und der Admin weiß weniger als vorher.

**Reihenfolge, von "gilt jetzt" nach "galt damals":**

1. **Datei existiert überhaupt?** `IFileAccess::getByFileId($fileId)`. Nichts -> Zustand `unknown`: entweder gelöscht oder eine fileid, die es nie gab. Wenn der Container einen Grabstein hat, kann die Seite sagen "war indexiert, ist gelöscht" (genau der Grund, warum `tombstone` kein `DELETE` ist, siehe `_TOMBSTONE_SQL`-Kommentar).
2. **Regelverstoß nach heutigen Regeln?** Live berechnet, ohne DB-Zeile: Mount nicht indexiert (`isIndexedStorage`), MIME nicht in der Allowlist, Größe über dem geltenden Cap, Pfad unter einem Ausschluss-Präfix. Ergebnis `skipped` mit Grund `mime_not_allowed`, `too_large` oder `excluded`. **Diese Stufe ist zwingend live**, siehe Pitfall 1.
3. **Queue-Zeile vorhanden?** `findling_queue` per `file_id`. `locked_at IS NULL` -> wartet, mit `kind` und `retries`. `locked_at` gesetzt -> läuft, mit dem Rest der Sperrzeit aus `QueueMapper::LOCK_TIMEOUTS[kind]`.
4. **PHP-Verdikt vorhanden?** `findling_file_state` per `file_id` -> `skipped`/`failed` plus Grund plus `updated_at`. Das ist die Quelle, die einen ausgeschalteten Container überlebt.
5. **Container-Verdikt vorhanden?** `GET /diagnose?fileId=` -> `indexed`, `indexed(truncated)`, `ocrUsed`, `indexedAt`, `attempts`. Nur hier steht "ist auffindbar".
6. **Nichts von allem?** Zustand `pending_crawl`: die Datei ist regelkonform, hat aber noch kein Verdikt und keine Queue-Zeile, also hat der Crawl sie noch nicht erreicht. Das ist ein eigener, benannter Zustand und darf nicht als "nicht indexiert, Grund unbekannt" erscheinen. Prüfbar an `mounts.cursor_file_id` aus `/status` beziehungsweise an der Frage, ob der Crawl-Job für dieses Storage noch in der Job-Liste steht.

**Konsequenz für die Anzeige:** Sechs Zustandsklassen, nicht drei. `indexed`, `indexed(truncated)`, `wartet`, `laeuft`, `skipped(<grund>)`, `failed(<grund>)`, `excluded`, `pending_crawl`, `unknown`. Jede bekommt ein deutsches Label; die Grundcodes bleiben als Rohwert daneben, damit ein Support-Fall zitierbar ist.

**Degradierung:** Fällt Stufe 5 aus (Container aus, Timeout), muss die Seite das SAGEN und nicht raten. "Container nicht erreichbar, Zustand aus der Nextcloud-Sicht" ist eine ehrliche Antwort; "nicht indexiert" wäre eine Lüge, und genau diese Lüge ist der Fehlermodus aus PITFALLS.md (fulltextsearch #597: Selbsttest meldet "ok", indexiert wird nichts).

### Pattern 2: Deckungsgrad als Bruch mit definiertem Nenner (ADM-01)

**What:** `Deckungsgrad = indexed / indexierbar`. Der Zähler kommt aus dem Container, der Nenner aus der Nextcloud-Dateiliste. Beide Seiten müssen dieselbe Menge meinen.

**Definition indexierbar** (und exakt diese Reihenfolge, weil jede Bedingung die nächste verkleinert):

```
indexierbar = Dateien in den aktivierten Mounts
              AND MIME in StorageService::ALLOWED_MIMETYPES
              AND size <= geltender Cap
              AND Pfad nicht unter einem Ausschluss-Praefix
              AND nicht end-to-end verschluesselt
```

Das ist wörtlich die Menge, die `StorageService::getFilesInMount` liefert, sobald sie Cap und Ausschlüsse anwendet. Deshalb darf der Nenner nur von dort kommen und nie aus einer zweiten Abfrage; sonst repariert der Reconcile jede Nacht die Differenz zwischen zwei Zählwerken, was der `getFileSlice`-Docblock schon für einen anderen Fall ausbuchstabiert.

**Was NICHT in den Nenner gehört:** `skipped` mit Grund `too_large`, `mime_not_allowed` oder `excluded`. Diese Dateien sind per Definition nicht indexierbar, und sie im Nenner zu führen produziert einen Deckungsgrad, der nie 100 Prozent erreicht und deshalb nichts mehr aussagt. Sie gehören in eine eigene Zeile "bewusst ausgelassen: N", direkt neben dem Bruch. `skipped(no_text_layer)` gehört hingegen NICHT dorthin, weil das nur der Übergabepunkt zur OCR-Spur ist und keine Endaussage.

**Kopfzahl der Seite** ist der Bruch, nicht die Rohzahlen. PITFALLS.md:44 und :51 nennen den fehlenden Deckungsgrad als eines der Symptome des stillen Ausfalls.

### Pattern 3: fileid -> Pfad ohne Leseberechtigung des Admins (D-03)

**What:** `IUserMountCache::getMountsForFileId($fileId)` liefert `ICachedMountFileInfo[]`. `getUser()->getUID()` ist der Nutzer, `getPath()` ist `mountPoint . internalPath`, also ein Pfad der Form `/alice/files/Ordner/datei.pdf`.

**Warum das und nicht `getUserFolder`:** Der Mount-Cache ist eine reine Abfrage über `oc_mounts` JOIN `oc_filecache`. Er richtet kein Dateisystem ein, prüft keine Rechte und funktioniert daher für eine Datei, die der Admin selbst nicht sehen darf. [VERIFIED: `lib/private/Files/Config/UserMountCache.php:373-413`]

**Besitzersicht wählen:** Bei mehreren Mounts (geteilte Datei) ist der Home-Mount des Besitzers der, dessen `getMountPoint()` genau `/<uid>/files/` ist. Alles andere ist eine Freigabe oder ein Team Folder. Für die Anzeige reicht: erster Mount, dessen `getRootInternalPath()` leer ist; sonst der erste überhaupt, dann zusätzlich "und N weitere Zugänge".

**Kosten:** Zwei Abfragen plus ein `userExists()` je fileid ([VERIFIED: derselbe Quellcode]; `02-RESEARCH.md:684` rechnet das für 100.000 Dateien vor). Für eine Fehlerlisten-Seite von 25 bis 50 Zeilen sind das unter 150 Abfragen, für eine Admin-Seite in Ordnung. **Für die Liste nicht mehr als eine Seite auflösen.** Existenz, MIME und Größe für die ganze Seite vorher in einem Zug: `IFileAccess::getByFileIds($ids)`.

**Gelöschte und getrashte Dateien:** Ohne Cache-Eintrag antwortet `getMountsForFileId` mit einem leeren Array (der `NotFoundException`-Zweig in `getCacheInfoFromFileId`). Eine getrashte Datei hat noch einen Eintrag, aber unter `/alice/files_trashbin/files/...`, weil `onlyUserFilesMounts` nur die Crawl-Mount-Liste umschreibt, nicht diese Abfrage. Das ist ein nützliches Signal ("liegt im Papierkorb") und muss als solches erkannt und benannt werden, nicht als normaler Pfad angezeigt.

### Pattern 4: Pfad -> fileid (Diagnose-Eingabe, D-04)

**What:** Das eine Eingabefeld akzeptiert beides. Die Unterscheidung ist trivial: `ctype_digit($input)` -> fileid, sonst Pfad.

**Pfad auflösen:**
1. Normalisieren: führenden und mehrfachen Schrägstrich weg, `..` verbieten (nicht filtern, ablehnen).
2. Ersten Segment als uid lesen, wenn der Pfad mit `/<uid>/files/` beginnt. Sonst: uid aus einem zweiten Feld oder aus dem Präfix `<uid>:` erwarten.
3. `IRootFolder::getUserFolder($uid)` und darauf `get($relativePath)`. `\OC\User\NoUserException` fangen, genau wie `GatewayController` es tut, und mit derselben Antwort wie "nicht gefunden" beantworten, damit die Eingabe keine Nutzerliste ausspäht.
4. `getId()` ist die fileid, ab da läuft Muster 1.

**Warum nicht `IRootFolder::get('/alice/files/...')` direkt:** Der Wurzelordner braucht die Mounts des Nutzers, und die werden erst durch `getUserFolder($uid)` eingerichtet. Der Aufruf ohne diesen Schritt ist von der Aufrufreihenfolge im Request abhängig, also genau die Art Fehler, die nur auf einer Instanz auftritt.

### Pattern 5: Der Crawl ist der Metadaten-Scan (ADM-03)

**What:** `StorageCrawlJob` sieht bereits jede indexierbare Datei mit `getSize()` und `getMimeType()`, bevor irgendeine Extraktion stattgefunden hat. Er zählt heute in lokalen Variablen (`$seen`, `$queued`, `$skipped`) und wirft sie in eine Logzeile. Diese Zähler dauerhaft zu machen ist der ganze Scan.

**Tabelle `findling_scan_stats`** (eine Zeile je Storage, wie `mounts` im Container):

| Spalte | Bedeutung |
|---|---|
| `storage_id` (PK) | Mount |
| `files_seen` | Dateien, die der Crawl in diesem Mount angesehen hat |
| `bytes_seen` | Summe ihrer Größen |
| `ocr_candidates` | davon mit einem MIME, der OCR braucht oder brauchen kann |
| `over_cap` | davon über dem Größen-Cap (also `skipped(too_large)`) |
| `excluded` | davon unter einem Ausschluss-Präfix |
| `cursor_file_id` | Spiegel des Job-Arguments, damit die Seite den Fortschritt zeigt |
| `finished_at` | gesetzt, wenn der Crawl dieses Mounts terminiert hat (`$seen === 0`) |
| `updated_at` | |

**Wichtig: der Zähler muss idempotent sein.** Der Crawl läuft nach `occ findling:index --restart` erneut über dasselbe Storage. Ein reines `+=` verdoppelt die Schätzung. Zwei saubere Varianten: (a) beim Start eines Storages (`last_file_id === 0`) die Zeile zurücksetzen, dann während des Laufs addieren; (b) `cursor_file_id` als Wahrheit und die Zähler nur addieren, wenn `$entry->getId() > cursor_file_id`. Variante (a) ist einfacher und passt zur bestehenden Terminierungsbedingung.

**Vorläufig gegen vollständig:** Solange nicht jedes Storage ein `finished_at` hat, ist die Schätzung eine Untergrenze. Die Seite muss das beschriften ("Scan laeuft: N von M Mounts durch"). Eine Schätzung, die sich stillschweigend nach oben korrigiert, sieht wie ein Fehler aus.

**OCR-Anteil, MIME-Heuristik:**

| MIME | OCR-pflichtig? |
|---|---|
| `image/jpeg`, `image/png`, `image/tiff`, `image/webp` | immer (ein Bild hat keinen Textlayer) |
| `application/pdf` | unbekannt vor der Extraktion. Der Textlayer entscheidet, und der ist erst im Container sichtbar (`skipped(no_text_layer)` als Übergabe) |
| alles andere aus der Allowlist | nie |

Daraus folgt: der OCR-Anteil ist **vor** dem Lauf ein Intervall, kein Wert. Untergrenze = Bilder. Obergrenze = Bilder plus alle PDFs. Der wahre Wert entsteht während des Laufs aus `reasons_by_state()['skipped']['no_text_layer']` beziehungsweise aus `files.ocr_used` im Container. Die Seite zeigt anfangs das Intervall und ersetzt es, sobald genug PDFs durch sind. Ein einzelner geratener Prozentsatz wäre eine Zahl ohne Grundlage, und die Zielgruppe dieses Produkts hat schon einmal einem Statusbildschirm geglaubt, der nichts wusste.

### Pattern 6: Statusseite ohne Build-Step (D-02)

**What:** Vier Dateien, kein Werkzeug. `templates/admin.php` liefert Markup und lädt `js/admin.js`. `Admin::getForm()` legt die Erstzahlen in den Initial-State. Das Skript liest sie synchron und pollt danach.

**Erstbefüllung lesen** (das Format ist geprüft, nicht geraten): Nextcloud rendert je Schlüssel ein eigenes Hidden-Input mit der id `initial-state-<app>-<key>` und dem base64-kodierten JSON als `value`. [VERIFIED: `core/templates/layout.initial-state.php` + `InitialStateService::getInitialStates()` auf stable32 und stable34]

`atob` ist hier sicher, obwohl es Bytes und nicht UTF-8 liefert: `provideInitialState` benutzt `json_encode($data, JSON_THROW_ON_ERROR)` ohne `JSON_UNESCAPED_UNICODE`, also sind alle Nicht-ASCII-Zeichen als `\uXXXX` entkommen und die base64-Nutzlast ist reines ASCII. [VERIFIED: `lib/private/InitialStateService.php:43`] Trotzdem die Empfehlung: **deutsche Labels gehören ins PHP-Template**, nicht in den Initial-State. Der Initial-State trägt Zahlen und Codes. Dann ist die Frage gar nicht zu stellen.

**Polling-Kadenz:** 5 s, solange die Queue nicht leer ist, sonst 30 s, und Pausieren bei `document.hidden`. Begründung: die Seite ist selten offen, aber wenn sie offen ist, will der Admin Fortschritt sehen. `visibilitychange` verhindert, dass ein vergessener Tab die Instanz eine Woche lang alle fünf Sekunden befragt.

**CSRF:** Der Token bei **jedem** Aufruf frisch aus `document.head.dataset.requesttoken` lesen, nie beim Laden in eine Variable kopieren. Nextcloud rotiert den Token bei Sitzungserneuerung und meldet das über das Ereignis `csrf-token-update`; eine gecachte Kopie wird nach einer langen Sitzung still ungültig, und die Seite bleibt dann ohne Fehlermeldung auf alten Zahlen stehen. [VERIFIED: `core/src/OC/requesttoken.ts` `setRequestToken`]

### Pattern 7: Dauer und Platzbedarf kalibrieren sich selbst

**What:** Statt aus Konstanten vorherzusagen, misst die Seite den laufenden Lauf und rechnet hoch. Die Konstanten sind nur der Startwert für die erste Minute.

**Warum:** Alle gemessenen Raten stammen von einem amd64-Laptopkern. Das Hardware-Ziel ist eine ARM-Box mit zwei bis vier langsameren Kernen, und der Messlauf dafür steht laut STATE.md noch in Phase 5 aus. Eine Vorhersage aus den amd64-Zahlen wäre auf der Zielhardware um einen unbekannten Faktor falsch. Eine Hochrechnung aus dem eigenen Lauf braucht diesen Faktor nicht.

**Dauer:**
```
rate_text = Dokumente mit ocr_used=0, indexed_at im letzten Fenster / Fensterlaenge
rate_ocr  = Dokumente mit ocr_used=1, indexed_at im letzten Fenster / Fensterlaenge
rest_text, rest_ocr = aus dem Scan-Zaehler minus dem, was schon durch ist
verbleibend = rest_text / rate_text + rest_ocr / rate_ocr
```
Vor dem ersten Dokument: `rate_ocr` aus `1984 ms x OCR_MAX_PAGES`, `rate_text` aus einem dokumentierten Startwert, beides sichtbar als "Startwert, wird gemessen".

**Platzbedarf:**
```
bytes_je_dokument = Groesse des Index-Verzeichnisses / docs
erwartet = bytes_je_dokument x indexierbar
```
Beide Zahlen kommen aus dem Container. `docs` steht schon in `StatusResponse`; die Verzeichnisgröße muss dazu (`sum(f.stat().st_size for f in index_dir.rglob('*') if f.is_file())`, in einem Worker-Thread wie `report()` selbst). Vor dem ersten Dokument: kein Wert, sondern der Satz "wird gemessen, sobald die ersten Dokumente im Index sind". Das ist besser als eine Zahl, die niemand belegen kann.

**Hart begrenzen:** Der Container hat `MIN_FREE_BYTES = 524.288.000` und pausiert darunter (`paused_low_disk`). Wenn `erwartet > frei - MIN_FREE_BYTES`, muss die Seite das als Warnung zeigen. Das ist die einzige Stelle, an der die Schätzung eine Handlung auslöst, und sie tut es, bevor der Index stehen bleibt.

**Ein eigenes Fenster braucht eine SQL-Erweiterung:** `files.indexed_at` ist ein Integer-Zeitstempel und es gibt keinen Index darauf. Für ein Fenster über 100.000 Zeilen ist ein `WHERE indexed_at > ?` ein Full Scan der Tabelle. Bei einer Admin-Seite, die alle 5 s pollt, ist das zu teuer. Zwei Auswege: einen Index `files_indexed_at` anlegen (Schema-Erweiterung, `CREATE INDEX IF NOT EXISTS`, kein Versionsbump nötig, weil sich kein Feld ändert), oder den Durchsatz im Container einmal pro Minute cachen. Empfehlung: **Index anlegen**, das ist die ehrlichere Lösung und kostet auf 100.000 Zeilen wenige hundert Kilobyte.

### Pattern 8: Alle vier Schalter greifen PHP-seitig

**What:** Für ADM-04 gibt es keinen Transportweg in den Container, weil jeder Schalter an einer PHP-Quelle sitzt, aus der der Container zieht.

| Schalter | Durchsetzungsort (PHP) | Wie der Container davon erfährt |
|---|---|---|
| Team Folders an/aus | `StorageService::MOUNT_PROVIDERS` -> `getMounts()` | `GET /mounts` liefert die neue Liste; die Reconcile-Runde arbeitet nur noch die verbliebenen Mounts ab |
| External Storage an/aus | dieselbe Liste (`OCA\Files_External\Config\ConfigAdapter`, heute auskommentiert) | dito |
| Größen-Cap | `StorageCrawlJob::MAX_SIZE` und `FileEventListener` (beide heute die Konstante) | betroffene Dateien werden nicht mehr eingereiht; Bestand siehe unten |
| Ordner-Ausschlüsse | `StorageService::getFilesInMount`/`getFileSlice` plus `FileEventListener` | die Dateien fallen aus Crawl und Slice, der Reconcile liest sie als "gone" |

**Die Konstanten müssen Defaults werden, nicht verschwinden.** `StorageCrawlJob::MAX_SIZE` und `MOUNT_PROVIDERS` bleiben als dokumentierte Vorgabe im Code stehen; `SettingsService` liefert den geltenden Wert aus appconfig mit genau diesen Konstanten als Default. `StorageService::MOUNT_PROVIDERS` ist heute `private const` mit einem auskommentierten External-Storage-Eintrag und der Notiz "Es wird ein Schalter in Phase 4 (ADM-04), weshalb die Zeile hier stehen bleibt". Der Kommentar sagt genau, was jetzt passiert: Zeile aktivieren, Liste aus appconfig zusammensetzen.

**Ein Feld muss der Container trotzdem melden, nicht empfangen:** die eigene `max_file_bytes`-Auflösung, damit die Seite eine widersprüchliche Einstellung erkennen kann (Pitfall 2).

### Pattern 9: Räumung nach einem neuen Ausschluss (D-07)

**What:** Zwei Wege, beide bestehend, beide idempotent. Der schnelle wird angestoßen, der langsame ist das Netz.

**Weg A, sofort (empfohlen):** Beim Speichern eines neuen Präfixes löst PHP das Präfix je Mount zu Ordner-fileids auf und plant `SubtreeExpandJob` mit `kind => QueueMapper::KIND_DELETE`. Der Job wandert den Teilbaum in Bändern von 250 mit 30-Sekunden-Deckel und 5-Sekunden-Abstand und reiht je Nachfahre eine Löschzeile ein. Der Poller macht daraus `_forget`: `drop_document` plus `forget_acl` plus `tombstone`. Das ist die Unshare-/Lösch-Räumung aus Phase 3, wörtlich, ohne eine Zeile neuen Räum-Code. `KIND_RANK` in `QueueMapper` gibt `delete` den höchsten Rang, also überschreibt eine Löschzeile eine wartende Content-Zeile und nicht umgekehrt.

`SubtreeExpandJob::EXPANDABLE_KINDS` enthält `KIND_DELETE` bereits, `IJobList::add` dedupliziert über das Argument, und `getFilesInMount` filtert nach MIME, was für eine Löschung richtig ist ("eine Datei, die nie indexiert wurde, hat kein Dokument, das zu räumen wäre"). Es ist also wirklich nur ein Aufruf.

**Weg B, Netz:** Sobald `getFileSlice` das Präfix aussortiert, fehlen die Dateien in der Reconcile-Seite. `Store.gone_in_range` findet sie als lokal bekannt und in der Seite nicht vorhanden und macht daraus Löschzeilen. Das passiert ohne jeden neuen Code, aber erst in der nächsten Runde, also bis zu `FINDLING_RECONCILE_MIN_INTERVAL_HOURS` (Default 24) später.

**Warum beide:** Weg A macht die Wirkung für den Admin sichtbar, solange er noch auf der Seite ist. Weg B fängt ab, was Weg A verpasst (Ordner, die zum Zeitpunkt des Speicherns nicht auflösbar waren, Mounts, die erst später erscheinen). Weg A allein wäre eine einmalige Aktion ohne Nachprüfung, Weg B allein wäre ein Tag Wartezeit auf eine Einstellung, die "der naechste Lauf haelt sich daran" versprochen hat.

**Die Rücknahme heilt sich selbst.** Nimmt der Admin ein Präfix wieder weg, tauchen die Dateien in der nächsten Slice auf. `Store.known_etags` liefert für grabsteinmarkierte Dateien nichts zurück ("either it was never judged, or it carries a tombstone and turning up in a page again makes it a restore"), der Reconcile reiht sie ein, und `_IS_UNCHANGED_SQL` mit `deleted_at IS NULL` verhindert, dass der unveränderte Content-Hash sie stillschweigend als "schon da" durchwinkt. Das ist bereits so gebaut, aber die Seite muss die Latenz benennen: "wirkt mit dem naechsten Abgleich, spaetestens in N Stunden", und den bestehenden Ausweg nennen (`occ findling:index --restart`).

### Pattern 10: appconfig-Schlüssel und ihre Validierung

**What:** Vier Schlüssel, alle typisiert, alle mit dem heutigen Code-Default.

| Schlüssel | Typ | Default | Validierung |
|---|---|---|---|
| `exclusions` | Array von Strings | `[]` | je Eintrag: normalisieren (Schrägstriche), `..` ablehnen, leere Einträge verwerfen, Obergrenze der Listenlänge (Vorschlag 64), Länge je Eintrag begrenzen |
| `max_file_bytes` | Int | `StorageCrawlJob::MAX_SIZE` (52.428.800) | untere Grenze (Vorschlag 1 MB), obere Grenze = der vom Container gemeldete Wert (Pitfall 2) |
| `index_team_folders` | Bool | `true` | — |
| `index_external_storage` | Bool | `false` | — |

**Optional, aber gut hier:** ein `ILexicon` (@since 31, in NC 32 vorhanden) deklariert diese vier Schlüssel mit Typ, Default und Beschreibung an einer Stelle. Dann validiert und dokumentiert `occ config:app:set findling ...` sich selbst und der Admin hat einen zweiten, skriptbaren Zugang, ohne dass die Phase ein occ-Kommando bauen muss.

**Cache-Frage aus Claude's Discretion:** `IAppConfig` cached pro Request. Der Crawl-Job liest also einmal je Slice und der Event-Listener einmal je Schreiboperation. Das ist genau die gewünschte Semantik ("der naechste Lauf haelt sich daran") und braucht keine eigene Invalidierung. Ein Cache auf einem Service-Feld wäre falsch: der Event-Listener lebt so lange wie der Request, der Crawl-Job so lange wie die Slice, und beides ist kurz genug.

### Anti-Patterns to Avoid

- **Zwei Zählwerke für dieselbe Zahl in der Anzeige mischen.** `skipped`/`failed` stehen in `findling_file_state` UND in der Container-`files`-Tabelle. Die Seite muss sich pro Zahl für eine Quelle entscheiden und dazuschreiben, welche es ist. Sonst zeigt sie zwei Werte, die "eigentlich gleich" sein müssten, und der erste Support-Fall ist die Differenz.
- **Die Diagnose ein Snippet zeigen lassen.** Ein Textauszug ist Dateiinhalt und an SRCH-02 gebunden (nur nach bestandenem Recheck). Die Diagnose ist eine Metadaten-Sicht. Die Grenze hier zu verwischen wäre der Weg, auf dem ein Admin-Werkzeug zum Inhaltsleck wird.
- **`ExAppRequired` auf die Admin-Routen setzen, um Gate B zu beruhigen.** Das wäre die falsche Richtung: `ExAppRequired` verlangt eine ExApp-Sitzung, also könnte der Browser des Admins die Route gar nicht erreichen, und jeder registrierte Fremd-Container schon. Gate B muss erweitert werden, nicht umgangen.
- **Den Grund als Freitext durchreichen.** `FileStateService::record` verwirft stillschweigend jeden Grund, der nicht in der geschlossenen Liste steht. Ein neuer Grund, der nur auf einer Seite existiert, produziert deshalb keine Fehlermeldung, sondern eine Datei ohne Verdikt. Genau davor warnt der Docblock der Konstante.
- **Den Deckungsgrad aus `docs` (Tantivy) statt aus `indexed` (state.db) bilden.** Die beiden sind absichtlich zwei Quellen: sie gleich zu haben ist der Beweis, dass der Upsert funktioniert (`tools/index_status.py`-Docstring). Beide anzeigen, aber der Bruch nimmt `indexed`.
- **`ISection` implementieren.** Existiert in NC 32-34 nicht. Siehe Pitfall 5.
- **Eine neue schreibende OCS-Route für den Container bauen.** `test_readonly_gate.py` hat eine Allowlist mit drei Einträgen und einen Test namens `test_write_allowlist_has_exactly_three_entries`. Phase 4 braucht keinen vierten Eintrag, wenn die Räumung PHP-seitig eingereiht wird (Muster 9).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| fileid -> anzeigbarer Pfad | Eigene Abfrage auf `oc_filecache` plus `oc_mounts` | `IUserMountCache::getMountsForFileId` | Die Präfixlogik der Mount-Zuordnung nachzubauen ist genau die Cleverness, die `02-RESEARCH.md:684` als Ursache eines systematisch falschen Ergebnisses benennt. Und der Server macht es in zwei Abfragen. |
| Teilbaum eines Ordners auflösen und Löschaufträge einreihen | Neuer Job, neue Bänderung, neuer Cursor | `SubtreeExpandJob` mit `kind => KIND_DELETE` | Existiert, ist gebändert, hat Wanduhr-Deckel, Cursor im Job-Argument und einen Selbstnachfolger. Die Bänderung und der 30-Sekunden-Deckel sind gemessene Werte (perf audit H2). |
| Dokument, ACL-Zeilen und Zustand einer Datei aus dem Index entfernen | Neue Räum-Route im Container | Löschzeile in der Queue -> `Poller._forget` | Die drei Schreibvorgänge sind schon idempotent, in der richtigen Reihenfolge, und lassen das alte Verdikt lesbar, "so that phase 4 can still say what the file was before it went". Wörtlich für diese Phase gebaut. |
| CSRF-Schutz für die eigenen Admin-Routen | Eigenes Token, eigener Header | Kein Attribut setzen; `SecurityMiddleware` verlangt CSRF und Admin per Default | `SecurityMiddleware::beforeController` verlangt Admin, sofern kein `NoAdminRequired` steht, und die CSRF-Prüfung läuft ohne `NoCSRFRequired` ohnehin. Weniger Code ist hier auch die strengere Variante. |
| Erstzahlen in die Seite bringen | Ein erster `fetch` beim Laden | `IInitialState` | Spart eine Netzrunde, und die Seite ist nie kurz leer. Format geprüft, siehe Muster 6. |
| Freier Platz des Volumes | Eigener Aufruf | `shutil.disk_usage` in `api/resources.py` | Steht schon dort, samt der Behandlung eines nicht messbaren Volumes. |
| Zustand pro Zustand zählen | `COUNT(*)` je Zustand | `Store.counts()` / `FileStateService::counts()` | Beide liefern **alle** Zustände mit Nullen. Der Grund steht im Docstring: eine Statusausgabe, die einen leeren Zustand weglässt, macht "nichts fehlgeschlagen" und "der Zaehler ist kaputt" ununterscheidbar. |
| Gründe pro Zustand zählen | Eigene Gruppierung | `Store.reasons_by_state()` | Existiert und ist im Docstring ausdrücklich als "die Aufschluesselung, aus der Phase 4 ihre Fehlerliste baut" deklariert. Fehlt nur auf der PHP-Seite. |
| Deutsche Zahl-/Datumsformatierung | `number_format` mit Hand-Locale | `OCP\IDateTimeFormatter` und die l10n-Funktionen des Templates | Nextcloud kennt die Sprache des Admins; `updatenotification` benutzt `IDateTimeFormatter` genau dafür. |

## Runtime State Inventory

Phase 4 ist kein Rename, aber D-07 verändert **bestehenden Laufzeitzustand außerhalb von git**. Deshalb dieser Abschnitt.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | (1) Container-`state.db`: `files`-Zeilen und `acl`-Zeilen für Dateien, die durch einen neuen Ausschluss oder einen gesenkten Cap unindexierbar werden. (2) Tantivy-Index: die zugehörigen Dokumente. (3) `findling_file_state` (Nextcloud-DB): alte `skipped`/`failed`-Zeilen für dieselben Dateien. (4) `findling_queue`: eventuell wartende Content-Zeilen für ausgeschlossene Dateien. | (1)+(2): Datenmigration über Löschaufträge, Muster 9. (3): kein Eingriff nötig, das alte Verdikt bleibt absichtlich lesbar; die Diagnose überschreibt es mit der Live-Regel (Muster 1, Stufe 2). (4): `KIND_RANK` lässt die Löschzeile die Content-Zeile ersetzen, kein eigener Eingriff. |
| Live service config | Nextcloud-`oc_appconfig` der App `findling`: heute nur `last_job_run`. Kommen dazu: `exclusions`, `max_file_bytes`, `index_team_folders`, `index_external_storage`. Liegt in der Nextcloud-DB, nicht in git. | Nur Code-Änderung (Schlüssel schreiben und lesen). Keine Migration bestehender Werte, weil die Schlüssel neu sind und der Default dem heutigen Verhalten entspricht. |
| OS-registered state | Nextcloud-Job-Liste (`oc_jobs`): `StorageCrawlJob` und `SubtreeExpandJob` mit Argumenten. Ein neuer Ausschluss plant zusätzliche `SubtreeExpandJob`-Einträge. | Keiner. `QueuedJob` entfernt sich vor dem Lauf aus der Liste, `IJobList::add` dedupliziert über das Argument. Keine Altlast, die aufgeräumt werden müsste. |
| Secrets/env vars | `FINDLING_MAX_FILE_BYTES` ist eine AppAPI-Umgebungsvariable des Containers, gesetzt über die App-Einstellungen von AppAPI, nicht in git. Sie bleibt unverändert; die Phase liest sie nur (über `/status`) und klemmt die PHP-Einstellung daran. Alle anderen `FINDLING_*` bleiben unangetastet. | Keine Änderung. Nur die Anzeige "Der Container liest hoechstens X" plus die Klemmung. Siehe Pitfall 2. |
| Build artifacts | Keine. Es gibt keinen Build-Step für die PHP-App (D-02) und kein Paketartefakt, das den neuen Zustand cached. Das Container-Image bekommt zwei neue GET-Routen, also einen Versionsbump beider `info.xml` und ein neues Image-Tag, aber das ist der bestehende Release-Weg (`docker.yml` vergleicht alle drei Versionen gegen das git-Tag). | Beide `info.xml` und `<image-tag>` gemeinsam anheben, wie in Phase 2 von 0.1.0 auf 0.2.0. |

## Common Pitfalls

### Pitfall 1: `mime_not_allowed` wird nie geschrieben, `excluded` wird es auch nicht

**What goes wrong:** Erfolgskriterium 2 verlangt "Typ nicht unterstuetzt" als nennbaren Grund. Man sucht in `findling_file_state` und findet nichts, weil der Grund im Code existiert und niemand ihn schreibt.

**Why it happens:** Der Crawl filtert nach MIME **in der Abfrage** (`getAllowedMimeIds()` wandert in `getByAncestorInStorage`), also sieht er eine unpassende Datei nie. Der Event-Listener macht `return`, ohne ein Verdikt zu schreiben (`FileEventListener::queue`, Schritt 2). Der Container schreibt `mime_not_allowed` nur für Dateien, die trotzdem bei ihm ankommen, und das passiert praktisch nicht. Dasselbe gilt für einen neuen Ausschluss, wenn man die Präfixe wie den MIME-Filter in die Abfrage zieht.

**How to avoid:** Stufe 2 der Vorrangregel (Muster 1) berechnet diese Gründe live aus den heute geltenden Regeln, ohne DB-Zeile. Die Alternative, für jede ausgeschlossene Datei eine Zeile zu schreiben, kostet auf einem ausgeschlossenen Archivordner mit 200.000 Dateien 200.000 Zeilen für eine Information, die aus vier Vergleichen folgt.

**Warning signs:** Ein Plan-Task, der lautet "Ausschluss schreibt skipped(excluded) in findling_file_state". Der Deckungsgrad-Nenner, der nach dem Setzen eines Ausschlusses gleich bleibt.

### Pitfall 2: Der Container setzt den Größen-Cap ein zweites Mal durch

**What goes wrong:** Der Admin hebt den Cap auf 100 MB. Die 80-MB-PDF wird eingereiht, der Container bricht den Download ab und schreibt `skipped(too_large)`. Die Seite zeigt einen Cap von 100 MB und eine Datei, die wegen Größe übersprungen wurde. Genau der Widerspruch, den diese Phase beseitigen soll.

**Why it happens:** Zwei Durchsetzungsstellen im Container: `nc/client.py:209` deckelt den Download an `settings().max_file_bytes`, `extract/dispatch.py:135` prüft die Größe noch einmal. `settings()` ist `lru_cache`d und liest nur Umgebungsvariablen, also lässt sich der Wert zur Laufzeit gar nicht ändern.

**How to avoid:** `StatusResponse` um `maxFileBytes` ergänzen und die PHP-Einstellung **an diesem Wert klemmen**: die Eingabe akzeptiert nur Werte bis zu dem, was der Container gemeldet hat, und die Seite schreibt dazu, dass für mehr `FINDLING_MAX_FILE_BYTES` in den AppAPI-App-Einstellungen angehoben werden muss (was einen Container-Neustart bedeutet, weil die Variable beim Start gelesen wird). Klemmen statt Warnen, damit die Seite nie eine Zahl zeigt, die nicht gilt. Ist der Container nicht erreichbar, gilt der zuletzt gemeldete Wert; ist keiner bekannt, gilt `MAX_FILE_BYTES` als Obergrenze.

**Warning signs:** Ein Eingabefeld ohne Obergrenze. Eine Antwort auf `/status`, die `maxFileBytes` nicht enthält.

### Pitfall 3: Zwei Wahrheiten über `skipped` und `failed`, und zwei Docstrings, die sich widersprechen

**What goes wrong:** Man baut die Fehlerliste aus der Container-Antwort, weil `status.py` sagt "Phase 4 builds the admin page; this is where its numbers come from". Bei ausgeschaltetem Container ist die Liste leer und die Seite behauptet, es gebe keine Fehler.

**Why it happens:** Die beiden Docstrings sind unabhängig voneinander geschrieben und widersprechen sich:
- `FileStateService`: "die Statusseite der Phase 4 liest diese Tabelle und fragt nie den Container. Den Container zu fragen wuerde eine zweite Stelle schaffen, die die Wahrheit ueber dieselbe Datei kennt."
- `status.py`: "Phase 4 baut die Admin-Seite; hier kommen ihre Zahlen her."
- `QueueController::acknowledgeDocuments` löst es implizit auf: "die auf der Nextcloud-Seite ist die, die ein Admin noch lesen kann, wenn der Container aus ist."

**How to avoid:** Die Aufteilung explizit machen und in beide Docstrings schreiben. Vorschlag: `skipped`/`failed` samt Gründen und die Fehlerliste kommen aus `findling_file_state`. `indexed`, `indexed(truncated)`, `docs`, `aclRows`, Versionsmarken, Platz und Durchsatz kommen aus dem Container. Wer bei ausgeschaltetem Container was zeigen kann, ist dann eine Eigenschaft und keine Überraschung. Die Container-Zahlen bleiben zusätzlich sichtbar (als "Sicht des Containers"), weil eine Differenz zwischen den beiden ein diagnostisches Signal ist und kein Fehler der Seite.

**Warning signs:** Eine einzige Zahl "failed" auf der Seite, ohne Quellenangabe. Ein Plan, der `FileStateService` gar nicht anfasst.

### Pitfall 4: Ausschluss-Präfixe in zwei verschiedenen Pfadräumen

**What goes wrong:** Der Crawl vergleicht gegen `ICacheEntry::getPath()` (storage-intern, `files/Archiv/x.pdf`), der Event-Listener gegen `Node::getPath()` (absolut, `/alice/files/Archiv/x.pdf`). Ein Präfix trifft in einem und nicht im anderen. Ergebnis: der Crawl lässt den Ordner in Ruhe, aber jede Speicherung darin reiht die Datei wieder ein. Der Index füllt sich langsam mit genau dem, was ausgeschlossen sein sollte, und niemand sieht es.

**Why it happens:** Genau dieser Fehlermodus steht schon als Warnung im Code: `StorageService::isIndexedStorage` erklärt, dass eine zweite Providerliste "die zwei wuerden sich an dem Tag widersprechen, an dem External Storage ein Schalter wird (ADM-04): Ereignisse wuerden weiter indexieren, was der Crawl in Ruhe lassen sollte".

**How to avoid:** Genau ein Helfer, genau ein Pfadraum, beide Aufrufer benutzen ihn. Empfehlung: mount-relativer Pfad, also `getInternalPath()` minus dem internen Pfad des Mount-Roots. Der Crawl holt den Root-Pfad einmal je Slice (`IFileAccess::getByFileIdInStorage($overriddenRoot, $storageId)->getPath()`), der Listener über `$node->getMountPoint()->getStorageRootId()`. Der Helfer bekommt einen eigenen Test, der beide Aufrufwege gegen dieselbe Datei stellt und dasselbe Ergebnis fordert. Siehe Open Question 1 zur Frage, welcher Raum dem Admin angezeigt wird.

**Warning signs:** Zwei Stellen im Diff, die `str_starts_with` mit unterschiedlich gebauten Pfaden aufrufen. Ein Plan-Task, der nur den Crawl anpasst.

### Pitfall 5: `OCP\Settings\ISection` gibt es nicht mehr

**What goes wrong:** Man folgt einem Tutorial oder einer älteren App, schreibt `class Section implements ISection`, und Nextcloud stirbt beim Rendern der Settings-Navigation mit einem Klassen-nicht-gefunden-Fehler.

**Why it happens:** `lib/public/Settings` enthält in NC 32, 33 und 34 nur: `DeclarativeSettingsTypes`, `Events/`, `IDeclarativeManager`, `IDeclarativeSettingsForm`, `IDeclarativeSettingsFormWithHandlers`, `IDelegatedSettings`, `IIconSection`, `IManager`, `ISettings`, `ISubAdminSettings`. `IIconSection` erbt von nichts und deklariert alle vier Methoden selbst. [VERIFIED: GitHub contents API auf stable32 und stable34; `ISection.php` antwortet auf stable30 bis stable34 mit 404]

**How to avoid:** `implements \OCP\Settings\IIconSection` mit `getID()`, `getName()`, `getPriority()`, `getIcon()`. `getPriority()` muss laut Docblock zwischen 0 und 99 liegen (bei `ISettings` zwischen 0 und 100).

**Warning signs:** Ein `use OCP\Settings\ISection;` im Diff.

### Pitfall 6: Ein Grabstein bedeutet nicht `gone`

**What goes wrong:** Nach der Räumung durch einen Ausschluss trägt die Datei im Container einen Grabstein. Die Diagnose liest ihn und sagt "geloescht". Die Datei liegt aber unverändert auf der Platte. Der Admin sucht eine Datei, die es gibt, und bekommt gesagt, sie sei weg.

**Why it happens:** `Poller._forget` benutzt `tombstone` für jede Art des Entfernens aus dem Index, weil `record` den Versuchszähler hochzählen würde. Die Räumung nach Ausschluss ist mechanisch eine Löschung, semantisch nicht.

**How to avoid:** Vorrangregel, Stufe 2 vor Stufe 5 (Muster 1). Ein Grabstein wird nur dann als "geloescht" angezeigt, wenn Stufe 1 bestätigt, dass die Datei wirklich keinen Cache-Eintrag mehr hat. Existiert sie und ist ausgeschlossen: `excluded`. Existiert sie und ist regelkonform: `pending_crawl` mit dem Zusatz "war indexiert, wird beim naechsten Abgleich neu erfasst".

**Warning signs:** Eine Diagnose, die `deletedAt` direkt in ein Label übersetzt.

### Pitfall 7: Gate B lehnt jeden Admin-Controller ab, in beide Richtungen

**What goes wrong:** Man legt `SettingsController` mit `ApiRoute`-Attributen an und `backend/tests/test_php_trust_boundary.py` wird rot: "is a route without ExAppRequired". Man lässt `ApiRoute` weg und ein anderer Test derselben Datei wird rot: "test_every_controller_of_the_app_carries_at_least_one_route".

**Why it happens:** Gate B kennt genau eine Routenklasse. `scan_source` fordert für jede Methode mit `ApiRoute` das Attribut `ExAppRequired` und `rejectForeignCaller()` als **erste** Anweisung. `test_every_controller_of_the_app_carries_at_least_one_route` fordert umgekehrt, dass jede Datei in `php/lib/Controller/` mindestens eine `ApiRoute`-Methode hat. Und `test_the_gate_sees_every_route_the_sources_declare` vergleicht die Zahl der gefundenen Routen mit der Zahl der Zeilen, die "ApiRoute" enthalten, weshalb eine `use`-Zeile das Gate bricht.

**How to avoid:** Gate B in derselben Arbeit erweitern, die den Controller anlegt, und dabei **verschärfen**:
- Zwei Klassen: eine Route trägt entweder `ExAppRequired` (dann zusätzlich `rejectForeignCaller()` als erste Anweisung, wie heute) oder keines davon (dann ist sie eine Admin-Route).
- Für die Admin-Klasse neue Forderungen: **kein** `NoAdminRequired`, **kein** `PublicPage`, **kein** `NoCSRFRequired`, **kein** `ExAppRequired`. Das ist die Bedingung, unter der `SecurityMiddleware` Admin und CSRF verlangt.
- Die Anti-Vakuum-Klausel anpassen: `>= 8` wird zu `>= 8 + <neue Routen>`, und die Zählung muss `FrontpageRoute` mitzählen, falls dieses Attribut verwendet wird.
- Der Test, dass jeder Controller mindestens eine Route hat, bleibt und gilt weiter, weil Admin-Routen nun als Routen zählen.
- Neue Selbsttests im bestehenden Stil: eine Admin-Route mit `NoAdminRequired` wird gemeldet, eine mit `NoCSRFRequired` wird gemeldet, eine ohne jedes Attribut ist sauber.

**Warning signs:** Ein Plan, der den Controller anlegt und Gate B nicht nennt. Ein `use OCP\AppFramework\Http\Attribute\ApiRoute;` in irgendeinem Controller.

### Pitfall 8: `findling_queue` hat kein `created_at`

**What goes wrong:** PITFALLS.md:44 nennt als Statusmaß unter anderem "Alter des aeltesten pending-Eintrags". Man plant die Zahl ein und findet keine Spalte.

**Why it happens:** `Version001000Date20260816000000` legt `findling_queue` mit `id`, `file_id`, `storage_id`, `root_id`, `is_update`, `size`, `locked_at`, `retries` an, spätere Migrationen ergänzen `dirty`, `claim_token`, `kind`. Kein Zeitstempel der Einreihung. `locked_at` ist bei wartenden Zeilen `NULL`.

**How to avoid:** Entweder verzichten (die Zahl ist keine Anforderung von ADM-01) oder eine Migration mit `created_at` einplanen und die Zahl als "aelteste wartende Zeile" zeigen. Ein Ersatz über die aufsteigende `id` sagt nur die Reihenfolge, nicht das Alter. Empfehlung: verzichten in dieser Phase, dafür `scheduled` und `running` zeigen und daneben `last_job_run` aus appconfig, denn die eigentliche Frage hinter der PITFALLS-Zeile ("laeuft der Cron ueberhaupt") beantwortet `last_job_run` direkt. Der `SchedulerJob`-Docblock sagt genau, dass der Wert für diese Phase gesammelt wird.

**Warning signs:** Ein Plan-Task "Alter des aeltesten Eintrags anzeigen" ohne Migration.

### Pitfall 9: Der Store-Transform leert den `<settings>`-Block

**What goes wrong:** Man vermutet, `<settings>` müsse an einer bestimmten Stelle stehen oder werde vom Store abgelehnt, und rätselt an der CI-Ausgabe.

**Why it happens:** `pre-info.xslt` des App Store hat die Templates für `activity` und `settings` **vertauscht**: das `settings`-Template kopiert `settings`, `filters` und `providers` (die Kinder von `activity`), das `activity`-Template kopiert `admin` und `admin-section` (die Kinder von `settings`). Der `<settings>`-Block wird deshalb zu einem leeren `<settings/>` normalisiert, und weil im XSD alle Kinder des Typs `settings` `minOccurs="0"` haben, validiert das leere Element.

[VERIFIED, empirisch reproduziert am 2026-09-02: `pre-info.xslt` und `info.xsd` von `nextcloud/appstore@master` heruntergeladen, ein `info.xml` mit `<settings><admin>...</admin><admin-section>...</admin-section></settings>` transformiert. Ergebnis: `<settings/>`, Validierung `True`.]

**How to avoid:** Nichts dagegen tun, aber es festschreiben. Das ist die **exakt gleiche Lage wie beim `<routes>`-Block der ExApp**, für den `php.yml` bereits einen Schritt "State the routes finding explicitly" hat, der rot wird, wenn die Annahme sich ändert. Ein Zwillingsschritt für `<settings>` gehört dazu: prüfen, dass der normalisierte Block leer ist, und den Grund dazuschreiben. Nextcloud selbst liest `<settings>` zur Laufzeit aus dem installierten `appinfo/info.xml` (`AppManager::loadApp()`), also ist die Store-Normalisierung folgenlos, **solange das Tarball die Datei unverändert trägt** (dieselbe Bedingung, die für die Routen schon dokumentiert ist).

Die Reihenfolge im Quell-`info.xml` ist übrigens gleichgültig: das XSLT gibt die Elemente in fester Schema-Reihenfolge aus. Trotzdem `<settings>` nach `<commands>` schreiben, weil der Kommentar in der Datei sich auf die Schema-Reihenfolge beruft und die dort so lautet. [VERIFIED: `info.xsd` Zeilen 56-58]

**Warning signs:** Ein Plan, der `php.yml` nicht anfasst.

### Pitfall 10: `access_level ADMIN` in der ExApp-`info.xml` schützt den `exAppRequest`-Weg nicht

**What goes wrong:** Man verlässt sich darauf, dass die neue Diagnose-Route wegen `access_level ADMIN` nur von Admins erreichbar ist, und setzt auf der PHP-Route `NoAdminRequired`, weil "der Container das ja prüft".

**Why it happens:** Die Prüfung sitzt in `ExAppProxyController::passesExAppProxyRouteAccessLevelCheck`, also im Weg Browser -> AppAPI-Proxy -> ExApp. `PublicFunctions::exAppRequest` geht über `AppAPIService::requestToExApp` und kommt an dieser Prüfung nicht vorbei. [VERIFIED: `nextcloud/app_api@main` `lib/Controller/ExAppProxyController.php:338,348` gegen `lib/Service/AppAPIService.php:64-75`]

**How to avoid:** Beide Ebenen bewusst setzen. `access_level ADMIN` in `backend/appinfo/info.xml` bleibt richtig (Verteidigung in der Tiefe für den Proxy-Weg, den Findling nicht benutzt, aber der existiert). Der wirksame Schutz für die Admin-Seite ist der PHP-Controller ohne `NoAdminRequired`. Nebenbei: der Docstring von `status.py` behauptet heute, `access_level ADMIN` in der `info.xml` sei "where that decision is enforced". Für den `exAppRequest`-Weg ist das nicht wahr, und Phase 4 ist der Zeitpunkt, den Satz zu präzisieren.

**Warning signs:** `NoAdminRequired` auf einer Route der Admin-Seite. Ein Plan-Task, der die Zugriffsprüfung dem Container zuschreibt.

### Pitfall 11: `php -l` sieht `php/templates` heute nicht

**What goes wrong:** Ein Syntaxfehler in `templates/admin.php` fällt erst auf, wenn die Settings-Seite im Browser weiß bleibt, weil auf der Entwicklungsmaschine kein PHP installiert ist.

**Why it happens:** `php.yml:64` prüft `find php/lib php/appinfo -name '*.php'`. Ein neues Verzeichnis wird nicht mitgeprüft. Der Kommentar darüber sagt ausdrücklich, dass es kein PHP auf der Entwicklungsmaschine gibt und dieser Job die einzige Absicherung ist.

**How to avoid:** `php/templates` in den `find`-Pfad. Dieselbe Zeile deckt dann auch spätere Templates ab.

**Warning signs:** Ein Plan, der `templates/` anlegt und `php.yml` nicht anfasst.

### Pitfall 12: MAX_LIST_LENGTH und die Bänderung (CR-01)

**What goes wrong:** Man baut eine Aktion, die eine Liste von fileids an die Queue-Routen gibt (etwa "diese 500 Dateien neu einreihen"), und der Aufruf wird mit "Malformed list of queue ids" abgelehnt.

**Why it happens:** `QueueController::MAX_LIST_LENGTH = 256` und `intList()` **lehnt ab statt zu filtern**, weil eine teilweise angenommene Quittung den Worker in dem Glauben lässt, Zeilen seien entfernt. Der Wert ging in Plan 03-14 von 1000 auf 256 herunter (perf audit M9), und CR-01 der Phase-3-Review war genau der Fall, dass der Reconcile seine Funde in Bändern unter diese Grenze übergeben muss (`REQUEUE_BAND = 200`).

**How to avoid:** Phase 4 sollte diese Routen gar nicht anfassen. Die Räumung reiht PHP-seitig über `SubtreeExpandJob` ein und geht nicht über die HTTP-Grenze. Falls doch eine Liste über die Grenze geht: in Bändern von höchstens 200, wie `REQUEUE_BAND`. Für die **Fehlerliste** der Seite gilt die Grenze nicht (die geht nicht über die Queue-Routen), aber die Größenordnung ist ein guter Anhalt: eine Seite mit 25 bis 50 Zeilen, Sortierung nach `updated_at` absteigend, `LIMIT`/`OFFSET`, und ein `(state, updated_at)`-Index in `findling_file_state`, weil dort heute nur ein Index auf `state` liegt.

**Warning signs:** Eine Zahl über 256 in einem Aufruf gegen `/queues/documents*`.

### Pitfall 13: Neue Gründe müssen an drei Stellen gleichzeitig landen

**What goes wrong:** Man fügt `excluded` in `FileStateService::REASONS` ein, und `backend/tests/test_extract_errors.py::test_php_reason_list_matches_python` wird rot.

**Why it happens:** Der Test liest die PHP-Konstante per Regex aus der Datei und vergleicht die Menge **in beiden Richtungen** mit `errors.STATE_REASONS`. Ein weiterer Test vergleicht `errors.STATE_REASONS` mit `repo.STATE_REASONS`. Drei Listen, zwei Vergleiche, keine Toleranz.

**How to avoid:** In einem Task alle drei anfassen: `php/lib/Service/FileStateService.php` (`REASONS`), `backend/src/findling/extract/errors.py` (`Reason.EXCLUDED` plus Aufnahme in `STATE_REASONS['skipped']`), `backend/src/findling/store/repo.py` (`STATE_REASONS['skipped']`). Der Docblock der PHP-Konstante beschreibt die Falle bereits ausdrücklich, und `record()` verwirft einen unbekannten Grund stillschweigend, also wäre das Ergebnis eine Datei ohne Verdikt.

**Warning signs:** Ein Diff, der nur eine der drei Dateien anfasst.

## Code Examples

### Beispiel 1: Registrierung der Sektion und des Formulars

```xml
<!-- php/appinfo/info.xml, nach <commands>. Beide Klassennamen einzeilig:
     der Schemtyp php-class erlaubt keine umgebende Leerraumzeile, genau wie
     bei repair-steps und commands schon vermerkt. -->
<settings>
	<admin>OCA\Findling\Settings\Admin</admin>
	<admin-section>OCA\Findling\Settings\Section</admin-section>
</settings>
```

```php
<?php
// php/lib/Settings/Section.php
// Source: nextcloud/server stable34 lib/public/Settings/IIconSection.php
declare(strict_types=1);

namespace OCA\Findling\Settings;

use OCA\Findling\AppInfo\Application;
use OCP\IL10N;
use OCP\IURLGenerator;
use OCP\Settings\IIconSection;

/**
 * IIconSection and not ISection: OCP\Settings\ISection does not exist in
 * Nextcloud 30 and later, and this app declares min-version 32. The four
 * methods below are the whole interface.
 */
class Section implements IIconSection {
	public function __construct(
		private IL10N $l,
		private IURLGenerator $url,
	) {
	}

	public function getID(): string {
		// This string is the URL of the page: /settings/admin/findling.
		return Application::APP_ID;
	}

	public function getName(): string {
		return $this->l->t('Findling');
	}

	public function getPriority(): int {
		// Between 0 and 99, see the interface docblock.
		return 75;
	}

	public function getIcon(): string {
		return $this->url->imagePath(Application::APP_ID, 'app-dark.svg');
	}
}
```

```php
<?php
// php/lib/Settings/Admin.php
// Source: the shape of nextcloud/server stable34 apps/updatenotification/lib/Settings/Admin.php
declare(strict_types=1);

namespace OCA\Findling\Settings;

use OCA\Findling\AppInfo\Application;
use OCA\Findling\Service\AdminViewService;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\AppFramework\Services\IInitialState;
use OCP\Settings\ISettings;

class Admin implements ISettings {
	public function __construct(
		private IInitialState $initialState,
		private AdminViewService $view,
	) {
	}

	public function getForm(): TemplateResponse {
		// Numbers and codes only. Every label is translated in the template,
		// so nothing here has to survive base64 and atob.
		$this->initialState->provideInitialState('bootstrap', $this->view->overview());

		// RENDER_AS_BLANK ('') renders the form body alone; the settings page
		// supplies the frame. Anything else produces a page inside a page.
		return new TemplateResponse(Application::APP_ID, 'admin', [], TemplateResponse::RENDER_AS_BLANK);
	}

	public function getSection(): ?string {
		return Application::APP_ID;
	}

	public function getPriority(): int {
		// Between 0 and 100, see the interface docblock.
		return 50;
	}
}
```

### Beispiel 2: Template und Vanilla-JS ohne Build-Step

```php
<?php
// php/templates/admin.php
// Source: the shape of nextcloud/server stable34 apps/updatenotification/templates/admin.php
declare(strict_types=1);

// Resolved to findling/js/admin.mjs first and findling/js/admin.js second,
// see OC\Template\JSResourceLocator::appendScriptIfExist. The call belongs
// here and not into getForm(): the template is rendered before the layout
// collects the script list.
\OCP\Util::addScript('findling', 'admin');
\OCP\Util::addStyle('findling', 'admin');
?>
<div id="findling-admin" class="section">
	<h2><?php p($l->t('Findling search index')); ?></h2>
	<p class="settings-hint" id="findling-coverage-hint"><?php p($l->t('Loading...')); ?></p>
	<table id="findling-errors"><tbody></tbody></table>
</div>
```

```javascript
// php/js/admin.js
// Sources:
//   core/templates/layout.initial-state.php  (the hidden input, id and base64)
//   core/src/OC/requesttoken.ts              (document.head.dataset.requesttoken)
//   lib/private/AppFramework/Http/Request.php (the header name is requesttoken)
'use strict'

function initialState (key) {
  const element = document.getElementById('initial-state-findling-' + key)
  if (element === null) {
    return null
  }
  // atob is safe here: provideInitialState calls json_encode without
  // JSON_UNESCAPED_UNICODE, so every non-ASCII character arrives as \uXXXX
  // and the base64 payload is plain ASCII.
  return JSON.parse(atob(element.value))
}

async function ask (path, params) {
  const url = OC.generateUrl('/apps/findling/admin/' + path) +
    (params ? '?' + new URLSearchParams(params).toString() : '')
  const response = await fetch(url, {
    headers: {
      // Read fresh on every call. Nextcloud rotates the token on session
      // refresh, and a copy taken at load time goes stale without a word.
      requesttoken: document.head.dataset.requesttoken,
      Accept: 'application/json'
    }
  })
  if (!response.ok) {
    throw new Error('findling: ' + response.status)
  }
  return response.json()
}
```

### Beispiel 3: fileid zu anzeigbarem Pfad, in der Besitzersicht

```php
<?php
// php/lib/Service/PathResolverService.php (excerpt)
// Source: nextcloud/server stable34
//   lib/public/Files/Config/IUserMountCache.php::getMountsForFileId
//   lib/private/Files/Config/CachedMountFileInfo.php::getPath
declare(strict_types=1);

namespace OCA\Findling\Service;

use OCP\Files\Config\ICachedMountFileInfo;
use OCP\Files\Config\IUserMountCache;

final class PathResolverService {
	public function __construct(
		private IUserMountCache $mountCache,
	) {
	}

	/**
	 * The owner and the readable path of one file id, or null.
	 *
	 * This is a query over oc_mounts joined with oc_filecache and nothing
	 * else. It sets up no filesystem, checks no permission and therefore
	 * answers for a file the admin may not open himself, which is exactly
	 * what D-03 asks for: the container hands over a number, this side turns
	 * it into something a human can read.
	 *
	 * An empty answer means the file has no cache entry any more, so it is
	 * really gone rather than merely invisible.
	 *
	 * @return array{uid:string,path:string,shares:int,trashed:bool}|null
	 */
	public function describe(int $fileId): ?array {
		$mounts = $this->mountCache->getMountsForFileId($fileId);
		if ($mounts === []) {
			return null;
		}

		$owner = $this->ownerMountOf($mounts);
		$uid = $owner->getUser()->getUID();
		// getPath() is mountPoint . internalPath, so /alice/files/Ordner/x.pdf
		// for a home mount. The prefix is stripped for the display and the uid
		// is shown in its own column.
		$absolute = $owner->getPath();
		$prefix = '/' . $uid . '/files/';
		$trashed = str_starts_with($absolute, '/' . $uid . '/files_trashbin/');

		return [
			'uid' => $uid,
			'path' => str_starts_with($absolute, $prefix)
				? substr($absolute, strlen($prefix))
				: ltrim($absolute, '/'),
			'shares' => count($mounts) - 1,
			// A file in the trash bin still has a cache entry, and saying so is
			// a diagnosis rather than a detail: the search dropped it on
			// purpose (phase 3, D-10) and it is not a failure.
			'trashed' => $trashed,
		];
	}

	/**
	 * The home mount of the owner, or the first mount when there is none.
	 *
	 * A home mount is the one whose root has no internal path of its own;
	 * everything else is a share or a Team Folder. Guessing by the shortest
	 * path would break for a team folder mounted at the top level.
	 *
	 * @param list<ICachedMountFileInfo> $mounts
	 */
	private function ownerMountOf(array $mounts): ICachedMountFileInfo {
		foreach ($mounts as $mount) {
			if ($mount->getRootInternalPath() === '') {
				return $mount;
			}
		}

		return $mounts[0];
	}
}
```

### Beispiel 4: Die neue Container-Route, mit dem Privacy-Vertrag im Docstring

```python
"""GET /diagnose: the verdict this container holds for one file, and nothing else.

Same contract as :mod:`findling.api.status`, one row narrower: the answer carries
the state, the reason code, whether OCR was used, when it was indexed, how many
attempts it took and whether a tombstone is on the row. It carries no path, no
title and no text, although the ``files`` table holds a path and a title for
every row. That is the whole point of D-03: the number travels, the name stays,
and the PHP side turns the number back into something a human can read, in the
permission model that owns that decision.

Declared with access level ADMIN in appinfo/info.xml, which guards the AppAPI
proxy path. The path this app actually uses is PublicFunctions::exAppRequest,
and that one does not pass through the proxy's access level check: the effective
guard there is the admin-only PHP route in front of it.
"""

import asyncio
import logging

from fastapi import APIRouter
from pydantic import BaseModel

from findling.config import settings
from findling.store.repo import open_read_only

LOGGER = logging.getLogger("findling.api.diagnose")

ROUTER = APIRouter()

NOT_JUDGED = "this container has no verdict for that file"


class DiagnoseResponse(BaseModel):
    """What one container knows about one file id.

    Every field defaults, so a file nobody judged answers with the same shape as
    one that has been indexed twice. ``state`` empty plus the note is the honest
    answer to "never seen".
    """

    fileId: int = 0
    state: str = ""
    reason: str = ""
    ocrUsed: bool = False
    indexedAt: int = 0
    attempts: int = 0
    textChars: int = 0
    deletedAt: int = 0
    indexVersion: int = 0
    note: str = ""


def _report(file_id: int) -> DiagnoseResponse:
    resolved = settings()
    if not resolved.state_db.is_file():
        return DiagnoseResponse(fileId=file_id, note=NOT_JUDGED)

    store = open_read_only(resolved.state_db)
    try:
        row = store.file_row(file_id)
    finally:
        store.close()

    if row is None:
        return DiagnoseResponse(fileId=file_id, note=NOT_JUDGED)

    # Field by field and never row spread into the model: the row carries path
    # and title, and a spread would put both on the wire the day somebody adds
    # a field to the table.
    return DiagnoseResponse(
        fileId=file_id,
        state=str(row["state"]),
        reason="" if row["reason"] is None else str(row["reason"]),
        ocrUsed=bool(row["ocr_used"]),
        indexedAt=int(row["indexed_at"] or 0),
        attempts=int(row["attempts"] or 0),
        textChars=int(row["text_chars"] or 0),
        deletedAt=int(row["deleted_at"] or 0),
        indexVersion=int(row["index_version"] or 0),
    )


@ROUTER.get("/diagnose")
async def read_diagnosis(fileId: int) -> DiagnoseResponse:
    """Answer with the verdict of one file, by number."""
    return await asyncio.to_thread(_report, fileId)
```

```xml
<!-- backend/appinfo/info.xml, im <routes>-Block. ADMIN wie /status. -->
<route>
	<url>diagnose</url>
	<verb>GET</verb>
	<access_level>ADMIN</access_level>
	<headers_to_exclude>[]</headers_to_exclude>
	<bruteforce_protection>[401]</bruteforce_protection>
</route>
```

### Beispiel 5: Aufruf einer GET-Route des Containers aus PHP

```php
// php/lib/Service/ExAppService.php (Ergaenzung)
// Source: nextcloud/app_api@main lib/Service/AppAPIService.php::prepareRequestToExApp
//   For method GET the params are appended with http_build_query, so this is
//   a query string call and not a JSON body. The default timeout over there
//   is 3 seconds; an admin page may wait longer than a search, but not much.
$response = $appApi->exAppRequest(
	Application::BACKEND_APP_ID,
	'/diagnose',
	$userId,           // the current admin; the route reads no identity
	'GET',
	['fileId' => $fileId],
	['timeout' => 2.0],
);
// Case 1 first, always: AppAPI catches every transport exception and hands
// back an array, so an unknown, unreachable or timed out backend arrives here
// and calling a method on it would be a fatal error.
if (is_array($response)) {
	return null;   // the page says "container not reachable", never "not indexed"
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| `OCP\Settings\ISection` für die Sektion | `OCP\Settings\IIconSection` (alle vier Methoden selbst deklariert) | vor NC 30 entfernt; auf stable30 bis stable34 nicht vorhanden | Alte Tutorials und alte Apps sind nicht kopierbar. Siehe Pitfall 5. |
| Settings-Klassen im Code registrieren | `<settings>` in `appinfo/info.xml`, gelesen von `AppManager::loadApp()` | seit NC 20 | `IRegistrationContext` hat kein `registerSettings()`; wer dort sucht, findet nichts. |
| `OC.requestToken` als Quelle des CSRF-Tokens | `document.head.dataset.requesttoken`, rotierbar, Ereignis `csrf-token-update` | NC 32-34 (`core/src/OC/requesttoken.ts`) | Token bei jedem Aufruf frisch lesen, nicht cachen. |
| Ein Initial-State-Input je App | Ein Input je Schlüssel, id `initial-state-<app>-<key>` | mindestens seit NC 32, identisch in NC 34 | Der Schlüsselname gehört in die id, nicht in eine Ebene des JSON. |
| Nur `<script>`-Dateien als `.js` | `.mjs` bevorzugt, `.js` als Fallback | `JSResourceLocator::appendScriptIfExist` | `js/admin.js` funktioniert weiter; `js/admin.mjs` wäre ein ES-Modul ohne Bundler. |
| `exAppRequestWithUserInit()` | `exAppRequest()` | deprecated seit AppAPI 3.0.0 | Steht schon in CLAUDE.md unter What NOT to Use. |
| Formulare mit Vue-Bundle | Für ein Zahlen-und-Tabellen-Formular reicht Vanilla plus `IInitialState` | — | D-02. Nextcloud-CSS liefert `.section`, `.settings-hint`, Buttons und Tabellenstile ohne Import. |

**Deprecated/outdated:**
- `OCP\Settings\ISection`: existiert nicht mehr, ersetzt durch `IIconSection`.
- `#[\Override]`: der Kern benutzt es, aber das ist PHP 8.3. Diese App deklariert 8.2.
- `exAppRequestWithUserInit()`: deprecated seit AppAPI 3.0.0.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | Die vier ADM-04-Schalter brauchen keinen Transport in den Container, weil er seine Arbeit ausschließlich aus PHP-Antworten zieht. Abgeleitet aus dem Lesen von `nc/queue.py`, `worker/poller.py`, `worker/reconcile.py` und `nc/files.py`, nicht aus einem Lauf. | Muster 8 | Gäbe es einen Pfad, auf dem der Container eine Datei ohne PHP-Antwort in den Index bringt, würde ein Ausschluss dort nicht greifen. Prüfbar: `grep` auf alle Aufrufe von `store.record` und `writer.add_document` und die Frage, aus welcher Quelle der Job kam. Sollte in einem frühen Task des Plans verifiziert werden. |
| A2 | Im Erstindex dominiert der HTTP-Abruf der Bytes die Kosten je Datei um Größenordnungen. | Gemessene Raten, Muster 7 | Wenn nicht, ist die Dauer-Schätzung anders zusammengesetzt. Steht mehrfach als Begründung im Code (`QueueService::usersFor`, `02-RESEARCH.md:684`), ist aber nirgends gemessen. Für die selbstkalibrierende Variante folgenlos, weil sie den Gesamtdurchsatz misst und nicht seine Bestandteile. |
| A3 | Ein einzelner `SubtreeExpandJob`-Aufruf je Ausschluss-Präfix je Mount reicht für die Räumung, ohne den Job zu ändern. | Muster 9 | Wenn `getFilesInMount` mit dem Ordner-fileid als Ancestor bei einem Groupfolder-Mount anders antwortet als bei einem Home-Mount, braucht es mehr. `SubtreeExpandJob` benutzt genau diesen Aufruf schon für Löschungen und ACL-Änderungen in Team Folders, also ist das Risiko klein. |
| A4 | `getPriority()` 75 für die Sektion und 50 für das Formular sind sinnvolle Werte. | Code-Beispiel 1 | Kosmetik. Die Sektion erscheint nur an einer anderen Stelle der Navigation. |
| A5 | Eine Fehlerlisten-Seite von 25 bis 50 Zeilen ist die richtige Größe. | Muster 3, Pitfall 12 | Zu klein wäre umständlich, zu groß wären hunderte Mount-Cache-Abfragen je Poll. Sollte beim Bau an einer Instanz mit vielen `failed`-Zeilen gegengeprüft werden. |
| A6 | Ein `(state, updated_at)`-Index auf `findling_file_state` und ein `indexed_at`-Index in `state.db` sind nötig. | Pattern 7, Pitfall 12 | Ohne Messung. Auf einer kleinen Instanz sind beide überflüssig; auf 100.000 Zeilen bei 5-Sekunden-Polling nicht. Beide sind billig und rückwärtskompatibel. |
| A7 | Deutsche Prosa auf der Admin-Seite ist gewünscht, aber die Quellstrings sind Englisch mit einer `l10n/de.json`. | Open Question 3 | Bei falscher Annahme ist es eine reine Textänderung, aber sie betrifft jede Zeile des Templates. Sollte vor dem Bau geklärt werden. |

## Open Questions (RESOLVED)

Alle fünf Fragen sind entschieden und in die Pläne übernommen (Stand 02.09.2026):

1. RESOLVED: Owner-Bestätigung 02.09., Ausschlüsse nur für Home-Mounts, relativ zum `files`-Ordner (D-06-Präzisierung in 04-CONTEXT.md; umgesetzt in Plan 04-08).
2. RESOLVED: D-05 gewinnt; Beschriftung "vorläufig, Scan läuft" in 04-CONTEXT.md festgehalten, der Verifier prüft gegen diese Formulierung (Plan 04-05).
3. RESOLVED: Quellstrings Englisch über `$l->t()` plus `l10n/de.json` (Plan 04-03, konsistent mit 04-UI-SPEC.md).
4. RESOLVED: `occ findling:diagnose` als kleiner Endtask in Plan 04-10; wird zuerst gestrichen, wenn der Termin drückt.
5. RESOLVED: KEIN "Erweitert"-Bereich; die Fünf-Blöcke-Regel des 04-UI-SPEC.md gewinnt als bewusste Abweichung von der Empfehlung unten. `backend.reasons` bleibt in der API-Antwort von `AdminViewService::overview()` verfügbar, wird aber nicht gerendert.

Ursprüngliche Diskussion:

1. **In welchem Pfadraum gibt der Admin ein Ausschluss-Präfix ein?**
   - Was wir wissen: Nur der **mount-relative** Pfad (interner Pfad minus internem Pfad des Mount-Roots) ist für Crawl und Event-Listener gleich billig und gleich definiert. Der absolute Nextcloud-Pfad (`/alice/files/...`) bräuchte im Crawl eine Mount-Abfrage je Datei. Der nutzersichtbare Pfad ist für Team Folders nicht eindeutig, weil der Mount-Punkt je Nutzer anders heißen kann.
   - Was unklar ist: Ob der Admin "Archiv" eingeben soll (gilt dann im `files`-Ordner **jedes** Nutzers und in **jedem** Team Folder) oder ob er einen konkreten Ort meint. Das erste ist mächtig und für die Zero-Config-Zielgruppe überraschend, das zweite ist erwartbar und braucht eine Mount-Auswahl in der UI.
   - Empfehlung: Ausschlüsse gelten **nur für Home-Mounts** und werden relativ zum `files`-Ordner des Nutzers eingegeben, also `Archiv`, `Backups`, `.stversions`. Team Folders und External Storage haben ihren eigenen Ganz-oder-nichts-Schalter aus D-08 und brauchen keine Präfixe. Das ist erklärbar in einem Satz, deckt den realen Fall ("dieser Ordnername soll überall draußen bleiben") und macht den Pfadraum eindeutig, weil bei Home-Mounts mit `onlyUserFilesMounts=true` der Root-interne Pfad immer `files` ist. Die allgemeine mount-relative Variante bleibt als Erweiterung offen. Das berührt D-06, deshalb sollte der Planner das vor der Aufgabenzerlegung bestätigen lassen.

2. **"VOR dem Erstindex" oder "ab Minute 1"?**
   - Was wir wissen: Erfolgskriterium 3 der Roadmap sagt "Admin sieht **vor** dem Erstindex eine Schaetzung". D-05 sagt "kein Bestaetigungs-Gate, der Erstindex startet weiter von selbst, die Schaetzung steht ab Minute 1 informativ auf der Statusseite". Der Crawl reiht ein, während er zählt; die Schätzung ist also von Anfang an vorläufig und wächst.
   - Was unklar ist: Ob "vollstaendige Schaetzung, bevor die erste Datei extrahiert wird" gefordert ist. Machbar wäre es: ein `ScanJob`, der die Mounts einmal ohne jeden Schreibvorgang durchzählt und erst danach den `SchedulerJob` plant. Kosten: eine zweite Wanderung über die Dateiliste und eine Verzögerung des Indexstarts um genau die Zeit, die dieser Durchlauf braucht, was dem Zero-Config-Versprechen entgegenläuft.
   - Empfehlung: D-05 gewinnt, weil es die spätere und ausdrückliche Entscheidung ist. Die Seite beschriftet die Schätzung als "vorlaeufig, Scan laeuft: N von M Mounts durch" und wird "vollstaendig", sobald jedes Storage ein `finished_at` hat. Der Verifier sollte Kriterium 3 gegen diese Formulierung prüfen und nicht gegen "bevor irgendetwas indexiert wurde".

3. **Sprache der Admin-UI-Strings.**
   - Was wir wissen: CLAUDE.md sagt "Code/README Englisch, Projektkommunikation Deutsch". Beide `info.xml` beschreiben die App auf Englisch. Die App hat heute kein `l10n/`-Verzeichnis. `Util::addScript` lädt automatisch `findling/l10n/<lang>.js` und ignoriert eine fehlende Datei stillschweigend.
   - Was unklar ist: Quellstrings Englisch plus `l10n/de.json`, oder direkt Deutsch im Template.
   - Empfehlung: Quellstrings Englisch über `$l->t()` plus eine `l10n/de.json` mit `{"translations": {...}, "pluralForm": "nplurals=2; plural=(n != 1);"}`. Das passt zur Store-Einreichung (PKG-05) und zur Projektregel, und die deutschen Labels stehen an einer Stelle. Alle Grundcodes (`too_large`, `ocr_failed`, ...) bekommen dort ihr Label; die Rohcodes bleiben zusätzlich sichtbar, damit ein Support-Fall zitierbar ist.

4. **Kommt ein `occ`-Kommando als Zweitzugang zur Diagnose?**
   - Was wir wissen: `IndexCommand` existiert mit `--status` und `--restart`. `tools/index_status.py` ist der Zweitzugang zu den Container-Zahlen ohne signierten Header. CONTEXT.md nennt das occ-Kommando ausdrücklich als nice-to-have.
   - Was unklar ist: Ob es in den Umfang passt.
   - Empfehlung: `occ findling:diagnose <pfad|fileid>` ist billig, wenn `AdminViewService::diagnose()` einmal existiert (das Kommando ist dann ein Aufruf plus Ausgabe) und es ist der einzige Weg, die Diagnose ohne Browser zu bekommen, was für einen Support-Fall genau der wichtige Weg ist. Als eigener, kleiner Task am Ende einplanen und zuerst streichen, wenn der Termin drückt.

5. **Zeigt die Seite die Container-Sicht auf `skipped`/`failed` zusätzlich an?**
   - Was wir wissen: Beide Seiten zählen dieselben Zeilen (Pitfall 3). Eine Differenz ist diagnostisch wertvoll und für den Admin verwirrend.
   - Empfehlung: ja, aber unter "Erweitert" und mit Quellenangabe, nicht in der Kopfzeile. PITFALLS.md:399 warnt vor der Seite mit 20 Optionen; dasselbe gilt für 20 Zahlen.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker | Lokale Nextcloud (Port 8090) für die Sichtprobe der Admin-Seite | ja | 29.5.2 | — |
| uv | Backend-Tests, ruff, pyright, vulture | ja | 0.11.7 | — |
| PHP auf dem Host | `php -l` vor dem Commit | **nein** | — | `docker compose exec -T app php -l <datei>` in der lokalen Instanz; sonst der Job `lint` in `php.yml`. Der Kommentar in `php.yml` sagt ausdrücklich, dass es kein PHP auf der Entwicklungsmaschine gibt. |
| Node / npm | — | ja (v22.21.0) | v22.21.0 | Wird nicht gebraucht: D-02 schließt einen Build-Step aus. Der Umstand, dass Node da ist, darf nicht zur Einführung eines Bundlers verleiten. |
| tesseract auf dem Host | — | **nein** | — | Nur im Container-Image nötig. Phase 4 ruft kein OCR auf. |
| xsltproc / xmllint | Store-Validierungspfad für `info.xml` | nur in CI | — | Lokal reproduzierbar mit `uv run --with lxml python`, so ist die Erkenntnis in Pitfall 9 entstanden. |
| Nextcloud-Admin-Konto der Dev-Instanz | Sichtprobe von `/settings/admin/findling` | ja | `admin` / `findling-dev-admin` | `docs/dev-setup.md:65` |

**Missing dependencies with no fallback:** keine.

**Missing dependencies with fallback:**
- PHP auf dem Host: Container oder CI. **Konsequenz für den Plan:** jeder PHP-Task braucht einen Verifikationsschritt, der im Container läuft, nicht auf dem Host. Und `php.yml` muss `php/templates` mitprüfen (Pitfall 11), weil ein Syntaxfehler dort sonst erst im Browser auffällt.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | ja | Keine eigene. `SecurityMiddleware` verlangt eine angemeldete Sitzung, sofern kein `PublicPage` steht. Die Admin-Routen setzen kein Attribut und sind damit angemeldet-plus-Admin. |
| V3 Session Management | ja | Nextcloud-Sitzung. Der CSRF-Token rotiert; die Seite liest ihn bei jedem Aufruf frisch (`document.head.dataset.requesttoken`), sonst bleibt sie nach einer Sitzungserneuerung still auf alten Zahlen. |
| V4 Access Control | ja | Zwei Ebenen und beide bewusst: (1) PHP-Routen ohne `NoAdminRequired` -> `SecurityMiddleware` verlangt `isAdminUser()` und wirft sonst `NotAdminException`. (2) `access_level ADMIN` in `backend/appinfo/info.xml` für den AppAPI-Proxy-Weg. Ebene 2 greift **nicht** für `exAppRequest`, siehe Pitfall 10. |
| V5 Input Validation | ja | Diagnose-Eingabe: `ctype_digit` -> fileid, sonst Pfad; `..` **ablehnen** statt filtern. Ausschluss-Präfixe: normalisieren, Listenlänge und Eintragslänge begrenzen. Cap: geklemmter Ganzzahlbereich. Grundcodes: geschlossene Liste, wie `FileStateService::record` es schon tut. Container-Route: `fileId` als `int` in der Signatur, also lehnt FastAPI alles andere mit 422 ab. |
| V6 Cryptography | nein | Phase 4 macht keine Kryptografie. Der signierte AppAPI-Header wird nicht nachgebaut (die bewusste Restrisiko-Entscheidung steht bei jedem `rejectForeignCaller`). |
| V7 Error Handling / Logging | ja | Projektregel: das Log trägt Zähler und Grundcodes, nie eine Bibliotheksmeldung und nie einen Pfad. Die neuen Controller folgen dem Muster von `GatewayController::getFileContents`: statischer Satz plus `['exception' => $e]`, weil Nextcloud die Ausnahme selbst unter dem Log-Level des Admins rendert. |
| V8 Data Protection | ja | D-03 ist die zentrale Kontrolle: der Container liefert Zahlen, PHP löst Namen auf. Die neue `DiagnoseResponse` baut ihre Felder einzeln auf und spreizt nie die Datenbankzeile, weil die Zeile `path` und `title` trägt. |
| V12 Files | ja | Die Diagnose öffnet keine Datei. `PathResolverService` liest den Mount-Cache (DB), nicht das Dateisystem. Der einzige Ort, der einen Node auflöst, ist die Pfad-Eingabe, und der liest nur `getId()`. Kein `fopen`, kein Stream, kein Inhalt. |
| V13 API | ja | Admin-Routen sind CSRF-pflichtig, weil kein `NoCSRFRequired` steht. Keine CORS-Freigabe. Keine Rate-Limit-Attribute nötig, weil die Routen admin-only sind. |
| V14 Configuration | ja | appconfig-Werte werden gelesen und validiert, nie ungeprüft in eine Abfrage oder in einen Pfad gegeben. Der Cap wird am gemeldeten Container-Wert geklemmt, damit keine Einstellung existiert, die nicht gilt. |

### Known Threat Patterns for PHP-Companion + ExApp + Vanilla-JS-Adminseite

| Pattern | STRIDE | Standard Mitigation |
|---|---|---|
| Ein registrierter Fremd-Container ruft die neuen PHP-Routen | Elevation of Privilege | Die Admin-Routen tragen **kein** `ExAppRequired`, sind also für eine ExApp-Sitzung nicht erreichbar. Gate B muss das erzwingen (Pitfall 7). |
| Nicht-Admin ruft die Admin-Routen | Elevation of Privilege | Default von `SecurityMiddleware`. Kein `NoAdminRequired` setzen. Gate B prüft das textuell mit. |
| CSRF gegen die Schreibroute der Schalter | Tampering | Kein `NoCSRFRequired`. Token-Header bei jedem Aufruf. |
| Aufzählung von Nutzernamen über die Pfad-Eingabe | Information Disclosure | "Nutzer gibt es nicht" und "Datei gibt es nicht" bekommen dieselbe Antwort, wörtlich wie in `GatewayController` beim `NoUserException`-Zweig. |
| Aufzählung von Dateinamen über die fileid-Eingabe | Information Disclosure | Die Route ist admin-only. Ein Admin darf jede Datei der Instanz benennen; er kann sie über die Files-App ohnehin. Es wird kein Inhalt geliefert, nur Pfad und Verdikt. Die Grenze zu SRCH-02 bleibt: kein Snippet. |
| Pfad-Traversal über die Diagnose-Eingabe | Tampering | `..` wird abgelehnt. Die Auflösung geht über `Folder::get()` in einem Nutzer-Ordner, nicht über Dateisystempfade. Die Container-Route nimmt nur einen `int`. |
| Freitext im Grundcode landet in der Datenbank oder im Log | Information Disclosure | Geschlossene Liste in `FileStateService::record` und in `Store.record`. Der abgelehnte Wert wird **nicht** geloggt, weil ein Dateiname genau in diesem Feld ankommt. |
| Dateiname oder Pfad in einer Container-Logzeile oder Container-Antwort | Information Disclosure | Der Modul-Docstring von `status.py` ist der Vertrag, `api/diagnose.py` bekommt denselben. Die Felder werden einzeln aufgebaut. |
| XSS über einen Pfad in der Fehlerliste | Tampering | Pfade sind Nutzerdaten. Im Template `p()` verwenden, nie `print_unescaped`. Im JS `textContent` setzen, nie `innerHTML`. |
| Ein hängender Container blockiert die Admin-Seite | Denial of Service | Kurzes Timeout je Aufruf (Muster: `ExAppService::REQUEST_TIMEOUT_SECONDS`, hier 2 s), `is_array($response)`-Prüfung **vor** allem anderen, und die Seite zeigt "Container nicht erreichbar" statt zu raten. |
| Ein vergessener Tab pollt eine Woche lang | Denial of Service | `document.hidden` pausiert das Polling; Intervall wächst bei leerer Queue. |
| Ein Ausschluss räumt versehentlich den halben Index | Tampering | Der Räumweg ist idempotent und reversibel: `tombstone` statt `DELETE`, und der Reconcile holt die Dateien nach Rücknahme des Präfixes zurück. Die Seite zeigt vor dem Speichern, wie viele indexierte Dateien unter dem Präfix liegen. |

## Sources

### Primary (HIGH confidence)

Nextcloud-Server, geprüft gegen die Branches `stable32`, `stable33`, `stable34` (Abruf 2026-09-02):
- `lib/private/App/AppManager.php:485-544` - Registrierung der Settings-Klassen aus `info.xml`, in `loadApp()`
- `lib/public/Settings/ISettings.php` - `getForm`, `getSection`, `getPriority`, Prioritätsbereich 0-100
- `lib/public/Settings/IIconSection.php` - vier Methoden, erbt von nichts, Prioritätsbereich 0-99
- GitHub contents API `lib/public/Settings?ref=stable34` und `?ref=stable32` - vollständiger Inhalt des Namensraums, `ISection.php` nicht vorhanden
- `lib/private/Settings/Manager.php:140-217` - wie eine registrierte Klasse zu einem Formular wird
- `lib/public/AppFramework/Http/TemplateResponse.php:30-50,87` - `RENDER_AS_BLANK`, Konstruktorsignatur
- `lib/public/AppFramework/Services/IInitialState.php` - `provideInitialState`, `provideLazyInitialState`, @since 20.0.0
- `lib/private/InitialStateService.php:36-43,118-129` - `json_encode` ohne `JSON_UNESCAPED_UNICODE`, Schlüsselschema `<app>-<key>`
- `core/templates/layout.initial-state.php` (stable32 und stable34, byteidentisch) - `<input id="initial-state-...">` mit base64
- `lib/public/Util.php:104-156` - `addScript`, `addStyle`, `addInitScript`, automatische Übersetzungen
- `lib/private/Template/JSResourceLocator.php:29-107` - `.mjs` vor `.js`, Suchreihenfolge, fehlende l10n wird ignoriert
- `core/src/OC/requesttoken.ts` - `document.head.dataset.requesttoken`, `setRequestToken`, Ereignis `csrf-token-update`
- `lib/private/AppFramework/Http/Request.php:446-464` - CSRF-Prüfung liest `requesttoken` aus GET, POST oder Header
- `lib/private/AppFramework/Middleware/Security/SecurityMiddleware.php:110-175` - Admin per Default, `NoAdminRequired` als Ausnahme
- GitHub contents API `lib/public/AppFramework/Http/Attribute?ref=stable32` - vollständige Attributliste
- `lib/public/IAppConfig.php` (stable32) - `getValueArray`/`setValueArray` und die übrigen typisierten Zugriffe
- `lib/public/Files/Config/IUserMountCache.php:61-67` - `getMountsForFileId($fileId, ?$user)`
- `lib/public/Files/Config/ICachedMountFileInfo.php`, `ICachedMountInfo.php` - `getPath`, `getInternalPath`, `getRootInternalPath`, `getUser`
- `lib/private/Files/Config/UserMountCache.php:373-413` - Abfrageform, leeres Ergebnis bei fehlendem Cache-Eintrag
- `lib/private/Files/Config/CachedMountFileInfo.php` - `getPath() = getMountPoint() . getInternalPath()`
- `lib/public/Files/Cache/IFileAccess.php` - `getByFileId`, `getByFileIds`, `getByAncestorInStorage`, `getDistinctMounts`
- `lib/public/Files/Cache/ICacheEntry.php` - Methodenliste
- `lib/public/Files/Node.php`, `lib/public/Files/FileInfo.php` - `getPath`, `getInternalPath`
- `lib/public/Config/Lexicon` (stable32) und `lib/public/AppFramework/Bootstrap/IRegistrationContext.php:449` - `registerConfigLexicon` @since 31.0.0
- `lib/private/L10N/Factory.php:572-595`, `lib/private/L10N/L10N.php:205` - `l10n/<lang>.json`
- `apps/updatenotification/lib/Settings/Admin.php` und `apps/updatenotification/templates/admin.php` (stable34) - das Kernmuster: `IInitialState` in `getForm()`, `Util::addScript` im Template, `RENDER_AS_BLANK`

Nextcloud AppAPI, `main` (Abruf 2026-09-02):
- `lib/PublicFunctions.php:29-43` - `exAppRequest`-Signatur, `['error' => ...]` bei unbekannter ExApp
- `lib/Service/AppAPIService.php:64-200` - `prepareRequestToExApp`: `GET` -> `http_build_query`, Default-Timeout 3 s, `http_errors => false`
- `lib/Controller/ExAppProxyController.php:338,348` und `lib/Service/ExAppRouteHelper.php` - `access_level` gilt für den Proxy-Weg, nicht für `exAppRequest`

Nextcloud App Store, `master` (Abruf 2026-09-02):
- `nextcloudappstore/api/v1/release/info.xsd:56-58,436-446` - `<settings>` nach `<commands>`, Typ `settings` mit sechs optionalen Kindern
- `nextcloudappstore/api/v1/release/pre-info.xslt:60-61,81-93` - `activity`- und `settings`-Template vertauscht; empirisch reproduziert (siehe Pitfall 9)

Eigener Code (die tragenden Verträge, alle gelesen):
- `backend/src/findling/api/status.py` - Privacy-Vertrag, `StatusResponse`, ADMIN-Muster
- `backend/src/findling/store/repo.py` - `STATE_REASONS`, `file_row`, `counts`, `reasons_by_state`, `tombstone`, `known_etags`, `gone_in_range`, `replace_acl`, `forget_acl`, `_TOMBSTONE_SQL`, `_IS_UNCHANGED_SQL`
- `backend/src/findling/store/schema.sql` - `files`, `acl`, `mounts`, `reconcile`, vorhandene Indizes
- `backend/src/findling/config.py` - alle Deckel, `settings()` als `lru_cache` über Umgebungsvariablen
- `backend/src/findling/api/resources.py` - `low_disk`, `shutil.disk_usage`, `degraded`
- `backend/src/findling/worker/poller.py:690-717` - `_forget`: `drop_document` + `forget_acl` + `tombstone`
- `backend/src/findling/nc/queue.py`, `backend/src/findling/nc/client.py:209` - was der Container aus PHP zieht, Download-Deckel
- `backend/src/findling/tools/index_status.py` - Zweitzugang, `docs` gegen `indexed` als Beweis
- `backend/tests/test_php_trust_boundary.py` - Gate B, vollständig gelesen
- `backend/tests/test_readonly_gate.py:200-215` - `OCS_WRITE_ALLOWLIST`, `test_write_allowlist_has_exactly_three_entries`
- `backend/tests/test_extract_errors.py:130-158` - Gründe-Paritätstest über drei Listen
- `php/lib/Service/FileStateService.php` - `STATES`, `REASONS`, `record`, `counts`
- `php/lib/Service/QueueService.php` - `claim`, `describe`, `usersFor`, `MAX_USERS`, `KIND_BATCH`
- `php/lib/Service/StorageService.php` - `MOUNT_PROVIDERS` mit dem ADM-04-Kommentar, `ALLOWED_MIMETYPES`, `getFilesInMount`, `getFileSlice`
- `php/lib/Controller/QueueController.php` - `MAX_LIST_LENGTH = 256`, `rejectForeignCaller`, Attributschreibweise
- `php/lib/Controller/ReconcileController.php` - `DEFAULT_SLICE`, `MAX_SLICE`, `final`-Marke, ADM-04-Kommentar zur Mount-Liste
- `php/lib/Controller/GatewayController.php` - `NoUserException`-Muster, Log-Regel
- `php/lib/BackgroundJobs/StorageCrawlJob.php` - `BATCH_SIZE`, `MAX_SECONDS`, `TX_BAND`, `MAX_SIZE`, Cursor im Job-Argument
- `php/lib/BackgroundJobs/SubtreeExpandJob.php` - `EXPANDABLE_KINDS`, Bänderung, der Wiederverwendungspunkt für D-07
- `php/lib/BackgroundJobs/SchedulerJob.php` - `LAST_JOB_RUN` mit dem Phase-4-Kommentar
- `php/lib/Listener/FileEventListener.php` - die drei Fragen vor dem Einreihen, wo Cap und Mount-Test sitzen
- `php/lib/Db/QueueMapper.php` - `KINDS`, `LOCK_TIMEOUTS`, `KIND_RANK`
- `php/lib/Migration/Version001000Date*.php` - Spalten von `findling_queue` und `findling_file_state`
- `php/appinfo/info.xml`, `backend/appinfo/info.xml` - Elementreihenfolge, Routenblock, Umgebungsvariablen
- `.github/workflows/php.yml` - `php -l`-Pfad, Store-Validierungspfad, der Routen-Assertionsschritt als Vorbild
- `.planning/research/PITFALLS.md:38,44,51,193,340,347,399,413,444` - Deckungsgrad als Statusmaß, stiller Ausfall, zwei getrennte Admin-Aktionen, keine Seite mit 20 Optionen
- `docs/ocr.md` Messungen 1-5 - gemessene OCR-Raten und Speicherbefunde
- `docs/dev-setup.md` - Port 8090, Admin-Zugangsdaten, occ-Aufrufe für die Sichtprobe
- `.planning/phases/02-indexkern-und-volltextsuche/02-05-SUMMARY.md:106` - Prozessstart-Hochrechnung
- `.planning/phases/02-indexkern-und-volltextsuche/02-RESEARCH.md:177,684` - Kosten von `getMountsForFileId` und die bewusste Entscheidung dagegen

### Secondary (MEDIUM confidence)

- Eigene lokale Reproduktion der Store-Normalisierung mit `lxml` gegen `pre-info.xslt` und `info.xsd` von `nextcloud/appstore@master` (2026-09-02): `<settings>` wird geleert, das Ergebnis validiert. HIGH für die Tatsache, MEDIUM für die Prognose, dass der Store-Fehler bestehen bleibt.
- Umgebungserhebung auf der Entwicklungsmaschine (Docker 29.5.2, uv 0.11.7, Node v22.21.0, kein PHP, kein tesseract).

### Tertiary (LOW confidence)

- Die Aussage, dass der HTTP-Byteabruf die Kosten des Erstindex dominiert. Steht mehrfach als Begründung im eigenen Code, ist aber nirgends gemessen (Assumptions Log A2).
- Jede absolute Dauer-Vorhersage auf ARM. Der Messlauf steht laut STATE.md in Phase 5 aus. Deshalb Muster 7 (Selbstkalibrierung) statt einer Konstantenrechnung.

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** - keine neuen Pakete; jede verwendete Nextcloud-Schnittstelle wurde gegen `stable32`, `stable33` oder `stable34` von `nextcloud/server` beziehungsweise `main` von `nextcloud/app_api` gelesen, nicht aus Erinnerung zitiert. Die zwei Stellen mit dem höchsten Irrtumsrisiko (Wegfall von `ISection`, Format des Initial-State) sind über die GitHub-contents-API und die Layout-Templates zweifach geprüft.
- Architecture: **HIGH** für die Zuordnung "wer hält welche Zahl" und für die Wiederverwendung der Phase-3-Räummechanik, weil beides aus dem gelesenen Code plus den Docblocks folgt, die diese Phase namentlich nennen. **MEDIUM** für den Zuschnitt der neuen Services, weil das eine Gestaltungsentscheidung und keine Feststellung ist.
- Pitfalls: **HIGH** für 1, 2, 3, 5, 7, 8, 9, 11, 12, 13 (jeweils am Quellcode oder am Test belegt, Pitfall 9 zusätzlich empirisch reproduziert). **MEDIUM** für 4, 6, 10 (aus dem Code abgeleitet, nicht an einer laufenden Instanz gesehen).
- Schätz-Heuristik: **MEDIUM** für die Mechanik (Crawl-Zähler, Selbstkalibrierung), **LOW** für alle absoluten Zahlen. Deshalb ist die empfohlene Konstruktion so gebaut, dass sie ohne die fehlenden Zahlen funktioniert.
- Sicherheit: **HIGH**. Die Zugriffsentscheidung liegt an einer Stelle (`SecurityMiddleware`-Default), die Gate-B-Erweiterung macht sie prüfbar, und die Trennung Zahl/Name aus D-03 ist im Code der Container-Route strukturell und nicht durch Disziplin durchgesetzt.

**Research date:** 2026-09-02
**Valid until:** 2026-10-02 für die Nextcloud-Schnittstellen (das Fenster NC 32-35 ist stabil, `IIconSection` und `IInitialState` sind seit Jahren unverändert). 2026-09-16 für die Store-Erkenntnis aus Pitfall 9, weil das ein Fehler in `pre-info.xslt` ist, der jederzeit behoben werden kann; die CI-Assertion ist genau dafür da. Der eigene Code ist die Wahrheit bis zum nächsten Commit, deshalb sollte der Planner die genannten Zeilennummern beim Zerlegen einmal gegenprüfen.
</content>
</invoke>
