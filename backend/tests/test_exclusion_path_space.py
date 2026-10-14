"""Gate D: one exclusion helper, one path space, one mount list (pitfall 4).

The failure mode this gate exists for, word for word out of the phase research:
two places in the diff that call ``str_starts_with`` with differently built
paths lead to the crawl leaving the folder alone while every save inside it
queues the file again, and the index fills up slowly with exactly what was
supposed to be left out, without anybody seeing it.

That failure is quiet in every direction. The crawl looks correct because it
skips the folder. The event listener looks correct because it queues what it is
handed. The page looks correct because nothing failed and nothing was skipped:
the files are indexed, which is precisely what was not wanted. The only place
the mistake is visible is the diff, and only if somebody notices that the crawl
compares against ``files/Archiv/x.pdf`` while the listener compares against
``/alice/files/Archiv/x.pdf``. So this gate reads the diff instead.

Five things are held, and each of them is one of the ways the exclusion can come
apart:

1. Neither the crawl nor the event listener may compare a prefix itself. The
   comparison lives in ``ExclusionService::isExcluded`` and the path space in
   ``ExclusionService::mountRelativePath``, and those two are what make the two
   call paths agree by construction.
2. Both of them have to call that helper. A file left out by the crawl and
   queued again by the next save is worse than no exclusion at all, because the
   setting says it worked.
3. ``StorageService`` may hold exactly one mount list. A second answer to "which
   mounts are in" is the failure the warning at ``isIndexedStorage`` has been
   predicting since phase 2: events would keep indexing what the crawl was told
   to leave alone, and the day it happens is the day external storage becomes a
   switch.
4. Neither of them may use ``StorageCrawlJob::MAX_SIZE`` as the value in force.
   The constant stays as the documented default, and the value in force comes
   from ``SettingsService::maxFileBytes()``, which is the one place that clamps
   it at what the container reported (pitfall 2).
5. Since phase 5, for finding IN-07: the validation on the way in and the
   comparison on the way out have one answer about a dot segment. The first four
   hold that both call paths ask the same helper; this one holds that the helper
   itself does not contradict itself, because a shape the validation stores and
   the comparison never meets is a rule that exists on the settings page and
   nowhere else. That is the same quiet failure as above, one layer further in:
   the admin excluded a folder, the page agrees with them, and the index fills up
   anyway.
6. Since plan 33-02, for the patterns of D-30-01: the three call sites that
   skip their root lookup on an instance without rules (the event listener,
   ``QueueService::describe`` and the reconcile slice) ask
   ``ExclusionService::hasRules()`` and no longer whether the prefix list is
   empty. A guard on the prefixes alone checks nothing on an instance that only
   has patterns (pitfall 1 of the phase 33 research).
7. Since plan 33-02 as well: the matcher and the normalisation of a pattern
   contain no glob function, no regular expression and no split of the path
   into segments, read method by method (T-33-03, ReDoS), and the normalisation
   refuses a dot segment with the traversal code like the prefixes do. The one
   fixed ``preg_replace`` in ``trimmed()`` is not part of this probe and stays
   allowed: a fixed pattern, linear, on the prefix path since 1.0.

**Why this is a textual check and not a PHP test.** There is no PHP test
environment on the development machine and none in this repository; the PHP side
is checked with ``php -l`` in a container and nothing else. A textual gate that
runs is worth more than the perfect test that does not exist, and it is the same
shape as Gate A in ``test_readonly_gate.py``, Gate B in
``test_php_trust_boundary.py`` and Gate C in ``test_admin_ui_contract.py``: read
the sources, judge them, name the file and the reason on every finding.

Two self tests against text samples belong to that shape and are not decoration.
A gate whose only assertion is "the current tree is clean" stays green on the day
somebody deletes its body, so both ways of breaking a call site are staged below
and the gate has to report both of them, while a clean counter sample has to stay
silent.

**Comment lines are skipped, and they have to be.** The docblocks of both files
name ``MAX_SIZE`` and both name the helper, which is the whole point of a
docblock that explains where a value comes from. A plain text counter would
therefore report the very documentation that makes the rule findable, and a gate
that punishes its own explanation gets deleted within a week.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PHP_ROOT = Path(__file__).resolve().parents[2] / "php" / "lib"

CRAWL = PHP_ROOT / "BackgroundJobs" / "StorageCrawlJob.php"
LISTENER = PHP_ROOT / "Listener" / "FileEventListener.php"
STORAGE_SERVICE = PHP_ROOT / "Service" / "StorageService.php"

# The third call site, added for review finding CR-01. The reconcile of plan
# 03-12 is a third way into the queue: it requeues every file whose etag the
# container cannot match, and it never sees a path, so the hand-out of the bytes
# in QueueService::describe is the last point the rules of today can be applied.
# Without a check there a fresh exclusion is undone within one reconcile
# interval, because the container reads the tombstones of the cleared subtree as
# restores and re-fetches the whole folder.
QUEUE_SERVICE = PHP_ROOT / "Service" / "QueueService.php"

# The service that owns both halves of the space: the validation on the way in
# and the comparison on the way out. Read here since phase 5, for finding IN-07.
EXCLUSION_SERVICE = PHP_ROOT / "Service" / "ExclusionService.php"

# The fourth call site, added for the owner decision of 03.10.2026 (part a) after
# run 7 of the 28-07 chain. The file slice of the reconcile carries every file of
# the mount, excluded or not, because a filtered page would read as final and
# fire the deletion rule. Without a mark the container read every excluded file
# it did not know as unindexed, requeued it, describe() answered with a delete
# order, and the next quiet round found it unknown again: 549 files every ~300 s.
# So the slice marks such a row live as skipped(excluded), and it has to work the
# rule out through the same helper and the same path space as the other three.
RECONCILE_CONTROLLER = PHP_ROOT / "Controller" / "ReconcileController.php"

# The fifth call site, added in plan 33-04 for way A of the patterns. A pattern
# cannot be resolved into folder ids the way a prefix can, so the sweep walks
# every file of every mount and asks the rule of today for each of them. It has
# to ask it through the one helper on the one path space like the crawl does,
# or the sweep would clear what the crawl indexes, or leave in the index what
# the crawl leaves alone.
EXCLUSION_SWEEP = PHP_ROOT / "BackgroundJobs" / "ExclusionSweepJob.php"

# The one helper both call paths go through, and the one method that builds the
# path they hand it.
HELPER_CALL = "isExcluded"
PATH_SPACE_CALL = "mountRelativePath"

# The value in force, and the constant that is only its default.
CAP_CALL = "maxFileBytes"
CAP_CONSTANT = "MAX_SIZE"

# Every way of comparing the start of a string that PHP offers, plus the two
# pattern functions. None of them belongs in a call site: a prefix comparison
# here is a second path space by definition, because the path it compares was
# built next to it rather than by the one method that owns the space.
PREFIX_COMPARISONS = (
    "str_starts_with",
    "strncmp",
    "strncasecmp",
    "substr_compare",
    "fnmatch",
    "preg_match",
)

# The one mount list of the app. The composed list is the only argument this
# call may carry, because that is what makes getMounts, isIndexedStorage and the
# mounts route give the same answer.
MOUNT_QUERY = "getDistinctMounts"
#
# The first argument is read up to the first comma, non greedily, which is the
# separator in every well formed call. A call that composes its list inside the
# parentheses, ``array_merge($a, $b)``, therefore reads as a truncated argument
# and is reported: composing a list at the call site is precisely the second
# answer this check is about, so the safe direction is to name it.
_MOUNT_QUERY_CALL = re.compile(r"getDistinctMounts\(\s*(.*?)\s*,")
COMPOSED_PROVIDER_LIST = "$this->providers()"

# A line that only defines the constant, which is allowed and is in fact where
# the documented default has to stay.
_CAP_DEFINITION = re.compile(r"const\s+MAX_SIZE\s*=")

# The two segment shapes a stored prefix may never carry, as they are written in
# PHP. Both are refused in normalise() and neither is filtered out: a filter
# would turn a prefix into a different prefix, and the admin would have excluded
# a folder they never typed.
#
# The second one is the finding. A path out of the file cache never carries a
# ``.`` segment, so a rule holding one was stored, listed on the page as in
# force, and matched nothing at all: the quiet failure the refusal of ``..``
# exists to prevent, in the one shape that was still let through (IN-07).
DOT_SEGMENT = "'.'"
PARENT_SEGMENT = "'..'"

# The one trim both halves go through, which is what makes the value the
# validation accepts and the value the comparison receives the same value.
SHARED_TRIM = "$this->trimmed("

# The two halves of the space, by signature.
VALIDATION_METHOD = "public function normalise("
COMPARISON_METHOD = "public function isExcluded("

# The guard of the three call sites that skip their root lookup without rules,
# and the two shapes of the guard it replaced (plan 33-02, pitfall 1).
RULE_GUARD = "hasRules()"
OLD_GUARDS = ("prefixes() !== []", "prefixes() === []")

# The two methods of the pattern half, by name (fixed in plan 33-02), and what
# neither of them may contain. preg_ covers every function of the family.
PATTERN_METHODS = ("function matchesAPattern(", "function normalisePattern(")
PATTERN_FORBIDDEN = ("fnmatch(", "preg_", "explode(")
PATTERN_TRAVERSAL_CODE = "ERROR_TRAVERSAL"

# Lines that are not a statement: blank, and the comment shapes PHP uses. ``#``
# covers an attribute as well, which is the safe direction here too: an
# attribute is never a prefix comparison and never a size cap.
_NOT_A_STATEMENT = ("//", "/*", "*", "#")


def statements(source: str) -> list[tuple[int, str]]:
    """Every line of a PHP source that carries code, with its line number.

    One place decides what a comment is, so the four checks below cannot
    disagree about it.
    """
    return [
        (number, stripped)
        for number, line in enumerate(source.splitlines(), start=1)
        if (stripped := line.strip()) and not stripped.startswith(_NOT_A_STATEMENT)
    ]


def scan_call_site(name: str, source: str) -> list[str]:
    """Findings of one of the two call paths, empty list when it is clean."""
    violations: list[str] = []
    code = statements(source)

    for number, line in code:
        for comparison in PREFIX_COMPARISONS:
            if comparison in line:
                violations.append(
                    f"{name}:{number}: compares a path with {comparison} instead of asking "
                    f"ExclusionService::{HELPER_CALL}, which is a second path space"
                )

        if CAP_CONSTANT in line and _CAP_DEFINITION.search(line) is None:
            violations.append(
                f"{name}:{number}: uses {CAP_CONSTANT} as the size cap in force instead of asking "
                f"SettingsService::{CAP_CALL}(), so an admin who moved the cap is ignored"
            )

    if not any(HELPER_CALL in line for _, line in code):
        violations.append(
            f"{name}: never calls ExclusionService::{HELPER_CALL}, so an excluded file is left "
            "alone on one path and queued on the other"
        )

    if not any(CAP_CALL in line for _, line in code):
        violations.append(
            f"{name}: never asks SettingsService::{CAP_CALL}(), so the size cap of the page has no effect here"
        )

    return violations


def scan_mount_list(name: str, source: str) -> list[str]:
    """Findings of the mount list: a second answer to which mounts are in."""
    violations: list[str] = []
    calls = [(number, line) for number, line in statements(source) if MOUNT_QUERY in line]

    if len(calls) != 1:
        violations.append(
            f"{name}: calls {MOUNT_QUERY} {len(calls)} times instead of once, so this app holds "
            "more than one answer to which mounts are indexed"
        )

    for number, line in calls:
        match = _MOUNT_QUERY_CALL.search(line)
        argument = "" if match is None else match.group(1).strip()
        if argument != COMPOSED_PROVIDER_LIST:
            violations.append(
                f"{name}:{number}: asks {MOUNT_QUERY} with {argument or 'an unreadable argument'} "
                f"instead of {COMPOSED_PROVIDER_LIST}, which is the list the two switches compose"
            )

    return violations


def method_body(name: str, source: str, signature: str) -> str:
    """The lines of one PHP method, from its signature to its closing brace.

    Every method of these classes sits one tab in, so a line that is exactly one
    tab and a brace ends it. Crude on purpose: a gate that needed a PHP parser
    would need a PHP toolchain, and this repository deliberately has none.
    """
    lines = source.splitlines()
    starts = [number for number, line in enumerate(lines) if signature in line]
    assert starts, f"{name}: {signature} is gone, so this gate would pass on nothing"
    start = starts[0]
    for end in range(start + 1, len(lines)):
        if lines[end] == "\t}":
            return "\n".join(lines[start : end + 1])
    raise AssertionError(f"{name}: {signature} has no closing brace at method level")


def scan_segment_refusal(name: str, source: str) -> list[str]:
    """Findings about the two halves of the one path space, empty when clean.

    Three statements, and together they are what makes the validation and the
    comparison agree about a dot segment.

    One, the validation refuses both dot shapes. Two, the comparison interprets
    no segment at all, so a shape refused on the way in can never turn up on the
    way out with a different answer. Three, both halves reach their value through
    the same trim, so they are talking about the same string in the first place.
    """
    violations: list[str] = []
    validation = method_body(name, source, VALIDATION_METHOD)
    comparison = method_body(name, source, COMPARISON_METHOD)

    for segment in (PARENT_SEGMENT, DOT_SEGMENT):
        if segment not in validation:
            violations.append(
                f"{name}: normalise() does not refuse a {segment} segment, so a prefix carrying one "
                "is stored, shown as a rule in force and matches nothing"
            )

    if "explode(" in comparison or DOT_SEGMENT in comparison or PARENT_SEGMENT in comparison:
        violations.append(
            f"{name}: isExcluded() interprets segments of its own, so the answer to a dot segment "
            "no longer depends on normalise() alone and the two halves can disagree"
        )

    for half, body in ((VALIDATION_METHOD, validation), (COMPARISON_METHOD, comparison)):
        if SHARED_TRIM not in body:
            violations.append(
                f"{name}: {half} does not go through {SHARED_TRIM}, so the value it judges is not "
                "the value the other half judges, which is a second path space"
            )

    return violations


def scan_old_guards(name: str, source: str) -> list[str]:
    """Findings of one file: every statement that still guards on the prefixes alone."""
    return [
        f"{name}:{number}: guards on the prefix list alone ({guard}), so an instance with "
        f"patterns and no prefix checks nothing here; ask ExclusionService::{RULE_GUARD}"
        for number, line in statements(source)
        for guard in OLD_GUARDS
        if guard in line
    ]


def scan_pattern_methods(name: str, source: str) -> list[str]:
    """Findings of the pattern half: a forbidden call in the matcher or the normalisation.

    Read method by method, so the fixed ``preg_replace`` of ``trimmed()`` is
    outside every body judged here. A method that disappeared is an assertion
    and not a pass, through method_body().
    """
    violations: list[str] = []
    for signature in PATTERN_METHODS:
        body = method_body(name, source, signature)
        violations.extend(
            f"{name}: {signature.removeprefix('function ')}) contains {forbidden}, which is a glob, "
            "a regular expression or a split of the path, and none of them is linear by construction"
            for forbidden in PATTERN_FORBIDDEN
            if forbidden in body
        )

    if PATTERN_TRAVERSAL_CODE not in method_body(name, source, PATTERN_METHODS[1]):
        violations.append(
            f"{name}: normalisePattern() never answers {PATTERN_TRAVERSAL_CODE}, so a pattern with a "
            "dot segment is stored and matches nothing"
        )

    return violations


_HELPER_ON_THE_PATH_SPACE = re.compile(r"isExcluded\(\s*\$this->exclusionService->mountRelativePath\(")
_HELPER_CALL_SITE = re.compile(r"(?<!function )isExcluded\(")


def scan_sweep(name: str, source: str) -> list[str]:
    """Findings of the sweep job (plan 33-04), empty list when it is clean.

    Stricter than the crawl on purpose: every call of the helper has to take
    the path straight out of ``mountRelativePath``, nested in the call, so a
    path the sweep assembled next to the call cannot reach the comparison. The
    statements are joined first, because the nested call spans two lines.
    """
    violations: list[str] = []
    code = statements(source)

    for number, line in code:
        for comparison in PREFIX_COMPARISONS:
            if comparison in line:
                violations.append(
                    f"{name}:{number}: compares a path with {comparison} instead of asking "
                    f"ExclusionService::{HELPER_CALL}, which is a second path space"
                )

    joined = "\n".join(line for _, line in code)
    calls = len(_HELPER_CALL_SITE.findall(joined))
    on_the_space = len(_HELPER_ON_THE_PATH_SPACE.findall(joined))

    if calls == 0:
        violations.append(
            f"{name}: never calls ExclusionService::{HELPER_CALL}, so the sweep clears nothing "
            "or clears by a rule of its own"
        )
    elif on_the_space != calls:
        violations.append(
            f"{name}: hands ExclusionService::{HELPER_CALL} a path it built itself instead of "
            f"the one out of ExclusionService::{PATH_SPACE_CALL}, which is a second path space"
        )

    return violations


def _call_sites() -> list[tuple[str, str]]:
    """The two call paths of the exclusion, as (file name, source)."""
    return [(path.name, path.read_text(encoding="utf-8")) for path in (CRAWL, LISTENER)]


# -- the real tree ---------------------------------------------------------


def test_the_four_files_of_the_exclusion_exist() -> None:
    # The anti vacuity clause. Every scanner above returns an empty list for a
    # file it cannot read, so a gate that lost its files would look perfect.
    missing = [
        path.name
        for path in (
            CRAWL,
            LISTENER,
            STORAGE_SERVICE,
            QUEUE_SERVICE,
            EXCLUSION_SERVICE,
            RECONCILE_CONTROLLER,
            EXCLUSION_SWEEP,
        )
        if not path.is_file()
    ]

    assert missing == []


def test_the_sweep_asks_the_helper_on_the_one_path_space() -> None:
    # Plan 33-04, the fifth call site. The sweep decides which indexed files a
    # new pattern takes out of the index, so a second answer here clears files
    # the crawl keeps or keeps files the crawl leaves alone.
    source = EXCLUSION_SWEEP.read_text(encoding="utf-8")

    assert scan_sweep(EXCLUSION_SWEEP.name, source) == []


def test_the_validation_and_the_comparison_share_one_path_space() -> None:
    # The fifth statement of this gate, added in phase 5 for finding IN-07. The
    # four above hold that both call paths ask the same helper; this one holds
    # that the helper itself has one answer, because a shape the validation lets
    # through and the comparison never sees is a rule that exists on the page and
    # nowhere else.
    source = EXCLUSION_SERVICE.read_text(encoding="utf-8")

    assert scan_segment_refusal(EXCLUSION_SERVICE.name, source) == []


def test_both_call_paths_go_through_the_one_helper() -> None:
    violations = [message for name, source in _call_sites() for message in scan_call_site(name, source)]

    assert violations == []


def test_the_app_holds_exactly_one_mount_list() -> None:
    source = STORAGE_SERVICE.read_text(encoding="utf-8")

    assert scan_mount_list(STORAGE_SERVICE.name, source) == []


def test_the_path_space_is_built_by_the_one_method_that_owns_it() -> None:
    # The other half of check one. Refusing a hand rolled comparison is not
    # enough on its own: a call site could hand isExcluded a path it assembled
    # itself, and then the comparison would be shared while the space would not.
    for name, source in _call_sites():
        code = statements(source)

        assert any(PATH_SPACE_CALL in line for _, line in code), name


def test_the_reconcile_requeue_path_consults_the_helper() -> None:
    # Review finding CR-01. QueueService::describe is the point where a row the
    # reconcile requeued turns back into a fetch of the bytes, so the rules of
    # today have to be asked there through the same helper and the same path
    # space as the other two call sites. The cap half of scan_call_site does not
    # apply here, because describe hands out work orders and enforces no size,
    # so the two exclusion checks are asserted on their own.
    code = statements(QUEUE_SERVICE.read_text(encoding="utf-8"))

    violations = [
        f"{QUEUE_SERVICE.name}:{number}: compares a path with {comparison} instead of asking "
        f"ExclusionService::{HELPER_CALL}, which is a second path space"
        for number, line in code
        for comparison in PREFIX_COMPARISONS
        if comparison in line
    ]

    assert violations == []
    assert any(HELPER_CALL in line for _, line in code), (
        f"{QUEUE_SERVICE.name}: never calls ExclusionService::{HELPER_CALL}, so the reconcile "
        "re-indexes an excluded subtree within one interval and undoes the clearing"
    )
    assert any(PATH_SPACE_CALL in line for _, line in code), QUEUE_SERVICE.name


def test_the_reconcile_slice_marks_excluded_rows_through_the_helper() -> None:
    # Owner decision of 03.10.2026, part a. The slice is the fourth place the
    # rules of today are applied, and the mark it hands the container has to come
    # out of the one helper on the one path space: a prefix compared here would be
    # a second answer to "is this file excluded", and the container would leave
    # alone what describe() still hands out, or the other way round.
    code = statements(RECONCILE_CONTROLLER.read_text(encoding="utf-8"))

    violations = [
        f"{RECONCILE_CONTROLLER.name}:{number}: compares a path with {comparison} instead of asking "
        f"ExclusionService::{HELPER_CALL}, which is a second path space"
        for number, line in code
        for comparison in PREFIX_COMPARISONS
        if comparison in line
    ]

    assert violations == []
    assert any(HELPER_CALL in line for _, line in code), (
        f"{RECONCILE_CONTROLLER.name}: never calls ExclusionService::{HELPER_CALL}, so the "
        "reconcile requeues every excluded file it does not know on every quiet round"
    )
    assert any(PATH_SPACE_CALL in line for _, line in code), RECONCILE_CONTROLLER.name


def test_an_excluded_row_is_handed_out_as_a_delete_order() -> None:
    # The other half of CR-01, and the half that keeps a cleared subtree clear:
    # a tombstoned file that the reconcile requeued as a restore has to be
    # re-deleted, not merely dropped. Dropping the row would leave the document
    # in the index whenever the file was indexed before the rule arrived. So the
    # branch behind the helper has to answer with a delete order, and this test
    # reads exactly that: KIND_DELETE within the statements that follow the
    # isExcluded call.
    lines = [line for _, line in statements(QUEUE_SERVICE.read_text(encoding="utf-8"))]
    index = next(i for i, line in enumerate(lines) if HELPER_CALL in line)

    assert any("KIND_DELETE" in line for line in lines[index : index + 8]), (
        f"{QUEUE_SERVICE.name}: the exclusion branch of describe() does not answer with a "
        "delete order, so a tombstoned excluded file is not re-deleted"
    )


def test_no_call_site_guards_on_the_prefixes_alone() -> None:
    # Plan 33-02, pitfall 1. Every PHP file of the app except the service that
    # owns both lists, so a fourth guard written next week is caught as well.
    violations = [
        message
        for path in sorted(PHP_ROOT.rglob("*.php"))
        if path != EXCLUSION_SERVICE
        for message in scan_old_guards(path.name, path.read_text(encoding="utf-8"))
    ]

    assert violations == []


def test_exactly_the_known_call_sites_ask_has_rules() -> None:
    # The guard is asked where the root lookup is skipped, and nowhere else: the
    # crawl and the diagnosis call isExcluded() without a guard, and another
    # caller would be a place nobody reviewed for the pattern half. The sweep of
    # plan 33-04 is the fourth: without any rule it ends before it reads a
    # single mount.
    callers = {
        path.name
        for path in PHP_ROOT.rglob("*.php")
        if path != EXCLUSION_SERVICE
        and any(RULE_GUARD in line for _, line in statements(path.read_text(encoding="utf-8")))
    }

    assert callers == {LISTENER.name, QUEUE_SERVICE.name, RECONCILE_CONTROLLER.name, EXCLUSION_SWEEP.name}


def test_the_pattern_half_holds_no_glob_no_regex_and_no_split() -> None:
    source = EXCLUSION_SERVICE.read_text(encoding="utf-8")

    assert scan_pattern_methods(EXCLUSION_SERVICE.name, source) == []


def test_the_two_mount_switches_are_read_and_the_external_entry_is_live() -> None:
    # The switches of D-08 at their enforcement point. The external storage
    # provider was a commented out line from phase 2 with the note that it
    # becomes a switch in ADM-04, so this asserts that the line is code now and
    # that both switches are actually asked.
    code = [line for _, line in statements(STORAGE_SERVICE.read_text(encoding="utf-8"))]

    assert any("Files_External" in line for line in code)
    assert any("indexTeamFolders" in line for line in code)
    assert any("indexExternalStorage" in line for line in code)


# -- self tests: the gate has to report both ways of breaking a call site --

_CLEAN_CALL_SITE = """<?php

class ExampleJob {
\t/**
\t * Fifty megabytes. From plan 04-08 on, MAX_SIZE is the default of a
\t * configurable value and no longer the cap itself, and isExcluded is asked
\t * for the rest.
\t */
\tpublic const MAX_SIZE = 50 * 1024 * 1024;

\tprivate function walk(): void {
\t\t$cap = $this->settingsService->maxFileBytes();
\t\t$root = $this->storageService->mountRootPath($storageId, $rootId);

\t\tforeach ($this->entries() as $entry) {
\t\t\t$relative = $this->exclusionService->mountRelativePath($entry->getPath(), $root);
\t\t\tif ($this->exclusionService->isExcluded($relative)) {
\t\t\t\tcontinue;
\t\t\t}

\t\t\tif ($entry->getSize() > $cap) {
\t\t\t\tcontinue;
\t\t\t}
\t\t}
\t}
}
"""

_CLEAN_MOUNT_LIST = """<?php

class ExampleService {
\tpublic function getMounts(): iterable {
\t\treturn $this->fileAccess->getDistinctMounts($this->providers(), true);
\t}
}
"""


def test_the_clean_samples_are_clean() -> None:
    # The counter sample of everything below. Without it a gate that reported
    # every file as broken would pass all the failure tests too. The call site
    # sample also pins the comment case: its docblock names MAX_SIZE, and a gate
    # that reported that would be reporting its own documentation.
    assert scan_call_site("ExampleJob.php", _CLEAN_CALL_SITE) == []
    assert scan_mount_list("ExampleService.php", _CLEAN_MOUNT_LIST) == []


def test_a_hand_rolled_prefix_comparison_is_reported() -> None:
    # The first of the two ways, and the one pitfall 4 describes: the comparison
    # is copied to the call site, the path next to it is built differently, and
    # the two call paths stop agreeing about the same file.
    source = _CLEAN_CALL_SITE.replace(
        "$this->exclusionService->isExcluded($relative)",
        "str_starts_with($relative, $prefix)",
    )

    violations = scan_call_site("ExampleJob.php", source)

    assert len(violations) == 2
    assert any("str_starts_with" in message and "second path space" in message for message in violations)
    assert any(f"never calls ExclusionService::{HELPER_CALL}" in message for message in violations)


def test_a_call_site_that_never_asks_the_helper_is_reported() -> None:
    # The second way, and the quieter one: nobody wrote a comparison, the call
    # was simply not added when this file was touched. The crawl then leaves the
    # folder alone and every save inside it queues the file again.
    source = _CLEAN_CALL_SITE.replace(
        "\t\t\tif ($this->exclusionService->isExcluded($relative)) {\n\t\t\t\tcontinue;\n\t\t\t}\n\n",
        "",
    )

    violations = scan_call_site("ExampleJob.php", source)

    assert len(violations) == 1
    assert f"never calls ExclusionService::{HELPER_CALL}" in violations[0]


def test_the_constant_used_as_the_cap_in_force_is_reported() -> None:
    # The constant stays in the code as the documented default, so the gate has
    # to tell the definition from the use. This replaces the use and keeps the
    # definition, which is exactly the shape of the regression.
    source = _CLEAN_CALL_SITE.replace(
        "$cap = $this->settingsService->maxFileBytes();",
        "$cap = StorageCrawlJob::MAX_SIZE;",
    )

    violations = scan_call_site("ExampleJob.php", source)

    assert len(violations) == 2
    assert any("as the size cap in force" in message for message in violations)
    assert any(f"never asks SettingsService::{CAP_CALL}()" in message for message in violations)


def test_the_definition_of_the_constant_alone_is_clean() -> None:
    # The counter sample of the test above, and the reason the definition regex
    # exists at all: a gate that reported the constant wherever it stood would
    # force the measured default out of the file it was measured in.
    assert _CAP_DEFINITION.search("\tpublic const MAX_SIZE = 50 * 1024 * 1024;") is not None
    assert _CAP_DEFINITION.search("\t\t$cap = StorageCrawlJob::MAX_SIZE;") is None


def test_a_second_mount_list_is_reported() -> None:
    source = _CLEAN_MOUNT_LIST.replace(
        "\t}\n}\n",
        "\t}\n\n\tpublic function others(): iterable {\n"
        "\t\treturn $this->fileAccess->getDistinctMounts(self::HOME_MOUNT_PROVIDERS, true);\n\t}\n}\n",
    )

    violations = scan_mount_list("ExampleService.php", source)

    assert len(violations) == 2
    assert any("more than one answer" in message for message in violations)
    assert any("HOME_MOUNT_PROVIDERS" in message for message in violations)


def test_a_mount_list_that_is_not_the_composed_one_is_reported() -> None:
    # One call, wrong argument. This is how the switches get bypassed without
    # anybody adding a second list: the constant is still there, so asking it
    # directly reads like a harmless simplification.
    source = _CLEAN_MOUNT_LIST.replace(COMPOSED_PROVIDER_LIST, "self::HOME_MOUNT_PROVIDERS")

    violations = scan_mount_list("ExampleService.php", source)

    assert len(violations) == 1
    assert COMPOSED_PROVIDER_LIST in violations[0]


_CLEAN_EXCLUSION_SERVICE = """<?php

class ExampleExclusionService {
\tpublic function normalise(string $prefix): ?string {
\t\t$value = $this->withoutTheFilesFolder($this->trimmed(trim($prefix)));
\t\tif ($value === '') {
\t\t\treturn null;
\t\t}

\t\tforeach (explode('/', $value) as $segment) {
\t\t\tif ($segment === '..' || $segment === '.') {
\t\t\t\treturn null;
\t\t\t}
\t\t}

\t\treturn $value;
\t}

\tpublic function isExcluded(string $mountRelativePath): bool {
\t\t$path = $this->trimmed($mountRelativePath);
\t\tif ($path === '') {
\t\t\treturn false;
\t\t}

\t\tforeach ($this->prefixes() as $prefix) {
\t\t\tif ($path === $prefix || str_starts_with($path, $prefix . '/')) {
\t\t\t\treturn true;
\t\t\t}
\t\t}

\t\treturn false;
\t}
}
"""


def test_the_clean_exclusion_sample_is_clean() -> None:
    # The counter sample of the three below, and it is the shape the real file
    # has: both refusals in the validation, no segment handling in the
    # comparison, one trim on both sides.
    assert scan_segment_refusal("ExampleExclusionService.php", _CLEAN_EXCLUSION_SERVICE) == []


def test_a_validation_that_keeps_a_dot_segment_is_reported() -> None:
    # The regression itself: somebody removes the second half of the condition
    # because a single dot looks harmless next to a double one.
    source = _CLEAN_EXCLUSION_SERVICE.replace("$segment === '..' || $segment === '.'", "$segment === '..'")

    violations = scan_segment_refusal("ExampleExclusionService.php", source)

    assert len(violations) == 1
    assert "does not refuse a '.' segment" in violations[0]


def test_a_comparison_that_interprets_segments_is_reported() -> None:
    # The other direction, and the one that would make the two halves disagree
    # while both look careful: the comparison starts filtering what the
    # validation refuses, so a dot segment gets two answers in one app.
    source = _CLEAN_EXCLUSION_SERVICE.replace(
        "\t\t$path = $this->trimmed($mountRelativePath);",
        "\t\t$parts = explode('/', $mountRelativePath);\n\t\t$path = $this->trimmed(implode('/', $parts));",
    )

    violations = scan_segment_refusal("ExampleExclusionService.php", source)

    assert len(violations) == 1
    assert "interprets segments of its own" in violations[0]


def test_a_half_that_skips_the_shared_trim_is_reported() -> None:
    # The quietest of the three. Both halves still agree about dot segments and
    # they no longer agree about slashes, which is the original pitfall 4 one
    # layer further in.
    source = _CLEAN_EXCLUSION_SERVICE.replace(
        "$path = $this->trimmed($mountRelativePath);", "$path = $mountRelativePath;"
    )

    violations = scan_segment_refusal("ExampleExclusionService.php", source)

    assert len(violations) == 1
    assert COMPARISON_METHOD in violations[0]


def test_a_method_that_disappeared_is_not_a_pass() -> None:
    # The anti vacuity clause of this scanner. Renaming the validation away
    # would otherwise make every statement above unreachable and the gate green.
    source = _CLEAN_EXCLUSION_SERVICE.replace(VALIDATION_METHOD, "private function normaliseSomething(")

    with pytest.raises(AssertionError, match="is gone"):
        scan_segment_refusal("ExampleExclusionService.php", source)


def test_a_comment_is_not_a_statement() -> None:
    # The mechanism behind the docstring paragraph, pinned. All four comment
    # shapes and a blank line drop out, and the one line of code stays.
    source = "<?php\n\n// a line comment\n/* an opening line */\n * a docblock line\n#[Attribute]\n$cap = 1;\n"

    assert statements(source) == [(1, "<?php"), (7, "$cap = 1;")]


# -- self tests of the pattern half (plan 33-02) ---------------------------

_CLEAN_GUARD = """<?php

class ExampleListener {
\tprivate function queue(): void {
\t\t// A comment may name prefixes() !== [] without being a guard.
\t\tif (!$isDeletion && $this->exclusionService->hasRules()) {
\t\t\t$relative = $this->exclusionService->mountRelativePath($path, $root);
\t\t}
\t}
}
"""

_CLEAN_PATTERN_SERVICE = """<?php

class ExamplePatternService {
\tprivate function normalisePattern(string $pattern): array {
\t\t$value = $this->withoutTheFilesFolder($this->trimmed(trim($pattern)));
\t\t$framed = '/' . $value . '/';
\t\tif (str_contains($framed, '/../') || str_contains($framed, '/./')) {
\t\t\treturn [null, self::ERROR_TRAVERSAL];
\t\t}

\t\treturn [$value, null];
\t}

\tprivate function matchesAPattern(string $path): bool {
\t\t$characters = mb_str_split('/' . $path);
\t\tforeach ($characters as $character) {
\t\t\t$state = (($state << 1) & ($masks[$character] ?? 0)) | ($state & $star);
\t\t}

\t\treturn ($state & $accept) !== 0;
\t}

\tprivate function trimmed(string $path): string {
\t\t$collapsed = preg_replace('#/+#', '/', $path);

\t\treturn trim($collapsed ?? $path, '/');
\t}
}
"""


def test_the_clean_guard_sample_is_clean() -> None:
    # The counter sample, and it pins the comment case: the docblocks of the
    # three call sites explain the guard they replaced.
    assert scan_old_guards("ExampleListener.php", _CLEAN_GUARD) == []


def test_a_guard_on_the_prefixes_alone_is_reported() -> None:
    source = _CLEAN_GUARD.replace("$this->exclusionService->hasRules()", "$this->exclusionService->prefixes() !== []")

    violations = scan_old_guards("ExampleListener.php", source)

    assert len(violations) == 1
    assert RULE_GUARD in violations[0]


def test_the_other_shape_of_the_old_guard_is_reported() -> None:
    source = _CLEAN_GUARD.replace(
        "!$isDeletion && $this->exclusionService->hasRules()", "$this->exclusionService->prefixes() === []"
    )

    violations = scan_old_guards("ExampleListener.php", source)

    assert len(violations) == 1
    assert "prefixes() === []" in violations[0]


def test_the_preg_replace_of_trimmed_alone_is_clean() -> None:
    # The counter sample of the two below. The one fixed preg_replace of the
    # file stands in trimmed(), and trimmed() is called from the normalisation,
    # so a probe over the whole file or over the call would report it.
    assert scan_pattern_methods("ExamplePatternService.php", _CLEAN_PATTERN_SERVICE) == []


def test_a_regular_expression_in_the_matcher_is_reported() -> None:
    source = _CLEAN_PATTERN_SERVICE.replace(
        "\t\treturn ($state & $accept) !== 0;",
        "\t\treturn preg_match($this->translated($pattern), $path) === 1;",
    )

    violations = scan_pattern_methods("ExamplePatternService.php", source)

    assert len(violations) == 1
    assert "matchesAPattern" in violations[0]
    assert "preg_" in violations[0]


def test_a_glob_or_a_split_in_the_normalisation_is_reported() -> None:
    source = _CLEAN_PATTERN_SERVICE.replace(
        "\t\t$framed = '/' . $value . '/';",
        "\t\t$framed = implode('/', explode('/', $value));\n\t\t$hit = fnmatch($value, 'x');",
    )

    violations = scan_pattern_methods("ExamplePatternService.php", source)

    assert len(violations) == 2
    assert all("normalisePattern" in message for message in violations)
    assert any("fnmatch(" in message for message in violations)
    assert any("explode(" in message for message in violations)


def test_a_normalisation_that_keeps_a_dot_segment_is_reported() -> None:
    source = _CLEAN_PATTERN_SERVICE.replace("return [null, self::ERROR_TRAVERSAL];", "return [$value, null];")

    violations = scan_pattern_methods("ExamplePatternService.php", source)

    assert len(violations) == 1
    assert PATTERN_TRAVERSAL_CODE in violations[0]


def test_a_matcher_that_disappeared_is_not_a_pass() -> None:
    source = _CLEAN_PATTERN_SERVICE.replace("function matchesAPattern(", "function matchesSomething(")

    with pytest.raises(AssertionError, match="is gone"):
        scan_pattern_methods("ExamplePatternService.php", source)


# -- self tests of the sweep probe (plan 33-04) ------------------------------

_CLEAN_SWEEP = """<?php

final class ExampleSweepJob {
\tprotected function run($argument): void {
\t\tif (!$this->exclusionService->hasRules()) {
\t\t\treturn;
\t\t}

\t\t$mountRoot = $this->storageService->mountRootPath($storageId, $overriddenRoot);
\t\tforeach ($this->storageService->getFilesInMount($storageId, $overriddenRoot, $cursor, 10) as $entry) {
\t\t\tif ($this->exclusionService->isExcluded(
\t\t\t\t$this->exclusionService->mountRelativePath($entry->getPath(), $mountRoot),
\t\t\t)) {
\t\t\t\t$hits[] = $entry->getId();
\t\t\t}
\t\t}
\t}
}
"""


def test_the_clean_sweep_sample_is_clean() -> None:
    # The counter sample of the two below, in the shape of the real job.
    assert scan_sweep("ExampleSweepJob.php", _CLEAN_SWEEP) == []


def test_a_sweep_that_never_asks_the_helper_is_reported() -> None:
    source = _CLEAN_SWEEP.replace("$this->exclusionService->isExcluded(", "$this->matches(")

    violations = scan_sweep("ExampleSweepJob.php", source)

    assert len(violations) == 1
    assert f"never calls ExclusionService::{HELPER_CALL}" in violations[0]


def test_a_sweep_that_builds_its_own_path_is_reported() -> None:
    # The quiet one: the helper is asked, but with a path assembled next to the
    # call, so the comparison is shared and the space is not.
    source = _CLEAN_SWEEP.replace(
        "$this->exclusionService->mountRelativePath($entry->getPath(), $mountRoot),",
        "$mountRoot . '/' . $entry->getPath(),",
    )

    violations = scan_sweep("ExampleSweepJob.php", source)

    assert len(violations) == 1
    assert "a path it built itself" in violations[0]


def test_a_sweep_with_a_hand_rolled_comparison_is_reported() -> None:
    source = _CLEAN_SWEEP.replace(
        "\t\t\t\t$hits[] = $entry->getId();\n",
        "\t\t\t\t$hits[] = $entry->getId();\n\t\t\t}\n\t\t\tif (fnmatch('*.key', $entry->getPath())) {\n",
    )

    violations = scan_sweep("ExampleSweepJob.php", source)

    assert len(violations) == 1
    assert "fnmatch" in violations[0]
