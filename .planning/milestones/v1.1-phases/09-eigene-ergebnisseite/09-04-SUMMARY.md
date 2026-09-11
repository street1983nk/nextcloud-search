---
phase: 09-eigene-ergebnisseite
plan: 04
subsystem: api
tags: [php, controller, routing, url-vertrag, paginierung, xss, gates]

requires:
  - phase: 09-eigene-ergebnisseite
    provides: "09-01: ExAppService::PAGE_REQUEST_TIMEOUT_SECONDS = 1.5 und der Messbericht 2026-09-seitenbudget"
  - phase: 09-eigene-ergebnisseite
    provides: "09-02: Gate B kennt die Routenklasse userpage und die Anti-Vakuitaets-Schranke 13"
  - phase: 09-eigene-ergebnisseite
    provides: "09-03: SearchService::run, SearchCaps, SearchOutcome, ApprovedHit"
provides:
  - PageController mit genau einer Route findling.page.index (GET /apps/findling/)
  - Der geprüfte URL-Vertrag query, names, page, cursors mit stillem Rückfall auf Seite 1
  - Der Parametervertrag des Templates (elf Schlüssel), den Plan 09-05 konsumiert
  - Highlighter::segments als einzige Übersetzung von Highlight-Offsets in Textstücke
  - PageController::PAGE_SIZE 25, MAX_PAGE 20, BUDGET_SECONDS 3.0 als benannte Konstanten
  - php/tests/Unit/PageControllerTest.php mit 19 Fällen
  - php/tests/Unit/HighlighterTest.php mit 11 Fällen
affects: [09-05, 09-06, 09-07, 09-08]

tech-stack:
  added: []
  patterns:
    - "Der Zerleger liefert Textstücke mit Marke statt zusammengebautem HTML, damit auf der Seite keine Zeichenkette Auszeichnung aus Daten baut"
    - "Ein Cursorpfad in der Adresse trägt den Rückweg, statt einen Offset aus der Seitenzahl zu rechnen"
    - "Jede Abweichung im URL-Vertrag fällt still auf Seite 1 zurück; die Seite macht über die eigene Adresszeile keine Aussage"
    - "Eine Fremdkonstante wird im Controller voll qualifiziert referenziert, damit ein Zähl-Kriterium zählbar bleibt"

key-files:
  created:
    - php/lib/Controller/PageController.php
    - php/lib/Text/Highlighter.php
    - php/tests/Unit/PageControllerTest.php
    - php/tests/Unit/HighlighterTest.php
  modified:
    - php/lib/Service/ExAppService.php

key-decisions:
  - "ExAppService::MAX_HIGHLIGHTS wird öffentlich, damit der Zerleger den Deckel liest statt ihn zu kopieren"
  - "IL10N wird nicht injiziert: der Controller erzeugt keinen einzigen übersetzten Text, alle Zustandstexte stehen im Template"
  - "Kein $appName-Konstruktorargument, sondern Application::APP_ID, wie in allen drei bestehenden Controllern der App"
  - "nextUrl entsteht nur, wenn der gemeldete Cursor echt hinter dem Startcursor liegt, sonst wäre der Weiter-Knopf ein Link zurück auf Seite 1"

patterns-established:
  - "Stand-in-Welt für einen Controller ohne Nextcloud: sechs OCP-Schnittstellen als Attrappe, echte Wertobjekte per require, php im Testcontainer"

requirements-completed: [UI-01, UI-02]

duration: 95min
completed: 2026-09-09
---

# Phase 9 Plan 04: Serverhälfte der Ergebnisseite Summary

**Eine Route, `findling.page.index`, prüft die vier Werte ihrer Adresse, reicht die Zahlen der Seite an den geteilten Dienst und legt dem Template elf fertige Werte hin; der neue `Highlighter` zerlegt einen Auszug an Zeichen-Offsets in Textstücke mit Marke und baut dabei kein einziges Zeichen Auszeichnung.**

## Performance

- **Duration:** rund 95 min
- **Tasks:** 3 (Task 1 als TDD-Zyklus)
- **Files:** 5 (4 neu, 1 geändert), 1.267 Zeilen dazu, 1 weg

## Accomplishments

- `PageController` trägt genau eine Route. Gate B klassifiziert sie als `userpage`, die Anti-Vakuitäts-Schranke steht damit bei 13 gefundenen Routen und 13 Attributnennungen, und `scan_source` meldet über alle vier Controller keine Verletzung.
- Der URL-Vertrag ist vollständig geprüft: `query` läuft durch `PlainText::bounded(…, 255)` und gilt bei ungültigem UTF-8 als leer, `names` setzt den Filter nur beim Wort `1`, `page` fällt für alles ausserhalb von 1 bis 20 auf 1, und `cursorPath()` verlangt genau `page` Einträge, Ziffernform, Startwert 0 und strenge Monotonie. Jede Abweichung ergibt `[0]` und Seite 1, ohne Meldung.
- Die Zahlen der Seite stehen als benannte Konstanten mit Begründung: `PAGE_SIZE` 25 (25 × 4 = 100 = die grösste Kandidatenzahl eines Containeraufrufs), `MAX_PAGE` 20, `MAX_ROUNDS` 3, `OVERFETCH` 4, `MAX_RECHECKS_PER_HIT` 2, `MAX_RECHECKS_ABSOLUTE` 64, `MAX_QUERY_LENGTH` 255 und `BUDGET_SECONDS` 3.0 mit Messdatum und dem Pfad `docs/measurements/2026-09-seitenbudget/README.md`, Abschnitt 6.2, im Docblock.
- Der Per-Call-Deckel reist als `\OCA\Findling\Service\ExAppService::PAGE_REQUEST_TIMEOUT_SECONDS`, voll qualifiziert und ohne `use`-Import, damit das Zähl-Kriterium des Plans genau eine Nennung sieht.
- `Highlighter::segments()` liefert eine Liste aus `text` und `mark`. Es gibt in der Klasse kein `htmlspecialchars` und kein Markierungselement als Zeichenkette; das Element setzt erst das Template, und jedes Stück läuft dort einzeln durch den escapenden Drucker (T-09-02).
- Der Zerleger arbeitet ausschliesslich mit `mb_substr` und expliziter Kodierung UTF-8, sortiert die Bereiche selbst nach Startwert und verwirft überlappende, rückwärts laufende und ausserhalb des Textes liegende Bereiche, statt sie zurechtzubiegen. Die Zahl der markierten Bereiche ist auf `ExAppService::MAX_HIGHLIGHTS` geklemmt, gelesen aus der Konstante.
- 30 neue PHPUnit-Fälle: 11 in `HighlighterTest`, 19 in `PageControllerTest`. Keiner davon schreibt eine Konstante der Seite als Zahl in eine Erwartung; alle werden per Reflection gelesen.

## Task Commits

1. **Task 1: Der Highlight-Zerleger (TDD)** - `d92f5cb` (test, RED), `0012590` (feat, GREEN)
2. **Task 2: Der PageController mit genau einer Route** - `1b8ba05` (feat)
3. **Task 3: Der Test des Controllers** - `4b9086a` (test)

Ein REFACTOR-Commit für Task 1 entfällt: die GREEN-Fassung war bereits die Form, die der Plan beschreibt, und eine Umformung ohne Verhaltensänderung hätte nichts verbessert.

## Verification

| Prüfung | Ergebnis |
|---|---|
| `php -l` über `Highlighter.php`, `PageController.php`, `ExAppService.php`, beide Testklassen | 5 von 5 `No syntax errors` |
| `grep -c 'FrontpageRoute'` in `PageController.php` | 1 |
| `grep -c 'NoAdminRequired'` / `grep -c 'NoCSRFRequired'` | 1 / 1 |
| `grep -c 'getFirstNodeById\|isReadable\|ExAppService'` in `PageController.php` | 1, und das ist die Zeile mit `PAGE_REQUEST_TIMEOUT_SECONDS` |
| `grep -c 'RENDER_AS_USER'` in `PageController.php` | 1 |
| `grep -c '2026-09-seitenbudget'` in `PageController.php` | 1 (Docblock von `BUDGET_SECONDS`) |
| `grep -c 'mb_substr'` / `grep -cw 'substr'` in `Highlighter.php` | 3 / 0 |
| `grep -c 'htmlspecialchars\|<mark'` in `Highlighter.php` | 0 |
| `grep -c 'function test'` in `HighlighterTest.php` / `PageControllerTest.php` | 11 / 19 |
| `grep -c '25\|== 20'` in `PageControllerTest.php` | 0 |
| `uv run pytest -q tests/test_php_trust_boundary.py tests/test_php_acl_boundary.py` | 29 passed |
| Routenklassifikation von Gate B | 13 Routen, davon `PageController.php::index` als `userpage`, 0 Verletzungen |
| `uv run pytest -q` (ganze Backend-Suite) | 1778 passed, 15 skipped |
| Lokale Verhaltensprobe des Zerlegers (Stand-in-Welt) | 15 von 15 grün |
| Lokale Verhaltensprobe des Controllers (Stand-in-Welt) | 61 von 61 grün |

**Nicht lokal prüfbar:** der PHPUnit-Job. Auf dieser Maschine gibt es kein PHP ausserhalb des Testcontainers und keinen `nextcloud/server`-Checkout, den `php/tests/bootstrap.php` verlangt; die Suite ist laut `docs/testing.md` bewusst CI-only. Ersatz sind die beiden Verhaltensproben, die dieselben Aussagen gegen eine Stand-in-Welt führen.

**Ebenfalls nicht geprüft: die `curl`-Zeile der Plan-Verifikation.** Der Testcontainer `findling-nextcloud` bindet `C:/Users/Student/nextcloud-search/php` ein, also den Hauptbaum und nicht diesen Worktree; die neue Route ist dort noch nicht installiert. Ein Kopieren in das Bind-Mount hätte den Arbeitsbaum ausserhalb dieses Worktrees verändert und ist deshalb unterblieben. Der Nachweis, dass die Route ohne Sitzung auf die Anmeldung führt und mit Sitzung antwortet, gehört damit in die Abnahme nach Plan 09-05, wo das Template existiert und die Seite überhaupt rendern kann. Bis dahin ist ein 500 an dieser Adresse der erwartete Zustand: `TemplateResponse` benennt `search`, und `php/templates/search.php` legt erst Plan 09-05 an.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `ExAppService::MAX_HIGHLIGHTS` war privat**

- **Found during:** Task 1
- **Issue:** Der Plan verlangt, dass der Zerleger den Deckel aus der Konstante liest statt ihn abzuschreiben. Die Konstante war `private`, ein Zugriff aus `OCA\Findling\Text\Highlighter` also unmöglich.
- **Fix:** Die Konstante wird `public`, mit einem Docblock-Absatz, der die zweite Leserin benennt und begründet, warum zwei Kopien derselben Zahl zwei Zahlen sind, die auseinanderlaufen. Dieselbe Bewegung wie bei `REQUEST_TIMEOUT_SECONDS` in Plan 09-03.
- **Files modified:** `php/lib/Service/ExAppService.php`
- **Commit:** `0012590`

**2. [Rule 2 - Missing critical functionality] Kein `nextUrl`, wenn der Cursor nicht vorrückt**

- **Found during:** Task 2
- **Issue:** Der Plan baut `nextUrl` aus `hasMore`, `page < MAX_PAGE` und `failure === null`. Meldet der Dienst `hasMore` mit einem `nextCursor`, der nicht echt hinter dem letzten Element des Pfads liegt, entstünde ein Pfad, der nicht streng aufsteigend ist. Genau dieser Pfad wird beim nächsten Aufruf von `cursorPath()` verworfen, der Besucher landet still auf Seite 1, und der Weiter-Knopf wäre ein Zurück-Knopf.
- **Fix:** Vierte Bedingung `nextCursor > letztes Element`. Das ist die wörtliche Umsetzung der Zeile "Nie 'Weiter' ins Leere" des Paginierungsvertrags und kein neues Verhalten daneben.
- **Files modified:** `php/lib/Controller/PageController.php`
- **Commit:** `1b8ba05`, Testfall `testANextCursorThatDoesNotAdvanceOffersNoNextAddress`

### Abweichungen von der Bauform des Plans

**3. `IL10N` wird nicht injiziert.** Der Plan listet es unter den Konstruktorabhängigkeiten. Der Controller erzeugt jedoch keinen einzigen übersetzten Text: jeder Zustandssatz, jede Überschrift und der zugängliche Name einer Trefferzeile stehen laut 09-UI-SPEC im Template, und das Template bekommt sein `$l` von Nextcloud selbst. Eine ungenutzte Abhängigkeit wäre im Bestand dieser App ein Fremdkörper, denn `IL10N` wird dort ausschliesslich dort injiziert, wo es benutzt wird (`Provider`, `AdminViewService`, `Section`). Sollte Plan 09-05 wider Erwarten einen übersetzten Wert aus dem Controller brauchen, ist das ein Konstruktorargument mehr und keine Umbauarbeit.

**4. Kein `$appName`-Konstruktorargument.** Der Plan nennt `$appName` als erste Abhängigkeit. Alle drei bestehenden Controller der App (`SettingsController`, `GatewayController`, `QueueController`) nehmen stattdessen nur `IRequest` und rufen `parent::__construct(Application::APP_ID, $request)`. Die neue Klasse folgt dem Bestand, weil ein von aussen gesetzter App-Name eine Angabe wäre, die niemand je anders setzt.

## Threat Model

Alle Dispositionen des Plans sind umgesetzt oder bewusst übernommen.

| Threat ID | Umsetzung |
|---|---|
| T-09-09 (Tampering, `cursors`/`page`) | `cursorPath()` prüft Länge, Ziffernform, Startwert und strenge Monotonie; jede Abweichung ergibt `[0]` und `page` 1. Acht Zusicherungen in `PageControllerTest`, acht in der Verhaltensprobe |
| T-09-01 (Tampering, `query`) | `PlainText::bounded(…, 255)`; ungültiges UTF-8 gilt als leer. Der Wert reist unescaped, weil genau eine Stelle escaped, und das ist das Template |
| T-09-02 (Tampering, Auszug und Offsets) | `Highlighter::segments()` liefert Textstücke, nie Auszeichnung. Ausserhalb liegende, überlappende und rückwärts laufende Bereiche werden verworfen, nicht repariert |
| T-09-07 (DoS, tiefe Paginierung) | `MAX_PAGE` 20 im Controller, davor `SearchService::MAX_CONTAINER_OFFSET` 1200 und der Scan-Deckel im Container |
| T-09-09 (Spoofing, CSRF) | accept, wie geplant: die Route ist GET, ändert keinen Zustand, und das Fehlen des Token-Zwangs ist die Bedingung dafür, dass Lesezeichen, Zurück-Navigation und der Dialog-Link funktionieren. Gate B erzwingt das Attribut für die Klasse `userpage` |
| T-09-06 (Spoofing, fremder Container) | Die Route trägt weder das Container- noch das Öffentlich-Attribut; Gate B verbietet beide für diese Klasse und prüft es an der Methode |
| T-09-04 (EoP, zweite Berechtigungsentscheidung) | Der Controller ruft ausschliesslich `SearchService::run`. `test_php_acl_boundary.py` bleibt grün: genau eine Lesbarkeitsfrage und ein Register von drei Auflösungen, keine davon in diesem Controller |
| T-09-08 (Info Disclosure, Log) | Eine statische Zeile, nur bei den zwei Gründen, die einen Fehlerblock erzeugen. Kein Suchbegriff, kein Pfad, keine Nutzerkennung. Die Verhaltensprobe zählt die Zeilen: 1 bei `backend_silent` und `version_drift`, 0 bei `no_home_folder` und `offset_ceiling` |
| T-09-SC (Supply Chain) | Kein Paket installiert, kein `composer require`, kein `npm install` |

Keine neue Angriffsfläche ausserhalb des Registers: die Route ist die einzige neue Netzwerkoberfläche, sie liest, und sie steht im Modell.

## Notes for Future Phases

- **Der Parametervertrag steht.** Das Template von Plan 09-05 bekommt genau diese elf Schlüssel: `query` (unescaped, geklemmt), `titleOnly`, `page`, `maxPage`, `hits`, `hasMore`, `degraded`, `failure`, `previousUrl`, `nextUrl`, `formAction`. Ein Treffer trägt `fileId`, `title`, `path`, `iconUrl`, `url` und `segments`; `segments` ist leer, wenn kein Auszug vorliegt, und das Template setzt dann den Pfad an diese Stelle.
- **`failure` ist keine Anweisung, welchen Block zu zeigen ist.** `FAILURE_OFFSET_CEILING` gehört laut 09-UI-SPEC auf die Hinweiszeile und nie auf den Fehlerblock, `FAILURE_BACKEND_SILENT`, `FAILURE_VERSION_DRIFT` und `FAILURE_NO_HOME_FOLDER` auf den Fehlerblock. Diese Zuordnung trifft das Template.
- **Der Weiter-Link kann auch bei `hasMore` fehlen**, nämlich auf der letzten Seite, nach einem Fehlgrund und bei einem Cursor, der nicht vorrückt. Das Template darf `hasMore` also nicht als Ersatz für `nextUrl !== null` benutzen.
- **`php/templates/search.php` fehlt noch.** Bis Plan 09-05 antwortet die Route mit 500. Das ist kein Defekt dieses Plans, sondern die geplante Reihenfolge.
- **Die lokalen Verhaltensproben liegen in `.dev/probe-0904/`** und sind gitignoriert. Sie ersetzen PHPUnit nicht und wollen es nicht: sie stellen eine Stand-in-Welt aus sechs OCP-Attrappen und lassen die echten Klassen darin laufen.

## Self-Check: PASSED
