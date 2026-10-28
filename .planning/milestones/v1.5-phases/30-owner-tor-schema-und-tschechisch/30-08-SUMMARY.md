---
phase: 30-owner-tor-schema-und-tschechisch
plan: 08
subsystem: docs/store-texte (language-analyzers, ocr, READMEs, beide info.xml, store-listing)
tags: [cz-03, cz-01, cz-02, d-30-06, store-text, rel-05, doku]
requires: [30-02, 30-04, 30-05, 30-07]
provides:
  - "docs/language-analyzers.md: Abschnitt Czech (an/aus, Kette ohne Stemmer, Lucene-Liste mit byt/jez, Platz 0.358, halbgefülltes Ziel, Rückweg auf 1.4.2 nicht getestet und nicht unterstützt), Langform CZ-03 und Inhaltswörter der Stoppliste, Lizenz/Herkunft"
  - "Grenzliste mit fünf Einträgen in allen sechs Store-Beschreibungen, zeichengleich gegen die Doku-Kurzliste (LIMITATION_COUNT = 5)"
  - "Suchsprachen-Zeile mit Tschechisch, OCR-Zeile zehn Sprachen, env-Texte mit cs und ces (Czech)"
  - "docs/store-listing.md: Entwurf v1.5.0 (Teil Phase 30), Owner-Abnahme offen bis REL-05"
affects: [30-09, 34 Umstiegs-Doku, 36 REL-05 Store-Text-Abnahme]
tech-stack:
  added: []
  patterns: ["Store-Wortlaut schon in info.xml, aber als Entwurf markiert: Gate-Kopplung erzwingt die Übernahme, Abnahme folgt mit REL-05"]
key-files:
  created: []
  modified:
    - docs/language-analyzers.md
    - docs/ocr.md
    - README.md
    - README.en.md
    - README.fr.md
    - backend/appinfo/info.xml
    - php/appinfo/info.xml
    - docs/store-listing.md
    - backend/tests/test_store_metadata.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Fünfter Eintrag im Planer-Wortlaut übernommen (en/de/fr), als Entwurf für REL-05 markiert (D-30-06)"
  - "FINDLING_OCR_LANGUAGES-Schlusssatz 'tuned for German and English only' wird zu 'by default' (seit 1.3.0 war 'only' schon unwahr)"
  - "PHP-Baumhash bewegt sich nicht: das Rezept liest nur **/*.php, die einzige Byteänderung unter php/ ist appinfo/info.xml; Journalabsatz trotzdem gesetzt"
  - "CZ-03 abgehakt (Grenze in Doku und Grenzliste); Owner-Wortlaut-Abnahme bleibt offener Punkt für REL-05"
metrics:
  duration: "ca. 50 min (davon 10,9 min volle Suite)"
  completed: 2026-10-10
  tasks: 2
  files: 10
---

# Phase 30 Plan 08: Tschechisch-Grenze in Doku und Store-Texten Summary

Die Grenze "tschechische Suche ohne Stammformreduktion" (CZ-03) steht als Langform in `docs/language-analyzers.md` und als fünfter Eintrag in der Grenzliste aller sechs Store-Beschreibungen, zeichengleich gegen die Doku-Kurzliste per Gate; Suchsprachen-, OCR- und env-Texte sowie die drei READMEs nennen cs bzw. ces. Der Wortlaut ist in `docs/store-listing.md` als Entwurf für die Owner-Abnahme bei REL-05 markiert.

## Ergebnis

**Task 1 (cd0750c2), Langform:**
- `docs/language-analyzers.md`: neuer Abschnitt `## Czech` vor "Known limits": Einschalten (`de,en,cs` oder `de,cs`, Neustart, Re-Analyse aus `body_de`, kein Neulesen, kein OCR, keine Neu-Einbettung, vectors.db bytegleich mit Verweis auf 30-05 und 30-07), Abschalten baut ebenfalls um und lässt `body_cs` leer, Bestand ohne cs bleibt auf Schema 2 (Lesestelle akzeptiert 2 und 3); Kette `simple -> lowercase -> ascii_fold -> custom_stopword -> remove_long(48)` mit Begründung; Falltabelle (`smlouvě`/`smlouve`/`SMLOUVĚ` treffen, `smlouva`/`smlouvě` nicht, Stoppwörter `proč`/`už`/`jsem`, Ausnahme `byt`); Stoppliste Lucene 10.5.2 mit Zahlen 171/169/167, Ausnahmen `byt` und `jez`, Inhaltswörter `strana`/`zprávy`/`první` bleiben (D-30-05); Platz 0.358 gegen 0.40; halbgefülltes Schema-2-Ziel wird verworfen; Rückweg auf 1.4.2 "is not tested and not supported", ohne Verhaltensaussage, mit Sicherungsempfehlung.
- Unter "Known limits": Langform CZ-03 (Flexion, Akzentpaar trifft, Semantik ab zwei Wörtern gleicht teilweise aus, Alternative und Preis) und Inhaltswörter auf der Stoppliste. D-06-Satz auf "fixed ... D-30-06 extends it by the Czech entry to five points" fortgeschrieben; "four entries" kommt nicht mehr vor.
- Nebenstellen nachgezogen: Codeliste `cs` (sieben Codes), OCR-Liste `ces`, Boost-Satz "Czech included", Schema-Tor nennt `QUERYABLE_SCHEMA_GENERATIONS` (2 und 3).
- "Licence and provenance": tschechische Liste (Apache-2.0, NOTICE in THIRD-PARTY.md, Änderungsvermerk 4(b), Original-Fixture, Generator).
- `docs/ocr.md`: Nachtrag 10.10.2026, `ces` als zehnte Sprache, zehn Allowlist-Einträge, Bild-Beweis docker.yml "Czech OCR in the image (CZ-01)".
- READMEs: zehn Sprachen / ten languages / dix langues, Tschechisch/Czech/tchèque in der Klammerliste, keine weiteren Sätze.

**Task 2 (50328ace), Grenzliste und Store-Texte:**
- RED belegt: nur `LIMITATION_COUNT = 5` plus neue Testzeile gegen die alten Texte: 5 failed / 76 passed in `test_store_metadata.py`.
- Sechs Beschreibungen: fünfter Eintrag als letzter Punkt (en "Czech: no stemming, inflected forms count as separate words", de "Tschechisch: keine Stammformreduktion, gebeugte Formen gelten als eigene Wörter", fr "Tchèque : pas de racinisation, les formes fléchies comptent comme des mots distincts"); Suchsprachen-Zeile mit Tschechisch; OCR-Zeile zehn/ten/dix (nur `php/appinfo/info.xml`, die Backend-Texte tragen keine OCR-Zeile).
- `backend/appinfo/info.xml` env: `FINDLING_LANGUAGES` "out of de, en, es, it, nl, pt and cs; cs works without stemming, ...", `FINDLING_OCR_LANGUAGES` "... est (Estonian) and ces (Czech)", Schlusssatz "by default" statt "only", Kommentar "ten language models".
- Doku-Kurzliste fünf Punkte, Einleitung nennt D-30-06 und den Entwurfsstatus, "The five entries point back ...".
- `docs/store-listing.md`: "# Entwurf v1.5.0 (Teil Phase 30)" mit Vermerk "Owner-Abnahme offen, mit der Store-Text-Abnahme vor Release (REL-05, Phase 36); Grundlage D-30-06", Wortlauten je Sprache (Grenzeintrag, Suchsprachen-Zeile, OCR-Zeile) und den zwei Variablentexten. Ältere Entwürfe unverändert.
- Gate-Datei: `LIMITATION_COUNT = 5` mit Kommentar D-30-06, Docstrings und Testname "five", Testzeile mit neuer Suchsprachen-Zeile.
- PHP-Baumhash: Rezept über `php/` gefahren (Test `test_measurement_scripts.py` grün), Hash und `PHP_FILES_TODAY` (90) unverändert, Journalabsatz Plan 30-08.

## Gates

Vor beiden Commits: ruff check, ruff format --check (197 Dateien), pyright latest 0 Fehler, vulture grün. Task 1: doku-lesende Tests 878 passed. Task 2: `test_store_metadata.py` + `test_measurement_scripts.py` 558 passed; volle Suite 4787 passed / 25 skipped (10:54 min, Skipzahl wie vorher). Beide info.xml wohlgeformt (lokal kein xmllint, Schemaprüfung in CI). Keine Em-/En-Dashes in den berührten Dateien.

## CI (Commit 50328ace)

Gepusht 08:48Z, alle acht Workflows success:

| Lauf | Workflow | Ergebnis |
|---|---|---|
| 38039184250 | PHP and store metadata gates | success |
| 38039184261 | Python gates | success |
| 38039184259 | Integration | success |
| 38039184223 | Resilience | success |
| 38039184274 | Multi-arch image | success |
| 38039184186 | Security scans | success |
| 38039184258 | OpenSSF Scorecard | success |
| 38039184349 | HaRP deploy (stable33/34/35, x86 und arm, bis 09:10:25Z) | success |

## Commits

| Commit | Inhalt |
|---|---|
| cd0750c2 | docs(30-08): Czech chain, its limits and ten OCR languages in docs and READMEs |
| 50328ace | docs(30-08): fifth known limitation Czech in all six store texts, draft for REL-05 |

## Deviations from Plan

**1. [Rule 1 - Stale Doku] Schema-Tor und Codelisten in language-analyzers.md**
- Der Absatz "What a question searches" sagte "not literally the current mark", seit 30-03 gelten aber 2 und 3 (`QUERYABLE_SCHEMA_GENERATIONS`); Codeliste "all six codes", OCR-Liste ohne `ces`, Boost-Satz "the four languages". Minimal fortgeschrieben.

**2. [Rule 1 - Unwahre Aussage] FINDLING_OCR_LANGUAGES "tuned for German and English only"**
- Seit 1.3.0 nicht mehr wahr; zu "by default" fortgeschrieben (Plan erlaubt minimale Fortschreibung).

**3. PHP-Baumhash unverändert**
- Plan erwartete einen neuen `PHP_TREE_HASH_TODAY`. Das Rezept liest nur `**/*.php`, `appinfo/info.xml` liegt außerhalb; Hash bleibt `bee7a954...9225`, Journalabsatz dokumentiert den Lauf.

**4. READMEs ohne Suchsprachen-Zeile**
- Die must_haves nennen "Tschechisch als verfügbare Suchsprache" auch für READMEs; die READMEs haben keine Suchsprachen-Zeile, und die Task-Aktion verbietet weitere Sätze (Kurztext-Regel). Nur die OCR-Faktenzeile geändert; Tschechisch als Suchsprache steht in den sechs Store-Texten.

**5. Kein separater RED-Commit**
- Wie 30-06/30-07: grüne Gates vor jedem Commit verlangt; RED lokal belegt (5 failed).

## Offene Owner-Punkte

- Wortlaut des fünften Grenz-Eintrags (en/de/fr) sowie Suchsprachen-, OCR- und Variablentexte: Abnahme mit der Store-Text-Abnahme vor Release (REL-05, Phase 36). Bei Änderung drei Stellen gemeinsam ändern (Doku-Kurzliste, sechs Beschreibungen, store-listing.md).
- Nichts eingereicht.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche. T-30-31 (fünfter Eintrag in allen sechs Beschreibungen, Gate), T-30-32 (Abgleich Doku gegen Store-Text, `LIMITATION_COUNT = 5`), T-30-33 (Entwurf als offen markiert, keine Einreichung), T-30-34 (PHP-Baumhash-Rezept gefahren, unverändert, Journal) umgesetzt.

## Self-Check: PASSED

- `grep -c "Czech: no stemming, inflected forms count as separate words"` je 1 in backend/appinfo/info.xml, php/appinfo/info.xml, docs/language-analyzers.md
- `LIMITATION_COUNT = 5` einmal, Kommentar nennt D-30-06
- docs/store-listing.md enthält D-30-06 und REL-05
- Commits cd0750c2 und 50328ace auf origin/main
