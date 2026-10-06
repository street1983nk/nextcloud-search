# Auditbericht Phase 29

## CI-Beweis

Stand: 06.10.2026, Plan 29-13. Dieser Abschnitt nennt je Push den Kopf-SHA, die Laufnummer je Workflow und das Ergebnis.

### Push 1: 57b83358..390360c3

Freigabe des Owners, wörtlich: Auf die Frage "Bestaetigst du den Push von main (57b83358..390360c3) nach origin?" antwortete der Owner "ok". Vor dem Push geprüft: 76 Commits, alle von street1983nk, keine Co-Authored-By- oder Claude-Trailer; Suche in `git log -p` nach IPv4- und Token-Mustern ergab nur die Loopback-Adresse, eine Adresse aus dem Dokumentationsnetz nach RFC 5737 und den Plantext selbst; keine Box-Adresse, kein Token.

Kopf: `390360c3d21e5c827223362f3df33728512d42c7`, gepusht 10:49Z.

| Workflow | Lauf | Attempt | Ergebnis |
|---|---|---|---|
| Python gates (python.yml) | 37452332061 | 1 | success, 4721 passed, 14 skipped |
| PHP and store metadata gates (php.yml) | 37452332197 | 1 | success, PHPUnit `OK (589 tests, 2106 assertions)` |
| Multi-arch image (docker.yml) | 37452332135 | 1 | success, amd64 und arm64 |
| Integration (integration.yml) | 37452332015 | 1 | success |
| Resilience (resilience.yml) | 37452332174 | 1 | success |
| HaRP deploy (deploy-harp.yml) | 37452332294 | 1 | **failure**, nur Bein stable34/8.2/ubuntu-24.04, Schritt "Store upgrade 3" |

Die PHPUnit-Suite (`php/tests/Unit`) enthält `Version001400Date20261006000000Test.php`, `ProfileControllerTest.php` und `AdminViewServiceTest.php`; sie liefen damit erstmals in CI und sind grün.

Belege aus dem Bein stable34/amd64 (Job 112231598056), alle Schritte bis "Store upgrade 2b" grün:

- Store install 7: `content hit after 3 cron rounds, with nothing configured` und `occ calls between the installation and the hit: none, which is what zero config means`.
- Store upgrade 2b: `the picture is failed/corrupt in state.db and in findling_file_state`, `the sidecar is failed/corrupt in state.db and in findling_file_state`, `sown: a picture and a sidecar, both failed(corrupt) under v1.3.2, and the seed word finds nothing`.

### Befund C-29-01: Sprachmarke der 1.3.2-Installation

- Roter Schritt: "Store upgrade 3", `the v1.3.2 installation reports the languages mark 'de,en' instead of an empty one, so a rebuild already stamped it`.
- Kein Flake-Muster: Die Zusicherung prüfte eine Annahme aus Plan 29-11 ("1.3.2 meldet die Marke leer, solange kein Neuaufbau sie stempelt"), die der erste echte Lauf widerlegt. Die Upgrade-Strecke läuft nur auf diesem Bein, die anderen drei Beine waren dort `skipped`.
- Ursache, belegt am Code des Tags v1.3.2: `findling.index.open.stamp_a_new_directory` schreibt Schema-, Sprach- und Niederländisch-Marke, bevor ein frisches Indexverzeichnis angelegt wird (Befund M-19-05). Eine frische 1.3.2-Installation trägt die Marke deshalb mit dem registrierten Satz de,en. Das Produkt verhält sich richtig, die Erwartung im Workflow war falsch.
- Fix `8ae89572`: "Store upgrade 3" verlangt `de,en` (den Satz, den "Store upgrade 4" registriert, also ordnet das Upgrade keinen Neuaufbau an); "Store upgrade 5" verlangt `de,en` vorher und denselben Wert nachher. Das ist nicht schwächer als vorher: Jeder andere Wert vorher und jede Änderung nachher sind rot. Der Test `test_upgrade_seed_steps.py` folgt und prüft zusätzlich die Bedingung in Schritt 5.
- Lokal vor dem Commit: volle Suite 4711 passed, 25 skipped; ruff, ruff format, pyright (latest), vulture sauber.

### Push 2: 390360c3..7130c4f0

Freigabe des Owners, wörtlich: Auf die Frage "Darf ich die 2 Commits 390360c3..7130c4f0 (8ae89572 Fix, 7130c4f0 Auditbericht) auf origin/main pushen?" antwortete der Owner "ok".

Kopf: `7130c4f0240d88ca650f8ca44153bf98ff936b3b`, gepusht 11:21Z.

| Workflow | Lauf | Attempt | Ergebnis |
|---|---|---|---|
| Python gates | 37455892343 | 1 | **failure**, 1 failed (Befund C-29-02), 4721 passed, 14 skipped |
| Multi-arch image | 37455892371 | 1 | success |
| Integration | 37455892246 | 1 | success |
| Resilience | 37455892221 | 1 | success |
| HaRP deploy | 37455892381 | 1 | **failure**, nur Bein stable34/amd64, Schritt "Store upgrade 6" (Befund C-29-03); stable33, stable34/arm64 und stable35 success |
| PHP and store metadata gates | nicht ausgelöst | | Pfadfilter: der Diff 390360c3..7130c4f0 berührt weder `php/**` noch `backend/appinfo/**` noch einen anderen Pfad des Filters; der Beleg bleibt Lauf 37452332197 |

Belege aus dem Bein stable34/amd64 (Job 112243285452), Schritte 3 bis 5 jetzt grün:

- Store upgrade 4: `the instance performed the app update: 1.3.2 to 1.4.0`.
- Store upgrade 5, wörtlich:
  - `unchanged  .marks.indexVersion = 1`, ebenso schemaVersion 2, analyzerVersion 1, wordlistHash und tantivyVersion unverändert.
  - `the sidecar is skipped/system_file in state.db and in findling_file_state`
  - `the picture is indexed in state.db and carries no verdict in findling_file_state`
  - `the seed word finds exactly the file id 141, the picture 1.3.2 had booked as corrupt`
  - `no start_rebuild_on_drift line in 60 lines of container log`
  - `the recheck mark was absent before the upgrade and reads done after it`
  - `the languages mark reads de,en before and after the upgrade, nothing was restamped`
  - `unchanged  embedding mark = multilingual-e5-small/int8/384/1024` und `unchanged  vector stock without the picture = ...:94:222`, keine Neu-Einbettung des Bestands; `the picture carries 1 chunk(s), embedded once as a new document`
  - `the profile in force after the upgrade is economy`
  - `all eight assurances hold`
- Store upgrade 6: neun von zehn Zusicherungen grün, darunter `the question alemanes went from 0 to 1 hits across the rebuild` und `vectors.db is unchanged`.

### Befund C-29-02: Adressmuster im Auditbericht

- Rot: `test_public_artifacts.py::test_no_file_under_docs_carries_a_finding_outside_the_exception_list[muster-der-umsetzung]`, gefunden in diesem Bericht.
- Ursache: Der Abschnitt zu Push 1 nannte die beiden bei der Vorab-Suche gefundenen Adressen wörtlich. Die Ausnahmeliste des Gates führt nur unvermeidbare Kernelversionen; eine Adresse in einem Bericht ist vermeidbar.
- Fix: Formulierung ohne Adressen (Loopback, Dokumentationsnetz nach RFC 5737), keine Ausnahme. Lehre: Der lokale Vollauf vor Push 2 lief vor dem Anlegen dieses Berichts; der Bericht war nicht im lokalen Gate.

### Befund C-29-03: Schemaschritt im Neuaufbau von Store upgrade 6

- Rot: `the schema mark is still 2 after the rebuild, so nothing was stamped and the rebuild did not go through`.
- Ursache, belegt: Zusicherung 1 verlangte einen Schritt nach oben. Das galt beim Start v1.2.0 (Index-`SCHEMA_VERSION` 1). v1.3.2 und der Kopf tragen beide 2 (`git grep SCHEMA_VERSION v1.3.2 HEAD -- backend/src`), ein reiner Sprachsprung hat keine Schemadrift zu beantworten. Die übrigen neun Zusicherungen hielten, die Sprachmarke ging korrekt auf `de,en,es`.
- Fix `7361b771`: Zusicherung 1 verlangt 2 vorher und 2 nachher; ein Test bindet die 2 an `findling.config.SCHEMA_VERSION`, damit eine künftige Schemaerhöhung das Gate rot macht. Dass der Neuaufbau gestempelt hat, belegt Zusicherung 2, denn nur `stamp_after_swap` schreibt den neuen Satz in ein bestehendes Verzeichnis.

### Push 3: 7130c4f0..7b8b4271

Freigabe des Owners, wörtlich: Auf die Frage "Darf ich die 2 Commits 7130c4f0..7b8b4271 (7361b771 Fix Store upgrade 6, 7b8b4271 Auditbericht) auf origin/main pushen?" antwortete der Owner "ok". Mit diesem Wort hat der Owner die geänderte Zusicherung aus C-29-03 gesehen und mitgetragen.

Kopf: `7b8b4271ec73ae4160dd68afdc2dcc130d40b6bc`, gepusht 12:00Z. **Alle ausgelösten Workflows grün, jeweils im ersten Attempt.**

| Workflow | Lauf | Attempt | Ergebnis |
|---|---|---|---|
| Python gates | 37460204981 | 1 | success, 4723 passed, 14 skipped |
| Multi-arch image | 37460204900 | 1 | success, amd64 und arm64 |
| Integration | 37460204996 | 1 | success |
| Resilience | 37460204909 | 1 | success |
| HaRP deploy | 37460204929 | 1 | success, alle vier Beine (stable33, stable34 amd64 und arm64, stable35) |
| PHP and store metadata gates | nicht ausgelöst | | Pfadfilter: seit 390360c3 hat sich kein Pfad des Filters geändert (nur `deploy-harp.yml`, ein Backend-Test und diese Doku); der PHP-Beleg bleibt Lauf 37452332197 auf 390360c3, `OK (589 tests, 2106 assertions)` |

Belege aus dem Upgrade-Bein stable34/amd64 (Job 112257592326), wörtlich:

- Store install 7: `content hit after 3 cron rounds, with nothing configured`; `none, which is what zero config means`.
- Store upgrade 2b: `sown: a picture and a sidecar, both failed(corrupt) under v1.3.2, and the seed word finds nothing`.
- Store upgrade 3: `three terms, one file each; the Spanish question with no hit at all; the languages mark de,en; the state is on record in upgrade-before.json`.
- Store upgrade 4: `the instance performed the app update: 1.3.2 to 1.4.0`.
- Store upgrade 5:
  - `unchanged  .marks.indexVersion = 1`
  - `the sidecar is skipped/system_file in state.db and in findling_file_state`
  - `the seed word finds exactly the file id 141, the picture 1.3.2 had booked as corrupt`
  - `the recheck mark was absent before the upgrade and reads done after it`
  - `the languages mark reads de,en before and after the upgrade, nothing was restamped`
  - `unchanged  embedding mark = multilingual-e5-small/int8/384/1024`
  - `the profile in force after the upgrade is economy`
  - `all eight assurances hold`
- Store upgrade 6: `the schema mark reads 2 before and after the rebuild, the schema of the running code`; `the question alemanes went from 0 to 1 hits across the rebuild, which is the Spanish chain and the field plan working together`; `all ten assurances hold`.

Damit sind die Fremdinstallation (Store install 0 bis 7) und die Upgrade-Strecke 1.3.2 auf 1.4.0 (Store upgrade 0 bis 6) mit der neuen Saat auf demselben Kopf Ende zu Ende grün.

### Offen

- Einzelnachweis der beiden Linux-SIGKILL-Fälle aus `test_slots_kill.py` (Merker aus 29-04): python.yml läuft mit `-q` ohne `-rs`. Der Lauf 37452332061 belegt die Suite insgesamt (4721 passed, 14 skipped), nicht die beiden Fälle namentlich. Lokal ist kein Linux verfügbar (Docker-Engine und WSL-Distribution laufen nicht). Plan 29-13 sieht keine Workflow-Änderung dafür vor; der Nachweis (`-rs` für diese Datei) geht an Plan 29-14.

## Phasenaudit Security, Bugs, Performance (Plan 29-14)

Stand: 06.10.2026, gelesen gegen den Baum von `1c5c9995` (Kopf nach Welle 10), Umfang `git diff 57b83358..1c5c9995` der Produktpfade: `backend/src/findling` (15 Dateien, darunter neu `extract/cfb.py` und `worker/recheck.py`), `php/lib`, `php/js`, `php/templates`, beide `appinfo/info.xml`, `backend/pyproject.toml`, `.github/workflows/deploy-harp.yml`, `scripts/ci/make_upgrade_seed_tiff.py`, `scripts/ops/aws_box.sh`. Dazu die Abweichungen aller dreizehn Executor-SUMMARYs (29-01 bis 29-13) als Prüfliste. Owner-Regel vom 15.08.2026: Befunde vor dem Phasenabschluss fixen; Owner-Regel vom 06.09.2026: Abgabe erst nach Abnahme dieser Härtung.

Schweregrade wie in `docs/audits/2026-09-phase-23/README.md`: CRIT (Datenverlust, Rechtedurchbruch, Codeausführung), HIGH (Ausfall oder Fehlurteil im Normalbetrieb), MEDIUM (Fehlverhalten unter präparierter Eingabe oder Randlage, begrenzt), LOW (Doku, Hygiene, bewusste Grenze).

### Urteil

**0 CRIT / 0 HIGH / 1 MEDIUM (behoben) / 4 LOW (2 behoben, 2 bewusst so).** Keine offene Zeile ab MEDIUM. Die Härtungsmatrix aus 29-04 ist erneut gefahren und vollständig grün, keine xfail-Marke, kein Befund H-29-NN.

### Befundtabelle

| ID | Schwere | Dimension | Beleg | Entscheid und Fix |
|---|---|---|---|---|
| F-29-01 | MEDIUM | Security (DoS) | `backend/src/findling/extract/image.py` `_normalise_sample_format`: das Budget zählte nur IFD-Einträge, nicht die SampleFormat-Werte dahinter. Viele IFDs können auf ein gemeinsames Wertefeld zeigen, jedes lief es erneut ab; eine präparierte Datei von n Bytes kostete rund n² Schritte statt des einen Durchgangs, den T-29-23b zusichert. Begrenzt nur durch den Extraktions-Timeout des Kinds, der Slot ist so lange belegt. | **Behoben.** Zweites Budget `values_left = length // 2` für die gelaufenen Werte, das IFD-Budget zählt Bytes (`6 + 12 * count` je IFD, damit auch Ketten leerer IFDs begrenzt sind). Test zuerst rot: `backend/tests/test_ocr.py::test_a_sample_format_array_shared_by_many_ifds_is_walked_at_most_once_over`; Positivkontrolle `test_a_shared_small_sample_format_array_of_a_multi_page_tiff_is_still_patched`. Alle SF0-, Float- und Saat-Tests grün. |
| F-29-02 | LOW | Bug (Doku) | `Version001400Date20261006000000.php` (unter `php/lib/Migration`), Klassenkommentar: nannte als Nachprüfung "every failed(corrupt) and skipped(unreadable) verdict". Die Nachprüfung (`worker/recheck.py`) wählt failed(corrupt), failed(out_of_memory), die drei neuen skipped-Codes und jeden Sidecar-Namen, nie unreadable. | **Behoben** (Kommentar korrigiert, PHP-Baumhash nachgezogen). Kein Verhalten betroffen. |
| F-29-03 | LOW | Bug (Randlage) | `backend/src/findling/nc/client.py:286`: ShortRead vergleicht mit der Größe, die `QueueService` bei der Ausgabe aus dem Dateicache liest (`php/lib/Service/QueueService.php:840`). Ist der Cache veraltet und größer als die Datei (externer Speicher außerhalb von Nextcloud geändert und noch nicht gescannt, oder eine falsche Klartextgröße bei serverseitiger Verschlüsselung), kommt jeder Download kurz an; die Datei endet nach den Wiederholungen der Queue als failed(repeatedly_stuck) statt indexiert. | **Bewusst so** für 1.4.0. Owner-Entscheid D-29-04: ein kurzer Download wird nie als Urteil über die Datei gelesen. Das Urteil ist auf der Statusseite sichtbar und keine Falschaussage über den Inhalt; sobald der Cache die Datei neu kennt, ändert sich das ETag und der Abgleich reiht sie neu ein. Feldbeobachtung in `deferred-items.md`. |
| F-29-04 | LOW | Bug (Doku) | `backend/src/findling/extract/cfb.py:98` fängt OSError, struct.error, UnicodeDecodeError, ValueError und `_Malformed`; der Modulkopf sagt "every read or structure error, of whatever kind". Gelesen: jede Ausnahme, die der Code erreichen kann, ist in der Liste (Einträge sind 128-Byte-Scheiben aus Sektoren von 512 oder 4096 Byte, ein IndexError ist nicht erreichbar). Eine unerwartete Klasse würde vom Kind als failed(corrupt) mit Klassenname gemeldet, also der Weg vor 1.4.0. | **Bewusst so.** Kein erreichbarer Pfad; eine Änderung am Paket nur für den Kommentar zieht den Baumhash ohne Nutzen. |
| F-29-05 | LOW | Performance | `backend/src/findling/worker/poller.py:930` und `worker/recheck.py:113`: die Nachprüfung läuft in der ersten Runde nach dem Upgrade bis zum Ende, vor dem Claim. Auf der meldenden Instanz sind das 8.512 Kandidaten (4.486 Sidecars, 2.199 corrupt, 1.827 out_of_memory am 03.10.), also 43 requeue-Aufrufe zu je 200; auf einer Instanz mit 100.000 Sidecars wären es 500 Aufrufe in einer Runde. | **Bewusst so.** Einmalig (RECHECK_MARK "done"), unterbrechbar (Cursor nach jedem bestätigten Band, ein Fehlschlag beendet die Runde und die nächste setzt fort), kein Download und kein Kind in dieser Phase. |

Keine Befunde in den Kategorien CRIT und HIGH. Geprüft und ohne Befund: die Liste unter "Security" bis "Performance" unten.

### Security

STRIDE gegen jede Mitigation der Pläne 29-01 bis 29-13, je mit Datei:Zeile oder Testname. "accept" heißt: im Plan bewusst angenommen, hier nachgelesen, dass die Annahme trägt.

| Threat | Mitigation | Beleg |
|---|---|---|
| T-29-01 | Kein neuer Code ohne Signal an eine 1.3.2-Companion | `backend/src/findling/nc/queue.py:144` (`_SKIPPED_FALLBACK`), `:160` (`_wire_reason`); `test_queue_client.py::test_without_the_signal_no_new_code_leaves_the_container` |
| T-29-02 | Nur exakt int 2 gilt als Signal | `nc/queue.py:172` (`_verdicts`, bool ausgeschlossen); `test_queue_client.py::test_any_other_verdicts_value_reads_as_none` |
| T-29-03 | Reason-Liste Python/PHP paritätisch, Katalog über 16 Dateien | `test_extract_errors.py::test_php_reason_list_matches_python`; `php/lib/Service/FileStateService.php:116`, `:167`; `test_admin_ui_contract.py` (Katalogtests), die drei Labels stehen in allen 16 Katalogen |
| T-29-04 | accept: statische Labels | `php/lib/Service/AdminViewService.php:497` ff., keine Platzhalter |
| T-29-05 | Pillow-Issue nur mit selbst erzeugter Repro | `scripts/ci/make_upgrade_seed_tiff.py`; `test_upgrade_seed_fixture.py::test_the_generator_writes_the_committed_bytes_again` |
| T-29-06, T-29-07 | Außentexte nur mit Owner-Wort, keine Box-Belege versprochen | Abnahme-Wortlaut in 29-02-SUMMARY; Store-Text nennt nur 730.2 (`test_store_metadata.py::test_the_measured_figure_stands_in_every_language_of_the_backend_half`) |
| T-29-08 | FINDLING_MAX_CELLS-Default gleich MAX_CELLS | `backend/appinfo/info.xml` (Variable FINDLING_MAX_CELLS, 200000); `test_info_xml_defaults.py` EXPECTED `"FINDLING_MAX_CELLS": str(config.MAX_CELLS)` |
| T-29-09 | Kein httpx2 | `backend/pyproject.toml` filterwarnings-Eintrag; `uv.lock` enthält weder httpx2 noch olefile (0 Treffer) |
| T-29-10 | Sweep löscht nur das eigene Schlüsselpaar | `scripts/ops/aws_box.sh` (`key_pair_id`, Fall `key-pair)`); `test_ops_scripts.py::test_the_aws_destroy_counts_the_kept_key_pair_by_its_id_and_not_as_a_leftover` |
| T-29-11 | Analyse-Log ohne Pfade | `nc/queue.py` requeue-Warnung: Anzahl, Klassenname, Status, Dauer |
| T-29-12, T-29-13 | Lückentests je Szenario, Matrix mit Beleg | `docs/audits/2026-10-phase-29/haertungsmatrix.md`, `backend/tests/test_launch_hardening.py` (6 Fälle) |
| T-29-14 | accept: `._x.pdf` nimmt nur die eigene Datei aus dem Index | Urteil skipped(system_file) sichtbar auf der Statusseite |
| T-29-15 | Keine Endlosschleife kurzer Downloads | `worker/poller.py:1958` (genau ein Wiederholversuch), `:1502` (kein unlock); `test_poller.py::test_a_download_that_stays_short_gets_no_verdict_and_the_pass_goes_on` |
| T-29-16 | ShortRead-Meldung nur mit file id und Bytezahlen | `nc/client.py:233`, `:287`; `test_gateway_client.py::test_a_download_that_ends_short_of_the_expected_size_raises_short_read` |
| T-29-17 | Basisname in Python, kein LIKE | `extract/errors.py:282` (`is_sidecar_name`), `worker/poller.py:1480`, `store/repo.py:416` (Rohleser ohne Muster); `test_poller.py::test_a_name_that_only_resembles_a_sidecar_is_indexed` |
| T-29-18, T-29-19 | Fehlerklasse nur in Form `[A-Za-z0-9_.]{1,200}`, beidseitig geprüft | `store/repo.py:510`, `:902`; `AdminViewService.php:305`, `:1515`; `test_store_repo.py::test_an_error_class_outside_the_allowed_shape_is_stored_as_nothing`, PHPUnit `AdminViewServiceTest.php`, Fall "a value outside the shape of a class name is refused"; Ausgabe in `php/js/admin.js:771` als Textknoten |
| T-29-20 | accept: Diagnose bleibt ADMIN | Route und occ unverändert, `api/diagnose.py:114` nur ein neues Feld |
| T-29-21 | Dekompressionsbombe | `extract/image.py:67` (MAX_IMAGE_PIXELS), `:325` (Header-Schätzung gegen RLIMIT_AS); `test_ocr.py::test_a_picture_over_the_free_address_space_is_out_of_memory` |
| T-29-22 | Shim nur fehlende Schlüssel | `extract/image.py:87`, `:121` (`setdefault`); `test_ocr.py::test_the_shim_changes_no_entry_pillow_ships`, `test_the_shim_adds_only_keys_pillow_does_not_ship`. Seiteneffekt nur bei Import des Extraktionsmoduls, das Hauptprozess-Lesen von Bildern gibt es nicht |
| T-29-23, T-29-23b | SF3 nie normalisiert; Puffer begrenzt; Patch linear | `extract/image.py:84` (32 MiB), `:383`; `test_ocr.py::test_a_float_tiff_is_an_unsupported_variant_and_not_corrupt`, `test_a_compressed_sample_format_zero_tiff_over_the_buffer_cap_is_an_honest_verdict`, `test_a_sample_format_patch_never_reaches_outside_the_buffer`; die Linearität erst nach F-29-01 |
| T-29-24 | detail nur Klassenname oder feste Kennung | `extract/errors.py:274`, `extract/image.py:164` (`_HEADER_ESTIMATE`) |
| T-29-25 | CFB-Zyklus, Sektorzahl, Offsets | `extract/cfb.py:76`, `:139` (Besucht-Menge), `:109` (`_read_at` gegen die Dateigröße), `:169` (nur Header-DIFAT); `test_cfb.py::test_a_fat_chain_with_a_cycle_ends_in_none`, `test_a_directory_longer_than_the_cap_ends_in_none`, `test_absurd_header_fields_end_in_none`, `test_a_truncated_compound_file_ends_in_none` |
| T-29-26 | Nur ganze Verzeichnisnamen | `extract/cfb.py:78`, `:79`; `test_cfb.py::test_only_whole_names_count_and_never_a_part_of_one`, `test_only_the_directory_is_read_and_never_the_whole_file` |
| T-29-27 | Sniff-Fehler ergibt None | `extract/cfb.py:98`; `test_cfb.py::test_a_missing_file_is_none_and_not_an_exception`, siehe F-29-04 |
| T-29-28 | stdlib only | `extract/cfb.py` importiert `struct` und `typing`; `uv.lock` ohne olefile |
| T-29-29 | Bänder unter der Listengrenze | `worker/recheck.py:113`; `test_recheck.py::test_the_band_is_the_one_of_the_reconcile` |
| T-29-30 | Kein Vollreindex, keine Neu-Einbettung | `test_recheck.py::test_the_index_generation_and_the_vector_marks_stay_untouched`; CI-Beleg Store upgrade 5 `unchanged  .marks.indexVersion = 1`, `unchanged  embedding mark` |
| T-29-31 | Lauf einmalig | `worker/recheck.py:129`; `test_recheck.py::test_after_done_the_run_never_hands_anything_over_again`, `test_a_new_process_resumes_at_the_cursor` |
| T-29-32 | accept: keine neue Route | bestehendes requeueAs, `php/lib/Db/QueueMapper.php:616` |
| T-29-33, T-29-34, T-29-35 | Vollindex-Term verdrahtet, Tausender-Rundung, Sparsam unverändert | `profile.py:416`, `:454`, `:468`; `test_profile.py::test_standard_loses_slots_on_a_tight_box_as_the_stock_grows`, `test_note_index_files_rounds_down_to_whole_thousands`, `test_economy_ignores_the_stock_value_for_value` |
| T-29-36 | Migration verwirft die gespeicherte Backend-Version | `Version001400Date20261006000000.php:79`, `:85`; PHPUnit `Version001400Date20261006000000Test.php`, grün in Lauf 37452332197 |
| T-29-37, T-29-39 | Upgrade-Beweis exakt, Migrationszweig erreicht | `.github/workflows/deploy-harp.yml:4140` (Store upgrade 4), `:4485`, `:4846`; Lauf 37460204929 grün, alle vier Beine |
| T-29-38 | Versionen im Gleichschritt | `test_lockstep_versions.py::test_the_two_halves_and_the_image_tag_carry_the_same_version` (1.4.0 dreimal) |
| T-29-40 | Fixture selbst erzeugt | `scripts/ci/make_upgrade_seed_tiff.py`, `test_upgrade_seed_fixture.py::test_the_generator_writes_the_committed_bytes_again` |
| T-29-41, T-29-42, T-29-43 | Store-Text wortgleich, eine Messzahl, Katalog | `test_store_metadata.py::test_the_three_files_of_the_store_texts_exist`, `test_no_store_text_carries_a_dash_or_an_emoji`, `RESIDENT_FIGURE = "730.2"`; `test_admin_ui_contract.py` |
| T-29-44, T-29-45, T-29-46, T-29-47 | Push-Wort, Autor, keine Abschwächung, keine Adressen | Abschnitt "CI-Beweis" oben (drei Pushes je mit eigenem Wort, Autor- und Mustersuche vor Push 1); C-29-03 als geänderte, nicht abgeschwächte Zusicherung mit Owner-Wort |

Gezielte Prüfungen ohne Befund:

- **CFB-Leser** (`extract/cfb.py`): Zyklus über die Besucht-Menge, Kettenlänge höchstens 1024 Sektoren, jeder Sektor gegen die Dateigröße geprüft bevor er gelesen wird, FAT-Zugriffe nur über die 109 Header-DIFAT-Einträge (FREESECT dort endet in `_Malformed`), FAT-Cache höchstens 109 Tabellen. Namen werden nur aus Stream-Einträgen und nur mit gültiger Länge dekodiert.
- **Shim-Seiteneffekt**: `OPEN_INFO` bekommt nur Schlüssel per `setdefault`; Float (SampleFormat 3) wird nie abgebildet.
- **file_errors**: Wert wird vor der Transaktion geformt geprüft und außerhalb der Form verworfen statt gekürzt; `give_up` und `reset_for_reindex` räumen mit; die Diagnose zeigt die Klasse nur, wenn Karte und Container beide failed sagen (`AdminViewService.php:1082`).
- **requeue-Bänder** der Nachprüfung: 200 je Aufruf, Cursor nur nach `ok`.
- **Draht-Rückfall K6**: ein fehlgeschlagener Profil-Read setzt das Signal zurück (29-01 Abweichung 2), der Rückfall gilt je Liste mit einem Code, den 1.3.2 unter diesem Zustand speichert.
- **Logzeilen**: alle neuen `LOGGER`-Aufrufe im Diff (poller.py, recheck.py) tragen Zahlen und Klassennamen, keinen Pfad und keinen Ausnahmetext.
- **Secrets im Diff**: Suche nach Passwort-, Token- und Schlüsselmustern über `backend/src` und `php/lib` des Diffs: nur Prosa ("password protected").

### Bugs

- **Sechs #18-Klassen**: Sidecar (`._`, `~$`) vor dem ersten Byte und aus Index, Vektoren und Prefilter genommen (`_drop_a_sidecar`); Negativkontrollen `.hidden`, `a._b`, `_x` indexiert (`test_poller.py::test_a_name_that_only_resembles_a_sidecar_is_indexed`, `test_extract_errors.py::test_a_sidecar_name_starts_with_the_apple_double_or_the_lock_stub_marker`). OLE unter OOXML-Namen: verschlüsselt vor legacy. TIFF-Varianten: LA-Shim, SF0-Patch, SF3 ehrlich. Große JPEGs: Draft vor der Schätzung. Kurzer Download: ShortRead. Fehlerklasse: detail.
- **Sidecar in der OCR-Spur aus einer 1.3-Queue**: die Nachprüfung reicht jede Sidecar-Zeile als content zurück, und `QueueMapper::requeueAs` schaltet die Art einer vorhandenen Zeile um (`php/lib/Db/QueueMapper.php:632`); der Endzustand ist skipped(system_file). Kein Befund.
- **ShortRead bei Größe 0**: `expected > 0` als Bedingung (`nc/client.py:286`), eine requeueAs-Zeile mit Größe 0 wird nie geprüft. Datei gewachsen: kein Befund, die Bytegrenze bleibt die Obergrenze. Veralteter Cache: F-29-03.
- **Nachprüfung bei Neustart**: Cursor in state.db, `test_recheck.py::test_a_new_process_resumes_at_the_cursor`. **Companion ohne Signal**: Nachprüfung startet nicht, `test_poller.py::test_without_the_signal_the_re_check_never_starts`.
- **Pickle des detail-Felds**: Feld zuletzt und mit Default, `compare=False`; Pickle-Test aus 29-06 prüft detail ausdrücklich.
- **Mehrseiten-TIFF mit Orientierung**: Rotation in place, jeder Frame wird beim seek neu dekodiert; `test_every_frame_of_a_rotated_multi_frame_tiff_is_upright` pinnt die Gleichheit mit dem alten Kopierweg. Die Pillow-Beobachtung zur TIFF-Orientierung ist vorbestehend und steht in `deferred-items.md`.
- **ocr_failed außerhalb der Nachprüfung** (Research Pattern 7, Open Question 4): `extract/image.py` mappt den Tod der Engine am Adressraum auf ocr_failed. Kein Fix dieses Release berührt die Engine, und der draft-Pfad senkt das Bild, das die Engine bekommt, nicht (sie bekommt ohnehin höchstens 3500 px Kante). Ein zweiter Lauf kostete OCR-Zeit für dasselbe Urteil. Ausgeschlossen per Test `test_recheck.py::test_ocr_failed_is_never_selected`.
- **Tombstone und file_errors**: ein gelöschter Datensatz behält seine Klasse bis zum nächsten Reindex; sie beschreibt das letzte Urteil dieser Datei und erscheint nur neben failed. Kein Befund.

### Performance

| Pfad | Kosten | Beleg |
|---|---|---|
| Sidecar-Skip | kein Download, kein Kind; zwei idempotente Schreibvorgänge (Löschterm im Index, ACL-Zeilen), Commit im gemeinsamen Schritt 2 | `worker/poller.py:1853` |
| Nachprüfung | einmalig, 43 requeue-Aufrufe bei 8.512 Kandidaten der meldenden Instanz; state.db in Blöcken zu 2000 Zeilen über den Primärschlüssel | `worker/recheck.py`, F-29-05 |
| CFB-Sniff | 512 Byte Header, je Verzeichnissektor ein Sektor (verschlüsselte Pakete: ein bis zwei), FAT-Sektoren nur bei Kettenwechsel und gecacht; Obergrenze 4 MiB Verzeichnis | `extract/cfb.py`, `test_cfb.py::test_only_the_directory_is_read_and_never_the_whole_file` |
| draft-Pfad | 8192 x 5464 mit Orientierung 6: Spitze CMYK 467 auf 131 MiB, RGB 466 auf 48 MiB (Research, 29-07) | `extract/image.py:271` |
| SF0-Patch | eine Kopie bis 32 MiB, kurz zwei (64 MiB); nach F-29-01 linear in der Dateigröße | `extract/image.py:84`, `:420` |
| note_index_files | ein COUNT über `files_state` je Pass mit Urteilen; Neuberechnung des Profils nur beim Wechsel der Tausenderstufe (1000 Dateien = 6 MiB, eine OCR-Slot-Einheit 250 MiB) | `worker/poller.py:2240`, `profile.py:454` |
| ShortRead | höchstens ein zusätzlicher Download je kurz angekommener Datei und Pass | `worker/poller.py:1958` |

### Matrix-Lauf

Die Matrix aus 29-04 ist am 06.10.2026 erneut gefahren, Ergebnis in `haertungsmatrix.md` Abschnitt "Erneuter Lauf (Plan 29-14)": 37 passed, 2 skipped (die beiden Linux-SIGKILL-Fälle, lokal Windows). Keine xfail-Marke in `test_launch_hardening.py`.

### SIGKILL-Namensbeleg

`.github/workflows/python.yml` hat einen eigenen Schritt "The SIGKILL cases by name (test_slots_kill.py)" mit `pytest -v -rs`, und der Gesamtlauf läuft mit `-rs`. Beleg: Lauf 37467788135 (Python gates auf 99326ae2, 06.10.2026) zeigt beide Fälle namentlich PASSED: `test_a_killed_main_process_mid_pass_loses_no_row_and_indexes_once` und `test_a_killed_child_mid_pass_is_retried_alone_and_indexed_once`.

## Owner-Abnahme der Haertung (06.10.2026)

Die gemeinsame Playwright-Runde lief am 06.10.2026 auf der Dev-Instanz (App und
Backend beide 1.4.0, Backend als Host-Prozess aus den Quellen). Alle fuenf
Pruefpunkte sind mit echten Testdateien belegt: die Zeile "System- oder
Hilfsdatei" (zwei hochgeladene Begleitdateien, Abhilfetext und Beispielpfade,
deutsch und englisch), "Old Office format under a new name" (CFB-Datei mit
Workbook-Stream unter .xlsx-Namen), "Image variant that cannot be read"
(SampleFormat-3-TIFF), die Zeile "Error class" auf der Diagnosekarte
(zipfile.BadZipFile an einer kaputten .xlsx) und dieselbe Zeile in
occ findling:diagnose (mit Wert und leer). Der Versionswaechter (K6) wurde
vorher live gesehen: mit Backend 1.3.0 zeigte die Karte den Banner und die
Suche blieb bewusst leer, nach dem Angleich verschwand er.

Owner-Signal woertlich: "abgenommen du kannst weiter" (06.10.2026, auf die
Vorlage mit Audit-Stand 0 CRIT / 0 HIGH, der Playwright-Tabelle, den
deferred-items und der Push-Frage zu den Audit-Commits). Damit sind die
Haertung abgenommen, die deferred-items bestaetigt und der beschriebene Push
samt Abschluss-Doku dieses Plans freigegeben.

## Die Belegkette der Abgabe v1.4.0

Geschrieben am 06.10.2026 in Plan 29-15, nach dem Tag-Push. Jede Zeile trägt
eine Zahl, eine Laufnummer oder einen Wortlaut; keine ist geschätzt oder aus
einem früheren Release übernommen. Die Zeilen 6 und folgende (Einreichung,
HTTP-Codes, Gegenprobe der App-Seiten) schreibt Plan 29-16.

Owner-Wort zum Tag, wörtlich: Frage "Gibst du das Wort fuer Tag v1.4.0 auf
99326ae2?" (nach komplettem CI-Grün auf 99326ae2), Antwort "go" (06.10.2026).

| Nr. | Was | Beleg |
|---|---|---|
| 1 | **Tag** | `v1.4.0`, annotiert ("Findling 1.4.0", Tagger street1983nk, Tag-Objekt `0959338252e653b3a64c23e3cfeb031490778c39`), auf `99326ae2667ddc243456f7787f1010efd500e357`, gelesen mit `git rev-list -n 1 v1.4.0` und gegen `git ls-remote origin 'refs/tags/v1.4.0^{}'` gegengeprüft. Nur das Tag wurde gepusht, `main` nicht |
| 2 | **Release** | Lauf **37470623070** ("Release archives for the app store"), success, genau vier Anhänge. Im Protokoll: `appinfo/signature.json was written and is not empty`, zweimal `the release signature is 684 base64 characters` und zweimal `Verified OK` aus der Gegenprobe der Signatur gegen das Zertifikat |
| 3 | **Anhänge** | `findling.tar.gz` **529.651 B**, `findling.tar.gz.sig` **684 B**, `findling_backend.tar.gz` **33.663 B**, `findling_backend.tar.gz.sig` **684 B**. Alle unter der Store-Grenze von 20.971.520 B; die größere Hälfte liegt bei 2,5 Prozent davon (v1.3.2: 371.641 B und 32.427 B). Unabhängig nachgeprüft: Anhänge per `gh release download` geholt, beide Zertifikate frisch aus `nextcloud/app-certificate-requests` (`subject=CN=findling`, `subject=CN=findling_backend`), `openssl dgst -sha512 -verify` lieferte lokal `findling: Verified OK` und `findling_backend: Verified OK`; in den Archiven `<version>1.4.0</version>` beidseitig und `<image-tag>1.4.0</image-tag>` |
| 4 | **Container-Abbild** | `docker manifest inspect ghcr.io/street1983nk/findling_backend:1.4.0` mit leerem `DOCKER_CONFIG`, also ohne Login: `application/vnd.oci.image.index.v1+json` mit `linux/amd64` und `linux/arm64`, dazu die zwei Herkunftsbelege als `unknown/unknown`. Abgefragt **vor** der Einreichung |
| 5 | **Release-Notiz** | `gh release edit v1.4.0 --notes-file` mit der abgenommenen englischen Faktenliste aus `docs/store-listing.md`, "Entwurf 1.4.0" Teil 6, als Kopf vor den generierten Notizen. Einzige Abweichung ist der dort vorab vereinbarte Zusatz "and on the admin page" in der Zeile zur Fehlerklasse, weil 29-12 die Zeile "Error class" auf der Verwaltungskarte gebaut hat. Beleg `gh release view v1.4.0 --json body --jq .body \| head -5`: "Findling 1.4.0. Both apps need to be on 1.4.0." gefolgt von den Zeilen zu Performance profiles, Search model und Reading and OCR processes; der Dank an budachst und #18 stehen im Text |

### Die sieben Tag-Läufe, alle success

Release **37470623070**, PHP and store metadata gates **37470623202**,
Multi-arch image **37470623060**, HaRP deploy **37470623144**, Python gates
**37470623033**, Integration **37470623360**, Resilience **37470623071**. Kein
Lauf wurde wiederholt, der Tag ist nicht gewandert.
