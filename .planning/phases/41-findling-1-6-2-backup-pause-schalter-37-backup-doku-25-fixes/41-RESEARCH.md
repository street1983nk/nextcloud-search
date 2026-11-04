# Phase 41: Findling 1.6.2 (Backup-Pause, Backup-Doku, #25, Nachaudit-Fixes) - Research

**Researched:** 2026-11-04
**Domain:** Brownfield-Änderung beider Apps (Python-ExApp `backend/`, PHP-Companion `php/`): Arbeitsruhe aller Schreiber mit konsistentem Volume, asynchrone Zählung im Status-Pfad, Coverage-Repräsentant, vier Nachaudit-Fixes, Release 1.6.2
**Confidence:** HIGH (alles am Code von `main` 91bd49f8 belegt; SQLite-Semantik aus der offiziellen Doku)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Backup-Pause-Schalter (#37, Owner-GO 30.10.2026)
- D-41-01: Zwei Wege, gleiche Wirkung: `occ findling:pause` / `occ findling:resume` (PHP-Companion) und ein Schalter auf der Admin-Seite.
- D-41-02: In der Pause ruhen Indexer, Embedding und Poller (keine neuen Claims, laufender Batch endet sauber oder wird ohne Retry-Gutschrift-Schaden zurückgegeben).
- D-41-03: Beim Eintritt in die Pause: SQLite-WAL checkpointen (TRUNCATE) und Tantivy committen, damit das Volume konsistent kopierbar ist; erst danach meldet der Status "paused" (Backup darf erst dann starten).
- D-41-04: Die Suche läuft in der Pause weiter (lesend).
- D-41-05: Pause-Zustand übersteht einen Neustart von Container und Nextcloud (kein stilles Auto-Resume).
- D-41-06: Zusage im Issue wörtlich: "indexing stops and everything is flushed to disk while search keeps working".

#### Backup-Doku (#37)
- D-41-07: Abschnitt Backup in der Doku: Weg A docker stop / Volume sichern / docker start; Weg B Pause-Schalter; Einstellungen liegen in der NC-Datenbank (appconfig), nicht im Volume; Volume ist komplett neu aufbaubar, Backup spart nur Zeit (OCR/Embeddings); Index enthält extrahierten Text unverschlüsselt, Backup behandeln wie Datei-Backup.
- D-41-08: Doku dreisprachig wie die übrigen Nutzer-Dokus (DE zuerst), kurze Faktenliste (Owner-Regel kurze Produkttexte).

#### Issue #25 (Owner-GO 29.10.2026)
- D-41-09: embeddedLeftOut nicht mehr bei LEFT_OUT_EMBEDDED_CEILING=100_000 (status.py:153) überspringen; Zählung asynchron im Hintergrund und gecacht (Muster Kandidat F aus Phase 40), damit AdminViewService::leftOutCounts() beide Zahlen bekommt und der Dedup nicht still ausfällt.
- D-41-10: Repräsentant einer Share-Gruppe in ScanStatsService.php:474 = Mitglied mit größtem files_seen statt kleinster finished-ID.
- D-41-11: Testfälle aus dem Issue: indexedLeftOut 113 851; Mitglieder 28k bis 112k je Share; Nenner ~246k statt 178k.

#### Nachaudit 1.6.0 (Owner-Entscheid 29.10.2026)
- D-41-12: F-40N-01 bis F-40N-04 aus 40-NACHAUDIT.md beheben; Entwurf 40-07-PLAN.md (untracked, für 1.6.1 geschrieben) ist Vorlage, nicht verbindlich; jeweils Negativtest zuerst (RED).

#### Release
- D-41-13: Version 1.6.2 an allen Lockstep-Stellen, CHANGELOG, Upgrade-Strecke ab v1.5.0 (wie 1.6.1), beide Apps gleiche Version.
- D-41-14: Audit Security/Bugs/Performance über das Delta v1.6.1..Kopf, Fixes ab MEDIUM (Vorlage 40-08).
- D-41-15: Eine schlanke Owner-Runde (Release-Notiz, neue nutzersichtbare Texte, Umlaut-Audit) vor dem Tag (Vorlage 40-09); Store-Text nur ändern, wenn nötig.
- D-41-16: Tag, Signatur, Store-Submit (store-submit.yml) und Issue-Antworten (#37, #25) nur nach Owner-Wort; Issue-Antworten erst NACH Store-Release (Dauerregel). Classifier blockt Tag-Push, Merge, Store-POST: Owner führt diese Schritte aus.
- D-41-17: Keine Inhalte verlassen den Server (Findling-Regel 02.11.); kein externer Dienst.

### Claude's Discretion
- Wo der Pause-Zustand gespeichert wird (appconfig der Companion vs. Backend-Datei), solange D-41-05 hält und es genau eine Quelle der Wahrheit gibt.
- Form des Admin-Schalters und Statustext, im Stil der bestehenden Admin-Seite, l10n-Kette wie üblich.
- Ob die embedded-Zählung den bestehenden Fill-Refresh-Mechanismus nutzt oder einen eigenen Job.

### Deferred Ideas (OUT OF SCOPE)
- 1.7: occ findling:backup/restore (Snapshot-Archiv), F-40-06, Tombstones in `indexed`, italienisches Testset, e5-base Opt-in.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| D-41-01 | occ pause/resume + Admin-Schalter | Abschnitt "Pause: Companion-Seite" (zwei neue Commands nach Muster `DiagnoseCommand`, POST-Route in `SettingsController`, Schlüssel in `SettingsService`) |
| D-41-02 | Indexer, Embedding, Poller ruhen; Batch ohne Gutschrift-Schaden | Holds nach Muster `hold_for_probe`; Poller wartet auf Pass-Ende wie `ProbeRun._pause`; Unlock refundiert (`QueueMapper::unlock`, retries - 1) |
| D-41-03 | WAL TRUNCATE + Tantivy-Commit vor "paused" | Schreiber-Inventar, Writer-Close wie `stand_down` (wait_merging_threads), `PRAGMA wal_checkpoint(TRUNCATE)` auf state.db und vectors.db mit Busy-Prüfung |
| D-41-04 | Suche läuft weiter | Suchpfad nutzt nur `open_read_only` (query_only) und Tantivy-Searcher; keine Abhängigkeit von Poller-Flags |
| D-41-05 | Übersteht Neustart | appconfig-Schlüssel als einzige Quelle, Backend startet "gehalten bis zur ersten Antwort" |
| D-41-06 | Wortlaut der Zusage | Status-Zustand `paused` erst nach Checkpoint; Doku-Satz deckungsgleich |
| D-41-07/08 | Backup-Doku dreisprachig | Muster `docs/migrate-from-fulltextsearch{,.en,.fr}.md`; Volume-Inhalt aus `config.py:1672-1677` |
| D-41-09 | embeddedLeftOut ohne Deckel, async+cache | Kandidat-F-Muster `resources.py:1029-1100` plus Lehren F-40N-03/F-40N-06 |
| D-41-10/11 | Repräsentant = größtes files_seen | `ScanStatsService.php:474`, Test `testTheRepresentativeIsTheSmallestFinishedMember` kippt |
| D-41-12 | F-40N-01..04 | Code an HEAD identisch mit v1.6.0, 40-07-PLAN Tasks 1+2 inklusive Zeilennummern gültig |
| D-41-13..17 | Release, Audit, Owner-Runde | Lockstep-Stellen, Baumhash-Paare, UPGRADE_FROM_TAG v1.5.0, head_green.sh, store-submit.yml |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Code, Bezeichner, Kommentare, Logzeilen englisch; echte Umlaute nur in deutscher Prosa, nie in Code, URLs, YAML.
- Keine Gedankenstriche (U+2013, U+2014) in Texten, keine Emojis.
- Python-Gates lokal grün vor Commit: ruff (Vollregelsatz) check + format --check, pyright basic (`PYRIGHT_PYTHON_FORCE_VERSION=latest`), vulture `--min-confidence 80`.
- Keine Inhalte verlassen den Server, kein Telemetrie-Phoning; Berechtigungs-Durchgriff strikt (Endfilter in PHP).
- Logzeilen ohne Pfad, Titel, Nutzername, Inhalt; nur Klassennamen und Zahlen (Modulregel in main.py, poller.py, T-40-22).
- Kurze Produkttexte: Faktenlisten, Entwurf vor Release dem Owner zeigen.
- Launch-Härtung: Rand- und Fehlerpfade, Neustart/Upgrade, Negativtests.
- Nach jeder Phase Security-, Bug-, Performance-Audit, Befunde vor Abschluss fixen.
- Commits als street1983nk <k.cherif@outlook.de>; Commits außerhalb `.planning` mit Claude-Session-Zeile (40-07-Kontextblock), `.planning`-Commits ohne Trailer; kein "Closes #N".
- Issue-Antworten erst nach Store-Release; Tag, Merge, Store-POST führt der Owner aus.
- RAM knapp: Tests seriell im Vordergrund, Volltestsuite in zwei Hälften (`tests/test_[a-m]*.py`, `tests/test_[n-z]*.py`) oder als CI-Beleg; kein lokales Docker.
- GSD-Workflow für alle Repo-Änderungen.

## Summary

Der Code auf `main` (91bd49f8) ist in `backend/src`, `php/lib`, `php/js`, `php/templates` und `php/l10n` byte-gleich mit v1.6.0 (`git diff --stat v1.6.0..HEAD` über diese Pfade ist leer; 1.6.1 brachte nur pypdf und Patch-Abhängigkeiten). Damit sind F-40N-01 bis F-40N-04 nachweislich unbehoben (`_OUTAGE_STATUS = frozenset({502, 503, 504})` in client.py:160, kein `GATEWAY_OUTAGE_MIN_STORAGES`, kein `GATEWAY_ERROR_RETRIES`, `'The next run tries again.'` bei gateway_error in AdminViewService.php:562-565, `_FILL_REFRESH = thread` vor `thread.start()` in resources.py:1064-1065), und der Entwurf 40-07-PLAN.md mit allen Zeilenangaben und Entscheiden E-40-07-01 bis -05 ist 1:1 als Vorlage verwendbar. Nur Task 3 dieses Entwurfs (Version 1.6.1) ist überholt.

Für den Pause-Schalter existiert im Backend bereits fast alles als Muster: Poller und EmbedRunner haben einen zweiten Halte-Mechanismus neben `arm/silence` (`hold_for_probe`/`release_probe_hold`, ein `asyncio.Event`, das nur den nächsten Pass verhindert), die Vorabprüfung (`ProbeRun._pause`, probe_run.py:543-555) wartet über `pass_in_flight` und `runner.parked` auf das Ende des laufenden Batches, und `Poller.stand_down` (poller.py:813-874) zeigt, wie der Tantivy-Writer sauber abgegeben wird (`writer.close()` = `wait_merging_threads`, kein Auto-Commit; der Pass committet ohnehin vor jeder Quittung). Was fehlt: ein eigener Pause-Hold (nicht der Probe-Hold, sonst hebt das Ende einer Prüfung die Pause auf), ein Hold für den Reconcile (hat heute nur `arm/silence`, keinen `in_flight`-Marker), das Anhalten eines Index-Rebuilds zwischen zwei Bändern (`should_stop` existiert), ein Checkpoint `PRAGMA wal_checkpoint(TRUNCATE)` auf state.db und vectors.db (nirgends im Code bisher) und ein Statusfeld.

Empfohlene Architektur: **eine Quelle der Wahrheit im appconfig der Companion** (`paused`), vom Backend über die bestehende, nur vom eigenen Backend lesbare Route `GET /ocs/v2.php/apps/findling/profile` gelesen (ein Feld mehr in der Antwort, keine neue ExApp-Route, kein neuer Meta-Schlüssel im Volume). Ein neuer Koordinator im Backend (`worker/pause.py`, eine Lifespan-Aufgabe) liest den Wunsch periodisch, hält alle Schreiber an, wartet auf den laufenden Batch, gibt den Writer ab, checkpointet beide Datenbanken und meldet erst dann `pause: "paused"` in `/status`. Ein Backup des Volumes enthält damit keinen Pause-Marker (ein Restore startet nicht still pausiert), und die Doku-Aussage "Einstellungen liegen in der NC-Datenbank, nicht im Volume" bleibt wahr.

**Primary recommendation:** Pause = appconfig-Schlüssel + Lese-Feld in `/profile` + Backend-Koordinator mit eigenem Hold-Event, Warten auf Pass-Ende (kein Abbruch), Writer-Close, `wal_checkpoint(TRUNCATE)` mit `busy == 0`-Prüfung; #25 als hybride Zählung (synchron bis 100 000 wie heute, darüber asynchron gecacht mit den Lehren aus F-40N-03/06); Nachaudit-Fixes aus 40-07 Tasks 1+2 übernehmen.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Pause-Wunsch speichern (Quelle der Wahrheit) | Companion (NC-DB, appconfig) | - | Übersteht Container- und NC-Neustart, liegt nicht im Volume (D-41-05, D-41-07) |
| occ pause/resume, Admin-Schalter | Companion (PHP Command, FrontpageRoute) | Browser (admin.js) | Admin-Grenze und CSRF liegen in NC |
| Pause-Wunsch an Backend liefern | Companion-Route `/profile` (ExAppRequired) | - | Bestehender Pull-Kanal, Backpressure-Regel "Container fragt, nichts pusht" |
| Schreiber anhalten, Batch abschließen, Writer abgeben, Checkpoint | Backend (`worker/pause.py`, Poller, Runner, Reconcile, Rebuild) | - | Nur das Backend kennt seine Schreiber und Dateien |
| Ist-Zustand "pausing/paused" melden | Backend `/status` (ADMIN) | Companion liest und zeigt | Status "paused" darf erst nach Checkpoint gelten (D-41-03) |
| Suche in der Pause | Backend Lesepfad + PHP Endfilter | - | unverändert, nur lesend |
| embeddedLeftOut-Zählung | Backend `/status` (Hintergrundthread, Cache) | - | Braucht state.db + vectors.db |
| Repräsentant einer Share-Gruppe | Companion (`ScanStatsService`) | - | scan_stats liegen in der NC-DB |
| Backup-Doku | docs/ (drei Sprachen) | README-Verweis | Nutzer-Doku |

## Standard Stack

Keine neuen Abhängigkeiten. Alles mit Bordmitteln des bestehenden Stacks:

| Baustein | Version (Stand Repo) | Einsatz in Phase 41 |
|---------|---------|---------|
| Python sqlite3 (stdlib, CPython 3.13) | Image python:3.13-slim-trixie | `PRAGMA wal_checkpoint(TRUNCATE)` auf state.db und vectors.db [CITED: sqlite.org/pragma.html#pragma_wal_checkpoint] |
| tantivy-py | 0.26.0 | `IndexWriter.commit()` (schon je Pass), `wait_merging_threads()` über `IndexBatchWriter.close()` [VERIFIED: codebase index/writer.py:475-487] |
| asyncio.Event | stdlib | Pause-Hold, gleiches Muster wie `_probe_release` [VERIFIED: codebase poller.py:676-684] |
| threading.Thread (daemon) | stdlib | Hintergrundzählung #25, Muster Kandidat F [VERIFIED: codebase resources.py:1050-1100] |
| OCP\IAppConfig | NC 33-35 | `getValueBool`/`setValueBool` (schon in SettingsService:455, :762) [VERIFIED: codebase] |
| Symfony Console via OC\Core\Command | NC | zwei neue Commands, Muster `DiagnoseCommand`/`IndexCommand` [VERIFIED: codebase] |

**Installation:** keine.

## Package Legitimacy Audit

Keine externen Pakete werden installiert oder geändert. slopcheck nicht nötig. **Removed:** keine. **Flagged:** keine.

## Architecture Patterns

### System Architecture Diagram

```
Admin (occ findling:pause | Schalter Admin-Seite)
        |
        v
Companion: SettingsService::setPaused(true)  --> appconfig findling/paused (NC-DB, einzige Quelle)
        |                                              ^
        | (occ --wait / Seite pollt)                   | GET /profile (ExAppRequired, eigener Backend-Aufrufer)
        v                                              |
Companion liest GET /status (ADMIN) <---------+   Backend PauseCoordinator (Tick ~15 s, Lifespan-Task)
   pause: running | pausing | paused          |        |
                                              |        | wanted=paused?
                                              |        v
                                              |   1. hold: Poller, EmbedRunner, Reconcile(+Catch-up), GuardWatch-Persist,
                                              |      Probe-Start verweigern, Rebuild should_stop -> True
                                              |   2. warten: poller.pass_in_flight == False, runner.parked, reconcile idle,
                                              |      kein Rebuild-Band, keine Probe aktiv  (Zustand "pausing")
                                              |   3. Poller: unlock_held(), writer.close() (wait_merging_threads), track.close()
                                              |   4. wal_checkpoint(TRUNCATE) state.db, vectors.db; busy==0 sonst Retry
                                              +-- 5. Zustand "paused" (+ pausedSince)
                                                       |
                                              wanted=running? -> holds lösen, Rebuild-Frage neu stellen,
                                                       Poller._open() baut Writer neu

Suche (Unified Search -> PHP -> /search, /snippets, /similar) läuft in jedem Zustand über den Lesepfad (query_only, Tantivy-Searcher).
```

### Komponenten und Fundstellen

| Datei | Rolle heute | Änderung |
|------|------|------|
| `backend/src/findling/worker/poller.py` | `_probe_release` (:676-684), `hold_for_probe` (:793-803), `pass_in_flight` (:788), `run` (:921-962), `stand_down` (:813-874), `run_once` liest `companion_choice()` vor dem Claim (:991) | zweites Event `_backup_release` + `hold_for_backup/release_backup_hold`; `run` wartet darauf wie auf den Probe-Hold; neue Methode `quiesce_for_backup()` = Schritte 2-3 von `stand_down` OHNE `_armed.clear()` |
| `backend/src/findling/worker/embedding.py` | `EmbedRunner._probe_release`, `parked`, `run` (:1525-1559) | gleiches zweites Event; `parked` ist das Warte-Signal |
| `backend/src/findling/worker/reconcile.py` | `Reconcile.run` (:351-388) ohne Hold, ohne `in_flight` | Hold-Event + `in_flight`-Flag; Abbruch zwischen zwei Scheiben über bestehende Frühausgänge (Lesezeichen bleibt) |
| `backend/src/findling/main.py` | Lifespan-Tasks (:920-1200), `_armable_tasks` (:253-271), `companion_reader()` (:551-567), Rebuild `should_stop=stop_event.is_set` (:838-880) | Koordinator-Task erzeugen, `should_stop` um Pause erweitern, nach Resume `_start_the_rebuild_if_due()` |
| `backend/src/findling/worker/probe_run.py` | `start`, `_pause` | Start bei aktiver Pause mit 409 verweigern (neue Ursache `paused`) |
| `backend/src/findling/worker/watch.py` | `GuardWatch._persist_if_changed` schreibt state.db bei Änderung | in der Pause nicht schreiben (Revision merken, nach Resume persistieren) |
| `backend/src/findling/nc/queue.py` | `CompanionChoice`, `companion_choice()` (:707-746) | Feld `paused: bool | None` (None = nicht lesbar, fehlendes Feld eines alten Companions = False) |
| `backend/src/findling/api/status.py` | `StatusResponse` | Feld `pause` (geschlossene Menge) und `pausedSince` |
| `php/lib/Controller/ProfileController.php` | Antwort `profile, precision, confirmed, verdicts` (:84-107) | `'paused' => $this->settingsService->paused()` im selben try |
| `php/lib/Service/SettingsService.php` | Schlüssel-Konstanten, `getValueBool` | `KEY_PAUSED = 'paused'`, `paused()`, `setPaused(bool)` |
| `php/lib/Command/` | Index, Diagnose, Purge | `PauseCommand`, `ResumeCommand` (+ Eintrag in `<commands>` der php/appinfo/info.xml) |
| `php/lib/Controller/SettingsController.php` | FrontpageRoutes `/admin/...` ohne NoAdminRequired | `POST /admin/pause` mit `paused` (bool) |
| `php/lib/Service/AdminViewService.php`, `php/templates/admin.php`, `php/js/admin.js` | Overview, Status-Sätze | Ist-Zustand und Schalter, Sätze über `t()`/`textContent` |

### Pattern 1: Eigener Hold neben arm/silence (nicht den Probe-Hold teilen)
**What:** Ein `asyncio.Event` je Schreiber, bei Geburt gesetzt; `run` wartet davor wie vor `_probe_release`.
**Why:** `arm/silence` gehört AppAPI-Enable und Lifespan (Kommentar poller.py:676-683); der Probe-Hold wird in `ProbeRun.run` im `finally` immer gelöst (probe_run.py:480-481). Teilt die Pause eines dieser Signale, hebt ein Enable oder das Ende einer Prüfung die Pause still auf, genau das verbietet D-41-05.
**Example (aus dem Code, Muster):**
```python
# Source: backend/src/findling/worker/poller.py:921-935
while not stop_event.is_set():
    if not self._armed.is_set():
        await _first_of(self._armed.wait(), stop_event.wait())
        continue
    if not self._probe_release.is_set():
        await _first_of(self._probe_release.wait(), stop_event.wait())
        continue
    # neu: derselbe Block für self._backup_release
```

### Pattern 2: Warten auf den laufenden Batch statt Abbruch
**What:** Wie `ProbeRun._pause` (probe_run.py:543-555): Hold setzen, dann pollen bis `not poller.pass_in_flight and runner.parked.is_set()`.
**Why:** Der Pass quittiert regulär (Commit vor Quittung), es entsteht keine Belastung. Ein Abbruch über `_abort` wäre gutschriftneutral (`QueueMapper::unlock` zieht `retries - 1` ab, QueueMapper.php:827-851), verwirft aber erledigte OCR-Arbeit und ist ein neuer Pfad. Warten erfüllt D-41-02 ("endet sauber") ohne neuen Abbruchpfad.
**Kosten:** Leerlauf sofort; Text-Pass Sekunden bis Minuten; OCR-Pass bis zur Lease, `PROBE_PAUSE_SECONDS = OCR_LOCK_TIMEOUT_SECONDS = 1800` (config.py:1094, :575). Der Status zeigt so lange `pausing`. Kein Timeout im Backend nötig (es hält weiter, bis der Pass endet); `occ findling:pause --wait` hat einen eigenen Timeout.

### Pattern 3: Writer abgeben ohne zu silencen
**What:** Schritte 2 und 3 aus `stand_down` (unlock_held, `writer.close()` im Thread, `track.close()`), ohne `self._armed.clear()`. `_open()` baut beim nächsten Pass Writer und Track neu (Kommentar poller.py:866-870).
**Why:** `IndexBatchWriter.close()` ruft `wait_merging_threads()` (writer.py:475-487): danach laufen keine Segment-Merges mehr, die Lock-Datei ist frei, die Index-Dateien ändern sich bis zum Resume nicht. Ein offener Writer mit laufenden Merges würde Segmentdateien während der Kopie anlegen und löschen.

### Pattern 4: Checkpoint mit Busy-Prüfung
**What:** Eigene kurze Verbindung je Datei (state.db, vectors.db, nur wenn `is_file()`), `PRAGMA busy_timeout`, dann `PRAGMA wal_checkpoint(TRUNCATE)`; Rückgabezeile `(busy, log, checkpointed)`; nur `busy == 0` zählt, sonst nach kurzer Pause erneut (Zustand bleibt `pausing`). `log == -1` heißt "kein WAL-Modus" (NFS-Fallback, enable_wal repo.py:720-737) und ist ebenfalls Erfolg.
**Why:** TRUNCATE "blocks until there is no database writer and all readers are reading from the most recent snapshot ... and until all readers are finished with the log file", danach ist die WAL-Datei 0 Byte [CITED: sqlite.org/pragma.html]. Lesende Suchverbindungen (autocommit, kurze Statements) blockieren nur kurz; Busy ist möglich und muss behandelt werden.
**Hinweis:** vectors.db hat sqlite-vec; der Checkpoint selbst braucht die Erweiterung nicht (Pages-Kopie). Verbindung ohne `mode=ro` (Checkpoint schreibt die Hauptdatei), Datei nie neu anlegen (vorher `is_file()`).

### Pattern 5: Hybride Zählung #25 (Kandidat F mit den Lehren)
**What:** In status.py `_left_out`: `indexed_left_out` bleibt synchron. `embedded_left_out`: bis `LEFT_OUT_EMBEDDED_SYNC_CEILING = 100_000` (heutige Zahl, gemessen ~40 ms für 60 000 Dokumente, 40-AUDIT.md P1) synchron wie heute; darüber aus einem Cache, Schlüssel `frozenset(leave_out)`, mit Hintergrundthread (single flight) bei Fehlen oder Ablauf.
**Pflicht-Lehren aus Phase 40:**
- F-40N-03: `thread.start()` in try, bei `RuntimeError` Flag zurück auf None, Antwort aus dem Cache (oder Feld fehlt).
- F-40N-06(b): TTL ab Messende zählen, nicht ab Messbeginn.
- Cache begrenzt (z. B. nur letzter Schlüssel oder höchstens 4), weil die Companion die leaveOut-Liste je nach Repräsentant ändert.
- Generations-/Pfad-Guard beim Schreiben wie `_refresh_fill:1093` (vectors.db kann nach Präzisionswechsel neu gefüllt werden).
- Autouse-Fixture in backend/tests/conftest.py (`quiesce_the_fill_refresh`) um den neuen Thread erweitern, sonst flaky Tests.
**Warum hybrid statt immer async:** Kleine Instanzen bekämen sonst beim ersten Poll kein embeddedLeftOut, `leftOutCounts()` (AdminViewService.php:2132-2145) gäbe null, die Seite spränge zwischen Dedup und 1.5-Zählung. Hybrid ändert für Instanzen unter 100 000 nichts.

### Anti-Patterns to Avoid
- **Pause über `silence()`:** kollidiert mit Enable/Disable und dem Arm-Marker auf dem Volume (main.py:283-325).
- **Pause-Marker im Volume:** Backup enthielte den Marker, ein Restore käme still pausiert hoch; zweite Quelle neben appconfig.
- **"paused" melden, sobald der Wunsch gelesen ist:** verletzt D-41-03; Status muss drei Werte haben.
- **Probe-Hold teilen:** siehe Pattern 1.
- **Neue ExApp-Route für einen Push:** braucht info.xml-Route, HaRP-Registrierung beim Update, Mischbetrieb-Fragen; der Pull über `/profile` reicht.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Konsistente SQLite-Kopie | Dateien selbst flushen/kopieren | `PRAGMA wal_checkpoint(TRUNCATE)` | WAL-Semantik, Leser-Synchronisation |
| Tantivy flushen | eigene Merge-Steuerung | `commit()` je Pass + `wait_merging_threads()` über `IndexBatchWriter.close()` | Merges laufen in Hintergrundthreads |
| Warten auf Batch | neuer Abbruchpfad | `pass_in_flight` / `parked` wie `ProbeRun._pause` | erprobt, ohne Belastung |
| Admin-User für occ-Aufruf des Backends | eigene Auth | `DiagnoseCommand::adminUserId()`-Muster + `ExAppService::adminGet` | AppAPI-Signatur, ADMIN-Route |
| Hintergrundzählung | Job-Framework | Daemon-Thread + Lock wie Kandidat F | bekanntes, auditiertes Muster |
| Antwort-Auswertung im PHP | eigenes HTTP | `ExAppService::adminGet` (4 Fälle, Größengrenze) | Fehlerfälle schon abgedeckt |

## Runtime State Inventory

Keine Umbenennung; trotzdem relevant, weil ein neuer gespeicherter Zustand entsteht:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Neuer appconfig-Schlüssel `findling/paused` (NC-DB). Kein neuer Meta-Schlüssel in state.db (bewusst). | Code-Edit; keine Migration (fehlender Schlüssel = nicht pausiert); Upgrade-Strecke prüft "nach Upgrade nicht pausiert" |
| Live service config | AppAPI-Routenliste des Backends unverändert, wenn keine neue ExApp-Route | keine |
| OS-registered state | Keine. | keine (verifiziert: kein systemd/cron im Projekt) |
| Secrets/env vars | Keine neuen. Optional neue Env `FINDLING_PAUSE_POLL_SECONDS` nicht empfohlen (Zero-Config) | keine |
| Build artifacts | Baumhash-Paare: neue Python-Datei `worker/pause.py` erhöht `PACKAGE_FILES_TODAY` 80 -> 81; neue PHP-Dateien (`PauseCommand.php`, `ResumeCommand.php`) erhöhen `PHP_FILES_TODAY` 110 -> 112 (backend/tests/test_measurement_scripts.py:1126-1127, :2376-2377) | Journalabsatz je Plan; eingefrorenes Paar :458/:468 nie anfassen |

## Common Pitfalls

### Pitfall 1: Pause wird durch Enable, Rebuild-Ende oder Probe-Ende still aufgehoben
**What goes wrong:** `enabled_handler` ruft `task.arm()` (main.py:369-374), der Rebuild ruft `_arm_the_poller` (main.py:744-762), die Probe löst ihren Hold im finally.
**How to avoid:** eigenes Event, das nur der Koordinator setzt/löscht; Tests: Pause, dann Enable-Handler, dann Probe-Ende, dann Rebuild-Arm: Poller bleibt gehalten.

### Pitfall 2: Nach Container-Neustart läuft ein Pass, bevor der Wunsch gelesen ist
**What goes wrong:** Lifespan armt bei vorhandenem Arm-Marker sofort (main.py:1185-1196); Reconcile und Runner starten ohne Companion-Lesen.
**How to avoid:** Koordinator startet im Zustand "unbekannt = gehalten" (Holds bei Geburt gelöscht für den Backup-Hold, Gegenteil zum Probe-Hold) und löst erst nach der ersten erfolgreichen Antwort von `/profile` mit `paused` false oder fehlendem Feld. Risiko: eine dauerhaft 500 antwortende Profil-Route hielte die Indexierung an; sichtbar machen über `pause: "unknown"` im Status (Open Question 1).

### Pitfall 3: Mischbetrieb Patch-Versionen
**What goes wrong:** `ExAppService::majorMinor` vergleicht nur Major.Minor (E-40-07-06), Companion 1.6.2 mit Backend 1.6.1 gilt als passend. Das alte Backend ignoriert `paused`, die Seite würde "pausiert" glauben.
**How to avoid:** Companion zeigt "paused" nur, wenn `/status` das Feld `pause` mit `paused` liefert; fehlt das Feld, Satz "Backend kennt die Pause nicht, beide Apps aktualisieren" und occ Exit 1. Companion 1.6.1 mit Backend 1.6.2: Feld fehlt in `/profile` -> nicht pausiert.

### Pitfall 4: Weitere Schreiber übersehen
**Inventar (verifiziert per grep `write_meta|open_store`):** Poller (Store, Vektoren, Tantivy-Writer, Track), EmbedRunner (über Track), Reconcile (eigener Store, give_up, Lesezeichen), Catch-up-Reconcile (main.py:1127-1137), Rebuild (zweites Index-Verzeichnis, Marks; main.py:808-880), ProbeRun (Meta, fp32-Datei, Sweep), GuardWatch (Meta bei Änderung, watch.py:159-176), Recheck/Catch-up Teil A (laufen im Poller-Pass). Lesend: /status, /rates, /diagnose, Suche, Fill-Refresh, neue Left-out-Zählung. Start-Schreiber vor Lifespan-Tasks: `claim_the_volume`, `recover_the_index_directories` (nur beim Start, vor dem Koordinator).
**How to avoid:** Jeder Schreiber bekommt Hold oder Verweigerung; Test je Schreiber.

### Pitfall 5: Auto-Checkpoint während der Kopie
**What goes wrong:** Jede spätere Schreibtransaktion hängt Frames an die WAL; bei 1000 Seiten checkpointet SQLite automatisch in die Hauptdatei, mitten in einer Kopie.
**How to avoid:** In der Pause schreibt niemand (Pitfall 4); GuardWatch-Persist aussetzen.

### Pitfall 6: Status-Sätze der Admin-Seite in der Pause
**What goes wrong:** Sätze wie Gateway-Ausfall, Queue-Stillstand, Schätzung der Restzeit, Reconcile "not due" können in der Pause falsch klingen; die PHP-Crawl-Jobs (StorageCrawlJob, SchedulerJob) füllen die Queue weiter (NC-DB, nicht Volume).
**How to avoid:** Bei `pause` != running einen Pause-Satz zeigen und die Schätzung ausblenden; Crawl bewusst weiterlaufen lassen (berührt das Volume nicht) und in der Doku nennen.

### Pitfall 7: Tests, die das alte Verhalten festnageln
- `test_status_leave_out.py:176-186` und `test_phase40_audit.py:829-846` (`test_p1_the_vector_figure_stops_above_a_hundred_thousand_documents`, Assertion `LEFT_OUT_EMBEDDED_CEILING == 100_000`, Feld fehlt ab 100 001) müssen neu abgeleitet werden: ab 100 001 Feld nach `join` des Refreshs vorhanden.
- `php/tests/Unit/ScanStatsServiceTest.php:176` `testTheRepresentativeIsTheSmallestFinishedMember` kippt.
- docs/admin-page.md:152, :173 nennt "die kleinste durchgezählte Storage-ID" als Repräsentant.
- `test_admin_ui_contract.py:3859` pinnt 354 de-Schlüssel.
- W-1-Tests in test_poller.py (:1303, :1331, :1388, :1499) kippen unter E-40-07-01 (40-07-PLAN.md, interfaces).

### Pitfall 8: Repräsentant ändert sich während des Crawls
**What goes wrong:** files_seen eines unfertigen Mitglieds wächst; der Repräsentant und damit die leaveOut-Liste wechseln, der Cache-Schlüssel auch.
**How to avoid:** Tie-Break deterministisch (größtes files_seen, bei Gleichstand fertig vor unfertig, dann kleinste ID); Cache begrenzt; neue Liste startet einen neuen Lauf, kein Wachstum.

### Pitfall 9: Tantivy-Writer-Lock nach Restore
**What goes wrong:** Mit offenem Writer kopiert, enthält das Backup `.tantivy-writer.lock`; mit geschlossenem Writer nicht.
**How to avoid:** Writer im Pause-Eintritt schließen (Pattern 3). [ASSUMED: tantivy nutzt eine Datei-Sperre, die nach Restore ohne laufenden Prozess nicht blockiert; durch Writer-Close irrelevant.]

## Code Examples

### Checkpoint (neu, Form)
```python
# Source: SQLite pragma doc (wal_checkpoint) + Verbindungsregeln aus store/repo.py:740-783
def checkpoint(path: Path) -> bool:
    """True when the WAL of path is empty, or the file is not in WAL mode."""
    if not path.is_file():
        return True
    connection = sqlite3.connect(path, autocommit=True, check_same_thread=False)
    try:
        connection.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
        busy, log, _ = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        return busy == 0 or log == -1
    finally:
        connection.close()
```

### Companion-Antwort erweitern
```php
// Source: php/lib/Controller/ProfileController.php:90-96 (gleicher try, 500 bei Lesefehler)
'verdicts' => self::VERDICTS_GENERATION,
'paused' => $this->settingsService->paused(),
```

### Repräsentant
```php
// Source: php/lib/Service/ScanStatsService.php:474 (heute: $finished[0] ?? $counted[0] ?? $members[0])
$counted = array_values(array_filter($members, static fn (int $id): bool => isset($rows[$id])));
usort($counted, static fn (int $a, int $b): int =>
	[$rows[$b]['filesSeen'], ($rows[$b]['finished'] ?? false) ? 1 : 0, $a]
	<=> [$rows[$a]['filesSeen'], ($rows[$a]['finished'] ?? false) ? 1 : 0, $b]);
$representative = $counted[0] ?? $members[0];
```
(Rows tragen camelCase-Schlüssel, `COUNTERS` mappt `files_seen => filesSeen`, ScanStatsService.php:63-64, :418-421.)

## Nachaudit F-40N-01..04 (Stand HEAD)

| Befund | Stelle an HEAD | Zustand | Vorlage |
|---|---|---|---|
| F-40N-01 | poller.py:204-215, :2362-2382, :1238-1247 | unbehoben | 40-07 Task 1, E-40-07-01/02 |
| F-40N-02 | reconcile.py:678/:695, repo.py:342-375 (`_RECORD_SQL`), AdminViewService.php:562-565 | unbehoben | 40-07 Task 2, E-40-07-03/04/05 (neuer Katalogsatz en/de/fr steht wörtlich im Entwurf) |
| F-40N-03 | resources.py:1063-1065 | unbehoben | 40-07 Task 1 |
| F-40N-04 | client.py:152-160 | unbehoben | 40-07 Task 1 |

Interfaces-Block von 40-07 (Zeilennummern) gilt unverändert, weil der Code seit v1.6.0 nicht geändert wurde. Die STOPP-Regel aus E-40-07-06 (keine Migration, kein Schema, kein neuer Meta-Schlüssel) bleibt für 1.6.2 sinnvoll und wird durch die empfohlene Pause-Architektur eingehalten.

## Release-Mechanik

- **Lockstep-Stellen** (Muster Commit 0f12c43a "release: 1.6.1"): `backend/appinfo/info.xml` `<version>` und `<image-tag>`, `php/appinfo/info.xml` `<version>`, je drei Doku-Links `blob/v1.6.1` -> `blob/v1.6.2`; CHANGELOG `[1.6.2]` plus Linkdefinition; Gate `backend/tests/test_lockstep_versions.py`, `test_store_metadata.py`. `backend/pyproject.toml` version ist keine Lockstep-Stelle.
- **php/appinfo/info.xml `<commands>`** (eine Zeile) bekommt zwei Commands: das ist eine Änderung außerhalb von Version/Links; Store-Metadaten-Tests, die den info.xml-Diff gegen den Vortag auf Version/Links begrenzen, prüfen (40-07 Task 3 Akzeptanz "zeigt nur Version, Image-Tag und die sechs Links").
- **Upgrade-Strecke:** `UPGRADE_FROM_TAG: v1.5.0` in deploy-harp.yml bleibt (D-41-13); Kommentare "the tree carries 1.6.x" auf 1.6.2 (Muster 3a7085b8); Zitat "installed_version went from 1.5.0 to 1.6.2". Empfehlung: einen Schritt ergänzen, der nach dem Upgrade `pause: running` im Status prüft (kein stilles Pausieren nach Upgrade).
- **CI-Gate:** `scripts/ci/head_green.sh "<sha>" "Python gates" "PHP and store metadata gates" "HaRP deploy" "Integration" "Resilience" "Multi-arch image" "Security scans"`.
- **l10n-Kette:** 16 Dateien `php/l10n/{de,de_DE,es,fr,it,nl,pt_BR,pt_PT}.{json,js}`, Schlüssel = englischer Satz; fünf Tabellen `docs/l10n-{french,spanish,italian,dutch,portuguese}.md`; de-Schlüsselzahl in test_admin_ui_contract.py:3859 (354 + 1 aus F-40N-02 + n Pause-Sätze, jeweils mit Absatz).
- **Release/Store:** release.yml (Tag), store-submit.yml (Owner löst aus). Tag-Kopf = audited_head-Regel aus 40-08/40-09.

## Plan-Zuschnitt (Empfehlung)

Seriell, weil Katalogdateien, Baumhash-Paare und test_admin_ui_contract.py von mehreren Plänen berührt werden:
1. F-40N-01..04 (40-07 Tasks 1+2, ohne Bump).
2. #25: Backend hybride Zählung + PHP Repräsentant + Tests D-41-11.
3. Pause Backend: Koordinator, Holds, Quiesce, Checkpoint, Statusfeld, Probe-Verweigerung, Rebuild-Stop.
4. Pause Companion: Schlüssel, `/profile`-Feld, occ pause/resume (`--wait[=Sekunden]`), Admin-Schalter, Sätze, l10n.
5. Backup-Doku DE/EN/FR (+ README-Verweis), CI-Beweis Pause/Neustart/Resume in HaRP- oder Integration-Workflow.
6. Version 1.6.2, CHANGELOG, Upgrade-Kommentare, grüner Kopf.
7. Audit v1.6.1..Kopf (Vorlage 40-08, audited_head).
8. Owner-Runde (Vorlage 40-09).
9. Tag und Store (Owner), danach Issue-Antworten #37/#25.

## Test-Landkarte (Nachweise je Erfolgskriterium)

`workflow.nyquist_validation` ist false; trotzdem die geforderten Nachweise:

| SC | Verhalten | Test | Datei |
|---|---|---|---|
| 1 | Pause bei Leerlauf: Holds, Writer zu, Checkpoint, `paused` | Unit mit Doubles | neu `backend/tests/test_backup_pause.py` |
| 1 | Pause während laufendem Batch: `pausing` bis Pass-Ende, Quittung regulär, keine Belastung (keine Zeile ohne unlock/ack), danach `paused` | Unit (Poller-Double mit Event im Pass) | test_backup_pause.py |
| 1 | Doppeltes pause, doppeltes resume, resume während pausing | Unit | test_backup_pause.py |
| 1 | Neustart in der Pause: neuer Koordinator startet gehalten, liest `paused`, kein Pass vor dem Lesen | Unit + Lifespan | test_backup_pause.py, test_main_lifespan.py |
| 1 | Enable-Handler, Probe-Ende, Rebuild-Arm heben die Pause nicht auf | Unit | test_backup_pause.py |
| 1 | Checkpoint: WAL nach Pause 0 Byte; Busy-Leser -> Retry, erst danach `paused` | Unit mit echter SQLite im tmp | test_backup_pause.py |
| 1 | Suche in der Pause liefert Treffer | Endpoint-Test | test_backup_pause.py / bestehende Such-Tests |
| 1 | Probe-Start in der Pause -> 409 `paused` | Endpoint | test_probe_endpoint.py |
| 1 | `/profile` liefert `paused`; Lesefehler 500 ohne Feld | PHPUnit | ProfileControllerTest.php |
| 1 | occ pause/resume: Schlüssel, Ausgabe, Exit-Codes, Backend ohne Feld -> Exit 1 | PHPUnit | neu PauseCommandTest.php |
| 1 | Admin-Route nur Admin, CSRF | PHPUnit + Integration | SettingsControllerTest.php |
| 1 | Echte Instanz: pause -> paused, docker restart -> paused, Suche ok, resume -> Indexierung | CI | deploy-harp.yml oder integration.yml |
| 2 | Doku dreisprachig, Links gültig, keine Gedankenstriche | Doku-Gate | test_store_metadata.py o. ä. |
| 3 | 113 851 left-out: Feld nach Refresh vorhanden, Wert korrekt; Thread-Start-Fehler -> erneuter Start | Endpoint | test_status_leave_out.py, test_phase40_audit.py (neu abgeleitet) |
| 3 | Repräsentant größtes files_seen; 28k..112k je Share -> Nenner ~246k | PHPUnit | ScanStatsServiceTest.php |
| 4 | F-40N-01..04 | wie 40-07 behavior-Blöcke | test_poller.py, test_gateway_client.py, test_status_endpoint.py, test_reconcile.py, test_store_repo.py, test_admin_ui_contract.py |

Befehle: `cd backend && PYTHONUTF8=1 uv run --no-sync python -m pytest -q tests/<datei>`; PHP nur in CI (lokal kein `php`).

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | nein (bestehend) | AppAPI-Signatur |
| V4 Access Control | ja | `POST /admin/pause` ohne `NoAdminRequired` (nur Admin); occ = Shell-Admin; `/profile` mit `ExAppRequired` + `rejectForeignCaller` (EX-APP-ID == findling_backend); `/status` ADMIN |
| V5 Input Validation | ja | Body nur bool; Statusfeld geschlossene Menge; Companion wertet nur `paused === true` |
| V7 Logging | ja | Logzeilen nur Zustand und Klassennamen |
| V6 Cryptography | nein | - |

| Pattern | STRIDE | Mitigation |
|---------|--------|------------|
| Nicht-Admin pausiert die Indexierung | Elevation/DoS | Admin-only Route, CSRF-Token (admin.js sendet `requesttoken`) |
| Fremde ExApp liest/setzt Pause | Spoofing | `rejectForeignCaller`, kein Schreibweg über ExApp |
| Pause als Dauer-Abschaltung ohne Sichtbarkeit | DoS | Satz auf Admin-Seite, `occ findling:index --status`/Diagnose zeigt Pause |
| Backup mit Klartext | Information Disclosure | Doku-Satz D-41-07 |
| Hintergrundzählung als Last | DoS | single flight, TTL ab Ende, begrenzter Cache |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | Python-Tests/Gates | ✓ | 0.11.7 | - |
| gh | CI-Gate, Issues lesen | ✓ | 2.92.0 | - |
| php | PHPUnit lokal | ✗ | - | CI-Job "PHP and store metadata gates" |
| docker | lokale Instanz | ✓ installiert, Nutzung untersagt (RAM) | 29.5.2 | CI (HaRP deploy, Integration) |
| Freier RAM | Testläufe | 5,6 GB bei Messung | - | Tests einzeln, Volltest in zwei Hälften |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Container- und Volume-Namen `nc_app_findling_backend` / `nc_app_findling_backend_data` gelten auch unter HaRP (aus Owner-Antwort #37, nicht im Code geprüft) | Doku | Falscher Befehl in der Doku; im CI-Lauf `docker ps` gegenprüfen |
| A2 | Tantivy-Lock-Datei stört nach Restore nicht | Pitfall 9 | gering, durch Writer-Close irrelevant |
| A3 | Koordinator-Takt 15 s ist als zusätzliche OCS-Last vertretbar | Architektur | mehr Last; Alternative: Takt 30 s oder nur der Poller liest |
| A4 | Warten auf Pass-Ende (bis ~30 min bei OCR) ist für Backup-Skripte akzeptabel | Pattern 2 | Owner will schnelleren Eintritt -> kooperativer Abbruch über `_abort` mit voller Gutschrift |

## Open Questions

1. **Start ohne lesbare Profil-Route:** gehalten bleiben (D-41-05 strikt) oder nach Frist laufen? Empfehlung: gehalten, `pause: "unknown"` im Status mit eigenem Satz; Owner-Runde zur Kenntnis.
2. **Rebuild während Pause-Wunsch:** Empfehlung: Rebuild zwischen zwei Bändern stoppen (Resume-Cursor `_resume_cursor`, rebuild.py:575), halb gefülltes Zielverzeichnis bleibt; nach Resume `_start_the_rebuild_if_due()`. Doku: Backup während eines Rebuilds enthält zwei Index-Verzeichnisse.
3. **Ein Feld oder zwei im Status:** `pause` (running/pausing/paused/unknown) plus `pausedSince` (Epoch) empfohlen; occ `--wait` pollt `/status`.
4. **Crawl in der Pause:** Empfehlung weiterlaufen lassen (NC-DB), dokumentieren; Owner-Kenntnis.

## Sources

### Primary (HIGH confidence)
- Codebase `main` 91bd49f8: poller.py, embedding.py, reconcile.py, probe_run.py, main.py, watch.py, status.py, resources.py, repo.py, writer.py, queue.py, client.py, config.py; ProfileController.php, SettingsService.php, ExAppService.php, ScanStatsService.php, AdminViewService.php, QueueMapper.php, DiagnoseCommand.php; info.xml beider Apps; Tests test_status_leave_out.py, test_phase40_audit.py, ScanStatsServiceTest.php, test_measurement_scripts.py, test_admin_ui_contract.py.
- `git diff --stat v1.6.0..HEAD` (Code unverändert), `git show --stat 0f12c43a 3a7085b8`.
- https://www.sqlite.org/pragma.html#pragma_wal_checkpoint (Modi, Rückgabezeile).
- 40-NACHAUDIT.md, 40-07/08/09-PLAN.md, 40-AUDIT.md (P1-Messung).
- GitHub Issues #37, #25 (Owner-Zusagen, Messwerte mbozem).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, keine neuen Pakete.
- Architecture: HIGH für Muster (alle am Code), MEDIUM für Koordinator-Details (neu, Entscheidungen offen in Open Questions).
- Pitfalls: HIGH, Fundstellen belegt.

**Research date:** 2026-11-04
**Valid until:** bis zum nächsten Code-Commit auf main in backend/src oder php/lib
