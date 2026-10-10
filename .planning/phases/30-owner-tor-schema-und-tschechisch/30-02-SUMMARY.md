---
phase: 30-owner-tor-schema-und-tschechisch
plan: 02
subsystem: ocr/image
tags: [czech, ocr, tesseract, cz-01, docker, ci-proof]
requires: [30-01]
provides:
  - "tesseract-ocr-ces=1:4.1.0-2 im Image, Bau-Pruefung per --list-langs"
  - "OCR_LANGUAGE_ALLOWLIST mit zehn Eintraegen (ces), Standard bleibt deu, eng, fra"
  - "backend/tests/probe_image_ocr_czech.py: Bild-Beweis im gebauten Image"
  - "docker.yml-Schritt 'Czech OCR in the image (CZ-01)' auf amd64 und arm64"
affects: [30-04 TESSERACT_NAME cs, 30-08 Store-/README-Texte zehn Sprachen]
tech-stack:
  added: ["Debian tesseract-ocr-ces 1:4.1.0-2"]
  patterns: ["Bauform 16-10 (Pin, --list-langs, Allowlist, Gate)", "Image-Probe als nicht gesammeltes Skript mit Leerseiten-Gegenprobe"]
key-files:
  created:
    - backend/tests/probe_image_ocr_czech.py
  modified:
    - backend/Dockerfile
    - backend/src/findling/config.py
    - backend/tests/test_ocr_languages.py
    - backend/tests/test_measurement_scripts.py
    - THIRD-PARTY.md
    - .github/workflows/docker.yml
decisions:
  - "ces nur angeboten, nicht Standard (OCR_DEFAULT_LANGUAGES bleibt drei)"
  - "Probe verlangt 3 von 4 Erwartungswoertern; gemessen 4 von 4 auf beiden Architekturen"
metrics:
  duration: "ca. 35 min (davon 10,6 min volle Suite, ca. 6 min CI)"
  completed: 2026-10-10
  tasks: 2
  files: 7
---

# Phase 30 Plan 02: Tschechisch als OCR-Sprache Summary

`tesseract-ocr-ces` 1:4.1.0-2 gepinnt im Image, beim Bau per `--list-langs` erzwungen, `ces` in der Allowlist (zehn Einträge, Standard unverändert drei) und im gebauten Image auf amd64 und arm64 nachgewiesen: eine tschechische Zeile wird über `-l ces` gelesen und über die Kette `cs` zu den erwarteten Suchtermen.

## Ergebnis

- Paket verifiziert am 10.10.2026: madison (stable 1:4.1.0-2, main, all, Quelle tesseract-lang) und packages.debian.org/trixie (Download 1411716 Byte, installiert 3722.0 kB).
- `FINDLING_OCR_LANGUAGES=deu+ces` ergibt `("deu", "ces")` ohne Warnung (neuer Fall `test_czech_is_accepted_in_the_admin_order_without_a_warning`).
- Gates `test_every_offered_language_has_a_pinned_apt_line` / `..._is_proven_when_the_image_is_built` decken ces automatisch.
- Baumhash `d09ecf1f...5272`, `PACKAGE_FILES_TODAY` bleibt 74, Journalabsatz Plan 30-02.
- Lokal: volle Suite 4729 passed / 25 skipped, ruff, ruff format, pyright (latest), vulture grün; pytest sammelt die Probe nicht (0).

## CI-Beweis

docker.yml-Lauf **38027012519** (Commit 715c02c8), Ergebnis success: beide Build-Jobs und der Manifest-Merge grün. Ausgabe des Schritts "Czech OCR in the image (CZ-01)", identisch auf beiden Architekturen:

| Architektur | --list-langs ces | tschechische Seite | weiße Seite |
|---|---|---|---|
| linux/amd64 | True | 10 Tokens, 4 von 4 (smlouva, ucetni, rizeni, rijen) | 0 Tokens |
| linux/arm64 | True | 10 Tokens, 4 von 4 (smlouva, ucetni, rizeni, rijen) | 0 Tokens |

Imagegröße (Summe komprimierter Layer laut Registry-Manifest):

| Architektur | vorher (Tag 1.4.2) | nachher (Tag 715c02c8, = dev) | Differenz |
|---|---|---|---|
| amd64 | 301294996 | 303016706 | +1721710 Byte |
| arm64 | 296892302 | 298625455 | +1733153 Byte |

Die Differenz enthält neben dem ces-Paket (1411716 Byte Download) auch die kleinen Codeänderungen aus 30-01.

## Commits

| Commit | Inhalt |
|---|---|
| 07559931 | feat(30-02): Paket, Bau-Prüfung, Allowlist 10, env-Fall, THIRD-PARTY, Baumhash |
| 715c02c8 | test(30-02): Probe-Skript und docker.yml-Schritt |

Gepusht wurde `53dea276..715c02c8` auf origin main (inklusive der vorher ungepushten 30-01-Commits).

## Deviations from Plan

**1. [Rule 3 - Planabweichung Ort] Baumhash liegt in test_measurement_scripts.py, nicht in config.py**
- Plan nannte config.py; die Konstante `PACKAGE_TREE_HASH_TODAY` steht in `backend/tests/test_measurement_scripts.py` (wie in 30-01). Dort nachgezogen.

**2. [Formatierung] Tschechischer Satz literal statt als \u-Escapes**
- `ruff format` normalisiert die Escapes zu Literalen; das Repo führt tschechische Testdaten in `test_czech_analyzer.py` ebenfalls literal. Kommentar entsprechend angepasst, Bezeichner und Logik bleiben ASCII.

**3. [Ergänzung] Installierte Größe von ces (3722.0 kB) zusätzlich zur Downloadgröße** in Dockerfile-Kommentar und THIRD-PARTY.md, analog zu den sechs Packs von 16-10.

## Nicht erledigt / bewusst ausgelassen

- `TESSERACT_NAME["cs"] = "ces"` folgt mit Plan 30-04 (braucht `cs` in `SUPPORTED_LANGUAGES`).
- Store-/README-/info.xml-Texte "zehn Sprachen" folgen mit Plan 30-08.
- CZ-01 in REQUIREMENTS.md als erledigt markiert (Paket, Bau-Prüfung, Allowlist, Bild-Beweis); die Kopplung `TESSERACT_NAME["cs"]` reist mit CZ-02/30-04.

## Self-Check: PASSED

- Dateien vorhanden: probe_image_ocr_czech.py, Dockerfile mit ces-Zeile und Prüfung
- Commits 07559931 und 715c02c8 im Log, CI-Lauf 38027012519 success
