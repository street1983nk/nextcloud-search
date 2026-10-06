---
status: partial
phase: 24-owner-tor-profil-ger-st-und-marken-reparatur
source: [24-VERIFICATION.md]
started: 2026-09-28T09:00:00Z
updated: 2026-09-28T10:30:00Z
---

## Current Test

[Test 1 wartet auf den Push-Entscheid des Owners]

## Tests

### 1. PHPUnit in CI (php.yml) nach dem Push
expected: php.yml laeuft gruen, einschliesslich ProfileControllerTest (neuer WR-02-Fall: Lesefehler antwortet 500 ohne Profilnamen). Lokal gibt es kein PHP; Push-Entscheid liegt beim Owner.
result: [pending]

### 2. Live-Durchstich auf der Test-Nextcloud
expected: `occ config:app:set findling profile --value=standard` setzen, eine Pollerrunde abwarten, `GET /status` lesen: gewaehltes Profil Standard, plausible Hardware-Werte (Kerne, Speicher, Architektur), nichts umgeschaltet. Gegenprobe mit Companion 1.3.x ohne Profil-Route: Container bleibt auf Sparsam.
result: passed (mit Befund, behoben)

Durchgefuehrt 2026-09-28 auf der Dev-Instanz (findling-nextcloud, NC 34.0.3, Port 8090; Companion aus dem Repo per occ upgrade auf 1.3.0; Backend mit HEAD-Code neu gestartet):

- Ohne gesetztes Profil: chosen/effective/suggested = economy, alle Werte aus dem Profil.
- Nach `occ config:app:set findling profile --value=standard` und einer Pollerrunde: chosen = standard. Die OCS-Route weist einen Admin-Aufruf mit "ExApp required" ab (nur das eigene Backend liest).
- Das Dev-Backend laeuft auf dem Windows-Host (kein /proc/meminfo, keine cgroups): Speicher unbekannt, daher effective = economy, downgraded = true. Das ist die vorgesehene vorsichtige Rueckstufung.
- Linux-Erkennung separat im Backend-Image mit HEAD-Code unter harten Docker-Grenzen: --cpus=4/--memory=8g gibt cgroup v2, 4 Kerne, Limit 8 GiB, Vorschlag standard; gewaehlt performance wird auf standard zurueckgestuft. --cpus=2/--memory=3g gibt Vorschlag economy, standard und performance werden auf economy zurueckgestuft.
- Die Gegenprobe mit einem Companion 1.3.x ohne Profil-Route ist durch Tests abgedeckt (404 = None = letztes bekanntes Profil, sonst Sparsam) und wurde nicht live gefahren.

BEFUND (behoben in b345fa3): --cpus=8/--memory=16g auf einer VM mit 8 GB physischem Speicher las als 16-GB-Box, ueberschritt die 12-GB-Schwelle und loeste performance mit 6 OCR-Slots auf. threshold_memory_bytes nahm memory.max ungeprueft. Fix: min(memory.max, MemTotal), RED/GREEN-Test in test_hardware.py, Gegenprobe live: Schwelle 7,6 GB, performance faellt auf standard zurueck. Suite 3495 passed, alle Gates gruen.

## Summary

total: 2
passed: 1
issues: 1
pending: 1
skipped: 0
blocked: 0

## Gaps

- Befund aus Test 2 (Limit ueber dem physischen Speicher hob die Schwelle an): behoben in b345fa3, kein offener Gap.
