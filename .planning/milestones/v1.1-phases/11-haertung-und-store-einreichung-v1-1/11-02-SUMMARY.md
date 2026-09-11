---
phase: 11-haertung-und-store-einreichung-v1-1
plan: 02
subsystem: ops-werkzeug
tags: [di-10-01, d-04, lastwerkzeug, ratsche, tdd]

# Dependency graph
requires:
  - phase: 10-vergleichsmessung-auf-der-aws-box
    provides: DI-10-01 mit der Stufentabelle und der Rohdatei rohdaten/97-stufe-16.json
  - phase: 11-haertung-und-store-einreichung-v1-1
    provides: 11-RESEARCH.md Abschnitt 2.2 und 4.2 mit beiden Fix-Wegen und der Ratschen-Bauform
provides:
  - "search_load.py zaehlt eine Ergebnisgruppe ohne Containerteil als Fehlschlag EmptyResultGroup"
  - "--min-hits als ausdruecklicher Schalter, Vorgabe 1, mit --min-hits 0 als Weg zurueck"
  - "hits_per_request und min_hits im Bericht, also der Fingerabdruck ohne Nextcloud-Protokoll"
  - "test_upgrade_compatibility.py als Waechter ueber die vier stabilen Indexmarken (D-04)"
affects: [11-06, 11-10, 11-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Messwerkzeug wird gegen einen gestellten Antwortkoerper geprueft, per Monkeypatch auf urlopen, statt gegen eine Box"
    - "Berichtsschluessel werden aus dem Syntaxbaum gelesen und nicht per Textsuche gezaehlt (Grep-Hygiene aus 06-10)"
    - "Ratsche gegen die eigene Zusage: Goldtabelle plus Selbsttest, der rot wird, wenn der Waechter selbst geloescht wird"

key-files:
  created:
    - backend/tests/test_upgrade_compatibility.py
  modified:
    - scripts/ops/search_load.py
    - backend/tests/test_ops_scripts.py

key-decisions:
  - "Beide Wege aus DI-10-01 zusammen, wie in 11-RESEARCH.md 4.2 empfohlen: Umdeutung mit Schalter plus eigene Kennzahl, statt einer von beiden"
  - "tantivy_version wird gegen den Banner gehalten und nicht gegen den nackten Wert; der Plan nennt '0.26.0', expected_versions liefert 'tantivy v0.26.0, index_format v7'. Die Goldtabelle bleibt wie geplant, der Vergleich prueft Enthaltensein und eine zweite Zusicherung haelt zusaetzlich 'index_format v7'"
  - "Der wordlist_hash wird ueber den Debian-Pin wngerman=20161207-15 gehalten und nicht ueber ein Digest-Literal; dazu der exakte tantivy-Pin, weil er den Banner erzeugt"
  - "Der Wert von --min-hits steht als min_hits im Bericht, damit eine Rohdatei ihre eigene Lesart traegt und ein Lauf mit 0 als solcher lesbar bleibt"

patterns-established:
  - "Ein Werkzeug in scripts/ops wird im Test per spec_from_file_location geladen und dabei in sys.modules eingetragen, sonst scheitert eine Dataclass mit slots"
  - "Zaehlnamen in Testnamen sind Reibung mit Absicht: die Zahl im Namen und die Zahl in der Zusicherung sind dieselbe"

requirements-completed: []

# Metrics
duration: 25min
completed: 2026-09-10
---

# Phase 11 Plan 02: Werkzeug-Fix DI-10-01 und die D-04-Ratsche Summary

**Das Lastwerkzeug zaehlt einen abgebrochenen Containeraufruf nicht mehr als Erfolg, meldet die Treffer je Anfrage und traegt seinen Schalterwert im Bericht; die D-04-Zusage hat einen Waechter, der bei jeder bewegten Indexmarke rot wird.**

## Performance

- **Duration:** rund 25 min, keine Box-Minute
- **Started:** 2026-09-10T18:55:00Z
- **Completed:** 2026-09-10T19:20:00Z
- **Tasks:** 3 von 3
- **Files modified:** 1 neu, 2 geaendert

## Accomplishments

- **DI-10-01 ist behoben.** `_one_search` bekommt `min_hits` als Parameter, und eine Ergebnisgruppe mit weniger Treffern ergibt das Fehlschlagkennwort `EmptyResultGroup`. Der `MalformedAnswer`-Zweig steht unveraendert davor, also bleibt ein Koerper der falschen Form ein Koerper der falschen Form und wird nicht unter dem neuen Namen abgelegt.
- **Der Schalter macht die Umdeutung ausdruecklich.** `--min-hits`, Vorgabe 1, mit einem Hilfetext, der die Ursache und den Weg zurueck nennt. `--min-hits 0` stellt das Verhalten vor dem 10.09.2026 her.
- **Der Fingerabdruck steht jetzt im Bericht.** `hits_per_request` direkt neben `hits_total`, auf zwei Nachkommastellen, und `min_hits` bei den uebrigen Schaltern. Die Tabelle aus `00-kernaussage.md` (5,40 bis 4,16 Treffer je Anfrage) muss kuenftig niemand mehr von Hand ausrechnen.
- **Der Modulkopf traegt die Beleglage:** was `failures` bis zum 10.09.2026 zaehlte, warum die Zahl falsch war, die 17 Abbrueche mit `cURL error 28`, die Rohdatei `rohdaten/97-stufe-16.json` mit `"failures": 0` ueber 160 Anfragen und Abschnitt 9.3 des Messberichts.
- **Sechzehn neue Zusicherungen**, davon zehn im Lastwerkzeug-Block und sechs in der Ratsche. Der Knopf-Zaehler stimmt wieder: `test_the_load_tool_names_its_four_knobs_in_the_usage`.
- **Die Ratsche gegen D-04 steht.** `GOLD_V1_0_3` mit den vier stabilen Marken, ein Befund je Marke mit Ist, Soll und dem Satz "ein Upgrade von 1.0.x wuerde jetzt einen Reindex ausloesen (D-04)", dazu das Indexformat des Banners, der Debian-Pin der Wortliste und der exakte tantivy-Pin.

## Task Commits

1. **Task 1, RED:** `93af4e2` , acht Faelle gegen das Werkzeug, alle rot mit `TypeError: _one_search() takes 2 positional arguments but 3 were given`, `KeyError: 'hits_per_request'`, `SystemExit: 2` und `assert 0 == 1`
2. **Task 1, GREEN:** `83f8557` , `--min-hits`, `EmptyResultGroup`, `hits_per_request`, `min_hits`, Modulkopf
3. **Task 2:** `e4808b4` , Knopf-Zaehler auf vier, Berichtsschluessel aus dem Syntaxbaum, Selbsttest des Lesers
4. **Task 3:** `ba39880` , `backend/tests/test_upgrade_compatibility.py`, die Ratsche mit Selbsttest

Gepusht: `2a3e4c8..ba39880` auf `origin/main`.

## Gate-Ergebnis

Alle ueber das ganze Repo, lokal vor dem Push:

| Gate | Ergebnis |
|---|---|
| `uv run python -m pytest -q` | **1984 passed, 15 skipped** (Grundlinie 1968 / 15, also plus 16) |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 121 files already formatted |
| `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run vulture src tests --min-confidence 80` | keine Ausgabe |

CI nach dem Push von `ba39880`, alle fuenf gruen: Python gates (34519607701),
Multi-arch image (34519607749), Integration (34519607691), Resilience
(34519607737), HaRP deploy (34519607753).

Gegenprobe zur Ratsche, ohne Commit gefahren: mit `SCHEMA_VERSION = 2` und dem Banner `tantivy v0.27.0, index_format v8` meldet `drift_findings` genau zwei Befunde, beide mit Marke, Ist, Soll und `D-04`.

## Files Created/Modified

- `scripts/ops/search_load.py` , `--min-hits` (Vorgabe 1), `EmptyResultGroup` hinter dem unveraenderten `MalformedAnswer`-Zweig, `hits_per_request` und `min_hits` im Bericht, ein Absatz im Modulkopf mit Rohdatei und Belegstelle.
- `backend/tests/test_ops_scripts.py` , Modul-Lader fuer das Werkzeug, gestellter Antwortkoerper ueber `urlopen`, zehn neue Zusicherungen, `test_the_load_tool_names_its_three_knobs_in_the_usage` umbenannt auf `..._four_knobs_...`.
- `backend/tests/test_upgrade_compatibility.py` (neu, 172 Zeilen) , `GOLD_V1_0_3`, `drift_findings`, sechs Zusicherungen inklusive Selbsttest.

## Was die Ratsche jetzt konkret festhaelt

| Marke | Gehaltener Wert | Woran sie haengt | Wie der Test rot wird |
|---|---|---|---|
| `schema_version` | `"1"` | `backend/src/findling/config.py` | Wertvergleich, Befund nennt Ist und Soll |
| `index_version` | `"1"` | `backend/src/findling/config.py` | Wertvergleich |
| `analyzer_version` | `"1"` | `backend/src/findling/index/analyzer.py` | Wertvergleich |
| `tantivy_version` | `"0.26.0"` im Banner | `tantivy.__version__`, gepinnt in `backend/pyproject.toml` | Enthaltensein im Banner, plus eigene Zusicherung auf `index_format v7` |
| `wordlist_hash` | kein Literal | Debian-Paket `wngerman=20161207-15` in `backend/Dockerfile` | Der Pin muss woertlich in der Dockerfile stehen |

Zusaetzlich: `expected_versions` muss genau die fuenf Marken in dieser Reihenfolge liefern, und der uebergebene Digest muss unveraendert durchgereicht werden. Eine verschwundene Marke ist ein Befund, weil `Store.version_mismatch` sie auch als Unterschied liest. Der Selbsttest haelt den Leser selbst: ein geloeschter Rumpf liefert die leere Liste und macht die Zusicherungen darueber rot statt still gruen.

## Deviations from Plan

**1. [Rule 1 - Bug im Plan] `tantivy_version` ist ein Banner und kein nackter Wert**
- **Gefunden bei:** Task 3, vor dem Schreiben der Datei
- **Sachverhalt:** Der Plan sagt, `expected_versions()` liefere fuer `tantivy_version` den Wert `"0.26.0"`. Gemessen liefert es `"tantivy v0.26.0, index_format v7"`, weil `open.py` den vollen Banner speichert (mit Begruendung im Docstring: tantivy verspricht nicht, dass das Plattenformat eigene Releases ueberlebt). Ein strikter Gleichheitsvergleich waere sofort rot gewesen, und zwar ohne dass sich irgendetwas bewegt haette.
- **Fix:** `GOLD_V1_0_3` bleibt wie im Plan gefordert (vier Schluessel, Werte `"1"`, `"1"`, `"1"`, `"0.26.0"`). Der Vergleich prueft fuer diese eine Marke Enthaltensein statt Gleichheit, und **zwei zusaetzliche** Zusicherungen fangen ab, was das Enthaltensein durchliesse: `index_format v7` muss im Banner stehen, und `tantivy==0.26.0` muss exakt in `backend/pyproject.toml` stehen. Die Ratsche ist damit strenger als die geplante, nicht schwaecher.
- **Datei:** `backend/tests/test_upgrade_compatibility.py`
- **Commit:** `ba39880`

**2. [Rule 3 - blockierender Defekt] Der Modul-Lader brauchte einen Eintrag in `sys.modules`**
- **Gefunden bei:** Task 1, beim ersten RED-Lauf
- **Sachverhalt:** `Sample` in `search_load.py` ist eine Dataclass mit `slots=True`. Deren Erzeugung baut die Klasse ein zweites Mal und schlaegt dafuer das eigene Modul unter seinem Namen nach. Ohne Eintrag endete der Import in einem `AttributeError` in `dataclasses.py`, der weder das Werkzeug noch die Testdatei nennt: die Tests waren rot, aber aus dem falschen Grund.
- **Fix:** Der Lader traegt das Modul unter `SEARCH_LOAD_MODULE` in `sys.modules` ein, mit dem Grund im Docstring. Danach war das RED sauber (`TypeError` zur fehlenden Signatur).
- **Datei:** `backend/tests/test_ops_scripts.py`
- **Commit:** `93af4e2` (in denselben RED-Commit aufgenommen, weil der Lader Teil des RED-Nachweises ist und der Commit noch nicht gepusht war)

**3. [Abweichung in der Bauform, nicht in der Sache] Berichtsschluessel per Syntaxbaum statt `tokenize`**
- **Sachverhalt:** Der Plan laesst `tokenize` oder einen Zeilenvergleich ohne Kommentare zu und verbietet ein nacktes `grep -c`. Gewaehlt ist `ast`: `report_keys` liest die Schluessel des Berichts-Wortverzeichnisses aus dem Baum, in ihrer Reihenfolge.
- **Warum:** Es ist die Bauform, die diese Datei schon fuehrt (`imported_packages`, der Zugangsdaten-Test), und nur der Baum traegt die **Reihenfolge**, die fuer die Zusicherung "der Quotient steht neben der Summe" gebraucht wird.

**4. Rundung auf zwei Nachkommastellen**
- **Sachverhalt:** 11-RESEARCH.md 4.2 schlaegt eine Nachkommastelle vor, der Plan zwei. Umgesetzt sind zwei, wie im Plan; die Zusicherung prueft `10 / 3 == 3.33`.

**5. REL-01 NICHT abgehakt**
- **Sachverhalt:** Die Plan-Frontmatter traegt `requirements: [REL-01]`, aber REL-01 ist die Store-Einreichung selbst und wird von den meisten Plaenen dieser Phase getragen. Wie in 11-01 bleibt die Kennung `Pending` bis zur tatsaechlichen Abgabe.

## Issues Encountered

Keine, die offen blieben. Der einzige Stolperstein war der Modul-Lader (Abweichung 2), und er war in einem Lauf erledigt.

## Nicht angefasst, mit Absicht

- **Kein `backend/src/`, kein `php/`, kein `.github/`.** `git diff --name-only 2a3e4c8..HEAD` nennt genau drei Dateien: das Werkzeug und die beiden Testdateien.
- **Die gefahrenen Messskripte** unter `docs/measurements/*/skripte/` und die Rohdaten bleiben unveraendert; ein nachtraeglicher Edit faelschte den Messbestand.
- **`docs/performance.md` und `docs/testing.md`** nennen das Werkzeug, aber keine der beiden Stellen macht eine Aussage ueber `failures` oder die Berichtsschluessel. Der Nachzug der Messtexte laeuft ohnehin gebuendelt in der Store-Text-Runde (DI-10-03).
- **`deferred-items.md` der Phase 10** ist nicht bearbeitet worden. DI-10-01 wird im Phase-11-Audit (Plan 11-10) mit dem Beweis aus 11-06 geschlossen, nicht hier.

## TDD Gate Compliance

- **Task 1** hat beide Tore: RED `93af4e2` (`test`, acht rote Faelle mit protokolliertem Grund), GREEN `83f8557` (`feat`). Kein REFACTOR noetig.
- **Task 2 und Task 3** sind selbst Test-Plaene und tragen deshalb `test`-Commits ohne eigenes GREEN. Das RED zu der Verhaltensaenderung, die Task 2 bewacht, liegt in `93af4e2`; die Ratsche aus Task 3 hat ihr Gegenstueck in der Gegenprobe oben und in ihrem Selbsttest gegen gestellte Marken.

## Next Phase Readiness

- **Plan 11-06 (Box-Beweis) kann den Fix gegen echte Last stellen.** Erwartet wird: eine Stufe, in der Abbrueche im Nextcloud-Protokoll stehen, meldet jetzt `failure_kinds: {"EmptyResultGroup": N}`, und `hits_per_request` faellt sichtbar unter den Wert der niedrigen Stufen.
- **Achtung fuer jeden kuenftigen Lauf:** die Vorgabe ist 1. Auf einer Instanz, deren Bestand die zehn festen Begriffe nicht traegt, meldet das Werkzeug jetzt Fehlschlaege und endet mit Code 1, wenn keine einzige Antwort Treffer hatte. Der Weg dorthin ist `--min-hits 0`, und der Lauf bleibt als solcher lesbar, weil `min_hits` im Bericht steht.
- **Plan 11-11 (Versionsbump) laeuft jetzt gegen einen Waechter:** wer eine Indexmarke bewegt, sieht es lokal in Sekunden und nicht erst bei einem Bestandsnutzer.
- **Plan 11-10 (Audit)** kann DI-10-01 mit diesem Plan und dem Box-Beweis schliessen; T-11-04 und T-11-05 aus dem Threat-Register sind hier bedient.

## Self-Check: PASSED

- `scripts/ops/search_load.py`: `min-hits` 4 Treffer, `EmptyResultGroup` 3, `hits_per_request` 2, Signatur `def _one_search(url: str, authorization: str, min_hits: int)`, `97-stufe-16.json` woertlich im Modulkopf, `--help` nennt den Schalter und die Vorgabe 1.
- `backend/tests/test_ops_scripts.py`: `..._three_knobs_...` 0 Treffer, `..._four_knobs_...` 1 Treffer, `EmptyResultGroup` und `"--min-hits", "0"` je vorhanden.
- `backend/tests/test_upgrade_compatibility.py` vorhanden, 172 Zeilen, `GOLD_V1_0_3` mit genau vier Schluesseln, `D-04` im Befundsatz, `wngerman=20161207-15` gefordert.
- Commits `93af4e2`, `83f8557`, `e4808b4`, `ba39880` im Log und auf `origin/main`.
- `git diff --name-only 2a3e4c8..HEAD` nennt keine Datei unter `backend/src/`, `php/` oder `.github/`.
- Keine Gedankenstriche, kein verbotenes Vokabular, ASCII in Quelltext und Testdateien wie im Repositoriumsbestand.

---
*Phase: 11-haertung-und-store-einreichung-v1-1*
*Completed: 2026-09-10*
