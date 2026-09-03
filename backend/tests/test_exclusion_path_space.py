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


def _call_sites() -> list[tuple[str, str]]:
    """The two call paths of the exclusion, as (file name, source)."""
    return [(path.name, path.read_text(encoding="utf-8")) for path in (CRAWL, LISTENER)]


# -- the real tree ---------------------------------------------------------


def test_the_four_files_of_the_exclusion_exist() -> None:
    # The anti vacuity clause. Every scanner above returns an empty list for a
    # file it cannot read, so a gate that lost its files would look perfect.
    missing = [
        path.name for path in (CRAWL, LISTENER, STORAGE_SERVICE, QUEUE_SERVICE, EXCLUSION_SERVICE) if not path.is_file()
    ]

    assert missing == []


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
