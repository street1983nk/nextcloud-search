# Local development setup

This is the shortest path from an empty machine to a search hit that was produced
inside the backend and shown in the normal Nextcloud search bar. It is also the
setup used for the visual proof of phase 1.

## Prerequisites

| Tool | Why | Note |
|------|-----|------|
| Docker Desktop | runs the test Nextcloud | must be started before anything else |
| uv | runs the Python backend | version 0.11.7, the one that produced `backend/uv.lock` |
| curl | health checks in the scripts | any recent version |
| gh | reading the state of the integration workflow | only needed for the CI check |

There is deliberately **no PHP and no composer** on this machine. Every PHP call
runs inside the container, which is why the commands below never invoke a local
binary. A bare `php` call would fail with "command not found" and send you
looking for a path problem that does not exist.

## How the pieces are wired

```
browser  ->  http://localhost:8080  ->  Nextcloud (container)
                                          |  PHP companion, app id findling
                                          |  AppAPI proxy
                                          v
                                        http://host.docker.internal:10035
                                          |
                                        findling_backend (plain process on the host)
```

Two addresses do the work, and mixing them up is the single most common failure:

- The **backend** reaches Nextcloud at `http://localhost:8080`, because it runs on
  the host where the port is published.
- **Nextcloud** reaches the backend at `http://host.docker.internal:10035`, because
  `localhost` inside the container is the container itself. The compose file adds
  `host.docker.internal:host-gateway` so this also holds on a plain Linux daemon.

For the same reason `scripts/dev/register-exapp.sh` binds the backend to `0.0.0.0`
while the integration workflow binds it to `127.0.0.1`. In CI both sides live on
the same host, here they do not. A loopback bind would look perfectly healthy in
the backend log and still be invisible to the container.

## Step by step

1. Start Docker Desktop and wait until it reports that the engine is running.

2. Point the compose client at the file once, from the repository root. Every
   command below relies on it, and it saves repeating the path:

   ```bash
   export COMPOSE_FILE=scripts/dev/compose.yaml
   ```

3. Start the test Nextcloud:

   ```bash
   docker compose up -d
   ```

   The first start installs Nextcloud into a named volume and takes a minute or
   two. It is finished when `curl -sf http://localhost:8080/status.php` answers.
   Admin credentials are `admin` / `findling-dev-admin`, set in the compose file.

4. Start the backend and register it:

   ```bash
   sh scripts/dev/register-exapp.sh
   ```

   The script waits for the instance, enables `app_api` and `findling`, starts the
   backend on port 10035, waits for its heartbeat, removes any earlier
   registration and finally performs the AppAPI handshake. It prints `registered`
   when the handshake is through. The backend log is written to `.dev/exapp.log`
   and its process id to `.dev/exapp.pid`.

5. Create a test user, so the identity in the result is not the installer:

   ```bash
   docker compose exec -T -u www-data -e OC_PASS=findling-dev-testuser app php occ user:add --password-from-env testuser
   ```

   `-e` is what carries the variable into the container; a plain shell assignment
   in front of the command would only reach the compose client. The password is a
   throwaway value of a throwaway instance and is not used anywhere else.

6. Open http://localhost:8080 in a browser and log in as `testuser`.

7. Type `findling-canary` into the search bar at the top.

   Expected: a result group **File contents** with the entry **findling-canary**.
   The second line reads `produced inside container <host> at <timestamp> for user
   testuser`. That line is the proof: the host name and the timestamp come from
   the running backend process, and the user id comes from the signed AppAPI
   header, so no hard coded string in PHP can produce it.

### `findling-canary` is a reserved search term

The backend answers with that entry for this one term and for no other. The
comparison is exact: leading and trailing spaces are ignored, everything else is
an ordinary search, so `findling-canary contract` finds documents and not the
canary. A file whose name or content contains the word is found the normal way
and is not affected by any of this.

The entry has file id 0, which is the only file id the PHP side accepts without
resolving it against the user's own folder, and it accepts it only under this
exact title. There is no document behind it, it appears in no other search, and
nothing about it depends on the index existing: it answers on a container that
was deployed a minute ago and has not indexed anything yet, which is exactly the
situation somebody asks it in.

Do not reuse the word for anything else, and do not use "contains" anywhere in
the comparison. A diagnostic that shows up uninvited stops being evidence of
anything.

## Phase 2: from a file on disk to a content hit

The proof of phase 1 was that an answer came out of the running container. The
proof of phase 2 is the product itself: a word out of a real German document,
typed into the ordinary search bar, brings the document back with an excerpt from
its text, and only to somebody who is allowed to see the file.

**Port 8090 and not 8080, everywhere in this section.** A second local Nextcloud
holds 8080 on this machine, and two instances on one port do not fail loudly,
they answer each other's requests. `FINDLING_PORT` is read by the compose file
and by `register-exapp.sh`, so exporting it once covers both.

```bash
export COMPOSE_FILE=scripts/dev/compose.yaml
export FINDLING_PORT=8090
```

The dialect stays SQLite here. The second dialect is not a local exercise: the
job `index-search-e2e` in `.github/workflows/integration.yml` runs the whole
proof below a second time against MariaDB, which is where a dialect dependent
query builder defect shows up.

### 1. Start the instance and the backend

```bash
docker compose up -d
curl -sf http://localhost:8090/status.php > /dev/null && echo up
```

The German constituent list comes next, and it needs one command that phase 1 did
not need. The runtime image installs the Debian package `wngerman`, but the
development backend runs as a plain host process, and there is no
`/usr/share/dict/ngerman` on a developer machine. The command below builds the
artifact once, directly into the volume the backend reads, in a throwaway
container:

```bash
docker run --rm \
  -v "$(pwd)/backend/src:/src:ro" -v "$(pwd)/.dev/storage:/storage" \
  -e PYTHONPATH=/src -e APP_PERSISTENT_STORAGE=/storage \
  -e DEBIAN_FRONTEND=noninteractive \
  python:3.13-slim-trixie sh -c 'apt-get update -qq \
    && apt-get install -y -qq --no-install-recommends wngerman > /dev/null \
    && python -c "from findling.index.wordlist import build_artifact; a = build_artifact(); print(len(a.entries), a.digest)"'
```

Expected output: `276496 b1f64012ca7f5b6e57de2cb1bafa2521cb6606f3ccef5d6fd17396edc808dde0`.
That is the same entry count and the same digest as in `docs/german-analyzer.md`.
A different digest means a different tokenisation, not a cosmetic difference.

```bash
sh scripts/dev/register-exapp.sh
```

### 2. Two accounts, and the corpus in the first one

```bash
docker compose exec -T -u www-data -e OC_PASS=findling-dev-testuser app php occ user:add --password-from-env testuser
docker compose exec -T -u www-data -e OC_PASS=findling-dev-kollegin app php occ user:add --password-from-env kollegin
docker compose exec -T -u www-data app php occ files:scan --all

docker compose cp testdata/corpus app:/var/www/html/data/testuser/files/corpus
docker compose exec -T -u root app chown -R www-data:www-data /var/www/html/data/testuser/files/corpus
docker compose exec -T -u www-data app php occ files:scan --all
```

`docker compose cp` copies as root, so the `chown` is not optional: a file the
web server cannot read is invisible to the crawl and to the file list alike.

### 3. Share exactly one file, before the crawl

```bash
curl -s -u testuser:findling-dev-testuser \
  -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
  -d 'path=/corpus/09-bescheid.pdf' -d 'shareType=0' \
  -d 'shareWith=kollegin' -d 'permissions=1' \
  http://localhost:8090/ocs/v2.php/apps/files_sharing/api/v1/shares
docker compose exec -T -u www-data app php occ files:scan --all
```

The order matters and it is not a detail of this script: the access list is
written while a file is indexed. A share granted after the crawl is not seen by
this phase at all, events and reconciliation are phase 3. Sharing through the
Files interface works just as well, as long as it happens before the next step.

### 4. Crawl

```bash
docker compose exec -T -u www-data app php occ findling:index --restart --no-interaction
docker compose exec -T -u www-data app php occ background-job:worker 'OCA\Findling\BackgroundJobs\SchedulerJob' --once
docker compose exec -T -u www-data app php occ background-job:worker 'OCA\Findling\BackgroundJobs\StorageCrawlJob' --stop_after 60
```

Two spellings that cost a run each when they were wrong. `--no-interaction`:
`occ` treats this shell as interactive, so the restart question would default to
No and the queue would stay empty. `--stop_after` with an underscore: the dashed
spelling does not exist on `background-job:worker`, Symfony rejects it and the
crawl never starts.

### 5. Watch it finish

```bash
docker compose exec -T -u www-data app php occ findling:index
(cd backend && uv run python -m findling.tools.index_status --db ../.dev/storage/state.db)
```

The first command is the Nextcloud side: `scheduled` and `handed to the worker`
both have to reach zero. The second is the container side and answers with JSON;
it is done when `indexed` is 8, `skipped` is 2 and `failed` is 1. Those three
numbers are the corpus doing its job: the scan without a text layer and the
encrypted PDF are skipped, the zero byte PDF fails, and the picture never enters
the queue because the crawl only takes document types.

If nothing is indexed at all, read `.dev/exapp.log` first. A `FileNotFoundError`
on `/usr/share/dict/ngerman` means the artifact step above was skipped.

### 6. The hit, in the browser

Open http://localhost:8090, log in as `testuser` and type `Genehmigung` into the
search bar.

Expected: the result group **File contents** shows `09-bescheid.pdf`, and the
second line is an excerpt out of the document in which
`Grundstücksverkehrsgenehmigung` appears. The word searched for is a constituent
of that compound and stands nowhere in the file name or the path, so the excerpt
can only have come from the text of the file. It is readable plain text without
any markup.

Second probe: `Vertrag` finds `11-uebersicht.odt`, which says `Verträge` and
never says `Vertrag`.

### 7. The counter probe, and the reason any of this may run on a server

Log out and log in as `kollegin`. Search for `Genehmigung`: exactly one hit, the
shared `09-bescheid.pdf`. Search for `Frist`, for `Vertrag` and for `Mueller`:
nothing at all, although all three find a file for `testuser`.

Which of the twelve documents a user sees is decided in PHP against that user's
own folder, and the excerpt is cut only afterwards. Both halves are asserted in
`index-search-e2e` on every push, on two database dialects.

## Counter check: the backend goes away

```bash
docker compose exec -T -u www-data app php occ app_api:app:unregister findling_backend
```

Search again. The search bar has to keep working exactly as before, only without
the Findling result group and without an error message. If the whole search dies
instead, the proxy treated an error array as a response object.

## Diagnosis, in this order

Always ask the provider list first. It splits the problem in half in one request:

```bash
curl -sf -u testuser:<password> -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
  'http://localhost:8080/ocs/v2.php/search/providers'
```

- **`findling` is missing:** the fault is in the PHP app. Either the search
  provider is registered in `boot()` instead of `register()`, or `getOrder()`
  returned null, or the app directory is not named exactly `findling`.
- **`findling` is listed but there is no result group:** the fault is behind the
  proxy, in the backend or in the registration. Continue with the next request.

```bash
curl -sf -u testuser:<password> -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
  'http://localhost:8080/ocs/v2.php/search/providers/findling/search?term=findling-canary'
```

Then, in this order:

1. `curl -sf http://127.0.0.1:10035/heartbeat` , is the backend alive at all?
2. `tail -n 40 .dev/exapp.log` , the first log line names the binding mode. If it
   says unix socket, the HaRP variables are set in the shell and the port is not
   being served.
3. `docker compose exec -T -u www-data app php occ app_api:app:list` , is the registration still there and enabled?
4. `docker compose logs --tail 100 app` , Nextcloud side errors.

## Windows and WSL2

Docker Desktop uses the WSL2 backend. Bind mounts from a Windows path into the
container are noticeably slower than a path inside the Linux file system, and file
watching is unreliable across that boundary. For everyday work put the checkout in
the WSL2 file system, for example under `~/src/nextcloud-search`, and not under
`C:\Users\...`. The compose file works either way, it only gets slower.

## Shutting down

```bash
docker compose down
kill "$(cat .dev/exapp.pid)"
```

`down` keeps the named volume, so the next start is fast and the instance keeps
its users. Add `-v` to throw the instance away and start from an empty Nextcloud.

## Checking the CI proof

The same path runs on every push through `.github/workflows/integration.yml`:

```bash
gh run list --workflow=integration.yml --limit 1 --json conclusion -q '.[0].conclusion'
```

Expected: `success`. The workflow asserts the same subline, including the user id,
and it also runs the counter check with the backend unregistered.
