# Phase 28: Abnahme-Anfahrt - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md; this log preserves the alternatives considered.

**Date:** 2026-09-29
**Phase:** 28-abnahme-anfahrt
**Areas discussed:** Kostendeckel und Abbruch, Boxen und Profile je Zelle, Messumfang je Zelle, Rückfluss in Formel (SC4)

---

## Kostendeckel und Abbruch

| Option | Description | Selected |
|--------|-------------|----------|
| Rechenblatt + 30 % Reserve | Deckel aus dem Rechenblatt nach Messumfang plus 30 % Puffer, Freigabe vor Boxstart | ✓ |
| Fest 25 USD | Harte Obergrenze, Umfang wird angepasst | |
| Fest 50 USD | Etwa das halbe Guthaben | |

| Option | Description | Selected |
|--------|-------------|----------|
| Stopp + Rückfrage | Laufende Zelle fertig, keine neue, Box bleibt bis Owner-Wort | ✓ |
| Harter Stopp + Abbau | Sofort abbauen, fehlende Zellen ungemessen | |
| Warnung bei 80 % | Rückfrage bei 80 %, harter Stopp bei 100 % | |

**User's choice:** jeweils die Empfehlung.

---

## Boxen und Profile je Zelle

| Option | Description | Selected |
|--------|-------------|----------|
| m7g.large wie bisher | Gleiche Box wie die Store-Messung | ✓ |
| Ohne eigene Referenzbox | Sparsam nur auf Matrix-Boxen | |

| Option | Description | Selected |
|--------|-------------|----------|
| Alle 3, Probe entscheidet | Probe je Stufe, Verdikt gegen Messung | ✓ |
| Nur passende Stufe | Nur das vorgeschlagene Profil | |
| Alle 3 ohne Probe | Per occ erzwingen | |

| Option | Description | Selected |
|--------|-------------|----------|
| c7a, 2 GB/Kern | Nah an Selfhost-Hardware, günstiger | ✓ |
| m7a, 4 GB/Kern | Mehr Luft, teurer | |
| Gemischt | 4K/8K c7a, 16K/32K m7a | |

**User's choice:** jeweils die Empfehlung.

---

## Messumfang je Zelle

| Option | Description | Selected |
|--------|-------------|----------|
| Teilkorpus fest + 1 Volllauf | ~5.000 OCR-lastige Docs je Zelle, voller Korpus nur Sparsam auf Referenzbox | ✓ |
| Voller Korpus überall | 52k je Zelle, ~35 bis 45 USD | |
| Nur Zeitfenster | Feste Zeit je Zelle, hochgerechnet | |

| Option | Description | Selected |
|--------|-------------|----------|
| Ja, auf 2 Zellen | Standard+fp32 auf knapper und großzügiger Box | ✓ |
| Ja, überall wo möglich | Jede Standard/Leistung-Zelle zusätzlich fp32 | |
| Nein | nur automatisiert | |

**User's choice:** jeweils die Empfehlung.

---

## Rückfluss in Formel (SC4)

| Option | Description | Selected |
|--------|-------------|----------|
| Formel nachziehen, Owner je Fall | Messwerte ersetzen Schätzwerte, Toleranz +10 %, Streichung je Fall | ✓ |
| Automatisch streichen | Stufe > +10 % wird nicht angeboten | |
| Nur dokumentieren | Entscheid in Phase 29 | |

**User's choice:** Empfehlung.

---

## Claude's Discretion

- Teilkorpus-Auswahl, Zellen-Reihenfolge, Wahl der beiden fp32-Zellen, Form von Rohdaten und Bericht.

## Deferred Ideas

- WR-04-Rest (no_text_layer), secure-27-Hinweise F-3 und T-27-39: Phase 29.
- Issue #14 Leserwahl: nach Diagnose von budachst.
