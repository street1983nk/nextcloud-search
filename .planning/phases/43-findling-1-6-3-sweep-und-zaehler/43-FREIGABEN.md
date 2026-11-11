# Phase 43: Owner-Freigaben für Push, Merge, Tag, Dispatch, Kommentar

Je Gegenstand genau eine Maschinenzeile (Bindende Vorgaben in 43-02-PLAN.md). Kanal: Claude Code Terminal, über den Koordinator.

Owner-Vorgabe vor dem Push: "Erst fixen, dann pushen (Empfohlen)", also zuerst der Befund G1 aus dem 43-07-Checkpoint (gespeicherte Ruhe des Prüflaufs überlebt einen Neustart) als fix(43-16).

Freigabe Push 43-07: "Ja, auf main pushen" (2026-11-07 14:29, Claude Code Terminal) Entscheid: ja
Freigabe Dispatch 43-07: "Ja, starten" (2026-11-07 14:29, Claude Code Terminal) Entscheid: ja

Umfang: genau ein Push des entstandenen HEAD (43-01 bis 43-07 plus Fix) auf origin main, genau ein Dispatch von "Coverage end to end" nach grünen Push-Läufen. Kein Tag, kein Release, kein Store. Jeder weitere Push oder Dispatch braucht eine neue Freigabe.

Freigabe Push 43-07 Fix 1: "Ja, pushen und dann E2E" (2026-11-07 15:00, Claude Code Terminal) Entscheid: ja

Umfang Fix 1: genau ein Push von e65e34c3 (20fafb7e und e65e34c3: Fixture-Pfad im phpunit-Job, Controller-Double, sechs geprüfte Routen); derselbe Wortlaut deckt zusammen mit "Ja, starten" genau einen Dispatch von "Coverage end to end", wenn alle acht Push-Workflows grün sind.

Vollzug: Push 53090f80 (Freigabe Push 43-07), Push e65e34c3 (Freigabe Push 43-07 Fix 1), alle acht Push-Workflows auf e65e34c3 grün; genau ein Dispatch "Coverage end to end" auf main, Lauf 42381671975 (gedeckt durch Freigabe Dispatch 43-07 und Fix 1), rot wegen des Harness (Speicher-Suche local::%), Korrektur c2037b29 lokal, nicht gepusht.

Freigabe Push und Dispatch 43-07 Fix 2: "Ja, pushen und E2E (Empfohlen)" (2026-11-07, Claude Code Terminal) Entscheid: ja

Umfang Fix 2: genau ein Push von 22f6f441, c2037b29, 5c30b0f9 plus dieser Freigabezeile auf origin main, genau ein Dispatch von "Coverage end to end", wenn alle Push-Workflows grün sind.

Vollzug Fix 2: Push e038ee13, die vier ausgelösten Push-Workflows grün; genau ein Dispatch "Coverage end to end", Lauf 42394655350, rot in allen vier Varianten: "the queue did not drain within 1500 s", jeder Abruf des Content-Gateways endet im ReadTimeout, danach auch Pause-Wunsch und Queue (php -S antwortet nicht mehr). Ursache offen.

Freigabe Diagnose-Patch, Push und Dispatch 43-07 Fix 3: "Go" (2026-11-07, Claude Code Terminal) Entscheid: ja

Umfang Fix 3: Diagnose im Harness (Gateway-Probe Home und SMB vor dem Crawl, Abbruch nach drei Gateway-Ausfällen mit Prozessliste, Log von php -S in eine Datei), genau ein Push auf origin main, genau ein Dispatch von "Coverage end to end", wenn die Push-Workflows grün sind.

Vollzug Fix 3: Push 62d88c9c, sechs Push-Workflows grün; genau ein Dispatch "Coverage end to end", Lauf 42401892996, rot in allen vier Varianten, jetzt nach rund 6 Minuten statt 25. Gateway-Proben vor dem Crawl grün (Home und SMB je 200 in unter 0,13 s). Befund: im ersten Indexierungsdurchgang liefert der Gateway die Dateien 87 bis 90 für bob, die nächste Dateianfrage wird angenommen und nie beendet; je Durchgang bleibt ein PHP-Worker mit zwei smbclient-Prozessen (ohne smbclient-Erweiterung, icewind/smb mit Binary) hängen.

Freigabe Diagnose, Push und Dispatch 43-07 Fix 4: "Ok" (2026-11-07, Claude Code Terminal) Entscheid: ja

Umfang Fix 4: Gateway-Proben für bob auf gesperrt-bob.txt und alice auf gesperrt-alle.txt vor dem Crawl (je 60 s, beide laufen, danach Abbruch mit Bericht bei einem Hänger), Datei-IDs 80 bis 110 mit Pfad im Hang-Bericht; genau ein Push von 9d0fb3bb plus diesem Stand auf origin main, genau ein Dispatch von "Coverage end to end", wenn die Push-Workflows grün sind.

Vollzug Fix 4: Push 1c254392, vier Push-Workflows grün; genau ein Dispatch "Coverage end to end", Lauf 42404849768, rot in allen vier Varianten wie erwartet. Befund belegt: Home- und SMB-Probe 200 in unter 0,17 s, der Gateway-Abruf von gesperrt-bob.txt (Datei 92, bob) und von gesperrt-alle.txt (Datei 68, alice) antwortet in 60 s nicht (http 000), in allen vier Varianten, also auch mit 1.6.2. Ohne smbclient-PHP-Erweiterung liefert icewind/smb Share::read() eine Pipe aus smbclient "get"; bei einer DENY-ACE bleibt sie offen.

Owner-Entscheid DENY-ACE-Hänger (2026-11-07, Claude Code Terminal): "Fix in 1.6.3 (Empfohlen)": Gateway liest SMB-Streams mit Zeitdeckel, Abbruch mit 422, smbclient-Prozess beenden, Datei zählt als unlesbar (D-43-11); TDD, PHPUnit, E2E-Variante mit smbclient-PHP-Erweiterung; Push und Dispatch einzeln fragen.
Owner zum Upstream-Bericht: "Bitte keine voreiligen Issues, mache eine reichere [Recherche] vorher und dann können wir darüber sprechen." Kein Issue, kein Kommentar ohne neue Freigabe.

Owner-Entscheide zu 43-17 (2026-11-07, Claude Code Terminal):
Entscheid F1 43-17: B, in 43-17 selbst: "Als 'nicht lesbar' zählen (Empfohlen)": vom Gateway mit 422 abgelehnte Dateien zählen in "nicht lesbar", nicht als Fehler; der Dispatch wartet darauf.
Entscheid F2 43-17: "Ja, wenn RAM reicht (Empfohlen)": PHPUnit lokal per scripts/dev/phpunit_docker.sh nur bei mindestens 4 GB freiem RAM, sonst seriell abwarten.
Entscheid F3 43-17: "Ja (Empfohlen)": v1.6.2 und upgrade nativ (php-smbclient), gate-crawl und gate-queue Wrapped, gate-queue zusätzlich nativ.
Entscheid F4 43-17: "Ja, in 43-17 (Empfohlen)": 422 zählt nicht zur Ausfall-Schwelle GATEWAY_SAME_STATUS_OUTAGE_AFTER, mit Test.

Freigabe Push 43-18: "Go bitte sorgfältig das Ziel bleibt das Beste für die User zu liefern" (2026-11-07 22:34, Claude Code Terminal) Entscheid: ja
Freigabe Dispatch 43-18: "Go bitte sorgfältig das Ziel bleibt das Beste für die User zu liefern" (2026-11-07 22:34, Claude Code Terminal) Entscheid: ja

Umfang 43-18: genau ein Push des entstandenen HEAD (Commits von 43-17 und 43-18 samt Planung, fdfc573a bis 296d428a plus diese Zeilen) auf origin main, genau ein Dispatch von "Coverage end to end" nach grünen Push-Workflows. Kein Tag, kein Release, kein Store, kein Kommentar.

Vollzug 43-18: Push 84a5ce84, alle acht Push-Workflows grün (PHPUnit 1135 Tests OK); genau ein Dispatch "Coverage end to end", Lauf 42418778026, rot in allen fünf Beinen. Kern-Fix belegt: gesperrte Dateien 422 in rund 0,1 s in Wrapped und nativ, leer.txt 200 mit 0 Bytes, kein smbclient-Prozess bleibt hängen; gate-queue/native: Zähler, Nenner, notReadable, Urteile skipped/unreadable gleich der Wahrheit. Abweichungen: (1) Wrapped, gross.bin gedrosselt: 422 nach 30,2 s (Frist für erste Daten), vermutlich große SMB-Leseblöcke von smbclient bei 100 KB/s, Produktrelevanz offen; (2) 1.6.2-Companion nativ: leer.txt 200 statt erwarteter 400, Harness-Erwartung falsch; (3) Suchgegenprobe 15 statt 23 Wörter, fehlende Namen nicht protokolliert.

Freigabe Push 43-18 Fix 1: "J" (2026-11-07 23:57, Claude Code Terminal) Entscheid: ja
Freigabe Dispatch 43-18 Fix 1: "J" (2026-11-07 23:57, Claude Code Terminal) Entscheid: ja

Umfang Fix 1: genau ein Push von 555dae83 bis ad2aba47 plus diesen Zeilen (Fristen 80 s, Harness-Befunde aus Lauf 42418778026), genau ein Dispatch von "Coverage end to end" nach grünen Push-Workflows.

Vollzug 43-18 Fix 1: Push 71933631, acht Push-Workflows grün; genau ein Dispatch, Lauf 42425348629, rot in allen fünf Beinen. Befunde: (1) Wrapped gross.bin bei 200 KB/s: 422 nach 60 s trotz 80-s-Frist; Ursache icewind/smb Options::$timeout = 20 (smbclient -t 20 je Operation, Server 3rdparty/icewind/smb/src/Options.php:14), ein 8-MiB-Block braucht bei 200 KB/s rund 42 s; Admin-Stellschraube Speicher-Option timeout (apps/files_external/lib/Lib/Storage/SMB.php:103-106). (2) upgrade: occ upgrade bricht ab, "The files of the app viewer were not correctly replaced" (Harness, viewer fehlt im Server-Checkout). (3) Suchgegenprobe 15/23 in gate-queue/native und v1.6.2: aaron bekommt für jedes Suchwort dieselben drei Treffer projekt-1..3, alle Suchwörter beginnen mit "zq"; Ursache offen (Präfix/Fuzzy-Treffer vermutet).

Freigabe Push 43-18 Fix 2: "Ok" (2026-11-08, Claude Code Terminal) Entscheid: ja
Freigabe Dispatch 43-18 Fix 2: "Ok" (2026-11-08, Claude Code Terminal) Entscheid: ja

Umfang Fix 2: genau ein Push von ef42dc3f bis c11f749a plus diesen Zeilen (ein Wort je Datei, Suche mit limit 25, viewer im Server-Checkout, gross.bin innerhalb des smbclient-Timeouts plus Nachweis mit timeout=120), genau ein Dispatch von "Coverage end to end" nach grünen Push-Workflows. Kein Tag, kein Release, kein Store, kein Kommentar.

Freigabe Push 43-18 Fix 3: "Ja , aber bitte Check die Lage nochmal , es sollte ein einfacher Fix sein und wir sind schon Wochen damit beschäftigt" (2026-11-08, Claude Code Terminal) Entscheid: ja
Freigabe Dispatch 43-18 Fix 3: "Ja , aber bitte Check die Lage nochmal , es sollte ein einfacher Fix sein und wir sind schon Wochen damit beschäftigt" (2026-11-08, Claude Code Terminal) Entscheid: ja

Umfang Fix 3: genau ein Push von 7e658fc0 bis 24093fc6 plus diesen Zeilen (Soll der Suchgegenprobe aus eingepflanzten Wörtern der Wahrheit, Catch-up von 1.5 unter 1.6.2 abwarten), genau ein Dispatch von "Coverage end to end" nach grünen gestarteten Push-Workflows. Kein Tag, kein Release, kein Store, kein Kommentar.

Vollzug 43-18 Fix 3: Push fa0ab5e7, vier gestartete Push-Workflows grün; genau ein Dispatch, Lauf 42482017221: gate-crawl/wrapped, gate-queue/wrapped, gate-queue/native, v1.6.2/native grün; upgrade/native rot vor dem Crawl ("Error: in prepare, database is locked (5)" beim Lesen der Nextcloud-SQLite, gateway probe locked-for-all: no file id), Harness-Zufall. Wahrheitszeile ohne Wort belegt: home::admin files/welcome.txt.

Freigabe Rerun 43-18 Fix 3 upgrade: "Ja" (2026-11-08, Claude Code Terminal) Entscheid: ja
Umfang: genau ein gh run rerun 42482017221 --failed, ohne Code-Änderung.

Entscheid 43-20: "Ok" (2026-11-08, Claude Code Terminal): einmaliger neuer Wiederholungszähler für Weigerungszeilen beim ersten Start von 1.6.3.

Freigabe Push 43-20: "Go" (2026-11-08, Claude Code Terminal) Entscheid: ja
Freigabe Dispatch 43-20: "Go" (2026-11-08, Claude Code Terminal) Entscheid: ja

Umfang 43-20: genau ein Push von 06dd3c12 bis 054ab685 plus diesen Zeilen (Vollzug Fix 3, einmaliger neuer Wiederholungszähler für Weigerungszeilen von 1.6.2, sqlite3-Wartezeit im Harness), genau ein Dispatch von "Coverage end to end" nach grünen gestarteten Push-Workflows. Kein Tag, kein Release, kein Store, kein Kommentar.

Freigabe Push 43-08: "Ja, Push + 1 Dispatch" (2026-11-08 20:13, Claude Code Terminal) Entscheid: ja
Freigabe Dispatch 43-08: "Ja, Push + 1 Dispatch" (2026-11-08 20:13, Claude Code Terminal) Entscheid: ja

Umfang 43-08: genau ein Push der acht lokalen Commits 11127790..684ded20 plus dieser Zeilen (43-07-Doku und Summary, 43-19 Abhilfetexte, 43-08 Bump 1.6.3, Upgrade-Strecke, STATE), genau ein Dispatch von "Coverage end to end" nach gruenen gestarteten Push-Workflows auf dem neuen Kopf. Kein Tag, kein Release, kein Store, kein Kommentar. CHANGELOG [1.6.3] lag dem Owner woertlich vor (inkl. fuenfter Known-limitations-Satz aus 43-18-SUMMARY).

Freigabe Push 43-09: "Ja, Push + 1 Dispatch" (2026-11-08 22:01, Claude Code Terminal) Entscheid: ja
Freigabe Dispatch 43-09: "Ja, Push + 1 Dispatch" (2026-11-08 22:01, Claude Code Terminal) Entscheid: ja

Umfang 43-09: genau ein Push der sechs lokalen Commits (43-08-Nachtraege 9f6ddc79/800d58e4/12f00467, Audit-Fix 37b518d6, Audit e8c052e3, Summary 757127e6) plus dieser Zeilen, genau ein Dispatch von "Coverage end to end" nach gruenen gestarteten Push-Workflows. Kein Tag, kein Release, kein Store, kein Kommentar. Audit-Ergebnis lag dem Owner vor (0 CRIT/HIGH/MEDIUM offen, F-43A-01 MEDIUM gefixt, 2 LOW akzeptiert).

Freigabe Push 43-10 main: "Ja, alle vier" (2026-11-08 23:31, Claude Code Terminal) Entscheid: ja
Freigabe Push 43-10 rc: "Ja, alle vier" (2026-11-08 23:31, Claude Code Terminal) Entscheid: ja
Freigabe Dispatch 43-10 release: "Ja, alle vier" (2026-11-08 23:31, Claude Code Terminal) Entscheid: ja
Freigabe Dispatch 43-10 proof: "Ja, alle vier" (2026-11-08 23:31, Claude Code Terminal) Entscheid: ja

Umfang 43-10: genau ein Push auf main (Proof-Workflow, Skript, TESTBUILD, SUMMARY, 43-09-Nachtraege, diese Zeilen), genau ein Push des Branches rc/1.6.3-rc.1 (nie mergen), genau ein Dispatch release.yml auf rc/1.6.3-rc.1 mit create_release=false (Archiv nur als Workflow-Artefakt, 30 Tage), genau ein Dispatch rc-version-proof.yml. Kein Tag, kein oeffentliches Release, kein Store, kein Kommentar.

Freigabe Push 43-10 Proof-Fix: "Ja, Push + Proof-Retry" (2026-11-09 00:59, Claude Code Terminal) Entscheid: ja
Freigabe Dispatch 43-10 proof Wiederholung: "Ja, Push + Proof-Retry" (2026-11-09 00:59, Claude Code Terminal) Entscheid: ja

Umfang: genau ein Push der Skript-Fixes (SIGPIPE, Heartbeat 300 s) plus dieser Zeilen auf main, genau EIN erneuter Dispatch rc-version-proof.yml mit denselben Parametern (archive_run_id 42537119924, image_sha 655fe197...). Kein weiterer Archiv-Lauf, kein Tag, kein Store.

Freigabe Push 43-10 Sonden-Fix: "Ja, Push + Retry 2" (2026-11-09 03:23, Claude Code Terminal) Entscheid: ja
Freigabe Dispatch 43-10 proof Wiederholung 2: "Ja, Push + Retry 2" (2026-11-09 03:23, Claude Code Terminal) Entscheid: ja

Umfang: genau ein Push (Heartbeat-Sonde liest Container-Log, gh download --dir) plus dieser Zeilen, genau EIN erneuter Proof-Dispatch mit denselben Parametern (Archiv 42537119924). Kein Tag, kein Store.

Freigabe Push 43-10 a6-Korrektur: "Ja, Push + Retry 3" (2026-11-09 05:52, Claude Code Terminal) Entscheid: ja
Freigabe Dispatch 43-10 proof Wiederholung 3: "Ja, Push + Retry 3" (2026-11-09 05:52, Claude Code Terminal) Entscheid: ja

Umfang: genau ein Push (a6 shipped.json-Korrektur nach deploy-harp-Muster) plus dieser Zeilen, genau EIN erneuter Proof-Dispatch (Archiv 42537119924). A5 war im Lauf 42551978920 ok. Kein Tag, kein Store.

Freigabe Kommentar 43-11: "Ja, so posten" (2026-11-09 06:23, Claude Code Terminal) Entscheid: ja
Umfang: genau ein Kommentar in #25 (gekuerzte Fassung, vom Owner zeichengenau gesehen), kein Schliessen, kein weiterer Kommentar.

Freigabe Push 43-12: "Wie empfohlen" und "Wie ja" (2026-11-09 07:05, Claude Code Terminal) Entscheid: ja
Umfang: genau ein Push auf main nach git pull --rebase: CHANGELOG-Satz D2, Gesamttext v1.6.3 in docs/store-listing.md, Gate scan_full_text_1_6_3, 43-ABNAHME.md, diese Zeilen, dazu die 5 lokalen Doku-Commits davor. Kein Tag, kein Dispatch, kein Store, kein Kommentar.

Freigabe Kommentar 43-11 Rückmeldung: "Ja go" (2026-11-09 09:25, Claude Code Terminal) Entscheid: ja
Umfang: genau ein kurzer Kommentar in #25 (Wortlaut vom Owner gesehen), gepostet: https://github.com/street1983nk/nextcloud-search/issues/25#issuecomment-6735423819. Kein Schließen.
Freigabe Planung 43-21: "Ja go" (2026-11-09 09:25, Claude Code Terminal) Entscheid: ja
Umfang: Zusatzplan vor dem Store für die Unterwurzeln derselben Freigabe (D-43-15) und die Faltung der Schreibweise von Host und Freigabe; nur Planung, Ausführung und jeder Push brauchen eigene Freigaben.

Freigabe Entscheid 43-21 OE-1: "Wie empfohlen" (2026-11-09 10:36, Claude Code Terminal) Entscheid: a
Freigabe Entscheid 43-21 OE-2: "Wie empfohlen" (2026-11-09 10:36, Claude Code Terminal) Entscheid: a
Freigabe Entscheid 43-21 OE-3: "Wie empfohlen" (2026-11-09 10:36, Claude Code Terminal) Entscheid: a
Freigabe Entscheid 43-21 OE-4: "Wie empfohlen" (2026-11-09 10:36, Claude Code Terminal) Entscheid: a
Freigabe Entscheid 43-21 OE-5: "Wie empfohlen" (2026-11-09 10:36, Claude Code Terminal) Entscheid: a
Freigabe Entscheid 43-21 OE-6: "Wie empfohlen" (2026-11-09 10:36, Claude Code Terminal) Entscheid: a
Freigabe Entscheid 43-21 OE-7: "Wie empfohlen" (2026-11-09 10:36, Claude Code Terminal) Entscheid: a
Freigabe Entscheid 43-21 OE-8: "Wie empfohlen" (2026-11-09 10:36, Claude Code Terminal) Entscheid: a
Umfang: nur Entscheide für 43-21 bis 43-29, kein Push, kein Dispatch, kein Kommentar.

## Freigabe 09.11.2026 (Abend): Antwort an mbozem, rc.2 gestrichen

Owner-Wort: "Rc2 Streichen und antworten und Mittwoch geht es weiter".

Umfang: genau ein Kommentar auf #25 (Wortlaut lag dem Owner im Chat vor, gepostet 09.11.2026 abends), 43-28 (Testbuild rc.2) gestrichen, Versionsnachweis kuenftig rc.1 -> 1.6.3 in 43-26/43-27. Kein Push, kein Tag, kein Store. Weiter am Mittwoch 11.11. mit 43-23 (PHPUnit bei RAM >= 4 GB).

## Freigabe 11.11.2026: Push von main und Dispatch des Abnahmetests (43-26)

Frage im Wortlaut des Plans mit den Optionen a, b, nein gestellt; der Owner antwortete "Go für Findling". Gelesen als Option a (Push und Dispatch), die Changelog-Sätze aus 43-23 stehen damit vor der Textrunde 43-12 öffentlich auf main.

Freigabe Push 43-26: "Go für Findling" (2026-11-11 09:29, Claude Code Terminal) Entscheid: ja
Freigabe Dispatch 43-26: "Go für Findling" (2026-11-11 09:29, Claude Code Terminal) Entscheid: ja
Umfang: genau ein Push auf main nach git pull --rebase mit den lokalen Commits von 43-21 bis 43-26 Task 1, dem Reset der Dokumentschlüssel in Bändern (53373888, c93a6f1e) und diesen Zeilen; genau ein Dispatch von coverage-e2e.yml auf dem gepushten Kopf. Kein Tag, kein Release, kein Store, kein Kommentar. Jede Wiederholung nach einem roten Bein braucht neue Zeilen.

## Freigabe 11.11.2026: Push und Dispatch von Fix 1 (43-26)

Nach dem roten Lauf 42991291089 lag dem Owner im Chat der Befund vor (drei Ursachen, Fix 1 lokal in sechs Commits, Restrisiken des nächsten Laufs). Frage: "Darf ich main mit den sechs Commits von Fix 1 pushen und danach coverage-e2e.yml einmal auf dem neuen Kopf dispatchen?" Antwort des Owners: "Go".

Freigabe Push 43-26 Fix1: "Go" (2026-11-11 12:28, Claude Code Terminal) Entscheid: ja
Freigabe Dispatch 43-26 Fix1: "Go" (2026-11-11 12:28, Claude Code Terminal) Entscheid: ja
Umfang: genau ein Push auf main nach git pull --rebase mit den Commits 07eadd03, e02ff71f, a311b827, f4375578, 76be7820, 893af895 und diesen Zeilen; genau ein Dispatch von coverage-e2e.yml auf dem gepushten Kopf. Kein Tag, kein Release, kein Store, kein Kommentar. Jede weitere Wiederholung braucht neue Zeilen.

## Freigabe 11.11.2026 (Abend): Push des Audit-Nachtrags und der Fix-Runde (43-27)

Dem Owner lag im Chat vor: Audit-Nachtrag ohne CRITICAL, HIGH, MEDIUM; die drei LOW-Befunde F-43B-01 bis -03 lokal per TDD behoben (PHPUnit 1200 Tests grün, Python-Module grün); zwei Hinweise: der Schlüsselinhalt für gehashte Speicher ohne Identität ändert sich innerhalb von Format 2 (unveröffentlicht), und der neue Changelog-Satz zu F-43B-02 ist ein Entwurf für die Textrunde 43-12. Antwort des Owners: "Push erstmal dann mach ich clear".

Freigabe Push 43-27: "Push erstmal dann mach ich clear" (2026-11-11 19:03, Claude Code Terminal) Entscheid: ja
Umfang: Push von main nach git pull --rebase, zuerst genau bis 9bf7dddf (letzter Commit außerhalb von .planning), nach grünen Workflows auf diesem Kopf die Planungs-Commits danach (4ae8c833, 6d6f7740, diese Zeilen). Kein Dispatch von coverage-e2e.yml: dafür liegt noch KEINE Freigabe vor, die Zeile "Freigabe Dispatch 43-27" fehlt bewusst. Kein Tag, kein Release, kein Store, kein Kommentar.

## Freigabe 11.11.2026 (Abend): Dispatch von coverage-e2e.yml nach der Fix-Runde (43-27)

Dem Owner lag im Chat vor: fünf von acht Workflows auf 9bf7dddf grün, drei liefen noch; nach Grün folgen die Planungs-Commits aus der Freigabe Push 43-27. Frage: "Darf ich danach EINEN Dispatch von coverage-e2e.yml auf main starten (7 Beine, etwa 45 Minuten)? Der Code ist zwischen A und dem späteren Kopf identisch, nur Planungsdateien kommen dazu." Antwort des Owners: "Ja ok".

Freigabe Dispatch 43-27: "Ja ok" (2026-11-11 19:19, Claude Code Terminal) Entscheid: ja
Umfang: genau ein Dispatch von coverage-e2e.yml auf main, nachdem alle Workflows auf 9bf7dddf grün sind und die Planungs-Commits gepusht wurden (kein Code-Unterschied zu 9bf7dddf). Kein Tag, kein Release, kein Store, kein Kommentar. Jede Wiederholung braucht eine neue Zeile.

## Freigabe 11.11.2026 (späterer Abend): Push und Dispatch nach Fix 2 (43-27)

Dem Owner lag im Chat vor: der Lauf 43079756645 war in einem von sieben Beinen rot (gate-queue / native, ein StorageCrawlJob starb an "database is locked", zwei Dateien fehlten); nach seinem Entscheid "A" der Produkt-Fix lokal (RED ae44f61d, GREEN 2dacf753, Doku 5a37961a), Gegenprobe ohne Fix rot, volle PHPUnit-Suite 1205 Tests grün, Python-Gates grün; Befund F-43B-05 als LOW eingestuft, Changelog-Satz als Entwurf für die Textrunde 43-12. Frage: "Darf ich main pushen (erst genau bis 2dacf753, nach grünen Workflows den Doku-Commit und die Freigabe-Zeilen), und danach EINEN neuen Lauf von coverage-e2e.yml starten?" Antwort des Owners: "Go".

Freigabe Push 43-27 Fix 2: "Go" (2026-11-11 20:46, Claude Code Terminal) Entscheid: ja
Freigabe Dispatch 43-27 Fix 2: "Go" (2026-11-11 20:46, Claude Code Terminal) Entscheid: ja
Umfang: Push von main nach git pull --rebase, zuerst genau bis 2dacf753 (letzter Commit außerhalb von .planning), nach grünen Workflows auf diesem Kopf die Planungs-Commits danach (5a37961a, diese Zeilen); genau ein Dispatch von coverage-e2e.yml auf main ohne Code-Unterschied zu 2dacf753. Kein Tag, kein Release, kein Store, kein Kommentar. Jede Wiederholung braucht neue Zeilen.
