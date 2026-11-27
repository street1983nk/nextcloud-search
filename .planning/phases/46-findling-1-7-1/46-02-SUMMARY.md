---
phase: 46-findling-1-7-1
plan: 02
subsystem: admin-ui
tags: [excl-08, tastatur, ime]
requires: [46-01]
provides: [addOnEnter, Gate Enter in beiden Regelfeldern]
affects: [php/js/admin.js]
key-files:
  modified:
    - php/js/admin.js
    - backend/tests/test_admin_ui_contract.py
duration: ca. 25 min
completed: 2026-11-27
---

# 46-02: Enter fügt in Ordner- und Musterliste hinzu (EXCL-08)

## Ergebnis

- RED 10744068 `test(46-02): enter in either rule field takes the way of its button`: `test_enter_in_either_rule_field_takes_the_way_of_its_button` rot (erster Fund `the helper addOnEnter is missing or defined twice`, dazu je Liste die fehlenden Aufrufe); Positivkontrolle `test_the_enter_gate_sees_a_missing_guard` übersprungen, solange der Gate rot ist (gewollt), ihr erster Teil (Fassung ohne Helfer wie in 1.7.0) prüft immer.
- GREEN a4ea0a93 `fix(46-02): enter adds an entry to the folder and the pattern list`: neuer Helfer `addOnEnter (field, addEntry)` (keydown, nur `Enter`, nicht bei `event.isComposing` oder `keyCode === 229`, nicht mit Shift/Strg/Alt/Meta, dann `preventDefault()` und derselbe Aufruf wie der Knopf). Der Körper der beiden click-Handler ist unverändert in `addFolderEntry` bzw. `addPatternEntry` gezogen; Knopf und Taste rufen dieselbe Funktion. Kein neues Markup, `grep -c innerHTML php/js/admin.js` = 0, `node --check` grün.
- Mutationen je rot und zurückgesetzt (Datei byte-gleich, `cmp`): M1 ohne isComposing, M2 ohne preventDefault, M3 Taste nur am Ordnerfeld.
- Läufe: test_admin_ui_contract und test_admin_locale 251 passed; ruff, ruff format, pyright (0 Fehler), vulture grün.
- Docker-Teil von B3 offen (JS-Änderung, php_gates/PHPUnit prüfen JS nicht direkt); vor dem ersten Push (46-06) im freigegebenen Docker-Fenster.
- Browserprobe (Enter, Feldmeldungen, IME über CDP mit Positivkontrolle in zh_TW) folgt im Volltest 46-07 (P-ENT, P-IME).

## Abweichungen

- Ein gemeinsamer Helfer statt je ein keydown-Handler am Feld: `addEventListener('keydown'` steht deshalb zweimal in admin.js (Helfer und Escape der Bestätigung), nicht dreimal. Das verify von 46-02 (`-ge 3`) ist damit zu streng formuliert; der Gate prüft stattdessen, dass beide Setups `addOnEnter(field, ...)` mit der Funktion ihres Knopfs aufrufen. Inhaltlich gleichwertig (D-46-04: "eine gemeinsame Funktion je Liste").
