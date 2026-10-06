---
phase: 28-abnahme-anfahrt
verified: 2026-10-06T00:00:00Z
status: passed
score: 7/7 must-haves verified
overrides_applied: 0
gaps: []
---

# Phase 28: Abnahme-Anfahrt Verification Report

**Phase Goal:** RAM-Messung je Profilstufe am gebauten Produkt auf echter Hardware, Deckel vorab freigegeben (MESS-10).
**Status:** passed (nachgeholte Verifikation vor Milestone-Close v1.4)
**Re-verification:** Nein, initial

## Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Deckel vorab freigegeben, vor Boxstart | VERIFIED | README: "Anfahrt freigegeben: 30.09.2026, Deckel 119,82 h / 59,43 USD"; `rohdaten/02-rechenblatt-freigabe.txt` vorhanden; erster Start 2026-09-30T16:53Z |
| 2 | 18-Zellen-Matrix komplett gemessen, alle rc 0 | VERIFIED | `auswertung.txt` hat 18 Zellenzeilen (1,2,5-9,11-21); je Zelle-Ordner `10-zelle.txt`; Kettenlogs enden je Box mit `zelle-ende ... rueckgabe 0`; Abbruchlaeufe liegen separat (`-abbruch<code>`) und gehen in keine Zahl ein |
| 3 | Zaehltore exakt 5000 | VERIFIED | alle 17 Teilkorpus-Zellen: `zaehltor bestanden 5000`; S-voll (Vollkorpus) hat `indexed 52137` am Ende, ohne Zaehltor 5000 (richtig) |
| 4 | RAM-Spitze je Profilstufe/Box, SC4 bewertet, Owner-Entscheide dokumentiert | VERIFIED | README Abschn. 4, performance.md "Abnahme-Anfahrt v1.4": 12 getragen, 6 nicht getragen (11,16,17,20,21,S-voll); Owner-Signal 05.10. woertlich ("je-fall ... wert=250 MiB, store=kein Fall"); C1 743,9 MB innerhalb Band 715,6 bis 744,8 (Store-Zahl 730,2 bleibt) |
| 5 | Boxen + Snapshot abgebaut, 0 USD/h, Sweep 17 Regionen | VERIFIED | `08-abbau-boxen.txt`: 17 Regionen 0 Instanzen/Volumes/Adressen/Schluessel/AMIs; `09-abbau-snapshot.txt`: 0 eigene Snapshots in 17 Regionen, Nachlesung 19:52Z 0/0, "laufender Satz 0 USD/h" |
| 6 | Kosten im Deckel | VERIFIED | Boxen 34,13 USD + Snapshot 0,51 = 34,64 USD gegen 59,43 USD (58,3 %); Sicherheitsstopp 71,32 nie erreicht |
| 7 | performance.md-Kapitel + OCR_SLOT_COST_BYTES 250 MiB mit Schutznetz | VERIFIED | performance.md Z. 4864-4988 (RAM, fp32, C1, Slotkosten, Entscheide); `config.py:896 OCR_SLOT_COST_BYTES = 250 * MIB`; Test `test_config.py:1294` pinnt 262_144_000; `pytest test_config/test_guard/test_probe` (PYTHONUTF8=1): 339 passed |

**Score:** 7/7

## Requirements Coverage

| Requirement | Plaene | Status | Evidence |
|-------------|--------|--------|----------|
| MESS-10 | 28-01..28-14 | SATISFIED | Truths 1-7. Hinweis: `.planning/REQUIREMENTS.md` fuehrt MESS-10 noch als `[ ]`/"Pending" (Zeile 42, 78); Bookkeeping beim Milestone-Close auf erledigt setzen |

## Anti-Patterns / Befunde (nicht blockierend)

| Datei | Befund | Schwere |
|-------|--------|---------|
| `docs/performance.md` Z. 4888, README Z. 350/364 | nennt Zwischenstand 34,09 USD; Endstand 34,13 (Boxen) / 34,64 (Phase) steht in README Z. 436-438 und `rohdaten/90-kosten.txt`. Beide im Deckel, nur nicht konsistent | Info |
| S-voll | anon-Spitze +19,9 % ueber Rechnung, Vollindex-Term (6 KiB/Datei, `MAIN_PROCESS_PER_FILE_BYTES`) per Quick 261005-vit gebaut; Laufzeit-Verdrahtung bewusst offen (28-14 "ehrlich offene Punkte", Phase-29-Kandidat) | Info (dokumentierte Akzeptanz) |

## Bewusst offene Punkte (dokumentierte Akzeptanzen, keine Gaps)

Feldbelege D-29-11, AR-28-01..05, T-28-69 (laut 28-SECURITY.md per "ok weiter" geschlossen, SECURED 71/71, `threats_open: 0`), 250 MiB ohne Feldlauf.

## Human Verification

Keine offenen Punkte. Owner-Abnahme 06.10.2026 woertlich "approved" (28-14-SUMMARY, Abschnitt Owner-Abnahme).

_Verifier: Claude (gsd-verifier)_
