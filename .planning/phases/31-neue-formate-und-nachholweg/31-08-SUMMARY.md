---
phase: 31-neue-formate-und-nachholweg
plan: 08
subsystem: Extraktion (extract/archive.py, config.py)
tags: [fmt-02, d-31-07, d-30-03, zip, zip64, quine, zip-bomb, shared-budget, blocker-2, befund-10]
requires:
  - phase: 31-04
    provides: "mail.clean_display_name für die Namen der Mitglieder, mail.extract_eml als Mitgliedsleser"
  - phase: 31-05
    provides: "legacy_doc.extract_msword als Mitgliedsleser"
  - phase: 31-06
    provides: "legacy_xls.extract_msexcel, dispatch._run_ooxml_route mit OLE-Sniff; Kindprozess mit Selbstabbruch als Testmuster"
  - phase: 31-07
    provides: "Stand d7a9f3a2, eine malloc-Arena im Extraktionskind, 512 MiB Adressraum"
provides:
  - "extract_zip(path) -> ExtractionOutcome: Abschnitte U+001C, Anzeigename, Zeilenumbruch, Mitgliedstext"
  - "count_central_directory(handle, size, *, limit): Köpfe PK\\x01\\x02 selbst gezählt wie zipfile, höchstens limit + 1"
  - "_ArchiveBudget: Einträge, Verzeichnisbytes, deklarierte und gelesene Bytes, Mitglieder mit Text, Frist, gemeinsam für alle Ebenen"
  - "config.py: ARCHIVE_MAX_ENTRIES 10 000, ARCHIVE_MAX_CENTRAL_DIRECTORY_BYTES 8 MiB, ARCHIVE_MAX_RATIO 100, ARCHIVE_RATIO_MIN_BYTES 1 MiB, ARCHIVE_MAX_DEPTH 2, ARCHIVE_MAX_TEXT_MEMBERS 1000, ARCHIVE_TIME_SHARE 0.75, ARCHIVE_MEMBER_MARK"
  - "Messbericht docs/measurements/2026-10-formate-v15, Abschnitt ZIP-Grenzwerte"
affects: [31-09 Snippet nennt die innere Datei (liest die Marke U+001C), 31-10 Freischaltung application/zip, 31-11 Nachholweg, 31-12 Saat .zip, 31-14 docs/formats.md, 31-15 Audit]
tech-stack:
  added: []
  patterns:
    - "Vorprüfung als genaue Portierung der Bibliotheksstelle (CPython _EndRecData/_EndRecData64/_RealGetContents), Konsistenztest gegen die Bibliothek"
    - "Ein Budget-Objekt für alle Verschachtelungsebenen statt Grenzen je Ebene"
    - "Echtes ZIP-Quine zur Testlaufzeit gebaut (Deflate-Blöcke gleicher Länge, CRC-Fixpunkt als lineares System über GF(2))"
key-files:
  created:
    - backend/src/findling/extract/archive.py
    - backend/tests/test_extract_archive.py
  modified:
    - backend/src/findling/config.py
    - backend/tests/test_extract_edge_paths.py
    - backend/tests/test_measurement_scripts.py
    - docs/measurements/2026-10-formate-v15/README.md
decisions:
  - "Alle Startwerte von D-31-07 bleiben (gemessen bestätigt); neu ist nur die Längengrenze des Zentralverzeichnisses, 8 MiB"
  - "Auch die Verzeichnislänge kommt aus dem gemeinsamen Budget, damit ein äußeres und ein inneres Verzeichnis, die gleichzeitig offen sind, zusammen unter der Grenze bleiben"
  - "zipfile liest den ZIP64-Locator immer, nicht nur bei 0xFFFF-Feldern; die Vorprüfung bildet das genau ab"
  - "Mitgliedsdateien liegen neben der Scratch-Datei als <scratch>.m<n>.part statt in einem eigenen Verzeichnis: Reste eines gekillten Kinds räumt der Sweep des Pollers (*.part)"
  - "Ein Mitglied, an dem sein Leser scheitert, bleibt Name; MemoryError geht weiter (Adressraum des Kinds ist erschöpft)"
  - "Ein inneres ZIP mit kaputtem Verzeichnis bleibt Name, ein Overlap in jeder Ebene ist archive_limit für die ganze Datei"
  - "Zeichendeckel max_text_chars beendet die Mitgliedsschleife vor dem nächsten Mitglied (indexed(truncated)), damit die Texte nicht über den Deckel hinaus im Speicher wachsen"
metrics:
  duration: "ca. 120 min"
  completed: 2026-10-11
  tasks: 2
  files: 6
---

# Phase 31 Plan 08: ZIP-Extraktor mit eigener Kopfzählung und gemessenen Grenzen Summary

ZIP-Dateien werden als ein Dokument gelesen: jedes Mitglied steht als Abschnitt mit der Marke U+001C und seinem bereinigten Namen im Text, lesbare Mitglieder mit ihrem Text, ohne OCR. Vor `ZipFile` zählt archive.py die Köpfe des Zentralverzeichnisses selbst, nach derselben Schleife wie zipfile; die Zahl im Endsatz (auch ZIP64) wird nie geglaubt. Alle Grenzen ziehen aus einem Budget für alle Ebenen. Noch nicht in Allowlist und Dispatch (31-10), Snippet mit innerer Datei folgt in 31-09.

## Task 1: Messungen (11.10.2026, i5-1335U, Windows 11, CPython 3.13.13, je drei Läufe, Median)

| Messung | Ergebnis |
|---|---|
| (1) ZipFile, leere Einträge | 10 000: 5,47 MiB / 0,34 s; 100 000: 55,88 MiB / 3,23 s |
| (1) ZipFile, nur Verzeichnis | Spitze etwa 2 x Länge + 0,55 KiB je Kopf; 10 000 x 4 KiB-Namen 82,49 MiB; **beide Grenzen (10 000, 8 MiB) 19,47 MiB / 0,29 s** |
| (1) eigene Zählung | konstant 0,064 MiB (64-KiB-Blöcke); 10 000 in 0,055 s, 100 000 in 0,55 s, 8 MiB in 0,091 s; 41 MB abgelehnt vor dem Lesen |
| (2) Rate, zehn reale Dateien ab 1 MB | 1,1 (DOCX) bis 17,9 : 1 (Log); Nullbytes 1028,6 : 1 |
| (3) Zeit je Mitglied | 200 DOCX/PDF/TXT in 2,34 s = 11,7 ms; 1 000 in rund 12 s von 90 s |
| (4) A3 | ä ö ü Ä Ö Ü ß in cp437 und cp850 gleiche Bytes; bestätigt |
| (5) A10 | alle Offsets gegen APPNOTE 6.3.10 und CPython bestätigt; Befund: Locator wird immer gelesen |

Festgelegt und begründet (Tabelle im Bericht): Einträge 10 000, Verzeichnislänge 8 MiB (neu), entpackt 256 MiB, Rate 100 : 1 ab 1 MiB, Tiefe 2, 1 000 Mitglieder mit Text, Zeitanteil 0,75. **Keine Abweichung vom Startwert.** Begründungen in einem Satz: 10 000 liegen weit über einer gepackten Dokumentenmappe und zwei Größenordnungen unter dem Adressraum; 8 MiB lassen 838 Byte je Kopf (real 100 bis 300) und halten ZipFile bei 19,5 MiB; 100 : 1 hat Faktor 5 Abstand zur redundantesten realen Datei und ist ein Zehntel der Deflate-Obergrenze; 1 000 Mitglieder brauchen ein Siebtel des Zeitanteils.

CPython-Quelle (lokal, `Lib/zipfile/__init__.py` 3.13.13): `_EndRecData64` Zeilen 252 bis 309, `_EndRecData` 312 bis 369, `_RealGetContents` 1460 bis 1540 (concat 1475/1476, Verzeichnisbeginn 1482, `while total < size_cd` ab 1489, Overlap-Prüfung in `open` 1698 bis 1709).

## Task 2: archive.py

- Stufe 1: `_end_record`/`_end_record64` portieren `_EndRecData`/`_EndRecData64` (Kommentarsuche über 65 557 Byte, Locator immer, vorangestellte Daten, Prüfung `diroffset + dirsize == reloff`); Beginn = Lage des Endsatzes minus Länge. Länge gegen Budget, dann `count_central_directory` über ein 64-KiB-Fenster bis höchstens Grenze + 1, falsche Signatur oder kurzer Kopf -> `CorruptDirectory` -> failed(corrupt).
- Stufe 2: `ZipFile(path)`, Summe `file_size` gegen das Budget, Rate je Mitglied ab 1 MiB, Tiefe vor dem Auspacken eines inneren ZIP.
- Stufe 3: Mitglieder nach Endung (`_MEMBER_READERS`: pdf nur Textschicht, docx/pptx/xlsx über `_run_ooxml_route` mit OLE-Sniff, odt/ods/odp, html/htm/xhtml, rtf, txt/md/csv, eml, doc, xls; zip mit Tiefe + 1 und demselben Budget). Verschlüsselt (Bit 0x1), Methode außer 0/8/12/14, unbekannte Endung, über `max_file_bytes`: nur Name. Strom in `<scratch>.m<n>.part` mit Bytezählung, im finally gelöscht. U+001C aus jedem Mitgliedstext entfernt, Namen über `clean_display_name`.
- Urteile: Grenze -> skipped(archive_limit); Overlap-BadZipFile -> archive_limit; andere BadZipFile, NotImplementedError, UnicodeDecodeError beim Öffnen -> failed(corrupt) mit Klassenname; alle Dateien verschlüsselt -> skipped(encrypted); Mitgliederdeckel, Zeichendeckel, Zeitanteil -> indexed(truncated). Kein Log.
- Akzeptanz: `grep -n "extractall\|\.extract(" archive.py` leer, `PK\x01\x02` trifft (beides auch als Test).

### RED

Gegen einen Stub (`extract_zip` -> skipped(empty_text), `count_central_directory` -> 0): **44 failed, 3 passed**. Grün blieben die Quine-Bauprobe (prüft nur den Testhelfer), `test_an_empty_zip_file_is_empty_text` und `test_no_member_name_reaches_the_log`; beide unten per Gegenprobe (G16, G15) belegt. Rote Erstausgabe der Blocker-2- und Befund-10-Fälle, je gleich:

```
E           reason: <Reason.EMPTY_TEXT: 'empty_text'> != <Reason.ARCHIVE_LIMIT: 'archive_limit'>
```

(EOCD 5/10 001, ZIP64 5/10 001, Verzeichnislänge, 50 innere ZIPs Einträge, 50 innere ZIPs Bytes; die Gegenproben einzelnes inneres ZIP rot mit `assert <State.SKIPPED> is <State.INDEXED>`.) Später ergänzt und gegen die fertige Fassung per Gegenprobe belegt: Zeichendeckel (G18), geschärfter Traversal-Fall (G10).

### GREEN und Gegenproben

48 passed in 7,3 s (lokal). Bombenfälle im gespawnten Kind mit Timer-Selbstabbruch nach 10 s und Zeitmessung im Kind (< 5 s gefordert), jeweils rund 0,4 s: EOCD 5/10 001 und ZIP64 5/10 001 (ZipFile-Aufrufe 0), Quine (ZipFile-Aufrufe genau 2), Tiefe 3, 50 innere ZIPs (Einträge und Bytes), Rate, Overlap, Traversal-Namen, Verschlüsselung (gemischt, alle, AES/Deflate64), cp437- und UTF-8-Namen.

Gegenproben (je ein Eingriff, Testdatei gelaufen, zurückgebaut, Bytes gegen Sicherung verglichen):

| Probe | Eingriff | rot |
|---|---|---|
| G1 | Eintragszahl aus `zipfile._EndRecData` statt eigener Zählung | 3: EOCD 5/10 001, ZIP64 5/10 001, falsche Signatur (ZipFile-Aufruf statt 0) |
| G2 | Budget je Ebene | 2: 50 innere ZIPs Einträge, 50 innere ZIPs Bytes |
| G3 | keine Verzeichnislänge | 1 |
| G4 | keine Tiefe | 2: Quine, Tiefe 3 |
| G5 | keine Rate | 1 |
| G6 | Overlap als kaputtes Mitglied | 1 |
| G7 | verschlüsselte Mitglieder gelesen | 3 |
| G8 | Namen nicht bereinigt | 2 |
| G9 | Marke im Mitgliedstext belassen | 1 |
| G10 | Mitglied unter seinem Namen geschrieben | 5, darunter Traversal |
| G11 / G12 / G18 | ohne Mitgliederdeckel / Zeitanteil / Zeichendeckel | je 1 |
| G13 | `max_file_bytes` ignoriert | 1 |
| G14 | Mitgliedsdateien nicht gelöscht | 27 (Baumvergleich) |
| G15 | Mitgliedsnamen ins Log | 1 |
| G16 | ohne empty_text | 2 |
| G17 | alle verschlüsselt trotzdem indexed | 1 |

## Commits

| Commit | Inhalt |
|---|---|
| bc945400 | feat(31-08): read ZIP archives within measured limits |

## Gates und CI

- Lokal vor bc945400: ruff check (backend und ../scripts) grün, ruff format (212 Dateien) grün, pyright latest 0 Fehler, vulture grün, volle Suite **5265 passed, 27 skipped** (668 s; die zwei Warnungen stammen aus test_ocr, vorbestehend). PACKAGE_TREE_HASH_TODAY `e31b130073a882d3ecca3c6f21d5e085bf5dec564c2e12703d12fbb0d170b080`, PACKAGE_FILES_TODAY 78, Journalabsatz "Plan 31-08".
- Push `d7a9f3a2..bc945400`, CI: Python gates **38129929315** (5277 passed, 15 skipped), Multi-arch image **38129929312**, Security scans 38129929307, OpenSSF Scorecard 38129929298, Integration **38129929290**, Resilience **38129929308**, HaRP deploy **38129929344**; alle sieben success. PHP-Gates liefen nicht (kein php/-Pfad berührt).

## Deviations from Plan

**1. [Rule 2] Verzeichnislänge aus dem gemeinsamen Budget.** Der Plan prüft die Länge je Verzeichnis. Ein äußeres und ein inneres ZipFile sind gleichzeitig offen; mit einer Grenze je Ebene könnten beide zusammen das Doppelte halten. Die Länge zieht jetzt vom selben Budget wie Einträge und Bytes; `count_central_directory` prüft die feste Grenze zusätzlich.

**2. [Rule 1] ZIP64-Locator immer gelesen.** Die Plan-Skizze (Research) las den ZIP64-Endsatz nur bei 0xFFFF-Feldern. CPython liest den Locator immer; sonst wäre ein Endsatz mit kleinen Feldern plus Locator ein Umweg. Portiert wie `_EndRecData64`, Konsistenzfall "zip64-prepended".

**3. Ort der Mitgliedsdateien.** Plan: `<scratch>/m-<n>`. Umgesetzt: `<Scratch-Datei>.m<n>.part` neben der Scratch-Datei des Jobs. Das Kind kennt kein Scratch-Verzeichnis, nur den Pfad seiner Datei; mit der Endung `.part` räumt der Poller-Sweep (`*.part`) Reste eines gekillten Kinds. Die Dateiwege-Liste in test_extract_edge_paths.py hat drei neue, begründete Einträge (Lesen des Verzeichnisses, Schreiben des Mitglieds, Löschen), 10 statt 7.

**4. [Rule 2] Zeichendeckel als vierter Stopp.** Ohne ihn hätten bis zu 1 000 Mitglieder je 512 KiB Text im Speicher gesammelt. Über `max_text_chars` liest die Schleife kein weiteres Mitglied (indexed(truncated)); Test mit Aufrufzähler, G18.

**5. Testlücke selbst gefunden (G10).** Die erste Fassung des Traversal-Falls blieb unter G10 grün: `passwd` ohne Endung wird nie ausgepackt, und `/abs/pfad.txt` landete außerhalb von tmp_path (G10 legte dabei ein leeres `C:\abs` an, entfernt). Jetzt liegt die Scratch-Datei zwei Ebenen tief, ein Name `../../etc/passwd.txt` und ein absoluter Name innerhalb von tmp_path werden vom Baumvergleich gesehen; G10 rot.

**6. Echtes Quine statt Nachbildung.** Der Testhelfer baut ein 720-Byte-ZIP, dessen einziges Mitglied die Datei selbst ist (`ZipFile.read` liefert dieselben Bytes; eigener Test). Konstruktion nach Cox (2010) mit Blöcken zu 15 Byte; CRC-Fixpunkt per Gauß über GF(2).

**7. Testdaten.** `"vor\x1cnach"` (8 Byte) erkannte charset-normalizer als UTF-16; der Markentest nutzt einen natürlichen Satz. Suchwörter ohne den gesperrten Wortstamm (E-H2), z. B. `packquendel`.

**8. Mitgliedsleser fangen fremde Ausnahmen.** Für Einzeldateien übersetzt die Sandbox-Grenze Ausnahmen; im ZIP kostet ein Mitglied, an dem sein Leser scheitert, nur seinen Text. MemoryError wird weitergereicht.

## Known Stubs

Keine. `application/zip` ist absichtlich noch nicht in Allowlist und Dispatch (31-10); der Docstring von dispatch.py ("Container formats ... are not opened at all") wird dort mit angepasst.

## Threat Flags

Keine neue Fläche über das Register hinaus. T-31-23 (eigene Zählung, Längengrenze, Tests EOCD/ZIP64 mit Aufrufzähler 0, G1, G3), T-31-24 (Rate, Overlap, Quine über die Tiefe, Bytezählung, G4 bis G6), T-31-24b (gemeinsames Budget, 50 innere ZIPs, G2), T-31-25 (laufende Nummern, Baumvergleich, G10, G14), T-31-26 (clean_display_name, U+202E, G8), T-31-27 (kein Log, caplog, G15) umgesetzt.

## Requirements

FMT-02 ist als Extraktor erfüllt, für Nutzer aber erst mit 31-09 (Snippet) und 31-10 (Freischaltung) durchsuchbar; FMT-02 bleibt in REQUIREMENTS.md offen.

## Offene Punkte

- 31-09: Snippet sucht die letzte Marke U+001C vor dem Fragment und nennt den Namen bis zum Zeilenende; ein Mitglied ohne Text steht als `\x1cname\n\n\n`.
- 31-10: `application/zip` -> `extract_zip`, dispatch-Docstring, danach FMT-02 auf Complete (nach 31-09).
- 31-15 (Audit): Ein Office-Mitglied öffnet seine eigene ZipFile ohne Kopfzählung (wie eine einzelne DOCX bisher); durch `max_file_bytes` je Mitglied und die Frist begrenzt, im Audit bewerten.

## Self-Check: PASSED

archive.py, test_extract_archive.py, config.py, Messbericht (Abschnitt ZIP-Grenzwerte) und diese SUMMARY vorhanden; Commit bc945400 in der Historie, origin/main auf bc945400; alle sieben CI-Läufe success. STATE.md und ROADMAP.md von Hand nachgezogen (8/15, nächster Plan 31-09), FMT-02 in REQUIREMENTS.md offen.
