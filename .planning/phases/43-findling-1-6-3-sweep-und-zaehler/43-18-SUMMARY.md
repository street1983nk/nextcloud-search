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

## Fix-Runde 1 (Lauf 42418778026, 2026-11-07)

Anlass: Dispatch-Lauf 42418778026 rot in allen fünf Beinen, Kern-Fix belegt (gesperrte Dateien 422 in rund 0,1 s). Drei Abweichungen, drei Aufgaben. Lokal committet, nicht gepusht, kein Dispatch.

| Aufgabe | Commit | Betreff |
|---------|--------|---------|
| 1 (RED) | 5d0918c0 | test(43-18): a slow smb line waits eighty seconds for a whole read block |
| 1 (GREEN) | efa39712 | fix(43-18): the gateway waits for a whole smb read block before it gives up |
| 2 und 3 | 1456ffa2 | ci(43-18): empty file 200 from both companions, smb at 200 KB/s, named search misses |

**1. Produkt, Fristen 80 s.** Beleg des Koordinators: Samba 4.19.5 source3/libsmb/clireadwrite.c:363-366, bei SMB2 ist chunk_size = smb2cli_conn_max_read_size, Server-Standard "smb2 max read" 8 MiB; cli_pull reicht erst nach einem vollständigen Block an FD 5. `FIRST_BYTE_SECONDS` und `IDLE_SECONDS` von 30.0 auf 80.0, unter `_DEFAULT_TIMEOUT_SECONDS = 90.0` (backend nc/client.py:179, httpx-Lesetimeout zwischen zwei Teilen der Antwort). Am Code geprüft:
- DENY unberührt: Wrapped endet über den Anstupser beim ersten leeren Read mit EOF ohne Daten (OUTCOME_EMPTY, 422 über den 0-Bytes-Zweig, keine Frist beteiligt); nativ scheitert schon fopen.
- MAX_READS 60000 bleibt: je Read eine Zeile (PHP_EOL, 1 Byte) in die stdin-Pipe (65536). Erste Wartezeit 80 s bei 20 ms Pause rund 4000 leere Reads, je Lücke 80 s bei 200 ms rund 400; 50 MiB in 8-MiB-Blöcken: 6400 Datenreads, eine erste Wartezeit, sechs Lücken, rund 13000 Reads.
- Tests (BoundedStreamReaderTest): Konstanten 80.0; erste Daten nach 79 s ergeben DATA und END_COMPLETE; 81 s ohne Daten ergeben TIMEOUT zwischen 80 und 81 s (im Controller 422 über den bestehenden Fall mit FIRST_BYTE_SECONDS); Lücke 79 s zwischen Blöcken COMPLETE, 81 s STALLED; 50 MiB in 8-MiB-Blöcken 79 s auseinander COMPLETE unter 15000 Reads. Kommentar mit Beleg in BoundedStreamReader.php, D-43-16 in 43-CONTEXT.md um einen Satz ergänzt.
- Baumhash PHP 129 Dateien, 7cc9aa68 auf 6d1847e61ab8be280337b230b231b857b4e6c441858ac4b350a66e3d2266b79a, zweimal gerechnet (40b-baumhash.py und find, LC_ALL=C sort, tr -d '\r', sha256sum); Positivkontrolle `git archive HEAD~1` vor GREEN ergab 7cc9aa68.
- **PHPUnit lokal: nein** (kein Docker, kein lokales PHP). Beleg erst im CI-Job nach einem freigegebenen Push.

**2. Harness, leer.txt.** Befund: die Plan-Annahme "1.6.2-Companion antwortet 400 auf leer.txt" (43-18-PLAN.md, T-43-62, aus StreamResponse.php:47-49 mit Output.php:37) war falsch; gemessen in Lauf 42418778026 sind 200 mit 0 Bytes auf v1.6.2/native und upgrade/native. Erwartung jetzt 200 mit 0 Bytes für beide Companions, die 0-Bytes-Prüfung gilt für beide. Die Unterscheidung alt und neu trägt allein das Container-Urteil failed/gateway_error von v1.6.2. 43-18-PLAN.md unverändert; 43-07-PLAN.md Task 3 korrigiert.

**3. Harness, Drosselung und Suchgegenprobe.**
- gross.bin: `THROTTLE_RATE=1600kbit` (rund 200 KB/s), ein 8-MiB-Block in rund 42 s, 10 MB in zwei Blöcken, gesamt rund 52 s; curl -m 150 (`LARGE_MAX_SECONDS`); neu und strenger: ein gedrosselter Abruf unter 40 s (`LARGE_MIN_SECONDS`) ist ein Fehler, weil dann keine lange Lücke geprüft wurde.
- Suchgegenprobe: Befund im Log von 42418778026, die fehlenden Namen standen schon in den notes (45 Namen), aber vermischt mit nie suchbaren Dateien (backlog-*.png, gesperrte Dateien). Jetzt je fehlendem Namen eine note "search miss in the numerator truth" bzw. "outside the numerator truth" (Abgleich gegen die Dateinamen in numerator.tsv) mit der Kurzform der Rohantwort für den ersten Nutzer (Anzahl entries und Titel, sonst OCS-Status und die ersten 120 Bytes). Die Kurzform geht in eine Datei, nicht auf stdout, die Zählung des Aufrufers bleibt unverändert (auch für die Rückweg-Probe). Soll bleibt 23, keine Erwartung gelockert. jq-Ausdruck lokal mit drei Beispielantworten geprüft (Liste, leere Liste, HTML).

**Tests der Runde:** test_workflow_pins, test_workflow_contexts, test_workflow_size, test_measurement_scripts 608 passed; `bash -n` beider Skripte grün; ruff check, ruff format --check, pyright latest 0 errors auf test_measurement_scripts.py, vulture leer.

**Grenze für Known limitations (43-08):** Unter etwa 100 KB/s (8 MiB in 80 s, genau 105 KB/s) weist der Gateway im Wrapped-Modus Dateien größer als ein SMB2-Leseblock ab (422 vor den Headern) oder beendet sie kurz (stalled zwischen zwei Blöcken); der Container hätte dort ohnehin seinen 90-s-Timeout. Mit den längeren Lücken sinkt die Größengrenze aus MAX_READS bei langsamen Leitungen etwas (bei 200 KB/s rund 1230 Reads je 8-MiB-Block, also rund 390 MiB statt 469 MiB); betrifft nur FINDLING_MAX_FILE_BYTES über der Vorgabe.

## Fix-Runde 2 (Lauf 42425348629, 2026-11-08)

Anlass: Vollzug Fix 1 (43-FREIGABEN.md), alle fünf Beine rot mit drei Harness-Befunden. Kein Produktcode geändert. Lokal committet, nicht gepusht, kein Dispatch.

| Aufgabe | Commit | Betreff |
|---------|--------|---------|
| 2 (viewer) | c7c53bfc | ci(43-18): the coverage legs carry the shipped app viewer for occ upgrade |
| 1 und 3 | 289c0120 | ci(43-18): one word per file, search with limit 25, gross.bin inside the smb timeout |
| 4 und 5 | dieser docs-Commit | Texte-Entwurf, 43-19-Ergänzung, 43-DEBUG-SUCHE.md, diese Runde |

**1. Suchwörter.** `next_word` setzt `NEXT_WORD` statt zu drucken; alle sechs Aufrufer (samba_file, gesperrt-alle/-bob, home_file, backlog-*.png, Rückweg) per grep gefunden und umgestellt, kein `$(next_word)` mehr. `words_unique` (`cut -f1 words.tsv | sort | uniq -d` leer, Zeilen gleich verschiedene Wörter, sonst fail) vor dem Crawl und vor der Gegenprobe (die Backlog-Wörter kommen erst in Phase A dazu). Positiv- und Negativkontrolle lokal in bash: 60 Aufrufe ergeben 60 verschiedene Wörter, das alte Muster `a=$(next_word)` ergibt leer, `words_unique` scheitert an einem doppelten Wort. Gegenprobe mit `--data-urlencode limit=25`: belegt am Server stable34, `UnifiedSearchController::search(?int $limit)` mit `SearchQuery::LIMIT_DEFAULT = 5`, Deckel `unified-search.max-results-per-request` 25. Rückweg-Prüfung: wird erst jetzt aussagekräftig, denn bisher trug der alte Inhalt von notiz.txt dasselbe Wort, die Suche fand die Datei also auch ohne den neuen Inhalt; jetzt ist das Wort neu (eigener fail, falls es schon in words.tsv steht). Die beiden gleich.txt tragen jetzt je ein eigenes Wort plus `zqgleichdoc`, wie 43-07-PLAN.md es beschreibt ("Inhalt mit zwei Wörtern je Share"). Soll 23 unverändert.

**2. viewer.** Eigener Schritt in coverage-e2e.yml nach dem Server-Checkout: `actions/checkout@3d3c42e5... # v7.0.1`, `repository: nextcloud/viewer`, `ref: stable34`, `path: apps/viewer` (Muster aus nextcloud-audio-video-search deploy-harp.yml). setup-test-nc kann es nicht (kein viewer-Eingang, sie checkt den Server nicht selbst aus). Für alle fünf Beine, damit die Instanz überall gleich ist; nur das upgrade-Bein braucht es (Updater::checkAppsRequirements, Lauf 42425348629). viewer stable34 existiert (7ca0059c), info.xml min/max 34, composer/ und js/ liegen im Repo. Andere Workflows unverändert.

**3. gross.bin.** `throttle_smb <rate>`; `large_probe` bei `THROTTLE_RATE=8mbit` (rund 1 MB/s, 8 MiB in rund 8,4 s, innerhalb smbclient -t 20), Mindestdauer 8 s (unter einem einzigen 8-MiB-Block bei dieser Rate, ungedrosselt deutlich unter 1 s), curl -m 60. Neu `large_probe_long`: `files_external:config <daten_mount> timeout 120`, Rücklesen muss 120 ergeben (sonst fail "tests nothing"), Abruf bei 1600kbit (rund 200 KB/s, 10 MiB in rund 52 s), Pflicht 200, gleiches sha256, Mindestdauer 40 s, curl -m 150; danach Option geleert und rückgelesen (leer = Standard 20, SMB.php:103-106), damit der Crawl mit dem Stand eines frischen Speichers läuft. Beide nur in den Wrapped-Beinen, beide collect.

**4. Texte.** 43-TEXTE.md: Abschnitt "Vorab-Entwurf zu Block V" mit EN und DE (FR macht 43-19). 43-19-PLAN.md: must_have und Aktion ergänzt; Erkennung über `function_exists('smbclient_state_new')` (icewind/smb System::libSmbclientAvailable), Satz als eigener Schlüssel nur bei fehlender Erweiterung, de-Schlüsselzahl dann 355.

**5.** 43-DEBUG-SUCHE.md mit Nachtrag (V1 belegt, Fix umgesetzt) committet.

**Abweichungen:**
- [Befund] Die Option heißt nicht Mount-Option: `files_external:option` setzt Mount-Optionen, die SMB::__construct nie sieht; `timeout` ist eine Backend-Option (`Lib/Backend/SMB.php`, DefinitionParameter `timeout`, FLAG_OPTIONAL und FLAG_HIDDEN, also im Web-Formular unsichtbar) und wird mit `occ files_external:config <mount> timeout 120` gesetzt (`Command/Config.php::setOption` → setBackendOption; ConfigAdapter reicht getBackendOptions an den Konstruktor). Per occ setzbar, daher kein STOPP; Harness und Texte nennen files_external:config.
- [Befund] Block V gibt es in 43-TEXTE.md noch nicht (schreibt erst 43-19); der Zusatzsatz steht deshalb als Vorab-Entwurf davor, 43-19 übernimmt ihn.
- Die frühere Grenze "unter etwa 100 KB/s" (Fix-Runde 1) gilt nur mit erhöhtem timeout; ohne Erweiterung und mit Standard-timeout liegt die Grenze bei etwa 420 KB/s (siehe unten).

**Tests der Runde:** `bash -n` beider Skripte grün; test_workflow_pins, test_workflow_contexts, test_workflow_size, test_measurement_scripts 608 passed. Kein Python berührt, daher kein ruff/pyright/vulture. Harness nicht lokal gelaufen (kein Docker, kein lokales PHP); Beleg erst im nächsten freigegebenen Dispatch.

**Known limitations für 43-08 (ersetzt die Grenze aus Fix-Runde 1 für SMB ohne Erweiterung):** Im Wrapped-Modus (SMB ohne php-smbclient) startet icewind/smb smbclient mit `-t 20`; ein SMB2-Leseblock von 8 MiB muss innerhalb dieses timeout (Standard 20 s) ankommen, also ab etwa 420 KB/s (8 MiB / 20 s). Langsamer: Dateien größer als ein Block werden 422 und zählen als nicht lesbar. Abhilfe: Erweiterung php-smbclient installieren (Admin-Handbuch: "strongly recommended") oder Backend-Option timeout des Speichers erhöhen (`occ files_external:config <mount> timeout <s>`, nicht im Web-Formular); mit erhöhtem timeout greift die Gateway-Grenze von rund 105 KB/s (80 s je Block) aus Fix-Runde 1.

## Fix-Runde 3 (Lauf 42477570073, 2026-11-08)

Anlass: Dispatch-Lauf 42477570073 (Kopf fbd5626c). Alle Produktvergleiche (Zähler 23, Nenner 55, notReadable 1, Urteile gesperrt/leer, Gateway-Proben, große Datei) gleich der Wahrheit; zwei Harness-Befunde. Kein Produktcode geändert. Lokal committet, nicht gepusht, kein Dispatch.

| Aufgabe | Commit | Betreff |
|---------|--------|---------|
| 1 und 2 | 7e658fc0 | ci(43-18): search expectation from planted words of truth names, catch-up of 1.5 done under 1.6.2 |

**1. Suchgegenprobe (gate-crawl/wrapped, gate-queue/wrapped, gate-queue/native, v1.6.2/native: Soll 23, gefunden 22).** Alle Fehltreffer lagen außerhalb der Wahrheit, keiner in ihr; gate-crawl: 28 Wörter, 6 außerhalb (daten-carol-1/2, dave-1/2, verwaist, gesperrt-alle), also 22 Wörter für 23 Wahrheitszeilen. Eine indexierte Wahrheitszeile trägt kein Wort des Harness. Welche, ist unbelegt (Verdacht: eine Skeleton-Datei aus einem Home, das vor dem Leeren von skeletondirectory entstand); die neue note nennt sie im nächsten Lauf.
- Soll jetzt = Zahl der WORDS-Zeilen, deren Dateiname als Basename in numerator.tsv steht. Ein Wort zählt einmal je Datei, in die es geschrieben wurde; die zwei gleich.txt (daten und archiv, je ein Wort) bleiben zwei Soll-Treffer, solange beide in der Wahrheit stehen.
- Nicht lockerer: das Wort eines Wahrheitsnamens muss seine Datei finden (Titelvergleich in search_crosscheck); ein gefundenes Wort außerhalb der Wahrheit hebt found über das Soll; neu ist die eigene Prüfung "search misses in the numerator truth" mit Soll 0, damit ein Treffer außerhalb keinen Miss innerhalb verdecken kann.
- Jede Wahrheitszeile ohne Wort: note "numerator truth row without a planted word: <Speicher> <Pfad>" (Schlüssel, kein Inhalt), Anzahl als eigene Zeile der Ergebnistabelle. Soll 0 Wörter der Wahrheit ergibt fail ("tests nothing").
- Lokal geprüft mit Beispieldaten: zwei gleich.txt in der Wahrheit, eine Zeile home::admin files/Nextcloud.png ohne Wort, ein Wort außerhalb: Soll 3, 1 Zeile ohne Wort, wie erwartet.
- Rückweg-Probe (rollback-word.tsv, ein Wort, Soll 1): nichts zu tun, sie nutzt nur search_crosscheck und vergleicht mit 1.

**2. upgrade/native: "a catch-up round swept before phase A".** Befund zur Catch-up-Marke unter 1.6.2, am Tag v1.6.2 gelesen:
- Schlüssel `recheck_1_5_0` (CATCHUP_MARK, store/repo.py:194), Werte leer, Cursor-Ziffern, `reconcile`, `done` (CATCHUP_DONE).
- 1.6.2 fährt die Runde auch bei FINDLING_RECONCILE_ENABLED=false (main.py:1277-1282, once-Task): Teil A im Poller bei verdicts-Generation 3 (1.6.2-Companion meldet 3, ProfileController.php:53) und nach `recheck_1_4_0`; Teil B eine Abgleichsrunde hinter dem Ruhetor (Crawl vorbei, weniger als RECONCILE_QUIET_MAX = 100 offene Zeilen), die once-Task schaut alle RECONCILE_TICK_SECONDS = 300 s nach der Marke. 1.6.2 kann sie also fertigstellen, sie hatte im Job nur nicht genug Zeit.
- 1.6.2 fegt in dieser Runde auch (reconcile.py, Schritt 5), schreibt aber kein `storage_sweep_at` (SWEEP_MARK gibt es erst im Kopf). W5 behält damit seine Bedeutung für alle Beine: es fängt nur einen Feger des Kopfes vor Phase A.
- Fix: im upgrade-Bein nach dem ersten drain und vor der verwaisten Zeile warten, bis `recheck_1_5_0` = `done` ist (Schlüssel und Wert aus `${SRC}/backend/src/findling/store/repo.py` gelesen), hart `CATCHUP_TIMEOUT=900` (zwei Ticks, die Runde, Puffer), sonst fail mit Schlüssel und aktuellem Wert. Danach ein drain (die Runde kann Zeilen zurückgeben) und die Prüfung, dass unter 1.6.2 kein `storage_sweep_at` steht. note und Tabellenzeile mit der Wartezeit. Der Guard W5 bleibt unverändert.
- Warum vor der verwaisten Zeile: der Catch-up-Gang hätte verwaist.txt als verschwunden gewertet. Im selben Lauf meldete /coverage nach dem Backfill docKeysUnresolved 0 statt mindestens 1 (Warnung, failures+1); wahrscheinliche Ursache, unbelegt: die Catch-up-Runde des Kopfes hat die verwaiste Zeile vorher zum Grabstein gemacht (Backfill done=48 bei 53 lebenden Zeilen vor dem Update).

**Grenzen der Runde:**
- Gibt die 1.6.2-Runde die Zeilen failed(gateway_error) der gesperrten Dateien neu aus (Restbudget), steigt attempts unter 1.6.2 um eins mehr; reicht danach das Budget für die Neuvergabe durch den Kopf in Phase B nicht, scheitert judge_locked "upgrade after phase B". Das wäre ein Befund, keine Lockerung.
- Schafft 1.6.2 die Runde nicht in 900 s, bricht das Bein mit klarer Meldung ab. Saubere Alternative, nicht umgesetzt: vor dem Start des Kopfes `recheck_1_5_0` von Hand auf `done` setzen (1.6.2 selbst sieht das vor, reconcile.py:756 "a hand set CATCHUP_DONE ends the second chance at once"); Begründung: der Test misst die Kopf-Runde aus 43-02, nicht den Abschluss der 1.5-Nachholung.

**Tests der Runde:** `bash -n` beider Skripte grün; shellcheck lokal nicht verfügbar; test_workflow_pins, test_workflow_contexts, test_workflow_size, test_workflow_tag_triggers, test_measurement_scripts, test_ops_scripts 756 passed. Harness nicht lokal gelaufen; Beleg erst im nächsten freigegebenen Dispatch.

## Threat Flags

Keine neue Angriffsfläche: keine Route, kein Schlüssel, keine Schemaänderung; die Probe- und Urteilszeilen tragen nur Status, Sekunden, Bytes, Datei-IDs.

## Known Stubs

Keine.

## Self-Check: PASSED

- Dateien vorhanden: alle unter key-files.modified.
- Commits vorhanden: 6dc71363, ba4b9398, 7ef3bc9b.
