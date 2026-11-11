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

## Nachtrag 43-27: Wurzeln und Schreibweisen (D-43-15, D-43-17)

**Stand:** 11.11.2026, lokal, vor dem Owner-Checkpoint für den Push.
**0 CRIT / 0 HIGH / 0 MEDIUM / 4 LOW / 7 INFO** über den Code-Delta
`37b518d6..2261167b` (E2E-Kopf des grünen Laufs 43016026129; `git diff
2261167b..HEAD -- . ':!.planning'` enthält nur die zwei Test-Commits dieses
Plans unter backend/tests). Kein Produktcode geändert, kein Baumhash bewegt.
Das Frontmatter ist bewusst NICHT angefasst: `audited_head`, `status_43_27`
und `d_43_15` lassen sich erst nach dem Push binden (Abschnitt "Was nach dem
Push noch einzutragen ist").

### Umfang

`git diff --stat 37b518d6..2261167b -- . ':!.planning'`: 49 Dateien, 8.628
Zeilen dazu, 703 weg. Über den Planumfang hinaus ausdrücklich enthalten: der
Reset der Dokumentschlüssel in Bändern (53373888, c93a6f1e), Fix 1
(07eadd03, e02ff71f) und die Harness-Commits von 43-26.

Lesetiefe, ehrlich benannt: "ganz" heißt die ganze Datei, "Diff plus
Methoden" heißt der Diff und jede geänderte Methode samt ihren Aufrufern
ganz, der unveränderte Rest der Datei nicht erneut (er lag dem Audit 43-09
vor). Die Regel "jede geänderte Datei ganz" ist damit für sechs große Dateien
NICHT voll erfüllt; sie sind in der Tabelle so markiert.

| Datei | Lesetiefe | Urteil |
|---|---|---|
| backend/src/findling/worker/doc_keys.py | ganz | Generation 2, Reset vor dem Meta-Wert (:387-391), Runde ohne state.db nach 5 s (:346-352), fremdes Format wie fehlende Route, Prüflauf schreibt für absent die Sentinel (:461-477); Proben R1, R2, V; ok |
| backend/src/findling/api/coverage.py | ganz | Sperre vor Zählung und Cache (:398-406), docKeyFormat als echte Ganzzahl, 422 vor note_coverage_call; ok |
| backend/src/findling/store/repo.py | Diff plus Methoden (reset_doc_keys, set_doc_keys, Coverage-SQL, _transaction) | Bänder zu 100.000 über den Primärschlüssel, je eine Transaktion, Kante nach jedem Commit neu gefragt (:1714-1731); F-43B-03 (:2441, außerhalb des Deltas) |
| backend/src/findling/nc/files.py, nc/queue.py | Diff plus Methoden | format und docKeyFormat nur als `type(...) is int` und gleich 2; ok |
| php/lib/Service/StorageService.php | ganz | shareIdentity, shareIdentities, resolveHashed, rebuiltIds; nur fünf Konfigurationsschlüssel, nie password; F-43B-01 (:779-789, :907-938) |
| php/lib/Service/DocKeyService.php | ganz | Format 2 über Freigabe NUL Freigabe-Pfad, NFC, keine Faltung von Wurzel und Pfad; F-43B-01 (:202-205) |
| php/lib/Service/FileStateService.php | Diff plus Methoden (distinctPathsByReasons, phpOnlyRows, withoutOtherVerdicts, heldWithoutVerdict, belowRoot) | Schlüssel und N1 aus derselben Regel (sharePathOf), Präfixgrenze `root + '/'`; F-43B-04 (:981-1012) |
| php/lib/Service/AdminViewService.php | Diff plus Methoden (countingShares, logShareIdentities, coverageBody, perDocumentAnswer, perDocumentFiguresFor) | ein Aufruf shareIdentities je Overview, Zähler direkt danach, Logzeile nur fünf Zahlen; ok |
| php/lib/Service/QueueService.php, Controller/ReconcileController.php | Diff plus Methoden | docKeyFormat neben jedem docKey, format in der Antwort; ok |
| .github/workflows/coverage-e2e.yml, rc-version-proof.yml | Trigger, permissions, uses, Eingaben | nur workflow_dispatch, contents: read, Actions mit vollem SHA, Eingaben nur über env, keine `${{ }}` in run-Zeilen; ok |
| .github/workflows/deploy-harp.yml | Diff | Schritt nach scripts/ci/upgrade_from_release_assets.sh verschoben (43-10); ok |
| scripts/ci/coverage_e2e.sh | Diff plus die Abschnitte B1, Topologieänderung, Phase A, judge_locked, read_settled, age_sweep_stamp | set -euo pipefail, keine Passwortausgabe, kein set -x; Befunde I-43B-01 und I-43B-03 |
| scripts/ci/coverage_truth.sh, rc_version_proof.sh, upgrade_from_release_assets.sh, e2e_head_proof.sh (ganz), e2e_head_proof_selftest.sh | Diff, Abrufe und Shell-Optionen | Abrufe nur eigenes Release, eigenes Repo und das öffentliche Zertifikat aus nextcloud/app-certificate-requests, nur auf dem Runner; ok |
| scripts/release/store-archive.sh, scripts/dev/phpunit_docker.sh | Diff | CHANGELOG.de.md und CHANGELOG.fr.md reisen im Archiv mit; Kataloge schreibgeschützt eingehängt; ok |
| CHANGELOG.md, CHANGELOG.de.md, CHANGELOG.fr.md, docs/store-listing.md | Diff von CHANGELOG.md | vier neue Punkte in 1.6.3 (Entwurf für 43-12 Runde 2), Gleichschritt-Test grün; die Texte selbst sind Sache der Owner-Runde |
| backend/tests/*, php/tests/* (23 Dateien) | Testnamen und die für die Belege benutzten Fälle | als Belege unten benannt; PHP-Tests nicht lokal gefahren (siehe "Nicht belegt") |

### Methode

- Neun Proben in `backend/tests/test_phase43_audit_roots.py` (Commit
  a2bc46ad), eigene Zeilen, eigene Companion-Attrappe, Schlüssel selbst
  gerechnet. Gegenprobe mit sieben Einzelmutationen der Quellen, anderes
  Muster als die Umsetzung, Wiederherstellung per sha256sum -c belegt:
  Meta-Wert vor dem Reset (rot), ein UPDATE über die ganze Tabelle (2 rot),
  Kante der Bänder nur am Anfang gefragt (rot), Arming hinter dem Blick neu
  gefragt (Probe F-43B-02 rot, wie für den Fix angekündigt), silence ohne
  Wirkung (2 rot). 0 Überlebende.
- Belege des Laufs 43016026129 aus den Artefakten und Job-Logs unter
  `scratchpad/e2e-fix1` (art, logs), Zeilenangaben wie in 43-E2E-WURZEL.md.
- PHP nur per Durchsicht plus CI-Beleg: PHPUnit "OK (1197 tests, 7647
  assertions)" Lauf 42987540725 auf a42d2dc6, `git diff a42d2dc6 2261167b --
  php` leer. In diesem Plan ist keine PHP-Datei geändert.
- Gates vor beiden Commits: ruff check "All checks passed!", ruff format
  "258 files already formatted", pyright (latest) "0 errors, 0 warnings",
  vulture 80 Exit 0. pytest mit Modulauswahl und timeout 540: zwölf Module um
  Schlüssel, Zählung und Kataloge 1238 passed; zwölf Module um Lifespan,
  Reconcile, Catch-up, Pause, Leseschicht, Speicher 741 passed. Die volle
  Suite lief lokal nicht (Regel des Auftrags).

### Security (T-43-84, T-43-85)

| Hypothese | Beleg | Ergebnis |
|---|---|---|
| password oder andere Zugangsdaten werden gelesen | StorageService REBUILT_CONFIG_KEYS = host, share, root, user, port, die Abfrage bindet genau diese Liste (:887-891) und prüft jeden Schlüssel der Antwort erneut (:897); Grep nach "password" in den drei Zählklassen: nur zwei Kommentarzeilen; PHPUnit testTheConfigurationIsAskedForFiveKeysAndNeverForAPassword | nie gelesen |
| Pfad, Host, Freigabe, Wurzel, Anmeldename in Log oder Antwort | neue Logzeilen des Deltas: Python 1 (nur Sekundenzahl), PHP 4 (fünf Zähler, Anzahl, Exception-Klasse); PHPUnit testNoLogLineCarriesAHostAShareARootOrALogin, testTheLogLineCarriesFiveWholeNumbersAndNoName, testTheAnswerCarriesNoPathNoShareOnlyHex, testTheAnswerCarriesCountsOnly; Python test_the_log_lines_carry_numbers_and_never_a_path_or_a_key | nur Zahlen |
| Freigabe-Identität oder doc_key außerhalb der Zählpfade | test_share_identities_are_asked_by_the_counting_services_only, test_document_keys_are_asked_by_the_counting_services_only, test_no_search_path_gateway_or_listener_code_touches_the_counting, test_the_search_never_reads_a_doc_key (je mit Positivkontrolle); Suchprobe W5 im Lauf: 15 von 15 Zeilen in sieben Beinen | nur Zählung |
| Berechtigungsdurchgriff berührt | kein Diff in SearchService, PathResolverService, GatewayController, Listener (git diff --stat); W5: kein Nutzer bekommt privat.txt des anderen hinter [homes] | unberührt |
| Neuer Eingang, neue Route, neuer Abruf nach außen | backend/appinfo und php/appinfo ohne Diff; URL-Grep über backend/src und php/lib: kein neuer Abruf (ein parse_url-Hilfspräfix); neues Overview-Feld coverage.shareIdentity nur fünf Ganzzahlen (shareIdentityCounters) | keiner |
| Workflows | nur workflow_dispatch, contents: read, gepinnte Actions, Eingaben über env | ok |

### STOPP-Regel (T-43-84)

`git diff --stat 37b518d6..HEAD` über php/lib/Migration, store/schema.sql,
store/vectors.sql, index/schema.py, backend/appinfo, php/appinfo, php/l10n,
php/js, php/templates, backend/docker: leer. Im Diff von backend/src kein
Treffer auf SCHEMA_VERSION, STORE_SCHEMA_MARK oder einen neuen Meta-Schlüssel;
im Diff von php/lib kein Treffer auf IAppConfig, setValue, getValue,
deleteKey. Die Ausnahmen und ihre Owner-Zeilen (43-FREIGABEN.md, je
"Entscheid: a"):

| Ausnahme | Inhalt | OE-Zeile | im Diff gefunden |
|---|---|---|---|
| A-1 | DOC_KEY_GENERATION 1 nach 2 im bestehenden Meta-Wert | OE-5 | doc_keys.py, ein Wert, kein neuer Schlüssel |
| A-2 | docKeyFormat im Auftrag und in POST /coverage, format in GET /reconcile/doc-keys | OE-5 | QueueService, ReconcileController, AdminViewService, coverage.py, files.py, queue.py |
| A-3 | lesende Abfragen auf oc_mounts, oc_external_mounts, oc_external_config | OE-2 | StorageService resolveHashed, nur SELECT |
| A-4 | PHPUnit lokal per Docker | OE-6 | scripts/dev/phpunit_docker.sh (Katalog-Mount) |
| A-5 | Feld coverage.shareIdentity und eine Logzeile je Stunde über den lokalen Cache | OE-2 | AdminViewService, ICacheFactory::createLocal, kein AppConfig |

Weitere Ausnahmen gibt es nicht. Die zwei Konstanten außerhalb der Liste
(_RESET_DOC_KEYS_BAND, DOC_KEY_NO_STATE_SECONDS) sind Zeitverhalten, kein
Schema, kein Schlüssel, kein Vertrag.

### Verschmelzungsliste: wann zwei Speicher als eine Freigabe zählen

Leitregel: zwei verschiedene Dateien dürfen nie ein Dokument werden; jeder
Zweifel endet ungruppiert (Zahl zu hoch, nie verschmolzen).

| Weg | Regel | Beleg | Urteil |
|---|---|---|---|
| Faltung von Host und Freigabe | ASCII-klein (PHP ab 8.2, strtolower ohne Locale), sonst nichts | testTheMbozemSituationIsOneShareOfFortySevenStorages, testAnotherHostOrAnotherShareIsNeverAGroup, test_the_mbozem_spellings_are_one_share; E2E: Mount /Daten-gross zählt mit /daten einmal (k = 4 in sechs Beinen) | hält |
| Wurzel-Normalisierung ('.', '//', '..', Backslash) | '.' und leere Segmente fallen, '..' und Backslash geben keine Identität | Katalog share_identity_cases.json, testEveryCatalogueCaseYieldsItsHandTypedIdentity, testADoubleSlashInTheLoginNameIsNeverAGroupAndOneInTheRootCollapses | hält |
| Groß- und Kleinschreibung in Wurzel und Pfad | nie gefaltet | test_a_root_that_differs_only_in_case_is_another_root, testRootAndPathAreNeverFolded; E2E: Bericht.txt und bericht.txt zwei Zeilen und getrennt gefunden | hält |
| Unicode | NFC wie Nextcloud (Cache.php normalize, stable34 :1253-1255); NFC/NFD-Zwillinge sind schon in Nextcloud eine Zeile | Katalogfall Wurzel mit NFD-Umlaut; Grenze von Nextcloud, nicht von Findling | hält, Grenze benannt |
| Gehashte IDs | Identität nur bei exaktem md5-Treffer des nachgebauten Namens | testEveryHashedCatalogueEntryNeedsAMatchingMd5, test_every_stored_md5_is_recomputed_and_only_a_match_gives_an_identity; E2E: hashedVerified 3, hashedUngrouped 2 in sechs Beinen | hält; Lücke F-43B-01 beim Schlüssel, nicht bei der Gruppe |
| $user und andere Platzhalter | $user ersetzt, jedes andere $ gibt keine Identität | Katalogfälle "$user in the root", "another placeholder than $user is never rebuilt", "a hidden share with '$'" | hält (versteckte Freigaben mit $ bei gehashter ID bleiben ungruppiert) |
| [homes] und Freigabe gleich Anmeldename | nie gruppiert (OE-3 a) | Katalogfall "Samba homes rebuilt with a matching md5 is still never grouped"; E2E: privat.txt je Nutzer 2 von 2, W5 vier Zeilen | hält |
| SFTP | je Anmeldung und Host mit Port (OE-4 a) | testSftpIsGroupedPerLoginWithItsPortAndOtherBackendsAreNot | hält |
| Samba %U, %S auf der Serverseite | nicht erkennbar | bekannte Grenze, OE-7 a, Known limitation im CHANGELOG-Entwurf | Grenze, Owner-entschieden |
| Mischbetrieb 1.6.2 mit Kopf-Container | kein /coverage, Backfill wartet (404) | Bein upgrade: X 68, E 94, E 95 | hält |
| Mischbetrieb rc.1-Companion mit Kopf-Container | 422, 1.6.2-Weg, kein Auftrag schreibt einen Schlüssel | Bein upgrade-rc1: E 21 bis E 24, X 66 | hält |
| Mischbetrieb Kopf-Companion mit rc.1-Container | 422, 1.6.2-Weg; rc.1 nimmt Format 2 ungeprüft, das Update setzt zurück | Bein upgrade-rc1-cf: E 22, E 23 | hält |
| Kopf mit Kopf nach rc.1, vor dem Reset (Zeitfenster, Generationssperre) | counting, keine Zahl aus Format 1 | Bein upgrade-rc1-cf: E 24 bis E 27 unter der Backup-Pause; test_coverage_counts_nothing_during_a_backup_pause_before_the_reset; Probe R1 für den abgebrochenen Reset | hält |
| Kopf-Companion mit 1.6.2-Container | 404, 1.6.2-Weg | test_status_with_leave_out_still_answers_for_a_companion_1_6_2; Bein upgrade (Rückweg) | hält |
| Identität ändert sich zwischen Auftrag und Zählung | Annahme des Plans: nur Überzählung, weil die Freigabe im Schlüssel steht | Probe test_p_f_43b_01: ein Mitglied ohne Identität zählt zu viel (2 statt 1), zwei Mitglieder ohne Identität unter zwei Wurzeln verschmelzen zwei Dateien (1 statt 2) | **Annahme trifft in einem Fall nicht zu, F-43B-01 (LOW)** |
| Geänderte Konfiguration mit alter oc_mounts-Zeile | der md5 des Nachbaus trifft die alte ID nicht, also keine Identität | Katalogfall "the configuration no longer matches the stored id", testASecondCallReadsTheConfigurationAfresh | hält (ungruppiert) |
| Überlappende Unterwurzeln /a und /a/b | Freigabe-Pfad ist Wurzel plus Pfad, N1 fragt je Wurzel den Rest; Grenze `root + '/'`, also trifft /a nicht /ab | testOneUnreadableFileUnderTwoRootsIsOneDocument, testTwoFilesWithOneInternalPathUnderTwoRootsStayTwoDocuments, testN1ForAMemberUnderARootAsksThePathBelowItsRoot, testAMemberWhoseRootDoesNotHoldThePathIsNotAsked; E2E: Wurzeln /, sicherheit, projekt | hält |

### Reset in Bändern (53373888, c93a6f1e) und Fix 1 (07eadd03, e02ff71f)

| Frage | Beleg | Ergebnis |
|---|---|---|
| Abbruch mitten im Reset | Probe test_a_reset_that_breaks_off_between_two_bands_...: nach dem Fehler im zweiten Band ein Band vergessen, zwei mit alten Schlüsseln, Meta-Wert unverändert Generation 1, niemand gefragt, in_flight gefallen; die nächste Runde vergisst den Rest, und im Augenblick des ersten Meta-Schreibens steht kein alter Schlüssel mehr | Sperre hält, zweiter Lauf räumt auf |
| Gleichzeitige Schreiber und neue Zeilen | Probe test_writers_and_new_rows_between_two_bands_...: Schlüssel in ein fertiges Band bleibt, in ein offenes Band wird vergessen und neu gefragt, neue Zeile über allen IDs wird von einem weiteren Band erreicht, neue Zeile in einer Lücke bleibt; kein alter Schlüssel übrig | hält |
| Garantiert "erst Reset, dann Meta-Wert" unter Bändern dasselbe wie in 43-24 | Ja, mit einer Voraussetzung, die im Code gilt: jeder Schreiber eines Kopf-Containers schreibt nur Format 2 (queue.py `_doc_key`, files.py `_names_the_format`), also kann nach dem Reset nur NULL oder Format 2 stehen. Bestehend: test_the_keys_are_gone_before_the_mark_says_generation_two; neu Probe R1; Mutation "Meta-Wert vor dem Reset" rot | gleichwertig |
| 5 s zwischen Geburt der Datenbank und Runde | ein Auftrag kann einen Schlüssel schreiben, die Runde vergisst ihn und fragt im selben Zug neu; antwortet die Companion nicht, wartet der Rest einen Takt, die Sperre hält so lange nicht mehr (Meta-Wert steht), die Zeilen zählen als fehlend, also counting | richtig, keine falsche Zahl |
| Companion zuerst: rc.1-Container nimmt Format 2 ungeprüft | der Kopf-Container kann sie nicht unterscheiden und vergisst sie einmal | sichere Richtung, Bein upgrade-rc1-cf |
| Runde läuft beim Eintreffen der Backup-Pause schon | Reset und Meta-Wert werden noch geschrieben; der Koordinator hat keinen eigenen Zeitdeckel und sagt erst paused, wenn in_flight gefallen ist (pause.py), danach beginnt kein Band mehr | kein Schreiben nach "paused" |

### Die fünf Prüfpunkte aus dem grünen Lauf 43016026129

**1. Nenner in Phase A schwankt (35, 64, 65, 66): erwartetes Verhalten,
Vermutung bestätigt (I-43B-01).** Ursache am Code: ein Bild, das hinter dem
Crawl hochgeladen wird, steht in keinem Scan-Zähler. Der erste Pass schreibt
skipped(no_text_layer) und reicht es an OCR weiter (poller.py hand_over,
KIND_OCR); ab diesem Urteil ist die Zeile judged (repo.py :2305-2307), und der
Nenner je Teil ist max(Scan-Zähler, judged plus PHP-only). Beleg aus den
Containerlogs: in gate-queue / native und upgrade-rc1-cf steht "POST
/coverage" VOR "pass finished, claimed=32 ... skipped=29 ... requeued=29"
(X 65 gegen X 70, X 129 gegen X 134): Nenner 35. In gate-queue / wrapped
steht der Pass davor (X 62 gegen X 67): Nenner 64, also 29 Bilder mehr; in
upgrade und upgrade-rc1 war auch das dreißigste Bild beurteilt (65, 66).
Probe: test_a_picture_that_waits_for_ocr_is_judged_from_its_first_pass_on_...
Kein Produktfehler: der Nenner läuft neuen Dateien bis zu ihrem ersten Urteil
nach, das ist die Regel D-43-11 seit 43-05. Harness-Schwäche: Phase A prüft
die Anzeige gegen die Regel im Augenblick des Lesens, nicht gegen eine feste
Zahl. Empfehlung (nicht umgesetzt, wäre ein neuer Lauf): die Übersicht in
Phase A erst lesen, wenn der erste Pass geendet hat, dann ist der Nenner in
jedem Bein mit Rückstau derselbe.

**2. "doc key verify, checked=95 corrected=3" (im Bein upgrade 2): richtig,
Vermutung widerlegt (I-43B-02).** Es sind nicht die Zeilen des Carol
entzogenen Speichers (dessen ID ist ausgeschrieben, seine Dateicache-Zeilen
bleiben, kein Schlüssel ändert sich). Es sind die drei indexierten Dateien
im Home des gelöschten Nutzers dave (dave-1.txt, dave-2.txt, verwaist.txt):
`occ user:delete` nimmt die Dateicache-Zeilen weg, der Container, der für
Phase A startet, prüft sofort, die Companion nennt die drei IDs absent, jede
bekommt die Sentinel. Im Bein upgrade hat das Harness die Dateicache-Zeile
von verwaist.txt schon vorher gelöscht (docKeysUnresolved=1, E 95), diese
Zeile trägt die Sentinel schon: 2. Die Logzeile steht in jedem Bein direkt
vor "storage sweep ... gone=1 ... removed storages [23]". Probe:
test_the_verify_pass_counts_the_rows_whose_file_cache_row_went_as_corrections
(3 und 2). Nicht aus dem Lauf selbst belegbar: welche drei Datei-IDs es
waren (die Artefakte enthalten keine state.db); die Herleitung stützt sich
auf Code, Harness-Ablauf und die Zahlen 3, 3, 3, 3, 3 und 2.

**3. Zeitreserve der wrapped-gate-Beine (112 s): Harness-Befund mit
Empfehlung, nicht umgesetzt (I-43B-03).** Risiko: der Aufbau bis zum Stopp
brauchte 188 s von 300 s; ein um 60 Prozent langsamerer Runner macht den Lauf
ungültig (W5 bricht ab, es entsteht nie eine falsche Zahl). Der vorige Lauf
lag bei 187 bis 203 s, die Streuung ist also klein gegen die Reserve, aber
nicht abgesichert. Die vorgeschlagene Lösung (Catch-up abwarten, Stempel
altern wie in den rc.1-Beinen) ändert die Aussage von Phase A: heute zeigen
die gate-Beine den ERSTEN Sweep einer frischen Installation (storage_sweep_at
"not set"), danach zeigten sie wie die rc.1-Beine einen fälligen Sweep nach
gealtertem Stempel. Deshalb nach der Regel des Auftrags nicht umgesetzt.
Empfehlung in zwei Stufen: (a) ohne Änderung der Aussage die gedrosselten
Proben der wrapped-Beine (71 s) hinter den Stopp des Containers legen, das
hebt die Reserve auf rund 180 s; zu prüfen, ob eine Probe den laufenden
Container braucht. (b) Wenn die Aussage "erster Sweep" entbehrlich ist, weil
die rc.1-Beine und das Bein upgrade den Sweep hinter blockiertem Tor ohnehin
zeigen: Catch-up abwarten und Stempel altern. Beides ändert scripts/ci und
verlangt einen neuen E2E-Lauf für die Bindung.

**4. Flakiger Test test_a_disable_while_the_cycle_waits_silences_it_again:
Ursache ist ein Fenster im Produkt (F-43B-02, LOW), der Test ist
stabilisiert.** Vorher 7 von 300 rot (3, 3, 1 je 100), immer "assert 1 ==
0". Ursache: `Reconcile.run(once=True)` fragt das Arming, liest dann die
Marke im Thread (`_catchup_mark`) und fragt danach nur die Backup-Pause
erneut (reconcile.py :460), nicht das Arming. Ein Disable, das in dieses
Lesen fällt, hält die Runde nicht auf. Beweis der Ursache: mit der einen
zusätzlichen Bedingung (Arming hinter dem Lesen neu gefragt) ist der ALTE
Test 300 von 300 grün, und die Probe test_p_f_43b_02 kippt wie angekündigt.
Der Test selbst (Commit cdd16d05) lässt das laufende Lesen jetzt enden,
bevor er die Marke schreibt (in_flight kann nach dem Disable nur fallen):
600 von 600 grün; mit wirkungslosem silence rot. Das Fenster hat eine eigene
Probe und eine eigene Kontrolle.

**5. 72 mal "coverage count without a vector stock", 24 mal "vector stock
could not be opened": Folge des Harness, mit einem kleinen Produktanteil
(F-43B-03, LOW).** Das Harness startet mit FINDLING_EMBED_ENABLED=false, es
gibt keine vectors.db. Die erste Zeile fällt je synchroner Zählung (5, 5, 5,
9, 9, 39 je Bein, gleich der Zahl der POST /coverage mit Zahl; im Bein
upgrade-rc1-cf 9 von 14, die übrigen fünf enden an der Sperre vor der
Zählung), die zweite einmal je Prozessstart (2, 3, 3, 4, 5, 5, 2). Die Zahlen
sind richtig (Vektorzahl 0). Produktanteil: eine Instanz, die Embeddings
bewusst abschaltet, bekommt bei jedem Blick auf die Admin-Seite eine
WARNING-Zeile im Containerlog.

### Performance und Hochrechnungen (gemessen gegen gerechnet)

| Größe | Wert | gemessen oder gerechnet |
|---|---|---|
| Reset bei 491.000 Zeilen, ein UPDATE | 7,7 bis 9,1 s Schreibsperre | gemessen (c93a6f1e, x86, SSD) |
| Reset in Bändern zu 100.000 | zweiter Schreiber wartet höchstens 2,4 s, gesamt 9 bis 10 s | gemessen (c93a6f1e) |
| Reset auf ARM oder langsamer Platte | mit Faktor 5 rund 12 s je Band, über dem busy_timeout von 10 s; Folge wäre ein abgebrochener Pass des Pollers, der wiederholt wird (poller.py fängt je Pass) | gerechnet, nicht gemessen (I-43B-05) |
| Reset beim Update 1.6.2 nach 1.6.3 | alle Schlüssel sind NULL, das UPDATE trifft keine Zeile | Durchsicht |
| Neuaufbau bei 491.000 Zeilen | 25 Bänder zu 200 je Runde, eine Runde je 300 s: 99 Runden, rund 8,2 bis 8,9 h "wird gezählt" | gerechnet aus den Konstanten und aus 65 s je 1.000 Zeilen (43-16, CI-Hardware); der Lauf 43016026129 misst den Durchsatz nicht (95 Zeilen, nur Wartezeit) |
| Abfragen je Auftragsstapel (docKeysFor) | je 200 Datei-IDs eine Dateicache-Abfrage plus eine auf oc_storages, bei gehashten IDs drei weitere: 2 bis 5 | Durchsicht, PHPUnit testTheIdentitiesAreAskedOncePerBandWithTheDistinctStorages |
| Abfragen je Overview, mbozem (101 Mounts, 47 Mitglieder, ausgeschriebene IDs) | shareIdentities 1, Verweigerungen je Speicher 1, PHP-only 1, N1 je Wurzel mit Kandidaten und je 1.000 Hashes 1: zusammen 4 bis etwa 6 | gerechnet aus dem Code; PHPUnit testTheIdentitiesAreAskedOnceAndHandedToTheGroupingAndTheCount, testUnhashedIdsAskNothingButTheStorages |
| Abfragen je Overview, 1000 Mitglieder einer Wurzel | shareIdentities 5 bis 6 (Bänder zu 200), sonst wie oben; N1 eine je 1.000 Kandidaten | gerechnet |
| Abfragen je Overview, 1000 Mitglieder mit 1000 Wurzeln ($user in der Wurzel) | N1 bis zu einer Abfrage je Wurzel, unter der ein PHP-only-Kandidat liegt, also höchstens 1000, dazu Wurzeln mal Kandidaten Vergleiche in PHP | gerechnet, nicht gemessen (F-43B-04) |
| shareIdentities bei 50.000 eingebundenen Speichern | 250 Abfragen auf oc_storages je Overview, nur mit externen Speichern im Crawl | gerechnet (I-43B-06) |

### Befunde

#### F-43B-01 (LOW, offen, Owner-Punkt): Schlüssel ohne Identität für gehashte Speicher

- **Fundstelle:** `php/lib/Service/DocKeyService.php:202-205`,
  `php/lib/Service/StorageService.php:779-789` und `:907-938`,
  wirksam über `backend/src/findling/worker/doc_keys.py:461-477`.
- **Szenario:** Ein Speicher mit gehashter ID hat seine Identität nur,
  solange oc_mounts ihn zeigt und die Konfiguration lesbar ist. Fragt der
  Prüflauf in dieser Lücke (Speicher ausgehängt, Zeilen leben noch bis zum
  Sweep) oder scheitert eine der drei Konfigurationsabfragen (shareIdentities
  fängt den Fehler und lässt die gehashten IDs ungruppiert, statt zu werfen;
  der Satz im Klassenkommentar von docKeysFor "a failing lookup fails the
  whole answer" gilt nur für die erste Abfrage), gibt die Companion einen
  Schlüssel mit leerer Freigabe über den Pfad im Speicher aus. Kommt der
  Speicher zurück in seine Gruppe, zählt er bis zum nächsten Prüflauf
  (höchstens ein Tag Ruhe plus Durchlauf, sofort nach einem Neustart) zu
  viel. Sind ZWEI gehashte Mitglieder derselben Freigabe mit verschiedenen
  Wurzeln zugleich betroffen und liegt unter beiden Wurzeln eine Datei mit
  gleichem Restpfad, tragen beide denselben Schlüssel: zwei Dateien zählen
  als ein Dokument.
- **Beleg und Reproduktion:** `uv run --no-sync pytest
  tests/test_phase43_audit_roots.py -k f_43b_01` (Container-Seite: 2 und 1
  mit richtigen Schlüsseln, 2 und 2 mit einem Mitglied ohne Identität, 1 und
  2 mit zweien). Die PHP-Seite ist per Durchsicht belegt und durch die
  bestehenden Tests testAnEntryWithoutIdentityGetsTheFormWithAnEmptyShare und
  testAFailingConfigurationQueryLeavesHashedIdsUngroupedAndLogsCountersOnly
  beschrieben; ein eigener PHPUnit-Fall dafür existiert nicht.
- **Schwere LOW:** nur die Zahl auf der Admin-Seite, selten (gehashte ID,
  zwei Wurzeln, beide zugleich betroffen, gleicher Restpfad), heilt von
  selbst, keine Suche, keine Rechte, kein Datenverlust. Aber: es ist der
  eine Weg, auf dem die Leitregel der Pläne 43-21 bis 43-29 nicht hält, und
  die Annahme des Plans "nur Überzählung" ist damit falsch. Deshalb kein
  stilles Akzeptieren, sondern Owner-Punkt.
- **Fix-Skizze (nicht umgesetzt):** docKeysFor gibt für eine ID in
  32-hex-Form ohne Identität einen Schlüssel aus, der den Speicher trägt
  (Freigabe-Teil zum Beispiel '#' plus Speichernummer; keine echte Freigabe
  beginnt so), dann kann nichts mehr verschmelzen. PHP-Änderung mit Katalog,
  PHPUnit, PHP-Baumhash und neuem E2E-Lauf.

#### F-43B-02 (LOW, offen, Owner-Punkt): Disable im Blick auf die Catch-up-Marke

- **Fundstelle:** `backend/src/findling/worker/reconcile.py:451-462`
  (außerhalb des Deltas, gefunden über den flakigen Test).
- **Szenario:** Nur im einmaligen Catch-up-Zyklus bei ausgeschaltetem
  Reconcile: fällt das Disable in das Lesen der Marke, läuft noch eine Runde
  gegen eine eben abgeschaltete Instanz. Fenster von Millisekunden je Takt
  von 300 s. Dieselbe Klasse wie F-41A-02 (dort für die Backup-Pause, mit
  c8fa6d98 behoben).
- **Beleg und Reproduktion:** `-k f_43b_02` (Fenster künstlich offen
  gehalten: rounds == 1, Marke done) und die Kontrolle `-k
  between_two_looks` (rounds == 0).
- **Fix-Skizze (nicht umgesetzt, Wirkung belegt):** in Zeile 460 das Arming
  mitfragen (`or not self._armed.is_set()`); damit war der alte Test 300 von
  300 grün. Produktänderung, also Paket-Baumhash und neuer E2E-Lauf.

#### F-43B-03 (LOW, offen, Owner-Punkt): WARNING je Zählung ohne Vektorbestand

- **Fundstelle:** `backend/src/findling/store/repo.py:2441` (außerhalb des
  Deltas, aus 43-03).
- **Szenario:** Ohne vectors.db (Embeddings abgeschaltet, oder vor dem ersten
  Vektor) schreibt jede synchrone Zählung eine WARNING-Zeile; die Admin-Seite
  fragt bei jedem Abruf. Die Zahl ist richtig. Die Suchseite behandelt
  denselben Zustand bei abgeschalteten Embeddings als normal
  (api/resources.py :944).
- **Beleg und Reproduktion:** `-k f_43b_03` (drei Zählungen, drei Zeilen);
  im Lauf 72 Zeilen bei 72 Zählungen.
- **Fix-Skizze (nicht umgesetzt):** einmal je Prozess, oder info, solange
  embed_enabled aus ist.

#### F-43B-04 (LOW, akzeptiert): N1 je Wurzel kostet Wurzeln mal Kandidaten

- **Fundstelle:** `php/lib/Service/FileStateService.php:981-1012`.
- **Szenario:** Eine Gruppe aus vielen Mitgliedern mit je eigener Wurzel
  ($user in der Wurzel, seit 43-21 eine Gruppe) fragt N1 je Wurzel, unter der
  ein PHP-only-Kandidat liegt, und vergleicht in PHP jede Wurzel mit jedem
  Kandidaten. Gedeckelt durch COVERAGE_MAX_MEMBERS (1000 Mitglieder, darüber
  der sichtbare 1.6.2-Weg). Bei 1000 Wurzeln und 10.000 Kandidaten sind das
  zehn Millionen Zeichenkettenvergleiche und bis zu 1000 kleine Abfragen je
  Overview.
- **Entscheid: akzeptieren.** Gerechnet, nicht gemessen; Kandidaten sind nur
  Dokumente, die allein diese Seite beurteilt hat (unlesbar, hängengeblieben,
  gone), und in einer Freigabe mit Heimatwurzeln je Nutzer sind das wenige.
  Die Lage des Melders (47 Mitglieder, wenige Wurzeln) kostet 4 bis 6
  Abfragen. Kein Owner-Punkt, aber für eine spätere Messung vorgemerkt.

#### INFO

- **I-43B-01:** Nenner in Phase A, siehe Prüfpunkt 1. Erwartetes Verhalten,
  Harness liest zu verschiedenen Zeitpunkten.
- **I-43B-02:** corrected=3 und 2, siehe Prüfpunkt 2. Richtiges Verhalten.
- **I-43B-03:** Zeitreserve 112 s, siehe Prüfpunkt 3. Harness, Empfehlung.
- **I-43B-04:** Neuaufbau bei 491.000 Zeilen rund 8,2 bis 8,9 h ohne Zahl
  ("wird gezählt"). Wie gebaut (43-16), für die Texte in 43-12 zu wissen;
  betrifft das Update von rc.1 und von 1.6.2 gleich.
- **I-43B-05:** Bandsperre auf langsamer Hardware gegen das busy_timeout von
  10 s nicht gemessen; Folge wäre ein wiederholter Pass, kein Verlust. Trifft
  nur Instanzen mit vorhandenen Schlüsseln (rc.1).
- **I-43B-06:** shareIdentities fragt oc_storages in Bändern zu 200 für alle
  eingebundenen Speicher, auch die Homes: 250 Abfragen je Overview bei 50.000
  Speichern, nur mit externen Speichern im Crawl.
- **I-43B-07:** Aus 43-E2E-WURZEL.md unverändert offen und kein Audit-Befund:
  skipped/gone beim Claim nicht gezeigt (gone_path=not_exercised), PHPUnit
  nicht auf dem Kopf des Laufs (Pfadfilter), der parametrisierte rc-Proof
  nicht auf dem Kopf gelaufen, Linkfreigabe ohne eigene Ergebniszeile.

### Abweichungen vom Plan

1. **rc.2 gestrichen (Owner 09.11.2026, 43-28 entfällt).** Betroffene Stellen
   des Plans: key_links ("43-28 (rc.2)"), der Kontext des Checkpoints ("rc.2
   baut darauf"), option-a ("rc.2 kann folgen"), option-b ("43-28 wartet"),
   Trust Boundary und T-43-83 ("geht in rc.2", "im rc.2"). Umgesetzt in der
   Fassung ohne rc.2: der Versionsnachweis ist rc.1 nach 1.6.3 direkt (Beine
   upgrade-rc1 und upgrade-rc1-cf), der audited_head bindet 43-29, 43-12 und
   43-13.
2. **Umfang größer als der Plan:** Reset in Bändern, Fix 1 und die fünf
   Prüfpunkte aus dem grünen Lauf sind mit auditiert (Auftrag).
3. **Kein Fix nötig nach der Planregel** (kein Befund ab MEDIUM); deshalb
   kein RED/GREEN-Paar am Produkt. Die zwei Test-Commits ändern nur
   backend/tests.
4. **Lesetiefe:** sechs große Dateien nur als Diff plus Methoden, siehe
   Umfang.
5. **Das verify von Task 3 ist ohne PHP-Änderung nicht erfüllbar:**
   `head_green.sh <A> ... "PHP and store metadata gates" ...` verlangt einen
   Lauf dieses Workflows AUF dem Kopf A. php.yml startet nur bei Änderungen
   unter php/, backend/appinfo und drei weiteren Pfaden und hat keinen
   workflow_dispatch. Ein Push ohne PHP-Änderung erzeugt diesen Lauf nicht
   (wie Abweichung 8 in 43-26). Dazu müssen die übrigen sechs Workflows auf A
   selbst laufen, also muss der Push genau bei A enden (siehe unten).

### Für die Owner-Runde

1. **Drei offene LOW (F-43B-01, F-43B-02, F-43B-03):** jetzt beheben (ein
   weiterer Arbeitsgang mit TDD, PHPUnit per Docker für F-43B-01,
   beide Baumhashes, danach Push und EIN neuer E2E-Lauf, der dann auch den
   PHP-Workflow auf dem Kopf mitbringt) oder nach v1.7 (dann bleibt die
   Bindung am Lauf 43016026129, und das verify von Task 3 braucht für den
   PHP-Workflow eine ausdrückliche Owner-Ausnahme wie in 43-26).
2. **I-43B-04** für die Texte: nach dem Update zeigt eine Instanz mit
   491.000 Zeilen rund neun Stunden "wird gezählt".
3. **F-43B-04** akzeptiert, keine Entscheidung nötig.

### Was nach dem Push noch einzutragen ist

Nichts davon steht heute im Frontmatter. Reihenfolge, damit die Workflows
auf A selbst laufen: zuerst genau bis A pushen (`git push origin <A>:main`),
A ist der letzte Commit außerhalb von .planning (`git log -1 --format=%H --
. ':!.planning'`, heute cdd16d05, nach einem `git pull --rebase` neu lesen),
danach die Planungs-Commits.

| Zeile im Frontmatter | Wert | Bedingung |
|---|---|---|
| `audited_head:` (die eine vorhandene Zeile ersetzen) | A, 40 hex | A liegt auf origin/main, `scripts/ci/e2e_head_proof.sh <A> 43-E2E-WURZEL.md` Exit 0 (ohne Code-Fix über den Lauf 43016026129, weil backend/tests nicht zu den Code-Pfaden des Skripts zählt; mit Code-Fix erst nach `Lauf-ID-Fix` und `Kopf-SHA-Fix` unter "## Nachtrag 43-27" in 43-E2E-WURZEL.md) |
| `audited_head_43_09:` | 37b518d6754a4a8a8593dc537a13b27644caf986 | zusammen mit der Zeile darüber |
| `diff_43_27:` | 37b518d6..A | |
| `findings_43_27:` | 11 (0 CRIT, 0 HIGH, 0 MEDIUM, 4 LOW, 7 INFO), bei Fixes neu zählen | |
| `critical_open_43_27:`, `high_open_43_27:`, `medium_open_43_27:` | je 0 | |
| `status_43_27:` | passed | erst wenn head_green.sh für A grün ist (sieben Workflows, oder sechs plus Owner-Ausnahme für den PHP-Workflow) und e2e_head_proof.sh Exit 0 |
| `recommendation_43_27:` | Text nach dem Owner-Entscheid zu den drei LOW | |
| `d_43_15:` | behoben | nur zusammen mit status_43_27 passed |

`status:` und `recommendation:` der Runde 43-09 bleiben unverändert (T-43-86).
Dazu der Abschnitt "Läufe auf audited_head" mit den Lauf-IDs der Workflows
auf A und dem E2E-Lauf.

### Nicht belegt

- PHPUnit lokal nicht gelaufen (keine PHP-Änderung in diesem Plan); der
  PHP-Stand ist durch den CI-Lauf 42987540725 auf a42d2dc6 bei leerem Diff
  unter php/ belegt, nicht durch einen Lauf auf 2261167b.
- Die PHP-Hälfte von F-43B-01 und die Kosten von F-43B-04 nur per Durchsicht
  und Rechnung.
- Welche drei Datei-IDs der Prüflauf korrigiert hat (keine state.db in den
  Artefakten).
- Bandsperre und Neuaufbau auf ARM und bei 491.000 Zeilen in echt; MySQL
  und PostgreSQL für die N1-Abfragen; eine echte Fremdinstanz.
- Die volle Python-Suite lokal (nur 24 Module mit Auswahl).
- Sechs große Dateien nicht ganz neu gelesen (siehe Umfang).
