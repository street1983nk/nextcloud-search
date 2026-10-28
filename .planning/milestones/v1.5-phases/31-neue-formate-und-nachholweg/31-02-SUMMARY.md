---
phase: 31-neue-formate-und-nachholweg
plan: 02
subsystem: Urteilskette (Reason-Codes, Companion-Generation, l10n)
tags: [fmt-02, fmt-03, fmt-06, archive_limit, unsupported_variant, verdicts-generation, l10n, e-h2]
requires:
  - phase: 31-01
    provides: "Pins olefile, xlrd, pillow-heif (für die Formate, auf die sich die Texte beziehen)"
provides:
  - "Reason.ARCHIVE_LIMIT (skipped) in errors.py, store/repo.py, FileStateService REASONS und STATE_REASONS, AdminViewService REASON_TEXT"
  - "VERDICTS_GENERATION 3 auf beiden Seiten, KNOWN_VERDICTS_GENERATIONS {2, 3} im Container, Fallback-Tabelle je Generation"
  - "öffentliche SKIPPED_FALLBACK_WITHOUT_SIGNAL (drei Paare, ohne archive_limit) für das gezielte Neu-Urteil in 31-11"
  - "recheck_1_4_0 startet bei Generation 2 und 3"
  - "fünf Sätze (zwei neu, drei geändert) in 16 Katalogen und fünf l10n-Dokus"
  - "docs/formats.md mit den Abschnitten Upgrade order und Skip codes"
  - "Driftgegenprobe REASON_TEXT gegen die Python-Codeliste"
affects: [31-04 .eml (archive_limit bleibt ZIP), 31-05 .doc und 31-06 .xls (unsupported_variant), 31-08 ZIP (archive_limit), 31-11 Nachholweg (SKIPPED_FALLBACK_WITHOUT_SIGNAL), 31-14 docs/formats.md, 36 REL-05 (Owner-Abnahme Wortlaut)]
tech-stack:
  added: []
  patterns: ["Fallback je Generation statt exakt einer Generation", "ein Testfall je Satz und Katalog (parametrisiert, ids mit Dateinamen)"]
key-files:
  created:
    - docs/formats.md
  modified:
    - backend/src/findling/extract/errors.py
    - backend/src/findling/store/repo.py
    - backend/src/findling/nc/queue.py
    - backend/src/findling/worker/poller.py
    - backend/src/findling/worker/recheck.py
    - backend/tests/test_queue_client.py
    - backend/tests/test_poller.py
    - backend/tests/test_extract_errors.py
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
    - php/lib/Controller/ProfileController.php
    - php/lib/Service/FileStateService.php
    - php/lib/Service/AdminViewService.php
    - php/tests/Unit/ProfileControllerTest.php
    - php/l10n/*.js, php/l10n/*.json (16 Dateien)
    - docs/l10n-dutch.md, docs/l10n-french.md, docs/l10n-italian.md, docs/l10n-portuguese.md, docs/l10n-spanish.md
    - docs/store-listing.md
    - backend/pyproject.toml (Nebencommit)
decisions:
  - "Sichtbarer Wortlaut sagt ZIP file / ZIP-Datei statt des Plan-Vorschlags mit dem gesperrten Wortstamm (Vokabelregel E-H2); archive_limit gilt laut 31-04 nur für ZIP"
  - "Der Codename archive_limit steht wegen E-H2 nicht in docs/store-listing.md; dort Zeile 'ZIP-Grenzcode', Codename und Sätze in docs/formats.md Abschnitt Skip codes"
  - "archive_limit reist an Generation 2 und ohne Signal als skipped too_large, in der failed-Liste als corrupt"
  - "_wire_reason liest eine unbekannte Generation wie kein Signal (Tabelle None)"
metrics:
  duration: "ca. 85 min (davon 11 min volle Suite lokal, ca. 25 min CI)"
  completed: 2026-10-11
  tasks: 2
  files: 39
---

# Phase 31 Plan 02: archive_limit, allgemeineres unsupported_variant und Verdict-Generation 3 Summary

Der Skip-Code `archive_limit` steht in allen vier Codelisten und mit Label und Hilfe in allen 16 Katalogen und fünf l10n-Dokus; `unsupported_variant` und die Hilfe von `mime_not_allowed` sind für die Formate von 1.5 neu gefasst; die Companion meldet Generation 3, der Container spricht mit 2 und 3 und schickt `archive_limit` nur an eine 3-Companion.

## Task 1: Generation 3 mit weiter gültiger 2

- queue.py: `VERDICTS_GENERATION = 3`, `KNOWN_VERDICTS_GENERATIONS = frozenset({2, 3})`, `_verdicts` gibt jeden Wert dieser Menge zurück (bool, str, float, andere Zahlen sind None). Öffentlich `SKIPPED_FALLBACK_WITHOUT_SIGNAL` (system_file und legacy_format -> mime_not_allowed, unsupported_variant -> image_not_ocrable). `_SKIPPED_FALLBACK_BY_GENERATION`: 3 leer, 2 archive_limit -> too_large, None = die drei Paare plus archive_limit -> too_large; `_FAILED_FALLBACK_BY_GENERATION`: 3 leer, 2 archive_limit -> corrupt, None alle vier -> corrupt. Alle Tabellen als MappingProxyType. `_wire_reason(reason, verdicts, tables)` wählt nach Generation. Kommentarblock nennt beide Mischfenster, docs/formats.md und 31-11.
- Die zwei weiteren Stellen (acknowledge, companion_choice) verglichen nur über `_wire_reason` bzw. `_verdicts`; ihre Docstrings sind auf die Menge gezogen.
- poller.py: `choice.verdicts in KNOWN_VERDICTS_GENERATIONS` startet recheck_1_4_0; recheck.py-Docstring nachgezogen. Kein Haken für 31-11.
- PHP: `VERDICTS_GENERATION = 3` samt Docblock (3 = archive_limit und die Formate von 1.5), ProfileControllerTest erwartet 3 (sieben Stellen).
- docs/formats.md neu: Abschnitt "## Upgrade order" (Backend zuerst, warum, was bei umgekehrter Reihenfolge passiert, Heilung durch `recheck_1_5_0`).
- RED (einzeln, `-p no:randomly`): **25 failed, 51 passed**; rot u. a. `test_the_container_knows_the_generations_2_and_3`, `test_a_companion_announcing_a_known_generation_reads_as_that_generation[3]`, `test_verdicts_is_a_closed_set_of_two_generations[3-3]`, `test_without_the_signal_no_new_code_leaves_the_container` (3 Fälle), `test_towards_generation_2_only_archive_limit_falls_back`, `test_towards_generation_3_every_code_travels_unchanged`, `test_the_fallback_without_signal_is_public_and_holds_the_three_pairs_of_1_4`, beide Tabellen-Tests, je drei Fälle der STATE_REASONS-Gegenprobe pro Liste (`AttributeError: ... '_FAILED_FALLBACK_BY_GENERATION'`), `test_every_other_code_travels_unchanged` (4), `test_the_upgrade_order_is_documented` (FileNotFoundError), `test_with_the_signal_a_corrupt_sidecar_ends_as_system_file_once[3]`. Der Fall `[2]` war grün (bestehendes Verhalten, bleibt Absicherung).
- GREEN: 338 passed, 1 skipped über test_queue_client, test_poller, test_profile_wire, test_recheck; einzig `test_the_new_codes_are_skipped_only_in_the_companion` blieb rot bis Task 2 (archive_limit fehlte in PHP).

## Task 2: archive_limit, Labels, 16 Kataloge, fünf Dokus, Codetabelle

- errors.py `ARCHIVE_LIMIT = "archive_limit"` in der skipped-Gruppe, Kommentar von UNSUPPORTED_VARIANT allgemein ("an image encoding, Word 95, BIFF before 5"); repo.py, FileStateService REASONS und STATE_REASONS; AdminViewService REASON_TEXT.
- Endgültige englische Sätze:
  - archive_limit: "ZIP file over the safety limits" / "None. ZIP files that are nested too deep, too large, too densely packed or hold too many files are skipped so the container keeps running."
  - unsupported_variant: "Variant of this format that cannot be read" / "None. The file uses a variant or an encoding Findling cannot read, for example Word 95 or an unusual image encoding."
  - mime_not_allowed Hilfe: "None. Findling reads PDF, Office, OpenDocument, text, mails, ZIP files and images."
- Deutsch (de und de_DE gleich): "ZIP-Datei über den Sicherheitsgrenzen", "Keine. ZIP-Dateien, die zu tief verschachtelt, zu groß oder zu dicht gepackt sind oder zu viele Dateien enthalten, werden übersprungen, damit der Container weiterläuft.", "Variante dieses Formats, die nicht gelesen werden kann", "Keine. Die Datei nutzt eine Variante oder Kodierung, die Findling nicht lesen kann, zum Beispiel Word 95 oder eine ungewöhnliche Bildkodierung.", "Keine. Findling liest PDF, Office, OpenDocument, Text, Mails, ZIP-Dateien und Bilder." fr, es, it, nl, pt_PT, pt_BR im Wortschatz des jeweiligen Katalogs (conteneur, contenedor, contenitore, container, contentor, contêiner; ficheiro gegen arquivo).
- Alte Schlüssel ("Image variant that cannot be read", alter unsupported_variant-Hilfetext, alter mime_not_allowed-Hilfetext) aus allen 16 Dateien und fünf Dokus entfernt; de.json 300 -> 302 Schlüssel.
- Tests: `test_archive_limit_of_plan_31_02_is_a_decision_and_never_a_failure`, `test_every_reason_code_has_a_label_and_a_remedy_on_the_status_page` (neu: REASON_TEXT gegen die Python-Codeliste), `test_the_catalogue_list_holds_all_sixteen_files`, `test_the_reason_sentence_of_plan_31_02_stands_translated_in_the_catalogue` (5 x 16 = 80 Fälle, deutsche Werte zusätzlich ohne gesperrten Wortstamm), `test_the_reason_sentences_of_plan_31_02_stand_in_the_service`, `test_every_language_table_names_the_reason_sentences_of_plan_31_02` (5 Dokus).
- RED: `-k reason_sentence` **86 failed** (80 Katalog-Fälle, Service, 5 Dokus), dazu rot `test_archive_limit_of_plan_31_02_...` und `test_the_german_catalogue_covers_both_german_language_codes` (Schlüsselzahl).
- Gegenproben für die vorher grünen Tests: Katalogtupel ohne `pt_BR.js` -> `assert 15 == 16`; REASON_TEXT ohne archive_limit-Zeile -> `Extra items in the right set: 'archive_limit'`; de.json-Wert mit gesperrtem Wortstamm -> `[archive_limit-label-de.json]` rot. Jeweils zurückgesetzt.
- collect-only `-k reason_sentence`: 86 Tests, davon 80 `test_the_reason_sentence_of_plan_31_02_stands_translated_in_the_catalogue[<sentence>-<datei>]`, z. B. `[archive_limit-help-de.json]`, `[unsupported_variant-label-pt_BR.js]`.
- `grep -l "ZIP file over the safety limits" php/l10n/*` -> 16 Dateien; `grep -rn "Image variant that cannot be read" php/ docs/l10n-*.md` -> leer.
- docs/store-listing.md Teil 4: unsupported_variant nachgezogen, Zeilen mime_not_allowed und "ZIP-Grenzcode", Vermerk "Wortlaut Entwurf Phase 31, Owner-Abnahme bei REL-05". docs/formats.md Abschnitt "## Skip codes" mit Codename und Fallback-Hinweis.
- Baumhashes im selben Commit: PACKAGE_TREE_HASH_TODAY `d6062645...bb32a0d` (74 Dateien), PHP_TREE_HASH_TODAY `97a83197...24c3f3af` (90 Dateien), Journalabsätze "plan 31-02" bei beiden.

## Nebencommit

`0b78d646` chore: Kommentar über dem Pin in backend/pyproject.toml nennt jetzt 0.33.0 (2026-09-24, Upload-Datum aus uv.lock) statt 0.32.0 (2026-06-16). Außerhalb von backend/src/findling, Baumhash-Tests grün (4 passed), `uv lock --check` ok, 44 Tests, die pyproject lesen, grün.

## Commits

| Commit | Inhalt |
|---|---|
| 0b78d646 | chore: semantic-text-splitter comment names the pinned 0.33.0 |
| aa498caf | feat(31-02): archive_limit, a wider unsupported_variant and verdict generation 3 |

## Gates und CI

- Lokal vor aa498caf: ruff check grün, ruff format (201 Dateien) grün, pyright latest 0 Fehler, vulture grün, volle Suite **5008 passed, 25 skipped** (635,6 s; einzige Warnung ist die bekannte PIL-EXIF-Warnung in test_ocr).
- Push `ebcc4092..aa498caf` (beide Commits), alle success: Python gates **38096296384** (5019 passed, 14 skipped), PHP and store metadata gates **38096296404**, Integration **38096296387**, Resilience **38096296386**, HaRP deploy **38096296437**, Multi-arch image **38096296444**, Security scans 38096296410, OpenSSF Scorecard 38096296405.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan-Wortlaut verletzte die Vokabelregel E-H2**
- **Found during:** Task 2 (vor dem Schreiben der Kataloge)
- **Issue:** Die vorgeschlagenen Sätze ("Archive over the safety limits", "ZIP archives", deutsch "Archiv über den Sicherheitsgrenzen") tragen den gesperrten Wortstamm. test_public_artifacts sperrt deutsche Formen in docs/ (die deutsche Spalte der l10n-Dokus), test_store_metadata sperrt den Stamm in docs/store-listing.md in jeder Schreibung, auch englisch und im Codenamen.
- **Fix:** Sichtbare Sätze sagen "ZIP file" / "ZIP-Datei" (archive_limit gilt laut 31-04 nur für ZIP), in allen Sprachen. In store-listing.md steht der neue Code als "ZIP-Grenzcode" mit Verweis; Codename und Sätze stehen in docs/formats.md (englisch, die Regel fängt dort nur deutsche Formen). Der Plan-Akzeptanztest `grep -l "Archive over the safety limits"` ist deshalb sinngemäß mit "ZIP file over the safety limits" erfüllt (16 Dateien). Spanisch ("archivo") und Italienisch: es nutzt das übliche Wort für Datei (Ausnahmeliste vorhanden), it nutzt "file ZIP" und bringt keinen neuen Treffer.
- **Files modified:** wie Task 2
- **Commit:** aa498caf

**2. [Rule 2] Driftgegenprobe REASON_TEXT**
- **Found during:** Task 2
- **Issue:** Der Plan nannte eine Driftgegenprobe gegen REASON_TEXT; es gab keine, ein Code ohne Zeile wäre auf der Statusseite als "Unknown reason" erschienen.
- **Fix:** `test_every_reason_code_has_a_label_and_a_remedy_on_the_status_page`.
- **Commit:** aa498caf

**3. Zusatz: docs/formats.md Abschnitt "Skip codes"**
- Nötig als Ort für den Codenamen (siehe 1); 31-14 erweitert die Datei weiter.

## Known Stubs

Keine. Die Sätze von archive_limit und die Generation 3 sind verdrahtet; erzeugt wird archive_limit erst vom ZIP-Extraktor (31-08), das ist Planfolge, kein Stub.

## Threat Flags

Keine neue Fläche. T-31-03 (Fallback je Generation, Test liest PHP STATE_REASONS je Zielcode und Generation), T-31-04 (geschlossene Menge {2, 3}, Tests mit bool/str/float/0/1/4), T-31-05b (Upgrade-Reihenfolge dokumentiert, öffentliche Ersatztabelle für 31-11) und T-31-05 (Wortlaut als Entwurf markiert) sind umgesetzt.

## Requirements

FMT-02, FMT-03 und FMT-06 stehen im Frontmatter, sind für Nutzer aber erst mit den Extraktoren (31-04 bis 31-08), der Freischaltung (31-10) und dem Nachholweg (31-11) da. Nicht als Complete markiert.

## Offene Punkte

- Owner-Abnahme der fünf Sätze (en/de, sechs weitere Kataloge folgen) bei REL-05; Entwurf in docs/store-listing.md Teil 4 und docs/formats.md.
- Vorbestehend, außerhalb des Plans: Die Ausnahmegründe in test_public_artifacts.py nennen für l10n-spanish.md "61" und für l10n-italian.md "nine" Treffer; gezählt waren vor diesem Plan schon 79 und 10. Nicht angefasst.
- Vorbestehend: der Docblock von REASON_TEXT spricht von "Twenty codes"; nicht angefasst.
- 31-11 nutzt `SKIPPED_FALLBACK_WITHOUT_SIGNAL` für das gezielte Neu-Urteil.

## Self-Check: PASSED

docs/formats.md und diese SUMMARY vorhanden; Commits 0b78d646 und aa498caf in der Historie, origin/main auf aa498caf; alle acht CI-Läufe success.
