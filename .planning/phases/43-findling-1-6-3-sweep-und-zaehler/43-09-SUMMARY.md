---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 09
subsystem: audit (security, bugs, performance)
tags: [audit, 1.6.3, coverage, doc-key, sweep, bounded-stream]
requires:
  - 43-08 (Release-Stand d9f8a65d, letzter gepushter Code-Kopf)
  - 43-E2E.md (Läufe 42503731869 und 42516315101, PHPUnit 1140 OK)
provides:
  - 43-AUDIT.md mit audited_head 37b518d6 (0 CRIT / 0 HIGH / 0 MEDIUM offen / 2 LOW entschieden / 4 INFO)
  - backend/tests/test_phase43_audit.py (15 Proben, je Hypothese eine)
  - Fix F-43A-01 (COVERAGE_SYNC_CEILING 25.000) als lokaler Commit 37b518d6
affects:
  - 43-10 (Testbuild gegen audited_head)
  - 43-12 (Owner-Runde: F-43A-01-Hinweis, D-43-15/K6)
  - Task 2/3 dieses Plans (Owner-Freigabe, Push, head_green, E2E-Beleg)
key-files:
  created:
    - backend/tests/test_phase43_audit.py
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-AUDIT.md
  modified:
    - backend/src/findling/api/coverage.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "F-43A-01 (MEDIUM) per TDD gefixt statt gemeldet: Deckel-Senkung ist kein Architektur-Schnitt, der Hintergrundpfad ist der seit 43-04 geprüfte Weg"
  - "F-43A-02 und F-43A-03 (LOW) akzeptiert mit Begründung, keine Owner-LOWs"
  - "audited_head auf den Fix-Kopf 37b518d6 gezogen, Nachtrag über genau den Fix-Delta im Bericht"
metrics:
  duration: "ca. 30 min Messung + Proben, gesamt rund 2,5 h lokale Arbeit"
  completed: 2026-11-08
  tasks: 1 von 3 (Task 2 Checkpoint und Task 3 Push/CI stehen aus)
  commits: 2
---

# Phase 43 Plan 09: Audit 1.6.3 Summary

Audit über den ganzen Delta v1.6.2..d9f8a65d (53 Dateien, 6.363 Zeilen) mit 15
gefahrenen Proben und einer Messung: ein MEDIUM gefunden und lokal per TDD
gefixt (F-43A-01: der synchrone Zähldeckel von POST /coverage lag mit 100.000
Zeilen über dem 2-s-Admin-Timeout der Companion, auf ARM fiel die Seite ab etwa
56.000 Zeilen dauerhaft und wortlos auf die 1.6.2-Zahl zurück; jetzt 25.000),
zwei LOW entschieden (akzeptiert), vier INFO dokumentiert. audited_head =
37b518d6. NUR lokale Arbeit: Push und CI-Beleg warten auf die Owner-Freigabe
(Task 2, Checkpoint beim Koordinator).

## Commits

| Hash | Nachricht |
|------|-----------|
| 37b518d6 | fix(43-09): the coverage sync ceiling keeps a slow box under the admin timeout |
| e8c052e3 | docs(43-09): audit of the 1.6.3 delta |

Autor street1983nk <k.cherif@outlook.de>, ohne Trailer, keine closes-Wörter
(je geprüft: `git log -1 --format=%B | grep -icE ... = 0`).

## Task 1: Audit mit Proben, Bericht, Fix ab MEDIUM

- Umfang mechanisch belegt: `git diff --stat v1.6.2..d9f8a65d` über die zehn
  Pfadgruppen des Plans, 53 Dateien, jede mit Urteil in 43-AUDIT.md
  (backend/docker ohne Delta); Diff jeder Datei einzeln gelesen, die zwei
  großen Harness-Skripte zusätzlich mit Muster-Greps (curl/sudo/URLs).
- Pflicht-Hypothesen alle gefahren: 15 neue Proben in test_phase43_audit.py
  (Routen-Deklaration gegen gemountete Pfade samt Groß-/Kleinschreibung,
  strict-Body-Grenzen, Gate-Momentaufnahme, Pause im Lückenfenster, Stempel
  ohne Abwesende, Uhrsprung, D-43-11-Doppelzählung, 31.571-Backlog in Bändern,
  Single-Flight nach unerwartetem Fehler, PHP-Attribute, Grenzen-Parität,
  Deckel gegen Timeout); der Rest über benannte bestehende Tests (lokal
  mitgefahren: 748 + 804 Tests grün) und CI-Belege (PHPUnit 1140 OK, E2E
  fünf Beine, HaRP-Zusicherungen 14-18).
- Messung P-b (Scratch, 190.000 Zeilen): 102.311 Zeilen in 0,738 s (x86, best
  of 3), mal Faktor 5 für ARM = 3,69 s gegen 2,0 s Timeout; Zeilen unter 2 s
  bei Faktor 5: rund 55.400. Backlog-Probe: 31.571 Löschaufträge in 169
  Bändern zu höchstens 200, 0,03 s gegen die Fake-Queue.
- Fix F-43A-01 per TDD: Probe zuerst rot gegen 100.000 gesehen, dann
  COVERAGE_SYNC_CEILING = 25.000 mit Begründung im Code, Baumhash nachgezogen
  (75212e53, Rezept und unabhängige Pipeline gleich, Positivkontrolle über den
  Baum von d9f8a65d ergibt den alten Hash 3d704f65).
- Gates vor jedem Commit: ruff check, ruff format --check (255 Dateien),
  pyright latest 0 errors, vulture 80 Exit 0; test_phase43_audit.py dreimal
  15 passed.

## Befunde (Kurzfassung, Details in 43-AUDIT.md)

| ID | Schwere | Entscheid |
|---|---|---|
| F-43A-01 | MEDIUM | gefixt (Commit 37b518d6) |
| F-43A-02 (Sweep-Stempel in der Zukunft nach Uhrsprung) | LOW | akzeptiert, dieselbe Kadenzregel wie der Walk |
| F-43A-03 (eine Warnzeile je Overview-Abruf im Mischbetrieb) | LOW | akzeptiert, vorübergehend und Diagnose zum sichtbaren Banner |
| I-43A-01 bis I-43A-04 | INFO | dokumentierte Absichten/Randlagen, kein Handlungsbedarf |

## Deviations from Plan

1. **[Rule 1] MEDIUM F-43A-01 gefixt statt nur berichtet:** der Plan sieht das
   ausdrücklich vor (MEDIUM hier per TDD fixen); audited_head auf den neuen
   Kopf gezogen, Nachtrag über den Fix-Delta im Bericht.
2. **Bewusst nicht ausgeführt (Auftrag des Koordinators):** Push, Dispatch,
   head_green.sh, e2e_run-Zeile, FREIGABEN-Zeilen; Task 2 ist ein blocking
   Checkpoint, Task 3 läuft erst nach "Entscheid: ja". STATE.md und ROADMAP.md
   wie beauftragt nicht angefasst.
3. **PHP-Messungen (Validierungskosten W-d, N1 auf MySQL/PG) nicht lokal
   gefahren:** kein lokales PHP/Docker (Vorgabe 43-02, wie 43-15); stattdessen
   Durchsicht, die 43-04/43-05-Messungen (1,40 MB bei 50.000, Bänder 1000) und
   die grünen CI-Beine als Beleg, im Bericht je Hypothese ausgewiesen.

## Known Stubs

Keine. Der Bericht trägt bewusst noch keine `e2e_run:`-Zeile und keinen
Abschnitt "Läufe auf audited_head": beides ist per Plan Inhalt von Task 3 nach
der Freigabe.

## Threat Flags

Keine neue Angriffsfläche: der Fix ändert eine Konstante, keine Route, keinen
Schlüssel, kein Schema. T-43-27 und T-43-28 im Bericht als umgesetzt belegt.

## Offen (Checkpoint beim Koordinator, Task 2 und 3)

- Owner-Frage: Push von Audit-Bericht, Proben und Fix-Commit auf main
  (git log origin/main..HEAD unten), plus Dispatch "Coverage end to end",
  weil ein Code-Fix dabei ist (je eigene Freigabezeile in 43-FREIGABEN.md).
- Nach Freigabe: `git pull --rebase`, Push, head_green.sh über die sieben
  Workflows auf audited_head, `gh workflow run coverage-e2e.yml --ref main`,
  Lauf-ID als `e2e_run:` und Abschnitt "Läufe auf audited_head" in 43-AUDIT.md.

`git log --oneline origin/main..HEAD` (Stand dieser SUMMARY):

```
e8c052e3 docs(43-09): audit of the 1.6.3 delta
37b518d6 fix(43-09): the coverage sync ceiling keeps a slow box under the admin timeout
12f00467 docs(43-08): state, phase 43 plan 08 complete
800d58e4 docs(43-08): second green end to end run on the 1.6.3 head
9f6ddc79 docs(43-08): coordinator note, push green and the upgrade proof line
```

## Self-Check: PASSED

- Commits 37b518d6 und e8c052e3 vorhanden, Autor street1983nk
  <k.cherif@outlook.de>, ohne Trailer, closes-Grep 0.
- 43-AUDIT.md mit `audited_head: 37b518d6...` (40 Hex), test_phase43_audit.py
  mit 15 `def test_`, Gates grün, Proben dreimal grün.
