---
phase: 27
slug: vorab-pruefung-und-settings-oberflaeche
status: verified
threats_total: 50
threats_closed: 50
threats_open: 0
asvs_level: 1
block_on: high
register_authored_at_plan_time: true
created: 2026-09-29
---

# Phase 27: Security

> Sicherheitsvertrag der Phase: Bedrohungsregister, akzeptierte Risiken, Prüfpfad.
> Jede Mitigation ist am Code belegt (Datei:Zeile) und, wo der Plan einen Test oder ein Gate verlangt, am Testnamen; SUMMARY-Behauptungen gelten nicht als Beleg.
> Stand nach den 12 Review-Fixes 918f340d bis d25c85e8 (CR-01, WR-01 bis WR-11), HEAD ad747494. Seit c87a0239 (CI-Stand) ist unter `php/`, `backend/` und `.github/` nichts geändert (`git diff --stat c87a0239 HEAD` leer).
> CI unabhängig per `gh run view` bestätigt: PHP and store metadata gates 36596834116 success, Integration 36596834631 success (Schritt "A user who is not an admin reaches neither the probe nor the profile route" success), HaRP deploy 36596834148 success, alle auf c87a0239.
> Pfade ohne Präfix liegen unter `backend/src/findling/`, Python-Tests unter `backend/tests/`, PHP-Tests unter `php/tests/Unit/`.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Browser -> PHP-Routen | untrusted Werte und Aufrufer; Admin-Sitzung und requesttoken nötig | profile, precision |
| PHP (exAppRequest) -> Container-Routen | signierter AppAPI-Aufruf; das Access-Level der info.xml wird auf diesem Weg nicht geprüft | Ziel der Probe |
| Container -> PHP (Probe-Ergebnis) | Verdikt, Ursache, Id, Zahlen als untrusted Codes | Codes, Zahlen, 16-Hex-Id |
| PHP -> appconfig | einzige Schreibstellen für Profil, Präzision, Bestätigung | Profil, Präzision, Token (32 Hex) |
| appconfig profile_check -> Overview | per occ beschreibbar, also untrusted | gespeichertes Verdikt |
| Overview -> Browser (Initial State, Poll, DOM) | alles hier ist für den Admin sichtbar | Katalogsätze, Zahlen, bool guardConfirmable |
| Admin-Auftrag -> Container-Ressourcen | eine Probe bindet Speicher, CPU, Netz, hält Poller und Runner an | Pause, Kinder, Download |
| GitHub-Release -> models_dir | fp32-Datei aus dem Netz | 470268510 Bytes |
| Paketdatei -> Probe-Kind | die Scanseite wird im gehärteten Kind geparst | probe_scan.pdf |
| Probe-Kinder -> Hauptprozess, Kernel -> Wächter | Pipes, memory.events während der Probe | Messwerte, Kill-Ereignisse |
| Loop-Schreiber -> Thread-Leser | Wächter-Zustand wird aus to_thread gelesen | Kappe, Token |
| Messaufbau -> Repository, lokales Repository -> GitHub | Live-Protokolle werden committet, Push macht öffentlich | Codes, Zahlen, Commits |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status | Evidence |
|-----------|----------|-----------|-------------|------------|--------|----------|
| T-27-01 | Spoofing | Ursachencodes ohne Satz | mitigate | jede Ursache genau ein Satz, unbekannter Code blendet aus, Parität | closed | php/templates/admin.php:1054-1068 (13 Einträge `$probeCauseNames`, gleich den 13 `PROBE_CAUSES` in php/lib/Service/ProbeService.php:42), :1080 (`isset($probeCauseNames[...])`, sonst `''`), :1081-1086 (Satz mit fehlender Zahl bleibt verborgen); php/js/admin.js:1850-1862 (`hasOwnProperty`, sonst leer); tests/test_admin_ui_contract.py:2726 `test_the_script_and_the_template_name_every_probe_code_alike`; tests/test_probe_run.py:1035 `test_every_nofit_path_of_the_orchestrator_carries_the_figures_of_its_sentence` (CR-01) |
| T-27-02 | Repudiation | SC1-Wortlaut still geändert | mitigate | Owner-Checkpoint alt/neu, Signal wörtlich | closed | 27-01-SUMMARY.md:48-50 (Owner-Signal wörtlich "approved", 29.09.2026, für "Bei Sparsam bleiben" und sechs neue Sätze) |
| T-27-03 | Tampering | probe_scan.pdf im Image | mitigate | sha256 und Bytezahl gepinnt, Test, Digest vor Nutzung | closed | probe.py:114-115 (`PROBE_SCAN_SHA256`, `PROBE_SCAN_BYTES`); unabhängig nachgemessen: `sha256sum` = 320bb1aa...a81f3, `wc -c` = 79506; tests/test_probe.py:398 `test_the_scan_page_matches_its_pins`; Nutzung siehe T-27-29 |
| T-27-04 | Spoofing | freie Wörter im Probe-Zustand | mitigate | Setter werfen ValueError, decode verwirft fremde Felder | closed | probe.py:285-307, :336-340 (Setter `raise ValueError` für Schlüssel, Verdikt, Ursache, Id, Profil, Präzision, Schritt, Zähler), :440 (`foreign probe fields`), :447-457, :478 (`decode` -> None); tests/test_probe.py:286 `test_foreign_words_raise`, :342 `test_decode_drops_a_foreign_field_value` |
| T-27-05 | DoS | Probe selbst als OOM | mitigate | Vorab-Tore, unlesbarer Headroom nie zugelassen | closed | probe.py:256-258 (`first_slot_admitted`: `headroom is not None and ...`), :266-268 (`model_child_admitted` gleich); worker/probe_run.py:597-603, :669-673 (Tore vor jedem Kind); tests/test_probe.py:211 `test_the_gates_before_the_children`; tests/test_probe_run.py:907 `test_an_unreadable_headroom_starts_no_child`, :917, :925 |
| T-27-06 | Tampering | zerrissener Token-Snapshot (IN-01) | mitigate | eine unveränderliche Referenz, atomarer Austausch, Regressionstest | closed | guard.py:192 (`_STATE: _State`), :200-202 (`_set_cap` tauscht die Referenz per `replace`), :280-281, :300 (`snapshot` liest eine Referenz); tests/test_guard.py:392 `test_a_reader_thread_never_sees_a_torn_state` |
| T-27-07 | DoS | irreführender Fehlertyp im Shutdown (IN-02) | mitigate | Submit unter Sperre plus Übersetzung, Regressionstest | closed | extract/pool.py:174-184 (`with self._lock`, geschlossen -> `RuntimeError(_CLOSED)`, auch übersetzt aus dem Executor-Fehler :181-184); tests/test_pool.py:253 `test_a_closed_pool_refuses_further_calls` |
| T-27-08 | Tampering | saveProfile mit fremden Werten | mitigate | strict in_array im Service, fp32 in economy nur als Bestand | closed | php/lib/Service/SettingsService.php:555-566 (`validPair` strict, :727-728; economy+fp32 nur bei gespeichertem fp32), :103, :134 (geschlossene Mengen); php/tests/Unit/SettingsServiceTest.php (PHPUnit grün in 36596834116) |
| T-27-09 | EoP | Umgehung der Probe über Schreibweg | mitigate | needsProbe/isDownward serverseitig, Schreiben ohne Probe nur bei isDownward | closed | php/lib/Service/SettingsService.php:518-538; php/lib/Controller/ProfileSettingsController.php:108-112 (`!isDownward` -> 400 `probe_required`); einzige Aufrufer von `saveProfile`: ProfileSettingsController.php:114 und ProbeService.php:319 (grep über php/lib); php/tests/Unit/ProfileSettingsControllerTest.php:235 `testAnUpwardTargetNeedsTheProbe`; live raw/06-abwaerts.txt |
| T-27-10 | Info Disclosure | Logs des Transports | mitigate | statische Sätze mit Statuszahl | closed | php/lib/Service/ExAppService.php:691-741 (`adminOutcome`: nur statische Sätze, höchstens `status`), :753-769 (`bytes`); der Pfad-loggende `call()` (:873-966) wird von adminSend/adminState nicht benutzt (:673-689 rufen `proxyRequest` direkt, :801-815 loggt nicht) |
| T-27-11 | DoS | Indexierung dauerhaft pausiert | mitigate | eigenes Event, Freigabe im finally, Neustart ungehalten, Pause-Deckel 1800 s | closed | worker/poller.py:590-591 (`_probe_release` gesetzt beim Bau), :699-714; worker/embedding.py:1429-1430, :1456-1464; worker/probe_run.py:473-477 (finally hebt beide und `probe.release()`), :541-544 (Deckel -> `pause_timeout`); config.py:467, :947 (1800); tests/test_probe_run.py:437 `test_a_cancellation_lifts_the_hold`, :417, :407; tests/test_poller.py:2663 |
| T-27-12 | Tampering | Probe überschreibt Enable/Disable von AppAPI | mitigate | arm/silence unberührt, Test | closed | worker/poller.py:707-709 ("Arms nothing: a silenced poller stays silent", nur `_probe_release.set()`); tests/test_poller.py:2679 `test_a_probe_hold_neither_arms_nor_silences`; tests/test_embedding_runner.py:862 `test_a_probe_hold_of_the_runner_arms_nothing_and_stops_cleanly` |
| T-27-13 | DoS | Fehlabsenkung durch Probe-Kill | mitigate | Rebase plus verworfene Kills während Messung und einem Nachlauf-Tick | closed | worker/watch.py:214-227 (`probe.measuring()` oder `_probe_trailing` -> `rebase`, `take_child_kills()`); seit WR-09 (20041463) nur im Messteil: worker/probe_run.py:609 (`probe.measure()`), probe.py:516-531; tests/test_watch.py:284, :302 `test_the_first_tick_after_the_pre_check_is_suspended_as_well`, :327, :260 `test_a_kill_in_the_pass_the_pause_waits_for_still_lowers` |
| T-27-14 | EoP | Modell-Kind | mitigate | setsid, nice, oom_score_adj, secrets geschält vor schwerem Import | closed | embed/model_probe.py:61-67 (Import der Sandbox-Teile), :232-236 (`os.setsid()`, `os.nice`, `_lower_own_standing()`, `_shed_secrets()`), :240 (erster schwerer Import danach); tests/test_model_probe.py:142 `test_the_child_hardens_itself_before_anything_heavy_is_imported`, :173, :226 |
| T-27-15 | Tampering | ungeprüfte fp32-Datei geladen | mitigate | measure nur nach bestandenem Digest | closed | worker/probe_run.py:551-562 (vorhandene Datei: `fp32_verified`, sonst `digest_mismatch`), :580-587 (Download: nur `PROCURED` geht weiter), :528-531 (`_measure` erst nach `_weights`); embed/weights.py:130-155 (Größe und sha256), :254 (Download: Länge und Digest); tests/test_probe_run.py:523 `test_a_placed_file_with_another_digest_is_digest_mismatch_and_stays` |
| T-27-16 | DoS | hängendes oder speicherfressendes Kind | mitigate | Deadline mit Gruppenkill, Vorab-Tor, oom_score_adj 1000 | closed | embed/model_probe.py:300-312 (`_kill_child_tree` bei Deadline); worker/probe_run.py:669-673 (Tor `MODEL_PROBE_CHILD_BYTES` + Reserve); config.py:953; oom_score_adj über `_lower_own_standing` (T-26-02); tests/test_model_probe.py:191 `test_a_child_over_the_deadline_is_killed_and_reads_as_timeout`, :234 |
| T-27-17 | EoP | Nicht-Admin startet Probe oder speichert | mitigate | Plain Controller ohne Aufheber, Gate B mit Ratsche, Live-403 | closed | php/lib/Controller/ProfileSettingsController.php:41 (`extends Controller`), :65, :81, :93 (nur `FrontpageRoute`); grep `NoAdminRequired\|NoCSRFRequired\|PublicPage\|ExAppRequired\|SubAdminRequired\|AuthorizedAdminSetting` in der Datei: 0 Treffer; tests/test_php_trust_boundary.py:274 `test_every_route_of_every_controller_is_guarded`, :318-321 (Ratsche 16/15); live raw/07-nicht-admin.txt (4 x HTTP403, Profil vorher/nachher economy); CI Integration 36596834631 |
| T-27-18 | Tampering | CSRF auf Start, Stand und Speichern | mitigate | kein NoCSRFRequired, SecurityMiddleware prüft requesttoken auch bei GET | closed | ProfileSettingsController.php ohne `NoCSRFRequired` (grep 0); tests/test_php_trust_boundary.py:468 `test_no_csrf_required_on_an_admin_route_is_reported`; php/js/admin.js:207, :239 (`requesttoken` je Aufruf). Siehe Hinweis 2 |
| T-27-19 | Tampering | Browser behauptet "passt" | mitigate | Commit nur aus Container-Antwort, hash_equals-Id, gleiches Ziel; keine Route nimmt Verdikt | closed | php/lib/Service/ProbeService.php:421-428 (`matches`: done, `hash_equals`, beide Ziele), :318-319 (nur `VERDICT_FITS` und `unchangedSince`, WR-06), :306; Routen nehmen nur `profile`, `precision` (ProfileSettingsController.php:66, :94); php/tests/Unit/ProbeServiceTest.php:383 `testAFitsOfAnotherProbeSavesNothing`, :404, :324 `testAFitsDoesNotOverwriteASaveMadeWhileItRan`, :347. Siehe Flag F-1 (WR-07 adopt) |
| T-27-20 | Tampering | fremde Werte für Profil/Präzision | mitigate | strict in_array im Controller und im Service | closed | ProfileSettingsController.php:95, :122-128 (strict); ProbeService.php:98, :513-519 (erneut); SettingsService.php:556, :727-728 (dritte Prüfung); php/tests/Unit/ProfileSettingsControllerTest.php:140 `testAnInvalidCheckDoesNotReachTheContainer`, :255; php/tests/Unit/ProbeServiceTest.php:252 `testStartJudgesTheTargetAgain` |
| T-27-21 | Info Disclosure | Bestätigungs-Token | mitigate | nur serverseitig aus frischem /status, nach /D-Prüfung, nie an Browser, nie geloggt | closed | php/lib/Service/ProbeService.php:366-382 (`adminGet('/status')`, `hexToken`, nur bei `chosen === $profile`, Log-Satz ohne Wert); SettingsService.php:587-595 (`/^[0-9a-f]{32}$/D`); `state()`/`result()` (:202-279) ohne Token-Feld; php/tests/Unit/ProbeServiceTest.php:427, :452 |
| T-27-22 | Spoofing | Container-Wörter in der Seite | mitigate | alle Felder gegen PROBE_*-Mengen, Parität per Test | closed | ProbeService.php:39-43 (Mengen), :493-510 (`snapshot` je Feld über `member`, `counter`, `numbers`, `probeId`); tests/test_probe_php_parity.py:52 `test_the_php_set_equals_the_python_set`; php/tests/Unit/ProbeServiceTest.php:465 `testUnknownFieldsAreDropped`, :482 |
| T-27-23 | Info Disclosure | Token im Browser (AR-26-02 verfällt) | mitigate | guardToken entfernt, guardConfirmable als bool, Test | closed | php/lib/Service/AdminViewService.php:2263 (`'guardConfirmable' => self::hexToken(...) !== null`); grep `guardToken` in AdminViewService.php, admin.php, admin.js, Admin.php: 0 Treffer; tests/test_admin_ui_contract.py:2452 `test_the_token_never_reaches_the_browser` |
| T-27-24 | Spoofing | Container- oder appconfig-Wörter als Seitentext | mitigate | Richter je Feld, geschlossene Mengen, unbekannt verworfen | closed | php/lib/Service/AdminViewService.php:774-808 (`judgedCheck`: Profil, Präzision, Verdikt, Ursache gegen Mengen, Zahlen nur bekannte Schlüssel >= 0), :755-764; php/templates/admin.php:1080 (Anzeige nur über Map) |
| T-27-25 | Tampering | manipuliertes profile_check per occ | accept | siehe AR-27-01 | closed | Annahme am Code bestätigt: AdminViewService.php:774-808 und ProbeService.php:252-279 prüfen den gespeicherten Wert erneut; nur Anzeige, kein Schreibpfad liest ihn als Freigabe (Commit nur aus Container-Snapshot, ProbeService.php:306-319) |
| T-27-26 | DoS | Probe-Dauerfeuer, dauerhafte Pause | mitigate | Einzelflug mit Lock, drei Deckel, Freigabe im finally, Admin-only | closed | worker/probe_run.py:357, :419-421 (`_start_lock`, laufend -> `START_BUSY`), :541-544, :581, :612 (Deckel); config.py:938, :942, :947 (120/600/1800); :473-477 (finally); Admin-only siehe T-27-17; tests/test_probe_run.py:332 `test_a_second_start_while_running_is_busy`, :476 |
| T-27-27 | DoS | Probe selbst löst OOM aus | mitigate | Vorab-Tore vor jedem Kind, N-Lauf nur nach "fits", Kinder oom_score_adj 1000 | closed | worker/probe_run.py:620, :625 (`_admitted_headroom`), :669-673, :655-659 (N Kinder nur bei `VERDICT_FITS` und slots > 1); OCR-Kinder sind ExtractionWorker mit oom_score_adj 1000 (extract/sandbox.py, T-26-02); tests/test_probe_run.py:917, :925 |
| T-27-28 | Tampering | Download-Missbrauch | mitigate | feste URL, fester sha256 und Länge, einziger Netzweg fetch_release_asset | closed | embed/weights.py:52-58 (`FP32_SHA256`, `FP32_BYTES`, `FP32_ASSET_URL` konstant), :247 (`fetch(FP32_ASSET_URL, write, cap=FP32_BYTES)`), :254; worker/probe_run.py:94, :314 (Standard `fetch_release_asset`), :582; kein URL-Feld im Request (api/probe.py:65-71, `extra="forbid"`); nc/client.py `fetch_release_asset` nur https auf `ASSET_HOSTS`; tests/test_weights.py:92-127; kein httpx/urllib in probe_run.py, probe.py, api/probe.py (grep 0) |
| T-27-29 | Tampering | manipulierte Scanseite | mitigate | Digest gegen PROBE_SCAN_SHA256 vor jedem Lauf, sonst probe_failed | closed | worker/probe_run.py:627-632 (sha256 der gelesenen Bytes vor `_ocr`); tests/test_probe_run.py:1101 `test_a_scan_page_with_another_digest_is_probe_failed`, :1087 |
| T-27-30 | Info Disclosure | Logs und Ergebnis | mitigate | nur Codes, Zahlen, Typnamen; Id ist Zufall | closed | alle LOGGER-Aufrufe in worker/probe_run.py (:403, :410, :432, :470, :488, :503, :524, :631, :770, :826, :834, :843), api/probe.py:140, embed/model_probe.py:303: nur Codes und `type(error).__name__`; Id: worker/probe_run.py:424 (`secrets.token_hex(8)`) |
| T-27-31 | Spoofing (XSS) | Wörter im Markup | mitigate | nur Katalogsätze über PHP-Maps, Ausgabe nur mit p() | closed | php/templates/admin.php:1054-1097 (Sätze nur aus `$l->t` und Maps), :1224-1227 (`p(...)`); grep `<?=`/`echo`/`print_unescaped` in admin.php: 0 Treffer |
| T-27-32 | Info Disclosure | Token im Markup | mitigate | Way-back-Zeile samt Token entfernt, Gate | closed | admin.php:1005 (nur `guardConfirmable`); tests/test_admin_ui_contract.py:2452 (prüft `'token'`, `profile_confirmed`, `occ config:app:set` nicht im Template) |
| T-27-33 | Tampering | versteckter Erweitert-Bereich | mitigate | ADM-04-Gate: ein select, drei option, eine Checkbox, kein details/summary | closed | grep `<details\|<summary` in admin.php: 0; tests/test_admin_ui_contract.py:2581 `test_the_profile_block_has_one_select_with_three_profiles`, :2614 `test_the_profile_block_has_no_advanced_area` |
| T-27-34 | EoP | direkter Aufruf der Probe-Route | mitigate | AppAPI-Signatur, ADMIN in info.xml, wirksame Grenze PHP | closed | main.py:1258 (`APP.add_middleware(AppAPIAuthMiddleware)`), :1266 (Router danach); backend/appinfo/info.xml:359-361, :373-375 (ADMIN); tests/test_probe_endpoint.py:169 `test_a_start_without_any_appapi_header_is_unauthorized`, :159, :247, :255, :263; HaRP deploy 36596834148 prüft die Routen samt Level |
| T-27-35 | Tampering | fremde Werte im Body | mitigate | pydantic Literal, extra forbid, 422 | closed | api/probe.py:65-71 (`extra="forbid"`, zwei `Literal`); tests/test_probe_endpoint.py:118 `test_a_foreign_value_is_422_and_never_reaches_the_check` |
| T-27-36 | DoS | parallele Probe-Starts | mitigate | Einzelflug, 409 busy, rebuild 409 | closed | api/probe.py:142-145; worker/probe_run.py:419-423; tests/test_probe_endpoint.py:90, :99 |
| T-27-37 | Info Disclosure | Probe-Stand und Status | mitigate | nur Codes, Zahlen, Id; Status misst nichts | closed | api/probe.py:74-120 (Feldliste, `numbers` nur `NUMBER_KEYS`), :149-152; tests/test_probe_endpoint.py:205 `test_the_state_of_a_finished_check_carries_codes_and_numbers_only`, :232 `test_the_state_measures_nothing_and_changes_nothing` |
| T-27-38 | DoS | Pause überlebt den Shutdown | mitigate | close() vor stop_indexing, finally hebt Pause auf | closed | main.py:1151-1166 (`probe_run.close()` vor `stop_indexing.set()`); worker/probe_run.py:436-446, :473-477; tests/test_probe_endpoint.py:318 `test_the_lifespan_restores_recovers_and_closes_before_the_poller` |
| T-27-39 | Spoofing (XSS) | Poll-Antwort im DOM | mitigate | nur textContent, keine Markup-APIs, unbekannt verborgen | closed | php/js/admin.js:249-255 (`text()` setzt `textContent`), :1847-1869; grep `innerHTML\|outerHTML\|insertAdjacentHTML\|createElement\|document.write` in admin.js: 0; tests/test_admin_ui_contract.py:365-385 (`scan_script`), :1786. Siehe Hinweis 3 |
| T-27-40 | Tampering | Skript als Entscheider "Probe nötig?" | mitigate | Skript wählt nur Beschriftung, PHP entscheidet | closed | serverseitig: ProfileSettingsController.php:67, :108 (T-27-09); tests/test_admin_ui_contract.py:2799 `test_the_script_decides_the_probe_like_the_service` |
| T-27-41 | Info Disclosure | Token im Skript | mitigate | "Erneut prüfen" sendet nur Profil und Präzision | closed | php/js/admin.js:1690, :1946 (`{ profile, precision }`); tests/test_admin_ui_contract.py:2843 `test_the_script_sends_only_profile_and_precision`, :2452 |
| T-27-42 | Spoofing (XSS) | Katalogwert bricht die Seite | mitigate | Gate gegen nacktes % und \|, Ausgabe über p()/textContent | closed | tests/test_admin_ui_contract.py:3420 `test_no_catalogue_value_can_break_the_page`, :3368; Ausgabe siehe T-27-31, T-27-39 |
| T-27-43 | Repudiation | Sprache mit englischem Rest | mitigate | Vollständigkeits- und Wortlaut-Gate, begründete Ausnahmen | closed | tests/test_admin_ui_contract.py:2900 `test_every_sentence_of_the_profile_block_is_in_every_catalogue`, :3293 `test_every_catalogue_value_carries_a_wording_of_its_language`, :3243, :3670 (WR-11, Doku-Tabellen, Ausnahme `Findling`) |
| T-27-44 | EoP | Admin-Routen für Nicht-Admins | mitigate | Live-Schritt erwartet nie 200 und unveränderten Profilschlüssel | closed | .github/workflows/integration.yml:273-320 (`expect_refused` 401/403/302/303 je Route, `test "${before}" = "${after}"`, Gegenprobe Admin); Integration 36596834631 Schritt success (per `gh run view`) |
| T-27-45 | Repudiation | occ-Weg ohne Probe missverstanden | mitigate | Doku: occ überspringt die Probe, nur Wächter sichert | closed | docs/profiles.md:104, docs/embeddings.md:916, docs/admin-page.md:565 |
| T-27-46 | Info Disclosure | Zugangsdaten, Tokens in Rohdaten | mitigate | nur Codes und Zahlen, grep-Kriterium | closed | `grep -rniE "password\|secret\|requesttoken\|authorization\|bearer\|[0-9a-f]{32}"` auf docs/measurements/2026-09-probe-live/: nur die Wortnennung "session login with requesttoken" (kein Wert) in raw/07 sowie Image-Digests und Korpus-Prüfsumme, kein Geheimnis |
| T-27-47 | EoP | Nicht-Admin erreicht Admin-Route | mitigate | Live-Beleg kein 200, unveränderter Profilschlüssel | closed | docs/measurements/2026-09-probe-live/raw/07-nicht-admin.txt (5 x HTTP403 "Logged in account must be an admin", occ profile vor/nach economy, Admin-Gegenprobe HTTP200) |
| T-27-48 | Info Disclosure | ungewollter Push | mitigate | Push nur nach Owner-Entscheid | closed | 27-16-SUMMARY.md:40-44 (Signal wörtlich "push-now", zweiter Push mit erneutem Owner-Wort); 27-VERIFICATION.md:129 (Push der Review-Fixes bis c87a0239 nach Owner-Wort "ja"); `git status -sb`: main 2 Commits vor origin (nur Doku), kein weiterer Push |
| T-27-49 | Repudiation | offene Belege als erledigt gemeldet | mitigate | stay-local listet offene Belege als human_needed | closed | 27-16-PLAN.md:14, :60; 27-VERIFICATION.md:4, :11-20 (status human_needed, fp32 live und Maschinenübersetzungen offen benannt) |
| T-27-50 | Repudiation | Issue- oder Store-Text ohne Freigabe | mitigate | nur Entwürfe auf Owner-Wunsch, kein Posten | closed | 27-16-SUMMARY.md:44 ("keine Issue- oder Store-Texte"), :134 ("Keine Issue- oder Store-Entwürfe gewünscht") |

*Status: open, closed. Disposition: mitigate (Umsetzung nötig), accept (dokumentiertes Risiko), transfer (Dritter).*

---

## Verfall der Altannahmen durch die neue Schreibroute

| Risk ID | Ursprung | Status in Phase 27 | Ersatz |
|---------|----------|--------------------|--------|
| AR-24-02 | T-24-14, "Schreibweg nur occ" | **verfallen** (superseded). Mit ProfileSettingsController entsteht eine Browser-Schreibroute für Profil und Präzision. | T-27-17 bis T-27-20 und T-27-09: Admin-only und CSRF durch den Plain Controller ohne Aufheber (ProfileSettingsController.php:41, :65, :81, :93; Gate B, Live-403, CI 36596834631); Direktschreiben nur `isDownward` (:108-112); Aufwärts nur über `ProbeService::takeOver` (ProbeService.php:306-319) mit Commit-Bindung an die selbst gestartete Probe (16-Hex-Id per `hash_equals`, beide Ziele gleich, Zustand "done", Verdikt "fits", seit WR-06 unveränderter Stand seit Start). occ bleibt zweiter Weg mit Serverzugang (T-27-45). |
| AR-26-02 | T-26-17, "Token auf der Adminseite" | **verfallen** (superseded). Der Token steht nicht mehr auf der Seite; die Bestätigung schreibt PHP selbst. | T-27-21, T-27-23, T-27-32, T-27-41: Token nur serverseitig aus frischem `/status` gelesen, gegen `/^[0-9a-f]{32}$/D` geprüft und nur geschrieben, wenn der Wächter genau das gerade als "fits" bestätigte Profil gewählt hat (ProbeService.php:366-382); Browser bekommt nur `guardConfirmable` als bool (AdminViewService.php:2263). |
| AR-26-01 | T-26-07, Profilroute ExAppRequired | gültig, unverändert | ProfileController.php:65 weiterhin nur `ApiRoute` GET; kein neuer Schreibweg dort. |
| AR-26-03 | T-26-26, Token in /status | gültig | /status bleibt ADMIN; einziger PHP-Leser des Tokens ist jetzt `ProbeService::confirm`, der ihn nicht weitergibt. |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-27-01 | T-27-25 | `profile_check` ist per `occ config:app:set` beschreibbar; occ-Zugang ist Serverzugang und damit bereits volle Rechte. Der Wert ist nur Anzeige für den Admin, wird beim Lesen erneut gegen die geschlossenen Mengen geprüft (AdminViewService.php:774-808, ProbeService.php:252-279) und ist nie Grundlage eines Commits (Commit nur aus dem Container-Snapshot, ProbeService.php:306-319). | Owner (Plan 27-08, Register zur Planzeit) | 2026-09-29 |

*Akzeptierte Risiken tauchen in späteren Audits nicht erneut auf.*

---

## Unregistered Flags

Keine. Die Threat-Flags-Abschnitte in 27-06, 27-07, 27-09, 27-10, 27-11 und 27-12-SUMMARY.md melden keine neue Fläche und verweisen nur auf registrierte IDs; die übrigen SUMMARYs haben keinen Threat-Flags-Abschnitt.

### Informative Flags aus den Review-Fixes (keine Blocker, keine neue Angriffsfläche)

- **F-1 (WR-07, 5c2c7edf, zu T-27-19):** `ProbeService::adopt` (ProbeService.php:165-194) übernimmt bei `busy`/`unreachable` ohne eigenen Datensatz die Id einer laufenden Probe aus `/probe/state`, wenn beide Ziele exakt gleich sind. Die Id stammt damit nicht mehr zwingend aus der eigenen Startantwort, sondern aus dem gleichen vertrauenswürdigen Container-Kanal; der Commit bleibt an Id (`hash_equals`), Ziel, "done", "fits" und unveränderten Stand gebunden. Folge: klickt ein zweiter Admin dasselbe Ziel, während die Probe eines ersten läuft, übernimmt er dessen Verdikt. Beide sind Admins, der Browser liefert weiterhin kein Verdikt. Tests: php/tests/Unit/ProbeServiceTest.php:215, :231 (grün in 36596834116).
- **F-2 (WR-06, 52e1cfb7, zu T-27-19):** Ein Pending-Datensatz ohne `inForce` (aus der Zeit vor dem Fix) committet wie bisher (ProbeService.php:404-407); ein unlesbarer nie (:470-476). Fenster höchstens `PENDING_STALE_SECONDS` = 3000 s nach dem Update.
- **F-3 (WR-08, 168fa999, zu T-27-15/D-27-17):** Die Besitzmarke `probe_fp32_fetched` hängt jetzt an der Datei, nicht an der Probe-Id (worker/probe_run.py:497-501, :557). Legt ein Admin eine eigene Datei über eine noch markierte, geholte Datei, gilt sie als geholt und fällt bei einem späteren "nofit" weg. Setzt Schreibzugriff aufs Volume voraus; nur Verfügbarkeit, keine Integrität der Messung (Digest-Prüfung bleibt vor jeder Nutzung).
- **F-4 (WR-08):** Nach "fits" bleibt eine geholte fp32-Datei bis `PROBE_TAKEOVER_SECONDS` = 3000 s (config.py:962) liegen, auch wenn PHP nicht committet; der Sweeper räumt danach. Plattenplatz war vor dem Download gegen `FP32_BYTES + min_free_bytes` geprüft (embed/weights.py:306).
- **F-5 (WR-09, 20041463, zu T-27-13):** Die Wächter-Aussetzung ist enger geworden (nur Messteil plus ein Tick); Kills des regulären Durchlaufs während der Pause senken wieder. Stärkt die Absicherung.
- **F-6 (WR-01, WR-02, WR-04):** geänderte SQL in FileStateService (Join auf `filecache`, breiteres Delete in `revokeFailures`) nutzt ausschließlich `createNamedParameter` mit festen Literalen; kein neuer Eingang.

## Hinweise (informativ, keine Blocker)

1. **T-27-34:** Das ADMIN-Level der Container-Routen wird auf dem Weg `PublicFunctions::exAppRequest` nicht durchgesetzt (api/probe.py:21-26 benennt das selbst). Die wirksame Grenze ist die PHP-Route (T-27-17) plus AppAPI-Signatur; das ist die im Plan deklarierte Mitigation.
2. **T-27-18:** Der CSRF-Schutz ist der der Nextcloud-SecurityMiddleware. Der Kopf `OCS-APIRequest: true` erfüllt dort die CSRF-Prüfung (Framework-Verhalten, von Browsern ohne CORS-Preflight nicht setzbar); der CI-Schritt nutzt das bewusst, damit eine Ablehnung nur die Admin-Prüfung sein kann. Die Lese-Route GET führt den idempotenten Take-over aus und ist durch dieselbe Prüfung gedeckt.
3. **T-27-39:** Der Plan nennt Gate C mit `createElement`; `scan_script` (tests/test_admin_ui_contract.py:365-385) prüft innerHTML, outerHTML, insertAdjacentHTML und document.write, nicht `createElement`. Die Abwesenheit ist per grep belegt (0 Treffer in admin.js), ein automatisches Gate dafür fehlt.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-29 | 50 | 50 | 0 | Claude (gsd-security-auditor) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-29
