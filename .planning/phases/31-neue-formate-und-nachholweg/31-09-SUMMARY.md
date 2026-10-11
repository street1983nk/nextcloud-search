---
phase: 31-neue-formate-und-nachholweg
plan: 09
subsystem: Suche (index/search.py), Extraktion (extract/dispatch.py, extract/archive.py)
tags: [fmt-02, d-30-03, d-30-08, snippet, highlights, pitfall-14, befund-15]
requires:
  - phase: 31-08
    provides: "Text einer ZIP-Datei aus Abschnitten U+001C + bereinigter Name + Zeilenumbruch + Mitgliedstext, ARCHIVE_MEMBER_MARK in config.py"
provides:
  - "snippets_for: Auszug eines ZIP-Treffers beginnt mit '<innere Datei>: ', Highlights hinter den Präfix verschoben"
  - "_passage_of: semantischer Auszug nennt die innere Datei ebenso"
  - "U+001C verlässt keinen Auszug mehr; Präfix nur für ext zip"
  - "cap_text(text, *, member_marks=False): entfernt U+001C außer für den ZIP-Leser"
affects: [31-10 Freischaltung application/zip, 31-11 Nachholweg, 31-14 docs/formats.md, 31-15 Audit]
tech-stack:
  added: []
  patterns:
    - "Name der inneren Datei am ersten Highlight gelesen, nicht am Fragmentanfang"
    - "Zeichenbereiche erst auf dem Rohfragment umgerechnet, dann für entfernte Marken und den Präfix verschoben"
key-files:
  created:
    - backend/tests/test_archive_snippet.py
  modified:
    - backend/src/findling/index/search.py
    - backend/src/findling/extract/dispatch.py
    - backend/src/findling/extract/archive.py
    - backend/tests/test_extract_text.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Ankerpunkt für den Namen ist der erste Highlight-Bereich, nicht der Fragmentanfang (gemessen: tantivy beginnt das Fragment einer kurzen ZIP-Datei beim ersten Mitglied)"
  - "Präfix nur bei gespeichertem ext == 'zip'; U+001C wird aus jedem Auszug entfernt, auch ohne Präfix"
  - "cap_text entfernt U+001C zentral; archive.py ist der einzige Aufrufer mit member_marks=True"
  - "Der Deckel snippet_chars gilt im semantischen Weg für den Text aus dem Dokument, der Name (höchstens 255 Zeichen) kommt hinzu"
metrics:
  duration: "ca. 75 min"
  completed: 2026-10-11
  tasks: 1
  files: 6
---

# Phase 31 Plan 09: Auszug nennt die innere Datei Summary

Ein ZIP-Treffer zeigt im Auszug den Namen der inneren Datei vor dem Fragment, z. B. `innen/rechnung.txt: ... zipquendel ...`; der Name kommt aus dem gespeicherten `body_de` (letzte Marke U+001C vor dem ersten Highlight), ohne Schemafeld und ohne Indexmarke (D-30-03, D-30-08). Die Hervorhebungen zeigen nach dem Präfix weiter genau auf die gesuchten Wörter. U+001C trägt nur noch der Text einer ZIP-Datei und erscheint in keinem Auszug.

## Umsetzung

- `index/search.py`: `_member_at(stored, position)` (letzte Marke bis Position, Name bis Zeilenumbruch), `_member_of(stored, fragment, offset)` (`str.find`, sonst None), `_is_archive` (gespeichertes `ext` == `"zip"`), `_without_marks` (Marke raus, Bereiche um die Marken davor verschoben), `_named` (Präfix `name + ": "`, Bereiche um `len(name) + 2`), `_excerpt` für den lexikalischen Weg. `_passage_of` liest den Namen am Chunkanfang. Kein zweiter Searcher-Aufruf: Text und `ext` kommen aus dem Dokument, das `_document_for` schon geladen hat (`get_first`).
- `extract/dispatch.py`: `cap_text(text, *, member_marks=False)` entfernt `ARCHIVE_MEMBER_MARK`, Docstring nennt den Grund (Befund 15).
- `extract/archive.py`: der eine `cap_text`-Aufruf mit `member_marks=True`.
- Baumhash: `PACKAGE_TREE_HASH_TODAY` `3d649243778d91e28b81d4df551688be03546c2418b96c3faa7dd5a57ded20ad`, `PACKAGE_FILES_TODAY` bleibt 78, Journalabsatz "Plan 31-09". PHP unverändert, PHP-Paar bleibt.

## RED

Neue Datei test_archive_snippet.py gegen den Stand 3d1e6b30: **10 failed, 3 passed**. Erste Fehlerzeilen:

```
E       AssertionError: assert False            (startswith "innen/rechnung.txt: ", "a.txt: ", "erste.txt: ", "name.txt: ")
E       AssertionError: assert '\x1c' not in '\x1ca.txt\n...del und mehr'
E       AssertionError: assert '\x1c' not in 'vorher\x1cn...standquendel'
E       AttributeError: module 'findling.index.search' has no attribute '_member_of'   (2 Fälle)
E       AssertionError: assert 'vorher\x1cna...estandquendel' == 'vorhername.t...estandquendel'
```

Später ergänzt, einzeln rot: `test_a_new_text_file_with_the_mark_is_found_without_it` (`assert '\x1c' not in 'Sehr geehrt...im Schreiben'`). test_extract_text.py: `test_a_text_file_with_the_archive_mark_is_indexed_without_it` (`assert '\x1c' not in ...`), `test_cap_text_removes_the_archive_mark_by_default` (Vergleich ungleich), `test_cap_text_keeps_the_archive_mark_for_the_archive_reader` (TypeError, Parameter fehlt).

Vor der Änderung grün und daher per Gegenprobe belegt: Bytegleichheit ohne Marke (Werte vor der Änderung aus `snippets_for` gelesen und gepinnt: `(20, 50)` bzw. `(5, 11), (54, 58)`), Namenssuche "rechnung.txt", Schema-Wache.

## Gegenproben

Je ein Eingriff, Tests gelaufen, Datei aus Sicherung zurück, `cmp` gleich:

| Probe | Eingriff | rot |
|---|---|---|
| G1 | Präfix immer gesetzt | 2: Bytegleichheit ohne Marke, Bestands-.txt |
| G2 | ext-Prüfung aus (`_is_archive` immer True) | 1: Bestands-.txt |
| G3 | Anker am Fragmentanfang statt am Highlight | 2: zweites Mitglied, Bestandstext als ZIP-Datei |
| G4 | Highlights nicht verschoben | 4 |
| G5 | Marke bleibt im Auszug | 2 |
| G6 | archive.py ohne `member_marks=True` | 16 in test_extract_archive.py (ZIP-Tests aus 31-08) |
| G7 | cap_text entfernt nichts | 2 in test_extract_text.py, 1 Ende-zu-Ende-Fall |
| G8 | Name `rechnung.txt` im Testtext ersetzt | 3, darunter die Namenssuche |
| G9 | `SCHEMA_VERSION = 4` | 1: Schema-Wache |
| G10 | `_passage_of` ohne Namen | 1 |

## Gates und CI

- Lokal vor 70be3383: ruff check (backend und ../scripts) grün, ruff format (213 Dateien) grün, pyright latest 0 Fehler, vulture grün, volle Suite **5282 passed, 27 skipped** (737 s; die zwei Warnungen aus test_ocr, vorbestehend). Plan-Prüfbefehl: 637 passed.
- `git diff --stat 3d1e6b30..HEAD -- backend/src/findling/index/schema.py` leer.
- Push `3d1e6b30..70be3383`, CI: Python gates **38132651127** (5294 passed, 15 skipped), Multi-arch image **38132651082**, Security scans 38132651114, OpenSSF Scorecard 38132651047, Integration **38132651134**, Resilience **38132651060**, HaRP deploy **38132651075**; alle sieben success. PHP-Gates liefen nicht (kein php/-Pfad berührt).
- Push `70be3383..ddaa4c51` (nur Testwort, siehe Abweichung 6), CI: Python gates **38133773017** (5294 passed, 15 skipped), Multi-arch image 38133773022, Security scans 38133772958, OpenSSF Scorecard 38133772975, Integration 38133773009, Resilience 38133773040, HaRP deploy 38133772994; alle sieben success. Vor ddaa4c51 lokal: ruff, format, pyright latest, vulture grün, betroffene Tests 583 passed, G3 erneut rot.

## Commits

| Commit | Inhalt |
|---|---|
| 70be3383 | feat(31-09): the excerpt of an archive hit names the inner file |
| ddaa4c51 | test(31-09): search word of the ZIP excerpt tests without the blocked stem |

## Deviations from Plan

**1. [Rule 1] Anker am ersten Highlight statt am Fragmentanfang.** Plan und Research lesen den Namen bei `rfind(MARK, 0, pos + 1)` mit `pos` = Fragmentanfang. Gemessen: tantivy beginnt das Fragment einer kurzen ZIP-Datei beim ersten Token des Textes, also im ersten Mitglied (`'\x1ca.txt\nerstes\n\n\x1cinnen/rechnung.txt\nzipquendel und mehr'`). Mit dem Fragmentanfang hätte ein Treffer im zweiten Mitglied `a.txt: ` bekommen, der Pflichtfall des Plans wäre rot. Der Name wird deshalb an `pos + erster Highlight-Beginn` gelesen (G3 belegt es). Ohne Highlight gilt der Fragmentanfang.

**2. Signatur `_member_of(stored, fragment, offset)`.** Der Plan nennt `_member_of(stored, fragment)`; der dritte Parameter trägt den Ankerpunkt aus Abweichung 1.

**3. Bereichsumrechnung vor dem Verschieben.** `char_ranges` läuft auf dem Rohfragment (mit Marke), danach werden die Bereiche um die entfernten Marken und den Präfix verschoben. So bleibt die Bytezählung der Engine die einzige Eingabe der Umrechnung.

**4. Testfall Mehrfachfund ohne Nachbar-Fragment.** "Fragment nicht per str.find gefunden" ist mit tantivy nicht herstellbar (Fragment ist immer ein Ausschnitt des gespeicherten Textes); geprüft über `_member_of` direkt.

**5. php.yml.** Der Plan erwartet einen grünen php.yml-Lauf des Pushes. Der Workflow startet nur bei Änderungen unter php/; kein PHP-Pfad berührt, daher kein Lauf (wie bei 31-08). PHP_TREE_HASH_TODAY unverändert.

**6. [Rule 1] Vokabelregel E-H2 im Testwort.** Das Suchwort des Plans enthielt den gesperrten Wortstamm. 31-08 hatte ihn in Testdaten bereits vermieden; das Wort heißt jetzt `zipquendel` (ddaa4c51). Kein automatischer Gate hatte es gefangen, die Regel sperrt den Stamm in docs/ und Store-Texten.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche. T-31-28b umgesetzt (cap_text entfernt U+001C außer für ZIP-Dateien, Präfix nur für ext zip, Tests mit .txt neu und Bestand, G1, G2, G7), T-31-28 (Name in 31-08 bereinigt, Subline bleibt reiner Text in PHP), T-31-30 (`str.find` nur auf dem schon geladenen Text, nur für ext zip; Messung in 31-14).

## Requirements

FMT-02 Darstellungsteil erfüllt. FMT-02 bleibt in REQUIREMENTS.md offen bis 31-10 (Freischaltung application/zip).

## Offene Punkte

- 31-10: `application/zip` freischalten, dispatch-Docstring "Container formats ... are not opened at all" anpassen, danach FMT-02 auf Complete.
- 31-14: Kosten von `str.find` je ZIP-Treffer auf großem ZIP-Text messen (T-31-30).
- 31-15 (Audit): Der Umbenennungsweg des Pollers (`_rewrite_metadata`, poller.py ab Zeile 1906) übernimmt den gespeicherten Text unverändert. Eine vor 1.5 indexierte .txt mit U+001C, die zu `.zip` umbenannt wird, bekäme bis zur nächsten Inhaltsextraktion einen Präfix aus ihrer eigenen Zeile. Inhalt bleibt der eigene des Dokuments, Auswirkung nur Anzeige; im Audit bewerten.
- Bei der Suche nach dem Namen selbst (z. B. "rechnung.txt") liegt der erste Highlight auf dem ersten passenden Wort; trifft "txt" schon den ersten Mitgliedsnamen, nennt die Subline dieses Mitglied (dokumentierte Grenze der ersten Fundstelle).

## Self-Check: PASSED

test_archive_snippet.py, search.py, dispatch.py, archive.py und diese SUMMARY vorhanden; Commits 70be3383 und ddaa4c51 in der Historie, origin/main auf ddaa4c51; alle CI-Läufe beider Pushes success. index/schema.py seit 3d1e6b30 unverändert. STATE.md und ROADMAP.md von Hand nachgezogen (9/15, nächster Plan 31-10), FMT-02 in REQUIREMENTS.md offen.
