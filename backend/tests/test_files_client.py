"""The two reading calls of the reconcile and the layer that translates them.

Same shape as ``test_queue_client.py``, and for the same reason: every test here
runs against a fake session doppelganger, never against a real Nextcloud. The
integration workflow proves the wire, these tests prove the behaviour a green
wire would still hide.

Three of them carry more weight than the rest.

*The final mark tests.* The deletion rule of the reconcile reads "known locally
in the range behind the cursor up to the last id of the page, but not in the
page". Only the last page may drop the upper bound. A page that claims to be
final when it is not turns every file behind its end into a deletion, so a
missing or unreadable mark has to mean "not final" and nothing else.

*The discard tests.* A row this layer refuses looks exactly like a row that is no
longer there, and the reconcile would answer that with a deletion. The counter is
therefore not a statistic, it is the signal that the page must not be used for a
deletion verdict at all.

*The transport error tests.* An exception escaping a reconcile call would end the
task that carries it. Every call has a defined result for the case where
Nextcloud is unreachable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from findling.nc.client import AsyncNextcloudApp
from findling.nc.files import FileList, FileRow, Mount

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "findling"
CLIENT_SOURCE = PACKAGE_ROOT / "nc" / "client.py"
FILES_SOURCE = PACKAGE_ROOT / "nc" / "files.py"

MOUNTS_PATH = "/ocs/v2.php/apps/findling/mounts"
SLICE_PATH = "/ocs/v2.php/apps/findling/files/slice"

# One mount exactly as ReconcileController::mounts builds it. The overridden root
# is the files folder of a home mount and therefore not the same node as the
# root; both travel, because storage id and root id together identify the mount
# while the overridden root is what the slice query walks.
MOUNT = {"storageId": 3, "rootId": 2, "overriddenRoot": 17}

# One row as ReconcileController::filesSlice built it before plan 05-03: five
# fields, no path, no name, no owner. It stays in this shape on purpose, because
# it is also the answer of a companion app one release behind, and the two
# verdict fields below have to be optional for exactly that reason.
ROW = {
    "fileId": 4711,
    "etag": "5d41402abc4b2a76b9719d911017c592",
    "size": 12345,
    "mtime": 1756600000,
    "mime": "application/pdf",
}

# The same row with the verdict the Nextcloud side holds for the file: two codes
# out of the closed list both sides share, and no third field. This is the
# handover that stops the comparison from requeueing a file that was given up
# (review finding IN-03 of phase 3).
ROW_GIVEN_UP = {**ROW, "state": "failed", "reason": "repeatedly_stuck"}


class _FakeSession:
    """The one method of the private session object the reconcile calls touch."""

    def __init__(self, answers: dict[tuple[str, str], Any] | None = None, error: Exception | None = None) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self._answers = answers or {}
        self._error = error

    async def ocs(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        if self._error is not None:
            raise self._error
        return self._answers.get((method, path), {})


class _FakeApp:
    """Carries a session and counts nothing else; these calls need no more."""

    def __init__(self, session: _FakeSession) -> None:
        self._session = session


def _files(session: _FakeSession) -> FileList:
    return FileList(cast("AsyncNextcloudApp", _FakeApp(session)))


async def test_mounts_delivers_the_mount_list_as_objects() -> None:
    session = _FakeSession({("GET", MOUNTS_PATH): {"mounts": [MOUNT]}})

    result = await _files(session).mounts()

    assert result.unavailable is False
    assert result.discarded == 0
    assert result.mounts == (Mount(storage_id=3, root_id=2, overridden_root=17),)
    assert session.calls[0][:2] == ("GET", MOUNTS_PATH)


async def test_a_page_without_verdict_codes_reads_as_no_verdict() -> None:
    # A row of a companion app that does not send the two codes yet. It has to
    # produce the behaviour of before, so both fields answer with the empty
    # string, which the round reads as "no verdict" and therefore as work.
    session = _FakeSession({("GET", SLICE_PATH): {"files": [ROW], "final": True}})

    result = await _files(session).page(storage=3, root=17, after=4000, limit=500)

    assert result.unavailable is False
    assert result.discarded == 0
    assert result.files == (
        FileRow(
            file_id=4711,
            etag="5d41402abc4b2a76b9719d911017c592",
            size=12345,
            mtime=1756600000,
            mime="application/pdf",
        ),
    )
    assert (result.files[0].state, result.files[0].reason) == ("", "")
    method, path, kwargs = session.calls[0]
    assert (method, path) == ("GET", SLICE_PATH)
    assert kwargs["params"] == {"storage": 3, "root": 17, "after": 4000, "limit": 500}


async def test_a_page_carries_the_verdict_codes_of_the_nextcloud_side() -> None:
    session = _FakeSession({("GET", SLICE_PATH): {"files": [ROW_GIVEN_UP], "final": True}})

    result = await _files(session).page(storage=3, root=17, after=0, limit=500)

    assert result.discarded == 0
    assert (result.files[0].state, result.files[0].reason) == ("failed", "repeatedly_stuck")


async def test_a_verdict_field_that_is_not_a_string_reads_as_no_verdict() -> None:
    # The safe direction: an unreadable code must never be believed. Believing
    # one would suppress the requeue of a file nobody ever gave up on, which is
    # the one way this handover could lose a document.
    for broken in (None, 17, ["failed"], {"state": "failed"}, True):
        session = _FakeSession({("GET", SLICE_PATH): {"files": [{**ROW, "state": broken}], "final": True}})

        result = await _files(session).page(storage=3, root=17, after=0, limit=500)

        assert result.files[0].state == "", broken
        assert result.discarded == 0, broken


async def test_a_page_is_final_only_when_the_answer_says_so() -> None:
    session = _FakeSession({("GET", SLICE_PATH): {"files": [ROW], "final": True}})

    result = await _files(session).page(storage=3, root=17, after=0, limit=500)

    assert result.final is True


async def test_a_page_without_a_readable_final_mark_is_not_final() -> None:
    # The safe direction, and the whole reason this is not guessed from the row
    # count: a repetition costs one round, a wrong deletion verdict costs
    # documents. A missing mark, a null and a string that merely looks true all
    # mean "not final" (T-03-1104).
    for answer in ({"files": [ROW]}, {"files": [ROW], "final": None}, {"files": [ROW], "final": "true"}):
        session = _FakeSession({("GET", SLICE_PATH): answer})

        result = await _files(session).page(storage=3, root=17, after=0, limit=500)

        assert result.final is False, answer


async def test_an_empty_page_is_no_files_and_no_error() -> None:
    # PHP renders an empty list and an empty associative array differently, and
    # a mount whose last page is empty is an everyday event, not a failure.
    for answer in ({"files": [], "final": True}, {"files": {}, "final": True}, {}):
        session = _FakeSession({("GET", SLICE_PATH): answer})

        result = await _files(session).page(storage=3, root=17, after=0, limit=500)

        assert result.files == ()
        assert result.unavailable is False


async def test_an_unusable_mount_entry_is_discarded_and_counted() -> None:
    # A mount without a storage or without a root names nothing that could be
    # walked, and the boolean cases exist because True is an int in Python and
    # would otherwise pass as the storage id 1.
    broken = [
        {**MOUNT, "storageId": 0},
        {**MOUNT, "rootId": 0},
        {**MOUNT, "overriddenRoot": 0},
        {**MOUNT, "storageId": True},
        "not-an-object",
    ]
    session = _FakeSession({("GET", MOUNTS_PATH): {"mounts": [*broken, MOUNT]}})

    result = await _files(session).mounts()

    assert [mount.storage_id for mount in result.mounts] == [3]
    assert result.discarded == len(broken)


async def test_an_unusable_file_row_is_discarded_and_counted() -> None:
    # Every one of these would end as a wrong verdict rather than as an error: a
    # row without a usable file id names no document, and a row without an etag
    # cannot be compared, so passing it on would mean "unchanged" for a file that
    # may well have changed.
    broken = [
        {**ROW, "fileId": 0},
        {**ROW, "fileId": True},
        {**ROW, "etag": ""},
        {**ROW, "size": -1},
        {**ROW, "mime": ""},
        "not-an-object",
    ]
    session = _FakeSession({("GET", SLICE_PATH): {"files": [*broken, ROW], "final": True}})

    result = await _files(session).page(storage=3, root=17, after=0, limit=500)

    assert [row.file_id for row in result.files] == [4711]
    assert result.discarded == len(broken)


async def test_a_page_with_a_discarded_row_is_incomplete_and_says_so() -> None:
    # The contract the reconcile of plan 03-12 reads: a refused row is missing
    # from the page, and "missing from the page" is precisely the shape of a
    # deletion. A page with a discard therefore may update and requeue, but it
    # must not delete.
    session = _FakeSession({("GET", SLICE_PATH): {"files": [{**ROW, "etag": ""}, ROW], "final": True}})

    result = await _files(session).page(storage=3, root=17, after=0, limit=500)

    assert result.discarded == 1
    assert result.complete is False


async def test_a_page_without_a_discard_is_complete() -> None:
    session = _FakeSession({("GET", SLICE_PATH): {"files": [ROW], "final": True}})

    result = await _files(session).page(storage=3, root=17, after=0, limit=500)

    assert result.complete is True


async def test_a_transport_error_is_a_defined_result_and_not_an_exception() -> None:
    # An exception escaping here would end the task that runs the reconcile while
    # everything else keeps answering, which is the failure nobody notices.
    session = _FakeSession(error=OSError("nextcloud is not reachable"))
    files = _files(session)

    mounts = await files.mounts()
    page = await files.page(storage=3, root=17, after=0, limit=500)

    assert mounts.unavailable is True
    assert mounts.mounts == ()
    assert page.unavailable is True
    assert page.files == ()
    # An unreachable Nextcloud is not a finished mount. Final would end the walk
    # over this storage and leave everything behind the cursor looking deleted.
    assert page.final is False
    assert page.complete is False


async def test_a_broken_answer_shape_is_not_a_page_of_nothing() -> None:
    # A list where an object was promised, or a string where the list was: none
    # of that is "the mount is empty", and reading it that way would delete a
    # storage worth of documents.
    for answer in ("nonsense", ["files"], {"files": "nonsense"}):
        session = _FakeSession({("GET", SLICE_PATH): answer})

        result = await _files(session).page(storage=3, root=17, after=0, limit=500)

        assert result.files == (), answer
        assert result.final is False, answer


def test_no_reconcile_call_builds_a_client_of_its_own() -> None:
    """One client per run, so the layer below must not be able to make one.

    ``create_app_client`` is defined in the client module and must not be called
    from here at all: the client is handed in, it holds a connection pool, and a
    client per page would pay a handshake and a PHP bootstrap per page.
    """
    assert "create_app_client" not in FILES_SOURCE.read_text(encoding="utf-8")


def test_the_reconcile_paths_stand_as_literals_at_the_call_site() -> None:
    """The shape the read-only gate depends on, pinned from the other side.

    Both new calls read, so neither needs an allowlist entry. The gate still
    reads the path as a literal at the call site, and a module constant would
    leave it with "an unknown path" for every future edit of these two calls.
    """
    source = CLIENT_SOURCE.read_text(encoding="utf-8")

    assert source.count(f'"{MOUNTS_PATH}"') == 1
    assert source.count(f'"{SLICE_PATH}"') == 1
