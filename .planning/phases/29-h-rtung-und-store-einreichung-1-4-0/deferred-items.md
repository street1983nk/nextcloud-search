# Deferred Items Phase 29

## Aus 29-07 (außerhalb des Plan-Umfangs, nicht gefixt)

- **Pillow 12.3.0, TIFF mit Orientierungstag 6:** Pillow wendet die Orientierung eines TIFF schon beim Laden selbst an, `exif_transpose` sieht danach keine Orientierung mehr. Lokal beobachtet: ein 1000x700-TIFF (linke Hälfte schwarz) mit Tag 274 = 6 meldet vor dem Laden 700x1000, nach dem Laden 1000x700 mit oberer Hälfte weiß und unterer schwarz, also nicht die erwartete 90-Grad-Drehung (ein JPEG mit derselben Orientierung kommt korrekt als 700x1000 mit oberer Hälfte schwarz an). Verhalten ist vor und nach 29-07 identisch (Kopie und in_place liefern dieselben Bytes, Test `test_every_frame_of_a_rotated_multi_frame_tiff_is_upright` pinnt die Gleichheit). Gedrehte TIFFs sind im Feld selten; prüfen, ob das ein Pillow-Fehler ist (Upstream-Issue zusammen mit dem OPEN_INFO-Vorschlag aus 29-15).
