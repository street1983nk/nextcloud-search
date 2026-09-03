"""What the search costs while the index is being written.

The cheap half of this question is answered: a search against a resting index
costs 0.1 ms, the ACL prefilter for 400 candidates 0.18 ms, twenty snippets
4.2 ms. What nobody has measured is the same search during a batch commit,
and that is the number a user feels, because the indexer and the search share one
process and one file system. tantivy releases the GIL in add_document, commit and
search, so the two are not supposed to block each other; a commit is an fsync all
the same, and on a slow disk an fsync is exactly the moment the search bar hangs.

So this module measures instead of assuming. Two modes:

* ``idle``: N searches against a resting index.
* ``under-write``: the same N searches while documents are written in the
  background and batch commits go off, plus the number of commits that fell into
  the measurement window.

Both print the median and the p95, the document count and the size of the index
directory. The run with a throttled disk (docker run --device-write-bps) belongs
to the measurement job of plan 02-13 because it needs a container; this module is
the measuring point that job calls. If the number comes out badly there, the knob
is ``batch_max_bytes`` in :mod:`findling.config`, and the decision about it is
made and documented there rather than anticipated here.

Numbers only, never a token and never a word from a document: this path would see
user content in a production index, and a measurement that prints what it read is
the cheapest way to leak it (T-02-14). The text below is fixed and synthetic.

Run it with::

    uv run python -m findling.index.bench --mode idle --queries 200
    uv run python -m findling.index.bench --mode under-write --queries 200
"""

import argparse
import math
import statistics
import tempfile
import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from tantivy import Index

from findling.config import settings
from findling.index.open import open_index, open_reader
from findling.index.schema import FIELD_BODY_DE, FIELD_NAME, FIELD_TITLE
from findling.index.wordlist import FUGEN, SYSTEM_WORDLIST, load_constituents
from findling.index.writer import FLUSH_COMMITTED, IndexBatchWriter, IndexRecord

MODE_IDLE: Final = "idle"
MODE_UNDER_WRITE: Final = "under-write"

# How long to wait before repeating a commit that hit a transient IO error. See
# _commit below for the measurement behind it.
_COMMIT_RETRY_SECONDS: Final = 0.25

# Fixed synthetic German prose, written without umlauts the same way the analyzer
# measurement is, so that the workload is identical on every machine and reveals
# nothing about any real document.
_SENTENCES: Final = (
    "Die Kuendigungsfrist betraegt drei Monate und beginnt am Ersten des Monats.",
    "Die Rechnung wurde im Jahresabschluss der Verwaltung geprueft und freigegeben.",
    "Der Vertrag regelt die Betriebskosten, die Nebenkosten und die Kaution.",
    "Die Sitzungsvorlage des Ausschusses nennt den Haushalt und die Satzung.",
)

# Terms that occur in the text above, so every search collects real hits. A query
# without hits measures the parser and not the search.
_QUERIES: Final = ("vertrag", "rechnung", "monate", "satzung", "verwaltung", "haushalt")

# Enough entries to build a real automaton when the Debian list is absent, which
# is the case on every developer machine outside the container.
_SAMPLE_CONSTITUENTS: Final = (
    "abschluss",
    "aufgabe",
    "ausschuss",
    "betrieb",
    "frist",
    "grund",
    "haushalt",
    "jahre",
    "kaution",
    "kosten",
    "kuendigung",
    "monat",
    "neben",
    "rechnung",
    "satzung",
    "sitzung",
    "verkehr",
    "vertrag",
    "verwaltung",
    "vorlage",
)


@dataclass
class _WriteCounters:
    """What the background writer did inside the measurement window."""

    documents: int = 0
    commits: int = 0
    retries: int = 0
    # Only the fill sets this. It is the write side of the tool, next to the
    # search latency this module was built for, and it is the number a change to
    # the write path is measured against; without it a claim about the indexing
    # cost would have no artefact anywhere.
    seconds: float = 0.0
    states: list[str] = field(default_factory=list)


def _commit(writer: IndexBatchWriter, counters: _WriteCounters) -> None:
    """Commit the pending batch and survive one transient IO error.

    Measured on Windows 11 with tantivy 0.26.0: roughly every third run of a
    thousand documents, one commit fails with "An IO error occurred: 'Zugriff
    verweigert (os error 5)'" in the middle of a merge, and the very same commit
    succeeds a quarter of a second later. That is the well known difference
    between the two operating systems: POSIX unlinks a mapped file without
    complaint, Windows refuses while a handle is open. The app ships as a Linux
    container, so the retry lives here in the measuring tool rather than in
    :mod:`findling.index.writer`, where a swallowed IO error would hide a full
    volume. The number of retries is reported, so the artefact stays visible.
    """
    try:
        result = writer.flush()
    except ValueError as error:
        if "IO error" not in str(error):
            raise
        counters.retries += 1
        time.sleep(_COMMIT_RETRY_SECONDS)
        result = writer.flush()
    counters.states.append(result.state)
    if result.state == FLUSH_COMMITTED:
        counters.commits += 1


def batch_full(writer: IndexBatchWriter, *, files: int, max_bytes: int) -> bool:
    """True once the pending batch has reached one of the two caps.

    The rule lives here and not on the writer, because this module is its only
    caller. In production the batch boundary is the claim: the poller commits
    once per claimed batch and never asks a predicate, so the version of this
    that sat on IndexBatchWriter was dead code that vulture did not report at
    min-confidence 80 (phase 2 performance audit).

    Both caps travel as arguments rather than being read from
    :mod:`findling.config` inside, so that a loop over a thousand documents does
    not resolve the settings a thousand times and a test does not need the
    environment to state a cap.

    The byte cap is the one that matters in principle: thirty scanned PDFs are a
    different workload from thirty text files, and the memory the writer holds
    follows the text rather than the file count. In practice the file cap is
    reached first for every document this app accepts, and the arithmetic behind
    that stands at :attr:`IndexBatchWriter.pending_bytes`.
    """
    return writer.pending >= files or writer.pending_bytes >= max_bytes


def _percentile(samples: Sequence[float], fraction: float) -> float:
    """Nearest rank percentile, so a p95 over 200 samples is a real sample."""
    ordered = sorted(samples)
    rank = max(1, math.ceil(fraction * len(ordered)))
    return ordered[rank - 1]


def _constituents(source: Path) -> tuple[list[str], str]:
    """Return the constituent list and the name of where it came from.

    The word list decides how German text is split, not how fast a search is, so
    a miniature list is acceptable here. It is named in the output all the same:
    a measurement that hides which inputs it ran on invites the wrong comparison.
    """
    if source.exists():
        return load_constituents(source), str(source)
    return sorted({*_SAMPLE_CONSTITUENTS, *FUGEN}), "builtin-sample"


def _body(words: int) -> str:
    """Build one document body of roughly ``words`` words from the fixed text."""
    parts: list[str] = []
    length = 0
    while length < words:
        sentence = _SENTENCES[len(parts) % len(_SENTENCES)]
        parts.append(sentence)
        length += len(sentence.split())
    return " ".join(parts)


def _record(file_id: int, body: str) -> IndexRecord:
    return IndexRecord(
        file_id=file_id,
        storage_id=1,
        name=f"dokument-{file_id}.pdf",
        title="Vertrag und Rechnung",
        path=f"/bench/dokument-{file_id}.pdf",
        ext="pdf",
        body=body,
        mtime=1_700_000_000,
    )


def _fill(writer: IndexBatchWriter, documents: int, body: str) -> _WriteCounters:
    """Write the base index in batches, exactly the way the poller will."""
    resolved = settings()
    counters = _WriteCounters()
    started = time.perf_counter()
    for file_id in range(documents):
        writer.add(_record(file_id, body))
        counters.documents += 1
        if batch_full(writer, files=resolved.batch_files, max_bytes=resolved.batch_max_bytes):
            _commit(writer, counters)
    _commit(writer, counters)
    counters.seconds = time.perf_counter() - started
    return counters


def _search_once(index: Index, query_text: str) -> int:
    """One search the way the API path runs it: fresh searcher, parse, search."""
    searcher = index.searcher()
    query = index.parse_query(
        query_text,
        [FIELD_BODY_DE, FIELD_NAME, FIELD_TITLE],
        conjunction_by_default=True,
    )
    return len(searcher.search(query, 10).hits)


def _measure_searches(index: Index, queries: int, pace_seconds: float) -> tuple[list[float], int]:
    """Run the searches and return one duration in milliseconds per search.

    The pause between two searches is not measured, and it is the reason the
    number means anything: 200 searches back to back take six milliseconds in
    total and therefore fall between two commits, which measures nothing about
    the interference this module exists to find. Spread over a second they land
    on the fsyncs as well, and the p95 is then the answer to the real question.
    """
    durations: list[float] = []
    hits = 0
    for number in range(queries):
        query_text = _QUERIES[number % len(_QUERIES)]
        started = time.perf_counter()
        hits += _search_once(index, query_text)
        durations.append((time.perf_counter() - started) * 1000)
        if pace_seconds > 0:
            time.sleep(pace_seconds)
    return durations, hits


def _write_until(writer: IndexBatchWriter, stop: threading.Event, first_file_id: int, body: str) -> _WriteCounters:
    """Keep writing and committing until the search loop says stop."""
    resolved = settings()
    counters = _WriteCounters()
    file_id = first_file_id
    while not stop.is_set():
        writer.add(_record(file_id, body))
        counters.documents += 1
        file_id += 1
        if batch_full(writer, files=resolved.batch_files, max_bytes=resolved.batch_max_bytes):
            _commit(writer, counters)
    if writer.pending:
        _commit(writer, counters)
    return counters


def _directory_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def measure(
    directory: Path,
    *,
    mode: str,
    queries: int,
    documents: int,
    words: int,
    wordlist: Path,
    pace_seconds: float = 0.005,
) -> dict[str, float | int | str]:
    """Run one measurement and return its numbers."""
    constituents, source = _constituents(wordlist)
    index = open_index(directory, constituents)
    body = _body(words)

    writer = IndexBatchWriter(index, directory=directory)
    filling = _fill(writer, documents, body)
    open_reader(index)

    counters = _WriteCounters()
    started = time.perf_counter()
    if mode == MODE_UNDER_WRITE:
        stop = threading.Event()
        result: list[_WriteCounters] = []
        background = threading.Thread(
            target=lambda: result.append(_write_until(writer, stop, documents, body)),
            name="findling-bench-writer",
        )
        background.start()
        try:
            durations, hits = _measure_searches(index, queries, pace_seconds)
        finally:
            stop.set()
            background.join()
        counters = result[0]
    else:
        writer.close()
        durations, hits = _measure_searches(index, queries, pace_seconds)
    elapsed = time.perf_counter() - started
    # Idempotent: the idle branch closed the writer before it measured anything.
    writer.close()

    index.reload()
    report: dict[str, float | int | str] = {
        "mode": mode,
        "wordlist": source,
        "constituents": len(constituents),
        "documents_in_index": index.searcher().num_docs,
        "index_bytes": _directory_bytes(directory),
        "fill_seconds": round(filling.seconds, 3),
        "fill_documents": filling.documents,
        "queries": queries,
        "hits_total": hits,
        "median_ms": round(statistics.median(durations), 4),
        "p95_ms": round(_percentile(durations, 0.95), 4),
        "max_ms": round(max(durations), 4),
        "window_seconds": round(elapsed, 3),
        "commit_retries": filling.retries + counters.retries,
    }
    if mode == MODE_UNDER_WRITE:
        report["commits_in_window"] = counters.commits
        report["documents_written_in_window"] = counters.documents
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Measure the search latency of the Findling index.")
    parser.add_argument("--mode", choices=(MODE_IDLE, MODE_UNDER_WRITE), default=MODE_IDLE)
    parser.add_argument("--queries", type=int, default=200, help="searches in the measurement window")
    parser.add_argument("--docs", type=int, default=1000, help="documents written before measuring")
    parser.add_argument("--words", type=int, default=600, help="words per document")
    parser.add_argument("--index-dir", type=Path, default=None, help="reuse a directory instead of a temporary one")
    parser.add_argument("--wordlist", type=Path, default=SYSTEM_WORDLIST, help="constituent source")
    parser.add_argument("--pace-ms", type=float, default=5.0, help="unmeasured pause between two searches")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="findling-bench-", ignore_cleanup_errors=True) as scratch:
        directory = Path(scratch) / "index" if args.index_dir is None else args.index_dir
        report = measure(
            directory,
            mode=args.mode,
            queries=args.queries,
            documents=args.docs,
            words=args.words,
            wordlist=args.wordlist,
            pace_seconds=args.pace_ms / 1000,
        )
        for key, value in report.items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
