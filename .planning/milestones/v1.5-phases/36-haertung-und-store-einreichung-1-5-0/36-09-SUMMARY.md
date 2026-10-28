---
phase: 36-haertung-und-store-einreichung-1-5-0
plan: 09
subsystem: Extraktion (Bild, Mail, OLE/CFB)
tags: [hart-06, d-36-02, d-36-17, f-36-07-1, blocked-malicious, image-pixels, mail-nesting, cfb-cycle, tiff]
requires: [36-07, 36-08, 36-17]
provides:
  - "image.IMAGE_BOMB_PIXELS_PER_BYTE = 1000 (O6); _refused_by_pillow: image_pixels oder too_large, MAX_IMAGE_PIXELS nur im try/finally aus"
  - "mail.MAIL_MAX_NESTING = 32 (O6); forwarding_depth (Stapel über raw_items, kein Header-Budget) und count_forward_headers für den RecursionError-Zweig"
  - "image._has_frame: Rahmenlauf bis ocr_max_pages plus eine Probe, n_frames wird im Produktcode nirgends gelesen (F-36-07-1)"
  - "cfb.CompoundCycle(CorruptCompoundFile) und cfb.check_cycles (DIFAT-Kette, Verzeichniskette, Verzeichnisbaum vor olefile)"
  - "Korpus aus 36-07 ohne eine xfail-Markierung"
affects: [36-11]
tech-stack:
  added: []
  patterns:
    - "Signatur als Unterklasse der Defekt-Ausnahme: CompoundCycle ist CorruptCompoundFile, wer nur die Elternklasse kennt, behält sein Urteil"
    - "Vorprüfung meldet nur die Signatur und lässt jeden anderen Defekt der Bibliothek (check_cycles schweigt bei allem außer einem Zyklus)"
    - "Rahmen per seek-Probe statt Zählung; die Probe hinter der Seitengrenze trennt Kappung und Dateiende"
key-files:
  created: []
  modified:
    - backend/src/findling/extract/image.py
    - backend/src/findling/extract/mail.py
    - backend/src/findling/extract/cfb.py
    - backend/src/findling/extract/legacy_doc.py
    - backend/src/findling/extract/legacy_xls.py
    - backend/tests/test_extract_signatures.py
    - backend/tests/test_phase36_hostile_corpus.py
    - backend/tests/test_phase31_audit.py
    - backend/tests/test_ocr.py
    - backend/tests/test_extract_mail.py
    - backend/tests/test_legacy_doc.py
    - backend/tests/test_legacy_xls.py
    - backend/tests/test_measurement_scripts.py
    - .planning/phases/36-haertung-und-store-einreichung-1-5-0/deferred-items.md
decisions:
  - "Kein neuer Detailcode für TIFF mit vielen Seiten (A3 nennt keine Signatur): Urteil bleibt READABLE bzw. indexed(truncated) nach D-08, nur die Laufzeit hängt an der Seitengrenze; keine Owner-Frage nötig, der Fall läuft im Kind in 0,20 s"
  - "DIFAT- und Verzeichniszyklen erkennt olefile nur als allgemeine OleFileError; deshalb walkt cfb.check_cycles beide vor olefile (Produkt-Fix vor Harness-Patch)"
  - "Eine Kette, die hinter ihrem Stream weiterläuft, wird bis zur Tabellenlänge weiterverfolgt: kehrt sie zu einem besuchten Sektor zurück, ist es cfb_cycle, sonst corrupt"
  - "Der Bytezustand entscheidet: test_legacy_xls 'fat_chain_that_runs_on_past_its_stream' (letzter Sektor zeigt auf den ersten) ist ein Zyklus und jetzt cfb_cycle, mit neuer Positivkontrolle ohne Zyklus (corrupt)"
  - "Die HEIC-Fallzeile 'declares-100000-by-100000' in test_phase31_audit ist nach A3 eine Bombe (10 GP in wenigen KB) und jetzt image_pixels; control.heic (60 MP) bleibt too_large"
  - "Gegenprobe n_frames: die gesperrte Property wirft nur, wenn Pillow die Kette noch laufen müsste (_n_frames unbekannt); Pillows eigene Grenzprüfung in seek liest den bereits bekannten Wert und walkt nichts"
metrics:
  duration: "ca. 90 min Arbeit (06:32 bis 08:00 Ortszeit) plus 61 min volle lokale Suite und das Warten auf CI"
  completed: 2026-10-21
  tasks: 3
  files: 14
requirements: [HART-06]
---

# Phase 36 Plan 09: Bild-, Mail- und OLE-Signaturen, TIFF-Rahmenlauf Summary

Drei weitere Angriffssignaturen enden jetzt als `skipped(blocked_malicious)` mit Detailcode: `image_pixels` (Pillow verweigert über 100 MP und das Bild deklariert mehr als 1000 Pixel je Dateibyte), `mail_nesting` (message/rfc822 tiefer als 32 Ebenen) und `cfb_cycle` (Zyklus in FAT-, MiniFAT-, DIFAT- oder Verzeichniskette und im Verzeichnisbaum). Der TIFF-Rahmenlauf liest höchstens `ocr_max_pages` Rahmen plus eine Probe und fragt `n_frames` nie ab (F-36-07-1): `tiff-of-100000-ifds` braucht im Sandbox-Kind 0,20 s statt 27,8 s. Der Korpus aus 36-07 hat keine xfail-Markierung mehr.

## Commits

| Task | Name | Commit |
|------|------|--------|
| 1 | image_pixels und mail_nesting, Bestandstests auf Zielurteil, Ratsche f22a443b | f93baefa |
| 2 | TIFF-Rahmenlauf an der Seitengrenze (F-36-07-1), Ratsche 9586dc89 | c46c1945 |
| 3 | cfb_cycle, Nachzug Audit und Legacy-Tests, letzte xfail weg, Ratsche 73e0501d | d120f953 |

## Was gebaut ist

**image.py**
- `_refused_by_pillow(path)` im Zweig `DecompressionBombError`: setzt `Image.MAX_IMAGE_PIXELS` im `try/finally` auf `None`, öffnet mit `mode="r"` nur für `.size`, setzt im `finally` zurück. `width * height > 1000 * max(Dateigröße, 1)` ergibt `image_pixels`, sonst `too_large`; jede Ausnahme beim zweiten Öffnen bleibt `too_large`.
- `_has_frame(picture, index)`: `seek(index)`; `EOFError`, `OSError`, `SyntaxError`, `ValueError`, `TypeError`, `KeyError`, `struct.error` heißen "kein weiterer Rahmen".
- `_decode_smaller`: Probe auf Rahmen 1, danach immer `seek(0)`, der Draft erst danach und nur ohne zweiten Rahmen.
- `_read_frames`: Schleife über `range(ocr_max_pages)`, ab Rahmen 1 per Probe; wurden alle Rahmen der Grenze gelesen und die Frist nicht erreicht, entscheidet die Probe auf Rahmen `ocr_max_pages` über `truncated`. `grep -rnE 'getattr\([^)]*n_frames|\.n_frames\b' src/findling` findet nichts.

**mail.py**
- `forwarding_depth(message)`: Stapel statt Rekursion, Content-Type aus `raw_items()`, also ohne Header-Budget und ohne Header-Parser. Über 32 endet die Mail vor dem Textsammeln als `mail_nesting`.
- Im `RecursionError`-Zweig zählt `count_forward_headers(raw)` die Zeilen `Content-Type: message/rfc822` (jede Schreibweise, nach CR oder LF); über 32 ist `mail_nesting`, sonst bleibt `failed(corrupt, RecursionError)`.

**cfb.py, legacy_doc.py, legacy_xls.py**
- `CompoundCycle(CorruptCompoundFile)` an den Zyklusstellen: Sektor doppelt in `_visit_once`, Kette hinter dem Streamende zurück auf einen besuchten Sektor (`_run_on`, durch die Tabellenlänge begrenzt), doppelter Sektor der Verzeichniskette in `_directory`.
- `check_cycles(path)` vor olefile, nach `check_fat_size`: DIFAT-Kette (`_walk_difat`, begrenzt durch die Sektoren der Datei) und Verzeichnisbaum (`_walk_tree`, Tiefensuche mit Pfadmarken, geteilte Einträge sind kein Zyklus). Wirft nur bei einem Zyklus, alles andere bleibt bei olefile.
- Beide Leser fangen `cfb.CompoundCycle` vor der Elternklasse. Der Sniff `ole_kind` fängt `CompoundCycle` mit und antwortet wie vorher (Baumzyklus: "word", Zyklus der Verzeichniskette: None).

## Bestandstests mit Zielurteil (D-36-17, plan 36-09)

**test_ocr.py**
- `test_a_picture_over_the_pixel_cap_is_too_large_without_being_decoded` heißt `..._is_blocked_malicious_without_being_decoded`: `blocked_malicious/image_pixels`, `engine.calls == []` bleibt.
- `test_a_picture_just_over_the_pixel_cap_is_too_large_as_well` (56 MP, Pillow warnt nur): unverändert TOO_LARGE.

**test_extract_mail.py**
- `test_twenty_five_hundred_forwarded_levels_end_as_corrupt` heißt `..._end_as_mail_nesting`: `skipped/blocked_malicious/mail_nesting`.
- `_nested_mail`-Fälle (900 Ebenen indexed, 1000 Ebenen corrupt/RecursionError, 2500 Ebenen truncated) und `test_a_recursion_error_in_every_access_ends_as_corrupt`: unverändert.

**test_legacy_doc.py** (Helfer `_blocked_cycle`)
- cfb_cycle: `test_a_fat_cycle_is_blocked_as_malicious_in_time` (beide Streams), `test_a_difat_cycle_is_blocked_as_malicious_in_time`, `test_a_minifat_cycle_is_blocked_as_malicious_in_time` (beide Parameter), `test_a_cycle_in_the_chain_of_the_mini_stream_itself_is_blocked_as_malicious_in_time`.
- unverändert corrupt: `fat_chain_past_the_end_of_the_file`, `fat_chain_that_ends_early`, `fat_declared_larger_than_the_file`, `directory_tree_too_deep_for_olefile` (RecursionError), `minifat_chain_past_the_mini_stream`.

**test_legacy_xls.py** (Helfer `_blocked_cycle`)
- cfb_cycle: `test_a_fat_cycle_is_blocked_as_malicious_in_time`; `test_a_difat_cycle_is_blocked_as_malicious_in_time[cycle]` (letzter DIFAT-Sektor zeigt auf den ersten), `[control]` (ENDOFCHAIN) wird gelesen; `test_a_minifat_cycle_is_blocked_as_malicious_in_time[cycle]`, control liest Text; `test_a_minifat_chain_that_runs_on_past_its_stream_into_a_cycle_is_blocked_as_malicious_in_time` (beide); `test_the_book_stream_behind_an_empty_workbook_is_checked_too[cycle]`, control liest Text.
- Abweichung vom Plan: `test_a_fat_chain_that_runs_on_past_its_stream_is_corrupt_in_time` baut `fat={start + 7: start}`, der letzte der acht Sektoren zeigt auf den ersten. Das ist nach dem Bytezustand ein Zyklus. Der Test heißt jetzt `..._runs_on_past_its_stream_into_a_cycle_is_blocked_as_malicious_in_time` (cfb_cycle). Neu ist die Positivkontrolle `..._runs_on_past_its_stream_without_a_cycle_is_corrupt_in_time` (`fat={start + 7: 100}`, corrupt).
- unverändert corrupt: `fat_chain_past_the_end_of_the_file`, `fat_declared_larger_than_the_file`.

**test_phase31_audit.py**
- `rfc822-nested-1000-times`: `blocked_malicious` (mail_nesting).
- Word: `difat-cycle`, `minifat-cycle`, `directory-cycle`, `fat-cycle` auf `blocked_malicious`, Detail `cfb_cycle` wird geprüft; `fat-declared-far-past-the-file` bleibt corrupt.
- Excel: `minifat-cycle-under-the-workbook` auf `blocked_malicious/cfb_cycle`.
- HEIC: `declares-100000-by-100000` auf `blocked_malicious/image_pixels` (10 GP in wenigen KB). `control.heic` (8000 x 7500) im Logtest bleibt TOO_LARGE.

**test_cfb.py**: unverändert grün. **test_image_heic.py** ~192 (gesenkte Grenze, declared_over 3.0): unverändert TOO_LARGE für HEIC und JPEG, die Testbilder liegen unter 1000 Pixel je Byte.

## Neue Randtests

- test_extract_signatures.py, image_pixels: PNG-Bombe ohne einen `load()`-Aufruf; honest_large_jpeg too_large; genau 1000 Pixel je Byte (400 000 Byte) too_large, 399 999 Byte blocked; 60 MP nur Warnung too_large; `MAX_IMAGE_PIXELS` vor und nach dem Zweig gleich, beim zweiten Öffnen `None`, auch wenn das zweite Öffnen wirft.
- mail_nesting: 33 blocked, 32 indexed, 1000 blocked statt corrupt, Tiefe 0/1/32/33 an der geparsten Mail, 40 weitergeleitete Geschwister indexed, Zählung jeder Schreibweise, RecursionError mit 33 bzw. 32 Weiterleitungsköpfen.
- cfb_cycle: sechs Zyklusarten für .doc (FAT, FAT der Mini-Stream-Kette, MiniFAT, DIFAT, Verzeichniskette, Verzeichnisbaum), fünf für .xls (der Workbook liegt im Mini-Stream, FAT-Fall ist die Container-Kette); Strukturfehler ohne Zyklus corrupt; `check_cycles` schweigt bei allem ohne Zyklus; Sniff-Antworten unverändert.
- test_ocr.py, Rahmenlauf: n_frames-Gegenprobe (3 Seiten, 3 Aufrufe), 3 Seiten bei Grenze 2 truncated mit 2 Aufrufen, 2 Seiten bei Grenze 2 ganz, 1 Seite, JPEG behält seinen Draft ("L", 3500 x 2800), `tiff_many_ifds(40_000)` mit Engine (truncated, 30 Aufrufe) und ohne Engine (ocr_unavailable) je unter 1 s, kaputter Link hinter Seite 2 liefert 2 Seiten ohne truncated, jede Strukturausnahme der Probe heißt "kein Rahmen".
- Rot belegt: alle neuen Tests gegen den Produktcode vor dem jeweiligen Task (Task 1: 13 rot, Task 2: die n_frames-Gegenprobe und die 40 000-IFD-Fälle rot, Task 3: 26 rot).

## Korpus (test_phase36_hostile_corpus.py)

- Alle Markierungen sind weg: `png-bomb`, `rfc822-nested-33-times`, `rfc822-nested-1000-times`, `tiff-of-100000-ifds` und die fünf CFB-Zyklen. `grep -c xfail` ergibt 0.
- Positivkontrollen bleiben: `honest-large-jpeg` und `png-of-60-megapixels` too_large, `rfc822-nested-32-times` indexed, `doc-fat-declared-far-past-the-file` corrupt, `tiff-ifd-cycle` READABLE.
- Laufzeiten lokal im Kind (Windows, `--durations`): `tiff-of-100000-ifds` 0,20 s (Grenze 5 s, vorher 27,8 s), `png-bomb` 0,09 s, `rfc822-nested-1000-times` 0,07 s, `xls-minifat-cycle` 0,02 s.

## Gates und CI

- Lokal grün: ruff check und format, pyright 0 errors, vulture; Baumhash je Task mit dem Rezept und unabhängig mit find, sort, tr, sha256sum (f22a443b, 9586dc89, 73e0501d).
- Volle Suite lokal: 6164 passed, 264 skipped, 1 failed, 15 errors in 61 min. Der Fehler `test_v14_zelle.py::test_kette_refuses_incomplete_values[broken4]` ist der bekannte Lastflake aus 36-08, das Modul einzeln 72 passed. Die 15 Errors sind `test_phase33_audit.py`: der Docker-Aufruf des PHP-Treibers lief lokal 600 s in den Timeout (Umgebung, kein Bezug zu diesem Plan); in CI grün.
- CI für d120f953 (der Push enthält alle drei Commits):
  - Python gates 39552834732 grün: ubuntu mit RLIMIT_AS, 6191 passed, 253 skipped, kein xfailed, 374,5 s. Das ist der Speicherbeleg für den ganzen Korpus. Der Lauf schreibt keine `--durations`, die Laufzeit einzelner Korpusfälle steht deshalb nicht im Log; die 5-s-Grenze von `tiff-of-100000-ifds` prüft der Test selbst (`ran.seconds < case.seconds`) und ist grün.
  - Grün: Integration 39552834576, Security scans 39552834509, Multi-arch image 39552834580, OpenSSF Scorecard 39552834512, Resilience 39552834702.
  - HaRP deploy 39552834525 grün in allen vier Beinen (stable33, stable34 amd64 und arm64, stable35).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Paket-Ratsche je Task statt einmal in Task 3**
- **Found during:** Task 1
- **Issue:** image.py und mail.py ändern den Baumhash; ohne Nachzug wäre der Commit von Task 1 rot gewesen. Der Plan wollte Task 2 und 3 gemeinsam committen, der Auftrag verlangt einzelne Commits je Task.
- **Fix:** drei Journalabsätze "Moved on 2026-10-21 by Plan 36-09" (f22a443b, 9586dc89, 73e0501d), je zweifach nachgerechnet; Task 2 eigener Commit.
- **Commits:** f93baefa, c46c1945, d120f953

**2. [Rule 1 - Bug] Zweites Image.open ohne Modus brach die Schreib-Ratsche**
- **Found during:** Task 2 (test_extract_edge_paths)
- **Issue:** Das neue `Image.open(path)` in `_refused_by_pillow` (Commit f93baefa) zählte die Ratsche als neue Öffnung.
- **Fix:** `Image.open(path, mode="r")` wie in `_read_normalised`. Der Commit von Task 1 ist in diesem einen Test rot; er wurde nicht einzeln gepusht, der Push trägt alle drei.
- **Commit:** c46c1945

**3. [Rule 1 - Bug] DIFAT- und Verzeichniszyklen endeten nicht im cfb-Walk**
- **Found during:** Task 3
- **Issue:** olefile erkennt beide selbst und meldet sie als OleFileError, also corrupt.
- **Fix:** `cfb.check_cycles` vor olefile (Plan: "Produktpfad so ziehen, dass er CompoundCycle wirft").
- **Commit:** d120f953

**4. [Rule 1 - Bug] Zyklus hinter dem Streamende**
- **Found during:** Task 3
- **Issue:** `_visit_once` endet nach der Streamlänge. Eine Kette, die danach in einen Zyklus läuft (test_legacy_xls "into a cycle", xlrd läuft sie), war nur corrupt.
- **Fix:** `_run_on` folgt der Kette bis zur Tabellenlänge weiter.
- **Commit:** d120f953

**5. [Rule 2 - Missing critical] TypeError und KeyError in der Probe**
- **Found during:** Task 2
- **Issue:** Pillows `_setup` meldet eine IFD hinter dem Dateiende als `TypeError("Missing dimensions")`, gemessen. Ohne Fang wäre ein kaputter Link auf Seite 3 als Ausnahme aus dem Zweig gegangen.
- **Fix:** beide in den Fang von `_has_frame` aufgenommen, mit eigenem Test.
- **Commit:** c46c1945

### Kleinere Abweichungen

- n_frames-Gegenprobe: Die Property wirft nur, solange `_n_frames` unbekannt ist. Pillows `seek` liest `n_frames` selbst, sobald das Kettenende bekannt ist; das ist eine gespeicherte Zahl, und eine immer werfende Property hätte Pillow statt dieses Codes geprüft. Gegen den alten Code ist der Test rot.
- test_legacy_xls `fat_chain_that_runs_on_past_its_stream` ist nach dem Bytezustand ein Zyklus (siehe oben), neue Positivkontrolle ohne Zyklus.
- test_phase31_audit HEIC `declares-100000-by-100000` ist nach A3 eine Bombe und jetzt image_pixels.
- Commit-Text von Task 3 ist der im Plan vorgegebene Sammeltitel, obwohl Task 1 und 2 eigene Commits haben.

## Threat Flags

Keine neue Oberfläche. T-36-32 bis T-36-37 sind umgesetzt: nur Kopf gelesen, MAX_IMAGE_PIXELS im finally zurück (getestet); iterative Tiefe und Vorzählung; eigene Ausnahme für Zyklen, Frist im Kind bleibt; Positivkontrollen honest_large_jpeg, control.heic, 40 Geschwister-Mails; Probe statt n_frames mit Gegenprobe und 5-s-Grenze im Kind; kein blocked_malicious für viele Seiten.

## Known Stubs

Keine.

## Self-Check: PASSED

- Dateien vorhanden: backend/src/findling/extract/cfb.py (mit `class CompoundCycle(CorruptCompoundFile)`), 36-09-SUMMARY.md
- Commits f93baefa, c46c1945 und d120f953 vorhanden und auf origin/main
- Alle sieben CI-Läufe für d120f953 grün
