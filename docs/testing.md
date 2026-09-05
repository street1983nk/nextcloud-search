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
| `test_uninstall_contract.py` | A disable of the app that removes data. Nextcloud runs the uninstall repair steps on every disable, so the gate pins that the intent mark is asked before anything is delegated, that the step holds no removal of its own and never breaks off, that every table removal has an existence check in front of it, that the app config goes last and that the table names come out of their constants. It says nothing about whether the removal works; that is the measurement in `docs/uninstall.md`. |
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
- a query whose content words stand in no document brings back the document it
  paraphrases, through the ordinary search route (`index-search-e2e`, since
  phase 6). The step before it runs the same query with the second track
  switched off and requires an empty answer, so a hit can only have come out of
  the vector half. What this pair does not prove is ranking quality: it says the
  vector half travels the whole stack and reaches the right user, not that the
  document stands first.

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

## The gates of phase 6, and the boundary of each one

The semantic half brought eleven test files and two steps that only the built
image can run. They are listed together because they are easy to mistake for one
another: several of them look like "the semantic search works" and none of them
says that on its own.

| Gate | What it proves | What it does not prove |
|---|---|---|
| `test_vec_extension_probe.py` (06-01) | The CPython of this image allows loadable SQLite extensions and vec0 really loads, on both architectures; a KNN query runs under `PRAGMA query_only = 1`. | That the extension is fast enough. The scan latency is a measurement and lives in `docs/measurements/2026-09-05-welle0-arm64/`. |
| `test_embed_bench.py` (06-02) | The measuring tools compute what they claim: characters per token, tokens per second and scan latency, over staged inputs with known answers, and they print numbers and never text. | Nothing about the model. It checks the ruler, not what was measured with it. |
| `test_model_quality.py` (06-03) | The three language test sets are well formed, unique and free of lexical bridges: no content word of a query stands in its own passage, machine enforced over every case. The rank arithmetic, the tie handling and the three refusal paths of the tool are checked as well. | The quality of the model. The numbers are in `docs/measurements/2026-09-05-modellqualitaet/`, they are a lower bound by construction, and they are not comparable with a public benchmark figure. |
| `test_vector_store.py` (06-04) | The four operations of the vector stock, the delete order of `replace_chunks`, the banding of long id lists, and that a `Neighbour` carries six numbers and nothing that could hold content. | That the stock is ever filled. That is the second track. |
| `test_chunker.py` (06-05) | Chunk boundaries are character offsets and never byte offsets, and the token cap is respected against the tokenizer that ships. | That a chunk is a sensible passage. Where a sentence is cut is the splitter's judgement and is not asserted. |
| `test_embed_model.py` (06-05) | The E5 prefixes are set and change the ranking, and a missing model gives the honest `embedding_unavailable` verdict instead of an exception. | Absolute quality. The prefix case proves a difference in rank, not that the ranking is good; that number is the measurement report of plan 06-03. |
| `test_rrf_fusion.py` (06-06) | The merge is a pure function over two lists of numbers: rank starts at 1, an empty list is the identity, equal scores keep a fixed order, and a weight of zero removes its list instead of scoring it zero. | Nothing about permissions. `fusion.py` never learns who is asking, which the boundary gate below asserts. |
| `test_semantic_search.py` (06-06) | The three success criteria of the phase as behaviour: a paraphrase finds the document with a control run beside it that finds nothing, a user without a permission row gets nothing, and a broken vector half costs the semantics and not the search. | That the built image behaves the same way. The model here is a stand-in; the image level answer is the two steps below. |
| `test_embedding_track.py` (06-07) | The second track: which files enter it, that a verdict of that track never reaches `Store.record`, and that a delete on the first track takes the vectors with it. | The throughput of the track. The rate is a measurement, and the wait in `integration.yml` is derived from it. |
| `test_semantic_snippet.py` (06-08) | The excerpt of a purely semantic hit is cut behind the one permission prefilter and behind the PHP recheck, in characters and not in bytes, and the rank chunk is asked for in the direction the prefilter asks in. | That the excerpt is the most useful passage. It is the passage of the nearest chunk, which is a different claim. |
| `test_semantic_boundary.py` (06-10) | There is no second exit: no route of `api/` carries `semantic` or `vector` in its path, the permission prefilter is called at exactly two places and in which two, the merge and the embedder do not know the question at all, the answer of the search path carries three fields, and the origin mark is not reachable from a user answer. | That the one route filters correctly. That is `test_acl_prefilter.py`, the PHP recheck and the `search-parity` job. This gate is about absence, and absence is the one thing a functional test cannot show. |
| Offline step (`docker.yml`, 06-10) | That no network is needed. The published image starts with `--network none`, embeds a small stock of its own making and answers a paraphrase out of it, on amd64 and on arm64, with a control run that finds nothing without the stock. | That no network is attempted. `HF_HUB_OFFLINE=1` is a net and not a proof, and `onnxruntime` writes "Failed to persist telemetry device ID" to stderr in every run with the network cut as well: a failed local file system write, not traffic, measured in plan 06-03 and named here because it is the line that gets read the wrong way round. |
| Model-gone step (`docker.yml`, 06-10) | Criterion 3 on the level of the image: with an empty directory mounted over the model directory the ordinary query answers the same hits as a run without any semantics, carries the degraded mark, and is neither empty nor an error. The step ends by running its own verdict against a deliberately empty index and requiring it to come back red. | That every way a model can fail behaves like this. It covers the model that is not there; the model that loads and then raises is `test_semantic_search.py`. |

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
The other eleven are unit test material, and number 9 turned out to be unit test
material too: doubled, it is a header on a request object and four cases, which
is what `php/tests/Unit/GatewayControllerTest.php` does since plan 05-16.

**State of this list.** All twelve have a test. Numbers 1 to 6 arrived with plan
05-15 and numbers 7 to 12 with plan 05-16, in
`php/tests/Unit/ExAppServiceTest.php`, `php/tests/Unit/ProviderTest.php`,
`php/tests/Unit/PlainTextTest.php` and
`php/tests/Unit/GatewayControllerTest.php`. Which number is asserted by which
test name is a table in `05-16-SUMMARY.md`, and plan 05-19 is the one that
rewrites this section around it. The list itself is deliberately left whole
rather than trimmed: it is
the specification these tests are read against, and a specification that shrinks
as it is implemented cannot be used to check the implementation afterwards.

## What closes it

A PHPUnit job in `php.yml`, CI only, following the pattern every Nextcloud app
uses: check out `nextcloud/server` at the same branch the integration jobs use,
place the app in `apps/findling`, add PHPUnit as a dev dependency to
`php/composer.json`, and run the suite with the server's `tests/bootstrap.php` so
that `OCP` is available and `IRootFolder`, `IUserManager`, `IAppManager`,
`IUserMountCache`, `IFileAccess` and `LoggerInterface` can be mocked with
`createMock`.

This is what plan 05-15 built, and it is built exactly that way. The job is
called `phpunit`, it checks out `stable34`, it installs a throwaway SQLite
instance so the server bootstrap has a config to read, and it runs
`php/phpunit.xml` against `php/tests`. Two things were added to the sketch above
while it was being run for the first time. `php/tests/bootstrap.php` aborts with
its own message when there is no server checkout at the path it computed, because
the alternative is a class not found thirty lines into an unrelated test; the job
proves that guard on every run before it runs the suite. And the job asserts how
many tests actually executed, because a suite that reports success without
executing anything is the failure mode this repository calls vacuous.

The suite stays CI only, and that is a fact about the machine rather than a
preference: there is no PHP on the development machine of this project, so it is
not documented as a local command anywhere. That was also the reason the gap
existed for three phases. Writing a PHPUnit suite and a new CI job without being
able to run either of them once is how a workflow ends up red for reasons that
have nothing to do with the code under test; what changed is that this phase
builds the server checkout per version anyway.
