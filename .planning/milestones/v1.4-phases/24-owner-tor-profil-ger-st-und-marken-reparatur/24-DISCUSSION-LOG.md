# Phase 24: Owner-Tor, Profil-Gerüst und Marken-Reparatur - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md , this log preserves the alternatives considered.

**Date:** 2026-09-27
**Phase:** 24-Owner-Tor, Profil-Gerüst und Marken-Reparatur
**Areas discussed:** Profil-Weg A/B/C, Anteile + Store-Satz, fp32-Lieferweg (K7), Vorschlags-Schwellen

---

## Profil-Weg A/B/C (Owner-Tor Teil 1)

| Option | Description | Selected |
|--------|-------------|----------|
| Weg B: OCS-Route | PHP-OCS-Route (Muster queues/documents/stats), Container fragt einmal je Runde; Live-Wechsel, echte Vorab-Prüfung, echte Settings-Seite; lru_cache-Schichtung nötig | ✓ |
| Weg A: Umgebungsvariable | FINDLING_PROFILE via AppAPI; minimal, aber Neustart je Wechsel, Vorab-Prüfung nur Text | |
| Weg C: Datei im Persistenzpfad | context_chat-Muster; kein Neustart, aber Schreibroute nötig und zwei Ablageorte (Drift-Risiko) | |

**User's choice:** Weg B: OCS-Route (Empfehlung übernommen)

| Option | Description | Selected |
|--------|-------------|----------|
| Letztes bekanntes, sonst Sparsam | Zuletzt gelesenes Profil gilt für die Prozesslebensdauer; nie eines lesbar = Sparsam | ✓ |
| Sofort Sparsam | Jeder Lesefehler setzt sofort zurück; Flattern bei Gateway-Schluckauf | |
| Du entscheidest | Claude hängt sich an das bestehende Gateway-Fehlermuster des Pollers | |

**User's choice:** Letztes bekanntes, sonst Sparsam (Empfehlung übernommen)

---

## Anteile + Store-Satz (Owner-Tor Teil 2)

| Option | Description | Selected |
|--------|-------------|----------|
| Research-Vorschlag | Standard 50 % Kerne / 40 % Speicher (max 4 Slots); Leistung Kerne-1 / 60 % (max 16) | ✓ |
| Konservativer | Standard 40/30, Leistung 60/50; mehr Luft für Nextcloud, weniger Tempo | |
| Aggressiver | Standard 60/50, Leistung Kerne-1/75; höheres K4-Risiko | |

**User's choice:** Research-Vorschlag (Empfehlung übernommen)

| Option | Description | Selected |
|--------|-------------|----------|
| Ohne Klick: unverändert sparsam | Zwei Sätze: Default unverändert, dann Anteile je Profil mit Einladung zum Opt-in | ✓ |
| Kurzform nur Anteil | Eine Zeile ohne Prozentzahlen je Profil | |
| Additive Form | context_chat-Muster (Grundlast plus Freigabe) | |

**User's choice:** Zunächst Rückfrage ("welche option wäre für die user am besten, am einfachsten, am sichersten und am zuverlässigsten und vorallem geschwidigkeit maximiert"); Empfehlung Option 1 wurde begründet (einfachstes Modell, führt mit dem gepinnten Sparsam-Versprechen, lädt Nutzer mit starker Hardware aktiv zum Profilwechsel ein), Owner bestätigte: "ok dann machen wir es so".
**Notes:** Wortlaut verbindlich für den 1.4.0-Store-Text: "Ohne Zutun läuft Findling unverändert sparsam wie bisher. Wer mehr Hardware hat, gibt per Profil höchstens die Hälfte der Box frei (Profil Standard) oder alles bis auf einen Kern (Profil Leistung)."

---

## fp32-Lieferweg (Owner-Tor Teil 3, K7)

| Option | Description | Selected |
|--------|-------------|----------|
| Nachladen bei Opt-in | int8 bleibt im Abbild; fp32 erst bei ausdrücklicher Admin-Wahl, Digest-Prüfung, klares Verdikt bei Offline; kein +352 MB für alle | ✓ |
| Ins Abbild | +352 MB für jede Installation; offline-fähig, berührt K7-Vorbehalt | |
| Du entscheidest | Festlegung in der Planung nach Researcher-Prüfung | |

**User's choice:** Nachladen bei Opt-in (Empfehlung übernommen)

---

## Vorschlags-Schwellen (HW-01)

| Option | Description | Selected |
|--------|-------------|----------|
| Research-Vorschlag | Standard ab 6 GB + 3 Kernen, Leistung ab 12 GB + 6 Kernen | ✓ |
| Früher vorschlagen | Standard ab 4 GB + 2 Kernen, Leistung ab 8 GB + 4 Kernen; mehr "passt nicht"-Verdikte | |
| Du entscheidest | Herleitung aus P22-Basiszahlen in der Planung | |

**User's choice:** Research-Vorschlag (Empfehlung übernommen)

| Option | Description | Selected |
|--------|-------------|----------|
| Gespeichert bleibt, wirksam gedrosselt | Gewähltes Profil bleibt stehen, Container drosselt selbsttätig und meldet gewählt vs. wirksam; kehrt bei Wachstum zurück | ✓ |
| Gespeichertes Profil wird zurückgesetzt | Dauerhafte Herabstufung; temporärer Engpass überschreibt Admin-Wahl | |

**User's choice:** Gespeichert bleibt, wirksam gedrosselt (Empfehlung übernommen)

---

## Claude's Discretion

- Download-Quelle und Digest-/Signaturmechanik des fp32-Nachladens (Festlegung spätestens Phase-25-Plan)
- Technischer Schnitt der lru_cache-Schichtung in config.py und genaue Form der OCS-Route
- Form der Marken-Erweiterung in store/vectors.py (Randbedingung: alte Marke = int8, kein Zwangs-Reindex)

## Deferred Ideas

- Bau des fp32-Nachladewegs → Phase 25 (MOD-02)
- Echte Slots/Nebenläufigkeit → Phasen 25/26; Phase 24 baut nur Formel + Meldung
- idle-Guard EmbeddingModel.release() → Mitnahme-Kandidat Phase 25 (bereits in ROADMAP)
