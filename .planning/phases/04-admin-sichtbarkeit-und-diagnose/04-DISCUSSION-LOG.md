# Phase 4: Admin-Sichtbarkeit und Diagnose - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-02
**Phase:** 04-admin-sichtbarkeit-und-diagnose
**Areas discussed:** UI-Ort und Technik, Fehlerliste + Pro-Datei-Diagnose, Vorab-Schätzung, Toggle-Mechanik

---

## UI-Ort und Technik

| Option | Description | Selected |
|--------|-------------|----------|
| NC-Admin-Settings | Sektion "Findling" in den Verwaltungseinstellungen via ISettings der Companion-App, PHP proxied /status | ✓ |
| Eigene ExApp-Seite | AppAPI ui.top_menu direkt aus dem Container | |
| Beides | Settings-Einstieg plus ExApp-Vollseite | |

**User's choice:** NC-Admin-Settings (Empfohlen)

| Option | Description | Selected |
|--------|-------------|----------|
| Vanilla JS | PHP-Template + fetch + NC-CSS, kein npm/Build-Step | ✓ |
| Vue 3 + @nextcloud/vue | NC-Hausstil, aber Node-Toolchain im bisher build-freien PHP-Repo | |
| Du entscheidest | Claude wählt beim Planen | |

**User's choice:** Vanilla JS (Empfohlen)

---

## Fehlerliste + Pro-Datei-Diagnose

| Option | Description | Selected |
|--------|-------------|----------|
| Pfade PHP-seitig | Container nur fileids (Privacy-Grundsatz status.py), PHP löst zur Anzeigezeit auf | ✓ |
| Nur IDs in der Liste | Pfad erst bei Klick einzeln aufgelöst | |
| Du entscheidest | | |

**User's choice:** Pfade PHP-seitig (Empfohlen)

| Option | Description | Selected |
|--------|-------------|----------|
| Pfad ODER fileid | Ein Feld akzeptiert beides, Fehlerliste verlinkt in die Diagnose | ✓ |
| Nur Pfad-Eingabe | | |
| Datei-Picker | Deckt Fremd-Nutzer-Dateien nicht ab | |

**User's choice:** Pfad ODER fileid (Empfohlen)

---

## Vorab-Schätzung

| Option | Description | Selected |
|--------|-------------|----------|
| Autostart + Info | Erstindex startet von selbst, Schätzung als Metadaten-Scan ab Minute 1 informativ | ✓ |
| Karenzfenster | Start nach z.B. 15 Minuten, Admin kann vorher anpassen | |
| Admin bestätigt | Widerspricht Zero-Config | |

**User's choice:** Autostart + Info (Empfohlen)

---

## Toggle-Mechanik

| Option | Description | Selected |
|--------|-------------|----------|
| Ja, aktiv räumen | Nächster Lauf/Reconcile entfernt Bestand unter dem Ausschluss | ✓ |
| Nur künftig | Bestand bleibt bis zur nächsten Änderung | |
| Du entscheidest | | |

**User's choice:** Ja, aktiv räumen (Empfohlen)

| Option | Description | Selected |
|--------|-------------|----------|
| Pfad-Präfixe | Liste von Ordner-Pfaden, Präfix-Match, keine Glob-/Regex-Falle | ✓ |
| Glob-Muster | Mächtiger, Fehlbedienungsrisiko | |
| Präfixe + Ordnername-Blacklist | Zusätzlich "überall ausschließen wenn Ordner so heißt" | |

**User's choice:** Pfad-Präfixe (Empfohlen)

## Claude's Discretion

- Settings-Transport PHP→Container, Cache-Invalidierung
- Schätz-Heuristik-Details, UI-Polling-Kadenz
- Fehlerlisten-Pagination/Sortierung/Obergrenzen
- Zuschnitt der neuen ExApp-Routen und Schemas
- occ-Kommando als optionaler Zweitzugang

## Deferred Ideas

Keine. (Außerhalb der Phase am selben Tag erledigt: Dependabot-PRs #4/#5 gemergt, GitHub-Ruleset protect-main angelegt.)
