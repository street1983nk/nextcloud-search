---
phase: 02-indexkern-und-volltextsuche
plan: 08
subsystem: extraction
tags: [extraction, pdf, ooxml, opendocument, caps, xxe, zip-slip, tdd]

requires:
  - phase: 02-indexkern-und-volltextsuche
    plan: 05
    provides: errors.py with the closed taxonomy, dispatch.py with the allowlist and cap_text, the extraction child
provides:
  - findling/extract/pdf.py, PDF text with the encryption question asked before pdfium opens the file, page cap and skipped(no_text_layer)
  - findling/extract/office.py, DOCX, PPTX and XLSX with a read only workbook and the cell limit
  - findling/extract/odf.py, ODT, ODS and ODP through zipfile and a hardened lxml parser, without unpacking
  - findling/extract/dispatch.py, every route of the allowlist now reaches an extractor
  - findling/extract/errors.py, two more measured exception classes
affects: [02-04 indexing worker, 03 OCR via skipped(no_text_layer), 02-13 memory protocol]

tech-stack:
  added: []
  patterns:
    - "The cheap library answers the question that decides the verdict, the fast one does the work"
    - "Every C object of a page is closed in a nested finally, because the error path is where closing gets forgotten"
    - "A cap is enforced while reading and ends the loop, so a bounded document is a verdict and never half a text"
    - "A format module raises and never invents a reason; from_exception is the single place that reads exceptions"
    - "A security switch is proven against a counter measurement with a parser built without it"

key-files:
  created:
    - backend/src/findling/extract/pdf.py
    - backend/src/findling/extract/office.py
    - backend/src/findling/extract/odf.py
    - backend/tests/test_extract_documents.py
  modified:
    - backend/src/findling/extract/dispatch.py
    - backend/src/findling/extract/errors.py

key-decisions:
  - "The text layer threshold is counted per page and set to 25 characters, because the document wide 100 of assumption A2 would file the corpus PDF with a real text layer (63 characters) as an OCR candidate"
  - "FileNotDecryptedError is deliberately absent from the exception table: from_exception only builds failed verdicts and failed(encrypted) is not a pair the taxonomy has"
  - "One function serves ODT, ODS and ODP, because the words of all three sit in the same two elements"
  - "The page cap produces the same visible state as the character cap, indexed(truncated), instead of a quiet half document"

patterns-established:
  - "Pattern: an order between two libraries is proven by replacing the second one with a call that fails"
  - "Pattern: a resource is proven closed on the error path, not on the happy one"
  - "Pattern: the whole allowlist is walked by one test, so no route can lose its extractor quietly"

requirements-completed: [IDX-06, SRCH-01]

duration: 45min
completed: 2026-08-31
---

# Phase 02 Plan 08: Dokumentformate Summary

**PDF, Office und OpenDocument liefern jetzt Text, und jeder Weg, der schiefgehen kann, endet mit einem Grundcode aus der geschlossenen Liste statt mit einer durchgereichten Ausnahme.**

## Performance

- **Duration:** ca. 45 min
- **Tasks:** 3 von 3
- **Files modified:** 6 (4 neu, 2 geaendert), 922 Zeilen
- **Tests:** 308 bestanden, 1 uebersprungen (POSIX-only), vorher 288; 27 Testfunktionen im neuen Modul

## Accomplishments

- **Die passwortgeschuetzte PDF ist eine Entscheidung, kein Fehlschlag, und das ist bewiesen statt behauptet.** Der Test ersetzt `pypdfium2.PdfDocument` durch einen Aufruf, der beim ersten Kontakt fehlschlaegt; die Datei kommt trotzdem als `skipped(encrypted)` zurueck. Die Reihenfolge ist damit gemessen und nicht nur kommentiert.
- **`skipped(no_text_layer)` entsteht ab dem ersten Indexlauf.** Phase 3 bekommt ihre OCR-Warteschlange geschenkt und braucht keinen vollstaendigen Reindex, nur um zu erfahren, welche Dateien sie betreffen.
- **Kein C-Objekt bleibt offen, auch nicht wenn eine Seite mitten im Dokument wirft.** Der Testfall patcht `get_text_bounded` so, dass er wirft, und besteht darauf, dass Textpage und Page in dieser Reihenfolge geschlossen wurden.
- **Eine Mappe wird ausschliesslich nur-lesend und mit Werten statt Formeln geoeffnet**, und der Test schaut dem Aufruf dabei zu, statt den Quelltext zu lesen. Ueber der Zellgrenze bricht die Schleife ab und liefert `skipped(too_many_cells)`, nie einen halben Text.
- **OpenDocument laeuft ohne odfpy und ohne Auspacken.** Aus dem Archiv wird genau eine Datei gelesen; `extractall` ist im Test durch einen Aufruf ersetzt, der fehlschlaegt, also kann Zip-Slip nicht zurueckkehren.
- **Der XML-Parser ist mit einer Gegenmessung belegt:** dieselbe ODF-Datei liefert durch einen Parser ohne die drei Schalter `TOPSECRET-PASSPHRASE`, durch unseren nicht.
- **Der Dispatcher hat keine offene Stelle mehr.** Ein Test laeuft ueber alle vierzehn Mimetypes der Allowlist und besteht darauf, dass jeder der acht Wege bei einem Extraktor ankommt.

## Task Commits

1. **Task 1: PDF mit vorgeschalteter Verschluesselungserkennung** , RED `87a4d39` (test), GREEN `d081ef3` (feat)
2. **Task 2: OOXML mit Zellobergrenze und Nur-Lese-Mappe** , RED `b911539` (test), GREEN `9da5d25` (feat)
3. **Task 3: OpenDocument ohne odfpy und ohne Auspacken** , RED `541b084` (test), GREEN `2f3ae99` (feat)

## TDD Gate Compliance

Alle drei Aufgaben sind `tdd="true"`, und die Reihenfolge stimmt diesmal auch im Arbeitsablauf: jedes Testmodul wurde zuerst geschrieben und lief nachweislich rot (`ModuleNotFoundError: No module named 'findling.extract.pdf'`, `... .office`, `... .odf`), erst danach entstand die Implementierung. Im Log liegen drei `test`-Commits, jeweils gefolgt von ihrem `feat`-Commit. Ein REFACTOR-Schritt war in keiner Aufgabe noetig.

## Files Created/Modified

- `backend/src/findling/extract/pdf.py` , `extract_pdf`, Verschluesselungsfrage ueber pypdf, Seitenschleife ueber pypdfium2, verschachtelte `finally`-Bloecke, Schwelle je Seite mit Annahme A2 als Begruendung.
- `backend/src/findling/extract/office.py` , `extract_docx` (Absaetze plus Tabellenzellen), `extract_pptx` (Shapes mit Textrahmen), `extract_xlsx` (nur-lesend, Werte statt Formeln, Zellzaehler, `finally`).
- `backend/src/findling/extract/odf.py` , `extract_odf` fuer ODT, ODS und ODP; nur `read()` aus dem Archiv, Namensraum als Konstante, gehaerteter Parser.
- `backend/src/findling/extract/dispatch.py` , fuenf Wege eingetragen, `NotImplementedError` ersatzlos entfernt, Formatmodule weiterhin erst im Routenzweig importiert.
- `backend/src/findling/extract/errors.py` , zwei gemessene Eintraege ergaenzt (`pypdf.errors.EmptyFileError`, `pptx.exc.PackageNotFoundError`) und die Begruendung, warum `FileNotDecryptedError` fehlt.
- `backend/tests/test_extract_documents.py` , 27 Testfunktionen, 32 Faelle: fuenf PDF-Ausgaenge, Ressourcenschluss auf dem Fehlerpfad, Seitendeckel, DOCX-Tabellen, PPTX-Rahmen, Mappenoeffnung, Zellgrenze, drei kaputte Pakete, ODF in Dokumentreihenfolge, XXE mit Gegenmessung, Zip-Slip-Sperre und ein Lauf ueber die gesamte Allowlist.

## Decisions Made

- **Die Schwelle fuer `no_text_layer` zaehlt je Seite und steht bei 25 Zeichen.** Der Plan nennt Annahme A2, "unter 100 Zeichen im ganzen Dokument". Dieser Wert ist mit dem Referenzkorpus unvereinbar: `01-text-layer.pdf` traegt gemessene 63 Zeichen, waere also mit 100 als OCR-Kandidat eingestuft worden, obwohl das RESEARCH dieselbe Datei ausdruecklich als `indexed` fuehrt. Die gemessenen Punkte sind 63 Zeichen auf einer Seite gegen 0 Zeichen auf der gescannten Seite; jede Schwelle dazwischen trennt sie. Je Seite zu zaehlen ist zusaetzlich genau die Form, die der Plan selbst als besser benennt: eine PDF mit einer Deckblattzeile und vierzig Scanseiten faellt jetzt auf die richtige Seite. Der Fehler ist asymmetrisch, deshalb liegt die Schwelle hoch statt niedrig: eine Textdatei faelschlich in die OCR-Schlange zu legen kostet Rechenzeit und liefert am Ende trotzdem den Text, ein Scan faelschlich als `indexed` zu fuehren heisst, dass ihn nie wieder jemand ansieht. Die Zahl und diese Abwaegung stehen im Kommentar an der Konstante, damit Phase 3 dort nachjustieren kann.
- **`FileNotDecryptedError` kommt nicht in die Ausnahmetabelle**, obwohl die Uebergabenotiz aus Plan 02-05 das vorschlug. `from_exception` baut ausschliesslich `failed`-Urteile, und `encrypted` gehoert zu `skipped`: der Eintrag haette keine Ausnahme uebersetzt, sondern im Fehlerbehandler selbst einen `ValueError` ausgeloest. Eine Passwortdatei ist eine Entscheidung, und die faellt dort, wo die Datei geoeffnet wird. Zwei Testfaelle halten beide Haelften fest.
- **Ein Seitendeckel liefert dasselbe sichtbare Ergebnis wie der Zeichendeckel.** Ein abgeschnittenes Dokument, das wie ein vollstaendiges aussieht, ist die teuerste Art von Suchergebnis; `indexed(truncated)` sagt es.
- **Eine Funktion fuer ODT, ODS und ODP.** Der Unterschied zwischen den dreien liegt in dem Teil des Formats, den wir nicht lesen. Drei Funktionen mit identischem Rumpf waeren drei Stellen gewesen, an denen ein Sicherheitsschalter haette fehlen koennen.
- **Der Namensraum steht als Konstante, nicht als Zeichenkettensuche nach `text:p`.** Das Praefix ist in XML frei waehlbar; eine Suche darauf ist eine Wette darauf, dass niemand seine Datei anders schreibt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Die Schwelle aus Annahme A2 haette die eigene Referenzdatei falsch einsortiert**

- **Found during:** Task 1
- **Issue:** `01-text-layer.pdf` liefert gemessen 63 Zeichen. Mit der vorgeschlagenen dokumentweiten Schwelle von 100 Zeichen waere genau die Datei, die das RESEARCH als `indexed` fuehrt und deren erste Planbehauptung "aus dem PDF kommt der Text" lautet, als `skipped(no_text_layer)` geendet.
- **Fix:** Schwelle je Seite (25 Zeichen), mit der vollstaendigen Begruendung, der gemessenen Zahl und der Asymmetrie der Fehlerrichtung im Kommentar an der Konstante. Siehe "Decisions Made".
- **Files modified:** `backend/src/findling/extract/pdf.py`
- **Verification:** Korpusdatei 01 kommt als `indexed`, Korpusdatei 02 als `skipped(no_text_layer)`.
- **Committed in:** `d081ef3`

**2. [Rule 2 - Missing critical] Die Ausnahmetabelle kannte die pypdf- und pptx-Fehler noch nicht**

- **Found during:** Task 1 und Task 2
- **Issue:** `errors.py` ist das Netz an der Prozessgrenze. Ohne Eintrag waere eine entkommene `EmptyFileError` als pauschales `corrupt` gelandet, obwohl "es war nichts zu lesen" auf der Statusseite eine andere Auskunft ist als "der Parser hat sich verschluckt". Bei python-pptx kam hinzu, dass es eine eigene `PackageNotFoundError`-Klasse wirft, die mit der von python-docx nichts zu tun hat.
- **Fix:** zwei gemessene Eintraege ergaenzt (`pypdf.errors.EmptyFileError` zu `empty_file`, `pptx.exc.PackageNotFoundError` zu `corrupt`), beide gegen die echten Ausnahmeobjekte getestet. `errors.py` bleibt dabei ohne Fremdimport, weil die Tabelle qualifizierte Klassennamen vergleicht.
- **Files modified:** `backend/src/findling/extract/errors.py`, `backend/tests/test_extract_documents.py`
- **Verification:** `uv run pytest -q` mit 308 bestandenen Tests; `errors.py` importiert weiterhin nur die Standardbibliothek.
- **Committed in:** `d081ef3`, `9da5d25`

**3. [Rule 3 - Blocking] python-pptx sagt dem Typpruefer nicht, was `has_text_frame` garantiert**

- **Found during:** Task 2
- **Issue:** `shape.text_frame` steht nicht an der Basisklasse, also meldet pyright einen Fehler, obwohl der Zugriff durch `has_text_frame` abgesichert ist. Der naheliegende Ausweg, ein `isinstance`-Test gegen die konkreten Shape-Klassen, haette die Platzhaltertypen verloren, und auf denen steht der meiste Text einer Folie.
- **Fix:** ein eng gefasstes `# pyright: ignore[reportAttributeAccessIssue]` genau an der betroffenen Zeile, mit der Begruendung daneben. Keine neue Abhaengigkeit, keine globale Regelaufweichung; dasselbe Vorgehen wie bei lxml in Plan 02-05.
- **Files modified:** `backend/src/findling/extract/office.py`
- **Verification:** `uv run pyright` mit 0 Fehlern, `ruff` ohne Befund.
- **Committed in:** `9da5d25`

### Abweichungen von den Abnahmekriterien

**4. Kein CI-Lauf moeglich.** Alle fuenf Gates liefen lokal auf Windows 11, Python 3.13.13: `pytest` (308 bestanden, 1 uebersprungen), `ruff check`, `ruff format --check`, `pyright` (0 Fehler), `vulture` (kein Befund). Der uebersprungene Fall ist der `RLIMIT_AS`-Test aus Plan 02-05, der POSIX braucht. Der GitHub-Actions-Lauf steht aus und wird nicht simuliert.

**5. Der Dispatcher bekam zwei Hilfsfunktionen statt eines einzigen `match`-Blocks.** Acht Wege mit je eigenem verzoegerten Import in einer Funktion waeren ein Block gewesen, in dem der Import eines Formats leicht in den falschen Zweig rutscht. `_run_ooxml_route` und `_run_text_route` halten je einen Import fuer ihre Gruppe; die Eigenschaft, dass eine Textdatei nie pypdf oder pdfium laedt, bleibt dabei unveraendert erhalten.

**6. `read_only=True` und `data_only=True` stehen in `office.py` genau einmal, wie gefordert.** Der Modul-Docstring nennt die beiden Schalter deshalb in Worten ("die Nur-Lese-Schaltung", "die Werte-statt-Formeln-Schaltung") statt als Bezeichner. Die Begruendung ist vollstaendig da, die Zaehlung stimmt, und keine Verteidigung wurde dafuer weggenommen.

## Bekannte Grenzen, dokumentiert statt behoben

- **python-docx liefert keine Kopf- und Fusszeilen, keine Fussnoten, keine Textfelder.** Nachlesen ueber `word/header*.xml` und `word/footnotes.xml` waere moeglich und ist nicht Phase 2. Steht als Kommentar im Modul.
- **Tabellen in Tabellen werden nicht durchlaufen.** Dieselbe Grenze, dieselbe Stelle im Kommentar.
- **Legacy-Formate DOC, XLS und PPT** bleiben ausserhalb v1 und landen ueber die Allowlist als `skipped(mime_not_allowed)`.
- **Die Schwelle je Seite ist ungemessen.** Sie trennt die beiden gemessenen Punkte des Referenzkorpus, mehr nicht. Phase 3 hat mit den OCR-Ergebnissen die Daten, um sie zu belegen oder zu verschieben.

## Issues Encountered

- **`ruff` sortierte den Import des noch nicht existierenden Moduls in den falschen Block.** Im RED-Commit meldete `ruff check` I001 fuer `from findling.extract.pdf import extract_pdf`, weil die Datei noch nicht auf der Platte lag; mit dem GREEN-Commit war der Befund verschwunden. Die natuerliche Reihenfolge blieb stehen, statt sie fuer einen Zwischenstand zu verbiegen.
- **`pypdf` gibt bei kaputten Dateien Diagnosetext aus** ("EOF marker not found"), bevor es wirft. Das ist Ausgabe der Bibliothek, kein Log dieses Projekts, und sie enthaelt keinen Pfad.
- **Der Zellgrenzentest senkt die Grenze, statt eine Mappe mit 200.000 Zellen zu schreiben.** Geprueft wird der Zaehler und das Urteil, nicht die Faehigkeit von openpyxl, grosse Dateien zu schreiben. Die Einstellung wird in einem `finally` zurueckgesetzt, damit kein anderer Test eine warme Konfiguration erbt.

## User Setup Required

Keine. Alle Abhaengigkeiten (`pypdf`, `pypdfium2`, `python-docx`, `python-pptx`, `openpyxl`, `lxml`) waren bereits gepinnt; dieser Plan hat keine hinzugefuegt.

## Next Phase Readiness

- **02-04 (Indexer)** ruft weiterhin `extract_guarded(path, mime, size)` und bekommt fuer jeden der acht Wege ein fertiges Urteil.
- **Phase 3 (OCR)** findet ihre Kandidatenliste als `skipped(no_text_layer)` und in `pdf.py` die Schwelle samt Begruendung an genau einer Stelle.
- **02-13 (Memory)** kann sich auf drei durchgesetzte Deckel stuetzen: Zellgrenze, Seitengrenze und Zeichengrenze.

Kein Blocker.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat Models des Plans. Alle sieben Eintraege (T-02-81 bis T-02-87) sind umgesetzt und jeweils mit einem Testfall belegt, die drei sicherheitsrelevanten davon mit einem Test, der ohne die Massnahme nachweislich fehlschlaegt.

## Self-Check: PASSED

Alle sechs angelegten beziehungsweise geaenderten Dateien liegen im Worktree, alle sechs Commit-Hashes stehen im Log von `gsd/agent-02-08`. `git diff --diff-filter=D 5306798 HEAD` ist leer, es wurde also in keinem Commit dieses Plans eine Datei geloescht.

---
*Phase: 02-indexkern-und-volltextsuche*
*Completed: 2026-08-31*
