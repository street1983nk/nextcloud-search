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

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from conftest import Corpus
from findling.config import MAX_FILE_BYTES
from findling.main import APP
from findling.store.repo import FileMeta, open_store

pytestmark = pytest.mark.usefixtures("appapi_environment")

Sign = Callable[[str], dict[str, str]]

STATUS_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "api" / "status.py"

FIELDS = {
    "indexed",
    "truncated",
    "skipped",
    "failed",
    "reasons",
    "aclRows",
    "docs",
    "indexVersion",
    "analyzerVersion",
    "wordlistHash",
    "reindexRequired",
    "lowDisk",
    "diskFreeBytes",
    "diskTotalBytes",
    "indexBytes",
    "maxFileBytes",
    "note",
}

# Six odd ids carry two permission rows, six even ones carry one.
ACL_ROWS = 18


def _status(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    response = client.get("/status", headers=headers)

    assert response.status_code == 200, response.text
    return response.json()


def _strings(value: Any) -> Iterator[str]:
    """Every string in the answer, keys of nested mappings included.

    The privacy claim of this file is about the whole answer and not about its
    top level. ``reasons`` carries its codes as keys, so a check that only
    walked the values would stop proving anything the day a breakdown is added.
    """
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():  # pyright: ignore[reportUnknownVariableType]
            yield from _strings(key)
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:  # pyright: ignore[reportUnknownVariableType]
            yield from _strings(item)


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


def test_truncated_is_counted_separately_and_stays_inside_indexed(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # D-08 of phase 3: a document whose text was cut off is searchable at the
    # front and not at the back, and an admin who cannot see that number reads
    # "indexed" as a promise the container never made.
    store = open_store(indexed_volume.root / "state.db")
    meta = FileMeta(storage_id=1, root_id=1, path="/x", title="x", mime="application/pdf", size=1, mtime=1)
    store.record(103, meta, "indexed", "truncated")
    store.close()

    answer = _status(client, sign("admin"))

    assert answer["truncated"] == 1
    assert answer["indexed"] == indexed_volume.documents + 1
    assert answer["truncated"] <= answer["indexed"]


def test_the_reasons_break_the_states_down_and_name_the_absent_reason_as_an_empty_string(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # None is not a JSON object key. Normalising it to an empty string here is
    # what keeps the answer readable by a page that indexes into the mapping
    # instead of guessing which of two spellings this release produced.
    store = open_store(indexed_volume.root / "state.db")
    meta = FileMeta(storage_id=1, root_id=1, path="/x", title="x", mime="text/plain", size=1, mtime=1)
    store.record(104, meta, "failed", "corrupt")
    store.close()

    answer = _status(client, sign("admin"))

    assert answer["reasons"]["indexed"][""] == indexed_volume.documents
    assert answer["reasons"]["failed"]["corrupt"] == 1
    assert answer["reasons"]["skipped"] == {}


def test_the_volume_is_reported_as_raw_numbers_and_the_index_size_is_measured(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The admin page computes a space requirement out of these three, so it
    # needs the measurements and not the flag that lowDisk already carries.
    answer = _status(client, sign("admin"))

    assert answer["diskTotalBytes"] > 0
    assert answer["diskFreeBytes"] > 0
    assert answer["diskTotalBytes"] >= answer["diskFreeBytes"]
    assert answer["indexBytes"] > 0
    assert answer["maxFileBytes"] == MAX_FILE_BYTES


def test_the_answer_carries_no_path_no_file_name_and_no_search_term(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    store = open_store(indexed_volume.root / "state.db")
    meta = FileMeta(storage_id=1, root_id=1, path="/x", title="x", mime="text/plain", size=1, mtime=1)
    store.record(105, meta, "skipped", "too_large")
    store.record(106, meta, "indexed", "truncated")
    store.close()

    answer = _status(client, sign("admin"))

    for value in _strings(answer):
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
    assert answer["truncated"] == 0
    assert answer["reasons"] == {}
    assert answer["aclRows"] == 0
    assert answer["docs"] == 0
    assert answer["indexBytes"] == 0
    assert answer["note"] != ""


def test_the_size_cap_is_reported_even_without_a_state_database(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    # Pitfall 2: the container enforces the cap a second time, so the PHP
    # setting has to be clamped to this number. It comes out of the environment
    # and not out of the database, and an empty container is no reason to
    # withhold it from the page that would otherwise show a value that does not
    # apply.
    assert not (volume / "state.db").exists()

    answer = _status(client, sign("admin"))

    assert answer["maxFileBytes"] == MAX_FILE_BYTES


def test_a_request_without_any_appapi_header_is_unauthorized(client: TestClient) -> None:
    response = client.get("/status")

    assert response.status_code == 401


def test_every_route_of_this_container_is_mounted() -> None:
    # Named without a count, because the previous name claimed three and the
    # container has had four since plan 04-05. A test whose name has to be
    # corrected alongside the assertion is a test that will one day only have
    # the assertion corrected.
    #
    # Asked through the OpenAPI description rather than by walking APP.routes.
    # Measured on fastapi 0.141.1: an included router sits in the route list as a
    # private wrapper object with no path of its own, so a test that walked the
    # list would have to unwrap a private type and would be green for the wrong
    # reason on the release that renames it.
    paths = set(APP.openapi()["paths"])

    assert {"/search", "/snippets", "/status", "/rates"} <= paths


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
