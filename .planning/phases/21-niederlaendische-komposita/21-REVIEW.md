---
phase: 21-niederlaendische-komposita
reviewed: 2026-09-25T15:30:00Z
depth: standard
files_reviewed: 40
files_reviewed_list:
  - .github/workflows/deploy-harp.yml
  - .github/workflows/docker.yml
  - backend/src/findling/api/resources.py
  - backend/src/findling/index/analyzer.py
  - backend/src/findling/index/bench.py
  - backend/src/findling/index/open.py
  - backend/src/findling/index/rebuild.py
  - backend/src/findling/index/schema.py
  - backend/src/findling/index/wordlist_nl.py
  - backend/src/findling/store/repo.py
  - backend/src/findling/tools/index_status.py
  - backend/src/findling/tools/one_load.py
  - backend/src/findling/worker/poller.py
  - backend/tests/conftest.py
  - backend/tests/fixtures/compound_cases_nl.txt
  - backend/tests/fixtures/constituents_nl.txt
  - backend/tests/test_dutch_analyzer.py
  - backend/tests/test_index_open.py
  - backend/tests/test_index_rebuild.py
  - backend/tests/test_index_status.py
  - backend/tests/test_language_analyzers.py
  - backend/tests/test_language_proof_steps.py
  - backend/tests/test_measurement_scripts.py
  - backend/tests/test_poller.py
  - backend/tests/test_read_side.py
  - backend/tests/test_readonly_gate.py
  - backend/tests/test_store_repo.py
  - backend/tests/test_upgrade_compatibility.py
  - backend/tests/test_wordlist_nl.py
  - docs/dutch-analyzer.md
  - docs/language-analyzers.md
  - docs/measurements/2026-09-komposita-nl/README.md
  - docs/measurements/2026-09-komposita-nl/rohdaten/fixture-subset.txt
  - docs/measurements/2026-09-komposita-nl/rohdaten/kennzahlen.txt
  - docs/measurements/2026-09-komposita-nl/rohdaten/ram.txt
  - docs/measurements/2026-09-komposita-nl/rohdaten/tokens-rezept-b.tsv
  - docs/performance.md
  - scripts/dev/compound_probe_nl.py
  - scripts/dev/measure_compounds_nl.sh
findings:
  critical: 1
  warning: 2
  info: 5
  total: 8
status: issues_found
---

# Phase 21: Code-Review-Bericht

**Reviewed:** 2026-09-25T15:30:00Z
**Depth:** standard
**Files Reviewed:** 40
**Status:** issues_found

## Summary

Geprüft wurde die niederländische Kompositazerlegung der Phase 21: das neue Modul `wordlist_nl.py`, die Splitterkette in `analyzer.py`, die siebte Marke `wordlist_hash_nl` (open.py, repo.py, index_status.py), der Band-Umbau statt Vollreindex (rebuild.py, poller.py `answered_elsewhere`), die Verdrahtung aller `open_index`- und `expected_versions`-Aufrufer, die CI-Änderungen (nlc-Fall in deploy-harp, wdutch-Gates in docker.yml) sowie Mess-Skripte, Fixtures und Doku. Für Dateien, die nur teilweise von Phase 21 berührt sind, wurde zusätzlich der Diff gegen dd8e4d2 gelesen.

Gesamtbild: Die Marken-Logik (nie geseedet, `_dutch_list_is_legacy` fällt geschlossen, Band-Run beantwortet den Drift, Stamp hinter dem Swap) ist konsistent umgesetzt und ungewöhnlich dicht getestet, inklusive AST-Gates gegen vergessene Aufrufer. Trotzdem gibt es einen kritischen Befund: Ein nicht UTF-8-dekodierbares Dutch-Artefakt auf dem Volume wirft eine `UnicodeDecodeError`, die durch alle Fangnetze fällt und den Container-Start dauerhaft verhindert; das verletzt den eigenen Fail-closed-Vertrag des Moduls und die M-18-06-Invariante ("nie ein Container, der nicht hochkommt"). Dazu zwei Warnungen: ein Race, das zwei niederländische Automaten resident macht, und eine Versorgungslücke, die Plan 21-01 im Enable-Pfad hinterlassen hat.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Korruptes Dutch-Artefakt (invalides UTF-8) verhindert den Container-Start dauerhaft

**File:** `backend/src/findling/index/wordlist_nl.py:148` (dazu `:179-181`, `:216-218`), Kette über `backend/src/findling/api/resources.py:239` und `:1028-1039`, `backend/src/findling/main.py:688` und `:805`, `backend/src/findling/api/status.py:397`
**Issue:** Das Modul verspricht Fail-closed ("trusted only while that digest describes it"), prüft den Digest aber erst NACH dem strikten Dekodieren. Enthält `dict/nl-full.txt` oder `nl-full.txt.sha256` auch nur ein invalides UTF-8-Byte (Bit-Rot, halber Block, Handbearbeitung), wirft `_read_artifact` bzw. `digest_path.read_text` eine `UnicodeDecodeError`, bevor der Digest-Vergleich den Rebuild-Pfad nehmen kann. `_artifact_key` fängt nur `OSError` (Zeile 180-181), `expected_marks` in resources.py fängt nur `OSError` (Zeile 239), `report_version_drift` fängt nur `OSError`/`sqlite3.Error` (Zeilen 1030, 1035). Die Ausnahme erreicht ungefangen `await asyncio.to_thread(resources.report_version_drift)` in main.py:688: der Lifespan bricht ab, der Container startet nicht, und zwar bei jedem Neustart erneut, bis jemand die Datei von Hand löscht. Dieselbe Kette liegt hinter `_rebuild_is_due` (main.py:805, fängt nur `sqlite3.Error`), und die Statusroute (status.py:397, fängt `OSError`/`sqlite3.Error`/`VectorStoreError`) antwortet 500. Nur die Suche überlebt, weil `one_round` jede Ausnahme fängt. Betroffen sind alle Installationen mit aktivem nl. Hinweis: das deutsche Zwillingsmodul (`wordlist.py:181`) trägt dieselbe strikte Lesung, der Befund ist dort vorbestehend; Phase 21 hat mit dem zweiten Artefakt und dem `dutch_mark`-Aufruf in `expected_marks` die Angriffsfläche verdoppelt, statt die Lücke zu schließen.
**Fix:**
```python
# wordlist_nl.py: undecodierbare Bytes sind eine Form von "Artefakt kaputt"
# und nehmen denselben Rebuild-Pfad wie ein falscher Digest.

def _read_artifact(target: Path) -> list[str]:
    return [line for line in target.read_text(encoding=ENCODING, errors="replace").split("\n") if line]

# _artifact_key: den Digest-Read tolerant machen
    try:
        status = target.stat()
        recorded = digest_path.read_text(encoding=ENCODING, errors="replace").strip()
    except OSError:
        return None
```
In `_load_artifact` denselben `errors="replace"`-Read verwenden: ersetzte Bytes ändern den Inhalt, der Digest-Vergleich schlägt fehl, und der Rebuild aus der Quelle läuft wie beim Tamper-Fall. Zusätzlich als zweites Netz `except (OSError, UnicodeDecodeError)` in `resources.expected_marks` und in `report_version_drift`, damit auch der deutsche Zwilling (wordlist.py:181) den Start nie mehr kosten kann. Ein Testfall analog `test_a_tampered_artifact_is_rebuilt_from_the_source`, nur mit `target.write_bytes(b"\xff\xfe\x00kaputt")`, macht den Fix rot-beweisbar.

## Warnings

### WR-01: Kein Lock um den Dutch-Automaten-Cache, zwei Threads bauen zwei 25-MB-Automaten

**File:** `backend/src/findling/index/analyzer.py:426-458` (dazu `:187`, gleiches Muster vorbestehend bei `_CACHED_GERMAN:373-386`)
**Issue:** `cached_dutch_analyzer` und `dutch_chain_for` machen Check-then-act auf `_CACHED_DUTCH` ohne Lock, und die Baustrecke zwischen Miss und Insert ist 0,75 bis 0,8 s lang (gemessen, ram.txt). Die Leseseite öffnet unter `resources._LOCK`, der Poller (`_open_writer`) und der Band-Run (`transfer_documents`) öffnen in eigenen Threads ohne dieses Lock. Treffen zwei Öffnungen im Startfenster zusammen, verfehlen beide den Cache und bauen je einen Automaten; der Verlierer bleibt über die Tokenizer-Registrierung seines Index-Objekts referenziert und resident. Das sind bis zu 2 x ~25 MB (plus im gleichen Fenster 2 x deutscher Automat) auf der 4-GB-Box, exakt die Doppellast, die das Modul laut eigener Doku verhindern soll ("never twice for the same list"). Der Test `test_two_openings_with_dutch_build_one_automaton` ist single-threaded und kann das Race nicht sehen; `one_load` misst nur die Engine, nicht die Automaten.
**Fix:** Ein `threading.Lock` in analyzer.py, das Lookup und Build umschließt (Muster von `wordlist_nl._CACHE_LOCK` übernehmen):
```python
_ANALYZER_LOCK = threading.Lock()

def cached_dutch_analyzer(digest: str, constituents: Sequence[str]) -> TextAnalyzer:
    with _ANALYZER_LOCK:
        cached = _CACHED_DUTCH.get(digest)
        if cached is not None:
            return cached
        analyzer = dutch_analyzer(constituents)
        _CACHED_DUTCH.clear()
        _CACHED_DUTCH[digest] = analyzer
        return analyzer
```
Dasselbe für `cached_german_analyzer` (vorbestehend, gleiche Klasse). `dutch_chain_for` sollte den Cache-Lookup unter demselben Lock machen oder direkt an `cached_dutch_analyzer` delegieren.

### WR-02: Nach Plan 21-01 beantwortet ein Enable ohne Neustart einen Sprach-/NL-Drift gar nicht mehr

**File:** `backend/src/findling/worker/poller.py:348-356`, `backend/src/findling/main.py:223-276` und `:803-807`
**Issue:** Der Band-Rebuild wird ausschließlich im Lifespan gestartet (`main.py:805`), und nur wenn `was_enabled` beim Start wahr ist. `enabled_handler` armiert Poller und Reconcile, plant aber keinen Rebuild. Vor Plan 21-01 fing `_open_state` diesen Fall teuer, aber wirksam ab: `start_rebuild_on_drift` hob beim Armieren die Generation, und der Crawl beantwortete den Drift. Seit `answered_elsewhere=MARKS_A_REBUILD_ANSWERS` hebt ein Schema-, Sprach- oder NL-Drift die Generation nicht mehr. Konsequenz: Ein Container, der deaktiviert startet (z. B. Upgrade mit neu gesetztem `FINDLING_LANGUAGES` bei ausgeschalteter App) und dann per `/enabled` aktiviert wird, indexiert los, aber der Drift bleibt bis zum naechsten Container-Neustart unbeantwortet: das reindexRequired-Banner steht, `body_nl`/neue Chains bleiben leer, und keine der beiden Abhilfen (Generation-Raise, Band-Run) läuft. Die Tests der Phase decken nur den Weg über den Start ab.
**Fix:** Entweder im `enabled_handler` (bzw. beim Armieren des Pollers) dieselbe Frage stellen wie der Lifespan und den Rebuild-Task nachziehen:
```python
if enabled and not shared_volume and await asyncio.to_thread(_rebuild_is_due):
    # denselben Task starten wie main.py:806, mit demselben stop_event
```
Oder, falls der Owner den Neustart als dokumentierten Weg festlegt: die Lücke in docs/dutch-analyzer.md ("The rebuild path") und im Banner-Text benennen, damit ein Admin weiß, dass ein Neustart nötig ist. Stillschweigend offen lassen ist die schlechteste der drei Varianten.

## Info

### IN-01: Ein Dutch-Listen-Fehler wird als Drift der DEUTSCHEN Wortliste gemeldet

**File:** `backend/src/findling/api/resources.py:235-241` und `:268-271`
**Issue:** `expected_marks` bündelt `build_artifact()` (deutsch) und `dutch_mark()` (niederländisch) in einem try. Schlägt nur die Dutch-Seite mit `OSError` fehl (fehlende wdutch-Quelle außerhalb des Images, volles Volume beim Artefakt-Schreiben), antwortet `version_drift` mit `[UNPROVEN_WORDLIST]` = `"wordlist_hash"`, und `reindexRequired` auf der Statusseite nennt die falsche Ursache. Auch die Log-Zeile sagt "the constituent list is unavailable" ohne zu sagen, welche.
**Fix:** Zweite Konstante `UNPROVEN_WORDLIST_NL = "wordlist_hash_nl"` und die beiden Aufrufe in getrennte try-Blöcke legen, damit die Meldung die richtige Liste nennt.

### IN-02: Code-Kommentare zitieren die zurückgezogene 17,6-MB-Zahl

**File:** `backend/src/findling/index/analyzer.py:185`, `backend/src/findling/index/open.py:189-190`
**Issue:** Beide Kommentare beziffern den Dutch-Automaten mit "roughly 17.6 MB". docs/performance.md (Nachtrag 25.09.) widerruft genau diese Zahl ausdrücklich ("gilt für das Produkt nicht") und misst 24,2 bis 25,3 MB produktnah. Ein späterer Budget-Rechner, der den Kommentar liest, rechnet 8 MB zu optimistisch.
**Fix:** Beide Stellen auf "24 bis 25 MB (gemessen, docs/performance.md Nachtrag 25.09.2026)" ändern.

### IN-03: deploy-harp: Summary und Kommentare nicht auf fünf Fälle nachgezogen

**File:** `.github/workflows/deploy-harp.yml:1115`, `:1120`, `:1129`
**Issue:** Die Step-Summary-Zeile "es, it, nl and pt each answered on the ordinary search route" zählt den nlc-Fall nicht auf (die Folgezeile erwähnt ihn separat, die Aufzählung bleibt aber falsch), und die Kommentare "-- and the four documents go again" sowie "Leaving four foreign language documents" sprechen weiter von vier, obwohl die Schleifen fünf Dateien hochladen und löschen. Reine Lesbarkeit, keine Logik.
**Fix:** "five cases" bzw. "five documents" in Summary-Zeile und beiden Kommentaren.

### IN-04: dutch_analyzer umgeht die Schutzpfade von snowball_analyzer

**File:** `backend/src/findling/index/analyzer.py:402-414`
**Issue:** `dutch_analyzer` indiziert `FOLDED_STOPWORDS[SNOWBALL_NAME["nl"]]` direkt. `snowball_analyzer` beantwortet einen fehlenden Supplement-Eintrag mit einer benannten `ValueError`; hier wäre es ein nackter `KeyError` ohne Erklärung. Außerdem wird `SNOWBALL_NAME["nl"]` doppelt nachgeschlagen, obwohl `name` schon existiert. Heute unkritisch (der Key existiert, ein Test hält die Kette per AST), aber die beiden Faktoren derselben Kette lesen sich unterschiedlich streng.
**Fix:** `Filter.custom_stopword(list(FOLDED_STOPWORDS[name]))` verwenden und optional dieselbe Fehlermeldung wie in `snowball_analyzer` vorschalten.

### IN-05: DUTCH_CHAIN_VERSION liegt nicht neben der Kette, die es versioniert

**File:** `backend/src/findling/index/wordlist_nl.py:100-105`, `backend/src/findling/index/analyzer.py:137-139`
**Issue:** Der Kommentar über `ANALYZER_VERSION` begründet dessen Ort mit "a version number kept away from the thing it versions is a version number that stops being raised". `DUTCH_CHAIN_VERSION` verletzt genau diese Regel: es steht in wordlist_nl.py, muss aber bei jeder Änderung von `analyzer.dutch_analyzer` steigen. Der Grund (wordlist_nl darf analyzer nicht importieren, D-02) ist nachvollziehbar, und Kommentare auf beiden Seiten plus der AST-Test mildern das Risiko. Es bleibt trotzdem der einzige Versionszähler des Projekts, der nicht neben seinem Gegenstand wohnt.
**Fix:** Mindestens einen Test ergänzen, der bei einer Änderung des `dutch_analyzer`-Filterbaums (Hash über die AST-Kette) rot wird, solange `DUTCH_CHAIN_VERSION` unverändert ist; das macht das "muss steigen" durchsetzbar statt erinnerbar.

---

_Reviewed: 2026-09-25T15:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
