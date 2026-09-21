---
phase: 16-haertung-und-store-einreichung-v1-2-0
plan: 07
subsystem: release-mechanik
tags: [rel-02, versionsbump, migration, di-11-06, baumhash, lockstep]

# Dependency graph
requires:
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: Version001100Date20260911000000 als Vorlage samt der fuenf Regeln in ihrem Klassenkommentar
  - phase: 16-haertung-und-store-einreichung-v1-2-0
    provides: der dokumentierte Entscheid zu DI-11-06 aus Plan 16-04 (weitergereicht, Kehrseite ist der Migrationszwang je Minor-Sprung)
provides:
  - die drei Versionsstellen sagen 1.2.0, in einem Commit
  - php/lib/Migration/Version001200Date20260921000000.php, die Migration des Minor-Sprungs
  - php/tests/Unit/Version001200Date20260921000000Test.php mit sechs Faellen
  - PHP_FILES_TODAY 66 und der nachgezogene PHP_TREE_HASH_TODAY
affects: [16-09-upgrade-beweis, 16-11-store-texte, 16-14-abgabe]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Der Dateiname und der Klassenname einer Nextcloud-Migration sind zeichengleich; ein Gate im verify prueft class <Dateiname> im Text der Datei, weil eine Abweichung die Migration still nie ausfuehrt"
    - "Die Migration verwirft die veraltete Versionsmarke und schreibt keine an ihre Stelle; die Zeichenkette ownVersion kommt in der Datei nicht vor, und das ist pruefbar"
    - "Neue .php-Dateien heben PHP_FILES_TODAY und PHP_TREE_HASH_TODAY im selben Commit; die historischen Zwillinge PHP_FILES und PHP_TREE_HASH bleiben unberuehrt"
    - "Das Lockstep-Gate nennt bewusst keine Versionszahl, damit es nicht die erste Datei ist, die jemand beim Bump bearbeitet; es musste fuer diesen Bump nicht angefasst werden"

key-files:
  created:
    - php/lib/Migration/Version001200Date20260921000000.php
    - php/tests/Unit/Version001200Date20260921000000Test.php
  modified:
    - php/appinfo/info.xml
    - backend/appinfo/info.xml
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Der Datumsteil des Namens ist 20260921 und nicht der Arbeitsname 20260922 aus der Dateiliste des Plans. Der Plan schreibt den Tag der Entstehung vor und nennt seinen eigenen Eintrag ausdruecklich einen Arbeitsnamen; die Datei entstand am 21.09.2026"
  - "Der Klassenkommentar ist fortgeschrieben und nicht kopiert: er nennt den Minor-Sprung 1.1.0 auf 1.2.0, den gemessenen Beleg aus dem Upgrade-Beweis von 11-11 und den Satz, dass jeder Minor-Sprung eine Migration braucht, solange die Marke so gepflegt wird, mit Verweis auf DI-11-06 und den Entscheid aus 16-04"
  - "Die Zeichenkette ownVersion kommt weder in der Migration noch in ihrem Test vor. Der Sachverhalt wird in Prosa als die Version dieser Haelfte benannt, damit die Pruefung des Plans nicht an einem Kommentar scheitert und trotzdem gesagt ist, was gemeint ist"
  - "Der Test hat sechs Faelle statt der vier der Vorlage. Die zwei zusaetzlichen sind die, die der Plan als Eigenschaften verlangt: ein zweiter Lauf ist ein no-op und wirft nicht, und der Konstruktor bekam nichts, womit er den Container fragen koennte"
  - "Der Nachweis, dass der Container nicht gefragt wird, sitzt auf dem Konstruktor und nicht auf einem Aufrufzaehler. Eine Migration kann den Container nur ueber einen Mitarbeiter erreichen, den sie hereingereicht bekommt; ein Konstruktor mit genau einem Parameter vom Typ IAppConfig ist die Aussage selbst und nicht ihr Schatten"
  - "Die Kommentare der info.xml, die die frueheren Spruenge erzaehlen, bleiben unberuehrt. Der Plan sagt zu Task 2 Sonst nichts, und die Texte beider Dateien gehoeren Plan 16-11"

patterns-established:
  - "Eine Migration je Minor-Sprung ist ab jetzt eine Kette mit zwei Gliedern; die Vorlage steht nicht mehr allein da, und der neue Klassenkommentar verweist namentlich auf die Vorgaengerin"

requirements-completed: []
requirements-partial:
  - "REL-02: der Bump und die Migration stehen. Offen bleiben der Upgrade-Beweis (16-09), die Messzahl im Gleichschritt (16-10/16-11), der Tag und die zweimal HTTP 201 (16-14)"

# Metrics
duration: 30 min
completed: 2026-09-21
---

# Phase 16 Plan 07: Versionsbump 1.2.0 und die Migration des Minor-Sprungs Summary

Die drei Versionsstellen sagen 1.2.0, und der Sprung bringt seine Migration mit: `Version001200Date20260921000000` verwirft die veraltete Versionsmarke des Containers in `postSchemaChange`, schreibt bewusst keine an ihre Stelle, überlebt einen zweiten Lauf als no-op und bekam nichts hereingereicht, womit sie den Container fragen könnte.

## Was gebaut wurde

**Die Migration.** `php/lib/Migration/Version001200Date20260921000000.php` folgt der Vorlage `Version001100Date20260911000000.php` in allen fünf Regeln ihres Klassenkommentars: sie sitzt in `postSchemaChange`, weil sie Daten und keine Tabelle anfasst; sie liest `ExAppService::KEY_BACKEND_VERSION` über `IAppConfig` und löscht den Schlüssel; ein fehlender Schlüssel ist ein no-op mit `$output->info` und kein Wurf; sie fragt den Container nicht; und ihr Dateiname ist mit ihrem Klassennamen zeichengleich.

Der Klassenkommentar ist fortgeschrieben, nicht kopiert. Er nennt den Minor-Sprung 1.1.0 auf 1.2.0 als Anlass, zitiert den gemessenen Beleg aus dem Upgrade-Beweis von Plan 11-11 (dreißig Kanariensuchen leer, `companion 1.1.0, backend 1.0.3` im Protokoll), und er trägt den Satz weiter, dass **jeder** Minor-Sprung eine Migration dieser Form braucht, solange die Versionsmarke so gepflegt wird wie heute. Dieser Satz steht dort mit Verweis auf DI-11-06 und auf den Entscheid aus Plan 16-04: der Punkt ist mit Verdikt und Zieladresse weitergereicht, und genau das ist es, was diese Datei zur Pflicht macht.

**Der Test.** `php/tests/Unit/Version001200Date20260921000000Test.php` hat sechs Fälle: die Marke wird gelöscht, eine fehlende Marke ist ein no-op mit Meldung, es wird nie eine eigene Version geschrieben, die verworfene Zahl steht in der Meldung, ein zweiter Lauf löscht nichts und wirft nichts, und der Konstruktor hat genau einen Parameter vom Typ `IAppConfig`. Der Schlüssel wird wie in der Vorlage per Reflexion aus `ExAppService` gelesen statt abgeschrieben, damit eine Umbenennung der Konstanten einen Test bricht und nicht still gegen eine Zeichenkette besteht, die niemand mehr schreibt.

**Der Bump.** `php/appinfo/info.xml` `<version>`, `backend/appinfo/info.xml` `<version>` und das `<image-tag>` daneben stehen auf `1.2.0`, in einem Commit. `min-version 33` und `max-version 35` sind unberührt (HART-03), keine Matrix hat sich bewegt, und `backend/tests/test_lockstep_versions.py` ist unverändert: das Gate nennt weiterhin keine Zahl und musste für diesen Bump nicht angefasst werden.

**Der Nachzug.** `PHP_FILES_TODAY` geht von 64 auf 66 und `PHP_TREE_HASH_TODAY` auf `7942f09f3c1f905b3a0a6c7fa4abbdfa90378a037adfc978f7b38c3e59f9ec41`, gerechnet mit der bestehenden Rezeptur `40b-baumhash.py` über `php` und `**/*.php`. Die Kommentarkette hat ihren Eintrag in der Form der bestehenden: Datum, Plan, die Zahl bewegt sich zum ersten Mal seit dem 11.09.2026 wieder, um zwei, und beide Dateinamen stehen dort. Die historischen Zwillinge `PHP_FILES` (58) und `PHP_TREE_HASH` bleiben unberührt.

## Verifikation

| Was | Befehl | Ergebnis |
|---|---|---|
| Name und Rumpf der Migration | das Python-Gate aus Task 1 | `name und rumpf ok` |
| Genau eine Migration, genau ein Test | `ls ... grep -c "Version001200Date"` | 1 und 1 |
| Versionsstellen | `grep -c "1.2.0"` je Datei | php 1, backend 2 |
| Lockstep | `uv run pytest tests/test_lockstep_versions.py -q` | 23 bestanden |
| Baumhash und Zaehlung | `uv run pytest tests/test_measurement_scripts.py -q` | 376 bestanden |
| ruff | `uv run ruff check tests` | sauber |
| ruff format | `uv run ruff format --check tests` | 70 Dateien formatiert |
| pyright | `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright` | 0 errors, 0 warnings |
| vulture | `uv run vulture src tests --min-confidence 80` | sauber |
| volle Suite | `uv run pytest -q` | **2469 bestanden / 15 uebersprungen**, unveraendert gegen den Stand nach 16-06 |

Die volle Suite lief zweimal grün: einmal vor dem Commit der PHP-Dateien und der Konstanten, einmal nach dem Bump der drei Versionsstellen.

## Abweichungen vom Plan

### 1. Der Datumsteil des Namens ist 20260921, nicht 20260922

**Gefunden bei:** Task 1.
**Sachverhalt:** Die Dateiliste des Plans trägt `Version001200Date20260922000000.php`. Der Plan nennt diesen Eintrag selbst einen Arbeitsnamen und schreibt vor, dass der Tag der Entstehung gilt und die SUMMARY den tatsächlichen Namen nennt.
**Folge:** Die Dateien heißen `Version001200Date20260921000000.php` und `Version001200Date20260921000000Test.php`. Kein Ratschluss, sondern die ausdrückliche Vorgabe des Plans.

### 2. Die Reihenfolge der Commits ist 1+3, dann 2

**Gefunden bei:** dem Schnitt der Commits.
**Sachverhalt:** Task 3 verlangt in seinem Abnahmekriterium, dass `git show --stat` Migration, Test und Konstanten im **selben** Commit zeigt. Ein eigener Commit je Task wäre ein Zwischenstand mit rotem Messgate, also ein Commit, den niemand fahren kann. Dieselbe Begründung steht schon in 16-06.
**Folge:** Zwei Commits statt drei. `12e8663` trägt Task 1 und Task 3, `734a1b2` trägt Task 2. Der Bump berührt keine `.php`-Datei, also bewegt er den Baumhash nicht und darf allein stehen.

### 3. Die Zeichenkette ownVersion kommt auch im Test nicht vor

**Gefunden bei:** Task 1.
**Sachverhalt:** Das Gate des Plans prüft nur die Migration. Der Klassenkommentar der Vorlage benutzt den Namen der Methode jedoch mehrfach in Prosa, und ein Kopieren hätte das Gate gerissen.
**Folge:** Beide neuen Dateien benennen den Sachverhalt als "die Version dieser Hälfte" statt mit dem Methodennamen. Der Kommentar sagt weiterhin, was gemeint ist, und die Prüfung bleibt eine Prüfung und keine Falle.

## Was offen bleibt

**Der PHP-Teil ist nur statisch geprüft.** Auf dieser Maschine läuft kein PHP; es gibt kein `php -l` und kein PHPUnit hier. Die Migration und ihre sechs Fälle laufen zum ersten Mal wirklich im Job `phpunit` von `.github/workflows/php.yml`, und der läuft beim nächsten Push. **Eine Laufnummer kann diese SUMMARY deshalb nicht nennen**, weil der Auftrag ausdrücklich nicht pusht. Der nächste Plan, der pusht, trägt sie nach. Geprüft wurde stattdessen: die Zeichengleichheit von Datei- und Klassenname maschinell, die Abwesenheit von `ownVersion` maschinell, und die Bauform gegen die Vorlage Zeile für Zeile. Das Werkzeug `willReturnOnConsecutiveCalls` ist in diesem Repositorium bereits mit PHPUnit 11.5.56 in Gebrauch (`CrawlAdvanceServiceTest.php`), also kein neues Risiko.

**Die Kommentare der info.xml erzählen den Sprung auf 1.2.0 noch nicht.** Beide Dateien führen eine Erzählung der früheren Sprünge, und sie endet bei 1.1.0. Der Plan sagt zu Task 2 ausdrücklich "Sonst nichts", und die Texte beider Dateien gehören geschlossen zu Plan 16-11. Dort gehört der Absatz hin, nicht hierher.

## Known Stubs

Keine. Beide neuen Dateien sind vollständig ausgeführt, kein Platzhalter, kein leerer Rückgabewert.

## Threat Flags

Keine. Dieser Plan fügt keine Netzoberfläche, keinen Pfad und kein Schema hinzu; die vier Bedrohungen des Plans (T-16-24 bis T-16-27) sind je mit einem Gate oder einem Fall belegt.

## Self-Check: PASSED

Zwei Commits vorhanden (`12e8663`, `734a1b2`), die zwei neuen und die drei geaenderten Dateien vorhanden, alle verify-Befehle der drei Tasks gruen, volle Suite 2469 bestanden / 15 uebersprungen.
