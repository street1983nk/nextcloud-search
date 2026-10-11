---
phase: 31-neue-formate-und-nachholweg
plan: 07
subsystem: Extraktion (extract/image.py, extract/sandbox.py), Image-Probe (docker.yml)
tags: [fmt-05, d-31-06, heic, heif, pillow-heif, rlimit-as, malloc-arena, checkpoint]
requires:
  - phase: 31-01
    provides: "pillow-heif==1.8.0 gepinnt, Lizenzbelege"
  - phase: 31-06
    provides: "Stand 5283634b"
provides:
  - "pillow-heif als Pillow-Plugin in extract/image.py (thumbnails, depth, aux aus, decode_threads=1)"
  - "HEIF-Schätzung als Messmodell: 80 MiB fest plus 7 Byte je Pixel (RGB), 9 Byte für andere Modi; HEIF über der Schätzung -> skipped(too_large)"
  - "abgeschnittene HEIC (ValueError aus load) -> failed(corrupt) detail builtins.ValueError"
  - "sandbox._limit_malloc_arenas: mallopt(M_ARENA_MAX, 1) im Extraktionskind vor den Parser-Importen"
  - "backend/tests/probe_image_ocr_heic.py: OCR-Beweis (Gate) und RAM-Messung im Image, amd64 und arm64"
  - "Messbericht docs/measurements/2026-10-formate-v15, Abschnitte HEIC-Dekodier-RAM und Eine malloc-Arena im Extraktionskind"
affects: [31-10 Freischaltung image/heic und image/heif, 31-12 Saatdateien, 31-14 docs/formats.md, 31-15 Audit (JPEG out_of_memory gegen HEIF too_large)]
tech-stack:
  added: []
  patterns: ["Adressraum-Schätzung als gemessenes Modell fest plus je Pixel", "mallopt im Kind statt Umgebungsvariable, damit Hauptprozess und Enkel unberührt bleiben", "Messprobe im Image mit Kindprozessen und Selbstabbruch per SIGALRM"]
key-files:
  created:
    - backend/tests/test_image_heic.py
    - backend/tests/probe_image_ocr_heic.py
    - .planning/phases/31-neue-formate-und-nachholweg/31-07-SUMMARY.md
  modified:
    - backend/src/findling/extract/image.py
    - backend/src/findling/extract/sandbox.py
    - backend/tests/test_sandbox.py
    - backend/tests/test_measurement_scripts.py
    - .github/workflows/docker.yml
    - docs/measurements/2026-10-formate-v15/README.md
    - docs/ocr.md
decisions:
  - "Checkpoint ausgelöst: 48-MP-HEIF endete unter 512 MiB auf beiden Architekturen als skipped(too_large) (Lauf 38121953472)"
  - "Owner-Entscheid: MALLOC_ARENA_MAX messen; Fall A eingetreten (Wert 1: 48 MP mit 15,9/17,3 % Rest, kein Nachteil im Text- und OCR-Weg); gesetzt nur im Extraktionskind per mallopt; Limit bleibt 512 MiB"
  - "Schätzung für HEIF ist ein Messmodell (80 MiB + 7 B/px RGB, 9 B/px sonst) statt Faktor; Planregel (Faktor 5,5) hätte 24 MP gesperrt, Faktor 3 ließ 36 bis 38 MP durch"
  - "decode_threads=1 bleibt, obwohl mit einer Arena 4 Threads nicht mehr Adressraum kosten (A5 war der Arena-Effekt)"
  - "Offen für 31-15: JPEG über der Schätzung failed(out_of_memory) (D-29-07), HEIF skipped(too_large)"
metrics:
  duration: "ca. 130 min Arbeit (ohne Wartezeit am Checkpoint)"
  completed: 2026-10-11
  tasks: 3
  files: 10
---

# Phase 31 Plan 07: HEIC/HEIF im Bildpfad mit gemessenem Speicherbedarf Summary

HEIC-Fotos laufen über pillow-heif durch den gehärteten Bildpfad und werden im Image auf amd64 und arm64 per OCR gelesen. Die Messung zeigte für HEIF einen festen Anteil von rund 160 MiB: Die malloc-Arena des Decoder-Threads reserviert Adressraum, den RLIMIT_AS mitzählt. Mit einer Arena im Extraktionskind passt auch ein 48-MP-Foto unter den Standard von 512 MiB, mit 16 bis 17 Prozent Rest. Die Schätzung ist jetzt ein Messmodell statt eines Faktors. Freischaltung der Mimetypen folgt in 31-10.

## Checkpoint (Task 3): ausgelöst, Owner-Entscheid

- Ausgelöst durch Lauf 38121953472: `heic-ram mp=48 fmt=HEIF ... estimate_mib=558.1 ... verdict=skipped/too_large` auf amd64 (Restgröße 439,3 MiB) und arm64 (446,6 MiB). Bis dahin committet und gepusht: 44cf3fc7, fc6e2f2d, 6c87b22f; Grenzen und Budget nicht geändert.
- Entscheid des Owners: zuerst `MALLOC_ARENA_MAX` messen (unset, 1, 2). Fall A (ein Wert passt sicher, mindestens 10 % Rest, kein Nachteil) -> gezielt im Extraktionskind setzen, Limit bleibt 512 MiB. Fall B -> option-b (too_large dokumentieren). Schätzung als Messmodell, Tests mit Gegenprobe; JPEG/HEIF-Urteilsfrage für 31-15 notieren.
- **Eingetreten: Fall A mit `MALLOC_ARENA_MAX` = 1.** docs/formats.md bekommt deshalb keinen too_large-Satz.

### Messtabelle MALLOC_ARENA_MAX (Lauf 38124726627, Commit ff610f10, Median aus 3, MiB)

| Arch | Wert | Laden 12/24/48 MP (VmPeak-Zuwachs) | Spitze voller Pfad 12/24/48 MP (absolut, unter 512 MiB) | Rest bei 48 MP |
|---|---|---|---|---|
| amd64 | unset | 241,4 / 323,4 / 485,6 | 354,9 / 418,6 / 500,5 | 11,5 (2,2 %) |
| amd64 | 1 | 113,4 / 195,4 / 357,6 | 226,9 / 290,6 / 430,6 | **81,4 (15,9 %)** |
| amd64 | 2 | 177,4 / 259,4 / 421,6 | 290,9 / 354,6 / 494,6 | 17,4 (3,4 %) |
| arm64 | unset | 241,5 / 323,5 / 485,8 | 347,8 / 411,7 / 509,4 | 2,6 (0,5 %) |
| arm64 | 1 | 113,5 / 195,5 / 357,8 | 219,8 / 283,7 / 423,4 | **88,6 (17,3 %)** |
| arm64 | 2 | 177,5 / 259,5 / 421,8 | 283,8 / 347,7 / 487,4 | 24,6 (4,8 %) |

- VmHWM des vollen Pfads zwischen den Werten höchstens 1,5 MiB verschieden, Laufzeit gleich (amd64 0,76/0,97/1,32 s).
- Übriger Weg des Kinds (Text-PDF, DOCX mit numpy, Scan auf der OCR-Route, JPEG): VmPeak, VmHWM, Sekunden und Urteil für unset, 1 und 2 gleich (größte Abweichung 0,4 MiB und 30 ms). Das Kind ist einthreadig (Pools gepinnt), Tesseract ein eigener Prozess; im Hauptprozess mit Threads ist nichts gemessen, deshalb dort nichts gesetzt.
- Gegenprobe mit dem ausgelieferten Mechanismus (mallopt im Kind), Lauf 38125992894: 48 MP indexed, absolute Spitze 431,7 MiB (amd64, Rest 80,3 MiB = 15,7 %) und 424,8 MiB (arm64, 87,2 MiB = 17,0 %); Werte mit mallopt gleich denen mit Umgebungsvariable auf 0,1 MiB.
- Korrektur einer eigenen Aussage aus dem Checkpoint-Bericht: Der volle Pfad eines 48-MP-HEIF passte auch ohne Arenagrenze, aber mit nur 2,6 bis 11,5 MiB Rest. Im Messbericht vermerkt.

## Task 1: HEIC im Bildpfad

- `pillow_heif.register_heif_opener(thumbnails=False, depth_images=False, aux_images=False, decode_threads=1)` beim Modulimport; `DISABLE_SECURITY_LIMITS` bleibt False.
- `picture.load()` eng in `_read_frames`: ValueError -> `failed(corrupt)` detail `builtins.ValueError`; libheif meldet abgeschnittene Pixeldaten als ValueError, alle anderen Decoder als OSError (lokal belegt: Kürzung vor Byte 372 -> UnidentifiedImageError beim Öffnen, danach ValueError beim Laden).
- HEIF über der Schätzung -> `skipped(too_large)`; andere Formate unverändert `failed(out_of_memory)` (D-29-07).
- RED (einzeln, gegen den Stand ohne Registrierung): `9 failed, 1 passed, 1 skipped`. Der Test "abgeschnittener Kopf" war vorher grün (gleiches UnidentifiedImageError-Urteil); belegt durch Gegenprobe G6 (detail im OSError-Zweig verändert -> rot).
- Gegenproben (je ein Eingriff, rot, zurückgebaut): G1 ohne ValueError-Handler -> abgeschnittene HEIC rot; G2 Faktor 2 -> zwei Schätzungstests rot; G3 HEIF als out_of_memory -> Adressraumtest rot; G4 doppelte Drehung -> zwei Tests rot; G5 Standardoptionen -> Optionstest rot.
- Der Engine-Test mit echtem Tesseract läuft weder lokal noch im Python-Gate (kein tesseract); verbindlicher Beweis ist die Image-Probe.

## Task 2: Image-Probe, Messung, Modell

- Probe `backend/tests/probe_image_ocr_heic.py`, Schritt "HEIC OCR and decode memory in the image (FMT-05)" in docker.yml auf beiden Architekturen, Frist 5 min (Lauf dauert rund 35 s). Gate: Optionen `[False, False, False, 1]`, HEIC-Seite `indexed` mit `fotoquendel`, weiße HEIC `skipped/empty_text`. Logzitat (Lauf 38125992894, beide Architekturen): `heic page: verdict indexed/-, fotoquendel found: True`, `heic ocr in the image: ok`.
- Kinder: Selbstabbruch per `signal.alarm(180)`, Eltern warten höchstens 210 s.
- Erste Messung ohne Arenagrenze (Lauf 38121953472): HEIF 241/323/486 MiB beim Laden (fest rund 160 MiB plus 7 Byte je Pixel), JPEG genau 4 Byte je Pixel; 4 Decoder-Threads 707 statt 323 MiB (A5).
- Der MALLOC_ARENA_MAX-Sweep lief einmal (Teil 3 der Probe, Commit ff610f10) und wurde danach wieder aus der Probe genommen; die Kinder der Probe rufen jetzt `sandbox._limit_malloc_arenas()` wie das Extraktionskind.
- **Modell** (Konstanten mit Herleitung in image.py und im Bericht): Laden mit einer Arena = 32,0 MiB + 7,00 B/px exakt an allen drei Größen; voller Pfad bei 12/24 MP höchstens 72,6 MiB über der Ladegeraden (Arbeitskopie für die OCR). Modell 80 MiB + 7 B/px liegt über jedem Messwert und über der Schranke "Ladegerade + 5 B je Pixel der verkleinerten Kopie" bis 50 MP; 12/24/48 MP schätzt es auf 161,4/243,4/405,6 MiB gegen 437,9/445,0 MiB Restgröße. Alpha und andere Modi: 9 B/px als ungemessene obere Schranke.
- Modelltests: RED als Gegenproben, je rot: Faktor 3 (5 Tests: 12-MP-Messwert, 48 MP passt nicht x2, Lücke, Alpha), Faktor 5,5 (6: 24 und 48 MP x2, Lücke, Alpha), 40 MiB fest (3), 6 B/px (2), `>=` statt `>` (Grenztest), Alpha wie RGB (1).
- Arenatests in test_sandbox.py: RED `4 failed, 1 skipped` (der Linux-Test ist unter Windows übersprungen); GREEN; der Linux-Test lief im Python-Gate 38125992889 (nicht in der Skip-Liste) und hat seine Gegenprobe eingebaut (ohne Grenze mindestens 64 MiB Zuwachs, mit Grenze unter 32 MiB; lokal im Image 72 gegen 8 MiB).
- A5 neu bewertet: mit einer Arena kosten 4 Threads gleich viel wie einer (195,4 MiB); decode_threads=1 bleibt.
- docs/ocr.md: HEIC-Bedarf mit einer Arena, 48 MP unter 512 MiB, Hinweis auf `FINDLING_EXTRACT_ADDRESS_SPACE_BYTES`.

## Commits

| Commit | Inhalt |
|---|---|
| 44cf3fc7 | feat(31-07): HEIC and HEIF through the picture branch, provisional factor |
| fc6e2f2d | docs(31-07): HEIC decode memory on amd64 and arm64, 48 MP over the default cap |
| 6c87b22f | docs(31-07): state at the owner checkpoint of the 48 MP HEIF |
| ff610f10 | test(31-07): image probe measures MALLOC_ARENA_MAX unset, 1 and 2 |
| c64bdf04 | feat(31-07): one malloc arena in the extraction child, HEIF estimate by measured model |
| 075a75f3 | docs(31-07): one malloc arena, 48 MP HEIF fits 512 MiB, the measured model |

## Gates und CI

- Lokal vor jedem Code-Commit: ruff check, ruff format (229 Dateien), pyright latest 0 Fehler, vulture grün; volle Suite vor 44cf3fc7 und fc6e2f2d `5197 passed, 26 skipped`, vor c64bdf04 `5217 passed, 27 skipped`; vor ff610f10 die betroffenen 672 Tests.
- Baumhash: 44cf3fc7 `e8f55044...cdca0`, c64bdf04 `3dd8dc3c9dbd42b52109a84361ca6ce9e3a654139c446a5315eb18108692b8e3`, PACKAGE_FILES_TODAY 77, Journalabsätze "Plan 31-07".
- CI, alle grün:
  - 44cf3fc7: Multi-arch image **38121953472**, Python gates **38121953464**, Integration 38121953459, Resilience 38121953452, Security 38121953461, Scorecard 38121953502; HaRP 38121953486 durch den Folgepush abgebrochen (concurrency cancel-in-progress).
  - fc6e2f2d: Multi-arch image **38122992533**, Python gates 38122992518 (5208 passed), Integration 38122992583, Resilience 38122992510, HaRP **38122992531**, Security 38122992498, Scorecard 38122992522.
  - ff610f10: Multi-arch image **38124726627** (Sweep), Python gates 38124726549, Integration 38124726588, Resilience 38124726584, HaRP 38124726598, Security 38124726605, Scorecard 38124726567.
  - c64bdf04: Multi-arch image **38125992894**, Python gates **38125992889** (5229 passed, 15 skipped), Security 38125992903, Scorecard 38125992905, Integration 38125992871, Resilience 38125992900, HaRP **38125992946**.
  - 075a75f3 (nur Doku): Python gates 38126396672, Security 38126396745, Scorecard 38126396689.

## Deviations from Plan

**1. [Rule 4 -> Owner] Checkpoint ausgelöst, Entscheid umgesetzt.** Statt option-a oder option-b nach Owner-Vorgabe die malloc-Arenen gemessen und begrenzt (Fall A). Neue Funktion in sandbox.py, die nicht in der Dateiliste des Plans stand.

**2. Faktorregel des Plans ersetzt.** Die Regel (kleinster Faktor über allen VmPeak-Zuwächsen) ergab 5,5 und hätte 24 MP gesperrt; auf Owner-Entscheid Messmodell fest plus je Pixel.

**3. HEIF über der Schätzung `skipped(too_large)`, JPEG weiter `failed(out_of_memory)`.** Wie im Plan verlangt; die Ungleichheit ist für das Audit 31-15 notiert.

**4. Probe misst mehr als geplant:** Laden unter dem Deckel, Thread-Vergleich (A5), einmalig der Arena-Sweep mit dem Text- und OCR-Weg des Kinds (Korpus eingebunden, danach wieder entfernt).

**5. Vokabelregel E-H2:** Der erste Testsatz enthielt den gesperrten Wortstamm; ersetzt durch "fotoquendel im Kellerraum der Gemeinde" (fc6e2f2d).

**6. Job-Frist von docker.yml:** zuerst auf 35 min angehoben, nach dem gemessenen Lauf (35 s) wieder 20 min, Schrittfrist 5 min.

**7. Eigene Fehleinschätzung korrigiert:** Im Checkpoint-Bericht stand, der volle Pfad eines 48-MP-HEIF passe ohne Arenagrenze nicht. Gemessen passte er knapp (2,6 bis 11,5 MiB Rest); im Messbericht als Korrektur vermerkt.

## Known Stubs

Keine. image/heic und image/heif sind absichtlich noch nicht in der Allowlist (Plan 31-10); FMT-05 bleibt bis dahin offen.

## Threat Flags

Keine neue Fläche über das Register hinaus. T-31-20 (Optionen, Sandbox-Kind), T-31-21 (MAX_IMAGE_PIXELS-Test, Messmodell, too_large statt Kill), T-31-22 (ValueError eng, Test) umgesetzt. `ctypes.CDLL(None)` im Kind lädt nur die schon geladene C-Bibliothek des Prozesses.

## Self-Check: PASSED

Alle sechs Commits vorhanden (git cat-file), alle Dateien der key-files vorhanden, alle CI-Läufe oben grün.
