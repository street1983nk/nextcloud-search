# Phase 13: Filter und Sortierung auf der Ergebnisseite - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-16
**Phase:** 13-filter-und-sortierung-auf-der-ergebnisseite
**Areas discussed:** Filter-Bedienung, Sortier-Bedienung, Zeitraumfilter-UI, Aktive Filter + Leerzustand

---

## Filter-Bedienung (Typgruppen)

| Option | Description | Selected |
|--------|-------------|----------|
| Mehrfachauswahl | Mehrere Gruppen kombinierbar (?types=pdf,images), Chip schaltet an/aus | ✓ |
| Einzelauswahl | Genau eine Gruppe aktiv (Radio-Muster) | |

| Option | Description | Selected |
|--------|-------------|----------|
| Chip-Leiste | Sechs Chips ueber der Trefferliste, serverseitige Links ohne JavaScript | ✓ |
| Dropdown | Kompakter, braucht ohne JS einen Anwenden-Button | |

**User's choice:** Mehrfachauswahl + Chip-Leiste (beide Empfehlungen)
**Notes:** keine

---

## Sortier-Bedienung

| Option | Description | Selected |
|--------|-------------|----------|
| Drei Textlinks | Segmentschalter Relevanz / Zuletzt geaendert / Aelteste zuerst, No-JS | ✓ |
| Dropdown mit Anwenden | Select plus Button | |

| Option | Description | Selected |
|--------|-------------|----------|
| Datum je Treffer | Unter Datums-Sortierung zeigt jeder Treffer sein Aenderungsdatum | ✓ |
| Datum immer anzeigen | Aenderungsdatum in allen Sortiermodi | |
| Nichts Zusaetzliches | Nur Reihenfolge aendert sich | |

**User's choice:** Drei Textlinks + Datum je Treffer unter Datums-Sortierung (beide Empfehlungen)
**Notes:** Score erscheint unter Sortierung nie (tantivy-order_by_field-Befund)

---

## Zeitraumfilter-UI

| Option | Description | Selected |
|--------|-------------|----------|
| Schnellbereiche als Chips | Heute / 7 Tage / 30 Tage / Dieses Jahr als Link-Chips, kein Formular | ✓ |
| Freie Datumsfelder | von/bis-Formular mit Anwenden-Button | |
| Beides | Schnellbereiche plus aufklappbare Datumsfelder | |

**User's choice:** Schnellbereiche als Chips (Empfehlung)
**Notes:** Unified-Search-Datumsfilter wird zusaetzlich uebernommen (FILT-03); freie Datumsfelder als Deferred Idea festgehalten

---

## Aktive Filter + Leerzustand

| Option | Description | Selected |
|--------|-------------|----------|
| Aktive Chips + Alle zuruecksetzen | Aktive Chips hervorgehoben mit x, Link nur bei aktiven Filtern | ✓ |
| Separate Aktiv-Leiste | Zusaetzliche Zeile "Aktive Filter: ..." | |

| Option | Description | Selected |
|--------|-------------|----------|
| Hinweis + Entfernen-Link | Eigener Leerzustand mit "Filter zuruecksetzen"-Link | ✓ |
| Standard-Leerzustand | Wie Suche ohne Treffer | |

**User's choice:** Aktive Chips mit x + eigener Leerzustand (beide Empfehlungen)
**Notes:** keine

---

## Claude's Discretion

- Chip-Reihenfolge, Label-Wortlaute (EN/DE/FR), SVG-Icons, Hervorhebungsstil
- URL-Parameternamen und Kanonisierung
- Abbildung der sechs UI-Gruppen auf Extensions (EIN Vokabular mit type:-Syntax)
- Schnellbereichs-Grenzen (Kalender- vs rollierende Fenster)

## Deferred Ideas

- Freie Datumsfelder (von/bis-Formular) — v1.x
- Sortierung nach Name/Groesse — v2+ (Fast-Field, Reindex)
- Facettenzaehler je Dateityp — ausgeschlossen (T-02-93)
- Mimetype-Gruppen aus files.mime — v1.x
- Personenfilter, Ordner-Einschraenkung — eigene Phasen
