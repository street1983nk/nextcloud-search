---
phase: quick-261002-af9
plan: 01
subsystem: mess-harness
tags: [blocker-28-07, harness-tor, queue, messlauf, tdd]
requires: []
provides:
  - "10-zelle.sh: Schritt vorrat-tor (Abbruch 73) zwischen Registrierung und Bewaffnung"
  - "93b-nullstand.sh: Rueckgabewerte wieder 0/11/12, Quelle 4 nur protokolliert"
  - "test_v14_zelle.py: STUB_NACHSCHUB-Mechanik + Nachschub-Test (rc 0)"
affects: [phase-28-messlauf]
tech-stack:
  added: []
  patterns: ["Tor-Position vor der Bewaffnung: nur dort ist Vorrat zwingend Altbestand"]
key-files:
  created: []
  modified:
    - backend/tests/test_v14_zelle.py
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/93b-nullstand.sh
decisions:
  - "ORDER-Konstante erst im GREEN-Commit angepasst, damit die Alt-Suite am RED-Stand grün bleibt"
  - "Neuer Schritt als Abschnitt 4b nummeriert, keine Umnummerierung der Folgeabschnitte"
metrics:
  duration: "~25 min"
  completed: "2026-10-02"
---

# Quick Task 261002-af9: Vorrats-Tor vor die Bewaffnung ziehen Summary

Das 73er-Vorrats-Tor wandert vom 93b-Schritt (nach der Bewaffnung) an den neuen Schritt vorrat-tor vor der Bewaffnung; 93b urteilt wieder nur 0/11/12 und protokolliert Quelle 4 nur noch. PHP unberührt.

## Tasks

| Task | Commit | Inhalt |
| ---- | ------ | ------ |
| 1 (RED) | e5bd515e `test(quick-af9): expect the stock gate before the arming` | Test 1 umgebaut (73 am frühen Tor, Abwesenheits-Asserts für enable/baumhash/93b-Datei), Test 2 neu (`test_cell_tolerates_fresh_topup_after_the_arming`, rc 0), Stub: enable-Zweig setzt Marke `bewaffnet`, findling:index antwortet STUB_NACHSCHUB nur mit dieser Marke; Trigger-Marken-Mechanik unberührt |
| 2 (GREEN) | c04e7431 `fix(quick-af9): move the stock gate before the arming` | 10-zelle.sh: Schritt vorrat-tor (inline-Lesung, Abbruch 73 mit bezifferter Zeile `vorrat-tor altvorrat N`), 93b-Schritt ohne 13er-Mapping, Kopf aktualisiert (Schrittliste, 73er-Tabellenzeile); 93b-nullstand.sh: rc 13 und `vorrat-voll`-Marker entfernt, Urteils-Absatz mit Lauf-4-Begründung; ORDER-Konstante trägt vorrat-tor |

## RED-Beleg (vor dem Fix, Stand e5bd515e)

Gefilterter Lauf `pytest tests/test_v14_zelle.py -q -k "work_stock or topup or nought"`: **2 failed, 6 passed**.

- Test 1 (`test_cell_nought_reading_refuses_a_filled_work_stock`): Abbruch fiel noch am 93b-Schritt:
  ```
  assert steps[-1] == "vorrat-tor", steps
  AssertionError: assert '93b-nullstand' == 'vorrat-tor'
  ```
- Test 2 (`test_cell_tolerates_fresh_topup_after_the_arming`): Zelle brach noch mit 73 ab:
  ```
  assert 73 == 0
  stderr: '10-zelle: der Arbeitsvorrat der PHP-Haelfte ist nicht leer, --rm-data raeumt die NC-Queue nicht'
  ```
- Volle Suite am RED-Stand: 2 failed, 64 passed (Alt-Suite grün, inkl. Zähltor-, rc-67- und rc-71-Tests).

## Gates (GREEN, Stand c04e7431)

- `pytest tests/test_v14_zelle.py tests/test_measurement_scripts.py -q` (PYTHONUTF8=1): **543 passed**
- `ruff check` + `ruff format --check` auf test_v14_zelle.py: sauber
- `exit 13` in 93b-nullstand.sh (ohne Kommentare): 0 Treffer
- `abbruch 73` in 10-zelle.sh (ohne Kommentare): genau 1, am vorrat-tor
- `schritt vorrat-tor` in 10-zelle.sh (ohne Kommentare): genau 1
- Beide Shell-Skripte: 0 CR-Bytes, 0 Em-/En-Dashes, 0 Nicht-ASCII-Zeichen

## Deviations from Plan

**1. [Rule 3 - Blockierend] ORDER-Konstante im GREEN- statt im RED-Commit angepasst**
- **Found during:** Task 1
- **Issue:** `test_cell_order_runs_every_step_in_the_order_of_pattern_1` prüft die exakte Schrittfolge; mit vorrat-tor in ORDER wäre der Order-Test am RED-Stand rot gewesen, entgegen der Plan-Vorgabe "Alt-Suite muss weiter grün sein".
- **Fix:** ORDER (eine Zeile, `"vorrat-tor"` zwischen registrierung und bewaffnung) wandert in den fix-Commit; Task-2-Dateiliste damit um test_v14_zelle.py erweitert.
- **Commit:** c04e7431

**2. [Kosmetisch] Neuer Abschnitt als "4b." nummeriert**
- Die Abschnittskommentare in 10-zelle.sh sind durchnummeriert (1-16); der neue Schritt heißt "4b.", damit die 12 Folgeabschnitte nicht umnummeriert werden müssen.

## Known Stubs

Keine. Die Skripte tragen weiterhin die Kopfzeile "DIESE FASSUNG IST NICHT GEFAHREN" (beabsichtigt: sie fahren erst auf der Anfahrt-Box).

## Threat Flags

Keine neuen Oberflächen: nur Mess-Harness (lesendes Tor, occ findling:index) und boxloser Test-Stub. T-af9-01 mitigiert (Tor liest nur, Abbruch 73 vor allem Teuren), T-af9-02 mitigiert (arbeitsvorrat-Zeile bleibt in der 93b-Rohdatei, Rückbau im Kopf begründet).

## Self-Check: PASSED

- backend/tests/test_v14_zelle.py: FOUND
- docs/measurements/2026-10-abnahme-anfahrt/skripte/10-zelle.sh: FOUND
- docs/measurements/2026-10-abnahme-anfahrt/skripte/93b-nullstand.sh: FOUND
- Commit e5bd515e: FOUND
- Commit c04e7431: FOUND
