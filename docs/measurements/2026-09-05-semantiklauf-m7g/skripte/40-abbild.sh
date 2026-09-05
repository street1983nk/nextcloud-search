#!/bin/sh
# The image WITH the semantic half, built on the box, pushed into the registry on
# the box. Same path as 10-abbild.sh of plan 05-21, one tag further on.
#
# What is different from 05-21: this image carries the model stage of
# backend/Dockerfile, so the build pulls the e5-small weights and quantises them
# to int8. That stage is the reason the build is longer than the one of 05-21 and
# the reason this script runs detached.
#
# The proof that the built image carries the code of this tree is a hash over
# every python file of the package with line endings normalised, because the tree
# comes from Windows and carries CRLF.
set -eu

TAG='localhost:5000/findling_backend:06-11-arm'
REPO=/home/ubuntu/work/repo0611
OUT=/home/ubuntu/work/semantik
mkdir -p "$OUT"

echo "=== Registry auf 127.0.0.1:5000 ==="
sudo docker ps --format '{{.Names}} {{.Status}}' --filter name=findling-registry

echo "=== Bau ==="
date -u +'bau-start %Y-%m-%dT%H:%M:%SZ'
cd "$REPO/backend"
sudo docker build --build-context scripts="$REPO/scripts" --tag "$TAG" . 2>&1 | tail -40
date -u +'bau-ende %Y-%m-%dT%H:%M:%SZ'

echo "=== Push und Kennung ==="
sudo docker push "$TAG" 2>&1 | tail -3
sudo docker image inspect "$TAG" --format 'Id={{.Id}} Size={{.Size}} Created={{.Created}}'
sudo docker image inspect "$TAG" --format 'RepoDigest={{index .RepoDigests 0}}' || true

echo "=== Baumhash im Abbild ==="
sudo docker run --rm --entrypoint /app/.venv/bin/python "$TAG" - <<'PY'
import hashlib
import pathlib

root = pathlib.Path("/app/.venv/lib/python3.13/site-packages/findling")
h = hashlib.sha256()
n = 0
for p in sorted(root.rglob("*.py")):
    data = p.read_bytes().replace(b"\r\n", b"\n")
    h.update(p.relative_to(root).as_posix().encode() + b"\0" + hashlib.sha256(data).hexdigest().encode() + b"\n")
    n += 1
print("dateien:", n)
print("baumhash:", h.hexdigest())
PY

echo "=== Baumhash des Arbeitsbaums, zum Vergleich ==="
python3 - <<'PY'
import hashlib
import pathlib

root = pathlib.Path("/home/ubuntu/work/repo0611/backend/src/findling")
h = hashlib.sha256()
n = 0
for p in sorted(root.rglob("*.py")):
    data = p.read_bytes().replace(b"\r\n", b"\n")
    h.update(p.relative_to(root).as_posix().encode() + b"\0" + hashlib.sha256(data).hexdigest().encode() + b"\n")
    n += 1
print("baum-dateien:", n)
print("baum-baumhash:", h.hexdigest())
PY

echo "=== Baumhash der PHP-Haelfte ==="
python3 - <<'PY'
import hashlib
import pathlib

root = pathlib.Path("/home/ubuntu/work/repo0611/php")
h = hashlib.sha256()
n = 0
for p in sorted(root.rglob("*.php")):
    data = p.read_bytes().replace(b"\r\n", b"\n")
    h.update(p.relative_to(root).as_posix().encode() + b"\0" + hashlib.sha256(data).hexdigest().encode() + b"\n")
    n += 1
print("php-dateien:", n)
print("php-baumhash:", h.hexdigest())
PY

echo "=== Die Semantik im Abbild: Modell, vec0, Pruefsumme ==="
sudo docker run --rm --entrypoint /bin/sh "$TAG" -c '
  echo "-- Modellverzeichnis --"
  ls -la /usr/local/share/findling/model
  echo "-- sha256 der int8-Datei --"
  sha256sum /usr/local/share/findling/model/model.onnx 2>/dev/null || \
    find /usr/local/share/findling/model -name "*.onnx" -exec sha256sum {} \;
  echo "-- vec0 --"
  ls -la "$FINDLING_VEC0_PATH" 2>/dev/null || find / -name "vec0*.so" 2>/dev/null | head -3
  echo "-- die Umgebungsvorgaben --"
  env | grep -i "FINDLING\|HF_HUB" | sort
'

echo "=== Die Semantik antwortet: ein echter Einbettungsaufruf im Abbild ==="
sudo docker run --rm --network none --entrypoint /app/.venv/bin/python "$TAG" - <<'PY'
from findling.api import resources

m = resources.query_model()
v = m.embed_query("Wie kuendige ich meinen Vertrag?")
print("verfuegbar:", v.available)
print("dimension:", len(v.vector) if v.vector is not None else None)
PY

echo "40-ABBILD-FERTIG"
