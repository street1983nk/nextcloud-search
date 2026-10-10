# File formats

Findling 1.5 reads mails, ZIP archives, Word 97 to 2003 documents (.doc), Excel 97 to 2003 workbooks (.xls) and HEIC photos in addition to the formats of 1.4. This page collects what an admin needs to know about them; the sections on each format follow with their plans.

## Upgrade order

Findling has two parts that Nextcloud updates separately: the Findling backend (ExApp, the container) and the Findling app (the companion in the Apps list). Update the Findling backend (ExApp) first, then the Findling app.

Why: the two parts agree on a verdict generation. A 1.5 backend knows the generations of 1.4 and 1.5 and talks correctly to a 1.4.2 app in the meantime. A 1.4.2 backend does not know the generation a 1.5 app announces, treats it as no signal and reports `system_file`, `legacy_format` and `unsupported_variant` to Nextcloud under their 1.3 substitutes (`mime_not_allowed`, `mime_not_allowed`, `image_not_ocrable`). The status page then shows those files under the wrong reason.

If the order was the other way round, nothing needs to be done by hand. Once both parts run 1.5, the one time catch up after the upgrade (mark `recheck_1_5_0`) judges exactly those files again, the ones whose Nextcloud row carries a substitute while the backend holds the real code, and leaves every other file alone. With the recommended order there is nothing to correct and no file is judged again.

## Skip codes

Three codes of the status page change with 1.5 (D-31-03): one is new, two get a new wording. The wording is a draft of phase 31 and is approved with the release (REL-05).

| Code | Label | Remedy |
|---|---|---|
| `archive_limit` (new) | ZIP file over the safety limits | None. ZIP files that are nested too deep, too large, too densely packed or hold too many files are skipped so the container keeps running. |
| `unsupported_variant` (wider) | Variant of this format that cannot be read | None. The file uses a variant or an encoding Findling cannot read, for example Word 95 or an unusual image encoding. |
| `mime_not_allowed` (remedy only) | File type not supported | None. Findling reads PDF, Office, OpenDocument, text, mails, ZIP files and images. |

`archive_limit` is used for ZIP files only. A companion of generation 2 (Findling app 1.4.x) does not know it; towards that companion the backend reports it as `too_large`, and without any generation signal as well. The German wording is in `docs/store-listing.md`, part 4.
