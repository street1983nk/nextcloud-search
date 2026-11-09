---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 22
subsystem: php/Service, php/Controller, backend/tests
tags: [D-43-14, D-43-15, D-43-17, OE-1, OE-5, OE-6, doc-key, counting]
requires: [43-21]
provides: [DocKeyService::DOC_KEY_FORMAT, docKeyOf mit Freigabe-Identität, docKeysFor über shareIdentities, docKeyFormat im Auftrag, format in GET /reconcile/doc-keys, Format-2-Katalog doc_key_cases.json]
affects: [43-23, 43-24]
tech-stack:
  added: []
  patterns: [Dokumentschlüssel über Freigabe und Freigabe-Pfad mit NUL-Trennung, Formatmarke an jedem Übergang]
key-files:
  created:
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-22-SUMMARY.md
  modified:
    - php/lib/Service/DocKeyService.php
    - php/lib/Service/QueueService.php
    - php/lib/Controller/ReconcileController.php
    - php/tests/Unit/DocKeyServiceTest.php
    - php/tests/Unit/QueueServiceTest.php
    - php/tests/Unit/ReconcileControllerTest.php
    - backend/tests/fixtures/doc_key_cases.json
    - backend/tests/test_share_identity_cases.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Fehlt die Identitätsabfrage (shareIdentities wirft), scheitert docKeysFor als Ganzes statt Schlüssel ohne Freigabe auszugeben; der Auftrag reist dann ohne docKey, die Route antwortet 500 (beides schon vorhanden)"
  - "shareIdentities wird je Band nur gefragt, wenn das Band mindestens einen Eintrag außerhalb des Papierkorbs hat; Papierkorb- und fehlende Zeilen fragen keine Identität"
  - "Die Wurzel wird in docKeyOf nicht nachbearbeitet (kein trim), sie kommt schon normalisiert aus StorageService; der ganze Freigabe-Pfad wird in NFC gebracht"
metrics:
  started: 2026-11-09T11:35:00Z
  completed: 2026-11-09T12:25:00Z
  tasks: 2
  files: 9
---

# Phase 43 Plan 22: Dokumentschlüssel Format 2 über die Freigabe

Der Dokumentschlüssel ist jetzt sha256 über `'2' NUL Freigabe NUL Freigabe-Pfad` (Wurzel vor dem filecache-Pfad, NFC, ohne Groß-/Kleinfaltung); dieselbe Datei hat unter `//Daten`, `//Daten` mit Wurzel `/Projekte` und `//daten` einen Schlüssel, `Bericht.txt`/`bericht.txt`, zwei Freigaben und Einzelspeicher gegen Freigabe bleiben getrennt. Jeder Auftrag mit docKey trägt `docKeyFormat: 2`, `GET /reconcile/doc-keys` antwortet mit `format: 2`.

## Tasks

| Task | Inhalt | Commit |
|------|--------|--------|
| 1 | RED: 18 Format-2-Fälle (13 Format-1-Fälle als Geschichte), Python-Nachrechnung beider Formate, PHPUnit-Tests für Schlüssel, Auftrag, Route | 11850d86 |
| 2 | GREEN: DocKeyService Format 2 mit StorageService, docKeyFormat, format, PHP-Baumhash | c0e124c1 |

## Belege

- **RED lokal** (`scripts/dev/phpunit_docker.sh --filter 'DocKeyService|QueueService|ReconcileController|StorageService'`, freier RAM 4,2 GB): 114 Tests, 1 Error (DOC_KEY_FORMAT unbekannt), 19 Failures (13 DocKeyServiceTest, 3 QueueServiceTest, 3 ReconcileControllerTest). Ein erster Lauf hatte 9 Errors durch einen eigenen Fehler im Testumbau (Mock `$storageService` in einem anderen Helfer entfernt), vor dem RED-Commit behoben; gültig ist der zweite Lauf.
- **GREEN lokal** (RAM 4,3 GB): gleicher Filter 114 Tests, 1241 Assertions, OK. Volle Suite ohne Filter (RAM 4,2 GB): 1165 Tests, 7378 Assertions, OK (Boden 28).
- **Gegenprobe PHP (Negativkontrolle)**: docKeyOf mutiert (Freigabe aus dem Hash, Wurzel nicht vorangestellt, Pfad klein), Filter DocKeyService|QueueService|ReconcileController: 88 Tests, 10 Failures (9 DocKeyServiceTest, QueueServiceTest::testTheKeyOfAJobFollowsTheShareOfItsStorage). Datei danach wiederhergestellt (cmp identisch), erst dann committet.
- **Gegenprobe Python (Positivkontrolle)**: ein Format-2-Hash im Katalog um ein Zeichen verfälscht: 3 Failures (Nachrechnung, Relationen, benannte Fälle); Katalog danach unverändert (git diff leer).
- **Hashes von Hand**: alle elf verschiedenen Format-2-Werte per `printf '2\000%s\000%s' '<Freigabe>' '<Freigabe-Pfad>' | sha256sum` gerechnet, Befehl je Fall in `derivation`; in tests/test_share_identity_cases.py unabhängig mit hashlib aus den Katalogfeldern nachgerechnet (Freigabe-Pfad nach der Regel des Plans, nicht aus der Implementierung), Format 1 ebenso.
- **pytest**: tests/test_share_identity_cases.py 87 grün; mit test_measurement_scripts.py, test_phase40_audit.py, test_php_trust_boundary.py 745 grün, 7 übersprungen; test_doc_keys.py, test_phase43_audit.py, test_coverage_counts.py, test_coverage_endpoint.py, test_allowlist_parity.py 148 grün.
- **Python-Gates** vor beiden Commits: ruff check grün, ruff format 256 Dateien sauber, pyright 0/0/0, vulture 0.
- **PHP-Baumhash**: b3f9109f -> af5413cdbfb3025ac83a3d55a2e50484c766a8168b2cf4893836f7bfb12c250d, 129 Dateien; Rezept 40b-baumhash.py und unabhängig find/sort/tr/sha256sum beide af5413cd; dieselbe Pipeline über `git archive 414e52f5` vor dem Plan: b3f9109f. PACKAGE-Paar und eingefrorenes PHP_FILES/PHP_TREE_HASH unberührt.
- **Sicherheit (T-43-65 bis T-43-67)**: DocKeyService loggt nichts; Test prüft, dass weder Pfad noch Host, Freigabe oder Wurzel in der Antwort stehen, nur Hex; die bestehenden Logtests von QueueService und ReconcileController (kein Pfad, kein Schlüssel im Log) laufen grün. Freigabe im Hash und NUL-Trennung mit eigenen Fällen (zwei Freigaben, Einzelspeicher gegen Freigabe, Teil zwischen Freigabe und Pfad verschoben). Allowlist aus 43-21 (shareIdentities( nur in StorageService/DocKeyService/AdminViewService) gilt weiter und ist grün.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Testanpassung] Relationsschwelle im Python-Test**
- Der eigene Python-Test verlangte zuerst mindestens 5 differsFrom-Relationen, der Katalog hat 4 (bericht.txt, Wurzel projekte, andere Freigabe, Einzelspeicher). Schwelle auf 4 gesetzt, gleiche Schwelle im PHPUnit-Test. Alle Pflichtfälle des Plans sind da; die Trennung "files/ nicht gekürzt" prüft weiter testTheFilesPrefixIsNotCut.

**2. QueueServiceReaderTest unverändert**
- Der Plan sah dort eine Anpassung des Konstruktor-Mocks vor; der Test baut DocKeyService per `createMock`, das ruft keinen Konstruktor, also war keine Änderung nötig (Datei unberührt, Test grün).

Sonst plangemäß. Keine STOPP-Regel berührt: nur die Vertragsfelder `docKeyFormat` im Auftrag und `format` in der Antwort von `GET /reconcile/doc-keys` (A-2), keine neue Route, keine Migration, kein Schema, kein Meta- oder AppConfig-Schlüssel, kein sichtbarer Satz.

## Bekannte Grenzen und offene Punkte

- **Zwischenzustand bis 43-24:** PHP liefert jetzt nur noch Format 2; der Container von rc.1 kennt `docKeyFormat`/`format` nicht und würde die neuen Schlüssel neben den alten speichern. Erst 43-24 (DOC_KEY_GENERATION 2, Generationssperre) macht das sicher. Unveröffentlicht, nur lokal; nicht einzeln ausliefern.
- **shareIdentityStats:** docKeysFor ruft shareIdentities, das die Zähler des letzten Aufrufs setzt. In 43-23 muss AdminViewService die Zähler direkt nach dem eigenen Aufruf lesen (so ist es dort geplant); ein Claim in einem anderen Prozess berührt das nicht.
- **Docker-Daemon:** lief bei Start schon (andere Sitzungen), nicht gestoppt, wie in 43-21.

## Threat Flags

Keine neuen Flächen außerhalb des Bedrohungsmodells.

## Self-Check: PASSED

- FOUND: php/lib/Service/DocKeyService.php (DOC_KEY_FORMAT = 2, shareIdentities()), backend/tests/fixtures/doc_key_cases.json ("format": 2), php/tests/Unit/DocKeyServiceTest.php
- FOUND: Commits 11850d86, c0e124c1
