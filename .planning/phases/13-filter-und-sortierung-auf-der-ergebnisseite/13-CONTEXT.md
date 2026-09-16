# Phase 13: Filter und Sortierung auf der Ergebnisseite - Context

**Gathered:** 2026-09-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Nutzer grenzen Treffer auf der eigenen Ergebnisseite nach Dateityp-Gruppen und
Zeitraum ein und sortieren nach Datum, ohne dass die semantische Suchhaelfte
oder die Rechtegrenze verloren geht. Requirements: FILT-01 bis FILT-05.
Verbindliche Bauordnung: Backend-Felder (SearchRequest/SnippetsRequest,
candidates-Pfad) VOR der PHP-Oberflaeche. Die Ergebnisseite bleibt
serverseitig gerendert, ohne Vue, ohne Build-Schritt, ohne neue JSON-Route
(Phase-9-Muster).

</domain>

<decisions>
## Implementation Decisions

### Filter-Bedienung (Typgruppen)
- **D-01:** Mehrfachauswahl der sechs Typgruppen (PDF, Dokumente, Tabellen,
  Praesentationen, Bilder, Text). Mehrere Gruppen sind kombinierbar
  (z.B. ?types=pdf,images); jeder Chip schaltet seine Gruppe an/aus. Das
  Backend-Feld ist eine Liste.
- **D-02:** Darstellung als Chip-Leiste ueber der Trefferliste, alle sechs
  Gruppen immer sichtbar, als serverseitige Links ohne JavaScript (kein
  Dropdown, kein Formular fuer die Typwahl).

### Sortier-Bedienung
- **D-03:** Sortierwahl als drei Textlinks (Segmentschalter): Relevanz
  (Standard) | Zuletzt geaendert | Aelteste zuerst. Aktiver Modus
  hervorgehoben, ein Klick wechselt sofort, serverseitig ohne JavaScript.
- **D-04:** Unter Datums-Sortierung zeigt jeder Treffer sein Aenderungsdatum
  ("Geaendert am ..."). Der Relevanz-Score erscheint unter Sortierung NIE
  (tantivy liefert unter order_by_field den Feldwert statt des Scores;
  Candidate.score ist unter Sortierung 0.0). Unter Relevanz-Sortierung
  bleibt die Trefferdarstellung wie bisher (kein Datum als Zusatzzeile).

### Zeitraumfilter-UI
- **D-05:** Zeitraum auf der Ergebnisseite ueber feste Schnellbereiche als
  Link-Chips (Heute, 7 Tage, 30 Tage, Dieses Jahr) neben den Typ-Chips.
  KEINE freien Datumsfelder, kein Formular in dieser Phase. Der Datumsfilter
  des Unified-Search-Dialogs wird zusaetzlich uebernommen und via
  getSupportedFilters() deklariert (FILT-03); since/until aus der URL werden
  defensiv gelesen und wirken unabhaengig von den Schnellbereichen.

### Aktive Filter und Leerzustand
- **D-06:** Aktive Typ-/Zeitraum-Chips bleiben in der Leiste hervorgehoben und
  tragen ein x zum Einzeln-Entfernen; daneben ein Link "Alle Filter
  zuruecksetzen", der nur bei mindestens einem aktiven Filter erscheint.
  Keine separate Aktiv-Leiste (keine doppelte Information).
- **D-07:** Bei 0 Treffern unter aktivem Filter erscheint ein eigener
  Leerzustand: Hinweis "Keine Treffer mit den aktiven Filtern" plus Link
  "Filter zuruecksetzen", der dieselbe Suche ungefiltert oeffnet.

### Claude's Discretion
- Chip-Reihenfolge, exakte Wortlaute der Labels (dreisprachig EN/DE/FR nach
  bestehendem Katalog-Muster), Icon-Wahl (SVG, keine Emojis), Abstaende und
  Hervorhebungsstil des aktiven Zustands.
- URL-Parameternamen und Kanonisierung (types/sort/since/until o.ae.),
  solange FILT-04 gilt: Filter/Sortierung reisen in der URL, jede Aenderung
  setzt auf Seite 1 zurueck, fremder Cursorpfad wird abgewiesen.
- Genaue Abbildung der sechs UI-Gruppen auf Extensions (EIN Filtervokabular
  fuer UI-Gruppen und die bestehende type:-Textsyntax, nicht zwei).
- Schnellbereichs-Grenzen (Kalender- vs rollierende Fenster), solange
  since/until-Semantik im Backend eindeutig ist.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone-Recherche v1.2 (Pflichtlektuere fuer diese Phase)
- `.planning/research/SUMMARY.md` — Kernbefunde Filter/Sortierung: Filter NIE
  als type:-Text (schaltet Semantik via carried_operators ab); Filter als
  Occur.Must-Klausel VOR dem Fusionsfenster (sonst halbleere Seiten);
  Sortierung ist eigener rein lexikalischer Modus (tantivy order_by_field
  liefert Feldwert statt Score); mtime ist bereits fast=True, kein Reindex.
- `.planning/research/STACK.md` — Integrationsbefund _mtimes_of()/Occur.Must,
  tantivy-0.26.0-Signatur order_by_field/Order/offset.
- `.planning/research/ARCHITECTURE.md` — Nahtstellen: query/rewrite.py::
  build_query(extensions=...), index/search.py::candidates (einziger Ort fuer
  Reihenfolge/Sichtbarkeit), php/lib/Controller/PageController.php (defensiv
  gelesene geschlossene Werte, keine neue Route).
- `.planning/research/PITFALLS.md` — Pitfalls 1-3 (Filter hinter Fusion,
  type:-Text, Sortierung in der Fusion) mit Vermeidungspfaden.

### Requirements und Roadmap
- `.planning/REQUIREMENTS.md` — FILT-01 bis FILT-05 (end-to-end formuliert,
  inkl. extra=forbid-Falle: neue optionale Felder in SearchRequest/
  SnippetsRequest muessen beide Modelle ergaenzen).
- `.planning/ROADMAP.md` — Phase-13-Ziel und 5 Success Criteria.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `index/search.py::candidates` — traegt kuenftig Filterklausel UND
  Sortierzweig; einziger Ort, an dem Reihenfolge und Sichtbarkeit entstehen.
- `query/rewrite.py::build_query` — bekommt extensions=...-Parameter, nutzt
  denselben Occur.Must-Mechanismus wie _mtimes_of() fuer die semantische
  Haelfte; carried_operators bleibt unberuehrt.
- `php/lib/Controller/PageController.php` — Erweiterung um defensiv gelesene
  geschlossene Werte (types, sort, since, until); Phase-9-Ergebnisseite
  serverseitig, Katalog-Schluessel-Muster (EN/DE/FR, 174 Schluessel Stand
  v1.1) fuer neue Labels.
- `lexical_only`-Modus — Vorbild fuer den Sortierzweig (eigener Modus,
  RRF aus, Score 0.0).

### Established Patterns
- Cursor-Pagination mit Pfadbindung: jede Filter-/Sortieraenderung
  invalidiert den Cursor und setzt auf Seite 1; fremde Cursorpfade werden
  abgewiesen (FILT-04).
- Paritaetstest ACL-Vorfilter + finaler PHP-Recheck muss die neuen Parameter
  abdecken (FILT-05); kein gefilterter/sortierter Treffer umgeht die
  Rechtegrenze.
- Pydantic extra=forbid auf Request-Modellen: neue optionale Felder muessen
  in SearchRequest UND SnippetsRequest ergaenzt werden, sonst 422.
- Vokabular-Gate public: "archiv" in oeffentlichen Artefakten verboten.

### Integration Points
- getSupportedFilters() im Unified-Search-Provider: Datumsfilter deklarieren,
  damit Findling-Treffer bei gesetztem Datumsfilter nicht mehr stumm
  verschwinden (FILT-03).
- Tantivy-Schema unveraendert: ext (Term) und mtime (Fast-Field) existieren
  seit v1.0 (index/schema.py:105/114) — kein Reindex, keine Migration der
  Indexstruktur; die 1.2.0-Versionsmigration ist Phase-16-Thema.

</code_context>

<specifics>
## Specific Ideas

- Sechs Typgruppen sind eine geschlossene Liste; keine Trefferzaehler je Typ
  (waere Zaehl-Orakel vor dem Rechtefilter, T-02-93).
- Eine Paraphrasensuche findet unter aktivem Filter dasselbe Dokument wie
  ohne Filter (Success Criterion 1) — der Beweis, dass die Semantik unter
  Filter aktiv bleibt.
- Gleiche Zeitstempel sortieren stabil ueber file_id als Zweitschluessel.

</specifics>

<deferred>
## Deferred Ideas

- Freie Datumsfelder (von/bis-Formular) auf der Ergebnisseite — erst wenn die
  Schnellbereiche nachweislich nicht reichen (v1.x).
- Sortierung nach Name oder Groesse — neues Fast-Field, SCHEMA_VERSION-
  Sprung, Vollreindex; ausdruecklich v2+.
- Facettenzaehler je Dateityp — ausgeschlossen (Zaehl-Orakel, T-02-93).
- Mimetype-Gruppen aus files.mime statt ext — v1.x, falls Genauigkeit
  wichtiger wird als "no join against files".
- Personenfilter, Ordner-Einschraenkung — eigene Phasen.

</deferred>

---

*Phase: 13-filter-und-sortierung-auf-der-ergebnisseite*
*Context gathered: 2026-09-16*
