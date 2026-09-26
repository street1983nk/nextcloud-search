---
phase: 22-messanfahrt-bl-f03
plan: 07
subsystem: messanfahrt
tags: [rechenblatt, deckel, owner-checkpoint, dismax-regel, laufwerte, v13]
requires:
  - "22-06 (W4: F4 3,955, D-03 angewandt, Box-Digest-Kandidat)"
provides:
  - "Freigabezeile: Anfahrt freigegeben 26.09.2026, Deckel 24 h / 3,76 USD (Variante stunden), Weg a, B4 gefahren (F4 = 3,955)"
  - "Laufwerte im README: DECKEL_MINUTEN 1354, DECKEL_REST_MINUTEN 86, B4_GEPLANT ja, EINZELWEG a"
  - "00-ablauf.md Abschnitt 6: Owner-Antwort wörtlich, dismax-Regel ohne Ermessen; E10 mit Schwellen 0,05 und 1,20"
affects:
  - "22-08 (Aufbau und unbeaufsichtigter Lauf lesen nur noch diese Laufwerte)"
  - "22-09 (B4 mit DECKEL_REST_MINUTEN 86, Kosten gegen 3,76 USD)"
  - "22-10 (MESS-09-Entscheid allein nach der eingefrorenen Regel)"
tech-stack:
  added: []
  patterns:
    - "Owner-Antwort wörtlich plus die Empfehlung, auf die sie antwortet, beide als Zitat; Auflösung darunter"
    - "Entscheidungsregel als Kennzahlzeilen der Rohdatei formuliert (Zeilenname, Vergleich, Schwelle), damit nach der Messung nichts auszulegen ist"
key-files:
  created:
    - .planning/phases/22-messanfahrt-bl-f03/22-07-SUMMARY.md
  modified:
    - docs/measurements/2026-09-v13-messung/README.md
    - docs/measurements/2026-09-v13-messung/skripte/00-ablauf.md
    - backend/tests/test_v13_ablauf.py
    - .planning/phases/22-messanfahrt-bl-f03/22-07-PLAN.md
    - .planning/phases/22-messanfahrt-bl-f03/22-RESEARCH.md
    - .planning/phases/22-messanfahrt-bl-f03/deferred-items.md
decisions:
  - "Owner 26.09.2026 ('machen wir nach deiner empfehlung'): Weg a, EINZELWEG=a, kein Block teilweg, 00-lauf.sh unverändert"
  - "Owner 26.09.2026: Deckel Variante Stunden, 24 h mit B4, höchstens 3,76 USD; DECKEL_MINUTEN=1354, DECKEL_REST_MINUTEN=86"
  - "Owner 26.09.2026: dismax-Regel = Research-Vorschlag (RBO@10-Median +0,05 über summe, kein Sprachfall-Eigenrang schlechter, Latenz-Median höchstens 1,20-fach); beide tie-Werte geprüft, höherer RBO-Median gewinnt, Gleichstand 0.0; sonst Summe"
  - "Owner 26.09.2026: F4-Definition N4/N1 bestätigt (3,955), B4_GEPLANT=ja; Freigabeumfang wie README 1.5"
metrics:
  duration: "ca. 25 min (Task 3, ohne Task 1 und Checkpoint)"
  completed: 2026-09-26
  tasks: 3
  files: 7
---

# Phase 22 Plan 07: Rechenblatt, Owner-Freigabe und eingefrorene Laufwerte Summary

Der Owner hat die Anfahrt am 26.09.2026 vor jeder Boxminute freigegeben: Weg a, Deckel 24 h / höchstens 3,76 USD mit B4, die dismax-Regel des Research-Vorschlags, F4 = 3,955 bestätigt. Die Antworten stehen wörtlich in `00-ablauf.md` Abschnitt 6, die Regel ist in Kennzahlzeilen von `98d-dismax-probe.txt` ohne Ermessen formuliert, und die Laufwerte 1354 / 86 / ja / a stehen im README. Mit dem Commit sind sie eingefroren.

## Aufgaben

| Task | Name | Commit | Dateien |
| ---- | ---- | ------ | ------- |
| 1 | Rechenblatt mit Preisen, W4-Ergebnis und den drei Fragen | 00c5598 | README Abschnitte 1 und 5 |
| 2 | Owner-Freigabe | (Checkpoint) | Antwort am 26.09.2026, im Plan unter `<result>` festgehalten |
| 3 | Antworten einfrieren, Laufwerte festhalten | 9ee4e70 | README, 00-ablauf.md, test_v13_ablauf.py, 22-07-PLAN.md, 22-RESEARCH.md |

## Owner-Antwort

Wörtlich: „machen wir nach deiner empfehlung“, auf die Empfehlung „Weg a, Deckel stunden, dismax vorschlag, F4 bestaetigt, freigegeben“.

| Frage | Entscheid | Laufwert |
|---|---|---|
| 1, 44/6-Weg | Weg a: die 37 des Snapshots einzeln, 44 / 6 nicht reproduzierbar | `EINZELWEG=a` |
| 2, Deckel | Variante Stunden: 24 h gesamt mit B4, höchstens 3,76 USD | `DECKEL_MINUTEN=1354`, `DECKEL_REST_MINUTEN=86` |
| 3, dismax und F4 | Research-Vorschlag, beide tie-Werte nach derselben Regel; F4 N4/N1 bestätigt | `B4_GEPLANT=ja` |
| Freigabe | freigegeben, Umfang README 1.5 (Aufbau, A-Record, Typwechsel B4 hin und zurück, Abbau ohne Ende-Snapshot) | Freigabezeile |

## Die eingefrorene dismax-Regel

Für `<t>` in `dismax_t00`, `dismax_t01`: (1) `kennzahl rbo10_gegen_altplan <t>` mindestens 0,05 über `summe`; (2) in den Sprachfall-Anfragen 11 bis 20 steht die eigene Datei unter `spitze <t>` nicht schlechter als unter `spitze summe` (`rueckfall` und nicht zuzuordnende zählen nicht als schlechter); (3) `kennzahl latenz_ms <t>` höchstens 1,20-fach von `summe`. Erfüllt ein `<t>` alle drei, heißt der Entscheid dismax; erfüllen beide, gilt der höhere RBO-Median, bei Gleichstand 0.0. Sonst Summe. Nicht entschieden bei Rückgabe 49 oder wenn keine eigene Datei zuzuordnen ist.

## Verifikation

- `grep -E "^Anfahrt freigegeben: [0-9]{2}\.[0-9]{2}\.2026"` README: Treffer
- `test_v13_ablauf.py` und `test_public_artifacts.py`: 109 passed; volle Suite 3259 passed / 15 skipped
- ruff check, ruff format --check, pyright (latest), vulture: grün
- `git diff 00c5598 -- skripte/00-lauf.sh` leer (Weg a, kein teilweg)
- Laufverzeichnis nach dem Commit sauber

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Tests hielten die offenen Stände fest**
- **Found during:** Task 3
- **Issue:** `test_the_run_plan_leaves_the_owner_decisions_open` verlangte dreimal „Antwort: offen“, `test_the_run_plan_report_frame_waits_for_the_release` die offene Freigabezeile; beide wären mit dem Einfrieren rot geworden.
- **Fix:** ersetzt durch `test_the_run_plan_freezes_the_owner_decisions_of_checkpoint_22_07` (Wortlaut, Datum, Laufwerte, Schwellen in Abschnitt 6 und E10) und `test_the_run_plan_report_carries_the_release_and_the_run_values` (Freigabezeile, Laufwerttabelle, Summe 1440 min).
- **Files modified:** backend/tests/test_v13_ablauf.py
- **Commit:** 9ee4e70

**2. [Checker-Warnung 2] RESOLVED-Marker in 22-RESEARCH Open Questions**
- Überschrift „Open Questions (RESOLVED)“ wie in Phase 20 und 21, je Frage eine RESOLVED-Zeile mit Quelle (Fragen 1 bis 4 Checkpoint 22-07 und Pläne 22-01/22-06, Frage 5 per Umsetzung in 22-02).

## Deferred Issues

- **Sprachfall-Eigenrang ohne eigene Zeile in 98d** (deferred-items.md, Abschnitt 22-07): Bedingung 2 der Regel braucht die Kennung der eigenen Datei jedes Sprachfalls, die 98d nicht kennt; der Bericht ordnet sie aus dem Bestand der Box zu. Liegen die Sprachfall-Dateien nicht im Snapshot, lautet der MESS-09-Entscheid nach der Regel „nicht entschieden“. 22-08 hält in P0 fest, ob sie im Bestand stehen.

## Known Stubs

Keine. Der Abschnitt „Bericht“ im README bleibt bis nach der Anfahrt offen, wie geplant (22-11).

## Self-Check: PASSED

- FOUND: docs/measurements/2026-09-v13-messung/README.md (Freigabezeile, Laufwerte)
- FOUND: docs/measurements/2026-09-v13-messung/skripte/00-ablauf.md (Abschnitt 6 gefüllt)
- FOUND: 00c5598, 9ee4e70
