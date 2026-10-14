---
phase: 33-ausschlussmuster-und-admin-feinschliff
plan: 08
subsystem: docs, changelog, store-draft
tags: [docs, exclusions, patterns, reconcile, d-33-01, changelog, store-draft, rel-05]
requires:
  - "33-02: Syntax, Normalisierung, elf Codes, Grenzen 32/60, Matcher"
  - "33-03: Weg C im Abgleich (D-33-01)"
  - "33-04: Kehrjob Weg A, forgetVerdicts in allen Räumwegen"
  - "33-05 bis 33-07: Musterliste, Grenzblock, Hardware-Hinweis, Kataloge"
provides:
  - "docs/admin-page.md: Abschnitt Ausschlussmuster (Syntax mit Beispiel und Gegenbeispiel, Pfadraum, Groß/Klein mit A1, NFC, Mac-Bundles, Grenzen, Tabelle der elf Codes, Weg A und Weg C mit Verzögerung, Rückweg, Verhältnis zur Ordnerliste, Protokoll)"
  - "docs/reconcile.md: Abschnitt Dateien unter einer Ausschlussregel (D-33-01) mit beiden Owner-Entscheiden"
  - "CHANGELOG Unreleased: zwei Added- und zwei Changed-Zeilen (#21, #22)"
  - "docs/store-listing.md: Entwurf v1.5.0 (Teil Phase 33), Teil 1 bis 3, Owner-Abnahme offen (REL-05)"
affects: [33-09, 33-10, 33-11, 36]
tech-stack:
  added: []
  patterns: []
key-files:
  created: []
  modified:
    - docs/admin-page.md
    - docs/reconcile.md
    - docs/store-listing.md
    - CHANGELOG.md
decisions:
  - "33-08: Der Store-Entwurf schlägt eine neue Zeile der Funktionsliste vor statt die Zeile Ausschlüsse/exclusions zu ändern: README.md:27, README.en.md:27, README.fr.md:28 meinen die Suchsyntax, die sechs Beschreibungen nennen Ausschlussregeln gar nicht"
  - "33-08: Empfehlung an den Owner (Teil 3): Grenzblock und Hardware-Hinweis ohne eigene Store-Zeile (Kurztext-Regel)"
requirements-completed: []
metrics:
  duration: "ca. 25 min inkl. Volltestlauf (14:11 min) und CI"
  completed: 2026-10-14
  tasks: 2
  files: 4
---

# Phase 33 Plan 08: Doku, CHANGELOG und Store-Entwurf Teil Phase 33 Summary

docs/admin-page.md erklärt die Ausschlussmuster vollständig (Syntax, Pfadraum, Groß/Klein samt zweiter Regel `*.KEY`, NFC, Mac-Bundles, Grenzen 32 und 60, alle elf Ablehnungscodes, Weg A in der nächsten Cron-Runde und Weg C spätestens beim nächsten Abgleich); docs/reconcile.md beschreibt D-33-01 mit beiden Owner-Entscheiden; der CHANGELOG nennt die Phase mit #21 und #22; der Store- und README-Text liegt als Entwurf "Teil Phase 33" für REL-05 bereit, info.xml und READMEs unberührt.

EXCL-01 bis EXCL-03 und POL-01 bleiben laut Phasenplan offen bis 33-11 (Live-Beleg in 33-09, Abnahme in 33-10).

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | Musterabschnitt in admin-page.md und D-33-01 in reconcile.md | 57739fe8 | docs/admin-page.md, docs/reconcile.md |
| 2 | CHANGELOG und Store-Entwurf Teil Phase 33, Gates, Commit und CI | 57739fe8 | CHANGELOG.md, docs/store-listing.md |

Task 1 und 2 laufen laut Plan in einem Commit.

## Umsetzung

**docs/admin-page.md**

- Neuer Abschnitt "## Ausschlussmuster" zwischen "Der Pfadraum der Ausschlüsse" und "Was beim Hinzufügen und beim Entfernen eines Ausschlusses passiert", mit Unterabschnitten Syntax, Pfadraum, Groß geschriebene Endungen, Typische Mac-Bundles, Grenzen, Abgelehnte Eingaben, Was beim Speichern passiert, Ein Muster entfernen, Muster oder Ordner?, Was im Protokoll steht.
- Syntaxtabelle mit Beispiel und Gegenbeispiel: `*.photoslibrary`, `*/node_modules/*` (oben und tief), `Scan_??.pdf` (`?` nie `/`), `Backups/*` (verankert). Regeln: Vorfahre oder Datei selbst, Vergleich auch mit `/` davor, Groß/Klein zählt, NFC (`Caf?` trifft `Café`); Vereinheitlichung beim Speichern (Leerraum, doppelte und äußere `/`, führendes `files/`), erlaubte Zeichen `( ) + $ ^ .`.
- A1: `*.key` trifft `Vortrag.KEY` nicht, zweite Regel `*.KEY` anlegen; Prüfung über die Diagnose der Einzeldatei.
- Mac-Bundles: `*.photoslibrary`, `*.app`, `*.bundle`, `*.key`, `*.pages`, `*.numbers`, `*.fcpbundle`.
- Grenzen: Ordner 64 zu 256 Byte unverändert, Muster 32 zu 60 Zeichen (D-33-03, Messung 33-02: rund 6 ms je Aufruf im schlimmsten Fall).
- Tabelle aller elf Codes mit Liste (beide oder nur Muster) und Grund; Lesen einer per `occ` gesetzten Liste (unbrauchbare Einträge gelten nicht, Grenze 32, Protokoll nur Zahl).
- Wirkung: zahlenlose Bestätigung; neue Dateien nicht eingereiht; Weg A (Kehrjob ab der nächsten Cron-Runde, 1000 Dateien oder 30 s je Lauf, Neustart bei Änderung der Liste); Weg C (nächster Abgleichzyklus, Takt aus `FINDLING_RECONCILE_MIN_INTERVAL_HOURS`, `FINDLING_RECONCILE_HOUR`, `FINDLING_RECONCILE_QUIET_MAX`, auch für Präfixe); alte Einträge der Fehlerliste verschwinden mit (B2, G4); Kopfzahl nach der nächsten Nachzählung, Diagnose "Durch Regel ausgeschlossen" sofort.
- Rückweg: Muster entfernen, laufender Kehrjob endet, Dateien über den Abgleich oder `occ findling:index --restart` zurück.
- Bestand nachgezogen: Bedingung 5 des Nenners, Diagnose-Stufe 2 und die Tabelle "Die vier Schalter" nennen Präfix und Muster; der Pfadraum-Abschnitt verweist auf die zweite Liste.

**docs/reconcile.md**

- Neuer Abschnitt "## Dateien unter einer Ausschlussregel (D-33-01)" hinter "Die verlorene Übergabe an die OCR-Spur", Verweis darauf in Schritt 5 von "Wie er arbeitet".
- Inhalt: Marke `skipped(excluded)` live von der PHP-Seite; bekannte Datei unter der Marke wird Arbeit vor dem ETag-Vergleich; `describe()` macht den Löschauftrag; Grabstein; danach unbekannt plus Marke, liegen gelassen. Urteilszeilen weg (describe und Slice). Owner-Entscheid 03.10.2026 Teil a und seine Erweiterung vom 13.10.2026; Netzfälle (occ, neuer Mount, Umbenennen); keine Schleife (Mitgliedschaft, Bänder zu 200, Ruhe-Gate); Rückweg.

**CHANGELOG.md** (Unreleased): Added "Exclusion patterns ..." (#22) und "The admin page shows the limits per file read only ..." (#21); neuer Block Changed mit "Files under a rule leave the index at the next reconcile ..." (#22) und "The hint about too little hardware for a profile is reworded in all languages."

**docs/store-listing.md**: "# Entwurf v1.5.0 (Teil Phase 33)" hinter Teil Phase 32, Kopf wie dort. Teil 1 eine neue Zeile der Funktionsliste in en/de/fr ohne Zahl, Grenzen nur als Verweis auf docs/admin-page.md; Teil 2 dieselbe Zeile in den drei READMEs; Teil 3 Empfehlung "keine Store-Zeile" für Grenzblock und Hardware-Satz, dazu Verweis auf den zurückgestellten Fund "half of the box" aus deferred-items.md.

## Belege

- **Gegenprobe der Doku-Beispiele gegen den echten Matcher** (unabhängig vom Text, über `backend/tests/drivers/exclusion_driver.php` auf php:8.3-cli, Quelle `php/lib/Service/ExclusionService.php`): 14 Pfade, Antworten genau wie dokumentiert (`Fotos/Mediathek.photoslibrary/...` ja, `Notiz.photoslibrary.txt` nein, `node_modules/...` oben ja, tief ja, `node_modules_alt` nein, `Scan_01.pdf` ja, `Scan_1.pdf` nein, `Scan_0/.pdf` nein, `Backups/2024/x.pdf` ja, `Alt/Backups/x.pdf` nein, `Vortrag.key` ja, `Vortrag.KEY` nein, `Vortrag.key/Data/x.jpg` ja, `Café/x.txt` über `Caf?/*` ja).
- Task-1-Prüfung: `photoslibrary` in admin-page.md, `D-33-01` in reconcile.md, keine U+2013/U+2014; je Code genau eine Tabellenzeile (11 von 11).
- Vokabel- und Store-Gates gegen den Entwurf: `tests/test_public_artifacts.py tests/test_store_metadata.py tests/test_admin_ui_contract.py` 333 passed, kein Fund, nichts umformuliert.
- **Gates lokal (backend/, PYTHONUTF8=1):** pytest **5680 passed, 159 skipped** (14:11 min); ruff check grün; ruff format --check 222 Dateien; pyright 0 errors (latest); vulture leer; reuse lint 2728/2728. Striche über die vier Dateien: keine.
- Kein PHP, kein `backend/src`, keine info.xml und keine README geändert (`git diff --quiet HEAD -- php backend/src backend/appinfo/info.xml README.md README.en.md README.fr.md`); PHPL-Block leer, kein Baumhash bewegt.

## CI (57739fe8)

Alle mit `gh run watch <id> --exit-status` bis zum Ende beobachtet, beide grün:

- Security scans 38533252248
- OpenSSF Scorecard 38533252271

Nur Doku geändert, deshalb keine Python-, PHP-, Resilience-, Integration-, HaRP- oder Image-Läufe (Pfadfilter), wie bei 33-01. Erste Liste leer, zweiter Aufruf mit 2 Läufen, dritter Aufruf gleich.

## Deviations from Plan

### Auto-fixed Issues

**1. [Regel 1 - Bug] README-Zeile "Ausschlüsse/exclusions" meint die Suchsyntax**
- **Gefunden in:** Task 2
- **Problem:** Plan und Interfaces nehmen an, README.md:27, README.en.md:27 und README.fr.md:28 seien die Ausschluss-Zeile, die geändert werden könnte ("z. B. Ausschlüsse nach Ordner oder Muster"). Die Zeilen stehen aber unter "Volltextsuche mit deutscher Wortbehandlung: ... Phrasen, Ausschlüsse, Dateityp-Filter" und meinen den Ausschluss eines Worts in der Anfrage. Die sechs Store-Beschreibungen nennen Ausschlussregeln gar nicht.
- **Fix:** Der Entwurf schlägt eine neue Zeile vor und hält ausdrücklich fest, dass die drei Suchsyntax-Zeilen unverändert bleiben.
- **Dateien:** docs/store-listing.md
- **Commit:** 57739fe8

**2. [Regel 1 - Bug] Bestandsdoku nannte nur Präfixe**
- **Gefunden in:** Task 1
- **Problem:** Nenner-Bedingung 5, Diagnose-Stufe 2, die Tabelle "Die vier Schalter" und der Einstieg von "Der Pfadraum der Ausschlüsse" ("ohne Muster und ohne Platzhalter") beschrieben nur Präfixe; seit 33-02 prüfen Crawl und Diagnose beide Listen.
- **Fix:** Die vier Stellen nennen Präfix und Muster; die Tabelle trägt beide Grenzen und schreibt 256 Byte statt 256 Zeichen.
- **Commit:** 57739fe8

### Weitere Abweichungen

1. **reconcile.md hatte keinen Ausschlussabschnitt zum Umschreiben**: neu angelegt, mit Verweis aus Schritt 5.
2. **Owner-Kürzel in der Doku ausgeschrieben**: G1 bis G4 stehen in der öffentlichen Doku als "Owner-Entscheid vom 13.10.2026", weil die Kürzel nur in den Planungsdateien erklärt sind.
3. **CHANGELOG mit Grenzzahl und Doku-Verweis** in der Musterzeile ("At most 32 patterns of 60 characters (docs/admin-page.md)"), sonst Wortlaut des Plans.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche. T-33-25: nur Entwurf in docs/store-listing.md, info.xml und READMEs per `git diff --quiet` unverändert, Abnahme bei REL-05. T-33-26: beide Räumwege mit Verzögerung beschrieben, abgeglichen mit 33-03- und 33-04-SUMMARY und mit dem Treiber gegengeprüft; Live-Beleg folgt in 33-09.

## Self-Check: PASSED

- FOUND: docs/admin-page.md (`*.photoslibrary`, 11 Codezeilen), docs/reconcile.md (`D-33-01`), docs/store-listing.md (`Entwurf v1.5.0 (Teil Phase 33)`, `admin-page.md`), CHANGELOG.md (#21, #22)
- FOUND: 57739fe8
