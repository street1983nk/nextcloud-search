---
phase: 35-stretch-aehnliche-dokumente-und-spikes
plan: 05
subsystem: semantic-search
status: abgeschlossen
tags: [STR-01, similar-documents, content-route, vector-store, permission-prefilter]
requires:
  - 35-04 / 35-04B (SIMILAR_CEILING 54,5, centroid)
provides:
  - "POST /similar {fileId, limit} -> {candidates: [{fileId}], degraded}"
  - "index.search.similar_candidates(store, vectors, uid, file_id, limit) -> list[int]"
  - "VectorStore.vectors_of(file_id) -> list[bytes]"
  - "config.SIMILAR_SCAN_CHUNKS = 300, config.SIMILAR_CEILING = 54.5"
affects:
  - 35-06 (PHP-Companion ruft /similar, Drahtformat hier festgelegt)
key-files:
  created:
    - backend/src/findling/api/similar.py
    - backend/tests/test_similar_endpoint.py
  modified:
    - backend/src/findling/store/vectors.py
    - backend/src/findling/index/search.py
    - backend/src/findling/config.py
    - backend/src/findling/main.py
    - backend/appinfo/info.xml
    - backend/tests/test_vector_store.py
    - backend/tests/test_search_library.py
    - backend/tests/test_semantic_boundary.py
    - backend/tests/test_info_xml_defaults.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "SIMILAR_CEILING = 54.5 aus 35-04B übernommen, als feste Konstante (keine Umgebungsvariable, kein info.xml-Eintrag)"
  - "near_enough mit band = SIMILAR_CEILING, damit das Band nie enger schneidet als die Decke"
  - "Fehler und fehlende Leseseite ergeben candidates [] mit degraded true (Muster von /search)"
metrics:
  completed: 2026-10-19
  tasks: 2
  files: 12
---

# Phase 35 Plan 05: Container-Route für ähnliche Dokumente Summary

`POST /similar` liefert für eine vom Vorfilter bestätigte Quelle bis zu `limit` bestätigte Nachbar-IDs, gebaut aus dem Centroid der gespeicherten Vektoren der Quelle, ohne Modell, ohne Schema- und Indexänderung; Decke `SIMILAR_CEILING` 54,5.

## Commits

| Schritt | Commit | Inhalt |
|---|---|---|
| Task 1 + 2 (gemeinsam, Ratschen ziehen zusammen) | b9b1f102 | vectors_of, similar_candidates, Konstanten, Route, Registrierung, Ratschen |

Rot belegt vor der Umsetzung: Task 1 (ImportError `SIMILAR_CEILING`, 2 failed in test_vector_store), Task 2 (16 failed, Route nicht registriert).

## Umsetzung

- `similar_candidates`: `_permit` auf die Quelle zuerst (vor jedem Vektorzugriff, Spy-Test), dann `vectors_of`, `centroid`, ein `nearest`-Scan mit `SIMILAR_SCAN_CHUNKS + len(source)`, Quelle raus, `near_enough`, `documents_from_chunks`, `_permit` auf das Fenster, Kappen auf `limit`.
- `grep -c prefilter_visible search.py` = 2; Aufrufer-Gate `["_permit", "snippets_for"]` unverändert grün.
- Route: `extra="forbid"`, `fileId >= 1`, `1 <= limit <= SEARCH_LIMIT_MAX`; `userId` im Body ergibt 400 über den bestehenden Handler in main.py; fehlender Nutzer 401; Log nur mit Typname.
- info.xml: nur Kommentar erweitert, keine `<route>`; `grep -cE "<url>[^<]*similar"` = 0; Store-Validierung (`validate_info_xml.sh`) bestanden.
- Gegenprobe Registrierung: `APP.openapi()["paths"]` enthält `/similar` genau einmal, nur `post`.
- Baumhash: 80 Dateien, `ad36dbfb...`, unabhängig mit find/sort/tr/sha256sum nachgerechnet, gleich.

## Deviations from Plan

- **[Rule 1] Registrierungstest:** `APP.routes` zeigt in dieser FastAPI-Version eingebundene Router als `_IncludedRouter` ohne Pfad; der Test liest deshalb `APP.openapi()["paths"]`.
- **Kommentar in config.py** nennt den "permission prefilter" als Prosa; das Zählgate betrifft nur index/search.py.
- **Hinweis Messgrundlage:** 35-04B maß Centroid gegen Centroid, die Route vergleicht Centroid der Quelle gegen einzelne Chunks der Nachbarn (Minimum je Dokument). Bei Dokumenten mit 2 bis 3 Chunks liegt die Chunk-Distanz typischerweise nahe der Centroid-Distanz; für Audit 35-12 vermerkt.
- Kein Push, kein CI-Lauf (Worktree, Orchestrator merged und pusht); CI-Laufnummern daher noch offen.

## Gates

- ruff check, ruff format, pyright (latest) 0 Fehler, vulture (src tests, 80) sauber, reuse lint konform.
- Volle Suite: 5814 passed, 264 skipped.

## Threat Flags

Keine neuen Flächen außerhalb des Threat-Modells (T-35-12 bis T-35-18 umgesetzt bzw. akzeptiert wie geplant).

## Known Stubs

Keine.

## Self-Check: PASSED

- Dateien vorhanden: backend/src/findling/api/similar.py, backend/tests/test_similar_endpoint.py.
- Commit vorhanden: b9b1f102.
