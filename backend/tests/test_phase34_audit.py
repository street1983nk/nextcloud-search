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
import shutil
import subprocess
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
