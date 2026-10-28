---
phase: 35-stretch-aehnliche-dokumente-und-spikes
plan: 03
subsystem: messung-str02
tags: [testset, semantik, granite, entscheidungsregel, checkpoint]
status: komplett (Owner-Abnahme 19.10.2026)
requires: []
provides:
  - "testdata/semantik/de.jsonl mit 120 Fällen (de-01 bis de-42 byte-gleich)"
  - "MINIMUM_CASES de = 120"
  - "docs/measurements/2026-10-granite-vergleich/README.md, Abschnitte 1 bis 7 (Regel vor der Messung)"
affects: [35-04, 35-09, 35-10, 35-11]
key-files:
  created:
    - docs/measurements/2026-10-granite-vergleich/README.md
  modified:
    - testdata/semantik/de.jsonl
    - testdata/semantik/README.md
    - backend/tests/test_model_quality.py
decisions:
  - "Stichprobe Durchsatz: 500 Dokumente, random.Random(\"granite-35\").sample über bytewise sortierte Pfade des phase5-Lastkorpus"
  - "Kostendeckel-Vorschlag: 4 h Posten x 1,30 = 5,2 h, 0,60 USD netto (m7g.large 0,0978 USD/h, gelesen 19.10.2026 16:20Z)"
  - "int8-Fenster granite: --min-bytes 85000000 --max-bytes 110000000"
metrics:
  completed: 2026-10-19
  tasks_done: 3
  tasks_total: 3
---

# Phase 35 Plan 03: Messvorbereitung granite (STR-02) Summary

Deutsches Testset von 42 auf 120 Paare erweitert (Untergrenze im Test gesichert) und die Entscheidungsregel samt Methode des granite-Berichts vor jeder Messung committet; der Owner hat beides am 19.10.2026 ohne Änderung abgenommen.

## Stand

| Task | Name | Commit | Status |
|---|---|---|---|
| 1 | Deutsches Testset auf 120 Paare | f8ca7296 | erledigt |
| 2 | Entscheidungsregel und Methode | 3d1a41b7 | erledigt |
| 3 | Owner-Abnahme | 43e5adac | erledigt: `Owner-Abnahme: 19.10.2026, "Regel abgenommen"`, keine Änderungen |

## Task 3

Owner-Antwort (über den Orchestrator): "Regel abgenommen". Regel (a) bis (d), Methode, Stichprobe (500 Dokumente, Seed `granite-35`), Kostendeckel (5,2 h, 0,60 USD) und das 120er-Testset gelten wie vorgelegt. Zeile am Zeilenanfang in Abschnitt 7 eingetragen; Prüfung `grep -E "^Owner-Abnahme: ..."` grün, `rohdaten/` existiert nicht. Doku-Gates (`test_public_artifacts`, `test_measurement_scripts`, `test_model_quality`) 568 passed. Die Regel ist eingefroren.

## Task 1: Belege

- **TDD rot vor dem Anhängen** (`"de": 120`, 42 Fälle):
  `FAILED tests/test_model_quality.py::test_each_language_carries_at_least_the_cases_its_verdict_needs[de]`,
  `AssertionError: assert 42 >= 120`, `1 failed, 35 passed`.
- **Danach grün:** volle Suite `5761 passed, 264 skipped` (12 min, seriell), ruff check, ruff format --check, pyright (0 errors), vulture, reuse lint grün.
- **Byte-Gleichheit Zeilen 1 bis 42** (committete Blobs, LF): `git show a88de31f:... | head -42 | sha256sum` = `git show HEAD:... | head -42 | sha256sum` = `ab828c24...bfd07d`. Arbeitskopie (CRLF) vor und nach dem Anhängen ebenfalls gleich (`2781558b...c28f`).
- **Stamm-Brücken, unabhängig vom Gate:** eigene Prüfung über alle 78 neuen Fälle (gefalteter Präfix ab 5 Zeichen oder Wort-in-Wort ab 4), danach Handdurchsicht. Zwei echte Brücken gefunden und umgeschrieben, im `note` vermerkt: de-50 (Schein gegen Bescheinigung, jetzt "medizinischer Nachweis"), de-86 (spät gegen Verspätung, Anfrage jetzt "nach Plan"). Drei Fehlalarme ohne Änderung (de-55 verschwunden/verschlossen, de-93 lange/verlangen, de-99 Unterstützung/Unterkunft).
- **Handstichprobe zehn Fälle** (Ziehung wie README Abschnitt 7): de-99, de-79, de-57, de-90, de-83, de-72, de-116, de-111, de-85, de-54; keine Stamm-Brücke.
- Repo-weite Suche nach "42 Fälle/42 cases/204 Paare/de.jsonl": nur historische Messberichte und Messergebnisse, keine Gegenwartsbehauptung nachzuziehen.

## Task 2

README mit Abschnitten 1 (Regel a bis d: Vorzeichentest einseitig 0,05; 5 Prozent MRR; 2 GiB minus höchstens 256 MiB Abstandsverlust; 1,5 s kalt), 2 (sha256 der drei Dateien: de `700c74d2...`, en `95173d6e...`, fr `d5ef6d1c...`; Stichprobe 500/Seed `granite-35`), 3 (Revision `835ad140...`, fp32-sha256, Fenster 85 bis 110 Mio. Byte, IBM-int8 nur Vergleich, Lizenz), 4 (Kommandozeilen, Positivkontrolle mean, 512/1024, Pad-Token, amd64 seriell, arm64 `mem=4G`), 5 (Pflichtpunkte 10.10.), 6 (Rechenblatt), 7 (Platzhalter Owner-Abnahme). `rohdaten/` existiert nicht.

## Deviations from Plan

1. **[Rule 3] Push und CI-Block nicht ausgeführt.** Paralleler Worktree-Lauf; Push auf origin main und CI-Beobachtung übernimmt der Orchestrator nach dem Merge. CI-Laufnummern stehen deshalb noch aus.
2. **[Rule 1] Fund des Gates `schluesselwort-mit-wert`** (`test_public_artifacts.py`) im ersten README-Entwurf ("Pad-Token:" wurde als Schlüsselwort mit Wert erkannt); Satz umgestellt, Gate grün vor dem Commit.
3. **Byte-Vergleich auf Blobs statt Arbeitskopie:** die Arbeitskopie trägt unter `core.autocrlf=true` CRLF; das Prüfkommando des Plans (git show gegen Arbeitskopie) würde deshalb immer abweichen. Belegt ist der Vergleich auf den committeten Blobs; der README nennt diesen Weg.
4. **Ziehbefehl Stichprobe:** im README steht `shuf ... --random-source=<(yes granite-35-03)`; ausgeführt wurde wegen der Werkzeugsperre die gleichwertige Datei-Variante (`yes granite-35-03 | head -c 1000000` als Datei), gleiche Bytes am Anfang des Zufallsstroms.

## Known Stubs

Keine. Die Abschnitte ab 8 (Ergebnisse) entstehen planmäßig in 35-09 bis 35-11.

## Self-Check: PASSED

- docs/measurements/2026-10-granite-vergleich/README.md vorhanden, Owner-Zeile in Abschnitt 7
- testdata/semantik/de.jsonl 120 Zeilen
- Commits f8ca7296, 3d1a41b7, 8aff64f8 und 43e5adac im Log
