# Review des Release-Diffs Findling 1.7.0 (Plan 45-21, Task 1)

Stand: 2026-11-23, Kopf d3786c6f (letzter Commit außerhalb .planning: 25980ccd). Diff `v1.6.5..HEAD -- . ':!.planning'`.

## Auftrag

Wörtlich aus 45-21-PLAN.md, Task 1:

> den ganzen Diff v1.6.5..HEAD ohne .planning Datei für Datei lesen und prüfen auf Korrektheit (Rand- und Fehlerpfade, Nebenläufigkeit, Upgrade ab 1.6.2 bis 1.6.5, Verträglichkeit Container/Begleit-App in beiden Update-Reihenfolgen), Sicherheit (Rechte-Grenzen, Enumeration, Injection, XSS, Logs ohne Pfade und Namen, Taint), Performance (Abfragen je Request, Schleifen, Kappungen), Nextcloud-Store- und AppAPI-Vorgaben, Sprache aller nutzersichtbaren Texte in 18 Katalogen (Platzhalter, Umlaute, Vokabel), Doku- und CHANGELOG-Fakten gegen den Code, Testqualität (Verhalten statt Implementierung; jedes neue Gate mit Fehl-Sample). Jede Aussage über Fremdcode (Nextcloud-Kern, AppAPI, richdocuments, files_accesscontrol, groupfolders, files_external) mit Quelle am passenden Tag.

Zusätzlich vom Koordinator: die drei Fixes aus 45-20 (U-45-20-01 aec5edcf/151dca7b, U-45-20-02 f3290689/1d191e7e, U-45-20-03 3550b2b3/c9dc3270/0f6afac7) und der CI-Job watermark-59 (457a0786) voll im Review; die Prüfspur-Zeile (uid und Pfad im audit.log) als Threat-Flag für 45-16 bewerten; I-45-20-05 bewerten; die Randnotiz aus 45-26 (gepflanzten Wert im Treiber zurücklesen) bewerten.

Methode und Unabhängigkeit (B8, T-45-73): Dieser Executor hat keinen der Pläne 45-01 bis 45-26 umgesetzt. Ein eigener Reviewer-Agent ließ sich in dieser Umgebung nicht starten (kein Agent-Werkzeug); deshalb liest der Executor selbst, mit anderer Methode als die Umsetzung: Code am Kopf gegen den Stand v1.6.5, Projektregeln (CLAUDE.md) und Fremdcode an der Quelle, nicht die Tests oder SUMMARYs der Umsetzung. Fremdquellen in diesem Review per raw.githubusercontent.com am 2026-11-23, abgelegt unter `<scratchpad>/src21/`: nextcloud/server stable34 `lib/private/AppConfig.php`, `lib/private/AllConfig.php`, `lib/private/Files/Config/UserMountCache.php`, `lib/private/Files/Config/CachedMountInfo.php`, `apps/admin_audit/lib/Listener/CriticalActionPerformedEventListener.php`, `apps/admin_audit/lib/Actions/Action.php`, `apps/admin_audit/lib/Actions/Files.php`; richdocuments v12.0.2 aus `<scratchpad>/src59/v12.0.2/` (SHA-256 im Audit, `### Quellen am Tag`). Eigene Prüfskripte: `<scratchpad>/l10n_check.py` (Kataloge). Mutation an der Quelle mit Rückbau byte-gleich (SHA-256 vor und nach).

Tiefe: Laufzeitcode (php/lib, php/js, php/templates, php/css, backend/src, Migrationen, scripts/ci des Update-Nachweises) Zeile für Zeile im Diff; Kataloge per eigenem Skript; Workflows, Gate-Skripte und Tests auf Gate-Logik, Fehl-Samples und Ausdrücke in run-Blöcken; Lockdateien und Fixtures auf Herkunft und Zweck; Doku und CHANGELOG gegen den Code als Stichprobe je Aussage zu #25, #45, #59, E3, I-45-26-01.

## Umfang

- `git diff --stat v1.6.5..HEAD -- . ':!.planning'`: 169 Dateien, 21516 Einfügungen, 1296 Löschungen.
- 68 Commits ohne .planning (`git log --oneline v1.6.5..HEAD -- . ':!.planning' | wc -l`), von b3b6f844 (docs security) bis 25980ccd (docs 45-20), darunter die Merges #56 und #57, Phase 44 (Gates), 45-01 bis 45-09 (#45, Audit), 10d9707e (45-10), 45-17 bis 45-20 und 45-22 bis 45-26 (#59, V-45-10-02/03, E3, #25, I-45-23-07, I-45-26-01, I-45-25-01) und die Fixes U-45-20-01 bis -03 samt 457a0786.
- Wirksam beim Nutzer: 24 Dateien php/lib, php/js/admin.js, php/css/admin.css, php/templates/admin.php (search.php nur Formatierung: `git diff -w --ignore-blank-lines` ohne Zeile), 18 Kataloge, 8 Dateien backend/src, beide info.xml, pyproject/uv.lock (Abhängigkeiten).

## Geprüft

- .github/actions/setup-test-nc/action.yml: nur `persist-credentials: false` am checkout, kein Schreibweg mit git im Job.
- .github/dependabot.yml: Gruppen und cooldown für pip, composer (php/tools) und actions; keine Automerge-Regel.
- .github/fixtures/workflow-lint-probe.yml: absichtlich fehlerhafte Probe für zizmor und actionlint, wird nur vom Gate gelesen, nie als Workflow ausgeführt (liegt außerhalb .github/workflows).
- .github/workflows/coverage-e2e.yml: persist-credentials false und Rechte-Block, keine Logikänderung.
- .github/workflows/deploy-harp.yml: Prüfung 14b (Update-Probe) im Store-upgrade-Schritt, Größe unter der Grenze von 512000 Bytes; keine `${{ }}`-Ausdrücke mit Fremdinhalt in run-Blöcken.
- .github/workflows/docker.yml: gepinnte Actions, persist-credentials false; keine Laufzeitwirkung.
- .github/workflows/integration.yml: Jobs M-45-01 (ein externer Speicher aus und zurück) und watermark-59 (richdocuments 11.1.3 per SHA-256 gepinnt, Version nach app:enable geprüft, M1 mit Kontrolle "Wasserzeichen aus", M3 policy_blocked); run-Blöcke nur mit env-Variablen; M3 greift, weil das Backend erst nach dem Abruf auf `is_unchanged` prüft (poller.py Z. 1815), der Abruf das Gateway also wieder erreicht; Job noch nie auf einem Runner gelaufen (R-45-21-08).
- .github/workflows/issue-notify.yml: Rechte-Block, keine Logikänderung.
- .github/workflows/measure.yml: persist-credentials und gepinnte Actions.
- .github/workflows/php.yml: Psalm-Taint gegen OCP 33/34/35 mit eigener SARIF-Zählung, php-cs-fixer dry-run, Job update-in-process mit FROM_TAGS ab v1.3.2, ext-redis für phpunit; Gate-Skripte mit eigener Probe.
- .github/workflows/probe-92d.yml: persist-credentials, keine Logikänderung.
- .github/workflows/python.yml: Gates wie bisher, Caching, Strukturgate-Tests eingebunden.
- .github/workflows/rc-version-proof.yml: Rechte-Block, keine Logikänderung.
- .github/workflows/release.yml: Rechte-Block, keine Logikänderung.
- .github/workflows/resilience.yml: Rechte-Block, keine Logikänderung.
- .github/workflows/scorecard.yml: Rechte und Pins, keine Logikänderung.
- .github/workflows/security.yml: Rechte-Block, keine Logikänderung.
- .github/workflows/smb-acl-measure.yml: persist-credentials false.
- .github/workflows/store-release-delete.yml: Rechte-Block, keine Logikänderung.
- .github/workflows/store-submit.yml: Rechte-Block, keine Logikänderung.
- .github/workflows/workflow-lint.yml: zizmor und actionlint über alle Workflows mit Positivprobe aus der Fixture; Gate schlägt fehl, wenn die Probe nicht anschlägt.
- CHANGELOG.de.md: [1.7.0] deckt sich mit CHANGELOG.md Punkt für Punkt; Wortlaute E3 und I-45-26-01 wie in 45-FREIGABEN.md.
- CHANGELOG.fr.md: dieselben Punkte wie EN und DE, Wortlaute E3 und I-45-26-01 wie freigegeben.
- CHANGELOG.md: jede Aussage gegen den Code: Ausschluss externer Speicher (StorageService::excludedStorageIds), Plätze (admin.js refreshSlots), Ablehnung von Objekt/Lückenliste (SettingsController::listOf), Locale (admin.js locale), Nachzählung 6 h (SettingsService::scanRecountDue), Rückhalt zweimal Intervall nie beim Crawl (reconcile.py run_once, BACKSTOP_FACTOR 2), Leser in Besitzer-Reihenfolge und Prüfspur (GatewayReader), policy_blocked, E3 (SnippetPolicy), Beispielpfad, Update aus 1.3.x (Version001500); stimmt.
- LICENSES/MIT.txt: MIT-Text für REUSE, unverändert übernommen.
- PRODUCT.md: neun Sprachen mit zh_TW; deckt sich mit php/l10n (9 Katalogpaare).
- README.en.md: neue Fakten 1.7.0 (externe Speicher einzeln, Plätze); deckt sich mit dem Code.
- README.fr.md: dieselben Fakten wie EN.
- README.md: dieselben Fakten wie EN, Deutsch zuerst.
- THIRD-PARTY.md: Versionen deckungsgleich mit backend/pyproject.toml (pypdf 7.0.1, pypdfium2 5.15.2, semantic-text-splitter 0.33.2, fastapi 0.162.5).
- backend/appinfo/info.xml: Version und image-tag 1.7.0, Doku-Links auf v1.7.0, Text der Ruheschwelle beschreibt den Rückhalt richtig.
- backend/pyproject.toml: Patch- und Minor-Updates gepinnt, pypdf-Major 7 (#55) im Lock.
- backend/src/findling/api/status.py: reconcileHeldSince nur ab einem Intervall, null bei ausgeschaltetem Abgleich, Zukunft, Unsinn; nur eine Zahl, Satz aus dem Katalog.
- backend/src/findling/extract/errors.py: Reason POLICY_BLOCKED nur unter failed zugelassen.
- backend/src/findling/nc/client.py: GatewayPolicyRefused nur bei 403 und genau Kopfwert `policy`; 403 ohne Kopf bleibt GatewayRefused (AppAPI-403 bleibt Ausfall).
- backend/src/findling/nc/queue.py: Generation 4 mit leerer Tabelle (W3), policy_blocked an Gen 3/2/None als gateway_error; beide Update-Reihenfolgen geprüft gegen docs/formats.md.
- backend/src/findling/store/repo.py: policy_blocked in der Strähne von gateway_error und unreadable, Erneuerung 1.7.0 erst ab Generation 4 (U-45-20-01), eigene Transaktion je Marke, Logzeile nur Zahl und Marke.
- backend/src/findling/worker/catchup.py: nur Docstring zum Rückhalt.
- backend/src/findling/worker/poller.py: Erneuerung vor dem Claim nur bei Generation >= 4, Ausnahme dort landet im allgemeinen Pass-Handler (Z. 1081-1097, Rückgabe der Zeilen, Back-off); policy_blocked zählt nie zum Ausfall; Kommentar-Reihenfolge verrutscht (R-45-21-04).
- backend/src/findling/worker/reconcile.py: _gate ohne Logzeile, Rückhalt nur bei fälligem Lauf und nur hinter der Ruheschwelle, nie bei Crawl oder unlesbarer Warteschlange, Zeitpunkt erst nach ganzem Zyklus gelöscht; warning-Zeile nur Zahlen.
- backend/tests/test_admin_locale.py: Locale-Fälle mit drei Teilen und Rückfall auf root.lang, Verhalten über Node-Ausführung des Skripts.
- backend/tests/test_admin_ui_contract.py: Vertrag Seite/Skript/Katalog, neue Sätze und Platzhalter, Gates mit Fehl-Samples.
- backend/tests/test_exclusion_path_space.py: Platzhalter- und Leerzeichenfälle der Ordnerliste.
- backend/tests/test_extract_errors.py: POLICY_BLOCKED nur unter failed.
- backend/tests/test_gateway_client.py: Kopf und Wert gegen die PHP-Konstanten, 403 ohne Kopf bleibt GatewayRefused.
- backend/tests/test_measurement_scripts.py: Strukturgates für Skripte und Workflows mit Fehl-Samples.
- backend/tests/test_phase31_audit.py: Anpassung an Generation 4.
- backend/tests/test_phase33_audit.py: Objekt-Fall jetzt `empty` (L-45-09-02).
- backend/tests/test_phase34_audit.py: Einzeiler an neuer Regel.
- backend/tests/test_phase36_audit.py: Anpassung an Generation 4 und Fallback-Tabellen.
- backend/tests/test_php_acl_boundary.py: Endfilterung SearchService bleibt; zusätzliche Fälle SnippetPolicy-Variable einmal geschrieben.
- backend/tests/test_php_static_gates.py: neue statische Gates (origin-Muster mit D, watermark-Job, Regeln 8), jeweils mit Fehl-Sample.
- backend/tests/test_php_supply_chain_gates.py: Digests der Lint-Images und Lockdateien der PHP-Werkzeuge mit Fehl-Samples.
- backend/tests/test_poller.py: Erneuerung erst ab Generation 4, policy_blocked ohne Ausfallzählung, Catch-up ab 3.
- backend/tests/test_queue_client.py: Wire-Mapping Generation 4/3/2/None.
- backend/tests/test_reconcile.py: Rückhalt, Crawl, unlesbar, Zeitpunkt, Zukunftsstempel, Freigabe nach ganzem Zyklus.
- backend/tests/test_status_endpoint.py: reconcileHeldSince-Grenzen.
- backend/tests/test_store_metadata.py: Meta-Schlüssel und Strähnen-SQL.
- backend/tests/test_store_repo.py: Erneuerung je Marke, Generationsbedingung, Doppellauf.
- backend/tests/test_unified_search_plugin.py: Zahl an neue Konstante angepasst.
- backend/tests/test_update_in_process_proof.py: Schlüssel, Meldung und FROM_TAG mit Fehl-Samples; kein Rücklesen des gepflanzten Werts geprüft (R-45-21-03).
- backend/tests/test_upgrade_seed_steps.py: Anpassung an neue Migration.
- backend/tests/test_workflow_tag_triggers.py: neuer Workflow ohne Tag-Trigger.
- backend/uv.lock: Lock zu pyproject.toml passend (Versionen gleich, Hashes aus PyPI).
- docs/admin-page.md: neue Abschnitte zu externen Speichern, Plätzen, policy_blocked, Abhilfe "Besitzer zuerst, 20 insgesamt", Dateisperren, Rückhalt; gegen AdminViewService und Kataloge geprüft.
- docs/formats.md: Generation 4 und beide Update-Reihenfolgen; gegen queue.py und poller.py geprüft.
- docs/l10n-catalogues.md: Schlüsselzahl und Ablauf der Katalogpflege, zh_TW ergänzt.
- docs/l10n-chinese.md: Sprachdoku zh_TW (Beitrag #56), Vokabel wie im Katalog.
- docs/l10n-dutch.md: neue Sätze mit Vokabel der Sprachdoku.
- docs/l10n-french.md: neue Sätze, Vokabel wie im Katalog.
- docs/l10n-italian.md: neue Sätze, Vokabel wie im Katalog.
- docs/l10n-portuguese.md: neue Sätze für pt_BR und pt_PT.
- docs/l10n-spanish.md: neue Sätze, Vokabel wie im Katalog.
- docs/language-analyzers.md: Sprachliste um zh_TW der Oberfläche ergänzt, Analyzer unverändert.
- docs/privacy.md: Wasserzeichen-Abschnitt; Prüfspur-Zeile, info-Zeile mit `reader`, Team Folder, keine Umgehung und E3 decken sich mit GatewayReader, GatewayController und SnippetPolicy.
- docs/reconcile.md: zitierte warning-Zeile Z. 497 gleich dem Literal in reconcile.py; Strähne mit policy_blocked.
- docs/security-guidelines-abgleich.md: Abgleich mit den Nextcloud-Sicherheitsrichtlinien, Aussagen mit Codeverweis.
- docs/store-listing.md: Belege 1.6.5, Abschnitt ohne gesperrten Wortstamm.
- docs/testing.md: lokale Rezepte für Psalm-Taint, php-cs und Update-Nachweis.
- php/.php-cs-fixer.dist.php: nextcloud/coding-standard, nur Formatierung.
- php/appinfo/info.xml: Version 1.7.0, Doku-Links v1.7.0; NC-Fenster unverändert.
- php/css/admin.css: Klassen für Liste, Plätze, Warnung; keine Fremdressourcen.
- php/js/admin.js: Locale-Kandidaten mit Intl-Prüfung; neue Texte nur über `text()`/textContent und Funktions-Replacements; Mount-IDs nur als Ziffern; keine innerHTML-Senke neu.
- php/l10n/de.js: gleiches Wörterbuch wie de.json (eigenes Skript), Platzhalter je Schlüssel gleich.
- php/l10n/de.json: 386 Schlüssel, Platzhalter gleich, keine Gedankenstriche, echte Umlaute (Wortliste mit Positivkontrolle: das Skript meldete "Ausschluss" als Treffer, korrekte Schreibung, Wortliste überschießend).
- php/l10n/de_DE.js: gleich de_DE.json.
- php/l10n/de_DE.json: 386 Schlüssel, Platzhalter gleich, keine Gedankenstriche.
- php/l10n/es.js: gleich es.json.
- php/l10n/es.json: 386 Schlüssel, Platzhalter gleich, keine Gedankenstriche.
- php/l10n/fr.js: gleich fr.json.
- php/l10n/fr.json: 386 Schlüssel, Platzhalter gleich, keine Gedankenstriche; Text 5 und Platzhalter wie freigegeben.
- php/l10n/it.js: gleich it.json.
- php/l10n/it.json: 386 Schlüssel, Platzhalter gleich, keine Gedankenstriche.
- php/l10n/nl.js: gleich nl.json.
- php/l10n/nl.json: 386 Schlüssel, Platzhalter gleich, keine Gedankenstriche.
- php/l10n/pt_BR.js: gleich pt_BR.json.
- php/l10n/pt_BR.json: 386 Schlüssel, Platzhalter gleich, keine Gedankenstriche.
- php/l10n/pt_PT.js: gleich pt_PT.json.
- php/l10n/pt_PT.json: 386 Schlüssel, Platzhalter gleich, keine Gedankenstriche.
- php/l10n/zh_TW.js: gleich zh_TW.json, Plural-Form gleich.
- php/l10n/zh_TW.json: 386 Schlüssel (Beitrag #56 plus Nachträge), Platzhalter gleich; jeder im Code genutzte Schlüssel in allen neun Katalogen vorhanden.
- php/lib/BackgroundJobs/ScanRecountJob.php: nur Docblock zum Mindestabstand.
- php/lib/BackgroundJobs/StorageCrawlJob.php: Marker `findling/crawl-active` nur im Crawl-Modus, Freigabe im verschachtelten finally vor dem Slice-Lock; isPassingLockError nur DB-, Redis- und RedisCluster-Ausnahme; Nachfolger vor der Logzeile.
- php/lib/Controller/GatewayController.php: rejectForeignCaller unverändert vorn; not_found gleich wie vorher; policy als 403 mit Kopf, Satz statisch, Kontext id, asked, origin; info-Zeile mit reader (Owner a1).
- php/lib/Controller/ProfileController.php: VERDICTS_GENERATION 4.
- php/lib/Controller/SettingsController.php: excludedExternalMounts optional, Objekt und Lückenliste abgewiesen, Log nur Zähler.
- php/lib/Listener/FileEventListener.php: nur Reihenfolge der use-Zeilen (Formatierung).
- php/lib/Migration/Version001500Date20261012000000.php: keine Klasse der App mehr, Literale, Marke nur von 0 auf Zeit, vergisst scan_recounted_at (m1); Typen passen zu SettingsService (setValueInt/getValueInt).
- php/lib/Migration/Version001700Date20261123000000.php: löscht backend_app_version, Literale, idempotent, kein Containeraufruf.
- php/lib/Service/AdminViewService.php: Grund policy_blocked mit Abhilfe (drei Versuche = GATEWAY_ERROR_RETRIES), neue unreadable-Abhilfe passt zu readingOrder, lockingUnshared und reconcileHeldSince durchgereicht.
- php/lib/Service/CrawlAdvanceService.php: crawling() liest nur CRAWL_ACTIVE_LOCK.
- php/lib/Service/ExclusionService.php: neuer Code wildcard nur für neue Einträge, alte bleiben in Kraft.
- php/lib/Service/ExternalMountService.php: nur Admin-Mounts (type 1), parametrisierte Abfrage, Backend-Name aus dem Katalog von files_external, duplicate nur nach Einhängepunkt; Liste ohne Obergrenze (R-45-21-10).
- php/lib/Service/FileStateService.php: policy_blocked in beiden Listen.
- php/lib/Service/GatewayReader.php: Erkennung nur bei Klasse, Meldung und erstem Frame; zweites Öffnen in actAs; mit Besitzer genau einer, ohne Besitzer höchstens 20; jede andere ForbiddenException policy; Ereignis nur nach einem Öffnen in actAs; Docblock widerspricht dem Verhalten (R-45-21-01).
- php/lib/Service/LockingCheckService.php: nur APCu und ArrayCache, class_exists auf dem Rohwert nach dem Namensvergleich; DI-Naht mit Closure-Default wie bestehendes Muster.
- php/lib/Service/ProbeService.php: zwei Leerzeilen (Formatierung).
- php/lib/Service/QueueService.php: Liste und Reihenfolge nach ReaderCandidates verschoben, Verhalten gleich außer Besitzer zuerst.
- php/lib/Service/ReaderCandidates.php: Besitzer nur über Home-Mount `/<uid>/` mit Home-Provider, im selben Durchlauf, Kappung 500 und 20 bleiben; warning-Text "queued file" auch auf dem Gateway-Weg (R-45-21-09).
- php/lib/Service/SearchOutcome.php: nur Docblock.
- php/lib/Service/SearchService.php: zwei Hunks, Konstruktor-Parameter SnippetPolicy und der Block vor exApp->snippets; Endfilterung unberührt.
- php/lib/Service/SettingsService.php: Liste der Mounts defensiv gelesen und gekappt, scanRecountDue mit Mindestabstand, Regeln, Zukunftsstempel.
- php/lib/Service/SnippetPolicy.php: fail-closed, Vereinigung der Modi, unbekannter Schlüssel auf yes = kein Ausschnitt; Kommentar zu lazy falsch und ungetestet (R-45-21-02).
- php/lib/Service/StorageService.php: Ausschluss nur für Speicher, die ausschließlich unter ausgeschlossenen Admin-Mounts hängen; Tabellen-Guard; Bänder zu ABSENT_LOOKUP_BAND.
- php/lib/Settings/Admin.php: Mount-Liste als Template-Parameter, Fehler nur mit Zähler geloggt.
- php/psalm.xml: Taint-Konfiguration mit Stubs für AppAPI.
- php/templates/admin.php: alle neuen Ausgaben über p(), keine print_unescaped; Haken nur aus Template-Daten.
- php/templates/search.php: nur Formatierung (diff -w leer).
- php/tests/RouteSecurity/Fixtures.php: Einzeiler an neue Konstruktor-Signatur.
- php/tests/Unit/AdminSettingsTest.php: Mount-Liste nie im initial state, Fehlerpfad.
- php/tests/Unit/AdminViewServiceTest.php: neue Felder und Gründe.
- php/tests/Unit/CrawlAdvanceServiceTest.php: crawling() auf den Marker, Slice-Lock allein ist kein Crawl.
- php/tests/Unit/ExclusionServiceTest.php: wildcard neu abgewiesen, alter Eintrag bleibt.
- php/tests/Unit/ExternalMountServiceTest.php: Typ-Filter, Sortierung, duplicate, Katalog.
- php/tests/Unit/FileStateServiceCoverageTest.php: policy_blocked in beiden Listen.
- php/tests/Unit/GatewayControllerTest.php: 403 mit Kopf, origin, info-Zeile mit reader, not_found gleich.
- php/tests/Unit/GatewayReaderTest.php: 22 Fälle für Erkennung, Besitzer, ohne Besitzer, Kappung, andere Ausnahme, Ereignis nur in actAs.
- php/tests/Unit/LockingCheckServiceTest.php: Groß/Klein, Rohwert, Klasse fehlt, Noop.
- php/tests/Unit/MigrationSelfContainedTest.php: Version001500 aus GRANDFATHERED entfernt.
- php/tests/Unit/ProfileControllerTest.php: Generation 4.
- php/tests/Unit/ProviderTest.php: Konstruktor-Anpassung.
- php/tests/Unit/QueueServiceReaderTest.php: Besitzer zuerst, 20 insgesamt.
- php/tests/Unit/QueueServiceTest.php: Konstruktor-Anpassung.
- php/tests/Unit/ReaderCandidatesTest.php: Besitzererkennung nur Home-Mount, Kappung, Fehlerpfad.
- php/tests/Unit/RouteSecurityTest.php: Einzeiler.
- php/tests/Unit/ScanRecountJobTest.php: Mindestabstand im Job.
- php/tests/Unit/SearchServiceTest.php: E3 über die echte SnippetPolicy auf Mocks.
- php/tests/Unit/SecureViewRefusal.php: Ausnahmen mit gesetztem Trace (echt, Frame weiter oben, andere Meldung).
- php/tests/Unit/SettingsControllerTest.php: Formfehler der Mount-Liste und Objektform.
- php/tests/Unit/SettingsServiceTest.php: Lesen mit Kappung, Typkonflikt, Mindestabstand.
- php/tests/Unit/SnippetPolicyTest.php: 29 Fälle je Modus; kein Fall mit lazy gespeichertem Modusschlüssel (R-45-21-02, Mutation grün).
- php/tests/Unit/StorageCrawlJobTest.php: Marker, verschachteltes finally, passierende Lock-Fehler, Grenzen.
- php/tests/Unit/StorageServiceTest.php: Ausschluss, gemischte Mounts, Tabellen-Guard.
- php/tests/Unit/Version001500Date20261012000000Test.php: Literale gegen Konstanten, Marke, Vergessen.
- php/tests/Unit/Version001603Date20261108000000Test.php: Einzeiler.
- php/tests/Unit/Version001700Date20261123000000Test.php: Literale gegen Konstanten, Löschen, Zweitlauf.
- php/tools/php-cs-fixer/composer.json: nur Werkzeug, eigener Lock.
- php/tools/php-cs-fixer/composer.lock: Werkzeug-Lock, nicht im App-Archiv.
- php/tools/psalm/AppFrameworkTainter.php: Taint-Quellen für AppFramework-Parameter.
- php/tools/psalm/composer.json: nur Werkzeug.
- php/tools/psalm/composer.lock: Werkzeug-Lock, nicht im App-Archiv.
- php/tools/psalm/stubs/app_api.phpstub: Stubs für AppAPI-Funktionen.
- php/tools/psalm/taint-probe/ProbeController.php: Positivprobe des Taint-Gates.
- scripts/ci/php_cs_gate.sh: dry-run mit Probe.
- scripts/ci/psalm_taint_gate.sh: SARIF-Zählung, rot ohne Bericht.
- scripts/ci/update_in_process_driver.php: pflanzt backend_app_version, prüft nach Minor-Schritt; kein Rücklesen nach dem Pflanzen (R-45-21-03).
- scripts/ci/update_in_process_proof.sh: Kontrolle 2, FROM_TAGS ab v1.3.2.
- scripts/ci/workflow_lint_gate.sh: zizmor und actionlint mit Positivprobe.
- scripts/dev/php_gates_docker.sh: lokales Rezept aller PHP-Gates.

## Prüfung der Fixes aus 45-20 an der Quelle

- U-45-20-01 (aec5edcf, 151dca7b): `Store.renew_refusal_streaks(companion_generation=...)` nimmt die Marke `refusal_streaks_1_7_0` nur bei Generation >= `RENEW_1_7_0_MIN_GENERATION` (4) dazu (repo.py); `_open_state` von Poller und Abgleich rufen ohne Generation, also nur die Marke 1.6.3; einziger Aufruf mit Generation im Poller vor dem Claim (poller.py Z. 1155-1162). Gegenprobe am Code: ohne Generation keine 1.7-Marke, mit 3 keine, mit 4 genau einmal (Marke in derselben Transaktion). Kein Befund.
- U-45-20-02 (f3290689, 1d191e7e): `CriticalActionPerformedEvent` nur in `openAs()` nach erfolgreichem `opened()` (GatewayReader.php Z. 231-236), also nur im zweiten Durchgang in actAs. Quelle admin_audit stable34: `CriticalActionPerformedEventListener` ruft `log($message, $params, array_keys($params))`, `Action::log` setzt per `vsprintf` in Reihenfolge der Schlüssel ein (Action.php Z. 48-67); Schlüssel id, path, reader passen zur Reihenfolge der drei `%s` in AUDIT_MESSAGE. Pfad und uid sind Parameter, nicht Format, also keine Formatstring-Injektion. Kein Befund am Verhalten; der Docblock oben im Klassenkommentar widerspricht (R-45-21-01).
- U-45-20-03 (3550b2b3, c9dc3270, 0f6afac7): `origin()` liest nur `function` und `class` von `getTrace()[0]`, beide gegen `/^[A-Za-z_\\{}][A-Za-z0-9_\\{}]{0,254}$/D`; Meldung und Argumente nie. Ein Closure-Name mit Pfad (PHP 8.4 `{closure:/pfad:Z}`) enthält `/` und `:` und wird `unknown` bzw. fällt auf die Funktion zurück. Der Modifier D verhindert den Zeilenumbruch am Ende. Kein Befund.
- 457a0786 (watermark-59): siehe Zeile integration.yml oben und R-45-21-08.

## Befunde

| ID | Schwere | Datei:Zeile | Befund | Beleg | Empfehlung | Status |
|---|---|---|---|---|---|---|
| R-45-21-01 | LOW | php/lib/Service/GatewayReader.php:61-63, 71 | Der Klassenkommentar sagt "the read hooks name the reader of the second open, usually the owner" und "The reader stays inside the app and is never logged". Beides stimmt am Kopf nicht: admin_audit schreibt für ein Lesen in actAs `--` (derselbe Kommentar Z. 88-91, Grund für a4), die Person nennt nur das eigene Ereignis (Z. 233-236), und GatewayController loggt sie als `reader` in der info-Zeile (Owner a1). Irreführend für die Datenschutzprüfung in 45-16; docs/privacy.md beschreibt es richtig | Code-Zitate Z. 61-63, 71 gegen Z. 88-96, 233-236 und GatewayController `'reader' => $opened['reader']`; Quelle admin_audit stable34 Files.php Z. 31-48 (eigene Zeile ohne Person im Text, Person aus der Sitzung) | Klassenkommentar an das Verhalten angleichen (Prüfspur über das Ereignis, uid in der info-Zeile, sonst nirgends); keine Verhaltensänderung, kein Nutzertext | offen |
| R-45-21-02 | LOW | php/lib/Service/SnippetPolicy.php:188-190 | Kommentar "richdocuments reads them through IConfig, which does not care whether a key is lazy" ist falsch: IConfig::getAppValue liest nur nicht-lazy Werte. Das Verhalten (lazy Schlüssel mitlesen) ist sicher, unterdrückt höchstens mehr als richdocuments, ist aber durch keinen Test gehalten: Mutation "beide isLazy-Lesungen durch false ersetzt" lässt SnippetPolicyTest grün | AllConfig.php stable34 Z. 163-165 (`getAppValue` ruft `AppConfig::getValue`), AppConfig.php stable34 Z. 1489-1494 (`return $this->fastCache[$app][$key] ?? $default`, nur nicht-lazy); `watermark_enabled` liest richdocuments selbst nicht-lazy (Application.php v12.0.2 Z. 138, SecureViewService Z. 28) wie Findling Z. 184. Mutation: `OK (29 tests, 49 assertions)`, Datei danach per SHA-256 byte-gleich | Kommentar richtigstellen (Findling liest lazy Modusschlüssel bewusst mit, fail-closed, mehr als richdocuments); Test zuerst: ein lazy gespeicherter Modusschlüssel unterdrückt den Ausschnitt, Mutation rot | offen |
| R-45-21-03 | LOW | scripts/ci/update_in_process_driver.php:132-133 | Der Treiber pflanzt `backend_app_version` und liest ihn nicht zurück. Schlägt das Pflanzen still fehl, meldet ein Kandidatenlauf nach einem Minor-Schritt "recorded backend version ... dropped", obwohl nie etwas gepflanzt war; nur Kontrolle 2 fängt das (45-26, unter M35 beobachtet). Randnotiz aus 45-26, bewertet: sinnvolle Härtung, billig, macht jeden Kandidatenlauf selbsttragend | Code Z. 132-133 (setValueString ohne Rücklesen), Z. 181-193 (Erfolgszeile aus dem Zustand nach dem Update); 45-26-SUMMARY "Neue Befunde", M35 | Test zuerst (Strukturgate in test_update_in_process_proof.py mit Fehl-Sample: Rücklesen fehlt oder vergleicht nicht), dann direkt nach dem Pflanzen `getValueString` lesen und bei Abweichung `proofFail`; Docker-Lauf des Update-Nachweises mit Mutation (Pflanzen entfernt -> Kandidat rot) | offen |
| R-45-21-04 | LOW | backend/src/findling/worker/poller.py:1138-1164 | Der Block der Erneuerung 1.7.0 steht zwischen dem Kommentar "The re-check of the old stock after the upgrade (D-29-10) ..." und dem Code des Re-Checks; der Kommentar beschreibt jetzt scheinbar die Erneuerung, der Re-Check steht ohne Kommentar | Code Z. 1138-1148 (Kommentar Re-Check), Z. 1149-1162 (Erneuerung), Z. 1164 (Re-Check) | Kommentar des Re-Checks direkt vor dessen `if` setzen; reine Umstellung, kein Verhalten | offen |
| R-45-21-05 | LOW | php/lib/Service/GatewayReader.php:158-170 (Quelle Gegenprobe 45-20, U-45-20-03) | Die warning-Zeile einer anderen ForbiddenException nannte keine Herkunft | 45-AUDIT.md `#### Befunde dieser Gegenprobe`; am Kopf nachgeprüft: `origin()` nur Klasse::Funktion des ersten Frames, Muster mit D (0f6afac7), Controller hängt `origin` nur bei gesetztem Wert an | schon behoben (Entscheid c2) | behoben c9dc3270, 0f6afac7 (vor 45-21), nachgeprüft |
| R-45-21-06 | INFO | php/lib/Service/GatewayReader.php:96, 233-236 (Threat-Flag 45-20) | Prüfspur-Zeile mit uid und Pfad im audit.log: Datenschutz bewertet. admin_audit schreibt für jedes Lesen ohnehin id und Pfad (`File with id "%s" accessed: "%s"`) und die Person der Sitzung; die neue Zeile nennt dieselbe Datenart (uid, Pfad, id), nie Inhalt, nur bei aktivem admin_audit, nur nach einem Lesen in actAs. Ohne die Zeile wäre die Person einer Lesung nicht nachvollziehbar (U-45-20-02) | admin_audit stable34 Files.php Z. 31-48, Action.php Z. 48-67; GatewayReader Z. 233-236 | in 45-16 unter T-45-74 als bewusste, dokumentierte Erweiterung der Prüfspur führen (docs/privacy.md nennt sie); keine Codeänderung | geschlossen |
| R-45-21-07 | INFO | .planning (verify 45-20 Task 1), I-45-20-05 | verify akzeptiert `"asked":"20"` als Zeichenkette, die Zahl wird weiter exakt geprüft | nextcloud.log schreibt Kontextwerte als Zeichenkette (45-AUDIT.md, I-45-20-05); reine Testtechnik, kein Produktcode | keine Aktion, vom Orchestrator als INFO bestätigt | geschlossen |
| R-45-21-08 | INFO | .github/workflows/integration.yml (Job watermark-59) | Der Job ist strukturell geprüft (Gate scan_watermark_job mit Fehl-Samples, zizmor und actionlint grün), aber noch nie auf einem Runner gelaufen (kein Push) | 45-20-SUMMARY, 45-AUDIT.md `### CI-Strecke, CHANGELOG und Doku 45-20` | erster Lauf nach `Freigabe Push 45-10`, Ergebnis in 45-10 Task 1 belegen | geschlossen (Nachweis in 45-10) |
| R-45-21-09 | INFO | php/lib/Service/ReaderCandidates.php:159 | Die warning-Zeile "could not resolve who sees a queued file" mit `exception` kommt seit #59 auch vom Gateway (zweite Runde), nicht nur aus der Warteschlange; Wortlaut und Ausnahme aus QueueService von 1.6.5 übernommen. Ausnahmen aus `getMountsForFileId` sind Datenbankfehler (NotFoundException fängt der Kern selbst, Benutzer per LazyUser ohne Abfrage) | UserMountCache.php stable34 Z. 373-423; ReaderCandidates Z. 159 | keine Aktion; vorbestehend, keine neue Datenart | geschlossen |
| R-45-21-10 | INFO | php/lib/Service/ExternalMountService.php `read()` | Die Liste der Admin-Mounts wird ohne Obergrenze gelesen; nur Admins legen Mounts an, die Seite rendert sie einmal | Code `read()` ohne LIMIT; ExternalMountService wird nur von Settings\Admin gerufen | keine Aktion | geschlossen |
| R-45-21-11 | INFO | php/lib/Service/GatewayReader.php:226-238 | Das Ereignis wird auch dispatcht, wenn `fopen` false lieferte (der Controller antwortet dann 422); admin_audit selbst schreibt seine Lesezeile ebenso vor dem Öffnen (`BeforeNodeReadEvent`) | Files.php stable34 Z. 31 (BeforeNodeReadEvent); GatewayReader Z. 253 | keine Aktion, gleiche Semantik wie admin_audit | geschlossen |

Keine Befunde CRITICAL, HIGH oder MEDIUM. Vier LOW offen (R-45-21-01 bis -04), einer schon behoben (R-45-21-05); keiner der vier ändert einen nutzersichtbaren Text.
