# Store identity freeze

**Freeze date: 2026-08-15**

This document is binding. The identifiers below are frozen before any code writes
them into a file, a namespace or a directory name. They must not be changed again.

## Frozen identifiers

| Item | Value | Store section |
|------|-------|---------------|
| PHP companion app id | `findling` | Apps |
| Python ExApp id | `findling_backend` | External Apps |
| PHP namespace | `OCA\Findling` | n/a |
| Python package | `findling` | n/a |
| Container image | `ghcr.io/street1983nk/findling_backend` | n/a |
| Source repository | `github.com/street1983nk/nextcloud-search` | n/a |
| License | AGPL-3.0-or-later | n/a |

Both parts always carry the same major and minor version, so users cannot let them
drift apart. This mirrors the `context_chat` / `context_chat_backend` pattern, which
is the only verified two entry layout for a search provider backed by an ExApp.

## Availability evidence

Checked live immediately before the freeze on 2026-08-15:

| Feed | Query | Result |
|------|-------|--------|
| `https://apps.nextcloud.com/api/v1/platform/34.0.0/apps.json` | `"id": "findling"` | 0 hits |
| `https://apps.nextcloud.com/api/v1/platform/34.0.0/apps.json` | `"id": "findling_backend"` | 0 hits |
| `https://apps.nextcloud.com/api/v1/appapi_apps.json` | `"findling_backend"` | 0 hits |
| `https://apps.nextcloud.com/api/v1/appapi_apps.json` | `"id": "findling"` | 0 hits |

A substring sweep for `findling` over both feeds returned no entry at all, so neither
id is taken and neither collides with a similarly named app.

## Why the freeze happens first

The app certificate is bound to the app id through the certificate subject
(`-subj "/CN=findling"`). Renaming an app after the certificate signing request has
been merged invalidates the certificate and forces a second CSR round. Measured merge
times in `nextcloud/app-certificate-requests` (state 2026-08-15) have a median of
three to four days with an outlier of eleven days. A rename late in the schedule would
therefore cost more than a week of calendar time and would put the release date at
risk. See phase research, Pitfall 8 ("late rename invalidates the certificate").

Each app id needs its own certificate signing request, so two pull requests are filed
against `nextcloud/app-certificate-requests`, one per id, on the day of the freeze.

## Change procedure

There is none in the normal sense. Changing either id after the certificate signing
requests are merged requires:

1. A new CSR per changed id, with the new id as the certificate subject.
2. Waiting for the merge, historically three to eleven days.
3. A new store entry, because the app id is the store primary key. The old entry
   cannot be renamed, it can only be abandoned.
4. Renaming the namespace, the Python package, the container image and every route.

Any proposal to rename must be treated as a schedule change, not as a cosmetic one.

## Decision record

The owner froze both ids on 2026-08-15. The decision is recorded in
`.planning/phases/01-integrationsbeweis/01-CONTEXT.md`, section "Identity and store",
and in `.planning/PROJECT.md` under key decisions.

## Certificate status

Both signing requests were generated on 2026-08-15, the day of the freeze, and prepared
as two separate branches in the fork `street1983nk/app-certificate-requests`. Two
separate pull requests against `nextcloud/app-certificate-requests`, one per app id, so
a question about one app does not hold up the other. Key handling, fingerprints and the
signing path are documented in `docs/certificates.md`.

| App id | Fork branch | Pull request title | Status | Pull request | Submitted | Merged |
|--------|-------------|--------------------|--------|--------------|-----------|--------|
| `findling` | `findling-csr` | Add certificate request for findling | prepared, not submitted | _pending_ | _pending_ | _pending_ |
| `findling_backend` | `findling-backend-csr` | Add certificate request for findling_backend | prepared, not submitted | _pending_ | _pending_ | _pending_ |

Verified on both branches before submission: each branch adds exactly one file, the
signing request itself, and changes nothing else. No key material is contained in either
branch. Expect a median of three to four days until merge, with an observed outlier of
eleven days. Nothing in phase 1 is blocked while the requests are pending.

Opening the pull requests is an owner step. The branches are ready and the commands
below only need to be executed.

### Pull request body for findling

> findling is the PHP companion app of a Nextcloud search integration. It registers a
> search provider so that document search results appear in the normal unified search,
> and forwards every query to its ExApp counterpart findling_backend, which is submitted
> in a separate request. Source code: https://github.com/street1983nk/nextcloud-search,
> licensed AGPL-3.0-or-later.

### Pull request body for findling_backend

> findling_backend is the ExApp container behind the findling search app. It extracts
> text, runs OCR and maintains the search index inside the instance, so no file content
> ever leaves the server. It is only reachable through the companion app findling, which
> is submitted in a separate request. Source code:
> https://github.com/street1983nk/nextcloud-search, licensed AGPL-3.0-or-later.

Nobody is mentioned in either description. The maintainers are subscribed to the
repository, so a mention only creates noise.

### Commands that open the two pull requests

```bash
gh pr create --repo nextcloud/app-certificate-requests --base master --head street1983nk:findling-csr --title "Add certificate request for findling" --body "findling is the PHP companion app of a Nextcloud search integration. It registers a search provider so that document search results appear in the normal unified search, and forwards every query to its ExApp counterpart findling_backend, which is submitted in a separate request. Source code: https://github.com/street1983nk/nextcloud-search, licensed AGPL-3.0-or-later."
gh pr create --repo nextcloud/app-certificate-requests --base master --head street1983nk:findling-backend-csr --title "Add certificate request for findling_backend" --body "findling_backend is the ExApp container behind the findling search app. It extracts text, runs OCR and maintains the search index inside the instance, so no file content ever leaves the server. It is only reachable through the companion app findling, which is submitted in a separate request. Source code: https://github.com/street1983nk/nextcloud-search, licensed AGPL-3.0-or-later."
```

After both are open, record the two links, the submission date and later the merge date
in the table above. Once a request is merged, the signed certificate appears in the same
directory of the upstream repository and is fetched by the release workflow as described
in `docs/certificates.md`.
