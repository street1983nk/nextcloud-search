"""GET /diagnose: the verdict of one file, and not a single character of its name.

Same contract as ``test_status_endpoint.py`` and ``test_rates_endpoint.py``, one
row narrower: the field set is asserted as a whole, so a later plan that adds
"the path, just for support" to this answer has to change this test on purpose
rather than by accident.

The claim that matters most here is the one about absence, and it is stronger
than on the two counting routes: this route is asked for exactly one file id, and
the row it reads carries a path and a title for that very file (T-04-40). So the
privacy test does not merely walk a breakdown of counters, it sets a path and a
title that could not arrive by chance and then demands their absence from the
answer.

The second claim is that a file nobody judged is an ordinary answer and not a
404. An admin who looks up a file that has never been reached gets the same field
set with zeros plus a note, because "this container has no verdict" is an answer
and a status code is not.

The third claim arrives with phase 6 and it is about where a hit came from. D-14
draws the line through this route: an origin mark is a statement about a search
and not about a file, so it would be a statement about a document the PHP recheck
has not confirmed yet if it travelled on the search path. Here it is an
administrator asking about one file they already named, admin side, and not once
per hit. The field set test of the candidate model over in
``test_search_endpoint.py`` is the other half of that line and it stays untouched.
"""

import sqlite3
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from conftest import Corpus
from findling.api import resources
from findling.api.diagnose import NO_ORIGIN, NOT_JUDGED
from findling.embed.model import DIMENSIONS, EmbedOutcome
from findling.index.fusion import BOTH, LEXICAL, SEMANTIC
from findling.main import APP
from findling.store.repo import FileMeta, open_store
from findling.store.vectors import Chunk, open_vectors

pytestmark = pytest.mark.usefixtures("appapi_environment")

Sign = Callable[[str], dict[str, str]]

_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src" / "findling"
DIAGNOSE_SOURCE = _SOURCE_ROOT / "api" / "diagnose.py"
# The two files the origin mark must not appear in, and the manifest that says
# who may ask this route anything at all.
API_SEARCH_SOURCE = _SOURCE_ROOT / "api" / "search.py"
INDEX_SEARCH_SOURCE = _SOURCE_ROOT / "index" / "search.py"
BACKEND_INFO = Path(__file__).resolve().parents[2] / "backend" / "appinfo" / "info.xml"

FIELDS = {
    "fileId",
    "state",
    "reason",
    "ocrUsed",
    "indexedAt",
    "attempts",
    "textChars",
    "deletedAt",
    "indexVersion",
    "embedded",
    "chunks",
    "note",
}

# The one key that is there only when it was asked for. It is absent and never
# null: a null origin would read as "this container looked and found nothing",
# which is a different sentence from "nobody asked".
ORIGIN = "origin"

# A path and a title no fixture produces, so their absence from the answer cannot
# be an accident of the corpus.
PRIVATE_PATH = "/Personalakten/Kuendigung-Mueller.pdf"
PRIVATE_TITLE = "Kuendigung-Mueller.pdf"
PRIVATE_FILE_ID = 7001

# A line every document of the corpus carries, and one no document carries. The
# pair is what separates a lexical hit from a purely semantic one.
TERM = "Kündigungsfrist"
PARAPHRASE = "Weltraumbahnhof"

# An odd file id, so it is the one the stocked chunk belongs to. Which user may
# see it does not matter here: this route is admin side and asks no prefilter.
STOCKED_FILE = 1
UNSTOCKED_FILE = 2


class _Model:
    """A stand-in that answers one vector, so no 118 MB artifact has to exist.

    The read side builds its model through ``resources.query_model``, and that
    is the seam these cases replace: constructing the real wrapper loads
    nothing, but a container without the artifact answers the honest
    ``embedding_unavailable`` verdict and the vector branch would never run.
    """

    def embed_query(self, text: str) -> EmbedOutcome:
        return EmbedOutcome.ready([tuple(1.0 if index == 1 else 0.0 for index in range(DIMENSIONS))])


def _stock_chunks(root: Path, file_id: int, total: int) -> None:
    """Give one document that many chunks, pointing at the vector of _Model."""
    stock = open_vectors(root / "vectors.db")
    try:
        stock.replace_chunks(
            file_id,
            [
                Chunk(
                    ordinal=ordinal,
                    char_start=ordinal * 20,
                    char_end=ordinal * 20 + 20,
                    embedding=bytes(127 if index == 1 else 0 for index in range(DIMENSIONS)),
                )
                for ordinal in range(total)
            ],
        )
    finally:
        stock.close()


def _diagnose(
    client: TestClient,
    headers: dict[str, str],
    file_id: int,
    query: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {"fileId": file_id}
    if query is not None:
        params["query"] = query
    response = client.get("/diagnose", headers=headers, params=params)

    assert response.status_code == 200, response.text
    return response.json()


def _strings(value: Any) -> Iterator[str]:
    """Every string in the answer, keys of nested mappings included."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():  # pyright: ignore[reportUnknownVariableType]
            yield from _strings(key)
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:  # pyright: ignore[reportUnknownVariableType]
            yield from _strings(item)


def _write_named_row(database: Path, state: str, reason: str | None) -> None:
    """One judged row whose path and title are unmistakable."""
    store = open_store(database)
    meta = FileMeta(
        storage_id=1,
        root_id=1,
        path=PRIVATE_PATH,
        title=PRIVATE_TITLE,
        mime="application/pdf",
        size=4096,
        mtime=1_700_000_000,
    )
    store.record(PRIVATE_FILE_ID, meta, state, reason, text_chars=1234, ocr_used=True)
    store.close()


def test_the_answer_carries_the_verdict_and_nothing_else(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _diagnose(client, sign("admin"), 1)

    assert set(answer) == FIELDS
    assert answer["fileId"] == 1
    assert answer["state"] == "indexed"
    assert answer["reason"] == ""
    assert answer["indexedAt"] > 0
    assert answer["attempts"] == 1
    assert answer["deletedAt"] == 0
    assert answer["note"] == ""


def test_a_file_id_without_a_row_answers_with_zeros_and_a_note(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The ordinary case of this route: an admin looks up a file the crawl has not
    # reached. Answering 404 would send them hunting for a defect, and the honest
    # answer is the same field set with nothing in it plus the sentence saying so.
    answer = _diagnose(client, sign("admin"), 999_999)

    assert set(answer) == FIELDS
    assert answer["fileId"] == 999_999
    assert answer["state"] == ""
    assert answer["reason"] == ""
    assert answer["indexedAt"] == 0
    assert answer["attempts"] == 0
    assert answer["note"] == NOT_JUDGED


def test_a_file_id_below_one_answers_with_the_note_rather_than_an_error(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # An admin page needs no error message for a number. Zero and a negative id
    # cannot name a file, so they get the same answer as a file nobody judged.
    for file_id in (0, -5):
        answer = _diagnose(client, sign("admin"), file_id)

        assert set(answer) == FIELDS
        assert answer["state"] == ""
        assert answer["note"] == NOT_JUDGED


def test_without_a_state_database_the_answer_is_zeros_and_a_note(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    # A container that was deployed a minute ago. Not an error, and answering
    # with one would send an admin hunting for a defect that is a normal state.
    assert not (volume / "state.db").exists()

    answer = _diagnose(client, sign("admin"), 42)

    assert set(answer) == FIELDS
    assert answer["fileId"] == 42
    assert answer["state"] == ""
    assert answer["note"] == NOT_JUDGED


def test_a_zero_byte_state_database_is_an_answer_and_not_a_server_error(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    # A kill between sqlite3.connect and the schema script leaves exactly this
    # file behind: it opens cleanly and the first query raises "no such table".
    # The docstring of the report promises never to raise, so a broken state is
    # the no-verdict answer and never a 500 (review finding WR-01).
    (volume / "state.db").touch()

    answer = _diagnose(client, sign("admin"), 42)

    assert set(answer) == FIELDS
    assert answer["fileId"] == 42
    assert answer["state"] == ""
    assert answer["note"] == NOT_JUDGED


def test_a_state_file_that_is_no_database_is_an_answer_and_not_a_server_error(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    # The other realistic shape: the file is not SQLite at all, so the open
    # itself raises DatabaseError rather than OSError (review finding WR-01).
    (volume / "state.db").write_bytes(b"this is not a sqlite database")

    answer = _diagnose(client, sign("admin"), 42)

    assert set(answer) == FIELDS
    assert answer["fileId"] == 42
    assert answer["state"] == ""
    assert answer["note"] == NOT_JUDGED


def test_the_answer_carries_no_path_and_no_title_although_the_row_holds_both(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The most important test of this file. The row this route reads carries a
    # path and a title, and the fields are built one by one for exactly that
    # reason: a row spread would put both on the wire the day somebody adds a
    # column (T-04-40, D-03).
    _write_named_row(indexed_volume.root / "state.db", "skipped", "too_large")

    answer = _diagnose(client, sign("admin"), PRIVATE_FILE_ID)

    assert answer["state"] == "skipped"
    assert answer["reason"] == "too_large"
    assert answer["textChars"] == 1234
    assert answer["ocrUsed"] is True
    for value in _strings(answer):
        assert "/" not in value
        assert PRIVATE_TITLE not in value
        assert "Mueller" not in value
        assert "Kuendigung" not in value


def test_a_tombstone_is_handed_over_as_a_timestamp_and_never_as_a_label(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # Pitfall 6: a tombstone means "removed from the index" and not "the file is
    # gone". Only the Nextcloud side can tell those apart, because only it can
    # see whether the file still has a cache entry, so this route hands over the
    # number and translates nothing.
    store = open_store(indexed_volume.root / "state.db")
    store.tombstone(2, at=1_700_000_500)
    store.close()

    answer = _diagnose(client, sign("admin"), 2)

    assert answer["deletedAt"] == 1_700_000_500
    # The verdict is untouched by the mark, and no field of the answer turns the
    # timestamp into a word. Only the values are walked here and not the keys:
    # the key is the name of the number and the values are what could carry a
    # reading of it.
    assert answer["state"] == "indexed"
    for value in answer.values():
        if isinstance(value, str):
            assert "delete" not in value.lower()
            assert "gone" not in value.lower()


def test_the_two_new_fields_say_whether_one_file_has_vectors_and_how_many(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The per file half of D-16. The status page answers "how many documents
    # carry a vector"; this route answers it for the one document an admin
    # named, which is the question that follows it: a paraphrase does not find
    # this file, and the honest reason is either "no vector yet" or something
    # else entirely.
    _stock_chunks(indexed_volume.root, STOCKED_FILE, 3)

    answer = _diagnose(client, sign("admin"), STOCKED_FILE)

    assert set(answer) == FIELDS
    assert answer["embedded"] is True
    assert answer["chunks"] == 3
    assert answer["state"] == "indexed"


def test_a_document_without_vectors_says_so_instead_of_leaving_the_fields_out(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The ordinary state of the first hours, and the field set does not change
    # for it: a page that has to ask whether a key exists writes one default in
    # its template and a different one in its script.
    _stock_chunks(indexed_volume.root, STOCKED_FILE, 1)

    answer = _diagnose(client, sign("admin"), UNSTOCKED_FILE)

    assert set(answer) == FIELDS
    assert answer["embedded"] is False
    assert answer["chunks"] == 0


def test_without_a_query_the_answer_carries_no_origin_at_all(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # Absent and not null. The origin is a statement about a search, so without
    # a search there is nothing to state, and a null would read as the verdict
    # "neither half found it" rather than as "nobody asked".
    answer = _diagnose(client, sign("admin"), STOCKED_FILE)

    assert ORIGIN not in answer
    assert set(answer) == FIELDS


def test_a_purely_semantic_hit_is_named_semantic_and_a_hit_of_both_halves_is_named_both(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The question this route was extended for: why is this document in that
    # list. The paraphrase occurs in no document of the corpus, so the engine
    # cannot have contributed it, and the term occurs in every one of them, so
    # both halves have.
    _stock_chunks(indexed_volume.root, STOCKED_FILE, 1)
    monkeypatch.setattr(resources, "query_model", _Model)

    semantic = _diagnose(client, sign("admin"), STOCKED_FILE, query=PARAPHRASE)
    both = _diagnose(client, sign("admin"), STOCKED_FILE, query=TERM)

    assert semantic[ORIGIN] == SEMANTIC
    assert both[ORIGIN] == BOTH


def test_a_document_only_the_engine_found_is_named_lexical(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The counter case of the one above, and the reason the pair is worth having:
    # a mark that said "semantic" for every document would be green in the case
    # above and useless.
    _stock_chunks(indexed_volume.root, STOCKED_FILE, 1)
    monkeypatch.setattr(resources, "query_model", _Model)

    answer = _diagnose(client, sign("admin"), UNSTOCKED_FILE, query=TERM)

    assert answer[ORIGIN] == LEXICAL


def test_a_document_neither_half_found_is_named_as_such_and_not_as_a_gap(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The fourth answer. "Neither" is a finding and it is the one an admin is
    # looking at when they type a line and a file they expected to see.
    _stock_chunks(indexed_volume.root, STOCKED_FILE, 1)
    monkeypatch.setattr(resources, "query_model", _Model)

    answer = _diagnose(client, sign("admin"), UNSTOCKED_FILE, query=PARAPHRASE)

    assert answer[ORIGIN] == NO_ORIGIN


def test_a_blank_query_is_no_query_at_all(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # A field an admin left empty arrives as an empty string, and answering it
    # with "neither half found it" would be a verdict about a search nobody ran.
    answer = _diagnose(client, sign("admin"), STOCKED_FILE, query="   ")

    assert ORIGIN not in answer


def test_without_a_vector_stock_the_second_track_is_empty_and_the_origin_is_still_answered(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A container built without the model, or one whose stock was thrown away.
    # Not an error anywhere: the lexical half of the answer is untouched, and
    # the origin of a document the engine found is still lexical.
    (indexed_volume.root / "vectors.db").unlink()
    monkeypatch.setattr(resources, "query_model", _Model)

    answer = _diagnose(client, sign("admin"), STOCKED_FILE, query=TERM)

    assert answer["embedded"] is False
    assert answer["chunks"] == 0
    assert answer[ORIGIN] == LEXICAL


def test_a_vector_file_that_is_no_database_is_an_answer_and_not_a_server_error(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The same rule as on the status route: a broken stock costs the two fields
    # of the second track and never the verdict of the first (WR-01).
    (indexed_volume.root / "vectors.db").write_bytes(b"this is not a sqlite database")

    answer = _diagnose(client, sign("admin"), STOCKED_FILE)

    assert set(answer) == FIELDS
    assert answer["embedded"] is False
    assert answer["chunks"] == 0
    assert answer["state"] == "indexed"


def test_the_answer_carries_no_text_field_with_a_query_or_without_one(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The field set as a set, on both shapes of the answer. The origin is the
    # first thing this route ever said about a search, and the shortest way from
    # here to a leak is a "matched passage" next to it: the offsets that would
    # make one are sitting in the stock this very answer counted.
    _stock_chunks(indexed_volume.root, STOCKED_FILE, 1)
    monkeypatch.setattr(resources, "query_model", _Model)

    asked = _diagnose(client, sign("admin"), STOCKED_FILE, query=TERM)
    plain = _diagnose(client, sign("admin"), STOCKED_FILE)

    assert set(asked) == FIELDS | {ORIGIN}
    assert set(plain) == FIELDS
    for name in ("text", "snippet", "body", "passage", "excerpt", "chunkText"):
        assert name not in asked
    for value in _strings(asked):
        assert PARAPHRASE not in value
        assert "Beschäftigten" not in value


def test_a_file_id_that_is_not_a_number_is_refused(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The signature takes an int, so anything else is a defect of the caller and
    # stays a validation error instead of arriving inside the handler as a 500.
    response = client.get("/diagnose", headers=sign("admin"), params={"fileId": "the invoice"})

    assert response.status_code == 422


def test_a_request_without_any_appapi_header_is_unauthorized(client: TestClient) -> None:
    response = client.get("/diagnose", params={"fileId": 1})

    assert response.status_code == 401


def test_the_diagnose_module_opens_the_state_read_only() -> None:
    # A static check, because the wrong call would pass every test in this file:
    # the writing connection answers the same question, it just also lets a
    # defect in a read path change the operating state.
    source = DIAGNOSE_SOURCE.read_text(encoding="utf-8")

    assert "open_read_only" in source
    assert "open_store" not in source


def test_the_answer_is_built_field_by_field_and_never_spread_from_the_row() -> None:
    # The static half of the privacy claim above. The behaviour test proves that
    # today's field set carries no name; this one proves the mechanism that keeps
    # it that way when a column is added to the table.
    source = DIAGNOSE_SOURCE.read_text(encoding="utf-8")

    assert "**row" not in source
    assert source.count("row[") >= 8


def test_the_origin_mark_is_asked_for_here_and_nowhere_on_the_search_path() -> None:
    # D-14 as a grep, because it is a property of where a name appears rather
    # than of what any single answer contains. An origin mark on the search path
    # would be a fourth value about a document the PHP recheck has not confirmed
    # yet, and the field set test of the candidate model is the other half of
    # this claim (T-06-30, T-06-43).
    assert "origins(" in DIAGNOSE_SOURCE.read_text(encoding="utf-8")
    assert "origins" not in API_SEARCH_SOURCE.read_text(encoding="utf-8")
    assert "origins" not in INDEX_SEARCH_SOURCE.read_text(encoding="utf-8")


def test_the_route_keeps_the_access_level_it_was_declared_with() -> None:
    # The route learned to say something new about a search, and that is exactly
    # the moment to assert that it did not also learn to answer to somebody
    # else. ADMIN guards the AppAPI proxy path; the effective guard of the path
    # this app walks is the admin only PHP route in front of it (pitfall 10).
    manifest = BACKEND_INFO.read_text(encoding="utf-8")
    block = manifest[manifest.index("<url>diagnose</url>") :]

    assert "<access_level>ADMIN</access_level>" in block[: block.index("</route>")]


def test_the_answer_contract_still_says_there_is_no_text_field(
    client: TestClient,
    sign: Sign,
) -> None:
    # The sentence of the module header is the reason the field set above is
    # what it is, and this plan added three fields to that model. The sentence
    # stays word for word, so a later reader finds the rule and not its remains.
    source = DIAGNOSE_SOURCE.read_text(encoding="utf-8")

    assert "there is no text field on this model and there is not going to be one" in source


def test_the_diagnose_module_carries_neither_dash() -> None:
    # Written over the code points, so that this file does not carry the two
    # characters it exists to keep out.
    source = DIAGNOSE_SOURCE.read_text(encoding="utf-8")

    assert chr(0x2014) not in source
    assert chr(0x2013) not in source


def test_asking_for_a_diagnosis_changes_nothing(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    database = indexed_volume.root / "state.db"
    before = database.read_bytes()

    _diagnose(client, sign("admin"), 1)

    assert database.read_bytes() == before


def test_the_route_is_mounted() -> None:
    # Asked through the OpenAPI description rather than by walking APP.routes,
    # for the reason spelled out in test_status_endpoint.py.
    assert "/diagnose" in set(APP.openapi()["paths"])


def test_a_row_of_a_newer_container_is_answered_without_the_extra_column(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The forward looking half of T-04-40. A column this build does not know
    # about must not travel, and it cannot, because every field of the answer is
    # named in the model. Written against the file directly, because the store
    # has no way to add a column and never will.
    database = indexed_volume.root / "state.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute("ALTER TABLE files ADD COLUMN owner_hint TEXT")
        connection.execute("UPDATE files SET owner_hint = ? WHERE file_id = 1", (PRIVATE_TITLE,))
        connection.commit()
    finally:
        connection.close()

    answer = _diagnose(client, sign("admin"), 1)

    assert set(answer) == FIELDS
    for value in _strings(answer):
        assert PRIVATE_TITLE not in value
