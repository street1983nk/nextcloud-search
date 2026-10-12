---
phase: 31-neue-formate-und-nachholweg
plan: 12
subsystem: Upgrade-CI (deploy-harp.yml Store upgrade 2b und 3c), Saat-Fixtures, Gates
tags: [fmt-06, d-31-02, sc2, sc4, upgrade-ci, saat, repeatedly_stuck, zip-bombe]
requires:
  - phase: 31-05
    provides: "word97-latin.doc und make_legacy_fixtures.py"
  - phase: 31-06
    provides: "biff8-values.xls"
  - phase: 31-08
    provides: "archive.extract_zip mit ARCHIVE_MAX_DEPTH 2 und ARCHIVE_MAX_RATIO 100 ab 1 MiB"
  - phase: 31-11
    provides: "Nachholweg recheck_1_5_0, Teil-A-Regel select_catchup_candidates, NEW_MIMETYPES"
provides:
  - ".github/fixtures/upgrade-seed-formats/: acht Saatdateien (eml, zip, Zip-Bombe, doc, xls, heic, Word-OLE als .docx, stale-size .txt)"
  - "scripts/ci/make_upgrade_seed_formats.py mit SEED_WORDS, BOMB, render_deterministic"
  - "Store upgrade 2b: Saat der neuen Formate unter 1.4.2 und repeatedly_stuck in fester Reihenfolge, IDs UPGRADE_SEED_{MAIL,ZIP,BOMB,DOC,XLS,HEIC,OLE,STALE}_ID"
  - "Store upgrade 3c: recheck_1_5_0 absent, UPGRADE_OLD_STOCK_DIGEST, UPGRADE_CATCHUP_CANDIDATES/_CANDIDATE_STATES/_CHANGED/_CHANGED_VERDICTS"
  - "seed-probe.py: neue Fragen rows, reconcile, catchup, digest"
affects: [31-13 Store upgrade 5 und gemeinsamer Push, 31-15 Audit]
tech-stack:
  added: []
  patterns:
    - "ZIP von Hand gebaut, Nullbytes als Deflate mit fester Huffman-Tabelle: bytegleich auf jeder Plattform"
    - "Positive Kontrolle in derselben Suchrunde (Saatwort des Bildes = 1), bevor eine Null gilt"
    - "Ermittelte Erwartungsliste im Run-Text, Bestand wird gegen sie gehalten statt übernommen"
key-files:
  created:
    - scripts/ci/make_upgrade_seed_formats.py
    - backend/tests/fixtures/legacy/word97-ole-seed.doc
    - .github/fixtures/upgrade-seed-formats/seed-mail.eml
    - .github/fixtures/upgrade-seed-formats/seed-archive.zip
    - .github/fixtures/upgrade-seed-formats/seed-bomb.zip
    - .github/fixtures/upgrade-seed-formats/seed-word.doc
    - .github/fixtures/upgrade-seed-formats/seed-excel.xls
    - .github/fixtures/upgrade-seed-formats/seed-photo.heic
    - .github/fixtures/upgrade-seed-formats/seed-ole-under-docx.docx
    - .github/fixtures/upgrade-seed-formats/seed-stale-size.txt
  modified:
    - scripts/dev/make_legacy_fixtures.py
    - backend/tests/fixtures/legacy/README.md
    - backend/tests/test_upgrade_seed_fixture.py
    - backend/tests/test_upgrade_seed_steps.py
    - .github/workflows/deploy-harp.yml
decisions:
  - "Saat am Andockblock in Store upgrade 2b, kein eigener Schritt 2c: q, seed_probe, seed_hits und open_rows stehen dort schon, ein neuer Schritt hätte sie ein zweites Mal gebraucht"
  - "Die sieben Dateien kommen per WebDAV (Listener-Weg von 1.4.2), nicht per files:scan und Crawl: keine zweite Vollrunde über 300 Dateien, und der Listener ist genau der Weg, auf dem 1.4.2 die neuen Typen verwirft"
  - "Vor Schritt 1 wartet die Strecke auf den ersten beendeten Abgleich-Zyklus von 1.4.2; danach ist laut reconcile.py:645-653 vor 24 h kein Zyklus fällig, also gilt für die .txt genau 0 Zeilen in state.db"
  - "Die Dateicache-Größe der .txt wird nach dem Aufgeben per sqlite3 auf den echten Wert zurückgesetzt (kein Ereignis), damit 31-13 das Nachholen und nicht eine erfundene Größe misst"
  - "Altbestand: keine Nachhol-Kandidaten (Teil A und B leer); 3c hält den Bestand gegen diese Ermittlung und bricht ab, wenn er abweicht"
  - "Checkpoint Task 2 nicht ausgelöst, alle fünf Schritte gangbar"
metrics:
  duration: "ca. 55 min, davon ca. 30 min Testläufe und CI"
  completed: 2026-10-12
  tasks: 3
  files: 15
---

# Phase 31 Plan 12: Saat der neuen Formate unter v1.4.2 Summary

Die Upgrade-Strecke sät jetzt acht weitere Dateien auf der echten 1.4.2-Installation: sechs neue Typen und eine Zip-Bombe, die 1.4.2 nie einreiht, eine Word-97-Datei unter .docx-Namen, die 1.4.2 als skipped(legacy_format) bucht, und eine .txt, die 1.4.2 nach seiner eigenen Regel als failed(repeatedly_stuck) aufgibt, ohne Containerzeile. Store upgrade 3c hält vor dem Upgrade fest: recheck_1_5_0 fehlt, der Altbestand hat keine Nachhol-Kandidaten, und ein Digest über die stabilen Spalten des Altbestands geht nach GITHUB_ENV. Der Workflow-Commit bleibt lokal und geht mit 31-13 Task 1 auf main.

## Ermittlung unter v1.4.2 (Quelle `git show v1.4.2:<pfad>`)

### Feste Reihenfolge für repeatedly_stuck

| Schritt | gangbar | Beleg (Datei:Zeile in v1.4.2) |
|---|---|---|
| 1. ExApp stoppen | ja | `docker stop` des Containers. Die Strecke startet Container schon an anderer Stelle neu (deploy-harp.yml Store upgrade 6, `docker start`). Ein Stopp löscht die Armierungsmarke nicht, nur das Abschalten tut das (backend/src/findling/main.py:270-275 `_forget_the_enable`, gerufen nur im enabled_handler beim Abschalten, :340) |
| 2. Hochladen, Listener reiht ohne Container ein | ja | php/lib/Listener/FileEventListener.php:381 (Allowlist), :487 `enqueueFile`; kein Aufruf des Containers auf dem Weg; QueueMapper.php:217-236 schreibt die Zeile mit `size` und freiem `locked_at` |
| 3. Größe in oc_filecache und Queue-Zeile | ja | Die Queue hat die Spalte `size` (php/lib/Migration/Version001000Date20260816000000.php:70). Die Auslieferung nimmt die Größe des Knotens, also des Dateicaches (php/lib/Service/QueueService.php:840 und :907). Der Container erwartet genau so viele Bytes (backend/src/findling/nc/client.py:286-287, ShortRead). Das Gateway setzt keine Content-Length: GatewayController.php:102-107 gibt eine StreamResponse auf `fopen`, die NC stable34 per `stream_copy_to_stream` schreibt (lib/private/AppFramework/Http/Output.php:35-42). `judge` lässt die Datei durch, weil +4096 Byte weit unter `max_file_bytes` liegen (extract/dispatch.py:135) |
| 4. Container starten, warten bis er antwortet | ja | main.py:1103-1111: Ist die Marke da, wird beim Start armiert, Logzeile "findling backend was enabled before this start, indexing continues without a switch". Der Abgleich ist danach nicht fällig (siehe unten) |
| 5. Je Auslieferung kurz gelesen, Sperre zurückdatieren | ja | poller.py:1502-1511: zweimal kurz, Logzeile "download of one file stayed short twice, handing the row back unjudged", kein Urteil und kein unlock. Am Rundenende `_held.clear()` ohne unlock (poller.py:1197). Spalte `locked_at` (Migration :74), frei ist `locked_at <= now - LOCK_TIMEOUT` (QueueMapper.php:926), LOCK_TIMEOUT 900 für content (:102, :147). Der Claim zählt `retries + 1` (:402). MAX_DELIVERIES 3 (QueueService.php:65), der vierte Claim schreibt `failed/repeatedly_stuck` (:325-326) über FileStateService (REASONS :127, STATE_REASONS :179) |

**Checkpoint Task 2 nicht ausgelöst, alle fünf Schritte gangbar (Tabelle).**

### state.db für die .txt (Blocker 1)

| Frage | Ergebnis | Beleg |
|---|---|---|
| Schreibt 1.4.2 bei zweimal kurzem Lesen ein Urteil? | nein | poller.py:1502-1511 (`return 0` ohne `_collect`) |
| Wann entsteht eine give_up-Zeile? | nur in einem Abgleich-Zyklus nach dem Aufgeben | reconcile.py:505-517 (`stored is None and written_off`) |
| Läuft unter 1.4.2 nach dem Aufgeben ein Zyklus? | nein, wenn der erste Zyklus vorher beendet ist | `_is_due` reconcile.py:645-653: sofort fällig nur ohne beendeten Zyklus oder mitten im Gang, sonst erst nach `RECONCILE_MIN_INTERVAL_HOURS` 24 (config.py:544). Die Strecke setzt keine `FINDLING_RECONCILE_*` (grep ohne Treffer). Neu: Store upgrade 2b wartet vor Schritt 1 über die Probe `reconcile` (MAX(finished_at) gesetzt, kein after_file_id > 0), bis der Zyklus beendet ist |

Zusicherung deshalb: **0 Zeilen in state.db** (auch keine Grabsteinzeile, Probe `rows` zählt alle).

### Wie 1.4.2 die übrigen Saatdateien behandelt

| Datei | Typ in Nextcloud | 1.4.2 | Beleg |
|---|---|---|---|
| seed-mail.eml, seed-archive.zip, seed-bomb.zip, seed-word.doc, seed-excel.xls, seed-photo.heic | message/rfc822, application/zip, application/msword, application/vnd.ms-excel, image/heic | nie eingereiht: keine Zeile in state.db, keine in findling_file_state | StorageService.php:111-130 (Allowlist ohne die Typen), FileEventListener.php:381; der Crawl filtert mit derselben Liste (StorageService.php:456) |
| seed-ole-under-docx.docx | docx | skipped(legacy_format) auf beiden Seiten | extract/cfb.py:105 (Strom WordDocument), lokal gegengeprüft: `ole_verdict` aus v1.4.2 auf der Datei ergibt `skipped/legacy_format`; FileStateService.php:117/:168 kennt den Code |

### Nachhol-Kandidaten im CI-Altbestand

Der Altbestand sind alle Nicht-Saat-Dateien: 39 Dateien des Referenzkorpus (testdata/CORPUS.md:110-150), upgrade-carta-es.txt, upgrade-dopis-cs.txt, 256 Fülltexte, welcome.txt (git-Skeleton von stable34 enthält nur `core/skeleton/welcome.txt`) sowie language-proof-*.txt und findling-zero-config.txt aus früheren Schritten.

| Teil | Kriterium (worker/catchup.py bzw. reconcile.py aus 31-11) | Treffer im Altbestand | Beleg |
|---|---|---|---|
| A | skipped(legacy_format) außer PowerPoint | keiner | Magic-Bytes aller Korpusdateien: keine OLE-Signatur; CORPUS.md nennt kein legacy_format |
| A | nicht indexierte Zeile eines neuen Typs | keiner | kein .eml/.zip/.doc/.xls/.heic im Altbestand |
| A | failed(repeatedly_stuck) | keiner | CORPUS.md: die sechs failed sind empty_file (06) und corrupt (24, 26, 27, 28, 33); Store upgrade 5 zählt nextcloud.failed 6 (Lauf 38238806189) |
| B | Nextcloud repeatedly_stuck ohne Containerzeile | keiner | wie oben |
| B | Mischfenster-Paar (Ersatzcode gegen echten Code) | keiner | Store upgrade 4 hebt erst den Begleiter (deploy-harp.yml `occ upgrade`), dann den Container (`app_api:app:unregister`/`register`). Ein 1.4.2-Container schickt einem 1.5-Begleiter nur bekannte Codes. Die zwei image_not_ocrable-Dateien (05, 22) hält der Container ebenfalls als image_not_ocrable, kein Paar |
| B | unbekannte Datei (neuer Typ ohne Containerzeile) | keiner | wie Teil A |

Erwartung: `UPGRADE_CATCHUP_CANDIDATES` leer, `UPGRADE_CATCHUP_CHANGED` leer. 3c rechnet die Kandidaten aus den Daten nach (Teil A über die Probe `catchup`, Teil B über drei Abfragen) und bricht ab, wenn sie von der Ermittlung abweichen.

Die Saat ist nicht im Digest. Für sie gilt nach dem Upgrade (Gegenstand von 31-13): sechs neue Typen über Teil B unbekannt, Word-OLE über Teil A (legacy_format, kein PowerPoint), .txt über die Nachhol-Ausnahme in Teil B (abgeschrieben, keine Containerzeile).

### Saatwörter im übrigen CI-Korpus

`test_no_seed_word_stands_in_the_reference_corpus` liest jede Datei von testdata/corpus als UTF-8, UTF-16 und Latin-1: kein Treffer. Gegenprobe: eine Datei `zz-gegenprobe.txt` mit "cachequendel" im Korpus macht den Test rot, danach wieder gelöscht. Die Füll- und Sprachtexte von Store upgrade 2 stehen im Workflow, keiner enthält "quendel". Der Abschnitt der Strecke prüft außerdem vor dem Säen, dass alle sieben Wörter nichts finden, mit positiver Kontrolle.

## Umsetzung

- **Saat (Task 1, 8cf62567, gepusht):** `make_upgrade_seed_formats.py` schreibt eml, zip, Bombe und txt deterministisch. Die ZIPs baut es von Hand (feste DOS-Zeit, System Unix, Modus 0644). Die 1 048 771 Nullbytes der Bombe sind ein Deflate-Strom mit fester Huffman-Tabelle (ein Literal, 4065 Treffer zu 258 Byte), 7095 Byte groß; kein zlib der Maschine ändert ein Byte. Die Bombe: ebene2.zip enthält ebene3.zip enthält notiz.txt (Tiefe 3 > ARCHIVE_MAX_DEPTH 2), dazu nullen.bin mit Rate 158:1 > 100:1. Das Foto (1600 x 600, DejaVuSans 110 px, Zeilen "fotoquendel", "Urlaub am See", "fotoquendel") rendert der Generator nur, wenn es fehlt oder bei `--render-photo`. word97-ole-seed.doc stammt aus `make_legacy_fixtures.py --name word97-ole-seed` (neue Option, die übrigen fünf Fixtures blieben unberührt).
- **Store upgrade 2b (Task 3, b021f16c, lokal):** Der Andockkommentar ist durch die Saat ersetzt. Ablauf:
  - positive Kontrolle und sieben Wörter mit 0 Treffern
  - WebDAV-Upload der sieben Dateien, IDs mit Musterprüfung, Mimetypen gegen die Erwartung
  - warten, bis die Queue leer und die Word-OLE beurteilt ist
  - fail-closed: sechs Typen plus Bombe ohne Zeile auf beiden Seiten, Word-OLE skipped/legacy_format auf beiden Seiten
  - warten auf den beendeten Abgleich-Zyklus
  - die fünf Schritte, je mit Budget und `::error::` mit Schrittnummer
  - nach dem Aufgeben: genau 3 kurze Lesungen, Queue leer
  - Dateicache-Größe zurück, dann .txt failed/repeatedly_stuck in findling_file_state, 0 Zeilen in state.db, keine Queue-Zeile
  - sieben Wörter wieder 0 mit positiver Kontrolle
  - Export der acht IDs nach `^[0-9]+$`
- **seed-probe.py:** neue Fragen `rows`, `reconcile`, `catchup` und `digest`. `catchup` ist die Regel von select_catchup_candidates, ausgeschrieben, weil der befragte Container 1.4.2 ist. `digest` liest nur `file_id, state, IFNULL(reason, ''), IFNULL(etag, '')` und die Chunk-Zahl. Lokal auf einer state.db nach dem v1.4.2-Schema geprüft: Ergebnis gleich `select_catchup_candidates` ([2, 4, 5, 6]). Der Digest bleibt gleich, wenn attempts, indexed_at und index_version sich bewegen.
- **Store upgrade 3c:**
  - `catchup=$(seed_probe meta recheck_1_5_0)` muss `absent` sein; die Variable heißt nicht `recheck`, weil ein bestehender Gate-Fall `"${recheck}" != "absent"` im ganzen Workflow verbietet
  - zehn Saat-IDs mit Muster `^[0-9]+(,[0-9]+){9}$`
  - Kandidaten nachgerechnet und gegen die ermittelten Listen gehalten
  - Stand je Kandidat, Musterprüfung beider Listen und der Urteilslisten
  - `comm -12` über beide Listen vor dem GITHUB_ENV-Block
  - Digest ohne Saat-IDs und ohne `UPGRADE_CATCHUP_CHANGED`, Muster `^[0-9a-f]{64}$`
  - Store upgrade 5 ist unverändert (31-13).
- Lokal mit Stubs in Git-Bash (`bash -eo pipefail`) ausgeführt: leerer Bestand grün, mit Exportzeilen. Teil-A-Kandidat, abgeschriebene Datei ohne Zeile, unbekannter neuer Typ und gesetzte Marke jeweils rot mit Meldung. Dieselbe ID in beiden Listen rot. Geänderter Kandidat: aus dem Digest genommen. Gleicher Kandidat: bleibt drin, Stand exportiert.

## RED

- Task 1, `test_upgrade_seed_fixture.py` vor dem Generator: **20 failed, 8 passed, 1 skipped**. Grün vorher waren die 7 alten Fälle und `test_no_seed_word_stands_in_the_reference_corpus` (Gegenprobe oben).
- Task 3, `test_upgrade_seed_steps.py` gegen den Workflow von HEAD: **17 failed, 54 passed**. Grün vorher waren `test_no_line_writes_a_verdict_into_a_table`, `test_the_seed_and_record_steps_carry_no_expression` (zwei Parameter) und `test_the_record_step_parses_in_bash`. Gegenproben auf dem neuen Workflow, je ein Eingriff, danach `cmp` gleich:
  - `UPDATE oc_findling_file_state SET ... 'repeatedly_stuck'` vor Schritt 4 eingefügt: rot
  - `${{ matrix.runner }}` in 3c eingefügt: rot
  - offenes `if` in 3c eingefügt: rot
- Ein Fall war nach GREEN zuerst rot, weil der Test den Exportblock der zwei alten IDs fand. Korrigiert auf den letzten Exportblock (`rindex`).
- `test_the_seed_step_leaves_room_for_phase_31` ist **ersetzt** durch `test_the_seed_step_sows_the_new_formats_where_phase_31_was_announced`. Begründung: Der Andockkommentar war der Platzhalter für genau diese Saat. Der Ersatzfall verlangt, dass er fehlt und die Saat nach dem Export der zwei bisherigen IDs steht.

## Gates und CI

- Lokal vor 8cf62567: ruff check (backend und beide Skripte), ruff format --check, pyright latest 0 Fehler, vulture grün, volle Suite **5429 passed, 30 skipped**.
- Lokal vor b021f16c: dieselben Gates, volle Suite **5449 passed, 30 skipped**, darin tests/test_measurement_scripts.py (Baumhash unverändert, `backend/src/findling` und `php/` nicht berührt).
- HEIC-Lesung: Lokal gibt es kein tesseract, der Fall `test_the_engine_reads_the_word_of_the_photo` ist hier und in python.yml übersprungen. Beleg im Image `findling_backend:dev` (ohne die HEIC-Route von 31-07, deshalb direkt): pillow-heif 1.8.0 öffnet die Datei (1600 x 600 RGB), tesseract `-l deu+eng` liest "fotoquendel / Urlaub am See / fotoquendel". Der Lesebeweis durch 1.5 folgt in 31-13.
- Push `fc003c0a..8cf62567` (Workflow unverändert), alle sieben Läufe success:
  - Python gates **38244385443** (5441 passed, 18 skipped)
  - HaRP deploy **38244385580**: vier Jobs success, darunter stable34/ubuntu-24.04 mit Store upgrade 0 bis 7
  - Resilience 38244385479, Integration 38244385596, Multi-arch image 38244385486, Security scans 38244385547, OpenSSF Scorecard 38244385632

## Commits

| Commit | Inhalt | gepusht |
|---|---|---|
| 8cf62567 | test(31-12): the seed of the new formats for the upgrade proof | ja |
| b021f16c | ci(31-12): sow the new formats on 1.4.2 and record them before the upgrade | nein (geht mit 31-13 Task 1) |

## Deviations from Plan

**1. [Rule 2] Warten auf den ersten Abgleich-Zyklus vor Schritt 1.** Ob die Strecke unter 1.4.2 nach dem Aufgeben einen Zyklus fährt, hing bisher vom Zeitpunkt ab. Wenn der erste Zyklus von 1.4.2 noch nicht gelaufen war, wäre er sofort fällig (reconcile.py:647), und dann entstünde eine give_up-Zeile. Das wäre ein "0 oder 1", das der Plan ausschließt. Der Schritt liest deshalb nur (Probe `reconcile`) und wartet mit Budget. Die Reihenfolge der fünf Schritte bleibt unverändert.

**2. [Rule 2] Dateicache-Größe nach dem Aufgeben zurück.** Ohne Rücksetzen würde 1.5 die Datei nach dem Upgrade wieder kurz lesen, und 31-13 könnte "indexed" nicht zusichern. Der Grund wäre eine Größe, die die Strecke selbst erfunden hat. Zurückgesetzt wird per sqlite3 (kein files:scan, also kein Ereignis). Danach prüft der Schritt den 1.4.2-Zustand noch einmal: failed/repeatedly_stuck, 0 Zeilen, keine Queue-Zeile. **Befund für 31-13:** Die Zusicherung "indexed" für STALE setzt dieses Rücksetzen voraus.

**3. WebDAV statt files:scan plus Crawl** für die sieben Dateien (Entscheidung oben). Die Wörter-Abfrage hat eine positive Kontrolle (Saatwort des Bildes genau 1), sonst wäre eine 0 bei unerreichbarem Container grün.

**4. Zusätzliche Exportwerte in 3c:** `UPGRADE_CATCHUP_CANDIDATE_STATES` (Stand je Kandidat) und `UPGRADE_CATCHUP_CHANGED_VERDICTS` (erwartetes neues Urteil). Der Plan verlangt beides, nennt aber keinen Namen. Muster: `id=state/reason`, kommagetrennt.

**5. [Rule 1] Musterprüfung leerer Listen.** `printf '%s' "" | grep -Eq` findet keine Zeile und schlug bei der leeren Liste fehl, im Stub-Lauf gefunden. Jetzt `printf '%s\n'`. Ebenso `grep -q` hinter `docker logs` durch `grep -c` ersetzt (pipefail und SIGPIPE).

## Known Stubs

Keine. Die leeren Kandidatenlisten sind das Ergebnis der Ermittlung, kein Platzhalter. 3c prüft sie gegen den Bestand.

## Threat Flags

Keine neue Fläche außerhalb des Plans. Umgesetzt:

- T-31-38: Musterprüfung vor jedem GITHUB_ENV-Wert, Gate-Fälle
- T-31-39: Ermittlungstabellen mit Quelle, fail-closed je Saat, 3c hält den Bestand gegen die Ermittlung
- T-31-40: Run-Texte ohne `${{`, Gate-Fall mit Gegenprobe
- T-31-40b: kein UPDATE/INSERT/REPLACE in einer Zeile mit repeatedly_stuck oder legacy_format, Gate-Fall mit Gegenprobe

Hinweis: Die Strecke schreibt per sqlite3 in oc_filecache und oc_findling_queue (Größe, Sperrzeit). Das betrifft nur den CI-Bestand.

## Requirements

FMT-06, FMT-02 und die anderen FMT bleiben **Pending** (Owner-Linie: E2E-Beweis in 31-13). POL-02 ist seit 31-03 Complete. Dieser Plan formuliert die 1.4.2-Ausgangslage, der CI-Beleg folgt mit dem gemeinsamen Push in 31-13.

## Offene Punkte

- 31-13: Push von b021f16c nur zusammen mit 31-13 Task 1. Im ersten Lauf die Logzeilen von Store upgrade 2b zitieren:
  - "step 1" bis "step 5"
  - "three deliveries read short"
  - Abgleich-Zyklus beendet
  - acht Zustände
  - 3c-Zeile mit Digest und Kandidaten
- 31-13: STALE-Zusicherung "indexed" stützt sich auf das Rücksetzen der Größe (Abweichung 2). Zip-Bombe nach dem Upgrade: skipped(archive_limit), Container läuft weiter (SC2).
- Risiko für den ersten CI-Lauf: Nach `docker start` muss der HaRP-Tunnel wieder stehen. Die positive Kontrolle zeigt das mit klarer Meldung. Store upgrade 6 erzeugt Container neu (`docker create`), hier wird derselbe Container wieder gestartet, die Zertifikate bleiben in seinem Dateisystem.
- Lokal liegt ein Image `findling_backend:1.4.3` von heute (ca. 4 h alt). Es stammt nicht aus diesem Plan, Herkunft unbekannt (Parallel-Session?).

## Abschlussprüfung (nach dem letzten Commit dieses Plans)

Wird nach dem Docs-Commit ergänzt.
