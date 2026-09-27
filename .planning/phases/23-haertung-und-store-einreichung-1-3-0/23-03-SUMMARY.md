---
phase: 23-haertung-und-store-einreichung-1-3-0
plan: 03
subsystem: docs/store-text
tags: [store-listing, known-limitations, hart-05, rel-03, owner-acceptance]
requires: []
provides:
  - "Abgenommener Store-Textentwurf 1.3.0 (sechs Texte, Umgebungsvariablen-Text, Changelog-Zeile, Issue-#14-Antwortentwurf)"
  - "Known-limitations-Kurzliste in docs/language-analyzers.md, zeichengleich zum EN-Store-Block"
affects:
  - "Plan 23-07 (wörtliche Übernahme in beide info.xml, drei READMEs, RESIDENT_FIGURE)"
  - "Plan 23-09 (Changelog-Zeile, Issue-#14-Antwort nach Owner-Wort)"
tech-stack:
  added: []
  patterns: ["Entwurf mit Owner-Checkpoint nach Vorlage 16-11"]
key-files:
  created: []
  modified:
    - docs/store-listing.md
    - docs/language-analyzers.md
    - docs/measurements/2026-09-komposita-nl/README.md
decisions:
  - "Store-Text 1.3.0 am 27.09.2026 vom Owner abgenommen: \"Text abgenommen\""
  - "F1: vierter Grenzpunkt bleibt \"French has no full text analysis chain for document text\""
  - "F2: Auszug-Grenze bleibt nur in der Doku, Store-Kurzliste bei vier D-06-Punkten"
  - "F3: \"gegen das v1.3-Abbild\" mit Messdatum 26.09.2026 reicht, keine Nachmessung am Release-Abbild"
metrics:
  completed: 2026-09-27
  tasks: 2
  files: 3
requirements: [HART-05, REL-03]
---

# Phase 23 Plan 03: Store-Textentwurf 1.3.0 Summary

Dreisprachiger Store-Textentwurf 1.3.0 mit Sprachzeile, vier Known limitations und der Messzahl 730,2 MB. Dazu der neue Text der Umgebungsvariable, die Changelog-Zeile mit Dank an budachst (#14) und die Grenzliste zeichengleich in `docs/language-analyzers.md`. Der Owner hat alles am 27.09.2026 im Wortlaut abgenommen.

## Tasks

| Task | Name | Commit |
|---|---|---|
| 1 | Entwurf 1.3.0 und Grenzliste in der Doku | 23ba896 |
| 2 | Owner-Abnahme eingearbeitet (Abnahme, F2, Datum) | 88f1f35 |

## Was entstanden ist

- `docs/store-listing.md`, Abschnitt "Entwurf v1.3.0", Teil 1 bis 7:
  - Sprachzeile (D-11) und Grenzblock (D-06)
  - Messzahl 730,2 MB mit neun Fundstellen und der Lesart "drei Stellen = drei Artefaktgruppen" (D-09)
  - die sechs Texte im Wortlaut
  - alter und neuer Text von `FINDLING_EMBED_IDLE_RELEASE_SECONDS`
  - Changelog-Zeile und Entwurf der Antwort in Issue #14 (D-05)
  - "Was bewusst nicht drin steht", "Die Abnahme" und ein Eintrag im Änderungsprotokoll
- `docs/language-analyzers.md`:
  - Unterabschnitt "Known limitations (short list, HART-05)"
  - Grenzzeile zu Französisch
  - Fußnote eingelöst
  - Ankündigung der Auszug-Grenze umgestellt (F2)
- Messbericht 21-04, Abschnitt 4.3: Quelle je Zahl genannt. 41,9 MB stammt aus der Vergleichsmessung m7g, Abschnitt 5.2. 42,1 MB stammt aus grundlast-fein, arm64 nativ.

## Die Abnahme (Owner, 27.09.2026, im Wortlaut der Auswahl)

- ABNAHME: "Text abgenommen": die sechs Texte, der Umgebungsvariablen-Text, die Changelog-Zeile und der Issue-Antwort-Entwurf sind abgenommen wie vorgelegt.
- F1: "So lassen": der vierte Grenzpunkt bleibt "French has no full text analysis chain for document text".
- F2: "Ankündigung anpassen": die Auszug-Grenze bleibt in der Doku und wird nicht für den Store-Text angekündigt. Die Store-Kurzliste bleibt bei den vier D-06-Punkten.
- F3: "Ja, reicht": die Formulierung "gegen das v1.3-Abbild" mit Datum 26.09. bleibt, keine Nachmessung am Release-Abbild.

## Verifikation

- Jeder der sechs Entwurfstexte enthält genau eine Messzahl (730.2 MB, 730,2 MB, 730,2 Mo). Die Sprachzeile steht direkt vor dem Grenzblock, der Grenzblock hat genau 4 Punkte, "año" ist enthalten. Maschinell geprüft.
- Die EN-Grenzliste steht zeichengleich in `docs/language-analyzers.md`.
- Keine Zeichen U+2013 oder U+2014 in den geänderten Dateien. Keine Platzhalter `<Datum>` mehr.
- `test_store_metadata.py`, `test_public_artifacts.py`, `test_measurement_scripts.py` und die Tests, die die geänderten Doku-Dateien lesen, sind grün.

## Deviations from Plan

- **[Owner-Auftrag F2]:** In `docs/language-analyzers.md` wurde die Ankündigung der Auszug-Grenze für den Store-Text umgestellt. Der Plan hatte das nicht vorgesehen, es kommt aus der Checkpoint-Frage F2. Commit 88f1f35.

Sonst wurde der Plan wie geschrieben ausgeführt.

## Offene Hinweise für Plan 23-07

- Der Kopfabsatz "Stand dieser Datei" in `docs/store-listing.md` beschreibt die Texte noch als Entwurf für 1.2.0. Er ist mit der Übernahme nachzuziehen.
- Der XML-Kommentar über `FINDLING_EMBED_IDLE_RELEASE_SECONDS` in `backend/appinfo/info.xml` und `docs/admin-page.md` gehören zum Plan des Kaltstart-Fixes.

## Self-Check: PASSED

- docs/store-listing.md, docs/language-analyzers.md, docs/measurements/2026-09-komposita-nl/README.md: vorhanden
- Commits 23ba896 und 88f1f35: vorhanden
