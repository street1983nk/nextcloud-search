---
phase: 07-gemeinsame-embedding-engine
verified: 2026-09-08T14:11:10Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 3/4
  gaps_closed:
    - "Erfolgskriterium 4: Der Speicherunterschied zum Stand 1.0.x ist auf amd64 als Zahl belegt und benennt ausdruecklich, an welcher Stelle er anfaellt"
  gaps_remaining: []
  regressions: []
---

# Phase 7: Gemeinsame Embedding-Engine Verification Report

**Phase Goal:** Findling kommt auf derselben Box mit weniger Speicher aus, weil Suche und Indexer sich eine Modellinstanz teilen, und der Nutzer merkt davon nichts ausser dem freien Speicher.
**Verified:** 2026-09-08T14:11:10Z (Erstpruefung), Nachtrag 2026-09-08 nach Owner-Entscheid zu SC4
**Status:** passed
**Re-verification:** Yes , nach Schliessung der SC4-Luecke durch den Owner-Entscheid vom 08.09.2026

## Owner-Entscheid vom 08.09.2026, gegengelesen

Die Erstpruefung hatte SC4 als FAILED markiert: der Roadmap-Wortlaut verlangt eine amd64-Zahl fuer den Speicherunterschied zum Stand 1.0.x, und nur eine arm64-Zahl existierte (-712,6 MB Suchphase, -25,1 MB Gesamtspitze, aus der Nachmessung vom 07.09.2026).

Der Owner hat entschieden, keine Neuinterpretation vorzunehmen, sondern die bereits vorhandene amd64-Zahl aus der Feinmessung (Plan 07-03) als Beleg zu verdrahten: der erste Poller-Durchlauf kostete im veroeffentlichten Abbild (eifriger Bau) auf amd64 nativ 575,6 MB und kostet mit dem faulen Bau (Phase 7) noch 0,6 MB, gemessene Ersparnis 575,0 MB. Die Kernbehauptung dahinter ist, dass der eifrige Bau **das tatsaechliche Verhalten aller 1.0.x-Releases** ist, sodass dieser Vorher-Nachher-Vergleich tatsaechlich "1.0.x gegen 1.1" misst, nicht nur "1.1 vor 07-03 gegen 1.1 nach 07-03".

**Diese Kernbehauptung wurde unabhaengig gegen die Git-Historie geprueft, nicht nur gegen die Doku:**

```
git merge-base --is-ancestor 43a1737 v1.0.0   -> true  (v1.0.0 enthaelt shared_model, Plan 06.1-02)
git merge-base --is-ancestor 43a1737 v1.0.3   -> true  (v1.0.3, der juengste 1.0.x-Tag, ebenfalls)
git merge-base --is-ancestor 6dcc0d1 v1.0.3   -> false (v1.0.3 enthaelt den faulen Bau aus Plan 07-03 NICHT)
git merge-base --is-ancestor 6dcc0d1 HEAD     -> true  (main/842f3c8 enthaelt ihn)
git show v1.0.3:backend/src/findling/worker/poller.py | grep _build_the_cutter  -> kein Treffer
```

Damit ist bestaetigt, unabhaengig von jeder SUMMARY-Behauptung: **jeder ausgelieferte 1.0.x-Tag (v1.0.0 bis v1.0.3) hat bereits die geteilte Engine (06.1-02), aber noch den eifrigen Bau von Tokenizer und Splitter.** Der einzige Verhaltensunterschied zwischen "Stand 1.0.x" und "Stand nach Phase 7" ist also genau der faule Bau, den `02-nachmessung-fauler-bau-amd64.txt` misst. Die Rohdatei existiert real und traegt exakt die im Text zitierten Zahlen:

```
20-zweite-spur-verdrahtet   06-poller-importiert -> 20  575.6   (Abschnitt A, eifrig, entspricht 1.0.x)
06-poller-importiert -> 20-zweite-spur-verdrahtet          0.6   (Abschnitt B, faul, entspricht Phase 7)
```

Die geaenderte Passage in `docs/performance.md` (Zeile 3498-3509, gegen den Arbeitsbaum gelesen, noch nicht committet) benennt Quelle, Architektur (amd64 nativ), Rohdatei und die Stelle (Grundlast eines Containers, der nur noch sucht) korrekt und enthaelt keine em-/en-dashes. Die Argumentationskette haelt.

**Ergebnis: SC4 wird von FAILED auf VERIFIED gehoben, Status von `gaps_found` auf `passed`.**

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth (Roadmap-Wortlaut) | Status | Evidence |
|---|---|---|---|
| 1 | Modellgewichte in einem Container sind pro Prozess genau einmal geladen; ein Test kann rot werden und faellt bei einer zweiten Instanz | VERIFIED | `backend/src/findling/embed/engine.py:58` `shared_model()`, Halter `_ENGINE` Zeile 51 (Lock Zeile 55); `backend/src/findling/tools/one_load.py::measure()`/`findings()` zaehlt `wordlist_reads_after_index/search`, `engine_loads_after_search/worker`; CI-Gate `.github/workflows/resilience.yml:1420-1425` "One engine and one constituent list per process" auf `ubuntu-24.04`. Rotbeweise real vorhanden und lauffaehig: `backend/tests/test_one_load.py:188,234,248`. Lokal ausgefuehrt: 191 gezielte Tests gruen, volle Suite 1713 passed/15 skipped/0 failed. |
| 2 | Erste semantische Suche nach Leerlauf haelt p95-Budget 2,5 s, gemessen nicht geschaetzt | VERIFIED | arm64: `docs/performance.md:3262` p95=max=1.332,1 ms, Budget 2.500 ms, `p95_within_budget: true` (Rohdatei `rohdaten/64-stufe-01.json`). amd64: `docs/performance.md:3386` 1.299 ms (sqlite) / 1.392 ms (mysql), CI-Lauf `34221154596` vom 08.09.2026, `integration.yml`/`index-search-e2e`, verifiziert per `gh run list` (Integration = success auf Merge-Commit `842f3c8`). Beide unter der 1,5-s-Aufrufdecke und dem 2,5-s-Budget. |
| 3 | Faellt Engine aus/fehlt Modell, liefert Suche unveraendert Volltexttreffer statt Fehler, Admin sieht Zustand in Diagnose | VERIFIED | Fallback: `backend/src/findling/index/search.py:203-229` `_semantic_documents()` faengt jede Exception im Vektorpfad separat ab und gibt `[]` zurueck, Merge wird Identitaet auf dem Volltext-Ranking (D-19/D-20). Admin-Sichtbarkeit (Plan 07-04 + Audit-Fixes): `embed/engine.py:249-306` `engine_state()`, 5 geschlossene Zustaende `ENGINE_LOADED/COLD/DISABLED/MISSING/RETRY_PENDING`; durchgereicht `api/status.py:184,255,350`; validiert `php/lib/Service/AdminViewService.php:177,1876`; gerendert `php/templates/admin.php:73-74,348` und `php/js/admin.js:299,366,390-415`. Drei neue Gates real vorhanden und gruen (`backend/tests/test_admin_ui_contract.py:480,536,557`). Audit-Fixes bestaetigt am Code: HIGH-1, MEDIUM-2, MEDIUM-5 (D-21). |
| 4 | Speicherunterschied zum Stand 1.0.x ist auf amd64 als Zahl belegt, mit Stelle (Grundlast/Suchphase/Gesamtspitze) | **VERIFIED** (nach Owner-Nachtrag) | `docs/performance.md:3498-3509`: amd64-nativ, 575,6 MB (eifrig, = Verhalten von v1.0.0-v1.0.3, git-verifiziert) gegen 0,6 MB (faul, = Stand nach Phase 7), Ersparnis 575,0 MB, Stelle = Grundlast eines Containers nach dem ersten Poller-Durchlauf. Rohdatei `docs/measurements/2026-09-grundlast-fein/rohdaten/02-nachmessung-fauler-bau-amd64.txt` existiert und traegt exakt diese Zahlen (Zeile 21: `575.6`, Zeile 41: `0.6`). Zusaetzlich weiterhin die arm64-Zahlen (Suchphase -712,6 MB, Gesamtspitze -25,1 MB) und die amd64-Latenzzahl (1.299/1.392 ms) im selben Bericht. |

**Score:** 4/4 Roadmap-Erfolgskriterien verifiziert.

### Requirements Coverage (EFF-01, EFF-02)

| Requirement | Beschreibung | Status | Evidence |
|---|---|---|---|
| EFF-01 | Gemeinsame Embedding-Engine-Instanz, hoechstens einmal pro Prozess geladen | SATISFIED | `docs/performance.md` Abschnitt "Die eine Engine" (Zeile 3132ff.), `load_count()` (`embed/model.py:143`), CI-Tor `resilience.yml:1420`. |
| EFF-02 | Erste semantische Suche nach Leerlauf haelt 2,5-s-p95-Budget, kein Kaltstart-Rueckschritt | SATISFIED | arm64 UND amd64 gemessen; DI-07-01 geschlossen (`deferred-items.md:16-18`, bestaetigt in `docs/performance.md:3386`). |

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `backend/src/findling/embed/engine.py` | `shared_model()`, `engine_state()`, `ENGINE_STATES` | VERIFIED | Existiert, substantiell, verdrahtet, Datenfluss lokal getestet (191 gezielte + 1713 volle Testsuite gruen). |
| `backend/src/findling/embed/model.py` | `load_count()`, `artifacts_present`, `artifacts_absent`, `load_cooling_down` | VERIFIED | Alle vier Symbole vorhanden (`model.py:143,207,368,383`), real genutzt. |
| `backend/src/findling/tools/one_load.py` | siebte Zahl `cold_search_ms`/`cold-search-ms` | VERIFIED | `one_load.py:158-169,320`. |
| `.github/workflows/integration.yml` | amd64-Kaltstartmessung + Strukturtor | VERIFIED | Schritt "cold semantic search over apache..." (Zeile 1709), Wortzahl-Tor (Zeile 1603); Lauf `34221154596` erfolgreich. |
| `docs/measurements/2026-09-grundlast-fein/` | amd64-native + arm64-emulierte Feinmessung | VERIFIED | README + Rohdaten vorhanden, Zahlen intern konsistent, Rohdatei `02-nachmessung-fauler-bau-amd64.txt` traegt exakt die im Bericht zitierten Zahlen. |
| `docs/performance.md`, Abschnitt "Der Stand der Zahlen" | amd64-Zahl fuer Speicherdifferenz zu 1.0.x | VERIFIED | Nachtrag Zeile 3498-3509, gegen Git-Historie unabhaengig gegengelesen (siehe Owner-Entscheid-Abschnitt oben). **Aenderung liegt im Arbeitsbaum, noch nicht committet.** |
| `php/lib/Service/AdminViewService.php` | `engineState()` gegen `ENGINE_STATES` | VERIFIED | `AdminViewService.php:177,1876-1877`; CI-Job "PHP and store metadata gates" gruen auf Merge-Commit. |
| `php/lib/Db/QueueMapper.php::requeueAs` | Dirty-Zeile wird freigegeben statt auf Folgespur geschoben | VERIFIED | Code-Stelle (Zeile 609-660) exakt wie in `07-AUDIT-FIXES.md` beschrieben; Regressionsgate `test_a_dirty_row_is_never_moved_to_the_embedding_track` (`backend/tests/test_queue_client.py:651`) real vorhanden und gruen. |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `api/resources.py::query_model` | `embed/engine.py::shared_model` | direkter Aufruf | WIRED | `resources.py:270` |
| `worker/poller.py::_wire_the_second_track` | `embed/engine.py::shared_model` | `self._model = shared_model()` | WIRED | `poller.py:1491` |
| `embed/engine.py::engine_state` | `api/status.py::StatusResponse.engineState` | Funktionsaufruf | WIRED | `status.py:255` |
| `api/status.py` (JSON) | `php/lib/Service/AdminViewService.php::engineState` | HTTP-Antwortfeld, validiert gegen geschlossene Menge | WIRED | `AdminViewService.php:1813` |
| `AdminViewService` | `php/templates/admin.php` / `php/js/admin.js` | `findling-semantic-engine`, Satzkatalog | WIRED | `admin.php:73-74,348`; `admin.js:390-415` |
| `php/lib/Db/QueueMapper.php::requeueAs` | Embedding-Spur | `dirty`-Flag entscheidet Freigabe statt Uebergabe | WIRED, mit Regressionsgate | `QueueMapper.php:609-660`, Test `test_queue_client.py:651` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|---|---|---|---|---|
| `findling-semantic-engine` (admin.php) | `$engineState` | `AdminViewService::engineState($backend['engineState'])` liest echte HTTP-Antwort des Containers | Ja | FLOWING |
| `cold-search-ms` in `one_load.py`-Report | `cold_search_ms` | `time.perf_counter()` um echten `drive_the_search_side()`-Aufruf | Ja | FLOWING |
| amd64-Kaltstartzeile in `docs/performance.md:3386` | Protokollzeile aus CI-Lauf | `integration.yml` echter `curl` gegen echte Nextcloud/PHP/AppAPI | Ja, mit Lauf-ID referenziert | FLOWING |
| SC4-Speicherzahl amd64 (`docs/performance.md:3505`) | 575,6 MB / 0,6 MB | `docs/measurements/2026-09-grundlast-fein/rohdaten/02-nachmessung-fauler-bau-amd64.txt`, echter Docker-Lauf, `--network none` | Ja, Rohdatei mit Zeitstempel und Image-Digest vorhanden | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Volle Backend-Testsuite laeuft lokal gruen | `uv run pytest -q` (backend) | `1713 passed, 15 skipped, 1 warning in 261.14s` | PASS |
| Phase-7-relevante Suiten gezielt gruen | `uv run pytest -q tests/test_embed_engine.py tests/test_one_load.py tests/test_embedding_track.py tests/test_status_endpoint.py tests/test_admin_ui_contract.py tests/test_queue_client.py` | `191 passed` | PASS |
| `ruff check` auf den geaenderten Kern-Dateien | `uv run ruff check src/findling/embed/engine.py src/findling/embed/model.py src/findling/worker/poller.py src/findling/tools/one_load.py src/findling/api/status.py` | `All checks passed!` | PASS |
| `admin.js` syntaktisch gueltig | `node --check php/js/admin.js` | kein Fehler | PASS |
| Git-Nachweis "eifrig = 1.0.x-Verhalten" | `git merge-base --is-ancestor <commit> <tag>` gegen v1.0.0-v1.0.3 | bestaetigt (siehe Owner-Entscheid-Abschnitt) | PASS |
| PHP-Syntaxpruefung | `php -l ...` | nicht ausfuehrbar (kein PHP im Verifier-Environment) | SKIP (durch CI-Gruenlauf "PHP and store metadata gates" auf `842f3c8` abgedeckt) |

### Probe Execution

Keine dedizierten `scripts/*/tests/probe-*.sh` fuer diese Phase gefunden; stattdessen CI-Gates (`resilience.yml`, `integration.yml`, `measure.yml`) als Aequivalent geprueft.

| CI-Workflow | Commit | Ergebnis | Status |
|---|---|---|---|
| Integration | `842f3c8` (Merge Audit-Fixes) | success (11m11s) | PASS |
| Resilience | `842f3c8` | success (13m5s) | PASS |
| Python gates | `842f3c8` | success (3m21s) | PASS |
| PHP and store metadata gates | `842f3c8` | success (39s) | PASS |
| Multi-arch image | `842f3c8` | success (2m0s) | PASS |
| HaRP deploy | `842f3c8` | success (12m46s) | PASS |
| Integration (vorheriger Lauf) | `14a10d5` | **failure** (11m5s) | dokumentierte Ursache (H4-Regression via `requeueAs`), behoben in `842f3c8` |

Alle sechs Workflows auf dem finalen Phasenstand `842f3c8` gruen, per `gh run list` objektiv nachgepruft. Der eine rote Integrationslauf davor ist im Audit-Fix-Dokument ursaechlich erklaert und die Behebung ist im Code nachvollziehbar (`QueueMapper::requeueAs`) und regressionsgesichert.

Hinweis: Der SC4-Nachtrag in `docs/performance.md` ist zum Zeitpunkt dieser Pruefung im Arbeitsbaum vorhanden, aber noch nicht committet (`git status`: "modified: docs/performance.md"). Dieser Verifier committet nicht; die Aenderung muss vor Phasenabschluss committet werden, sonst ist SC4 im naechsten `main`-Stand wieder unbelegt.

### Anti-Patterns Found

Keine TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER-Marker in den gepruften Phase-7-Dateien. Keine em-/en-dashes in `docs/performance.md` (0/0, inklusive der neuen Passage).

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|---|---|---|
| 1 | DI-07-04: native arm64-Rohmessung der Feinmessung (bisher nur QEMU-emuliert) | Phase 10 | `deferred-items.md:95-122`; Entscheid haengt nicht daran (faellt gegen die native amd64-Zahl, 544,3 MB gegen Schwelle 100 MB), arm64-Emulation liegt nur 1,2 % neben der groben nativen Messung |
| 2 | DI-07-02: 1,5-s-Aufrufdecke vs. 2,5-s-Gruppenbudget, Marge nur 167,9 ms | Phase 10 | `deferred-items.md:43-66` |
| 3 | DI-07-03: bis zu vier Containeraufrufe je Suche durch Rechteabgleich-Schleife | Phase 10 / Phase 11 | `deferred-items.md:69-92` |

DI-07-01 (amd64-Kaltstartzahl) ist geschlossen und bestaetigt im Code. Diese drei bleiben offen und sind korrekt als solche dokumentiert; keiner davon ist ein Blocker fuer den Phasenabschluss.

### Human Verification Required

Keine.

### Gaps Summary

Alle vier Roadmap-Erfolgskriterien der Phase sind jetzt solide erfuellt und am Code nachgewiesen, nicht nur behauptet. Die Ein-Engine-Zusage haelt mit einem echten, rotfaehigen CI-Tor (SC1), die Kaltstartzahl ist auf arm64 UND amd64 gemessen und liegt unter beiden Decken (SC2), der Volltext-Fallback samt Admin-Sichtbarkeit ist Ende-zu-Ende verdrahtet und durch zehn Audit-Befunde zusaetzlich gehaertet (SC3), und der Speicherunterschied zum Stand 1.0.x ist jetzt sowohl auf arm64 als auch auf amd64 nativ mit Rohdaten belegt, mit einer im Owner-Entscheid vom 08.09.2026 sauber begruendeten und gegen die Git-Historie unabhaengig bestaetigten Argumentationskette (SC4). Die lokale Testsuite (1713 Tests) und alle sechs CI-Workflows auf dem finalen Merge-Commit sind gruen.

Einzige verbleibende Auffaelligkeit: `docs/performance.md` traegt den SC4-Nachtrag aktuell nur im Arbeitsbaum, noch nicht committet. Kein inhaltlicher Gap, aber vor Abschluss der Phase zu committen.

---

_Verified: 2026-09-08T14:11:10Z, Nachtrag zum Owner-Entscheid: 2026-09-08_
_Verifier: Claude (gsd-verifier)_
