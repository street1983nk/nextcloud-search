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
