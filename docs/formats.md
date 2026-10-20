# File formats

Findling 1.5 reads mails (.eml), ZIP files, Word 97 to 2003 documents (.doc), Excel 97 to 2003 workbooks (.xls) and HEIC/HEIF photos in addition to the formats of 1.4. This page collects what an admin needs to know about them: what is read, what is not, the verdict a file gets when it cannot be read, the limits, and what happens once after the upgrade. The store text and the READMEs name the formats only; the details are here.

| Format | Mimetype | Read by | Type filter group |
|---|---|---|---|
| Mail (.eml) | `message/rfc822` | own reader on the Python `email` package | `text` |
| ZIP file (.zip) | `application/zip` | own reader on `zipfile`, directory counted first | none (D-31-05) |
| Word 97 to 2003 (.doc) | `application/msword` | olefile plus own reader of the piece table | `documents` |
| Excel 97 to 2003 (.xls) | `application/vnd.ms-excel` | xlrd, after a check of the compound file | `spreadsheets` |
| HEIC/HEIF photo | `image/heic`, `image/heif` | pillow-heif, then OCR like every picture | `images` |

No headless office suite is involved: the image carries no LibreOffice, antiword or catdoc.

## Mail (.eml)

| | |
|---|---|
| What is read | Subject, From, To and Cc, decoded in any charset; the text part, or the text of an HTML only mail through the same hardened HTML route as an HTML file; the names of the attachments |
| What is not read | The content of attachments (D-31-04): a search for `vertrag.pdf` finds the mail, a word inside that PDF does not. Bcc, the Received chain and every other header |
| Verdict when it cannot be read | A mail with more than 1000 MIME parts gives its headers only, `indexed(truncated)`. A header longer than 32 KiB is read up to that length, and a mail whose headers together would cost the parser more than 1 MiB gives its headers only; both end as `indexed(truncated)`. A mail nested so deep that the parser runs out of recursion ends as `failed(corrupt)` with the detail `RecursionError`. A header the parser cannot read is left out, the rest of the mail is still indexed |

Mail addresses in From, To and Cc become searchable text. Who sees a hit is decided by the same permission check as for every other file (see `docs/privacy.md`).

## ZIP file

| | |
|---|---|
| What is read | The text of every member Findling can read on its own (PDF with a text layer, DOCX, PPTX, XLSX, ODT, ODS, ODP, HTML, RTF, TXT, Markdown, CSV, EML, DOC, XLS) and of inner ZIP files one level deep. Every member stands in the text with its cleaned name, so a member without text is still found by its name. A hit names the inner file in its excerpt, for example `innen/notiz.txt: ...` |
| What is not read | No OCR inside a ZIP file: pictures stay names, a PDF counts only with a text layer. Encrypted members, members with an unknown extension, members compressed with anything but stored, deflate, bzip2 or LZMA, and members over the file size cap stay names. Nothing is unpacked to disk under its own name |
| Verdict when it cannot be read | Over one of the limits below: `skipped(archive_limit)`. Every member encrypted: `skipped(encrypted)`. A broken central directory: `failed(corrupt)`. The member count, the time share or the text cap end the member loop with `indexed(truncated)` |

### ZIP limits

Fixed constants in `backend/src/findling/config.py`, no admin setting (D-31-07). They hold for the ZIP file as a whole: entries, directory bytes, declared and read bytes and members with text are drawn from one budget that every nesting level shares, so fifty inner ZIP files just under a limit each are one ZIP file over it. The entry count is Findling's own count of the central directory headers before `zipfile` opens the file; the number in the end record is never believed.

| Limit | Constant | Value | Over it |
|---|---|---|---|
| Entries | `ARCHIVE_MAX_ENTRIES` | 10000 | `skipped(archive_limit)` |
| Length of the central directory | `ARCHIVE_MAX_CENTRAL_DIRECTORY_BYTES` | 8 MiB | `skipped(archive_limit)` |
| Uncompressed bytes, declared and read | `EXTRACT_ARCHIVE_TOTAL_MAX_BYTES` | 256 MiB | `skipped(archive_limit)` |
| Compression ratio of one member | `ARCHIVE_MAX_RATIO`, from `ARCHIVE_RATIO_MIN_BYTES` on | 100 to 1, from 1 MiB on | `skipped(archive_limit)` |
| Nesting | `ARCHIVE_MAX_DEPTH` | 2 (a ZIP file inside the ZIP file is read, a ZIP file inside that one ends the whole file) | `skipped(archive_limit)` |
| Members handed to a text reader | `ARCHIVE_MAX_TEXT_MEMBERS` | 1000 | `indexed(truncated)` |
| Share of the extraction timeout for the member loop | `ARCHIVE_TIME_SHARE` | 0.75 | `indexed(truncated)` |
| One member | `FINDLING_MAX_FILE_BYTES` | 50 MiB, the cap of single files | the member stays a name |

The measurements behind every value (2026-10-11, medians of three runs) are in `docs/measurements/2026-10-formate-v15/README.md`, section "ZIP-Grenzwerte". No value moved from the starting point of D-31-07; the length limit of the directory is new.

## Word 97 to 2003 (.doc)

| | |
|---|---|
| What is read | All text of the piece table: main text, footnotes, headers, comments and text boxes. Of a field the result stays and the instructions go. A Word file under a `.docx` name is read by the same reader since 1.5. A file under a Word name that is really RTF, HTML or DOCX is read by what its first bytes say |
| What is not read | Word 6, Word 95 and older. Text deleted under tracked changes is not told apart and is indexed with the rest (a known limit) |
| Verdict when it cannot be read | Word 95 and older, or no `WordDocument` stream: `skipped(unsupported_variant)`. Password protected, XOR obfuscation included: `skipped(encrypted)`. A damaged compound file: `failed(corrupt)` |

## Excel 97 to 2003 (.xls)

| | |
|---|---|
| What is read | The cell values of every sheet of an Excel 5 to 2003 workbook (BIFF5 and BIFF8), written the way the XLSX reader writes them, error cells as their text (`#DIV/0!`). An Excel file under an `.xlsx` name is read by the same reader since 1.5. A file under an Excel name that is really XLSX, HTML or CSV is read by what its first bytes say |
| What is not read | Workbooks before Excel 5 (BIFF2 to BIFF4) and workspace files. Sheet names |
| Verdict when it cannot be read | Over the cell limit of XLSX (`FINDLING_MAX_CELLS`, default 200000): `skipped(too_many_cells)`. BIFF before 5: `skipped(unsupported_variant)`. Password protected: `skipped(encrypted)`. A damaged compound file: `failed(corrupt)`. One huge sheet is held by the address space of the extraction child: `failed(out_of_memory)` |

## HEIC and HEIF photos

| | |
|---|---|
| What is read | The picture, through OCR like JPEG, PNG, TIFF and WebP. Thumbnails, depth and auxiliary images inside the file are not decoded |
| Memory | Decoding a HEIC needs more address space than a JPEG of the same size. With the one malloc arena of the extraction child (since plan 31-07) a 48 MP photo fits under the default of 512 MiB with about 80 MiB to spare, measured on amd64 and arm64. Details in `docs/ocr.md` and `docs/measurements/2026-10-formate-v15/README.md` |
| Verdict when it cannot be read | A photo whose estimate does not fit into the address space: `skipped(too_large)`; raise `FINDLING_EXTRACT_ADDRESS_SPACE_BYTES` to read it. A truncated file: `failed(corrupt)` |

## Old PowerPoint

The PowerPoint format before 2007 has no reader in 1.5. A `.ppt` file is outside the allowlist and ends as `skipped(mime_not_allowed)`; an old PowerPoint file under a `.pptx` name stays `skipped(legacy_format)` as in 1.4.

## Type filter

The six type groups know the new extensions: `eml` under `text`, `doc` and `dot` under `documents`, `xls` and `xlt` under `spreadsheets`, `heic` and `heif` under `images`. `zip` stands in no group (D-31-05): a ZIP file has no document type of its own, whatever its members are, so it appears only when no group is chosen, and choosing all six groups finds slightly less than choosing none. The table and the other limits of the filter are in `docs/search-filters.md`.

## After the upgrade to 1.5

The existing files of an instance are caught up once and without a full reindex, with no step by the admin (FMT-06, D-31-01). Two parts run under the mark `recheck_1_5_0` in `state.db`:

- **Part A** goes through `state.db` and queues once, in bands of at most 200: every `skipped(legacy_format)` except PowerPoint, every row of the new types that is not indexed, and every `failed(repeatedly_stuck)` row once (D-31-02), so files given up under 1.4 get a second chance now that the most common cause, a stale size in the file cache, is fixed.
- **Part B** is one reconcile cycle that is due at once. It compares metadata only and finds the files of the new types that never had a row, because 1.4 never queued them. During this one cycle a file Nextcloud wrote off as `repeatedly_stuck` is queued instead of given up.

Nothing else is touched: no full crawl, no new embedding of indexed files, no change to the index generation. The mark ends as `done` and the catch up never runs again; it also runs once when the reconcile is switched off. The container log names the two steps with numbers only. The full description, with the values of the mark, is in `docs/reconcile.md`, section "Der einmalige Nachholzyklus nach dem Upgrade auf 1.5".

## Upgrade order

Findling has two parts that Nextcloud updates separately: the Findling backend (ExApp, the container) and the Findling app (the companion in the Apps list). Update the Findling backend (ExApp) first, then the Findling app.

Why: the two parts agree on a verdict generation. A 1.5 backend knows the generations of 1.4 and 1.5 and talks correctly to a 1.4.2 app in the meantime. A 1.4.2 backend does not know the generation a 1.5 app announces, treats it as no signal and reports `system_file`, `legacy_format` and `unsupported_variant` to Nextcloud under their 1.3 substitutes (`mime_not_allowed`, `mime_not_allowed`, `image_not_ocrable`). The status page then shows those files under the wrong reason.

If the order was the other way round, nothing needs to be done by hand. Once both parts run 1.5, the one time catch up after the upgrade (mark `recheck_1_5_0`) judges exactly those files again, the ones whose Nextcloud row carries a substitute while the backend holds the real code, and leaves every other file alone. With the recommended order there is nothing to correct and no file is judged again.

## Skip codes

Four codes of the status page change with 1.5 (D-31-03, D-36-03): two are new, two get a new wording. The wording of phase 31 is approved with the release (REL-05), the one of `blocked_malicious` was approved on 20.10.2026 (D-36-04).

| Code | Label | Remedy |
|---|---|---|
| `archive_limit` (new) | ZIP file over the safety limits | None. ZIP files that are nested too deep, too large, too densely packed or hold too many files are skipped so the container keeps running. |
| `blocked_malicious` (new) | File blocked as malicious | None. The file carries the signature of an attack (see the detail) and is not read any further, so the container keeps running. Remove or replace the file if it is not meant to be there. |
| `unsupported_variant` (wider) | Variant of this format that cannot be read | None. The file uses a variant or an encoding Findling cannot read, for example Word 95 or an unusual image encoding. |
| `mime_not_allowed` (remedy only) | File type not supported | None. Findling reads PDF, Office, OpenDocument, text, mails, ZIP files and images. |

`archive_limit` is used for ZIP files only. A companion of generation 2 (Findling app 1.4.x) does not know it; towards that companion the backend reports it as `too_large`, and without any generation signal as well. The German wording is in `docs/store-listing.md`, part 4.

`blocked_malicious` is used only for a file with a signature no normal tool produces (D-36-17); a file that is only large keeps its old verdict. The admin page shows one detail code under the label "Detail", always one of these eight:

| Detail code | Signal |
|---|---|
| `zip_ratio` | a ZIP member of at least 1 MiB declares more than 1000 times its compressed size, on any level |
| `zip_overlap` | ZIP members overlap each other, on any level |
| `zip_traversal` | a ZIP member name holds a `..` segment, starts with `/`, `\` or a drive letter, or holds a NUL |
| `package_entries` | an ODF or OOXML package lists more than 10 000 entries |
| `xml_entities` | the XML parser of an ODF or OOXML part reports entity amplification |
| `image_pixels` | a picture over 100 megapixels with more than 1000 pixels per byte of the file |
| `mail_nesting` | a mail nests attached mails deeper than 32 levels |
| `cfb_cycle` | a sector chain of an old Office file (OLE) runs in a circle |

A ZIP member between 100 and 1000 times its compressed size stays `archive_limit`. Like `archive_limit`, `blocked_malicious` reaches a companion of generation 2 or one without a generation signal as `too_large`.

## Stale file cache size

When Nextcloud's file cache names a larger size than the file really has (a file changed on external storage outside Nextcloud, or a size under server side encryption), the backend downloads it twice, and if both answers have the same length and the same content hash it reads them as the real file and judges it like any other, instead of ending it as `repeatedly_stuck` (POL-02); two short answers that differ stay a passing fault and the row comes back later. The case shows in the backend log as `the file cache names a stale size, the same N of M bytes arrived twice`, numbers only. The limit (A8): a proxy that cuts every answer at exactly the same byte looks the same, and that file is then indexed with the cut content; the remedy is the proxy configuration, not Findling.

## Not supported

- PowerPoint before 2007 (`.ppt`), see "Old PowerPoint" above
- Outlook mails (`.msg`)
- Other packed formats: 7z, rar, tar, gz
- BMP and GIF pictures
- The content of mail attachments; reading them is a candidate for a later release, not a promise
- OCR inside ZIP files
