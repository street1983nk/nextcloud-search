---
phase: 36-haertung-und-store-einreichung-1-5-0
plan: 17
subsystem: Bildpfad (extract/image.py), Abhängigkeiten, Lizenzangaben
tags: [hart-06, f-36-07-2, pillow-13, certifi, pip-audit, tiff-shim, python-pillow-10139]
requires: [36-07]
provides:
  - "pillow==13.0.0 gepinnt, uv.lock: pillow 13.0.0 und certifi 2026.10.19, sonst keine Fassung bewegt"
  - "image._grey_of: Grau mit assoziiertem Alpha (Modus La unter Pillow 13) gibt das erste Band weiter, wie unter 12.3.0"
  - "TIFF-Shim zurückgebaut auf die SampleFormat-0-Spiegel, Wiedervorlage python-pillow#10139 entschieden (Fall A)"
  - "Seed-Tests der Upgrade-Strecke gegen die festgeschriebene OPEN_INFO-Tabelle von Pillow 12.3.0 (der Pillow von 1.3.2)"
affects: [36-08, 36-09]
tech-stack:
  added: []
  patterns:
    - "Upstream-Beleg im frischen Interpreter ohne findling (Unterprozess, ast.literal_eval der Ausgabe)"
    - "Aussage über eine Altfassung an einer festgeschriebenen, einmalig mit uv run --no-project --with gewonnenen Tabelle"
key-files:
  created:
    - .planning/phases/36-haertung-und-store-einreichung-1-5-0/36-17-SUMMARY.md
  modified:
    - backend/pyproject.toml
    - backend/uv.lock
    - backend/src/findling/extract/image.py
    - backend/tests/test_ocr.py
    - backend/tests/test_upgrade_seed_fixture.py
    - backend/tests/test_measurement_scripts.py
    - scripts/ci/make_upgrade_seed_tiff.py
    - THIRD-PARTY.md
    - .planning/phases/36-haertung-und-store-einreichung-1-5-0/deferred-items.md
decisions:
  - "Fall A der Wiedervorlage: Pillow 13.0.0 enthält PR #10140 (compare Merge-Commit 52d303ae...13.0.0 = ahead 83 / behind 0, Unterprozess-Probe öffnet ExtraSamples 0 und 1 ohne Shim); die Grau-Schlüssel sind aus dem Shim entfernt"
  - "Grau mit assoziiertem Alpha: erstes Band (gespeicherter Grauwert, Bild auf Schwarz) statt Entmultiplizieren, damit der Bildpfad unter 13 wie unter 12.3.0 liest"
  - "Task-Zuschnitt verschoben: Seed-Tests, THIRD-PARTY.md und der Upstream-Test sind schon im Commit von Task 1, weil die Gates vor jedem Commit die volle Suite grün verlangen; Task 2 trägt den Rückbau des Shims"
  - "corresponding_source.py und test_third_party_versions.py unverändert: pillow.libs bringt keine neue Bibliothek, nur Fassungswechsel permissiver Bibliotheken"
metrics:
  duration: "ca. 70 min (03:50 bis 05:01 Ortszeit), davon 2 x 13 min volle lokale Suite und ca. 30 min CI"
  completed: 2026-10-21
  tasks: 2
  files: 9
requirements: [HART-06]
---

# Phase 36 Plan 17: Pillow 13.0.0 und certifi 2026.10.19 Summary

Pillow geht von 12.3.0 auf 13.0.0 und certifi von 2026.7.22 auf 2026.10.19. Damit ist pip-audit über die gesperrte Menge grün. Security scans 39533470359 auf ff4b275d ist grün, der Job "pip-audit over the locked set" eingeschlossen. Unter Pillow 13 öffnet Grau mit assoziiertem Alpha im Modus `La`, und den kann Pillow nicht nach `L` wandeln. Das hätte jedes solche TIFF still gebrochen; `image._grey_of` behebt es. Die Wiedervorlage python-pillow#10139 ist entschieden: Upstream-Fix ist drin, die Grau-Schlüssel sind aus dem Shim zurückgebaut.

## Commits

| Task | Name | Commit |
|------|------|--------|
| 1 | Pins heben, Bildpfad gegen 13.0.0 prüfen, La-Fix, Duplikat-Test, Seed-Tests, THIRD-PARTY | ac5cb16b |
| 2 | Rückbau der Grau-Schlüssel im TIFF-Shim, Ratsche, deferred-items | ff4b275d |

Der Plan-Commit 4ddc6ec2 ist mit demselben Push (083a793d..ff4b275d) auf origin/main gegangen.

## Lock und Legitimität

- `git diff --stat backend/uv.lock`: 20 Einfügungen, 20 Löschungen. Geänderte Blöcke: nur `name = "certifi"` (2026.7.22 auf 2026.10.19), `name = "pillow"` (12.3.0 auf 13.0.0) und die Specifier-Zeile `{ name = "pillow", specifier = "==13.0.0" }` in `requires-dist` von findling. pillow-heif bleibt 1.8.1. `uv lock --check` grün.
- PyPI-JSON pillow 13.0.0: Projekt `pillow`, Quelle github.com/python-pillow/Pillow, `requires_python >=3.11`, Upload 2026-10-16 22:16Z (Wheels) / 22:18Z (sdist). Wheels `cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64` (sha256 5f56499c1a74d2b8...) und `cp313-cp313-manylinux_2_27_aarch64.manylinux_2_28_aarch64` (19b66ca0a4d25cc0...), dieselben Tags wie bei 12.3.0. Die Hashes in uv.lock stimmen mit PyPI überein, auch win_amd64 (9dda0788...) und sdist (cdcd1ba2...).
- PyPI-JSON certifi 2026.10.19: Projekt `certifi`, Quelle github.com/certifi/python-certifi, Upload 2026-10-20 02:24Z, `py3-none-any` (42d35340cc5b9ba7...), sdist 035c1e85572b141b..., gleich im Lock.
- pip-audit lokal (Export wie security.yml, `--no-dev`, 59 Pakete): "No known vulnerabilities found".

## Prüfung des Major-Sprungs (Task 1)

Ausgangszustand unter 12.3.0: Bildsuite 299 passed, 12 skipped (kein Tesseract lokal), 30 xfailed; Korpus 34 passed, 30 xfailed.

**(a) Doppelte TIFF-Tags, erster Wert gilt jetzt** (Release-Notes 13.0.0, "Duplicate TIFF tags"). Fundstellen: `_has_compressed_sample_format_zero` liest `tag_v2[SampleFormat]`, `_normalise_sample_format` patcht jedes Vorkommen. Neuer Test `test_a_tiff_with_a_duplicate_sample_format_tag_is_read` (raw, LZW, Deflate; Reihenfolgen 0/1 und 1/0). Gemessen unter 12.3.0: 0 dann 1 raw indexed, **0 dann 1 komprimiert failed(corrupt) builtins.OSError** (Pillow sah 1 und machte keine gepatchte Kopie, libtiff nimmt den ersten Wert 0 und lehnt ab), 1 dann 0 in allen drei indexed. Unter 13.0.0: alle sechs indexed mit Grauwert 200, `tag_v2` zeigt den ersten Wert. Urteil: betrifft, Verbesserung, im Test festgeschrieben.

**(b) `reducing_gap` jetzt auch für RGBA und LA in `thumbnail`** (Release-Notes, "Resizing images with alpha"). Fundstelle `_encode_frame`. Der Shim liefert unter 13 kein LA mehr (siehe Task 2), Pillow liefert `L` (ExtraSamples 0) oder `La` (ExtraSamples 1). Beim Prüfen fiel der eigentliche Bruch auf: `test_a_grey_tiff_with_an_extra_channel_is_read[1-*]` (6 Fälle) wurde rot mit `ValueError: conversion from La to L not supported`. Ursache: Pillow 13 mappt ExtraSamples 1 selbst auf ("La", "La"), `setdefault` des Shims greift nicht mehr, und `convert("L")` kann `La` nicht. Fix im Produktpfad: `_grey_of` nimmt bei `La` `getchannel(0)`, also den gespeicherten Grauwert. Das ist genau, was 12.3.0 mit dem Shim (LA, Alpha verworfen) weitergab. Neuer Test `test_grey_with_associated_alpha_hands_the_stored_grey_scaled` (4000 x 3000, Alpha 128, über der Kantengrenze, also mit `thumbnail` auf `La`): Grau 200 und 3500 x 2625. Entmultiplizieren hätte 255 ergeben. Gegenprobe ohne Fix: 7 rot. Upgrade-Seed-Bild (`L`, 0/255) unverändert. Urteil: betrifft, behoben.

**(c) API-Prüfung gegen 13.0.0** per `uv run python -c`: `Image.DecompressionBombError` (Unterklasse von Exception) vorhanden, `Image.MAX_IMAGE_PIXELS` setzbar (Vorgabe 89478485), `Image.Image.draft` vorhanden, `ImageOps.exif_transpose(image, *, in_place=False)` gleiche Signatur, `TiffImagePlugin.II`/`MM` = b"II"/b"MM", `OPEN_INFO` vorhanden, `tag_v2` als Instanzattribut (im Duplikat-Test genutzt), `PngImagePlugin.MAX_TEXT_CHUNK` = 1048576, `thumbnail(size, resample=BICUBIC, reducing_gap=2.0)`. Meldung bei unbekannter Variante ohne Shim (SampleFormat 3, Float-Grau) wörtlich `'unknown pixel mode'`, `_is_unsupported_tiff_variant` greift weiter (Float-Tests grün). Gebündelt: libtiff 4.7.2, libjpeg-turbo 8.0, libwebp 1.6.0, zlib-ng 1.3.1. Urteil: betrifft nicht, belegt.

**(d) Security-Zeilen der 13.0.0-Notes für Formate unseres Bildpfads:**
- Critical "Stale native image storage reused after mode transitions" (CVE-2026-96639): betrifft jeden `convert`; mit 13.0.0 behoben.
- Critical "JPEG decoder buffer overflow from scanlines wider than tile extents": JPEG-Eingang, behoben.
- High "Unbounded Exif header replacement loop" (CVE-2026-96643): `exif_transpose` liest Exif, behoben.
- High "TIFF tile and YCbCr decoding out-of-bounds read from undersized libtiff buffers": TIFF-Eingang über libtiff, behoben.
- High "TIFF decoding returned uninitialized memory for short JPEG strips": TIFF-Eingang, behoben.
- High-Zeilen zum TIFF-Encoder (Colormap, Heap-Overflow, Tag-Mismatch) und Medium "TIFF encoder use-after-free": wir schreiben kein TIFF im Produkt, nur PNG; betrifft Tests und Generatoren, nicht den Bildpfad.
- Medium "TIFF and Exif IFD parsing memory and CPU amplification from shared tag data": TIFF- und Exif-Eingang, behoben in Pillow; unser eigener IFD-Lauf `_normalise_sample_format` ist davon unabhängig gedeckelt (F-29-01).
- Medium "APNG decompression bomb bypass via delayed disposal-frame sizing": PNG-Eingang, behoben.
- Medium "GIF comment handling quadratic-time blowup", Low "GIF decompression bomb check used a size discarded on failure": GIF-Eingang, behoben.
- WebP: keine Zeile.

Bildsuite unter 13.0.0 nach Task 1: alle Bilddateien grün (test_ocr, test_image_heic, test_ocr_french, test_ocr_languages, test_upgrade_seed_fixture, test_phase31_audit). Korpus `test_phase36_hostile_corpus.py`: **34 passed, 30 xfailed**, gleich wie in 36-07, kein XPASS, nichts entmarkiert.

## Wiedervorlage TIFF-Shim (Task 2): Fall A

- Weg 1, am Tag: `gh api repos/python-pillow/Pillow/pulls/10140`: "Support greyscale TIFFs with ExtraSamples 0 or 1", gemergt 2026-10-07T08:06:49Z, Merge-Commit 52d303ae51f8fecdd54b6fd44256e37c93665493. `compare/52d303ae...13.0.0`: status `ahead`, ahead_by 83, behind_by 0, also im Tag enthalten. Issue #10139 ist geschlossen. Die Release-Notes nennen den PR nicht.
- Weg 2, am installierten Paket: frischer Interpreter ohne findling. `OPEN_INFO[(II|MM, 1, (1,), 1, (8, 8), (0,))] = ("L", "LX")` und `(..., (1,)) = ("La", "La")`. ExtraSamples 0 öffnet als `L`, Grau 200, in raw, LZW und Deflate. Unter 12.3.0 waren beide Schlüssel None und jedes Öffnen `UnidentifiedImageError`.
- Beide Wege stimmen überein. Rückbau: `_register_tiff_variants` setzt die Grau-Schlüssel nicht mehr und spiegelt nur noch SampleFormat 1 als 0, jeweils mit dem Wert, den Pillow dem Original gibt. Vorher schrieb der Shim für die Spiegel der Grau-Schlüssel ("LA", "LA"), was nicht mehr zu Pillow passte. Docstring auf den neuen Stand.
- Tests: `test_pillow_itself_reads_grey_with_an_extra_channel` (Unterprozess, Modi festgeschrieben), `test_the_shim_adds_only_sample_format_zero_mirrors_with_pillows_values` (rot gegen den alten Shim, grün nach dem Rückbau), `test_grey_with_an_extra_channel_and_sample_format_zero_is_read` (beide Klassen von #18 in einer Datei, alle Kompressionen). Die Wächter `test_the_shim_adds_only_keys_pillow_does_not_ship` und `test_the_shim_changes_no_entry_pillow_ships` sind grün. `_SHIM_KEYS` ist nicht leer und enthält nur SampleFormat-0-Schlüssel.
- Seed-Bild der Upgrade-Strecke: `test_the_pillow_of_1_3_2_has_no_entry_for_it` prüft gegen die festgeschriebene Tabelle `PILLOW_12_3_0_GREY_TWO_CHANNEL_KEYS`, gewonnen mit `uv run --no-project --with pillow==12.3.0`. 1.3.2 pinnt laut Tag v1.3.2 pillow 12.3.0. Die Tabelle enthält nur ExtraSamples 2 für II und MM. Der Schlüssel des Seed-Bilds `(MM, 1, (1,), 1, (8, 8), (0,))` fehlt dort, und Öffnen über diese Tabelle endet in `UnidentifiedImageError`. `test_this_code_reads_it_and_it_turns_grey`: Modus `L`, Extrema (0, 255). Der Generator schreibt weiter dieselben Bytes.

## pillow.libs 12.3.0 gegen 13.0.0

Je 18 Dateien, auf amd64 und arm64 dieselbe Menge. Keine Bibliothek kommt dazu, keine fällt weg:

| Bibliothek | 12.3.0 | 13.0.0 |
|---|---|---|
| libharfbuzz | .so.0.61421.0 | .so.0.61450.0 |
| liblzma | .so.5.8.3 | .so.5.8.4 |
| libtiff | .so.6.2.0 | .so.6.3.0 |
| libXau, libavif 16.4.2, libbrotlicommon/-dec 1.2.0, libfreetype 6.20.6, libjpeg 62.4.0, liblcms2 2.0.19, libopenjp2 2.5.4, libpng16 16.58.0, libsharpyuv 0.1.2, libwebp 7.2.0, libwebpdemux 2.0.17, libwebpmux 3.1.2, libxcb 1.1.0, libzstd 1.5.7 | gleich | gleich (teils neuer Build-Hash) |

Alle Fassungswechsel betreffen permissive Lizenzen (HarfBuzz Old-MIT, xz/liblzma 0BSD, libtiff-Lizenz). Es gibt keine neue Quellpflicht und keine Owner-Frage. `corresponding_source.py` bleibt unverändert. THIRD-PARTY.md nennt die pillow.libs nicht einzeln und bekommt nur die Fassung 13.0.0. `test_third_party_versions.py` nennt keine Pillow-Fassung und bleibt unverändert. `test_corresponding_source.py` ist grün. docs/ocr.md, docs/performance.md und docs/store-listing.md bleiben unberührt (historische Messumgebung).

## CI auf ff4b275d

| Workflow | Lauf | Ergebnis |
|---|---|---|
| Security scans (CodeQL, pip-audit over the locked set, REUSE) | 39533470359 | success |
| Python gates | 39533470423 | success |
| Multi-arch image | 39533470400 | success |
| Integration | 39533470365 | success |
| Resilience | 39533470374 | success |
| HaRP deploy | 39533470378 | success |
| OpenSSF Scorecard | 39533470419 | success |

Lokal vor jedem Commit: ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture, reuse lint grün. Volle Suite nach Task 1: 6007 passed, 264 skipped, 30 xfailed. Nach Task 2: 6014 passed, 264 skipped, 30 xfailed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Grau mit assoziiertem Alpha wäre unter Pillow 13 gebrochen**
- **Found during:** Task 1, Punkt (b)
- **Issue:** Pillow 13.0.0 öffnet ExtraSamples 1 als `La`, `convert("L")` wirft `ValueError`. Das wäre ein Absturz in `_encode_frame` gewesen, also failed statt indexed.
- **Fix:** `_grey_of` (erstes Band bei `La`), Test mit Halb-Alpha und Skalierung.
- **Files modified:** backend/src/findling/extract/image.py, backend/tests/test_ocr.py
- **Commit:** ac5cb16b

**2. [Rule 3 - Blocking] Task-Zuschnitt für grüne Commits**
- **Issue:** Die Gates aus 36-01 verlangen vor jedem Commit die volle Suite grün. Nach dem Pin-Wechsel waren `test_the_shim_maps_grey_with_an_extra_channel_to_la`, beide Seed-Tests und `test_third_party_versions.py` rot. Der Plan hatte sie Task 2 zugeordnet.
- **Fix:** Upstream-Test (ersetzt den Mapping-Test), Seed-Test-Umbau, THIRD-PARTY.md und die erste Ratschen-Bewegung sind schon im Commit von Task 1. Task 2 trägt den Rückbau im Shim mit seinen Tests und der zweiten Ratschen-Bewegung.
- **Commit:** ac5cb16b, ff4b275d

**3. Shim-Spiegel mit veralteten Werten**
- Unter 13.0.0 hätte der alte Shim die SampleFormat-0-Spiegel der Grau-Schlüssel mit ("LA", "LA") belegt statt mit Pillows Werten. Mit dem Rückbau in Task 2 ist das behoben; ein Test hält es fest.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche. Der Unterprozess im Test startet nur `sys.executable` mit festem Programmtext.

## Self-Check: PASSED

- FOUND: backend/pyproject.toml (pillow==13.0.0), backend/uv.lock (certifi-2026.10.19, pillow 13.0.0), THIRD-PARTY.md (`| \`pillow\` | 13.0.0 |`)
- FOUND: Commits ac5cb16b, ff4b275d auf origin/main
- FOUND: Security scans 39533470359 success auf ff4b275d
