---
phase: 33-ausschlussmuster-und-admin-feinschliff
plan: 02
subsystem: exclusions
tags: [exclusions, patterns, matcher, redos, gate-d, phpunit, difference-test]
requires:
  - "33-01: Owner-Antworten G1 bis G4 (32 x 60, ? nie über /, Groß/Klein zählt, no_wildcard abgelehnt)"
provides:
  - "ExclusionService: patterns(), validatePatterns(), savePatterns(), newPatterns(), hasRules(), bitparalleler Matcher, isExcluded über beide Listen"
  - "SettingsService::KEY_EXCLUSION_PATTERNS = 'exclusion_patterns'"
  - "backend/tests/drivers/exclusion_driver.php: wiederverwendbarer php:8.3-cli-Treiber (Modi answers und timing) für 33-11"
  - "Differenztest gegen die v1.4.2-Fixture und Laufzeitreihe (backend/tests/test_exclusion_driver.py)"
affects: [33-03, 33-04, 33-05, 33-09, 33-11]
tech-stack:
  added: []
  patterns:
    - "Shift-And mit Stern-Selbstschleifen, Kompilat je Request, Pfad einmal je Aufruf zerlegt"
    - "Gate D methodengenau: Körper von matchesAPattern und normalisePattern ohne fnmatch(, preg_, explode("
    - "Byte-gleiche Fixture eines alten Release-Stands außerhalb von php/, mit -text und Blob-Prüfung"
key-files:
  created:
    - php/tests/Unit/ExclusionServiceTest.php
    - php/tests/Unit/FileEventListenerTest.php
    - backend/tests/drivers/exclusion_driver.php
    - backend/tests/fixtures/exclusion_v1_4_2/ExclusionService.php
    - backend/tests/fixtures/exclusion_v1_4_2/PROVENANCE.md
    - backend/tests/test_exclusion_driver.py
  modified:
    - php/lib/Service/ExclusionService.php
    - php/lib/Service/SettingsService.php
    - php/lib/Listener/FileEventListener.php
    - php/lib/Service/QueueService.php
    - php/lib/Controller/ReconcileController.php
    - php/tests/Unit/QueueServiceReaderTest.php
    - php/tests/Unit/ReconcileControllerTest.php
    - backend/tests/test_exclusion_path_space.py
    - backend/tests/test_measurement_scripts.py
    - backend/pyproject.toml
    - .gitattributes
decisions:
  - "33-02: Muster stehen im eigenen appconfig-Schlüssel exclusion_patterns; Präfixcode von 1.4.2 byte-gleich, gegen die v1.4.2-Fixture verglichen"
  - "33-02: Ein Muster ohne Literal nach Abzug von *, ? und / ist no_literal (so fallen *, */* und ?* darunter)"
  - "33-02: Eine Negation wird nach dem Falten der Schrägstriche geprüft (führendes ! des normalisierten Musters); ungültiges UTF-8 bekommt unsupported_character"
  - "33-02: Der describe()-Fall 'nur Muster' steht in QueueServiceReaderTest.php, weil describe() dort über claim() geprüft wird"
metrics:
  duration: "ca. 2 h 30 min inkl. zweier voller Suiten und zweier CI-Runden"
  completed: 2026-10-13
  tasks: 3
  files: 17
---

# Phase 33 Plan 02: Ausschlussmuster im Kern Summary

Ausschlussmuster mit `*` und `?` im eigenen appconfig-Schlüssel `exclusion_patterns`, geprüft mit elf geschlossenen Codes und verglichen von einem bitparallelen Matcher ohne Regex, linear in der Pfadlänge; `isExcluded()` prüft erst die Präfixe von 1.4.2 unverändert und dann die Muster, `hasRules()` ersetzt die drei Präfix-Guards. Ein Differenztest gegen die byte-gleiche v1.4.2-Fixture belegt, dass die Präfixe unverändert wirken.

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | Muster lesen, prüfen, speichern und bitparallel vergleichen | 75f5f29e | ExclusionService.php, SettingsService.php, ExclusionServiceTest.php |
| 2 | hasRules an den drei Guards, Gate D erweitert, PHPUnit "nur Muster", Baumhash | 75f5f29e | FileEventListener.php, QueueService.php, ReconcileController.php, FileEventListenerTest.php, QueueServiceReaderTest.php, ReconcileControllerTest.php, test_exclusion_path_space.py, test_measurement_scripts.py |
| 3 | Treiber, Differenztest gegen v1.4.2 und Laufzeitreihe | 3c1d5a97 | exclusion_driver.php, Fixture, PROVENANCE.md, test_exclusion_driver.py, .gitattributes, pyproject.toml |

Task 1 und 2 laufen laut Plan in einem Commit.

## Dateien

Geändert oder neu (17): siehe `key-files` oben.

Geprüft, keine Änderung (die Mocks liefern schon je Schlüssel, keiner liest die Präfixliste als Musterliste):

- `php/tests/Unit/ProbeServiceTest.php` (`$this->values[$key]`)
- `php/tests/Unit/ProfileSettingsControllerTest.php` (`$this->values[$key]`)
- `php/tests/Unit/SettingsServiceTest.php` (`$this->values[$key]`)
- `php/tests/Unit/StorageCrawlJobTest.php` (nur `KEY_EXCLUSIONS` liefert `['Archiv']`, sonst Default)
- `php/tests/Unit/QueueServiceTest.php` (leeres gemocktes IAppConfig)

Von der `willReturnMap`-Vorgabe weicht die Form ab: alle neuen und erweiterten Mocks nutzen `willReturnCallback` je Schlüssel wie die Nachbartests, weil `willReturnMap` bei optionalen Parametern von `getValueArray` an der Argumentzahl hängt. Die Wirkung (je Schlüssel eine Antwort) ist dieselbe.

## Belege

**TDD Gate D (Task 2):** Nach dem Anlegen der Proben und Selbsttests liefen in `test_exclusion_path_space.py` 2 Fälle rot (`test_no_call_site_guards_on_the_prefixes_alone`, `test_exactly_the_three_known_call_sites_ask_has_rules`), 31 grün; nach dem Umstellen der Guards 33 grün. Die Probe (b) war schon grün, weil Task 1 vorher stand; Gegenprobe am echten File: `preg_match("#x#", $path)` temporär in `matchesAPattern` eingefügt, `test_the_pattern_half_holds_no_glob_no_regex_and_no_split` rot, Datei zurück. Der Selbsttest "preg_replace nur in trimmed()" meldet keinen Befund, die Selbsttests mit altem Guard, mit `preg_match(` im Matcher und ohne `ERROR_TRAVERSAL` melden je genau einen.

**PHPUnit (nur CI):** vorher 666 Tests (Lauf 38385967900, 4c481f74), nachher 743 Tests, 2649 Assertions (Lauf 38450953800, 75f5f29e). +77: ExclusionServiceTest 69, FileEventListenerTest 5, QueueServiceReaderTest 2, ReconcileControllerTest 1. Rot war vor Task 1 nur als Textprüfung belegbar (Aufruf unbekannter Methoden), der Matcher wurde zusätzlich vorab über den Treiber mit 22 Pfaden und alle elf Codes über ein Scratch-Skript auf php:8.3-cli geprüft.

Orte der "nur Muster"-Fälle: Listener in `FileEventListenerTest.php` (Datei unter `X.key/` nicht eingereiht, Kontrolldatei eingereiht, Löschung läuft durch, ohne Regeln keine Wurzelabfrage, Präfix wirkt weiter), `describe()` in `QueueServiceReaderTest.php` (Abholung unter `*.key` wird Löschauftrag, Kontrollpfad wird Inhaltsauftrag), Slice in `ReconcileControllerTest.php` (`testWithPatternsOnlyTheRowAPatternMatchesCarriesTheExcludedMark`).

**Differenztest (Task 3):** alter Stand aus der Fixture, neuer aus `php/lib`, gleicher Treiber; Korpus mit 89 Präfixeinträgen (19 schwierige vorne, darunter `a*b`, `x?y`, `Foto (2024)`, `files/Backups`, `//Doppelt//Pfad/`, `Groß`/`groß`/`GROSS`, NFD-`Café`, Steuerzeichen, `.`, `..`, `./Archiv`, `Archiv/../x`, `files`, 257 Bytes, `7`, `null`; dahinter 70 Füller, Deckel 64 greift) und 155 Pfaden. `prefixes()`, jede `isExcluded()`-Antwort und die Logzeilen beider Stände sind gleich, Musterliste leer. Positivkontrolle mit `*.key` im neuen Stand: genau ein Unterschied, `Vortrag.key/Data/x.jpg` (die Bündel-Datei unter `Archiv` war schon per Präfix aus).

Gegenprobe Differenztest: Präfixprüfung im neuen Stand temporär auf `if (str_starts_with($path, $prefix)) {` (per `sed` auf `isExcluded`), `pytest -k answer_exactly` rot ("At index 2 diff: True != False", Pfad `Archivx.pdf`), Datei zurück, `git diff --quiet -- php` sauber.

Herkunft: lokal grün (Tag vorhanden, `git show` byte-gleich, Commit 17363bb2); `git hash-object` der Fixture = `805c63392a4337a1845794106d5e831a92868f12`, kein CR, nach `rm` plus `git checkout --` erneut byte-gleich zu `git show v1.4.2:...` (`cmp`).

CI-Beleg aus dem python.yml-Log (Lauf 38456525959): `5663 passed, 148 skipped`; übersprungen aus der neuen Datei nur `tests/test_exclusion_driver.py:235: tag v1.4.2 not fetched` und `:365: timing series runs only with FINDLING_TIMING=1`. Differenztest, Positivkontrolle und Blob-Test liefen also und waren grün.

**Laufzeitreihe (lokal, php:8.3-cli in Docker, 50 Wiederholungen, 3 Pfade je Länge, Median je Aufruf):**

| Pfadlänge | gutartig (32 Muster) | feindlich (32 x 60 Zeichen) |
|---|---|---|
| 250 | 0,4539 ms | 0,4763 ms |
| 500 | 0,8030 ms | 0,8717 ms |
| 1000 | 1,5063 ms | 1,5470 ms |
| 2000 | 3,1581 ms | 3,3922 ms |
| 4000 | 6,0249 ms | 6,0955 ms |

t(4000)/t(1000): gutartig 4,00, feindlich 3,94 (Band 2,5 bis 6). Feindlicher Median bei 4000: 6,10 ms, unter 12,6 ms.

Gegenprobe Laufzeitreihe: je Zeichen temporär den ganzen Rest erneut durchlaufen (`foreach (array_slice($characters, $index) as $again)` vor dem Schritt). Der volle Test mit 50 Wiederholungen lief über 10 min in die Zeitgrenze und wurde abgebrochen; die Gegenprobe lief dann über denselben Treiber mit einer Wiederholung: 1000 Zeichen 279,6 ms, 4000 Zeichen 4456,4 ms, Quotient 15,94, außerhalb des Bands und über der Decke, also rot. Datei zurück, `git diff --quiet -- php` sauber.

## Treiber

`backend/tests/drivers/exclusion_driver.php`, Kopfkommentar mit Aufruf, Eingabe, Modi und Stubs. Stubs: `OCP\IAppConfig`, `OCP\BackgroundJob\IJobList`, `Psr\Log\LoggerInterface`, `OCA\Findling\AppInfo\Application`, `OCA\Findling\Service\SettingsService` (zwei Schlüsselkonstanten), `OCA\Findling\Service\StorageService` (jede Methode wirft). Weitere `use`-Ziele der Quelldatei (`BackgroundJobs\SubtreeExpandJob`, `Db\QueueMapper`) braucht weder Laden noch Bauen, sie sind nicht gestubbt. Konstruktor beider Stände gleich (IAppConfig, StorageService, IJobList, LoggerInterface). Kein Gate liest den Treiber oder die Fixture als Teil des PHP-Baums (der Baumhash liest nur `php/**/*.php`).

## CI

- 75f5f29e: PHP and store metadata gates 38450953800, Python gates 38450953681, Security scans 38450953942, OpenSSF Scorecard 38450953821, Resilience 38450953703, Integration 38450953853, HaRP deploy 38450953795, Multi-arch image 38450954092; alle grün (`gh run watch --exit-status`).
- 3c1d5a97: Python gates 38456525959, Security scans 38456525964, OpenSSF Scorecard 38456525876, Resilience 38456525880, Integration 38456525936, HaRP deploy 38456525926, Multi-arch image 38456526255; alle grün (`gh run watch --exit-status`; der HaRP-Lauf brauchte einen zweiten Watch-Aufruf, weil der erste in die lokale Zeitgrenze lief).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Marker `timing` registriert**
- **Gefunden in:** Task 3
- **Problem:** Der Plan verlangt einen Marker `timing`; ohne Registrierung warnt pytest bei jedem Lauf.
- **Fix:** `markers = ["timing: ..."]` in `backend/pyproject.toml` (`[tool.pytest.ini_options]`), Datei nicht in der Planliste. Berührt weder `backend/src` noch den Paket-Baumhash.
- **Commit:** 3c1d5a97

**2. SPDX-Köpfe**
- Die Nachbardateien (PHP-Tests, Python-Tests) tragen keinen SPDX-Kopf, die Lizenz kommt aus `REUSE.toml` (`path = "**"`). Treiber, Test und PHP-Tests folgen den Nachbarn; `PROVENANCE.md` trägt den verlangten SPDX-Kopf als HTML-Kommentar. `reuse lint` grün (2713/2713 vor Task 3, danach erneut grün).

**3. Mock-Form `willReturnCallback` statt `willReturnMap`** (siehe Abschnitt Dateien).

**4. Escapes im Python-Test**
- Beim Schreiben der Datei wurden die Escapes `ß` und `́` als Zeichen eingesetzt; vor dem Commit per Codepunkt wieder auf Escapes gesetzt. `LC_ALL=C grep -nP "[^\x09\x0A\x0D\x20-\x7E]"` über Test, Treiber, ExclusionServiceTest und ExclusionService leer.

## Known Stubs

Keine. `savePatterns()` plant noch keinen Kehrjob; das ist laut Plan Sache von 33-04 und im Docblock vermerkt. Die Formular-Route ruft `savePatterns()` erst ab 33-05.

## Threat Flags

Keine neue Fläche über das Threat Register hinaus. T-33-03 bis T-33-08 sind umgesetzt (Matcher linear und gemessen, `no_literal`, defensives Lesen mit Deckel und Zählern, Antworten nur mit Codes, Differenztest, `hasRules()` an drei Stellen).

## Self-Check: PASSED

- FOUND: ExclusionServiceTest.php, FileEventListenerTest.php, exclusion_driver.php, Fixture, PROVENANCE.md, test_exclusion_driver.py
- FOUND: 75f5f29e, 3c1d5a97
