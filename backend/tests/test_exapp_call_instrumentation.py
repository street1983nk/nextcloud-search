"""Auflage A3, gelesen als Text: die Messung des inneren Aufrufs.

Finding M-01 of the phase 15 audit left one question open, and it is the one
MEM-03 actually asks: does the INNER call keep its ceiling. Three of the four
runs of the first search took longer than 1.5 s, the status was 200 in all
four, and no raw file of that trip carries the duration of the call from PHP to
the container. The methodology correction in ``docs/performance.md`` has said
since 10.09.2026 that the ceiling of 1501 ms belongs to that inner call and not
to the whole request on the user route, so a total above 1.5 s proves nothing
either way. Plan 16-06 measures the inner call in
``php/lib/Service/ExAppService.php`` and writes it down once it was slow.

**Why this gate reads a PHP file as text.** There is no PHP on the development
machine of this project and none in this repository, so the PHPUnit cases of
``php/tests/Unit/ExAppServiceTest.php`` only ever run in CI and never before a
commit. The same reasoning is written out in ``docs/testing.md`` and is what
the other textual gates of this repository rest on: a gate that reads the
source as text is worth more than the perfect check that does not exist here.
It fails closed, so a file that moved makes it red rather than quiet, and the
case that carries the most weight brings its own self test against a staged
sample, so that a scanner whose body was deleted cannot report zero findings
over zero statements and look healthy.

**What it holds, in four statements.** The measurement sits around the proxy
call and nothing else (threat T-16-22: a measurement that wandered off would
time the whole request again and answer a different question). The line stands
behind the threshold (T-16-20: the unified search asks once per keystroke, so a
line per call would fill the log of an instance). No statement this class
writes into the log carries a search term, a file name or a user id (T-16-21:
the log of a Nextcloud is not a private place). And the threshold sits below
the lowest of the three ceilings, because M-01 describes calls NEAR the ceiling
and a threshold on the ceiling itself would see none of them.

**What it does not prove.** Nothing about the number on the target hardware.
The instrumentation is built on the development machine; the figure comes from
the next box, and the wording of A3 says so itself.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

EXAPP_SERVICE = REPO_ROOT / "php" / "lib" / "Service" / "ExAppService.php"

# The logging threshold of plan 16-06 and the three ceilings it has to stay
# below. Named here rather than valued: a number copied into this file is a
# number that keeps being asserted after somebody moved it in the class.
THRESHOLD = "SLOW_CALL_LOG_MILLISECONDS"
CEILINGS = (
    "REQUEST_TIMEOUT_SECONDS",
    "PAGE_REQUEST_TIMEOUT_SECONDS",
    "ADMIN_REQUEST_TIMEOUT_SECONDS",
)

# What may never appear inside a statement that writes into the log. The first
# two are the parameters that carry what a user asked for and who asked, the
# other three are the field names such a value would most plausibly arrive
# under. Word bounded on purpose: the "Body" inside "$responseBody" is a length
# and not a content, and a gate that went red on it would be switched off.
FORBIDDEN = (
    r"\$body\b",
    r"\$userId\b",
    r"\bterm\b",
    r"\bquery\b",
    r"\bfilename\b",
)

# A float class constant of the PHP half, whatever its visibility.
_CONSTANT = r"const\s+{name}\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*;"


def read(path: Path) -> str:
    """The text of one file, or an empty string when it is not there.

    The empty string makes every case below red, which is the fail closed
    direction: a gate whose file moved has to say so rather than pass.
    """
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def php_float(source: str, name: str) -> float | None:
    """The value of a PHP class constant, or None when the source has none.

    None rather than a zero: a constant that could not be read at all and one
    that is zero are different findings, and a zero would compare like a number
    while meaning that nothing was found.
    """
    found = re.search(_CONSTANT.format(name=name), source)

    return None if found is None else float(found.group(1))


def lines_of_the_call_method(source: str) -> list[str]:
    """The body of ``private function call``, line by line.

    The whole file would be the wrong scope for the first two cases: the admin
    path has a transport call of its own, and it would supply a second
    ``proxyRequest`` that has nothing to do with the ceiling of the search.
    """
    lines = source.splitlines()
    starts = [index for index, line in enumerate(lines) if line.lstrip().startswith("private function call(")]
    if len(starts) != 1:
        return []

    body: list[str] = []
    for line in lines[starts[0] + 1 :]:
        if line.rstrip() == "\t}":
            return body
        body.append(line)

    return body


def log_statements(source: str) -> list[str]:
    """Every statement that writes into the log, each one whole.

    Whole rather than line by line, and that is the difference between a gate
    and a gesture: the fields of a warning stand on the lines BELOW the one
    that names the logger, so a scan over single lines would read the message
    and miss everything that travels with it.
    """
    lines = source.splitlines()
    statements: list[str] = []
    index = 0
    while index < len(lines):
        if "logger->" in lines[index]:
            collected = [lines[index]]
            while not collected[-1].rstrip().endswith(");") and index + 1 < len(lines):
                index += 1
                collected.append(lines[index])
            statements.append("\n".join(collected))
        index += 1

    return statements


def user_content_in(source: str) -> list[str]:
    """Every log statement of a source that carries something a user supplied.

    One finding per statement and pattern, with the statement quoted, because a
    finding that only says "user content found" sends the reader through a
    thousand lines looking for it.
    """
    findings: list[str] = []
    for statement in log_statements(source):
        findings.extend(
            f"{pattern} stands in this log statement: {statement.strip()}"
            for pattern in FORBIDDEN
            if re.search(pattern, statement)
        )

    return findings


def test_the_measurement_wraps_the_proxy_call_and_nothing_else() -> None:
    """Threat T-16-22: the measurement stays around the one call it is about.

    Checked over the order of the lines and not over the mere presence of the
    two readings. A ``hrtime`` at the top of the method and one at the bottom
    would satisfy a presence check perfectly and would time the clamping, the
    four failure cases and the parser along with the call, which is the total
    duration under a new name.
    """
    body = lines_of_the_call_method(read(EXAPP_SERVICE))
    assert body != [], "the call method of ExAppService.php could not be read at all"

    readings = [index for index, line in enumerate(body) if "hrtime(" in line]
    assert len(readings) == 2, f"expected exactly two clock readings in call(), found {len(readings)}"

    first, second = readings
    between = [line.strip() for line in body[first + 1 : second] if line.strip() != ""]
    assert len(between) == 1, f"the two readings enclose more than the call itself: {between}"
    assert "proxyRequest(" in between[0], f"the two readings do not enclose the proxy call: {between[0]}"


def test_the_log_line_stands_behind_the_threshold() -> None:
    """Threat T-16-20: a line per keystroke is noise and not a measurement."""
    body = lines_of_the_call_method(read(EXAPP_SERVICE))
    assert body != [], "the call method of ExAppService.php could not be read at all"

    readings = [line for line in body if "hrtime(" in line]
    measured = re.match(r"\s*(\$[A-Za-z_][A-Za-z0-9_]*)\s*=", readings[-1])
    assert measured is not None, f"the measured duration is not assigned to a variable: {readings[-1]}"

    conditions = [index for index, line in enumerate(body) if THRESHOLD in line]
    assert len(conditions) == 1, f"expected exactly one use of {THRESHOLD} in call(), found {len(conditions)}"

    condition = body[conditions[0]]
    assert condition.lstrip().startswith("if ("), f"{THRESHOLD} is not used as a condition: {condition.strip()}"
    assert measured.group(1) in condition, (
        f"the condition does not compare the measured duration {measured.group(1)}: {condition.strip()}"
    )

    following = [line.strip() for line in body[conditions[0] + 1 :] if line.strip() != ""]
    assert following[0].startswith("$this->logger->info("), (
        f"the line behind the threshold is not the log line: {following[0]}"
    )


def test_no_log_statement_of_this_class_carries_user_content() -> None:
    """Threat T-16-21: the log of a Nextcloud is not a private place.

    The floor under the number of statements is the other half of the case. A
    scanner that found nothing to look at would report no findings at all and
    would be green for the worst of reasons.
    """
    source = read(EXAPP_SERVICE)
    statements = log_statements(source)
    assert len(statements) >= 10, f"only {len(statements)} log statements were found, so the scan read nothing"

    assert user_content_in(source) == []


def test_the_scan_for_user_content_goes_red_on_a_staged_line() -> None:
    """The proof that the case above can fail, staged and never read off disk.

    A mutation of the file itself would be exactly the change this gate exists
    to stop, so the sample lives here as a string: what is under test is the
    scanner, not the source.
    """
    staged = (
        "\t\t\t$this->logger->info('Findling: slow backend call', [\n"
        "\t\t\t\t'path' => $path,\n"
        "\t\t\t\t'term' => $body['query'],\n"
        "\t\t\t]);\n"
    )

    findings = user_content_in(staged)
    assert findings != [], "a log line carrying the search term was not reported"
    assert len(findings) == 3, f"expected three of the patterns of that line to be reported, got {findings}"

    innocent = (
        "\t\t\t$this->logger->warning('Findling: backend answer is not a bounded string body', [\n"
        "\t\t\t\t'path' => $path,\n"
        "\t\t\t\t'bytes' => is_string($responseBody) ? strlen($responseBody) : -1,\n"
        "\t\t\t]);\n"
    )
    assert user_content_in(innocent) == [], "the scan reports a length as if it were a content"


def test_the_threshold_is_declared_and_sits_below_every_ceiling() -> None:
    """M-01 describes calls NEAR the ceiling, so the threshold has to be under it."""
    source = read(EXAPP_SERVICE)

    threshold = php_float(source, THRESHOLD)
    assert threshold is not None, f"{THRESHOLD} could not be read at all"

    ceilings = {name: php_float(source, name) for name in CEILINGS}
    unreadable = sorted(name for name, value in ceilings.items() if value is None)
    assert unreadable == [], f"these ceilings could not be read at all: {unreadable}"

    lowest = min(value for value in ceilings.values() if value is not None) * 1000
    assert 0 < threshold < lowest, (
        f"{THRESHOLD} is {threshold} ms against a lowest ceiling of {lowest} ms, "
        "so the threshold would see none of the calls M-01 describes"
    )
