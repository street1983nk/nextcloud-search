"""GET /status: numbers about the container, and nothing about its documents.

Phase 4 builds the admin page on top of this answer; phase 2 makes sure the
numbers exist and that nothing else does. The claim that matters most here is
again one about absence: the field set is asserted as a whole, so a later plan
that adds "the file that failed last" to help with support has to change this
test on purpose rather than by accident. A path, a file name or a search term on
an admin page is the shortest route out of this container for exactly the data
this app promises never to move.

The second claim is that a fresh container answers. A missing state database is
what an installation looks like for the first few minutes, and a 500 there would
send an admin looking for a defect that is a normal state.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from conftest import Corpus
from findling.main import APP
from findling.store.repo import FileMeta, open_store

pytestmark = pytest.mark.usefixtures("appapi_environment")

Sign = Callable[[str], dict[str, str]]

STATUS_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "api" / "status.py"

FIELDS = {
    "indexed",
    "skipped",
    "failed",
    "aclRows",
    "docs",
    "indexVersion",
    "analyzerVersion",
    "wordlistHash",
    "reindexRequired",
    "lowDisk",
    "note",
}

# Six odd ids carry two permission rows, six even ones carry one.
ACL_ROWS = 18


def _status(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    response = client.get("/status", headers=headers)

    assert response.status_code == 200, response.text
    return response.json()


def test_the_answer_carries_the_counters_the_versions_and_nothing_else(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _status(client, sign("admin"))

    assert set(answer) == FIELDS
    assert answer["indexed"] == indexed_volume.documents
    assert answer["skipped"] == 0
    assert answer["failed"] == 0
    assert answer["aclRows"] == ACL_ROWS
    assert answer["docs"] == indexed_volume.documents
    assert answer["indexVersion"] == 1
    assert answer["analyzerVersion"] == 1
    assert answer["wordlistHash"] == indexed_volume.digest


def test_the_counters_name_every_state_including_the_empty_ones(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # A status output that omits an empty state makes "no failures" and "the
    # counter is broken" look identical, and telling those two apart is the whole
    # promise of this app.
    store = open_store(indexed_volume.root / "state.db")
    meta = FileMeta(storage_id=1, root_id=1, path="/x", title="x", mime="text/plain", size=1, mtime=1)
    store.record(101, meta, "skipped", "too_large")
    store.record(102, meta, "failed", "corrupt")
    store.close()

    answer = _status(client, sign("admin"))

    assert answer["indexed"] == indexed_volume.documents
    assert answer["skipped"] == 1
    assert answer["failed"] == 1


def test_the_answer_carries_no_path_no_file_name_and_no_search_term(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _status(client, sign("admin"))

    for value in answer.values():
        if isinstance(value, str):
            assert "/" not in value
            assert "Akte" not in value


def test_a_matching_index_needs_no_reindex(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _status(client, sign("admin"))

    assert answer["reindexRequired"] is False
    assert answer["lowDisk"] is False
    assert answer["note"] == ""


def test_a_version_drift_is_reported_as_reindex_required(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # Pitfall 14: the word list changed and the index did not, so the tokenisation
    # of a query no longer agrees with the tokenisation of the documents. Hits
    # then disappear with nothing anywhere saying why, unless this says it.
    store = open_store(indexed_volume.root / "state.db")
    store.write_meta("wordlist_hash", "a different list entirely")
    store.close()

    answer = _status(client, sign("admin"))

    assert answer["reindexRequired"] is True


def test_without_a_state_database_the_answer_is_zeros_and_a_note(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    # A container that was deployed a minute ago. Not an error, and answering
    # with one would send an admin hunting for a defect that is a normal state.
    assert not (volume / "state.db").exists()

    answer = _status(client, sign("admin"))

    assert set(answer) == FIELDS
    assert answer["indexed"] == 0
    assert answer["aclRows"] == 0
    assert answer["docs"] == 0
    assert answer["note"] != ""


def test_a_request_without_any_appapi_header_is_unauthorized(client: TestClient) -> None:
    response = client.get("/status")

    assert response.status_code == 401


def test_all_three_routes_are_mounted() -> None:
    paths = {route.path for route in APP.routes if isinstance(route, APIRoute)}

    assert {"/search", "/snippets", "/status"} <= paths


def test_the_status_module_opens_the_state_read_only() -> None:
    # A static check, because the wrong call would pass every test in this file:
    # the writing connection answers the same questions, it just also lets a
    # defect in a read path change the operating state.
    source = STATUS_SOURCE.read_text(encoding="utf-8")

    assert "open_read_only" in source
    assert "open_store" not in source


def test_asking_for_the_status_changes_nothing(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    database = indexed_volume.root / "state.db"
    before = database.read_bytes()

    _status(client, sign("admin"))

    assert database.read_bytes() == before
