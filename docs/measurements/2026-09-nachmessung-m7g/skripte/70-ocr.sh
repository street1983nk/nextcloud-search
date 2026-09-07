#!/bin/sh
# The page for the OCR comparison, rendered the way the pipeline renders it.
#
# 00001-bescheid.pdf is a file of the scan_single category, which is the category
# the run time of the full run is made of: a page image with no text layer, so
# findling.extract.pdf declares it scanned and hands it to tesseract. It is
# rendered here with the same library and the same resolution the pipeline uses
# (pypdfium2, FINDLING_OCR_DPI default 300), so the page the two language sets
# are compared on is the page the product really sees.
set -eu

OUT=/home/ubuntu/work/nachmessung
mkdir -p "$OUT"
CONTAINER=nc_app_findling_backend
QUELLE=/mnt/findling/ncdata/lasttest/files/loadtest/00001-bescheid.pdf

{
    date -u +'ocr-start %Y-%m-%dT%H:%M:%SZ'

    echo "=== The file, and the proof it is a scan ==="
    sudo ls -la "$QUELLE"
    sudo cp "$QUELLE" /tmp/00001-bescheid.pdf
    sudo chmod 644 /tmp/00001-bescheid.pdf
    sudo docker cp /tmp/00001-bescheid.pdf "$CONTAINER:/tmp/seite.pdf"

    echo "=== The page, rendered with the library and the resolution of the pipeline ==="
    sudo docker exec -i "$CONTAINER" /app/.venv/bin/python - <<'PY'
import pathlib

from findling.config import settings
from findling.extract import raster
import pypdfium2

resolved = settings()
print("ocr_dpi:", resolved.ocr_dpi)
print("ocr_languages of this image:", resolved.ocr_languages)
document = pypdfium2.PdfDocument("/tmp/seite.pdf")
print("pages:", len(document))
png = raster.render_page_png(document, 0, dpi=resolved.ocr_dpi)
pathlib.Path("/tmp/seite.png").write_bytes(png)
print("png bytes:", len(png))
PY

    echo "=== The two language sets against each other, five runs each, alternating ==="
    sudo docker cp /home/ubuntu/work/69-ocr-drei-sprachen.py "$CONTAINER:/tmp/69-ocr.py"
    sudo docker exec "$CONTAINER" /app/.venv/bin/python /tmp/69-ocr.py /tmp/seite.png --runs 5

    echo "=== The traineddata this image carries, with their sizes ==="
    sudo docker exec "$CONTAINER" ls -la /usr/share/tesseract-ocr/5/tessdata/

    date -u +'ocr-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$OUT/70-ocr.txt"
echo "70-FERTIG" > "$OUT/70-FERTIG"
