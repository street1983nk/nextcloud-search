# Deferred Items Phase 29

## Box-gebundene Belege (D-29-11), nächste Anfahrt

Phase 29 bleibt boxlos (Owner-Entscheid D-29-11). Die vier Feldbelege warten auf die nächste ohnehin nötige Anfahrt einer Box (budachst-ähnlicher Bestand oder AWS-Box), keiner davon ist im Store-Text versprochen (T-29-07):

1. **Fall 1 (#18, 512-MB-Adressraum):** Diagnosezeile aus Entscheid A (embed-handover, a0ac5aee) ist eingebaut; der Feldbeleg fehlt: `nextcloud.log` mit der requeue-Warnung (Anzahl, Klasse, Status, Dauer), `NPA_TIMEOUT` der Instanz und der HaRP-Pfad nebeneinander. Nächste Anfahrt.
2. **fp32-Rückkehr-Vollständigkeit:** Statusreihe nach einem Wechsel fp32 und zurück auf int8 bis `embedded == indexed` bei `indexed > 0`, dazu leere `EMBEDDING_BACKLOG_MARK` in state.db. Lokal belegt durch `test_launch_hardening.py::test_a_second_precision_change_before_the_first_rewrite_ends_leaves_a_consistent_stock_under_the_right_mark`, im Feld offen. Nächste Anfahrt.
3. **Fall 2 (#18, Kurz-Download):** Feldlauf hinter einem Proxy, der Antworten abschneidet, mit dem Beleg, dass ShortRead greift (keine corrupt-Urteile, Zeilen laufen in den Lock-Timeout und enden höchstens als repeatedly_stuck). Lokal belegt durch `test_poller.py::test_a_download_that_stays_short_gets_no_verdict_and_the_pass_goes_on`. Nächste Anfahrt.
4. **250-MiB-Feldlauf an Zelle 11:** Lauf der Messleiter mit dem Vollindex-Term (D-29-12) an Zelle 11. Nächste Anfahrt.

**Annahme A5 (Faktor 2 der Header-Schätzung):** `_WORKING_COPIES = 2` in `extract/image.py` stammt aus den gemessenen Spitzen (8192 x 5464: CMYK 131 MiB, RGB 48 MiB nach draft). RLIMIT_AS zählt Adressraum, nicht den gemessenen Arbeitssatz, daher ist der Faktor eine Untergrenze. Im Feld prüfen: Anteil der out_of_memory-Urteile mit Klasse `findling.extract.image.HeaderEstimate` gegen solche ohne Klasse (Tod im Decoder) auf dem Bestand der meldenden Instanz. Nächste Anfahrt.

## Bewusst nicht in der Nachprüfung: ocr_failed

Die einmalige Nachprüfung nach dem Upgrade (D-29-10, `worker/recheck.py`) wählt failed(corrupt), failed(out_of_memory), skipped(system_file), skipped(legacy_format), skipped(unsupported_variant) und jeden Sidecar-Namen. failed(ocr_failed) bleibt draußen (Research Pattern 7, Open Question 4, ratifiziert in 29-02 Teil 9): `extract/image.py` mappt den Tod der Engine am Adressraum auf ocr_failed, kein Fix von 1.4.0 berührt die Engine, und der draft-Pfad senkt das Bild nicht, das die Engine bekommt (höchstens 3500 px Kante ohnehin). Ein zweiter Lauf kostete OCR-Zeit für dasselbe Urteil. Test: `test_recheck.py::test_ocr_failed_is_never_selected`. Eine Datei mit ocr_failed wird wie bisher bei einer Änderung neu gelesen.

## Aus dem Phasenaudit (29-14), LOW mit Entscheid "bewusst so"

- **F-29-03, ShortRead gegen veraltete Cachegröße:** Ist die Größe im Dateicache größer als die Datei (externer Speicher außerhalb von Nextcloud geändert und nicht gescannt, oder falsche Klartextgröße bei serverseitiger Verschlüsselung), endet die Datei als failed(repeatedly_stuck) statt indexiert, bis ein Scan das ETag ändert und der Abgleich sie neu einreiht. Feldbeobachtung: Anteil repeatedly_stuck auf Instanzen mit externem Speicher oder Verschlüsselung. Falls das im Feld auftritt, Kandidat für 1.4.1: zwei kurze Antworten mit identischer Bytezahl als echte Dateigröße lesen. Das ändert D-29-04 und braucht ein Owner-Wort.
- **F-29-05, Nachprüfung in einer Runde:** auf sehr großen Beständen (100.000 Sidecars wären 500 requeue-Aufrufe) verzögert die erste Runde nach dem Upgrade den Claim einmalig. Feldbeobachtung, kein Fix geplant.

## Aus 29-07 (außerhalb des Plan-Umfangs, nicht gefixt)

- **Pillow 12.3.0, TIFF mit Orientierungstag 6:** Pillow wendet die Orientierung eines TIFF schon beim Laden selbst an, `exif_transpose` sieht danach keine Orientierung mehr. Lokal beobachtet: ein 1000x700-TIFF (linke Hälfte schwarz) mit Tag 274 = 6 meldet vor dem Laden 700x1000, nach dem Laden 1000x700 mit oberer Hälfte weiß und unterer schwarz, also nicht die erwartete 90-Grad-Drehung (ein JPEG mit derselben Orientierung kommt korrekt als 700x1000 mit oberer Hälfte schwarz an). Verhalten ist vor und nach 29-07 identisch (Kopie und in_place liefern dieselben Bytes, Test `test_every_frame_of_a_rotated_multi_frame_tiff_is_upright` pinnt die Gleichheit). Gedrehte TIFFs sind im Feld selten; prüfen, ob das ein Pillow-Fehler ist (Upstream-Issue zusammen mit dem OPEN_INFO-Vorschlag aus 29-15).

## Float-TIFF (SampleFormat 3)

Nur evaluieren, nicht zugesagt (Korrektur 05.10.). 1.4.0 gibt Float-TIFFs das ehrliche Urteil skipped(unsupported_variant) statt corrupt (T-29-23, `test_ocr.py::test_a_float_tiff_is_an_unsupported_variant_and_not_corrupt`). Ein Decode über eine Normierung der Gleitkommawerte auf 8 Bit wäre ein eigener Pfad mit eigenem Speicherbudget; Kandidat nach Feldbedarf.

## Admin-UI-Reste

- **#21 Limits auf der Admin-Seite anzeigen** (Zellgrenze, Bytegrenze, Adressraum je Dokument): in 1.4.0 nur als Deploy-Variable deklariert (FINDLING_MAX_CELLS), keine Anzeige.
- **#22 Ausschlussmuster als Einstellung** und Sonderbehandlung von Mac-Bundles (.key, .pages als Ordner): nicht gebaut; Sidecars werden fest übersprungen.
- **Fehlerklasse auf der Diagnosekarte** ist seit 29-12 eingebaut; die gemeinsame Playwright-Runde der Owner-Abnahme (29-14 Task 3) prüft die drei neuen Labels und die Zeile "Error class" in Englisch und Deutsch.

## Deferred Ideas aus 29-CONTEXT.md (Verweis)

Siehe `29-CONTEXT.md`, Abschnitt Deferred Ideas: eigenes Verdikt "abgeschnitten" für #18 (Kandidat 1.4.1, erst nach belegtem Befund), #21-Anzeige, #22-Einstellung und Mac-Bundles, HEIF/HEIC-Opener (Hypothese, nicht belegt), Box-Belege D-29-11 (oben), Float-TIFF (oben).
