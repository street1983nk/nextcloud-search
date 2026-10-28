# Phase 30: Owner-Tor, Schema und Tschechisch, Context

**Gathered:** 2026-10-10 (Owner-Tor per Rueckfrage, alle vier Empfehlungen angenommen)
**Status:** Ready for planning

## Owner-Entscheide (Tor fuer den ganzen Milestone v1.5)

- **D-30-01 Ausschlussmuster-Syntax (EXCL, Phase 33):** Einfache Platzhalter, nur `*` und `?` (fnmatch-artig, kein `**`, keine Negation, keine Regex). Beispiele `*.photoslibrary`, `*/node_modules/*`. Bestehende Praefix-Ausschluesse bleiben gueltig.
- **D-30-02 Tschechische Stoppwoerter (CZ-02):** Liste aus Lucene `CzechAnalyzer` (Apache 2.0), Lizenz- und Herkunftsbeleg im Repo ablegen (wie die anderen Wortlisten). Akzentfaltung: Stoppwortliste muss nach der Faltung passen (Supplement-Logik wie bei den anderen Sprachen in index/analyzer.py pruefen).
- **D-30-03 ZIP-Treffer (FMT-02, Phase 31):** EIN Treffer je Archiv. Das Archiv ist ein Dokument, Text aller inneren Dateien zusammen; das Snippet nennt die innere Datei. KEIN neues Schemafeld noetig.
- **D-30-04 Nachholweg (FMT-06, Phase 31):** Alle neu lesbaren Typen werden nach dem Upgrade nachgeholt: bisher als `legacy_format` uebersprungene .doc/.xls plus alle .eml/.zip/.heic, in Baendern wie die 1.4-Altbestands-Nachpruefung, ohne bestehende Treffer anzufassen.

## Nachentscheide nach Research (10.10.2026, Claude nach Empfehlung, Owner-Linie "Rueckfragen minimal", Veto jederzeit)

- **D-30-05 Stoppliste:** Lucene `cz/stopwords.txt` (releases/lucene/10.5.2) wird uebernommen, gefaltet und entdoppelt; Eintraege, deren gefaltete Form ein haeufiges Inhaltswort ergibt (mindestens `byt` aus `být`), werden als benannte Ausnahme ENTFERNT und im Herkunftsbeleg aufgefuehrt. Inhaltswoerter des Originals (`strana`, `zprávy`, `první`) bleiben wie bei Lucene (bewaehrter Stand, kein Eigenbau).
- **D-30-06 Grenzliste:** Fuenfter Eintrag (Tschechisch ohne Stammformreduktion) wird in de/en/fr entworfen; der Wortlaut geht mit der Store-Text-Abnahme vor Release (REL-05) an den Owner. D-06 (vier Eintraege) wird damit auf fuenf erweitert.
- **D-30-07 Upgrade-Beweis:** Beide Richtungen in deploy-harp (de,en -> de,cs Umbau und zurueck), wie in v1.3; UPGRADE_FROM_TAG auf v1.4.2 umziehen, Schritte 2b/3c/5 entsprechend anpassen.
- **D-30-08 Schema-Einmaligkeit:** Phase 30 ist der einzige Schemaschritt (SCHEMA_VERSION 2 -> 3, LEGACY_SCHEMA_STEPS ("2","3"),("1","3")). Der Plan muss als Pruefzeile festhalten, dass der Ordnerfilter (Phase 32) ueber die `path`-Spalte in state.db ohne Schemafeld auskommt (Annahme A5).
- **Pflicht-Fix:** `_of_the_marks` (api/resources.py) muss Schema-Generation 2 UND 3 akzeptieren, sonst verlieren Bestandsinstallationen mit es/it/nl/pt still ihre Sprachfelder.

## Folge fuer Phase 30

- Da D-30-03 kein Schemafeld braucht, ist die einzige Schema-/Markenaenderung des Milestones das tschechische Koerperfeld (CZ-02). Bestandsinstallationen ohne `cs` in FINDLING_LANGUAGES bauen NICHT um.
- tantivy hat keinen tschechischen Snowball-Stemmer: Kette = Tokenizer, Kleinschreibung, Akzentfaltung, Stoppwoerter, KEIN Stemmer. Die Allowlist-Gegenprobe (test_language_allowlist.py) vergleicht gegen die laufende tantivy-Engine; Tschechisch braucht daher einen eigenen Weg ausserhalb von SNOWBALL_NAME (nicht einfach in LANGUAGE_ALLOWLIST eintragen, sonst Panic-/ValueError-Pfad).
- `ces`-OCR: Weg wie dan/est in Plan 16-10 (eigene apt-Zeile, Bau-Pruefung, OCR_LANGUAGE_ALLOWLIST).
- Upgrade-CI-Beweis: 1.4.2 -> neu ohne Umbau bei de,en; mit cs Umbau per Re-Analyse.
- Grenze dokumentieren (CZ-03): keine Stammformreduktion.

## Quellen

- .planning/research/v1.5-recherche-2026-10-10.md
- Issue #26 (mnaiman), Antwort issuecomment-6093545909: "Czech OCR und Czech text field planned for 1.5"
