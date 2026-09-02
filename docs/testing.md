# What is tested, and the one gap that is left

This document exists because of a single honest answer to the question "is the
PHP half tested?". It is not, not by a unit test, and `php -l` is a syntax check
and not a test. What follows is what covers which half, what the remaining gap
is, and what closes it.

## The two halves are not tested the same way

| Half | Gates | Runs where |
|---|---|---|
| Python backend | ruff, ruff format, pyright basic, vulture, pytest | locally before every commit, and in `python.yml` |
| PHP companion | `php -l`, the textual gates in `backend/tests/`, plus both integration jobs end to end | `php.yml` and `integration.yml`, CI only |

The reason for the difference is not a decision, it is the development machine:
there is no PHP and no composer on it, and the local system Python is broken
which is why the backend runs through `uv`. Every PHP change in this repository
is therefore written once and verified in CI, never executed while it is written.
That is worth knowing when reading a PHP diff here.

What the PHP half is covered by today is therefore three things and not one:
`php -l` over `php/lib`, `php/appinfo` and `php/templates` inside the container,
the two integration jobs end to end, and the textual gates below, which read the
PHP sources with a Python parser and judge them. The last group is the part that
grew with phase 4: the admin page added a second route class, a design contract
and a second path space, and each of those is a property no syntax check and no
end to end job can see. What is still missing is a PHPUnit suite, and the gap
section further down names the twelve behaviours that would fill it.

## The textual gates over the PHP sources

Every one of these lives in `backend/tests/` and runs with the ordinary
`uv run python -m pytest -q`. They parse text instead of executing PHP, which is
a deliberate trade: a gate that pins a property is worth more than the perfect
test that does not exist on a machine without PHP. Each of them also carries self
tests against staged samples, so that a gate whose body was deleted cannot report
zero violations over zero routes and look healthy.

| Gate | What it prevents |
|---|---|
| `test_readonly_gate.py` (Gate A) | A write call on a user file. The allowlist holds exactly three entries, and a fourth way of opening a file for writing fails the gate instead of being reviewed later. |
| `test_php_trust_boundary.py` (Gate B) | A route without its boundary, in either of the two route classes: an `ApiRoute` missing `ExAppRequired` or `rejectForeignCaller` as its first statement hands the work stock to a foreign container, and a `FrontpageRoute` carrying `NoAdminRequired`, `PublicPage`, `NoCSRFRequired` or `ExAppRequired` hands the admin page to somebody who is not the admin. The route count is a ratchet, so a plan that adds a route has to raise it. |
| `test_extract_errors.py` | A drift between the three reason lists. A reason code the container writes and the PHP side has no label for would reach an admin as an empty cell. |
| `test_allowlist_parity.py` | A drift between the two mimetype allowlists. A type one side reads and the other refuses is a file that is queued forever or never counted. |
| `test_admin_ui_contract.py` (Gate C) | The mechanically checkable prohibitions of the design contract, over the three files of the page: no markup built from a string in the script, no unescaped printing in the template, no inline script, no literal colour in the stylesheet, no removed focus ring, no dash that is not a hyphen, no emoji, and none of the five Nextcloud APIs the contract retired. It says nothing about how the page looks; that is the human sight check. |
| `test_exclusion_path_space.py` | A second exclusion path space. The crawl, the event listener, the clearing and the diagnosis have to compare a prefix through the one helper on the one space, otherwise a Team Folder file is judged by a rule that does not apply to it. |
| `test_status_endpoint.py`, `test_rates_endpoint.py`, `test_diagnose_endpoint.py` | The three container routes the admin page reads: the shape of the answer, the privacy boundary (numbers, never names) and the answer for a file nothing knows. |

## What the integration jobs do cover

`integration.yml` is not a smoke test, it exercises the PHP paths that matter,
through the real unified search API of a real Nextcloud:

- the search provider is registered and visible (`walking-skeleton`, canary step)
- a search returns exactly one canary hit whose subline can only have been
  produced inside the backend, for the user the signed header named
- the permission recheck lets that canary through, which is the one exception in
  `Provider::search` and the one entry `ExAppService::filterCandidates` accepts
  without a file behind it
- an ordinary search term does not see the canary, so the diagnostic hit cannot
  colour a normal search unnoticed
- the provider reports `term` and `title-only` as its filters, which is what
  keeps a client with a set filter from skipping the provider without a word
- a backend that hangs costs one result group and not the search: status 200, no
  entries, under six seconds against a stub that answers after ten
- a backend that is gone costs one result group and not the search, which is the
  `is_array($response)` branch
- the content gateway delivers every file of the reference corpus to its owner
  (`readonly-gate`)
- the same file ids answer 404 for a user who exists and owns nothing
- the same file ids answer 404 for a user id that does not exist at all, which is
  the case that used to answer 500 and told a caller which accounts exist
- not one byte and not one timestamp of the corpus moves in the process

## The three acceptances of phase 3, and what each one does not prove

Since phase 3 the three acceptance statements of the roadmap are gates that run
on every commit instead of sentences somebody once checked. Each of them is
listed with what it proves and with what it deliberately does not, because an
acceptance test that is read as proving more than it does is worse than none.

**Gate B over the whole OCR corpus** (`readonly-gate`). The corpus is indexed
with the OCR track switched on, and file list, checksums, modification times and
sizes are frozen before and compared afterwards. What it proves: neither the
download path nor the renderer nor the engine writes to a user file, over
thirty three files including twelve broken PDFs, five pictures and a nine
gigapixel page. What it does not prove: that nothing is written anywhere else on
the instance. It watches the corpus directory, not the data directory.

Its second half is the verdict counter, and it exists because the first half can
be green for the wrong reason. A comparison only measures the files the run
touched, so a pass that never reached the pictures would compare thirty three
untouched files with thirty three untouched files and say nothing at all. The
counter therefore asserts, file by file, the verdict `testdata/CORPUS.md` names,
and it counts the caps of the OCR cascade separately. What it does not prove:
that the recognised text is any good. It only knows that a file was judged and
how.

**IDX-04, word for word** (`reconcile-and-dach`). A file is created, a second
one changed and a third one removed past the event path, with `occ files:scan`,
which is what a mass import and a restore from a backup look like. A step in
between proves that no queue row was created, then exactly one reconcile cycle
runs, and afterwards the new file is findable, the changed one answers with its
new content and the removed one is findable for neither of the two users. What it
proves: after one cycle the index is correct even though not a single event
arrived. What it does not prove: the cadence. When a cycle starts is decided
against the clock of the container and is measured in `test_reconcile.py`; the
cycle in the job is triggered by hand, and the reconcile task of the container is
switched off for that whole job so that "exactly one" is a fact.

**D-09, the DACH promise** (`reconcile-and-dach`). The Swiss document is searched
for with both spellings, with ss and with the sharp s, and the Austrian one with
its own word form. What it proves: a scanned document from Switzerland or Austria
is findable through the ordinary search route after OCR. What it does not prove:
that tesseract read the page correctly. That is deliberate and is the whole
reason the assertion is a search and not a comparison of the recognised text: a
text comparison would be a test against the version of the engine and would go
red on the next Debian point release. The limit that a search for `Januar` does
not find `Jänner` is documented in `docs/german-analyzer.md` and asserted
nowhere, because it is not a defect.

## The gap

These behaviours of the PHP half have no test at all today. They are pure logic,
they are the parts a unit test covers well, and they are exactly the parts that
were added or changed by the security audit follow up, which is why they are
listed by name rather than summarised:

1. `ExAppService::filterCandidates` drops a candidate whose `fileId` is absent or
   is not an integer.
2. It drops a candidate with a non positive `fileId` whose title is not the
   canary.
3. It strips `title` and `snippet` off every candidate with a positive `fileId`,
   so nothing the container volunteers before the recheck can be displayed.
4. `Provider::search` drops a candidate whose node cannot be resolved through the
   user's own folder, and takes title and link from the resolved node.
5. It returns an empty result, not unchecked hits, when the user has no home
   folder.
6. `PlainText::bounded` replaces control characters with a single space, keeps
   the tab, caps at the given length, cuts on character boundaries and refuses
   invalid UTF-8. The replacement is one character for one character, and that
   the length is preserved is the property number 12 relies on.
7. `ExAppService::searchCandidates` refuses an empty term without a round trip
   and clamps the limit into 1..100.
8. The answer body is refused above one megabyte, before it reaches
   `json_decode`.
9. `GatewayController::getFileContents` answers 403 when `EX-APP-ID` is not
   `findling_backend`.
10. `Provider::search` asks at most three times, resolves at most
    `min(64, limit * 2)` nodes per search, and stops asking when the wall clock
    of two and a half seconds is used up.
11. It requests excerpts only after the recheck, only for the surviving file
    ids, and not at all when the budget is gone, in which case the subline is
    the path.
12. `ExAppService::filterSnippets` drops an excerpt for a file id that was not
    asked for, and drops the highlight ranges of a text the cleaning made
    shorter, because every offset behind the cut would point elsewhere. A text
    that only changed characters without changing its length keeps them.

Number 9 is reachable over HTTP but not from the integration job as it stands: it
would need a second registered ExApp to call the gateway under a foreign app id.
The other eleven are unit test material.

## What closes it

A PHPUnit job in `php.yml`, CI only, following the pattern every Nextcloud app
uses: check out `nextcloud/server` at the same branch the integration jobs use,
place the app in `apps/findling`, add PHPUnit as a dev dependency to
`php/composer.json`, and run the suite with the server's `tests/bootstrap.php` so
that `OCP` is available and `IRootFolder`, `IUserManager`, `IAppManager`,
`IUserMountCache`, `IFileAccess` and `LoggerInterface` can be mocked with
`createMock`.

It is deliberately not part of the audit follow up. Writing a PHPUnit suite and a
new CI job without being able to run either of them once is how a workflow ends
up red for reasons that have nothing to do with the code under test, and the
twelve items above are the specification for whoever writes it with a PHP runtime
at hand. Until then the gap is here, in writing, and not in somebody's memory.
