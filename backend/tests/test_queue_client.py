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

import logging
import re
from pathlib import Path
from typing import Any, cast

import pytest

from findling.nc.client import AsyncNextcloudApp
from findling.nc.queue import KIND_EMBED, KINDS, MAX_ACK_LIST, DocumentQueue, QueueJob

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "findling"
CLIENT_SOURCE = PACKAGE_ROOT / "nc" / "client.py"
QUEUE_SOURCE = PACKAGE_ROOT / "nc" / "queue.py"

# The other end of the acknowledgement. Two tests at the bottom of this file read
# it, because the ceiling of the list and the closed list of reason codes are one
# agreement between the halves and cannot be imported across the boundary.
QUEUE_CONTROLLER = PACKAGE_ROOT.parents[2] / "php" / "lib" / "Controller" / "QueueController.php"
PHP_QUEUE_MAPPER = PACKAGE_ROOT.parents[2] / "php" / "lib" / "Db" / "QueueMapper.php"

CLAIM_PATH = "/ocs/v2.php/apps/findling/queues/documents"
ACK_PATH = "/ocs/v2.php/apps/findling/queues/documents"
UNLOCK_PATH = "/ocs/v2.php/apps/findling/queues/documents/unlock"
REQUEUE_PATH = "/ocs/v2.php/apps/findling/queues/documents/requeue"
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

# A delete row, exactly as the delete branch of QueueService::describe builds it:
# a file id, the storage it lived on, and nothing else. There is no node left to
# ask for a name, a mimetype or a size, and no user list to build, which is the
# whole reason that branch exists.
DELETE_SOURCE = {
    "fileId": 4711,
    "storageId": 3,
    "kind": "delete",
}

# An acl row as the acl branch of QueueService::describe builds it after an
# unshare: the file is still there, but nobody in the prefilter may see it any
# more. The empty list is the payload of the job, which is why it appears here as
# the normal shape rather than as an edge case.
ACL_SOURCE = {
    "fileId": 4711,
    "storageId": 3,
    "kind": "acl",
    "userIds": [],
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
    # All five known kinds have their own branch by now; anything else runs the
    # ordinary content route.
    for unknown in ("thumbnails", "", 7):
        session = _FakeSession({("GET", CLAIM_PATH): {"files": {"91": {**SOURCE, "kind": unknown}}}})

        result = await _queue(session).claim(limit=1, max_bytes=1)

        assert result.jobs[0].kind == "content", unknown


async def test_an_ocr_job_keeps_its_kind_across_the_queue_boundary() -> None:
    # Regression for the Sichtprobe finding of phase 3: KIND_OCR existed, the
    # poller branch existed, but the kind was missing from KINDS, so every row
    # the requeue route created was degraded to content and the second track
    # judged the same bytes as no_text_layer again instead of running the
    # engine. The kind has to survive the trip, exactly like metadata does.
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {"91": {**SOURCE, "kind": "ocr"}}}})

    job = (await _queue(session).claim(limit=1, max_bytes=1)).jobs[0]

    assert job.kind == "ocr"


async def test_a_delete_job_survives_without_users_mime_or_size() -> None:
    # The one row that must not be discarded, and the line right above used to
    # discard it. A deleted file has no node, so QueueService::describe can offer
    # no mimetype, no size and no user who still sees it. Refusing the entry here
    # is how the document stayed in the index forever (pitfalls 3 and 4).
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {"91": DELETE_SOURCE}}})

    result = await _queue(session).claim(limit=1, max_bytes=1)

    assert result.discarded == 0
    job = result.jobs[0]
    assert (job.queue_id, job.file_id, job.kind) == (91, 4711, "delete")
    assert (job.user_ids, job.fetch_as, job.mime, job.size) == ((), "", "", 0)


async def test_a_delete_job_without_a_usable_file_id_is_still_discarded() -> None:
    # The one field a deletion cannot do without: it is the whole payload, and a
    # zero would tell the index to forget a document nobody named.
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {"91": {**DELETE_SOURCE, "fileId": 0}}}})

    result = await _queue(session).claim(limit=1, max_bytes=1)

    assert result.jobs == ()
    assert result.discarded == 1


async def test_an_acl_job_survives_an_empty_user_list() -> None:
    # The emptiness is the message. An unshare leaves a file that nobody in the
    # prefilter may see, and discarding the entry here would leave the old
    # permission rows standing for good (pitfall 4).
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {"91": ACL_SOURCE}}})

    result = await _queue(session).claim(limit=1, max_bytes=1)

    assert result.discarded == 0
    job = result.jobs[0]
    assert (job.queue_id, job.file_id, job.kind) == (91, 4711, "acl")
    assert (job.user_ids, job.fetch_as, job.mime, job.size) == ((), "", "", 0)


async def test_an_acl_job_carries_the_new_user_list() -> None:
    # The other half of the same job: who may see the file now, in the order the
    # PHP side sorted them into.
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {"91": {**ACL_SOURCE, "userIds": ["anna", "bernd"]}}}})

    job = (await _queue(session).claim(limit=1, max_bytes=1)).jobs[0]

    assert job.user_ids == ("anna", "bernd")


async def test_a_capped_user_list_arrives_as_a_marked_job() -> None:
    # Perf audit M5. An instance wide team folder puts the complete user list of
    # the instance on every single file, so QueueService::usersFor caps it and
    # says that it did. The marker is the whole point: without it the container
    # would write the first few hundred names as if they were the truth, and the
    # file would drop out of the prefilter for everybody behind the cap.
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {"91": {**SOURCE, "userIdsTruncated": True}}}})

    job = (await _queue(session).claim(limit=1, max_bytes=1)).jobs[0]

    assert job.users_truncated is True
    # The short list still travels: fetchAs is taken from it, and reading the
    # bytes as somebody who may see the file is exactly what a capped list still
    # answers correctly.
    assert job.user_ids == ("alice", "bob")


async def test_an_uncapped_job_is_not_marked() -> None:
    # The default has to be the strict one. A missing marker is the ordinary
    # case, and reading it as "capped" would make every file a candidate for
    # every user, which is the direction that costs query time on every search.
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {"91": SOURCE, "92": ACL_SOURCE}}})

    result = await _queue(session).claim(limit=2, max_bytes=1)

    assert [job.users_truncated for job in result.jobs] == [False, False]


async def test_a_marker_that_is_not_a_boolean_is_read_as_uncapped() -> None:
    # The marker arrives from outside this process, and anything that is not the
    # explicit truth has to fall to the strict side. Reading a stray string as
    # true would widen the prefilter through a typo on the PHP side.
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {"91": {**SOURCE, "userIdsTruncated": "vielleicht"}}}})

    job = (await _queue(session).claim(limit=1, max_bytes=1)).jobs[0]

    assert job.users_truncated is False


async def test_an_acl_job_without_a_usable_file_id_is_still_discarded() -> None:
    # Same rule as for a deletion: the file id names the document the permissions
    # belong to, and a zero would rewrite the rows of nothing at all.
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {"91": {**ACL_SOURCE, "fileId": 0}}}})

    result = await _queue(session).claim(limit=1, max_bytes=1)

    assert result.jobs == ()
    assert result.discarded == 1


async def test_an_empty_queue_is_no_work_and_no_error() -> None:
    # PHP renders an empty associative array as a JSON list, so both shapes have
    # to read as "nothing to do" rather than as a broken answer.
    for answer in ({"files": {}}, {"files": []}, {}):
        session = _FakeSession({("GET", CLAIM_PATH): answer})

        result = await _queue(session).claim(limit=32, max_bytes=64)

        assert result.jobs == ()
        assert result.unavailable is False


async def test_acknowledge_sends_all_three_lists_to_the_delete_endpoint() -> None:
    # The third list is always spelled out, empty or not: a body whose shape
    # depends on its content is a body the other side has to guess at, and OCS
    # binds a missing parameter to the default of the method either way.
    session = _FakeSession({("DELETE", ACK_PATH): {"acknowledged": 2, "recorded": 1}})

    result = await _queue(session).acknowledge([91, 92], {93: "timeout"})

    assert result.ok is True
    assert result.count == 2
    method, path, kwargs = session.calls[0]
    assert (method, path) == ("DELETE", ACK_PATH)
    assert kwargs["json"] == {
        "files": [91, 92],
        "failed": [{"queueId": 93, "reason": "timeout"}],
        "skipped": [],
    }


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


async def test_requeue_sends_the_file_ids_and_the_kind_to_the_requeue_endpoint() -> None:
    # File ids, not queue row ids. The container knows the file it just looked
    # into, and the reconcile of plan 03-12 knows nothing else either.
    session = _FakeSession({("POST", REQUEUE_PATH): {"requeued": 2}})

    result = await _queue(session).requeue([4711, 4712], kind="ocr")

    assert result.ok is True
    assert result.count == 2
    method, path, kwargs = session.calls[0]
    assert (method, path) == ("POST", REQUEUE_PATH)
    assert kwargs["json"] == {"fileIds": [4711, 4712], "kind": "ocr"}


async def test_requeue_with_nothing_to_hand_over_does_not_call_nextcloud() -> None:
    # Every pass that finds no scanned PDF would otherwise pay a round trip for
    # an answer that can only be zero, which on a small box is the same cost as
    # the empty acknowledgement this rule already exists for.
    session = _FakeSession()

    result = await _queue(session).requeue([], kind="ocr")

    assert result.ok is True
    assert session.calls == []


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
    requeued = await queue.requeue([4711], kind="ocr")
    counters = await queue.stats()

    assert claimed.unavailable is True
    assert claimed.jobs == ()
    assert acknowledged.ok is False
    assert unlocked.ok is False
    assert requeued.ok is False
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

    The gate reads the path as a literal at the call site. Tidying these five
    calls into constants would leave it with "an unknown path", which is a
    violation for the writing three and blindness for all five.
    """
    source = CLIENT_SOURCE.read_text(encoding="utf-8")

    assert source.count('"/ocs/v2.php/apps/findling/queues/documents"') == 2
    assert source.count('"/ocs/v2.php/apps/findling/queues/documents/unlock"') == 1
    assert source.count('"/ocs/v2.php/apps/findling/queues/documents/requeue"') == 1
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


# -- the third list of the acknowledgement (DI-04-03) ------------------------


async def test_acknowledge_sends_the_skip_verdicts_as_a_third_list() -> None:
    # Keyed by file id and not by queue row id, unlike the failure list. The
    # receiving half writes into findling_file_state, which is keyed by file id,
    # and a skipped row travels in the done list as well, so its queue row is
    # deleted in the same request: a queue id would have to be translated before
    # the delete, while the file id is what the verdict is about anyway.
    session = _FakeSession({("DELETE", ACK_PATH): {"acknowledged": 1, "recorded": 1}})

    result = await _queue(session).acknowledge([91], {}, {4711: "encrypted"})

    assert result.ok is True
    method, path, kwargs = session.calls[0]
    assert (method, path) == ("DELETE", ACK_PATH)
    assert kwargs["json"] == {
        "files": [91],
        "failed": [],
        "skipped": [{"fileId": 4711, "reason": "encrypted"}],
    }


async def test_a_skip_verdict_alone_is_worth_a_call() -> None:
    # The done list is empty when every row of the batch was handed over, and a
    # skip verdict still has to reach the other side: it is the only thing that
    # ever puts one of the four container reasons into the error list.
    session = _FakeSession({("DELETE", ACK_PATH): {"acknowledged": 0, "recorded": 1}})

    result = await _queue(session).acknowledge([], {}, {4711: "empty_text"})

    assert result.ok is True
    assert len(session.calls) == 1


async def test_three_empty_lists_still_do_not_call_nextcloud() -> None:
    # The rule of the empty acknowledgement survives the third list. An idle
    # instance polls every two minutes and must not pay a round trip for an
    # answer that can only be zero.
    session = _FakeSession()

    result = await _queue(session).acknowledge([], {}, {})

    assert result.ok is True
    assert session.calls == []


async def test_a_skip_list_over_the_limit_is_cut_and_says_so(caplog: pytest.LogCaptureFixture) -> None:
    # T-05-46. The receiving half refuses a list longer than its own ceiling and
    # answers the whole request with a bad request, which would cost the batch
    # its acknowledgement. Cutting here keeps the acknowledgement, loses only
    # the verdicts beyond the ceiling, and says how many those were. A batch is
    # capped at MAX_BATCH_FILES on the Nextcloud side, so this cannot be reached
    # by an ordinary pass; it is the guard against the day that changes.
    session = _FakeSession({("DELETE", ACK_PATH): {"acknowledged": 1}})
    oversized = dict.fromkeys(range(1, MAX_ACK_LIST + 8), "empty_text")

    with caplog.at_level(logging.WARNING, logger="findling.nc.queue"):
        await _queue(session).acknowledge([91], {}, oversized)

    _, _, kwargs = session.calls[0]
    assert len(kwargs["json"]["skipped"]) == MAX_ACK_LIST
    assert "7" in caplog.text


def test_the_container_cap_matches_the_ceiling_of_the_receiving_half() -> None:
    """The two numbers are one agreement, so they are compared instead of copied.

    ``QueueController::MAX_LIST_LENGTH`` decides what Nextcloud accepts, and a
    container that sends more than that turns a whole acknowledgement into a bad
    request. The constant cannot be imported across the language boundary, so it
    is read out of the source, the same way the reason lists are held against
    each other in ``test_extract_errors.py``.
    """
    source = QUEUE_CONTROLLER.read_text(encoding="utf-8")
    match = re.search(r"const MAX_LIST_LENGTH = (\d+);", source)
    assert match is not None, "the ceiling of the acknowledgement is no longer where this test looks for it"
    assert int(match.group(1)) == MAX_ACK_LIST


def test_the_receiving_half_takes_a_skip_list_and_judges_its_codes() -> None:
    """Gate for the other end of the crossing, read out of the PHP source.

    There is no PHP test environment in this repository, so the guarantee that
    the sending side has a counterpart is textual, in the shape of Gate B in
    ``test_php_trust_boundary.py``. Three properties are pinned, and each of
    them is a way in which the list could rot into a silent data loss: the
    parameter has to exist, its entries have to be judged against the closed
    list of reason codes, and it has to be bounded by the shared ceiling above.
    """
    source = QUEUE_CONTROLLER.read_text(encoding="utf-8")
    assert re.search(r"public function acknowledgeDocuments\([^)]*\$skipped", source, re.DOTALL) is not None
    block = re.search(r"private function skipList\(array \$raw\): \?array \{(.*?)\n\t\}", source, re.DOTALL)
    assert block is not None, "the skip list has no validator of its own"
    body = block.group(1)
    assert "FileStateService::REASONS" in body
    assert "self::MAX_LIST_LENGTH" in body


async def test_an_embed_job_keeps_its_kind_across_the_queue_boundary() -> None:
    # The same regression the OCR case above nails down, for the second track of
    # phase 6: a kind that is missing from KINDS degrades to content, and a row
    # the handover created would then extract the same bytes again instead of
    # embedding the text the index already holds.
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {"91": {**SOURCE, "kind": "embed"}}}})

    job = (await _queue(session).claim(limit=1, max_bytes=1)).jobs[0]

    assert job.kind == KIND_EMBED
    assert job.kind == "embed"


async def test_requeue_sends_the_embed_kind_unchanged() -> None:
    # The handover of plan 06-07 travels through the same call the OCR one uses,
    # and the kind is the only thing that differs between them.
    session = _FakeSession({("POST", REQUEUE_PATH): {"requeued": 1}})

    result = await _queue(session).requeue([4711], kind=KIND_EMBED)

    assert result.ok is True
    _method, _path, kwargs = session.calls[0]
    assert kwargs["json"] == {"fileIds": [4711], "kind": "embed"}


def test_both_halves_know_the_same_kinds_of_work() -> None:
    """Gate over the closed list itself, read out of the PHP source.

    The list decides which branch the container runs and which lock timeout the
    row travels under, and it exists twice because a PHP constant has no import
    into this process. A kind that only one half knows is not a typo with a
    stack trace: the requeue is refused with "Unknown job kind" and the track it
    was supposed to reach simply never runs, which is the shape of the phase 3
    Sichtprobe finding.
    """
    source = PHP_QUEUE_MAPPER.read_text(encoding="utf-8")
    block = re.search(r"const KINDS = \[(.*?)\];", source, re.DOTALL)
    assert block is not None, "the closed list of kinds is no longer where this gate looks for it"
    names = re.findall(r"self::(KIND_[A-Z]+),", block.group(1))
    values = set()
    for name in names:
        literal = re.search(rf"const {name} = '([a-z]+)';", source)
        assert literal is not None, f"{name} stands in KINDS without a literal of its own"
        values.add(literal.group(1))

    assert values == set(KINDS)


def test_the_receiving_half_validates_a_requeue_against_that_same_list() -> None:
    """The other end of the handover: an unknown kind is refused, not stored.

    Textual for the reason the gate above is textual. What it pins is that the
    controller compares against ``QueueMapper::KINDS`` rather than against a
    pattern or a copy of the list, because a copy is what lets a new kind be
    accepted on one side and rejected on the other.
    """
    source = QUEUE_CONTROLLER.read_text(encoding="utf-8")
    assert re.search(r"in_array\(\$kind, QueueMapper::KINDS, true\)", source) is not None
