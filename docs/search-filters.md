# The type groups of the search filter

The result page offers six type groups, and the search line offers the same six
words behind `type:`. Both are resolved through one table, `TYPE_GROUPS` in
`backend/src/findling/query/rewrite.py`. There is no second table on the PHP
side: the companion app knows the six group names and not a single extension.

## The table

| Group | Extensions |
|---|---|
| `pdf` | `pdf` |
| `documents` | `docx`, `odt`, `rtf` |
| `spreadsheets` | `xlsx`, `ods`, `csv` |
| `presentations` | `pptx`, `odp` |
| `images` | `jpg`, `jpeg`, `jps`, `mpo`, `png`, `tif`, `tiff`, `webp` |
| `text` | `txt`, `text`, `md`, `markdown`, `mdown`, `mdwn`, `mkd`, `htm`, `html`, `json`, `xml`, `yaml`, `yml`, `conf`, `cnf`, `eml`, `adoc`, `asciidoc`, `org`, `fb2`, `js` |

The extensions are the ones the mimetype mapping of the server produces for the
eighteen mimetypes the indexer accepts. Both `jpg` and `jpeg` are listed, and so
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

## The two limits

These two belong here and deliberately not into the code, because both are
properties of the index rather than decisions a reader could make differently.

**An extension that is not listed is reachable under no group.** The table is an
allowlist, not a mapping with a fallback. A `.epub` file is indexed if its
mimetype is one of the eighteen the extractor accepts, and it is found by every
unfiltered search, but no chip of the six brings it up.

**A file without an extension is reachable under no group either.** The indexer
writes the extension into a raw field, `extension_of` returns the empty string
for a name without a dot, and an empty raw field produces no term at all. A term
query therefore cannot reach such a file, under any group. Unfiltered searches
find it as before.

## The period

`since` and `until` narrow by the modification time of the file, both bounds
inclusive, and either one may stand alone. The value is a Unix time stamp in
seconds, the same number the server stores, so the comparison carries no time
zone of its own. The bounds run as a range over the fast column of the index;
neither a reindex nor a schema change is involved.
