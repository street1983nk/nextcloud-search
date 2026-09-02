"""GET /rates: the measured throughput of the running pass, and nothing about its documents.

Same contract as ``test_status_endpoint.py`` and for the same reason: the field
set is asserted as a whole, so a later plan that adds "the document that took the
longest" to help with support has to change this test on purpose rather than by
accident. The table this route counts over carries a path and a title for every
row (T-04-24).

The two behaviour claims are the ones the estimate of the admin page stands on. A
text document and a scanned one cost orders of magnitude apart, so a single
combined rate would put the wrong number on the page for every instance whose mix
is not the mix of the test corpus. And a window that saw nothing at all has to
answer zero, because a division by the length of an empty window is the shortest
way from an admin page to a 500.
"""

import sqlite3
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from conftest import Corpus
from findling.api.rates import STARTUP_OCR_PAGE_MS, WINDOW_SECONDS_MAX, WINDOW_SECONDS_MIN
from findling.main import APP

pytestmark = pytest.mark.usefixtures("appapi_environment")

Sign = Callable[[str], dict[str, str]]

RATES_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "api" / "rates.py"

FIELDS = {
    "docsPerHourText",
    "docsPerHourOcr",
    "windowSeconds",
    "bytesPerDoc",
    "docs",
    "indexBytes",
    "startupRateOcrMs",
    "note",
}


def _rates(client: TestClient, headers: dict[str, str], **params: int) -> dict[str, Any]:
    response = client.get("/rates", headers=headers, params=params)

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


def _mark_as_scanned(database: Path, file_ids: Sequence[int]) -> None:
    """Set ocr_used on the given rows, the way an OCR run would have.

    Written straight against the file rather than through the store, because
    ``Store.record`` takes the flag together with a whole verdict and would
    overwrite the timestamp the window test depends on.
    """
    connection = sqlite3.connect(database)
    try:
        connection.executemany(
            "UPDATE files SET ocr_used = 1 WHERE file_id = ?",
            [(file_id,) for file_id in file_ids],
        )
        connection.commit()
    finally:
        connection.close()


def _backdate(database: Path, seconds: int) -> None:
    """Move every indexed_at that far into the past."""
    connection = sqlite3.connect(database)
    try:
        connection.execute("UPDATE files SET indexed_at = indexed_at - ?", (seconds,))
        connection.commit()
    finally:
        connection.close()


def test_the_answer_carries_the_rates_and_nothing_else(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _rates(client, sign("admin"))

    assert set(answer) == FIELDS
    assert answer["docs"] == indexed_volume.documents
    assert answer["indexBytes"] > 0
    assert answer["windowSeconds"] > 0
    assert answer["startupRateOcrMs"] == STARTUP_OCR_PAGE_MS


def test_text_and_scanned_documents_are_counted_apart(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The whole reason this route exists as two rates: a page of OCR costs about
    # two seconds and a page of text costs nothing measurable, so one combined
    # figure would be wrong for every instance whose mix differs from the one it
    # was measured on.
    scanned = (1, 2, 3)
    _mark_as_scanned(indexed_volume.root / "state.db", scanned)

    answer = _rates(client, sign("admin"))

    assert answer["docsPerHourOcr"] == len(scanned)
    assert answer["docsPerHourText"] == indexed_volume.documents - len(scanned)


def test_a_window_without_a_single_document_answers_zero(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # Not an error and not a division by the length of an empty window: an
    # instance whose first pass finished last week has no throughput right now,
    # and the page has to fall back to its labelled startup value instead of
    # receiving a 500.
    _backdate(indexed_volume.root / "state.db", WINDOW_SECONDS_MAX)

    answer = _rates(client, sign("admin"), windowSeconds=WINDOW_SECONDS_MIN)

    assert answer["docsPerHourText"] == 0
    assert answer["docsPerHourOcr"] == 0
    assert answer["windowSeconds"] == WINDOW_SECONDS_MIN


def test_the_window_is_clamped_instead_of_refused(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # An admin page asking for a window does not need an error message for it,
    # so an absurd value is brought into the range the index can serve cheaply
    # rather than rejected (T-04-25, T-04-26).
    too_small = _rates(client, sign("admin"), windowSeconds=1)
    too_large = _rates(client, sign("admin"), windowSeconds=99_999_999)

    assert too_small["windowSeconds"] == WINDOW_SECONDS_MIN
    assert too_large["windowSeconds"] == WINDOW_SECONDS_MAX


def test_a_window_parameter_that_is_not_a_number_is_refused(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The clamp above is about a number out of range. Something that is not a
    # number at all is a defect of the caller and stays a validation error.
    response = client.get("/rates", headers=sign("admin"), params={"windowSeconds": "an hour or so"})

    assert response.status_code == 422


def test_the_bytes_per_document_are_measured_and_never_guessed(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _rates(client, sign("admin"))

    assert answer["bytesPerDoc"] == answer["indexBytes"] // answer["docs"]
    assert answer["bytesPerDoc"] > 0
    assert answer["note"] == ""


def test_without_a_state_database_the_answer_is_zeros_and_a_note(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    # A container that was deployed a minute ago. Not an error, and answering
    # with one would send an admin hunting for a defect that is a normal state.
    assert not (volume / "state.db").exists()

    answer = _rates(client, sign("admin"))

    assert set(answer) == FIELDS
    assert answer["docsPerHourText"] == 0
    assert answer["docsPerHourOcr"] == 0
    assert answer["docs"] == 0
    assert answer["bytesPerDoc"] == 0
    assert answer["note"] != ""


def test_the_answer_carries_no_path_no_file_name_and_no_search_term(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    _mark_as_scanned(indexed_volume.root / "state.db", (1, 2))

    answer = _rates(client, sign("admin"))

    for value in _strings(answer):
        assert "/" not in value
        assert "Akte" not in value


def test_a_request_without_any_appapi_header_is_unauthorized(client: TestClient) -> None:
    response = client.get("/rates")

    assert response.status_code == 401


def test_the_rates_module_opens_the_state_read_only() -> None:
    # A static check, because the wrong call would pass every test in this file:
    # the writing connection answers the same questions, it just also lets a
    # defect in a read path change the operating state.
    source = RATES_SOURCE.read_text(encoding="utf-8")

    assert "open_read_only" in source
    assert "open_store" not in source


def test_asking_for_the_rates_changes_nothing(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    database = indexed_volume.root / "state.db"
    before = database.read_bytes()

    _rates(client, sign("admin"))

    assert database.read_bytes() == before


def test_the_route_is_mounted() -> None:
    # Asked through the OpenAPI description rather than by walking APP.routes,
    # for the reason spelled out in test_status_endpoint.py.
    assert "/rates" in set(APP.openapi()["paths"])
