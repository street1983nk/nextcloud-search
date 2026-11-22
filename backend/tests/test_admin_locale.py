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


def test_the_page_language_is_rewritten_the_same_way(tmp_path: Path) -> None:
    function = function_of(SCRIPT.read_text(encoding="utf-8"))
    cases: list[tuple[str | None, str]] = [
        (None, "zh_Hant_TW"),  # no attribute, the page language in underscore notation
        ("", "sr_Latn_RS"),  # an empty attribute, the same
        ("not a tag", "pt_BR"),  # no tag, a two part page language
        ("pt_BR", "en"),  # its own two part locale still wins
    ]
    report = run_locale(function, cases, tmp_path)

    assert [entry for entry in report if entry["error"] is not None] == []
    assert [entry["tag"] for entry in report] == ["zh-Hant-TW", "sr-Latn-RS", "pt-BR", "pt-BR"]


def test_a_page_language_left_as_is_is_caught(tmp_path: Path) -> None:
    # The positive control for the test above: with root.lang handed on
    # unchanged, or with its first underscore rewritten only, zh_Hant_TW
    # falls through to English instead of becoming its own tag.
    function = function_of(SCRIPT.read_text(encoding="utf-8"))
    rewritten = "(root.lang || '').replace(/_/g, '-')"
    assert rewritten in function

    unchanged = function.replace(rewritten, "root.lang")
    first_only = function.replace(rewritten, "(root.lang || '').replace('_', '-')")
    for mutated in (unchanged, first_only):
        report = run_locale(mutated, [(None, "zh_Hant_TW")], tmp_path)
        assert report[0]["error"] is None
        assert report[0]["tag"] == "en"


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


# The confirmation of the external storage (finding V-45-10-02 of the full
# test of 45-10, owner decision c of 45-19): a storage this save newly keeps
# out is named by its mount point, and by its id as well where the server
# marked its row as sharing the mount point with another one, whatever the
# type. The functions are cut out of admin.js and run in node against rows
# built the way the template renders them.
MOUNT_FUNCTIONS = ("text", "mountBoxes", "mountIdOf", "mountPointOf", "mountDuplicateOf", "confirmedMounts")
CONFIRMATION_CALL = "text('findling-rules-confirm-mounts-value', confirmedMounts(newMounts))"
ID_KEY = "%1$s (ID %2$s)"

_MOUNT_HARNESS = r"""
const fs = require('fs')
const source = fs.readFileSync(process.argv[2], 'utf-8')
const cases = JSON.parse(fs.readFileSync(process.argv[3], 'utf-8'))
const report = []
for (const c of cases) {
  const boxes = c.rows.map(function (row) {
    const label = { textContent: row[1] }
    const item = { querySelector: function (selector) { return selector === '.findling-path' ? label : null } }
    return {
      dataset: row[2] === null ? {} : { mountDuplicate: row[2] },
      getAttribute: function (name) { return name === 'data-mount-id' ? String(row[0]) : null },
      closest: function (selector) { return selector === '.findling-rules__mount' ? item : null }
    }
  })
  // The element the line is written into takes text only: markup set on it
  // would throw, so a value that reached innerHTML could not pass.
  const element = {
    textContent: '',
    set innerHTML (value) { throw new Error('innerHTML: ' + value) }
  }
  const document = {
    querySelectorAll: function (selector) {
      if (selector !== '#findling-rules-mounts-list input[data-mount-id]') {
        throw new Error('selector ' + selector)
      }
      return boxes
    },
    getElementById: function (id) { return id === 'findling-rules-confirm-mounts-value' ? element : null }
  }
  const t = function (app, sentence) {
    return Object.prototype.hasOwnProperty.call(c.catalogue, sentence) ? c.catalogue[sentence] : sentence
  }
  const run = new Function(
    'document', 't', 'newMounts',
    "const MOUNT_LIST = 'findling-rules-mounts-list'\n" + source + '\n' + c.call
  )
  let value = null
  let error = null
  try {
    run(document, t, c.ids)
    value = element.textContent
  } catch (thrown) {
    error = thrown.name + ': ' + thrown.message
  }
  report.push({ value, error })
}
process.stdout.write(JSON.stringify(report))
"""

# One row: id, mount point, and the value of data-mount-duplicate (None for a
# row without the attribute, which is how the template renders a single one).
MountRow = tuple[int, str, str | None]


def mount_functions_of(script: str) -> str:
    """The six functions of the confirmation line out of admin.js, in order."""
    parts = []
    for name in MOUNT_FUNCTIONS:
        found = re.findall(rf"^  function {name} \([^)]*\) \{{\n.*?^  \}}\n", script, re.MULTILINE | re.DOTALL)
        assert len(found) == 1, f"admin.js holds {len(found)} functions named {name}"
        parts.append(found[0])
    return "\n".join(parts)


def run_confirmation(
    functions: str,
    cases: list[tuple[list[MountRow], list[int], dict[str, str]]],
    tmp_path: Path,
    call: str = CONFIRMATION_CALL,
) -> list[dict[str, Any]]:
    """The text the confirmation line holds for each (rows, ids, catalogue)."""
    harness = tmp_path / "mounts.js"
    harness.write_text(_MOUNT_HARNESS, encoding="utf-8")
    source = tmp_path / "functions.js"
    source.write_text(functions, encoding="utf-8")
    pairs = tmp_path / "mount-cases.json"
    pairs.write_text(
        json.dumps(
            [
                {"rows": [list(row) for row in rows], "ids": ids, "catalogue": catalogue, "call": call}
                for rows, ids, catalogue in cases
            ]
        ),
        encoding="utf-8",
    )
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


def values_of(report: list[dict[str, Any]]) -> list[str | None]:
    """The line of each case, after the promise that no case threw."""
    assert [entry["error"] for entry in report if entry["error"] is not None] == []
    return [entry["value"] for entry in report]


def test_the_confirmation_names_the_id_of_storages_that_share_a_mount_point(tmp_path: Path) -> None:
    """V-45-10-02, form i: '/Gemeinsam (ID 11), /Gemeinsam (ID 12), /Projekte'."""
    script = SCRIPT.read_text(encoding="utf-8")
    # The anti vacuity clause: the line of the page is written by the
    # function run here, through text() and so through textContent.
    assert script.count(CONFIRMATION_CALL) == 1
    assert "      element.textContent = value\n" in mount_functions_of(script)

    shared: list[MountRow] = [(11, "/Gemeinsam", "true"), (12, "/Gemeinsam", "true"), (13, "/Projekte", None)]
    single: list[MountRow] = [(1, "/Archiv", None), (2, "/Belege", None)]
    report = run_confirmation(
        mount_functions_of(script),
        [
            (shared, [11, 12, 13], {}),
            (shared, [11], {}),
            (shared, [13], {}),
            (single, [1, 2], {}),
            # The sentence comes out of the catalogue: the full width
            # parentheses of zh_TW, and a language that puts the id first.
            (shared, [12], {ID_KEY: "%1$s\uff08ID %2$s\uff09"}),
            (shared, [11], {ID_KEY: "ID %2$s: %1$s"}),
        ],
        tmp_path,
    )

    assert values_of(report) == [
        "/Gemeinsam (ID 11), /Gemeinsam (ID 12), /Projekte",
        "/Gemeinsam (ID 11)",
        "/Projekte",
        "/Archiv, /Belege",
        "/Gemeinsam\uff08ID 12\uff09",
        "ID 11: /Gemeinsam",
    ]


def test_the_confirmation_follows_the_duplicate_rule_across_backends(tmp_path: Path) -> None:
    """Rule c of 45-19: the id follows the mark of the server, which counts the mount point alone.

    5 SMB/CIFS, 8 SFTP and 17 SMB/CIFS all on /Share: ExternalMountService
    marks all three, so the template gives all three data-mount-duplicate
    and the confirmation names every id. Only the exact value true counts.
    """
    script = SCRIPT.read_text(encoding="utf-8")
    share: list[MountRow] = [(5, "/Share", "true"), (8, "/Share", "true"), (17, "/Share", "true")]
    odd: list[MountRow] = [(5, "/Share", "TRUE"), (8, "/Share", "1"), (17, "/Share", "")]
    report = run_confirmation(
        mount_functions_of(script),
        [(share, [5, 8, 17], {}), (share, [8], {}), (odd, [5, 8, 17], {})],
        tmp_path,
    )

    assert values_of(report) == [
        "/Share (ID 5), /Share (ID 8), /Share (ID 17)",
        "/Share (ID 8)",
        "/Share, /Share, /Share",
    ]


def test_the_confirmation_keeps_markup_and_replacement_patterns_as_text(tmp_path: Path) -> None:
    """T-45-65: a mount point is text, and the id is put in by one pass with a function."""
    script = SCRIPT.read_text(encoding="utf-8")
    rows: list[MountRow] = [
        (3, "<img src=x onerror=alert(1)>", "true"),
        (4, "<img src=x onerror=alert(1)>", "true"),
        (6, "$&x", "true"),
        (7, "$&x", "true"),
        (9, "/a%2$s", "true"),
        (10, "/a%2$s", "true"),
        (14, "/b%1$s$'", None),
    ]
    report = run_confirmation(mount_functions_of(script), [(rows, [3, 6, 9, 14], {})], tmp_path)

    assert values_of(report) == [
        "<img src=x onerror=alert(1)> (ID 3), $&x (ID 6), /a%2$s (ID 9), /b%1$s$'",
    ]
