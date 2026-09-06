# Reference corpus for the read only invariant (IDX-07), the German search proof and OCR

Thirty nine small files with four jobs.

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

**Job four, since the launch hardening.** The files `34` to `39` are not broken,
they want something. `34` is a decompression bomb, an OOXML package whose one
part declares a byte more than the archive member cap of
`backend/src/findling/config.py` allows; until it existed, that cap was measured
against a fixture of 65 bytes with the cap lowered to 64, which proves the
comparison and nothing else. The five behind it are well formed PDFs that
describe an action: a script on open, an embedded file, an address, an
encryption a current office suite writes, and a thousand levels of nesting. All
six travel the road a user document travels and lie in the directory
`readonly-gate` freezes.

Because of job two the files must be neither moved nor renamed nor split into
subdirectories, and no word may be added to one of them without checking the
tables below: `readonly-gate` resolves the file ids over the basename in a flat
WebDAV path, and `index-search-e2e` asserts that a search term hits exactly one
file. Since phase 3 that rule is not a promise any more but a check:
`build_corpus.py` refuses to write the corpus if one of the terms of the second
table stands in a second file.

Total size is 391 KB. 313 KB of that are the rendered pages of job three, which
is the price of being able to prove anything at all about OCR, and 65 KB are the
one compressed part of the bomb of job four, which is the floor deflate allows
for a member of that declared size and is worked out in `build_corpus.py`. The
twelve files of the first two jobs still weigh under 7 KB together.

The rendered pages grew by 18 KB on 2026-09-06: the two DACH files took on the
formats the owner asked about, and a rendered line costs pixels. What they took
on and why it went into the existing two files rather than into a new one stands
under "The DACH cases of phase 3" below.

## The files

The verdict column is the **end** verdict: what a file is left with after the
text pass and, where the text pass handed it over, after the OCR pass as well.
`skipped(no_text_layer)` therefore appears nowhere below any more. It is not an
end state since phase 3, it is the handover to the second track, and a scan that
still carried it would be a scan the OCR pass never reached.

Measured on 2026-09-01 with the runtime image of this repository, over the whole
corpus, text pass first and one forced OCR pass for every handover, which is
exactly the sequence `worker/poller.py` produces.

The character counts of `15` and `16` were measured again on 2026-09-06, after
the two pages took on the DACH formats and after `fra` joined the engine's
language list. The two files that did not change, `13` and `30`, came back with
1593 and 332 characters in the same run, byte for byte the numbers of
2026-09-01, so the run compares with the earlier one and the third language did
not move what the engine reads on these pages.

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
| `15-schweiz-baubewilligung.pdf` | One scanned A4 page in Swiss spelling, ss instead of the sharp s, with a numeric date, an amount carrying the Swiss apostrophe and a line of capitals with umlauts | `indexed` through the OCR track, 664 characters | Strasse, Baubewilligung, Ersatzabgabe |
| `16-oesterreich-mitteilung.pdf` | One scanned A4 page in Austrian wording, with a file reference of two slashes, an amount in German notation and a written out date | `indexed` through the OCR track, 594 characters | Jänner, Grundbuchsauszug, Erlagschein, Parteienverkehr |
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
| `34-zip-bombe.docx` | An OOXML package whose `word/document.xml` declares 64 MiB plus one byte and is 65 kB on disk | `skipped(too_large)`, decided on the archive directory, without opening a single member | none |
| `35-startaktion-javascript.pdf` | A document with `/OpenAction` and a JavaScript name tree | `indexed`, the page text and not one character of the script | none |
| `36-eingebettete-datei.pdf` | A document with a file attached inside it | `indexed`, the page text; the attachment is neither unpacked nor read | none |
| `37-verweis-ins-netz.pdf` | A link annotation with a `/URI` action | `indexed`, the page text; the address stays a string and no socket is opened | none |
| `38-aes256-verschluesselt.pdf` | Standard security handler, version 5, revision 6, AES with 256 bits | `skipped(encrypted)`, the same verdict as the RC4 file and over a different road through pypdf | none |
| `39-tief-verschachtelt.pdf` | A page dictionary with a thousand levels of nested arrays in it | `indexed`, the parser refuses the nesting and reads the page | none |

Twenty six indexed, seven skipped, six failed. None of the caps of the OCR
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

### The formats that arrived on 2026-09-06, and what they are for

Three terms prove that a scanned DACH document is findable. They do not say how
well the engine read the page, and a search hit never will: a word the engine
missed simply fails, and a character it got wrong inside a word it still stemmed
correctly is invisible to a search. That is not a gap in the test, it is what
the test is for, and the reasoning is written out in `docs/testing.md`.

The question the owner asked is the other one: does the chain read the umlauts,
the dates and the amounts of this region. That is an answer in numbers, so the
two DACH pages took on the cases it needs and
`findling.extract.ocr_quality` measures the character error rate against them.
The truth is not borrowed from anywhere: `build_corpus.py` renders these pages
out of its own prose, so the source text is the ground truth, byte for byte.

| Case group | On the page | File |
|---|---|---|
| Date, numeric | `01.03.2026` | `15-schweiz-baubewilligung.pdf` |
| Date, written out | `1. März 2026` | `16-oesterreich-mitteilung.pdf` |
| Amount, Swiss notation | `CHF 1'234.56`, apostrophe as the thousands separator | `15-schweiz-baubewilligung.pdf` |
| Amount, German notation | `1.234,56 Euro` | `16-oesterreich-mitteilung.pdf` |
| File reference with slashes | `Geschäftszahl BH/MU/2026/0042-7` | `16-oesterreich-mitteilung.pdf` |
| Two more Austrian words | Erlagschein, Parteienverkehr | `16-oesterreich-mitteilung.pdf` |
| Capitals with umlauts | `ÄNDERUNGEN AN DER AUSSENHÜLLE BENÖTIGEN EINE ZUSTIMMUNG` | `15-schweiz-baubewilligung.pdf` |

They went into the two existing files rather than into a new one because a new
file is not cheap here: it needs a row in the table above, an entry in the
verdict map of `backend/tests/test_extract_documents.py`, a file id in the read
only gate, and it moves the file count that three documents quote. Extending two
files costs their byte size and their character count, and both are written down
above. The price of the choice is visible, the price of the other one would have
been spread over four places.

None of these seven is asserted as a search term, and that is deliberate. The
gate stays what it is, a search hit that survives a Debian point release. The
formats are material for the measurement, and the measurement carries a coarse
bar of its own. What it found is in `docs/measurements/2026-09-06-ocr-dach/`.

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
password is `findling-owner`, and `38-aes256-verschluesselt.pdf` carries the same
two. Both are published here on purpose, because a reviewer has to be able to
open the files, and because nothing in this repository is protected by them.

## The six files that want something

The ten broken PDFs above are accidents: a truncated copy, a wrong offset, a tree
that points at itself. The six files of job four are not broken at all. Every one
of them is a well formed document, and the question each of them asks is not
whether the parser survives it but whether anything of what it asks for happens.

That difference is why each of them is asserted twice in
`backend/tests/test_extract_documents.py`: once that the structure really stands
in the file, and once that the verdict came back without it doing anything. A
test that only checked the verdict would stay green on the day the generator
stops writing the structure, which is the quietest way a security fixture can
die. Three of the files carry a marker word that stands inside the dangerous part
alone, `Skriptmarke`, `Anlagenmarke` and `Netzmarke`, so "it did not run" can be
told apart from "it ran and left no trace".

Two of them are worth a sentence of their own.

`38` is the second encrypted file and not a duplicate of the first. `07` is RC4
with 40 bits, which is what a decade old document looks like, and pypdf answers
`is_encrypted` for it without raising. `38` is what a current office suite
writes, and it takes a different road: pypdf tries the empty password while the
reader is still being built, reaches for an AES provider this lock file
deliberately does not carry and raises `DependencyError`, which descends from
`Exception` and not from `PdfReadError`. Before the launch hardening that
exception escaped the extractor and the document was recorded as
`failed(corrupt)`, which is the wrong word twice: the file is intact, and an
admin would have gone looking for a broken document instead of for a password.
Both roads now end in `skipped(encrypted)`, because the two are the same document
to whoever reads the status page.

`39` is measured rather than guessed. Nesting depths of 100, 400, 500, 512, 600,
1000, 5000 and 50000 were run through the text route on 2026-09-06: every one of
them ends in a verdict, the parser refuses the nested object past its own
recursion limit and reads the page regardless, and the whole range takes 13 to 38
milliseconds. A thousand is the depth the file carries because it sits
unambiguously on one side of every cap, four orders of magnitude inside the
extraction timeout, and keeps the file under three kilobytes. A depth that landed
near a cap would be a coin toss between a fast machine and a loaded runner rather
than a test.

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
