---
phase: 03-aktualit-t-und-ocr
plan: 09
subsystem: ocr-verdrahtung
tags: [ocr, dispatcher, sandbox, deadline, killpg, poller, etag, ocr_used, tdd]
requires:
  - "03-08: extract_pdf_ocr(path) als picklebare Funktion und die vierstufige Deckel-Kaskade"
  - "03-07: der Requeue-Pfad, der eine Zeile genau einmal auf die zweite Spur legt (kind=ocr)"
  - "03-06: die gemessene Textlayer-Schwelle in pdf.py, die entscheidet, wer ueberhaupt in die Spur kommt"
  - "03-05: die gemessenen Deckel in config.py und docs/ocr.md, inklusive ocr_hard_deadline_seconds"
  - "02-05: das Sandbox-Kind mit setsid, killpg und RLIMIT_AS"
provides:
  - "Route.OCR als vierter Zweig des Dispatchers, gewaehlt ueber die Job-Art statt ueber den Mimetype"
  - "eine harte Deadline je Auftrag statt je Worker (ExtractionWorker._ask, extract_guarded)"
  - "der OCR-Zweig im Poller: Bytes holen, erzwungene Route, lange Frist, kein Schnellpfad"
  - "files.etag und files.ocr_used werden zum ersten Mal geschrieben"
  - "ein Enkel-Test, der den Gruppen-Kill mit einem echten Enkelprozess belegt"
affects:
  - "03-10 (Bildzweig: nutzt Route.OCR und die Deadline je Auftrag unveraendert weiter)"
  - "03-12 (Abgleich: vergleicht den hier geschriebenen etag)"
  - "03-13 (Gate B: die Nur-Lesen-Invariante ueber den verdrahteten OCR-Pfad)"
  - "Phase 4 (weist ocr_used auf der Statusseite aus)"
tech-stack:
  added:
    - "keine neue Abhaengigkeit"
  patterns:
    - "Deadline als Argument des Auftrags, nicht als Eigenschaft des Workers"
    - "Route als Eigenschaft des Auftrags, nicht als Pseudo-Mimetype in der Allowlist"
    - "ein Verdikt traegt mit, ob OCR dafuer lief; der Umbenennungspfad reicht die Marke weiter"
key-files:
  created:
    - ".planning/phases/03-aktualit-t-und-ocr/03-09-SUMMARY.md"
  modified:
    - "backend/src/findling/extract/sandbox.py"
    - "backend/src/findling/extract/dispatch.py"
    - "backend/src/findling/worker/poller.py"
    - "backend/src/findling/store/repo.py"
    - "backend/tests/test_sandbox.py"
    - "backend/tests/test_ocr.py"
    - "backend/tests/test_poller.py"
    - "backend/tests/test_extract_documents.py"
key-decisions:
  - "Die erzwungene Route ueberspringt judge vollstaendig, damit die zweite Spur wirklich unabhaengig vom Mimetype ist; der Groessendeckel geht dabei nicht verloren, weil er auf dem Gateway-Pfad erneut greift"
  - "sandbox.py bekommt die Route als str getippt statt als Route, damit der Elternteil den Dispatcher weiterhin nie importiert"
  - "ocr_used wird ueberschrieben statt akkumuliert; der Umbenennungspfad traegt den gespeicherten Wert ausdruecklich weiter"
  - "etag wandert in FileMeta, weil es wie Mimetype und Groesse mit dem Warteschlangeneintrag ankommt"
  - "Eine vierte Probe-Art grandchild statt eines echten tesseract im Test, weil der Gegenstand die Wache ist und nicht die Engine"
patterns-established:
  - "Probe-Art fuer eine Prozesskonstellation, die kein Dokument herstellen kann"
  - "Aufrufaufzeichnung im Extraktor-Ersatz: Route und Frist sind sonst unsichtbar, weil sie denselben Index erzeugen"
requirements-completed: [OCR-01, OCR-02]
duration: ca. 45 Minuten
completed: 2026-09-01
---

# Phase 3 Plan 09: Die OCR-Maschine verdrahtet

**Ein gescanntes PDF ist ab jetzt ueber seinen Inhalt auffindbar: der Dispatcher kennt eine vierte Route, die ueber die Job-Art gewaehlt wird, das Sandbox-Kind bekommt seine Frist je Auftrag statt je Worker, und der Zustand vermerkt, dass OCR dafuer gelaufen ist.**

## Performance

- **Dauer:** ca. 45 Minuten
- **Tasks:** 3 (alle mit TDD-Gates)
- **Commits:** 6 (drei RED, drei GREEN)
- **Geänderte Dateien:** 8
- **Tests:** 588 grün auf dem Entwicklungsrechner (6 übersprungen), 594 grün im Container ohne ein einziges Überspringen

## Task-Commits

1. **Task 1: Deadline je Auftrag im Sandbox-Kind** , `3731045` (test, RED) und `be61b3b` (feat, GREEN)
2. **Task 2: OCR als vierter Zweig im Dispatcher** , `42911bb` (test, RED) und `6b56972` (feat, GREEN)
3. **Task 3: OCR-Aufträge im Poller, mit Vermerk im Zustand** , `9a03e99` (test, RED) und `cd2c3f6` (feat, GREEN)

## Was gebaut wurde

### Task 1: zwei Deadlines statt einer (TDD)

`ExtractionWorker._ask` nimmt die Frist als Argument entgegen; der im Konstruktor
gebundene Wert bleibt der Vorgabewert, sodass jeder Aufruf, den es vor diesem Plan
gab, unverändert weiterläuft. `run`, `probe` und die Fassade `extract_guarded`
reichen den Wert durch.

Der Kommentar an `pipe.poll` trägt jetzt die Begründung, warum es zwei Fristen
gibt: läge die harte Deadline gleichauf mit der weichen, würde der Elternteil das
Kind genau in dem Moment töten, in dem es seinen Teiltext durch die Pipe schiebt,
und `indexed(truncated)` aus D-08 käme in der Praxis nie vor (T-03-902). Der
Abstand wird in `config.py` abgeleitet, nicht als zweite Konstante geführt, also
wandert er mit, wenn ein Admin das weiche Budget anhebt.

`setsid`, `_kill_child_tree`, das Secrets-Shedding und die vier Recycling-Regeln
sind unangetastet. Die Grep-Gates belegen es: `setsid` steht weiterhin genau
einmal, `killpg` einmal, `_WORKER` fünfmal, also unverändert gegenüber dem Stand
vor diesem Plan.

Neu ist eine vierte Probe-Art. `grandchild` startet im Sandbox-Kind einen echten
Enkelprozess, gibt dessen pid zurück und lässt ihn laufen; der Test treibt danach
eine Frist über die Deadline und belegt, dass der Gruppen-Kill den Enkel
mitnimmt. Die Lebendigkeit wird über `/proc/<pid>/stat` gelesen und nicht über
Signal 0, weil ein verwaister Enkel an pid 1 des Containers hängt und dort als
Zombie liegen bleiben kann: `os.kill(pid, 0)` nennt einen Zombie lebendig, und
genau diese Antwort darf der Test nicht akzeptieren.

### Task 2: Route.OCR im Dispatcher (TDD)

`Route.OCR` ist der einzige Zweig, auf den kein Mimetype zeigt. Die
Einstiegsfunktion bekommt einen optionalen `route`-Parameter, der die
Routenwahl übersteuert; `judge` bleibt unverändert die Stelle, die aus Typ und
Größe ein Urteil bildet, und muss nichts über Job-Arten wissen. Der Kommentar
nennt den Grund, warum das sauberer ist als ein Pseudo-Mimetype: eine zweite Spur
ist eine Eigenschaft des Auftrags, nicht der Datei, und ein Eintrag in
`ALLOWED_MIMETYPES` würde jedem Leser dieser Tabelle vorspiegeln, Nextcloud könne
so einen Typ liefern.

Der Größendeckel geht mit der Übersteuerung nicht verloren, er ist bereits
bezahlt: ein OCR-Auftrag existiert nur, weil für dieselbe Datei ein Inhaltsjob
durch `judge` und durch das Gateway lief, wo eine inzwischen gewachsene Datei als
`skipped(too_large)` endet, bevor ein Byte extrahiert wird. Das steht als Absatz
im Docstring.

Der Import von `ocr` steht im `case`, aus demselben Grund wie bei jeder anderen
Route: das Kind wird alle 200 Dateien recycelt, und `ocr` zieht `raster` und
darüber Pillow nach. Ein Test prüft beides, den Import im Zweig und das Fehlen
auf Modulebene, letzteres über den AST statt über eine Zeichenkette.

Der Modul-Docstring beschreibt den Bildpfad jetzt so, wie er ist: die Route
existiert, sie wird über die Job-Art erreicht, und Bilddateien selbst kommen
erst mit Plan 03-10 in die Allowlist. Bis dahin ist der einzige Weg in diese
Route ein gescanntes PDF, das der Textdurchlauf als `skipped(no_text_layer)`
beurteilt hat.

### Task 3: der OCR-Zweig im Poller und der Vermerk im Zustand (TDD)

`_read_the_scan` läuft wie der Inhaltszweig, mit drei Unterschieden, die jeder
einen eigenen Kommentar tragen:

| Unterschied | Warum |
|---|---|
| Route wird auf `Route.OCR` erzwungen | die zweite Spur gehört zum Auftrag, nicht zum Mimetype |
| Frist ist `ocr_hard_deadline_seconds` | 660 s statt 120 s, mit Abstand über der weichen Deadline des Kindes |
| kein `is_unchanged` | die Bytes sind dieselben wie beim Textversuch; der Schnellpfad würde den Lauf wegquittieren |

Der Zweig quittiert und übergibt nie erneut: diese Zeile *war* die Übergabe, und
sie noch einmal auf die Spur zu legen wäre die Endlosschleife aus T-03-704 von
der anderen Seite. Die Scratch-Datei wird im `finally` verworfen wie auf dem
Inhaltspfad, und ein Test mit einem Extraktor, der wirft, belegt genau den
Fehlerpfad.

`repo.record` schreibt zwei Felder, die seit Phase 2 leer im Schema stehen.
`etag` sitzt in `FileMeta`, weil es wie Mimetype, Größe und mtime mit dem
Warteschlangeneintrag ankommt und Nextclouds eigene Versionsmarke ist; ohne einen
gespeicherten Wert müsste der Abgleich aus Plan 03-12 jede Datei holen, um
festzustellen, dass sich keine geändert hat. `ocr_used` ist ein Schlüsselwort von
`record` und wird gesetzt, sobald ein OCR-Lauf stattgefunden hat, auch wenn er
`skipped(empty_text)` ergab: die Marke sagt, dass die Zeit aufgewendet wurde,
nicht dass sie sich gelohnt hat, und ohne sie kann Phase 4 ein Dokument, das
niemand angesehen hat, nicht von einem unterscheiden, das durch die Engine ging
und nichts hergab.

Die Marke wird überschrieben und nicht akkumuliert. Das verlangt vom Aufrufer
eine Entscheidung, und der Umbenennungspfad trifft sie ausdrücklich: er schreibt
ein Verdikt, das er nicht selbst erzeugt hat, liest den gespeicherten Wert und
reicht ihn weiter. Ohne diese Zeile würde die aufgewendete Engine-Zeit an dem Tag
aus dem Zustand verschwinden, an dem jemand die Datei in einen anderen Ordner
schiebt.

## Verifikation

| Gate | Ergebnis |
|---|---|
| `uv run python -m pytest -q` (Host) | 588 passed, 6 skipped |
| gesamte Suite im Container, echte Engine | 594 passed, 0 skipped |
| `tests/test_poller.py` im Container | 53 passed, 0 skipped (Host: 52 passed, 1 skipped) |
| `tests/test_sandbox.py` + `tests/test_ocr.py` im Container | 41 passed, 0 skipped |
| `uv run ruff check .` / `ruff format --check .` | Exit 0, 65 Dateien formatiert |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src tests --min-confidence 80` | Exit 0, keine Ausgabe |
| `grep -n 'def _ask' sandbox.py` | zeigt `timeout_seconds: float \| None = None` |
| `grep -c '_timeout_seconds' sandbox.py` | 3 (gefordert mindestens 2) |
| `grep -c 'def test_group_kill_reaches_a_grandchild'` | 1 |
| `grep -c 'setsid'` / `grep -c 'killpg'` / `grep -c '_WORKER'` | 1 / 1 / 5, `_WORKER` unverändert gegenüber `5ccd595` |
| `grep -c 'OCR = "ocr"' dispatch.py` | 1 |
| `grep -n 'case Route.OCR' -A 4 dispatch.py` | zeigt `from findling.extract import ocr` im `case` |
| `grep -ci 'until then a picture is honestly reported as unsupported'` | 0 |
| `grep -ci 'image' dispatch.py` | 3 |
| `grep -c 'def test_scanned_pdf_is_findable_after_ocr'` | 1 |
| `grep -c 'ocr_used'` repo.py / poller.py | 5 / 8 (gefordert 2 / 1) |
| `grep -c 'etag' repo.py` | 6 (gefordert mindestens 2) |
| `grep -n 'ocr' -A 20 poller.py \| grep -c 'is_unchanged'` | 0 |
| Korpus nach allen Läufen unverändert | `git status --porcelain testdata/` leer |

Der Endnachweis lief im Container wirklich gegen die Engine: `Bebauungsplan`
steht in genau einer Korpusdatei und dort nur als Pixel, und nach einem
`run_once` über eine `kind=ocr`-Zeile liefert eine Suche über `body_de` genau
diese Datei-ID zurück. Das ist Erfolgskriterium 2 der Phase, durch den ganzen
Durchlauf statt auf Modulebene, und ohne dass irgendwo OCR konfiguriert wurde.

## Abweichungen vom Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierendes Problem] Der Allowlist-Rundgang kannte `Route.OCR` noch nicht**

- **Gefunden bei:** Task 2
- **Problem:** `test_every_route_of_the_allowlist_has_an_extractor_behind_it`
  behauptet `set(fixtures) == set(Route)`. Mit der vierten Route wurde diese
  Zusage falsch, obwohl an ihr inhaltlich nichts falsch ist: `Route.OCR` steht
  bewusst in keiner Mimetype-Tabelle.
- **Fix:** Der Vergleich lautet jetzt `set(Route) - {Route.OCR}`, dazu eine
  zweite Behauptung, dass `Route.OCR` in `ALLOWED_MIMETYPES.values()` nicht
  vorkommt. Aus einer Lücke wird damit eine Aussage.
- **Datei:** `backend/tests/test_extract_documents.py`, außerhalb von
  `files_modified` und die einzige solche Datei.

**2. [Rule 1 - Bug] Der Metadaten-Zweig fiel bei der Bearbeitung heraus**

- **Gefunden bei:** Task 3
- **Problem:** Beim Einfügen des OCR-Zweigs in `_handle` verschwand die Zeile
  `if job.kind == KIND_METADATA and await self._rewrite_metadata(...)`.
  Umbenennungen wären danach über den Inhaltsweg gelaufen und vom Schnellpfad
  wirkungslos wegquittiert worden, also genau Pitfall 2.
- **Fix:** Zeile wiederhergestellt, vor dem OCR-Zweig.
- **Bemerkenswert ist, wer es gefunden hat:** vier bestehende Tests aus Plan
  03-04 wurden sofort rot, darunter `test_metadata_job_does_not_fetch_bytes`,
  das genau diesen Rückfall misst. Nichts davon ist in einem Commit gelandet.

**3. [Rule 3 - Blockierendes Problem] Der Containerlauf braucht ein neu gebautes Testimage**

- **Gefunden bei:** Task 3
- **Problem:** Das Abnahmekriterium nennt `docker run ... <image> uv run pytest`.
  Die Images `findling-ocr-08` und `findling-ocr-08-test` aus Plan 03-08 tragen
  in ihrer virtuellen Umgebung den Code von 03-08; die eingehängten Quellen unter
  `/w/backend/src` liegen nicht auf `sys.path`, ein Lauf gegen das alte Image
  hätte also den alten Code geprüft und trotzdem grün gemeldet.
- **Fix:** `findling-ocr-09` aus diesem Arbeitsbaum gebaut, darüber ein
  Wegwerf-Image `findling-ocr-09-test`, das als root `uv` (per Digest, dieselbe
  Version wie im Dockerfile) und die beiden gepinnten Test-Pakete in die
  vorhandene virtuelle Umgebung legt. Gelaufen wird read-only:
  `docker run --rm -v "$PWD:/w:ro" -w /w/backend -e PYTHONDONTWRITEBYTECODE=1 --entrypoint /app/.venv/bin/python findling-ocr-09-test -m pytest -q -p no:cacheprovider`.
- **Nicht eingecheckt:** Das Hilfs-Dockerfile sind vier Zeilen und steht hier
  vollständig genug, um es nachzustellen, so wie in Plan 03-08. Was dauerhaft
  geprüft werden muss, gehört in `.github/workflows`; das ist unten als
  zurückgestellter Punkt notiert.

---

**Summe:** 3 Abweichungen, alle automatisch behoben. Keine Scope-Ausweitung: eine
Testzusage, die durch die neue Route falsch wurde, ein eigener Bearbeitungsfehler
und eine Werkzeugfrage des Containerlaufs.

## Entscheidungen

- **Die erzwungene Route überspringt `judge` vollständig.** Die Alternative wäre,
  `judge` zuerst laufen zu lassen und nur die Routenwahl zu ersetzen. Dann wäre
  "unabhängig vom Mimetype" nicht wahr, sondern "unabhängig vom Mimetype, solange
  er in der Allowlist steht", und der Bildzweig aus Plan 03-10 hinge an einer
  Tabelle, die er nicht braucht. Der Größendeckel bleibt trotzdem wirksam, weil
  er auf dem Gateway-Pfad ein zweites Mal greift; der Docstring sagt das.
- **`sandbox.py` importiert `Route` nicht.** Der Parameter ist als `str | None`
  getippt. `Route` ist ein `StrEnum`, das Element reist als es selbst durch die
  Pipe, und der Elternteil bleibt bei der Regel des Modul-Docstrings, den
  Dispatcher nie zu laden.
- **`ocr_used` wird überschrieben, nicht akkumuliert.** Ein `MAX(files.ocr_used,
  excluded.ocr_used)` wäre bequemer und wäre falsch: eine Datei, die heute ein
  Scan war und morgen durch ein Text-PDF ersetzt wird, behielte die Marke für
  immer. Die Weitergabe steht deshalb dort, wo ein Verdikt wiederholt geschrieben
  wird, und der Kommentar an `_RECORD_SQL` benennt diese Pflicht des Aufrufers.
- **Eine vierte Probe-Art statt eines echten tesseract im Enkel-Test.** Der
  Gegenstand ist die Wache, nicht die Engine. Ein Test, der tesseract braucht, um
  `killpg` zu belegen, wäre auf jeder Maschine ohne Engine übersprungen, und
  gerade dort ist die Prozessdisziplin dieselbe.
- **`ExtractFile` ist offen in seinen Argumenten.** Die drei positionalen
  auszuschreiben und die beiden Schlüsselwörter wegzulassen sähe präzise aus und
  wäre falsch, weil die Namen der Schlüsselwörter der Teil sind, den ein Ersatz
  treffen muss.

## Bekannte Stubs

Keine. Beide Felder, die dieser Plan zum ersten Mal schreibt, werden auch
gelesen: `ocr_used` von den Tests dieses Plans und ab Phase 4 von der
Statusseite, `etag` ab Plan 03-12.

## Zurückgestellt

- **Der Containerlauf gehört auf Dauer in `.github/workflows`.** Plan 03-08 hat
  ihn dieser Nummer zugeschrieben; `.github/workflows/integration.yml` steht aber
  nicht in `files_modified` dieses Plans, und Gate B ist der erklärte Inhalt von
  Plan 03-13. Der Lauf ist hier von Hand belegt (594 passed, 0 skipped) und der
  Befehl ist oben vollständig protokolliert.

## Threat Flags

Keine neue Angriffsfläche außerhalb des Registers. Die sechs Dispositionen sind
umgesetzt:

| Threat | Umsetzung |
|---|---|
| T-03-901 | Harte Deadline im Elternteil plus `killpg` über die Prozessgruppe, Recycling danach; `test_group_kill_reaches_a_grandchild` mit echtem Enkelprozess, im Container tatsächlich gelaufen |
| T-03-902 | Die harte Deadline kommt aus `ocr_hard_deadline_seconds`, also abgeleitet und strikt über der weichen; der Abstand ist an `pipe.poll` und im Poller kommentiert, und ein Test prüft `timeout > ocr_job_seconds` |
| T-03-903 | `_shed_secrets` unverändert; der Enkel erbt eine Umgebung, in der nichts Sensibles mehr steht |
| T-03-904 | Weiterhin genau eine Worker-Fassade, `_WORKER` unverändert fünfmal im Modul; der Docstring von `extract_guarded` sagt jetzt ausdrücklich, dass das auch mit der OCR-Spur so bleibt |
| T-03-905 | Löschung im `finally` auf beiden Zweigen, plus ein Test, der den Extraktor werfen lässt und danach kein `.part` mehr findet |
| T-03-906 | Der OCR-Zweig ist ausschließlich über die Job-Art erreichbar, die nur der Requeue erzeugt; zwei Tests belegen, dass ein PDF mit Textlayer weder im Dispatcher noch im Poller in die Route läuft |

## TDD Gate Compliance

Alle drei Tasks tragen `tdd="true"`, und die Gate-Folge steht im Log:

| Task | RED | GREEN | REFACTOR |
|---|---|---|---|
| 1 | `3731045` (`probe() got an unexpected keyword argument 'timeout_seconds'`) | `be61b3b` | nicht nötig |
| 2 | `42911bb` (`type object 'Route' has no attribute 'OCR'`) | `6b56972` | nicht nötig |
| 3 | `9a03e99` (`assert None is <Route.OCR: 'ocr'>`, `etag` ist `None`) | `cd2c3f6` | nicht nötig |

Jedes RED war rot aus dem beabsichtigten Grund. In Task 1 fehlte der Parameter,
in Task 2 der Enum-Wert, in Task 3 die Route und die beiden Spalten. Eine
Behauptung in Task 1 (`ohne Frist gilt der Standardwert`) war von Anfang an grün,
und das ist Absicht: sie ist der Rückfallschutz für die Aufrufer, die es vor
diesem Plan schon gab.

## Was die nächsten Pläne davon haben

- Plan 03-10 findet die Route, die Fristweitergabe und den `ocr_used`-Vermerk
  fertig vor und muss nur die Bildmimetypes in `ALLOWED_MIMETYPES` aufnehmen und
  `image_not_ocrable` erzeugen. Der Satz im Dispatcher-Docstring, der auf 03-10
  verweist, ist dann anzupassen.
- Plan 03-12 findet `files.etag` gefüllt vor und kann vergleichen, statt zu holen.
- Phase 4 kann `ocr_used` ausweisen und damit sagen, wofür die Zeit draufging,
  auch bei einem Dokument, das nach dem OCR-Lauf leer blieb.

## Self-Check: PASSED

- Alle acht geänderten Dateien stehen in `git diff --name-only 5ccd595..HEAD`.
- Alle sechs Commit-Hashes stehen im Log von `worktree-agent-03-09`.
- Weder `.planning/STATE.md` noch `.planning/ROADMAP.md` sind im Diff.
- `testdata/` ist unverändert, `git status --porcelain testdata/` ist leer.

---

*Phase: 03-aktualit-t-und-ocr, Plan 09*
*Abgeschlossen: 2026-09-01*
