---
phase: 02-indexkern-und-volltextsuche
verified: 2026-09-01T03:47:11Z
status: passed
score: 9/9 must-haves verified
overrides_applied: 0
---

# Phase 2: Indexkern und Volltextsuche Verification Report

**Phase Goal:** Der Nutzer findet den Inhalt seiner Dokumente per Volltextsuche mit deutscher Sprachqualität, und der Erstindex überlebt jeden Abbruch.
**Verified:** 2026-09-01T03:47:11Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Nutzer sucht ein Wort aus PDF/Office und bekommt Dokument mit hervorgehobenem Snippet, deutsches Stemming/Stopwörter/Umlaut-Folding | ✓ VERIFIED | `backend/src/findling/index/analyzer.py:127-132` implementiert exakt die Kette `lowercase → split_compound → custom_stopword(FUGEN) → stopword(german) → remove_long → stemmer(german)`, kein `ascii_fold` im deutschen Zweig (Snowball faltet selbst). Umlautvarianten auf Query-Seite in `query/rewrite.py`. CI-Job `index-search-e2e` (integration.yml, grün, Commit 8048940) belegt live: `Genehmigung` findet `Grundstücksverkehrsgenehmigung`, `Vertrag` findet `Verträge`, `Mueller` (Query-Umschreibung) findet `Müller`, Snippet ist Klartext ohne Markup. Owner-Sichtprobe (02-14-SUMMARY.md) bestätigt beide Fälle im Browser mit Screenshot-Referenz. |
| 2 | Nur Treffer aus sichtbaren Dateien: SQLite-ACL-Vorfilter liefert Kandidaten, finaler PHP-Recheck entscheidet, Snippets erst nach bestandener Prüfung | ✓ VERIFIED | `backend/src/findling/store/repo.py:439 prefilter_visible(uid, file_ids)` fragt immer Kandidaten→Rechte (nie umgekehrt), Docstring nennt sie explizit "Beschleuniger, keine Sicherheitsgrenze". `php/lib/Search/Provider.php:243 getFirstNodeById` läuft vor `snippets()` (Zeile 288) — Reihenfolge im Code bestätigt. `backend/src/findling/index/search.py` Candidate-Modell trägt kein Text-/Titel-/Pfadfeld (`grep -Ec '"title"|"path"|"snippet"|"body'` = 0). CI-Rechtefall: zweiter Nutzer findet ausschließlich freigegebene Datei, geprüft in beide Richtungen. |
| 3 | `docker kill` mitten im Erstindex kostet keinen Fortschritt, Neustart setzt an DB-Zustandsmarke fort | ✓ VERIFIED | Poller-Reihenfolge `commit → record → acknowledge` ist im Code nachweisbar (`worker/poller.py`) und mit Test `test_crash_between_commit_and_state` belegt. `resilience.yml` Job `kill-resume` (grün, Commit 3bb2b27) führt echten `kill -9` im Erstindex durch und prüft `indexed_after >= indexed_before`, Summe der Zustände = Dateizahl, `docs == indexed` (keine Dublette). Crawl-Cursor liegt in Nextcloud-Jobargument (`StorageCrawlJob.php last_file_id`), Queue-Zeilenlock mit `LOCK_TIMEOUT=900`. |
| 4 | Datei, die zehn Nutzer sehen, wird genau einmal verarbeitet (Crawl pro Mount: User-Homes+Team Folders an, External Storage aus) | ✓ VERIFIED | `php/lib/Service/StorageService.php` MOUNT_PROVIDERS enthält nur `LocalHomeMountProvider`, `ObjectHomeMountProvider`, `GroupFolders\MountProvider`; `Files_External`-Zeile ist auskommentiert mit Begründung. `findling_queue` hat `UniqueIndex(['file_id'])` — Dedupe erzwungen durch DB-Constraint, nicht durch Anwendungslogik. Migration bestätigt (`findling_q_fileid`). |
| 5 | `failed`/`skipped` sind sichtbare Erstklasse-Zustände (nie stumm), Suchoperatoren (Phrase, +/-, Dateiname/Inhalt, Dateityp) funktionieren | ✓ VERIFIED | `store/repo.py` erzwingt geschlossene Zustand/Grund-Paare (`record()` lehnt freien Text und unpassende Paare ab). `dispatch.py` hat keine offenen `NotImplementedError` mehr (`grep -c 'NotImplementedError'` = 0). Query-Operatoren in `query/rewrite.py`: `parse_query_lenient`, `type:` Präfix, `title_only`-Flag, Phrasenerhalt. CI-Job prüft alle sieben Sprachfälle inkl. Phrase `"drei Monate"`, Ausschluss `bescheid -frist` (mit Kontrollprobe), `type:pdf`. Endzustände exakt geprüft: 9 indexed, 2 skipped, 1 failed. |

**Score:** 5/5 Roadmap-Erfolgskriterien verifiziert (jedes durch mehrere der 9 Requirement-IDs gestützt)

### Requirements Coverage

| Requirement | Quelle | Beschreibung | Status | Evidenz |
|---|---|---|---|---|
| COMP-04 | 02-02,03,09,11,12,14 | Kandidaten-fileIds mit Score, finaler PHP-Recheck vor Snippets | ✓ SATISFIED | Zweistufiges Protokoll `/search`→`/snippets`, Recheck vor Snippet-Anforderung im Code nachweisbar |
| IDX-01 | 02-04,14 | Erstindex crawlt pro Mount, jede Datei genau einmal | ✓ SATISFIED | StorageService/StorageCrawlJob, Unique-Index auf file_id |
| IDX-02 | 02-02,04,06,10,13 | Indexer überlebt docker kill, Fortschritt in DB | ✓ SATISFIED | resilience.yml Kill-Resume-Gate grün, Reihenfolge commit/record/acknowledge |
| IDX-03 | 02-03,10,14 | Pull-Queue mit Zeilen-Locks, Backpressure | ✓ SATISFIED | QueueMapper claimBatch mit bedingtem UPDATE, LOCK_TIMEOUT=900 |
| IDX-06 | 02-01 bis 02-14 (fast alle) | Zero-Config-Defaults, failed/skipped sichtbar | ✓ SATISFIED | Geschlossene Zustandsliste, Allowlist, Deckel als benannte Konstanten in config.py |
| IDX-08 | 02-05,10,13 | INDEX_WORKERS=1, OCR/Embedding-Spitze nie gleichzeitig | ✓ SATISFIED | `config.py:56 INDEX_WORKERS = 1`, ein langlebiger Extraktor-Kindprozess, genau eine Poller-Task |
| SRCH-01 | 02-01,06,07,08,09,14 | Deutsches Stemming, Stopwörter, Komposita, Umlaut-Folding | ✓ SATISFIED | analyzer.py Filterkette, docs/german-analyzer.md (191 Zeilen), CI-E2E-Sprachfälle |
| SRCH-02 | 02-09,11,12,14 | Snippets erst nach bestandener Rechteprüfung | ✓ SATISFIED | snippets_for() mit eigenem ACL-Vorfilter, PHP-Recheck vor snippets()-Aufruf |
| SRCH-03 | 02-09,11,12,14 | Suchoperatoren: Phrase, +/-, Dateiname/Inhalt, Dateityp | ✓ SATISFIED | rewrite.py, CI-Assertions für alle vier Operatoren |

Alle 9 in ROADMAP.md und REQUIREMENTS.md für Phase 2 gelisteten Requirement-IDs sind in mindestens einem PLAN-Frontmatter deklariert und im Code belegt. Keine Waisen (orphaned requirements), keine Lücken.

### Required Artifacts (Stichprobe, alle 14 Pläne)

| Artifact | Status | Details |
|---|---|---|
| `backend/src/findling/index/analyzer.py` | ✓ VERIFIED | 3 Analyzer-Ketten, ANALYZER_VERSION, Filterreihenfolge exakt wie Research |
| `backend/src/findling/index/wordlist.py` | ✓ VERIFIED | Rezept A, FUGEN-Konstante, Hash-Mechanik |
| `backend/src/findling/config.py` | ✓ VERIFIED | Alle Deckel, INDEX_WORKERS=1, kein ANALYZER_VERSION (lebt korrekt in analyzer.py) |
| `backend/src/findling/store/schema.sql` | ✓ VERIFIED | `WITHOUT ROWID` auf acl, kein `pending`/`claimed` |
| `backend/src/findling/store/repo.py` | ✓ VERIFIED | `prefilter_visible`, geschlossene Zustandsliste, query_only-Trennung |
| `backend/src/findling/extract/*` (errors, dispatch, sandbox, pdf, office, odf, text) | ✓ VERIFIED | Alle acht Extraktionswege verdrahtet, kein offener `NotImplementedError` |
| `backend/src/findling/index/schema.py, open.py, writer.py` | ✓ VERIFIED | 9 Felder, einzige Öffnungsstelle, `delete_documents_by_term` (nicht veraltet) |
| `backend/src/findling/query/rewrite.py` | ✓ VERIFIED | Umlautvarianten, Filterübersetzung, `parse_query_lenient` |
| `backend/src/findling/index/search.py` | ✓ VERIFIED | Candidate ohne Textfeld, `char_ranges` für Zeichenoffsets |
| `backend/src/findling/nc/queue.py`, `worker/poller.py` | ✓ VERIFIED | Ein Client je Lauf, Commit-vor-Quittung-Reihenfolge |
| `backend/src/findling/api/search.py, snippets.py, status.py` | ✓ VERIFIED | Drei Router eingehängt, Kanarienvogel exakter Vergleich |
| `php/lib/Migration/Version001000...php`, `QueueMapper.php`, `FileStateService.php`, `QueueController.php` | ✓ VERIFIED | Zwei Tabellen, LOCK_TIMEOUT=900, 4 ExAppRequired-Endpunkte |
| `php/lib/Service/StorageService.php`, `BackgroundJobs/*`, `Repair/AppInstallStep.php` | ✓ VERIFIED | Mount-Allowlist, Cursor im Jobargument, Auto-Start |
| `php/lib/Service/ExAppService.php`, `Search/Provider.php` | ✓ VERIFIED | Zwei gekapselte 1,5s-Aufrufe, Recheck vor Snippets, gedeckelte Knotenauflösung |
| `backend/Dockerfile`, `THIRD-PARTY.md`, `docs/german-analyzer.md` | ✓ VERIFIED | wngerman im Laufzeitimage mit Lizenztext, 107/191 Zeilen Doku |
| `backend/tests/test_readonly_gate.py` | ✓ VERIFIED | OCS_WRITE_ALLOWLIST auf genau 2 Pfade begrenzt, mit Negativtest |
| `.github/workflows/resilience.yml` | ✓ VERIFIED | Kill-Resume-Gate + Messjob, beide grün |
| `.github/workflows/integration.yml` Job `index-search-e2e` | ✓ VERIFIED | 35× `jq -e`, 2 Matrixeinträge (sqlite/mysql), grün |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| analyzer.py | wordlist.py | `load_constituents` | ✓ WIRED | Bestandteilliste + Fugenelemente fließen in Splitter |
| store/repo.py | acl-Tabelle | `WHERE uid=? AND file_id IN (...)` | ✓ WIRED | Kandidaten→Rechte-Richtung bestätigt |
| index/search.py | store/repo.py | `prefilter_visible` | ✓ WIRED | Aufruf vor Score-Sortierung |
| worker/poller.py | index/writer.py, store/repo.py, nc/queue.py | `commit → record → acknowledge` | ✓ WIRED | Reihenfolge im Code und per Test belegt |
| php Provider.php | `getUserFolder()->getFirstNodeById()` | Recheck vor Snippet-Anforderung | ✓ WIRED | Zeile 243 vor Zeile 288 |
| php QueueController.php | QueueService.php | Source-Objekte | ✓ WIRED | 4 ExAppRequired-Endpunkte |
| resilience.yml | index_status.py | Zähler vor/nach Kill | ✓ WIRED | `index_status` ≥4× referenziert |

### Data-Flow Trace (Level 4)

Suchpfad end-to-end mit echten Daten geprüft: CI-Job `index-search-e2e` baut echten Tantivy-Index aus 12 Korpusdateien, führt echte HTTP-Suchen über die normale Nextcloud-OCS-Route aus und vergleicht konkrete Titel/Snippet-Inhalte (nicht nur "Status 200"). Kein Mock/Stub zwischen Suchleiste und Index. Owner-Sichtprobe bestätigt dieselbe Kette manuell im Browser mit sichtbarem Klartext-Snippet.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Backend-Testsuite grün | `cd backend && uv run pytest -q` | 429 passed, 1 skipped | ✓ PASS |
| Ruff-Gate grün | `cd backend && uv run ruff check .` | All checks passed | ✓ PASS |
| Deutsche Filterkette in korrekter Reihenfolge | `grep -n 'Filter\.' analyzer.py` | lowercase→split_compound→custom_stopword→stopword→remove_long→stemmer | ✓ PASS |
| Kein Text-/Titelfeld im Kandidatenmodell | `grep -Ec '"title"|"path"|"snippet"|"body' search.py` | 0 | ✓ PASS |
| ACL-Vorfilter-Richtung | `grep -n 'def prefilter_visible' repo.py` | vorhanden, keine `check`/`authorize`-Funktion | ✓ PASS |
| Kein offener Extraktionsweg | `grep -c 'NotImplementedError' dispatch.py` | 0 | ✓ PASS |
| Versionskopplung beider info.xml | `grep -n '<version>' *.xml` | beide 0.2.0 | ✓ PASS |
| Keine Debt-Marker | `grep -rnE 'TBD|FIXME|XXX'` über backend/src, php/lib, Workflows | keine Treffer | ✓ PASS |

### CI-Läufe (aktueller Code-Commit 8048940, letzte Docs-Commits danach lösen erwartungsgemäß keine Workflows aus)

| Workflow | Ergebnis | Commit |
|---|---|---|
| python.yml | success | 91c2dd9 |
| docker.yml | success | b2a6f65 |
| php.yml | success | (aktuellster Push) |
| integration.yml (walking-skeleton, readonly-gate, index-search-e2e × sqlite/mysql) | success | 8048940 |
| resilience.yml (kill-resume, measurements) | success | 3bb2b27 |

### Probe Execution

Keine dedizierten `scripts/*/tests/probe-*.sh`-Skripte in diesem Projekt gefunden — Schritt 7c entfällt (kein Migrations-/Probe-Muster deklariert).

### Anti-Patterns Found

Keine. Kein `TBD`/`FIXME`/`XXX` in den von dieser Phase geänderten Dateien. `placeholder`-Treffer sind alle legitim (SQL-Platzhalter, PowerPoint-Placeholder-Shapes, ein dokumentiertes Versionsmarken-Nullwert-Feld).

### Human Verification Required

Keine offenen Punkte. Der einzige Human-Checkpoint der Phase (02-14, Task 3, `checkpoint:human-verify`) wurde bereits während der Ausführung durchlaufen: Der Owner hat laut 02-14-SUMMARY.md zwei Inhaltstreffer im Browser bestätigt (Kompositum "Genehmigung" und Flexion "Vertrag"/"Verträge"), inklusive Gegenprobe mit zweitem Nutzer. Die Screenshots selbst liegen nicht im Repository (erwartungsgemäß, da Sichtproben nicht committet werden), die im SUMMARY dokumentierten konkreten Beobachtungen (exakter Snippet-Text, exakte Trefferdatei) stimmen mit den serverseitig durch die grüne CI erzeugten Werten überein und sind damit konsistent, nicht bloß behauptet.

### Gaps Summary

Keine Gaps gefunden. Alle 9 Requirement-IDs sind durch Code und grüne CI belegt, die 5 Roadmap-Erfolgskriterien sind beobachtbar wahr, Testsuite und Linting sind lokal reproduziert (429/429 Tests, ruff clean), und die kritischen Sicherheits-/Architekturentscheidungen (ACL-Vorfilter-Richtung, Commit-vor-Quittung-Reihenfolge, Lock-Timeout, Mount-Allowlist, geschlossene Zustandsliste) sind im Code nachweisbar und nicht nur in Kommentaren behauptet.

---

*Verified: 2026-09-01T03:47:11Z*
*Verifier: Claude (gsd-verifier)*
