---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 18
subsystem: container-poller, coverage-e2e
tags: [gateway, unreadable, outage-threshold, coverage, e2e, smb, tdd]
requires: [43-17]
provides: [D-43-16 Container-Hälfte, GATEWAY_UNREADABLE_STATUS, E2E fünf Beine]
affects: [43-07, 43-19, 43-08]
tech-stack:
  added: []
  patterns: [422 vor jeder Zählung aus der Ausfall-Schwelle, eine Ablehnungsserie über zwei Paare, Matrix als include-Liste variant x smb]
key-files:
  created: []
  modified:
    - backend/src/findling/nc/client.py
    - backend/src/findling/worker/poller.py
    - backend/src/findling/store/repo.py
    - backend/src/findling/extract/errors.py
    - backend/tests/test_poller.py
    - backend/tests/test_store_repo.py
    - backend/tests/test_reconcile.py
    - backend/tests/test_coverage_counts.py
    - backend/tests/fixtures/coverage_topology.json
    - php/tests/Unit/CoverageTopologyParityTest.php
    - backend/tests/test_measurement_scripts.py
    - .github/workflows/coverage-e2e.yml
    - scripts/ci/coverage_e2e.sh
    - scripts/ci/coverage_truth.sh
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-07-PLAN.md
decisions:
  - "Gateway 422 wird im Container skipped(unreadable), alle anderen Status ab 400 bleiben failed(gateway_error)"
  - "422 zählt nicht zur Ausfall-Schwelle und wird nie belastet; bei fremder Eskalation geht die Zeile erstattet und ohne Urteil zurück"
  - "failed(gateway_error) und skipped(unreadable) sind eine Ablehnungsserie auf gleichem etag (attempts, gateway_retry_candidates)"
  - "_COVERAGE_JUDGED und die Wahrheit expected_denominator_phase_a lassen unreadable aus, die PHP-Seite zählt es über oc_findling_file_state"
  - "E2E: fünf Beine (gate-crawl/wrapped, gate-queue/wrapped, gate-queue/native, v1.6.2/native, upgrade/native), Modus per function_exists belegt"
metrics:
  completed: 2026-11-07
  tasks: "2 von 3 (Task 3 offen, wartet auf Owner)"
  files: 15
---

# Phase 43 Plan 18: Gateway 422 als nicht lesbar, E2E mit fünf Beinen Summary

Der Container urteilt eine Gateway-Antwort 422 als skipped(unreadable), zählt sie nicht zur Ausfall-Schwelle, wiederholt sie gedeckelt wie failed(gateway_error) und lässt sie aus judged heraus, damit die PHP-Seite sie genau einmal im Nenner und in "nicht lesbar" zählt; das Harness "Coverage end to end" läuft in fünf Beinen (Wrapped und nativ) mit harten Proben für gesperrte, leere und große Dateien.

**Stand: Task 1 und Task 2 lokal committet. Task 3 (Checkpoint Push und Dispatch) ist offen und wartet auf den Owner; keine Freigabezeile geschrieben, nichts gepusht, nichts dispatcht.**

## Commits

| Task | Commit | Betreff |
|------|--------|---------|
| 1 (RED) | 6dc71363 | test(43-18): a refused open is an unreadable file and no outage |
| 1 (GREEN) | ba4b9398 | fix(43-18): the container counts a refused open as not readable and never as an outage |
| 2 | 7ef3bc9b | ci(43-18): native and wrapped smb legs, hard probes for locked, empty and large files |
| 3 | offen | Checkpoint, Owner-Freigabe Push und Dispatch |

## Umsetzung Task 1

- client.py: `GATEWAY_UNREADABLE_STATUS: Final = 422` mit Kommentar (nur cannotOpen, kein Proxy-Status, 1.6.2 nur über fopen false); die Antwort reist weiter als GatewayRefused.
- poller.py: `_refusal_outcome(refused)` gibt für 422 `skipped(Reason.UNREADABLE)`, sonst `failed(GATEWAY_ERROR)`; genutzt im Inhaltszweig und im Scan-Zweig. `_count_refusal` kehrt bei 422 vor jeder Zählung zurück, die Zeile kommt nicht in `_refused_rows`, also nicht in `charged` (F4, W11). Der Zweig _RefusalsPiledUp ist unverändert.
- repo.py: `_RECORD_SQL` setzt die Serie über beide Paare auf gleichem etag fort (Eintritt aus anderem Urteil oder neuem etag setzt 1); `gateway_retry_candidates` liefert beide Paare mit attempts <= limit; `_COVERAGE_JUDGED` schließt 'unreadable' aus. Keine Spalte, kein Index, kein Meta-Schlüssel, Vokabular unverändert.
- errors.py: Kommentar an UNREADABLE ("also written by the container for a gateway 422, D-43-16").
- Fixture: neue Variante `gateway_unreadable` mit eigener Topologie (Gruppe [51, 52] alle Mitglieder unreadable, Gruppe [61, 62] mit lesendem Mitglied 61 für N1, Einzelspeicher 71), Python- und PHP-Erwartung von Hand hergeleitet: Nenner 6, Zähler 4, notReadable 2, Quote 66 %. Mit unreadable in judged stünde der Nenner bei 8 (doppelt).
- CoverageTopologyParityTest: neuer Fall `testAGatewayUnreadableFileCountsOnceAndAsNotReadable` liest dieselbe Variante. PHP-Code unverändert.
- test_coverage_counts: Zufallstopologie um ("skipped", "unreadable") erweitert, die Mengenrechnung der Wahrheit schließt unreadable aus.
- Baumhashs (je zweimal gerechnet, Rezept 40b-baumhash.py und find, LC_ALL=C sort, tr -d '\r', sha256sum): PACKAGE 83 Dateien, 1c5a8954 auf 2908e94bc47220eb5dc82491ebce61300a9d66575673a9f079f784d3b01d6ed3 (Positivkontrolle `git archive HEAD` vor GREEN ergab 1c5a8954); PHP 129 Dateien, e67c5d95 auf 7cc9aa68bf4bafeb49029f17c5e648f7d34cd8c30f04188a39940e197d36b900 (Positivkontrolle `git archive HEAD~1` ergab e67c5d95). PHP_FILES/PHP_TREE_HASH unberührt.

## Umsetzung Task 2

- Workflow: Matrix als include-Liste variant x smb (fünf Beine), Jobname `coverage-e2e (<variant>, <smb>)`, Artefakt `coverage-e2e-<variant>-<smb>`, `fail-fast: false`. Für native Beine vor setup-test-nc ein eigener Schritt `shivammathur/setup-php@eb7c497e18156a6bbabfef1d3a82760b9eda3962 # 2.40.0` mit php 8.2, `extensions: smbclient`, `coverage: none`. `SMB_MODE` an den Skriptschritt.
- setup-php und smbclient: setup-php installiert auf Ubuntu Erweiterungen, die als Paket vorliegen (README des gepinnten Stands); `php8.2-smbclient` steht im Paketindex von ppa:ondrej/php für noble (amd64), per curl auf Packages.gz geprüft. Kein apt-Ausweichweg nötig. Ob der zweite setup-php-Lauf in der Action die Erweiterung stehen lässt, belegt erst der Lauf: das Skript bricht ab, wenn function_exists nicht zu SMB_MODE passt.
- coverage_e2e.sh: SMB_MODE Pflicht; Modusprüfung per `php -r 'function_exists("smbclient_state_new")'` mit Zeile in der Ergebnistabelle; `head_companion` (gate-crawl, gate-queue immer, upgrade nur zwischen Update und Rückweg); `gemeinsam/leer.txt` (0 Bytes, per smbclient als alice) und `gemeinsam/gross.bin` (10 MB Zufall, Typ außerhalb der Wahrheit); `gateway_probe <label> <uid> <fid> <Status> [collect]` mit PROBE_MAX_SECONDS=10 und size_download-Prüfung für leer.txt hinter dem Kopf; `large_probe` mit tc htb auf lo (800 kbit, Filter sport und dport 445, EXIT-Trap entfernt die Drosselung), curl -m 240, sha256 gegen die Quelle; `no_stale_smbclient` nach den Proben und nach Phase B; `judge_locked` für die Urteile (Kopf nach dem ersten drain, upgrade nach Phase B, v1.6.2 failed/gateway_error nur im Container als Gegenprobe); drain hinter einer 1.6.2-Companion tolerant mit `outage_abort_tolerated` und `drain_incomplete` (Ergebnistabelle und Schlusszeilen); W10-Prüfung auf oc_filecache (keine Testdatei außer leer.txt mit Größe 0). soft und probe_hangs entfallen.
- coverage_truth.sh: `judged_rows` schließt 'unreadable' aus, Herleitung nennt D-43-16; php_only unverändert.
- 43-07-PLAN.md Task 3: prüft "Freigabe Push 43-18" und "Freigabe Dispatch 43-18", wertet fünf Beine aus, verify zählt fünf erfolgreiche Jobs; Absatz "Umgestellt am 2026-11-07 durch 43-18 (DENY-ACE-Fix)".

## Tests

- RED (6dc71363): 16 failed, 476 passed, 1 skipped (test_poller, test_store_repo, test_reconcile, test_coverage_counts).
- GREEN: verify-Satz plus Vokabular-Paritätstests (test_poller, test_store_repo, test_reconcile, test_coverage_counts, test_coverage_endpoint, test_status_leave_out, test_measurement_scripts, test_phase41_audit, test_admin_ui_contract, test_extract_errors, test_phase31_audit, test_queue_client) 1668 passed, 1 skipped; test_gateway_client 37 passed; test_phase40_audit, test_reconcile_vanished, test_status_endpoint, test_store_vanished 228 passed, 7 skipped. Freier RAM vor den Läufen 5,2 bis 5,6 GB. Keine Vollsuite.
- Workflow-Tests (pins, contexts, size): 36 passed. `bash -n` beider Skripte grün; shellcheck lokal nicht vorhanden.
- Gates: ruff check, ruff format --check (254 Dateien), pyright latest 0 errors, vulture leer.
- **PHPUnit lokal: nein** (Owner: Docker bleibt aus, kein lokales PHP). Der neue Paritätsfall und die PHP-Teile von 43-17 werden erst im CI-Job nach dem freigegebenen Push belegt. Die PHP-Erwartung des Fixture-Falls ist von Hand aus perDocumentDenominator (max je Teil) und notReadable (Summe der notReadable-Teile) hergeleitet; der Python-Test hält dieselbe Arithmetik.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocker] RED-Test der Konstante ohne pyright-Fehler**
- **Found during:** Task 1 (RED)
- **Issue:** `nc_client_module.GATEWAY_UNREADABLE_STATUS` scheitert im RED-Stand an pyright (unbekanntes Attribut), das Gate muss vor jedem Commit grün sein.
- **Fix:** Test liest `vars(nc_client_module).get("GATEWAY_UNREADABLE_STATUS")`; RED ist eine Assertion, kein Importfehler.
- **Commit:** 6dc71363

**2. Prozessprüfung über Vorfahren statt nur Eltern (W12)**
- **Issue:** icewind/smb startet smbclient per proc_open; zwischen php -S und smbclient können sh oder stdbuf stehen, eine reine Elternprüfung fände dann nichts (leere Prüfung).
- **Fix:** `no_stale_smbclient` geht bis zu fünf Vorfahren hoch; findet `pgrep -f 'php -S'` keinen Prozess, bricht der Lauf ab ("tests nothing").
- **Commit:** 7ef3bc9b

**3. Fixture-Fall als eigene Topologie**
- **Issue:** Der Plan nennt einen Fixture-Fall "gateway_unreadable"; die Varianten hatten bisher nur extraRows zur Haupttopologie.
- **Fix:** Variante mit eigenen rows, mounted, groups und vollständigem expected samt php-Block; die Haupttopologie und ihre Erwartung bleiben unverändert.
- **Commit:** 6dc71363

**4. Werkzeug-Befund grep 3.0**
- Die doppelten Backslash-Prüfungen und `\|` wurden zusätzlich mit `grep -F` gegengeprüft (files.path, findling.store je 0 Treffer); die Gedankenstrich-Prüfung per Positivkontrolle (eine Probezeile mit U+2014 ergibt 1 Treffer).

## W4 (verlorene Quittung), Grenze statt Test

Der unchanged-Zweig des Pollers greift nur nach einem erfolgreichen Abruf mit content_hash und nur für state 'indexed' (`_IS_UNCHANGED_SQL`); eine 422-Zeile erreicht ihn nie. Bleibt die Quittung aus (queue.py: "could not acknowledge a batch"), kommen die Zeilen nach dem Sperrablauf zurück, der Container fragt das Gateway erneut, urteilt bei 422 wieder skipped(unreadable) und quittiert es dann; attempts steigt dabei um eins (die Serie zählt die erneute Ablehnung). Bis zur erneuten Quittung fehlt die Datei in oc_findling_file_state und damit im Nenner und in notReadable. Kein Test, da der Code keinen unchanged-Pfad für diese Zeile vorsieht.

## Changelog-Vermerk (Bestandszeilen aus 1.6.2)

Zeilen failed(gateway_error), die 1.6.2 für eine 422 geschrieben hat, werden nicht umgeschrieben (STOPP-Regel). Mit Restbudget (attempts <= 3 auf unverändertem etag) vergibt der Abgleich sie erneut, und der Kopf urteilt dann skipped(unreadable); erschöpfte Zeilen bleiben bis zur nächsten Dateiänderung (oder `occ findling:index --restart`) Fehler.

## Grenzen

- T-43-59 Restrisiko: ein Netzfehler zwischen stat und cli_open im Wrapped-Modus wird 422 und damit unreadable; die gedeckelte Wiederholung über beide Paare mildert das.
- tc auf dem Runner ist ungeprüft: geht es nicht, läuft gross.bin ungedrosselt, die note "tc could not throttle" und `throttled=0` in der Ergebnistabelle zeigen es.
- v1.6.2 und upgrade vor dem Update: ein toleranter drain läuft bis DRAIN_TIMEOUT (1500 s) je drain; endet er dort mehrfach, kann das Bein die Jobfrist von 90 min erreichen.
- Die Erwartungen der Proben für die 1.6.2-Companion (Sperrproben 422 nativ, leer.txt 400) stammen aus dem Plan (StreamResponse.php:47-49 mit Output.php:37) und sind lokal nicht gelaufen; eine Abweichung bricht das Bein ab und ist dann ein Befund.

## Threat Flags

Keine neue Angriffsfläche: keine Route, kein Schlüssel, keine Schemaänderung; die Probe- und Urteilszeilen tragen nur Status, Sekunden, Bytes, Datei-IDs.

## Known Stubs

Keine.

## Self-Check: PASSED

- Dateien vorhanden: alle unter key-files.modified.
- Commits vorhanden: 6dc71363, ba4b9398, 7ef3bc9b.
