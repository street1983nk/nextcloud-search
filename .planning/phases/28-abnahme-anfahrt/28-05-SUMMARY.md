---
phase: 28-abnahme-anfahrt
plan: 05
subsystem: messung
tags: [abnahme-anfahrt, owner-tor, deckel, rechenblatt, mess-10]
requires:
  - phase: 28-01
    provides: 02-rechenblatt.py deckel
  - phase: 28-03
    provides: 00-typwechsel.sh preis und quota
  - phase: 28-04
    provides: Runbook Abschnitt 3, x86-Vorprobe
provides:
  - "Rohdatei 01-vorbedingungen.txt: kostenlose Lesungen vor der Anfahrt"
  - "Rohdatei 02-rechenblatt-freigabe.txt: Sätze vom 30.09., Deckel, datierte Owner-Freigabe"
affects: [28-06, 28-07, 28-08]
tech-stack:
  added: []
  patterns: ["curl über stdout statt -o, Inline-Python ohne Rückstrich (Windows/MSYS)"]
key-files:
  created:
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/01-vorbedingungen.txt
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/02-rechenblatt-freigabe.txt
  modified:
    - docs/measurements/2026-10-abnahme-anfahrt/skripte/00-typwechsel.sh
    - backend/tests/test_v14_typwechsel.py
decisions:
  - "Owner-Freigabe 30.09.2026: Variante A mit Anker, Deckel 119,82 h / 59,43 USD, Sicherheitstimer 71,32 USD"
  - "Guthaben-Abgleich gegen den neu gelesenen Stand 104,11 USD (nicht 104,29 aus D-26-10)"
metrics:
  duration: "ca. 30 min Ausführung plus Owner-Wartezeit"
  completed: 2026-09-30
requirements: [MESS-10]
---

# Phase 28 Plan 05: Owner-Tor C1, Rechenblatt und Freigabe Summary

Kostenlose Vorbedingungen gelesen, Sätze am 30.09. neu gelesen (unverändert gegen 29.09.), Deckel mit Anker 59,43 USD vom Owner datiert freigegeben; keine Box gestartet.

## Ergebnisse

- Konto infranodedev ja, Snapshot completed, arm64-Abbild (gepinnt) und amd64-Abbild vorhanden, vCPU-Quota 32, alle sechs Typen in eu-central-1a/b/c.
- Schlüsselpaar fehlt in AWS, lokal vorhanden und stimmig: Block 2 legt es an oder importiert es.
- Abbild zu c87a0239: docker.yml-Lauf 36596834250, Index-Digest sha256:6a0c13be...d80f. Kopf 3f0e0a83: Lauf 36738661950, Index sha256:f49a90f7...11bc (nur Kenntnis).
- Sätze: alle sieben Box-Sätze identisch mit dem Research-Stand; Summe 45,18 USD (mit Anker 45,71), Deckel 58,74 USD (mit Anker 59,43), Timer 70,49 bzw. 71,32 USD.
- Guthaben neu gelesen (Owner): 104,11 USD; Rest nach Deckel 44,68 USD, nach Timer 32,79 USD.

## Owner-Signal (Task 2, wörtlich)

"freigabe, Variante mit Anker. Owner hat am 30.09.2026 freigegeben: Deckel 119,82 h / 59,43 USD, Sicherheitstimer 71,32 USD."

Freigabezeile: `Anfahrt freigegeben: 2026-09-30, Deckel 119,82 h / 59,43 USD`

## Commits

| Task | Commit | Inhalt |
|---|---|---|
| 1 | d809c8df | fix: 00-typwechsel preis auf Windows lauffähig, Regressionstest |
| 1 | 2b186581 | docs: Vorbedingungen und Rechenblatt mit Tagessätzen |
| 3 | cb49fa70 | docs: datierte Owner-Freigabe, Guthaben 104,11 USD |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 00-typwechsel.sh preis endete auf der Entwicklungsmaschine mit "preis-karte unlesbar"**
- **Found during:** Task 1
- **Issue:** curl -o bekam wegen MSYS_NO_PATHCONV den mktemp-Pfad unübersetzt und schrieb nach C:\tmp (gelesene Datei leer); zusätzlich wurde `\x1f` im -c-Argument an ein Windows-Python zu einem Steuerzeichen; preis-quelle las ein Feld, das die Karte nicht hat.
- **Fix:** curl über stdout-Umleitung, Gzip-Signatur als bytes((31, 139)), Quelle aus hawkFilePublicationDate; Stub im Test kann beides, neuer Regressionstest.
- **Files modified:** skripte/00-typwechsel.sh, backend/tests/test_v14_typwechsel.py
- **Commit:** d809c8df

### Hinweise

- `git diff origin/main..HEAD -- backend/src php` ist heute leer und damit ohne Aussage (HEAD = origin/main). Gegen c87a0239: backend/src unverändert, php 30 Dateien (Hotfixes 1.3.1/1.3.2), uv.lock mit numpy 2.5.3 und semantic-text-splitter 0.33.0. Gemessen wird weiter das Abbild zu c87a0239.
- Die Preis-API antwortet in diesem Konto (Runbook-Nachtrag 26.09. nannte sie gesperrt).
- Zugangsdaten kamen aus der aws-login-Sitzung und wurden für 00-typwechsel.sh ohne Ausgabe in die Umgebung exportiert.
- Vor und nach der Freigabe: 0 Instanzen, 0 Volumes mit purpose=findling-phase5.

## Self-Check: PASSED

- 01-vorbedingungen.txt und 02-rechenblatt-freigabe.txt vorhanden, genau eine Zeile "Anfahrt freigegeben:".
- Commits d809c8df, 2b186581, cb49fa70 vorhanden, Autor street1983nk, nicht gepusht.
- test_public_artifacts.py 55 passed, test_v14_typwechsel.py 45 passed.
