---
phase: 30-owner-tor-schema-und-tschechisch
reviewed: 2026-10-10T14:30:00Z
depth: deep
files_reviewed: 22
files_reviewed_list:
  - .gitattributes
  - .github/workflows/deploy-harp.yml
  - .github/workflows/docker.yml
  - README.md
  - README.en.md
  - README.fr.md
  - REUSE.toml
  - THIRD-PARTY.md
  - backend/Dockerfile
  - backend/appinfo/info.xml
  - backend/src/findling/api/resources.py
  - backend/src/findling/config.py
  - backend/src/findling/index/analyzer.py
  - backend/src/findling/index/open.py
  - backend/src/findling/index/rebuild.py
  - backend/src/findling/index/schema.py
  - backend/src/findling/index/stopwords_cs.py
  - backend/src/findling/query/rewrite.py
  - backend/src/findling/store/repo.py
  - backend/tests/probe_image_ocr_czech.py
  - docs/language-analyzers.md
  - scripts/dev/czech_stopwords.py
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 30: Code-Review-Bericht

**Geprüft:** 2026-10-10
**Tiefe:** deep (Aufrufketten über `open.py`, `rebuild.py`, `repo.py`, `resources.py`, `status.py`, `writer.py`, `poller.py`)
**Umfang:** `git diff cfe0c33a..HEAD` ohne `.planning/`
**Status:** issues_found

## Zusammenfassung

Geprüft wurden der Produktivcode der Phase (Schema 3 mit `body_cs`, Ratsche
`LEGACY_SCHEMA_STEPS`, Lesetor `QUERYABLE_SCHEMA_GENERATIONS`, Kette
`czech_analyzer`, Stoppwortmodul und Generator), das Dockerfile, die beiden
Workflows (Store upgrade 2b bis 7, CZ-01) sowie Doku und Store-Texte. Die bekannten
LOW-Befunde L-30-02 und L-30-03 aus `30-AUDIT.md` werden nicht erneut gemeldet;
für beide wurde kein schwererer Aspekt gefunden.

Kein CRITICAL. Zwei WARNINGs mit Beleg: (1) ein Upgrade auf 1.5 mitten in einem
laufenden Voll-Crawl erhöht die Generation ein zweites Mal und wirft den
Fortschritt weg, obwohl der Schemaschritt laut Ratsche keine Drift ist; (2) der
Bild-Beweis CZ-01 unterscheidet das tschechische Modell nicht vom englischen,
entgegen seiner eigenen Zusicherung. Dazu drei INFO-Punkte.

Gegengeprüft und ohne Befund: Ratsche nur Vorwärtspaare, Lesetor `{"2","3"}` mit
Testbindung `str(SCHEMA_VERSION) in QUERYABLE_SCHEMA_GENERATIONS`
(`test_query_fields_plan.py:215`), Writer und `_document_from` schreiben
`body_cs` nur über `BODY_FIELD`, `may_rebuild`/`_new_language_count` zählen `cs`
korrekt, Statusseite liest `languagesActive` aus der Marke (Schleifenabbruch in
Store upgrade 7 daher nicht verfrüht), Kettenverhalten der Doku-Tabelle
(`proč/už/jsem` -> keine Tokens, `Nájemní smlouva na byt` ->
`najemni, smlouva, byt`, `remove_long(48)`) per Probe bestätigt.

## Warnings

### WR-01: Upgrade auf 1.5 während eines laufenden Voll-Crawls erhöht die Generation erneut

**Datei:** `backend/src/findling/index/open.py:329-338` (ausgelöst durch `backend/src/findling/config.py:57`, `SCHEMA_VERSION = 3`)

**Problem:** `start_rebuild_on_drift` vergleicht den in `state.db` gespeicherten
`REBUILD_MARK` mit `fingerprint(expected)`, und der Fingerabdruck läuft über
ALLE erwarteten Marken, also auch über `schema_version`. Der Schemaschritt 2 auf 3
ist nach `LEGACY_SCHEMA_STEPS` ausdrücklich keine Drift, ändert aber den
Fingerabdruck. Szenario: Eine 1.4.2-Installation steckt in einem Voll-Crawl
(Generation wegen einer echten Drift erhöht, zum Beispiel neue Wortliste,
Analyzer- oder tantivy-Formatwechsel, oder `FINDLING_REBUILD_FALLBACK=fullreindex`).
Der Admin aktualisiert auf 1.5. Beim Start sieht der Poller
(`worker/poller.py:375`) dieselbe Restdrift `wordlist_hash`, aber einen anderen
Fingerabdruck, erhöht die Generation ein zweites Mal und macht damit jedes schon
neu geschriebene Urteil des laufenden Crawls stale. Auf einer OCR-lastigen
Installation sind das Stunden bis Tage Extraktion, die doppelt laufen; genau das,
was Phase 30 zusagt zu vermeiden ("An installation without cs does not rebuild
for it", `config.py:50-56`). Das bestehende Planungsrisiko in 30-RESEARCH
(Zeile 247) betrachtet nur das halb gefüllte Umbauziel (`.rebuild-for`), nicht
den Crawl-Fingerabdruck in `state.db`.

**Beleg** (`uv run python` in `backend/`, Probe im Scratch-Verzeichnis):

```text
1.4.2 raises to 2 mismatch ['wordlist_hash']
1.4.2 again (restart, same code): None
1.5 mismatch: ['wordlist_hash']
the index was built by different code; raised the generation to 3 so the next crawl rebuilds it
1.5 on the same volume mid crawl raises to 3
```

Aufbau: `open_store(meta=...)` mit den Erwartungen von 1.4.2 (Schema `"2"`) und
abweichendem `wordlist_hash`; `start_rebuild_on_drift(..., answered_elsewhere=MARKS_A_REBUILD_ANSWERS)`
erst mit Schema-2-, dann mit Schema-3-Erwartung. Die Positivkontrolle (gleicher
Code, Neustart) liefert korrekt `None`.

**Fix:** Einen gespeicherten Fingerabdruck auch dann als "derselbe Lauf"
gelten lassen, wenn er sich nur in einer entschuldigten Schemamarke
unterscheidet:

```python
from findling.store.repo import LEGACY_SCHEMA_STEPS  # oder ein öffentlicher Helfer

def _fingerprints_of_the_same_run(expected: Mapping[str, str]) -> set[str]:
    current = expected[SCHEMA_MARK]
    variants = {fingerprint(expected)}
    for older, newer in LEGACY_SCHEMA_STEPS:
        if newer == current:
            variants.add(fingerprint({**expected, SCHEMA_MARK: older}))
    return variants

    ...
    wanted = fingerprint(expected)
    stored = store.read_meta().get(REBUILD_MARK)
    if stored == wanted:
        return None
    if stored in _fingerprints_of_the_same_run(expected):
        store.write_meta(REBUILD_MARK, wanted)  # Lauf übernehmen, nicht neu starten
        return None
```

Den `.rebuild-for`-Fingerabdruck des Umbauziels NICHT so lockern: dort ist das
Verwerfen gewollt (anderes Feldlayout im Ziel). Regressionstest nach dem Muster
der Probe oben.

### WR-02: Bild-Beweis CZ-01 ist mit dem englischen Modell genauso grün

**Datei:** `backend/tests/probe_image_ocr_czech.py:20-22`, `:54-56`, `:102-108`; Schritt "Czech OCR in the image (CZ-01)" in `.github/workflows/docker.yml`

**Problem:** Der Docstring sichert zu: "Three of four still rules out a page read
with the wrong model, which comes back as plausible rubbish". Das stimmt nicht.
Die erwarteten Wörter werden erst NACH `czech_analyzer()` verglichen, und die
Kette faltet die Akzente weg. Das englische Modell liest die DejaVu-Zeile als
`Najemni smlouva na byt v Brné, ucetni rizeni, rijen`, also nach der Faltung
dieselben vier Begriffe. Der OCR-Teil beweist damit nur, dass `-l ces` überhaupt
etwas liest, nicht dass das tschechische Modell die Zeichen besser trifft. Ein
späterer Fehler, bei dem `ces` still durch ein anderes Modell ersetzt oder die
Sprache im Aufruf verloren geht, bliebe grün, solange `--list-langs` `ces` nennt.

**Beleg** (im Image `ghcr.io/street1983nk/findling_backend:dev`, erzeugt
2026-10-10T09:50Z, `docker run --network none`, gleiche `_png`/`read_page`/
`czech_analyzer` wie das Skript):

```text
ces 4 ['smlouva', 'ucetni', 'rizeni', 'rijen'] PASS
eng 4 ['smlouva', 'ucetni', 'rizeni', 'rijen'] PASS
deu 2 ['smlouva', 'ucetni'] fail
deu+eng+fra 2 ['smlouva', 'ucetni'] fail
spa 2 ['smlouva', 'ucetni'] fail

ces 'Nájemní smlouva na byt v Brně, účetní řízení, říjen'  has r-caron: True  e-caron: True
eng 'Najemni smlouva na byt v Brné, ucetni rizeni, rijen'  has r-caron: False e-caron: False
```

**Fix:** Zusätzlich den ROHTEXT vor der Faltung prüfen, und zwar auf Zeichen, die
nur ein Modell mit tschechischem Zeichensatz ausgeben kann, zum Beispiel:

```python
raw = read_page(_png(font_path), "ces", PAGE_SECONDS)
czech_letters = sum(raw.count(ch) for ch in "řěůčš")
ok = listed and len(found) >= REQUIRED_HITS and czech_letters >= 3 and not blank
print(f"czech page: {czech_letters} letters only the ces model writes")
```

Optional als Gegenprobe denselben Streifen mit `eng` lesen und verlangen, dass
dort `ř` fehlt (Positivkontrolle der Trennschärfe). Den Satz im Docstring an das
tatsächlich Bewiesene anpassen.

## Info

### IN-01: Veraltete Zählungen und Aussagen in Kommentaren nach dem siebten Körperfeld

**Dateien:**
- `backend/src/findling/index/rebuild.py:203-204`: "the six body fields exist in every build"; seit Schema 3 sind es sieben, und ein Schema-2-Verzeichnis unter 1.5 hat gerade NICHT alle Felder des Builds.
- `backend/Dockerfile:294-295` und `:300`: "it makes the six languages available" und "The analyzer chain of the index is untouched by all of this and stays German and English"; seit 30-02/30-04 sind es sieben Zusatzpakete, und es gibt eine `cs`-Kette im Index.
- `backend/src/findling/index/open.py:177`: "every installation that does not run all six languages".
- `backend/src/findling/api/resources.py:95`, `:159`, `:967`, `:982`: "six chains", "all six".

**Problem:** Kein Laufzeitfehler, aber die Kommentare tragen in diesem Projekt
die Begründungen; die Aussage in `rebuild.py:203` ist für die Schema-2-unter-
Schema-3-Lage sachlich falsch.
**Fix:** Zahlen auf sieben bzw. "every body field of this build" umstellen, im
Dockerfile den Satz zur Analysekette auf "German and English by default, Czech
since 1.5 as its own setting" ändern.

### IN-02: `STEMMERLESS_LANGUAGES` steuert nichts, nur Tests lesen es

**Datei:** `backend/src/findling/config.py:186`

**Problem:** `grep` über `backend/src` findet die Konstante nur an ihrer
Definition; gelesen wird sie ausschließlich in
`backend/tests/test_language_allowlist.py:40-125`. Die Registrierung der Kette
ist in `open.py:199` (`TOKENIZER_CS`, `czech_analyzer()`) und `schema.py:190` von
Hand verdrahtet. Ein zweiter Eintrag in der Menge würde den Test
`set(SUPPORTED_LANGUAGES) == snowball | STEMMERLESS_LANGUAGES` bestehen lassen,
ohne dass irgendwo eine Kette oder ein Feld entsteht; erst `add_document` fiele
dann still (Writer-Kommentar `writer.py:320-322`).
**Fix:** Entweder als reine Testinvariante in den Test verschieben, oder einen
Test ergänzen, der für jeden Code der Menge eine registrierte Kette und ein
Schemafeld mit passendem Tokenizer verlangt.

### IN-03: Doku überzeichnet den Ausweg für Inhaltswörter auf der Stoppliste

**Datei:** `docs/language-analyzers.md`, Abschnitt "Czech content words on the stop word list" ("on an instance that also runs `de` or `en`, those chains still index the word")

**Problem:** Für `de` gilt das nur in der akzentuierten Schreibweise, weil die
deutsche Kette tschechische Akzente nicht faltet. Auf `de,cs`, der Menge, die die
Doku selbst empfiehlt und die der CI-Beweis fährt, findet die akzentlose Frage
`zpravy` oder `prvni` ein Dokument mit `zprávy`/`první` über keinen Körperteil:
`body_cs` verwirft das Wort, `body_de` hält es nur mit Akzent.

**Beleg** (`uv run python` in `backend/`):

```text
'zprávy první smlouvě' de ['zprávy', 'první', 'smlouvě'] en ['zpravi', 'prvni', 'smlouv'] cs ['smlouve']
'zpravy prvni'         de ['zpravy', 'prvni']            en ['zpravi', 'prvni']           cs []
```

**Fix:** Den Satz präzisieren: "`en` indexes the word in both spellings, `de` only
as written with its accents; on `de,cs` a question without accents finds it
through no body field."

---

_Geprüft: 2026-10-10_
_Prüfer: Claude (gsd-code-reviewer)_
_Tiefe: deep_
