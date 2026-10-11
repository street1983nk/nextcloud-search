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
  41 MiB über dem Laden); die passt in diese Luft nicht. (Widerlegt im
  Folgelauf, siehe "Korrektur" unten: Der volle Pfad passte mit 2,6 bis
  11,5 MiB Rest.)

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
Plan 31-07 (Checkpoint, siehe unten; das Messmodell steht im Abschnitt
"Eine malloc-Arena im Extraktionskind").

### 48 MP unter dem Standard-Adressraum

Ein 48-MP-HEIF ("HEIF Max") endete in diesem Lauf unter dem Standard-Adressraum
von 512 MiB auf beiden Architekturen als `skipped(too_large)`. Das war das
Urteil der Schätzung (558,1 MiB gegen 439,3 bzw. 446,6 MiB Restgröße); das
Laden allein passte unter dem Deckel mit 2,9 MiB Luft (arm64). Damit war der
Checkpoint von Plan 31-07 ausgelöst.

Korrektur aus dem Folgelauf 38124726627: Hier stand, der volle Pfad passe nicht
in diese Luft. Gemessen (Schätzung abgeschaltet) passte er doch, mit einer
Spitze von 500,5 MiB (amd64) und 509,4 MiB (arm64) von 512 MiB, also 11,5 und
2,6 MiB Rest. Ein Urteil "passt" mit so wenig Rest wäre trotzdem keines, auf
das man sich verlassen kann. Wie es weiterging, steht im folgenden Abschnitt.

---

## Eine malloc-Arena im Extraktionskind (Owner-Entscheid zu Plan 31-07)

**Entscheid des Owners am Checkpoint (11.10.2026):** Erst messen, ob
`MALLOC_ARENA_MAX` den festen Anteil des HEIF-Bedarfs senkt (unset, 1, 2, beide
Architekturen, 12/24/48 MP, Median aus drei Läufen, dazu die Wirkung auf den
übrigen Text- und OCR-Weg des Kinds). Passt ein 48-MP-HEIF mit einem Wert sicher
unter 512 MiB (mindestens 10 Prozent Rest) ohne messbaren Nachteil, wird der
Wert gezielt für das Extraktionskind gesetzt (Fall A); sonst bleibt es bei
too_large und einem Satz in docs/formats.md (Fall B). Das Limit bleibt in beiden
Fällen bei 512 MiB. Die Schätzung wird ein Messmodell statt eines Faktors.

**Ergebnis: Fall A, `MALLOC_ARENA_MAX` = 1.**

### Messung der drei Werte

Lauf **38124726627** (Commit `ff610f10`), Teil 3 der Probe: jedes Kind bekam
`MALLOC_ARENA_MAX` über die Umgebung. "Laden" wie oben (ohne Deckel),
"voller Pfad" ist `extract_image` unter dem Deckel von 512 MiB mit
abgeschalteter Schätzung; ausgewiesen ist die absolute VmPeak-Spitze des Kinds,
denn sie ist es, die an `RLIMIT_AS` stößt. 90 Prozent des Deckels sind
460,8 MiB. Alle Werte in MiB.

| Architektur | MALLOC_ARENA_MAX | MP | VmPeak-Zuwachs Laden | VmPeak-Spitze voller Pfad | Rest zu 512 MiB bei 48 MP | Urteil | Sekunden |
|---|---|---|---|---|---|---|---|
| amd64 | unset | 12 / 24 / 48 | 241,4 / 323,4 / 485,6 | 354,9 / 418,6 / 500,5 | 11,5 (2,2 %) | indexed | 0,76 / 0,97 / 1,33 |
| amd64 | 1 | 12 / 24 / 48 | 113,4 / 195,4 / 357,6 | 226,9 / 290,6 / 430,6 | 81,4 (15,9 %) | indexed | 0,76 / 0,97 / 1,32 |
| amd64 | 2 | 12 / 24 / 48 | 177,4 / 259,4 / 421,6 | 290,9 / 354,6 / 494,6 | 17,4 (3,4 %) | indexed | 0,76 / 0,97 / 1,32 |
| arm64 | unset | 12 / 24 / 48 | 241,5 / 323,5 / 485,8 | 347,8 / 411,7 / 509,4 | 2,6 (0,5 %) | indexed | 0,65 / 0,84 / 1,18 |
| arm64 | 1 | 12 / 24 / 48 | 113,5 / 195,5 / 357,8 | 219,8 / 283,7 / 423,4 | 88,6 (17,3 %) | indexed | 0,66 / 0,85 / 1,19 |
| arm64 | 2 | 12 / 24 / 48 | 177,5 / 259,5 / 421,8 | 283,8 / 347,7 / 487,4 | 24,6 (4,8 %) | indexed | 0,67 / 0,86 / 1,19 |

Die residente Seite (VmHWM des vollen Pfads, 158 bis 363 MiB je nach Größe)
unterscheidet sich zwischen den drei Werten um höchstens 1,5 MiB. Jede
zusätzliche Arena kostet 64 MiB Adressraum (unset gegen 2 gegen 1: 128 und
64 MiB mehr) und belegt davon fast nichts.

Der übrige Weg des Kinds, dieselben Kinder über `dispatch.extract`, Median aus
drei Läufen:

| Architektur | Datei (Weg) | VmPeak | VmHWM | Sekunden | Urteil |
|---|---|---|---|---|---|
| amd64 | 01-text-layer.pdf (Text-PDF) | 88,7 | 47,7 bis 47,8 | 0,12 | indexed |
| amd64 | 10-kuendigung.docx (Office, mit numpy) | 171,9 bis 172,3 | 67,1 bis 67,3 | 0,33 | indexed |
| amd64 | 13-ratsvorlage-scan.pdf (OCR-Route, Tesseract) | 99,9 | 62,5 bis 62,6 | 2,78 | indexed |
| amd64 | 17-beleg.jpg (Bild-OCR) | 73,4 | 36,1 bis 36,4 | 0,37 | indexed |
| arm64 | 01-text-layer.pdf | 81,6 | 46,7 | 0,10 | indexed |
| arm64 | 10-kuendigung.docx | 157,6 bis 157,7 | 66,8 | 0,28 bis 0,31 | indexed |
| arm64 | 13-ratsvorlage-scan.pdf | 92,9 | 61,8 | 2,66 bis 2,67 | indexed |
| arm64 | 17-beleg.jpg | 66,2 | 35,1 | 0,33 | indexed |

Die Spannen sind die Werte für unset, 1 und 2; wo nur eine Zahl steht, waren
alle drei gleich. Kein messbarer Nachteil: Das Kind arbeitet in einem Thread
(die nativen Thread-Pools sind seit Plan 06.1-19 auf 1 gepinnt), und der
Tesseract-Enkel ist ein eigener Prozess. Mehrere Arenen braucht im Kind
niemand. Im Hauptprozess dagegen laufen Suche, Einbettung (onnxruntime) und
Server mit eigenen Threads, und dort ist nichts gemessen.

### Umsetzung

`extract/sandbox.py`, `_limit_malloc_arenas`: `mallopt(M_ARENA_MAX, 1)` über
ctypes im Kind, direkt nach `RLIMIT_AS` und vor dem ersten Import der Parser,
nicht über die Umgebung. So bleiben der Hauptprozess und der Tesseract-Enkel
unberührt. Abseits von Linux und mit einer C-Bibliothek ohne `mallopt` passiert
nichts. Ein Test im Linux-Lauf startet ein Kind mit einem Thread, der über
malloc anlegt, und verlangt ohne Grenze mindestens 64 MiB Adressraumzuwachs,
mit Grenze unter 32 MiB (lokal im Image gemessen: 72 gegen 8 MiB).

Gegenprobe im gebauten Image, Lauf **38125992894** (Commit `c64bdf04`, Index
`sha256:d4feb56ab220934834565f9980824738f988826a5db8d0d5352519535bb428f5`,
amd64 `sha256:f40bef8f4e155f29f20e272b77cdcc69551d1ff46e5efc3bb839887779d2cbb7`,
arm64 `sha256:4b98d18664af198e2f6b4f95280209a1ab9b364845b42c002f982106cc75f634`):
Die Probe ruft dieselbe Funktion in jedem Kind, und die Werte mit `mallopt`
gleichen denen mit `MALLOC_ARENA_MAX=1` auf 0,1 MiB.

| Architektur | MP | VmPeak-Zuwachs Laden | VmPeak-Zuwachs voller Pfad | Restgröße | Schätzung (Modell) | Spitze absolut | Rest zu 512 MiB | Urteil |
|---|---|---|---|---|---|---|---|---|
| amd64 | 12 | 113,4 | 154,0 | 437,9 | 161,4 | 228,1 | 283,9 | indexed |
| amd64 | 24 | 195,4 | 217,6 | 437,9 | 243,4 | 291,7 | 220,3 | indexed |
| amd64 | 48 | 357,6 | 357,6 | 437,9 | 405,6 | 431,7 | 80,3 (15,7 %) | **indexed** |
| arm64 | 12 | 113,5 | 154,1 | 445,0 | 161,4 | 221,1 | 290,9 | indexed |
| arm64 | 24 | 195,5 | 218,0 | 445,0 | 243,4 | 285,0 | 227,0 | indexed |
| arm64 | 48 | 357,8 | 357,8 | 445,0 | 405,6 | 424,8 | 87,2 (17,0 %) | **indexed** |

Das Kind startet hier mit 74,1 (amd64) und 67,0 MiB (arm64), 1,1 und 1,3 MiB
mehr als im Sweep, weil die Probe jetzt `sandbox` importiert. Der OCR-Treffer
`fotoquendel` kam in jedem Lauf.

**A5 neu bewertet:** Mit einer Arena kosten vier Decoder-Threads genauso viel
Adressraum wie einer (24 MP: 195,4 gegen 195,4 MiB). Der Unterschied, den A5
gemessen hatte, waren die Arenen der zusätzlichen Threads. `decode_threads=1`
bleibt trotzdem: Es kostet nichts und hält die CPU-Last eines Kinds bei einem
Kern, wie bei Tesseract.

### Das Messmodell der Schätzung

Statt `Breite x Höhe x 4 x Faktor` schätzt `extract/image.py` ein HEIF als
**80 MiB fest plus 7 Byte je Pixel** (RGB; 9 Byte für andere Modi, siehe unten).
Herleitung aus den Werten mit einer Arena:

- Das Laden liegt genau auf einer Geraden: 32,0 MiB plus 7,00 Byte je Pixel
  (12 MP: 32,0 + 81,4 = 113,4; 24 MP: 32,0 + 163,4 = 195,4; 48 MP: 32,0 + 325,6 =
  357,6).
- Bei 12 und 24 MP liegt der volle Pfad darüber, weil nach dem Laden die
  verkleinerte Arbeitskopie für die OCR entsteht (höchstens 3500 x 2625 Pixel,
  4 Byte Farbe und 1 Byte Grau). Der größte Abstand zur Ladegeraden ist
  72,6 MiB (12 MP: 154,0 minus 81,4).
- Die Steigung wird übernommen, der feste Anteil auf 80 MiB über diese 72,6 MiB
  gesetzt. Damit liegt das Modell über jedem gemessenen Wert und über der
  Schranke "Ladegerade plus 5 Byte je Pixel der verkleinerten Kopie" bei jeder
  Größe bis zur Pixelgrenze von 50 MP. Es gibt keine Größe, bei der die
  Schätzung "passt" sagt und der Pfad nicht passt; die Lücke des Faktors 3
  zwischen 36 und 38 MP ist geschlossen.
- 12, 24 und 48 MP passen in ein frisches Kind (Schätzung 161,4 / 243,4 /
  405,6 MiB gegen 437,9 bzw. 445,0 MiB Restgröße). Bei 50 MP (Pixelgrenze)
  schätzt das Modell 413,8 MiB, also passt jedes HEIF, das die Pixelgrenze
  durchlässt, in ein frisches Kind. Ein Kind, das schon viele Dateien gelesen hat
  und dessen Adressraum gewachsen ist, urteilt ehrlich `skipped(too_large)`.
- Ein HEIF mit Alpha dekodiert eine vierte Ebene und einen Puffer mit 4 statt
  3 Byte; das sind nach derselben Rechnung 2 Byte je Pixel mehr. Nicht gemessen,
  deshalb als obere Schranke für jeden Modus außer RGB.

Die Tests in `backend/tests/test_image_heic.py` halten das fest (Modell über
jedem Messwert, 12/24/48 MP passen in ein frisches Kind beider Architekturen,
keine Lücke bis 50 MP, das Urteil kippt genau an der Schätzung) und werden mit
Faktor 3, Faktor 5,5, 40 MiB fest oder 6 Byte je Pixel rot.

**Offen für das Audit 31-15:** Ein JPEG über der Schätzung endet weiter als
`failed(out_of_memory)` (D-29-07), ein HEIF als `skipped(too_large)`. Ob beide
Formate dasselbe Urteil bekommen sollen, ist dort zu entscheiden.

---

## ZIP-Grenzwerte

Plan 31-08 (FMT-02, D-31-07). Die Startwerte des Owners waren 10 000
Einträge, 256 MiB entpackt, Rate 100 zu 1 ab 1 MiB, Tiefe 2 und kein OCR in
ZIP-Dateien, mit dem Auftrag, sie zu messen und begründet festzulegen.

Alle Messungen am 11.10.2026 auf dem Entwicklungsrechner (Windows 11, Intel
Core i5-1335U, 16 GB RAM, CPython 3.13.13 über uv), jede Lesung in einem
frischen Interpreter, drei Wiederholungen, angegeben ist der Median (die
Werte von tracemalloc waren in allen drei Läufen gleich). Die Skripte lagen im
Scratch-Verzeichnis der Sitzung und sind nicht Teil des Repos; ihr Verfahren
steht je Abschnitt.

### 1. Zentralverzeichnis

Verfahren: ZIP-Dateien mit N leeren Einträgen (`zipfile`, Namen
`d/000000.txt`), dazu Dateien, die nur aus einem Zentralverzeichnis und dem
Endsatz bestehen (die Form einer Speicherbombe, ohne lokale Kopfzeilen), mit
10 000 bzw. 100 000 Köpfen und Namen von 100, 792, 1600 und 4096 Byte.
Gemessen wurde die Spitze von tracemalloc und die Zeit um
`len(ZipFile(path).infolist())`, danach dieselben Dateien mit der eigenen
Zählung `count_central_directory`.

| Datei | Länge des Verzeichnisses | ZipFile Spitze | ZipFile Zeit | eigene Zählung Spitze | eigene Zählung Zeit |
|---|---|---|---|---|---|
| 1 000 leere Einträge | 0,06 MB | 0,59 MiB | 0,034 s | | |
| 10 000 leere Einträge | 0,6 MB | 5,47 MiB | 0,338 s | 0,064 MiB | 0,055 s |
| 50 000 leere Einträge | 2,9 MB | 28,01 MiB | 1,615 s | | |
| 100 000 leere Einträge | 5,8 MB | 55,88 MiB | 3,232 s | 0,064 MiB | 0,555 s |
| nur Verzeichnis, 10 000 x 100 Byte | 1,46 MB | 6,27 MiB | 0,256 s | | |
| nur Verzeichnis, 100 000 x 100 Byte | 14,6 MB | 63,89 MiB | 2,383 s | | |
| nur Verzeichnis, 10 000 x 792 Byte (beide Grenzen) | 8,38 MB (7,99 MiB) | 19,47 MiB | 0,290 s | 0,064 MiB | 0,091 s |
| nur Verzeichnis, 10 000 x 1600 Byte | 16,5 MB | 34,88 MiB | 0,296 s | | |
| nur Verzeichnis, 10 000 x 4096 Byte | 41,4 MB | 82,49 MiB | 0,349 s | abgelehnt vor dem Lesen | |

Auswertung: Die Spitze von `ZipFile` folgt etwa 2 x Länge des Verzeichnisses
plus 0,55 KiB je Kopf (das Verzeichnis wird am Stück gelesen, die Namen
dekodiert behalten). Die eigene Zählung liest in Blöcken von 64 KiB und bleibt
bei 64 KiB, unabhängig von Zahl und Länge. Mit beiden Grenzen zugleich
(10 000 Köpfe, 8 MiB) kostet `ZipFile` 19,5 MiB: unter 4 Prozent der 512 MiB
Adressraum des Extraktionskinds. Ohne die Längengrenze hätten 10 000 Köpfe mit
Namen von 4 KiB 82,5 MiB gekostet, bei 50 MiB Dateigröße wären es über 100 MiB.

### 2. Kompressionsrate realer Dateien

Verfahren: jede Datei mit `zipfile.ZIP_DEFLATED` und Stufe 9 gepackt, Rate =
entpackte Größe / gepackte Größe. Zehn echte Dateien ab 1 MB, die als
redundant gelten (Exporte, Logs, Markup); dazu Nullbytes als Obergrenze von
Deflate (A4).

| Datei | Größe | Rate |
|---|---|---|
| CSV, Messprotokoll aus dem Repo | 1,06 MB | 3,9 : 1 |
| CSV, Export des Lastkorpus | 56,0 MB | 5,4 : 1 |
| JSON, Tokenizer des Modells | 17,1 MB | 4,4 : 1 |
| TXT, Wortliste | 3,3 MB | 4,7 : 1 |
| SQL-Dump | 2,0 MB | 3,6 : 1 |
| Log einer IDE | 5,6 MB | 12,2 : 1 |
| Log einer Desktop-App | 5,6 MB | 17,9 : 1 |
| XML, Regeldatei von Office | 1,07 MB | 11,9 : 1 |
| HTML, Office-Cache | 2,7 MB | 3,1 : 1 |
| DOCX, Vorlage (schon gepackt) | 2,3 MB | 1,1 : 1 |
| Nullbytes, 1 MiB | 1 MiB | 1015,1 : 1 |
| Nullbytes, 50 MiB | 50 MiB | 1028,6 : 1 |

A4 bestätigt: Deflate endet bei rund 1030 zu 1 (gemessen 1028,6). Die
redundanteste reale Datei (ein Log) liegt bei 17,9 zu 1, also über dem Faktor
5 unter der Grenze von 100 zu 1. Eine Anhebung ist nicht nötig.

### 3. Zeit je Mitglied

Verfahren: eine ZIP-Datei mit 200 kleinen Mitgliedern (je ein Drittel DOCX
mit einem Absatz, eine Seite PDF mit Textschicht, TXT mit 2 KB), gelesen mit
`extract_zip` in einem frischen Interpreter, also mit den Importen der Leser.

| Lauf | Zeit | je Mitglied |
|---|---|---|
| 1 | 2,76 s | 13,8 ms |
| 2 | 2,34 s | 11,7 ms |
| 3 | 2,30 s | 11,5 ms |

Median 2,34 s, 11,7 ms je Mitglied. 1 000 Mitglieder mit Text brauchen damit
rund 12 s von den 90 s, die 75 Prozent der Frist von 120 s erlauben. Auf einer
langsameren Box hält zuerst der Zeitanteil an und das Ergebnis heißt
`indexed(truncated)`, nicht der Kill. Der Deckel bleibt bei 1 000.

### 4. Codepage der Namen (A3)

Verfahren: ä, ö, ü, Ä, Ö, Ü, ß in cp437 und cp850 kodiert und verglichen.
Ergebnis: in beiden Codepages dieselben Bytes (0x84, 0x94, 0x81, 0x8E, 0x99,
0x9A, 0xE1), und `zipfile` dekodiert sie ohne UTF-8-Flag als cp437 richtig.
A3 bestätigt; der Test mit einem Namen "Größe.txt" ohne Flag liest ihn richtig.

### 5. Offsets von Endsatz, ZIP64 und Kopf (A10)

Gegen PKWARE APPNOTE 6.3.10 (Abschnitte 4.3.12 bis 4.3.16) und gegen die
gelesene Quelle von CPython 3.13.13 (`Lib/zipfile/__init__.py`):

- Endsatz (4.3.16): 22 Byte fest, Eintragszahl gesamt bei +10, Länge des
  Verzeichnisses bei +12, Offset bei +16, Kommentarlänge bei +20; bestätigt.
- ZIP64-Locator (4.3.15): 20 Byte, direkt vor dem Endsatz; bestätigt.
- ZIP64-Endsatz (4.3.14): 56 Byte fest, Länge bei +40, Offset bei +48;
  bestätigt.
- Kopf im Verzeichnis (4.3.12): 46 Byte fest, Namenslänge bei +28, Extra bei
  +30, Kommentar bei +32; bestätigt.
- CPython: `_EndRecData64` Zeilen 252 bis 309, `_EndRecData` 312 bis 369,
  `_RealGetContents` 1460 bis 1540 (concat 1475 und 1476, Beginn des
  Verzeichnisses 1482, Schleife `while total < size_cd` ab 1489). Die
  Eintragszahl des Endsatzes kommt in der Schleife nicht vor.

Ein Befund über A10 hinaus: `_EndRecData64` liest den Locator **immer**, nicht
nur wenn Felder des Endsatzes 0xFFFF tragen. Ein Locator vor einem gewöhnlichen
Endsatz ersetzt dessen Länge und Offset. Die eigene Vorprüfung bildet das
genau so ab; ein Test mit einem ZIP64-Endsatz hinter vorangestellten Bytes
belegt den Weg über `concat`.

### Festgelegte Werte

Die Grenzen gelten für die ZIP-Datei als Ganzes: Einträge, Verzeichnisbytes,
deklarierte und gelesene Bytes und Mitglieder mit Text kommen aus einem
gemeinsamen Budget, das an jede innere Ebene weitergereicht wird (Befund 10).
Die Zahl der Einträge bestimmt die eigene Zählung der Köpfe vor `ZipFile`,
nie das Feld im Endsatz, weil `zipfile` das Verzeichnis über seine Bytelänge
liest (Blocker 2).

| Grenze | Startwert D-31-07 | gemessene Grundlage | festgelegt | Begründung |
|---|---|---|---|---|
| Einträge (`ARCHIVE_MAX_ENTRIES`) | 10 000 | 5,5 MiB und 0,34 s bei 10 000, 55,9 MiB und 3,2 s bei 100 000 | 10 000 | weit über einer gepackten Dokumentenmappe, zwei Größenordnungen unter dem Adressraum |
| Länge des Verzeichnisses (`ARCHIVE_MAX_CENTRAL_DIRECTORY_BYTES`) | keiner | Spitze 2 x Länge plus 0,55 KiB je Kopf, an beiden Grenzen 19,5 MiB | 8 MiB | 838 Byte je Kopf bei 10 000 Köpfen, ein realer Kopf braucht 100 bis 300 |
| Entpackt gesamt (`EXTRACT_ARCHIVE_TOTAL_MAX_BYTES`) | 256 MiB | vorhandene Konstante, Begründung in config.py | 256 MiB | halber Adressraum, fünffache Dateigröße; gilt für deklarierte und gelesene Bytes |
| Rate (`ARCHIVE_MAX_RATIO`, `ARCHIVE_RATIO_MIN_BYTES`) | 100 : 1 ab 1 MiB | reale Dateien bis 17,9 : 1, Deflate bis 1028,6 : 1 | 100 : 1 ab 1 MiB | fünffacher Abstand zur redundantesten realen Datei, ein Zehntel der Obergrenze |
| Tiefe (`ARCHIVE_MAX_DEPTH`) | 2 | Quine mit 720 Byte endet benannt nach zwei Öffnungen | 2 | eine innere ZIP-Datei wird gelesen, eine darin beendet die ganze Datei |
| Mitglieder mit Text (`ARCHIVE_MAX_TEXT_MEMBERS`) | 1 000 | 11,7 ms je Mitglied, 1 000 in rund 12 s | 1 000 | passt mit Abstand in den Zeitanteil |
| Zeitanteil (`ARCHIVE_TIME_SHARE`) | 75 % von 120 s | wie oben | 0,75 | ein großes Paket endet als `indexed(truncated)` statt durch den Kill |
| Einzelmitglied | über `max_file_bytes` übergehen | gleiche Grenze wie für Einzeldateien | 50 MiB | das Mitglied bleibt Name, die Datei läuft weiter |
| OCR | keins | eine Tesseract-Seite kostet 300 bis 600 MB und Sekunden | keins | Bilder bleiben Namen, ein PDF zählt nur mit Textschicht |

Abweichungen vom Startwert: keine. Neu gegenüber D-31-07 ist allein die
Längengrenze des Verzeichnisses (Blocker 2 der Planprüfung).
