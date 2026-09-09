"""No second recheck: the permission boundary of the PHP half, read out of the sources.

UI-03 of phase 9 asks for one answer to "may this user see this file", not two.
The own result page and the unified search dialog show the same hits under the
same rules, so plan 09-03 pulled the recheck loop out of ``Search/Provider.php``
into ``Service/SearchService.php`` and left both callers with nothing but a
translation. What this gate holds is that it stays that way.

**Why a grep and not a functional test.** A functional test cannot prove the
absence of a second recheck. It exercises what exists, and a second loop would
sit next to everything it touches while every single assertion stayed green.
Two call sites and three call sites behave identically in every scenario
anybody can write down, and only one of them is the structure UI-03 asks for.
So the assertions below read the sources, in the shape
``test_semantic_boundary.py`` invented for the Python half and
``test_php_trust_boundary.py`` repeated against PHP.

**The two questions are not the same question, and the gate treats them
differently.** Resolving a file id through the user's own folder answers "is
this reachable for them" and is asked at three places in this tree, each for a
different job: the search boundary, the content gateway that hands bytes to the
container behind ``rejectForeignCaller``, and the crawl, which asks a node for
its size and says in its own comment that it is not a permission control. A
register below names all three with their counts, so a fourth one cannot appear
quietly. The readability question is the search boundary itself: it is what
tells a reachable node from a readable one on a team folder, and it is asked at
exactly one place in the whole tree. A second recheck loop needs it, so pinning
it to one is what makes the second loop impossible rather than merely absent.

**Grep hygiene is part of the job here, not a detail.** The PHP sources of this
repository explain both names in prose: two event listeners, the queue service
and this phase's own service docblocks all mention them without calling them. A
counting assertion that trips over its own explanatory text is an assertion
somebody deletes, and they would be right to. Every count below therefore runs
over the code of a source with comments and string literals removed, and the
self tests prove the stripper does what it says.

**What this gate does not prove.** It says nothing about whether the one recheck
decides correctly. That is the job of ``php/tests/Unit/SearchServiceTest.php``,
of the ``search-parity`` job in ``.github/workflows/integration.yml`` and of the
guest and share scenarios beside it. This gate is about absence, and absence is
the one thing a functional test cannot show.
"""

from __future__ import annotations

import re
from pathlib import Path

PHP_LIB = Path(__file__).resolve().parents[2] / "php" / "lib"

# The two questions of the permission chain, by the name they are called under.
RESOLUTION = "getFirstNodeById"
READABILITY = "isReadable"

# The one file that is allowed to ask the readability question, relative to
# php/lib. It is the search boundary of the product: a node a user can reach is
# not always a node a user may read, and the difference is a team folder with
# per folder rules.
BOUNDARY = "Service/SearchService.php"

# Every place that resolves a file id, with how often it does so. Three jobs,
# three files, and each of them is a boundary of its own:
#
# * the search boundary, which decides what a search may show,
# * the content gateway, which opens the bytes for the container and is kept
#   from foreign containers by rejectForeignCaller rather than by this line,
# * the crawl, which resolves a node for its size and states in its own comment
#   that a stale prefilter costs result quality and never confidentiality.
#
# The register is a ratchet: a plan that adds a resolution adds it here, and a
# plan that removes one removes it here. A file that is not named is a finding,
# whatever it does with the node.
RESOLUTION_REGISTER = {
    BOUNDARY: 1,
    "Controller/GatewayController.php": 1,
    "Service/QueueService.php": 1,
}

# Block comments, line comments and both kinds of string literal, in the order
# they have to be removed. The hash sign is deliberately NOT a comment
# introducer here: PHP 8 attributes begin with a hash and a bracket, the routes
# of this app are declared with them, and a line filter that dropped them would
# swallow whole method bodies of the controllers. The PHP sources of this
# repository write every comment with slashes, which is what makes leaving the
# hash alone safe as well as necessary.
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENT = re.compile(r"//[^\n]*")
_DOUBLE_QUOTED = re.compile(r'"(?:\\.|[^"\\])*"', re.DOTALL)
_SINGLE_QUOTED = re.compile(r"'(?:\\.|[^'\\])*'", re.DOTALL)


def code_of(source: str) -> str:
    """One PHP source with its comments and string literals removed.

    Block comments go first, because a line comment inside a docblock is part of
    the docblock and removing it separately would leave the docblock standing.
    The literals go last, so that a slash inside a string cannot start a comment
    that eats the rest of the file.
    """
    without_comments = _LINE_COMMENT.sub("", _BLOCK_COMMENT.sub("", source))

    return _SINGLE_QUOTED.sub("''", _DOUBLE_QUOTED.sub('""', without_comments))


def calls(source: str, name: str) -> int:
    """How often a method is *called* in the code of a source.

    An arrow and the name is a call, a definition is not: ``function isReadable``
    declares the question instead of asking it, and counting a declaration
    against the budget of the askers would make the gate unreadable on the day
    somebody writes one.
    """
    return len(re.findall(r"->\s*" + re.escape(name) + r"\s*\(", code_of(source)))


def php_sources() -> list[tuple[str, str]]:
    """Every PHP source under php/lib, as (relative path, text), in a fixed order."""
    return [
        (path.relative_to(PHP_LIB).as_posix(), path.read_text(encoding="utf-8"))
        for path in sorted(PHP_LIB.rglob("*.php"))
    ]


def resolution_findings(sources: list[tuple[str, str]]) -> list[str]:
    """Every disagreement between the register and the tree, one line each.

    A finding names the file and the number, because a gate that only says
    "something moved" sends the next reader looking for what this function has
    already found.
    """
    counted = {name: calls(source, RESOLUTION) for name, source in sources}

    unregistered = [
        f"{name} resolves a file id {count} time(s) and is not in the register of {RESOLUTION}"
        for name, count in sorted(counted.items())
        if count and name not in RESOLUTION_REGISTER
    ]
    wrong_count = [
        f"{name} resolves a file id {counted.get(name, 0)} time(s), the register says {expected}"
        for name, expected in sorted(RESOLUTION_REGISTER.items())
        if counted.get(name, 0) != expected
    ]

    return unregistered + wrong_count


def readability_findings(sources: list[tuple[str, str]]) -> list[str]:
    """Every place that asks the readability question, beyond the one that may."""
    counted = {name: calls(source, READABILITY) for name, source in sources}

    return [
        f"{name} asks the readability question {count} time(s); only {BOUNDARY} may, and only once"
        for name, count in sorted(counted.items())
        if count != (1 if name == BOUNDARY else 0)
    ]


# -- the real tree ---------------------------------------------------------


def test_the_gate_reads_php_sources_at_all() -> None:
    # The first anti vacuity clause. A renamed directory would leave every
    # count below running over an empty list, and an empty list agrees with
    # every rule there is.
    sources = php_sources()

    assert PHP_LIB.is_dir(), f"{PHP_LIB} is not a directory"
    assert len(sources) > 5, f"php/lib holds {len(sources)} sources, which is too few to be the tree"


def test_the_boundary_still_asks_both_questions_after_the_stripping() -> None:
    # The second clause, and the one that catches a stripper that ate too much.
    # Without it a regular expression that swallowed whole method bodies would
    # report zero call sites everywhere and look like a perfectly clean tree.
    source = (PHP_LIB / BOUNDARY).read_text(encoding="utf-8")

    assert calls(source, RESOLUTION) == 1
    assert calls(source, READABILITY) == 1


def test_the_readability_question_is_asked_at_exactly_one_place() -> None:
    assert readability_findings(php_sources()) == []


def test_every_file_that_resolves_a_file_id_is_one_of_the_three_registered_ones() -> None:
    assert resolution_findings(php_sources()) == []


# -- self tests: the gate has to report what it judges ----------------------


_SECOND_CALLER = """<?php

namespace OCA\\Findling\\Controller;

final class PageController {
	public function index(int $fileId): void {
		$node = $this->rootFolder->getUserFolder('u')->getFirstNodeById($fileId);
		if (!$node->isReadable()) {
			return;
		}
	}
}
"""


def test_a_second_caller_in_a_second_file_is_reported() -> None:
    # The red proof of both counts, against the real tree plus one file. The
    # shape is the one this phase could have written by accident: a page
    # controller that does its own recheck instead of asking the shared service.
    grown = [*php_sources(), ("Controller/PageController.php", _SECOND_CALLER)]

    resolution = resolution_findings(grown)
    readability = readability_findings(grown)

    assert len(resolution) == 1
    assert "Controller/PageController.php" in resolution[0]
    assert len(readability) == 1
    assert "Controller/PageController.php" in readability[0]


_DOCBLOCK_ONLY = """<?php

/**
 * The recheck resolves the file through getUserFolder()->getFirstNodeById()
 * and then asks $node->isReadable(), and neither line is a call site.
 */
final class Listener {
	// A second explanation, this time behind two slashes:
	// ->getFirstNodeById() is where a candidate becomes a hit.
	public function handle(): void {
		$reason = 'getFirstNodeById';
		$other = "->isReadable()";
	}
}
"""


def test_a_name_in_a_docblock_or_a_string_is_not_a_call_site() -> None:
    # The hygiene this gate exists with rather than beside: the PHP sources
    # explain both names in prose in at least four files, and a gate that
    # counted its own explanations would be deleted by the next reader.
    assert calls(_DOCBLOCK_ONLY, RESOLUTION) == 0
    assert calls(_DOCBLOCK_ONLY, READABILITY) == 0


_WITH_ATTRIBUTES = """<?php

final class GatewayController {
	#[\\OCP\\AppFramework\\Http\\Attribute\\ExAppRequired]
	#[\\OCP\\AppFramework\\Http\\Attribute\\ApiRoute(verb: 'GET', url: '/files/{fileId}')]
	public function getFileContents(int $fileId, string $userId): void {
		$file = $this->rootFolder->getUserFolder($userId)->getFirstNodeById($fileId);
	}
}
"""


def test_an_attribute_line_does_not_hide_the_body_behind_it() -> None:
    # The reason the hash sign is not treated as a comment introducer. Every
    # route of this app is declared with a PHP 8 attribute, and a stripper that
    # read the hash as a comment would drop the declaration and, on a one line
    # method, the call with it.
    assert calls(_WITH_ATTRIBUTES, RESOLUTION) == 1
    assert "ApiRoute" in code_of(_WITH_ATTRIBUTES)


def test_a_declaration_of_the_question_is_not_a_call_of_it() -> None:
    # A class that implements the question rather than asking it, which is what
    # a test double in php/tests does. The rule keeps the gate readable if such
    # a class ever moves into php/lib.
    declaration = "<?php\nfinal class Node {\n\tpublic function isReadable(): bool {\n\t\treturn true;\n\t}\n}\n"

    assert calls(declaration, READABILITY) == 0
