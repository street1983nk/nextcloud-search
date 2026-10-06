---
phase: 29-h-rtung-und-store-einreichung-1-4-0
plan: 07
subsystem: backend/extract
tags: [pillow, tiff, jpeg, ocr, memory, issue-18]
requires:
  - "29-01: Reason.UNSUPPORTED_VARIANT"
  - "29-06: ExtractionOutcome.failed(reason, detail=...)"
provides:
  - "TIFF-Shim (_register_tiff_variants, _SHIM_KEYS) über PIL.TiffImagePlugin.OPEN_INFO"
  - "_normalise_sample_format: komprimierte SampleFormat-0-TIFFs werden über eine gepatchte In-Memory-Kopie gelesen"
  - "_is_unsupported_tiff_variant: skipped(unsupported_variant) statt failed(corrupt)"
  - "_decode_smaller/_draft_target: JPEG-draft auf das seitentreue Zielmaß"
  - "_over_address_space: failed(out_of_memory, detail=findling.extract.image.HeaderEstimate)"
affects:
  - "29-02 Teil 7 und Teil 9 (e): #18-Antwortentwurf, Grenze von D-29-06(b)"
  - "29-15: Upstream-Vorschlag an Pillow"
tech-stack:
  added: []
  patterns:
    - "Laufzeit-Ergänzung eines Pillow-Moduldicts nur per setdefault, mit Wächtertest gegen ein unberührtes OPEN_INFO aus frischem Interpreter"
key-files:
  created:
    - .planning/phases/29-h-rtung-und-store-einreichung-1-4-0/deferred-items.md
  modified:
    - backend/src/findling/extract/image.py
    - backend/tests/test_ocr.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Prüf-Schritt D-29-06(b): Weg (i) scheitert, Weg (ii) liefert korrekte Pixel; komprimierte SF0-TIFFs werden deshalb gelesen (Puffer bis 32 MiB), darüber unsupported_variant"
  - "_SF0_PATCH_MAX_BYTES = 32 MiB: kurzzeitig zwei Kopien (64 MiB), danach eine, die BytesIO ohne weitere Kopie teilt"
  - "Header-Schätzung zählt Pillows Speicherbreite (mehrkanalig 4 Byte je Pixel), nicht Kanäle x 1 Byte"
  - "Image.open auf dem Puffer mit mode=\"r\", damit die Schreib-Ratsche ihn als Lesezugriff erkennt (keine neue Ausnahme in der Liste)"
metrics:
  duration: "ca. 75 min"
  completed: 2026-10-06
  tasks: 2
  files: 3
---

# Phase 29 Plan 07: TIFF-Varianten und große JPEGs (#18) Summary

TIFF-Varianten aus #18 werden über einen setdefault-Shim auf `OPEN_INFO` lesbar (Grau+Extrakanal als `("LA","LA")`, SampleFormat 0 wie 1, komprimiertes SF0 über eine gepatchte In-Memory-Kopie); Float-TIFFs bekommen `skipped(unsupported_variant)`. Große JPEGs werden per `draft` auf das seitentreue Zielmaß dekodiert und in place gedreht, und eine Header-Schätzung gegen RLIMIT_AS liefert `failed(out_of_memory)` statt `corrupt`.

## Prüf-Schritt D-29-06(b): komprimierte SampleFormat-0-TIFFs (wörtlich, für 29-02)

Lokal gefahren gegen Pillow 12.3.0 mit gebündeltem libtiff 4.7.1 (Windows, backend/.venv), Testdateien selbst erzeugt: Grau 8 Bit, Tag 339 per Byte-Patch auf 0, LZW und Deflate, jeweils II und MM. Der Shim war aktiv, ohne ihn scheitert bereits `Image.open`.

| Datei | nur Shim (`load()`) | Weg (i): Tag 339 in `tag_v2`/`tag` auf (1,), dann `load()` | Weg (ii): Tag 339 im `BytesIO`-Puffer auf 1 gepatcht, aus dem Puffer geöffnet |
|---|---|---|---|
| L, LZW, II | `OSError('decoder error -2')` | `OSError('decoder error -2')` | Pixel korrekt |
| L, LZW, MM | `OSError('decoder error -2')` | `OSError('decoder error -2')` | Pixel korrekt |
| L, Deflate, II | `OSError('decoder error -2')` | `OSError('decoder error -2')` | Pixel korrekt |
| L, Deflate, MM | `OSError('decoder error -2')` | `OSError('decoder error -2')` | Pixel korrekt |
| L und RGB, raw, II und MM | Pixel korrekt | Pixel korrekt | Pixel korrekt |

libtiff schreibt dabei auf stderr `_TIFFVSetField: tempfile.tif: Bad value 0 for "SampleFormat" tag.` Weg (i) erreicht libtiff nie, weil libtiff die Tags selbst aus den Bytes liest. Weg (ii) ist deshalb als `_normalise_sample_format` gebaut; der Test `test_sf0_compressed_probe` hält beide Ergebnisse fest (Weg (i) muss weiter mit `decoder error -2` scheitern, Weg (ii) korrekte Pixel liefern).

**Satz für 29-02 Teil 7 und Teil 9 (e):** "TIFFs mit SampleFormat 0 werden ab 1.4.0 gelesen, unkomprimiert direkt und komprimiert (LZW, Deflate) über eine korrigierte Kopie im Arbeitsspeicher; diese Kopie wird nur bis 32 MiB Dateigröße angelegt, ein größeres komprimiertes SampleFormat-0-TIFF bekommt das Urteil `unsupported_variant` statt `corrupt`. Gleitkomma-TIFFs (SampleFormat 3, auch Float16) werden nicht dekodiert und bekommen ebenfalls `unsupported_variant`."

Hinweis aus der Research bleibt gültig: die im Feld beobachtete #18-Variante war SampleFormat 3, nicht 0; SF0 ist eine abgeleitete Klasse.

## Was gebaut wurde

**Task 1 (acb093e5 RED, e2092842 GREEN): TIFF-Shim und ehrliches Variantenurteil**
- `_register_tiff_variants()` als Modul-Seiteneffekt neben `Image.MAX_IMAGE_PIXELS`: `(II|MM, 1, (1,), 1, (8, 8), (0|1,))` auf `("LA","LA")`; zu jedem Schlüssel mit SampleFormat `(1,)` (inklusive der neuen LA-Schlüssel) die `(0,)`-Variante; nur `setdefault`; Rückgabe = wirklich hinzugefügte Schlüssel als `_SHIM_KEYS`.
- `_is_unsupported_tiff_variant(path)`: TIFF-Magic, dann `TiffImagePlugin.TiffImageFile(path)`; `SyntaxError("unknown pixel mode")` ergibt `skipped(UNSUPPORTED_VARIANT)`, alles andere `failed(CORRUPT, detail=<Klasse>)`.
- `_has_compressed_sample_format_zero` + `_read_normalised` + `_normalise_sample_format`: Größengrenze `_SF0_PATCH_MAX_BYTES`, `readinto` in einen bytearray, Patch nur exakter Nullen in allen IFDs, Offsets gegen die Puffergröße geprüft, IFD-Schleifenschutz, Eintragsbudget `len // 12`; jeder Strukturfehler ergibt `unsupported_variant`.
- Beide CORRUPT-Stellen tragen jetzt `detail` (Klassenname, nie die Meldung, T-29-24).
- Tests: Grau+Extra 0/1 x raw/LZW/Deflate x II/MM (12), SF0 raw L/RGB x II/MM, Prüf-Schritt (4), SF0 komprimiert (4), Puffergrenze, Patch-Offset außerhalb des Puffers, Float16-Grau und 8-Bit-Float-RGB, kaputte IFD, reiner Müll, Wächter gegen ein unberührtes `OPEN_INFO` aus einem frischen Interpreter ("Pillow ships this key now, check and retire the shim"), keine Pillow-Zeile verändert, LA-Ziel.

**Task 2 (6736ee23 RED, fedb0058 GREEN): JPEG-draft, exif_transpose in place, Header-Schätzung, Pins**
- `_draft_target(w, h)` seitentreu (8192x5464 ergibt (3500, 2334)); `_decode_smaller` nur bei einem Frame und langer Kante über 3500; `picture.draft("L", ziel)` (RGB wird grau, CMYK bleibt CMYK, beide auf 4096x2732).
- `_encode_frame`: `ImageOps.exif_transpose(picture, in_place=True)`, dann `thumbnail`, dann `convert("L")`; keine Arbeitskopie mehr.
- `_over_address_space`: nach dem draft `w * h * _pixel_bytes(mode) * _WORKING_COPIES (2)` gegen `RLIMIT_AS` weich minus `VmSize` aus `/proc/self/status`; ohne Deckel, ohne Statusdatei oder unter Windows keine Schätzung. Überschreitung: `failed(OUT_OF_MEMORY, detail="findling.extract.image.HeaderEstimate")`.
- Tests: seitentreues Ziel, Größe nach draft vor dem Laden (RGB, CMYK), Endbild 2334x3500 aufrecht (RGB, CMYK), kleines JPEG ohne draft, Mehrseiten-TIFF je Frame byte-gleich mit dem alten Kopierweg, Kunstdeckel ergibt out_of_memory ohne Engine-Aufruf, Schätzung zählt das gedraftete Maß, kein Deckel = normaler Weg, VmSize-Leser, fehlende Statusdatei, Windows ohne Deckel.
- `PACKAGE_TREE_HASH_TODAY` = `42f2fd36817063952c3611e3ffead8dbaa530b4c36489f1a3e2e76b6d3014e7a` (Kommentar "plan 29-07 changed image.py"), `PACKAGE_FILES_TODAY` bleibt 71, PHP-Pin unverändert (`3f72f80d...`).

## Verifikation

- `pytest tests/test_ocr.py`: 92 passed, 8 skipped (Engine-Tests ohne tesseract).
- Volle Suite einmal komplett: 4562 passed, 25 skipped, 1 failed (Schreib-Ratsche, siehe Abweichung 2, danach behoben); nach dem Fix die betroffenen Dateien erneut: extract*, ocr*, sandbox, allowlist, measurement_scripts 795 passed, 14 skipped.
- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture --min-confidence 80 sauber.
- Akzeptanz-Greps: `info.setdefault` Treffer; `L;16B` außerhalb von Kommentaren 0; `in_place=True` und `.draft(` je ein Treffer im Code; `MAX_IMAGE_PIXELS = None` kein Treffer; `_normalise_sample_format` und `UNSUPPORTED_VARIANT` vorhanden, passend zum positiven Prüf-Schritt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Header-Schätzung mit Pillows echter Pixelbreite**
- **Found during:** Task 2
- **Issue:** Die Formel "Breite x Höhe x Kanäle x Bytes je Kanal" unterschätzt mehrkanalige Bilder: Pillow hält RGB, LA, CMYK intern mit 4 Byte je Pixel.
- **Fix:** `_pixel_bytes(mode)`: mehrkanalig 4, `I`/`F` 4, `I;16*` 2, sonst 1; Faktor 2 wie geplant.
- **Commit:** fedb0058

**2. [Rule 3 - Blocking] Schreib-Ratsche in test_extract_edge_paths**
- **Found during:** Task 2, volle Suite
- **Issue:** `Image.open(stream)` auf dem SF0-Puffer zählte als neuer möglicher Schreibzugriff (Modus nicht ablesbar).
- **Fix:** `Image.open(stream, mode="r")`, Modus ablesbar, die gepinnte Liste bleibt unverändert; Baumhash danach erneut gepinnt.
- **Commit:** fedb0058

**3. [Rule 1 - Test] Mehrseiten-Orientierungstest gegen den alten Kopierweg statt gegen eine erwartete Drehung**
- **Found during:** Task 2 RED
- **Issue:** Pillow 12.3.0 wendet die Orientierung eines TIFF schon beim Laden selbst an; `exif_transpose` sieht danach keine Orientierung mehr, das Ergebnis ist nicht die erwartete 90-Grad-Drehung (vorbestehend, vor und nach 29-07 gleich).
- **Fix:** Der Test vergleicht jeden Frame byte-genau mit dem Ergebnis des alten Kopierwegs, zwei Frames mit unterschiedlicher Größe und Muster; die Pillow-Beobachtung steht in `deferred-items.md`.
- **Commit:** 6736ee23

## Deferred Issues

- Pillow-TIFF-Orientierung (Tag 274 = 6) ergibt beim Laden keine korrekte Drehung; siehe `deferred-items.md`, Kandidat für das Upstream-Issue in 29-15.

## Threat Flags

Keine neue Oberfläche außerhalb des Bedrohungsmodells: die In-Memory-Kopie (T-29-23b) ist durch `_SF0_PATCH_MAX_BYTES`, geprüfte Offsets, IFD-Schleifenschutz und Eintragsbudget begrenzt; `detail` trägt nur Klassennamen bzw. die feste Kennung `HeaderEstimate` (T-29-24); `MAX_IMAGE_PIXELS` bleibt bei 50 MP (T-29-21); SF3 wird nie normalisiert (T-29-23); der Shim ändert nur fehlende Schlüssel (T-29-22).

## Self-Check: PASSED

- backend/src/findling/extract/image.py, backend/tests/test_ocr.py, backend/tests/test_measurement_scripts.py, deferred-items.md vorhanden
- Commits acb093e5, e2092842, 6736ee23, fedb0058 im Log
