"""The locale of php/js/admin.js survives every locale code Nextcloud offers.

admin.js turns the session locale on the root element (``data-locale``, for
example ``zh_Hant_TW``) into the tag Intl takes, and builds a number format and
a relative time format from it as its first statements. Before this test the
function replaced the first underscore only, so the 42 locales of Nextcloud 34
with three parts became tags such as ``zh-Hant_TW``, both constructors threw a
RangeError, and the throw ended the script before a single button, form or poll
of the admin page was wired. Nothing on the page said so: the half the server
renders looked complete.

The test cuts the function out of the script and runs it in node against every
three part code of ``resources/locales.json`` (Nextcloud 34.0.3, read on
2026-11-20), a sample of two part codes and values that are no tag at all, and
builds both formats from every answer. The positive control runs the old
function the same way and expects the throw, so a harness that cannot see the
fault cannot pass.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "php" / "js" / "admin.js"

# The function from its declaration to the brace that closes it at its indent.
FUNCTION = re.compile(r"^  function locale \(\) \{\n.*?^  \}\n", re.MULTILINE | re.DOTALL)

# The function as it stood before, for the positive control.
OLD_FUNCTION = """  function locale () {
    const root = document.documentElement
    const own = (root.dataset.locale || '').replace('_', '-')
    return own || root.lang || 'en'
  }
"""

# Every code with two or more underscores in resources/locales.json of
# Nextcloud 34.0.3: 42 of 750.
THREE_PART = (
    "az_Cyrl_AZ", "az_Latn_AZ", "bs_Cyrl_BA", "bs_Latn_BA", "ff_Latn_BF", "ff_Latn_CM",
    "ff_Latn_GH", "ff_Latn_GM", "ff_Latn_GN", "ff_Latn_GW", "ff_Latn_LR", "ff_Latn_MR",
    "ff_Latn_NE", "ff_Latn_NG", "ff_Latn_SL", "ff_Latn_SN", "pa_Arab_PK", "pa_Guru_IN",
    "shi_Latn_MA", "shi_Tfng_MA", "sr_Cyrl_BA", "sr_Cyrl_ME", "sr_Cyrl_RS", "sr_Cyrl_XK",
    "sr_Latn_BA", "sr_Latn_ME", "sr_Latn_RS", "sr_Latn_XK", "uz_Arab_AF", "uz_Cyrl_UZ",
    "uz_Latn_UZ", "vai_Latn_LR", "vai_Vaii_LR", "yue_Hans_CN", "yue_Hant_HK", "zh_Hans_CN",
    "zh_Hans_HK", "zh_Hans_MO", "zh_Hans_SG", "zh_Hant_HK", "zh_Hant_MO", "zh_Hant_TW",
)  # fmt: skip

# Two part codes of the languages the app ships a catalogue for.
TWO_PART = ("de_DE", "de_CH", "en_US", "en_GB", "fr_FR", "es_ES", "it_IT", "nl_NL", "pt_PT", "pt_BR", "cs_CZ")

_HARNESS = r"""
const fs = require('fs')
const source = fs.readFileSync(process.argv[2], 'utf-8')
const cases = JSON.parse(fs.readFileSync(process.argv[3], 'utf-8'))
const run = new Function('document', source + '\nreturn locale()')
const report = []
for (const [dataLocale, lang] of cases) {
  const dataset = dataLocale === null ? {} : { locale: dataLocale }
  const document = { documentElement: { dataset, lang } }
  let tag = null
  let error = null
  try {
    tag = run(document)
    new Intl.NumberFormat(tag)
    new Intl.RelativeTimeFormat(tag, { numeric: 'auto' })
  } catch (thrown) {
    error = thrown.name + ': ' + thrown.message
  }
  report.push({ dataLocale, lang, tag, error })
}
process.stdout.write(JSON.stringify(report))
"""


def _node() -> str:
    node = shutil.which("node")
    # Not a skip, for the reason test_unified_search_plugin gives: a contract
    # that quietly stops judging on a machine without node is a vacuous green.
    assert node is not None, "node is required for the run of admin.js (GitHub runners carry it)"
    return node


def function_of(script: str) -> str:
    """The source of ``locale()`` out of admin.js."""
    found = FUNCTION.findall(script)
    assert len(found) == 1, f"admin.js holds {len(found)} functions named locale"
    return found[0]


def run_locale(function: str, cases: list[tuple[str | None, str]], tmp_path: Path) -> list[dict[str, Any]]:
    """What ``function`` answers for each (data-locale, lang) pair, and whether Intl takes it."""
    harness = tmp_path / "harness.js"
    harness.write_text(_HARNESS, encoding="utf-8")
    source = tmp_path / "locale.js"
    source.write_text(function, encoding="utf-8")
    pairs = tmp_path / "cases.json"
    pairs.write_text(json.dumps(cases), encoding="utf-8")
    finished = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [_node(), str(harness), str(source), str(pairs)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    assert finished.returncode == 0, finished.stderr
    report: list[dict[str, Any]] = json.loads(finished.stdout)
    assert len(report) == len(cases)
    return report


def test_the_script_formats_with_the_function_it_holds() -> None:
    # The anti vacuity clause: the function below is the one the two formats
    # of the page are built from.
    script = SCRIPT.read_text(encoding="utf-8")
    assert function_of(script)
    assert "new Intl.NumberFormat(locale())" in script
    assert "new Intl.RelativeTimeFormat(locale()" in script


def test_every_three_part_locale_becomes_its_own_tag(tmp_path: Path) -> None:
    function = function_of(SCRIPT.read_text(encoding="utf-8"))
    report = run_locale(function, [(code, "en") for code in THREE_PART], tmp_path)

    assert [entry for entry in report if entry["error"] is not None] == []
    # Its own tag, not the fallback: zh-Hant-TW and not the zh-TW of the page language.
    assert {entry["dataLocale"]: entry["tag"] for entry in report} == {
        code: code.replace("_", "-") for code in THREE_PART
    }


def test_the_two_part_locales_keep_working(tmp_path: Path) -> None:
    function = function_of(SCRIPT.read_text(encoding="utf-8"))
    report = run_locale(function, [(code, "en") for code in TWO_PART], tmp_path)

    assert [entry for entry in report if entry["error"] is not None] == []
    assert {entry["dataLocale"]: entry["tag"] for entry in report} == {
        code: code.replace("_", "-") for code in TWO_PART
    }


def test_a_value_that_is_no_tag_falls_back_without_a_throw(tmp_path: Path) -> None:
    function = function_of(SCRIPT.read_text(encoding="utf-8"))
    cases: list[tuple[str | None, str]] = [
        (None, "zh-TW"),  # no attribute: the page language
        ("", "de"),  # an empty attribute: the page language
        ("not a tag", "fr"),  # no tag: the page language
        ("not a tag", ""),  # neither: English
        ("x_", "no tag either"),  # neither: English
    ]
    report = run_locale(function, cases, tmp_path)

    assert [entry for entry in report if entry["error"] is not None] == []
    assert [entry["tag"] for entry in report] == ["zh-TW", "de", "fr", "en", "en"]


def test_the_harness_sees_the_fault_of_the_old_function(tmp_path: Path) -> None:
    # The positive control: the old line throws for every three part code and
    # for no two part code, so the two tests above can fail.
    report = run_locale(OLD_FUNCTION, [(code, "en") for code in (*THREE_PART, *TWO_PART)], tmp_path)
    thrown = {entry["dataLocale"] for entry in report if entry["error"] is not None}

    assert thrown == set(THREE_PART)
    assert all(entry["error"].startswith("RangeError") for entry in report if entry["error"] is not None)


def test_a_first_underscore_only_is_caught_even_behind_the_check(tmp_path: Path) -> None:
    # The second control: with the check in place the old replace would no
    # longer throw, it would quietly fall back to the page language. The
    # equality in test_every_three_part_locale_becomes_its_own_tag is what
    # catches that, and this shows it does.
    function = function_of(SCRIPT.read_text(encoding="utf-8"))
    mutated = function.replace(".replace(/_/g, '-')", ".replace('_', '-')")
    assert mutated != function

    report = run_locale(mutated, [("zh_Hant_TW", "zh-TW")], tmp_path)
    assert report[0]["error"] is None
    assert report[0]["tag"] == "zh-TW"
