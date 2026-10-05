---
phase: 28-abnahme-anfahrt
plan: 12
subsystem: profile-formula
tags: [sc4, ocr-slot-cost, probe, guard, tree-hash, mess-10]
requires:
  - 28-11 (Owner-Entscheide vom 05.10.2026, README Abschnitt 14)
provides:
  - OCR_SLOT_COST_BYTES = 250 MiB (262.144.000 Byte) in Formel, Probe und Wächter
  - fortgeschriebener Baumhash-Pin 27db8b41...
  - Vorlage Vollindex-Term (Analyse, kein Code) für den Owner-Entscheid
affects:
  - backend/src/findling/profile.py (_memory_term, embed_lane_fits) über die Konstante
  - backend/src/findling/probe.py (judge, first_slot_admitted, pending_load_bytes)
  - backend/src/findling/guard.py (throttled_slots, Reserve)
tech-stack:
  added: []
  patterns: [Konstante mit Messquelle im Kommentar, Rechenweg im Testkommentar]
key-files:
  created: []
  modified:
    - backend/src/findling/config.py
    - backend/tests/test_config.py
    - backend/tests/test_profile.py
    - backend/tests/test_poller.py
    - backend/tests/test_v14_teilkorpus.py
    - backend/tests/test_measurement_scripts.py
    - docs/profiles.md
    - docs/admin-page.md
decisions:
  - "OCR_SLOT_COST_BYTES 235 -> 250 MiB nach Owner-Entscheid 05.10.2026; FP32_EXTRA_BYTES, MAIN_PROCESS_BASELINE_BYTES, EMBED_ACTIVATION_BYTES, NEXTCLOUD_CORE_LOAD unverändert"
  - "Vollindex-Term nicht gebaut, nur als Vorlage im SUMMARY; Umsetzung per Owner-Entscheid (Phase 29 oder Gap-Plan)"
  - "RESIDENT_FIGURE 730.2 bleibt (Store-Zahl: kein Fall)"
metrics:
  duration: ~40 min
  completed: 2026-10-05
  tasks: 2
  files: 8
---

# Phase 28 Plan 12: Rückfluss der Slot-Kosten (SC4) Summary

`OCR_SLOT_COST_BYTES` steht auf den vom Owner bestätigten 250 MiB = 262.144.000 Byte; Embed-Lane- und Wächter-Reserve folgen per Verweis, alle Rechenbeispiele sind aus der Formel neu gerechnet, der Baumhash-Pin ist fortgeschrieben, und für S-voll liegt eine Vorlage für einen Vollindex-Term zur Owner-Entscheidung vor.

## Was gemacht wurde

**Task 1 (TDD): Konstante und Tests**
- RED: Pin in `test_config.py` auf `250 * 1024 * 1024 == 262_144_000`, mit Quelle (Messordner, Abschnitt 14). Lauf schlug wie erwartet fehl.
- GREEN: `config.py` `OCR_SLOT_COST_BYTES = 250 * MIB`, Kommentar mit Messordner, Messzeitraum (01. bis 05.10.2026, 18 Zellen, ARM und x86), Maß (kleinster Slotwert, unter dem anon/Rechnung höchstens 1,10 für alle 17 Teilkorpus-Zellen gilt, gleichwertig 15 MiB Hauptprozess-Zuschlag je Slot) und Owner-Datum. `EMBED_LANE_RESERVE_BYTES` und `GUARD_RESERVE_BYTES` bleiben Verweise.
- Neu gerechnet:
  - `test_profile.py::test_the_fp32_term_shrinks_the_memory_term`: 16 GiB, Standard: Budget 0,32 x 16384 - 1257,5 = 3985,38 MiB; / 250 = 15 (vorher 16), fp32 (3985,38 - 367) / 250 = 14 (vorher 15).
  - `test_profile.py::test_the_activations_can_tip_the_lane_over`: die alte Box (4680 MiB) liefert mit 250 MiB schon ohne Aktivierungen 0 Slots (240,1 MiB). Neue Box 4730 MiB: 256,1 MiB = 1 Slot, minus 27 MiB = 229,1 MiB = 0 Slots; Fenster 4711 bis 4795 MiB im Kommentar.
  - `test_poller.py`: Kommentar 235 -> 250 MiB (Test symbolisch, 3 x Slotwert trägt weiter 3 Slots).
  - Probe-, Probe-Run- und Wächter-Tests sind symbolisch (`OCR_SLOT_COST_BYTES + GUARD_RESERVE_BYTES - 1` usw.) und liefern mit dem neuen Wert dieselben Verdikt-Übergänge; `first_slot_admitted` liegt bei 2 x 250 MiB. Keine Änderung nötig, alle grün.
  - Sparsam-Pin (ein Slot, OCR_CLAIM_BATCH = 2) unverändert grün.
- Baumhash: `PACKAGE_TREE_HASH_TODAY` per Test-Messung neu bestimmt = `27db8b4140529babd63912eeba93e63a9a63e36b0b2043274b37c2a953a4ad3f`, `PACKAGE_FILES_TODAY` bleibt 71, Kommentarblock nach Muster. Der Kommentar nennt die drei Bäume der Anfahrt-Zellen (Stände c87a0239, f73566c1, 18602c48), alle vor dieser Änderung. `PHP_TREE_HASH_TODAY` unverändert, `git diff --stat 68ebc5cb HEAD -- php` leer.

**Task 2: Texte**
- `docs/profiles.md`: Slotkosten 250 MiB mit Verweis auf `docs/measurements/2026-10-abnahme-anfahrt/`, Drossel (250 MiB plus Reserve 250 MiB), Auslöser der Absenkung (Headroom unter 250 MiB).
- `docs/admin-page.md`: "Passt knapp: Speicherreserve unter 250 MiB".
- `grep -c "235 MiB"` in beiden Dateien: 0. `docs/performance.md` nennt 235 MiB weiter als B2-Messergebnis (historische Quelle, bewusst unverändert).

## Verifikation

- Volle Suite: 4428 passed, 25 skipped (690 s).
- ruff check + format --check, pyright (latest, 0 Fehler), vulture (min-confidence 80), ruff über `scripts/`: grün.
- `test_store_metadata.py` grün, `RESIDENT_FIGURE` "730.2" unverändert.
- Kein Push.

## Commits

| Task | Commit | Inhalt |
|---|---|---|
| 1 RED | 66bf7a44 | test(28-12): pin OCR_SLOT_COST_BYTES to the measured 250 MiB |
| 1 GREEN | 2f26d9fb | feat(28-12): Konstante, neu gerechnete Tests, Baumhash-Pin |
| 2 | de177897 | docs(28-12): profiles.md, admin-page.md |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] test_v14_teilkorpus.py nachgezogen (nicht in files_modified)**
- **Found during:** Task 1
- **Issue:** `12-slotkosten.py rechnung` importiert `findling.config.OCR_SLOT_COST_BYTES`; der Test schrieb die Rechnung mit `235 * MIB` von Hand aus und schlug fehl.
- **Fix:** Handrechnung auf `250 * MIB`, Kommentar, dass die Anfahrt-Zellen noch mit 235 MiB liefen. Das Messskript selbst bleibt unverändert (`B2_SLOT_MIB = 235.0` ist der B2-Vergleichswert, kein Produktwert).
- **Commit:** 2f26d9fb

**2. [Rule 3 - Blocking] Baumhash-Pin mit Task 1 statt Task 2 committet**
- **Issue:** Der Pin deckt `config.py` ab; zwischen einem Task-1-Commit ohne Pin und Task 2 wäre die volle Suite rot gewesen (Regel: Gates grün vor jedem Commit).
- **Fix:** Pin im GREEN-Commit fortgeschrieben; Task 2 enthält nur die Doku.

**3. Bekannte Abweichung Abbild:** Der Plan nennt c87a0239 allein; die Messung lief auf drei Ständen (c87a0239, f73566c1, 18602c48, nur Probe-Schwellen/Reconcile/Crawl geändert, README Abschnitt 2). Kommentar im Pin-Block nennt alle drei Bäume.

**4. Kommentarmaß abweichend vom Planwortlaut:** Der Plan schlug als Maß "VmHWM Kind plus tesseract, Maximum über alle Zellen" (448 MiB) vor; der Owner wählte 250 MiB nach dem Tragekriterium. Der Kommentar in `config.py` nennt das tatsächlich gewählte Maß.

## TDD Gate Compliance

RED-Commit `test(28-12)` 66bf7a44 vor GREEN-Commit `feat(28-12)` 2f26d9fb. Kein Refactor nötig.

## Vorlage Vollindex-Term (S-voll, Owner-Entscheid offen)

Analyse, kein Code. Grundlage: README Abschnitte 4, 7, 10, 11.

**Befund**
- S-voll (m7g.large, Sparsam, 1 Slot, 52.137 Dateien): anon 1.788,9 MiB gegen Rechnung 1.492,5 MiB (mit 235 MiB), +19,9 %.
- Mit dem neuen Slotwert 250 MiB: Rechnung 1.507,5 MiB, Grenze 1.658,3 MiB, nötiger Zuschlag **118,8 MiB** (vorher 133,8 MiB; der neue Slotwert deckt 15 MiB davon).
- Gleiche Box, gleiche Stufe, Anker S-T mit 5.000 Dateien: anon 1.512,0 MiB, Hauptprozess 1.291,6 MiB. Zwischen 5.000 und 52.137 Dateien wachsen anon um 276,9 MiB und der Hauptprozess um 279,5 MiB, also **rund 6,0 KiB je zusätzlicher Datei**, fast vollständig im Hauptprozess. Der Platz neben dem Hauptprozess bleibt bei 217,8 MiB je Slot (wie in den Teilkorpus-Zellen).
- Einschränkungen: nur zwei Datenpunkte (5.000 und 52.137), keine Wiederholung; die Hauptprozess-Reihe der S-voll deckt nur die ersten 11,9 h ab; Verlauf (linear oder sättigend) unbekannt; Ursache im Prozess (Tantivy-Reader/Segmente, sqlite-Cache, Mengen in Crawl/Reconcile, Queue-Zustand) nicht zerlegt.

**Mechanismus (Vorschlag)**
- Ein Posten im Hauptprozess-Anteil der Rechnung, linear in der Dateizahl des Index: `INDEX_MAIN_PROCESS_BYTES_PER_FILE x Dateien`.
- Koeffizient, zwei Lesarten:
  - knapp (Tragekriterium wie beim Slotwert, 1,10 Toleranz): 118,8 MiB / 52.137 = **2,4 KiB je Datei** (aufgerundet); bei 5.000 Dateien +11,7 MiB, trägt S-voll genau.
  - ohne Toleranzverbrauch (gemessenes Wachstum): **6 KiB je Datei**; bei 52.137 Dateien rund 305 MiB, bei 5.000 rund 29 MiB.
  - Empfehlung: 6 KiB, weil der Index nach der Messung weiter wächst und 2,4 KiB die Toleranz schon bei 52.137 Dateien voll ausschöpft.
- Dateizahl zur Laufzeit: `state.db` bzw. `index.searcher().num_docs` (bereits im Code genutzt, z. B. `worker/poller.py`, `index/rebuild.py`).

**Wo im Code er säße**
- `config.py`: neue Konstante mit Messquelle (Muster wie `OCR_SLOT_COST_BYTES`).
- `profile.py::_memory_term` / `resolve`: zusätzlicher `extra_bytes`-Anteil aus der Dateizahl (wie heute `FP32_EXTRA_BYTES`), damit Standard und Leistung auf großen Indizes weniger Slots rechnen. Die Dateizahl müsste wie `note_weights` über ein `note_index_files(n)` in den Snapshot kommen, mit fester Kadenz (z. B. je Runde oder je 1.000 Dateien), sonst springt die Slotzahl.
- Wichtig: **Sparsam hat keinen Speicherterm** (`_memory_term` gibt 0, Slots fest 1). Für S-voll selbst ändert der Term an der Slotzahl nichts. Für Sparsam wirkt er nur auf (a) die dokumentierte Rechnung und RAM-Anforderung (`docs/profiles.md`, Store-Anforderungstext) und (b) `12-slotkosten.py rechnung` als Abnahmewerkzeug.
- `probe.py` / `guard.py`: keine Änderung nötig; Probe und Wächter lesen den Headroom live, der Hauptprozesszuwachs ist dort schon enthalten.

**Tests**
- `test_config.py`: Pin der neuen Konstante.
- `test_profile.py`: Speicherterm mit 0, 5.000 und 52.137 Dateien (Rechenweg im Kommentar), Kadenz der Snapshot-Aktualisierung, kein Einfluss auf Sparsam (Sparsam-Pin bleibt).
- `test_probe*.py`, `test_guard.py`: unverändert grün als Gegenprobe.
- `test_v14_teilkorpus.py`: Rechnung mit Dateizahl; Messskript braucht dann ein Argument für die Dateizahl.
- `test_measurement_scripts.py`: Baumhash-Pin fortschreiben.

**Aufwand**
- Code und Tests ohne neue Messung: rund 0,5 bis 1 Tag.
- Empfohlene Vorstufe: eine Zerlegungsmessung des Hauptprozesses (smaps/tracemalloc bei 5.000, 20.000, 52.137 Dateien) auf einer Box, um Verlauf und Ursache zu klären: rund 1 Tag plus Boxkosten. Erst danach den Koeffizienten festschreiben.
- Owner-Entscheide nötig: Koeffizient (2,4 oder 6 KiB), mit oder ohne Vorstufe, Phase 29 oder Gap-Plan.

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: backend/src/findling/config.py (OCR_SLOT_COST_BYTES = 250 * MIB)
- FOUND: backend/tests/test_measurement_scripts.py (PACKAGE_TREE_HASH_TODAY 27db8b41...)
- FOUND: Commits 66bf7a44, 2f26d9fb, de177897
