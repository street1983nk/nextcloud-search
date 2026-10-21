# Phase 36: zurückgestellte Befunde

## Aus 36-07 (Korpus)

### F-36-07-1: TIFF-Rahmenlauf wächst überlinear mit der IFD-Zahl

- **Fundstelle:** `backend/src/findling/extract/image.py`, `_read_frames` (und jede Stelle, die `n_frames` liest). Pillow liest für `n_frames` jede IFD der Kette.
- **Gemessen am 21.10.2026 (Windows, Pillow 12.3.0):** im Prozess 5 000 IFDs 0,38 s, 10 000 IFDs 0,66 s, 20 000 IFDs 1,81 s, 40 000 IFDs 5,51 s. Im Sandbox-Kind brauchte `tiff_many_ifds(100_000)` (10 MB) 27,8 s, bei einer Fallgrenze von 30 s. Das Urteil hat einen Namen (`failed/ocr_unavailable` ohne Engine), aber die Datei blockiert das Kind eine halbe Minute. Mit doppelt so vielen IFDs endet sie an der Frist (`timeout`).
- **Korpus:** `tiff-of-100000-ifds` in `test_phase36_hostile_corpus.py` verlangt einen Lauf unter 5 s (`_FRAME_WALK_SECONDS`) und ist mit `xfail(strict=True, reason="built in 36-09")` markiert.
- **Vorschlag für 36-09:** Den Rahmenlauf an der Seitengrenze (`ocr_max_pages`) beenden, statt `n_frames` zu lesen, zum Beispiel per `seek(ocr_max_pages)` als Probe auf "mehr Rahmen" für `indexed(truncated)`. Danach die Markierung entfernen. Das steht noch nicht im Plan 36-09 und muss dort ergänzt werden.
- **Warum nicht in 36-07:** Der Fehler ist schon da und liegt in Produktcode, den 36-09 ohnehin anfasst (image.py). Laut Scope-Grenze wird er hier nicht behoben.
