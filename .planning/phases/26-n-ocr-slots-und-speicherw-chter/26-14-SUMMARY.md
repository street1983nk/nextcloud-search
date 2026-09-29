---
phase: 26-n-ocr-slots-und-speicherw-chter
plan: 14
subsystem: ci, ops/measurement, docs
tags: [push, ci-evidence, sc2, sc3, phpunit, slot-ladder, PAR-02, PAR-03]
requires:
  - "26-11: Kill-Test tests/test_slots_kill.py (SC2, Linux-CI)"
  - "26-12: slot_ladder.py und measure.yml Job slots (SC3)"
  - "26-13: Live-Latenzprobe nice 10 (D-26-12)"
provides:
  - "docs/measurements/2026-09-slot-leiter-ci/: Leiter 1/2/4 auf arm64-CI mit Rohdaten"
  - "docs/performance.md: Nachtrag vom 29.09.2026 zur Slot-Leiter"
  - "CI-Belege SC2 (Kill-Test), PHPUnit 24/25/26, Abbild dev mit Phase-26-Poller"
affects: [26-VERIFICATION, 24-HUMAN-UAT Test 1, 28]
tech-stack:
  added: []
  patterns: []
key-files:
  created:
    - docs/measurements/2026-09-slot-leiter-ci/README.md
    - docs/measurements/2026-09-slot-leiter-ci/raw/ (8 Dateien)
  modified:
    - docs/performance.md
decisions:
  - "Owner-Entscheid Push: 'Ja, jetzt pushen (Empfohlen)' (29.09.2026, AskUserQuestion), push-now; nur main, keine Tags, kein force"
  - "raw/f4.txt der W4-Probe desselben Laufs zusätzlich abgelegt, damit die Einordnung gegen die W4-Obergrenze im selben Lauf belegbar ist"
metrics:
  duration: "ca. 35 min (Push 04:42Z bis 05:17Z)"
  completed: 2026-09-29
  tasks: 3
  files: 10
status: complete
---

# Phase 26 Plan 14: Push, CI-Belege und Messleiter Summary

Push nach Owner-Entscheid, alle sechs Push-Läufe grün (Kill-Test SC2 in Linux-CI, PHPUnit 386 Tests), arm64-Leiter über den echten Poller mit Faktor 2,000 und 1,979 je Stufe gegen 1,05 (gesamt 3,958) gemessen und abgelegt; Phase vom Owner am 29.09.2026 abgenommen.

## Tasks

| Task | Name | Commit | Dateien |
| ---- | ---- | ------ | ------- |
| 1 | Push-Entscheid | (kein Commit, Push `cce78abd..d91305df`) | keine |
| 2 | CI-Belege einsammeln, Messleiter ablegen | c364c8c8 | docs/measurements/2026-09-slot-leiter-ci/**, docs/performance.md |
| 3 | Owner-Abnahme | "approved" (29.09.2026), im SUMMARY-Commit | 26-14-SUMMARY.md |

## Task 1: Push-Entscheid

- Owner-Signal wörtlich: **"Ja, jetzt pushen (Empfohlen)"** (29.09.2026, per AskUserQuestion, über den Orchestrator übermittelt), entspricht `push-now`.
- Vor dem Push: `git log origin/main..HEAD --oneline | wc -l` = 229, alle Autor `street1983nk <k.cherif@outlook.de>`, keine Co-Author-Trailer.
- `git push origin main`: `cce78abd..d91305df`, keine Tags, kein force. Danach 0 lokale Commits vor origin.
- Der Messdaten-Commit c364c8c8 ist NUR LOKAL; ein weiterer Push braucht ein neues Owner-Wort.

## Task 2: CI-Belege

Push-Läufe auf Commit `d91305df`:

| Workflow | Lauf-ID | Ergebnis | Beleg |
|---|---|---|---|
| Python gates (python.yml) | 36522819711 | grün | ubuntu-24.04: 3904 passed, 11 skipped; ruff, format, pyright, vulture grün |
| PHP and store metadata gates (php.yml) | 36522819728 | grün | PHPUnit 11.5.56: OK (386 tests, 1400 assertions); php -l, info.xml grün |
| Multi-arch image (docker.yml) | 36522819732 | grün | `:dev` = Index `sha256:3327dd65ab563d446ba9f6f7fd2c4315f5204168846b1a78d0cea7c65da19205`, amd64 + arm64 |
| Integration | 36522819718 | grün | |
| Resilience | 36522819707 | grün | |
| HaRP deploy | 36522819716 | grün | |

- **SC2 Kill-Test:** `tests/test_slots_kill.py` hat als einzige Skip-Bedingung `sys.platform != "linux"`; auf ubuntu-24.04 liefen also beide Fälle mit (`-q` nennt keine Einzelnamen), der Lauf ist grün. Lokal unter Windows zählt die Suite 22 skipped, in CI 11.
- **PHPUnit-Posten eingesammelt** (derselbe Lauf 36522819728 fährt die ganze Suite `php/tests/Unit`):
  - Phase 26: 26-02 (KIND_BATCH_INDEX_LANE, profile_confirmed) und 26-05 (Adminseite, Kataloge): grün
  - Phase 24, 24-HUMAN-UAT Test 1 (php.yml grün inkl. ProfileControllerTest, WR-02-Fall): grün
  - Phase 25, 25-03/25-04 (PHPUnit lokal nicht fahrbar): grün
  - Das Nachtragen in 24-HUMAN-UAT.md bleibt dem Orchestrator bzw. dem Verifier überlassen.

Messlauf `measure.yml`, manuell mit `image_ref=dev` gestartet, nachdem docker.yml `:dev` vom Commit d91305df (mit Phase-26-Poller) veröffentlicht hatte:

| Lauf-ID | Jobs | Ergebnis |
|---|---|---|
| 36523219615 | W4 slot curve on arm64 (slots), Wave 0 arm64, Wave 0 amd64 | alle grün |

- Runner `ubuntu-24.04-arm`, Neoverse-N2, 4 Kerne, Digest wie oben, Commit d91305df.
- Leiter (Median Seiten/s): 1 Slot 0,286; 2 Slots 0,572; 4 Slots 1,132. Alle Runden `failed 0`, `byte_capped_claims 0`.
- **SC3-Faktoren:** Stufe 1 auf 2 = 2,000 (Zugewinn), Stufe 2 auf 4 = 1,979 (Zugewinn), gesamt 1 auf 4 = 3,958. Beide Stufen über 1,05.
- Einordnung: W4-Obergrenze 3,955 (26.09.) bzw. 3,976 im selben Lauf; der Poller erreicht sie praktisch voll.
- **K1-Hinweis:** Faktor 1 auf 4 = 3,958, also weit über 1,5. Kein K1-Rückfall.
- Nebenzahl (ohne Bewertung): embed_slots 1 = 60,3, embed_slots 2 = 90,4 Passagen/s.
- Abgelegt: `raw/` mit ladder-corpus, ladder-slots-1/2/4, ladder-factor, ladder-embed, machine und f4; README als Faktenliste; Nachtrag in performance.md.

Lokale Gates nach Task 2: `uv run pytest -q` 3893 passed, 22 skipped (Pin-Tests und test_profile.py grün); ruff check, ruff format --check, pyright latest (0 errors), vulture: grün.

## Stand der Success Criteria

| SC | Stand | Beleg |
|---|---|---|
| SC1 N Slots, Anspruch >= N OCR-Zeilen | grün | Pläne 26-02/04/06/09, Kill-Harness mit N = 4, PHPUnit grün |
| SC2 Kill in halber Staffel, N >= 4 | grün (CI) | python.yml 36522819711 auf ubuntu-24.04 |
| SC3 Faktor auf arm64-CI gegen 1,05 | grün (CI) | measure.yml 36523219615, 2,000 / 1,979; Sparsam-Pin grün |
| SC4 Wächter drosselt, senkt, zeigt an | grün (Tests), live optional | 26-03/26-10, Status- und Adminseite; Live-Blick im nc35-Harness als optionaler Abnahmepunkt |

- D-26-08 (Kill-Test beider Fälle in Linux-CI): grün.
- D-26-09 (Leiter 1/2/4, Sparsam ein Slot): grün.
- D-26-12 (Latenzprobe nice 10): live belegt in `docs/measurements/2026-09-nice-latenz/`, Owner-Abnahme dort bereits vermerkt.

## Task 3: Owner-Abnahme

- Signal wörtlich: **"approved"**, Owner-Abnahme der Phase 26 erteilt mit der Option **"Abnehmen (Empfohlen)"**, 29.09.2026, per AskUserQuestion, über den Koordinator übermittelt.
- Ohne den optionalen Live-Blick (Punkt 5, `/status` im nc35-Harness); SC4 bleibt damit durch Tests belegt.
- Keine Befunde des Owners. Der Plan sieht die Abnahme nur im SUMMARY vor, keine weitere Beweisdatei.

## Deviations from Plan

- **raw/f4.txt zusätzlich abgelegt:** nicht in der Dateiliste des Plans, aber nötig, um die Einordnung gegen die W4-Obergrenze im selben Lauf zu belegen. Kein Codeeinfluss.

Sonst wie geplant.

## Known Stubs

Keine.

## Threat Flags

Keine. T-26-46: Push nur nach Owner-Entscheid, Folge-Commit bleibt lokal. T-26-48: Rohdaten enthalten nur synthetische Scans und Maschinendaten.

## Self-Check: PASSED

- FOUND: docs/measurements/2026-09-slot-leiter-ci/README.md
- FOUND: docs/measurements/2026-09-slot-leiter-ci/raw/ladder-factor.txt
- FOUND: c364c8c8
- `grep -c slot-leiter-ci docs/performance.md` = 1, README enthält "1,05"
