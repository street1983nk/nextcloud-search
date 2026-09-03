---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 15
subsystem: php
tags: [phpunit, unit-tests, ci-gate, composer, supply-chain, ocp-mocks, security-boundary]

# Dependency graph
requires:
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: 05-13, die vereinheitlichten Action-Pinnungen und test_workflow_pins.py, dessen fuenf Regeln der neue Job erfuellen muss
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: 05-01 und 05-08, der Server-Checkout je Version und die Composite Action setup-test-nc als Vorbild fuer Reihenfolge und Extensionsliste
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: 05-07, ExAppService mit driftOnRecord und der Provider-Stand, gegen den die Tests geschrieben sind
provides:
  - php/tests, die erste Unit-Test-Suite der PHP-Haelfte, 43 Tests
  - der CI-Job phpunit in php.yml, CI-only, mit Server-Checkout, Bootstrap-Negativprobe und einer Untergrenze fuer die ausgefuehrte Testzahl
  - php/tests/bootstrap.php, das OCP aus dem Server-Checkout laedt und ohne Server mit eigener Meldung abbricht
  - phpunit/phpunit als einzige und exakt gepinnte dev-Abhaengigkeit des Repositories, mit composer.lock
  - Tests fuer die Verhaltensweisen 1 bis 6 aus docs/testing.md, darunter die drei am Kandidatenfilter
affects: [Plan 05-16 (Verhaltensweisen 7 bis 12), Plan 05-18 (Release-Archiv darf require-dev nicht enthalten), Phase-Review]

# Tech tracking
tech-stack:
  added:
    - phpunit/phpunit 11.5.56 als require-dev der PHP-Haelfte, exakt gepinnt, Bezug nur in CI
  patterns:
    - Ein Test-Bootstrap, der seine Vorbedingung selbst prueft und mit einer eigenen Meldung abbricht, statt sie dreissig Zeilen spaeter als Klassennicht-gefunden zu zeigen
    - Der Job prueft die ausgefuehrte Testzahl aus dem JUnit-Protokoll, nicht aus der menschenlesbaren Zusammenfassung
    - Ein konstanter Wert der Produktionsklasse wird im Test per Reflection gelesen und nie abgeschrieben
    - Die Negativprobe eines Gates laeuft auf einem Wegwerf-Zweig, damit der Arbeitszweig keinen absichtlich kaputten Commit traegt

key-files:
  created:
    - php/tests/bootstrap.php
    - php/phpunit.xml
    - php/composer.lock
    - php/tests/Unit/BootstrapTest.php
    - php/tests/Unit/ExAppServiceTest.php
    - php/tests/Unit/ProviderTest.php
    - php/tests/Unit/PlainTextTest.php
  modified:
    - php/composer.json
    - php/lib/Service/ExAppService.php
    - .github/workflows/php.yml
    - .gitignore
    - docs/testing.md
    - .planning/phases/05-h-rtung-und-store-einreichung-v1-0/deferred-items.md

key-decisions:
  - "phpunit/phpunit 11.5.56, exakt gepinnt: die Hauptversion stammt aus vendor-bin/phpunit/composer.json von nextcloud/server stable34 (^11.5) und ist nach oben durch php >=8.2 begrenzt, weil PHPUnit 12 bereits 8.3 verlangt"
  - "Der Job faehrt stable34 und keine Matrix, weil die PHPUnit-Hauptversion an den Serverzweig gebunden ist; die Folge ist als DI-05-17 festgehalten"
  - "ExAppService verliert das Schluesselwort final und behaelt die Absicht als @final-Annotation, weil PHPUnit keine finale Klasse doppeln kann und Provider sie beim konkreten Typ nimmt"
  - "Kein Code-Coverage-Aufbau: es gibt keine Zahl, die daraus folgen soll, und die Messgroesse dieser Suite ist die Liste in docs/testing.md"
  - "failOnDeprecation bleibt aus, weil die Suite im Autoload-Raum des Servers laeuft und dessen Deprecations nicht die dieses Repositories sind"

requirements-completed: [PKG-05]

duration: 34 min
completed: 2026-09-03
---

# Phase 5 Plan 15: PHPUnit-Suite und CI-Job fuer die PHP-Haelfte Summary

Die PHP-Haelfte hat zum ersten Mal Unit-Tests: 43 Faelle gegen die Verhaltensweisen 1 bis 6 aus `docs/testing.md`, ausgefuehrt von einem CI-Job, der `nextcloud/server` auscheckt und die Suite mit dessen Bootstrap faehrt, damit `IRootFolder` und Geschwister mit `createMock` gedoppelt werden koennen.

## Was gebaut wurde

**Das Geruest (Task 2).** `php/composer.json` bekommt `require-dev` mit `phpunit/phpunit` in der exakten Version `11.5.56` und `autoload-dev` fuer den Testnamensraum `OCA\Findling\Tests\`. Die Laufzeit-Abhaengigkeiten sind unberuehrt: `composer.lock` weist `packages: 0` und `packages-dev: 27` aus. `php/phpunit.xml` faehrt die strengen Schalter dieses Projekts und keinen Coverage-Aufbau. `php/tests/bootstrap.php` laedt zuerst das Bootstrap des Servers und danach den Autoload der App.

**Der Job.** `phpunit` in `php.yml` checkt den Server aus, verschiebt die App nach `apps/findling`, installiert eine Wegwerf-Instanz auf SQLite, damit `lib/base.php` eine Konfiguration zu lesen hat, installiert die dev-Abhaengigkeiten und faehrt die Suite. Vor dem Lauf steht die Negativprobe des Bootstrap-Waechters, danach die Feststellung der ausgefuehrten Testzahl aus dem JUnit-Protokoll.

**Die Tests (Task 3).** Drei Klassen fuer die sechs Verhaltensweisen, plus `BootstrapTest` als Antivakuitaetstest des Geruests.

| Verhalten | Datei | Kern der Behauptung |
|-----------|-------|---------------------|
| 1 | `ExAppServiceTest` | Kandidat ohne `fileId` oder mit einer, die keine ganze Zahl ist (Zeichenkette, Gleitkommazahl, null, Array, Bool), wird verworfen |
| 2 | `ExAppServiceTest` | `fileId` 0 oder negativ ueberlebt nur als Kanarienvogel, und auch der nur mit Auszug |
| 3 | `ExAppServiceTest` | Jeder Kandidat mit positiver `fileId` verliert `title` und `snippet`, auch wenn der Container beide mitschickt |
| 4 | `ProviderTest` | Ein Knoten, den der eigene Ordner nicht aufloest, wird nie ein Treffer; Titel und Link kommen aus dem Knoten; ein aufloesbarer, aber nicht lesbarer Knoten faellt ebenfalls |
| 5 | `ProviderTest` | Ohne Home-Verzeichnis ist das Ergebnis leer, und der Container wird gar nicht erst gefragt |
| 6 | `PlainTextTest` | Ein Leerzeichen je Steuerzeichen mit Laengenerhalt, Tabulator bleibt, Klemmung, Zeichengrenze auch ausserhalb der Basisebene, ungueltiges UTF-8 wird verweigert |

Der Kanarienvogel-Wert wird per Reflection aus der privaten Konstante gelesen. `grep -rn "findling-canary" php/tests/` findet nichts, was die geforderte Form ist: eine Umbenennung der Konstante macht die Tests rot statt stumm.

## Belege

Alle Laeufe auf dem Zweig `worktree-agent-05-15`, Workflow `php.yml`.

| Lauf | Ergebnis | Was er zeigt |
|------|----------|--------------|
| 33772152218 | rot | Der Bootstrap-Waechter feuert bei seinem ersten Einsatz, weil der Vorgabepfad vier statt drei Ebenen hochging. Der Fehler war eine Zeile, die Meldung nannte den gesuchten Pfad und seine Herkunft. |
| 33772390698 | gruen | Das Geruest traegt: PHPUnit 11.5.56 auf PHP 8.2.33, `OK (3 tests, 10 assertions)`, `the suite executed 3 tests, the floor is 1` |
| 33772868132 | gruen | Die sechs Verhaltensweisen: `OK (43 tests, 80 assertions)`, `the suite executed 43 tests, the floor is 14` |
| 33773014571 | rot | Die Rotprobe, siehe unten |
| 33773350793 | gruen | Abschlusslauf nach dem Doku-Nachzug, unveraendert 43 Tests |

**Die Rotprobe.** Auf dem Wegwerf-Zweig `worktree-agent-05-15-redprobe` wurde in `filterCandidates` das Abstreifen aufgehoben (`$kept[] = $candidate` statt `$kept[] = ['fileId' => $fileId]`), also genau Verhalten 3 gebrochen. Ergebnis: `Tests: 43, Assertions: 78, Failures: 3`, und die drei sind exakt die drei Faelle zu Verhalten 3:

```
1) ExAppServiceTest::testEveryCandidateWithAPositiveFileIdLosesItsTitleAndItsSnippet
2) ExAppServiceTest::testTheStrippingHoldsForEveryCandidateOfAPageAndNotOnlyTheFirst
3) ExAppServiceTest::testAPageMixingTheCanaryWithOrdinaryHitsKeepsBothRulesApart
```

Der Zweig ist lokal und auf `origin` geloescht, der Arbeitszweig hat nie einen absichtlich kaputten Commit getragen, und `grep "DELIBERATE DEFECT" php/lib/Service/ExAppService.php` findet nichts.

**Die Bootstrap-Negativprobe** laeuft in jedem Lauf mit, nicht nur einmal: der Schritt setzt `NEXTCLOUD_SERVER_ROOT=/nonexistent-on-purpose`, verlangt einen Fehlschlag und prueft den Wortlaut. Log: `the bootstrap aborted with its own message, as intended`.

## Die Paketfreigabe, protokolliert

Der Plan beginnt mit einem blockierenden Checkpoint, weil die Legitimitaetstabelle in `05-RESEARCH.md` fuer diese Phase leer ist und `phpunit/phpunit` damit als ungeprueft gilt. Die drei Punkte wurden vor der Freigabe gegen die Registry erhoben, nicht behauptet:

| Prueffrage | Befund am 03.09.2026 |
|-----------|----------------------|
| Quell-Repo | `github.com/sebastianbergmann/phpunit`, 20.048 Sterne |
| Downloads | 991.073.957 gesamt, 17.667.181 im Monat |
| Aktualitaet | 833 stabile Versionen seit 2012-09-18, zuletzt 13.3.2 am 2026-08-27 |

Der Owner hat daraufhin freigegeben, unter drei Bedingungen, die alle eingehalten sind: exakter Pin (`11.5.56`, kein Caret-Bereich), ausschliesslich `require-dev` mit Installation nur im CI-Job, und `composer.lock` im Repository. Dass nichts davon ins Release-Archiv gelangt, steht als `_comment` in `composer.json` und wird von Plan 05-18 nachgeprueft (T-05-63).

Der Bezug selbst lief in einem Wegwerf-Container auf `php:8.2-cli`, mit Signaturpruefung des Composer-Installers gegen `composer.github.io/installer.sig`. Kein npm, kein PyPI, kein crates.io, wie in `05-RESEARCH.md` festgestellt (T-05-SC).

## Abweichungen vom Plan

### 1. [Rule 3 - Blocker] `ExAppService` war final und liess sich nicht doppeln

- **Gefunden bei:** Task 3, beim Entwurf von `ProviderTest`
- **Problem:** `Provider` nimmt `ExAppService` beim konkreten Typ, und die Klasse war `final`. PHPUnit kann eine finale Klasse nicht doppeln, und eine typisierte Eigenschaft laesst sich auch per Reflection nicht mit einem Fremdobjekt belegen. Damit waren die Verhaltensweisen 4 und 5 nicht behauptbar: beide sind Aussagen ueber `Provider::search` bei einer kontrollierten Antwort des Dienstes.
- **Behebung:** Das Schluesselwort entfaellt, die Absicht bleibt als `@final`-Annotation im Klassenkommentar samt Begruendung. Kein Verhalten aendert sich, nichts im Repository erweitert die Klasse.
- **Geprueft:** Alle vier Laeufe nach der Aenderung gruen, `php -l` sauber.
- **Datei:** `php/lib/Service/ExAppService.php` (steht nicht in `files_modified` des Plans)
- **Commit:** 74b2437

### 2. [Rule 1 - Bug] Der Vorgabepfad des Bootstraps ging eine Ebene zu hoch

- **Gefunden bei:** Task 2, im ersten CI-Lauf
- **Problem:** Der Job VERSCHIEBT `php` nach `apps/findling`, legt es nicht hinein. Das Bootstrap landet also unter `apps/findling/tests/`, drei Ebenen unter dem Serverstamm, und der Vorgabewert rechnete mit vier.
- **Behebung:** `dirname(__DIR__, 3)`. Der Fehler wurde durch den eigenen Waechter sichtbar und nicht durch einen Klassennicht-gefunden-Fehler, was genau der Zweck des Waechters ist.
- **Commit:** 070bdf1

### 3. [Rule 1 - Bug] Zwei Kommentare waren durch diese Arbeit sachlich falsch geworden

- **Gefunden bei:** Abschluss von Task 3
- **Problem:** Der Kommentar am `lint`-Job behauptete weiterhin, die PHP-Haelfte habe keinen Unit-Test, und nannte "nine behaviours", wo die Liste zwoelf fuehrt. `docs/testing.md` fuehrte alle zwoelf Punkte unveraendert als ungetestet und beschrieb den Job im Konjunktiv.
- **Behebung:** Beide nachgezogen. Die Liste der zwoelf bleibt vollstaendig stehen und bekommt eine Zustandsangabe darueber, welche sechs Tests haben; eine Spezifikation, die beim Umsetzen schrumpft, kann die Umsetzung hinterher nicht mehr pruefen.
- **Dateien:** `.github/workflows/php.yml`, `docs/testing.md`
- **Commit:** a6c53d0

**Gesamt:** 3 Abweichungen, alle automatisch behoben (1 Blocker, 2 Bugs). **Auswirkung:** keine auf das Verhalten der App. Die einzige Produktionsaenderung ist der entfallene `final`-Modifikator.

## Deferred Items

**DI-05-17:** Die Suite laeuft nur gegen `stable34`, waehrend die uebrigen Gates eine Matrix ueber 32, 33, 34 und 35 fahren. Grund ist die Bindung der PHPUnit-Hauptversion an den Serverzweig (`^11.5` auf stable34, `^10.5.35` auf stable32). Eine Matrix hiesse vier PHPUnit-Versionen und vier Lockdateien, also eine Entscheidung ueber die Bezugsdisziplin und keine Zeile. Adressiert an Plan 05-16 oder den Phase-Review.

## Was diese Suite nicht kann, ausdruecklich

Sie laeuft ohne Datenbank, Dateisystem und Netz, und das ist ihre Staerke und ihre Grenze zugleich. Kein Test hier beruehrt eine echte Berechtigung, einen echten Knoten oder eine echte Containerantwort: was geprueft wird, ist die Logik zwischen den Schnittstellen. Dass die Kette als Ganzes haelt, bleibt Sache der Integrationsjobs und des Paritaetstests aus 05-09. Waehrend der Arbeit ist kein Fall aufgetreten, der mehr als Mocks gebraucht haette.

Punkt 9 der Liste bleibt auch nach Plan 05-16 ohne Unit-Test, wie `docs/testing.md` schon feststellt: er braucht eine zweite registrierte ExApp.

## Threat Flags

Keine. Der Plan fuegt keine Netzroute, keinen Auth-Pfad und keine Schemaaenderung hinzu. Die drei Bedrohungen des Registers sind adressiert: T-05-62 durch Owner-Freigabe, exakten Pin und `composer.lock`; T-05-63 durch die Trennung von `require-dev` und die Zusage im `_comment`, die 05-18 prueft; T-05-64 durch `failOnEmptyTestSuite`, den Antivakuitaetstest, die Untergrenze der Testzahl im Job und die einmal rot gesehene Suite.

## Known Stubs

Keine.

## Naechster Schritt

Bereit fuer Plan 05-16: die Verhaltensweisen 7 bis 12 haengen an demselben Geruest, und die Untergrenze `MINIMUM_TESTS` im Job ist die Stelle, die dabei mitwaechst.

## Self-Check: PASSED

Sieben angelegte Dateien liegen auf der Platte, fuenf Commits sind in der Historie
(310bf97, 070bdf1, 74b2437, a6c53d0, 07ca35a), der Wegwerf-Zweig der Rotprobe ist
lokal und auf `origin` verschwunden, der `require`-Block von `php/composer.json`
ist gegenueber dem Ausgangsstand unveraendert (der Diff zeigt nur `_comment`,
`require-dev` und `autoload-dev`), und weder `STATE.md` noch `ROADMAP.md` wurden
angefasst. Letzter Workflow-Lauf 33773350793: gruen, 43 Tests.
