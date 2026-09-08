---
phase: 08-deutsche-komposita-ohne-behelf
verified: 2026-09-08T22:30:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 8: Deutsche Komposita ohne Behelf Verification Report

**Phase Goal:** Ein Nutzer, der ein Teilwort eintippt, findet die Dokumente mit dem
zusammengesetzten Wort, und die Wortliste dahinter ist lizenzrechtlich sauber und
dokumentiert.
**Verified:** 2026-09-08T22:30:00Z
**Status:** passed
**Re-verification:** No, initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria, aktueller Wortlaut nach Owner-Entscheid a)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | "Belehrung" findet "Rechtsmittelbelehrung", "Auszug" findet "Grundbuchsauszug", "Erinnerung" findet "Zahlungserinnerung"; jeder dieser Faelle wird ohne `Filter.split_compound` rot; "Vereinbarung"/"Pachtvereinbarung" ist als Kriterium zurueckgezogen, "Genehmigung"/"Baugenehmigung" als benannte Grenze gefuehrt | VERIFIED | `.github/workflows/integration.yml:1428` Schritt "The ten German language cases, as the owner", Faelle 8-10 (Zeilen 1508-1558) benutzen genau Belehrung/Auszug/Erinnerung gegen 15-schweiz-baubewilligung.pdf/16-oesterreich-mitteilung.pdf/30-nur-ein-bild.pdf. `backend/tests/test_corpus_terms.py::CI_TERMS` (Zeile 71-77) spiegelt exakt dieselben drei Paare. `test_a_ci_term_finds_nothing_once_the_splitter_is_taken_out` (Zeile 229, lokal gruen) ist der lokale Waechter fuer den "wird ohne Splitter rot"-Beweis; der AUDIT.md-Mit/Ohne-Splitter-Tisch (Fund H-01, gemessen 08.09.2026 im echten Debian-Abbild) belegt es zusaetzlich am realen Rezept. `Vereinbarung` steht in `SPLIT_INDEPENDENT`/`test_a_split_independent_term_is_kept_out_of_the_ci_set` als benannter Gegenfall. `Baugenehmigung` steht in `COMPOUNDS` (test_analyzer.py:107) mit genau einem Token und in `docs/german-analyzer.md` "Known limits" als benannte Grenze |
| 2 | Zerlegung laeuft ueber `split_compound` mit der mitgelieferten Wortliste, nicht ueber eine Prefix-Query; ein Test belegt den Weg statt nur das Ergebnis | VERIFIED | `backend/tests/test_index_open.py`: `test_without_the_splitter_the_constituent_finds_nothing` (Zeile 289, Negativkontrolle), `test_a_mere_prefix_of_the_compound_does_not_hit` (Zeile 310, Praefix-Gegenprobe), `test_the_question_side_produces_the_same_terms_as_the_index_side` (Zeile 325, Termgleichheit). `backend/tests/test_analyzer.py::filter_chain` (Zeile 545) + `test_the_german_chain_stands_in_the_measured_order` (Zeile 562) haelt die Filterreihenfolge per AST fest. Alle vier Tests lokal gruen (siehe Testlauf unten). `index/analyzer.py`, `index/open.py`, `query/rewrite.py` sind im Phasendiff byteweise unveraendert (`git diff --stat b7f7b01..ba131b2` = 0 Zeilen fuer alle drei Dateien) |
| 3 | Lizenz, Herkunft und Fassung der Wortliste stehen im Repo und im Abbild, Vertraeglichkeit mit AGPL-3.0 begruendet | VERIFIED | `THIRD-PARTY.md:18-33` begruendet GPL-2+/AGPL-3.0-Kompatibilitaet (AGPLv3 section 13) und nennt Lizenz, Herkunft (Debian `wngerman`), Lizenztextpfad im Abbild. `.github/workflows/docker.yml` Schritt "The word list, its version and its licence in this image" prueft im veroeffentlichten Abbild `dpkg-query` gegen `20161207-15`, Zeilen/Bytes gegen `356010`/`4725887`, Anwesenheit und Modus `0444` von `/usr/local/share/findling/COPYING.wngerman` (Zeilen 242-292, alle vier Literale mit `grep` bestaetigt). Trockenlauf mit vier einzeln gefahrenen Rotbeweisen dokumentiert in 08-03-SUMMARY.md |
| 4 | Wechsel der Wortliste erzwingt sichtbar Reindex (Digest neben `schema_version`/`analyzer_version`) | VERIFIED | `backend/tests/test_status_endpoint.py::test_switching_the_dictionary_variant_asks_for_a_reindex` (Zeile 408, lokal gruen) faehrt den echten Adminweg: `FINDLING_COMPOUND_DICT` umstellen, Marken-Cache leeren, Statusroute meldet `reindexRequired=True` mit der Marke `wordlist_hash` (`api/resources.py:52`, `UNPROVEN_WORDLIST = "wordlist_hash"`). Rotbeweis mit zwei Mutationen in 08-03-SUMMARY.md dokumentiert |
| 5 | Endungsvergleich abgeschlossen dokumentiert, jede Abweichung benannt, jeder Befund Testfall oder bewusst offen | VERIFIED | `docs/measurements/2026-09-nachmessung-m7g/README.md` Abschnitt 7 traegt zwei Absaetze "Entscheidung: ..." (Zeilen 297, 340). Alle sechs zitierten Testnamen mit `grep -n` gegenverifiziert: `test_exactly_twenty_files_lie_above_the_size_cap` (`test_load_corpus.py:113`), `test_a_file_over_the_size_cap_is_skipped_a_second_time` (`test_extract_errors.py:297`), `test_no_text_layer_is_requeued_and_not_acknowledged` (`test_poller.py:452`), `test_a_stored_no_text_layer_verdict_does_not_block_the_handover` (`test_poller.py:526`) existieren exakt wie zitiert und laufen gruen |

**Score:** 5/5 truths verified

### Requirements Coverage (QUAL-01, QUAL-02, QUAL-03)

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| QUAL-01 | 08-03, 08-05 | Lizenzkonforme Wortliste, AGPL-kompatibel dokumentiert | SATISFIED | `THIRD-PARTY.md`, CI-Schritt im Abbildbau (siehe Truth 3) |
| QUAL-02 | 08-01, 08-02, 08-04 | Teilwortsuche findet Komposita, CI-Sprachfall-Set, muss ohne Splitter rot werden | SATISFIED | Truth 1 und 2, plus Wegbeweis in `test_index_open.py`/`test_analyzer.py` |
| QUAL-03 | 08-05 | Endungsvergleich durchgefuehrt und dokumentiert, Befunde als Testfaelle | SATISFIED | Truth 5 |

`REQUIREMENTS.md` selbst traegt die Kaestchen fuer QUAL-01 bis QUAL-03 noch als `[ ]` und die Traceability-Tabelle noch als "Pending" -- laut allen fuenf SUMMARY-Dateien ist das bewusst dem Orchestrator ueberlassen ("Beides pflegt der Orchestrator nach der Phasenverifikation"). Kein Waisenbefund: alle drei Requirements sind genau Phase 8 zugeordnet.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `scripts/dev/compound_probe.py` | Messsonde gegen Rezept A, `--against` fuer Gleichheitsbeweis | VERIFIED | Existiert, ruff/ruff format gruen, ruft `german_analyzer`/`load_constituents` des Produkts |
| `scripts/dev/measure_compounds.sh` | Wegwerf-Container, wngerman/tantivy gepinnt | VERIFIED | Enthaelt `wngerman=20161207-15`, `tantivy==0.26.0`, `--against`-Unterstuetzung |
| `docs/measurements/2026-09-komposita-rezept-a/` | Messbericht mit Rohdaten | VERIFIED | README.md + drei Rohdatendateien vorhanden, TSV/kennzahlen mit den Zahlen 356010/276496/digest |
| `backend/tests/fixtures/compound_cases_de.txt` | 46+ Faelle, spaeter 48 | VERIFIED | `wc -l` = 48 |
| `backend/tests/fixtures/constituents_de.txt` | erweiterte Fixture, sortiert, ohne Doppelte | VERIFIED | `wc -l` = 223, `sort -u` liefert dieselbe Datei |
| `backend/tests/test_index_open.py` | Wegbeweis-Tests | VERIFIED | Vier Zieltests vorhanden und lokal gruen |
| `backend/tests/test_analyzer.py` | 21-Zeilen-COMPOUNDS, filter_chain-Waechter | VERIFIED | 21 Tupel in COMPOUNDS gezaehlt, `filter_chain` + Test vorhanden |
| `backend/tests/test_corpus_terms.py` | Korpus-Waechter mit zwei Toren | VERIFIED | Existiert, 10 Testfunktionen, CI_TERMS = Belehrung/Auszug/Erinnerung, LETTER_TRAPS haelt Verkehr/Abgabe als verworfen |
| `backend/tests/test_status_endpoint.py` | Variantenwechsel-Test | VERIFIED | `test_switching_the_dictionary_variant_asks_for_a_reindex` vorhanden und gruen |
| `.github/workflows/docker.yml` | Lizenz-/Versions-CI-Schritt | VERIFIED | Schritt mit allen vier Literalen vorhanden, YAML parst |
| `.github/workflows/integration.yml` | Zehn deutsche Sprachfaelle | VERIFIED | "The ten German language cases, as the owner", 0 Treffer fuer "seven German language cases", YAML parst |
| `THIRD-PARTY.md` | Lizenzbegruendung + Hinweis auf CI-Mitfahrt | VERIFIED | Abschnitt vorhanden, nennt Schrittnamen woertlich |
| `docs/german-analyzer.md` | Known limits erweitert | VERIFIED | Vier neue/erweiterte Abschnitte vorhanden, keine Nennung von "sixteen test compounds" mehr |
| `docs/measurements/2026-09-nachmessung-m7g/README.md` | Zwei Entscheidungssaetze | VERIFIED | Beide "Entscheidung:"-Absaetze vorhanden |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `test_index_open.py` | `index/open.py` | `register_tokenizer`, splitterlose Kette vor dem Schreiben | WIRED | `grep -c register_tokenizer` = 2, Negativkontrolle schreibt/fragt auf derselben ueberschriebenen Kette |
| `test_analyzer.py::filter_chain` | `index/analyzer.py` | `ast.parse` ueber die Quelldatei | WIRED | Test vergleicht mit `==` gegen vollstaendige Liste `["lowercase", "split_compound", "custom_stopword", "stopword", "remove_long", "stemmer"]` |
| `docker.yml` CI-Schritt | veroeffentlichtes Abbild | `docker run --rm --network none` gegen `${IMAGE}@${DIGEST}` | WIRED | Schritt steht im Job mit `steps.push.outputs.digest`, vier Pruefungen mit vier Fehlermeldungen |
| `test_status_endpoint.py` | `api/resources.py::version_drift` | Statusroute meldet `reindexRequired`/`wordlistHash` | WIRED | Test ruft echte Route, prueft `expected_marks() is not None` gegen Ersatzantwort UNPROVEN_WORDLIST |
| `test_corpus_terms.py` | `scripts/dev/build_corpus.py` | Modul aus Pfad geladen, `FILES`/`UNIQUE_TERMS` gelesen | WIRED | `_load_build_corpus`-Muster uebernommen, `UNIQUE_TERMS` traegt die drei neuen Begriffe, `git status --short testdata/corpus` leer |
| `integration.yml` | `testdata/corpus` | OCS-Suchroute mit Konstituent als Suchbegriff | WIRED (CI-seitig ungeprueft in diesem Lauf) | Workflow laeuft nur auf `push`/`pull_request` auf `main`; lokale Vorpruefung ist `test_corpus_terms.py`, laut 08-04-SUMMARY explizit als "Beweis erst beim ersten Lauf auf main" benannt |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Volle Backend-Testsuite | `cd backend && uv run pytest -q` | 1749 passed, 15 skipped, 162,33 s | PASS |
| Zielgerichtete Phase-8-Tests | `uv run pytest -q tests/test_index_open.py tests/test_analyzer.py tests/test_status_endpoint.py tests/test_corpus_terms.py` | 154 passed | PASS |
| ruff check/format (backend) | `uv run ruff check .` / `ruff format --check .` | All checks passed / 117 files formatted | PASS |
| pyright (backend) | `uv run pyright` | 0 errors, 0 warnings | PASS |
| vulture (backend) | `uv run vulture src tests --min-confidence 80` | keine Ausgabe | PASS |
| ruff auf scripts/dev/*.py | `uv run ruff check ../scripts/dev/compound_probe.py ../scripts/dev/build_corpus.py` | All checks passed, formatted | PASS |
| `docker.yml`/`integration.yml` YAML-Gueltigkeit | `python -c "yaml.safe_load(...)"` | beide parsen | PASS |
| Keine Produktionscode-Aenderung ausserhalb der 7 Kommentarzeilen | `git diff --stat b7f7b01..ba131b2 -- index/analyzer.py index/open.py query/rewrite.py` | 0 Zeilen | PASS |

### Zahlenkonsistenz (quer über Doku, Tests, CI, Roadmap/Requirements)

| Zahl | Ort | Ergebnis |
|---|---|---|
| 21 Kompositafaelle | `COMPOUNDS` in `test_analyzer.py` | 21 Tupel gezaehlt |
| 10 CI-Sprachfaelle | `integration.yml` Schrittname, `ROADMAP.md` Phase 10 SC2, `REQUIREMENTS.md` MESS-02 | alle drei nennen "zehn"/"10" |
| 223 Fixture-Eintraege | `backend/tests/fixtures/constituents_de.txt` | `wc -l` = 223, sortiert, ohne Doppelte |
| 48 Messfaelle | `backend/tests/fixtures/compound_cases_de.txt`, Docstring `test_analyzer.py` | `wc -l` = 48, Docstring nennt "48 cases" |

Keine Abweichung gefunden.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `.planning/STATE.md` | 5-14, 28-33 | Commit `ba131b2` ("STATE auf den Ausfuehrungsstand gezogen (M-05, L-07)") behauptet, den Audit-Befund M-05 (STATE.md widerspricht ROADMAP.md) und L-07 (Em-Dashes) zu schliessen, aendert aber nur zwei Textzeilen. `status: executing`, `stopped_at: Completed 06-10-PLAN.md`, `Plan: 1 of 5`, `completed_plans: 4`, `percent: 20` und `Status: Executing Phase 08` bleiben unveraendert stehen, obwohl Phase 8 laut ROADMAP.md komplett ist (alle 5 Plaene). Zusaetzlich steht in Zeile 28 weiterhin ein echtes Em-Dash-Zeichen (U+2014, bestaetigt mit `grep -nP` auf Byteebene), das L-07 ausdruecklich als zu entfernen benannt hatte | WARNING (kein Blocker fuer den Phasenzweck) | STATE.md bleibt fuer Session-Fortsetzung ("weiter" nach `/clear`) irrefuehrend: ein Leser landet an Phase 08 Plan 1, obwohl Phase 8 fertig und Phase 9 die naechste offene Arbeit ist. Betrifft keine der 5 Roadmap-Erfolgskriterien und keine der drei Requirements der Phase, da STATE.md laut allen fuenf Plan-Summaries explizit dem Orchestrator gehoert und keinem der Phasenplaene zugewiesen war |
| `.planning/REQUIREMENTS.md` | 15-17, 54-56 | Kaestchen fuer QUAL-01/02/03 stehen noch als `[ ]`, Traceability-Tabelle noch "Pending" | INFO, kein Befund | Laut 08-05-SUMMARY.md bewusst dem Orchestrator nach der Phasenverifikation ueberlassen, kein Widerspruch zur inhaltlichen Erfuellung |

**Empfehlung zum STATE.md-Befund:** Da dies eine reine Planungsartefakt-Pflege ist (kein Produktcode, keine der fuenf Erfolgskriterien betroffen) und in allen Plan-Summaries ausdruecklich als Orchestrator-Zustaendigkeit deklariert wurde, wird hier keine Blockierung der Phase empfohlen. Es sollte aber im Zuge des Phasenabschlusses nachgezogen werden (Plan/Status/Prozentzahlen aktualisieren, verbleibendes Em-Dash entfernen), damit die Commit-Behauptung "M-05, L-07" nachtraeglich stimmt.

### Human Verification Required

Keine. Alle fuenf Erfolgskriterien sind ueber Tests, CI-Konfiguration und Dokumentation programmatisch nachprueft; kein Kriterium haengt an visueller Darstellung, Echtzeitverhalten oder einer externen Integration, die nur ein Mensch beurteilen koennte. Der einzige Punkt, der programmatisch nicht abschliessend geprueft werden konnte, ist der tatsaechliche erste Lauf von `integration.yml` auf `main` fuer die drei neuen Sprachfaelle (Faelle 8-10) -- das ist aber kein Verifikationsluecke dieser Pruefung, sondern eine strukturelle Eigenschaft des Workflows selbst (laeuft nur auf `push`/`pull_request`), die alle Phasenplaene (08-04-SUMMARY, 08-01-SUMMARY) selbst so benennen und durch die lokale Vorpruefung `test_corpus_terms.py` bereits abgedeckt haben.

### Gaps Summary

Keine Gaps bei den fünf Erfolgskriterien der Phase, bei QUAL-01/02/03 oder bei den Kernartefakten. Alle Testfunktionen, die Roadmap und Dokumentation zitieren, existieren wortgleich und laufen lokal grün (1749 passed, 15 skipped); die Qualitätsgates (ruff, ruff format, pyright, vulture) sind grün für backend und für die betroffenen scripts/dev/*.py; kein Produktionscode außerhalb von sieben Kommentarzeilen in tools/index_status.py wurde verändert; alle quer referenzierten Zahlen (21, 10, 223, 48) stimmen überein.

Der einzige gefundene Mangel ist eine Diskrepanz zwischen der Commit-Behauptung "STATE auf den Ausfuehrungsstand gezogen (M-05, L-07)" und dem tatsächlichen Inhalt von STATE.md, die als WARNING (nicht blockierend) oben dokumentiert ist. Da STATE.md laut Konvention der Phase explizit dem Orchestrator und nicht den Ausführungsplänen gehört, hindert dies die Feststellung "Phase 8 Ziel erreicht" nicht.

---

*Verified: 2026-09-08T22:30:00Z*
*Verifier: Claude (gsd-verifier)*
