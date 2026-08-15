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
