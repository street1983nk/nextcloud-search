---
phase: 29-h-rtung-und-store-einreichung-1-4-0
verified: 2026-10-06T00:00:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
---

# Phase 29: Härtung und Store-Einreichung 1.4.0 Verification Report

**Phase Goal:** Findling 1.4.0 steht als signiertes App-Paar im Store, mit gehärteten Parallelpfaden und einer Anteils-Aussage im Owner-Wortlaut.
**Status:** passed. Re-verification: nein.

## Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Härtung deckt Rand-/Fehlerpfade ab, grün; Audit 0 CRIT / 0 HIGH, MEDIUM behoben, LOW entschieden | VERIFIED | docs/audits/2026-10-phase-29/README.md: 0C/0H/1 MEDIUM (F-29-01 behoben, mit Test) / 4 LOW (2 behoben, 2 bewusst so, in deferred-items.md); haertungsmatrix.md vorhanden; lokal `test_launch_hardening.py` grün; Python gates 37467788135 success auf 99326ae2 (gh bestätigt); SIGKILL-Fälle namentlich belegt |
| 2 | Fremdinstallation + Upgrade 1.3.2 auf 1.4.0 grün; Bestand landet in Sparsam ohne Neu-Einbettung | VERIFIED | HaRP deploy 37460204929 grün, alle vier Beine; Store install 0-7, Store upgrade 0-6, "profile in force ... economy", "unchanged embedding mark", `.marks.indexVersion` unverändert. Drei CI-Rotbefunde (C-29-01..03) offen dokumentiert und mit Fix und Owner-Wort geschlossen, keine Abschwächung |
| 3 | Beide Apps 1.4.0 (K6), signiert, Submission 2x HTTP 201 | VERIFIED | `backend/appinfo/info.xml` und `php/appinfo/info.xml` tragen `<version>1.4.0</version>`; Release 37470623070 success (gh), Release v1.4.0 mit genau 4 Assets (529.651 B, 33.663 B, je .sig 684 B); Log von 37473805519 zeigt wörtlich `release findling v1.4.0: HTTP 201` und `release findling_backend v1.4.0: HTTP 201`; live abgerufen: beide App-Seiten verlinken v1.4.0 |
| 4 | Store-Texte gate-konform, Anteils-Satz im Owner-Wortlaut (D-24-04), Owner-Abnahme vor Abgabe | VERIFIED | `SHARE_SENTENCE_DE` in test_store_metadata.py identisch mit D-24-04 in 24-CONTEXT.md (Wortvergleich); Satz in beiden info.xml; Gate-Tests (store_metadata, lockstep, launch_hardening) lokal 110 passed; Abnahme "ok abgenommen" (29-02) und "abgenommen du kannst weiter" (29-14) vor Tag/Einreichung (Tag-Wort "go") |

## Requirements Coverage

| Requirement | Status | Evidence |
|---|---|---|
| REL-04 | SATISFIED | REQUIREMENTS.md Zeile 43 [x] und Traceability Zeile 79 Complete; alle Bestandteile (gleiche Version beider Apps, Härtung + Audit, gate-konforme Texte, Anteils-Satz im Owner-Wort, Abnahme) oben belegt. Keine verwaisten Phase-29-IDs gefunden |

## Anti-Patterns / Probes

Keine Blocker gefunden. Bekannte Verschiebungen sind bewusst und dokumentiert: vier Box-gebundene Feldbelege (D-29-11, Owner-Entscheid, im Store-Text nicht versprochen), F-29-03/F-29-05 LOW, Pillow-TIFF-Orientierung, Float-TIFF, #21/#22 (deferred-items.md). Keine TBD/FIXME-Prüfung am Code im Detail wiederholt; Gate-Suiten laufen grün.

## Human Verification Required

Keine. Owner-Abnahmen sind wörtlich dokumentiert; die UI-Abnahme erfolgte bereits gemeinsam per Playwright (29-14).

## Hinweise (Warnungen, nicht blockierend)

- Box-Feldbelege (4 Punkte) bleiben bis zur nächsten Box-Anfahrt offen (D-29-11), Vorbehalt im Requirement vermerkt.
- Nicht eigenständig erneut erhoben: Signaturprüfung der Archive (openssl) und Docker-Manifest; Verifiziert wurden Läufe, Assets, Größen, Submission-Log und Live-App-Seiten.
- Die Phase-28-Restposition T-28-69 betrifft nicht Phase 29.
