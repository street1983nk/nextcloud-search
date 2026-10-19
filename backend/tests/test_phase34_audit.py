"""The probes of the phase 34 audit (34-AUDIT.md): the migration path.

Phase 34 put a new server check into every answer of the admin page and of its
five second poll (ParallelSearchService, the key parallelSearch of
AdminViewService::overview), a banner with an external link into the template,
a new sentence into 16 catalogues and public statements about a foreign app on
three pages. This module holds the audit probes as regression tests.

**Source probes (Docker, skipped without it).** ``token_get_all`` of PHP itself
on ``php:8.3-cli`` (a one-off script held here as a string) instead of the
regular expressions of the contract gate in ``test_admin_ui_contract.py``:
which tokens print, what reaches the href, where the URL comes from.

**Render probes (Docker).** The banner fragment of the real template, cut out
by position and run by PHP with a stub ``p()`` that escapes exactly as the
core does and a stub IL10N; the HTML is read with ``html.parser``, never with
a regular expression. The same harness answers the language map oracle.

**Instance probes, skipped without an instance.** Rights of a non admin, the
log after toggling a simulated app flag, the banner decision against rows of
``oc_appconfig`` read by SQL. They need these variables:

    FINDLING_AUDIT34_URL          http://localhost:8090
    FINDLING_AUDIT34_ADMIN_PASS   password of admin
    FINDLING_AUDIT34_USER         a non admin account
    FINDLING_AUDIT34_USER_PASS    its password
    FINDLING_AUDIT34_CONTAINER    name of the Nextcloud container (occ, log)

Every simulated flag is removed again in a ``finally``; the instance is left as
it was found (no row ``enabled`` for either app id).

Only ASCII in this file: every other character is written as an escape.
"""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import httpx
import pytest

REPO = Path(__file__).resolve().parents[2]
TEMPLATE = REPO / "php" / "templates" / "admin.php"
L10N_DIR = REPO / "php" / "l10n"
IMAGE = os.environ.get("FINDLING_AUDIT34_PHP_IMAGE", "php:8.3-cli")

APP_IDS = ("fulltextsearch", "files_fulltextsearch")
TAG_BASE = "https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/"
NEW_KEY = (
    "At least one app of the full text search framework (fulltextsearch, "
    "files_fulltextsearch) is enabled next to Findling. Results from the same "
    "file can then appear twice in the search bar. Disable these apps once "
    "Findling has finished its first index run."
)
LINK_KEY = "Steps in the documentation"

# The files phase 34 added or changed outside .planning, for the text probes
# that need no git history (git diff 00dbafab..a701b4f9, 39 files).
PHASE_FILES: tuple[str, ...] = (
    "CHANGELOG.md",
    "README.md",
    "README.en.md",
    "README.fr.md",
    "docs/admin-page.md",
    "docs/l10n-dutch.md",
    "docs/l10n-french.md",
    "docs/l10n-italian.md",
    "docs/l10n-portuguese.md",
    "docs/l10n-spanish.md",
    "docs/migrate-from-fulltextsearch.md",
    "docs/migrate-from-fulltextsearch.en.md",
    "docs/migrate-from-fulltextsearch.fr.md",
    "docs/store-listing.md",
    "php/css/admin.css",
    "php/lib/Service/AdminViewService.php",
    "php/lib/Service/ParallelSearchService.php",
    "php/templates/admin.php",
    "php/tests/Unit/ParallelSearchServiceTest.php",
    "php/tests/Unit/SettingsControllerTest.php",
    "backend/tests/test_admin_ui_contract.py",
    "backend/tests/test_measurement_scripts.py",
    "backend/tests/test_migration_path.py",
)

# ---------------------------------------------------------------------------
# Docker and PHP
# ---------------------------------------------------------------------------


def _docker() -> str:
    docker = shutil.which("docker")
    if docker is None:
        pytest.skip("docker is not available")
    probe = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [docker, "version", "--format", "{{.Server.Version}}"],
        capture_output=True,
        check=False,
        timeout=60,
    )
    if probe.returncode != 0:
        pytest.skip("docker is installed but its daemon does not answer")
    return docker


def run_php(script: str, payload: object) -> Any:
    """Run ``script`` (read from stdin) on the PHP image over the repository.

    The payload travels base64 encoded as the first argument, the answer is the
    JSON the script prints.
    """
    docker = _docker()
    arg = base64.b64encode(json.dumps(payload).encode()).decode()
    answer = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [docker, "run", "--rm", "-i", "-v", f"{REPO}:/app:ro", "-w", "/app", IMAGE, "php", "--", arg],
        input=script,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=600,
        env={**os.environ, "MSYS_NO_PATHCONV": "1"},
    )
    assert answer.returncode == 0, answer.stderr + answer.stdout
    return json.loads(answer.stdout)


# token_get_all of one source text; every token as [name, text, line].
TOKENS_PHP = r"""<?php
$in = json_decode(base64_decode($argv[1]), true);
$src = array_key_exists('source', $in) ? $in['source'] : file_get_contents($in['file']);
$out = [];
foreach (token_get_all($src) as $t) {
    if (is_array($t)) {
        $out[] = [token_name($t[0]), $t[1], $t[2]];
    } else {
        $out[] = ['CHAR', $t, 0];
    }
}
echo json_encode($out);
"""

Token = tuple[str, str, int]


def tokens_of(*, file: str | None = None, source: str | None = None) -> list[Token]:
    payload: dict[str, str] = {"file": file} if file is not None else {"source": source or ""}
    raw = run_php(TOKENS_PHP, payload)
    return [(str(name), str(text), int(line)) for name, text, line in raw]


_PRINTING = frozenset({"T_ECHO", "T_PRINT", "T_OPEN_TAG_WITH_ECHO", "T_EVAL", "T_INLINE_HTML"})
_RAW_CALLS = frozenset({"print_unescaped", "printf", "vprintf", "print_r", "var_dump", "var_export", "readfile"})


@dataclass(slots=True)
class OutputReport:
    """What the token probe sees in a template."""

    printing_tokens: list[str] = field(default_factory=list)
    raw_calls: list[str] = field(default_factory=list)
    banner_blocks: list[list[str]] = field(default_factory=list)
    url_assignments: list[list[str]] = field(default_factory=list)
    map_assignments: list[list[str]] = field(default_factory=list)
    map_writes: int = 0


def _significant(tokens: list[Token]) -> list[Token]:
    return [t for t in tokens if t[0] not in {"T_WHITESPACE", "T_COMMENT", "T_DOC_COMMENT"}]


def _statement_from(tokens: list[Token], start: int) -> list[str]:
    """Texts of the significant tokens from ``start`` up to the next ``;``."""
    texts: list[str] = []
    depth = 0
    for name, text, _ in tokens[start:]:
        if name in {"T_WHITESPACE", "T_COMMENT", "T_DOC_COMMENT"}:
            continue
        if text in {"[", "("}:
            depth += 1
        elif text in {"]", ")"}:
            depth -= 1
        texts.append(f"{name}:{text}")
        if text == ";" and depth == 0:
            break
    return texts


def output_report(tokens: list[Token]) -> OutputReport:
    report = OutputReport()
    # Printing tokens other than the HTML between PHP blocks, and raw calls.
    for i, (name, text, line) in enumerate(tokens):
        if name in _PRINTING - {"T_INLINE_HTML"}:
            report.printing_tokens.append(f"{line}:{name}")
        if name == "T_STRING" and text in _RAW_CALLS:
            nxt = _significant(tokens[i + 1 : i + 4])
            if nxt and nxt[0][1] == "(":
                report.raw_calls.append(f"{line}:{text}")
    # The PHP blocks inside the banner: from the inline HTML that opens the
    # element with the id up to the inline HTML that closes the paragraph.
    inside = False
    block: list[str] | None = None
    for name, text, _ in tokens:
        if name == "T_INLINE_HTML":
            if 'id="findling-banner-parallel"' in text:
                inside = True
            elif inside and "</p>" in text:
                inside = False
            continue
        if not inside:
            continue
        if name == "T_OPEN_TAG":
            block = []
        elif name == "T_CLOSE_TAG":
            if block is not None:
                report.banner_blocks.append(block)
            block = None
        elif block is not None and name not in {"T_WHITESPACE", "T_COMMENT"}:
            block.append(f"{name}:{text}")
    # Assignments of the URL and of the map, and any write into the map.
    for i, (name, text, _) in enumerate(tokens):
        if name != "T_VARIABLE" or text not in {"$migrationDocsUrl", "$migrationDocsUrls"}:
            continue
        nxt = _significant(tokens[i + 1 : i + 3])
        if nxt and nxt[0][1] == "=":
            target = report.url_assignments if text == "$migrationDocsUrl" else report.map_assignments
            target.append(_statement_from(tokens, i))
        elif text == "$migrationDocsUrls" and nxt and nxt[0][1] == "[":
            # an index access; a write if an "=" follows the closing bracket
            depth = 0
            for later in _significant(tokens[i + 1 :]):
                if later[1] == "[":
                    depth += 1
                elif later[1] == "]":
                    depth -= 1
                    if depth == 0:
                        continue
                if depth == 0:
                    if later[1] in {"=", ".=", "??="}:
                        report.map_writes += 1
                    break
    return report


def _judge_banner_block(block: list[str]) -> str | None:
    """None for a block that is control flow or exactly ``p(<one expression>);``."""
    if not block:
        return "empty block"
    first = block[0]
    if first in {"T_IF:if", "CHAR:}", "T_ELSE:else", "T_ENDIF:endif"}:
        if any(part.startswith(("T_ECHO", "T_PRINT")) for part in block):
            return f"control block prints: {block}"
        return None
    if first != "T_STRING:p" or block[1] != "CHAR:(" or block[-1] != "CHAR:;":
        return f"output not through p(): {block}"
    return None


def _judge_report(report: OutputReport) -> list[str]:
    problems: list[str] = []
    problems += [f"printing token {t}" for t in report.printing_tokens]
    problems += [f"raw output call {c}" for c in report.raw_calls]
    if len(report.banner_blocks) < 4:
        problems.append(f"only {len(report.banner_blocks)} PHP blocks inside the banner")
    for block in report.banner_blocks:
        verdict = _judge_banner_block(block)
        if verdict is not None:
            problems.append(verdict)
    href_blocks = [b for b in report.banner_blocks if "T_VARIABLE:$migrationDocsUrl" in b]
    if len(href_blocks) != 1 or href_blocks[0] != [
        "T_STRING:p",
        "CHAR:(",
        "T_VARIABLE:$migrationDocsUrl",
        "CHAR:)",
        "CHAR:;",
    ]:
        problems.append(f"the href is not exactly p($migrationDocsUrl): {href_blocks}")
    text_blocks = [b for b in report.banner_blocks if "T_STRING:t" in b]
    for block in text_blocks:
        # p($l->t('<literal>')); the argument of t is one constant string
        after_t = block[block.index("T_STRING:t") + 1 :]
        if after_t[:3] != ["CHAR:(", after_t[1], "CHAR:)"] or not after_t[1].startswith("T_CONSTANT_ENCAPSED_STRING:"):
            problems.append(f"a text of the banner is not one literal through t(): {block}")
    if len(text_blocks) != 2:
        problems.append(f"expected two translated texts in the banner, found {len(text_blocks)}")
    if len(report.url_assignments) != 1:
        problems.append(f"$migrationDocsUrl is assigned {len(report.url_assignments)} times")
    else:
        rhs = report.url_assignments[0][2:]
        if rhs[:2] != ["T_VARIABLE:$migrationDocsUrls", "CHAR:["]:
            problems.append(f"$migrationDocsUrl does not come from the map: {rhs}")
    if len(report.map_assignments) != 1:
        problems.append(f"the map is assigned {len(report.map_assignments)} times")
    else:
        parts = report.map_assignments[0][2:]
        allowed = {"CHAR:[", "CHAR:]", "CHAR:,", "CHAR:;", "T_DOUBLE_ARROW:=>"}
        strange = [p for p in parts if p not in allowed and not p.startswith("T_CONSTANT_ENCAPSED_STRING:")]
        if strange:
            problems.append(f"the map holds more than literals: {strange}")
        values = [
            parts[i + 1].split(":", 1)[1].strip("'\"")
            for i, p in enumerate(parts)
            if p == "T_DOUBLE_ARROW:=>" and i + 1 < len(parts)
        ]
        expected = {
            TAG_BASE + "migrate-from-fulltextsearch.md",
            TAG_BASE + "migrate-from-fulltextsearch.fr.md",
            TAG_BASE + "migrate-from-fulltextsearch.en.md",
        }
        if set(values) != expected or len(values) != 3:
            problems.append(f"the map values are {values}")
    if report.map_writes:
        problems.append(f"the map is written {report.map_writes} times after its literal")
    return problems


# A template with every mistake the probe must see, and one clean banner.
_BAD_TEMPLATE = """<?php
$migrationDocsUrls = ['de' => 'https://example.org/a', 'en' => $_['url']];
$migrationDocsUrls['fr'] = $_['other'];
$migrationDocsUrl = $_['link'];
?>
<p id="findling-banner-parallel"<?php if (!$x) { ?> hidden<?php } ?>>
<span><?php echo $l->t($_['text']); ?></span>
<span><?php print_unescaped($l->t('Hello')); ?></span>
<a href="<?= $migrationDocsUrl ?>"><?php p($l->t($key)); ?></a>
</p>
<?php print('x'); ?>
"""


def test_the_token_probe_sees_every_unescaped_output_and_a_foreign_url() -> None:
    """Positive control: the probe is not blind to what it is meant to find."""
    problems = _judge_report(output_report(tokens_of(source=_BAD_TEMPLATE)))
    text = "\n".join(problems)
    assert "printing token" in text  # echo, <?=, print
    assert "raw output call" in text  # print_unescaped
    assert "output not through p()" in text
    assert "the href is not exactly p($migrationDocsUrl)" in text
    assert "is not one literal through t()" in text
    assert "does not come from the map" in text
    assert "the map holds more than literals" in text
    assert "the map is written 1 times" in text


def test_every_output_of_the_banner_goes_through_p_and_the_href_comes_from_three_literals() -> None:
    report = output_report(tokens_of(file="php/templates/admin.php"))
    assert _judge_report(report) == []


# ---------------------------------------------------------------------------
# The rendered banner
# ---------------------------------------------------------------------------

# Cuts the PHP part (map and language choice) and the HTML of the banner out
# of the real template by position, and runs them with stubs. p() escapes as
# the core does (OCP\Util::sanitizeHTML: htmlspecialchars, ENT_QUOTES, UTF-8).
RENDER_PHP = r"""<?php
$in = json_decode(base64_decode($argv[1]), true);
$src = file_get_contents('php/templates/admin.php');
$a = strpos($src, '$parallelSearch = ');
$b = strpos($src, '?>', $a);
$c = strpos($src, '<p class="findling-banner findling-banner--warning" id="findling-banner-parallel"');
$d = strpos($src, '</p>', $c) + 4;
if ($a === false || $b === false || $c === false) { fwrite(STDERR, "fragment not found"); exit(3); }
$code = substr($src, $a, $b - $a) . ' ?>' . substr($src, $c, $d - $c);
final class StubL10N {
    public function __construct(private string $code, private array $map) {}
    public function t(string $text, $parameters = []): string { return $this->map[$text] ?? $text; }
    public function getLanguageCode(): string { return $this->code; }
}
if ($in['raw'] ?? false) {
    function p($s) { print((string)$s); }
} else {
    function p($s) { print(htmlspecialchars((string)$s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')); }
}
$out = [];
foreach ($in['cases'] as $case) {
    $l = new StubL10N($case['lang'], $case['map'] ?? []);
    $_ = ['parallelSearch' => $case['parallel']];
    $alertIcon = 'M0,0';
    ob_start();
    eval($code);
    $out[] = ob_get_clean();
}
echo json_encode($out);
"""


@dataclass(slots=True)
class Element:
    tag: str
    attrs: dict[str, str | None]
    text: str = ""


class _Banner(HTMLParser):
    """Every element of the fragment with its attributes and its own text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[Element] = []
        self._stack: list[Element] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        element = Element(tag, dict(attrs))
        self.elements.append(element)
        if tag not in {"path"}:
            self._stack.append(element)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.elements.append(Element(tag, dict(attrs)))

    def handle_endtag(self, tag: str) -> None:
        while self._stack:
            if self._stack.pop().tag == tag:
                break

    def handle_data(self, data: str) -> None:
        if self._stack:
            self._stack[-1].text += data


def parse_banner(html: str) -> list[Element]:
    parser = _Banner()
    parser.feed(html)
    parser.close()
    return parser.elements


def render(cases: list[dict[str, Any]], *, raw: bool = False) -> list[str]:
    out = run_php(RENDER_PHP, {"cases": cases, "raw": raw})
    assert isinstance(out, list)
    return [str(x) for x in out]


INJECTED = '<b id="inj">x</b><script>alert(1)</script>" onmouseover="alert(2)'


def _injection_cases() -> list[dict[str, Any]]:
    return [
        {"lang": "de", "parallel": True, "map": {NEW_KEY: INJECTED, LINK_KEY: INJECTED}},
        {"lang": "fr", "parallel": True, "map": {NEW_KEY: "ok", LINK_KEY: INJECTED}},
    ]


def test_the_render_probe_sees_markup_when_p_does_not_escape() -> None:
    """Positive control: with a p() that prints raw, the injected elements appear."""
    for html in render(_injection_cases(), raw=True):
        tags = [e.tag for e in parse_banner(html)]
        assert "b" in tags or "script" in tags, html


def test_markup_in_a_catalogue_value_renders_as_text() -> None:
    for html in render(_injection_cases()):
        elements = parse_banner(html)
        tags = [e.tag for e in elements]
        assert tags == ["p", "svg", "path", "span", "a"], (tags, html)
        anchor = elements[-1]
        assert (anchor.attrs.get("href") or "").startswith(TAG_BASE)
        assert anchor.attrs.get("target") == "_blank"
        assert anchor.attrs.get("rel") == "noreferrer noopener"
        assert set(anchor.attrs) == {"class", "href", "target", "rel"}
        assert INJECTED in anchor.text
        assert all("onmouseover" not in (k or "") for e in elements for k in e.attrs)


def test_the_banner_is_hidden_unless_the_flag_is_exactly_true() -> None:
    cases = [{"lang": "de", "parallel": value} for value in (True, False, None, 1, "1", "true", [], [True])]
    htmls = render(cases)
    hidden = ["hidden" in parse_banner(html)[0].attrs for html in htmls]
    assert hidden == [False, True, True, True, True, True, True, True]


# ---------------------------------------------------------------------------
# The catalogues
# ---------------------------------------------------------------------------


def _catalogue(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        data = json.loads(text)
        translations = data["translations"]
    else:
        start = text.index("{")
        translations, _ = json.JSONDecoder().raw_decode(text, start)
    assert isinstance(translations, dict)
    return {str(k): str(v) for k, v in translations.items()}


def _catalogues() -> list[Path]:
    return sorted([*L10N_DIR.glob("*.json"), *L10N_DIR.glob("*.js")])


_MARKUP_OR_URL = ("<", ">", '"', "http", "://", "www.", "street1983nk", ".md")


def test_the_markup_scan_of_the_catalogues_sees_a_planted_value() -> None:
    """Positive control for the scan below."""
    planted = {NEW_KEY: 'Siehe <a href="https://x">hier</a>', LINK_KEY: "ok"}
    hits = [m for value in planted.values() for m in _MARKUP_OR_URL if m in value]
    assert set(hits) >= {"<", ">", '"', "http", "://"}


def test_no_catalogue_value_of_the_two_banner_keys_carries_markup_or_a_url() -> None:
    catalogues = _catalogues()
    assert len(catalogues) == 16
    findings: list[str] = []
    for path in catalogues:
        translations = _catalogue(path)
        if NEW_KEY not in translations:
            findings.append(f"{path.name}: the banner sentence is missing")
        if LINK_KEY not in translations:
            findings.append(f"{path.name}: the link text is missing")
        for key in (NEW_KEY, LINK_KEY):
            value = translations.get(key, "")
            findings += [f"{path.name}: {key[:20]}... carries {m!r}" for m in _MARKUP_OR_URL if m in value]
    assert findings == []


# ---------------------------------------------------------------------------
# Text probes without git history
# ---------------------------------------------------------------------------

_DASHES = (chr(0x2013), chr(0x2014))


def test_no_file_of_the_phase_carries_an_en_or_em_dash() -> None:
    hits = []
    for name in PHASE_FILES:
        for number, line in enumerate((REPO / name).read_text(encoding="utf-8").splitlines(), 1):
            if any(d in line for d in _DASHES):
                hits.append(f"{name}:{number}")
    assert hits == []


def test_the_dash_probe_sees_a_dash() -> None:
    assert any(d in "a" + chr(0x2013) + "b" for d in _DASHES)


# ---------------------------------------------------------------------------
# Instance probes
# ---------------------------------------------------------------------------

URL = os.environ.get("FINDLING_AUDIT34_URL", "")
ADMIN_PASS = os.environ.get("FINDLING_AUDIT34_ADMIN_PASS", "")
USER = os.environ.get("FINDLING_AUDIT34_USER", "")
USER_PASS = os.environ.get("FINDLING_AUDIT34_USER_PASS", "")
CONTAINER = os.environ.get("FINDLING_AUDIT34_CONTAINER", "")

instance = pytest.mark.skipif(
    not (URL and ADMIN_PASS and USER and USER_PASS and CONTAINER),
    reason="no audit instance (FINDLING_AUDIT34_URL and friends)",
)

OVERVIEW = "/index.php/apps/findling/admin/overview"
PAGE = "/index.php/settings/admin/findling"


def occ(*args: str) -> subprocess.CompletedProcess[str]:
    docker = _docker()
    return subprocess.run(  # noqa: S603 - an argument list, never a shell
        [docker, "exec", "-u", "www-data", CONTAINER, "php", "occ", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=600,
        env={**os.environ, "MSYS_NO_PATHCONV": "1"},
    )


def container_php(code: str) -> str:
    docker = _docker()
    out = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [docker, "exec", "-u", "www-data", CONTAINER, "php", "-r", code],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        timeout=600,
        env={**os.environ, "MSYS_NO_PATHCONV": "1"},
    )
    return out.stdout


def sql(query: str) -> list[list[Any]]:
    code = (
        '$db = new PDO("sqlite:/var/www/html/data/nextcloud.db");'
        "echo json_encode($db->query(base64_decode('"
        + base64.b64encode(query.encode()).decode()
        + "'))->fetchAll(PDO::FETCH_NUM));"
    )
    rows = json.loads(container_php(code))
    assert isinstance(rows, list)
    return rows


def enabled_rows() -> dict[str, str]:
    """The independent truth: rows ``enabled`` of the two app ids, read by SQL."""
    rows = sql(
        "SELECT appid, configvalue FROM oc_appconfig WHERE configkey = 'enabled' "
        "AND appid IN ('fulltextsearch', 'files_fulltextsearch')"
    )
    return {str(r[0]): str(r[1]) for r in rows}


def nextcloud_log() -> list[str]:
    return container_php('readfile("/var/www/html/data/nextcloud.log");').splitlines()


def access_log_since(since: str) -> list[str]:
    docker = _docker()
    out = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [docker, "logs", "--since", since, CONTAINER],
        capture_output=True,
        check=False,
        timeout=120,
    )
    return (out.stdout + out.stderr).decode("utf-8", "replace").splitlines()


def client(user: str, password: str) -> tuple[httpx.Client, str]:
    session = httpx.Client(base_url=URL, auth=(user, password), timeout=300)
    token = session.get("/index.php/csrftoken").json()["token"]
    return session, token


def clear_flags() -> None:
    for app_id in APP_IDS:
        occ("config:app:delete", app_id, "enabled")


def wait_for_overview(session: httpx.Client, token: str, expected: bool) -> bool:
    """The web process reads appconfig through a local cache; wait for it."""
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        answer = session.get(OVERVIEW, headers={"requesttoken": token})
        if answer.status_code == 200 and answer.json().get("parallelSearch") is expected:
            return True
        time.sleep(1)
    return False


def banner_state(session: httpx.Client) -> tuple[int, bool | None]:
    """Status of the page and whether the banner is visible (None: not in the DOM)."""
    page = session.get(PAGE)
    if page.status_code != 200:
        return page.status_code, None
    for element in parse_banner(page.text):
        if element.attrs.get("id") == "findling-banner-parallel":
            return 200, "hidden" not in element.attrs
    return 200, None


@pytest.fixture
def clean_flags() -> Any:
    before = enabled_rows()
    assert before == {}, f"the instance carries flags before the probe: {before}"
    try:
        yield
    finally:
        clear_flags()
        assert enabled_rows() == {}


@instance
def test_a_non_admin_never_sees_the_overview_or_the_page(clean_flags: None) -> None:
    _ = clean_flags
    occ("config:app:set", "fulltextsearch", "enabled", "--value=yes")
    admin, admin_token = client("admin", ADMIN_PASS)
    assert wait_for_overview(admin, admin_token, expected=True)
    # positive control: the admin sees key and banner
    assert "parallelSearch" in admin.get(OVERVIEW, headers={"requesttoken": admin_token}).json()
    assert banner_state(admin) == (200, True)
    user, user_token = client(USER, USER_PASS)
    overview = user.get(OVERVIEW, headers={"requesttoken": user_token})
    assert overview.status_code == 403
    assert "parallelSearch" not in overview.text
    page = user.get(PAGE)
    assert page.status_code in {403, 404} or "findling-banner-parallel" not in page.text
    assert "findling-banner-parallel" not in page.text
    assert "migrate-from-fulltextsearch" not in page.text
    anonymous = httpx.get(URL + OVERVIEW, timeout=60, follow_redirects=False)
    assert anonymous.status_code in {401, 303, 302}
    assert "parallelSearch" not in anonymous.text


@instance
def test_toggling_the_flag_writes_no_log_line_with_an_app_id(clean_flags: None) -> None:
    _ = clean_flags
    marker = f"zz34ctl{int(time.time())}"
    since = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 2))
    log_before = len(nextcloud_log())
    admin, token = client("admin", ADMIN_PASS)
    for _round in range(3):
        occ("config:app:set", "fulltextsearch", "enabled", "--value=yes")
        assert wait_for_overview(admin, token, expected=True)
        assert banner_state(admin) == (200, True)
        occ("config:app:delete", "fulltextsearch", "enabled")
        assert wait_for_overview(admin, token, expected=False)
        assert banner_state(admin) == (200, False)
    # positive control: a failed login names the marker in nextcloud.log, the
    # request path names it in the access log of the container
    httpx.request("PROPFIND", URL + "/remote.php/dav/files/" + marker, auth=(marker, "x"), timeout=60)
    httpx.get(URL + "/index.php/" + marker, timeout=60)
    new_lines = nextcloud_log()[log_before:]
    access = access_log_since(since)
    assert any(marker in line for line in new_lines), "control line missing in nextcloud.log"
    assert any(marker in line for line in access), "control line missing in the access log"
    named = [line for line in [*new_lines, *access] if any(a in line for a in APP_IDS)]
    assert named == []


# ---------------------------------------------------------------------------
# Bugs: the language map against an oracle
# ---------------------------------------------------------------------------

PAGE_BY_SUFFIX = {
    ".md": TAG_BASE + "migrate-from-fulltextsearch.md",
    ".fr.md": TAG_BASE + "migrate-from-fulltextsearch.fr.md",
    ".en.md": TAG_BASE + "migrate-from-fulltextsearch.en.md",
}


def oracle_suffix(code: str) -> str:
    """The rule of PE-34-3 in its own words: the German page for a code that
    begins with de, the French page for one that begins with fr, else English."""
    if code[:2] == "de":
        return ".md"
    if code[:2] == "fr":
        return ".fr.md"
    return ".en.md"


ORACLE_TABLE = {
    "de": ".md",
    "de_DE": ".md",
    "de_CH": ".md",
    "fr": ".fr.md",
    "fr_CA": ".fr.md",
    "en": ".en.md",
    "en_GB": ".en.md",
    "es": ".en.md",
    "pt_BR": ".en.md",
    "nl": ".en.md",
    "cs": ".en.md",
    "": ".en.md",
    "dsb": ".en.md",
    "fur": ".en.md",
}


def test_the_oracle_table_follows_its_rule() -> None:
    assert {code: oracle_suffix(code) for code in ORACLE_TABLE} == ORACLE_TABLE


def test_the_link_of_the_template_follows_the_oracle_for_every_language() -> None:
    codes = list(ORACLE_TABLE)
    htmls = render([{"lang": code, "parallel": True} for code in codes])
    chosen: dict[str, str | None] = {}
    for code, html in zip(codes, htmls, strict=True):
        anchors = [e for e in parse_banner(html) if e.tag == "a"]
        assert len(anchors) == 1
        chosen[code] = anchors[0].attrs.get("href")
    assert chosen == {code: PAGE_BY_SUFFIX[suffix] for code, suffix in ORACLE_TABLE.items()}


# ---------------------------------------------------------------------------
# Bugs: the banner decision against appconfig rows read by SQL
# ---------------------------------------------------------------------------


def truth_from_rows(rows: dict[str, str]) -> bool:
    """Enabled for anyone, as the core defines it: a row ``enabled`` whose value
    is not ``no`` (``yes`` or a JSON list of groups)."""
    return any(value != "no" for value in rows.values())


BANNER_CASES: list[tuple[str, list[tuple[str, str]]]] = [
    ("no row", []),
    ("fulltextsearch yes", [("fulltextsearch", "yes")]),
    ("files_fulltextsearch yes", [("files_fulltextsearch", "yes")]),
    ("group only", [("fulltextsearch", '["findling-probe34"]')]),
    ("value no", [("fulltextsearch", "no")]),
    ("both no", [("fulltextsearch", "no"), ("files_fulltextsearch", "no")]),
]


@instance
def test_the_banner_agrees_with_the_appconfig_rows_in_every_case(clean_flags: None) -> None:
    _ = clean_flags
    admin, token = client("admin", ADMIN_PASS)
    seen: list[tuple[str, bool, int, bool | None]] = []
    for label, flags in BANNER_CASES:
        clear_flags()
        for app_id, value in flags:
            occ("config:app:set", app_id, "enabled", f"--value={value}")
        rows = enabled_rows()
        assert rows == dict(flags), label
        truth = truth_from_rows(rows)
        assert wait_for_overview(admin, token, expected=truth), label
        status, visible = banner_state(admin)
        seen.append((label, truth, status, visible))
    assert seen == [(label, truth, 200, truth) for label, truth, _, _ in seen]
    assert [truth for _, truth, _, _ in seen] == [False, True, True, True, False, False]


@instance
def test_the_disable_command_of_the_page_takes_three_ids_in_one_call(clean_flags: None) -> None:
    """Step 4 names three ids in one call, none of them installed here."""
    _ = clean_flags
    answer = occ("app:disable", "files_fulltextsearch", "fulltextsearch_elasticsearch", "fulltextsearch")
    assert answer.returncode == 0
    assert answer.stdout.count("No such app enabled") == 3
    assert enabled_rows() == {}


# ---------------------------------------------------------------------------
# Bugs: the facts of the pages
# ---------------------------------------------------------------------------

MIGRATION_PAGES = {
    "de": REPO / "docs" / "migrate-from-fulltextsearch.md",
    "en": REPO / "docs" / "migrate-from-fulltextsearch.en.md",
    "fr": REPO / "docs" / "migrate-from-fulltextsearch.fr.md",
}


@dataclass(frozen=True, slots=True)
class Claim:
    app: str
    source: str  # "store" (field created of the release) or "github" (published_at)
    version: str
    date: str  # ISO
    spec: str = ""  # platformVersionSpec of the store release, where the page names the range


# What the pages claim, one row per statement (Stand 19.10.2026).
CLAIMS: tuple[Claim, ...] = (
    Claim("fulltextsearch", "github", "v35.0.0", "2026-09-20"),
    Claim("fulltextsearch", "store", "33.0.3", "2026-09-20", ">=33.0.0 <36.0.0"),
    Claim("fulltextsearch", "store", "34.0.2", "2026-09-18"),
    Claim("fulltextsearch", "store", "35.0.0", "2026-09-18"),
    Claim("files_fulltextsearch", "store", "34.0.1", "2026-08-06", ">=34.0.0 <35.0.0"),
    Claim("files_fulltextsearch", "store", "35.0.0", "2026-09-18", ">=35.0.0 <36.0.0"),
    Claim("fulltextsearch_elasticsearch", "github", "v35.0.1", "2026-10-07"),
    Claim("fulltextsearch_elasticsearch", "github", "v34.0.3", "2026-10-07"),
    Claim("files_fulltextsearch_tesseract", "store", "32.0.0", "2026-01-19", ">=32.0.0 <33.0.0"),
    Claim("fulltextsearch_sql", "store", "1.5.1", "2026-10-14"),
    Claim("fulltextsearch_postgresql", "store", "0.1.4", "2026-10-10"),
)

# The answer of the App Store API (platform/{32.0.0,33.0.0,34.0.3,35.0.0}/apps.json,
# field created) and of the GitHub releases API (published_at), queried with
# curl and jq on 19.10.2026 at 13:21 UTC, independent of the gh query of 34-01:
# per app and source the newest stable release.
SNAPSHOT_NEWEST: dict[tuple[str, str], tuple[str, str]] = {
    ("fulltextsearch", "github"): ("v35.0.0", "2026-09-20"),
    ("fulltextsearch", "store"): ("35.0.0", "2026-09-18"),
    ("files_fulltextsearch", "store"): ("35.0.0", "2026-09-18"),
    ("fulltextsearch_elasticsearch", "github"): ("v35.0.1", "2026-10-07"),
    ("files_fulltextsearch_tesseract", "store"): ("32.0.0", "2026-01-19"),
    ("fulltextsearch_sql", "store"): ("1.5.1", "2026-10-14"),
    ("fulltextsearch_postgresql", "store"): ("0.1.4", "2026-10-10"),
}

_SEMVER = re.compile(r"\bv?\d+\.\d+\.\d+\b")
_DATE = re.compile(r"\b(\d\d)\.(\d\d)\.(\d{4})\b")


def sections(text: str) -> list[str]:
    """The text under each level two heading, in order."""
    return text.split("\n## ")[1:]


def _versions_and_dates(text: str) -> tuple[set[str], set[str]]:
    versions = {v for v in _SEMVER.findall(text) if not _DATE.fullmatch(v)}
    return versions, {f"{y}-{m}-{d}" for d, m, y in _DATE.findall(text)}


def page_facts(text: str) -> dict[str, tuple[set[str], set[str]]]:
    """Per bullet of the maintenance section: app id, versions, ISO dates."""
    maintenance = sections(text)[2]
    facts: dict[str, tuple[set[str], set[str]]] = {}
    for bullet in maintenance.split("\n- ")[1:]:
        first = bullet.split()[0].rstrip(",:")
        if first.startswith(("fulltextsearch", "files_fulltextsearch")):
            facts[first] = _versions_and_dates(bullet)
            continue
        # the bullet of the third party platform apps names two apps, each
        # with its figures between the end of its link and the next link
        for app in ("fulltextsearch_sql", "fulltextsearch_postgresql"):
            own = bullet.split(f"/{app})", 1)[1].split("[", 1)[0] if f"/{app})" in bullet else ""
            facts[app] = _versions_and_dates(own)
    return facts


def claimed_facts() -> dict[str, tuple[set[str], set[str]]]:
    out: dict[str, tuple[set[str], set[str]]] = {}
    for claim in CLAIMS:
        versions, dates = out.setdefault(claim.app, (set(), set()))
        versions.add(claim.version)
        dates.add(claim.date)
    return out


@pytest.mark.parametrize("language", sorted(MIGRATION_PAGES))
def test_every_fact_of_the_page_is_a_claim_of_the_audit(language: str) -> None:
    text = MIGRATION_PAGES[language].read_text(encoding="utf-8")
    assert page_facts(text) == claimed_facts()
    assert any(day in text for day in ("19.10.2026", "19 October 2026", "19 octobre 2026"))


def test_the_claims_agree_with_the_snapshot_of_the_audit_day() -> None:
    for (app, source), (version, date) in SNAPSHOT_NEWEST.items():
        mine = [c for c in CLAIMS if c.app == app and c.source == source]
        # the page names the newest release of each source, older ones beside
        # it are allowed (fulltextsearch 33.0.3 and 34.0.2 next to 35.0.0)
        assert any(c.version == version and c.date == date for c in mine), (app, source)


def test_the_fact_check_sees_a_wrong_date() -> None:
    """Positive control: one changed date on a page is a difference."""
    text = MIGRATION_PAGES["de"].read_text(encoding="utf-8").replace("14.10.2026", "15.10.2026")
    assert page_facts(text) != claimed_facts()


NETWORK = os.environ.get("FINDLING_AUDIT34_NETWORK", "") == "1"


def _store_releases() -> dict[str, list[dict[str, Any]]]:
    releases: dict[str, list[dict[str, Any]]] = {}
    apps = {c.app for c in CLAIMS}
    for platform in ("32.0.0", "33.0.0", "34.0.3", "35.0.0"):
        answer = httpx.get(f"https://apps.nextcloud.com/api/v1/platform/{platform}/apps.json", timeout=300)
        answer.raise_for_status()
        for app in answer.json():
            if app["id"] in apps:
                known = releases.setdefault(app["id"], [])
                known += [rel for rel in app["releases"] if rel not in known]
    return releases


def _github_releases(app: str) -> list[dict[str, Any]]:
    answer = httpx.get(
        f"https://api.github.com/repos/nextcloud/{app}/releases?per_page=10",
        headers={"User-Agent": "findling-audit-34"},
        timeout=60,
    )
    answer.raise_for_status()
    data = answer.json()
    assert isinstance(data, list)
    return data


def _numeric(version: str) -> tuple[int, ...]:
    return tuple(int(x) for x in version.split("."))


@pytest.mark.skipif(not NETWORK, reason="network probe, set FINDLING_AUDIT34_NETWORK=1")
def test_every_claim_holds_in_the_app_store_and_on_github_today() -> None:
    store = _store_releases()
    wrong: list[str] = []
    for claim in CLAIMS:
        if claim.source == "store":
            match = [r for r in store.get(claim.app, []) if r["version"] == claim.version]
            if not match or match[0]["created"][:10] != claim.date:
                wrong.append(f"{claim}: the store answers {match[:1]}")
            elif claim.spec and match[0]["platformVersionSpec"] != claim.spec:
                wrong.append(f"{claim}: the store says {match[0]['platformVersionSpec']}")
        else:
            rels = _github_releases(claim.app)
            match = [r for r in rels if r["tag_name"] == claim.version]
            if not match or match[0]["published_at"][:10] != claim.date:
                wrong.append(f"{claim}: GitHub answers {[r['tag_name'] for r in rels[:3]]}")
    tesseract = [r["version"] for r in store.get("files_fulltextsearch_tesseract", [])]
    if tesseract != ["32.0.0"]:
        wrong.append(f"files_fulltextsearch_tesseract has {tesseract}")
    stale: list[str] = []
    for (app, source), (version, _) in SNAPSHOT_NEWEST.items():
        if source == "store":
            stable = [r["version"] for r in store.get(app, []) if "-" not in r["version"] and not r["isNightly"]]
            newest = max(stable, key=_numeric)
        else:
            newest = next(r["tag_name"] for r in _github_releases(app) if not r["prerelease"])
        if newest != version:
            stale.append(f"{app} ({source}): {newest} is newer than {version}")
    assert wrong == []  # a wrong statement: MEDIUM
    assert stale == []  # a newer release than the page names: LOW, the page says "Stand"


# ---------------------------------------------------------------------------
# Bugs: formula, switch line and links, checked without the gate
# ---------------------------------------------------------------------------

_C_CEDILLA = chr(0xE7)
FORMULA_LINES = {
    "de": "OCR ohne Datei" + chr(0xE4) + "nderung und ohne Elasticsearch",
    "en": "OCR without changing files and without Elasticsearch",
    "fr": "OCR sans modifier les fichiers et sans Elasticsearch",
}
_DE_LINK = "[Deutsch](migrate-from-fulltextsearch.md)"
_EN_LINK = "[English](migrate-from-fulltextsearch.en.md)"
_FR_NAME = f"Fran{_C_CEDILLA}ais"
_FR_LINK = f"[{_FR_NAME}](migrate-from-fulltextsearch.fr.md)"
FIRST_LINES = {
    "de": f"Deutsch | {_EN_LINK} | {_FR_LINK}",
    "en": f"{_DE_LINK} | English | {_FR_LINK}",
    "fr": f"{_DE_LINK} | {_EN_LINK} | {_FR_NAME}",
}


@pytest.mark.parametrize("language", sorted(MIGRATION_PAGES))
def test_the_switch_line_is_line_one_of_the_page(language: str) -> None:
    lines = MIGRATION_PAGES[language].read_text(encoding="utf-8").splitlines()
    assert lines[0] == FIRST_LINES[language]


@pytest.mark.parametrize(
    "language",
    ["de", "en", pytest.param("fr", marks=pytest.mark.xfail(strict=True, reason="L-34-02"))],
)
def test_the_formula_stands_on_one_line_of_the_page(language: str) -> None:
    """A line based search (grep -F, a scraper of the store text) finds it."""
    lines = MIGRATION_PAGES[language].read_text(encoding="utf-8").splitlines()
    assert any(FORMULA_LINES[language] in line for line in lines)


LINKED_FILES = (
    *MIGRATION_PAGES.values(),
    REPO / "README.md",
    REPO / "README.en.md",
    REPO / "README.fr.md",
)


def relative_targets(path: Path) -> list[str]:
    """Every Markdown link target that is neither absolute nor an anchor."""
    rest = path.read_text(encoding="utf-8")
    targets: list[str] = []
    while "](" in rest:
        _, rest = rest.split("](", 1)
        target = rest.split(")", 1)[0].strip()
        if target and not target.startswith(("http://", "https://", "mailto:", "#")):
            targets.append(target.split("#", 1)[0])
    return targets


def test_every_relative_link_of_pages_and_readmes_resolves() -> None:
    missing: list[str] = []
    counted = 0
    for path in LINKED_FILES:
        for target in relative_targets(path):
            counted += 1
            if not (path.parent / target).exists():
                missing.append(f"{path.name}: {target}")
    assert counted > 20
    assert missing == []


def test_the_link_check_sees_a_missing_target(tmp_path: Path) -> None:
    page = tmp_path / "p.md"
    page.write_text("[a](nowhere.md) [b](https://x) [c](#top)\n", encoding="utf-8")
    assert relative_targets(page) == ["nowhere.md"]
    assert not (tmp_path / "nowhere.md").exists()


# ---------------------------------------------------------------------------
# Bugs: the steps of the page against the protocol of 34-02
# ---------------------------------------------------------------------------

NACHWEIS = REPO / ".planning" / "phases" / "34-umstiegsweg" / "34-02-NACHWEIS.md"

# Commands of the steps the protocol does not hold verbatim, with what covers them.
COVERED_ELSEWHERE = {
    "occ fulltextsearch:live": "source only: row 7a, systemd unit of the wiki, linked in step 2",
    "occ app:disable files_fulltextsearch fulltextsearch_elasticsearch fulltextsearch": (
        "rows 4 and 4b, and the three ids in one call on 8090 in this audit"
    ),
    "occ app:remove <app-id>": "row 5b, the placeholder for both ids",
}


def step_commands(text: str) -> list[str]:
    steps = sections(text)[3]
    commands: list[str] = []
    if "```sql" in steps:
        before, rest = steps.split("```sql", 1)
        block, after = rest.split("```", 1)
        commands += [line.strip() for line in block.splitlines() if line.strip()]
        steps = before + after
    spans = steps.split("`")[1::2]
    commands += [s for s in spans if s.startswith(("occ ", "--"))]
    return commands


@pytest.mark.parametrize("language", sorted(MIGRATION_PAGES))
def test_every_command_of_the_steps_is_in_the_protocol_or_marked(language: str) -> None:
    protocol = NACHWEIS.read_text(encoding="utf-8")
    commands = step_commands(MIGRATION_PAGES[language].read_text(encoding="utf-8"))
    assert len(commands) >= 8, commands
    loose = [c for c in commands if c not in protocol and c not in COVERED_ELSEWHERE]
    assert loose == []


# ---------------------------------------------------------------------------
# Bugs: quality of the gates, by mutation on a scratch copy
# ---------------------------------------------------------------------------

MUTATION = os.environ.get("FINDLING_AUDIT34_MUTATION", "") == "1"
GATE_MODULES = ("tests/test_migration_path.py", "tests/test_admin_ui_contract.py")
_FIFTH_LINK = (
    '\n<a href="https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/formats.md"'
    ' target="_blank" rel="noreferrer noopener">x</a>\n'
)


@dataclass(frozen=True, slots=True)
class Mutation:
    label: str
    path: str
    old: str  # "" appends
    new: str
    expected: frozenset[str]  # the gate tests that must go red, and no other


MUTATIONS: tuple[Mutation, ...] = (
    Mutation(
        "formula removed (de)",
        "docs/migrate-from-fulltextsearch.md",
        FORMULA_LINES["de"],
        "OCR ohne Elasticsearch",
        frozenset({"test_pages_exist_with_switch_line_and_formula"}),
    ),
    Mutation(
        "forbidden phrase (en)",
        "docs/migrate-from-fulltextsearch.en.md",
        "",
        "\nFindling is the " + "on" + "ly OCR you need.\n",
        frozenset({"test_forbidden_claim_occurs_in_no_shipped_file"}),
    ),
    Mutation(
        "forbidden phrase (fr)",
        "docs/migrate-from-fulltextsearch.fr.md",
        "",
        "\nFindling est la " + "seu" + "le OCR.\n",
        frozenset({"test_forbidden_claim_occurs_in_no_shipped_file"}),
    ),
    Mutation(
        "README.en.md on the German page",
        "README.en.md",
        "docs/migrate-from-fulltextsearch.en.md",
        "docs/migrate-from-fulltextsearch.md",
        frozenset({"test_readme_sections_link_the_page_of_their_language"}),
    ),
    Mutation(
        "store draft on blob/main",
        "docs/store-listing.md",
        "blob/v1.5.0/docs/migrate-from-fulltextsearch.en.md",
        "blob/main/docs/migrate-from-fulltextsearch.en.md",
        frozenset({"test_draft_section_of_phase_34_carries_a_tag_link_per_language"}),
    ),
    Mutation(
        "fifth link in the template",
        "php/templates/admin.php",
        "",
        _FIFTH_LINK,
        frozenset({"test_the_change_hint_links_the_anchor_of_the_documentation"}),
    ),
)


@pytest.fixture(scope="module")
def scratch_copy(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("gates")
    for top in REPO.iterdir():
        if top.is_file():
            shutil.copy2(top, root / top.name)
    shutil.copytree(REPO / "docs", root / "docs", ignore=shutil.ignore_patterns("measurements"))
    shutil.copytree(REPO / "php", root / "php", ignore=shutil.ignore_patterns("vendor", "node_modules"))
    shutil.copytree(REPO / "store", root / "store")
    (root / "backend" / "appinfo").mkdir(parents=True)
    shutil.copy2(REPO / "backend" / "appinfo" / "info.xml", root / "backend" / "appinfo" / "info.xml")
    shutil.copy2(REPO / "backend" / "pyproject.toml", root / "backend" / "pyproject.toml")
    shutil.copytree(
        REPO / "backend" / "tests", root / "backend" / "tests", ignore=shutil.ignore_patterns("__pycache__")
    )
    return root


def red_gate_tests(root: Path) -> set[str]:
    """Run the two gate modules in the copy; the names of the failed tests."""
    answer = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-rf",
            "-p",
            "no:cacheprovider",
            "-p",
            "no:randomly",
            *GATE_MODULES,
        ],
        cwd=root / "backend",
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=900,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    assert "passed" in answer.stdout or "failed" in answer.stdout, answer.stdout + answer.stderr
    red: set[str] = set()
    for line in answer.stdout.splitlines():
        if line.startswith("FAILED "):
            node = line.split()[1].split("::", 1)[1]
            red.add(node.split("[", 1)[0])
    return red


@pytest.mark.skipif(not MUTATION, reason="mutation run of the gates, set FINDLING_AUDIT34_MUTATION=1")
def test_the_unmutated_copy_is_green(scratch_copy: Path) -> None:
    assert red_gate_tests(scratch_copy) == set()


@pytest.mark.skipif(not MUTATION, reason="mutation run of the gates, set FINDLING_AUDIT34_MUTATION=1")
@pytest.mark.parametrize("mutation", MUTATIONS, ids=[m.label for m in MUTATIONS])
def test_each_mutation_turns_exactly_its_gate_red(scratch_copy: Path, mutation: Mutation) -> None:
    target = scratch_copy / mutation.path
    original = target.read_bytes()
    text = original.decode("utf-8")
    if mutation.old:
        assert mutation.old in text, mutation.label
        mutated = text.replace(mutation.old, mutation.new, 1)
    else:
        mutated = text + mutation.new
    target.write_bytes(mutated.encode("utf-8"))
    try:
        red = red_gate_tests(scratch_copy)
    finally:
        target.write_bytes(original)
    assert red == mutation.expected
