# Phase 17: Owner-Tor und Analyseketten , Musterkarte

**Erstellt:** 2026-09-23
**Dateien analysiert:** 18 (8 neu, 10 geändert)
**Analoga gefunden:** 18 / 18 (kein einziger Fall ohne Vorbild im Baum)
**Eingaben:** `17-RESEARCH.md`. Ein `17-CONTEXT.md` existiert nicht, `discuss-phase` wurde übersprungen; die Dateiliste stammt deshalb aus RESEARCH.md, Abschnitte 3.1, 4.4, 5.2, 6.1 und "Vorgeschlagene Dateien dieser Phase".

---

## Dateiklassifikation

### Neu anzulegen

| Neue Datei | Rolle | Datenfluss | Nächstes Analogon | Passung |
|---|---|---|---|---|
| `backend/tests/test_language_analyzers.py` | test (Tabellentest plus Paritätsgate) | transform | `backend/tests/test_analyzer.py` + `backend/tests/test_ocr_languages.py` | exakt (zwei Hälften, zwei Vorbilder) |
| `backend/tests/fixtures/chain_cases_es.txt` (und it, nl, pt) | fixture | file-I/O | `backend/tests/fixtures/compound_cases_de.txt` | Rollenpassung, Format weicht ab (Formfamilie je Zeile statt Wort je Zeile) |
| `backend/tests/fixtures/chain_known_losses_es.txt` (und it, nl, pt) | fixture | file-I/O | kein direktes Analogon; nächstes Muster ist die Doppelrichtungs-Behauptung in `test_analyzer.py:203-235` (dokumentierte Grenzen als Test) | Teilpassung |
| `scripts/dev/chain_probe.py` | dev-tool (Sonde) | batch/transform | `scripts/dev/compound_probe.py` | exakt |
| `scripts/dev/measure_chains.sh` | dev-tool (Treiber) | batch | `scripts/dev/measure_compounds.sh` | Rollenpassung, **ohne Container** |
| `docs/language-analyzers.md` | docs (Produktdoku) | , | `docs/german-analyzer.md` | exakt |
| `docs/measurements/2026-09-analyseketten/README.md` plus `rohdaten/` | docs (Messbericht) | file-I/O | `docs/measurements/2026-09-komposita-rezept-a/` | exakt |
| `.planning/phases/17-owner-tor-und-analyseketten/17-GRUNDSATZ-ENTSCHEID.md` | planning (Owner-Tor) | , | `.planning/milestones/v1.2-phases/12-messwerkzeug-runbook-und-terminentscheid/12-STABLE35-ENTSCHEID.md` | exakt |

### Zu ändern

| Datei | Rolle | Datenfluss | Analogon für die Änderung | Passung |
|---|---|---|---|---|
| `backend/src/findling/index/analyzer.py` | index core (Kettenfabrik) | transform | dieselbe Datei, `english_analyzer()` Zeilen 182-192 und `german_analyzer()` Zeilen 146-179 | exakt (Selbstanalogon) |
| `backend/src/findling/index/wordlist.py` **oder** neu `index/stopwords.py` | data/constant | , | `FUGEN` (`wordlist.py:95`) plus `wordlist_hash()` (`wordlist.py:143-153`) | exakt |
| `backend/src/findling/config.py` | config | , | `OCR_LANGUAGE_ALLOWLIST` (`config.py:265-292`) plus `_ocr_languages()` (`config.py:1028-1064`) | exakt |
| `backend/pyproject.toml` | config (Pin) | , | die vorhandene Zeile 13 `"tantivy==0.26.0"` | exakt |
| `backend/uv.lock` | lock | , | , (nur `uv lock --upgrade-package tantivy`, nie von Hand) | n/a |
| `backend/tests/test_upgrade_compatibility.py` | test (Ratsche) | , | dieselbe Datei, `GOLD_V1_0_AND_V1_1` Zeilen 42-82 | exakt |
| `backend/src/findling/store/repo.py` | store (Vergleichsregel) | , | `Store.version_mismatch()` Zeilen 631-669, die `index_version`-Ausnahme ist das Präzedenzmuster | exakt |
| `.github/workflows/deploy-harp.yml` | CI | , | Job "Store upgrade 5", Zusicherung 2, Zeilen 3288-3291 | exakt |
| `.github/dependabot.yml` | config | , | **Der `ignore`-Eintrag für tantivy existiert bereits** (Zeilen am Dateiende). Siehe Befund unten. | n/a |
| `THIRD-PARTY.md` | docs (Lizenzliste) | , | Zeile 139 plus Begründungsabsatz Zeilen 150-155 | exakt |

---

## Musterzuweisungen

### `backend/src/findling/index/analyzer.py` (index core, transform)

**Analogon:** dieselbe Datei. Die neue Fabrik steht zwischen `english_analyzer()` und `name_analyzer()`.

**Importmuster** (Zeilen 56-66), unverändert übernehmen und nur die neue Konstante ergänzen:

```python
import gc
import logging
import time
import unicodedata
from collections.abc import Sequence
from pathlib import Path

from tantivy import Filter, TextAnalyzer, TextAnalyzerBuilder, Tokenizer

from findling.config import DEFAULT_COMPOUND_DICT, settings
from findling.index.wordlist import FUGEN, SYSTEM_WORDLIST, load_constituents, rss_bytes, wordlist_hash
```

**Kettenmuster, das die neue Fabrik kopiert** (Zeilen 182-192). Das ist wörtlich die Kette A aus der Messung, ihr fehlt nur `custom_stopword`:

```python
def english_analyzer() -> TextAnalyzer:
    """Build the English chain: fold, drop stopwords, stem with Porter."""
    return (
        TextAnalyzerBuilder(Tokenizer.simple())
        .filter(Filter.lowercase())
        .filter(Filter.ascii_fold())
        .filter(Filter.stopword("english"))
        .filter(Filter.remove_long(MAX_TOKEN_CHARS))
        .filter(Filter.stemmer("english"))
        .build()
    )
```

**Konstantenmuster mit begründendem Kommentar** (Zeilen 70-90). `LANGUAGE`-nahe Konstanten dieser Phase werden genauso geschrieben: Kommentar erklärt, warum der Wert dort steht, nicht was er ist:

```python
# Raise this whenever a chain below changes. It lives here, next to the chains it
# describes, and not in findling.config, because a version number kept away from
# the thing it versions is a version number that stops being raised.
ANALYZER_VERSION = 1

# The schema stores the NAME of a tokenizer, never the tokenizer. Opening an
# index without registering exactly these names fails at the first parse_query
# with "the tokenizer 'de' for the field 'body_de' is unknown", which reads like
# a broken index and is a missing line of setup. Plan 02-06 reads them from here.
TOKENIZER_DE = "de"
TOKENIZER_EN = "en"
TOKENIZER_NAME = "name"

# Longest token that may reach the index. Generous on purpose: it exists to stop
# base64 blobs and minified assets, not German words.
MAX_TOKEN_CHARS = 48
```

**Modulkopf-Satz, der präzisiert werden muss** (Zeilen 51-53). RESEARCH 6.3 verlangt hier einen Zusatz, damit `ANALYZER_VERSION` nicht aus Vorsicht gehoben wird:

```python
Any change to a chain below has to raise ANALYZER_VERSION. Tokenisation is part
of the data: an index written with one chain and queried with another disagrees
with itself, and the only correct answer to that is a visible reindex.
```

**Tabellenmuster im Modulkopf** (Zeilen 3-22). Die neue Kette bekommt eine gleichartige Tabelle mit einer Zeile je Filterposition und der Spalte "Why exactly here". Nicht kürzen: der Tabellentest in `test_analyzer.py` und die Doku hängen an genau dieser Begründungsform.

**Was NICHT übernommen wird:** das Singleton-Cache-Muster (`_CACHED_GERMAN`, Zeilen 92-102 und 211-224) und der Build-Zähler. Es existiert nur, weil das deutsche Automaton 0,44 s und 23 MB kostet. Die vier Snowball-Ketten sind einkompiliert und kosten nichts; ein Cache dafür wäre Ballast, den `vulture` zu Recht anmeckert.

---

### `backend/src/findling/index/wordlist.py` (oder neu `index/stopwords.py`) , FOLDED_STOPWORDS

**Analogon:** `FUGEN` und `wordlist_hash()` in `backend/src/findling/index/wordlist.py`.

**Konstantenmuster** (Zeile 95):

```python
FUGEN = ("s", "es", "n", "en", "er", "ns")
```

Die Ergänzungsliste ist derselbe Fall eine Größenordnung weiter: ein Tupel je Sprache (77 es, 10 it, 0 nl, 30 pt), ausgeliefert im Code, erzeugt vom Dev-Skript. Der Modulkopf muss sagen, aus welchem tantivy-Tag sie stammt.

**Hash-Muster gegen stilles Driften** (Zeilen 143-153), wörtlich das, was RESEARCH Pitfall 5 verlangt:

```python
def wordlist_hash(entries: Sequence[str]) -> str:
    """Return the SHA-256 of the list, stable across processes and machines.

    Hashing the joined entries rather than the source file is deliberate: what
    changes the tokenisation is the filtered list, not the bytes it came from. A
    Debian point release that only reorders lines must not force a reindex, and a
    changed window must.
    """
    digest = hashlib.sha256()
    digest.update("\n".join(entries).encode(ENCODING))
    return digest.hexdigest()
```

**Achtung Marken-Falle:** `wordlist_hash` ist eine der fünf Versionsmarken (`expected_versions`, `open.py:139`). Ein Hash über die neue Stoppwortergänzung darf **nicht** in dieselbe Marke einfließen und in Phase 17 überhaupt keine Marke werden, sonst fällt Erfolgskriterium 4. Er gehört in einen Test, nicht in `expected_versions()`.

---

### `backend/src/findling/config.py` (config)

**Analogon:** `OCR_LANGUAGE_ALLOWLIST` plus `_ocr_languages()`.

**Positivlisten-Muster** (Zeilen 265-292). Der Kommentar trägt Datum, Messung, Gegenstelle und die Konsequenz eines Alleingangs:

```python
# What the image actually carries, and therefore the only values that may ever
# reach the command line (T-03-502). Measured on 2026-09-01,
# `tesseract --list-langs` in the built image answered deu, eng and osd, ...
#
# This set is maintained together with the apt block in backend/Dockerfile, and
# backend/tests/test_ocr_languages.py compares the two in both directions ...
# Switching on the Fraktur option means uncommenting tesseract-ocr-frk there and
# adding "frk" here, in the same change. Adding it here alone would produce a
# call that tesseract rejects on every page.
OCR_LANGUAGE_ALLOWLIST = frozenset({"deu", "eng", "fra", "spa", "ita", "nld", "por", "dan", "est"})
```

`LANGUAGE_ALLOWLIST` wird genauso geschrieben: `frozenset`, Kommentar nennt die Messung (18 Stemmer, 13 Stoppwortlisten, 5 in der Differenz), die Gegenstelle (das laufende tantivy) und die Folge eines Alleingangs (Panic in 0.26.0, ValueError in 0.26.2).

**Leser-Muster für Umgebungsvariablen** (Zeilen 1028-1064). Struktur: `raw` lesen, leer gleich Default, Schleife mit `kept`/`dropped`, zwei getrennte Warnungen, Rückgabe als Tupel:

```python
    raw = os.environ.get("FINDLING_OCR_LANGUAGES", "").strip()
    if not raw:
        return OCR_DEFAULT_LANGUAGES

    kept: list[str] = []
    dropped = False
    for part in raw.split("+"):
        candidate = part.strip().lower()
        if not candidate:
            continue
        if candidate not in OCR_LANGUAGE_ALLOWLIST:
            dropped = True
            continue
        if candidate not in kept:
            kept.append(candidate)

    if not kept:
        LOGGER.warning("FINDLING_OCR_LANGUAGES names no installed language, falling back to the built in default")
        return OCR_DEFAULT_LANGUAGES
    if dropped:
        LOGGER.warning("FINDLING_OCR_LANGUAGES names a language this image does not carry, ignoring that entry")
    return tuple(kept)
```

**Der bestehende Sprachleser, der erweitert wird** (Zeilen 1002-1015). Er filtert heute gegen `DEFAULT_LANGUAGES` und normalisiert bereits auf Schemafeldreihenfolge. Genau diese Eigenschaft ist in RESEARCH 5.2 der Unterschied zur OCR-Variante und muss erhalten bleiben:

```python
def _languages() -> tuple[str, ...]:
    """Return the active language fields, in schema order.

    An empty or unrecognisable list keeps both fields. Dropping to no language at
    all would produce an index that cannot answer anything, which is a worse
    outcome than ignoring the variable.
    """
    requested = {part.strip().lower() for part in os.environ.get("FINDLING_LANGUAGES", "").split(",")}
    kept = tuple(language for language in DEFAULT_LANGUAGES if language in requested)
    if kept:
        return kept
    if requested - {""}:
        LOGGER.warning("FINDLING_LANGUAGES names no supported language, falling back to the built in default")
    return DEFAULT_LANGUAGES
```

Die vorhandene Konstante steht in Zeile 80 mit genau dem Kommentar, den `SUPPORTED_LANGUAGES` erbt:

```python
# Field order of the schema, not the order somebody types into the environment.
DEFAULT_LANGUAGES = ("de", "en")
```

**Heikel:** `DEFAULT_LANGUAGES` bleibt `("de", "en")` (Werkseinstellung, E-17-3). `SUPPORTED_LANGUAGES` ist die neue, größere Menge. Beide Namen im selben Modul verwechselt ein Leser leicht; der Kommentar muss den Unterschied in einem Satz sagen. Das Feld `Settings.languages` (`config.py:745`, befüllt in Zeile 1116) hängt daran.

---

### `backend/tests/test_language_analyzers.py` (test, transform)

Zwei Hälften mit zwei Vorbildern.

**Hälfte 1, Tabellentest.** Analogon `backend/tests/test_analyzer.py`.

Modulkopf-Muster (Zeilen 1-23), inklusive der Umlautbegründung, die für Akzente wörtlich gilt:

```python
"""The German chain, asserted token by token.

This table asserts WHAT is split, not THAT something was split. The difference is
the whole value of the file: a test that only checks "more than one token came
back" stays green while the splitter produces confetti, ...

Umlauts appear only inside string literals. They are data here, the words the
product has to handle; the identifiers stay ASCII as the project rules require.
"""
```

Fixture-Muster (Zeilen 51-56 und 138-148): Pfadkonstanten oben, Modul-Fixtures, die einmal lesen.

```python
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt"

# The measured case list. Every word this module makes a claim about has to
# stand in here, because a claim about a word that was never fed to the probe is
# a claim about nothing.
CASES = Path(__file__).resolve().parent / "fixtures" / "compound_cases_de.txt"

@pytest.fixture(scope="module")
def constituents() -> list[str]:
    """The measured constituent subset, read once for the whole module."""
    return FIXTURE.read_text(encoding="utf-8").split()
```

Das Gate über dem Gate (Zeilen 237-250), das die Formfamilien-Tabelle an die Messung bindet:

```python
def test_every_asserted_word_stands_in_the_measured_case_list() -> None:
    measured = set(CASES.read_text(encoding="utf-8").split())
    asserted = [text for text, _ in COMPOUNDS] + [text for text, _ in UNSPLIT] + [GRUNDSTUECK_ASCII]

    missing = sorted(word for word in asserted if word not in measured)

    assert missing == [], (
        f"asserted here but never measured, add to {CASES.name} and rerun scripts/dev/measure_compounds.sh: {missing}"
    )
```

**Der Kettenwächter über den AST** (Zeilen 495-540 plus Tests 562-630). Das ist das Muster, das "`ascii_fold` steht vorn" hält, und es ist stärker als jede Tokenbehauptung, weil es die Filterposition benennt statt sie zu erraten:

```python
# The source the guard reads. The file and not the imported module, because a
# built analyser tells nobody in which order it was built.
ANALYZER_SOURCE = PACKAGE_ROOT / "index" / "analyzer.py"

EXPECTED_GERMAN_CHAIN = [
    "lowercase",
    "split_compound",
    "custom_stopword",
    "stopword",
    "remove_long",
    "stemmer",
]

EXPECTED_NAME_CHAIN = ["lowercase", "ascii_fold", "remove_long"]
```

Die zugehörige Leseroutine `filter_chain(source, function)` steht in `test_analyzer.py:540-560` und ist **wiederverwendbar**: sie nimmt Quelltext und Funktionsnamen entgegen. Für die neue Fabrik lautet die Erwartung:

```python
EXPECTED_SNOWBALL_CHAIN = [
    "lowercase",
    "ascii_fold",
    "stopword",
    "custom_stopword",
    "remove_long",
    "stemmer",
]
```

Dazu gehören nach dem Vorbild der Zeilen 578-630 drei Selbsttests des Wächters: der Wächter unterscheidet zwei Ketten, er sieht eine nach hinten verschobene Faltung (das Anti-Muster mit Namen, entspricht `test_the_guard_sees_remove_long_pulled_in_front_of_the_splitter`), und ein Kommentar, der einen Filter nennt, landet nicht in der Kette.

**Hälfte 2, Positivlisten-Parität.** Analogon `backend/tests/test_ocr_languages.py`.

Die Doppelrichtung ist das ganze Muster (Zeilen 94-122); nur die Gegenstelle wechselt vom Dockerfile zum laufenden tantivy:

```python
def test_every_offered_language_has_a_pinned_apt_line() -> None:
    lines = _dockerfile_lines()
    installed = _installed(lines)

    missing = set(OCR_LANGUAGE_ALLOWLIST) - installed
    assert not missing, f"the allowlist offers languages the image does not install: {missing}"

    surplus = installed - set(OCR_LANGUAGE_ALLOWLIST) - {"osd"}
    assert not surplus, f"the image carries language packs nothing may ever use: {surplus}"

    # The mutation, staged here rather than described: with the apt line of one
    # language gone, this case has to see it go. A gate whose red state is never
    # produced is a gate nobody has tested.
    assert MUTATED_LANGUAGE in installed
    assert MUTATED_LANGUAGE not in _installed(_without(lines, MUTATED_LANGUAGE))
```

Übertragung: eine Sprache aus `SUPPORTED_LANGUAGES`, die nicht in `LANGUAGE_ALLOWLIST` steht, ist eine wartende Panic; eine Sprache in `LANGUAGE_ALLOWLIST`, für die `Filter.stopword(...)` **plus** `Filter.stemmer(...)` bis zum `build()` nicht durchläuft, ist eine falsche Zusage. **`build()` und nicht nur die Filterkonstruktion**, RESEARCH 5.1: der Fehler tritt erst beim Bauen auf.

Die Zahlenbehauptung als eigener Test, Vorbild Zeilen 125-139 (`test_the_default_stays_at_three_and_is_a_true_subset_of_the_offer`): 13 in der Positivliste, 6 im Produkt, `set(SUPPORTED_LANGUAGES)`-Abbildung über `SNOWBALL_NAME` ist eine echte Teilmenge.

**Das dritte Gate, das kein Vorbild hat und trotzdem Pflicht ist:** `Filter.custom_stopword([])` ist ein No-op. RESEARCH 6.3 und A6 machen es zur Bedingung dafür, dass `english_analyzer()` überhaupt in die gemeinsame Fabrik darf. Form: dieselbe Tokenliste für dieselben Eingaben mit und ohne leeren Filter, keine Prosa.

Der Muster-Kopf für die Fehlermeldungen ist durchgehend `backend/tests/test_allowlist_parity.py:54-64`: die Meldung nennt den Namen **und** die Seite, auf der er fehlt, nie zwei Mengen zum Vergleichen.

---

### `backend/tests/fixtures/chain_cases_es.txt` und Geschwister (fixture, file-I/O)

**Analogon:** `backend/tests/fixtures/compound_cases_de.txt`.

Heutiges Format, ein Wort je Zeile, keine Kommentare:

```
Grundstücksverkehrsgenehmigung
Kündigungsfrist
Sitzungsvorlage
```

Neues Format laut RESEARCH 3.3, eine Formfamilie je Zeile, Kommentare mit `#`:

```
# lemma: alle Schreibweisen, die ein Mensch tippt oder ein Dokument traegt
información informacion informaciones
alemán aleman alemanes alemana alemanas
```

**Konsequenz für den Planer:** `compound_cases_de.txt` wird mit `.split()` gelesen (`test_analyzer.py:141`, `compound_probe.py:161`). Das neue Format braucht einen eigenen Leser (Zeile für Zeile, `#` abschneiden, dann `.split()`), und dieser Leser muss von Sonde und Test geteilt werden, sonst driften Messung und Abnahme auseinander. Legen Sie ihn neben die Sonde und importieren Sie ihn im Test, nicht umgekehrt: `scripts/` ist kein Paket (`docs/testing.md`, Zeilen 25-36), also führt der Import nur in dieser Richtung.

---

### `scripts/dev/chain_probe.py` (dev-tool, batch/transform)

**Analogon:** `scripts/dev/compound_probe.py`, vollständig.

**Sicherheitsregel im Docstring** (Zeilen 26-38), wörtlich zu übertragen und auf Snowball-Listen plus Fixtures umzuschreiben:

```python
Security rule, carried unchanged from T-02-14: the probe reads the case list of
the repository, the Debian word list of the image, and with ``--against`` one
further list that the caller names. It never reads state.db, never an index and
never a user file, so nothing it prints can be user content. The words it prints
are the cases of the repository and the entries of a published spelling
dictionary.

Usage: compound_probe.py [--against LIST] CASES OUTPUT_DIR
```

**Die Regel, die die Sonde ehrlich macht** (Zeilen 63-71). Die Sonde baut **keine** eigene Kette, sie ruft die ausgelieferte:

```python
def _tokenise(constituents: Sequence[str], words: Sequence[str]) -> list[list[str]]:
    """Return the tokens the shipped German chain produces for every word.

    One factory call for both runs of this probe. The chain is the one the
    product ships, taken from findling.index.analyzer, because a chain rebuilt
    here would measure this file instead of the product.
    """
    analyzer = german_analyzer(constituents)
    return [analyzer.analyze(word) for word in words]
```

**Achtung, hier weicht Phase 17 bewusst ab:** das Messskript aus RESEARCH 3.2 baut sieben Kandidatenketten selbst, und das muss es auch, denn sechs davon existieren im Produkt nicht. Die Auflösung: die Kandidaten-Fabrik lebt in der Sonde, aber die Kette A+ wird **zusätzlich** gegen `snowball_analyzer()` aus dem Paket gefahren und Token für Token verglichen. Das ist dieselbe Beweisform wie `_differing()` unten, nur mit dem Produkt als Gegenstelle statt mit der vollen Wortliste.

**Ausgabemuster** (Zeilen 52-56, 105-122, 171-173): drei Dateien mit festen Namen, eine TSV mit Kopfzeile, eine `kennzahlen.txt` mit ausschliesslich Zahlen und Digests:

```python
TOKENS_FILE = "tokens-rezept-a.tsv"
SUBSET_FILE = "fixture-subset.txt"
NUMBERS_FILE = "kennzahlen.txt"

HEADER = ("word", "chars", "in_ngerman", "entry_in_list", "tokens")
```

```python
def _numbers(...) -> str:
    """Return the key figures of the run. Numbers and digests, nothing else."""
    figures = {
        "source_lines": source_lines,
        "entries": len(entries),
        "wordlist_hash": wordlist_hash(entries),
        ...
    }
    return "\n".join(f"{name}={value}" for name, value in figures.items()) + "\n"
```

**Rot-Muster** (Zeilen 125-134 und 175-189): eine Differenz ist Rückgabecode 1, und die Meldung nennt jeden abweichenden Fall einzeln auf stderr:

```python
def _differing(words, left, right) -> list[str]:
    """Return the cases whose two token lists are not the same list."""
    return [word for word, one, other in zip(words, left, right, strict=True) if one != other]


def _report(words: Sequence[str], headline: str) -> None:
    """Write a difference to stderr, headline first and then case by case."""
    print(f"compound_probe: {headline}", file=sys.stderr)
    for word in words:
        print(f"compound_probe: differing case: {word}", file=sys.stderr)
```

**Argumentmuster** (Zeilen 137-158 und 195-196): handgeschriebener Parser, kein argparse, `main(argv)` gibt int zurück, `raise SystemExit(main(sys.argv[1:]))`.

---

### `scripts/dev/measure_chains.sh` (dev-tool, batch)

**Analogon:** `scripts/dev/measure_compounds.sh`, aber **ohne Docker**.

**Was übernommen wird** (Zeilen 38-47 und 67-80): `set -eu`, Pin als vollständiges Argument statt als nackte Versionsnummer, Pfadauflösung über `CDPATH='' cd --`, Vorbedingungen mit eigener Fehlermeldung und Rückgabecode:

```sh
set -eu

# The two pins stand here as whole apt and pip arguments, not as bare version
# numbers, so that a grep for the pin finds the line that really installs it.
IMAGE="python:3.13-slim-trixie"
WNGERMAN="wngerman=20161207-15"
TANTIVY="tantivy==0.26.0"

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/../.." && pwd)
```

**Kopfkommentar-Muster** (Zeilen 13-36): welche Dateien geschrieben werden, welche Zahlen erwartet werden, und der Satz, der den Umgang mit einer Abweichung regelt. Wörtlich übertragbar:

```sh
# Expected from the phase research, for the full variant:
#   source_lines=356010  entries=276496
#   wordlist_hash=b1f64012ca7f5b6e57de2cb1bafa2521cb6606f3ccef5d6fd17396edc808dde0
# A deviation is a finding for the measurement report, not a reason to edit a
# file by hand.
```

Für Phase 17 lauten die Erwartungswerte 65 Familien, 573 Paare, A+ 467, Ergänzungsliste 77/10/0/30.

**Was ersatzlos entfällt:** der `docker run`-Block (Zeilen 77-80 und 104-123) samt `--volume ... :ro`-Kette und die MSYS-Warnung aus Zeile 35. Die Begründung gehört als Satz in den Kopf, weil sie der einzige sichtbare Unterschied zum Vorbild ist: alle vier Stoppwortlisten und alle vier Stemmer sind in tantivy einkompiliert, also genügt `uv run` aus `backend/`, und ein Container würde nur Laufzeit kosten. Der Gegensatz ist im Vorbild bereits benannt ("there is no Debian word list on this machine").

**Gate-Hinweis:** `scripts/` läuft nur durch ruff und ruff format, und mit `--config backend/pyproject.toml` (`docs/testing.md`, Zeilen 20-36). Nicht durch pyright, nicht durch vulture.

---

### `docs/language-analyzers.md` (docs)

**Analogon:** `docs/german-analyzer.md`, Aufbau eins zu eins.

Abschnittsfolge des Vorbilds: Kopfsatz, "The constituent list", "Measured numbers", "The filter order", die gemessene Tabelle, "Licence and provenance", "Memory", "What splitting costs at ranking time", "Known limits".

**Kettenabschnitt** (Zeilen 85-106). Textdiagramm plus Tabelle mit einer Zeile je Position und der Spalte "Why exactly here", danach der Absatz über den bewussten Ausreißer:

```text
simple -> lowercase -> split_compound(list) -> custom_stopword(FUGEN)
       -> stopword("german") -> remove_long(48) -> stemmer("german")
```

| Position | Filter | Why exactly here |
|---|---|---|
| 1 | `lowercase` | Everything after this compares strings exactly, and the list is lowercase |
| 5 | `remove_long(48)` | **After** the splitter. In front of it a 63 character compound is dropped whole |

Der Absatz danach erklärt, warum die deutsche Kette keine Faltung hat. Das Gegenstück dieser Phase ist der Absatz, warum die vier neuen Ketten eine haben und warum vorn.

**Grenzen-Abschnitt** (Zeilen 256 ff.). Form: fette Kennung, ein Absatz je Grenze, jede Grenze nennt die Alternative und warum sie teurer ist:

```markdown
## Known limits

These six are measured, documented and deliberately not fixed here.

**D2, verb forms.** The Snowball stemmer unifies the infinitive and the noun but
not the past tense or the participle: `suchen` and `Suche` both become `such`, ...
This cannot be fixed without replacing the stemmer, which would change every
term in the index.
```

Hier landen die zwei roten Zeilen aus RESEARCH 3.4 (`-ción`/`-ção`-Numerus), `año` gleich `ano`, `ciudad`/`ciudades`, `huis`/`huizen` und die fehlende portugiesische Rechtschreibvereinheitlichung. Achtung Owner-Regel 07.09.: das hier ist `docs/`, nicht Store-Text, also darf es ausführlich sein. Die Kurzfassung für HART-05 entsteht in Phase 23 und wird dem Owner vorgelegt.

---

### `docs/measurements/2026-09-analyseketten/` (docs, file-I/O)

**Analogon:** `docs/measurements/2026-09-komposita-rezept-a/`.

Ablage: `README.md` plus Unterverzeichnis `rohdaten/` mit den drei Dateien der Sonde.

**Kopf des Berichts** (README Zeilen 1-13), deutsch, mit dem Satz, der ihn zur Zitiergrundlage macht:

```markdown
# Rezept A, Fall fuer Fall gemessen, 08.09.2026

Dieser Bericht ist die Messgrundlage der Phase 8. Jede spaetere Aussage dieser
Phase ueber Token soll eine Zeile in `rohdaten/tokens-rezept-a.tsv` zitieren
koennen statt geraten zu werden ...

Gemessen wurde mit `scripts/dev/measure_compounds.sh`, das
`scripts/dev/compound_probe.py` in einem Wegwerf-Container faehrt. Die Sonde
baut keine eigene Filterkette: sie ruft `load_constituents` und
`german_analyzer` aus dem ausgelieferten Paket, damit der Bericht das Produkt
misst und nicht sich selbst.
```

**Umgebungstabelle als Abschnitt 1** (Zeilen 17-32): Datum, Abbild, Wortliste, Suchbibliothek mit Fassung, Quelle, Zahlen, Digest. Für Phase 17 stehen dort stattdessen die tantivy-Fassung beider Läufe, der Tag von `stopwords.rs`, die Wortzahlen 308/279/203/101 und der Hash der Ergänzungsliste.

**Hinweis:** Dieser Bericht verwendet ASCII-Ersatzschreibung (`fuer`, `ueber`). Das ist der Bestand dieses Verzeichnisses; die globale Regel verlangt echte Umlaute in deutscher Prosa. Neue Texte dieser Phase schreiben echte Umlaute, die Nachbardatei bleibt unangetastet.

---

### `17-GRUNDSATZ-ENTSCHEID.md` (planning, Owner-Tor)

**Analogon:** `.planning/milestones/v1.2-phases/12-messwerkzeug-runbook-und-terminentscheid/12-STABLE35-ENTSCHEID.md`, 299 Zeilen.

**Kopfmuster** (Zeilen 1-9). Der zweite Absatz ist die tragende Eigenschaft des Musters und muss sinngemäß übernommen werden:

```markdown
# Phase 12: stable35-Fenster-Entscheid (HART-03)

**Angelegt:** 2026-09-14 (Plan 12-01, Task 1)
**Zweck:** Die Frist dieses Entscheids ist der 16.09.2026, zwei Tage nach
Phasenbeginn. Beide Zweige werden deshalb VORHER vollständig ausformuliert,
inklusive der fertigen Ersatztexte für den YAML-Kommentar. Am Stichtag wird nur
noch gelesen, welcher Zweig greift, und der zugehörige Text eingesetzt; es wird
an diesem Tag kein Satz mehr entworfen. Folgepläne zitieren die Optionskennung
(a oder b) und keine Zusammenfassung.
```

**Abschnittsfolge, wörtlich zu übernehmen:**

1. `## Die Frage` , eine Frage, ein Satz.
2. `### Was festgestellt ist` , mit gelesenen Dateien samt Zeilennummern und Datum, plus einer Ist/Soll-Tabelle je betroffener Stelle.
3. `### Was unklar ist`
4. `### Die Leitplanke, die für beide Optionen gilt` , hier gehört die scharfe Definition von "D-04 berühren" aus RESEARCH 6.3 hin, sonst blockiert das Tor die Phase (Pitfall 8).
5. `### Option a: ...` und `### Option b: ...` , je mit "Greift, wenn ...", "Beweisgrundlage", "Vollzug".
6. `## Die fertigen Ersatztexte für <Datei>` , wortwörtlich einsetzbare Blöcke.
7. `## Vollzug am <Datum>` , leer angelegt, später gefüllt.
8. `### Vollzugs-Checkliste` , nummerierte Schritte.

**Ist/Soll-Tabellenmuster** (Zeilen 34-40):

| Ort | Ist-Zustand am 14.09.2026 | Zielzustand bei NC 35 final |
|---|---|---|
| Matrixeintrag `server-version: stable35` (Zeilen 217 bis 273) | `tolerate-failure: true` | `tolerate-failure: false`, der Ast wird muss-grün |

Für E-17-7 ist das die Tabelle der sieben Stellen aus RESEARCH 4.1.

**Vollzugsmuster** (Zeilen 233-281). Feste Felder: Datum, gelesener Stand als Tabelle mit dem abgesetzten Kommando darüber, greifender Zweig mit Begründung, Beleg, Laufnummer des Beweislaufs, "Vollzogen am / durch Plan".

**Checklisten-Muster** (Zeilen 282-299), sieben nummerierte Schritte, Schritt 4 enthält den Satz, den Phase 17 braucht: "ein roter Lauf ist ein Befund und wird gelesen, bevor irgendetwas geändert wird".

**Owner-Vorlage:** eigene Aufgabe vom Typ `checkpoint:human-verify` mit `gate="blocking"` (RESEARCH 6.1). Abnahme: Owner hat "freigegeben" geschrieben oder benannt, was zu ändern ist; benannte Änderungen sind eingearbeitet und erneut vorgelegt.

**Kennungsschema:** E-17-1 bis E-17-8, Optionen als Kleinbuchstaben. Folgepläne zitieren `E-17-7 Option a`, nie eine Zusammenfassung.

---

### `backend/tests/test_upgrade_compatibility.py` (test, Ratsche)

**Analogon:** dieselbe Datei. Das ist die Datei, die der Pin-Sprung rot macht, und ihr Modulkopf verbietet ausdrücklich, sie grün zu reparieren:

```python
**A red test here is not a repair, it is a question for the owner.** Nothing in
this file may be adjusted to make it green again. The green way out is to leave
the mark where it is; the other way out is a decision that an upgrade rebuilds
every installed index, and that decision is not a test edit.
```

**Was zu ändern ist, und nur mit E-17-7 Option "lockern" im Rücken** (Zeilen 42-77):

```python
GOLD_V1_0_AND_V1_1 = {
    "schema_version": "1",
    "index_version": "1",
    "analyzer_version": "1",
    "tantivy_version": "0.26.0",
}

TANTIVY_MARK = "tantivy_version"

# The index format of tantivy 0.26.0. It is the half of the banner that decides
# whether the files on disk can still be opened at all.
GOLD_INDEX_FORMAT = "index_format v7"

TANTIVY_PIN = "tantivy==0.26.0"
```

**Vergleichsmuster, das schon heute die Sonderbehandlung des Banners trägt** (Zeilen 85-100). Die Zeile `held = gold in value if mark == TANTIVY_MARK else value == gold` ist der Ort, an dem aus "enthält 0.26.0" ein "enthält `index_format v7`" wird:

```python
def drift_findings(marks: Mapping[str, str]) -> list[str]:
    """Every gold mark the given set does not carry, as one sentence each.

    Fails closed: a mark that is missing altogether reads as the empty value and
    becomes a finding, because that is exactly how the store reads it too.
    """
    findings: list[str] = []
    for mark, gold in GOLD_V1_0_AND_V1_1.items():
        value = marks.get(mark, "")
        held = gold in value if mark == TANTIVY_MARK else value == gold
        if not held:
            findings.append(
                f"{mark} ist {value!r} statt {gold!r}; "
                f"ein Upgrade von 1.0.x oder 1.1.x wuerde jetzt einen Reindex ausloesen (D-04)"
            )
    return findings
```

**Selbsttest-Muster** (Zeilen 103-127): drei gestellte Datensätze, einer hält, einer hat eine bewegte Marke, einem fehlt eine. Jede Änderung an der Vergleichsregel braucht eine vierte Probe: derselbe `index_format`, andere Patchnummer, muss grün sein.

---

### `backend/src/findling/store/repo.py` (store, Vergleichsregel)

**Analogon:** `Store.version_mismatch()`, Zeilen 631-669. Die Lockerung ist kein Musterbruch, sondern eine zweite Ausnahme neben der, die schon da ist:

```python
        ``index_version`` is the one mark that is a floor rather than an equality:
        a lost index directory raises the local generation past the code's
        baseline to force a reindex, and that is a healthy state, not a drift.
        Only a stored generation BELOW the expected one means the index predates
        the current code.
```

```python
        stored = self.read_meta()
        diverging = []
        for key, value in expected.items():
            current = stored.get(key)
            if current == value:
                continue
            if key == "index_version" and _generation_at_least(current, value):
                continue
            diverging.append(key)
        return diverging
```

Die neue Ausnahme steht als dritte `if`-Zeile mit einem Hilfsvergleicher nach dem Vorbild von `_generation_at_least`, und der Docstring bekommt einen Absatz im selben Ton. Der Satz aus Zeile 637 ("A mark that was never written counts as diverging") ist gleichzeitig die Wurzel von Pitfall 3 und bleibt unverändert.

**Erzeugerseite** (`backend/src/findling/index/open.py`, Zeilen 61-67 und 123-141). Der Banner wird weiter gespeichert; nur der Vergleich lockert:

```python
# The banner of the extension module, measured as "tantivy v0.26.0, index_format
# v7". The type stub shipped with tantivy 0.26.0 does not declare the attribute,
# so the read is annotated for pyright rather than replaced by a lookup with a
# default: a fallback value here would turn a renamed attribute into a version
# mark that quietly says the wrong thing.
TANTIVY_VERSION: Final[str] = tantivy.__version__  # pyright: ignore[reportAttributeAccessIssue]
```

```python
    return {
        "schema_version": str(SCHEMA_VERSION),
        _LOCAL_GENERATION: str(INDEX_VERSION),
        "analyzer_version": str(ANALYZER_VERSION),
        "wordlist_hash": digest,
        "tantivy_version": TANTIVY_VERSION,
    }
```

Der Docstring von `expected_versions` beschreibt die Zuständigkeitstrennung, die RESEARCH als nicht aufweichbar markiert: "this module knows what the current code produces, the store knows what the existing index was built with, and only the caller that holds both may decide what a difference means".

Der `pyright: ignore`-Kommentar ist beim Fassungswechsel zu prüfen: falls 0.26.2 das Attribut im Stub deklariert, wird der Kommentar unnötig und `ruff`/`pyright` melden ihn.

---

### `.github/workflows/deploy-harp.yml` (CI)

**Analogon:** Job "Store upgrade 5", Zusicherungen 1 bis 6, Zeilen 3266-3348.

**Die Stelle, die vom Pin-Sprung getroffen wird** (Zeilen 3288-3291):

```bash
          echo "--- 2, die gleichen fuenf Marken (D-04) ---"
          for mark in schemaVersion indexVersion analyzerVersion wordlistHash tantivyVersion; do
            unchanged ".marks.${mark}" "a version mark moved, and a moved mark is a full reindex on every installation in the field (D-04)"
          done
```

**Der Vergleicher** (Zeilen 3270-3281), der das Muster "jede Zusicherung läuft, keine bricht ab" trägt:

```bash
          fail=0
          # One comparison, one sentence saying what it means, and every one of
          # them runs: a step that stopped at the first difference would hide
          # which of the six the upgrade broke.
          unchanged() {
            path="$1"
            meaning="$2"
            was=$(jq -r "${path}" "${before}")
            now=$(jq -r "${path}" "${after}")
            if [ "${was}" != "${now}" ]; then
              echo "::error::${meaning}: ${path} was ${was} before the upgrade and is ${now} after it"
              fail=1
            else
              echo "unchanged  ${path} = ${was}   (${meaning})"
            fi
          }
```

**Das Muster für eine Marke, die sich ändern DARF** (Zusicherung 6, Zeilen 3331-3342). Falls E-17-7 "lockern" fällt, ist `tantivyVersion` genau dieser Fall: die Marke bewegt sich, und die Zusicherung wird von "unverändert" auf "von X nach Y, und zwar genau dahin" umgeschrieben, nicht gelöscht:

```bash
          echo "--- 6, the two date bounds of the provider, and this one HAS to have changed ---"
          was=$(jq -r '.searchFilters.dates' "${before}")
          now=$(jq -r '.searchFilters.dates' "${after}")
          if [ "${was}" != "false" ] || [ "${now}" != "true" ]; then
            echo "::error::the provider declared the two date bounds as ${was} before the upgrade and as ${now} after it, and the change plan 13-06 made has to arrive on an existing installation"
            ...
```

Zusicherungen 4 und 5 (kein Reindex-Banner, keine Zeile `built by different code`, Zeilen 3303-3329) bleiben unverändert und müssen grün bleiben. Sie sind der eigentliche Beweis von Erfolgskriterium 4; Zusicherung 2 ist nur der erste Anzeiger.

**Der Zusammenfassungsblock** (Zeilen 3350-3362) zählt die Marken im Klartext auf und muss mitgeändert werden, sonst behauptet die Job-Zusammenfassung etwas, das der Schritt darüber nicht mehr prüft.

---

### `.github/dependabot.yml` (config)

**Befund, der RESEARCH korrigiert:** RESEARCH 4.1 und 4.4 behaupten, es gebe keinen `ignore`-Eintrag für tantivy ("Phase-16-Vorschlag, nie umgesetzt"). Er **existiert** am Dateiende, mit Begründung und Owner-Datum:

```yaml
    # tantivy carries index format v7 from 0.26.2 on, which means a reindex on
    # every installation that already runs. The pin therefore only ever moves on
    # purpose and together with a reindex plan (owner decision of 2026-09-21).
    #
    # The service already answered the comment command on pull request #10 with
    # "I won't notify you about tantivy again", but that state lives inside a
    # foreign service and not in this repository, and dependabot said so itself:
    # closing a grouped pull request ignores nothing. So the rule stands here, in
    # a file, where a reader of the tree can find it.
    ignore:
      - dependency-name: "tantivy"
        update-types:
          - version-update:semver-major
          - version-update:semver-minor
          - version-update:semver-patch
```

Für den Planer heißt das dreierlei. Erstens: keine Aufgabe "ignore-Eintrag anlegen", er ist da. Zweitens: der Kommentar behauptet "index format v7 from 0.26.2 on, which means a reindex", und die eigene Messung in RESEARCH 4.2 widerlegt das (v7 in **beiden** Fassungen, Index in beide Richtungen lesbar). Der Kommentar ist also sachlich falsch und muss mit dem Entscheid berichtigt werden, sonst steht im Baum eine Begründung, die der Messbericht widerlegt. Drittens: der Kommentar nennt einen Owner-Entscheid vom 21.09.2026, den E-17-7 ablöst; das Ablösen gehört datiert in denselben Kommentar.

---

### `THIRD-PARTY.md` (docs)

**Analogon:** Zeile 139 und der Begründungsabsatz Zeilen 150-155:

```markdown
| `tantivy` | 0.26.0 | MIT | github.com/quickwit-oss/tantivy-py | `/app/.venv/lib/python3.13/site-packages/tantivy` |
```

Der Absatz darunter erklärt, dass die Lizenz von tantivy als einzige nicht aus PyPI ablesbar ist und am Tag des Repos gelesen wurde. Beim Fassungswechsel wandert der Tag in diesem Absatz mit, nicht nur die Zahl in der Tabelle. Zusätzlich neu: die Snowball-Stoppwortlisten sind BSD-3-Clause und einkompiliert, also keine neue Zeile, aber eine Erwähnung wert, weil die Ergänzungsliste aus ihnen abgeleitet ist und im Repo ausgeliefert wird.

---

## Geteilte Muster

### Begründender Kommentar statt beschreibender

**Quelle:** durchgehend, deutlichstes Beispiel `backend/src/findling/index/analyzer.py:70-73`
**Gilt für:** jede neue Konstante, jede neue Funktion, jede CI-Zusicherung

Ein Kommentar sagt in diesem Baum nie, was der Wert ist, sondern warum er dort steht und was passiert, wenn jemand ihn allein ändert. Ein Plan, dessen Aufgabe mit "Konstante LANGUAGE_ALLOWLIST hinzufügen" endet, hat die Hälfte nicht beauftragt.

### Doppelrichtungs-Gate mit Selbstmutation

**Quelle:** `backend/tests/test_ocr_languages.py:94-122`, `backend/tests/test_allowlist_parity.py:54-90`
**Gilt für:** `test_language_analyzers.py`, Hälfte 2

Drei Bestandteile: beide Richtungen werden behauptet, die Meldung nennt den Namen und die Seite, und das Gate beweist seinen eigenen roten Zustand an einer gestellten Mutation. Der Satz dazu steht in `test_ocr_languages.py:107-108`: "A gate whose red state is never produced is a gate nobody has tested."

### Die Gegenstelle wird gelesen, nie zweitgeschrieben

**Quelle:** `test_ocr_languages.py:15-19`, `test_allowlist_parity.py:25-27`
**Gilt für:** Positivlisten-Test, Kettenwächter, Pin-Tests

Der Test importiert die Konstante und liest die Gegenstelle als Text oder befragt die laufende Bibliothek. Er schreibt die Menge nie ein zweites Mal hin: "a test that repeats the set it guards agrees with itself on the very day somebody adds a tenth language, which is the only day it matters."

### Die Messung misst das Produkt, nicht sich selbst

**Quelle:** `scripts/dev/compound_probe.py:64-71`, `docs/measurements/2026-09-komposita-rezept-a/README.md:8-13`
**Gilt für:** `chain_probe.py`, Messbericht

Die Sonde ruft die ausgelieferte Fabrik. Wo Phase 17 davon abweichen muss (sechs Kandidatenketten gibt es im Produkt nicht), wird die Abweichung durch einen Token-für-Token-Vergleich der Siegerkette gegen `snowball_analyzer()` wieder geschlossen.

### Messsonden sehen nie Nutzertext (T-02-14)

**Quelle:** `backend/src/findling/index/analyzer.py:227-232`, `scripts/dev/compound_probe.py:26-31`
**Gilt für:** `chain_probe.py`, `measure_chains.sh`

```python
# Measurement mode. Numbers only, never a token and never a word: this path sees
# user content, and a measurement that prints what it tokenised is the cheapest
# way to leak it (T-02-14). Driven by scripts/dev/measure_wordlist.sh, which runs
# it in a throwaway Debian container.
```

Für Phase 17 ist die Regel leichter einzuhalten und muss trotzdem im Modulkopf stehen: die Sonde liest nur veröffentlichte Snowball-Listen und Repo-Fixtures, nie `state.db`, nie einen Index, nie eine Nutzerdatei.

### Eine bewegte Marke ist eine Owner-Frage, kein Test-Edit

**Quelle:** `backend/tests/test_upgrade_compatibility.py:15-24`, `.github/workflows/deploy-harp.yml:3288-3291`
**Gilt für:** jeden Plan mit tantivy-Bezug

Die Reihenfolge ist zwingend: Entscheiddokument anlegen, Owner-Checkpoint, dann erst `uv lock --upgrade-package tantivy`, `uv sync`, volle Suite, dann Gold-Werte und CI-Zusicherung mit dem Messbeleg im Kommentar. Nie umgekehrt. Frühwarnzeichen laut RESEARCH Pitfall 2: ein Plan, dessen Abnahmekriterium "Gold-Werte auf 0.26.2 aktualisiert" lautet.

### Sprache und Zeichen

**Quelle:** `CLAUDE.md`, `backend/tests/test_analyzer.py:21-23`
**Gilt für:** alle Dateien dieser Phase

Code, Docstrings und Bezeichner Englisch. `.planning/`-Dokumente und `docs/`-Prosa Deutsch mit echten Umlauten. Akzente und Umlaute in Python ausschließlich in String-Literalen, mit dem Satz im Modulkopf, der das begründet. Keine Em-Dashes, auch nicht in Docstrings; dafür gibt es Gates im Baum.

### Qualitätsgates vor jedem Commit

**Quelle:** `docs/testing.md:18-36`
**Gilt für:** alle Pläne

Aus `backend/`: `uv run ruff check`, `uv run ruff format --check`, `uv run pyright`, `uv run vulture`, `uv run python -m pytest -q`. Für `scripts/dev/*` nur ruff und ruff format, mit `--config backend/pyproject.toml`. Kein pyright, kein vulture auf `scripts/`.

---

## Ohne Analogon

| Datei / Baustein | Rolle | Datenfluss | Grund |
|---|---|---|---|
| `backend/tests/fixtures/chain_known_losses_*.txt` | fixture | file-I/O | Der Baum kennt dokumentierte Grenzen nur als Prosa in `docs/german-analyzer.md` und als einzelne Testfälle (`test_analyzer.py:203-235`), nie als eigene Datei. Nächstes Muster für die Strenge "rot, sobald ein Verlust dazukommt **oder** verschwindet" ist die Doppelrichtungs-Behauptung von `test_allowlist_parity.py:54-64`. Format und Leser sind neu zu entwerfen. |
| Formfamilien-Metrik (`family_score`) | test-helper | transform | Es gibt im Baum keinen paarzählenden Vergleicher. RESEARCH 3.2 druckt ihn vollständig ab; er braucht nur englische Docstrings, ruff-Format und die Auslagerung der Wortlisten in Fixtures. |
| Mehrsprachiger Leser für Fixture-Zeilen mit `#`-Kommentaren | utility | file-I/O | Alle heutigen Fixtures werden mit `.split()` über die ganze Datei gelesen. Der neue Leser wird von Sonde und Test geteilt und lebt neben der Sonde, weil `scripts/` kein Paket ist. |

---

## Reihenfolgehinweise für den Planer

Aus RESEARCH 6.3, hier als Musterfolge gelesen.

**Vor dem Owner-Tor zulässig:** `chain_probe.py`, `measure_chains.sh`, die Fixtures, der Messbericht, `docs/language-analyzers.md`, `LANGUAGE_ALLOWLIST` plus Paritätstest, die vier Analyse-Funktionen **angelegt und nirgends registriert**, die Überführung von `english_analyzer()` in die gemeinsame Fabrik (nur mit dem No-op-Beweis als Test).

**Hinter dem Owner-Tor:** alles, was `backend/pyproject.toml`, `backend/uv.lock`, `test_upgrade_compatibility.py`, `store/repo.py:version_mismatch`, `deploy-harp.yml` oder `THIRD-PARTY.md` anfasst.

**Die Falle, die der Planer scharf fassen muss:** "D-04 berühren" heißt jede Änderung, die eine der fünf Marken bewegt, ein Schemafeld anlegt oder die Query-Feldliste erweitert. Nicht mehr. Ohne diese Definition im Entscheiddokument blockiert das Tor die ganze Phase (RESEARCH Pitfall 8).

**`ANALYZER_VERSION` bleibt in Phase 17 auf 1.** Der Modulkopfsatz in `analyzer.py:51` wird um "a chain that is added but registered nowhere changes no tokenisation" ergänzt, im selben Plan, der die Ketten anlegt. Sonst hebt der nächste Leser die Marke aus Vorsicht und löst genau das aus, was Erfolgskriterium 4 verbietet.

---

## Metadaten

**Suchraum:** `backend/src/findling/` (index, store, config), `backend/tests/`, `scripts/dev/`, `docs/`, `docs/measurements/`, `.github/workflows/`, `.github/`, `.planning/milestones/`
**Vollständig gelesene Dateien:** `index/analyzer.py`, `tests/test_ocr_languages.py`, `tests/test_allowlist_parity.py`, `tests/test_upgrade_compatibility.py`, `scripts/dev/compound_probe.py`, `scripts/dev/measure_compounds.sh`, `.github/dependabot.yml`
**Gezielt gelesene Bereiche:** `config.py` (70-95, 250-310, 1000-1070), `tests/test_analyzer.py` (1-60, 130-300, 495-643), `index/wordlist.py` (95-155), `index/open.py` (40-155), `store/repo.py` (631-676), `docs/german-analyzer.md` (1-40, 85-110, 256-300), `deploy-harp.yml` (3256-3400), `12-STABLE35-ENTSCHEID.md` (1-50, 100-150, 233-299)
**Datum der Musterextraktion:** 2026-09-23
