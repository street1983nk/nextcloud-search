---
phase: 24
slug: owner-tor-profil-ger-st-und-marken-reparatur
status: verified
threats_total: 24
threats_closed: 24
threats_open: 0
asvs_level: 1
block_on: high
register_authored_at_plan_time: true
created: 2026-09-28
---

# Phase 24: Security

> Sicherheitsvertrag der Phase: Bedrohungsregister, akzeptierte Risiken, Prüfpfad.
> Jede Mitigation ist am Code belegt (Datei:Zeile), nicht an Doku oder Absicht.
> Stand nach den Review-Fixes WR-01 (637c02b), WR-02 (d0705e4) und dem UAT-Fix b345fa3.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| state.db meta -> Poller | gespeicherte Embedding-Marke gegen die gewünschte verglichen | eigener Schreibwert, keine Nutzerdaten |
| AppAPI-Umgebung -> Container | Admin-gesetzte und von AppAPI injizierte Variablen erreichen config.py | Konfigurationszahlen |
| cgroup/proc-Dateien -> Container | vom Kernel geliefert, auf fremden Hosts ungewohnter Inhalt möglich | Kerne, Speicher, Architektur |
| Companion-Antwort -> note_chosen | Profilname über OCS aus appconfig, per occ ungeprüft beschreibbar | Profilname (geschlossene Menge) |
| fremde ExApp -> OCS-Route /profile | jede installierte ExApp kann OCS-Routen mit AppAPI-Signatur rufen | Profilname |
| occ/Serverzugang -> appconfig | ungeprüfter Schreibweg für findling/profile | Profilname |
| Upgrade-Fenster | neuer Container mit altem Companion ohne Route | 404 |
| Admin-Browser/AppAPI -> GET /status | Route access_level ADMIN | Hardwarewerte, Profilstand |
| Container -> Logs | Startaussage der Hardware-Erkennung | nur Ausnahmetyp |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status | Evidence |
|-----------|----------|-----------|-------------|------------|--------|----------|
| T-24-01 | DoS | embedding_mark / Poller-Drift | mitigate | int8-Marke bytegleich zu 1.3 plus Gold-Ratchet | closed | backend/src/findling/store/vectors.py:306-310 (int8 = 4-teilige Basis); backend/tests/test_upgrade_compatibility.py:326-338 (GOLD_VECTOR_MARK_V1_3 als Literal); backend/tests/test_embedding_track.py:1225-1247 (1.3-Marke, keine Drift-Kette, keine Requeues) |
| T-24-02 | Tampering | Präzisionswechsel ohne Marke | mitigate | fp32-Suffix, Drift leert Kette und bettet neu ein; beide Richtungen getestet | closed | vectors.py:314 (`f"{base}/{weights}"`); test_embedding_track.py:1250-1274 (fp32 -> int8) und 1277-1299 (int8 -> fp32): Drift-Kette vollständig, chunk_count 0, Requeue KIND_EMBED; test_vector_store.py:404-407 |
| T-24-03 | Info Disclosure | ValueError-Meldung | mitigate | Meldung nennt den Wert nicht | closed | vectors.py:311-313 (statisch "unknown weight precision"); test_vector_store.py:411-415 (`"fp16" not in str(...)`) |
| T-24-04 | Tampering | explicit_int_from_environment | mitigate | nur gültige, bereichsgeprüfte, vom Default abweichende Werte; Gleichstand info.xml/config.py | closed | backend/src/findling/config.py:1077-1092 (leer/nicht ganzzahlig/<1/außerhalb bounds/gleich Default -> None); backend/tests/test_info_xml_defaults.py:82 (Gleichstand), :101-105 (Default nie Override); test_config.py:1162-1185 |
| T-24-05 | DoS | hardware.detect | mitigate | jede unlesbare/kaputte Datei ergibt None, nie eine Ausnahme | closed | backend/src/findling/hardware.py:44-59 (_read fängt OSError/ValueError, _positive_int), :166-179 (Callables in try/except), :112-124 (WR-01: v1-Sentinel-Boden 1<<60), :147-157 (b345fa3: min(memory.max, MemTotal)); test_hardware.py:88, 108, 131, 138, 144, 166, 191, 270 |
| T-24-06 | Info Disclosure | Hardwaredaten | accept | siehe AR-24-01 | closed | Begründung am Code bestätigt: hardware.py ohne logging-Import und ohne Netz (Zeilen 23-29); Ausgabe nur über /status mit ADMIN (backend/appinfo/info.xml:307-310) |
| T-24-07 | Info Disclosure | Logzeilen der Env-Leser | mitigate | neuer Leser loggt nicht; bestehende nennen nur Variablennamen | closed | config.py:1077-1092 ohne LOGGER-Aufruf; bestehende Leser config.py:1033-1208 nur `%s` = name; test_config.py:1188-1196 (`assert not caplog.records`) |
| T-24-08 | Tampering | note_chosen | mitigate | geschlossene Menge PROFILE_NAMES, Unbekanntes ändert nichts, kein Log | closed | backend/src/findling/profile.py:98 (PROFILE_NAMES), :314-315 (None/unbekannt -> return); profile.py ohne Logger (Imports :40-86); test_profile.py:354 |
| T-24-09 | DoS | Profil zwingt Box in OOM | mitigate | effective = min(gewählt, passend) plus RAM-Term; kein Wert im Betrieb verdrahtet | closed | profile.py:147-150 (min über PROFILE_ORDER), :171-176 (memory_term im min), hardware.py:147-157 (Schwelle min(memory.max, MemTotal), b345fa3); einziger Leser von snapshot() ist api/status.py:91/296 (grep über src/findling); test_profile.py:253, 258, 334, 345; test_hardware.py:270 |
| T-24-10 | DoS | Flattern durch Selbstmessung | mitigate | Hardware einmal je Start eingefroren | closed | einziger detect-Aufruf main.py:777 (Lifespan); Hardware frozen dataclass hardware.py:127; profile.py:299-303 note_hardware nur aus Lifespan; test_main_lifespan.py:1122, 1169-1178 (`to_thread(detect)` genau einmal); test_hardware.py:283 |
| T-24-11 | Info Disclosure | Logs | mitigate | profile.py loggt keine Profil- oder Umgebungswerte | closed | profile.py importiert kein logging (Zeilen 40-86), kein LOGGER im Modul |
| T-24-12 | Spoofing / Info Disclosure | ProfileController::profile | mitigate | ExAppRequired plus rejectForeignCaller als erste Anweisung, fremd -> 403; Antwort nur Profilname | closed | php/lib/Controller/ProfileController.php:51 (ExAppRequired), :55-58 (erste Anweisung), :81-93 (Vergleich mit BACKEND_APP_ID, 403), :61 (nur `profile`), :70 (WR-02: 500 ohne Namen); php/tests/Unit/ProfileControllerTest.php:109-129, 132-144 |
| T-24-13 | Tampering | SettingsService::profile | mitigate | geschlossene Menge PROFILES, Unbekanntes -> economy plus reject() ohne Wert | closed | php/lib/Service/SettingsService.php:101 (PROFILES), :277-281 (strict in_array, reject, PROFILE_DEFAULT), :365-371 (Kontext nur Zähler); ProfileControllerTest.php:93-107 |
| T-24-14 | EoP | Schreibweg | accept | siehe AR-24-02 | closed | Begründung am Code bestätigt: KEY_PROFILE nur gelesen (SettingsService.php:92, 273), kein saveProfile, ProfileController nur GET (:53) |
| T-24-15 | Info Disclosure | Logs (PHP) | mitigate | statische Log-Sätze, Profilwert nie im Kontext | closed | ProfileController.php:68 (statischer Satz, nur exception), :87 (nur Aufrufer-ID); SettingsService.php:367-370; ProfileControllerTest.php:96-101 (Kontext enthält "turbo" nicht) |
| T-24-16 | Tampering | DocumentQueue.profile | mitigate | nur str aus PROFILE_NAMES, sonst None; note_chosen prüft zweites Mal | closed | backend/src/findling/nc/queue.py:521-524 (isinstance str und in PROFILE_NAMES), profile.py:314; test_queue_client.py:445-452 (turbo, 3, None, {}, [], "standard", None) |
| T-24-17 | DoS | Poller-Runde bei fehlender Route | mitigate | jede Exception -> None, debug-Zeile, Runde läuft weiter | closed | queue.py:512-519 (`except Exception` -> debug, None); poller.py:751; test_queue_client.py:455-472 (werfende Fakes); test_poller.py:1788 (Companion ohne Route) |
| T-24-18 | DoS | Flattern bei Gateway-Aussetzern | mitigate | letzter erfolgreich gelesener Wert bleibt | closed | profile.py:314-315 (None ändert _CHOSEN nicht); test_profile.py:354 |
| T-24-19 | Info Disclosure | Logs (Queue) | mitigate | debug-Zeile ohne Antwortinhalt oder Ausnahmetext | closed | queue.py:518 (statischer Satz ohne Args); test_queue_client.py:469-472 (`str(error) not in`, args leer) |
| T-24-20 | Tampering | OCS-Schreibpfad | mitigate | GET ohne Allowlist-Eintrag, Gate A grün | closed | backend/src/findling/nc/client.py:485-488 (GET); backend/tests/test_readonly_gate.py:239-246 (Allowlist ohne /profile); test_queue_client.py:562 (Pfad-Literal genau einmal) |
| T-24-21 | Info Disclosure | StatusResponse.profile | mitigate | nur über bestehende ADMIN-Route, keine neue Route, keine Telemetrie | closed | backend/src/findling/api/status.py:412 (Feld in bestehendem Report), :606 (einzige Route /status); info.xml:307-310 (ADMIN); keine Netzimporte in status.py/profile.py/hardware.py |
| T-24-22 | DoS | Lifespan-Erkennung | mitigate | to_thread, try/except Exception, Start läuft mit Sparsam weiter | closed | backend/src/findling/main.py:776-779; test_main_lifespan.py:1146-1167 (werfender detect, 200, economy), :1169-1178 |
| T-24-23 | Tampering | Statusroute nebenwirkungsfrei | mitigate | _profile_report liest nur snapshot(); Test in beiden Zweigen | closed | status.py:289-322 (nur snapshot()), Importe :76-93 ohne detect/note_*; test_status_endpoint.py:1190 (BRANCHES volume/indexed_volume), :1234-1330 parametrisiert |
| T-24-24 | Info Disclosure | Logs (Lifespan) | mitigate | Warnung nennt nur den Ausnahmetyp | closed | main.py:779 (`type(error).__name__`); test_main_lifespan.py:1163-1167 ("PermissionError" enthalten, "/sys" nicht) |

*Status: open · closed*
*Disposition: mitigate (Umsetzung nötig) · accept (dokumentiertes Risiko) · transfer (Dritte)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-24-01 | T-24-06 | Hardwaredaten (Kerne, Speicher, Architektur, cgroup-Version) sind Betriebsdaten des eigenen Servers. detect() loggt keine Werte und sendet nichts; sichtbar nur über GET /status mit access_level ADMIN; keine Telemetrie (Projektregel). Am Code bestätigt: hardware.py ohne logging/Netz, info.xml:310 ADMIN. | Owner (Plan 24-02, Register zur Planzeit) | 2026-09-28 |
| AR-24-02 | T-24-14 | In Phase 24 gibt es keinen Schreibweg für das Profil außer `occ config:app:set` (erfordert Serverzugang, also bereits volle Rechte). Keine Schreibroute; saveProfile und ADMIN-FrontpageRoute folgen erst in Phase 27 und brauchen dort ein eigenes Register. Am Code bestätigt: KEY_PROFILE wird nur gelesen, ProfileController nur GET. | Owner (Plan 24-04, Register zur Planzeit) | 2026-09-28 |

*Akzeptierte Risiken tauchen in späteren Audits nicht erneut auf. AR-24-02 ist an Phase 27 gebunden: sobald dort eine Schreibroute entsteht, verfällt die Begründung.*

---

## Unregistered Flags

Keine. Einziger Threat-Flags-Abschnitt (24-02-SUMMARY.md) nennt keine neue Fläche und verweist auf T-24-05/06/07. 24-04/24-05-SUMMARY.md bestätigen nur registrierte IDs.

## Hinweise (informativ, keine Blocker)

- PHP-Belege (T-24-12, T-24-13, T-24-15) sind per Quelltext und Unit-Test-Inspektion geprüft; PHPUnit läuft nur in CI (24-HUMAN-UAT.md Test 1, pending bis zum Push).
- Review IN-02 (Default `weights=WEIGHTS_INT8` am Poller-Aufruf) berührt T-24-02 ab Phase 25: dann muss die tatsächlich geladene Präzision übergeben werden, sonst schreibt ein fp32-Bestand die int8-Marke. In Phase 24 lädt nur int8, daher heute kein offener Pfad.
- IN-04 (keine Groß-/Kleinschreibung-Normalisierung) ist fail-safe (economy), kein Sicherheitsbefund.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-28 | 24 | 24 | 0 | gsd-security-auditor (Belege per grep/Read; 14 Python-Testdateien: 713 passed, 1 skipped) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-28
