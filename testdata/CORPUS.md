# Reference corpus for the read only invariant (IDX-07), the German search proof and OCR

Thirty three small files with three jobs.

**Job one, since phase 1.** The CI job `readonly-gate` copies them into a
throwaway Nextcloud, lets the container read every one of them through the
content gateway, and compares checksums, modification times, sizes and the file
count before and after. If the read path ever writes, the second comparison says
so.

**Job two, since phase 2.** The CI job `index-search-e2e` indexes the very same
directory and then searches it through the ordinary Nextcloud search route. The
files `09` to `12` carry the German language cases that job asserts on.

**Job three, since phase 3.** The files `13` to `33` are what OCR can be judged
on: German administrative prose that exists only as pixels, the Swiss and the
Austrian spelling, the four image formats of D-05, two images that must never
reach the OCR engine, and ten more PDFs that are broken in ten different ways.
Without them every acceptance statement about OCR would be a claim about two
files, one of which is 814 bytes.

Because of job two the files must be neither moved nor renamed nor split into
subdirectories, and no word may be added to one of them without checking the
tables below: `readonly-gate` resolves the file ids over the basename in a flat
WebDAV path, and `index-search-e2e` asserts that a search term hits exactly one
file. Since phase 3 that rule is not a promise any more but a check:
`build_corpus.py` refuses to write the corpus if one of the terms of the second
table stands in a second file.

Total size is 302 KB, of which 295 KB are the rendered pages of job three. That
is the price of being able to prove anything at all about OCR; the twelve files
of the first two jobs still weigh under 7 KB together.

## The files

The verdict column is the **end** verdict: what a file is left with after the
text pass and, where the text pass handed it over, after the OCR pass as well.
`skipped(no_text_layer)` therefore appears nowhere below any more. It is not an
end state since phase 3, it is the handover to the second track, and a scan that
still carried it would be a scan the OCR pass never reached.

Measured on 2026-09-01 with the runtime image of this repository, over the whole
corpus, text pass first and one forced OCR pass for every handover, which is
exactly the sequence `worker/poller.py` produces.

**This column is read by a machine.** The `readonly-gate` job of
`.github/workflows/integration.yml` parses the first backticked token of every
verdict cell and asserts it file by file against the state database after its
indexing pass. Everything behind that token is prose and is ignored. Two rules
follow from that, and both matter more than they look: a new file needs a row
here or the job fails on the missing reference, and a verdict that changes has to
change here in the same commit.

| File | What it is | Verdict | The one term that stands only here |
|---|---|---|---|
| `01-text-layer.pdf` | One page PDF with an embedded Helvetica text object, 63 characters | `indexed` | none |
| `02-scan-no-text-layer.pdf` | One page PDF showing an 8x8 greyscale image, no text object at all | `skipped(empty_text)`, handed over and the engine found nothing on eight by eight pixels | none |
| `03-document.docx` | Minimal but valid OOXML package, two paragraphs, one of them with real umlauts and a sharp s | `indexed` | none |
| `04-notes.txt` | UTF-8 plain text with umlauts and a sharp s | `indexed` | none |
| `05-picture.png` | 8x8 greyscale PNG | `skipped(image_not_ocrable)`, below the plausibility threshold, no engine is started | none |
| `06-zero-bytes.pdf` | An empty file with a PDF extension | `failed(empty_file)` | none |
| `07-password-protected.pdf` | PDF encrypted with the standard security handler, revision 2, 40 bit RC4 | `skipped(encrypted)` | none |
| `08-legacy-encoding.txt` | German text in Windows-1252, without a byte order mark | `indexed` | none |
| `09-bescheid.pdf` | German administrative text in a PDF text layer, font with `/Encoding /WinAnsiEncoding`, 123 characters | `indexed` | Genehmigung |
| `10-kuendigung.docx` | German notice of termination as OOXML | `indexed` | Frist, drei Monate |
| `11-uebersicht.odt` | OpenDocument text, the format the office trio was missing | `indexed` | Verträge |
| `12-aktenvermerk.txt` | A short file note in Windows-1252 | `indexed` | Müller |
| `13-ratsvorlage-scan.pdf` | Three A4 pages of council prose as greyscale images, no text object on any page | `indexed` through the OCR track, 1593 characters over three pages | Bebauungsplan |
| `14-pacht-mit-anhang.pdf` | Five pages: two with a real text layer, three scanned annex pages | `indexed` on the text pass, the three annex pages stay unread on purpose | Pachtvereinbarung |
| `15-schweiz-baubewilligung.pdf` | One scanned A4 page in Swiss spelling, ss instead of the sharp s | `indexed` through the OCR track, 493 characters | Strasse, Baubewilligung |
| `16-oesterreich-mitteilung.pdf` | One scanned A4 page in Austrian wording | `indexed` through the OCR track, 404 characters | Jänner, Grundbuchsauszug |
| `17-beleg.jpg` | A slip with readable text as JPEG, the format phone uploads arrive in | `indexed`, the picture track of plan 03-10 | Zahlungsavis |
| `18-aushang.png` | A notice with readable text as PNG | `indexed`, the picture track | Sperrmüllabfuhr |
| `19-uebermittlung.tif` | A one page TIFF with readable text, deflate compressed | `indexed`, the picture track | Übermittlungsprotokoll |
| `20-rueckruf.webp` | A note with readable text as lossless WebP | `indexed`, the picture track, and leptonica reads WebP without a detour | Rückrufbitte |
| `21-sendebericht.tif` | Three pages in one TIFF, the shape a fax archive has | `indexed`, all three pages in one verdict | Sendebericht |
| `22-icon.png` | 48 by 48 pixels, an icon | `skipped(image_not_ocrable)`, refused below the plausibility threshold, without starting the engine | none |
| `23-gedreht.jpg` | A page photographed sideways, EXIF orientation 6 | `indexed`, uprighted before the engine sees it | Lieferschein |
| `24-abgeschnittener-trailer.pdf` | The file stops in the middle of its trailer | `failed(corrupt)` | none |
| `25-kaputte-xref.pdf` | Every cross reference entry carries a broken keyword | `indexed`, pdfium rebuilds the table | none |
| `26-riesige-seitenzahl.pdf` | 627 bytes that declare one hundred thousand pages | `failed(corrupt)`, and above all: no allocation and no hang | none |
| `27-nullbytes-im-kopf.pdf` | A PDF header followed by 512 NUL bytes | `failed(corrupt)` | none |
| `28-ohne-seiten.pdf` | Valid structure, correct cross reference table, zero pages | `failed(corrupt)` | none |
| `29-doppelt-komprimiert.pdf` | A content stream behind two chained Flate filters | `indexed`, pdfium applies both filters | none |
| `30-nur-ein-bild.pdf` | One A4 page, one image, no text object in the whole file | `indexed` through the OCR track, 332 characters | Zahlungserinnerung |
| `31-riesenformat.pdf` | A page of 14400 by 14400 points, the largest the format allows | `skipped(empty_text)`, handed over, and the nine gigapixel page comes back without readable text | none |
| `32-startxref-ins-leere.pdf` | Correct objects, and a `startxref` that points past the end of the file | `indexed`, pdfium recovers | none |
| `33-seitenbaum-zyklus.pdf` | A page tree that contains itself | `failed(corrupt)`, and above all: no hang | none |

Twenty two indexed, five skipped, six failed. None of the caps of the OCR
cascade is reached on this corpus: no `indexed(truncated)`, no `failed(timeout)`
and no `failed(out_of_memory)`, and the same job that counts the verdicts counts
those three separately, because a corpus that starts hitting a cap is a corpus
whose numbers stop meaning what stands here.

Four of these verdicts are the interesting ones, because they are not what a
first guess says. `25`, `29` and `32` are broken in ways pdfium repairs on the
fly, so they end up indexed; asserting `failed` for them would be asserting a
bug. `26` and `33` are the two that could hang a test run instead of ending it,
and both come back in under ten milliseconds.

Two more are worth knowing before somebody reads them as defects. `14` keeps its
three scanned annex pages unread: a file has exactly one verdict, and the mixed
case is decided in favour of the text that is already machine readable, with the
reasoning in `docs/ocr.md`. And `31` is the one file whose verdict says that a
guard held: a page of nine gigapixels is not rendered, so the engine has nothing
to read and the file ends as `skipped(empty_text)` rather than as a memory
incident.

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

## The DACH cases of phase 3

These three terms are the acceptance basis of D-09, and each of them lives in a
file where the word is a picture of a word. They can only be found after OCR has
run, which is exactly what makes them an acceptance test instead of a claim.

| Case | Searched for | Word in the file | File |
|---|---|---|---|
| Swiss spelling | `Straße` and `Strasse` | Strasse, Bahnhofstrasse | `15-schweiz-baubewilligung.pdf` |
| Austrian wording | `Jänner` | Jänner | `16-oesterreich-mitteilung.pdf` |
| Scanned German prose | `Bebauungsplan` | Bebauungsplan | `13-ratsvorlage-scan.pdf` |

The Swiss case works in both directions without any extra machinery: the German
analyzer chain has no `ascii_fold`, and the Snowball stemmer folds both the
sharp s and the double s onto the token `strass`. The Austrian case is a plain
term match; `Januar` finding `Jänner` would be synonymy and is deliberately not
built. Both statements are measured in `docs/german-analyzer.md`.

## Why twelve broken files

The predecessor app `files_fulltextsearch_tesseract` destroyed user data on its
error path, not on its happy path. A corpus of well formed documents would prove
the pleasant half of the invariant only.

Phase 1 had two of them, the zero byte PDF and the encrypted one, which are the
two cheapest ways into a failure handler. Ten more arrived with OCR, and each of
them names a different failure path in the table above, because "a corrupt PDF"
is not one case: a file that stops mid trailer, a file that declares a hundred
thousand pages in six hundred bytes and a page tree that points at itself fail
in three different places of three different libraries.

All twelve are expected to fail extraction gracefully, to be recorded with a
verdict, and never to be modified, deleted or rewritten. That last part is what
`readonly-gate` measures, and it is the reason the broken files exist at all.

The user password of `07-password-protected.pdf` is `findling`, the owner
password is `findling-owner`. Both are published here on purpose, because a
reviewer has to be able to open the file, and because nothing in this repository
is protected by them.

## Regenerating

Every file is produced by `scripts/dev/build_corpus.py`, with fixed timestamps
and a fixed document id, so a rebuild is byte identical:

```bash
cd backend && uv run python ../scripts/dev/build_corpus.py
```

The script is the source of truth for what is inside these files. Adding a file
means adding it there, never dropping a downloaded document into this directory:
an unknown sample carries an unknown licence. The German, Swiss and Austrian
prose in the script is invented, which is the other half of the same rule.

Adding a **word** to an existing file is the same kind of change and needs the
same care: a term that turns up in a second file quietly turns one of the
assertions of `index-search-e2e` into a test that proves nothing. Since phase 3
the script checks that itself and refuses to write the corpus otherwise.

### The one dependency, and why it is fenced in

Until phase 2 the builder used the standard library alone. Rendered text inside
an image cannot be produced that way, so phase 3 added exactly one drawer,
Pillow, which is a pinned runtime dependency of the container anyway.

The typeface is the part that had to be nailed down, because it decides what the
pixels look like and therefore what OCR reads:

| What | Value |
|---|---|
| File | `testdata/fonts/DejaVuSans.ttf`, 759720 bytes |
| SHA-256 | `57f73e11f51999432bf7ab22ce55b6f945d5eca1bf824404cfa9ec2e3718c84e` |
| Origin | `fonts-dejavu-core` 2.37-8, out of the base image pinned in `backend/Dockerfile` |
| Licence | Bitstream Vera Fonts Licence plus public domain changes, full text in `testdata/fonts/COPYING.dejavu` |

The builder verifies that digest before it draws the first glyph and refuses to
run if it has moved. `ImageFont.load_default()` is not an option here and the
docstring of the script says why: its Aileron Regular has a limited character
set and travels with the Pillow version, and umlauts plus the sharp s are the
one thing a DACH corpus must not lose. A second check renders
`Strasse Jänner Grundstücksverkehrsgenehmigung` and fails the build if any
character comes out as a replacement box.

`.gitattributes` marks this directory as binary (`-text`), so no checkout on any
platform can rewrite a line ending inside a PDF and break its cross reference
table. `08-legacy-encoding.txt` depends on the same rule for a second reason: it
is not UTF-8, and any tool that decided to "fix" its bytes would remove the one
property it exists for.
