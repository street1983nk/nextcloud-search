---
phase: 03-aktualit-t-und-ocr
plan: 06
subsystem: ocr-korpus-und-textlayer-schwelle
tags: [ocr, korpus, dach, pdf, messung, testdaten, schrift]
requires:
  - "scripts/dev/build_corpus.py (Regel: ein Suchbegriff, eine Datei)"
  - "backend/src/findling/extract/pdf.py (_MIN_CHARS_PER_PAGE als Annahme A2)"
  - "backend/Dockerfile (gepinnter Basis-Image-Digest, Quelle der Schrift)"
  - "pillow 12.3.0 aus Plan 03-05"
provides:
  - "33 Korpusdateien: gescannte deutsche Verwaltungsprosa, CH- und AT-Schreibweise, JPG/PNG/TIFF/mehrseitiges TIFF/WebP, Icon, EXIF-gedrehtes Foto, zwölf defekte PDFs"
  - "reproduzierbarer Korpusbau mit gepinnter, per SHA-256 geprüfter Schrift"
  - "gemessene Textlayer-Schwelle plus Anteilsregel je Seite statt Dokumentdurchschnitt"
  - "docs/ocr.md: Abschnitt Die Textlayer-Erkennung mit Messtabelle und Kommandozeile"
  - "dokumentiertes Verdikt je Korpus-PDF, als Test abgesichert"
affects:
  - "scripts/dev/build_corpus.py"
  - "scripts/ci/slow_backend.py"
  - "testdata/CORPUS.md"
  - "testdata/corpus/ (21 neue Dateien)"
  - "testdata/fonts/ (neu)"
  - "backend/src/findling/extract/pdf.py"
  - "backend/tests/test_extract_documents.py"
  - "docs/ocr.md"
  - "THIRD-PARTY.md"
  - ".gitattributes"
  - ".github/workflows/integration.yml"
tech-stack:
  added:
    - "DejaVuSans.ttf aus fonts-dejavu-core 2.37-8, als Datei eingecheckt und per SHA-256 geprüft (kein neues Paket)"
  patterns:
    - "gepinnte Binärabhängigkeit durch Digestprüfung statt durch Versionsnummer"
    - "fail-closed vor dem ersten geschriebenen Byte: Glyphenprobe und Eindeutigkeitsprüfung im Bauskript"
    - "Deckel und Schwellen als benannte Konstante mit Messung im Kommentar"
key-files:
  created:
    - "testdata/fonts/DejaVuSans.ttf"
    - "testdata/fonts/COPYING.dejavu"
    - "testdata/corpus/13-ratsvorlage-scan.pdf bis 33-seitenbaum-zyklus.pdf"
    - ".planning/phases/03-aktualit-t-und-ocr/03-06-SUMMARY.md"
  modified:
    - "scripts/dev/build_corpus.py"
    - "testdata/CORPUS.md"
    - "backend/src/findling/extract/pdf.py"
    - "backend/tests/test_extract_documents.py"
    - "docs/ocr.md"
    - "THIRD-PARTY.md"
    - ".github/workflows/integration.yml"
    - ".gitattributes"
    - "scripts/ci/slow_backend.py"
decisions:
  - "Die Schrift wird nicht im Container gerendert, sondern einmal aus dem gepinnten Basis-Image geholt und eingecheckt: nur so läuft der Korpusbau auf jeder Maschine und liefert trotzdem bitgleiche Pixel"
  - "_MIN_CHARS_PER_PAGE bleibt bei 25, die Zahl ist jetzt gemessen statt angenommen (A2 bestätigt)"
  - "_SCAN_PAGE_SHARE = 2/3, echt größer: 2 von 3 gescannten Seiten werden extrahiert, 3 von 4 nicht"
  - "Beim gemischten PDF werden die Scanseiten in v1 NICHT zusätzlich OCR-t: eine Datei, ein Verdikt"
  - "Scans werden ohne synthetisches Rauschen gerendert: sonst misst der Abnahmetest den Rauschgenerator"
  - "Die erwarteten Verdikte der Integrationsprüfung wurden mit dem echten Dispatcher erzeugt, nicht abgezählt"
metrics:
  duration: "ca. 75 Minuten"
  tasks: 2
  commits: 3
  files-changed: 31
  tests: "501 passed, 1 skipped"
  completed: 2026-09-01
---

# Phase 3 Plan 06: Der DACH-OCR-Korpus und die gemessene Textlayer-Schwelle

21 neue Korpusdateien, an denen sich OCR überhaupt behaupten lässt, ein
Bauskript, das seine eine neue Abhängigkeit begründet und einzäunt, und eine
Textlayer-Entscheidung, die nicht mehr auf einem Dokumentdurchschnitt beruht,
sondern auf zwei an echten Seiten gemessenen Zahlen.

## Was gebaut wurde

### Task 1: der Korpus wächst von 12 auf 33 Dateien

Der Korpus trug bisher 12 Dateien mit zusammen 6,6 KB, davon genau eine ohne
Textlayer: ein 814 Byte großes PDF mit einem 8x8-Pixel-Grauverlauf. Jede Aussage
über OCR wäre daran eine Behauptung gewesen.

Jetzt liegen dort zusätzlich:

| Datei | Wofür sie da ist |
|---|---|
| `13-ratsvorlage-scan.pdf` | drei A4-Seiten deutsche Ratsvorlage, die nur als Pixel existieren |
| `14-pacht-mit-anhang.pdf` | zwei Seiten mit Textlayer, drei gescannte Anlagen dahinter (Pitfall 9, Bug M2) |
| `15-schweiz-baubewilligung.pdf` | Schweizer Schreibweise, "Strasse" und "Bahnhofstrasse" |
| `16-oesterreich-mitteilung.pdf` | österreichische Fassung, "Jänner" |
| `17` bis `21` | JPG, PNG, TIFF, mehrseitiges TIFF und WebP, jeweils mit lesbarem Text |
| `22-icon.png` | 48 x 48 Pixel, muss unterhalb der Plausibilitätsschwelle abgewiesen werden |
| `23-gedreht.jpg` | dieselbe Seite quer fotografiert, EXIF-Orientierung 6 |
| `24` bis `33` | zehn PDFs, zehn verschiedene Fehlerpfade |

Die zehn defekten Dateien sind nicht zehnmal dasselbe: abgeschnittener Trailer,
zerstörte xref-Einträge, 627 Byte mit 100000 deklarierten Seiten, Nullbytes im
Kopf, gültige Struktur ohne Seiten, doppelt komprimierter Stream, reines
Bild-PDF, 14400 x 14400 Punkt Seitenformat, `startxref` ins Leere und ein
Seitenbaum, der sich selbst enthält. Zusammen mit den beiden aus Phase 1 sind es
die zwölf, die Gate B braucht.

**Die Regel, die bricht, und wie sie eingezäunt ist.** Gerenderten Text in einem
Bild kann die Standardbibliothek nicht erzeugen. Der Docstring des Bauskripts
trägt dafür jetzt einen eigenen Absatz: Pillow zeichnet, und Pillow ist seit
Plan 03-05 ohnehin eine gepinnte Laufzeitabhängigkeit. Die Schrift stammt aus
`fonts-dejavu-core` 2.37-8 im gepinnten Basis-Image des Dockerfiles, liegt als
`testdata/fonts/DejaVuSans.ttf` im Repository und wird vor dem ersten Glyphen
gegen ihren SHA-256 geprüft. Der eingebaute Standardschriftschnitt von Pillow
ist ausdrücklich ausgeschlossen, und der Grund steht daneben: Aileron Regular
hat laut Pillow-Doku einen eingeschränkten Zeichensatz und wandert mit der
Pillow-Version, und Umlaute plus ß sind genau das Risiko eines DACH-Korpus.

**Zwei fail-closed-Prüfungen laufen, bevor das erste Byte geschrieben wird.**
Die erste rendert `Strasse Jänner Grundstücksverkehrsgenehmigung` und bricht ab,
wenn ein Zeichen als Ersatzkästchen herauskommt (Vergleich gegen die Bitmap
eines Zeichens aus dem privaten Bereich, U+E000). Die zweite prüft die alte
Docstring-Regel, die bisher nur eine Zusage war: jeder deklarierte Suchbegriff
muss in genau einer Datei stehen. Sie sieht dabei auch das, was ein grep nicht
findet, nämlich ZIP-Mitglieder und den Text, der nur als Pixel existiert.

`testdata/CORPUS.md` nennt jetzt je Datei Zweck, gemessenes Verdikt und den
einen Begriff, der ausschließlich dort steht.

### Task 2: die Schwelle, gemessen statt geschätzt (TDD)

Erst gemessen, dann geändert. Zeichen je Seite über den ganzen Korpus:

| Datei | Gemessen | Was die Seite ist |
|---|---|---|
| `14-pacht-mit-anhang.pdf` | 456, 442, 0, 0, 0 | volle A4-Prosa, dann die Anlagen |
| `09-bescheid.pdf` | 123 | drei kurze Zeilen |
| `01-text-layer.pdf` | 63 | zwei kurze Zeilen |
| `29-doppelt-komprimiert.pdf` | 29 | eine Zeile, die dünnste echte Textseite |
| `31-riesenformat.pdf` | 12 | nur eine Überschrift |
| neun gerenderte Scanseiten | jeweils 0 | Scans |

Die wichtigste Zahl ist die Null: eine gerasterte Seite misst nicht wenig,
sondern exakt nichts. Der Korpus allein ließe deshalb jede Schwelle zwischen 1
und 12 zu, und genau darum ist er nicht der ganze Maßstab. Die 25 bleiben, weil
sie die Frage beantworten, die der Korpus nicht stellt: eine gemessene
Prosazeile ist 38 Zeichen breit, ein aufgestempeltes "Seite 3 von 40" sind 14,
die dünnste echte Textseite hat 29. Annahme A2 überlebt ihre Messung, und der
Kommentar im Code trägt jetzt Datum, Dateinamen und Zahlen statt eines
Vorbehalts.

Neu ist `_SCAN_PAGE_SHARE = 2/3`. Je Seite zu zählen ist nur die halbe Antwort
auf Bug M2; die andere Hälfte ist, dass eine einzelne Seite nichts entscheiden
darf. Zwei gemessene Fälle klammern den Wert ein: die Pachtvereinbarung mit 3
von 5 Seiten unter der Schwelle muss extrahiert werden, ein Deckblatt vor neun
Scans mit 9 von 10 muss in die OCR-Spur. Der Vergleich ist echt größer, also
sind 2 von 3 noch ein Textdokument und 3 von 4 nicht mehr.

Der gemischte Fall indexiert den Text und schickt die Scanseiten in v1 nicht
zusätzlich durch tesseract. Eine Datei hat genau ein Verdikt; ein zweiter
Teil-Job je Datei wäre eine eigene Mechanik mit eigenem Warteschlangeneintrag,
eigenem Versuchszähler und einer eigenen Art, halb fertig zu sein. Das steht als
Begründung an der Stelle im Code, an der jemand es später ändern würde.

## Abweichungen vom Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierendes Problem] Die Schrift wird eingecheckt statt im Image gerendert**

- **Gefunden bei:** Task 1
- **Problem:** Der Plan verlangt Rendering "im selben Basis-Image" und
  gleichzeitig, dass `cd backend && uv run python ../scripts/dev/build_corpus.py`
  auf dem Entwicklungsrechner mit Exit 0 endet. Beides zusammen geht nicht:
  Windows hat kein `fonts-dejavu-core`, und ein Bauskript, das nur in einem
  Container läuft, wäre genau die Verrottung, gegen die der Docstring
  argumentiert.
- **Fix:** Die Schrift wurde einmal aus dem per Digest gepinnten Basis-Image
  gelesen (`fonts-dejavu-core` 2.37-8) und liegt als Datei im Repository. Das
  Skript prüft ihren SHA-256 vor dem ersten Glyphen. Das ist strenger als ein
  apt-Pin: es hängt nicht mehr an einer Paketversion, sondern an 759720 exakten
  Bytes.
- **Dateien:** `testdata/fonts/DejaVuSans.ttf`, `testdata/fonts/COPYING.dejavu`,
  `.gitattributes`, `THIRD-PARTY.md`
- **Commit:** 3f66f69

**2. [Rule 2 - Fehlende kritische Funktionalität] Lizenzpflicht der eingecheckten Schrift**

- **Gefunden bei:** Task 1
- **Problem:** Eine Schriftdatei in einem öffentlichen Repository trägt eine
  Lizenz, auch wenn sie in keinem Release-Artefakt landet. Ohne Eintrag wäre die
  einzige Binärdatei mit fremdem Urheberrecht die einzige ohne Nachweis.
- **Fix:** `debian/copyright` des Pakets liegt als `COPYING.dejavu` daneben, und
  THIRD-PARTY.md hat einen neuen Abschnitt für Material, das im Repository, aber
  nicht im Image liegt, samt Bitstream-Vera-Bedingungen und der Feststellung,
  dass keine davon hier greift.
- **Commit:** 3f66f69

**3. [Rule 2 - Fehlende kritische Funktionalität] Eindeutigkeit der Suchbegriffe wird geprüft, nicht zugesagt**

- **Gefunden bei:** Task 1
- **Problem:** Die Regel "ein Suchbegriff, eine Datei" stand als Zusage im
  Docstring. Mit 33 Dateien, deren Text teils in Pixeln, teils in deflatierten
  Streams und teils in ZIP-Mitgliedern liegt, kann kein Mensch das mehr im Kopf
  halten, und ein zweiter Träger macht aus einer grünen Behauptung eine leere.
- **Fix:** `UNIQUE_TERMS` plus `_assert_terms_stand_in_one_file`; der Bau bricht
  ab, bevor eine Datei geschrieben wird. Der Textzugriff geht durch ZIPs hindurch
  und zieht den gerenderten Text der Bilddateien mit heran.
- **Commit:** 3f66f69

**4. [Rule 3 - Blockierendes Problem] Der gewachsene Korpus hätte die Integrationsprüfung rot gemacht**

- **Gefunden bei:** Task 2
- **Problem:** `index-search-e2e` prüft exakte Zähler (`EXPECTED_INDEXED: 8`,
  `SKIPPED: 2`, `FAILED: 1`). 21 neue Dateien, davon 14 neue PDFs, hätten diese
  Prüfung sofort gebrochen. Die Zähler sind Absicht und sollen exakt sein, also
  war nicht die Prüfung falsch, sondern ihr Bezugspunkt veraltet.
- **Fix:** Neue Werte 12 / 7 / 6, erzeugt mit dem echten Dispatcher über den
  Korpus mit den Mimetypes der PHP-Allowlist, nicht abgezählt. Der Kommentar
  daneben sagt, wie sie entstanden sind und dass sie sich wieder bewegen, sobald
  der OCR-Zweig die acht Bilddateien indexierbar macht.
- **Commit:** 4cf724f

**5. [Rule 3 - Blockierendes Problem] Drei tote noqa-Direktiven in scripts/ci**

- **Gefunden bei:** Task 1
- **Problem:** Das Abnahmekriterium verlangt `uv run ruff check ../scripts` mit
  Exit 0. Der Lauf war schon vorher rot, an einer Datei, die dieser Plan nicht
  anfasst: drei `# noqa: N802` für eine Regel, die im Regelsatz gar nicht aktiv
  ist (RUF100).
- **Fix:** Direktiven entfernt, die Begründung bleibt als gewöhnlicher Kommentar
  stehen. Drei Zeilen, kein Verhaltensunterschied.
- **Commit:** 3f66f69

### Bewusst nicht getan

- **Kein synthetisches Rauschen, kein Schräglauf, kein Fleck auf den Scans.** Ein
  Korpus mit erzeugtem Schmutz misst den Schmutzerzeuger. Am Tag, an dem
  tesseract ein Wort weniger liest, könnte niemand sagen, ob sich die Engine oder
  das Rauschen bewegt hat. Realistische Degradation gehört in eine Messung, nicht
  in eine Vorrichtung.
- **Keine Prüfsummenliste der 33 Dateien im Repository.** Das Bauskript druckt
  je Datei Größe und SHA-256, und ein zweiter Lauf ist bitgleich. Eine
  eingecheckte Liste würde beim nächsten zlib- oder Pillow-Sprung eine Prüfung
  rot färben, die niemandem hilft; der Anker der Reproduzierbarkeit ist die
  Schrift, und deren Digest steht fest verdrahtet im Skript und in CORPUS.md.
- **Keine Änderung an den zwölf Dateien aus Phase 1 und 2.** Sie kommen byteweise
  unverändert aus dem Bau, damit Gate B weiterhin dieselben Prüfsummen
  vergleicht. Verifiziert über `git status`: keine der zwölf ist als geändert
  gemeldet.
- **Keine Bild-Mimetypes in den beiden Allowlists.** Pitfall 13 verlangt sie an
  zwei Stellen gleichzeitig, zusammen mit dem OCR-Zweig, und das ist der Plan,
  der `Route.OCR` baut. Die sieben Bilddateien liegen bis dahin im Korpus, ohne
  ein Verdikt zu bekommen; das ist in CORPUS.md je Zeile vermerkt.

## Bekannte Stubs

Keine. Der Plan liefert Testdaten und eine Entscheidung im bestehenden
Extraktionspfad; es entsteht keine Oberfläche und kein halb verdrahteter
Datenfluss. Die sieben Bilddateien ohne Verdikt sind kein Stub, sondern die
Eingabe des nachfolgenden Plans, und sie sind als solche dokumentiert.

## Threat Flags

Keine neue Angriffsfläche außerhalb des Registers. Die vier Dispositionen des
Plans sind umgesetzt:

| Threat | Umsetzung |
|---|---|
| T-03-601 | `26-riesige-seitenzahl.pdf` und `33-seitenbaum-zyklus.pdf` liegen im Korpus, beide enden in unter zehn Millisekunden mit `failed(corrupt)`; der Test hat eine Zeitschranke, damit ein Hänger als Fehlschlag endet und nicht als hängender Lauf. Gemessen: `len(document)` liefert bei 627 Byte tatsächlich 100000, erst der Seitendeckel macht daraus 30 Leseversuche |
| T-03-602 | Bau ausschließlich über das Skript, Schrift per SHA-256 gepinnt, Basis-Image per Digest, zweiter Lauf bitgleich verifiziert |
| T-03-603 | Jede Zeile deutscher, Schweizer und österreichischer Prosa ist erfunden und steht im Skript; kein Dokument wurde kopiert |
| T-03-604 | Schwelle an echten mehrseitigen Dokumenten gemessen, Bewertung je Seite plus Anteilsregel, das gemischte PDF als eigener Testfall und als Korpusdatei |

## Verifikation

| Gate | Ergebnis |
|---|---|
| `uv run python ../scripts/dev/build_corpus.py` | Exit 0, 33 Dateien, 308915 Byte |
| zweiter Lauf bitgleich (`sha256sum` davor und danach) | identisch |
| die zwölf Dateien aus Phase 1 und 2 unverändert | `git status` meldet nur neue Dateien |
| `ls testdata/corpus \| wc -l` | 33 (gefordert mindestens 28) |
| `grep -ci 'dejavu' scripts/dev/build_corpus.py` | 8 |
| `grep -c 'load_default' scripts/dev/build_corpus.py` | 0 |
| `grep -c '^\|' testdata/CORPUS.md` | 55 (gefordert mindestens 33) |
| Umlautprüfung CORPUS.md | 15 Treffer echte Umlaute, 0 ASCII-Ersatzschreibungen |
| `uv run python -m pytest -q` | 501 passed, 1 skipped |
| `uv run ruff check .` / `ruff format --check .` | Exit 0, 62 Dateien formatiert |
| `uv run ruff check ../scripts` / `ruff format --check ../scripts` | Exit 0 |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src tests --min-confidence 80` | Exit 0, keine Ausgabe |
| Messkommentar im Code | Datum 2026-09-01 und Korpusdateien innerhalb von 12 Zeilen über der Konstante |
| `.github/workflows/integration.yml` | parst als YAML, Zähler aus dem echten Dispatcher |

## TDD Gate Compliance

Task 2 trägt `tdd="true"`, und die Gate-Folge steht im Log:

- RED: `714a188 test(03-06): failing tests for the per page text layer decision`.
  Rot auf zwei Ebenen: `_SCAN_PAGE_SHARE` existierte nicht, das Modul war nicht
  importierbar. Zusätzlich wurde vor der Umsetzung gemessen, was die alte Regel
  antwortet, damit der Bruch belegt und nicht behauptet ist: zwei dichte Seiten
  vor acht Scans ergaben `indexed`, drei leere Seiten von vier ebenfalls, beide
  müssen `skipped(no_text_layer)` sein.
- GREEN: `4cf724f feat(03-06): decide the text layer per page and by the measured share`,
  44 Tests in der Datei grün, 501 in der Suite.
- REFACTOR: nicht nötig, alle Gates waren nach GREEN grün.

Drei der fünf geforderten Verhaltensweisen waren schon vor der Änderung grün
(reiner Scan, echter Textlayer, Deckblatt vor neun Scans), weil die alte
Dokumentregel für genau diese Eingaben zufällig dasselbe antwortet. Sie sind
deshalb keine neuen Behauptungen, sondern Regressionssperren, und das ist hier
vermerkt statt stillschweigend als RED verbucht.

## Commits

| Commit | Typ | Inhalt |
|---|---|---|
| 3f66f69 | feat | 21 Korpusdateien, Bauskript mit gepinnter Schrift und zwei fail-closed-Prüfungen, CORPUS.md, THIRD-PARTY.md, .gitattributes |
| 714a188 | test | RED-Gate der Textlayer-Entscheidung |
| 4cf724f | feat | GREEN-Gate: pdf.py je Seite plus Anteilsregel, docs/ocr.md, Zähler der Integrationsprüfung |

## Self-Check: PASSED

Alle zehn in dieser Zusammenfassung genannten Dateien existieren, der Korpus
zählt 33 Dateien, alle drei Commit-Hashes stehen im Log, und
`git diff --name-only 244f8e3..HEAD` enthält weder `STATE.md` noch `ROADMAP.md`.

## Was die nächsten Pläne davon haben

- Der Plan, der `Route.OCR` baut, hat für jede Behauptung eine Datei: vier
  Bildformate, ein mehrseitiges TIFF, ein Icon für die Plausibilitätsschwelle
  und ein EXIF-gedrehtes Foto für die Drehung.
- Die Abnahme von D-09 läuft über drei Suchbegriffe, die ausschließlich als
  Pixel existieren: `Bebauungsplan`, `Strasse` und `Jänner`. Vor OCR findet sie
  keiner, danach genau einen Treffer, und das Bauskript hält die Eindeutigkeit
  selbst nach.
- `skipped(no_text_layer)` ist ab jetzt eine belastbare Liste: sieben Dateien
  des Korpus tragen dieses Verdikt, jede aus einem anderen Grund, und
  `CORPUS.md` sagt bei jeder, welchen.
- Die Zähler in `integration.yml` bewegen sich beim nächsten Mal genau dann,
  wenn die Bild-Mimetypes in beide Allowlists wandern. Das ist der eingebaute
  Beleg für Pitfall 13.
