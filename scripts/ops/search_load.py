#!/usr/bin/env python3
"""Concurrent search load over the route a user takes, with the memory beside it.

Two questions, and they are not the same one asked twice.

The first: does the search stay usable while several people search at once and
the embedding track fills behind them? The clock to hold the answer against is
the one Provider.php carries, BUDGET_NANOSECONDS = 2_500_000_000, and the number
worth comparing is the p95 of a real search over the OCS route rather than a call
into the container.

The second: what does the vector scan do to the cgroup that anon alone does not
show? A brute force scan pulls the vector stock into the file cache of the same
cgroup. memory.current counts that, anon does not, and a store claim taken from
anon alone is the cheaper half of the truth. Both are read here, before, during
and after the load.

**What this tool undertakes: nothing.** It does not name a concurrency level that
the product promises. Which number is a sensible promise is measured first and
written down afterwards, in plan 06.1-18 and in the report that comes out of it.
A figure decided before the measurement would be exactly the sort of figure this
project refuses everywhere else.

**The measurement happened, on 07.09.2026, and here is what it says.** Ten rounds
per level over the OCS route on the arm box of this phase (m7g.large, 2 vCPU
Graviton3, 4 GB, All-in-One, 51.961 documents, 145.854 chunks), 410 requests in
all, not one of them failed:

    conc   requests   p50        p95          budget 2500 ms
       1         10   376.4 ms     481.6 ms   held
       4         40   885.1 ms   1,009.4 ms   held
       8         80   1,792.9 ms  1,915.0 ms  held
      12        120   2,724.0 ms  3,045.4 ms  broken
      16        160   3,476.0 ms  3,782.7 ms  broken

So the promise is **eight concurrent searches**: the highest level whose p95 stays
under the budget, at 76.6 percent of it, with oom, oom_kill and oom_group_kill all
still at zero. The series is in
docs/measurements/2026-09-nachmessung-m7g/ and the promise is written down in
docs/performance.md, section "Die Nachmessung".

That promise is still a promise about one box and one instance, for the reason in
the paragraph below, and this module header is not the place it is enforced: this
tool takes the concurrency as an argument and measures whatever it is handed.

**And what a run of it does not prove.** A number taken on a CI instance with the
PHP development server says nothing about a production instance. The unified
search asks every provider at once and waits for all of them, so the PHP process
pool of the instance sets the ceiling just as much as this app does, and that
pool is a different size in every deployment. A number taken here is a number
about this machine and this instance.

**What "failures" counted until 10.09.2026, and why the figure was wrong.** A
failure was a transport error or a body that is not the shape of an OCS answer,
and nothing else. An aborted container call is neither of those: the OCS route
answers it with HTTP 200 and a result group without a container part, so entries
is the empty list, the request counts as answered, and its measured duration is
the duration of an answer that carries nothing. The Nextcloud log of 10.09.2026
holds 17 aborted calls with cURL error 28 in the window of level 16 of the
concurrency series, while
docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/97-stufe-16.json reports
"failures": 0 over 160 requests. The only trace in the report was in the hits,
4.16 per request against 5.40 at level 1, and that quotient had to be worked out
by hand. It is written up as DI-10-01 in section 9.3 of
docs/measurements/2026-09-vergleichsmessung-m7g/README.md.

Since then a result group with fewer entries than --min-hits is a failure under
a name of its own, EmptyResultGroup, and hits_per_request stands in the report
next to hits_total. --min-hits 0 restores the reading from before that date, for
an instance whose stock does not carry the ten fixed TERMS, and the value it ran
with stands in the report as min_hits, so a raw file carries its own reading
without the command line that produced it.

**Where it comes from.** The sequential sample 45-suchlast.py of the semantic run
of 05.09.2026 asked the same questions and read the same two memory figures. What
it could not do is run several searches at the same time, and it reached its
helper module through an entry pushed into sys.path, which made it a tool for one
box. This one takes the questions and the output and leaves the box behind: the
address, the account and the container are arguments, and nothing outside the
standard library is imported. A third load test tool would be a foreign body for
one loop, with an installation of its own in an environment that is supposed to
work offline.

**What a term without stock is called since 21.09.2026 (DI-11-03).**
EmptyResultGroup counted an aborted container call and a search that found
nothing under one name, and the tool cannot tell the two apart from where it
stands: the OCS route answers both with HTTP 200 and a result group without a
container part, and the difference is in the Nextcloud log on the other side. A
second failure name taken off that answer would be a name without a
distinguishing mark. So the question is asked before the run instead of after
it. A pre-run probe asks the index in the process of the container, over
ranked_sides, how much stock each of the ten terms has, and a term the index
holds nothing for is called ohne-treffer rather than fehlschlag for the rest of
the run. The probe writes one line per term into the head of the raw file,
before the measured figures. If it does not answer, the run goes ahead and the
raw file says vorlaufsonde: nicht verfuegbar, and the separation stays undone
where a reader sees it: a silent return to the old counting is the finding of
DI-11-03 itself.

Usage:

    export FINDLING_LOAD_PASSWORD='...'
    ./search_load.py --base-url http://localhost:8080 --user alice \\
        --concurrency 10 --rounds 3 --container nc_app_findling_backend
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

# The route a user takes. Everything a search costs on a small box that is not
# the engine sits behind this path: the process pool of the instance, the
# permission recheck of every candidate and the second call for the excerpt.
OCS_ROUTE: Final = "/ocs/v2.php/search/providers/findling/search"

# The wall clock one result group is budgeted, mirrored from
# Provider::BUDGET_NANOSECONDS. It is reported next to the measured figures and
# nothing here fails because of it: a slow answer is a finding for a report, not
# an exit code of a measuring tool.
BUDGET_MS: Final = 2500

# The name of the environment variable the password is read from, unless the
# caller names another one. It is never an argument: an argument stands in the
# process list of the machine and in the shell history of whoever typed it.
DEFAULT_PASSWORD_ENV: Final = "FINDLING_LOAD_PASSWORD"  # noqa: S105 - a variable name, not a value

# Where the cgroup of a container sits depends on the cgroup driver of the
# daemon and both forms exist in the field: the systemd driver, which is the
# default on Ubuntu, and cgroupfs. The root is overridable for a run that looks
# at a copy of the files.
CGROUP_ROOT_ENV: Final = "FINDLING_CGROUP_ROOT"
DEFAULT_CGROUP_ROOT: Final = "/sys/fs/cgroup"

# Paraphrases and plain terms mixed, so that the semantic half of the search
# takes part in the load. A list of lexical terms alone would measure the full
# text index and report it as the cost of a search.
#
# ASCII only, as every identifier and literal in this repository is: a term with
# an umlaut in it would make this a question about the query side umlaut variant
# instead of about the load.
TERMS: Final = (
    "Vertrag beenden",
    "Kuendigung",
    "Widerspruch einlegen",
    "Bescheid",
    "Rechnung bezahlen",
    "Mahnung",
    "Termin absagen",
    "Mitteilung",
    "Antrag stellen",
    "Beschluss",
)

# Ceiling per request. Well above the budget of a result group, because the point
# of this tool is to see a slow answer and to time it, not to cut it off and
# count it as a failure.
REQUEST_TIMEOUT_SECONDS: Final = 30.0

# The name of the failure that carries both causes, as a constant rather than as
# a literal in two places: since the probe exists the report splits it, and a
# name spelled out twice is a name that gets renamed once.
EMPTY_RESULT_GROUP: Final = "EmptyResultGroup"

# Where the interpreter of the shipped image sits. backend/Dockerfile puts the
# environment under /app/.venv, and 98c-sprachfaelle.sh of the v1.2 run reaches
# the in-container probe by the same path. Overridable, so that this is a
# default and not a fixed assumption about an image.
PROBE_PYTHON_ENV: Final = "FINDLING_PROBE_PYTHON"
DEFAULT_PROBE_PYTHON: Final = "/app/.venv/bin/python"

# Ceiling for the whole probe. It reads an index that may be large, and it must
# not be able to hold up the run it stands in front of.
PROBE_TIMEOUT_SECONDS: Final = 120.0

# The line the raw file carries when the probe did not answer. Fail closed in
# the open: the run continues, and the two counters stay unsplit in writing.
PROBE_UNAVAILABLE: Final = "vorlaufsonde: nicht verfuegbar"

# The pre-run probe of DI-11-03, as a program for the interpreter of the
# container. It asks ranked_sides, the function a search of this container builds
# its two lists with, which is the same question 73-bestand-sonde.py of the v1.2
# run asks in the same place. Asked from out here the question has no answer, and
# that is the whole of DI-11-03; asked in the process before the load, it has one.
#
# Two limits, named here rather than discovered later. The probe asks the lexical
# half only and hands ranked_sides no semantic side, because a semantic side
# would load the query model and warm the very container whose memory is about to
# be read; the diagnosis route carries the same sentence one file over. A term
# without lexical stock can therefore still be answered by the vector half, and an
# empty answer for such a term is filed under ohne-treffer even where the call was
# aborted. And the figure leaves the container over the docker channel of the
# operator, the one 98c-sprachfaelle.sh uses, and never over a route a user can
# reach: a hit count on a user route would be the counting oracle of T-02-93.
PROBE_PROGRAM: Final = """
import sys

from findling.api.resources import read_side
from findling.index.search import ranked_sides
from findling.query.rewrite import build_query

side = read_side()
if side is None:
    raise SystemExit(2)
for term in sys.argv[1:]:
    rewritten = build_query(side.index, term, title_only=False)
    if rewritten.query is None:
        print("stock=0 window=0 term=%s" % term)
        continue
    # count is absent from the type stub of tantivy 0.26.0 and present at
    # runtime, the gap 73-bestand-sonde.py names. Neither ruff nor pyright reads
    # this string, so it is without consequence here as well.
    stock = side.index.searcher().search(rewritten.query, 1, count=True).count
    sides = ranked_sides(side.index, rewritten.query)
    print("stock=%d window=%d term=%s" % (stock, len(sides.lexical), term))
"""


@dataclass(frozen=True, slots=True)
class Sample:
    """One search: how long it took, how many hits, and how it failed if it did.

    The failure is a type name and never a message. A message from urllib can
    carry the address it was pointed at, and an operating tool whose output ends
    up in a log has no business repeating a URL that may hold a query.
    """

    term: str
    ms: float
    hits: int
    failure: str | None


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _authorization(user: str, password_env: str) -> str:
    """The basic auth header, built in the one place the credential exists.

    It is read here and turned into a header here, so there is exactly one
    function in this file in which the value appears at all, and no output of
    this tool can reach it (T-05-17). A missing value is a refusal and never an
    anonymous run: an unauthenticated search answers with a 401 for every request
    and the report would be a page of failures with no cause named.
    """
    secret = os.environ.get(password_env, "")
    if not secret:
        raise SystemExit(f"search_load: {password_env} is empty or not set")
    return "Basic " + base64.b64encode(f"{user}:{secret}".encode()).decode("ascii")


def _search_url(base_url: str, term: str, limit: int) -> str:
    """The OCS route with the term and an explicit limit.

    The limit travels rather than being left to the default of the caller,
    because the number of hits decides how many nodes the provider resolves and
    how many excerpts the second call asks for. A load figure without it would be
    a figure about a limit nobody wrote down.
    """
    query = urllib.parse.urlencode({"term": term, "limit": str(limit)})
    return f"{base_url.rstrip('/')}{OCS_ROUTE}?{query}"


def _one_search(url: str, authorization: str, min_hits: int) -> tuple[float, int, str | None]:
    """One request: milliseconds, hits, and the type name of a failure.

    A monotonic clock, because a wall clock adjustment during a load run would
    either double a duration or make it negative. The duration is measured around
    the whole call including a failure, so a failed request still contributes its
    time to the log even though it stays out of the percentiles.

    ``min_hits`` decides where a search that found nothing ends and a request
    that failed begins. It is handed in rather than read from a constant so
    that the value has exactly one way through this file: the command line, the
    report and this comparison.
    """
    request = urllib.request.Request(  # noqa: S310 - the scheme is checked in _checked_base_url
        url,
        headers={
            "Authorization": authorization,
            "OCS-APIRequest": "true",
            "Accept": "application/json",
        },
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as answer:  # noqa: S310
            payload = json.loads(answer.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError) as error:
        return ((time.perf_counter() - started) * 1000, 0, type(error).__name__)
    elapsed_ms = (time.perf_counter() - started) * 1000

    entries = payload.get("ocs", {}).get("data", {}).get("entries")
    if not isinstance(entries, list):
        # A 200 whose body is not the shape of an OCS answer is a failure of the
        # request and not a search that found nothing. Counting it as zero hits
        # would hide a broken route behind an empty result.
        return (elapsed_ms, 0, "MalformedAnswer")
    if len(entries) < min_hits:
        # The OCS route answers an aborted container call with HTTP 200 and a
        # result group without a container part, so this is where the loss of a
        # whole answer becomes visible at all: on 10.09.2026 the Nextcloud log
        # held 17 aborted calls of level 16 next to "failures": 0 in the report.
        return (elapsed_ms, len(entries), EMPTY_RESULT_GROUP)
    return (elapsed_ms, len(entries), None)


def _cgroup_of(container: str) -> Path:
    """The cgroup directory of one container, or a refusal that names the cause.

    The container id and nothing else is asked of the docker client, and that
    question doubles as the existence check. The memory figures come out of the
    files below, for the reason rss_sampler.sh states at length: the client
    reports memory.current, which counts the page cache of the mmap index, and a
    store claim built on it describes this app as worse than it is.
    """
    finished = subprocess.run(  # noqa: S603 - a fixed argument list, and nothing here goes through a shell
        ["docker", "inspect", "-f", "{{.Id}}", container],  # noqa: S607 - docker comes off the path by design
        capture_output=True,
        text=True,
        check=False,
    )
    container_id = finished.stdout.strip()
    if finished.returncode != 0 or not container_id:
        raise SystemExit(f"search_load: docker does not know a container called '{container}'")

    root = Path(os.environ.get(CGROUP_ROOT_ENV, DEFAULT_CGROUP_ROOT))
    for candidate in (root / f"system.slice/docker-{container_id}.scope", root / f"docker/{container_id}"):
        if (candidate / "memory.stat").is_file():
            return candidate
    raise SystemExit(
        f"search_load: no readable memory.stat for container '{container}'; "
        f"tried {root}/system.slice/docker-<id>.scope and {root}/docker/<id>"
    )


def _memory(cgroup: Path | None) -> dict[str, object]:
    """anon, file, slab and memory.current of the cgroup, in one grip.

    Both figures on purpose, and the distance between them is the point: anon is
    the heap, memory.current adds the page cache that a full vector scan pulls in,
    and a reader who only ever sees one of the two cannot tell a growing heap
    from a warming cache.

    A cgroup that was not named is a state and not an error: this tool is useful
    against an instance whose container is out of reach, it just cannot say
    anything about the memory then, and it says that rather than writing zeroes.
    """
    if cgroup is None:
        return {"at": _now(), "state": "not measured, no container was named"}

    values: dict[str, object] = {"at": _now()}
    try:
        lines = (cgroup / "memory.stat").read_text(encoding="utf-8").splitlines()
    except OSError:
        values["state"] = "memory.stat could not be read"
        return values
    for line in lines:
        name, _, raw = line.partition(" ")
        if name in {"anon", "file", "slab"}:
            values[name] = int(raw)
    # memory.peak arrived in kernel 5.19 and can be absent. It is not the figure
    # the store claim is made from, so a missing one is reported and does not end
    # the run.
    for name in ("memory.current", "memory.peak"):
        try:
            values[name] = int((cgroup / name).read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            values[name] = "na"
    return values


def _probe_lines(reason: str) -> list[str]:
    """The head of a raw file whose probe did not answer, and why it did not.

    The reason names a state of this tool and never the message of a library. A
    message can carry the address or the path it came from, which is the rule the
    failure names of Sample follow one dataclass up.
    """
    return [
        PROBE_UNAVAILABLE,
        f"grund: {reason}, {_now()}",
        "die trennung ohne-treffer gegen fehlschlag unterbleibt in diesem lauf",
    ]


def _probe(container: str | None) -> tuple[frozenset[str] | None, list[str]]:
    """The stock of every term of this run, read in the container before the load.

    Two things come back: the terms the index holds nothing for, and the lines
    that go into the head of the raw file. None instead of a set is the answer of
    a probe that did not run, and it is deliberately not the empty set: the empty
    set says every term has stock, which is a claim, and None says nobody asked.

    Nothing here ends the run. A load run without the probe is the run this tool
    made before 21.09.2026, and it is still a measurement; what it may not be is
    a measurement that looks like one with the probe (T-16-13).
    """
    if container is None:
        return (None, _probe_lines("no container was named, so the probe had nowhere to run"))

    interpreter = os.environ.get(PROBE_PYTHON_ENV, DEFAULT_PROBE_PYTHON)
    try:
        finished = subprocess.run(  # noqa: S603 - a fixed argument list, and nothing here goes through a shell
            ["docker", "exec", container, interpreter, "-c", PROBE_PROGRAM, *TERMS],  # noqa: S607 - docker comes off the path by design
            capture_output=True,
            text=True,
            check=False,
            timeout=PROBE_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return (None, _probe_lines(f"the probe could not be run, {type(error).__name__}"))
    if finished.returncode != 0:
        # The return code and never the error output of the container: that
        # stream carries paths of the machine and, on a bad day, a line of a
        # configuration. The code says enough to go and look, which is its job.
        return (None, _probe_lines(f"the probe in the container ended with return code {finished.returncode}"))

    measured: dict[str, tuple[int, int]] = {}
    for line in finished.stdout.splitlines():
        head, _, term = line.partition(" term=")
        if not term or not head.startswith("stock="):
            continue
        fields: dict[str, str] = {}
        for piece in head.split(" "):
            name, _, raw = piece.partition("=")
            fields[name] = raw
        try:
            measured[term] = (int(fields["stock"]), int(fields["window"]))
        except (KeyError, ValueError):
            return (None, _probe_lines("a line of the probe could not be read"))
    if set(measured) != set(TERMS):
        # A partial answer is no answer. Splitting the counters on some of the
        # terms would put two readings into one raw file.
        return (None, _probe_lines(f"the probe answered for {len(measured)} of {len(TERMS)} terms"))

    without = sorted(term for term, (stock, window) in measured.items() if stock == 0 and window == 0)
    lines = [f"vorlaufsonde {_now()}, {len(TERMS)} begriffe im container gefragt"]
    if without:
        lines += [f"ohne treffer: {term}" for term in without]
    else:
        lines.append("ohne treffer: keiner der begriffe")
    lines += [f"bestand={stock} fenster={window} begriff={term}" for term, (stock, window) in measured.items()]
    return (frozenset(without), lines)


def _percentile(values: list[float], share: float) -> float:
    """Nearest rank on an ascending list, the reading the reference sample used.

    Named rather than inlined so that the p95 of this tool and the p95 of the
    measurement it grew out of are the same statement about the same data.
    """
    index = min(len(values) - 1, round(share * (len(values) - 1)))
    return values[index]


def _checked_base_url(raw: str) -> str:
    """The address, once, with its scheme checked before anything is opened."""
    parsed = urllib.parse.urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise argparse.ArgumentTypeError("the base url has to be an http or https address")
    return raw


def _positive(raw: str) -> int:
    number = int(raw)
    if number < 1:
        raise argparse.ArgumentTypeError("has to be at least one")
    return number


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="search_load.py",
        description=(
            "Drive concurrent searches over the ordinary OCS route and report p50, p95 and max "
            "next to the memory of the container cgroup. It measures and promises nothing: which "
            "concurrency is a sensible undertaking follows from the measurement of plan 06.1-18."
        ),
    )
    parser.add_argument(
        "--base-url",
        required=True,
        type=_checked_base_url,
        help="Address of the Nextcloud instance, for instance http://localhost:8080",
    )
    parser.add_argument("--user", required=True, help="Account the searches run as")
    parser.add_argument(
        "--password-env",
        default=DEFAULT_PASSWORD_ENV,
        help=(
            f"Name of the environment variable the password is read from (default {DEFAULT_PASSWORD_ENV}). "
            "The value is never an argument, because an argument stands in the process list."
        ),
    )
    parser.add_argument(
        "--concurrency",
        type=_positive,
        default=4,
        help="How many searches run at the same time. This is the whole subject of the tool.",
    )
    parser.add_argument(
        "--rounds",
        type=_positive,
        default=3,
        help="How many times that many searches are driven. Requests are concurrency times rounds.",
    )
    parser.add_argument(
        "--limit",
        type=_positive,
        default=5,
        help="Hits per search, handed to the route explicitly because it decides how much work a search is.",
    )
    parser.add_argument(
        "--min-hits",
        type=int,
        default=1,
        help=(
            "How many hits an answer has to carry to count as answered (default 1). Fewer than that is "
            "the failure EmptyResultGroup, because the OCS route answers an aborted container call with "
            "a status of 200 and a result group without a container part. --min-hits 0 restores the "
            "reading from before 10.09.2026, for an instance whose stock does not carry the ten fixed "
            "terms; anything below zero reads the same way, since no answer can have fewer hits than none."
        ),
    )
    parser.add_argument(
        "--container",
        default=None,
        help=(
            "Name or id of the backend container, for the memory readings and for the pre-run probe "
            "of DI-11-03. Without it both are left out and the raw file says so."
        ),
    )
    parser.add_argument(
        "--json",
        default=None,
        help="Write the full report to this file as well. It goes to standard output in any case.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = _parse(argv)
    authorization = _authorization(arguments.user, arguments.password_env)
    cgroup = _cgroup_of(arguments.container) if arguments.container else None

    # Before the first memory reading and before the first level, in that order.
    # The probe touches the lexical index itself, and a reading taken after it
    # would count that touch as a cost of the load (DI-11-03).
    stockless, probe_lines = _probe(arguments.container)

    before = _memory(cgroup)
    during: list[dict[str, object]] = []
    samples: list[Sample] = []

    # A thread pool out of the standard library, and the concurrency is the pool
    # size: every round hands it exactly that many searches, so that many are in
    # flight at once rather than that many being worked through in some order.
    with ThreadPoolExecutor(max_workers=arguments.concurrency) as pool:
        for round_number in range(arguments.rounds):
            first = round_number * arguments.concurrency
            terms = [TERMS[(first + slot) % len(TERMS)] for slot in range(arguments.concurrency)]
            futures = [
                pool.submit(
                    _one_search,
                    _search_url(arguments.base_url, term, arguments.limit),
                    authorization,
                    arguments.min_hits,
                )
                for term in terms
            ]
            for term, future in zip(terms, futures, strict=True):
                elapsed_ms, hits, failure = future.result()
                samples.append(Sample(term=term, ms=elapsed_ms, hits=hits, failure=failure))
            during.append(_memory(cgroup))

    after = _memory(cgroup)

    # The times of the successful requests only, and the failures counted apart
    # from them. A failed request that contributed its duration to the p95 would
    # move the figure by an amount nobody could read back out of it.
    times = sorted(sample.ms for sample in samples if sample.failure is None)
    failures: dict[str, int] = {}
    for sample in samples:
        if sample.failure is not None:
            failures[sample.failure] = failures.get(sample.failure, 0) + 1

    # Next to hits_total and never instead of it, because the sum and the
    # quotient answer different questions: the sum says how much was found, the
    # quotient is the fingerprint of an answer that arrived empty (DI-10-01).
    hits_total = sum(sample.hits for sample in samples)

    # DI-11-03: the answers below --min-hits, split by what the probe found. A
    # term the index holds nothing for was answered and not lost, and the two
    # were never the same event. The total stands beside the split, so a raw file
    # of this tool can still be read against one from before 21.09.2026, and the
    # split is absent by name where the probe did not answer.
    empty_total = failures.get(EMPTY_RESULT_GROUP, 0)
    empty_groups: dict[str, object] = {"gesamt": empty_total}
    if stockless is None:
        empty_groups["getrennt"] = "nein, " + PROBE_UNAVAILABLE
    else:
        without_stock = sum(
            1 for sample in samples if sample.failure == EMPTY_RESULT_GROUP and sample.term in stockless
        )
        empty_groups["ohne-treffer"] = without_stock
        empty_groups["fehlschlag"] = empty_total - without_stock

    report: dict[str, object] = {
        # First key, so the terms without stock stand in the head of the raw file
        # and in front of the measured figures.
        "vorlaufsonde": probe_lines,
        "started": before.get("at"),
        "target": arguments.base_url,
        "user": arguments.user,
        "concurrency": arguments.concurrency,
        "rounds": arguments.rounds,
        "limit": arguments.limit,
        "min_hits": arguments.min_hits,
        "requests": len(samples),
        "answered": len(times),
        "failures": sum(failures.values()),
        "failure_kinds": failures,
        "empty_result_groups": empty_groups,
        "hits_total": hits_total,
        "hits_per_request": round(hits_total / len(samples), 2) if samples else 0.0,
        "budget_ms": BUDGET_MS,
        "memory": {"before": before, "during": during, "after": after},
        "ended": _now(),
    }
    if times:
        report["p50_ms"] = round(statistics.median(times), 1)
        report["p95_ms"] = round(_percentile(times, 0.95), 1)
        report["max_ms"] = round(times[-1], 1)
        # Reported and never a verdict of this tool: see the module header on what
        # a number from one machine is worth.
        report["p95_within_budget"] = report["p95_ms"] < BUDGET_MS

    text = json.dumps(report, ensure_ascii=False, indent=1)
    print(text)
    if arguments.json:
        Path(arguments.json).write_text(text + "\n", encoding="utf-8")

    if not times:
        # The one failure this tool knows, and it is the rule the measuring steps
        # of resilience.yml carry: a bad number is a result, an absent one is a
        # broken run. Not one answered request means there is nothing to report.
        print("search_load: not one request was answered, so nothing was measured", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
