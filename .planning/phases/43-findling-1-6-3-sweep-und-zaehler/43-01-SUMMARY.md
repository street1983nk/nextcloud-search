---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 01
subsystem: l10n / Admin-Seite (Texte)
tags: [texte, owner-freigabe, l10n, deckungsgrad]
requires: []
provides:
  - "Freigegebene Wortlaute EN/DE/FR für Hinweis H, Zählsatz Z, Satz U und Rückfallsatz L in 43-TEXTE.md (Maschinenzeilen für 43-06)"
affects: [43-06]
tech-stack:
  added: []
  patterns: ["Owner-Freigabe vor Katalogänderung, Maschinenzeilen als Quelle für zeichengleiche Übernahme"]
key-files:
  created:
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-TEXTE.md
  modified: []
decisions:
  - "Owner-Freigabe 'Go' am 2026-11-07: H Variante (b), Z (a), U (a), L (a)"
  - "Kein eigener L-missing-Satz, das Versionsbanner findling-banner-lockstep deckt den Fall Backend 1.6.2 ab"
  - "Französische Leerzeichen vor : ; ? ! nach docs/l10n-french.md (einfaches Leerzeichen); die neuen Sätze enthalten diese Zeichen nicht"
metrics:
  duration: "etwa 2 h (inklusive Wartezeit auf die Owner-Antwort)"
  completed: 2026-11-07
---

# Phase 43 Plan 01: Wortlaute zur Freigabe Summary

Vier neue Sätze für den Abschnitt "Deckungsgrad der Suche" (einmaliger Hinweis zur Zählung pro Dokument mit 7-Tage-Regel, Zählsatz, Satz zu nicht lesbaren Dateien, Rückfallsatz über den Grenzen) in DE/EN/FR entworfen, mit den Glossarbegriffen abgeglichen und vom Owner mit "Go" freigegeben.

## Tasks

| Task | Name | Commit |
|---|---|---|
| 1 | Textentwürfe DE/EN/FR mit Begründung | 05b8a508 |
| 2 | Owner-Freigabe, Maschinenzeilen gefüllt | 2b9af5d7 |

## Freigabe

- Zitat: "Go", 2026-11-07, Claude Code Terminal (über den Koordinator, auf die Vorlage "wie empfohlen").
- Die zwölf Maschinenzeilen in 43-TEXTE.md sind per Skript aus den Tabellen der empfohlenen Varianten übernommen, also zeichengleich.

## Deviations from Plan

- Gegen die Entwürfe im Plan sind die Begriffe an den Katalogbestand angepasst: "Deckungsgrad" statt "Abdeckung", "externer Speicher ... eingebunden" statt "Freigabe", "Speicherorte", "mehrfach hängen geblieben", FR "peuvent être trouvés par la recherche". Z: "in Kürze" ist ersetzt, weil der Backfill bei großen Instanzen länger dauert. Die Gründe stehen je Block in 43-TEXTE.md, der Owner hat die angepasste Fassung freigegeben.
- Für L-missing gibt es keine Maschinenzeilen, wie der Plan es vorsieht, wenn im Abschnitt schon ein Satz erscheint (Versionsbanner).
- STATE.md und ROADMAP.md sind hier nicht fortgeschrieben, weil parallel 43-02 läuft; das übernimmt der Koordinator.

## Known Stubs

Keine.

## Self-Check: PASSED

- 43-TEXTE.md ist vorhanden, die Prüfung aus Task 2 (Freigabe, Zitat, Datum, zwölf Textzeilen, keine U+2013/U+2014) ist grün.
- Die Commits 05b8a508 und 2b9af5d7 stehen im Log.
