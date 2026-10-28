---
phase: 40-haertung-und-store-einreichung-1-6-0
audited: 2026-10-28
diff: v1.5.1..336ccae7
files_reviewed: 48
findings:
  critical: 0
  high: 0
  medium: 0
  low: 6
  total: 6
status: open
---

# Phase 40: Launch-Audit 1.6.0 (Security, Bugs, Performance)

**Stand:** offen (Security, Bugs und Performance gefahren; Fixes und LOW-Entscheidungen folgen in Task 3).

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

## Bugs

### B1 Weg C, Zählschlüssel

- Vorhanden in `php/tests/Unit/StorageServiceTest.php`: "@" im Nutzernamen
  (`testALoginNameWithAnAtSignKeepsTheHostAfterTheLastOne`), Port bei SFTP und
  home::/local::/object::/webdav::/owncloud::/amazon:: nie gruppiert
  (`testSftpIsGroupedWithItsPortAndOtherBackendsAreNot`), md5-gekürzte IDs
  (`testAnIdNextcloudHashedIsNeverAGroup`), `$user` in der Wurzel
  (`testARootWithTheUserInItIsNeverAGroup`).
- Ergänzt (fehlte): `testADoubleSlashInTheLoginNameIsNeverAGroupAndOneInTheRootStaysInTheKey`.
  Ein `//` im Login-Namen (`smb::corp//anna@fs.example//team//`) lässt vor dem
  ersten `//` kein `@`, also keine Gruppe (sichere Richtung); ein `//` tiefer in
  der Wurzel bleibt Teil des Schlüssels; Domänen-Login mit `@` und Port bei
  SFTP ergibt denselben Schlüssel wie ein einfacher Login. Host = Text nach dem
  LETZTEN `@` vor dem ersten `//`, wie in 39-01 belegt. Läuft nur in "PHP and
  store metadata gates" (Lauf-ID unter "Stand").

### B2 Nenner unter Weg C

- Belegt vorhanden in `AdminViewServiceTest.php`:
  `testANumeratorNeverFallsBelowNought` (indexedLeftOut 50 > indexed 10 ergibt
  0, nicht negativ), `testAFigureIsNeverNegativeAndNeverAboveAHundred`
  (`coverageShare`: mehr gezählt als indexierbar ergibt null, nie 100),
  `testAContainerWithoutTheTwoFieldsGivesNullAndNotNought` und
  `testHalfAnAnswerIsNoDeduplication` (Rückfall auf 1.5 ohne beide Felder).
- Container-Seite neu: `test_b2_the_left_out_counter_never_exceeds_the_figure_it_is_subtracted_from`
  (alle Storages ausgelassen, mit Tombstone): `indexedLeftOut <= indexed`,
  `embeddedLeftOut <= embedded`. Die Klammer bei 0 in `figures()` ist also nur
  Absicherung, keine Korrektur eines Normalfalls. Kein Befund.

### B3 IN-Fixes aus 39-03

- `archive.too_many_entries`: `test_b3_too_many_entries_judges_the_limit_like_1_5`
  mit gesenkter Grenze 20: 19 und 20 Einträge False, 21 True; Grenze selbst
  bleibt erlaubt wie in 1.5. Bestandstests mit der echten Grenze:
  `test_extract_signatures.py` Zeile 435 (Grenze + 1 blockiert) und 457 (Grenze
  liest), `test_10001_entries_are_an_archive_limit`. Kaputte Datei und fehlende
  Datei ergeben False, der Leser selbst diagnostiziert
  (`test_b3_a_file_that_is_no_package_is_left_to_its_reader`).
- Verwaiste vanished_storages-Stempel: `test_b3_a_stamp_of_a_storage_with_a_living_row_and_a_bookmark_stays`:
  Storage 7 (lebende Zeile, Lesezeichen, Stempel, nicht gelistet) behält
  Stempel und Lesezeichen, der alte Stempelwert bleibt; Storage 8 (nur
  Stempel) verliert ihn. Bestand: `test_an_orphan_stamp_is_dropped_with_the_orphan_bookmarks`,
  `test_an_orphan_stamp_alone_is_dropped_without_any_bookmark`. Kein Befund.

### B4 rules_changed_at: saveRules gegen rulesPendingNow

- Lektüre `AdminViewService.php:2039-2056` und `SettingsService::forgetRulesChange`:
  der Poll liest den Stempel, entscheidet "nicht mehr ausstehend" und ruft dann
  `forgetRulesChange()`, das den Stempel ein zweites Mal liest und auf 0 setzt.
  Speichert ein zweiter Admin genau zwischen diesen beiden Lesungen neue
  Regeln, löscht der Poll den neuen Stempel mit, und der Hinweis für diese
  Änderung erscheint nicht. Zweiter Fall: Stempel und Recount-Beginn haben
  Sekundenauflösung; startet ein Recount in derselben Sekunde vor dem
  Speichern, gilt er als "nach der Änderung" (`recountedAt >= changedAt`), und
  der Hinweis endet, sobald keine Crawl- oder Sweep-Jobs mehr anstehen.
- Folge in beiden Fällen: nur der Hinweissatz fehlt; die Suche wendet die
  Regel sofort an, die Zähler stimmen nach dem nächsten Recount. Kein Einfluss
  auf Rechte oder Suche. **F-40-05 (LOW)**.

### B5 fastapi 0.143.2 auf 0.161.1

Release-Notes 0.144 bis 0.161.1 (GitHub-API, Stand 28.10.2026) mit
Verhaltensänderung für unsere Nutzung:

- 0.148.0: Standardwerte weggelassener Query-Parameter werden nicht mehr
  validiert. leaveOut hat den Standard `None`; abgedeckt durch
  `test_s1_without_the_parameter_neither_counter_is_on_the_wire` und
  `test_status_endpoint.py::test_an_old_companion_without_the_parameter_gets_no_new_field`.
- 0.155.0: `**extra` an `Query()` entfernt (TypeError). Wir übergeben nur
  `max_length` und `pattern`; der Import der App in jeder Testdatei mit
  TestClient deckt es ab.
- 0.156.0 bis 0.156.6: Field-Attribute in Request-Parametern erhalten.
  Musterprüfung abgedeckt durch die 15 Werte von S1 und
  `test_status_leave_out.py::test_anything_but_a_short_list_of_numbers_is_refused`.
- `Field(exclude_if=...)` (pydantic, Antwortmodell): unverändert, abgedeckt
  durch `test_status_endpoint.py::test_an_old_companion_without_the_parameter_gets_no_new_field`
  und S1 (Felder fehlen ohne Parameter).
- 0.146.0 (`root_path` deprecated), 0.147/0.149/0.150 (Formulare), 0.151
  (JSON-Body `null`), 0.152 (Header-Modelle), 0.160 (Parametermodelle): nicht
  genutzt (`grep root_path\|openapi_prefix\|Body(\|Form(` in backend/src
  leer). Kein Befund.

### B6 Tombstones: indexed gegen indexedLeftOut

- `Store.counts()` (`repo.py:1052-1062`) zählt alle Zeilen mit Zustand
  `indexed`, auch tombstoned (Stand 1.5, Feld `indexed` der Antwort);
  `indexedLeftOut` zählt nur lebende (`deleted_at IS NULL`, so geplant in
  39-01). Probe `test_b6_f_40_06_a_tombstone_stays_in_indexed_and_out_of_indexed_left_out`:
  Storage 2 mit 2 lebenden und 1 Tombstone, `indexed` 5, `indexedLeftOut` 2,
  Zähler nach Abzug 3, also bleibt der Tombstone im Zähler.
- Beziffert: Zähler unter Weg C = lebende Dokumente des Repräsentanten plus
  ALLE Tombstones der Gruppe. Beispiel: eine Freigabe für 10 Nutzer mit 1000
  Dateien, 10 davon gelöscht und tombstoned (je Storage 10, zusammen 100
  Zeilen). In 1.5 hebt das den Zähler um 100 bei 9900 indexierbar (rund 1
  Punkt), unter Weg C um 100 bei 990 indexierbar (rund 10 Punkte), solange
  die Erstindexierung läuft. Bei voller Abdeckung ist der Zähler in beiden
  Fällen größer als indexierbar, und `coverageShare` zeigt keine Zahl statt
  einer falschen (wie in 1.5). Die Verstärkung um die Gruppengröße ist neu in
  v1.6. **F-40-06 (LOW)**.

## Performance

### P1 Kosten von GET /status mit leaveOut

- `test_p1_the_status_call_with_leave_out_over_a_hundred_thousand_documents`
  (`-m timing`, nur mit `FINDLING_TIMING=1`): synthetischer Bestand von
  100 000 lebenden indexierten Dokumenten in 3 Storages (40 000, 30 000,
  30 000), jedes mit einer Vektorzeile, `leaveOut=2,3` (60 000 Dokumente,
  unter der Decke). Gemessen am 28.10.2026 auf dieser Box, Median von 5
  Läufen über den TestClient: **ohne leaveOut 55,0 ms, mit leaveOut 95,2 ms**,
  also rund 40 ms für beide Zähler über 60 000 Dokumente. Ergebnis
  `(indexedLeftOut, embeddedLeftOut) = (60000, 60000)`.
- Decke `LEFT_OUT_EMBEDDED_CEILING` mit der echten Zahl, nicht gesenkt:
  `test_p1_the_vector_figure_stops_above_a_hundred_thousand_documents`,
  Storage 2 mit genau 100 000 Dokumenten: `embeddedLeftOut` 100000 da; mit
  100 001: Feld fehlt, `indexedLeftOut` 100001. Läuft ohne Timing-Schalter.
  Kein Befund.

### P2 Abfragen und Container-Aufrufe je Poll der Admin-Seite

- **Container-Aufrufe je Poll:** v1.5.1 `AdminViewService.php:672`
  `adminGet('/status', ..., [])`, HEAD `:655` `adminGet('/status', ...,
  $parameters)`: leaveOut hängt am bestehenden Statusaufruf. Dazu in beiden
  Ständen `/rates` in `estimate()` (v1.5.1 `:2139`, HEAD `:2352`), nur solange
  die Erstindexierung läuft. Also **1 Aufruf je Poll nach der Erstindexierung,
  2 währenddessen, in v1.5.1 und HEAD gleich**. Kein zusätzlicher Aufruf.
- **Datenbankabfragen:** `ScanStatsService::totals` v1.5.1 zwei Abfragen je
  Band von 500 Storages (Summen und `finished_at`), HEAD eine (Zeilen, im
  Speicher summiert). Neu: `StorageService::countingKeyGroups` eine Abfrage
  je Band von 200 Storages gegen oc_storages, nur mit externen Speichern und
  ab zwei Mounts; `FileStateService::countByReason` für die ausgelassenen
  Storages eine Abfrage, nur wenn eine Gruppe etwas ausließ;
  `rulesWorkQueued` höchstens zwei Zeilen (je Jobklasse eine), nur solange ein
  Stempel steht und der Recount danach begann; `forgetRulesChange` ein
  Schreibzugriff, einmal je Änderung. Bei bis zu 500 Mounts ohne Gruppe:
  v1.5.1 2, HEAD 2 (1 totals plus 1 Gruppenabfrage), mit Gruppe 3. Kein
  Befund (P5 aus 36-12: keine Abfrage je Storage).

### P3 Wächter: Leerlauf und Flut

- Lektüre: die Leerlauf-Schleife wartet in `read -r -t "${POLL_SECONDS}"`
  (`harp_connect.sh:468`), kein Busy-Wait; je Durchlauf höchstens ein
  `check_files` (Fingerabdruck über zwei `sha256sum`).
- Probe `test_p3_ten_idle_seconds_are_about_ten_looks_at_the_files_and_no_busy_wait`
  (Linux): ein `sha256sum` vorn im PATH zählt die Aufrufe, 10 s Leerlauf bei
  Poll 1 s müssen höchstens ceil(10/1)+1 Blicke auf die Dateien sein und
  mindestens 5; CPU-Zeit des Wächters samt Kindern aus `/proc/<pid>/stat`
  unter 1 s. Zahl aus dem CI-Lauf unter "Stand".
- Flut: 10 000 x509-Zeilen unter 60 s (S3-Probe). Jede x509-Zeile kostet
  einen Subshell-Fork für `remedy_due`; frpc wählt höchstens alle paar
  Sekunden neu, im Betrieb sind das wenige Zeilen je Minute. Kein Befund.

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

### F-40-05 (LOW): Hinweis nach Regeländerung kann bei einem Rennen ausbleiben

- **Ort:** `php/lib/Service/AdminViewService.php:2039-2056` (`rulesPendingNow`),
  `SettingsService::forgetRulesChange`.
- **Beleg:** B4 (Lektüre, zwei Lesungen des Stempels ohne Vergleich beim
  Löschen; Sekundenauflösung von Stempel und Recount-Beginn).
- **Einordnung:** nur der Hinweissatz fehlt, Suche und spätere Zähler stimmen.

### F-40-06 (LOW): Tombstones ausgelassener Storages bleiben im Zähler

- **Ort:** `backend/src/findling/store/repo.py:444-451`
  (`_INDEXED_IN_STORAGES_SQL` mit `deleted_at IS NULL`) gegen
  `Store.counts()` (`:1052`).
- **Probe:** `test_b6_f_40_06_a_tombstone_stays_in_indexed_and_out_of_indexed_left_out`.
- **Einordnung:** die Prozentzahl kann während der Erstindexierung um die
  Tombstones der ganzen Gruppe zu hoch stehen (Beispiel B6: rund 10 statt 1
  Punkt); bei voller Abdeckung keine falsche Zahl, sondern keine.

## Was gegengeprüft wurde, nicht nur gelesen

| Prüfung | Verfahren (anders als die Umsetzung) | Ergebnis |
|---|---|---|
| S1 | 15 Missbrauchswerte gegen die echte Route, report() durch einen Rekorder ersetzt | 15 mal 422, Rekorder leer; F-40-01 |
| S1 SQL | Anweisungen an execute() einer aufzeichnenden Verbindung statt Quelltext | nur Platzhalter |
| S2 | Schreibanweisung in die Funktion gereicht statt Pragmas gelesen; WAL-Schreiber mit offener Transaktion | readonly, kein Block |
| S3 | eigenes frpc-Double mit Bytes statt der Harness-Zeilen; Gegenprobe unter Git Bash | nichts ausgeführt; F-40-02, F-40-03 |
| S4 | alle Senken von admin.js gesucht statt der neuen Zeilen | keine Markup-Senke |
| B2 | Container-Zähler gegen ihre Minuenden statt der PHP-Klammer | nie größer |
| B6 | Tombstone im Probebestand statt Lektüre von 39-01 | F-40-06 beziffert |
| P1 | echte Decke 100 000 statt gesenkter, 100 000 Zeilen per Bulk-Insert | Feld fehlt ab 100 001 |
| P3 | sha256sum vorn im PATH zählt die Schleife, CPU aus /proc | Zahl in Stand |
