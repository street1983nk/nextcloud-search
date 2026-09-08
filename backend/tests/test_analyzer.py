"""The German chain, asserted token by token.

This table asserts WHAT is split, not THAT something was split. The difference is
the whole value of the file: a test that only checks "more than one token came
back" stays green while the splitter produces confetti, and that is exactly how
the naive recipe passed review elsewhere.

Every expectation below was measured against the real Debian list
(/usr/share/dict/ngerman, 276496 entries after recipe A) inside the container
image the app ships on. The fixture in tests/fixtures/constituents_de.txt is the
union of two things: the entries of that list which occur inside one of the
cases of tests/fixtures/compound_cases_de.txt, and the entries the suite already
carried. The union is not believed, it is measured: scripts/dev/measure_compounds.sh
--against tests/fixtures/constituents_de.txt runs the shipped chain over the
fixture and over the full list and exits non zero on the first case whose tokens
differ. So the table below is the behaviour of the real list, not of a convenient
miniature. A developer machine has no Debian word list, and a test that skips
itself when the list is missing is a test that never runs.

Umlauts appear only inside string literals. They are data here, the words the
product has to handle; the identifiers stay ASCII as the project rules require.
"""

import ast
import unicodedata
from collections.abc import Iterator
from pathlib import Path

import pytest
from tantivy import Index, TextAnalyzer

from findling.index.analyzer import (
    ANALYZER_VERSION,
    TOKENIZER_DE,
    TOKENIZER_EN,
    TOKENIZER_NAME,
    build_count,
    cached_german_analyzer,
    english_analyzer,
    german_analyzer,
    name_analyzer,
    normalize,
)
from findling.index.open import open_index
from findling.index.wordlist import wordlist_hash
from findling.index.writer import IndexBatchWriter, IndexRecord
from findling.query.rewrite import build_query

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt"

# The measured case list. Every word this module makes a claim about has to
# stand in here, because a claim about a word that was never fed to the probe is
# a claim about nothing.
CASES = Path(__file__).resolve().parent / "fixtures" / "compound_cases_de.txt"

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "findling"

# The two places the normalisation helper may be called from, and no third. One
# is the write side, the other is the question side; a third call somewhere else
# would be a second text space, which is the failure this whole plan is about.
EXPECTED_NORMALIZE_CALLERS = ("index/writer.py", "query/rewrite.py")

# One file name in the two spellings a mixed client base produces. macOS hands
# the name over decomposed, Linux and the web interface composed, and the two are
# different byte strings for the same name on screen.
NAME_NFC = unicodedata.normalize("NFC", "Kündigung Grüße.pdf")
NAME_NFD = unicodedata.normalize("NFD", "Kündigung Grüße.pdf")

# The 63 character one. Its own name below, because it is the cheapest insurance
# this project can buy: with remove_long in front of the splitter it yields the
# empty token list and the document becomes unfindable under any of its parts.
RINDFLEISCH = "Rindfleischetikettierungsüberwachungsaufgabenübertragungsgesetz"

# The ASCII transcription of the first compound. Its own name because the two
# spellings are one word to a reader and two different token lists to the index.
GRUNDSTUECK_ASCII = "Grundstuecksverkehrsgenehmigung"

# The twenty one everyday administrative compounds, with the tokens the full
# Debian list produces for each of them. This is the regression guard, and it
# guards both directions: a split that gets lost fails here just as loudly as a
# split that gets invented, because every line names the tokens instead of
# counting them. The seven single token lines are not decoration and not a
# comment either, they are the honest limit of the recipe written down as an
# assertion, so that a change which makes one of them splittable also has to say
# so out loud. UNSPLIT below cannot do this work: in every one of the four
# recipe variants measured in docs/measurements/2026-09-komposita-rezept-a/ all
# ten of its words survive whole, so a suite that only checks precision waves
# each of those variants through while recall falls apart.
COMPOUNDS = [
    ("Grundstücksverkehrsgenehmigung", ["grundstuck", "verkehr", "genehm"]),
    ("Kündigungsfrist", ["kundig", "frist"]),
    ("Sitzungsvorlage", ["sitzung", "vorlag"]),
    ("Haushaltssatzung", ["haushalt", "satzung"]),
    ("Jahresabschluss", ["jahr", "abschluss"]),
    ("Betriebskostenabrechnung", ["betriebskost", "abrechn"]),
    ("Krankenversicherung", ["krank", "versicher"]),
    ("Rechnungsnummer", ["rechnung", "numm"]),
    ("Datenschutzgrundverordnung", ["datenschutz", "grund", "verordn"]),
    ("Bundesausbildungsförderungsgesetz", ["bund", "ausbild", "forder", "gesetz"]),
    (RINDFLEISCH, ["rindfleisch", "etikettier", "uberwach", "aufgab", "ubertrag", "gesetz"]),
    ("Dampfschifffahrt", ["dampfschiff", "fahrt"]),
    ("Aufenthaltserlaubnis", ["aufenthalt", "erlaubnis"]),
    ("Gewerbeanmeldung", ["gewerb", "anmeld"]),
    # The seven that do not come apart today, each with the one token it really
    # produces. Six of them stand in the filtered list themselves, and an entry
    # is never split, so "Mietvertrag" is not findable through "Vertrag".
    ("Mietvertrag", ["mietvertrag"]),
    ("Bebauungsplan", ["bebauungsplan"]),
    ("Baugenehmigung", ["baugenehm"]),
    ("Bauantrag", ["bauantrag"]),
    # The seventh one is the case that does not explain itself through the list
    # at all: "Baukosten" is no entry, but "bau" has three characters and MIN_LEN
    # is four, so the lower bound alone keeps the word whole. Two independent
    # locks, and reading only the entry column misses this one.
    ("Baukosten", ["baukost"]),
    ("Arbeitsvertrag", ["arbeitsvertrag"]),
    ("Steuerbescheid", ["steuerbescheid"]),
]

# Ten everyday words that must survive whole. A recipe that splits any of them
# produces nonsense terms instead of better recall.
UNSPLIT = [
    ("Information", "information"),
    ("Vertrag", "vertrag"),
    ("Rechnung", "rechnung"),
    ("Sitzung", "sitzung"),
    ("Kunde", "kund"),
    ("Formular", "formular"),
    ("Termin", "termin"),
    ("Ordnung", "ordnung"),
    ("Beamter", "beamt"),
    ("Genehmigung", "genehm"),
]


@pytest.fixture(scope="module")
def constituents() -> list[str]:
    """The measured constituent subset, read once for the whole module."""
    return FIXTURE.read_text(encoding="utf-8").split()


@pytest.fixture(scope="module")
def german(constituents: list[str]) -> TextAnalyzer:
    """One German analyser for the whole module; building it is not free."""
    return german_analyzer(constituents)


@pytest.mark.parametrize(("text", "expected"), COMPOUNDS, ids=[text for text, _ in COMPOUNDS])
def test_the_twenty_one_compounds_produce_the_measured_tokens(
    german: TextAnalyzer, text: str, expected: list[str]
) -> None:
    assert german.analyze(text) == expected


def test_the_sixty_three_character_compound_does_not_disappear(german: TextAnalyzer) -> None:
    tokens = german.analyze(RINDFLEISCH)

    # Measured: with remove_long(40) at position two this is []. The word is then
    # gone from the index and the document is unfindable under any of its parts.
    # tantivy's own default analyzer makes exactly this mistake.
    assert tokens != []
    assert len(tokens) == 6
    assert "gesetz" in tokens


def test_no_bare_linking_element_reaches_the_index(german: TextAnalyzer) -> None:
    tokens = german.analyze("Kündigungsfrist")

    # Without custom_stopword(FUGEN) this is ["kundig", "s", "frist"], and "s"
    # then matches every second document in the corpus.
    assert tokens == ["kundig", "frist"]
    assert "s" not in tokens


@pytest.mark.parametrize(("text", "expected"), UNSPLIT, ids=[text for text, _ in UNSPLIT])
def test_ten_everyday_words_stay_whole(german: TextAnalyzer, text: str, expected: str) -> None:
    assert german.analyze(text) == [expected]


def test_german_stopwords_leave_nothing_behind(german: TextAnalyzer) -> None:
    # The built in list carries real umlauts and compares exactly, which is why
    # it stands after the splitter and before any folding.
    assert german.analyze("für über während könnte und der die das") == []


@pytest.mark.parametrize(
    ("singular", "plural"),
    [("Haus", "Häuser"), ("Vertrag", "Verträge"), ("Straße", "Strasse")],
)
def test_nominal_inflection_collapses_into_one_term(german: TextAnalyzer, singular: str, plural: str) -> None:
    assert german.analyze(singular) == german.analyze(plural)


def test_the_stemmer_folds_umlauts_without_a_folding_filter(german: TextAnalyzer) -> None:
    # This is why there is no ascii_fold in the German branch. Folding before the
    # splitter would make the list, which carries umlauts, unmatchable, and the
    # splitting would fail silently.
    assert german.analyze("Müller") == german.analyze("Muller") == ["mull"]


def test_documented_limit_d2_past_tense_is_not_unified(german: TextAnalyzer) -> None:
    # Infinitive and noun meet, past tense and participle do not. Not fixable
    # without replacing the stemmer, so the acceptance criterion of CONTEXT.md is
    # restated on nominal inflection. See docs/german-analyzer.md, "Known limits".
    assert german.analyze("suchen") == german.analyze("Suche") == ["such"]
    assert german.analyze("suchte") == ["sucht"]
    assert german.analyze("gesucht") == ["gesucht"]


def test_documented_limit_d3_spelled_out_umlaut_does_not_meet_the_umlaut(german: TextAnalyzer) -> None:
    # "Mueller" and "Müller" are the same name to a human and two terms to the
    # index. The fix belongs on the query side, plan 02-09: a query containing
    # ue, oe, ae or ss also gets the umlaut variant, joined with Occur.Should.
    # See docs/german-analyzer.md, "Known limits".
    assert german.analyze("Mueller") == ["muell"]
    assert german.analyze("Müller") == ["mull"]
    assert german.analyze("Mueller") != german.analyze("Müller")


def test_the_transcribed_umlaut_costs_the_split_not_only_the_term(german: TextAnalyzer) -> None:
    # The same word twice, once with the character and once with the two letters
    # a keyboard without umlauts produces. Measured: the umlaut spelling comes
    # apart into three parts, the transcription stays one thirty one character
    # token, because the constituent list carries "grundstück" and not
    # "grundstueck" and the splitter compares exactly.
    #
    # add_umlaut_variants of plan 02-09 does not reach this: it widens the
    # question, and the index side has no counterpart to it. So a document that
    # spells the compound this way is findable under the whole word only. Open
    # question 5 of the phase research, and a named limit rather than a defect.
    assert german.analyze(GRUNDSTUECK_ASCII) == ["grundstuecksverkehrsgenehm"]
    assert german.analyze("Grundstücksverkehrsgenehmigung") == ["grundstuck", "verkehr", "genehm"]


def test_every_asserted_word_stands_in_the_measured_case_list() -> None:
    # The guard over the guard. Every word this module makes a claim about has to
    # be a word the probe of plan 08-01 really ran, otherwise the table could
    # grow a line that was never measured against the real Debian list and would
    # still look exactly like the measured ones.
    measured = set(CASES.read_text(encoding="utf-8").split())
    asserted = [text for text, _ in COMPOUNDS] + [text for text, _ in UNSPLIT] + [GRUNDSTUECK_ASCII]

    missing = sorted(word for word in asserted if word not in measured)

    assert missing == [], (
        f"asserted here but never measured, add to {CASES.name} and rerun scripts/dev/measure_compounds.sh: {missing}"
    )


def test_the_english_analyzer_folds_where_the_german_one_must_not(german: TextAnalyzer) -> None:
    english = english_analyzer()

    # A different algorithm stems here, so folding is safe and useful.
    assert english.analyze("Müller") == ["muller"]
    assert english.analyze("Müller") != german.analyze("Müller")
    assert english.analyze("the running documents") == ["run", "document"]


def test_the_name_analyzer_folds_and_does_not_stem() -> None:
    tokens = name_analyzer().analyze("Kündigungsfrist_2024.pdf")

    # A file name is looked for as it is written. Stemming it would make
    # "Kuendigung.pdf" and "Kuendigungen.pdf" the same file name.
    assert tokens == ["kundigungsfrist", "2024", "pdf"]


def test_analyzer_is_built_once(constituents: list[str]) -> None:
    # A second build in the same process is not a blemish. It is 0.44 s and
    # roughly 23 MB again, which on a 4 GB box is the difference between a search
    # service and a memory problem.
    digest = wordlist_hash(constituents) + "-built-once"
    before = build_count()

    first = cached_german_analyzer(digest, constituents)
    second = cached_german_analyzer(digest, constituents)

    assert first is second
    assert build_count() - before == 1


def test_a_changed_word_list_forces_a_new_automaton(constituents: list[str]) -> None:
    before = build_count()

    cached_german_analyzer("digest-a", constituents)
    cached_german_analyzer("digest-b", constituents)

    # The cache is keyed on the digest of the list, because a changed list is a
    # changed tokenisation (T-02-11).
    assert build_count() - before == 2


def test_the_tokenizer_names_are_the_ones_the_schema_stores() -> None:
    # The schema persists the name of a tokenizer, never the tokenizer. Opening
    # an index without registering these exact names fails at the first query
    # with an error that reads like a broken index.
    assert (TOKENIZER_DE, TOKENIZER_EN, TOKENIZER_NAME) == ("de", "en", "name")


def test_the_analyzer_version_is_pinned_next_to_the_chain() -> None:
    # Tokenisation is part of the data. Every change to the chain above has to
    # raise this number, because the index and the query parser have to agree.
    assert ANALYZER_VERSION == 1


# ---------------------------------------------------------------------------
# Unicode file names: one name, two spellings, one text space.
#
# This is not the exotic corner it looks like. A German user base with a mixed
# set of clients produces it at the first umlaut in a file name, and the symptom
# is an empty result list, which is the one symptom nobody reports as a bug.
# ---------------------------------------------------------------------------


@pytest.fixture
def index(constituents: list[str], tmp_path: Path) -> Index:
    return open_index(tmp_path / "index", constituents)


@pytest.fixture
def writer(index: Index, tmp_path: Path) -> Iterator[IndexBatchWriter]:
    batch = IndexBatchWriter(index, directory=tmp_path / "index")
    yield batch
    batch.close()


def _record(name: str, file_id: int = 1) -> IndexRecord:
    return IndexRecord(
        file_id=file_id,
        storage_id=7,
        name=name,
        title=name,
        path=f"/Vertraege/{name}",
        ext="pdf",
        body=f"Die Anlage {name} gehoert zum Vorgang.",
        mtime=1_700_000_000,
    )


def _hits(index: Index, question: str) -> int:
    index.reload()
    rewritten = build_query(index, question, title_only=True)
    if rewritten.query is None:
        return 0
    return len(index.searcher().search(rewritten.query, 10).hits)


def test_the_two_spellings_of_one_name_are_two_names_before_the_helper() -> None:
    # The measurement that makes the rest of this section necessary, and the
    # reason ascii_fold is not enough: it folds ASCII, and a combining diaeresis
    # is not ASCII. The simple tokenizer splits on the combining character, so
    # the decomposed name does not merely tokenise differently, it produces terms
    # that share nothing with the composed one.
    analyzer = name_analyzer()

    assert NAME_NFC != NAME_NFD
    assert analyzer.analyze(NAME_NFC) == ["kundigung", "grusse", "pdf"]
    assert analyzer.analyze(NAME_NFD) == ["ku", "ndigung", "gru", "sse", "pdf"]


def test_the_helper_makes_the_two_spellings_one_name() -> None:
    analyzer = name_analyzer()

    assert normalize(NAME_NFD) == normalize(NAME_NFC)
    assert analyzer.analyze(normalize(NAME_NFD)) == analyzer.analyze(normalize(NAME_NFC))


@pytest.mark.parametrize(
    ("written", "asked"),
    [(NAME_NFD, NAME_NFC), (NAME_NFC, NAME_NFD)],
    ids=["written-nfd-asked-nfc", "written-nfc-asked-nfd"],
)
def test_a_name_is_found_in_the_other_unicode_spelling(
    written: str, asked: str, index: Index, writer: IndexBatchWriter
) -> None:
    # Both directions, because a normalisation on one side only is worse than
    # none: it moves the failure to the other client instead of removing it.
    writer.add(_record(written))
    writer.flush()

    assert _hits(index, "Kündigung") == 1
    assert _hits(index, asked) == 1


def test_a_name_over_the_length_of_a_file_system_limit_is_written_and_found(
    index: Index, writer: IndexBatchWriter
) -> None:
    # Over 255 characters, which is where several file systems stop. The name is
    # built out of words rather than out of one run of letters on purpose: a
    # single token longer than MAX_NAME_CHARS is dropped by remove_long, which is
    # the documented behaviour of the chain and not the subject of this case.
    name = " ".join(f"Kuendigung{number:03d}" for number in range(30)) + ".pdf"

    assert len(name) > 255

    writer.add(_record(name))
    writer.flush()

    assert _hits(index, "Kuendigung017") == 1


@pytest.mark.parametrize(
    "name",
    ["Bericht\nzweite Zeile.pdf", "Bericht‮gfp.pdf", "Bericht​­.pdf"],
    ids=["line-break", "direction-override", "zero-width"],
)
def test_a_name_with_a_control_character_breaks_neither_side(name: str, index: Index, writer: IndexBatchWriter) -> None:
    # None of these needs a change here, and that is the point of pinning them:
    # the tokenizer splits on them and the parser never sees them, because the
    # search line is a different string than the file name.
    #
    # The display side is a different question and it has an answer of its own:
    # a direction override reverses the rest of the line in a browser, and
    # PlainText::bounded of the PHP companion is the one place that shortens a
    # name for display. Nothing is rebuilt here in Python.
    writer.add(_record(name))
    writer.flush()

    assert _hits(index, "Bericht") == 1


def test_the_normalisation_does_not_build_a_second_automaton(index: Index, writer: IndexBatchWriter) -> None:
    # The ratchet against the expensive mistake. A normalisation that touched the
    # word list or its digest would have the cache miss and build the automaton a
    # second time, which is 0.44 s and roughly 23 MB again on a 4 GB box. The
    # counter answers that without a measurement.
    before = build_count()

    writer.add(_record(NAME_NFD))
    writer.flush()

    assert _hits(index, NAME_NFC) == 1
    assert build_count() == before


# -- the helper has exactly two callers --------------------------------------


def normalize_callers(relative_path: str, source: str) -> list[str]:
    """Modules that call the normalisation helper, read off the syntax tree.

    Only a bare call of the imported name counts. ``unicodedata.normalize`` is
    written with its module in front and is the implementation of the helper, not
    a second caller of it, and the syntax tree tells the two apart without a
    special case.

    Reading the tree is also the comment filter this count needs: a comment that
    says "never call normalize() here" is not part of the tree, so it cannot
    raise the number.
    """
    normalized = relative_path.replace("\\", "/")
    tree = ast.parse(source, filename=relative_path)
    return [
        normalized
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "normalize"
    ]


def test_the_helper_is_called_from_exactly_two_modules() -> None:
    callers = sorted(
        {
            caller
            for path in sorted(PACKAGE_ROOT.rglob("*.py"))
            for caller in normalize_callers(path.relative_to(PACKAGE_ROOT).as_posix(), path.read_text(encoding="utf-8"))
        }
    )

    # Not a tautology, a ratchet. One caller means one side normalises and the
    # other does not, which is the empty result list this section exists for.
    # Three means a third text space that nobody compares against the first two.
    assert tuple(callers) == EXPECTED_NORMALIZE_CALLERS


def test_the_counting_gate_sees_a_third_caller() -> None:
    source = "def f(text):\n    return normalize(text)\n"

    assert normalize_callers("api/search.py", source) == ["api/search.py"]


def test_a_comment_that_names_the_helper_does_not_raise_the_count() -> None:
    source = "# Do not call normalize(text) here, the write side has done it.\ndef f(text):\n    return text\n"

    assert normalize_callers("api/search.py", source) == []


def test_the_implementation_of_the_helper_is_not_counted_as_a_caller() -> None:
    source = 'def normalize(text):\n    return unicodedata.normalize("NFC", text)\n'

    assert normalize_callers("index/analyzer.py", source) == []


# -- the order of the filters, read off the syntax tree ----------------------
#
# The table at the top of this file asserts what the chain produces today. It
# goes red when the splitter disappears, and it would also go red for a hundred
# other reasons, so it never says which position of the chain moved. The guard
# below says exactly that: it reads the chain out of the source of
# index/analyzer.py and holds its order, so pulling a filter past its neighbour
# is a failure of its own and not a puzzle in a token table.
#
# Reading the tree rather than the text is what makes the guard trustworthy. A
# comment that names a filter is not part of the tree, so prose about the chain
# cannot hold the guard green while the chain itself is gone.

# The source the guard reads. The file and not the imported module, because a
# built analyser tells nobody in which order it was built.
ANALYZER_SOURCE = PACKAGE_ROOT / "index" / "analyzer.py"

# The shipped German order. Three of its neighbourships are load bearing, and
# every one of them was measured; the test below names them.
EXPECTED_GERMAN_CHAIN = [
    "lowercase",
    "split_compound",
    "custom_stopword",
    "stopword",
    "remove_long",
    "stemmer",
]

# The file name chain, held so that the guard has to tell two chains apart.
EXPECTED_NAME_CHAIN = ["lowercase", "ascii_fold", "remove_long"]


def _factory_names(build: ast.Call) -> list[str]:
    """Walk a builder chain from its build() call inwards and name the filters.

    The chain is one nested expression, so the outermost call is ``build()`` and
    the innermost is the builder itself. Walking outside in and reversing at the
    end is what turns that nesting back into the order the filters run in.
    """
    names: list[str] = []
    node: ast.expr = build
    while isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if node.func.attr == "filter" and node.args:
            factory = node.args[0]
            if isinstance(factory, ast.Call) and isinstance(factory.func, ast.Attribute):
                names.append(factory.func.attr)
        node = node.func.value
    names.reverse()
    return names


def filter_chain(source: str, function: str) -> list[str]:
    """Return the filters of one analyser factory, in the order they run.

    ``Filter.lowercase()`` becomes ``"lowercase"``. Only the syntax tree is read,
    exactly as :func:`normalize_callers` above does it, so neither a docstring
    nor a comment that names a filter can put one into the list. A function this
    source does not define, or one that builds no chain, gives the empty list.
    """
    for definition in ast.walk(ast.parse(source)):
        if not isinstance(definition, ast.FunctionDef) or definition.name != function:
            continue
        for call in ast.walk(definition):
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == "build":
                return _factory_names(call)
    return []


def test_the_german_chain_stands_in_the_measured_order() -> None:
    # Three positions carry the recipe, and each of them was measured rather
    # than reasoned about.
    # lowercase before the splitter: everything after it compares strings byte
    # for byte and the constituent list is lowercase, so without it the splitter
    # does not fire at all, and it fails silently while shallow tests stay green.
    # remove_long after the splitter: in front of it the 63 character compound
    # becomes the empty token list and the document is findable under none of its
    # six parts, which is the mistake tantivy's own default analyzer makes.
    # stemmer last: a stemmed compound matches no entry of the list any more, so
    # a splitter behind it would have nothing left to find.
    chain = filter_chain(ANALYZER_SOURCE.read_text(encoding="utf-8"), "german_analyzer")

    assert chain == EXPECTED_GERMAN_CHAIN


def test_the_guard_tells_two_chains_apart() -> None:
    # Without this, a guard that always returned the same list would look green
    # for the German chain and prove nothing at all.
    chain = filter_chain(ANALYZER_SOURCE.read_text(encoding="utf-8"), "name_analyzer")

    assert chain == EXPECTED_NAME_CHAIN


def test_the_guard_sees_a_missing_splitter() -> None:
    source = (
        "def german_analyzer(constituents):\n"
        "    return (\n"
        "        TextAnalyzerBuilder(Tokenizer.simple())\n"
        "        .filter(Filter.lowercase())\n"
        "        .filter(Filter.custom_stopword(list(FUGEN)))\n"
        '        .filter(Filter.stopword("german"))\n'
        "        .filter(Filter.remove_long(MAX_TOKEN_CHARS))\n"
        '        .filter(Filter.stemmer("german"))\n'
        "        .build()\n"
        "    )\n"
    )

    chain = filter_chain(source, "german_analyzer")

    assert "split_compound" not in chain
    assert chain != EXPECTED_GERMAN_CHAIN


def test_the_guard_sees_remove_long_pulled_in_front_of_the_splitter() -> None:
    # The anti pattern with a name. The token table alone would report this as
    # "the 63 character compound is suddenly empty" and leave the reader to work
    # out why; the guard reports the filter that moved.
    source = (
        "def german_analyzer(constituents):\n"
        "    return (\n"
        "        TextAnalyzerBuilder(Tokenizer.simple())\n"
        "        .filter(Filter.lowercase())\n"
        "        .filter(Filter.remove_long(MAX_TOKEN_CHARS))\n"
        "        .filter(Filter.split_compound(list(constituents)))\n"
        "        .filter(Filter.custom_stopword(list(FUGEN)))\n"
        '        .filter(Filter.stopword("german"))\n'
        '        .filter(Filter.stemmer("german"))\n'
        "        .build()\n"
        "    )\n"
    )

    chain = filter_chain(source, "german_analyzer")

    assert chain.index("remove_long") < chain.index("split_compound")
    assert chain != EXPECTED_GERMAN_CHAIN


def test_a_comment_that_names_a_filter_does_not_enter_the_chain() -> None:
    source = (
        "def german_analyzer(constituents):\n"
        "    # split_compound used to stand here, see Filter.split_compound below.\n"
        "    return (\n"
        "        TextAnalyzerBuilder(Tokenizer.simple())\n"
        "        .filter(Filter.lowercase())\n"
        "        .build()\n"
        "    )\n"
    )

    chain = filter_chain(source, "german_analyzer")

    assert chain == ["lowercase"]
