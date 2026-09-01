"""The four queue calls and the layer that turns their answers into work.

Every test here runs against a fake session doppelganger, never against a real
Nextcloud, following the shape of ``test_gateway_client.py``: the integration
workflow proves the wire, and these tests prove the behaviour a green wire would
still hide.

Three of them carry more weight than the rest.

*The transport error tests.* A queue call that raises would tear the exception
through the poller loop and end the only indexing task in the process. The search
would keep answering, so nobody would notice for days. Every call therefore has a
defined result for the case where Nextcloud is unreachable.

*The discard test.* The source objects come out of Nextcloud, but they are built
from file cache rows, and a row without a mimetype or without a single user who
can see it is not a rare event on an instance with broken mounts. Passing such an
entry on would end as a confusing failure deep in the extraction path instead of
as a counter.

*The client tests.* One client per run is not a style question. A client per file
costs a connection setup and, on the PHP side, a bootstrap including signature
verification, and at a hundred thousand files that is the difference between an
initial index and a weekend.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, cast

from findling.nc.client import AsyncNextcloudApp
from findling.nc.queue import DocumentQueue, QueueJob

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "findling"
CLIENT_SOURCE = PACKAGE_ROOT / "nc" / "client.py"
QUEUE_SOURCE = PACKAGE_ROOT / "nc" / "queue.py"

CLAIM_PATH = "/ocs/v2.php/apps/findling/queues/documents"
ACK_PATH = "/ocs/v2.php/apps/findling/queues/documents"
UNLOCK_PATH = "/ocs/v2.php/apps/findling/queues/documents/unlock"
STATS_PATH = "/ocs/v2.php/apps/findling/queues/documents/stats"

# One row exactly as QueueService::describe builds it, keys included. The queue
# row id is the key of the map and arrives as a string, because that is what a
# JSON object does to integer keys.
SOURCE = {
    "fileId": 4711,
    "storageId": 3,
    "rootId": 2,
    "path": "Vertraege/Kuendigung.pdf",
    "title": "Kuendigung.pdf",
    "mime": "application/pdf",
    "size": 12345,
    "mtime": 1756600000,
    "etag": "5d41402abc4b2a76b9719d911017c592",
    "kind": "content",
    "userIds": ["alice", "bob"],
    "fetchAs": "alice",
    "isUpdate": False,
}


class _FakeSession:
    """The one method of the private session object the queue calls touch."""

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
    """Carries a session and counts nothing else; the queue calls need no more."""

    def __init__(self, session: _FakeSession) -> None:
        self._session = session


def _queue(session: _FakeSession) -> DocumentQueue:
    return DocumentQueue(cast("AsyncNextcloudApp", _FakeApp(session)))


async def test_claim_delivers_jobs_with_ids_metadata_users_and_fetch_as() -> None:
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {"91": SOURCE}}})

    result = await _queue(session).claim(limit=32, max_bytes=64)

    assert result.unavailable is False
    assert result.discarded == 0
    job = result.jobs[0]
    assert job == QueueJob(
        queue_id=91,
        file_id=4711,
        storage_id=3,
        root_id=2,
        path="Vertraege/Kuendigung.pdf",
        title="Kuendigung.pdf",
        mime="application/pdf",
        size=12345,
        mtime=1756600000,
        etag="5d41402abc4b2a76b9719d911017c592",
        kind="content",
        user_ids=("alice", "bob"),
        fetch_as="alice",
        is_update=False,
    )
    method, path, kwargs = session.calls[0]
    assert (method, path) == ("GET", CLAIM_PATH)
    assert kwargs["params"] == {"n": 32, "max_bytes": 64}


async def test_claim_keeps_the_two_access_questions_apart() -> None:
    # Who may read a file in order to index it and who may find it are different
    # questions, and phase 3 answers them differently. Collapsing the fields is
    # how a prefilter quietly turns into a permission model.
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {"91": SOURCE}}})

    job = (await _queue(session).claim(limit=1, max_bytes=1)).jobs[0]

    assert job.fetch_as == "alice"
    assert job.user_ids == ("alice", "bob")


async def test_claim_carries_the_kind_of_the_job() -> None:
    # The kind picks the branch in the poller, so it has to survive the trip.
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {"91": {**SOURCE, "kind": "metadata"}}}})

    job = (await _queue(session).claim(limit=1, max_bytes=1)).jobs[0]

    assert job.kind == "metadata"


async def test_a_source_without_a_kind_is_a_content_job() -> None:
    # Rows written by a PHP side from before the kind column carry no kind at
    # all. They are ordinary content jobs and must keep running as such rather
    # than being discarded as unusable.
    source = {key: value for key, value in SOURCE.items() if key != "kind"}
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {"91": source}}})

    result = await _queue(session).claim(limit=1, max_bytes=1)

    assert result.discarded == 0
    assert result.jobs[0].kind == "content"


async def test_a_kind_this_container_does_not_know_is_a_content_job() -> None:
    # The job picks the branch, so an unknown value must not pick one (T-03-201).
    # delete, acl and ocr arrive with plans 03-03 to 03-05; until their branch
    # exists, a row carrying them runs the ordinary content route.
    for unknown in ("delete", "acl", "ocr", "", 7):
        session = _FakeSession({("GET", CLAIM_PATH): {"files": {"91": {**SOURCE, "kind": unknown}}}})

        result = await _queue(session).claim(limit=1, max_bytes=1)

        assert result.jobs[0].kind == "content", unknown


async def test_an_empty_queue_is_no_work_and_no_error() -> None:
    # PHP renders an empty associative array as a JSON list, so both shapes have
    # to read as "nothing to do" rather than as a broken answer.
    for answer in ({"files": {}}, {"files": []}, {}):
        session = _FakeSession({("GET", CLAIM_PATH): answer})

        result = await _queue(session).claim(limit=32, max_bytes=64)

        assert result.jobs == ()
        assert result.unavailable is False


async def test_acknowledge_sends_both_lists_to_the_delete_endpoint() -> None:
    session = _FakeSession({("DELETE", ACK_PATH): {"acknowledged": 2, "recorded": 1}})

    result = await _queue(session).acknowledge([91, 92], {93: "timeout"})

    assert result.ok is True
    assert result.count == 2
    method, path, kwargs = session.calls[0]
    assert (method, path) == ("DELETE", ACK_PATH)
    assert kwargs["json"] == {"files": [91, 92], "failed": [{"queueId": 93, "reason": "timeout"}]}


async def test_acknowledge_with_nothing_to_say_does_not_call_nextcloud() -> None:
    # Two empty lists are a request that can only answer zero. The batch that
    # produced them was already handled, and a round trip per idle poll on a
    # small box is a cost with no counterpart.
    session = _FakeSession()

    result = await _queue(session).acknowledge([], {})

    assert result.ok is True
    assert session.calls == []


async def test_unlock_sends_the_open_ids_to_the_unlock_endpoint() -> None:
    session = _FakeSession({("POST", UNLOCK_PATH): {"released": 3}})

    result = await _queue(session).unlock([91, 92, 93])

    assert result.ok is True
    assert result.count == 3
    method, path, kwargs = session.calls[0]
    assert (method, path) == ("POST", UNLOCK_PATH)
    assert kwargs["json"] == {"ids": [91, 92, 93]}


async def test_stats_returns_the_counters_of_the_queue() -> None:
    session = _FakeSession({("GET", STATS_PATH): {"scheduled": 7, "running": 2, "failed": 1}})

    counters = await _queue(session).stats()

    assert (counters.scheduled, counters.running, counters.failed) == (7, 2, 1)
    assert counters.ok is True
    assert session.calls[0][:2] == ("GET", STATS_PATH)


async def test_a_transport_error_is_a_defined_result_and_not_an_exception() -> None:
    # The poller runs as the single indexing task of the process. An exception
    # escaping here would end it while the search keeps answering, which is the
    # failure nobody notices.
    session = _FakeSession(error=OSError("nextcloud is not reachable"))
    queue = _queue(session)

    claimed = await queue.claim(limit=32, max_bytes=64)
    acknowledged = await queue.acknowledge([91], {})
    unlocked = await queue.unlock([91])
    counters = await queue.stats()

    assert claimed.unavailable is True
    assert claimed.jobs == ()
    assert acknowledged.ok is False
    assert unlocked.ok is False
    assert counters.ok is False


async def test_a_source_with_unusable_fields_is_discarded_and_counted() -> None:
    # Every one of these has been seen on an instance with a broken mount, and
    # each would end as a confusing failure deep in the extraction path instead
    # of as a number somebody can act on.
    broken = {
        "no-file-id": {**SOURCE, "fileId": 0},
        "no-mime": {**SOURCE, "mime": ""},
        "nobody-sees-it": {**SOURCE, "userIds": []},
        "no-fetch-user": {**SOURCE, "fetchAs": ""},
        "not-an-object": "queued",
        "negative-size": {**SOURCE, "size": -1},
    }
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {**broken, "91": SOURCE}}})

    result = await _queue(session).claim(limit=32, max_bytes=64)

    assert [job.queue_id for job in result.jobs] == [91]
    assert result.discarded == len(broken)


async def test_a_queue_id_that_is_not_a_number_is_discarded() -> None:
    # The key of the map is what has to come back on acknowledgement. A key that
    # is not a row id would acknowledge nothing and leave the row to circle until
    # the give-up rule catches it.
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {"not-a-number": SOURCE}}})

    result = await _queue(session).claim(limit=32, max_bytes=64)

    assert result.jobs == ()
    assert result.discarded == 1


def test_no_queue_call_builds_a_client_of_its_own() -> None:
    """One client per run, so the layers below must not be able to make one.

    ``create_app_client`` is defined in the client module and must not be called
    from the queue layer at all: the client is handed in, it holds a connection,
    and a client per file pays a handshake and a PHP bootstrap per file.
    """
    assert "create_app_client" not in QUEUE_SOURCE.read_text(encoding="utf-8")


def test_the_queue_paths_stand_as_literals_at_the_call_site() -> None:
    """The shape the read-only gate depends on, pinned from the other side.

    The gate reads the path as a literal at the call site. Tidying these four
    calls into constants would leave it with "an unknown path", which is a
    violation for the writing two and blindness for all four.
    """
    source = CLIENT_SOURCE.read_text(encoding="utf-8")

    assert source.count('"/ocs/v2.php/apps/findling/queues/documents"') == 2
    assert source.count('"/ocs/v2.php/apps/findling/queues/documents/unlock"') == 1
    assert source.count('"/ocs/v2.php/apps/findling/queues/documents/stats"') == 1


def test_the_queue_layer_names_no_forbidden_identifier() -> None:
    """No function called delete, in either module.

    Invariant 2 of the gate is purely name based, and the writing entry point of
    nc_py_api.files is called delete. A queue call named after the HTTP verb it
    uses would collide with it and be reported wherever it stood.
    """
    for module in (CLIENT_SOURCE, QUEUE_SOURCE):
        source = module.read_text(encoding="utf-8")

        assert not re.search(r"\bdef delete|\.delete\(", source), module.name


def test_nc_py_api_is_still_named_in_the_client_module_only() -> None:
    """Gate A restated as a text scan, now that a second nc module exists."""
    pattern = re.compile(r"\bnc_py_api\b|\bhttpx\b")
    offenders = sorted(
        path.relative_to(PACKAGE_ROOT).as_posix()
        for path in PACKAGE_ROOT.rglob("*.py")
        if pattern.search(path.read_text(encoding="utf-8"))
    )

    assert offenders == ["nc/client.py"]
