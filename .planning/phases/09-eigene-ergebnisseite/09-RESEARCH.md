# Phase 9: Eigene Ergebnisseite - Research

**Researched:** 2026-09-08
**Domain:** Nextcloud-App-Seite (PHP-Controller, serverseitiges Template, Vanilla-JS) auf dem bestehenden zweistufigen Suchpfad
**Confidence:** HIGH fuer die Bestandsaufnahme der eigenen Quellen und der Nextcloud-Quellen, MEDIUM fuer das Zeitbudget und die Positions-Wiederherstellung im Browser

## Summary

Die Phase baut keine neue Suche. Sie baut eine zweite Oberflaeche auf denselben zwei Container-Aufrufen, die der Provider heute schon macht, und der ganze Rest der Phase ist die Frage, wie diese zweite Oberflaeche entsteht, ohne die Sicherheitsgrenze zu verdoppeln. Der Befund der Codelese ist erfreulich: `Provider::search()` enthaelt die komplette Recheck-Schleife in einer einzigen Methode, sie haengt an genau sieben Konstruktor-Abhaengigkeiten, und sie hat bereits alle Parameter, die eine Seitenroute braeuchte, nur eben als Konstanten statt als Argumente. Der geteilte Dienst ist deshalb ein Extract-Method-Refactoring mit Parametrisierung von vier Konstanten, keine Neukonstruktion.

Drei Befunde muessen vor der Planung auf dem Tisch liegen, weil sie Annahmen der 09-UI-SPEC beruehren. Erstens: `SEARCH_OFFSET_MAX` im Container steht bei 1200, und ein Offset darueber beantwortet der Container mit 422, was auf der PHP-Seite als `null` ankommt und auf der neuen Seite den Fehlerblock "Backend stumm" ausloesen wuerde. Bei 20 Anzeigeseiten a 25 Treffern ist diese Grenze fuer einen Nutzer mit vielen verworfenen Kandidaten erreichbar. Zweitens: `#app-content` ist in stable33, stable34 und stable35 ein eigener Scroll-Container (`overflow: auto`) innerhalb eines `position: fixed` `#content`, und jede AppFramework-Antwort traegt `Cache-Control: no-cache, no-store, must-revalidate`. Stufe 2 des Rueckkehrvertrags, "der Browser macht das von selbst", ist damit browserabhaengig und in Firefox praktisch abgeschaltet. Drittens: `ExAppService::call()` deckelt jeden Suchaufruf hart auf `REQUEST_TIMEOUT_SECONDS = 1.5`, unabhaengig davon, was der Aufrufer an Restbudget hereinreicht. Ein groesseres Zeitbudget der Seitenroute wirkt deshalb erst, wenn dieser Deckel ein Parameter wird.

Alles andere ist bestaetigt und unauffaellig: die Seitenroute ist reiner Read-Path, sie beruehrt den Engine-Lebenszyklus aus Phase 7 nicht, die Python-Seite braucht fuer Cursors keine Aenderung, und `<navigations>` ueberlebt die Store-Transformation unveraendert.

**Primary recommendation:** Erst den geteilten Recheck-Dienst extrahieren und mit einem PHPUnit-Test belegen, dann die dritte Routenklasse in Gate B, dann `php/img/app.svg` plus Navigationseintrag, dann Controller, Template, CSS und Skript, und zuletzt die Paritaets-Erweiterung. Die drei Befunde oben werden in dieser Reihenfolge als eigene Aufgaben eingeplant, nicht als Randnotiz einer anderen.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Suchanfrage entgegennehmen, Parameter pruefen | Frontend Server (PHP-Controller) | Browser (Formular) | `<form method="get">` liefert die Werte, die Pruefung gehoert auf den Server, weil die Adresse frei editierbar ist |
| Kandidaten beschaffen und Snippets holen | API (Python-Container) | Frontend Server (Proxy) | Unveraendert der bestehende Weg ueber `ExAppService` |
| Berechtigungsentscheidung | Frontend Server (PHP) | keiner | Die eine Sicherheitsgrenze des Produkts, `getFirstNodeById` plus `isReadable`. Nie im Container, nie im Browser |
| Highlight-Offsets zu `<mark>` uebersetzen | Frontend Server (PHP-Template) | keiner | Nie HTML aus der Container-Antwort. Offsets kommen als Zahlen, das Markup entsteht serverseitig |
| Trefferliste rendern, Paginierung, Leerzustaende | Frontend Server (PHP-Template) | keiner | Vollstaendiges erstes HTML, kein Nachladen (Erfolgskriterium 5) |
| Rueckkehr-Markierung und Positionswiederherstellung | Browser (`search.js`, sessionStorage) | Browser (History) | Reine Anzeigeerinnerung, kein Serverzustand, kein zweiter Suchweg |
| Dateityp-Symbole | Frontend Server (`IMimeTypeDetector`) | CDN/Static (Core-Assets) | Symbole gehoeren dem Server, werden per URL referenziert |
| Navigationseintrag | Frontend Server (`info.xml`) | keiner | `NavigationManager` liest `navigations` aus der installierten `info.xml` |

## Vertragsbindungen (aus 09-UI-SPEC.md, approved)

Es gibt keine CONTEXT.md fuer diese Phase. Der approved UI-Contract nimmt ihre Stelle ein. Die folgenden Punkte sind **gesetzt** und werden von dieser Recherche nicht neu verhandelt:

- Kein npm, kein Vue, kein Build-Step. PHP-Template plus Vanilla-JavaScript.
- Route `findling.page.index`, `#[FrontpageRoute(verb: 'GET', url: '/')]` plus `#[NoAdminRequired]` plus `#[NoCSRFRequired]`.
- URL-Vertrag `?query=&names=1&page=N&cursors=0.40.95`.
- Seitengroesse 25, Overfetch 4, `MAX_PAGE` 20.
- Einstieg als zusaetzlicher Ergebniseintrag am Ende der Gruppe, kein `IInAppSearch`.
- Highlights serverseitig in `<mark>` uebersetzt, nie HTML aus der Container-Antwort.
- Dreistufiger Rueckkehrvertrag (URL, Browser, Markierung).
- Die 24 Copy-Elemente EN/DE/FR aus der Copy-Tabelle.

Wo diese Recherche einen Konflikt mit der Realitaet der Quellen findet, steht er unten unter "Common Pitfalls" und unter "Open Questions", nicht als stille Aenderung.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UI-01 | Nutzer koennen aus der Unified Search auf eine eigene Findling-Ergebnisseite wechseln, die alle Treffer mit Paginierung zeigt | Abschnitte "Bestand: Provider.php", "Bestand: ExAppService.php", "Cursor-Semantik und die Offset-Decke", "Einstiegspunkt", "Navigationseintrag und app.svg" |
| UI-02 | Nutzer koennen von der Ergebnisseite einen Treffer oeffnen und zurueckkehren, ohne die Trefferliste zu verlieren | Abschnitt "Positions-Wiederherstellung: was der Browser wirklich tut", Pitfall 2 |
| UI-03 | Die Ergebnisseite respektiert dieselbe Berechtigungsgrenze wie die Unified Search | Abschnitte "Der geteilte Recheck-Dienst", "Gate B: die dritte Routenklasse", "Paritaetstest: was die neue Route mitpruefen muss" |

## Project Constraints (from CLAUDE.md)

Aus `./CLAUDE.md` und den globalen Regeln, alle mit derselben Verbindlichkeit wie ein gesetzter Vertragspunkt:

| Direktive | Folge fuer diese Phase |
|-----------|------------------------|
| PHP >= 8.2, Nextcloud 33 bis 35 | Kein PHP-8.3-Syntax. Jede Core-API gegen alle drei Zweige pruefen |
| Code Englisch, Projektkommunikation Deutsch | Klassennamen, CSS-Klassen, IDs, Routennamen, Quell-Strings englisch. Kommentare in den Quellen englisch (so haelt es der gesamte Bestand). Planungsdokumente deutsch |
| Keine Em-Dashes, keine En-Dashes, nirgends | Gate C (`test_admin_ui_contract.py`) prueft das heute schon fuer die drei Admin-Dateien. Die drei neuen Dateien muessen in dieselbe Pruefung |
| Echte Umlaute nur in deutscher Prosa, nie in Code | `php/l10n/de.json` traegt echte Umlaute (tut es heute schon). Bezeichner bleiben ASCII |
| Keine Emojis | Symbole ausschliesslich als Inline-SVG. Gate C prueft es |
| Python-Qualitaetsgates (ruff-Vollregelsatz, pyright basic, vulture, lokal gruen vor Commit) | Gilt, sobald `backend/` oder `backend/tests/` angefasst wird. Die Erweiterung von Gate B und Gate C sind Python-Dateien und fallen darunter |
| Nach jeder Phase Security-, Bug- und Performance-Audit, Befunde ab MEDIUM vor Phasenabschluss fixen (Owner-Regel 15.08.2026) | Als Aufgaben am Phasenende einplanen, nicht danach |
| Nur Owner als Contributor, keine Claude-Trailer | Commits als `street1983nk <k.cherif@outlook.de>` |
| Doku dreisprachig, Deutsch als Standard | Betrifft README, nicht diese Phase direkt. `fr.json` siehe Open Question 3 |

## Standard Stack

Diese Phase installiert **kein einziges neues Paket**. Weder npm noch composer noch pip. Der Abschnitt "Package Legitimacy Audit" entfaellt deshalb ausdruecklich (siehe unten).

### Core (alles bereits vorhanden)

| Baustein | Version / Herkunft | Zweck | Warum Standard |
|----------|--------------------|-------|----------------|
| `OCP\AppFramework\Controller` | Nextcloud 33 bis 35 | Basisklasse des neuen `PageController` | Dieselbe Basisklasse wie `SettingsController` heute. `OCSController` waere falsch, die Route liegt unter `/apps/findling/` [VERIFIED: php/lib/Controller/SettingsController.php] |
| `#[FrontpageRoute]` | `@since 29.0.0` | Routendeklaration am Methodenattribut | Der Bestand deklariert jede Route so, `appinfo/routes.php` bleibt leer [VERIFIED: nextcloud/server stable33 lib/public/AppFramework/Http/Attribute/FrontpageRoute.php] |
| `OCP\AppFramework\Http\TemplateResponse` mit `RENDER_AS_USER` | NC 33 bis 35 | Normale Nutzerseite in `#app-content` | Der Standardweg fuer eine App-Seite ohne Vue |
| `OCP\Files\IMimeTypeDetector::mimeTypeIcon()` | `@since 8.2.0` | Dateityp-Symbol pro Treffer | In stable33 unveraendert vorhanden [VERIFIED: nextcloud/server stable33 lib/public/Files/IMimeTypeDetector.php] |
| `OCP\Util::addStyle` / `addScript` | NC 33 bis 35 | Einbindung von `search.css` und `search.js` | Genau so macht es `php/templates/admin.php` heute, und zwar aus dem Template heraus und nicht aus der Settings-Klasse, weil das Template vor dem Sammeln der Ressourcenlisten laeuft [VERIFIED: php/templates/admin.php Zeilen 22 bis 27] |
| `OCP\IURLGenerator::linkToRoute` | NC 33 bis 35 | Der Link aus dem Dialog auf die Seite, und der Link je Treffer auf `files.View.showFile` | `Provider::resourceUrl()` nutzt es bereits [VERIFIED: php/lib/Search/Provider.php Zeile 588] |
| `OCP\IL10N::t()` | NC 33 bis 35 | Jede sichtbare Zeichenkette | Bestehendes Muster, 149 Schluessel liegen bereits in `php/l10n/de.json` [VERIFIED: php/l10n/de.json] |
| PHPUnit 11.5 | ueber `php/composer.json`, CI-only | Unit-Tests des geteilten Dienstes | Es gibt kein PHP auf der Entwicklungsmaschine. Der Job `phpunit` in `.github/workflows/php.yml` checkt `nextcloud/server` `stable34` aus und laeuft im Autoload-Raum des Servers [VERIFIED: .github/workflows/php.yml] |

### Supporting (Core-CSS-Klassen, die die Seite ohne eigenen Code bekommt)

| Baustein | Herkunft | Wann verwenden |
|----------|----------|----------------|
| `.hidden-visually` | `core/css/global.scss` Zeile 66 in stable34 | Der Screenreader-Text "zuletzt geoeffnet" der Rueckkehr-Markierung. Kein eigenes CSS noetig [VERIFIED: nextcloud/server stable34 core/css/global.scss] |
| `.hidden` | `core/css/global.scss` Zeile 62 | Nur falls ein Block wirklich per Klasse geschaltet werden muss. Die 09-UI-SPEC bevorzugt `hidden` als Attribut, das bleibt richtig |
| `icon-search` | Core-Klasse | Das Symbol des Einstiegs-Eintrags im Suchdialog. `Provider::toEntries()` setzt es bereits fuer jeden Treffer [VERIFIED: php/lib/Search/Provider.php Zeile 561] |
| `#app-content` | `core/css/apps.scss` Zeile 742, identisch in stable33, stable34, stable35 | Der Rahmen der Seite. Nicht ueberschreiben, nur eigenen Innenabstand setzen [VERIFIED: raw.githubusercontent.com nextcloud/server stable33/34/35 core/css/apps.scss] |

### Alternatives Considered

| Statt | Koennte man | Abwaegung |
|-------|-------------|-----------|
| Ein neuer `PageController` | `SettingsController` um eine Methode erweitern | Nein. Gate B urteilt pro Methode, aber eine Nutzerseiten-Methode in einem Admin-Controller macht die Klasse gemischt und die Absicht unlesbar. Eine Klasse, eine Routenklasse |
| Recheck-Dienst als neue Klasse `php/lib/Service/SearchService.php` | Provider bleibt Eigentuemer, Controller ruft den Provider | Nein. `IProvider::search()` nimmt `ISearchQuery` und liefert `SearchResult`, beides ist die Sprache des Dialogs. Der Controller muesste ein `ISearchQuery` faelschen und ein `SearchResult` wieder auseinandernehmen. Eine eigene Klasse mit einer eigenen, ehrlichen Signatur ist billiger und pruefbarer |
| Offset-Decke im Container anheben | `SEARCH_OFFSET_MAX` in `backend/src/findling/config.py` erhoehen | Moeglich, aber es ist eine Sicherheitskonstante mit eigener Begruendung (security audit C1) und wuerde die Python-Gates plus einen Container-Build in eine PHP-Phase ziehen. Empfehlung: in PHP clampen, siehe Pitfall 1 |

**Installation:** entfaellt. Keine neue Abhaengigkeit in dieser Phase.

## Package Legitimacy Audit

**Nicht anwendbar.** Diese Phase installiert kein Paket aus einer Registry: kein npm (die Companion-App hat bis heute keine `package.json` und bekommt in dieser Phase keine), kein neues composer-Paket (`php/composer.json` bleibt unveraendert), kein neues PyPI-Paket (die Backend-Aenderungen dieser Phase sind Tests und, falls Open Question 1 so entschieden wird, eine Konstante). Die einzigen neuen Fremdmaterialien sind drei SVG-Pfaddaten aus Material Design Icons, die woertlich in der 09-UI-SPEC stehen und gegen den in `THIRD-PARTY.md` bereits gepinnten Commit `9e04201d4557e729822fb57f62a316c3dea1d4a8` gezogen wurden. Kein Paket, keine Laufzeit, kein Code.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Bestandsaufnahme: `php/lib/Search/Provider.php`

590 Zeilen, eine Klasse, `final`, implementiert `IFilteringProvider`. Der Suchpfad von heute, in der Reihenfolge, in der er laeuft:

1. **Deadline setzen.** `BUDGET_NANOSECONDS = 2_500_000_000`, gemessen mit `hrtime()` ueber einen injizierbaren `\Closure $clock` (Zeile 57, 112 bis 125). Diese Naht existiert nur fuer die Tests und ist genau der Grund, warum sich das Zeitbudget der Seitenroute ohne neue Abhaengigkeit testen laesst.
2. **Leerer Suchbegriff** -> `SearchResult::complete(name, [])` (Zeile 192).
3. **Versionsdrift.** `ExAppService::driftOnRecord()`, kein Round-Trip, liest den zuletzt gemeldeten Wert aus `appConfig` (Zeile 210 bis 222). Bei Drift: leere Gruppe plus `logger->warning` mit beiden Nummern.
4. **`getUserFolder()`** in `try/catch(\Throwable)`. Jeder Fehler bedeutet leere Gruppe, niemals ungeprueft ausliefern (Zeile 226 bis 238).
5. **Guenstige Reduktion.** `storageIdsOfUser()` einmal pro Suche ueber `IUserMountCache`, danach `reduceIds()` pro Seite ueber `IFileAccess::getByFileIds()`. Ueberapproximation, `null` heisst "kann nichts entscheiden" und schickt alle Kandidaten in den gedeckelten Recheck (Zeile 447 bis 498).
6. **Runden-Schleife.** `MAX_ROUNDS = 3`, `OVERFETCH = 4`, Abbruch bei genug Treffern, aufgebrauchtem Recheck-Budget oder abgelaufener Deadline (Zeile 247 bis 250).
7. **Fetch-Limit.** `min($limit * OVERFETCH, $recheckBudget - $rechecks + $limit)`, das Restbudget reist als `secondsLeft` mit (Zeile 257 bis 258).
8. **Der Recheck.** Pro Kandidat: `fileId <= 0` ist der Canary-Pfad; nicht in `$keptIds` heisst entschieden und verworfen; `getFirstNodeById()`; `instanceof File`; `isReadable()`; Titel und Pfad aus dem bestaetigten Node ueber `PlainText::bounded(..., 255)` (Zeile 305 bis 382).
9. **Cursor-Fortschreibung.** `$consumed` zaehlt entschiedene Kandidaten. Bei vorzeitigem Stopp `$offset += $consumed`, sonst `$offset = $page['nextOffset']` (Zeile 384 bis 394).
10. **Snippets erst danach**, nur fuer Ueberlebende, mit Restbudget (Zeile 404 bis 413).
11. **Rendern.** `toEntries()` baut `SearchResultEntry` mit `thumbnailUrl: ''`, Titel, Subline (Snippet oder Pfad), `resourceUrl`, `icon: 'icon-search'`, dazu die Attribute `fileId` und `highlights` als JSON (Zeile 549 bis 576).
12. **Rueckgabe.** `complete()` oder `paginated($name, $entries, $offset)` (Zeile 417 bis 419).

**Was in den geteilten Dienst muss:** die Schritte 3 bis 10, also alles zwischen "gibt es Drift" und "Snippets fuer die Ueberlebenden". Was **nicht** hinein gehoert: Schritt 11, denn `SearchResultEntry` ist die Sprache des Dialogs und die Seite rendert HTML.

**Was parametrisiert werden muss:** `BUDGET_NANOSECONDS`, `MAX_ROUNDS`, `OVERFETCH` sowie das Paar `MAX_RECHECKS_PER_HIT` / `MAX_RECHECKS_ABSOLUTE`. Die 09-UI-SPEC sagt Seitengroesse 25 und Overfetch 4; `MAX_RECHECKS_ABSOLUTE = 64` ist fuer 25 Anzeigetreffer zu klein (`25 * 2 = 50`, aber die absolute Decke greift bei 64 erst spaeter, also passt es gerade noch). Bei einem Nutzer, dessen Kandidaten mehrheitlich verworfene Freigaben sind, wird eine Anzeigeseite dadurch kurz. Die 09-UI-SPEC hat das bereits als "Kurze Seite" im Paginierungsvertrag akzeptiert und verbietet jede Erklaerung dazu. Das ist konsistent, muss aber bewusst uebernommen und nicht stillschweigend anders parametriert werden.

**Der bestehende Paritaetstest:** Job `search-parity` in `.github/workflows/integration.yml` ab Zeile 2611, Vergleich ueber `scripts/ci/parity_diff.py`. Siehe eigener Abschnitt unten.

**Vorhandene PHP-Unit-Tests:** `php/tests/Unit/ProviderTest.php` deckt die Verhalten 4, 5, 10 und 11 aus `docs/testing.md` ab, komplett auf Mocks, mit stillgestellter Uhr ueber das `\Closure`-Argument. Ein Test des geteilten Dienstes kann diese Datei fast eins zu eins uebernehmen; der Provider-Test schrumpft dann auf "der Provider reicht durch und rendert richtig".

## Bestandsaufnahme: `php/lib/Service/ExAppService.php`

846 Zeilen. Die fuer Phase 9 relevanten Signaturen und Konstanten, alle [VERIFIED: Quelle gelesen 2026-09-08]:

```php
public function searchCandidates(
    string $userId, string $term, int $limit, int $offset, bool $titleOnly,
    float $secondsLeft = self::REQUEST_TIMEOUT_SECONDS
): ?array;
// -> array{candidates: list<array{fileId:int,title?:string,snippet?:string}>,
//          hasMore: bool, nextOffset: int, degraded: bool} | null

public function snippets(
    string $userId, string $term, array $fileIds, bool $titleOnly,
    float $secondsLeft = self::REQUEST_TIMEOUT_SECONDS
): array;
// -> array<int, array{text: string, highlights: list<array{int,int}>}>

public function driftOnRecord(): ?array; // ['companion' => string, 'container' => string] | null
```

| Konstante | Wert | Bedeutung fuer Phase 9 |
|-----------|------|------------------------|
| `MIN_LIMIT` / `MAX_LIMIT` | 1 / 100 | 25 Anzeigetreffer x Overfetch 4 = 100. Passt exakt, wie die 09-UI-SPEC sagt |
| `MAX_SNIPPET_IDS` | 100 | Wird bei 25 Treffern pro Seite nie erreicht |
| `MAX_SNIPPET_LENGTH` | 1000 | Das Snippet, aus dem die zwei geklampten Zeilen entstehen |
| `MAX_HIGHLIGHTS` | 32 | Obergrenze der `<mark>`-Bereiche pro Zeile |
| `MAX_TITLE_LENGTH` | 255 | Deckel auf dem Container-Titel (nur Canary) |
| `MAX_BODY_BYTES` | 1048576 | Antwortdeckel vor `json_decode` |
| `REQUEST_TIMEOUT_SECONDS` | **1.5** | **Harter Deckel pro Suchaufruf.** Siehe Pitfall 3 |
| `ADMIN_REQUEST_TIMEOUT_SECONDS` | 2.0 | Nur `adminGet()` |
| `MIN_CALL_SECONDS` | 0.3 | Unter diesem Restbudget wird gar nicht erst gerufen |

**Fehlerbehandlung in `call()`** (Zeile 615 bis 683): vier Faelle, alle enden in `null`. Erstens Proxy nicht aufloesbar. Zweitens AppAPI liefert ein Array statt einer Response, das ist der unerreichbare Container. Drittens Statuscode >= 400, denn AppAPI setzt `http_errors` auf false. Viertens Body zu gross oder kein Array nach `json_decode`. **Jeder dieser Faelle ist auf der neuen Seite der Fehlerblock "Backend stumm".** Das ist nur dann richtig, wenn es tatsaechlich ein Backendproblem war, und genau hier liegt Pitfall 1.

**Traegt die ExApp-API heute schon Cursors?** Ja. `nextOffset` ist der Cursor, den die 09-UI-SPEC in `cursors=0.40.95` sammelt. Es ist ein Container-Offset ueber **erlaubte Kandidaten** (`backend/src/findling/index/search.py`, dokumentiert in `backend/src/findling/config.py` Zeile 88 bis 89), nicht ueber rohe Engine-Treffer und nicht ueber genehmigte Treffer. Die Semantik ist exakt die, die der Cursorpfad braucht. **Eine Python-Aenderung fuer Cursors ist nicht noetig.**

## Bestandsaufnahme: `backend/src/findling/api/search.py`

`POST /search`, Antwortmodell:

```python
class Candidate(BaseModel):
    fileId: int
    score: float = 0.0
    mtime: int = 0

class SearchResponse(BaseModel):
    candidates: list[CanaryCandidate | Candidate]
    hasMore: bool = False
    nextOffset: int = 0
    degraded: bool = False
```

Also: **Offsets ja, Scores ja, Highlight-Offsets nein.** Highlights kommen erst aus `POST /snippets`, Modell `Snippet(text: str, highlights: list[tuple[int, int]])`. Das ist genau die Trennung, die die Sicherheitsreihenfolge erzwingt: der Kandidat traegt strukturell keinen Text, weil `Candidate` kein Textfeld hat und `test_semantic_boundary.py` das als Menge der Feldnamen festhaelt.

Request-Grenzen (`backend/src/findling/config.py`):

| Konstante | Wert | Wirkung |
|-----------|------|---------|
| `SEARCH_LIMIT_MAX` | 100 | Spiegelbild von `ExAppService::MAX_LIMIT` |
| `SEARCH_OFFSET_MAX` | `100 * 4 * 3` = **1200** | Offset darueber -> 422 -> `null` auf der PHP-Seite |
| `SEARCH_QUERY_MAX_CHARS` | 512 | Die 09-UI-SPEC deckelt `query` bei 255, also unkritisch |
| `SEARCH_SCAN_MAX` | 10000 | Rohe Engine-Treffer pro Kandidatenaufruf |
| `SEARCH_VECTOR_DEPTH` | 300 | Unabhaengig vom `limit`. Ein tiefer Vektorscan kostet pro Runde gleich viel, egal ob 20 oder 100 gefragt sind |

Bestaetigt durch `backend/tests/test_search_endpoint.py` Zeile 169 bis 190: `SEARCH_OFFSET_MAX` wird angenommen, `SEARCH_OFFSET_MAX + 1` wird mit 422 abgewiesen.

**Es gibt heute keinen Test, der `ExAppService::MAX_LIMIT` gegen `SEARCH_LIMIT_MAX` oder eine PHP-Spiegelung von `SEARCH_OFFSET_MAX` vergleicht.** Wenn die PHP-Seite die 1200 spiegelt, braucht sie einen Gate nach dem Muster von `backend/tests/test_lockstep_versions.py`, sonst driften die beiden Zahlen.

## Cursor-Semantik und die Offset-Decke

Der Cursorpfad der 09-UI-SPEC ist zustandslos und korrekt begruendet. Die Arithmetik dahinter muss die Planung kennen:

- Anzeigeseite N beginnt beim Container-Offset `cursors[N-1]`.
- Nach dem Rendern der Seite steht der naechste Cursor fest, das ist der Wert, den der geteilte Dienst zurueckgibt (heute die lokale Variable `$offset` am Ende von `Provider::search()`).
- Pro Anzeigeseite waechst der Offset um die Zahl der **entschiedenen** Kandidaten, nicht um 25. Im besten Fall 25, im schlechtesten bis zu `MAX_ROUNDS * fetchLimit`.
- 20 Anzeigeseiten sind deshalb im guenstigen Fall Offset 500, bei einer Genehmigungsquote von einem Drittel schon rund 1500.
- **1500 > `SEARCH_OFFSET_MAX` = 1200.** Der Container antwortet mit 422, PHP macht daraus `null`, die Seite zeigt "Die Suche antwortet gerade nicht". Das ist eine Falschaussage: das Backend antwortet einwandfrei, es lehnt nur einen zu tiefen Cursor ab.

Zwei saubere Auswege, beide planbar:

1. **In PHP clampen (empfohlen).** Der geteilte Dienst kennt eine Konstante `MAX_CONTAINER_OFFSET = 1200`, prueft den Startcursor davor und meldet dem Aufrufer "Decke erreicht" statt zu rufen. Die Seite zeigt dann die Hinweiszeile "Es gibt weitere Treffer. Grenzen Sie die Suche ein, um sie zu sehen.", die es fuer `page == MAX_PAGE` ohnehin schon gibt. Kein Container-Build, kein Protokollwechsel. Preis: eine gespiegelte Zahl, die einen Drift-Gate braucht.
2. **`SEARCH_OFFSET_MAX` anheben.** Aendert eine Sicherheitskonstante mit eigener Begruendung, zieht Python-Gates und einen Image-Build in die Phase und beantwortet die Frage nur bis zur naechsten Genehmigungsquote.

Empfehlung: Variante 1, plus ein Gate `backend/tests/test_search_limits_lockstep.py` nach dem Muster von `test_lockstep_versions.py`, das `SEARCH_OFFSET_MAX` und `SEARCH_LIMIT_MAX` gegen die beiden PHP-Konstanten liest. Textueller Vergleich, wie alle bestehenden PHP-Gates.

## Der geteilte Recheck-Dienst

**Vorschlag der Form**, damit die Planung eine konkrete Signatur diskutieren kann statt einer Idee:

```php
// php/lib/Service/SearchService.php
final class SearchService {
    public function __construct(
        private ExAppService $exApp,
        private IRootFolder $rootFolder,
        private IUserMountCache $mountCache,
        private IFileAccess $fileAccess,
        private LoggerInterface $logger,
        ?\Closure $clock = null,
    ) {}

    /**
     * @return SearchOutcome  approved hits, the next container cursor, hasMore,
     *                        degraded, and the reason when nothing could be asked
     */
    public function run(
        string $userId,
        string $term,
        bool $titleOnly,
        int $pageSize,
        int $startCursor,
        float $budgetSeconds,
    ): SearchOutcome;
}
```

`SearchOutcome` traegt: `list<ApprovedHit{fileId,title,path,mimeType}>`, `nextCursor:int`, `hasMore:bool`, `degraded:bool`, `failure:?string` mit den geschlossenen Werten `backend_silent`, `version_drift`, `no_home_folder`, `offset_ceiling`. Der Provider bildet `backend_silent` und `version_drift` weiterhin auf eine leere Gruppe ab, die Seite bildet sie auf ihre zwei Fehlerbloecke ab. Ein Enum statt eines Bools, weil die Seite drei Zustaende unterscheiden muss, die der Dialog alle gleich behandelt.

`mimeType` ist neu und wird nur von der Seite gebraucht (Dateityp-Symbol). Er kommt aus dem **bestaetigten** Node, wie Titel und Pfad, nie aus der Container-Antwort.

**Der Gate, der die Einmaligkeit haelt.** Muster: `backend/tests/test_semantic_boundary.py`. Es liest Quelltext mit entfernten Kommentaren und Stringliteralen und zaehlt Aufrufstellen. Fuer PHP: ein Gate, das in `php/lib/` zaehlt, wie viele Stellen `getFirstNodeById` und `isReadable` aufrufen. Erwartung nach der Phase: **genau eine Datei, genau eine Stelle je Aufruf, naemlich `SearchService.php`**. Ein zweiter Aufrufer ist die zweite Sicherheitsflaeche, die UI-03 verbietet, und ein funktionaler Test kann seine Abwesenheit nicht beweisen. Die Kommentar- und Stringentfernung ist hier genauso noetig wie auf der Python-Seite, weil der PHP-Bestand die Namen in Prosa erklaert: `Provider.php` erwaehnt `getFirstNodeById` heute in einem Kommentar, `SettingsController.php` erwaehnt `rejectForeignCaller` in Prosa und musste deshalb schon einmal umformuliert werden (Pitfall 7 von Phase 4).

**Reihenfolge:** der Dienst steht **vor** dem Controller. Wird die Seite zuerst gebaut, entsteht die zweite Flaeche, und sie wieder zusammenzuziehen ist teurer als sie nie zu bauen (offener Punkt 1 der 09-UI-SPEC).

## Gate B: die dritte Routenklasse

`backend/tests/test_php_trust_boundary.py`, 421 Zeilen, textueller Scan ueber `php/lib/Controller/*.php`. Heute:

| Klasse | Erkennungsmerkmal | Regel |
|--------|-------------------|-------|
| `exapp` | `#[...ApiRoute]` ueber der Methode | Muss `ExAppRequired` tragen **und** `rejectForeignCaller()` als **erste** Anweisung im Rumpf haben |
| `admin` | `#[...FrontpageRoute]` ueber der Methode | Darf **keines** aus `FORBIDDEN_ON_ADMIN_ROUTE = ("NoAdminRequired", "PublicPage", "NoCSRFRequired", "ExAppRequired")` tragen |

Eine Methode mit beiden Attributnamen zaehlt als `admin` (die strengere Klasse, Zeile 154 bis 157).

**Das Problem:** die neue Seitenroute traegt `FrontpageRoute` **plus** `NoAdminRequired` **plus** `NoCSRFRequired`. Das ist heute ein doppelter Verstoss, und die 09-UI-SPEC nennt es korrekt als Planungsvoraussetzung.

**Der Weg, der die Schutzwirkung nicht verduennt.** Nicht die Verbotsliste kuerzen, sondern eine dritte Klasse einfuehren, die an der **Attributkombination** erkannt wird und ihre **eigene** Verbotsliste bekommt:

| Klasse | Erkennung | Verboten bleibt |
|--------|-----------|-----------------|
| `admin` | `FrontpageRoute` **ohne** `NoAdminRequired` | `NoAdminRequired`, `PublicPage`, `NoCSRFRequired`, `ExAppRequired` (unveraendert) |
| `userpage` (neu) | `FrontpageRoute` **plus** `NoAdminRequired` **plus** `NoCSRFRequired`, alle drei | `PublicPage`, `ExAppRequired`. Zusaetzlich: `NoAdminRequired` und `NoCSRFRequired` sind **Pflicht**, nicht nur erlaubt |

Warum das nicht verduennt: die Admin-Klasse behaelt ihre vier Verbote woertlich. Eine Admin-Methode, der jemand `NoAdminRequired` anhaengt, wandert dadurch nicht heimlich in die lockere Klasse, sondern wird zur Nutzerseite und muss dann **auch** `NoCSRFRequired` tragen, sonst meldet der Gate eine unvollstaendige Nutzerseite. Eine halbe Absenkung ist damit weiterhin rot. Die Klasse wird an der Methode erkannt und nie am Dateinamen, das ist die bestehende Regel und bleibt es.

**Was mitwaechst:**

- Zwei neue Selbsttest-Muster nach dem Vorbild von `_GUARDED` und `_ADMIN`: ein sauberes `_USER_PAGE` und je ein schmutziges pro neuem Verbot. Der bestehende Kommentar zu diesem Punkt (Zeile 27 bis 30) sagt selbst, warum: ein Gate, dessen einzige Aussage "der aktuelle Baum ist sauber" ist, bleibt gruen, wenn jemand seinen Rumpf loescht.
- Die Anti-Vakuitaets-Klausel `assert len(routes) >= 12` (Zeile 243) steigt auf 13, samt Kommentarzeile, die die neue Route benennt. Der Kommentar sagt selbst: "Every plan that adds a route raises this bound with it".
- `test_every_controller_of_the_app_carries_at_least_one_route` bleibt automatisch gruen, weil `PageController` genau eine Route hat.

**Reihenfolge:** Gate B lernt die Klasse **bevor** der erste `PageController` existiert. Genau die Reihenfolge, die Phase 4 fuer die zweite Klasse gewaehlt hat, und aus demselben Grund: sonst steht der Baum zwischendurch rot (offener Punkt 2 der 09-UI-SPEC, bestaetigt gegen den Kommentar in `test_php_trust_boundary.py` Zeile 32 bis 47 und gegen die Decision-Liste in `.planning/STATE.md`).

## Gate C: was `test_admin_ui_contract.py` wirklich prueft

`backend/tests/test_admin_ui_contract.py`, drei Dateipfade fest verdrahtet:

```python
TEMPLATE   = REPO_ROOT / "php" / "templates" / "admin.php"
STYLESHEET = REPO_ROOT / "php" / "css"       / "admin.css"
SCRIPT     = REPO_ROOT / "php" / "js"        / "admin.js"
```

Die Scanner, exakt:

| Scanner | Prueft |
|---------|--------|
| `scan_script` | `innerHTML` und `outerHTML` als Teilstring; dazu `_deprecated` |
| `scan_template` | `print_unescaped` als Teilstring; `<script` als Teilstring; dazu `_deprecated` |
| `scan_stylesheet` | `_HEX_COLOUR` (Regex mit Negativ-Lookahead, damit `#findling-coverage` kein Treffer ist), `rgb(`/`rgba(`/`hsl(`/`hsla(`, `outline\s*:\s*none`; dazu `_deprecated` |
| `scan_prose` | Em-Dash `\u2014`, En-Dash `\u2013`, Emoji-Regex `[\U0001f000-\U0001faff\u2600-\u27bf\ufe0f]` |
| `_deprecated` | `OCP.InitialState.loadState`, `OC.getCanonicalLocale`, `OC.getLanguage`, `OC.dialogs.confirmDestructive`, `icon-info` |

Dazu drei Struktur-Tests: die drei Dateien muessen existieren (Anti-Vakuitaet), das Skript liest `dataset.requesttoken` nur eingerueckt (also innerhalb einer Funktion), und das Skript enthaelt `AbortController` und `visibilityState`.

**Was das fuer die neue Seite heisst:**

- Die drei neuen Dateien `php/templates/search.php`, `php/css/search.css`, `php/js/search.js` muessen in `_sources()` aufgenommen werden, sonst prueft der Gate sie nicht und die 09-UI-SPEC-Verbote mit `[G]` sind unbelegt.
- Die 09-UI-SPEC verbietet zusaetzlich `insertAdjacentHTML` und `document.write`. `scan_script` kennt beide heute nicht. Sie kommen als zwei neue Teilstring-Pruefungen dazu, mit je einem Selbsttest.
- `IInAppSearch` darf in keiner PHP-Datei der App vorkommen. Das ist ein neuer Scan ueber `php/lib/**/*.php`, nicht ueber die drei Seitendateien. Er gehoert in denselben Gate oder in Gate B, aber er braucht einen Selbsttest, sonst ist er wertlos. **Heutiger Stand geprueft:** `grep -rn "IInAppSearch" php/ backend/ docs/` findet null Treffer, der Gate startet also gruen.
- Die beiden Tests `test_the_script_reads_the_token_inside_the_call` und `test_the_script_polls_politely` gelten **nur** fuer `admin.js` und duerfen nicht auf `search.js` ausgeweitet werden: die neue Seite ruft nichts und pollt nichts, also gibt es weder Token noch `AbortController` noch `visibilityState`. Der Gate muss die drei Dateien in `_sources()` aufnehmen, ohne diese drei Sondertests mitzuziehen. Das ist die konkrete Stelle, an der ein unaufmerksames "einfach dieselbe Liste" den Baum rot macht.
- `test_the_two_translation_files_carry_the_same_keys` vergleicht `de.json` gegen `de.js`. Wenn `fr.json` kommt, muss `fr.js` mitkommen und der Test auf beide Sprachpaare erweitert werden.

## Paritaetstest: was die neue Route mitpruefen muss

Der Job `search-parity` (`.github/workflows/integration.yml` ab Zeile 2611) arbeitet so:

- Zwei Konten plus Team-Folder plus Gruppe, sechs Szenarien, je ein eigener Marker im Dateinamen.
- `unified_search_max_results_per_request` wird auf 100 hochgesetzt, weil `SearchQuery::LIMIT_DEFAULT` bei 5 steht.
- Eine Shell-Funktion `ask()` ruft `GET /ocs/v2.php/search/providers/{files|findling}/search?term=...&limit=100` als der jeweilige Nutzer.
- `scripts/ci/parity_diff.py` liest **beide** Antworten als JSON, extrahiert `ocs.data.entries[].attributes.fileId` und vergleicht in beide Richtungen. `missing` ist ein funktionaler Defekt, `extra` ein Sicherheitsdefekt. `--expect-min` verhindert eine gruene Aussage ueber zwei leere Mengen.

**Die neue Route liefert HTML, nicht JSON.** `_file_ids()` wuerde an `json.loads` scheitern und `MalformedAnswer` werfen, also Exitcode 3. Drei Wege:

1. **Dritter Eingabemodus in `parity_diff.py`** (empfohlen). Ein `--findling-html`-Pfad, der die `fileId` aus `id="findling-hit-<n>"` liest. Die Zeilen-Id steht in der 09-UI-SPEC ohnehin als Anker der Rueckkehr-Markierung, sie ist also kein Testartefakt, sondern schon Vertrag. Der Extraktor faellt genauso hart aus wie der JSON-Extraktor: eine Seite ohne `<ol>` und ohne Trefferzeile ist `MalformedAnswer` und nie die leere Menge. `backend/tests/test_parity_diff.py` existiert bereits und bekommt die Faelle dazu.
2. Ein `?format=json` an der Seitenroute. **Abgelehnt:** das ist der zweite Suchweg, den die 09-UI-SPEC ausdruecklich verbietet, und er waere eine Route, die den ganzen Rechte-Pfad noch einmal beweisen muesste.
3. Die Seite gar nicht in den Paritaetsjob nehmen. **Abgelehnt:** Erfolgskriterium 4 verlangt woertlich, dass der bestehende Paritaetstest die neue Route mitdeckt.

Der Aufruf muss mit Session-Cookie laufen, nicht mit Basic-Auth plus `OCS-APIRequest`. Praktischer Weg im Job: `curl` mit Cookie-Jar gegen `/login`, Requesttoken aus der Login-Seite, danach `GET /apps/findling/?query=...&limit`-frei. Weil die Route `NoCSRFRequired` traegt, braucht der GET selbst kein Token; das Token wird nur fuer den Login-POST gebraucht. Das ist ein neuer Schritt im Job und die aufwendigste Einzelaufgabe der Phase auf der CI-Seite.

Die Seitengroesse 25 gegen `--expect-min` beachten: die Szenarien vergleichen wenige Dateien, aber ein Szenario mit mehr als 25 Treffern wuerde auf der Seite nur die erste Seite liefern. Entweder `--expect-min` klein halten oder alle Seiten abklappern. Empfehlung: die vorhandenen Szenarien haben alle deutlich unter 25 Treffer, also reicht Seite 1, und das gehoert als Satz in den Job-Kommentar, damit ein spaeteres Szenario mit 30 Dateien nicht stillschweigend falsch vergleicht.

## Navigationseintrag und `php/img/app.svg`

**Bestand:** `php/img/` enthaelt genau eine Datei, `app-dark.svg`, ein `magnify` von Material Design Icons mit `fill="currentColor"`, `viewBox="0 0 24 24"`, 16 x 16. `php/lib/Settings/Section.php` Zeile 65 referenziert sie ueber `imagePath(APP_ID, 'app-dark.svg')`.

**Warum `app.svg` wirklich fehlt** [VERIFIED: nextcloud/server stable34 lib/private/App/AppManager.php Zeile 117 bis 129]:

```php
public function getAppIcon(string $appId, bool $dark = false): ?string {
    $possibleIcons = $dark ? [$appId . '-dark.svg', 'app-dark.svg']
                           : [$appId . '.svg', 'app.svg'];
    ...
}
```

Der Navigationseintrag laeuft ueber `NavigationManager::init()` [VERIFIED: nextcloud/server stable34 lib/private/NavigationManager.php Zeile 315 bis 375]: wenn `<icon>` gesetzt ist, wird `imagePath($app, $icon)` versucht; schlaegt das fehl oder fehlt `<icon>`, greift `getAppIcon($app)` **ohne** `$dark`, sucht also `findling.svg` und `app.svg` und findet keine von beiden. Danach faellt es auf `core/places/default-app-icon.svg` zurueck. Ergebnis heute: ein generisches Platzhaltersymbol im App-Menue.

**Kleinster sauberer Weg:** `php/img/app.svg` als inhaltsgleiche Kopie von `app-dark.svg` anlegen. Beide sind schwarz (`currentColor` in einem `<img src>` loest zur SVG-eigenen Standardfarbe auf, also Schwarz), und genau das erwartet Nextcloud fuer `app.svg`: der Server themt es per CSS-Filter fuer die Kopfleiste. Kein neuer Symbolsatz, keine zweite Lizenzfrage, kein neuer MDI-Name.

**Was mitwaechst:** `THIRD-PARTY.md` Zeile 210 nennt heute woertlich, wo jedes der neun Symbole landet, und `magnify` steht dort nur mit `php/img/app-dark.svg`. Der zweite Ort kommt in dieselbe Zeile. Die drei **neuen** Namen `chevron-left`, `chevron-right`, `file-search-outline` kommen in die Aufzaehlung in Zeile 209 und in die Pruefschleife in Zeile 278, in dem Plan, der sie zuerst rendert.

**Wo `<navigations>` in `info.xml` hin muss** [VERIFIED: nextcloud/appstore info.xsd, gepinnter Commit `eda850ba61407c6e4da3e23316614c6126406652`, derselbe, den `.github/workflows/php.yml` validiert]:

Die `xs:sequence` des Wurzeltyps ordnet: `... commands, settings, activity, dashboard, fulltextsearch, navigations, contactsmenu, ...`. Die heutige `php/appinfo/info.xml` endet mit `<settings>`. `<navigations>` gehoert also **hinter** `<settings>`, ans Dateiende. Eine falsche Position ist ein harter Validierungsfehler im Job `app-metadata`.

Der Typ:

```xml
<navigations>
  <navigation>
    <id>...</id>      <!-- optional -->
    <name>...</name>  <!-- PFLICHT, non-empty-string -->
    <route>...</route><!-- Pattern: [0-9a-zA-Z_]+(\.[0-9a-zA-Z_]+){2} -->
    <icon>...</icon>  <!-- xs:anyURI -->
    <order>...</order><!-- xs:int -->
    <type>...</type>  <!-- link | settings -->
  </navigation>
</navigations>
```

`findling.page.index` passt auf das Routenmuster (genau drei Segmente). `<name>Findling</name>` wird von `NavigationManager` durch `$l->t($nav['name'])` geschickt, also ueber den l10n-Katalog der App uebersetzt; `Findling` steht dort bereits als Schluessel. `pre-info.xslt` kopiert `navigations` und jedes Kind einzeln durch (Zeile 96 bis 131), es wird also **nicht** wie `<routes>` verworfen und **nicht** wie `<settings>` geleert. Der Job-Schritt "State the settings finding explicitly" bleibt davon unberuehrt.

## Einstiegspunkt aus der Unified Search

`Provider::toEntries()` baut heute pro Treffer:

```php
$entry = new SearchResultEntry(
    thumbnailUrl: '', title: $hit['title'],
    subline: $excerpt === null ? $hit['subline'] : $excerpt['text'],
    resourceUrl: $this->resourceUrl($fileId), icon: 'icon-search',
);
$entry->addAttribute('fileId', (string)$fileId);
```

Der Zusatzeintrag ist derselbe Konstruktor mit `title` = uebersetztes "Show all results", `subline` = "Opens the Findling results page", `icon` = `icon-search`, `thumbnailUrl` = `''`, `resourceUrl` = `linkToRoute('findling.page.index', ['query' => $term] + ($titleOnly ? ['names' => '1'] : []))`, und **ohne** `addAttribute('fileId', ...)`. `IURLGenerator::linkToRoute()` haengt Parameter, die kein Routenplatzhalter sind, als Query-String an; `page` und `cursors` bleiben weg, der Einstieg ist immer Seite 1.

Eingefuegt wird er **nach** `toEntries()` und nur wenn `$exhausted === false`. Er darf nirgends gegen `$limit` zaehlen. Die Rueckgabeform bleibt `SearchResult::paginated($name, $entries, $offset)`, damit die Cursorsemantik des Dialogs unangetastet bleibt.

Ein Detail, das die Planung nicht uebersehen darf: `$approved === []` fuehrt heute in Zeile 397 zu einem fruehen `SearchResult::complete($this->getName(), [])`. Bei null genehmigten Treffern ist `$exhausted` irrelevant, der Einstieg erscheint also korrekterweise nicht. Bei genehmigten Treffern und `$exhausted === false` erscheint er. Das ist genau die Regel der 09-UI-SPEC, sie faellt hier aber nicht von selbst heraus, sondern muss an der richtigen der beiden Rueckgabestellen eingebaut werden.

## Positions-Wiederherstellung: was der Browser wirklich tut

Die 09-UI-SPEC nimmt an, Stufe 2 des Rueckkehrvertrags sei geschenkt, weil ein gewoehnliches Dokument seine Scrollposition beim Zurueck selbst wiederherstellt. Gegen die echten Nextcloud-Quellen geprueft, stimmt das so nicht.

**Befund 1: `#app-content` ist ein eigener Scroll-Container.** [VERIFIED: nextcloud/server, `core/css/apps.scss`, in stable33, stable34 und stable35 byte-gleich an Zeile 742]

```scss
#app-content {
    z-index: 1000;
    background-color: var(--color-main-background);
    flex-basis: 100vw;
    overflow: auto;      /* <- hier */
    position: initial;
    height: 100%;
}
```

und darueber, Zeile 702 bis 716:

```scss
#content {
    display: flex;
    height: var(--body-height);
    overflow: clip;
    &:not(.with-sidebar--full) { position: fixed; }
}
```

Das Dokument selbst scrollt also nicht. `history.scrollRestoration` wirkt auf `document.scrollingElement`, und dessen Offset ist hier immer 0. Ob ein Browser die Scrollposition eines **verschachtelten** Scroll-Containers ueber eine Navigation hinweg wiederherstellt, ist nicht spezifiziert und unterscheidet sich zwischen Firefox und Chromium.

**Befund 2: jede AppFramework-Antwort traegt `Cache-Control: no-cache, no-store, must-revalidate`.** [VERIFIED: nextcloud/server stable34 `lib/public/AppFramework/Http/Response.php` Zeile 237, Standardwert im Header-Array; Zeile 104 setzt denselben Wert in `cacheFor(0)`]

`no-store` ist der klassische Ausschlussgrund fuer den Back-Forward-Cache. Firefox nennt "cache-control: no-store" ausdruecklich als programmatischen Grund, eine Seite nicht in den bfcache zu legen. Chrome hat das seit den Experimenten ab Version 116 aufgeweicht und laesst CCNS-Seiten inzwischen in den bfcache, wirft sie aber bei jeder Cookie- oder Autorisierungsaenderung wieder heraus. [CITED: developer.chrome.com/docs/web-platform/bfcache-ccns] [CITED: web.dev/articles/bfcache]

**Folgen fuer die Planung:**

- Der `pageshow`-Handler mit `event.persisted === true` wird in Firefox praktisch nie feuern. Das Skript darf sich nicht darauf verlassen; es muss auf `pageshow` **unabhaengig** von `persisted` arbeiten, so wie die 09-UI-SPEC es ohnehin beschreibt.
- `performance.getEntriesByType('navigation')[0].type === 'back_forward'` funktioniert weiterhin, auch ohne bfcache: der Navigationstyp wird unabhaengig vom Cache gemeldet. Die Fokusregel der 09-UI-SPEC bleibt also gueltig.
- `scrollIntoView({block: 'center'})` auf einer Trefferzeile scrollt den naechsten scrollbaren Vorfahren, und das ist `#app-content`. Die Mechanik der Stufe 3 funktioniert also. Sie ist aber **nicht** mehr die Zugabe, als die die 09-UI-SPEC sie beschreibt, sondern der tragende Teil der Positionswiederherstellung.
- Die Bedingung "nur wenn die Zeile nicht ohnehin im Sichtfeld ist" bleibt richtig und wird in der Praxis fast immer wahr sein, weil `#app-content` nach einer echten Neuladung oben steht.
- **Abnahme-Sichtprobe 5 der 09-UI-SPEC ist so nicht haltbar.** Sie verlangt bei abgeschaltetem JavaScript "dieselbe Scrollposition, vom Browser". Nach obigem Befund ist das browserabhaengig und in Firefox unwahrscheinlich. Die Sichtprobe gehoert umformuliert auf: dieselbe Seite 3, dieselbe Suche, keine Markierung, keine Fehlermeldung, und die Scrollposition ist das, was der Browser gibt.

Eine dritte Moeglichkeit existiert und ist **nicht** empfohlen: den `Cache-Control`-Header der Seitenantwort auf `private, no-cache, must-revalidate` senken, um bfcache zu ermoeglichen. Das legt eine nutzerspezifische Trefferliste mit Dateinamen und Textauszuegen in den Plattencache des Browsers. Auf einem geteilten Rechner ist das eine neue Preisgabe fuer einen Komfortgewinn. Wenn die Planung es dennoch erwaegen will, ist es eine Owner-Entscheidung und kein Implementierungsdetail.

## Zeitbudget der Seitenroute: wie gemessen wird

Der offene Punkt 4 der 09-UI-SPEC verlangt Messen statt Raten. Die Voraussetzungen sind da.

**Der harte Deckel, der zuerst weg muss.** `ExAppService::call()` Zeile 616:

```php
$timeout = min(self::REQUEST_TIMEOUT_SECONDS, $secondsLeft);
```

`REQUEST_TIMEOUT_SECONDS` ist 1.5 und privat. Ein groesseres Zeitbudget der Seitenroute wirkt deshalb heute **nur** darauf, wie viele Runden gefahren werden, nie darauf, wie lange ein einzelner Aufruf warten darf. Wenn die Messung ergibt, dass ein einzelner Aufruf bei 100 angefragten Kandidaten laenger als 1.5 s braucht, muss der Deckel ein Argument werden: entweder ein zweiter Konstantenwert `PAGE_REQUEST_TIMEOUT_SECONDS` mit eigenem Aufrufpfad, nach dem Vorbild von `ADMIN_REQUEST_TIMEOUT_SECONDS`, oder ein optionaler Ceiling-Parameter. Der erste Weg passt besser zum Bestand: `adminGet()` ist genau aus diesem Grund eine eigene Methode neben `call()`, und der Kommentar dort begruendet es ausdruecklich damit, dass ein Aufrufer nie eine Regel lesen soll, die nicht seine ist.

**Die Messumgebung ist vorhanden und laeuft.** [VERIFIED: `docker ps` am 08.09.2026]

| Fakt | Wert |
|------|------|
| Container | `findling-nextcloud`, Image `nextcloud:34.0.3-apache`, Up 6 Tage |
| Port | 8090 auf allen Interfaces, `status.php` antwortet 200 |
| Server | 34.0.3.2, `installed: true`, `maintenance: false`, **`needsDbUpgrade: true`** |
| Installierte App | `findling: 0.3.0` (das Repo steht bei 1.0.3, die Instanz ist also aelter) |
| Compose | `C:\Users\Student\nextcloud-search\scripts\dev\compose.yaml` |
| Nutzer und Korpus | `testuser` / `kollegin` plus `testdata/corpus`, Anleitung in `docs/dev-setup.md` |
| Bremse fuer die stumme Haelfte | `scripts/ci/slow_backend.py` |
| Auf der Maschine **nicht** vorhanden | PHP (`php` fehlt), also kein lokaler PHPUnit-Lauf, kein lokales `php -l` ausserhalb des Containers |

**Das Messverfahren, konkret:**

1. `needsDbUpgrade` zuerst aufloesen (`occ upgrade` im Container), sonst misst man einen Wartungszustand.
2. Die Instanz auf den Repo-Stand bringen (Compose bindet `php/` ein, aber die App-Version 0.3.0 deutet auf einen alten Stand; `occ app:update` bzw. Neuinstallation vor der Messung).
3. Korpus so weit fuellen, dass ein Suchbegriff mehr als 100 Kandidaten hat. `testdata/corpus` reicht dafuer moeglicherweise nicht; `scripts/dev/build_load_corpus.py` existiert und erzeugt einen groesseren Bestand.
4. Drei Messreihen, je 20 Wiederholungen, mit `curl -w '%{time_total}'` gegen die Seitenroute, aufgeteilt nach dem Weg der Zeit:
   - Reihe A: `titleOnly=1`, ein Wort. Rein lexikalisch, kein Vektorlauf.
   - Reihe B: ein Wort, `titleOnly=0`. Nach `one_round()` in `search.py` ist ein Ein-Wort-Suchlauf `lexical_only`, also ebenfalls ohne Vektorseite.
   - Reihe C: zwei Woerter, `titleOnly=0`. Das ist der hybride Fall mit `SEARCH_VECTOR_DEPTH = 300` pro Runde, und **das ist der teure**.
5. Getrennt messen: Kandidatenaufruf, Recheck-Schleife, Snippet-Aufruf. Am billigsten ueber `logger->debug`-Zeitmarken im geteilten Dienst, die nur bei aktivem Debug-Log geschrieben werden, oder ueber drei separate `curl`-Laeufe gegen die Container-Routen direkt (der Container ist ueber den AppAPI-Proxy erreichbar, siehe `docs/dev-setup.md`).
6. Das Budget ist p95 der Reihe C plus 50 Prozent Reserve, gerundet auf halbe Sekunden, und die Zahl kommt mit ihrem Messdatum in den Kommentar der Konstante. So haelt es der ganze Bestand (siehe die Kommentare an `SEARCH_VECTOR_DEPTH`, `OCR_DPI`, `MAX_RECHECKS_PER_HIT`).

**Erwartungshaltung, damit die Messung eine Aussage widerlegen kann:** die Seitenroute holt pro Runde bis zu 100 Kandidaten statt bis zu 80 (`20 * 4`) im Dialog, also rund ein Viertel mehr Engine-Arbeit pro Runde bei gleicher Rundenzahl. Der Vektoranteil aendert sich gar nicht, weil `SEARCH_VECTOR_DEPTH` nicht am `limit` haengt. Die Recheck-Schleife waechst dagegen linear mit der Seitengroesse: bis zu 50 statt bis zu 40 `getFirstNodeById`-Aufrufe. Die plausible Groessenordnung ist also "wie der Dialog, plus ein Viertel", nicht "doppelt". Wenn die Messung deutlich mehr zeigt, ist das ein Befund und keine Bestaetigung.

## Phase-7-Erbe: reiner Read-Path, bestaetigt

Die Erwartung stimmt. Belegt:

- Der Engine-Halter liegt in `backend/src/findling/embed/engine.py`, `shared_model()` baut die Huelle und **laedt nichts**; geladen wird beim ersten Text, der die Engine erreicht.
- `LOAD_RETRY_SECONDS = 300.0` in `backend/src/findling/embed/model.py` Zeile 132 ist die 300-Sekunden-Karenz. Sie wird von einem fehlgeschlagenen Ladeversuch gesetzt, nicht von einer Route.
- `api/resources.py::query_model()` ist ein reiner Durchreicher auf `shared_model()`.
- In `api/search.py::one_round()` wird die semantische Seite nur gebaut, wenn `not lexical_only and side.vectors is not None and settings().embed_enabled`. `lexical_only` ist wahr bei Operatoren, bei einem einzigen Term und bei `titleOnly`.

Die neue Seitenroute ruft **dieselben zwei Container-Routen** wie der Dialog, mit denselben Feldern. Sie kann den Engine-Lebenszyklus nur genauso ausloesen, wie eine Dialogsuche es heute tut, und sie fuegt keinen neuen Zeitpunkt und keinen neuen Zustand hinzu. Es gibt keine Aenderung an `worker/`, an `embed/` oder an `resources.py` in dieser Phase.

Ein Nebeneffekt, der benannt gehoert und kein Defekt ist: eine Seite mit 25 Treffern loest bis zu 3 Runden mit je bis zu `SEARCH_VECTOR_DEPTH = 300` Chunk-Treffern aus, genau wie eine Dialogsuche. Wer viel blaettert, bezahlt pro Seite einen vollen Vektorscan. Das ist die bekannte Eigenschaft von sqlite-vec brute force und steht seit dem Stack-Entscheid so im Projekt.

## l10n-Bestand

| Fakt | Befund |
|------|--------|
| Verzeichnis | `php/l10n/` enthaelt genau zwei Dateien: `de.js` und `de.json` |
| Sprachen | Nur Deutsch. Kein `fr`, kein `en` (Quell-Strings sind Englisch und laufen ohne Katalog durch) |
| Schluesselzahl | 149 Eintraege in `de.json` |
| Format `de.json` | `{"translations": {"<quelle>": "<uebersetzung>", ...}, "pluralForm": ...}` |
| Format `de.js` | `OC.L10N.register("findling", { ... }, "nplurals=2; plural=(n != 1);");` |
| Echte Umlaute | Ja, in den deutschen Werten (`Deckungsgrad`, `zu groß`), wie die Projektregel es verlangt |
| Gate | `test_admin_ui_contract.py::test_the_two_translation_files_carry_the_same_keys` vergleicht die Schluesselmengen von `de.json` und `de.js` |

Die 24 neuen Copy-Elemente sind neue Schluessel in **beiden** deutschen Dateien. Fuer Franzoesisch braucht es `fr.json` **und** `fr.js`, sonst uebersetzt der Browser-Teil nicht. Empfehlung zu Open Question 3 siehe unten.

Ein Punkt, den die Copy-Tabelle offen laesst: die Seite hat **keinen** JavaScript-sichtbaren Text ausser dem Screenreader-Satz "zuletzt geoeffnet". Der kommt aus dem Template (`.hidden-visually`-Span, serverseitig gerendert, per `hidden` geschaltet), nicht aus `search.js`. Damit braucht `search.js` gar keinen l10n-Zugriff, was den `de.js`-Teil auf null neue Schluessel reduzieren wuerde. Der Gate vergleicht aber die Schluesselmengen der beiden Dateien, also muessen die neuen Schluessel trotzdem in beide. Das ist kein Widerspruch, nur eine Stelle, an der ein Plan versucht sein koennte, `de.js` zu ueberspringen.

## Architecture Patterns

### System Architecture Diagram

```
                    Browser
                       |
     +-----------------+------------------------+
     |                                          |
 (A) Unified-Search-Dialog                 (B) GET /apps/findling/
     |  OCS /search/providers/findling/search       ?query=&names=&page=&cursors=
     |                                          |
     v                                          v
 Provider::search()                       PageController::index()
 (IFilteringProvider)                     (FrontpageRoute + NoAdminRequired
     |                                     + NoCSRFRequired)
     |                                          |
     |   Parameter pruefen: query<=255,          |  Parameter pruefen, ungueltig
     |   Cursor aus ISearchQuery                 |  -> still auf page=1, cursors=0
     |                                          |
     +------------------+-----------------------+
                        |
                        v
              SearchService::run(userId, term, titleOnly,
                                 pageSize, startCursor, budget)
                        |
             +----------+-----------+
             |                      |
             v                      |
    driftOnRecord()  ---(drift)---> | failure = version_drift
             |                      |
             v                      |
    getUserFolder() --(throws)----> | failure = no_home_folder
             |                      |
             v                      |
    IUserMountCache::getMountsForUser()   (einmal pro Lauf)
             |
             v
   +---- Runden-Schleife (max 3, Deadline, Recheck-Budget) ----+
   |                                                            |
   |   ExAppService::searchCandidates(limit=pageSize*4,         |
   |                                  offset=cursor)            |
   |            |                                               |
   |            +--> Container POST /search                     |
   |            |      -> {candidates[fileId,score,mtime],       |
   |            |          hasMore, nextOffset, degraded}        |
   |            |      -> null bei 4xx/5xx/Timeout              |
   |            |         (auch bei offset > 1200!)             |
   |            v                                               |
   |   IFileAccess::getByFileIds()   (guenstige Reduktion)      |
   |            v                                               |
   |   pro Kandidat: getFirstNodeById -> instanceof File        |
   |                 -> isReadable()  <-- DIE Sicherheitsgrenze |
   |                 -> Titel, Pfad, MimeType aus dem Node      |
   |                                                            |
   +----------------------------+-------------------------------+
                                |
                                v
              ExAppService::snippets(approvedFileIds)
                                |
                                +--> Container POST /snippets
                                       -> {text, highlights[[start,end],...]}
                                |
                                v
                        SearchOutcome
                        {hits[], nextCursor, hasMore, degraded, failure}
                                |
             +------------------+------------------+
             |                                     |
             v                                     v
   Provider::toEntries()                  templates/search.php
   -> SearchResultEntry[]                 -> h1, Formular, Banner,
   + Einstiegs-Eintrag falls              -> <ol> mit Trefferzeilen,
     !exhausted                              Highlights per mb_substr
   -> SearchResult::paginated()              in <mark> zerlegt, jedes
             |                                Stueck einzeln escaped
             v                              -> Paginierungslinks
   Suchdialog (Vue, Core)                  -> css/search.css, js/search.js
                                                     |
                                                     v
                                           Browser: sessionStorage
                                           'findling:lasthit',
                                           pageshow -> Markierung,
                                           scrollIntoView, Fokus
```

### Empfohlene Dateistruktur (nur die neuen und geaenderten)

```
php/
├── appinfo/info.xml            # + <navigations> HINTER <settings>
├── img/
│   ├── app-dark.svg            # unveraendert
│   └── app.svg                 # NEU, inhaltsgleiche Kopie
├── lib/
│   ├── Controller/
│   │   └── PageController.php  # NEU, genau eine Route
│   ├── Search/Provider.php     # GEAENDERT: ruft SearchService, haengt Einstieg an
│   └── Service/
│       └── SearchService.php   # NEU, die eine Sicherheitsgrenze
├── css/search.css              # NEU
├── js/search.js                # NEU
├── templates/search.php        # NEU
├── l10n/de.json, de.js         # + 24 Schluessel
└── tests/Unit/
    ├── SearchServiceTest.php   # NEU, uebernimmt die Faelle aus ProviderTest
    └── ProviderTest.php        # GEAENDERT, schrumpft auf Durchreichen und Rendern

backend/tests/
├── test_php_trust_boundary.py  # + dritte Routenklasse, + Selbsttests, Bound 12 -> 13
├── test_admin_ui_contract.py   # + drei neue Dateien, + zwei neue Skript-Verbote,
│                               #   + IInAppSearch-Scan, + fr-Katalogpaar falls Open Q3 ja
├── test_parity_diff.py         # + HTML-Extraktor-Faelle
└── test_search_limits_lockstep.py  # NEU, falls die Offset-Decke gespiegelt wird

scripts/ci/parity_diff.py       # + --findling-html
.github/workflows/integration.yml  # search-parity: Login mit Cookie, Seitenroute abfragen
THIRD-PARTY.md                  # + drei MDI-Namen, + zweiter Ort fuer magnify
docs/testing.md                 # + die neuen Verhalten in der Liste
```

### Pattern 1: Vier Konstanten werden vier Argumente

**Was:** Die Recheck-Schleife bleibt woertlich, aber `BUDGET_NANOSECONDS`, `MAX_ROUNDS`, `OVERFETCH` und die Recheck-Deckel kommen von aussen.

**Wann:** Beim Extrahieren des geteilten Dienstes, in einem einzigen Schritt. Extrahieren und parametrisieren getrennt zu machen erzeugt einen Zwischenstand, in dem der Provider seine eigenen Konstanten an einen Dienst uebergibt, der sie selbst schon hat.

```php
// Source: abgeleitet aus php/lib/Search/Provider.php Zeile 241 bis 258
$recheckBudget = min($caps->recheckAbsolute, $pageSize * $caps->recheckPerHit);
$deadline = ($this->clock)() + (int)($budgetSeconds * 1_000_000_000);

for ($round = 0; $round < $caps->maxRounds; $round++) {
    if (count($approved) >= $pageSize || $rechecks >= $recheckBudget || ($this->clock)() >= $deadline) {
        break;
    }
    $fetchLimit = min($pageSize * $caps->overfetch, $recheckBudget - $rechecks + $pageSize);
    // ...
}
```

**Anti-Pattern:** die Werte als optionale Argumente mit Defaults in die Methode zu haengen. Dann ruft der Provider `run($uid, $term, $titleOnly)` und die Seite `run($uid, $term, $titleOnly, 25, $cursor, 6.0)`, und niemand sieht mehr, welche Zahl wo gilt. Ein kleines, benanntes Wertobjekt macht beide Aufrufer gleich lesbar.

### Pattern 2: Highlights serverseitig in `<mark>`, mit eigener Sortierung

**Was:** `filterHighlights()` prueft Grenzen und Anzahl, sagt aber nichts ueber die Reihenfolge zu. Der Renderer sortiert selbst und verwirft Ueberlappungen.

**Wann:** In jeder Trefferzeile mit Snippet.

```php
// Source: Verhalten abgeleitet aus php/lib/Service/ExAppService.php::filterHighlights
// und php/lib/Text/PlainText.php (die Bereinigung ist laengentreu, deshalb
// zeigen die Offsets nach PlainText::bounded weiterhin auf die richtigen Zeichen)
usort($ranges, static fn (array $a, array $b): int => $a[0] <=> $b[0]);

$out = '';
$cursor = 0;
foreach ($ranges as [$start, $end]) {
    if ($start < $cursor || $end <= $start) {
        continue; // ueberlappend oder rueckwaerts: verwerfen, nicht reparieren
    }
    $out .= htmlspecialchars(mb_substr($text, $cursor, $start - $cursor), ENT_QUOTES, 'UTF-8');
    $out .= '<mark>' . htmlspecialchars(mb_substr($text, $start, $end - $start), ENT_QUOTES, 'UTF-8') . '</mark>';
    $cursor = $end;
}
$out .= htmlspecialchars(mb_substr($text, $cursor), ENT_QUOTES, 'UTF-8');
```

`mb_substr`, nicht `substr`: Zeichen-Offsets, keine Byte-Offsets. Das ist Abnahme-Sichtprobe 15 der 09-UI-SPEC und die einzige Stelle der Seite, an der ueberhaupt HTML aus Daten entsteht.

**Warum die Bereinigung nicht stoert:** `PlainText::bounded()` ersetzt ein Steuerzeichen durch **ein** Leerzeichen, ist also laengentreu, und der Kommentar in der Datei sagt ausdruecklich, dass diese Eigenschaft tragend ist, weil `ExAppService` die Laengen vergleicht, um zu entscheiden, ob die Offsets noch stimmen.

**Anti-Pattern:** die Offsets an den Browser geben und dort `<mark>` bauen. Das waere Markup aus einer Zeichenkette im Skript, und Gate C verbietet es woertlich.

### Anti-Patterns to Avoid

- **Einen zweiten `getFirstNodeById`-Aufrufer bauen.** Genau das verbietet UI-03. Der Zaehl-Gate ist die einzige Konstruktion, die es dauerhaft haelt.
- **Die Verbotsliste `FORBIDDEN_ON_ADMIN_ROUTE` kuerzen, um die neue Route durchzulassen.** Damit waere jede Admin-Route der App mit einem Schlag ungeschuetzt. Die dritte Klasse ist die einzige Antwort, die nichts wegnimmt.
- **`page=N` in einen Offset umrechnen.** Die 09-UI-SPEC begruendet das ausfuehrlich, der Code bestaetigt es: `$offset` waechst um die Zahl der entschiedenen Kandidaten, nicht um die Zahl der angezeigten.
- **Den Dateinamen oder Pfad aus `$candidate` nehmen.** Der Container schickt beides gar nicht (Modell `Candidate` hat drei Felder), aber der Canary-Pfad hat einen `title`, und ein unaufmerksames Rendern koennte ihn benutzen.
- **`page` und `cursors` in der `action` des Formulars lassen.** Jede neue Suche beginnt auf Seite 1, sonst zeigt die Seite Seite 7 einer Suche, die nur zwei Seiten hat.
- **`insertAdjacentHTML` in `search.js`.** Heute prueft Gate C es nicht. Es steht in der Verbotsliste der 09-UI-SPEC. Ohne die Gate-Erweiterung ist das Verbot ein Satz ohne Wirkung.

## Don't Hand-Roll

| Problem | Nicht bauen | Stattdessen | Warum |
|---------|-------------|-------------|-------|
| Zweite Berechtigungspruefung fuer die Seite | Eine eigene Recheck-Schleife im Controller | `SearchService::run()`, derselbe Aufruf wie der Provider | UI-03. Zwei Schleifen driften garantiert, und die zweite wird nie so gut getestet wie die erste |
| Dateityp-Symbole | Einen eigenen Symbolsatz pro Mimetype | `IMimeTypeDetector::mimeTypeIcon()` | Der Server hat die Zuordnung fuer alle Typen, gethemt, seit 8.2.0, ohne zweite Lizenzfrage |
| Screenreader-Text verstecken | Eigene CSS-Klasse mit `position: absolute; left: -10000px` | Core-Klasse `.hidden-visually` | Steht in `core/css/global.scss`, in allen drei Zweigen, und ist genau diese Regel |
| Scrollposition merken | Position in `sessionStorage` schreiben und beim Laden `scrollTop` setzen | Die Zeilen-Id merken und `scrollIntoView` | Eine Pixelzahl ist nach einem Themewechsel, einer anderen Fensterbreite oder einem anderen Snippet falsch. Ein Anker nicht |
| Escaping im Template | Eigene Escaping-Funktion | `p()` fuer jeden Wert, `htmlspecialchars(..., ENT_QUOTES, 'UTF-8')` im Highlight-Renderer | Gate C prueft die Abwesenheit von `print_unescaped`. Eine eigene Funktion waere ein Weg daran vorbei |
| Text bereinigen und kuerzen | Eigene `substr`-Logik fuer Titel und Pfad | `PlainText::bounded()` | Existiert, ist laengentreu, faengt ungueltiges UTF-8 ab, und die Laengentreue traegt die Highlight-Offsets |
| Paginierungs-URLs bauen | Zeichenketten zusammenkleben | `IURLGenerator::linkToRoute('findling.page.index', [...])` | Baut den Query-String korrekt und beruecksichtigt `overwritewebroot` |
| Fileids aus der Seite fuer den Paritaetstest | Einen Vue-Renderer oder einen HTML-Parser mitbringen | Eine Regex auf `id="findling-hit-(\d+)"` in `parity_diff.py` | Standardbibliothek ist Pflicht in dieser Datei (Modul-Docstring sagt es ausdruecklich), und die Id ist bereits Vertrag |

**Key insight:** Diese Phase ist fast vollstaendig eine Umverdrahtung von Vorhandenem. Jede Zeile, die etwas neu erfindet, das der Provider oder der Core schon kann, ist ein Kandidat fuer eine Nachfrage im Plan-Check.

## Common Pitfalls

### Pitfall 1: Die Offset-Decke des Containers meldet sich als "Backend stumm"

**Was schiefgeht:** Der Nutzer blaettert auf Seite 14, der Startcursor liegt bei 1240, der Container antwortet 422, `ExAppService::call()` protokolliert "backend returned an error" und liefert `null`, der Dienst meldet "kein Ergebnis", und die Seite zeigt "Die Suche antwortet gerade nicht. Findling konnte sein Backend nicht erreichen."

**Warum es passiert:** `SEARCH_OFFSET_MAX = SEARCH_LIMIT_MAX * SEARCH_OVERFETCH * SEARCH_ROUNDS` = 1200, und ein Anzeige-Offset ist kein Container-Offset. Der Kommentar an der Konstante sagt "No legitimate cursor ever climbs past a full result set of overfetched, multi-round candidates" und meint damit **einen** Dialogaufruf, nicht zwanzig verkettete Seiten.

**Wie vermeiden:** Der geteilte Dienst prueft den Startcursor gegen eine gespiegelte PHP-Konstante, **bevor** er ruft, und meldet `offset_ceiling` statt `backend_silent`. Die Seite bildet das auf die vorhandene Hinweiszeile "Es gibt weitere Treffer. Grenzen Sie die Suche ein" ab, nicht auf den Fehlerblock. Dazu ein Lockstep-Gate ueber beide Zahlen.

**Warnzeichen:** Ein 422 mit `path: /search` im Nextcloud-Log, waehrend `occ findling:index` einen gesunden Container meldet.

### Pitfall 2: Stufe 2 des Rueckkehrvertrags existiert nicht so, wie sie beschrieben ist

**Was schiefgeht:** Die Abnahme laeuft in Chrome, alles sieht gut aus, in Firefox landet der Nutzer nach dem Zurueck oben in der Liste, und die Sichtprobe mit abgeschaltetem JavaScript scheitert reproduzierbar.

**Warum es passiert:** `#app-content` ist der Scroll-Container, nicht das Dokument, und jede AppFramework-Antwort traegt `no-store`, was Firefox vom bfcache ausschliesst.

**Wie vermeiden:** Stufe 3 als tragend planen, nicht als Zugabe. `pageshow` ohne Abhaengigkeit von `event.persisted`. `scrollIntoView` auf der Zeile (scrollt korrekt `#app-content`). Abnahme-Sichtprobe 5 umformulieren.

**Warnzeichen:** Eine Implementierung, die `if (event.persisted)` als Bedingung hat, oder ein Test, der nur in einem Browser laeuft.

### Pitfall 3: Ein groesseres Zeitbudget, das nichts bewirkt

**Was schiefgeht:** Die Seitenroute bekommt 6 Sekunden Budget, die Messung zeigt keine Verbesserung gegenueber 2.5 Sekunden, und niemand versteht warum.

**Warum es passiert:** `ExAppService::call()` deckelt jeden Aufruf auf `min(1.5, $secondsLeft)`. Ein groesseres Budget kauft nur mehr Runden, nie mehr Geduld pro Runde. Wenn ein Kandidatenaufruf bei 100 Treffern laenger als 1.5 s braucht, laeuft er in den Timeout, `call()` liefert `null`, die Runde bricht ab, und mehr Budget aendert daran nichts.

**Wie vermeiden:** Vor der Budget-Entscheidung messen, wie lange **ein** Kandidatenaufruf mit `limit=100` dauert. Erst danach entscheiden, ob nur `BUDGET_NANOSECONDS` oder auch der Per-Call-Deckel ein Parameter wird.

**Warnzeichen:** Kurze Seiten mit "Weiter"-Knopf bei einem Nutzer, dessen Kandidaten fast alle genehmigt werden. Das ist dann kein ACL-Effekt, sondern ein Timeout.

### Pitfall 4: Gate C zieht die Admin-Sondertests auf die neue Seite mit

**Was schiefgeht:** `search.js` wird in `_sources()` aufgenommen, jemand erweitert dabei auch `test_the_script_reads_the_token_inside_the_call` und `test_the_script_polls_politely` auf beide Dateien, und der Baum steht rot, weil `search.js` weder ein Token liest noch pollt.

**Warum es passiert:** Die drei Struktur-Tests lesen heute direkt `SCRIPT.read_text()` und nicht `_sources()`. Wer nur `_sources()` erweitert, ist sicher; wer "konsequent" sein will, bricht es.

**Wie vermeiden:** Die drei Sondertests bleiben woertlich an `admin.js`, mit einem Kommentar, der sagt warum: die Verwaltungsseite beobachtet einen laufenden Vorgang, ein Suchergebnis ist eine Antwort auf eine Frage.

**Warnzeichen:** Ein Diff, das `SCRIPT` durch eine Liste ersetzt.

### Pitfall 5: `<navigations>` an der falschen Stelle in `info.xml`

**Was schiefgeht:** Der Job `app-metadata` wird rot mit einer XSD-Meldung, die auf ein voellig anderes Element zeigt.

**Warum es passiert:** Der Wurzeltyp ist eine `xs:sequence`. `navigations` gehoert zwischen `fulltextsearch` und `contactsmenu`, also **hinter** `<settings>`. An jeder anderen Stelle ist es ein Reihenfolgefehler, und XSD-Meldungen zu Sequenzen benennen selten das falsch platzierte Element.

**Wie vermeiden:** Ans Dateiende, hinter `<settings>`. Vor dem Commit `scripts/dev/validate_info_xml.sh` laufen lassen (braucht `xsltproc` und `xmllint`; ob beide auf der Maschine sind, ist ungeprueft, im Zweifel im Container).

**Warnzeichen:** Eine Fehlermeldung, die `settings` oder `commands` nennt, obwohl daran nichts geaendert wurde.

### Pitfall 6: Der Einstiegs-Eintrag zaehlt als Treffer

**Was schiefgeht:** Der Dialog zeigt 20 Findling-Treffer, davon einer ist der Einstieg. Oder: der Paritaetsjob liest 21 Eintraege und findet einen ohne `attributes.fileId`, was `parity_diff.py` als `MalformedAnswer` mit Exitcode 3 meldet.

**Warum es passiert:** `_file_ids()` in `parity_diff.py` wirft **ausdruecklich**, wenn ein Eintrag kein `attributes.fileId` hat, und zwar mit der Begruendung, dass ein stilles Weglassen eine falsche Antwort auf eine Rechtefrage waere.

**Wie vermeiden:** Zwei Dinge zugleich. Erstens: der Eintrag darf nicht gegen `$limit` zaehlen (er wird nach `toEntries()` angehaengt). Zweitens: `parity_diff.py` muss ihn kennen und ueberspringen, und zwar an genau **einem** Merkmal, naemlich der `resourceUrl`, die auf `/apps/findling/` zeigt, nicht am fehlenden Attribut. Ein pauschales "Eintraege ohne fileId ignorieren" wuerde den Schutz aus dem Modul-Docstring aufheben.

**Warnzeichen:** `parity inconclusive` oder Exitcode 3 in einem Szenario, das vorher gruen war.

### Pitfall 7: Ein Attributname in Prosa bricht die Anti-Vakuitaets-Klausel

**Was schiefgeht:** `test_the_gate_sees_every_route_the_sources_declare` wird rot, obwohl keine Route geaendert wurde.

**Warum es passiert:** Die Klausel zaehlt Zeilen in `php/lib/Controller/*.php`, die `ApiRoute` oder `FrontpageRoute` enthalten, und vergleicht sie mit der Zahl gefundener Routen. Ein Klassenkommentar in `PageController.php`, der `FrontpageRoute` erwaehnt, ist eine Erwaehnung ohne Route. `SettingsController.php` sagt genau das in seinem eigenen Kommentar und hat es deshalb vermieden.

**Wie vermeiden:** Im Kommentar von `PageController.php` die Attributnamen umschreiben statt sie zu nennen, so wie es `SettingsController.php` vormacht ("die vier Attributnamen sind deliberately nicht ausgeschrieben, damit ein grep ueber diese Klasse bei null bleibt").

**Warnzeichen:** `assert len(routes) == mentions` schlaegt fehl mit `mentions` groesser als `routes`.

## Code Examples

### Die Routendeklaration der neuen Seite

```php
// Source: Form aus php/lib/Controller/SettingsController.php, Attribute aus
// nextcloud/server stable33 lib/public/AppFramework/Http/Attribute/
#[\OCP\AppFramework\Http\Attribute\NoAdminRequired]
#[\OCP\AppFramework\Http\Attribute\NoCSRFRequired]
#[\OCP\AppFramework\Http\Attribute\FrontpageRoute(verb: 'GET', url: '/')]
public function index(): TemplateResponse {
    // ...
    return new TemplateResponse(Application::APP_ID, 'search', $parameters, TemplateResponse::RENDER_AS_USER);
}
```

Vollstaendig qualifizierte Attributnamen, wie im ganzen Bestand, damit die Anti-Vakuitaets-Klausel von Gate B zaehlbar bleibt.

### Ressourcen aus dem Template heraus einbinden

```php
// Source: php/templates/admin.php Zeile 22 bis 27, woertlich uebernommene Begruendung
// Die beiden Aufrufe gehoeren hierher und nicht in den Controller. Das Template
// wird gerendert, bevor das Layout seine Ressourcenlisten einsammelt, ein Aufruf
// aus dem Controller kaeme also zu frueh oder zu spaet.
\OCP\Util::addScript('findling', 'search');
\OCP\Util::addStyle('findling', 'search');
```

Achtung auf den Unterschied: bei der Verwaltungsseite ist es die Settings-Klasse, die zu spaet waere. Bei einer `TemplateResponse` aus einem Controller waere ein Aufruf im Controller **vor** dem Rendern tatsaechlich zulaessig. Das Template-Muster wird trotzdem beibehalten, damit beide Seiten der App dieselbe Bauweise haben.

### Der Einstiegs-Eintrag im Provider

```php
// Source: abgeleitet aus php/lib/Search/Provider.php::toEntries und ::resourceUrl
if (!$exhausted && $entries !== []) {
    $entries[] = new SearchResultEntry(
        thumbnailUrl: '',
        title: $this->l10n->t('Show all results'),
        subline: $this->l10n->t('Opens the Findling results page'),
        resourceUrl: $this->urlGenerator->linkToRoute(
            'findling.page.index',
            ['query' => $term] + ($titleOnly ? ['names' => '1'] : []),
        ),
        icon: 'icon-search',
    );
    // Deliberately no addAttribute('fileId'): this entry is not a hit and must
    // never be counted as one.
}
```

### Cursorpfad pruefen, still zurueckfallen

```php
// Source: URL-Vertrag der 09-UI-SPEC, Pruefform nach dem Muster von
// php/lib/Search/Provider.php::startOffset
/** @return list<int> genau $page Eintraege, oder [0] wenn irgendetwas nicht stimmt */
private function cursorPath(string $raw, int $page): array {
    $parts = $raw === '' ? [] : explode('.', $raw);
    if (count($parts) !== $page || $page > self::MAX_PAGE) {
        return [0];
    }
    $path = [];
    $previous = -1;
    foreach ($parts as $part) {
        if (!ctype_digit($part)) {
            return [0];
        }
        $value = (int)$part;
        if ($value <= $previous) {   // streng aufsteigend, erster Wert muss 0 sein
            return [0];
        }
        if ($path === [] && $value !== 0) {
            return [0];
        }
        $previous = $value;
        $path[] = $value;
    }
    return $path;
}
```

Jede Abweichung fuehrt auf `[0]`, also Seite 1, ohne Fehlermeldung. Die Seite macht ueber die eigene Adresszeile keine Aussage.

## Runtime State Inventory

Diese Phase ist keine Umbenennung und keine Migration, aber sie beruehrt drei Stellen ausserhalb des Quelltexts, und die gehoeren benannt.

| Kategorie | Gefunden | Erforderliche Aktion |
|-----------|----------|----------------------|
| Gespeicherte Daten | Keine. Die Seite schreibt nichts. Kein `appConfig`-Schluessel, keine Migration, keine Tabelle. `sessionStorage['findling:lasthit']` liegt im Browser und ist pro Sitzung fluechtig | keine |
| Live-Service-Konfiguration | Der Navigationseintrag wird von Nextcloud beim App-Laden aus der **installierten** `appinfo/info.xml` gelesen (`AppManager::loadApp` -> `NavigationManager::init`). Eine bereits installierte Instanz zeigt ihn erst nach einem App-Update, nicht nach einem blossen Dateitausch | Bei der lokalen Abnahme `occ app:update findling` oder Neuinstallation, sonst fehlt der Eintrag und man sucht am falschen Ende |
| OS-registrierter Zustand | Keiner. Kein Background-Job, kein Cron, kein Task | keine |
| Secrets und Umgebungsvariablen | Keine neuen. Die Seite nutzt den bestehenden AppAPI-Proxy mit dem bestehenden Schluessel | keine |
| Build-Artefakte / installierte Pakete | Die lokale Testinstanz `findling-nextcloud` traegt `findling: 0.3.0`, das Repo steht bei `1.0.3`. Ausserdem meldet `status.php` `needsDbUpgrade: true` | Vor jeder Messung und jeder Sichtprobe: `occ upgrade`, App auf den Repo-Stand bringen. Sonst misst und sieht man einen fremden Stand |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker | Lokale Test-Nextcloud, Sichtproben, Messung | ja | 29.5.2 (desktop-linux) | keiner noetig |
| Laufende Test-Nextcloud | Sichtproben 1 bis 20, Zeitmessung | ja | `findling-nextcloud`, `nextcloud:34.0.3-apache`, Port 8090, HTTP 200 | keiner noetig |
| PHP auf der Maschine | `php -l`, lokaler PHPUnit-Lauf | **nein** | - | `php -l` im Container; PHPUnit ausschliesslich in CI (`php.yml`, Job `phpunit`), so ist es dokumentiert und so bleibt es |
| Python 3.13 | Gates B und C, `parity_diff.py`, Backend-Tests | ja | 3.13.1 | keiner noetig |
| uv | Backend-Testumgebung | ja | 0.11.7 | keiner noetig |
| node / npm | **wird nicht gebraucht** | ja (22.21.0 / 11.14.1) | - | ausdruecklich nicht verwenden, die Companion-App hat keinen Build-Step |
| `xsltproc` / `xmllint` | `scripts/dev/validate_info_xml.sh` lokal | ungeprueft | - | Der Job `app-metadata` in `php.yml` installiert beide und validiert ohnehin. Lokal notfalls ueberspringen |
| Zweiter Browser (Firefox) | Sichtproben 4 und 5, Rueckkehrvertrag | ungeprueft | - | Ohne zweiten Browser bleibt Befund 2 unbelegt. Das ist die eine Sichtprobe, die wirklich zwei Engines braucht |

**Fehlende Abhaengigkeiten ohne Ausweg:** keine.
**Fehlende Abhaengigkeiten mit Ausweg:** PHP lokal (CI-only, so eingerichtet und dokumentiert); `xsltproc`/`xmllint` (CI deckt es ab); Firefox (falls nicht vorhanden, muss der Rueckkehrvertrag in Chrome geprueft und der Firefox-Fall als offener Punkt in die Verifikation geschrieben werden statt stillschweigend als bestanden zu gelten).

## Security Domain

`security_enforcement` ist in `.planning/config.json` nicht auf `false` gesetzt, also gilt es.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | nein | Die Route hat keine eigene Authentifizierung. `SecurityMiddleware` verlangt ohne `PublicPage` eine angemeldete Sitzung, und `PublicPage` ist in der neuen Gate-B-Klasse verboten |
| V3 Session Management | ja (indirekt) | `NoCSRFRequired` auf einer **lesenden** Route ist zulaessig, weil es nichts zu faelschen gibt: die Route veraendert keinen Zustand. Der Nachweis liegt in Gate B, das `PublicPage` weiterhin verbietet, also bleibt die Sitzung Pflicht |
| V4 Access Control | **ja, die Kernkategorie** | `SearchService::run()`: `getFirstNodeById()` gegen den **eigenen** `userFolder` plus `isReadable()`. Ein Zaehl-Gate haelt die Einmaligkeit. Der Paritaetsjob prueft beide Richtungen: `missing` funktional, `extra` sicherheitsrelevant |
| V5 Input Validation | ja | `query` auf 255 Zeichen via `PlainText::bounded`, `maxlength="255"` am Feld; `names` nur `1`; `page` ganzzahlig 1 bis 20; `cursors` streng geprueft, sonst still auf Seite 1. Jede Ausgabe durch `p()` bzw. `htmlspecialchars(..., ENT_QUOTES, 'UTF-8')` |
| V6 Cryptography | nein | Kein Schluesselmaterial, keine Signatur, kein Hash in dieser Phase |
| V7 Error Handling / Logging | ja | Kein Pfad, kein Dateiname, keine Bibliotheksmeldung im Log. Muster: statischer Satz nach aussen, Exception im `exception`-Feld. So halten es alle bestehenden Controller |
| V14 Configuration | ja | `Content-Security-Policy` bleibt die Nextcloud-Standardrichtlinie. Kein Inline-Skript (Gate C prueft `<script`), also keine Lockerung noetig |

### Known Threat Patterns for dieses Stacks

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Reflected XSS ueber `query` in `h1` und Formularwert | Tampering | Ausgabe ausschliesslich ueber `p()`. Gate C verbietet `print_unescaped`. Abnahme-Sichtprobe 14 mit `<script>` im Suchbegriff |
| Stored/Reflected XSS ueber ein Container-Snippet | Tampering | Der Highlight-Renderer escaped **jedes** Teilstueck einzeln und setzt nur `<mark>` selbst. Nie HTML aus der Antwort |
| Information Disclosure ueber die Trefferliste (fremde Dateinamen) | Information Disclosure | Titel, Pfad und Mimetype ausschliesslich aus dem bestaetigten Node, nie aus `$candidate`. Der Container schickt sie strukturell gar nicht |
| Information Disclosure ueber Trefferzahlen ("3 Treffer entfernt") | Information Disclosure | Kein Satz und keine Zahl ueber verworfene Kandidaten. Keine Gesamttrefferzahl. Verbotsliste der 09-UI-SPEC |
| Existenz fremder Dateien ueber unterschiedliche Antwortzeiten sondieren | Information Disclosure | Nicht neu und nicht durch diese Phase verschaerft: der Recheck-Pfad ist derselbe wie im Dialog. Wird nicht zusaetzlich gehaertet, gehoert aber ins Security-Audit am Phasenende |
| DoS ueber tiefe Paginierung | Denial of Service | `MAX_PAGE` 20 in PHP plus `SEARCH_OFFSET_MAX` 1200 im Container plus `SEARCH_SCAN_MAX` 10000 pro Aufruf. Die drei Deckel sind vorhanden; Pitfall 1 ist ihre unschoene Beruehrung, nicht ihre Abwesenheit |
| DoS ueber sehr lange `query` | Denial of Service | 255 Zeichen in PHP, 512 im Container, `SEARCH_QUERY_MAX_DEPTH` 32 gegen Klammer-Rekursion |
| CSRF gegen die Seitenroute | Spoofing | Nicht anwendbar: reine GET-Route ohne Zustandsaenderung. Der Nachweis, dass sie das bleibt, ist die neue Gate-B-Klasse plus die Tatsache, dass `PageController` genau eine Methode hat |
| Fremder ExApp-Container erreicht die Seitenroute | Elevation of Privilege | `ExAppRequired` bleibt in der neuen Klasse verboten. Ohne das Attribut erreicht kein registrierter Container die Route |

## State of the Art

| Alter Ansatz | Aktueller Ansatz | Wann geaendert | Bedeutung |
|--------------|------------------|----------------|-----------|
| `appinfo/routes.php` mit einem Routen-Array | `#[FrontpageRoute]` / `#[ApiRoute]` am Methodenattribut | NC 29 | Der Bestand nutzt es bereits ausschliesslich. `routes.php` bleibt leer, muss aber existieren |
| `IInAppSearch` fuer "in dieser App weitersuchen" | Ein zusaetzlicher Ergebniseintrag mit `resourceUrl` | Der Knopf hat in stable33 bis master keinen Handler und kein `href` [CITED: 09-UI-SPEC, verifiziert am 08.09.2026] | Ein toter Knopf ist schlechter als kein Knopf. `IInAppSearch` kommt in keiner Datei der App vor, heute nicht und danach nicht |
| Scrollposition per `history.scrollRestoration` | Anker plus `scrollIntoView` innerhalb von `#app-content` | Nicht "geaendert", sondern eine Fehlannahme, die diese Recherche korrigiert | Siehe Pitfall 2 |
| Chrome schliesst `Cache-Control: no-store` vom bfcache aus | Chrome laesst CCNS-Seiten seit den Rollouts ab Version 116 in den bfcache und wirft sie bei Cookie-Aenderungen heraus; Firefox schliesst sie weiter aus | 2024 bis 2025 [CITED: developer.chrome.com/docs/web-platform/bfcache-ccns] | Das Verhalten ist browserabhaengig geworden, was es fuer eine Zusage schlechter macht, nicht besser |

**Veraltet / nicht verwenden:**

- `OCP.InitialState.loadState`, `OC.getCanonicalLocale`, `OC.getLanguage`, `OC.dialogs.confirmDestructive`, `icon-info` in NC 32 entfernt. Gate C prueft alle fuenf, und die neuen Dateien fallen ab sofort unter dieselbe Pruefung.
- `exAppRequestWithUserInit()`, deprecated seit AppAPI 3.0.0. Wird von `ExAppService` bereits nicht verwendet.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Ein Container-Offset von 1500 ist bei 20 Anzeigeseiten realistisch erreichbar | Cursor-Semantik und die Offset-Decke | Die Rechnung stuetzt sich auf eine angenommene Genehmigungsquote von einem Drittel. Bei hoher Quote wird die Decke nie erreicht und die Clamp-Logik ist toter Code. Der Deckel muss trotzdem da sein, weil eine niedrige Quote genau der Fall ist, fuer den der Recheck existiert. **Kann mit dem Team-Folder-Szenario der lokalen Instanz gemessen werden** |
| A2 | Firefox stellt die Scrollposition eines verschachtelten Scroll-Containers nach einer Navigation ohne bfcache nicht wieder her | Positions-Wiederherstellung | Wenn Firefox es doch tut, ist Stufe 2 gerettet und Stufe 3 wieder eine Zugabe. Aendert nichts an der Implementierung, nur an der Formulierung von Sichtprobe 5. **Empirisch pruefbar, siehe Environment Availability** |
| A3 | Ein Kandidatenaufruf mit `limit=100` bleibt unter dem 1.5-s-Deckel von `call()` | Zeitbudget | Falls nicht, ist ein groesseres Seitenbudget wirkungslos und der Per-Call-Deckel muss ebenfalls parametriert werden. **Genau das misst die vorgeschlagene Messreihe** |
| A4 | Die vorhandenen Paritaets-Szenarien haben je weniger als 25 Treffer, sodass Seite 1 der neuen Route ausreicht | Paritaetstest | Ein Szenario mit mehr Treffern wuerde still falsch vergleichen und `missing` melden, wo nur paginiert wurde. **Aus den Marker-Zaehlungen im Job ablesbar, vor der Implementierung pruefen** |
| A5 | `php/img/app.svg` als inhaltsgleiche Kopie von `app-dark.svg` wird vom App-Menue korrekt gethemt | Navigationseintrag | Falls das Symbol im dunklen Kopfbereich unsichtbar ist, braucht es eine invertierte Fassung. **Eine Sichtprobe auf der lokalen Instanz beantwortet es in einer Minute** |
| A6 | Eine dritte Routenklasse in Gate B verwaessert die Admin-Klasse nicht | Gate B | Die vorgeschlagene Erkennung ueber die Attributkombination ist eine Konstruktion dieser Recherche, kein Bestand. Sie muss im Plan mit ihren Selbsttests stehen, sonst ist die Behauptung ungeprueft |
| A7 | Der Paritaetsjob kann sich per Cookie-Login anmelden und die Seitenroute als HTML abrufen | Paritaetstest | Falls die Login-Automatisierung im Job an einem Detail scheitert (Zwei-Faktor-Vorgabe, Rate-Limit), braucht Erfolgskriterium 4 einen anderen Weg. **Vor der Implementierung mit einem Wegwerf-Skript gegen die lokale Instanz probieren** |

## Open Questions (RESOLVED)

Alle fuenf Fragen sind durch die Plaene der Phase beantwortet (Stand 08.09.2026):
Q1 Offset-Decke -> 09-03 (PHP-Clamp MAX_CONTAINER_OFFSET + Lockstep-Gate, Container unangetastet);
Q2 Per-Call-Deckel/Zeitbudget -> 09-01 (ceilingSeconds-Parameter, Budget aus fuenf Messreihen);
Q3 fr.json -> 09-08 (vertagt, 24 Wortlaute nach docs/l10n-french.md, ROADMAP-Zeiger bei Phase 11);
Q4 Sichtprobe 5 / Rueckkehrvertrag -> 09-05/09-08 (JS-Fallback tragend, UI-SPEC-Umformulierung);
Q5 Paritaets-Einstieg -> 09-07 (--findling-html-Modus, Cookie-Login).
(Die urspruenglichen Fragen stehen darunter im Wortlaut.)


1. **Wie wird die Offset-Decke behandelt: PHP-Clamp oder hoehere `SEARCH_OFFSET_MAX`?**
   - Was wir wissen: Der Container lehnt Offsets ueber 1200 mit 422 ab, PHP macht daraus einen Fehlerblock mit falschem Wortlaut. Die Konstante hat eine eigene Sicherheitsbegruendung (security audit C1).
   - Was unklar ist: Ob der Owner eine gespiegelte Zahl in PHP akzeptiert, auch mit Drift-Gate, oder lieber die Container-Konstante anhebt.
   - Empfehlung: PHP-Clamp plus Lockstep-Gate. Haelt die Phase aus dem Container heraus und beantwortet die Frage endgueltig statt bis zur naechsten Quote.

2. **Wird der Per-Call-Deckel `REQUEST_TIMEOUT_SECONDS` parametriert?**
   - Was wir wissen: Er ist privat, fest bei 1.5, und deckelt jeden Suchaufruf unabhaengig vom Aufrufer-Budget. `ADMIN_REQUEST_TIMEOUT_SECONDS` zeigt, wie ein zweiter Wert im Bestand aussieht.
   - Was unklar ist: Ob 1.5 Sekunden fuer einen Aufruf mit `limit=100` ausreichen.
   - Empfehlung: Erst messen, dann entscheiden. Falls noetig, ein `PAGE_REQUEST_TIMEOUT_SECONDS` mit eigenem Aufrufpfad, nicht ein optionales Argument an `call()`.

3. **`fr.json` in dieser Phase oder als eigener Schritt vor der Store-Abgabe?**
   - Was wir wissen: Die App liefert heute nur `de.js` und `de.json`. Die franzoesischen Wortlaute stehen vollstaendig in der Copy-Tabelle. Ein franzoesischer Katalog braucht **beide** Dateien, und der Gate `test_the_two_translation_files_carry_the_same_keys` muesste auf zwei Sprachpaare erweitert werden. Die `info.xml` und `docs/store-listing.md` fuehren Franzoesisch bereits als dritte Sprache (D-12), und die OCR-Sprachen umfassen Franzoesisch.
   - Was unklar ist: Ob ein franzoesischer Katalog fuer 24 Zeichenketten sinnvoll ist, solange die anderen 149 Zeichenketten der App nur Englisch und Deutsch koennen.
   - Empfehlung: **Vertagen.** Ein Katalog, der 24 von 173 Zeichenketten uebersetzt, ist eine halb franzoesische Oberflaeche und damit schlechter als eine ganz englische. Die Wortlaute stehen in der 09-UI-SPEC und gehen nicht verloren. Der franzoesische Katalog gehoert in einen eigenen Schritt, der **alle** Zeichenketten der App abdeckt, vor der Store-Abgabe. Das ist eine Owner-Entscheidung, und diese Empfehlung ist ihre Vorlage.

4. **Bleibt Abnahme-Sichtprobe 5 in ihrer heutigen Formulierung?**
   - Was wir wissen: Sie verlangt bei abgeschaltetem JavaScript "dieselbe Scrollposition, vom Browser". Nach Befund 1 und 2 ist das browserabhaengig.
   - Was unklar ist: Nichts Technisches. Es ist eine Frage, ob die 09-UI-SPEC an dieser einen Zeile nachgezogen wird.
   - Empfehlung: Umformulieren auf "dieselbe Seite 3, dieselbe Suche, keine Markierung, keine Fehlermeldung, Scrollposition nach Browserverhalten". Der Rest der Sichtprobe bleibt woertlich und bleibt wertvoll.

5. **Wie erkennt `parity_diff.py` den Einstiegs-Eintrag im Dialog-Ergebnis?**
   - Was wir wissen: Er hat kein `attributes.fileId`, und der heutige Extraktor wirft bei genau diesem Fall ausdruecklich.
   - Was unklar ist: Ob im Paritaetsjob ueberhaupt ein Szenario mehr Treffer hat, als der Dialog zeigt (dann erscheint der Eintrag gar nicht). Bei `limit=100` und Szenarien mit wenigen Dateien ist `$exhausted` immer wahr, der Eintrag erscheint nie, und `parity_diff.py` sieht ihn nicht.
   - Empfehlung: Trotzdem behandeln, an der `resourceUrl` und nicht am fehlenden Attribut, plus ein Testfall in `test_parity_diff.py`. Ein Job, der nur zufaellig gruen ist, weil ein Szenario zu klein ist, ist ein Job, der beim naechsten groesseren Szenario ohne Vorwarnung rot wird.

## Sources

### Primary (HIGH confidence)

Eigene Quellen, alle am 08.09.2026 vollstaendig gelesen:
- `php/lib/Search/Provider.php` (590 Zeilen), `php/lib/Service/ExAppService.php` (846 Zeilen, Konstanten und Suchpfad), `php/lib/Text/PlainText.php`, `php/lib/Controller/SettingsController.php`, `php/lib/Settings/Section.php`, `php/lib/AppInfo/Application.php`
- `php/appinfo/info.xml`, `php/appinfo/routes.php`, `php/phpunit.xml`, `php/templates/admin.php` (Kopf), `php/l10n/de.json`, `php/l10n/de.js`, `php/img/app-dark.svg`, `php/tests/Unit/ProviderTest.php` (Kopf)
- `backend/src/findling/api/search.py`, `backend/src/findling/api/snippets.py` (Modelle), `backend/src/findling/config.py` (Suchkonstanten), `backend/src/findling/embed/engine.py`, `backend/src/findling/embed/model.py` (`LOAD_RETRY_SECONDS`)
- `backend/tests/test_php_trust_boundary.py` (vollstaendig), `backend/tests/test_admin_ui_contract.py` (Scanner und Struktur-Tests), `backend/tests/test_semantic_boundary.py` (Kopf), `backend/tests/test_search_endpoint.py` (Offset-Faelle)
- `scripts/ci/parity_diff.py`, `.github/workflows/integration.yml` (Job `search-parity`), `.github/workflows/php.yml`, `docs/dev-setup.md`, `THIRD-PARTY.md`
- `.planning/phases/09-eigene-ergebnisseite/09-UI-SPEC.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `./CLAUDE.md`, `.planning/config.json`

Nextcloud-Server, `raw.githubusercontent.com`, am 08.09.2026 gezogen:
- `core/css/apps.scss` in `stable33`, `stable34`, `stable35`: `#app-content` Zeile 742 (`overflow: auto`), `#content` Zeile 702 (`position: fixed`, `overflow: clip`)
- `core/css/global.scss` `stable34`: `.hidden-visually` Zeile 66, `.hidden` Zeile 62
- `lib/public/AppFramework/Http/Response.php` `stable34`: Zeile 104 und 237, `Cache-Control: no-cache, no-store, must-revalidate`
- `lib/public/AppFramework/Http/Attribute/FrontpageRoute.php` `stable33`: `@since 29.0.0`
- `lib/public/Files/IMimeTypeDetector.php` `stable33`: `mimeTypeIcon()` `@since 8.2.0`
- `lib/private/NavigationManager.php` `stable34`: Zeile 315 bis 375, Navigationsregistrierung und `$l->t($nav['name'])`
- `lib/private/App/AppManager.php` `stable34`: `getAppIcon()` Zeile 117 bis 129

Nextcloud-App-Store, gepinnter Commit `eda850ba61407c6e4da3e23316614c6126406652` (derselbe, gegen den `php.yml` validiert):
- `info.xsd`: Position von `navigations` in der Wurzel-Sequenz, Typ `navigation`, Routenmuster
- `pre-info.xslt`: Zeile 64, 96 bis 100, 115 bis 131, `navigations` ueberlebt die Transformation

Lokale Umgebung, per `docker ps`, `docker inspect` und `curl` am 08.09.2026 geprueft:
- Container `findling-nextcloud`, `nextcloud:34.0.3-apache`, Port 8090, `status.php` HTTP 200, `version 34.0.3.2`, `needsDbUpgrade: true`, App `findling: 0.3.0`, Compose in `scripts/dev`
- Werkzeuge: `php` fehlt, `python3` 3.13.1, `uv` 0.11.7, `docker` 29.5.2, `node` 22.21.0, `npm` 11.14.1

### Secondary (MEDIUM confidence)

- Chrome for Developers, "Enabling bfcache for Cache-Control: no-store": Chrome laesst CCNS-Seiten seit den Experimenten ab Version 116 in den bfcache und wirft sie bei Cookie- oder Autorisierungsaenderungen heraus
- web.dev, "Back/forward cache": Firefox nennt `cache-control: no-store` als Grund, eine Seite nicht zu cachen; bfcache in Firefox, Chrome und Safari vorhanden

### Tertiary (LOW confidence)

- Die Annahme, dass Firefox die Scrollposition eines verschachtelten Scroll-Containers ohne bfcache nicht wiederherstellt, stuetzt sich auf die Abwesenheit einer Spezifikation und nicht auf eine gepruefte Quelle. Als A2 im Assumptions Log gefuehrt und empirisch pruefbar.

## Metadata

**Confidence breakdown:**
- Bestand der eigenen Quellen (Provider, ExAppService, Gates, CI): HIGH, alle Dateien vollstaendig gelesen, Zeilennummern belegt
- Nextcloud-APIs und -CSS: HIGH, gegen drei Zweige einzeln geprueft, nicht aus dem Gedaechtnis
- Store-Schema und Transformation: HIGH, gegen den Commit gezogen, den die CI selbst validiert
- Backend-Grenzen (Offsets, Limits, Engine-Lebenszyklus): HIGH, Quellen und die dazugehoerigen Tests gelesen
- Zeitbudget der Seitenroute: LOW, ausdruecklich ungemessen. Die Recherche liefert das Verfahren, nicht die Zahl
- Positions-Wiederherstellung im Browser: MEDIUM. Die beiden Ursachen sind verifiziert, das konkrete Verhalten pro Browser ist es nicht
- Vorgeschlagene dritte Routenklasse in Gate B: MEDIUM, eine Konstruktion dieser Recherche, mit Selbsttests belegbar, aber heute nicht belegt

**Research date:** 2026-09-08
**Valid until:** 2026-10-08 fuer die eigenen Quellen und die Nextcloud-Zweige. 2026-09-15 fuer die bfcache-Aussagen, weil Chrome an diesem Verhalten aktiv arbeitet.
