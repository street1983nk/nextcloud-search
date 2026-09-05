# Third party material shipped with Findling

Findling itself is AGPL-3.0-or-later. This file lists every third party artifact
that is *distributed* with it, either inside the backend container image or
inside the app store release archives, together with its origin, its version, its
licence and the place it can be found in the image.

Two sentences up front, because they are the reason this file exists at all:

- **The recipe that derives data from the German word list stays in this
  repository.** `backend/src/findling/index/wordlist.py` reduces
  `/usr/share/dict/ngerman` to the length window, lowercases it, adds the linking
  elements and writes `dict/de.txt` into the app volume. That file is derived
  data from a GPL-2+ work and it is distributed inside the image, so the script
  that produces it is kept where anybody can read it, next to the measurement in
  `docs/german-analyzer.md` and the reproducible run in
  `scripts/dev/measure_wordlist.sh`.
- **GPL-2+ and AGPL-3.0 are compatible here.** GPL-2+ means "version 2 or, at
  your option, any later version", so the word list may be used under GPLv3, and
  GPLv3 and AGPLv3 are explicitly combinable (AGPLv3 section 13). Nothing in this
  list is copyleft in a way that reaches further than that, and nothing in it is
  non-commercial or share-alike on the data level.

## The word list

| Item | Value |
|---|---|
| Debian package | `wngerman`, version `20161207-15`, `Architecture: all` |
| Source package | `igerman98`, upstream Björn Jacke, Debian maintainer Roland Rosenfeld |
| Origin | Debian trixie archive, installed with `apt-get` during the image build |
| File in the image | `/usr/share/dict/ngerman` (356010 lines, 4725887 bytes) |
| Licence | **GPL-2+** (`debian/copyright`, `Files: *`, `Copyright: 1999-2016 Björn Jacke`); upstream additionally offers an OASIS distribution licence as an alternative |
| Licence text in the image | `/usr/local/share/findling/COPYING.wngerman`, copied from `/usr/share/doc/wngerman/copyright` |
| Derived artifact | `$APP_PERSISTENT_STORAGE/dict/de.txt`, produced at start up, SHA-256 recorded in the meta table |

`wngerman` pulls one dependency into the image even with
`--no-install-recommends`, and it is listed here because it is distributed too:

| Item | Value |
|---|---|
| Debian package | `dictionaries-common` 1.30.10, 711 kB installed |
| Why it is there | hard `Depends` of `wngerman`; it registers the word list with the ispell machinery. Findling reads the plain file and never calls any of it |
| Licence | GPL-2+ and GPL-3+ in parts (`/usr/share/doc/dictionaries-common/copyright`), both reachable from AGPL-3.0 through GPLv3 |

Measured: the whole apt layer, both packages and the dpkg metadata together, is
8.2 MB, of which 4.6 MB is `/usr/share/dict`.

The licence text is copied to a path of our own on purpose. Debian slim images
carry `path-exclude /usr/share/doc/*` in `/etc/dpkg/dpkg.cfg.d`, and only a
`path-include` for `copyright` keeps that one file alive today. A licence
obligation must not depend on a dpkg configuration line in a base image somebody
else maintains, so the build copies the file and fails if it is missing.

## The OCR engine and its language data

Added in phase 3. Same construction as the word list above and for the same
reason: the data has to be in the image, because a first start that downloads a
model is not zero-config.

| Item | Value |
|---|---|
| Debian package | `tesseract-ocr`, version `5.5.0-1+b1`, architecture dependent |
| Source package | `tesseract`, upstream `github.com/tesseract-ocr/tesseract` |
| Origin | Debian trixie archive, installed with `apt-get` during the image build |
| Files in the image | `/usr/bin/tesseract` plus `libtesseract5` and `libleptonica6` |
| Licence | **Apache-2.0** (`debian/copyright`, `Files: *`, `Copyright: 1988-1995 Hewlett Packard Company, 2006-2024 Google Inc.`) |
| Licence text in the image | `/usr/local/share/findling/COPYING.tesseract`, copied from `/usr/share/doc/tesseract-ocr/copyright` |
| Version pin | **none on purpose.** The package is architecture dependent and carries the binary NMU suffix `+b1` on amd64 and on arm64. A hard pin breaks the multi-arch build; the anchor is the digest of the base image |

| Item | Value |
|---|---|
| Debian packages | `tesseract-ocr-deu`, `tesseract-ocr-eng`, `tesseract-ocr-osd`, all version `1:4.1.0-2`, all `Architecture: all` |
| Source package | `tesseract-lang`, upstream `github.com/tesseract-ocr/tessdata_fast` |
| Files in the image | `/usr/share/tesseract-ocr/5/tessdata/deu.traineddata` (1525436 bytes), `eng.traineddata` (4113088 bytes), `osd.traineddata` (10562727 bytes) |
| Licence | **Apache-2.0** (`debian/copyright`, `Upstream-Name: tessdata_fast`) |
| Licence text in the image | `/usr/local/share/findling/COPYING.tesseract-langdata`, copied from `/usr/share/doc/tesseract-ocr-deu/copyright` |
| Version pin | `1:4.1.0-2`, hard. `Architecture: all`, so amd64 and arm64 read byte identical models and no scan is read differently on the ARM box than on the x86 one |

Two licence files cover five packages, and that is measured, not assumed: on
2026-09-01 the copyright files of `tesseract-ocr` and `libtesseract5` were byte
identical (`md5 cd5e791f…`), and so were the three of `tesseract-ocr-deu`,
`-eng` and `-osd` (`md5 63a049f5…`).

The optional Fraktur model `tesseract-ocr-frk` `1:4.1.0-2` is **not** installed
today. It carries the same licence and would be listed here the moment the line
in the Dockerfile is uncommented.

`tesseract-ocr` pulls a large dependency closure into the image even with
`--no-install-recommends`, and all of it is distributed too:

| Item | Value |
|---|---|
| Count | 71 new Debian packages, 104415 kB installed size, measured on 2026-09-01 in the pinned base image |
| The heavy ones | `tesseract-ocr-osd` (10331 kB, the orientation model), `libtesseract5` (3948 kB), `libicu76` (37371 kB, via `libxml2` and `libharfbuzz`), the pango, cairo, freetype and X11 client libraries that `libtesseract5` links, and the image codecs `libtiff6`, `libwebp7`, `libopenjp2-7`, `libpng16-16t64`, `libjpeg62-turbo`, `libgif7` |
| Licences | all Debian main, therefore DFSG free, per package under `/usr/share/doc/*/copyright`; the closure is MIT, BSD, LGPL-2.1+, X11/MIT-X, Apache-2.0 and, for `libgnutls30t64`, LGPL-2.1+ with the usual GPL-3+ tools split. Nothing in it is copyleft beyond LGPL, and nothing reaches further than the AGPL-3.0 of Findling |

That closure is why the OCR feature is not free in image size. It is the price
of not shipping our own build of tesseract, which would mean owning its security
updates ourselves.

## Python packages of the extraction and index path

All ten are installed from PyPI into `/app/.venv` and are pinned exactly in
`backend/pyproject.toml` and `backend/uv.lock`. All ten ship wheels; no
`setup.py` runs at installation time.

| Package | Version | Licence | Source repository | Place in the image |
|---|---|---|---|---|
| `tantivy` | 0.26.0 | MIT | github.com/quickwit-oss/tantivy-py | `/app/.venv/lib/python3.13/site-packages/tantivy` |
| `pypdfium2` | 5.13.0 | Apache-2.0 or BSD-3-Clause (wrapper), BSD-3-Clause (bundled PDFium) | github.com/pypdfium2-team/pypdfium2 | `/app/.venv/lib/python3.13/site-packages/pypdfium2` |
| `pypdf` | 6.16.1 | BSD-3-Clause | github.com/py-pdf/pypdf | `/app/.venv/lib/python3.13/site-packages/pypdf` |
| `python-docx` | 1.2.0 | MIT | github.com/python-openxml/python-docx | `/app/.venv/lib/python3.13/site-packages/docx` |
| `python-pptx` | 1.0.2 | MIT | github.com/scanny/python-pptx | `/app/.venv/lib/python3.13/site-packages/pptx` |
| `openpyxl` | 3.1.5 | MIT | foss.heptapod.net/openpyxl/openpyxl | `/app/.venv/lib/python3.13/site-packages/openpyxl` |
| `striprtf` | 0.0.32 | BSD-3-Clause | github.com/joshy/striprtf | `/app/.venv/lib/python3.13/site-packages/striprtf` |
| `charset-normalizer` | 3.5.1 | MIT | github.com/jawah/charset_normalizer | `/app/.venv/lib/python3.13/site-packages/charset_normalizer` |
| `lxml` | 6.1.1 | BSD-3-Clause (bundled libxml2 and libxslt: MIT) | github.com/lxml/lxml | `/app/.venv/lib/python3.13/site-packages/lxml` |
| `pillow` | 12.3.0 | MIT-CMU | github.com/python-pillow/Pillow | `/app/.venv/lib/python3.13/site-packages/PIL` |

`tantivy` is the one entry whose licence is **not** readable from its PyPI
metadata: the 0.26.0 release carries neither a `license` field nor a licence
classifier. The MIT text is in `LICENSE` of the tagged upstream repository
(`quickwit-oss/tantivy-py`, tag `0.26.0`), and the Rust crate the bindings wrap
is MIT as well. It is written down here so the next reader does not have to
repeat the search.

## Python packages of the semantic path, and the model they run

Added in phase 6. Four packages and one model, all pinned exactly in
`backend/pyproject.toml` and `backend/uv.lock`. All four ship wheels; no
`setup.py` runs at installation time.

| Package | Version | Licence | Source repository | Place in the image |
|---|---|---|---|---|
| `fastembed` | 0.8.0 | Apache-2.0 | github.com/qdrant/fastembed | `/app/.venv/lib/python3.13/site-packages/fastembed` |
| `onnxruntime` | 1.29.0 | MIT | github.com/microsoft/onnxruntime | `/app/.venv/lib/python3.13/site-packages/onnxruntime` |
| `sqlite-vec` | 0.1.9 | Apache-2.0 | github.com/asg017/sqlite-vec | `/app/.venv/lib/python3.13/site-packages/sqlite_vec`, and the extension itself a second time at `/usr/local/lib/findling/vec0.so` |
| `semantic-text-splitter` | 0.32.0 | MIT | github.com/benbrandt/text-splitter | `/app/.venv/lib/python3.13/site-packages/semantic_text_splitter` |

`sqlite-vec` is the entry with the second copy, and the copy is the point. The
package ships a prebuilt shared library inside its wheel, and that library is
what SQLite loads into the process. The build copies it out of the wheel to a
path of our own, checks its SHA-256 in the same `RUN` and exports the path as
`FINDLING_VEC0_PATH`, so the thing that gets loaded is a property of the image
and not a property of a package layout that may move in the next release. The
Apache-2.0 text travels with it as
`/usr/local/share/findling/COPYING.sqlite-vec`, for the same reason the word
list and the OCR data carry theirs: the image is what is distributed.

The model is not a package, so it gets its own table:

| Item | Value |
|---|---|
| Model | `intfloat/multilingual-e5-small`, 384 dimensions, 512 token context |
| Origin | HuggingFace, repository `intfloat/multilingual-e5-small`, read on 2026-09-04 |
| Licence | **MIT** (HuggingFace API, `cardData.license = "mit"`, tag `license:mit`) |
| Licence text in the image | `/usr/local/share/findling/COPYING.multilingual-e5-small` |
| What is fetched at build time | `onnx/model.onnx` (470268510 bytes, fp32), `onnx/tokenizer.json`, `onnx/sentencepiece.bpe.model`, `config.json`, `tokenizer_config.json`, `special_tokens_map.json`, each checked against a SHA-256 written in `backend/Dockerfile` |
| What is distributed | the **self quantised** int8 ONNX file plus the tokenizer and the configuration, under `/usr/local/share/findling/model`. The fp32 original stays in the build stage and never reaches the runtime image |
| Why self quantised | the int8 file the upstream repository ships is `onnx/model_qint8_avx512_vnni.onnx`, and AVX512-VNNI is x86 only. On the ARM box this app targets it is unusable, so the build quantises `onnx/model.onnx` itself with `scripts/dev/quantize_model.py` |

Two network libraries enter the image through `fastembed` and are listed here
because they are distributed too: `huggingface-hub` 1.30.0 (Apache-2.0) and
`requests` 2.34.2 (Apache-2.0). Neither is called at run time. The model and the
tokenizer sit at fixed paths in the image, `HF_HUB_OFFLINE=1` is set in the
runtime stage, and the probe of plan 06-01 as well as the offline test of plan
06-10 run the container with `--network none`. `numpy`, `tokenizers`,
`protobuf`, `flatbuffers` and the rest of the closure are resolved and pinned in
`backend/uv.lock`, which stays the authoritative list of what lands in
`/app/.venv`.

`usearch` is deliberately **not** installed. It is the documented way out if
brute force KNN stops scaling, plan 06-04 writes that way out down in
`docs/embeddings.md`, and a
fallback path that nobody imports is not a dependency and does not belong in a
list of distributed material.

## The rest of what the image carries

| Item | Version | Licence | Origin | Place in the image |
|---|---|---|---|---|
| `python:3.13-slim-trixie` base image | digest `sha256:ffb752e1…c6e30a` | Debian base: mixed free licences, per package under `/usr/share/doc/*/copyright`; CPython: PSF-2.0 | docker-library/python | the image itself |
| `nc-py-api[app]` | 0.30.3 | BSD-3-Clause | github.com/cloud-py-api/nc_py_api | `/app/.venv` |
| `fastapi` | 0.141.1 | MIT | github.com/fastapi/fastapi | `/app/.venv` |
| `httpx` | 0.28.1 | BSD-3-Clause | github.com/encode/httpx | `/app/.venv` |
| `frpc` | frp 0.61.1 | Apache-2.0 | fatedier/frp, fetched from the pinned commit of nextcloud/HaRP that vendors the byte identical tarball | `/usr/local/bin/frpc` |

The transitive dependencies of the packages above (starlette, uvicorn, pydantic
and their own dependencies) are resolved and pinned in `backend/uv.lock`, which
is the authoritative list of what actually lands in `/app/.venv`. They are not
repeated here one by one; this file names the direct edges, the lock file names
the closure.

`uv` 0.11.7 and the build stage tools (`curl`, `ca-certificates`) are build time
only. They are not part of the runtime image and are therefore not distributed.

## The icon path data of the admin page

Added in phase 4. This one is not in the container image, it travels in the app
store archive of the PHP companion app, which is why it is listed among the
distributed material and not further down.

| Item | Value |
|---|---|
| Project | Material Design Icons by Pictogrammers |
| Source repository | `github.com/Templarian/MaterialDesign-SVG` |
| Pinned commit | `9e04201d4557e729822fb57f62a316c3dea1d4a8` (tag `v7.4.47`), read on 2026-09-02 |
| Licence | **Apache-2.0** (`LICENSE` of the repository), compatible with the AGPL-3.0 of Findling |
| What is used | the `d` attribute of nine icons and nothing else: `magnify`, `alert-circle-outline`, `clock-outline`, `minus-circle-outline`, `content-cut`, `folder-off-outline`, `check-circle-outline`, `information-outline` and `close` |
| Where it lands | `php/img/app-dark.svg` carries `magnify` as the section icon. `php/templates/admin.php` carries the other eight: `alert-circle-outline` in the banners of the coverage block and the failed chip, `clock-outline` in the chip of the waiting queue and the queued chip of the lookup, `minus-circle-outline` for skipped, `content-cut` for a truncated document, `folder-off-outline` for an excluded file, `check-circle-outline` for an indexed one, `information-outline` in the hint banners and the unknown chip, and `close` on the button that removes one folder exclusion |

The commit is pinned instead of `master` because a path is data, and data that
is quoted has to be quotable. Every string in this repository is byte identical
to the `svg/<name>.svg` of the same name at that commit, which is a claim
anybody can check with the command at the end of this file.

The table is kept complete rather than growing a row per plan. It said for two
plans that the remaining icons of the phase four design contract "get their row
here in the plan that first renders one of them", and that is what happened now:
plan 04-08 renders `close`, which is the one icon of this page that the design
contract does not list at all, because the contract names eight states and this
is a control. An attribution table that lags behind the markup by two plans is a
table nobody can check, so the whole list is named here at once.

No package, no icon font, no build step and no runtime dependency. What is
copied here is nine hundred characters of curve data, which is why the app has
no `package.json` at all: the design contract of phase 4 forbids a bundler in
the companion app, and an icon set was the only reason to want one.

A tenth icon would need no new row either, only a new name in the table above:
the licence, the repository and the pinned commit are the same for all of them,
and what is copied is the curve data of one glyph.

## Material in the repository that is not in the image

One entry, added in phase 3, and it is listed although it travels with neither
the container image nor the app store archives: it is committed to a public
repository, and a font carries a licence whether it is shipped or not.

| Item | Value |
|---|---|
| File | `testdata/fonts/DejaVuSans.ttf`, 759720 bytes, SHA-256 `57f73e11f51999432bf7ab22ce55b6f945d5eca1bf824404cfa9ec2e3718c84e` |
| Debian package | `fonts-dejavu-core` 2.37-8, `Architecture: all` |
| Origin | read out of the base image pinned in `backend/Dockerfile`, not downloaded from anywhere else |
| Licence | Bitstream Vera Fonts Licence (permissive, redistribution and modification allowed); the DejaVu changes are public domain |
| Licence text | `testdata/fonts/COPYING.dejavu`, the `debian/copyright` of the package verbatim |
| Why it is here | `scripts/dev/build_corpus.py` renders the scanned pages of the OCR corpus with it. The pixels have to be identical on every machine and in every year, so the typeface is pinned by checksum instead of taken from whatever the build host happens to have installed |

The Bitstream Vera licence asks that the fonts not be sold on their own and that
the names "Bitstream" and "DejaVu" not be used to promote derived work without
permission. Neither applies here: the file is unmodified, it is not sold, and it
is not part of any release artifact.

## How to check this file against reality

```bash
# the word list and its licence, inside the built image
docker run --rm ghcr.io/street1983nk/findling_backend:dev \
    sh -c 'wc -lc /usr/share/dict/ngerman; head -3 /usr/local/share/findling/COPYING.wngerman'

# the OCR engine, its models and both licence texts, inside the built image
docker run --rm --entrypoint sh ghcr.io/street1983nk/findling_backend:dev \
    -c 'tesseract --list-langs; ls -l /usr/local/share/findling/'

# the pinned versions of the Python side
grep -A 20 '^dependencies' backend/pyproject.toml

# the icon path data against the pinned upstream commit
mdi=9e04201d4557e729822fb57f62a316c3dea1d4a8
for icon in magnify alert-circle-outline clock-outline minus-circle-outline \
            content-cut folder-off-outline check-circle-outline \
            information-outline close; do
    curl -sf "https://raw.githubusercontent.com/Templarian/MaterialDesign-SVG/${mdi}/svg/${icon}.svg" \
        | grep -o 'd="[^"]*"'
done
grep -o 'd="[^"]*"' php/img/app-dark.svg php/templates/admin.php
```
