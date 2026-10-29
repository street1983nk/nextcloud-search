---
phase: 40-haertung-und-store-einreichung-1-6-0
plan: 04
subsystem: release
tags: [owner-acceptance, store-text, umlaut-audit, gate]
requires:
  - 40-03 (grüne Upgrade-Strecke)
  - 40-06 (Fix-Paket #36, Kandidat F, Nachtrag W-1/W-2)
provides:
  - 40-OWNER-VORLAGE.md (eine Runde, Empfehlung je Punkt)
  - 40-ABNAHME.md (GO: ja, Zitat, Datum, Kanal, Frage, Tag-Kopf)
  - docs/store-listing.md "# Entwurf v1.6.0 (Gesamttext), abgenommen am 29.10.2026"
  - scan_full_text_1_6_0 in backend/tests/test_store_metadata.py
affects:
  - 40-05 (Tag auf den Tag-Kopf, Einreichung)
key-files:
  created:
    - .planning/phases/40-haertung-und-store-einreichung-1-6-0/40-OWNER-VORLAGE.md
    - .planning/phases/40-haertung-und-store-einreichung-1-6-0/40-ABNAHME.md
  modified:
    - docs/store-listing.md
    - backend/tests/test_store_metadata.py
    - docs/runbook-messbox.md
    - docs/reconcile.md
    - docs/performance.md
    - docs/ocr.md
    - docs/l10n-dutch.md
    - docs/l10n-italian.md
    - docs/l10n-portuguese.md
decisions:
  - "Owner 29.10.2026: alle Punkte wie empfohlen (A1 bis A3, B, C, D1, E1/E2, G1 bis G3) und GO für Tag und Einreichung"
  - "F-40-06 in v1.7; historische Umlaute (docs/audits, docs/measurements) als eigener Doku-Commit nach dem Release; Unschärfe des Gateway-Satzes auf der v1.7-Merkliste"
metrics:
  completed: 2026-10-29
  tasks: 3
---

# Phase 40 Plan 04: Owner-Abnahme 1.6.0 Summary

Eine Owner-Runde über die Vorlage: drei Katalogsätze, der Gateway-Satz, Store-Text, Release-Notiz, F-40-06, Umlaut-Rest und Kandidat F alle wie empfohlen, GO für Tag v1.6.0 und Einreichung. Davor ein volles Umlaut-Audit mit 130 gefixten Stellen in docs/, danach der Gesamttext-Abschnitt mit eigenem Gate.

## Was gemacht wurde

- **Task 1:** Umlaut-Audit (info.xml beider Apps, 16 Kataloge, admin.php/admin.js, drei READMEs, CHANGELOG und weitere Wurzeldateien, alle 84 Markdown-Dateien unter docs/). Produkttexte und Kataloge sauber; 130 Stellen ASCII-Ersatz bzw. ss statt ß in sieben docs-Dateien als reine Zeichenkorrektur gefixt (00a63edf); rund 1800 Stellen in 39 historischen Berichten als Owner-Punkt E1. Vorlage 40-OWNER-VORLAGE.md (62334434).
- **Task 2:** Owner-Runde über den Koordinator; Antwort in 40-ABNAHME.md.
- **Task 3:** Gesamttext v1.6.0 in docs/store-listing.md mit den vier Sätzen en/de/fr und der Release-Notiz; Gate `scan_full_text_1_6_0` (Abschnitt, Abnahmedatum, de-Sätze zeichengleich mit php/l10n/de.json, Notiz endet mit der Full-Changelog-Zeile) plus sechs Selbsttests (91a0603f). Tag-Kopf festgelegt und belegt (40-ABNAHME.md).

## Commits

| Commit | Inhalt |
|---|---|
| 00a63edf | docs(40-04): real umlauts and sharp s in the German prose of the docs |
| 62334434 | docs(40-04): owner template for the 1.6.0 acceptance |
| 91a0603f | docs(40-04): owner acceptance of 1.6.0 and the full text |

## Verifikation

- 00a63edf: head_green "Python gates" "Security scans" Exit 0 (40856857305, 40856857515, Scorecard 40856857456); lokal 1248 Tests der doku-lesenden Dateien grün.
- 62334434: Security scans 40858675145 (Versuch 2 nach pypi.org-Read-Timeout im pip-audit-Schritt, Netzfehler) und Scorecard 40858675050 success.
- 91a0603f: test_store_metadata.py 117 passed lokal, ruff, ruff format, pyright latest 0 Fehler, vulture sauber, `-k tree_hash` grün; head_green über sechs Workflows Exit 0 (Python gates 40860811496, HaRP deploy 40860811483, Integration 40860811469, Resilience 40860811447, Multi-arch image 40860811482, Security scans 40860811457, Scorecard 40860811488), PHP gates per Zitat 40834773386. Tag-Kopf 91a0603f in 40-ABNAHME.md. Der erste Wartelauf im Hintergrund wurde vom Speicher-Reaper gestoppt, der Beleg ist der Vordergrundlauf danach.

## Deviations from Plan

- **Vorlage um Punkte erweitert:** G2 (Gateway-Satz als eigene Frage mit Alternative), G3 (schon geposteter #36-Kommentar), E1/E2 (historische Umlaute). Kein Umlaut-Fund wurde still korrigiert, wenn er Code, Test-Anker oder Zitat berührt.
- **Umlaut-Fixes vorab committed:** auf Anweisung des Koordinators als eigener Commit vor der Runde (reine Zeichenkorrektur), nicht als Vorlagenpunkt.
- **Gate prüft vier statt drei Sätze:** der Gateway-Satz aus 40-06 wurde in derselben Runde bestätigt und steht im Gesamttext mit.
- **Datum der Abnahme:** Uhrzeit ist die Übermittlung durch den Koordinator (11:48), die Owner-Antwort lag davor am selben Tag; im Protokoll vermerkt.

## Known Stubs

Keine.

## Self-Check: PASSED

- Dateien vorhanden: 40-OWNER-VORLAGE.md, 40-ABNAHME.md, Abschnitt Gesamttext in docs/store-listing.md.
- Commits auf origin/main: 00a63edf, 62334434, 91a0603f.
