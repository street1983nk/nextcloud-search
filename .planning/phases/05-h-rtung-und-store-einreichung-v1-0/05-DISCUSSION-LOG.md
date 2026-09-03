# Phase 5: Härtung und Store-Einreichung v1.0 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-03
**Phase:** 5-Härtung und Store-Einreichung v1.0
**Areas discussed:** ARM-Lasttest-Setup, Einreichung + Versionierung, Uninstall-Cleanup-UX, Härtungs-Umfang, Paritätstest-Semantik, Zertifikats-Status

---

## ARM-Lasttest-Setup

| Option | Description | Selected |
|--------|-------------|----------|
| Hetzner CAX11 mieten | Ampere ARM, 2 vCPU, 4 GB, ~4 EUR/Monat, reproduzierbar | ✓ |
| Eigener Raspberry Pi | Realistischstes Selfhoster-Szenario, Setup-Aufwand | |
| Oracle Free Tier ARM | Gratis, aber Kapazitäts-Lotterie | |

| Option | Description | Selected |
|--------|-------------|----------|
| Synthetisch skaliert | Deterministischer Generator, reproduzierbar | ✓ |
| Echte eigene Dokumente | Realistisch, aber privat + nicht reproduzierbar | |
| Beides | Synthetisch + Plausibilitätscheck | |

| Option | Description | Selected |
|--------|-------------|----------|
| OOM-frei + Peak-Budget | Peak-RSS unter festem Budget als Store-Grenzwert | ✓ |
| Nur OOM-frei | Schwächere Aussage | |
| Zusätzlich Dauerbetrieb | +24h Idle-Messung | |

| Option | Description | Selected |
|--------|-------------|----------|
| AIO auf der ARM-Box | Lasttest erledigt AIO-Deploy-Beweis mit | ✓ |
| docker-compose auf der ARM-Box | Schlanker, AIO-Beweis separat | |
| Beide nacheinander | Vollständigst, mehr Zeit | |

| Option | Description | Selected |
|--------|-------------|----------|
| Claude bestellt im bestehenden Hetzner-Konto | Kosten dokumentiert, Box danach löschen | ✓ |
| Owner bestellt selbst | Claude bereitet vor | |
| Später entscheiden | | |

| Option | Description | Selected |
|--------|-------------|----------|
| ~10.000 Dateien / ~5 GB | Familien-/Vereins-Cloud (Empfehlung) | |
| ~50.000 Dateien / ~20 GB | Kleine Organisation, Volllauf 1-2 Tage | ✓ |
| ~2.000 Dateien / ~1 GB | Smoke-Test | |

**Notes:** Owner wählte bewusst den größeren Korpus gegen die Empfehlung. Folge: Hetzner-Volume nötig (CAX11 hat 40 GB Disk).

| Option | Description | Selected |
|--------|-------------|----------|
| CI-Matrix 32+33+34 | integration.yml zur Matrix erweitern | ✓ |
| CI nur Ränder 32+34 | | |
| 34 in CI, 32/33 manuell | | |

| Option | Description | Selected |
|--------|-------------|----------|
| docs/ + Store-Text + README | Voller Bericht + verdichtete Kernaussage | ✓ |
| Nur Repo-Doku | | |
| Nur Store-Kernaussage | | |

---

## Einreichung + Versionierung

| Option | Description | Selected |
|--------|-------------|----------|
| v1.0 sofort allein (Empfehlung) | Jahresende-Puffer, frühes Feedback | |
| Mit v1.1 bündeln | Ein Launch mit vollem Featureset | ✓ |
| Nach Phase-5-Abschluss entscheiden | | |

**Notes:** Owner-Entscheid GEGEN die Staffelungs-Empfehlung; ersetzt den offenen PROJECT.md-Punkt.

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 5 = einreichungsbereit | Signierte Release-Kandidatur, Abgabe nach Phase 6 | ✓ |
| Phase 6 vorziehen | Reihenfolge tauschen | |
| Einreichung trotzdem in Phase 5 | Faktisch doch Staffelung | |

| Option | Description | Selected |
|--------|-------------|----------|
| Lockstep, identische Nummer | Paarweise Releases, exakte Major.Minor-Prüfung | ✓ |
| Getrennt + Kompatibilitätsmatrix | | |
| Lockstep Major.Minor, Patch frei | | |

| Option | Description | Selected |
|--------|-------------|----------|
| EN/DE/FR + Privacy-Block | Muster MCP Connector, ohne Synergie-Claim | ✓ |
| Nur EN/DE | | |
| Nur EN | | |

| Option | Description | Selected |
|--------|-------------|----------|
| 1.0.0 | Store-Erstauftritt ist die 1.0 | ✓ |
| 1.1.0 | Interne Nomenklatur sichtbar | |
| 0.9.0 als Beta, dann 1.0.0 | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Ja, Bündel vor Jahresende (mit Staffelungs-Fallback) | Phase 5+6 bis Dezember | ✓ |
| Ja, ohne Fallback | | |
| Deadline lockern | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Claude baut aus Dev-Instanz | Playwright-Screenshots + Header-Bild nach Bildpost-Linie | ✓ |
| Nur echte UI-Screenshots | | |
| Owner liefert die Medien | | |

---

## Uninstall-Cleanup-UX

| Option | Description | Selected |
|--------|-------------|----------|
| AppAPI-Standardmechanik | ExApps-UI-Checkbox / occ --rm-data ist die Bestätigung | ✓ |
| Eigener Dialog in der Findling-Admin-Seite | | |
| Beides | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Suche aus, Index bleibt | Re-Enable ohne Reindex | ✓ |
| Suche aus + Queue leeren | | |
| Wie Uninstall ohne Volume | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Sanft degradieren + Hinweis | Banner existiert; Reihenfolge dokumentiert | ✓ |
| Companion-Removal räumt mit | | |
| Gegenseitige Abhängigkeit erzwingen | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Beim Companion-Remove | Uninstall-Step löscht Tabellen + appconfig | ✓ |
| Nur nach separater Bestätigung | | |
| Beim Backend-Unregister | | |

---

## Härtungs-Umfang

| Option | Description | Selected |
|--------|-------------|----------|
| Beide Deferred Items in Phase 5 | DI-04-03 + DI-04-04 | ✓ |
| Nur DI-04-04 | | |
| Beide nach v1.1 | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Sicherheit ja, Perf nur bei Relevanz (Empfehlung) | | |
| Alles abarbeiten | Jeden offenen Review-Rest schließen | ✓ |
| Nichts pauschal | | |

**Notes:** Owner wählte die gründlichste Variante gegen die Empfehlung; Deadline-Spannung durch Staffelungs-Fallback abgefedert.

| Option | Description | Selected |
|--------|-------------|----------|
| Kern-Drills auf der Box | kill/Resume, Backend offline, Platte fast voll | ✓ |
| Nur Volllauf | | |
| Drills + 24h-Dauerbetrieb | | |

---

## Paritätstest-Semantik (Zusatz-Grauzone)

| Option | Description | Selected |
|--------|-------------|----------|
| Sichtbarkeits-Parität | Treffer genau dann, wenn nativ sichtbar; beidseitig | ✓ |
| Nie-mehr-als-nativ | Nur Sicherheitsrichtung | |
| Volle Treffer-Parität | Praktisch nicht definierbar | |

| Option | Description | Selected |
|--------|-------------|----------|
| Gruppenloser Minimal-Nutzer (Empfehlung) | | |
| Gastnutzer (guests-App) | | |
| Beides testen | Minimal-Nutzer in CI, Gast manuell vor Einreichung | ✓ |

---

## Zertifikats-Status (Zusatz-Grauzone, faktisch geklärt)

Live-Prüfung statt Frage: beide CSR-PRs (#1165, #1166) am 19.08. gemergt, beide
.crt im appstore-Repo vorhanden. Kein Blocker, keine Owner-Entscheidung nötig.

## Claude's Discretion

- Peak-RSS-Budgetwert und Messwerkzeug/Kadenz
- Generator-Design des 50k-Lastkorpus
- CI-Matrix-Zuschnitt
- Paritätstest-Fixtures und OCS-Aufrufe
- Uninstall-Implementierung im Detail
- Arbeitspaket-Reihenfolge

## Deferred Ideas

- Roadmap-Formal-Edit (Kriterium 4 "einreichungsbereit"): nicht beauftragt, Entscheidung in CONTEXT D-08/D-09 festgehalten
- MCP-Synergie sichtbar machen: nach tatsächlicher Einreichung (Connector-Backlog BL-01..03)
- Launch-Kommunikation: gehört zur Einreichung nach Phase 6
