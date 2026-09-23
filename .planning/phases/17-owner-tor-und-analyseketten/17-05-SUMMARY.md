---
phase: 17-owner-tor-und-analyseketten
plan: 05
subsystem: testing
tags: [tantivy, snowball, ascii-fold, stopwords, messsonde, fixtures, messbericht]

# Dependency graph
requires:
  - phase: 17-owner-tor-und-analyseketten
    provides: snowball_analyzer, FOLDED_STOPWORDS, folded_stopwords_hash aus Plan 17-03
  - phase: 08-komposita-rezept-a
    provides: scripts/dev/compound_probe.py und measure_compounds.sh als Form- und Treibervorlage
provides:
  - scripts/dev/chain_probe.py mit read_families, chain, family_score, stopword_leaks, verify_against_product
  - scripts/dev/measure_chains.sh, der Treiber ohne Container
  - vier Formfamilien-Fixtures chain_cases_es/it/nl/pt.txt, 65 Familien, 573 geordnete Paare
  - vier Verlustlisten chain_known_losses_es/it/nl/pt.txt aus dem Messlauf
  - backend/tests/fixtures/snowball_stopwords_0_26_2.txt, die geparste eingebaute Liste
  - docs/measurements/2026-09-analyseketten mit Messbericht und Rohdaten
affects: [17-06, 17-07, 18-schema-und-registrierung, 23-haertung-und-doku]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Messsonde darf eigene Kandidaten bauen, wenn sie die Siegervariante Token fuer Token gegen das Produkt gegenprueft"
    - "Der Fixture-Leser lebt neben der Sonde und wird vom Test importiert, nicht nachgebaut"
    - "Eine Messung ohne Container, wenn die Datenquelle in der Bibliothek einkompiliert ist"
    - "Bekannte Verluste als eigene Fixture, als Behauptung in beide Richtungen"

key-files:
  created:
    - scripts/dev/chain_probe.py
    - scripts/dev/measure_chains.sh
    - backend/tests/fixtures/chain_cases_es.txt
    - backend/tests/fixtures/chain_cases_it.txt
    - backend/tests/fixtures/chain_cases_nl.txt
    - backend/tests/fixtures/chain_cases_pt.txt
    - backend/tests/fixtures/chain_known_losses_es.txt
    - backend/tests/fixtures/chain_known_losses_it.txt
    - backend/tests/fixtures/chain_known_losses_nl.txt
    - backend/tests/fixtures/chain_known_losses_pt.txt
    - backend/tests/fixtures/snowball_stopwords_0_26_2.txt
    - docs/measurements/2026-09-analyseketten/README.md
    - docs/measurements/2026-09-analyseketten/rohdaten/familien.tsv
    - docs/measurements/2026-09-analyseketten/rohdaten/kennzahlen.txt
    - docs/measurements/2026-09-analyseketten/rohdaten/verluste.tsv
  modified: []

key-decisions:
  - "Die Sonde baut die sieben Kandidatenketten selbst, weil sechs davon im Produkt nicht existieren, und schliesst diese Ausnahme mit verify_against_product gegen snowball_analyzer"
  - "Der Fixture-Leser read_families steht in der Sonde und nicht im Paket, weil scripts/ kein Paket ist und der Import nur in dieser Richtung laufen kann"
  - "chain_probe liest die eingebaute Stoppwortliste in zwei Formen (stopwords.rs und TSV-Fixture) mit einem zweiten kleinen Rust-Leser statt per Import aus stopword_supplement.py"
  - "Die Ergaenzungsliste der Messung ist FOLDED_STOPWORDS aus dem Paket, nicht eine in der Sonde neu abgeleitete, damit Kandidat und Produkt dieselbe Liste sehen"
  - "Der Messlauf faehrt gegen tantivy 0.26.0 aus backend/uv.lock, nicht gegen 0.26.2 wie die Recherche; die Zahlen sind identisch und der Pin haengt am Owner-Tor"

patterns-established:
  - "Messung misst das Produkt: eine selbst gebaute Siegerkette ist nur zulaessig mit Token-fuer-Token-Gegenprobe, Rueckgabecode 1 bei Differenz"
  - "Treiber ohne Container, wenn die Quelle einkompiliert ist, mit der Begruendung im Kopfkommentar"
  - "Erwartungswerte im Kopfkommentar des Treibers plus der Satz, dass eine Abweichung ein Befund ist"

requirements-completed: [LEX-01]

# Metrics
duration: 30min
completed: 2026-09-23
---

# Phase 17 Plan 05: Messwerkzeug und Messbericht der Analyseketten Summary

**Die Kettenmessung liegt als wiederholbares Werkzeug im Repo: Sonde mit sieben Kandidaten und Produkt-Gegenprobe, Treiber ohne Container, neun Fixtures und ein datierter Bericht, der alle Zahlen der Recherche (65 Familien, 573 Paare, A+ 467 gegen C+ 463, Ergaenzungsliste 77/10/0/30) exakt reproduziert.**

## Performance

- **Duration:** 30 min
- **Started:** 2026-09-23T19:38:00Z
- **Completed:** 2026-09-23T20:08:00Z
- **Tasks:** 3
- **Files modified:** 15 angelegt, 0 geaendert

## Accomplishments

- `scripts/dev/chain_probe.py` misst sieben Kandidatenketten ueber Formfamilien, prueft die Dichtheit der Stoppwortlisten in beiden Schreibweisen und faehrt die Siegerkette A+ Token fuer Token gegen `snowball_analyzer()` aus dem Paket. Eine abweichende Form ist Rueckgabecode 1; der Lauf meldete null.
- Vier Formfamilien-Fixtures mit genau 20, 14, 13 und 18 Familien und den Paarsummen 208, 56, 81 und 228. Alle im Plan aufgezaehlten Pflichtfamilien stehen in der jeweiligen Datei.
- `scripts/dev/measure_chains.sh` laeuft ohne Container, traegt die Erwartungswerte im Kopf und reicht den Rueckgabecode der Sonde durch.
- Der Messlauf reproduziert **jede** Zahl der Recherche: es 174/178, it 56/54, nl 57/57, pt 180/174, Summe 467 gegen 463, Ergaenzungsliste 77/10/0/30, Digest `d056d459...`, null Stoppwort-Lecks in beiden Schreibweisen.
- `backend/tests/fixtures/snowball_stopwords_0_26_2.txt` mit 308 spanischen, 279 italienischen, 203 portugiesischen und 101 niederlaendischen Zeilen, maschinell aus dem gepinnten Tag erzeugt, mit Herkunft, Datum, Lizenz und Wortzahlen im Kopf.
- Vier Verlustlisten direkt aus `rohdaten/verluste.tsv`: es 17, it 0, nl 12, pt 24 Formpaare.
- `docs/measurements/2026-09-analyseketten/README.md`, 8 Abschnitte, echte Umlaute, keine Em-Dashes, mit Umgebungstabelle, Kandidatentabelle, Leck-Tabelle, Verdikt je Sprache, der 15-zeiligen Testfall-Tabelle, der gerichteten Nebenrechnung und dem Abweichungsabschnitt.

## Task Commits

1. **Task 1: Die Sonde chain_probe.py** - `bcb1459` (feat)
2. **Task 2: Formfamilien-Fixtures und der Treiber ohne Container** - `812a64b` (feat)
3. **Task 3: Messlauf, Rohdaten, bekannte Verluste und Messbericht** - `39ad52b` (docs)

## Files Created/Modified

- `scripts/dev/chain_probe.py` - Sonde: sieben Kandidaten, Formfamilien-Metrik, Stoppwort-Dichtheit, Gegenprobe gegen `snowball_analyzer()`, geteilter Fixture-Leser `read_families`
- `scripts/dev/measure_chains.sh` - Treiber ohne Container, Erwartungswerte im Kopf, Pfadaufloesung ueber `CDPATH='' cd --`
- `backend/tests/fixtures/chain_cases_es.txt` - 20 Familien, 208 Paare
- `backend/tests/fixtures/chain_cases_it.txt` - 14 Familien, 56 Paare
- `backend/tests/fixtures/chain_cases_nl.txt` - 13 Familien, 81 Paare
- `backend/tests/fixtures/chain_cases_pt.txt` - 18 Familien, 228 Paare
- `backend/tests/fixtures/chain_known_losses_es.txt` - 17 Formpaare, die unter A+ nicht zueinander finden
- `backend/tests/fixtures/chain_known_losses_it.txt` - leer bis auf den Kopf, Italienisch ist unter A+ fehlerfrei
- `backend/tests/fixtures/chain_known_losses_nl.txt` - 12 Formpaare
- `backend/tests/fixtures/chain_known_losses_pt.txt` - 24 Formpaare
- `backend/tests/fixtures/snowball_stopwords_0_26_2.txt` - 891 Zeilen `sprache<TAB>wort` aus tantivy Tag 0.26.2
- `docs/measurements/2026-09-analyseketten/README.md` - der Messbericht
- `docs/measurements/2026-09-analyseketten/rohdaten/familien.tsv` - eine Zeile je Form und Kandidat
- `docs/measurements/2026-09-analyseketten/rohdaten/kennzahlen.txt` - ausschliesslich `name=wert`
- `docs/measurements/2026-09-analyseketten/rohdaten/verluste.tsv` - 53 Formpaare mit ihren Termen

## Decisions Made

- **Die Ausnahme der Sonde wird im Modulkopf benannt und sofort geschlossen.** Sechs der sieben Kandidaten gibt es im Produkt nicht, also baut die Sonde sie. `verify_against_product` faehrt A+ und `snowball_analyzer()` ueber jede Form jeder Familie und meldet jede Differenz einzeln auf stderr.
- **`read_families` lebt in der Sonde.** `scripts/` ist kein Paket, also kann der Import nur vom Test in die Sonde laufen, nie umgekehrt. Der Docstring sagt das.
- **Kein Import zwischen zwei Dev-Skripten.** `chain_probe` traegt einen eigenen kleinen Rust-Leser statt `stopword_supplement.parse_stopwords` zu importieren, weil ein solcher Import nur traegt, wenn der Interpreter zufaellig in `scripts/dev` gestartet wurde; die Task-Verifikation laedt die Datei per `importlib` aus `backend/`.
- **Die Messung nutzt die ausgelieferte Ergaenzungsliste.** `FOLDED_STOPWORDS` aus dem Paket statt einer in der Sonde neu abgeleiteten Liste, sonst vergleicht die Gegenprobe zwei verschiedene Ketten.
- **Der Lauf faehrt gegen tantivy 0.26.0.** Die Recherche mass gegen 0.26.2. Die Zahlen sind identisch; das ist im Bericht unter Punkt 8 als Unterschied benannt und stuetzt die Aussage, dass der Patch-Sprung die Tokenisierung nicht bewegt. Der Pin selbst haengt am Owner-Tor und wurde nicht angefasst.

## Deviations from Plan

None - plan executed exactly as written.

Zwei Praezisierungen innerhalb des Plans, beide ohne Regelbezug:

- Der Plan nennt fuer Spanisch die "`administracion`-Familie" ohne Formenzahl. Sie steht als `administración administracion` in der Fixture; die Pluralform derselben Klasse traegt bereits die `información`-Familie, und nur mit dieser Aufteilung treffen die Fixtures die im Plan geforderten Paarsummen (208) und die gemessenen Trefferzahlen (A+ 174, C+ 178) gleichzeitig.
- Die `<lang>_leaks_accented`- und `<lang>_leaks_flat`-Zeilen stehen nur dann in `kennzahlen.txt`, wenn `--stopwords` gegeben ist. Ohne die Liste ueberspringt die Sonde diesen Teil mit einer Zeile auf stderr, wie im Plan gefordert, und schreibt dann keine Zahl, die sie nicht gemessen hat.

## Issues Encountered

Keine. Der Messlauf endete im ersten Anlauf mit Rueckgabecode 0 und traf alle Erwartungswerte.

## Verification

- `sh scripts/dev/measure_chains.sh` : Rueckgabecode 0, drei nicht leere Rohdatendateien.
- `kennzahlen.txt`: `total_families=65`, `total_pairs=573`, `total_Aplus_hits=467`, `total_Cplus_hits=463`, `es_supplement=77`, `it_supplement=10`, `nl_supplement=0`, `pt_supplement=30`, alle vier Sprachen `leaks_accented=0` und `leaks_flat=0`.
- `uv run ruff check --config backend/pyproject.toml scripts/dev/chain_probe.py` und `ruff format --check`: gruen.
- `uv run ruff check`, `uv run ruff format --check`, `uv run pyright` (0 errors), `uv run vulture` (leer) aus `backend/`: gruen.
- `uv run python -m pytest -q`: **2507 passed, 15 skipped** in 225 s.
- `git diff --quiet backend/src/`: kein Produktionspfad angefasst.
- `sh -n scripts/dev/measure_chains.sh`: gueltig; die Datei enthaelt nirgends das Wort `docker`.
- Der Bericht enthaelt weder U+2013 noch U+2014 und hat 171 inhaltliche Zeilen.
- Die Stoppwort-Fixture zaehlt 308 spanische, 279 italienische, 203 portugiesische und 101 niederlaendische Zeilen.

## Known Stubs

Keine. Alle angelegten Dateien tragen echten, gemessenen Inhalt.

## Threat Flags

Keine neue Angriffsflaeche. Der Plan legt Werkzeug, Fixtures und Dokumentation an und beruehrt keinen Produktionspfad, keinen Netzwerkendpunkt und kein Schema. T-17-17 (Informationsabfluss der Sonde) ist als Sicherheitsregel im Modulkopf von `chain_probe.py` umgesetzt, T-17-18 (stille Anpassung abweichender Zahlen) ueber die Erwartungswerte im Treiberkopf und Abschnitt 8 des Berichts, T-17-19 (fremde Quelle) ueber Herkunft, Datum, Lizenz und Wortzahlen im Kopf der Stoppwort-Fixture, T-17-20 (Sonde misst sich selbst) ueber `verify_against_product`. T-17-SC: kein Paket installiert, `backend/uv.lock` unveraendert.

## Next Phase Readiness

- Plan 17-06 kann `read_families` aus `scripts/dev/chain_probe.py` importieren und die vier Verlustlisten als Doppelrichtungs-Behauptung pruefen; die Stoppwort-Fixture macht die Dichtheitsmessung offline testbar.
- `docs/language-analyzers.md` (Plan 17-07) kann Kettenordnung, Messzahlen und die Grenzen aus `docs/measurements/2026-09-analyseketten/README.md` zitieren statt sie neu zu behaupten.
- Das Owner-Tor bleibt unberuehrt: weder `backend/pyproject.toml` noch `backend/uv.lock`, `test_upgrade_compatibility.py`, `store/repo.py` oder `deploy-harp.yml` sind angefasst.

## Self-Check: PASSED

- Alle 15 im Summary genannten Dateien existieren auf der Platte.
- Alle drei Task-Commits stehen in der Historie: `bcb1459`, `812a64b`, `39ad52b`.
- STATE.md und ROADMAP.md wurden nicht angefasst; sie gehoeren dem Orchestrator.

---
*Phase: 17-owner-tor-und-analyseketten*
*Completed: 2026-09-23*
