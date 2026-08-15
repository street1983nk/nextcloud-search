---
phase: 01-integrationsbeweis
plan: 05
subsystem: api
tags: [php, nextcloud, appapi, unified-search, iprovider, ocs, github-actions]

requires:
  - phase: 01-integrationsbeweis
    provides: "Eingefrorene Store-Identitaet findling / findling_backend (Plan 01-01, docs/store-identity.md)"
  - phase: 01-integrationsbeweis
    provides: "integration.yml mit roter Kanarienprobe auf die Providerliste (Plan 01-02)"
provides:
  - "PHP-Companion-App findling: info.xml, routes.php, composer.json"
  - "Registrierung des Suchanbieters ueber registerSearchProvider in register()"
  - "IProvider-Implementierung mit int-Order und Klartext-Subline"
  - "ExAppService als einzige Stelle mit exAppRequest, Timeout 2 s, vier stille Fehlerpfade"
  - "Content-Gateway GET /ocs/v2.php/apps/findling/files/{fileId}?userId=, nur lesend, nur fuer ExApps"
  - "php.yml: php -l ueber alle PHP-Dateien, Actions per Commit-SHA gepinnt"
affects: [01-06, 01-07, 01-08, 02-indexierung]

tech-stack:
  added: [shivammathur/setup-php]
  patterns:
    - "Ein einziger Proxy-Kapselungspunkt: nur ExAppService ruft exAppRequest"
    - "Ein einziger Dateilesepunkt: nur GatewayController ruft fopen, und nur mit 'r'"
    - "Grep-pruefbare Sicherheitsinvarianten statt Review-Vertrauen"
    - "Pfadgefilterte CI-Workflows je Sprachbereich (python.yml, php.yml)"

key-files:
  created:
    - php/appinfo/info.xml
    - php/appinfo/routes.php
    - php/composer.json
    - php/lib/AppInfo/Application.php
    - php/lib/Search/Provider.php
    - php/lib/Service/ExAppService.php
    - php/lib/Controller/GatewayController.php
    - .github/workflows/php.yml
  modified: []

key-decisions:
  - "IRootFolder und LoggerInterface werden per Konstruktor injiziert, nicht als Controller-Methodenparameter: Methodenparameter einer Controller-Action bindet der Dispatcher aus Request-Parametern, ein Service-Typehint dort waere ein TypeError zur Laufzeit"
  - "NoCSRFRequired zusaetzlich zu ExAppRequired: die Berechtigung an diesem Endpunkt ist der signierte AppAPI-Header, nicht die Session"
  - "ExAppRequired wird voll qualifiziert geschrieben, damit die Datei genau ein Vorkommen traegt und das Grep-Gate aussagekraeftig bleibt"
  - "Treffer aus dem Backend werden vor dem Provider auf Schluessel und Typen gefiltert (vierter Fehlerfall)"
  - "fileId 0 verlinkt die Dateiliste statt einer Datei-Route, damit der Kanarien-Treffer nicht ins Leere zeigt"

patterns-established:
  - "Fehlerpfad-Reihenfolge im Proxy: is_array zuerst, dann Status, dann JSON, dann Struktur"
  - "Logs tragen Transportzustaende, nie Suchbegriffe, Titel, Snippets oder Dateiinhalte"
  - "404 sowohl fuer nicht vorhanden als auch fuer nicht sichtbar, keine Existenzpreisgabe"

requirements-completed: [COMP-01, COMP-02]

duration: 25 min
completed: 2026-08-15
---

# Phase 1 Plan 05: PHP-Companion-App Summary

**PHP-App findling mit IProvider-Registrierung, gekapseltem exAppRequest-Proxy (Timeout 2 s, vier stille Fehlerpfade) und einem nur lesenden, ExApp-gebundenen Content-Gateway, dazu ein php -l-Gate in der CI.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-08-15T12:41:00Z
- **Completed:** 2026-08-15T11:06:00Z (13:06 lokal)
- **Tasks:** 3
- **Files created:** 8

## Accomplishments

- Die Unified Search kann den Anbieter `findling` ueberhaupt erst annehmen: `registerSearchProvider` steht in `register()`, `getOrder()` liefert immer einen int. Damit sind die beiden stummen Ursachen aus Pitfall 3, die in PHP liegen, ausgeschlossen; die dritte (Verzeichnisname ungleich App-ID) erledigt der Move-Schritt in `integration.yml`.
- Der Proxy in den Container lebt in genau einer Klasse. Timeout 2 Sekunden, bewusst unter dem AppAPI-Default von 3. Alle vier Fehlerfaelle (Array mit `error`, Status >= 400, nicht parsbarer Body, falsche Struktur) enden in einem leeren Ergebnis, keiner wirft.
- Der rechtegepruefte Lesekanal steht: `getUserFolder($userId)->getFirstNodeById($fileId)->fopen('r')` als `StreamResponse`, erreichbar nur fuer ExApps. Es gibt kein zweites Berechtigungsmodell und keinen Pfadstring an der Schnittstelle.
- `php.yml` lintet jede PHP-Datei gegen PHP 8.2, die untere Grenze aus der `info.xml`. Beide Actions sind per Commit-SHA gepinnt.

## Task Commits

1. **Task 1: App-Metadaten und Registrierung des Suchanbieters** - `a120a0a` (feat)
2. **Task 2: Geschuetzter Proxy in den Container mit hartem Timeout** - `b15dc7d` (feat)
3. **Task 3: Content-Gateway und PHP-Gate in der CI** - `cabe01a` (feat)

## Files Created/Modified

- `php/appinfo/info.xml` - Store-Metadaten: id `findling`, namespace `Findling`, Version 0.1.0, agpl, Kategorie files, NC 32 bis 35, PHP ab 8.2. Die Beschreibung nennt die Privacy-Zusage (keine Dateiaenderung, kein Inhalt verlaesst den Server) und die Voraussetzung AppAPI plus External App "Findling Backend". Kein Versuch, `app_api` als Abhaengigkeit zu deklarieren, das XSD kennt kein solches Element.
- `php/appinfo/routes.php` - Leere `routes`- und `ocs`-Arrays; die Gateway-Route kommt ueber das ApiRoute-Attribut.
- `php/composer.json` - psr-4 `OCA\Findling\` auf `lib/`, keine Runtime-Abhaengigkeiten.
- `php/lib/AppInfo/Application.php` - Konstanten `APP_ID` und `BACKEND_APP_ID`, `register()` enthaelt genau die eine Registrierungszeile, `boot()` ist leer.
- `php/lib/Search/Provider.php` - `IProvider` (nicht `IExternalProvider`), Order -5 auf `files.`-Routen sonst 25, Subline als Klartext, Datei-Route je Treffer.
- `php/lib/Service/ExAppService.php` - Der einzige `exAppRequest`-Aufruf im Projekt, zwei Laufzeit-Guards, drei Auswertungsfaelle plus defensive Trefferfilterung.
- `php/lib/Controller/GatewayController.php` - OCS-Endpunkt `GET /files/{fileId}`, `ExAppRequired`, nur `fopen('r')`, 404 bei nicht vorhanden und bei nicht sichtbar, 422 bei nicht oeffenbar, 500 mit Log ohne Dateiinhalt.
- `.github/workflows/php.yml` - Pfadgefiltert auf `php/**`, setup-php 8.2, `find ... | xargs -0 -n1 php -l`.

## Decisions Made

- **Konstruktorinjektion statt Methodenparameter im Controller.** Code-Beispiel 5 im RESEARCH fuehrt `IRootFolder` in der Methodensignatur. Der Nextcloud-Dispatcher fuellt Action-Parameter aus Request-Parametern, ein Service-Typehint dort wuerde zur Laufzeit als TypeError enden. Der Rumpf ist wortgleich uebernommen, die Abhaengigkeiten wandern in den Konstruktor.
- **`NoCSRFRequired` zusaetzlich zu `ExAppRequired`.** Die Berechtigung an diesem Endpunkt ist der signierte AppAPI-Header, nicht die Session; ein Session-CSRF-Token existiert im ExApp-Aufruf gar nicht. Ohne das Attribut kaeme der Gateway in Phase 2 potenziell nur bis zu einer 412.
- **`ExAppRequired` voll qualifiziert geschrieben.** Mit Import stuende der Bezeichner dreimal in der Datei (Import, Attribut, Kommentar) und das Grep-Gate aus dem Plan (genau ein Vorkommen) waere nicht mehr aussagekraeftig. Voll qualifiziert bleibt genau das Attribut uebrig.
- **Trefferfilterung vor dem Provider.** Ein Backend, das gueltiges JSON mit falschen Typen liefert, wuerde sonst einen TypeError in die Suche tragen. Eintraege ohne die drei erwarteten Schluessel mit den erwarteten Typen werden verworfen und nur als Anzahl geloggt.
- **`fileId <= 0` verlinkt `files.view.index`.** Der Kanarien-Treffer der Phase 1 hat keine echte Datei hinter sich; eine `showFile`-Route mit fileid 0 zeigte ins Leere.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] IRootFolder und LoggerInterface in den Konstruktor verschoben**
- **Found during:** Task 3 (Content-Gateway)
- **Issue:** Code-Beispiel 5 des RESEARCH deklariert `getFileContents(IRootFolder $rootFolder, int $fileId, string $userId)`. Nextcloud bindet Parameter einer Controller-Action aus den Request-Parametern; fuer `$rootFolder` gaebe es keinen Request-Wert, der Aufruf endete in einem TypeError, sobald der Gateway das erste Mal gerufen wird.
- **Fix:** `IRootFolder` und `LoggerInterface` werden per Konstruktor injiziert, `parent::__construct(Application::APP_ID, $request)`. Der Methodenrumpf bleibt wortgleich, `$rootFolder->` wurde zu `$this->rootFolder->`.
- **Files modified:** php/lib/Controller/GatewayController.php
- **Verification:** Grep-Gates des Plans weiterhin gruen (`ExAppRequired` 1, `fopen('r')` 1, `getFirstNodeById` 1, verbotene fopen-Modi 0); Laufzeitnachweis erst in Phase 2, wenn der Container den Gateway wirklich ruft.
- **Committed in:** cabe01a

**2. [Rule 2 - Missing Critical] Null-Pruefung auf den Nutzer vor dem app_api-Guard**
- **Found during:** Task 2 (Proxy)
- **Issue:** `IUserManager::get()` liefert `null` fuer einen unbekannten Nutzer. `isEnabledForUser('app_api', null)` faellt auf den Sessionnutzer zurueck und beantwortet damit eine andere Frage als die gestellte.
- **Fix:** Frueher Ausstieg mit leerem Ergebnis und Log auf `info`.
- **Files modified:** php/lib/Service/ExAppService.php
- **Verification:** Der Guard steht vor jedem weiteren Zugriff; `grep -c 'exAppRequest'` bleibt 1.
- **Committed in:** b15dc7d

**3. [Rule 2 - Missing Critical] Defensive Trefferfilterung (vierter Fehlerfall)**
- **Found during:** Task 2 (Proxy)
- **Issue:** Der Plan verlangt die Filterung ausdruecklich als Ergaenzung zu Code-Beispiel 3; ohne sie traegt ein fehlerhaftes Backend Typfehler bis in `SearchResultEntry`.
- **Fix:** `filterHits()` laesst nur Eintraege mit `fileId:int`, `title:string`, `snippet:string` durch und loggt die Anzahl der verworfenen Eintraege, nicht deren Inhalt.
- **Files modified:** php/lib/Service/ExAppService.php
- **Verification:** Rueckgabetyp entspricht dem phpdoc `list<array{fileId:int,title:string,snippet:string}>`.
- **Committed in:** b15dc7d

**4. [Rule 2 - Missing Critical] NoCSRFRequired am Gateway**
- **Found during:** Task 3 (Content-Gateway)
- **Issue:** Der Plan nennt nur `ExAppRequired` und `ApiRoute`. Der ExApp-Aufruf traegt keinen Session-CSRF-Token; ohne das Attribut ist eine Abweisung durch die SecurityMiddleware moeglich, bevor der Endpunkt ueberhaupt laeuft.
- **Fix:** `#[NoCSRFRequired]` ergaenzt, mit Begruendung im Doc-Kommentar. Die Zugangskontrolle bleibt vollstaendig bei `ExAppRequired` plus der Rechteaufloesung ueber den Nutzerordner; es wird nichts geoeffnet, was vorher zu war.
- **Files modified:** php/lib/Controller/GatewayController.php
- **Verification:** Grep-Gates unveraendert gruen.
- **Committed in:** cabe01a

---

**Total deviations:** 4 auto-fixed (1 Bug, 3 fehlende kritische Funktionalitaet)
**Impact on plan:** Alle vier sind Korrektheits- oder Sicherheitsanforderungen im Rahmen der geplanten Dateien. Kein Scope-Zuwachs, keine neue Datei, keine neue Abhaengigkeit.

## Issues Encountered

- **`grep -c 'ExAppRequired'` lieferte zunaechst 3 statt der geforderten 1.** Ursache: Import, Attribut und ein Kommentar. Geloest, indem das Attribut voll qualifiziert geschrieben und der Kommentar umformuliert wurde. Der Import entfaellt damit, das Gate misst wieder genau das Attribut.
- **Keine lokale PHP-Toolchain.** `php`, `composer` und `xmllint` sind auf dem Entwicklungsrechner nicht vorhanden (im RESEARCH unter "Environment Availability" dokumentiert). Ersatzweise lokal geprueft: `info.xml` als wohlgeformtes XML (ElementTree), `composer.json` als gueltiges JSON, `php.yml` als gueltiges YAML, dazu saemtliche Grep-Gates des Plans. Die eigentliche Syntaxpruefung uebernimmt `php.yml` selbst.

## Verification

| Kriterium | Ergebnis |
|---|---|
| `grep -c '<id>findling</id>' php/appinfo/info.xml` | 1 PASS |
| `grep -c 'max-version="35"' php/appinfo/info.xml` | 1 PASS |
| `grep -v '^\s*//' php/lib/AppInfo/Application.php \| grep -c 'registerSearchProvider'` | 1 PASS |
| `grep -c 'public function boot' php/lib/AppInfo/Application.php`, Rumpf leer | 1 PASS |
| `grep -Ec 'return null' php/lib/Search/Provider.php` | 0 PASS |
| `grep -c 'exAppRequest' php/lib/Service/ExAppService.php` | 1 PASS |
| `grep -rl 'exAppRequest' php/lib --include='*.php'` | nur ExAppService.php PASS |
| `grep -c 'is_array(' php/lib/Service/ExAppService.php`, Pruefung vor jedem Methodenaufruf | 3 PASS |
| `grep -c 'getStatusCode() >= 400' php/lib/Service/ExAppService.php` | 1 PASS |
| `grep -c "'timeout' => self::TIMEOUT_SECONDS" php/lib/Service/ExAppService.php` | 1 PASS |
| `grep -c 'exAppRequestWithUserInit' php/lib/Service/ExAppService.php` | 0 PASS |
| `grep -c 'ExAppRequired' php/lib/Controller/GatewayController.php` | 1 PASS |
| `grep -c "fopen('r')" php/lib/Controller/GatewayController.php` | 1 PASS |
| `grep -Ec "fopen\('(r\+\|w\|a\|x)" php/lib/Controller/GatewayController.php` | 0 PASS |
| `grep -c 'getFirstNodeById' php/lib/Controller/GatewayController.php` | 1 PASS |
| `uses:`-Zeilen in php.yml vs. per Commit-SHA gepinnt | 2 von 2 PASS |
| `grep -rn 'fopen(' php/lib` | genau eine Stelle, Modus 'r' PASS |

### Offen bis zum Push durch den Orchestrator

Zwei Kriterien lassen sich in einem lokalen Worktree ohne Remote nicht erfuellen, weil sie einen CI-Lauf voraussetzen. Nach dem Wave-Merge und dem Push sind sie mit genau diesen Befehlen zu pruefen:

```bash
gh run list --workflow=php.yml --limit 1 --json conclusion -q '.[0].conclusion'          # erwartet: success
gh run list --workflow=integration.yml --limit 1 --json conclusion -q '.[0].conclusion'  # erwartet: success
```

`integration.yml` ist bis zu diesem Push rot, und zwar an genau der Stelle `occ app:enable -f findling`, weil `php/` leer war. Mit diesem Plan existiert die App; der Schritt und die anschliessende Kanarienprobe auf `/ocs/v2.php/search/providers` sind der eigentliche Beweis der Phase. Faellt die Kanarienprobe trotz gruenem `app:enable` durch, liegt es laut Pitfall 3 an Ursache vier (Provider registriert, aber ohne Ergebnisse) und damit im Container, nicht in dieser App.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat-Registers des Plans. Die vier Dispositionen mit `mitigate` an den Dateien dieses Plans sind umgesetzt:

| Threat ID | Umsetzung |
|---|---|
| T-01-16 | `ExAppRequired` plus Rechteaufloesung ueber `getUserFolder($userId)` |
| T-01-17 | 404 sowohl bei nicht vorhanden als auch bei nicht sichtbar |
| T-01-18 | ausschliesslich `fopen('r')`, int-fileId, Grep-Gate gegen jeden anderen Modus |
| T-01-19 | `timeout` 2 Sekunden, jeder Fehlerfall liefert sofort ein leeres Ergebnis |
| T-01-20 | `is_array()` vor jedem Methodenaufruf auf der Antwort, plus Laufzeit-Guards |
| T-01-21 | Logs tragen Statuscodes und Transportfehler, nie Suchbegriffe, Titel oder Snippets |

## Known Stubs

- `php/appinfo/routes.php` fuehrt bewusst leere Arrays. Das ist kein Platzhalter: die einzige Route dieser App wird als Attribut deklariert. Die Datei muss trotzdem existieren.
- Der Provider verlinkt bei `fileId <= 0` die Dateiliste. Diese Sonderbehandlung faellt weg, sobald der Container in Phase 2 echte Treffer mit echten fileIds liefert.

## User Setup Required

None - keine externe Dienstkonfiguration noetig.

## Next Phase Readiness

- Die PHP-Seite des Durchstichs ist vollstaendig. Was jetzt noch fehlt, ist der `/search`-Endpunkt im Container (Plan 01-04, parallele Wave) und die Registrierung der ExApp.
- Das Antwortformat ist festgelegt und wird vom Filter erzwungen: `results[]` mit `fileId` (int), `title` (string), `snippet` (string, Klartext). Der Container muss genau das liefern, sonst verwirft der Filter still.
- Fuer Plan 01-07 vorgemerkt: die XSD-Validierung der `info.xml` (xsltproc `pre-info.xslt` und danach `xmllint --schema info.xsd`, beide Dateien mit fixem Commit-SHA) gehoert dort in `php.yml` ergaenzt, zusammen mit der zweiten `info.xml`.

## Self-Check: PASSED

Alle acht angelegten Dateien existieren auf der Platte, alle drei Task-Commits (`a120a0a`, `b15dc7d`, `cabe01a`) stehen im Log, und saemtliche Grep-Acceptance-Kriterien der drei Tasks sind nach der Korrektur des `ExAppRequired`-Zaehlers gruen. Offen bleiben ausschliesslich die beiden CI-Kriterien, die einen Push voraussetzen; die Pruefbefehle stehen oben.

---
*Phase: 01-integrationsbeweis*
*Completed: 2026-08-15*
