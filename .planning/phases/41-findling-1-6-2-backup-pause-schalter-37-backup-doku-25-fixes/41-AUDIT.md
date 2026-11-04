---
phase: 41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes
audited: 2026-11-04
audited_head: 5dc1aa127a495c78ec4ef5272a275c6788c92af0
audited_head_before_issue_44: efdca6840ee89b3373d9706b0e3c94039c4ef8d4
audited_head_before_fixes: 738a13731f6448aa97f0a752d5553c6c54db3e85
diff: v1.6.1..efdca684
fix_delta: 738a1373..efdca684
fix_delta_issue_44: efdca684..5dc1aa12
files_reviewed: 46
fix_files_reviewed: 5
findings:
  critical: 0
  high: 0
  medium: 0
  low: 4
  info: 4
  total: 8
low_fixed: 4
low_open: 0
status: passed
recommendation: 1.6.2 mit den vier LOW-Fixes und dem Fix von #44 (Owner-Entscheide 04.11.2026); 41-11 taggt gegen audited_head 5dc1aa12 oder einen Kopf mit leerem Code-Diff dazu
---

# Phase 41: Audit 1.6.2 (Security, Bugs, Performance)

**Stand:** 04.11.2026, **0 CRIT / 0 HIGH / 0 MEDIUM / 4 LOW / 4 INFO** über den
ganzen Code-Delta `v1.6.1..738a1373` (Code-Kopf von 41-08; HEAD c5bb0850 ändert
nur `.planning/`). Keine Rechte-Umgehung, kein Datenleck, kein externer Dienst.
Die Pause hält, was Issue #37 zusagt, solange der Container läuft: in "paused"
bewegt sich kein Byte des Volumes (Probe P, Datei für Datei mit sha256). Die
vier LOW betreffen Randfälle, in denen trotzdem etwas schreibt: ein Stopp oder
Neustart des Containers während der Kopie, das einmalige Catch-up nach einem
Upgrade, der fp32-Sweep eines Vorab-Checks, und der stille Zustand "unknown"
ohne Companion (offene Frage aus 41-08). Kein Fix in diesem Plan; kein
Code-Pfad hat sich seit `audited_head` geändert.

## Umfang

Code-Kopf mechanisch: `git log -1 --format=%H -- backend/src backend/docker
backend/appinfo php/appinfo php/lib php/js php/templates php/l10n
.github/workflows scripts` = `738a13731f6448aa97f0a752d5553c6c54db3e85`.

`git diff --stat v1.6.1..738a1373` über diese Pfade: **46 Dateien, 2523 Zeilen
dazu, 253 weg**. Jede Datei mit Urteil:

| Datei | Plan | Urteil |
|---|---|---|
| backend/src/findling/worker/pause.py (neu, 398) | 41-03/04 | gelesen ganz; Zustandsmaschine korrekt (Q, R); Schreiber-Inventar unvollständig in drei Randfällen (F-41A-01, -02, -04) |
| backend/src/findling/main.py | 41-04 | gelesen ganz; Attach vor create_task, erster tick vor dem Server, Abbau-Reihenfolge ok; Rebuild-Frage nach Resume ok |
| backend/src/findling/worker/poller.py | 41-01/03 | Hold, quiesce, reopen, Schwelle über storage_id, `_mark_the_charged` gelesen; Probe Q, U; ok |
| backend/src/findling/worker/reconcile.py | 41-01/03 | Hold, in_flight, ROUND_HELD, Retry-Deckel gelesen; Fenster vor in_flight im Catch-up (F-41A-02) |
| backend/src/findling/worker/embedding.py | 41-03 | Hold im run, parked bleibt gesetzt; ok. fp32-Abruf (unverändert) wird von der Pause nicht gefragt (F-41A-04) |
| backend/src/findling/worker/watch.py | 41-03 | suspend/resume_persist ok; `note_shutdown_begins` (unverändert) schreibt an der Pause vorbei (F-41A-01) |
| backend/src/findling/worker/probe_run.py | 41-04 | Start fragt die Pause vor dem Rebuild; ok. `recover` (unverändert) fragt sie nicht (F-41A-04) |
| backend/src/findling/api/status.py | 41-02/04 | Hintergrundzählung single flight, LRU 4, Kennung (Pfad, dev, ino); `pause`/`pausedSince` geschlossene Menge; Probe T; ok |
| backend/src/findling/api/resources.py | 41-01 | RuntimeError beim Thread-Start gefangen, Flag zurück; ok |
| backend/src/findling/api/probe.py | 41-04 | dritter 409-Zweig `paused`, ohne Id; ok |
| backend/src/findling/probe.py | 41-04 | Konstante START_PAUSED; ok |
| backend/src/findling/nc/client.py | 41-01 | `_OUTAGE_STATUS` = 408, 429, 502, 503, 504; Probe U über 400 bis 599; ok |
| backend/src/findling/nc/queue.py | 41-04 | `paused` nur `is True`, Fehlerpfad None; ok |
| backend/src/findling/store/repo.py | 41-01 | CASE in `_RECORD_SQL`, `gateway_retry_candidates` gebändert, nur Platzhalter; Probe U; ok |
| backend/appinfo/info.xml | 41-08 | Version, Image-Tag, sechs Links `blob/v1.6.2`; ok |
| php/appinfo/info.xml | 41-08 | Version, Links, `<commands>` + PauseCommand, ResumeCommand; ok |
| php/lib/Command/PauseCommand.php (neu) | 41-05 | Exit-Vertrag, strikte Menge, `--wait` geprüft vor dem Speichern; PHPUnit 958 OK; ok |
| php/lib/Command/ResumeCommand.php (neu) | 41-05 | Exit 0 immer, Wunsch gelöscht; ok |
| php/lib/Controller/ProfileController.php | 41-05 | `paused` im selben try hinter rejectForeignCaller; Probe S; ok |
| php/lib/Controller/SettingsController.php | 41-06 | `setPause` ohne Öffner-Attribut (Admin, CSRF), nur bool oder "true"/"false"; Probe S; ok |
| php/lib/Service/SettingsService.php | 41-05 | KEY_PAUSED, getValueBool mit Vorgabe false; ok |
| php/lib/Service/AdminViewService.php | 41-01/06 | pauseState strikt, unsupported, quietInPause, `/rates` in der Pause nicht gefragt; ok |
| php/lib/Service/ScanStatsService.php | 41-02 | usort über (-filesSeen, finished, id), deterministisch; ok (INFO I-41A-03) |
| php/js/admin.js | 41-06 | Sätze über t() und text(), send() mit requesttoken, kein Markup; Probe S; ok |
| php/templates/admin.php | 41-06 | Sätze über `$l->t()` und `p()`, Zustand nur gegen feste Wörter; ok |
| php/l10n/de.js, de.json, de_DE.js, de_DE.json, es.js, es.json, fr.js, fr.json, it.js, it.json, nl.js, nl.json, pt_BR.js, pt_BR.json, pt_PT.js, pt_PT.json | 41-01/06 | je 7 Schlüssel dazu, Schlüsselmenge in allen 8 JSON gleich (md5 der Schlüsselliste fabc2943 achtmal), kein `<` oder `>` im Delta; Ausgabe nur über t()/textContent; ok |
| .github/workflows/deploy-harp.yml | 41-07/08 | Zusicherung 13, Halbentfernung wartet auf den gelesenen Wunsch, Blöcke nach scripts/ci; nur localhost-URLs; ok |
| .github/workflows/python.yml | Dependabot | setup-uv auf v10.3.3, volle SHA gepinnt; ok |
| .github/workflows/security.yml | Dependabot | dasselbe; ok |
| scripts/ci/backup_pause_proof.sh (neu) | 41-07/08 | nur Testinstanz, localhost, set -eo pipefail; ok |
| scripts/ci/store_install_register.sh (neu) | 41-08 | wörtlich verschoben, localhost; ok |

Gegengelesen außerhalb des Diffs: `worker/watch.py` restore und
note_shutdown_begins, `worker/probe_run.py` recover und `_sweep`,
`worker/embedding.py` `_procure`/`aclose`/`close`, `worker/catchup.py` und
`worker/recheck.py` (laufen im Pass des Pollers, also unter `pass_in_flight`),
`store/repo.py` `embedded_in_storages` (mode=ro und query_only),
`main.py` `_run_the_rebuild` (arm am Ende, Hold bleibt), alle Schreibstellen
(`grep -rn "open_store(\|write_meta\|\.record(\|IndexBatchWriter(\|\.commit()"
backend/src`). Die Routen der API schreiben nichts (`POST` nur /probe, /search,
/similar, /snippets).

## Methode

- Proben als Tests in `backend/tests/test_phase41_audit.py` (24 Tests, dreimal
  hintereinander grün), Messungen als Skript
  `scratchpad/a41/v_measure.py` mit wörtlicher Ausgabe unten.
- Andere Wege als die Baupläne: Pause am Plattenzustand gemessen (jede Datei des
  Volumes mit Größe, mtime_ns, sha256), nicht an Flags; Positivkontrolle
  `test_p_the_snapshot_sees_a_single_meta_write`; Kontrolle zu F-41A-01
  (`test_p_without_the_shutdown_write_...`) mit genau dem einen Schreiber
  ausgeschaltet. Retry-Deckel an echten Zeilen statt am Reconcile.
  Statusraster über den echten Streaming-Abruf mit MockTransport für jeden
  Status 400 bis 599. Zugriffsregeln aus den Attributzeilen vor der Methode,
  mit Positivkontrolle auf ProfileController (NoCSRFRequired muss gefunden
  werden).
- PHPUnit am Kopf (php/ in den Server-Checkout synchronisiert, Docker
  nextcloud:32.0.15-apache): `OK (958 tests, 5851 assertions)`.
- Gates mit der Probedatei: ruff check (Vollsatz) "All checks passed!",
  ruff format --check "244 files already formatted", pyright (latest) "0
  errors", vulture 80 Exit 0. Volltestsuite siehe 41-09-SUMMARY.md.

## Security

### S1 Rechte im Suchpfad
Unberührt: `api/search.py`, `api/snippets.py`, `api/similar.py` und die
PHP-Endfilterung sind nicht im Delta. Die Suche in der Pause liest denselben
Index (Probe P: /search 200 in "paused").

### S2 Wer kann pausieren (Probe S)
- `POST /admin/pause`: keine Öffner-Attribute vor der Methode und an der Klasse
  (`test_s_the_pause_route_is_admin_only_and_needs_the_request_token`), also nur
  Admins mit Request-Token; admin.js sendet über `send()` mit `requesttoken`
  (`test_s_the_admin_page_sends_the_switch_with_the_request_token`).
- Den Wunsch liest nur die Backend-ExApp: `/profile` trägt ExAppRequired, und
  `rejectForeignCaller` steht vor dem Lesen von `paused`
  (`test_s_only_the_backend_exapp_reads_the_wish`). Eine ExApp-Route, die den
  Wunsch schreibt, gibt es nicht.
- occ gegen ein Backend ohne Feld `pause`: Exit 1
  (PHPUnit `testPauseAgainstAnOldBackendFails`, im Lauf oben grün); ein
  fremder Wert ist nie "paused" (`testAnOddStatusValueIsNotTakenAsPaused`).

### S3 Logzeilen
`git diff v1.6.1..738a1373 -- backend/src php/lib | grep -E "^\+.*(LOGGER\.|logger->)"`:
18 neue Zeilen, alle nur Zustandswörter, Zahlen oder `type(error).__name__`;
die zwei PHP-Zeilen sind feste Sätze (eine mit Exception-Objekt im Kontext,
wie die übrigen der Klasse). Kein Pfad, kein Name.

### S4 Kein externer Dienst (D-41-17)
`git diff v1.6.1..738a1373 -- <Pfade> | grep -nE "^\+.*https?://"`: 13 Treffer.
6 sind die Doku-Links `github.com/street1983nk/nextcloud-search/blob/v1.6.2/docs/...`
in den Store-Beschreibungen der zwei info.xml (Text für Menschen, kein Abruf),
7 sind `http://localhost:8080/...` in deploy-harp.yml und den zwei CI-Skripten
(Testinstanz). Kein Code-Pfad ruft eine neue Adresse.

### S5 Klartext im Backup
Doku-Satz in drei Sprachen vorhanden und per Gate geprüft (41-07,
test_backup_docs.py); kein Code-Thema.

## Bugs

### B1 Zustandsmaschine des Koordinators
- Resume während pausing: `wish is False and state != running` ruft `_resume`;
  vor dem quiesce ist `reopen` ein No-op, danach öffnet es den Track (Test
  `test_resume_while_pausing_releases_without_a_checkpoint` aus 41-03; der
  Ablauf ist im Code einzig über die eine Task des Koordinators, also ohne
  Wettlauf zwischen settle und resume).
- Doppeltes quiesce: idempotent über `_backup_quiesced`; nach einem Resume
  setzt `reopen` das Flag zurück, die nächste Pause gibt wieder ab.
- Writer-Neuöffnung nach Resume: `_open()` baut den Writer wie nach einem
  Stand-down des Rebuilds, im Thread. Bestätigt beim Bau der Probe Q: nach
  quiesce und Resume baut der erste Pass den Writer über `_open_writer` neu.
- Probe Q (`test_q_enable_disable_probe_end_and_rebuild_end_do_not_lift_the_pause`):
  echter Poller mit einer Queue, die sofort einen Job gäbe, im Zustand paused;
  arm, silence+arm, Probe-Hold und Freigabe, arm (Rebuild-Ende): 0 Claims in
  drei Takten; erst der Wunsch "nicht pausiert" bringt den ersten Claim.
- Lesefehler (`test_q_a_failed_read_changes_nothing_but_a_waiting_start`, 5
  Fälle): nie gelesen bleibt unknown; spät gelesen folgt dem Wunsch; laufend
  plus Lesefehler bleibt running; pausiert plus Lesefehler bleibt paused.
  Urteil gegen D-41-19: richtig, D-41-19 gilt nur bis zur ersten Antwort.

### B2 Checkpoint (Probe R)
- Leser in langer Transaktion, Log mit Frames: zwei Takte bleibt der Zustand
  pausing, das Log hat Bytes; nach dem Ende des Lesers paused und das Log leer
  oder weg (`test_r_a_reader_in_a_long_transaction_keeps_pausing_and_its_end_brings_paused`).
- Rollback-Journal (NFS-Fallback) und fehlende vectors.db: paused, und im
  Verzeichnis liegt danach nur `state.db` (`test_r_a_rollback_journal_and_a_missing_vector_file_still_reach_paused`).

### B3 Schreiber-Inventar am Plattenzustand (Probe P)
- Echte Lifespan mit allen Schreibern, Wunsch paused, nach "paused" drei
  weitere Takte, eine Suche und ein Statusbericht: **keine Datei des Volumes
  geändert**, jedes `-wal` 0 Byte. Die Suche legt `vectors.db-shm` und ein
  leeres `vectors.db-wal` an (Leser im WAL-Modus, keine Daten).
- Neustart in der Pause: die neue Lifespan liest den Wunsch und ist wieder
  paused (D-41-05), ohne dass sich Daten ändern, sobald der eine Schreiber aus
  F-41A-01 ausgeschaltet ist (Kontrolle). Mit ihm schreibt der Stopp zwei
  Meta-Zeilen (F-41A-01).
- Catch-up nach Upgrade: Fenster zwischen Hold-Prüfung und `in_flight`
  (F-41A-02).
- fp32-Sweep und fp32-Abruf: nicht an die Pause angebunden (F-41A-04).
- GuardWatch.restore schreibt direkt, aber nur, wenn eine Pass-Marke eines
  unsauberen Endes liegt; in der Pause läuft kein Pass, die Marke ist leer
  (Neustart-Probe: keine Meta-Änderung beim Start).
- Enable/Disable während der Pause schreibt die Arm-Marke ins Volume
  (Admin-Handlung, I-41A-02); arm hebt die Pause nicht auf (Probe Q).

### B4 Mischbetrieb
- Companion 1.6.1 + Backend 1.6.2: `/profile` ohne `paused` ist False, das
  Backend läuft (Test `test_companion_choice_reads_paused`, Fall fehlendes Feld).
- Companion 1.6.2 + Backend 1.6.1: Seite zeigt "unsupported", occ Exit 1
  (PHPUnit). Der Wunsch bleibt gespeichert und wirkt nach dem Update des
  Backends; das sagt der Satz "Update both apps to the same version."

### B5 Rebuild-Cursor nach Pause (D-41-20)
`_the_rebuild_should_stop` fragt die Pause zwischen zwei Bändern; der Resume
fragt den Rebuild neu (`_resume_after_the_pause`). Belegt durch
`test_a_rebuild_stops_between_bands_on_a_pause_and_resumes` und
`test_the_rebuild_arm_does_not_lift_the_pause` (test_main_lifespan.py), dazu
Probe Q (arm am Rebuild-Ende hebt den Hold nicht).

### B6 Upgrade lässt nichts pausiert
Der Wunsch liegt nur in appconfig; ein Upgrade schreibt ihn nicht. CI-Zusicherung
13 (41-08, Lauf 41803255633): nach dem Upgrade running, pauseWished false, kein
`findling/paused` in oc_appconfig.

### B7 F-40N-Fixes (Probe U)
- Schwelle: sechs Ablehnungen von storage 0 bei 10 geclaimten Zeilen bleiben
  Verdikte, die erste von storage 4 eskaliert
  (`test_u_storage_id_zero_counts_as_one_storage_and_a_second_storage_escalates`).
  Mehrere Slots ändern daran nichts: `_count_refusal` ist synchron und zählt je
  Pass über Mengen.
- Marke im `_abort` bei werfendem `record`: die nicht belasteten Zeilen 2 und 3
  gehen zurück (`test_u_a_mark_that_cannot_be_written_never_keeps_the_rest_from_going_back`).
- Retry-Deckel an echten Zeilen: indexed ist kein Kandidat; fünf Ablehnungen
  derselben Version ergeben `[True, True, True, False, False]`; ein neuer Etag
  ist wieder Kandidat (`test_u_the_retry_cap_is_three_refusals_of_one_version`).
  Höchstens vier Anfragen je Datei und Version bestätigt.
- Raster 400 bis 599 über `_stream_file`: Ausfall genau {408, 429, 502, 503,
  504}, "nicht deins" genau {404}, 194 Verdikte
  (`test_u_the_outage_grid_over_every_status_from_400_to_599`).

### B8 Hintergrundzählung #25 (Probe T)
- Zehn Listen nacheinander, je eine zweite Liste während der laufenden Zählung:
  höchstens ein lebender Zähl-Thread, Cache höchstens 4, jede Liste hat beim
  zweiten Fragen ihre Zahl (`test_t_ten_lists_in_a_row_run_one_count_at_a_time_and_keep_four`).
- Zählung nach Checkpoint: keine Datei geändert (`test_t_the_background_count_writes_nothing`).
- Repräsentant bei wachsendem files_seen: deterministisch nach (-filesSeen,
  finished, id) (PHPUnit `testEqualFilesSeenPrefersFinishedThenTheSmallestId`);
  ein Wechsel während des Crawls ergibt eine neue leaveOut-Liste (I-41A-03).

## Performance (Probe V)

- Koordinator: `test_v_the_coordinator_reads_the_wish_once_per_poll_and_no_more`
  zählt 15 bis 22 Lesungen in 1 s bei 50 ms Takt, im Zustand running wie im
  Zustand unknown; mit PAUSE_POLL_SECONDS = 15 sind das **240 Profil-Lesungen
  je Stunde**, im Leerlauf wie ohne Companion. Der Rückzug des Pollers endet bei
  12 Claims je Stunde (RETREAT_MAX_SECONDS 300); die Lesungen des Koordinators
  haben keine solche Leiter (Teil von F-41A-03).
- Hintergrundzählung und Retry-Abfrage, `scratchpad/a41/v_measure.py`, Ausgabe
  wörtlich (Entwicklungsrechner x86, 250 000 Zeilen in files, 125 000 Chunks):

  ```
  left out count 4 of 10 storages, ~100k docs: figure 45001, median 68 ms, max 75 ms
  left out count all 10 storages, 250k docs: figure 120001, median 93 ms, max 102 ms
  gateway_retry_candidates, page of 1000 ids over 250000 rows: 20 candidates, median 0.34 ms, max 0.79 ms
  ```

  Die Zählung läuft im Hintergrund-Thread, höchstens einmal je 5 Minuten und
  Liste; auch mit Faktor 5 auf ARM unter einer Sekunde. Die zusätzliche Abfrage
  je Reconcile-Seite kostet unter 1 ms. Kein Befund.

## Bekannte Grenzen aus 41-01 bis 41-08

| Grenze | Quelle | Urteil |
|---|---|---|
| Zwei kaputte Storages in Folge belasten die Grenzzeilen: 28 Claims, 3 Eskalationen | 41-01 | bestätigt (gepinnter Test aus 41-01 grün; Probe U zur Storage-0-Regel) |
| Instanz mit einer Storage: jede Datei endet failed(gateway_error) mit höchstens vier Anfragen je Version | 41-01, E-40-07-02 | bestätigt, Probe U: drei Retries plus die erste Anfrage |
| Über 100 000 fehlt die Zahl bis zur ersten Hintergrundzählung, die Seite rechnet dann wie 1.5 | 41-02 | bestätigt, Probe T: erstes Fragen None, zweites mit Zahl |
| pausing kann bei OCR bis etwa 30 min dauern | 41-03, D-41-18 | bestätigt als Entwurf (kein Abbruch, Probe R zeigt pausing bis die Bedingung fällt); nicht gemessen |
| Status-Wert prozesslokal, nach Start unknown bis zur ersten Lesung | 41-04, 41-08 | bestätigt, Probe Q "never_read" |
| Unlesbare Profil-Route hält die Indexierung an (T-41-18 accept) | 41-04 | bestätigt; ohne Companion still und ohne D-17-Zeile, siehe F-41A-03 |
| Nach Neustart in der Pause wieder paused (CI: 7 s nach der ersten Antwort) | 41-07/08 | bestätigt lokal, Probe P Neustart; Daten unverändert bis auf F-41A-01 |
| Upgrade-Strecke prüft pause running | 41-08 | bestätigt (Lauf 41803255633) |

## Befunde

### F-41A-01 (LOW): Stopp eines pausierten Containers schreibt state.db

- **Datei:** `backend/src/findling/worker/watch.py:272-286` (`note_shutdown_begins`),
  aufgerufen im Abbau der Lifespan; vorbei an `suspend_persist`.
- **Szenario:** Weg B, die Kopie läuft, der Container wird gestoppt oder neu
  gestartet (Neustart des Hosts, Auto-Update). Der Stopp schreibt
  `multi_slot_pass` und `multi_slot_chosen` als "" (gemessen 16 512 Byte Log,
  oder beim Schließen der letzten Verbindung schon in state.db zurückgeschrieben);
  der nächste Start checkpointet das in state.db, bevor er wieder "paused" sagt.
- **Probe:** `test_p_f_41a_01_a_stop_in_the_pause_writes_two_meta_rows_into_the_log`;
  Kontrolle ohne diesen einen Schreiber: Stopp und Neustart ändern keine Daten.
- **Folge:** Die Werte sind logisch gleich (leer), eine Kopie über den Stopp
  hinweg kann state.db und Log aus zwei Momenten mischen; das Volume ist laut
  Doku vollständig neu aufbaubar. Kein Datenverlust an der Quelle.
- **Fix-Vorschlag:** in `note_shutdown_begins` nicht schreiben, solange
  `_persist_suspended` gilt (in der Pause läuft kein Pass, die Marke ist leer),
  oder nur schreiben, wenn eine Marke gesetzt ist.

### F-41A-02 (LOW): Catch-up kann nach "paused" eine Runde beginnen

- **Datei:** `backend/src/findling/worker/reconcile.py:415-460` (`run`, `once=True`).
- **Szenario:** Nur im einmaligen Catch-up-Zyklus nach dem Upgrade auf 1.5+ bei
  ausgeschaltetem Reconcile. Zwischen der Hold-Prüfung und `in_flight = True`
  liegt `await self._catchup_mark()` (Thread-Sprung). Fällt der Pausen-Eintritt
  in diese Lücke, sieht der Koordinator keine Runde, sagt "paused", und die
  Runde schreibt danach `rewind_reconcile_walk` in state.db; die erste Scheibe
  endet dann mit ROUND_HELD.
- **Probe:** `test_p_f_41a_02_the_catch_up_can_write_after_paused_when_the_hold_lands_in_its_mark_read`
  (Lücke künstlich verlängert, damit sie jedes Mal getroffen wird).
- **Folge:** ein Schreibvorgang in einem Fenster von Millisekunden, einmal je
  Instanz und Upgrade.
- **Fix-Vorschlag:** `in_flight` vor dem Lesen der Marke setzen oder den Hold
  nach dem Lesen erneut prüfen.

### F-41A-03 (LOW): Ohne Companion bleibt das Backend still auf "unknown" (offene Frage aus 41-08)

- **Datei:** `backend/src/findling/worker/pause.py` (`run`, `_read`),
  `backend/src/findling/nc/queue.py` (Fehlerpfad nur DEBUG).
- **Szenario:** Ein Container startet ohne Companion (nur die ExApp
  installiert, oder die Companion entfernt und der Container neu gestartet).
  Nach D-41-19 hält er alle Schreiber, der Poller fragt die Queue nie, also
  kommt die Rückzugszeile von D-17 ("the Nextcloud half looks removed") nie.
  Im Log steht auf INFO-Ebene nichts, was den Zustand erklärt. Zugleich liest
  der Koordinator alle 15 s (240 je Stunde, Probe V), auch nach einer
  Halbentfernung im laufenden Betrieb, wo der Poller sich auf 12 je Stunde
  zurückzieht.
- **Folge:** Keine Daten in Gefahr: ohne Companion gibt es ohnehin keine Queue
  und keine Admin-Seite. Schlechter diagnostizierbar als 1.6.1, und die Last
  der Lesungen hat keine Rückzugsleiter (4 kleine Anfragen je Minute).
- **Einordnung:** LOW, keine Zusage verletzt; D-41-19 ist Owner-Entscheid und
  wirkt hier wie entschieden. **Owner-Punkt für 41-10.**
- **Optionen:** (a) annehmen und in docs/backup*.md bzw. Fehlersuche einen
  Satz ergänzen; (b) v1.7: eine einmalige WARNING-Zeile nach drei
  unlesbaren Lesungen im Zustand unknown (ohne Katalogsatz) und eine
  Rückzugsleiter für die Lesungen wie beim Poller.

### F-41A-04 (LOW): fp32-Sweep und fp32-Abruf schreiben in der Pause

- **Datei:** `backend/src/findling/worker/probe_run.py:795-865` (`recover`,
  `_sweep`), `backend/src/findling/worker/embedding.py:1254-1284` (`_procure`);
  `pause.py` `_writers_rest` kennt beide nicht.
- **Szenario:** Ein Vorab-Check hat die fp32-Gewichte geholt, die Marke
  `probe_fp32_fetched=1` ist offen, und die Companion sagt int8. Antwortet die
  Companion erst nach "paused", löscht der Sweep die Gewichte (bis 470 MB) aus
  `models/` und schreibt die Marke in state.db. Ebenso läuft ein fp32-Abruf,
  der vor der Pause begann, in der Pause weiter und schreibt `.part` in
  `models/`.
- **Probe:** `test_p_f_41a_04_the_sweep_of_a_pre_check_writes_and_deletes_in_the_pause`
  (Antwort der Companion bewusst erst nach "paused").
- **Folge:** Kopie kann eine halbe oder fehlende Gewichtsdatei enthalten; die
  Gewichte werden bei Bedarf neu geholt, der Index ist nicht betroffen.
- **Fix-Vorschlag:** Sweep wartet auf `not wants_pause()`; `_writers_rest`
  wartet auf einen laufenden Abruf oder der Abruf startet in der Pause nicht.

### I-41A-01 (INFO): Leser legen in der Pause `-shm` und ein leeres `-wal` an
Probe P: die Suche öffnet vectors.db lesend und legt `vectors.db-shm` (32 768
Byte) und `vectors.db-wal` (0 Byte) an. Keine Daten; beim Kopieren harmlos.
Kein Handlungsbedarf.

### I-41A-02 (INFO): Enable/Disable während der Pause schreibt die Arm-Marke
Admin-Handlung auf der Apps-Seite während einer Kopie; die Pause bleibt (Probe
Q). Kein Handlungsbedarf.

### I-41A-03 (INFO): Repräsentantenwechsel während des Crawls
Wächst files_seen zweier Mitglieder einer Share-Gruppe abwechselnd, wechselt
der Repräsentant und damit die leaveOut-Liste; über 100 000 Dokumenten fehlt
`embeddedLeftOut` dann für einen Poll, bis die Hintergrundzählung die neue Liste
hat (Cache hält 4 Listen, Probe T). Vorübergehend, nur während des Crawls.

### I-41A-04 (INFO): Lesungen des Wunsches im laufenden Betrieb
240 kleine Profil-Lesungen je Stunde zusätzlich (A3 aus 41-RESEARCH.md,
bewusst). Mit F-41A-03 entschieden.

## Threat-Register T-41-01 bis T-41-34

| ID | Urteil |
|---|---|
| T-41-01 | umgesetzt; Probe U (Storage 0 eskaliert allein nie), Test 200 Dateien aus 41-01 grün |
| T-41-02 | umgesetzt; Probe U, höchstens vier Anfragen je Datei und Version |
| T-41-03 | umgesetzt; gateway_error bei gleichem Etag ist Arbeit (`_compare`), kein skipped(gone) |
| T-41-04 | accept bestätigt; Endverlust durch Marke und Retry behoben (Probe U) |
| T-41-05 | umgesetzt; S3, keine Logzeile mit Pfad |
| T-41-06 | umgesetzt; RuntimeError gefangen (resources.py), Test aus 41-01 |
| T-41-07 | umgesetzt; Satz über t()/textContent, 16 Kataloge gleich |
| T-41-08 | umgesetzt; Probe T, ein Thread, Cache 4 |
| T-41-09 | umgesetzt; Flag zurück bei RuntimeError (status.py) |
| T-41-10 | umgesetzt; zwei Zahlen, keine Zeile |
| T-41-11 | umgesetzt; Kennung (Pfad, dev, ino) vor dem Schreiben |
| T-41-12 | umgesetzt; Probe R und P; Lücken nur in den Randfällen F-41A-01, -02, -04 |
| T-41-13 | umgesetzt; Probe Q |
| T-41-14 | umgesetzt; kein Abbruch, quiesce mit unlock_held |
| T-41-15 | umgesetzt; S3 |
| T-41-16 | umgesetzt; Probe S, kein Schreibweg über eine ExApp-Route |
| T-41-17 | umgesetzt; `is True`, Test aus 41-04 |
| T-41-18 | accept bestätigt; Nebenwirkung F-41A-03 als Owner-Punkt |
| T-41-19 | umgesetzt; 409 paused, probe_busy hält pausing; Sweep danach siehe F-41A-04 |
| T-41-20 | umgesetzt; Probe S |
| T-41-21 | umgesetzt; PHPUnit `testAnOddStatusValueIsNotTakenAsPaused` grün |
| T-41-22 | umgesetzt; PHPUnit `testPauseAgainstAnOldBackendFails` grün |
| T-41-23 | accept bestätigt; occ druckt nur Zustandswörter |
| T-41-24 | umgesetzt; Probe S (Attribute) |
| T-41-25 | umgesetzt; Probe S (requesttoken) |
| T-41-26 | umgesetzt; nur bool oder "true"/"false", sonst 400 |
| T-41-27 | umgesetzt; geschlossene Menge, Sätze aus dem Katalog |
| T-41-28 | umgesetzt; Pause-Satz und Schalter-Text sichtbar |
| T-41-29 | umgesetzt; Doku-Satz, Gate test_backup_docs.py |
| T-41-30 | umgesetzt; occ --wait nur bei paused Exit 0; CI WAL 0 Byte |
| T-41-31 | umgesetzt; A1 im CI belegt (41-08) |
| T-41-32 | umgesetzt; STOPP-Prüfung leer (41-08), kein Schema im Delta |
| T-41-33 | umgesetzt; Zusicherung 13 |
| T-41-34 | umgesetzt; beide Apps 1.6.2 |

Plan 41-09 selbst: T-41-35 (audited_head im Frontmatter, Code-Diff bis HEAD
leer), T-41-36 (kein Fix, also kein Fix-Delta), T-41-37 (Proben P bis V mit
Zahlen) umgesetzt.

## Befundtabelle

| ID | Schwere | Datei | Entscheid |
|---|---|---|---|
| F-41A-01 | LOW | worker/watch.py note_shutdown_begins | Owner-Punkt 41-10 (Fix jetzt oder v1.7), Empfehlung v1.7 |
| F-41A-02 | LOW | worker/reconcile.py run(once=True) | v1.7 (deferred-items.md) |
| F-41A-03 | LOW | worker/pause.py, nc/queue.py | Owner-Punkt 41-10 (annehmen oder v1.7) |
| F-41A-04 | LOW | worker/probe_run.py recover, worker/embedding.py _procure | Owner-Punkt 41-10 (Fix jetzt oder v1.7), Empfehlung v1.7 |
| I-41A-01 | INFO | Leser im WAL-Modus | kein Handlungsbedarf |
| I-41A-02 | INFO | main.py enabled_handler | kein Handlungsbedarf |
| I-41A-03 | INFO | ScanStatsService.php / status.py | kein Handlungsbedarf |
| I-41A-04 | INFO | worker/pause.py | mit F-41A-03 |

## Urteil

0 CRIT, 0 HIGH, 0 MEDIUM über den ganzen Delta `v1.6.1..738a1373`. Kein Fix in
diesem Plan, kein Fix-Delta, `audited_head` = Code-Kopf. Jeder LOW ist
entschieden: keiner verletzt eine Zusage im laufenden Betrieb; F-41A-01 und
F-41A-04 betreffen eine Kopie, die über einen Neustart oder einen vorher
begonnenen fp32-Vorgang reicht, F-41A-02 ein Fenster von Millisekunden einmal je
Upgrade. Ein Fix vor dem Tag hieße neuer Code-Kopf, neues Nachaudit und neuer
CI-Lauf; das ist eine Owner-Abwägung, keine Pflicht aus diesem Audit.

## Für die Owner-Runde 41-10

1. **F-41A-03** (offene Frage aus 41-08): Container ohne Companion bleibt still
   auf "unknown" und schreibt die D-17-Zeile nie; Lesungen 240 je Stunde ohne
   Rückzugsleiter. Vorschlag: annehmen für 1.6.2, v1.7 mit einmaliger
   WARNING-Zeile und Leiter. Alternativ ein Satz in docs/backup*.md.
2. **F-41A-01**: Stopp oder Neustart während einer Kopie nach Weg B schreibt
   zwei leere Meta-Zeilen in state.db. Vorschlag: v1.7 (Fix drei Zeilen in
   watch.py). Alternativ in 1.6.2 mit neuem Kopf und Nachaudit; oder ein
   Doku-Satz "während der Kopie den Container nicht neu starten" (nutzersichtbar,
   dreisprachig).
3. **F-41A-04**: fp32-Sweep und fp32-Abruf schreiben in `models/` (und eine
   Meta-Zeile) auch in der Pause. Vorschlag: v1.7; Gewichte sind neu holbar.

## Nachaudit: Fix-Delta 738a1373..efdca684 (04.11.2026)

**Anlass:** Owner-Entscheid 04.11.2026: alle vier LOW (F-41A-01 bis -04) vor
dem Release beheben statt v1.7. Damit gilt der Abschnitt "Für die Owner-Runde
41-10" oben als erledigt; die Befundtabelle bleibt als Stand von 738a1373
stehen, der Entscheid je LOW steht hier.

**Code-Kopf mechanisch** (`git log -1 --format=%H -- backend/src backend/docker
backend/appinfo php/appinfo php/lib php/js php/templates php/l10n
.github/workflows scripts`): `efdca6840ee89b3373d9706b0e3c94039c4ef8d4`, neuer
`audited_head`. 41-11 taggt diesen Kopf oder einen Kopf, dessen Code-Diff zu
`efdca684` leer ist.

**Commits** (Autor street1983nk, ohne Trailer, je Befund ein Commit, Probe zuerst
umgedreht und rot gesehen, dann Fix):

| Commit | Befund |
|---|---|
| b0c10754 | fix(41): the stop of a paused container writes no shutdown mark (F-41A-01) |
| c8fa6d98 | fix(41): the catch-up raises in_flight with its hold check (F-41A-02) |
| 6b9d0995 | fix(41): the reads of the pause wish back off and say so once (F-41A-03) |
| efdca684 | fix(41): the fp32 sweep and the fp32 fetch respect the backup pause (F-41A-04) |

`git diff --stat 738a1373..efdca684` über die Code-Pfade: 5 Dateien in
backend/src (main.py 13, worker/pause.py 72, worker/probe_run.py 57,
worker/reconcile.py 35, worker/watch.py 11 Zeilen), dazu backend/tests
(test_phase41_audit.py, test_measurement_scripts.py). Kein PHP, kein l10n, kein
Workflow, kein Skript, kein nutzersichtbarer Text; PHPUnit deshalb nicht neu
gefahren (Stand 958 OK am alten Kopf, php/ unverändert).

### Urteil je Datei

| Datei | Befund | Urteil |
|---|---|---|
| worker/watch.py | F-41A-01 | `note_shutdown_begins` liest bei `_persist_suspended` erst die zwei Pass-Marken und schreibt nur, wenn eine gesetzt ist. In "paused" läuft kein Pass, beide sind leer, also kein Schreiben. Ein Pass, der während "pausing" noch läuft, behält seine Marke und wird wie bisher geräumt (sonst läse der nächste Start ein unsauberes Ende, Pitfall 9). Das Lesen öffnet nur die vorhandene Verbindung bzw. legt `-shm` und ein leeres `-wal` an (I-41A-01). ok |
| worker/reconcile.py | F-41A-02 | `in_flight` geht im selben Schritt wie die Hold-Prüfung hoch, ohne `await` dazwischen, und fällt nur im `finally`. Nach dem Lesen der Catch-up-Marke wird der Hold erneut gefragt; gehalten, startet keine Runde. Der Zweig "Marke noch nicht CATCHUP_RECONCILE" senkt `in_flight` vor dem langen Warten. Ausnahmen von `run_once` wie bisher gefangen; `_catchup_mark` fängt selbst. Im asyncio-Modell wettlauffrei: der Koordinator sieht entweder die Runde oder die Runde den Hold. ok |
| worker/pause.py | F-41A-03, F-41A-04 | Leiter: jede unlesbare Lesung in Folge verdoppelt das Warten ab dem Poll bis `PAUSE_RETREAT_MAX_SECONDS` = 300 (= `RETREAT_MAX_SECONDS` des Pollers, per Test gleich gehalten), Exponent gedeckelt. Eine WARNING nach `PAUSE_UNREADABLE_WARN_AFTER` = 3 (= `RETREAT_AFTER_ROUNDS`), mit Zustandswort und Deckel, ASCII, kein Pfad; die Zeile je Ausnahme des Lesens nur bis zu dieser Ansage, danach DEBUG. Erste Antwort setzt die Leiter zurück, eine INFO-Zeile nur, wenn die WARNING kam (wie `_recovered` des Pollers). Der Zustand ändert sich durch eine unlesbare Lesung nicht: unknown hält alle Schreiber (D-41-19), sonst gilt die letzte Antwort (D-17-Muster: still zurückziehen, nicht anhalten). Neu `fetch_busy` in `_writers_rest`: ein laufender fp32-Abruf hält "pausing", ohne Abbruch (wie D-41-18). ok |
| worker/probe_run.py | F-41A-04 | `recover` fragt die Pause vor jedem Versuch (dann auch kein Lesen der Companion) und in `_sweep_step` erneut nach dem Lesen, im selben Schritt, in dem `sweeping` hochgeht. Reihenfolge der Entscheidungen (fp32, Übernahme offen, int8) unverändert; Übernahme-Warten über `_sweep_waits_for_takeover` wie zuvor `max(retry, takeover_poll)`. ok |
| main.py | F-41A-04 | `_the_probe_is_busy` zählt einen laufenden Sweep, `_an_fp32_fetch_runs` liest `precision.snapshot().procuring` und geht als `fetch_busy` in den Koordinator. Nur Lesen von Flags, kein I/O. ok |

S3 (Logzeilen) über den Fix-Delta: `git diff 738a1373..efdca684 -- backend/src |
grep -E "^\+.*(LOGGER\.|https?://)"`: drei neue Zeilen in pause.py (WARNING der
Leiter, INFO der Rückkehr, Umschalter warning/debug), eine verschobene in
reconcile.py; nur Zustandswörter, Zahlen und Klassennamen. Keine URL.

### Proben (backend/tests/test_phase41_audit.py, jetzt 26 Tests)

Methode wie oben: Plattenzustand Datei für Datei (Größe, mtime_ns, sha256), jede
Probe mit Positivkontrolle auf demselben Pfad. Alle vier umgedrehten Proben vor
dem Fix rot gesehen.

- **F-41A-01:** `test_p_f_41a_01_a_stop_in_the_pause_writes_nothing` (echte
  Lifespan, Wunsch paused, Stopp: `_data_moved == {}`; vor dem Fix
  `{'state.db': 'changed'}`).
  `test_p_f_41a_01_the_shutdown_mark_writes_only_outside_the_pause_or_for_a_set_mark`,
  vier Fälle: ohne Pause schreibt derselbe Pfad (Positivkontrolle, sha256 von
  state.db ändert sich); Pause ohne Marke schreibt nichts (vor dem Fix rot);
  Pause mit gesetzter Marke räumt sie; einzelne Wahl ohne Pass-Marke wird
  geräumt. `test_p_a_stop_and_a_restart_in_the_pause_move_no_data` läuft jetzt
  über den echten Abbau ohne Platzhalter (vor dem Fix rot).
- **F-41A-02:**
  `test_p_f_41a_02_a_hold_that_lands_in_the_mark_read_of_the_catch_up_keeps_pausing_and_nothing_writes`
  erzwingt die Verschränkung (das Lesen der Marke wartet auf ein Event, der
  Pausen-Eintritt fällt hinein): `in_flight` True, Zustand "pausing" (vor dem Fix
  rot: `in_flight` False, Zustand paused), nach dem Lesen kein
  `rewind_reconcile_walk`, dann "paused" und 0,2 s später kein Byte bewegt.
  Kontrolle `..._control_without_the_hold_the_same_catch_up_rewinds`: ohne Hold
  spult dieselbe Runde zurück.
- **F-41A-03:** `test_v_f_41a_03_the_ladder_retreats_to_twelve_reads_an_hour_and_an_answer_resets_it`
  (keine Antwort und werfendes Lesen): Wartezeiten 15, 30, 60, 120, 240, 300,
  300, 300 s, also 12 Lesungen je Stunde statt 240; Zustand bleibt unknown,
  `wants_pause()` True; die erste Antwort setzt auf 15 s und den Zustand auf
  running. `test_v_f_41a_03_one_warning_after_three_unreadable_reads_and_one_info_on_the_way_back`:
  zwei Fehlversuche ohne Zeile, beim dritten genau eine WARNING (enthält
  "unknown" und "300"), zehn weitere ohne Zeile, eine INFO bei der Rückkehr, neue
  Serie warnt wieder einmal; die letzte Antwort (paused) bleibt in Kraft.
  `test_v_the_coordinator_reads_at_the_pace_of_the_poll_and_backs_off_without_an_answer`:
  Laufschleife mit 50 ms Poll, mit Antwort 15 bis 22 Lesungen je Sekunde, ohne
  Antwort 3 bis 6 (vor dem Fix 16).
- **F-41A-04:** `test_p_f_41a_04_the_sweep_of_a_pre_check_waits_for_the_end_of_the_pause`
  (echte Lifespan, Start in der Pause mit `probe_fp32_fetched=1` und fp32-Datei):
  in "paused" 1 s und ein weiterer Takt ohne geänderte Datei, Gewichte da, Marke
  "1", Companion nicht gefragt (vor dem Fix rot: Datei gelöscht). Positivkontrolle
  im selben Test: Wunsch "nicht pausiert", derselbe Sweep fragt, löscht und leert
  die Marke. `test_p_f_41a_04_a_pause_that_arrives_during_the_read_of_the_companion_holds_the_sweep`
  erzwingt die Pause innerhalb des Lesens: nichts gelöscht, sha256 gleich, kein
  zweites Lesen, `sweeping` nie True; nach der Freigabe sweept derselbe ProbeRun.
  Gegenprobe: mit entfernter Nachfrage nach dem Lesen wird diese Probe rot (1
  failed), mit ihr grün. `test_p_f_41a_04_a_running_fp32_fetch_keeps_the_pause_on_pausing_until_it_ended`
  am Koordinator aus `main._build_the_pause`: laufender Abruf, drei Takte
  "pausing" (vor dem Fix rot: sofort paused), nach dem Ende "paused"; Kontrolle
  ohne Abruf sofort paused.

### Gates am Fix-Kopf (lokal, vor jedem der vier Commits)

- ruff check (Vollsatz) "All checks passed!" für backend und scripts, ruff format
  --check "244 files already formatted" bzw. "21 files", pyright (latest)
  "0 errors, 0 warnings, 0 informations", vulture 80 Exit 0.
- Volltestsuite in zwei Hälften mit den sechs --ignore, am Kopf efdca684:
  `tests/test_[a-m]*.py` 3185 passed, 41 skipped; `tests/test_[n-z]*.py` 3415
  passed, 262 skipped; 0 failed.
- test_phase41_audit.py dreimal hintereinander: 35 passed, 35 passed, 35 passed.
- Baumhash-Ratsche des Pakets je Commit nachgezogen und unabhängig mit find,
  sort, sed, sha256sum nachgerechnet: 75e34151, 3d8f694b, a8864566, 98687977;
  81 Dateien, PHP-Paar unverändert.

### Verbleibendes, bewusst

- Ein fp32-Abruf, der vor der Pause begann, verlängert "pausing" bis zu seinem
  Ende (bis 470 MB); kein Abbruch, dasselbe Prinzip wie der OCR-Batch (D-41-18).
  Die Doku sagt schon: Backup erst bei "paused".
- Nach einem Resume holt der Sweep spätestens nach `RECOVER_RETRY_SECONDS` (5 s)
  nach.
- Eine wieder installierte Companion wird nach einer langen Serie spätestens nach
  300 s gelesen, wie beim Rückzug des Pollers.

### Urteil Nachaudit

0 CRIT / 0 HIGH / 0 MEDIUM / 0 LOW offen über `v1.6.1..efdca684`. Die vier LOW
sind behoben und mit umgedrehten Proben samt Positivkontrolle belegt; der Fix
bringt keinen neuen Befund. `audited_head` = `efdca6840ee89b3373d9706b0e3c94039c4ef8d4`.
CI-Beleg des Kopfes siehe unten.

### CI-Beleg des Fix-Kopfes

Push 605b7dbe..e27b17de (e27b17de = efdca684 plus nur `.planning/`), alle Läufe
auf e27b17de success: Python gates 41821538047, Integration 41821538106,
Resilience 41821538078, HaRP deploy 41821537851, Multi-arch image 41821538102,
Security scans 41821538411, OpenSSF Scorecard 41821538083. PHP and store
metadata gates läuft wegen des Pfadfilters nicht (php/, backend/appinfo und die
Filterpfade seit f12649a2 unverändert, `git diff --stat f12649a2 HEAD` darüber
leer); Beleg Lauf 41792859857 success auf f12649a2, "OK (958 tests, 5851
assertions)".

## Nachaudit #44: Fix-Delta efdca684..5dc1aa12

Owner-Entscheid 04.11.2026: Issue #44 (einzelne UTF-16-Surrogate im extrahierten
Text, `UnicodeEncodeError` in `add_text`, Stillstand des ganzen Passes) kommt in
1.6.2. Zwei Code-Commits: aef9966f (Teil 1, Reparatur in `normalize`) und
5dc1aa12 (Teil 2, Eindämmung je Datei). Gelesen: `git diff efdca684..5dc1aa12`,
7 Dateien, 515 Zeilen dazu, 44 weg.

### Ursache, selbst nachgestellt

- striprtf 0.0.35 liefert für `\u-10179?\u-8704?` die zwei Hälften als zwei
  Codepunkte: `'Hallo 😀 Welt'`. `normalize` (NFC) ließ sie stehen,
  tantivy 0.26.2 `Document.add_text` warf `UnicodeEncodeError: surrogates not
  allowed` (writer.py Zeile 315 am Kopf efdca684, wie im Issue).
- `add` reihte `delete_documents_by_query` VOR den Feldern ein. Gemessen mit dem
  Writer von efdca684: alte Version von 42 committet, vergifteter Satz für 42
  wirft, Nachbar 43 geschrieben, Commit: danach 1 Dokument, die alte Version von
  42 ist still weg. Mit 5dc1aa12: 2 Dokumente, alte Version da.
- Der Fehler lief aus `_work` und `run_once` in den Catch-all von `run()`, der
  `unlock_held()` rief; die Probe unten zeigt vor dem Fix `unlocked == [[91, 92,
  93]]` und keine Quittung, also derselbe Kopf-Batch beim nächsten Claim.

### Urteil je Datei

| Datei | Teil | Urteil |
|-------|------|--------|
| index/analyzer.py | 1 | `normalize` ruft zuerst `_without_surrogates`: ASCII-Text (gespeichertes Flag) geht durch, sonst eine strikte UTF-8-Probe, und nur wenn sie wirft der Round-Trip `utf-16-le` mit `surrogatepass` hin und `replace` zurück. Paare werden zu einem Zeichen, einzelne Hälften zu U+FFFD; kein BOM wird erzeugt oder geschluckt (Little Endian auf beiden Seiten, Kontrolltest mit führendem U+FEFF). Gemessen bei MAX_TEXT_CHARS (524.288 Zeichen deutsch, best of 7): 0,75 ms vorher, 1,04 ms mit Probe, 2,15 ms mit Reparatur; Regex über den Surrogatbereich wäre allein 1,2 ms. Die Zahlen stehen im Docstring. Weiterhin genau zwei Aufrufer (writer.py, rewrite.py), der Zähltest ist unverändert grün. ANALYZER_VERSION bleibt: ein Text mit Surrogaten kam nie in den Index (er warf), also ändert sich kein vorhandener Term. ok |
| index/writer.py | 1, 2 | `add` baut das Dokument in `_document_of` vollständig, BEVOR die Löschung eingereiht wird; jede Ausnahme beim Bau wird `UnwritableRecord(cause=Klassenname)` mit `from None`, also ohne Nachricht und ohne Kette (die Nachricht eines Encode-Fehlers zitiert den Text). Löschung und `add_document` bleiben außerhalb: ein Fehler des Writers selbst ist kein Befund über eine Datei und beendet den Pass wie bisher. `_pending` und `_pending_bytes` zählen erst nach dem Einreihen. Pfad und Endung bleiben unnormalisiert, Begründung mit Messung im Docstring (siehe unten). ok |
| worker/poller.py | 2 | Neuer `_write_or_fail` an allen drei Schreibstellen (Inhalt, OCR-Spur über den Pool, Umbenennung). Gefangen wird nur `UnwritableRecord`; daraus wird `failed(corrupt)`, die Nachbarn laufen weiter und bekommen in `_record_verdicts` ihr Urteil. Der Schreibaufruf selbst steht unverändert in `to_thread` bzw. `self._pool.call` (T-26-19); der Quelltext-Ratchet `test_the_blocking_work_runs_off_the_event_loop` hielt das fest und blieb unverändert, das Produkt wurde ihm angepasst. Beim Umbenennen wird ein abgelehnter Satz als failed gesammelt, ohne Embedding-Spur und ohne übernommenes OCR-Flag; die alte Version bleibt unter dem alten Namen. Logzeile: WARNING mit Datei-ID und Klassenname, kein Name, kein Pfad, kein Text. ok |
| tests/test_analyzer.py | 1 | 8 neue Tests; Surrogate über `chr()` gebaut, weil ein Editor `😀` im Quelltext zu einem Emoji zusammenzieht (beim Schreiben dieses Fixes passiert). ok |
| tests/test_index_writer.py | 2 | 3 neue Tests (Fehlerart ohne Inhalt, alte Version bleibt, Positivkontrolle Ersetzen). ok |
| tests/test_poller.py | 2 | 6 neue Tests, siehe Proben. ok |
| tests/test_measurement_scripts.py | 1, 2 | Baumhash-Ratsche je Commit mit Begründung nachgezogen, unabhängig mit find, sort, sed, sha256sum gerechnet: 26537789 (aef9966f), f6716e41 (5dc1aa12); 81 Dateien, PHP-Paar unverändert. EXPECTED_TRAVEL_PATH_WRITES unberührt und grün. ok |

### Wahl des Reason-Codes: corrupt

Bestehender Code, kein neuer Text. `encoding_unknown` sagt dem Admin "Zeichensatz
nicht erkannt, als UTF-8 speichern"; das ist für eine Datei, deren Text sauber
gelesen wurde und deren Ablehnung jeder Wert des Satzes sein kann, der falsche
Rat. `corrupt` ("Datei beschädigt, außerhalb von Nextcloud prüfen und neu
hochladen") ist zugleich das, was die App schon für jede unvorhergesehene
Ausnahme sagt (`ExtractionOutcome.from_exception`). Nach Teil 1 erreicht ein
Emoji-RTF diesen Pfad nicht mehr; er ist die Absicherung für alles, was künftig
an einem Wert scheitert.

### Pfad und Endung: Beleg statt Annahme

Beide kommen aus dem OCS-JSON der Queue, das Nextcloud mit `json_encode($array,
JSON_HEX_TAG)` schreibt (BaseResponse.php:101, Image nextcloud:35.0.2-apache).
Gemessen mit php:8.2-cli: ein Zeichen außerhalb der BMP geht als Escape-Paar
`😀` hinaus, das `json.loads` zu einem Codepunkt zusammenfügt (in
Python nachgeprüft); ein Name mit UTF-8-kodiertem Surrogat (`\xED\xA0\xBD`) ist
"Malformed UTF-8" und lässt `json_encode` ganz scheitern, statt eine Hälfte
auszugeben. Eine einzelne Hälfte entsteht in Python nur aus einem einzelnen
Escape, und das schreibt PHP nicht. Käme doch eine an, fängt Teil 2 sie für diese
eine Datei ab (in den Writer-Tests genau so geprobt). Pfad und Titel gehen
zusätzlich in die State-DB; das ist der Grund, warum die Poller-Proben den Body
vergiften und nicht den Pfad.

### Proben

Methode: Fault-Injection statt Ersatzteil. Der Body läuft durch das echte
striprtf und die echte tantivy-Bindung; die Fixture `normalize_of_1_6_1` setzt
nur `findling.index.writer.normalize` auf das NFC ohne Reparatur von 1.6.1
zurück, damit Teil 2 allein und am exakten Wert von #44 geprüft wird. Vor dem
Fix gegen poller.py und writer.py von aef9966f laufen lassen: 4 rot, 2
Kontrollen grün; danach 6 grün.

- `test_one_file_the_index_cannot_take_fails_alone_and_the_pass_goes_on`: Batch
  91, 92 (Emoji-RTF), 93. Vorher `UnicodeEncodeError` aus `run_once`. Nachher
  `(indexed, failed) == (2, 1)`, Quittung `([91, 93], {92: "corrupt"})`, kein
  Unlock, State 4711 und 4713 indexed, 4712 failed/corrupt, Index nur 4711 und
  4713; genau eine WARNING mit "UnicodeEncodeError" und "4712", ohne Name, Pfad
  oder Text, kein "unexpected".
- `test_one_file_the_index_cannot_take_no_longer_stalls_the_loop`: derselbe
  Batch durch `run()`. Vorher `unlocked == [[91, 92, 93]]`, keine Quittung (der
  Stillstand aus dem Issue). Nachher kein Unlock, Quittung wie oben.
- `test_a_scan_the_index_cannot_take_fails_alone` (OCR-Spur über den Pool) und
  `test_a_rename_the_index_cannot_take_fails_alone_and_keeps_the_old_name`
  (Bau beim neuen Namen abgelehnt): vorher rot, nachher failed(corrupt), die
  Datei bleibt unter "kuendigung" auffindbar, nicht unter dem neuen Namen.
- Positivkontrolle 1 `test_the_same_batch_without_the_emoji_indexes_all_three`:
  gleiche Injektion, RTF ohne Emoji, alle drei indexed. Positivkontrolle 2
  `test_the_batch_of_issue_44_indexes_all_three_with_the_repair`: ausgelieferte
  Normalisierung, Emoji-RTF, alle drei indexed, gespeicherter Body enthält
  U+1F600.
- Teil 1 allein: `test_an_rtf_with_an_emoji_is_indexed_and_keeps_the_emoji`
  (echte Extraktion, vorher `UnicodeEncodeError` in writer.py:315, nachher
  gespeichert "Hallo U+1F600 und ...", "weltkugel" findet das Dokument).

### Gates am Kopf 5dc1aa12 (lokal)

- ruff check (Vollsatz) "All checks passed!", ruff format --check "244 files
  already formatted", pyright (latest) "0 errors, 0 warnings, 0 informations",
  vulture 80 Exit 0.
- Volltestsuite in zwei Hälften mit den sechs --ignore: `tests/test_[a-m]*.py`
  3196 passed, 41 skipped; `tests/test_[n-z]*.py` 3420
  passed, 262 skipped, 1 failed: `test_a_large_broken_storage_does_not_hold_up_the_queue`
  mit `os error 5` im tantivy-Commit (gesperrte Segmentdatei unter Windows,
  bekannt aus 05-03 und 30-09, der Test berührt keinen der geänderten Pfade);
  test_poller.py danach dreimal einzeln 242 passed, 1 skipped, und der Lauf von
  Hälfte 2 vor der letzten Änderung an poller.py hatte ihn grün. CI ist der Beleg.
- test_phase41_audit.py dreimal hintereinander: 35 passed, 35 passed, 35 passed.

### Verbleibendes, bewusst

- Die RTF-Plausibilitätsprüfung zählt die zwei Hälften als nicht druckbar. Ein
  sehr kurzes RTF, das zu mehr als 10 Prozent aus Emoji besteht, bleibt
  skipped(empty_text) wie bisher; beim Bau des Regressionstests mit einem
  Satz von 20 Zeichen gesehen. Kein Stillstand, kein falsches Urteil über
  Nachbarn, nur eine Grenze, die es schon gab.
- Die 7 Dateien des Melders stehen nach 1.6.1 auf failed(repeatedly_stuck);
  nach dem Update holt `occ findling:index --restart` sie zurück (so im Issue
  beantwortet).

### Urteil Nachaudit #44

0 CRIT / 0 HIGH / 0 MEDIUM / 0 LOW offen über `efdca684..5dc1aa12`. #44 ist an
der Ursache behoben und zusätzlich je Datei eingedämmt, beides mit umgedrehten
Proben samt Positivkontrollen belegt. `audited_head` =
`5dc1aa127a495c78ec4ef5272a275c6788c92af0`. CI-Beleg siehe unten.
