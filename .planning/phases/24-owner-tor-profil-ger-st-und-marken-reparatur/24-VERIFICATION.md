---
phase: 24-owner-tor-profil-ger-st-und-marken-reparatur
verified: 2026-09-28T00:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "PHPUnit-Lauf der Companion-Tests in CI (php.yml), sobald der Owner pusht: php/tests/Unit/ProfileControllerTest.php inkl. WR-02-Fall (500 ohne Profilnamen) und SettingsService::profile()"
    expected: "Alle PHPUnit-Fälle grün; ProfileController antwortet 200 {profile} für das Findling-Backend, 403 für fremde ExApp, 500 bei Lesefehler; unbekannter/fehlender appconfig-Wert ergibt economy"
    why_human: "Kein lokales PHP; PHP-Verhalten ist nur durch Code-Lesen und die Python-Gleichstandstests belegt, nicht durch einen Lauf"
  - test: "Live-Durchstich auf der Test-Nextcloud: occ config:app:set findling profile --value=standard, eine Pollerrunde abwarten, dann GET /status lesen"
    expected: "Block profile meldet chosen=standard, suggested/effective passend zur Box, Hardware-Block mit cgroup-bewussten Werten; mit Companion 1.3.x ohne Route bleibt economy und der Container läuft weiter"
    why_human: "Route-Registrierung per ApiRoute-Attribut, ExAppRequired-Auth über AppAPI und die echte cgroup-Lesung im Container sind nur live prüfbar; lokal nur mit Fakes und Fake-Bäumen getestet"
---

# Phase 24: Owner-Tor, Profil-Gerüst und Marken-Reparatur Verification Report

**Phase Goal:** Die Grundsatzentscheide des Milestones sind schriftlich gefallen, bevor Code sie implizit trifft; danach kennt der Container Profile als Anteils-Formel an der erkannten Hardware, schlägt ein Profil vor, ohne umzuschalten, und die Vektor-Marke erkennt einen Präzisionswechsel.
**Verified:** 2026-09-28 (HEAD d3f62c0)
**Status:** human_needed
**Re-verification:** Nein, Erstverifikation

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Datierter Owner-Entscheid zu Profilweg, Anteilen inkl. Store-Satz und fp32-Lieferweg, VOR dem ersten Code | VERIFIED | 24-CONTEXT.md D-24-01..07 (Commit 0988fc5, 27.09. 14:42), D-24-08 (b528014, 15:09). `git log ebf8b17..b528014 --name-only`: nur .planning-Dateien. Erster Code-Commit in backend/src oder php/lib: 9a59a88 um 15:38. Store-Satz D-24-04 wörtlich in docs/profiles.md:50 |
| 2 | Admin setzt Profil über den entschiedenen Weg (OCS, occ), Container meldet berechnete Werte mit Obergrenzen; Env-Var überstimmt sichtbar | VERIFIED | SettingsService::profile() (geschlossene Menge, Default economy), ProfileController GET /profile (ApiRoute wie QueueController/ReconcileController, 403 für fremde ExApp, 500 bei Lesefehler nach WR-02). client.read_profile -> DocumentQueue.profile() -> poller.run_once `note_chosen(await queue.profile())` vor dem Claim (poller.py:751). Spot-Check: 16 Kerne/32 GB, performance -> ocrSlots 15 (Kernterm C-1, Cap 16); FINDLING_OCR_MAX_PAGES=45 -> ocrMaxPages 45, Quelle env; =30 (injizierter Default) -> Quelle profile |
| 3 | Sparsam ohne Zutun, Wert für Wert gepinnt; Store-Zahl und test_store_metadata.py unverändert | VERIFIED | test_profile.py:172 parametrisiert über 5 Hardware-Fälle, Literal UND Konstante je Feld; test_the_constants_behind_economy_are_the_running_ones prüft laufende Konstanten (INDEX_WORKERS, EMBED_THREADS, num_threads=1 in writer/rebuild). `git diff 0988fc5 HEAD -- backend/tests/test_store_metadata.py`: leer. config.py-Diff: keine entfernte Zeile, settings()/Settings unangetastet. Ruhezustand im Spot-Check: economy mit exakt heutigen Werten |
| 4 | Statusroute meldet Kerne, Speicher, Architektur cgroup-bewusst und Vorschlag, schaltet nichts; bei Schrumpfung größte passende Stufe, gemeldet | VERIFIED | hardware.detect(): min(process_cpu_count, cpu.max), memory.max sonst MemAvailable (formula) bzw. MemTotal (Schwellen), v1-Fallback mit Sentinel-Boden (WR-01 637c02b). main.py:777 einmal beim Start per to_thread vor Modellladen, Fehler -> economy. status.py ProfileReport mit chosen/suggested/effective/downgraded/hardware/values/sources. Spot-Check: 4 Kerne/8 GB, chosen performance -> effective standard, downgraded True. Keine Schreibpfade aus snapshot() |
| 5 | int8/fp32-Wechsel desselben Modells löst Vektor-Reindex aus; alte Marke ohne Präzision = int8, kein Re-Embed | VERIFIED | vectors.py:271 embedding_mark: int8 durch Abwesenheit (byte-identisch `multilingual-e5-small/int8/384/1024`), fp32 hängt `/fp32` an, Unbekanntes -> ValueError. Poller nutzt embedding_mark (poller.py:2111), Read-Side ebenso (resources.py:265). Tests: test_a_v1_3_mark_without_a_precision_is_read_as_int8_and_nothing_is_re_embedded, beide Wechselrichtungen mit forget_all + Requeue embed (test_embedding_track.py:1225-1295), Gold-Literal test_upgrade_compatibility.py:338 |

**Score:** 5/5 truths verified

Anmerkung zu Truth 5: Der Wechsel int8 -> fp32 wird im Test durch Umbiegen des `embedding_mark`-Aufrufs simuliert, weil ein echtes fp32-Laden erst mit MOD-02 (Phase 25) existiert. Das ist der Phasenschnitt (D-24-05); die Produktionsaufrufstelle stützt sich noch auf den int8-Default (Review IN-02, als Merker für Phase 25 dokumentiert).

### Plan-Must-Haves (zusätzlich geprüft)

Alle Truths der Pläne 24-01 bis 24-06 decken sich mit dem Code: Konstanten D-24-03/06/08 in config.py:853-909, explicit_int_from_environment (config.py:1057) mit Default-Gleichheit -> None, info.xml-Gleichstandstest, geschlossene Profilmenge PHP/Python, note_chosen(None/unbekannt) ändert nichts (Spot-Check "kept performance"), kein Profilwert in Poller/Writer/Sandbox verdrahtet, docs/profiles.md mit D-24-01..08 datiert und fp32-Nachladeweg als Phase-25-Entscheid.

### Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| backend/src/findling/profile.py | VERIFIED | Formel, Vorschlag, wirksam, Overrides, Prozesszustand; importiert von status.py, poller.py, main.py, queue.py |
| backend/src/findling/hardware.py | VERIFIED | cgroup v2/v1/none, nie werfend; von main.py aufgerufen |
| backend/src/findling/config.py | VERIFIED | Profilkonstanten außerhalb des lru_cache |
| backend/src/findling/store/vectors.py | VERIFIED | embedding_mark mit weights |
| backend/src/findling/api/status.py | VERIFIED | profile-Block in beiden Zweigen |
| backend/src/findling/nc/client.py, nc/queue.py, worker/poller.py | VERIFIED | Lesedraht je Runde |
| php/lib/Controller/ProfileController.php, php/lib/Service/SettingsService.php | VERIFIED (Code gelesen, Lauf nur CI) | Route, Fremd-ExApp-Guard, 500 bei Lesefehler |
| docs/profiles.md | VERIFIED | Owner-Tor datiert, Store-Satz wörtlich |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| poller.run_once | profile.note_chosen | `note_chosen(await queue.profile())` vor claim | WIRED |
| DocumentQueue.profile | PHP /ocs/v2.php/apps/findling/profile | client.read_profile | WIRED |
| main lifespan | profile.note_hardware | `note_hardware(await asyncio.to_thread(detect))` | WIRED |
| api/status | profile.snapshot | `_profile_report()` in beiden Antwortzweigen | WIRED |
| poller Leerlaufrunde | embedding_mark | Driftvergleich -> forget_all, Marke, Requeue | WIRED |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real Data | Status |
|----------|------|--------|-----------|--------|
| /status profile.hardware | Hardware | detect() über Kernel-Dateien beim Start | ja | FLOWING |
| /status profile.chosen | Profile | appconfig über OCS je Pollerrunde | ja (live unbestätigt, siehe Human) | FLOWING |
| /status profile.values | ProfileValues | resolve(effective, hardware) inkl. Env | ja | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Phase-Tests | `uv run pytest` (12 Dateien: profile, hardware, profile_wire, status_endpoint, upgrade_compatibility, embedding_track, vector_store, config, info_xml_defaults, store_metadata, queue_client, main_lifespan) | 625 passed | PASS |
| Ruhezustand economy = heutige Werte | Skript gegen _profile_report() | ocrSlots 1, Heap 50_000_000, 30 Seiten, 300 dpi | PASS |
| Schrumpfung | chosen performance, 4 Kerne/8 GB | effective standard, downgraded True | PASS |
| Env überstimmt, injizierter Default nicht | OCR_MAX_PAGES 45 vs. 30 | env vs. profile | PASS |
| Lint/Format | `ruff check`, `ruff format --check` | grün | PASS |

### Probe Execution

Keine Probes deklariert (scripts/*/tests/probe-*.sh nicht vorhanden, Phase keine Migrationsphase). SKIPPED.

### Requirements Coverage

| Requirement | Source Plan | Status | Evidence |
|-------------|------------|--------|----------|
| PROF-01 | 24-02, 24-03, 24-06 | SATISFIED | Anteils-Formel mit Caps in profile.ocr_slots, gemeldet in /status |
| PROF-02 | 24-03 | SATISFIED | Economy-Pin-Test, Store-Gate unverändert |
| PROF-03 | 24-02, 24-04, 24-05, 24-06 | SATISFIED | Weg B entschieden und gebaut, Env-Override mit Quelle env |
| HW-01 | 24-02, 24-03, 24-06 | SATISFIED | cgroup-bewusste Erkennung, Vorschlag, Rückstufung gemeldet, kein Umschalten |
| MOD-01 | 24-01 | SATISFIED | Präzision in der Marke, Upgrade-Test ohne Re-Embed |

Keine verwaisten Requirements: REQUIREMENTS.md ordnet Phase 24 genau diese fünf IDs zu.

### Anti-Patterns Found

Keine TBD/FIXME/XXX in den geänderten Dateien. Review-Befunde WR-01/WR-02 behoben (637c02b, d0705e4). IN-01..06 offen als Info dokumentiert (u. a. IN-02 int8-Default an der Poller-Aufrufstelle, IN-03 fehlender Paritätstest PROFILE_VALUE_KEYS), nicht zielgefährdend.

### Human Verification Required

1. **PHPUnit in CI** , nach Owner-Push php.yml abwarten; erwartet grün inkl. WR-02-Fall. Grund: kein lokales PHP.
2. **Live-Durchstich** , `occ config:app:set findling profile --value=standard`, eine Pollerrunde, dann `GET /status`; erwartet chosen standard und plausibler Hardware-Block; mit Companion 1.3.x bleibt economy. Grund: AppAPI-Auth, Attribut-Routing und echte cgroup-Lesung nur live prüfbar.

### Gaps Summary

Keine Lücken. Alle fünf Roadmap-Kriterien sind im Code belegt und durch eigene Testläufe und Spot-Checks bestätigt. Offen sind nur der CI-Lauf der PHP-Tests und ein Live-Durchstich auf der Test-Nextcloud.

---

_Verified: 2026-09-28_
_Verifier: Claude (gsd-verifier)_

## Nachtrag Pre-Close v1.4 (2026-10-06)

Beide Human-Verification-Punkte sind inzwischen belegt:
1. PHPUnit in CI: php.yml lief seit Phase 28 mehrfach gruen, zuletzt Tag-Lauf
   37470623202 (v1.4.0, 589 Tests) inkl. ProfileControllerTest; erster Beleg
   Lauf 37452332197.
2. Live-Durchstich Profilroute: in Phase 28 auf echten Boxen je Zelle gefahren
   (Profilwechsel Teil der 18-Zellen-Matrix); am 06.10. zusaetzlich live auf der
   Dev-Instanz gesehen (Statuskarte mit Profilblock, K6-Banner mit Companion
   1.3.0, economy nach Upgrade im CI-Bein "Store upgrade 5").
Status deshalb auf passed gesetzt.
