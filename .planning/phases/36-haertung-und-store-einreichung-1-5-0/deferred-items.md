# Phase 36: zurückgestellte Befunde

## Aus 36-07 (Korpus)

### F-36-07-1: TIFF-Rahmenlauf wächst überlinear mit der IFD-Zahl

- **Fundstelle:** `backend/src/findling/extract/image.py`, `_read_frames` (und jede Stelle, die `n_frames` liest). Pillow liest für `n_frames` jede IFD der Kette.
- **Gemessen am 21.10.2026 (Windows, Pillow 12.3.0):** im Prozess 5 000 IFDs 0,38 s, 10 000 IFDs 0,66 s, 20 000 IFDs 1,81 s, 40 000 IFDs 5,51 s. Im Sandbox-Kind brauchte `tiff_many_ifds(100_000)` (10 MB) 27,8 s, bei einer Fallgrenze von 30 s. Das Urteil hat einen Namen (`failed/ocr_unavailable` ohne Engine), aber die Datei blockiert das Kind eine halbe Minute. Mit doppelt so vielen IFDs endet sie an der Frist (`timeout`).
- **Korpus:** `tiff-of-100000-ifds` in `test_phase36_hostile_corpus.py` verlangt einen Lauf unter 5 s (`_FRAME_WALK_SECONDS`) und ist mit `xfail(strict=True, reason="built in 36-09")` markiert.
- **Vorschlag für 36-09:** Den Rahmenlauf an der Seitengrenze (`ocr_max_pages`) beenden, statt `n_frames` zu lesen, zum Beispiel per `seek(ocr_max_pages)` als Probe auf "mehr Rahmen" für `indexed(truncated)`. Danach die Markierung entfernen. Das steht noch nicht im Plan 36-09 und muss dort ergänzt werden.
- **Warum nicht in 36-07:** Der Fehler ist schon da und liegt in Produktcode, den 36-09 ohnehin anfasst (image.py). Laut Scope-Grenze wird er hier nicht behoben.

### F-36-07-2: pip-audit rot durch neue Advisories (Pillow, certifi)

- **Lauf:** Security scans 39524695697 auf 1d97d932, Job "pip-audit over the locked set". Der letzte grüne Lauf war 39485332200 auf 37fb122e (20.10.2026, 19:39Z). Die Advisories sind seitdem neu erschienen, Ursache ist nicht 36-07 (dort wurden nur Testdateien geändert).
- **Funde:** `pillow 12.3.0`: CVE-2026-112895, -112400, -112397, -112896, -112897, -112395, -112404, -112899, Fix erst in 13.0.0 (Major-Sprung). `certifi 2026.7.22`: PYSEC-2026-4320, Fix 2026.10.19.
- **Warum nicht hier:** Ein Paket-Update ist kein Auto-Fix (Rule 3 schließt Paketinstallationen aus). Pillow 13 ist ein Major-Sprung im Bildpfad (image.py, TIFF-Varianten aus D-29-06, `MAX_IMAGE_PIXELS`) und braucht eine Prüfung der Änderungen, die Quellpaket-Liste (corresponding_source) und die Wheel-Matrix (arm64).
- **Vorschlag:** Vor der Einreichung 1.5.0 eigener Schritt: certifi auf 2026.10.19, Pillow auf 13.x mit vollem Korpus (36-07) und Bildtests. Owner-Entscheid, ob das in 36-09 (Bildpfad) oder in einem eigenen Plan passiert.
