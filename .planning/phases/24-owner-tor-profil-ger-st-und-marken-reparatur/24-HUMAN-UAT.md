---
status: partial
phase: 24-owner-tor-profil-ger-st-und-marken-reparatur
source: [24-VERIFICATION.md]
started: 2026-09-28T09:00:00Z
updated: 2026-09-28T09:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. PHPUnit in CI (php.yml) nach dem Push
expected: php.yml laeuft gruen, einschliesslich ProfileControllerTest (neuer WR-02-Fall: Lesefehler antwortet 500 ohne Profilnamen). Lokal gibt es kein PHP; Push-Entscheid liegt beim Owner.
result: [pending]

### 2. Live-Durchstich auf der Test-Nextcloud
expected: `occ config:app:set findling profile --value=standard` setzen, eine Pollerrunde abwarten, `GET /status` lesen: gewaehltes Profil Standard, plausible Hardware-Werte (Kerne, Speicher, Architektur), nichts umgeschaltet. Gegenprobe mit Companion 1.3.x ohne Profil-Route: Container bleibt auf Sparsam.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
