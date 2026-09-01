---
phase: 03-aktualit-t-und-ocr
plan: 08
subsystem: ocr-maschine
tags: [ocr, tesseract, pypdfium2, pillow, subprozess, deckel, verdikte, tdd]
requires:
  - "03-05: tesseract deu+eng+osd im Laufzeitimage, die OCR-Konstanten in config.py, docs/ocr.md mit fuenf Messungen"
  - "03-06: der DACH-Korpus mit gescannten Seiten und die gemessene Textlayer-Schwelle je Seite"
  - "02-05: das Sandbox-Kind mit setsid, killpg und RLIMIT_AS, in das dieser Zweig hineinlaeuft"
provides:
  - "backend/src/findling/extract/raster.py: eine Seite als Graustufen-PNG, stride-sicher, mit Kantendeckel gegen die PDF-Bombe"
  - "backend/src/findling/extract/ocr.py: tesseract als Subprozess ueber stdin/stdout mit der vierstufigen Deckel-Kaskade"
  - "drei neue Verdikte (image_not_ocrable, ocr_failed, ocr_unavailable) an allen vier Orten"
  - "ein Paritaets-Gate zwischen der Python-Reason-Liste und der PHP-Konstante REASONS"
  - "19 Tests, die im Container ohne Ueberspringen gegen die echte Engine laufen"
affects:
  - "03-09 (verdrahtet extract_pdf_ocr in den Dispatcher und setzt die harte Deadline im Elternteil)"
  - "03-10 (Bildzweig: nutzt dieselbe Engine-Funktion und das Verdikt image_not_ocrable)"
  - "03-13 (Gate B: die Nur-Lesen-Invariante ueber den OCR-Pfad)"
  - "Phase 4 (drei neue Reason-Codes brauchen je eine deutsche Beschriftung)"
tech-stack:
  added:
    - "keine neue Abhaengigkeit: pypdfium2 und pillow lagen bereits gepinnt vor"
  patterns:
    - "Fremdprozess statt Bibliotheks-Binding, damit ein Absturz den Enkel trifft und nicht das Sandbox-Kind"
    - "Deckel-Kaskade mit Trennlinie: die drei oberen Ebenen liefern ein Teilergebnis, die beiden unteren ein Scheitern"
    - "Rasterung und Engine als zwei Dateien, damit die Pixelseite ohne installierte Engine testbar bleibt"
    - "Reason-Paritaet ueber Sprachgrenzen als Test statt als Zusage"
key-files:
  created:
    - "backend/src/findling/extract/raster.py"
    - "backend/src/findling/extract/ocr.py"
    - "backend/tests/test_ocr.py"
    - ".planning/phases/03-aktualit-t-und-ocr/03-08-SUMMARY.md"
  modified:
    - "backend/src/findling/extract/errors.py"
    - "backend/src/findling/store/repo.py"
    - "php/lib/Service/FileStateService.php"
    - "backend/tests/test_extract_errors.py"
key-decisions:
  - "MAX_EDGE_PIXELS = 5000: A4 und A3 werden bei 300 dpi weiterhin voll aufgeloest gerastert, erst die absurde Seite wird skaliert"
  - "_MIN_OCR_CHARS = 25, dieselbe Zahl wie pdf._MIN_CHARS_PER_PAGE, aber je Dokument statt je Seite und bewusst dupliziert statt importiert"
  - "Ein Exitcode ungleich null beendet den ganzen Job, weil dieselbe Wand auf Seite zwei noch steht"
  - "Die Engine-Tests laufen ueber alle drei DACH-Begriffe (Bebauungsplan, Strasse, Jaenner) statt nur ueber einen"
  - "Der Containerlauf braucht ein Wegwerf-Testimage: das Auslieferungsimage traegt weder uv noch pytest, und das soll so bleiben"
patterns-established:
  - "Protokoll statt Duck-Typing fuer die vier Bitmap-Eigenschaften, damit ein gepolsterter Testfall ohne PDF baubar ist"
  - "Engine-Ersatz je Seite im Test, weil Timeout und Signaltod als echte Dokumente Tests ueber das Dokument waeren"
requirements-completed: [OCR-01, OCR-02]
duration: ca. 35 Minuten
completed: 2026-09-01
---

# Phase 3 Plan 08: Die OCR-Maschine

**pypdfium2 rastert Seite für Seite in Graustufen, tesseract liest sie als Subprozess über stdin, und vier ineinandergreifende Deckel entscheiden, ob aus einem langen Scan ein Teilergebnis wird oder ein ehrliches Scheitern.**

## Performance

- **Dauer:** ca. 35 Minuten
- **Tasks:** 3 (alle mit TDD-Gates)
- **Commits:** 6 (drei RED, drei GREEN)
- **Geänderte Dateien:** 7, exakt die aus `files_modified`
- **Tests:** 554 grün auf dem Entwicklungsrechner (4 übersprungen), 19 von 19 grün im Container ohne ein einziges Überspringen

## Was gebaut wurde

### Task 1: drei Verdikte an allen vier Orten (TDD)

`image_not_ocrable` als `skipped`, `ocr_failed` und `ocr_unavailable` als `failed`,
einsortiert in die nach Zustand geordneten Blöcke von `errors.py`, wortgleich in
`repo.py` und in derselben Änderung in `php/lib/Service/FileStateService.php`.
Ohne den dritten Ort verwirft `record()` den Reason still, und die Datei bekommt
am Ende gar kein Verdikt.

Neu ist das Gate dafür. Für die beiden Python-Listen gab es längst einen
Vergleich, für die dritte Liste keinen: `test_php_reason_list_matches_python`
liest die PHP-Konstante per Regex und vergleicht sie in beide Richtungen. Ein
Code, den nur eine Seite kennt, erzeugt ab jetzt einen roten Test statt einer
Lücke auf der Statusseite.

`image_not_ocrable` steht nicht in `_EXCEPTION_REASONS`, und das ist ebenfalls
kein Versprechen mehr: `test_the_exception_table_holds_failures_only` läuft über
alle Werte der Tabelle und verlangt, dass jeder zu `failed` gehört. Ein Eintrag,
der es nicht tut, würde im Fehlerhandler eine `ValueError` werfen, also genau
dort, wo gerade nichts mehr schiefgehen darf.

### Task 2: Seiten rastern, sparsam und stride-sicher (TDD)

`raster.py` macht aus genau einer Seite ein Graustufen-PNG:
`page.render(scale=..., grayscale=True, draw_annots=False)`, dann die auf
`stride` gepolsterten Zeilen einzeln auf die Seitenbreite geschnitten, dann
`Image.frombytes` und PNG mit niedriger Kompression. Der rohe Block als Ganzes
gelesen ergäbe keine Ausnahme, sondern Schrägstreifen, die immer noch wie ein
Scan aussehen; der Test dagegen baut eine absichtlich gepolsterte Bitmap mit
drei Pixeln in fünf Byte je Zeile und prüft die sechs Pixelwerte.

Die Freigabe ist verschachtelt wie in `pdf._page_text`, und der Test belegt auch
die Reihenfolge: bei einem Fehler im Kodierer steht im Protokoll erst `bitmap`,
dann `page`.

Der Bombenschutz ist eine Kantenlänge, kein festes dpi. `31-riesenformat.pdf`
misst 14400 x 14400 Punkt und würde bei 300 dpi zu 60000 Pixeln je Kante, also
neun Gigapixeln in einem Kanal. `MAX_EDGE_PIXELS = 5000` liegt über A3 bei
300 dpi (4961), lässt also jedes gewöhnliche Format unangetastet, und greift nur
bei der absurden Seite. Der Kommentar nennt den Grund in einem Satz: `RLIMIT_AS`
ist der letzte Halt, nicht der erste.

Das Modul kennt tesseract nicht und startet keinen Kindprozess. Genau deshalb ist
es eine eigene Datei: die Pixelseite ist auf einer Maschine ohne OCR-Engine
prüfbar, und das ist die Entwicklungsmaschine dieses Projekts.

### Task 3: tesseract als Subprozess mit der Deckel-Kaskade (TDD)

`ocr.extract_pdf_ocr(path)` liegt auf Modulebene, damit es wie `extract_pdf` in
das Extraktionskind gepickelt werden kann. Der Ablauf: Dokument öffnen, über
`min(Seitenzahl, Seitendeckel)` iterieren, vor jeder Seite die weiche
Gesamtdeadline mit `time.monotonic` prüfen, je Seite rastern und an die Engine
geben.

Der Aufruf ist eine Argumentliste, niemals eine Shell:

```
tesseract - - -l deu+eng --oem 1 --psm 3 -c tessedit_do_invert=0
```

mit `OMP_THREAD_LIMIT=1` in der Umgebung, `capture_output`, `timeout` je Seite
und `check=False`. Der Test prüft diese Zeile Argument für Argument, dazu die
Variable, den Timeout-Wert und dass die Eingabe mit der PNG-Signatur beginnt.
`stderr` wird eingesammelt und weggeworfen; ein eigener Test schiebt einen
Dateinamen durch `stderr` und verlangt, dass er in keinem Log auftaucht
(T-02-107).

Die Abbildung der Ausgänge:

| Ausgang | Verdikt | Was mit der Schleife passiert |
|---|---|---|
| Seitendeckel gerissen | `indexed(truncated)` | endet, Text bleibt |
| weiche Deadline gerissen | `indexed(truncated)` | endet, Text bleibt |
| eine Seite im Zeitdeckel | keines | Seite verworfen, läuft weiter |
| alle Seiten im Zeitdeckel | `failed(timeout)` | nichts gelesen, also ein Fehler |
| Exitcode ungleich null | `failed(ocr_failed)` | bricht ab |
| Engine nicht vorhanden | `failed(ocr_unavailable)` | bricht ab |
| unter 25 Zeichen am Ende | `skipped(empty_text)` | regulär beendet |

Dass ein Exitcode ungleich null den ganzen Job beendet, ist eine Entscheidung
und steht als Kommentar da: was Seite eins umgebracht hat, steht vor Seite zwei
noch genauso, und der Rest des Budgets wäre gegen dieselbe Wand gefahren.

## Verifikation

| Gate | Ergebnis |
|---|---|
| `uv run python -m pytest -q` (Host) | 554 passed, 4 skipped |
| `pytest tests/test_ocr.py` im Container, echte Engine | 19 passed, 0 skipped |
| `uv run ruff check .` / `ruff format --check .` | Exit 0, 65 Dateien formatiert |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src tests --min-confidence 80` | Exit 0, keine Ausgabe |
| `php -l php/lib/Service/FileStateService.php` (php:8.2-cli) | No syntax errors detected |
| `grep -Ec 'image_not_ocrable\|ocr_failed\|ocr_unavailable'` in errors.py / repo.py / php | 5 / 3 / 3 (gefordert je mindestens 3) |
| `grep -c 'def test_php_reason_list_matches_python'` | 1 |
| raster.py: `grayscale=True` / `stride` / `frombuffer` / `finally` / `subprocess` | 1 / 7 / 0 / 4 / 0 |
| raster.py: Bombenschutz `max_edge\|MAX_EDGE\|scale` | 13 |
| ocr.py: `shell=True` / `OMP_THREAD_LIMIT` / `tessedit_do_invert=0` | 0 / 1 / 1 |
| ocr.py: `LOGGER.…(… stderr …)` | keine Treffer |
| test_ocr.py: Fehlerpfade / `truncated` / Nur-Lesen-Test | 3 / 2 / 1 |
| Korpus nach allen Läufen unverändert | `git status --porcelain testdata/` leer, Prüfsummentest grün |

Die drei DACH-Begriffe aus `testdata/CORPUS.md` wurden im Container tatsächlich
aus Pixeln gelesen: `Bebauungsplan` aus `13-ratsvorlage-scan.pdf`, `Strasse` aus
`15-schweiz-baubewilligung.pdf` und `Jänner` aus `16-oesterreich-mitteilung.pdf`.
Jeder dieser Begriffe steht in genau einer Korpusdatei, und in keiner davon als
Text. Das ist die Abnahmegrundlage von D-09, hier auf Modulebene belegt.

## Abweichungen vom Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierendes Problem] Der Containerlauf braucht ein Wegwerf-Testimage**

- **Gefunden bei:** Task 3
- **Problem:** Das Abnahmekriterium lautet
  `docker run ... <image> uv run pytest tests/test_ocr.py -q`. Das
  Auslieferungsimage trägt aber weder `uv` noch `pytest`: die Runtime-Stage
  kopiert nur die mit `--no-dev` gebaute virtuelle Umgebung, und `uv` bleibt in
  der Build-Stage. Der Befehl kann dort nicht laufen, und ihn lauffähig zu
  machen hieße, Testwerkzeug in das ausgelieferte Image zu legen.
- **Fix:** Ein Wegwerf-Image `FROM findling-ocr-08`, das als root `uv` (per
  Digest, dieselbe Version wie im Dockerfile) und die beiden gepinnten
  Test-Pakete in die vorhandene virtuelle Umgebung legt. Gelaufen wird
  read-only gemountet:
  `docker run --rm -v "$PWD:/w:ro" -w /w/backend --entrypoint /app/.venv/bin/python findling-ocr-08-test -m pytest tests/test_ocr.py -q`.
  Damit laufen die Tests gegen genau die Engine, die Sprachdaten und das
  installierte Paket des Auslieferungsimage, und das Image selbst bleibt sauber.
- **Verifikation:** 19 passed, 0 skipped im Container.
- **Nicht eingecheckt:** Das Hilfs-Dockerfile ist vier Zeilen und liegt bewusst
  nicht im Repository, so wie der Messtreiber aus Plan 03-05 nicht darin liegt.
  Es steht hier vollständig genug, um es nachzustellen; was dauerhaft geprüft
  werden muss, gehört in `.github/workflows`, und dort ist der Containerlauf
  Sache von Plan 03-09, der den Zweig verdrahtet.

**2. [Rule 3 - Blockierendes Problem] Kein PHP auf dem Entwicklungsrechner**

- **Gefunden bei:** Task 1
- **Problem:** `php -l` ist auf dieser Maschine nicht vorhanden; das
  Abnahmekriterium verlangt es.
- **Fix:** Die Prüfung lief in `php:8.2-cli`, also in derselben PHP-Version, die
  `.github/workflows/php.yml` verwendet, mit read-only gemountetem `php/`.
- **Verifikation:** `No syntax errors detected in php/lib/Service/FileStateService.php`.

**3. [Rule 1 - Bug im Test] `Image.getdata` ist in Pillow 12 abgekündigt**

- **Gefunden bei:** Task 2
- **Problem:** Der Pixelvergleich des stride-Tests benutzte `getdata()`. Die
  Suite schaltet `DeprecationWarning` auf `error`, also war der Test rot, aber
  aus dem falschen Grund.
- **Fix:** `image.tobytes()` statt `getdata()`; dieselbe Aussage, ohne die
  abgekündigte API.

---

**Summe:** 3 Abweichungen, alle automatisch behoben (2 blockierend, 1 Testfehler).
**Wirkung auf den Plan:** keine Scope-Ausweitung. Zwei der drei sind
Werkzeugfragen der Entwicklungsmaschine, die dritte eine Zeile im Test.

## Entscheidungen

- **`MAX_EDGE_PIXELS = 5000`.** Der Plan verlangt eine Zielkantenlänge, nennt
  aber keine Zahl. 5000 liegt über A3 bei 300 dpi (4961), lässt also jedes
  gewöhnliche Format bei voller Auflösung, und deckelt die Seite, die es nicht
  ist, bei 25 MB in einem Kanal.
- **`_MIN_OCR_CHARS = 25`.** Dieselbe Zahl, mit der `pdf.py` entscheidet, dass
  eine Seite Text trägt, hier aber auf das fertige Dokument angewandt. Bewusst
  dupliziert statt importiert, mit der Begründung im Kommentar: die Einheit ist
  eine andere, und ein Import von `pdf.py` zöge pypdf in ein Kind, das alle 200
  Dateien neu startet und es sonst nicht braucht.
- **Ein Exitcode ungleich null beendet den Job.** Die Alternative wäre, die
  restlichen Seiten trotzdem zu versuchen. Da der häufigste Fall dieses Ausgangs
  der Speichertod ist (Messung 5 in `docs/ocr.md`), wäre das ein Vielfaches der
  Zeit für dasselbe Ergebnis.
- **Ein Protokoll für die Bitmap.** `_encode_page` nimmt kein `PdfBitmap`,
  sondern die vier Eigenschaften, von denen es abhängt. Nur so lässt sich ein
  gepolsterter Fall im Test bauen, ohne ein PDF zu suchen, das pdfium zum Polstern
  bringt.
- **Ein `pyright: ignore` beim Skalierungsargument.** pypdfium2 liefert keine
  Typinformation, pyright liest den Typ von `scale` aus dem Vorgabewert `1` ab
  und lehnt danach jeden Fließkommawert ab. Die Zeile trägt die Begründung.

## Bekannte Stubs

Keine. `image_not_ocrable` ist der einzige der drei neuen Codes, den dieser Plan
noch nicht produziert; er gehört zum Bildzweig aus Plan 03-10 und steht hier, weil
Pitfall 14 verlangt, dass ein Reason in derselben Änderung an allen vier Orten
ankommt. Ein zweiter Durchgang durch vier Dateien und eine Nextcloud-Migration
wäre der teurere Weg. Beide anderen Codes sind ab sofort erreichbar.

`extract_pdf_ocr` ist noch nirgends verdrahtet: `dispatch.py` kennt keine
`Route.OCR`, und die harte Deadline des Elternteils liegt weiterhin bei
`EXTRACT_TIMEOUT_SECONDS`. Beides ist der erklärte Inhalt von Plan 03-09, im
Zielabschnitt dieses Plans so benannt ("hier entsteht der Motor").

## Threat Flags

Keine neue Angriffsfläche außerhalb des Registers. Die sechs Dispositionen sind
umgesetzt:

| Threat | Umsetzung |
|---|---|
| T-03-801 | Argumentliste, nie `shell=True`; die Sprachliste ist in `config._ocr_languages` gegen die Allowlist geprüft, bevor sie hier ankommt. Test prüft die Argumente einzeln und dass kein `shell` übergeben wird |
| T-03-802 | Seitendeckel vor der Schleife plus `MAX_EDGE_PIXELS` statt festem dpi; `31-riesenformat.pdf` als Testfall |
| T-03-803 | `subprocess.run(timeout=)` je Seite, weiche Gesamtdeadline vor jeder Seite; harte Deadline und `killpg` bleiben beim Elternteil (Plan 03-09) |
| T-03-804 | `stderr` wird eingesammelt und verworfen; eigener Test mit einem Dateinamen darin, plus das Grep-Gate |
| T-03-805 | Kein Schreibpfad, keine Zwischendatei; Prüfsummen- und Metadatenvergleich in `test_original_file_is_unchanged_after_ocr`, auf beiden Pfaden (mit und ohne Engine) |
| T-03-806 | Eigenes Verdikt `ocr_unavailable` statt `failed(corrupt)`, in beiden Sprachen und mit Test |

## TDD Gate Compliance

Alle drei Tasks tragen `tdd="true"`, und die Gate-Folge steht im Log:

| Task | RED | GREEN | REFACTOR |
|---|---|---|---|
| 1 | `448e391` (Sammelfehler: `Reason.IMAGE_NOT_OCRABLE` existiert nicht) | `2559a4a` | nicht nötig |
| 2 | `93fa74b` (Modul `raster` nicht importierbar) | `35ed7d7` | nicht nötig |
| 3 | `3264155` (Modul `ocr` nicht importierbar) | `5f4e314` | nicht nötig |

Jedes RED war rot aus dem beabsichtigten Grund und nicht aus einem zufälligen:
in Task 1 fehlte der Enum-Wert, in Task 2 und 3 das Modul. Nach jedem GREEN waren
alle Gates ohne Nacharbeit grün, deshalb gibt es keinen REFACTOR-Commit.

## Commits

| Commit | Typ | Inhalt |
|---|---|---|
| 448e391 | test | RED: drei Verdikte, PHP-Parität, Ausnahmetabelle |
| 2559a4a | feat | GREEN: die drei Codes in errors.py, repo.py und FileStateService.php |
| 93fa74b | test | RED: Rasterung, stride, Freigabereihenfolge, Kantendeckel |
| 35ed7d7 | feat | GREEN: raster.py |
| 3264155 | test | RED: Deckel-Kaskade, drei Fehlerpfade, Aufrufform, Nur-Lesen |
| 5f4e314 | feat | GREEN: ocr.py |

## Was die nächsten Pläne davon haben

- Plan 03-09 findet eine picklebare Funktion `extract_pdf_ocr(path)` vor, die nur
  noch eine `Route` und einen Job-Timeout braucht. Die harte Deadline muss
  strikt über `settings().ocr_job_seconds` liegen; `ocr_hard_deadline_seconds`
  liefert genau diesen Wert bereits abgeleitet.
- Plan 03-10 bekommt `raster.py` nicht, wohl aber `_read_page`-Verhalten und die
  Verdikte: der Bildzweig kodiert mit Pillow statt mit pdfium und gibt dieselbe
  Byte-Folge an dieselbe Engine. `image_not_ocrable` liegt bereits an allen vier
  Orten.
- Phase 4 braucht drei deutsche Beschriftungen: "Bild zu klein für Texterkennung",
  "Texterkennung fehlgeschlagen", "Texterkennung im Image nicht vorhanden". Mehr
  Codes sind bewusst nicht entstanden.

## Self-Check: PASSED

- Alle sieben geänderten Dateien existieren und stehen in `git diff --name-only 3f16b9e..HEAD`.
- Alle sechs Commit-Hashes stehen im Log von `worktree-agent-03-08`.
- Weder `.planning/STATE.md` noch `.planning/ROADMAP.md` sind im Diff.
- `testdata/` ist unverändert.

---

*Phase: 03-aktualit-t-und-ocr, Plan 08*
*Abgeschlossen: 2026-09-01*
