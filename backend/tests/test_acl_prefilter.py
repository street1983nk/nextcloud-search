"""The ACL prefilter: direction, declarativeness, and the name it carries.

The prefilter is the one piece of this project that is easiest to misunderstand
in a way that costs confidentiality. It looks like a permission check, it is not
one, and the tests below fix the three properties that keep it honest.

**Direction.** Given candidates, ask which of them are permitted. The inverse,
materialising every file a user can see, is the documented anti-pattern of the
app this one replaces: it grows with the instance instead of with the query.

**Declarative writes.** ``replace_acl`` deletes and re-inserts inside one
transaction, because the crawl transports the target state and not a delta. A
lost delta is wrong forever; a lost target state repairs itself with the next
delivery.

**The name.** ``prefilter_visible``, never ``check`` and never ``authorize``. The
last test in this file is a grep with a reason: once somebody believes the
backend already decided, the PHP recheck becomes an obvious thing to optimise
away, and that recheck is the only authority there is.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest

from conftest import CONSTITUENTS
from findling.index.open import open_index
from findling.index.writer import IndexBatchWriter
from findling.nc.client import AsyncNextcloudApp
from findling.nc.queue import CallResult, ClaimResult, QueueJob, QueueStats
from findling.store import repo
from findling.store.repo import Store, open_store
from findling.worker.poller import ROUND_WORKED, Poller

PACKAGE_ROOT = Path(repo.__file__).resolve().parents[1]


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    yield opened
    opened.close()


def test_replace_acl_writes_exactly_the_given_users(store: Store) -> None:
    store.replace_acl(1, ["anna", "bernd"])

    assert store.prefilter_visible("anna", [1]) == {1}
    assert store.prefilter_visible("bernd", [1]) == {1}
    assert store.prefilter_visible("carla", [1]) == set()


def test_replace_acl_is_declarative_and_drops_what_is_missing(store: Store) -> None:
    # The crawl hands over the target state. Bernd lost the share, and the second
    # delivery is all it takes for that to become true here.
    store.replace_acl(1, ["anna", "bernd"])
    store.replace_acl(1, ["anna"])

    assert store.prefilter_visible("anna", [1]) == {1}
    assert store.prefilter_visible("bernd", [1]) == set()


def test_replace_acl_with_an_empty_list_leaves_no_row(store: Store) -> None:
    store.replace_acl(1, ["anna"])
    store.replace_acl(1, [])

    assert store.prefilter_visible("anna", [1]) == set()
    assert store.acl_rows_per_document() == 0.0


def test_prefilter_visible_returns_only_the_permitted_candidates(store: Store) -> None:
    store.replace_acl(1, ["anna"])
    store.replace_acl(2, ["bernd"])
    store.replace_acl(3, ["anna", "bernd"])

    assert store.prefilter_visible("anna", [1, 2, 3, 4]) == {1, 3}


def test_prefilter_visible_of_a_user_without_rows_is_empty_and_not_an_error(store: Store) -> None:
    store.replace_acl(1, ["anna"])

    assert store.prefilter_visible("nobody", [1, 2, 3]) == set()


def test_prefilter_visible_with_no_candidates_does_not_touch_the_database(store: Store) -> None:
    statements: list[str] = []
    store.trace(statements.append)
    try:
        result = store.prefilter_visible("anna", [])
    finally:
        store.trace(None)

    assert result == set()
    assert statements == []


def test_prefilter_visible_bands_a_long_candidate_list(store: Store) -> None:
    # 5000 candidates fit into one IN list on this build, but the parameter limit
    # is a build option and this function must not depend on it.
    candidates = list(range(1, 5001))
    for file_id in candidates:
        if file_id % 7 == 0:
            store.replace_acl(file_id, ["anna"])

    statements: list[str] = []
    store.trace(statements.append)
    try:
        banded = store.prefilter_visible("anna", candidates)
    finally:
        store.trace(None)

    one_by_one = {file_id for file_id in candidates if store.prefilter_visible("anna", [file_id])}

    assert banded == one_by_one
    assert len(banded) == 714
    assert len(statements) == 5


def test_prefilter_passes_a_file_with_truncated_user_list(store: Store) -> None:
    # Perf audit M5, and the design decision that comes with it. An instance wide
    # team folder gives every single file the complete user list of the instance,
    # so QueueService caps that list. A capped list must not be written as if it
    # were the whole truth: the file would vanish from the prefilter for everybody
    # behind the cap, and a prefilter that is stricter than reality hides
    # documents from people who may read them.
    #
    # The collective row is the answer. It says "this file has no usable list",
    # the prefilter lets the file through as a candidate for any user, and the
    # PHP recheck decides as it does for every other hit. The prefilter is
    # allowed to be more generous than the truth, never stricter, because it is
    # not the security boundary (COMP-04).
    store.replace_acl(1, [repo.ACL_ANY_USER])

    assert store.prefilter_visible("anna", [1]) == {1}
    assert store.prefilter_visible("bernd", [1]) == {1}
    assert store.prefilter_visible("somebody-who-never-logged-in", [1]) == {1}


def test_prefilter_still_filters_for_normal_files(store: Store) -> None:
    # The other half of the same decision, and the more important one. The
    # collective row is an exception for capped lists and must not soften the
    # ordinary case: a file with a real user list stays invisible to everyone who
    # is not on it, and a user who happens to see a collective file gets no free
    # pass for the rest.
    store.replace_acl(1, [repo.ACL_ANY_USER])
    store.replace_acl(2, ["anna"])
    store.replace_acl(3, ["bernd"])

    assert store.prefilter_visible("anna", [1, 2, 3]) == {1, 2}
    assert store.prefilter_visible("bernd", [1, 2, 3]) == {1, 3}
    assert store.prefilter_visible("carla", [1, 2, 3]) == {1}


def test_the_reserved_uid_cannot_collide_with_a_real_one() -> None:
    # Nextcloud refuses an asterisk in a user id, which is what makes it usable
    # as the reserved value. A collision would be the bad direction of this
    # mechanism: a user literally called like the marker would see every capped
    # file, and no test anywhere would notice.
    assert repo.ACL_ANY_USER == "*"


def test_forget_acl_removes_every_row_of_one_file(store: Store) -> None:
    store.replace_acl(1, ["anna", "bernd", "carla"])
    store.replace_acl(2, ["anna"])

    removed = store.forget_acl(1)

    assert removed == 3
    assert store.prefilter_visible("anna", [1, 2]) == {2}


def test_prefilter_forgets_a_deleted_file(store: Store) -> None:
    # The prefilter half of D-10, and it is asked for every user rather than for
    # the one who deleted the file. A row left behind for a second user is not a
    # leak, because the PHP recheck still runs, but it is a candidate the search
    # pays for on every query and a hit that flickers before it disappears.
    store.replace_acl(1, ["anna", "bernd"])
    store.replace_acl(2, ["anna", "bernd"])

    store.forget_acl(1)

    assert store.prefilter_visible("anna", [1, 2]) == {2}
    assert store.prefilter_visible("bernd", [1, 2]) == {2}


class _OneBatchQueue:
    """The queue calls of one pass, answered from a single scripted batch."""

    def __init__(self, *jobs: QueueJob) -> None:
        self._batches = [tuple(jobs)]
        self.acknowledged: list[list[int]] = []

    async def claim(self, *, limit: int, max_bytes: int) -> ClaimResult:
        del limit, max_bytes
        return ClaimResult(jobs=self._batches.pop(0)) if self._batches else ClaimResult()

    async def acknowledge(self, done: Any, failed: Any, skipped: Any = None) -> CallResult:
        # Neither verdict list matters here: this file is about the prefilter,
        # and an acl job writes no verdict at all.
        del failed, skipped
        self.acknowledged.append(list(done))
        return CallResult(ok=True, count=len(self.acknowledged[-1]))

    async def unlock(self, ids: Any) -> CallResult:
        return CallResult(ok=True, count=len(list(ids)))

    async def stats(self) -> QueueStats:
        return QueueStats()


class _NoGateway:
    """Stands in for the pooled HTTP client. The acl path never asks it anything."""

    async def aclose(self) -> None:
        return None


async def test_unshare_with_empty_user_list_clears_the_prefilter(tmp_path: Path, store: Store) -> None:
    # Pitfall 4, proved through the whole container path rather than against
    # replace_acl alone. After an unshare nobody sees the file any more, so
    # usersFor answers with an empty list, and every layer between Nextcloud and
    # this table used to read that emptiness as "the row is unusable": the entry
    # was written off as skipped(gone) and the old permission rows stayed. The
    # question is asked from the point of view of bernd, who lost the share, and
    # of anna, who never had one to lose.
    index = open_index(tmp_path / "index", CONSTITUENTS)
    writer = IndexBatchWriter(index, directory=tmp_path / "index", min_free_bytes=0)
    store.replace_acl(4711, ["anna", "bernd"])
    queue = _OneBatchQueue(
        QueueJob(
            queue_id=94,
            file_id=4711,
            storage_id=3,
            root_id=0,
            path="",
            title="",
            mime="",
            size=0,
            mtime=0,
            etag="",
            kind="acl",
            user_ids=(),
            fetch_as="",
            is_update=False,
        )
    )
    poller = Poller(
        store=store,
        writer=writer,
        tmp_dir=tmp_path / "tmp",
        client_factory=lambda: cast("AsyncNextcloudApp", object()),
        gateway_factory=lambda: cast("Any", _NoGateway()),
        queue_factory=lambda nc: cast("Any", queue),
    )

    try:
        result = await poller.run_once()
    finally:
        writer.close()

    assert result.state == ROUND_WORKED
    assert store.prefilter_visible("bernd", [4711]) == set()
    assert store.prefilter_visible("anna", [4711]) == set()
    assert queue.acknowledged == [[94]]


async def test_a_marked_acl_job_writes_the_collective_row_and_not_the_short_list(tmp_path: Path, store: Store) -> None:
    # The container half of M5, proved through the whole pass rather than against
    # replace_acl alone. Nextcloud capped the user list of this file and said so,
    # and what has to reach the table is the collective row, never the first few
    # hundred names: those names are the shape that makes the file disappear for
    # everybody else.
    index = open_index(tmp_path / "index", CONSTITUENTS)
    writer = IndexBatchWriter(index, directory=tmp_path / "index", min_free_bytes=0)
    queue = _OneBatchQueue(
        QueueJob(
            queue_id=95,
            file_id=4712,
            storage_id=3,
            root_id=0,
            path="",
            title="",
            mime="",
            size=0,
            mtime=0,
            etag="",
            kind="acl",
            user_ids=("anna", "bernd"),
            users_truncated=True,
            fetch_as="",
            is_update=False,
        )
    )
    poller = Poller(
        store=store,
        writer=writer,
        tmp_dir=tmp_path / "tmp",
        client_factory=lambda: cast("AsyncNextcloudApp", object()),
        gateway_factory=lambda: cast("Any", _NoGateway()),
        queue_factory=lambda nc: cast("Any", queue),
    )

    try:
        result = await poller.run_once()
    finally:
        writer.close()

    assert result.state == ROUND_WORKED
    # One row, and it is the collective one. Two hundred names plus a marker
    # would be the version that looks harmless and costs exactly the memory the
    # cap was introduced to save.
    assert store.acl_rows() == 1
    assert store.prefilter_visible("carla", [4712]) == {4712}


def test_acl_rows_per_document_is_the_status_figure(store: Store) -> None:
    store.replace_acl(1, ["anna", "bernd", "carla"])
    store.replace_acl(2, ["anna"])

    assert store.acl_rows_per_document() == 2.0


def test_the_prefilter_is_never_named_like_a_permission_check() -> None:
    source = (PACKAGE_ROOT / "store" / "repo.py").read_text(encoding="utf-8")

    assert "def prefilter_visible" in source
    assert "def check" not in source
    assert "def authorize" not in source


def test_the_package_never_claims_the_backend_already_checked() -> None:
    # The warning sign from the pitfall list, verbatim. Once this sentence stands
    # anywhere, somebody will read it as permission to drop the PHP recheck.
    offenders = [
        path.relative_to(PACKAGE_ROOT).as_posix()
        for path in sorted(PACKAGE_ROOT.rglob("*.py"))
        if "already checked" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []
