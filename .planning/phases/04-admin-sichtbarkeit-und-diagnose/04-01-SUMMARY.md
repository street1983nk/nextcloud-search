---
phase: 04-admin-sichtbarkeit-und-diagnose
plan: 01
subsystem: testing
tags: [pytest, github-actions, php, security-gate, nextcloud, appstore]

# Dependency graph
requires:
  - phase: 03-aktualit-t-und-ocr
    provides: "Gate B (backend/tests/test_php_trust_boundary.py) mit einer Routenklasse und acht ExApp-Routen"
  - phase: 02-speicher-und-pull-queue
    provides: "php.yml mit php -l ueber php/lib und php/appinfo sowie dem Store-Validierungspfad inklusive Schritt 'State the routes finding explicitly'"
provides:
  - "Gate B kennt zwei Routenklassen: ApiRoute (ExApp) und FrontpageRoute (Admin)"
  - "Admin-Routen werden negativ gepruegt: kein NoAdminRequired, PublicPage, NoCSRFRequired, ExAppRequired"
  - "Admin-Routen brauchen kein rejectForeignCaller, und diese Lockerung ist selbst durch einen Test festgeschrieben"
  - "routes_of zaehlt FrontpageRoute-Methoden als Routen, ein reiner Admin-Controller erfuellt damit die Ein-Route-Pflicht"
  - "php -l der CI deckt php/templates ab, das Verzeichnis existiert ab jetzt"
  - "CI-Schritt 'State the settings finding explicitly' haelt die <settings>-Normalisierung des Store-Transforms als brechbare Annahme fest"
affects: [04-02, 04-03, 04-04, 04-06, 04-07, 04-09, 04-10, admin-controller, php-templates, store-release]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Zwei Routenklassen in einem textuellen Gate, unterschieden allein am Attributnamen, mit Vorrang der strengeren Klasse bei Vermischung"
    - "Negative Attributpruefung: die Admin-Klasse wird an dem gemessen, was sie NICHT tragen darf"
    - "Zwillingsschritt-Muster in php.yml: jede Annahme ueber pre-info.xslt bekommt einen CI-Schritt, der rot wird, wenn die Annahme kippt"

key-files:
  created:
    - php/templates/.gitkeep
  modified:
    - backend/tests/test_php_trust_boundary.py
    - .github/workflows/php.yml

key-decisions:
  - "Eine Methode mit beiden Attributnamen gilt als Admin-Route, weil die Admin-Klasse die strengere ist und Vermischung damit gemeldet statt durchgelassen wird"
  - "Die Anti-Vakuum-Untergrenze bleibt bei >= 8, weil noch kein Admin-Controller existiert; der Kommentar verpflichtet jeden Plan, der eine Route hinzufuegt, die Grenze mit anzuheben"
  - "php/templates wird mit einer .gitkeep angelegt statt den find-Pfad tolerant zu machen, weil jede tolerante Schreibweise das Gate stumm weniger pruefen laesst"
  - "Der neue Store-Schritt ueberspringt sich selbst, solange php/appinfo/info.xml keinen <settings>-Block hat, und faellt sowohl bei Kindern im normalisierten Block als auch bei einem ganz verschwundenen Block durch (fail closed)"
  - "ADM-01 und ADM-02 werden NICHT als erledigt markiert: dieser Plan baut nur die Gates um, die liefernden Plaene 04-03 bis 04-10 tragen dieselben IDs"

patterns-established:
  - "Routenklasse am Attribut: ApiRoute heisst ExAppRequired plus rejectForeignCaller als erste Anweisung, FrontpageRoute heisst kein Zugriffsattribut"
  - "Jede Lockerung eines Gates bekommt einen eigenen Test, der die Lockerung festschreibt, damit sie nicht versehentlich zurueckgedreht wird"

requirements-completed: [ADM-01, ADM-02]

# Metrics
duration: 12 min
completed: 2026-09-02
---

# Phase 4 Plan 01: Gate B mit zwei Routenklassen und CI-Sicht auf php/templates Summary

**Gate B unterscheidet ab jetzt ExApp-Routen (`ApiRoute` plus `ExAppRequired` plus `rejectForeignCaller`) von Admin-Routen (`FrontpageRoute` ohne jedes Zugriffsattribut) und meldet jedes der vier verbotenen Attribute auf einer Admin-Route namentlich; die CI prueft `php/templates` mit `php -l` und haelt die `<settings>`-Normalisierung des Store-Transforms als brechbare Annahme fest.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-02T16:11:00Z (ungefaehr, Start des Executors)
- **Completed:** 2026-09-02T16:23:00Z
- **Tasks:** 2 (Task 1 als TDD-Zyklus mit zwei Commits)
- **Files modified:** 3 (2 geaendert, 1 neu)

## Accomplishments

- Gate B hat zwei Routenklassen. `ROUTE_ATTRIBUTES = (ROUTE_ATTRIBUTE, ADMIN_ROUTE_ATTRIBUTE)` ist die Menge, ueber die `routes_of` und die Anti-Vakuum-Zaehlung laufen; `Route.kind` traegt `"exapp"` oder `"admin"`, und `scan_source` verzweigt daran.
- Die ExApp-Klasse ist unveraendert. Alle fuenf bestehenden Selbsttests und beide Baumtests laufen ohne Aenderung weiter, die Meldungstexte sind dieselben.
- Die Admin-Klasse ist strenger als die ExApp-Klasse: fuer jeden Namen aus `FORBIDDEN_ON_ADMIN_ROUTE` (`NoAdminRequired`, `PublicPage`, `NoCSRFRequired`, `ExAppRequired`), der ueber einer `FrontpageRoute`-Methode steht, entsteht eine Meldung mit Datei, Zeile, Methodenname, gefundenem Attribut und Begruendung in einem Satz.
- Sechs neue Selbsttests, davon vier negative: sauberer Admin-Controller, Admin-Route ohne `rejectForeignCaller` ist sauber, und je einer fuer die vier verbotenen Attribute. Insgesamt hat Gate B damit elf Selbsttests und drei Baumtests.
- Eine Methode, die beide Attributnamen traegt, faellt in die strengere Klasse. Damit ist die Vermischung der Klassen selbst eine Meldung und keine Luecke.
- `test_every_controller_of_the_app_carries_at_least_one_route` bleibt gueltig, weil FrontpageRoute-Methoden als Routen zaehlen. Ein Controller mit ausschliesslich Admin-Routen ist damit anlegbar, ohne dass ein Gate rot wird.
- Der Modul-Docstring haelt die Begruendung aus Pitfall 7 und Pitfall 10 schriftlich fest: `ExAppRequired` auf einer Admin-Route dreht den Schutz um (der Admin-Browser kaeme nicht hin, jeder registrierte Fremd-Container schon), und `access_level ADMIN` in `backend/appinfo/info.xml` greift nur im Weg Browser zu AppAPI-Proxy zu ExApp, nicht bei `PublicFunctions::exAppRequest`. Der wirksame Schutz ist der PHP-Controller selbst.
- `php -l` sieht `php/templates`. Das Verzeichnis ist mit einer `.gitkeep` angelegt, deren Inhalt den Grund nennt, und der Kommentarblock ueber dem Schritt sagt, dass es auf der Entwicklungsmaschine kein PHP gibt.
- Der neue Schritt `State the settings finding explicitly` ist der Zwilling von `State the routes finding explicitly`, in derselben Form und mit derselben Absicht: er ist heute ein Ueberspringen mit Begruendung, ab Plan 04-03 eine Zusicherung, und er wird rot, wenn der Store seine Vertauschung der Templates fuer `activity` und `settings` korrigiert.

## Task Commits

Jede Aufgabe wurde einzeln committet:

1. **Task 1 (RED): Selbsttests fuer die Admin-Routenklasse** - `538f8dd` (test)
2. **Task 1 (GREEN): zwei Routenklassen in Gate B** - `e1fcb50` (feat)
3. **Task 2: php/templates im php -l-Pfad und der settings-Schritt** - `c002157` (chore)

Ein REFACTOR-Commit war nicht noetig: die GREEN-Fassung ist die Endfassung, `scan_source` verzweigt einmal und kehrt fuer die Admin-Klasse frueh zurueck.

## Files Created/Modified

- `backend/tests/test_php_trust_boundary.py` - Gate B: neue Konstanten `ADMIN_ROUTE_ATTRIBUTE`, `ROUTE_ATTRIBUTES`, `FORBIDDEN_ON_ADMIN_ROUTE`; `Route.kind`; zweiklassiges `routes_of` und `scan_source`; Anti-Vakuum-Zaehlung ueber beide Attributnamen; sechs neue Selbsttests; Docstring-Absatz zu beiden Klassen
- `.github/workflows/php.yml` - `find php/lib php/appinfo php/templates` im Schritt `Syntax check every PHP file` plus Begruendung im Kommentar; neuer Schritt `State the settings finding explicitly` hinter dem Routen-Zwilling
- `php/templates/.gitkeep` - haelt das Verzeichnis offen, damit `find` nicht abbricht; nennt den Grund und den Plan, der das erste Template bringt

## Decisions Made

- **Vermischung faellt in die strenge Klasse.** Eine Methode mit `ApiRoute` und `FrontpageRoute` gilt als `admin`. Die andere Richtung waere die unsichere: eine Admin-Route, die versehentlich auch `ApiRoute` traegt, wuerde nach der milderen Regel beurteilt.
- **Untergrenze bleibt bei 8.** Es gibt noch keinen Admin-Controller, also waere jede hoehere Zahl heute rot. Der Kommentar an der Assertion verpflichtet den Plan, der die erste Admin-Route anlegt, die Grenze mit anzuheben, sonst hoert die Klausel auf, ein Sperrklinkenrad zu sein.
- **`.gitkeep` statt tolerantem `find`.** Der Plan hat diese Wahl vorgegeben und die Begruendung stimmt: `find ... 2>/dev/null` oder eine `-path`-Konstruktion laesst das Gate im Zweifel weniger pruefen als es behauptet, und genau das ist der Fehlermodus, gegen den der Job existiert.
- **Der settings-Schritt ist fail closed in beide Richtungen.** Leerer normalisierter Block heisst gruen mit Begruendungszeile, Kinder im Block heissen rot, und ein ganz verschwundener Block heisst ebenfalls rot. Ein verschwundener Block waere eine andere Aenderung derselben Annahme, also darf er nicht als Erfolg durchgehen.
- **ADM-01 und ADM-02 bleiben offen.** Siehe Deviations.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Der settings-Schritt behandelt auch den verschwundenen Block als Fehler**
- **Found during:** Task 2
- **Issue:** Der Plan nennt als Fehlerfall nur "Quellblock vorhanden plus normalisierter Block MIT Kindern". Ein normalisierter Block, der ganz fehlt, waere damit stumm gruen gewesen, obwohl er dieselbe Annahme bricht wie ein Block mit Kindern: er wuerde bedeuten, dass `pre-info.xslt` `<settings>` nicht mehr leert, sondern verwirft.
- **Fix:** Dritter Zweig im Schritt mit eigener Meldung und `exit 1`. Der Erfolgsfall ist ausschliesslich `<settings/>`.
- **Files modified:** `.github/workflows/php.yml`
- **Verification:** Alle drei Zweige lokal mit `bash -e` und den drei Eingaben `<settings/>`, `<settings><admin>X</admin></settings>` und einem Dokument ohne `settings` durchgespielt; Ergebnis PASS, FAIL-Kinder, FAIL-verschwunden.
- **Committed in:** `c002157`

### Bewusste Abweichung ohne Auto-Fix

**2. [Rule 4-nah, dokumentiert statt ausgefuehrt] ADM-01 und ADM-02 wurden nicht als erledigt markiert**
- **Found during:** Abschluss (Schritt `update_requirements`)
- **Issue:** Die Plan-Frontmatter traegt `requirements: [ADM-01, ADM-02]`, und der Workflow verlangt `requirements.mark-complete`. Dieser Plan liefert aber keinen Teil der Statusseite und keine Pro-Datei-Diagnose, er baut nur die Gates um, die den Bau erlauben. Ein Haken haette behauptet, die Statusseite existiere.
- **Entscheidung:** Nicht markiert. Die liefernden Plaene tragen dieselben IDs (04-03, 04-04, 04-06 und 04-10 fuer ADM-01; 04-07, 04-09 und 04-10 fuer ADM-02), der Haken faellt dort korrekt. Die IDs stehen wie vom Template gefordert in `requirements-completed` dieser Zusammenfassung, damit die Zuordnung Plan zu Anforderung nachvollziehbar bleibt.
- **Files modified:** keine
- **Impact:** `.planning/REQUIREMENTS.md` bleibt unangetastet. Eine Verifikation, die nach ADM-01 fragt, findet den Punkt weiter offen, was der Wahrheit entspricht.

---

**Total deviations:** 1 auto-fixed (1 fehlende kritische Funktionalitaet), 1 bewusst nicht ausgefuehrt und dokumentiert
**Impact on plan:** Kein Scope-Creep. Der Auto-Fix macht den neuen CI-Schritt fail closed statt nur halb geschlossen; die zweite Abweichung verhindert eine falsche Fortschrittsmeldung.

## Issues Encountered

- **Ein RED-Test war bereits gruen.** `test_an_admin_route_needs_no_reject_foreign_caller` lief schon in der RED-Phase durch, allerdings leer: `routes_of` erkannte die FrontpageRoute-Methode gar nicht, also gab `scan_source` eine leere Liste zurueck. Der Test ist kein Feature-Nachweis, sondern eine Sperre gegen das Zurueckdrehen der Lockerung, und die anderen fuenf RED-Tests belegten die Abwesenheit der Funktion eindeutig (5 failed, 9 passed). Nach GREEN ist derselbe Test nicht mehr leer, weil `routes_of` jetzt genau eine Route findet.
- Sonst keine. Beide Aufgaben liefen ohne Nacharbeit durch.

## Verification

- `cd backend && uv run python -m pytest tests/test_php_trust_boundary.py tests/test_readonly_gate.py -q` -> 39 passed
- `cd backend && uv run ruff check .` -> All checks passed
- `cd backend && uv run ruff format --check .` -> 72 files already formatted
- `cd backend && uv run pyright` -> 0 errors, 0 warnings, 0 informations
- `cd backend && uv run vulture src tests --min-confidence 80` -> keine Ausgabe
- `.github/workflows/php.yml` ist gueltiges YAML (`yaml.safe_load`), die Schrittliste des Jobs `app-metadata` endet auf `State the routes finding explicitly` und `State the settings finding explicitly`, der `php -l`-Schritt lautet `find php/lib php/appinfo php/templates -name '*.php' -print0 | xargs -0 -n1 php -l`
- `APPSTORE_SHA` unveraendert `5c4373d7d026a8f7c7838cc9990fecaf19e8e682`
- `grep -c 'FrontpageRoute' backend/tests/test_php_trust_boundary.py` -> 6; `grep -v '^#' ... | grep -c 'NoAdminRequired'` -> 4
- `assert len(routes) == mentions` und `assert len(routes) >= 8` beide weiterhin vorhanden
- Kein Em-Dash und kein En-Dash in beiden geaenderten Dateien; `backend/tests/test_php_trust_boundary.py` enthaelt kein einziges Zeichen ueber ASCII
- `git diff --diff-filter=D --name-only HEAD~3 HEAD` -> leer, keine Datei geloescht

## Known Stubs

`php/templates/.gitkeep` ist ein Platzhalter mit Absicht: das Verzeichnis muss existieren, damit `find` nicht abbricht, und das erste echte Template kommt in Plan 04-03. Sonst keine Stubs.

## User Setup Required

Keine. Es wurde kein Paket installiert und kein externer Dienst angefasst (T-04-SC: Phase 4 hat keinen Installationsschritt).

## Next Phase Readiness

- Ein PHP-Controller mit ausschliesslich `FrontpageRoute`-Methoden und ohne Zugriffsattribut kann jetzt angelegt werden, ohne dass Gate B, Gate A oder der `php -l`-Job rot werden. Das ist die Voraussetzung, die Plan 04-03 braucht.
- Fuer den Plan, der die erste Admin-Route anlegt, bleiben zwei Pflichten offen und sind im Code kommentiert: die Untergrenze `assert len(routes) >= 8` mit anheben, und `<settings>` im `php/appinfo/info.xml` nach `<commands>` schreiben, wodurch der neue CI-Schritt von "uebersprungen" auf "geprueft" umschaltet.
- Offen aus dem RESEARCH und nicht Teil dieses Plans: der Docstring von `backend/src/findling/api/status.py` behauptet weiter, `access_level ADMIN` in der `info.xml` sei der Ort, an dem die Entscheidung durchgesetzt wird. Pitfall 10 widerlegt das fuer den `exAppRequest`-Weg. Die Praezisierung gehoert in den Plan, der die Diagnoseroute anfasst.

---
*Phase: 04-admin-sichtbarkeit-und-diagnose*
*Completed: 2026-09-02*

## Self-Check: PASSED

Alle drei Dateien liegen auf der Platte, `php/templates/.gitkeep` ist von git erfasst, und alle vier Commits (`538f8dd`, `e1fcb50`, `c002157`, `edeeff5`) sind in der Historie auffindbar.
