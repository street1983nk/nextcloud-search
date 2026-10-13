"""The contract of php/js/unified-search.js, the filter entries of plan 32-04.

The script puts seven entries of Findling into the menu of the Nextcloud unified
search: six type groups and one folder entry. It runs on every page of every
logged in user, inside a frontend this repository does not own, so the contract
is held from two sides that do not share a method:

- **a reading of the source** (comments removed, string literals kept): the six
  groups in the order of ``SearchFilters::TYPES`` as PHP declares it, the ids,
  ``appId`` and ``searchFrom``, feature detection before every API, the emit
  inside a ``setTimeout``, no empty folder value, the translation keys of the
  wording draft D-32-04 and a list of prohibitions. Every rule has a self test
  on a sample script, with the clean sample as the positive control.
- **a run of the script** in node, inside a sandbox that plays the core
  frontend: what is registered, what each click sends and when, what a folder
  choice sends, and that a page without one of the APIs neither registers nor
  throws. The run sees behaviour, so a rule the reading gets wrong cannot hide
  a wrong script, and the other way round.

The core facts these rules come from, read in nextcloud/server stable33,
stable34 and stable35 on 2026-10-13: ``registerFilterAction`` in
``core/src/unified-search.ts``; ``addProviderFilter`` calls the callback before
it pushes the chip, and a second click on an applied entry removes the chip and
pushes a fresh one without ``extraParams`` (``UnifiedSearchModal.vue``
stable34:674-704, stable35:1212-1240); ``handlePluginFilter`` sets
``extraParams`` only on a chip that already exists (stable34:828-845,
stable35:1365-1380); a parameter with an empty value is refused by the core with
HTTP 400 before Findling is asked (32-RESEARCH, pitfall 3).
"""

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from test_admin_ui_contract import scan_prose, scan_script
from test_type_vocabulary_parity import PHP_SEARCH_FILTERS, php_type_groups

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "php" / "js" / "unified-search.js"

APP_ID = "findling"
TYPE_ID_PREFIX = "findling-type-"
FOLDER_ID = "findling-folder"
ADD_FILTER_EVENT = "nextcloud:unified-search:add-filter"

# The six group names as the catalogues already carry them, one per group.
GROUP_KEYS = ("PDF", "Documents", "Spreadsheets", "Presentations", "Images", "Text")

# The four new keys of the wording draft D-32-04. The catalogues follow in plan
# 32-05; until then the script may only use these and the six above.
NEW_KEYS = (
    "File contents: %s",
    "File contents in a folder",
    "File contents in %s",
    "Choose the folder to search in",
)
ALLOWED_KEYS = frozenset(GROUP_KEYS + NEW_KEYS)

# What a script that runs on every page must never do, with the reason in the
# message. Matched on the code with comments removed.
PROHIBITED = (
    (re.compile(r"\binnerHTML\b"), "builds markup from a string (innerHTML)"),
    (re.compile(r"\bouterHTML\b"), "builds markup from a string (outerHTML)"),
    (re.compile(r"\binsertAdjacentHTML\b"), "builds markup from a string (insertAdjacentHTML)"),
    (re.compile(r"\beval\s*\("), "evaluates a string as code (eval)"),
    (re.compile(r"\bFunction\s*\("), "evaluates a string as code (Function)"),
    (re.compile(r"\bconsole\s*\."), "writes to the console of somebody else's page"),
    (re.compile(r"\bfetch\s*\("), "talks to the network (fetch)"),
    (re.compile(r"\bXMLHttpRequest\b"), "talks to the network (XMLHttpRequest)"),
    (re.compile(r"\bimport\b"), "is a module (import), but no bundler serves this app"),
    (re.compile(r"\brequire\s*\("), "is a module (require), but no bundler serves this app"),
    (re.compile(r"\blocalStorage\b"), "keeps state in localStorage"),
)

# Each API the script touches, and the typeof question that has to be asked
# before it is called. The legacy search has no OCA.UnifiedSearch, a future core
# may drop the deprecated file picker, and a page of another app must never
# break because of this script.
FEATURE_CHECKS = (
    ("registerFilterAction", re.compile(r"typeof\s+[\w.]*\bregisterFilterAction\s*[!=]==\s*'function'")),
    ("the emit of the event bus", re.compile(r"typeof\s+[\w.]*\bemit\s*[!=]==\s*'function'")),
    ("OC.dialogs.filepicker", re.compile(r"typeof\s+[\w.]*\bfilepicker\s*[!=]==\s*'function'")),
    ("OC.imagePath", re.compile(r"typeof\s+[\w.]*\bimagePath\s*[!=]==\s*'function'")),
)

_STRING_OR_COMMENT = re.compile(
    r"""('(?:\\.|[^'\\\n])*'|"(?:\\.|[^"\\\n])*"|`(?:\\.|[^`\\])*`)|(/\*.*?\*/|//[^\n]*)""",
    re.DOTALL,
)
_STRING = re.compile(r"""'(?:\\.|[^'\\\n])*'|"(?:\\.|[^"\\\n])*"|`(?:\\.|[^`\\])*`""", re.DOTALL)


def code_of(source: str) -> str:
    """The script without its comments, string literals kept as they are.

    One pass over strings and comments together, so a ``//`` inside a string is
    not taken for a comment and a quote inside a comment does not open a string.
    """
    return _STRING_OR_COMMENT.sub(lambda match: match.group(1) or "", source)


def _blank_strings(code: str) -> str:
    """The code with every string literal replaced by spaces of the same length.

    Used for bracket matching only, so a parenthesis inside a label cannot close
    a call.
    """
    return _STRING.sub(lambda match: " " * len(match.group(0)), code)


def _argument_spans(code: str, callee: str) -> list[tuple[int, int]]:
    """The argument lists of every call of ``callee``, as offsets into ``code``."""
    blank = _blank_strings(code)
    spans: list[tuple[int, int]] = []
    for match in re.finditer(r"\b" + re.escape(callee) + r"\s*\(", blank):
        depth = 0
        for index in range(match.end() - 1, len(blank)):
            if blank[index] == "(":
                depth += 1
            elif blank[index] == ")":
                depth -= 1
                if depth == 0:
                    spans.append((match.end(), index))
                    break
    return spans


def type_entries(code: str) -> list[tuple[str, str]] | None:
    """The pairs of ``TYPE_ENTRIES`` as (group, English key), or None without the constant."""
    match = re.search(r"\bconst\s+TYPE_ENTRIES\s*=\s*\[(.*?)\]\s*\n", code, re.DOTALL)
    if match is None:
        return None
    return re.findall(r"\[\s*'([a-z]+)'\s*,\s*'([^']*)'\s*\]", match.group(1))


def _app_id_names(code: str) -> set[str]:
    """The identifiers a ``const`` binds to the string 'findling'."""
    return set(re.findall(r"\bconst\s+(\w+)\s*=\s*'findling'", code))


def contract_findings(name: str, source: str, php_types: list[str] | None) -> list[str]:
    """Every rule of the contract the source breaks, one line each."""
    code = code_of(source)
    findings: list[str] = []

    # The six groups, in the order PHP declares them and with the keys the
    # catalogues carry.
    entries = type_entries(code)
    if entries is None:
        findings.append(f"{name}: has no constant TYPE_ENTRIES")
    else:
        groups = [group for group, _ in entries]
        if php_types is None or groups != php_types:
            findings.append(f"{name}: TYPE_ENTRIES lists {groups}, SearchFilters::TYPES says {php_types}")
        findings.extend(
            f"{name}: the group {group} is labelled with the key {key!r}, which is not a group name of the catalogues"
            for group, key in entries
            if key not in GROUP_KEYS
        )

    # The ids. Never exactly 'findling', which is the id of the provider and
    # would collide with it in the chip list of the core.
    findings.extend(
        f"{name}: lacks the id literal {literal!r}"
        for literal in (TYPE_ID_PREFIX, FOLDER_ID)
        if repr(literal) not in code
    )
    names = _app_id_names(code)
    for value in re.findall(r"\bid\s*:\s*([^,}\s]+)", code):
        if value in {"'findling'", '"findling"'} or value in names:
            findings.append(f"{name}: registers or sends the id 'findling', the id of the provider itself")

    # appId and searchFrom: 'findling' on every entry and every event.
    for key in ("appId", "searchFrom"):
        values = re.findall(r"\b" + key + r"\s*:\s*([^,}\s]+)", code)
        if not values:
            findings.append(f"{name}: never sets {key}")
        findings.extend(
            f"{name}: sets {key} to {value}, not to 'findling'"
            for value in values
            if value != "'findling'" and value not in names
        )

    # Two call sites: one in the loop over the six groups, one for the folder.
    calls = len(re.findall(r"\.registerFilterAction\s*\(", code))
    if calls != 2:
        findings.append(
            f"{name}: calls registerFilterAction at {calls} places, expected 2 (the type loop and the folder)"
        )

    findings.extend(
        f"{name}: never asks whether {api} exists before using it"
        for api, pattern in FEATURE_CHECKS
        if pattern.search(code) is None
    )
    if re.search(r"(?<![\w.])_nc_event_bus\b", code):
        findings.append(f"{name}: reads _nc_event_bus as a bare global instead of window._nc_event_bus")

    # The emit happens after the core has pushed the chip, never inside the
    # callback that runs before the push.
    emits = [match.start() for match in re.finditer(r"\.emit\s*\(", code)]
    spans = _argument_spans(code, "setTimeout")
    if not emits:
        findings.append(f"{name}: never emits {ADD_FILTER_EVENT}")
    findings.extend(
        f"{name}: emits outside a setTimeout, before the core has pushed the chip"
        for offset in emits
        if not any(start <= offset < end for start, end in spans)
    )
    if repr(ADD_FILTER_EVENT) not in code:
        findings.append(f"{name}: never names the event {ADD_FILTER_EVENT}")

    # No empty folder value: the core answers an empty parameter with HTTP 400
    # and Findling is never asked.
    if re.search(r"\bfolder\s*:\s*['\"`]", code):
        findings.append(f"{name}: sends a literal folder value")
    if re.search(r"(?:\|\||\?\?)\s*''", code):
        findings.append(f"{name}: falls back to an empty string, which would reach the core as an empty parameter")
    if not (re.search(r"!==\s*''", code) and re.search(r"!==\s*'/'", code)):
        findings.append(f"{name}: sets the folder without ruling out '' and the root '/'")

    # Translation keys: only the ten of the draft, every new one used, and only
    # through the catalogue of findling.
    used = set(re.findall(r"\bt\(\s*'findling'\s*,\s*'((?:\\.|[^'\\])*)'", code))
    findings.extend(
        f"{name}: translates the key {key!r}, which is not in the draft D-32-04" for key in sorted(used - ALLOWED_KEYS)
    )
    findings.extend(
        f"{name}: never translates the key {key!r} of the draft D-32-04" for key in NEW_KEYS if key not in used
    )
    if re.search(r"\bt\(\s*(?!'findling'\s*,)", code):
        findings.append(f"{name}: translates through another catalogue than the one of findling")

    findings.extend(f"{name}: {reason}" for pattern, reason in PROHIBITED if pattern.search(code) is not None)

    return findings


# -- the run in node ---------------------------------------------------------

# A sandbox that plays the core frontend. It reports what the script registered
# and what each callback sent before and after the timers ran, plus the error
# message of anything that was thrown. Translations are marked with brackets, so
# a label that did not go through t() is visible in the report.
_HARNESS = r"""
'use strict'
const fs = require('fs')
const vm = require('vm')
const source = fs.readFileSync(process.argv[2], 'utf8')

function sandbox (options) {
  const log = { registered: [], emitted: [], pickers: [], listeners: [], timers: [], errors: [] }
  const win = {}
  win.window = win
  win.document = {
    readyState: options.readyState || 'complete',
    addEventListener: (name, fn) => log.listeners.push([name, fn]),
  }
  win.setTimeout = (fn) => { log.timers.push(fn); return log.timers.length }
  win.t = (app, text) => app === 'findling' ? '[' + text + ']' : '?'
  if (options.api !== false) {
    win.OCA = { UnifiedSearch: {} }
    if (options.register !== false) {
      win.OCA.UnifiedSearch.registerFilterAction = (action) => {
        if (options.registerThrows) { throw new Error('register failed') }
        log.registered.push(action)
      }
    }
  }
  win.OC = {}
  if (options.imagePath !== false) {
    win.OC.imagePath = (app, file) => '/apps/' + app + '/img/' + file + '.svg'
  }
  if (options.dialogs !== false) {
    win.OC.dialogs = {
      FILEPICKER_TYPE_CHOOSE: 1,
      filepicker: (...args) => log.pickers.push(args),
    }
  }
  if (options.bus !== false) {
    win._nc_event_bus = { emit: (name, detail) => log.emitted.push({ name, detail }) }
  }
  const context = vm.createContext(win)
  try {
    vm.runInContext(source, context)
    if (options.fireLoaded) {
      log.registeredBeforeLoaded = log.registered.length
      for (const [name, fn] of log.listeners) {
        if (name === 'DOMContentLoaded') { fn() }
      }
    }
  } catch (error) {
    log.errors.push(String(error && error.message))
  }
  return log
}

function flush (log) {
  while (log.timers.length > 0) {
    try { log.timers.shift()() } catch (error) { log.errors.push(String(error && error.message)) }
  }
}

function click (log, id, apply) {
  const action = log.registered.find((entry) => entry.id === id)
  const before = log.emitted.length
  try { action.callback(apply) } catch (error) { log.errors.push(String(error && error.message)) }
  const synchronous = log.emitted.length - before
  flush(log)
  return { synchronous, sent: log.emitted.slice(before + synchronous) }
}

function pick (log, value) {
  const picker = log.pickers[log.pickers.length - 1]
  const before = log.emitted.length
  try { picker[1](value) } catch (error) { log.errors.push(String(error && error.message)) }
  const synchronous = log.emitted.length - before
  flush(log)
  return { synchronous, sent: log.emitted.slice(before + synchronous) }
}

const report = {}

const full = sandbox({})
report.registered = full.registered.map((entry) => ({
  id: entry.id, appId: entry.appId, searchFrom: entry.searchFrom, label: entry.label,
  icon: entry.icon, callback: typeof entry.callback,
}))
report.types = {}
for (const entry of full.registered.filter((item) => item.id.startsWith('findling-type-'))) {
  report.types[entry.id] = { first: click(full, entry.id, true), again: click(full, entry.id, false) }
}
const folder = {}
folder.open = click(full, 'findling-folder', true)
folder.pickerCount = full.pickers.length
folder.pickerArgs = full.pickers.length
  ? full.pickers[0].map((arg) => typeof arg === 'function' ? 'function' : arg)
  : null
folder.chosen = pick(full, '/Projekte/2026/')
folder.again = click(full, 'findling-folder', false)
folder.pickerCountAfterAgain = full.pickers.length
click(full, 'findling-folder', true)
folder.root = pick(full, '/')
click(full, 'findling-folder', true)
folder.empty = pick(full, '')
click(full, 'findling-folder', true)
folder.notAString = pick(full, ['/Projekte'])
click(full, 'findling-folder', true)
folder.replacement = pick(full, "/Belege/$& und $'")
report.folder = folder
report.errors = full.errors

const loading = sandbox({ readyState: 'loading', fireLoaded: true })
report.loading = { before: loading.registeredBeforeLoaded, after: loading.registered.length, errors: loading.errors }

report.missing = {}
for (const [label, options] of Object.entries({
  noApi: { api: false },
  noRegister: { register: false },
  registerThrows: { registerThrows: true },
  noDialogs: { dialogs: false },
  noImagePath: { imagePath: false },
  noBus: { bus: false },
})) {
  const log = sandbox(options)
  const clicks = []
  for (const entry of log.registered) {
    clicks.push(click(log, entry.id, true))
  }
  report.missing[label] = {
    registered: log.registered.map((entry) => entry.id),
    icons: log.registered.map((entry) => entry.icon),
    emitted: log.emitted.length,
    pickers: log.pickers.length,
    errors: log.errors,
  }
}

process.stdout.write(JSON.stringify(report))
"""


def _node() -> str:
    node = shutil.which("node")
    # Not a skip: a contract that quietly stops judging on a machine without
    # node is the vacuous green this repository refuses everywhere else.
    assert node is not None, "node is required for the run of unified-search.js (GitHub runners carry it)"
    return node


def run_in_node(script: Path, tmp_path: Path) -> dict[str, Any]:
    """The report of the sandbox run of ``script``."""
    harness = tmp_path / "harness.js"
    harness.write_text(_HARNESS, encoding="utf-8")
    finished = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [_node(), str(harness), str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    assert finished.returncode == 0, finished.stderr
    report: dict[str, Any] = json.loads(finished.stdout)
    return report


# -- the real script ---------------------------------------------------------


def test_the_plugin_exists_and_is_not_empty() -> None:
    # The anti vacuity clause: every reader below finds nothing in a file that
    # is not there.
    assert PLUGIN.is_file()
    assert code_of(PLUGIN.read_text(encoding="utf-8")).strip() != ""


def test_the_plugin_keeps_the_contract() -> None:
    php_types = php_type_groups(PHP_SEARCH_FILTERS.read_text(encoding="utf-8"))
    assert php_types is not None

    assert contract_findings(PLUGIN.name, PLUGIN.read_text(encoding="utf-8"), php_types) == []


def test_the_plugin_breaks_none_of_the_prohibitions_of_the_two_pages() -> None:
    source = PLUGIN.read_text(encoding="utf-8")

    assert scan_script(PLUGIN.name, source) + scan_prose(PLUGIN.name, source) == []


def test_node_accepts_the_syntax_of_the_plugin() -> None:
    finished = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [_node(), "--check", str(PLUGIN)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert finished.returncode == 0, finished.stderr


def test_the_run_registers_seven_entries_in_the_order_of_the_php_groups(tmp_path: Path) -> None:
    php_types = php_type_groups(PHP_SEARCH_FILTERS.read_text(encoding="utf-8"))
    assert php_types is not None
    report = run_in_node(PLUGIN, tmp_path)

    assert report["errors"] == []
    assert [entry["id"] for entry in report["registered"]] == [
        *(TYPE_ID_PREFIX + group for group in php_types),
        FOLDER_ID,
    ]
    for entry in report["registered"]:
        assert entry["appId"] == APP_ID
        assert entry["searchFrom"] == APP_ID
        assert entry["id"] != APP_ID
        assert entry["icon"] == "/apps/findling/img/app.svg"
        assert entry["callback"] == "function"
    labels = [entry["label"] for entry in report["registered"]]
    assert labels == [f"[File contents: [{key}]]" for key in GROUP_KEYS] + ["[File contents in a folder]"]


def test_every_type_click_sends_its_group_later_and_again_on_the_second_click(tmp_path: Path) -> None:
    report = run_in_node(PLUGIN, tmp_path)

    assert len(report["types"]) == len(GROUP_KEYS)
    for entry_id, clicks in report["types"].items():
        group = entry_id.removeprefix(TYPE_ID_PREFIX)
        label = next(entry["label"] for entry in report["registered"] if entry["id"] == entry_id)
        expected = {
            "name": ADD_FILTER_EVENT,
            "detail": {
                "id": entry_id,
                "appId": APP_ID,
                "searchFrom": APP_ID,
                "filterUpdateText": label,
                "filterParams": {"types": group},
            },
        }
        # Pitfall 2: the second click (apply false) re-creates the chip without
        # extraParams, so it has to send again.
        for click in (clicks["first"], clicks["again"]):
            assert click["synchronous"] == 0
            assert click["sent"] == [expected]


def test_the_folder_entry_opens_the_folder_picker_and_sends_the_chosen_folder(tmp_path: Path) -> None:
    folder = run_in_node(PLUGIN, tmp_path)["folder"]

    assert folder["open"] == {"synchronous": 0, "sent": []}
    assert folder["pickerCount"] == 1
    assert folder["pickerArgs"] == [
        "[Choose the folder to search in]",
        "function",
        False,
        ["httpd/unix-directory"],
        True,
        1,
        "/",
        {"allowDirectoryChooser": True},
    ]
    assert folder["chosen"]["synchronous"] == 0
    assert folder["chosen"]["sent"] == [
        {
            "name": ADD_FILTER_EVENT,
            "detail": {
                "id": FOLDER_ID,
                "appId": APP_ID,
                "searchFrom": APP_ID,
                "filterUpdateText": "[File contents in %s]".replace("%s", "2026"),
                "filterParams": {"folder": "/Projekte/2026"},
            },
        }
    ]
    # The second click on the applied entry sends the remembered folder again,
    # without a second picker.
    assert folder["again"]["sent"] == folder["chosen"]["sent"]
    assert folder["pickerCountAfterAgain"] == 1


def test_the_root_and_an_empty_choice_send_no_folder_value_at_all(tmp_path: Path) -> None:
    folder = run_in_node(PLUGIN, tmp_path)["folder"]

    for choice in (folder["root"], folder["empty"]):
        assert [sent["detail"]["filterParams"] for sent in choice["sent"]] == [{}]
    assert folder["notAString"]["sent"] == []


def test_a_folder_name_is_text_and_never_a_replacement_pattern(tmp_path: Path) -> None:
    # String.prototype.replace reads $& and $' in a replacement string; a folder
    # is named by its owner, so the chip has to show the name as it is.
    folder = run_in_node(PLUGIN, tmp_path)["folder"]

    assert [sent["detail"]["filterUpdateText"] for sent in folder["replacement"]["sent"]] == [
        "[File contents in $& und $']"
    ]


def test_the_plugin_waits_for_the_document_when_it_is_still_loading(tmp_path: Path) -> None:
    loading = run_in_node(PLUGIN, tmp_path)["loading"]

    assert loading == {"before": 0, "after": 7, "errors": []}


@pytest.mark.parametrize(
    ("case", "registered", "pickers"),
    [
        ("noApi", [], 0),
        ("noRegister", [], 0),
        ("registerThrows", [], 0),
        (
            "noDialogs",
            [
                TYPE_ID_PREFIX + group
                for group in ("pdf", "documents", "spreadsheets", "presentations", "images", "text")
            ],
            0,
        ),
        ("noImagePath", None, 1),
        ("noBus", None, 1),
    ],
)
def test_a_missing_api_registers_less_and_never_throws(
    tmp_path: Path, case: str, registered: list[str] | None, pickers: int
) -> None:
    missing = run_in_node(PLUGIN, tmp_path)["missing"][case]

    assert missing["errors"] == []
    if registered is not None:
        assert missing["registered"] == registered
    else:
        assert len(missing["registered"]) == 7
    assert missing["pickers"] == pickers
    if case == "noImagePath":
        assert missing["icons"] == [""] * 7
    if case == "noBus":
        assert missing["emitted"] == 0


# -- self tests --------------------------------------------------------------

# A sample that keeps every rule, written for these tests and not copied from
# the plugin. It is the positive control: the reader has to find nothing in it,
# or every finding below would prove nothing.
_SAMPLE = """'use strict'
;(function () {
  const APP = 'findling'
  const TYPE_ENTRIES = [
    ['pdf', 'PDF'],
    ['documents', 'Documents'],
    ['spreadsheets', 'Spreadsheets'],
    ['presentations', 'Presentations'],
    ['images', 'Images'],
    ['text', 'Text'],
  ]
  const t = typeof window.t === 'function' ? window.t : function (app, text) { return text }
  function later (detail) {
    setTimeout(function () {
      const bus = window._nc_event_bus
      if (bus && typeof bus.emit === 'function') {
        bus.emit('nextcloud:unified-search:add-filter', detail)
      }
    }, 0)
  }
  function picon () {
    return window.OC && typeof window.OC.imagePath === 'function' ? window.OC.imagePath(APP, 'app') : ''
  }
  function folderParams (path) {
    const params = {}
    if (path !== '' && path !== '/') {
      params.folder = path
    }
    return params
  }
  const api = window.OCA && window.OCA.UnifiedSearch
  if (!api || typeof api.registerFilterAction !== 'function') {
    return
  }
  TYPE_ENTRIES.forEach(function (entry) {
    const id = 'findling-type-' + entry[0]
    const label = t('findling', 'File contents: %s').replace('%s', function () { return t('findling', entry[1]) })
    api.registerFilterAction({ id: id, appId: APP, searchFrom: APP, label: label, icon: picon(), callback: function () {
      later({ id: id, appId: APP, searchFrom: APP, filterUpdateText: label, filterParams: { types: entry[0] } })
    } })
  })
  const dialogs = window.OC && window.OC.dialogs
  if (dialogs && typeof dialogs.filepicker === 'function') {
    api.registerFilterAction({ id: 'findling-folder', appId: 'findling', searchFrom: APP,
      label: t('findling', 'File contents in a folder'), icon: picon(), callback: function () {
        dialogs.filepicker(t('findling', 'Choose the folder to search in'), function (path) {
          later({ id: 'findling-folder', appId: APP, searchFrom: APP,
            filterUpdateText: t('findling', 'File contents in %s'), filterParams: folderParams(path) })
        })
      } })
  }
})()
"""

_TYPES = ["pdf", "documents", "spreadsheets", "presentations", "images", "text"]


def test_the_sample_keeps_the_contract_which_makes_the_findings_below_meaningful() -> None:
    assert contract_findings("sample.js", _SAMPLE, _TYPES) == []


def test_the_sample_runs_and_the_run_sees_what_the_reading_sees(tmp_path: Path) -> None:
    sample = tmp_path / "sample.js"
    sample.write_text(_SAMPLE, encoding="utf-8")

    report = run_in_node(sample, tmp_path)

    assert report["errors"] == []
    assert len(report["registered"]) == 7
    assert all(click["first"]["synchronous"] == 0 for click in report["types"].values())


def test_markup_from_a_string_is_a_finding() -> None:
    source = _SAMPLE.replace("const params = {}", "const params = {}\n    document.body.innerHTML = path")

    assert contract_findings("sample.js", source, _TYPES) == ["sample.js: builds markup from a string (innerHTML)"]


def test_an_emit_inside_the_callback_is_a_finding(tmp_path: Path) -> None:
    source = _SAMPLE.replace(
        "later({ id: id,", "window._nc_event_bus.emit('nextcloud:unified-search:add-filter', { id: id,"
    )
    assert source != _SAMPLE

    assert contract_findings("sample.js", source, _TYPES) == [
        "sample.js: emits outside a setTimeout, before the core has pushed the chip"
    ]

    # The run sees the same mistake from the other side.
    sample = tmp_path / "sync.js"
    sample.write_text(source, encoding="utf-8")
    report = run_in_node(sample, tmp_path)
    assert all(click["first"]["synchronous"] == 1 for click in report["types"].values())


def test_an_empty_folder_value_is_a_finding() -> None:
    literal = _SAMPLE.replace("filterParams: folderParams(path)", "filterParams: { folder: '' }")
    unguarded = _SAMPLE.replace("if (path !== '' && path !== '/') {", "if (path) {")
    fallback = _SAMPLE.replace("params.folder = path", "params.folder = path || ''")
    assert len({literal, unguarded, fallback, _SAMPLE}) == 4

    assert contract_findings("sample.js", literal, _TYPES) == ["sample.js: sends a literal folder value"]
    assert contract_findings("sample.js", unguarded, _TYPES) == [
        "sample.js: sets the folder without ruling out '' and the root '/'"
    ]
    assert contract_findings("sample.js", fallback, _TYPES) == [
        "sample.js: falls back to an empty string, which would reach the core as an empty parameter"
    ]


def test_the_id_of_the_provider_is_a_finding() -> None:
    literal = _SAMPLE.replace("{ id: 'findling-folder', appId: 'findling'", "{ id: 'findling', appId: 'findling'")
    bound = _SAMPLE.replace("{ id: 'findling-folder', appId: 'findling'", "{ id: APP, appId: 'findling'")
    assert len({literal, bound, _SAMPLE}) == 3

    expected = "sample.js: registers or sends the id 'findling', the id of the provider itself"
    assert expected in contract_findings("sample.js", literal, _TYPES)
    assert expected in contract_findings("sample.js", bound, _TYPES)


def test_a_group_order_other_than_the_php_one_is_a_finding() -> None:
    swapped = _SAMPLE.replace(
        "['pdf', 'PDF'],\n    ['documents', 'Documents'],", "['documents', 'Documents'],\n    ['pdf', 'PDF'],"
    )
    assert swapped != _SAMPLE

    assert contract_findings("sample.js", swapped, _TYPES) == [
        (
            "sample.js: TYPE_ENTRIES lists ['documents', 'pdf', 'spreadsheets', 'presentations', 'images', 'text'], "
            "SearchFilters::TYPES says ['pdf', 'documents', 'spreadsheets', 'presentations', 'images', 'text']"
        )
    ]


def test_a_missing_feature_check_and_a_foreign_key_are_findings() -> None:
    unchecked = _SAMPLE.replace("if (dialogs && typeof dialogs.filepicker === 'function') {", "if (dialogs) {")
    foreign = _SAMPLE.replace("'File contents in a folder'", "'Search in a folder'")
    assert len({unchecked, foreign, _SAMPLE}) == 3

    assert contract_findings("sample.js", unchecked, _TYPES) == [
        "sample.js: never asks whether OC.dialogs.filepicker exists before using it"
    ]
    assert contract_findings("sample.js", foreign, _TYPES) == [
        "sample.js: translates the key 'Search in a folder', which is not in the draft D-32-04",
        "sample.js: never translates the key 'File contents in a folder' of the draft D-32-04",
    ]


def test_a_comment_neither_hides_nor_creates_a_finding() -> None:
    commented = _SAMPLE.replace("'use strict'", "'use strict'\n// innerHTML, console.log and eval( are only words here")
    hidden = _SAMPLE.replace(
        "        bus.emit('nextcloud:unified-search:add-filter', detail)",
        "        // bus.emit('nextcloud:unified-search:add-filter', detail)",
    )
    assert len({commented, hidden, _SAMPLE}) == 3

    assert contract_findings("sample.js", commented, _TYPES) == []
    assert "sample.js: never emits nextcloud:unified-search:add-filter" in contract_findings(
        "sample.js", hidden, _TYPES
    )
