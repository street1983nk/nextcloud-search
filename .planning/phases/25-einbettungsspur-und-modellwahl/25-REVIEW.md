---
phase: 25-einbettungsspur-und-modellwahl
reviewed: 2026-09-28T14:10:20Z
depth: standard
files_reviewed: 65
files_reviewed_list:
  - backend/src/findling/api/resources.py
  - backend/src/findling/api/status.py
  - backend/src/findling/config.py
  - backend/src/findling/embed/engine.py
  - backend/src/findling/embed/model.py
  - backend/src/findling/embed/weights.py
  - backend/src/findling/index/writer.py
  - backend/src/findling/lane.py
  - backend/src/findling/main.py
  - backend/src/findling/memory_guard.py
  - backend/src/findling/nc/client.py
  - backend/src/findling/nc/queue.py
  - backend/src/findling/precision.py
  - backend/src/findling/profile.py
  - backend/src/findling/store/vectors.py
  - backend/src/findling/tools/one_load.py
  - backend/src/findling/worker/embedding.py
  - backend/src/findling/worker/poller.py
  - backend/tests/conftest.py
  - backend/tests/test_acl_prefilter.py
  - backend/tests/test_admin_ui_contract.py
  - backend/tests/test_config.py
  - backend/tests/test_embed_engine.py
  - backend/tests/test_embed_model.py
  - backend/tests/test_embedding_runner.py
  - backend/tests/test_embedding_track.py
  - backend/tests/test_index_writer.py
  - backend/tests/test_instance_marker.py
  - backend/tests/test_lifecycle.py
  - backend/tests/test_main_lifespan.py
  - backend/tests/test_measurement_scripts.py
  - backend/tests/test_memory_guard.py
  - backend/tests/test_one_load.py
  - backend/tests/test_poller.py
  - backend/tests/test_precision.py
  - backend/tests/test_precision_wiring.py
  - backend/tests/test_profile.py
  - backend/tests/test_profile_wire.py
  - backend/tests/test_queue_client.py
  - backend/tests/test_readonly_gate.py
  - backend/tests/test_semantic_search.py
  - backend/tests/test_status_endpoint.py
  - backend/tests/test_track_connections.py
  - backend/tests/test_upgrade_compatibility.py
  - backend/tests/test_v13_ablauf.py
  - backend/tests/test_vector_store.py
  - backend/tests/test_weights.py
  - docs/admin-page.md
  - docs/embeddings.md
  - docs/measurements/2026-09-fp32-speicher/README.md
  - docs/measurements/2026-09-fp32-speicher/release-notes.md
  - docs/measurements/2026-09-fp32-speicher/skripte/01-fp32-speicher.py
  - docs/profiles.md
  - php/js/admin.js
  - php/lib/Controller/ProfileController.php
  - php/lib/Controller/QueueController.php
  - php/lib/Db/QueueMapper.php
  - php/lib/Service/AdminViewService.php
  - php/lib/Service/QueueService.php
  - php/lib/Service/SettingsService.php
  - php/templates/admin.php
  - php/tests/Unit/AdminViewServiceTest.php
  - php/tests/Unit/ProfileControllerTest.php
  - php/tests/Unit/QueueControllerTest.php
  - php/tests/Unit/QueueServiceTest.php
findings:
  critical: 0
  warning: 4
  info: 4
  total: 8
status: fixed
---

# Phase 25: Code Review Report

**Reviewed:** 2026-09-28
**Depth:** standard
**Files Reviewed:** 65
**Status:** fixed (all four warnings fixed on 2026-09-28: WR-01 in 00ecee3, WR-02 in 25ec895, WR-03 in 8ca5983, WR-04 in be2779c; the four Info items stay as noted)

## Summary

Reviewed the embedding lane and model precision work of phase 25 end to end:
the lane claim filter with echo (`lane.py`, `nc/queue.py`, `nc/client.py`, PHP
`QueueController`/`QueueService`/`QueueMapper`), the precision state machine
(`precision.py`), the fp32 procurement (`embed/weights.py`,
`fetch_release_asset`), the EmbeddingTrack as owner with connections of its own
and the EmbedRunner as second driver (`worker/embedding.py`,
`worker/poller.py`), the swap of the engine (`embed/engine.py`,
`embed/model.py`), the memory guard (`memory_guard.py`, `profile.py`,
`config.py`), the lifespan wiring (`main.py`), the status fields
(`api/status.py`, `api/resources.py`, `store/vectors.py`), the admin line
(PHP `AdminViewService`, `admin.php`, `admin.js`) and the fp32 measurement.
The focus areas of the mandate were traced through the code rather than
assumed:

- **Concurrency (two writers under WAL, track lock, swap at lane boundary):**
  the track opens state and vector connections of its own; both drivers take
  rows only under `EmbeddingTrack.lock`; the runner re-checks the level behind
  the lock and again per row; the poller waits for the runner to park before
  an Economy claim (`_runner_parked`, 60 s against a ~18 s round); every
  SQLite error inside a pass or a round hands the held rows back unjudged
  (`ROUND_PAUSED_STORE_ERROR`, runner `_work` catch). The engine swap runs
  under the track lock, in a step without a row in work, holder first and
  release second with a bounded retry (`_let_go_of`). No deadlock found: the
  lock ordering is strictly track-lock -> thread hop, never the reverse.
- **Fail-closed paths:** every procurement outcome ends on int8
  (`end_procurement(succeeded=False)` -> `fp32_unavailable`; no retry until
  int8-then-fp32, pinned by `test_precision.py`); an unreadable headroom is
  never admitted (`memory_guard.admits`); unknown hardware leaves
  `embed_lane_fits` False; a missing echo is sticky
  (`lane.note_refused`, T-25-16); a mark on fp32 without a verified file
  settles on int8 and the drift chain re-embeds with int8 rather than
  answering out of an unreachable stock. Two deviations from the fail-closed
  promises are WR-01 and WR-03 below.
- **PHP trust boundary:** `rejectForeignCaller()` is the first statement of
  every route of `QueueController` and `ProfileController`; every 500 answer
  is a static sentence with the exception in its own log field, never in the
  body; the lane is validated against the closed `QueueService::LANES` before
  the database; the lane echo travels in the answer so a 1.3 companion is
  recognisable by its absence; `AdminViewService` judges `precisionActive`
  against a closed two-word list and `reembedRunning` as a strict boolean, and
  the model name on the page is built on the PHP side out of one of two words
  (T-25-14). The digest and length pins of the release asset match between
  `weights.py`, the Dockerfile documentation in the measurement README and the
  release notes; `fetch_release_asset` carries no AppAPI credential, follows
  redirects by hand against a two-host https allowlist and clears cookies per
  hop.

No Critical issue was found. Four Warnings: a lost `note_active` after an
aborted drift chain that can later tear down an active fp32 under Economy, a
lane mode that stays "parallel" on the runner's failure paths, an exception
that escapes the "never an exception" contract of `procure_fp32`, and a 470 MB
fp32 file with no removal path when it was downloaded but never activated.
Four Info items concern lifespan hygiene, a stale docstring, lock scope and a
long-held verification lock.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: `note_active` is lost when the drift chain aborts after the engine swap; a later Economy round then tears down an active fp32 and deletes the weights

**FIXED in 00ecee3** (fix(25): WR-01 report the weights switch at the swap, not through the mark step return).

**File:** `backend/src/findling/worker/embedding.py:906-910, 929-942, 1056-1074`
**Issue:** `_answer_the_vector_drift` runs the chain as forget_all -> cursor ->
mark -> `_swap_the_engine(switch, ...)` -> `_next_backlog_band(store, ...)`.
The band read is a SQLite query on the same state database a second writer is
using; if it throws (for example `database is locked` past the 10 s busy
timeout, exactly the two-writer case this phase introduces),
`_vector_mark_step` swallows the exception and returns `([], None)`, so
`keep_the_vector_stock_in_step` never calls `note_active(switched)` although
the swap already happened. From then on `precision._ACTIVE` stays `INT8` while
the holder runs fp32, and it can never be repaired inside this process: every
later step finds `held == target` (`fp32`), so `switch` is always None and
`note_active` is never reached again. Consequences: (a) `/status` reports
`precisionActive: int8` for a container that computes fp32 vectors
(`_model_report` reads `state.active` once settled); (b) when the effective
level later drops to Economy (or the box shrinks), `decide()` walks the
`_ACTIVE is INT8` branch into `_decide_fp32`, sets
`_FAILURE = fp32_not_in_economy` and answers target int8; the mark step then
sees held fp32 against target int8, runs the full drift chain, empties the
stock and `remove_fp32_weights` deletes the 470 MB file. That is exactly the
teardown D-25-03/D-25-10 rule out ("an active fp32 stays until the key says
int8, also under economy"). A restart repairs the state (settle from mark plus
verified file), but the teardown, once triggered, is not undone by a restart.
**Fix:** report the switch where it happens instead of through the return
value, so an abort behind the swap cannot lose it:
```python
# in _answer_the_vector_drift, directly after the swap:
if switch is not None:
    self._swap_the_engine(switch, settings().models_dir)
    note_active(switch)   # the holder and the mark agree at this line
    LOGGER.warning(...)
```
and drop the `switched` half of the tuple (or keep it and make
`note_active` idempotent at both sites). A test that stages a throwing
`indexed_file_ids` after a precision switch would pin it.

### WR-02: The embed runner leaves the lane mode on "parallel" on its failure paths, so the status lies and the poller keeps filtering to the index lane

**FIXED in 25ec895** (fix(25): WR-02 hand the lane back to the loop when a runner round fails).

**File:** `backend/src/findling/worker/embedding.py:1425-1440, 1410-1413`; reader at `backend/src/findling/worker/poller.py:764`
**Issue:** `_round` publishes `lane.note_mode(MODE_PARALLEL, REASON_NONE)`
before the claim. Two ways out of the round do not go through `_park`: a claim
that answers `unavailable` (`return ROUND_GATEWAY_UNAVAILABLE`, line
1438-1440) and every unexpected exception, which `run()` catches at line
1410-1413 (including a failure of `self._open()`, whose `client_factory` can
throw before a queue exists). In both cases the module state keeps saying
`mode == parallel` while nothing runs, for the whole backoff (up to
`EMBED_RUNNER_BACKOFF_MAX_SECONDS = 300 s` per cycle). Two consequences: the
status page and the lane report show a parallel lane that is not running, and
the poller keeps claiming `LANE_INDEX` (poller.py:764) based on the stale
mode, so embed rows are claimed by nobody for as long as the runner keeps
failing while the poller keeps working (the runner has a client and a pool of
its own, so the two can diverge). `test_embedding_runner.py` pins the mode
after a worked round and after every parked reason, but no test covers the
unavailable or the exception path.
**Fix:** treat both paths as a park of their own:
```python
if claim.unavailable:
    self._back_off()
    lane.note_mode(lane.MODE_INLINE, lane.REASON_NONE)  # or a named reason
    return ROUND_GATEWAY_UNAVAILABLE
```
and in `run()`'s except branch reset the mode the same way (or move the
`note_mode(MODE_PARALLEL, ...)` to after a successful, honoured claim). If a
new reason word is added, it has to join `lane.REASONS` and the page contract.

### WR-03: `procure_fp32` can raise although its module promises "every failure is a value, never an exception"

**FIXED in 8ca5983** (fix(25): WR-03 map the seal and the close of a download to an outcome, never an exception). The fsync maps ENOSPC to NO_ROOM and every other OSError to UNAVAILABLE; the close of the sink is suppressed on every way out; pinned by three tests in `test_weights.py`.

**File:** `backend/src/findling/embed/weights.py:243-266, 288-291` (contract at lines 24-25 and 269)
**Issue:** in `_download` only the `fetch(...)` call sits inside the
`except Exception` branch. `await asyncio.to_thread(_seal, sink)` (flush plus
`os.fsync`) and the `sink.close()` of the outer `finally` are not mapped to an
outcome: an `OSError` there (ENOSPC at fsync is a realistic case for an app
whose own scenario is the tight volume; the free-space precheck happens before
470 MB are written, not after) propagates through `procure_fp32`, whose
`try/finally` has no `except`. The one production caller,
`EmbeddingTrack._procure`, compensates with a blanket `except Exception` and
logs "ended in an unexpected ...", so today the state machine still ends on
`fp32_unavailable` and the `.part` is dropped by the `finally`. But the
module-level contract ("Every failure is a value out of PROCURE_OUTCOMES,
never an exception the caller has to know", D-25-04) is broken for exactly the
failure class the NO_ROOM outcome exists for, and any second caller (a future
occ tool, a test that calls `procure_fp32` directly) inherits the crash.
**Fix:** map the seal and the close to UNAVAILABLE inside `_download`:
```python
try:
    await asyncio.to_thread(_seal, sink)
except OSError as error:
    _log_unavailable(error)
    return UNAVAILABLE
finally:
    with contextlib.suppress(OSError):
        sink.close()
```
(keeping the close for the happy path as well), and a test that lets the sink
throw at fsync pins the outcome.

### WR-04: A downloaded but never activated fp32 file has no removal path; choosing int8 only deletes the weights when fp32 was active

**FIXED in be2779c** (fix(25): WR-04 remove a downloaded but never activated fp32 file on the way back to int8). The state machine records the way back of the key (`precision.withdrawal_pending`), and the mark step removes the file once the key stands on int8, the holder runs int8 and no fetch is writing it; a sideloaded file under a standing fp32 wish is never touched (D-25-06). Pinned in `test_precision.py` and by three cases in `test_precision_wiring.py`.

**File:** `backend/src/findling/embed/weights.py:191-203`; only call site `backend/src/findling/worker/embedding.py:1217-1230`; refusal branch `backend/src/findling/precision.py:194-199`
**Issue:** `remove_fp32_weights` is reachable through exactly one path:
`_swap_the_engine` with `leaving_fp32 = engine_precision() == "fp32" and
target is INT8`. That condition is only true when fp32 was actually active.
The sequence "admin chooses fp32 under Standard, the 470 MB download
completes, the effective level is or becomes Economy before the next mark
step" ends with `_decide_fp32` refusing the activation
(`fp32_not_in_economy`, D-25-10) while the verified file already sits under
`models/`. When the admin then withdraws the choice with int8, the holder was
never fp32, no swap happens, and the file stays on the volume forever; the
same holds when the download completes after the key already went back to
int8 (the running fetch is not cancelled and `os.replace` installs the file).
470 MB of dead weight sit on a volume whose free-space floor is 500 MB and
whose target boxes are 4-8 GB, and `docs/embeddings.md` (section 11, the way
back) promises that going back to int8 removes the file, "auch eine von Hand
abgelegte". The docstring of `remove_fp32_weights` ("a file nobody uses is
470 MB on the volume for nothing") states the intent that this path misses.
**Fix:** delete the unused file where the withdrawal is observed, not only
where the engine swaps. The cheapest correct place is the mark step: when the
chosen precision is int8, the holder is int8 and no procurement is running,
call `remove_fp32_weights(models_dir)` once (it is idempotent and answers
whether anything was there). Alternatively cancel `self._procurement` in
`note_chosen_precision`-adjacent track code when the key goes back to int8.
Either way `docs/embeddings.md` and the behaviour have to say the same thing.

## Info

### IN-01: The lifespan starts four tasks before its try/finally begins, and the rebuild question at startup is unguarded

**File:** `backend/src/findling/main.py:873-986`
**Issue:** between `asyncio.create_task(_POLLER.run(...))` (line 873) and the
`try:` at line 988 the lifespan runs plain awaits: the reconcile/release task
creation, the enable mark read and `await _start_the_rebuild_if_due()` (line
986). Unlike the same call in `enabled_handler` (wrapped in
`except Exception`, lines 316-320), this one is bare; an exception there (or
in `default_reconcile()`/`settings()` in between) aborts the lifespan without
ever reaching the `finally`, leaving the created tasks running and the module
globals set while the ASGI startup fails. Low likelihood (the callees catch
their own realistic failures), but the guarded twin one screen up shows the
intended shape.
**Fix:** wrap the startup rebuild call like the enable handler does, or move
the task creation inside the `try`.

### IN-02: Stale docstring reference to `_embed_document` in the one-load gate

**File:** `backend/src/findling/tools/one_load.py:338-341`
**Issue:** the docstring of `drive_the_second_track` says "`_embed_document`
reads exactly these three on every row"; the method was renamed and moved to
`EmbeddingTrack._embed` in plan 25-07. The wiring the tool drives is correct,
only the name in the sentence is from before the move.
**Fix:** rename the reference to `EmbeddingTrack._embed`.

### IN-03: The runner holds the track lock across a network call

**File:** `backend/src/findling/worker/embedding.py:1432-1456`
**Issue:** `_round` takes `self._track.lock` and then awaits `queue.claim(...)`
inside it, so the poller's idle mark step (and, in a mixed moment, an inline
embed row) waits behind a companion round trip, including its timeout when the
companion is slow. Not a deadlock (the lock ordering is one-way) and the
poller's idle pass has nothing urgent, but the docstrings around the lock say
"held while a row is embedded and while the mark step runs" and do not name
the claim; either claim outside the lock (re-checking the level behind it, as
the code already does) or a sentence at the lock naming the widened scope
would keep the next reader from narrowing it wrongly.
**Fix:** comment or narrow; behaviour today is correct.

### IN-04: `fp32_verified` hashes 470 MB while holding the verdict lock

**File:** `backend/src/findling/embed/weights.py:146-160`
**Issue:** the sha256 over the whole file runs inside `_VERDICT_LOCK`
(a `threading.Lock`), so a concurrent `_remember_verified` from the
procurement task, or a second verifier thread, blocks for the seconds the hash
takes on the target box. All current callers verify under the track lock
anyway, so this costs nothing today; it is worth a line because the lock
protects a one-entry dict and the hash does not need it.
**Fix:** compute the digest outside the lock and double-check the key before
writing the verdict, or leave it and say so at the lock.

---

_Reviewed: 2026-09-28T14:10:20Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
