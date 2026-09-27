---
phase: 18-schema-marken-und-umbauweg
plan: 11
subsystem: php-companion
tags: [migration, lockstep, appconfig, upgrade, LEX-04]

# Dependency graph
requires:
  - phase: 16-messung-und-lockstep
    provides: "Version001200Date20260921000000.php als vollstaendige Kopiervorlage samt Unittest, und der Klassenkommentar, der jeden weiteren Minor-Schritt zu dieser Migration verpflichtet"
  - phase: 11-lockstep-und-drift
    provides: "ExAppService::KEY_BACKEND_VERSION, driftOnRecord() und der gemessene Beleg des Sprungs 1.0.3 auf 1.1.0 mit dreissig leeren Canary-Suchen"
provides:
  - "php/lib/Migration/Version001300Date20260924000000.php: Lockstep-Migration des Minor-Sprungs 1.2.0 auf 1.3.0, verwirft den aufgezeichneten Backend-Stand und schreibt keinen neuen"
  - "php/tests/Unit/Version001300Date20260924000000Test.php: sechs Faelle, darunter Zweitlauf und Konstruktorprobe gegen jeden Containerkontakt"
  - "Ratsche: PHP-Baumhash 15e00b2b bei 68 Dateien"
affects: [23-release]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Lockstep-Migration je Minor-Sprung wird kopiert und nicht neu gedacht: Name, Datum und die beiden Versionsnummern des Kommentars sind die einzigen Stellen, an denen sie sich unterscheiden darf"
    - "Der Klassenkommentar einer Migration ist der Ort, an dem ein teurer Lauf ausdruecklich anderswo verortet wird, weil der naechste Leser dieser Datei genau dort ueber die Idee stolpert"

key-files:
  created:
    - php/lib/Migration/Version001300Date20260924000000.php
    - php/tests/Unit/Version001300Date20260924000000Test.php
  modified:
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Das Datum im Datei- und Klassennamen ist 20260924 und nicht das im Frontmatter vorgeschlagene 20260925: der Kontextabschnitt des Plans verlangt das tatsaechliche Anlegedatum, und beide Vorgaenger halten es so"
  - "Der Rumpf ist Zeile fuer Zeile der des Vorgaengers, inklusive des Docblocks von postSchemaChange; der Diff gegen die Vorlage besteht aus dem Klassennamen, zwei Versionspaaren des Kommentars und dem neuen vierten Absatz"
  - "Die Testdaten wandern von '1.1.0' auf '1.2.0' mit, weil das die Zahl ist, die eine Bestandsinstallation vor diesem Update aufgezeichnet hat"
  - "Die Versionsnummern in beiden info.xml bleiben unberuehrt; der Bump auf 1.3.0 gehoert in die Release-Phase, die Migration liegt vorher bereit"

patterns-established:
  - "Zwei ankommende Dateien in der PHP-Haelfte bekommen einen Absatz der Kommentarkette, der beide Dateinamen nennt und ausdruecklich sagt, dass keine andere Datei ihre Bytes bewegt hat"

requirements-completed: [LEX-04]

# Metrics
duration: ~35min
completed: 2026-09-24
---

# Phase 18 Plan 11: Die Lockstep-Migration des Minor-Sprungs Summary

**Zehn Zeilen, die beim Upgrade auf 1.3.0 den aufgezeichneten Backend-Stand verwerfen statt ihn zu raten, als zeichengleich benannte Kopie des 1.2.0-Musters mit einem vierten Kommentarabsatz, der den ein- bis dreistuendigen Indexumbau ausdruecklich in den Container und nicht in `occ upgrade` verortet.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-09-24
- **Tasks:** 2, je ein atomarer Commit
- **Files created:** 2, **modified:** 1

## Accomplishments

- **Die Migration steht als echte Kopie.** `diff -u` gegen `Version001200Date20260921000000.php` zeigt genau vier Stellen: die Ueberschriftszeile (1.1.0 auf 1.2.0 wird 1.2.0 auf 1.3.0), das Versionspaar im zweiten Absatz, der Verweis auf die Migration des vorigen Minors (11.09.2026 wird 21.09.2026) und die Klassenzeile. Der Rumpf, also Konstruktor, Docblock und `postSchemaChange`, ist byteweise derselbe.
- **Die drei Absaetze der Bauart sind woertlich mitgewandert.** Dass jeder Minor-Schritt eine Migration dieser Form braucht, solange der aufgezeichnete Stand so gefuehrt wird wie heute; dass von dieser Migration nichts vom Container verlangt wird, weil sie im Wartungsmodus ohne angemeldeten Nutzer laeuft und AppAPI den Container gerade neu starten koennte; und dass Datei- und Klassenname zeichengleich sein muessen, weil Nextcloud Migrationen nach Dateinamen laedt und ein Unterschied bedeutet, dass die Migration stillschweigend nie ausgefuehrt wird.
- **Der vierte Absatz ist der Grund, warum dieser Plan ueberhaupt einen Kommentar schreibt.** Er sagt, dass 1.3.0 seinen Index mit einer Textanalyse schreibt, die 1.2.0 nicht hatte, dass ein bestehender Index deshalb einmal durchlaufen werden muss, dass dieser Lauf auf der Zielhardware ein bis drei Stunden dauert, und dass er genau deshalb nicht hier liegt: im Wartungsmodus waere das ein Nachmittag Ausfall fuer jemanden, der ein Update einer Suchapp geklickt hat. Der Umbau laeuft im Container als Lifespan-Aufgabe, und die Suche antwortet waehrenddessen aus dem Index, der schon da ist.
- **Sechs Testfaelle, dieselben wie beim Vorgaenger.** Aufgezeichneter Stand wird verworfen (mit dem Schluessel aus `ExAppService` per Reflection statt als kopiertem String), leerer Stand bleibt unangetastet und meldet genau eine Zeile, `setValueString` wird in keinem der beiden Zustaende gerufen, die verworfene Zahl steht in der Ausgabe, ein zweiter Lauf nimmt den No-op-Zweig und faellt nicht um, und der Konstruktor hat genau einen Parameter vom Typ `IAppConfig`, also nichts, was den Container erreichen koennte. Die `schemaClosure()` der Vorlage faellt weiterhin laut durch, falls jemand hier spaeter doch das Schema anfasst.
- **PHP-Ratsche von 66 auf 68 bewegt,** neuer Baumhash `15e00b2b37e003ff98b0cc3ca87affdea215eb160c1671153f9e616bf9cf70eb`, gemessen mit dem unveraenderten Rezept `40b-baumhash.py` ueber `php` mit `**/*.php`. Der neue Absatz der Kommentarkette nennt beide ankommenden Dateien, sagt, dass keine ging, und dass keine andere Datei der Haelfte ihre Bytes bewegt hat.
- **Volle Suite 2712 passed / 15 skipped, alle vier Gates gruen** (ruff check, ruff format --check, pyright mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, vulture).

## Task Commits

1. **Task 1: die Lockstep-Migration des Minor-Sprungs auf 1.3.0** - `2526819` (feat)
2. **Task 2: die sechs Faelle des Unittests und die PHP-Ratsche auf 68** - `a321b7a` (test)

## Files Created/Modified

- `php/lib/Migration/Version001300Date20260924000000.php` (neu, 111 Zeilen) - Kopie der Vorlage; `postSchemaChange` liest `backend_app_version`, meldet bei leerem Wert `no recorded backend version to drop` und kehrt zurueck, sonst `deleteKey` und die verworfene Zahl in der Ausgabe.
- `php/tests/Unit/Version001300Date20260924000000Test.php` (neu, 158 Zeilen) - dieselben sechs Faelle wie beim Vorgaenger, auf die neue Klasse und auf `1.2.0` als aufgezeichnete Zahl umgestellt.
- `backend/tests/test_measurement_scripts.py` - vierzehnter Absatz der PHP-Kommentarkette, `PHP_FILES_TODAY` 66 auf 68, `PHP_TREE_HASH_TODAY` neu.

## Decisions Made

- **Das Datum im Namen ist der 24.09.2026.** Der Kontextabschnitt des Plans sagt ausdruecklich, dass der Name im Frontmatter ein Vorschlag ist und das Datum beim Anlegen auf das tatsaechliche Datum gesetzt wird. Beide Vorgaenger halten es so (die Migration vom 11.09. traegt `Date20260911`, die vom 21.09. traegt `Date20260921`), und der einzige Zwang, den Nextcloud kennt, ist die Ordnung: `Version001300Date20260924000000` sortiert hinter `Version001200Date20260921000000`, also laeuft sie nach ihr.
- **Der Docblock von `postSchemaChange` bleibt unveraendert,** obwohl er die Migrationen vom 04.09. und vom 11.09. nennt und nicht die vom 21.09. Beide Saetze sind weiterhin wahr, und der Plan verlangt einen Rumpf, der Zeile fuer Zeile derselbe ist; eine Umschreibung haette den Nachweis "nur Name und Datum unterscheiden sich" zerstoert, um nichts zu gewinnen.
- **Die Zahl in den Testdaten wandert mit.** Der Vorgaenger prueft mit `'1.1.0'`, weil das die Zahl war, die eine Instanz vor dem Sprung auf 1.2.0 aufgezeichnet hatte. Hier ist es `'1.2.0'`. Die Faelle bleiben inhaltlich dieselben; nur die Zahl, die eine Bestandsinstallation wirklich in `appconfig` stehen hat, ist eine andere.
- **Kein Versionsbump.** `php/appinfo/info.xml` und `backend/appinfo/info.xml` sind unberuehrt, wie der Plan es verlangt: die Migration liegt bereit und laeuft erst, wenn die Version sie in der Release-Phase erreicht.
- **`.github/workflows/deploy-harp.yml` wurde nicht angefasst** (Plan 18-12 laeuft parallel darauf); `git diff --stat` gegen die Basis zeigt genau drei Dateien.

## Deviations from Plan

### Auto-fixed Issues

Keine. Es gab keinen Rule-1-, Rule-2- oder Rule-3-Eingriff.

### Benannte Abweichung

**1. Dateiname traegt 20260924 statt 20260925**
- **Gefunden bei:** Task 1, beim Anlegen der Datei
- **Sachverhalt:** Das Frontmatter und die `must_haves.artifacts` des Plans nennen `Version001300Date20260925000000`; der Kontextabschnitt desselben Plans sagt, der Name sei ein Vorschlag und das Datum werde beim Anlegen auf das tatsaechliche Datum gesetzt. Ausgefuehrt wurde am 24.09.2026.
- **Entscheidung:** Der Kontextabschnitt gewinnt, weil er die spezifischere Anweisung ist und weil beide Vorgaengermigrationen das Anlegedatum tragen. Ein in der Zukunft liegendes Datum im Namen waere zudem eine Angabe, die kein Ereignis belegt.
- **Folge:** Die Pfade der `must_haves`-Artefakte lauten faktisch `php/lib/Migration/Version001300Date20260924000000.php` und `php/tests/Unit/Version001300Date20260924000000Test.php`. Sonst aendert sich nichts: Datei- und Klassenname sind zeichengleich, die Sortierung hinter der Migration vom 21.09.2026 stimmt, und der Test belegt die Zeichengleichheit ueber `ReflectionClass` auf genau diesen Klassennamen.
- **Commits:** `2526819`, `a321b7a`

## Threat Model Umsetzung

| Threat ID | Umsetzung |
|-----------|-----------|
| T-18-11-01 (Migration wartet auf den Container) | Der Rumpf ruft weder `adminGet` noch `proxyRequest`; der Konstruktor bekommt genau einen Parameter, `IAppConfig`, und `testTheMigrationAsksTheContainerForNothing` prueft Anzahl und Typ per Reflection. |
| T-18-11-02 (Migration laeuft nie, weil der Name abweicht) | Datei- und Klassenname sind zeichengleich; `#[CoversClass]` und die Reflection im Test wuerden bei einer Abweichung sofort fallen. Der Absatz dazu ist woertlich mitgewandert. |
| T-18-11-03 (Doppellauf verwirft einen frischen Wert) | `testASecondRunDropsNothingAndThrowsNothing`: zweite Lesung ist der leere String, `deleteKey` genau einmal, `info` genau zweimal, keine Ausnahme. |
| T-18-11-04 (Umbau in der Migration) | Ausdruecklich nicht hier, festgehalten im vierten Absatz des Klassenkommentars samt der Begruendung (ein bis drei Stunden im Wartungsmodus). |
| T-18-11-SC (Paketinstallation) | Kein Paket beruehrt, `composer.json` und `composer.lock` unveraendert. |

## Verification

- `cd backend && uv run python -m pytest -q tests/test_lockstep_versions.py tests/test_ops_scripts.py` - **93 passed**
- `cd backend && uv run python -m pytest -q tests/test_measurement_scripts.py` - **376 passed**
- `cd backend && uv run python -m pytest -q` - **2712 passed, 15 skipped**
- `uv run ruff check` - All checks passed
- `uv run ruff format --check` - 133 files already formatted
- `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright` - 0 errors, 0 warnings
- `uv run vulture` - keine Befunde
- `python docs/measurements/2026-09-vergleichsmessung-m7g/skripte/40b-baumhash.py php "**/*.php"` - `dateien: 68`, `baumhash: 15e00b2b...`
- Beide `info.xml` unveraendert, `deploy-harp.yml` unveraendert (`git diff --stat` gegen die Basis: drei Dateien)
- Beide neuen Dateien sind reines ASCII (`file` meldet "ASCII text"), also keine Em-Dashes und keine Umlaute im Code

## Known Stubs

Keine.

## Hinweis fuer die Release-Phase

Die Migration verwirft den aufgezeichneten Stand, sobald `occ upgrade` sie erreicht, und das passiert erst mit dem Versionsbump auf 1.3.0. Wer den Bump setzt, ohne diese Datei mitzuliefern, bekommt genau den gemessenen Zustand des Sprungs 1.0.3 auf 1.1.0 zurueck: jede Suche leer, bis jemand die Einstellungsseite oeffnet.

## Self-Check: PASSED

Beide neuen Dateien und die SUMMARY existieren am Baum, beide Task-Commits stehen im Log (2526819, a321b7a), keine Em-Dashes in dieser Datei.
