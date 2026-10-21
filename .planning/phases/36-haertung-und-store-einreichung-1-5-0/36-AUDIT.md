---
phase: 36-haertung-und-store-einreichung-1-5-0
audited: 2026-10-21
diff: 17363bb2..e7538389
files_reviewed: 76
findings:
  critical: 0
  high: 0
  medium: 0
  low: 4
  total: 4
status: offen
fix_commits: []
fixed: []
still_open: [L-36-01, L-36-02, L-36-03, L-36-04]
---

# Phase 36: Launch-Audit 1.5.0 (Security, Bugs, Performance)

**Stand:** offen (Task 1 abgeschlossen, Performance und Behandlung folgen).

**Umfang:** milestone-weit. Basis ist `git merge-base HEAD v1.4.3` =
`17363bb2` (Tag v1.4.2, Zweigpunkt von `release/1.4.x`; v1.4.3 = 0f088d05
liegt nur auf dem Release-Zweig). `git diff --stat 17363bb2..HEAD -- backend/src
php/lib php/js php/templates .github/workflows`: **76 Dateien, 11 892 Zeilen
dazu, 1 124 weg** (gesamter Baum: 598 Dateien, 358 Commits). Gelesen bzw. per
Probe gefahren: `php/lib/Controller/ReconcileController.php`,
`StorageService.php`, `AdminViewService.php`, `PageController.php`,
`QueueController.php`, `backend/src/findling/worker/reconcile.py`,
`nc/files.py`, `nc/client.py`, `store/repo.py`, `extract/{archive,odf,office,
image,mail,cfb,errors,legacy_doc,legacy_xls}.py`, `main.py`,
`.github/workflows/release.yml`, `deploy-harp.yml`; alle 41 neu hinzugekommenen
Logzeilen des Diffs (`git diff -U4 17363bb2..HEAD -- backend/src php/lib | grep
-E "^\+.*(LOGGER\.|logger->)"`). Vorher gelesen: alle SUMMARYs 36-01 bis 36-11
und 36-17, 32-AUDIT (L-32-01, 03, 04, 05, 07), 34-AUDIT, 35-AUDIT (L-35-02,
L-35-06).

**Wo gelaufen:** Windows 11 Pro 10.0.26200, 2,2 GB RAM frei, alles seriell,
kein Browser. Instanz `findling-nextcloud` (http://localhost:8090, NC 34,
SQLite, `php/` als Bind-Mount, also Stand des Arbeitsbaums), Backend als
Host-Prozess auf 10035 über `FINDLING_PORT=8090 FINDLING_RECONCILE_ENABLED=false
sh scripts/dev/register-exapp.sh` (Abgleich-Zyklen nur als eigene
`run_once`-Prozesse, Muster 36-05). state.db vor dem ersten Eingriff gesichert:
`.dev/backup-36-12/state.db.bak`, SHA-256 `1fa39039...0877e0`. Quelltextproben
und ein Test je Befund in `backend/tests/test_phase36_audit.py`.

## Security

### S1 Trust Boundary aller ApiRoute-Methoden, `/storages/gone`

- **Gate:** `uv run python -m pytest tests/test_php_trust_boundary.py` grün,
  darunter `test_every_route_of_every_controller_is_guarded`,
  `test_the_guard_has_to_be_the_first_statement`,
  `test_missing_reject_foreign_caller_is_reported` (Positivkontrolle des Gates).
- **Live** `GET /ocs/v2.php/apps/findling/storages/gone?ids[0]=2&ids[1]=999999`:
  (a) als admin per Basic-Auth ohne AppAPI-Kopf: **412** `{"message":"ExApp
  required"}`; (b) `EX-APP-ID: findling_evil` mit dem echten Secret: **412**;
  (c) `findling_backend` mit falschem Secret: **412**; (d) Positivkontrolle mit
  gültiger Signatur: **200** `{"gone":[999999],"deselected":[]}`. Ein zweites
  registriertes ExApp gibt es auf 8090 nicht; den Fall "gültige Signatur,
  fremde App" deckt `ReconcileControllerTest` (403 ohne Dienstaufruf, CI).

### S2 Eingaben der neuen Route

Mit gültiger Signatur, je ein curl: 256 IDs **200** (Kontrolle), 257 IDs
**400**, `ids=` **400**, Skalar `ids=5` **400**, `ids[]=a` **400**, `1e3`,
`-1`, `0`, `+1`, `1.5`, `<img>`, `1%0A`, `ids[0][0]=1` je **400**, ohne
`ids` 200 mit zwei leeren Listen, doppelte ID 200. **Kein 500.** Ein Befund:
`ids[0]=12345678901234567890` (20 Ziffern) antwortet **200 mit
`"gone":[9223372036854775807]`**, weil der Cast auf PHP_INT_MAX klemmt; `014`
liest als 14. Siehe **L-36-02**.

### S3 Logs

- **Quelltext:** die 41 neuen Logzeilen des Milestone-Diffs gelesen. Sie
  tragen statische Sätze, Zähler, Typnamen (`type(error).__name__`), Storage-IDs
  (Nachlauf, T-36-17) und auf PHP-Seite `['exception' => $e]` im eigenen Feld;
  keine Pfade, keine Dateinamen, keine fileid-Listen, keine Nutzer-IDs in
  Findling-eigenen Sätzen. Die Länge der Storage-ID-Listen ist unbegrenzt,
  siehe **L-36-03**.
- **Live, Standard-Loglevel (info):** Marke `.dev/exapp.log` Zeile 25,
  `audit3612-logprobe.txt` als admin hochgeladen (PUT 201), indexiert
  (`indexed=1` nach 36 s). Neue Zeilen: 2, davon mit `userId` **0**, httpx/httpcore
  **0**, Dateiname oder Prüfwort **0**.
- **Positivkontrolle:** Backend gestoppt (nur die eigenen PIDs), mit
  `FINDLING_LOG_LEVEL=debug` neu registriert, `audit3612-debugprobe.txt`
  hochgeladen: genau die erwartete Zeile erscheint, `INFO:httpx:HTTP Request:
  GET .../files/21732?userId=admin`. L-35-06 ist damit geschlossen (36-02,
  c9c55300/03a45248, Tests `test_the_client_loggers_stand_on_warning_by_default`
  und `..._speak_again_under_debug`).
- **Log-Sonde der Korpusfälle:** `test_no_line_of_the_corpus_run_carries_a_name_or_a_word_of_the_content`
  (36-07, 14 Dateien, acht Geheimwörter, Positivkontrolle
  `DecompressionBombWarning`) grün im Lauf von P1.

### S4 Detailcodes und XSS

- **Quelltextprobe (Syntaxbaum, nicht grep):** jedes `detail=` und jedes
  zweite Positionsargument von `skipped`/`failed` in `extract/*.py` ist ein Code
  der geschlossenen Liste A3, ein Klassenname (`module.qualname` bzw.
  `RecursionError`), ein Aufruf von `_class_of` oder `over.signature`; jedes
  `OverLimit(...)`-Argument löst zu einem Code der Liste auf. 20 Fundstellen,
  0 Abweichungen. Positivkontrolle: Nachricht, Mitgliedsname, fremder Code und
  fremdes OverLimit werden alle fünf gemeldet. Tests
  `test_every_detail_of_an_extractor_is_a_closed_code_or_a_class_name`,
  `test_the_detail_probe_reports_a_message_a_name_and_a_foreign_code`,
  `test_from_exception_builds_its_detail_out_of_the_type_alone`.
- **XSS-Probe:** `<img src=x onerror=alert(1)>`, `image_pixels<script>`, `../x`
  werden von `repo._ERROR_CLASS_SHAPE` (fullmatch) und von
  `AdminViewService::ERROR_CLASS_PATTERN` (aus dem PHP-Quelltext gelesen, mit
  PCRE-Semantik ausgewertet) verworfen
  (`test_markup_in_a_detail_is_refused_by_both_form_checks`). Die Karte setzt
  den Wert per `textContent` (`admin.js` Zeile 283), `innerHTML` kommt in
  `admin.js` und `unified-search.js` nicht vor.
- **Nebenfund:** `ERROR_CLASS_PATTERN` und vier weitere verankerte Formprüfungen
  in `php/lib` stehen ohne `D`-Modifikator; `$` erlaubt damit ein abschließendes
  `\n`. Live belegt: `?similar=14%0A` öffnet die Ähnlich-Ansicht von Datei 14
  ("Ähnlich zu: Triangle.odp", 3 Nachbarn), obwohl der Docblock von
  `similarId` nur kanonische Zahlen nennt. Siehe **L-36-01**.

### S5 Löschpfad M-32-02

- **Quelltextprobe (Syntaxbaum):** `run_once` ruft `_sweep_vanished` genau
  einmal, im `if found.mounts and (not found.discarded)` hinter der Schleife
  `for mount in found.mounts`, die bei jedem vorzeitigen Ende zurückkehrt; der
  `found.unavailable`-Ausgang steht davor. `KIND_DELETE` benutzt im Modul nur
  `_hand_over`, der Nachlauf ruft `requeue` nie direkt
  (`test_the_sweep_is_reached_only_behind_a_full_walk_of_a_clean_list`,
  `test_delete_orders_of_the_reconcile_leave_through_one_place`).
- **Monkeypatch:** `_sweep_vanished` durch einen Rekorder ersetzt, ein
  gelöschter Storage 14 im Bestand: nur die Runde "walked" erreicht ihn (genau
  einmal, mit `{3}`), "empty", "discarded", "unavailable", "ended_early" nie,
  und keine Runde erzeugt einen Löschauftrag
  (`test_the_sweep_runs_for_a_walked_round_only`, 5 Parameter). Dazu die
  16 Tests aus 36-04 (`test_reconcile_vanished.py`) grün.

### S6 Zip Slip

`grep -rn "extractall\|\.extract(\|open(\|write(" extract/`: die einzige
Schreiböffnung ist `member.open("wb")` in `archive._copy`; `member` kommt aus
`budget.next_scratch()`, das nur `f"{self.scratch}.m{self.serial}.part"` baut.
Kein `extractall`, kein `extract`. Als Syntaxbaumprobe
`test_no_extractor_unpacks_or_writes_under_a_member_name` (prüft auch, dass
`next_scratch` weder `filename`, `orig_filename`, `info` noch `name` liest).
Traversal-Namen enden ohnehin vor dem ersten Lesen als `zip_traversal`
(`test_a_climbing_name_is_judged_before_any_member_is_read`, 36-08).

### S7 Release-Kette

- `release.yml` Zeilen 512 bis 514: `corresponding_source.py fetch dist/source`,
  danach `--verify-only dist/source`, danach `git archive`; alles im einen
  `gh release create` (36-02, Probe 39439309752 mit neun Dateien).
- `ARCHIVES` trägt vier SHA-256 (`corresponding_source.py` Zeilen 93 bis 117).
  Stempeltest `test_the_recipe_stamp_follows_the_locked_pillow_heif` und
  Gegenprobe `test_the_stamp_gate_fires_on_a_stale_stamp` grün,
  `test_the_gate_fires_on_a_stale_row` (THIRD-PARTY.md) grün.
- Pins: `test_workflow_pins.py` grün. Unabhängige Gegenprobe: `grep -h "uses:"
  .github/workflows/*.yml | grep -vE "@[0-9a-f]{40}"` findet nur die lokale
  Composite-Action `./findling-src/.github/actions/setup-test-nc` (9) und eine
  Kommentarzeile; 61 Aufrufe tragen einen 40-stelligen SHA, alle 18 im
  Milestone neu hinzugekommenen ebenfalls.

### S8 Öffentliche Artefakte

`git diff --stat 17363bb2..HEAD -- '*.zip' '*.docx' '*.png' '*.tif*' '*.eml'
'*.doc' '*.xls' ...` und `git diff --numstat | awk '$1=="-"'`: 12 Binärdateien
plus `seed-mail.eml`, alle bekannt. `.github/fixtures/upgrade-seed-formats/`
(Upgrade-Saaten aus 31-12, `seed-bomb.zip` 391 Byte = reine Tiefe 3 nach O4 (a),
36-08) und `backend/tests/fixtures/legacy/` (LibreOffice-Ausgaben aus 31-05/06,
Digests in den Tests gepinnt). Keine Datei des bösartigen Korpus liegt im Baum;
er entsteht zur Laufzeit aus `backend/tests/hostile.py` (D-36-01).

## Bugs

| Nr. | Fall | Verfahren | Ergebnis | Urteil |
|---|---|---|---|---|
| B1 | Wire-Fallback der Sammelklasse gegen 1.4.x | `test_no_code_reaches_a_companion_that_does_not_know_it[None,0,1,2,3,4,99]` | 7 grün; `blocked_malicious` geht an Generation 2 und ohne Signal als `too_large` bzw. `corrupt` | in Ordnung |
| B2 | Detail einer skipped-Datei bis `/diagnose` | `hostile.png_bomb()` (390 Byte) und `hostile.zip_ratio_member()` (2 286 Byte) als admin hochgeladen, Poller `skipped=2`; `GET /apps/findling/admin/diagnose?ref=<id>` mit Session | 21733: `skipped`, `blocked_malicious`, Label "Datei als bösartig gesperrt", `errorClass` **`image_pixels`**; 21734: dito **`zip_ratio`**. Die Karte setzt "Detail: %s" für skipped (admin.js 808 bis 811, `textContent`) | in Ordnung |
| B3 | Rückkehr eines Storage, 404 eines 1.4.x-Companions, F4 | 36-04: `test_a_storage_that_comes_back_loses_its_stamp_and_a_new_absence_starts_over`, `test_no_answer_to_the_storage_question_means_grace_and_never_a_delete`, `test_a_storage_that_vanished_mid_walk_leaves_no_walk_open_for_good` | grün (214 passed im Sicherheitsblock) | in Ordnung |
| B4 | Upgrade-Zweig vor 36-13 | `grep -n UPGRADE_FROM_TAG deploy-harp.yml` = `v1.4.2` (Zeile 148), beide `info.xml` `<version>1.4.2</version>` | Reihenfolge für 36-13 bestätigt: erst Bump auf 1.5.0, dann `v1.4.3` (Pitfall 8). Als Wächter `test_the_upgrade_start_is_never_ahead_of_the_tree` | in Ordnung |
| B5 | Neubewertung alter LOWs | siehe Abschnitt "Neubewertung" | alle mit Urteil | in Ordnung |

### Neubewertung (B5)

| Befund | Prüfung heute | Urteil |
|---|---|---|
| L-32-01 Array-Form, 500 im Kern | live: `findling/search?term=Vertrag` 200, `&folder[]=/Projekte` **500**, Kern-Provider `files/search?...&path[]=/Projekte` ebenfalls **500**, `path=/Projekte` 200 | unverändert Kernverhalten von NC 34, Findling wird nicht erreicht; accept bleibt |
| L-32-03 umbenannter Ordner unter dem Chip | Quelltext `SearchService::scopeOf` unverändert seit 32 | von USRCH-03/T-32-06 verlangt; accept bleibt |
| L-32-04 Groß- und Kleinschreibung | auf 8090 weiter nicht nachstellbar (lokaler Speicher unterscheidet), der files_external-Lokalspeicher aus 36-05 ebenso | nur gebaute Werte auf SMB/S3; accept bleibt, Fremdinstallation 36-15 bleibt Beobachtungspunkt |
| L-32-05 Waisen bis zum Abgleich | mit M-32-02 strenger geworden: der Nachlauf räumt nun auch ganze Speicher | höchstens ein Abgleich-Intervall, nie ein Treffer; accept bleibt |
| L-32-07 Symbol nicht im CHANGELOG | CHANGELOG `[Unreleased]` ist zeichengleich mit dem am 20.10. abgenommenen B3 (36-11) | Owner hat den Releasetext ohne die Zeile abgenommen: erledigt durch Owner-Entscheid |
| L-35-02 Requeue weckt den Poller nicht sofort | Code unverändert (`POLL_COOLDOWN_MAX_SECONDS` 120 s) | accept bleibt |
| L-35-06 httpx-INFO mit fileid/userId | S3 live mit Positivkontrolle | **geschlossen** durch 36-02 |

## Performance

Gemessen am 21.10.2026 auf dem Entwicklungsrechner (Windows, Python 3.13 der
uv-Umgebung), seriell, nach dem Stopp des Host-Backends für P1, P2 und P4; P3
und P5 gegen 8090 mit laufendem Backend. Skripte und Rohdaten im Scratch der
Session (`p2_count.py`, `p2.jsonl`, `p3_cycle.py`, `p3-ohne.jsonl`,
`p3-mit.jsonl`), nicht im Repo.

### P1 Laufzeit je Korpusfall

- **Lokal:** `uv run python -m pytest tests/test_phase36_hostile_corpus.py
  --durations=0`: 64 passed in 10,10 s. Langsamster Korpusfall
  `package[docx]` **0,71 s** (erster Fall der Familie, enthält den Start des
  Kinds), dann `ratio-about-150` 0,51 s, `honest-large-jpeg` 0,31 s,
  `tiff-of-100000-ifds` 0,24 s, `xlsx-of-a-million-records` 0,15 s. Länger
  sind nur die zwei Prüfungen über den ganzen Korpus (Log-Sonde 3,02 s,
  Determinismus 1,84 s), keine davon ist ein Fall.
- **CI (ubuntu, RLIMIT_AS):** `python.yml` ruft pytest ohne `--durations`, das
  Log nennt keine Einzelzeiten. Jeder Fall prüft seine Frist selbst
  (`named_and_quick`: `ran.seconds < case.seconds`, `CASE_SECONDS` = 30 s, für
  `tiff-of-100000-ifds` 5 s); Python gates 39552834732 (d120f953, letzter Lauf
  mit geändertem Extraktor) und 39563847299 (7a4c3b2c) grün.
- **Urteil:** Maximum 0,71 s gegen 30 s; in Ordnung.

### P2 Kosten der Vorzählung (F3)

Je Datei ein frisches Kind (`p2_count.py`), 20 Läufe von
`archive.count_central_directory(handle, size, limit=ARCHIVE_MAX_ENTRIES)`,
Spitzen-Arbeitsspeicher des Kinds über `GetProcessMemoryInfo`
(PeakWorkingSetSize; unter Linux nimmt das Skript `ru_maxrss`). Leerlauf des
Kinds mit denselben Importen: **26,9 MiB**. Im Repo liegen keine echten
PPTX/XLSX (`testdata/` hat nur DOCX/ODT bis 66 KB), deshalb die größten des
Lastkorpus `.dev/probe-live/loadcorpus` wie in 36-08.

| Datei | Größe | Einträge | p50 | p95 | max | Spitze |
|---|---|---|---|---|---|---|
| 00414-stellungnahme.pptx | 349 893 B | 22 | 0,049 ms | 0,103 ms | 0,271 ms | 27,1 MiB |
| 00378-bescheid.xlsx | 346 874 B | 7 | 0,048 ms | 0,124 ms | 0,372 ms | 27,1 MiB |
| 00410-vertrag.docx | 346 877 B | 4 | 0,040 ms | 0,097 ms | 0,292 ms | 27,1 MiB |
| testdata 34-zip-bombe.docx | 66 154 B | 3 | 0,037 ms | 0,076 ms | 0,194 ms | 27,0 MiB |
| Paket 10 001 Einträge (`package_with_entries`) | 470 087 B | 10 001 | 4,935 ms | 6,186 ms | 39,6 ms | 27,4 MiB |
| Paket 150 000 Einträge | 7 050 040 B | Abbruch bei 10 001 | 4,993 ms | 18,291 ms | 24,9 ms | 27,1 MiB |
| Paket 1 Mio. Einträge | 47 000 040 B | `OverLimit` (Verzeichnis > 8 MiB) | 0,137 ms | 0,387 ms | 0,637 ms | 27,2 MiB |

**Vorher/nachher:** derselbe Weg wie vor dem Fix (`zipfile.ZipFile(path)`)
im selben Kind: 1-Mio.-Paket **3 705 ms, Spitze 447,1 MiB**; 150 000 Einträge
544 ms, 89,1 MiB. Die Recherche maß im Linux-Image 454 MiB und 32 s (F3); die
Speicherzahl stimmt überein, die Zeit hängt an der Maschine. Nachher kostet
dieselbe Datei 0,4 ms (p95) und 0,3 MiB über dem Leerlauf. **Urteil:** F3
geschlossen, die Vorzählung kostet auf echten Dateien unter 0,4 ms (p95).

### P3 Nachlauf M-32-02 auf 8090

Je Zyklus ein eigener Prozess `Reconcile(min_interval_hours=0,
pause_seconds=0.0).run_once()` mit der Umgebung des Host-Backends;
OCS-Aufrufe gezählt an `nc_py_api._session.AsyncNcSessionBasic.ocs`
(gezählt, nicht geschätzt); Zeit per `perf_counter` um den Zyklus. Bestand:
3 Mounts (2, 3, 4), 481 Dateien.

| Lauf | Abwesend | Zeit | OCS-Aufrufe | Nachlauf-Zeile |
|---|---|---|---|---|
| ohne (3 Läufe) | 0 | 0,432 / 0,397 / 0,458 s | 8: stats 4, mounts 1, slice 3 | keine |
| 1 verschwunden (Storage 16, oc_storages vorhanden) + 1 gelöscht (49 Zeilen) | 2 | 0,689 s | 10: + `storages/gone` 1, + `requeue` 1 | `absent=2 gone=1 deselected=0 stamped=1 removed=1` |
| 300 gelöscht (je 1 Zeile) + 1 verschwunden | 301 | **19,007 s** | 310: + `storages/gone` **2** (256 + 45), + `requeue` **300** | `absent=301 gone=300 stamped=1 removed=300`, mit allen 300 IDs |
| nach Rückbau | 0 | 0,380 s | 8 | keine |

- Die Storage-Frage hält "höchstens ein Band je 256 abwesende Storages" (2 für
  301). Die Löschaufträge gehen je Storage einzeln: L-36-04. Die Zeile nennt
  alle IDs: L-36-03.
- Synthetische Zeilen (file_id 95 000 000 ff., Storages 16 und 900 001 ff.)
  über die Store-API angelegt, nach dem Abarbeiten der Löschaufträge per SQL
  wieder entfernt; Endstand lebend 2/3/4 = 59/371/49 wie vorher,
  `vanished_storages` leer.
- **Urteil:** im gewöhnlichen Fall +0,26 s und 2 Aufrufe; 300 gelöschte
  Storages in einer Runde 19 s, einmalig, nachts und hinter dem Ruhetor.
  In Ordnung, mit den zwei LOWs.

### P4 Pixel-Zweig

- **Quelltext:** `_refused_by_pillow` steht nur im `except
  Image.DecompressionBombError` von `extract_image` (Zeile 266), das zweite
  `Image.open(path, mode="r")` nur dort.
- **Gezählt** (Image.open umwickelt): normales PNG 800 x 600 **1** Öffnung,
  `honest_large_jpeg` (über 100 MP, ehrlich) 2, `png_bomb` 2.
- **Zeit** `png_bomb` im Prozess, 20 Läufe: p50 **0,32 ms**, p95 0,93 ms, max
  7,03 ms; Urteil `skipped/blocked_malicious/image_pixels`.
- **Urteil:** in Ordnung.

### P5 Datenbankabfragen je Poll

- **Messung:** `occ config:system:set query_log_file --value=/tmp/q3612.log`,
  `query_log_file_requestid yes` (später `query_log_file_backtrace yes` für
  die Zuordnung), 1 Aufwärmaufruf, dann 5 x `GET
  /index.php/apps/findling/admin/overview` als admin mit Session, je 87 bis
  131 ms. Abfragen je Aufruf nach Request-ID: **169, 169, 169, 170, 169**
  (34-AUDIT: 186).
- **Zuordnung (Backtrace):** 126 der 172 Zeilen eines Aufrufs kommen über
  `AdminViewService::examples` → `PathResolverService::describeMany` (81
  Beispielzeilen in 12 Gruppen, je `getMountsForFileId` plus Nutzer), der Rest
  sind Zähler (`oc_findling_file_state` 16, `oc_findling_queue` 12) und Kern.
  Obergrenze: `EXAMPLES_PER_GROUP` = 20 je Gruppe, Gruppen aus der
  geschlossenen Liste (25 Gründe); hochgerechnet mit 1,56 Abfragen je
  Beispielzeile höchstens rund 830 je Aufruf.
- **Urteil: kein Release-Blocker.** Gedeckelt durch Konstanten (T-04-34), nur
  während eine Admin-Seite offen ist (Takt 5 s aktiv, 30 s im Leerlauf), kein
  Nutzerpfad, gemessene Antwort 0,1 s. Bleibt Deferred für v1.6
  (Bündelung der Mount-Abfragen in `describeMany`), keine Owner-Frage.
- **Rückbau:** `config:system:delete` für alle drei Schlüssel,
  `config:system:get query_log_file` Exit 1, `/tmp/q3612.log` gelöscht.

## Befunde

### L-36-01 (LOW): Fünf verankerte PHP-Formprüfungen ohne `D` lassen ein abschließendes `\n` durch

- **Ort:** `PageController.php` 480 (`similarId`) und 1028 (Fingerabdruck),
  `AdminViewService.php` 312 (`REASON_PATTERN`) und 322
  (`ERROR_CLASS_PATTERN`), `ExAppService.php` 269 (`VERSION_PATTERN`).
- **Beleg:** live `?similar=14%0A` = Ähnlich-Ansicht von 14; der Rest der App
  schreibt dieselbe Regel mit `$/D` (`AdminViewService` 2686, `ProbeService`
  523, `SettingsService` 493/599).
- **Einordnung:** kein Schaden nachweisbar (der Cast entfernt den Umbruch, die
  Werte landen per `textContent`), aber jede der fünf Prüfungen steht an einer
  Vertrauensgrenze und sagt mehr zu, als sie hält.
- **Test:** `test_every_anchored_php_form_check_ends_at_the_very_end`
  (xfail strict, L-36-01) mit Positivkontrolle
  `test_the_dollar_probe_tells_the_two_spellings_apart`.

### L-36-02 (LOW): Die ID-Parser der Container-Routen nehmen nicht kanonische Ziffernfolgen

- **Ort:** `ReconcileController::storageIdList` (neu in 36-03) und dieselbe
  Form in `QueueController::positiveId` (Bestand).
- **Beleg:** S2, 20 Ziffern ergeben `"gone":[9223372036854775807]`, `014`
  ergibt 14.
- **Einordnung:** nur der eigene Container erreicht die Routen (S1), er sendet
  nur Zahlen aus state.db und schneidet die Antwort auf die gefragten IDs
  (36-04); kein Index-Schaden. Die Route antwortet aber auf eine Frage, die
  nicht gestellt wurde.
- **Test:** `test_the_id_parsers_of_the_container_routes_take_canonical_numbers_only`
  (xfail strict, L-36-02).

### L-36-03 (LOW): Die Zeile des Storage-Nachlaufs nennt alle Storage-IDs ungekürzt

- **Ort:** `worker/reconcile.py`, `_sweep_vanished`, Logzeile "storage sweep".
- **Beleg:** P3 (Task 2): eine Runde mit 300 gelöschten Storages schrieb eine
  Zeile mit allen 300 IDs; ein gestempelter Storage steht 30 Tage lang in jeder
  fälligen Runde in "waiting".
- **Einordnung:** keine personenbezogenen Daten (Storage-IDs sind erlaubt,
  T-36-17), aber eine Logzeile ohne Obergrenze.
- **Test:** `test_the_sweep_line_names_a_bounded_number_of_storages`
  (xfail strict, L-36-03; rot belegt: 301 IDs genannt).

### L-36-04 (LOW): Ein Löschauftrag je gelöschtem Storage

- **Ort:** `_sweep_vanished` ruft `_hand_over` je Storage; 300 Storages mit je
  einer Datei sind 300 `POST .../requeue`.
- **Beleg:** P3, 19,0 s für die Runde mit 300 gelöschten Storages gegen 0,4 s
  ohne.
- **Test:** siehe Entscheidung (Task 3).

## Was gegengeprüft wurde, nicht nur gelesen

| Prüfung | Verfahren (anders als die Umsetzung) | Ergebnis |
|---|---|---|
| S1 | curl mit drei falschen Kopfvarianten und Positivkontrolle | 412/412/412, Kontrolle 200 |
| S2 | 16 Eingabeformen per curl gegen die echte Route | kein 500; L-36-02 |
| S3 | Live-Log unter info und debug (Positivkontrolle) | 0 userId-Zeilen, unter debug 1 |
| S4 | Syntaxbaum statt grep, PHP-Muster mit PCRE-Semantik ausgewertet | 20 Fundstellen sauber; L-36-01 |
| S5 | Syntaxbaum plus Rekorder statt der Bestandstests | nur "walked" erreicht den Nachlauf |
| S6 | Syntaxbaum über alle Schreiböffnungen | eine, nummeriert |
| S7 | `uses:` per grep gegen 40-stellige SHAs statt des Pin-Tests | nur lokale Action unpinned |
| B2 | echte Bomben aus den Generatoren durch den echten Poller | `image_pixels`, `zip_ratio` auf der Diagnose |
