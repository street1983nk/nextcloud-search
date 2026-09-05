"""The gate over the wave 0 measuring tool of phase 6.

Three numbers decide this phase, and until this file existed all three were
estimates: how many characters a German token has (A1), how many tokens a second
the quantised model produces on two shared ARM cores (A2 and A3), and how long a
full brute force scan over a vec0 table takes (the ground under A4 and under the
choice between int8, bit vectors and usearch).

What this file can prove and what it cannot, said plainly, because the difference
is the whole reason the workflow exists. It proves that the tool measures the
right thing, reports it with its hardware, refuses to invent a number when its
input is missing, and never prints a word it read. It proves nothing about the
values: those come from a run on real aarch64 hardware and land in
``docs/measurements/2026-09-05-welle0-arm64/README.md``.

The model is not here. It is a constant of the image (118 MB of int8 ONNX at
``$FINDLING_EMBED_MODEL_DIR``) and no test in this repository downloads it, so
the two model bound modes are tested against substitutes that are honest about
what they replace: a miniature BPE tokenizer trained in three lines for the
character counting, and a stand in for the inference session for the throughput
loop. The extension is a different case and needs no substitute: sqlite-vec is an
ordinary dependency, so the scan latency mode runs here for real, only smaller.
"""

from __future__ import annotations

import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import sqlite_vec
from tokenizers import Tokenizer, models, pre_tokenizers, trainers

from findling.embed import bench

if TYPE_CHECKING:
    from collections.abc import Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS = REPO_ROOT / "testdata" / "corpus"

# The German the miniature tokenizer is trained on and the text the character
# counting is measured over. Written without umlauts, the same way the analyser
# measurement and index/bench.py are, so the byte count is the character count on
# every machine and the sample says nothing about any real document.
_GERMAN = (
    "Die Kuendigungsfrist betraegt drei Monate und beginnt am Ersten des Monats. "
    "Die Rechnung wurde im Jahresabschluss der Verwaltung geprueft und freigegeben. "
    "Der Vertrag regelt die Betriebskosten, die Nebenkosten und die Kaution. "
    "Die Sitzungsvorlage des Ausschusses nennt den Haushalt und die Satzung."
)


def _tokenizer_dir(root: Path) -> Path:
    """A directory shaped like ``$FINDLING_EMBED_MODEL_DIR``, with a tiny tokenizer in it.

    Sixty merges over four sentences, which is a laughable vocabulary and exactly
    the point: the ratio it produces is meaningless and the arithmetic around it
    is what is under test. The real vocabulary has 250.002 entries and weighs 17
    MB, and it arrives in the image rather than in a test fixture.
    """
    # S106 reads "<unk>" as a hardcoded password. It is the unknown token of a
    # BPE vocabulary and there is no secret anywhere in this file.
    tokenizer = Tokenizer(models.BPE(unk_token="<unk>"))  # noqa: S106
    tokenizer.pre_tokenizer = pre_tokenizers.Whitespace()
    tokenizer.train_from_iterator(
        [_GERMAN],
        trainers.BpeTrainer(vocab_size=60, special_tokens=["<unk>"]),
    )
    directory = root / "model"
    directory.mkdir(parents=True, exist_ok=True)
    tokenizer.save(str(directory / "tokenizer.json"))
    return directory


def _vec0_path() -> str:
    """The extension of the installed wheel, with the suffix SQLite would append.

    In the image this value is ``$FINDLING_VEC0_PATH`` and nothing else; the tool
    refuses to guess, which is one of the tests below. Here the guess is made by
    the test rather than by the tool, so that the measurement itself can be run.
    """
    return sqlite_vec.loadable_path() + (".dll" if sys.platform == "win32" else ".so")


def _pairs(lines: Sequence[str]) -> dict[str, str]:
    """The key=value pairs of an output block, flattened into one mapping.

    Row lines (``scan size=... p50_ms=...``) carry their own keys and are read by
    the tests that care about them; this helper is for the header, where every
    key appears once.
    """
    found: dict[str, str] = {}
    for line in lines:
        for token in line.split():
            key, sign, value = token.partition("=")
            if sign:
                found.setdefault(key, value)
    return found


def _rows(lines: Sequence[str], prefix: str) -> list[dict[str, str]]:
    """Every row line with the given first word, as a list of mappings."""
    rows: list[dict[str, str]] = []
    for line in lines:
        parts = line.split()
        if not parts or parts[0] != prefix:
            continue
        row: dict[str, str] = {}
        for token in parts[1:]:
            key, sign, value = token.partition("=")
            if sign:
                row[key] = value
        rows.append(row)
    return rows


# -- behaviour 1: characters per token -------------------------------------


def test_chars_per_token_counts_characters_and_tokens(tmp_path: Path) -> None:
    source = tmp_path / "text"
    source.mkdir()
    (source / "a.txt").write_text(_GERMAN, encoding="utf-8")
    (source / "b.txt").write_text(_GERMAN, encoding="utf-8")

    lines = bench.run_chars_per_token(_tokenizer_dir(tmp_path), source, limit=bench.DEFAULT_CHARACTER_LIMIT)
    found = _pairs(lines)

    assert found["mode"] == bench.MODE_CHARS
    assert int(found["files"]) == 2
    assert int(found["characters"]) == 2 * len(_GERMAN)
    assert int(found["tokens"]) > 0
    # The one number this mode exists for, and it has to be the quotient of the
    # two above rather than an average of per file quotients.
    assert float(found["chars_per_token"]) == pytest.approx(int(found["characters"]) / int(found["tokens"]), abs=0.001)


def test_chars_per_token_prints_no_word_and_no_file_name(tmp_path: Path) -> None:
    # T-06-06. This path sees real documents in the field, so the measurement is
    # only allowed to print numbers. The check is the one T-02-14 asks for: every
    # word of the text is looked for in the output, and the file names too.
    source = tmp_path / "text"
    source.mkdir()
    (source / "kuendigung-mueller.txt").write_text(_GERMAN, encoding="utf-8")

    output = "\n".join(bench.run_chars_per_token(_tokenizer_dir(tmp_path), source, limit=bench.DEFAULT_CHARACTER_LIMIT))

    for word in re.findall(r"[A-Za-z]{4,}", _GERMAN):
        assert word.lower() not in output.lower(), f"the output carries the word {word!r} from the text it read"
    assert "kuendigung-mueller" not in output
    assert str(source) not in output


def test_chars_per_token_reads_the_real_corpus_of_this_repository(tmp_path: Path) -> None:
    # The anti vacuity clause of the mode: it has to find German text in the
    # place the plan names, not only in a fixture a test just wrote.
    lines = bench.run_chars_per_token(_tokenizer_dir(tmp_path), CORPUS, limit=bench.DEFAULT_CHARACTER_LIMIT)
    found = _pairs(lines)

    assert int(found["files"]) >= 3
    assert int(found["characters"]) > 500


def test_chars_per_token_stops_at_the_character_limit(tmp_path: Path) -> None:
    source = tmp_path / "text"
    source.mkdir()
    (source / "a.txt").write_text(_GERMAN * 20, encoding="utf-8")

    found = _pairs(bench.run_chars_per_token(_tokenizer_dir(tmp_path), source, limit=100))

    assert int(found["characters"]) == 100


def test_chars_per_token_accepts_a_single_file(tmp_path: Path) -> None:
    # The German word list of the image is one file at a fixed path, and it is
    # the vocabulary heavy end of the same question. A reader that only walked
    # directories could not be pointed at it.
    source = tmp_path / "ngerman"
    source.write_text(_GERMAN, encoding="utf-8")

    found = _pairs(bench.run_chars_per_token(_tokenizer_dir(tmp_path), source, limit=bench.DEFAULT_CHARACTER_LIMIT))

    assert int(found["files"]) == 1
    assert int(found["characters"]) == len(_GERMAN)


def test_chars_per_token_survives_a_legacy_encoding(tmp_path: Path) -> None:
    # 08-legacy-encoding.txt of the reference corpus is cp1252, and German
    # holdings from before 2010 are full of it. A decoder that only knew utf-8
    # would either crash or drop the file, and a dropped file is a silently
    # smaller sample.
    source = tmp_path / "text"
    source.mkdir()
    (source / "alt.txt").write_bytes("Bescheid über die Grundsteuer".encode("cp1252"))

    found = _pairs(bench.run_chars_per_token(_tokenizer_dir(tmp_path), source, limit=bench.DEFAULT_CHARACTER_LIMIT))

    assert int(found["files"]) == 1
    assert int(found["characters"]) == len("Bescheid über die Grundsteuer")


# -- behaviour 2: tokens per second ----------------------------------------


def test_tokens_per_second_reports_the_slow_end_next_to_the_median(tmp_path: Path) -> None:
    # A stand in for the inference session, because the model is a constant of
    # the image. What is under test is the arithmetic around it: that a p95 of a
    # throughput is the slow end and not the fast one, and that the batch and the
    # sequence travel with the number.
    # Five, not four: the first call is the warm up round the tool throws away,
    # and a test that supplied only the measured ones would pass on a tool that
    # counted the load time into the throughput.
    durations = iter([0.001, 0.010, 0.010, 0.010, 0.100])

    def run_batch(_ids: list[list[int]]) -> None:
        time.sleep(next(durations))

    lines = bench.run_tokens_per_second(
        _tokenizer_dir(tmp_path),
        run_batch=run_batch,
        batch=2,
        sequence=8,
        rounds=4,
        threads=2,
    )
    found = _pairs(lines)

    assert found["mode"] == bench.MODE_TOKENS
    assert int(found["batch"]) == 2
    assert int(found["sequence"]) == 8
    assert int(found["threads"]) == 2
    assert int(found["tokens_per_round"]) == 16
    # The p95 duration is the slow round, so the tokens per second beside it has
    # to be the smaller of the two. A p95 that came out higher than the p50 would
    # be a throughput quoted from its best moment.
    assert float(found["p95_ms"]) > float(found["p50_ms"])
    assert float(found["tokens_per_second_p95"]) < float(found["tokens_per_second_p50"])


def test_tokens_per_second_builds_full_length_batches(tmp_path: Path) -> None:
    # No padding anywhere: a padded batch measures the padding as well and the
    # tokens per second would be quoted over tokens that carry nothing.
    tokenizer = Tokenizer.from_file(str(_tokenizer_dir(tmp_path) / "tokenizer.json"))

    ids = bench.synthetic_batch(tokenizer, batch=3, sequence=17)

    assert len(ids) == 3
    assert {len(row) for row in ids} == {17}


def test_tokens_per_second_needs_at_least_one_round(tmp_path: Path) -> None:
    with pytest.raises(bench.BenchError, match="rounds"):
        bench.run_tokens_per_second(
            _tokenizer_dir(tmp_path),
            run_batch=lambda _ids: None,
            batch=1,
            sequence=4,
            rounds=0,
            threads=1,
        )


# -- behaviour 3 and 4: scan latency, int8 and bit --------------------------


@pytest.mark.parametrize("vector_type", [bench.VECTOR_INT8, bench.VECTOR_BIT])
def test_scan_latency_measures_both_storage_types(tmp_path: Path, vector_type: str) -> None:
    lines = bench.run_scan_latency(
        _vec0_path(),
        directory=tmp_path,
        sizes=(200, 400),
        queries=5,
        vector_type=vector_type,
        cache=bench.CACHE_WARM,
    )
    found = _pairs(lines)
    rows = _rows(lines, bench.ROW_SCAN)

    assert found["mode"] == bench.MODE_SCAN
    assert found["vector_type"] == vector_type
    assert int(found["k"]) == bench.NEIGHBOURS
    assert int(found["dimensions"]) == bench.DIMENSIONS
    assert [int(row["size"]) for row in rows] == [200, 400]
    for row in rows:
        assert row["cache"] == bench.CACHE_WARM
        # A warm series drops nothing, and a "true" here would read as if it had.
        assert row["cache_dropped"] == "n/a"
        assert float(row["p50_ms"]) > 0
        assert float(row["p95_ms"]) >= float(row["p50_ms"])
        assert int(row["neighbours"]) == bench.NEIGHBOURS


def test_scan_latency_stores_bit_vectors_eight_times_smaller() -> None:
    # The whole reason the bit column is measured next to the int8 one: 48 bytes
    # against 384. If both widths came out the same, the comparison the report
    # draws would be between two identical things.
    assert bench.vector_bytes(bench.VECTOR_INT8) == bench.DIMENSIONS
    assert bench.vector_bytes(bench.VECTOR_BIT) == bench.DIMENSIONS // 8


def test_scan_latency_vectors_are_the_same_on_every_machine() -> None:
    # A fixed seed is what makes two runs on two architectures comparable. The
    # construction is SHA-256 in counter mode, the same one the corpus builder
    # and the A12 probe use, so no float conversion sits between the seed and
    # the bytes.
    assert bench.vector(7, bench.DIMENSIONS) == bench.vector(7, bench.DIMENSIONS)
    assert bench.vector(7, bench.DIMENSIONS) != bench.vector(8, bench.DIMENSIONS)
    assert len(bench.vector(7, 48)) == 48


# -- behaviour 5: cold says when it could not be cold -----------------------


def test_cold_says_out_loud_when_the_page_cache_could_not_be_dropped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # T-06-09, and the reason this mode has a switch at all. A cold run that
    # silently reports a warm number is the one failure of this tool that would
    # never be noticed, because the number looks perfectly reasonable.
    monkeypatch.setattr(bench, "drop_page_cache", lambda: (False, "PermissionError: [Errno 1] not permitted"))

    lines = bench.run_scan_latency(
        _vec0_path(),
        directory=tmp_path,
        sizes=(200,),
        queries=3,
        vector_type=bench.VECTOR_INT8,
        cache=bench.CACHE_COLD,
    )
    rows = _rows(lines, bench.ROW_SCAN)

    assert rows
    for row in rows:
        assert row["cache"] == bench.CACHE_COLD
        assert row["cache_dropped"] == "false"
    joined = "\n".join(lines)
    assert "cold_not_enforced" in joined
    assert "PermissionError" in joined


def test_cold_reports_the_drop_when_it_worked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The counter sample. Without it the test above would also pass on a tool
    # that reports "not enforced" unconditionally.
    monkeypatch.setattr(bench, "drop_page_cache", lambda: (True, None))

    lines = bench.run_scan_latency(
        _vec0_path(),
        directory=tmp_path,
        sizes=(200,),
        queries=3,
        vector_type=bench.VECTOR_INT8,
        cache=bench.CACHE_COLD,
    )
    rows = _rows(lines, bench.ROW_SCAN)

    assert [row["cache_dropped"] for row in rows] == ["true"]
    assert "cold_not_enforced" not in "\n".join(lines)


def test_both_runs_the_warm_and_the_cold_series_over_one_fill(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The difference is the statement, not the mean (06-RESEARCH.md 2.2), and a
    # difference between two separately filled tables would carry the fill
    # variance as well.
    monkeypatch.setattr(bench, "drop_page_cache", lambda: (True, None))

    lines = bench.run_scan_latency(
        _vec0_path(),
        directory=tmp_path,
        sizes=(200,),
        queries=3,
        vector_type=bench.VECTOR_INT8,
        cache=bench.CACHE_BOTH,
    )
    rows = _rows(lines, bench.ROW_SCAN)

    assert [row["cache"] for row in rows] == [bench.CACHE_WARM, bench.CACHE_COLD]
    assert {int(row["size"]) for row in rows} == {200}


# -- behaviour 6: no number without its hardware ----------------------------


def test_every_mode_prints_the_architecture_and_the_visible_cpus(tmp_path: Path) -> None:
    # T-06-07. A number without its hardware is a claim that will be quoted at
    # the wrong machine, and every one of these three numbers is architecture
    # dependent in a different way.
    source = tmp_path / "text"
    source.mkdir()
    (source / "a.txt").write_text(_GERMAN, encoding="utf-8")
    model = _tokenizer_dir(tmp_path)

    blocks = [
        bench.run_chars_per_token(model, source, limit=bench.DEFAULT_CHARACTER_LIMIT),
        bench.run_tokens_per_second(model, run_batch=lambda _ids: None, batch=1, sequence=4, rounds=2, threads=1),
        bench.run_scan_latency(
            _vec0_path(),
            directory=tmp_path,
            sizes=(200,),
            queries=3,
            vector_type=bench.VECTOR_INT8,
            cache=bench.CACHE_WARM,
        ),
    ]

    for lines in blocks:
        found = _pairs(lines)
        assert found["arch"] == bench.architecture()
        assert int(found["cpus"]) >= 1


# -- behaviour 7: a missing input is an error, never a zero -----------------


def test_a_missing_extension_variable_is_a_named_refusal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FINDLING_VEC0_PATH", raising=False)

    with pytest.raises(bench.BenchError, match="FINDLING_VEC0_PATH"):
        bench.extension_path()


def test_a_missing_model_variable_is_a_named_refusal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FINDLING_EMBED_MODEL_DIR", raising=False)

    with pytest.raises(bench.BenchError, match="FINDLING_EMBED_MODEL_DIR"):
        bench.model_directory()


def test_a_model_directory_without_a_tokenizer_is_a_named_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FINDLING_EMBED_MODEL_DIR", str(tmp_path))

    with pytest.raises(bench.BenchError, match=r"tokenizer\.json"):
        bench.load_tokenizer(bench.model_directory())


def test_a_text_source_without_readable_text_is_a_named_refusal(tmp_path: Path) -> None:
    empty = tmp_path / "text"
    empty.mkdir()

    with pytest.raises(bench.BenchError, match="no readable text"):
        bench.run_chars_per_token(_tokenizer_dir(tmp_path), empty, limit=bench.DEFAULT_CHARACTER_LIMIT)


def test_a_path_that_is_not_an_extension_is_a_named_refusal(tmp_path: Path) -> None:
    decoy = tmp_path / "vec0.so"
    decoy.write_bytes(b"this is not a shared object")

    with pytest.raises(bench.BenchError, match="could not be loaded"):
        bench.run_scan_latency(
            str(decoy),
            directory=tmp_path,
            sizes=(10,),
            queries=1,
            vector_type=bench.VECTOR_INT8,
            cache=bench.CACHE_WARM,
        )


def test_main_turns_a_refusal_into_a_non_zero_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # The whole chain, because a BenchError that main swallowed would still end
    # in a green run and an empty artefact.
    monkeypatch.delenv("FINDLING_VEC0_PATH", raising=False)

    code = bench.main(["--mode", bench.MODE_SCAN, "--sizes", "10", "--queries", "1", "--db-dir", str(tmp_path)])

    assert code != 0
    assert "FINDLING_VEC0_PATH" in capsys.readouterr().err


def test_main_refuses_a_scratch_directory_that_does_not_exist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # mkdir is a forbidden identifier of the read-only gate (IDX-07, invariant
    # 2), so this module creates no directory anywhere and says so instead. The
    # test is here rather than only in the gate, because the gate would stay
    # green on a version that silently measured into a temporary directory it
    # was not asked for.
    monkeypatch.setenv("FINDLING_VEC0_PATH", _vec0_path())

    code = bench.main(
        ["--mode", bench.MODE_SCAN, "--sizes", "10", "--queries", "1", "--db-dir", str(tmp_path / "absent")]
    )

    assert code != 0
    assert "does not exist" in capsys.readouterr().err


def test_main_measures_and_exits_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("FINDLING_VEC0_PATH", _vec0_path())

    code = bench.main(
        ["--mode", bench.MODE_SCAN, "--sizes", "300", "--queries", "3", "--cache", "warm", "--db-dir", str(tmp_path)]
    )
    out = capsys.readouterr().out

    assert code == 0
    found = _pairs(out.splitlines())
    assert found["arch"] == bench.architecture()
    assert _rows(out.splitlines(), bench.ROW_SCAN)


# -- the defaults the plan pins --------------------------------------------


def test_the_default_size_series_covers_success_criterion_four() -> None:
    # Criterion 4 of the phase: the vector schema is fixed only after a load test
    # over at least 50.000 synthetic documents, which is 100.000 chunks at the
    # two chunk cap of D-01. The series has to reach that number, and beyond it,
    # or the criterion is asserted by a run that never touched it.
    assert 100_000 in bench.DEFAULT_SIZES
    assert max(bench.DEFAULT_SIZES) >= 1_000_000


def test_the_dimension_and_the_neighbour_count_are_the_ones_of_the_phase() -> None:
    assert bench.DIMENSIONS == 384
    assert bench.NEIGHBOURS == 50


def test_the_source_carries_no_dashes_that_the_project_rule_forbids() -> None:
    # Em dash and en dash. The rule is a project rule and it is cheapest to hold
    # where the file is written rather than in a review.
    source = Path(bench.__file__).read_text(encoding="utf-8")

    # Written as code points rather than as the characters themselves, so that
    # this file does not carry the very thing it forbids.
    assert chr(0x2014) not in source
    assert chr(0x2013) not in source


# -- the extension really is what is being measured -------------------------


def test_the_filled_table_is_a_vec0_table(tmp_path: Path) -> None:
    # The anti vacuity clause of the scan mode. A measurement that had quietly
    # fallen back to an ordinary table would still print plausible milliseconds,
    # and they would be the milliseconds of a full table scan in SQLite rather
    # than of a brute force KNN in vec0.
    database = tmp_path / "probe.db"
    connection = bench.open_database(database, _vec0_path())
    try:
        bench.fill(connection, size=100, vector_type=bench.VECTOR_INT8)
        sql = connection.execute("SELECT sql FROM sqlite_master WHERE name = ?", (bench.TABLE,)).fetchone()
    finally:
        connection.close()

    assert sql is not None
    assert "USING vec0" in sql[0]
    assert f"int8[{bench.DIMENSIONS}]" in sql[0]


def test_a_query_returns_the_requested_number_of_neighbours(tmp_path: Path) -> None:
    database = tmp_path / "probe.db"
    connection = bench.open_database(database, _vec0_path())
    try:
        bench.fill(connection, size=200, vector_type=bench.VECTOR_INT8)
        rows = bench.query_once(connection, vector_type=bench.VECTOR_INT8, number=3)
    finally:
        connection.close()

    assert rows == bench.NEIGHBOURS


def test_open_database_reports_a_missing_extension_file(tmp_path: Path) -> None:
    with pytest.raises(bench.BenchError, match="could not be loaded"):
        bench.open_database(tmp_path / "probe.db", str(tmp_path / "absent.so"))


def test_drop_page_cache_never_raises() -> None:
    # It runs on Windows, in an unprivileged container and as root, and only one
    # of those three can succeed. The contract is a pair, never an exception:
    # the caller has to be able to write the failure down instead of dying on it.
    dropped, note = bench.drop_page_cache()

    assert isinstance(dropped, bool)
    assert note is None or isinstance(note, str)
    if not dropped:
        assert note


def test_sqlite_is_new_enough_for_the_extension() -> None:
    # Not a property of this module, and here on purpose: every number of the
    # scan mode is a property of this SQLite, and the report quotes it.
    assert sqlite3.sqlite_version_info >= (3, 41)
