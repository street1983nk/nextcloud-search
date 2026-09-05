"""Every cap of phase 2 has exactly one home, and a typo never stops the container.

The second half is the part worth a test. A self hosted box has no operator
watching the boot log; an ExApp that refuses to start because somebody typed
``FINDLING_MAX_TEXT_CHARS=512k`` is an outage without a diagnosis. So the reader
of a number falls back to the measured default and logs a warning, and that
behaviour is asserted here rather than hoped for.

``INDEX_WORKERS`` gets its own test for the opposite reason: it is architecture,
not configuration (IDX-08). OCR and embedding peaks must never run at the same
time on a 4 GB box, so the value may not become an environment variable by
accident. The test fails the moment somebody makes it one.
"""

from __future__ import annotations

import re
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from findling.config import (
    EMBED_CHUNK_TOKENS,
    EMBED_CONTEXT_TOKENS,
    EMBED_MODEL_DIR,
    EMBED_SPECIAL_TOKENS,
    EMBED_TOKEN_CAP_RANGE,
    INDEX_WORKERS,
    MAX_TEXT_CHARS,
    OCR_CLAIM_BATCH,
    OCR_HARD_DEADLINE_MARGIN_SECONDS,
    OCR_JOB_SECONDS_MAX,
    OCR_LOCK_TIMEOUT_SECONDS,
    settings,
)

PHP_QUEUE_MAPPER = Path(__file__).resolve().parents[2] / "php" / "lib" / "Db" / "QueueMapper.php"
PHP_QUEUE_SERVICE = Path(__file__).resolve().parents[2] / "php" / "lib" / "Service" / "QueueService.php"

# Every variable the module reads. Cleared before each test so a developer
# machine that happens to export one of them cannot turn a red test green.
ENVIRONMENT = (
    "APP_PERSISTENT_STORAGE",
    "FINDLING_COMPOUND_DICT",
    "FINDLING_LANGUAGES",
    "FINDLING_MAX_TEXT_CHARS",
    "FINDLING_INDEX_WORKERS",
    "FINDLING_OCR_ENABLED",
    "FINDLING_OCR_LANGUAGES",
    "FINDLING_OCR_MAX_PAGES",
    "FINDLING_OCR_PAGE_SECONDS",
    "FINDLING_OCR_JOB_SECONDS",
    "FINDLING_OCR_DPI",
    "FINDLING_EMBED_ENABLED",
    "FINDLING_EMBED_TOKEN_CAP",
    "FINDLING_EMBED_CHUNK_TOKENS",
    "FINDLING_EMBED_CHUNK_OVERLAP",
    "FINDLING_EMBED_BATCH_SIZE",
    "FINDLING_EMBED_SEQUENCE_LEN",
    "FINDLING_EMBED_MODEL_DIR",
)


@pytest.fixture(autouse=True)
def _isolated_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Give every test an empty environment and a cold cache."""
    for name in ENVIRONMENT:
        monkeypatch.delenv(name, raising=False)
    settings.cache_clear()
    yield
    settings.cache_clear()


def test_defaults_are_the_measured_numbers() -> None:
    current = settings()

    assert current.max_file_bytes == 52_428_800
    assert current.batch_files == 32
    assert current.batch_max_bytes == 67_108_864
    assert current.extract_timeout_seconds == 120
    assert current.extract_address_space_bytes == 536_870_912
    assert current.extract_worker_max_files == 200
    assert current.max_text_chars == 524_288
    assert current.max_cells == 200_000
    assert current.max_pdf_pages == 500
    assert current.min_free_bytes == 524_288_000
    assert current.writer_heap_bytes == 50_000_000
    assert current.poll_cooldown_start_seconds == 15
    assert current.poll_cooldown_max_seconds == 120
    assert current.snippet_chars == 200
    assert current.search_limit_max == 100
    assert current.languages == ("de", "en")
    assert current.compound_dict == "full"


def test_persistent_storage_places_all_four_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APP_PERSISTENT_STORAGE", str(tmp_path))
    settings.cache_clear()

    current = settings()

    assert current.index_dir == tmp_path / "index"
    assert current.state_db == tmp_path / "state.db"
    assert current.dict_dir == tmp_path / "dict"
    assert current.tmp_dir == tmp_path / "tmp"


def test_without_persistent_storage_everything_lands_under_the_temp_directory() -> None:
    current = settings()

    root = Path(tempfile.gettempdir())
    assert current.index_dir.parent.parent == root
    assert current.index_dir.parent == current.state_db.parent == current.dict_dir.parent == current.tmp_dir.parent


@pytest.mark.parametrize("variant", ["full", "nouns"])
def test_both_measured_dictionary_variants_are_accepted(monkeypatch: pytest.MonkeyPatch, variant: str) -> None:
    monkeypatch.setenv("FINDLING_COMPOUND_DICT", variant)
    settings.cache_clear()

    assert settings().compound_dict == variant


@pytest.mark.parametrize("value", ["", "  ", "gross", "FULL_", "nouns,full"])
def test_an_unknown_dictionary_variant_falls_back_to_full(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("FINDLING_COMPOUND_DICT", value)
    settings.cache_clear()

    assert settings().compound_dict == "full"


def test_german_only_leaves_the_english_body_field_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_LANGUAGES", "de")
    settings.cache_clear()

    assert settings().languages == ("de",)


def test_both_languages_are_kept_in_the_documented_order(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_LANGUAGES", "en, de")
    settings.cache_clear()

    # The order is the field order of the schema, not the order somebody typed.
    assert settings().languages == ("de", "en")


def test_an_unknown_language_list_falls_back_to_both(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_LANGUAGES", "klingon")
    settings.cache_clear()

    assert settings().languages == ("de", "en")


def test_index_workers_is_a_constant_and_not_an_environment_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_INDEX_WORKERS", "8")
    settings.cache_clear()

    # Serial indexing is architecture (IDX-08): OCR and embedding peaks must not
    # meet on a 4 GB box. Turning this into a knob would be a silent regression.
    assert INDEX_WORKERS == 1
    assert not hasattr(settings(), "index_workers")


@pytest.mark.parametrize("value", ["512k", "", "  ", "-1", "0", "12.5", "eins"])
def test_an_unusable_number_falls_back_instead_of_raising(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("FINDLING_MAX_TEXT_CHARS", value)
    settings.cache_clear()

    assert settings().max_text_chars == MAX_TEXT_CHARS


def test_a_usable_number_is_taken_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_MAX_TEXT_CHARS", "1024")
    settings.cache_clear()

    assert settings().max_text_chars == 1024


def test_a_broken_number_warns_without_naming_its_value(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("FINDLING_MAX_TEXT_CHARS", "512k")
    settings.cache_clear()

    with caplog.at_level("WARNING", logger="findling.config"):
        settings()

    # T-02-14: the log carries the name of the variable, never its content.
    assert "FINDLING_MAX_TEXT_CHARS" in caplog.text
    assert "512k" not in caplog.text


def test_settings_is_frozen_so_a_cap_cannot_drift_at_runtime() -> None:
    current = settings()

    with pytest.raises((AttributeError, TypeError)):
        current.max_text_chars = 1  # pyright: ignore[reportAttributeAccessIssue]


def test_settings_is_cached_so_every_caller_sees_the_same_caps() -> None:
    assert settings() is settings()


def test_settings_has_slots_so_a_typo_cannot_invent_a_cap() -> None:
    current = settings()

    # slots=True is half of the guarantee above: frozen stops a field from being
    # rewritten, slots stops a misspelled one from being added at all.
    assert not hasattr(current, "__dict__")


# ---------------------------------------------------------------------------
# OCR, phase 3. Every default below is a number from docs/ocr.md, measured on
# 2026-09-01 in the shipping image, not a guess.
# ---------------------------------------------------------------------------


def test_ocr_defaults_are_the_measured_numbers() -> None:
    current = settings()

    assert current.ocr_enabled is True
    assert current.ocr_languages == ("deu", "eng")
    assert current.ocr_max_pages == 30
    assert current.ocr_page_seconds == 30
    assert current.ocr_job_seconds == 600
    assert current.ocr_hard_deadline_seconds == 660
    assert current.ocr_dpi == 300


def test_ocr_languages_falls_back_to_the_default_when_none_is_installed(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("FINDLING_OCR_LANGUAGES", "klingon")
    settings.cache_clear()

    with caplog.at_level("WARNING", logger="findling.config"):
        current = settings()

    # Not an exception: a typo in an admin form must not produce a container
    # that refuses to start on an unattended box (T-03-504).
    assert current.ocr_languages == ("deu", "eng")
    assert "FINDLING_OCR_LANGUAGES" in caplog.text
    assert "klingon" not in caplog.text


def test_an_ocr_language_that_is_not_installed_is_dropped_and_the_rest_stays(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # frk is a real tesseract language code, but the package is not in the image
    # today, so it may not reach the command line either.
    monkeypatch.setenv("FINDLING_OCR_LANGUAGES", "deu+frk")
    settings.cache_clear()

    assert settings().ocr_languages == ("deu",)


@pytest.mark.parametrize(
    "value",
    ["deu; rm -rf /", "deu+--psm 0", "$(id)", "deu+eng --tessdata-dir /tmp", "../../etc/passwd"],
)
def test_the_ocr_language_list_never_leaves_the_allowlist(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("FINDLING_OCR_LANGUAGES", value)
    settings.cache_clear()

    # T-03-502: the value reaches an argument list of a subprocess. Nothing that
    # is not a language this image actually carries may survive this reader.
    assert set(settings().ocr_languages) <= {"deu", "eng"}


def test_a_usable_ocr_language_list_is_taken_in_the_order_it_was_asked_for(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FINDLING_OCR_LANGUAGES", "eng+deu")
    settings.cache_clear()

    # Unlike FINDLING_LANGUAGES, which is a schema field order, this one is a
    # tesseract argument: the first language weighs more, so the admin's order
    # is the answer.
    assert settings().ocr_languages == ("eng", "deu")


@pytest.mark.parametrize("value", ["dreissig", "", "  ", "-1", "0", "30.5", "100000"])
def test_an_unusable_ocr_page_cap_falls_back_instead_of_raising(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("FINDLING_OCR_MAX_PAGES", value)
    settings.cache_clear()

    assert settings().ocr_max_pages == 30


@pytest.mark.parametrize("value", ["0", "71", "1200", "dreihundert"])
def test_an_ocr_dpi_outside_the_measured_range_falls_back(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("FINDLING_OCR_DPI", value)
    settings.cache_clear()

    # A4 at 1200 dpi is 137 megapixels and bursts the 512 MB address space of
    # the sandbox child measured in docs/ocr.md, so the ceiling is a cap, not
    # taste (T-03-503).
    assert settings().ocr_dpi == 300


@pytest.mark.parametrize("value", ["false", "FALSE", "0", "no", "off"])
def test_ocr_can_be_switched_off_without_touching_the_rest_of_the_extraction(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("FINDLING_OCR_ENABLED", value)
    settings.cache_clear()

    current = settings()

    assert current.ocr_enabled is False
    # The switch is for the OCR branch alone. Everything the text extraction
    # needs keeps the values it had.
    assert current.max_file_bytes == 52_428_800
    assert current.max_pdf_pages == 500
    assert current.extract_timeout_seconds == 120
    assert current.extract_address_space_bytes == 536_870_912
    assert current.languages == ("de", "en")


@pytest.mark.parametrize("value", ["vielleicht", "ja", "1.0", "  "])
def test_an_unusable_ocr_switch_stays_on_instead_of_raising(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("FINDLING_OCR_ENABLED", value)
    settings.cache_clear()

    assert settings().ocr_enabled is True


@pytest.mark.parametrize("job_seconds", ["120", "600", "780", "1800"])
def test_the_hard_deadline_always_stays_above_the_soft_one(monkeypatch: pytest.MonkeyPatch, job_seconds: str) -> None:
    monkeypatch.setenv("FINDLING_OCR_JOB_SECONDS", job_seconds)
    settings.cache_clear()

    current = settings()

    # If the parent killed the child at the same second the child stops its own
    # page loop, the partial text would never make it through the pipe and
    # indexed(truncated) would never occur in practice. Deriving the hard
    # deadline is what keeps that true when an admin moves the soft one, and it
    # holds for an out of range value as well, because that falls back to the
    # default before the derivation runs.
    assert current.ocr_hard_deadline_seconds > current.ocr_job_seconds
    assert current.ocr_hard_deadline_seconds == current.ocr_job_seconds + 60


def test_the_job_ceiling_itself_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_OCR_JOB_SECONDS", str(OCR_JOB_SECONDS_MAX))
    settings.cache_clear()

    assert settings().ocr_job_seconds == OCR_JOB_SECONDS_MAX


@pytest.mark.parametrize("job_seconds", ["781", "900", "1800"])
def test_a_job_budget_that_would_outlive_the_ocr_lock_falls_back(
    monkeypatch: pytest.MonkeyPatch, job_seconds: str
) -> None:
    # Review finding WR-04. The old ceiling of 1800 declared a value valid at
    # which a single job's hard deadline (1860 s) already outlived the 1800 s
    # OCR lock, and a claim of two jobs could legitimately work for twice that:
    # the rows reappeared as free, collected retries and ended as
    # failed(repeatedly_stuck) while the engine was working correctly. A
    # documented maximum that rebuilds the stuck-claim failure is worse than a
    # typo, so these values now degrade like every other out of range number.
    monkeypatch.setenv("FINDLING_OCR_JOB_SECONDS", job_seconds)
    settings.cache_clear()

    current = settings()

    assert current.ocr_job_seconds == 600
    assert current.ocr_hard_deadline_seconds == 660


def _php_constant_entry(source_path: Path, block_name: str, key: str) -> int:
    """One integer entry of a PHP constant array, read out of the source.

    Read as text because a PHP constant cannot be imported, in the shape of the
    mimetype allowlist gate: writing the number into the Python side by hand a
    second time would be exactly the drift this gate exists to catch.
    """
    source = source_path.read_text(encoding="utf-8")
    block = re.search(rf"const {block_name} = \[(.*?)\];", source, re.DOTALL)
    assert block is not None, f"the {block_name} constant is no longer where this gate looks for it"
    entry = re.search(rf"{key} => (\d+),", block.group(1))
    assert entry is not None, f"{block_name} no longer carries a literal for {key}"
    return int(entry.group(1))


def test_the_mirrored_php_numbers_behind_the_job_ceiling_are_the_real_ones() -> None:
    # The parity gate of the derivation. OCR_JOB_SECONDS_MAX is computed from
    # two PHP-side numbers this module can only mirror; the day one of them
    # moves, this test goes red instead of the ceiling silently drifting away
    # from the lock it exists to stay under.
    assert _php_constant_entry(PHP_QUEUE_MAPPER, "LOCK_TIMEOUTS", "KIND_OCR") == OCR_LOCK_TIMEOUT_SECONDS
    assert _php_constant_entry(PHP_QUEUE_SERVICE, "KIND_BATCH", "KIND_OCR") == OCR_CLAIM_BATCH


def test_a_full_ocr_claim_at_the_ceiling_stays_under_the_lock_timeout() -> None:
    # The invariant behind WR-04, spelled out: a claim of OCR_CLAIM_BATCH jobs,
    # each running to its hard deadline, must end before the lock expires and
    # hands the rows out a second time.
    worst_claim = OCR_CLAIM_BATCH * (OCR_JOB_SECONDS_MAX + OCR_HARD_DEADLINE_MARGIN_SECONDS)

    assert worst_claim < OCR_LOCK_TIMEOUT_SECONDS


def test_an_ocr_cap_cannot_drift_at_runtime_either() -> None:
    current = settings()

    with pytest.raises((AttributeError, TypeError)):
        current.ocr_max_pages = 1  # pyright: ignore[reportAttributeAccessIssue]


# ---------------------------------------------------------------------------
# Embeddings, phase 6. One test per value, the same density the OCR block above
# carries, because every one of these numbers fails silently: a chunk that
# outgrows the sequence loses its tail without an error, a cap an admin turns to
# an absurd value buys hours of ARM time nobody watches, and a model directory
# that falls back to a guess would turn the honest embedding_unavailable verdict
# into a download attempt.
# ---------------------------------------------------------------------------


def test_embedding_defaults_are_the_chosen_numbers() -> None:
    current = settings()

    assert current.embed_enabled is True
    assert current.embed_token_cap == 1024
    # 510 and not 512: the encoder adds an opening and a closing marker, so a
    # chunk of a full window would arrive at the session as 514 tokens and lose
    # its last two without anything failing.
    assert current.embed_chunk_tokens == 510
    assert current.embed_chunk_tokens + EMBED_SPECIAL_TOKENS == EMBED_CONTEXT_TOKENS
    assert current.embed_chunk_overlap == 0
    assert current.embed_batch_size == 2
    assert current.embed_sequence_len == 512
    assert current.embed_model_dir == Path(EMBED_MODEL_DIR)


def test_the_token_cap_can_be_turned_up(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_EMBED_TOKEN_CAP", "4096")
    settings.cache_clear()

    # D-01 calls the cap a setting an operator with time and hardware may raise,
    # and a cap that only ever degrades to its default would not be one.
    assert settings().embed_token_cap == 4096


def test_the_documented_ceiling_of_the_token_cap_is_itself_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_EMBED_TOKEN_CAP", str(EMBED_TOKEN_CAP_RANGE[1]))
    settings.cache_clear()

    assert settings().embed_token_cap == EMBED_TOKEN_CAP_RANGE[1]


@pytest.mark.parametrize("value", ["0", "-1", "100000", "viel", "1024.0"])
def test_a_token_cap_outside_the_measured_range_falls_back(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("FINDLING_EMBED_TOKEN_CAP", value)
    settings.cache_clear()

    # Zero is in this list on purpose: it reads like "switch embedding off" and
    # is not. That switch is FINDLING_EMBED_ENABLED, and a cap of zero would
    # otherwise produce a second, silent way to disable a feature.
    assert settings().embed_token_cap == 1024
    assert settings().embed_enabled is True


@pytest.mark.parametrize("value", ["9999", "513", "512", "511", "0", "acht"])
def test_a_chunk_size_above_the_context_window_falls_back(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, value: str
) -> None:
    monkeypatch.setenv("FINDLING_EMBED_CHUNK_TOKENS", value)
    settings.cache_clear()

    with caplog.at_level("WARNING", logger="findling.config"):
        current = settings()

    # The model window is 512 tokens and two of them belong to the encoder. A
    # larger chunk is not refused by anything downstream, it is silently cut at
    # the session and the tail of every chunk disappears from the index, so this
    # has to warn and degrade rather than start a container that indexes less
    # than it says. 512 and 511 are in the list on purpose: they look like the
    # window and are already one and two tokens too many.
    assert current.embed_chunk_tokens == EMBED_CHUNK_TOKENS
    assert current.embed_chunk_tokens + EMBED_SPECIAL_TOKENS <= EMBED_CONTEXT_TOKENS
    assert "FINDLING_EMBED_CHUNK_TOKENS" in caplog.text
    assert value not in caplog.text


def test_a_smaller_chunk_size_is_taken(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_EMBED_CHUNK_TOKENS", "256")
    settings.cache_clear()

    assert settings().embed_chunk_tokens == 256


def test_a_zero_overlap_is_a_legitimate_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_EMBED_CHUNK_OVERLAP", "0")
    settings.cache_clear()

    # Zero is the default and a real answer, so this value may not travel
    # through the reader that refuses zero as "a cap of nothing".
    assert settings().embed_chunk_overlap == 0


def test_a_usable_overlap_is_taken(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_EMBED_CHUNK_OVERLAP", "64")
    settings.cache_clear()

    assert settings().embed_chunk_overlap == 64


@pytest.mark.parametrize("value", ["512", "600", "-1", "halb"])
def test_an_overlap_that_cannot_advance_falls_back_to_zero(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("FINDLING_EMBED_CHUNK_OVERLAP", value)
    settings.cache_clear()

    # An overlap that is not smaller than the chunk never advances: the splitter
    # would produce the same window forever, on a machine with nobody watching.
    current = settings()
    assert current.embed_chunk_overlap == 0
    assert current.embed_chunk_overlap < current.embed_chunk_tokens


@pytest.mark.parametrize("value", ["0", "-4", "64", "zwei"])
def test_an_unusable_batch_size_falls_back(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("FINDLING_EMBED_BATCH_SIZE", value)
    settings.cache_clear()

    assert settings().embed_batch_size == 2


def test_a_larger_batch_inside_the_range_is_taken(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_EMBED_BATCH_SIZE", "8")
    settings.cache_clear()

    # Lever 4 of 06-RESEARCH.md 3.6 measured at batch 8 as well, so the range
    # covers the shape the wave 0 report quotes beside the default.
    assert settings().embed_batch_size == 8


@pytest.mark.parametrize("value", ["513", "1024", "0", "lang"])
def test_a_sequence_length_above_the_context_window_falls_back(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("FINDLING_EMBED_SEQUENCE_LEN", value)
    settings.cache_clear()

    assert settings().embed_sequence_len == 512
    assert settings().embed_sequence_len <= EMBED_CONTEXT_TOKENS


def test_a_chunk_never_outgrows_the_sequence_the_session_sees(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("FINDLING_EMBED_SEQUENCE_LEN", "256")
    settings.cache_clear()

    with caplog.at_level("WARNING", logger="findling.config"):
        current = settings()

    # The two values are read independently and are not independent. An admin
    # who lowers the sequence to save memory and leaves the chunk size alone
    # would otherwise feed 510 token chunks into a 256 token session, and half of
    # every chunk would leave the index without a single error line.
    assert current.embed_sequence_len == 256
    assert current.embed_chunk_tokens == 256 - EMBED_SPECIAL_TOKENS
    assert "FINDLING_EMBED_CHUNK_TOKENS" in caplog.text


@pytest.mark.parametrize("value", ["false", "FALSE", "0", "no", "off"])
def test_embedding_can_be_switched_off_without_touching_the_full_text_side(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("FINDLING_EMBED_ENABLED", value)
    settings.cache_clear()

    current = settings()

    assert current.embed_enabled is False
    # The switch owns the second track and nothing else. Full text and OCR keep
    # every number they had, which is the whole promise of criterion 3.
    assert current.ocr_enabled is True
    assert current.max_text_chars == 524_288
    assert current.languages == ("de", "en")


@pytest.mark.parametrize("value", ["vielleicht", "ja", "1.0", "  "])
def test_an_unusable_embedding_switch_stays_on(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("FINDLING_EMBED_ENABLED", value)
    settings.cache_clear()

    assert settings().embed_enabled is True


@pytest.mark.parametrize("value", ["", "   "])
def test_an_empty_model_directory_yields_the_built_in_path(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("FINDLING_EMBED_MODEL_DIR", value)
    settings.cache_clear()

    # Not an error, and not a check that the directory exists either. Whether
    # there is a model behind the path is a question for embed/model.py, which
    # answers it with the embedding_unavailable verdict; a configuration reader
    # that refused to resolve would move that verdict into the boot path.
    assert settings().embed_model_dir == Path(EMBED_MODEL_DIR)


def test_a_model_directory_from_the_environment_is_taken(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FINDLING_EMBED_MODEL_DIR", str(tmp_path))
    settings.cache_clear()

    assert settings().embed_model_dir == tmp_path


def test_a_broken_embedding_number_warns_without_naming_its_value(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("FINDLING_EMBED_TOKEN_CAP", "1024k")
    settings.cache_clear()

    with caplog.at_level("WARNING", logger="findling.config"):
        settings()

    assert "FINDLING_EMBED_TOKEN_CAP" in caplog.text
    assert "1024k" not in caplog.text


def test_an_embedding_cap_cannot_drift_at_runtime_either() -> None:
    current = settings()

    with pytest.raises((AttributeError, TypeError)):
        current.embed_token_cap = 1  # pyright: ignore[reportAttributeAccessIssue]
