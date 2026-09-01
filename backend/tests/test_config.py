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

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from findling.config import INDEX_WORKERS, MAX_TEXT_CHARS, settings

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


@pytest.mark.parametrize("job_seconds", ["120", "600", "900", "1800"])
def test_the_hard_deadline_always_stays_above_the_soft_one(monkeypatch: pytest.MonkeyPatch, job_seconds: str) -> None:
    monkeypatch.setenv("FINDLING_OCR_JOB_SECONDS", job_seconds)
    settings.cache_clear()

    current = settings()

    # If the parent killed the child at the same second the child stops its own
    # page loop, the partial text would never make it through the pipe and
    # indexed(truncated) would never occur in practice. Deriving the hard
    # deadline is what keeps that true when an admin moves the soft one.
    assert current.ocr_hard_deadline_seconds > current.ocr_job_seconds
    assert current.ocr_hard_deadline_seconds == current.ocr_job_seconds + 60


def test_an_ocr_cap_cannot_drift_at_runtime_either() -> None:
    current = settings()

    with pytest.raises((AttributeError, TypeError)):
        current.ocr_max_pages = 1  # pyright: ignore[reportAttributeAccessIssue]
