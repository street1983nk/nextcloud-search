---
phase: 41-findling-1-6-2-backup-pause-schalter-37-backup-doku-25-fixes
verified: 2026-11-04T18:37:06Z
status: gaps_found
score: 6/7 must-haves verified (6/6 ROADMAP-Kriterien, 1 Plan-Wahrheit aus 41-11 offen)
overrides_applied: 0
gaps:
  - truth: "Belegkette steht in docs/store-listing.md '# Release 1.6.2 (<Datum>)'; STATE.md und ROADMAP.md tragen den Stand (41-11-PLAN must_haves)"
    status: failed
    reason: "docs/store-listing.md hat keinen Abschnitt '# Release 1.6.2'. Jede Version seit 1.4.1 hat einen solchen Abschnitt (Zeilen 2888 bis 3248), 41-CONTEXT nennt ihn als kanonisches Belegmuster, und das automatische verify von 41-11 (grep '# Release 1.6.2' und beide HTTP-201-Zeilen in docs/store-listing.md) schlägt am Kopf fehl. Die Belege selbst existieren (41-11-SUMMARY.md, 41-ISSUE-ANTWORTEN.md, ROADMAP Kriterium 6), nur nicht an der Stelle, an der der nächste Release-Plan sie als Vorlage sucht. Kein Einfluss auf das Produkt."
    artifacts:
      - path: "docs/store-listing.md"
        issue: "Abschnitt '# Release 1.6.2 (04.11.2026)' fehlt; enthält weder 'release findling v1.6.2: HTTP 201' noch 'release findling_backend v1.6.2: HTTP 201'"
    missing:
      - "Abschnitt '# Release 1.6.2 (04.11.2026)' direkt vor '# Release 1.6.1 (02.11.2026): Sicherheitsupdate' (heute Zeile 2888) einfügen, Form wie 1.6.1/1.6.0"
      - "Inhalt: Tag v1.6.2 annotiert auf ba098b00f61cb57dfa8bc127c264e198e4afa313; sieben Tag-Läufe success (Release archives 41869261561 mit zweimal 'Verified OK', PHP 41869261491, Python 41869261151, Integration 41869261583, Resilience 41869261405, Multi-arch 41869261338, HaRP 41869261143 inkl. Schritt 'Backup pause, across restarts'); Release immutable, findling.tar.gz 656 338 B und findling_backend.tar.gz 44 225 B je mit .sig; Store submission 41875127182 HTTP 401 (Token), 41885026379 mit den wörtlichen Zeilen 'release findling v1.6.2: HTTP 201' und 'release findling_backend v1.6.2: HTTP 201'; Store-API apps.json findling und appapi_apps.json findling_backend nennen 1.6.2 (04.11.2026 18:28Z); Verweis auf die Release-Notiz im Abschnitt 'Entwurf v1.6.2 (Gesamttext)'"
      - "Reiner Doku-Commit auf main (Tag bleibt unberührt), danach: grep -q '# Release 1.6.2' docs/store-listing.md && grep -q 'release findling_backend v1.6.2: HTTP 201' docs/store-listing.md; backend/tests/test_store_metadata.py und das Gate scan_full_text_1_6_2 lokal grün"
---

# Phase 41: Findling 1.6.2 Verifikationsbericht

**Phasenziel:** Findling 1.6.2 (beide Apps) im Store mit den Zusagen aus Issue #37 und #25 und den vier Nachaudit-Befunden aus 40-NACHAUDIT.md, die 1.6.1 bewusst nicht mitnahm.
**Geprüft:** 2026-11-04T18:37:06Z
**Status:** gaps_found (Produktziel erreicht; eine Doku-Lücke aus Plan 41-11)
**Re-Verifikation:** Nein, erste Prüfung

Code-Stand: Tag `v1.6.2` = `ba098b00f61cb57dfa8bc127c264e198e4afa313` (lokal per `git rev-parse v1.6.2^{}`). `git diff ba098b00 HEAD` ändert nur `.planning/`, der geprüfte Code ist also der ausgelieferte. Nicht abgefragt: apps.nextcloud.com (Rate-Limit-Vorgabe); Store-Stand aus 41-ISSUE-ANTWORTEN.md und dem Log von Lauf 41885026379.

## Zielerreichung

### Beobachtbare Wahrheiten

| # | Wahrheit | Status | Beleg |
|---|----------|--------|-------|
| 1 | SC1 Backup-Pause (#37): occ pause/resume, Admin-Schalter, Indexer/Embedding/Poller ruhen, WAL gecheckpointet, Tantivy geschlossen, Suche läuft, übersteht Neustart, Negativtests | VERIFIED | `php/appinfo/info.xml:321` registriert PauseCommand und ResumeCommand (`setName('findling:pause')`, `findling:resume`); `SettingsController::setPause` (POST /admin/pause) und `php/js/admin.js` ROUTE_PAUSE schreiben denselben appconfig-Schlüssel `paused` (SettingsService:236); ProfileController liefert `paused` aus; `worker/pause.py` PauseCoordinator hält Poller, Runner (Embedding), Reconcile, GuardWatch, wartet auf `_writers_rest` (Batch, Rebuild, Probe, fp32-Abruf), dann `quiesce_for_backup` (Writer close mit wait_merging_threads, Track zu) und `PRAGMA wal_checkpoint(TRUNCATE)` auf state.db und vectors.db, erst dann `paused`; verdrahtet in `main.py:663-680, 1216-1231`. Tests: `test_backup_pause.py` (u. a. pass_in_flight, pause_twice_and_resume_twice_are_idempotent, unreadable_wish_keeps_the_writers_held, search_answers_while_paused, paused_leaves_both_wal_files_empty), `PauseCommandTest.php` (PauseTwice, ResumeTwice, OddStatusValue). Neustart: HaRP-Lauf 41869261143 Schritt "Backup pause, across restarts of the backend and of Nextcloud" success, Log "pause after the container restart: paused, indexed still 12" und "pause after the Nextcloud restart: paused" |
| 2 | SC2 Backup-Doku: docker stop/start, Einstellungen in NC-appconfig, Index unverschlüsselt, dreisprachig | VERIFIED | `docs/backup.md`, `backup.en.md`, `backup.fr.md`: Weg A `docker stop/start nc_app_findling_backend`, appconfig-Zeile, "unverschlüsselt" / "unencrypted" / "non chiffré", Weg B Pause mit `occ findling:pause --wait`; verlinkt aus README.md/.en/.fr und admin-page.md; `docs/backup.en.md` liegt im Tag (Link der #37-Antwort löst auf); `test_backup_docs.py` vorhanden; keine ASCII-Umlaute gefunden |
| 3 | SC3 #25: embeddedLeftOut über 100 000 asynchron und gecacht, Repräsentant = größtes files_seen, Tests mit 113 851 und ungleichen Mitgliedern | VERIFIED | `api/status.py:855-856` über `LEFT_OUT_EMBEDDED_SYNC_CEILING` `_cached_left_out` (Hintergrund-Thread single flight, Cache je leaveOut-Liste und Stock-Kennung, kein Deckel); `ScanStatsService.php:470-491` usort nach -filesSeen, dann finished, dann id; Tests `test_phase40_audit.py:835` (113 851), `test_status_leave_out.py:201`, `ScanStatsServiceTest.php:237` (246 053 statt 178 551) |
| 4 | SC4 F-40N-01..04 behoben, Negativtest zuerst | VERIFIED | Commit-Reihenfolge RED b535151f vor den fix-Commits 59119398, a30eb009, a4b5f4d8, 2a9c3511, 8397d93f (alle im Tag); Tests mit F-40N-01..04 in test_poller.py, test_reconcile.py, test_gateway_client.py, test_status_endpoint.py, test_store_repo.py |
| 5 | SC5 Audit über den ganzen Delta v1.6.1..Kopf, Fixes ab MEDIUM | VERIFIED | 41-AUDIT.md: v1.6.1..738a1373 (0 CRIT/HIGH/MEDIUM, 4 LOW), Nachaudit 738a1373..efdca684 (LOW-Fixes) und efdca684..5dc1aa12 (#44); Code-Diff 5dc1aa12..ba098b00 nur CHANGELOG.md, docs/store-listing.md, backend/tests/test_store_metadata.py, also kein unauditierter Code im Tag |
| 6 | SC6 Owner-Runde vor dem Tag, Tag v1.6.2, beide Archive signiert, beide Uploads HTTP 201, Antworten #37/#25 nach Store-Release | VERIFIED | 41-ABNAHME.md "GO: ja", Gesamttext-Abschnitt in store-listing.md; alle sieben Tag-Läufe success auf ba098b00 (gh run view); Release archives 41869261561 zweimal "Verified OK"; Release immutable mit beiden .sig; Store submission 41885026379 Log "release findling v1.6.2: HTTP 201" (18:13:54Z) und "release findling_backend v1.6.2: HTTP 201" (18:13:55Z); Kommentare #25 18:19:27Z, #44 18:19:29Z, #37 18:24:04Z, alle nach dem Upload; Lockstep 1.6.2 in beiden info.xml und image-tag, CHANGELOG [1.6.2]. Abweichung #37 (vorzeitig geschlossen 15:21:48Z durch Commit-Schlüsselwort, kein Kommentar vor dem Release, angepasster Schlussabsatz mit Owner-Freigabe) ist vom Owner akzeptiert |
| 7 | 41-11 Plan-Wahrheit: Belegkette in docs/store-listing.md "# Release 1.6.2 (<Datum>)" | FAILED | Kein solcher Abschnitt; letzter Release-Abschnitt ist "# Release 1.6.1 (02.11.2026)" (Zeile 2888). Siehe Gaps |

**Score:** 6/7 (alle sechs ROADMAP-Kriterien erfüllt)

### Erforderliche Artefakte

| Artefakt | Erwartet | Status | Details |
|----------|----------|--------|---------|
| `backend/src/findling/worker/pause.py` | PauseCoordinator, WAL-Checkpoint | VERIFIED | 462 Zeilen, in main.py verdrahtet, Status über `publish`/`pause_state` |
| `php/lib/Command/PauseCommand.php`, `ResumeCommand.php` | occ-Befehle | VERIFIED | in info.xml registriert, `--wait` mit Timeout |
| `php/lib/Controller/SettingsController.php`, `php/js/admin.js`, `php/templates/admin.php` | Admin-Schalter | VERIFIED | POST /admin/pause, l10n in 16 Katalogen |
| `docs/backup*.md` | Doku DE/EN/FR | VERIFIED | siehe Wahrheit 2 |
| `scripts/ci/backup_pause_proof.sh` | CI-Beweis über Neustarts | VERIFIED | aus deploy-harp.yml:1971 aufgerufen, auf dem Tag grün |
| `docs/store-listing.md` "# Release 1.6.2" | Belegkette | MISSING | siehe Gaps |

### Key-Links

| Von | Nach | Über | Status |
|-----|------|------|--------|
| occ / Admin-Schalter | appconfig `paused` | SettingsService | WIRED |
| appconfig | Container | ProfileController `paused` → `pause_wish_reader()` | WIRED |
| PauseCoordinator | Poller, Embedding-Runner, Reconcile, GuardWatch | attach_* in main.py | WIRED |
| Status-Route | Admin-Seite / `occ findling:pause --wait` | `pause_state()` | WIRED |
| status.py `_cached_left_out` | AdminViewService::leftOutCounts | embeddedLeftOut | WIRED |

### Data-Flow (Level 4)

| Artefakt | Variable | Quelle | Echte Daten | Status |
|----------|----------|--------|-------------|--------|
| Admin-Pausezeile | pause/pausedSince | PauseCoordinator über Status-Route | ja, im CI-Lauf gegen echte Instanz | FLOWING |
| Dedup-Nenner | embeddedLeftOut | Hintergrundzählung vectors.db | ja (None bis zur ersten Zählung, laut Doku "reload or two") | FLOWING |

### Verhaltensprüfungen

| Verhalten | Befehl | Ergebnis | Status |
|-----------|--------|----------|--------|
| Tag-Läufe | `gh run view <id> --json conclusion` für sieben Läufe | alle success, headSha ba098b00 | PASS |
| Store-Upload | `gh run view 41885026379 --log` | zweimal HTTP 201 | PASS |
| Signatur | `gh run view 41869261561 --log` | zweimal "Verified OK" | PASS |
| Pause über Neustart | `gh run view 41869261143 --log` | paused nach Container- und NC-Neustart, Zähler unverändert | PASS |
| Tag-Links | `git cat-file -e v1.6.2:<pfad>` für alle blob/v1.6.2-Pfade und docs/backup.en.md | alle vorhanden | PASS |

Lokale Python-Teilläufe nicht gefahren; CI auf dem Tag ist der Beleg (Vorgabe).

### Probe-Ausführung

Keine `scripts/*/tests/probe-*.sh` in der Phase deklariert. Übersprungen.

### Anforderungen

| Anforderung | Quelle | Status | Beleg |
|-------------|--------|--------|-------|
| Owner-GO 29.10./30.10./02.11.2026 | ROADMAP Phase 41 | SATISFIED | Kriterien 1 bis 6 erfüllt |

### Anti-Pattern

| Datei | Zeile | Muster | Schwere | Wirkung |
|-------|-------|--------|---------|---------|
| (Phasen-Delta backend/src, php/lib, php/js, php/templates, scripts, docs) | | TBD/FIXME/XXX | | keine Treffer |
| Commit f88b46e7 | | "closes" vor #37 | Warnung | schloss #37 vor dem Store-Release; Lehre in 41-ISSUE-ANTWORTEN.md festgehalten |

### Menschliche Prüfung

1. **UI-Sichtung der Backup-Pause in einer laufenden 1.6.2-Instanz**
   Test: Admin-Seite öffnen, "Indexierung pausieren" schalten, Statuszeile "Pause wird vorbereitet" bis "pausiert" beobachten, dann fortsetzen; DE und EN.
   Erwartet: Schalter und Zustandssätze passen zu docs/backup.md, keine Sprachfehler, Suche bleibt nutzbar.
   Warum Mensch: Optik und Wortlaut der Admin-Seite; in STATE.md als offener Owner-Punkt geführt.
2. **Forum-Post I1 (Thread 249775)** durch den Owner, nicht Teil der Erfolgskriterien.

### Zusammenfassung der Lücken

Das Produktziel ist erreicht: beide Apps 1.6.2 laut Upload-Log im Store, alle Zusagen aus #37 und #25 sowie F-40N-01..04 im Code mit Tests und grünem CI auf dem Tag, Audit ohne unauditierten Code-Rest.

Offen ist eine reine Doku-Lücke aus Plan 41-11: der Abschnitt "# Release 1.6.2" in docs/store-listing.md fehlt. Urteil: echte, aber kleine Lücke. Sie bricht die Belegkette, die seit 1.4.1 für jede Version an genau dieser Stelle steht und die der nächste Release-Plan als Vorlage liest; das automatische verify von 41-11 ist am Kopf rot. Behebung ohne Tag-Bewegung per Doku-Commit (Inhalt siehe `gaps.missing`). Kein Blocker für Phase 42.

---

_Geprüft: 2026-11-04T18:37:06Z_
_Prüfer: Claude (gsd-verifier)_
