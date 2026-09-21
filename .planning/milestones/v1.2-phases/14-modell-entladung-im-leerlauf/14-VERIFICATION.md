---
phase: 14-modell-entladung-im-leerlauf
verified: 2026-09-19T18:59:19Z
status: passed
score: 5/5 must-haves verified (MEM-02 code-complete, evidence measurement explicitly deferred to Phase 15 by REQUIREMENTS.md with owner acceptance)
overrides_applied: 0
deferred:
  - truth: "Nach Ablauf der TTL sind beide Speicherhalter frei, belegt an der Messgroesse 'Rueckkehr zur Grundlast nach einem Indexlauf' (MEM-02 Beleg-Messgroesse)"
    addressed_in: "Phase 15"
    evidence: "REQUIREMENTS.md line 65 documents MEM-02 as 'Pending ... der Beleg an der Messgroesse entsteht auf der Box der Phase 15'; ROADMAP.md Phase 14 Owner-Checkpoint section states the same; ROADMAP.md Phase 15 goal is exactly the box measurement run this evidence needs. Code path (main.py::_release_when_idle releasing both poller.release_cutter() and engine release_if_idle()) is built, tested and spot-checked live (14-12-SUMMARY.md Sichtprobe 3: 376.3 MB freed after 75s idle on a libc without malloc_trim). Owner accepted the phase on 19.09.2026 with this exclusion named explicitly."
---

# Phase 14: Modell-Entladung im Leerlauf Verification Report

**Phase Goal:** Der Container gibt nach Leerlauf beide Speicherhalter frei, hinter einem ab Werk ausgeschalteten Schalter, ohne dass die erste Suche danach langsamer wird
**Verified:** 2026-09-19T18:59:19Z
**Status:** passed
**Re-verification:** No , initial verification

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Ein Vorprueflauf weist die tatsaechliche RSS-Rueckgabe (gc.collect + malloc_trim) auf Zielhardware aus, BEVOR die Funktion fertig gebaut wird; ein negatives Ergebnis wird dokumentiert statt ausgeliefert | VERIFIED | `docs/measurements/2026-09-entladung-vorpruefung/skripte/00-ablauf.md` (threshold committed `6387d2d`, 19.09.2026 14:29) precedes `docs/measurements/2026-09-entladung-vorpruefung/README.md` raw data (`64257e0`, 14:58, 29 min later). Result: E1-E4 all held, median RSS return 100.0% on aarch64 target arch against the shipped image (`ghcr.io/.../findling_backend:dev`, digest resolved), 5/5 cycles `trim_rc=1`. Gate 14-02 (`checkpoint:human-verify`) recorded owner answer "freigegeben" 19.09.2026 releasing waves 3-8. |
| 2 | Admin schaltet die Entladung ueber genau eine benannte Umgebungsvariable ein (TTL Sekunden, 0 = aus), ab Werk aus | VERIFIED | `backend/src/findling/config.py`: `EMBED_IDLE_RELEASE_SECONDS = 0` (default off), `EMBED_IDLE_RELEASE_SECONDS_RANGE = (60, 86400)`, reader `_seconds_or_off_from_environment("FINDLING_EMBED_IDLE_RELEASE_SECONDS", ...)` at line 1179-1180 lets 0 through before range check, warns by variable name only on nonsense, never raises. `backend/appinfo/info.xml:467` exposes `FINDLING_EMBED_IDLE_RELEASE_SECONDS` to admins. Live spot-check (14-12-SUMMARY.md Sichtprobe 2) confirmed three positions (unset / 60 / invalid 3) behave as specified on a running instance. |
| 3 | Nach Ablauf der TTL sind beide Speicherhalter frei (Embedding-Engine UND Poller-Cutter/Tokenizer), Messgroesse "Rueckkehr zur Grundlast nach einem Indexlauf" | VERIFIED (code), deferred (box evidence) | `backend/src/findling/main.py::_release_when_idle` (line 254) runs as third lifespan task, calls `release_if_idle()` (embed engine) and, only behind a release that actually happened, `poller.release_cutter()` (line 296-311); guarded by `poller.busy` and per-batch `_in_flight` counters so no release happens mid-run. All blocking calls (`gc.collect`, `malloc_trim`) go through `asyncio.to_thread`, verified by AST-level test `test_every_blocking_call_of_the_tick_runs_in_a_worker_thread`. Live spot-check: real search loaded engine to 533.4 MB RSS, 75s later `engineState=unloaded` and RSS 157.2 MB (376.3 MB / 70.5% freed on a machine WITHOUT malloc_trim). Metric name "Rueckkehr zur Grundlast nach einem Indexlauf" is fixed in `docs/performance.md` with explicit rejection of the forbidden alternative "Grundlast minus X". The measured proof against that exact metric is intentionally deferred to the Phase 15 box run , REQUIREMENTS.md and ROADMAP.md both document this exclusion by name, and the owner's phase acceptance explicitly excludes MEM-02. This is a documented deferral, not a gap. |
| 4 | Die erste Suche nach einer Entladung liefert innerhalb der 1,5-Sekunden-Decke lexikalische Treffer und waermt das Modell im Hintergrund nach | VERIFIED | `embed/engine.py::query_may_load()` gates on the switch; `index/search.py`, `api/search.py`, `api/snippets.py` thread `may_load` through `SemanticSide`/`QueryEmbedder`; `api/search.py::search` fires `asyncio.create_task(asyncio.to_thread(warm))` after answering. `api/diagnose.py` deliberately keeps loading (written justification at line 212). Four new ACL-parity test cases added in 14-12 close a gap where the degraded round could bypass the ACL prefilter (`test_a_degraded_round_gives_a_user_without_a_permission_row_nothing`, `test_a_degraded_round_hands_out_exactly_the_permitted_documents`, `test_the_degraded_round_asks_the_prefilter_as_often_as_the_ordinary_one`, `test_the_php_recheck_knows_nothing_about_the_switch`), all present and passing. Live spot-check: cold search 1.369-1.438s (below 1.5s ceiling but thin margin of 60-130ms, reported to and accepted by owner), warm search 0.406-0.483s, engine returns to `loaded` after warm-up without a second search. No cURL error 28 recurrence during the check window. |
| 5 | Die Admin-Seite zeigt den Engine-Zustand nach der neu formulierten one_load-Zusage, und das Gate prueft genau diese Zusage | VERIFIED | Sixth word `unloaded`: `embed/engine.py:125,139` (`ENGINE_UNLOADED`, `ENGINE_STATES` frozenset), mirrored in `php/lib/Service/AdminViewService.php:180`, rendered identically in `php/templates/admin.php:80` and `php/js/admin.js:452`; all six catalog files (`de.json`, `de.js`, `de_DE.json`, `de_DE.js`, `fr.json`, `fr.js`) carry the new sentence key (verified by grep, all six hit). `docs/admin-page.md` state table updated with the 7th row (silent-container line). New promise "never two engines at once, exactly one load per warm window" reformulated at three matching locations: `tools/one_load.py` module head, `findings()` (line 406+), and `.github/workflows/resilience.yml` explainer text (line 1406+). Gate verified red-capable via 5 mutation test cases in `test_one_load.py` (`test_it_goes_red_when_a_release_leaves_two_engines_behind`, `test_it_goes_red_when_the_warm_up_loads_twice`, etc.). French wording accepted unchanged by owner (native speaker) 19.09.2026. |

**Score:** 5/5 truths verified (1 with an explicitly documented, owner-accepted deferral of its box-measurement evidence to Phase 15 , not a gap of this phase per task instructions).

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | MEM-02 evidence measurement at the metric "Rueckkehr zur Grundlast nach einem Indexlauf" | Phase 15 | `.planning/REQUIREMENTS.md` line 65: "Pending ... der Beleg an der Messgroesse entsteht auf der Box der Phase 15. Die Abnahme der Phase am 19.09.2026 schliesst dieses Requirement ausdruecklich NICHT ein". `.planning/ROADMAP.md` Phase 14 Owner-Checkpoint section repeats this exclusion by name. Code and unit/live-instance spot-check evidence exist now (see truth 3 above); only the box-measured metric proof is deferred. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `docs/measurements/2026-09-entladung-vorpruefung/skripte/00-ablauf.md` | Pre-registered E1-E4 thresholds | VERIFIED | Present, committed before raw data, contains E1-E4 |
| `docs/measurements/2026-09-entladung-vorpruefung/README.md` | Verdict report with raw numbers | VERIFIED | Present, judged 100.0% median return, "Gehalten" |
| `.github/workflows/measure.yml` | Step E "RSS returned by a release" on both matrix legs | VERIFIED | Confirmed present and run (measure.yml run 35443822228) |
| `backend/src/findling/config.py` | `embed_idle_release_seconds` field + reader + constants | VERIFIED | `EMBED_IDLE_RELEASE_SECONDS`, `_RANGE`, `_seconds_or_off_from_environment`, field at line 784 |
| `backend/appinfo/info.xml` | `FINDLING_EMBED_IDLE_RELEASE_SECONDS` documented for admins | VERIFIED | Line 467 |
| `backend/src/findling/worker/poller.py` | `busy` property + `release_cutter()` | VERIFIED | Lines 479, 1694; guarded by `self.busy` at 1723 |
| `backend/src/findling/embed/model.py` | `release()`, `_UNLOAD_COUNT`, `unload_count()`, `may_load`, `_last_use`, `_in_flight`, `malloc_trim` | VERIFIED | All present with expected ordering (gc.collect before malloc_trim, guarded for OSError/AttributeError) |
| `backend/src/findling/embed/engine.py` | `query_may_load()`, `release_if_idle()`, `warm()`, `warm_wanted()`, `released_count()`, `ENGINE_UNLOADED` | VERIFIED | All present, wired to `settings()` and `model.py::release` |
| `backend/src/findling/main.py` | `_release_when_idle` third lifespan task | VERIFIED | Present at line 254, calls both holders through `asyncio.to_thread`, stop-event checked twice per tick |
| `backend/src/findling/api/search.py`, `api/snippets.py` | `may_load`/`query_may_load` wiring + warm trigger | VERIFIED | Both routes import and use `query_may_load`; `search.py` fires `create_task(to_thread(warm))` |
| `backend/src/findling/api/diagnose.py` | Written justification for continuing to load | VERIFIED | Comment at line 212 |
| `backend/src/findling/tools/one_load.py` | Fourth phase (unload/rewarm), two new report fields | VERIFIED | `engine_unloads_after_release`, `engine_loads_after_rewarm` present, `findings()` logic present |
| `.github/workflows/resilience.yml` | Updated explainer text for new promise | VERIFIED | "warm window" wording present at line 1406+ |
| `php/lib/Service/AdminViewService.php`, `templates/admin.php`, `js/admin.js` | Sixth state `unloaded` mirrored on both halves | VERIFIED | All three contain `unloaded` with matching sentence key |
| `php/l10n/{de,de_DE,fr}.{json,js}` | Six catalog files carry new sentence | VERIFIED | All six confirmed via grep |
| `docs/admin-page.md`, `docs/embeddings.md`, `docs/performance.md`, `docs/runbook-messbox.md` | Admin/measurement/runbook documentation | VERIFIED | All contain the switch name and/or the fixed metric name; forbidden alternative wording explicitly rejected in `performance.md` |
| `docs/audits/2026-09-phase-14/README.md` | Audit report, ASVS V5/V7/V12, bug/perf pass, 5 success criteria with evidence | VERIFIED | 383-line report present, independently re-run gate numbers match (see below) |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `.github/workflows/measure.yml` | measurement scripts dir | `docker run -v ...:/skripte:ro` | VERIFIED | Confirmed in 14-02 raw run 35443822228 |
| `backend/appinfo/info.xml` | `config.py` | identical variable name | VERIFIED | `FINDLING_EMBED_IDLE_RELEASE_SECONDS` byte-identical at both locations |
| `poller.py::release_cutter` | `poller.py::_build_the_cutter` | lazy rebuild pair | VERIFIED | `_chunker`/`_model` reset together, AST-gated (`test_...` at line 3022) |
| `model.py::release` | `malloc_trim(0)` | gc.collect then trim, in order | VERIFIED | Order confirmed at lines around 634-672 |
| `model.py::_embed` | `self._last_use` | one line covers search + index track | VERIFIED | Line 533 |
| `engine.py::release_if_idle` | `model.py::release` | holder asks the clock, holder itself releases | VERIFIED | Confirmed by reading `release_if_idle` body |
| `engine.py::query_may_load` | `config.py::settings` | `embed_idle_release_seconds` decides | VERIFIED | `return settings().embed_idle_release_seconds == 0` |
| `main.py::_release_when_idle` | `engine.py::release_if_idle` | `asyncio.to_thread`, never on the loop | VERIFIED | Line 310 |
| `main.py::_release_when_idle` | `worker/poller.py::busy` | second condition | VERIFIED | Line 296 |
| `api/search.py` | `embed/engine.py::query_may_load` | rule asked, not repeated | VERIFIED | Line 303 |
| `api/search.py::search` | `embed/engine.py::warm` | `create_task(to_thread(warm))` after response round | VERIFIED | Line 388 |
| `php/templates/admin.php` | `php/js/admin.js` | word-identical state-to-sentence mapping | VERIFIED | Both map `unloaded` to the same English source string; test `test_both_halves_of_the_page_map_the_same_state_to_the_same_sentence` present in `test_admin_ui_contract.py` |
| `embed/engine.py::ENGINE_STATES` | `test_admin_ui_contract.py` | gate imports the container's set | VERIFIED | `from findling.embed.engine import ENGINE_STATES`, `assert set(template) == set(ENGINE_STATES)` |
| `tools/one_load.py::findings` | `embed/model.py` | `load_count`/`unload_count` as difference | VERIFIED | Both counters read and diffed at lines 349-399 |

### Data-Flow Trace (Level 4)

Not applicable in the classic sense (no React/frontend rendering pipeline) , this is a backend/PHP admin-page feature. Data flow was instead traced end-to-end via the live-instance spot checks recorded in 14-12-SUMMARY.md: a real search loaded the engine (RSS 533.4 MB), the idle tick released it after 75s (RSS 157.2 MB, `engineState` flips to `unloaded`), and the admin page rendered the exact sentence tied to that state from the shared catalog key. This is a genuine, measured, non-hardcoded data path, not a stub.

### Behavioral Spot-Checks (independently re-run by this verifier)

| Behavior | Command | Result | Status |
|---|---|---|---|
| Lint clean | `uv run ruff check .` (backend/) | "All checks passed!" | PASS |
| Format clean | `uv run ruff format --check .` | "123 files already formatted" | PASS |
| Types clean | `uv run pyright` | "0 errors, 0 warnings, 0 informations" | PASS |
| Dead code clean | `uv run vulture src tests --min-confidence 80` | no output | PASS |
| Full test suite | `uv run pytest -q` | "2262 passed, 15 skipped, 1 warning in 215.80s" | PASS , matches the number claimed in `docs/audits/2026-09-phase-14/README.md` and 14-12-SUMMARY.md exactly |
| No debt markers in phase-touched files | `grep -n -E "TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER"` across all 14 phase-modified source files | no matches | PASS |

### Probe Execution

No dedicated `scripts/*/tests/probe-*.sh` files are declared by this phase's plans, and none exist under that convention in this repository for this feature area (the phase's own gate is the `.github/workflows/resilience.yml` `one_load` tool and `measure.yml`, both of which are CI-only and require Docker/GHA runners that are out of scope for a local re-run). Step 7c: SKIPPED , no locally runnable probe scripts declared or found; CI-only gates (`measure.yml`, `resilience.yml`) were instead verified by reading their already-executed run artifacts (`docs/measurements/2026-09-entladung-vorpruefung/README.md`, `docs/audits/2026-09-phase-14/README.md`) referencing specific GitHub Actions run IDs and commit SHAs.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| MEM-01 | 14-03 | Single named env var, TTL seconds, 0=off, off by default | SATISFIED | `config.py`, `info.xml`, live 3-position spot check |
| MEM-02 | 14-04 to 14-07, 14-11 | Both memory holders freed, measured at "return to baseline after an index run" | CODE SATISFIED / EVIDENCE DEFERRED to Phase 15 (per REQUIREMENTS.md and ROADMAP.md, owner-accepted exclusion , not a gap of this phase) | `main.py::_release_when_idle`, `poller.py::release_cutter`, `model.py::release`; live spot-check showed 376.3 MB freed (70.5%) on a libc without malloc_trim, explicitly named as "a hint, not proof at the metric" |
| MEM-03 | 14-05, 14-08 | First search after unload answers lexically within 1.5s, warms in background | SATISFIED | `embed/model.py::may_load`, `api/search.py` warm trigger, live spot-check 1.369-1.438s cold vs 1.5s ceiling |
| MEM-04 | 14-01, 14-02 | Pre-check proves actual RSS return before the feature is finished, negative result would be documented instead of shipped | SATISFIED | `docs/measurements/2026-09-entladung-vorpruefung/README.md`, gate 14-02 owner "freigegeben" |
| MEM-05 | 14-09, 14-10 | one_load promise reformulated, admin page shows state, gate checks exactly this promise | SATISFIED | `ENGINE_UNLOADED`, admin page both halves, `tools/one_load.py` fourth phase + 5 mutation tests, owner-decided wording (Zweig B) |

No orphaned requirements: `.planning/REQUIREMENTS.md` maps exactly MEM-01 through MEM-05 to Phase 14, and all five appear in at least one plan's `requirements:` frontmatter field (14-01/14-03/14-04/14-05/14-06/14-07/14-08/14-09/14-10/14-11/14-12).

### Anti-Patterns Found

None. No `TBD`, `FIXME`, `XXX`, `TODO`, `HACK`, or `PLACEHOLDER` markers found in any of the 14 phase-modified source files. No empty stub implementations, no hardcoded-empty return values feeding rendered output. The one "known stub" noted in 14-03-SUMMARY.md (`embed_idle_release_seconds` unread at that point in the sequence) is explicitly a deliberately staged, sequential build across waves , it is read by 14-06/14-07 later in the same phase, and this is documented as intentional rather than a gap.

### Human Verification Required

None outstanding. The phase's own workflow already routed all human-judgment items through an owner checkpoint that has concluded:

- The Phase 14 gate (14-02, MEM-04 pre-check) was decided by the owner ("freigegeben", 19.09.2026).
- The phase acceptance checkpoint (14-12) was decided by the owner ("abgenommen", 19.09.2026), including explicit sign-off on: the French wording (native speaker), the thin 1.5s margin (60-130ms) being visible before acceptance, and the 900s suggested-default wording.
- The engineState word-choice checkpoint (MEM-05, Zweig B `unloaded`) was decided by the owner on 19.09.2026 (documented in `14-CONTEXT.md`).

The one item worth flagging for awareness rather than as a blocking gap: the live spot-check margin on the 1.5-second ceiling (1.369s-1.438s measured, i.e. 60-130ms under the ceiling) is thin on the development machine used for the spot-check. This was reported to and explicitly accepted by the owner as part of the 14-12 checkpoint rather than being an unresolved risk; it is noted here for visibility into Phase 15's box measurement, not as an open question of this phase.

### Gaps Summary

No blocking gaps found. All artifacts required by the PLAN frontmatter across 14-01 through 14-12 exist, are substantive (not stubs), and are wired end-to-end (config → engine → lifespan task → API routes → admin UI → CI gates). The full backend test suite (2262 passed, 15 skipped) and all four quality gates (ruff check, ruff format, pyright, vulture) were independently re-run by this verifier and match the numbers claimed in the phase's own audit report exactly, which increases confidence that the audit report was not narrated but genuinely executed.

The only requirement not fully closed by this phase is MEM-02's measurement-metric evidence, and that is by explicit design: `.planning/REQUIREMENTS.md` and `.planning/ROADMAP.md` both name Phase 15's paid box run as the location where that evidence is produced, and the phase-14 owner acceptance explicitly excludes it. Per this verification's instructions, that is correct and not treated as a gap of Phase 14.

---

*Verified: 2026-09-19T18:59:19Z*
*Verifier: Claude (gsd-verifier)*
