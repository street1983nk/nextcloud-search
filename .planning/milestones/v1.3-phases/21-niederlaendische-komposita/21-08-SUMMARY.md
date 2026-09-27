---
phase: 21-niederlaendische-komposita
plan: 08
subsystem: ci
tags: [ci, language-proof, nl, komposita, textgate]
requires: []
provides:
  - "Kompositumfall nlc (gemeentebelastingen ueber belasting) im CI-Schritt Language proof"
  - "Textgate mit fuenf Faellen und PAGE_CALLS_EXPECTED = 5"
affects:
  - .github/workflows/deploy-harp.yml
  - backend/tests/test_language_proof_steps.py
tech-stack:
  added: []
  patterns: ["eine Frage-Tabelle (set_term) fuer Poll-Schleife und Verschwinden-Messung"]
key-files:
  created: []
  modified:
    - .github/workflows/deploy-harp.yml
    - backend/tests/test_language_proof_steps.py
decisions:
  - "Frage-Tabelle als Shell-Funktion set_term, damit nlc) term=belasting ;; genau einmal steht und beide Schleifen dieselben Woerter fragen"
metrics:
  duration: "ca. 20 min"
  completed: 2026-09-25
requirements: [KOMP-01]
---

# Phase 21 Plan 08: Kompositumfall im CI-Sprachbeweis Summary

Fünfter Fall `nlc` im bestehenden Schritt "Language proof": Dokument "De gemeentebelastingen voor dit jaar zijn verhoogd.", Frage `belasting`, über OCS-Route und Ergebnisseite, mit dokumentierter Rot-Begründung ohne `split_compound`; der Textgate hält fünf Fälle und wird rot, wenn der Fall fehlt.

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | Fünftes Dokument im Schritt Language proof | 29cf143 | .github/workflows/deploy-harp.yml |
| 2 | Textgate kennt den fünften Fall | d08ed90 | backend/tests/test_language_proof_steps.py |

## Kollisionsprüfung (vor der Änderung)

`grep -n -i "gemeente\|belasting\|verhoogd" .github/workflows/deploy-harp.yml` auf dem Stand dd8e4d2: **kein Treffer**. Keines der neuen Wörter ist ein Term, den ein anderer Beweis des Workflows zählt.

## Was sich im Schritt geändert hat

- Kommentarabsatz unter "-- the four documents --" mit "red without split_compound, measured 2026-09-25", den vier Querprobe-Zeilen (de, en, nl without, nl with) und Verweis auf die one term rule (Kommentar zur Vektorhälfte in "Store upgrade 3").
- `printf` für `language-proof-nlc.txt` (reines ASCII, Datei bleibt byteweise ASCII, geprüft).
- Upload, Poll (`missing="es it nl pt nlc"`), Erster-Treffer-Zuordnung, Ergebnisseite (fünfter literaler `curl`, `?query=belasting`), Prüfschleife, Löschschleife und Verschwinden-Messung laufen über `es it nl pt nlc`.
- Kommentar "Five literal calls and no loop" mit dem Hinweis, dass nl zwei Fälle hat.
- `git diff -U0` zeigt nur Hunks zwischen Zeile 911 und 1188 (Schritt Language proof); Store upgrade 5 und 6 byteidentisch.

## Rot-Belege (Gegenproben am echten Workflow, danach zurück)

Scan über eine Kopie des echten Workflows mit je einem entfernten nlc-Eintrag:

- Ergebnisseiten-Aufruf nlc entfernt: 2 Befunde, "does not ask the result page for 'belasting'" und "calls the result page 4 times and not 5".
- Case-Zeile `nlc) term=belasting ;;` entfernt: 1 Befund, "does not ask the search route for 'belasting'".
- `printf` des nlc-Dokuments entfernt: 1 Befund, "does not name language-proof-nlc.txt".
- Unveränderter Workflow: 0 Befunde.

Dieselben drei Gegenproben stehen jetzt dauerhaft als Selbsttests gegen `_CLEAN` in der Suite.

## Verifikation

- YAML gültig, `nlc) term=belasting ;;` 1x, `apps/findling/?query=belasting` 1x, Rot-Satz 1x, `language-proof-nlc.txt` 1x.
- `pytest tests/test_language_proof_steps.py`: 29 passed.
- ruff check, ruff format --check, vulture (80): grün; pyright (latest): 0 errors.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Frage-Tabelle als Funktion `set_term`**
- **Found during:** Task 1
- **Issue:** Die Verschwinden-Messung trägt eine zweite, identische `case`-Tabelle. Sie muss nlc ebenfalls kennen (Plan verlangt die Messung über nlc), eine zweite Zeile `nlc) term=belasting ;;` hätte das Akzeptanzkriterium "genau 1" gebrochen.
- **Fix:** Beide Tabellen durch eine Shell-Funktion `set_term` ersetzt (ohne Subshell gerufen, damit `exit 1` bei unbekanntem Code den Schritt beendet). Beide Schleifen fragen damit garantiert dieselben Wörter.
- **Commit:** 29cf143

**2. [Rule 3 - Blocking] `_CLEAN`-Zeile für nlc im `--arg`-Stil**
- **Found during:** Task 2
- **Issue:** Ein `_CLEAN`-Eintrag im Muster der vier anderen hätte `"language-proof-nlc.txt"` ein zweites Mal geschrieben (Kriterium: genau 1).
- **Fix:** Beispielzeile als `jq -e --arg file language-proof-nlc.txt '.title == $file' five.json`, wie der echte Workflow die Zuordnung prüft.
- **Commit:** d08ed90

Zusätzlich: Step-Summary-Zeilen und Meldungen des Schritts auf fünf Fälle gezogen (reine Texte).

## Hinweise

- Der Schritt ist bis zur Verdrahtung (21-07) erwartbar rot; Push erst in Plan 21-09.
- Stepname (`PROOF_STEP`) unverändert.

## Self-Check: PASSED

- FOUND: .github/workflows/deploy-harp.yml (nlc-Fall)
- FOUND: backend/tests/test_language_proof_steps.py (PAGE_CALLS_EXPECTED = 5)
- FOUND: 29cf143, d08ed90
