---
phase: 27-vorab-pr-fung-und-settings-oberfl-che
plan: 12
subsystem: php-companion
tags: [js, admin-ui, profile, probe, a11y, security]
requires: [27-07, 27-08, 27-10]
provides:
  - setupProfile in php/js/admin.js mit Probe-Start, Probe-Poll (2000 ms, eigener AbortController), Verdikt-Karte, Abwärtswegen, Stay on Economy, Check again, Check Standard
  - JS-Maps stepNames, verdictNames, probeCauseNames, precisionSentences, startErrors, guardCauseNames, PROBE_CAUSE_NEEDS
  - needsProbe im Skript nach SettingsService::needsProbe (nur Knopfbeschriftung)
  - Gates für Map-Gleichheit, Poll-Takt, Regel-Gleichheit und Payload
affects: [27-13]
tech-stack:
  added: []
  patterns: [Maps als Funktionen mit t() für späte Übersetzung, ein Platzhalter-Durchlauf mit Funktionsersetzung, Ergebnis-Identität über at/profile/precision/verdict]
key-files:
  created: []
  modified:
    - php/js/admin.js
    - backend/tests/test_admin_ui_contract.py
decisions:
  - "Ende der Probe erkannt an state != running nach gesehenem running, an einem neuen Ergebnis (at, profile, precision, verdict) oder nach drei ruhigen Antworten; die Overview trägt keine Probe-Id"
  - "Der Status-Poll aktualisiert Auskunftszeilen, Wächter-Banner und Präzisionszeile (precisionVerdict); das Formular folgt dem gespeicherten Stand nur, solange der Admin es nicht angefasst hat"
  - "ocr_n zeigt 'Check running.' ohne Schritt, weil die Stand-Route die Slotzahl nicht liefert"
  - "'Check Standard' prüft Standard mit der Präzision des letzten Verdikts"
  - "Fehlerzeile während der Probe nur mit dem Satz des eigenen Starts (busy), sonst Startfehler oder Sperrgrund (Z14, Z15, Z16a)"
metrics:
  duration: ca. 40 min
  completed: 2026-09-29
  tasks: 2
  files: 2
---

# Phase 27 Plan 12: Skript der Profilfläche Summary

admin.js bedient den Block "Performance profile": Probe starten über POST admin/profile/check, Stand alle 2000 ms abfragen mit Schritt und Downloadbytes, Verdikt-Karte mit Chip, Ursache, Folge und Angebot der nächstniedrigeren Stufe, Abwärtswege und "Stay on Economy" sofort über POST admin/profile, alles über hidden, disabled und Textknoten.

## Erledigt

| Task | Inhalt | Commit |
|------|--------|--------|
| 1 | Konstanten ROUTE_PROFILE, ROUTE_PROFILE_CHECK, POLL_PROBE_MS = 2000; probeRequest; Maps gleich den Template-Maps; needsProbe; refreshForm (Häkchen nur Standard/Leistung, Reindex lang/kurz, Beschriftung und disabled, Kein-Änderung-Hinweis, Stay-Regel); saveProfile, startProbe, enterProbe, probePoll, verdictCard, leaveProbe; profileView im Status-Poll inkl. Einstieg in Z6 bei probeRunning; Live-Region und Fokus nach UI-SPEC; Nojs-Zeile verborgen | e05e0efd |
| 2 | test_the_script_and_the_template_name_every_probe_code_alike, test_the_probe_poll_is_two_seconds, test_the_script_decides_the_probe_like_the_service, test_the_script_sends_only_profile_and_precision; Token-Gate um profile_confirmed im Skript erweitert | 4da4b1a0 |

## Verifikation

- `node --check php/js/admin.js` grün
- Wegwerf-Smoke mit Node und Minimal-DOM (danach gelöscht): Z2 vorbelegt, fp32 zeigt Reindex-Zeile, Start sendet nur profile/precision, Fokus auf Fortschritt, Download "143,1 MB of 381,5 MB", Verdikt narrow mit Ursache und Folge, Fokus auf "Stay on Economy", Stay speichert economy, busy wechselt in Z6 mit Satz
- Greps: POLL_PROBE_MS = 2000 1, ROUTE_PROFILE_CHECK 1, ROUTE_PROFILE 1, innerHTML/outerHTML/createElement/insertAdjacentHTML/document.write 0, guardToken/profile_confirmed 0
- `uv run pytest -q tests/test_admin_ui_contract.py`: 76 passed; ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture sauber
- Baumhash-Pin und Kataloge nicht angefasst

## Deviations from Plan

**1. [Rule 2] Zusätzliche Maps precisionSentences und guardCauseNames**
- **Found during:** Task 1
- **Issue:** Der Status-Poll muss #findling-profile-precision (precisionVerdict, Commit 76e3e345) und das Wächter-Banner (Z10 verschwindet mit dem nächsten Poll) aktualisieren
- **Fix:** beide Maps gleich $precisionSentences und $causeNames des Templates; Gate prüft precisionSentences mit
- **Commit:** e05e0efd

**2. Gate prüft zusätzlich PROBE_CAUSE_NEEDS gegen $probeCauseNeeds**, damit keine Hälfte einen Satz mit Loch zeigt, den die andere verbirgt (4da4b1a0).

## Hinweise für 27-13 (Kataloge)

Nur im Skript benutzte Schlüssel: `downloading the model, %1$s of %2$s`, `OCR with %s slots`, `Check running.`, `A check is already running. Its result appears here.`, `The profile was not saved. Nothing changed.`. Alle übrigen Sätze stehen auch im Template.

## Known Stubs

- Schritt ocr_n zeigt nur "Check running.", solange die Stand-Route keine Slotzahl liefert (ProbeService::state gibt numbers nicht aus).

## Threat Flags

Keine neue Fläche. T-27-39 (nur Textknoten, Codes über Maps, unbekannt verborgen), T-27-40 (Skript wählt nur die Beschriftung) und T-27-41 (nur profile und precision, Gate) umgesetzt.

## Self-Check: PASSED

- php/js/admin.js, backend/tests/test_admin_ui_contract.py geändert
- Commits e05e0efd und 4da4b1a0 im Log
