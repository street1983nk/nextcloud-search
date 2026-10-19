"""POST /similar: neighbour ids for one document, and nothing about anybody else's.

The route receives a file id from another process, so most of the claims here
are about who does not get an answer and what an answer does not carry. A
foreign source, an unknown one and a user without a permission row all get the
same empty list; a neighbour the prefilter does not confirm is absent; and the
JSON of an answer has exactly two keys at the top and one per candidate, so no
distance or score can ride along.

The vector stock is written by hand with vectors on the unit circle of the first
two axes, so a neighbour lies at a chosen distance on the int8 L2 scale without
a model. Two of them at angles a and b lie 127 * 2 * sin(|a - b| / 2) apart.
"""

import logging
import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from conftest import Corpus
from findling.api import resources
from findling.api import similar as api_similar
from findling.config import SEARCH_LIMIT_MAX
from findling.embed.model import DIMENSIONS, to_int8
from findling.index import search as index_search
from findling.main import APP
from findling.store.vectors import Chunk, open_vectors

pytestmark = pytest.mark.usefixtures("appapi_environment")

Sign = Callable[[str], dict[str, str]]

# alice and bob see the odd ids, bob alone sees the even ones, carol has no row.
ALICE_FILE = 1
BOB_FILE = 2
NEAR_OWN = 3
NEAR_FOREIGN = 4
FAR_OWN = 5
OUT_OF_REACH = 7


def _at(angle: float) -> bytes:
    return to_int8([math.cos(angle), math.sin(angle), *([0.0] * (DIMENSIONS - 2))])


def _stock_neighbours(root: Path) -> None:
    """ALICE_FILE at the origin, an own and a foreign neighbour close by, one far away."""
    placed = {
        ALICE_FILE: 0.0,
        BOB_FILE: 0.0,
        NEAR_FOREIGN: 0.05,
        NEAR_OWN: 0.10,
        FAR_OWN: 0.30,
        OUT_OF_REACH: 0.80,
    }
    stock = open_vectors(root / "vectors.db")
    try:
        for file_id, angle in placed.items():
            stock.replace_chunks(file_id, [Chunk(ordinal=0, char_start=0, char_end=40, embedding=_at(angle))])
    finally:
        stock.close()


def _similar(client: TestClient, headers: dict[str, str], **body: object) -> dict[str, Any]:
    response = client.post("/similar", json={"fileId": ALICE_FILE, "limit": 10, **body}, headers=headers)

    assert response.status_code == 200, response.text
    return response.json()


def _ids(answer: dict[str, Any]) -> list[int]:
    return [candidate["fileId"] for candidate in answer["candidates"]]


def test_a_confirmed_source_gets_its_confirmed_neighbours_and_never_itself(
    client: TestClient, sign: Sign, indexed_volume: Corpus
) -> None:
    _stock_neighbours(indexed_volume.root)

    answer = _similar(client, sign(indexed_volume.alice))

    assert _ids(answer) == [NEAR_OWN, FAR_OWN]
    assert ALICE_FILE not in _ids(answer)


def test_bob_sees_the_neighbour_alice_may_not_and_in_rank_order(
    client: TestClient, sign: Sign, indexed_volume: Corpus
) -> None:
    # The floor under the case above: the foreign neighbour is really there and
    # really near, so its absence for alice is the prefilter and not the scan.
    _stock_neighbours(indexed_volume.root)

    answer = _similar(client, sign(indexed_volume.bob))

    assert _ids(answer) == [BOB_FILE, NEAR_FOREIGN, NEAR_OWN, FAR_OWN]


def test_the_answer_carries_ids_and_the_flag_and_nothing_else(
    client: TestClient, sign: Sign, indexed_volume: Corpus
) -> None:
    _stock_neighbours(indexed_volume.root)

    answer = _similar(client, sign(indexed_volume.alice))

    assert set(answer) == {"candidates", "degraded"}
    assert answer["candidates"]
    assert all(set(candidate) == {"fileId"} for candidate in answer["candidates"])
    assert answer["degraded"] is False


def test_a_source_only_bob_may_see_answers_alice_with_nothing(
    client: TestClient, sign: Sign, indexed_volume: Corpus
) -> None:
    _stock_neighbours(indexed_volume.root)

    answer = _similar(client, sign(indexed_volume.alice), fileId=BOB_FILE)

    assert answer["candidates"] == []


def test_an_unknown_source_and_a_user_without_a_row_get_nothing(
    client: TestClient, sign: Sign, indexed_volume: Corpus
) -> None:
    _stock_neighbours(indexed_volume.root)

    assert _similar(client, sign(indexed_volume.bob), fileId=999_999)["candidates"] == []
    assert _similar(client, sign(indexed_volume.carol))["candidates"] == []


def test_the_limit_caps_the_answer(client: TestClient, sign: Sign, indexed_volume: Corpus) -> None:
    _stock_neighbours(indexed_volume.root)

    assert _ids(_similar(client, sign(indexed_volume.bob), limit=2)) == [BOB_FILE, NEAR_FOREIGN]


def test_user_id_in_the_body_is_rejected(client: TestClient, sign: Sign) -> None:
    response = client.post("/similar", json={"fileId": 1, "limit": 5, "userId": "bob"}, headers=sign("alice"))

    assert response.status_code == 400
    assert response.json()["detail"] == "user identity is taken from the AppAPI header only"


@pytest.mark.parametrize(
    "body",
    [
        {"fileId": 0, "limit": 5},
        {"fileId": 1, "limit": 0},
        {"fileId": 1, "limit": SEARCH_LIMIT_MAX + 1},
        {"fileId": 1},
    ],
    ids=["file-id-zero", "limit-zero", "limit-over-the-cap", "limit-missing"],
)
def test_a_body_out_of_bounds_is_refused(client: TestClient, sign: Sign, body: dict[str, int]) -> None:
    response = client.post("/similar", json=body, headers=sign("alice"))

    assert response.status_code == 422


def test_missing_user_id_is_unauthorized(client: TestClient, sign: Sign) -> None:
    response = client.post("/similar", json={"fileId": 1, "limit": 5}, headers=sign(""))

    assert response.status_code == 401


def test_a_request_without_any_appapi_header_is_unauthorized(client: TestClient) -> None:
    response = client.post("/similar", json={"fileId": 1, "limit": 5})

    assert response.status_code == 401


def test_the_route_needs_no_model(
    client: TestClient, sign: Sign, indexed_volume: Corpus, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The seam every other read route builds its model through, made to fail.
    # The neighbours come out of the stored vectors, so the answer is the same.
    _stock_neighbours(indexed_volume.root)

    def no_model() -> object:
        message = "the model must not be loaded for similar documents"
        raise AssertionError(message)

    monkeypatch.setattr(resources, "query_model", no_model)

    assert _ids(_similar(client, sign(indexed_volume.alice))) == [NEAR_OWN, FAR_OWN]


def test_a_failure_answers_empty_and_logs_only_a_type_name(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # The library message names the file and the user on purpose: the log line
    # of the route must carry neither.
    def broken(*args: object) -> list[int]:
        message = f"file {args[3]} of {args[2]} could not be read"
        raise RuntimeError(message)

    monkeypatch.setattr(index_search, "similar_candidates", broken)

    with caplog.at_level(logging.DEBUG, logger="findling.api.similar"):
        answer = _similar(client, sign(indexed_volume.alice), fileId=4711)

    assert answer["candidates"] == []
    assert answer["degraded"] is True
    lines = [record.getMessage() for record in caplog.records if record.name == "findling.api.similar"]
    assert lines == ["finding similar documents ended in an unexpected RuntimeError"]
    assert all("4711" not in record.getMessage() for record in caplog.records)
    assert all(indexed_volume.alice not in record.getMessage() for record in caplog.records)


def test_a_missing_index_answers_empty_and_degraded(client: TestClient, sign: Sign, volume: Path) -> None:
    assert not (volume / "index").exists()

    answer = _similar(client, sign("alice"))

    assert answer == {"candidates": [], "degraded": True}


def test_the_route_is_registered_exactly_once() -> None:
    # Read off the application itself rather than off the source, so the
    # registration in main.py is what is checked and not the decorator. The
    # schema of the app lists every mounted path once per verb; included
    # routers do not show their paths on APP.routes in this FastAPI.
    paths = APP.openapi()["paths"]

    assert list(paths).count("/similar") == 1
    assert set(paths["/similar"]) == {"post"}
    assert api_similar.ROUTER.routes, "the router of the module declares the route"
