---
phase: 31-neue-formate-und-nachholweg
plan: 15
subsystem: Audit der Phase 31 (Extraktion mail/archive/legacy_doc, Worker reconcile/recheck/catchup, Spiegelskript, deploy-harp)
tags: [audit, security, performance, fmt-01, fmt-02, fmt-03, fmt-06, pol-02, h-31-01, h-31-02, m-31-01, m-31-02]
requires:
  - phase: 31-01 bis 31-14
    provides: "die fünf Formate, der Nachholweg recheck_1_5_0, die Upgrade-Strecke, docs/formats.md"
provides:
  - "31-AUDIT.md: 0 CRITICAL, 2 HIGH, 2 MEDIUM, 10 LOW; alle HIGH/MEDIUM gefixt, LOW entschieden; status fixed"
  - "backend/tests/test_phase31_audit.py: bösartiger Formatkorpus (ZIP, Mail, Word, Excel, HEIC) durch das Sandbox-Kind, Log-Probe, Nachholweg-Proben, Wire-Raster, Spiegelcheck, Importprobe, Gate gegen zeilenweise Musterprüfungen"
  - "mail.py: Kopfzeilen auf 32 KiB gekürzt, 1 MiB Parser-Budget je Mail, danach nur Kopfzeilen (indexed(truncated))"
  - "archive.py: Overlap-Warnung von zipfile verworfen, OSError eines Mitglieds macht es zum Namen"
  - "legacy_doc.py: Word 6/95 (wIdent 0xA5DC) skipped(unsupported_variant)"
  - "reconcile.py: gewöhnliche Runde lässt Abgeschriebene ohne Zeile liegen, solange der Nachholweg offen ist"
  - "recheck.py: resume_after (ASCII-Ziffern bis 2^63-1), von catchup.py mitbenutzt"
  - "corresponding_source.py: fremde Einträge und Pfade mit ../ abgelehnt; deploy-harp: [[ =~ ]] statt printf | grep"
affects: [32 bis 36, insbesondere 36 Launch-Korpus und Upgrade-Matrix]
tech-stack:
  added: []
  patterns:
    - "EmailPolicy-Unterklasse mit Budgetobjekt: header_fetch_parse ist die eine Stelle, an der das email-Paket Kopfzeilen parst"
    - "Korpus als Tabellen name -> (Bauer, Urteil, Wort, Befund), jede Datei durch ExtractionWorker, Positivkontrolle für den Kind-stderr"
    - "Gegenproben-Skript: eine Ersetzung, Testauswahl, Rückkopie mit filecmp"
key-files:
  created:
    - backend/tests/test_phase31_audit.py
    - .planning/phases/31-neue-formate-und-nachholweg/31-AUDIT.md
    - .planning/phases/31-neue-formate-und-nachholweg/deferred-items.md
  modified:
    - backend/src/findling/extract/mail.py
    - backend/src/findling/extract/archive.py
    - backend/src/findling/extract/legacy_doc.py
    - backend/src/findling/worker/reconcile.py
    - backend/src/findling/worker/recheck.py
    - backend/src/findling/worker/catchup.py
    - backend/tests/test_measurement_scripts.py
    - backend/tests/test_upgrade_seed_steps.py
    - scripts/release/corresponding_source.py
    - .github/workflows/deploy-harp.yml
    - docs/formats.md
    - docs/reconcile.md
    - .planning/REQUIREMENTS.md
decisions:
  - "H-31-01 als HIGH eingestuft wie H1 des Sicherheitsaudits (RTF): 1,2 MB Mail hielt den einzigen Indexer 120 s fest"
  - "Kopfzeilengrenze 32 KiB je Wert und 1 MiB je Mail, gemessen: echte Mail mit 999 Anhängen braucht 316 278 Zeichen"
  - "H-31-02: Overlap-Warnung verwerfen statt archive_limit, weil das Lesebudget die Wiederholungen ohnehin zählt"
  - "M-31-01: solange der Nachholweg offen ist, weder Aufgeben noch Übergeben in einer gewöhnlichen Runde; nur der Nachholzyklus übergibt, einmal"
  - "L-31-01 auch in recheck.py gefixt (Teil A wartet auf den Re-Check); embedding.py vor Phase 31, in deferred-items.md"
  - "LOW accept: L-31-04, -05, -06, -08, -09, -10 mit Zielphase 36 oder nach v1.5"
metrics:
  duration: "ca. 250 min, davon ca. 75 min volle Testläufe und ca. 60 min CI"
  completed: 2026-10-12
  tasks: 3
  files: 16
---

# Phase 31 Plan 15: Security-, Bug- und Performance-Audit Summary

Ein zur Testlaufzeit gebauter Korpus aus 15 ZIP-, 15 Mail-, 17 Word-, 8 Excel- und 8 HEIC-Fällen lief durch das echte Sandbox-Kind und fand zwei HIGH (Mail-Kopfzeilen hielten den Indexer bis zur Frist, ein ZIP-Mitgliedsname im Log), zwei MEDIUM (Nachholweg-Ausnahme in der falschen Runde, Word 6/95 als beschädigt) und zehn LOW. Alle HIGH und MEDIUM sind gefixt und durch rot gesehene Tests belegt, vier LOW gefixt, sechs LOW mit Grund akzeptiert; CI auf 53fae392 grün, HaRP deploy 38292944828 über Store upgrade 0 bis 7.

## Befunde und Fixes

| ID | Befund | Fix | Commit |
|---|---|---|---|
| H-31-01 | To mit 100 000 Adressen (1,2 MB) und Content-Type 1 MB: `failed(timeout)` nach 120 s; 900 Teile x 8 KiB: 96,6 s | Richtlinie mit Kürzung auf 32 KiB und 1 MiB Budget; danach 0,18 s, 0,99 s, 2,66 s | 013d1c58 |
| H-31-02 | `UserWarning: Overlapped entries: '<Name>'` im Kind-stderr | Warnung um `archive.open` verworfen | 013d1c58 |
| M-31-01 | Datei bekam zwei Chancen bzw. keine, wenn Teil A mitten in einer Runde endet oder steht | Zweig `held` in `_compare`, Rundenflag aus `run_once` | 97891f3a |
| M-31-02 | echte Word-6-Datei `failed(corrupt)` | wIdent 0xA5DC zugelassen, `unsupported_variant` | 013d1c58 |
| L-31-01 | Cursor 2^64, hochgestellte oder arabische Ziffern hielten Teil A und den Re-Check an | `resume_after` | 97891f3a |
| L-31-02 | negatives Mitglied machte die ganze ZIP-Datei `corrupt` | `OSError` um `archive.open` | 013d1c58 |
| L-31-03 | `--verify-only` grün mit fremdem Archiv und mit `../` | fremde Einträge und Pfade abgelehnt | 004dc865 |
| L-31-07 | sieben `printf | grep -Eq`-Prüfungen zeilenweise | `[[ =~ ]]`, Gate verschärft | 004dc865 |
| L-31-04, -05, -06, -08, -09, -10 | siehe 31-AUDIT.md | accept mit Grund | |

## TDD

- Task 1 (02e11bf1): Korpus gegen den Stand vor den Fixes **74 passed, 16 xfailed**, danach mit Word 6 und Generationsfall 18 xfailed; Suite 5557 passed, 30 skipped, 18 xfailed. Jeder rote Fall als `xfail(strict=True, reason=<ID>)` markiert, rot gesehen auch per `--runxfail` (z. B. `assert ['ueberlappgeheim'] == []`, `findling.extract.legacy_doc.CorruptDocument`, `OverflowError`, `[] == [7]`).
- Task 3: je Fix die Markierung entfernt und grün; der Re-Check-Fall von L-31-01 zuerst rot gesehen (`OverflowError`, `ValueError`, `assert [] == [7]`), dann gefixt. Am Ende kein `xfail(strict=True` mehr in der Datei.
- Gegenproben: G1 bis G14 (Grenzen, die schon hielten) und F1 bis F8 (Fixes zurückgenommen), jede rot, jede Datei per `filecmp` gleich zurück. G4 und G15 waren nicht trennscharf und sind durch G4c und den Detail-Check ersetzt (53fae392); F5 durch F5b.

## Performance (Kurzfassung, Einzelheiten in 31-AUDIT.md)

- Formate über das Kind: .eml 0,043 s, .doc 0,394 s, .xls 0,415 s kalt; ZIP mit 50 Mitgliedern 1,01 s, +120 MiB.
- Große ZIP-Datei an der Mitgliedergrenze: 1000 DOCX in 21,6 s `indexed(truncated)`, weit vor der Frist.
- Snippet-Mehrkosten durch die Mitgliedsnamen: -1,2 bis +3,3 % (Grenze 20 %), auch bei 450 000 Zeichen (T-31-30).
- Nachholweg auf 200 000 Zeilen: Teil A 0,25 s Rechenzeit; Abgleich je Seite dauerhaft +4,3 %, im Nachholzyklus bis +15,5 % (L-31-10, accept); Nachholdauer der CI (303 s) ist der 300-s-Takt, große Instanzen zahlen dazu die Extraktion der nachgeholten Dateien und rund 7 bis 10 Minuten Metadaten.
- Suchprozess: -0,2 MiB gegen den Stand vor Phase 31. Image +2 Prozent, HEIC-RAM im Budget.

## Gates und CI

- Lokal vor 02e11bf1: 5557 passed, 30 skipped, 18 xfailed; vor 013d1c58: 5568 passed, 30 skipped, 8 xfailed; vor 97891f3a: 5576 passed, 30 skipped, 3 xfailed; vor 004dc865 und 53fae392: 5579 passed, 30 skipped. Jedes Mal ruff check (backend und ../scripts), ruff format --check, pyright latest 0 Fehler, vulture grün.
- Baumhash: 71a4df12...a5bd (013d1c58), c5498922...09db (97891f3a), Journal "Plan 31-15, Befund ...", 79 Dateien; PHP unverändert.
- Push `2b5e4426..53fae392`, alle per `gh run watch` abgewartet, alle success: Python gates **38292944805** (5591 passed, 18 skipped, Korpus unter Linux mit RLIMIT_AS), HaRP deploy **38292944828** (vier Jobs, Store upgrade 0 bis 7, "all ten assurances hold", recheck_1_5_0 done nach 302 s), Integration **38292944794**, Resilience **38292944962**, Multi-arch image **38292944825**, Security scans **38292944814**, OpenSSF Scorecard **38292944843**. PHP gates liefen nicht (php/ unberührt).

## Commits

| Commit | Inhalt |
|---|---|
| 02e11bf1 | test(31-15): malicious format corpus through the sandbox child and audit report |
| 013d1c58 | fix(31-15): bounded mail headers, no member name in the log, Word 6 and 95 named |
| 97891f3a | fix(31-15): every written off file gets its one chance, a manipulated cursor restarts at zero |
| 004dc865 | fix(31-15): the mirror check refuses foreign files and paths, pattern checks hold the whole value |
| 53fae392 | test(31-15): four Word cases hold the reader's own CorruptDocument as the detail |

## Deviations from Plan

**1. [Rule 2] L-31-01 auch im Re-Check von 1.4 gefixt.** `recheck.py` ist Prüfgegenstand und Teil A wartet auf ihn; dieselbe Funktion `resume_after` dient beiden. `embedding.py` hat dasselbe Muster, liegt aber vor Phase 31 und steht in `deferred-items.md`.

**2. [Rule 1] Ein Korpusfall änderte sein erwartetes Urteil.** Content-Type mit 10 000 Parametern (89 KB) war vor dem Fix `indexed`, jetzt `indexed(truncated)`, weil die Kopfzeile über 32 KiB gekürzt wird; der Text bleibt vollständig. Dokumentiert im Test und in docs/formats.md.

**3. Gate verschärft statt gelockert.** `test_upgrade_seed_steps.py::_checked_before` nimmt nach L-31-07 nur noch `[[ =~ ]]` an; die gepinnten Formen in drei Gate-Fällen folgen dem Workflow.

**4. DIFAT-Zyklus nur in kleiner Form.** Ein echter Zyklus braucht mehr als 109 FAT-Sektoren (Datei ab rund 7 MB, gegen die Vorgabe kleiner Korpusdateien); die kleine Form endet an `check_fat_size` bzw. olefile. Großer Fall als L-31-09 in Phase 36.

**5. Tiefen- und Hilfsbilder bei HEIC.** pillow-heif 1.8 schreibt keine Tiefen- oder Hilfsbilder; geprüft sind die Registrierungsoptionen im eigenen Prozess und eine HEIC mit Vorschaubild.

**6. Echte Bestandsdateien.** Für FAT-Schranke und ENDOFCHAIN liefen 32 echte Altformat-Dateien dieses Rechners durch die Prüfungen, ohne Namen auszugeben; daraus stammt M-31-02.

**7. docs/formats.md und docs/reconcile.md ergänzt** (Kopfzeilengrenze, Regel von M-31-01). Store-Texte und READMEs unberührt (REL-05).

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche. T-31-47 (Korpus durch den echten Sandbox-Pfad, Urteil, Laufzeit, lebender Worker), T-31-48 (caplog und Kind-stderr mit Positivkontrolle; H-31-02 gefixt), T-31-49 (`../`, NUL, Bidi, Überlänge in ZIP und Mail; nichts unter einem Mitgliedsnamen geschrieben), T-31-50 (jede Prüfung mit Befehl und Ergebnis in 31-AUDIT.md) umgesetzt.

## Owner-Fragen

Keine aus diesem Plan: kein Fix berührt Schema, Indexmarke oder Analysekette (D-30-08). Offen bleiben die bekannten Punkte (REL-05, A8-Veto aus 31-03).

## Self-Check: PASSED

31-AUDIT.md (`still_open: [L-31-04, L-31-05, L-31-06, L-31-08, L-31-09, L-31-10]`, sieben `## `-Abschnitte, Performance-Tabelle mit Medianen), test_phase31_audit.py (kein `xfail(strict=True`), deferred-items.md und diese SUMMARY vorhanden; 02e11bf1, 013d1c58, 97891f3a, 004dc865, 53fae392 auf origin/main; alle sieben CI-Läufe auf 53fae392 success.
