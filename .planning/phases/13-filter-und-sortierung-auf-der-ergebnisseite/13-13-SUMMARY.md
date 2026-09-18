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

requirements-completed: []  # FILT-01 bis FILT-05 werden erst nach der Owner-Freigabe (Task 2) markiert

duration: 25min
completed: 2026-09-18
---

# Phase 13 Plan 13: Gesamtlauf, Audit-Durchgang und die offene Abnahme Summary

**Alle sechs Gate-Stufen laufen in einem Zug gruen (2128 passed, 15 vorbestehende Umgebungs-Skips), der Security-, Bug- und Performance-Durchgang ist gefahren mit vier Befunden (zwei behoben per neuem Testfall, zwei erklaert), und die 17 Sichtproben samt D-01 bis D-07 warten als Task 2 auf den Owner an der laufenden Instanz.**

## Performance

- **Duration:** 25 min (Task 1)
- **Started:** 2026-09-18T16:05:12Z
- **Completed:** 2026-09-18T16:30:00Z (Task 1; Task 2 offen)
- **Tasks:** 1 von 2 (Task 2 ist der Owner-Checkpoint)
- **Files modified:** 1

## Status der beiden Tasks

| Task | Stand |
|---|---|
| Task 1: Gesamtlauf aller Gates und Audit-Durchgang | ABGESCHLOSSEN |
| Task 2: Die 17 Sichtproben an der laufenden Instanz | OFFEN, wartet auf den Owner (checkpoint:human-verify, Resume-Signal "abgenommen") |

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

## Die 17 Sichtproben: OFFEN (Task 2, Owner)

Die 17 Abnahme-Sichtproben aus 13-UI-SPEC (Abschnitt "Abnahme-Sichtproben")
plus die Dialog-Probe zu FILT-03 sind NICHT gelaufen: sie brauchen die laufende
Instanz nach `docs/dev-setup.md` (Port 8090, `testuser` und `kollegin`,
Testkorpus), und auf dieser Maschine ist die Docker-Engine aus. Jede
Sichtprobe wird bei der Abnahme hier mit ihrem Ergebnis nachgetragen, ebenso
das namentliche Abhaken der sieben Entscheidungen D-01, D-02, D-03, D-04,
D-05, D-06 und D-07 an der laufenden Seite. Bis dahin gilt: maschinell ist
alles gruen, was maschinell pruefbar ist; was nur an der Seite faellt
(Tastatur, Screenreader, dunkles Theme, hoher Kontrast, Handybreite,
Mitternacht, drei Sprachen), steht aus.

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
