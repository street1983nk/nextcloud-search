---
phase: 31-neue-formate-und-nachholweg
plan: 05
subsystem: Extraktion (extract/legacy_doc.py)
tags: [fmt-03, d-31-03, doc, olefile, ms-doc, piece-table, cfb, dos]
requires:
  - phase: 31-04
    provides: "Stand 04ac68a2, alle Gates grün"
  - phase: 31-01
    provides: "olefile==0.47 gepinnt"
provides:
  - "extract_msword(path) -> ExtractionOutcome: Sniff OLE / RTF / DOCX / HTML unter Word-Namen, sonst skipped(unsupported_variant)"
  - "extract_doc(path) -> ExtractionOutcome: olefile (DEFECT_INCORRECT) plus Piece Table nach [MS-DOC] 2.4.1"
  - "decode_compressed(raw) mit der Sondertabelle aus [MS-DOC] 2.9.73"
  - "CorruptDocument als benannte Ausnahme (detail findling.extract.legacy_doc.CorruptDocument)"
  - "conftest.build_cfb(..., streams=...) und cfb_entry(start, size, child, right) für Dateien mit Strominhalt"
  - "drei LibreOffice-Fixtures mit Suchwörtern wortquendel, glyphquendel, zellquendel (Saat für 31-12)"
affects: [31-06 OLE unter OOXML-Namen (extract_doc), 31-10 Freischaltung .doc, 31-12 Saatdateien, 31-15 Audit]
tech-stack:
  added: []
  patterns: ["Sektorketten nach olefile ein zweites Mal mit Besuchsmenge ablaufen", "Kopfzeilenprüfung vor der Bibliothek, wenn deren Aufwand quadratisch wächst", "Lesebudget gleich doppelter Zeichendeckel, danach truncated"]
key-files:
  created:
    - backend/src/findling/extract/legacy_doc.py
    - backend/tests/test_legacy_doc.py
    - backend/tests/fixtures/legacy/README.md
    - backend/tests/fixtures/legacy/word97-latin.doc
    - backend/tests/fixtures/legacy/word97-unicode.doc
    - backend/tests/fixtures/legacy/word97-table-field.doc
    - scripts/dev/make_legacy_fixtures.py
  modified:
    - backend/tests/conftest.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "fObfuscated allein wird ignoriert, wie FibBase es verlangt (MUST be ignored ohne fEncrypted); XOR-verschleierte Dateien tragen immer fEncrypted und enden als skipped(encrypted)"
  - "Vor olefile: deklarierte FAT-Sektorzahl höchstens Bedarf der Dateigröße plus 1, sonst failed(corrupt); gemessen kosten 20 000 deklarierte FAT-Sektoren olefile 29 s"
  - "Nach olefile: Ketten von WordDocument, Tabellenstrom und Ministrom einmal mit Besuchsmenge abgelaufen, weil olefile Zyklen innerhalb der deklarierten Länge stillschweigend als wiederholte Sektoren liefert"
  - "Ganzer Text der Piece Table (auch Fußnoten, Kopfzeilen, Kommentare); gelöschter Text unter Änderungsverfolgung wird mit indexiert (bekannte Grenze, im Modul-Docstring)"
  - "Lesebudget 2x max_text_chars, weil Feldcodes erst nach dem Lesen fallen; nicht vollständig gelesen heißt truncated"
  - "Interne olefile-Tabellen (fat, minifat, kids_dict, isectStart, size, is_minifat, sectorsize) stehen nicht im typeshed-Stub; Zugriff untypisiert mit Typprüfung, olefile ist auf 0.47 gepinnt"
metrics:
  duration: "ca. 90 min (davon 2x volle Suite lokal ca. 21 min, CI ca. 20 min)"
  completed: 2026-10-11
  tasks: 2
  files: 9
---

# Phase 31 Plan 05: .doc-Extraktor (FMT-03) Summary

Word-97-bis-2003-Dateien werden ohne LibreOffice gelesen: olefile öffnet die Verbunddatei, der Text kommt über FIB, Clx und Piece Table nach [MS-DOC], komprimierte Stücke mit der Sondertabelle statt cp1252; verschlüsselte, alte und kaputte Dateien enden mit benanntem Urteil in unter 5 s. Noch nicht freigeschaltet (31-10).

## Spezifikationsbelege

**A1 (fcClx/lcbClx bei 0x01A2/0x01A6): bestätigt.**
- [MS-DOC] 2.5.1 Fib (learn.microsoft.com/.../ms-doc/9aeaa2e7-4a45-468e-ab13-3f6193eb9394): FibBase 32 Byte, csw MUST 0x000E, fibRgW 28 Byte, cslw MUST 0x0016, fibRgLw 88 Byte, cbRgFcLcb (0x005D bei nFib 0x00C1, 0x0088 bei 0x0101), dann fibRgFcLcbBlob ab 32+2+28+2+88+2 = 0x9A.
- [MS-DOC] 2.5.6 FibRgFcLcb97 (.../0c9df81f-98d0-454e-ad84-b612cd05b1a4): Feldliste per Skript abgezählt, die ersten 66 Felder sind 33 saubere fc/lcb-Paare (fcStshfOrig bis lcbSttbfAssoc), fcClx ist Feld 66 = Paar 33: 0x9A + 33 x 8 = 0x01A2, lcbClx 0x01A6.
- Gegen einen fremden Schreiber geprüft: in allen LibreOffice-Fixtures zeigt 0x01A2 auf ein Byte 0x02 (Pcdt) in 1Table, lcbClx jeweils 21 Byte endet im Strom (Test `test_the_clx_offsets_hold_in_a_file_that_libreoffice_wrote`, Gegenprobe mit 0x01A0 rot).
- Das Modul prüft csw, cslw und cbRgFcLcb und liest dann an den festen Offsets.

**A2 (Steuerzeichen): bestätigt und ergänzt.**
- [MS-DOC] 2.8.25 Plcfld (.../751b09bb-72f0-45ef-8e87-666dea68219f): 0x13 Feldanfang, 0x14 Trenner (optional), 0x15 Feldende, Felder verschachtelt (ABNF `Field = Begin *Field [Sep] *Field End`); Anweisungen zwischen Anfang und Trenner bzw. Ende, Ergebnis zwischen Trenner und Ende.
- sprmCFSpec in 2.6.1 Character Properties: 0x01 Bildanker, 0x02 Fußnotenreferenz, 0x03/0x04 Linien, 0x05 Kommentarreferenz, 0x08 Zeichnungsobjekt.
- 2.4.3 Overview of Tables: Zellmarke und Zeilenmarke sind bei Tiefe 1 beide 0x07.
- Nicht in der Spezifikation, an LibreOffice-Ausgabe gemessen: 0x1F weiches Trennzeichen (entfernt), 0x1E geschütztes Trennzeichen (wird `-`).
- FcCompressed (2.9.73): Sondertabelle 0x82..0x9F mit 24 Einträgen; 0x80, 0x8E, 0x9E fehlen, also nicht cp1252. Der Test vergleicht alle 256 Bytes gegen die von der Seite abgeschriebene Tabelle.

## Task 1: Fixtures, CFB-Builder, Tests (RED)

- `scripts/dev/make_legacy_fixtures.py` einmal gelaufen: LibreOffice 26.2.4.2 (Windows, Build-ID 0229ac93...), `.fodt`-Quellen, `--convert-to "doc:MS Word 97"`, eigenes Profil im Temp-Verzeichnis. Drei Dateien, SHA-256 im Test und in `fixtures/legacy/README.md`.
- Gemessen an den Fixtures: nFib 0x0101, je ein UTF-16-Stück (LibreOffice schreibt keine komprimierten Stücke), 1Table und bei zwei Dateien auch WordDocument im Ministrom.
- `build_cfb` um `streams` erweitert (FAT-Sektoren zuerst, dann Verzeichnis, dann Ströme, Polsterung auf 4096 Byte, Baum als Kette rechter Geschwister). Byte-Gleichheit für alle bisherigen Aufrufer gegen die alte Fassung aus HEAD geprüft (9 Aufrufmuster plus cfb_entry, identisch); `test_cfb.py` und `test_extract_documents.py` 120 passed.
- RED: zuerst Sammelfehler `ModuleNotFoundError: findling.extract.legacy_doc`; dann gegen einen Stub (`skipped(empty_text)`, `decode_compressed` liefert ""): **73 failed, 5 passed**, alle 73 am Verhalten rot. Grün gegen den Stub blieben die drei Digest-Tests, `test_the_msword_entry_reads_a_real_doc_like_the_doc_reader` und `test_the_clx_offsets_hold_in_a_file_that_libreoffice_wrote`; alle fünf per Gegenprobe belegt (unten G11, Digest mit gekipptem Byte rot, Offset 0x01A0 rot).
- Unterwegs: zwei Parameter-IDs sprengten unter Windows die Umgebungsvariable `PYTEST_CURRENT_TEST` (über 32767 Zeichen); lesbare `ids` gesetzt.

## Task 2: legacy_doc.py (GREEN)

- 78 passed beim ersten Lauf (am Ende 78 Fälle in 1,4 s; der DIFAT-Fall schreibt eine 7-MB-Datei).
- Gegenproben (je ein Eingriff in legacy_doc.py, Testdatei gelaufen, zurückgebaut, Datei per `filecmp` identisch):

| Probe | Eingriff | rot |
|---|---|---|
| G1 | kein zweiter Kettenlauf | 5: FAT-Zyklus WordDocument und 1Table, MiniFAT-Zyklus WordDocument und 1Table, Zyklus in der Kette des Ministroms |
| G2 | keine FAT-Größenprüfung | 1: 20 000 deklarierte FAT-Sektoren (Lauf 26,7 s statt 1,4 s) |
| G3 | RecursionError nicht gefangen | 1: Verzeichnisbaum mit 3000 Einträgen |
| G4 | cp1252 statt Sondertabelle | 2: Byte 0x80, alle 256 Bytes |
| G5 | fObfuscated allein = verschlüsselt | 1 |
| G6 / G6b | keine Längenprüfung komprimiert / Unicode | 1 / 4 |
| G7 | keine Prüfung aufsteigender CPs | 1 |
| G8 / G8b | kein truncated-Flag / Budget nur 1x Deckel | je 1 |
| G9 | keine Clx-Grenze | 1: riesiges lcbClx |
| G10 | BOM nicht entfernt | 1 |
| G11 | OLE an den RTF-Leser | 1 |
| G12 | verschachtelte Felder flach | 1 |
| G13 | 0x07 nicht auf Tab | 2 |
| G14 | Prc nicht übersprungen | 1 |
| G15 | csw/cslw/cbRgFcLcb ungeprüft | 3 |
| G16 | Tabellenstrom ohne fWhichTblStm | 1 |
| G17 | nFib ungeprüft | 3 |

- Zwei Tests wurden durch die Gegenproben geschärft: der MiniFAT-Zyklus lag zuerst im FIB-Bereich und wäre ohne Kettenlauf trotzdem als corrupt geendet (G1 zuerst nur 3 rot); jetzt liegt er hinter allem, was der Leser parst. Der Fib-Zähltest verschob zuerst das ganze Layout; jetzt wird nur der Zähler gepatcht (G15 zuerst 0 rot).
- Kettenschutz, jeweils Urteil benannt und unter 5 s, mit Kontrolle ohne Defekt: FAT-Zyklus (beide Ströme), FAT-Kette hinter dem Dateiende (olefile: OleFileError), Kette endet zu früh, DIFAT-Zyklus in einer 7-MB-Datei mit 110 FAT-Sektoren (olefile: OSError "incorrect end of DIFAT"; Kontrolle mit ENDOFCHAIN liest), FAT größer als die Datei, MiniFAT-Zyklus (beide Ströme), MiniFAT-Kette hinter dem Ministrom, Zyklus in der Kette des Ministroms. Der DIFAT-Zyklus selbst wird von olefile erkannt; unsere Größenprüfung sorgt dafür, dass olefile dorthin in kurzer Zeit kommt.
- Akzeptanz: `grep -nP "\x{2013}|\x{2014}" legacy_doc.py` leer, `cp1252` nur im Docstring, der sagt warum nicht; legacy_doc.py, test_legacy_doc.py und das Skript reines ASCII.
- PACKAGE_TREE_HASH_TODAY `ae65ecac...c26b398`, PACKAGE_FILES_TODAY 76, Journalabsatz "Plan 31-05".

## Commits

| Commit | Inhalt |
|---|---|
| faa11e16 | feat(31-05): read legacy Word .doc without LibreOffice |

## Gates und CI

- Lokal vor faa11e16: ruff check (Backend und `../scripts` mit Backend-Konfiguration) grün, ruff format grün (206 + 20 Dateien), pyright latest 0 Fehler, vulture grün, volle Suite **5133 passed, 25 skipped** (562 s).
- Push `04ac68a2..faa11e16`, alle sieben success: Python gates **38105517809** (5144 passed, 14 skipped), Integration **38105517797**, Resilience **38105517848**, HaRP deploy **38105517806**, Multi-arch image **38105517791**, Security scans 38105517854, OpenSSF Scorecard 38105517810. PHP-Gates liefen nicht (kein php/-Pfad berührt).

## Deviations from Plan

**1. [Rule 2] FAT-Größenprüfung vor olefile.** Gemessen: olefile 0.47 hängt jeden FAT-Sektor per Arraykopie an; 20 000 deklarierte FAT-Sektoren in einer 180-kB-Datei kosten 29 s, quadratisch wachsend. Die "festen Schleifenlängen" aus T-31-13 schützen davor nicht. Prüfung: deklarierte Zahl höchstens Bedarf aus der Dateigröße plus 1.

**2. [Rule 2] Zweiter Kettenlauf nach olefile.** olefile erkennt einen Zyklus innerhalb der deklarierten Stromlänge nicht, es liefert die wiederholten Sektoren als Strominhalt (gemessen, G1). Ohne den Lauf wäre ein FAT- oder MiniFAT-Zyklus als indexierter Mülltext geendet statt mit benanntem Urteil.

**3. [Rule 2] RecursionError gefangen.** olefile baut den Verzeichnisbaum rekursiv; eine Kette von 3000 Geschwistern endet in RecursionError (gemessen). Urteil failed(corrupt) mit detail `builtins.RecursionError`.

**4. [Spezifikation vor Plan] fObfuscated allein.** Der Plan nennt "fObfuscated gesetzt -> encrypted". FibBase sagt: fObfuscated gilt nur bei fEncrypted, sonst MUST be ignored. Umgesetzt nach Spezifikation: fEncrypted plus fObfuscated -> encrypted (Test), fObfuscated allein -> gelesen (Test, G5).

**5. Lesebudget 2x Deckel statt Ende am Deckel.** Feldcodes fallen erst nach dem Lesen; am Deckel zu stoppen hätte ein Dokument, dessen erste Zeichen Feldanweisungen sind, als empty_text enden lassen (Test, G8b). Wer nicht alles gelesen hat, markiert truncated.

**6. Zusätzliche Prüfungen aus der Spezifikation:** csw, cslw, cbRgFcLcb (2.5.1), cbGrpprl nicht negativ und höchstens 0x3FA2 (2.9.210), Pcdt-Länge 4 + 12n (2.9.178), aufsteigende CPs (2.8.35), lcbClx größer 0 (2.5.6).

**7. Fixture-Grenze:** LibreOffice schreibt nur UTF-16-Stücke. Komprimierte Stücke und Sondertabelle prüfen Dateien, die der Test nach [MS-DOC] baut. Eine echte Word-Datei mit komprimiertem Text (etwa aus dem Apache-POI-Testkorpus) wäre ein weiterer Beleg; bewusst nicht geholt, weil Fremddatei mit eigener Lizenzannotation.

**8. [Rule 3] Gate "file travel path writes":** `open(path, "rb")` zählte das AST-Gate als Schreibzugriff (es liest den Modus aus dem ersten Argument). Umgestellt auf `Path(path).open("rb")` wie in office.py, Gate unverändert.

**9. Werkzeugbefund wie in 31-04:** Das Schreibwerkzeug hat `\u`-Escapes in Modul und Tests in echte Zeichen verwandelt (darunter U+2013/U+2014 in der Sondertabelle). Per Skript zurück in Escapes gesetzt und vor dem Commit geprüft.

## Known Stubs

Keine. extract_msword ist absichtlich noch nicht in dispatch und Allowlist eingehängt; das ist Plan 31-10 (OLE unter OOXML-Namen: 31-06).

## Threat Flags

Keine neue Fläche. T-31-13 (FAT/DIFAT/MiniFAT-Zyklen, riesige lcbClx, FAT größer als die Datei, tiefer Verzeichnisbaum), T-31-14 (jede Länge gegen ihren Strom, Tests), T-31-15 (nur Klassenname als detail, Test ohne Inhalt und Pfad) umgesetzt und per Gegenprobe belegt.

## Requirements

FMT-03 ist als Extraktor erfüllt, aber für Nutzer noch nicht durchsuchbar: die Freischaltung kommt in 31-10. FMT-03 bleibt in REQUIREMENTS.md offen.

## Offene Punkte

- 31-06: extract_doc für OLE-Word unter .docx-Namen nutzen.
- 31-10: .doc über extract_msword in Allowlist und Dispatch freischalten, danach FMT-03 auf Complete.
- 31-12: die drei Fixtures als Saat (Suchwörter wortquendel, glyphquendel, zellquendel).
- 31-15: im Audit prüfen, ob die FAT-Schranke "Bedarf plus 1" an echten Bestandsdateien hält.

## Self-Check: PASSED

legacy_doc.py, test_legacy_doc.py, drei Fixtures, README, Skript und diese SUMMARY vorhanden; Commit faa11e16 in der Historie, origin/main auf faa11e16; alle sieben CI-Läufe success.
