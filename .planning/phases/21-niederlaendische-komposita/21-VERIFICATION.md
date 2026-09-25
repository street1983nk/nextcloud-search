---
phase: 21-niederlaendische-komposita
verified: 2026-09-25T16:40:36Z
status: passed
score: 9/9 must-haves verified
overrides_applied: 0
---

# Phase 21: Niederlaendische Komposita Verification Report

**Phase Goal:** Nutzer findet niederlaendische Komposita ueber ihre Glieder (Beispiel:
`gemeentebelastingen` ueber `belasting`), oder die Phase faellt am eigenen Tor als Ganzes.
GO-Tor erteilt am 25.09.2026 (21-GO-ENTSCHEID.md, Fenster 4-14, Liste freigegeben, CC-BY-3.0).
**Verified:** 2026-09-25T16:40:36Z
**Status:** passed
**Re-verification:** No , initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | D-08 (stempelt der fullreindex-Ausweg die Verzeichnismarken?) wurde per Test beantwortet BEVOR die nl-Marke gebaut wurde | VERIFIED | `backend/tests/test_index_rebuild.py` enthaelt `test_the_full_reindex_way_out_leaves_the_marks_of_a_directory_as_they_were`; Suite gruen |
| 2 | Eine Sprach-/Schema-Drift, die der Band-Umbau beantwortet, hebt beim Oeffnen des Zustands im Poller keine Generation mehr | VERIFIED | `open.py:start_rebuild_on_drift(..., answered_elsewhere=...)`, Aufruf in `poller.py` mit `answered_elsewhere=MARKS_A_REBUILD_ANSWERS` gefunden |
| 3 | Das Abbild traegt die niederlaendische Wortliste aus wdutch=1:2.20.19+1-3 mitsamt Lizenztext, CI prueft Version/Zeilen/Bytes/Lizenzzeile/Modus | VERIFIED | `backend/Dockerfile:239-244` (Pin, `install -D -m 0444 COPYING.wdutch`); `.github/workflows/docker.yml:300-324` (Gate mit 413288/5096240/`License: CC-BY-3.0`) |
| 4 | THIRD-PARTY.md nennt CC-BY-3.0 fuer die OpenTaal-Liste (D-04) | VERIFIED | `THIRD-PARTY.md:54-67` Abschnitt "The Dutch word list" mit CC-BY-3.0, OpenTaal-Attribution, Upstream-Wahlfreiheit als Anmerkung |
| 5 | Rezept B (Fenster 4-14, Faltung vor dem Splitter, Tussenklanken s/e/en) ist als eigenes Modul gebaut, ANALYZER_VERSION bleibt 1 | VERIFIED | `wordlist_nl.py:84-85` (`MIN_LEN=4, MAX_LEN=14`), `analyzer.py:138` (`ANALYZER_VERSION = 1`), `DUTCH_CHAIN_VERSION: Final = 1` als getrennter Zaehler |
| 6 | Die siebte Marke `wordlist_hash_nl` verhaelt sich wie die Sprachmarke (nicht gesaet, Fehlen bei off = Altbestand, Schreiben nur hinter Verzeichnistausch/-neubau) | VERIFIED | `open.py:96,256,352,412`, `rebuild.py:116,243,948`, entsprechende Tests in `test_store_repo.py`/`test_index_rebuild.py` laufen in der gruenen Suite |
| 7 | Splitterkette steht hinter der Faltung, wird nur bei aktivem nl registriert (freie Registrierung, 8 Ketten) und `gemeentebelastingen` wird ueber `belasting` gefunden, ohne Splitter kein Treffer | VERIFIED | `open.py:192` `register_tokenizer(TOKENIZER_NL, dutch_chain_for(dutch))`; CI-Lauf 36157139922, Schritt "Language proof": Fall `nlc` gruen auf allen 4 Matrixzeilen (unabhaengig per `gh run view` bestaetigt) |
| 8 | Bestandsinstallationen ohne nl bleiben unberuehrt (kein Banner, kein Umbau), End-to-End ueber Store upgrade 5 (D-09) | VERIFIED | CI-Lauf 36157139922: "Store upgrade 5" success, laut SUMMARY "all seven assurances hold"; unabhaengig per `gh run view` als `success` bestaetigt |
| 9 | Kritische Review-Befunde (CR-01 Container-Absturz bei korruptem Artefakt, WR-01 Automaten-Race, WR-02 fehlender Rebuild bei Enable) sind tatsaechlich im Code behoben | VERIFIED | `wordlist_nl.py`/`wordlist.py` lesen mit `errors="replace"`, `resources.py:243,256` faengt `(OSError, UnicodeDecodeError)`; `analyzer.py:183,205,401,450,485` `_GERMAN_LOCK`/`_DUTCH_LOCK` um Lookup+Bau; `main.py:302` `_start_the_rebuild_if_due` von Lifespan UND `enabled_handler` gerufen; passende Tests (`\xff\xfe\x00kaputt`, `threading.Barrier`) vorhanden |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/src/findling/index/wordlist_nl.py` | Rezept B, Digest-Cache, fail-closed | VERIFIED | 323 Zeilen, `MIN_LEN`/`MAX_LEN`/`TUSSENKLANKEN`/`dutch_mark`/`DUTCH_CHAIN_VERSION` vorhanden, `errors="replace"`-Fix drin |
| `backend/src/findling/index/analyzer.py` | `dutch_analyzer`, `cached_dutch_analyzer`, `dutch_chain_for`, Lock | VERIFIED | Funktionen vorhanden, `_DUTCH_LOCK`/`_GERMAN_LOCK` umschliessen Lookup und Bau |
| `backend/src/findling/index/open.py` | `DUTCH_MARK`, `expected_versions(..., dutch_mark=...)`, freie Registrierung | VERIFIED | Alle Symbole gefunden |
| `backend/src/findling/index/rebuild.py` | `MARKS_A_REBUILD_ANSWERS` mit `DUTCH_MARK`, `stamp_after_swap(..., dutch_mark=...)` | VERIFIED | Gefunden, Marke wird hinter dem Tausch geschrieben |
| `backend/src/findling/store/repo.py` | `_dutch_list_is_legacy`, Saat-Ausnahme | VERIFIED | Laut SUMMARY 21-05 umgesetzt, in gruener Suite getestet |
| `backend/Dockerfile` | wdutch-Pin, COPYING.wdutch 0444 | VERIFIED | Zeilen 239-244 |
| `.github/workflows/docker.yml` | CI-Gate fuer wdutch | VERIFIED | Zeilen 300-324, prueft Version/Zeilen/Bytes/Lizenz |
| `.github/workflows/deploy-harp.yml` | Fall `nlc` im Schritt Language proof | VERIFIED | Zeilen 912-1164, fuenf Faelle inkl. `nlc`, CI gruen |
| `THIRD-PARTY.md` | Abschnitt "The Dutch word list" | VERIFIED | Zeilen 54-67 |
| `docs/dutch-analyzer.md` | Referenzdokument | VERIFIED | 248 Zeilen, existiert |
| `docs/performance.md`, `docs/language-analyzers.md` | Budget-Nachtrag, Kompositum-Verweis | VERIFIED (laut Diff-Belegen in SUMMARY, nicht erneut voll gelesen) | Grep-Belege aus SUMMARY plausibel, Kernaussagen (wordlist_hash_nl, 316740) durch Testgates (`test_measurement_scripts.py`, gruen in Suite) abgesichert |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `poller.py` | `rebuild.MARKS_A_REBUILD_ANSWERS` | `answered_elsewhere=MARKS_A_REBUILD_ANSWERS` | WIRED | Grep bestaetigt Aufruf |
| `analyzer.py` | `wordlist_nl.py` | `TUSSENKLANKEN`/`build_artifact_nl` Import | WIRED | Kein Importkreis, laut SUMMARY 21-03 grep-belegt |
| `open.py` | `analyzer.dutch_chain_for` | `register_tokenizer(TOKENIZER_NL, dutch_chain_for(dutch))` | WIRED | Zeile 192 bestaetigt |
| `rebuild.py`/`poller.py`/`resources.py`/`one_load.py` | `wordlist_nl.dutch_digest_for`/`dutch_mark` | `dutch=dutch_digest_for(languages)`, `dutch_mark=dutch_mark(languages)` an jeder Aufrufstelle | WIRED | AST-Gates `test_every_caller_in_src_names_the_dutch_mark`/`..._dutch_choice` in gruener Suite, Selbsttests vorhanden |
| `resources.py` | CR-01-Fix | `except (OSError, UnicodeDecodeError)` als zweites Netz | WIRED | Zeilen 243, 256 bestaetigt |
| `main.py enabled_handler` | `_start_the_rebuild_if_due` | direkter Aufruf aus `enabled_handler` UND Lifespan | WIRED | Zeilen 295, 873 bestaetigt (WR-02) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Volle Backend-Suite laeuft lokal gruen | `cd backend && uv run pytest -q` | `2985 passed, 15 skipped, 1 warning in 183.89s`, exit 0 | PASS |
| CI-Laeufe der Phase sind tatsaechlich gruen (nicht nur laut SUMMARY) | `gh run view <id> --json status,conclusion,name` fuer alle 5 zitierten Laeufe | alle 5: `"status":"completed","conclusion":"success"` | PASS |
| CR-01-Fix vorhanden | grep `errors="replace"` in wordlist_nl.py/wordlist.py, grep `UnicodeDecodeError` in resources.py | Treffer an allen erwarteten Stellen | PASS |
| WR-01-Fix vorhanden | grep `_DUTCH_LOCK`/`_GERMAN_LOCK`, grep `Barrier` in test_index_open.py | Locks umschliessen Lookup+Bau, Barrier-Test existiert | PASS |
| WR-02-Fix vorhanden | grep `_start_the_rebuild_if_due` in main.py | Wird von Lifespan UND `enabled_handler` gerufen | PASS |
| Debt-Marker-Scan auf phasenrelevanten Dateien | grep `TBD\|FIXME\|XXX` auf 7 Kerndateien | keine Treffer | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| KOMP-01 | 21-01 bis 21-09 (alle neun Plaene) | Nutzer findet niederlaendische Komposita ueber ihre Glieder via `split_compound` mit wdutch/OpenTaal-Liste, lizenzklar, eigene Digest-Marke, RAM-Budget vor dem Bau gemessen | SATISFIED | Splitterkette verdrahtet und per CI (nlc-Fall) bewiesen; Lizenz in THIRD-PARTY.md; Marke `wordlist_hash_nl` verhaelt sich wie D-06 verlangt; RAM real gemessen (24,2-25,3 MB statt der urspruenglich angenommenen ~23 MB), Budget gegen 2000 MB haelt (dokumentiert in docs/performance.md, Owner kannte die Abweichung ueber den Checkpoint) |

Keine weiteren Requirement-IDs sind in REQUIREMENTS.md fuer Phase 21 vermerkt (Zeile 72: nur KOMP-01) , keine verwaisten Requirements gefunden. Anmerkung: die Status-Spalte in REQUIREMENTS.md zeigt noch "Pending"; das ist ein Tracking-Feld, keine Code-Evidenz, und liegt ausserhalb des Verifikationsscopes des Codes selbst.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `backend/src/findling/index/analyzer.py` | 402-414 | IN-04: `dutch_analyzer` greift direkt auf `FOLDED_STOPWORDS[SNOWBALL_NAME["nl"]]` zu (nackter KeyError statt benannter ValueError wie im Zwillingspfad) | Info | Heute unkritisch (Key existiert, AST-Gate haelt die Kette), im REVIEW.md als offen dokumentiert, kein Fix im Auftrag |
| `backend/src/findling/index/wordlist_nl.py` | 100-105 | IN-05: `DUTCH_CHAIN_VERSION` steht nicht neben der Kette, die es versioniert (analyzer.py); kein AST-Hash-Test erzwingt das Hochsetzen bei Kettenaenderung | Info | Dokumentiert im REVIEW.md, kein Fix im Auftrag, Kommentare auf beiden Seiten mildern das Risiko |

Beide sind laut Review-Frontmatter (`fix_status.open: [IN-04, IN-05]`) bewusst offen gelassen, ausserhalb des Fix-Auftrags, und mit Info-Schweregrad eingestuft. Sie blockieren das Phasenziel nicht: der Splitter funktioniert nachweislich (CI-Beweis), und ein spaeterer Kettenwechsel ohne Versionsanhebung ist ein Risiko fuer zukuenftige Aenderungen, nicht fuer den aktuellen Stand.

### Human Verification Required

Keine offenen Punkte. Der einzige im Plan vorgesehene Human-Checkpoint (Owner-Freigabe fuer den Push, 21-09-PLAN.md Task 3) ist bereits erledigt: SUMMARY dokumentiert "Owner-Freigabe: 'approved', 2026-09-25", und der resultierende Push samt CI-Gruenlauf wurde in dieser Verifikation unabhaengig per `gh run view` bestaetigt.

### Gaps Summary

Keine Gaps. Alle neun Observable Truths sind im Code nachweisbar, nicht nur in der SUMMARY behauptet. Die beiden offen gebliebenen Info-Befunde (IN-04, IN-05) aus dem Code-Review sind laut REVIEW.md-Frontmatter bewusst ausserhalb des Fix-Auftrags und mit dokumentierter Begruendung offen; sie sind kein Blocker fuer das Phasenziel. Die kritischen und Warning-Befunde (CR-01, WR-01, WR-02) wurden unabhaengig im Code nachgepruft und sind tatsaechlich behoben, nicht nur im REVIEW.md als "resolved" behauptet. Der lokale Testlauf (2985 passed, 15 skipped) und alle fuenf zitierten CI-Laeufe wurden in dieser Verifikation eigenstaendig reproduziert bzw. gegengeprueft.

---

_Verified: 2026-09-25T16:40:36Z_
_Verifier: Claude (gsd-verifier)_
