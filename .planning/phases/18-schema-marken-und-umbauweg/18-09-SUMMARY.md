---
phase: 18-schema-marken-und-umbauweg
plan: 09
subsystem: index
tags: [rebuild, lifespan, poller, ocr, startup-warning, LEX-03, LEX-06]

# Dependency graph
requires:
  - phase: 18-schema-marken-und-umbauweg
    provides: "Plan 18-06: may_rebuild, transfer_documents, counts_match, FINDLING_REBUILD_FALLBACK; Plan 18-07: swap_in, stamp_after_swap, reset_read_side; Plan 18-08: recover_the_index_directories"
  - phase: 14-speicher-und-entlastung
    provides: "_release_when_idle als drittes Vorbild einer langlaufenden Lifespan-Aufgabe, RELEASE_STOP_SECONDS als Vorbild eines Stoppbudgets"
  - phase: 05-lebenszyklus-und-marken
    provides: "armed_marker als Gedaechtnis des Enable, Poller.arm und Poller.silence"
provides:
  - "backend/src/findling/index/rebuild.py mit rebuild_the_index: ein Einstiegspunkt, der die sieben Schritte in dieser Reihenfolge fuehrt, plus rebuild_progress als Prozesswert"
  - "Sechs Antworttexte des Laufs: NOTHING_TO_REBUILD, NO_LIVE_DIRECTORY, FALLBACK_TO_FULL_REINDEX, NOT_ENOUGH_ROOM, RUN_STOPPED_EARLY, RUN_INCOMPLETE, REBUILD_THROUGH"
  - "backend/src/findling/main.py mit der vierten Lifespan-Aufgabe, REBUILD_STOP_SECONDS und dem Aufraeumpfad vor dem Anlegen der Aufgaben"
  - "backend/src/findling/main.py mit warn_on_uncovered_languages: eine Startzeile mit Anzahl statt Sprachcode"
  - "backend/src/findling/config.py mit TESSERACT_NAME und FULL_REINDEX_FALLBACK"
  - "Ratsche auf Baumhash f133d6f5 bei unveraenderten 56 Dateien"
affects: [18-10, 18-11, 18-12]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Der Poller erreicht das Indexpaket als Rueckrufpaar und nie als Import: silence und arm werden hereingereicht, damit index/ den worker/ nicht kennt"
    - "arm() steht im finally und deckt auch die Abweisungen: ein Umbau, der sich selbst verweigert, darf keine Installation stillstellen"
    - "Das Scharfschalten fragt den Enable-Merker, nicht sich selbst: ein waehrend des Laufs abgeschalteter Container bleibt abgeschaltet"
    - "Stoppbudget nach der Abbruchkoernung bemessen: ein Band, nicht ein Lauf"
    - "Fortschritt als Prozesswert nach dem Vorbild von engine_state: eine Funktion liefert den Stand, kein zweiter Zustand auf der Platte"

key-files:
  created: []
  modified:
    - backend/src/findling/index/rebuild.py
    - backend/src/findling/main.py
    - backend/src/findling/config.py
    - backend/tests/test_index_rebuild.py
    - backend/tests/test_main_lifespan.py
    - backend/tests/test_ocr_languages.py
    - backend/tests/test_measurement_scripts.py
    - docs/language-analyzers.md

key-decisions:
  - "Der Einstiegspunkt stellt die Drift selbst fest und beantwortet nur die zwei Marken, die ein Umbau aendern kann (schema_version, languages); ein Wortlisten- oder Tantivy-Drift hat eine andere Abhilfe und wuerde vom Bandlauf nur den alten Text weitertragen"
  - "arm() umschliesst im finally auch die frueh abbrechenden Zweige, weil ein nicht scharfgeschalteter Poller teurer ist als ein unnoetiges Scharfschalten"
  - "_arm_the_poller fragt den Enable-Merker: ein Admin kann waehrend eines Stundenlaufs abschalten, und der Merker ist genau das, was der Disable entfernt"
  - "Die vierte Aufgabe ist keine Schleife: ein Umbau ist die einmalige Antwort auf eine Drift, und die Marken, die er schreibt, halten den naechsten Start davon ab"
  - "REBUILD_STOP_SECONDS = 30.0, bemessen an einem Band plus Reserve und nicht an einem Lauf; der Abbau des Umbaus steht als erster der vier, weil er die Verzeichnisse der anderen drei umbenennt"
  - "Der Aufraeumpfad laeuft im else-Zweig der Volume-Pruefung, also nicht auf einem fremden Volume, und vor dem Anlegen der Indexierungsaufgabe"
  - "Die OCR-Startwarnung laeuft auch auf einem geteilten Volume, weil sie eine Aussage ueber die Umgebung ist und nicht ueber den Bestand"
  - "start_rebuild_on_drift wird genau einmal gerufen, im Rueckfallzweig; die statische Sperrklinke wurde umgedreht und mit Datum begruendet, nicht gruen gemacht"

patterns-established:
  - "Unit-Beleg fuer eine Verdrahtung ueber den Zustand des echten Objekts: der Test baut einen echten Poller, faehrt main._run_the_rebuild und liest poller.armed vor, zwischen und nach den zwei Rueckrufen; nur Poller.silence loescht das Flag und nur Poller.arm setzt es"
  - "Der Dirigent nennt die Bandgroesse am Aufrufpunkt, statt sie der Vorgabe der Funktion zu ueberlassen: eine in die Signaturvorgabe eingefrorene Konstante ist von keinem Test erreichbar"
  - "Wortgrenzen fuer zweibuchstabige Codes, Teilzeichenkette fuer dreibuchstabige Namen: 'de' steckt in 'model', also waere die Teilzeichenkettenpruefung gruen aus dem falschen Grund"

requirements-completed: [LEX-03, LEX-06]

# Metrics
duration: ~75min
completed: 2026-09-24
---

# Phase 18 Plan 09: Der Ausloeser des Umbaus und die OCR-Startwarnung Summary

**Der Umbau bekommt seinen Aufrufer: eine vierte Lifespan-Aufgabe startet nur bei echter Drift, stellt den Poller ruhig, fuehrt Vorpruefung, Bandlauf, Endprobe, Tausch und Stempel in dieser Reihenfolge und schaltet danach wieder scharf; dazu die eine Startzeile, die sagt, dass eine Koerpersprache ohne Scanner dahinter im Index als Rauschen landet.**

## Performance

- **Duration:** ~75 min
- **Completed:** 2026-09-24
- **Tasks:** 3 (Task 1 und 2 je ein atomarer Commit, Task 3 als TDD-Zyklus RED/GREEN, kein Refactor noetig)
- **Files created:** 0, **modified:** 8

## Accomplishments

- **`rebuild_the_index()` fuehrt die sieben Schritte.** Drift feststellen, Rueckfall pruefen, Liveverzeichnis pruefen, Platz pruefen, Poller ruhigstellen, Bandlauf, Endprobe, Leseseite verwerfen, Tausch, Stempel, Poller scharfschalten. Die Reihenfolge ist der Inhalt der Funktion, genau wie eine Ebene tiefer bei `swap_in`, und sie steht als nummerierte Liste im Docstring.
- **Der Poller kommt als Rueckrufpaar herein.** `silence` und `arm` sind Parameter, kein Import: `worker/poller.py` ist schon heute der Aufrufer von `expected_versions`, ein Import in die Gegenrichtung waere ein Kreis. Dasselbe gilt fuer `reset_read_side`, das als dritter Rueckruf hereinkommt, weil die Leseseite aus dem Index liest und nie umgekehrt.
- **`arm()` steht im `finally` und deckt auch die Abweisungen.** Jeder Ausgang dieser Funktion ist der Ausgang aus einem stillgestellten Container. Ein unnoetiges Scharfschalten kostet nichts, ein ausgelassenes kostet eine Installation, die aussieht wie immer und nicht mehr indexiert.
- **Der Rueckfall ist ausloesbar und ist der vorhandene Weg.** `FINDLING_REBUILD_FALLBACK=fullreindex` hebt ueber `start_rebuild_on_drift` die Generation, jedes gespeicherte Verdikt wird schal, das bestehende Reindex-Banner nennt den Befehl. Kein Bandlauf, kein zweites Verzeichnis, und der Test belegt beides: `index_version` um eins hoeher, `index.rebuild` existiert nicht.
- **Die Sperrklinke wurde umgedreht, nicht gruen gemacht.** `test_the_rebuild_never_calls_the_function_that_raises_the_generation` hiess bis heute "nirgends"; sie heisst jetzt `test_the_generation_is_raised_in_the_fallback_branch_and_nowhere_else`, prueft genau einen Aufruf und genau in `rebuild_the_index`, und traegt den Begruendungsabsatz mit Datum. `stamp_after_rebuild` bleibt ganz draussen.
- **Fortschritt als Prozesswert.** `rebuild_progress()` liefert `RebuildProgress(running, documents_carried, documents_total)`, gepflegt zwischen den Baendern und nach dem Vorbild von `engine_state`. Kein Zaehler in `state.db`, der dem Verzeichnis widersprechen koennte, und nach dem Lauf wieder der Ruhezustand, damit kein Banner stehen bleibt.
- **`should_stop` zwischen zwei Baendern.** Der Bandlauf fragt vor jedem Band, ob der Container heruntergefahren wird, und bricht dort ab, wo Abbrechen nichts kostet: hinter dem Commit des letzten Bandes. Ein so beendeter Lauf tauscht nicht ein und haelt sein halb gefuelltes Verzeichnis fuer den naechsten Start.
- **Die vierte Lifespan-Aufgabe.** Gebaut nach `_release_when_idle` bis in die Fehlerbehandlung: `asyncio.create_task`, `asyncio.to_thread` fuer die ganze blockierende Arbeit, `except asyncio.CancelledError: raise` vor dem allgemeinen Zweig, und der allgemeine Zweig loggt nur `type(error).__name__` mit dem Satz, dass Suche und Indexierung weiterlaufen.
- **Drei Bedingungen vor dem Anlegen.** Die Marken muessen es verlangen (in einem Worker-Thread gefragt), das Volume muss diesem Container gehoeren, und der Container muss scharfgeschaltet sein. Je ein Lifespan-Fall belegt jede der drei.
- **`REBUILD_STOP_SECONDS = 30.0` mit Begruendung.** Ein Band ist die Abbruchkoernung, also ist das Budget ein Band plus Reserve und nie ein ganzer Lauf. Der Abbau des Umbaus steht als erster der vier im `finally`, weil er der einzige ist, der die Verzeichnisse der anderen drei umbenennt.
- **Der Aufraeumpfad hat seinen Aufrufer.** `recover_the_index_directories()` laeuft per `to_thread` vor dem Anlegen der Indexierungsaufgabe; ein Test faehrt die Reihenfolge als Journal (`["clean up", "poller"]`).
- **Der Beleg fuer die echte Verdrahtung (Pruefer-Hinweis).** `test_the_rebuild_hands_the_real_silence_and_arm_of_the_poller_into_the_run` baut einen echten `Poller` ueber `default_poller()`, setzt ihn als `main._POLLER`, faehrt `main._run_the_rebuild` und liest `poller.armed` vor, zwischen und nach den zwei Rueckrufen: `True -> False -> True`. Nur `Poller.silence` loescht dieses Flag und nur `Poller.arm` setzt es, also ist die Lesefolge der Beweis. Gegenprobe gefahren: mit einem zur Nulloperation gemachten `_silence_the_poller` faellt genau dieser Fall rot.
- **Die OCR-Startwarnung.** `TESSERACT_NAME` in `config.py` ist die geschlossene Umkehrung der zwei vorhandenen Listen, `warn_on_uncovered_languages()` steht in `main.py` an derselben Stelle wie `report_version_drift`, nennt die Anzahl und nie einen Code, und verweigert nichts: ein Lifespan-Fall startet den Container mit `de,en,es` gegen `deu+eng`, bekommt die Zeile und dennoch 200 auf `/heartbeat`.
- **Doku.** `docs/language-analyzers.md` erklaert die Kombination der zwei Einstellungen, die stille Falle dahinter und das Beispiel fuer Spanisch mit beiden Variablen.
- **Ratsche bewegt.** `PACKAGE_FILES_TODAY` bleibt 56, `PACKAGE_TREE_HASH_TODAY = f133d6f5...`, Kommentarkette um den fuenfundzwanzigsten Absatz erweitert, der `index/rebuild.py`, `main.py` und `config.py` nennt.
- Volle Suite **2700 passed / 15 skipped**, alle vier Gates gruen.

## Task Commits

1. **Task 1: ein Einstiegspunkt, der die sieben Schritte fuehrt** - `d5e2c58` (feat)
2. **Task 2: die vierte Lifespan-Aufgabe und der Aufraeumpfad davor** - `7c899e6` (feat)
3. **Task 3 RED: die Koerpersprachen gegen die OCR-Sprachen, fuenf fallende Faelle** - `5b4544e` (test)
4. **Task 3 GREEN: die Startwarnung, TESSERACT_NAME, Doku und Ratsche** - `ca4a39b` (feat)

## Files Created/Modified

- `backend/src/findling/index/rebuild.py` (624 auf 887 Zeilen) - `MARKS_A_REBUILD_ANSWERS`, `_CARRIED_WITHOUT_A_MARK`, sechs Antwortkonstanten, `RebuildProgress` mit `rebuild_progress()` und `_note_progress()`, `_new_language_count()`, `rebuild_the_index()`; `transfer_documents` bekam `should_stop` und pflegt den Fortschrittswert; Modulkopf auf den neuen Dirigenten umgeschrieben.
- `backend/src/findling/main.py` (569 auf 815 Zeilen) - `REBUILD_STOP_SECONDS`, `_silence_the_poller()`, `_arm_the_poller()`, `_rebuild_is_due()`, `_run_the_rebuild()`, `_rebuild_the_index_directory()`, `warn_on_uncovered_languages()`; im Lifespan der Aufruf des Aufraeumpfads, die Startwarnung, das Anlegen der vierten Aufgabe und ihr Abbau als erster im `finally`.
- `backend/src/findling/config.py` - `TESSERACT_NAME` (sechs Eintraege, Umkehrung von `SUPPORTED_LANGUAGES` gegen `OCR_LANGUAGE_ALLOWLIST`) und `FULL_REINDEX_FALLBACK` als Name der zweiten Schalterstellung.
- `backend/tests/test_index_rebuild.py` (1045 auf 1324 Zeilen) - Abschnitt "the one entry point, and the order it leads" mit sieben Faellen, den Helfern `_Hands` und `_a_volume_that_asks_for_a_rebuild`, dazu die umgedrehte Sperrklinke und der Helfer `_called_names`.
- `backend/tests/test_main_lifespan.py` (424 auf 755 Zeilen) - Abschnitt zur vierten Aufgabe mit acht Faellen, darunter der Verdrahtungsbeleg gegen den echten Poller und der statische Gate auf `to_thread` und die Reihenfolge der zwei `except`-Zweige.
- `backend/tests/test_ocr_languages.py` (139 auf 284 Zeilen) - Abschnitt "the body languages against the OCR languages" mit fuenf Faellen inklusive gestellter Probe fuer eine siebte Koerpersprache.
- `backend/tests/test_measurement_scripts.py` - fuenfundzwanzigster Absatz der Kommentarkette, neuer Baumhash bei unveraenderten 56 Dateien.
- `docs/language-analyzers.md` (320 auf 344 Zeilen) - drei Absaetze zur Kombination der zwei Sprachvariablen, vor "`body_de` is stored whatever the set says".

## Decisions Made

- **Der Einstiegspunkt stellt die Drift selbst fest, beantwortet aber nur zwei Marken.** `MARKS_A_REBUILD_ANSWERS` ist `{schema_version, languages}`, weil genau die zwei durch den Lauf wahr werden. Ein bewegter Wortlisten-Hash, eine bewegte Analyzer-Version und ein bewegtes Tantivy-Banner sind echte Unterschiede mit anderer Abhilfe: sie brauchen die Dokumente neu gelesen, und der Bandlauf traegt den alten Text weiter.
- **`_new_language_count` liest die gespeicherte Sprachmarke.** Fehlt sie, gilt das Paar `("de", "en")`, weil keine Ausgabe bis 1.2.0 ein Koerperfeld ausserhalb dieses Paares schreiben konnte. Die zweite Schreibweise neben `repo.LEGACY_LANGUAGES` haelt ein Testfall zusammen, genau wie beim Schemaschluessel; importiert wird sie nicht, weil der Umbau aus dem Store-Paket genau zwei Namen nehmen darf.
- **Der Dirigent nennt die Bandgroesse am Aufrufpunkt.** Als `band_documents` nur die Signaturvorgabe war, war `BAND_DOCUMENTS` fuer keinen Test des echten Laufs erreichbar: die Vorgabe wird beim `def` gebunden. Jetzt steht die Zahl am Aufrufpunkt, wo ohnehin die Entscheidung liegt (Speicher eines Schritts und Absturzkoernung des Laufs).
- **`_arm_the_poller` fragt den Enable-Merker.** Ein Umbau laeuft Stunden, ein Admin kann in dieser Zeit abschalten, und der Disable entfernt genau diesen Merker. Ohne die Bedingung kaeme der Container mit indexierendem Poller aus dem Umbau, waehrend Nextcloud die App als aus fuehrt.
- **Die Startwarnung laeuft auch auf einem geteilten Volume.** Aufraeumpfad und Driftbericht sind Aussagen ueber einen Bestand, der dort einer anderen Instanz gehoert; die Sprachwarnung ist eine Aussage ueber die Umgebung dieses Containers und stimmt unabhaengig davon, wem der Index gehoert.
- **Die Warnung geht durch `to_thread`, obwohl sie nur die Einstellungen liest.** Der Grund steht als Satz daneben: drei Startaussagen in einer Reihe, von denen eine anders geformt ist, sind eine Frage, die jeder spaetere Leser stellen und beantworten muss, und das kostet mehr als der Thread-Sprung.
- **Die vierte Aufgabe endet, statt zu ticken.** Ein Umbau ist die einmalige Antwort auf eine Drift. Der Stempel am Ende ist es, der den naechsten Start davon abhaelt, und eine Schleife haette einen zweiten Ort gebraucht, an dem "fertig" definiert wird.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `BAND_DOCUMENTS` war fuer den Test des echten Laufs unerreichbar**
- **Found during:** Task 1, beim ersten roten Lauf der Fortschritts- und Stoppfaelle
- **Issue:** `transfer_documents(..., band_documents: int = BAND_DOCUMENTS)` bindet die Konstante beim `def`, also wirkte `monkeypatch.setattr` auf das Modulattribut nicht, und beide Faelle liefen mit einem einzigen Band von 500 Dokumenten.
- **Fix:** `rebuild_the_index` uebergibt `band_documents=BAND_DOCUMENTS` ausdruecklich, mit dem Satz daneben, warum der Dirigent diese Zahl nennt.
- **Files modified:** `backend/src/findling/index/rebuild.py`
- **Commit:** `d5e2c58`

**2. [Rule 2 - Missing critical functionality] Das Scharfschalten haette einen abgeschalteten Container wieder indexieren lassen**
- **Found during:** Task 2, beim Schreiben von `_arm_the_poller`
- **Issue:** Der Plan sagt "Poller scharfschalten" ohne Bedingung. Ein Umbau laeuft Stunden; wird die App in dieser Zeit abgeschaltet, haette das `arm()` im `finally` einen Backend wieder indexieren lassen, das Nextcloud als aus fuehrt.
- **Fix:** `_arm_the_poller` fragt `_was_enabled_before_this_start()`, also den Merker, den der Disable entfernt; ein eigener Testfall belegt, dass ohne Merker nicht scharfgeschaltet wird.
- **Files modified:** `backend/src/findling/main.py`, `backend/tests/test_main_lifespan.py`
- **Commit:** `7c899e6`

**3. [Rule 3 - Blocking] Zweite Schreibweise der Schalterstellung `fullreindex`**
- **Found during:** Task 1
- **Issue:** `rebuild.py` haette die Zeichenkette ein zweites Mal buchstabieren muessen; eine falsch geschriebene zweite Schreibweise trifft nie zu, also waere der Rueckfallweg unerreichbar und nichts wuerde es sagen.
- **Fix:** `FULL_REINDEX_FALLBACK` in `config.py`, `REBUILD_FALLBACK_POSITIONS` baut darauf auf; `test_config.py` haelt die Positionsliste unveraendert.
- **Files modified:** `backend/src/findling/config.py`
- **Commit:** `d5e2c58`

### Geplante Abweichung mit Auftrag

- **Die statische Sperrklinke auf `start_rebuild_on_drift` wurde umgedreht.** Der Plan nennt den einen erlaubten Aufruf ausdruecklich ("die einzige Stelle der Phase"), also war der rote Lauf dieses Falls eine Aufforderung und kein Defekt. Umgesetzt nach dem Muster, das die Recherche fuer die Upgrade-Sperrklinke vorgibt: neuer Name, Begruendungsabsatz mit Datum, schaerfere Zusicherung (genau ein Aufruf, genau in `rebuild_the_index`) statt einer weicheren.

### Zusatz aus dem Pruefer-Hinweis

- **Unit-Beleg fuer die echte Verdrahtung.** Die Task-2-Kriterien pruefen nur Anlegen und Abbau der Aufgabe, und die Faelle in `test_index_rebuild.py` reichen naturgemaess eigene Rekorder herein. Ein Paar Rueckrufe, das ins Leere geht, saehe in beiden Suiten genau wie ein funktionierendes aus: der Umbau traegt alles herueber, die Zahlen stimmen, der Tausch gelingt, und der einzige Unterschied waeren die Dokumente, die der Poller in der Zwischenzeit in das Quellverzeichnis geschrieben hat. Deshalb der zusaetzliche Fall gegen den echten `Poller` samt Gegenprobe.

## Was dieser Plan ausdruecklich nicht tut

- **Kein Statusfeld und keine Adminanzeige.** `rebuild_progress()` und die Namen der nicht abgedeckten Sprachen haben hier keinen Leser ausser dem Test; `GET /status` und die Adminseite baut Plan 18-10.
- **Kein Kanarienvogel fuer die Suche waehrend des Laufs.** Dass die Suche waehrend des Umbaus weiter antwortet, folgt aus dem Aufbau (der Tausch sind zwei Umbenennungen, die Leseseite wird genau davor verworfen) und wird in Plan 18-12 als CI-Zusicherung gemessen.
- **Keine Aenderung am Poller.** `arm` und `silence` sind unveraendert; der Umbau ruft sie, er baut sie nicht um.
- **Kein Neubau des Driftberichts.** `report_version_drift` bleibt wie er ist; die vierte Aufgabe stellt ihre Frage selbst und ueber eine engere Markenmenge.

## Threat-Dispositionen

| Threat ID | Umsetzung |
|---|---|
| T-18-09-01 | `silence()` steht vor dem ersten geschriebenen Dokument, `arm()` hinter dem Stempel; das Journal eines echten Laufs belegt `["silence", "document", "drop_read_side", "stamp", "arm"]`, und der Verdrahtungsfall belegt dieselben zwei Aufrufe am echten Poller |
| T-18-09-02 | `except asyncio.CancelledError: raise` vor dem allgemeinen Zweig (statisch geprueft), allgemeiner Zweig loggt nur den Typnamen und sagt, dass das alte Verzeichnis steht und Suche und Indexierung weiterlaufen |
| T-18-09-03 | `REBUILD_STOP_SECONDS` an einem Band bemessen, `wait_for` plus `cancel` plus `gather(return_exceptions=True)` wie bei den drei vorhandenen Aufgaben; ein Fall misst die Abbauzeit gegen das Budget |
| T-18-09-04 | Die Warnzeile nennt die Anzahl; zwei Faelle lesen sie und finden keinen der sechs Codes als Wort und keinen der neun tesseract-Namen als Teilzeichenkette |
| T-18-09-05 | Die vierte Aufgabe wird auf einem geteilten Volume nicht angelegt (dieselbe Bedingung wie fuer die Indexierung), der Aufraeumpfad laeuft dort ebenfalls nicht |
| T-18-09-06 | `warn_on_uncovered_languages` im Lifespan, eine Zeile je Start; die Namen folgen in Plan 18-10 ueber die ADMIN-Route |
| T-18-09-SC | Kein Paket installiert |

## Verification

- `uv run pytest -q` - 2700 passed, 15 skipped
- `uv run pytest -q tests/test_index_rebuild.py` - 47 passed
- `uv run pytest -q tests/test_main_lifespan.py tests/test_lifecycle.py` - 52 passed
- `uv run pytest -q tests/test_ocr_languages.py` - 8 passed
- `uv run pytest -q tests/test_measurement_scripts.py` - 376 passed
- `uv run ruff check` - All checks passed
- `uv run ruff format --check` - 133 files already formatted
- `uv run pyright` - 0 errors, 0 warnings, 0 informations
- `uv run vulture` - keine Meldung
- `40b-baumhash.py backend/src/findling "**/*.py"` - `dateien: 56`, `baumhash: f133d6f5c3bfe451fbf62fb1bbd57a887f3ec3647318b4a3a20a11974b5ddc5b`
- must_haves: `REBUILD_STOP_SECONDS` zweimal ausserhalb der Kommentare in `main.py` (Definition und Abbau), `.silence()` in `main.py` vorhanden, `to_thread` dreizehnmal in `main.py`
- RED-Lauf vor dem GREEN-Commit belegt (ImportError auf `TESSERACT_NAME`)
- Gegenprobe zum Verdrahtungsbeleg gefahren: `_silence_the_poller` zur Nulloperation gemacht, genau der eine Fall faellt rot, Aenderung danach verworfen
- Keine Em-Dashes in `docs/language-analyzers.md` (Zeichenpruefung auf U+2014 und U+2013)

## Known Stubs

Keine im Sinne von leeren Rueckgaben oder Platzhaltertexten. Zwei Funktionen haben heute nur Testleser und einen benannten Produktivleser im Folgeplan: `rebuild_progress()` (Plan 18-10, Fortschritt auf der Adminseite) und die Namen der nicht abgedeckten Sprachen, die dieselbe Route traegt. Beide sind vollstaendig und geprueft; sie sind keine Attrappe, sondern eine Schnittstelle vor ihrem Anzeiger.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat Models des Plans: keine neue Route, kein neues Schema, keine neue Vertrauensgrenze, kein neuer Netzpfad. Die neuen Dateizugriffe sind die des Umbaus (zwei Indexverzeichnisse, zwei Umbenennungen, ein `rmtree` auf einem selbst benannten Pfad), die schon in 18-06 bis 18-08 begutachtet wurden, und eine zweite schreibende SQLite-Verbindung auf die Zustandsdatenbank, die unter WAL serialisiert wird und nur die drei Marken des Stempels schreibt.

## Self-Check: PASSED

- `backend/src/findling/index/rebuild.py` vorhanden (887 Zeilen), enthaelt `def rebuild_the_index` und `def rebuild_progress`
- `backend/src/findling/main.py` vorhanden (815 Zeilen), enthaelt `REBUILD_STOP_SECONDS`, `_rebuild_the_index_directory` und `warn_on_uncovered_languages`
- `backend/src/findling/config.py` enthaelt `TESSERACT_NAME` und `FULL_REINDEX_FALLBACK`
- `docs/language-analyzers.md` vorhanden (344 Zeilen), nennt beide Sprachvariablen nebeneinander
- Commits `d5e2c58`, `7c899e6`, `5b4544e`, `ca4a39b` im Log gefunden
- Keine Datei geloescht (`git diff --diff-filter=D` ueber die vier Commits leer)
- Arbeitsbaum nach dem letzten Task-Commit sauber, ausser der untracked Recherchedatei des parallel laufenden Lesers
