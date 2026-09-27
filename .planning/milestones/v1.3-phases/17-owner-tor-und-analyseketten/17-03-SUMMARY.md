---
phase: 17-owner-tor-und-analyseketten
plan: 03
subsystem: index
tags: [tantivy, snowball, ascii-fold, stopwords, analyzer, ast-guard, sha256]

# Dependency graph
requires:
  - phase: 02-index-und-analysekette
    provides: german_analyzer, english_analyzer, name_analyzer, ANALYZER_VERSION, wordlist_hash als Muster
  - phase: 08-komposita-rezept-a
    provides: scripts/dev/compound_probe.py als Sondenmuster, AST-Kettenwaechter in test_analyzer.py
provides:
  - snowball_analyzer(language, folded_stopwords) als eine Kettenfabrik fuer en, es, it, nl, pt
  - FOLDED_STOPWORDS mit 117 gefalteten Snowball-Stoppwoertern plus folded_stopwords_hash
  - scripts/dev/stopword_supplement.py als Erzeuger der Ergaenzungsliste aus dem gepinnten tantivy-Tag
  - AST-Kettenwaechter EXPECTED_SNOWBALL_CHAIN plus No-op-Beweis fuer Filter.custom_stopword([])
affects: [17-04, 17-05, 17-06, 18-schema-und-registrierung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Kettenfabrik je Algorithmusfamilie statt einer Funktion je Sprache"
    - "Abgeleitete Konstanten werden maschinell erzeugt und per Testkonstante gehasht, nie per Versionsmarke"
    - "Der AST-Kettenwaechter wird importiert statt kopiert, damit es nur ein Gate gibt"

key-files:
  created:
    - backend/src/findling/index/stopwords.py
    - scripts/dev/stopword_supplement.py
    - backend/tests/test_language_analyzers.py
  modified:
    - backend/src/findling/index/analyzer.py
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Der Hash der Ergaenzungsliste bleibt Testkonstante FOLDED_SUPPLEMENT_SHA256 und wird keine sechste Versionsmarke, weil eine fehlende Marke auf jeder Bestandsinstallation als Abweichung gelesen wuerde"
  - "ANALYZER_VERSION bleibt 1, weil die vier neuen Ketten nirgends registriert sind und die englische Kette tokenidentisch bleibt"
  - "Kein Singleton-Cache fuer die Snowball-Ketten: sie sind einkompiliert, im Gegensatz zum deutschen Automaton mit 0,44 s und 23 MB"
  - "Die Faltung nutzt tantivys eigenen Filter, nie einen Nachbau ueber unicodedata"
  - "Das Werkzeug liest zusaetzlich mod.rs, weil die englische Liste dort inline steht und nicht als const in stopwords.rs"

patterns-established:
  - "Dev-Sonde: handgeschriebener Argumentparser, main(argv) -> int, stdout nur name=wert mit Zahlen und Digests, Sicherheitsregel T-02-14 im Modulkopf"
  - "Erwartungswerte als Kopfkommentar der Sonde, mit dem Satz, dass eine Abweichung ein Befund und kein Grund zum Handeditieren ist"
  - "Baumhash-Ratsche: bei wachsender Dateizahl wird die Zahl des Laufs von der Zahl des Baums getrennt (PACKAGE_FILES gegen PACKAGE_FILES_TODAY), Vorbild ist das PHP-Paar"

requirements-completed: [LEX-01]

# Metrics
duration: 62min
completed: 2026-09-23
---

# Phase 17 Plan 03: Kettenfabrik und gefaltete Ergaenzungsliste Summary

**Eine Fabrik `snowball_analyzer()` baut die gemessene Kette lowercase, ascii_fold, stopword, custom_stopword, remove_long, stemmer fuer en, es, it, nl und pt; die 117 gefalteten Stoppwoerter sind maschinell aus tantivy-Tag 0.26.2 erzeugt und per SHA-256 in einem Test gehalten, nicht in einer Versionsmarke.**

## Performance

- **Duration:** 62 min
- **Started:** 2026-09-23
- **Completed:** 2026-09-23
- **Tasks:** 3
- **Files modified:** 5 (3 neu, 2 geaendert)

## Accomplishments

- `scripts/dev/stopword_supplement.py` leitet die Ergaenzungsliste aus den Snowball-Listen des gepinnten Tags ab und faltet dabei mit tantivys eigenem Filter. Gemessen und mit den Erwartungswerten der Recherche deckungsgleich: spanish 308 eingebaut / 77 Ergaenzung, italian 279 / 10, dutch 101 / 0, portuguese 203 / 30, english 33 / 0, zusammen 117.
- `backend/src/findling/index/stopwords.py` liefert `FOLDED_STOPWORDS` und `folded_stopwords_hash`. Alle 117 Eintraege sind ASCII, je Sprache duplikatfrei, Digest `d056d4597f989c7e03113c529c92cef980254f72c4d4e5deace4588ea033311a`.
- `snowball_analyzer()` steht in `analyzer.py` zwischen `english_analyzer()` und `name_analyzer()`; `english_analyzer()` delegiert an sie und behaelt Signatur und Namen. `index/open.py` ist unveraendert, `ANALYZER_VERSION` steht weiter auf 1.
- `backend/tests/test_language_analyzers.py` haelt zwoelf Faelle: Verhalten der vier Sprachen, Unbewegtheit der englischen Kette, der AST-Kettenwaechter mit drei Selbsttests, der No-op-Beweis ueber 13 Woerter und die Integritaet der Ergaenzungsliste in beide Richtungen.
- Volle Suite gruen: 2503 bestanden, 15 uebersprungen. ruff, ruff format, pyright und vulture gruen; das Dev-Skript ruff-gruen mit `--config backend/pyproject.toml`.

## Task Commits

1. **Task 1: Erzeugungswerkzeug und ausgelieferte Ergaenzungsliste** , `d1f2a68` (feat)
2. **Task 2 RED: Verhaltenstests der Kettenfabrik** , `5ddd02c` (test)
3. **Task 2 GREEN: snowball_analyzer plus Ueberfuehrung von english_analyzer** , `c4dea37` (feat)
4. **Task 3: Kettenwaechter, No-op-Beweis, Integritaet der Ergaenzungsliste** , `965d84b` (test)

Kein REFACTOR-Commit: nach GREEN gab es nichts aufzuraeumen, die Fabrik ersetzte den handgeschriebenen Rumpf von `english_analyzer()` direkt.

## Files Created/Modified

- `scripts/dev/stopword_supplement.py` , erzeugt die Ergaenzungsliste aus `stopwords.rs` und `mod.rs` des gepinnten Tags, schreibt den fertigen Literalblock und druckt nur Zahlen und Digests
- `backend/src/findling/index/stopwords.py` , `FOLDED_STOPWORDS` (117 Eintraege) und `folded_stopwords_hash`, mit der Marken-Falle als Warnabsatz im Modulkopf
- `backend/src/findling/index/analyzer.py` , zweite Kettentabelle im Modulkopf, der Satz ueber die nicht registrierte Kette, `snowball_analyzer()`, `english_analyzer()` als Einzeiler
- `backend/tests/test_language_analyzers.py` , zwoelf Faelle, `EXPECTED_SNOWBALL_CHAIN`, `FOLDED_SUPPLEMENT_SHA256`, `EXPECTED_SUPPLEMENT_SIZES`
- `backend/tests/test_measurement_scripts.py` , Baumhash-Ratsche des Python-Pakets von 54 auf 55 Dateien nachgezogen (siehe Abweichung 1)

## Decisions Made

- **Der Supplement-Hash bleibt Testkonstante.** In `expected_versions()` waere er eine sechste Marke, die auf keiner Bestandsinstallation existiert; `Store.version_mismatch` liest eine fehlende Marke als Abweichung, und das Ergebnis waere ein voller Reindex (gemessen 19 h 20 min) fuer eine Konstante, die keine geschriebene Tokenisierung beruehrt. `grep` in `index/open.py` findet weder `FOLDED_STOPWORDS` noch `folded_stopwords_hash`.
- **`ANALYZER_VERSION` bleibt 1.** Der Modulkopf sagt jetzt ausdruecklich, warum: eine hinzugefuegte, nirgends registrierte Kette aendert keine Tokenisierung. Ohne diesen Satz hebt der naechste Leser die Marke aus Vorsicht und reisst Erfolgskriterium 4 der Phase.
- **Kein Cache fuer die Snowball-Ketten.** Das deutsche Muster (`_CACHED_GERMAN`, `build_count`) existiert wegen 276496 Woertern, 0,44 s und 23 MB. Die vier Snowball-Ketten sind einkompiliert; ein Cache waere Ballast, den vulture zu Recht anmeckern wuerde. Begruendung steht im Docstring.
- **Die Faltung laeuft ueber tantivys Filter.** Ein Nachbau ueber `unicodedata` faellt anders aus (tantivy faltet auch das scharfe s zu `ss`), und eine Ergaenzungsliste, die nicht zur Kette passt, ist schlimmer als keine: sie sieht richtig aus und leckt trotzdem.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Baumhash-Ratsche des Python-Pakets nachgezogen**
- **Found during:** Task 3 (volle Suite)
- **Issue:** `tests/test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_python_package` schlug mit `assert 55 == 54` fehl. Die Ratsche zaehlt die Dateien unter `backend/src/findling`; `index/stopwords.py` ist die 55. Datei. Der Test ist ein Gate ueber genau die Aenderung, die dieser Plan macht, und die volle Suite ist Abnahmebedingung des Plans.
- **Fix:** Nach dem Vorbild des PHP-Paares (`PHP_FILES` gegen `PHP_FILES_TODAY`) wurde `PACKAGE_FILES_TODAY = 55` mit neuem `PACKAGE_TREE_HASH_TODAY` eingefuehrt und die Behauptung darauf umgestellt; `PACKAGE_FILES = 54` bleibt die Zahl des Laufs vom 09.09.2026 und wird jetzt zusaetzlich gegen `dateien: 54` in `rohdaten/40b-baumhash.txt` gehalten, genau wie die PHP-Haelfte es tut. Ein Kommentarabsatz nennt Datum, Plan, die neu hinzugekommene Datei und die geaenderte.
- **Files modified:** `backend/tests/test_measurement_scripts.py`
- **Verification:** `uv run python -m pytest tests/test_measurement_scripts.py -q` , 376 bestanden; volle Suite 2503 bestanden
- **Committed in:** `965d84b` (Task-3-Commit)

### Abweichungen vom Planwortlaut, ohne Regelbezug

**2. `parse_stopwords` nimmt den Quelltext statt eines Pfades**
- Der Plan zitiert die Signatur `parse_stopwords(path) -> dict[str, list[str]]` aus RESEARCH 3.2. Umgesetzt ist `parse_stopwords(text: str)`, weil derselbe Parser den heruntergeladenen und den per `--source` benannten Stand bedient. Ein Werkzeug, das einen Download nur auf die Platte schreibt, um ihn zurueckzulesen, hat einen Cache erfunden. Der Docstring sagt das.

**3. Das Werkzeug liest zwei Dateien statt einer**
- `stopwords.rs` des Tags 0.26.2 traegt zwoelf `pub const`-Listen, aber keine englische: die englische Liste steht inline im match-Zweig von `mod.rs` (aus Lucene uebernommen, 33 Eintraege, reines ASCII). Ohne den zweiten Leser waere `english_supplement=0` eine Behauptung statt einer Messung. `--source` erwartet deshalb `mod.rs` neben der benannten `stopwords.rs`.

**4. Zusatzbefund im Parser, Rot-Beweis gefahren**
- Der Parserentwurf aus RESEARCH 3.2 sucht nach `&[` ab dem Doppelpunkt und faengt damit den Typ `&[&str]` statt des Werts. Der erste Lauf meldete `spanish_builtin=1`. Die Klammertiefe wird jetzt gezaehlt und ab dem Zuweisungszeichen gesucht; der Kommentar an der Stelle nennt den Grund. Danach traf jeder der fuenf Erwartungswerte.

**5. Die RED-Phase von Task 2 legte die Datei aus Task 3 an**
- `backend/tests/test_language_analyzers.py` ist Artefakt von Task 3, aber Task 2 ist `tdd="true"` und braucht ein rotes Gate. Die fuenf Verhaltenstests entstanden deshalb im RED-Commit `5ddd02c` (rot: `ImportError: cannot import name 'snowball_analyzer'`), die sieben Gates aus Task 3 kamen in `965d84b` dazu. Es entstand keine zusaetzliche Datei ausserhalb der vier Pfade des Plans.

---

**Total deviations:** 1 auto-fixed (Rule 3, blockierend) plus 4 Wortlautabweichungen mit Begruendung
**Impact on plan:** Kein Scope-Zuwachs. Die Ratsche war ein Gate ueber genau diese Aenderung und musste mitgezogen werden, sonst waere die Suite rot geblieben.

## Issues Encountered

- **Der Parserentwurf der Recherche fing den Rust-Typ statt des Werts.** Sichtbar geworden, weil die Erwartungswerte als Kopfkommentar im Werkzeug stehen: `spanish_builtin=1` gegen erwartete 308 ist ein Befund und keine Zahl, ueber die man hinwegliest. Behoben durch Klammertiefenzaehlung.
- **Die englische Snowball-Liste fehlt in `stopwords.rs`.** Gefunden beim Vergleich der zwoelf gefundenen Namen mit den 13 Listen aus RESEARCH 5.1. Behoben durch den zweiten Leser ueber `mod.rs`.

## Verification

- `uv run python -m pytest -q` aus `backend/`: 2503 bestanden, 15 uebersprungen, 0 fehlgeschlagen
- `uv run python -m pytest tests/test_language_analyzers.py -q`: 12 bestanden
- `uv run ruff check`, `uv run ruff format --check`, `uv run pyright` (0 errors), `uv run vulture`: gruen
- `uv run ruff check --config pyproject.toml ../scripts/dev/stopword_supplement.py` und `ruff format --check`: gruen
- `git diff --quiet backend/src/findling/index/open.py` und `git diff --quiet backend/pyproject.toml`: beide unveraendert
- `grep -n "ANALYZER_VERSION = " backend/src/findling/index/analyzer.py`: `= 1`
- `grep -c "folded_stopwords_hash\|FOLDED_STOPWORDS" backend/src/findling/index/open.py`: 0
- `grep -c "def filter_chain" backend/tests/test_language_analyzers.py`: 0
- Werkzeug zweimal gefahren, ueber Netz und ueber `--source`: byteidentische Ausgabe, gleicher Digest

## Known Stubs

Keine. Alles, was dieser Plan anlegt, ist vollstaendig verdrahtet und getestet. Was der Plan bewusst NICHT tut und was deshalb kein Stub, sondern Zusage einer spaeteren Nummer ist:

- Kein Tokenizer fuer es, it, nl oder pt ist in `index/open.py` registriert, und es gibt keine `TOKENIZER_ES`-artige Konstante. Das ist Zusage von Phase 18, zusammen mit dem Schema.
- Die vollstaendige Dichtheitsmessung ueber alle 891 eingebauten Stoppwoerter braucht `stopwords.rs` und ist Zusage der Plaene 17-05 und 17-06. Was hier steht, ist die Notwendigkeit jedes Ergaenzungseintrags, also die Gegenrichtung.
- `docs/language-analyzers.md` existiert noch nicht; `snowball_analyzer` verweist darauf als Ort des dokumentierten Preises (Numerusklasse bei akzenttragendem Snowball-Suffix). Anlage ist Zusage eines spaeteren Plans der Phase.

## Threat Flags

Keine neue sicherheitsrelevante Oberflaeche. Alle vier `mitigate`-Zusagen des Bedrohungsregisters sind umgesetzt: T-17-09 (Erzeugungswerkzeug plus `FOLDED_SUPPLEMENT_SHA256` plus Notwendigkeitstest je Eintrag), T-17-10 (`ANALYZER_VERSION` unbewegt, keine Registrierung, Hash keine Marke, Modulkopfsatz gegen das vorsorgliche Heben), T-17-11 (No-op-Beweis ueber 13 Woerter plus Vergleich gegen die handgebaute Kette), T-17-12 (Sicherheitsregel T-02-14 im Modulkopf, stdout nur Zahlen und Digests), T-17-13 (Waechter liest den Syntaxbaum, Selbsttest mit Filternamen in Kommentar und Docstring). T-17-SC: kein Paket installiert, kein Abhaengigkeitsmanifest beruehrt, `backend/pyproject.toml` unveraendert.

## Next Phase Readiness

- Die Fabrik steht und ist von aussen benutzbar; Plan 17-04 kann die Positivliste und die Sprachkonfiguration darauf setzen, ohne die Kette noch einmal anzufassen.
- Die Plaene 17-05 und 17-06 finden in `scripts/dev/stopword_supplement.py` einen Parser fuer `stopwords.rs`, den die Dichtheitsmessung wiederverwenden kann statt ihn nachzubauen.
- Offen fuer die Phase, nicht fuer diesen Plan: `docs/language-analyzers.md`, die Fixtures je Sprache, der Messbericht und die Registrierung in Phase 18.

---
*Phase: 17-owner-tor-und-analyseketten*
*Completed: 2026-09-23*

## Self-Check: PASSED

Alle sechs genannten Dateien existieren, alle vier Commit-Hashes stehen im Log dieses Worktrees.
