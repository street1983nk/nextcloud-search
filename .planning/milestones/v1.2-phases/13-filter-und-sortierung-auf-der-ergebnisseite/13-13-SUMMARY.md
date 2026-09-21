---
phase: 13-filter-und-sortierung-auf-der-ergebnisseite
plan: 13
subsystem: testing
tags: [abnahme, gates, audit, asvs, security, bugs, performance, filt-01, filt-02, filt-03, filt-04, filt-05]

requires:
  - phase: 13-filter-und-sortierung-auf-der-ergebnisseite
    plan: 11
    provides: "sechs Kataloge mit je 197 Schluesseln und die nachgezogenen Zahlen-Gates"
  - phase: 13-filter-und-sortierung-auf-der-ergebnisseite
    plan: 12
    provides: "drei Paritaetsszenarien und das nachgezogene Testregister"
provides:
  - "Gate-Protokoll des Gesamtlaufs: alle sechs Stufen in einem Zug gruen, 2128 passed"
  - "Security-Durchgang V4/V5/V7 mit je einer Feststellung und die drei Bedrohungsmuster"
  - "Bug-Durchgang ueber die fuenf ungedeckten Pfade, zwei davon jetzt mit eigenem Testfall"
  - "Performance-Nachweis am Code: Sortierzweig unter SEARCH_SCAN_MAX, Filterklausel vor dem Fusionsfenster"
affects: [phase-14, phase-15]

tech-stack:
  added: []
  patterns:
    - "Ein Audit-Pfad ohne Gate bekommt ein Gate statt eines Protokollsatzes: die zwei neuen Testfaelle halten den Befund fest, nicht nur diese Datei"

key-files:
  created: []
  modified:
    - backend/tests/test_query_rewrite.py

key-decisions:
  - "Der woertliche Verify-grep auf isReadable zaehlt einen Phase-11-Kommentar mit; der Nachweis wurde sinnwahrend als Aufrufstellen-Zaehlung gefuehrt, die Datei blieb unangetastet"
  - "since groesser until und alle sechs Typgruppen zugleich sind als Testfaelle festgehalten statt nur als Code-Lektuere protokolliert"

patterns-established: []

requirements-completed: [FILT-01, FILT-02, FILT-03, FILT-04, FILT-05]  # Owner-Abnahme 19.09.2026

duration: 25min
completed: 2026-09-18
---

# Phase 13 Plan 13: Gesamtlauf, Audit-Durchgang und die offene Abnahme Summary

**Alle sechs Gate-Stufen laufen in einem Zug gruen (2128 passed, 15 vorbestehende Umgebungs-Skips), der Security-, Bug- und Performance-Durchgang ist gefahren mit vier Befunden (zwei behoben per neuem Testfall, zwei erklaert), und die 17 Sichtproben samt D-01 bis D-07 warten als Task 2 auf den Owner an der laufenden Instanz.**

## Performance

- **Duration:** 25 min (Task 1)
- **Started:** 2026-09-18T16:05:12Z
- **Completed:** 2026-09-19 (Task 1 am 18.09., Task 2 mit Owner-Abnahme am 19.09.)
- **Tasks:** 2 von 2
- **Files modified:** 1

## Status der beiden Tasks

| Task | Stand |
|---|---|
| Task 1: Gesamtlauf aller Gates und Audit-Durchgang | ABGESCHLOSSEN |
| Task 2: Die 17 Sichtproben an der laufenden Instanz | BESTANDEN, Owner-Abnahme 19.09. (siehe Nachtrag 19.09. Mittag) |

## Task Commits

1. **Task 1: zwei Audit-Pfade als Testfaelle festgehalten** - `98fa6d7` (test)

## Gate-Protokoll

Die vollstaendige Kette beider Haelften, in einem Zug am 18.09.2026 gegen main
(`dca5007` plus der Testcommit dieses Plans), so wie `python.yml` sie faehrt:

| Stufe | Ausgang |
|---|---|
| `uv run ruff check .` | gruen, "All checks passed!" |
| `uv run ruff format --check .` | gruen, 122 Dateien |
| `uv run pyright` | gruen, 0 errors, 0 warnings |
| `uv run vulture src tests --min-confidence 80` | gruen, keine Ausgabe |
| `uv run pytest -q` (VOLLE Suite, nicht nur tests/unit) | gruen, 2128 passed, 15 skipped |
| `uv run ruff check ../scripts` | gruen |

Kein `skip` wurde hinzugefuegt, keine Schwelle gesenkt, kein Gate gelockert
(T-13-62). Die 15 Skips sind saemtlich vorbestehende Umgebungs-Skips und keiner
gehoert zu Phase 13: zwei fehlendes Embed-Modell (`FINDLING_EMBED_MODEL_DIR`),
neun fehlendes Tesseract auf dieser Maschine (laufen im Container), vier
POSIX-Limits (`RLIMIT_AS`), die auf Windows nicht pruefbar sind.

Die Zahl 2128 statt 2126 (Stand 13-12) kommt aus den zwei neuen Testfaellen
dieses Plans (Befund 2 unten).

PHP-Gates (`php -l`, PHPUnit, Store-Metadaten) sind CI-Sache: auf dieser
Maschine gibt es kein PHP und die Docker-Engine ist aus. Lokal liefen die vier
Text-Gates, die den PHP-Quelltext lesen, einzeln nach: `test_php_acl_boundary.py`,
`test_php_trust_boundary.py`, `test_admin_ui_contract.py` (45 Tests, darunter
die sechs Verbots-Gates aus 13-10 und die vier Katalog-Gates) und
`test_search_fields_lockstep.py`, zusammen 89 passed.

### Verify-Block des Plans

Der Block lief woertlich und fiel an genau einer Stelle: dem letzten grep
(`grep -c 'isReadable' ... | grep -qx 1`). Alles davor war gruen. Der Grund ist
Befund 1 unten; die sinnwahrende Fassung (Aufrufstellen `->isReadable(` statt
Textvorkommen) endet mit GRUEN:

```
prefilter_visible ausserhalb von Kommentaren: 2   (gefordert: 2)
->getFirstNodeById( Aufrufstellen:            1   (gefordert: 1)
->isReadable( Aufrufstellen:                  1   (gefordert: 1)
isReadable als Textvorkommen:                 2   (1 Aufruf + 1 Kommentar aus Phase 11)
```

## Die bewusst offenen Zwischenstaende aus 13-09 und 13-10

Geprueft und bestaetigt: `test_admin_ui_contract.py` traegt `== 197` genau
einmal und `== 174` gar nicht mehr; die vier Katalog-Gates (Schluesselmengen
ueber sechs Dateien, deutsche Zwillinge, franzoesische Vollstaendigkeit mit
fuenf benannten G2-Ausnahmen, Platzhalter-Paritaet) sind im Gesamtlauf gruen.
Praezisierung zum Plantext: 13-09 und 13-10 haben die Katalog-Gates nie rot
hinterlassen, weil die Gates die Kataloge lesen und nicht die Vorlage; der
bewusst unvollstaendige Zwischenstand war, dass die 23 Quell-Strings nur auf
Englisch existierten. 13-11 hat die Kataloge und beide Zahlen nachgezogen, und
der Gesamtlauf belegt es.

## Security-Durchgang (ASVS V4, V5, V7)

### V4 Access Control: bestanden

Die Rechtegrenze ist in Zahl, Ort und Reihenfolge unveraendert. Aufrufstellen
gezaehlt wie `test_php_acl_boundary.py` es tut (Pfeil plus Name, Kommentare und
Zeichenketten entfernt): `->getFirstNodeById(` genau einmal
(SearchService.php:349), `->isReadable(` genau einmal (SearchService.php:362).
`prefilter_visible` steht ausserhalb von Kommentaren genau zweimal in
`backend/src/findling/index/search.py` (Relevanzzweig und Sortierzweig), und
`test_the_permission_prefilter_is_called_at_exactly_two_places` haelt das als
Gate. Keine neue Route: der Phasen-Diff (Basis `c874545`) beruehrt weder
`php/appinfo` noch registriert er einen neuen FastAPI-Endpunkt; die einzige
Aenderung an einer Routendatei ist die Erweiterung der bestehenden
Diagnose-Signatur um Query-Parameter (13-03), am bestehenden Endpunkt.

### V5 Input Validation: bestanden

Jeder der vier neuen Wire-Felder hat seine geschlossene Menge oder Grenze und
seinen Negativfall (alle in `backend/tests/test_search_endpoint.py` bzw.
`test_snippets_endpoint.py`):

| Feld | Grenze | Negativfall |
|---|---|---|
| `SearchRequest.types` | Literal-Sechsermenge plus `max_length=SEARCH_TYPE_GROUPS_MAX` | `test_an_unknown_group_name_is_refused_and_never_ignored`, `test_more_group_names_than_the_vocabulary_holds_are_refused` |
| `SearchRequest.sort` | Literal-Dreiermenge | `test_an_unknown_sort_name_is_refused` |
| `SearchRequest.since` | `ge=0, le=SEARCH_MTIME_MAX` | `test_a_time_edge_outside_its_bounds_is_refused` (-1 und MAX+1) |
| `SearchRequest.until` | dieselbe Feldgrenze | strukturgleich mit `since`; die Decke selbst ist als gueltig belegt (`test_the_documented_time_ceiling_is_accepted`) |

`SnippetsRequest` traegt ausdruecklich kein `sort`
(`test_a_sort_field_in_the_excerpt_body_is_refused`), und das Lockstep-Gate
haelt beide Modelle zusammen. Jeder der sechs neuen Adresswerte der Seite hat
seine geschlossene Menge oder Klemme und seinen Negativfall (alle in
`php/tests/Unit/PageControllerTest.php`, gruen in CI, Textlage lokal gelesen):

| Adresswert | Geschlossene Menge / Grenze | Negativfall |
|---|---|---|
| `types` | Kanonisierung als Schleife ueber `SearchFilters::TYPES` | `testAnUnknownGroupIsLeftOutAndARepeatedOneIsKeptOnce` |
| `sort` | `SearchFilters::SORTS`, stiller Rueckfall | `testASortModeTheAddressDoesNotKnowIsRelevance` |
| `range` | `PageController::QUICK_RANGES` | `testAQuickRangeTheAddressDoesNotKnowSetsNoBoundAtAll` |
| `since` | 0 bis `SearchFilters::EPOCH_MAX`, fremdartig heisst nicht gesetzt | `testATimeBoundThatIsNotOneIsNotSet` (fuenf Formen) |
| `until` | dieselbe Klemme | derselbe Fall, beide Grenzen je Durchlauf |
| `fp` | Formpruefung acht Hexzeichen vor jedem Vergleich | `testAFingerprintThatIsNotOneIsPageOne` |

### V7 Logging: bestanden

Der Phasen-Diff ueber `backend/src`, `php/lib` und `php/templates` enthaelt
genau einen neuen Logger-Aufruf: `LOGGER.info("the candidate scan hit its raw
ceiling and answered a truncated page")` im Sortierzweig (search.py:538), eine
literale Konstante ohne Suchbegriff, ohne Pfad und ohne Trefferzahl, wortgleich
mit dem vorbestehenden Satz des Relevanzzweigs (Zeile 621) und mit demselben
Kommentar ("Only the fact, never the query or the counts"). Kein weiterer
neuer Log-Satz in der Phase.

### Die drei Bedrohungsmuster

- **Kein Zaehl-Orakel (T-13-65):** `CandidatePage` traegt weiterhin keinen
  Gesamtwert (Kommentar an `needed`, search.py:515), die Diagnoseroute nimmt
  die Filter, gibt aber keine Trefferzahl heraus (13-03), der Cursor zaehlt
  erlaubte Kandidaten, und das Gate
  `scan_filter_row_for_a_counting_oracle` haelt die Leiste frei von `count`,
  `total`, `badge`, `disabled` und Pluralausgabe. Alle zehn Chips werden immer
  gerendert, ohne Zahl, ohne Punkt, ohne Ausgrauen.
- **Keine zweite Tuer an der Rechtegrenze (T-13-63):** siehe V4; dazu der
  13-12-Befund, dass der Filter ausschliesslich die Seite erreicht und keine
  der beiden OCS-Routen, es gibt also keinen zweiten Weg an denselben Bestand.
- **Keine unbegrenzten Parameter:** alle vier Wire-Felder tragen Menge oder
  Grenze (Tabelle oben), die PHP-Seite klemmt statt abzulehnen
  (`typeGroupsWithin`, `epochWithin`), und beide Suchzweige fahren die Decke
  `SEARCH_SCAN_MAX` (unten).

## Bug-Durchgang ueber die fuenf Pfade ohne Gate

| Pfad | Nachweis | Ergebnis |
|---|---|---|
| Gefilterte Suche ueber mehrere Seiten | `test_paging_through_a_filtered_ranking_loses_no_hit` (Engine: keine Dublette, keine Luecke) plus `testThePagingLinksCarryTheFingerprintAndTheActiveFilters` (Adresse) | gruen |
| Sortierte Suche ueber mehrere Seiten | `test_two_sorted_pages_are_the_one_deep_page` plus `test_a_sort_changes_the_order_and_never_the_set` | gruen |
| Zeitraum ohne Treffer | `test_a_period_that_lies_in_the_future_is_empty_and_not_an_error` (leere Seite, kein Fehler, `errors == []`) | gruen |
| `since` groesser als `until` | war ungedeckt; jetzt `test_a_lower_bound_above_the_upper_bound_is_empty_and_not_an_error` (Befund 2, Commit `98fa6d7`): leere Seite, kein Fehler | gruen |
| Adresse mit allen sechs Typen gleichzeitig | war ungedeckt; jetzt `test_all_six_type_groups_together_are_no_narrowing` (ebd.): Union ueber das ganze Vokabular antwortet wie die ungefilterte Suche; der Draht nimmt genau sechs Namen an (`SEARCH_TYPE_GROUPS_MAX`), die Kanonisierung der Seite laeuft ueber die geschlossene Liste | gruen |

Nur an einer laufenden Instanz pruefbar und darum Task 2 zugeordnet: das
Zusammenspiel dieser Pfade in der Oberflaeche, insbesondere Sichtprobe 5
(blaettern, dann Chip: Seite 1 ohne Dublette), Sichtprobe 6 (von Hand kopierte
`cursors`-Adresse) und Sichtprobe 9 (Mitternachtsverhalten von "Heute" in der
Ortszeit). Der Paritaetsjob (Szenarien 11 bis 13 aus 13-12) laeuft erst in CI;
die zwei dort zuerst anzusehenden Punkte stehen in 13-12-SUMMARY.

## Performance-Durchgang (am Code, nicht gemessen)

- **Dieselbe Decke:** `scan_cap = SEARCH_SCAN_MAX` wird in `candidates()` VOR
  der Zweig-Weiche gesetzt (search.py:519) und unveraendert an beide Zweige
  gereicht: der Sortierzweig bekommt `scan_cap=scan_cap` (Zeile 531, Schleife
  in `_sorted_round`, Zeile 429), der Relevanzzweig laeuft dieselbe Variable in
  seiner Fortsetzungsschleife (Zeile 601). Der Docstring (Zeile 497) sagt es
  ausdruecklich: "Both sections are bounded by SEARCH_SCAN_MAX raw hits".
- **Filterklausel vor dem Fusionsfenster:** `build_query` haengt die Klausel
  als `Occur.Must` an die geparste Abfrage (rewrite.py:556), und genau diese
  Abfrage fuellt das Fenster (`_sides(..., window=min(rrf_window,
  SEARCH_SCAN_MAX))`, search.py:549). Das Fenster sieht also nur gefilterte
  Treffer; nichts wird erst geholt und dann verworfen. Die semantische Haelfte
  wird an ihrem einzigen Indexkontakt mit derselben Klausel geschnitten
  (`_mtimes_of(filter_query=...)`, search.py:388-389) und ist ihrerseits durch
  `vector_scan_max` gedeckelt.
- **Zuordnung:** Die Messung auf grossem Bestand (52.111 Dokumente, Annahme A1
  der Recherche) gehoert in die Phase-15-Anfahrt und wird dort unter MESS-05
  mitgenommen; T-13-66 bleibt bis dahin ein bewusst angenommenes Risiko.

## Befunde, je mit Einordnung

**1. [erklaert] Der woertliche Verify-grep auf `isReadable` zaehlt einen
Kommentar aus Phase 11 mit.** `grep -c 'isReadable'` liefert 2, weil der
DI-07-03-Kommentar aus Plan 11-13 (Commit `78ed14c`, SearchService.php:214) den
Methodennamen nennt; die Aufrufstelle ist genau eine (Zeile 362). Der Zustand
besteht seit Phase 11 unveraendert und ist kein Werk dieser Phase. Das
projekteigene Gate `test_php_acl_boundary.py` zaehlt ausdruecklich
Aufrufstellen (`->` plus Name, Kommentare entfernt) und dokumentiert im
eigenen Testfixture, dass ein Kommentar keine Aufrufstelle ist; es ist gruen.
Der Nachweis wurde deshalb sinnwahrend als Aufrufstellen-Zaehlung gefuehrt
(GRUEN, siehe Gate-Protokoll), dieselbe Behandlung wie die
Media-Query-Zaehlung in 13-10. Die Datei wurde NICHT angefasst: den
Phase-11-Kommentar umzuformulieren, nur damit ein naiver grep besteht, waere
eine Anpassung des Pruefgegenstands an die Pruefung. Fuer den Python-Teil
desselben Verify macht der Plan es selbst richtig (`grep -v '^ *#'` vor der
`prefilter_visible`-Zaehlung); die PHP-Haelfte hat schlicht keinen
Kommentar-Ausschluss bekommen.

**2. [behoben] Zwei Pfade des Bug-Durchgangs hatten keinen Testfall.**
`since` groesser als `until` und alle sechs Typgruppen zugleich waren nirgends
belegt. Beide Verhalten wurden nicht nur gelesen, sondern als Testfaelle
festgehalten (`test_a_lower_bound_above_the_upper_bound_is_empty_and_not_an_error`,
`test_all_six_type_groups_together_are_no_narrowing` in
`backend/tests/test_query_rewrite.py`), beide auf Anhieb gruen: das umgekehrte
Fenster ist eine leere Seite und kein Fehler, die Voll-Auswahl engt nichts
ein. Commit `98fa6d7`; die Suite waechst von 2126 auf 2128.

**3. [bewusst hingenommen] 15 Umgebungs-Skips in der Suite.** Embed-Modell,
Tesseract und POSIX-Limits fehlen auf dieser Windows-Maschine; alle 15 Skips
bestehen seit frueheren Phasen, tragen ihren Grund im Skip-Text und laufen im
Container bzw. in CI. Keiner beruehrt Phase 13, keiner wurde in dieser Phase
hinzugefuegt.

**4. [bewusst hingenommen] Eine Deprecation-Warnung aus Fremdcode.** Die
installierte fastapi-Testclient-Datei warnt beim Import und empfiehlt darin
ein anderes Paket. Das ist Fremdcode in `site-packages`, kein Code dieses
Baums, und die Empfehlung wird ausdruecklich NICHT befolgt: diese Phase
installiert kein Paket (T-13-SC), und ein Paketwechsel auf Zuruf einer
Warnung waere genau das Warnsignal, das 13-RESEARCH beschreibt. Beobachten,
nicht handeln.

**5. [behoben] Die sortierte Runde wiederholte und übersprang Dokumente an
Seitengrenzen.** Fundweg: Sichtprobe 8 an der laufenden Instanz (Port 8090),
zweimal deterministisch identisch gemessen. Messung: Suche "Genehmigung" mit
sort=newest über alle 12 Seiten (25 je Seite, 300 Zeilen) lieferte nur 273
eindeutige file_ids, 27 Dubletten und 27 fehlende Dokumente gegenüber
sort=oldest (das umgekehrt 11 Dubletten und 11 Lücken hatte); die Dubletten
saßen an angrenzenden Seitengrenzen und begannen exakt beim Übergang von
Seite 5 auf 6. Ursache: `_sorted_round` in
`backend/src/findling/index/search.py` wählte die Portionsgröße als
`max(needed, _SCAN_CHUNK_MIN)`, und needed wächst mit der Seitentiefe. Die
Gleichstands-Nachsortierung nach (mtime, file_id) läuft je Portion; bis
Seite 5 (needed <= 128) lagen die Portionsgrenzen aller Anfragen gleich, ab
Seite 6 (needed = 151) verschoben sie sich. Damit zerfiel die große
Zeitstempel-Gleichstandsgruppe des Massenuploads je Anfrage anders, und die
Offset-Slices benachbarter Seiten überlappten beziehungsweise ließen aus. Der
Kommentar an der Stelle behauptete Stabilität, war aber mit konstanten
Portionsgrenzen gemessen worden. Fix: feste Portionsschrittweite
(`chunk_limit = min(_SCAN_CHUNK_MIN, scan_cap - raw_cursor)`), damit
reproduziert jede Anfrage dieselbe deterministische Gesamtfolge;
`SEARCH_SCAN_MAX` bleibt die Decke, keine neue Konfiguration, die
Relevanz-Rangfolge ist unberührt. Regressionstest
`test_pages_of_unequal_depth_repeat_and_lose_nothing_across_a_portion_boundary`
(160 Dokumente gleichen Zeitstempels über der 128er-Grenze, parametrisiert
für newest und oldest), Gegenprobe vor dem Fix rot mit 160 Zeilen bei nur 141
eindeutigen Dokumenten. Kommentar wahrheitsgemäß nachgezogen. Commits
`264ffb8` (Fix + Test) und `6e22c48` (Baumhash des Pakets nachgezogen); die
Suite wächst von 2128 auf 2130. Der lexikalische Zweig mit derselben
`max(needed, ...)`-Konstruktion (Zeile ~602) bleibt unverändert: dort gibt es
keine Nachsortierung je Portion, die Engine-Reihenfolge bei Score-Gleichstand
hängt von der Dokumentadresse und nicht vom angefragten Limit ab, ein roter
Test war nicht konstruierbar.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Fehlende Zusicherung] Zwei ungedeckte Audit-Pfade als Tests festgehalten**
- **Found during:** Task 1, Bug-Durchgang
- **Issue:** siehe Befund 2
- **Fix:** zwei neue Testfaelle in `backend/tests/test_query_rewrite.py`
- **Files modified:** backend/tests/test_query_rewrite.py
- **Verification:** beide gruen, volle Kette danach erneut in einem Zug gruen
- **Committed in:** `98fa6d7`

### Nachweis statt Datei-Aenderung

**2. [Rule 3 - Blockierend] Der Verify-Block des Plans ist an einer unveraenderten Datei rot**
- **Found during:** Task 1, Verify
- **Issue:** siehe Befund 1
- **Fix:** keiner am Baum; die pruefbare Absicht (genau eine Aufrufstelle je
  Frage der Rechtekette) wurde mit der Zaehlweise des projekteigenen Gates
  nachgewiesen, Praezedenz ist die 13-10-Abweichung zur Media-Query-Zahl
- **Files modified:** keine

---

**Total deviations:** 1 auto-fixed (Rule 2), 1 Nachweis angepasst (Rule 3)
**Impact on plan:** Kein Scope-Creep; beide staerken die Pruefbarkeit, keiner aendert Verhalten.

## Die zwei bekannten Checkpoint-Punkte fuer Task 2

1. **Aus 13-11:** Die 23 franzoesischen Wortlaute der Leiste sind maschinell
   geprueft, aber von keinem Muttersprachler und nicht vom Owner gelesen. Die
   Abnahme in `docs/l10n-french.md` vom 11.09.2026 deckt 173 Zeilen; der
   datierte Nachtrag dort sagt es. Gehoert zur Freigabe dieser Phase
   (Sichtprobe 17 streift es: "Feuilles de calcul" bricht die Leiste nicht).
2. **Aus 13-12:** Das dritte Paritaetsszenario (`types=images`) ist als direkte
   Wegnahme-Messung gebaut statt als symmetrischer Vergleich, weil der Filter
   nur die Seite erreicht und keine der beiden OCS-Routen. Die
   `extra`-Richtung ist unter dem wegnehmenden Filter nur ueber leere Mengen
   belegt; wer es schaerfer will, braucht ein Fixture mit zwei Dateitypen
   (Erweiterung, kein Nachtrag). Der Owner nimmt diese Bauform mit ab.

## Die 17 Sichtproben: VORBEREITET am 18.09. abends, Abnahme durch den Owner OFFEN

Die Docker-Engine wurde am 18.09. abends gestartet, die Instanz nach
`docs/dev-setup.md` hochgefahren (Port 8090, DB-Upgrade auf 34.0.3 nachgezogen,
Backend als Host-Prozess neu registriert) und die Proben wurden per Browser
(Playwright) und im DOM gemessen. Das Embedding-Modell fehlte dem Host-Prozess;
es wurde aus dem Shipping-Image 1.1.0 extrahiert und ueber
FINDLING_EMBED_MODEL_DIR eingebunden. Der Altbestand traegt KEINE Vektoren
(indexiert, als das Modell fehlte; Reconcile traegt Vektoren bewusst nicht
nach), darum lief die Paraphrasen-Probe gegen eine frisch hochgeladene Datei.

Ergebnisse, in der Reihenfolge der UI-SPEC. "gemessen" heisst: im DOM oder
ueber die ausgelieferten Seiten automatisiert belegt; was nur ein Mensch
abnehmen kann, steht ausdruecklich beim Owner.

1. BESTANDEN (gemessen): zehn Chips (6 Dateityp + 4 Zeitraum) und drei
   Sortierlinks ueber der Liste, alle Chips ohne aria-current, "Relevanz"
   traegt aria-current=true und die active-Klasse, kein Zuruecksetzen-Link
   im Findling-Bereich (der einzige Regex-Treffer war ein versteckter
   Nextcloud-Profilhinweis).
2. BESTANDEN (gemessen): types=pdf liefert 25/25 PDF-Treffer, Chip mit
   aria-current=true und aria-label "Filter PDF entfernen", Link "Alle Filter
   zuruecksetzen" erscheint, Anzeige "Seite 1", Adresse ohne page/cursors.
3. BESTANDEN (gemessen): types=pdf,images zeigt beide Chips aktiv, Treffer
   beider Gruppen (pdf und tif); der aktive PDF-Chip verlinkt auf
   types=images, entfernt also nur sich selbst.
4. TEILWEISE BESTANDEN (gemessen, mit Einschraenkung): die CI-Paraphrase
   ("Wann darf ich meinen Job aufgeben und wie lange muss ich vorher warten",
   kein Wort im Zieldokument) findet die frisch indexierte Datei
   kuendigungsfrist-probe.txt OHNE Filter und UNTER types=text gleichermassen;
   die Semantik bleibt unter Filter also aktiv. NICHT pruefbar an dieser
   Instanz: "Seite voll besetzt statt halbleer", weil nur eine Datei Vektoren
   traegt. Der volle Fall gehoert an eine Instanz aus dem Container-Image
   (Modell und Vektoren ab Werk) oder in die CI (index-search-e2e deckt den
   Mechanismus).
5. BESTANDEN (gemessen): auf Seite 3 geblaettert, Chip-Link von dort traegt
   weder page noch cursors (Seite 1 der neuen Auswahl); die komplette
   types=pdf-Blaetterei (8 Seiten, 195 Treffer) ist dublettenfrei und
   lueckenlos.
6. BESTANDEN (gemessen): cursors samt fp aus der ungefilterten Suche in eine
   types=pdf-Adresse kopiert: 200, "Seite 1", 25 Treffer, kein Fehlerblock,
   keine Ausnahme im Backend-Log.
7. BESTANDEN (gemessen): unter sort=newest traegt jede der 25 Zeilen
   "Geaendert am ...", die Folge faellt monoton, nirgends ein Relevanzwert;
   unter Relevanz ist die Datumszeile weg (0 Treffer im DOM). Der
   Accessible Name der Trefferzeile traegt das Datum mit ("..., geaendert am
   9. September 2026"), das deckt die Screenreader-Haelfte von Probe 14.
8. BESTANDEN NACH BEFUND 5 (gemessen): die Erstmessung ueber alle 12 Seiten
   fand 27 Dubletten/27 Luecken (newest) bzw. 11/11 (oldest), deterministisch
   reproduzierbar; Ursache und Fix stehen als Befund 5 oben (264ffb8).
   Nachmessung nach Fix und Backend-Neustart: newest und oldest je 300
   Zeilen, 0 Dubletten, 0 Luecken, identische Mengen in beiden Richtungen.
9. BESTANDEN (gemessen, Mitternachtsfall offen): range=year dann range=today,
   jeweils genau EIN Zeitraum-Chip aktiv; range=today enthaelt die Datei der
   letzten Stunde (kuendigungsfrist-probe.txt, hochgeladen 18.09. abends).
   Die Probe UM MITTERNACHT Ortszeit steht aus (heute 18-19 Uhr gemessen).
10. BESTANDEN (gemessen): Leerzustand "Keine Treffer mit den aktiven Filtern"
    mit Satz und Link "Filter zuruecksetzen" auf dieselbe Suche ohne Filter,
    die wieder Treffer liefert.
11. BESTANDEN (gemessen): Backend-Prozess gestoppt, gefilterte Seite geladen:
    Fehlerblock "Die Suche antwortet gerade nicht ... Ihre Dateien sind
    unveraendert" steht, der Filter-Leerzustand schweigt, alle zehn Chips
    bleiben als Links bedienbar. Backend danach wieder gestartet.
12. STRUKTURELL BESTANDEN (gemessen): das Suchformular ist ein GET-Formular
    auf /apps/findling/ (Feld query), alle 14 Bedienelemente (10 Chips, 3
    Sortierlinks, Zuruecksetzen) sind reine a-href-Links, ebenso das
    Blaettern. Ein Lauf mit tatsaechlich abgeschaltetem JavaScript bleibt dem
    Owner (konstruktiv kann nichts an JavaScript haengen).
13. STRUKTURELL BESTANDEN (gemessen): Chips vor Sortierlinks in
    Dokumentreihenfolge, je Chip genau EIN Fokus-Stopp (keine geschachtelten
    Fokusziele), :hover/:focus-Regeln vorhanden, fokussierter Chip zeigt
    einen Umriss. Der echte Nur-Tastatur-Durchgang bleibt dem Owner.
14. STRUKTURELL BESTANDEN (gemessen): role=group mit Namen "Dateityp",
    "Zeitraum", "Sortieren nach" (Accessibility-Baum), aktiver Chip traegt
    aria-current=true plus aria-label "Filter PDF entfernen", Trefferzeile
    nennt unter Sortierung das Datum im Accessible Name. Der echte
    Screenreader-Durchgang bleibt dem Owner.
15. BESTANDEN (gemessen, hoher Kontrast offen): dunkles Theme per occ
    aktiviert; Kontraste: Chip 15.04:1, aktiver Chip 8.47:1, aktiver
    Sortierlink 15.04:1, Trefferzeile 15.04:1, Datumszeile 6.29:1, alles
    ueber 4.5:1. Aktiver Chip ist ohne Farbe erkennbar: x-Icon (svg) plus
    anderer Rahmen. Der Modus "hoher Kontrast" wurde nicht emuliert, bleibt
    dem Owner.
16. BESTANDEN MIT ERKLAERUNG (gemessen): bei 390px brechen die Chips in drei
    Zeilen um, kein waagerechtes Scrollen (scrollWidth 390 = Viewport). Die
    44px-Mindesthoehe haengt an "@media (pointer: coarse)", nicht an der
    Breite: am Desktop-Browser messen die Chips 34px, auf Touch-Geraeten
    greift die 44px-Regel. Das weicht vom Wortlaut der Probe ab (Breite),
    trifft aber ihren Zweck (Touch-Ziele); Einordnung als "erklaert", der
    Owner nimmt die Bauform mit ab.
17. BESTANDEN MIT NEBENBEFUND (gemessen): DE, EN (alle 10 Chips, 3
    Sortierlinks, Zuruecksetzen, Leerzustand uebersetzt, null deutsche Reste
    im EN-Lauf) und FR komplett; "Feuilles de calcul" (134px breit) bricht
    die Leiste bei 390px nicht, kein Text abgeschnitten. NEBENBEFUND: der
    Gruppenname der Unified Search, "File contents" aus
    php/lib/Search/Provider.php:108, fehlt als einziger t()-Schluessel in
    allen drei Katalogen (Gegenprobe ueber alle 146 t()-Strings des
    PHP-Teils gegen de.json: genau 1 Treffer). Die Gruppe erscheint deshalb
    in jedem nicht-englischen UI englisch. Kein Phase-13-Schluessel
    (Bestand vor der Phase), Behebung als kleiner Folge-Commit moeglich;
    franzoesischer Wortlaut faellt unter den bekannten Checkpoint-Punkt 1.

Dialog-Probe zu FILT-03: BESTANDEN (gemessen): im Unified-Search-Dialog
"Genehmigung" gesucht, Datumsfilter "Dieses Jahr" gesetzt: die
Findling-Gruppe bleibt mit Treffern stehen statt zu verschwinden.

Die sieben Entscheidungen an der laufenden Seite:

- D-01 WIEDERGEFUNDEN: types=pdf,images kombiniert zwei Gruppen, das
  Backend-Feld ist eine Liste (Adresse traegt die Aufzaehlung).
- D-02 WIEDERGEFUNDEN: Chip-Leiste ueber der Trefferliste, alle sechs
  Typ-Chips auch im gefilterten Zustand sichtbar, alles serverseitige Links.
- D-03 WIEDERGEFUNDEN: drei Sortierlinks als Segmentschalter, aktiver per
  aria-current und active-Klasse hervorgehoben, ein Klick wechselt sofort.
- D-04 WIEDERGEFUNDEN: Datumszeile je Treffer NUR unter Datums-Sortierung,
  nirgends ein Relevanzwert.
- D-05 WIEDERGEFUNDEN: vier Schnellbereiche als Link-Chips, keine freien
  Datumsfelder; der Dialog-Datumsfilter wirkt (FILT-03-Probe).
- D-06 WIEDERGEFUNDEN: aktive Chips hervorgehoben mit x (svg + aria-label
  "Filter ... entfernen"), Zuruecksetzen-Link nur bei mindestens einem
  aktiven Filter.
- D-07 WIEDERGEFUNDEN: eigener Leerzustand bei 0 Treffern unter aktivem
  Filter, mit Link auf dieselbe Suche ungefiltert, die wieder liefert.

OFFEN FUER DIE ABNAHME durch den Owner (Resume-Signal "abgenommen"):
der echte Nur-Tastatur- und Screenreader-Durchgang (13, 14), hoher Kontrast
(15), ein echtes Touch-Geraet oder die Bewertung der pointer-coarse-Bauform
(16), ein Lauf mit abgeschaltetem JavaScript (12), die Mitternachtsprobe (9),
der volle Paraphrasen-Fall auf einer Instanz mit Vektorbestand (4), dazu die
zwei bekannten Checkpoint-Punkte oben und der Nebenbefund "File contents".

## Nachtrag 19.09.: Abnahme-Session, vier Proben per Browser-Automation nachgezogen

Auf Wunsch des Owners wurden die vier automatisierbaren Restproben per
Playwright an der laufenden Instanz gefahren (Port 8090, testuser). Damit
steigen die Proben 12, 13, 15 und 16 von "strukturell bestanden" auf
"gemessen bestanden":

- Probe 13 (Tastatur): BESTANDEN. Reiner Tab-Durchgang protokolliert:
  Reihenfolge Suchfeld-Bereich, dann PDF, Dokumente, Tabellen,
  Praesentationen, Bilder, Text, Heute, Letzte 7 Tage, Letzte 30 Tage,
  Dieses Jahr, Relevanz, Zuletzt geaendert, Aelteste zuerst, erste
  Trefferzeile. Genau ein Stopp je Chip, sichtbarer Fokus-Umriss auf jedem
  der 14 Bedienelemente und der Trefferzeile, Enter aktiviert den
  fokussierten Chip (Adresse traegt danach types=pdf).
- Probe 15 (hoher Kontrast): BESTANDEN, jetzt inklusive forced-colors.
  Unter emuliertem forced-colors: active ist der aktive Chip ohne Farbe
  erkennbar (x-Icon sichtbar, Rahmen), Text in Systemfarben lesbar. Das
  dunkle Theme war bereits am 18.09. gemessen (alle Kontraste ueber 4.5:1).
- Probe 12 (ohne JavaScript): BESTANDEN. Mit per CDP abgeschalteter
  Script-Ausfuehrung wurden alle fuenf Bedienwege real gefahren: Chip
  (types=pdf), Sortierlink (sort=newest, 25 Datumszeilen), Blaettern
  (page=2 mit cursors und fp), Alle Filter zuruecksetzen, und das
  GET-Formular (query=Beendigung, 2 Treffer). EINORDNUNG: Nextclouds
  eigener noscript-Hinweis ("Diese Anwendung benoetigt JavaScript zum
  ordnungsgemaessen Betrieb...") legt sich als Overlay ueber die Seite und
  faengt Mausklicks ab; per Tastatur ist alles voll bedienbar. Das ist
  Verhalten der Nextcloud-Shell, nicht der App; die Findling-Seite selbst
  braucht nachweislich kein JavaScript.
- Probe 16 (Touch): VOLL BESTANDEN, der Erklaer-Punkt vom 18.09. entfaellt.
  In einem echten Mobil-Kontext (isMobile plus hasTouch, 390px, pointer:
  coarse greift) messen alle zehn Chips exakt 44px Mindesthoehe, brechen in
  drei Zeilen um, kein waagerechtes Scrollen.

Damit verbleiben fuer die Abnahme durch den Owner nur noch: der echte
Screenreader-Durchgang (Probe 14; der Accessibility-Baum mit Gruppennamen,
aria-current und "Filter PDF entfernen" ist als maschineller Beleg
protokolliert), die Mitternachtsprobe (9), die Bewertung des
Paraphrasen-Restfalls (4, Vektorbestand), die zwei bekannten Punkte
(franzoesische Wortlaute, drittes Paritaetsszenario) und der Nebenbefund
"File contents".

## Nachtrag 19.09. Vormittag: Mitternachtsprobe gefahren, Restfall eingeordnet, Nebenbefund gefixt

Owner-Ansage vom 19.09.: die fuenf offenen Abnahmepunkte direkt abarbeiten.
Stand danach:

- Probe 9 (Mitternachtsfall): BESTANDEN (gemessen). Der Tageswechsel
  18. auf 19.09. war zum Messzeitpunkt (~10:00 Ortszeit) vollzogen, die
  Probe prueft genau die Tagesgrenze und braucht dafuer nicht die Uhrzeit
  00:00. Beide Richtungen belegt: (a) mitternacht-probe-19-09.txt per
  WebDAV hochgeladen (201), nach der Indexierung erscheint sie unter
  range=today; (b) kuendigungsfrist-probe.txt vom 18.09. erscheint unter
  range=today NICHT mehr (0 Treffer im HTML), waehrend range=year sie
  weiter fuehrt (3 Treffer, die Datei ist also da und indexiert, nur eben
  nicht mehr "heute").
- Probe 4 (Paraphrasen-Restfall): per Owner-Ansage vom 19.09. als
  ausreichend belegt angenommen: der CI-Beweis (index-search-e2e) plus der
  Ein-Datei-Beweis unter Filter an dieser Instanz stehen, der volle Fall
  ("Seite voll besetzt") laeuft auf der Phase-15-Box mit Vektorbestand
  ab Werk mit.
- Nebenbefund "File contents": GEFIXT als Folge-Commit. Der Schluessel
  steht jetzt in allen sechs Katalogen (de/de_DE/fr, je .json und .js),
  DE "Dateiinhalte", FR "Contenu des fichiers"; das Katalog-Zahlengate in
  backend/tests/test_admin_ui_contract.py ist auf 198 angehoben und traegt
  den verlangten Herkunftsabsatz. Der franzoesische Wortlaut faellt
  weiterhin unter den Checkpoint-Punkt der ungeprueften franzoesischen
  Wortlaute.

Damit liegen beim Owner nur noch die zwei Bewertungen: Screenreader-Probe 14
(A11y-Baum als maschineller Beleg protokolliert; wahlweise eigener
Narrator-Lauf: Win+Strg+Enter, ueber die Filterleiste) und die zwei bekannten
Punkte (23 franzoesische Wortlaute ungeprueft, Wegnahme-Bauform des dritten
Paritaetsszenarios). Danach fehlt nur das Wort "abgenommen".

## Nachtrag 19.09. Mittag: Owner-Abnahme erteilt, Phase 13 geschlossen

Der Owner hat in der Abnahme-Session vom 19.09. die drei letzten offenen
Bewertungen entschieden:

- Probe 14 (Screenreader): der protokollierte A11y-Baum reicht als Beleg,
  ein eigener Narrator-Durchgang ist nicht verlangt.
- Die 23 franzoesischen Wortlaute der Leiste plus "Contenu des fichiers"
  (Nebenbefund-Fix vom Vormittag): abgenommen wie vorgelegt, gegen die
  EN/DE/FR-Tabelle des Copywriting-Contracts; Nachtrag in
  docs/l10n-french.md.
- Wegnahme-Bauform des dritten Paritaetsszenarios: abgenommen; das
  Zwei-Dateitypen-Fixture bleibt als moegliche spaetere Erweiterung
  notiert, kein Nachtrag der Phase.

Damit sind alle 17 Sichtproben, die FILT-03-Dialogprobe und D-01 bis D-07
bestanden oder abgenommen, Task 2 ist erfuellt, FILT-01 bis FILT-05 stehen
auf Complete und die Phase ist geschlossen (STATE, ROADMAP, REQUIREMENTS
in diesem Commit).

## Issues Encountered

Keine ueber die Befunde hinaus.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Task 2 (Owner-Checkpoint) ist der einzige offene Schritt der Phase; danach
  koennen FILT-01 bis FILT-05 in `.planning/REQUIREMENTS.md` als erfuellt
  markiert werden, nicht frueher.
- Der erste CI-Lauf nach dem Merge zeigt die Paritaetsszenarien 11 bis 13; die
  zwei zuerst anzusehenden Punkte stehen in 13-12-SUMMARY.
- MESS-05 (Messung auf grossem Bestand) ist der Phase-15-Anfahrt zugeordnet.

---
*Phase: 13-filter-und-sortierung-auf-der-ergebnisseite*
*Completed: 2026-09-18 (Task 1; Task 2 offen)*

## Self-Check: PASSED

- `backend/tests/test_query_rewrite.py` FOUND
- Commit `98fa6d7` FOUND
- Gate-Kette in einem Zug nachgefahren: GRUEN (2128 passed, 15 skipped)
- Verify-Block sinnwahrend: GRUEN; woertlich: rot am isReadable-grep (Befund 1)
- "D-07" und "Sichtprobe" stehen in dieser Datei, wie must_haves es verlangt
