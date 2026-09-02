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
"""

import sqlite3
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from conftest import Corpus
from findling.api.diagnose import NOT_JUDGED
from findling.main import APP
from findling.store.repo import FileMeta, open_store

pytestmark = pytest.mark.usefixtures("appapi_environment")

Sign = Callable[[str], dict[str, str]]

DIAGNOSE_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "api" / "diagnose.py"

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
    "note",
}

# A path and a title no fixture produces, so their absence from the answer cannot
# be an accident of the corpus.
PRIVATE_PATH = "/Personalakten/Kuendigung-Mueller.pdf"
PRIVATE_TITLE = "Kuendigung-Mueller.pdf"
PRIVATE_FILE_ID = 7001


def _diagnose(client: TestClient, headers: dict[str, str], file_id: int) -> dict[str, Any]:
    response = client.get("/diagnose", headers=headers, params={"fileId": file_id})

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
