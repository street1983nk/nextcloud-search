"""POST /search: candidates, page marks, and the three things that must not leak.

This suite replaces the phase 1 file ``test_search_canary.py``. Its six claims
are all still here, they are just made against the new protocol: a body may not
name a user, a request without an identity gets 401, and the canary text stays
free of markup because the unified search UI interpolates the subline as text.

Three of the assertions below are about things that must be *absent*, and they
are the reason this file exists rather than a single happy path test:

* a candidate carries no name, no path and no text, because the answer leaves the
  container before the permission recheck has run,
* an ordinary search never sees the canary, because a diagnostic hit that mixes
  into real results is a diagnostic nobody can trust,
* a missing index answers empty and degraded rather than raising, because the
  unified search calls every provider in parallel and a throwing provider costs
  the user the whole search.
"""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from socket import gethostname
from typing import Any

import pytest
from fastapi.testclient import TestClient

from conftest import Corpus
from findling.api.search import CANARY_TITLE, Candidate, build_canary_hits
from findling.store.repo import open_store

pytestmark = pytest.mark.usefixtures("appapi_environment")

Sign = Callable[[str], dict[str, str]]

# Spelled out as a literal rather than read from the implementation: a test that
# reads the constant it guards follows a rename instead of catching it. The same
# string is frozen on the PHP side as ExAppService::CANARY_TITLE.
CANARY = "findling-canary"

TERM = "Kündigungsfrist"


def _search(client: TestClient, headers: dict[str, str], **body: object) -> dict[str, Any]:
    response = client.post("/search", json={"query": TERM, **body}, headers=headers)

    assert response.status_code == 200, response.text
    return response.json()


def test_a_candidate_carries_no_name_no_path_and_no_text(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _search(client, sign(indexed_volume.bob))

    candidates = answer["candidates"]
    assert candidates, "the corpus matches this term, so this must not be empty"
    for candidate in candidates:
        assert set(candidate) == {"fileId", "score", "mtime", "ext"}


def test_the_candidate_model_has_no_text_field() -> None:
    # The structural half of pitfall 5. A functional test cannot see this: the
    # result the user finally gets is filtered further down the line and looks
    # correct whether or not the model carries a text field.
    assert set(Candidate.model_fields) == {"fileId", "score", "mtime", "ext"}


def test_the_answer_carries_the_page_marks(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _search(client, sign(indexed_volume.bob), limit=3)

    assert answer["hasMore"] is True
    assert answer["nextOffset"] > 0
    assert answer["degraded"] is False


def test_the_next_page_does_not_repeat_the_first_one(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    headers = sign(indexed_volume.bob)
    first = _search(client, headers, limit=3)
    second = _search(client, headers, limit=3, offset=first["nextOffset"])

    ids_of_first = {candidate["fileId"] for candidate in first["candidates"]}
    ids_of_second = {candidate["fileId"] for candidate in second["candidates"]}
    assert ids_of_first
    assert ids_of_second
    assert ids_of_first & ids_of_second == set()


def test_a_candidate_is_only_returned_to_a_user_the_prefilter_confirms(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _search(client, sign(indexed_volume.alice), limit=100)

    file_ids = {candidate["fileId"] for candidate in answer["candidates"]}
    assert file_ids, "alice sees the odd file ids"
    assert all(file_id % 2 for file_id in file_ids)


def test_a_user_without_a_permission_row_gets_nothing(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # Half the security claim of this endpoint: an empty answer, not an
    # exception, and above all not the unfiltered list.
    answer = _search(client, sign(indexed_volume.carol), limit=100)

    assert answer["candidates"] == []


def test_title_only_leaves_the_document_text_out_of_the_question(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    headers = sign(indexed_volume.bob)

    assert _search(client, headers, titleOnly=False)["candidates"] != []
    assert _search(client, headers, titleOnly=True)["candidates"] == []


def test_user_id_in_the_body_is_rejected(client: TestClient, sign: Sign) -> None:
    response = client.post("/search", json={"query": "contract", "userId": "bob"}, headers=sign("alice"))

    assert response.status_code == 400
    assert response.json()["detail"] == "user identity is taken from the AppAPI header only"


def test_an_unknown_field_that_is_not_an_identity_stays_a_422(client: TestClient, sign: Sign) -> None:
    # A misspelled field is a typo, not an attack. Answering it with the identity
    # message would send whoever made the typo hunting for a security problem.
    response = client.post("/search", json={"query": "contract", "limitt": 5}, headers=sign("alice"))

    assert response.status_code == 422
    assert "limitt" in str(response.json()["detail"])


@pytest.mark.parametrize("limit", [0, 101])
def test_limit_out_of_range_is_rejected(client: TestClient, sign: Sign, limit: int) -> None:
    response = client.post("/search", json={"query": "contract", "limit": limit}, headers=sign("alice"))

    assert response.status_code == 422


def test_a_negative_offset_is_rejected(client: TestClient, sign: Sign) -> None:
    response = client.post("/search", json={"query": "contract", "offset": -1}, headers=sign("alice"))

    assert response.status_code == 422


def test_an_offset_past_the_ceiling_is_rejected(client: TestClient, sign: Sign) -> None:
    # Security audit C1: an unbounded offset makes tantivy allocate
    # (limit+offset)*24 bytes and aborts the process with a Rust allocation
    # failure no Python handler can catch. The model rejects it before the engine
    # is ever entered, so this stays a 422 and not a dead container.
    from findling.config import SEARCH_OFFSET_MAX

    response = client.post(
        "/search",
        json={"query": "contract", "offset": SEARCH_OFFSET_MAX + 1},
        headers=sign("alice"),
    )

    assert response.status_code == 422


def test_the_documented_offset_ceiling_is_accepted(client: TestClient, sign: Sign) -> None:
    # The boundary itself is a legitimate cursor and must answer normally.
    from findling.config import SEARCH_OFFSET_MAX

    response = client.post(
        "/search",
        json={"query": "contract", "offset": SEARCH_OFFSET_MAX},
        headers=sign("alice"),
    )

    assert response.status_code == 200


def test_an_overlong_query_is_rejected(client: TestClient, sign: Sign) -> None:
    # Security audit C2/M3: a megabyte-long query is seconds of CPU per request,
    # and the expansion runs against the live index. The length ceiling stops it
    # at the model.
    from findling.config import SEARCH_QUERY_MAX_CHARS

    response = client.post(
        "/search",
        json={"query": "a" * (SEARCH_QUERY_MAX_CHARS + 1)},
        headers=sign("alice"),
    )

    assert response.status_code == 422


def test_missing_user_id_is_unauthorized(client: TestClient, sign: Sign) -> None:
    # A signed header without a user name: the signature checks out, the identity
    # does not exist. Answering with results here would be the actual bug.
    response = client.post("/search", json={"query": "contract"}, headers=sign(""))

    assert response.status_code == 401


def test_a_request_without_any_appapi_header_is_unauthorized(client: TestClient) -> None:
    response = client.post("/search", json={"query": "contract"})

    assert response.status_code == 401


def test_a_request_with_the_wrong_secret_is_unauthorized(client: TestClient, sign: Sign) -> None:
    headers = sign("alice")
    # base64 of "alice:not-the-secret": right shape, wrong credential.
    headers["AUTHORIZATION-APP-API"] = "YWxpY2U6bm90LXRoZS1zZWNyZXQ="

    response = client.post("/search", json={"query": "contract"}, headers=headers)

    assert response.status_code == 401


def test_the_canary_answers_its_own_name(client: TestClient, sign: Sign, indexed_volume: Corpus) -> None:
    response = client.post("/search", json={"query": CANARY}, headers=sign(indexed_volume.bob))

    assert response.status_code == 200
    canaries = [candidate for candidate in response.json()["candidates"] if candidate["fileId"] == 0]
    assert len(canaries) == 1
    assert canaries[0]["title"] == CANARY
    assert indexed_volume.bob in canaries[0]["snippet"]


def test_an_ordinary_search_never_sees_the_canary(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _search(client, sign(indexed_volume.bob), limit=100)

    assert all(candidate["fileId"] > 0 for candidate in answer["candidates"])


def test_a_term_that_merely_contains_the_canary_word_does_not_summon_it(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # The comparison is exact, not "contains". Otherwise the canary colours every
    # search that happens to carry the word, and the one diagnostic this project
    # has stops being evidence of anything.
    answer = _search(client, sign(indexed_volume.bob), query=f"{CANARY} Vertrag")

    assert all(candidate["fileId"] > 0 for candidate in answer["candidates"])


def test_surrounding_space_still_reaches_the_canary(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    answer = _search(client, sign(indexed_volume.bob), query=f"  {CANARY}  ")

    assert [candidate["fileId"] for candidate in answer["candidates"]] == [0]


def test_a_missing_index_answers_empty_and_degraded(client: TestClient, sign: Sign, volume: Path) -> None:
    # A fresh container, deployed and not yet indexed. The unified search calls
    # every provider in parallel, so a throwing provider costs the user the whole
    # search rather than one result group.
    assert not (volume / "index").exists()

    answer = _search(client, sign("alice"))

    assert answer["candidates"] == []
    assert answer["degraded"] is True
    assert answer["hasMore"] is False


def test_the_canary_answers_even_without_an_index(client: TestClient, sign: Sign, volume: Path) -> None:
    # The diagnostic has to survive exactly the situation it is used in: somebody
    # is asking whether the container answers at all.
    assert not (volume / "index").exists()

    response = client.post("/search", json={"query": CANARY}, headers=sign("alice"))

    assert [candidate["fileId"] for candidate in response.json()["candidates"]] == [0]


def test_a_version_drift_is_degraded_but_still_answers(
    client: TestClient,
    sign: Sign,
    indexed_volume: Corpus,
) -> None:
    # Pitfall 14: the word list changed and the index did not, so queries are
    # tokenised differently than the documents were. Hits are still better than
    # silence, but the caller has to be told.
    store = open_store(indexed_volume.root / "state.db")
    store.write_meta("analyzer_version", "99")
    store.close()

    answer = _search(client, sign(indexed_volume.bob))

    assert answer["degraded"] is True
    assert answer["candidates"] != []


def test_canary_hit_carries_host_time_and_user() -> None:
    hits = build_canary_hits("alice")

    assert len(hits) == 1
    snippet = hits[0].snippet
    assert gethostname() in snippet
    assert "alice" in snippet
    # Read the timestamp back independently instead of rebuilding the format
    # string of the implementation: a shared pattern would prove nothing.
    stamp = snippet.split(" at ", maxsplit=1)[1].split(" for user ", maxsplit=1)[0]
    assert datetime.fromisoformat(stamp).tzinfo is not None


def test_canary_hit_carries_the_title_the_php_companion_accepts() -> None:
    # The companion resolves every hit with a file id above zero through the
    # user's own folder and drops whatever does not resolve. A hit with file id 0
    # never resolves, so this exact title is the only reason it reaches the user.
    hit = build_canary_hits("alice")[0]

    assert hit.fileId == 0
    assert hit.title == CANARY
    assert CANARY_TITLE == CANARY


def test_canary_snippet_has_no_markup() -> None:
    snippet = build_canary_hits("alice")[0].snippet

    # The unified search UI renders the subline as Vue text interpolation, so a
    # tag would reach the user literally instead of being rendered.
    assert "<" not in snippet
    assert ">" not in snippet
