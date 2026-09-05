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

The third claim arrives with phase 5 and it is about one field. ``appVersion`` is
the version AppAPI registered this container under, and D-11 has the PHP half
compare its major and minor against it, so a wrong or missing value there does
not produce a wrong number on a page, it produces a search that answers
differently from what either half believes. Three properties are asserted for
it: it comes out of the environment, it is there for a container that has no
index yet, and it is not derived from the two index format marks next to it.

The fourth claim arrives with phase 6 and it is the second track. ``embedded``
counts the documents that carry a vector, and it exists because the semantic
half fills up for hours after the full text half is already usable: without a
number of its own the page says a hundred per cent while a paraphrase finds
nothing, with nowhere saying why (D-16). Three properties are asserted for it:
it is contained in ``indexed`` and never added next to it, a container without a
vector stock answers with nought plus a note rather than with an error, and a
vector file that is not a database is the same answer for the same reason
(WR-01).
"""

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from conftest import APP_VERSION, Corpus
from findling.api.status import NO_VECTORS_YET, STATE_UNREADABLE, VECTORS_UNREADABLE, report
from findling.config import MAX_FILE_BYTES
from findling.main import APP
from findling.store.repo import FileMeta, open_store
from findling.store.vectors import EMBEDDING_DIMENSIONS, Chunk, open_vectors

pytestmark = pytest.mark.usefixtures("appapi_environment")

Sign = Callable[[str], dict[str, str]]

STATUS_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "api" / "status.py"

FIELDS = {
    "indexed",
    "truncated",
    "embedded",
    "skipped",
    "failed",
    "reasons",
    "aclRows",
    "docs",
    "indexVersion",
    "analyzerVersion",
    "appVersion",
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

# An em dash and an en dash, written as escapes rather than as themselves so
# that this file does not carry the two characters it exists to keep out. The
# same device test_admin_ui_contract.py uses for the three files of the page.
EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)


def _stock_vectors(root: Path, chunks_per_file: dict[int, int]) -> None:
    """Give the named documents that many chunks each, in the real vector stock.

    The vectors themselves are constant and meaningless here: this file asks how
    many documents carry one, never which of them is closest to anything. What
    the chunk counts are for is the one property a COUNT over the wrong column
    would get wrong, and it would get it wrong plausibly: a document with three
    chunks has to raise the figure by one and not by three.
    """
    stock = open_vectors(root / "vectors.db")
    try:
        for file_id, total in chunks_per_file.items():
            stock.replace_chunks(
                file_id,
                [
                    Chunk(
                        ordinal=ordinal,
                        char_start=ordinal * 100,
                        char_end=ordinal * 100 + 80,
                        embedding=bytes(EMBEDDING_DIMENSIONS),
                    )
                    for ordinal in range(total)
                ],
            )
    finally:
        stock.close()


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


def test_the_second_track_is_counted_separately_and_stays_inside_indexed(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # D-16: the embedding track fills up for hours after the full text half is
    # already usable, so the page needs a figure of its own for it. Five of the
    # twelve documents carry a vector here and one of them carries three chunks,
    # which is what tells a count over documents from a count over chunks.
    _stock_vectors(indexed_volume.root, {1: 3, 2: 1, 3: 1, 4: 1, 5: 1})

    answer = _status(client, sign("admin"))

    assert answer["embedded"] == 5
    assert answer["indexed"] == indexed_volume.documents
    assert answer["embedded"] <= answer["indexed"]
    assert answer["note"] == ""


def test_a_container_whose_second_track_has_not_started_reports_nought_embedded(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The ordinary state of the first hours: the vector stock exists, the full
    # text half is complete and nothing has been embedded yet. Nought is an
    # honest figure here and not a missing one, so there is no note.
    answer = _status(client, sign("admin"))

    assert answer["embedded"] == 0
    assert answer["indexed"] == indexed_volume.documents
    assert answer["note"] == ""


def test_without_a_vector_database_the_answer_is_a_state_with_a_note(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # A container built without the model, or one whose vector stock was thrown
    # away, which is a supported way of rebuilding the semantic half. Not an
    # error: the full text numbers of this answer are all still true, and a 500
    # would take them off the page along with the one that is missing (WR-01).
    (indexed_volume.root / "vectors.db").unlink()

    answer = _status(client, sign("admin"))

    assert set(answer) == FIELDS
    assert answer["embedded"] == 0
    assert answer["indexed"] == indexed_volume.documents
    assert answer["note"] == NO_VECTORS_YET


def test_a_zero_byte_vector_database_is_an_answer_and_not_a_server_error(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The same two shapes of a broken state the state database has, one file
    # over: a kill between connect and the schema script leaves a file that
    # opens cleanly and fails on the first query.
    vectors = indexed_volume.root / "vectors.db"
    vectors.unlink()
    vectors.touch()

    answer = _status(client, sign("admin"))

    assert set(answer) == FIELDS
    assert answer["embedded"] == 0
    assert answer["indexed"] == indexed_volume.documents
    assert answer["note"] == VECTORS_UNREADABLE


def test_a_vector_file_that_is_no_database_is_an_answer_and_not_a_server_error(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The other shape: the file exists and is not SQLite at all, so the open
    # itself raises rather than the first query.
    (indexed_volume.root / "vectors.db").write_bytes(b"this is not a sqlite database")

    answer = _status(client, sign("admin"))

    assert set(answer) == FIELDS
    assert answer["embedded"] == 0
    assert answer["note"] == VECTORS_UNREADABLE


def test_a_broken_state_database_outranks_the_note_of_the_vector_stock(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    # Both halves are missing here, and the answer carries one note, so the two
    # have to be ordered rather than concatenated. The state database is the
    # bigger finding: without it there are no counters at all, while a missing
    # vector stock costs exactly one of them.
    (volume / "state.db").touch()

    answer = _status(client, sign("admin"))

    assert answer["embedded"] == 0
    assert answer["note"] == STATE_UNREADABLE


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


def test_the_answer_names_the_version_this_container_was_registered_under(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # D-11 needs a field that this route did not have: the app version of this
    # half. It comes out of APP_VERSION, which AppAPI injects into the container
    # when it deploys it, so what is reported is the version this container was
    # really registered under rather than a constant baked into the image, which
    # would agree with the registration only until somebody forgot to raise it.
    answer = _status(client, sign("admin"))

    assert answer["appVersion"] == APP_VERSION


def test_the_app_version_is_reported_without_a_state_database(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    # A container deployed a minute ago is exactly the one whose version has to
    # be readable: the protocol check of the other half may not wait for an index
    # to exist, otherwise the first minutes after an update are the minutes in
    # which nobody can tell a mismatch from a slow first pass.
    assert not (volume / "state.db").exists()

    answer = _status(client, sign("admin"))

    assert set(answer) == FIELDS
    assert answer["appVersion"] == APP_VERSION


def test_the_app_version_is_not_derived_from_the_index_marks(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # Three values, three sources, and none of them computed out of another. The
    # two marks say how the index was built, the app version says which release
    # is running, and a page that mixed them would answer a protocol question
    # with a reindex banner. Moving the marks therefore moves nothing here.
    store = open_store(indexed_volume.root / "state.db")
    store.write_meta("analyzer_version", "7")
    store.write_meta("index_version", "9")
    store.close()

    answer = _status(client, sign("admin"))

    assert answer["appVersion"] == APP_VERSION
    assert answer["analyzerVersion"] == 7
    assert answer["indexVersion"] == 9


def test_without_the_environment_variable_the_app_version_is_empty_and_the_answer_is_whole(
    monkeypatch: pytest.MonkeyPatch,
    volume: Path,
) -> None:
    # Asked of report() and not through the client, and that is not convenience.
    # The AppAPI middleware builds a session object per request which reads
    # APP_VERSION itself, so a request that arrives without the variable never
    # reaches this route at all; whether it should is AppAPI's business. What
    # belongs to this route is the shape of its answer, and it stays whole: every
    # field is there and the version is an empty string rather than a missing key,
    # because a page that has to ask whether a key exists writes one default in
    # its template and a different one in its script.
    assert not (volume / "state.db").exists()
    monkeypatch.delenv("APP_VERSION", raising=False)

    answer = report().model_dump()

    assert set(answer) == FIELDS
    assert answer["appVersion"] == ""


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
    assert answer["embedded"] == 0
    assert answer["reasons"] == {}
    assert answer["aclRows"] == 0
    assert answer["docs"] == 0
    assert answer["indexBytes"] == 0
    assert answer["note"] != ""


def test_a_zero_byte_state_database_is_an_answer_and_not_a_server_error(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    # A kill between sqlite3.connect and the schema script leaves exactly this
    # file behind: it opens cleanly and the first query raises "no such table".
    # The contract of this route says a broken state is an answer, never a 500,
    # and the banner of the admin page depends on it (review finding WR-01).
    (volume / "state.db").touch()

    answer = _status(client, sign("admin"))

    assert set(answer) == FIELDS
    assert answer["indexed"] == 0
    assert answer["note"] == STATE_UNREADABLE


def test_a_state_file_that_is_no_database_is_an_answer_and_not_a_server_error(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    # The other realistic shape of a broken state: the file exists and is not
    # SQLite at all, so the open itself raises DatabaseError rather than OSError
    # (review finding WR-01).
    (volume / "state.db").write_bytes(b"this is not a sqlite database")

    answer = _status(client, sign("admin"))

    assert set(answer) == FIELDS
    assert answer["indexed"] == 0
    assert answer["note"] == STATE_UNREADABLE


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
    # container has had five since plan 04-07. A test whose name has to be
    # corrected alongside the assertion is a test that will one day only have
    # the assertion corrected.
    #
    # Asked through the OpenAPI description rather than by walking APP.routes.
    # Measured on fastapi 0.141.1: an included router sits in the route list as a
    # private wrapper object with no path of its own, so a test that walked the
    # list would have to unwrap a private type and would be green for the wrong
    # reason on the release that renames it.
    paths = set(APP.openapi()["paths"])

    assert {"/search", "/snippets", "/status", "/rates", "/diagnose"} <= paths


def test_the_status_module_opens_the_state_read_only() -> None:
    # A static check, because the wrong call would pass every test in this file:
    # the writing connection answers the same questions, it just also lets a
    # defect in a read path change the operating state.
    source = STATUS_SOURCE.read_text(encoding="utf-8")

    assert "open_read_only" in source
    assert "open_store" not in source


def test_the_second_track_figure_says_in_words_that_it_lives_inside_indexed() -> None:
    # The counters of this answer are read by a page that puts them next to each
    # other, and two of them are subsets of a third. That is invisible in the
    # numbers and it is the one mistake that stays plausible after it is made:
    # an addition of indexed and embedded produces a total larger than the
    # corpus, on a page whose entire purpose is that the admin can trust it.
    source = STATUS_SOURCE.read_text(encoding="utf-8")

    assert source.count("embedded") >= 2
    assert source.count("Contained in indexed above and never added next to it") == 2


def test_no_field_of_the_answer_is_spread_out_of_a_row() -> None:
    # T-04-06 held statically, because the behaviour tests cannot see it: the
    # files table carries path and title, and a spread would put both on the
    # wire in the same commit that meant to add a counter.
    source = STATUS_SOURCE.read_text(encoding="utf-8")

    assert "**row" not in source


def test_the_status_module_carries_neither_dash() -> None:
    # Written over the code points so that this file does not carry the two
    # characters it exists to keep out, the same device the UI gate uses.
    source = STATUS_SOURCE.read_text(encoding="utf-8")
    assert EM_DASH not in source
    assert EN_DASH not in source


def test_asking_for_the_status_changes_nothing(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    database = indexed_volume.root / "state.db"
    before = database.read_bytes()

    _status(client, sign("admin"))

    assert database.read_bytes() == before
