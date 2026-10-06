# Phase 27: Vorab-Prüfung und Settings-Oberfläche - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md, this log preserves the alternatives considered.

**Date:** 2026-09-29
**Phase:** 27-vorab-pr-fung-und-settings-oberfl-che
**Areas discussed:** fp32 auf der Fläche, Probe-Ablauf, Verdikt und Folgen, Texte und Rückwege

---

## fp32 auf der Fläche

| Option | Description | Selected |
|--------|-------------|----------|
| Häkchen unter der Auswahl | nur bei Standard/Leistung, Probe testet mit, beides zusammen gespeichert | ✓ |
| Vierter Eintrag im Auswahlfeld | "Leistung mit fp32", mischt zwei Schlüssel | |
| fp32 bleibt occ-only | Seite zeigt nur an | |

| Option | Description | Selected |
|--------|-------------|----------|
| In der Probe laden, bei Fehlschlag löschen | Klick = Admin-Aktion, bei passt bleibt Datei | ✓ |
| In der Probe laden, Datei bleibt liegen | spart Download beim Wiederholen | |
| Nur rechnen, nicht laden | keine echte Modellprobe | |

| Option | Description | Selected |
|--------|-------------|----------|
| Hinweiszeile mit Schätzung | Dokumentzahl + Dauer, kein Dialog | ✓ |
| Bestätigungsdialog | zusätzlicher Klick | |
| Nur Hinweis ohne Zahl | am einfachsten | |

**User's choice:** jeweils die Empfehlung.

---

## Probe-Ablauf

| Option | Description | Selected |
|--------|-------------|----------|
| Hintergrund + Fortschrittszeile | Seite pollt, Ergebnis überlebt Neuladen | ✓ |
| Synchron warten mit Spinner | reißt an Proxy-Timeouts | |

| Option | Description | Selected |
|--------|-------------|----------|
| Indexierung pausieren, danach weiter | saubere Messung, kein gemeinsames OOM | ✓ |
| Parallel weiterlaufen | verfälschte Messung | |

| Option | Description | Selected |
|--------|-------------|----------|
| Messteil ca. 2 min, Download extra | eigener Download-Deckel ca. 10 min | ✓ |
| Ein Gesamtdeckel ca. 5 min | | |
| Du entscheidest | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Erst 1 Slot, dann Ziel-N | Slot-Kosten dieser Box messen, vorab rechnen | ✓ |
| Direkt Ziel-N nach Formel-Vorab | Repo-Messwerte statt Box | |
| Leiter 1/2/.../N | zu lang | |

**User's choice:** jeweils die Empfehlung.

---

## Verdikt und Folgen

| Option | Description | Selected |
|--------|-------------|----------|
| Knapp: nicht speichern, eine Stufe tiefer anbieten | nur bei passt speichern | ✓ |
| Knapp: mit Warnung speicherbar | weicht von PRUEF-01 ab | |
| Knapp = weniger Slots | neuer Mechanismus | |

| Option | Description | Selected |
|--------|-------------|----------|
| Abwärts (Sparsam, fp32->int8) sofort speichern | ohne Probe | ✓ |
| Jede Änderung durch die Probe | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Verdikt verfällt nicht | D-24-07 + Wächter sichern ab | ✓ |
| Neu prüfen bei Hardware-Änderung | | |

**User's choice:** jeweils die Empfehlung.
**Notes:** Leistung zu Standard läuft weiter durch die Probe; Ursachenliste legt die Research fest.

---

## Texte und Rückwege

| Option | Description | Selected |
|--------|-------------|----------|
| "Bei Sparsam bleiben" | keine Verwechslung mit Profil Standard | ✓ |
| "Nichts ändern" | | |
| Wortlaut wie Roadmap | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Absenkung: Hinweis + "Erneut prüfen" | Probe = Admin-Bestätigung (Token) | ✓ |
| Nur Bestätigen-Knopf ohne Probe | | |

| Option | Description | Selected |
|--------|-------------|----------|
| occ bleibt, dokumentiert ohne Probe | | ✓ |
| Nur noch UI | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Env-Var: Auswahl frei, Hinweis nennt überstimmte Werte | Probe rechnet mit wirksamen Werten | ✓ |
| Nicht auf der Seite zeigen | | |

**User's choice:** jeweils die Empfehlung.
**Notes:** Erste Env-Var-Frage ("Auswahl gesperrt") beruhte auf einer falschen Annahme (Env überstimmt ganzes Profil); nach Blick in `profile.py:276` korrigiert und neu gefragt.

---

## Claude's Discretion

- Ursachenliste, Routenform, Speicherort des Probe-Ergebnisses, Poll-Intervall, Pause-Mechanik
- Sicherheitsabstand "passt knapp", genaue Zeitdeckel, synthetische Scanseite
- Katalogtexte, Platzierung (UI-SPEC), Bedrohungsregister der Schreibroute

## Deferred Ideas

- Issue #18 Fix-Kandidaten: nicht gefaltet (Trefferwert 0,2)
