# Phase 21: Niederlaendische Komposita - Pattern Map

**Mapped:** 2026-09-25
**Files analyzed:** 27 (neu oder geaendert)
**Analogs found:** 26 / 27

Leitsatz fuer alle Plaene: Phase 21 ist fast vollstaendig ein "zweites Exemplar" bestehender Muster. Das deutsche Splitter-Paket (Phase 2/8/17) liefert Modul, Kette, Sonde, Fixture, Dockerfile-Block, docker.yml-Gate und THIRD-PARTY-Abschnitt; die Sprachmarke `languages` (Phase 18/19) liefert jede Markenstelle. Kopieren, nicht verallgemeinern: `wordlist.py` und `german_analyzer` bleiben byteidentisch (deutscher Digest `b1f64012...dde0`).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `backend/src/findling/index/wordlist_nl.py` (NEU) | utility/service | file-I/O + transform | `backend/src/findling/index/wordlist.py` | exact |
| `backend/src/findling/index/analyzer.py` (+ `dutch_analyzer`, `cached_dutch_analyzer`, `dutch_build_count`, Docstring) | utility (Kette) | transform | `german_analyzer` / `cached_german_analyzer` im selben File | exact |
| `backend/src/findling/index/open.py` (+ `DUTCH_MARK`, `DUTCH_LIST_OFF`, Signatur `open_index`, `expected_versions`, `_MARKS_OF_A_DIRECTORY`, `stamp_a_new_directory`) | config/registry | request-response | `LANGUAGES_MARK` im selben File | exact |
| `backend/src/findling/index/rebuild.py` (`MARKS_A_REBUILD_ANSWERS`, `stamp_after_swap`, `rebuild_the_index`, 4x `open_index`) | service | batch | `LANGUAGES_MARK`-Behandlung im selben File | exact |
| `backend/src/findling/store/repo.py` (`_DUTCH_MARK`, `_seed_meta`, `version_mismatch`, `_dutch_list_is_legacy`) | model/store | CRUD | `_LANGUAGES_MARK` / `_languages_are_legacy` im selben File | exact |
| `backend/src/findling/worker/poller.py` (Z. 347, 372, 373) | service | event-driven | eigene Aufrufstellen von `expected_versions`/`open_index` | exact |
| `backend/src/findling/api/resources.py` (Z. 233, 688) | controller | request-response | eigene Aufrufstellen | exact |
| `backend/src/findling/tools/one_load.py` (Z. 232, 265), `index/bench.py` (Z. 287), `tools/index_status.py` (Z. 125) | utility/tool | batch | eigene Aufrufstellen | exact |
| `backend/src/findling/api/status.py` (optional `wordlistHashNl`, Discretion) | controller | request-response | `wordlistHash` Z. 162/393 | exact |
| `backend/src/findling/index/schema.py` Z. 170-171 (Kommentar) | config | n/a | selbst | exact |
| `backend/Dockerfile` (wdutch-Block) | config | build | `wngerman`-Block Z. 172-211 | exact |
| `.github/workflows/docker.yml` (wdutch-Gate) | config/CI | build-verify | Schritt "The word list, its version and its licence in this image" Z. 223-291 | exact |
| `THIRD-PARTY.md` (Abschnitt "The Dutch word list") | docs | n/a | "## The word list" Z. 24-52 | exact |
| `scripts/dev/measure_compounds_nl.sh` (NEU) | tool | batch | `scripts/dev/measure_compounds.sh` | exact |
| `scripts/dev/compound_probe_nl.py` (NEU) | tool | transform | `scripts/dev/compound_probe.py` | exact |
| `backend/tests/fixtures/compound_cases_nl.txt` (NEU) | test fixture | n/a | `fixtures/compound_cases_de.txt` | exact |
| `backend/tests/fixtures/constituents_nl.txt` (NEU, von Sonde erzeugt) | test fixture | n/a | `fixtures/constituents_de.txt` | exact |
| `docs/measurements/2026-09-komposita-nl/README.md` + `rohdaten/` (NEU) | docs | n/a | `docs/measurements/2026-09-komposita-rezept-a/` | exact |
| `backend/tests/test_wordlist_nl.py` (NEU) | test | n/a | `backend/tests/test_wordlist.py` | exact |
| `backend/tests/test_analyzer.py` oder neues `test_dutch_analyzer.py` | test | n/a | `backend/tests/test_analyzer.py` Z. 91-291 | exact |
| `backend/tests/test_language_analyzers.py` (beide nl-Ketten) | test | n/a | selbst + `chain_cases_nl.txt` | role-match |
| `backend/tests/test_store_repo.py` (siebte Marke) | test | n/a | Block "the sixth mark and its exception" Z. 302-395 | exact |
| `backend/tests/test_upgrade_compatibility.py` (`ALL_MARKS`, `GOLD_V1_3`, `WDUTCH_PIN`) | test | n/a | selbst Z. 89-164, 329-355 | exact |
| `backend/tests/test_index_open.py` (Registrierung, Stempel) | test | n/a | selbst Z. 662-722, 853 | exact |
| `backend/tests/test_index_rebuild.py` (D-08: fullreindex stempelt?) | test | n/a | selbst (Fixture-Muster Z. 85) | role-match |
| `.github/workflows/deploy-harp.yml` Language proof (5. Dokument) + `backend/tests/test_language_proof_steps.py` | CI + test | request-response | Schritt Z. 829-1163 + Gate-Konstanten Z. 85-133 | exact |
| `docs/language-analyzers.md` Z. 440-446, `docs/performance.md`, ggf. `docs/dutch-analyzer.md` | docs | n/a | `docs/german-analyzer.md` | role-match |

## Pattern Assignments

### `backend/src/findling/index/wordlist_nl.py` (utility, file-I/O + transform)

**Analog:** `backend/src/findling/index/wordlist.py` (399 Zeilen, komplett gelesen)

**Modul-Docstring** (Z. 1-63): Rezepttabelle im Docstring, Quelle und Lizenz am Ende. Fuer nl: Rezepte A/B mit Fenstern aus 21-RESEARCH "Rezepte" uebernehmen, B 4-14 als gewaehlt (D-03), Quelle `wdutch 1:2.20.19+1-3`, Lizenz CC-BY-3.0 (D-04).

**Imports** (Z. 65-73) - wiederverwenden statt kopieren:
```python
import hashlib
import logging
import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from findling.config import DEFAULT_COMPOUND_DICT, settings
```
Fuer nl zusaetzlich: `from findling.index.wordlist import DIGEST_SUFFIX, ENCODING, Artifact, rss_bytes, wordlist_hash` (Research: "wordlist_hash wiederverwenden (import, nicht kopieren)"; `rss_bytes` laut "Don't Hand-Roll"). Plus `from tantivy import Filter, TextAnalyzerBuilder, Tokenizer` fuer den Fold der Liste (Anti-Pattern: kein `unicodedata`).

**Konstanten** (Z. 77-101):
```python
SYSTEM_WORDLIST = Path("/usr/share/dict/ngerman")
MIN_LEN = 4
MAX_LEN = 14
# The same constant is used twice on purpose: it goes into the splitter here and
# comes back out as a custom stopword in findling.index.analyzer. ...
FUGEN = ("s", "es", "n", "en", "er", "ns")
```
nl: `SYSTEM_WORDLIST_NL = Path("/usr/share/dict/dutch")`, `MIN_LEN = 4`, `MAX_LEN = 14`, `TUSSENKLANKEN = ("s", "e", "en")` mit demselben "used twice"-Kommentar. Zusaetzlich `DUTCH_LIST_OFF: Final = "off"` (entweder hier oder in open.py, siehe unten).

**Rezeptfunktion** (Z. 118-140) - Kern-Abweichung beachten:
```python
def load_constituents(source: Path = SYSTEM_WORDLIST, *, variant: str = DEFAULT_COMPOUND_DICT,
                      window: tuple[int, int] = (MIN_LEN, MAX_LEN)) -> list[str]:
    minimum, maximum = window
    ...
    for word in source.read_text(encoding=ENCODING, errors="replace").split():
        if not word.isalpha() or not minimum <= len(word) <= maximum:
            continue
        ...
        words.add(word.lower())
    words.update(FUGEN)
    return sorted(words)
```
nl-Version nach Research-Prototyp (21-RESEARCH Z. 405-427): **`split("\n")` statt `split()`** (4.380 Zeilen mit Leerzeichen), keine `variant`, Fenster auf die UNGEFALTETE Laenge, Fold per tantivy-Kette `simple -> lowercase -> ascii_fold`, nur Eintraege mit genau einem Token. `window`-Keyword beibehalten (Sonde misst 4-12/4-13/4-16).

**Artefakt** (Z. 156-181, 253-335): `artifact_path()` -> fuer nl `settings().dict_dir / "nl-full.txt"` (Name ein Mal buchstabiert, weil Fixture und Build lesen, Kommentar Z. 159-163). `_digest_path`, fail-closed `_load_artifact` (Z. 299-335) 1:1 uebernehmen.

**Cache/Zaehler** (Z. 207-250): Identitaetsschluessel `(path, digest, size, mtime_ns)`, `_CACHE_LOCK`, `read_count()`. Abweichung nach D-02: die Liste wird NACH dem Automatenbau FREIGEGEBEN; gecacht wird nur der Digest (Identitaetsschluessel -> Digest), nicht `entries`. Zaehler `read_count_nl()` als Testhebel behalten.

**Sprachgate (neu, kein direktes Analog):** `dutch_mark(languages: Sequence[str]) -> str` liefert `DUTCH_LIST_OFF`, ohne die Datei zu lesen, wenn `"nl" not in languages`; sonst Digest. Dazu `dutch_constituents_for(languages) -> list[str] | None` (Research Pattern 2).

**Messmodus** (Z. 338-399): `measure()` gibt nur Zahlen (T-02-14), `if __name__ == "__main__":  # pragma: no cover` mit `key=value`-Ausgabe.

---

### `backend/src/findling/index/analyzer.py` (Kette, transform)

**Analog:** selbes File, `german_analyzer` Z. 191-224, `cached_german_analyzer` Z. 331-344, `_CACHED_GERMAN`/`_BUILD_COUNT` Z. 137-152.

**Singleton + Zaehler** (Z. 137-152):
```python
_CACHED_GERMAN: dict[str, TextAnalyzer] = {}
_BUILD_COUNT = 0

def build_count() -> int:
    """Return how many German automata this process has built."""
    return _BUILD_COUNT
```
-> `_CACHED_DUTCH`, `_DUTCH_BUILD_COUNT`, `dutch_build_count()`.

**Fabrik mit Logging** (Z. 204-224):
```python
    global _BUILD_COUNT
    started = time.perf_counter()
    analyzer = (
        TextAnalyzerBuilder(Tokenizer.simple())
        .filter(Filter.lowercase())
        .filter(Filter.split_compound(list(constituents)))
        .filter(Filter.custom_stopword(list(FUGEN)))
        .filter(Filter.stopword("german"))
        .filter(Filter.remove_long(MAX_TOKEN_CHARS))
        .filter(Filter.stemmer("german"))
        .build()
    )
    _BUILD_COUNT += 1
    LOGGER.info("german automaton built from %d entries in %.3f s, build %d in this process", ...)
```
nl-Kette (D-07, Pitfall 3, Research Z. 431-443): `lowercase -> ascii_fold -> split_compound -> custom_stopword(TUSSENKLANKEN) -> stopword("dutch") -> custom_stopword(FOLDED_STOPWORDS["dutch"]) -> remove_long(MAX_TOKEN_CHARS) -> stemmer("dutch")`. Den Sprachnamen aus `SNOWBALL_NAME["nl"]` nehmen, nicht als Literal (Muster `open.py` Z. 152-156).

**Cache-Fabrik** (Z. 331-344):
```python
def cached_german_analyzer(digest: str, constituents: Sequence[str]) -> TextAnalyzer:
    cached = _CACHED_GERMAN.get(digest)
    if cached is not None:
        return cached
    analyzer = german_analyzer(constituents)
    _CACHED_GERMAN.clear()
    _CACHED_GERMAN[digest] = analyzer
    return analyzer
```

**`snowball_analyzer("dutch")` bleibt unveraendert** (Z. 242-312, Pitfall 4): sie ist die Kette ohne nl.

**Docstring-Ergaenzung** (Z. 77-87, Pattern 4): Der Satz "Any change to a chain below has to raise ANALYZER_VERSION" bekommt die Ausnahme fuer die nl-Splitterkette, im Stil des bestehenden Absatzes Z. 81-87 ("The other half of that sentence ..."): die Aenderung traegt die eigene Marke `wordlist_hash_nl`, ein Hub von `ANALYZER_VERSION` waere ein Vollreindex fuer alle (D-05). Optional `DUTCH_CHAIN_VERSION = 1` neben der Kette (Research Pattern 4, Discretion).

**Import-Grenze:** `analyzer.py` importiert heute aus `wordlist` (Z. 101). Neu analog `from findling.index.wordlist_nl import TUSSENKLANKEN`. Der Extraktions-Wachter (`findling/extract/__init__.py` Z. 6-12, Laufzeit-Test gegen geladene Module im Kind) muss `wordlist_nl` mit abdecken; `wordlist_nl` darf `analyzer` NICHT importieren (Muster `wordlist.measure` Docstring Z. 373-378).

---

### `backend/src/findling/index/open.py` (Registry + Marken)

**Analog:** selbes File.

**Markenkonstante mit Begruendungsblock** (Z. 62-76):
```python
# The sixth mark, and the one that is easiest to read as the opposite of what it
# is. It names the language set the index on disk was BUILT with, and never the
# set the running container currently wishes for. ...
LANGUAGES_MARK: Final = "languages"
```
-> `DUTCH_MARK: Final = "wordlist_hash_nl"` mit gleichartigem Kommentar (nicht gesaet, Fehlen = Legacy bei `off`, Vergleichsausnahme in `repo._dutch_list_is_legacy`).

**Registrierung** (Z. 123-160), heute:
```python
def open_index(path: Path, constituents: Sequence[str]) -> Index:
    ...
    index.register_tokenizer(TOKENIZER_DE, cached_german_analyzer(wordlist_hash(constituents), constituents))
    ...
    index.register_tokenizer(TOKENIZER_NL, snowball_analyzer(SNOWBALL_NAME["nl"]))
```
Neu: `open_index(path, constituents, *, dutch: Sequence[str] | None)` (keyword-only, kein Default in `src`). **Achtung Gate:** `test_index_open.py::test_open_index_registers_eight_chains_and_hangs_none_of_them_on_a_condition` (Z. 662-673) zaehlt `register_tokenizer`-Aufrufe unter einem `ast.If` als Befund (`registrations_of_open_index`, Z. 581-613, `isinstance(node, ast.If)`). Die Auswahl der Variante gehoert deshalb in eine Hilfsfunktion (z. B. `analyzer.dutch_chain_for(dutch)` gibt Splitter-Kette oder `snowball_analyzer("dutch")`), der `register_tokenizer(TOKENIZER_NL, ...)`-Aufruf bleibt frei. `EXPECTED_REGISTRATIONS = 8` bleibt.

**Erwartete Marken** (Z. 181-211):
```python
def expected_versions(digest: str, languages: str) -> dict[str, str]:
    return {
        SCHEMA_MARK: str(SCHEMA_VERSION),
        _LOCAL_GENERATION: str(INDEX_VERSION),
        "analyzer_version": str(ANALYZER_VERSION),
        "wordlist_hash": digest,
        "tantivy_version": TANTIVY_VERSION,
        LANGUAGES_MARK: languages,
    }
```
-> neuer keyword-only Parameter `dutch_mark: str`, Eintrag `DUTCH_MARK: dutch_mark` am Ende (Reihenfolge ist Teil von `ALL_MARKS` in `test_upgrade_compatibility.py`). `fingerprint()` (Z. 214-230) nimmt die Marke automatisch mit, das aendert den `.rebuild-for`-Fingerabdruck (Runtime State Inventory).

**Verzeichnismarken** (Z. 288, 291-345):
```python
_MARKS_OF_A_DIRECTORY: Final = frozenset({_LOCAL_GENERATION, SCHEMA_MARK, LANGUAGES_MARK})
...
    store.write_meta(SCHEMA_MARK, expected[SCHEMA_MARK])
    store.write_meta(LANGUAGES_MARK, expected[LANGUAGES_MARK])
```
-> `DUTCH_MARK` in die frozenset aufnehmen und in `stamp_a_new_directory` mitschreiben. `stamp_after_rebuild` (Z. 411-414) ueberspringt sie dann automatisch.

---

### `backend/src/findling/index/rebuild.py` (service, batch)

**Analog:** selbes File.

**Marken, die der Umbau beantwortet** (Z. 226-233):
```python
MARKS_A_REBUILD_ANSWERS: Final = frozenset({_SCHEMA_MARK, LANGUAGES_MARK})
```
-> `DUTCH_MARK` aufnehmen, Kommentar Z. 226-232 um die Begruendung ergaenzen ("Re-Analyse genuegt, weil `body_nl` aus dem gespeicherten `body_de`-Text neu entsteht"). `main._rebuild_is_due` (main.py Z. 473) liest dieselbe Menge, keine zweite Liste.

**Stempel hinter dem Tausch** (Z. 877-931):
```python
def stamp_after_swap(store: Store, languages: str) -> None:
    store.write_meta(_SCHEMA_MARK, str(SCHEMA_VERSION))
    store.write_meta(LANGUAGES_MARK, languages)
    store.write_meta(REBUILD_MARK, "")
```
-> Signatur um `dutch_mark: str` erweitern (keyword-only), Aufrufstelle Z. 1278.

**Einstieg** (Z. 1101-1129):
```python
    artifact = build_artifact()
    languages = ",".join(resolved.languages)
    expected = expected_versions(artifact.digest, languages)
    drifted = MARKS_A_REBUILD_ANSWERS.intersection(store.version_mismatch(expected))
    ...
        if resolved.rebuild_fallback == FULL_REINDEX_FALLBACK:
            start_rebuild_on_drift(store, expected)
            ...
            return FALLBACK_TO_FULL_REINDEX
```
Das ist die Stelle fuer D-08/Open Question 4: der fullreindex-Zweig schreibt keine Verzeichnismarke, `stamp_after_rebuild` ueberspringt `_MARKS_OF_A_DIRECTORY`. Der Test fuer D-08 gehoert in `test_index_rebuild.py` und prueft das heutige Verhalten fuer `languages`, BEVOR die nl-Marke dazukommt.

**`open_index`-Aufrufe** Z. 551, 552, 988, 995 und `_make_the_target_fit_this_code(target, constituents, wanted)` (Z. 946) bekommen die nl-Liste durchgereicht.

---

### `backend/src/findling/store/repo.py` (store, CRUD)

**Analog:** selbes File.

**Literal statt Import** (Z. 81-88):
```python
# ... a literal here keeps the store from importing the index side, ...
# The seed test in tests/test_store_repo.py fails the moment the two spellings part company.
_LANGUAGES_MARK: Final = "languages"
```
-> `_DUTCH_MARK: Final = "wordlist_hash_nl"` und `_DUTCH_LIST_OFF: Final = "off"` als Literale (repo importiert weder Index-Seite noch config, Z. 102-107).

**`_DEFAULT_META`** (Z. 191-199): nl-Marke NICHT aufnehmen; Kommentar Z. 177-190 ("One expected mark is missing from here on purpose ...") um die zweite Ausnahme ergaenzen.

**Vergleich** (Z. 756-771):
```python
            if key == _SCHEMA_MARK and _schema_is_legacy(current, value):
                continue
            if key == _LANGUAGES_MARK and _languages_are_legacy(current, value):
                continue
            diverging.append(key)
```
-> dritte Zeile `if key == _DUTCH_MARK and _dutch_list_is_legacy(current, value): continue`; Docstring Z. 737-745 nennt dann drei Ausnahmen.

**Legacy-Regel** (Z. 1465-1489) als Vorlage:
```python
def _languages_are_legacy(stored: str | None, expected: str) -> bool:
    if stored is not None:
        return False
    return set(expected.split(",")) <= set(LEGACY_LANGUAGES)
```
-> `_dutch_list_is_legacy(stored, expected)`: `stored is None and expected == _DUTCH_LIST_OFF` (Research Z. 448-454).

**Saat** (Z. 1541-1563):
```python
    seed = dict(_DEFAULT_META)
    seed.update(meta or {})
    seed.pop(_LANGUAGES_MARK, None)
```
-> `seed.pop(_DUTCH_MARK, None)` direkt darunter (Pitfall 1, T-18-05-01). Docstring "With one named exception" -> zwei.

---

### Aufrufer von `expected_versions` / `open_index` (service/controller/tool)

**Analog:** jeweils die eigene Zeile; alle bauen heute `",".join(settings().languages)`.

| Datei | Zeile | heute |
|---|---|---|
| `worker/poller.py` | 347 | `expected_versions(build_artifact().digest, ",".join(settings().languages))` in `_open_state` + `start_rebuild_on_drift` |
| `worker/poller.py` | 372-373 | `stamp_a_new_directory(...)`, `open_index(resolved.index_dir, artifact.entries)` |
| `worker/poller.py` | 1990 | `marks = expected_versions(...)` |
| `api/resources.py` | 233 | `_MARKS` (Cache je `dict_dir`), Z. 237-242 zeigt, wie eine Marke nachtraeglich angehaengt wird (`EMBEDDING_MARK`) |
| `api/resources.py` | 688 | `open_index(resolved.index_dir, build_artifact().entries)` (Leseseite) |
| `tools/one_load.py` | 232, 265 | `open_index`, `open_store(..., meta=expected_versions(...))` |
| `index/bench.py` | 287 | `open_index(directory, constituents)` |
| `tools/index_status.py` | 125 | `open_index(directory, ())` (wird nie gefragt; Test `test_the_only_index_opened_without_a_word_list_is_never_asked_a_question` Z. 527) -> `dutch=None` |

Muster: der nl-Wert kommt aus EINER Hilfsfunktion (`wordlist_nl.dutch_mark(settings().languages)`), nie inline zusammengebaut (vgl. Docstring `expected_versions` Z. 193-202).

**Pruefpunkt fuer den Planer:** `_open_state` (poller.py Z. 347-349) ruft `start_rebuild_on_drift` mit der vollen Erwartung; `start_rebuild_on_drift` (open.py Z. 259-273) hebt bei JEDER Abweichung die Generation. Fuer die Sprachmarke muss dieselbe Frage schon beantwortet sein (Startreihenfolge in `main.py`, Umbau vor Poller?); die nl-Marke erbt exakt dieselbe Behandlung. Per Test belegen, dass ein nl-Drift keinen Generationshub (= Vollreindex) ausloest.

---

### `backend/src/findling/api/status.py` (optional, Discretion)

**Analog:** Z. 162 `wordlistHash: str = ""`, Z. 393 `wordlistHash=marks.get("wordlist_hash", "")`; Spiegel in `tools/index_status.py` Z. 64 (`"wordlistHash": "wordlist_hash"`). Bei Aufnahme `wordlistHashNl` muss `test_admin_ui_contract.py` (Schluessellisten) mitziehen. Research empfiehlt: nur wenn billig, sonst genuegt das Banner.

---

### `backend/Dockerfile` (config, build)

**Analog:** Z. 172-211
```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends wngerman=20161207-15 \
    && rm -rf /var/lib/apt/lists/* \
    && test -s /usr/share/dict/ngerman \
    && test -s /usr/share/doc/wngerman/copyright \
    && install -D -m 0444 /usr/share/doc/wngerman/copyright \
        /usr/local/share/findling/COPYING.wngerman
```
Neuer Block direkt darunter mit gleichem Kommentaraufbau (Messwerte 413288 Zeilen / 5096240 Byte, Pin-Begruendung, kein Laufzeit-Download, Lizenzpflicht). Pin `wdutch=1:2.20.19+1-3`, `DEBIAN_FRONTEND=noninteractive` im RUN (Pitfall 6), Ziel `COPYING.wdutch`, Modus 0444.

---

### `.github/workflows/docker.yml` (CI-Gate)

**Analog:** Schritt "The word list, its version and its licence in this image" Z. 223-291 (vier Pruefungen, vier Meldungen):
```sh
            version=$(dpkg-query -W -f=\${Version} wngerman)
            if [ "${version}" != "20161207-15" ]; then ... exit 1; fi
            lines=$(wc -l < /usr/share/dict/ngerman | tr -d " ")
            bytes=$(wc -c < /usr/share/dict/ngerman | tr -d " ")
            if [ "${lines}" != "356010" ] || [ "${bytes}" != "4725887" ]; then ... exit 1; fi
            if ! grep -q "Upstream-Name: igerman98" "${licence}"; then ... fi
            if ! grep -q "License: GPL-2+" "${licence}"; then ... fi
            mode=$(stat -c %a "${licence}")
            if [ "${mode}" != "444" ]; then ...
```
Zweiter Schritt (oder zweiter Block im selben Schritt) fuer `wdutch`: Version `1:2.20.19+1-3`, `413288` / `5096240`, Lizenz-Strings vorher per `head` aus einem gebauten Container ablesen (Kommentar Z. 268-271 verlangt das; erwartet: `License: CC-BY-3.0` im `Files: wordlist/*`-Stanza), Modus 444.

---

### `THIRD-PARTY.md`

**Analog:** "## The word list" Z. 24-52 (Tabelle Item/Value) plus Vorspann Z. 8-22 und Pruefkommando Z. 328-330.
```markdown
| Debian package | `wngerman`, version `20161207-15`, `Architecture: all` |
| Source package | `igerman98`, upstream Björn Jacke, Debian maintainer Roland Rosenfeld |
| Origin | Debian trixie archive, installed with `apt-get` during the image build |
| File in the image | `/usr/share/dict/ngerman` (356010 lines, 4725887 bytes) |
| Licence | **GPL-2+** (`debian/copyright`, `Files: *`, ...); upstream additionally offers ... as an alternative |
| Licence text in the image | `/usr/local/share/findling/COPYING.wngerman`, copied from `/usr/share/doc/wngerman/copyright` |
| Derived artifact | `$APP_PERSISTENT_STORAGE/dict/de.txt`, produced at start up, SHA-256 recorded in the meta table |
```
Neuer Abschnitt "## The Dutch word list" mit derselben Tabelle: `wdutch` `1:2.20.19+1-3`, Quelle `dutch` (OpenTaal), `/usr/share/dict/dutch` (413288 lines, 5096240 bytes), Licence **CC-BY-3.0** laut `debian/copyright` `Files: wordlist/*`, Anmerkung upstream BSD-3-Clause und/oder CC BY 3.0 (D-04), Namensnennung "OpenTaal, https://www.opentaal.org", Derived artifact `dict/nl-full.txt` als gefilterte und gefaltete Bearbeitung. `dictionaries-common` ist schon gelistet (Z. 36-43). Pruefkommando Z. 328-330 um `wc -lc /usr/share/dict/dutch` erweitern. Englische Prosa (Datei ist englisch).

---

### `scripts/dev/measure_compounds_nl.sh` (tool, batch)

**Analog:** `scripts/dev/measure_compounds.sh` (123 Zeilen, komplett gelesen). Struktur 1:1: Kopfkommentar mit erwarteten Kennzahlen (Z. 18-22: "A deviation is a finding ..., not a reason to edit a file by hand"), Pins als ganze Argumente (Z. 40-44), `--against`-Parsing (Z. 49-61), read-only Mounts (Z. 91-102), `docker run --rm` (Z. 106-123).
```sh
IMAGE="python:3.13-slim-trixie"
WNGERMAN="wngerman=20161207-15"
TANTIVY="tantivy==0.26.0"
```
**Achtung:** das deutsche Skript pinnt noch `tantivy==0.26.0`. Das nl-Skript muss `tantivy==0.26.2` nennen (Research-Messung; `test_upgrade_compatibility.py::test_the_measurement_script_names_the_pinned_engine` Z. 368-381 prueft dasselbe fuer `measure_chains.sh`, das Muster auf das nl-Skript ausdehnen). Erwartete Werte: `source_lines=413288`, `entries=316740`, Digest-Praefix `ee7f3b8380c75283`. Ausgabe nach `docs/measurements/2026-09-komposita-nl/rohdaten`, Fallliste `backend/tests/fixtures/compound_cases_nl.txt`.

### `scripts/dev/compound_probe_nl.py` (tool, transform)

**Analog:** `scripts/dev/compound_probe.py` (196 Zeilen, komplett gelesen). Uebernehmen: Docstring mit Sicherheitsregel T-02-14 (Z. 26-31), `_tokenise` ruft die AUSGELIEFERTE Fabrik (Z. 63-71, Memory-Regel "Gegenprobe nie mit dem Muster der Umsetzung"), `_subset`/`_differing`/`--against` (Z. 74-148), `main` mit Exit 1 bei Tokenabweichung (Z. 151-192).
```python
from findling.index.analyzer import german_analyzer
from findling.index.wordlist import ENCODING, SYSTEM_WORDLIST, load_constituents, wordlist_hash
...
    analyzer = german_analyzer(constituents)
    return [analyzer.analyze(word) for word in words]
```
nl: `dutch_analyzer` + `wordlist_nl.load_constituents_nl`. Abweichungen: `_subset` muss gegen die GEFALTETEN, kleingeschriebenen Faelle vergleichen (Liste ist gefaltet); `in_source` aus `split("\n")`. Zusaetzlich Waechter-Spalte und eine Kennzahl "Komposita ueber Glied" (21/28) und "Waechter einteilig" (32/33), weil die Research genau diese Zahlen reproduziert haben will. Optional ein Modus "ohne Splitter" gegen `snowball_analyzer("dutch")` fuer die 0/28-Zeile.

### `backend/tests/fixtures/compound_cases_nl.txt`, `constituents_nl.txt`

**Analog:** `fixtures/compound_cases_de.txt` (Leerraum-getrennte Woerter, per `.split()` gelesen, conftest.py Z. 63-65) und `constituents_de.txt` (von der Sonde als `fixture-subset.txt` erzeugt). Inhalt: 28 Komposita + 33 Waechter + `coordinatiecentrum` (flach) aus 21-RESEARCH Z. 146-178. Ein Muttersprachler-Vorbehalt als datierter Kommentar ist nicht moeglich (Leerraum-Format); Vorbehalt A4 in README der Messung festhalten.

### `docs/measurements/2026-09-komposita-nl/`

**Analog:** `docs/measurements/2026-09-komposita-rezept-a/` mit `README.md` und `rohdaten/{fixture-subset.txt,kennzahlen.txt,tokens-rezept-a.tsv}`. Gleiche Dateinamen, Tokenliste als `tokens-rezept-b.tsv`. README nennt die 23-MB-Zahl ausdruecklich als ueberholte Schaetzung (Research Z. 215).

---

### `backend/tests/test_wordlist_nl.py` (test)

**Analog:** `backend/tests/test_wordlist.py`. Muster: Modul-Docstring "Recipe ..., asserted rather than trusted" (Z. 1-24), Miniatur-Quelle als Tupel mit Kommentar je Klasse (Z. 50-69), Fixtures `source` und `storage` (Z. 72-88):
```python
@pytest.fixture
def storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    root = tmp_path / "volume"
    root.mkdir(parents=True)
    monkeypatch.setenv("APP_PERSISTENT_STORAGE", str(root))
    settings.cache_clear()
    yield root
    settings.cache_clear()
```
Testnamen-Stil: `test_the_window_and_the_alphabetic_test_decide_what_stays`, `test_the_linking_elements_are_entries_of_their_own` (prueft auch das Literal: `assert FUGEN == (...)`), `test_a_tampered_artifact_is_rebuilt_from_the_source`, `test_the_list_on_the_volume_is_read_once_per_process`, `test_the_cache_never_answers_for_a_missing_artifact`. nl-spezifisch dazu: eine Quellzeile mit Leerzeichen (zeilenweises Lesen), eine Trema-Zeile (`coördinatie` landet gefaltet), `dutch_mark(("de","en")) == "off"` ohne Dateizugriff (Quelle fehlt -> kein Fehler), Liste nach Bau freigegeben (D-02).

### Kettentests (`test_analyzer.py` oder `test_dutch_analyzer.py`)

**Analog:** `backend/tests/test_analyzer.py` Z. 91-291. Parametrisierte Tabellen `COMPOUNDS`/`UNSPLIT` mit den gemessenen Token (Z. 91-135), Modul-Fixtures (Z. 138-147), der "guard over the guard" (Z. 237-249: jedes behauptete Wort steht in der gemessenen Fallliste), Tussenklank-Test (Z. 168-174 -> "kein Token der Laenge 1", Pitfall 5), Singleton-Tests (Z. 269-291):
```python
def test_analyzer_is_built_once(constituents: list[str]) -> None:
    digest = wordlist_hash(constituents) + "-built-once"
    before = build_count()
    first = cached_german_analyzer(digest, constituents)
    second = cached_german_analyzer(digest, constituents)
    assert first is second
    assert build_count() - before == 1
```
Plus: `ANALYZER_VERSION` bleibt 1 (bestehender Test `test_the_analyzer_version_is_pinned_next_to_the_chain` Z. 301).

### `backend/tests/test_language_analyzers.py`

**Analog:** selbst plus `fixtures/chain_cases_nl.txt`/`chain_known_losses_nl.txt` und `scripts/dev/chain_probe.py`. Pitfall 4: die Phase-17-Tabellen laufen gegen BEIDE nl-Ketten, die Differenz wird dokumentiert, keine der beiden still ersetzt.

### `backend/tests/test_store_repo.py` (siebte Marke)

**Analog:** Block Z. 302-395 ("the sixth mark and its exception"). Fall-fuer-Fall-Tests aus der Zustandstabelle (Research Z. 301-309), inklusive:
```python
def test_the_language_mark_is_never_written_by_the_seed(tmp_path: Path) -> None:
    expected = expected_versions("ein-digest", "de,en,es")
    opened = open_store(tmp_path / "state.db", meta=expected)
    try:
        assert LANGUAGES_MARK not in opened.read_meta()
        assert opened.version_mismatch(expected) == [LANGUAGES_MARK]
    finally:
        opened.close()
```
und die direkte Regelpruefung `test_the_language_exception_falls_closed` (Z. 381-394) als Vorlage fuer `_dutch_list_is_legacy` (None/"off" True; None/Digest False; "off"/Digest False; ""/"off" False). Warnzeichen Pitfall 1: kein Test, der die Marke setzt und dann "kein Drift" prueft.

### `backend/tests/test_upgrade_compatibility.py`

**Analog:** selbst. `GOLD_V1_3` (Z. 135-141) um `DUTCH_MARK: "off"` ergaenzen, `ALL_MARKS` (Z. 157-164) um die siebte Marke mit Ausnahme-Kommentar im Stil Z. 147-156, Docstring von `test_no_mark_appeared_and_none_went_missing` (Z. 329-345) um die siebte begruendete Ausnahme (Pitfall 2, nicht einfach "gruen machen"). Neuer Pin-Test nach `test_the_word_list_is_held_through_its_debian_pin` (Z. 348-355):
```python
WNGERMAN_PIN = "wngerman=20161207-15"
...
    assert WNGERMAN_PIN in DOCKERFILE.read_text(encoding="utf-8"), WNGERMAN_PIN
```
-> `WDUTCH_PIN = "wdutch=1:2.20.19+1-3"`. Alle `expected_versions(...)`-Aufrufe dieser Datei (Z. 279, 293, 325, 342) bekommen den neuen keyword-Parameter.

### `backend/tests/test_index_open.py`

**Analog:** selbst. Registrierungs-Gate Z. 662-673 (bleibt 8, keine Registrierung unter `if`), Verhaltenstests Z. 676-722 (`FINDLING_LANGUAGES=de` schreibt trotzdem, fremde Kette antwortet) als Vorlage fuer "nl inaktiv -> Snowball-Kette, kein Automat gebaut (`dutch_build_count` unveraendert)" und "nl aktiv -> `gemeentebelastingen` ueber `belasting` in `body_nl`". Splitter-Gegenprobe nach `test_without_the_splitter_the_constituent_finds_nothing` (Z. 352). Stempeltest `test_the_stamp_leaves_the_two_marks_of_a_directory_alone` (Z. 853) um die nl-Marke erweitern; `test_expected_versions_names_every_mark_the_store_compares` (Z. 468).

### `backend/tests/test_index_rebuild.py` (D-08)

**Analog:** selbst (Fixture `FIXTURE = .../constituents_de.txt` Z. 85). Neuer erster Test: `FINDLING_REBUILD_FALLBACK=fullreindex` + Sprachdrift -> `rebuild_the_index` liefert `FALLBACK_TO_FULL_REINDEX`; danach Crawl + `stamp_after_rebuild`; pruefen, ob `languages`/`schema_version` je gestempelt werden. Ergebnis entscheidet, ob die nl-Marke eine dokumentierte Grenze erbt.

---

### `.github/workflows/deploy-harp.yml` Language proof + `test_language_proof_steps.py`

**Analog:** Schritt Z. 829-1163 (komplett gelesen). Fuenftes Dokument, kein fuenfter Schritt. Stellen, die mitziehen:
- Dokumente Z. 911-918: `printf 'De gemeentebelastingen voor dit jaar zijn verhoogd.\n' > "${RUNNER_TEMP}/language-proof-nlc.txt"` (reines ASCII, keine Oktal-Escapes noetig).
- Upload-Schleife Z. 920 `for lang in es it nl pt` -> `... pt nlc`.
- Poll-Schleife Z. 950 `missing=`, `case` Z. 956-961 `nlc) term=belasting ;;`.
- Treffer-Zuordnung Z. 1014-1023 (erster Treffer == Datei).
- Ergebnisseite Z. 1041-1059: "Four literal calls and no loop" -> fuenfter literaler Aufruf `?query=belasting`; `PAGE_CALLS_EXPECTED` im Gate auf 5.
- Loeschschleife Z. 1096 und Verschwinden-Messung Z. 1129-1141.
- Kommentarblock nach Muster Z. 886-896 mit der Querprobe "red without split_compound, measured 2026-09-25" (de/en/nl-ohne/nl-mit, Research Z. 395-401).
- Pruefung `entries | length >= 1`, nie Subline (Z. 963-976, Pitfall 7).

Gate `backend/tests/test_language_proof_steps.py` Z. 85-133: `DOCUMENTS`, `QUESTIONS`, `PAGE_CALLS_EXPECTED = 4` erweitern; Schrittname `PROOF_STEP` Z. 90 ("the four new chains") bleibt oder wird bewusst umbenannt (dann beide Stellen). `_CLEAN`-Beispiel Z. 503ff und `scan_proof_step` Z. 239 lesen die Listen.

### Doku

- `docs/language-analyzers.md` Z. 440-446 ("**Compounds are German only.** ... scheduled for phase 21") umschreiben.
- `backend/src/findling/index/schema.py` Z. 170-171 Kommentar ("Its chain has no compound splitter") aktualisieren; `schema.py` sonst unveraendert (keine Schemaaenderung).
- `docs/performance.md`: Posten +17,6 MB (freigegeben), 23-MB-Richtigstellung.
- `docs/german-analyzer.md` als Strukturvorlage fuer `docs/dutch-analyzer.md` (oder Abschnitt in `language-analyzers.md`, Discretion).

## Shared Patterns

### Marke, die wie die Sprachmarke reist
**Source:** `open.py` Z. 62-76, 288, 340-341; `repo.py` Z. 81-88, 177-199, 756-771, 1465-1489, 1553-1555; `rebuild.py` Z. 226-233, 877-931
**Apply to:** open.py, repo.py, rebuild.py, alle `expected_versions`-Aufrufer, test_store_repo.py, test_upgrade_compatibility.py
Jede Sonderbehandlung von `languages` bekommt ein Gegenstueck; zwei Schreibweisen (open.py `Final` + repo.py Literal) werden von einem Test zusammengehalten.

### Artefakt fail closed mit Identitaetsschluessel
**Source:** `wordlist.py` Z. 207-335
**Apply to:** wordlist_nl.py
Digest-Datei `.sha256` neben dem Artefakt, Schluessel `(path, digest, size, mtime_ns)`, Lock, Zaehler als Testhebel, Log mit Anzahl und Zaehler.

### Singleton je Digest + Build-Zaehler
**Source:** `analyzer.py` Z. 137-152, 331-344
**Apply to:** `cached_dutch_analyzer`, alle Tests, die "nur einmal gebaut" oder "ohne nl nie gebaut" behaupten.

### Messmodus nur Zahlen (T-02-14)
**Source:** `wordlist.py` Z. 338-399, `analyzer.py` Z. 347-404, `compound_probe.py` Z. 26-31
**Apply to:** wordlist_nl.measure, compound_probe_nl.py, measure_compounds_nl.sh

### Paket-Pin, fail-closed Build, Artefakt-Gate
**Source:** `Dockerfile` Z. 172-211, `docker.yml` Z. 223-291, `test_upgrade_compatibility.py` Z. 96-99, 348-355
**Apply to:** Abbild-Plan (Dockerfile, docker.yml, THIRD-PARTY.md, Pin-Test)

### Gegenprobe ueber die ausgelieferte Fabrik
**Source:** `compound_probe.py` Z. 63-71; deploy-harp Kommentar Z. 886-896
**Apply to:** Sonde, CI-Fall, Kettentests: gemessen wird ueber `dutch_analyzer` UND `snowball_analyzer("dutch")`, nie ueber eine nachgebaute Kette.

### Qualitaetsgates
ruff-Vollregelsatz, `ruff format --check`, pyright basic (`PYRIGHT_PYTHON_FORCE_VERSION=latest`), vulture. Vulture-Hinweis aus `analyzer.py` Z. 288-292: keine ungenutzten Caches/Konstanten anlegen; ein `DUTCH_LIST_OFF`, das nur in Tests gelesen wird, braucht einen echten Leser in `src`.

## No Analog Found

| File/Element | Role | Data Flow | Reason |
|---|---|---|---|
| `wordlist_nl.dutch_mark(languages)` / `dutch_constituents_for(languages)` | utility | transform | Es gibt heute keine Wortliste, deren Laden an der Sprachmenge haengt; die deutsche Liste wird immer gebaut. Vorlage ist nur die Research (Pattern 2), Kern: bei inaktivem nl `"off"` bzw. `None`, ohne die Quelle oder das Artefakt anzufassen. |

## Metadata

**Analog search scope:** `backend/src/findling/{index,store,worker,api,tools,extract}`, `backend/tests` (+ fixtures), `scripts/dev`, `.github/workflows/{docker,deploy-harp}.yml`, `backend/Dockerfile`, `THIRD-PARTY.md`, `docs/`
**Files scanned:** 24 gelesen oder gezielt gegrept
**Pattern extraction date:** 2026-09-25
