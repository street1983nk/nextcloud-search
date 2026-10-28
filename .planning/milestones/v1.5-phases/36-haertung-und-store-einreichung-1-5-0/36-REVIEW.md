---
phase: 36-haertung-und-store-einreichung-1-5-0
reviewed: 2026-10-28T00:00:00Z
depth: standard
files_reviewed: 33
files_reviewed_list:
  - backend/pyproject.toml
  - backend/src/findling/config.py
  - backend/src/findling/extract/archive.py
  - backend/src/findling/extract/cfb.py
  - backend/src/findling/extract/errors.py
  - backend/src/findling/extract/image.py
  - backend/src/findling/extract/legacy_doc.py
  - backend/src/findling/extract/legacy_xls.py
  - backend/src/findling/extract/mail.py
  - backend/src/findling/extract/odf.py
  - backend/src/findling/extract/office.py
  - backend/src/findling/main.py
  - backend/src/findling/nc/client.py
  - backend/src/findling/nc/files.py
  - backend/src/findling/nc/queue.py
  - backend/src/findling/store/repo.py
  - backend/src/findling/store/schema.sql
  - backend/src/findling/worker/reconcile.py
  - php/appinfo/info.xml
  - php/js/admin.js
  - php/lib/Controller/PageController.php
  - php/lib/Controller/ProfileController.php
  - php/lib/Controller/QueueController.php
  - php/lib/Controller/ReconcileController.php
  - php/lib/Service/AdminViewService.php
  - php/lib/Service/ExAppService.php
  - php/lib/Service/FileStateService.php
  - php/lib/Service/StorageService.php
  - php/tests/Unit/AdminViewServiceTest.php
  - php/tests/Unit/ProfileControllerTest.php
  - php/tests/Unit/QueueControllerTest.php
  - php/tests/Unit/ReconcileControllerTest.php
  - php/tests/Unit/StorageServiceTest.php
findings:
  critical: 0
  warning: 2
  info: 6
  total: 8
status: issues_found
---

# Phase 36: Code Review Report

**Reviewed:** 2026-10-28
**Depth:** standard
**Files Reviewed:** 33 (diff 9040328c..HEAD, e0c801fd)
**Status:** issues_found

## Summary

Reviewed the hardening and store-submission diff for 1.5.0/1.5.1: the new
blocked_malicious verdict class with its eight signature codes (zip_ratio,
zip_overlap, zip_traversal, cfb_cycle, image_pixels, mail_nesting,
xml_entities, package_entries), the CFB cycle walks, the M-32-02 storage
sweep (vanished_storages grace, PHP storages/gone route, classifyAbsent),
the httpx/httpcore logger quieting, the /D regex anchors and canonical-id
checks on the PHP side, and the store texts. The separate security audit
already ran; this review focused on bugs and quality.

Logic that was traced and found correct: the zip ratio two-pass order
(answer O12), the overlap-warning capture in `_copy` (sources closed, scratch
cleanup intact), `_walk_tree`'s iterative DFS (LIFO guarantees the leaving
marker pops before a duplicate push, shared entries are not false cycles,
`<3I` unsigned parsing makes NOSTREAM hit the bounds check), the frame probe
replacing `n_frames` (seek(0) restores frame 0 before the draft), the sweep's
gating on a full, undiscarded walk (T-36-13), band/ceiling parity
GONE_LOOKUP_BAND == MAX_STORAGE_IDS == 256 (held by a parity test), the
`ids[0]=`/`ids[1]=` workaround for nc_py_api's patch_param dict rebuild,
`isIndexedStorage`'s lazy population when `classifyAbsent` is hit cold,
`detailOfVerdict`'s state/reason agreement rules, and the migrate links in
both info.xml files resolving at tag v1.5.1. No blocker was found; two
warnings and six info items follow.

## Warnings

### WR-01: `is_entity_bomb` substring match can misclassify an innocent broken file as malicious

**File:** `backend/src/findling/extract/errors.py:531` (used by `extract/odf.py:505` and `extract/office.py` `_entity_bomb_or_raise`)
**Issue:** The bomb test is `_AMPLIFICATION in str(error)` with
`_AMPLIFICATION = "amplification"`. lxml's `XMLSyntaxError` messages quote
element and attribute names from the file (for example
`Opening and ending tag mismatch: amplification line 1 and p`). A merely
corrupt ODF/DOCX/PPTX whose markup contains an element or attribute named
`amplification` is therefore reported as `skipped(blocked_malicious,
xml_entities)` instead of its honest corrupt/xml verdict. That violates
D-36-17 ("blocked_malicious nur bei KLARER Angriffssignatur"); the existing
wording test guards only the true-positive side (library wording drift), not
this false-positive side. The expat path (openpyxl) is not affected because
`ParseError` messages carry no file content.
**Fix:** Tighten the needle to the shared two-word phrase, which both parsers
use and which cannot be a bare tag name in the message position it appears in:
```python
_AMPLIFICATION: Final = "amplification factor"
```
(libxml2: "Maximum entity amplification factor exceeded"; expat: "limit on
input amplification factor ... breached"). Add a negative test: a mismatched
tag named `amplification` must stay a plain XML verdict.

### WR-02: `_sweep_vanished` docstring promises "no answer ... never a deletion", but an aged stamp still deletes without confirmation

**File:** `backend/src/findling/worker/reconcile.py:808` (docstring) and the loop at ~line 843; also `backend/src/findling/nc/files.py:358` ("the safe reading")
**Issue:** The docstring says "No answer to the question means grace for all
of them and never a deletion." The code, however, falls through to
`living_file_ids` + `_hand_over` for any absent storage whose
`vanished_storages` stamp is already `VANISHED_STORAGE_GRACE_SECONDS` old,
including rounds where `files.gone_storages` answered `None` (1.4.x companion
answering 404 forever, or a transient failure). So against a companion that
never confirms anything, documents of a storage absent for more than 30 days
are deleted purely on the local stamp. That is arguably the intended D-36-05
semantics (grace waited out), but it contradicts both this docstring and the
ReconcileController doc ("it deletes at once only what this route confirms
and keeps its grace period for the rest" - "keeps" reads as indefinite). On a
data-deletion path a maintainer must be able to trust the invariant as
written.
**Fix:** Either make the docstrings say what the code does ("no answer means
no immediate deletion; the grace still runs out and then deletes without
confirmation"), or, if the stricter invariant is wanted, skip the
grace-expiry deletion when `answer is None`:
```python
if answer is None or (storage_id not in gone and storage_id not in deselected):
    first = await asyncio.to_thread(store.mark_vanished, storage_id, now)
    if answer is None or now - first < VANISHED_STORAGE_GRACE_SECONDS:
        stamped.append(storage_id)
        continue
```
Decide which behavior is the contract and align code and prose; today they
disagree.

## Info

### IN-01: `zip_traversal` raised as a bare literal while its siblings have constants

**File:** `backend/src/findling/extract/archive.py:441`
**Issue:** `_ZIP_RATIO` and `_ZIP_OVERLAP` are module constants
(`archive.py:134-135`), but the third signature is raised as
`raise OverLimit("zip_traversal")`. One typo away from a detail code outside
the closed list of 36-WORTLAUT A3 that no catalog entry matches.
**Fix:** Add `_ZIP_TRAVERSAL: Final = "zip_traversal"` next to the other two
and raise the constant.

### IN-02: Stale module comment contradicts `_refused_by_pillow`

**File:** `backend/src/findling/extract/image.py:70-73` vs `image.py:285-315`
**Issue:** The comment above `Image.MAX_IMAGE_PIXELS = _MAX_PIXELS` still
says Pillow is "never told None", while `_refused_by_pillow` now sets
`Image.MAX_IMAGE_PIXELS = None` inside its try/finally. The guidance a reader
takes from the module header is no longer true without reading the new
function.
**Fix:** Extend the comment with one sentence pointing at the single sanctioned
exception (`_refused_by_pillow`, header re-read after a refusal, restored in a
finally).

### IN-03: `_too_many_entries` duplicated verbatim in two modules

**File:** `backend/src/findling/extract/odf.py:64-78` and `backend/src/findling/extract/office.py:570-584`
**Issue:** The helper (open, `fstat`, `count_central_directory`,
`OverLimit -> True`, `CorruptDirectory/OSError -> False`) is copied character
for character. The next change to the refusal rule has to be made twice, and
the two copies can drift.
**Fix:** Move it into `archive.py` (it already owns `count_central_directory`
and both exception types) and import it from both callers.

### IN-04: `vanished_storages` rows can linger forever

**File:** `backend/src/findling/store/repo.py:419-436` (`drop_orphan_bookmarks`) and `repo.py:389-404` (`clear_vanished`)
**Issue:** A storage that is stamped in `vanished_storages` and then loses all
its living rows through the ordinary delete path (so it leaves
`living_storages()`) without ever reappearing in the mount list keeps its
stamp row forever: `clear_vanished` only clears listed storages,
`forget_storage` only runs for swept storages, and `drop_orphan_bookmarks`
cleans `reconcile` and `mounts` but not `vanished_storages`. Harmless to
behavior (a returning storage is always cleared while listed before the
sweep computes `absent` in the same round), but dead rows accumulate.
**Fix:** Have `drop_orphan_bookmarks` also delete orphaned
`vanished_storages` rows (`_FORGET_STORAGE_VANISHED_SQL` already exists).

### IN-05: `_refused_by_pillow` relies on an undeclared single-thread invariant

**File:** `backend/src/findling/extract/image.py:290-307`
**Issue:** Temporarily setting the process-global `Image.MAX_IMAGE_PIXELS` to
`None` is safe only because the extraction child reads one file on one thread,
as the docstring itself says. Nothing enforces that invariant; if extraction
ever gains a thread (or another module opens an image during this window),
the decompression-bomb guard is off process-wide for that window.
**Fix:** None required now. Consider a comment at the extraction-child entry
point naming this dependency, or compute the pixel count from the
`DecompressionBombError` message-free path by reading the header with
`ImageFile`-level parsing if threading ever lands.

### IN-06: `count_forward_headers` counts quoted headers in bodies

**File:** `backend/src/findling/extract/mail.py:358` and `extract_eml:374-377`
**Issue:** After a `RecursionError`, the fallback counts every line of the raw
bytes matching `content-type: message/rfc822`, including lines inside bodies
and text attachments that merely quote mail headers. A mail deep enough to
beat the parser for another reason but containing >32 such quoted lines is
labeled `mail_nesting` instead of `failed(corrupt, RecursionError)`. The
docstring calls it "an upper bound", so this is a known coarseness; impact is
only the verdict class of an already-hostile file.
**Fix:** None required; if precision is ever wanted, require the match to sit
in a header block (before the first blank line of each nested part is hard on
raw bytes, so the current trade-off is defensible as documented).

---

_Reviewed: 2026-10-28_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
