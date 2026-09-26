# Phase 23: Haertung und Store-Einreichung 1.3.0 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md , this log preserves the alternatives considered.

**Date:** 2026-09-26
**Phase:** 23-haertung-und-store-einreichung-1-3-0
**Areas discussed:** Kaltstart-Fix V-22-01/02, Alte gone-Zeilen (Issue #14), Release-Text-Zuschnitt, Haertungs-Umfang

---

## Kaltstart-Fix V-22-01/02

| Option | Description | Selected |
|--------|-------------|----------|
| In 1.3.0 fixen | Bekannter Produktbefund seit 10.09., trifft jeden Selfhoster mit Schalter 0 bei jedem Neustart; Fix + Test + Nachmessung in Phase 23 | ✓ |
| Nur dokumentieren, v1.4 | 1.3.0 bleibt schlank, Fix reist mit v1.4 (BL-F04) | |
| Nur V-22-02 (Einwortregel) | Kleiner Fix nur auf /snippets, allgemeiner Fall wartet | |

**User's choice:** In 1.3.0 fixen (Empfehlung uebernommen)

| Option | Description | Selected |
|--------|-------------|----------|
| Lexikalisch sofort + Hintergrundladen | Erste Suche antwortet rein lexikalisch unter dem Deckel, Gewichte laden im Hintergrund; nie 0 Treffer, RAM bleibt lazy | ✓ |
| Vorwaermen beim Start | Gewichte laden direkt nach Containerstart; ~250-400 MB RAM ab Start, bricht Lazy-Load-Prinzip | |
| Du entscheidest | Claude waehlt in der Planung | |

**User's choice:** Lexikalisch sofort + Hintergrundladen (Empfehlung uebernommen)

---

## Alte gone-Zeilen (Issue #14)

| Option | Description | Selected |
|--------|-------------|----------|
| Reparaturlauf beim Upgrade | 1.3.0-Migration reiht alle skipped(gone)-Eintraege einmalig neu ein; neuer Code sortiert korrekt | ✓ |
| Liegen lassen + dokumentieren | Doku nennt den manuellen Rescan-Weg | |
| Nur betroffene neu einreihen | Nur gone-Eintraege in Team-Folder-Mounts; gezielter, aber aufwaendiger | |

**User's choice:** Reparaturlauf beim Upgrade (Empfehlung uebernommen)

---

## Release-Text-Zuschnitt

| Option | Description | Selected |
|--------|-------------|----------|
| Changelog + Issue-Antwort | Changelog-Zeile mit Dank an budachst + Verweis #14; nach Release Antwort im Issue; Store-Kurztext frei davon | ✓ |
| Nur Changelog | Keine weitere Kommunikation im Issue | |
| Auch im Store-Text | Zusaetzlich ein Satz im Store-Beschreibungstext | |

**User's choice:** Changelog + Issue-Antwort (Empfehlung uebernommen)

| Option | Description | Selected |
|--------|-------------|----------|
| Alle 4 Punkte als Kurzliste | Block "Known limitations" mit vier knappen Zeilen im Store-Text, identisch in der Doku | ✓ |
| Ein Satz + Doku-Link | Sammelsatz mit Link, Details nur in der Doku | |

**User's choice:** Alle 4 Punkte als Kurzliste (Empfehlung uebernommen)

---

## Haertungs-Umfang

| Option | Description | Selected |
|--------|-------------|----------|
| Security voll, Rest gezielt | Security-Audit ueber die ganze App; Bug/Performance gezielt auf die seit 1.2.0 geaenderten Pfade | ✓ |
| Alles voll wiederholen | Alle drei Audits ueber die komplette App | |
| Du entscheidest | Claude legt die Tiefe im Plan fest | |

**User's choice:** Security voll, Rest gezielt (Empfehlung uebernommen)

---

## Claude's Discretion

- Mechanik des Hintergrundladens und Nachweis (Test + CI-Nachmessung)
- Zuschnitt des Reparaturlaufs (Migrationsschritt vs. Startup-Job), idempotent
- HART-04-Weg (Pin entfernen oder belegen, numpy)
- Reihenfolge der Haertungsschritte, E2E nach probe-92d-Muster
- Kleine Doku-Befunde mitnehmen (21-04: 41,9 statt 42,1 MB)

## Deferred Ideas

- BL-F04 Erstindex-Beschleunigung bleibt v1.4 (budachsts Beschleunigungsfrage reist dort)
- Nach-v1.3-Liste der ROADMAP unveraendert (FR-Koerperfeld, pt_BR/pt_PT, NL-Akzente, Sortierung, Mimetype-Gruppen, Pro-Schiene)
