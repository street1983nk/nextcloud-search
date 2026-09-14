# Phase 12: Messwerkzeug, Runbook und Terminentscheid - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-14
**Phase:** 12-messwerkzeug-runbook-und-terminentscheid
**Areas discussed:** stable35-Entscheid, Budget-Grundlage der Anfahrt, Cron-Intervall-Regel, Runbook-Zuschnitt

---

## stable35-Entscheid

| Option | Description | Selected |
|--------|-------------|----------|
| In v1.2.0 heben | v1.2.0 kommt ohnehin; das Release traegt das neue Fenster (max 35) | ✓ |
| Nur dokumentieren | Fenster hebt erst ein spaeteres Release | |
| You decide | Claude entscheidet nach Beweislage | |

| Option | Description | Selected |
|--------|-------------|----------|
| deploy-harp-Strecke auf 35 | NC-35-final-Check plus Fremdinstallations-/Upgrade-Strecke gruen gegen stable35 | ✓ |
| Nur Release-Status pruefen | NC 35 final laut Releases reicht | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Dokumentieren + neuer Termin | Fenster bleibt, naechster RE-CHECK-Termin gesetzt; Phase 12 erfuellt | ✓ |
| Vor Einreichung erneut pruefen (Pflicht) | Re-Check als blockierendes Kriterium in Phase 16 | |
| You decide | | |

**User's choice:** Heben in v1.2.0 bei finalem NC 35; Beweis = deploy-harp gegen stable35; Fallback = dokumentieren + neuer Termin.

---

## Budget-Grundlage der Anfahrt

| Option | Description | Selected |
|--------|-------------|----------|
| Vollkorpus | 52.111 Docs, vergleichbar mit Baseline und v1.1; Deckel muss >= 31 h sein | ✓ |
| Teilkorpus | Billiger, aber eingeschraenkt vergleichbar; braeuchte Werkzeug in Phase 12 | |
| Entscheid vertagen auf Phase 15 | Beide Wege vorbereiten | |

| Option | Description | Selected |
|--------|-------------|----------|
| Deckel-Rechenblatt ins Runbook | Vor jeder Anfahrt neu gerechnet, belegte Zahlbasis fuer die Freigabe | ✓ |
| Nur einmalig | Kein Runbook-Pflichtteil | |

| Option | Description | Selected |
|--------|-------------|----------|
| m7g.large | Identischer Typ = Vergleichbarkeit | ✓ |
| Anderer Typ | | |

**User's choice:** Vollkorpus, Rechenblatt als Runbook-Pflichtteil, m7g.large.

---

## Cron-Intervall-Regel

| Option | Description | Selected |
|--------|-------------|----------|
| Festnageln + protokollieren | Anfahrt setzt Systemcron auf 5 Minuten UND protokolliert | ✓ |
| Nur protokollieren | Ist-Zustand festhalten, nicht veraendern | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Fail-closed im Skript | Vorpruefschritt bricht ab, wenn Intervall nicht stimmt/protokolliert | ✓ |
| Runbook-Checkliste reicht | Manueller Pflichtschritt | |
| You decide | | |

**User's choice:** Festnageln + protokollieren, fail-closed im Skript.

---

## Runbook-Zuschnitt

| Option | Description | Selected |
|--------|-------------|----------|
| Snapshot-Pfad + Verweise | Hauptpfad Wiederaufbau aus snap-03f1d1d9; Neuaufbau nur Verweis | ✓ |
| Beide Pfade voll | Auch Neuaufbau von null ausgearbeitet | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Copy-paste-Bloecke + Pruefpunkte | Nummerierte Kommandobloecke mit erwarteten Ausgaben | ✓ |
| Prosa mit Verweisen | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Abbau + Kostenfuehrung komplett | Abbau-Checkliste, box.env-Pflege, Deckel-Rechenblatt als Pflichtteile | ✓ |
| Nur Aufbau und Messung | | |

**User's choice:** Snapshot-Hauptpfad, Copy-paste-Form, Abbau/Kosten als Pflichtteile.

## Claude's Discretion

- Technischer Zuschnitt der neuen Fremdbestands-Messgroesse (Diagnose-Route, Schwellen-Semantik, 98b anpassen oder ersetzen)
- Design des aws_box.sh-Unterbefehls Volume-aus-Snapshot
- Dokumentationsort/Form des stable35-Entscheids
- Ob der Cron-Fail-closed-Check eigenes Skript oder Schritt in bestehendem Anfahrtskript ist

## Deferred Ideas

- Teilkorpus-Werkzeug (abgelehnt fuer v1.2, Option fuer spaetere Messkampagnen)
- Neuaufbau-von-null-Runbook voll ausarbeiten (erst falls der Snapshot je geloescht wird)
