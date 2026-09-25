---
phase: 20-ui-kataloge-es-it-nl-pt
verified: 2026-09-25T12:00:00Z
status: passed
score: 9/9 must-haves verified
overrides_applied: 0
---

# Phase 20: UI-Kataloge es/it/nl/pt Verification Report

**Phase-Ziel:** Findling spricht in der Oberflaeche Spanisch, Italienisch, Niederlaendisch und
Portugiesisch (pt_PT und pt_BR) im Gleichstand mit EN/DE/FR.
**Geprueft:** 2026-09-25T12:00:00Z
**Status:** passed
**Re-Verifikation:** Nein, Erstverifikation

## Vorgehen

Codebasis direkt gepruft (nicht nur SUMMARY.md geglaubt): alle acht Katalog-Sprachcodes
(de, de_DE, fr, es, it, nl, pt_PT, pt_BR) mit eigenem, von der Umsetzung unabhaengigem
Python-Skript byteweise gegen `de.json` geprueft (Schluesselmenge, Werte, Pluralregel je
`.json`/`.js`-Paar), die vollstaendige Backend-Testsuite lokal ausgefuehrt, der
CI-Sprachbeweis-Lauf ueber `gh run view --log` einzeln nachgelesen (nicht nur der gruene Haken
des Jobs), und alle fuenf Sprachdokumente sowie `docs/l10n-catalogues.md` gegen die
Roadmap-Erfolgskriterien gelesen.

## Zielerreichung

### Beobachtbare Wahrheiten (Roadmap-Erfolgskriterien, Phase 20)

| # | Wahrheit | Status | Beleg |
|---|----------|--------|-------|
| 1 | Ein Nutzer auf es/it/nl/pt_BR/pt_PT sieht Findling vollstaendig in dieser Sprache, inklusive Fehler-/Diagnosetexte, keine englischen Reste | VERIFIED | CI-Lauf 36126493024, Job `search-parity`, Schritt "The result page answers in every new language (core lang)": alle fuenf Codes melden den uebersetzten Titel und die Abwesenheit des englischen Quellsatzes (Log einzeln nachgelesen, kein `::error::` ausgeloest). Zusaetzlich Sichtprobe in 20-09-SUMMARY.md: 5 Sprachen x Adminseite + 3 Ergebnisseiten, 0 englische Reste, Gegenprobe mit `en` liefert 37/1-3 Funde (die Suche findet also etwas, wenn es da ist) |
| 2 | Jeder neue Katalog fuehrt dieselbe Schluesselzahl wie `de.json`; Gate parametrisiert statt viermal kopiert | VERIFIED | Eigene Zaehlung: alle 8 Kataloge (de, de_DE, fr, es, it, nl, pt_PT, pt_BR) fuehren exakt 202 Schluessel, keine Differenz. `L10N_CATALOGUES`-Tupel in `test_admin_ui_contract.py` fuehrt 16 Eintraege (8 Codes x json+js), alle sechs Vollstaendigkeits-/Platzhalter-/Prozent-/Pipe-Gates laufen ueber dieses eine Tupel, kein sprachspezifischer Testname mehr |
| 3 | Pluralformen stimmen: `nplurals=3` fuer es/it/pt_BR/pt_PT, `nplurals=2` fuer nl, gelesen statt erinnert | VERIFIED | Eigene Extraktion aus den Dateien: es/it/pt_PT/pt_BR tragen `nplurals=3` (pt_PT/pt_BR mit dem `n==0\|\|n==1`-Vorderzweig), nl traegt `nplurals=2`; `pluralForm` in `.json` und die vierte Registrierungs-Zeichenkette in `.js` sind je Code zeichengleich (eigener Vergleich, 8/8) |
| 4 | pt-Ladepfad vor der Uebersetzungsarbeit verifiziert; zehn neue Dateien am richtigen Ort, keine `pt.json` | VERIFIED | `php/l10n/pt.json` existiert nicht (geprueft); alle 16 Dateien (8 Codes) liegen unter `php/l10n/`; kein separates ExApp-`l10n`-Verzeichnis im Repo; `docs/l10n-catalogues.md` Abschnitt "Der Ladepfad" (Plan 20-02) dokumentiert den Messbefund an der laufenden Instanz |
| 5 | Jeder Katalog traegt datierten Review-Vorbehalt nach FR-Muster, kein Muttersprachler-Gate blockiert | VERIFIED | `docs/l10n-spanish.md`, `-italian.md`, `-dutch.md`, `-portuguese.md` (zwei Vorbehalte fuer pt_PT und pt_BR) tragen je einen auf 25.09.2026 datierten Absatz "Dieser Katalog ist von keinem Muttersprachler gelesen worden" mit ausdruecklicher Nicht-Blockade |

**Score:** 5/5 Roadmap-Erfolgskriterien verifiziert (zusaetzlich 4 Plan-spezifische Must-haves aus den Review-Fixes, siehe unten)

### Zusaetzliche Must-haves aus dem Review (WR-01 bis WR-03)

| # | Wahrheit | Status | Beleg |
|---|----------|--------|-------|
| 6 | `.json` und `.js` jeder Sprache tragen dieselben Werte (WR-01-Fix) | VERIFIED | Eigenes Skript: alle 8 Sprachpaare `keys_match=True values_match=True plural_match=True`. Gate `test_the_two_halves_of_every_language_carry_the_same_values` mit `scan_value_equality` im Code vorhanden (Commit `cde0aab`) |
| 7 | G2 erkennt unuebersetzte Pluralwerte trotz `_::_`-Verkettung (WR-02-Fix) | VERIFIED | `scan_completeness` teilt Kompositschluessel an `_::_` (Code gelesen, Zeilen 825ff.), Commit `245f020` in der Historie |
| 8 | `python.yml` startet die Dokument-Gates bei Aenderung an `docs/l10n-*.md` (WR-03-Fix) | VERIFIED | `.github/workflows/python.yml` fuehrt `docs/l10n-*.md` in push- UND pull_request-Pfaden, Commit `69c7186` |
| 9 | Testsuite gruen nach den Review-Fixes | VERIFIED | Lokal ausgefuehrt: `2881 passed, 15 skipped` (deckt sich exakt mit der Angabe aus 20-09-SUMMARY.md/Kontext); `test_admin_ui_contract.py` allein: 54 passed |

**Gesamt-Score:** 9/9 Must-haves verifiziert

### Erforderliche Artefakte

| Artefakt | Erwartung | Status | Details |
|----------|-----------|--------|---------|
| `php/l10n/es.json`, `es.js` | Spanischer Katalog, 202 Schluessel, nplurals=3 | VERIFIED | Existiert, 202 Schluessel, Werte/Regel .json=.js |
| `php/l10n/it.json`, `it.js` | Italienischer Katalog | VERIFIED | Existiert, 202 Schluessel, nplurals=3 |
| `php/l10n/nl.json`, `nl.js` | Niederlaendischer Katalog, nplurals=2 | VERIFIED | Existiert, 202 Schluessel, nplurals=2, zwei Formen |
| `php/l10n/pt_PT.json`, `pt_PT.js` | Europ. Portugiesisch, nplurals=3, kein `pt.json` | VERIFIED | Existiert, kein `pt.json` im Baum |
| `php/l10n/pt_BR.json`, `pt_BR.js` | Brasilianisches Portugiesisch, eigene Varietaet | VERIFIED | Existiert, `PORTUGUESE_WORDINGS_THAT_MUST_DIFFER` haelt 11 benannte Unterschiede zu pt_PT (Gate im Code, Commit-Historie f79254c) |
| `backend/tests/test_admin_ui_contract.py` | Parametrisierte Gates, `L10N_CATALOGUES` mit 16 Eintraegen | VERIFIED | Code gelesen, 16-Tupel bestaetigt, alle Scanner (Vollstaendigkeit, Platzhalter, Prozent, Pipe, Pluralregel, Wertegleichheit) laufen darueber |
| `.github/workflows/integration.yml` | Sprachbeweis je Code im Job `search-parity` | VERIFIED | Schritt vorhanden, tatsaechlich ausgefuehrt und gruen (Run 36126493024) |
| `.github/workflows/python.yml` | `php/l10n/**` und `docs/l10n-*.md` in Pfadfiltern | VERIFIED | Beide Glob-Muster in push- und pull_request-Pfaden |
| `docs/l10n-catalogues.md` | Ladepfad-Beweis, Pluralregeln, Schlussabschnitt | VERIFIED | 448 Zeilen, Abschnitt "Stand nach Phase 20" mit Dateiliste, Gate-Tabelle, CI-Beweis |
| `docs/l10n-spanish.md`, `-italian.md`, `-dutch.md`, `-portuguese.md` | Wortwahl, 202 Tabellenzeilen, datierter Vorbehalt, min. 260 Zeilen | VERIFIED | 409/477/534/697 Zeilen, alle ueber dem geforderten Minimum, Vorbehalt datiert 25.09.2026 |

### Data-Flow-Trace (Stufe 4)

Nicht anwendbar im klassischen Sinn (keine Laufzeit-Datenquelle, sondern statische
Katalogdateien). Stattdessen wurde der Katalog-Ladepfad end-zu-end bewiesen: der CI-Schritt
liest den Erwartungswert zur Laufzeit aus der INSTALLIERTEN `apps/findling/l10n/<code>.json`
(nicht aus einer Kopie im Testcode) und prueft die tatsaechliche HTTP-Antwort der Ergebnisseite.
Damit ist die Kette Katalogdatei -> Nextcloud-Ladepfad -> gerenderte Seite tatsaechlich
durchlaufen und nicht nur behauptet.

### Schluessel-Link-Verifikation

| Von | Nach | Via | Status | Details |
|-----|------|-----|--------|---------|
| `test_admin_ui_contract.py` (`L10N_CATALOGUES`) | `php/l10n/*.json`/`*.js` | Tupel-Iteration ueber alle Scanner | WIRED | Code gelesen, 16 Eintraege, alle Gates iterieren darueber |
| `.github/workflows/integration.yml` (Sprachbeweis-Schritt) | `apps/findling/l10n/<code>.json` | `php -r` liest den installierten Katalog zur Laufzeit | WIRED | Tatsaechlicher CI-Lauf bestaetigt (Log gelesen, 5/5 Codes gruen) |
| `.github/workflows/python.yml` (Pfadfilter) | `docs/l10n-*.md` | Glob in push/pull_request | WIRED | Beide Listen fuehren das Muster |
| `docs/l10n-catalogues.md` (Regeltabelle) | `PLURAL_FORM_OF` in `test_admin_ui_contract.py` | `test_the_rule_table_of_the_documentation_and_the_constant_are_one_string` | WIRED | Gate im Code vorhanden, Testlauf lokal gruen |

### Verhaltens-Stichproben

| Verhalten | Kommando | Ergebnis | Status |
|-----------|----------|----------|--------|
| Alle Katalog-Gates lokal gruen | `uv run pytest tests/test_admin_ui_contract.py -q` (backend/) | `54 passed` | PASS |
| Gesamte Backend-Suite lokal gruen | `uv run pytest -q` (backend/) | `2881 passed, 15 skipped` in 240s | PASS |
| Kein `pt.json` im Baum | `ls php/l10n/pt.json` | `No such file or directory` | PASS |
| Keine Debt-Marker in Phase-Dateien | grep TBD/FIXME/XXX ueber Katalog-, Test- und CI-Dateien | keine Treffer | PASS |

### Probe-/CI-Ausfuehrung

| Probe | Kommando | Ergebnis | Status |
|-------|----------|----------|--------|
| CI-Sprachbeweis, Run 36126493024 | `gh run view 36126493024` | alle 8 Jobs gruen, inkl. `search-parity` | PASS |
| CI-Sprachbeweis, Einzel-Log | `gh run view --job=108043694820 --log \| grep "the result page answers"` | `es`, `it`, `nl`, `pt_PT`, `pt_BR` je mit korrekt uebersetztem Titel gemeldet, kein `::error::` fuer diese Zeilen ausgeloest | PASS |

### Requirements-Abdeckung

| Requirement | Quelle | Beschreibung | Status | Beleg |
|-------------|--------|---------------|--------|-------|
| KAT-01 | Plaene 20-01 bis 20-09 | UI-Kataloge im Gleichstand mit EN/DE/FR, Schluesselzahl aus `de.json` gezaehlt (202, nicht 199/174), zehn neue Dateien, `nplurals=3` korrekt, Gates parametrisiert | SATISFIED | Alle Katalogdateien vorhanden, 202 Schluessel je Datei nachgezaehlt, `L10N_CATALOGUES`-Tupel parametrisiert |
| KAT-02 | Plaene 20-02, 20-04 bis 20-09 | Uebersetzungen maschinell plus Review mit datiertem Vorbehalt, pt-Ladepfad vor Uebersetzungsarbeit verifiziert | SATISFIED | Vorbehalte in allen vier Sprachdokumenten datiert 25.09.2026, Ladepfad-Beweis in `docs/l10n-catalogues.md` (Plan 20-02, vor 20-04) |

Keine Waisen-Requirements: `.planning/REQUIREMENTS.md` Zeilen 70-71 fuehren ausschliesslich
KAT-01 und KAT-02 fuer Phase 20, beide sind in jedem Plan als `requirements:` deklariert.

### Anti-Pattern-Befunde

Keine Blocker gefunden. `20-REVIEW.md` dokumentiert drei Warnungen (WR-01 bis WR-03), alle drei
mit Commit-Hash als behoben markiert und im Code nachgewiesen (siehe Must-haves 6-8 oben). Drei
Hinweise (IN-01 bis IN-03) bleiben bewusst offen als dokumentierte, nicht blockierende
Verbesserungsvorschlaege (Fehlermeldungs-Praezision, Trap-Fehlerbehandlung, zahlbasierte statt
praesenzbasierte Vokabular-Ausnahmen) , das ist eine explizite, im Review begruendete
Entscheidung und kein uebersehener Mangel.

Keine TBD/FIXME/XXX-Marker in den von dieser Phase veraenderten Dateien.

### Menschliche Verifikation erforderlich

Keine. Beide in der Phase eingeplanten Checkpoints (`checkpoint:human-verify`, blockierend)
sind bereits waehrend der Ausfuehrung vom Owner abgenommen worden, nicht nur behauptet:

- **20-01, Task 3** (Vorher-Nachher-Sonde de/fr): Owner-Antwort "weiter" am 25.09.2026,
  dokumentiert in `20-01-SUMMARY.md` Zeile 230 ("OWNER-GO 25.09.2026").
- **20-09, Task 3** (Sichtprobe in fuenf Sprachen): Owner-Antwort "approved" am 25.09.2026,
  dokumentiert in `20-09-SUMMARY.md` mit vollstaendiger Tabelle (Adminseite, drei
  Ergebnisseiten je Sprache, Gegenprobe mit `en`).

Beide Checkpoints sind blockierende `checkpoint:human-verify`-Aufgaben und keine ans Phasenende
verschobenen `auto`-Aufgaben; die menschliche Pruefung ist damit bereits erfolgt und nicht
offen fuer diese Verifikation.

### Zusammenfassung der Lücken

Keine. Alle neun Must-haves (fuenf Roadmap-Erfolgskriterien plus vier Review-Fix-Nachweise)
sind mit unabhaengig nachgemessenen Belegen verifiziert: eigenes Python-Skript gegen die
Katalogdateien, lokaler Testlauf der gesamten Suite (2881 passed / 15 skipped, deckt sich mit
der Angabe), und der tatsaechliche CI-Lauf 36126493024 wurde Zeile fuer Zeile im Log gelesen statt
dem gruenen Haken oder der SUMMARY.md geglaubt. Phase-Ziel erreicht.

---

_Geprueft: 2026-09-25T12:00:00Z_
_Verifier: Claude (gsd-verifier)_
