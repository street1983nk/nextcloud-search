"""The probes of the phase 32 audit (32-AUDIT.md): filters of the unified search.

Phase 32 opened a new input right in front of the permission boundary (the
folder of the unified search dialog), a hidden second search provider
(``findling-filter``) and a script on every page of a logged in user. This
module holds the audit probes as regression tests, in two groups.

**Source probes, always run.** They read the PHP tree and the script with
small hand written scanners, character by character, and never with a regular
expression over the source. ``test_php_acl_boundary.py`` strips comments and
strings with regular expressions and counts names; doing the same here would
repeat its blind spots, so this module walks a state machine instead (code,
line comment, block comment, both kinds of string, heredoc, and on the script
side template and regex literals) and works on the tokens it yields: a call
is ``->``, a name and ``(``, a member is ``.`` and a name. Each scanner has a
positive control that feeds it the shape it has to find.

**Instance probes, skipped without an instance.** They run the corpus of
manipulated filter values against a real Nextcloud over the OCS route, as the
users alice and bob, and read the log of the instance and of the backend
afterwards. They need the seed of 32-AUDIT.md (alice owns /Projekte with a
subfolder, /Projekte2, /Café32, /Alt32, /Leer32 and /Wurzel.txt; bob owns
/Geheim and /NurBob, shares /Geteilt with alice and has taken the share of
/Weg back) and these variables:

    FINDLING_AUDIT32_URL          http://localhost:8090
    FINDLING_AUDIT32_ALICE_PASS   password of alice
    FINDLING_AUDIT32_BOB_PASS     password of bob
    FINDLING_AUDIT32_CONTAINER    name of the Nextcloud container (log probe)
    FINDLING_AUDIT32_BACKEND_LOG  path of the backend log (log probe)
    FINDLING_AUDIT32_BACKEND_URL  http://127.0.0.1:10035 (log probe control)

The expectation of every corpus value is written down in the table before the
run: the narrowed set, or the hits of the search without a filter (USRCH-03),
and never a file alice cannot see without the filter.
"""

from __future__ import annotations

import os
import secrets
import shutil
import statistics
import subprocess
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import httpx
import pytest

REPO = Path(__file__).resolve().parents[2]
PHP_LIB = REPO / "php" / "lib"
SCRIPT = REPO / "php" / "js" / "unified-search.js"

# ---------------------------------------------------------------------------
# A PHP scanner, character by character
# ---------------------------------------------------------------------------

IDENT = "id"
VAR = "var"
STR = "str"
OP = "op"

_OPS = ("?->", "->", "::", "=>", "(", ")", "[", "]", "{", "}", ",", ";", "=")


@dataclass(frozen=True, slots=True)
class Token:
    kind: str
    text: str


def _ident_end(source: str, start: int) -> int:
    end = start
    while end < len(source) and (source[end].isalnum() or source[end] == "_" or ord(source[end]) > 127):
        end += 1
    return end


def _quoted_end(source: str, start: int, quote: str) -> int:
    """Index behind the closing quote of a string that opens at start."""
    i = start + 1
    while i < len(source):
        if source[i] == "\\":
            i += 2
            continue
        if source[i] == quote:
            return i + 1
        i += 1
    return len(source)


def _heredoc_end(source: str, start: int) -> tuple[int, str]:
    """Index behind a heredoc or nowdoc that opens at start, and its body."""
    i = start + 3
    while source[i] in " \t":
        i += 1
    quote = source[i] if source[i] in "'\"" else ""
    if quote:
        i += 1
    name_end = _ident_end(source, i)
    name = source[i:name_end]
    body_start = source.index("\n", name_end) + 1
    j = body_start
    while j < len(source):
        line_end = source.find("\n", j)
        line = source[j : len(source) if line_end == -1 else line_end]
        if line.strip().startswith(name) and not _ident_end(line.strip(), len(name)) > len(name):
            return j + line.index(name) + len(name), source[body_start:j]
        if line_end == -1:
            break
        j = line_end + 1
    return len(source), source[body_start:]


def php_tokens(source: str) -> list[Token]:
    """The code tokens of a PHP file: names, variables, strings and operators.

    Everything outside ``<?php`` and every comment is dropped. ``#[`` opens an
    attribute and stays code; a lone ``#`` opens a line comment.
    """
    tokens: list[Token] = []
    i = source.find("<?php")
    if i == -1:
        return tokens
    i += len("<?php")
    while i < len(source):
        char = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if char.isspace():
            i += 1
        elif char == "/" and nxt == "*":
            end = source.find("*/", i + 2)
            i = len(source) if end == -1 else end + 2
        elif (char == "/" and nxt == "/") or (char == "#" and nxt != "["):
            end = source.find("\n", i)
            i = len(source) if end == -1 else end
        elif char in "'\"":
            end = _quoted_end(source, i, char)
            tokens.append(Token(STR, source[i + 1 : end - 1]))
            i = end
        elif source.startswith("<<<", i):
            end, body = _heredoc_end(source, i)
            tokens.append(Token(STR, body))
            i = end
        elif char == "$" and (nxt.isalpha() or nxt == "_"):
            end = _ident_end(source, i + 1)
            tokens.append(Token(VAR, source[i:end]))
            i = end
        elif char.isalpha() or char == "_" or char == "\\":
            end = i
            while end < len(source) and (source[end].isalnum() or source[end] in "_\\"):
                end += 1
            tokens.append(Token(IDENT, source[i:end].rsplit("\\", 1)[-1]))
            i = end
        else:
            for op in _OPS:
                if source.startswith(op, i):
                    tokens.append(Token(OP, op))
                    i += len(op)
                    break
            else:
                tokens.append(Token(OP, char))
                i += 1
    return tokens


def method_calls(tokens: list[Token], name: str) -> int:
    """How often ``->name(`` or ``?->name(`` appears among the tokens."""
    count = 0
    for k in range(len(tokens) - 2):
        if (
            tokens[k].kind == OP
            and tokens[k].text in ("->", "?->")
            and tokens[k + 1] == Token(IDENT, name)
            and tokens[k + 2] == Token(OP, "(")
        ):
            count += 1
    return count


def call_arguments(tokens: list[Token], start: int) -> list[Token]:
    """The tokens between the parenthesis at start and its partner."""
    depth = 0
    for k in range(start, len(tokens)):
        if tokens[k] == Token(OP, "("):
            depth += 1
        elif tokens[k] == Token(OP, ")"):
            depth -= 1
            if depth == 0:
                return tokens[start + 1 : k]
    return tokens[start + 1 :]


def logger_calls(tokens: list[Token]) -> list[list[Token]]:
    """The argument tokens of every ``->logger->level(...)`` call."""
    found = []
    for k in range(len(tokens) - 4):
        if (
            tokens[k] == Token(OP, "->")
            and tokens[k + 1] == Token(IDENT, "logger")
            and tokens[k + 2] == Token(OP, "->")
            and tokens[k + 3].kind == IDENT
            and tokens[k + 4] == Token(OP, "(")
        ):
            found.append(call_arguments(tokens, k + 4))
    return found


def php_files() -> dict[str, list[Token]]:
    return {
        path.relative_to(PHP_LIB).as_posix(): php_tokens(path.read_text(encoding="utf-8"))
        for path in sorted(PHP_LIB.rglob("*.php"))
    }


# ---------------------------------------------------------------------------
# A JavaScript scanner, character by character
# ---------------------------------------------------------------------------

# After one of these a slash opens a regex literal, after anything else it divides.
_REGEX_BEFORE = set("(,=:[!&|?{};+-*%<>~^") | {"return", "typeof", ""}


def js_tokens(source: str) -> list[Token]:
    """Names, strings and punctuation of a plain script, comments dropped."""
    tokens: list[Token] = []
    i = 0
    previous = ""
    while i < len(source):
        char = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if char.isspace():
            i += 1
            continue
        if char == "/" and nxt == "*":
            end = source.find("*/", i + 2)
            i = len(source) if end == -1 else end + 2
            continue
        if char == "/" and nxt == "/":
            end = source.find("\n", i)
            i = len(source) if end == -1 else end
            continue
        if char in "'\"`":
            end = _quoted_end(source, i, char)
            tokens.append(Token(STR, source[i + 1 : end - 1]))
            previous = "str"
            i = end
            continue
        if char == "/" and previous in _REGEX_BEFORE:
            j = i + 1
            in_class = False
            while j < len(source):
                if source[j] == "\\":
                    j += 2
                    continue
                if source[j] == "[":
                    in_class = True
                elif source[j] == "]":
                    in_class = False
                elif source[j] == "/" and not in_class:
                    break
                j += 1
            j += 1
            while j < len(source) and source[j].isalpha():
                j += 1
            tokens.append(Token(STR, source[i:j]))
            previous = "str"
            i = j
            continue
        if char.isalpha() or char in "_$":
            end = i
            while end < len(source) and (source[end].isalnum() or source[end] in "_$"):
                end += 1
            word = source[i:end]
            tokens.append(Token(IDENT, word))
            previous = word if word in ("return", "typeof") else "id"
            i = end
            continue
        tokens.append(Token(OP, char))
        previous = char if char not in ")]" else "id"
        i += 1
    return tokens


def js_members(tokens: list[Token]) -> list[tuple[str, str]]:
    """Every ``object.member`` pair, with the object name or '' for an expression."""
    pairs = []
    for k in range(1, len(tokens) - 1):
        if tokens[k] == Token(OP, ".") and tokens[k + 1].kind == IDENT:
            owner = tokens[k - 1].text if tokens[k - 1].kind == IDENT else ""
            pairs.append((owner, tokens[k + 1].text))
    return pairs


# ---------------------------------------------------------------------------
# Positive controls of both scanners
# ---------------------------------------------------------------------------

_PHP_CONTROL = """<?php
/**
 * getFirstNodeById() in a docblock and ->isReadable() in a docblock.
 */
final class X {
	#[\\Override]
	public function a(): void {
		// $userFolder->getFirstNodeById($id) in a line comment
		$s = '->getFirstNodeById(1)';
		$t = "->isReadable()";
		$h = <<<EOT
		->getFirstNodeById(2)
		EOT;
		$node = $this->root->getFirstNodeById($id);
		$ok = $node?->isReadable();
		$this->logger->debug('ignored', ['path' => $folder]);
		$body = ['folder' => $filters->folder];
	}
}
"""


def test_the_php_scanner_finds_a_real_call_and_nothing_in_comments_or_strings() -> None:
    tokens = php_tokens(_PHP_CONTROL)
    assert method_calls(tokens, "getFirstNodeById") == 1
    assert method_calls(tokens, "isReadable") == 1
    assert Token(IDENT, "Override") in tokens, "an attribute is code, not a comment"
    strings = [t.text for t in tokens if t.kind == STR]
    assert "->getFirstNodeById(1)" in strings
    assert any("getFirstNodeById(2)" in s for s in strings), "the heredoc is one string token"
    calls = logger_calls(tokens)
    assert len(calls) == 1
    assert Token(VAR, "$folder") in calls[0]
    assert Token(STR, "folder") in tokens
    assert Token(IDENT, "folder") in tokens


_JS_CONTROL = """
// el.innerHTML = 'comment'
/* document.write('block') */
const a = 'innerHTML'
const r = /^\\/+|\\/+$/g
const b = x.replace(/a\\/b[/]c/, '')
el.innerHTML = a
document.title = r
"""


def test_the_js_scanner_finds_a_real_member_and_nothing_in_comments_strings_or_regexes() -> None:
    members = js_members(js_tokens(_JS_CONTROL))
    assert ("el", "innerHTML") in members
    assert ("document", "title") in members
    assert ("x", "replace") in members
    assert ("document", "write") not in members
    assert [m for m in members if m[1] == "innerHTML"] == [("el", "innerHTML")]


# ---------------------------------------------------------------------------
# Source probes of the phase
# ---------------------------------------------------------------------------


def test_the_php_tree_asks_resolution_and_readability_exactly_once_each() -> None:
    """One resolution and one readability question, both in the search boundary."""
    resolutions: dict[str, int] = {}
    readability: dict[str, int] = {}
    for name, tokens in php_files().items():
        if (count := method_calls(tokens, "getFirstNodeById")) > 0:
            resolutions[name] = count
        if (count := method_calls(tokens, "isReadable")) > 0:
            readability[name] = count
    assert resolutions == {"Service/SearchService.php": 1}
    assert readability == {"Service/SearchService.php": 1}


def test_no_folder_value_has_a_way_into_a_request_body_of_exappservice() -> None:
    """ExAppService knows no folder: neither a property, nor a key, nor a variable."""
    tokens = php_tokens((PHP_LIB / "Service" / "ExAppService.php").read_text(encoding="utf-8"))
    assert tokens, "the scanner read the file"
    # 'path' is no probe here: ExAppService carries the route path of the admin
    # page under that name since phase 4, which is no file path.
    named = {t.text.lower() for t in tokens if t.kind in (IDENT, VAR, STR)}
    assert not {n for n in named if "folder" in n or n in ("$scope", "scope", "scopeof", "coordinates")}


def test_the_folder_of_the_filters_goes_into_scopeof_and_nowhere_else() -> None:
    tokens = php_tokens((PHP_LIB / "Service" / "SearchService.php").read_text(encoding="utf-8"))
    uses = [
        k
        for k in range(len(tokens) - 1)
        if tokens[k] == Token(OP, "->")
        and tokens[k + 1] == Token(IDENT, "folder")
        and tokens[k - 1] == Token(VAR, "$filters")
    ]
    assert len(uses) == 1
    k = uses[0]
    window = tokens[max(0, k - 6) : k]
    assert Token(IDENT, "scopeOf") in window


_PHASE_PHP = (
    "Search/Provider.php",
    "Search/FilterProvider.php",
    "Service/SearchService.php",
    "Service/SearchFilters.php",
    "Listener/LoadUnifiedSearchFiltersListener.php",
    "Controller/PageController.php",
)

# Variables that carry user content in these files: the term, the folder, a
# path, a raw filter value, a node or a cache entry.
_CONTENT_VARS = {
    "$term",
    "$folder",
    "$path",
    "$value",
    "$raw",
    "$query",
    "$node",
    "$scope",
    "$entry",
    "$candidate",
    "$filters",
    "$filter",
}


def test_no_log_call_of_the_phase_files_carries_a_term_a_folder_or_a_path() -> None:
    offenders = []
    for name in _PHASE_PHP:
        tokens = php_tokens((PHP_LIB / name).read_text(encoding="utf-8"))
        for arguments in logger_calls(tokens):
            carried = {t.text for t in arguments if t.kind == VAR} & _CONTENT_VARS
            if carried:
                offenders.append((name, sorted(carried)))
    assert offenders == []


def test_the_filter_provider_decides_nothing_about_rights() -> None:
    """findling-filter hands a chip request to the real provider and does nothing else."""
    tokens = php_tokens((PHP_LIB / "Search" / "FilterProvider.php").read_text(encoding="utf-8"))
    names = {t.text for t in tokens if t.kind == IDENT}
    assert not names & {
        "getFirstNodeById",
        "isReadable",
        "getUserFolder",
        "SearchService",
        "ExAppService",
        "IRootFolder",
        "LoggerInterface",
        "IDBConnection",
    }
    # Exactly one call into the real provider's search, with the user and the
    # query exactly as they came.
    calls = [
        k
        for k in range(len(tokens) - 3)
        if tokens[k] == Token(VAR, "$this")
        and tokens[k + 2] == Token(IDENT, "provider")
        and tokens[k + 4] == Token(IDENT, "search")
    ]
    assert len(calls) == 1
    arguments = call_arguments(tokens, calls[0] + 5)
    assert [t.text for t in arguments] == ["$user", ",", "$query"]


def test_the_page_listener_holds_no_service() -> None:
    """It runs on every page view: no constructor, nothing injected."""
    tokens = php_tokens((PHP_LIB / "Listener" / "LoadUnifiedSearchFiltersListener.php").read_text(encoding="utf-8"))
    names = {t.text for t in tokens if t.kind == IDENT}
    assert "__construct" not in names
    assert method_calls(tokens, "isLoggedIn") == 1


# What the script may touch on the page: reading the ready state and waiting for
# it. Nothing else of the document, no element, no storage, no network.
_DOM_WRITES = {
    "innerHTML",
    "outerHTML",
    "insertAdjacentHTML",
    "insertAdjacentElement",
    "write",
    "writeln",
    "appendChild",
    "append",
    "prepend",
    "replaceChildren",
    "insertBefore",
    "createElement",
    "setAttribute",
    "textContent",
    "innerText",
    "cookie",
    "src",
    "href",
}
_FORBIDDEN_NAMES = {
    "eval",
    "Function",
    "fetch",
    "XMLHttpRequest",
    "sendBeacon",
    "localStorage",
    "sessionStorage",
    "indexedDB",
    "WebSocket",
    "importScripts",
    "axios",
}


def test_the_script_writes_nothing_into_the_page_and_asks_the_server_nothing() -> None:
    tokens = js_tokens(SCRIPT.read_text(encoding="utf-8"))
    members = js_members(tokens)
    assert members, "the scanner read the script"
    assert {m for m in members if m[1] in _DOM_WRITES} == set()
    assert {t.text for t in tokens if t.kind == IDENT} & _FORBIDDEN_NAMES == set()
    assert {m[1] for m in members if m[0] == "document"} == {"readyState", "addEventListener"}
    # The one property the script writes is the filter map of the menu entry.
    writes = {
        tokens[k - 1].text
        for k in range(1, len(tokens) - 1)
        if tokens[k] == Token(OP, "=")
        and tokens[k + 1] != Token(OP, "=")
        and k >= 2
        and tokens[k - 2] == Token(OP, ".")
    }
    assert writes == {"filters", "folder"}


# ---------------------------------------------------------------------------
# Instance probes
# ---------------------------------------------------------------------------

URL = os.environ.get("FINDLING_AUDIT32_URL", "")
ALICE = os.environ.get("FINDLING_AUDIT32_ALICE_PASS", "")
BOB = os.environ.get("FINDLING_AUDIT32_BOB_PASS", "")
CONTAINER = os.environ.get("FINDLING_AUDIT32_CONTAINER", "")
BACKEND_LOG = os.environ.get("FINDLING_AUDIT32_BACKEND_LOG", "")
BACKEND_URL = os.environ.get("FINDLING_AUDIT32_BACKEND_URL", "")

instance = pytest.mark.skipif(not (URL and ALICE and BOB), reason="no audit instance (FINDLING_AUDIT32_URL)")

WORD = "auditwort32"
DOOR = "Show all results"

# What alice sees without a filter, what she sees in /Projekte, and what she must
# never see. Weg.txt was shared and the share was taken back before the run.
UNFILTERED = frozenset({"Plan.txt", "Tief.pdf", "Neben.txt", "Cafe.txt", "Umbenannt.txt", "Wurzel.txt", "Geteilt.txt"})
PROJEKTE = frozenset({"Plan.txt", "Tief.pdf"})
FOREIGN = frozenset({"Geheim.txt", "NurBob.txt", "Weg.txt"})
PDF = frozenset({"Tief.pdf"})
TEXT = UNFILTERED - PDF
EMPTY: frozenset[str] = frozenset()

CAFE_NFC = unicodedata.normalize("NFC", "Café32")
CAFE_NFD = unicodedata.normalize("NFD", "Café32")


@dataclass(frozen=True, slots=True)
class Case:
    """One corpus value: the raw query string piece and the allowed outcomes."""

    label: str
    query: str
    allowed: tuple[frozenset[str], ...]
    status: int = 200


def _q(text: str) -> str:
    """Percent encode every byte that is not unreserved, so the server reads text."""
    return "".join(c if c.isalnum() or c in "-._~" else "".join(f"%{b:02X}" for b in c.encode()) for c in text)


FOLDER_CASES = (
    Case("traversal into bob", "folder=" + _q("/../bob/files/Geheim"), (UNFILTERED,)),
    Case("traversal encoded once", "folder=..%2F..%2Fbob", (UNFILTERED,)),
    Case("traversal encoded twice", "folder=..%252F..%252Fbob%252Ffiles%252FGeheim", (UNFILTERED,)),
    Case("dot segments back into the own folder", "folder=" + _q("/./Projekte/../Projekte"), (UNFILTERED, PROJEKTE)),
    # The core turns a backslash into a slash (PathHelper::normalizePath), so
    # this is the own subfolder in another spelling.
    Case("backslash separators", "folder=" + _q("\\Projekte\\Unter"), (frozenset({"Tief.pdf"}), UNFILTERED)),
    Case("backslash traversal", "folder=" + _q("..\\..\\bob\\files\\Geheim"), (UNFILTERED,)),
    Case("NUL byte", "folder=%2FProjekte%00", (UNFILTERED,)),
    Case("NUL byte inside", "folder=%2FProj%00ekte", (UNFILTERED,)),
    Case("line feed", "folder=%2FProjekte%0A", (UNFILTERED,)),
    Case("unit separator", "folder=%2FProjekte%1F", (UNFILTERED,)),
    Case("delete", "folder=%2FProjekte%7F", (UNFILTERED,)),
    Case("NFC name", "folder=" + _q("/" + CAFE_NFC), (frozenset({"Cafe.txt"}),)),
    # M-32-01 as well: the NFD spelling resolved and found nothing below it.
    # Since the fix the value is composed into NFC and narrows like the NFC one.
    Case("NFD name", "folder=" + _q("/" + CAFE_NFD), (frozenset({"Cafe.txt"}),)),
    Case("bidi override", "folder=" + _q("/Projekte‮"), (UNFILTERED,)),
    Case("bidi in front", "folder=" + _q("/‮etkejorP"), (UNFILTERED,)),
    Case("4000 characters", "folder=" + _q("/" + "a" * 3999), (UNFILTERED,)),
    Case("4001 characters", "folder=" + _q("/" + "a" * 4000), (UNFILTERED,)),
    Case("a folder only bob has", "folder=%2FGeheim", (UNFILTERED,)),
    Case("a folder of bob by his home path", "folder=" + _q("/bob/files/Geheim"), (UNFILTERED,)),
    Case("a folder nobody has", "folder=%2FGibtEsNicht32", (UNFILTERED,)),
    Case("a share taken back", "folder=%2FWeg", (UNFILTERED,)),
    Case("a received share", "folder=%2FGeteilt", (frozenset({"Geteilt.txt"}),)),
    Case("a file instead of a folder", "folder=%2FWurzel.txt", (UNFILTERED,)),
    Case("trailing slash", "folder=%2FProjekte%2F", (PROJEKTE,)),
    Case("no leading slash", "folder=Projekte", (PROJEKTE,)),
    Case("double slashes", "folder=%2F%2FProjekte%2F%2FUnter", (frozenset({"Tief.pdf"}), UNFILTERED)),
    Case("subfolder", "folder=%2FProjekte%2FUnter", (frozenset({"Tief.pdf"}),)),
    Case("prefix sibling", "folder=%2FProjekte2", (frozenset({"Neben.txt"}),)),
    Case("prefix without separator", "folder=%2FProjekt", (UNFILTERED,)),
    Case("an empty own folder", "folder=%2FLeer32", (EMPTY,)),
    Case("root", "folder=%2F", (UNFILTERED,)),
    Case("many slashes", "folder=%2F%2F%2F%2F", (UNFILTERED,)),
    Case("home of the user", "folder=~", (UNFILTERED,)),
    Case("tilde bob", "folder=" + _q("~bob/Geheim"), (UNFILTERED,)),
    Case("proc self", "folder=" + _q("/proc/self/root"), (UNFILTERED,)),
    # M-32-01: a dot segment resolved to a node with a path nobody else uses,
    # and the recheck below it found nothing, an empty group. Since the fix a
    # value with a dot segment is no folder at all.
    Case("dot", "folder=.", (UNFILTERED,)),
    Case("slash dot", "folder=%2F.", (UNFILTERED,)),
    Case("trailing dot segment", "folder=%2FProjekte%2F.", (UNFILTERED,)),
    Case("leading dot segment", "folder=%2F.%2FProjekte", (UNFILTERED,)),
    Case("inner dot segment", "folder=%2FProjekte%2F.%2FUnter", (UNFILTERED,)),
    Case("backslash dot segment", "folder=" + _q("\\Projekte\\.\\Unter"), (UNFILTERED,)),
    Case("a hidden name is no dot segment", "folder=%2F.versteckt32", (UNFILTERED,)),
    Case("other case on a case sensitive storage", "folder=%2Fprojekte", (UNFILTERED,)),
    Case("dot dot", "folder=..", (UNFILTERED,)),
    Case("url as folder", "folder=" + _q("http://127.0.0.1:10035/"), (UNFILTERED,)),
    Case("empty value", "folder=", (), 400),
)

TYPE_CASES = (
    Case("upper case", "types=PDF", (PDF,)),
    Case("blanks around", "types=" + _q(" pdf "), (PDF,)),
    Case("two with blank", "types=" + _q("pdf, text"), (UNFILTERED,)),
    Case("empty parts", "types=" + _q(",,pdf,,"), (PDF,)),
    Case("semicolon", "types=" + _q("pdf;text"), (UNFILTERED,)),
    Case("a thousand repetitions", "types=" + _q(",".join(["pdf"] * 1000)), (UNFILTERED,)),
    Case("cyrillic er", "types=" + _q(chr(0x0440) + "df"), (UNFILTERED,)),
    Case("fullwidth", "types=" + _q("".join(map(chr, (0xFF50, 0xFF44, 0xFF46)))), (UNFILTERED,)),
    Case("json text", "types=" + _q('["pdf"]'), (UNFILTERED,)),
    Case("NUL next to a name", "types=pdf%00", (UNFILTERED,)),
    Case("unknown group", "types=archives", (UNFILTERED,)),
    Case("text group", "types=text", (TEXT,)),
    Case("empty value", "types=", (), 400),
)

# Array forms: what the core does with them is the finding, not an expectation.
ARRAY_CASES = (
    Case("folder as array", "folder%5B%5D=%2FProjekte", (UNFILTERED, PROJEKTE, EMPTY), -1),
    Case("types as array", "types%5B%5D=pdf", (UNFILTERED, PDF, EMPTY), -1),
)


@dataclass
class Answer:
    status: int
    titles: frozenset[str]
    ids: tuple[str, ...]
    door: str | None
    cursor: object
    seconds: float
    body: str = ""


@dataclass
class CorpusRun:
    answers: dict[tuple[str, str], Answer] = field(default_factory=dict)
    nextcloud_lines: list[str] = field(default_factory=list)
    backend_lines: list[str] = field(default_factory=list)
    array_lines: list[str] = field(default_factory=list)
    markers: tuple[str, str] = ("", "")


def ask(user: str, provider: str, query: str, password: str | None = None) -> Answer:
    secret = password if password is not None else (ALICE if user == "alice" else BOB)
    url = f"{URL}/ocs/v2.php/search/providers/{provider}/search?format=json&term={WORD}&limit=20&{query}"
    started = time.perf_counter()
    response = httpx.get(url, auth=(user, secret), headers={"OCS-APIRequest": "true"}, timeout=60)
    seconds = time.perf_counter() - started
    titles: set[str] = set()
    ids: list[str] = []
    door = None
    cursor = None
    if response.status_code == 200:
        data = response.json()["ocs"]["data"]
        cursor = data.get("cursor")
        for entry in data["entries"]:
            file_id = entry["attributes"].get("fileId") if isinstance(entry["attributes"], dict) else None
            if file_id is None:
                door = entry["resourceUrl"]
                continue
            titles.add(entry["title"])
            ids.append(file_id)
    return Answer(response.status_code, frozenset(titles), tuple(sorted(ids)), door, cursor, seconds, response.text)


def _nextcloud_log_lines() -> list[str]:
    if not CONTAINER:
        return []
    docker = shutil.which("docker")
    if docker is None:
        return []
    out = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [docker, "exec", CONTAINER, "cat", "/var/www/html/data/nextcloud.log"],
        capture_output=True,
        check=True,
        env={**os.environ, "MSYS_NO_PATHCONV": "1"},
    )
    return out.stdout.decode("utf-8", "replace").splitlines()


def _backend_log_lines() -> list[str]:
    if not BACKEND_LOG:
        return []
    return Path(BACKEND_LOG).read_text(encoding="utf-8", errors="replace").splitlines()


@pytest.fixture(scope="module")
def corpus() -> CorpusRun:
    run = CorpusRun()
    nc_before = len(_nextcloud_log_lines())
    backend_before = len(_backend_log_lines())
    for case in FOLDER_CASES + TYPE_CASES:
        for provider in ("findling", "findling-filter"):
            run.answers[(case.label + " / " + case.query[:5], provider)] = ask("alice", provider, case.query)
    run.answers[("baseline", "findling")] = ask("alice", "findling", "")
    run.answers[("baseline", "findling-filter")] = ask("alice", "findling-filter", "")
    # Positive controls of the log probe: a failed login with a marker as user
    # name, which the core logs as a warning, and a marker in the path of a
    # request to the backend, which its access log writes.
    nc_marker = "auditmarker32" + secrets.token_hex(4)
    backend_marker = "auditmarker32" + secrets.token_hex(4)
    # Not the search route: the core writes the address into the line, and the
    # address of a search carries the term.
    httpx.get(
        f"{URL}/ocs/v2.php/cloud/user?format=json",
        auth=(nc_marker, "wrong-" + secrets.token_hex(4)),
        headers={"OCS-APIRequest": "true"},
        timeout=30,
    )
    if BACKEND_URL:
        httpx.get(f"{BACKEND_URL}/heartbeat?{backend_marker}=1", timeout=10)
    time.sleep(2)
    run.markers = (nc_marker, backend_marker)
    run.nextcloud_lines = _nextcloud_log_lines()[nc_before:]
    run.backend_lines = _backend_log_lines()[backend_before:]
    # The array forms last and on their own: the core answers them with a 500
    # and logs the request address (L-32-01), which is not the probe above.
    array_before = len(_nextcloud_log_lines())
    for case in ARRAY_CASES:
        for provider in ("findling", "findling-filter"):
            run.answers[(case.label + " / " + case.query[:5], provider)] = ask("alice", provider, case.query)
    run.array_lines = _nextcloud_log_lines()[array_before:]
    return run


def _cases() -> list[Case]:
    return list(FOLDER_CASES + TYPE_CASES)


@instance
def test_the_seed_is_what_the_corpus_expects(corpus: CorpusRun) -> None:
    baseline = corpus.answers[("baseline", "findling")]
    assert baseline.status == 200
    assert baseline.titles == UNFILTERED
    chipless = corpus.answers[("baseline", "findling-filter")]
    assert (chipless.status, chipless.titles) == (200, EMPTY)
    bob = ask("bob", "findling", "")
    assert {"Geheim.txt", "NurBob.txt", "Weg.txt", "Geteilt.txt"} <= bob.titles


@instance
@pytest.mark.parametrize("case", _cases(), ids=lambda c: c.label)
@pytest.mark.parametrize("provider", ["findling", "findling-filter"])
def test_a_manipulated_value_never_shows_a_foreign_file_and_never_fails(
    corpus: CorpusRun, case: Case, provider: str
) -> None:
    answer = corpus.answers[(case.label + " / " + case.query[:5], provider)]
    assert answer.status == case.status, answer.body[:300]
    assert answer.status < 500
    assert not answer.titles & FOREIGN
    assert answer.titles <= UNFILTERED
    if case.status == 200:
        assert answer.titles in case.allowed


@instance
@pytest.mark.parametrize("case", ARRAY_CASES, ids=lambda c: c.label)
def test_the_array_form_of_a_filter_ends_in_the_core_before_findling_is_asked(corpus: CorpusRun, case: Case) -> None:
    """L-32-01: SearchComposer::buildFilter() takes a string and the core throws.

    The core answers with HTTP 500 and logs a TypeError with the request
    address; Findling is never reached. The counter probe with the core's own
    Files provider (path[] and term[]) answers the same way, see 32-AUDIT.md.
    """
    for provider in ("findling", "findling-filter"):
        answer = corpus.answers[(case.label + " / " + case.query[:5], provider)]
        assert answer.status == 500
        assert answer.titles == EMPTY
    if CONTAINER:
        errors = [line for line in corpus.array_lines if '"level":3' in line]
        assert errors
        assert all(
            "SearchComposer::buildFilter(): Argument #2 ($value) must be of type string" in line for line in errors
        )
        assert not any("Findling" in line or "OCA\\\\Findling" in line for line in errors)


@instance
def test_a_foreign_folder_and_a_folder_nobody_has_answer_alike() -> None:
    """The oracle probe: same status, same ids, and the time is measured."""
    foreign: list[float] = []
    missing: list[float] = []
    first_foreign = ask("alice", "findling-filter", "folder=%2FGeheim")
    first_missing = ask("alice", "findling-filter", "folder=%2FGibtEsNicht32")
    assert (first_foreign.status, first_foreign.ids) == (first_missing.status, first_missing.ids)
    for _ in range(11):
        foreign.append(ask("alice", "findling-filter", "folder=%2FGeheim").seconds)
        missing.append(ask("alice", "findling-filter", "folder=%2FGibtEsNicht32").seconds)
    difference = statistics.median(foreign) - statistics.median(missing)
    print(f"oracle median foreign {statistics.median(foreign):.4f} s, missing {statistics.median(missing):.4f} s")
    assert abs(difference) < 0.25


@instance
def test_no_log_line_carries_a_corpus_folder_or_the_term(corpus: CorpusRun) -> None:
    nc_marker, backend_marker = corpus.markers
    if CONTAINER:
        assert any(nc_marker in line for line in corpus.nextcloud_lines), "positive control: the failed login is logged"
    if BACKEND_URL and BACKEND_LOG:
        assert any(backend_marker in line for line in corpus.backend_lines), "positive control: the access log"
    words = ("Projekte", "Geheim", "GibtEsNicht32", "NurBob", "Café32", "Cafe", "Leer32", "Wurzel", "proc/self", WORD)
    found = [
        (word, line[:200])
        for line in corpus.nextcloud_lines + corpus.backend_lines
        for word in words
        if word in line or word in unicodedata.normalize("NFD", line)
    ]
    assert found == []


@instance
def test_the_next_page_of_a_folder_stays_in_the_folder() -> None:
    first = ask("alice", "findling-filter", "folder=%2FProjekte&limit=1")
    assert len(first.titles) == 1
    assert first.titles <= PROJEKTE
    assert first.cursor is not None, "one of two hits shown, the group is paginated"
    second = ask("alice", "findling-filter", f"folder=%2FProjekte&limit=1&cursor={first.cursor}")
    assert second.titles <= PROJEKTE
    assert first.titles | second.titles == PROJEKTE


@instance
def test_a_folder_and_a_type_go_together_with_the_date_of_the_core() -> None:
    now = time.time()
    since = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - 30 * 86400))
    until = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now + 86400))
    old_since, old_until = "2020-01-01T00:00:00Z", "2021-01-01T00:00:00Z"
    assert ask("alice", "findling-filter", f"folder=%2FProjekte&since={since}&until={until}").titles == PROJEKTE
    assert ask("alice", "findling-filter", f"folder=%2FProjekte&since={old_since}&until={old_until}").titles == EMPTY
    assert ask("alice", "findling-filter", f"types=pdf&since={since}&until={until}").titles == PDF
    assert ask("alice", "findling-filter", f"types=pdf&since={old_since}&until={old_until}").titles == EMPTY


@instance
def test_the_door_of_a_type_chip_carries_the_type_and_never_the_folder() -> None:
    typed = ask("alice", "findling-filter", "types=text&limit=2")
    assert typed.door is not None
    assert "types=text" in typed.door
    folder = ask("alice", "findling-filter", "folder=%2FProjekte&limit=1")
    assert folder.door is not None
    assert "folder" not in folder.door
    assert "Projekte" not in folder.door


def _move(source: str, target: str) -> int:
    response = httpx.request(
        "MOVE",
        f"{URL}/remote.php/dav/files/alice/{source}",
        auth=("alice", ALICE),
        headers={"Destination": f"{URL}/remote.php/dav/files/alice/{target}"},
        timeout=30,
    )
    return response.status_code


@instance
def test_a_folder_renamed_while_the_chip_stands_is_no_folder_any_more() -> None:
    """The chip still names the old folder; the value no longer resolves (USRCH-03)."""
    assert ask("alice", "findling-filter", "folder=%2FAlt32").titles == frozenset({"Umbenannt.txt"})
    assert _move("Alt32", "Neu32") == 201
    try:
        old = ask("alice", "findling-filter", "folder=%2FAlt32")
        new = ask("alice", "findling-filter", "folder=%2FNeu32")
        assert old.status == 200
        assert old.titles == UNFILTERED
        assert new.titles == frozenset({"Umbenannt.txt"})
    finally:
        assert _move("Neu32", "Alt32") == 201


@instance
def test_the_provider_list_names_findling_and_not_the_hidden_one() -> None:
    response = httpx.get(
        f"{URL}/ocs/v2.php/search/providers?format=json",
        auth=("alice", ALICE),
        headers={"OCS-APIRequest": "true"},
        timeout=30,
    )
    ids = {p["id"] for p in response.json()["ocs"]["data"]}
    assert "findling" in ids
    assert "findling-filter" not in ids
