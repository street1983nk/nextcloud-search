# Deferred items of phase 04

Out of scope discoveries. Each one was found while executing a plan of this
phase, none of them was caused by the task at hand, and none of them was fixed
there. They are written down here so that they are not rediscovered from scratch.

## DI-04-01: `scripts/dev/register-exapp.sh` declares one route out of five

**Found during:** 04-10, while preparing the sight check.

The script registers the ExApp with a route list of exactly one entry,
`search` (POST, access level 1 = USER), and the comment above that line claims
the list "mirrors `backend/appinfo/info.xml` exactly: one route". Since phase 2
and phase 4 that file declares five routes: `search` and `snippets` at USER
level, and `status`, `rates` and `diagnose` at ADMIN level.

**Why it is not blocking.** The admin page and `occ findling:diagnose` reach the
container through `PublicFunctions::exAppRequest`, and that call goes straight to
`AppAPIService::requestToExApp` without consulting the registered route list.
The route list is checked in `ExAppProxyController` on the browser to proxy to
ExApp path, and this app uses that path nowhere. So the four admin routes work in
the local instance despite the missing declarations, which was verified with
`occ findling:diagnose 190` answering `indexed` out of the container.

**Why it should still be fixed.** The comment states a parity that no longer
holds, and a local registration that differs from a released installation is
exactly the shape of a defect that works here and breaks in CI. The cheap fix is
to build the JSON route list in the script out of `backend/appinfo/info.xml`
instead of writing it by hand, with the access level mapping PUBLIC 0, USER 1,
ADMIN 2 that `OCA\AppAPI\Db\ExAppRouteAccessLevel` defines.

## DI-04-02: the dev backend has to be restarted after a plan that adds a route

**Found during:** 04-10, while preparing the sight check.

The development backend runs as a plain host process started by
`scripts/dev/register-exapp.sh`, and the script leaves a process that answers its
heartbeat running, on purpose and idempotently. Python has already imported its
modules at that point, so a route added by a later plan does not exist in that
process. On this machine the consequence was a container answering 404 on
`GET /diagnose` while the route had been in the sources since plan 04-07, which
looks exactly like a defect of the PHP half: the page and the command both say
"the backend does not answer".

The workaround is to stop the process before running the script:

```bash
kill "$(cat .dev/exapp.pid)" && rm -f .dev/exapp.pid
sh scripts/dev/register-exapp.sh
```

What would remove the trap: the script comparing the version or the route list of
the answering process against the sources and restarting it when they differ, or
a sentence in `docs/dev-setup.md` next to the idempotency promise. Both are
outside the file list of plan 04-10.

## DI-04-03: skip verdicts of the container never reach the error list per file

**Found during:** 04-10, sight check 4 of the owner walkthrough.

**Gap closure material.** The error list of block 3 holds the groups the
Nextcloud half knows, and it knows only what it decided itself: `too_large` and
`empty_file` were both present with the correct label, the correct remedy and
resolvable example paths. The verdicts the container decides per file, that is
`encrypted`, `no_text_layer`, `empty_text` and `image_not_ocrable`, do not appear
as groups, because the acknowledgement channel of `QueueController` carries a
`failureList` and no equivalent list of skip verdicts. Only failures flow back
per fileid; a skipped file is acknowledged as done and its reason stays in the
container.

**Why it is not a defect of the page.** The per file answer exists and was seen:
the live diagnosis names exactly those verdicts, with label and remedy, for a
path as well as for a fileid, and `occ findling:diagnose` gives the same answer
without a browser. What is missing is the aggregation, not the knowledge.

**What closes it.** Extend the acknowledgement channel so a skip verdict travels
per fileid the way a failure already does, privacy clean, that is fileids and
reason codes and no paths and no text. The reason vocabulary is already
identical on both sides and gated by `test_extract_errors.py`, so the receiving
half needs no new codes. Once the rows exist in `findling_file_state`, block 3
gains those groups with example paths for free, because the grouping reads that
table and nothing else.

**Owner decision of the walkthrough:** accepted as a gap closure plan, not as a
blocker of phase 4.

## DI-04-04: nothing re-stamps the version marks after a completed rebuild

**Found during:** 04-10, owner walkthrough, while clearing the reindex banner.

The reindex banner appears when the version marks stored in the index differ
from the versions the current code expects (`expected_versions` in
`index/open.py`). Its own remedy sentence names `occ findling:index --restart`.
That command can never clear the flag: `_seed_meta` in `store/repo.py` writes a
meta key only when it is missing, and no code path re-stamps the marks after a
rebuild has finished. So a rebuild does the work the banner asks for and the
banner stays.

On the dev instance the marks were stamped by hand after the full rebuild. That
is factually correct there, because all 139 documents were re-ingested with the
current code, but it is a manual step no admin can be expected to know.

**What closes it.** A completed rebuild has to write the expected versions, so
the mark follows the work instead of the installation. The place is the end of
the rebuild path, not `_seed_meta`, because seeding must stay a first start
operation. Whatever the shape, the banner and the command it names have to agree
afterwards: the remedy sentence is a promise the code has to keep.

**Owner decision of the walkthrough:** accepted as a gap closure plan, not as a
blocker of phase 4.
