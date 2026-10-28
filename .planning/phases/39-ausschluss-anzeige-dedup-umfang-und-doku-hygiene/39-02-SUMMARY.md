---
phase: 39-ausschluss-anzeige-dedup-umfang-und-doku-hygiene
plan: 02
subsystem: docs
tags: [docs, umlaute, hygiene, DOCS-01]
requires: []
provides:
  - "docs/dev-setup.md, docs/embeddings.md, docs/install-check.md mit echten Umlauten und scharfem s in deutscher Prosa"
affects:
  - docs/dev-setup.md
  - docs/embeddings.md
  - docs/install-check.md
tech-stack:
  added: []
  patterns:
    - "Umlaut-Gate mit Schutzschichten (Fences, Spans, Link-Ziele, URLs, Pfade) und Allowlists, HEAD als Positivkontrolle"
key-files:
  created: []
  modified:
    - docs/dev-setup.md
    - docs/embeddings.md
    - docs/install-check.md
decisions:
  - "Allowlist-Vergleich per str.lower() statt casefold, weil casefold das scharfe s zu ss faltet und so Groesse/Grösse ueber ein erlaubtes Größe durchlassen wuerde"
  - "Pfade und Dateinamen in Prosa (Token mit / oder bekannter Endung) als fuenfte Schutzschicht, damit modellqualitaet-artige Pfadteile nie angefasst werden"
  - "Code-Fences bleiben unangetastet, auch der nginx-Kommentar in dev-setup.md Zeile 394 mit fuer/ueber/Domaenen (Code-Block)"
metrics:
  duration: "ca. 25 min"
  completed: 2026-10-28
  tasks: 2
  files: 3
requirements: [DOCS-01]
---

# Phase 39 Plan 02: Echte Umlaute in drei Doku-Dateien Summary

89 Wortkorrekturen in der deutschen Prosa von dev-setup.md, embeddings.md und install-check.md (ae/oe/ue zu Umlaut, ss zu scharfem s nach langem Vokal oder Diphthong, Umlaut+ss zu Umlaut+scharfem s); per Skript belegt, dass Code-Fences, Code-Spans, Link-Ziele, URLs, Pfade und die Korpusbegriffe byte-gleich zum Ausgangsstand 502f05be sind.

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | Gegenprobe-Skript und Kandidatenliste | (kein Repo-Commit, Skript ausserhalb des Repos) | `.dev/umlaut-gate/umlaut_gate.py` (gitignored) |
| 2 | Umlaute und scharfes s setzen, Gegenprobe gruen | 9c3ca5e5 | docs/dev-setup.md, docs/embeddings.md, docs/install-check.md |

Korrekturen je Datei: dev-setup.md 6, embeddings.md 42, install-check.md 41. Jede Ersetzung ist ein von Hand entschiedenes Wortpaar aus der Kandidatenliste und wurde nur in der Prosa-Schicht angewandt (Offsets der geschuetzten Teile ausgeblendet).

## Gegenprobe (Schutz)

Modus `schutz` auf `HEAD:docs/<datei>` (502f05be) gegen den Arbeitsstand und gegen den Commit 9c3ca5e5: identisch, JSON-sha256 beider Ausgaben `a783c3dfa4d31f14bbcbcb1545309db47add3f4c8abf6bb33dbdd5a3c3786ef5`.

| Datei | Fences | Spans | Link-Ziele | URLs | Pfade | Zweitwohnungsteuer | Grundsteuermessbetrag | Bahnhofstrasse | Strasse/strasse | Mueller | U+2014/U+2013 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dev-setup.md | 27 | 145 | 0 | 2 | 1 | 0 | 0 | 0 | 0/0 | 1 | 0/0 |
| embeddings.md | 7 | 179 | 17 | 0 | 4 | 0 | 0 | 0 | 0/0 | 0 | 0/0 |
| install-check.md | 14 | 375 | 2 | 0 | 0 | 2 | 2 | 0 | 0/0 | 0 | 0/0 |

Gleiche sha256 fuer jede Liste vorher und nachher, gleiche Zaehlungen, keine Gedankenstriche eingefuehrt.

## Regel-Gate

- Arbeitsstand und Commit 9c3ca5e5: `regel` mit Exit 0, 0 Treffer.
- Positivkontrolle HEAD (502f05be): Exit 1, 93 Treffer, darunter `ueber` (install-check.md 1014, 1026), `Groesse` (embeddings.md 273, 280), `ausserdem` (embeddings.md 287), `gross` (embeddings.md 630), `heisst`, `fuehrt`, `Grösse` (Umlaut vor ss), `Dateigrösse`, `Indexgrösse`.
- `fuer` steht im Ausgangsstand nur in einem Code-Block (dev-setup.md 394, nginx-Kommentar), also in keiner Prosa; zusaetzliche synthetische Kontrolle `.dev/umlaut-gate/control.md` ("Das gilt fuer alle, auch ueber die Groesse hinaus." plus `fuer` im Span): Exit 1 mit fuer, ueber, Groesse; das `fuer` im Span wird nicht gemeldet.
- Selbstpruefung der Allowlists: "Groesse" testweise in ALLOW_UE eingefuegt, Skript bricht mit `AssertionError: checker form in allowlist: Groesse` ab; danach wieder entfernt.
- `git diff --word-diff` zeigt ausschliesslich Wortwechsel mit Umlaut- oder ss/scharf-s-Bezug; `git diff --stat` nur die drei Dateien (76 Zeilen).
- `cd backend && uv run pytest tests/test_public_artifacts.py -q`: 55 passed. Zusaetzlich test_config.py und test_embed_model.py (verweisen auf embeddings.md): 266 passed, 2 skipped.

## Endgueltige Allowlists (woertlich)

```python
ALLOW_UE: list[str] = [
    "Abbauen", "aktuell", "bauen", "bequem", "constituent", "Continue", "Daemon", "Daemons",
    "Dauer", "dauerhaft", "dauern", "dauert", "does", "Erstindexdauer", "Genaueres",
    "Gesamtdauer", "goes", "guest", "Konsistenzquelle", "Neueinbettung", "neue", "neuen",
    "neuer", "neues", "Quellcode", "Quelle", "Quelltext", "query", "question", "queue",
    "request", "requests", "Sequenz", "Startsequenz", "teuerste", "value",
    "Vertrauensbeziehung", "Vertrauenskette", "Vertrauensspeicher", "zueinander", "zuerst",
]
ALLOW_SS: list[str] = [
    "abgerissene", "access", "across", "addresses", "Adresse", "Adressen", "Adressraum",
    "Adressraumgrenze", "Alltagsstack", "anfassen", "angefasst", "Anlass", "Arbeitsspeicher",
    "asserted", "asserts", "assignment", "Assistent", "Aufschlüsselung", "Aussage", "aussagt",
    "aussehen", "ausschließlich", "ausschließt", "Ausschluss", "Ausschnitt", "Basisstand", "besser", "Betriebssystem", "bewusst",
    "Bytefassung", "dass", "dasselbe", "desselben", "dessen", "Einbettungsspur", "Ergebnisses",
    "erschlossen", "Fassung", "Fassungen", "Fassungs", "Fassungsspanne", "Fassungssprung",
    "Fremdschlüssel", "gemessen", "gemessene", "gemessenen", "gerissen", "geschlossen",
    "geschlossene", "Herausschneiden", "Hilfsskripten", "hinterlassen", "Initialisierungsstand",
    "Interessant", "Kindprozess", "Klassenfehler", "lassen", "lässt", "loslassen", "message",
    "messbar", "Messbares", "Messbericht", "Messbox", "Messkorpus", "Messlauf", "Messpunkt",
    "Messrate", "Messreihen", "Messstand", "Messung", "Messwert", "missing", "misst", "Modellfassung",
    "muss", "müssen", "müsste", "müssten", "mussten", "nachgemessen", "Nachmessung", "passen",
    "passendem", "passender", "passiert", "passt", "password", "Passwort", "Passwörter", "process",
    "Prozess", "Prozesses", "Prozessgrenze", "Prozessliste", "Prozessor", "Qualitätsaussage",
    "Quantisierungsstufe", "Regressionslücke", "riss", "Schemafassung", "Schloss", "Schlüssel",
    "Schlüssels", "Serverfassungen", "SSD", "Stattdessen", "Statusseite", "Textausschnitt",
    "ungemessen", "verlassen", "Versionsfassung", "Vertrauensspeicher", "Verwaltungsseite",
    "voraussetzt", "währenddessen", "Werksstand", "Zugriffsstufe", "zulässig", "Zusammenfassung",
    "zusammengefasst",
]
```

Keine Checker-Form steht in einer der Listen (vom Skript per Assertion erzwungen). `ausschließlich` und `ausschließt` stehen in ALLOW_SS, weil sie an der Fuge aus+schl ein ss tragen; die ASCII-Form `ausschliesslich` ist dadurch nicht erlaubt (Vergleich per lower(), das scharfe s bleibt unterscheidbar).

## Restliste der Kandidaten (begruendet unveraendert)

Alle verbleibenden Woerter mit ae/oe/ue oder ss ausserhalb geschuetzter Teile stehen in den Allowlists oben: deutsche Woerter ohne Umlaut (neue, Dauer, Quelle, Sequenz, Vertrauen-Komposita, zuerst), englische Woerter der englischen Abschnitte von dev-setup.md (does, goes, queue, request, process, password, access, across), ss nach kurzem Vokal (dass, muss, Messung, Fassung, Adresse, Schlüssel, lässt) und ss an Kompositionsfugen (Alltagsstack, Betriebssystem, Statusseite, Werksstand). Geschuetzt und bewusst unberuehrt: `Mueller` (dev-setup.md, im Code-Span, Suchwort des Korpus), Zweitwohnungsteuer und Grundsteuermessbetrag (install-check.md), der nginx-Kommentar im Code-Block von dev-setup.md.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] casefold im Allowlist-Vergleich**
- **Gefunden bei:** Task 2, erster Regel-Lauf
- **Problem:** Der Plan schreibt den Vergleich "nach casefold" vor. casefold faltet das scharfe s zu ss, damit galt jedes korrigierte Wort (Größe, heißt) als ss-Wort, und ein erlaubtes "Größe" haette "Grösse" und "Groesse"-artige Faelle mit erlaubt.
- **Fix:** Vergleich und ss-Erkennung per `str.lower()`.
- **Dateien:** nur das Gate-Skript (ausserhalb des Repos).

**2. [Rule 3 - Blocking] Skriptort und Zeilenenden**
- Das Scratchpad-Verzeichnis war aus dem isolierten Worktree nicht beschreibbar; das Skript liegt deshalb im gitignorierten `.dev/umlaut-gate/` des Worktrees, weiterhin nicht im Repo.
- `core.autocrlf=true`: der Arbeitsstand traegt CRLF, die Blobs LF. Das Skript normalisiert CRLF zu LF beim Lesen, damit HEAD und Arbeitsstand vergleichbar sind (der erste Vergleich zeigte sonst Scheinunterschiede in Fences und Spans).

**3. [Rule 2 - Missing] Pfade als Schutzschicht**
- Pfade und Dateinamen in Prosa (Token mit `/` oder Endung .md/.py/.pdf/...) sind eine zusaetzliche geschuetzte Liste mit eigener sha256, wie der Plan in den must_haves fordert.

**4. Fence-Zeilen-Zahl** dev-setup.md hat 54 Fence-Zeilen (27 Bloecke, davon eingerueckte in Listen), nicht 46 wie im Planungskontext; das Skript erkennt eingerueckte Fences.

## Known Stubs

Keine.

## Self-Check: PASSED

- docs/dev-setup.md, docs/embeddings.md, docs/install-check.md: FOUND, geaendert in 9c3ca5e5
- Commit 9c3ca5e5: FOUND
