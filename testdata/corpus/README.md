# Reference corpus for the read only invariant (IDX-07)

Eight small files that exist for one purpose: the CI job `readonly-gate` copies
them into a throwaway Nextcloud, lets the container read every one of them
through the content gateway, and compares checksums, modification times, sizes
and the file count before and after. If the read path ever writes, the second
comparison says so.

This is **not** the search quality corpus. Ranking, OCR accuracy and German text
handling are measured against the Ratsvorlagen PDFs in phase 2 and phase 3. What
is collected here is variety of shape, not volume: a container format, a text
format, an image, two encodings and two files that are broken on purpose.

Total size is just over 4 KB, so the repository carries no binary weight.

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

`.gitattributes` marks this directory as binary (`-text`), so no checkout on any
platform can rewrite a line ending inside a PDF and break its cross reference
table. `08-legacy-encoding.txt` depends on the same rule for a second reason: it
is not UTF-8, and any tool that decided to "fix" its bytes would remove the one
property it exists for.
