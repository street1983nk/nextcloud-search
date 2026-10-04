---
created: 2026-10-04
title: "Oeffentliche 1.4-Zusagen aus #18 (03.10.) und der OCR-zu-Embed-Lock-Timeout aus Lauf 9"
area: general
---

## A. In #18 oeffentlich zugesagte 1.4-Punkte (Kommentare 5970113095/5971965802/5974358682, alle diagnostisch belegt)

1. Sidecar-Skip: `._*` (AppleDouble, #22-Entscheid) UND `~$*` (Office-Lockstubs) ueberspringen mit ehrlichem Verdikt. Auf der budachst-Instanz 4.486 von 6.685 corrupt (67 %).
2. TIFF-Decode-Shim, zwei Achsen (macht die Dateien INDEXIERBAR, nicht nur ehrlicher beschriftet):
   a) fehlende OPEN_INFO-Eintraege Grau+Extrakanal mit ExtraSamples 0/1 (Golfpreis-Klasse; per Nachbau mit Pillow 12.3.0 bewiesen, Experiment in der Session vom 03.10.);
   b) SampleFormat-0-Normalisierung auf den Spec-Default 1 (zweite Variantenklasse, 16-bit-RGBA-Druckexporte hinter .png/.jpg-Namen; SampleFormat != 1 reproduziert den Fehler exakt). Dazu Upstream-PR an Pillow vorschlagen.
3. Grosse JPEGs bei reduzierter Skalierung dekodieren (Pillow draft-Mode; wir skalieren fuer OCR ohnehin auf 3500 px) + Header-Vorabschaetzung Breite x Hoehe x Kanaele gegen den Adressraum-Deckel -> ehrliches Urteil statt "beschaedigt". Belegt: 50-MB-CMYK 8192x5464 dekodiert ohne Deckel sauber; oom-Split 99 % Bilder (2.251 jpeg).
4. OLE-Sniff: Kopf d0cf11e0 unter OOXML-Endung -> ehrliches Verdikt, unterscheide legacy (.xls, Stream "Workbook"/"Book") vs. passwortgeschuetzt ("EncryptionInfo"/"EncryptedPackage"). Auf der Instanz 693 xlsx + 105 pptx + 70 docx.
5. Fehlerdetail je Datei speichern (die echte Reader-Exception statt pauschal corrupt); haette diese ganze Diagnose um Tage verkuerzt.
6. NACHPRUEFUNG der Altbestaende nach dem Upgrade: Verdikte kleben an der etag; die Fix-Klassen (1-4) muessen aktiv neu geprueft werden, sonst bleiben zehntausende Fehlurteile stehen. Oeffentlich zugesagt ("re-checked after the upgrade, no manual cleanup").

## B. Produktbefund Lauf 9 (04.10., Owner-Entscheid: Debug nach der x86-Haelfte)

- OCR-zu-Embed-Uebergabe lief 2x in einen Lock-Timeout ("could not move 30 files to the embed track, they run into the lock timeout", 05:02:56Z + 05:34:19Z, je ANDERE 30 Dateien, exakt 60 s nach dem Commit). Die Dateien haengen bis zum OCR-Lock-Ablauf (1800 s) und werden einmal DOPPELT per OCR verarbeitet. Kein Datenverlust; Nutzerwirkung: Bestand bis 30 min spaeter vollstaendig + Doppelarbeit am Ende jeder Indexierung.
- Ursache UNBELEGT: der requeue-Pfad in queue.py protokolliert die Ausnahme ohne Details. Sofortmassnahme-Kandidat: Ausnahme-Details im requeue-Log.
- Belege: docs/measurements/2026-10-abnahme-anfahrt/rohdaten/m7g.4xlarge/L-T/container-auszug.txt, Lauf 9.
- Naechster Schritt: /gsd-debug boxlos nach Abschluss der x86-Haelfte.

- Slot: Phase 29 (Haertung 1.4.0); Punkt B ggf. frueher per Debug-Session.
