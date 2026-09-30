---
created: 2026-09-28T08:21:52.300Z
title: Issue #18 Fix-Kandidaten einplanen (JPG-Verdikt, HEIF, Download-Groessenpruefung)
area: general
files:
  - backend/src/findling/errors.py:212
---

## Problem

Issue #18 (budachst): ueber 5000 JPGs werden faelschlich als "kaputt" (corrupt) verworfen. Analyse 28.09.2026 abgeschlossen: tesseract ist unschuldig, das Verdikt kommt aus Pillow bzw. `from_exception` in errors.py:212, das unbekannte Exceptions pauschal als corrupt einstuft. Vier Hypothesen:

1. Angeschnittene/truncated JPEGs, die der Nextcloud-Preview-Weg toleriert, unser Pfad aber nicht
2. HEIC-Dateien hinter .jpg-Endung: pi-heif ist NIRGENDS als Pillow-Opener registriert, HEIC schlaegt daher immer fehl
3. Exotische JPEG/EXIF-Variante wirft eine Nicht-OSError-Exception
4. Download prueft heruntergeladene Bytes NICHT gegen die Sollgroesse (echter Bug-Kandidat)

Rueckfrage an budachst GEPOSTET (issuecomment-5865917799, Owner-GO lag vor): file/xxd-ffd9-Check + `occ findling:diagnose` + Team-Folder-Frage. Stand 28.09.: WARTEN auf Antwort.

## Solution

Sobald budachst antwortet, Fix-Kandidaten je nach bestaetigter Hypothese formal in v1.4 einplanen:

- truncated/angeschnittene Dateien als EIGENES Verdikt statt Pauschal-corrupt (errors.py from_exception)
- HEIF-Handling: pi-heif als Pillow-Opener registrieren (HEIC hinter .jpg)
- Download-Groessenpruefung: Bytes gegen Sollgroesse pruefen

Phasen-Slot-Kandidat: Phase 29 (Haertung+Release) oder eigener Einschub nach Antwort. Entscheid ueber den Slot liegt beim Owner.

## Update 2026-09-30

budachst 28.09.: die Dateien sind TIFF hinter .jpg (Team-Ordner __groupfolders/8, Agenturmaterial). Image.open erkennt am Inhalt, also scheitert das DEKODIEREN der TIFF-Variante (CMYK/16 Bit/Ebenen/Kompression) -> OSError -> Pauschal-corrupt (extract/image.py:112/137). Antwort gepostet (issuecomment-5915833064): Bitte um `file`-Zeile, optional Beispieldatei. Fix-Kandidat: eigenes Verdikt "unsupported image variant" + TIFF-Varianten lesen. Hypothesen 1/2 (truncated, HEIC) fuer diesen Fall vom Tisch.
