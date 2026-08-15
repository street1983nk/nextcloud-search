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

   Expected: a result group **File contents** with the entry **Findling canary**.
   The second line reads `produced inside container <host> at <timestamp> for user
   testuser`. That line is the proof: the host name and the timestamp come from
   the running backend process, and the user id comes from the signed AppAPI
   header, so no hard coded string in PHP can produce it.

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
