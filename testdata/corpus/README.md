# Reference corpus for the read only invariant (IDX-07) and the German search proof

Twelve small files with two jobs.

**Job one, since phase 1.** The CI job `readonly-gate` copies them into a
throwaway Nextcloud, lets the container read every one of them through the
content gateway, and compares checksums, modification times, sizes and the file
count before and after. If the read path ever writes, the second comparison says
so.

**Job two, since phase 2.** The CI job `index-search-e2e` indexes the very same
directory and then searches it through the ordinary Nextcloud search route. The
files `09` to `12` carry the German language cases that job asserts on.

Because of job two the files must be neither moved nor renamed nor split into
subdirectories, and no word may be added to one of them without checking the
table below: `readonly-gate` resolves the file ids over the basename in a flat
WebDAV path, and `index-search-e2e` asserts that a search term hits exactly one
file.

Ranking quality and OCR accuracy are still **not** measured here; those belong to
the Ratsvorlagen material of phase 3. What is collected here is variety of shape
plus one carrier per language case.

Total size is under 7 KB, so the repository carries no binary weight.

## The files

| File | What it is | Which path it exercises |
|---|---|---|
| `01-text-layer.pdf` | One page PDF with an embedded Helvetica text object | The cheap path: text can be extracted without OCR |
| `02-scan-no-text-layer.pdf` | One page PDF showing an 8x8 greyscale image, no text object at all | The expensive path: text extraction returns nothing, so OCR has to decide |
| `03-document.docx` | Minimal but valid OOXML package, two paragraphs, one of them with real umlauts and a sharp s | ZIP based office formats and their part relationships |
| `04-notes.txt` | UTF-8 plain text with umlauts and a sharp s | Encoding detection, the one file that is not a container |
| `05-picture.png` | 8x8 greyscale PNG | Image files, which reach OCR without a PDF around them |
| `06-zero-bytes.pdf` | An empty file with a PDF extension | The error path: a parser handed zero bytes |
| `07-password-protected.pdf` | PDF encrypted with the standard security handler, revision 2, 40 bit RC4 | The error path: a document that cannot be opened at all |
| `08-legacy-encoding.txt` | The same kind of German text in Windows-1252, without a byte order mark | Encoding detection where it can actually fail: every umlaut is a single byte and invalid UTF-8 |
| `09-bescheid.pdf` | German administrative text in a PDF text layer, font with `/Encoding /WinAnsiEncoding` | The compound and the file type case |
| `10-kuendigung.docx` | German notice of termination as OOXML | The second compound, the phrase and the exclusion case |
| `11-uebersicht.odt` | OpenDocument text, the format the office trio was missing | The nominal inflection case |
| `12-aktenvermerk.txt` | A short file note in Windows-1252 | The written out umlaut case |

## The language cases and which file carries them

Every search term of the CI job `index-search-e2e` hits exactly one file. That is
the whole point of the table: in a corpus where every word stands everywhere, a
green assertion only says that something was found. The tokens in the last column
were measured against the real constituent list (`/usr/share/dict/ngerman`,
recipe A of `docs/german-analyzer.md`), not derived from the spelling.

| Case | Searched for | Word in the file | File | Tokens |
|---|---|---|---|---|
| Compound over one constituent | `Genehmigung` | Grundstücksverkehrsgenehmigung | `09-bescheid.pdf` | `grundstuck verkehr genehm` |
| Compound over one constituent | `Frist` | Kündigungsfrist | `10-kuendigung.docx` | `kundig frist` |
| Written out umlaut | `Mueller` | Müller | `12-aktenvermerk.txt` | query `muell` plus variant `mull` |
| Nominal inflection | `Vertrag` | Verträge | `11-uebersicht.odt` | `vertrag` |
| Phrase | `"drei Monate"` | drei Monate | `10-kuendigung.docx` | `drei monat`, adjacent |
| Exclusion | `bescheid -frist` | Bescheid without Kündigungsfrist | `09-bescheid.pdf` | `bescheid` minus `frist` |
| File type | `type:pdf bescheid` | Bescheid in a PDF | `09-bescheid.pdf` | `bescheid` plus `ext:pdf` |

The one word that stands in **two** files on purpose is `Bescheid`, in `09` and
in `10`. Without it the exclusion `bescheid -frist` would have nothing to
exclude and would be green even if the minus did nothing at all.

Two documented limits of the analysis chain are deliberately **not** in this
table and deliberately not asserted anywhere: `suchte` does not find `suchen`,
and `Mietvertrag` is not findable through `Vertrag` because it stands in the
constituent list itself. Both are measured and explained in
`docs/german-analyzer.md` under "Known limits"; neither is a defect.

The user password of `07-password-protected.pdf` is `findling`, the owner
password is `findling-owner`. Both are published here on purpose, because a
reviewer has to be able to open the file, and because nothing in this repository
is protected by them.

## Why two broken files

The predecessor app `files_fulltextsearch_tesseract` destroyed user data on its
error path, not on its happy path. A corpus of well formed documents would prove
the pleasant half of the invariant only. The zero byte PDF and the encrypted PDF
are the two cheapest ways to send an extractor into its failure handling, and
the gate insists that failure handling still leaves every byte on disk untouched.

Both are expected to be readable as a byte stream in phase 1: the gateway hands
out content, it does not parse it. From phase 2 on they are expected to fail
extraction gracefully and to be recorded as skipped, never to be modified,
deleted or rewritten.

## Regenerating

Every file is produced by `scripts/dev/build_corpus.py` from the Python standard
library alone, with fixed timestamps and a fixed document id, so a rebuild is
byte identical:

```bash
python scripts/dev/build_corpus.py
```

The script is the source of truth for what is inside these files. Adding a file
means adding it there, never dropping a downloaded document into this directory:
an unknown sample carries an unknown licence.

Adding a **word** to an existing file is the same kind of change and needs the
same care: a term that turns up in a second file quietly turns one of the
assertions of `index-search-e2e` into a test that proves nothing.

`.gitattributes` marks this directory as binary (`-text`), so no checkout on any
platform can rewrite a line ending inside a PDF and break its cross reference
table. `08-legacy-encoding.txt` depends on the same rule for a second reason: it
is not UTF-8, and any tool that decided to "fix" its bytes would remove the one
property it exists for.
