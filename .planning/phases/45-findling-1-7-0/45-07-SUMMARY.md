---
phase: 45-findling-1-7-0
plan: 07
subsystem: docs (README DE/EN/FR, admin-page, language-analyzers, l10n-chinese), store gates
tags: [store-04, rel-07, readme, gates, d-45-14]
requires: [45-06]
provides:
  - "Alle drei READMEs tragen Suchsprachen, die fünf bekannten Grenzen (eigener Abschnitt direkt nach der Sprachzeile), Messzahl, Formatliste, Share-Satz, Similar documents und die drei Neuerungen von 1.7.0"
  - "README-Gates für Messzahl (genau einmal je Sprache), Grenzen, Sprachzeile, Doku-Vergleich, Share-Satz, Similar documents, Formate; info.xml-Gates dieser Inhalte entfernt oder auf 'falls vorhanden' gesetzt"
  - "docs/admin-page.md: Speicherliste, Zähler, wildcard und neuer no_wildcard-Satz"
  - "45-README-PRUEFUNG.md: Faktenprüfung je Aussage mit Quelle, Umlaut-Audit"
affects: [45-08, 45-11]
tech-stack:
  added: []
  patterns: ["Ein README-Gate je Sprache über READMES = ((README, ''), (README_DE, 'de'), (README_FR, 'fr'))", "Selbsttests auf ausgeschriebenen Samples, damit sie den kurzen Store-Text von 45-11 überleben"]
key-files:
  created:
    - .planning/phases/45-findling-1-7-0/45-README-PRUEFUNG.md
  modified:
    - README.md
    - README.en.md
    - README.fr.md
    - docs/admin-page.md
    - docs/language-analyzers.md
    - docs/l10n-chinese.md
    - backend/tests/test_store_metadata.py
    - backend/tests/test_phase36_audit.py
decisions:
  - "Kurzregel der Store-Beschreibung bleibt auf info.xml als 'höchstens eine Messzahl' (vorher 'genau eine'); die Pflicht zur Zahl wandert als 'genau einmal' in jedes README"
  - "Vergleich der info.xml-Formatliste mit dem Entwurf von Phase 31 bleibt, aber nur, wo eine Beschreibung die Liste noch trägt (Schutz gegen Drift bis 45-11, kein Hindernis für den kurzen Text)"
  - "Neuerungen 1.7.0 in den READMEs mit '(ab 1.7.0)' markiert, weil main vor dem Release schon beschreibt, was 1.7.0 bringt"
  - "Oberfläche 'in neun Sprachen' gezählt: Englisch plus de, es, fr, it, nl, pt_PT, pt_BR, zh_TW; de_DE ist die Sie-Form desselben Deutsch"
metrics:
  duration: "ca. 50 min laut Systemzeit (bis 04:40 UTC)"
  completed: 2026-11-22
---

# Phase 45 Plan 07: READMEs mit den verlagerten Store-Inhalten, Gates umgezogen (STORE-04) Summary

Die drei READMEs tragen jetzt alles, was der kurze Store-Text in 45-11 abgibt (Messzahl, fünf Grenzen, Formatliste, Share-Satz, Similar documents), dazu Suchsprachen und die Neuerungen von 1.7.0; die Gates dieser Inhalte lesen die READMEs je Sprache, jeder umgezogene Gate hat ein Fehl-Sample, und die Kern-Gates (Datenschutz, Connector, Umstiegs-Link) prüfen unverändert die info.xml.

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | READMEs und Doku auf 1.7.0, Faktenprüfung | fdfe1b70 | README.md, README.en.md, README.fr.md, docs/admin-page.md, docs/language-analyzers.md, docs/l10n-chinese.md, 45-README-PRUEFUNG.md |
| 2 | Gates der verlagerten Inhalte auf die READMEs | 907baa2f | backend/tests/test_store_metadata.py, backend/tests/test_phase36_audit.py |

## READMEs (Task 1)

- Feature-Liste je Sprache um vier Punkte ergänzt: Ausschluss einzelner von Admins angelegter externer Speicher (ab 1.7.0), freie Plätze der Ordner- und Musterlisten (ab 1.7.0), Oberfläche in neun Sprachen inkl. Traditional Chinese (ab 1.7.0), Suchsprachen (Wortlaut der info.xml) als letzter Punkt.
- Neuer Abschnitt "## Bekannte Grenzen" / "## Known limitations" / "## Limites connues" direkt danach, fünf Punkte wortgleich aus der info.xml derselben Sprache, EN wortgleich mit docs/language-analyzers.md; Verweis auf die Doku (DE/FR mit Sprachhinweis).
- Messzahl, Formatliste, Share-Satz und Similar documents standen schon in allen drei READMEs wortgleich; Messzahl je README genau einmal.
- Faktenprüfung: 24 Aussagen mit Quelle in 45-README-PRUEFUNG.md, kein offener Befund. 7 GitHub-Links per curl je einmal 200, 16 relative Links vorhanden. Store-, Shields-, Scorecard- und Best-Practices-Links nicht abgefragt (Plan: nur GitHub/Doku).
- docs/admin-page.md: Tabellenzeile External Storage; neue Abschnitte "Einzelne externe Speicher ausschließen (ab 1.7.0)" (nur Admin-Speicher, Opt-out, Hauptschalter aus = gesperrt und gespeichert, Inline-Bestätigung, Entfernen im nächsten vollständigen Abgleich ohne 30-Tage-Karenz als `deselected`, Nachindexieren beim nächsten regulären Abgleich, Protokoll nur Zähler), "Freie Plätze in den Listen", "Ordnerfeld: * und ? werden abgewiesen"; Tabelle "Abgelehnte Eingaben" um `wildcard` und den neuen `no_wildcard`-Satz.
- docs/language-analyzers.md: Absatz zur Kurzliste nennt jetzt README.en.md und D-45-14 statt der Store-Beschreibungen.
- Umlaut-Audit der geänderten deutschen Zeilen: drei Vorfilter-Treffer ("neuen", "neuer"), alle korrekt.

## Gate-Umzug (Task 2): entfernter info.xml-Gate -> README-Nachfolger

| Entfernter oder geänderter Gate (info.xml) | Nachfolger |
|---|---|
| `test_the_measured_figure_stands_in_every_language_of_the_companion_half` | `test_the_measured_figure_stands_once_in_every_readme_in_the_spelling_of_its_language` (DE/EN/FR, genau einmal) |
| `test_the_measured_figure_stands_in_every_language_of_the_backend_half` | derselbe |
| `test_every_store_description_carries_exactly_one_measured_figure` (genau eine) | `test_no_store_description_carries_more_than_one_measured_figure` (höchstens eine, bleibt auf info.xml) plus README-Gate oben |
| `test_every_description_carries_the_five_known_limitations_under_its_heading` | `test_every_readme_carries_the_five_known_limitations_under_its_heading` |
| `test_the_english_known_limitations_of_both_halves_stand_verbatim_in_the_doc` | `test_the_english_known_limitations_of_the_readme_stand_verbatim_in_the_doc` |
| `test_the_language_line_stands_right_before_the_limitations_in_all_six_descriptions` | `test_the_language_line_stands_right_before_the_limitations_in_all_three_readmes` |
| `test_every_description_names_the_formats_of_1_5_in_its_file_type_list` | `test_every_readme_names_the_formats_of_1_5_in_its_file_type_section` (bestand schon) |
| `test_every_file_type_list_stands_in_the_draft_of_phase_31_character_for_character` | bleibt, Scanner prüft nur noch Beschreibungen, die die Liste tragen |
| `test_the_share_sentence_stands_once_in_all_three_languages_of_both_halves` | `test_the_share_sentence_stands_in_the_readme_of_its_language` (bestand, jetzt über `scan_share_sentence`) |
| `test_the_german_companion_description_carries_the_owner_sentence_character_for_character` | derselbe (README.md, Owner-Wortlaut) |
| `test_the_similar_documents_line_stands_in_all_six_descriptions_and_the_changelog` (test_phase36_audit.py) | gleichnamig umgestellt auf die drei READMEs plus Changelog; voller Wortlaut in `test_the_similar_documents_line_stands_once_in_every_readme` |

Entfernte Scanner: `scan_resident_figure_of_an_info`, `scan_file_types`; Konstanten `LIMITATION_HEADINGS`, `MIGRATION_LINE_OPENINGS` (nur noch vom alten Sprachzeilen-Scanner genutzt). Neu: `READMES`, `README_LIMITATION_HEADINGS`, `SIMILAR_DOCUMENTS_LINES`, `readme_points`, `scan_similar_documents`; `scan_limitations`, `scan_language_line`, `scan_share_sentence`, `scan_limitations_against_doc` lesen README-Text je Sprache.

Selbsttests mit Fehl-Sample (B8), alle grün: mutierte Zahl in jedem README, Zahl doppelt (FR), README ohne Zahl bei Beschreibung ohne Zahl (DE), zweite Zahl in einer ausgeschriebenen Beschreibung, umformulierter Share-Satz (DE), doppelter Share-Satz (FR), fremdsprachiger Share-Satz (EN), README ohne dritte Grenze (DE, nur diese Datei gemeldet), README ohne Grenzen-Überschrift (FR), Grenzen hinter einem Absatz (EN), Doku um ein Zeichen geändert, README-Liste um Worte geändert, Doku ohne Abschnitt, Sprachzeile an den Listenanfang verschoben (EN), README ohne Grenzen-Überschrift für die Sprachzeile (DE), Similar-documents-Zeile fehlend, doppelt und gekürzt (FR), README ohne HEIC (FR), README ohne Formatabschnitt (DE), Formatliste mit Zusatz gegen den Entwurf; Positivfall: Beschreibung mit Entwurfsliste oder ganz ohne Liste besteht. Die Fälle, die bisher die echte info.xml mutierten (zweite Messzahl, Entwurfsvergleich), laufen jetzt auf ausgeschriebenen Samples und überleben so den kurzen Store-Text von 45-11.

Kern-Gates unverändert auf info.xml: Connector (`test_the_connector_sentence_stands_once_in_all_three_languages_of_both_halves`), Datenschutz (`test_the_privacy_paragraph_of_d_12_stands_in_all_three_languages_of_both_halves`), Umstiegs-Link (test_migration_path.py).

## Verifikation

- Plan-Verify Task 1: Überschriften, 730.2/730,2 je README, Traditionelles Chinesisch, Prüftabelle, keine U+2013/U+2014 in READMEs und geänderten Docs: OK.
- `pytest tests/test_store_metadata.py tests/test_phase36_audit.py tests/test_public_artifacts.py tests/test_migration_path.py`: 251 passed; nach Task 1 zusätzlich test_admin_ui_contract.py (467 passed mit den übrigen) und 22 weitere doku-lesende Dateien (1664 passed, 105 skipped).
- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture grün.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Similar-documents-Gate lag in test_phase36_audit.py**
- **Found during:** Task 2
- **Issue:** Der info.xml-Gate für "Similar documents" stand nicht in test_store_metadata.py, sondern in test_phase36_audit.py; er hätte den kurzen Store-Text von 45-11 blockiert.
- **Fix:** Dort auf die drei READMEs umgestellt (Changelog-Teil unverändert), voller Wortlaut-Gate mit Fehl-Samples neu in test_store_metadata.py.
- **Files modified:** backend/tests/test_phase36_audit.py
- **Commit:** 907baa2f

**2. [Auftrag des Orchestrators] docs/l10n-chinese.md**
- Zeile 129 (vorher 128): das wörtliche doppelte U+2014 in der Typografie-Regel ersetzt durch "(U+2014 written twice)", Sinn unverändert; die Datei hat jetzt kein U+2013/U+2014 mehr.
- Schlüsselzahlen nachgezählt am 22.11.2026 mit derselben Methode (Gegenprobe: auf edc08233 ergibt sie die alten 366/96/91): de.json und zh_TW.json je 380 Schlüssel, gleiche Reihenfolge, 102 mit Direktiven, 97 ohne Pluralschlüssel, 5 Plural mit 1 Form, 380 Tabellenzeilen; Zeilen in "The key set" und "Machine checks" sowie "380 single cases" angepasst, Datum der Nachzählung genannt.
- **Commit:** fdfe1b70

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: README.md, README.en.md, README.fr.md, docs/admin-page.md, docs/language-analyzers.md, docs/l10n-chinese.md, 45-README-PRUEFUNG.md, backend/tests/test_store_metadata.py, backend/tests/test_phase36_audit.py
- FOUND: fdfe1b70, 907baa2f
