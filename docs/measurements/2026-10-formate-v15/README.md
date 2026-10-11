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

---

## HEIC-Dekodier-RAM

**Frage (D-31-06, Annahmen A5 und A6 der Phase-Research):** Wie viel Adressraum
und wie viel residenten Speicher kostet das Dekodieren eines HEIC-Fotos mit 12,
24 und 48 Megapixeln auf amd64 und arm64, passt es unter den Standard-Adressraum
des Extraktionskinds (`FINDLING_EXTRACT_ADDRESS_SPACE_BYTES`, 512 MiB), und
welcher Faktor gehört in die Schätzung von `extract/image.py`?

**Datum:** 11.10.2026, 07:38 UTC.

**Lauf:** `docker.yml` Lauf **38121953472** (Commit `44cf3fc7`, HEIF-Faktor 3
vorläufig), Schritt "HEIC OCR and decode memory in the image (FMT-05)" auf
`ubuntu-24.04` (amd64) und `ubuntu-24.04-arm` (arm64), beide grün. Image-Index
`sha256:cb3576e45fd5bd453ee5bfe42770756f1e305f22f33c0f53b1f694551dc779ff`,
amd64 `sha256:ca62763c0cd4cd1632d5cbe02e754f204d44c2a68823871b1a7066506780cffd`,
arm64 `sha256:0a7a599db2be8bf4f00fe9cd520e467010a0ccd37b283a6cd9e696a29e71ec57`.

### Verfahren

Die Probe `backend/tests/probe_image_ocr_heic.py` läuft im gebauten Image ohne
Netz. Sie erzeugt alle Bilder zur Laufzeit: eine weiße RGB-Fläche mit einem
selbst geschriebenen Satz in DejaVu Sans (`testdata/fonts`), als HEIC über den
Encoder im pillow-heif-Wheel (x265, Qualität 80, Raster aus 512-Pixel-Kacheln
wie bei Apple-Geräten) und als JPEG derselben Fläche (Qualität 85) zur
Gegenmessung. Größen: 4032 x 3024 (12 MP), 5712 x 4284 (24 MP), 8064 x 6048
(48 MP, "HEIF Max"). Jede Datei wird in frischen Kindprozessen gelesen, je drei
Mal, ausgewiesen ist der Median (Einzelwerte gibt die Probe nicht aus).

- **Laden ohne Deckel:** Das Kind importiert den Bildpfad (damit ist der Opener
  registriert), liest `VmSize` und `VmRSS` aus `/proc/self/status`, ruft
  `Image.open(path).load()` ohne Draft und liest danach `VmPeak` und `VmHWM`.
  VmPeak-Zuwachs = VmPeak danach minus VmSize davor, also der zusätzliche
  Adressraum, den `RLIMIT_AS` zählt; VmHWM-Zuwachs = VmHWM danach minus VmRSS
  davor, die residente Seite.
- **Laden unter dem Deckel:** dasselbe in einem Kind mit `RLIMIT_AS` gleich dem
  Standard (512 MiB) und ohne die Schätzung davor. Es beantwortet, ob die
  Dekodierung unter dem Deckel überhaupt gelingt.
- **Voller Pfad unter dem Deckel:** `extract_image` wie im Extraktionskind
  (`RLIMIT_AS` gesetzt, native Thread-Pools auf 1), mit Urteil, Restgröße und
  Schätzung.

### Messwerte

| Architektur | MP | Format | VmPeak-Zuwachs Laden | VmHWM-Zuwachs Laden | unter 512 MiB geladen | VmPeak-Zuwachs voller Pfad | VmHWM-Zuwachs voller Pfad | Restgröße | Schätzung (Faktor 3) | Urteil |
|---|---|---|---|---|---|---|---|---|---|---|
| amd64 | 12 | HEIF | 241,4 MiB | 84,2 MiB | ja (241,4) | 282,0 MiB | 124,6 MiB | 439,3 MiB | 139,5 MiB | indexed |
| amd64 | 12 | JPEG | 46,5 MiB | 47,1 MiB | ja (46,5) | 30,5 MiB | 31,0 MiB | 439,3 MiB | 23,3 MiB | indexed |
| amd64 | 24 | HEIF | 323,4 MiB | 165,9 MiB | ja (323,4) | 345,6 MiB | 188,3 MiB | 439,3 MiB | 280,0 MiB | indexed |
| amd64 | 24 | JPEG | 93,4 MiB | 93,9 MiB | ja (93,4) | 46,4 MiB | 46,8 MiB | 439,3 MiB | 46,7 MiB | indexed |
| amd64 | 48 | HEIF | 485,6 MiB | 327,9 MiB | ja, knapp (427,5) | 0,4 MiB | 0,7 MiB | 439,3 MiB | 558,1 MiB | **skipped(too_large)** |
| amd64 | 48 | JPEG | 186,1 MiB | 186,7 MiB | ja (186,1) | 30,5 MiB | 31,0 MiB | 439,3 MiB | 23,3 MiB | indexed |
| arm64 | 12 | HEIF | 241,5 MiB | 83,8 MiB | ja (241,5) | 282,1 MiB | 124,1 MiB | 446,6 MiB | 139,5 MiB | indexed |
| arm64 | 12 | JPEG | 46,5 MiB | 47,0 MiB | ja (46,5) | 30,5 MiB | 30,8 MiB | 446,6 MiB | 23,3 MiB | indexed |
| arm64 | 24 | HEIF | 323,5 MiB | 165,5 MiB | ja (323,5) | 346,0 MiB | 187,9 MiB | 446,6 MiB | 280,0 MiB | indexed |
| arm64 | 24 | JPEG | 93,4 MiB | 93,8 MiB | ja (93,4) | 46,4 MiB | 46,7 MiB | 446,6 MiB | 46,7 MiB | indexed |
| arm64 | 48 | HEIF | 485,8 MiB | 327,9 MiB | ja, knapp (443,7) | 0,4 MiB | 0,7 MiB | 446,6 MiB | 558,1 MiB | **skipped(too_large)** |
| arm64 | 48 | JPEG | 186,1 MiB | 186,5 MiB | ja (186,1) | 30,5 MiB | 30,8 MiB | 446,6 MiB | 23,3 MiB | indexed |

"Voller Pfad" beim 48-MP-HEIF misst nur das Öffnen des Kopfes: die Schätzung
lehnt das Bild ab, bevor eine Zeile dekodiert ist. Beim JPEG ist der volle Pfad
billiger als das Laden, weil der Draft von libjpeg das Bild vor dem Dekodieren
verkleinert (D-29-07); HEIF hat keinen solchen Draft. Der OCR-Treffer
(`fotoquendel`) kam in jedem Lauf mit Urteil indexed, auf beiden Architekturen.

Thread-Vergleich (24-MP-HEIC, Laden ohne Deckel, Zeilen `heic-threads`):

| Architektur | decode_threads | VmPeak-Zuwachs | VmHWM-Zuwachs |
|---|---|---|---|
| amd64 | 1 (registriert) | 323,4 MiB | 165,9 MiB |
| amd64 | 4 (Bibliotheksstandard) | 707,4 MiB | 167,0 MiB |
| arm64 | 1 (registriert) | 323,5 MiB | 165,5 MiB |
| arm64 | 4 (Bibliotheksstandard) | 707,5 MiB | 166,7 MiB |

### Auswertung

- **Die Architekturen sind gleich.** Alle Zuwächse liegen auf amd64 und arm64
  innerhalb von 0,4 MiB beieinander; nur die Restgröße unterscheidet sich, weil
  das Kind auf arm64 mit 65,4 MiB Adressraum startet und auf amd64 mit 72,7 MiB.
- **Der Bedarf ist fest plus linear, nicht proportional.** Die drei HEIF-Werte
  liegen genau auf einer Geraden: rund 160 MiB fest plus 7,0 Byte je Pixel
  (12 MP: 160 + 81 = 241; 24 MP: 160 + 163 = 323; 48 MP: 160 + 326 = 486). Der
  JPEG-Vergleich trifft Pillows eigene 4 Byte je Pixel genau, ohne festen
  Anteil. Bezogen auf das JPEG gleicher Größe braucht HEIF beim Laden das 5,2-,
  3,5- und 2,6-Fache (12, 24, 48 MP); je Pixel 20,8, 13,9 und 10,4 Byte.
- **Woher der feste Anteil kommt.** Jeder weitere Decoder-Thread kostet 128 MiB
  Adressraum (vier Threads: 707 statt 323 MiB, also 384 MiB für drei Threads
  mehr), resident aber fast nichts (167 statt 166 MiB). Das passt zu einer
  eigenen malloc-Arena je Thread, die glibc als Adressraum reserviert, ohne sie
  zu belegen. Ein Thread bleibt auch mit `decode_threads=1`, daher die rund
  160 MiB. Das ist eine Erklärung aus den Zahlen, nicht einzeln nachgewiesen.
- **Unter dem Deckel wird es knapper als ohne.** Beim 48-MP-HEIF lag der Zuwachs
  unter dem Deckel mit 427,5 (amd64) und 443,7 MiB (arm64) unter dem Wert ohne
  Deckel (485,6/485,8 MiB): wenn eine Reservierung scheitert, weicht malloc aus.
  Das Laden gelang, mit 11,8 und 2,9 MiB Luft. Danach bräuchte der volle Pfad
  noch die verkleinerte Arbeitskopie für die OCR (beim 12- und 24-MP-HEIF 22 bis
  41 MiB über dem Laden); die passt in diese Luft nicht.

**A5 (decode_threads=1 spart Adressraum unter RLIMIT_AS): bestätigt.** Mit dem
Bibliotheksstandard von vier Threads bräuchte schon das 24-MP-HEIC 707 MiB
Adressraum, mehr als der ganze Deckel von 512 MiB; mit einem Thread sind es
323 MiB. Resident ändert sich nichts.

**A6 (HEIC braucht einen höheren Faktor als JPEG): bestätigt, aber das
Faktormodell passt nicht.** Die Regel des Plans (kleinster ganz- oder
halbzahliger Faktor, mit dem `Breite x Höhe x 4 x Faktor` auf beiden
Architekturen über dem gemessenen VmPeak-Zuwachs liegt) ergäbe 5,5, getrieben
vom festen Anteil beim 12-MP-Bild. Mit 5,5 schätzte der Pfad ein 24-MP-HEIC auf
513,4 MiB und lehnte es als too_large ab, obwohl es unter dem Deckel dekodiert
und gelesen wird (Urteil indexed in jedem Lauf). Der vorläufige Faktor 3
unterschätzt den Bedarf kleiner Bilder (12 MP: 139,5 geschätzt gegen 282,0
gebraucht), was dort nichts kostet, weil der Bedarf weit unter der Restgröße
liegt; zwischen rund 36 und 38 MP schätzt er aber "passt", während der volle
Pfad nach der Geraden über 440 MiB bräuchte. Faktor und Modell sind deshalb
nicht in diesem Lauf festgelegt, sondern Teil der Owner-Entscheidung zu
Plan 31-07 (Checkpoint, siehe unten).

### 48 MP unter dem Standard-Adressraum

Ein 48-MP-HEIF ("HEIF Max") endet unter dem Standard-Adressraum von 512 MiB auf
beiden Architekturen als `skipped(too_large)`. Das ist das Urteil der Schätzung
(558,1 MiB gegen 439,3 bzw. 446,6 MiB Restgröße), und die Messung unter dem
Deckel gibt ihr recht: das Laden allein passt mit 2,9 MiB Luft (arm64), der
volle Pfad nicht. Damit ist der Checkpoint von Plan 31-07 ausgelöst; der
Standard-Adressraum bleibt unverändert, bis der Owner entschieden hat.
