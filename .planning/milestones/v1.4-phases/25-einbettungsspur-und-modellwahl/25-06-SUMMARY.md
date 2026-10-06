---
phase: 25-einbettungsspur-und-modellwahl
plan: 06
subsystem: embed-weights
tags: [fp32, release-asset, sideload, memory-guard, gate-a]
requires: ["25-01", "25-05"]
provides:
  - "nc.client: fetch_release_asset(url, write, *, cap, client=None), AssetRefused, ASSET_HOSTS, ASSET_MAX_REDIRECTS"
  - "embed.weights: FP32_SHA256/FP32_BYTES/FP32_ASSET_URL, fp32_weights_path, fp32_verified, clear_leftovers, remove_fp32_weights, procure_fp32, PROCURE_OUTCOMES, hash_count, forget_verdicts"
  - "memory_guard: anon_bytes, headroom_bytes, admits"
affects: [25-09 Pin-Neumessung, 25-11 Admin-Aktion fp32, Phase 26 Speicherwächter]
tech-stack:
  added: []
  patterns: ["Umleitungen von Hand, Allowlist-Prüfung je Sprung vor der Anfrage", ".part + fsync + os.replace", "Urteils-Cache an (Pfad, size, mtime_ns, Digest)"]
key-files:
  created:
    - backend/src/findling/embed/weights.py
    - backend/src/findling/memory_guard.py
    - backend/tests/test_weights.py
    - backend/tests/test_memory_guard.py
  modified:
    - backend/src/findling/nc/client.py
    - backend/tests/test_readonly_gate.py
decisions:
  - "Cookie-Jar des Clients wird vor jedem Sprung geleert, damit ein Set-Cookie eines Sprungs nie mitreist (T-25-22 über den Plan hinaus abgesichert)"
  - "Status außerhalb 2xx ohne Umleitung (auch 3xx ohne location) ist AssetRefused, nicht nur >= 400"
  - "Urteils-Cache-Schlüssel enthält zusätzlich den erwarteten Digest; Lesefehler beim Hash wird nicht gemerkt"
  - "memory_guard nutzt die öffentlichen Leser memory_limit und meminfo_bytes aus hardware.py; neu ist nur der memory.stat-Parser"
  - "cgroup v1 wird in memory_guard nicht ausgewertet (kein memory.max, keine anon-Zeile): Rückfall MemAvailable, im Docstring als bekannte Grenze benannt"
metrics:
  duration: "ca. 35 min"
  completed: 2026-09-28
  tasks: 3
  files: 6
---

# Phase 25 Plan 06: Bausteine der fp32-Beschaffung und der RAM-Bedingung Summary

Ein GET auf das eigene GitHub-Release mit Host-Allowlist je Sprung und Größendeckel (`fetch_release_asset`), eine atomare Datei-Seite mit festem sha256 und geschlossener Ergebnis-Menge (`embed/weights.py`) und ein neutraler RAM-Leser auf anon gegen memory.max (`memory_guard.py`); nichts davon läuft von selbst.

## Tasks

| Task | Name | Commits | Dateien |
|------|------|---------|---------|
| 1 | fetch_release_asset mit Host-Allowlist je Sprung | f2f32e1 (RED), ea681a8 (GREEN) | nc/client.py, tests/test_weights.py |
| 2 | embed/weights.py und Gate-Ausnahmepaar | 32f3ebd (RED), 85f15a1 (GREEN), 7d012d2 (style) | embed/weights.py, tests/test_readonly_gate.py, tests/test_weights.py |
| 3 | memory_guard.py | ef0f0b1 (RED), ea9b59c (GREEN) | memory_guard.py, tests/test_memory_guard.py |

## Was gebaut wurde

- **nc/client.py:** `ASSET_HOSTS` (github.com, release-assets.githubusercontent.com), `ASSET_MAX_REDIRECTS = 3`, `AssetRefused`, `_asset_client()` (follow_redirects=False, keine Header, kein `verify=_certificate_setting()`, trust_env an), `fetch_release_asset`. Jeder Sprung wird vor der Anfrage auf https und Host geprüft, relative location per `response.url.join`. Der Deckel zählt vor `write`. Ausnahmetexte nennen höchstens den Statuscode. Modul-Docstring um den Absatz zur einzigen Nicht-Nextcloud-Anfrage ergänzt. `client.stream("GET", target)` ist für Gate A ein Lesezugriff, die Write-Allowlist bleibt bei vier Einträgen.
- **embed/weights.py:** Konstanten aus Plan 25-01 (Tag `model-e5-small-fp32-614241f`, 470 268 510 Byte, Digest ca456c06...8665), `procure_fp32` mit Platzprüfung vor dem Strom, Hash und Längenzähler beim Schreiben, fsync, `os.replace`, `.part`-Entfernung im finally (synchron, abbruchsicher). Ergebnisse PROCURED, UNAVAILABLE, WRONG_DIGEST, NO_ROOM. `fp32_verified` synchron für `asyncio.to_thread`, ein stat bei fehlender Datei, kein Hash bei falscher Größe. `remove_fp32_weights` löscht auch eine selbst abgelegte Datei (D-25-09). Kein Import von httpx oder nc_py_api.
- **memory_guard.py:** `anon_bytes`, `headroom_bytes` (min(limit minus anon, MemAvailable), nie negativ, Rückfälle wie im Plan), `admits` (None heißt nie zugelassen). Kein logging, memory.current wird nie gelesen (Test mit Köderdatei).
- **Gate A:** Paar `("embed/weights.py", "mkdir")` mit eigenem Begründungsabsatz, Positivfall in `test_the_reviewed_exception_covers_exactly_the_named_modules`.

## Verifikation

- `pytest` gesamt: 3571 passed, 15 skipped, 1 deselected. Deselektiert ist, wie von der Welle-3-Pin-Regel vorgesehen, `tests/test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_python_package` (zwei neue Dateien unter `backend/src/findling` verschieben den Paket-Pin; Neumessung durch den Orchestrator/Plan 25-09 nach dem Merge).
- ruff check, ruff format --check, pyright (PYRIGHT_PYTHON_FORCE_VERSION=latest) 0 Fehler, vulture --min-confidence 80 sauber.
- Akzeptanz-Greps: Digest genau 1 in weights.py, kein httpx/nc_py_api in weights.py, Gate-Paar genau 1, `def headroom_bytes`/`def admits` je 1, kein `"memory.current"` und kein `import logging` in memory_guard.py.
- `git diff --stat ebf6f74 -- php backend/src/findling/worker backend/tests/test_measurement_scripts.py` leer.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Sicherheit] Cookies zwischen Sprüngen geleert**
- **Found during:** Task 1
- **Issue:** httpx speichert Set-Cookie-Antworten im Client-Jar; beim Verfolgen der Umleitungen von Hand wäre ein Cookie eines Sprungs beim nächsten Sprung auf denselben Host mitgereist. Das Threat Register (T-25-22) fordert "ohne Cookies".
- **Fix:** `client.cookies.clear()` vor jeder Anfrage; der Header-Test setzt ein Cookie auf dem ersten Sprung und prüft, dass keine Anfrage einen cookie-Header trägt.
- **Files modified:** backend/src/findling/nc/client.py, backend/tests/test_weights.py
- **Commit:** ea681a8

**2. [Rule 1 - Bug] Überlange Docstring-Zeile**
- **Found during:** Task 3 (Gesamtlauf ruff)
- **Issue:** Nach einer Umformulierung (um den Akzeptanz-Grep auf nc_py_api zu erfüllen) war eine Zeile in weights.py länger als 120 Zeichen; der Task-2-Commit enthielt sie bereits.
- **Fix:** Zeile umbrochen, eigener style-Commit.
- **Commit:** 7d012d2

Sonst wie geplant. Zusätzliche Tests über die Behavior-Liste hinaus: Start-URL außerhalb der Allowlist (keine Anfrage), drei Sprünge werden noch verfolgt, AssetRefused aus fetch ergibt UNAVAILABLE, zu kurzer Download ergibt WRONG_DIGEST, anon über der Grenze ergibt 0.

## TDD Gate Compliance

Je Task ein `test(25-06)`-Commit (RED, Sammelfehler beim Import bestätigt) vor dem `feat(25-06)`-Commit (GREEN). Kein Refactor-Commit nötig.

## Known Stubs

Keine. Die Bausteine sind bewusst unverdrahtet (D-25-05); der Aufruf auf Admin-Aktion und `models_dir` aus `findling.config` kommen mit Plan 25-11.

## Threat Flags

Keine neue Oberfläche außerhalb des Threat Registers: die einzige neue Netzanfrage ist T-25-21/22/27, der neue Dateipfad T-25-24/25.

## Self-Check: PASSED

- FOUND: backend/src/findling/embed/weights.py, backend/src/findling/memory_guard.py, backend/tests/test_weights.py, backend/tests/test_memory_guard.py
- FOUND: f2f32e1, ea681a8, 32f3ebd, 85f15a1, 7d012d2, ef0f0b1, ea9b59c
