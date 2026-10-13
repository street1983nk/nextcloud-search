# The type groups of the search filter

The result page offers six type groups, and the search line offers the same six
words behind `type:`. Both are resolved through one table, `TYPE_GROUPS` in
`backend/src/findling/query/rewrite.py`. There is no second table on the PHP
side: the companion app knows the six group names and not a single extension.
Since 1.5 the unified search of Nextcloud offers the same six groups and a
folder filter as well (see "In the unified search" below).

## The table

| Group | Extensions |
|---|---|
| `pdf` | `pdf` |
| `documents` | `docx`, `odt`, `rtf`, `doc`, `dot` |
| `spreadsheets` | `xlsx`, `ods`, `csv`, `xls`, `xlt` |
| `presentations` | `pptx`, `odp` |
| `images` | `jpg`, `jpeg`, `jps`, `mpo`, `png`, `tif`, `tiff`, `webp`, `heic`, `heif` |
| `text` | `txt`, `text`, `md`, `markdown`, `mdown`, `mdwn`, `mkd`, `htm`, `html`, `json`, `xml`, `yaml`, `yml`, `conf`, `cnf`, `eml`, `adoc`, `asciidoc`, `org`, `fb2`, `js` |

The extensions are the ones the mimetype mapping of the server produces for the
twenty four mimetypes the indexer accepts. Since 1.5 these include Word and
Excel 97 to 2003 (`doc`, `dot`, `xls`, `xlt`), HEIC photos (`heic`, `heif`) and
mails (`eml`, which stood under text before). Both `jpg` and `jpeg` are listed, and so
are `tif` and `tiff`, because a file with the other spelling wears the same
symbol in the file list and would otherwise fall out of a filter it visibly
belongs to.

`csv` sits with the spreadsheets rather than with the text files. It is a table
to everybody who opens it, and the group a user looks in is the group it belongs
to.

Group names are matched in lower case, and a name that is not in the table means
"no filter" rather than "no hits". A filter for a group and a `type:` word in
the same search combine as a union: `type:pdf` together with the chip for images
finds both, because the intersection of the two would be guaranteed empty and the
page has no way of explaining an empty list that is nobody's mistake.

## The limits

The first two belong here and deliberately not into the code, because both are
properties of the index rather than decisions a reader could make differently.
The third is a decision, and it is written down here as well.

**An extension that is not listed is reachable under no group.** The table is an
allowlist, not a mapping with a fallback. A `.epub` file is indexed if its
mimetype is one of the twenty four the extractor accepts, and it is found by every
unfiltered search, but no chip of the six brings it up.

**A file without an extension is reachable under no group either.** The indexer
writes the extension into a raw field, `extension_of` returns the empty string
for a name without a dot, and an empty raw field produces no term at all. A term
query therefore cannot reach such a file, under any group. Unfiltered searches
find it as before.

**A ZIP file belongs to no group.** Since 1.5 the text of the files inside a
ZIP file is searchable, and a hit names the inner file in its excerpt. The
ZIP file itself has no document type, whatever its members are, so `zip` stands
in none of the six groups: a ZIP file appears only when no group is chosen, and
choosing all six groups therefore finds slightly less than choosing none.

## In the unified search

Since 1.5 the filter menu of the Nextcloud search shows seven entries of
Findling: one per type group ("File contents: PDF" and so on) and "File
contents in a folder". A type entry narrows the Findling group to that type
group, the folder entry opens the folder picker and narrows it to the chosen
folder.

- The folder includes its sub folders.
- The folder is resolved and checked in the companion app, in the file tree of
  the user who searches, so shares and team folders behave as in the Files app.
  Every hit is still rechecked against the rights of that user; the folder never
  shows a file the user cannot open.
- The folder is never sent to the container; only the companion app sees it.

The limits:

- **A type chip and a folder chip at the same time are two groups, not one.**
  The unified search asks a provider once per chip, so "PDF" and "in Projects"
  produce one group of PDF files and one group of files in Projects, not the
  PDF files in Projects (D-32-02).
- **A type or a folder together with the date filter work together.** The date
  of the unified search is sent with every chip.
- **An empty value is refused by Nextcloud itself.** A request with `types=` or
  `folder=` and nothing after it is answered with HTTP 400 by the Nextcloud
  core, before Findling is asked. The filter entries never send an empty value
  (D-32-01). Choosing the root folder sends `folder=/`, which narrows nothing:
  the chip "File contents in /" shows the hits of the search without a folder.
- **A cancelled folder picker shows no hits.** The chip "File contents in a
  folder" stays, but carries no folder, and a chip without a parameter answers
  with nothing until a folder is chosen.
- **Unknown or manipulated values are ignored.** An unknown type group, an
  overlong value, a folder that does not exist, a path with `..`, a file instead
  of a folder or a folder outside the user's own tree: the search answers
  exactly as it would without the filter, never with an error (D-32-03).
- **A mixed value keeps the known names.** `pdf,videos` filters by `pdf` only;
  the unknown name is dropped.
- **The result page has no folder filter.** The entry "Show all results" at the
  end of a group carries the type groups to the result page, but not the
  folder.
- **ZIP files stay outside every type group** here as well (see "The limits"
  above).

### How the chips reach Findling

The Nextcloud core keeps every filter entry an app registers in its list of
providers, and a search without a chip asks each entry once, without the
parameter of any chip. The seven entries therefore do not ask the provider
`findling` (the one group "File contents" of a search without a chip) but a
second, hidden provider, `findling-filter`:

- Its order is null, so the provider list of the dialog does not name it: it is
  neither a group nor a menu entry of its own.
- A request without `types` and without `folder` is answered with an empty
  group and never reaches the backend. That is every request the core sends for
  a menu entry while no chip is set, and the core shows no group without a hit.
- A request with `types` or `folder` is handed to the provider `findling` as it
  came: same filters, same rights, same recheck, same group name.

An admin who limits the providers of the unified search with the core setting
`unified_search.providers_allowed` has to allow `findling-filter` next to
`findling`, or the chips of Findling stay empty.

**One dependency on core internals.** The date of the core is only sent with a
chip whose provider declares `since` and `until`. The core looks that up in its
provider list under the `searchFrom` of the chip and, for `findling-filter`,
finds nothing there and falls back to the chip itself. So the callback of each
entry writes the filter map (`since`, `until`, `types`, `folder`) onto `this`,
which the core sets to the menu entry it copies the chip from right after the
callback (Nextcloud 33 to 35 and master, read on 2026-10-13). This is not an API.
If a later core calls the callback differently, the entries still work and
still filter by type and folder; only a type or folder chip together with the
date filter loses the date. The script sets the map only when `this` is an
object, so nothing throws.

## The period

`since` and `until` narrow by the modification time of the file, both bounds
inclusive, and either one may stand alone. The value is a Unix time stamp in
seconds, the same number the server stores, so the comparison carries no time
zone of its own. The bounds run as a range over the fast column of the index;
neither a reindex nor a schema change is involved.
