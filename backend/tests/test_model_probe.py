"""The model child of the check: protocol, deadline, kill, hardening, import hygiene.

The process cases start real spawn children. The rehearsals of
``model_probe._rehearse`` stand in for a model that hangs, runs out of memory or
throws, for the reason ``extract/sandbox.py`` gives its probe jobs: a real
model that hangs on cue would test onnxruntime and not the guard. The one case
with real weights needs the int8 of the image and Linux, and says so when it
skips.
"""

from __future__ import annotations

import ast
import os
import signal
import sys
import threading
import time
from pathlib import Path

import pytest

from findling.embed import model, model_probe
from findling.embed.model_probe import (
    MEASURE_FAILED,
    MEASURE_KILLED,
    MEASURE_NO_MEMORY,
    MEASURE_OK,
    MEASURE_TIMEOUT,
    ModelMeasure,
)

PROBE_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "embed" / "model_probe.py"

MODEL_ENV = "FINDLING_EMBED_MODEL_DIR"

ONLY_POSIX = pytest.mark.skipif(
    sys.platform == "win32",
    reason="sessions, process groups and SIGKILL are POSIX; the container this ships in is Linux",
)


def _shipped_model() -> Path | None:
    """The model directory of the image, or None where there is none."""
    configured = os.environ.get(MODEL_ENV, "").strip()
    if not configured:
        return None
    directory = Path(configured)
    if (directory / "model.onnx").is_file() and (directory / "tokenizer.json").is_file():
        return directory
    return None


# ---------------------------------------------------------------------------
# The protocol, without a process.
# ---------------------------------------------------------------------------


def test_the_outcomes_are_a_closed_set_of_five() -> None:
    assert model_probe.MEASURE_OUTCOMES == frozenset({"ok", "timeout", "killed", "failed", "no_memory"})


def test_a_measure_names_its_delta() -> None:
    measure = ModelMeasure(outcome=MEASURE_OK, rss_before=100, rss_after=350, rate_milli=4000)
    assert measure.delta == 250


def test_a_well_formed_answer_becomes_a_measure() -> None:
    answer = (MEASURE_OK, 1000, 5000, 3500)
    assert model_probe._read_answer(answer) == ModelMeasure(MEASURE_OK, 1000, 5000, 3500)


@pytest.mark.parametrize(
    "answer",
    [
        None,
        "ok",
        (MEASURE_OK, 1, 2),
        (MEASURE_OK, 1, 2, 3, 4),
        ("sideways", 1, 2, 3),
        (MEASURE_OK, "1", 2, 3),
        (MEASURE_OK, 1, 2, 3.5),
        (MEASURE_OK, True, 2, 3),
        (MEASURE_OK, -1, 2, 3),
        (MEASURE_OK, 2, 1, 3),
        (MEASURE_OK, 1, 2, 0),
        (MEASURE_TIMEOUT, 0, 0, 0),
        (MEASURE_KILLED, 0, 0, 0),
    ],
)
def test_anything_else_is_a_failed_measure(answer: object) -> None:
    """A child can only report ok, failed or no_memory; timeout and killed are the parent's words."""
    assert model_probe._read_answer(answer).outcome == MEASURE_FAILED


@pytest.mark.parametrize("outcome", [MEASURE_FAILED, MEASURE_NO_MEMORY])
def test_a_failure_answer_carries_no_numbers(outcome: str) -> None:
    assert model_probe._read_answer((outcome, 0, 0, 0)) == ModelMeasure(outcome, 0, 0, 0)


def test_the_rate_is_milli_passages_per_second() -> None:
    # 8 passages in two seconds: four passages per second, 4000 milli.
    assert model_probe._rate_milli(2000) == 4000
    # Never a division by nought, and never nought itself.
    assert model_probe._rate_milli(0) == 8_000_000
    assert model_probe._rate_milli(10**9) == 1


def test_the_fixed_batch_is_eight_long_passages_and_no_user_data() -> None:
    assert len(model_probe.PASSAGES) == model_probe.PROBE_BATCH == 8
    assert model_probe.PROBE_SEQUENCE_LEN == 512
    assert all(len(passage) > 4 * model_probe.PROBE_SEQUENCE_LEN for passage in model_probe.PASSAGES)


def test_an_unknown_precision_is_refused() -> None:
    with pytest.raises(ValueError, match="precision"):
        model_probe.measure("fp16", Path("nowhere"), timeout_seconds=1.0)  # type: ignore[arg-type]


def test_the_weights_follow_the_precision(tmp_path: Path) -> None:
    image = tmp_path / "image"
    volume = tmp_path / "volume"
    assert model_probe._weights_of("int8", volume, image) == image / "model.onnx"
    assert model_probe._weights_of("fp32", volume, image) == volume / "multilingual-e5-small-fp32" / "model.onnx"


# ---------------------------------------------------------------------------
# Hardening and import hygiene, read from the source.
# ---------------------------------------------------------------------------


def _child_source() -> str:
    tree = ast.parse(PROBE_SOURCE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_child_main":
            segment = ast.get_source_segment(PROBE_SOURCE.read_text(encoding="utf-8"), node)
            assert segment is not None
            return segment
    raise AssertionError("_child_main is missing")


def test_the_child_hardens_itself_before_anything_heavy_is_imported() -> None:
    source = _child_source()
    order = [
        "os.setsid()",
        "os.nice(SANDBOX_NICE)",
        "_lower_own_standing()",
        "_shed_secrets()",
        "_rehearse(",
        "import onnxruntime",
    ]
    positions = [source.find(marker) for marker in order]
    assert all(position >= 0 for position in positions), dict(zip(order, positions, strict=True))
    assert positions == sorted(positions)


def test_the_child_carries_no_address_space_cap() -> None:
    """onnxruntime reserves far more virtual space than it uses; a cap would fail the load (A2)."""
    assert "_limit_address_space" not in PROBE_SOURCE.read_text(encoding="utf-8")
    assert "RLIMIT_AS" not in _child_source()


def test_the_module_imports_no_model_library_at_module_level() -> None:
    tree = ast.parse(PROBE_SOURCE.read_text(encoding="utf-8"))
    heavy = {"onnxruntime", "fastembed", "numpy", "tokenizers"}
    for node in tree.body:
        if isinstance(node, ast.Import):
            assert not {alias.name.split(".")[0] for alias in node.names} & heavy
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in heavy


def test_the_sandbox_parts_are_imported_not_copied() -> None:
    source = PROBE_SOURCE.read_text(encoding="utf-8")
    assert source.count("from findling.extract.sandbox import") == 1
    for name in ("def _shed_secrets", "def _lower_own_standing", "def _kill_child_tree", "get_context("):
        assert name not in source


def test_the_probe_is_never_the_engine_of_the_main_process() -> None:
    source = PROBE_SOURCE.read_text(encoding="utf-8")
    assert "swap_engine" not in source
    assert "EmbeddingModel(" not in source


# ---------------------------------------------------------------------------
# Real children, rehearsed.
# ---------------------------------------------------------------------------


def test_a_child_over_the_deadline_is_killed_and_reads_as_timeout(tmp_path: Path) -> None:
    started: list[int] = []
    begun = time.monotonic()
    result = model_probe._measure(
        "int8", tmp_path, timeout_seconds=3.0, embed_model_dir=tmp_path, rehearsal="sleep", on_start=started.append
    )
    assert result == ModelMeasure(MEASURE_TIMEOUT, 0, 0, 0)
    assert time.monotonic() - begun < 30
    assert started
    if sys.platform != "win32":
        # The child made itself a session leader, so its group id is its pid,
        # and after the group kill that group is empty.
        with pytest.raises(ProcessLookupError):
            os.killpg(started[0], 0)


def test_a_memory_error_in_the_child_reads_as_no_memory(tmp_path: Path) -> None:
    result = model_probe._measure(
        "int8", tmp_path, timeout_seconds=60.0, embed_model_dir=tmp_path, rehearsal="no_memory"
    )
    assert result == ModelMeasure(MEASURE_NO_MEMORY, 0, 0, 0)


def test_any_other_exception_in_the_child_reads_as_failed(tmp_path: Path) -> None:
    result = model_probe._measure("int8", tmp_path, timeout_seconds=60.0, embed_model_dir=tmp_path, rehearsal="fail")
    assert result == ModelMeasure(MEASURE_FAILED, 0, 0, 0)


def test_missing_weights_read_as_failed_and_load_nothing_in_the_parent(tmp_path: Path) -> None:
    loads, unloads = model.load_count(), model.unload_count()
    result = model_probe.measure("fp32", tmp_path, timeout_seconds=60.0)
    assert result.outcome == MEASURE_FAILED
    assert (model.load_count(), model.unload_count()) == (loads, unloads)


def test_the_child_leaves_the_parent_environment_alone(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_SECRET", "stays-in-the-parent")
    model_probe._measure("int8", tmp_path, timeout_seconds=60.0, embed_model_dir=tmp_path, rehearsal="fail")
    assert os.environ["APP_SECRET"] == "stays-in-the-parent"


@ONLY_POSIX
def test_a_kill_from_outside_reads_as_killed(tmp_path: Path) -> None:
    started: list[int] = []
    ready = threading.Event()

    def note(pid: int) -> None:
        started.append(pid)
        ready.set()

    results: list[ModelMeasure] = []
    runner = threading.Thread(
        target=lambda: results.append(
            model_probe._measure(
                "int8", tmp_path, timeout_seconds=60.0, embed_model_dir=tmp_path, rehearsal="sleep", on_start=note
            )
        )
    )
    runner.start()
    assert ready.wait(30)
    # Give the child the moment to reach its rehearsal, then do what the OOM
    # killer does: SIGKILL on the one process, not on the group.
    time.sleep(2.0)
    os.kill(started[0], signal.SIGKILL)
    runner.join(30)
    assert results == [ModelMeasure(MEASURE_KILLED, 0, 0, 0)]


@ONLY_POSIX
@pytest.mark.skipif(_shipped_model() is None, reason=f"{MODEL_ENV} carries no int8 model, so nothing real can load")
def test_a_real_int8_run_measures_memory_and_rate(tmp_path: Path) -> None:
    shipped = _shipped_model()
    assert shipped is not None
    loads = model.load_count()
    result = model_probe._measure("int8", tmp_path, timeout_seconds=300.0, embed_model_dir=shipped)
    assert result.outcome == MEASURE_OK
    assert result.rss_after > result.rss_before > 0
    assert result.rate_milli > 0
    assert model.load_count() == loads
