---
phase: 35-stretch-aehnliche-dokumente-und-spikes
plan: 04B
subsystem: semantic-search
status: abgeschlossen
tags: [STR-01, similar-documents, vector-distance, int8, measurement, nachmessung]
requires:
  - 35-04 (Bericht, Werkzeug --similar, centroid)
provides:
  - "SIMILAR_CEILING = 54,5 (Grundlage für 35-05, config-Änderung erst dort)"
  - scripts/dev/vector_distances.py --versions [--derive] [--groups]
  - docs/measurements/2026-10-aehnlich-distanzen/ Abschnitt 10 (Regel, Ergebnis, Grenzen)
affects:
  - 35-05 (kann starten: SIMILAR_CEILING 54,5)
key-files:
  created:
    - docs/measurements/2026-10-aehnlich-distanzen/rohdaten/02-selftest.txt
    - docs/measurements/2026-10-aehnlich-distanzen/rohdaten/02-umgebung.txt
    - docs/measurements/2026-10-aehnlich-distanzen/rohdaten/02-versions.txt
  modified:
    - docs/measurements/2026-10-aehnlich-distanzen/README.md
    - scripts/dev/vector_distances.py
    - backend/tests/test_vector_distances.py
decisions:
  - "Owner-Entscheid 19.10.2026: Weg 2, echte Dokumentpaare (Fassungspaare), Regel vor dem Lauf"
  - "SIMILAR_CEILING = 54,5: F1 46,0, F2 63,5, Mitte 54,75 abgerundet"
  - "Gruppenprobe nur Information: bei 54,5 liegen 10 von 38 Gruppenpaaren darunter, 0 von 287 Fremdpaaren"
metrics:
  completed: 2026-10-19
  tasks: 5
  files: 7
---

# Phase 35 Plan 04B: Nachmessung Fassungspaare Summary

Nachmessung nach Owner-Weg 2: echte Dokumentpaare (Basisdokument gegen seine Fassung, Centroid gegen Centroid, Seed 3504) trennen sich sauber von Unbeteiligten; die vorab festgelegte Regel liefert `SIMILAR_CEILING` 54,5.

## Commits (Reihenfolge belegt)

| Schritt | Commit | Inhalt |
|---|---|---|
| Owner-Entscheid | 8cfedcbf | Abschnitt 7, Zeile Weg 2 |
| Regel vor dem Lauf | 1a32b6c9 | Abschnitt 10.1 (F0 bis F4) |
| Tests rot | 1f9f8932 | 10 failed, 22 passed |
| Werkzeug grün | 48ae2b37 | `--versions`, 32 passed |
| Messung + Bericht | 12f55aad | Rohdaten 02-*, Abschnitte 10.2 bis 10.4 |

## Ergebnis

- Bestand: de 30, en 10, fr 30 Fassungspaare; 1740, 180, 1740 unbeteiligte Paare.
- Fassungen max 45,63; nächstes unbeteiligtes Paar 55,41 (Lücke knapp 10).
- F1 46,0; F2 63,5; F3 54,5 (Abstand 8,5 / 9,0); F4 erfüllt.
- Bei 54,5: alle 70 Fassungspaare darunter, alle 3660 unbeteiligten darüber.
- Hinweis für STR-01: themenverwandte, verschieden formulierte Dokumente fallen meist raus (Gruppenprobe 26,32 Prozent darunter).

## Deviations from Plan

- **Gruppenprobe nicht entscheidend:** in der Regel (10.1) vorab begründet, weil sie Themenverwandtschaft misst und ihre Zahlen seit 35-04 bekannt waren.
- **Werkzeug-Refactor:** `corpus_stock` nutzt jetzt `open_chunker` + `chunk_and_embed` (gleiches Verhalten, Tokenizer einmal je Lauf).
- Kein Push, kein CI-Lauf (Worktree, Orchestrator merged).

## Gates

- ruff (backend + scripts), ruff format, pyright (Projektkonfig) 0 Fehler, vulture sauber, reuse lint konform.
- Volle Suite: 5788 passed, 264 skipped.

## Known Stubs

Keine.

## Self-Check: PASSED

- Dateien vorhanden: README.md (Abschnitt 10), rohdaten/02-selftest.txt, 02-umgebung.txt, 02-versions.txt.
- Commits vorhanden: 8cfedcbf, 1a32b6c9, 1f9f8932, 48ae2b37, 12f55aad.
