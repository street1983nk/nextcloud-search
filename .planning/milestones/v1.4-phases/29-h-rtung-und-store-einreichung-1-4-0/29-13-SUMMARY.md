---
phase: 29-h-rtung-und-store-einreichung-1-4-0
plan: 13
subsystem: ci
tags: [push, ci-beweis, deploy-harp, upgrade, phpunit]
requires:
  - phase: 29-04
    provides: Merker SIGKILL-Einzelnachweis
  - phase: 29-11
    provides: Upgrade-Saat 1.3.2 auf 1.4.0
  - phase: 29-12
    provides: letzter lokaler Phasenstand
provides:
  - "Phasenstand auf origin/main (Kopf 7b8b4271), alle ausgelösten Workflows grün"
  - "CI-Beweis der Fremdinstallation und der Upgrade-Strecke 1.3.2 auf 1.4.0 mit Saat"
  - "erster PHPUnit-Beleg der PHP-Teile der Phase (Migration 1.4.0, ProfileController, AdminViewService)"
affects: [29-14]
tech-stack:
  added: []
  patterns: ["Zusicherungen an den Code-Konstanten festnageln (SCHEMA_VERSION per Test)"]
key-files:
  created:
    - docs/audits/2026-10-phase-29/README.md
  modified:
    - .github/workflows/deploy-harp.yml
    - backend/tests/test_upgrade_seed_steps.py
decisions:
  - "C-29-01: Store upgrade 3/5 verlangen die Sprachmarke de,en (1.3.2 stempelt ein frisches Verzeichnis), vorher und nachher gleich"
  - "C-29-02: Adressen aus dem Auditbericht entfernt statt Ausnahme im Gate"
  - "C-29-03: Store upgrade 6 Zusicherung 1 verlangt Schema 2 vorher und nachher statt einer Hebung; vom Owner mit dem Wort zu Push 3 mitgetragen"
metrics:
  duration: "ca. 85 min"
  completed: 2026-10-06
  tasks: 2
  files: 4
---

# Phase 29 Plan 13: Push und CI-Beweis Summary

Drei vom Owner einzeln freigegebene Pushes bringen den Phasenstand auf origin/main. Auf dem Kopf 7b8b4271 sind alle ausgelösten Workflows im ersten Attempt grün. Die Fremdinstallation und die Upgrade-Strecke 1.3.2 auf 1.4.0 mit Saat sind damit Ende zu Ende belegt. Drei Befunde zeigten sich erst im CI, alle drei lagen im Prüfgerüst, keiner im Produkt.

## Owner-Worte (wörtlich)

| Push | Frage | Antwort |
|---|---|---|
| 1, `57b83358..390360c3` | "Bestaetigst du den Push von main (57b83358..390360c3) nach origin?" | "ok" |
| 2, `390360c3..7130c4f0` | "Darf ich die 2 Commits 390360c3..7130c4f0 (8ae89572 Fix, 7130c4f0 Auditbericht) auf origin/main pushen?" | "ok" |
| 3, `7130c4f0..7b8b4271` | "Darf ich die 2 Commits 7130c4f0..7b8b4271 (7361b771 Fix Store upgrade 6, 7b8b4271 Auditbericht) auf origin/main pushen?" | "ok" (der Owner hat damit die geänderte Zusicherung C-29-03 gesehen und mitgetragen) |

Alle drei Worte hat der Orchestrator eingeholt und an mich weitergegeben. Vor jedem Push habe ich geprüft: Autor street1983nk, keine Co-Authored-By- oder Claude-Trailer, kein IPv4- und kein Token-Muster. Bei Push 1 gab es nur Treffer für die Loopback-Adresse, eine Adresse aus dem Dokumentationsnetz und den Plantext; bei Push 2 und 3 gar keine. Darüber hinaus gab es keine Pushes: kein Tag, kein Force, kein anderer Branch.

## CI-Beweis auf dem Kopf 7b8b4271

| Workflow | Lauf | Attempt | Ergebnis |
|---|---|---|---|
| Python gates | 37460204981 | 1 | success, 4723 passed, 14 skipped |
| Multi-arch image | 37460204900 | 1 | success (amd64, arm64) |
| Integration | 37460204996 | 1 | success |
| Resilience | 37460204909 | 1 | success |
| HaRP deploy | 37460204929 | 1 | success, vier Beine |
| PHP and store metadata gates | 37452332197 (auf 390360c3) | 1 | success, `OK (589 tests, 2106 assertions)`; auf den späteren Köpfen per Pfadfilter nicht ausgelöst, weil sich kein Pfad des Filters geändert hat |

Frühere Läufe: Push 1 auf 390360c3 hatte HaRP deploy 37452332294 rot (C-29-01), die anderen fünf grün (37452332061, 37452332197, 37452332135, 37452332015, 37452332174). Push 2 auf 7130c4f0 hatte Python 37455892343 (C-29-02) und HaRP 37455892381 (C-29-03) rot, die anderen grün (37455892371, 37455892246, 37455892221).

Zitate aus dem Upgrade-Bein (Job 112257592326), vollständig im Auditbericht:
- Store install 7: `content hit after 3 cron rounds, with nothing configured`
- Store upgrade 2b: `sown: a picture and a sidecar, both failed(corrupt) under v1.3.2, and the seed word finds nothing`
- Store upgrade 4: `the instance performed the app update: 1.3.2 to 1.4.0`
- Store upgrade 5: `unchanged  .marks.indexVersion = 1`, `the sidecar is skipped/system_file ...`, `the seed word finds exactly the file id 141 ...`, `unchanged  embedding mark = ...`, `the profile in force after the upgrade is economy`, `the recheck mark was absent before the upgrade and reads done after it`, `all eight assurances hold`
- Store upgrade 6: `all ten assurances hold`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] C-29-01: falsche Erwartung zur Sprachmarke von 1.3.2**
- **Gefunden in:** Task 2, HaRP 37452332294, Store upgrade 3
- **Problem:** Der Workflow erwartete aus Plan 29-11 eine leere Sprachmarke. 1.3.2 stempelt aber ein frisches Indexverzeichnis mit `de,en` (`stamp_a_new_directory`, M-19-05; am Tag v1.3.2 belegt).
- **Fix:** Schritt 3 verlangt `de,en`, Schritt 5 `de,en` vorher und den gleichen Wert nachher; den Test habe ich nachgezogen und um einen zweiten ergänzt.
- **Commit:** 8ae89572

**2. [Rule 1 - Bug] C-29-02: Adressmuster im eigenen Auditbericht**
- **Gefunden in:** Task 2, Python 37455892343, `test_public_artifacts.py[muster-der-umsetzung]`
- **Problem:** Der Bericht nannte die Treffer der Vorab-Suche wörtlich. Den lokalen Vollauf hatte ich gestartet, bevor der Bericht existierte.
- **Fix:** Umformuliert, keine Ausnahme im Gate.
- **Commit:** 7b8b4271

**3. [Rule 1 - Bug] C-29-03: Schemaschritt im Neuaufbau von Store upgrade 6**
- **Gefunden in:** Task 2, HaRP 37455892381
- **Problem:** Zusicherung 1 verlangte eine Hebung der Schemamarke. Das galt nur beim Start v1.2.0 (Schema 1); v1.3.2 und der Kopf tragen beide 2. Die übrigen neun Zusicherungen hielten.
- **Fix:** Zusicherung 1 verlangt jetzt 2 vorher und 2 nachher, ein Test bindet das an `findling.config.SCHEMA_VERSION`. Den Stempelnachweis trägt weiter Zusicherung 2 (Sprachmarke `de,en,es`). Das ist eine geänderte Zusicherung, keine abgeschwächte; der Owner hat sie mit dem Wort zu Push 3 mitgetragen.
- **Commit:** 7361b771

Weitere Abweichung: Das Owner-Wort zu Push 1 lag schon beim Start vor, deshalb hielt Task 1 nicht an. Jeder Fix-Push hatte sein eigenes Wort, wie der Plan es verlangt.

## Offen für 29-14

- **Namentlicher Linux-Beleg der beiden SIGKILL-Fälle** aus `test_slots_kill.py` (Merker aus 29-04): python.yml läuft mit `-q` ohne `-rs`. Lauf 37460204981 belegt die Suite insgesamt (4723 passed, 14 skipped), aber nicht die beiden Fälle mit Namen. Lokal gibt es kein Linux (Docker-Engine und WSL laufen nicht). Vorschlag: `-rs` oder `-v` für diese Datei in python.yml.
- Der Commit mit dieser SUMMARY und b10cec20 (Abschnitt Push 3 im Auditbericht) liegen nur lokal. Der nächste gedeckte Push nimmt sie mit.

## Known Stubs

Keine.

## Self-Check: PASSED

- docs/audits/2026-10-phase-29/README.md vorhanden
- Commits 8ae89572, 7130c4f0, 7361b771, 7b8b4271, b10cec20 im Log; origin/main = 7b8b4271
