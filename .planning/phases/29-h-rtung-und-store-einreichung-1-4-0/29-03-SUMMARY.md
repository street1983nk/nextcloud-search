---
phase: 29-h-rtung-und-store-einreichung-1-4-0
plan: 03
subsystem: deploy-config, test-hygiene, ops
tags: [info-xml, appapi, pytest, starlette, aws, diagnose]
requires: []
provides:
  - "Deploy-Variable FINDLING_MAX_CELLS (Default 200000 = config.MAX_CELLS)"
  - "Starlette-httpx2-Warnung testseitig stumm, auch unter -W error"
  - "aws_box destroy: Schlüsselpaar per KeyPairId in shared, key-pair-Tag-Treffer werden zurückgelesen"
  - "Boxlose Analyse der 60 s (A7 in einfacher Form widerlegt)"
affects: [29-12 (Endwortlaut der zwei Variablenbeschreibungen)]
tech-stack:
  added: []
  patterns: ["Erstimport unter warnings.catch_warnings in conftest, weil -W die ini-Filter überstimmt"]
key-files:
  created: []
  modified:
    - backend/appinfo/info.xml
    - backend/tests/test_info_xml_defaults.py
    - backend/pyproject.toml
    - backend/tests/conftest.py
    - backend/tests/test_ops_scripts.py
    - scripts/ops/aws_box.sh
    - .planning/debug/embed-handover-lock-timeout.md
decisions:
  - "Satz 'Only one document is read at a time' in FINDLING_EXTRACT_ADDRESS_SPACE_BYTES vorläufig ersetzt (Orchestrator-Vorgabe), Endwortlaut kommt mit 29-12"
  - "Starlette-Warnung: pyproject-Filter plus conftest-Erstimport, keine neue Abhängigkeit (httpx2 nicht gezogen)"
  - "Tag-Sweep liest auch key-pair-Treffer per describe-key-pairs --key-pair-ids zurück"
metrics:
  duration: "ca. 45 min"
  completed: 2026-10-06
  tasks: 3
  files: 7
requirements: [REL-04]
---

# Phase 29 Plan 03: Hygiene ohne Produktcode Summary

FINDLING_MAX_CELLS als AppAPI-Variable deklariert und gegen config.MAX_CELLS getestet, Starlette-Testwarnung ohne neue Abhängigkeit beseitigt, aws_box-Sweep zählt das geteilte Schlüsselpaar über seine key-ID, und die 60-s-Hypothese A7 ist boxlos gemessen und in einfacher Form widerlegt.

## Tasks

| Task | Inhalt | Commit |
|------|--------|--------|
| 1 | FINDLING_MAX_CELLS in info.xml (Default 200000), EXPECTED + Schwelle 17 | 395085f6 |
| 2 | Starlette-Filter (pyproject + conftest), KeyPairId in shared, key-pair-Rücklesen, Tests | 9607603a |
| 3 | a0ac5aee verifiziert, Nachtrag "Boxlose Vertiefung Phase 29" | fe00867e |

## Verifikation

- `test_info_xml_defaults.py`, `test_lockstep_versions.py`, `test_store_metadata.py`: 107 passed.
- `test_ops_scripts.py`: 121 passed; gegen das alte Skript 5 rot (RED belegt).
- `pytest -W error::UserWarning tests/test_diagnose_endpoint.py`: 32 passed; `httpx2` in uv.lock: 0.
- `test_queue_client.py`: 89 passed; Logzeilen in queue.py:640 und embedding.py:276 vorhanden.
- Volle Suite: 4438 passed, 25 skipped. ruff, ruff format, pyright (latest) 0 errors, vulture sauber.
- Nichts unter backend/src/findling oder php/ geändert, Baumhash-Pins unberührt.

## Messergebnis Task 3

Gehaltene Antwort: 30,1 s, NextcloudException status=408. Gehaltener Body: 30,0 s, ConnectionError status=none. Tröpfelnde Antwort: keine Gesamtfrist (int gilt je Lesevorgang). 60 s brauchen also zwei Wartezeiten, eine fremde Frist mit Byte-Fluss oder ein anderes NPA_TIMEOUT. Feldbeleg verschoben (D-29-11).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] -W error::UserWarning überstimmt den ini-Filter**
- **Found during:** Task 2
- **Issue:** Das Akzeptanzkriterium `pytest -W error::UserWarning` blieb rot, weil Kommandozeilenfilter Vorrang vor `filterwarnings` aus pyproject haben.
- **Fix:** conftest.py importiert den TestClient einmal unter `warnings.catch_warnings` mit genau diesem Ignore; spätere Importe treffen das gecachte Modul. pyproject-Eintrag bleibt für normale Läufe.
- **Files modified:** backend/tests/conftest.py
- **Commit:** 9607603a

**2. [Rule 1 - Bug] key-pair-Tag-Treffer wurden nie zurückgelesen**
- **Found during:** Task 2
- **Issue:** Im Teardown ohne zweite Box wird das Schlüsselpaar gelöscht, ein nachlaufender Tag-Index hätte es über `*) hit_state='there'` als Rest gemeldet und den Lauf rot beendet (gleiche Klasse wie die Volumes vom 11.09.).
- **Fix:** Fall `key-pair)` im Sweep liest per `describe-key-pairs --key-pair-ids` zurück; Strukturtest um `key-pair)` erweitert.
- **Commit:** 9607603a

**3. [Rule 1 - Test] Reihenfolgetest an die neue describe-key-pairs-Stelle angepasst**
- **Issue:** `body.index("describe-key-pairs")` traf nun den ID-Abruf vor dem Löschen.
- **Fix:** Der Test prüft die Reihenfolge am vollständigen Rücklese-Aufruf (`resource_gone "$(ec2_soft describe-key-pairs --key-names`).
- **Commit:** 9607603a

**4. Orchestrator-Vorgabe statt Planvorgabe: Beschreibung von FINDLING_EXTRACT_ADDRESS_SPACE_BYTES**
- Plan sagte "hier NICHT ändern", der Orchestrator verlangte die Korrektur. Der falsche Satz ist durch einen vorläufigen, sachlich richtigen ersetzt; 29-12 übernimmt den abgenommenen Wortlaut (dessen Gate "Only one document is read at a time = 0" ist schon erfüllt).
- **Commit:** 395085f6

### Hinweis TDD

Task 1 wurde in einem Commit gebaut (Test und Deklaration zusammen); RED für Task 2 wurde durch Lauf gegen das alte Skript belegt, nicht als eigener test-Commit.

## Known Stubs

Keine. Die Beschreibung von FINDLING_MAX_CELLS ist bewusst vorläufig (Endwortlaut aus 29-02, Übernahme in 29-12).

## Self-Check: PASSED

- FOUND: backend/appinfo/info.xml, backend/tests/conftest.py, scripts/ops/aws_box.sh, .planning/debug/embed-handover-lock-timeout.md
- FOUND: 395085f6, 9607603a, fe00867e
