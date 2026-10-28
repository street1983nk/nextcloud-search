# HaRP tunnel certificates

The backend container reaches HaRP through an frp tunnel with mutual TLS. This
page covers the one way that tunnel breaks for good: HaRP issues a new CA and the
backend still holds the old certificates.

## Cause

- `/certs/frp` inside the backend container (`ca.crt`, `client.crt`,
  `client.key`) is a copy. HaRP writes it into the container on
  `occ app_api:app:register` and `occ app_api:app:update`, and at no other time.
- HaRP creates a new CA named `harp.nc` only when its own `/certs/frp` is
  missing, which means after a restart without a persistent `/certs` volume.
- From then on HaRP refuses the old client certificate and the backend refuses
  the new server certificate. frpc keeps retrying with the old files.

## Recognising it

- frpc in the backend container log, about every 20 seconds:
  `connect to server error: tls: failed to verify certificate: x509: certificate signed by unknown authority (possibly because of "crypto/rsa: verification error" while trying to verify candidate authority certificate "harp.nc")`
- From Findling 1.6.0 on, the watcher in the same log names the cause:
  `harp_connect: the tunnel certificate is no longer accepted by HaRP (x509), most likely HaRP was restarted without its /certs volume and issued a new CA; frpc keeps retrying and picks up new files in /certs/frp by itself; copy them in or re-register the app, see https://github.com/street1983nk/nextcloud-search/blob/main/docs/harp-tunnel.md#repair-without-re-registering`
- `connect to server error: session shutdown` on its own is not a signal; it also
  appears in other situations.
- The container stays `running`, the search finds nothing.
- The admin page and `occ findling:diagnose` show that the backend does not
  answer (`backendReachable` false, the line `backend answered: no`), but not
  why. The cause is only in the container log, in the remedy line above.

## Prevention

- Put HaRP's `/certs` on a persistent volume. Then a restart keeps the CA.
- TrueNAS: fixed with truenas/apps PR #6254 (merged 2026-10-27). After that app
  update HaRP starts once with an empty volume and issues new certificates, so
  repair once as below.
- The update to Findling 1.6.0 goes through `app_api:app:update`, which also
  copies fresh certificates into the new container.

## Repair without re-registering

`HARP` stands for the name of the HaRP container: `appapi-harp` in the standard
installation, another name on TrueNAS and similar platforms (`docker ps` shows
it). The backend container is `nc_app_findling_backend`.

```sh
HARP=appapi-harp
for f in ca.crt client.crt client.key; do
  docker exec "$HARP" cat "/certs/frp/$f" \
    | docker exec -i nc_app_findling_backend sh -c 'umask 077; cat > "/certs/frp/.$1.new" && mv -f "/certs/frp/.$1.new" "/certs/frp/$1"' sh "$f"
done
```

- Do not use `docker cp` here: the files would belong to root and `client.key`
  would not be readable for the app user. `docker exec` writes as the app user.
- The temporary name plus `mv -f` means frpc never reads half a file.
- Expected within about 20 seconds in the backend log: `login to server success`,
  then `harp_connect: the tunnel is connected again`. No container restart is
  needed.

## Fallback: re-register without --rm-data

- `occ app_api:app:unregister findling_backend` without `--rm-data` keeps the data
  volume.
- Install again: External Apps in the admin settings, or
  `occ app_api:app:register findling_backend <daemon>`.
- The index and the settings stay in the volume. See [uninstall.md](uninstall.md).

## Limits

- The watcher never fetches certificates itself. HaRP's control API is not meant
  for ExApps, and using the shared key for it would be a misuse.
- frpc is restarted only for changed files that read the same in two checks in a
  row, at most 6 times per hour and at least 60 seconds apart.
- Never a fall back to a weaker mode: without readable files frpc keeps its
  current configuration.
- An instance with `FINDLING_HARP_PLAINTEXT=1` that later receives certificates
  switches to mutual TLS with the frpc restart the watcher makes for the new
  files. That is a step up and harmless.
- The remedy line appears at once, after 5, 15 and 60 minutes, then hourly.

## Proof

- CI step `Certificate rotation, a reissued HaRP CA heals after the three files are copied in`
  in `.github/workflows/deploy-harp.yml`, on all four legs including arm64: real
  reissue, tunnel shown dead without new files, healed after the copy above
  without re-register and without container restart. Green in deploy-harp run
  RUN_ID_PENDING.
- Watcher logic: `backend/tests/test_harp_connect_supervisor.py`.
