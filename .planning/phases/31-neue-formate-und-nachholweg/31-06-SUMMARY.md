---
phase: 31-neue-formate-und-nachholweg
plan: 06
subsystem: Extraktion (extract/legacy_xls.py, extract/cfb.py, extract/dispatch.py)
tags: [fmt-04, d-31-03, xls, xlrd, cfb, olefile, befund-9, ole-unter-ooxml]
requires:
  - phase: 31-05
    provides: "extract_doc, build_cfb mit Strömen, Kettenschutz für .doc, Stand 3ec167fc"
  - phase: 31-01
    provides: "xlrd==2.0.2 und olefile==0.47 gepinnt"
provides:
  - "extract_msexcel(path): Sniff OLE / XLSX / HTML oder XML-Spreadsheet-2003 / Text unter Excel-Namen, sonst skipped(unsupported_variant)"
  - "extract_xls(path): xlrd mit on_demand, ragged_rows=True, formatting_info=False, Log in eine Nullsenke, Zellgrenze settings().max_cells"
  - "cfb.ole_kind(path) -> 'encrypted' | 'word' | 'excel' | 'legacy' | None, entschieden nach den Strömen an der Spitze des Verzeichnisbaums"
  - "cfb.check_fat_size und cfb.walk_stream (bisher privat in legacy_doc), CorruptCompoundFile"
  - "conftest.cfb_with_difat (aus test_legacy_doc verschoben)"
  - "zwei LibreOffice-Fixtures biff8-values.xls (zellquendel, blattquendel) und biff8-far-cell.xls (fernquendel)"
affects: [31-10 Freischaltung .xls über extract_msexcel, 31-11 Nachholweg der legacy_format-Zeilen, 31-12 Saatdateien, 31-14 docs/formats.md, 31-15 Audit]
tech-stack:
  added: []
  patterns: ["Prüfungen vor einer Bibliothek mit eigenem CFB-Leser: Kette einmal mit Besuchsmenge bis ENDOFCHAIN", "Hängertests im Kindprozess mit Selbstabbruch per Timer-Thread", "Logsenke als Objekt im Speicher statt os.devnull (Dateiwege-Gate)"]
key-files:
  created:
    - backend/src/findling/extract/legacy_xls.py
    - backend/tests/test_legacy_xls.py
    - backend/tests/fixtures/legacy/biff8-values.xls
    - backend/tests/fixtures/legacy/biff8-far-cell.xls
  modified:
    - backend/src/findling/extract/cfb.py
    - backend/src/findling/extract/dispatch.py
    - backend/src/findling/extract/legacy_doc.py
    - backend/tests/conftest.py
    - backend/tests/test_cfb.py
    - backend/tests/test_extract_documents.py
    - backend/tests/test_extract_edge_paths.py
    - backend/tests/test_legacy_doc.py
    - backend/tests/test_measurement_scripts.py
    - backend/tests/fixtures/legacy/README.md
    - scripts/dev/make_legacy_fixtures.py
decisions:
  - "Zellzählung nach derselben Regel wie XLSX (jede Zelle, die die Bibliothek liefert, auch leere), aber xlrd liefert mit ragged_rows nur bis zur letzten Zelle je Zeile; openpyxl liefert das ganze Rechteck. Gleiche Quelle als .xlsx: far-cell = too_many_cells, als .xls: indexed"
  - "Werte wie extract_xlsx: Fehlerzellen als Text (#DIV/0!), weil openpyxl sie so liefert; gemessen an derselben Quelle als .xlsx, Ausgabe zeichengleich"
  - "Kettenprüfung vor xlrd (Befund 9): xlrd folgt einer Kette im Ministrom ohne Besuchsmenge bis zu einer negativen Sektornummer; Zyklus = Endlosschleife mit wachsendem Speicher. Darum check_fat_size, olefile und walk_stream vor xlrd, und walk_stream verlangt ENDOFCHAIN am Kettenende"
  - "Kettenprüfungen aus legacy_doc nach cfb.py verschoben (eine Logik für .doc und .xls); detail bei Kettenfehlern einer .doc ist jetzt findling.extract.cfb.CorruptCompoundFile"
  - "ole_kind entscheidet nach den Strömen an der Spitze des Baums: .doc mit eingebettetem Excel-Diagramm bleibt Word; bekannter Name außerhalb des Baums bleibt legacy_format; OLE ohne bekannten Namen bleibt beim alten Weg (failed(corrupt)), wie bisher"
  - "xlrds Logdatei ist ein Objekt mit write() statt os.devnull: open(..., 'w') zählt das Dateiwege-Gate als Schreibzugriff"
metrics:
  duration: "ca. 230 min (davon ca. 175 min ein Gegenproben-Lauf, der wegen Speicherwachstum in einem Hänger swappte, siehe Abweichung 6)"
  completed: 2026-10-11
  tasks: 2
  files: 15
---

# Phase 31 Plan 06: .xls-Extraktor und OLE unter OOXML-Namen (FMT-04) Summary

Excel-97-bis-2003-Dateien werden über xlrd mit derselben Zellgrenze wie XLSX gelesen, und Word- oder Excel-Altdateien unter .docx/.xlsx/.pptx-Namen, die 1.4.2 als `legacy_format` übersprang, gehen jetzt nach Inhalt an den .doc- bzw. .xls-Leser. Vor xlrd prüft cfb.py die Sektorketten, weil xlrds eigener CFB-Leser bei einem MiniFAT-Zyklus endlos läuft. Noch nicht für echte .xls-Mimetypen freigeschaltet (31-10).

## Befund 9: xlrds eigener CFB-Leser (Quelltext 2.0.2, compdoc.py, und gemessen)

- FAT-Ketten (`_locate_stream`) und Verzeichnis, Ministrom, SSAT, MSAT führen eine Besuchsliste `seen`: Zyklen dort enden als `CompDocError`.
- **Lücke:** Ein Strom unter 4096 Byte wird über `_get_stream(..., seen_id=None)` aus dem Ministrom gelesen. Die Schleife läuft `while s >= 0` ohne Besuchsliste und ohne Längengrenze: ein MiniFAT-Zyklus oder eine Kette, die hinter dem Stromende weiterläuft, ist eine Endlosschleife, die bei jedem Durchlauf ein Element an eine Liste hängt. Die Workbook-Ströme beider LibreOffice-Fixtures liegen im Ministrom (2538 und 1659 Byte), der Fall ist also real.
- Eine Sektornummer hinter dem Dateiende endet in xlrd als `IndexError` (`self.seen[s]`).
- Die Prüfung vor xlrd: `cfb.check_fat_size` (aus 31-05), olefile mit `DEFECT_INCORRECT` (DIFAT-Zyklus), `cfb.walk_stream` für jeden vorhandenen Strom `Workbook` und `Book` (FAT- und MiniFAT-Kette mit Besuchsmenge, gegen die von olefile auf die Dateigröße gekürzte Tabelle, und neu: Kettenende muss ENDOFCHAIN sein).

| Fall (Test) | Urteil, detail, Zeit (gemessen) | Ohne Prüfung vor xlrd (Gegenprobe X1) |
|---|---|---|
| FAT-Zyklus im Workbook | failed(corrupt), cfb.CorruptCompoundFile, 0,02 s | xlrd: CompDocError, auch corrupt |
| FAT-Kette hinter dem Dateiende (Sektor 100 von 128 FAT-Einträgen, Datei 11 Sektoren) | failed(corrupt), cfb.CorruptCompoundFile, 0,01 s | xlrd: IndexError; ohne IndexError in der Fangliste rot (X17) |
| FAT-Kette läuft hinter dem Stromende weiter | failed(corrupt), cfb.CorruptCompoundFile, 0,01 s | xlrd: CompDocError |
| DIFAT-Zyklus (7-MB-Datei, 110 FAT-Sektoren) | failed(corrupt), builtins.OSError (olefile), 0,01 s | xlrd: CompDocError |
| FAT größer als die Datei (20 000 Sektoren) | failed(corrupt), cfb.CorruptCompoundFile, 0,01 s | xlrd: schnell; ohne check_fat_size hängt olefile (X3 rot) |
| MiniFAT-Zyklus im Workbook | failed(corrupt), cfb.CorruptCompoundFile, 0,01 s | **xlrd hängt** (X1 rot) |
| MiniFAT-Kette läuft hinter dem Stromende in einen Zyklus (zwei Ziele) | failed(corrupt), cfb.CorruptCompoundFile, 0,01 s | **xlrd hängt** (X1, X2 rot) |
| Book-Strom mit MiniFAT-Zyklus hinter leerem Workbook | failed(corrupt), cfb.CorruptCompoundFile, 0,01 s | **xlrd hängt** (X1, X15 rot) |

Jeder Fall hat eine Kontrolle ohne Defekt (FAT-Workbook, DIFAT mit ENDOFCHAIN, unveränderte Fixture, umbenannte Fixture ohne Zyklus), die `VALUES_TEXT` liefert. Die Kettenfälle laufen in einem Kindprozess (spawn); die 5 s misst das Kind mit `time.monotonic()` um `extract_xls`, ein Timer-Thread beendet das Kind nach 10 s, der Elternprozess wartet höchstens 30 s. `pytest-timeout` ist nicht installiert (`import pytest_timeout`: ModuleNotFoundError).

## Task 1: legacy_xls.py (FMT-04)

- Fixtures: `make_legacy_fixtures.py --only xls` (neuer Schalter, damit die .doc-Fixtures nicht neu geschrieben werden), Quelle als `.fods`, LibreOffice 26.2.4.2, Build-ID `0229ac93...` aus `program/version.ini`. SHA-256 im Test und im README.
- Gleichheit mit XLSX gemessen: dieselbe `.fods`-Quelle von derselben LibreOffice nach .xlsx gewandelt und mit `extract_xlsx` gelesen ergibt zeichengleich `VALUES_TEXT` (`3`, `2.5`, `2024-03-15 00:00:00`, `#DIV/0!`, beide Blätter, keine Blattnamen). far-cell als .xlsx: `skipped(too_many_cells)`, weil openpyxl das Rechteck liefert.
- RED: gegen einen Stub (`skipped(empty_text)`) **29 failed, 2 passed** (die zwei Digest-Tests, per Definition grün gegen jede Implementierung). Die später ergänzten 7 Fälle (MiniFAT-Kette über das Stromende x2, FAT-Kette über das Stromende, Book hinter leerem Workbook x2, Markup-Fälle mit verschärfter Prüfung x2) gegen denselben Stub: 7 failed.
- GREEN: 36 passed (am Ende 23 s, davon die Kindprozesse).
- Gegenproben (je ein Eingriff, Testdatei gelaufen, zurückgebaut, Bytes verglichen):

| Probe | Eingriff | rot |
|---|---|---|
| X1 | keine Prüfung vor xlrd | 5: ohne Workbook, MiniFAT-Zyklus, Kette über Stromende x2, Book hinter leerem Workbook |
| X17 | wie X1 und IndexError nicht gefangen | zusätzlich Kette hinter dem Dateiende |
| X2 | walk_stream ohne ENDOFCHAIN-Prüfung | 2: Kette über Stromende x2 |
| X3 | kein check_fat_size | 1: FAT größer als die Datei |
| X4 | ragged_rows=False | 2: far-cell (tracemalloc), genaue Zellgrenze |
| X5 | ohne logfile (Standard sys.stdout) | 1: Logtest im frischen Interpreter |
| X6 | Zahlen per str | 6 |
| X7 | nur Zellen mit Wert zählen | 1: genaue Zellgrenze |
| X8 / X9 | Verschlüsselung / Varianten nicht abgebildet | 2 / 3 |
| X10 / X11 / X12 | ohne ZIP-Zweig / ohne Markup-Zweig / Text immer angenommen | 1 / 2 / 3 |
| X13 / X14 | Fehlerzellen weg / Datum als Zahl | 5 / 5 |
| X15 | nur der erste Strom geprüft | 1: Book hinter leerem Workbook |
| X16 | ohne Workbook trotzdem lesen | 1 |

## Task 2: OLE unter OOXML-Namen

- `cfb.ole_kind` ersetzt `ole_verdict` (einziger Aufrufer war dispatch). Neu gelesen werden die Links (links, rechts, Kind) jedes Verzeichniseintrags; die Spitze des Baums ist das Kind des Wurzeleintrags und dessen Geschwister, mit Besuchsmenge.
- `_run_ooxml_route`: encrypted -> skipped(encrypted), word -> `legacy_doc.extract_doc`, excel -> `legacy_xls.extract_xls`, legacy -> skipped(legacy_format), None -> Office-Leser wie bisher.
- RED: test_cfb gegen einen Stub `ole_kind -> None`: 29 failed, 29 passed; test_extract_documents: 5 failed (die fünf neuen Lesefälle). GREEN: 273 passed in den fünf betroffenen Testdateien.
- Gegenproben: Y1 flache Namen statt Baumspitze 14 rot; Y3 Excel bleibt legacy_format 2 rot; Y4 Word bleibt legacy_format 3 rot; Y5 Route statt Inhalt entscheidet 3 rot; Y6 legacy geht den alten Weg 6 rot. Nicht geprobt: Baumdurchlauf ohne Besuchsmenge, weil der Eingriff eine Endlosschleife mit wachsender Liste wäre (Speicher, siehe Abweichung 6); der Test `test_a_cycle_in_the_tree_of_the_root_ends` belegt das Ende positiv.
- `grep -n "LEGACY_FORMAT" dispatch.py cfb.py`: nur der Zweig `case "legacy"` in dispatch.py (cfb.py kennt keine Urteile mehr).

## Commits

| Commit | Inhalt |
|---|---|
| 5d6f1be6 | feat(31-06): read legacy Excel .xls and OLE Word/Excel under OOXML names |

## Gates und CI

- Lokal vor 5d6f1be6: ruff check (src, tests, ../scripts) grün, ruff format grün (227 Dateien), pyright latest 0 Fehler, vulture grün, volle Suite **5187 passed, 27 skipped**. PACKAGE_TREE_HASH_TODAY `b69c625d...5585a`, PACKAGE_FILES_TODAY 77, Journalabsatz "Plan 31-06".
- Push `3ec167fc..5d6f1be6`, alle sieben success: Python gates **38119372322** (5198 passed, 14 skipped), Integration **38119372398**, Resilience **38119372297**, HaRP deploy **38119372306**, Multi-arch image **38119372299**, Security scans 38119372330, OpenSSF Scorecard 38119372327. PHP-Gates liefen nicht (kein php/-Pfad berührt).

## Deviations from Plan

**1. [Rule 2] Kettenprüfung vor xlrd ist nötig, nicht optional.** Der Plan ließ offen, ob xlrd die Zyklen selbst besteht. Er besteht sie nicht: MiniFAT-Zyklus und eine über das Stromende laufende Ministrom-Kette sind Endlosschleifen (Quelltext und X1). Umgesetzt mit der 31-05-Logik.

**2. [Rule 2] ENDOFCHAIN-Prüfung in walk_stream (wirkt auch für .doc).** Eine Prüfung nur bis zur Stromlänge übersieht eine Kette, die hinter dem letzten Sektor weiterläuft; xlrd folgt ihr. Die Spezifikation verlangt ENDOFCHAIN am Kettenende; die drei .doc-Fixtures und alle 31-05-Tests bleiben grün. Ein .doc mit sauberem Inhalt, aber nicht abgeschlossener Kette endet jetzt als failed(corrupt) statt gelesen; im Audit 31-15 gegen Bestandsdateien prüfen.

**3. Kettenprüfungen nach cfb.py verschoben.** `_check_fat_size`, `_read_stream`-Kettenlauf und `_visit_once` aus legacy_doc.py sind jetzt `cfb.check_fat_size`, `cfb.walk_stream`, `cfb._visit_once`; legacy_doc.py nicht in der Dateiliste des Plans, aber eine Kopie wäre die zweite Stelle, an der dieselbe Prüfung auseinanderläuft. Folge: detail einer .doc mit Kettenfehler heißt `findling.extract.cfb.CorruptCompoundFile` statt `...legacy_doc.CorruptDocument`. `_with_difat` aus test_legacy_doc.py ist als `conftest.cfb_with_difat` für beide Testdateien da.

**4. Zellzählung weicht im Ergebnis von XLSX ab (Regel gleich).** Plan: "gleiche Zählweise wie extract_xlsx". Gemessen zählt extract_xlsx das Rechteck, weil openpyxl im read-only-Modus jede Zeile auf Blattbreite auffüllt und Leerzeilen liefert; dann wäre biff8-far-cell `too_many_cells`, der Plan verlangt aber `indexed`. Umgesetzt: gezählt wird, was die Bibliothek liefert (leere Zellen eingeschlossen), wie bei XLSX; mit ragged_rows liefert xlrd weniger. Im Modul-Docstring und README beschrieben.

**5. Plan-Widerspruch "OLE ohne bekannten Stream: skipped(legacy_format) wie bisher".** Bisher endete eine solche Datei beim Office-Leser als failed(corrupt) (Test `test_a_compound_file_without_a_known_stream_keeps_the_old_way`). Beibehalten, also "wie bisher" statt der Aktionszeile "other -> legacy_format". legacy_format behalten: PowerPoint und bekannte Namen außerhalb der Baumspitze (eingebettete Objekte).

**6. Gegenprobe X1 lief beim ersten Mal 2 h 55 min.** Die Kindprozesse der Hängerfälle wuchsen im Speicher (xlrd hängt bei jedem Durchlauf an eine Liste), der Elternprozess wartete 8 s plus 10 s Join, bei rund 2 GB freiem RAM swappte der Rechner. Behoben im Test: Timer-Thread im Kind beendet es nach 10 s per `os._exit`, der Elternprozess bricht ab, sobald das Kind tot ist. Danach dauert X1 72 s. Das schützt auch CI-Runner, falls eine Regression den Hänger zurückbringt.

**7. [Rule 3] os.devnull als Logsenke verletzte das Dateiwege-Gate** (`test_extract_edge_paths`, `open(..., "w")` zählt als Schreibzugriff). Ersetzt durch ein Objekt mit `write()`, das nichts behält.

**8. Logtest im frischen Interpreter statt caplog/capsys.** xlrds Standard-Logdatei ist das `sys.stdout` zur Importzeit; unter pytest ist das die globale Erfassung, die capsys nicht sieht. Der Test startet `sys.executable -c ...` mit `logging.basicConfig(level=DEBUG, stream=stderr)`, hängt 100 Byte an die Fixture (xlrd warnt dann über die Dateigröße) und verlangt stdout nur mit der eigenen Zeile und stderr leer, ohne "geheimblatt". Gegenprobe X5 rot.

**9. Zusätzliche Fälle:** FAT größer als die Datei (weil der .xls-Leser jetzt olefile fragt), Book hinter leerem Workbook (xlrd liest dann Book), FAT-Kette über das Stromende, eingebettete Objekte und Baumzyklus in test_cfb, Fehlertext mit Blattname gelangt nicht ins detail.

**10. Werkzeugbefund:** In Bash-Heredocs wurden `\n`- und `\r\n`-Escapes zu echten Zeilenumbrüchen; nur Hilfsskripte im Scratchpad betroffen, Repo-Dateien per Byte-Prüfung kontrolliert (Code rein ASCII, `\u`-Escapes in legacy_doc.py unverändert).

## Known Stubs

Keine. extract_msexcel ist absichtlich noch nicht in Dispatch und Allowlist für `application/vnd.ms-excel`; das ist Plan 31-10.

## Threat Flags

Keine neue Fläche über das Register hinaus. T-31-16 (ragged_rows, tracemalloc-Test), T-31-17 (Zellgrenze, RLIMIT_AS als Netz), T-31-18 (Nullsenke, Logtest im frischen Interpreter, detail ohne Meldungstext), T-31-19 (Inhalt entscheidet, Test doc-as-xlsx, xls-as-docx, doc-as-pptx) umgesetzt.

## Requirements

FMT-04 ist als Extraktor erfüllt, für Nutzer aber erst mit 31-10 durchsuchbar; FMT-04 bleibt in REQUIREMENTS.md offen. Word- und Excel-Altdateien unter OOXML-Namen werden ab diesem Stand gelesen (Leser für die legacy_format-Zeilen des Nachholwegs 31-11).

## Offene Punkte

- 31-10: .xls über extract_msexcel in Allowlist und Dispatch freischalten, danach FMT-04 auf Complete.
- 31-11: legacy_format-Zeilen nachholen; PowerPoint bleibt dabei legacy_format.
- 31-12: biff8-values.xls als Saat (zellquendel/blattquendel) und eine OLE-.docx.
- 31-14: docs/formats.md: Zellzählung .xls gegenüber .xlsx, legacy_format nur noch für PowerPoint und eingebettete Objekte.
- 31-15: ENDOFCHAIN-Prüfung und FAT-Schranke an echten Bestandsdateien prüfen.

## Self-Check: PASSED

legacy_xls.py, test_legacy_xls.py, beide .xls-Fixtures, README, Skript und diese SUMMARY vorhanden; Commit 5d6f1be6 in der Historie, origin/main auf 5d6f1be6; alle sieben CI-Läufe success. STATE.md und ROADMAP.md von Hand nachgezogen (gsd-sdk hatte die Statuszeile von STATE.md überschrieben, verworfen): 6/15, nächster Plan 31-07, FMT-03 und FMT-04 in REQUIREMENTS.md offen.
