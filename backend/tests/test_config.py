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
