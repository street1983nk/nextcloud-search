---
phase: 45-findling-1-7-0
plan: 27
subsystem: backend-poller, php-queue, coverage
tags: [issue-25, f3, poller, backstop, requeue, coverage, tdd]
requires: [45-21]
provides: [Zählfix QueueMapper::requeueAs (Dirty-Menge vor den Updates), Logzeile pass finished mit handed_ocr und handed_embed, Backstop OCR_HANDOVER_LIMIT 3 mit failed(repeatedly_stuck) und einer warning-Zeile, judged ohne failed/repeatedly_stuck in repo.py und coverage_truth.sh, Fixture-Fall Container-Zeile neben PHP-Zeile, CHANGELOG Text F3 EN/DE/FR, docs/ocr.md Abschnitt Backstop, Baumhashes PHP 86f595c7 -> 94720fd6 -> d5834a55 (147 -> 148 Dateien) und Paket 8c87b872 -> 961cd6ae -> d031ba6c (83)]
affects: [45-10, 45-11, 45-12, 45-13, 45-16, 45-14, 45-15]
tech-stack:
  added: []
  patterns: [Array-simulierte Datenbank mit Updates für QBMapper-Tests, Zähler je Prozess nur bei bestätigter Übergabe fortgeschrieben, Hash-Kriterium gegen legitime Wiederkehr, Logzeile mit byte-gleichem Präfix und Zeilenende erweitert]
key-files:
  created:
    - php/tests/Unit/QueueMapperTest.php
    - .planning/phases/45-findling-1-7-0/45-27-SUMMARY.md
  modified:
    - php/lib/Db/QueueMapper.php
    - php/lib/Service/FileStateService.php
    - backend/src/findling/worker/poller.py
    - backend/src/findling/worker/reconcile.py
    - backend/src/findling/store/repo.py
    - backend/tests/test_poller.py
    - backend/tests/test_coverage_counts.py
    - backend/tests/test_coverage_endpoint.py
    - backend/tests/fixtures/coverage_topology.json
    - backend/tests/test_measurement_scripts.py
    - scripts/ci/coverage_truth.sh
    - docs/ocr.md
    - docs/reconcile.md
    - CHANGELOG.md, CHANGELOG.de.md, CHANGELOG.fr.md
    - .planning/REQUIREMENTS.md
    - .planning/phases/45-findling-1-7-0/45-AUDIT.md
    - .planning/phases/45-findling-1-7-0/45-FREIGABEN.md
decisions:
  - "Texte F3 wörtlich wie im Plan (Owner \"Ok\", 2026-11-24 16:30 UTC): CHANGELOG EN/DE/FR, warning-Zeile mit \"demanded handovers\" (Anzahl = verlangte Übergaben, drei beim Auslösen), keine neuen Katalogtexte"
  - "Zählfix statt Verhaltenswechsel im Dirty-Zweig: beide Update-Statements byte-gleich, H1-Ursache bleibt bis zu den Melder-Daten offen (I-45-27-01)"
  - "Backstop im Container mit Hash-Kriterium, Zähler nur bei moved.ok, OCR-Urteil räumt, Neustart leert die Map als dokumentierte Grenze"
  - "judged schließt failed/repeatedly_stuck aus (Präzedenz D-43-16), die PHP-Seite zählt die Datei einmal über phpOnly"
metrics:
  duration: "über zwei Tage verteilt: Start 2026-11-24 16:30 UTC, Unterbrechung durch das Usage-Limit während der PHP-Gates von Task 2, Fortsetzung 2026-11-25; reine Arbeitszeit ca. 2,5 h, davon ca. 25 min Docker (PHPUnit gefiltert und voll, zwei volle PHP-Gate-Läufe)"
  completed: 2026-11-25
---

# Phase 45 Plan 27: #25 F3, eine kreisende Datei endet sichtbar Summary

Zählfix in QueueMapper::requeueAs (Dirty-Menge vor den Updates), Backstop im Poller nach drei verlangten Übergaben derselben Bytes an die OCR-Spur (failed(repeatedly_stuck), eine warning-Zeile nur mit Datei-ID und Anzahl), Logzeile mit handed_ocr/handed_embed bei byte-gleichem Präfix und Zeilenende, und ein Nenner, der die abgeschriebene Datei auf beiden Rechenwegen genau einmal zählt.

## Commits

| Task | Commit | Inhalt |
|---|---|---|
| 1 | b755694e | Freigabezeile `Freigabe Text F3 45-27` in 45-FREIGABEN.md |
| 2 | b5665f27 | Zählfix requeueAs, QueueMapperTest neu, PHP-Baumhash 94720fd6 (148) |
| 3 | 2a7befdc | Backstop und Logzeile im Poller, sieben Tests, Paket-Baumhash 961cd6ae |
| 4 | 4665574b | judged ohne failed/repeatedly_stuck (repo.py, coverage_truth.sh), Fixture-Fall, Kommentare, Baumhashes d031ba6c und d5834a55 |
| 5 | d3e6d76a | CHANGELOG EN/DE/FR, docs/ocr.md, docs/reconcile.md, Folge-Punkte, IDX-11 |

## TDD und Mutationen

- Task 2: RED `Tests: 3, Assertions: 9, Failures: 1.` (`Failed asserting that 2 is identical to 1.`), GREEN `OK (3 tests, 15 assertions)`; M50 und M51 je rot `testTheAnswerCountsNoRowThatWasOnlyHandedBack`.
- Task 3: RED `6 failed, 264 passed, 1 skipped` (der siebte Fall, `test_two_handovers_of_the_same_bytes_still_hand_over`, ist Wächter des bestehenden Verhaltens und belegt M52), GREEN `270 passed, 1 skipped`; M52 bis M57 je rot mit dem geplanten Test.
- Task 4: RED `8 failed, 82 passed` (neuer Fall `assert 19 == 18`), GREEN `90 passed`; M58 rot.
- Jede Mutation einzeln, Quelldatei danach per SHA-256 byte-gleich zurück. Alles wörtlich in 45-AUDIT.md unter `### RED und GREEN 45-27`.

## Gates (Endstand je Task, seriell)

- PHPUnit voll `OK (1451 tests, 9087 assertions)` (Task 2 und 4).
- `php_gates_docker.sh all` grün (Task 2 und 4): Psalm-Taint 0 Befunde gegen v33.0.9, v34.0.6, v35.0.3; php-cs-fixer `Found 0 of 145 files`; zizmor und actionlint ohne Fund, Proben gesehen.
- ruff `All checks passed!`, ruff format `261 files already formatted`, pyright latest `0 errors, 0 warnings, 0 informations`, vulture ohne Fund (jeder Task).
- pytest: Task 2 `572 passed` (test_measurement_scripts); Task 3 `842 passed, 1 skipped` plus `178 passed` (ganze `Weitere Tests:`-Liste); Task 4 `231 passed` plus `693 passed`; Task 5 `736 passed`, dazu `313 passed, 12 skipped` und `226 passed, 8 skipped` für die Tests, die CHANGELOG und die geänderten Doku-Seiten lesen.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Hilfsmethode im neuen PHPUnit-Test kollidierte mit PHPUnit**
- **Gefunden in:** Task 2 (erster RED-Lauf)
- **Problem:** `private static function matches()` überschrieb die finale Methode `PHPUnit\Framework\Assert::matches()` (Fatal error, 0 Tests).
- **Fix:** in `rowMatches()` umbenannt, danach RED wie geplant.
- **Commit:** b5665f27

**2. [Rule 1 - Test-Handzählung] test_coverage_endpoint.py hielt eigene Zählungen der Fixture-Zeilen**
- **Gefunden in:** Task 4 (GREEN)
- **Problem:** `_living(data) == 29` und `everything == 32` zählen die lebenden Fixture-Zeilen von Hand; die neue Container-Zeile 1214 macht daraus 30 und 33.
- **Fix:** bewusst nachgezogen (nicht abgeschwächt), mit Kommentar; im Audit genannt.
- **Commit:** 4665574b

**3. [Planpräzisierung] `Weitere Tests:`-Liste**
- Die grep-Liste des Plans trifft nach dem neuen Baumhash-Absatz (er nennt `handed_ocr`) auch tests/test_measurement_scripts.py; die Audit-Zeile führt deshalb sechs Dateien, exakt gleich der grep-Ausgabe.

**4. [Planpräzisierung] `Umgestellt: keine`**
- Alle acht bestehenden `result.skipped`-Erwartungen in test_poller.py sind endgültige Skips ohne Übergabe in derselben Runde; keine musste umgestellt werden. Die geforderte eine `Umgestellt:`-Zeile steht mit "keine" und einer Begründungszeile im Audit.

**5. [Ablauf] Unterbrechung durch das Usage-Limit**
- Während der PHP-Gates von Task 2 brach die Session ab. Am 25.11. geprüft: Baum per SHA-256 unverändert, RED von Task 2 war vor dem Fix sauber gesehen und im Audit wörtlich notiert, der Gate-Lauf war mit Erfolg zu Ende gelaufen (Skript unter `set -euo pipefail`, letzter Schritt grün); erneuter gefilterter GREEN-Lauf, dann alle Python-Gates neu, dann Commit.

Sonst: CoverageTopologyParityTest.php hält keine eigenen Erwartungszahlen (liest nur die unveränderten expected-Blöcke) und blieb unangetastet; scripts/ci/coverage_e2e.sh rechnet judged nicht selbst nach, nichts nachzuziehen. Kein neuer nutzersichtbarer Katalogtext entstand (Schlüsselzahl bleibt 387).

## Offene Folge-Punkte (mit Beleg in 45-AUDIT.md, `### Offene Folge-Punkte 45-27`)

- I-45-27-01: H1-Ursache, Dirty-Zweig von requeueAs (php/lib/Db/QueueMapper.php:659-667) lässt kind content und retries 0; wartet auf die DB-Abfrage des Melders.
- I-45-27-02: OCR-Reserve im Claim (php/lib/Service/QueueService.php:267, `if ($rows <= 0) { break; }`).
- I-45-27-03: Give-up-Semantik (php/lib/Service/QueueService.php:294 zählt nur Auslieferungen, requeueAs setzt retries auf 0).

## Hinweise an Folgepläne

- **45-10:** deploy-harp.yml Z. ~4054 (Kandidatenliste des Upgrade-Beweises) und Z. ~5576 (written_off-Abfrage, erwartet nur Seed-IDs) parsen den repeatedly_stuck-BESTAND. Erzeugt der Backstop auf der Probeinstanz echten Bestand, fällt er dort als unerwarteter Kandidat auf. Die Logzeilen-Konsumenten (resilience.yml Z. 399/500, deploy-harp.yml Z. 7910) bleiben gültig, Präfix und Zeilenende sind byte-gleich.
- **45-16 (secure-phase):** Threat-Register erweitert um T-45-88 bis T-45-91 (Fehlabschreibung durch den Backstop, Name/Pfad in der warning-Zeile, falsche requeued-Zahl, Doppelzählung im Nenner), alle mitigiert mit Tests und Mutationen M50 bis M58; Restrisiko Prozess-Neustart (Map leer) akzeptiert und in docs/ocr.md dokumentiert.
- **REL-07** bleibt offen bis zum Store-Release.

## Known Stubs

Keine.

## Threat Flags

Keine neue Oberfläche außerhalb des Threat-Registers des Plans: keine neue Route, kein neuer Datei- oder Netzzugriff; die neue Logzeile trägt nur Zähler und Datei-ID.

## Self-Check: PASSED

Commits b755694e, b5665f27, 2a7befdc, 4665574b, d3e6d76a vorhanden; php/tests/Unit/QueueMapperTest.php und diese Datei vorhanden; statische Verifies von Task 2 bis 5 am Endstand grün; keine Gedankenstriche.
