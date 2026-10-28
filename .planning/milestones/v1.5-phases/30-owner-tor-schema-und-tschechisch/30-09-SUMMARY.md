---
phase: 30-owner-tor-schema-und-tschechisch
plan: 09
subsystem: audit (security, bugs, performance der Phase 30)
tags: [audit, security, cz-01, cz-02, cz-03, d-30-08, licence, performance]
requires: [30-01, 30-02, 30-03, 30-04, 30-05, 30-06, 30-07, 30-08]
provides:
  - "30-AUDIT.md: Security, Bugs, Performance, 0 CRIT / 0 HIGH / 0 MEDIUM / 3 LOW, status fixed"
  - "backend/tests/test_phase30_audit.py: 62 Grenzproben-Fälle (OCR-Allowlist, Markenpaare, halbgefülltes Ziel, Generator, Sprachnormalisierung, Feldplan Schema 2, NOTICE)"
  - "Lucene-NOTICE und Lizenzpfad im ausgelieferten Modul stopwords_cs.py (L-30-01)"
affects: [Phasen-Verifikation 30, 31 deploy-harp (L-30-03 mitnehmen)]
tech-stack:
  added: []
  patterns: ["Grenzprobe mit Positivkontrolle (Allowlist-Erweiterung, Scanner-Selbsttest)", "Trennschärfe per Mutation M1 bis M6 an src und Generator", "Gegenprobe im gebauten Image statt nur im Repo"]
key-files:
  created:
    - backend/tests/test_phase30_audit.py
    - .planning/phases/30-owner-tor-schema-und-tschechisch/30-AUDIT.md
  modified:
    - backend/src/findling/index/stopwords_cs.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "L-30-01 fix: NOTICE nach Apache-2.0 4(d) im Moduldocstring, weil das Image weder THIRD-PARTY.md noch REUSE.toml trägt"
  - "L-30-02 accept: Treffer nur über body_cs ohne Auszug ist die dokumentierte allgemeine Grenze (language-analyzers.md:504); Reparatur bräuchte Schemaschritt oder Feature"
  - "L-30-03 accept: Vektordigest ungeprüft in GITHUB_ENV; Quelle eigener Container, Job ohne Geheimnis; mitnehmen, wenn Phase 31 deploy-harp anfasst"
metrics:
  duration: "ca. 75 min (davon 10,6 min volle Suite, ca. 20 min CI)"
  completed: 2026-10-10
  tasks: 3
  files: 4
---

# Phase 30 Plan 09: Security-, Bug- und Performance-Audit Summary

Audit über den ganzen Phasen-Diff `cfe0c33a..7310f9b3` (54 Dateien, +4811/-631) mit gefahrenen Grenzproben, unabhängigen Gegenproben und Messungen: **0 CRITICAL, 0 HIGH, 0 MEDIUM, 3 LOW**; L-30-01 (Lucene-NOTICE fehlte im ausgelieferten Modul) gefixt und im neu gebauten Image belegt, L-30-02 und L-30-03 begründet akzeptiert.

## Ergebnis

**Security**
- OCR-Grenze T-03-502 mit `ces`: 12 manipulierte Werte (Pfad, `;`, `|`, `$()`, Leerzeichen, Optionen, `cze`, leere Einträge) erreichen Tesseract nie; `CES` wird bewusst zu `ces` gesenkt. Positivkontrolle: Allowlist-Erweiterung lässt `ces;id` durch. Aufruf als Argumentliste (gefälschtes `subprocess.run`), AST-Scan über 74 Paketdateien ohne `shell=`.
- Ratsche exakt `{(1,2),(2,3),(1,3)}`, sechs Gegenpaare abgelehnt; Lesetor nur `2` und `3`, sechs Sprachen bleiben auf beiden (Pflicht-Fix).
- Generator: drei neue Manipulationen (anhängen, letztes Byte, CRLF) brechen vor jeder Ausgabe ab; nicht im Paket, nirgends importiert, nicht im Image. Upstream-Datei per curl geholt: bytegleich mit der Fixture.
- deploy-harp/docker.yml: keine neue Action, Ausdrücke nur in `env:`, App-Passwort maskiert.

**Bugs**
- Kein variabler Schlüssel auf `SNOWBALL_NAME` (AST), `cs` in `BODY_FIELD`/`BODY_BOOST`/`TESSERACT_NAME`; zehn Normalisierungsfälle ohne KeyError.
- Settings `de,cs` auf Schema-2-Verzeichnis vor dem Umbau: Plan ohne `body_cs`, keine Warnung, Treffer. Gegenprobe Marke `de,cs`: `body_cs` mit einer Warnung verworfen, Suche antwortet.
- Halbgefülltes Ziel gleichen Schemas mit fremdem Sprachsatz verworfen (neuer Fall neben dem 30-05-Fall).
- Stoppliste per NFKD statt tantivy nachgerechnet: 169 gefaltet, minus 2 = die ausgelieferten 167 in gleicher Reihenfolge.

**Performance** (2026-10-10, Windows 11, 12 Kerne, tantivy 0.26.2; Korpora: 50 Artikel tschechische Wikipedia und Repo-Prosa, je 2,27 Mio. Zeichen, 1516 Dokumente à 1500 Zeichen, Produkt-Schreibpfad)
- Zuwachs durch `cs`: +0,287 (cswiki) und +0,299 (Prosa), `es` +0,294/+0,285, unter `GROWTH_PER_LANGUAGE` 0,40; drei Läufe bytegleich.
- `czech_analyzer()` 33,8 bzw. 51,7 Mio. Zeichen/s, 2,4- bis 2,8-mal die deutsche Kette; Stoppfilter kostet 1 bis 9 %.
- Suchlatenz Schema 3 ohne cs gleich Schema 2 (32 bis 35 µs, Vorzeichen wechselt), drittes Körperfeld +5 µs.
- `tesseract-ocr-ces` Installed-Size 3722 kB (im Image per `dpkg-query`).

## Mutationen (Trennschärfe, je zurückgedreht, nichts committet)

| Mutation | rote Fälle |
|---|---|
| M1 Rückwärtspaar `("3","2")` in `LEGACY_SCHEMA_STEPS` | 2 |
| M2 Lesetor wieder literal `!= "3"` | 3 |
| M3 Allowlist-Prüfung in `_ocr_languages` aus | 9 |
| M4 Feldplan aus den Settings statt aus den Marken | 5 |
| M5 Generator schreibt Ausgabe vor der SHA-Prüfung | 3 |
| M6 `_make_the_target_fit_this_code` verwirft nie | 1 |

## Commits

| Commit | Inhalt |
|---|---|
| 08ab628b | test(30-09): Grenzproben, 30-AUDIT.md Security und Bugs |
| d5b0d982 | docs(30-09): Performance-Abschnitt |
| 9e9764bf | fix(30-09): L-30-01 NOTICE im Modul, Regressionstest, Baumhash `200f270a`, LOW-Entscheidungen |

## Gates und CI

- Lokal vor 9e9764bf: ruff check, ruff format --check (198 Dateien), pyright latest 0 Fehler, vulture grün; volle Suite **4849 passed, 25 skipped** (636,9 s; vorher 4787/25, plus 62).
- CI auf 9e9764bf, alle success: Python gates **38042757203** (4860 passed, 14 skipped), HaRP deploy **38042757174** (stable33/34/35, x86 und arm; Store upgrade 5 "all eight", 6 "all ten assurances hold", 7 durch), Multi-arch image 38042757235, Integration 38042757173, Resilience 38042757189, Security scans 38042757175, OpenSSF Scorecard 38042757172.
- Gegenprobe im Artefakt: `findling_backend:dev` (erzeugt 09:50Z aus 9e9764bf) trägt die NOTICE-Zeilen; `/usr/share/common-licenses/Apache-2.0` vorhanden.

## Deviations from Plan

**1. [Commit-Schnitt] Kein roter Commit.** Projektregel "Gates grün vor jedem Commit"; RED für L-30-01 lokal gesehen (`ValueError`, NOTICE-Zeile fehlt), Fix und Test im selben Commit wie in 30-06 bis 30-08.

**2. [Messverfahren] Ein Commit je Größenmessung.** Zwischen-Commits des Writers liefen unter Windows in `os error 5` (Segmentdatei gesperrt); gemessen wird mit einem Commit am Ende, wie auch 30-05.

**3. [Verfahren] Deutsche Snowball-Kette nachgebaut.** `snowball_analyzer("german")` lehnt mangels gemessenem Supplement ab; zusätzlich die Produktkette `german_analyzer` mit Fixture-Wortliste gemessen.

**4. [Beobachtung, kein Befund] 92 ResourceWarnings** "unclosed database" in der CI-Suite, gleich zahlreich im Lauf 38039184261 vor diesem Plan, nicht aus den berührten Testdateien (lokal mit `-rw` geprüft: keine).

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche. T-30-41 bis T-30-45 umgesetzt (Tests und Bericht oben); T-30-SC: kein Paket installiert (`reuse` lokal nicht vorhanden, Ergebnis aus CI).

## Self-Check: PASSED

- Dateien vorhanden: backend/tests/test_phase30_audit.py, 30-AUDIT.md (enthält `still_open`, Abschnitte Security, Bugs, Performance)
- Commits 08ab628b, d5b0d982, 9e9764bf im Log
