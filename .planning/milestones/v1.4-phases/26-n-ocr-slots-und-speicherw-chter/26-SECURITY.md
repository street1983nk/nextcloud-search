---
phase: 26
slug: n-ocr-slots-und-speicherwaechter
status: verified
threats_total: 48
threats_closed: 48
threats_open: 0
asvs_level: 1
block_on: high
register_authored_at_plan_time: true
created: 2026-09-29
---

# Phase 26: Security

> Sicherheitsvertrag der Phase: Bedrohungsregister, akzeptierte Risiken, Prüfpfad.
> Jede Mitigation ist am Code belegt (Datei:Zeile) und, wo der Plan einen Test verlangt, am Testnamen; SUMMARY-Behauptungen gelten nicht als Beleg.
> Stand nach den Review-Fixes CR-01 (91fefe8f), WR-01 (777f3a59) und WR-02 (15eb03d5), HEAD 17813972.
> Pfade ohne Präfix liegen unter `backend/src/findling/`, Tests unter `backend/tests/`.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Fremdbytes -> Parser im Kind | präparierte Dateien treffen auf C-Bibliotheken, nur im gehärteten Kind | Dateiinhalte |
| Kernel-OOM-Killer -> Prozesse des Containers | wen der Kernel tötet, entscheidet über Absturzschleife oder Solo-Wiederholung | SIGKILL, Exitcodes |
| appconfig (Admin, occ) -> Profilroute -> Container | nur Admins schreiben appconfig; der Container liest den Token | Bestätigungs-Token (32 Hex) |
| Container -> Anspruch (claim) | Container verlangt Zeilen je Lane, PHP verteilt | Lane, Zeilenzahl je Art |
| cgroupfs -> Wächterlogik | Zähler, die fehlen, kaputt oder zurückgesetzt sein können | memory.events, anon-Headroom |
| Pool-Threads -> Index-Writer, Default-Executor | N Threads schreiben in ein nicht threadsicheres Rust-Objekt; Wartezeiten dürfen die Suche nicht aushungern | Dokumente, Threads |
| Warteschlange (Companion) <-> Poller | Anspruch, Rückgabe und Quittung unter Parallelität | Queue-Ids, Verdikte |
| zwei Einbettungs-Tasks <-> geteilte Engine und Verbindungen | Nebenläufigkeit innerhalb der Einbettungsspur | Chunks, ACL |
| state.db meta -> Start | persistierte Werte bestimmen die wirksame Stufe nach einem Neustart | Kappe, Ursache, Token, Merker |
| Container -> Admin (GET /status, Adminseite) | Betriebsdaten werden im Admin-Browser gerendert | Stufe, Ursache, Token, Slotzahlen |
| Testprozess <-> Harness und Kinder | Signale an echte Prozesse im CI-Runner | SIGKILL, pids.json |
| CI-Workflow -> Abbild, Messaufbau -> Repository | Messläufe ohne Netz, Messergebnisse werden committet | synthetische Scans, Zahlen |
| lokales Repository -> öffentliches GitHub | ein Push macht den Stand öffentlich | Commits |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status | Evidence |
|-----------|----------|-----------|-------------|------------|--------|----------|
| T-26-01 | EoP | _child_main | mitigate | Reihenfolge setsid, nice, oom_score_adj, Geheimnisabwurf, RLIMIT_AS, Pool-Pinning, dann Dispatcher-Import; Reihenfolge-Test | closed | extract/sandbox.py:315 (`os.setsid()`), :321 (`os.nice(SANDBOX_NICE)`), :322 (`_lower_own_standing()`), :323 (`_shed_secrets()`), :324 (`_limit_address_space`), :328 (`_pin_native_thread_pools()`), :330 (Dispatcher-Import); tests/test_sandbox.py:560 `test_the_child_hardens_itself_before_the_parsers_load`, :569 `test_the_child_lowers_itself_before_anything_else_happens` (Quelltext-Reihenfolge per `body.index`), :547 `test_shedding_removes_every_appapi_credential` |
| T-26-02 | DoS | Hauptprozess als OOM-Opfer | mitigate | oom_score_adj 1000 in jedem Kind, best effort | closed | extract/sandbox.py:210-211 (`write_text("1000")` unter `contextlib.suppress(OSError)`); tests/test_sandbox.py:604 `test_lowering_the_own_standing_writes_both_values`, :594 `..._swallows_an_unwritable_proc`, :627 `test_the_child_reports_its_own_standing` (score 1000 im echten Kind), :581 `test_the_main_process_never_lowers_itself` |
| T-26-03 | Tampering | Endverdikt nach Fremd-Kill | mitigate | ChildKilled statt failed(corrupt/ocr_failed); exitcode vor _recycle gelesen; Timeout- und Halt-Kill ausgenommen | closed | extract/sandbox.py:579-583 (`_bury`: join, `exitcode == KILLED_EXIT_CODE and not self._halted` vor `_recycle`), :543-556 (Deadline-Pfad kehrt vor `_bury` mit TIMEOUT zurück), :508 (halt setzt Flag vor dem Kill), :606 und :628-629 (CR-01-Fix: Flag vor `process.start()`, Recheck danach); extract/ocr.py:215-221 (tesseract SIGKILL -> `EngineKilled`); tests/test_sandbox.py:362 `test_a_child_killed_from_outside_is_no_verdict`, :411 `test_a_halt_from_another_thread_is_the_modules_own_kill`, :440 `test_a_halt_into_the_start_window_kills_the_new_child_and_keeps_the_verdict`; tests/test_ocr.py:357, :379, :388, :395 |
| T-26-04 | Repudiation | Reason in der Quittung | mitigate | kein neuer Reason-Code, Ausnahme statt Verdikt | closed | extract/errors.py:44 (`class ChildKilled(Exception)`), :67 (`EngineKilled`), keine Reason-Erweiterung; tests/test_sandbox.py:505 `test_a_killed_child_carries_no_reason_code` (kein Reason enthält "kill") |
| T-26-05 | Tampering | profileConfirmed | mitigate | nur 32 Kleinbuchstaben-Hex, sonst null plus reject() | closed | php/lib/Service/SettingsService.php:368-388 (`preg_match('/^[0-9a-f]{32}$/D')`, sonst `reject()` und `return null`); php/lib/Controller/ProfileController.php:76; php/tests/Unit/ProfileControllerTest.php:212, :225, :252 `testATokenOutsideTheFormIsNullAndIsNotLogged` (nicht hex, 31, 33, Großbuchstaben, Trailing-Newline), :273 |
| T-26-06 | DoS | OCR-Anspruch im Lane all | mitigate | 32 nur im Lane index, Lane all bleibt 2 | closed | php/lib/Service/QueueService.php:194 (`KIND_BATCH[KIND_OCR] => 2`), :221 (`KIND_BATCH_INDEX_LANE[KIND_OCR] => 32`), :309-311 (Index-Decke nur bei `$lane === self::LANE_INDEX`); php/tests/Unit/QueueServiceTest.php:276 `testTheIndexLaneAsksForUpToThirtyTwoOcrRows`, :283 `testTheAllLaneStillAsksForTwoOcrRows`, :290 `testTheEmbedLaneIsUntouched`, :311 |
| T-26-07 | EoP | Profilroute | accept | siehe AR-26-01 | closed | Annahme am Code bestätigt: ProfileController.php:63 (`ExAppRequired`), :67 (`rejectForeignCaller()` erste Anweisung), :97-110 (EX-APP-ID gegen BACKEND_APP_ID, sonst 403); Route nur GET (:65) |
| T-26-08 | DoS | Fehlalarm durch memory.events max | mitigate | qualifiziertes Ereignis (Δmax und Headroom unter 235 MiB), Mindestabstand 60 s, Fenster 600 s | closed | guard.py:129-155 (`Escalation.observe`: `rise_max == 0 or headroom is None or headroom >= self._reserve` -> kein Ereignis, Fenster, min_gap); config.py:889, :928 (235 MiB), :933 (600), :937 (60); tests/test_guard.py:114 `test_a_rising_max_with_room_to_spare_is_never_an_event`, :123, :131, :139, :147, :186 |
| T-26-09 | DoS | zu viele Slots | mitigate | throttled_slots gegen headroom_bytes, unlesbar ein Slot | closed | guard.py:97-105 (`headroom is None` -> 1); tests/test_guard.py:90 `test_the_throttle_keeps_slot_one_always`, :97 |
| T-26-10 | Tampering | restore/note_confirmation | mitigate | geschlossene Mengen, Token 32 Hex, chosen None ändert nichts | closed | guard.py:52 (CAUSES), :68 (`_TOKEN_PATTERN`), :214-229 (restore prüft PROFILE_NAMES, CAUSES, Token, endliche Zeit), :236-250 (note_confirmation: chosen None/fremd -> False, `compare_digest` nur nach Formprüfung); tests/test_guard.py:337 `test_restore_drops_foreign_words`, :271, :289 `test_a_chosen_profile_that_was_not_read_changes_nothing`, :240 |
| T-26-11 | Info Disclosure | Token und Ursache in Logs | mitigate | guard.py loggt nichts (grep-Kriterium) | closed | `grep -cE "LOGGER\|logging\|print(" guard.py` = 0 (Plan 26-03:159). Siehe Hinweis 1 |
| T-26-12 | Tampering | IndexBatchWriter unter N Threads | mitigate | RLock um schreibende Methoden und Zähler | closed | index/writer.py:184 (`threading.RLock()`), :219, :253, :279 (add), :366 (drop_document), :421 (flush), :446, :456; tests/test_index_writer.py:730 `test_eight_threads_writing_the_same_id_leave_exactly_one_document`, :709 |
| T-26-13 | DoS | Default-Executor | mitigate | eigener ThreadPoolExecutor "findling-slot", kein to_thread im Pool | closed | extract/pool.py:167 (`ThreadPoolExecutor(..., thread_name_prefix="findling-slot")`), :169 (`run_in_executor(executor, ...)`), kein `to_thread`-Aufruf im Modul; tests/test_pool.py:215 `test_call_runs_in_the_pools_own_executor`; tests/test_poller.py:3951 `test_every_extraction_runs_in_the_threads_of_the_pool` |
| T-26-14 | EoP | N Kinder vergrößern Parserfläche | mitigate | jedes Kind ein unveränderter ExtractionWorker, Pool importiert keinen Parser | closed | extract/pool.py:46-47 (einzige Importe errors und sandbox), :113 (`worker_factory = ExtractionWorker`); tests/test_pool.py:262 `test_importing_the_pool_does_not_load_the_dispatcher` |
| T-26-15 | Tampering | guard-Felder aus dem Container | mitigate | geschlossene Mengen, Token 32 Hex, Zähler nicht negativ, Flag nur bool | closed | php/lib/Service/AdminViewService.php:198, :207 (Mengen), :1926-1940 (jedes Feld durch Prüfer), :2069, :2079, :2091 (`hexToken`, `/D`), :2102 (`guardCounter` >= 0), :2042 (`is_bool`); php/tests/Unit/AdminViewServiceTest.php:382, :390, :444 `testAGuardValueOutsideItsSetIsRefused` |
| T-26-16 | Spoofing (XSS) | Seitentext aus Container | mitigate | Anzeigewörter nur aus PHP-Maps und Katalogen, Ausgabe escaped | closed | php/templates/admin.php:277-295 (`$causeNames[...]`, `$profileNames[...]`, nur Maps), :531-533 (Ausgabe ausschließlich über `p()`); tests/test_admin_ui_contract.py:2785 `test_no_catalogue_value_can_break_the_page`, :2238 `test_the_guard_lines_are_built_out_of_closed_sets` |
| T-26-17 | Info Disclosure | Token auf der Adminseite | accept | siehe AR-26-02 | closed | Annahme am Code bestätigt: php/appinfo/info.xml:296 (nur `<admin>`-Settings); backend/appinfo/info.xml:308-310 (/status ADMIN) |
| T-26-18 | DoS | Zeilen über dem Lease | mitigate | Beschnitt auf 2 je Slot mit sofortigem unlock | closed | worker/poller.py:981-990 (`ocr_rows_to_keep`, Überschuss per `queue.unlock` vor jeder Extraktion); config.py:479, :496, :499; tests/test_poller.py:3906 `test_rows_beyond_two_per_slot_go_back_before_the_first_extraction`, :3929 |
| T-26-19 | Tampering | doppelte Indexierung unter N Slots | mitigate | Upsert unter Writer-Sperre, ein Commit je Staffel | closed | worker/poller.py:1576 (`self._pool.call(self._writer_or_die().add, ...)`, Upsert unter RLock aus T-26-12), :1073 (ein `flush` nach der Barriere); tests/test_poller.py:3875 `test_four_slots_read_eight_scans_four_at_a_time_and_index_each_once`; tests/test_slots_kill.py:171, :212 (echter SIGKILL, genau einmal im Index; Linux-CI-Lauf 36522819711 grün) |
| T-26-20 | Tampering | verschachtelte SQLite-Transaktionen | mitigate | _scan ohne Store, _judge_scan und _record_verdicts im Loop-Thread nach der Barriere | closed | worker/poller.py:1287-1298 (`_scan_in_a_slot` -> `_scan`, nur Pool und Writer), :1538-1610 (`_scan` ohne Store-Zugriff), :1215 (Barriere `gather`), :1235 (`_judge_scan` danach), :1083 (`_record_verdicts` nach dem Commit); Test mit echter state.db: tests/test_poller.py:3875. Siehe Hinweis 2 |
| T-26-21 | Spoofing | confirmed-Feld der Companion-Antwort | mitigate | fullmatch 32 Kleinbuchstaben-Hex, sonst None | closed | nc/queue.py:60 (`_TOKEN_PATTERN`), :585 (`isinstance(str) and fullmatch`, sonst None); tests/test_queue_client.py:581, :604 `test_a_malformed_confirmation_token_reads_as_none`, :614 |
| T-26-22 | Info Disclosure | neue Log-Felder | mitigate | nur Zähler (slots=%d) | closed | worker/poller.py:1123-1136 (nur `%d`-Felder); tests/test_poller.py:4074 `test_the_pass_line_carries_the_slots_and_nothing_about_a_file`, :2666 `test_no_log_call_names_a_path_a_title_or_a_piece_of_text` |
| T-26-23 | Tampering | verschachtelte Transaktionen vectors.db/state.db | mitigate | asyncio.Lock um replace_acl und replace_chunks | closed | worker/embedding.py:388 (`_write_lock = asyncio.Lock()`), :591-592 (replace_acl), :633-634 (replace_chunks), :379 (Chunker-Lock); tests/test_embedding_track.py:975 `test_two_rows_at_once_leave_one_chunk_set_each_in_real_databases`, :1028, :1001 |
| T-26-24 | DoS | Zeilen ohne Quittung nach Fehler | mitigate | _abort-Semantik nach der Barriere, unlock aller Zeilen | closed | worker/embedding.py:1599-1617 (gather, dann bei `sqlite3.Error`/`_DiskTight` `unlock_held()` ohne Verdikt), :1513, :1555 (run unlockt bei allem anderen); tests/test_embedding_runner.py:645 `test_a_store_error_in_one_of_two_rows_hands_every_row_back_without_a_verdict`, :674 |
| T-26-25 | DoS | Engine-Freigabe während einer Zeile | mitigate | idle-Guard unverändert, Test mit zwei Zeilen | closed | worker/embedding.py:1428, :1463, :1500-1504 (`_in_flight`); tests/test_embedding_track.py:1068 `test_the_idle_guards_let_go_only_after_both_rows_are_done` |
| T-26-26 | Info Disclosure | Token und Ursache in /status | accept | siehe AR-26-03 | closed | Annahme am Code bestätigt: backend/appinfo/info.xml:308-310 (`^/status$`, ADMIN); api/status.py:420-440 (nur Wörter, Zahlen, Token; keine Pfade) |
| T-26-27 | DoS | Statusroute | mitigate | reiner Leser über Snapshots | closed | api/status.py:420-440 (`guard.snapshot()`, `snapshot()`, kein Datei- oder Kernelzugriff); tests/test_status_endpoint.py:1526 `test_asking_for_the_guard_reads_no_kernel_counter` (memory_guard gepatcht auf `pytest.fail`) |
| T-26-28 | Tampering | Vertragsdrift Container/PHP | mitigate | Vertragstest mit Rot-Probe | closed | tests/test_admin_ui_contract.py:2304 `test_every_guard_field_the_service_reads_is_sent_by_the_container`, :2315, :2321 `test_a_guard_field_the_container_does_not_send_is_a_finding` (Rot-Probe) |
| T-26-29 | DoS | präparierte Datei erzwingt OOMs | mitigate | Solo-Wiederholung einmal, zweiter Kill = out_of_memory; jede Kill-Meldung senkt | closed | worker/poller.py:1236-1244 (Gate auf 1, Solo mit `_OnKill.OUT_OF_MEMORY`), :1604-1609 (zweiter Tod -> `failed(OUT_OF_MEMORY)`), :1210, :1297 (`report_child_kill`); guard.py:133-135 (Kill -> OOM_KILL sofort); tests/test_poller.py:4442 `test_a_scan_that_dies_alone_as_well_ends_as_out_of_memory` (5 geplante Kills, genau 2 Extraktionen), :4479; tests/test_guard.py:172 |
| T-26-30 | Tampering | Dateiverlust nach Fremd-Kill | mitigate | kein Verdikt beim ersten Kill, Solo vor dem Commit | closed | worker/poller.py:1231-1244 (Killed ohne `_judge_scan`, Solo vor `flush` :1073); tests/test_poller.py:4418 `test_a_scan_killed_beside_others_runs_again_alone_and_is_indexed`, :4461; tests/test_slots_kill.py:212 |
| T-26-31 | DoS | Speicherdruck durch Kinder | mitigate | throttled_slots je Runde, unlesbar ein Slot | closed | worker/poller.py:975-980 (Headroom je Staffel ab Ziel 2); tests/test_poller.py:4125 `test_a_short_headroom_throttles_four_slots_to_three_and_keeps_six_rows`, :4157 `test_an_unreadable_headroom_means_one_slot_and_two_rows`, :4176 |
| T-26-32 | Repudiation | Absturz ohne Spur | mitigate | multi_slot_pass vor der ersten Task, nach der Barriere gelöscht | closed | worker/poller.py:1051-1055 (Merker vor `_read_in_slots`, Löschen im finally), :1249-1283 (WR-02: CHOSEN zuerst, PASS als Commit-Punkt, beide geleert); tests/test_poller.py:4252 (zweite Verbindung), :4279 `test_the_pass_mark_is_written_last_and_cleared_first`, :4318, :4341 |
| T-26-33 | DoS | Absturzschleife nach OOM-Kill | mitigate | persistierte Absenkung plus Unrein-Ende-Merker, restore vor der ersten Poller-Runde | closed | worker/watch.py:168-198 (restore, unclean_end aus META_MULTI_SLOT_PASS), :159-163 (Persistenz); main.py:896-898 (restore) vor :915 (Poller-Task); tests/test_watch.py:124, :153 `test_restore_answers_an_unclean_end_with_a_lowering`; tests/test_main_lifespan.py:1619 `test_the_guard_restores_after_the_hardware_and_before_the_poller`; tests/test_slots_kill.py:171 |
| T-26-34 | Tampering | manipulierte meta-Werte | mitigate | guard.restore validiert gegen geschlossene Mengen | closed | worker/watch.py:177-182 (alles über `guard.restore`), :68-72 (`_level` gegen PROFILE_NAMES für den Merker); guard.py:214-229; tests/test_guard.py:337 `test_restore_drops_foreign_words`; tests/test_watch.py:175 |
| T-26-35 | DoS | Fehlalarm bei Updates | mitigate | note_shutdown_begins als erste Handlung im finally | closed | main.py:1032-1040 (erste Anweisung im finally, vor `stop_indexing.set()`); worker/watch.py:229-241; tests/test_main_lifespan.py:1665 `test_the_pass_mark_is_the_first_statement_of_the_finally`, :1651; tests/test_watch.py:297. Siehe Hinweis 3 |
| T-26-36 | Info Disclosure | Logs | mitigate | nur Ursachencode, Stufe und Typnamen, kein Token | closed | worker/watch.py:209, :225, :241, :254 (einzige LOGGER-Aufrufe: Ursache, Stufe, `type(error).__name__`); main.py:900; tests/test_watch.py:334 `test_the_lowering_line_carries_cause_and_level_and_no_token` |
| T-26-37 | DoS | hängender CI-Job | mitigate | harte Fristen, finally mit killpg der pids | closed | tests/test_slots_kill.py:74-75 (WAIT 20 s, RUN 25 s), :95, :114-119 (Fristen), :137-150 (`_reaped`: finally, `os.killpg` je pid aus pids.json) |
| T-26-38 | Tampering | Harness weicht von PHP ab | mitigate | KIND_BATCH aus config, retries/unlock/Quittung nach PHP-Regeln, Lease explizit | closed | tests/slots_kill_harness.py:124-127 (Decken aus paritätsgepinnter config), :146-148 (MAX_DELIVERIES aus dem PHP-Quelltext), :240-259 (Lease, retries + 1), :266-271 (unlock, retries - 1) |
| T-26-39 | Info Disclosure | Testdaten | accept | siehe AR-26-04 | closed | Annahme bestätigt: Harness erzeugt nur synthetische Dateien im tmp_path |
| T-26-40 | Tampering | Action-Pins | mitigate | keine Pin-Änderung, test_workflow_pins grün | closed | `git diff f230c290~1 HEAD -- .github/workflows/` ohne geänderte `uses:`-Zeile; .github/workflows/measure.yml:440, :443, :754 (SHA-Pins); tests/test_workflow_pins.py grün (lokaler Lauf) |
| T-26-41 | Info Disclosure | Messausgaben und Artefakte | mitigate | synthetische Scans, Ausgabe ohne Pfade/Texte, --network none | closed | .github/workflows/measure.yml:522, :544, :578, :594, :610, :680 (`--network none` im Job slots); tests/test_slot_ladder.py:101 `test_the_report_names_no_file_and_quotes_no_text`; docs/measurements/2026-09-slot-leiter-ci/ ohne Geheimnis (grep) |
| T-26-42 | Repudiation | geschönte Messbewertung | mitigate | feste Schwelle 1,05, "unbestimmt" und exit 1, Rohdaten als Artefakt | closed | .github/workflows/measure.yml:701-704 (`noise=1.05`), :730-732 (`ladder unbestimmt`, exit 1), :661-663, :754 (upload-artifact); tests/test_slot_ladder.py:67 `test_the_median_is_undetermined_after_a_lost_scan` |
| T-26-43 | Info Disclosure | Zugangsdaten in Ausgaben/Commit | mitigate | Zugang nur über Umgebungsvariablen, Test gegen Ausgabe, grep auf den Messordner | closed | scripts/ops/latency_probe.py:62, :107-111 (nur `os.environ`), :188 (Ausgabe nur `report_line`); tests/test_latency_probe.py:103 `test_credentials_never_reach_the_output`, :127; `grep -riE "password\|secret\|token\|authorization"` auf docs/measurements/2026-09-nice-latenz/ ohne Treffer |
| T-26-44 | Info Disclosure | Suchtreffer im Commit | mitigate | synthetischer Korpus, nur Latenzen und Zähler | closed | docs/measurements/2026-09-nice-latenz/raw/A-search.txt (nur Abbild, Zeiten, p50/p95/max, Fehlerzahl); tests/test_latency_probe.py:49 `test_report_line_carries_only_figures` |
| T-26-45 | Repudiation | überzogene Issue-Antwort | mitigate | README nennt cgroup-Grenze, Antwort nur nach Owner-Freigabe | closed | docs/measurements/2026-09-nice-latenz/README.md:30 (nice wirkt nur innerhalb derselben cgroup, status.php profitiert nicht); 26-13-SUMMARY.md:71 (nichts auf Issue #19 gepostet, kein Entwurf ohne Auftrag) |
| T-26-46 | Info Disclosure | ungewollter Push | mitigate | Push nur nach Owner-Entscheid | closed | 26-14-SUMMARY.md:49-52 (Owner-Signal wörtlich "Ja, jetzt pushen (Empfohlen)", Push `cce78abd..d91305df`, Folgecommits lokal); `git status -sb` zeigt main 13 Commits vor origin, also kein weiterer Push. Siehe Hinweis 4 |
| T-26-47 | Repudiation | offene Belege als erledigt | mitigate | stay-local listet offene Belege als human_needed, Abnahme-Checkpoint | closed | 26-14-PLAN.md:80-83, :107, :115 (stay-local-Pfad); gewählt wurde push-now, die Belege liegen als CI-Lauf-IDs vor und sind in 26-VERIFICATION.md unabhängig per `gh run view` bestätigt (36522819711, 36523219615, 36522819728); Abnahme 26-14-SUMMARY.md:103-105 |
| T-26-48 | Info Disclosure | Messartefakte | accept | siehe AR-26-05 | closed | Annahme bestätigt: docs/measurements/2026-09-slot-leiter-ci/ ohne Geheimnis und ohne Nutzerpfad (grep) |

*Status: open, closed. Disposition: mitigate (Umsetzung nötig), accept (dokumentiertes Risiko), transfer (Dritter).*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-26-01 | T-26-07 | Die Profilroute bleibt ExAppRequired mit `rejectForeignCaller` als erster Anweisung; der Token hat keine Wirkung außer dem Aufheben einer Absenkung, und das ist die sichere Richtung nur nach Admin-Handlung (occ). Am Code bestätigt: ProfileController.php:63, :67, :97-110. | Owner (Plan 26-02, Register zur Planzeit) | 2026-09-29 |
| AR-26-02 | T-26-17 | Der Token steht auf der Adminseite; Seite und /status sind Admin-only, der Token wirkt nur als Rückweg-Bestätigung nach einer Absenkung. Am Code bestätigt: php/appinfo/info.xml:296, backend/appinfo/info.xml:310. | Owner (Plan 26-05, Register zur Planzeit) | 2026-09-29 |
| AR-26-03 | T-26-26 | GET /status trägt Token und Ursache; die Route bleibt access_level ADMIN, keine Pfade, keine Inhalte. Am Code bestätigt: backend/appinfo/info.xml:308-310, api/status.py:420-440. | Owner (Plan 26-08, Register zur Planzeit) | 2026-09-29 |
| AR-26-04 | T-26-39 | Der Kill-Harness arbeitet nur mit synthetischen Dateien und Texten im tmp_path, keine Nutzerdaten. | Owner (Plan 26-11, Register zur Planzeit) | 2026-09-29 |
| AR-26-05 | T-26-48 | Die Messartefakte der Leiter enthalten nur synthetischen Korpus und Zahlen. Am Artefakt per grep bestätigt. | Owner (Plan 26-14, Register zur Planzeit) | 2026-09-29 |

*Akzeptierte Risiken tauchen in späteren Audits nicht erneut auf. AR-26-01 bis AR-26-03 hängen am Rückweg per occ: entsteht in Phase 27 eine Schreibroute für Profil oder Token, verfällt die Begründung.*

---

## Unregistered Flags

Keine. Die Threat-Flags-Abschnitte in 26-01, 26-03 bis 26-12 und 26-14-SUMMARY.md melden keine neue Fläche und verweisen nur auf registrierte IDs; 26-02 und 26-13-SUMMARY.md haben keinen Threat-Flags-Abschnitt.

## Hinweise (informativ, keine Blocker)

1. **T-26-11:** Der Plan verlangt ein grep-Kriterium, keinen Test. Der grep ist erfüllt (0 Treffer), ein automatischer Test, der ein späteres Logging in guard.py verhindert, fehlt. Die Aufrufer, die loggen (watch.py), sind durch T-26-36 und tests/test_watch.py:334 abgedeckt.
2. **T-26-20:** Die Mitigation ist strukturell (Tasks berühren nur Pool und Writer, Store-Zugriffe nach der Barriere im Loop-Thread). Es gibt keinen eigenen Test, der einen Store-Zugriff aus einer Task gezielt als Fehler meldet; der Nachweis ist die Code-Lesung plus die Slot-Tests gegen eine echte state.db.
3. **T-26-35 / IN-04:** Das Leeren des Merkers ist die erste Anweisung im finally (belegt), aber der Poller kann während dieses Awaits noch eine neue Mehr-Slot-Staffel beginnen, bevor `stop_indexing` gesetzt ist. Folge im schlechtesten Fall: eine unnötige Absenkung (sichere Richtung) nach einem Update. Laut 26-REVIEW.md bewusst offen.
4. **T-26-46:** Die Owner-Entscheidung ist nur über das SUMMARY belegt (vom Orchestrator übermittelt), nicht über ein eigenes Owner-Protokoll.
5. **Review-Fixes geprüft:** CR-01 (sandbox.py:606, :628-629, Test :440), WR-01 (poller.py:819-824, Test test_poller.py:2538), WR-02 (poller.py:1266-1267 und :1282-1283, watch.py:196, :238, Test :4279). IN-01 bis IN-04 bleiben offen dokumentiert, keiner berührt eine registrierte Mitigation außer IN-04 (Hinweis 3).
6. PHP-Belege (T-26-05/06/07/15/16/17) per Quelltext und Unit-Test-Inspektion geprüft; PHPUnit läuft nur in CI (Lauf 36522819728 grün laut 26-VERIFICATION.md). tests/test_slots_kill.py läuft nur unter Linux und war lokal (Windows) übersprungen; Beleg ist Lauf 36522819711.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-29 | 48 | 48 | 0 | gsd-security-auditor (Belege per grep/Read an HEAD 17813972; 15 Python-Testdateien: 540 passed, 19 skipped; Auswahl aus test_poller/test_main_lifespan/test_config: 248 passed, 1 skipped) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-29
