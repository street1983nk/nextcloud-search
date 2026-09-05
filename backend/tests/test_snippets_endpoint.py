"""POST /snippets: the only answer of this container that carries file content.

Which is why the claims here are mostly about who does not get one. A snippet is
document text, SRCH-02 says it is produced after the permission check and never
before, and this endpoint receives its file ids from another process. That the
caller only sends ids that survived its recheck is an assumption about a
different program running correctly, and an endpoint that relies on it is a
confused deputy: whoever reaches the proxy could ask for the content of any
document by its number.

The offsets are the second reason this file exists. The engine reports byte
ranges and the wire protocol promises characters, so the corpus puts two multi
byte characters in front of every match; without them both conventions produce
the same numbers and the assertion would be green either way.
"""

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from conftest import Corpus, body_of
from findling.api import resources
from findling.embed.model import DIMENSIONS, EmbedOutcome
from findling.store.vectors import Chunk, open_vectors

pytestmark = pytest.mark.usefixtures("appapi_environment")

Sign = Callable[[str], dict[str, str]]

TERM = "Kündigungsfrist"

# A line that occurs in no document of this corpus, which the floor assertion of
# the semantic case states rather than assumes.
PARAPHRASE = "Weltraumbahnhof"

# How much of the body the stored chunk of the semantic case covers. Short
# enough to be well under the excerpt cap, so the assertion is about the place
# of the cut and not about its length.
PASSAGE_CHARS = 30

# An odd file id, so alice may see it and bob may see it. Even ids belong to bob
# alone, which is what the prefilter claim below rests on.
ALICE_FILE = 1
BOB_FILE = 2


class _Model:
    """A stand-in that answers one vector, so no 118 MB artifact has to exist.

    The read side builds its model through ``resources.query_model``, and that
    is the seam these cases replace: constructing the real wrapper loads
    nothing, but a container without the artifact answers the honest
    ``embedding_unavailable`` verdict and the semantic path would never run.
    """

    def embed_query(self, text: str) -> EmbedOutcome:
        return EmbedOutcome.ready([tuple(1.0 if index == 1 else 0.0 for index in range(DIMENSIONS))])


def _stock_one_chunk(root: Path) -> None:
    """Put one chunk over the opening of alice's document into the stock."""
    stock = open_vectors(root / "vectors.db")
    try:
        stock.replace_chunks(
            ALICE_FILE,
            [
                Chunk(
                    ordinal=0,
                    char_start=0,
                    char_end=PASSAGE_CHARS,
                    embedding=bytes(127 if index == 1 else 0 for index in range(DIMENSIONS)),
                )
            ],
        )
    finally:
        stock.close()


def _snippets(client: TestClient, headers: dict[str, str], **body: object) -> dict[str, Any]:
    response = client.post(
        "/snippets",
        json={"query": TERM, "fileIds": [ALICE_FILE], **body},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    return response.json()["snippets"]


def test_a_confirmed_file_id_gets_a_fragment(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _snippets(client, sign(indexed_volume.alice))

    assert set(answer) == {str(ALICE_FILE)}
    assert TERM.lower() in answer[str(ALICE_FILE)]["text"].lower()


def test_the_highlights_count_characters_and_not_bytes(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # Two umlauts stand in front of the match, so a byte range would cut two
    # characters too far to the right and the slice would start mid word.
    snippet = _snippets(client, sign(indexed_volume.alice))[str(ALICE_FILE)]

    assert snippet["highlights"], "the term is in the text, so it must be marked"
    for start, end in snippet["highlights"]:
        assert 0 <= start < end <= len(snippet["text"])
    marked = snippet["text"][snippet["highlights"][0][0] : snippet["highlights"][0][1]]
    assert marked.lower().startswith("kündigung")


def test_fragment_has_no_markup(client: TestClient, sign: Sign, indexed_volume: Corpus) -> None:
    # The unified search UI renders the subline as Vue text interpolation, so a
    # tag would reach the user literally instead of being rendered. The engine
    # offers to_html() and this path never calls it.
    text = _snippets(client, sign(indexed_volume.alice))[str(ALICE_FILE)]["text"]

    assert "<" not in text
    assert ">" not in text


def test_a_file_id_the_prefilter_does_not_confirm_is_absent(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # alice asks for a document only bob may see, together with one of her own.
    # The missing key is the whole answer: there is no message that would tell a
    # caller whether that file exists.
    answer = _snippets(client, sign(indexed_volume.alice), fileIds=[ALICE_FILE, BOB_FILE])

    assert set(answer) == {str(ALICE_FILE)}


def test_a_user_without_a_permission_row_gets_nothing(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _snippets(client, sign(indexed_volume.carol), fileIds=[ALICE_FILE, BOB_FILE])

    assert answer == {}


def test_an_unknown_file_id_is_simply_absent(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _snippets(client, sign(indexed_volume.bob), fileIds=[999_999])

    assert answer == {}


def test_user_id_in_the_body_is_rejected(client: TestClient, sign: Sign) -> None:
    response = client.post(
        "/snippets",
        json={"query": TERM, "fileIds": [1], "userId": "bob"},
        headers=sign("alice"),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "user identity is taken from the AppAPI header only"


def test_more_than_a_hundred_file_ids_are_rejected(client: TestClient, sign: Sign) -> None:
    # The provider never asks for more than its display limit, so this only
    # bounds a caller that has gone wrong.
    response = client.post(
        "/snippets",
        json={"query": TERM, "fileIds": list(range(1, 102))},
        headers=sign("alice"),
    )

    assert response.status_code == 422


def test_exactly_a_hundred_file_ids_are_accepted(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    response = client.post(
        "/snippets",
        json={"query": TERM, "fileIds": list(range(1, 101))},
        headers=sign(indexed_volume.bob),
    )

    assert response.status_code == 200
    assert len(response.json()["snippets"]) == indexed_volume.documents


def test_missing_user_id_is_unauthorized(client: TestClient, sign: Sign) -> None:
    response = client.post("/snippets", json={"query": TERM, "fileIds": [1]}, headers=sign(""))

    assert response.status_code == 401


def test_a_request_without_any_appapi_header_is_unauthorized(client: TestClient) -> None:
    response = client.post("/snippets", json={"query": TERM, "fileIds": [1]})

    assert response.status_code == 401


def test_a_missing_index_answers_without_snippets(client: TestClient, sign: Sign, volume: Path) -> None:
    # A hit without an excerpt is still a hit: the subline falls back to the path
    # on the PHP side. An exception here would cost the user the whole search.
    assert not (volume / "index").exists()

    assert _snippets(client, sign("alice")) == {}


def test_the_artificial_delay_costs_time_and_changes_nothing(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The measuring aid of plan 02-14: it proves that the provider keeps its
    # 2.5 second wall clock and shows hits without an excerpt rather than none.
    # It may delay and nothing else, which is what the second assertion states.
    headers = sign(indexed_volume.bob)
    undelayed = _snippets(client, headers)

    monkeypatch.setenv("FINDLING_ARTIFICIAL_DELAY_MS", "150")
    started = time.monotonic()
    delayed = _snippets(client, headers)
    elapsed = time.monotonic() - started

    assert elapsed >= 0.15
    assert delayed == undelayed


def test_a_line_that_is_in_no_document_gets_no_fragment(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The floor under the case below. Without it a green semantic excerpt could
    # just mean that the line matched lexically after all.
    answer = _snippets(client, sign(indexed_volume.alice), query=PARAPHRASE)

    assert answer[str(ALICE_FILE)]["text"] == ""


def test_the_route_hands_the_raw_line_and_the_stock_to_the_second_path(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The wiring of this plan, end to end: the route passes the raw search line
    # and the vector stock, so a hit whose words do not occur in the document
    # still shows the passage that matched. The rewritten query could not do
    # this: a model needs words and a parsed query is not text any more.
    _stock_one_chunk(indexed_volume.root)
    monkeypatch.setattr(resources, "query_model", _Model)

    answer = _snippets(client, sign(indexed_volume.alice), query=PARAPHRASE)

    assert answer[str(ALICE_FILE)]["text"] == body_of(ALICE_FILE)[:PASSAGE_CHARS]
    assert answer[str(ALICE_FILE)]["highlights"] == []


def test_the_second_path_hangs_on_the_same_permission_check(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The chunk sits on an odd file id, so bob and alice may see it and carol
    # may not. A second excerpt path that produced text for carol would be the
    # confused deputy this endpoint exists to not be.
    _stock_one_chunk(indexed_volume.root)
    monkeypatch.setattr(resources, "query_model", _Model)

    answer = _snippets(client, sign(indexed_volume.carol), query=PARAPHRASE)

    assert answer == {}


def test_an_unusable_delay_is_ignored(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Same rule as every other variable this container reads: a value that cannot
    # be used falls back to the default instead of stopping anything.
    monkeypatch.setenv("FINDLING_ARTIFICIAL_DELAY_MS", "-1")

    assert _snippets(client, sign(indexed_volume.alice)) != {}
