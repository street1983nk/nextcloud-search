"""Boundary probes of the phase 30 audit (30-AUDIT.md), kept as regression tests.

Phase 30 moved the schema mark, opened the OCR allowlist for ces and brought a
vendored foreign list with a generator. Every group below is one boundary of
that work, probed from the outside and, where the boundary is a set, with a
positive control that shows the probe reacts to the set and not to something
else. The groups follow the behavior block of plan 30-09:

* the OCR argument boundary T-03-502 with ces (manipulated values never reach
  tesseract, the call is an argument list),
* the mark pairs of the schema ratchet and the read gate,
* a half filled rebuild target of foreign marks,
* the stop word generator (tamper stops it before any output, never run or
  imported by the package),
* the normalisation of FINDLING_LANGUAGES with cs, never a KeyError,
* the field plan of a schema 2 directory under schema 3 code.

Accents appear only inside string literals; identifiers stay ASCII.
"""

from __future__ import annotations

import ast
import gc
import hashlib
import importlib.util
import logging
import shutil
import sys
from pathlib import Path
from types import ModuleType

import pytest
from tantivy import Document, Index

from conftest import CONSTITUENTS, write_wordlist
from findling import config
from findling.api.resources import QUERYABLE_SCHEMA_GENERATIONS, _of_the_marks, field_plan_for
from findling.config import (
    DEFAULT_LANGUAGES,
    OCR_DEFAULT_LANGUAGES,
    OCR_LANGUAGE_ALLOWLIST,
    SCHEMA_VERSION,
    SNOWBALL_NAME,
    STEMMERLESS_LANGUAGES,
    SUPPORTED_LANGUAGES,
    TESSERACT_NAME,
    settings,
)
from findling.extract import ocr
from findling.index.open import LANGUAGES_MARK, SCHEMA_MARK, expected_versions, fingerprint, open_index
from findling.index.rebuild import TARGET_MARK_FILE, _make_the_target_fit_this_code
from findling.index.schema import (
    BODY_FIELD,
    FIELD_BODY_CS,
    FIELD_BODY_DE,
    FIELD_BODY_EN,
    FIELD_FILE_ID,
    FIELD_NAME,
    FIELD_TITLE,
)
from findling.query.rewrite import BODY_BOOST, LEGACY_PLAN, FieldPlan, build_query
from findling.store.repo import LEGACY_SCHEMA_STEPS, UNKNOWN_VERSION, _schema_is_legacy

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
PACKAGE = BACKEND / "src" / "findling"
GENERATOR = REPO_ROOT / "scripts" / "dev" / "czech_stopwords.py"
ORIGINAL = Path(__file__).resolve().parent / "fixtures" / "lucene_cz_stopwords_10_5_2.txt"
DOCKERFILE = BACKEND / "Dockerfile"


@pytest.fixture(autouse=True)
def _cold_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("FINDLING_LANGUAGES", "FINDLING_OCR_LANGUAGES"):
        monkeypatch.delenv(name, raising=False)
    settings.cache_clear()


def _resolved(monkeypatch: pytest.MonkeyPatch, name: str, value: str) -> config.Settings:
    monkeypatch.setenv(name, value)
    settings.cache_clear()
    try:
        return settings()
    finally:
        settings.cache_clear()


# -- 1. the OCR argument boundary T-03-502 with ces ---------------------------

# Each value carries ces next to something that must never reach tesseract: a
# path, a shell separator, a blank inside one entry, an option, an unknown code.
# What comes out is either the admin's valid remainder or the built in default,
# and nothing else.
MANIPULATED = {
    "ces+../x": ("ces",),
    "ces;id": OCR_DEFAULT_LANGUAGES,
    "ces deu": OCR_DEFAULT_LANGUAGES,
    "../ces": OCR_DEFAULT_LANGUAGES,
    "cze": OCR_DEFAULT_LANGUAGES,
    "ces+--psm+0": ("ces",),
    "-l+ces": ("ces",),
    "ces|sh": OCR_DEFAULT_LANGUAGES,
    "ces$(id)": OCR_DEFAULT_LANGUAGES,
    "+": OCR_DEFAULT_LANGUAGES,
    "ces++deu": ("ces", "deu"),
    "ces+ces": ("ces",),
}


@pytest.mark.parametrize(("raw", "expected"), sorted(MANIPULATED.items()))
def test_a_manipulated_ocr_value_never_reaches_tesseract(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: tuple[str, ...]
) -> None:
    chosen = _resolved(monkeypatch, "FINDLING_OCR_LANGUAGES", raw).ocr_languages

    assert chosen == expected
    assert set(chosen) <= OCR_LANGUAGE_ALLOWLIST
    assert not any(code.startswith("-") for code in chosen)


def test_upper_case_ces_is_read_as_ces_because_the_reader_lowers_on_purpose(monkeypatch: pytest.MonkeyPatch) -> None:
    """CES is accepted: _ocr_languages lowers every entry before the allowlist.

    Not a hole: lowering can only map onto an entry of the allowlist, and what
    reaches tesseract is that entry, never the admin's spelling.
    """
    assert _resolved(monkeypatch, "FINDLING_OCR_LANGUAGES", "CES+Deu").ocr_languages == ("ces", "deu")


def test_deu_plus_ces_is_accepted_in_the_admin_order(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _resolved(monkeypatch, "FINDLING_OCR_LANGUAGES", "deu+ces").ocr_languages == ("deu", "ces")


def test_the_probe_follows_the_allowlist_and_nothing_else(monkeypatch: pytest.MonkeyPatch) -> None:
    """Positive control: put a hostile entry INTO the allowlist and it gets through.

    Proves that the rejections above come from the allowlist and not from some
    other filter the probe does not know about.
    """
    monkeypatch.setattr(config, "OCR_LANGUAGE_ALLOWLIST", OCR_LANGUAGE_ALLOWLIST | {"ces;id"})
    assert _resolved(monkeypatch, "FINDLING_OCR_LANGUAGES", "ces;id").ocr_languages == ("ces;id",)


def test_the_page_call_is_an_argument_list_and_never_a_shell(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    class _Finished:
        returncode = 0
        stdout = b"smlouva"
        stderr = b""

    def _run(arguments: object, **options: object) -> _Finished:
        seen["arguments"] = arguments
        seen["options"] = options
        return _Finished()

    monkeypatch.setattr(ocr.subprocess, "run", _run)
    ocr.read_page(b"png", "deu+ces", 5)

    arguments = seen["arguments"]
    assert isinstance(arguments, list)
    assert arguments[arguments.index("-l") + 1] == "deu+ces"
    options = seen["options"]
    assert isinstance(options, dict)
    assert options.get("shell", False) is False


def _shell_true_calls(tree: ast.AST) -> list[int]:
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        for keyword in node.keywords
        if keyword.arg == "shell" and not (isinstance(keyword.value, ast.Constant) and keyword.value.value is False)
    ]


def test_no_call_in_the_package_asks_for_a_shell() -> None:
    found = {
        str(path.relative_to(PACKAGE)): lines
        for path in sorted(PACKAGE.rglob("*.py"))
        if (lines := _shell_true_calls(ast.parse(path.read_text(encoding="utf-8"))))
    }
    assert found == {}
    # Positive control: the scanner sees a shell=True when there is one.
    assert _shell_true_calls(ast.parse("import subprocess\nsubprocess.run('x', shell=True)\n")) == [2]


def test_ces_is_installed_and_proven_in_the_image_build() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert "tesseract-ocr-ces=1:4.1.0-2" in text
    assert "grep -qx ces" in text


# -- 2. the mark pairs of the ratchet and of the read gate -------------------


def test_the_ratchet_carries_exactly_the_three_forward_pairs() -> None:
    assert frozenset({("1", "2"), ("2", "3"), ("1", "3")}) == LEGACY_SCHEMA_STEPS


@pytest.mark.parametrize("pair", [("3", "2"), ("2", "1"), ("3", "1"), ("4", "3"), ("3", "4"), ("2", "2")])
def test_no_backward_or_unknown_pair_is_excused(pair: tuple[str, str]) -> None:
    assert pair not in LEGACY_SCHEMA_STEPS
    assert _schema_is_legacy(pair[0], pair[1]) is False


@pytest.mark.parametrize("pair", sorted(LEGACY_SCHEMA_STEPS))
def test_every_forward_pair_is_excused(pair: tuple[str, str]) -> None:
    assert _schema_is_legacy(pair[0], pair[1]) is True


def test_an_absent_or_unknown_stored_mark_gets_no_excuse() -> None:
    assert _schema_is_legacy(None, str(SCHEMA_VERSION)) is False
    assert _schema_is_legacy(UNKNOWN_VERSION, str(SCHEMA_VERSION)) is False


@pytest.mark.parametrize("stored", ["1", "4", "", None, UNKNOWN_VERSION, " 3", "3.0"])
def test_the_read_gate_gives_no_plan_outside_generations_2_and_3(stored: str | None) -> None:
    marks = {LANGUAGES_MARK: "de,en,es"} if stored is None else {SCHEMA_MARK: stored, LANGUAGES_MARK: "de,en,es"}
    assert _of_the_marks(marks) is None


@pytest.mark.parametrize("stored", ["2", "3"])
def test_the_read_gate_keeps_every_language_of_generations_2_and_3(stored: str) -> None:
    """The Pflicht-Fix of 30-CONTEXT: no silent loss of es, it, nl, pt."""
    plan = _of_the_marks({SCHEMA_MARK: stored, LANGUAGES_MARK: "de,en,es,it,nl,pt"})
    assert plan is not None
    assert plan.fields[:6] == tuple(BODY_FIELD[code] for code in ("de", "en", "es", "it", "nl", "pt"))
    assert frozenset({"2", "3"}) == QUERYABLE_SCHEMA_GENERATIONS


# -- 3. a half filled target of foreign marks --------------------------------
#
# test_czech_switch.py::test_a_half_filled_target_of_the_schema_2_expectation_is_discarded
# holds the schema 2 fingerprint case. This one is a different foreign mark: a
# target of THIS schema, filled for another language set.


def test_a_half_filled_schema_3_target_of_another_language_set_is_discarded(
    volume: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    digest = write_wordlist(volume)
    wanted = fingerprint(expected_versions(digest, "de,cs"))
    other = fingerprint(expected_versions(digest, "de,en"))
    assert other != wanted
    target = volume / "index.rebuild"
    half = open_index(target, CONSTITUENTS)
    writer = half.writer(heap_size=15_000_000, num_threads=1)
    document = Document()
    document.add_unsigned(FIELD_FILE_ID, 7)
    document.add_text(FIELD_BODY_DE, "Smlouva")
    writer.add_document(document)
    writer.commit()
    writer.wait_merging_threads()
    del writer, half
    gc.collect()
    (target / TARGET_MARK_FILE).write_text(other, encoding="utf-8")

    with caplog.at_level(logging.WARNING, logger="findling.index.rebuild"):
        _make_the_target_fit_this_code(target, CONSTITUENTS, wanted, dutch=None)
    fresh = open_index(target, CONSTITUENTS)
    fresh.reload()
    documents = fresh.searcher().num_docs
    del fresh
    gc.collect()

    assert documents == 0
    assert (target / TARGET_MARK_FILE).read_text(encoding="utf-8") == wanted
    assert any("other version marks" in record.getMessage() for record in caplog.records)


# -- 4. the stop word generator ----------------------------------------------


def _load_generator() -> ModuleType:
    specification = importlib.util.spec_from_file_location("czech_stopwords_audit", GENERATOR)
    if specification is None or specification.loader is None:  # pragma: no cover
        raise RuntimeError(f"the generator is not at {GENERATOR}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


@pytest.mark.parametrize("tamper", ["append", "last_byte", "crlf"])
def test_the_generator_stops_before_any_output_on_a_changed_byte(tmp_path: Path, tamper: str) -> None:
    generator = _load_generator()
    copy = tmp_path / ORIGINAL.name
    shutil.copyfile(ORIGINAL, copy)
    data = copy.read_bytes()
    if tamper == "append":
        data += b"x\n"
    elif tamper == "last_byte":
        data = data[:-1] + bytes([data[-1] ^ 0x20])
    else:
        data = data.replace(b"\n", b"\r\n")
    copy.write_bytes(data)
    assert hashlib.sha256(data).hexdigest() != generator.SOURCE_SHA256
    output = tmp_path / "out" / "literal.py"

    assert generator.main(["--source", str(copy), "--output", str(output)]) == 1
    assert not output.exists()
    assert not output.parent.exists()


def test_the_generator_writes_its_output_on_the_pinned_original(tmp_path: Path) -> None:
    """Positive control for the case above: the same call on the true bytes writes."""
    output = tmp_path / "out" / "literal.py"
    assert _load_generator().main(["--source", str(ORIGINAL), "--output", str(output)]) == 0
    assert output.is_file()


def _imported_modules(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_the_generator_lies_outside_the_package_and_nothing_in_it_imports_it() -> None:
    assert not GENERATOR.resolve().is_relative_to(BACKEND / "src")
    assert not list(PACKAGE.rglob("czech_stopwords*.py"))
    trees = [ast.parse(p.read_text(encoding="utf-8")) for p in PACKAGE.rglob("*.py")]
    imported = set().union(*(_imported_modules(tree) for tree in trees))
    assert not {name for name in imported if "czech_stopwords" in name or name.startswith("scripts")}
    # Nothing under the package loads a file by path either, so the import scan
    # above is not dodged by importlib.
    loaders = [
        str(p.relative_to(PACKAGE))
        for p in PACKAGE.rglob("*.py")
        if "spec_from_file_location" in p.read_text(encoding="utf-8")
    ]
    assert loaders == []
    # Positive control: the scan finds an import of the generator when there is one.
    assert "czech_stopwords" in _imported_modules(ast.parse("import czech_stopwords\n"))


def test_the_image_build_copies_no_scripts_tree_beyond_the_model_tool() -> None:
    copies = [line for line in DOCKERFILE.read_text(encoding="utf-8").splitlines() if line.startswith("COPY")]
    from_scripts = [line for line in copies if "scripts" in line]
    assert from_scripts == ["COPY --from=scripts dev/quantize_model.py /tmp/quantize_model.py"]


def test_the_package_runtime_reaches_for_no_network_in_the_czech_path() -> None:
    for path in (PACKAGE / "index" / "stopwords_cs.py", PACKAGE / "index" / "analyzer.py"):
        imported = _imported_modules(ast.parse(path.read_text(encoding="utf-8")))
        assert not imported & {"urllib", "urllib.request", "httpx", "requests", "socket", "http.client"}


# -- 5. the normalisation of FINDLING_LANGUAGES with cs -----------------------

LANGUAGE_CASES = {
    "cs": ("cs",),
    "cs,cs": ("cs",),
    "CS,de": ("de", "cs"),
    " cs , de ": ("de", "cs"),
    "cs,de": ("de", "cs"),
    "de,en,cs": ("de", "en", "cs"),
    "cz": DEFAULT_LANGUAGES,
    "cs;rm": DEFAULT_LANGUAGES,
    "czech": DEFAULT_LANGUAGES,
    "ces": DEFAULT_LANGUAGES,
}


@pytest.mark.parametrize(("raw", "expected"), sorted(LANGUAGE_CASES.items()))
def test_a_language_value_with_cs_resolves_as_documented_and_never_raises(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: tuple[str, ...]
) -> None:
    chosen = _resolved(monkeypatch, "FINDLING_LANGUAGES", raw).languages
    assert chosen == expected
    for code in chosen:
        # Every lookup a resolved code meets on its way, none of them a KeyError.
        assert BODY_FIELD[code]
        assert BODY_BOOST[code] > 0
        assert TESSERACT_NAME[code] in OCR_LANGUAGE_ALLOWLIST
        assert (code in SNOWBALL_NAME) != (code in STEMMERLESS_LANGUAGES)
    plan = _of_the_marks({SCHEMA_MARK: str(SCHEMA_VERSION), LANGUAGES_MARK: ",".join(chosen)})
    assert plan is not None
    assert plan.fields[: len(chosen)] == tuple(BODY_FIELD[code] for code in chosen)


def _variable_snowball_subscripts(tree: ast.AST) -> list[int]:
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == "SNOWBALL_NAME"
        and not isinstance(node.slice, ast.Constant)
    ]


def test_no_code_reaches_snowball_name_through_a_variable_key() -> None:
    """A KeyError for cs is only possible through a computed key; there is none."""
    found = {
        str(p.relative_to(PACKAGE)): lines
        for p in sorted(PACKAGE.rglob("*.py"))
        if (lines := _variable_snowball_subscripts(ast.parse(p.read_text(encoding="utf-8"))))
    }
    assert found == {}
    assert _variable_snowball_subscripts(ast.parse("SNOWBALL_NAME[code]\n")) == [1]


def test_cs_is_the_last_body_field_and_the_last_supported_language() -> None:
    assert SUPPORTED_LANGUAGES[-1] == "cs"
    assert tuple(BODY_FIELD) == SUPPORTED_LANGUAGES
    assert BODY_FIELD["cs"] == FIELD_BODY_CS


# -- 6. the field plan of a schema 2 directory under schema 3 code -----------


def _hits(index: Index, text: str, plan: FieldPlan) -> int:
    rewritten = build_query(index, text, plan=plan)
    assert rewritten.errors == []
    assert rewritten.query is not None
    return len(index.searcher().search(rewritten.query, limit=50).hits)


def test_cs_chosen_on_a_schema_2_directory_before_its_rebuild_searches_without_body_cs(
    schema_2_index: Index, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The admin chose de,cs, the rebuild has not run: the marks still say de,en.

    The plan comes from the marks and never from the settings, so body_cs is not
    even asked for (no warning of _probed), and the search answers hits.
    """
    monkeypatch.setenv("FINDLING_LANGUAGES", "de,cs")
    settings.cache_clear()
    assert settings().languages == ("de", "cs")

    with caplog.at_level(logging.WARNING, logger="findling.api.resources"):
        plan = field_plan_for({SCHEMA_MARK: "2", LANGUAGES_MARK: "de,en"}, schema_2_index)

    assert plan.fields == (FIELD_BODY_DE, FIELD_BODY_EN, FIELD_NAME, FIELD_TITLE)
    assert [record for record in caplog.records if "not in the directory" in record.getMessage()] == []
    assert _hits(schema_2_index, "Akte", plan) > 0


def test_a_mark_naming_cs_on_a_schema_2_directory_loses_body_cs_and_nothing_else(
    schema_2_index: Index, caplog: pytest.LogCaptureFixture
) -> None:
    """Counter probe: a mark that DOES name cs on a directory without the field.

    _probed drops body_cs with one warning and keeps the rest; the search still
    answers instead of raising. Shows the probe of the case above would see a
    body_cs request if one were made.
    """
    with caplog.at_level(logging.WARNING, logger="findling.api.resources"):
        plan = field_plan_for({SCHEMA_MARK: "2", LANGUAGES_MARK: "de,cs"}, schema_2_index)

    assert plan.fields == (FIELD_BODY_DE, FIELD_NAME, FIELD_TITLE)
    warnings = [record for record in caplog.records if "not in the directory" in record.getMessage()]
    assert len(warnings) == 1
    assert FIELD_BODY_CS in warnings[0].getMessage()
    assert plan != LEGACY_PLAN
    assert _hits(schema_2_index, "Akte", plan) > 0


def test_six_languages_on_a_schema_2_directory_keep_all_six_under_schema_3_code(schema_2_index: Index) -> None:
    plan = field_plan_for({SCHEMA_MARK: "2", LANGUAGES_MARK: "de,en,es,it,nl,pt"}, schema_2_index)
    bodies = tuple(BODY_FIELD[code] for code in ("de", "en", "es", "it", "nl", "pt"))
    assert plan.fields == (*bodies, FIELD_NAME, FIELD_TITLE)
    assert _hits(schema_2_index, "Akte", plan) > 0
