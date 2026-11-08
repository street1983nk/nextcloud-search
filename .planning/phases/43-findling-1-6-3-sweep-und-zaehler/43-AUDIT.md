---
phase: 43-findling-1-6-3-sweep-und-zaehler
audited: 2026-11-08
audited_head: 37b518d6754a4a8a8593dc537a13b27644caf986
audited_head_before_fix: d9f8a65d364d6b1bd65b7599da388d04dc746439
diff: v1.6.2..d9f8a65d
fix_delta: d9f8a65d..37b518d6
files_reviewed: 53
fix_files_reviewed: 3
e2e_run: 42525415627
findings:
  critical: 0
  high: 0
  medium: 1
  low: 2
  info: 4
  total: 7
medium_fixed: 1
low_fixed: 0
low_open: 0
status: passed
recommendation: 1.6.3 mit dem Fix F-43A-01 (lokal, Push braucht die Owner-Freigabe aus Task 2); 43-10/43-12 arbeiten gegen audited_head 37b518d6 oder einen Kopf mit leerem Code-Diff dazu
---

# Phase 43: Audit 1.6.3 (Security, Bugs, Performance)

**Stand:** 08.11.2026, **0 CRIT / 0 HIGH / 0 MEDIUM offen / 2 LOW entschieden /
4 INFO** über den ganzen Code-Delta `v1.6.2..d9f8a65d` (53 Dateien, 6.363
Zeilen dazu, 212 weg) plus den Fix-Delta `d9f8a65d..37b518d6`. Keine
Rechte-Umgehung, kein Datenleck, kein externer Dienst, kein Pfad und kein
Hash in Log oder Antwort. Ein MEDIUM wurde gefunden und lokal per TDD
behoben (F-43A-01: der synchrone Zähldeckel von POST /coverage lag über dem
2-Sekunden-Admin-Timeout der Companion, auf ARM fiel die Seite dadurch ab etwa
56.000 Zeilen dauerhaft und wortlos auf die 1.6.2-Zahl zurück). Beide LOW sind
entschieden und brauchen keinen Code; der Fix-Push wartet auf die
Owner-Freigabe (Task 2).

## Umfang

Code-Kopf mechanisch: `git log -1 --format=%H -- . ':!.planning'` =
`37b518d6754a4a8a8593dc537a13b27644caf986` (vor dem Fix: dd79d073 als letzter
Code-Commit unter d9f8a65d, dem letzten gepushten Stand).

`git diff --stat v1.6.2..d9f8a65d` über backend/src, backend/docker,
backend/appinfo, php/appinfo, php/lib, php/js, php/templates, php/l10n,
.github/workflows, scripts: **53 Dateien, 6.363 Zeilen dazu, 212 weg**
(backend/docker ohne Delta). Jede Datei mit Urteil:

| Datei | Plan | Urteil |
|---|---|---|
| backend/src/findling/worker/reconcile.py | 43-02/43-20 | ganz gelesen; Sweep mit eigenem Stempel (SWEEP_MARK) hinter dem stats.ok-Teil des Gates und vor dem Walk; Catch-up nur auf dem ruhigen Pfad; `_sweep_vanished` -> True/False/None mit Stempel nur bei True; IDs <= 0 gefiltert; Pause je Speicher geprüft; `renew_refusal_streaks` in `_open_state`, hinter dem Backup-Hold von `run()` (Probe im Code: `_open` läuft nur in `run_once`, das `run` erst nach `_backup_release` erreicht); Proben B-a bis B-e; ok |
| backend/src/findling/worker/doc_keys.py (neu, 584) | 43-16 | ganz gelesen; Bänder, Cursor dreiteilig, Generation-Reset genau einmal (I-43A-03), 404-Cooldown verdoppelt bis 1 h, Bisektion nach 3 unvollständigen Antworten, Sentinel '' nur für benannte oder beiseitegelegte IDs, Verify-Pass ruht 1 Tag, Backup-Pause zwischen Bändern, Logzeilen nur Zahlen; Belege test_doc_keys.py (44 Tests); ok |
| backend/src/findling/api/coverage.py (neu, 383) | 43-04 | ganz gelesen; strict-Pydantic mit extra=forbid, Grenzen vor jeder Datenbank, Single-Flight plus Cache (4 Schlüssel, 300 s, Bestandskennung dev/ino), Antwort nur Zahlen/IDs/bool/null; **F-43A-01 (MEDIUM, gefixt)**: COVERAGE_SYNC_CEILING 100.000 lag über dem Admin-Timeout auf ARM; nach Fix 25.000; Proben S-a/S-b/B-h und Messung P-b |
| backend/src/findling/store/repo.py | 43-02/16/18/20 | Diff ganz gelesen; SWEEP_MARK, REFUSAL_RENEW_MARK (eine Transaktion, Marke und UPDATE zusammen), doc_key nur über valid_doc_key, COALESCE hält Bestand (R2), Coverage-SQL nur Modulkonstanten, Listen als ein JSON-Parameter gebunden (json_each), INDEXED BY files_storage; Beleg test_the_predicates_are_module_constants_and_the_lists_travel_bound; ok |
| backend/src/findling/store/schema.sql | 43-16 | nur Spalte doc_key plus Index files_storage_doc_key, additiv und nullable, SCHEMA_VERSION unverändert (STOPP-Prüfung 43-08); ok |
| backend/src/findling/worker/poller.py | 43-15/18 | Diff gelesen; 422 -> skipped(unreadable) über `_refusal_outcome`, nie zur Ausfall-Schwelle (`_count_refusal` kehrt vor jeder Zählung um), doc_key mit dem Urteil und beim ACL-Auftrag nach Move; `renew_refusal_streaks` im Pass (hinter der Pause, D-41-19); ok |
| backend/src/findling/nc/client.py | 43-16/18 | GATEWAY_UNREADABLE_STATUS = 422 als Konstante, doc_keys als GET mit einem Komma-Wert (kein Allowlist-Eintrag nötig); ok |
| backend/src/findling/nc/files.py | 43-16 | DocKeyAnswer mit complete/unanswered gegen die gefragten IDs (W8), nur Hex-Werte gefragter IDs, 404 als route_missing, sonst None mit Klassenname; ok |
| backend/src/findling/nc/queue.py | 43-15 | docKey nur als 64 Hex übernommen, sonst None (nie löschend); ok |
| backend/src/findling/main.py | 43-04/16 | DocKeyBackfill als eigene Task, an Pause-Koordinator angehängt, Stop im Reconcile-Budget, Coverage-Router eingehängt; ok |
| backend/src/findling/extract/errors.py | 43-18 | nur Kommentar zu UNREADABLE; ok |
| backend/appinfo/info.xml | 43-04/43-08 | sechste Route `^/coverage$` POST ADMIN, verankert, bruteforce [401]; Version/Image-Tag/Links 1.6.3; Probe S-a und Ratchet in store_install_register.sh; ok |
| php/appinfo/info.xml | 43-08 | Version 1.6.3 und drei Doku-Links; kein Byte an Namen/Beschreibungen; ok |
| php/appinfo/routes.php | 43-15 | nur Kommentar (Routen weiter als Attribute, route-security.json); ok |
| php/lib/Controller/ReconcileController.php | 43-15 | docKeys hinter ExAppRequired/NoCSRFRequired, rejectForeignCaller vor allem; fileIdList kanonisch (ctype_digit, Rückabbildung, Deckel DOC_KEY_BAND, Rohlänge vor dem Split); Antwort immer Map (stdClass bei leer); Log nur Zähler; Probe D-e; ok |
| php/lib/Service/DocKeyService.php (neu, 142) | 43-15 | docKeyOf = sha256 über NFC-Pfad ohne führenden Slash, files/ bleibt (W2), Papierkorb-Präfixe absent; eine Quelle für Aufträge und Backfill; Pfade verlassen die Methode nie; PHPUnit DocKeyServiceTest gegen doc_key_cases.json (CI-Beleg unten); ok |
| php/lib/Service/QueueService.php | 43-15 | withDocKeys eine Abfrage je Claim, delete ohne Schlüssel, Fehlschlag kostet nur das Feld (Container behält und fragt nach); ok |
| php/lib/Controller/GatewayController.php | 43-17/18 | ein 422-Pfad `cannotOpen` (fopen false, leerer Erstblock bei Größe > 0, Timeout, Lesefehler, FileInUse per is_a-String); nonBlocking nur SMB ohne Encryption über instanceOfStorage; Antwort nach dem Vorlesen, vor den Headern; Log nur fileId; ok |
| php/lib/Http/BoundedStreamReader.php (neu, 227) | 43-17/18 | Fristen 80 s < 90 s des Backends, MAX_READS 60.000 gegen die stdin-Pipe, Pausen wachsend, Cap nur bei echtem nonBlocking; prime vor den Headern, pump schließt den Stream auf jedem Weg; ok |
| php/lib/Http/BoundedStreamResponse.php (neu, 73) | 43-17 | bewusst ohne Content-Length (ShortRead statt Ausfall), Log nur fileId, kein Log bei Client-Abbruch; ok |
| php/lib/Migration/Version001603Date20261108000000.php (neu, 97) | 43-06 | liest eine scan_stats-Zeile, schreibt genau coverage_per_document_hint (pending), zweite Ausführung No-op, Lesefehler nur Warnung; Probe S-f per Durchsicht, CI-Zusicherungen 14/15; ok |
| php/lib/Service/SettingsService.php | 43-06 | Drei-Zustände-Schlüssel, Stempel nur aus pending, max(2, now), coverageHintVisible statisch; C-d unten; ok |
| php/lib/Service/AdminViewService.php | 43-05/06/19 | Diff ganz gelesen; coverageBody kanonisch (nur eingebundene Mitglieder, erste Gruppe gewinnt, < 2 Mitglieder fällt), Antwortprüfung perDocumentAnswer (Summen, Paare, documents <= judged je Teil), Nenner je Teil max(PHP, judged+phpOnly) (D-43-11), Grenzen gespiegelt, sichtbarer legacy/limits, SMB-Hinweis hinter Closure-Sonde; Proben C-b, F-43A-01; ok |
| php/lib/Service/ScanStatsService.php | 43-05 | representative() als eine Regel für totals und groupParts, partsOf nie unter 0, refused nur je Repräsentant/Einzelspeicher; ok |
| php/lib/Service/FileStateService.php | 43-05 | countByReasonPerStorage und distinctPathsByReasons in Bändern zu STORAGE_BAND = 1000 (Oracle-Grenze), N1 über den Dateicache (LEFT JOIN, IS NULL), W-b über INNER JOIN, nur Zahlen und path_hash intern; PHPUnit FileStateServiceCoverageTest (12 Tests, CI); ok |
| php/lib/Controller/ProfileController.php, QueueController.php | 42-Reihe | nur `final`; ok |
| php/js/admin.js | 43-06 | vier neue Sätze über t()/text(), Sichtbarkeitsregeln counting/hint/notReadable/legacy wie im Template, keine Markup-Injektion (Katalog-Delta ohne < >); ok |
| php/templates/admin.php | 43-06 | vier neue p($l->t(...))-Zeilen, hidden-Logik deckungsgleich zu admin.js; ok |
| php/l10n/{de,de_DE,es,fr,it,nl,pt_BR,pt_PT}.{json,js} (16 Dateien) | 43-06/19 | je 7 Zeilen Delta (4 neue Coverage-Sätze, 1 SMB-Hinweis, 1 ersetzter unreadable-Satz); Schlüsselmenge in allen 8 JSON gleich (366 Schlüssel, md5 74fcb71d achtmal); kein `<` oder `>` im Delta; Ausgabe nur über t()/textContent; ok |
| .github/workflows/coverage-e2e.yml (neu, 172) | 43-07 | workflow_dispatch only, permissions contents: read, Secrets feste Testwerte, Checkouts und Actions mit vollem SHA gepinnt, Skripte immer vom Kopf (findling-harness); Variablen in Steps nur über env; ok |
| .github/workflows/deploy-harp.yml | 43-08 | Zusicherungen 14 bis 18 nur lesend (SC4), L-30-03-Guards vor GITHUB_ENV (hint als ^[0-9]*$), jq/sqlite3 mit zitierten Variablen, eingebettete Python-Probe read-only (mode=ro); ok |
| .github/workflows/php.yml | 42-03/42-02 | composer validate --strict und audit --locked (nichts installiert), schedule mit event_name in der Concurrency-Gruppe, Route-Gate liest junit.xml mit Floor 40 aus env, php -r ohne Shell-Interpolation; ok |
| .github/workflows/python.yml | 42-10 | Pfadfilter php/** statt php/l10n/**, Begründung im Kommentar; ok |
| scripts/ci/coverage_e2e.sh (neu, 1636) | 43-07/18 | set -euo pipefail, VARIANT/SMB_MODE gegen feste Mengen, nur localhost-URLs plus genau ein Download des eigenen 1.6.2-Release-Archivs (I-43A-04), Passwörter feste Testwerte und nie gedruckt, Variablen zitiert (Stichproben über alle curl/sudo/tc-Stellen); Harness, läuft nur auf dem Runner; ok |
| scripts/ci/coverage_truth.sh (neu, 326) | 43-07 | Wahrheit ohne Findling-Code (sudo -u find am Samba, SQL über Snapshots, eigener sha256 je interner Pfad), D-43-11-Regel in SQL aus der Definition, Positivkontrollen 1 und 2 eingebaut; ok |
| scripts/ci/store_install_register.sh | 43-04 | Ratchet auf exakt sechs Routen `^/coverage$:POST:2 ...`; ok |
| scripts/dev/phpunit_docker.sh (neu, 181) | 43-05 | liest SERVER_VERSION/MINIMUM_TESTS aus php.yml (kein Drift), Checkout-Branch-Wächter, Mounts über cygpath, Argumente unverändert an PHPUnit; nur Entwicklerwerkzeug; ok |

Gegengelesen außerhalb des Diffs: `worker/catchup.py` und `worker/pause.py`
(der Backfill hängt wie der Reconcile am Koordinator), `api/status.py`
(leaveOut unverändert für 1.6.2), `php/lib/Service/ExAppService.php`
(ADMIN_REQUEST_TIMEOUT_SECONDS = 2.0, MAX_BODY_BYTES = 1 MiB, adminSend ->
ADMIN_MISSING nur bei 404), `php/lib/Service/StorageService.php`
(countingKeyGroups unverändert).

## Methode

- Proben als Tests in `backend/tests/test_phase43_audit.py` (15 Tests, dreimal
  hintereinander grün: 15/15/15), je eine Probe für jede Hypothese, die kein
  Test der Pläne 43-01 bis 43-20 schon fährt; die übrigen Hypothesen sind unten
  mit dem bestehenden Test oder dem CI-Beleg benannt und wurden lokal
  mitgefahren (748 Tests der sechs Kernmodule grün, dazu 804 Tests der
  Nachbarmodule poller/store_repo/files_client/main_lifespan/backup_pause/
  catchup/admin_ui_contract/exapp_surface/lockstep_versions).
- Messungen als Skript `scratchpad/a43/measure_coverage.py`, Ausgabe wörtlich
  unten (P-b); die Backlog-Probe druckt ihre Zahlen im Test (P-c).
- Andere Wege als die Baupläne: die Routen-Deklaration gegen die wirklich
  gemounteten FastAPI-Pfade gehalten (nicht gegen die eigene Erwartungsliste),
  mit Groß-/Kleinschreibungs-Kontrolle (`/Coverage` ist nicht gemountet);
  PHP-Attribute aus den Quellzeilen vor der Methode mit Fensterkontrolle
  (genau drei `#[`-Zeilen); der D-43-11-Fall "erst indexiert, dann unreadable"
  über echte record-Übergänge statt über gebaute Zählerstände; Em-Dash- und
  Emoji-Audit über das ganze Delta mit Positivkontrolle.
- PHP nur per Durchsicht plus CI-Belege (lokal kein PHP, wie 43-15): PHPUnit
  "OK (1140 Tests, 6876 Assertions)" Lauf 42422989883, Pfadfilter-Beleg
  42513966089 auf d9f8a65d; E2E-Lauf 42503731869 (fünf Beine grün) und
  42516315101 auf d9f8a65d (43-E2E.md).
- Gates mit allen Änderungen: ruff check "All checks passed!", ruff format
  --check "255 files already formatted", pyright (latest) "0 errors,
  0 warnings, 0 informations", vulture 80 Exit 0; je vor dem Commit.

## Hypothesen und Proben

### Security

| Hypothese | Probe / Beleg | Ergebnis |
|---|---|---|
| /coverage ohne Admin erreichbar (HaRP-Deklaration, Groß-/Kleinschreibung wie 42-10) | test_every_declared_route_is_mounted_with_its_exact_case_and_verb (6 Routen, alle ADMIN, /coverage POST, `/Coverage` nicht gemountet); Ratchet store_install_register.sh (erster CI-Lauf der Phase fiel dort rot, bis das Literal die sechste Route kannte); test_the_route_is_declared_admin_and_post | kein Weg ohne ADMIN |
| Body-Grenzen umgehbar (verschachtelte Listen, bool als int bei strict, sehr große Ganzzahlen) | test_a_boolean_is_not_a_storage_id (strict weist True ab, Positivkontrolle [1] -> 200); test_a_nested_list_a_fraction_a_huge_number_and_an_extra_field_are_refused (7 Körper, darunter 10**18, eine 400-stellige Zahl, extra-Feld, 0 und -5: alle 422); bestehend test_a_body_outside_the_bounds_is_a_422_before_any_database | Grenzen halten |
| SQL-Bindung (json_each, keine Interpolation) | bestehend test_the_predicates_are_module_constants_and_the_lists_travel_bound; Durchsicht: jede Format-Einsetzung in _COVERAGE_SQL ist Modulkonstante, Listen reisen als ein JSON-Parameter; PHP nur QueryBuilder mit Named-Parametern | gebunden |
| Pfade/Hosts/Nutzer in Antwort oder Log | Logzeilen-Grep über den Delta: 22 neue Zeilen (12 Python, 10 PHP), nur Zustandswörter, Zähler, fileId oder `type(error).__name__`; die zwei PHP-Zeilen mit exception-Objekt gehen in den Kontext wie die übrigen der Klassen; bestehend test_the_answer_carries_numbers_booleans_and_null_only, test_an_unreadable_state_is_a_503_without_a_path, test_the_log_lines_carry_numbers_and_never_a_path_or_a_key | kein Pfad, kein Hash, kein Name |
| Cache-Schlüssel-Kollision zwischen Admins/Instanzen | canonical_key = sha256 über die kanonische Frage, Bestandskennung (Pfad, dev, ino) beider Stocks im Eintrag; bestehend test_the_cache_key_ignores_the_order_of_the_ids, test_a_replaced_state_database_drops_the_cache; ein Container trägt genau eine Instanz | keine Kollision |
| Migration liest/schreibt nur den einen Schlüssel | Durchsicht (ein SELECT auf scan_stats, ein setValueInt auf coverage_per_document_hint, Guard gegen zweite Ausführung); STOPP-Prüfung 43-08 bestanden; CI-Zusicherungen 14/15 im HaRP-Lauf 42513966073 grün | ja |
| Kein externer Dienst | URL-Grep über den Code-Delta: nur die drei blob/v1.6.3-Doku-Links in den zwei info.xml; Harness-Skripte nur localhost plus der Download des eigenen 1.6.2-Release (I-43A-04) | kein neuer Abruf |

### Bugs

| Hypothese | Probe / Beleg | Ergebnis |
|---|---|---|
| Sweep bei Wechsel busy/ruhig in derselben Runde | test_a_queue_that_turns_busy_in_the_round_stops_the_walk_before_its_next_slice (Gate wird vor jeder Scheibe neu gefragt, Sweep lief davor); test_a_queue_that_turns_calm_after_the_gate_read_still_waits_for_the_next_round (Momentaufnahme, Walk in der nächsten Runde) | sicher in beide Richtungen |
| Sweep im once/Catch-up-Modus | test_the_once_cycle_sweeps_only_under_the_catch_up_mark (vor Teil A keine Mountliste, unter der Marke Sweep mit Stempel); bestehend test_the_sweep_leaves_the_catch_up_alone | ok |
| Pause genau zwischen Mountliste und erstem Speicher | test_a_pause_between_the_mount_list_and_the_first_storage_ends_the_round_clean (kein Auftrag, kein Stempel, kein back_off, nicht einmal die Speicherfrage; nächste Runde holt nach); bestehend test_a_pause_during_the_sweep_ends_it_without_a_stamp, test_a_held_pause_starts_no_round_and_no_sweep | ok |
| Stempel bei "nichts abwesend" | test_a_sweep_with_nothing_absent_stamps_and_rests_for_its_cadence (Stempel gesetzt, Mountliste in der Folgerunde nicht gelesen) | ok, keine Liste je Tick |
| Uhr springt zurück (last_at in der Zukunft) | test_a_sweep_stamp_in_the_future_waits_and_a_past_stamp_is_due | F-43A-02 (LOW, akzeptiert) |
| Gruppe mit einem eingebundenen Mitglied | bestehend test_a_group_of_one_member_counts_as_a_single_storage; PHP coverageBody lässt Gruppen < 2 fallen (gleiche Regel wie _kept_groups) | zählt als Einzelspeicher |
| Speicher gleichzeitig Mitglied und doppelt in mounted | Python: Validator weist "a storage stands in two groups" ab, mounted als Menge; PHP: coverageBody dedupliziert ($taken, erste Gruppe gewinnt) und baut nie so einen Körper | Vertrag hält |
| counting dauerhaft (Thread stirbt) | test_an_unexpected_error_in_the_background_count_does_not_wedge_the_single_flight (ValueError, finally gibt den Slot frei, dritter Abruf hat die Zahl); bestehend test_a_count_that_fails_in_the_background_leaves_no_entry_and_is_tried_again; Backfill: Sentinel beendet counting (test_a_file_without_a_file_cache_row_gets_the_sentinel_and_ends_counting) | kein Verklemmen (I-43A-02) |
| Gemischte Versionen beider Richtungen | Companion 1.6.3 + Container 1.6.2: ADMIN_MISSING -> legacyReason missing, Lockstep-Banner, /status wie 1.6.2 (test_status_with_leave_out_still_answers_for_a_companion_1_6_2); Companion 1.6.2 + Container 1.6.3: Backfill-404-Cooldown (test_a_missing_route_waits_with_a_doubling_cooldown_and_keeps_the_cursor), counts ohne Schlüssel bleiben; E2E-Beine v1.6.2 und upgrade grün (43-E2E.md) | ok |
| 404-Warnung bei jedem Seitenaufruf im Mischbetrieb (Log-Flut) | Durchsicht: Container-Seite eine Zeile je Cooldown-Stufe (gedeckelt 1 h); PHP-Seite eine Warnzeile je Overview-Abruf, solange die Seite offen ist | F-43A-03 (LOW, akzeptiert) |

### D-43-11 (Nenner)

| Hypothese | Probe / Beleg | Ergebnis |
|---|---|---|
| Erst indexiert, später skipped/unreadable: doppelt im Nenner? | test_a_document_first_indexed_and_later_unreadable_counts_once_on_the_container_side (Einzelspeicher: nach dem Übergang weder documents noch judged; Gruppe: ein indexiertes Mitglied hält das Dokument genau einmal in beiden); PHP-Seite N1 per PHPUnit testUnreadableForOneMemberIndexedForAnotherCountsOnceAndIsNotInNotReadable (43-05) | zählt genau einmal |
| Gruppenreihenfolge zwischen Body, Antwort und groupParts | Durchsicht: Antwort in Request-Reihenfolge (_in_request_order), perDocumentAnswer prüft Länge je Gruppenliste, groupParts läuft über die Body-Gruppen in deren Reihenfolge; test_the_coverage_bounds_of_both_halves_are_the_same_numbers hält die Grenzen beider Hälften aneinander; E2E vergleicht die angezeigte Zahl gegen die Wahrheit (A/B je Bein gleich) | eine Reihenfolge |
| Bänder zu 1000 IDs in countByReasonPerStorage und distinctPathsByReasons | Durchsicht (STORAGE_BAND = 1000, auch für die Hash-Bänder der N1-Prüfung); PHPUnit "2500 IDs in drei Abfragen (1000/1000/500)" (43-05-SUMMARY, CI-Lauf oben) | gebändert, Oracle-fest |
| Hinweis-Zeitstempel bei Uhrsprung (D-43-12) | Durchsicht SettingsService: Stempel nur aus pending, max(2, now); Uhr zurück nach dem Stempel: now - state < 7 Tage bleibt wahr, der Hinweis steht länger; Uhr vor: er fällt früher; clearCoveragePerDocumentHint schreibt nur bei != 0 | kosmetisch, kein Befund (I-43A-05 entfällt, unter C-d dokumentiert) |

### R1/R2 (doc_key im Betrieb)

| Hypothese | Probe / Beleg | Ergebnis |
|---|---|---|
| docKey bei Lesern über SharedMount gleich dem Eigentümer | DocKeyService liest oc_filecache.path der file id, nie den Reader-Node (Durchsicht, Begründung im Klassenkommentar); E2E a1_rows_checked = 3/3 (zwei Speicher, zwei Leserpfade, ein Schlüssel, Schlüssel im Harness selbst gerechnet) | ja |
| Kein Auftrag setzt doc_key auf NULL zurück | COALESCE in _RECORD_SQL und _REFRESH_META_SQL, set_doc_keys schreibt nur Schlüssel oder Sentinel; bestehend test_a_verdict_without_a_key_keeps_the_stored_one; einziger NULL-Schreiber ist reset_doc_keys (Generationswechsel) | hält |
| Sentinel '' beendet counting | bestehend test_a_file_without_a_file_cache_row_gets_the_sentinel_and_ends_counting, test_the_sentinel_counts_as_a_document_of_its_own_and_is_no_missing_key | ja |
| Cursor-Reset | bestehend test_a_cursor_at_the_end_goes_back_for_a_new_row_without_a_key, test_a_mark_of_the_two_part_form_is_read_and_completed | ja |
| 404-Cooldown bei Companion 1.6.2 | bestehend test_a_missing_route_waits_with_a_doubling_cooldown_and_keeps_the_cursor, test_a_coverage_call_ends_the_cooldown_at_once, test_a_coverage_call_before_the_404_does_not_end_the_cooldown | ja |
| Umbenennen erneuert doc_key | bestehend test_a_rename_with_a_new_key_replaces_it_on_both_write_paths, test_an_acl_job_after_a_move_writes_the_new_key; Verify-Pass für den Rückweg (test_after_a_restart_a_stored_rest_is_ignored_and_a_stale_key_is_corrected_in_the_first_round) | ja |
| Rückweg 1.6.2 mit Spalte | E2E rollback_1_6_2 ok, second_upgrade_rename ok mit docKeysCorrected=1 (43-E2E.md); Spalte und Index überleben, 1.6.2 ignoriert sie | ja |

### D-43-14 (Schlüssel und Backfill)

| Hypothese | Probe / Beleg | Ergebnis |
|---|---|---|
| Normalisierung (NFC, Home-Präfix, Groß-/Kleinschreibung, verschiedene Wurzeln) | Durchsicht docKeyOf (NFC, ltrim /, kein Lowercase mit Begründung, files/ bleibt mit W2-Begründung); PHPUnit DocKeyServiceTest gegen handgerechnete doc_key_cases.json; verschiedene Wurzeln derselben Freigabe bleiben bewusst doppelt (D-43-15, bekannte Grenze, K6 in 43-12) | ok, Grenze dokumentiert |
| Backfill-Laufzeit 190.000 Zeilen, Last je Band | Messung 43-16: rund 3,4 h (25 Bänder je Runde, eine getFileByIds-Abfrage über 200 IDs je Band); E2E: 65 s je 1.000 Zeilen auf CI-Hardware | belegt |
| Abbruch und Fortsetzung | bestehend test_the_backfill_fills_a_thousand_rows_in_bounded_resumable_rounds, test_a_set_aside_row_does_not_count_as_missing_after_a_restart, test_an_unreachable_route_keeps_the_cursor | ja |
| Backup-Pause | bestehend test_a_backup_pause_ends_the_backfill_between_two_bands, test_the_verify_pass_respects_the_backup_pause | ja |
| Route /reconcile/doc-keys ohne ExApp-Anmeldung | test_the_doc_key_route_stands_behind_the_exapp_attributes_before_any_lookup (drei Attributzeilen, rejectForeignCaller vor fileIdList vor dem Service, Fensterkontrolle); RouteSecurityTest-Gate in php.yml (Floor 40, skipped = 0) | nur die signierte ExApp |
| Hash-Werte nie im Log | bestehend test_the_log_lines_carry_numbers_and_never_a_path_or_a_key; Logzeilen-Grep oben (PHP-debug-Zeile nur Zähler) | ja |
| Mischbetrieb ohne docKey im Auftrag | bestehend test_a_job_without_a_usable_key_carries_none plus COALESCE (R2) | ja |
| N1-NOT-EXISTS-Kosten auf MySQL/PostgreSQL bei 1000 Mitgliedern | Durchsicht: die N1-Prüfung ist ein LEFT JOIN ... IS NULL je 1000er-Hash-Band, IN-Listen durch COVERAGE_MAX_MEMBERS (1000) und STORAGE_BAND (1000) gedeckelt, oc_filecache trägt den Unique-Index (storage, path_hash); lokal nicht messbar (kein MySQL/PG), die Form ist die der bestehenden leaveOut-Abfragen | plausibel, CI-Beine grün |

### Performance

| Hypothese | Probe / Beleg | Ergebnis |
|---|---|---|
| Antwortgröße /coverage bis 50.000 Paare, Validierungskosten in PHP | bestehend test_the_answer_for_fifty_thousand_storages_stays_small: "50 000 storages: 1400238 bytes, 0.052 s"; deshalb COVERAGE_MAX_SINGLES = 25.000 in PHP (43-05, gegen MAX_BODY_BYTES 1 MiB); perDocumentAnswer ist ein O(n)-Durchlauf über höchstens 2 x 25.000 Paare, PHPUnit hält die Prüfregeln (lokal kein PHP für eine Zeitmessung, W-d: die Schranke ist die Antwortgröße, nicht die Schleife) | gedeckelt und sichtbar (legacy/limits) |
| /coverage auf 190.000 Zeilen und 50.000 mounted; synchrone Schwelle auf schwacher CPU; ADMIN_REQUEST_TIMEOUT_SECONDS | Messung P-b unten | **F-43A-01 (MEDIUM, gefixt)** |
| 31.571 Löschaufträge nach Fristablauf in einer Runde | test_the_delete_backlog_of_the_issue_goes_through_in_one_round_of_bands: "31,571 delete orders in one round: 169 bands of <= 200, 0.03 s"; die Aufträge liegen danach als scheduled in der Queue, das Quiet-Gate hält den Walk, der Sweep stempelt und ruht | ok, Bänder halten |
| Mountliste einmal pro Takt statt pro Runde | test_a_sweep_with_nothing_absent_stamps_and_rests_for_its_cadence; bestehend test_a_busy_queue_still_sweeps_once_per_cadence, test_a_list_that_stays_discarded_is_not_read_every_tick (W11); E2E: "walked rounds = 0" bei laufendem Sweep (43-E2E.md) | ok |

Messung P-b (`scratchpad/a43/measure_coverage.py`, Entwicklungsrechner x86,
190.000 Zeilen, Vektor-Stock für jede zweite Zeile, Ausgabe wörtlich):

```
A sync ceiling: 102311 living rows in 21 mounted storages
A request work: best 0.738 s, worst 1.713 s of 3
A times five for ARM: 3.69 s against the 2.0 s admin timeout of the companion
B whole stock: 190000 rows, 50000 mounted, canonical key 0.004 s (399ab1bb)
B count work: best 1.259 s, worst 2.976 s of 3 (background thread pays this)
per row 7.22 us; rows under 2.0 s at factor 5: about 55420
```

Der Hintergrundpfad (B) trägt die mbozem-Größe problemlos: der Thread zahlt
1,3 bis 3 s, die Antwort selbst sagt counting und kostet nichts; der Faktor 5
für ARM ist der Präzedenzfall aus 41-AUDIT.md (Probe V).

## Befunde

### F-43A-01 (MEDIUM, GEFIXT): Synchroner Zähldeckel über dem Admin-Timeout auf ARM

- **Datei:** `backend/src/findling/api/coverage.py` (COVERAGE_SYNC_CEILING).
- **Szenario:** Bis 100.000 lebende Zeilen in den eingebundenen Speichern
  zählte POST /coverage in der Anfrage. Gemessen kostet das 7,3 us je Zeile
  auf dem x86-Entwicklungsrechner, mit Faktor 5 auf der Zielhardware (ARM,
  4-8 GB) rund 36,5 us: ab etwa 56.000 Zeilen antwortet der Container nach
  mehr als 2,0 s, die Companion hat aufgelegt
  (ADMIN_REQUEST_TIMEOUT_SECONDS), adminOutcome meldet unreachable, und die
  Seite fällt in den wortlosen 1.6.2-Fallback (PER_DOCUMENT_FALLBACK). Das
  passiert bei JEDEM Seitenabruf erneut: genau die Instanzklasse, für die
  1.6.3 gebaut ist, sähe die neue Zahl nie, und jeder Abruf verbrennt
  zusätzlich eine mehrsekündige synchrone Zählung im Container.
- **Probe:** Messung P-b (wörtlich oben); Test
  `test_the_sync_ceiling_keeps_a_slow_box_under_the_admin_timeout_of_the_companion`
  liest das Timeout aus ExAppService.php und hält den Deckel gegen die
  gemessenen Kosten; vor dem Fix rot (100000 x 36,5 us = 3,65 s > 1,0 s),
  danach grün.
- **Fix:** COVERAGE_SYNC_CEILING = 25.000 (0,18 s x86, rund 0,9 s ARM, die
  andere Hälfte des Timeouts bleibt für HTTP, Signaturprüfung und die drei
  kleinen Lesungen). Darüber läuft der bestehende, geprüfte Hintergrundpfad:
  die Seite sagt einmal "wird gezählt", die Zahl kommt aus dem Cache (300 s).
  Kein Routen-, Schema- oder Vertragsschnitt; die Endpoint-Tests patchen die
  Konstante und bleiben unverändert gültig.
- **Commit:** 37b518d6 (lokal; Push erst nach Owner-Freigabe, Task 2).

### F-43A-02 (LOW, akzeptiert): Sweep-Stempel in der Zukunft nach Uhrsprung

- **Datei:** `backend/src/findling/worker/reconcile.py` (`_cadence_due`).
- **Szenario:** Springt die Uhr nach einem geschriebenen Stempel zurück (NTP,
  Host ohne RTC), liegt `storage_sweep_at` in der Zukunft; elapsed ist
  negativ und der Sweep ruht, bis die Wanduhr den Stempel plus Intervall
  wieder erreicht.
- **Probe:** `test_a_sweep_stamp_in_the_future_waits_and_a_past_stamp_is_due`
  (mit Positivkontrolle über einen Stempel der Vergangenheit); ein unlesbarer
  Stempel gilt als "nie gelaufen" (bestehend
  test_an_unreadable_stamp_reads_as_never_swept).
- **Entscheid: akzeptieren.** Es ist dieselbe Kadenzregel, die der Walk seit
  jeher über `last_finished_at` hat; kein Datenverlust, nur Verzögerung des
  Aufräumens um höchstens die Sprungweite, und die 30-Tage-Frist der
  Abwesenden hängt am eigenen Stempel je Speicher, nicht an dieser Kadenz.
  Eine Sonderbehandlung (Stempel > now kappen) wäre neuer Code für einen
  Randfall ohne Zusageverletzung. Kein Owner-Punkt.

### F-43A-03 (LOW, akzeptiert): Eine Warnzeile je Overview-Abruf im Mischbetrieb

- **Datei:** `php/lib/Service/AdminViewService.php` (perDocumentCoverage,
  Zweig ADMIN_MISSING) plus `ExAppService::adminOutcome` (bestehende Zeile).
- **Szenario:** Companion 1.6.3 vor dem Container-Update: jeder Abruf der
  Admin-Übersicht schreibt "the backend has no per document count" (und die
  bestehende 404-Zeile von adminOutcome). Bei offener Admin-Seite pollt die
  Seite, also mehrere Zeilen je Minute, solange der Mischbetrieb anhält.
- **Entscheid: akzeptieren.** Der Zustand ist vorübergehend (Minuten, bis das
  neue Image läuft), die Zeile ist genau die Diagnose zum sichtbaren
  Lockstep-Banner, und das Muster ist das der bestehenden
  adminOutcome-Zeilen seit 1.5. Die Container-Gegenrichtung ist gedeckelt
  (404-Cooldown verdoppelt bis 1 h, eine Zeile je Stufe, per Test belegt).
  Kein Owner-Punkt.

### I-43A-01 (INFO): 422 bei veralteter Cache-Größe

Eine Datei, die der Dateicache mit Größe > 0 führt, die aber inzwischen leer
ist, bekommt OUTCOME_EMPTY bei size > 0 und damit 422 -> skipped(unreadable)
mit gedeckelter Wiederholung; mit der nächsten Cache-Aktualisierung heilt das
Urteil. Bewusste Vorsicht (POL-02: der Größe wird nicht geglaubt), kein
Handlungsbedarf.

### I-43A-02 (INFO): Unerwarteter Fehlertyp im Zähl-Thread geht an threading.excepthook

`_refresh` fängt OSError und sqlite3.Error; jeder andere Typ läuft in den
Standard-excepthook (Traceback auf stderr, unsere Frames, keine Nutzdaten).
Der Single-Flight wird im finally immer freigegeben (Probe B-h). Kein
Handlungsbedarf; sollte je ein dritter Fehlertyp real auftreten, wäre eine
Klassennamen-Zeile wie überall sonst der Weg.

### I-43A-03 (INFO): Erste Backfill-Runde ohne Marke setzt vorhandene Schlüssel einmal zurück

Eine Datenbank ohne `doc_key_backfill_after` (frische 1.6.3-Installation in
den ersten Sekunden, oder Upgrade) verliert in der ersten Runde einmal alle
bis dahin aus Aufträgen übernommenen Schlüssel und baut sie neu. Bei frischen
Installationen ist der Bestand in diesem Moment nahe null, beim Upgrade ist
der Neubau der Zweck. Absicht laut Docstring und Test
(test_a_missing_or_older_generation_rebuilds_every_key_once); kein
Handlungsbedarf.

### I-43A-04 (INFO): Der E2E-Harness lädt das eigene 1.6.2-Release von GitHub

`coverage_e2e.sh` holt für die Beine v1.6.2/upgrade das signierte
Companion-Archiv des eigenen Releases (feste URL, nur auf dem Runner). Kein
Instanzinhalt verlässt den Runner; kein Produktpfad. Kein Handlungsbedarf.

## Threat-Register dieses Plans

| ID | Urteil |
|---|---|
| T-43-27 (Audit endet vor dem Release-Kopf) | umgesetzt: audited_head im Frontmatter, Fix-Delta als Nachtrag unten, 43-10/43-12 prüfen den leeren Code-Diff zum Tag-Kopf |
| T-43-28 (/coverage ohne Admin) | umgesetzt: Probe test_every_declared_route_is_mounted_with_its_exact_case_and_verb plus Ratchet im Skript |

## Nachtrag: Fix-Delta d9f8a65d..37b518d6 (08.11.2026)

`git diff --stat d9f8a65d..37b518d6` über die Code-Pfade: 3 Dateien, alle
backend (api/coverage.py 20 Zeilen, tests/test_measurement_scripts.py 11,
tests/test_phase43_audit.py 510 neu). Kein PHP, kein l10n, kein Workflow, kein
Skript, kein nutzersichtbarer Text; PHPUnit deshalb nicht neu nötig (php/
unverändert, Beleg-Läufe oben gelten weiter).

| Datei | Urteil |
|---|---|
| api/coverage.py | nur die Konstante und zwei Kommentare; der Hintergrundpfad, der jetzt ab 25.000 trägt, ist derselbe, den die Tests seit 43-04 fahren (Single-Flight, Cache, Stock-Kennung); counting-Satz und Cache-Verhalten unverändert |
| tests/test_measurement_scripts.py | Baumhash-Journal und PACKAGE_TREE_HASH_TODAY = 75212e53, Rezept und unabhängige Pipeline (find, sort, tr -d '\r', sha256sum, Zeilenformat Pfad NUL Hash) stimmen überein; Positivkontrolle: dieselbe Pipeline über den Baum von d9f8a65d ergibt den alten Hash 3d704f65 |
| tests/test_phase43_audit.py | die 15 Proben dieses Audits; die Deckel-Probe vor dem Fix rot gesehen (assert 100000 x 3.65e-05 <= 1.0 schlug fehl), danach grün |

Gates am Fix-Kopf (lokal, vor dem Commit): ruff check "All checks passed!",
ruff format --check "255 files already formatted", pyright (latest) "0 errors",
vulture 80 Exit 0; test_phase43_audit.py dreimal 15 passed; die sechs
Kernmodule 748 passed; neun Nachbarmodule 804 passed, 1 skipped.

## Urteil

0 CRIT, 0 HIGH, 0 MEDIUM offen über `v1.6.2..37b518d6`. Das eine MEDIUM
(F-43A-01) ist an der Ursache behoben und mit umgedrehter Probe samt Messung
belegt; der Fix bringt keinen neuen Befund. Beide LOW sind entschieden
(akzeptiert, Begründung je Befund oben), keiner verletzt eine Zusage; die vier
INFO sind dokumentierte Absichten oder Randlagen ohne Handlungsbedarf.
`audited_head` = `37b518d6754a4a8a8593dc537a13b27644caf986`; der CI-Beleg des
Kopfes folgt nach der Owner-Freigabe (Task 3).

## Für die Owner-Runde (43-12)

1. **F-43A-01** ist lokal gefixt (COVERAGE_SYNC_CEILING 25.000); sichtbare
   Folge: Instanzen mit 25.000 bis 100.000 Zeilen sehen nach dem Update einmal
   kurz den Satz "wird gezählt", danach die Zahl aus dem Hintergrundpfad.
   Kein Store-Text betroffen, kein CHANGELOG-Satz zwingend; wenn gewünscht,
   passt er unter Fixed ("coverage answers within the admin timeout on slow
   hardware").
2. **Keine Owner-LOWs.** F-43A-02 und F-43A-03 sind mit Begründung akzeptiert
   (dieselbe Kadenzregel wie der Walk; vorübergehende Diagnosezeile zum
   sichtbaren Banner).
3. **D-43-15** (verschiedene Wurzeln derselben Freigabe zählen doppelt) bleibt
   die bekannte Grenze aus dem CHANGELOG, Entscheidungspunkt K6 wie geplant.

## Läufe auf audited_head

Push 655fe197 (traegt den Fix-Kopf 37b518d6): alle gestarteten Push-Workflows
gruen (Python gates mit den 15 Audit-Proben, Resilience, HaRP deploy 26m41s,
Security scans, Multi-arch, Scorecard; PHP lief pfadbedingt nicht, Beleg bleibt
42513966089 auf unveraendertem php/). Dispatch "Coverage end to end"
42525415627: alle fuenf Beine gruen. Der MEDIUM-Fix F-43A-01 ist damit auch
end to end belegt.

## Fix-Delta nach dem Audit (09.11.2026)

Die rc-Branch-Läufe 42530680761 (HaRP) und 42530680760 (Python gates) deckten
zwei HARNESS-Fehler auf, kein Produktcode ist berührt; `audited_head` 37b518d6
bleibt unverändert gültig.

| Commit | Inhalt |
|---|---|
| 9f99df1f | `fix(43-10)`: das F2-Gate in tests/test_phase36_audit.py liest jetzt auch eine Prerelease-Version (`[0-9.]+` traf 1.6.3-rc.1 nicht, AssertionError in Lauf 42530680760); `_version()` ordnet eine Prerelease UNTER ihr Release (version_compare-Semantik: 1.6.2 <= 1.6.3-rc.1 < 1.6.3); Selbsttest mit dem rc-Beispiel erst rot gesehen, dann grün |
| bcab9012 | `ci(43-10)`: Zusicherung 18 (doc key backfill, D-43-14) pollt das Container-Log alle 5 s mit 240-s-Deckel statt genau einmal (Race gegen die Worker-Kadenz: Lauf 42513966073 prüfte bei Sekunde 62 und bestand, 42530680761 bei Sekunde 61 und scheiterte); bei Ablauf steht der bestehende ::error:: unverändert; dafür wandert der Schritt "Store upgrade 1" nach dem Muster 41-08 in scripts/ci/upgrade_from_release_assets.sh (deploy-harp.yml stand 36 Bytes unter dem 512000-Byte-Gate, jetzt 505990 Bytes, 6010 darunter); Wächter in test_upgrade_seed_steps.py erst rot gesehen, MOVED_STEPS nachgeführt |

Nur Workflow, Tests und scripts/ci; backend/src, php/ und l10n unberührt
(`git diff --stat 37b518d6..` belegt es). Baumhash-Journal unberührt, denn das
Rezept hasht nur backend/src/findling und php/. Gates am neuen Kopf lokal
gruen: ruff check, ruff format --check, pyright (latest) 0 errors, vulture 80
Exit 0; pytest test_phase36_audit (19 passed), test_workflow_size/pins/
contexts/tag_triggers, test_lockstep_versions, test_upgrade_seed_steps und die
übrigen Workflow-Wächter (zusammen 476 passed, 8 skipped); bash -n für das
neue Skript, YAML-Parse von deploy-harp.yml.
