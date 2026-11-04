---
phase: 41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes
audited: 2026-11-04
audited_head: 738a13731f6448aa97f0a752d5553c6c54db3e85
diff: v1.6.1..738a1373
files_reviewed: 46
findings:
  critical: 0
  high: 0
  medium: 0
  low: 4
  info: 4
  total: 8
status: passed
recommendation: 1.6.2 ohne Code-Fix; vier LOW als Owner-Punkte (41-10) bzw. v1.7
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
