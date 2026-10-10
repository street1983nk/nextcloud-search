# Phase 30: Owner-Tor, Schema und Tschechisch, Context

**Gathered:** 2026-10-10 (Owner-Tor per Rueckfrage, alle vier Empfehlungen angenommen)
**Status:** Ready for planning

## Owner-Entscheide (Tor fuer den ganzen Milestone v1.5)

- **D-30-01 Ausschlussmuster-Syntax (EXCL, Phase 33):** Einfache Platzhalter, nur `*` und `?` (fnmatch-artig, kein `**`, keine Negation, keine Regex). Beispiele `*.photoslibrary`, `*/node_modules/*`. Bestehende Praefix-Ausschluesse bleiben gueltig.
- **D-30-02 Tschechische Stoppwoerter (CZ-02):** Liste aus Lucene `CzechAnalyzer` (Apache 2.0), Lizenz- und Herkunftsbeleg im Repo ablegen (wie die anderen Wortlisten). Akzentfaltung: Stoppwortliste muss nach der Faltung passen (Supplement-Logik wie bei den anderen Sprachen in index/analyzer.py pruefen).
- **D-30-03 ZIP-Treffer (FMT-02, Phase 31):** EIN Treffer je Archiv. Das Archiv ist ein Dokument, Text aller inneren Dateien zusammen; das Snippet nennt die innere Datei. KEIN neues Schemafeld noetig.
- **D-30-04 Nachholweg (FMT-06, Phase 31):** Alle neu lesbaren Typen werden nach dem Upgrade nachgeholt: bisher als `legacy_format` uebersprungene .doc/.xls plus alle .eml/.zip/.heic, in Baendern wie die 1.4-Altbestands-Nachpruefung, ohne bestehende Treffer anzufassen.

## Folge fuer Phase 30

- Da D-30-03 kein Schemafeld braucht, ist die einzige Schema-/Markenaenderung des Milestones das tschechische Koerperfeld (CZ-02). Bestandsinstallationen ohne `cs` in FINDLING_LANGUAGES bauen NICHT um.
- tantivy hat keinen tschechischen Snowball-Stemmer: Kette = Tokenizer, Kleinschreibung, Akzentfaltung, Stoppwoerter, KEIN Stemmer. Die Allowlist-Gegenprobe (test_language_allowlist.py) vergleicht gegen die laufende tantivy-Engine; Tschechisch braucht daher einen eigenen Weg ausserhalb von SNOWBALL_NAME (nicht einfach in LANGUAGE_ALLOWLIST eintragen, sonst Panic-/ValueError-Pfad).
- `ces`-OCR: Weg wie dan/est in Plan 16-10 (eigene apt-Zeile, Bau-Pruefung, OCR_LANGUAGE_ALLOWLIST).
- Upgrade-CI-Beweis: 1.4.2 -> neu ohne Umbau bei de,en; mit cs Umbau per Re-Analyse.
- Grenze dokumentieren (CZ-03): keine Stammformreduktion.

## Quellen

- .planning/research/v1.5-recherche-2026-10-10.md
- Issue #26 (mnaiman), Antwort issuecomment-6093545909: "Czech OCR und Czech text field planned for 1.5"
