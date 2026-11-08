# 43-DEBUG-SUCHE: Suchgegenprobe 15 von 23 (CI-Lauf 42425348629)

Stand: 2026-11-08. Untersuchung ohne Produktänderung, ohne Commit.

## Ergebnis in einem Satz

Kein Produktfehler. Der Harness schreibt in **jede** Testdatei dasselbe Wort, weil `next_word()` in `$(...)` läuft und der Zähler `word_count` die Subshell nie verlässt. Die Suche liefert deshalb für jedes "eindeutige" Wort alle Dateien, gekappt auf die Seitengröße. Was dabei je Nutzer oben steht, ist vom Wort unabhängig.

## Belegt

### B1: Alle Wörter sind gleich (Harness-Fehler)

- `scripts/ci/coverage_e2e.sh:170` `word_count=0`, `:171-179` `next_word()` erhöht `word_count` und gibt das Wort aus.
- Alle Aufrufer nutzen Kommandosubstitution: `:184` (samba_file), `:799`, `:800` (gesperrt-*), `:942`, `:1155` (backlog-*.png), `:1351` (rollback/notiz.txt). `$(...)` ist eine Subshell, die Erhöhung geht verloren.
- Nachstellung mit genau den Zeilen 171-179 (Skript `scratchpad/search-debug/nw.sh`):

```
call 1: zqpkmqspbh (parent word_count=0)
call 2: zqpkmqspbh (parent word_count=0)
call 3: zqpkmqspbh (parent word_count=0)
call 4: zqpkmqspbh (parent word_count=0)
call 5: zqpkmqspbh (parent word_count=0)
```

- Eingeführt mit Commit `a5182e98` (ci(43-07)). Einzige Abweichung: `gleich.txt` trägt zusätzlich `zqgleichdoc`.

### B2: Mit identischem Wort reproduziert sich das CI-Bild exakt

`scratchpad/search-debug/test_repro_route.py::test_same_word_as_in_ci`: echter Index (`open_index`, deutsche Kette), echte Route `POST /search`, Rechtezeilen nach Topologie (aaron sieht nur projekt-*), `limit=5`:

```
SAME zqpkmqspbh aaron  ['projekt-1.txt@0.0156', 'projekt-2.txt@0.0154', 'projekt-3.txt@0.0152'] hasMore=False
SAME zqpkmqspbh alice  ['daten-gemeinsam-1.txt@0.0164', 'daten-gemeinsam-2.txt@0.0161', 'daten-gemeinsam-3.txt@0.0159', 'projekt-1.txt@0.0156', 'projekt-2.txt@0.0154'] hasMore=True
SAME zqpkmqspbh carol  ['daten-carol-1.txt@0.0139', ..., 'archiv-carol-1.txt@0.0125'] hasMore=True
```

- aaron bekommt für jedes Wort dieselben 3 Einträge, wie im CI-Log (Zeilen 1299 bis 1311 und 6679 bis 6688: immer `aaron: 3 entries [projekt-1.txt, projekt-3.txt, projekt-2.txt]`). Die Reihenfolge 1,3,2 in CI kommt aus den dortigen file_ids (Gleichstand, RRF-Tiebreak niedrigere file_id, `index/fusion.py`, `reciprocal_rank_fusion`).
- Alle Treffer haben denselben BM25-Wert, also entscheidet die file_id (= Crawl-Reihenfolge) über die ersten 5. Darum fehlen in den Varianten verschiedene Dateien: v1.6.2 vermisst daten-gemeinsam-1, daten-bob-1, notiz.txt; gate-queue findet diese, vermisst dafür archiv-bob-1..3 (Log 1299-1311 gegen 6679-6688).
- 15 = Vereinigung der festen Top-Listen von aaron (3) plus alice, bob, carol (je bis 5) über alle Durchläufe. Wörter, deren Datei zufällig in einer solchen Liste steht, gelten als "gefunden".

### B3: Mit eindeutigen Wörtern ist die Suche exakt

`scratchpad/search-debug/repro1.py` (reiner Abfragepfad, `build_query` + `searcher.search`) und `test_repro_route.py::test_synthetic` (ganze Route, Prefilter, vier Nutzer), 22 Dateien der Topologie mit den Wörtern, die `next_word` hätte liefern sollen (Zähler 1..22):

- Jedes Wort liefert genau eine Datei, die richtige, Score 4.974 (gleich.txt 4.386, längerer Text), in der Route 0.0164 (RRF 1/61).
- aaron bekommt `[]` für jedes Wort außer projekt-1..3; alice/bob/carol bekommen genau ihre Datei, sofern sie sie sehen dürfen.
- Kein Fallback "keine Treffer, dann irgendwas": `api/search.py:249-252` gibt bei leerer Abfrage leer zurück, `index/search.py::candidates` liefert nur, was die Engine trifft.

### B4: Abfragepfad, geprüfte Stellen

- Ein-Wort-Regel: `query/rewrite.py:391-418` (`carries_one_term`) und `api/search.py:307` (`lexical_only = ... or rewritten.one_term ...`): Ein Wort fragt nie die Vektorseite. Zusätzlich lief CI mit `FINDLING_EMBED_ENABLED: false` (Log z. B. Zeile 56, 1446).
- Konjunktion, keine Regex: `query/rewrite.py:700-706` (`conjunction_by_default=True`, `allow_regexes=False`). Kein Fuzzy, kein Präfix im Parser-Aufruf.
- Umlautvarianten: `add_umlaut_variants` macht aus `zqncgcqaec` `(zqncgcqaec OR zqncgcqäc)` und aus `...ss...` eine ß-Variante (Ausgabe repro1). Harmlos, keine Fremdtreffer.
- Komposita: `split_compound` zerlegt nur vollständig zerlegbare Tokens (`index/analyzer.py:309`); `zq...` ist nicht zerlegbar, Token bleibt ganz (repro1: 1 Treffer je Wort).
- PHP: `php/lib/Search/Provider.php:246-336` und `php/lib/Service/SearchService.php:201-511` reichen den Term unverändert durch (`ExAppService.php:461-470`), filtern per `getFirstNodeById` (`SearchService.php:723-742`), kein Ersatzergebnis. Seitengröße = `$query->getLimit()` (`Provider.php:283`).

### B5: Gegenprobe mit realistischen deutschen Begriffen

`test_repro_route.py::test_realistic`, 6 Dokumente, Nutzer alice, `limit=5`:

```
'Az. 4 K 123/25'      ['bescheid-bauantrag.txt']   (nicht widerspruch.txt mit Az. 4 K 125/23, nicht liste.txt mit 123, 25, 4, K verstreut)
'"4 K 123/25"'        ['bescheid-bauantrag.txt']
'123/25'              ['bescheid-bauantrag.txt']
'Bauantrag'           ['bescheid-bauantrag.txt', 'merkblatt.txt' (Bauanträge)]
'Müllgebühren'        ['satzung.txt', 'widerspruch.txt']
'Muellgebuehren'      ['satzung.txt', 'widerspruch.txt']
'Abfall'              ['gebuehren.txt']
'Bauamt Müllgebühren' []   (Konjunktion, kein Dokument hat beide)
'Gebühren'            []   (siehe V2)
```

Seltene Wörter und Aktenzeichen liefern den richtigen Treffer und keine Fremdtreffer.

## Vermutet (nicht in diesem Lauf belegt)

- V1: Seitengröße 5 kommt aus dem Nextcloud-Standard `SearchQuery::LIMIT_DEFAULT` (5), weil der Harness kein `limit` mitschickt. Nicht im NC-Quelltext nachgelesen; passt aber zu "aaron 3, sonst höchstens 5" und zu 15 Funden.
- V2: `Gebühren` findet `Müllgebühren` lokal nicht, weil die Test-Wortliste (`tests/fixtures/constituents_de.txt`, 223 Einträge) nicht die echte ngerman-Liste ist. Mit der echten Liste nicht geprüft (kein Debian-Paket lokal). Für diese Untersuchung ohne Belang.
- V3: Auch die Rollback-Prüfung (`coverage_e2e.sh:1351-1361`) nutzt dasselbe Wort und prüft damit nur, dass notiz.txt unter alices ersten 5 Treffern ist, nicht dass der neue Inhalt gefunden wird. gesperrt-*.txt und backlog-*.png tragen ebenfalls das gleiche Wort.

## Antworten auf die vier Fragen

1. Projekt-Treffer ohne das Wort: Das Wort steht in projekt-1..3 (und in allen anderen Dateien), siehe B1/B2. Abfragepfad, Fuzzy, Komposita, Stemmer, Semantik und PHP liefern keine Fremdtreffer (B3, B4).
2. Echte Treffer fehlen: Alle Dateien treffen mit gleichem Score, nur die ersten 5 je Nutzer nach file_id kommen zurück (B2, V1). Kein Rechtefilter-Fehler, kein fehlender Indexeintrag.
3. Kein Produktfehler, den User sehen würden; reines Harness-Artefakt (B3, B5).
4. Empfehlung:
   - **Harness-Fix (nötig):** Wort ohne Subshell erzeugen, z. B. `next_word` setzt eine globale Variable (`next_word; word="${NEXT_WORD}"`) statt zu drucken, oder das Wort deterministisch aus dem Dateinamen ableiten (`coverage-43-07-<relativer Pfad>`). Dazu eine Positivkontrolle vor der Gegenprobe: `cut -f1 "${WORDS}" | sort | uniq -d` muss leer sein, sonst `fail`. Zusätzlich die Gegenprobe mit `--data-urlencode limit=25` fragen, damit ein Rangproblem nicht als Fehltreffer zählt. Risiko gering: ändert nur Testdaten; Zählerwahrheiten hängen nicht am Wortinhalt (nachprüfen beim Umbau, `leer.txt` bleibt ohne Wort).
   - **Produktfix:** keiner nötig.

## Nachtrag 2026-11-08 (43-18 Fix 2)

- V1 belegt: `core/Controller/UnifiedSearchController.php::search` (stable34) setzt `$limit ??= SearchQuery::LIMIT_DEFAULT` (5, `lib/private/Search/SearchQuery.php:16`) und deckelt auf `unified-search.max-results-per-request` (Standard 25).
- Harness-Fix umgesetzt in 289c0120: `next_word` setzt `NEXT_WORD`, `words_unique` vor dem Crawl und vor der Gegenprobe, Gegenprobe mit `limit=25`, Rückweg-Wort neu (V3 damit erledigt).
