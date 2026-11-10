---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 24
subsystem: backend/worker, backend/nc, backend/api, backend/tests
tags: [D-43-14, D-43-15, D-43-17, OE-5, A-1, A-2, doc-key, counting, generation]
requires: [43-23]
provides: [DOC_KEY_GENERATION 2 mit einmaligem Neuaufbau, stored_generation, Generationssperre in POST /coverage vor Zählung und Cache, docKeyFormat 2 als Pflicht im Body und in jeder Antwort von POST /coverage, docKey im Auftrag nur neben docKeyFormat 2, format 2 als Pflicht in der Antwort von GET /reconcile/doc-keys, DocKeyAnswer.format_mismatch, Formatparität PHP und Container]
affects: [43-25, 43-26, 43-27]
tech-stack:
  added: []
  patterns: [Formatmarke an jedem Übergang als echte Ganzzahl, Sperre vor Zählung und Cache, fremdes Format wie fehlende Route]
key-files:
  created:
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-24-SUMMARY.md
  modified:
    - backend/src/findling/worker/doc_keys.py
    - backend/src/findling/nc/files.py
    - backend/src/findling/nc/queue.py
    - backend/src/findling/api/coverage.py
    - backend/tests/test_doc_keys.py
    - backend/tests/test_coverage_endpoint.py
    - backend/tests/test_share_identity_cases.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Die Sperre steht in _answer direkt nach dem Lesen von state.db: trägt doc_key_backfill_after nicht Generation 2 und hat die Anfrage lebende Zeilen, lautet die Antwort counting mit docKeysMissing gleich der Zahl dieser Zeilen, ohne coverage_counts und ohne Blick in den Cache; ohne lebende Zeilen der Anfrage bleibt es bei der Zahl 0"
  - "Die Route liest die Generation über stored_generation, dieselbe Lesung wie der Worker (_read_mark); ein fehlender, unlesbarer oder fremder Wert (auch eine höhere Generation) zählt nicht"
  - "docKeyFormat im Body ist Literal[2] plus ein Vor-Validator auf type(value) is int, weil ein strict Literal 2.0 als 2 annimmt"
  - "Dritte Formatkonstante DOC_KEY_FORMAT in nc/files.py (die Leseschicht importiert nichts aus worker); der Paritätstest hält DocKeyService::DOC_KEY_FORMAT, DOC_KEY_GENERATION, _DOC_KEY_FORMAT, DOC_KEY_FORMAT und den Katalog zusammen"
  - "Eine Backfill-Antwort ohne format 2 verwirft die ganze Frage (kein Schlüssel, kein absent), auch wenn nur ein Band abweicht; der Worker wartet mit demselben Cooldown wie beim 404 und einer eigenen Logzeile"
  - "Ein Auftrag mit anderem oder ohne Format trägt doc_key None; der Speicher schreibt dann nichts und löscht nichts (COALESCE aus 43-16)"
metrics:
  started: 2026-11-10T04:13:21Z
  completed: 2026-11-10T04:35:00Z
  tasks: 2
  files: 8
---

# Phase 43 Plan 24: Dokumentschlüssel Generation 2 mit Sperre und Formatmarke

Der Container zieht auf Format 2 nach: DOC_KEY_GENERATION ist 2, ein Meta-Wert der Generation 1 (rc.1) oder ein fehlender (1.6.2) setzt in der ersten Runde einmal alle doc_key auf NULL und baut sie neu auf. POST /coverage zählt nichts, solange der Meta-Wert nicht Generation 2 trägt, geprüft vor jeder Zählung und vor dem Cache, auch hinter einer Backup-Pause. Ein docKey aus einem Auftrag, eine Antwort von GET /reconcile/doc-keys und ein Body von POST /coverage gelten nur mit der Ganzzahl 2 als Format.

## Tasks

| Task | Inhalt | Commit |
|------|--------|--------|
| 1 | RED: Generation 2, Generationssperre, drei Formatmarken, Parität, Suchverbot | 4c5f4b3c |
| 2 | GREEN: doc_keys.py, files.py, queue.py, coverage.py, Paket-Baumhash | 2a30c4bf |

## Belege

- **Freigabe:** `Freigabe Entscheid 43-21 OE-5: "Wie empfohlen" (2026-11-09 10:36, Claude Code Terminal) Entscheid: a` steht in 43-FREIGABEN.md (Zeile 128), vor dem ersten Schritt geprüft.
- **RED lokal** (test_doc_keys, test_coverage_endpoint, test_share_identity_cases): 39 failed, 193 passed. Alle 39 enden in AssertionError, kein Sammelfehler, kein ERROR. Rot sind nur neue Tests; die Nachbarn test_phase43_audit, test_coverage_counts, test_measurement_scripts: 612 passed. Die verify-Zeile des Plans (sieben benannte Tests) endet mit Exitcode 1.
- **GREEN lokal**, vier Läufe mit Modulauswahl, je mit timeout 540:
  - A (test_doc_keys, test_coverage_endpoint, test_coverage_counts, test_share_identity_cases, test_measurement_scripts, test_phase40_audit, test_phase43_audit, test_store_metadata, test_changelog_translations, test_allowlist_parity, test_php_trust_boundary, test_admin_ui_contract): 1284 passed, 7 skipped; nach der Gegenprobe wiederholt: 1284 passed, 7 skipped.
  - B (test_queue_client, test_files_client, test_backup_pause, test_main_lifespan, test_exapp_surface, test_semantic_boundary, test_probe_endpoint, test_reconcile, test_reconcile_vanished, test_recheck, test_catchup, test_phase41_audit, test_phase36_audit): 574 passed.
  - C (test_poller, test_upgrade_seed_steps, test_embedding_runner, test_embedding_track, test_acl_prefilter, test_precision_wiring, test_probe_run, test_profile_wire, test_phase31_audit): 685 passed, 3 skipped.
  - D (test_launch_hardening): 6 passed.
  - Kein Modul hing. Zusammen 35 Module, 2549 passed, 10 skipped.
- **Erster GREEN-Versuch:** 4 failed, 268 passed. Ein echter Befund (2.0 ging als docKeyFormat durch, siehe Deviation 1) und eine falsche Erwartung in einem RED-Test (Deviation 3).
- **Gegenprobe 1 (Umsetzung zurückgesetzt):** die vier Quelldateien per `git show HEAD:<Datei>` auf den Stand des RED-Commits gesetzt, vier Module (test_doc_keys, test_coverage_endpoint, test_share_identity_cases, test_phase43_audit): 62 failed, 186 passed. Danach aus der Sicherung zurückgespielt, sha256sum -c viermal OK.
- **Gegenprobe 2 (18 gezielte Mutationen, je einzeln, anderes Muster als die Umsetzung):** keine Sperre, Sperre nur unter der Schwelle (hinter dem Cache), Sperre auch ohne Zeilen, docKeysMissing aus den Zeilen ohne Schlüssel statt der Anfrage, docKeyFormat im Body optional, ohne Ganzzahlprüfung im Body, Antwort ohne Format, Auftragsschlüssel ohne Formatprüfung, Auftragsformat nur per Vergleich (2.0), Auftragsformat 1, Backfill-Antwort ohne Formatprüfung, Backfill-Format nur per Vergleich, fremdes Format hält die Runde nicht an, falsche Logzeile, Generation 1, Meta-Wert vor dem Reset, kein Reset, stored_generation sagt immer 2. Ergebnis: 18 von 18 rot, 0 Überlebende. Danach cmp der vier Dateien gegen die Sicherung identisch, `git diff` vor und nach der Gegenprobe byteweise gleich, erst dann committet.
- **Python-Gates** vor beiden Commits: ruff check grün, ruff format 257 Dateien sauber, pyright 0/0/0 (PYRIGHT_PYTHON_FORCE_VERSION=latest), vulture rc 0 (als `vulture src tests --min-confidence 80` und in der Form des Plans).
- **Paket-Baumhash:** 75212e53 -> 5b1ace068d56ec458fbc4241dfecaf3e11ae63e0c4017ba19fba9e7d4d359af2, 83 Dateien, keine Datei kam oder ging. Rezept 40b-baumhash.py und unabhängig find, sort, tr -d '\r', sha256sum: beide 5b1ace06. Positivkontrolle über `git archive HEAD` vor dem Schritt mit beiden Wegen: 75212e53 (der Wert des Journals). PHP-Paare unberührt.
- **STOPP-Regel:** kein neuer Meta- oder AppConfig-Schlüssel, keine Migration, keine Route. `git diff --quiet 37b518d6 -- schema.sql vectors.sql index/schema.py` ist leer, SCHEMA_VERSION bleibt "2", STORE_SCHEMA_MARK unverändert; kein Diff unter php/ und backend/appinfo.
- **Sicherheit (T-43-72 bis T-43-75):** Sperre vor Zählung und Cache mit eigenen Tests (auch mit einer zuvor gecachten Zahl); 422 vor note_coverage_call (der echte Schalter _COVERAGE_SEEN bleibt nach zwei 422 ungesetzt); doc_key und docKey kommen in api/search.py, api/snippets.py, api/similar.py und index/ nicht vor (mit Positivkontrolle auf store/repo.py und nc/queue.py); die neue Logzeile trägt nur die Sekundenzahl, der Test prüft alle Zeilen der Runde auf Hex und Pfad.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Ein strict Literal[2] nimmt 2.0 an**
- **Found during:** Task 2, erster GREEN-Lauf (test_coverage_without_doc_key_format_is_422_before_any_database[float] blieb rot).
- **Issue:** Der Plan nimmt an, strict lasse 2.0 scheitern. Pydantic prüft ein Literal über Gleichheit, 2.0 kam mit 200 durch.
- **Fix:** Vor-Validator `_the_format_is_a_whole_number` (type(value) is int) am Feld docKeyFormat.
- **Files modified:** backend/src/findling/api/coverage.py
- **Commit:** 2a30c4bf

**2. Dritte Formatkonstante in nc/files.py**
- Der Plan nennt die Konstanten in doc_keys.py und queue.py. Die Leseschicht nc/files.py prüft `format` selbst und importiert nichts aus worker, daher `DOC_KEY_FORMAT: Final = 2` neben DOC_KEY_BAND. Der Paritätstest hält alle vier Zahlen und den Katalog zusammen.

**3. Tests im GREEN-Commit angepasst**
- `_post` in test_coverage_endpoint.py setzt docKeyFormat 2 in Objekt-Bodies ohne Format (so scheitert jeder Grenztest an seiner Grenze und nicht am fehlenden Format; test_phase43_audit.py nutzt denselben Helfer und blieb unverändert), ANSWER_KEYS bekommt docKeyFormat. Beides hätte im RED-Commit die bestehenden Tests rot gemacht; der Plan verlangt dort "der Rest der Module bleibt grün".
- test_a_rc1_mark_rebuilds_every_key_once erwartete nach der Füllrunde den Meta-Wert "2:5:0"; richtig ist "2:0:0", weil der Cursor nach einem vollen Durchgang an den Anfang zurückgeht (R2, bestehendes Verhalten). Erwartung korrigiert, nicht die Umsetzung.
- Neuer Test test_the_keys_are_gone_before_the_mark_says_generation_two für die Reihenfolge im Reset (Wahrheit 3 des Plans); er kam erst mit GREEN dazu.

**4. Zusätzliche Tests über die Liste des Plans hinaus (im RED-Commit)**
- test_a_cached_figure_is_not_answered_under_another_generation, test_a_state_without_rows_and_without_a_mark_answers_zeros, test_every_answer_names_the_format_of_the_keys. Die bestehenden Attrappen der Leseschicht und der Aufträge tragen ab RED `format: 2` bzw. `docKeyFormat: 2` (vor GREEN ohne Wirkung).

**5. Volltestsuite nicht gelaufen**
- Der Plan sieht die Volltestsuite in zwei Hälften vor. Nach Vorgabe des Koordinators nie ohne Modulauswahl (Hänger unter Windows); gelaufen sind die 35 oben genannten Module.

Sonst plangemäß. Keine STOPP-Regel berührt.

## Bekannte Grenzen und offene Punkte

- **E2E-Harness passt noch nicht zum Vertrag:** scripts/ci/coverage_e2e.sh baut den Body von POST /coverage in `coverage_body` (Zeile 758 bis 768) ohne docKeyFormat. Gegen diesen Container gibt das 422, die Prüfungen ab Zeile 1234, 1258 und 1623 lesen dann keine Antwort. Nicht geändert (außerhalb von files_modified); muss vor dem nächsten Dispatch in 43-25 oder 43-26 nachgezogen werden.
- **Dauer des Resets nicht gemessen:** reset_doc_keys ist ein UPDATE in einer Transaktion über alle Zeilen. Getestet mit 5 und 32 Zeilen, nicht mit den rund 491.000 von mbozem.
- **Nicht belegt:** ein echtes Update rc.1 -> 1.6.3 auf einer Instanz, der Mischbetrieb der Tabelle im Plan über die Leitung (nur als Einheitstests je Seite), ARM. Das ist E2E in 43-26 und Audit in 43-27.
- **PHPUnit nicht gelaufen:** keine PHP-Änderung, PHP-Baumhash unverändert. Die PHP-Seite des Vertrags ist mit 43-23 belegt.
- **Volle Python-Suite lokal nicht belegt**, erst in der CI nach einem freigegebenen Push.
- **Gewollte Folge der Sperre:** läuft der Backfill nie (Backend abgeschaltet, Companion von rc.1 ohne format), bleibt die Anzeige bei "wird gezählt"; eine Zahl aus alten Schlüsseln gibt es nicht.
- Nichts gepusht, kein Tag, kein Kommentar. main ist jetzt 21 Commits vor origin.

## Threat Flags

Keine neuen Flächen außerhalb des Bedrohungsmodells (T-43-72 bis T-43-75 umgesetzt und getestet). Keine neue Route, kein neuer Schlüssel, kein Schema.

## Self-Check: PASSED

- FOUND: backend/src/findling/worker/doc_keys.py (DOC_KEY_GENERATION: Final = 2, stored_generation), backend/src/findling/api/coverage.py (docKeyFormat, stored_generation), backend/src/findling/nc/queue.py (_DOC_KEY_FORMAT), backend/src/findling/nc/files.py (DOC_KEY_FORMAT, format_mismatch)
- FOUND: Commits 4c5f4b3c, 2a30c4bf
