---
phase: 29-h-rtung-und-store-einreichung-1-4-0
plan: 08
subsystem: backend/extract
tags: [cfb, ole, office, encrypted, legacy-format, issue-18]
requires:
  - "29-01: Reason.LEGACY_FORMAT"
  - "29-06: ExtractionOutcome.detail (Klasse des Leserfehlers)"
provides:
  - "backend/src/findling/extract/cfb.py: ole_verdict(path) -> ExtractionOutcome | None, stdlib-CFB-Verzeichnisleser mit Deckeln"
  - "OLE-Sniff am Anfang von dispatch._run_ooxml_route (Lazy-Import)"
  - "tests/conftest.py: build_cfb/cfb_entry, CFB-Schreiber nach MS-CFB 2.2/2.6"
affects:
  - "29-02: #18-Antwortentwurf (Fixklasse OLE unter OOXML-Endung erledigt)"
  - "PHP-Labels für encrypted/legacy_format (bestehen seit 29-01)"
tech-stack:
  added: []
  patterns:
    - "Urteil vor Arbeit wie office._too_large_to_read: Verdikt oder None, None = bisheriger Weg"
    - "Angreifer-kontrollierte Binärstruktur: jede Sektorposition gegen Dateigröße, Besucht-Menge, Längendeckel, jeder Fehler ergibt None"
key-files:
  created:
    - backend/src/findling/extract/cfb.py
    - backend/tests/test_cfb.py
  modified:
    - backend/src/findling/extract/dispatch.py
    - backend/tests/conftest.py
    - backend/tests/test_extract_documents.py
    - backend/tests/test_measurement_scripts.py
    - backend/tests/test_extract_edge_paths.py
decisions:
  - "CFB-Offsets (A1) gegen [MS-CFB] 2.2 und 2.6 auf learn.microsoft.com geprüft und bestätigt: Sector Shift 0x1E, FAT-Sektoranzahl 0x2C, erster Verzeichnissektor 0x30, DIFAT 0x4C (109 x 4 Byte), Eintrag 128 Byte, Name 64 Byte UTF-16LE, Namenslänge 0x40 (inkl. Null), Objekttyp 0x42"
  - "_MAX_DIRECTORY_SECTORS = 1024 (statt Beispielwert 4096): reale Office-Dateien haben 1 bis einige Dutzend Verzeichnissektoren; 1024 begrenzt einen feindlichen Lauf auf höchstens 4 MiB Verzeichnislesen"
  - "Nur Stream-Einträge (Objekttyp 2) zählen; ein Storage namens Workbook ist kein .xls"
  - "Verschlüsselung hat Vorrang vor Legacy; OLE ohne bekannten Namen ergibt None und läuft wie bisher in failed(corrupt)"
  - "FAT-Sektoren werden einzeln und nur bei Bedarf gelesen (Cache), nie die deklarierte FAT-Anzahl"
metrics:
  duration: "ca. 45 min"
  completed: 2026-10-06
  tasks: 2
  files: 7
---

# Phase 29 Plan 08: OLE-Sniff Summary

Office-Dateien unter .docx/.xlsx/.pptx, die in Wahrheit CFB-Container sind, bekommen jetzt skipped(encrypted) (EncryptionInfo/EncryptedPackage) oder skipped(legacy_format) (Workbook/Book/WordDocument/PowerPoint Document) statt failed(corrupt); der Leser ist reine stdlib und liest nur Kopf, benötigte FAT-Sektoren und die Verzeichniskette.

## Geprüfte Quelle (Annahme A1)

- [MS-CFB] 2.2 Compound File Header: https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-cfb/05060311-bfce-4b12-874d-71fd4ce63aea
- [MS-CFB] 2.6 Directory Entry: https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-cfb/60fe8611-66c3-496b-b70d-a504c94c9ace
- Ergebnis: alle Offsets der Research bestätigt; zusätzlich Objekttyp bei 0x42 genutzt. Sektor n liegt bei (n+1) x Sektorgröße.

## Tasks

| Task | Name | Commits |
|------|------|---------|
| 1 | CFB-Verzeichnisleser cfb.py mit Deckeln | a4dea682 (RED), bbb42a6d (GREEN) |
| 2 | Einhängen in _run_ooxml_route, Pins | 1e6df342 (RED), cfd475de (GREEN) |

## Verifikation

- tests/test_cfb.py: 46 grün (512 und 4096, alle Namen, Vorrang, exakte Namen, Storage zählt nicht, ZIP/leer/kurz/fehlend, Zyklus selbst/zweier mit Laufzeitgrenze, Längendeckel plus Positivkontrolle, absurde Kopffelder, abgeschnitten plus Positivkontrolle, ungültiger Shift, unmögliche Namenslänge, kaputtes UTF-16, DIFAT-Lücke mit 7-MB-Datei, Lesezähler höchstens 3 x 512 Byte bei 8 MB Datei)
- Dispatch: encrypted über alle drei OOXML-Typen, legacy über alle vier Streamnamen, OLE ohne bekannten Namen bleibt corrupt, kaputte ZIP bleibt failed(corrupt) mit Detailklasse, alte .doc/.xls/.ppt-Mimetypes bleiben mime_not_allowed, echte DOCX/XLSX/PPTX unverändert
- Volle Suite: 4623 passed, 25 skipped; einziger Fehlschlag war der Schreib-Ratchet (siehe Abweichung 2), danach grün
- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture sauber
- `grep -c olefile backend/pyproject.toml backend/uv.lock` = 0/0; cfb.py importiert nur struct, typing, findling.extract.errors
- Pins: PACKAGE_FILES_TODAY 71 auf 72, PACKAGE_TREE_HASH_TODAY 266b49eaa4fb184599d5943a7a7ad6c9d198cdf3097338a274da3a9981357a1d; PHP-Paar unverändert (3f72f80d...)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Testannahme] Detailklasse bei kaputter ZIP je Format**
- **Found during:** Task 2 (RED)
- **Issue:** Der Plan nennt "failed(corrupt) mit detail zipfile.BadZipFile" für alle drei Routen; python-docx und python-pptx verpacken BadZipFile aber in eigene PackageNotFoundError-Klassen (bestehendes Verhalten seit 29-06).
- **Fix:** Test prüft je Mimetype die tatsächliche, unveränderte Klasse (docx.opc.exceptions.PackageNotFoundError, zipfile.BadZipFile, pptx.exc.PackageNotFoundError).
- **Files modified:** backend/tests/test_extract_documents.py
- **Commit:** 1e6df342

**2. [Rule 3 - Blocking] Schreibstellen-Ratchet zählt open() in cfb.py**
- **Found during:** Task 2 (volle Suite)
- **Issue:** tests/test_extract_edge_paths.py pinnt jede möglicherweise schreibende Stelle des Dateiwegs; `open(path, "rb")` in cfb.py ist ein neuer Eintrag.
- **Fix:** Eintrag "extract/cfb.py: open" mit Begründung (nur lesend, Scratch-Datei des Dispatchers) aufgenommen, Zähltext sechs auf sieben.
- **Files modified:** backend/tests/test_extract_edge_paths.py
- **Commit:** cfd475de

**3. [Struktur] CFB-Schreiber in conftest.py statt im Testmodul**
- Beide Testmodule (test_cfb.py, test_extract_documents.py) brauchen ihn; das Projekt teilt Helfer bereits über `from conftest import ...`.

## Known Gap (bewusst)

Nur die 109 Header-DIFAT-Einträge werden gefolgt; eine Verzeichniskette mit FAT-Eintrag jenseits davon (ab Sektor 13952 bei 512er-Sektoren) ergibt None und den bisherigen Weg. Im Moduldocstring benannt, per Test abgedeckt.

## Threat Model

- T-29-25: Besucht-Menge, _MAX_DIRECTORY_SECTORS, nur Header-DIFAT, jede Position gegen Dateigröße geprüft (Tests Zyklus, Deckel, absurde Felder, abgeschnitten)
- T-29-26: nur Verzeichnisnamen von Stream-Einträgen, exakter Vergleich (Test MyWorkbookCopy, Books, workbook)
- T-29-27: jeder Fehler ergibt None (OSError, struct.error, UnicodeDecodeError, ValueError, _Malformed)
- T-29-28: stdlib only, grep 0
- Kein Logging im Modul, damit auch kein Inhalt in Logs (T-02-56).

## Self-Check: PASSED

- backend/src/findling/extract/cfb.py, backend/tests/test_cfb.py vorhanden
- Commits a4dea682, bbb42a6d, 1e6df342, cfd475de im Log
