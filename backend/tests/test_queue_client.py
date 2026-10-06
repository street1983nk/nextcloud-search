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
from findling.nc.queue import (
    _FAILED_FALLBACK,
    _SKIPPED_FALLBACK,
    KIND_EMBED,
    KINDS,
    LANE_EMBED,
    LANE_INDEX,
    MAX_ACK_LIST,
    TOPUP_IDLE,
    TOPUP_SUPPLIED,
    TOPUP_UNAVAILABLE,
    VERDICTS_GENERATION,
    CompanionChoice,
    DocumentQueue,
    QueueJob,
    _wire_reason,
)
from findling.store import repo

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
TOPUP_PATH = "/ocs/v2.php/apps/findling/queues/documents/topup"
PROFILE_PATH = "/ocs/v2.php/apps/findling/profile"

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


async def test_a_claim_with_a_lane_sends_it_as_a_parameter() -> None:
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {}, "lane": "embed"}})

    await _queue(session).claim(limit=8, max_bytes=16, lane=LANE_EMBED)

    assert session.calls[0][2]["params"] == {"n": 8, "max_bytes": 16, "lane": "embed"}


async def test_an_empty_answer_with_the_echo_still_honours_the_lane() -> None:
    # Pitfall 1: the echo is judged before the early return of an empty batch.
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {}, "lane": "embed"}})

    result = await _queue(session).claim(limit=8, max_bytes=16, lane=LANE_EMBED)

    assert result.jobs == ()
    assert result.lane_honored is True


async def test_an_answer_without_an_echo_does_not_honour_the_lane() -> None:
    # A 1.3 companion ignores the filter: its files may be of any kind (T-25-16).
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {"91": SOURCE}}})

    result = await _queue(session).claim(limit=8, max_bytes=16, lane=LANE_INDEX)

    assert [job.queue_id for job in result.jobs] == [91]
    assert result.lane_honored is False


async def test_an_echo_of_the_asked_lane_with_files_honours_it() -> None:
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {"91": SOURCE}, "lane": "index"}})

    result = await _queue(session).claim(limit=8, max_bytes=16, lane=LANE_INDEX)

    assert result.lane_honored is True
    assert len(result.jobs) == 1


@pytest.mark.parametrize(
    ("echo", "honored"),
    [("all", True), ("embed", False), ("index", False), ("turbo", False), (3, False), (None, False)],
)
async def test_a_claim_without_a_lane_asked_for_all(echo: object, honored: bool) -> None:
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {}, "lane": echo}})

    result = await _queue(session).claim(limit=32, max_bytes=64)

    assert result.lane_honored is honored
    assert session.calls[0][2]["params"] == {"n": 32, "max_bytes": 64}


async def test_an_echo_of_another_lane_does_not_honour_the_asked_one() -> None:
    session = _FakeSession({("GET", CLAIM_PATH): {"files": {}, "lane": "all"}})

    result = await _queue(session).claim(limit=8, max_bytes=16, lane=LANE_EMBED)

    assert result.lane_honored is False


async def test_an_unreachable_companion_honours_no_lane() -> None:
    session = _FakeSession(error=OSError("nextcloud is not reachable"))

    result = await _queue(session).claim(limit=8, max_bytes=16, lane=LANE_EMBED)

    assert result.unavailable is True
    assert result.lane_honored is False


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


async def test_top_up_reads_a_ran_slice_as_supplied() -> None:
    # The other side ran a crawl slice on our request (DI-10-04): more work is
    # on its way, and the poller keeps the short pause.
    session = _FakeSession({("POST", TOPUP_PATH): {"ran": True, "pending": True}})

    assert await _queue(session).top_up() == TOPUP_SUPPLIED
    assert session.calls[0][:2] == ("POST", TOPUP_PATH)


async def test_top_up_reads_a_running_slice_as_supplied_too() -> None:
    # ran=false with pending=true is the cron mid-slice at this very moment,
    # and rows are arriving from that slice just the same.
    session = _FakeSession({("POST", TOPUP_PATH): {"ran": False, "pending": True}})

    assert await _queue(session).top_up() == TOPUP_SUPPLIED


async def test_top_up_reads_no_crawl_job_as_idle() -> None:
    # The real "there is nothing left to crawl": the ordinary backoff ladder is
    # the right reaction, exactly as before this route existed.
    session = _FakeSession({("POST", TOPUP_PATH): {"ran": False, "pending": False}})

    assert await _queue(session).top_up() == TOPUP_IDLE


async def test_top_up_survives_a_companion_without_the_route() -> None:
    # The upgrade window: new container, old companion, 404 on this path. One
    # defined answer, never an exception through the poller loop.
    session = _FakeSession(error=OSError("no such route"))

    assert await _queue(session).top_up() == TOPUP_UNAVAILABLE


async def test_companion_choice_returns_profile_and_precision_the_admin_stored() -> None:
    # D-24-01 and D-25-02: the companion keeps both choices, the container asks
    # once per round and reads both out of the same answer.
    session = _FakeSession({("GET", PROFILE_PATH): {"profile": "standard", "precision": "fp32"}})

    assert await _queue(session).companion_choice() == CompanionChoice(profile="standard", precision="fp32")
    assert len(session.calls) == 1
    assert session.calls[0][:2] == ("GET", PROFILE_PATH)


async def test_a_companion_without_the_precision_field_leaves_precision_none() -> None:
    # The 1.3 field stand: the answer carries the profile only (K6).
    session = _FakeSession({("GET", PROFILE_PATH): {"profile": "standard"}})

    assert await _queue(session).companion_choice() == CompanionChoice(profile="standard", precision=None)


async def test_a_null_precision_reads_as_none() -> None:
    session = _FakeSession({("GET", PROFILE_PATH): {"profile": "economy", "precision": None}})

    assert await _queue(session).companion_choice() == CompanionChoice(profile="economy", precision=None)


async def test_each_value_is_judged_on_its_own() -> None:
    # A broken profile does not cost the precision and the other way round.
    session = _FakeSession({("GET", PROFILE_PATH): {"profile": "turbo", "precision": "int8"}})

    assert await _queue(session).companion_choice() == CompanionChoice(profile=None, precision="int8")


@pytest.mark.parametrize(
    "answer",
    [
        {"profile": "x", "precision": "fp16"},
        {"profile": "turbo"},
        {"profile": 3, "precision": 8},
        {"profile": None},
        {},
        [],
        "standard",
        None,
    ],
)
async def test_companion_choice_discards_anything_outside_the_closed_sets(answer: object) -> None:
    # T-24-16 and T-25-17: a value from outside this process picks nothing unless
    # it is one of the names; everything else reads like a failed call.
    session = _FakeSession({("GET", PROFILE_PATH): answer})

    assert await _queue(session).companion_choice() == CompanionChoice(profile=None, precision=None)


@pytest.mark.parametrize(
    "error",
    [OSError("404 no such route"), TimeoutError("gateway"), RuntimeError("anything")],
)
async def test_companion_choice_survives_a_companion_without_the_route(
    error: Exception, caplog: pytest.LogCaptureFixture
) -> None:
    # D-24-02 and K6: a 1.3 companion answers 404 here. One debug line without
    # any value in it, never an exception through the poller loop.
    session = _FakeSession(error=error)

    with caplog.at_level(logging.DEBUG, logger="findling.nc.queue"):
        assert await _queue(session).companion_choice() == CompanionChoice(profile=None, precision=None)

    records = [r for r in caplog.records if r.name == "findling.nc.queue"]
    assert len(records) == 1
    assert records[0].levelno == logging.DEBUG
    assert str(error) not in records[0].getMessage()
    assert records[0].args in (None, ())


# A made up confirmation token of the guard, not a secret (D-26-04).
_CONFIRMATION = "0123456789abcdef0123456789abcdef"


async def test_companion_choice_reads_the_confirmation_token() -> None:
    # D-26-04: the way back of the memory guard travels in the same answer.
    answer = {"profile": "standard", "precision": "int8", "confirmed": _CONFIRMATION}
    session = _FakeSession({("GET", PROFILE_PATH): answer})

    assert await _queue(session).companion_choice() == CompanionChoice(
        profile="standard", precision="int8", confirmed=_CONFIRMATION
    )


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(None, id="null"),
        pytest.param("ABC", id="short"),
        pytest.param(_CONFIRMATION[:31], id="31-chars"),
        pytest.param(_CONFIRMATION + "0", id="33-chars"),
        pytest.param(_CONFIRMATION.upper(), id="upper-case"),
        pytest.param(_CONFIRMATION[:31] + "g", id="not-hex"),
        pytest.param(_CONFIRMATION + "\n", id="trailing-newline"),
        pytest.param(12345, id="number"),
    ],
)
async def test_a_malformed_confirmation_token_reads_as_none(value: object) -> None:
    # T-26-21: only exactly 32 lower case hex digits count; the profile and the
    # precision next to it are judged on their own.
    session = _FakeSession({("GET", PROFILE_PATH): {"profile": "standard", "precision": "int8", "confirmed": value}})

    assert await _queue(session).companion_choice() == CompanionChoice(
        profile="standard", precision="int8", confirmed=None
    )


async def test_a_companion_without_the_confirmed_field_reads_as_none() -> None:
    # The 1.3 companion and the 1.4 companion before plan 26-02 never send it.
    session = _FakeSession({("GET", PROFILE_PATH): {"profile": "standard", "precision": "int8"}})

    assert (await _queue(session).companion_choice()).confirmed is None


@pytest.mark.parametrize("error", [OSError("500"), TimeoutError("gateway gone")])
async def test_a_failed_profile_call_leaves_all_three_values_none(error: Exception) -> None:
    session = _FakeSession(error=error)

    assert await _queue(session).companion_choice() == CompanionChoice(profile=None, precision=None, confirmed=None)


async def test_stats_returns_the_counters_of_the_queue() -> None:
    session = _FakeSession({("GET", STATS_PATH): {"scheduled": 7, "running": 2, "failed": 1}})

    counters = await _queue(session).stats()

    assert (counters.scheduled, counters.running, counters.failed) == (7, 2, 1)
    assert counters.ok is True
    assert session.calls[0][:2] == ("GET", STATS_PATH)


async def test_stats_carries_whether_the_crawl_is_unfinished() -> None:
    # Run 8 of the 28-07 chain: the reconcile walked ahead of an unfinished
    # crawl and requeued every file the crawl had not reached yet, and the crawl
    # then queued all of them a second time. The companion now says whether a
    # crawl is still under way, and this is the only place the container reads it.
    session = _FakeSession({("GET", STATS_PATH): {"scheduled": 0, "running": 0, "failed": 0, "crawling": True}})

    counters = await _queue(session).stats()

    assert counters.crawling is True


@pytest.mark.parametrize("answer", [{"scheduled": 0}, {"scheduled": 0, "crawling": "yes"}, {"crawling": 1}, []])
async def test_a_stats_answer_without_a_true_crawling_flag_reads_as_no_crawl(answer: object) -> None:
    # A companion before this field never sends it, and only a JSON true is a
    # yes: anything else keeps the behaviour of the release before.
    session = _FakeSession({("GET", STATS_PATH): answer})

    counters = await _queue(session).stats()

    assert counters.crawling is False


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
    assert source.count('"/ocs/v2.php/apps/findling/profile"') == 1


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


def test_a_dirty_row_is_never_moved_to_the_embedding_track() -> None:
    """The handover of this module, held at the end that decides what it means.

    The container hands a row over by file id and by kind, and what happens to
    the row is decided in ``QueueMapper::requeueAs``. One rule of that method
    cannot be seen from this side at all, and it is the reason this gate exists:
    a row whose file changed while the container was holding it carries the
    dirty mark, and that mark says the text the pass produced is already stale.

    The embedding track never fetches. It cuts the stored text of the index into
    chunks, so a dirty row carried onto it embeds bytes nobody has any more and
    then acknowledges itself away, and the write that arrived is lost until the
    reconcile finds it hours later. That is the H4 defect of the phase 2 audit
    rebuilt through the trailing track, and it is what turned the mutation case
    of integration.yml red on 08.09.2026: an empty work stock, no pass left to
    run, and an index carrying a revision nobody could search for any more.

    Textual for the reason every gate over the other half in this file is
    textual: there is no database and no Nextcloud in this process, and the rule
    is a condition inside a statement rather than a value anybody can read back.
    """
    source = PHP_QUEUE_MAPPER.read_text(encoding="utf-8")
    block = re.search(r"public function requeueAs\(.*?\n\t\}", source, re.DOTALL)
    assert block is not None, "the handover is no longer where this gate looks for it"
    body = block.group(0)

    # The switch takes rows that are not dirty ...
    assert "$switch->expr()->eq('dirty', $switch->createNamedParameter(false, IQueryBuilder::PARAM_BOOL))" in body
    # ... and the dirty ones are freed where they are, with the mark cleared and
    # their kind untouched, so the next content pass fetches what arrived.
    assert "$stale->expr()->eq('dirty', $stale->createNamedParameter(true, IQueryBuilder::PARAM_BOOL))" in body
    assert "$stale->createNamedParameter($this->freeMark(), IQueryBuilder::PARAM_DATE)" in body
    assert "->set('dirty', $stale->createNamedParameter(false, IQueryBuilder::PARAM_BOOL))" in body
    assert "->set('kind'" not in body.split("$stale = $this->db->getQueryBuilder();")[1], (
        "the handed back row keeps the kind it has, or it lands on the track that does not fetch after all"
    )


def test_the_receiving_half_validates_a_requeue_against_that_same_list() -> None:
    """The other end of the handover: an unknown kind is refused, not stored.

    Textual for the reason the gate above is textual. What it pins is that the
    controller compares against ``QueueMapper::KINDS`` rather than against a
    pattern or a copy of the list, because a copy is what lets a new kind be
    accepted on one side and rejected on the other.
    """
    source = QUEUE_CONTROLLER.read_text(encoding="utf-8")
    assert re.search(r"in_array\(\$kind, QueueMapper::KINDS, true\)", source) is not None


class _RefusedRequest(Exception):
    """Stands in for NextcloudException: a status code and a message with a path."""

    def __init__(self, status_code: int) -> None:
        super().__init__(f"[{status_code}] request: POST {REQUEUE_PATH} /secret/file.pdf")
        self.status_code = status_code


async def test_a_failed_requeue_names_the_exception_type_the_status_and_the_duration(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # The field run of 4 October 2026 (m7g.4xlarge, cell L-T) logged "could not
    # hand 30 files to another track" twice, 60 s after the commit each time, and
    # nothing that said why. Type, status code and duration tell a refusal of the
    # controller (immediate, 400), a server error (500) and a timeout of the
    # transport (no status, tens of seconds) apart; the exception text stays out
    # of the line, because it carries the request and may carry a path.
    session = _FakeSession(error=_RefusedRequest(400))
    caplog.set_level(logging.WARNING, logger="findling.nc.queue")

    result = await _queue(session).requeue([4711, 4712], kind="embed")

    assert result.ok is False
    lines = [record.getMessage() for record in caplog.records if record.name == "findling.nc.queue"]
    assert len(lines) == 1
    assert "could not hand 2 files to another track" in lines[0]
    assert "_RefusedRequest" in lines[0]
    assert "status=400" in lines[0]
    assert re.search(r"after \d+\.\d s", lines[0]) is not None
    assert "secret" not in lines[0]
    assert REQUEUE_PATH not in lines[0]


async def test_a_requeue_error_without_a_status_says_none(caplog: pytest.LogCaptureFixture) -> None:
    # A transport failure, a timeout or a refused connection, carries no HTTP
    # status at all, and the line has to say so rather than invent one.
    session = _FakeSession(error=TimeoutError())
    caplog.set_level(logging.WARNING, logger="findling.nc.queue")

    await _queue(session).requeue([4711], kind="embed")

    lines = [record.getMessage() for record in caplog.records if record.name == "findling.nc.queue"]
    assert len(lines) == 1
    assert "TimeoutError" in lines[0]
    assert "status=none" in lines[0]


# -- the verdict capability signal and the fallback on the wire (K6, plan 29-01) --

PHP_FILE_STATE_SERVICE = PACKAGE_ROOT.parents[2] / "php" / "lib" / "Service" / "FileStateService.php"
NEW_CODES = ("system_file", "legacy_format", "unsupported_variant")


def _php_state_reasons() -> dict[str, set[str]]:
    """STATE_REASONS of FileStateService.php, the table record() judges a pair by."""
    source = PHP_FILE_STATE_SERVICE.read_text(encoding="utf-8")
    block = re.search(r"const STATE_REASONS = \[(.*?)\];", source, re.DOTALL)
    assert block is not None, "the STATE_REASONS constant is no longer where this test looks for it"
    mapping = {
        state: set(re.findall(r"'([a-z_]+)'", inner))
        for state, inner in re.findall(r"'(indexed|skipped|failed)'\s*=>\s*\[(.*?)\]", block.group(1), re.DOTALL)
    }
    assert set(mapping) == {"indexed", "skipped", "failed"}
    return mapping


async def test_a_companion_announcing_the_generation_reads_as_verdicts_2() -> None:
    session = _FakeSession({("GET", PROFILE_PATH): {"profile": "standard", "precision": "int8", "verdicts": 2}})

    choice = await _queue(session).companion_choice()

    assert choice.verdicts == VERDICTS_GENERATION == 2


@pytest.mark.parametrize("value", [None, True, False, 1, 3, "2", 2.0, [2], {"v": 2}])
async def test_any_other_verdicts_value_reads_as_none(value: object) -> None:
    # T-29-02: a closed set like profile and precision. True is an int in
    # Python and 2.0 compares equal to 2, neither of them is the signal.
    session = _FakeSession({("GET", PROFILE_PATH): {"profile": "standard", "verdicts": value}})

    assert (await _queue(session).companion_choice()).verdicts is None


async def test_a_companion_without_the_verdicts_field_reads_as_none() -> None:
    # The 1.3.2 companion: the field does not exist.
    session = _FakeSession({("GET", PROFILE_PATH): {"profile": "standard", "precision": "int8"}})

    assert (await _queue(session).companion_choice()).verdicts is None


async def test_a_failed_profile_call_leaves_verdicts_none() -> None:
    session = _FakeSession(error=OSError("404"))

    assert (await _queue(session).companion_choice()).verdicts is None


def _ack_body(session: _FakeSession) -> dict[str, Any]:
    acks = [kwargs for method, path, kwargs in session.calls if (method, path) == ("DELETE", ACK_PATH)]
    assert len(acks) == 1
    return cast("dict[str, Any]", acks[0]["json"])


_SKIPS = {11: "system_file", 12: "legacy_format", 13: "unsupported_variant", 14: "too_large"}
_FAILS = {21: "system_file", 22: "legacy_format", 23: "unsupported_variant", 24: "timeout"}


@pytest.mark.parametrize("answer", [{"profile": "standard"}, {"profile": "standard", "verdicts": 1}, None])
async def test_without_the_signal_no_new_code_leaves_the_container(answer: dict[str, Any] | None) -> None:
    # T-29-01: a 1.3.2 companion refuses a whole list with one unknown code.
    # None stands for "companion_choice was never called".
    answers: dict[tuple[str, str], Any] = {("DELETE", ACK_PATH): {"acknowledged": 1}}
    if answer is not None:
        answers[("GET", PROFILE_PATH)] = answer
    session = _FakeSession(answers)
    queue = _queue(session)
    if answer is not None:
        await queue.companion_choice()

    await queue.acknowledge([1], _FAILS, _SKIPS)

    body = _ack_body(session)
    assert body["skipped"] == [
        {"fileId": 11, "reason": "mime_not_allowed"},
        {"fileId": 12, "reason": "mime_not_allowed"},
        {"fileId": 13, "reason": "image_not_ocrable"},
        {"fileId": 14, "reason": "too_large"},
    ]
    assert body["failed"] == [
        {"queueId": 21, "reason": "corrupt"},
        {"queueId": 22, "reason": "corrupt"},
        {"queueId": 23, "reason": "corrupt"},
        {"queueId": 24, "reason": "timeout"},
    ]
    serialized = repr(body)
    for code in NEW_CODES:
        assert code not in serialized


class _FlakyProfileSession(_FakeSession):
    """Announces the signal on the first profile read and fails on the second."""

    def __init__(self) -> None:
        super().__init__({("GET", PROFILE_PATH): {"profile": "standard", "verdicts": 2}})
        self.profile_reads = 0

    async def ocs(self, method: str, path: str, **kwargs: Any) -> Any:
        if (method, path) == ("GET", PROFILE_PATH):
            self.profile_reads += 1
            if self.profile_reads > 1:
                self.calls.append((method, path, kwargs))
                raise OSError("gateway gone")
        return await super().ocs(method, path, **kwargs)


async def test_a_failed_read_after_the_signal_falls_back_again() -> None:
    # The signal is the answer of the round, not a memory of an earlier one.
    session = _FlakyProfileSession()
    queue = _queue(session)
    assert (await queue.companion_choice()).verdicts == VERDICTS_GENERATION
    assert (await queue.companion_choice()).verdicts is None

    await queue.acknowledge([], {}, {11: "system_file"})

    assert _ack_body(session)["skipped"] == [{"fileId": 11, "reason": "mime_not_allowed"}]


async def test_with_the_signal_the_codes_travel_unchanged() -> None:
    session = _FakeSession(
        {
            ("GET", PROFILE_PATH): {"profile": "standard", "verdicts": 2},
            ("DELETE", ACK_PATH): {"acknowledged": 1},
        }
    )
    queue = _queue(session)
    await queue.companion_choice()

    await queue.acknowledge([1], _FAILS, _SKIPS)

    body = _ack_body(session)
    assert body["skipped"] == [{"fileId": file_id, "reason": reason} for file_id, reason in _SKIPS.items()]
    assert body["failed"] == [{"queueId": queue_id, "reason": reason} for queue_id, reason in _FAILS.items()]


def test_every_skipped_fallback_is_a_skipped_pair_the_companion_stores() -> None:
    # FileStateService::record drops a pair that is not in STATE_REASONS, and
    # the file then has no verdict in the PHP mirror at all. A skipped fallback
    # onto corrupt would be exactly that pair.
    php = _php_state_reasons()

    assert set(_SKIPPED_FALLBACK) == set(NEW_CODES)
    for code, target in _SKIPPED_FALLBACK.items():
        assert target in php["skipped"], (code, target)
        assert target in repo.STATE_REASONS["skipped"], (code, target)
        assert target not in NEW_CODES
    assert "corrupt" not in _SKIPPED_FALLBACK.values()


def test_every_failed_fallback_is_a_failed_pair_the_companion_stores() -> None:
    php = _php_state_reasons()

    assert set(_FAILED_FALLBACK) == set(NEW_CODES)
    for code, target in _FAILED_FALLBACK.items():
        assert target in php["failed"], (code, target)
        assert target in repo.STATE_REASONS["failed"], (code, target)
        assert target not in NEW_CODES


def test_the_new_codes_are_skipped_only_in_the_companion() -> None:
    # The failed table is defensive because the failed list never carries them.
    php = _php_state_reasons()
    for code in NEW_CODES:
        assert code in php["skipped"]
        assert code not in php["failed"]


@pytest.mark.parametrize("verdicts", [None, 1, 2])
def test_every_other_code_travels_unchanged(verdicts: int | None) -> None:
    for code in ("too_large", "excluded", "unreadable", "gone", "corrupt", "timeout"):
        assert _wire_reason(code, verdicts, fallback=_SKIPPED_FALLBACK) == code
        assert _wire_reason(code, verdicts, fallback=_FAILED_FALLBACK) == code
