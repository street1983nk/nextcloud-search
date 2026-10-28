---
phase: 31-neue-formate-und-nachholweg
plan: 04
subsystem: Extraktion (extract/mail.py, extract/text.py)
tags: [fmt-01, d-31-04, eml, mime, recursion, bidi, html]
requires:
  - phase: 31-03
    provides: "Stand f97b0134, alle Gates grün"
provides:
  - "extract_eml(path) -> ExtractionOutcome: Subject, From, To, Cc, bevorzugter Body (plain vor HTML), Anhangnamen ohne Inhalt"
  - "count_parts(raw) vor dem Parsen, MAX_MAIL_PARTS = 1000"
  - "clean_display_name(name) für 31-08 (ZIP-Mitgliedsnamen)"
  - "text.html_to_text(markup) als gemeinsame gehärtete HTML-Strecke für Datei und Mailteil"
affects: [31-08 ZIP (clean_display_name), 31-10 Freischaltung .eml über die Allowlist, 31-11 Nachholweg]
tech-stack:
  added: []
  patterns: ["Grobzählung über Rohbytes vor dem Parser als obere Schranke", "Ein try um Parser und alle rekursiven Zugriffe statt je Aufruf"]
key-files:
  created:
    - backend/src/findling/extract/mail.py
    - backend/tests/test_extract_mail.py
  modified:
    - backend/src/findling/extract/text.py
    - backend/tests/test_extract_text.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "RecursionError endet immer als failed(corrupt) mit detail 'RecursionError', auch wenn die Kopfzeilen schon gelesen sind: eine Mail mit hunderten Ebenen schreibt kein Mensch, die Statusseite soll sie benennen"
  - "Die Vorzählung kennt jede vom Parser akzeptierte Schreibweise der Boundary (boundary=, Groß/klein, boundary*=, boundary*0=, boundary*0*=, Abschnitte verbunden) und Zeilenanfänge nach einem einzelnen CR; gezählt werden nur öffnende Begrenzerzeilen"
  - "Ein kaputter Kopf (auch RecursionError im Header-Parser) wird ausgelassen, ebenso ein unlesbarer Anhangname; ein vom XML-Parser abgelehnter HTML-Teil kostet nur den Body"
  - "extract_html behält für XHTML-Dateien die Rohbytes (die Deklaration der Datei gilt); html_to_text entfernt die Deklaration und gibt UTF-8-Bytes an den Parser"
metrics:
  duration: "ca. 75 min (davon 11 min volle Suite lokal, ca. 20 min CI)"
  completed: 2026-10-11
  tasks: 2
  files: 5
---

# Phase 31 Plan 04: .eml-Extraktor (FMT-01) Summary

Ein eigener Mail-Leser im Sandbox-Pfad: Betreff, Absender, Empfänger (To, Cc) dekodiert, Textteil oder gehärteter HTML-Text, Anhänge nur mit Namen (D-31-04); Teile werden vor dem Parsen gezählt, `RecursionError` endet als benanntes Urteil. Noch nicht freigeschaltet (31-10).

## Messungen vorab (CPython 3.13.13, lokal)

- 500 / 900 verschachtelte multipart-Ebenen: Parsen 0,17 / 0,37 s, `get_body`, `iter_attachments`, `walk` ohne Fehler; 1000 und 2500 Ebenen: `RecursionError` im Parser.
- message/rfc822: 900 Ebenen gehen, 2500 werfen im Parser (Verschachtelung ganz ohne Boundary).
- 200 000 leere Teile (1,4 MB): Parsen 10,8 s.
- `boundary*=us-ascii''b`, `boundary*0="b"`, `BOUNDARY=b`: der Parser erkennt alle; die Vorzählung muss sie daher auch kennen.
- `From:` mit 5000 öffnenden Klammern: `RecursionError` beim Lesen des Kopfes.

## Task 1: html_to_text (Refactor)

- RED: 3 neue Fälle (`..._keeps_the_text_and_drops_the_script`, `..._reads_a_string_with_an_encoding_declaration`, `..._resolves_no_external_entity`); erst Sammelfehler `ImportError`, dann gegen einen Stub, der "" liefert, alle drei einzeln rot (`assert 'Rechnung' in ''`, `assert 'Grundstücksverkehrsgenehmigung' in ''`, `assert '&leak;' in ''`).
- GREEN: `html_to_text(markup: str) -> str` und `_visible_text(root)`; `extract_html` ruft für HTML `html_to_text`, für XHTML-Dateien weiterhin den XML-Parser auf den Rohbytes, beides über `_visible_text`. 28 passed, alle alten HTML-Fälle unverändert.
- Zusatzfall `test_html_to_text_ignores_an_encoding_the_string_no_longer_has` (Deklaration iso-8859-1, Text als str). Gegenprobe ohne Entfernen der Deklaration: rot (`'Kündigungsfrist' == 'K<U+FFFD>ndigungsfrist'`, Mojibake).

## Task 2: extract_eml

- RED: test_extract_mail.py mit 34 Fällen; erst Sammelfehler (Modul fehlt), dann gegen einen Stub (`skipped(empty_text)`, `count_parts` 0, `clean_display_name` Identität): **32 failed, 2 passed**, alle 32 rot am Verhalten. Grün gegen den Stub blieben `test_an_empty_mail_is_empty_text` und `test_nothing_of_the_mail_reaches_the_log`; beide sind unten per Gegenprobe belegt.
- GREEN: 34 passed (2,6 s, davon der 200 000-Teile-Fall).
- Gegenproben (jede einzeln in mail.py eingebaut, Testdatei gelaufen, zurückgebaut, Datei per `cmp` identisch):

| Probe | Eingriff | rot |
|---|---|---|
| G1 | keine Vorzählung | 9: 200 000 Teile, alle 5 Schreibweisen, Abschnitte, CR, 2500 Ebenen |
| G2 | nur `boundary=` ohne RFC 2231 | 5: drei RFC-2231-Schreibweisen, Abschnitte, 2500 Ebenen |
| G3 | Zeilenanfang nur nach LF | 1: CR-Fall |
| G4 | `except RecursionError` entfernt | 5: 1000 Ebenen, 2500 rfc822-Ebenen, get_body, iter_attachments, get_content |
| G5 | Abschlusszeilen mitgezählt | 2: genau an der Grenze, 1000 Ebenen |
| G6 | kaputter Kopf nicht ausgelassen | 1 |
| G7 | Rohmail ins Log | 1: Log-Fall |
| G8 | ohne cap_text | 1: leere Mail |
| G9 | HTML vor plain | 1: alternative |
| G10 | Anhangschleife ohne Grenze | 1: zweite Verteidigungslinie |
| G11 | unbekannter Zeichensatz nicht abgefangen | 1 |
| G12 | kaputtes HTML nicht abgefangen | 1 |
| G13 | Boundary-Abschnitte nicht verbunden | 1 |
| G14 | Bcc mitgelesen | 1 |

- Der Fall mit 200 000 Teilen läuft in der normalen Suite und damit in CI; ein Spion auf `BytesParser.parse` zählt Vollparse 0 und Kopfparse 1, Laufzeit unter 5 s.
- Akzeptanz: `grep -n "str(error)\|str(exc" mail.py` leer; `def clean_display_name` genau einmal.
- PACKAGE_TREE_HASH_TODAY `a8b438c1...bbf55`, PACKAGE_FILES_TODAY 75, Journalabsatz "Plan 31-04".

## Commits

| Commit | Inhalt |
|---|---|
| 4e08b18e | feat(31-04): read .eml files, headers, body and attachment names |

## Gates und CI

- Lokal vor 4e08b18e: ruff check grün, ruff format (203 Dateien) grün, pyright latest 0 Fehler, vulture grün, volle Suite **5055 passed, 25 skipped** (657 s).
- Push `f97b0134..4e08b18e`, alle sieben success: Python gates **38101409837** (5066 passed, 14 skipped), Integration **38101409888**, Resilience **38101409903**, HaRP deploy **38101409850**, Multi-arch image **38101409887**, Security scans 38101409898, OpenSSF Scorecard 38101410050. PHP-Gates liefen nicht (kein php/-Pfad berührt).

## Deviations from Plan

**1. [Plan-Widerspruch] 2500 multipart-Ebenen enden an der Vorzählung, nicht in RecursionError.**
Jede Ebene öffnet mit einer eigenen Begrenzerzeile, also liegen 2500 Ebenen vor dem Parsen über MAX_MAIL_PARTS; Ergebnis `indexed(truncated)` mit Betreff, kein Absturz. Der Plan verlangt Vorzählung UND für diesen Fall `failed(corrupt)`, beides zugleich geht nicht. Der RecursionError-Pfad ist mit zwei echten Fällen belegt: 1000 multipart-Ebenen (unter der Zählgrenze, über der Parser-Rekursion) und 2500 message/rfc822-Ebenen (ohne Boundary, keine Zählung sieht sie). Dazu die drei erzwungenen Fälle in get_body, iter_attachments, get_content.

**2. [Rule 2] Vorzählung kennt RFC-2231-Schreibweisen und CR-Zeilenenden.** Der Plan nennt nur `boundary=`. Gemessen akzeptiert der Parser auch `boundary*=`, `boundary*0=`, `boundary*0*=` und trennt an einem einzelnen CR; ohne das wäre die Zählung mit einer anderen Schreibweise umgehbar (G2, G3).

**3. Nur öffnende Begrenzerzeilen zählen.** Schlusszeilen öffnen keinen Teil; mit ihnen würden schon 500 Ebenen oder 999 Anhänge an der Grenze landen (G5).

**4. [Rule 1] Kaputte Kopfzeile und unlesbarer Anhangname werden ausgelassen**, auch bei `RecursionError` im Header-Parser (gemessen). Ein vom XML-Parser abgelehnter HTML-Teil kostet nur den Body.

**5. Andere Ausnahmen** laufen wie bei allen Formatmodulen bis zur Sandbox-Grenze und werden dort über `ExtractionOutcome.from_exception` übersetzt (nur Klassenname). mail.py fängt selbst nur `RecursionError` (benanntes Urteil), `LookupError`/`UnicodeDecodeError` (Zeichensatz) und `LxmlError` (HTML-Teil).

**6. Spion statt Zähler 0 auf BytesParser.parse.** `BytesHeaderParser.parse` ruft intern `BytesParser.parse(headersonly=True)`; der Test belegt deshalb "kein Vollparse, genau ein Kopfparse".

**7. Werkzeugbefund:** Das Schreibwerkzeug hat `\u`-Escapes im Quelltext in echte (unsichtbare) Bidi-Zeichen verwandelt. Vor dem Commit per Skript zurück in Escapes gesetzt; mail.py ist reines ASCII, die Tests tragen die Escapes.

## Known Stubs

Keine. extract_eml ist absichtlich noch nicht in dispatch/Allowlist eingehängt; das ist Plan 31-10.

## Threat Flags

Keine neue Fläche. T-31-09 (Vorzählung, RecursionError, Tests 200 000 Teile, 900/1000/2500 Ebenen, 1001 Anhänge), T-31-10 (html_to_text mit externer Entity), T-31-11 (clean_display_name, U+202E), T-31-12 (caplog, nur Klassenname als detail) umgesetzt und per Gegenprobe belegt.

## Requirements

FMT-01 ist als Extraktor erfüllt, aber für Nutzer noch nicht durchsuchbar: die Freischaltung kommt in 31-10. FMT-01 bleibt deshalb in REQUIREMENTS.md offen.

## Offene Punkte

- 31-10: .eml in Allowlist/Dispatch freischalten, danach FMT-01 auf Complete.
- 31-08: clean_display_name für ZIP-Mitgliedsnamen wiederverwenden.

## Self-Check: PASSED

mail.py, test_extract_mail.py und diese SUMMARY vorhanden; Commit 4e08b18e in der Historie, origin/main auf 4e08b18e; alle sieben CI-Läufe success.
