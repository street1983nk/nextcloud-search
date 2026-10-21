# Phase 36: zurückgestellte Befunde

## Aus 36-07 (Korpus)

### F-36-07-1: TIFF-Rahmenlauf wächst überlinear mit der IFD-Zahl

- **Fundstelle:** `backend/src/findling/extract/image.py`, `_read_frames` (und jede Stelle, die `n_frames` liest). Pillow liest für `n_frames` jede IFD der Kette.
- **Gemessen am 21.10.2026 (Windows, Pillow 12.3.0):** im Prozess 5 000 IFDs 0,38 s, 10 000 IFDs 0,66 s, 20 000 IFDs 1,81 s, 40 000 IFDs 5,51 s. Im Sandbox-Kind brauchte `tiff_many_ifds(100_000)` (10 MB) 27,8 s, bei einer Fallgrenze von 30 s. Das Urteil hat einen Namen (`failed/ocr_unavailable` ohne Engine), aber die Datei blockiert das Kind eine halbe Minute. Mit doppelt so vielen IFDs endet sie an der Frist (`timeout`).
- **Korpus:** `tiff-of-100000-ifds` in `test_phase36_hostile_corpus.py` verlangt einen Lauf unter 5 s (`_FRAME_WALK_SECONDS`) und ist mit `xfail(strict=True, reason="built in 36-09")` markiert.
- **Vorschlag für 36-09:** Den Rahmenlauf an der Seitengrenze (`ocr_max_pages`) beenden, statt `n_frames` zu lesen, zum Beispiel per `seek(ocr_max_pages)` als Probe auf "mehr Rahmen" für `indexed(truncated)`. Danach die Markierung entfernen. Das steht noch nicht im Plan 36-09 und muss dort ergänzt werden.
- **Warum nicht in 36-07:** Der Fehler ist schon da und liegt in Produktcode, den 36-09 ohnehin anfasst (image.py). Laut Scope-Grenze wird er hier nicht behoben.
- **ERLEDIGT 21.10.2026 durch Plan 36-09 (Task 2):** `image._has_frame` fragt Rahmen per `seek` ab, `_decode_smaller` und `_read_frames` lesen `n_frames` nicht mehr; der Lauf endet nach `ocr_max_pages` Rahmen plus einer Probe. `tiff-of-100000-ifds` lokal im Kind 0,20 s statt 27,8 s, `tiff_many_ifds(40_000)` im Prozess unter 1 s. Kein neuer Detailcode, das Urteil bleibt aus READABLE (D-08). Die xfail-Markierung ist entfernt.

### F-36-07-2: pip-audit rot durch neue Advisories (Pillow, certifi)

- **Lauf:** Security scans 39524695697 auf 1d97d932, Job "pip-audit over the locked set". Der letzte grüne Lauf war 39485332200 auf 37fb122e (20.10.2026, 19:39Z). Die Advisories sind seitdem neu erschienen, Ursache ist nicht 36-07 (dort wurden nur Testdateien geändert).
- **Funde:** `pillow 12.3.0`: CVE-2026-112895, -112400, -112397, -112896, -112897, -112395, -112404, -112899, Fix erst in 13.0.0 (Major-Sprung). `certifi 2026.7.22`: PYSEC-2026-4320, Fix 2026.10.19.
- **Warum nicht hier:** Ein Paket-Update ist kein Auto-Fix (Rule 3 schließt Paketinstallationen aus). Pillow 13 ist ein Major-Sprung im Bildpfad (image.py, TIFF-Varianten aus D-29-06, `MAX_IMAGE_PIXELS`) und braucht eine Prüfung der Änderungen, die Quellpaket-Liste (corresponding_source) und die Wheel-Matrix (arm64).
- **Vorschlag:** Vor der Einreichung 1.5.0 eigener Schritt: certifi auf 2026.10.19, Pillow auf 13.x mit vollem Korpus (36-07) und Bildtests. Owner-Entscheid, ob das in 36-09 (Bildpfad) oder in einem eigenen Plan passiert.
- **ERLEDIGT 21.10.2026 durch Plan 36-17** (Commits ac5cb16b und der Rückbau-Commit von Task 2, siehe 36-17-SUMMARY.md): pillow 13.0.0, certifi 2026.10.19, pip-audit lokal "No known vulnerabilities found". Korpus unverändert 34 grün / 30 xfailed, kein Fall kippt, nichts zu entmarkieren.
- **Für 36-08 und 36-09:** Grau mit assoziiertem Alpha öffnet unter Pillow 13 als `La` (nicht mehr `LA` über den Shim); `image._grey_of` gibt dessen erstes Band weiter. Der TIFF-Shim enthält nur noch die SampleFormat-0-Spiegel. F-36-07-1 bleibt unter Pillow 13 bestehen (`tiff-of-100000-ifds` weiter strict xfailed).

## Aus 36-15 (Owner-Abnahme, Ziel 1.5.1)

### L-36-05: "Bewusst ausgelassen: 0" mit Erklärsatz

- **Fundstelle:** `php/templates/admin.php:459-460`, `php/js/admin.js:402`, l10n (acht Sprachen).
- **Beobachtung 21.10.2026 auf 8096:** Bei 0 ausgelassenen Dateien steht "Bewusst ausgelassen: 0" plus "Diese Dateien sind zu groß ...".
- **Ziel 1.5.1:** bei 0 eigener Satz bzw. Erklärung ausblenden. Vom Owner akzeptiert, kein Blocker für 1.5.0. Siehe 36-AUDIT.md.

### L-36-06: Zähler nach einem neuen Ausschlussmuster verzögert

- **Beobachtung 21.10.2026 auf 8096:** Nach dem Speichern von `*.photoslibrary` ist die Datei sofort aus der Suche, die Zähler Indexiert / Durch Regel ausgeschlossen / Bewusst ausgelassen standen etwa 2 min später (zwei cron.php-Läufe) noch auf 100 / 0 / 0.
- **Ursache prüfen:** Kandidat `ScanRecountJob` (`INTERVAL_SECONDS = 15 * 60`).
- **Ziel 1.5.1:** sofortige Neuzählung nach dem Speichern oder ein Hinweis. Vom Owner akzeptiert, kein Blocker für 1.5.0. Siehe 36-AUDIT.md.
