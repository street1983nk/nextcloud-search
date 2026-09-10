# Phase 11: Haertung und Store-Einreichung v1.1 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-10
**Phase:** 11-haertung-und-store-einreichung-v1-1
**Areas discussed:** Box-Einsatz + Abbau, Upgrade-Pfad 1.0.x auf 1.1.0, Store-Texte + Franzoesisch, Release-Zuschnitt + Timing

---

## Box-Einsatz + Abbau

| Option | Description | Selected |
|--------|-------------|----------|
| Kurze Box-Anfahrt | ~4 h / 0,50 USD Deckel, Fixe gegen echten Lastkorpus, Index intakt | ✓ |
| Nur lokal + Unit-Tests | synthetische Antworten, Beweis gegen echte Last fehlt | |
| Fixes ohne Beweis einchecken | Code-Review genuegt | |

**User's choice:** Kurze Box-Anfahrt (Empfehlung)

| Option | Description | Selected |
|--------|-------------|----------|
| CI-Runner beide Archs | arm64 nativ lief in Phase 10, reproduzierbar, kostenlos | ✓ |
| arm64 auf der Box | echte Box; --rm-data-Falle (Lehre 06.1) | |
| Beides | CI als Gate plus einmal Box als Realprobe | |

**User's choice:** CI-Runner beide Archs (Empfehlung)

| Option | Description | Selected |
|--------|-------------|----------|
| Snapshot + Abbau | EBS-Snapshot des Korpus-Volumes (~1-2 USD/Monat), dann abbauen | ✓ |
| Kompletter Abbau ohne Snapshot | 0 USD laufend, Korpus-Neuaufbau kostet Tage | |
| Geparkt lassen | 9,40 USD/Monat, sofort startklar | |

**User's choice:** Snapshot + Abbau (Empfehlung)

---

## Upgrade-Pfad 1.0.x auf 1.1.0

| Option | Description | Selected |
|--------|-------------|----------|
| Index-kompatibel halten | bestehender Index bleibt unangetastet | ✓ |
| Reindex erlaubt, wenn sichtbar | Statusseite + Admin-Hinweis, automatischer Neuaufbau | |
| Nach Code-Befund entscheiden | Researcher prueft SCHEMA_VERSION, Entscheid beim Plan-Review | |

**User's choice:** Index-kompatibel halten (Empfehlung)

| Option | Description | Selected |
|--------|-------------|----------|
| Automatisch mit sichtbarem Status | Zero-Config bleibt, Statusseite zeigt Fortschritt | ✓ |
| Erst nach Admin-Klick | Admin waehlt Lastfenster | |

**User's choice:** Automatisch mit sichtbarem Status (Vorratsentscheid, falls je noetig)

---

## Store-Texte + Franzoesisch

| Option | Description | Selected |
|--------|-------------|----------|
| Neue Zahlen + alte als Vergleich | Muster 06.1, staerkste ehrliche Story | ✓ |
| Nur neue Zahlen | kuerzester Text, Fortschritt unsichtbar | |
| Beim Entwurf entscheiden | beide Varianten zur Text-Abnahme | |

**User's choice:** Neue Zahlen + alte als Vergleich (Empfehlung)

| Option | Description | Selected |
|--------|-------------|----------|
| Ja, eigenes FR-Gate | Owner liest alle FR-Strings + FR-Store-Text vor Abgabe | ✓ |
| Nur Store-Text, App-Strings Stichprobe | sichtbarster Text komplett | |
| Claude allein | kein eigenes Review | |

**User's choice:** Ja, eigenes FR-Gate (Empfehlung); Owner ist franzoesischer Muttersprachler

| Option | Description | Selected |
|--------|-------------|----------|
| Nein, nur in Bericht/README | Store-Text bleibt kurze Faktenliste | ✓ |
| Ja, knapp im Store-Text | ein Vorbehaltssatz pro Zahl | |

**User's choice:** Nein, nur in Bericht/README (Empfehlung)

---

## Release-Zuschnitt + Timing

| Option | Description | Selected |
|--------|-------------|----------|
| Pflicht + Werkzeug-Fixes | plus DI-10-01/02 mit Box-Beweis; 04/05/T-09-29 nur falls klein | ✓ |
| Nur Pflicht | kleinster Release | |
| Alles Offene | alle 7 Befunde, gefaehrdet Zeitfenster | |

**User's choice:** Pflicht + Werkzeug-Fixes (Empfehlung)

| Option | Description | Selected |
|--------|-------------|----------|
| Nach dem ISV-Call, im Zielfenster | ~16.-19.09., Call-Erkenntnisse in Texte | |
| So frueh wie moeglich | einreichen sobald fertig, auch vor dem 14.09. | ✓ |
| Ende des Fensters | ~20.-22.09. | |

**User's choice:** So frueh wie moeglich (bewusst GEGEN die Empfehlung: nicht auf den ISV-Call warten)

---

## Claude's Discretion

- Wellenschnitt und Reihenfolge der Plaene
- Zuschnitt der Haertungstests jenseits des Happy Path (Muster 06.1)
- Schluesselvergleich fuer zwei Sprachpaare technisch
- Kombination Box-Anfahrt Fix-Beweise mit Upgrade-Beweis (solange keine zweite NC am Mess-Docker)

## Deferred Ideas

- Box-Wiederaufbau-Runbook aus dem EBS-Snapshot (v1.2-Messplanung)
- Versionsfenster NC 35 / Release-Notes-Feinschliff (Discretion im Bestandsrahmen)
