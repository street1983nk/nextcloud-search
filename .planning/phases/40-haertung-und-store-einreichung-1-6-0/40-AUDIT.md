---
phase: 40-haertung-und-store-einreichung-1-6-0
audited: 2026-10-28
diff: v1.5.1..336ccae7
files_reviewed: 48
findings:
  critical: 0
  high: 0
  medium: 0
  low: 4
  total: 4
status: open
---

# Phase 40: Launch-Audit 1.6.0 (Security, Bugs, Performance)

**Stand:** offen (Security-Teil gefahren, Bugs und Performance folgen in Task 2).

**Umfang:** alle Änderungen des Milestones v1.6 (Phasen 37 bis 39). Basis ist
der Tag `v1.5.1`, Kopf beim Start `336ccae7`. `git diff --stat v1.5.1..336ccae7
-- backend/src backend/docker backend/appinfo/info.xml php/appinfo/info.xml
php/lib php/js php/templates php/l10n .github/workflows scripts/ci
docs/harp-tunnel.md`: **48 Dateien, 2258 Zeilen dazu, 199 weg**. Die beiden
info.xml wegen Access-Level und discussion-Element, docs/harp-tunnel.md wegen
des Kopierbefehls, den ein Admin ausführt. Gelesen bzw. per Probe gefahren:
`backend/src/findling/api/status.py`, `store/repo.py`, `extract/{archive,
errors,image,odf,office,sandbox}.py`, `nc/files.py`, `worker/reconcile.py`,
`backend/docker/harp_connect.sh`, `backend/docker/init.sh`,
`php/lib/Controller/SettingsController.php`,
`php/lib/Service/{AdminViewService,FileStateService,ScanStatsService,
SettingsService,StorageService}.php`, `php/templates/admin.php`,
`php/js/admin.js`, die 16 Kataloge, `.github/workflows/{deploy-harp,docker,
measure,python,scorecard,security,smb-acl-measure}.yml`,
`scripts/ci/smb_acl_measure.sh`, `scripts/ci/smb_acl_probe.php`,
`backend/pyproject.toml` und `uv.lock` (fastapi 0.143.2 auf 0.161.1, pypdf
6.21.1 auf 6.21.2, striprtf 0.0.33 auf 0.0.34).

**Wo gelaufen:** Windows 11 Pro 10.0.26200, ohne docker (Vorgabe der Phase).
Alle Proben stehen als Tests in `backend/tests/test_phase40_audit.py`. Die
Proben des Tunnel-Wächters brauchen bash, FIFO und POSIX-Signale und laufen
echt nur im gates-Job von python.yml (Ubuntu); lokal wurden sie zusätzlich
unter Git Bash als Gegenprobe gefahren, wo das möglich war.

## Security

### S1 Eingabe leaveOut (T-39-02)

- **Zugriffsebene:** `backend/appinfo/info.xml:347-349`, Route `^/status$`,
  `<access_level>ADMIN</access_level>`. Probe
  `test_s1_the_status_route_is_admin_and_the_only_route_that_reaches_it`:
  von allen Routen der info.xml trifft nur `^/status$` den Pfad `/status`,
  also hat leaveOut keine zweite, schwächer geschützte Route.
- **Missbrauchswerte:** `test_s1_every_malformed_leave_out_is_a_422_before_any_statement`
  mit den 15 Werten `""`, `"1,"`, `",1"`, `"1,,2"`, `" 1"`, `"1 "`, `"-1"`,
  `"+1"`, `"0x1"`, U+FF11 (Vollbreite), U+0663 (arabisch-indisch), `"1\n"`,
  19 Ziffern, 1001 IDs, 8001 Zeichen. Ergebnis: **15 mal 422**, und
  `report()` ist durch einen Rekorder ersetzt, der nie aufgerufen wurde (keine
  Abfrage läuft). `"1\n"` scheitert, weil pydantic das Muster mit der
  Rust-Regex-Engine prüft (`$` nur am Textende), Vollbreite und arabische
  Ziffern, weil `[0-9]` ASCII ist.
- **Ohne Parameter:** `indexedLeftOut` und `embeddedLeftOut` fehlen ganz
  (`test_s1_without_the_parameter_neither_counter_is_on_the_wire`).
- **Doppel-IDs:** `"2,2,2"` zählt wie `"2"` (2/2), Mengenbildung in
  `indexed_in_storages` und `embedded_in_storages`
  (`test_s1_a_repeated_id_counts_once`).
- **Führende Null:** `"01"`, `"1,02"`, `"00"` wurden mit 200 angenommen und
  als Storage 1 gezählt. Gleiche Klasse wie L-36-02: **F-40-01 (LOW)**.
- **SQL:** `test_s1_the_statements_carry_placeholders_and_never_an_id`
  fängt die Anweisungen an `execute()` einer aufzeichnenden Verbindung ab
  (der trace callback von sqlite3 zeigt die Werte eingesetzt und taugt dafür
  nicht): beide Zählanweisungen lauten `... storage_id IN (?,?)`, das Literal
  `987654321` steht in keiner. Formatiert wird nur die Zahl der Platzhalter
  (`repo.py:444-451`).
- **PHP-Seite:** `AdminViewService::leaveOutParameters` deckelte die Anzahl
  (1000), nicht die Länge. 1000 IDs mit acht Ziffern liegen unter der
  Anzahl und über 8000 Zeichen; der Container antwortet 422
  (`test_s1_a_thousand_ids_of_eight_digits_are_past_the_length_ceiling`), und
  `ExAppService::adminGet` macht aus jedem Status ab 400 ein `null`, die Seite
  zeigt dann "Backend nicht erreichbar" statt der Zählung wie 1.5:
  **F-40-04 (LOW)**.

### S1b info.xml beider Apps, discussion-Link

- `git diff v1.5.1..336ccae7 -- backend/appinfo/info.xml php/appinfo/info.xml`:
  in beiden Dateien nur ein Kommentar und
  `<discussion>https://help.nextcloud.com/t/.../249775</discussion>`; kein
  Access-Level einer Route geändert, keine Route dazu oder weg.
- Kein Codepfad ruft die discussion-URL ab. Beleg
  `test_s1b_no_code_path_fetches_the_discussion_url`: kein `.py`, `.php`
  oder `.js` unter backend/src, php/lib, php/js und php/templates enthält
  `249775` oder `help.nextcloud.com`. Das Element ist ein statischer Link der
  Store-Seite.

### S2 Dateizugriff der zweiten Leseverbindung (ATTACH von vectors.db)

- `embedded_in_storages` (`repo.py:1954`) bekommt beide Pfade nur aus der
  aufgelösten Konfiguration: `status.py:791`
  `embedded_in_storages(resolved.state_db, resolved.vectors_db, leave_out)`,
  die einzige Aufrufstelle (`test_s2_the_route_takes_both_paths_from_the_settings_only`).
  Aus der Anfrage kommen nur Zahlen.
- Fehlende vectors.db bleibt fehlend: `sqlite3.OperationalError`, keine Datei
  `vectors*` entsteht (`test_s2_a_missing_vector_database_stays_missing`).
- Sonderzeichen im Pfad: Verzeichnis `probe dir #1 %20 100%` (unter Linux
  zusätzlich ` what?mode=rw`, auf Windows ist `?` im Namen unmöglich).
  `Path.as_uri()` kodiert Leerzeichen, `#`, `%` und `?`; gezählt wird richtig
  (1 bzw. 2), daneben entsteht keine Datei unter einem abgeschnittenen Namen
  (`test_s2_a_path_with_blank_hash_percent_and_question_mark_is_counted_right`).
- Schreibversuch: die Zählanweisung wird in der Probe durch `DELETE FROM files`,
  `DELETE FROM vec.chunks` und `UPDATE files` ersetzt; alle drei scheitern mit
  `OperationalError` (readonly bzw. query_only), die Zählung danach ist
  unverändert 2 (`test_s2_a_write_over_the_connection_is_refused`).
- Paralleler Schreiber im WAL-Modus, einmal auf state.db, einmal auf
  vectors.db, mit offener `BEGIN IMMEDIATE`-Transaktion: die Zählung liefert
  den Stand vor der offenen Schreibung (2) und braucht weit unter der Hälfte
  des `busy_timeout` von 10 s
  (`test_s2_a_parallel_writer_in_wal_neither_blocks_nor_leaks`).

### S3 Tunnel-Wächter harp_connect.sh

- **lokale Ausführung nicht möglich:** bash mit FIFO und POSIX-Signalen gibt
  es auf dieser Box nur als Git Bash (WSL ist nur die docker-desktop-Distro).
  Die Proben sind auf win32 übersprungen und laufen echt im Schritt "The audit
  probes of 1.6.0 by name (test_phase40_audit.py)" des gates-Jobs von
  python.yml (Lauf-ID und PASSED-Zeilen trägt Task 3 unter "Stand" nach).
- **Lektüre:** kein `eval`, keine unquotierte Expansion von `${line}`; jede
  frpc-Zeile geht über `printf '%s\n' "${line}"` hinaus (nie als
  Formatstring), erkannt wird nur per `[[ "${line}" == *"..."* ]]`; keine Zeile
  wird Dateiname oder Befehl. Die Abhilfe-Zeile ist fest, mit
  `${CERT_DIR}` aus der Umgebung des Containers. FIFO mit `mkfifo -m 600`
  (`:449`), Konfiguration unter `umask 077`, `REMEDY_SCHEDULE` per
  `IFS=',' read -r -a` (`:173`) und Ziffernprüfung je Eintrag.
- **Injektionsprobe** `test_s3_hostile_frpc_lines_are_passed_through_and_never_run`:
  ein frpc-Double gibt `$(touch pwned)`, Backticks, `${IFS}$((1/0))${HP_SHARED_KEY}`,
  `%s%n%x%d%%%c`, ANSI- und OSC-Escapes, eine 64-KiB-Zeile, eine Zeile mit
  allen Bytes 0x01 bis 0xFF außer `\n` und danach 10 000 x509-Zeilen aus.
  Erwartet: keine Datei `pwned*`, der Schlüssel nie in der Ausgabe, jede
  Zeile Byte für Byte durchgereicht, Abhilfe-Zeile genau einmal (Plan 0, 300,
  900, 3600 s), frpc genau einmal gestartet, Exit 1 nach frpc-Exit 0, unter
  60 s. Gegenprobe unter Git Bash (200 statt 10 000 x509-Zeilen): alles wie
  erwartet bis auf die 64-KiB-Zeile, die nicht ganz ankam.
- **Ursache der 64-KiB-Zeile:** `read -t` gibt nach `POLL_SECONDS` auf, wenn
  eine Zeile bis dahin nicht vollständig ist, und hält das Gelesene in der
  Variablen; der Wächter warf es weg, der Rest stand als eigene Zeile da.
  Probe `test_s3_f_40_02_a_line_slower_than_the_poll_interval_stays_whole`:
  ein frpc-Double schreibt `connect to server error: tls: ...`, wartet 2,5 s
  (Poll 1 s) und schreibt `x509: ...\n`. Ergebnis unter Git Bash: nur
  `x509: ...` im Log, **keine Abhilfe-Zeile**. **F-40-02 (LOW)**: frpc
  schreibt eine Zeile in einem `write`, beim Standard-Poll von 10 s ist das
  im Betrieb kaum erreichbar, aber eine x509-Meldung kann so unerkannt
  bleiben.
- **Symlinks und Leerzeichen:** `test_s3_symlinked_files_in_a_directory_with_blanks_switch_to_mutual_tls_once`
  (Harness aus test_harp_connect_supervisor.py wiederverwendet):
  Zertifikatsverzeichnis `certs with blanks`, die drei Dateien als Symlinks
  auf Dateien außerhalb. Erwartet: genau ein Neustart in mTLS,
  `transport.tls.certFile = "<verzeichnis>/client.crt"` korrekt quotiert,
  danach "connected again". Wer /certs/frp beschreiben kann, kontrolliert den
  Tunnel ohnehin (HaRP-Volume); ein Symlink öffnet also keinen neuen Weg.
- **Kopierbefehl in docs/harp-tunnel.md** (Abschnitt
  repair-without-re-registering): Quotierung sauber (`"$1"` als Positionsparameter,
  `"$HARP"`), Ziel nur unter /certs/frp, `umask 077`, temporärer Name plus
  `mv -f`. Aber: scheitert das erste `docker exec "$HARP" cat` (zum Beispiel
  bei vertipptem Containernamen), liest die Backend-Hälfte nichts, schreibt
  eine leere Datei und verschiebt sie über das Zertifikat. Probe
  `test_s3_f_40_03_an_empty_read_leaves_the_file_as_it_was` gegen die
  Backend-Hälfte des Befehls aus der Doku; Gegenprobe mit `sh` unter Git Bash:
  leerer Lesevorgang ergibt eine leere `client.key`. **F-40-03 (LOW)**.

### S4 Ausgabe und XSS der neuen Sätze

- `test_s4_admin_js_writes_no_markup_at_all`: in php/js/admin.js kein
  `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, kein
  jQuery-`$(`/`.html(`.
- `test_s4_the_new_flags_only_toggle_static_elements`:
  `coverage.rulesPending` und `coverage.deliberatelyLeftOut` stehen nur in
  Bedingungen und im Fingerabdruck, nie in `textContent`; `coverage.deduplicated`
  kommt in admin.js gar nicht vor; die drei Elemente
  `findling-coverage-leftout-explain`, `-leftout-none` und `-rules-pending`
  werden nur über `shown(...)` (also `hidden`) geschaltet.
- `test_s4_the_three_sentences_are_rendered_escaped_by_the_template`: die drei
  neuen en-Sätze stehen je genau einmal in templates/admin.php, jeweils als
  `<?php p($l->t('...')); ?>`; `p()` escaped die Übersetzung aller 16
  Kataloge.

### S5 Zustandsschreiben im GET, Weg C ohne ACL-Einfluss

- `rulesPendingNow()` (`AdminViewService.php:2039`) löscht `rules_changed_at`
  per `forgetRulesChange()` beim ersten Poll nach dem Nachzählen. Bewertung:
  nur die ADMIN-Seite (Route der Settings-Seite), idempotent (schreibt nur,
  solange ein Stempel steht), keine Fremdeingabe (Zeitstempel aus dem
  eigenen appconfig). `test_s5_the_stamp_is_cleared_by_the_admin_page_only`:
  `forgetRulesChange(` steht nur in SettingsService (Definition) und genau
  einmal in AdminViewService. Rennen dazu siehe B4.
- `test_s5_the_counting_key_lives_in_the_counting_paths_only`:
  `countingKey(`/`countingKeyGroups(` stehen in php/lib nur in
  StorageService.php (Definition) und AdminViewService.php (Aufruf in
  `overview()`); ScanStatsService bekommt nur die fertigen Gruppen als
  Zahlenlisten. SearchService, AclService und der Indexpfad sehen die
  Gruppierung nie (T-40-06 accept bestätigt).

### S6 Workflows und Messskripte

- `scripts/ci/smb_acl_measure.sh`: **in scope, geprüft.** Läuft nur im
  dispatch-only Workflow auf einem Wegwerf-Runner; die beiden Samba-Passwörter
  sind feste Testwerte, gehen nur per stdin an `smbpasswd -s`, per
  `--password-from-env` an occ und per `-u` an curl, nie in eine Logzeile;
  `set -euo pipefail`, kein `eval`.
- `scripts/ci/smb_acl_probe.php`: **in scope, geprüft.** Nimmt Serverpfad,
  Kommando und Nutzer aus argv, das Passwort aus `PROBE_PASS`, gibt nur
  `stored`/`missing`/`seeded`, `node=... storage=...` oder einen
  Klassennamen aus, nie Passwort oder Dateiinhalt.
- `smb-acl-measure.yml`: nur `workflow_dispatch`, `permissions: contents: read`,
  keine `secrets.`, jede Action per 40-stelligem SHA gepinnt
  (`test_s6_the_smb_measurement_is_dispatch_only_read_only_and_pinned`).
- Alle Workflows: jedes `uses:` außer lokalen Actions per vollem SHA
  (`test_s6_every_action_of_every_workflow_is_pinned_to_a_full_sha`).
- deploy-harp.yml, Rotationsschritt: der HaRP-Schlüssel entsteht per
  `openssl rand -hex 16` und ist sofort per `::add-mask::` maskiert; der Schritt
  druckt nur die ersten 12 Zeichen des CA-Digests (öffentliches Zertifikat),
  `client.key` wird nie gehasht oder gedruckt; `permissions: contents: read`.
- Diffs von docker.yml, measure.yml, scorecard.yml, security.yml: nur
  SHA-Bumps gepinnter Actions (docker/login-action 4.7.0,
  codeql-action 4.39.1, setup-uv 10.3.2). python.yml: dazu der
  shellcheck-Schritt (installiert shellcheck aus dem Ubuntu-Archiv).

### S7 Abhängigkeiten

- `backend/uv.lock`: `starlette` **1.6.0** (Zeile 962/963), Constraint
  `{ name = "starlette", specifier = ">=1.0.1" }` (Zeile 6), `fastapi` 0.161.1
  (Zeile 149/150): der Boden von CVE-2026-48710 (BadHost) hält
  (`test_s7_the_lock_keeps_starlette_above_the_badhost_floor`).
- "Security scans" auf dem Startkopf 336ccae7: Lauf **40736775766** success.

## Befunde

### F-40-01 (LOW): leaveOut nimmt eine führende Null

- **Ort:** `backend/src/findling/api/status.py:142`, `LEAVE_OUT_PATTERN`
  `^[0-9]{1,18}(,[0-9]{1,18})*$`.
- **Probe:** `test_s1_f_40_01_only_canonical_numbers_are_taken` (`"01"`,
  `"1,02"`, `"00"`): 200 und Zählung für Storage 1 statt 422.
- **Einordnung:** nur der eigene Companion erreicht die ADMIN-Route, er
  schreibt Ganzzahlen per `implode`; kein Schaden, aber eine Antwort auf eine
  nicht gestellte Frage (Klasse L-36-02).

### F-40-02 (LOW): Eine Zeile, die langsamer als der Poll ankommt, verliert ihren Anfang

- **Ort:** `backend/docker/harp_connect.sh`, Leseschleife (`read -r -t`,
  Zweig "Above 128").
- **Probe:** `test_s3_f_40_02_a_line_slower_than_the_poll_interval_stays_whole`,
  rot unter Git Bash (nur `x509: ...` im Log, keine Abhilfe-Zeile).
- **Einordnung:** Daten aus dem Netz werden nicht ausgeführt (S3), aber eine
  Logzeile geht verloren und eine x509-Meldung bleibt unerkannt.

### F-40-03 (LOW): Ein leerer Lesevorgang leert das Zertifikat im Backend

- **Ort:** `docs/harp-tunnel.md:52`, gleicher Befehl in
  `.github/workflows/deploy-harp.yml:1089`.
- **Probe:** `test_s3_f_40_03_an_empty_read_leaves_the_file_as_it_was`; mit
  `sh` unter Git Bash: leere Eingabe ergibt leere `client.key`.
- **Einordnung:** nur bei einem Bedienfehler in einer Lage, in der der Tunnel
  ohnehin steht; der Wächter nimmt die leeren Dateien als geänderte Dateien
  und startet frpc darauf neu.

### F-40-04 (LOW): Die Admin-Seite kennt die Längendecke von leaveOut nicht

- **Ort:** `php/lib/Service/AdminViewService.php`, `leaveOutParameters`.
- **Probe:** `test_s1_a_thousand_ids_of_eight_digits_are_past_the_length_ceiling`
  (422 am Container) und `test_s1_f_40_04_the_page_holds_the_length_ceiling_of_the_route_too`
  (rot: keine Längendecke auf der PHP-Seite).
- **Einordnung:** erst ab Storage-IDs mit acht Ziffern und gut 900
  ausgelassenen Storages; dann aber "Backend nicht erreichbar" statt der
  Zählung wie 1.5.

## Was gegengeprüft wurde, nicht nur gelesen

| Prüfung | Verfahren (anders als die Umsetzung) | Ergebnis |
|---|---|---|
| S1 | 15 Missbrauchswerte gegen die echte Route, report() durch einen Rekorder ersetzt | 15 mal 422, Rekorder leer; F-40-01 |
| S1 SQL | Anweisungen an execute() einer aufzeichnenden Verbindung statt Quelltext | nur Platzhalter |
| S2 | Schreibanweisung in die Funktion gereicht statt Pragmas gelesen; WAL-Schreiber mit offener Transaktion | readonly, kein Block |
| S3 | eigenes frpc-Double mit Bytes statt der Harness-Zeilen; Gegenprobe unter Git Bash | nichts ausgeführt; F-40-02, F-40-03 |
| S4 | alle Senken von admin.js gesucht statt der neuen Zeilen | keine Markup-Senke |
