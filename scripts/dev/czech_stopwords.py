"""Derive the folded Czech stop word list of the cs chain from the Lucene original.

tantivy 0.26.2 carries neither a Czech Snowball stemmer nor a Czech stop word
list, so the cs chain of findling.index.analyzer filters through one custom
list, and this tool is the only producer of it. It reads the vendored Lucene
original, holds its bytes against the SHA-256 below, folds every entry with the
same chain the index runs in front of the stop word filter, keeps the order of
first appearance, drops the duplicates the fold creates, removes the named
exceptions and prints the result.

The fold is tantivy's own and never a rebuilt one over unicodedata: a rebuilt
fold is close but not equal, and the symptom of the difference is a stop word in
the index rather than a failing test (same rule as stopword_supplement.py).

Why exceptions exist at all. Lucene's CzechAnalyzer filters UNFOLDED, so the
list was never checked against what its entries become once the accents are
gone. Folding turns some stop words into a different, common content word: the
verb "to be" folds into "byt", which is "flat, apartment" and stands in every
lease; the relative pronoun "which" folds into "jez", which is "weir". Every
folded form that is no entry of the original was reviewed one by
one; the review table stands in the docstring of
backend/src/findling/index/stopwords_cs.py and in THIRD-PARTY.md, and
EXCEPTIONS below is exactly its set of exception rows.

Security rule, carried unchanged from T-02-14: this tool reads one published
word list out of the repository and nothing else. It never reads state.db,
never an index and never a user file, so nothing it prints can be user content.

Expected, measured on 2026-10-10 against releases/lucene/10.5.2:
  original_lines=172  original_unique=171  folded_unique=169
  new_forms=67  exceptions=2  shipped=167

Usage: czech_stopwords.py [--source PATH] [--output PATH]

Without --source the vendored copy under backend/tests/fixtures is read. With
--output the ready made Python literal blocks for CZECH_EXCEPTIONS and
CZECH_STOPWORDS_FOLDED are written there. The counts, the digest and the list of
new folded forms (form, TAB, original entry) go to stdout.
"""

import hashlib
import io
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from tantivy import Filter, TextAnalyzerBuilder, Tokenizer

from findling.index.stopwords import folded_stopwords_hash

ENCODING = "utf-8"

SOURCE_URL = (
    "https://raw.githubusercontent.com/apache/lucene/releases/lucene/10.5.2/"
    "lucene/analysis/common/src/resources/org/apache/lucene/analysis/cz/stopwords.txt"
)
SOURCE_TAG = "releases/lucene/10.5.2"
# Last commit that touched the file at that tag.
SOURCE_COMMIT = "e8e4245d9b36123446546ff15967ac95429ea2b0"
# SHA-256 of the bytes at SOURCE_URL, fetched on 2026-10-10. The vendored copy
# has to carry exactly these bytes; a deviation stops the run.
SOURCE_SHA256 = "61f06aa1e7567ee8c72e895ea33229033669ac1cc52c6d40369a9ee2b76ad915"

DEFAULT_SOURCE = (
    Path(__file__).resolve().parents[2] / "backend" / "tests" / "fixtures" / "lucene_cz_stopwords_10_5_2.txt"
)

# Folded forms removed from the shipped list, each with the reason it was
# removed. The single criterion: the folded form is at the same time a common
# Czech content word with a DIFFERENT meaning than the original entry, one that
# users really search without accents. A folded form that is only the flat
# spelling of the same word stays in the list.
EXCEPTIONS: dict[str, str] = {
    "byt": "fold of the verb b(y-acute)t, to be; byt is the noun flat/apartment, common in leases",
    "jez": "fold of the relative pronoun je(z-caron), which; jez is the noun weir, a plain content word",
}

SOURCE = "--source"
OUTPUT = "--output"

USAGE = "czech_stopwords: usage: czech_stopwords.py [--source PATH] [--output PATH]"

# One chain for the whole run: the tokenizer, lowercase and fold of the cs chain,
# in that order, without the stop word filter it is about to feed.
_FOLDER = TextAnalyzerBuilder(Tokenizer.simple()).filter(Filter.lowercase()).filter(Filter.ascii_fold()).build()


@dataclass(frozen=True)
class Derived:
    """Everything one run derives from the original."""

    entries: tuple[str, ...]
    folded: tuple[str, ...]
    new_forms: tuple[tuple[str, str], ...]
    shipped: tuple[str, ...]


def fold(word: str) -> str:
    """Fold one entry exactly the way the cs chain folds it.

    An entry has to come out as exactly one token. Lucene's list holds single
    words only, so anything else means the source is not the list it claims to
    be, and that is an error and not a guess.
    """
    tokens = _FOLDER.analyze(word)
    if len(tokens) != 1:
        raise ValueError(f"entry {word!r} folds into {len(tokens)} tokens, expected exactly one")
    return tokens[0]


def verify(data: bytes) -> bool:
    """Return True when the bytes are the pinned original."""
    return hashlib.sha256(data).hexdigest() == SOURCE_SHA256


def read_entries(data: bytes) -> tuple[str, ...]:
    """Return the non empty lines of the original, in file order."""
    return tuple(line.strip() for line in data.decode(ENCODING).splitlines() if line.strip())


def derive(entries: Sequence[str]) -> Derived:
    """Fold, deduplicate, list the new forms and remove the exceptions.

    First appearance order throughout, not sorted: a stable order that is not
    alphabetical is the cheapest proof that nobody reordered the list by hand.
    """
    originals = set(entries)
    folded: list[str] = []
    new_forms: list[tuple[str, str]] = []
    for entry in entries:
        form = fold(entry)
        if form in folded:
            continue
        folded.append(form)
        if form not in originals:
            new_forms.append((form, entry))
    shipped = tuple(form for form in folded if form not in EXCEPTIONS)
    return Derived(tuple(entries), tuple(folded), tuple(new_forms), shipped)


def build(source: Path) -> Derived | None:
    """Read and verify ``source`` and derive the list, or None on a bad source."""
    if not source.is_file():
        print(f"czech_stopwords: {source} does not exist", file=sys.stderr)
        return None
    data = source.read_bytes()
    if not verify(data):
        print(
            f"czech_stopwords: {source} is not the pinned original (SHA-256 {hashlib.sha256(data).hexdigest()}, "
            f"expected {SOURCE_SHA256})",
            file=sys.stderr,
        )
        return None
    derived = derive(read_entries(data))
    unknown = sorted(set(EXCEPTIONS) - {form for form, _ in derived.new_forms})
    if unknown:
        print(f"czech_stopwords: exceptions that are no new folded form: {', '.join(unknown)}", file=sys.stderr)
        return None
    return derived


def literal_block(derived: Derived) -> str:
    """Return the two literal blocks for stopwords_cs.py, one entry per line."""
    lines = ["CZECH_EXCEPTIONS: Final[tuple[str, ...]] = ("]
    lines.extend(f'    "{form}",' for form in EXCEPTIONS)
    lines.append(")")
    lines.append("")
    lines.append("CZECH_STOPWORDS_FOLDED: Final[tuple[str, ...]] = (")
    lines.extend(f'    "{form}",' for form in derived.shipped)
    lines.append(")")
    return "\n".join(lines) + "\n"


def report(derived: Derived) -> str:
    """Return counts, digest and the new folded forms. Published words only."""
    figures: list[tuple[str, object]] = [
        ("tag", SOURCE_TAG),
        ("original_lines", len(derived.entries)),
        ("original_unique", len(set(derived.entries))),
        ("folded_unique", len(derived.folded)),
        ("new_forms", len(derived.new_forms)),
        ("exceptions", len(EXCEPTIONS)),
        ("shipped", len(derived.shipped)),
        ("shipped_hash", folded_stopwords_hash(derived.shipped)),
    ]
    lines = [f"{name}={value}" for name, value in figures]
    lines.extend(f"new_form\t{form}\t{entry}" for form, entry in derived.new_forms)
    return "\n".join(lines) + "\n"


def _split_arguments(argv: Sequence[str]) -> tuple[Path, Path | None] | None:
    """Return the source and the optional output path."""
    rest = list(argv)
    source = DEFAULT_SOURCE
    output: Path | None = None
    while rest:
        if len(rest) < 2 or rest[0] not in (SOURCE, OUTPUT):
            return None
        if rest[0] == SOURCE:
            source = Path(rest[1])
        else:
            output = Path(rest[1])
        rest = rest[2:]
    return source, output


def main(argv: Sequence[str]) -> int:
    """Verify the original, derive the list, print the report."""
    parsed = _split_arguments(argv)
    if parsed is None:
        print(USAGE, file=sys.stderr)
        return 2
    source, output = parsed
    derived = build(source)
    if derived is None:
        return 1
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(literal_block(derived), encoding=ENCODING)
    # The new forms name their accented original; a console in a legacy code
    # page must not turn that into a crash.
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding=ENCODING)
    print(report(derived), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
