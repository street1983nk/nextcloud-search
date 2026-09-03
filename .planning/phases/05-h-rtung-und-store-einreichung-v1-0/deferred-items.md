# Deferred items of phase 05

Out of scope discoveries. Each one was found while executing a plan of this
phase, none of them was caused by the task at hand, and none of them was fixed
there. They are written down here so that they are not rediscovered from scratch.

## DI-05-01: `deploy-harp.yml` has not run on a GitHub runner yet

**Found during:** 05-01, at the last acceptance criterion of task 2.

The acceptance criterion asks for a green run of the new workflow on the working
branch, triggered with `gh workflow run deploy-harp.yml`. That was not possible
from the execution worktree, for two reasons that have nothing to do with the
workflow itself: the branch `worktree-agent-05-01` exists only locally and is
never pushed by a parallel executor, and `workflow_dispatch` only offers a
workflow that is present on the default branch.

**What was done instead.** The whole path was executed locally against
`scripts/dev/compose-harp.yaml`, which is the same sequence of commands with two
addresses changed, and both defects it uncovered are fixed (see the plan summary).
`actionlint` passes on the file, the YAML loads, and the HaRP digest was resolved
against the registry.

**What is left.** The workflow has push triggers on `backend/**`,
`php/appinfo/**` and its own path, so the first run happens on its own once this
branch is merged. Someone has to look at that run. Two things can only fail
there, because they have no local counterpart: the local registry on port 5000
of the runner and the `--net host` variant of the daemon registration, which
replaces the compose network of the local run.

## DI-05-02: HaRP fails to update the OS trust store inside the ExApp container

**Found during:** 05-01, while measuring the HaRP install.

HaRP runs two commands in the freshly created ExApp container through
`docker exec`: it copies the tunnel certificates into `/certs/frp`, and it runs
`update-ca-certificates`. The exec runs as the image user, which is the
unprivileged `findling` (uid 1000), so the second command fails:

```
Certificate update command failed in container 'nc_app_findling_backend'.
Exit: 2, /usr/sbin/update-ca-certificates: 109: cannot create
/etc/ssl/certs/ca-certificates.crt.new: Permission denied
```

**Why it was not fixed.** The first command is the load bearing one and is fixed
in 05-01 (the image now carries `/certs/frp` owned by that user). The second one
writes the HaRP CA into the operating system trust store of the container, and
`docker/harp_connect.sh` never reads it: it points frpc at
`trustedCaFile = /certs/frp/ca.crt` explicitly. A trust store that the
application can rewrite is a worse problem than a log line, so making
`/etc/ssl/certs` writable for uid 1000 is deliberately not the answer.

**What is left.** Two questions for the plan that owns the ARM and AIO run: does
anything in the container ever need to trust the HaRP CA through the OS bundle
(today nothing does, because the only TLS client is frpc), and does the error
line have to be silenced so that an admin does not read it as a broken install.
The honest cheap answer is a sentence in `docs/uninstall.md` or
`docs/dev-setup.md` naming the line as expected.

## DI-05-03: 05-RESEARCH.md Pattern 1 registers the daemon with the wrong nextcloud url

**Found during:** 05-01, when the first install ended in `heartbeat check failed`.

Pattern 1 of `05-RESEARCH.md` (and the `<interfaces>` block of 05-01-PLAN.md that
quotes it) registers the HaRP daemon with `http://localhost:8080` as the
Nextcloud url, that is with the address of Nextcloud. In HaRP mode AppAPI
resolves the address of an ExApp as `{nextcloud_url}/exapps/{appId}`
[VERIFIED: `DockerActions::resolveExAppUrl`, read in the running instance of
app_api on 2026-09-03], because HaRP is the entry point: it forwards `/exapps`
into the frp tunnel and everything else to `NC_INSTANCE_URL`. With the address of
Nextcloud in that position every heartbeat goes to the web server, which answers
404, and the install ends with `heartbeat check failed` next to a healthy
container.

**What was done.** `deploy-harp.yml` and `docs/dev-setup.md` carry the corrected
form (`http://localhost:8780` and `http://harp:8780`) with the reason next to it.

**What is left.** Everything else in this phase that quotes Pattern 1 has to use
the corrected form: plan 05-08 (version matrix and uninstall proof), and above
all the AIO run on the rented ARM box, where the same mistake would cost hours in
a run that takes a day. `05-RESEARCH.md` itself is deliberately not rewritten,
because a research document records what was known when it was written; this
entry is the correction.
