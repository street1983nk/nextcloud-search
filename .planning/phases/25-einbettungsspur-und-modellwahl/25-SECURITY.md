---
phase: 25
slug: einbettungsspur-und-modellwahl
status: verified
threats_total: 54
threats_closed: 54
threats_open: 0
asvs_level: 1
block_on: critical
register_authored_at_plan_time: true
created: 2026-09-28
---

# Phase 25: Security

> Sicherheitsvertrag der Phase: Bedrohungsregister, akzeptierte Risiken, Prüfpfad.
> Jede Mitigation ist am Code belegt (Datei:Zeile), nicht an Doku oder Absicht.
> Stand nach den Review-Fixes WR-01 (00ecee3), WR-02 (25ec895), WR-03 (8ca5983) und WR-04 (be2779c), HEAD 46f91398.
> Pfade ohne Präfix liegen unter `backend/src/findling/`, Tests unter `backend/tests/`.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Hugging Face -> Entwicklerrechner -> GitHub-Release | fp32-Datei aus fremdem Hub, einmal gemessen und als Release-Asset veröffentlicht | Modellgewichte (öffentlich) |
| Internet (GitHub, Proxy) -> Container | fremde Bytes werden zu einem Modell, das der Container ausführt | 470 MB Gewichte |
| Admin-Sideload -> Container | Datei im persistenten Volume aus unbekannter Quelle | Modellgewichte |
| cgroup-Dateien -> Zulassung | Kernelwerte entscheiden über Parallelität | memory.max, memory.stat anon, MemAvailable |
| ExApp-Aufrufer -> Queue-Route | nur die eigene ExApp darf Zeilen beanspruchen | Spurname, Warteschlangenzeilen |
| appconfig -> Profilroute -> Container | `model_precision` aus occ, Tippfehler möglich; löst Reindex, Download, Löschen aus | Präzisionsname (geschlossene Menge) |
| Companion-Antwort -> Container | Spur-Echo und Präzisionswert aus einer OCS-Antwort | Spurname, Präzisionsname |
| Upgrade-Fenster | neuer Container gegen 1.3-Companion ohne Filter und ohne Präzisionsfeld | fehlendes Echo, fehlendes Feld |
| Indexspur <-> Einbettungsspur | geteilte state.db, vectors.db und Tantivy-Verzeichnis | Metadaten, Vektoren |
| Lifespan <-> zwei Nebenläufer | Start, Stopp, Rebuild und Freigabe greifen in laufende Arbeit ein | gehaltene Queue-Zeilen, Modell im RAM |
| Container -> Admin (GET /status, Adminseite) | Betriebsdaten verlassen den Prozess, werden im Admin-Browser gerendert | Präzision, Verdikt, Spurzustand |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status | Evidence |
|-----------|----------|-----------|-------------|------------|--------|----------|
| T-25-01 | Tampering | hochgeladenes Asset | mitigate | sha256/Größe gegen Dockerfile-Pin, Download-Gegenprobe, immutable Release | closed | backend/Dockerfile:102 (Revision 614241f), :145 (Pin ca456c06...); embed/weights.py:52-53 (gleicher Digest, 470_268_510 Byte); docs/measurements/2026-09-fp32-speicher/rohdaten/02-release-gegenprobe.txt:13 (`release_immutable=true`), :17-19 (Größe, Digest der API), :27-30 (Download, sha256sum und certutil gleich dem Pin) |
| T-25-02 | EoP | Upload-Handlung | mitigate | Upload nur durch Owner, Executor lädt nichts hoch | closed | 25-01-SUMMARY.md:32, :67-68 (Executor hat nichts hochgeladen oder gepusht; Upload auf ausdrückliche Owner-Delegation durch die Orchestrator-Sitzung, Immutability vor dem Anlegen eingeschaltet). Siehe Hinweis 1 |
| T-25-03 | Info Disclosure | Messskript-Ausgabe | accept | siehe AR-25-01 | closed | Begründung am Artefakt bestätigt: rohdaten/01-*-lauf*.txt nur Zähler (`rss_anon_*_kb`, Raten, Versionen); 00-umgebung.txt nur Image-Digest, Docker-/Kernel-Version, Bildpfad im Container |
| T-25-04 | DoS | EmbeddingModel.release | mitigate | Idle-Prüfung unter self._lock, Test T10 | closed | embed/model.py:704-719 (`with self._lock`, `_in_flight`, `time.monotonic() - stamp < idle_seconds` -> False); embed/engine.py:610 (`held.release(idle_seconds=ttl_seconds)`); tests/test_embed_engine.py:1183 (Nutzung zwischen zweiter Lesung und release behält die Engine) |
| T-25-05 | Tampering | embedding_mark | mitigate | weights ohne Default, Aufrufer übergeben engine_precision() | closed | store/vectors.py:271 (`*, tokens: int, weights: str`, kein Default); einzige Aufrufer api/resources.py:243-245 (`weights=engine_precision()`) und worker/embedding.py:1003-1006 (gehaltene oder Ziel-Präzision); tests/test_vector_store.py:404-408 (Signaturtest) |
| T-25-06 | DoS | swap_engine | mitigate | Tausch lädt nichts, altes Modell zurückgegeben | closed | embed/engine.py:210-249 (`_build` baut nur Wrapper, `return old`, gleiches Gewicht -> None); tests/test_embed_engine.py:386 (`..._never_loads_the_new_one`), :368, :434 |
| T-25-07 | Spoofing | QueueController::getDocuments | mitigate | rejectForeignCaller erste Anweisung, Gate B, Controller-Test | closed | php/lib/Controller/QueueController.php:119-122 (erste Anweisung), :405-418 (EX-APP-ID gegen BACKEND_APP_ID, 403); tests/test_php_trust_boundary.py:95 (GUARD_CALL textuell); php/tests/Unit/QueueControllerTest.php:125-134 (fremder Aufrufer mit unbekannter Spur bekommt 403, kein `lane`-Feld) |
| T-25-08 | Tampering | Parameter lane | mitigate | geschlossene Menge LANES, strikt, 400 | closed | QueueController.php:124-126 (`in_array($lane, QueueService::LANES, true)` -> badLane); php/lib/Service/QueueService.php:81-84 (LANES); QueueController.php:572-576 (400 "Unknown lane."); QueueControllerTest.php:112 |
| T-25-09 | Info Disclosure | Logs | mitigate | statische Sätze ohne Eingabewert | closed | QueueController.php:573 (statischer Satz, kein Kontext); SettingsService.php:422-428 (nur Zähler `rejected`); QueueControllerTest.php:22-25 (Wert erreicht das Log nie) |
| T-25-10 | Tampering | model_precision | mitigate | geschlossene Menge, außerhalb null statt Default | closed | php/lib/Service/SettingsService.php:131 (PRECISIONS), :327-340 (strict in_array, reject(), `return null`); ProfileController.php:70; php/tests/Unit/ProfileControllerTest.php:178-204 (`fp16` -> `precision => null`); Containerseite: precision.py:142-143 (None/unbekannt ändert nichts), nc/queue.py:568 |
| T-25-11 | DoS | alter Container gegen neuen Companion | mitigate | Default all wie 1.3, Zusatzfelder stören nicht | closed | QueueController.php:118 (`$lane = QueueService::LANE_ALL`); QueueService.php:271-277 (Filter nur für index/embed, all = Schleife von 1.3); QueueControllerTest.php:78 (`['files' => [], 'lane' => 'all']`); nc/client.py:474-477 (1.4-Container sendet lane nur wenn gesetzt) |
| T-25-12 | EoP | Schreibweg Präzision | accept | siehe AR-25-02 | closed | Begründung am Code bestätigt: KEY_MODEL_PRECISION nur gelesen (SettingsService.php:121, 330), kein Setter in php/lib (grep), ProfileController nur GET |
| T-25-13 | Tampering | AdminViewService::backend | mitigate | precisionActive gegen Menge, reembedRunning nur bool | closed | php/lib/Service/AdminViewService.php:189 (PRECISIONS), :1890-1891, :1981-1982 (`is_string && in_array(..., true)` sonst null), :1993 (`is_bool` sonst null); php/tests/Unit/AdminViewServiceTest.php:268-271, :298-299 |
| T-25-14 | Tampering (XSS) | admin.php, admin.js | mitigate | p() bzw. textContent, Modellname aus geschlossener Menge | closed | php/templates/admin.php:253-259 (`$modelNames[...] ?? ''`, Name nie roh), :454 (`p($modelLine)`); php/js/admin.js:385-387 (Name aus `names`-Tabelle), :231-238 (`element.textContent = value`) |
| T-25-15 | Info Disclosure | Statusfläche | accept | siehe AR-25-03 | closed | Begründung am Code bestätigt: php/appinfo/info.xml:296 (nur `<admin>`-Settings); backend/appinfo/info.xml:308-310 (/status ADMIN) |
| T-25-16 | Spoofing | Echo der Spur | mitigate | lane_honored nur bei Echo aus LANES, das zur Anforderung passt | closed | nc/queue.py:424-427 (`isinstance(echoed, str) and echoed in LANES and echoed == (lane or LANE_ALL)`); nc/queue.py:91 (LANES); tests/test_profile_wire.py:99 (Gleichstand mit QueueService::LANES) |
| T-25-17 | Tampering | Präzisionswert | mitigate | nur PRECISION_NAMES, sonst None, Gleichstand PHP | closed | nc/queue.py:566-568; precision.py:50; tests/test_queue_client.py:505, :515, :522; tests/test_profile_wire.py (Gleichstand SettingsService::PRECISIONS) |
| T-25-18 | DoS | 1.3-Companion | mitigate | ohne lane bytegleich, fehlendes Feld None, Ausnahme -> CompanionChoice(None, None) | closed | nc/client.py:474-477 (`params["lane"]` nur wenn gesetzt); nc/queue.py:555-561 (`except Exception` -> `CompanionChoice(profile=None, precision=None)`), :567-568; tests/test_queue_client.py:515 |
| T-25-19 | Info Disclosure | Logs | mitigate | debug-Zeile ohne Antwortinhalt | closed | nc/queue.py:420, :560 (statische Sätze ohne Argumente) |
| T-25-20 | Tampering | heruntergeladene oder abgelegte Gewichte | mitigate | sha256 und Länge fest, beim Strom geprüft, Sideload verifiziert | closed | embed/weights.py:52-53 (Konstanten), :236-256 (Hash und Zähler beim Strom, falsch -> WRONG_DIGEST ohne Installation), :130-162 (fp32_verified für Sideload); worker/embedding.py:1169, :1188 (Aktivierung nur nach fp32_verified); tests/test_weights.py:329, :340, :458, :476, :483 |
| T-25-21 | Tampering / Info Disclosure | Umleitung | mitigate | Sprünge von Hand, Host gegen ASSET_HOSTS vor der Anfrage, nur https, max. drei | closed | nc/client.py:320 (ASSET_HOSTS), :324 (ASSET_MAX_REDIRECTS = 3), :341-346 (Schema und Host), :360 (`follow_redirects=False`), :370-392 (Prüfung vor dem nächsten Request); tests/test_weights.py:108, :121, :132, :143, :232 |
| T-25-22 | Info Disclosure | Zugangsdaten | mitigate | eigener Client ohne AppAPI-Header, ohne NC-Zertifikat, ohne Cookies | closed | nc/client.py:349-360 (eigener httpx.AsyncClient ohne Header und ohne `verify=_certificate_setting()`), :374 (`client.cookies.clear()` je Sprung); tests/test_weights.py:195 (keine Anfrage trägt Credential oder Cookie), :217 |
| T-25-23 | DoS | Platte | mitigate | Platzprüfung vor dem Strom, Deckel FP32_BYTES, .part immer entfernt | closed | embed/weights.py:299-308 (disk_usage vor dem Fetch -> NO_ROOM), :247 (`cap=FP32_BYTES`), nc/client.py:385-389 (Byte-Deckel), weights.py:310-313 (`finally: _drop_part`), :258-270 (WR-03: ENOSPC am fsync -> NO_ROOM); tests/test_weights.py:170, :348, :422 |
| T-25-24 | Tampering | halbe Datei nach Kill | mitigate | .part, fsync, os.replace im selben Verzeichnis, clear_leftovers | closed | embed/weights.py:109-111 (.part neben Ziel), :208-211 (flush + fsync), :280 (`os.replace`), :176-190 (clear_leftovers nur dieser Name); worker/embedding.py:1146-1149 (beim Öffnen, nie während eines laufenden Fetch); tests/test_weights.py:302, :521 |
| T-25-25 | EoP | Dateipfade | mitigate | fester Name unter models_dir aus Konfiguration, Gate-Ausnahme nur mkdir in weights.py | closed | embed/weights.py:60-62, :104-106 (fester Name); alle Aufrufer übergeben `settings().models_dir` (worker/embedding.py:1084, 1149, 1168, 1185, 1281), config.py:1434 (`root / "models"`); tests/test_readonly_gate.py:128 (nur `("embed/weights.py", "mkdir")`), :436 |
| T-25-26 | DoS | RAM-Bedingung | mitigate | anon statt memory.current, unlesbar nicht zugelassen | closed | memory_guard.py:27-43 (anon aus memory.stat), :46-64 (kein memory.current), :67-69 (`headroom is not None and ...`); tests/test_memory_guard.py:52, :91, :109. Fallback auf MemAvailable bei fehlendem anon ist planmäßig (25-06-PLAN.md:165) |
| T-25-27 | Info Disclosure | Telemetrie | mitigate | ein GET auf feste URL, nur auf Admin-Aktion, keine Kennung | closed | embed/weights.py:56-58 (feste URL), :247 (einziger Fetch-Aufruf); einziger Aufrufer von procure_fp32 ist worker/embedding.py:1216, nur über decide nach beobachtetem Wechsel des Admin-Schlüssels (precision.py:145-146, 235-238); nc/client.py:360 (keine Header) |
| T-25-28 | Tampering | geteilte SQLite-Verbindung | mitigate | eigene Verbindungen, Test mit zwei Schreibern unter WAL und busy_timeout | closed | worker/embedding.py:278-290 (eigene open_store-Verbindung), :380-397; store/repo.py:585, :631 (WAL, busy_timeout); store/vectors.py:383; tests/test_track_connections.py:144, :154, :171 |
| T-25-29 | Tampering | Tantivy-Writer | mitigate | eigener Handle mit stored_body, kein .writer() | closed | worker/embedding.py:572 (`stored_body` über eigenen Handle), :395-396 (`_open_read_handle`); tests/test_embedding_track.py:831-838 (`".writer(" not in source`), :844-853 (`poller._writer = None`) |
| T-25-30 | Tampering | Driftkette | mitigate | Marke, Drift, Bänder nur im Track, Reihenfolge unverändert | closed | worker/embedding.py:1072-1084 (forget_all, Cursor, Marke, Tausch); einzige Schreiber von EMBEDDING_MARK/EMBEDDING_BACKLOG_MARK in worker/embedding.py (grep über src/findling: status.py und resources.py nur lesend); tests/test_embedding_track.py:1250-1299 (Phase-24-Tests grün), :1348 |
| T-25-31 | DoS | state.db-Anlage | mitigate | nur existierende state.db, sät nichts | closed | worker/embedding.py:278-290 (`if not path.exists(): return None`); tests/test_track_connections.py:188 |
| T-25-32 | DoS | Startzustand | mitigate | Ziel None vor Lesen und settle, settle nur aus Marke plus verifizierter Datei | closed | precision.py:252-253 (`_CHOSEN is None or _ACTIVE is None` -> target None); worker/embedding.py:1150-1172 (settle aus Marke `/fp32` und fp32_verified; Lesefehler setzt nichts); tests/test_precision.py:86, :97, :105; tests/test_precision_wiring.py:275 (fp32-Start ohne Lesen, forget_all nie) |
| T-25-33 | Tampering | automatischer Download | mitigate | nur nach beobachtetem Übergang int8 -> fp32, einmal, kein Wiederholen | closed | precision.py:145-146 (erste Lesung nie ein Wechsel), :235-238 (PENDING einmal verbraucht), :208-215 (Fehlschlag -> VERDICT_UNAVAILABLE, kein Retry bis int8 und zurück); tests/test_precision.py:118, :128; tests/test_precision_wiring.py:368, :396 |
| T-25-34 | EoP | Profilwechsel als Auslöser | mitigate | Ablehnung unter Sparsam verbraucht Wunsch, Profilwechsel löst nichts aus | closed | precision.py:223-230 (`_PENDING = False`, VERDICT_NOT_IN_ECONOMY, danach nie FP32); tests/test_precision.py:179, :195; tests/test_precision_wiring.py:423 |
| T-25-35 | DoS | RAM-Schranke | mitigate | FP32_EXTRA_BYTES gemessen und abgezogen, embed_lane_fits ungeklammert | closed | config.py:864-868 (367 MiB, Messung 25-01); profile.py:188-190, :212 (Abzug im Speicherterm), :316-326 (`term >= max(1, slots)`, Term selbst ohne max-Klammer); worker/embedding.py:1594-1595 (fp32-Ladekosten im Live-Bedarf) |
| T-25-36 | DoS | Zeilen in Sperrfrist | mitigate | jeder Ausstieg ohne Quittung ruft unlock, SQLite-Fehler mit _abort-Semantik | closed | worker/embedding.py:1466-1474 (Generalfang unlock_held), :1510-1517, :1542-1550 (sqlite3.Error/_DiskTight -> unlock_held), :1552-1557 (Rest per unlock); worker/poller.py:824-835 (`_abort`); tests/test_embedding_runner.py:487, :633 |
| T-25-37 | DoS | IDX-08 in Sparsam | mitigate | Runner parkt in Economy, Hauptschleife wartet, Tor je Zeile | closed | worker/embedding.py:1567-1569 (Tor), :1496-1497 (erneut hinter der Sperre), :1531-1536 (je Zeile), :1480-1484 (parked); worker/poller.py:754-761, :837-848 (wartet auf parked vor dem Anspruch); tests/test_embedding_runner.py:309, :517, :839 (T1), :894 (T4) |
| T-25-38 | DoS | Speichererschöpfung | mitigate | statisch embed_lane_fits plus live anon mit Reserve und Ladekosten, unlesbar seriell | closed | worker/embedding.py:1572-1581 (statisch, dann live), :1583-1596 (Aktivierungen + EMBED_LANE_RESERVE_BYTES + Cutter- und Gewichts-Ladekosten); memory_guard.py:67-69; tests/test_embedding_runner.py:344, :356, :403 |
| T-25-39 | Spoofing | alter Companion ignoriert lane | mitigate | kein Anspruch ohne Echo, fehlendes Echo -> alles unlock, lebenslang geparkt | closed | worker/embedding.py:1570-1571 (`lane.snapshot().supported`), :1510-1517 (unlock_held, note_refused); lane.py:58-75 (`_REFUSED` sticky); worker/poller.py:773 (note_echo); tests/test_embedding_runner.py:334, :464 (T8) |
| T-25-40 | Tampering | Doppeleinbettung | mitigate | replace_chunks je Datei in einer Transaktion, Übergabe aus _held entfernt | closed | store/vectors.py:427-449 (Delete + Insert in `self._transaction()`); worker/embedding.py:601-614, :1552-1557 (quittiert/entsperrt, `_held.clear()`); tests/test_embedding_runner.py:588 (T6, echte vectors.db, kein doppelter Chunk) |
| T-25-41 | Info Disclosure | Logs | mitigate | Typnamen und Zähler, keine Werte | closed | worker/embedding.py:1473 (`type(error).__name__`), :1545-1547 (Zähler und Typname), :1516 (statisch), :1220, :1223 (Name des Ergebnisses aus geschlossener Menge) |
| T-25-42 | DoS | Abbau | mitigate | unlock_held nach Stopp, Ausnahme unterdrückt | closed | main.py:1016-1028 (`contextlib.suppress(Exception)` um `_EMBEDDING.unlock_held()`, vor dem Poller); tests/test_main_lifespan.py:1377, :1389, :1402 |
| T-25-43 | DoS | Freigabe während Einbettung | mitigate | track.busy statt poller.busy plus Idle-Guard unter Modellsperre | closed | main.py:458-464 (`track.busy or any(driver.busy ...)`); worker/embedding.py:432-437 (`_rows_in_work > 0`), :513-517; embed/model.py:704-719; tests/test_main_lifespan.py:321, :1454 |
| T-25-44 | Tampering | Rebuild | mitigate | Runner vor dem Poller stillgelegt, Handle abgegeben, danach beide bewaffnet | closed | main.py:526-539 (Runner zuerst, bei Fehlschlag kein Umbenennen), :575-577 (beide armen); tests/test_main_lifespan.py:1483 |
| T-25-45 | Info Disclosure | Start | mitigate | kein Netz und kein Download im Start, grep-Kriterium | closed | main.py ohne `fetch_release_asset`/`procure_fp32` (grep leer); tests/test_main_lifespan.py:1543-1544 (statischer Quelltexttest) |
| T-25-46 | Tampering | Mischbestand int8/fp32 | mitigate | Kette nur im Track unter Sperre, forget_all, Cursor, Marke, Tausch | closed | worker/embedding.py:1072-1092 (Reihenfolge, WR-01: note_active direkt nach dem Tausch), :1003-1009; worker/poller.py:793-794 und worker/embedding.py:1493, :1521 (nur unter `self._track.lock`); tests/test_precision_wiring.py:537-551 (Ereignisreihenfolge, `engine_precision() == active.value`), :692 |
| T-25-47 | DoS | Startzustand | mitigate | fp32 aus Marke plus verifizierter Datei, nie aus Lesefehler | closed | worker/embedding.py:1152-1158 (Lesefehler setzt nichts), :1165-1172; nc/queue.py:555-561 (werfende Profilroute -> None, ändert nichts, precision.py:142-143); tests/test_precision_wiring.py:275-295 (Route ohne Antwort, `forgotten == []`) |
| T-25-48 | Tampering | Modell aus dem Netz | mitigate | Aktivierung nur nach PROCURED oder fp32_verified, sonst Verdikt, kein Wiederholen | closed | precision.py:231-234 (FP32 nur bei `fp32_ready`), worker/embedding.py:1186-1189 (fp32_ready = fp32_verified), weights.py:284 (PROCURED nur nach Digest); tests/test_precision_wiring.py:597, :396 |
| T-25-49 | DoS | zwei Modelle im RAM | mitigate | swap_engine lädt nichts, altes Modell vor erstem Einbetten freigegeben | closed | worker/embedding.py:1243-1247 (`swap_engine`, `_let_go_of(old)`), :1619-1633; embed/engine.py:210-249; tests/test_embed_engine.py:386 (Ladezähler), tests/test_precision_wiring.py:614 |
| T-25-50 | Tampering | Löschen | mitigate | nur fp32_weights_path unter models_dir, nach Freigabe, nur beim Rückweg auf int8 | closed | worker/embedding.py:1241 (`leaving_fp32`), :1247-1250 (nach `_let_go_of`); WR-04-Pfad :1256-1286 (nur bei `withdrawal_pending`, Schlüssel int8, Halter int8, kein Fetch); embed/weights.py:193-205 (nur fester Pfad und .part); tests/test_precision_wiring.py:635, :743, :776, :804 |
| T-25-51 | Info Disclosure | Beschaffung beim Start | mitigate | Beschaffung nur über decide nach beobachtetem Wechsel | closed | worker/embedding.py:1189-1191 (einziger Start von `_start_the_procurement`); precision.py:145-146, :239-241; tests/test_precision_wiring.py:342 (ohne Wunsch nichts gehasht, geholt, getauscht) |
| T-25-52 | Info Disclosure | GET /status | accept | siehe AR-25-04 | closed | Begründung am Code bestätigt: api/status.py:365-386 (nur Wörter aus geschlossenen Mengen und int8/fp32); backend/appinfo/info.xml:308-310 (ADMIN) |
| T-25-53 | DoS | Statusroute | mitigate | Leser ohne I/O, Test | closed | api/status.py:365-386 (nur `precision.snapshot()`, `engine_precision()`, `lane.snapshot()`); tests/test_status_endpoint.py:1460-1477 (`hash_count` unverändert, Datei unberührt, kein Import von findling.embed.weights oder hashlib) |
| T-25-54 | Tampering | Doku-Anleitung Offline-Weg | mitigate | Doku nennt sha256 und Prüfung vor Nutzung | closed | docs/embeddings.md:913 (sha256), :927 (Container prüft vor Nutzung), :932-933 (sha256sum-Befehl mit Sollwert); Code-Seite T-25-20 |

*Status: open · closed*
*Disposition: mitigate (Umsetzung nötig) · accept (dokumentiertes Risiko) · transfer (Dritte)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-25-01 | T-25-03 | Die Messskript-Ausgabe (Plan 25-01) enthält nur RssAnon-Zähler, Raten, Versionen und feste Beispielsätze, keine Nutzerdaten und keine Pfade des Entwicklerrechners. Am Artefakt bestätigt: rohdaten/01-*.txt und 00-umgebung.txt tragen nur Zähler, Image-Digest und den Modellpfad im Abbild. | Owner (Plan 25-01, Register zur Planzeit) | 2026-09-28 |
| AR-25-02 | T-25-12 | Wie AR-24-02: `model_precision` hat keinen Schreibweg außer `occ config:app:set` (Serverzugang, also volle Rechte). Keine Schreibroute; die Settings-UI folgt in Phase 27 und braucht dort ein eigenes Register. Am Code bestätigt: KEY_MODEL_PRECISION wird nur gelesen, ProfileController nur GET. | Owner (Plan 25-03, Register zur Planzeit) | 2026-09-28 |
| AR-25-03 | T-25-15 | Präzision und Zähler auf der Statusfläche sind Betriebsdaten, sichtbar nur in den Admin-Einstellungen (php/appinfo/info.xml:296) über die ADMIN-Route /status. | Owner (Plan 25-04, Register zur Planzeit) | 2026-09-28 |
| AR-25-04 | T-25-52 | GET /status trägt Präzision, Verdikt und Spurzustand als Wörter aus geschlossenen Mengen; keine Pfade, Digests oder URLs. Route bleibt access_level ADMIN (backend/appinfo/info.xml:310). | Owner (Plan 25-12, Register zur Planzeit) | 2026-09-28 |

*Akzeptierte Risiken tauchen in späteren Audits nicht erneut auf. AR-25-02 ist an Phase 27 gebunden: sobald dort eine Schreibroute für Profil oder Präzision entsteht, verfällt die Begründung.*

---

## Unregistered Flags

Keine. Threat-Flags-Abschnitte in 25-06, 25-09, 25-10, 25-11 und 25-12-SUMMARY.md melden keine neue Fläche und verweisen nur auf registrierte IDs (T-25-21/22/24/25/27, Queue-Routen aus T-25-36..41, T-25-45, Host-Allowlist aus 25-06, T-25-52..54). Die übrigen SUMMARY-Dateien haben keinen Threat-Flags-Abschnitt.

## Hinweise (informativ, keine Blocker)

1. **T-25-02, Abweichung im Ablauf:** Der Plan sah den Upload als eigene Owner-Handlung vor; laut 25-01-SUMMARY.md:67-68 hat der Owner ihn an die Orchestrator-Sitzung delegiert. Der Kern der Mitigation (Executor lädt nichts hoch, pusht nichts) ist eingehalten, und die Integrität des Assets hängt nicht am Handelnden: immutable Release plus Digest-Pin im Code (T-25-01, T-25-20). Die Delegation ist nur über das SUMMARY belegt, nicht über ein eigenes Owner-Protokoll.
2. **T-25-26:** Fehlt die anon-Zeile bei gesetzter Grenze, antwortet headroom_bytes mit MemAvailable statt None. Das ist planmäßig (25-06-PLAN.md:165) und auf cgroup v1 dokumentiert (memory_guard.py:16-18); "nicht zugelassen" gilt, wenn gar nichts lesbar ist.
3. **T-25-47:** Der Test belegt den Zustand "Profilroute hat nicht geantwortet" (chosen None) direkt; dass eine werfende Route genau diesen Zustand erzeugt, belegen nc/queue.py:555-561 und tests/test_queue_client.py (werfende Fakes). Kein eigener End-to-End-Test mit werfender Route im Track.
4. **T-25-50 nach WR-04:** Es gibt jetzt zwei Löschpfade (Tausch und `_sweep_a_withdrawn_file`). Beide treffen nur `fp32_weights_path(models_dir)` plus `.part` und nur nach beobachtetem Rückweg fp32 -> int8; ein Sideload unter stehendem fp32-Wunsch wird nie gelöscht (tests/test_precision_wiring.py:804).
5. PHP-Belege (T-25-07..14) sind per Quelltext und Unit-Test-Inspektion geprüft; PHPUnit läuft nur in CI.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-28 | 54 | 54 | 0 | gsd-security-auditor (Belege per grep/Read an HEAD 46f91398; 15 Python-Testdateien: 533 passed, 1 skipped) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-28
