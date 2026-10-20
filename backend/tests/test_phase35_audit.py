"""Source probes of the phase 35 audit (plan 35-12), pinned as regression tests.

The live half of the audit ran against the development instance on 8090 and is
recorded with commands and results in
``.planning/phases/35-stretch-aehnliche-dokumente-und-spikes/35-AUDIT.md``.
What stays here is the half a checkout can prove on its own: the order of the
two permission questions, the route table, the prefilter count and the shape of
the log lines. Each of these held on audit day, and each is the kind of
property a later edit can break without any functional test noticing, because
every one of them is about absence or order rather than about behaviour.

Why a grep and not a functional test is argued at length in
``test_php_acl_boundary.py``; the short form is that a second call, a declared
route or a log line with a file id would sit next to green assertions forever.
The probes below read the sources the way that file does, against the one file
that owns each property, so a change trips the probe that names its reason.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SEARCH_SERVICE = REPO / "php" / "lib" / "Service" / "SearchService.php"
EXAPP_SERVICE = REPO / "php" / "lib" / "Service" / "ExAppService.php"
SIMILAR_ROUTE = REPO / "backend" / "src" / "findling" / "api" / "similar.py"
INDEX_SEARCH = REPO / "backend" / "src" / "findling" / "index" / "search.py"
INFO_XML = REPO / "backend" / "appinfo" / "info.xml"


def _method_body(source: str, marker: str) -> str:
    """The text of one PHP method, from its signature to the next method.

    Cut by the signature line and the following ``public``/``private``
    declaration rather than by brace counting: the probes below look for call
    sites whose spelling cannot appear in a comment, so the rough cut is
    enough, and a parser would be a dependency for four assertions.
    """
    start = source.index(marker)
    tail = source[start:]
    after = re.search(r"\n\t(?:public|private|protected) ", tail[1:])
    return tail if after is None else tail[: after.start() + 1]


def test_the_source_is_rechecked_before_the_container_is_asked() -> None:
    """S1: in SearchService::similar the permission question precedes the call.

    The audit probe on the instance showed no ``POST /similar`` for a foreign
    source; this is the structural half of the same claim. The two spellings
    are call sites and appear in no comment of the method.
    """
    body = _method_body(SEARCH_SERVICE.read_text(encoding="utf-8"), "public function similar(")
    recheck = body.index("self::readableFile(")
    container = body.index("$this->exApp->similarCandidates(")
    assert recheck < container


def test_the_similar_route_stays_out_of_the_route_table() -> None:
    """S5: /similar is a content route and is not declared in info.xml.

    The companion reaches it over the signed AppAPI path, which never consults
    the route table; a declared route would open it to the proxy. The audit
    fired the route unsigned and with a wrong secret and got 401 both times.
    """
    assert re.search(r"<url>[^<]*similar", INFO_XML.read_text(encoding="utf-8")) is None


def test_the_prefilter_is_called_exactly_twice_in_the_search_module() -> None:
    """The counting gate of plan 35-05, repeated by the audit.

    Two call sites of the permission prefilter in ``index/search.py``: the
    search path and the similar path. A third one would mean a new place makes
    permission claims, a single one would mean one of the two paths stopped
    asking.
    """
    assert INDEX_SEARCH.read_text(encoding="utf-8").count("prefilter_visible") == 2


def test_no_log_line_of_the_similar_code_names_a_file_or_user() -> None:
    """S6: the log lines of the new code carry no file id, path, title or user.

    The instance half of the probe scanned nextcloud.log and the backend log
    after the audit rounds and found no title of a test file. This half pins
    the shape of the statements themselves, in the three places phase 35 added
    log calls.
    """
    route = SIMILAR_ROUTE.read_text(encoding="utf-8")
    for line in route.splitlines():
        if "LOGGER." in line:
            assert "file_id" not in line
            assert "user_id" not in line
            assert "fileId" not in line

    similar_body = _method_body(SEARCH_SERVICE.read_text(encoding="utf-8"), "public function similar(")
    candidates_body = _method_body(EXAPP_SERVICE.read_text(encoding="utf-8"), "public function similarCandidates(")
    for body in (similar_body, candidates_body):
        for call in re.findall(r"logger->\w+\([^;]*;", body):
            assert "$sourceId" not in call
            assert "$candidateId" not in call
            assert "$uid" not in call
            assert "title" not in call.lower()
            assert "getPath" not in call


def test_the_log_probe_sees_a_planted_file_id() -> None:
    """Positive control of the probe above, on a synthetic statement."""
    planted = "$this->logger->warning('x', ['id' => $sourceId]);"
    found = re.findall(r"logger->\w+\([^;]*;", planted)
    assert found
    assert "$sourceId" in found[0]
