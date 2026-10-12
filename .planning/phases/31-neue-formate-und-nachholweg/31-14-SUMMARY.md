---
phase: 31-neue-formate-und-nachholweg
plan: 14
subsystem: Doku (docs/formats.md, privacy.md, CHANGELOG), Store-Texte (beide info.xml), READMEs, Gate test_store_metadata.py
tags: [fmt-01, fmt-02, fmt-03, fmt-04, fmt-05, fmt-06, pol-02, d-31-04, d-31-05, store-text, rel-05, e-h2]
requires:
  - phase: 31-02
    provides: "Wortlaute archive_limit, unsupported_variant, mime_not_allowed; docs/formats.md mit Upgrade order und Skip codes"
  - phase: 31-08
    provides: "ZIP-Grenzwerte in config.py und im Messbericht"
  - phase: 31-11
    provides: "Nachholweg recheck_1_5_0, docs/reconcile.md"
  - phase: 31-13
    provides: "E2E-Beweis der fünf Formate und des Nachholwegs"
provides:
  - "docs/formats.md: je Format gelesen, nicht gelesen, Urteil; ZIP-Grenzen wie config.py; Typfilter; Nachholweg; Not supported"
  - "Dateitypen-Liste mit DOC, XLS, Mails (EML), ZIP ohne Texterkennung und HEIC in allen sechs Beschreibungen und drei READMEs"
  - "docs/store-listing.md: Entwurf v1.5.0 (Teil Phase 31), Owner-Abnahme offen bis REL-05"
  - "Gate: fünf Formatwörter je Liste (ganze Wörter), jede Liste zeichengleich zum Entwurf"
  - "CHANGELOG Unreleased, Privacy-Satz zu Mail-Kopfzeilen"
affects: [31-15 Audit, 36 REL-05 Owner-Abnahme Store-Text]
tech-stack:
  added: []
  patterns: ["Entwurf als eingezäunter Block je Sprache, erste Zeile = Überschrift, Gate liest die Sprache von der Überschrift"]
key-files:
  created:
    - .planning/phases/31-neue-formate-und-nachholweg/31-14-SUMMARY.md
  modified:
    - docs/formats.md
    - docs/privacy.md
    - CHANGELOG.md
    - php/appinfo/info.xml
    - backend/appinfo/info.xml
    - README.md
    - README.en.md
    - README.fr.md
    - docs/store-listing.md
    - backend/tests/test_store_metadata.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "ZIP-Zeile sagt ZIP files / ZIP-Dateien / Fichiers ZIP statt des Planer-Vorschlags mit dem gesperrten Wortstamm (E-H2 sperrt ihn in docs/store-listing.md in jeder Schreibweise, wie 31-02)"
  - "Französisch 'sans OCR' (kürzer, wie Planer-Vorschlag), Bildzeile bleibt 'reconnaissance optique'"
  - "Empfehlung an den Owner: kein sechster Grenzlisten-Eintrag für ZIP; Grenzliste bleibt bei fünf"
  - "Altes PowerPoint präzisiert: .ppt ist mime_not_allowed, nur PowerPoint-OLE unter .pptx-Namen bleibt legacy_format (dispatch.py)"
  - "docs/ocr.md unverändert: HEIC steht dort seit 31-07, eine Formatliste gibt es dort nicht"
metrics:
  duration: "ca. 60 min, davon ca. 27 min lokale Volltestläufe und ca. 20 min CI"
  completed: 2026-10-12
  tasks: 2
  files: 11
---

# Phase 31 Plan 14: Formate und Grenzen von 1.5, Store-Text-Entwurf für REL-05 Summary

docs/formats.md beschreibt je neuem Format, was gelesen wird, was nicht und welches Urteil folgt, dazu die ZIP-Grenzen (Werte gleich config.py), den Typfilter, den einmaligen Nachholweg und was nicht unterstützt wird. Die Dateitypen-Liste der sechs Store-Beschreibungen und der drei READMEs nennt DOC, XLS, Mails (EML), ZIP-Dateien ohne Texterkennung und HEIC; ein Gate hält jede Liste zeichengleich gegen den neuen Abschnitt "Entwurf v1.5.0 (Teil Phase 31)" in docs/store-listing.md. Die Owner-Abnahme ist offen (REL-05), eingereicht ist nichts.

## Task 1: Doku (f1aa9137)

- **docs/formats.md** neu gegliedert (englisch, Tabellen): Übersicht (Mimetyp, Leser, Typgruppe), Abschnitte Mail, ZIP mit "ZIP limits", Word, Excel, HEIC/HEIF, Old PowerPoint, Type filter, After the upgrade to 1.5, Upgrade order (unverändert), Skip codes (unverändert), Stale file cache size (unverändert, A8 bleibt), Not supported.
- Quellen je Aussage: mail.py-Docstring (Subject/From/To/Cc, Bcc und Received nicht, MAX_MAIL_PARTS 1000, RecursionError), archive.py/31-08 (Leser je Endung, Methoden 0/8/12/14, Urteile), legacy_doc.py (nFib < 0x00C1, fEncrypted), legacy_xls.py (BIFF5/8, ragged rows, Zellgrenze), image.py/31-07 (Optionen, too_large, ValueError), ocr.md (Speicherwerte), dispatch.py (.ppt), search-filters.md, reconcile.md, 31-03.
- ZIP-Werte gegen config.py geprüft (Python-Ausgabe): `10000 8.0 256.0 100 1.0 2 1000 0.75 50.0 200000` (Einträge, Verzeichnis MiB, entpackt MiB, Rate, Rate ab MiB, Tiefe, Mitglieder, Zeitanteil, max_file_bytes MiB, MAX_CELLS) = Tabelle in docs/formats.md.
- **docs/privacy.md**: ein Satz im Punkt Volltextindex: Betreff, Von, An, Cc samt Mailadressen und Anhangnamen sind durchsuchbar (Bcc und Anhanginhalte nicht), dieselbe Rechteprüfung.
- **CHANGELOG.md**: "## [Unreleased]" über 1.4.3 (nicht über 1.4.2 wie im Plan, 1.4.3 ist seit heute erschienen), Added (fünf Formate, Auszug mit innerer Datei, Nachholweg), Fixed (POL-02, F-29-03).
- Verify: `grep -c "archive_limit\|unsupported_variant"` 12, Unreleased Zeile 7, kein Gedankenstrich.

## Task 2: Store-Texte, READMEs, Entwurf, Gate (76ce8463)

### RED

Neue Fälle in test_store_metadata.py (4 am echten Baum, 6 Selbsttests). Lauf gegen den alten Stand (`-p no:randomly`): **8 failed, 83 passed**. Rote Erstausgabe, z. B.:

```
E   Left contains 6 more items, first extra item: 'php/appinfo/info.xml: the file type list for the English default does not name DOC, XLS, EML, ZIP, HEIC (FMT-01 to FMT-05)'
E   Left contains 3 more items, first extra item: "README.en.md: the section '## Supported file types' does not name DOC, XLS, EML, ZIP, HEIC (FMT-01 to FMT-05)"
E   assert None is not None
E   Left contains 2 more items, first extra item: "docs/store-listing.md: has no section '# Entwurf v1.5.0 (Teil Phase 31)'"
```

Grün blieben zwei Selbsttests; per Gegenprobe belegt (je ein Eingriff, rot, Datei per cmp gegen Sicherung gleich):

| Probe | Eingriff | rot |
|---|---|---|
| G1 | Formatwort als Teilstring statt ganzes Wort | `test_docx_does_not_stand_in_for_doc_nor_xlsx_for_xls` (1 failed, 90 passed) |
| G2 | fehlender Entwurf gibt `{}` statt None | `test_a_store_listing_without_the_draft_of_phase_31_is_reported` (1 failed, 90 passed) |

### GREEN

- Dateitypen-Liste in allen sechs Beschreibungen (Wortlaut siehe docs/store-listing.md Teil 1), Absatz unter der Dateitypen-Überschrift der drei READMEs; keine weiteren Sätze.
- docs/store-listing.md: Abschnitt "# Entwurf v1.5.0 (Teil Phase 31)" nach Teil Phase 30, Teil 1 Dateitypen-Liste je Sprache (eingezäunte Blöcke) mit Unterschied zu 1.4.3, Teil 2 README-Zeilen, Teil 3 Wortlaute der Urteile aus 31-02 (en/de, ZIP-Grenzcode ohne Codenamen), Teil 4 Grenzlisten-Vorschlag mit Empfehlung "nein", Vermerk "Abnahme durch den Owner: offen (REL-05)". Ältere Entwürfe unverändert.
- `LIMITATION_COUNT = 5` unverändert (Zeile 450).
- PHP-Rezept gefahren: `(92, 'bad993f8230804cf83a552f151dbed9d0ea1b16e71dd2a2d1705c0a1b5f57048')`, unverändert; Journal "Measured again by Plan 31-14" in test_measurement_scripts.py.
- Gates-Tests: test_store_metadata, test_measurement_scripts, test_public_artifacts 623 passed.

## Gates und CI

- Lokal vor f1aa9137: ruff check, ruff format --check (215 Dateien), pyright latest 0 Fehler, vulture grün, volle Suite **5472 passed, 30 skipped** (852 s).
- Lokal vor 76ce8463: dieselben Gates grün, volle Suite **5482 passed, 30 skipped** (748 s).
- Push `bf16229f..76ce8463` (beide Commits). CI auf 76ce8463:
  - Python gates **38264572771** success (5494 passed, 18 skipped)
  - PHP and store metadata gates **38264572714** success (598 PHPUnit-Tests)
  - HaRP deploy **38264572769**, Integration **38264572679**, Resilience **38264572829**, Multi-arch image **38264572639**, Security scans 38264572718, OpenSSF Scorecard 38264572712, alle success (acht von acht, per `gh run watch` abgewartet)

## Deviations from Plan

**1. [Rule 1, Vokabelregel E-H2] ZIP-Zeile ohne den gesperrten Wortstamm.** Der Planer-Vorschlag ("ZIP archives", "ZIP-Archive", "Archives ZIP") hätte test_store_metadata rot gemacht: docs/store-listing.md wird in jeder Zeile und jeder Schreibweise auf den Stamm geprüft, und das Gate verlangt die Listen dort zeichengleich. Umgesetzt "ZIP files: the files inside, without OCR", "ZIP-Dateien: die enthaltenen Dateien, ohne Texterkennung", "Fichiers ZIP : les fichiers contenus, sans OCR"; im Entwurf als Abweichung vermerkt. Gleiche Lösung wie 31-02.

**2. [Rule 1] Altes PowerPoint präzisiert.** Die must-have-Zeile sagt "PowerPoint-Altformat bleibt legacy_format". Laut dispatch.py gilt das nur für PowerPoint-OLE unter .pptx-Namen; eine .ppt-Datei steht nicht in der Allowlist und endet als `skipped(mime_not_allowed)`. docs/formats.md nennt beides.

**3. CHANGELOG-Position.** Unreleased über 1.4.3 statt über 1.4.2, weil 1.4.3 seit heute erschienen ist.

**4. docs/ocr.md nicht geändert.** HEIC steht dort seit 31-07 (Deckel-Kaskade); eine Formatliste gibt es in ocr.md nicht.

**5. Gate strenger als verlangt.** Neben "fünf Formatwörter je Liste" hält ein Fall jede Liste zeichengleich gegen den Entwurf (key_link des Plans), mit Selbsttests.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche. T-31-44 (Formatzeile "without OCR", Grenzen in docs/formats.md, Gate auf Formatzeilen), T-31-45 (Entwurf als offen markiert, nichts eingereicht), T-31-46 (Satz in docs/privacy.md) umgesetzt.

## Requirements

FMT-01 bis FMT-06 und POL-02 waren seit 31-13 Complete; dieser Plan liefert die Doku dazu. REL-05 bleibt Pending, die Textabnahme umfasst jetzt auch den Entwurf Teil Phase 31.

## Offene Punkte

- Owner-Abnahme bei REL-05: Dateitypen-Liste (drei Sprachen), README-Zeilen, Wortlaute der Urteile, Grenzlisten-Frage (Empfehlung nein).
- Aus STATE übernommen, nicht Teil dieses Plans: Kosten von str.find je ZIP-Treffer auf großem ZIP-Text messen (T-31-30); nach 31-15 verschoben.
- Option für den Owner: Verweis auf docs/formats.md in den READMEs (der Plan verbot weitere Sätze, deshalb nicht gesetzt).
- `occ findling:diagnose` zeigt die Marke recheck_1_5_0 nicht (Frage aus 31-11); docs/formats.md nennt die Logzeilen und verweist auf reconcile.md, kein neuer Befehl.

## Self-Check: PASSED

docs/formats.md und diese SUMMARY vorhanden; f1aa9137 und 76ce8463 in der Historie, origin/main auf 76ce8463; alle acht CI-Läufe auf 76ce8463 success. STATE.md, ROADMAP.md (14/15) und REQUIREMENTS.md (REL-05 um den Entwurf Teil Phase 31 ergänzt) von Hand nachgezogen.
