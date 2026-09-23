"""Derive the folded stop word supplement of the Snowball chains.

The tool answers one question per language: which folded forms of the built in
Snowball stop word list are not entries of that list themselves. That set is the
supplement the analysis chain of findling.index.analyzer needs, because the
chain folds before it filters and the built in lists compare exactly and carry
real accents. Without the supplement 77 Spanish, 10 Italian and 30 Portuguese
stop words reach the index as ordinary terms, in both spellings.

The folding is done by tantivy's own filter and never by a rebuilt one. A hand
written fold over unicodedata is close but not equal: tantivy folds the sharp s
into a double s and the Dutch n forms as well, so a rebuilt fold produces a
supplement that does not fit the chain it is meant to complete, and the symptom
is a stop word in the index rather than a failing test.

The digest is computed by the shipped folded_stopwords_hash, not by a second
hashlib call in here, so that the number the tool prints is by construction the
number the test holds.

Security rule, carried unchanged from T-02-14: this tool reads published
Snowball stop word lists out of the tantivy source of a pinned tag, and nothing
else. It never reads state.db, never an index and never a user file, so nothing
it prints can be user content. What it prints are counts, a digest, and what it
writes is a published word list.

Expected from the phase research, tag 0.26.2, measured on 2026-09-23:
  spanish_supplement=77  italian_supplement=10  dutch_supplement=0
  portuguese_supplement=30  english_supplement=0  supplement_total=117
A deviation is a finding for the measurement report, not a reason to edit a
file by hand.

Usage: stopword_supplement.py [--tag TAG] [--source PATH] OUTPUT

OUTPUT receives the ready made Python literal block for FOLDED_STOPWORDS.
--source names a local copy of stopwords.rs and expects mod.rs next to it, which
is how the tool runs without a network. Without --source both files are fetched
from the pinned tag of quickwit-oss/tantivy.

TAG has to read like 0.26.2 and is checked against that form before it reaches
the URL. Without the check a value carrying path segments walks out of the
pinned repository, because httpx normalises the segments away before the request
leaves and the output still reports the string the caller wrote. The tag is not
the anchor of the loaded bytes either way: a git tag can be moved, and what
holds the result is the digest of the DERIVED list,
``FOLDED_SUPPLEMENT_SHA256`` in backend/tests/test_language_analyzers.py.
"""

import re
import sys
from collections.abc import Sequence
from pathlib import Path

import httpx
from tantivy import Filter, TextAnalyzerBuilder, Tokenizer

from findling.index.stopwords import folded_stopwords_hash

ENCODING = "utf-8"

# The tag the product measured against. It is a whole argument value and not a
# bare number so that a grep for the pin finds the line that really uses it.
DEFAULT_TAG = "0.26.2"

# The only shape a tag may have before it is formatted into RAW_URL. Three
# number groups and nothing else: no slash, no dot segment, no query. tantivy
# tags read exactly like this, so the form costs nothing, and it is the one
# thing between --tag and a download out of a foreign repository.
TAG_FORM = re.compile(r"\A[0-9]+\.[0-9]+\.[0-9]+\Z")

RAW_URL = "https://raw.githubusercontent.com/quickwit-oss/tantivy/{tag}/src/tokenizer/stop_word_filter/{name}"

STOPWORDS_FILE = "stopwords.rs"
MOD_FILE = "mod.rs"

TIMEOUT_SECONDS = 30.0

# Output order of the mapping. English first because it is the language the
# shipped chain already had, the other four in the order the phase measured them.
LANGUAGES = ("english", "spanish", "italian", "dutch", "portuguese")

# The English list is not a const in stopwords.rs. It stands inline in the match
# arm of mod.rs, copied there from Lucene, so it needs its own reader.
ENGLISH_MARKER = "Language::English => {"

TAG = "--tag"
SOURCE = "--source"

USAGE = "stopword_supplement: usage: stopword_supplement.py [--tag TAG] [--source PATH] OUTPUT"

# One folder for the whole run. Building it per word would be correct and slow,
# and the object is stateless.
_ASCII_FOLDER = TextAnalyzerBuilder(Tokenizer.raw()).filter(Filter.ascii_fold()).build()


def fold(word: str) -> str:
    """Fold exactly the way the analysis chain folds, by running tantivy's filter.

    The raw tokenizer is the point: it hands the whole entry to the filter as one
    token, so a multi word entry cannot be split into pieces on the way.
    """
    tokens = _ASCII_FOLDER.analyze(word)
    return tokens[0] if tokens else ""


def _array_after(text: str, start: int) -> list[str]:
    """Return the string literals of the first Rust slice at or after ``start``.

    The closing bracket is found by counting depth and not by the first ``]``,
    because the declaration of a const list reads ``&[&str] = &[`` and the type
    would otherwise end the value before it began. Only word literals stand
    inside these slices, so no bracket ever hides in a string.
    """
    body_start = text.find("&[", start)
    if body_start < 0:
        return []
    depth = 0
    body_end = body_start
    for offset, character in enumerate(text[body_start:], start=body_start):
        if character == "[":
            depth += 1
        elif character == "]":
            depth -= 1
            if depth == 0:
                body_end = offset
                break
    chunks = text[body_start + len("&[") : body_end].split(",")
    return [word for word in (chunk.strip().strip('"') for chunk in chunks) if word]


def parse_stopwords(text: str) -> dict[str, list[str]]:
    """Return {language: [word, ...]} for every const list of stopwords.rs.

    Takes the source text and not a path, because the same parser serves the
    downloaded copy and the one named with --source, and a tool that writes a
    download to disk only to read it back has invented a cache.
    """
    out: dict[str, list[str]] = {}
    marker = "pub const "
    pos = 0
    while True:
        start = text.find(marker, pos)
        if start < 0:
            return out
        name_end = text.find(":", start)
        name = text[start + len(marker) : name_end].strip()
        # From the assignment on, not from the colon: between the two stands the
        # type &[&str], which is a slice the reader must not mistake for a value.
        words = _array_after(text, text.find("=", name_end))
        out[name.lower()] = words
        pos = name_end + 1


def parse_english(text: str) -> list[str]:
    """Return the inline English list out of the match arm of mod.rs."""
    start = text.find(ENGLISH_MARKER)
    if start < 0:
        return []
    return _array_after(text, start)


def folded_supplement(words: Sequence[str]) -> list[str]:
    """Return the folded forms the built in list does not already carry.

    First appearance order, not sorted: the generator is the only producer of
    this list, and a stable order that is not alphabetical is the cheapest proof
    that nobody reordered it by hand.
    """
    have = set(words)
    extra: list[str] = []
    for word in words:
        candidate = fold(word)
        if candidate and candidate != word and candidate not in have and candidate not in extra:
            extra.append(candidate)
    return extra


def _download(tag: str, name: str) -> str:
    """Return one file of the pinned tag, or raise httpx.HTTPError."""
    response = httpx.get(RAW_URL.format(tag=tag, name=name), timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.text


def _sources(tag: str, source: Path | None) -> tuple[str, str] | None:
    """Return the text of stopwords.rs and of mod.rs, or None on failure."""
    if source is not None:
        sibling = source.parent / MOD_FILE
        if not source.is_file() or not sibling.is_file():
            print(
                f"stopword_supplement: {source} and {sibling} have to exist side by side",
                file=sys.stderr,
            )
            return None
        return source.read_text(encoding=ENCODING), sibling.read_text(encoding=ENCODING)
    try:
        return _download(tag, STOPWORDS_FILE), _download(tag, MOD_FILE)
    except httpx.HTTPError as error:
        print(
            f"stopword_supplement: cannot reach the pinned tag {tag}: {error.__class__.__name__}",
            file=sys.stderr,
        )
        print(
            f"stopword_supplement: pass {SOURCE} with a local copy of {STOPWORDS_FILE}, "
            f"with {MOD_FILE} next to it, to run without a network",
            file=sys.stderr,
        )
        return None


def _literal_block(supplement: dict[str, list[str]]) -> str:
    """Return the FOLDED_STOPWORDS literal, one entry per line."""
    lines = ["FOLDED_STOPWORDS: Final[dict[str, tuple[str, ...]]] = {"]
    for language in LANGUAGES:
        entries = supplement[language]
        if not entries:
            lines.append(f'    "{language}": (),')
            continue
        lines.append(f'    "{language}": (')
        lines.extend(f'        "{entry}",' for entry in entries)
        lines.append("    ),")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _numbers(tag: str, builtin: dict[str, list[str]], supplement: dict[str, list[str]], digest: str) -> str:
    """Return the key figures of the run. Counts and a digest, nothing else."""
    figures: list[tuple[str, object]] = [("tag", tag)]
    for language in ("spanish", "italian", "dutch", "portuguese", "english"):
        figures.append((f"{language}_builtin", len(builtin[language])))
        figures.append((f"{language}_supplement", len(supplement[language])))
    figures.append(("supplement_total", sum(len(entries) for entries in supplement.values())))
    figures.append(("supplement_hash", digest))
    return "\n".join(f"{name}={value}" for name, value in figures) + "\n"


def _split_arguments(argv: Sequence[str]) -> tuple[str, Path | None, Path] | None:
    """Return the tag, the optional local source and the output path.

    The tag is held against TAG_FORM here and not at the download, because here
    is the only place it enters the program: a value that never becomes a tag
    can never become a path segment of RAW_URL either.
    """
    rest = list(argv)
    tag = DEFAULT_TAG
    source: Path | None = None
    while rest and rest[0] in (TAG, SOURCE):
        if len(rest) < 2:
            return None
        if rest[0] == TAG:
            if not TAG_FORM.fullmatch(rest[1]):
                print(
                    f"stopword_supplement: {rest[1]} is no tag form like {DEFAULT_TAG}",
                    file=sys.stderr,
                )
                return None
            tag = rest[1]
        else:
            source = Path(rest[1])
        rest = rest[2:]
    if len(rest) != 1:
        return None
    return tag, source, Path(rest[0])


def main(argv: Sequence[str]) -> int:
    """Write the literal block and print the counts of the run."""
    parsed = _split_arguments(argv)
    if parsed is None:
        print(USAGE, file=sys.stderr)
        return 2

    tag, source, output = parsed
    texts = _sources(tag, source)
    if texts is None:
        return 1

    stopwords_text, mod_text = texts
    builtin = parse_stopwords(stopwords_text)
    builtin["english"] = parse_english(mod_text)

    missing = [language for language in LANGUAGES if not builtin.get(language)]
    if missing:
        print(f"stopword_supplement: the source carries no list for: {', '.join(missing)}", file=sys.stderr)
        return 1

    supplement = {language: folded_supplement(builtin[language]) for language in LANGUAGES}
    flat = [word for language in sorted(supplement) for word in supplement[language]]
    digest = folded_stopwords_hash(flat)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_literal_block(supplement), encoding=ENCODING)

    print(_numbers(tag, builtin, supplement, digest), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
