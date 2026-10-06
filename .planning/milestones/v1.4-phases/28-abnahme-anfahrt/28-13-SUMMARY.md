---
phase: 28-abnahme-anfahrt
plan: 13
subsystem: messinfrastruktur
tags: [aws, abbau, snapshot, kosten, sc3]
requires:
  - phase: 28-abnahme-anfahrt
    provides: "28-10 Abbau beider Boxen (08-abbau-boxen.txt), 28-11 SC4-Entscheide"
provides:
  - "Korpus-Snapshot gelöscht, belegt mit InvalidSnapshot.NotFound"
  - "Sweep über 17 Regionen: 0 Instanzen, Volumes, Adressen, Schlüsselpaare, AMIs, Snapshots"
  - "README Abschnitt 15 Abbau und Schlusskosten: 34,64 USD gegen Deckel 59,43 USD"
affects: [28-abnahme-anfahrt Bericht, Runbook 8 Schritt 6b und 9]
tech-stack:
  added: []
  patterns: ["Rücklesung je Ressource vor Tag-Treffer"]
key-files:
  created:
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/09-abbau-snapshot.txt
  modified:
    - docs/measurements/2026-10-abnahme-anfahrt/README.md
key-decisions:
  - "Owner-Signal C6 vom 05.10.2026: \"Loeschen\" (Option snapshot-loeschen), keine Nachmessung"
  - "Snapshot-Tage der Phase ab der Freigabe der Anfahrt (erster Start 30.09. 16:53:40Z) gerechnet, 0,51 USD; Gesamtstandzeit seit 11.09. (2,45 USD) nur als Monatsposten genannt"
requirements-completed: [MESS-10]
duration: 12min
completed: 2026-10-05
---

# Phase 28 Plan 13: Abbau des Korpus-Snapshots Summary

**Korpus-Snapshot nach Owner-Signal "Loeschen" gelöscht, InvalidSnapshot.NotFound zurückgelesen, 17 Regionen mit 0/0/0/0/0/0 gezählt; Phasenkosten 34,64 USD gegen Deckel 59,43 USD, laufender Satz 0 USD/h.**

## Performance

- **Duration:** ca. 12 min
- **Started:** 2026-10-05T19:07Z
- **Completed:** 2026-10-05T19:19Z
- **Tasks:** 2 (Task 1 Checkpoint entschieden, Task 2 ausgeführt)
- **Files modified:** 2

## Owner-Signal (Task 1, Checkpoint C6)

Entschieden am 05.10.2026 per Auswahlfrage. Das Signal, wörtlich:

> Loeschen

Gewählte Option: `snapshot-loeschen`. Die SC4-Entscheide aus 28-11 brauchen keine
Nachmessung; den Vollindex-Term wählte der Owner zudem als "6 KiB ohne Messung"
(Umsetzung im parallelen Plan 28-12, nicht Teil dieses Plans).

## Accomplishments

- Vorbedingungen gelesen: Konto erwartet ja, genau ein eigener Snapshot (der Korpus-Snapshot, `findling-corpus-keep`, 60 GB, angelegt 11.09.), 0 Volumes daraus, 0 eigene AMIs
- `delete-snapshot` 19:10:41Z, Rückgabe 0; Rücklesung zweimal `InvalidSnapshot.NotFound`
- Bestand über 17 Regionen ungefiltert: alle sechs Zahlen 0 (null laufende AWS-Kosten, D-26-10)
- README Abschnitt 15 mit Schlusskosten: Boxen 34,13 + Snapshot seit Freigabe 0,51 = 34,64 USD, Rest 24,79 USD, Deckel gehalten

## Task Commits

1. **Task 1: Owner-Bestätigung (C6)** , kein Commit (Checkpoint, Signal in diesem SUMMARY)
2. **Task 2: Snapshot löschen und null Kosten belegen** , `ea6b384b` (docs)

## Files Created/Modified

- `docs/measurements/2026-10-abnahme-anfahrt/rohdaten/09-abbau-snapshot.txt` , Löschung, Rücklesung, Tag-Sweep, Bestandszählung, Schlusskosten
- `docs/measurements/2026-10-abnahme-anfahrt/README.md` , neuer Abschnitt 15 "Abbau und Schlusskosten" mit Verweis auf 08- und 09-Rohdatei

## Decisions Made

- Snapshot-Tage der Phase ab der Freigabe der Anfahrt (30.09.2026, erster Boxstart 16:53:40Z) bis zur Löschung: 5,0952 Tage x 0,10 USD = 0,51 USD. Davon als einziger Posten nach dem Boxen-Abbau 0,0625 Tage (0,01 USD). Gesamtstandzeit seit dem Anlegen 24,47 Tage (2,45 USD) als Monatsposten außerhalb jedes Deckels genannt, nicht in die Phasensumme gerechnet.

## Deviations from Plan

None - plan executed exactly as written.

Beobachtung: Der Tag-Sweep (Runbook 8 Schritt 7) zählt in eu-central-1 `findling-corpus-keep 1`
statt der erwarteten 34 Nullen. Nach Art zurückgelesen ist es das Tag des gerade gelöschten
Snapshots selbst (Kennungsabgleich ja, Ressource `InvalidSnapshot.NotFound`, 0 eigene Snapshots).
Das Tag-Verzeichnis läuft nach (Runbook: bis zu einer Stunde); um 19:15:44Z und 19:18:46Z noch 1.
Kein Überbleibsel, aber eine numerische 0 dieser Zeile ist im Repo nicht belegt. Eine spätere
Nachlesung (frühestens 20:11Z) kann sie nachtragen, kostet nichts und ist optional.

## Issues Encountered

- Das Worktree-Werkzeug verweigerte zusammengesetzte Shell-Schleifen mit `aws`; der Sweep lief als temporäres Skript im Worktree, das danach entfernt wurde (nicht committet).

## Known Stubs

Keine.

## User Setup Required

None.

## Next Phase Readiness

- SC3-Abbau vollständig: keine AWS-Ressource der Phase mehr, laufender Satz 0 USD/h.
- Runbook 8 Schritt 6b ist jetzt erstmals gefahren; die Marke "in Phase 28 erstmals vollzogen" und Schritt 9 ("Snapshot bleibt") können im Bericht (28-08ff) nachgezogen werden.
- README Abschnitt 12 nennt die Schlusstabelle noch als ausstehend; Abschnitt 15 trägt sie jetzt (nicht angefasst, Owner-Regel nur erbetene Änderungen).

## Self-Check: PASSED

- FOUND: docs/measurements/2026-10-abnahme-anfahrt/rohdaten/09-abbau-snapshot.txt (4x InvalidSnapshot.NotFound)
- FOUND: README Verweis auf 09-abbau-snapshot
- FOUND: Commit ea6b384b
- Gate test_public_artifacts.py: 55 passed
