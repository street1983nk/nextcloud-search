---
phase: 30-owner-tor-schema-und-tschechisch
plan: 03
subsystem: store/api (Schemamarken, Feldplan)
tags: [schema, ratchet, cz-02, d-30-08, upgrade]
requires: [30-02]
provides:
  - "LEGACY_SCHEMA_STEPS {(1,2), (2,3), (1,3)} mit Begründung je Paar"
  - "QUERYABLE_SCHEMA_GENERATIONS {2, 3}, _of_the_marks fragt die Menge statt SCHEMA_VERSION"
  - "FIELDS_SCHEMA_2 (13 Namen) und build_schema_2()/write_schema_2_index eingefroren"
affects: [30-04 Schemasprung SCHEMA_VERSION 2 -> 3, 32 Ordnerfilter (A5)]
tech-stack:
  added: []
  patterns: ["Paare statt Zahlenvergleich auch für das Lesetor", "eingefrorene Fixture je Schemageneration, gegen meta.json geprüft"]
key-files:
  created: []
  modified:
    - backend/src/findling/store/repo.py
    - backend/src/findling/api/resources.py
    - backend/tests/conftest.py
    - backend/tests/test_schema_generations.py
    - backend/tests/test_store_repo.py
    - backend/tests/test_query_fields_plan.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "QUERYABLE_SCHEMA_GENERATIONS ausgeschrieben, nicht aus SCHEMA_VERSION abgeleitet; SCHEMA_VERSION-Import in resources.py entfällt"
  - "DEFAULT_FIELDS existiert nicht mehr; die Inklusion wird gegen LEGACY_PLAN (fields, title_only, boosts) geprüft"
metrics:
  duration: "ca. 45 min (davon 2 x ca. 10 min volle Suite)"
  completed: 2026-10-10
  tasks: 2
  files: 7
---

# Phase 30 Plan 03: Markenratsche und Lesetor vor dem Schemasprung Summary

Die Ratsche `LEGACY_SCHEMA_STEPS` trägt die Schritte ("2","3") und ("1","3"), das Lesetor `_of_the_marks` fragt die geschlossene Menge `QUERYABLE_SCHEMA_GENERATIONS = {"2","3"}` statt wörtlich `SCHEMA_VERSION`, und das Schema-2-Layout (13 Felder) ist als Liste und als eigener Fixture-Bau eingefroren. Bei `SCHEMA_VERSION = 2` verhaltensneutral; Plan 30-04 trifft damit auf ein abgesichertes Tor.

## Ergebnis

- Task 1: `version_mismatch` meldet für gespeichert "1"/"2" gegen erwartet "3" keine Drift; "3" gegen "2", None und `UNKNOWN_VERSION` gegen "3" bleiben Drift. Begründungsblock nennt D-30-08 und `body_cs`, Ratschensatz auf "schema 4" fortgeschrieben.
- Task 1: `build_schema_2()`, `open_schema_2_index`, `write_schema_2_index` (Verzeichnis `index-schema-2`) in conftest.py; `schema_2_index` ruft `build_schema()` nicht mehr. Ein Test liest die Feldnamen aus `meta.json` des geschriebenen Verzeichnisses und verlangt genau `FIELDS_SCHEMA_2`; Gegenprobe: `body_cs` wirft ValueError.
- Task 2: Marken {schema "3", de,en,es} und {schema "2", de,en,es} (mit `SCHEMA_VERSION` per monkeypatch auf 3) ergeben auf `schema_2_index` einen Plan mit `body_es`, ohne `body_cs`; `plan_falls_short` False. "1", fehlende Marke, "4", `UNKNOWN_VERSION` fallen weiter auf `LEGACY_PLAN`.
- Baumhash: Task 1 `34d61421...4e1e`, Task 2 `0f07f40c...e0f6`; `PACKAGE_FILES_TODAY` bleibt 74; je ein Journalabsatz.
- Gates: ruff, ruff format, pyright (latest) 0 Fehler, vulture grün; volle Suite 4742 passed / 25 skipped.
- `grep -v '^\s*#' resources.py | grep -c '!= str(SCHEMA_VERSION)'` = 0.

## Prüfzeile A5

- `backend/src/findling/store/schema.sql` Zeile 44: Tabelle `files` trägt `path TEXT NOT NULL` je `file_id`.
- `backend/src/findling/store/repo.py` Zeile 1361 `prefilter_visible(uid, file_ids)`: Vorfilter über Kandidaten-`file_id`s in Bändern (`_ACL_BAND`), Abfrage Zeile 1399 gegen `acl`. Ein Ordnerfilter (Phase 32, USRCH-02) lässt sich in derselben Form als Store-Vorfilter `files.path` über die Kandidaten-IDs bauen.
- Das tantivy-Feld `path` ist mit `TOKENIZER_STORED_ONLY` nur gespeichert, nicht durchsuchbar (schema.py Zeile 153); der Filter darf also gar nicht über tantivy laufen und braucht kein neues Feld.
- Ergebnis: **kein zweiter Schemaschritt nötig.** Hinweis für Phase 32 (kein Befund zu diesem Plan): Ob `files.path` der Nutzersicht entspricht (Team-Ordner, Mounts), ist dort zu klären; das ist eine Abbildungsfrage, keine Schemafrage.

## Commits

| Commit | Inhalt |
|---|---|
| 95f89f5e | test(30-03): RED Ratsche und eingefrorenes Schema-2-Layout |
| 75f62459 | feat(30-03): LEGACY_SCHEMA_STEPS 3 Paare, build_schema_2, Baumhash |
| 6060c123 | test(30-03): RED Feldplan unter Schema-3-Marken |
| fb9250f6 | fix(30-03): QUERYABLE_SCHEMA_GENERATIONS, Baumhash |

Nicht gepusht (Plan verlangt kein CI).

## Deviations from Plan

**1. [Rule 3 - Bezug] `DEFAULT_FIELDS` gibt es nicht mehr**
- Plan verlangte "`DEFAULT_FIELDS` steht in FIELDS_SCHEMA_2". Die Konstante fiel in Plan 19-01 (jetzt `LEGACY_PLAN`). Geprüft wird daher `fields | title_only | boosts` von `LEGACY_PLAN` gegen `FIELDS_SCHEMA_2`.

**2. [Testpflege] Bestehender Parametrierfall "3" in `test_a_schema_generation_this_code_never_saw_is_no_permission`**
- "3" ist jetzt eine abfragbare Generation; ersetzt durch "4", dazu die echte Konstante `UNKNOWN_VERSION`.

**3. [Commit-Schnitt] conftest.py im GREEN-Commit von Task 1**
- RED berührte nur Testdateien; die neuen conftest-Helfer kamen mit dem GREEN-Commit, damit der RED-Import tatsächlich scheitert. Beide RED-Läufe waren rot (Task 1: 3 Fehlschläge in test_store_repo plus Importfehler; Task 2: Importfehler `QUERYABLE_SCHEMA_GENERATIONS`).

**4. Ungenutzter Import** `SCHEMA_VERSION` in resources.py entfernt (einzige Verwendung war die ersetzte Gleichheit); der monkeypatch-Test nutzt `raising=False`.

## Threat Flags

Keine neue Angriffsfläche. T-30-11/12/13 durch die Tests oben abgedeckt.

## Self-Check: PASSED

- Commits 95f89f5e, 75f62459, 6060c123, fb9250f6 im Log
- `frozenset({("1", "2"), ("2", "3"), ("1", "3")})` in repo.py, `def build_schema_2` in conftest.py, `QUERYABLE_SCHEMA_GENERATIONS: Final = frozenset` in resources.py
