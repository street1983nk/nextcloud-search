---
phase: 03-aktualit-t-und-ocr
plan: 10
subsystem: ocr-bilder
tags: [ocr, pillow, tesseract, bilder, exif, decompression-bomb, allowlist, parity-gate, tdd]
requires:
  - "03-09: Route.OCR als vierter Zweig des Dispatchers und die Frist je Auftrag"
  - "03-08: die Deckel-Kaskade und der gemessene tesseract-Aufruf in ocr.py"
  - "03-05: die gemessenen Deckel in config.py und docs/ocr.md, inklusive des WebP-Ergebnisses"
  - "03-02: der Korpus mit acht Bilddateien, dem Icon und dem EXIF-gedrehten Foto"
provides:
  - "extract/image.py: Kopf lesen, Plausibilität prüfen, aufrichten, skalieren, an die Engine geben"
  - "die vier Bildmimetypes in beiden Allowlists, auf Route.OCR"
  - "das Paritäts-Gate über die doppelt geführte Mimetype-Liste, in beide Richtungen"
  - "öffentliche Namen für den einen gemessenen Engine-Aufruf (ocr.read_page und seine drei Ausgänge)"
affects:
  - "03-13 (Gate B und die Abnahme: die Bilddateien bekommen jetzt wirklich ein Verdikt)"
  - "03-12 (Abgleich: Bilder erscheinen ab jetzt in der Dateischeibe der PHP-Seite)"
  - "Phase 4 (Statusseite: image_not_ocrable und empty_text brauchen deutsche Beschriftungen)"
tech-stack:
  added:
    - "keine neue Abhängigkeit; pillow war seit 03-08 direkte Kante"
  patterns:
    - "Eine Route, zwei Dekoder: der Mimetype entscheidet, welcher die Datei öffnet"
    - "Deckel als benannte Konstante mit dem Satz, woran sie hängt, nie als Literal im Vergleich"
    - "Kopf lesen statt dekodieren: jede Ablehnung kostet einen Dateizeiger und keinen Speicher"
    - "Doppelt geführte Listen bekommen ein Gate, das den fehlenden Wert und die Seite nennt"
key-files:
  created:
    - "backend/src/findling/extract/image.py"
    - "backend/tests/test_allowlist_parity.py"
    - ".planning/phases/03-aktualit-t-und-ocr/03-10-SUMMARY.md"
  modified:
    - "backend/src/findling/extract/dispatch.py"
    - "backend/src/findling/extract/ocr.py"
    - "php/lib/Service/StorageService.php"
    - "backend/tests/test_ocr.py"
    - "backend/tests/test_extract_documents.py"
    - "backend/tests/test_extract_errors.py"
key-decisions:
  - "Der Mimetype wählt den Dekoder innerhalb von Route.OCR, weil die Route nur sagt, dass die Datei als Pixel zu lesen ist, und nicht, ob pdfium oder Pillow sie öffnet"
  - "Image.MAX_IMAGE_PIXELS wird auf das eigene Budget gesetzt; Pillows eigene Ablehnung oberhalb des doppelten Werts wird als skipped(too_large) übersetzt statt als Fehler"
  - "Die Pixelobergrenze wird vor den beiden Plausibilitätsregeln geprüft, weil sie die Speicherwache ist und nicht davon abhängen darf, dass die anderen beiden stehen bleiben"
  - "Die Zeichenschwelle für ein Bild ist 20 und nicht die 25 aus ocr.py, weil die Einheit ein Bild ist und kein Dokument aus bis zu dreißig Seiten"
  - "Der Engine-Aufruf in ocr.py bekommt öffentliche Namen, statt ihn aus image.py über einen privaten Namen zu greifen oder ein zweites Mal zu schreiben"
  - "Die Abnahme über die Korpusbegriffe vergleicht gefaltet, weil ein Rohtext-Vergleich ein Test gegen die tesseract-Version wäre (Pitfall 8), gemessen am großen Umlaut einer Überschrift"
patterns-established:
  - "Paritäts-Gate für eine bewusst doppelt geführte Liste, mit Selbsttest der Fehlermeldung"
  - "Bilddaten mit gefälschtem Kopf als Testmittel: die Bombe wird bewiesen, ohne sie zu bauen"
requirements-completed: [OCR-01]
duration: ca. 40 Minuten
completed: 2026-09-01
---

# Phase 3 Plan 10: Bilder als OCR-Kandidaten

**Ein fotografiertes oder gescanntes Dokument in JPG, PNG, TIFF oder WebP wird über seinen Text auffindbar, ein Icon kostet keine Engine-Zeit, eine Bildbombe endet als Verdikt, und die beiden doppelt geführten Mimetype-Listen können nicht mehr unbemerkt auseinanderlaufen.**

## Performance

- **Dauer:** ca. 40 Minuten
- **Begonnen:** 2026-09-01T11:33:00Z
- **Abgeschlossen:** 2026-09-01T12:12:00Z
- **Tasks:** 2 (beide TDD, vier Commits)
- **Dateien geändert:** 8 (2 neu, 6 geändert)

## Ergebnisse

- `extract/image.py` liest ein Bild in der Reihenfolge, auf die es ankommt: Kopf lesen ohne zu dekodieren, drei Plausibilitätsfragen mit sofortigem Verdikt, aufrichten, herunterskalieren, Graustufen, dann der eine gemessene tesseract-Aufruf.
- Alle fünf Bilddateien des Korpus liefern im Container mit echter Engine ihre Begriffe: Zahlungsavis, Sperrmüllabfuhr, Übermittlungsprotokoll, Rückrufbitte und Sendebericht. Der volle Lauf im Container ist 637 Tests grün, ohne eine einzige Auslassung.
- Das Icon aus dem Korpus wird abgelehnt, ohne dass die Engine überhaupt startet, und dasselbe gilt für ein Banner mit Seitenverhältnis zehn und für einen PNG-Kopf, der vierhundert Megapixel behauptet.
- Das hochkant fotografierte `23-gedreht.jpg` erreicht die Engine als 1000 mal 260 statt als 260 mal 1000. Ohne diesen Schritt läuft der Lauf erfolgreich durch und liefert Zeichensalat, was kein Verdikt jemals zeigen würde.
- Das neue Paritäts-Gate hat beim ersten Lauf sofort etwas gefunden, das seit Phase 2 offen war: `application/xhtml+xml` stand nur auf der Python-Seite. Der Extraktor kannte den Typ, die PHP-Suche lieferte nie eine solche Datei.

## Task-Commits

1. **Task 1: Bilder öffnen, prüfen und an OCR übergeben**
   - `43f2a6f` test: die fehlschlagenden Tests der Bildspur (RED)
   - `b2a5620` feat: `image.py` samt öffentlichen Namen für den Engine-Aufruf (GREEN)
   - `3652459` test: die Abnahme vergleicht gefaltet, nach der Messung im Container
2. **Task 2: Bildtypen auf beiden Seiten, mit Gate gegen das Auseinanderlaufen**
   - `c2be358` test: das fehlschlagende Paritäts-Gate (RED)
   - `dc51b34` feat: beide Allowlists, der Dekoder je Mimetype, `application/xhtml+xml` (GREEN)

## Dateien

- `backend/src/findling/extract/image.py` (neu): die Bildspur mit fünf benannten Deckeln, der Bombenwache und dem Verdikt unterhalb der Zeichenschwelle.
- `backend/tests/test_allowlist_parity.py` (neu): das Gate über die beiden Mimetype-Listen, in beide Richtungen, mit einem Selbsttest der Fehlermeldung und einer Sperre gegen HEIC, BMP und GIF.
- `backend/src/findling/extract/dispatch.py`: `IMAGE_MIMETYPES`, die vier Typen auf `Route.OCR`, und der Zweig, der anhand des Mimetypes zwischen pdfium und Pillow entscheidet.
- `backend/src/findling/extract/ocr.py`: `read_page`, `PageTimeout`, `EngineFailed`, `EngineMissing` heißen jetzt öffentlich; sonst unverändert.
- `php/lib/Service/StorageService.php`: die vier Bildtypen, `application/xhtml+xml`, und dieselbe Begründung wie auf der Python-Seite.
- `backend/tests/test_ocr.py`: neunzehn neue Tests für die Bildspur und den Weg dorthin.
- `backend/tests/test_extract_documents.py`, `backend/tests/test_extract_errors.py`: zwei Zusicherungen, die vorher sagten, dass Bilder nicht unterstützt werden.

## Entscheidungen

**Der Mimetype wählt den Dekoder, nicht die Route.** `Route.OCR` sagt nur, dass diese Datei als Pixel zu lesen ist. Ob pdfium oder Pillow sie öffnet, ist eine Eigenschaft der Datei, und der erzwungene OCR-Auftrag aus Plan 03-09 trägt den Mimetype seines Scans ohnehin mit. Eine fünfte Route wäre die Alternative gewesen, hätte aber die Aussage von Plan 03-09 zerschnitten, dass es genau einen Zweig für "als Bild lesen" gibt.

**Der Engine-Aufruf bekommt öffentliche Namen.** `image.py` braucht denselben Aufruf und dieselben drei Ausgänge wie `ocr.py`. Die zwei Alternativen waren, den privaten Namen aus einem Nachbarmodul zu greifen, oder den gemessenen Aufruf ein zweites Mal zu schreiben. Das Zweite ist ein Aufruf, der driftet, und beim Ersten behauptet ein Unterstrich etwas, das nicht mehr stimmt: ein Name, von dem ein Nachbarmodul abhängt, ist nicht privat.

**Die Pixelobergrenze steht vor den Plausibilitätsregeln.** Sie ist die Speicherwache, und eine Wache, die nur hält, solange zwei Regeln darüber stehen bleiben, ist keine.

**Zwanzig Zeichen statt fünfundzwanzig.** Die Schwelle in `ocr.py` beurteilt ein ganzes Dokument aus bis zu dreißig Seiten, die hier beurteilt ein einzelnes Bild, auf dem ein Stempel, eine Hausnummer und ein Datum ein plausibler Gesamtinhalt sind. Es ist der Startwert aus Pitfall 6.

**Die Abnahme vergleicht gefaltet.** Siehe unten unter den Messungen: das ist keine Abschwächung, sondern genau die Warnung aus Pitfall 8.

## Messungen im Container

Der volle Lauf im Wegwerf-Image aus Plan 03-09, mit den Quellen des Worktrees über `PYTHONPATH`:

```bash
docker run --rm -v "$PWD:/w:ro" -w /w/backend -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/w/backend/src --entrypoint /app/.venv/bin/python \
  findling-ocr-09-test -m pytest -q -p no:cacheprovider
# 637 passed in 64s
```

Dabei ist eine Sache aufgefallen, die vorher nur eine Vermutung der Recherche war. Tesseract 5.5.0 liest die Überschrift von `19-uebermittlung.tif` als "Ubermittlungsprotokoll", ohne die beiden Punkte über dem ersten Buchstaben. Die vier kleingeschriebenen Umlaute der anderen Bilder kommen unversehrt zurück; es ist der große in einer fetten Überschrift, der sie verliert.

Pitfall 8 der Phasenrecherche sagt genau dazu: der Abnahmetest muss über auffindbare Suchbegriffe laufen und nicht über einen Vergleich des OCR-Rohtextes, weil ein Rohtext-Vergleich ein Test gegen die tesseract-Version ist und beim nächsten Debian-Punktrelease rot wird. Der Test faltet deshalb beide Seiten so, wie die deutsche Analysekette es tut: der Snowball-Stemmer entfernt den Umlautakzent in seinem Postlude, also landen beide Schreibweisen auf demselben Term und die Datei ist über "Übermittlungsprotokoll" auffindbar. Die Faltung ist genau dieser eine Schritt und nichts darüber hinaus, ein Wort, das die Engine nicht gelesen hat, fällt weiterhin durch.

## Abnahmekriterien

Task 1:

| Kriterium | Ergebnis |
|---|---|
| `pytest tests/test_ocr.py -q` | Exit 0, 39 lokal grün und 8 übersprungen, im Container alle 47 |
| `grep -c 'MAX_IMAGE_PIXELS'` / `... = None` | 2 / 0 |
| `grep -c 'exif_transpose'` | 1 |
| `grep -c 'n_frames'` | 1 |
| `grep -Ec '^_[A-Z_]+ *(:\|=)'` | 6, gefordert mindestens 4 |
| Aussortier-Tests (icon, banner, too_large, image_not_ocrable) | 4, gefordert mindestens 3 |
| `test_exif_rotated_photo_is_uprighted` | 1 |
| `test_image_file_is_unchanged_after_ocr` | 1 |
| ruff, ruff format, pyright, vulture | alle Exit 0 |

Task 2:

| Kriterium | Ergebnis |
|---|---|
| `pytest tests/test_allowlist_parity.py -q` | Exit 0, 5 Tests |
| vier Bildtypen in beiden Listen | 4 und 4 |
| HEIC, BMP, GIF außerhalb von Kommentaren | 0 und 0 |
| `grep -c 'def test_'` im Gate | 5, gefordert mindestens 2 |
| `grep -ci 'heic'` in beiden Dateien | 2 und 1 |
| `php -l StorageService.php` | "No syntax errors detected", über `php:8.3-cli` im Container gelaufen, weil auf dieser Maschine kein PHP installiert ist |
| voller Lauf plus alle vier Gates | Exit 0 |

Die Gegenprobe von Hand, die der Plan verlangt: `image/webp` einseitig aus der PHP-Liste entfernt, das Gate wird rot mit der Meldung "the container would extract these and never receive one: ['image/webp']", danach zurückgesetzt und wieder grün. Die Prüfsummen der Korpusdateien sind nach allen Läufen unverändert (`git status testdata/` leer).

## Abweichungen vom Plan

### Automatisch behoben

**1. [Regel 1 - Fehler] `application/xhtml+xml` fehlte auf der PHP-Seite**
- **Gefunden bei:** Task 2, beim ersten Lauf des neuen Gates
- **Problem:** `dispatch.ALLOWED_MIMETYPES` kannte den Typ und führte ihn auf `Route.HTML`, `StorageService::ALLOWED_MIMETYPES` nicht. Eine XHTML-Datei wurde also nie eingereiht, obwohl der Extraktor dafür da war. Genau der Fall, für den das Gate gebaut wurde, nur eben schon vorhanden.
- **Behebung:** Typ in die PHP-Liste aufgenommen.
- **Dateien:** `php/lib/Service/StorageService.php`
- **Nachweis:** Gate grün in beide Richtungen; die Gegenprobe von Hand zeigt, dass es ohne den Eintrag rot wäre.
- **Commit:** `dc51b34`

**2. [Regel 3 - Blockierend] Öffentliche Namen für den Engine-Aufruf in `ocr.py`**
- **Gefunden bei:** Task 1
- **Problem:** `image.py` muss denselben gemessenen tesseract-Aufruf verwenden wie `ocr.py`, und dessen Aufruf plus die drei Ausgangsklassen waren privat. `ocr.py` steht nicht in `files_modified` des Plans.
- **Behebung:** `_read_page`, `_PageTimeout`, `_EngineFailed`, `_EngineMissing` heißen jetzt `read_page`, `PageTimeout`, `EngineFailed`, `EngineMissing`; der Grund steht als Kommentar darüber. Keine Verhaltensänderung, keine weiteren Aufrufer betroffen (vorher geprüft).
- **Dateien:** `backend/src/findling/extract/ocr.py`
- **Nachweis:** voller Lauf grün, auch im Container
- **Commit:** `b2a5620`

**3. [Regel 3 - Blockierend] Zwei Alt-Zusicherungen, die Bilder für nicht unterstützt erklärten**
- **Gefunden bei:** Task 2
- **Problem:** `test_extract_documents.py` behauptete, kein Mimetype führe auf `Route.OCR`, und lief anschließend über die ganze Allowlist; `test_extract_errors.py` führte `image/jpeg` und `image/png` in der Liste der bewusst nicht unterstützten Typen. Beide Dateien stehen nicht in `files_modified`, beide werden durch die Änderung zwangsläufig falsch.
- **Behebung:** Die erste Zusicherung sagt jetzt, dass genau die vier Bildtypen auf `Route.OCR` führen, und der Durchlauf überspringt sie mit Begründung. Die zweite führt an ihrer Stelle HEIC, BMP und GIF, was die Aussage sogar schärft.
- **Dateien:** `backend/tests/test_extract_documents.py`, `backend/tests/test_extract_errors.py`
- **Nachweis:** voller Lauf grün
- **Commit:** `dc51b34`

**4. [Regel 1 - Fehler] Die Korpus-Abnahme verglich den Rohtext**
- **Gefunden bei:** Task 1, beim ersten Lauf mit echter Engine im Container
- **Problem:** Der Test verlangte den Begriff Zeichen für Zeichen. Tesseract liest das große Ü der Überschrift ohne Punkte, also war der Test rot, obwohl die Datei über den Begriff auffindbar ist.
- **Behebung:** Beide Seiten werden gefaltet verglichen, genau um den Schritt, den die deutsche Analysekette ohnehin macht. Die Messung und die Begründung stehen im Docstring des Helfers.
- **Dateien:** `backend/tests/test_ocr.py`
- **Nachweis:** 52 von 52 im Container, danach der volle Lauf mit 637
- **Commit:** `3652459`

---

**Abweichungen insgesamt:** 4 automatisch behoben (2 Fehler, 2 blockierend)
**Auswirkung:** Kein Scope-Zuwachs. Zwei der vier sind Folgen der geplanten Änderung, eine ist ein Altfehler, den das neue Gate aufgedeckt hat, und eine ist eine Messung, die eine Annahme ersetzt.

## Zurückgestellt

Zwei Punkte gehören in `worker/poller.py`, das nicht in `files_modified` dieses Plans steht. Beide stehen ausführlich in `deferred-items.md`:

1. **Ein Bild kommt als Inhaltsjob und bekommt darum die kurze Frist.** 120 s statt der 660 s des OCR-Zweigs. Für einseitige Bilder reichlich (gemessen rund zwei Sekunden je Seite), für ein Faxarchiv mit vielen dichten Seiten knapp: das Verdikt wäre dann `failed(timeout)` statt des `indexed(truncated)`, das der Seitendeckel vorsieht.
2. **`ocr_used` wird für Bilder nicht gesetzt.** Der Poller setzt die Marke nur im Zweig `kind=ocr`. Die eigentliche Antwort auf D-05 ist aber `skipped(empty_text)` zusammen mit gesetztem `ocr_used`; ohne die Marke bleibt die aufgewendete Zeit auf der Statusseite von Phase 4 unsichtbar. Der Eingriff ist eine Zeile im Inhaltszweig.

## Bekannte Stubs

Keine.

## Aufgetretene Probleme

- Der Lesegate `test_readonly_gate` schlug zuerst an, weil `_encode_frame` `picture.copy()` benutzte und `copy` in der Liste der schreibenden Bezeichner von `nc_py_api.files` steht. Der Aufruf war ohnehin nur der unerreichbare Zweig der `exif_transpose`-Signatur; er ist durch eine Fallunterscheidung ohne Kopie ersetzt.
- Das Wegwerf-Image aus Plan 03-09 trägt das installierte Paket des damaligen Standes. Mit `PYTHONPATH=/w/backend/src` überlagern die Quellen des Worktrees die Installation, was einen Neubau des Images für diesen Nachweis erspart.

## Bereitschaft für die nächsten Pläne

- Plan 03-13 kann Gate B jetzt sinnvoll laufen lassen: die acht Bilddateien des Korpus bekommen ein Verdikt statt keines, was die Voraussetzung dafür ist, dass der Prüfsummenlauf überhaupt etwas beweist (Pitfall 13).
- Phase 4 braucht deutsche Beschriftungen für `image_not_ocrable`; `empty_text`, `too_large`, `ocr_failed` und `ocr_unavailable` waren schon vorher fällig.

---
*Phase: 03-aktualit-t-und-ocr*
*Abgeschlossen: 2026-09-01*
