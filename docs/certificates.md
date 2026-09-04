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

The directory holds exactly four files: `findling.key`, `findling.csr`,
`findling_backend.key` and `findling_backend.csr`.

Access is restricted to the owner. On a POSIX host that is `0700` on the directory and
`0600` on the two `.key` files. On the Windows workstation where the keys were generated
`chmod` is a no-op against NTFS: it reports success and leaves the file at `0644`. The
restriction there has to be an access control list, and it was applied as one:

```
icacls "%USERPROFILE%\.findling-secrets" /inheritance:r /grant:r "%USERNAME%:(OI)(CI)F"
```

Verify with `icacls "%USERPROFILE%\.findling-secrets\findling.key"`. The output must list
the owner account and nothing else. Do not trust `ls -l` on Windows for this check, it
shows the emulated mode, not the real permissions.

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

The digest is taken over the **DER** of the public key, not over the PEM text that
`openssl ... -pubkey` prints. The PEM text is not stable across openssl versions: for
the very same key, OpenSSL 3.0.13 and 3.5.6 print PEM that hashes to different values
(`f5324067...` against `78101179...` for `findling`). The table below therefore held a
value that only one machine could reproduce, and the release run failed on it on
04.09.2026 while the development machine kept saying the certificate was fine. The DER
is the encoding of the key itself and is identical under both versions.

```bash
openssl req -in ~/.findling-secrets/findling.csr -noout -pubkey \
  | openssl pkey -pubin -outform DER | openssl sha256
openssl req -in ~/.findling-secrets/findling_backend.csr -noout -pubkey \
  | openssl pkey -pubin -outform DER | openssl sha256
```

| App id | SHA256 of the public key (DER) |
|--------|--------------------------------|
| `findling` | `c99e28f3decd64cf5d3e7fdecaac4e3d29b3444c71b7cb914aff81519f2108ab` |
| `findling_backend` | `340d369f3573d9c936f0ce9de5e8af978425131c2d66adec2231e86642592e76` |

Both requests were checked with `openssl req -noout -verify` and both reported
`Certificate request self-signature verify OK`. Both keys are RSA 4096.

The same fingerprint can be taken from the issued certificate once it exists, which is
how the certificate is matched back to the local key:

```bash
openssl x509 -in findling.crt -noout -pubkey \
  | openssl pkey -pubin -outform DER | openssl sha256
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
- Strip carriage returns before writing the key to a file.

How to store the two key secrets, because getting this wrong costs a release run:
the value has to arrive with **LF** line endings. The key files in
`~/.findling-secrets/` are CRLF on the development machine, and a value stored from
them unchanged makes the signing step fail in a way that names neither the key nor
the line endings. PHP’s openssl cannot read a CRLF PEM, `openssl_sign` returns
false, and Nextcloud dies with `base64_encode(): Argument #1 ($string) must be of
type string, bool given` out of `IntegrityCheck/Checker.php` (seen on 04.09.2026,
run 33895245084). Store them from a shell that does not re-encode the stream:

```bash
tr -d '' < ~/.findling-secrets/findling.key \
  | gh secret set APP_PRIVATE_KEY --repo street1983nk/nextcloud-search
tr -d '' < ~/.findling-secrets/findling_backend.key \
  | gh secret set BACKEND_PRIVATE_KEY --repo street1983nk/nextcloud-search
```

The workflow strips CR as well, so a value stored the wrong way no longer breaks the
run. Both belts are wanted: the workflow protects the run, this paragraph protects
the next person from debugging a PHP type error.

How `.github/workflows/release.yml` implements the third rule is worth stating,
because it is not the `if:` condition the sentence suggests. That workflow has **no
`pull_request` trigger at all**. A condition inside a step can be weakened by a later
edit that looks harmless; a trigger that does not exist cannot be reached by anybody.
The workflow does accept a `workflow_dispatch`, and that is not a hole: dispatching a
workflow requires write access to this repository, so it can never come from a fork.
The rehearsal run needs it, and a rehearsal that produced no signature would rehearse
nothing.

## The release run

`.github/workflows/release.yml` turns everything below into one run. This section is the
reason the file has the shape it has, so that the next release does not have to guess.

### Two signatures, with the same key and different jobs

This is the single most confused part of a Nextcloud store release. If one of the two is
wrong, the store answers `Invalid signature` and does not say which.

| Signature | Command | Where it ends up | Who checks it |
|-----------|---------|------------------|---------------|
| Code signature | `occ integrity:sign-app --privateKey= --certificate= --path=` | `appinfo/signature.json` **inside** the archive | the integrity check of the Nextcloud instance |
| Release signature | `openssl dgst -sha512 -sign KEY archive.tar.gz \| openssl base64 -A` | the `signature` field of the upload, and `<archive>.sig` next to the archive | apps.nextcloud.com at upload time |

Both are needed, and the order is not a preference:

1. **Stage** the app into a directory named exactly after the app id.
2. **Code sign** it, so that `appinfo/signature.json` is inside the directory.
3. **Pack** the directory into a `tar.gz` with exactly one top level entry.
4. **Release sign** the packed archive.

Step 4 has to come last because the release signature belongs to the *bytes of the
archive*, and any change to the archive invalidates it. That has one consequence which
decides the shape of the whole workflow: **the archive that is signed must be the archive
that is uploaded, and nothing may rebuild it afterwards.** A `tar.gz` is not byte
reproducible, so a rebuilt archive carries a signature that belongs to a file nobody
has. The sister project of this author learned this on its 0.1.8 release, where the
locally built archive was 45710 bytes and the published one 45546, and its runbook now
recomputes the signature over the downloaded asset. `release.yml` needs no such step: it
builds each archive once, signs it, and hands that same file to `gh release create`.

Only the companion half is code signed. The reason is not that the other half is less
important, it is that the code signature is checked over the PHP files a Nextcloud
instance loads, and the ExApp half delivers none: it is a container that AppAPI runs
beside the instance, and its archive is metadata. The release signature, by contrast, is
required for **both** halves, because the store checks it for every upload.

### The hard limits, and what they measure today

Checked in the run as separate steps with separate messages, so that a failure names
which limit was hit. The measured column is the rehearsal of 04.09.2026 at version
1.0.0, which is also the answer to whether any of these is close.

| Limit | Value | Companion | Backend |
|-------|-------|-----------|---------|
| Archive size | under 20 MB (20971520 bytes) | 220913 bytes | 26807 bytes |
| `info.xml` size | under 512 KB (524288 bytes) | 15039 bytes | 25280 bytes |
| Top level entries in the archive | exactly 1, lowercase ASCII, with `appinfo/info.xml` in it | `findling/` | `findling_backend/` |
| Screenshot URL length | at most 256 characters | 91 to 102 characters | 91 to 101 characters |

Two more that are not sizes: the download URL must be `https`, and so must every
screenshot URL. `backend/tests/test_store_metadata.py` holds the two URL rules, including
the one no schema can state, namely that an image really lies behind the address.

### What is in the archives and what is deliberately not

The staging step uses an **include** list rather than an exclude list, so that a new
directory under `php/` has to be named before it ships instead of shipping because
nobody remembered to exclude it.

| Half | Contains | Measured |
|------|----------|----------|
| `findling` | `appinfo`, `lib`, `templates`, `js`, `css`, `img`, `l10n`, plus `LICENSE` and `THIRD-PARTY.md`, plus the `appinfo/signature.json` that signing writes | 67 entries |
| `findling_backend` | `appinfo/info.xml` byte for byte, plus `LICENSE` and `THIRD-PARTY.md` | 5 entries |

Never in either archive, and asserted in the run rather than merely intended:
`tests`, `phpunit.xml`, `composer.json`, `composer.lock`, `vendor`. Plan 05-15
introduced `phpunit/phpunit` as a `require-dev` dependency of the companion app, and the
promise that neither it nor a vendor directory reaches the release is written into
`php/composer.json` itself. An archive with test code in it is a different product from
the one that was reviewed.

Two things travel with both halves for a licence reason rather than a tidiness one.
`php/img/app-dark.svg` and `php/templates/admin.php` carry nine icon paths from Material
Design Icons under Apache-2.0, and `THIRD-PARTY.md` is the attribution for them.
Shipping the icons without the attribution is the one licence mistake these archives
could make. `LICENSE` travels because AGPL-3.0-or-later requires the licence text to
accompany the work.

The backend `info.xml` is copied byte for byte and is never filtered or rewritten. That
is a hard requirement: `pre-info.xslt` drops the `routes` block silently, so the store
database never sees the five routes of the container, and AppAPI reads them back out of
this archive at installation time. An archive with a rewritten `info.xml` installs an app
with no search route and no error message. The `app-metadata` job of `php.yml` holds that
finding as a step that goes red if the transform ever stops dropping them.

### How to run it

```bash
# The rehearsal: builds, signs, uploads four artifacts, creates NO release.
gh workflow run release.yml --ref main

# The real thing: a tag does it, and create_release is not needed on a tag push.
git tag v1.0.0 && git push origin v1.0.0
```

The `create_release` input defaults to false on purpose. A public release 1.0.0 that is
not in the store yet can be found and installed, which is threat T-05-77 of plan 05-18
and the owner's decision of 04.09.2026 for the rehearsal.

### One trap that is local to the development machine

`docs/certificates.md` gives `MSYS_NO_PATHCONV=1` for the interactive key generation on
Git Bash, and that is correct for a command whose only awkward argument is
`-subj "/CN=findling"`. It is the wrong tool the moment the same command also has file
paths: the prefix disables path conversion for *every* argument, so an output path under
`/tmp` reaches a native `openssl` literally and the command fails without writing
anything. Write the subject as `-subj "//CN=findling"` instead, which exempts that one
argument and leaves the paths alone. None of this applies to the workflow, which runs on
Linux.

## Checklist before a store submission

1. `openssl req -noout -subject` on the request still matches the app id.
2. The fingerprint of the fetched `.crt` matches the table above. `release.yml` does this
   by machine now, for both halves, and refuses to sign if either differs.
3. The signing step ran and the app directory contains a signature file. Asserted in the
   run for the companion half, and asserted to be *absent* for the backend half.
4. No key file exists anywhere under the repository: `git ls-files | grep -E '\.(key|pem)$'` is empty.
5. Both archives passed the store validation path (`xsltproc` with the pinned
   `pre-info.xslt`, then `xmllint` against the pinned `info.xsd`) over the staged
   `info.xml`, not over the working tree copy.
6. Both size limits held, and both release signatures verify against the fetched
   certificate.
7. Neither archive contains `tests`, `vendor`, `phpunit.xml`, `composer.json` or
   `composer.lock`.
8. `APP_PRIVATE_KEY` and `BACKEND_PRIVATE_KEY` exist as repository secrets, and
   `APPSTORE_TOKEN` exists for the upload in phase 6.
9. Both store entries name at least one screenshot, and an image really lies behind each
   address: `cd backend && uv run python -m pytest tests/test_store_metadata.py`.
