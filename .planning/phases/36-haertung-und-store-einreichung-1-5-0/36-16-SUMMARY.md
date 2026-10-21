---
phase: 36-haertung-und-store-einreichung-1-5-0
plan: 16
subsystem: Store-Einreichung 1.5.0 und Zustandspflege
tags: [rel-05, hart-06, store-submit, evidence]
requires: [36-15]
provides:
  - "Findling 1.5.0 und Findling Backend 1.5.0 im Store eingereicht, Lauf 39598694849, zweimal HTTP 201"
  - "Belegzeilen (10) bis (12) im Abschnitt Release 1.5.0 von docs/store-listing.md"
  - "HART-06 und REL-05 mit Beleg in REQUIREMENTS.md; ROADMAP Phase 36 mit Urteilen je Erfolgskriterium; STATE nachgezogen"
affects: [phase-36-verification]
tech-stack:
  added: []
  patterns:
    - "Gegenprobe je App-Seite per curl plus beide Kataloge, Zeitpunkte im Beleg"
key-files:
  created:
    - .planning/phases/36-haertung-und-store-einreichung-1-5-0/36-16-SUMMARY.md
  modified:
    - docs/store-listing.md
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/STATE.md
decisions:
  - "Phasenabschluss (Phase-36-Haken, phase.complete) bleibt beim Koordinator nach Code-Review und Verifier; ROADMAP-Zeile 36 steht auf 17/17, Executed, verification pending"
  - "appapi_apps.json mit 1.4.3 beim Beleg gilt als Katalog-Cache wie bei 1.4.3, kein Befund: beide App-Seiten nennen 1.5.0"
metrics:
  duration: "ca. 15 min nach dem Dispatch (12:19:35Z bis ca. 12:35Z)"
  completed: 2026-10-21
  tasks: 3
  files: 5
requirements: [REL-05, HART-06]
---

# Phase 36 Plan 16: Store-Einreichung 1.5.0 Summary

Beide Apps 1.5.0 sind auf das Owner-Wort "einreichen" mit zweimal HTTP 201 eingereicht (store-submit 39598694849, 12:19:46Z und 12:19:47Z), beide App-Seiten nennen 1.5.0 für Nextcloud 33 bis 35, und HART-06, REL-05, ROADMAP und STATE tragen den Beleg.

## Task 1: Owner-Freigabe (Koordinator)

- Frage: "Darf ich v1.5.0 beider Apps einreichen (store-submit.yml)?"
- Owner-Wort 21.10.2026, wörtlich: "einreichen".
- APPSTORE_TOKEN nicht neu geholt, unverändert seit 1.4.3; keine 400/401-Probe nötig, kein Wert ausgegeben.

## Task 2: Einreichung und Beleg

- Dispatch durch den Koordinator: `gh workflow run store-submit.yml --ref main -f tag=v1.5.0`, `register` aus. Lauf 39598694849, Job 119217379907, erstellt 12:19:35Z, success, Kopf 6c953a76.
- Log, Schritt "Submit both releases":
  - `2026-10-21T12:19:46.3241217Z release findling v1.5.0: HTTP 201`
  - `2026-10-21T12:19:47.6105228Z release findling_backend v1.5.0: HTTP 201`
- Gegenprobe (eigene Wiederholung):
  - 12:22:17Z Katalog Plattform 34.0.3: findling 1.5.0, 1.4.3, 1.4.2, `created` 12:19:46.159338Z.
  - 12:22:50Z `/apps/findling` und `/apps/findling_backend`: je 200, Stable channel 1.5.0 für NC 35, 34, 33, Download auf v1.5.0.
  - `appapi_apps.json` (findling_backend) 12:22:44Z, 12:23:47Z, 12:24:01Z, 12:24:16Z, 12:25:23Z, 12:25:51Z: sechsmal noch 1.4.3 (Katalog-Cache wie bei 1.4.3), vermerkt in docs/store-listing.md (12), Nachführung wird nachgeholt.
- Belegzeilen (10) bis (12) in docs/store-listing.md, Commit 4057d3ad (lokal). test_store_metadata.py 91 grün (Sperrwort-Prüfung eingeschlossen), keine Gedankenstriche.

## Task 3: Zustandspflege (bis vor die Push-Frage)

- REQUIREMENTS.md: HART-06 und REL-05 waren schon durch frühere Abschlüsse auf `[x]`; jetzt mit Beleg. HART-06 mit Vermerk "Upgrade-Strecke startet per D-36-13 von v1.4.3", Traceability mit Audit, Korpus, HaRP 39584388860, deploy-harp 39590105344; REL-05 mit Lauf 39598694849 und Belegkette.
- ROADMAP.md: 36-16 abgehakt, Urteile je Erfolgskriterium (Kriterium 2 "1.4.3 -> 1.5.0 per D-36-13"), Planliste 17 Pläne, Progress-Zeile 17/17 "Executed, verification pending". Der Phasenhaken in der Phasenliste bleibt offen (Koordinator).
- STATE.md: Kopf, Current Position, Metrik, Entscheid 36-16, zwei Blocker als erledigt markiert (pip-audit per 36-17, TIFF-Rahmenlauf per 36-09), Session.
- state.db-Sicherung `.dev/backup-36-05/state.db.bak` (SHA-256 7c4dffe5...cbc46, ignoriert, nie im Repo) gelöscht, Verzeichnis entfernt.
- Push-Frage an den Owner offen: "Darf ich die lokalen Doku-Commits pushen?"

## Deviations from Plan

1. **Task 1 und Dispatch vom Koordinator:** Freigabe und `gh workflow run` liefen beim Koordinator; hier Beleg, Gegenprobe und Zustandspflege.
2. **Kein Phasenabschluss:** auf Anweisung des Koordinators kein Phasenhaken und kein phase.complete; das folgt nach Code-Review und Verifier.
3. **Plan 36-17 in der Liste:** Die Planliste umfasst 17 Pläne (36-17 als Welle 8), nicht 16 wie im Plantext.
4. **[Rule 1] Veraltete Blocker in STATE.md:** pip-audit und TIFF-Rahmenlauf standen noch als offen, obwohl 36-17 und 36-09 sie geschlossen haben; als erledigt markiert.

## Known Stubs

Keine.

## Offen

- Owner-Wort zum Push der lokalen Doku-Commits, danach `git push origin main`, CI-Block und Push-Wortlaut in dieser SUMMARY.
- appapi_apps.json bis zur Nachführung auf 1.5.0 beobachten.
- Instanz 8096 und Volume `findling-harp143_backend_data` (aus 36-15) nach Owner-Ja abbauen.

## Self-Check: PASSED

- FOUND: "release findling v1.5.0: HTTP 201" und "release findling_backend v1.5.0: HTTP 201" in docs/store-listing.md
- FOUND: Commit 4057d3ad
- FOUND: `[x] **REL-05` und `[x] **HART-06` in REQUIREMENTS.md
- FOUND: "einreichen" in dieser SUMMARY
