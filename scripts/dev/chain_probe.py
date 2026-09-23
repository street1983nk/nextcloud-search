"""Measure the position of ascii_fold in the four new analysis chains.

The probe answers three questions per language and it answers them over the form
families of ``backend/tests/fixtures/chain_cases_<code>.txt``: how many ordered
pairs of spellings find each other under each of the seven candidate chains, how
many built in stop words leak through each chain in either spelling, and whether
the winning candidate is token for token the chain the product ships.

Why this probe builds chains at all. The rule of this tree is that a measurement
calls the shipped factory, because a chain rebuilt in a probe measures the probe
and not the product (scripts/dev/compound_probe.py, ``_tokenise``). Six of the
seven candidates below do not exist in the product, so they have to be built
here. :func:`verify_against_product` closes that exception again: the winning
candidate is run against ``snowball_analyzer`` from the package for every form of
every family, and one differing form is exit code 1.

Security rule, carried unchanged from T-02-14: the probe reads the fixture files
of this repository and, with ``--stopwords``, one published Snowball stop word
list. It never reads state.db, never an index and never a user file, so nothing
it prints can be user content. The words it prints are the cases of this
repository and the entries of a published stop word list.

Run it through scripts/dev/measure_chains.sh. Unlike the German splitter this
measurement needs no container: all four stop word lists and all four stemmers
are compiled into tantivy.

Usage: chain_probe.py [--stopwords PATH] FIXTURE_DIR OUTPUT_DIR
"""

import sys
from collections.abc import Sequence
from pathlib import Path

from tantivy import Filter, TextAnalyzer, TextAnalyzerBuilder, Tokenizer

from findling.index.analyzer import snowball_analyzer
from findling.index.stopwords import FOLDED_STOPWORDS, folded_stopwords_hash

ENCODING = "utf-8"

# The same cap the shipped chains use. Spelled out rather than imported so that
# a candidate chain stays a candidate: this file may not start to depend on the
# product for the six recipes the product does not have.
MAX_TOKEN_CHARS = 48

# The Snowball names, and the two letter codes the fixtures and the key figures
# use. The product speaks Snowball names, the phase documents speak codes.
LANGUAGES = ("spanish", "italian", "dutch", "portuguese")
CODE = {"spanish": "es", "italian": "it", "dutch": "nl", "portuguese": "pt"}

# The seven candidates of the phase research, in the order they are reported.
# The letter names the fold position, the plus names the folded supplement.
RECIPES = ("A", "Aplus", "B", "Bplus", "C", "Cplus", "Dplus")

# The candidate the product ships. It is the one :func:`verify_against_product`
# holds against the package, and the one the loss table is written for.
WINNER = "Aplus"

FAMILIES_FILE = "familien.tsv"
NUMBERS_FILE = "kennzahlen.txt"
LOSSES_FILE = "verluste.tsv"

FAMILIES_HEADER = ("language", "lemma", "form", "recipe", "tokens")
LOSSES_HEADER = ("language", "lemma", "left", "right", "left_tokens", "right_tokens")

FIXTURE_NAME = "chain_cases_{code}.txt"

STOPWORDS = "--stopwords"

USAGE = "chain_probe: usage: chain_probe.py [--stopwords PATH] FIXTURE_DIR OUTPUT_DIR"

# One row of familien.tsv and one of verluste.tsv. Named because the tuples are
# wide enough that a repeated annotation would be the longest line of the file.
FormRow = tuple[str, str, str, str, Sequence[str]]
LossRow = tuple[str, str, str, str, Sequence[str], Sequence[str]]

# One folder for the whole run, built from the raw tokenizer so that an entry is
# handed to the filter in one piece. Stateless, so one object is enough.
_ASCII_FOLDER = TextAnalyzerBuilder(Tokenizer.raw()).filter(Filter.ascii_fold()).build()


def read_families(path: Path) -> list[list[str]]:
    """Return the form families of one fixture, one list of forms per line.

    Line by line, everything from ``#`` on is a comment, the rest is split on
    whitespace, empty lines are skipped. This is the only place in the tree that
    lays out the new fixture format, and the test of plan 17-06 imports it from
    here instead of rebuilding it, because a second reader is a second format.

    It lives next to the probe and not in the package because ``scripts/`` is no
    package (docs/testing.md), so the import can only ever run in this direction:
    a test may load this file, this file may not be loaded by the product.
    """
    families: list[list[str]] = []
    for line in path.read_text(encoding=ENCODING).splitlines():
        forms = line.split("#", 1)[0].split()
        if forms:
            families.append(forms)
    return families


def read_builtin(path: Path) -> dict[str, list[str]]:
    """Return {language: [word, ...]} from a stop word source the caller names.

    Two shapes are accepted, because the same measurement runs in two places. A
    ``stopwords.rs`` of the pinned tantivy tag is what the fixture was generated
    from, and the generated fixture ``snowball_stopwords_<tag>.txt`` with its
    ``language<TAB>word`` lines is what an offline run reads. The Rust half is
    deliberately a second, small reader rather than an import of
    scripts/dev/stopword_supplement.py: ``scripts/`` is no package, so an import
    between two of its files would only work when the interpreter happens to
    have started in this directory.
    """
    text = path.read_text(encoding=ENCODING)
    if "pub const " in text:
        return _parse_rust(text)
    out: dict[str, list[str]] = {}
    for line in text.splitlines():
        if line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) == 2 and fields[1]:
            out.setdefault(fields[0], []).append(fields[1])
    return out


def _parse_rust(text: str) -> dict[str, list[str]]:
    """Return the const stop word slices of tantivy's stopwords.rs."""
    out: dict[str, list[str]] = {}
    marker = "pub const "
    pos = 0
    while True:
        start = text.find(marker, pos)
        if start < 0:
            return out
        name_end = text.find(":", start)
        name = text[start + len(marker) : name_end].strip()
        out[name.lower()] = _slice_after(text, text.find("=", name_end))
        pos = name_end + 1


def _slice_after(text: str, start: int) -> list[str]:
    """Return the string literals of the first Rust slice at or after ``start``.

    The end is found by counting bracket depth and not by the first ``]``, so
    that the type ``&[&str]`` of a declaration cannot end the value before it
    began. Only word literals stand inside these slices.
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


def fold(word: str) -> str:
    """Fold exactly the way the chains fold, by running tantivy's own filter."""
    tokens = _ASCII_FOLDER.analyze(word)
    return tokens[0] if tokens else ""


def chain(language: str, recipe: str, supplement: Sequence[str]) -> TextAnalyzer:
    """Build one candidate chain. The recipe names the fold position.

    A, Aplus and Dplus fold in front of the stop word filter, B and Bplus behind
    it and in front of the stemmer, C, Cplus and Dplus behind the stemmer. Every
    recipe with a plus carries the folded supplement as a custom stop word
    filter. Dplus folds twice and exists as a control.
    """
    builder = TextAnalyzerBuilder(Tokenizer.simple()).filter(Filter.lowercase())
    if recipe in ("A", "Aplus", "Dplus"):
        builder = builder.filter(Filter.ascii_fold())
    builder = builder.filter(Filter.stopword(language))
    if recipe in ("Aplus", "Bplus", "Cplus", "Dplus"):
        builder = builder.filter(Filter.custom_stopword(list(supplement)))
    if recipe in ("B", "Bplus"):
        builder = builder.filter(Filter.ascii_fold())
    builder = builder.filter(Filter.remove_long(MAX_TOKEN_CHARS))
    builder = builder.filter(Filter.stemmer(language))
    if recipe in ("C", "Cplus", "Dplus"):
        builder = builder.filter(Filter.ascii_fold())
    return builder.build()


def family_score(analyzer: TextAnalyzer, forms: Sequence[str]) -> tuple[int, int, dict[str, list[str]]]:
    """Ordered pairs of surface forms that share at least one term.

    The ordered pair is the point of the metric: it reads as "somebody typed the
    left form and the document carries the right one". A hundred percent means
    every spelling of a lemma finds every other one, the diagonal included, so a
    form that produces no term at all fails against itself too.
    """
    terms = {form: analyzer.analyze(form) for form in forms}
    hits = 0
    total = 0
    for left in forms:
        for right in forms:
            total += 1
            if terms[left] and terms[right] and set(terms[left]) & set(terms[right]):
                hits += 1
    return hits, total, terms


def stopword_leaks(analyzer: TextAnalyzer, builtin: Sequence[str], folder: TextAnalyzer) -> tuple[list[str], list[str]]:
    """Return the stop words that still produce a term, per spelling.

    Both spellings are measured because a chain can be tight in one and open in
    the other: folding in front of the built in list lets the accented entry
    through, folding behind it lets the flat one through. The first list is the
    entries as the built in list carries them, the second their folded forms.
    """
    accented = [word for word in builtin if analyzer.analyze(word)]
    flat: list[str] = []
    for word in builtin:
        tokens = folder.analyze(word)
        folded = tokens[0] if tokens else ""
        if folded and analyzer.analyze(folded):
            flat.append(folded)
    return accented, flat


def verify_against_product(language: str, families: Sequence[Sequence[str]], supplement: Sequence[str]) -> list[str]:
    """Return the forms whose winning candidate differs from the shipped chain.

    This is what makes the probe honest. The six other candidates are built here
    because they exist nowhere else, but the one the report recommends is held
    against ``snowball_analyzer`` from the package, form by form. An empty list
    means the measured chain and the shipped chain are the same chain.
    """
    candidate = chain(language, WINNER, supplement)
    product = snowball_analyzer(language, supplement)
    differing: list[str] = []
    for forms in families:
        differing.extend(form for form in forms if candidate.analyze(form) != product.analyze(form))
    return differing


def _families_tsv(rows: Sequence[FormRow]) -> str:
    """Return the form table: one line per form and candidate."""
    lines = ["\t".join(FAMILIES_HEADER)]
    lines.extend("\t".join((code, lemma, form, recipe, ",".join(tokens))) for code, lemma, form, recipe, tokens in rows)
    return "\n".join(lines) + "\n"


def _losses_tsv(rows: Sequence[LossRow]) -> str:
    """Return the pairs the winning candidate does not bring together."""
    lines = ["\t".join(LOSSES_HEADER)]
    lines.extend(
        "\t".join((code, lemma, left, right, ",".join(left_tokens), ",".join(right_tokens)))
        for code, lemma, left, right, left_tokens, right_tokens in rows
    )
    return "\n".join(lines) + "\n"


def _numbers(figures: Sequence[tuple[str, object]]) -> str:
    """Return the key figures of the run. Numbers and digests, nothing else."""
    return "\n".join(f"{name}={value}" for name, value in figures) + "\n"


def _losses(code: str, forms: Sequence[str], terms: dict[str, list[str]]) -> list[LossRow]:
    """Return the unordered pairs of one family that share no term.

    Unordered, because sharing a term is symmetric and a loss printed twice is
    still one loss. The lemma is the first form of the family, which is how the
    fixture spells the entry a human looks up.
    """
    rows: list[LossRow] = []
    lemma = forms[0]
    for index, left in enumerate(forms):
        for right in forms[index + 1 :]:
            if not (terms[left] and terms[right] and set(terms[left]) & set(terms[right])):
                rows.append((code, lemma, left, right, terms[left], terms[right]))
    return rows


def _report(headline: str, cases: Sequence[str]) -> None:
    """Write a difference to stderr, headline first and then case by case."""
    print(f"chain_probe: {headline}", file=sys.stderr)
    for case in cases:
        print(f"chain_probe: differing form: {case}", file=sys.stderr)


def _split_arguments(argv: Sequence[str]) -> tuple[Path | None, Path, Path] | None:
    """Return the optional stop word source, the fixture directory and the output."""
    rest = list(argv)
    stopwords: Path | None = None
    if rest and rest[0] == STOPWORDS:
        if len(rest) < 2:
            return None
        stopwords = Path(rest[1])
        rest = rest[2:]
    if len(rest) != 2:
        return None
    return stopwords, Path(rest[0]), Path(rest[1])


def main(argv: Sequence[str]) -> int:
    """Write the three measurement files and prove the winner is the product."""
    parsed = _split_arguments(argv)
    if parsed is None:
        print(USAGE, file=sys.stderr)
        return 2

    stopwords_path, fixture_dir, out_dir = parsed
    out_dir.mkdir(parents=True, exist_ok=True)

    builtin: dict[str, list[str]] = {}
    if stopwords_path is None:
        print("chain_probe: no --stopwords, the leak measurement is skipped", file=sys.stderr)
    elif not stopwords_path.is_file():
        print(f"chain_probe: no stop word source at {stopwords_path}, the leak measurement is skipped", file=sys.stderr)
    else:
        builtin = read_builtin(stopwords_path)

    form_rows: list[FormRow] = []
    loss_rows: list[LossRow] = []
    figures: list[tuple[str, object]] = []
    totals = dict.fromkeys(RECIPES, 0)
    total_families = 0
    total_pairs = 0

    for language in LANGUAGES:
        code = CODE[language]
        fixture = fixture_dir / FIXTURE_NAME.format(code=code)
        if not fixture.is_file():
            print(f"chain_probe: no fixture at {fixture}", file=sys.stderr)
            return 1
        families = read_families(fixture)
        supplement = FOLDED_STOPWORDS[language]

        differing = verify_against_product(language, families, supplement)
        if differing:
            _report(f"the {WINNER} candidate of {code} is not the chain the product ships", differing)
            return 1

        pairs = sum(len(forms) ** 2 for forms in families)
        figures.append((f"{code}_families", len(families)))
        figures.append((f"{code}_pairs", pairs))
        total_families += len(families)
        total_pairs += pairs

        for recipe in RECIPES:
            analyzer = chain(language, recipe, supplement)
            hits = 0
            for forms in families:
                family_hits, _, terms = family_score(analyzer, forms)
                hits += family_hits
                form_rows.extend((code, forms[0], form, recipe, terms[form]) for form in forms)
                if recipe == WINNER:
                    loss_rows.extend(_losses(code, forms, terms))
            figures.append((f"{code}_{recipe}_hits", hits))
            totals[recipe] += hits

        figures.append((f"{code}_supplement", len(supplement)))

        if builtin:
            accented, flat = stopword_leaks(chain(language, WINNER, supplement), builtin[language], _ASCII_FOLDER)
            figures.append((f"{code}_leaks_accented", len(accented)))
            figures.append((f"{code}_leaks_flat", len(flat)))

    flat_supplement = [word for name in sorted(FOLDED_STOPWORDS) for word in FOLDED_STOPWORDS[name]]
    figures.append(("total_families", total_families))
    figures.append(("total_pairs", total_pairs))
    figures.append(("total_Aplus_hits", totals["Aplus"]))
    figures.append(("total_Cplus_hits", totals["Cplus"]))
    figures.append(("supplement_hash", folded_stopwords_hash(flat_supplement)))

    (out_dir / FAMILIES_FILE).write_text(_families_tsv(form_rows), encoding=ENCODING)
    (out_dir / NUMBERS_FILE).write_text(_numbers(figures), encoding=ENCODING)
    (out_dir / LOSSES_FILE).write_text(_losses_tsv(loss_rows), encoding=ENCODING)

    print(
        f"chain_probe: {total_families} families, {total_pairs} ordered pairs, {len(loss_rows)} losses under {WINNER}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
