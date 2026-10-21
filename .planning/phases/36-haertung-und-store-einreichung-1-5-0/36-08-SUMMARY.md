---
phase: 36-haertung-und-store-einreichung-1-5-0
plan: 08
subsystem: Extraktion (ZIP, ODF, OOXML)
tags: [hart-06, d-36-17, f3, blocked-malicious, zip, odf, ooxml, xml-bomb, upgrade-seed]
requires: [36-06, 36-07, 36-17]
provides:
  - "archive.OverLimit(signature) mit den Codes zip_ratio, zip_overlap, zip_traversal; extract_zip setzt skipped(blocked_malicious, detail=...)"
  - "config.ARCHIVE_MALICIOUS_RATIO = 1000 (O12), zweistufige Verhältnisregel"
  - "errors.is_entity_bomb als einzige Stelle der Amplification-Regel"
  - "Vorzählung des Zentralverzeichnisses in odf.py und office.py vor jedem ZipFile (package_entries)"
  - "seed-bomb.zip als reine Tiefe 3 (O4 (a))"
affects: [36-09, 36-11]
tech-stack:
  added: []
  patterns:
    - "Signatur als Attribut der Grenzausnahme: OverLimit() bleibt archive_limit, OverLimit(code) wird blocked_malicious"
    - "XML-Fehler werden nur auf das Wort 'amplification' geprüft und sonst unverändert weitergeworfen, damit from_exception die bisherigen Urteile behält"
key-files:
  created:
    - backend/tests/test_extract_signatures.py
  modified:
    - backend/src/findling/config.py
    - backend/src/findling/extract/archive.py
    - backend/src/findling/extract/errors.py
    - backend/src/findling/extract/odf.py
    - backend/src/findling/extract/office.py
    - backend/tests/test_extract_archive.py
    - backend/tests/test_phase31_audit.py
    - backend/tests/test_phase36_hostile_corpus.py
    - backend/tests/test_upgrade_seed_fixture.py
    - backend/tests/test_measurement_scripts.py
    - scripts/ci/make_upgrade_seed_formats.py
    - .github/fixtures/upgrade-seed-formats/seed-bomb.zip
decisions:
  - "Traversal wird an ZipInfo.orig_filename geprüft, nicht an ZipInfo.filename: zipfile schneidet filename am NUL ab und ersetzt unter Windows den Backslash, damit wäre O5 (NUL) nicht erkennbar"
  - "Die zipfile-Warnung 'Overlapped entries' (zwei Einträge auf einem lokalen Header) gilt wie die Ablehnung als zip_overlap, auf jeder Ebene; nur so wechselt der Korpusfall inner-zip-with-overlap laut O2 (a) auf blocked_malicious"
  - "Signatur vor Grenze in der Verhältnisprüfung: ein Mitglied über 1000:1 wird auch dann zip_ratio, wenn davor ein Mitglied zwischen 100 und 1000 steht; Reihenfolge Einträge, Summe, Verhältnis (O7) bleibt"
  - "Traversal-Prüfung nach dem Verhältnis und vor dem ersten gelesenen Mitglied, auch für Verzeichniseinträge"
  - "O4 (a): seed-bomb.zip ist reine Tiefe 3 (391 Byte), deploy-harp.yml bleibt bei skipped/archive_limit"
metrics:
  duration: "ca. 85 min (04:45 bis 06:10 Ortszeit), davon 13 min volle lokale Suite und das Warten auf CI"
  completed: 2026-10-21
  tasks: 2
  files: 13
requirements: [HART-06]
---

# Phase 36 Plan 08: ZIP- und Paket-Signaturen Summary

Der Extraktor erkennt jetzt fünf Angriffssignaturen und meldet sie als `skipped(blocked_malicious)` mit Detailcode. In ZIP-Dateien sind das `zip_ratio` (über 1000:1), `zip_overlap` und `zip_traversal`, in ODF- und OOXML-Paketen `package_entries` (mehr als 10 000 Einträge, gezählt vor `ZipFile`) und `xml_entities`. Grenzfälle ohne Signatur bleiben `archive_limit`: Verhältnisse von 100 bis einschließlich 1000:1, Tiefe, Eintragszahl, deklarierte Summe. Alle 21 xfail-Fälle von 36-08 im Korpus sind grün, keine Prüfung wurde dafür abgeschwächt.

## Commits

| Task | Name | Commit |
|------|------|--------|
| 1 | ZIP-Signaturen in archive.py, Nachzug der Bestands- und Korpusfälle | 2b6ab1f2 |
| 2 | package_entries und xml_entities, Saat O4 (a), Ratsche | b9ec1b33 |

## Was gebaut ist

**archive.py**
- `OverLimit.__init__(signature=None)`. Ohne Signatur bleibt es `archive_limit`. Mit Signatur trägt das Urteil den Code aus der geschlossenen Liste, nie einen Namen oder eine Meldung.
- `_judge_ratios`: Ab 1 MiB prüft die Funktion zuerst jedes Mitglied auf mehr als `ARCHIVE_MALICIOUS_RATIO` (dann `zip_ratio`), danach auf mehr als `ARCHIVE_MAX_RATIO` (dann `archive_limit`). Die Konstante wird über das Modul gelesen, `monkeypatch` auf `archive.` greift.
- `_is_traversal(raw_name)`: prüft auf ein `..`-Segment (Trenner `/` oder `\`), einen führenden Trenner, einen Laufwerksbuchstaben und NUL. Aufgerufen wird sie mit `info.orig_filename`, für alle Mitglieder einer Ebene und bevor das erste gelesen wird.
- Überlappung: Die Ablehnung durch zipfile, die Warnung zu zwei Einträgen auf einem Header und die Überlappung in einer inneren ZIP-Datei enden alle als `zip_overlap`. Die Warnung wird nur aufgezeichnet und nie ausgegeben.

**odf.py, office.py, errors.py**
- `_too_many_entries(path)`: öffnet die Datei, liest die Größe per `os.fstat` und ruft `archive.count_central_directory(..., limit=ARCHIVE_MAX_ENTRIES)` auf.
  - Mehr Einträge als die Grenze oder ein Verzeichnis über 8 MiB (`OverLimit`) ergeben `package_entries`.
  - `CorruptDirectory` und `OSError` reichen die Datei an den Loader weiter.
  - In office.py läuft die Zählung in `_refused_before_the_loader` (vorher `_too_large_to_read`), also vor allen drei Loadern.
- `errors.is_entity_bomb(error)`: prüft nur, ob das Wort "amplification" in der Meldung steht. odf.py wendet die Regel bei `XMLSyntaxError` an. office.py fängt `(etree.XMLSyntaxError, ParseError)` um Loader und Walk, bei XLSX also auch beim Iterieren der Zeilen. Ist es keine Bombe, wird die Ausnahme unverändert weitergeworfen. Damit bleiben `xml_invalid` und `corrupt` wie vorher.
- Kein Verhältnis-Test für Office-Container (Pitfall 4). `34-zip-bombe.docx` bleibt `too_large`.

## Bestandstests mit Zielurteil (D-36-17, plan 36-08)

**test_extract_archive.py**
- `test_a_zip_file_inside_an_inner_one_ends_the_whole_file`: unverändert LIMIT.
- `test_a_member_over_the_ratio_is_an_archive_limit` ist geteilt:
  - `test_a_member_between_the_two_ratios_is_an_archive_limit`: etwa 155:1 (Nullen, alle 700 Byte ein Byte aus `shake_128(b"36-08")`), gemessen zwischen 100 und 1000, Ergebnis LIMIT ohne Detail.
  - `test_a_member_over_the_attack_ratio_is_blocked_as_malicious`: 2 MiB Nullen, gemessen 1023,5:1, Ergebnis `blocked_malicious/zip_ratio`. Deflate reicht, bzip2 oder LZMA sind nicht nötig.
- `test_a_large_member_of_ordinary_text_is_under_the_ratio` und `test_a_small_member_is_not_judged_by_its_ratio`: unverändert INDEXED.
- `test_overlapping_entries_are_an_archive_limit` heißt jetzt `test_overlapping_entries_are_blocked_as_malicious`, Ergebnis `zip_overlap`. Die BadZipFile-Vorprüfung bleibt.
- `test_names_that_climb_out_stay_text` heißt jetzt `test_names_that_climb_out_are_blocked_as_malicious`, Ergebnis `zip_traversal` ohne Text. Neu ist `test_names_with_dots_that_do_not_climb_stay_text` (`..x.txt`, `a..b/c.txt`, INDEXED mit Abschnitten).

**test_phase31_audit.py**
- `name-nul-and-both-separators`: Ergebnis `blocked_malicious/zip_traversal` (O5 (a)).
- `inner-zip-with-overlap`: Ergebnis `blocked_malicious/zip_overlap` (O2 (a)).
- Der Detailcode wird jetzt geprüft (`_ZIP_DETAILS`).

**test_upgrade_seed_fixture.py (O4 (a))**
- `test_the_bomb_carries_no_seed_word`: unverändert.
- `test_the_bomb_is_three_levels_deep_with_a_zero_member_over_the_ratio` heißt jetzt `test_the_bomb_is_three_levels_deep_without_a_member_over_the_ratio`: ein `.zip` je Ebene, innen ein `.txt`, auf keiner Ebene ein Mitglied über dem Verhältnis, `ARCHIVE_MAX_DEPTH == 2`.
- `test_the_bomb_is_an_archive_limit_for_this_code`: unverändert SKIPPED/ARCHIVE_LIMIT.
- `test_each_limit_alone_judges_the_bomb` heißt jetzt `test_the_depth_alone_judges_the_bomb`. Das Ergebnis ist ARCHIVE_LIMIT, mit Tiefe 10 INDEXED, zurück auf 2 wieder ARCHIVE_LIMIT. Den Verhältnis-Teil gibt es nicht mehr, ein Kommentar sagt warum.
- Der Kommentarblock um Zeile 160 ist nachgezogen.

**test_upgrade_seed_steps.py**
- Das Literal `skipped/archive_limit` bleibt, die Tests sind grün.

## Korpus (test_phase36_hostile_corpus.py)

- **archive:** Die 7 Markierungen sind weg (`ratio-over-the-attack-ratio`, `overlap-outside`, `overlap-inside`, vier `traversal-*`). Die Positivkontrollen `ratio-about-150` und `ratio-just-under-1000` bleiben `archive_limit`.
- **package:** Die 6 Markierungen sind weg. Die drei Pakete mit 1 Mio. Einträgen laufen jetzt: Die Zählung endet an der Länge des Verzeichnisses, ein ZipInfo wird nie gebaut. `docx-of-10000-records` bleibt `corrupt`.
- **xml:** Die 8 Markierungen sind weg (Billion Laughs und Quadratic Blowup in odt, docx, pptx, xlsx).
- `grep 'reason="built in 36-08"'`: kein Treffer. Es bleiben 9 xfail-Fälle von 36-09.

## Saat O4 (a)

- `_bomb()` baut nur noch drei Ebenen ZIP mit einer kurzen Notiz. Das Nullen-Mitglied ist weg, ebenso der unbenutzte Deflate-Schreiber (`_Bits`, `_zeros_deflated`, `ZERO_*`, `_DEFLATED`).
- `seed-bomb.zip` ist neu erzeugt und von 7095 auf 391 Byte geschrumpft. Die Generator-Prüfung byte für byte ist grün.
- Im echten Sandbox-Kind lokal: `skipped archive_limit None`.
- deploy-harp.yml ist unverändert. Der Kommentar bei 5615 nannte schon "depth 3 over ARCHIVE_MAX_DEPTH 2".

## Gegenprobe große echte Office-Dateien

Lokal, nicht im Repo (`.dev/probe-live/loadcorpus`, die größten ihrer Art):
- `00414-stellungnahme.pptx` (349 893 Byte): indexed, 26 692 Zeichen.
- `00378-bescheid.xlsx` (346 874 Byte): indexed, 13 199 Zeichen.
- `00410-vertrag.docx` (346 877 Byte): indexed, 35 557 Zeichen.

Im Repo liegen keine PPTX- oder XLSX-Dateien. Deshalb gibt es zwei Tests mit echten Paketen, die die eigenen Bibliotheken schreiben: eine XLSX mit 5000 Zeilen und 21 Blättern (openpyxl) und eine PPTX mit 200 Folien (python-pptx). Beide sind indexed.

## Gates

- Lokal grün:
  - ruff (src, tests, scripts mit `--config pyproject.toml`) und ruff format
  - pyright: 0 errors
  - vulture
  - reuse lint: 2905/2905
- Volle Suite lokal: 6121 passed, 264 skipped, 9 xfailed in 12:52. Ein erster Lauf mit `-x` brach an `test_v14_zelle.py::test_kette_without_a_readable_timer_does_not_start` ab, einem Shell-Test ohne Bezug zu diesem Plan. Einzeln und im zweiten vollen Lauf war der Test grün, er gilt als Lastflake.
- CI für b9ec1b33 (der Push enthält beide Commits):
  - Python gates 39541530987 sind grün: ubuntu mit RLIMIT_AS, 6132 passed, 253 skipped, 9 xfailed. Das ist der Speicherbeleg auch für die Pakete mit 1 Mio. Einträgen.
  - Grün sind auch Security scans 39541531055, Multi-arch image 39541531057, OpenSSF Scorecard 39541531002, Integration 39541531041 und Resilience 39541531035.
  - HaRP deploy 39541531048 ist grün in allen vier Beinen. "Store upgrade 5" lief auf stable34/ubuntu-24.04 grün (die anderen Beine überspringen den Schritt wie bisher), mit der Zeile "the ZIP bomb is skipped/archive_limit in state.db and in findling_file_state" für die neue Saat.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Traversal am rohen Namen statt an `info.filename`**
- **Found during:** Task 1
- **Issue:** zipfile schneidet `ZipInfo.filename` am NUL ab: `a\x00b` wird zu `a`. Unter Windows ersetzt es außerdem `\` durch `/`. Am `info.filename` wäre der NUL-Fall von O5 also nie erkennbar.
- **Fix:** `_is_traversal(info.orig_filename)`, so wie es 36-WORTLAUT.md A3 sagt ("`info.orig_filename` bzw. Name vor jeder Bereinigung"). Eine Quelltextprobe im Test belegt, dass weder die Regel noch `_read_zip` `clean_display_name` lesen und dass zipfile den Namen tatsächlich abschneidet.
- **Commit:** 2b6ab1f2

**2. [Rule 2 - Missing critical] Überlappungswarnung als Signatur**
- **Found during:** Task 1
- **Issue:** Der Korpusfall `inner-zip-with-overlap` baut zwei Einträge auf einem lokalen Header. Zu diesem Fall gibt zipfile nur eine Warnung aus ("Overlapped entries ... possible zip bomb"), keine Ablehnung. Mit der Ablehnung allein wäre der Fall nach O2 (a) indexed geblieben. Die echte innere Ablehnung (`hostile.zip_overlap`) war dagegen schon vorher `archive_limit`.
- **Fix:** `_copy` zeichnet die Warnungen beim Öffnen des Mitglieds auf. Eine Warnung, die mit "Overlapped entries" beginnt, wird zu `OverLimit("zip_overlap")`. Andere Warnungen bleiben verworfen, nichts geht nach stderr.
- **Commit:** 2b6ab1f2

**3. [Rule 3 - Blocking] Paket-Ratsche schon in Task 1**
- **Found during:** Task 1
- **Issue:** config.py und archive.py ändern den Baumhash. Ohne Nachzug wäre der Commit von Task 1 rot gewesen.
- **Fix:** Journalabsatz "Moved on 2026-10-21 by Plan 36-08" in Task 1 (9b51ba91) und ein zweiter in Task 2 (d832586d). Beide sind unabhängig mit find, sort, tr und sha256sum nachgerechnet.
- **Commits:** 2b6ab1f2, b9ec1b33

### Kleinere Abweichungen

- **Vorzählung zweimal:** Sie steht als kleine private Funktion `_too_many_entries` in odf.py und in office.py, weil der Plan `count_central_directory` in beiden Modulen verlangt. odf.py importiert office.py nicht, das würde docx und openpyxl laden.
- **Ausnahmen weiterwerfen:** In office.py wird ein XML-Fehler ohne Amplification weitergeworfen statt hier an `from_exception` übergeben. Das ist dasselbe Urteil wie vor dem Plan: Die Ausnahme kam schon bisher erst an der Sandbox-Grenze an.
- **Zusätzliche Tests über den Plan hinaus:**
  - Doppelte Namen an eigenen Headern sind keine Überlappung (Positivkontrolle).
  - Traversal-Name in einer inneren ZIP-Datei.
  - Signatur vor Grenze im Verhältnis.
  - `a/..` und `..` als Namen.
  - `pptx` mit 10 001 Einträgen.
  - Die Pakete mit 1 Mio. Einträgen auch ohne Sandbox.
- **test_measurement_scripts.py** ist in beiden Tasks geändert (je ein Ratschenabsatz, siehe 3.).

## Threat Flags

Keine neue Oberfläche. T-36-27 bis T-36-31 sind umgesetzt:
- Zählung vor jedem ZipFile.
- Amplification-Zuordnung mit Tests auf echte lxml- und expat-Ausnahmen.
- Traversal am rohen Namen, `left == [Dateiname]` in jedem Korpusfall.
- caplog- und repr-Probe auf "amplification".
- Gegenprobe mit großen echten Dateien.

## Known Stubs

Keine.

## Self-Check: PASSED

- Dateien vorhanden: backend/tests/test_extract_signatures.py, .github/fixtures/upgrade-seed-formats/seed-bomb.zip, 36-08-SUMMARY.md
- Commits 2b6ab1f2 und b9ec1b33 vorhanden und auf origin/main
