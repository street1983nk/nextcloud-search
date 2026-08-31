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

## Python packages of the extraction and index path

All nine are installed from PyPI into `/app/.venv` and are pinned exactly in
`backend/pyproject.toml` and `backend/uv.lock`. All nine ship wheels; no
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

`tantivy` is the one entry whose licence is **not** readable from its PyPI
metadata: the 0.26.0 release carries neither a `license` field nor a licence
classifier. The MIT text is in `LICENSE` of the tagged upstream repository
(`quickwit-oss/tantivy-py`, tag `0.26.0`), and the Rust crate the bindings wrap
is MIT as well. It is written down here so the next reader does not have to
repeat the search.

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

## How to check this file against reality

```bash
# the word list and its licence, inside the built image
docker run --rm ghcr.io/street1983nk/findling_backend:dev \
    sh -c 'wc -lc /usr/share/dict/ngerman; head -3 /usr/local/share/findling/COPYING.wngerman'

# the pinned versions of the Python side
grep -A 20 '^dependencies' backend/pyproject.toml
```
