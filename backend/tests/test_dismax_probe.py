"""The arithmetic of the disjunction_max probe 98d, held against a six field index.

98d runs inside the product container on the trip (MESS-09) and has never run.
What it measures there can only be read if three things hold here first: the per
word dismax keeps the hit set of the sum exactly, the figures overlap@10 and
RBO@10 are what their names say, and the output carries numbers and file ids and
never the text of a question (T-22-10). The decision rule is not in 98d and not
here; it stands in 00-ablauf.md.

The index follows the fixture of test_field_plan_ranking.py: through
``open_index``, field by field and never through keyword arguments. Unlike that
fixture the body fields are filled one by one with different texts, because the
case the per word shape exists for is a document that carries one word of the
question in one field and the other word in another.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest
from tantivy import Document, Index

from findling.api.resources import field_plan_for
from findling.config import SCHEMA_VERSION, SUPPORTED_LANGUAGES
from findling.index.open import LANGUAGES_MARK, SCHEMA_MARK, open_index
from findling.index.schema import (
    FIELD_BODY_DE,
    FIELD_BODY_EN,
    FIELD_BODY_ES,
    FIELD_FILE_ID,
    FIELD_MTIME,
    FIELD_NAME,
    FIELD_STORAGE_ID,
    FIELD_TITLE,
)
from findling.query.rewrite import FieldPlan

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
PROBE: Final = REPO_ROOT / "docs" / "measurements" / "2026-09-v13-messung" / "skripte" / "98d-dismax-probe.py"
CORPUS_BUILDER: Final = REPO_ROOT / "scripts" / "dev" / "build_load_corpus.py"

CONSTITUENTS: Final = (
    (Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt").read_text(encoding="utf-8").split()
)

# The example of 22-RESEARCH: the question is two words, and document 1 carries
# word A in one field and word B in another. The sum finds it, the per word
# dismax finds it, the whole line dismax does not.
QUESTION: Final = "haus garten"
SPLIT_HIT: Final = 1
ONE_FIELD_HIT: Final = 2
HALF_HIT: Final = 3
MANY_FIELD_HIT: Final = 4

# The long tail of document 4. Its three fields each carry both words in a long
# text, so each of them alone weighs less than the short German field of
# document 2 while the three together weigh more: the sum puts document 4
# first and the best field puts document 2 first. Fifteen words, found by trying
# 3, 8 and 15 against tantivy 0.26.2; the two shorter tails leave the order alone.
FILLER: Final = " ".join(["akte"] * 15)

# file id -> the body fields it fills and their text. Nothing else carries the
# two words: name and title are neutral, so the body fields decide.
BODIES: Final = {
    SPLIT_HIT: {FIELD_BODY_DE: "das haus steht am rand", FIELD_BODY_EN: "a garten behind it"},
    ONE_FIELD_HIT: {FIELD_BODY_DE: "haus und garten zu verkaufen"},
    HALF_HIT: {FIELD_BODY_DE: "ein haus ohne alles"},
    MANY_FIELD_HIT: {
        FIELD_BODY_DE: f"haus garten {FILLER}",
        FIELD_BODY_EN: f"haus garten {FILLER}",
        FIELD_BODY_ES: f"haus garten {FILLER}",
    },
}

# Every line the probe prints has one of these shapes, and the tokens after the
# first word are numbers, classes, form and figure names or id lists.
LINE_SHAPES: Final = re.compile(
    r"\A(?:anfrage \d+ [a-z0-9_]+(?: [a-z0-9_.,]+)*"
    r"|kennzahl [a-z0-9_]+ [a-z0-9_]+ [a-z0-9_.,]+"
    r"|treffermenge-ungleich anfragen? \d+(?: [a-z0-9_]+)?"
    r"|abbruch [a-z-]+)\Z"
)


def the_probe() -> ModuleType:
    spec = importlib.util.spec_from_file_location("dismax_probe_98d", PROBE)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe() -> ModuleType:
    return the_probe()


@pytest.fixture(scope="module")
def six_field_index(tmp_path_factory: pytest.TempPathFactory) -> Index:
    index = open_index(tmp_path_factory.mktemp("dismax-probe"), CONSTITUENTS)
    writer = index.writer(heap_size=15_000_000, num_threads=1)
    for file_id, bodies in BODIES.items():
        document = Document()
        document.add_unsigned(FIELD_FILE_ID, file_id)
        document.add_unsigned(FIELD_STORAGE_ID, 1)
        document.add_text(FIELD_NAME, f"akte-{file_id}.txt")
        document.add_text(FIELD_TITLE, "akte")
        for field, text in bodies.items():
            document.add_text(field, text)
        document.add_integer(FIELD_MTIME, 1_700_000_000 + file_id)
        writer.add_document(document)
    writer.commit()
    writer.wait_merging_threads()
    index.reload()
    return index


@pytest.fixture(scope="module")
def six_field_plan(six_field_index: Index) -> FieldPlan:
    plan = field_plan_for(
        {SCHEMA_MARK: str(SCHEMA_VERSION), LANGUAGES_MARK: ",".join(SUPPORTED_LANGUAGES)}, six_field_index
    )
    assert len([field for field in plan.fields if field.startswith("body_")]) == len(SUPPORTED_LANGUAGES)
    return plan


def test_the_per_word_dismax_keeps_the_hit_set_of_the_sum(
    probe: ModuleType, six_field_index: Index, six_field_plan: FieldPlan
) -> None:
    klasse, words = probe.klasse_von(QUESTION)
    assert klasse == probe.MEHRWORT
    total = probe.build_query(six_field_index, QUESTION, plan=six_field_plan).query
    expected = {SPLIT_HIT, ONE_FIELD_HIT, MANY_FIELD_HIT}
    assert set(probe.ranking(six_field_index, total)) == expected
    for tie in (0.0, 0.1):
        dismax = probe.dismax_query(six_field_index, words, six_field_plan, tie)
        assert set(probe.ranking(six_field_index, dismax)) == expected
        assert probe.same_hits(six_field_index, total, dismax)


def test_the_whole_line_dismax_loses_the_document_that_splits_its_words(
    probe: ModuleType, six_field_index: Index, six_field_plan: FieldPlan
) -> None:
    line = probe.line_dismax(six_field_index, QUESTION, six_field_plan, 0.0)
    found = set(probe.ranking(six_field_index, line))
    assert SPLIT_HIT not in found
    assert {ONE_FIELD_HIT, MANY_FIELD_HIT} <= found
    total = probe.build_query(six_field_index, QUESTION, plan=six_field_plan).query
    assert not probe.same_hits(six_field_index, total, line)


def test_the_dismax_changes_the_ranks_and_not_only_the_scores(
    probe: ModuleType, six_field_index: Index, six_field_plan: FieldPlan
) -> None:
    """The sum puts the document that answers through three fields first; dismax does not reward the count."""
    total = probe.build_query(six_field_index, QUESTION, plan=six_field_plan).query
    assert probe.ranking(six_field_index, total)[0] == MANY_FIELD_HIT
    _, words = probe.klasse_von(QUESTION)
    dismax = probe.dismax_query(six_field_index, words, six_field_plan, 0.0)
    assert probe.ranking(six_field_index, dismax)[0] == ONE_FIELD_HIT


def test_overlap_and_rbo_are_one_for_identical_and_nought_for_disjoint_lists(probe: ModuleType) -> None:
    same = list(range(1, 11))
    assert probe.overlap_at(same, same, 10) == 1.0
    assert probe.rbo_at(same, same, 10, p=0.9) == pytest.approx(1.0)
    other = list(range(11, 21))
    assert probe.overlap_at(same, other, 10) == 0.0
    assert probe.rbo_at(same, other, 10, p=0.9) == 0.0
    assert probe.overlap_at([], [], 10) == 1.0
    assert probe.rbo_at([], [], 10, p=0.9) == 1.0


def test_overlap_and_rbo_of_a_partial_overlap_are_the_hand_computed_values(probe: ModuleType) -> None:
    """Two hand computations, one below the depth of 10 and one at it.

    [1, 2] against [1, 3]: the depth stops at 2, A1 = 1 and A2 = 1/2, so
    RBO = (1 + 0.9 * 0.5) / (1 + 0.9) = 1.45 / 1.9 = 0.763157...

    1..10 against 1..5 followed by 11..15: A_d = 1 for d up to 5 and 5/d from 6
    to 10, so RBO = (sum of 0.9^(d-1) for d 1..5 + sum of 0.9^(d-1) * 5/d for d
    6..10) / (sum of 0.9^(d-1) for d 1..10) = 0.874924...; overlap@10 is 5/10.
    """
    assert probe.overlap_at([1, 2], [1, 3], 10) == 0.5
    assert probe.rbo_at([1, 2], [1, 3], 10, p=0.9) == pytest.approx(1.45 / 1.9)
    head = [1, 2, 3, 4, 5]
    assert probe.overlap_at([*head, 6, 7, 8, 9, 10], [*head, 11, 12, 13, 14, 15], 10) == 0.5
    assert probe.rbo_at([*head, 6, 7, 8, 9, 10], [*head, 11, 12, 13, 14, 15], 10, p=0.9) == pytest.approx(
        0.8749242036699413
    )
    assert probe.mean_rank_shift([1, 2, 3], [3, 2, 1]) == pytest.approx(4 / 3)
    assert probe.mean_rank_shift([1], [2]) is None


@pytest.mark.parametrize(
    ("line", "klasse"),
    [
        ('"drei Monate"', "rueckfall"),
        ("Vertrag AND Frist", "rueckfall"),
        ("type:pdf bescheid", "rueckfall"),
        ("(haus garten)", "rueckfall"),
        ("-haus garten", "rueckfall"),
        ("Beschluss Antrag", "rueckfall"),
        ("Vertrag", "einwort"),
        ("Kuendigung", "einwort"),
        ("Vertrag beenden", "mehrwort"),
        ("", "leer"),
    ],
)
def test_a_line_with_an_operator_a_phrase_or_a_variant_falls_back(probe: ModuleType, line: str, klasse: str) -> None:
    assert probe.klasse_von(line)[0] == klasse


def test_a_fallback_line_is_measured_with_the_sum_alone(
    probe: ModuleType, six_field_index: Index, six_field_plan: FieldPlan, capsys: pytest.CaptureFixture[str]
) -> None:
    assert probe.measure(six_field_index, six_field_plan, ['"haus garten"'], repetitions=1) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "anfrage 1 klasse rueckfall" in lines
    forms = {line.split()[3] for line in lines if line.startswith("anfrage 1 treffer ")}
    assert forms == {"summe"}


def test_the_output_carries_numbers_and_ids_and_never_the_text_of_a_question(
    probe: ModuleType, six_field_index: Index, six_field_plan: FieldPlan, capsys: pytest.CaptureFixture[str]
) -> None:
    words = probe.read_wordlist(CORPUS_BUILDER)
    sample = probe.stichprobe(words, 22, 4, 4)
    questions = (QUESTION, "haus", *sample)
    assert probe.measure(six_field_index, six_field_plan, questions, repetitions=1) == 0
    output = capsys.readouterr().out
    lines = output.splitlines()
    assert lines
    for line in lines:
        assert LINE_SHAPES.match(line), line
    tokens = set(output.lower().split())
    for question in questions:
        for word in question.lower().split():
            assert word not in tokens, word
    assert "anfrage 1 treffer summe 3" in lines
    assert "anfrage 1 treffer dismax_t00 3" in lines
    assert any(line.startswith("kennzahl rbo10_gegen_altplan dismax_t00 ") for line in lines)


def test_unequal_hit_sets_end_the_probe_with_49(
    probe: ModuleType,
    six_field_index: Index,
    six_field_plan: FieldPlan,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A per word dismax that forgets a field is a wrong probe, and it has to say so."""
    first_field = FieldPlan(
        fields=six_field_plan.fields[:1], boosts=six_field_plan.boosts, title_only=six_field_plan.title_only
    )
    original = probe.word_dismax
    monkeypatch.setattr(probe, "word_dismax", lambda index, word, _plan, tie: original(index, word, first_field, tie))
    assert probe.measure(six_field_index, six_field_plan, [QUESTION], repetitions=1) == 49
    lines = capsys.readouterr().out.splitlines()
    assert "treffermenge-ungleich anfrage 1 dismax_t00" in lines
    assert not any(line.startswith("kennzahl ") for line in lines)


def test_the_probe_ends_with_2_without_a_readable_index(
    probe: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(probe, "read_side", lambda: None)
    assert probe.main() == 2
    assert capsys.readouterr().out.splitlines() == ["abbruch kein-index"]


def test_the_sample_comes_out_of_the_word_list_and_is_fixed_by_its_seed(probe: ModuleType, tmp_path: Path) -> None:
    words = probe.read_wordlist(CORPUS_BUILDER)
    assert len(words) >= 100
    assert probe.stichprobe(words, 22, 3, 3) == probe.stichprobe(words, 22, 3, 3)
    assert len(probe.stichprobe(words, 22, 3, 3)) == 6
    assert probe.read_wordlist(tmp_path / "nicht-da.py") == ()


def test_the_probe_goes_through_the_product_functions_and_holds_no_decision_rule() -> None:
    text = PROBE.read_text(encoding="utf-8")
    for needle in ("read_side", "open_index", "field_plan_for", "build_query", "LEGACY_PLAN", "disjunction_max_query"):
        assert needle in text, needle
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    for rule_word in ("vorteil", "entscheid", "umsetzen"):
        assert rule_word not in code.lower(), rule_word
