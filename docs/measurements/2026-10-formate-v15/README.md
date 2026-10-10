# Messungen der Phase 31 (Formate v1.5), ab 11.10.2026

Dieser Bericht sammelt die Messungen der Phase 31 (neue Formate und
Nachholweg). Er beginnt mit der Imagegröße (Plan 31-01); die Abschnitte zum
Speicherbedarf beim Dekodieren großer HEIC-Fotos (Plan 31-07) und zu den
ZIP-Grenzwerten (Plan 31-08) hängen die späteren Pläne an.

---

## Imagegröße

**Frage:** Wie viel wächst das Backend-Image durch die drei Pakete der Phase,
olefile 0.47, xlrd 2.0.2 und pillow-heif 1.8.0 (mit libheif 1.23.4, libde265
1.1.3 und dem x265-Encoder 4.2 im Wheel)?

**Datum:** 10.10.2026, 22:16 bis 23:05 UTC (nach Ortszeit schon der 11.10.).

**Vorher:** Image des Commits `0fc8da9e` (Plan 31-01 Task 1, nur Workflow-Trigger
und ein Test, keine Paketänderung), gebaut von `docker.yml` Lauf 38090784794.
Die beiden Plattform-Manifeste sind bytegleich mit denen des Vorgängerbaus
(Index `sha256:92101c2ac289...`); nur der Index-Digest wechselte, weil die
Attestierung neu ist.

**Nachher:** Image des Commits `f124673c` (Pins aus Plan 31-01 Task 2, Skript
und Doku aus Task 3), gebaut von `docker.yml` Lauf **38093349796** (beide
Architekturen und der Manifest-Merge grün). `:dev` und das Commit-Tag
`f124673c8ba3926309b4d3b0c4d6297e5c2b630a` zeigen auf denselben Index.

### Komprimiert, aus dem Manifest

| Plattform | Digest vorher | Digest nachher | komprimiert vorher | komprimiert nachher | Differenz |
|---|---|---|---|---|---|
| Index | `sha256:ff7fe89687b750d71ee92a4f9f14e9627f8d88fc0e7835af72ee6304a88d1d32` | `sha256:766907ff2acf783d9d57ea1dcb3f9b79b3bc1bbed50f2b1fe854d08e01d1de20` | | | |
| linux/amd64 | `sha256:457369ef4d9d3ec903461fbd5e08fb3458d7739bfa992ab65834442cd442fd46` | `sha256:38b8b8d2b992862d9ab736b41435ae792fc254eee0671954252219d51d7cba94` | 303.036.097 B (303,04 MB) | 309.219.069 B (309,22 MB) | **+6.182.972 B (+6,18 MB, +5,90 MiB)** |
| linux/arm64 | `sha256:9db88fdcfef33a047a3908d609562bb689cb8111f22cbc0f8825ae6c2fc4e4a9` | `sha256:920b7bcda688962df6c9ba6968dfd7d58cdaf74fc2ee16a838e97d22d40d371f` | 298.630.984 B (298,63 MB) | 305.924.493 B (305,92 MB) | **+7.293.509 B (+7,29 MB, +6,96 MiB)** |

Beide Images haben 16 Layer; der Zuwachs liegt in dem Layer, den
`uv sync --frozen --no-dev` schreibt.

Verfahren: Manifest-Liste und je Plattform das Bild-Manifest mit
`docker buildx imagetools inspect <ref> --raw` gelesen und die Felder `size`
aller `layers` summiert (Konfiguration und Attestierung nicht mitgezählt).
Das Hilfsskript dafür, sinngemäß:

```python
import json, subprocess
def raw(ref):
    out = subprocess.run(["docker", "buildx", "imagetools", "inspect", ref, "--raw"],
                         check=True, capture_output=True, text=True).stdout
    return json.loads(out)
repo = "ghcr.io/street1983nk/findling_backend"
for m in raw(f"{repo}:dev")["manifests"]:
    if m.get("platform", {}).get("os") == "linux":
        layers = raw(f"{repo}@{m['digest']}")["layers"]
        print(m["platform"]["architecture"], m["digest"], sum(l["size"] for l in layers))
```

### Unkomprimiert, je Paket

amd64 im Image gemessen (Image per Digest gezogen, allein auf dem Rechner, mit
`--network none` gestartet, danach wieder entfernt):

```bash
docker run --rm --network none --entrypoint sh \
    ghcr.io/street1983nk/findling_backend@sha256:38b8b8d2b992862d9ab736b41435ae792fc254eee0671954252219d51d7cba94 \
    -c 'cd /app/.venv/lib/python3.13/site-packages && du -sb pillow_heif pillow_heif.libs \
        pillow_heif-*.dist-info _pillow_heif*.so olefile olefile-*.dist-info xlrd xlrd-*.dist-info'
```

arm64 aus den Wheels auf PyPI (entpackte Summe aller Einträge per
`zipfile`, `pillow_heif-1.8.0-cp313-cp313-manylinux_2_26_aarch64.manylinux_2_28_aarch64.whl`);
olefile und xlrd sind reines Python und auf beiden Architekturen gleich.

| Anteil | amd64 (im Image, `du -sb`) | arm64 (Wheel entpackt) |
|---|---|---|
| `pillow_heif.libs/libx265-*.so.216` | 22.785.761 B | 11.431.673 B |
| `pillow_heif.libs/libheif-*.so.1.23.4` | 3.017.649 B | 2.923.457 B |
| `pillow_heif.libs/libde265-*.so.0.2.3` | 983.713 B | 926.369 B |
| `_pillow_heif.cpython-313-*.so` | 286.689 B | 536.585 B |
| pillow-heif Python-Teil und dist-info | 200.678 B (mit Bytecode) | Rest der 15.915.099 B |
| **pillow-heif gesamt** | **27.274.490 B (27,27 MB)** | **15.915.099 B (15,92 MB)** |
| olefile samt dist-info | 469.452 B (mit Bytecode) | 369.227 B (Wheel) |
| xlrd samt dist-info | 698.924 B (mit Bytecode) | 383.799 B (Wheel) |
| **alle drei** | **28.442.866 B (28,44 MB)** | **16.668.125 B (16,67 MB) plus Bytecode** |

Das Image kompiliert beim Bau Bytecode (`UV_COMPILE_BYTECODE=1` in
`backend/Dockerfile`); auf amd64 macht das bei den drei Paketen rund 0,5 MB über
der Wheel-Summe aus, auf arm64 ist mit derselben Größenordnung zu rechnen.

Die x265-Version im Image ist per `pillow_heif.libheif_info()` belegt:
`x265 HEVC encoder (4.2+1-e444744)`, genau der Stand, den `x265Version.txt` im
Quellpaket `x265_4.2.tar.gz` nennt (`releasetag: 4.2`,
`repositorychangeset: e444744`, `releasetagdistance: 1`).

### Bewertung

Die Research erwartete rund 16 MB entpackt, davon libx265 11,4 MB; das trifft
arm64 genau (15,92 MB, libx265 11,43 MB), auf amd64 ist die x265-Bibliothek mit
22,79 MB doppelt so groß, sodass dort 27,27 MB entpackt und 6,18 MB komprimiert
hinzukommen (arm64 7,29 MB komprimiert), ein Zuwachs von rund 2 Prozent des
Downloads auf beiden Architekturen.
