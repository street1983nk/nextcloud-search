---
phase: 29
slug: h-rtung-und-store-einreichung-1-4-0
status: verified
threats_total: 65
threats_closed: 65
threats_open: 0
asvs_level: 1
block_on: high
created: 2026-10-06
audited_head: 62972497
tag: v1.4.0 (99326ae2)
---

# Phase 29: Security

> Sicherheitsvertrag der Phase: Threat-Register, akzeptierte Risiken, Audit-Trail.
> Erstellt aus den Artefakten (State B): 16 PLAN-`<threat_model>`-Blöcke, 16 SUMMARYs,
> Phasenaudit `docs/audits/2026-10-phase-29/README.md` (Plan 29-14), `deferred-items.md`.
> Jeder Beleg wurde am HEAD `62972497` (Tag v1.4.0 = `99326ae2` plus vier lokale Doku-Commits) nachgeprüft, nicht aus dem Bericht übernommen.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Nutzerdatei zu Extraktions-Kind | Beliebige Dateien aus Nextcloud (CFB/OLE unter OOXML-Namen, TIFF mit SampleFormat 0/3, große JPEGs, Sidecars) werden im Kind unter RLIMIT_AS gelesen | Angreiferkontrollierte Bytes, Dateinamen |
| Gateway-Download zu Container | Download über Nextcloud/Proxy, kann abgeschnitten ankommen (ShortRead) | Dateiinhalt, erwartete Größe aus dem Dateicache |
| Container zu Companion (PHP) | acknowledge/requeue/Diagnose; neue Reason-Codes nur bei Signal `verdicts == 2`, Fehlerklasse als Text | Reason-Codes, file ids, Klassennamen |
| Companion zu Admin-UI / occ | Labels, Fehlerklasse, Diagnosekarte, nur ADMIN | Statische Texte, geprüfte Klassennamen |
| Repo zu Öffentlichkeit | Push, Tag, Release, Store-Einreichung, Issue-Posts | Commits, Doku, Store-Token (Secret), Signaturschlüssel |

---

## Threat Register

Status-Spalte: `closed` = Mitigation am HEAD per grep/Code-Lektüre und, wo genannt, per Testlauf belegt. Alle zitierten pytest-Knoten wurden am 06.10.2026 gefahren: **389 passed** (`PYTHONUTF8=1 uv run pytest` über die einzeln benannten Tests sowie `test_cfb.py`, `test_recheck.py`, `test_lockstep_versions.py`, `test_store_metadata.py`, `test_admin_ui_contract.py`, `test_info_xml_defaults.py`, `test_public_artifacts.py`, `test_launch_hardening.py`, `test_upgrade_seed_steps.py`). PHPUnit lokal nicht gefahren; Beleg ist der grüne Tag-Lauf PHP gates 37470623202.

| Threat ID | Category | Component | Disposition | Mitigation / Beleg am HEAD | Status |
|-----------|----------|-----------|-------------|----------------------------|--------|
| T-29-01 | DoS | acknowledge gegen Companion 1.3.2 | mitigate | `nc/queue.py:144` `_SKIPPED_FALLBACK`, `:160` `_wire_reason`, `:578` Anwendung je skipped-Liste; Test `test_queue_client.py::test_without_the_signal_no_new_code_leaves_the_container` (passed) | closed |
| T-29-02 | Tampering | manipuliertes `verdicts` | mitigate | `nc/queue.py:172-178` `_verdicts`, bool und Nicht-int ausgeschlossen; `test_any_other_verdicts_value_reads_as_none` (passed) | closed |
| T-29-03 | Tampering | Reason-Liste Python/PHP | mitigate | `test_extract_errors.py::test_php_reason_list_matches_python` (passed), `test_admin_ui_contract.py` (passed) | closed |
| T-29-04 | Info Disclosure | neue Labels/Abhilfen | accept | AR-29-01 | closed |
| T-29-05 | Info Disclosure | Pillow-Issue, Issue-Antworten | mitigate | Repro selbst erzeugt (`scripts/ci/make_upgrade_seed_tiff.py`, `test_the_generator_writes_the_committed_bytes_again` passed); gepostetes Pillow-Issue #10139 per API gelesen: 0 Treffer für budachst, Mount-/Webroot-Pfade, groupfolder, IPv4 | closed |
| T-29-06 | Repudiation | Außentext ohne Owner-Freigabe | mitigate | 29-02-SUMMARY "Die Abnahme (wörtlich)": Owner "ok abgenommen" (06.10.2026) | closed |
| T-29-07 | Spoofing | Store-Text verspricht Box-Belege | mitigate | D-29-11 ausgenommen (`deferred-items.md`), eine Messzahl `RESIDENT_FIGURE = "730.2"` (`test_store_metadata.py:356`), `test_every_store_description_carries_exactly_one_measured_figure` (passed) | closed |
| T-29-08 | Tampering | FINDLING_MAX_CELLS-Default | mitigate | `backend/appinfo/info.xml:563-566` Default 200000 = `config.py:245` `MAX_CELLS = 200_000`; `test_info_xml_defaults.py` (passed) | closed |
| T-29-09 | Tampering | Testabhängigkeit httpx2 | mitigate | `backend/pyproject.toml` nur gezielter filterwarnings-Eintrag; `backend/uv.lock` 0 Treffer httpx2/olefile, im Phasendiff unverändert | closed |
| T-29-10 | DoS | AWS-Sweep löscht Fremdes | mitigate | `scripts/ops/aws_box.sh:1284` (`key_pair_id` nach `SSH_KEY_NAME`), `:1294`, `:1449`; `test_ops_scripts.py::test_the_aws_destroy_counts_the_kept_key_pair_by_its_id_and_not_as_a_leftover` (passed) | closed |
| T-29-11 | Info Disclosure | Analyse-Log | mitigate | `nc/queue.py:729-735` requeue-Warnung: Anzahl, Klassenname, Status, Dauer, kein Pfad | closed |
| T-29-12 | DoS | Parallelpfade unter OOM/Kill | mitigate | `test_launch_hardening.py` (passed); SIGKILL-Fälle namentlich in `.github/workflows/python.yml:181-182`, Lauf 37467788135 | closed |
| T-29-13 | Repudiation | Härtung ohne Beleg | mitigate | `docs/audits/2026-10-phase-29/haertungsmatrix.md`, je Zeile Datei::Test | closed |
| T-29-14 | Tampering | `._x.pdf` aus Index nehmen | accept | AR-29-02 | closed |
| T-29-15 | DoS | Endlosschleife kurzer Downloads | mitigate | `worker/poller.py:1958ff` genau ein Wiederholversuch, `:1383` Zeile ohne Urteil zurück; `test_a_download_that_stays_short_gets_no_verdict_and_the_pass_goes_on` (passed) | closed |
| T-29-16 | Info Disclosure | ShortRead-Meldung | mitigate | `nc/client.py:287` Meldung nur `file id`, Bytezahlen; `test_a_download_that_ends_short_of_the_expected_size_raises_short_read` (passed) | closed |
| T-29-17 | Tampering | Basisname per LIKE | mitigate | `extract/errors.py:282-296` `startswith(("._", "~$"))` in Python; Aufrufe `poller.py:1480`, `recheck.py`; `test_a_name_that_only_resembles_a_sidecar_is_indexed` (passed) | closed |
| T-29-18 | Info Disclosure | detail/file_errors mit Pfad | mitigate | `store/repo.py:510` `[A-Za-z0-9_.]{1,200}`, `:902` fullmatch sonst None; PHP `AdminViewService.php:305`, `:1515-1518`; `admin.js:771` Ausgabe als Text; `test_an_error_class_outside_the_allowed_shape_is_stored_as_nothing` (passed), PHPUnit `everythingThatIsNotAnErrorClass` | closed |
| T-29-19 | Tampering | sonderbarer Klassenname | mitigate | wie T-29-18, Prüfung vor der Transaktion (`repo.py:902`) | closed |
| T-29-20 | EoP | Diagnose für Nicht-Admins | accept | AR-29-03 | closed |
| T-29-21 | DoS | Dekompressionsbombe | mitigate | `extract/image.py:67` `MAX_IMAGE_PIXELS`, `:337-339` Header-Schätzung mit `_WORKING_COPIES`; `test_a_picture_over_the_free_address_space_is_out_of_memory` (passed) | closed |
| T-29-22 | Tampering | Shim ändert Pillow-Zustand | mitigate | `extract/image.py:121` nur `setdefault`; `test_the_shim_changes_no_entry_pillow_ships`, `test_the_shim_adds_only_keys_pillow_does_not_ship` (passed) | closed |
| T-29-23 | Tampering | SF3 als Integer | mitigate | `extract/image.py:471-474` patcht nur exakt 0; `test_a_float_tiff_is_an_unsupported_variant_and_not_corrupt` (passed) | closed |
| T-29-23b | DoS | In-Memory-Kopie SF0-Patch | mitigate | Gebaut nur nach Prüfschritt (`image.py:207` hinter `_has_compressed_sample_format_zero` `:374`); `_SF0_PATCH_MAX_BYTES = 32 MiB` (`:84`), Abbruch darüber `:398-399`; Offsets gegen Puffer `:455-470`, IFD-Zyklus `seen`, Byte-Budget `budget`, Werte-Budget `values_left` (F-29-01); Tests `..._over_the_buffer_cap_is_an_honest_verdict`, `..._never_reaches_outside_the_buffer`, `..._shared_by_many_ifds_is_walked_at_most_once_over`, Positivkontrolle `..._multi_page_tiff_is_still_patched` (alle passed) | closed |
| T-29-24 | Info Disclosure | detail mit Dateiinhalt | mitigate | `extract/image.py:164` feste Kennung `_HEADER_ESTIMATE`, sonst Klassenname | closed |
| T-29-25 | DoS | CFB FAT-Zyklus / Sektorzahl | mitigate | `extract/cfb.py:76` `_MAX_DIRECTORY_SECTORS = 1024`, `:139-143` Besucht-Menge, `:109-116` `_read_at` gegen Dateigröße, `:160-171` Sektorobergrenze und nur Header-DIFAT (109), `:181-189` Namenslänge; 7 benannte `test_cfb.py`-Tests (passed) | closed |
| T-29-26 | Tampering | Teilstring im Inhalt | mitigate | `cfb.py:101-104` Mengenschnitt ganzer Verzeichnisnamen, nur Stream-Einträge; `test_only_whole_names_count_and_never_a_part_of_one` (passed) | closed |
| T-29-27 | DoS | Ausnahme im Sniff | mitigate | `cfb.py:93-99` fängt OSError, struct.error, UnicodeDecodeError, ValueError, `_Malformed` und gibt None; Restklassen siehe F-29-04 / AR-29-07 | closed |
| T-29-28 | Tampering | Abhängigkeit olefile | mitigate | `cfb.py:41-46` nur `struct`, `typing`, eigenes Modul; `uv.lock` ohne olefile | closed |
| T-29-29 | DoS | requeue-Liste über 256 | mitigate | `worker/reconcile.py:148` `REQUEUE_BAND = 200`, importiert in `recheck.py:48`, Bänder `:112-113`; `test_the_band_is_the_one_of_the_reconcile` (passed) | closed |
| T-29-30 | DoS | Vollreindex/Neu-Einbettung | mitigate | `test_the_index_generation_and_the_vector_marks_stay_untouched` (passed); CI Store upgrade 5 "unchanged .marks.indexVersion", "unchanged embedding mark" (Lauf 37460204929, Tag-Lauf 37470623144) | closed |
| T-29-31 | DoS | Lauf wiederholt sich | mitigate | `recheck.py:100-101` Abbruch bei `done`, Cursor nur nach `ok` (`:116-125`), `:129` Marke done; `test_after_done_the_run_never_hands_anything_over_again`, `test_a_new_process_resumes_at_the_cursor` (passed); Start nur mit Signal `poller.py:930`, `test_without_the_signal_the_re_check_never_starts` (passed) | closed |
| T-29-32 | EoP | neue Route | accept | AR-29-04 | closed |
| T-29-33 | DoS | Slotzahl ignoriert Bestand | mitigate | `profile.py:195-243` `index_files` im Speicherterm; `test_standard_loses_slots_on_a_tight_box_as_the_stock_grows` (passed) | closed |
| T-29-34 | DoS | Snapshot flattert | mitigate | `profile.py:467-469` Tausender-Rundung, Abbruch bei gleichem Wert; `test_note_index_files_rounds_down_to_whole_thousands` (passed) | closed |
| T-29-35 | Tampering | Sparsam wandert | mitigate | `test_economy_ignores_the_stock_value_for_value` (passed) | closed |
| T-29-36 | DoS | Suche leer nach Update | mitigate | `php/lib/Migration/Version001400Date20261006000000.php:85` `deleteKey(... KEY_BACKEND_VERSION)`; PHPUnit `Version001400Date20261006000000Test.php` (Tag-Lauf 37470623202 grün) | closed |
| T-29-37 | Repudiation | Upgrade-Beweis abgeschwächt | mitigate | `deploy-harp.yml:4140ff` Store upgrade 4 bis 6, exakte Zusicherungen; C-29-01/C-29-03 als geänderte, nicht gelockerte Zusicherung (mit Test `test_upgrade_seed_steps.py`, passed, bindet an `SCHEMA_VERSION`) | closed |
| T-29-38 | Tampering | Versionen K6 | mitigate | `php/appinfo/info.xml:158`, `backend/appinfo/info.xml:172`, `:266` je 1.4.0; `test_lockstep_versions.py` (passed); `release.yml:179-191` Tag gegen beide | closed |
| T-29-39 | DoS | Migrationszweig nie erreicht | mitigate | `deploy-harp.yml:4140-4200` ERROR_UP_TO_DATE fail-closed; CI "the instance performed the app update: 1.3.2 to 1.4.0" | closed |
| T-29-40 | Info Disclosure | Fixture mit Fremddaten | mitigate | `scripts/ci/make_upgrade_seed_tiff.py`, Reproduktionstest (passed) | closed |
| T-29-41 | Repudiation | Store-Text weicht ab | mitigate | `test_store_metadata.py:417ff`, `:954ff` (D-24-04-Satz genau einmal), `:1576ff` (Owner-Wortlaut) (passed) | closed |
| T-29-42 | Spoofing | falsche Messzahl | mitigate | `test_store_metadata.py:889` `scan_one_measured_figure`, `:356` `RESIDENT_FIGURE = "730.2"` (passed) | closed |
| T-29-43 | Tampering | l10n-Drift | mitigate | `test_admin_ui_contract.py` (passed) | closed |
| T-29-44 | Repudiation | Push ohne Owner-Wort | mitigate | Pushes 1 bis 3 mit Frage und Antwort wörtlich (29-13-SUMMARY, Bericht "CI-Beweis"); Push 4 und 5 siehe Nachweiskette unten, Beobachtung O-29-01/O-29-02 | closed |
| T-29-45 | Spoofing | falscher Autor / Trailer | mitigate | Nachgeprüft `git log 57b83358..HEAD`: 100 Commits, alle `street1983nk <k.cherif@outlook.de>`, 0 Treffer Co-Authored-By/Claude/Anthropic | closed |
| T-29-46 | Tampering | Zusicherung abgeschwächt | mitigate | C-29-02 ohne Ausnahme im Gate gelöst; C-29-03 Zusicherung geändert (2 vorher und nachher, an `SCHEMA_VERSION` gebunden), Owner-Wort zu Push 3 | closed |
| T-29-47 | Info Disclosure | Box-IPs/Secrets in Commits | mitigate | Nachgeprüft `git log -p 57b83358..HEAD`: IPv4 nur `127.0.0.1` und `192.0.2.1` (RFC 5737), Token-/Key-Muster nur im Plantext; Gate `test_public_artifacts.py::test_no_file_under_docs_carries_a_finding_outside_the_exception_list` (passed) | closed |
| T-29-48 | Repudiation | Abgabe ohne Härtungsabnahme | mitigate | 29-14-SUMMARY und Bericht: Owner "abgenommen du kannst weiter" (06.10.2026), vor Tag und Einreichung | closed |
| T-29-49 | EoP | übersehener HIGH-Befund | mitigate | Phasenaudit 0 CRIT / 0 HIGH, jede Mitigation T-29-01..47 mit Datei:Zeile; hier am HEAD nachgeprüft (Zeilen stimmen nach F-29-01 weiter) | closed |
| T-29-50 | Repudiation | Fix-Push ohne Owner-Wort | mitigate | Push 2 und 3 je eigenes Wort "ok"; Push 4 (enthält Fix 64992430) unter "abgenommen du kannst weiter", siehe O-29-01 | closed |
| T-29-51 | Spoofing | Paket ohne Signatur | mitigate | `release.yml` Phasendiff nur Kommentar; Lauf 37470623070 zweimal "Verified OK", lokal gegen Upstream-Zertifikate nachgeprüft (Bericht Zeile 2/3) | closed |
| T-29-52 | Tampering | Abbild ohne arm64 | mitigate | Bericht Zeile 4: anonymer Manifestindex linux/amd64 und linux/arm64, vor der Einreichung | closed |
| T-29-53 | Repudiation | Tag-Push ohne Wort / Tag wandert | mitigate | 29-15-SUMMARY: Frage und Antwort "go" wörtlich; `git tag --points-at 99326ae2` = v1.4.0, Remote `^{}` identisch, kein Lauf wiederholt | closed |
| T-29-54 | Info Disclosure | Store-Token in Datei/Log | mitigate | `store-submit.yml:80,114,139` Token nur aus `secrets`, nur im Header; Phasendiff von `store-submit.yml` leer; `:167` Schlüssel-Cleanup; Antwortkörper in `RUNNER_TEMP`, Log nur HTTP-Code | closed |
| T-29-55 | Spoofing | Post/Schließen ohne Freigabe | mitigate | 29-16-SUMMARY "go" wörtlich auf eine Frage, die die sechs Posts nannte; per `gh` geprüft: #15, #18, #19, #21, #22 alle OPEN | closed |
| T-29-56 | Info Disclosure | Pillow-Issue mit Fremddaten | mitigate | wie T-29-05, Issue #10139 Autor street1983nk, 0 Fremddaten-Treffer | closed |
| T-29-57 | Repudiation | Abgabe ohne Belegkette | mitigate | Bericht "Die Belegkette der Abgabe v1.4.0": acht Zeilen mit Zahl/Laufnummer, Läufe 37473805519 (2x HTTP 201) | closed |
| T-29-58 | Repudiation | Doku-Push ohne Wort | mitigate | Push 5 `99326ae2..dd252a82` unter "go", dessen Frage den Doku-Push ausdrücklich nannte; Abweichung (kein zweiter Checkpoint) in 29-16-SUMMARY dokumentiert, siehe O-29-02 | closed |
| T-29-SC | Tampering | pip installs | accept | AR-29-05; `backend/uv.lock` im Phasendiff unverändert | closed |
| F-29-01 | DoS (MEDIUM) | SF0-Patch quadratisch | mitigate (fixed) | `image.py:447` `values_left`, `:466-470`; Fix 64992430, Test zuerst rot, jetzt passed | closed |
| F-29-02 | Doku (LOW) | Migrationskommentar | mitigate (fixed) | Kommentar korrigiert (64992430) | closed |
| F-29-03 | Randlage (LOW) | ShortRead gegen veraltete Cachegröße | accept | AR-29-06 | closed |
| F-29-04 | Doku (LOW) | CFB-Ausnahmeliste vs. Modulkopf | accept | AR-29-07 | closed |
| F-29-05 | Performance (LOW) | Nachprüfung in einer Runde | accept | AR-29-08 | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Nachweiskette der Owner-Worte (Push-Disziplin)

| Vorgang | Bereich (per `git reflog origin/main` geprüft) | Owner-Wort wörtlich | Fundstelle |
|---------|-----------------------------------------------|---------------------|-----------|
| Abnahme Außentexte | | "ok abgenommen" | 29-02-SUMMARY |
| Push 1 | 57b83358..390360c3 | "ok" auf "Bestaetigst du den Push von main (57b83358..390360c3) nach origin?" | 29-13-SUMMARY, Bericht |
| Push 2 | 390360c3..7130c4f0 | "ok" auf "Darf ich die 2 Commits 390360c3..7130c4f0 ... pushen?" | 29-13-SUMMARY, Bericht |
| Push 3 | 7130c4f0..7b8b4271 | "ok" auf "Darf ich die 2 Commits 7130c4f0..7b8b4271 ... pushen?" | 29-13-SUMMARY, Bericht |
| Härtungsabnahme + Push 4 | 7b8b4271..99326ae2 | "abgenommen du kannst weiter" | 29-14-SUMMARY, Bericht |
| Tag v1.4.0 | refs/tags/v1.4.0 auf 99326ae2 | "go" auf "Gibst du das Wort fuer Tag v1.4.0 auf 99326ae2?" | 29-15-SUMMARY, Bericht |
| Einreichung, Posts, Push 5 | 99326ae2..dd252a82 | "go" auf "Gibst du die Freigabe fuer die Einreichung und das Posten der abgenommenen Antworten?" (Vorlage nannte Doku-Push) | 29-16-SUMMARY |
| lokal, nicht gepusht | dd252a82..62972497 (a9812cfd, e0fe73c1, 61e7294c, 62972497) und diese Datei | noch keines | braucht eigenes Push-Wort |

### Beobachtungen (nicht blockierend)

- **O-29-01 (Push 4):** Die Antwort ist wörtlich belegt, die Frage nur sinngemäß ("Push-Frage zu den Audit-Commits `1c5c9995..3fd8349b`", 29-14-SUMMARY). Tatsächlich gepusht wurde `7b8b4271..99326ae2`; über den genannten Bereich hinaus gingen b10cec20 und 9ab18e12 (Bericht und SUMMARY von 29-13, dort als "nimmt der nächste gedeckte Push mit" angekündigt), 1c5c9995 und 99326ae2 (je zwei Zeilen ROADMAP.md) mit. Per `git show --stat` geprüft: reine Doku, kein Produktpfad. Der Bericht führt keinen eigenen Abschnitt "Push 4" mit Kopf-SHA; der CI-Beleg auf 99326ae2 steht in 29-15. Empfehlung: künftig Frage wörtlich und gepushten Bereich exakt festhalten.
- **O-29-02 (Push 5, Einreichung):** Ein "go" deckte Einreichung, Posts und Doku-Push, der Plan sah für den Push einen eigenen Checkpoint und für die Einreichung das Wort "einreichen" vor. Die Frage nannte beides ausdrücklich, die Abweichung ist in 29-16-SUMMARY dokumentiert. Schließen der Issues war nicht gedeckt und unterblieb (per `gh` geprüft).

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-29-01 | T-29-04 | Neue Labels und Abhilfen sind statische Texte ohne Platzhalter für Datei oder Pfad (`AdminViewService.php:497ff`) | Plan 29-01, im Phasenaudit nachgelesen | 2026-10-06 |
| AR-29-02 | T-29-14 | Wer eine eigene Datei `._x.pdf` nennt, nimmt nur diese aus dem Index; Urteil skipped(system_file) ist auf der Statusseite sichtbar | Plan 29-05 (D-29-05), Owner-Abnahme 29-14 | 2026-10-06 |
| AR-29-03 | T-29-20 | Diagnose und occ bleiben ADMIN-gebunden, nur ein neues Feld (`api/diagnose.py`) | Plan 29-06 | 2026-10-06 |
| AR-29-04 | T-29-32 | Keine neue Route, Nachprüfung über bestehendes ExAppRequired-requeue (`QueueMapper.php:616`) | Plan 29-09 | 2026-10-06 |
| AR-29-05 | T-29-SC | Keine Paketinstallation in der Phase; `uv.lock` unverändert | Plan 29-03 | 2026-10-06 |
| AR-29-06 | F-29-03 | ShortRead gegen veraltete Cachegröße endet als failed(repeatedly_stuck), kein Fehlurteil über den Inhalt; folgt aus D-29-04; 1.4.1-Kandidat in `deferred-items.md` | Owner, "abgenommen du kannst weiter" (deckt deferred-items) | 2026-10-06 |
| AR-29-07 | F-29-04 | CFB-Ausnahmeliste deckt jede erreichbare Ausnahme; eine unerwartete Klasse endet im Kind als failed(corrupt), also dem Weg vor 1.4.0 | Owner, wie AR-29-06 | 2026-10-06 |
| AR-29-08 | F-29-05 | Nachprüfung einmalig, unterbrechbar mit Cursor, ohne Download und Kind; verzögert den ersten Claim nach dem Upgrade einmal | Owner, wie AR-29-06 | 2026-10-06 |
| AR-29-09 | T-29-31 (Umfang) | failed(ocr_failed) bewusst nicht in der Nachprüfung (kein Fix berührt die Engine); `test_ocr_failed_is_never_selected` (passed) | Owner, Teil 9 in 29-02 ratifiziert, deferred-items | 2026-10-06 |
| AR-29-10 | T-29-07 | Box-gebundene Feldbelege (D-29-11, Annahme A5) offen bis zur nächsten Box-Anfahrt; im Store-Text nicht versprochen | Owner-Entscheid D-29-11, deferred-items | 2026-10-06 |

*Accepted risks do not resurface in future audit runs.*

---

## Unregistered Flags

Keine. Die Abschnitte `## Threat Flags` aus 29-01, 29-02, 29-06, 29-07, 29-09, 29-10, 29-11 und 29-16 verweisen ausschließlich auf bestehende Threat-IDs.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-06 | 47 (T-29-01..47) | 47 | 0 | Phasenaudit Plan 29-14 (gegen 1c5c9995) |
| 2026-10-06 | 65 (T-29-01..58, T-29-23b, T-29-SC, F-29-01..05) | 65 | 0 | gsd-security-auditor (am HEAD 62972497, 389 Tests gefahren) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-06
