# Phase 22: Messanfahrt BL-F03 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md , this log preserves the alternatives considered.

**Date:** 2026-09-25
**Phase:** 22-Messanfahrt BL-F03
**Areas discussed:** Deckel und Abbruchregel, B4-Entscheidungsregel, disjunction_max-Folge, Zeitnot-Prioritaet

---

## Deckel und Abbruchregel

| Option | Description | Selected |
|--------|-------------|----------|
| 24 h / ~3,00 USD | Rechenwert 11-17 h plus ~40% Reserve, keine Nachfreigabe mitten in der Anfahrt noetig | ✓ |
| 18 h / ~2,25 USD (knapp) | Nah am Rechenwert, Wiederholungen riskieren Unterbrechung | |
| 34 h / ~4,00 USD (grosszuegig) | Rund das Doppelte, Muster v1.2 | |

**User's choice:** 24 h / ~3,00 USD

| Option | Description | Selected |
|--------|-------------|----------|
| Harter Stopp + Bericht | Box haelt beim Deckel, Luecken dokumentiert, Owner entscheidet ueber Nachfreigabe | ✓ |
| Rueckfrage bei 80% | Meldung bei 19 h mit Prognose, Live-Entscheid | |
| Weiterfahren bis fertig | Deckel nur Prognose | |

**User's choice:** Harter Stopp + Bericht

---

## B4-Entscheidungsregel

| Option | Description | Selected |
|--------|-------------|----------|
| B4 fahren | Auch im CI-Kurven-Zwischenbereich 1,5-3,0; Verlauf ab 8 Kernen entscheidet den v1.4-Profilschnitt, Kosten ~1 USD | ✓ |
| B4 streichen | Nur >=3-Schwelle rechtfertigt den Typwechsel | |
| Am Messtag vorlegen | CI-Kurve mit Empfehlung, Owner entscheidet vor der Anfahrt | |

**User's choice:** B4 fahren (Faktor >= 1,5 heisst fahren; nur darunter entfaellt B4)

---

## disjunction_max-Folge

| Option | Description | Selected |
|--------|-------------|----------|
| In Phase 22 umsetzen | Kriterium 4 woertlich; CI-beweisbar ohne neue Box-Anfahrt, Phase 23 haertet den Endstand | ✓ |
| An Phase 23 uebergeben | Phase 22 bleibt reine Messphase | |
| Am Messergebnis entscheiden | Checkpoint mit Aufwandsschaetzung | |

**User's choice:** In Phase 22 umsetzen

---

## Zeitnot-Prioritaet

| Option | Description | Selected |
|--------|-------------|----------|
| Vorschlag | Streichreihenfolge B7 > B5 > B4 > B2/B3; Pflichtzahlen und B1 fallen nie | ✓ |
| B4 schuetzen | B4 erst nach B2/B3 streichen | |
| BL-F03 strikt zuerst, Rest egal | Streichreihenfolge der Mitmessposten liegt bei Claude | |

**User's choice:** Vorschlag

---

## Claude's Discretion

- Reihenfolge der Messungen innerhalb der Anfahrt (Research 1.5 als Startpunkt), Blockzuschnitt, Auswertungsformat, Rechenblatt-Gestaltung (Praezedenz v1.2).

## Deferred Ideas

- Tantivy num_threads als v1.4-Hebel fuer den Umbauweg (haengt an B6; Vergleichsmessung in CI).
- Marken-Reparatur vectors.py (Gewichts-Praezision) , bereits im v1.4-Umfang.
