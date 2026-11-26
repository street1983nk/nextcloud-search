---
phase: 45
slug: findling-1-7-0
status: verified
threats_open: 0
asvs_level: 1
created: 2026-11-26
---

# Phase 45: Security

> Sicherheitsvertrag der Phase: Threat-Register, akzeptierte Risiken und Audit-Trail.
> Register aus den `<threat_model>`-Blöcken von 45-01 bis 45-27 (register_authored_at_plan_time: true), jede ID genau einmal; 45-25 und 45-26 bringen keine eigene ID (ihr Teil steht unter T-45-81 bzw. T-45-33 und T-45-82).
> Geprüfter Stand: Tag-Kandidat K = 22f98ef260fb12f8b55844b76d8070e64f441a4d (Tag-Kopf aus 45-ABNAHME.md, = origin/main), audited_head bb4c0bc8ca9c2b96edacc4de8a846d9d5ccdfe4d. Belege je ID im Detail: 45-AUDIT.md `## Threat-Register 45` (T-45-01 bis T-45-34), `### Threat-Register 45-17 bis 45-24` und `## Nachtrag Threats vor dem Tag` (Proben P1 bis P9 am Kandidaten). Alle Proben mit `git show K:...`, nie mit `git show v1.7.0`; es gibt keinen Tag v1.7.0 (lokal, entfernt, als Release).

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Fremd-PR -> main | PR #56 und #57 von foolfitz, Kataloge und Workflow-Änderung | Fremdcode, Katalogwerte |
| Admin-Browser -> POST /admin/rules | Liste ausgeschlossener externer Speicher, Ordner- und Mustereinträge | Admin-Eingaben |
| occ / appconfig -> SettingsService | per occ geschriebene Werte ohne Routenprüfung | Konfiguration |
| Template / admin.js -> Seite | Einhängepunkte, Katalogwerte, Bestätigungssätze | Markup-Risiko (XSS) |
| ExApp -> Gateway (#59) | erneutes Öffnen als andere Person unter Secure View | Dateiinhalte, Rechte |
| Suche -> Textausschnitte (E3) | Ausschnitte von Dateien unter Secure View | Dateiinhalte |
| Begleit-App <-> Container (Generation 4) | Draht-Vokabular bei getrenntem Update | Urteile |
| Hintergrundjobs (Crawl, Nachzählung, Abgleich) | Locks, Marker, Rückhalt | Verfügbarkeit |
| Update 1.6.x -> 1.7.0 | Migrationen im laufenden Prozess (#51) | Verfügbarkeit der Suche |
| Executor -> Owner-Entscheide | Push, Store-Text, Abnahme, Signatur | Entscheidungshoheit |
| CI-Runner -> Signaturschlüssel | Environment release | Schlüssel |
| Tag-Kandidat | ein offener Threat am Kandidaten ginge mit dem Tag in den Store | alles oben |

---

## Threat Register

Beleg-Konvention: Datei:Zeile am Kandidaten K; Lauf-IDs per `gh run view` am 26.11.2026 gegengeprüft (45885132920 mit Job "Store update in one process (issue 51)", 45892161829 Signatur-Probe, beide headSha = K). P1 bis P9 = Proben in 45-AUDIT.md `## Nachtrag Threats vor dem Tag`.

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-45-01 | Tampering | Merge eines nachträglich geänderten PR-Kopfs | mitigate | `gh pr merge --match-head-commit` auf 168b6b13 (#57) und 51690b2a (#56), 45-PR-REVIEW.md | closed |
| T-45-02 | Elevation of Privilege | Workflow-Änderung in PR #56 | mitigate | Diff gelesen (45-PR-REVIEW.md); zizmor/actionlint grün; Workflows an K gleich dem zuletzt gelinteten Stand aff5f1d3 (Lauf 45425765738, P6) | closed |
| T-45-03 | Tampering (XSS) | zh_TW-Katalogwerte mit Markup | mitigate | nur `p()`/Textknoten; test_no_catalogue_value_can_break_the_page, Platzhalter-Parität (test_admin_ui_contract.py 236 passed an K, P9); kein print_unescaped im Template an K (P2) | closed |
| T-45-04 | Repudiation | Merge ohne Owner-Zustimmung | mitigate | `Freigabe Merge PR57 45-01` und `Freigabe Merge PR56 45-01` ("Go", 2026-11-22 01:04) in 45-FREIGABEN.md | closed |
| T-45-05 | Tampering | excludedExternalMounts() mit kaputtem occ-Wert | mitigate | Probe 3 (45-09); L-45-09-02/03 behoben (af0e5e13, fcfa50b2); PHPUnit an K success (Lauf 45885132920) | closed |
| T-45-06 | Denial of Service | sehr lange Liste | mitigate | Obergrenze 1000 beim Schreiben und Lesen (L-45-09-01 behoben 2b623a3f), Bänder und Cache (Probe 13b) | closed |
| T-45-07 | Information Disclosure | Logzeilen mit IDs oder Mountpunkten | mitigate | Probe 12 (nur Zähler), assertNoLogCarries; Logzeilen-Probe 45-21 | closed |
| T-45-08 | Tampering | ID eines persönlichen Mounts | mitigate | Probe 4 und 5 (nur ADMIN_MOUNT_TYPE, zweiter Mount hält den Speicher) | closed |
| T-45-09 | Denial of Service | Ausschluss löscht mehr als gewollt | mitigate | `!isIndexedStorage()` in deselected(), Probe 5, M-45-01; R-45-21-12 behoben (b3af58e9/6dc5bb70), Volltest 32 bis 34 echt | closed |
| T-45-10 | Elevation of Privilege | saveRules für Nicht-Admins | mitigate | route-security.json ohne Diff gegen v1.6.5, saveRules `attributes: []` an K (P8); RouteSecurityTest in PHPUnit an K success | closed |
| T-45-11 | Tampering | excludedExternalMounts mit Nicht-int, negativ, Riesenliste | mitigate | Probe 2 (elf Datensätze, Mutation); Objekt-Form abgelehnt (af0e5e13) | closed |
| T-45-12 | Information Disclosure | Mountpunkte im Initial State, Poll, Logs | mitigate | testTheMountListIsATemplateParameterAndNeverInTheInitialState; rules() nur IDs; Probe 12 | closed |
| T-45-13 | Tampering (XSS) | Einhängepunkt mit Markup | mitigate | Probe 10; an K P1 und P2 (innerHTML 0, Einhängepunkt nur über `p()` Z. 1745) | closed |
| T-45-14 | Denial of Service | altes admin.js löscht Ausschlüsse | mitigate | Default null = unverändert, testWithoutTheFieldTheStoredSelectionStaysAsItWas | closed |
| T-45-15 | Denial of Service | Upgrade sperrt Admins mit alten *-Einträgen | mitigate | Probe 11 (Duldung gespeicherter Einträge) | closed |
| T-45-16 | Tampering (XSS) | gerenderter Eintrag, Zählersatz, Katalogwert | mitigate | nur `p()`, Gate C, Funktions-Replacements gegen `$&`; an K P1, P2, test_admin_ui_contract.py | closed |
| T-45-17 | Information Disclosure | abgewiesener Wert in Antwort oder Log | mitigate | testANewFolderEntryWithAWildcardEarnsItsCodeAndNotItsValue | closed |
| T-45-18 | Spoofing | Client-Vorprüfung umgangen | accept | Server entscheidet in validate(); Script nur Komfort (R-45-01) | closed |
| T-45-19 | Tampering (XSS) | Einhängepunkt mit Markup in Liste und Bestätigung | mitigate | Probe 10; Sichtprobe 45-10 erledigt: 45-VOLLTEST.md Proben 2 bis 4 (0 `img[src=x]`, kein Dialog, Text wörtlich); an K P1, P2 | closed |
| T-45-20 | Denial of Service | versehentlicher Ausschluss | mitigate | Inline-Bestätigung mit Einhängepunkt, Fokus auf dem harmlosen Knopf (45-05); Volltest Proben 2 bis 4 und 34, Owner-Abnahme 45-10 | closed |
| T-45-21 | Tampering | Speichern ohne gerenderte Liste | mitigate | Probe 9 (inForceMounts unverändert, Fehl-Sample); Volltest P-FAIL 29 (`[1]` vorher und nachher) | closed |
| T-45-22 | Spoofing | manipulierte IDs im Request | accept | nur Admins (T-45-10), Form-Prüfung (T-45-11), fremde IDs wirken nur als Admin-Mounts (T-45-08) (R-45-02) | closed |
| T-45-23 | Tampering | template-injection in neuen run:-Blöcken | mitigate | zizmor/actionlint lokal und CI grün; Workflows an K = gelinteter Stand (P6); Strukturgate scan_watermark_job (kein `${{ }}` im run-Block) in test_php_static_gates.py 81 passed | closed |
| T-45-24 | Repudiation | Push ohne Owner-Zustimmung | mitigate | `Freigabe Push 45-06` vor dem Push (612b7c9e); alle späteren Pushes mit eigener Zeile (45-09, 45-10, 45-10 Fix, 45-10 V-07, 45-12) | closed |
| T-45-25 | Denial of Service | Ausschluss nur mit Gnadenfrist | mitigate | expect_unstamped in M-45-01 (stamp '') | closed |
| T-45-26 | Repudiation | Gate-Verlust beim Umzug | mitigate | Tabelle alt -> neu in 45-07-SUMMARY, Fehl-Sample je Gate | closed |
| T-45-27 | Information Disclosure | falsche Datenschutz-Aussage in README | mitigate | 45-README-PRUEFUNG.md (24 Aussagen mit Quelle); Datenschutz-Kern-Gate auf info.xml | closed |
| T-45-28 | Tampering | ungeplante Schema- oder Migrationsänderung | mitigate | an K: Migrations-Diff gegen v1.6.5 nur Version001500 (Owner m1) und Version001700 (45-26), beide ohne Schema-Aufruf und ohne Klasse der App (P8) | closed |
| T-45-29 | Denial of Service | Update bricht im laufenden Prozess (#51) | mitigate | FROM_TAGS v1.3.2 bis v1.6.5; Job "Store update in one process (issue 51)" an K success, alle sieben Kandidaten ok (P4) | closed |
| T-45-30 | Repudiation | Versionen laufen auseinander | mitigate | beide info.xml an K 1.7.0 (P8); test_lockstep_versions.py 23 passed (P9) | closed |
| T-45-31 | Tampering | auseinanderlaufende zizmor/actionlint-Digests | mitigate | Digest-Gate mit Fehl-Samples (92fd028a); an K beide Referenzen gleich (P8) | closed |
| T-45-32 | Elevation of Privilege | Rechte-Grenze der Regeln-Route | mitigate | wie T-45-10 | closed |
| T-45-33 | Denial of Service | Upgrade-Bruch ab 1.6.5 | mitigate | Beleg erneuert im Nachtrag: Update-Probe mit Kontrolle 2 (45-26, M35 und M36 rot), Job "Store update in one process (issue 51)" an K grün mit `control 2 ok` und `update proof: both controls reproduced, every candidate run passed` (Lauf 45885132920, Job 140133837003), echte Läufe 45-20 (Container zuerst, 1 Treffer, backend_app_version leer) und 45-10 P-UPD (Begleit-App zuerst, 1 Treffer) | closed |
| T-45-34 | Repudiation | Audit ohne Beleg | mitigate | jede Zeile von 45-AUDIT.md mit Probe; genau eine `audited_head:`-Zeile (bb4c0bc8) | closed |
| T-45-35 | Tampering (XSS) | Einhängepunkt mit Markup im echten Browser | mitigate | 45-VOLLTEST.md Saat `<img src=x onerror=alert(1)>`, Proben 2 bis 4 und 39 (0 img, kein Dialog); an K `git show K:php/js/admin.js \| grep -c innerHTML` = 0, Template nur `p()` (P1, P2) | closed |
| T-45-36 | Information Disclosure | Treffer eines ausgeschlossenen Speichers bleiben sichtbar | mitigate | Volltest 32 bis 34: nach dem echten Abgleich 0 Treffer (auch über Freigabe), Gegenkontrollen 1 Treffer | closed |
| T-45-37 | Repudiation | Abnahme ohne Owner | mitigate | `Abnahme Härtung 45-10: "Ok" (2026-11-26 14:40)` und `Abnahme zweite Sichtprüfung V-45-10-07: "Ja" (16:38)` | closed |
| T-45-38 | Tampering | Fix nach der Abnahme ändert den Kandidaten unbemerkt | mitigate | Diff audited_head..K nur die sieben in 45-12 erlaubten Dateien, CHANGELOG nur die Datumszeile | closed |
| T-45-39 | Repudiation | Store-Text ohne Owner-Freigabe | mitigate | `Freigabe Storetext 45-11: "Ok" (2026-11-26 18:59)`; P3: sechs Beschreibungen an K zeichengleich zum Entwurf am Freigabe-Commit 76c6f389, Positivkontrolle rot | closed |
| T-45-40 | Information Disclosure | falsche Datenschutz-Aussage im Store | mitigate | P3: Datenschutz-Zeile je Sprache wörtlich aus v1.6.5; PRIVACY_MARKERS-Gate (test_store_metadata.py 168 passed) | closed |
| T-45-41 | Tampering | ungültige info.xml bricht die Einreichung | mitigate | Job "info.xml on the store validation path" an K success (Lauf 45885132920); lokal 45-11 bestanden | closed |
| T-45-42 | Tampering | ungeprüfter Code zwischen Härtung und Tag | mitigate | wie T-45-38; Code c1cb767c = K | closed |
| T-45-43 | Repudiation | Push ohne Freigabe | mitigate | `Freigabe Push 45-12: "Ok" (2026-11-26 19:38)` steht im gepushten Kopf K selbst | closed |
| T-45-44 | Information Disclosure | Signaturschlüssel im Lauf | mitigate | release.yml an K: `environment: release`, umask 077, Aufräumschritt `if: always()`; Log "neither key file exists any more", Werte nur maskiert (P7); Lauf nach `Freigabe Signatur 45-13` | closed |
| T-45-45 | Spoofing | unsignierte oder falsch signierte Archive | mitigate | Lauf 45892161829: zweimal `Verified OK`, signature.json im Archiv (P7) | closed |
| T-45-46 | Tampering | Probe auf anderem Stand als dem Tag-Kopf | mitigate | headSha von 45892161829 = K | closed |
| T-45-55 | Repudiation | Tag, obwohl Threats offen sind | mitigate | blockierender Checkpoint 45-16 Task 2 vor 45-14, dieses Dokument mit threats_open 0 und jeder ID genau einmal; kein Tag v1.7.0 | closed |
| T-45-56 | Tampering | Beleg nur mit dem Muster der Umsetzung | mitigate | P3 gegen den Freigabe-Entwurf mit Fehl-Sample, P4 und P7 aus CI-Logs, P8 aus `git show K` | closed |
| T-45-57 | Elevation of Privilege | erneutes Öffnen im Gateway | mitigate | rejectForeignCaller erste Anweisung (GatewayController Z. 92 an K); PHPUnit an K success; test_php_trust_boundary.py 21 passed | closed |
| T-45-58 | Information Disclosure | 404-Gleichheit, Nutzer-Enumeration | mitigate | GatewayReader::open (NoUser unverändert), not_found-Gleichheit (GatewayControllerTest); Code seit audited_head unverändert | closed |
| T-45-59 | Information Disclosure | Logzeilen der neuen Zweige | mitigate | Logzeilen-Probe 45-21 (nur Zähler, fileId, Klassen, origin, reader-uid nach a1); 45-27 nur BACKSTOP_LINE mit Zahlen | closed |
| T-45-60 | Information Disclosure | Treffer für Empfänger unter Secure View | mitigate | SnippetPolicy vor exApp->snippets (SearchService Z. 539-545 an K); watermark-59 in Integration 45885132814 an K success; Volltest 17 bis 22; test_php_acl_boundary.py 13 passed | closed |
| T-45-61 | Denial of Service | Schleife des erneuten Öffnens | mitigate | MAX_READER_TRIES 20 (ReaderCandidates Z. 34, 198), mit Besitzer ein Versuch; Zeitmessung 0,21 s (45-20) | closed |
| T-45-62 | Denial of Service | Ausfallzählung im Poller | mitigate | worker/poller.py Z. 2730, 3010 an K; test_poller in Python gates an K success | closed |
| T-45-63 | Tampering | Draht-Vokabular bei getrenntem Update | mitigate | nc/queue.py VERDICTS_GENERATION 4, bekannte {2, 3, 4}, Rückfall gateway_error; R-45-21-14 (verdicts 3, verdictsMax 4) | closed |
| T-45-64 | Repudiation | Kandidat ändert sich unbemerkt, Fix ohne Owner | mitigate | Freigabe- und Entscheidzeilen je Befund; eine audited_head-Zeile; 45-10 komplett neu; Push nur mit Freigabe | closed |
| T-45-65 | Tampering (XSS) | Bestätigungszeile mit ID | mitigate | nur textContent, Regex-Ersetzung mit Callback, Gate mit Fehl-Samples (test_admin_ui_contract.py 236 passed an K); P1 | closed |
| T-45-66 | Tampering | Katalogwert des Platzhalters im Attribut | mitigate | nur `p()` (P2), test_no_catalogue_value_can_break_the_page | closed |
| T-45-67 | Information Disclosure | Umgehung einer Sperre durch Lesen als andere Person | mitigate | isSecureViewRefusal (GatewayReader Z. 145-154 an K: Nachricht UND Ursprungs-Frame); I-45-17-03 echt in 45-20 Schritt C (a) bis (c) | closed |
| T-45-68 | Tampering | Nachbau mit falscher Version oder ohne Quelle | mitigate | `### Quellen am Tag` mit SHA-256, Modustabellen vorher/nachher | closed |
| T-45-69 | Denial of Service | einmalige Erneuerung erzeugt Last | accept | Marke refusal_streaks_1_7_0 (repo.py Z. 246), höchstens drei Anfragen je Datei, einmal je Datenbank (R-45-03) | closed |
| T-45-70 | Spoofing | 403 einer fremden Quelle mit gefälschtem Kopf | accept | Antwort nur vom eigenen Gateway über AppAPI, Folge nur ein anderes Urteil (R-45-04) | closed |
| T-45-71 | Tampering | richdocuments-Download in CI | mitigate | integration.yml an K Z. 4893-4894 Version 11.1.3 und SHA-256 gepinnt, nach app:enable geprüft; Workflows gelintet (P6) | closed |
| T-45-72 | Repudiation | Simulation der Zeitmarke als echter Beleg | mitigate | kein d2-Fall, Schritt 0 und Abgleiche echt abgewartet (45-20, d1) | closed |
| T-45-73 | Repudiation | Review mit dem Muster der Umsetzung | mitigate | 45-REVIEW-1-7-0.md: zweiter Prüfer ohne Umsetzungskontext, Fremdquellen mit SHA-256, Befunde am Code nachgeprüft | closed |
| T-45-74 | Repudiation | Prüfspur nennt für Secure-View-Dateien die lesende Person | accept | Owner-Entscheid a4 (2026-11-23 15:47): Erweiterung der Prüfspur bewusst, in docs/privacy.md genannt; Threat Flag audit-trail aus 45-20-SUMMARY (R-45-05) | closed |
| T-45-75 | Information Disclosure | Textausschnitt einer Secure-View-Datei | mitigate | SnippetPolicy fail-closed vor den Ausschnitten (an K), watermark-59 an K success, Volltest 17 bis 22 | closed |
| T-45-76 | Spoofing | Erkennung bricht bei neuer richdocuments-Version | mitigate | beide Bedingungen nötig, sonst policy ohne Umgehung (an K Z. 145-154) | closed |
| T-45-77 | Denial of Service | Zusatzabfragen je Suche | mitigate | nur bei aktivem Wasserzeichen, gebändert je Seite (Delta-Audit 45-21) | closed |
| T-45-78 | Tampering | Bruch einer internen richdocuments-API (S2) | mitigate | entfallen, S2 nicht gebaut (Entscheid E3-Weg 45-22: S3, nur OCP); watermark-59 an K success | closed |
| T-45-79 | Denial of Service | Nachzählung gilt als unfertiger Crawl (#25 F1) | mitigate | CrawlAdvanceService Z. 91 nur CRAWL_ACTIVE_LOCK, Marker nur im Crawl-Modus (StorageCrawlJob Z. 296); Live-Probe F1 | closed |
| T-45-80 | Tampering | Abgleich neben unfertiger Crawl-Scheibe | mitigate | Marker unter dem Slice-Lock, Freigabe im verschachtelten finally (StorageCrawlJob Z. 326-334) | closed |
| T-45-81 | Denial of Service | Marker eines abgestürzten Prozesses; Locking-Hinweis | accept | TTL des Slice-Locks begrenzt die Wartezeit; Hinweis der Admin-Seite nach l1, class_exists wie Factory.php (I-45-25-01, M37 bis M40) (R-45-06) | closed |
| T-45-82 | Denial of Service | Nachzählung belegt den Slice-Lock | mitigate | RECOUNT_MIN_INTERVAL_SECONDS 6 h (SettingsService Z. 322, 398 an K), Regelzweig r1; Version001500 vergisst scan_recounted_at (m1) | closed |
| T-45-83 | Tampering | Rückhalt öffnet neben einem Crawl | mitigate | reconcile.py prüft crawling bei Rundenstart und je Scheibe; Live-Probe F2 | closed |
| T-45-84 | Denial of Service | Rückhalt-Zyklus auf einer 4-GB-Box | accept | BACKSTOP_FACTOR 2 (reconcile.py Z. 220 an K), Owner z1; Live-Probe mit 9000 Seiten OCR-Rückstand (R-45-07) | closed |
| T-45-85 | Information Disclosure | Warnzeile oder Statusfeld tragen Pfade oder Namen | mitigate | reconcileHeldSince `int \| None` (status.py Z. 471, 846 an K), Warnzeile nur Stunden, Zähler, Marke | closed |
| T-45-86 | Tampering | ungültiger oder künftiger Zeitpunkt im Zustandsspeicher | mitigate | ungültig oder Zukunft wird als jetzt neu geschrieben; gelöscht nur nach ROUND_WALKED; test_reconcile in Python gates an K | closed |
| T-45-87 | Repudiation | Live-Probe #25 verkürzt als Standard ausgegeben | mitigate | Zeilen `Verkürzt per Umgebung:` (mit Standardwerten) und `Lock per Skript gehalten:` in 45-AUDIT.md `### Live-Proben #25` | closed |
| T-45-88 | Denial of Service | Backstop schreibt eine gesunde Datei fälschlich ab | mitigate | nur gleiche Bytes (content_hash), nur erfolgreiche Übergaben, OCR_HANDOVER_LIMIT 3 (worker/poller.py Z. 174 an K); M53, M54, M56 rot (45-27) | closed |
| T-45-89 | Information Disclosure | warning-Zeile des Backstops | mitigate | BACKSTOP_LINE (poller.py Z. 181 an K) nur `%d` und file id; Namens-Gate im Test | closed |
| T-45-90 | Repudiation | requeued-Zahl meldet Spurwechsel, die nicht stattfanden | mitigate | QueueMapper `$dirtyBefore` vor den Updates (Z. 636, 677 an K); M50, M51 rot | closed |
| T-45-91 | Tampering | Deckungsgrad zählt abgeschriebene Datei doppelt | mitigate | judged schließt failed/repeatedly_stuck aus, coverage_truth.sh zieht nach; M58 rot (45-27) | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Nach dem Release nachzuprüfen

Gegenstand existiert vor dem Tag nicht; nicht als offen gezählt. Nachprüfung im Nachtrag von 45-15 (Release-Threats) in diesem Dokument.

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-45-47 | Tampering | Tag auf falschem Kopf | mitigate | Vorprüfung, verify Tag-Commit gleich Tag-Kopf K (45-14) | nach dem Release nachzuprüfen (45-15) |
| T-45-48 | Spoofing | unsignierte Pakete im Store | mitigate | Verified OK, SHA-256, Fremdinstallation aus den Release-Assets (45-14) | nach dem Release nachzuprüfen (45-15) |
| T-45-49 | Information Disclosure | Store-Token | mitigate | nur im Environment app-store, Dispatch nur nach Freigabe (45-14) | nach dem Release nachzuprüfen (45-15) |
| T-45-50 | Repudiation | Veröffentlichung ohne Owner | mitigate | getrennte Freigabezeilen Tag und Store (45-14) | nach dem Release nachzuprüfen (45-15) |
| T-45-51 | Denial of Service | Store-API-Sperre durch zu viele Abfragen | mitigate | B9, höchstens alle 10 Minuten, höchstens drei Versuche (45-14) | nach dem Release nachzuprüfen (45-15) |
| T-45-52 | Repudiation | Kommentar ohne Owner-Freigabe | mitigate | B2, je Thread eigene Freigabezeile (45-15) | nach dem Release nachzuprüfen (45-15) |
| T-45-53 | Information Disclosure | interne Details im Kommentar | mitigate | Entwürfe nur mit Release- und Doku-Links, Owner liest gegen (45-15) | nach dem Release nachzuprüfen (45-15) |
| T-45-54 | Spoofing | ungewollte Benachrichtigung durch @name | mitigate | @ nur nach ausdrücklicher Owner-Entscheidung (45-15) | nach dem Release nachzuprüfen (45-15) |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-45-01 | T-45-18 | Client-Vorprüfung ist nur Komfort, der Server entscheidet in validate() | Plan 45-04, Owner-Planabnahme | 2026-11-22 |
| R-45-02 | T-45-22 | manipulierte IDs nur durch Admins, Form geprüft, Wirkung nur auf Admin-Mounts | Plan 45-05, Owner-Planabnahme | 2026-11-22 |
| R-45-03 | T-45-69 | einmalige Erneuerung: höchstens drei Anfragen je betroffener Datei, einmal je Datenbank | Plan 45-18, Owner-Planabnahme | 2026-11-22 |
| R-45-04 | T-45-70 | 403 mit gefälschtem Kopf nur aus dem eigenen Gateway über AppAPI möglich, Folge nur ein anderes Urteil | Plan 45-18, Owner-Planabnahme | 2026-11-22 |
| R-45-05 | T-45-74 | Prüfspur nennt für Secure-View-Dateien die lesende Person (CriticalActionPerformedEvent mit fileid, Pfad, uid nur nach einem Lesen in actAs); dieselbe Datenart, die admin_audit für jedes Lesen schreibt; in docs/privacy.md genannt | Owner, `Entscheid Befund Prüfspur 45-20` (a4, "Soviel Aufwand wie nötig Hauptsache beste Qualität") | 2026-11-23 |
| R-45-06 | T-45-81 | Marker eines abgestürzten Prozesses hält den Abgleich höchstens bis zum Ablauf der TTL des Slice-Locks | Plan 45-23, Owner `Entscheid Locking 45-23` (l1) | 2026-11-22 |
| R-45-07 | T-45-84 | Rückhalt-Zyklus höchstens einmal je zwei Intervalle mit Pausen; Owner wollte den Fix in 1.7.0 mit dieser Last | Owner `Entscheid Rückhalt-Weg 45-23` (z1) | 2026-11-22 |

---

## Unregistered Flags

Keine. Alle `## Threat Flags` in 45-04, 45-05, 45-09, 45-17 bis 45-20 und 45-22 bis 45-27 melden keine neue Angriffsfläche oder verweisen auf registrierte IDs; der einzige Flag (45-20, audit-trail in GatewayReader.php) gehört zu T-45-74 (R-45-05).

Hinweise ohne Threat-Bezug, nach 1.7.0: I-45-12-01 (LOW, CI-Robustheit, HaRP Schritt 2b wartet nicht auf die leere Queue), I-45-10-07 (LOW, CI-Robustheit, Wörterbuch-Download ohne Zeitlimit), F3 I-45-23-01 (wartet auf Logs des Melders).

---

## Security Audit Trail

### Security Audit 2026-11-26

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-26 | 83 vor dem Tag (T-45-01 bis T-45-46, T-45-55 bis T-45-91) + 8 nach dem Release | 83 | 0 | Executor 45-16 nach secure-phase.md (ohne eigenen Auditor-Agenten, Proben selbst am Kandidaten) |

- Zählung vor dem Tag: 83 IDs; 76 mitigate, 7 accept (T-45-18, T-45-22, T-45-69, T-45-70, T-45-74, T-45-81, T-45-84), 0 transfer. T-45-47 bis T-45-54 nach dem Release.
- ASVS-Level 1, block_on: high; kein Befund ab LOW offen (alle LOW und MEDIUM aus 45-09, 45-10, 45-20, 45-21 behoben, 45-AUDIT.md).
- Proben am Kandidaten K: 45-AUDIT.md `## Nachtrag Threats vor dem Tag` (P1 bis P9), unabhängig vom Muster der Umsetzung, mit Positivkontrolle (P3).
- Implementierungsdateien nicht verändert.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-26 durch den Executor; Owner-Bestätigung als Zeile `Abschluss Security 45-16` in 45-FREIGABEN.md steht aus (Koordinator).
