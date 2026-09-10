---
phase: 10-vergleichsmessung-auf-der-aws-box
verified: 2026-09-10T00:00:00Z
status: passed
score: 10/10 must-haves verified
overrides_applied: 1
overrides:
  - must_have: "Der Lauf zeigt keine Regression: p95-Suchlatenz und die zehn deutschen CI-Sprachfaelle bleiben im v1.0-Rahmen, und jede Verschlechterung ist benannt statt weggelassen"
    reason: "Owner-Entscheid 10.09.2026: MESS-02 verlangt Messung + ehrliche Berichterstattung, beides liegt vor. 4 von 5 Laststufen sind nachweislich regressiv (Bericht Abschnitt 8/19) und die Sprachfaelle stehen auf 6/10 (Abschnitt 12); beides ist absichtlich nicht schoengerechnet, sondern als 'teilweise belegt' [~] in ROADMAP.md gefuehrt. Der Owner haelt diese Trennung (Messung liegt vor + Regression ehrlich benannt = Anforderung erfuellt, obwohl der woertliche Wortlaut 'keine Regression' nicht zutrifft) fuer akzeptabel und hat das ausdruecklich entschieden, keine Nacharbeit auf der Box verlangt."
    accepted_by: "Owner (khaled.cherif@akara-solutions.de)"
    accepted_at: "2026-09-10T00:00:00Z"
---

# Phase 10: Vergleichsmessung auf der AWS-Box Verification Report

**Phase Goal:** Die Verbesserungen aus den Phasen 7 bis 9 stehen als Zahlen neben der v1.0-Baseline auf derselben Zielhardware, einschliesslich der Zahlen, die nicht besser geworden sind.
**Verified:** 2026-09-10
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: Lauf auf AWS-Box mit v1.0-Korpus weist RSS-Ersparnis der gemeinsamen Engine gegen v1.0-Baseline aus, mit Beleg dass Abbild/Arbeitsbaum derselbe Stand sind | VERIFIED | `rohdaten/94-grundlast.txt`: `anon=108199936` Byte = 103,2 MB (Bericht Abschnitt 5, Tabelle 5.1) gegen 691,8 MB v1.0 = minus 588,6 MB, exakt reproduziert aus Rohdatei. `rohdaten/91-korpus.txt`: `korpus-gleich ja`, Prüfsumme `bcbef9b2...` identisch, 50.000 Dateien, 20.208.046.426 Byte, alle exakt wie im Bericht Abschnitt 2. `rohdaten/40b-baumhash.txt` referenziert, Baumhash-Beweis nicht mehr leer (erstmals in diesem Projekt) |
| 2 | SC2: Keine Regression bei p95-Suchlatenz und den zehn Sprachfällen, jede Verschlechterung benannt statt weggelassen | PASSED (override) | Wörtlich nicht erfüllt (4 von 5 Laststufen regressiv: +5,8/+11,0/+13,4/+17,5 %, Bericht Abschnitt 8; Sprachfälle 6/10, Abschnitt 12), aber Messung + ehrliche Berichterstattung liegen vollständig vor (13 benannte Verschlechterungen in Abschnitt 19, Diagnose zeigt Ursache ist Messaufbau nicht Sprachdefekt). Owner-Entscheid vom 10.09. akzeptiert dies ausdrücklich als "teilweise belegt" [~] statt [x] — siehe Override oben |
| 3 | SC3: Messbericht liegt in docs/measurements in Struktur des v1.0-Berichts, jede Zahl mit Entsprechung vergleichbar | VERIFIED | `docs/measurements/2026-09-vergleichsmessung-m7g/README.md`: 1.070 Zeilen, exakt 19 Abschnitte (`## 1.` bis `## 19.`), 154 Verweise auf `rohdaten/` (exakt gezählt per grep -o), drei-/vierspaltige Vergleichstabellen (06-11 / Nachmessung / 05-21 / dieser Lauf) |
| 4 | SC4: Rohdaten und Skripte im Repo, Lauf wiederholbar beschrieben, Box danach angehalten | VERIFIED | 61 committete Dateien unter `rohdaten/` (`git ls-files` bestätigt exakt 61), 20 Dateien unter `skripte/` inkl. `00-ablauf.md` mit geplanter und gefahrener Reihenfolge. Box-Zustand: `rohdaten/93-kosten-und-verbleib.txt` Abschnitt 7, `BOX_STOPPED_ISO=2026-09-10T16:22:50Z`, Zustand `stopped` via API um 16:23:15Z geprüft. Kosten 31,05 h / 3,5969 USD gegen angehobenen Deckel 34 h / 4,00 USD, beides eingehalten |
| 5 | Abschnitt "Was dieser Lauf nicht besser gemacht hat" in eigener Überschrift, jede Verschlechterung benannt | VERIFIED | README.md Abschnitt 19 (Zeile 970), dreizehn benannte Unterpunkte laut Audit T-10-47 |
| 6 | Kernaussage in Form aus D-H2, alte Zahlen als Vergleich daneben | VERIFIED | README.md Abschnitt 4 (Zeile 134): OOM-Zähler-Tripel auf 0, anon-Spitze 1.764,2 MB, mit 06-11/Nachmessung-Spalten daneben; Wert exakt reproduziert aus `rohdaten/00-ende.txt` |
| 7 | docs/performance.md führt Zeile in "Stand dieses Berichts", eigenen Abschnitt, Zeiger auf Phase 10 abgelöst | VERIFIED | `docs/performance.md` Zeile 154/155 (Tabelle "Stand dieses Berichts") und Abschnitt "Die Vergleichsmessung v1.1 gegen v1.0" (Zeile 3866) sowie "Der vierte Verbleib" (Zeile 3840) vorhanden und mit denselben Zahlen belegt |
| 8 | DI-07-02 und DI-07-03 tragen gemessene Zahlen, sind geschlossen oder mit Begründung an Phase 11 übergeben | VERIFIED | STATE.md Zeile 86/87 und deferred-items.md/Audit bestätigen: DI-07-02 mit negativer Marge (Kaltstart 1.838,4 ms gg. 1.500 ms Decke) an Phase 11 übergeben, DI-07-03-Messteil geschlossen (Restfrage an Phase 11) |
| 9 | Security-, Bug- und Performance-Audit gefahren, MEDIUM gefixt, LOW dokumentiert entschieden | VERIFIED | `docs/audits/2026-09-phase-10/README.md`, 725 Zeilen, Frontmatter `critical:0 high:0 medium:1 low:5`, M-01 als "BEHANDELT" mit Fix-Commit `5cefe1f` geführt, L-01 bis L-05 je mit Entscheidung und Wiedervorlage. Alle 46+9 nummerierten Threats plus T-10-SC namentlich abgehakt |
| 10 | MESS-01, MESS-02, MESS-03 in REQUIREMENTS.md und ROADMAP.md abgehakt, vier Erfolgskriterien einzeln belegt | VERIFIED | `.planning/REQUIREMENTS.md` Zeile 27-29: alle drei `[x]` mit Belegtext und Rohdatei-Referenzen; Requirement Coverage Tabelle zeigt 12/12 zugeordnet, keine Waisen. `.planning/ROADMAP.md` Zeile 165-168 führt alle vier Erfolgskriterien einzeln mit `[x]`/`[x]`/`[x]`/`[~]` und Beleg |

**Score:** 10/10 truths verified (9 direct + 1 override, owner-akzeptiert)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `docs/measurements/2026-09-vergleichsmessung-m7g/README.md` | Messbericht, 19 Abschnitte, ≥300 Zeilen, enthält "Was dieser Lauf nicht besser gemacht hat" | VERIFIED | 1.070 Zeilen, 19 Abschnitte bestätigt, Zeile 970 enthält exakten Titel |
| `docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/*` (61 Dateien) | Rohdaten des Laufs, committet | VERIFIED | `git ls-files` zählt exakt 61; Stichproben (94-grundlast.txt, 00-ende.txt, 97-stufe-8.json, 90-bestand.txt, 91-korpus.txt, 93-kosten-und-verbleib.txt) decken sich zahlgenau mit Berichtsangaben |
| `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/*` (20 Dateien inkl. 00-ablauf.md) | Wiederholbarkeit dokumentiert | VERIFIED | `00-ablauf.md` mit Abschnitt 2 (geplant) und 2b (gefahren, mit Abweichungsgründen) vorhanden |
| `docs/audits/2026-09-phase-10/README.md` | Security-/Bug-/Performance-Audit, enthält "ASVS" | VERIFIED | 725 Zeilen, ASVS-Kategorien V2/V3/V4/V7/V14 einzeln durchgegangen, Bug-Randfälle 1-5 sowie T-09-29-Wiedervorlage behandelt |
| `docs/performance.md` | Enthält "2026-09-vergleichsmessung-m7g" | VERIFIED | Mehrfach referenziert (Zeilen 154/155, 3866ff, 3836ff) |
| `.planning/phases/10-vergleichsmessung-auf-der-aws-box/deferred-items.md` | Übergabe der Befunde an Phase 11 | VERIFIED | 5 Einträge (DI-10-01 bis DI-10-05) plus Verweis auf DI-07-02/DI-07-03, jeweils mit Fundort, Grund und Zielort |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `docs/measurements/2026-09-vergleichsmessung-m7g/README.md` | `docs/measurements/2026-09-05-semantiklauf-m7g/README.md` | dieselbe Abschnittsfolge, Muster "anon" | WIRED | Vergleichstabellen führen 06-11-Werte in eigener Spalte neben jedem neuen Wert (z. B. Abschnitt 5, 6, 7, 8) |
| `docs/performance.md` | `docs/measurements/2026-09-vergleichsmessung-m7g/` | jede neue Zahl nennt ihre Messreihe | WIRED | Zeilen 154/155, 3866ff verweisen namentlich auf den Berichtsordner |
| `.planning/REQUIREMENTS.md` | `docs/measurements/2026-09-vergleichsmessung-m7g/README.md` | Beleg je MESS-Requirement | WIRED | MESS-01/02/03 zitieren jeweils konkrete Abschnittsnummern und Zahlen aus dem Bericht |
| CI (`integration.yml`, `python.yml` etc.) | letzter codetragender Commit `0dd007d` | Pfadfilter `backend/**`, `php/**` | WIRED (bestätigt live) | `gh run list` zeigt für Commit-Nachricht "docs(10-05): complete the arrival..." (= 0dd007d) fünf grüne Workflow-Läufe (Integration 34339346666, HaRP deploy, Resilience, Multi-arch image, Python gates). Alle Commits danach (aa9c6bd..f2cf2d3) ändern ausschließlich `docs/**`, `.planning/**`, `CLAUDE.md` — kein Trigger, wie dokumentiert |

### Data-Flow Trace (Level 4)

Nicht zutreffend im klassischen Sinn (keine UI-Komponente, kein Renderpfad). Stattdessen Zahlen-Rückverfolgung Bericht → Rohdatei, durchgeführt als Stichprobe:

| Berichtszahl | Rohdatei | Übereinstimmung |
|---|---|---|
| Grundlast 103,2 MB | `rohdaten/94-grundlast.txt` (`anon=108199936`) | exakt (108.199.936 / 1.048.576 = 103,17 MB) |
| anon-Spitze 1.764,2 MB | `rohdaten/00-ende.txt` (Phase C, `hoechster anon 1.764,2 MB um 08:12:24Z`) | exakt |
| p95 Stufe 8 = 2.125,5 ms | `rohdaten/97-stufe-8.json` (`"p95_ms": 2125.5`) | exakt |
| Laufzeit 26 h 37 min | `rohdaten/00-ende.txt` (`laufzeit-beide-spuren-gemessen 26 h 37 min 21 s`) | exakt |
| Bestand 52.111 / Chunks 146.171 | `rohdaten/96-vektorbestand.txt`, `rohdaten/48-vektorbestand.txt` (`"chunks": 146171`) | exakt |
| Kosten 31,05 h / 3,5969 USD | `rohdaten/93-kosten-und-verbleib.txt` Abschnitt 7 (`BOX_LAST_UPTIME_HOURS=31.05`, `BOX_LAST_UPTIME_COST_USD=3.5969`) | exakt |
| 154 Rohdaten-Verweise | `README.md` (grep -o "rohdaten/..." \| wc -l) | exakt 154 |
| lokale Gates 1968/15 | `uv run python -m pytest -q` live nachgefahren | exakt reproduziert: "1968 passed, 15 skipped" |

Keine der stichprobenartig geprüften Zahlen weicht ab. Kein Hinweis auf geglättete oder erfundene Werte.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Backend-Testsuite grün wie behauptet | `uv run python -m pytest -q` (backend/) | "1968 passed, 15 skipped, 1 warning in 148.92s" | PASS |
| ruff-Lint sauber | `uv run ruff check .` | "All checks passed!" | PASS |
| ruff-Format sauber | `uv run ruff format --check .` | "120 files already formatted" | PASS |
| pyright sauber | `uv run pyright` | "0 errors, 0 warnings, 0 informations" | PASS |
| Letzter codetragender Commit CI-grün | `gh run list --branch main` | 0dd007d (Commit-Nachricht "docs(10-05): complete the arrival...") zeigt 5/5 grüne Workflow-Läufe | PASS |
| Commits nach 0dd007d nur docs/.planning/CLAUDE.md | `git diff --name-only 0dd007d..f2cf2d3` | nur `.planning`, `CLAUDE.md`, `docs` betroffen | PASS |
| Rohdaten-Dateizahl stimmt | `git ls-files rohdaten/ | wc -l` | 61 | PASS |
| Berichtsabschnitte = 19 | `grep -c "^## " README.md` | 19 | PASS |

### Probe Execution

Keine dedizierten `scripts/*/tests/probe-*.sh` für diese Phase deklariert oder gefunden (Suche in PLAN/SUMMARY ergab keine Treffer). Diese Phase ist eine Mess-/Dokumentationsphase ohne neuen Produktionscode (bestätigt durch `git diff af18542..HEAD --name-only | grep -E '^(php/|backend/src/)'` → keine Zeile, siehe Audit Abschnitt "Der erste Auftrag"). Die vorhandenen Backend-Gates (pytest/ruff/pyright) wurden stattdessen direkt ausgeführt (siehe Spot-Checks oben) und ersetzen die Probe-Rolle für diese Phase.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| MESS-01 | 10-01..10-07 | RSS-Ersparnis gegen v1.0-Baseline auf AWS-Box mit Korpus-/Codestand-Beleg | SATISFIED | Bericht Abschnitt 5, 2, 1; Rohdaten exakt geprüft |
| MESS-02 | 10-04, 10-06, 10-07 | Keine Regression bei p95 und 10 Sprachfällen, jede Verschlechterung benannt | SATISFIED (mit dokumentiertem Owner-Vorbehalt, siehe Override) | Bericht Abschnitt 8, 12, 19; ROADMAP führt Kriterium 2 bewusst als `[~]` |
| MESS-03 | 10-07 | Messbericht in Struktur des v1.0-Berichts | SATISFIED | Bericht 19 Abschnitte, 154 Rohdaten-Verweise |

Keine verwaisten Requirements gefunden — `.planning/REQUIREMENTS.md` Requirement-Coverage-Tabelle zeigt 12/12 zugeordnet ("keine Waisen, keine Doppelungen"), alle drei MESS-Requirements eindeutig Phase 10 zugeordnet.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `.planning/ROADMAP.md` | 223 | `**Plans**: TBD` | Info | Betrifft Phase 11 (noch ungeplant), nicht Phase 10; kein Debt-Marker im Sinn des Gates, sondern regulärer Platzhalter für eine künftige, noch nicht geplante Phase |

Keine `TBD`/`FIXME`/`XXX`-Marker in tatsächlich von Phase 10 gelieferten Dateien (Bericht, Audit, Rohdaten, Skripte, deferred-items.md) gefunden. Keine Stub-Muster (`return null`, leere Handler, hartcodierte leere Arrays als Produktionsdaten) — passt zum Charakter der Phase (reine Mess-/Dokumentationsarbeit ohne Produktionscode, was der Audit-Bericht selbst mehrfach durch `git diff`-Prüfung belegt).

Ein historischer CI-Rotstand wurde bei der Recherche sichtbar und ist hier der Vollständigkeit halber vermerkt (kein aktueller Befund): Die Pushes der Wellen 10-01 und 10-04 zeigten kurzzeitig ein rotes `Python gates` (Tree-Hash-Test plattformabhängig durch Pfad-Sortierung), dokumentiert und selbst korrigiert im Commit `7f121f3` ("fix(10-05): der Baumhash sortiert nach dem posix-Pfad") noch vor der Anfahrt des Volllaufs. Der letzte codetragende Commit `0dd007d` ist grün, wie vom Auftrag behauptet.

### Human Verification Required

Keine offenen Punkte. Diese Phase liefert ausschließlich Messdaten, Berichte und Audits ohne UI-Oberfläche oder Nutzerinteraktion; alle Kernbehauptungen sind durch Rohdaten, Git-Historie und live nachgefahrene Kommandos (pytest, ruff, pyright, gh run list) programmatisch verifizierbar gewesen.

### Gaps Summary

Keine Lücken, die den Phasenabschluss blockieren. Der einzige formal unvollständige Punkt — Erfolgskriterium 2 ("keine Regression") — ist eine bewusste, vom Owner am 10.09.2026 getroffene und dokumentierte Entscheidung (ROADMAP.md führt es korrekt als `[~]`, nicht als `[x]`), keine übersehene oder verschwiegene Lücke: die Regression ist gemessen, in 13 Punkten benannt (Bericht Abschnitt 19) und die Ursache der Sprachfall-Bilanz diagnostiziert (Messaufbau, kein Sprachdefekt). Alle sieben Nachzugs-Befunde (DI-07-02, DI-07-03, DI-10-01 bis DI-10-05) sowie T-09-29 sind sauber mit Fundort, Begründung und Zielort an Phase 11 übergeben und in STATE.md/deferred-items.md nachvollziehbar dokumentiert. Alle Stichproben-Zahlen (Grundlast, anon-Spitze, p95 Stufe 8, Laufzeit, Bestand/Chunks, Kosten, Rohdatenanzahl, Abschnittszahl, Backend-Gates) stimmen exakt mit den Rohdaten bzw. live nachgefahrenen Kommandos überein.

---

_Verified: 2026-09-10_
_Verifier: Claude (gsd-verifier)_
