# Phase 17: Owner-Tor und Analyseketten , Research

**Researched:** 2026-09-23
**Domain:** Tantivy-Analyseketten für es/it/nl/pt, Snowball-Stemmer und -Stoppwortlisten, Versionsmarken und Owner-Entscheid
**Confidence:** HIGH für alles, was unten mit einer Zahl steht (selbst gemessen gegen `tantivy==0.26.0` in `backend/.venv` und gegen ein frisch installiertes `tantivy==0.26.2`), HIGH für die Repo-Befunde (am Quelltext gelesen), MEDIUM für die Frage, welche der beiden gleichwertigen Kettenreihenfolgen die Nutzer eines Tages glücklicher macht , das ist nach der Messung kein Messproblem mehr, sondern eine Produktabwägung.

---

## Summary

Der Widerspruch zwischen STACK, FEATURES und PITFALLS ist aufgelöst, und zwar so: **alle drei haben richtig gemessen, und alle drei haben aus einer Teilmenge eine allgemeine Empfehlung gezogen.** Die Faltung vor dem Stemmer bricht bei Spanisch und Portugiesisch die Numerus-Paare der Klasse `-ción`/`-ção` (PITFALLS hat recht). Die Faltung hinter dem Stemmer bricht bei denselben Sprachen die Akzent-Paare derselben Wörter (STACK hat recht). Die Faltung vor der Stoppwortliste lässt akzentuierte Stoppwörter durch (FEATURES hat recht). Es gibt **keine Kette, die alle drei Kriterien gleichzeitig erfüllt**, und das ist kein Versäumnis der drei Recherchen, sondern eine Eigenschaft der romanischen Snowball-Algorithmen.

Die eigene, zusammengeführte Messung über 65 Wortfamilien und 573 geordnete Formpaare (unten, Abschnitt 2) zeigt, dass die beiden ernsthaften Kandidaten sich **um 4 von 573 Paaren unterscheiden**, also praktisch gleichauf liegen, und dass sie in verschiedene Richtungen ausschlagen: `fold früh` gewinnt Italienisch (+2) und Portugiesisch (+6), `fold spät` gewinnt Spanisch (+4), Niederländisch ist ein exaktes Unentschieden. Der unstrittige Teil ist dagegen eindeutig: **Ohne die gefaltete Ergänzungs-Stoppwortliste (77 es, 10 it, 0 nl, 30 pt, zusammen 117 Wörter) leckt jede der Ketten Stoppwörter**, jede in ihrer eigenen Schreibweise. Die Liste ist also keine Reparatur für eine bestimmte Reihenfolge, sie ist in jeder Reihenfolge Pflicht.

Der zweite Befund dieser Recherche ist wichtiger als der erste, weil er ein Erfolgskriterium der Phase direkt trifft: **Der Sprung `tantivy==0.26.0` auf `0.26.2` bewegt eine Versionsmarke und löst damit auf jeder Bestandsinstallation einen vollen Reindex aus.** `expected_versions()` speichert den vollen Banner `"tantivy v0.26.0, index_format v7"`; `Store.version_mismatch` vergleicht ihn auf Gleichheit; `start_rebuild_on_drift` hebt daraufhin die Generation. Drei CI-Zusicherungen in `deploy-harp.yml` (gleiche Marken, kein Banner, keine Drift-Zeile) und ein Gate in `backend/tests/test_upgrade_compatibility.py` werden rot, und zwar mit genau der Meldung, die sie dafür vorgesehen haben. Das ist kein Unfall, sondern ein funktionierendes Gate: Phase 16 hat den Dependabot-Vorschlag auf 0.26.2 aus genau diesem Grund abgewiesen (Lauf 35556667085). Phase 17 muss diese Tür bewusst öffnen, sonst kollidiert LEX-07 mit Erfolgskriterium 4.

**Primary recommendation:** Kette einheitlich `lowercase -> ascii_fold -> stopword(lang) -> custom_stopword(gefaltet) -> remove_long -> stemmer(lang)` für alle vier neuen Sprachen (Rezept A+ aus STACK), die Ergänzungsliste maschinell aus `stopwords.rs` erzeugt und per Hash gehalten; `tantivy` auf 0.26.2 nur zusammen mit einer gelockerten Vergleichsregel für `tantivy_version` (die `index_format`-Hälfte entscheidet, der volle Banner wird weiter gespeichert); Sprachnamen über `LANGUAGE_ALLOWLIST` als Schnittmenge aus Stemmer- und Stoppwortsprachen (13 Kandidaten, davon 6 im Produkt), Muster `OCR_LANGUAGE_ALLOWLIST`.

---

## Phase Requirements

| ID | Beschreibung (aus REQUIREMENTS.md) | Research Support |
|----|-------------------------------------|------------------|
| LEX-01 | Vier Analyseketten mit Snowball-Stemmer und Stoppwortliste; `ascii_fold`-Position je Sprache MESSEND abgenommen; Abnahmekriterium ist die zusammengeführte Testfall-Tabelle aus STACK/FEATURES/PITFALLS | Abschnitte 2 und 3: die Messung ist durchgeführt, die Tabelle liegt vor, das Messskript ist vollständig abgedruckt und läuft ohne Container. Verdikt je Sprache in 2.4. |
| LEX-07 | `tantivy` auf 0.26.2 gepinnt (stopword-Panic wird ValueError, Union-Scorer-Fix, `index_format v7` unverändert); Sprachnamen über eine Positivliste analog `OCR_LANGUAGE_ALLOWLIST` | Abschnitt 4: Panic-Klasse exakt bestimmt (5 Sprachen), `index_format v7` in beiden Fassungen gemessen, Index in beide Richtungen les- und schreibbar, Tokenisierung über 224 Zeilen identisch. **Achtung:** Der behauptete "Union-Scorer-Fix" ist in den Release Notes von 0.26.2 nicht auffindbar (Abschnitt 4.3). Abschnitt 5: Entwurf der Positivliste. |

---

## Project Constraints (from CLAUDE.md)

Verbindlich für jeden Plan dieser Phase, aus `CLAUDE.md` gelesen:

| Regel | Konsequenz für Phase 17 |
|---|---|
| Code Englisch, Projektkommunikation Deutsch | Docstrings und Bezeichner Englisch; `17-*-ENTSCHEID.md` und `docs/`-Text Deutsch |
| Keine Em-Dashes (U+2014, U+2013) | Gilt auch für Python-Docstrings und Markdown; es gibt dafür bereits Gates im Repo |
| Echte Umlaute nur in deutscher Prosa, nie in Code | Die Testwörter sind Daten, keine Bezeichner. Vorbild: `backend/tests/test_analyzer.py` schreibt Umlaute ausschliesslich in String-Literalen und begründet das im Modulkopf. Für es/it/nl/pt gilt dasselbe für Akzente. |
| Qualitätsgates: ruff-Vollregelsatz, pyright basic, vulture, lokal grün vor Commit | `uv run ruff check`, `uv run ruff format --check`, `uv run pyright`, `uv run vulture`, `uv run python -m pytest -q`, alle aus `backend/`. Dev-Skripte unter `scripts/` laufen nur durch ruff, mit `--config backend/pyproject.toml` (docs/testing.md, Zeilen 20 bis 36). |
| `INDEX_WORKERS=1`, OCR und Embedding strikt seriell | Berührt diese Phase nicht, weil kein Indexpfad angefasst wird. |
| Owner-Regel 15.08.2026: nach jeder Phase Security-, Bug- und Performance-Audit | Gilt auch hier; die Phase ändert eine Eingabevalidierung (Positivliste), also ist der Security-Teil nicht leer. |
| Owner-Regel 07.09.2026: kurze Produkttexte, Owner-Abnahme vor Release | Betrifft HART-05/Phase 23, aber die dokumentierten Grenzen entstehen in dieser Phase (Abschnitt 3.5). |

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Analyseketten es/it/nl/pt bauen | Backend / Indexkern (`index/analyzer.py`) | - | Die Kette ist Teil der Daten: Index- und Frageseite benutzen dasselbe registrierte Tokenizer-Objekt. Es gibt keine zweite Stelle, an der sie leben dürfte. |
| Gefaltete Ergänzungs-Stoppwortliste | Backend / Indexkern (Konstante neben `FUGEN` in `index/wordlist.py` oder eigenes Modul) | Dev-Skript (`scripts/dev/`) erzeugt sie | Erzeugung gehört ins Werkzeug, Auslieferung in den Code. Vorbild: `FUGEN` plus `measure_compounds.sh`. |
| Sprachnamen-Positivliste | Backend / Konfiguration (`config.py`) | - | `config.py` ist im Repo die einzige Stelle, an der Umgebungsvariablen zu Werten werden, und `OCR_LANGUAGE_ALLOWLIST` steht schon dort. |
| Versionsmarken und Drift-Entscheid | Backend / Indexkern (`index/open.py`) plus Store (`store/repo.py`) | CI (`deploy-harp.yml`) | `open.py` weiss, was der Code erzeugt, `repo.py` weiss, was auf der Platte steht, und nur der Aufrufer entscheidet. Diese Trennung steht so im Docstring und darf nicht aufgeweicht werden. |
| Owner-Entscheid | Planungsebene (`.planning/phases/17-.../17-*-ENTSCHEID.md`) | - | Vorbild `12-STABLE35-ENTSCHEID.md`: das Dokument liegt in der Phase, nicht in `docs/`, weil es einen Entscheid festhält und keine Produktdokumentation ist. |
| Messbericht | `docs/measurements/2026-09-analyseketten/` plus `docs/language-analyzers.md` | - | Vorbild `docs/measurements/2026-09-komposita-rezept-a/` und `docs/german-analyzer.md`. |

---

## 1. Was die drei Recherchen wirklich gemessen haben

Die drei Positionen sind nicht drei Meinungen über dieselbe Messung, sondern drei Messungen über verschiedene Wortpaare. Nachgestellt und bestätigt:

| Quelle | Behauptung | Nachgemessen | Urteil |
|---|---|---|---|
| STACK.md | Kette A (`fold` früh) liefert für akzentuierte und flache Eingabe **immer denselben Term** | ja, 28 von 28 Akzentpaaren es, 24 von 24 pt | **bestätigt** |
| STACK.md | Kette A lässt akzentuierte Stoppwörter durch; Ergänzungsliste 77 es / 10 it / 30 pt / 0 nl schliesst die Lücke | ja, exakt diese Zahlen aus `stopwords.rs` Tag 0.26.2; mit Liste 0 Lecks in beiden Schreibweisen | **bestätigt** |
| STACK.md | Kette C (`fold` hinter dem Stemmer) ist "falsch", weil `informação` zu `inform` und `informacao` zu `informaca` wird | ja, exakt so gemessen | **bestätigt**, aber "falsch" ist zu stark, siehe unten |
| PITFALLS.md | `fold` vor dem Stemmer lässt `información` als `informacion` stehen, während `informaciones` zu `inform` wird | ja, exakt so gemessen | **bestätigt** |
| PITFALLS.md | Empfehlung `lowercase -> stopword -> remove_long -> stemmer -> ascii_fold` | die Empfehlung folgt aus einer Messung, die die flache Schreibweise nicht geprüft hat | **Empfehlung nicht tragfähig** |
| PITFALLS.md | `één` verschwindet bei `fold` zuerst ganz | ja | **bestätigt** (und unten als erwünscht bewertet) |
| FEATURES.md | Stoppwortlisten tragen echte Akzente und vergleichen exakt, frühes Falten leckt 3 pt / 2 es / 1 it | ja, in der Grössenordnung; die vollständige Zahl ist 30 pt / 77 es / 10 it, weil FEATURES nur je einen Satz geprüft hat | **bestätigt und nach oben korrigiert** |
| FEATURES.md | `ascii_fold` ist für es und pt zwingend, für it und nl gleichgültig | für nl bestätigt (Familienmetrik identisch in allen sieben Ketten), für it **widerlegt**: `qualità`/`qualita` fällt bei `fold` spät auseinander | **teilweise widerlegt** |
| FEATURES.md | Niederländische Betonungsakzente sind der Gegenfall, gehören aber in eine spätere `custom_stopword`-Liste | `fold` früh erledigt sie ohne jede Zusatzliste | **Vorschlag entbehrlich** |
| alle drei | Es gibt eine richtige Reihenfolge | **widerlegt.** Für es und pt gibt es keine Kette, die Akzent- und Numeruskonvergenz gleichzeitig herstellt | **neu** |

Die sachliche Wurzel, gemessen und nicht gelesen: Der spanische Snowball-Algorithmus trägt die Endung `ación` **mit** Akzent in seiner Suffixliste, die Pluralendung `aciones` **ohne**. Fällt der Akzent vor dem Stemmer, greift die Singularregel nicht mehr; fällt er danach, hat die flach getippte Singularform ihn nie gehabt. Dasselbe in Portugiesisch mit `ção`/`ções` und in der Klasse `alemán`/`alemanes`, `capitán`/`capitanes`, `francés`/`franceses`.

---

## 2. Die eigene Messung: Aufbau, Kandidaten, Ergebnis

### 2.1 Aufbau

* Werkzeug: `tantivy==0.26.2`, frisch in eine Wegwerf-venv installiert (`uv venv` plus `uv pip install`), Banner `tantivy v0.26.2, index_format v7`. Gegenprobe mit der Repo-venv (`tantivy==0.26.0`).
* Stoppwortlisten: `src/tokenizer/stop_word_filter/stopwords.rs` aus `quickwit-oss/tantivy`, Tag **0.26.2**, roh geladen und geparst. Gezählt: SPANISH 308 (84 akzentuiert), ITALIAN 279 (11), PORTUGUESE 203 (36), DUTCH 101 (0), GERMAN 231 (8). Die ersten fünf Zahlen decken sich mit STACK.md; bei Deutsch zählt STACK 7 Ergänzungsformen, gemessen sind es 8 (`daß` faltet zu `dass`, und `dass` steht nicht in der Liste). Für die deutsche Kette folgenlos, weil sie nicht faltet.
* Faltung: nicht mit `unicodedata` nachgebaut, sondern mit `Filter.ascii_fold()` selbst gefahren, damit die Ergänzungsliste exakt der Faltung des Produkts entspricht.
* Kein Container nötig. Anders als beim deutschen Splitter, der die Debian-Wortliste braucht, sind alle vier Stoppwortlisten und alle vier Stemmer in tantivy einkompiliert. Das Messskript läuft auf jeder Entwicklermaschine.

### 2.2 Die sieben Kandidaten

| Kürzel | Kette | Herkunft |
|---|---|---|
| A | `low, fold, stop, long, stem` | die vorhandene englische Kette, wörtlich kopiert |
| **A+** | `low, fold, stop, CSTOP, long, stem` | STACK.md |
| B | `low, stop, fold, long, stem` | FEATURES.md |
| B+ | `low, stop, CSTOP, fold, long, stem` | eigene Mischform |
| C | `low, stop, long, stem, fold` | PITFALLS.md |
| C+ | `low, stop, CSTOP, long, stem, fold` | eigene Mischform |
| D+ | `low, fold, stop, CSTOP, long, stem, fold` | doppelte Faltung, zur Kontrolle |

`CSTOP` ist `Filter.custom_stopword(<gefaltete Ergänzungsliste>)`.

### 2.3 Ergebnis

**Metrik.** Zwei getrennte Zähler für Akzentpaare und Flexionspaare verbergen genau das, worauf es ankommt, weil eine Kette ein Akzentpaar verlieren und ein Flexionspaar gewinnen kann und den Nutzer trotzdem gleich schlecht bedient. Deshalb wird über **Formfamilien** gemessen: für jedes Lemma alle Schreibweisen, die ein Mensch tippen oder ein Dokument tragen kann (akzentuiert und flach, Singular und Plural), und gezählt werden die geordneten Paare (getippte Form, Form im Dokument), die sich treffen. 100 Prozent heisst: jede Schreibweise findet jede andere.

**Formfamilien, geordnete Treffer von möglichen:**

| Sprache | Familien | Paare | A | **A+** | B | B+ | C | **C+** | D+ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| es | 20 | 208 | 174 | **174** | 174 | 174 | 178 | **178** | 174 |
| it | 14 | 56 | 56 | **56** | 56 | 56 | 54 | **54** | 56 |
| nl | 13 | 81 | 57 | **57** | 57 | 57 | 57 | **57** | 57 |
| pt | 18 | 228 | 180 | **180** | 180 | 180 | 174 | **174** | 180 |
| **Summe** | **65** | **573** | 467 | **467** | 467 | 467 | 463 | **463** | 467 |

**Stoppwort-Lecks (Wörter der eingebauten Liste, die trotzdem einen Term erzeugen):**

| Sprache | A (akz./flach) | A+ | B | B+ | C | C+ | D+ |
|---|---|---|---|---|---|---|---|
| es | 77 / 77 | **0 / 0** | 0 / 77 | 0 / 0 | 0 / 77 | 0 / 0 | 0 / 0 |
| it | 10 / 10 | **0 / 0** | 0 / 10 | 0 / 0 | 0 / 10 | 0 / 0 | 0 / 0 |
| nl | 0 / 0 | **0 / 0** | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| pt | 30 / 30 | **0 / 0** | 0 / 30 | 0 / 0 | 0 / 30 | 0 / 0 | 0 / 0 |

Lesart: Kette A (die kopierte englische) leckt beide Schreibweisen, die Ketten B und C lecken die flach getippte. Nur die Varianten mit `CSTOP` sind in beiden Schreibweisen dicht. **Die gefaltete Ergänzungsliste ist unabhängig von der Faltposition Pflicht**, und das ist das einzige Ergebnis dieser Messung, das keine Abwägung braucht.

**Zweite, unabhängige Stichprobe für Spanisch** (14 weitere Familien, gezielt aus der Akzentsuffix-Klasse `-ción`, `-án`, `-és`, `-en/-enes`): A+ 93 von 137, C+ 97 von 137. Das Vorzeichen bleibt, der Abstand bleibt klein (2,9 Prozentpunkte gegen 1,9 in der ersten Stichprobe).

**Die sechs Familien, die in jeder Kette kaputt sind, und wie sie kaputt sind (es):**

```
A+:  información=informacion  informacion=informacion  informaciones=inform
C+:  información=inform       informacion=informacion  informaciones=inform
```

Der Waisenplatz wandert, er verschwindet nicht. Bei `fold früh` ist die korrekt geschriebene Pluralform die Waise, bei `fold spät` die flach getippte Singularform.

**Weitere gemessene Einzelbefunde:**

* `D+` ist in jeder Sprache und jedem Wort **identisch** mit `A+`. Die zweite Faltung hinter dem Stemmer ist ein No-op, wenn vorn schon gefaltet wurde. Nicht einbauen.
* `B+` ist in der Familienmetrik identisch mit `A+`. Der einzige Unterschied liegt bei den niederländischen Betonungsakzenten: `A+` verwirft `één`, `vóór`, `hét`, `zó` vollständig, `B+` schreibt dafür die Terme `een`, `vor`, `het`, `zo` in den Index, die keine Anfrage je erreichen kann, weil die flache Schreibweise auf der Frageseite als Stoppwort fällt. `A+` ist damit sauberer, und der in REQUIREMENTS.md nach v1.4 verschobene Punkt "Niederländische Betonungsakzente als eigene `custom_stopword`-Liste" **entfällt ersatzlos**.
* Italienisch: `fold spät` reisst `qualità` (Term `qualit`) von `qualita` (Term `qual`) ab. Das ist der einzige italienische Fehlschlag überhaupt; `fold früh` ist dort mit 56 von 56 fehlerfrei.
* Niederländisch: die Familienmetrik ist in allen sieben Ketten gleich. Der niederländische Stemmer faltet selbst. FEATURES.md M3 bestätigt.
* Wortpaare, die in **jeder** Kette auseinanderfallen und deshalb in die dokumentierten Grenzen gehören: `ciudad`/`ciudades`, `joven`/`jóvenes`, `imagen`/`imágenes`, `examen`/`exámenes`, `huis`/`huizen`, `bedrijf`/`bedrijven`, `gemeente`/`gemeentes`, `café`/`cafés` und die gesamte portugiesische Klasse `informação`/`informações` (Terme `informaca` gegen `informaco`, in jeder Kette verschieden).
* Drei Wörter, um die sich die Recherchen streiten, stehen **gar nicht** in der jeweiligen Snowball-Liste und erzeugen deshalb in jeder Kette einen Term: it `già` (Term `gia`), it `però` (Term `per`), it `così` (Term `cos`), es `aún` (Term `aun`), es `sólo` (Term `sol`). Wer sie fallen sehen will, braucht eine eigene Liste; das ist eine Produktentscheidung und kein Kettenproblem.

### 2.4 Verdikt je Sprache

| Sprache | Messsieger | Abstand | Empfehlung |
|---|---|---|---|
| es | `fold spät` (C+) | +4 von 208 Paaren (1,9 Punkte), in der Zweitstichprobe +4 von 137 (2,9 Punkte) | **`fold früh` (A+)**, der Abstand wird von der Einheitlichkeit aufgewogen, siehe unten |
| it | `fold früh` (A+) | +2 von 56 Paaren, und A+ ist fehlerfrei | **`fold früh` (A+)** |
| nl | Unentschieden | 0 | **`fold früh` (A+)**, weil es die Betonungsakzente ohne Zusatzliste erledigt |
| pt | `fold früh` (A+) | +6 von 228 Paaren | **`fold früh` (A+)** |

**Begründung für die einheitliche Kette trotz des spanischen Gegenbefunds:**

1. Der Abstand ist in beiden Richtungen unter drei Prozentpunkten und beruht in Spanisch auf genau einer Wortklasse (`alemán`/`alemanes`).
2. `fold früh` ist die Form der schon ausgelieferten englischen Kette. Mit einer leeren Ergänzungsliste ist `Filter.custom_stopword([])` **gemessen ein No-op** (13 Testwörter, identische Tokens mit und ohne), also kann eine einzige Fabrik `en`, `es`, `it`, `nl` und `pt` bedienen, ohne die englische Tokenisierung um ein Byte zu verschieben. Deutsch bleibt die begründete Ausnahme. Fünf Ketten aus einer Fabrik gegen vier Ketten aus einer zweiten Fabrik mit umgedrehter Reihenfolge ist der Unterschied zwischen einer Regel und zwei Regeln.
3. Das Produkt liest OCR. Ein Scan, dem der Akzent verlorengeht, ist bei `fold früh` weiterhin unter der korrekten Schreibweise auffindbar, bei `fold spät` nicht mehr. Diese Richtung ist bei einer Dokumentensuche mit Tesseract im Pfad die häufigere.
4. `fold spät` produziert in it und nl zusätzlich Terme, die keine Anfrage erreichen kann (`perc`-Klasse ohne Ergänzungsliste, `vor`/`het`/`zo` mit ihr).

**Der Preis, der in die Dokumentation muss (HART-05):** `información` findet `informaciones` nicht und umgekehrt; dasselbe für `administración`, `facturación`, `resolución`, `notificación` und die ganze `-ción`-Klasse sowie für `alemán`/`alemanes`. Portugiesisch trennt `informação` von `informações` in jeder Kette. Dazu die schon bekannte Zusammenführung `año` gleich `ano`.

---

## 3. Das Messskript, so wie die Phase es übernehmen kann

### 3.1 Form und Ablage

Vorbild ist die deutsche Kette, die im Repo schon genau dieses Muster trägt:

| Rolle | Deutsch (vorhanden) | Vorschlag für diese Phase |
|---|---|---|
| Sonde | `scripts/dev/compound_probe.py` | `scripts/dev/chain_probe.py` |
| Treiber | `scripts/dev/measure_compounds.sh` (Container, weil Debian-Liste) | `scripts/dev/measure_chains.sh` (**kein Container nötig**, `uv run` genügt) |
| Fixture | `backend/tests/fixtures/compound_cases_de.txt` | `backend/tests/fixtures/chain_cases_es.txt` usw., je Sprache eine Datei, eine Formfamilie je Zeile |
| Tabellentest | `backend/tests/test_analyzer.py` | Erweiterung derselben Datei oder `backend/tests/test_language_analyzers.py` |
| Bericht | `docs/measurements/2026-09-komposita-rezept-a/` | `docs/measurements/2026-09-analyseketten/` |
| Produktdoku | `docs/german-analyzer.md` | `docs/language-analyzers.md` |

Die Sonde darf im laufenden Betrieb niemals Nutzertext sehen. Für den deutschen Splitter ist diese Regel als T-02-14 im Modulkopf festgehalten; hier ist sie leichter einzuhalten, weil die Sonde ausschliesslich veröffentlichte Snowball-Stoppwörter und die Fixture-Dateien des Repos liest.

### 3.2 Die Sonde

Der folgende Quelltext ist gelaufen und hat die Zahlen aus Abschnitt 2 erzeugt. Er ist hier vollständig abgedruckt, damit der Plan ihn nicht neu erfinden muss; für die Aufnahme ins Repo braucht er englische Docstrings, ruff-konforme Formatierung und die Auslagerung der Wortlisten in Fixtures.

```python
"""Measure the position of ascii_fold in the four new analysis chains.

Reads the Snowball stopword lists out of the tantivy source of the pinned tag,
derives the folded supplement per language, builds every candidate chain and
runs the united test vocabulary through all of them.

No user content is touched: every word is either a published Snowball stopword
or a case from the fixture files of this repository.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from tantivy import Filter, TextAnalyzerBuilder, Tokenizer

MAX_TOKEN_CHARS = 48
LANGS = ("spanish", "italian", "dutch", "portuguese")
CODE = {"spanish": "es", "italian": "it", "dutch": "nl", "portuguese": "pt"}


def parse_stopwords(path: Path) -> dict[str, list[str]]:
    """Return {language: [word, ...]} from tantivy's stopwords.rs."""
    text = path.read_text(encoding="utf-8")
    out: dict[str, list[str]] = {}
    marker = "pub const "
    pos = 0
    while True:
        start = text.find(marker, pos)
        if start < 0:
            break
        name_end = text.find(":", start)
        name = text[start + len(marker) : name_end].strip()
        body_start = text.find("&[", name_end) + 1
        body_end = text.find("];", body_start)
        words = [chunk.strip().strip('"') for chunk in text[body_start + 1 : body_end].split(",")]
        out[name.lower()] = [w for w in words if w]
        pos = body_end
    return out


def fold(word: str) -> str:
    """Fold exactly the way tantivy folds, by running its own filter."""
    folder = TextAnalyzerBuilder(Tokenizer.raw()).filter(Filter.ascii_fold()).build()
    tokens = folder.analyze(word)
    return tokens[0] if tokens else ""


def folded_supplement(words: Sequence[str]) -> list[str]:
    """Return the folded forms the built in list does not already carry."""
    have = set(words)
    extra: list[str] = []
    for word in words:
        folded = fold(word)
        if folded and folded != word and folded not in have and folded not in extra:
            extra.append(folded)
    return extra


def chain(language: str, recipe: str, supplement: Sequence[str]):
    """Build one candidate chain. The recipe names the fold position."""
    builder = TextAnalyzerBuilder(Tokenizer.simple()).filter(Filter.lowercase())
    if recipe in ("A", "Aplus", "Dplus"):
        builder = builder.filter(Filter.ascii_fold())
    builder = builder.filter(Filter.stopword(language))
    if recipe in ("Aplus", "Bplus", "Cplus", "Dplus"):
        builder = builder.filter(Filter.custom_stopword(list(supplement)))
    if recipe in ("B", "Bplus"):
        builder = builder.filter(Filter.ascii_fold())
    builder = builder.filter(Filter.remove_long(MAX_TOKEN_CHARS))
    builder = builder.filter(Filter.stemmer(language))
    if recipe in ("C", "Cplus", "Dplus"):
        builder = builder.filter(Filter.ascii_fold())
    return builder.build()


def family_score(analyzer, forms: Sequence[str]) -> tuple[int, int, dict[str, list[str]]]:
    """Ordered pairs of surface forms that share at least one term."""
    terms = {form: analyzer.analyze(form) for form in forms}
    hits = 0
    total = 0
    for left in forms:
        for right in forms:
            total += 1
            if terms[left] and terms[right] and set(terms[left]) & set(terms[right]):
                hits += 1
    return hits, total, terms
```

Aufruf je Sprache und Kette: Familien aus der Fixture lesen, `family_score` summieren, danach die Dichtheit der Stoppwortliste prüfen, indem jedes Wort der eingebauten Liste und jede gefaltete Form davon durch die Kette geschickt wird und einen leeren Tokenstrom liefern muss.

### 3.3 Die Fixture-Form

Eine Zeile je Formfamilie, Formen durch Leerzeichen getrennt, Kommentare mit `#`. Beispiel `chain_cases_es.txt`:

```
# lemma: alle Schreibweisen, die ein Mensch tippt oder ein Dokument traegt
información informacion informaciones
administración administracion administraciones
alemán aleman alemanes alemana alemanas
año ano años anos
ciudad ciudades
```

Damit ist die Abnahme nicht "die Kette liefert Tokens", sondern eine Zahl je Sprache, und ein Eintrag, der unter der Zielkette nicht perfekt ist, steht als bekannter Verlust in einer zweiten Fixture (`chain_known_losses_es.txt`), damit der Test rot wird, sobald ein Verlust dazukommt **oder** verschwindet. Das ist dieselbe Strenge, die `test_analyzer.py` schon für die deutschen Komposita fährt ("This table asserts WHAT is split, not THAT something was split").

### 3.4 Die zusammengeführte Testfall-Tabelle (Erfolgskriterium 2)

Alle in ROADMAP und LEX-01 benannten Fälle, mit dem gemessenen Ergebnis unter der empfohlenen Kette A+:

| # | Fall | Quelle | Ergebnis unter A+ | grün? |
|---|---|---|---|---|
| 1 | `información` / `informacion` (Akzentkonvergenz) | STACK, LEX-01 | beide `informacion` | ja |
| 2 | `información` / `informaciones` (Numerus) | PITFALLS, LEX-01 | `informacion` gegen `inform` | **nein, dokumentierter Verlust** |
| 3 | `informação` / `informacao` | STACK, LEX-01 | beide `informaca` | ja |
| 4 | `informação` / `informações` | PITFALLS, LEX-01 | `informaca` gegen `informaco` | **nein, in jeder Kette** |
| 5 | `informações` / `informacoes` | STACK | beide `informaco` | ja |
| 6 | `año` / `ano` | PITFALLS, LEX-01 | beide `ano`, bewusster Recall-Kauf | ja |
| 7 | `perché` als Stoppwort, akzentuiert und flach | FEATURES, PITFALLS, LEX-01 | beide leer | ja |
| 8 | `più` als Stoppwort, beide Schreibweisen | PITFALLS | beide leer | ja |
| 9 | `één` / `een` (Betonungsakzent gegen Stoppwort) | FEATURES, LEX-01 | beide leer, kein Mülltoken | ja |
| 10 | akzentuierte Stoppwörter es, alle 84 | FEATURES, LEX-01 | 0 Lecks, akzentuiert wie flach | ja |
| 11 | akzentuierte Stoppwörter pt, alle 36 | FEATURES, LEX-01 | 0 Lecks | ja |
| 12 | akzentuierte Stoppwörter it, alle 11 | FEATURES | 0 Lecks | ja |
| 13 | `qualità` / `qualita` | neu aus dieser Messung | beide `qualit` | ja |
| 14 | `città` / `citta`, `società`, `università` | STACK | je gleicher Term | ja |
| 15 | `coördinatie` / `coordinatie`, `financiën` / `financien` | FEATURES | je gleicher Term | ja |

Die beiden roten Zeilen sind das, was die Phase datiert als Verdikt festhalten muss: sie sind nicht reparierbar, ohne einen anderen Fall rot zu machen.

### 3.5 Was aus dieser Messung in die Doku muss

`docs/language-analyzers.md`, im Aufbau von `docs/german-analyzer.md` (Kettenordnung mit Begründung je Position, Messzahlen, bekannte Grenzen):

* die Kette je Sprache mit dem Grund je Filterposition,
* die Herkunft und der Hash der Ergänzungsliste,
* die Tabelle aus 3.4 mit Datum,
* der Abschnitt "Bekannte Grenzen": `-ción`/`-ção`-Numerus, `año` gleich `ano`, `ciudad`/`ciudades`, `huis`/`huizen`, keine pt-Rechtschreibvereinheitlichung, Komposita nur de und nl, Französisch ohne Körperfeld.

---

## 4. tantivy 0.26.0 auf 0.26.2

### 4.1 Der Befund, der ein Erfolgskriterium trifft

`backend/src/findling/index/open.py` speichert als Versionsmarke den **vollen Banner**:

```python
TANTIVY_VERSION: Final[str] = tantivy.__version__      # "tantivy v0.26.0, index_format v7"
...
"tantivy_version": TANTIVY_VERSION,
```

`Store.version_mismatch` vergleicht auf Gleichheit (Ausnahmeregel gibt es nur für `index_version`), `start_rebuild_on_drift` hebt bei Abweichung die lokale Generation, die Admin-Seite zeigt das Reindex-Banner und empfiehlt `occ findling:index --restart`. Das heisst: **allein der Patch-Sprung löst auf jeder Bestandsinstallation den vollen Crawl aus** , gemessen 19 h 20 min für 52.137 Dokumente.

Was dabei rot wird, alles gewollt und alles zu behandeln:

| Ort | Zusicherung | Reaktion auf den Pin-Sprung |
|---|---|---|
| `backend/tests/test_upgrade_compatibility.py`, `GOLD_V1_0_AND_V1_1` | `tantivy_version` enthält `"0.26.0"` | rot, Meldung: "ein Upgrade von 1.0.x oder 1.1.x wuerde jetzt einen Reindex ausloesen (D-04)" |
| dieselbe Datei, `TANTIVY_PIN = "tantivy==0.26.0"` | der Pin in `pyproject.toml` | rot |
| dieselbe Datei, `GOLD_INDEX_FORMAT = "index_format v7"` | die Formathälfte | **bleibt grün**, v7 ist unverändert |
| `.github/workflows/deploy-harp.yml`, "Store upgrade 5", Zusicherung 2 | `.marks.tantivyVersion` unverändert | rot |
| dieselbe Stelle, Zusicherung 4 | kein Reindex-Banner | rot |
| dieselbe Stelle, Zusicherung 5 | keine Zeile "built by different code" im Containerlog | rot |
| `.github/dependabot.yml` | kein `ignore`-Eintrag für tantivy (Phase-16-Vorschlag, nie umgesetzt) | Dependabot schlägt 0.26.2 weiterhin vor |

Der Kommentarblock über der Beweisstrecke benennt den Fall sogar wörtlich: "the day a mark really moves, assertion 2 below turns red before the two absence assertions do, and the question that follows belongs to the owner and not to a test edit." Genau diese Frage steht jetzt an, und sie gehört ins Owner-Tor.

### 4.2 Die Belege, mit denen die Tür aufgeht

Alles selbst gemessen:

| Beleg | Ergebnis |
|---|---|
| Indexformat beider Fassungen | `tantivy v0.26.0, index_format v7` und `tantivy v0.26.2, index_format v7` |
| Index mit 0.26.0 geschrieben, mit 0.26.2 geöffnet und durchsucht | `num_docs=1 hits=1`, Dokument unverändert zurück |
| Index mit 0.26.2 geschrieben, mit 0.26.0 geöffnet und durchsucht | `num_docs=1 hits=1`, also auch rückwärts, was den Rückweg eines missglückten Upgrades offenhält |
| Tokenisierung: 7 Ketten (de mit Splitter, en, name, es, it, nl, pt) über 32 Wörter, 224 Zeilen | `diff` leer, kein Unterschied zwischen 0.26.0 und 0.26.2 |
| Rad-Matrix auf PyPI | 0.26.0: 31 Dateien, 0.26.2: 26. Der Unterschied sind die weggefallenen `cp313t`-Räder (free-threaded). `cp313` manylinux_2_17 **aarch64** und **x86_64** sind vorhanden, also bleibt der ARM-Zielpfad bedient. Keine musllinux-Räder, in beiden Fassungen nicht; das Image ist glibc-basiert (`python:3.13-slim-trixie`). |

**Empfehlung:** Den Banner weiter speichern (er ist für die Diagnose wertvoll), aber die **Vergleichsregel** lockern: `tantivy_version` gilt als unverändert, solange die `index_format`-Hälfte gleich ist. Das ist derselbe Musterbruch, den `index_version` schon hat (Untergrenze statt Gleichheit), es steht an derselben Stelle (`Store.version_mismatch`), und die aufgegebene Absicherung ("tantivy könnte die Tokenisierung ändern, ohne das Format zu ändern") wird durch die Tabellentests aus Abschnitt 3 ersetzt, die diese Phase ohnehin baut und die eine geänderte Tokenisierung sofort rot machen.

Zweitbeste Lösung, falls der Owner die Regel nicht lockern will: Pin auf 0.26.0 lassen und die Panic-Frage allein über die Positivliste schliessen (Abschnitt 5 zeigt, dass das vollständig trägt). Dann muss LEX-07 umformuliert werden. Was **nicht** geht: den Pin bewegen und die Marke unverändert behaupten.

### 4.3 Was 0.26.2 wirklich bringt

Aus den Release Notes von `quickwit-oss/tantivy-py` (GitHub-API, Veröffentlichung 2026-09-17; ein Release 0.26.1 gibt es nicht) und aus der eigenen API-Diffprobe:

| Änderung | Relevanz |
|---|---|
| PR #734 "Handle stopword filters for languages without a builtin list" | **die eigentliche Begründung**, siehe Abschnitt 5 |
| PR #682 `Index.is_compatible(path)` neu | **relevant für Phase 18.** Prüft, ob das **Indexformat** dieser Fassung lesbar ist, und gibt True/False zurück statt zu werfen (ValueError nur, wenn gar kein Index da ist). Es prüft **nicht** das Schema, löst also den Feldabweichungs-Fall von LEX-04 **nicht**. Wer es dafür hält, baut die Falle ein. |
| `Query.and_must_match`, `Query.and_must_not_match`, `Query.or_should_match` neu | Bequemlichkeit für Phase 19, nicht nötig |
| PR #666 `add_date` verliert tzinfo | betrifft Datumsfelder; das Schema dieses Projekts nutzt keine tantivy-Datumsfelder |
| `disjunction_max_query` | **existiert schon in 0.26.0.** MESS-09 braucht das Upgrade nicht. |
| "Union-Scorer-Bugfix" | **in den Release Notes von 0.26.2 nicht auffindbar.** Der Sprung enthält keinen Bump des Rust-Kerns tantivy (nur serde, serde_json, chrono, pyo3-build-config, itertools, futures). Die Behauptung aus SUMMARY/STACK ist damit unbelegt und sollte aus der Begründung gestrichen werden, statt sie in die Owner-Vorlage zu übernehmen. |

### 4.4 Wo der Pin überall steht

| Datei | Form | Bewegt sich mit |
|---|---|---|
| `backend/pyproject.toml` | `"tantivy==0.26.0"` | von Hand |
| `backend/uv.lock` | `name = "tantivy" / version = "0.26.0"`, plus Rad-URLs mit sha256 und `{ name = "tantivy", specifier = "==0.26.0" }` | `uv lock --upgrade-package tantivy`, niemals von Hand |
| `backend/tests/test_upgrade_compatibility.py` | `GOLD_V1_0_AND_V1_1["tantivy_version"]`, `TANTIVY_PIN` | von Hand, mit Begründung im Kommentar |
| `backend/tests/test_index_open.py:413,418` | Marke und `index_format`-Zusicherung | prüft gegen `TANTIVY_VERSION`, bleibt grün |
| `.github/dependabot.yml` | kein Eintrag | Vorschlag Phase 16: `ignore` mit Begründung |
| `THIRD-PARTY.md` | Lizenzliste | Versionsangabe prüfen |

Ablauf ohne Überraschung: erst `uv lock --upgrade-package tantivy` in `backend/`, dann `uv sync`, dann die volle Suite, dann die Gold-Werte und die CI-Zusicherung anpassen, jeweils mit dem Messbeleg aus 4.2 im Kommentar. Keine Handkante an `uv.lock`.

---

## 5. Die Sprach-Positivliste

### 5.1 Die Panic-Klasse ist kleiner und schärfer als gedacht

Gemessen, beide Fassungen, `Filter.stopword(x)` und `Filter.stemmer(x)` jeweils bis zum `build()`:

| Eingabe | 0.26.0 | 0.26.2 |
|---|---|---|
| `"klingon"`, `"estonian"`, `""` | `ValueError: Unsupported language: ...` | dasselbe |
| `"romanian"` bei `stopword` | **`PanicException: called Option::unwrap() on a None value`**, dazu eine Panic-Zeile auf stderr | `ValueError: No builtin stop word list for language: romanian` |
| `"romanian"` bei `stemmer` | funktioniert | funktioniert |

Die Panic trifft also **nur** Sprachen, die einen Stemmer haben, aber keine eingebaute Stoppwortliste. Gemessen sind das genau fünf: **arabic, greek, romanian, tamil, turkish**. `Filter.stemmer` kennt 18 Sprachen, `Filter.stopword` 13.

Der Fehler tritt beim `build()` auf, nicht bei `Filter.stopword(...)`. Ein Test, der nur die Filterkonstruktion prüft, ist grün und beweist nichts.

### 5.2 Entwurf der Konstante

Muster ist `OCR_LANGUAGE_ALLOWLIST` in `backend/src/findling/config.py:292`, mit der zugehörigen Leseroutine `_ocr_languages()` und dem Paritätstest `backend/tests/test_ocr_languages.py`, der Dockerfile und Konstante in **beide** Richtungen vergleicht. Der Bauplan überträgt sich fast eins zu eins:

```python
# The closed set of language names that may ever reach Filter.stopword and
# Filter.stemmer. It is the INTERSECTION of the two sets tantivy supports:
# 18 languages have a stemmer, 13 have a builtin stop word list, and the five
# in the difference (arabic, greek, romanian, tamil, turkish) are the ones that
# panicked the Rust side in 0.26.0 and raise a ValueError in 0.26.2. Neither is
# an acceptable answer to a typo in an environment variable, so neither is ever
# reached: this list is what the reader trusts.
LANGUAGE_ALLOWLIST = frozenset(
    {"danish", "dutch", "english", "finnish", "french", "german", "hungarian",
     "italian", "norwegian", "portuguese", "russian", "spanish", "swedish"}
)

# The six the product carries a body field for, as two letter codes, in schema
# field order. SUPPORTED_LANGUAGES maps them onto the Snowball names above.
SUPPORTED_LANGUAGES = ("de", "en", "es", "it", "nl", "pt")
SNOWBALL_NAME = {"de": "german", "en": "english", "es": "spanish",
                 "it": "italian", "nl": "dutch", "pt": "portuguese"}
```

Zwei Unterschiede zur OCR-Variante, beide bewusst:

1. Der Trenner ist das Komma, nicht das Plus (`FINDLING_LANGUAGES` ist schon kommagetrennt, `FINDLING_OCR_LANGUAGES` plusgetrennt, weil das die Tesseract-Syntax ist).
2. Die Reihenfolge des Admins wird **nicht** übernommen, sondern auf die Schema-Feldreihenfolge normalisiert. Das steht heute schon so in `_languages()` und ist wichtig, sobald die Sprachmenge eine Versionsmarke wird: `"es,de"` und `"de,es"` müssen denselben Merker ergeben, sonst löst eine umsortierte Umgebungsvariable einen Umbau aus.

Der zugehörige Test hat zwei Hälften, nach dem Muster von `test_ocr_languages.py`: eine Sprache in `SUPPORTED_LANGUAGES`, die nicht in `LANGUAGE_ALLOWLIST` steht, ist eine Panic in Wartestellung; eine Sprache in der Positivliste, für die tantivy keinen Stemmer **und** keine Stoppwortliste hat, ist eine falsche Zusage. Beide Richtungen werden gegen das laufende tantivy geprüft, nicht gegen eine zweite Liste im Test.

### 5.3 Was die Positivliste **nicht** löst

`FINDLING_LANGUAGES` ist heute (Zeile 1009 bis 1015) gegen `DEFAULT_LANGUAGES` gefiltert und fällt bei leerem Ergebnis auf `("de", "en")` zurück. Ein unbekannter Name erzeugt eine Warnung, nie einen Absturz. Das heisst: **die Panic ist auf dem heutigen Pfad gar nicht erreichbar**, weil kein Name aus der Umgebung je an `Filter.stopword` durchgereicht wird. Erreichbar wird sie erst in Phase 18, wenn die Kettenfabrik eine Sprache aus der Konfiguration bekommt. Die Positivliste ist also eine Vorwegnahme, keine Reparatur eines heutigen Lochs; sie gehört trotzdem in diese Phase, weil sie die Voraussetzung dafür ist, dass Phase 18 die Fabrik überhaupt an die Konfiguration hängen darf.

---

## 6. Das Owner-Tor: Wortlaut und Struktur

### 6.1 Form

Vorbild ist `12-STABLE35-ENTSCHEID.md` aus Phase 12, das im Repo als bestes Muster eines Owner-Tors vorliegt. Seine tragenden Eigenschaften:

* Das Dokument liegt in der Phase (`.planning/phases/17-.../17-GRUNDSATZ-ENTSCHEID.md`), nicht in `docs/`.
* Es trennt sauber **"Was festgestellt ist"**, **"Was unklar ist"** und **"Die Optionen"**, und jede Option ist **vollständig ausformuliert, bevor** der Owner gefragt wird, inklusive der fertigen Ersatztexte für die betroffenen Dateien. Am Entscheidungstag wird nur noch gelesen, welcher Zweig greift.
* Folgepläne zitieren die Optionskennung (`E-17-3 Option a`), nie eine Zusammenfassung.
* Es gibt einen Abschnitt "Vollzug am ...", der nachträglich gefüllt wird und Datum plus Plannummer trägt.
* Die Vorlage beim Owner ist eine eigene Aufgabe vom Typ `checkpoint:human-verify` mit `gate="blocking"`, deren Abnahmekriterien lauten: Owner hat "freigegeben" geschrieben **oder** benannt, was zu ändern ist; benannte Änderungen sind eingearbeitet und erneut vorgelegt; ohne Freigabe wurde das Requirement nicht als erfüllt gemeldet.

Für Phase 17 heisst das: **Plan 17-01 legt das Entscheiddokument mit allen Optionen an, ein später Plan legt es vor, und dazwischen darf kein Plan liegen, der D-04 berührt.** "D-04 berühren" ist scharf zu fassen, sonst blockiert das Tor die ganze Phase: es bedeutet jede Änderung, die eine der fünf Marken bewegt, ein Schemafeld anlegt oder die Query-Feldliste erweitert. Die Kettenmessung, die Positivliste und die Dokumentation berühren D-04 nicht und können vor dem Entscheid laufen. Der tantivy-Pin **berührt D-04** (Abschnitt 4.1) und muss hinter das Tor.

### 6.2 Die Entscheide, mit Empfehlung

| Kennung | Frage | Empfehlung | Belegt durch |
|---|---|---|---|
| E-17-1 | Umbauweg: Re-Analyse aus den gespeicherten Feldern oder Vollreindex über Nextcloud? | **Re-Analyse.** Vollreindex ist gemessen 19 h 20 min für 52.137 Dokumente, die Re-Analyse ist auf 1 bis 3 h geschätzt und wird in MESS-08 nachgemessen; `vectors.db` und `state.db` bleiben unberührt | ARCHITECTURE.md, PITFALLS Nr. 2, alle vier Recherchen einig |
| E-17-2 | Feldmodell: sechs Körperfelder immer im Schema, Befüllung nach `FINDLING_LANGUAGES`? | **Ja (Modell A).** Leere Felder kosten gemessen null Byte; Alternativen (Index je Sprache, ein multilinguales Feld) sind einstimmig abgelehnt | STACK-Messung, FEATURES, ARCHITECTURE |
| E-17-3 | Darf `FINDLING_LANGUAGES` Deutsch und Englisch **abschalten**? | **Ja, erlauben.** Eine spanische Behörde soll nicht zwei unbenutzte Felder befüllen. Das Abschalten ist ohnehin derselbe Vorgang wie das Zuschalten: der Sprachmerker bewegt sich und löst den Umbau aus. Werkseinstellung bleibt `de,en`. Gegenoption: `de` und `en` als Boden erzwingen, einfacher zu erklären, kostet Bestandsinstallationen aber nichts und neuen Installationen Platz | `config.py:_languages()` erlaubt heute schon `FINDLING_LANGUAGES=de` |
| E-17-4 | Sprachmenge als sechster Versionsmerker in `expected_versions()`? | **Ja**, als normalisierte, nach Schemafeldreihenfolge sortierte Zeichenkette. **Mit Auflage:** eine neue Marke, die es im Bestand nicht gibt, zählt in `Store.version_mismatch` als Abweichung und löst damit selbst den Reindex aus, den sie verhindern soll. Sie muss also wie `_DEFAULT_META` gesät oder beim Fehlen als `"de,en"` gelesen werden | `store/repo.py:version_mismatch` ("A mark that was never written counts as diverging") |
| E-17-5 | Katalogprozess: maschinell plus Community-Review mit datiertem Vorbehalt, ohne Muttersprachler-Gate? | **Ja**, FR-Muster aus `docs/l10n-french.md` | FEATURES, KAT-02 |
| E-17-6 | Go/No-Go für die niederländischen Komposita | **Im Scope behalten**, endgültiges Tor in Phase 21; Sturzkriterium ist der Termin, und sie fällt als Ganzes, nicht halb | KOMP-01, ROADMAP Phase 21 |
| **E-17-7 (neu)** | Darf die Vergleichsregel für `tantivy_version` gelockert werden (nur die `index_format`-Hälfte entscheidet), damit der Pin-Sprung keinen Feld-Reindex auslöst? | **Ja.** Belege in 4.2: Format v7 in beiden Fassungen, Index in beide Richtungen lesbar, Tokenisierung über 224 Zeilen identisch. Gegenoption: Pin auf 0.26.0 lassen und LEX-07 umformulieren; die Panic wird von der Positivliste ohnehin unerreichbar | diese Recherche |
| **E-17-8 (neu, zur Kenntnis)** | Einheitliche Kettenreihenfolge `fold früh` für alle vier Sprachen, obwohl Spanisch isoliert 2 bis 3 Punkte für `fold spät` spricht, mit den zwei dokumentierten Verlusten aus 3.4 | **Ja**, Begründung in 2.4. Als Kenntnisnahme mit Widerspruchsmöglichkeit vorlegen, nicht als offene Frage: LEX-01 macht die Messung zum entscheidenden Instrument, und die Messung liegt vor | diese Recherche |

### 6.3 Was vor dem Tor laufen darf

| Arbeit | Vor dem Tor? | Grund |
|---|---|---|
| Kettenmessung, Sonde, Fixtures, Messbericht | ja | verändert keine Marke, kein Feld, keine Query |
| `docs/language-analyzers.md` | ja | Dokumentation |
| `LANGUAGE_ALLOWLIST` plus Paritätstest | ja | die Konstante wird von nichts gelesen, solange die Fabrik nicht daran hängt |
| Die vier Analyse-Funktionen anlegen, **ohne** sie zu registrieren | ja, mit Vorsicht | sie ändern keine bestehende Kette; `ANALYZER_VERSION` bleibt deshalb auf 1. Der Modulkopf sagt "Any change to a chain below has to raise ANALYZER_VERSION" , eine hinzugefügte, nirgends registrierte Kette ist keine Änderung an einer bestehenden. Das gehört als Satz in den Modulkopf, sonst hebt der nächste Leser die Marke aus Vorsicht und löst genau das aus, was Erfolgskriterium 4 verbietet. |
| tantivy-Pin bewegen | **nein** | bewegt `tantivy_version`, siehe 4.1 |
| `english_analyzer()` in die gemeinsame Fabrik überführen | ja, wenn tokenidentisch | `Filter.custom_stopword([])` ist gemessen ein No-op; der Beweis gehört als Test dazu, sonst ist es eine stille Änderung der englischen Tokenisierung |

---

## 7. "Bestandsinstallation unverändert" als Testbeleg (Erfolgskriterium 4)

Das Repo hat die Belegkette schon; sie muss nur benannt und gefahren werden. Konkret heisst das Kriterium:

| Aussage | Beleg | Kommando oder Ort |
|---|---|---|
| Kein neues Schemafeld | Feldtabelle in `backend/tests/test_index_open.py` (tantivy bietet keine Feld-Introspektion, deshalb Tabelle) | `uv run python -m pytest tests/test_index_open.py -q` |
| Keine bewegte Versionsmarke | `GOLD_V1_0_AND_V1_1` und `drift_findings()` | `uv run python -m pytest tests/test_upgrade_compatibility.py -q` |
| Die fünf Marken im Gleichschritt | `tests/test_lockstep_versions.py` | `uv run python -m pytest tests/test_lockstep_versions.py -q` |
| Die Suchfeldliste hat sich nicht erweitert | `tests/test_search_fields_lockstep.py` | dito |
| Volle Suite grün | alles | `uv run python -m pytest -q` aus `backend/` |
| Gates grün | ruff, ruff format, pyright, vulture | `uv run ruff check`, `uv run ruff format --check`, `uv run pyright`, `uv run vulture` |
| Auf einer echten Instanz nichts bewegt | `deploy-harp.yml`, Job "Store upgrade 5", sechs Zusicherungen: gleiche Treffer für drei Begriffe, gleiche fünf Marken, gleiche Zählerstände, kein Reindex-Banner, keine Drift-Zeile im Log, plus die Gegenprobe, dass sich überhaupt etwas geändert hat | CI, `UPGRADE_FROM_TAG` steht heute auf `v1.1.0`; LEX-08 hebt ihn in Phase 18 auf `v1.2.0` |

**Die Falle:** Erfolgskriterium 4 und LEX-07 widersprechen sich, solange `tantivy_version` den vollen Banner vergleicht. Entweder fällt E-17-7 auf "lockern" (dann bleiben alle sieben Zeilen oben grün), oder der Pin wandert in Phase 18, wo der Umbau ohnehin läuft. Ein Plan, der den Pin bewegt und danach behauptet, es habe sich nichts bewegt, wird von der eigenen CI widerlegt , das ist der gute Fall. Der schlechte Fall ist ein Plan, der die Gold-Werte "anpasst", ohne den Reindex zu bemerken.

---

## 8. Don't Hand-Roll

| Problem | Nicht selbst bauen | Stattdessen | Warum |
|---|---|---|---|
| Stoppwortlisten für es/it/nl/pt | eigene Wortlisten pflegen | `Filter.stopword("spanish")` usw. | 308/279/101/203 Wörter, einkompiliert, BSD-3-Clause, AGPL-verträglich, null RAM |
| Stammformen | eigene Suffixregeln | `Filter.stemmer(...)`, Snowball | die Suffixlisten sind akzentsensitiv und genau darin liegt die ganze Schwierigkeit dieser Phase |
| Akzentfaltung | `unicodedata.normalize('NFD')` plus Filtern | `Filter.ascii_fold()` | tantivy faltet auch `ß` zu `ss` und `ñ` zu `n`; eine nachgebaute Faltung erzeugt eine Ergänzungsliste, die nicht zur Kette passt |
| Gefaltete Ergänzungsliste | von Hand abtippen | maschinell aus `stopwords.rs` erzeugen, Hash im Test halten | 117 Wörter; eine Handliste driftet beim nächsten tantivy-Sprung unbemerkt |
| Akzentvarianten auf der Frageseite | ein `accent_variants` analog `umlaut_variants` | gar nicht, weil beide Seiten dieselbe faltende Kette fahren | bei fünf Vokalen erzeugt eine Akzentrekonstruktion sechs Klauseln je Wort; die Faltung erledigt es in der Tokenisierung, auf beiden Seiten |
| Spracherkennung | lingua, fasttext, py3langid | nichts davon | Anti-Feature, einstimmig, aus RAM-, Lizenz-, ARM- und Fehlerverhaltensgründen |
| Prüfung, ob ein Bestandsindex zum Code passt | `Index.is_compatible()` dafür halten | eigener Schemavergleich in Phase 18 | `is_compatible` prüft das **Indexformat**, nicht das Schema |

**Kernsatz:** In dieser Phase entsteht kein einziges neues Paket und keine einzige neue Wortliste. Was entsteht, ist eine Reihenfolge, eine abgeleitete Liste und ein Messprotokoll.

---

## 9. Common Pitfalls

### Pitfall 1: Die englische Kette als Vorlage kopieren, ohne die Ergänzungsliste

**Was schiefgeht:** 77 spanische, 30 portugiesische und 10 italienische Stoppwörter landen als Terme im Index, in **beiden** Schreibweisen (Kette A in Abschnitt 2.3).
**Warum:** `Filter.ascii_fold()` läuft in der englischen Kette vor `Filter.stopword("english")`, und für Englisch ist das folgenlos, weil die englische Liste keine Akzente trägt.
**Vermeidung:** `Filter.custom_stopword(<gefaltete Liste>)` direkt hinter `Filter.stopword(lang)`, Liste maschinell erzeugt.
**Frühwarnzeichen:** Ein Stoppworttest, der nur unakzentuierte Wörter prüft.

### Pitfall 2: Der tantivy-Pin bewegt eine Versionsmarke

**Was schiefgeht:** Voller Reindex auf jeder Installation im Feld, 19 h 20 min, ausgelöst von einem Patch-Sprung.
**Warum:** `expected_versions()` speichert den vollen Banner, `version_mismatch` vergleicht auf Gleichheit.
**Vermeidung:** E-17-7 entscheiden, bevor der Pin angefasst wird. Abschnitt 4.1 listet alle sieben Stellen, die rot werden.
**Frühwarnzeichen:** Ein Plan, dessen Abnahmekriterium lautet "Gold-Werte auf 0.26.2 aktualisiert".

### Pitfall 3: Der neue Sprachmerker löst selbst den Reindex aus

**Was schiefgeht:** Ein sechster Merker `languages` existiert auf keiner Bestandsinstallation. `version_mismatch` liest eine fehlende Marke als Abweichung ("A mark that was never written counts as diverging"), also bekommt jede Bestandsinstallation genau den Umbau, den der Merker verhindern soll.
**Vermeidung:** Die Marke säen (Muster `_DEFAULT_META`) oder ihr Fehlen als `"de,en"` lesen. Gehört als Auflage in E-17-4 und als Test in Phase 18.

### Pitfall 4: `ANALYZER_VERSION` aus Vorsicht heben

**Was schiefgeht:** Erfolgskriterium 4 fällt, obwohl sich an der Tokenisierung nichts geändert hat.
**Warum:** Der Modulkopf sagt "Any change to a chain below has to raise ANALYZER_VERSION", und eine hinzugefügte Kette sieht nach einer Änderung aus.
**Vermeidung:** Den Satz im Modulkopf präzisieren ("a chain that is added but registered nowhere changes no tokenisation") und die Marke in Phase 17 ausdrücklich auf 1 halten. Sie steigt in Phase 18 zusammen mit dem Schema.

### Pitfall 5: Die gefaltete Ergänzungsliste von Hand pflegen

**Was schiefgeht:** Beim nächsten tantivy-Sprung wächst eine Snowball-Liste um drei Wörter, die Ergänzungsliste nicht, und drei Stoppwörter lecken still.
**Vermeidung:** Erzeugungsskript plus Hash-Test, genau wie die Komposita-Wortliste (`wordlist_hash`).

### Pitfall 6: Den Verdikt-Test mit unakzentuierten Wörtern bauen

**Was schiefgeht:** Der Test ist grün, egal wo `ascii_fold` steht (PITFALLS benennt das als Warnsignal, und es stimmt).
**Vermeidung:** Die Formfamilien-Metrik aus 2.3. Ein Test, der Paare zählt, kann nicht aus Versehen grün sein.

### Pitfall 7: `Index.is_compatible()` für den Schemavergleich halten

**Was schiefgeht:** Phase 18 baut den dritten Zweig in `open_index()` auf einer Prüfung, die das Schema gar nicht ansieht, und der Totalausfall-Pfad bleibt offen.
**Vermeidung:** Die Semantik steht im Docstring der Methode ("index format version"); sie gehört wörtlich in die Notiz an Phase 18.

### Pitfall 8: Das Owner-Tor blockiert die ganze Phase

**Was schiefgeht:** "Vor diesem Entscheid kein Code, der D-04 berührt" wird als "vor diesem Entscheid kein Code" gelesen, und die Phase steht.
**Vermeidung:** Die Tabelle in 6.3 wörtlich in den ersten Plan übernehmen.

---

## 10. Code Examples

### Die empfohlene Kette (eine Fabrik für fünf Sprachen)

```python
# Source: eigene Messung 2026-09-23, tantivy 0.26.2, Abschnitt 2 dieser Recherche
def snowball_analyzer(language: str, folded_stopwords: Sequence[str]) -> TextAnalyzer:
    """Build the chain for one Snowball language other than German.

    The fold stands in front of the stop word filter and therefore in front of
    the stemmer, and that position was measured rather than reasoned about: it
    is the only position that keeps the accented and the flat spelling of a
    word on one term, which is what a user who does not type accents and a scan
    that lost them both need. The price is measured too and it is documented in
    docs/language-analyzers.md: the class of words whose Snowball suffix
    carries an accent loses its number pair.

    folded_stopwords is the supplement the fold tears into the built in list.
    The built in lists compare exactly and carry real accents, so once the fold
    has run in front of them they no longer match. The supplement is derived
    from the same lists, so it cannot drift away from them. For English and
    Dutch it is empty, and an empty custom_stopword filter is measured to be a
    no-op, which is why English can use this factory without its tokenisation
    moving by one byte.
    """
    return (
        TextAnalyzerBuilder(Tokenizer.simple())
        .filter(Filter.lowercase())
        .filter(Filter.ascii_fold())
        .filter(Filter.stopword(language))
        .filter(Filter.custom_stopword(list(folded_stopwords)))
        .filter(Filter.remove_long(MAX_TOKEN_CHARS))
        .filter(Filter.stemmer(language))
        .build()
    )
```

### Die Ergänzungsliste erzeugen

```python
# Source: eigene Messung 2026-09-23. Laeuft im Dev-Skript, nicht im Produkt.
def folded_supplement(words: Sequence[str]) -> list[str]:
    """Return the folded forms the built in list does not already carry."""
    folder = TextAnalyzerBuilder(Tokenizer.raw()).filter(Filter.ascii_fold()).build()
    have = set(words)
    extra: list[str] = []
    for word in words:
        folded = folder.analyze(word)
        candidate = folded[0] if folded else ""
        if candidate and candidate != word and candidate not in have and candidate not in extra:
            extra.append(candidate)
    return extra
```

Ergebnis, gezählt am 23.09.2026 gegen Tag 0.26.2: 77 (es), 10 (it), 0 (nl), 30 (pt), zusammen 117.

### Die Positivliste lesen

```python
# Source: Muster von config._ocr_languages(), backend/src/findling/config.py:1043
def _languages() -> tuple[str, ...]:
    """Return the active language fields, in schema order.

    Unlike the OCR reader this one does NOT keep the order the admin wrote.
    The schema field order is ours to decide, and once the language set is a
    version mark, "es,de" and "de,es" have to produce the same mark or a
    resorted environment variable would start a rebuild.
    """
    requested = {part.strip().lower() for part in os.environ.get("FINDLING_LANGUAGES", "").split(",")}
    unknown = requested - set(SUPPORTED_LANGUAGES) - {""}
    if unknown:
        LOGGER.warning("FINDLING_LANGUAGES names a language this build does not support, ignoring that entry")
    kept = tuple(language for language in SUPPORTED_LANGUAGES if language in requested)
    if kept:
        return kept
    if requested - {""}:
        LOGGER.warning("FINDLING_LANGUAGES names no supported language, falling back to the built in default")
    return DEFAULT_LANGUAGES
```

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `tantivy` | **0.26.2** (2026-09-17) | Suchmaschine, Analyseketten, Stemmer, Stoppwörter | schon im Einsatz; der Sprung ist ein Patch, `index_format v7` unverändert, Tokenisierung gemessen identisch |

### Supporting

Keine. Es wird **kein** neues PyPI- oder Systempaket installiert. Snowball-Stemmer und -Stoppwortlisten für es/it/nl/pt sind in tantivy einkompiliert (BSD-3-Clause, AGPL-verträglich).

### Alternatives Considered

| Statt | Könnte man | Abwägung |
|---|---|---|
| tantivy 0.26.2 | bei 0.26.0 bleiben | Die Panic-Klasse (5 Sprachen) ist von der Positivliste ohnehin unerreichbar. Der eigentliche Gewinn von 0.26.2 ist `Index.is_compatible` für Phase 18 und die saubere Ausnahme als zweite Verteidigungslinie. Kostet dafür den Marken-Entscheid E-17-7. |
| eingebaute Stoppwortlisten | eigene, gepflegte Listen | mehr Kontrolle, dafür 891 Wörter Pflegeaufwand und eine Lizenzfrage, wo heute keine ist |
| `fold früh` | `fold spät` je Sprache unterschiedlich | 4 von 573 Paaren Gewinn bei Spanisch gegen zwei Kettenformen im selben Modul |

**Installation:**

```bash
cd backend && uv lock --upgrade-package tantivy && uv sync
```

**Version verification:** `tantivy` 0.26.2 ist die aktuellste Fassung auf PyPI (gelesen 2026-09-23 über die PyPI-JSON-API, hochgeladen 2026-09-17). Eine Fassung 0.26.1 existiert nicht. Räder für `cp313` manylinux_2_17 aarch64 und x86_64 sind vorhanden; die `cp313t`-Räder (free-threaded) sind gegenüber 0.26.0 entfallen und werden von diesem Projekt nicht genutzt.

---

## Package Legitimacy Audit

Diese Phase installiert **kein neues Paket**. Geprüft wird allein die Bewegung eines bestehenden Pins.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---|---|---|---|---|---|---|
| `tantivy` | PyPI | Projekt seit 2020, Fassung 0.26.2 vom 2026-09-17 | schon im Produkt, keine neue Abhängigkeit | github.com/quickwit-oss/tantivy-py | nicht gelaufen (Werkzeug nicht installiert) | **Approved**, weil Bestandsabhängigkeit mit Hash-Pin in `uv.lock`, Herkunft über die offiziellen GitHub-Releases verifiziert |

**Packages removed due to slopcheck [SLOP] verdict:** keine
**Packages flagged as suspicious [SUS]:** keine

`slopcheck` wurde in dieser Sitzung nicht installiert. Das ist hier ohne Folgen, weil keine neue Paketkennung ins Spiel kommt: die Identität `tantivy` ist seit v1.0 im Produkt, der Hash steht in `uv.lock`, und der Sprung wird über `uv lock --upgrade-package` gefahren, nicht über einen frei getippten Namen. Sollte ein Plan dieser Phase wider Erwarten ein neues Paket vorschlagen, gehört ein `checkpoint:human-verify` davor.

---

## Architecture Patterns

### Systemzeichnung der Kette

```
Text aus dem Extraktor / Suchzeile des Nutzers
        |
        v
  normalize(NFC)                     <- findling.index.analyzer.normalize, beide Seiten
        |
        v
  Tokenizer.simple()                 <- teilt an allem, was nicht alphanumerisch ist
        |
        v
  Filter.lowercase()                 <- ab hier vergleicht alles exakt
        |
        +--- de: split_compound -> custom_stopword(FUGEN) -> stopword(german) -> remove_long -> stemmer(german)
        |        (faltet NICHT, der deutsche Stemmer faltet selbst und die Zerlegungsliste traegt Umlaute)
        |
        +--- en/es/it/nl/pt: ascii_fold -> stopword(lang) -> custom_stopword(gefaltet) -> remove_long -> stemmer(lang)
        |        (eine Fabrik, Ergaenzungsliste leer fuer en und nl)
        |
        +--- name: ascii_fold -> remove_long(60)        (kein Stoppwort, kein Stemmer)
        |
        +--- path: remove_long(0)                       (gespeichert, nie durchsucht)
        |
        v
  Terme, identisch auf Index- und Frageseite
        |
        v
  tantivy-Index (Feld je Sprache, Schema persistiert den Tokenizer-NAMEN)
```

### Vorgeschlagene Dateien dieser Phase

```
backend/src/findling/index/analyzer.py     # + snowball_analyzer(), + FOLDED_STOPWORDS, ANALYZER_VERSION bleibt 1
backend/src/findling/config.py             # + LANGUAGE_ALLOWLIST, + SUPPORTED_LANGUAGES, + SNOWBALL_NAME
backend/tests/test_language_analyzers.py   # Formfamilien-Tabelle je Sprache, Stoppwort-Dichtheit, Positivlisten-Paritaet
backend/tests/fixtures/chain_cases_es.txt  # je Sprache eine Fixture, eine Formfamilie je Zeile
scripts/dev/chain_probe.py                 # die Sonde aus Abschnitt 3.2
scripts/dev/measure_chains.sh              # Treiber, ohne Container
docs/language-analyzers.md                 # Produktdoku im Muster von german-analyzer.md
docs/measurements/2026-09-analyseketten/   # Messbericht plus Rohdaten
.planning/phases/17-.../17-GRUNDSATZ-ENTSCHEID.md
```

### Anti-Patterns

* **Zwei Kettenformen im selben Modul** (früh faltend für drei Sprachen, spät faltend für eine). Der Gewinn ist gemessen 4 von 573 Paaren.
* **Eine zweite Kette für die Frageseite.** Die Symmetrie kommt allein daher, dass beide Seiten dasselbe registrierte Tokenizer-Objekt benutzen.
* **Die deutsche Kette "der Einheitlichkeit halber" mit `ascii_fold` nachrüsten.** Der Modulkopf begründet ausführlich, warum sie keines hat; es würde die Zerlegungsliste entwerten und den Splitter still scheitern lassen.
* **Die Ergänzungsliste als Python-Literal abtippen.**

---

## State of the Art

| Alt | Neu | Wann | Bedeutung |
|---|---|---|---|
| `Filter.stopword("romanian")` bringt den Prozess per Rust-Panic zu Fall | sauberer `ValueError: No builtin stop word list for language: ...` | tantivy-py 0.26.2, PR #734, 2026-09-17 | betrifft genau 5 Sprachen (arabic, greek, romanian, tamil, turkish) |
| keine Formatprüfung von aussen | `Index.is_compatible(path)` | 0.26.2, PR #682 | prüft das **Indexformat**, nicht das Schema |
| Boolesche Anfragen nur über `boolean_query` | `and_must_match`, `and_must_not_match`, `or_should_match` | 0.26.2, PR #531 | Bequemlichkeit, für v1.3 nicht nötig |
| `cp313t`-Räder | entfallen | 0.26.2 | ohne Folgen, das Projekt fährt `cp313` |

**Überholt oder zu streichen:**

* "Union-Scorer-Bugfix in 0.26.2" aus SUMMARY.md und STACK.md: in den Release Notes nicht auffindbar, kein Bump des Rust-Kerns im Sprung. Aus der Owner-Vorlage streichen.
* "Niederländische Betonungsakzente als eigene `custom_stopword`-Liste" (FEATURES, REQUIREMENTS "Future"): unter `fold früh` gegenstandslos.
* "GERMAN: 7 zusätzliche gefaltete Formen" (STACK): gemessen sind es 8. Folgenlos, weil die deutsche Kette nicht faltet.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---|---|---|
| Python 3.13 in `backend/.venv` | Messung und Suite | ja | 3.13.13 | - |
| `tantivy` in der Repo-venv | Gegenprobe 0.26.0 | ja | 0.26.0, `index_format v7` | - |
| `uv` | Wegwerf-venv, `uv lock`, `uv run` | ja | 0.11.7 | - |
| Netz zu PyPI und GitHub raw | `stopwords.rs`, Räderliste, Release Notes | ja | - | `stopwords.rs` einmal ins Repo legen |
| Docker | **nicht nötig** | - | - | Anders als beim deutschen Splitter braucht diese Messung keine Debian-Wortliste; alle Listen sind in tantivy einkompiliert. |
| `slopcheck` | Paketprüfung | nein | - | kein neues Paket, siehe Audit |

**Fehlende Abhängigkeiten ohne Ausweg:** keine.

---

## Security Domain

Die Phase ändert eine Eingabevalidierung, also ist der Abschnitt nicht leer, aber schmal.

| ASVS-Kategorie | Betroffen | Kontrolle |
|---|---|---|
| V2 Authentication | nein | - |
| V3 Session Management | nein | - |
| V4 Access Control | nein | - |
| V5 Input Validation | **ja** | Geschlossene Positivliste für `FINDLING_LANGUAGES`, Muster `OCR_LANGUAGE_ALLOWLIST` (T-03-502). Der Wert wandert nicht in eine Kommandozeile, sondern in einen FFI-Aufruf; ein nicht abgedeckter Name ist in 0.26.0 ein Prozessabbruch (Verfügbarkeit) und in 0.26.2 eine Ausnahme im Startpfad. |
| V6 Cryptography | nein | - |

| Muster | STRIDE | Standardabwehr |
|---|---|---|
| Sprachname aus der Umgebung erreicht `Filter.stopword` und beendet den Container | Denial of Service | geschlossene Positivliste plus Upgrade auf 0.26.2 als zweite Linie |
| Messsonde druckt Nutzertext | Information Disclosure | dieselbe Regel wie T-02-14: die Sonde liest nur Fixtures und veröffentlichte Snowball-Listen, nie `state.db`, nie einen Index, nie eine Nutzerdatei |
| Stiller Recall-Verlust durch eine unbemerkt driftende Ergänzungsliste | Tampering (unabsichtlich) | Hash-Test über die erzeugte Liste, wie `wordlist_hash` |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | Die Testwörter der Formfamilien sind gebräuchliche und korrekt geschriebene Wörter der vier Sprachen (kein Muttersprachler hat sie geprüft) | 2.3, 3.3 | Eine falsche Form verschiebt eine Prozentzahl. Die Reihenfolge-Aussage hängt nicht an einzelnen Wörtern, weil dieselben Familien in beiden Ketten gefahren werden. |
| A2 | Nutzer tippen Akzente häufig nicht, und OCR verliert sie gelegentlich | 2.4, Begründung 3 | Wenn beides selten ist, kippt die Empfehlung Richtung `fold spät` für Spanisch. Messbar in Phase 22 an echten Anfragen, heute nicht belegt. |
| A3 | Die geschätzte Umbauzeit 1 bis 3 h gegen 19 h 20 min | 6.2, E-17-1 | aus ARCHITECTURE übernommen, MESS-08 misst nach |
| A4 | `uv lock --upgrade-package tantivy` bewegt nur diese eine Zeile | 4.4 | Falls der Resolver mehr bewegt, ist der Diff der Beleg; vor dem Commit lesen |
| A5 | Der Owner will die Vergleichsregel für `tantivy_version` lockern (E-17-7) | 4.2, 7 | Bei Nein muss LEX-07 umformuliert oder der Pin nach Phase 18 verschoben werden |
| A6 | Ein leeres `Filter.custom_stopword([])` bleibt auch in künftigen tantivy-Fassungen ein No-op | 2.4, Code Examples | heute gemessen; ein Test hält es fest |

---

## Open Questions (RESOLVED, siehe Plaene 17-01/17-04/17-05: Q1 -> Owner-Tor E-17-7, Q2 -> nicht bauen, Q3 -> Leitplanke in 17-01, Q4 -> ungerichtete Metrik in 17-05)

1. **Fällt E-17-7 auf "lockern" oder auf "Pin stehen lassen"?**
   Bekannt: beide Wege sind gangbar und beide sind belegt. Unklar: die Risikoneigung des Owners gegenüber einer gelockerten Marke. Empfehlung: als erste Frage der Vorlage stellen, weil alle Pläne mit tantivy-Bezug daran hängen.

2. **Soll `già`, `però`, `così` (it) und `aún`, `sólo` (es) eine eigene Stoppwortergänzung bekommen?**
   Bekannt: sie stehen nicht in den Snowball-Listen und erzeugen deshalb Terme. Unklar: ob das stört. Empfehlung: **nicht** tun. Es ist eine inhaltliche Wortlistenpflege ohne Ende, und ein zusätzlicher Term schadet weniger als eine gelöschte Bedeutung.

3. **Wie eng ist "kein Code, der D-04 berührt"?**
   Vorschlag in 6.3; gehört im Entscheiddokument als Definition festgeschrieben, damit der Satz nicht in jeder Planprüfung neu ausgelegt wird.

4. **Trägt die Formfamilien-Metrik oder braucht es eine gerichtete Variante?**
   Die ungerichtete Metrik wichtet jede Schreibweise gleich. Eine gerichtete Variante (Dokumente korrekt akzentuiert, Anfragen gemischt) wurde von Hand für zwei Familien nachgerechnet und ergab für es einen Vorteil von `fold spät`, für pt ein Unentschieden. Empfehlung: die ungerichtete Metrik als Abnahme fahren und die gerichtete im Messbericht als Nebenrechnung nennen, damit ein späterer Leser die Abwägung nachvollziehen kann.

---

## Sources

### Primär (HIGH)

* Eigene Messung, 2026-09-23, `tantivy==0.26.2` in einer Wegwerf-venv und `tantivy==0.26.0` in `backend/.venv`: sieben Kandidatenketten, 65 Formfamilien, 573 geordnete Paare, 891 Stoppwörter in zwei Schreibweisen, 224 Zeilen Tokenisierungsvergleich, Index-Kreuzlesetest in beide Richtungen, Panic-Klasse.
* `quickwit-oss/tantivy`, Tag 0.26.2, `src/tokenizer/stop_word_filter/stopwords.rs` (roh geladen, geparst, gezählt).
* `quickwit-oss/tantivy-py`, Releases 0.26.0 und 0.26.2 über die GitHub-API (PR #734, #682, #531, #666; Veröffentlichung 0.26.2 am 2026-09-17; kein 0.26.1).
* PyPI-JSON-API für `tantivy`: Fassungsliste und vollständige Rädermatrix.
* Eigener Quelltext: `backend/src/findling/index/analyzer.py`, `index/open.py`, `store/repo.py`, `config.py`, `backend/tests/test_upgrade_compatibility.py`, `test_index_open.py`, `test_ocr_languages.py`, `test_allowlist_parity.py`, `.github/workflows/deploy-harp.yml`, `backend/pyproject.toml`, `backend/uv.lock`, `docs/testing.md`, `docs/german-analyzer.md`, `scripts/dev/compound_probe.py`, `scripts/dev/measure_compounds.sh`.
* `.planning/milestones/v1.2-phases/12-.../12-STABLE35-ENTSCHEID.md` und `12-02-PLAN.md` (Muster des Owner-Tors).

### Sekundär (MEDIUM)

* `.planning/research/STACK.md`, `FEATURES.md`, `PITFALLS.md`, `ARCHITECTURE.md`, `SUMMARY.md` , jede zitierte Behauptung dieser Dokumente wurde oben nachgemessen und ist als bestätigt, korrigiert oder widerlegt gekennzeichnet.
* `.planning/milestones/v1.1-phases/11-.../11-RESEARCH.md` (Zeile 1029: "tantivy unveraendert lassen, ein Bump waere ein Reindex fuer jeden Bestandsnutzer") und `.planning/milestones/v1.2-phases/16-.../16-RESEARCH.md` (Zeile 404: roter Lauf 35556667085 wegen genau dieses Sprungs).

### Tertiär (LOW)

* Eine über WebFetch zusammengefasste Fassung der Release Notes nannte falsche Jahreszahlen; die Daten in dieser Recherche stammen deshalb ausschliesslich aus der GitHub-API und der PyPI-API, nicht aus dieser Zusammenfassung.

---

## Metadata

**Confidence breakdown:**

* Kettenreihenfolge und Zahlen: **HIGH**, selbst gemessen, Skript abgedruckt, Gegenprobe gegen beide tantivy-Fassungen.
* Empfehlung `fold früh` einheitlich: **MEDIUM**, weil der Messabstand klein ist und die Begründung zu einem Teil auf einer Nutzungsannahme beruht (A2).
* tantivy-Marken-Befund: **HIGH**, am Quelltext und an der CI-Datei gelesen, in zwei früheren Recherchen unabhängig belegt.
* Panic-Klasse und Positivliste: **HIGH**, gemessen.
* "Union-Scorer-Fix": **widerlegt** (nicht in den Release Notes, kein Kern-Bump).
* Owner-Tor-Form: **HIGH**, direktes Muster im Repo.

**Research date:** 2026-09-23
**Valid until:** 2026-10-23 für die tantivy-Aussagen (Patch-Kadenz beobachten), unbefristet für die Messzahlen, solange der Pin steht , sie hängen an der Fassung, nicht am Datum.
