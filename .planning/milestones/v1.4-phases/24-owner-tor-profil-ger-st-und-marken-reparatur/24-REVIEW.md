---
phase: 24-owner-tor-profil-ger-st-und-marken-reparatur
reviewed: 2026-09-28T00:00:00Z
depth: standard
files_reviewed: 31
files_reviewed_list:
  - backend/appinfo/info.xml
  - backend/src/findling/api/status.py
  - backend/src/findling/config.py
  - backend/src/findling/hardware.py
  - backend/src/findling/main.py
  - backend/src/findling/nc/client.py
  - backend/src/findling/nc/queue.py
  - backend/src/findling/profile.py
  - backend/src/findling/store/vectors.py
  - backend/src/findling/worker/poller.py
  - backend/tests/conftest.py
  - backend/tests/test_acl_prefilter.py
  - backend/tests/test_config.py
  - backend/tests/test_embedding_track.py
  - backend/tests/test_hardware.py
  - backend/tests/test_info_xml_defaults.py
  - backend/tests/test_main_lifespan.py
  - backend/tests/test_measurement_scripts.py
  - backend/tests/test_poller.py
  - backend/tests/test_profile.py
  - backend/tests/test_profile_wire.py
  - backend/tests/test_queue_client.py
  - backend/tests/test_status_endpoint.py
  - backend/tests/test_upgrade_compatibility.py
  - backend/tests/test_vector_store.py
  - docs/admin-page.md
  - docs/embeddings.md
  - docs/profiles.md
  - php/lib/Controller/ProfileController.php
  - php/lib/Service/SettingsService.php
  - php/tests/Unit/ProfileControllerTest.php
findings:
  critical: 0
  warning: 2
  info: 6
  total: 8
status: issues_found
---

# Phase 24: Code Review Report

**Reviewed:** 2026-09-28
**Depth:** standard
**Files Reviewed:** 31
**Status:** issues_found

## Summary

Reviewed the six plans of phase 24 end to end: the embedding mark with weight
precision (24-01), the hardware detection and the explicit override reader
(24-02), the profile core with suggestion, effective level and process state
(24-03), the PHP profile route (24-04), the read wire through client, queue and
poller (24-05), and the reporting side in lifespan and `/status` (24-06), plus
the three documentation pages.

The owner decisions were verified against the code rather than assumed:

- **Mark byte-identity (MOD-01):** `embedding_mark` with the default weights
  produces exactly `multilingual-e5-small/int8/384/1024`; fp32 appends `/fp32`;
  an unknown precision raises without echoing the value. The upgrade case
  (stored 1.3.x mark, no drift, nothing re-embedded) and both switch directions
  are pinned by tests against hand-written literals.
- **Slot formula (D-24-03, D-24-08):** Standard uses `floor(0.5*C - 0.25)` with
  the reserve deduction on the memory term; Performance uses `floor(C - 1)`
  with no r deduction. I recomputed all seven parametrised slot cases in
  `test_profile.py` by hand; every expected value is arithmetically correct.
- **Thresholds vs. formula memory (D-24-06):** suggestion reads
  memory.max else MemTotal; the slot formula reads min(memory.max,
  MemAvailable). Both are implemented as two separate properties on
  `Hardware` and tested.
- **Error semantics (D-24-02):** the container keeps the last profile read;
  `note_chosen(None)` and unknown names change nothing; a 1.3 companion (404)
  costs one debug line without the exception text. One deviation on the PHP
  side is WR-02 below.
- **Injected defaults (research pitfall 1):** `explicit_int_from_environment`
  returns None for a value equal to the declared default, and
  `test_info_xml_defaults.py` pins every info.xml default to its config.py
  constant, closing the "drifted default overrules the profile" trap.

No Critical issue was found. Two Warnings concern a non-conservative fallback
in the cgroup v1 detection and a PHP error path that contradicts the agreed
"keep the last known profile" semantics. Six Info items concern boundary
hygiene, forward-looking drift risks for phases 25/26 and test robustness.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: cgroup v1 "no limit" sentinel is accepted as a real memory limit when MemTotal is unreadable

**File:** `backend/src/findling/hardware.py:105-115`
**Issue:** `_memory_limit_v1` filters the v1 "unlimited" encoding (a huge
page-aligned number such as 9223372036854771712) only by comparing against
MemTotal. When `/proc/meminfo` is missing or garbled, `total` is None, the
comparison is skipped and the sentinel is returned as a genuine limit. From
there `threshold_memory_bytes` becomes ~9.2 EB, so `suggest()` proposes
Performance on any box with >= 6 cores, and `formula_memory_bytes` loses its
memory bound (relevant once phase 26 wires the slots). This contradicts both
the module contract ("unusable input ... becomes None for the field it feeds")
and the fail-safe direction of D-24-06, where an unknown reading suggests
economy. The v2 path is immune because v2 spells "no limit" as the word `max`.
**Fix:**
```python
_V1_NO_LIMIT_FLOOR = 1 << 60  # anything this large is the kernel's "unlimited"

def _memory_limit_v1(root: Path, total: int | None) -> int | None:
    limit = _positive_int(_read(root / "memory" / "memory.limit_in_bytes"))
    if limit is None or limit >= _V1_NO_LIMIT_FLOOR:
        return None
    if total is not None and limit >= total:
        return None
    return limit
```
(Alternatively: return None whenever `total is None`, which is the strictly
conservative reading of the module contract.)

### WR-02: PHP error path answers "economy" instead of an error, defeating the container's D-24-02 fallback

**File:** `php/lib/Controller/ProfileController.php:59-68`
**Issue:** On any `Throwable` inside the read, the controller answers
`{"profile": "economy"}` with HTTP 200. The docblock justifies this with "an
error would only make the container fall back to the same value one step
later", but that is factually wrong for every container that has already read
a profile: D-24-02 says a failed read keeps the LAST KNOWN profile (e.g.
performance), and `DocumentQueue.profile()` implements exactly that for
transport errors and non-200 answers. By converting an internal read failure
into a valid-looking "economy", the PHP side makes the container downgrade a
running standard/performance box to economy for at least one round (up to
~25 minutes per the polling cadence), and from phase 26 on that silently
shrinks concurrency mid-index. The window is small (a DB outage fails the
whole OCS request anyway, which the container handles correctly), but the one
class of failure this catch covers is precisely the one where the two halves
now disagree about the semantics.
**Fix:** Answer the failure as a failure so the container's own rule applies:
```php
} catch (\Throwable $e) {
    $this->logger->error('Findling: the profile could not be read', ['exception' => $e]);
    return new DataResponse(['error' => 'profile unreadable'], Http::STATUS_INTERNAL_SERVER_ERROR);
}
```
`DocumentQueue.profile()` already turns the resulting exception into None and
keeps the last known name (D-24-02). If the 200-with-default behaviour is a
deliberate owner choice ("downgrade is the safe direction"), the docblock and
docs/profiles.md should say so explicitly instead of the incorrect
"same value one step later" reasoning, and the deviation from D-24-02 should
be recorded as a decision.

## Info

### IN-01: `read_profile` is missing from the boundary's `__all__` list

**File:** `backend/src/findling/nc/client.py:45-69`
**Issue:** The module presents `__all__` as the boundary contract ("the
writing entry points ... are deliberately absent from the re-export list").
`read_profile` (new in 24-05) is imported by `nc/queue.py` but absent from
`__all__`, as is the pre-existing `topup_documents`. Functionally harmless
(direct imports ignore `__all__`), but it muddies a list that is documented as
the intentional export surface.
**Fix:** Add `"read_profile"` (and `"topup_documents"`) to `__all__`, or state
in the header that `__all__` is not maintained as the contract.

### IN-02: Defaulted `weights` keyword lets a phase-25 caller silently write the int8 mark over an fp32 stock

**File:** `backend/src/findling/store/vectors.py:271` and `backend/src/findling/worker/poller.py:2111`
**Issue:** `embedding_mark(..., weights=WEIGHTS_INT8)` defaults to int8, and
the one production call site in the poller relies on that default. The
docstring itself warns that from phase 25 on the argument must be the
precision that was ACTUALLY loaded. With a default, forgetting to thread the
loaded precision through compiles cleanly and writes the int8 mark over an
fp32 stock, which is the exact drift the mark exists to make visible. The
Merker in docs/profiles.md names the risk; nothing mechanical enforces it yet.
**Fix:** In the phase 25 plan, either make `weights` keyword-only without a
default once a second precision can load, or add a test that the poller call
site passes the precision of the loaded model rather than relying on the
default.

### IN-03: No parity assertion between `PROFILE_VALUE_KEYS` and `ProfileValues` fields

**File:** `backend/src/findling/api/status.py:120-131`
**Issue:** The wire keys are spelled out by design, but nothing asserts that
`PROFILE_VALUE_KEYS` covers every field of `ProfileValues`. A field added in
phase 25/26 (e.g. a new slot kind) would silently vanish from the `/status`
wire; the admin page of phase 27 would render an incomplete table with no red
test anywhere. `profile.py` already exposes `_FIELDS` derived from
`fields(ProfileValues)`.
**Fix:** One test:
`assert set(PROFILE_VALUE_KEYS) == {f.name for f in fields(ProfileValues)}`.

### IN-04: `SettingsService::profile()` does no case normalisation and rejects with a generic log line

**File:** `php/lib/Service/SettingsService.php:270-284`
**Issue:** `occ config:app:set findling profile --value=Standard` (capital S)
silently runs economy; the only trace is the shared counter warning "refused a
settings value that is outside its range", which does not name the field, so
an admin debugging why the box stays frugal gets no pointer to the profile
key. The closed-set comparison itself is correct and matches the Python side.
**Fix:** Either normalise with `strtolower(trim($stored))` before the
`in_array` check, or use a profile-specific log sentence (still without the
value), e.g. "refused a stored profile name outside the closed set".

### IN-05: Resting-state profile tests are coupled to fixture ordering against a polluted shell

**File:** `backend/tests/test_profile.py:38-43,313-321` and `backend/tests/conftest.py:340-353`
**Issue:** The conftest autouse `forget_the_profile_state` recomputes the
snapshot via `reset()` BEFORE the module-level `_no_overrides` fixture deletes
the four override variables (conftest autouse fixtures run first). On a
developer shell that exports e.g. `FINDLING_OCR_DPI=200`, the snapshot is
computed with the override while `resolve(Profile.ECONOMY, None)` in
`test_the_resting_state_is_economy` is computed without it, and the equality
fails for a reason that has nothing to do with the code under test. CI is
clean, so this is robustness, not correctness.
**Fix:** Have `_no_overrides` call `profile.reset()` after the `delenv` loop,
or move the delenv loop into the conftest fixture ahead of `reset()`.

### IN-06: The profile request is issued even while the queue retreat is active

**File:** `backend/src/findling/worker/poller.py:744-751`
**Issue:** `note_chosen(await queue.profile())` runs before every claim,
including during the documented retreat against a removed companion. Each
retreat attempt now performs two failing HTTP calls (profile, then claim)
instead of one, each with its own debug line. The retreat ladder caps this at
twelve attempts per hour, so the cost is negligible; recorded only so that a
later phase that tightens the retreat knows the second call exists.
**Fix:** Optional: skip the profile read while `_unavailable_rounds >=
RETREAT_AFTER_ROUNDS`, re-reading on the first answered claim.

---

_Reviewed: 2026-09-28_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

## Fix-Stand (2026-09-28)

| Befund | Status | Commit | Beleg |
|--------|--------|--------|-------|
| WR-01 | behoben | 637c02b | Groessenboden 1 << 60 verwirft den v1-Sentinel auch ohne MemTotal; RED/GREEN-Test in test_hardware.py |
| WR-02 | behoben | d0705e4 | Lesefehler antwortet 500 mit error-Feld ohne Profilnamen; DocumentQueue.profile() macht daraus None, letztes bekanntes Profil bleibt (D-24-02); PHPUnit-Fall ergaenzt (laeuft nur in CI) |
| IN-01..06 | offen, dokumentiert | n/a | kein Fix-Auftrag fuer Info-Befunde |

Nach-Merge-Gate auf d0705e4: 3494 passed / 15 skipped, ruff + format + vulture + pyright (latest) gruen.
