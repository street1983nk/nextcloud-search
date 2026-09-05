"""The three language files under testdata/semantik, held against the one rule that makes them worth measuring.

A retrieval test set is easy to build and easy to build wrongly, and the wrong
one is not obviously wrong: if the words of the question also stand in the target
passage, then every method finds that passage, the lexical index best of all, and
the resulting number says nothing whatsoever about semantics. Such a set measures
full text search and reports it as proof of an embedding model.

So the rule is mechanical here rather than a paragraph of good intentions: **no
content word of a query may stand verbatim in its own passage**. Function words
are exempt, because a paraphrase cannot avoid articles and prepositions, and a
list of them per language is kept below. A violation is a red test that names the
identifier of the case and never the text of it, which is the same discipline the
measuring tool follows (T-02-14, T-06-11).

The passages of one language are at the same time the distractor set of that
language: every query competes against all the other passages of its file, so a
second list is not needed and cannot drift away from the first.

Two halves live in this file. The first, from plan 06-03 task 1, is the well
formedness of the data. The second, from task 2, is the behaviour of
``scripts/dev/model_quality.py``, which reads exactly these files.

The tool is a script rather than part of the installed package, so it is loaded
from its path, the same way test_load_corpus.py loads the corpus generator. It
belongs next to quantize_model.py where a reader looks for model tooling, and it
has to stay runnable with a bare ``uv run python scripts/dev/model_quality.py``.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from collections.abc import Mapping
from functools import cache
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
DATASET_DIR: Final = REPO_ROOT / "testdata" / "semantik"
README_PATH: Final = DATASET_DIR / "README.md"

LANGUAGES: Final = ("de", "en", "fr")
MINIMUM_CASES: Final = 40
FIELDS: Final = ("id", "query", "passage", "note")

# Letters and digits, no underscore, and the apostrophe is a separator rather
# than a letter. That last part is what makes the French cases checkable at all:
# "l'immeuble" has to become "l" and "immeuble", or the elided article would hide
# the noun behind it from the rule.
WORD: Final = re.compile(r"[^\W_]+")

# The function words of the three languages: articles, pronouns, prepositions,
# conjunctions, auxiliaries, modals and question words. They are exempt from the
# rule because a paraphrase cannot be written without them, and because their
# presence in both halves of a case tells nobody anything. Everything that is not
# in these sets counts as content, including numerals, which is deliberate: a
# date that stands in both halves is a lexical bridge like any other.
GERMAN_FUNCTION_WORDS: Final = """
    aber alle allem allen aller alles als also am an auch auf aus bei beim bin bis da dabei dadurch daher damit
    dann daran darf das dass dem den denn der des deshalb dessen die dies diese diesem diesen dieser dieses
    doch dort du durch ein eine einem einen einer eines er es etwas euch für gegen gewesen habe haben hat
    hatte hatten hier ich ihm ihn ihnen ihr ihre ihrem ihren ihrer im in ins ist ja je jede jedem jeden jeder
    jedes jetzt kann kein keine keinen keiner können könnte man mehr mein meine meinem meinen meiner mich mir
    mit muss musste müssen nach nicht nichts noch nun nur ob obwohl oder ohne schon sehr sein seine seinem
    seinen seiner seit sich sie sind so soll sollen sollte sondern um und uns unser unsere unserem unseren
    unter viel vom von vor war waren warum was weil welche welchem welchen welcher welches wem wen wenn wer
    werde werden weshalb wie wieder wir wird wo wobei wodurch womit woran worauf wovon wozu wurde wurden würde
    würden während über ab neben zu zum zur zwischen
    """

ENGLISH_FUNCTION_WORDS: Final = """
    a about above after again against all also am an and any are as at be because been before being below
    between both but by can could did do does doing done down during each every few for from further had has
    have having he her here hers him his how i if in into is it its itself just may me might mine more most
    much must my no nor not now of off on once one only or other our ours out over own per shall she should
    since so some still such than that the their theirs them then there these they this those through to too
    under until up us very was we were what when where which while who whom whose why will with within would
    you your yours
    """

FRENCH_FUNCTION_WORDS: Final = """
    a à ai alors as au aucun aucune aujourd auprès aura auront aux avaient avait avant avec avez avoir avons c
    car ce ceci cela celle celles celui ces cet cette ceux chaque chez combien comme comment d dans de depuis
    des dès doit doivent dois donc dont du durant elle elles en encore es est et étaient était été êtes être
    eux faut il ils j je jusqu l la là le lequel les leur leurs lors lorsque lui m ma mais me même mes mien moins
    mon n ne ni nos notre nous on ont ou où par parce pas peut peuvent plus plusieurs pour pourquoi pouvez
    puis qu quand que quel quelle quelles quels qui quoi s sa sans se sera seront ses si sien soit son sont
    sous suis sur t ta te tes toi ton tous tout toute toutes très trop tu un une vers vos votre vous y
    """

STOPWORDS: Final[Mapping[str, frozenset[str]]] = {
    "de": frozenset(GERMAN_FUNCTION_WORDS.split()),
    "en": frozenset(ENGLISH_FUNCTION_WORDS.split()),
    "fr": frozenset(FRENCH_FUNCTION_WORDS.split()),
}

# Assembled from code points, because this file would otherwise fail on itself.
DASHES: Final = (chr(0x2014), chr(0x2013))


def tokens(text: str) -> list[str]:
    """The words of a text: lowercased, punctuation dropped, digits kept as words of their own."""
    return WORD.findall(text.lower())


def content_words(text: str, language: str) -> set[str]:
    return set(tokens(text)) - STOPWORDS[language]


def overlapping_words(record: Mapping[str, str], language: str) -> set[str]:
    """The content words of the query that also stand in its passage. Empty is the only acceptable answer."""
    return content_words(record["query"], language) & set(tokens(record["passage"]))


@cache
def raw_lines(language: str) -> tuple[str, ...]:
    text = (DATASET_DIR / f"{language}.jsonl").read_text(encoding="utf-8")
    return tuple(text.splitlines())


@cache
def cases(language: str) -> tuple[dict[str, str], ...]:
    return tuple(json.loads(line) for line in raw_lines(language))


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_line_is_one_record_with_the_four_fields(language: str) -> None:
    for number, line in enumerate(raw_lines(language), start=1):
        assert line.strip(), f"{language}.jsonl line {number} is empty"
        record = json.loads(line)
        assert isinstance(record, dict), f"{language}.jsonl line {number}"
        assert tuple(sorted(record)) == tuple(sorted(FIELDS)), f"{language}.jsonl line {number}"
        for field in FIELDS:
            assert isinstance(record[field], str), f"{language}.jsonl line {number} field {field}"
            assert record[field].strip(), f"{language}.jsonl line {number} field {field} is empty"


@pytest.mark.parametrize("language", LANGUAGES)
def test_each_language_carries_at_least_forty_cases(language: str) -> None:
    assert len(cases(language)) >= MINIMUM_CASES


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_identifiers_are_unique_within_a_language(language: str) -> None:
    identifiers = [record["id"] for record in cases(language)]
    duplicates = sorted({identifier for identifier in identifiers if identifiers.count(identifier) > 1})
    assert duplicates == [], f"{language}: {duplicates}"
    assert all(identifier.startswith(f"{language}-") for identifier in identifiers)


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_passages_are_distinct_within_a_language(language: str) -> None:
    """The passages are the distractor set, so two identical ones would make a rank undecidable."""
    passages = [record["passage"] for record in cases(language)]
    repeated = sorted({record["id"] for record in cases(language) if passages.count(record["passage"]) > 1})
    assert repeated == [], f"{language}: {repeated}"


@pytest.mark.parametrize("language", LANGUAGES)
def test_no_content_word_of_a_query_stands_in_its_own_passage(language: str) -> None:
    """The rule. A case that fails here measures the lexical index and claims semantics.

    The failure names identifiers and the offending words, never a query and
    never a passage: this suite is read in CI logs that are more public than the
    corpus behind them.
    """
    offenders = {
        record["id"]: sorted(overlapping_words(record, language))
        for record in cases(language)
        if overlapping_words(record, language)
    }
    assert offenders == {}, f"{language}: word overlap in {offenders}"


def test_the_overlap_check_goes_red_on_a_case_that_would_measure_full_text_search() -> None:
    """The gate is shown to be able to fire, on a case built for the purpose.

    Without this, a rule that silently matched nothing would look exactly like a
    rule that everybody obeyed.
    """
    lexical = {
        "id": "de-probe",
        "query": "Wie hoch ist die Kündigungsfrist?",
        "passage": "Die Kündigungsfrist beträgt drei Monate zum Quartalsende.",
        "note": "A case that shares its content word and therefore proves nothing about semantics.",
    }
    assert overlapping_words(lexical, "de") == {"kündigungsfrist"}

    paraphrase = {
        "id": "de-probe-2",
        "query": "Wie lange vorher muss ich aussteigen?",
        "passage": "Die Kündigungsfrist beträgt drei Monate zum Quartalsende.",
        "note": "The same passage, asked for without any of its words.",
    }
    assert overlapping_words(paraphrase, "de") == set()


def test_the_apostrophe_does_not_hide_a_french_noun_from_the_rule() -> None:
    """l'autorisation has to be seen as autorisation, or the elision would be a loophole."""
    elided = {
        "id": "fr-probe",
        "query": "Quand expire l'autorisation ?",
        "passage": "L'autorisation devient caduque au bout de trois ans.",
        "note": "A case whose only shared word hides behind an elided article.",
    }
    assert overlapping_words(elided, "fr") == {"autorisation"}


def test_the_german_cases_carry_real_umlauts_and_a_sharp_s() -> None:
    text = (DATASET_DIR / "de.jsonl").read_text(encoding="utf-8")
    for character in ("ä", "ö", "ü", "ß"):
        assert character in text, character
    assert "\\u" not in text, "escaped code points instead of the characters themselves"


def test_the_french_cases_carry_accents_and_a_cedilla() -> None:
    text = (DATASET_DIR / "fr.jsonl").read_text(encoding="utf-8")
    for character in ("é", "è", "à", "ç"):
        assert character in text, character
    assert "\\u" not in text, "escaped code points instead of the characters themselves"


def test_no_dash_stands_in_the_five_files() -> None:
    for path in (README_PATH, *(DATASET_DIR / f"{language}.jsonl" for language in LANGUAGES), Path(__file__)):
        text = path.read_text(encoding="utf-8")
        for dash in DASHES:
            assert dash not in text, f"{dash!r} in {path.name}"


def test_the_readme_names_the_rule_the_origin_the_licence_and_the_absence_of_personal_data() -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    for phrase in ("Wortüberschneidung", "Herkunft", "Lizenz", "personenbezogene"):
        assert phrase in readme, phrase


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_readme_states_the_true_number_of_cases(language: str) -> None:
    """A count in prose drifts away from the files it counts unless something holds it."""
    rows = [line for line in README_PATH.read_text(encoding="utf-8").splitlines() if f"{language}.jsonl" in line]
    assert rows, f"the README does not mention {language}.jsonl"
    assert any(str(len(cases(language))) in row for row in rows), f"{language}: count not stated"


# ---------------------------------------------------------------------------
# The measuring tool, from task 2 of the same plan.
#
# Everything below runs without a model on disk and without onnxruntime. That is
# not a shortcut, it is the design: the arithmetic of a rank, the shape of the
# report and the three refusals are the parts that can be wrong in a way nobody
# would notice, and they are exactly the parts that need no weights.
# ---------------------------------------------------------------------------

TOOL_PATH: Final = REPO_ROOT / "scripts" / "dev" / "model_quality.py"


def _load_tool() -> ModuleType:
    specification = importlib.util.spec_from_file_location("model_quality", TOOL_PATH)
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


quality = _load_tool()


def _dummy_model(tmp_path: Path) -> Path:
    """A file that exists. Its content is never read on the paths tested here."""
    path = tmp_path / "model.onnx"
    path.write_bytes(b"not a model, and never opened on these paths")
    return path


def _one_hot(size: int, hot: int) -> list[float]:
    return [1.0 if index == hot else 0.0 for index in range(size)]


def test_the_rank_of_the_correct_passage_is_counted_from_one() -> None:
    """Three queries, three passages, one deliberate miss. No model anywhere near this."""
    import numpy as np

    passages = np.array([_one_hot(3, 0), _one_hot(3, 1), _one_hot(3, 2)], dtype=np.float32)
    queries = np.array(
        [
            _one_hot(3, 0),  # exactly its own passage
            [0.0, 0.9, 0.4],  # closest to its own, but not identical
            [0.9, 0.1, 0.4],  # closer to passage 0 than to its own passage 2
        ],
        dtype=np.float32,
    )
    assert quality.ranks_of(queries, passages) == [1, 1, 2]


def test_a_tie_is_counted_against_the_tool() -> None:
    """A model that maps everything onto one vector must not come out looking perfect."""
    import numpy as np

    identical = np.array([_one_hot(2, 0), _one_hot(2, 0)], dtype=np.float32)
    assert quality.ranks_of(identical, identical) == [2, 2]


def test_the_metrics_are_the_ordinary_ones() -> None:
    metrics = quality.metrics_of([1, 1, 2, 10])
    assert metrics.cases == 4
    assert metrics.recall_at_1 == pytest.approx(0.5)
    assert metrics.recall_at_5 == pytest.approx(0.75)
    assert metrics.mrr == pytest.approx((1.0 + 1.0 + 0.5 + 0.1) / 4)


def test_quantising_the_vectors_moves_them_without_turning_them_around() -> None:
    """The second stage, on its own: rounding to int8 costs precision, not direction."""
    import numpy as np

    original = quality.normalise(np.array([[0.31, -0.62, 0.72], [0.9, 0.1, -0.42]], dtype=np.float32))
    quantised = quality.quantise_to_int8(original)
    assert not np.array_equal(original, quantised)
    cosines = (quality.normalise(original) * quality.normalise(quantised)).sum(axis=1)
    assert cosines.min() > 0.999


def test_the_report_names_every_number_that_was_asked_for() -> None:
    model = Path("/model/int8/model.onnx")
    metrics = quality.Metrics(cases=42, recall_at_1=0.9524, recall_at_5=1.0, mrr=0.9762)
    report = quality.format_report(
        model, Path("/model"), DATASET_DIR / "de.jsonl", "on", "int8", metrics, [("de-13", 3)]
    )
    for token in ("Recall@1", "Recall@5", "MRR", "42", str(model), "de.jsonl", "on", "int8"):
        assert token in report, token
    assert "de-13 rank 3" in report


def test_a_missing_model_ends_with_a_named_message_and_a_non_zero_code(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = quality.main(
        [
            *("--model", str(tmp_path / "absent.onnx")),
            *("--tokenizer", str(tmp_path)),
            *("--dataset", str(DATASET_DIR / "de.jsonl")),
            *("--prefixes", "on"),
            *("--vector-dtype", "fp32"),
        ]
    )
    captured = capsys.readouterr()
    assert code != 0
    assert "model not found" in captured.err
    assert captured.out == ""


def test_a_missing_tokenizer_ends_with_a_named_message(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = quality.main(
        [
            *("--model", str(_dummy_model(tmp_path))),
            *("--tokenizer", str(tmp_path / "no-such-directory")),
            *("--dataset", str(DATASET_DIR / "de.jsonl")),
            *("--prefixes", "on"),
            *("--vector-dtype", "fp32"),
        ]
    )
    captured = capsys.readouterr()
    assert code != 0
    assert "tokenizer directory not found" in captured.err
    assert captured.out == ""


def test_an_empty_dataset_ends_with_a_named_message(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """An empty file is a refusal, never a zero that travels into a table as a measurement."""
    empty = tmp_path / "empty.jsonl"
    empty.write_text("\n\n", encoding="utf-8")
    code = quality.main(
        [
            *("--model", str(_dummy_model(tmp_path))),
            *("--tokenizer", str(tmp_path)),
            *("--dataset", str(empty)),
            *("--prefixes", "on"),
            *("--vector-dtype", "fp32"),
        ]
    )
    captured = capsys.readouterr()
    assert code != 0
    assert "dataset is empty" in captured.err
    assert captured.out == ""


def test_a_full_run_prints_no_word_of_the_test_set(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The privacy claim of this tool, checked rather than promised (T-02-14, T-06-11).

    The measurement itself is replaced, because what is under test here is the
    printing and not the model: every value the report can carry is fed in, the
    worst cases and the full per case list included, and none of the text behind
    those identifiers may appear.
    """
    metrics = quality.Metrics(cases=42, recall_at_1=0.9, recall_at_5=1.0, mrr=0.95)
    ranked = [(record["id"], number % 7 + 1) for number, record in enumerate(cases("de"))]
    monkeypatch.setattr(quality, "measure", lambda *_args, **_kwargs: (metrics, ranked))

    code = quality.main(
        [
            *("--model", "/model/int8/model.onnx"),
            *("--tokenizer", "/model"),
            *("--dataset", str(DATASET_DIR / "de.jsonl")),
            *("--prefixes", "on"),
            *("--vector-dtype", "int8"),
            "--per-case",
        ]
    )
    printed = capsys.readouterr().out.lower()
    assert code == 0

    corpus_words = {
        word
        for record in cases("de")
        for text in (record["query"], record["passage"])
        for word in tokens(text)
        if len(word) >= 5
    }
    leaked = sorted(word for word in corpus_words if word in printed)
    assert leaked == [], f"the report carries words out of the test set: {leaked}"


def test_the_two_prefixes_stand_in_the_tool() -> None:
    """Fallstrick 3 of the research: fastembed does not add them for a model registered by hand."""
    source = TOOL_PATH.read_text(encoding="utf-8")
    assert source.count("query: ") >= 1
    assert source.count("passage: ") >= 1


def test_the_per_case_line_names_every_rank_and_only_identifiers() -> None:
    """Two summaries cannot be compared case by case, so the ranks themselves have to be readable."""
    metrics = quality.Metrics(cases=3, recall_at_1=1 / 3, recall_at_5=1.0, mrr=0.6)
    ranked = [("fr-01", 1), ("fr-02", 2), ("fr-03", 4)]
    arguments = (Path("/model/model.onnx"), Path("/model"), DATASET_DIR / "fr.jsonl", "on", "fp32")

    without = quality.format_report(*arguments, metrics, ranked)
    assert "per case" not in without

    with_ranks = quality.format_report(*arguments, metrics, ranked, per_case=True)
    assert "per case      fr-01 1, fr-02 2, fr-03 4" in with_ranks


def test_the_help_names_all_five_switches(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        quality.parse_args(["--help"])
    printed = capsys.readouterr().out
    for switch in ("--model", "--tokenizer", "--dataset", "--prefixes", "--vector-dtype"):
        assert switch in printed, switch
