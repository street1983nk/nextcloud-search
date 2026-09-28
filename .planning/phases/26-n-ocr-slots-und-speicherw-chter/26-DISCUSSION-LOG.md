# Phase 26: N OCR-Slots und Speicherwächter - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md , this log preserves the alternatives considered.

**Date:** 2026-09-28
**Phase:** 26-n-ocr-slots-und-speicherwaechter
**Areas discussed:** Wächter-Eskalation und Rückweg, Kill-Semantik und Sperrfristen, Messfahrt und AWS-Matrix, Slot-Priorität (os.nice, A12)

---

## Wächter-Eskalation und Rückweg

| Option | Description | Selected |
|--------|-------------|----------|
| Wirksame Stufe + persistenter Merker | Gespeichertes Profil bleibt (D-24-07), Absenkung als eigener persistenter Merker, überlebt OOM-Neustart | ✓ |
| Nur wirksame Stufe im Prozess | Kein neuer Zustand, aber Absturzschleifen-Risiko nach OOM-Kill | |
| Gespeichertes Profil umschreiben | Widerspricht D-24-07 | |

**User's choice:** Wirksame Stufe + persistenter Merker (D-26-01)

| Option | Description | Selected |
|--------|-------------|----------|
| Rechnerisch je Runde gegen headroom_bytes | Passt-ein-weiterer-Slot-Rechnung vor jedem Staffel-Start, nutzt Phase-25-Leser | ✓ |
| Reaktiv auf memory.events high | Echtes Kernelsignal, fehlt aber auf v1-Hosts/ohne Limit | |
| Beides | Rechnung + high als Sofort-Auslöser | |

**User's choice:** Rechnerisch je Runde (D-26-02)

| Option | Description | Selected |
|--------|-------------|----------|
| 2x max im Fenster ODER 1 OOM-Kill | Delta-Zählung, Fenster ~10 min (Research final), OOM-Kill senkt sofort | ✓ |
| Nur oom_kill zählt | Weniger Fehlalarm, aber später | |
| Claude entscheidet nach Research | | |

**User's choice:** 2x max im Fenster ODER 1 OOM-Kill (D-26-03)

| Option | Description | Selected |
|--------|-------------|----------|
| Nur durch Admin-Aktion | Merker bleibt bis Profil neu gesetzt/bestätigt, kein Flattern | ✓ |
| Automatisch nach Ruhefenster | Zyklus-Risiko auf grenzwertigen Boxen | |
| Automatisch nach Neustart | Nur bewusste Neustarts, Erklärbedarf | |

**User's choice:** Nur durch Admin-Aktion (D-26-04)

---

## Kill-Semantik und Sperrfristen

| Option | Description | Selected |
|--------|-------------|----------|
| Fest = 2x Obergrenze (32) | Doppelpuffer, kein Routen-Parameter, Paritätstest einfach | ✓ |
| Dynamisch: Container nennt N | Sauberste Fristen, größere Companion-Änderung | |
| Fest = Obergrenze (16) | Slots können zwischen Ansprüchen leerlaufen | |

**User's choice:** KIND_BATCH[ocr] fest = 32 (D-26-05)

| Option | Description | Selected |
|--------|-------------|----------|
| Formel: Zeilen/N x Zeitdeckel + Marge | Sparsam automatisch lang, Leistung kurz | ✓ |
| Fest auf Worst Case | Nach Kill auf Leistung unnötig lange gesperrt | |
| Claude entscheidet nach Research | | |

**User's choice:** Sperrfrist-Formel (D-26-06)

| Option | Description | Selected |
|--------|-------------|----------|
| Adaptiv: Slots = min(N, gelieferte Zeilen) | Kein Versionscheck, kein Sonderpfad | ✓ |
| Versionscheck: 1 Slot bis Companion passt | Neuer Kopplungs-Mechanismus, künstlicher Verlust | |
| Claude entscheidet | | |

**User's choice:** Adaptiv (D-26-07)

| Option | Description | Selected |
|--------|-------------|----------|
| Beide Fälle: Container-Kill + Kind-Kill | Gründlichster Beleg der Zusagen | ✓ |
| Nur Container-Kill | N-Slot-Interaktion einzelner Kinder unbewiesen | |
| Claude entscheidet nach Research | | |

**User's choice:** Beide Fälle (D-26-08)

---

## Messfahrt und AWS-Matrix

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 28, Phase 26 nur CI | Keine Doppel-Anfahrt, MESS-10 verlangt die Matrix sowieso in 28 | ✓ |
| AWS-Matrix schon in Phase 26 | Frühere Gewissheit, doppelte Kosten | |
| Geteilt: Stichprobe in 26, Matrix in 28 | | |

**User's choice:** Phase 28, Phase 26 nur CI (D-26-09/10)

| Option | Description | Selected |
|--------|-------------|----------|
| 1 vs 2 vs 4 Slots, bestehendes Messwerkzeug | Leiter zeigt, wo Skalierung abknickt; Rauschgrenze 1,05 | ✓ |
| Nur 1 vs 4 (ein Paar) | Schnellste CI-Zeit, keine Zwischenstufe | |
| Claude entscheidet nach Research | | |

**User's choice:** Leiter 1/2/4 (D-26-09)

| Option | Description | Selected |
|--------|-------------|----------|
| Ja, so festschreiben | AWS-Entscheide 28.09. wörtlich als Phase-28-Block in CONTEXT.md | ✓ |
| Anpassen | | |

**User's choice:** Ja, festschreiben (D-26-10)

---

## Slot-Priorität (os.nice, A12)

| Option | Description | Selected |
|--------|-------------|----------|
| Nur die Sandbox-Kinder | tesseract erbt; Hauptprozess (Suche/API/Einbettung) bleibt normal | ✓ |
| Kinder + Einbettungs-Drossel prüfen | | |
| Claude entscheidet | | |

**User's choice:** Nur Sandbox-Kinder (D-26-11)

| Option | Description | Selected |
|--------|-------------|----------|
| nice 10 | Nachrangig, aber auf leerer Box ungebremst | ✓ |
| nice 19 (ganz hinten) | Sicherste UI, Erstindex ggf. spürbar länger | |
| Claude entscheidet nach Research | | |

**User's choice:** nice 10 (D-26-11)

| Option | Description | Selected |
|--------|-------------|----------|
| Immer, auch Sparsam | #19-Feldbeleg kam aus dem Ein-Slot-Betrieb | ✓ |
| Nur Standard/Leistung | Sparsam exakt wie heute, #19 dort unverbessert | |
| Claude entscheidet | | |

**User's choice:** Immer, auch Sparsam (D-26-11)

| Option | Description | Selected |
|--------|-------------|----------|
| CI-Zusicherung + Live-Latenzprobe | Mechanismus UND Wirkung belegt, Zahlbeleg für #19 | ✓ |
| Nur CI-Zusicherung | Wirkung nicht gemessen | |
| Claude entscheidet | | |

**User's choice:** CI-Zusicherung + Live-Latenzprobe (D-26-12)

---

## Claude's Discretion

- OOM-Kette R1 im Detail + endgültiger Fensterwert für D-26-03 (Research)
- Abbruchsemantik halber Staffeln (ack vs. Index-Commit, retries-Zusammenspiel)
- Semaphore-Platzierung, Zeilen-Zuteilung an Kinder, Form der Writer-Sperre
- Sperren um die geteilte Embedding-Engine (embed_slots = 2, D-25-12), idle-Guard-Mitnahme
- Schlüsselname/Wertemenge des Absenk-Merkers, Wortlaut der Statusmeldungen (acht Kataloge)
- Schnitt von CI-Kill-Test und CI-Messleiter

## Deferred Ideas

- AWS-Matrix, Quota-Erhöhung auf 48, Snapshot-Abbau: Phase 28 (in D-26-10 festgehalten)
- Issue #18 Fix-Kandidaten: wartet auf budachst, Slot-Entscheid beim Owner
