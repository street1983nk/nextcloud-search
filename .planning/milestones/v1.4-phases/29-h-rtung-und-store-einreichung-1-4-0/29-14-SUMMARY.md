---
phase: 29-h-rtung-und-store-einreichung-1-4-0
plan: 14
---

# Phase 29 Plan 14: Härtung abschließen Summary

Phasenaudit über alle Phase-29-Änderungen (Security/Bugs/Performance), Befundfixe,
SIGKILL-Namensbeleg vorbereitet, deferred-items fortgeschrieben, Owner-Abnahme der
Launch-Härtung per gemeinsamer Playwright-Runde.

## Ergebnis

- **Audit: 0 CRIT / 0 HIGH / 1 MEDIUM / 4 LOW.** Bericht in
  `docs/audits/2026-10-phase-29/README.md` (Abschnitt "Phasenaudit"), jede Mitigation
  T-29-01 bis T-29-47 mit Datei:Zeile oder Testname belegt.
  - F-29-01 MEDIUM (DoS, quadratische Schritte im SF0-Patch bei präparierten
    Mehrseiten-TIFFs): behoben (64992430), eigener Test war vor dem Fix rot.
  - F-29-02 LOW (falsche Fehlerklassen im Migrations-Kommentar): behoben.
  - F-29-03 LOW (Dateicache mit falscher Größe endet als repeatedly_stuck): bewusst so,
    folgt aus D-29-04; 1.4.1-Kandidat in deferred-items.
  - F-29-04 LOW (CFB-Kommentar vs. Ausnahmeliste): bewusst so, Liste deckt alle
    erreichbaren Ausnahmen.
  - F-29-05 LOW (Nachprüfung einmalig in einer Runde, bei budachst 43 Aufrufe,
    unterbrechbar mit Cursor): bewusst so.
- **Härtungsmatrix erneut gefahren:** 37 passed, 2 skipped (Linux-SIGKILL-Fälle,
  lokal Windows), keine xfail-Marken, kein Befund.
- **SIGKILL-Namensbeleg:** python.yml hat einen eigenen Schritt
  `pytest -v -rs tests/test_slots_kill.py`, Gesamtlauf mit `-rs`. Laufnummer kommt
  mit dem Push nach dieser Abnahme in den Bericht.
- **Pins:** Paket 38dab326... auf 3be00d8f... (73 Dateien), PHP 49ed9359... auf
  0763e839... (90 Dateien).
- **Gates:** Volle Suite 4713 passed / 25 skipped (nach Umformulierung des eigenen
  Berichts wegen des Docs-Gates), ruff, ruff format, pyright (latest), vulture sauber.

## Owner-Abnahme (Task 3)

Gemeinsame Playwright-Runde am 06.10.2026 auf der Dev-Instanz (Port 8090, App und
Backend beide 1.4.0, Backend als Host-Prozess aus den Quellen über
scripts/dev/register-exapp.sh). Live mit echten Testdateien belegt:

| Prüfpunkt | Beleg |
|---|---|
| System- oder Hilfsdatei / System or helper file | `._abnahme-29.docx` + `~$abnahme-29.docx` hochgeladen, beide skipped(system_file), Zeile mit Abhilfe und Beispielpfaden in DE und EN |
| Old Office format under a new name | CFB-Datei (Workbook-Stream) als .xlsx, skipped(legacy_format) |
| Image variant that cannot be read | SampleFormat-3-TIFF, skipped(unsupported_variant) |
| Error class auf der Diagnosekarte | kaputte .xlsx, failed(corrupt), Karte zeigt "Error class: zipfile.BadZipFile" |
| occ findling:diagnose zeigt "error class" | belegt mit Wert (zipfile.BadZipFile) und leer ("-") |

Zusatzbeleg: der K6-Versionswächter griff live (Banner bei App 1.4.0 gegen
Backend 1.3.0, Suche bewusst leer; nach dem Angleich weg).

**Owner-Signal wörtlich: "abgenommen du kannst weiter" (06.10.2026)**, auf die
Vorlage mit Audit-Stand, Playwright-Tabelle, deferred-items (Box-Belege D-29-11,
Annahme A5, ocr_failed ohne Nachprüfung, F-29-03, F-29-05) und der Push-Frage zu
den Audit-Commits `1c5c9995..3fd8349b`. Das Signal deckt die Härtungsabnahme, die
deferred-items und den beschriebenen Push samt der Abschluss-Doku dieses Plans.

## Commits

- 9f9ea48e docs(29-14): Phasenaudit und Matrix-Lauf
- 64992430 fix(29-14): F-29-01 und F-29-02, Pins nachgezogen
- c321e34e ci(29-14): SIGKILL-Fälle namentlich (-rs)
- b56118b9 docs(29-14): deferred-items, Wortbereinigung Testkopf
- (dieser Commit) docs(29-14): Owner-Abnahme und SUMMARY

## Offene Punkte

- Laufnummer des SIGKILL-Schritts nach dem Push in den Bericht eintragen (29-15/16
  oder direkt nach dem CI-Lauf).
- Die Abnahme-Testdateien liegen nur auf der lokalen Dev-Instanz.
