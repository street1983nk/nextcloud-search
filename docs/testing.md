# What is tested, and what each gate does not prove

This document exists because of a single honest answer to the question "is the
PHP half tested?". For three phases that answer was no, not by a unit test, and
`php -l` is a syntax check and not a test. Since plans 05-15 and 05-16 there is
a PHPUnit suite and the answer is yes, which is why this file no longer carries
a gap section. The twelve behaviours that gap was made of are still listed
further down, now each with the test that holds it.

What follows is what covers which half, and, for every gate, the sentence that
is worth more than the green tick: what it deliberately does not prove. A gate
read as proving more than it does is worse than no gate, and the failure this
file exists to prevent is a later reader quoting a green run for a claim nobody
ever measured.

## The two halves are not tested the same way

| Half | Gates | Runs where |
|---|---|---|
| Python backend | ruff, ruff format, pyright basic, vulture, pytest | locally before every commit, and in `python.yml` |
| Dev and CI scripts under `scripts/` | ruff and ruff format only, with `--config backend/pyproject.toml` | `python.yml`, same job as the backend gates |
| PHP companion | `php -l`, the textual gates in `backend/tests/`, plus both integration jobs end to end | `php.yml` and `integration.yml`, CI only |

The middle row is a **named limit**, added by the audit of phase 8. Until then
`scripts/` fell through all four Python gates, because they run with
`working-directory: backend` and because `[tool.pyright] include` and the
`vulture` arguments name `src` and `tests`. That mattered: `scripts/dev` carries
`build_corpus.py`, which the suite loads at run time, and `compound_probe.py`,
whose output is the measurement ground of the German analysis chain.

pyright and vulture are deliberately **not** part of that row. A dev script
reaches its dependencies over `sys.path` instead of over an installed package,
so pyright reports unresolved imports that say nothing about the code, and
vulture would flag every entry point a human calls by hand. Whoever turns
`scripts/` into a package should revisit both; until then the limit is written
down here rather than discovered again.

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
end to end job can see. The PHPUnit suite that used to be missing arrived with
plans 05-15 and 05-16 and grew again in plan 06.1-08; the twelve behaviours it
was written against, and the test that holds each of them, are the table further
down.

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
download path nor the renderer nor the engine writes to a user file, over every
file of the reference corpus, which is broken PDFs, pictures, a nine gigapixel
page and, since the launch hardening, a decompression bomb and five well formed
PDFs that want something. How many files that is, and what each of them is for,
is the business of `testdata/CORPUS.md` and is deliberately not counted a second
time here: the corpus grows, and a number kept in seven places is a number that
is wrong in six of them. What it does not prove: that nothing is written
anywhere else on the instance. It watches the corpus directory, not the data
directory.

Its second half is the verdict counter, and it exists because the first half can
be green for the wrong reason. A comparison only measures the files the run
touched, so a pass that never reached the pictures would hold the same untouched
files against themselves and say nothing at all. The
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

## The gates of the launch hardening, and the boundary of each one

Phase 06.1 was the phase that tested everything except the happy path, and it
left behind a row of gates that are easy to over read. Each of them is listed
with what it prevents and with what it does not prove, and the second column is
the one that will be quoted wrongly if it is missing. Where a plan summary named
a reservation, the reservation is copied here rather than smoothed over.

| Gate | What it prevents | What it does not prove |
|---|---|---|
| The arming mark and its two steps in `resilience.yml` (06.1-01) | A container that was switched on stops indexing after a restart, because the arming lived only in the process. The negative control beside it shows the gate can go red: the same restart without the mark indexes nothing. | That the mark survives a lost volume. It is state next to `state.db`, so an installation that loses the volume loses the mark with it, which is the same case as a lost index. |
| One engine and one constituent list per process (`resilience.yml`, 06.1-02 and 06.1-04) | A second embedding engine or a second copy of the constituent list inside one process, which is the shape that costs the memory budget on a small box. The ratchet counts loads and reads, not bytes. | A ceiling on resident memory. The difference around the first search is printed and left unjudged on purpose: plan 06.1-04 measured that the guarded step does not load a model at all, so a cap there could not go red for the reason it would name (DI-06.1-04). |
| `test_extract_edge_paths.py` (06.1-05) | A lying file extension, a byte order mark that becomes a character, a byte sequence without text indexed as if it were text, and a second place in the code that writes on the file path. | That a half readable file is repaired. The file with the encoding change is pinned as it is, because repairing it would mean guessing at a text that could not be read once already. |
| The corpus files 34 to 39 with their verdict table (06.1-06) | A decompression bomb or a PDF that wants an action travelling the road of a user document unnoticed. They lie in the directory `readonly-gate` freezes, so every one of them is measured by the read only invariant as well. | That a PDF viewer elsewhere refuses the action. The gate knows the verdict of the container and that not one byte moved. What another program would do with an open action is not a question this repository can answer. |
| Scenarios 7, 8 and 9 of `search-parity`, and the file that changes while it is read (`index-search-e2e`, 06.1-07) | A deleted file that stays findable, a version rollback that loses the file, a link share that quietly widens the access list, and a verdict written for content that no longer exists. | Ranking or hit counts. Parity is a statement about sets of fileids and about nothing else, and scenario 8 compares only over the name marker, because the native term filter never looks at a text layer. |
| `php/tests/Unit/GroupEventListenerTest.php` and scenario 10 (06.1-08) | A user who joins a group waiting for the nightly reconcile before the team folder becomes findable. The scenario also reads the prefilter rows, so a build on which only the PHP recheck works cannot carry it green. | The same for an ordinary share that goes to a group. That one reaches its members over the mount provider of `files_sharing` and still falls to the crawl; DI-06.1-02 names that rest. |
| `test_lockstep_versions.py` with the version window, and the drift step in `deploy-harp.yml` (06.1-09) | A version window that says one thing in the two `info.xml` and another in the CI matrix, in either direction: an entry outside the window and a promised version without an entry are both findings. | That a server outside the window works. The drift step proves the opposite politely, in both directions: the answer is empty and carries a success status, checked with the status code rather than with `curl -sf`, which would throw the two cases together. |
| `disk-full` in `resilience.yml` (06.1-11) | A full volume met with a crash or with a work stock written off, instead of with a pause the second track returns from. The counter probe forces a real ENOSPC and shows the volume really ends where the loop image ends. | The behaviour of the index write itself at ENOSPC. The free space floor exists so that case never arrives, which is why the pause in front of it is the subject and not the fault behind it. |
| Both sides of the budget edge in `walking-skeleton`, and `scripts/ops/search_load.py` (06.1-11) | A slow backend costing the search rather than one result group, and a load tool that can only measure the machine it was born on. | A concurrency promise. The tool deliberately makes none, and says so in its own module header; the number is a measurement and belongs to plan 06.1-18. |
| The install path out of the release archives in `deploy-harp.yml` (06.1-12) | An installation that only works from a checkout. Both halves arrive as the signed archives, the image comes out of the registry the archive names, and an anonymous pull is attempted before anything is installed. | That the app management web interface installs it. That is a click path, it is measured on no route, and it is written down as an uncovered area rather than left to be assumed (DI-06.1-16). |
| `scripts/dev/validate_info_xml.sh` and the store assertions in `test_store_metadata.py` (06.1-13) | A submission that fails on the store schema, an image of the wrong size, a category that does not exist, and a word the owner's vocabulary rule forbids. The pin of the schema stands in exactly two places and an assertion holds them equal. | That the store accepts the app. Only the store can say that, and it says it in phase 6. |
| `findling.extract.ocr_quality` with `testdata/corpus-truth.json` (06.1-14) | An OCR regression noticed only as a search hit that happens to still work. The measurement is a character error rate against a truth the generator wrote, and three counter probes show the rate moves. | Quality on foreign material, and it currently proves nothing on every run: the tool is driven by hand and by no job, so the total failure it was built to catch would surface at the next manual measurement and not before (DI-06.1-11). |
| `scripts/dev/aio_install_check.sh` and `docs/install-check.md` (06.1-16) | An install path measured only by CI. The script takes an address, a login and two archives, reaches into no working tree, and drives the same schedule on a machine set up the way a selfhoster sets one up. | The arm64 and all-in-one half in the same run. That is a second run on the box, in plan 06.1-18, with the image tag and the platform as the only two knobs that change. |

| `test_an_office_document_survives_the_many_core_trap_no_runner_could_reach` and the step of its own name in `python.yml` (06.1-24) | The many core trap of the Office path becoming invisible again: OpenBLAS starts one thread per CPU inside the capped address space of the extraction child, and no job in this repository could reach that, because a runner has two to four CPUs. The case lowers the cap and widens the thread stack so that two CPUs are enough, and it carries its own counterfactual: a child in the state before commit debb395 has to fail. | That the production cap of 512 MB is enough on a machine with many cores. The case runs at 192 MB with a 64 MB thread stack, which is a scaled model of the trap and not the production configuration. At how many cores the real cap breaks without the pin was measured once, at twelve, and is not a gate. |
| `QueueServiceTest.php` and the revocation in `QueueService::acknowledge` (06.1-24) | A `failed` verdict of the Nextcloud side outliving the later success of the same file, which is the contradiction of the sight check: the tiles count four files as failed and the error group advises "upload the file again" while the same files are findable. The test holds the set arithmetic including the exception that would silently delete a true failure, namely a permission change on the same file. | That the revocation works against a running instance. It is a unit test over a pure function; the wiring into the transaction and the database cannot be tested without a Nextcloud and belongs to the integration jobs. |

## The guest user probe, which is deliberately not a gate

`scripts/dev/guest_parity.sh` is the second half of scenario 6. Decision D-22
gives that scenario two bodies: the groupless minimal user, in the CI job since
plan 05-09, and a real guest user over the `guests` app. The same decision keeps
that app out of the CI matrix, and the reason is worth repeating because it
looks like laziness and is not one: the app is a foreign dependency with a
release window of its own, and a matrix that goes red because somebody else's
app has no release yet says nothing at all about Findling.

A promise like that is worth what holds it, so it is held by a test rather than
by good intentions. `backend/tests/test_guest_parity.py` counts the mentions of
that app over every workflow and every composite action, comments filtered out
first, and a single one turns the suite red.

The probe itself is a script and not a memory. It raises
`unified_search_max_results_per_request` and puts it back, asks with an explicit
`limit`, and hands both answers to `scripts/ci/parity_diff.py`, which is the
same judge the CI job uses. It asks three questions, because none of them is a
statement on its own: the guest finds his one shared file, he finds the other
marker in neither provider, and the owner still finds that other marker. A fourth
comparison stands in front of the three and is not one of them, see the
precondition below. It
removes the guest, the share and the two files on every way out.

```
FINDLING_CREATOR_PASS=the-password \
  scripts/dev/guest_parity.sh \
  --url http://localhost:8080 \
  --exec "docker exec -i -u www-data -w /var/www/html findling-nc" \
  --creator alice \
  --log guest-parity.log
```

The password is an environment variable and not an argument, and the probe
refuses a `--creator` value that still carries a colon. An argument stands in
the process list of the machine for as long as the run lasts, which is where
the security audit of plan 06.1-17 found it (DI-06.1-18).

The app is not installed by the probe. A test tool does not bring a foreign app
onto an instance, so the script names the two `occ` commands and stops.

### The precondition, which used to be missing

Before the first guest question the probe asks the OWNER for his own shared
marker, and it stops with exit code 2 if he does not find it. That step was added
by plan 06.1-19 and it closes DI-06.1-17. Without it the probe cannot tell its
two failure modes apart: an instance whose container is stopped has an empty work
stock as well, so the wait for the queue returns satisfied, and the first guest
comparison then reports a missing hit. Read literally that says "the guest does
not find a document he is allowed to see", which is a functional defect. What
really happened is that the probe could not take place. One of the two readings
says fix the permission chain, the other says start the container, and a probe
that cannot separate them sends its reader to the wrong place.

The shared marker and not the private one, because it is the file the guest is
asked about next, so its absence for its own owner is the narrowest statement
that the index does not carry the material of this probe. The exit code is 2 and
not 1 so that a caller can tell not performed from failed.

### State: passed, 07.09.2026

The run belongs to plan 06.1-19 and it happened, on the fresh instance of the
owner sight check.

| What | Value |
|---|---|
| Instance | Nextcloud 34.0.3, SQLite, docker compose behind a front proxy, port 8097 |
| Both halves | out of the archives of the release rehearsal, run 34116531030 |
| `guests` app | 4.9.0 |
| Guest account | `findling-guest-probe`, created by `testuser`, removed again |
| Protocol | `.dev/sichtprobe/guest-parity-sichtprobe.log` of that run |

Four comparisons, all passed, each one over the same judge the CI job uses:

| Scenario | Question | Native | Findling | Verdict |
|---|---|---|---|---|
| `owner-precondition` | does the owner find his own shared marker | 177 | 177 | passed |
| `guest-received-share` | does the guest find the one file he was given | 177 | 177 | passed |
| `guest-denied` | does he find the other marker in either provider | none | none | passed |
| `owner-still-finds` | does the owner still find that other marker | 178 | 178 | passed |

The two limits of this result, stated because they are the whole point of D-22:
it is a snapshot and not a standing gate, and it holds for version 4.9.0 of the
`guests` app and for no other. A second run against a later version of that app
is a second snapshot, not a confirmation of this one.

One property of the host rather than of the probe, written down because it cost a
run: the Git shell of Windows rewrites any argument that looks like a unix path,
and that includes the value of an option written as one word. `-d
path=/parityguest-1.txt` reached curl as a windows directory, so the share API
answered "Wrong path, file/folder does not exist" about a file that had just been
uploaded successfully. On such a host `MSYS2_ARG_CONV_EXCL` has to name the
container path and that OCS argument, and a blanket `*` is not the way out
because the probe hands curl its configuration through a path under `/tmp` of the
shell. Finding 7 of `docs/install-check.md` now covers this probe too.

## The twelve behaviours of the PHP half, and the test that holds each one

This section used to be called "The gap", and it was one: these twelve
behaviours are pure logic, they are the parts a unit test covers well, and they
are exactly the parts the security audit follow up added or changed. They had no
test at all until plan 05-15, and all twelve have one since plan 05-16.

The list is deliberately kept whole rather than trimmed. It is the specification
these tests are read against, and a specification that shrinks as it is
implemented cannot be used to check the implementation afterwards. What changed
is the last column: every line now names the file that holds it.

Every file below lives in `php/tests/Unit/` and runs in the `phpunit` job of
`php.yml`. Which test name asserts which half of a line is a table in
`05-16-SUMMARY.md`; this one stays at the level of the property, because the
property is what a reader is looking for.

| No | The behaviour | Held by | Since |
|---|---|---|---|
| 1 | `ExAppService::filterCandidates` drops a candidate whose `fileId` is absent or is not an integer. | `ExAppServiceTest.php` | 05-15 |
| 2 | It drops a candidate with a non positive `fileId` whose title is not the canary. | `ExAppServiceTest.php` | 05-15 |
| 3 | It strips `title` and `snippet` off every candidate with a positive `fileId`, so nothing the container volunteers before the recheck can be displayed. | `ExAppServiceTest.php` | 05-15 |
| 4 | `Provider::search` drops a candidate whose node cannot be resolved through the user's own folder, and takes title and link from the resolved node. | `ProviderTest.php` | 05-15 |
| 5 | It returns an empty result, not unchecked hits, when the user has no home folder. | `ProviderTest.php` | 05-15 |
| 6 | `PlainText::bounded` replaces control characters with a single space, keeps the tab, caps at the given length, cuts on character boundaries and refuses invalid UTF-8. The replacement is one character for one character, and the preserved length is what number 12 relies on. | `PlainTextTest.php` | 05-15 |
| 7 | `ExAppService::searchCandidates` refuses an empty term without a round trip and clamps the limit into 1..100. | `ExAppServiceTest.php` | 05-16 |
| 8 | The answer body is refused above one megabyte, before it reaches `json_decode`. | `ExAppServiceTest.php` | 05-16 |
| 9 | `GatewayController::getFileContents` answers 403 when `EX-APP-ID` is not `findling_backend`. | `GatewayControllerTest.php` | 05-16 |
| 10 | `Provider::search` asks at most three times, resolves at most `min(64, limit * 2)` nodes per search, and stops asking when the wall clock of two and a half seconds is used up. | `ProviderTest.php` | 05-16 |
| 11 | It requests excerpts only after the recheck, only for the surviving file ids, and not at all when the budget is gone, in which case the subline is the path. | `ProviderTest.php` and `ExAppServiceTest.php` | 05-16 |
| 12 | `ExAppService::filterSnippets` drops an excerpt for a file id that was not asked for, and drops the highlight ranges of a text the cleaning made shorter, because every offset behind the cut would point elsewhere. A text that only changed characters without changing its length keeps them. | `ExAppServiceTest.php` | 05-16 |

Number 9 is the one that took a detour worth recording. It is reachable over
HTTP but not from the integration job as it stands, which would need a second
registered ExApp calling the gateway under a foreign app id. Doubled, it turned
out to be unit test material after all: a header on a request object and four
cases.

What these twelve do not prove is the same thing for all of them: they are mocks
and they say nothing about the behaviour against a real instance. That is what
the two integration jobs are for, and the division of labour is the point rather
than a shortcoming.

Four more PHP test files stand beside them and are not part of this list,
because the list is a specification of one audit follow up and not an index of
the suite: `BootstrapTest.php` and `AdminViewServiceTest.php`, which arrived with
the scaffold in plan 05-15 and grew in plan 05-20,
`GroupEventListenerTest.php` from plan 06.1-08, and `QueueServiceTest.php` from
plan 06.1-24, which holds the arithmetic of the verdict revocation.

## What closed it

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
