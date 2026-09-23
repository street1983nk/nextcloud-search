---
phase: 17-owner-tor-und-analyseketten
plan: 04
subsystem: planning
tags: [owner-tor, freigabe, vollzug, tantivy, d-04, lex-01, lex-07]

# Dependency graph
requires:
  - phase: 17-owner-tor-und-analyseketten
    provides: "17-GRUNDSATZ-ENTSCHEID.md aus Plan 17-01 mit den acht ausformulierten Entscheiden"
provides:
  - "Datierter Owner-Vollzug vom 23.09.2026: alle acht Entscheide E-17-1 bis E-17-8 auf Option a"
  - "Das Tor ist OFFEN: Plaene 17-07 (Marken-Lockerung) und 17-08 (Pin-Sprung 0.26.2) sind freigegeben"
  - "Zitierfaehige Zweig-Tabelle im Vollzugsabschnitt, je betroffene Datei die vollziehende Plannummer"
affects: [17-07, 17-08, 18-schema-marken-und-umbauweg, 19-frageseite-freischalten, 20-ui-kataloge, 21-niederlaendische-komposita]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Vollzug nach dem 12-STABLE35-Muster: Datum, gelesener Stand, Zweig je Entscheid, Beleg, Plannummer"

key-files:
  created: []
  modified:
    - ".planning/phases/17-owner-tor-und-analyseketten/17-GRUNDSATZ-ENTSCHEID.md"

key-decisions:
  - "E-17-1 a: Re-Analyse-Umbau aus den gespeicherten Feldern statt Vollreindex"
  - "E-17-2 a: sechs Koerperfelder immer im Schema, FINDLING_LANGUAGES steuert nur die Befuellung"
  - "E-17-3 a: Deutsch und Englisch duerfen abgeschaltet werden"
  - "E-17-4 a: Sprachmenge wird sechster Versionsmerker, als normalisierte Zeichenkette"
  - "E-17-5 a: Kataloge maschinell plus Community-Review mit datiertem Vorbehalt, kein Muttersprachler-Gate"
  - "E-17-6 a: niederlaendische Komposita bleiben im Scope, endgueltiges Tor in Phase 21"
  - "E-17-7 a: Vergleichsregel tantivy_version gelockert, nur die index_format-Haelfte entscheidet"
  - "E-17-8 a: einheitliche Kettenreihenfolge fold frueh fuer alle vier Sprachen, Kenntnis genommen"

patterns-established: []

requirements-completed: []

# Metrics
duration: ca. 15 min
completed: 2026-09-23
---

# Phase 17 Plan 04: Owner-Tor vorgelegt und vollzogen

**Alle acht Entscheide fielen am 23.09.2026 auf Option a; der Vollzugsabschnitt
in `17-GRUNDSATZ-ENTSCHEID.md` ist datiert gefuellt und das Tor fuer die
Plaene 17-07 und 17-08 ist offen.**

## Ablauf

- Task 1 (checkpoint:human-verify, blocking): Die acht Entscheide wurden dem
  Owner in der Arbeitssitzung vom 23.09.2026 einzeln strukturiert vorgelegt,
  E-17-7 als erste Frage (zwei Abfragen zu je vier Entscheiden, jede Option
  mit dem im Dokument ausformulierten Inhalt). Antwort je Entscheid
  woertlich: "a". Keine Aenderungswuensche am Dokument.
- Task 2 (auto): Vollzugsabschnitt gefuellt (Datum 23.09.2026, gelesener
  Stand inkl. Suite-Zahl 2507/15 vom Welle-1-Merge und Stand 17-02/17-03,
  Zweig-Tabelle mit acht Zeilen, Beleg, Datei-zu-Plan-Zuordnung fuer 17-07
  und 17-08). Checklistenschritte 1 bis 3 als erledigt markiert, 4 bis 7
  offen. Beide Optionen jedes Entscheids stehen unveraendert im Dokument
  (`grep -c "^#### Option a:"` weiterhin 8).

## Verifikation

Die automatisierte Pruefkette des Plans lief GRUEN: Datumsformat der
Ueberschrift, acht Vollzugszeilen E-17-1 bis E-17-8, "Vollzogen am" mit
17-07 und 17-08, kein Platzhalter mehr, keine Em-Dashes.

## Wirkung auf Folgeplaene

- 17-07 darf `repo.py` und `test_upgrade_compatibility.py` anfassen
  (Checklistenschritt 4).
- 17-08 faehrt danach `uv lock --upgrade-package tantivy` (Schritt 5),
  Gates (Schritt 6) und die CI-/Doku-Nachzuege (Schritt 7).
- LEX-01 und LEX-07 werden weiterhin erst gemeldet, wenn die vollziehenden
  Plaene geliefert haben; dieser Plan meldet bewusst kein Requirement als
  erfuellt.
