---
phase: 23-haertung-und-store-einreichung-1-3-0
verified: 2026-09-27T07:53:38Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
---

# Phase 23: Haertung und Store-Einreichung 1.3.0 Verification Report

**Phase Goal:** Findling 1.3.0 steht als signiertes App-Paar im Store, mit ehrlich dokumentierten Grenzen des Sprachausbaus.
**Verified:** 2026-09-27T07:53:38Z
**Status:** passed
**Re-verification:** No , initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria, Phase 23)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Aufraeumbefunde geschlossen: fastembed-Pin entfernt/Import belegt, numpy sauber deklariert, Abhaengigkeitsliste bildet den Container-Ist ab | VERIFIED | `backend/pyproject.toml:44-45` deklariert `tokenizers==0.23.2` und `numpy==2.5.2` als direkte Kanten; `grep -c fastembed backend/pyproject.toml` liefert nur Kommentarzeilen, kein Paketeintrag; `backend/uv.lock` enthaelt keinen `name = "fastembed"` (bzw. loguru/mmh3/py-rust-stemmers/requests/urllib3) Eintrag; `.github/workflows/docker.yml:236-241` fuehrt einen `find_spec`-Abwesenheitsschritt "The image carries no fastembed and no requests (HART-04)" im gebauten Abbild; `THIRD-PARTY.md:211-213` listet tokenizers/numpy/onnxruntime 1.30.0 konsistent. Kein `import fastembed` irgendwo im Baum |
| 2 | Admin liest in Doku und Store-Text, was der Sprachausbau NICHT leistet (año/ano, pt-Rechtschreibreform, Komposita nur de/nl, FR ohne Koerperfeld) | VERIFIED | Alle vier Punkte stehen identisch in `docs/store-listing.md` (EN/DE/FR, mehrfach, z.B. Zeilen 154-158, 269-273), in `backend/appinfo/info.xml` und `php/appinfo/info.xml` (Zeilen 92-95, 118-121, 145) und in `docs/language-analyzers.md` (Abschnitt "año equals ano" Zeile 446 etc.); `backend/tests/test_store_metadata.py` haelt Gates fuer "genau vier Punkte" je Sprachblock (Zeile 419-420) |
| 3 | Fremdinstallation und Upgrade 1.2.0 auf 1.3.0 inkl. Umbau-Fall Ende-zu-Ende gruen; Audit 0 CRIT / 0 HIGH, MEDIUM behoben, LOW dokumentiert entschieden | VERIFIED | `docs/audits/2026-09-phase-23/README.md` (Frontmatter `critical: 0, high: 0, medium: 1, fixed: [F-23-01,F-23-02,F-23-03]`); der MEDIUM-Fix ist im Baum nachvollziehbar: Commits `5f9ca5f` (roter Test), `0227289` (Fix in `embed/engine.py::release_if_idle`), `9304cfc`, `ea293cc`, `b544842` existieren alle im Git-Log mit exakt den im Bericht genannten Botschaften; Migrationstest `php/tests/Unit/Version001300Date20260927000000Test.php` und die Migration `php/lib/Migration/Version001300Date20260927000000.php` existieren fuer den gone-Reparaturlauf; F-23-04 (LOW) ist vom Owner explizit auf v1.4-Backlog verwiesen ("Ja, v1.4-Backlog", `deferred-items.md`), F-23-05 (LOW) vom Owner entschieden ("So lassen") , beides dokumentiert entschieden, kein offener Blocker |
| 4 | v1.3.0 eingereicht: beide Apps signiert, Submission mit 2x HTTP 201, Store-Texte gate-konform und vom Owner vor der Abgabe abgenommen | VERIFIED | Tag `v1.3.0` ist lokal UND auf dem Remote `origin` vorhanden (`git ls-remote --tags origin` zeigt `refs/tags/v1.3.0^{}` = `744d7e4662af67c728aa9482197990c414c92bd3`), identisch zum Commit, den `23-09-SUMMARY.md` und der Auditbericht Abschnitt 11 nennen; beide info.xml stehen auf `<version>1.3.0</version>`; die RAM-Messzahl 730,2 MB steht an den drei geforderten Stellen identisch; Owner-Abnahmen sind an den Checkpoints dokumentiert ("Text abgenommen" in 23-03, "Haertung abgenommen" in 23-08, "Einreichen"/"Mit Zitatzeile"/"Offen lassen" in 23-09) , konsistent zwischen PLAN-Checkpoint, SUMMARY und Auditbericht. Die externen Store-HTTP-201-Antworten selbst wurden gemaess Aufgabenstellung nicht gegen den Store nachgerufen, sind aber zwischen 23-09-SUMMARY.md und Abschnitt 11 des Auditberichts wortgleich und mit derselben Laufnummer (36304007154) belegt |

**Score:** 4/4 truths verified

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|---|---|---|---|---|
| HART-04 | 23-02, 23-08, 23-09 | fastembed-Pin geklaert, numpy sauber deklariert | SATISFIED | pyproject.toml/uv.lock/docker.yml wie oben, REQUIREMENTS.md Traceability-Zeile mit Commits `4cea879`, `40919b6` |
| HART-05 | 23-03, 23-07, 23-08, 23-09 | Grenzen des Sprachausbaus dokumentiert | SATISFIED | vier Grenzpunkte in allen Store-Texten + Doku, gehalten von `test_store_metadata.py` |
| REL-03 | 23-01, 23-03, 23-04, 23-05, 23-06, 23-07, 23-08, 23-09 | v1.3.0 eingereicht, signiertes App-Paar, E2E-Upgrade-Beweis, 2x HTTP 201 | SATISFIED | Tag v1.3.0 auf GitHub verifiziert, Audit- und SUMMARY-Belege konsistent |

Keine Waisen: alle drei Requirement-IDs aus REQUIREMENTS.md sind in mindestens einem PLAN-frontmatter referenziert (siehe Tabelle 23-01 bis 23-09 oben in der Analyse), Abdeckungszeile in REQUIREMENTS.md bestaetigt "17 von 17 v1.3-Requirements einer Phase zugeordnet, keine Waise, keine Doppelung".

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `backend/pyproject.toml` | kein fastembed, tokenizers/numpy direkt gepinnt | VERIFIED | Zeilen 44-45, Kommentar begruendet Direktkanten |
| `backend/uv.lock` | ohne fastembed/loguru/mmh3/py-rust-stemmers/requests/urllib3 | VERIFIED | keine `name = "fastembed"` Zeile |
| `.github/workflows/docker.yml` | Abwesenheitspruefung im Abbild | VERIFIED | Schritt "The image carries no fastembed and no requests (HART-04)" Zeile 236 |
| `docs/store-listing.md`, `backend/appinfo/info.xml`, `php/appinfo/info.xml` | vier Known-limitations-Punkte, 730,2 MB an drei Stellen | VERIFIED | siehe Truth 2 und 4 |
| `php/lib/Migration/Version001300Date20260927000000.php` + Test | gone-Reparaturlauf als Migration mit PHPUnit-Beweis | VERIFIED | beide Dateien existieren |
| `docs/audits/2026-09-phase-23/README.md` | Haertungsbericht mit Erfolgskriterien-Tabelle | VERIFIED | Abschnitt 7 (Erfolgskriterien) und Abschnitt 11 (Belegkette Abgabe) vorhanden, intern konsistent zu 23-09-SUMMARY.md |
| Tag `v1.3.0` | signiertes Release, auf GitHub gepusht | VERIFIED | `git ls-remote --tags origin` bestaetigt Tag auf Commit 744d7e4 |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `backend/src/findling/api/search.py` | `backend/src/findling/embed/engine.py` | `background.add_task(warm)` nach `warm_wanted()` | WIRED | `grep -c "add_task(warm)"` und `BackgroundTasks`-Import bestaetigt (Plan 23-01 Acceptance-Kriterien erfuellt, Code gelesen) |
| `backend/src/findling/api/snippets.py` | `backend/src/findling/query/rewrite.py` | `rewritten.one_term` steuert semantische Seite | WIRED | `query_may_load` in snippets.py importiert und verwendet, Einwortregel referenziert dieselben Felder wie search.py |
| `.github/workflows/docker.yml` | `ghcr.io/street1983nk/findling_backend` | `find_spec`-Pruefung im laufenden Container | WIRED | Schritt vorhanden, Kommentar verweist auf HART-04 |
| Store-Texte (6 Sprachvarianten) | `docs/language-analyzers.md` | zeichengleiche Grenzpunkte | WIRED | Wortlaut in beiden Quellen identisch geprueft (año/ano, Rechtschreibreform, Komposita, FR) |
| Tag `v1.3.0` | GitHub Remote `origin` | `git push --tags` | WIRED | Remote-Tag gefunden, Commit-Hash identisch zu lokalem Tag und zu den in SUMMARY/Audit genannten Hashes |

### Anti-Patterns Found

Keine TBD/FIXME/XXX-Marker in den 34 von dieser Phase veraenderten Nicht-Planning-Dateien (`git diff --name-only 8b060e5..HEAD`, gefiltert). Keine Platzhalter-Returns oder leere Stub-Implementierungen in den geprueften Kern-Dateien (`engine.py`, `search.py`, `snippets.py`, `pyproject.toml`).

### Human Verification Required

Keine offenen Punkte fuer menschliche Pruefung identifiziert. Zwei Punkte sind bewusst als Restrisiko vom Owner akzeptiert und nicht Teil dieser Verifikation:
- Ladefenster D-08 ist nur in CI, nicht auf Zielhardware gemessen (Owner-akzeptiertes Restrisiko, in REQUIREMENTS.md-Traceability als Vorbehalt vermerkt).
- Wie der Nextcloud-Store die Store-Texte rendert, wurde nicht nachgesehen (Owner-akzeptierter Vorbehalt, HART-05-Zeile).

Die externen Store-Antworten selbst (2x HTTP 201, GitHub-Actions-Laufnummern) wurden gemaess Aufgabenstellung nicht gegen den Store/GitHub abgerufen; die Konsistenzpruefung zwischen 23-09-SUMMARY.md und Abschnitt 11 des Auditberichts ergab keine Widersprueche (gleiche Laufnummer 36304007154, gleicher Commit, gleicher Tag).

### Gaps Summary

Keine Gaps. Alle vier Roadmap-Erfolgskriterien der Phase 23 sind im Baum verifizierbar erfuellt, alle drei Requirement-IDs (HART-04, HART-05, REL-03) sind belegt, keine Waisen in REQUIREMENTS.md. Der einzige offene technische Befund (F-23-04, LOW) ist vom Owner explizit auf das v1.4-Backlog verwiesen und damit kein Gap dieser Phase.

---

_Verified: 2026-09-27T07:53:38Z_
_Verifier: Claude (gsd-verifier)_
