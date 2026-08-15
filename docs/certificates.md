# App certificates and release signing

**Created: 2026-08-15, the day the app ids were frozen.**

Nextcloud binds an app certificate to the app id through the certificate subject.
Both frozen ids therefore need their own signing key, their own certificate signing
request and their own certificate. See `docs/store-identity.md` for the frozen ids.

| App id | Store section | Certificate signing request | Certificate after merge |
|--------|---------------|-----------------------------|-------------------------|
| `findling` | Apps | `findling/findling.csr` | `findling/findling.crt` |
| `findling_backend` | External Apps | `findling_backend/findling_backend.csr` | `findling_backend/findling_backend.crt` |

Both paths are relative to the repository `nextcloud/app-certificate-requests`.

## Where the keys live

The two private keys and the two signing requests live **outside this repository**, in

```
~/.findling-secrets/
```

with `0700` on the directory and `0600` on the two `.key` files. The directory holds
exactly four files: `findling.key`, `findling.csr`, `findling_backend.key` and
`findling_backend.csr`.

Nothing in that directory is ever copied into this repository. Only the text of a
`.csr` leaves it, and only into the certificate request pull request, where it is
public by design. `.gitignore` blocks `*.key`, `*.pem` and `*.crt` as a second line
of defence, but the primary control is that the files are not inside the working tree
at all.

### Why this matters more than it looks

A private signing key that becomes public cannot be rotated quietly. It forces a
revoke and replace round in `nextcloud/app-certificate-requests`. That repository
contains real pull requests titled "Revoke and replace certificate for X (private key
exposed)". Measured merge times in that repository (state 2026-08-15) have a median of
three to four days, with an observed outlier of eleven days. A leak in the middle of
the release schedule therefore costs days of calendar time, not minutes, and it costs
them twice: once for the revocation and once for the replacement.

Consequences that follow from this, and that are not negotiable:

- The keys are never committed, never pasted into an issue, a pull request or a chat,
  and never printed into a build log.
- The keys never appear in a CI job as a file checked into the repository. They enter
  the release automation only as GitHub Actions secrets, see below.
- The command that generates them is run interactively by a human on a trusted machine,
  not by a workflow.

## How the keys were generated

Verbatim from the official documentation
(`developer_manual/app_publishing_maintenance/code_signing.rst`):

```bash
openssl req -nodes -newkey rsa:4096 -keyout findling.key         -out findling.csr         -subj "/CN=findling"
openssl req -nodes -newkey rsa:4096 -keyout findling_backend.key -out findling_backend.csr -subj "/CN=findling_backend"
```

The common name **must** be the app id. The server checks this during the integrity
check and otherwise reports `Certificate is not valid for required scope`. Verify
before submitting anything:

```bash
openssl req -in ~/.findling-secrets/findling.csr         -noout -subject   # subject=CN=findling
openssl req -in ~/.findling-secrets/findling_backend.csr -noout -subject   # subject=CN=findling_backend
```

Note for Git Bash on Windows: prefix the generating command with `MSYS_NO_PATHCONV=1`,
otherwise the shell rewrites `/CN=findling` into a Windows path and the subject ends up
wrong without any error message.

## Fingerprints

Recorded at creation time so that the request that eventually gets merged can be proven
to be the one that was generated here, and so that a swapped or regenerated key is
noticed instead of silently accepted.

```bash
openssl req -in ~/.findling-secrets/findling.csr         -noout -pubkey | openssl sha256
openssl req -in ~/.findling-secrets/findling_backend.csr -noout -pubkey | openssl sha256
```

| App id | SHA256 of the public key |
|--------|--------------------------|
| `findling` | `781011795ce8b96c78a9fb485d98dd3cd95e0d2cc93c684beebd3263b81e5e3b` |
| `findling_backend` | `70b9340b24457bd29fb107519495e51b3fb7e4edbcf725334c33a229be6f8b8e` |

Both requests were checked with `openssl req -noout -verify` and both reported
`Certificate request self-signature verify OK`. Both keys are RSA 4096.

The same fingerprint can be taken from the issued certificate once it exists, which is
how the certificate is matched back to the local key:

```bash
openssl x509 -in findling.crt -noout -pubkey | openssl sha256
```

If that value differs from the table above, the certificate does not belong to the
local key and must not be used.

## Submitting the requests

One pull request per app against `nextcloud/app-certificate-requests`. Two separate
pull requests rather than one combined request, so a question about one app does not
hold up the other. File name is `APP_ID/APP_ID.csr`, content is the full text of the
`.csr`, and nobody gets mentioned in the description: the maintainers are subscribed to
the repository.

The concrete branches, pull request titles and commands are tracked in
`docs/store-identity.md`, section "Certificate status".

## After the merge

Nextcloud commits the signed certificate into the same directory, where it is publicly
readable. The release workflow fetches it at build time instead of storing it:

```bash
wget --quiet "https://github.com/nextcloud/app-certificate-requests/raw/master/findling/findling.crt"
wget --quiet "https://github.com/nextcloud/app-certificate-requests/raw/master/findling_backend/findling_backend.crt"
```

The certificate is public information. Only the key is secret.

## Signing a release

```bash
php nextcloud/occ integrity:sign-app --privateKey=findling.key         --certificate=findling.crt         --path=<php-app-dir>
php nextcloud/occ integrity:sign-app --privateKey=findling_backend.key --certificate=findling_backend.crt --path=<exapp-dir>
```

The signature is written into the app directory and travels inside the release tarball.
Release metadata is then posted to `https://apps.nextcloud.com/api/v1/apps/releases`
with the `APPSTORE_TOKEN`. Both parts always carry the same major and minor version.

## Secrets in the release automation

The keys reach CI exclusively as GitHub Actions secrets in
`street1983nk/nextcloud-search`:

| Secret | Content | Used for |
|--------|---------|----------|
| `APP_PRIVATE_KEY` | signing key of `findling` | signing the PHP companion tarball |
| `BACKEND_PRIVATE_KEY` | signing key of `findling_backend` | signing the ExApp tarball |
| `APPSTORE_TOKEN` | apps.nextcloud.com account token | uploading the release metadata |

Rules for the workflow that consumes them:

- Write the secret to a file under `$RUNNER_TEMP`, never into the checkout, and remove
  it in a step that runs even when the job fails.
- Never echo a secret, never pass it as a command line argument that ends up in a log,
  and never enable step debugging on a job that touches them.
- The signing job runs only on tags from the default branch, never on pull requests
  from forks, because a fork workflow must never be able to reach these secrets.

## Checklist before a store submission

1. `openssl req -noout -subject` on the request still matches the app id.
2. The fingerprint of the fetched `.crt` matches the table above.
3. The signing step ran and the app directory contains a signature file.
4. No key file exists anywhere under the repository: `git ls-files | grep -E '\.(key|pem)$'` is empty.
