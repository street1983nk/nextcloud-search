---
phase: 23-haertung-und-store-einreichung-1-3-0
plan: 02
subsystem: backend-dependencies
tags: [dependencies, uv, lockfile, third-party, ci, hart-04]
requires: []
provides:
  - "pyproject ohne fastembed, mit direkten Kanten tokenizers==0.23.2 und numpy==2.5.2"
  - "uv.lock ohne fastembed, loguru, mmh3, py-rust-stemmers, requests, urllib3 (und win32-setctime)"
  - "CI-Schritt 'The image carries no fastembed and no requests (HART-04)' in docker.yml"
affects: [23-04]
tech-stack:
  added: []
  patterns: ["transitiv genutzte Abhängigkeit wird direkte Kante (wie pillow in Phase 3)", "Abwesenheitsprüfung im gepushten Digest mit --network none"]
key-files:
  created: []
  modified:
    - backend/pyproject.toml
    - backend/uv.lock
    - THIRD-PARTY.md
    - backend/Dockerfile
    - .github/workflows/docker.yml
decisions:
  - "win32-setctime fällt zusätzlich aus dem Lockfile: reine Windows-Abhängigkeit von loguru, nie im Linux-Abbild; akzeptiert statt zurückgenommen"
  - "numpy-Lizenz in THIRD-PARTY.md als BSD-3-Clause mit dem vollen License-Expression der Wheel-Metadaten (BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0)"
  - "Dockerfile-Kommentare 123 und 363 bleiben: sie beschreiben die Herkunft der Dateiliste, keinen Import und keine Installation"
metrics:
  duration: "ca. 25 min"
  completed: 2026-09-27
  tasks: 2
  files: 5
---

# Phase 23 Plan 02: fastembed-Pin raus, tokenizers und numpy direkt Summary

Der nie importierte fastembed==0.8.0-Pin ist entfernt, tokenizers 0.23.2 und numpy 2.5.2 sind direkte, exakt gepinnte Kanten auf unveränderten Versionen, und ein neuer docker.yml-Schritt beweist im gepushten Abbild (mit `--network none`), dass fastembed und requests fehlen und tokenizers und numpy da sind.

## Was gemacht wurde

**Task 1 (4cea879):** Vorabprüfung `^\s*(import fastembed|from fastembed)` über backend/src, backend/tests, scripts: leer, also Entfernen statt "Import belegen". pyproject: fastembed-Absatz raus, tokenizers/numpy mit Begründung im Stil des pillow-Absatzes ("Net new PyPI packages of phase 23: zero"), onnxruntime-Kommentar ohne fastembed-Bezug. `uv lock` mit uv 0.11.7, `uv lock --check` grün, `uv sync --frozen`. Lockfile-Diff (Name/Version aller Pakete vorher gegen nachher): nur Entfernungen, keine Versionsverschiebung; huggingface-hub 1.30.0, tqdm 4.70.0, numpy 2.5.2, tokenizers 0.23.2, pillow 12.3.0 unverändert.

**Task 2 (40919b6):** THIRD-PARTY.md: fastembed-Zeile durch tokenizers (Apache-2.0) und numpy (BSD-3-Clause) ersetzt, Lizenzen aus den dist-info-Metadaten gelesen; onnxruntime 1.29.0 auf 1.30.0 (Altbefund); "Four packages" auf "Five"; Netzabsatz: requests nicht mehr im Abbild, huggingface-hub kommt über tokenizers (im Lockfile belegt), HF_HUB_OFFLINE=1 bleibt nötig. Dockerfile: nur Kommentar 483-484 geändert. docker.yml: Offline-Kommentar umgestellt, neuer Schritt direkt nach "Answer A12 and A13 inside this image" mit Kommentarblock (prüft Container-Ist gegen pyproject, keine Versionsprüfung). Der Einzeiler wurde lokal in beide Richtungen getestet: positiv Exit 0, mit untergeschobenen Attrappen `fastembed.py`/`requests.py` Exit 1 mit je einer `::error::`-Zeile.

## Verifikation

- ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture grün
- pytest: 3324 bestanden, 15 übersprungen, nach beiden Tasks; entspricht der Referenz aus STATE.md
- `grep -c fastembed backend/pyproject.toml` = 0; tokenizers/numpy je 1
- keine der sechs Paketnamen mehr als `name =` im Lockfile
- `grep "through fastembed"` in Dockerfile und docker.yml: kein Treffer
- `git diff backend/Dockerfile`: nur Kommentarzeilen
- Der CI-Schritt selbst läuft erst im Push von Plan 23-04

## Deviations from Plan

**1. [Rule 1 - Befund] win32-setctime fällt zusätzlich aus dem Lockfile**
- **Found during:** Task 1
- **Issue:** Der Plan erlaubt nur sechs Verluste; `uv lock` entfernte auch win32-setctime 1.2.0.
- **Begründung:** reine Windows-Abhängigkeit von loguru (Marker sys_platform == 'win32'), ohne loguru verwaist; im Linux-Abbild nie installiert. Keine Versionsverschiebung, nur eine folgerichtige Entfernung, deshalb behalten.
- **Commit:** 4cea879

**2. [Rule 1] Einzeiler mit wörtlichem `find_spec('fastembed')`**
- **Found during:** Task 2
- Die erste Fassung iterierte über Namen; das Akzeptanzkriterium sucht den Literal. Explizit ausgeschrieben, vor dem Commit.

Sonst wie geplant. backend/src nicht angefasst.

## Known Stubs

Keine.

## Self-Check: PASSED

- backend/pyproject.toml, backend/uv.lock, THIRD-PARTY.md, backend/Dockerfile, .github/workflows/docker.yml geändert und committet
- Commits 4cea879 und 40919b6 vorhanden
