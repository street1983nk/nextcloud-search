---
phase: 17-owner-tor-und-analyseketten
verified: 2026-09-23T22:30:00Z
status: passed
score: 4/4 must-haves verified (Roadmap Success Criteria), LEX-01 und LEX-07 materiell erfuellt
overrides_applied: 0
gaps: []
deferred:
  - truth: "Ein unbekannter/nicht unterstuetzter Sprachname wird beim Start abgewiesen (aktive Verdrahtung der Positivliste gegen einen Produktionspfad)"
    addressed_in: "Phase 18"
    evidence: "Plan-Checker-Auflage aus dem Verifikationsauftrag, bestaetigt durch 17-02-SUMMARY.md Zeile 148: 'dass kein Produktionspfad sie liest, ist die ausdrueckliche Entscheidung des Plans (die Kettenfabrik haengt erst in Phase 18 daran)'"
human_verification: []
---

# Phase 17: Owner-Tor und Analyseketten Verification Report

**Phase Goal:** Die Grundsatzentscheide des Milestones sind schriftlich gefallen, bevor eine Zeile Code sie implizit trifft, und die vier Analyseketten es/it/nl/pt sind messend abgenommen.
**Verified:** 2026-09-23
**Status:** passed
**Re-verification:** Nein, Erstverifikation

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Datierter Owner-Entscheid zu allen sechs Grundsatzfragen plus E-17-7/E-17-8 liegt vor, vor jedem D-04-beruehrenden Code | VERIFIED | `.planning/phases/17-owner-tor-und-analyseketten/17-GRUNDSATZ-ENTSCHEID.md`, Abschnitt "Vollzug am 23.09.2026" (Zeilen 755-827): Datum 23.09.2026, gelesener Stand, alle acht Entscheide (E-17-1 bis E-17-8) mit Option "a" und Owner-Begruendung, CI-Beleg 35909161812, Plan-Zuordnung je Datei. Vollzugs-Checkliste (7 Punkte) vollstaendig mit Datum abgehakt |
| 2 | Zusammengefuehrte Testfall-Tabelle je Sprache gruen, `ascii_fold`-Position gemessen entschieden, Verdikt datiert in der Doku; Abnahmen laufen wirklich | VERIFIED | `docs/language-analyzers.md` enthaelt die 15-zeilige Testfall-Tabelle (STACK/FEATURES/PITFALLS), die Messtabelle (65 Formfamilien, 573 Paare, A+ 467 gegen C+ 463) und ein datiertes Verdikt (2026-09-23) samt "Known limits" fuer die zwei bewusst dokumentierten Verluste (informacion/informaciones, informacao/informacoes), die im Grundsatz-Entscheid E-17-8 als vom Owner mitunterschriebener Preis benannt sind. `uv run pytest tests/test_language_analyzers.py` aus `backend/`: **40 passed**. Rohdaten liegen unter `docs/measurements/2026-09-analyseketten/rohdaten/` (familien.tsv, kennzahlen.txt, verluste.tsv) |
| 3 | Unbekannter/nicht unterstuetzter Sprachname bringt den Container nicht per Rust-Panic zu Fall, sondern eine Positivliste (Muster `OCR_LANGUAGE_ALLOWLIST`) faengt ihn; `tantivy` auf 0.26.2, `index_format v7` unveraendert | VERIFIED (mit dokumentierter Phase-18-Einschraenkung) | `backend/src/findling/config.py:103-116`: `LANGUAGE_ALLOWLIST` (13 Eintraege, Kommentar verweist auf Muster `OCR_LANGUAGE_ALLOWLIST`). `backend/tests/test_language_allowlist.py`: 5 Tests, darunter ein Selbsttest, der die Panic-Klasse (romanian, Vertreter von arabic/greek/romanian/tamil/turkish) tatsaechlich gegen die laufende tantivy baut und `BaseException` faengt (deckt sowohl `PanicException` in 0.26.0 als auch `ValueError` in 0.26.2 ab). `backend/pyproject.toml:13`: `tantivy==0.26.2`; `backend/uv.lock` Zeile 996: `version = "0.26.2"`. `GOLD_INDEX_FORMAT = "index_format v7"` unveraendert in `backend/tests/test_upgrade_compatibility.py`. Die aktive Verdrahtung "beim Start abgewiesen" gegen einen echten Produktionspfad ist laut Auftrag und laut `17-02-SUMMARY.md` Zeile 148/152 bewusste Phase-18-Lieferung: siehe Abschnitt "Deferred Items" |
| 4 | Bestandsinstallation unveraendert: kein neues Feld, keine bewegte Versionsmarke (ausser der bewusst gelockerten `tantivy_version`-Haelfte), volle Suite gruen | VERIFIED | `backend/src/findling/config.py`: `SCHEMA_VERSION = 1`, `INDEX_VERSION = 1`, unveraendert. `backend/src/findling/index/schema.py`: nur die bekannten Felder (`name`, `title`, `path`, `ext`, `body_de`, `body_en`), keine neuen Sprachfelder. `backend/src/findling/index/open.py:123-141` (`expected_versions()`): weiterhin genau fuenf Marken, kein sechster `FOLDED_STOPWORDS`-Hash (Marken-Falle explizit vermieden). Volle Suite aus `backend/`: `uv run pytest -q` -> **2542 passed, 15 skipped** (deckt sich exakt mit dem im Grundsatz-Entscheid dokumentierten Endstand). CI-Lauf `35909161812` auf main: alle vier Matrix-Aeste (stable33/34/35, amd64+arm64) `success`, per `gh run view` bestaetigt |

**Score:** 4/4 Roadmap-Erfolgskriterien verifiziert

### Requirements Coverage

| Requirement | Beschreibung | Status | Evidenz |
|---|---|---|---|
| LEX-01 | Vier Analyseketten es/it/nl/pt, `ascii_fold`-Position messend entschieden, zusammengefuehrte Testfall-Tabelle als Abnahmekriterium | SATISFIED (materiell) | `backend/src/findling/index/analyzer.py` (`snowball_analyzer()`), `docs/language-analyzers.md`, `backend/tests/test_language_analyzers.py` (40 gruen). Die Ketten sind gebaut und gemessen abgenommen, aber laut Leitplanke D-04 in Phase 17 bewusst **nicht registriert** (kein Tokenizer-Eintrag in `index/open.py` fuer es/it/nl/pt) -- das ist die planmaessige Trennung "Kette bauen" (Phase 17) von "Kette anschliessen" (Phase 18/19), keine Luecke |
| LEX-07 | `tantivy` auf 0.26.2, stopword-Panic wird ValueError, `index_format v7` unveraendert, Sprachnamen ueber Positivliste | SATISFIED | Pin in `backend/pyproject.toml` und `backend/uv.lock` bestaetigt 0.26.2; `backend/tests/test_language_allowlist.py` testet die Panic-Klasse aktiv gegen die laufende Engine; `LANGUAGE_ALLOWLIST` in `config.py` vorhanden und durch Paritaetstest gegen die laufende tantivy abgesichert |

**Hinweis Requirements-Bookkeeping:** `.planning/REQUIREMENTS.md` fuehrt LEX-01 und LEX-07 noch als `[ ]` / Status "Pending" (Zeilen 11, 17, 62-63), und `.planning/ROADMAP.md` fuehrt Phase 17 noch als offene Checkbox mit "5/8 Plans Complete, In Progress" (Zeilen 49, 78-80, 164), obwohl alle 8 Plaene ein SUMMARY.md tragen und Plan 17-08 zuletzt am 23.09. 21:09 abgeschlossen wurde. Das ist ein Dokumentationsstand, kein Codebefund: die Aktualisierung dieser beiden Dateien ist ueblicherweise ein Abschlussschritt nach der Verifikation. Wird hier als Hinweis, nicht als Gap gefuehrt, weil kein materieller Beleg fehlt.

### Anti-Patterns und Marken-Falle

| Pruefung | Ergebnis |
|---|---|
| `FOLDED_STOPWORDS`-Hash NICHT in `index/open.py` | BESTAETIGT: nur `stopwords.py` und `test_language_analyzers.py` referenzieren `FOLDED_SUPPLEMENT_SHA256`; `expected_versions()` fuehrt weiterhin exakt fuenf Marken |
| `ANALYZER_VERSION` unveraendert (D-04) | BESTAETIGT: bleibt `1` in `analyzer.py`; Modulkopf begruendet explizit, warum eine gebaute, aber nicht registrierte Kette die Marke nicht bewegt |
| TBD/FIXME/XXX in phasenrelevanten Dateien | Keine gefunden in den gepruepften Dateien (`config.py`, `analyzer.py`, `open.py`, `repo.py`, `test_language_allowlist.py`, `test_language_analyzers.py`, `test_upgrade_compatibility.py`) |
| Deferred-items.md | Zwei zurueckgestellte Befunde aus Plan 17-08 (ueberfluessiger `pyright: ignore`-Kommentar, drei veraltete Versionsangaben in `THIRD-PARTY.md`), beide explizit begruendet und auf spaetere Plaene verwiesen, keine Blocker |

### Qualitaetsgates (Backend)

| Gate | Ergebnis |
|---|---|
| `uv run pytest -q` (volle Suite) | 2542 passed, 15 skipped, 259s |
| `uv run pytest tests/test_language_analyzers.py -q` | 40 passed |
| `uv run pytest tests/test_language_allowlist.py tests/test_upgrade_compatibility.py tests/test_analyzer.py -q` | 78 passed |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 129 files already formatted |
| `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run vulture` | keine Befunde |
| `gh run view 35909161812` | main, alle 4 Matrix-Jobs success |

### Human Verification Required

Keine. Alle Wahrheiten sind am Code, an den Tests und an einem echten CI-Lauf pruefbar; nichts erfordert visuelle oder Laufzeit-Beurteilung durch einen Menschen.

### Gaps Summary

Keine Gaps. Alle vier Roadmap-Erfolgskriterien sind am Code, an lauffaehigen Tests und an einem gruenen CI-Lauf verifiziert, nicht nur an den SUMMARY.md-Behauptungen. Die einzige offene Verdrahtung ("beim Start abgewiesen") ist laut Verifikationsauftrag ausdruecklich als Phase-18-Lieferung zu fuehren und dokumentiert bereits heute im Plan-Ergebnis, warum kein Produktionspfad die Positivliste in Phase 17 liest. Einzig auffaellig ist der Bookkeeping-Rueckstand in ROADMAP.md und REQUIREMENTS.md (Checkboxen und Status-Spalte nicht nachgezogen); das ist als Hinweis vermerkt, nicht als Blocker gewertet, weil es reine Dokumentationspflege ohne Codebezug ist.

---

*Verified: 2026-09-23*
*Verifier: Claude (gsd-verifier)*
