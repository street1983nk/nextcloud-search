"""The stemmerless Czech chain cs and its folded Lucene stop word list.

tantivy 0.26.2 carries neither a Czech Snowball stemmer nor a Czech stop word
list, so the chain is simple, lowercase, ascii_fold, one custom stop word list,
remove_long, and nothing else. These cases assert WHAT it produces: an accent
pair of the same form lands on one term, an inflection pair does not (that is
the documented limit of a chain without a stemmer, CZ-03), every entry of the
Lucene original vanishes in both spellings, and the named exceptions survive as
the content words they are.

The list is held three ways at once, because a stop word in the index is a
silent quality loss with no error anywhere: the vendored original against its
SHA-256, the module against the generator output, and the module against the
digest below. The review table in the module docstring is held against the
generator's list of new folded forms, and its exception rows against
CZECH_EXCEPTIONS.

Accents appear only inside string literals. They are data here, the words the
product has to handle; the identifiers stay ASCII as the project rules require.
"""

import hashlib
import importlib.util
import re
import shutil
import sys
from pathlib import Path
from types import ModuleType

import pytest
from tantivy import TextAnalyzer

from findling.index import stopwords_cs
from findling.index.analyzer import ANALYZER_VERSION, MAX_TOKEN_CHARS, TOKENIZER_CS, czech_analyzer, snowball_analyzer
from findling.index.stopwords import folded_stopwords_hash
from findling.index.stopwords_cs import CZECH_EXCEPTIONS, CZECH_STOPWORDS_FOLDED
from test_analyzer import ANALYZER_SOURCE, filter_chain

# The digest of the shipped list, produced by scripts/dev/czech_stopwords.py
# against releases/lucene/10.5.2 on 2026-10-10. It stands here and nowhere else:
# in expected_versions() it would be an eighth mark that no installation in the
# field carries. When this goes red, run the generator again and answer the mark
# question in the docstring of findling.index.stopwords_cs BEFORE pulling it.
CZECH_FOLDED_SHA256 = "624ac83b125c1ff3bffdddd7b97cfd1979217c08f2fb964b03a17c1cf26d0455"

# SHA-256 of the Lucene original, the same value the generator pins.
ORIGINAL_SHA256 = "61f06aa1e7567ee8c72e895ea33229033669ac1cc52c6d40369a9ee2b76ad915"

REPO_ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = Path(__file__).resolve().parent / "fixtures" / "lucene_cz_stopwords_10_5_2.txt"

# The generator is a script and not a package, so it is loaded by path, the
# same way test_language_analyzers.py loads scripts/dev/chain_probe.py.
GENERATOR = REPO_ROOT / "scripts" / "dev" / "czech_stopwords.py"
GENERATOR_MODULE = "czech_stopwords_under_test"

# The order the cs chain has to run its filters in. No stemmer and no built in
# stop word list: tantivy has neither for Czech, and Filter.stopword("czech")
# would raise at startup.
EXPECTED_CZECH_CHAIN = ["lowercase", "ascii_fold", "custom_stopword", "remove_long"]

# One row of the review table in the docstring of stopwords_cs.
REVIEW_ROW = re.compile(r"^\s*\| (?P<form>[a-z]+) \| [^|]+ \| (?P<verdict>keep|exception) \| [^|]+ \|\s*$")


def _load_generator() -> ModuleType:
    """Return ``scripts/dev/czech_stopwords.py`` as a module, loaded by path."""
    specification = importlib.util.spec_from_file_location(GENERATOR_MODULE, GENERATOR)
    if specification is None or specification.loader is None:  # pragma: no cover
        raise RuntimeError(f"the generator is not at {GENERATOR}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator() -> ModuleType:
    return _load_generator()


@pytest.fixture(scope="module")
def chain() -> TextAnalyzer:
    return czech_analyzer()


def _original_entries() -> list[str]:
    return [line.strip() for line in ORIGINAL.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_the_vendored_original_is_the_pinned_lucene_file() -> None:
    assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() == ORIGINAL_SHA256


def test_an_accent_pair_unites_and_an_inflection_pair_stays_apart(chain: TextAnalyzer) -> None:
    # Pitfall 2 of the research: smlouva and smlouve are two forms, not two
    # spellings. Without a stemmer they stay two terms, and that is the limit.
    assert chain.analyze("Smlouvě smlouve SMLOUVĚ smlouva") == ["smlouve", "smlouve", "smlouve", "smlouva"]


def test_every_czech_diacritic_is_folded(chain: TextAnalyzer) -> None:
    assert chain.analyze("ŘÍJEN Říjen rijen") == ["rijen", "rijen", "rijen"]
    assert chain.analyze("Žluťoučký kůň úpěl ďábelské ódy") == ["zlutoucky", "kun", "upel", "dabelske", "ody"]


def test_no_list_entry_reaches_the_index_in_either_spelling(chain: TextAnalyzer, generator: ModuleType) -> None:
    # The whole original, every entry twice, accented and folded. Only the
    # named exceptions may come through, and they have to come through as
    # exactly their folded form.
    leaks: list[str] = []
    for entry in _original_entries():
        flat = generator.fold(entry)
        expected = [flat] if flat in CZECH_EXCEPTIONS else []
        for spelling in (entry, flat):
            tokens = chain.analyze(spelling)
            if tokens != expected:
                leaks.append(f"{spelling} (from {entry}) gives {tokens}, expected {expected}")
    assert leaks == [], "; ".join(leaks)


def test_the_exceptions_stay_terms_and_original_content_words_stay_stop_words(chain: TextAnalyzer) -> None:
    assert chain.analyze("Nájemní smlouva na byt") == ["najemni", "smlouva", "byt"]
    assert chain.analyze("jez na řece") == ["jez", "rece"]
    # strana stands in the Lucene list itself, and D-30-05 keeps it there.
    assert chain.analyze("smluvní strana") == ["smluvni"]


def test_a_token_longer_than_the_limit_is_dropped(chain: TextAnalyzer) -> None:
    assert chain.analyze("x" * MAX_TOKEN_CHARS) == ["x" * MAX_TOKEN_CHARS]
    assert chain.analyze("x" * (MAX_TOKEN_CHARS + 1)) == []


def test_czech_stays_outside_the_snowball_factory() -> None:
    with pytest.raises(ValueError, match="czech"):
        snowball_analyzer("czech")


def test_the_czech_chain_has_no_stemmer_and_no_built_in_list() -> None:
    source = ANALYZER_SOURCE.read_text(encoding="utf-8")
    assert filter_chain(source, "czech_analyzer") == EXPECTED_CZECH_CHAIN
    assert TOKENIZER_CS == "cs"


def test_the_analyzer_version_stays_at_one() -> None:
    # A new chain for a new field moves no tokenisation of any index already
    # written, so no mark moves either.
    assert ANALYZER_VERSION == 1


def test_the_module_is_the_generator_output(generator: ModuleType) -> None:
    derived = generator.build(ORIGINAL)
    assert derived is not None
    assert derived.shipped == CZECH_STOPWORDS_FOLDED
    assert tuple(generator.EXCEPTIONS) == CZECH_EXCEPTIONS
    assert folded_stopwords_hash(CZECH_STOPWORDS_FOLDED) == CZECH_FOLDED_SHA256


def test_the_list_is_ascii_and_free_of_duplicates() -> None:
    assert all(word.isascii() for word in CZECH_STOPWORDS_FOLDED)
    assert len(CZECH_STOPWORDS_FOLDED) == len(set(CZECH_STOPWORDS_FOLDED))
    assert not set(CZECH_EXCEPTIONS) & set(CZECH_STOPWORDS_FOLDED)
    assert {"strana", "proc", "uz"} <= set(CZECH_STOPWORDS_FOLDED)
    assert "byt" in CZECH_EXCEPTIONS


def test_the_generator_stops_on_a_tampered_copy(generator: ModuleType, tmp_path: Path) -> None:
    copy = tmp_path / ORIGINAL.name
    shutil.copyfile(ORIGINAL, copy)
    data = bytearray(copy.read_bytes())
    data[0] ^= 0x01
    copy.write_bytes(bytes(data))
    assert generator.main(["--source", str(copy)]) != 0
    assert generator.main(["--source", str(ORIGINAL), "--output", str(tmp_path / "out.py")]) == 0


def test_the_review_table_covers_every_new_form_and_names_the_exceptions(generator: ModuleType) -> None:
    derived = generator.build(ORIGINAL)
    assert derived is not None
    doc = stopwords_cs.__doc__ or ""
    rows = [match for match in map(REVIEW_ROW.match, doc.splitlines()) if match]
    forms = [row["form"] for row in rows]
    assert forms == [form for form, _ in derived.new_forms]
    assert {row["form"] for row in rows if row["verdict"] == "exception"} == set(CZECH_EXCEPTIONS)
