# Phase 45: Launch-Härtung und Audit von Findling 1.7.0 (Plan 45-09)

Stand: 2026-11-22. Muster: Delta-Audit 43-27 (Prüfpunkt mit Probe, Befund mit Schwere, Fixes ab MEDIUM per TDD, audited_head).

audited_head: offen, wird in Task 3 nach dem freigegebenen Push und grünem Kopf gesetzt
status_45_09: lokal gehärtet, Push und CI-Belege offen

## Umfang

Delta `v1.6.5` (06a0d7c8) bis Kopf. Ohne `.planning` 35 Commits vor diesem Plan plus die Commits dieses Plans:

```
92fd028a test(45-09): the lint images of CI and of the local recipe carry the same digest
53a11d81 docs(45-08): CHANGELOG 1.7.0 in three languages
93996a4b chore(45-08): version 1.7.0 in both apps
907baa2f test(45-07): the gates of the moved store facts read the READMEs
fdfe1b70 docs(45-07): the READMEs carry the facts of 1.7.0 and the details that leave the store text
f95fdf86 ci(45-06): the integration run proves the exclusion of one external storage and its way back
ae57d083 feat(45-05): the admin page lists the external storage an admin set up, each with its own box
08eaa058 feat(45-04): free slots under both lists and a clear answer to * or ? in the folder field
42d3985b feat(45-03): the rules route saves the external storage kept out of the index
873c3e9d feat(45-03): a list of the external storage an admin set up
5445be3c feat(45-02): single external storages can be kept out of the index
fa288361 test(45-02): cases for the exclusion of single external storages
f6eff1a1 docs(45-01): PRODUCT and CHANGELOG name Traditional Chinese and the locale fix
ebd924cf fix(45-01): the admin page rewrites every underscore of root.lang as well
edc08233 Merge pull request #56 from foolfitz/feat/l10n-zh-tw
8cd9a0b4 Merge pull request #57 from foolfitz/fix/admin-locale-tag
fd48fd0a fix(44): Psalm-Taint-Gate auf Runnern scharf, MIT-Lizenztext für REUSE
c6142abb test(44-08): Strukturgate gegen stilles Entfernen der PHP- und Workflow-Gates, Doku
8e4ae166 ci(44-07): zizmor und actionlint als Gate über alle Workflows
ec3b3743 ci(44-06): cooldown, Cache, shellcheck und auditor-Befunde nach Owner-Entscheidung
325fb97a ci(44-05): Zugangsdaten nach dem checkout nicht mehr im Arbeitsbaum (zizmor artipacked)
1983d958 ci(44-04): php-cs-fixer mit nextcloud/coding-standard als dry-run-Gate
fb231ba1 test(44-04): Baumhash der PHP-Hälfte nach dem Formatierungs-Commit
fa1836f5 style(44-04): PHP-Quellen nach nextcloud/coding-standard formatiert, ohne Verhaltensänderung
8f5aca31 ci(44-03): lokales Rezept für das Psalm-Taint-Gate
1d6236f2 docs(store-listing): 1.6.5-Abschnitt ohne gesperrten Wortstamm umformuliert
4f51f090 ci(44-02): Psalm-Taint-Gate gegen OCP 33, 34 und 35 mit eigener SARIF-Zählung
168b6b13 fix(admin): the admin page keeps working under a three part locale such as zh_Hant_TW
51690b2a ci(integration): prove the zh_TW result page in the core lang step (#53)
66717f00 docs(l10n): record the zh_TW measurements in the shared catalogue proof (#53)
525f02de feat(l10n): Traditional Chinese (Taiwan) catalogue zh_TW (#53)
24c04abd docs(store-listing): release 1.6.5 evidence
cba2de8c chore(deps)(deps): bump pypdf from 6.21.4 to 7.0.1 in /backend (#55)
ec3674b6 chore(deps)(deps): bump the python-minor-and-patch group in /backend with 5 updates (#54)
b3b6f844 docs(security): guideline cross-check against the Nextcloud security guidelines
```

Wirksame Laufzeit-Änderungen: PHP-Companion (php/lib: SettingsService, StorageService, ExternalMountService neu, SettingsController, AdminViewService, ExclusionService, Settings\Admin; Template admin.php; admin.js; admin.css; 18 Kataloge). `git diff --stat v1.6.5..HEAD -- backend/src` ist leer: der Container ändert sich nur über Abhängigkeiten (pypdf 6.21.4 auf 7.0.1, #55; fünf Minor/Patch-Updates, #54). Alles in php/tools, scripts, .github ist Gate- und CI-Werkzeug ohne Laufzeitwirkung beim Nutzer. php/templates/search.php (320 Zeilen) ist die Formatierung von fa1836f5 (44-04, ohne Verhaltensänderung, Baumhash-Beleg fb231ba1).

## Security

| Nr | Prüfpunkt | Probe | Ergebnis |
|---|---|---|---|
| 1 | POST /admin/rules als Nicht-Admin und ohne Request-Token | `git diff --stat v1.6.5..HEAD -- php/tests/route-security.json` leer; Eintrag `SettingsController::saveRules` = `FrontpageRoute POST /admin/rules`, `attributes: []` (also weder NoAdminRequired noch NoCSRFRequired: der Kern verlangt Admin und Request-Token); RouteSecurityTest in der vollen PHPUnit-Suite grün (1284 Tests) | bestanden, keine neue Route, Rechte-Grenze unverändert |
| 2 | excludedExternalMounts mit Nicht-Liste, Strings, negativen Zahlen, 0, 1001 Einträgen, verschachtelten Arrays, Float, Bool, null-Eintrag | `SettingsControllerTest::testAnUnusableSelectionIsRefusedAndWritesNothing` mit elf Datensätzen ('x', 4, [0], [-3], ['4'], [[4]], [4.0], [true], [null], range(1, 1001), ['a' => ['b' => 4]]): je 400, `fields = {excludedExternalMounts: out_of_range}`, keine Schreibung, Log nur Zähler. Sechs Datensätze neu in diesem Plan. Positivkontrolle: Obergrenze in `usableMountList()` per Mutation entfernt -> genau der Fall "one more than the ceiling" rot (Tests: 11, Failures: 1), Datei danach byte-gleich zurück | bestanden. Ein Objekt mit Zahlwerten (`{"a": 4}`) wird nicht abgewiesen, sondern als Liste seiner Werte genommen: Befund L-45-09-02 |
| 3 | occ-Garbage in excluded_external_mounts (String, Typkonflikt, Fremdwerte) | `SettingsServiceTest::testATypeConflictReadsAsAnEmptyListWithACounterOnly` (Typkonflikt -> [] und eine Warnung nur mit Zählern), `testAnOccWrittenListKeepsItsPositiveIdsAndCountsTheRest` ([7, 3, 3, 0, -2, 'x'] -> [3, 7], unusable 3); Seite: `Admin::externalMounts()` fängt jeden Fehler, Template liest `$_['externalMounts']` defensiv (admin.php Z. 1106 bis 1117, is_array/is_int/is_string) | bestanden. Ein occ-Objekt mit Zahlwerten wird wie eine Liste gelesen (L-45-09-02); eine sehr lange occ-Liste wird ohne Obergrenze gelesen (L-45-09-01); occ-Liste ohne jemals aktiviertes files_external: L-45-09-03 |
| 4 | ID eines persönlichen Mounts in der Liste | `StorageServiceTest::testAPersonalMountIdInTheListHasNoEffect`; Code: Abfrage 1 in `excludedStorageIds()` mit `type = ADMIN_MOUNT_TYPE` (1) und Zeilenprüfung | bestanden, keine Wirkung |
| 5 | Storage mit ausgeschlossenem und zugelassenem Mount | `testAStorageThatAnIncludedMountAlsoCarriesStays` (23 unter Mount 6 und 7, 24 unter Mount 6 und Home-Provider, beide bleiben); Mutation aus 45-02 (Abfrage 3 aus) macht genau diesen Fall rot | bestanden |
| 6 | gelöschter und umbenannter Mount | gelöscht: `testADeletedMountIdInTheListHasNoEffectAndLeavesNoTrace` (ID 404, keine Wirkung, keine Logzeile). Umbenannt: `excludedStorageIds()` liest aus external_mounts nur `mount_id, type` und aus mounts nur `storage_id, mount_id, mount_provider_class`, nie `mount_point`; gespeichert wird die Konfigurations-ID (`KEY_EXCLUDED_EXTERNAL_MOUNTS`, Docblock SettingsService) | bestanden. Hinweis I-45-09-04 (verwaiste IDs bleiben bis zum nächsten Speichern der Seite stehen) |
| 7 | Admin-Mount mit Nutzer-Anmeldedaten (eine storage_id je Nutzer) | `testAnExcludedMountWithUserCredentialsTakesEveryStorageOfIt` (Mount 5 trägt 21 und 22, beide fallen heraus und sind deselected) | bestanden |
| 8 | Hauptschalter aus und wieder an mit gespeicherter Liste | `SettingsServiceTest::testWithTheSwitchOffTheStoredListIsReadUnchanged`, `StorageServiceTest::testWithTheSwitchOffTheListChangesNothingAndStaysReadable` (aus: keine Abfrage auf external_mounts) und neu `testTheStoredListTakesHoldAgainWhenTheSwitchComesBackOn` (wieder an: 21 fällt heraus und ist deselected; Liste leer: 21 zurück) | bestanden |
| 9 | files_external deaktiviert | `ExternalMountServiceTest::testWithoutFilesExternalTheListIsEmptyWithoutAQuery`, `AdminSettingsTest::testWithoutFilesExternalTheListIsEmptyAndSwitchedOff`; Template zeigt dann nur `#findling-rules-mounts-disabled`; Script sendet ohne gerenderte Liste `inForceMounts` unverändert (Gate `test_the_script_reads_a_mount_only_out_of_its_row_and_writes_it_as_text`, Fehl-Sample "leere Liste statt in Kraft stehender") | bestanden, Speichern lässt die Liste unverändert |
| 10 | XSS: Einhängepunkt `<img src=x onerror=alert(1)>` in Liste und Bestätigung | `ExternalMountServiceTest::testAMountPointWithMarkupComesBackUnchanged` (Rohwert, Escaping im Template); Template Z. 1684 bis 1685 nur `p()`; `grep -n "innerHTML\|insertAdjacentHTML\|outerHTML\|document.write" php/js/admin.js` ohne Treffer; Bestätigung per textContent (Gate mit Fehl-Sample "Label per innerHTML"). Sichtprobe im Browser folgt in 45-10 (T-45-19) | bestanden |
| 11 | alte Ordnereinträge mit * werden geduldet, neue abgewiesen | `ExclusionServiceTest::testAStoredFolderEntryWithAStarIsToleratedOnSave`, `testOnlyTheNewEntryWithAStarIsRefusedNextToAStoredOne`, `testAStoredEntryIsToleratedAlsoWhenSentInAnotherSpelling`, `testANewFolderEntryWithAWildcardEarnsItsCodeAndNotItsValue` | bestanden, ein Upgrade sperrt das Speichern nicht |
| 12 | Logs ohne Pfad, Mount-ID, Einhängepunkt | `git diff v1.6.5..HEAD -U0 -- php/lib php/templates php/js \| grep -E "^\+.*(logger->\|console\.)"`: vier neue Warnungen, Kontexte nur `['failed' => 1]`, `['unusable' => 1, 'inForce' => 0]`, `['unusable' => $unusable, 'inForce' => count($ids)]`; SettingsController zählt `'excludedExternalMounts' => count($mounts)`. Tests `assertNoLogCarries`, `assertTheLogOnlyCounts` | bestanden |
| 14 | Psalm-Taint OCP 33/34/35, php-cs-fixer, zizmor, actionlint | `bash scripts/dev/php_gates_docker.sh all` am Stand dieses Plans (Ergebnis unter "Lokale Gates") | siehe Lokale Gates |
| 31 | Digest-Gleichheit zizmor/actionlint (T-45-31) | neu `test_the_lint_images_carry_the_same_digest_in_ci_and_in_the_local_recipe` (92fd028a): liest workflow-lint.yml als YAML und php_gates_docker.sh zeilenweise, vergleicht die volle Referenz. Acht Fehl-Samples rot wie erwartet (zizmor-Digest im Rezept, actionlint-Digest im Workflow, anderer Tag, kein Digest, fehlt im Rezept, fehlt im Workflow, doppelt). RED vor dem Scanner: 9 failed. Positivkontrolle an den echten Dateien: Rezept-Kopie mit geändertem actionlint-Digest -> `ACTIONLINT_IMAGE differs ...`. Unabhängige Gegenprobe per grep/cut: beide Namen gleich | bestanden |

## Bugs

- Abhängigkeiten des Containers: pypdf 7.0.1 (Major, #55) und fünf Minor/Patch-Updates (#54). Probe: `pytest tests/test_extract_documents.py` plus alle Extraktor-, PDF-, ZIP- und Feindseligkeits-Testdateien: 485 passed. CI "Python gates", "Integration", "HaRP deploy" am Kopf 612b7c9e grün (45-06). Ergebnis: kein Befund.
- `classifyAbsent()`/`deselected()`: frühes Return jetzt nur ohne abgeschaltete Provider UND ohne ausgeschlossene Storages; beide Mengen durchlaufen `!isIndexedStorage()` (T-45-09). Integrationsbeleg M-45-01 (Lauf 44982244176): E1 deselected=1, stamp '', Kontrollen E3 und keep36 unverändert, Rückkehr im nächsten Abgleich.
- `save()` schreibt die Mount-Liste vor Cap und Schaltern; ein späterer Fehler im selben Aufruf ist nicht möglich, weil `validate()` vorher alles prüft (gleiche Reihenfolge wie im Bestand). Kein Befund.
- Hinweis aus 45-05: Bei zwei Speichern mit gleichem Einhängepunkt nennt die Bestätigung den Einhängepunkt zweimal ohne ID. Rein UI, Prüfung in 45-10 (Playwright), hier kein Befund.

## Performance

| Nr | Prüfpunkt | Probe | Ergebnis |
|---|---|---|---|
| 13a | keine Abfrage bei leerer Liste | `StorageServiceTest::testAnEmptyListAsksNoMountTable` (`getQueryBuilder` never) und Schalter aus ohne external_mounts-Abfrage (Probe 8) | bestanden |
| 13b | eine Abfragekette pro Request, gebändert | `testALongListIsAskedInBandsAndOncePerRequest`: 250 IDs -> external_mounts 200/50, mounts 200/50, zweiter `getMounts()` ohne neue Abfrage; Cache `$excludedStorages`, `isIndexedStorage()` liest `getMounts()` einmal je Request; `SettingsService::$excludedMounts` gecacht | bestanden |
| 13c | Seitenlast mit 200 Admin-Mounts | Abschätzung aus dem Code: `ExternalMountService::adminMounts()` stellt genau eine Abfrage (`external_mounts WHERE type = 1`), sortiert per Collator in O(n log n) (200 Einträge, Mikrosekunden bis wenige Millisekunden), Duplikat-Zählung O(n); das Template prüft je Zeile `in_array` gegen die ausgeschlossenen IDs (höchstens 1000 per Route) -> höchstens 200 x 1000 Vergleiche; 200 `<li>` mit je drei `p()`. Die Liste reist nicht im Initial State und nicht im Poll von fünf Sekunden (AdminSettingsTest::testTheMountListIsATemplateParameterAndNeverInTheInitialState) | unkritisch, kein Befund |
| 13d | Leseseite ohne Obergrenze | `excludedExternalMounts()` liest eine per occ geschriebene Liste in voller Länge; `excludedStorageIds()` fragt dann je 200 IDs eine Runde, also bei 100 000 IDs etwa 500 Abfragen einmal je Request (auch im Request eines Datei-Schreibvorgangs über den Listener) | Befund L-45-09-01 |

## Upgrade und Installation

- STOPP-Prüfung (Lehre #51, T-45-28): `git diff --stat v1.6.5..HEAD -- php/lib/Migration` leer; `git diff --stat v1.6.5..HEAD -- backend/src/findling/store/schema.sql backend/src/findling/store/vectors.sql backend/src/findling/index/schema.py` leer; `git diff --stat v1.6.5..HEAD -- backend/src` leer.
- Neuer appconfig-Schlüssel `excluded_external_mounts` ohne Migration: fehlender Schlüssel liest als leere Liste (`testAMissingKeyIsAnEmptyListOfExcludedMounts`), alle Admin-Mounts bleiben nach dem Upgrade drin.
- Altes admin.js aus dem Browser-Cache (1.6.5) sendet das Feld nicht: Liste bleibt (`testWithoutTheFieldTheStoredSelectionStaysAsItWas`, `testAFormWithoutTheFieldLeavesTheExcludedMountsAlone`, T-45-14).
- Gespeicherte Ordnereinträge mit * bleiben speicherbar (Probe 11, T-45-15).
- Update in einem Prozess aus v1.6.2, v1.6.3, v1.6.4, v1.6.5: `scripts/ci/update_in_process_proof.sh` Z. 47 `FROM_TAGS="${FROM_TAGS:-v1.6.2 v1.6.3 v1.6.4 v1.6.5}"`, Job "Store update in one process (issue 51)" in php.yml. CI-Beleg für den Kandidaten 1.7.0: offen bis zum freigegebenen Push (Task 3).
- HaRP deploy: `UPGRADE_FROM_TAG: v1.5.0` (deploy-harp.yml Z. 201) und die frische Installation ("Store install"-Schritte). CI-Beleg für den Kandidaten 1.7.0: offen bis zum freigegebenen Push (Task 3).

## Threat-Register 45

| Threat | Disposition | Beleg | Status |
|---|---|---|---|
| T-45-01 | mitigate | `gh pr merge --match-head-commit` auf 168b6b13 (#57) und 51690b2a (#56), 45-PR-REVIEW.md, 45-01-SUMMARY | mitigated |
| T-45-02 | mitigate | Diff von integration.yml gelesen (45-PR-REVIEW.md); zizmor/actionlint lokal und "Workflow security lint" in CI grün (Lauf 44982244168) | mitigated |
| T-45-03 | mitigate | Katalogwerte nur über `p()`/Textknoten, Gate `test_no_catalogue_value_can_break_the_page`, Platzhalter-Paritäts-Gate grün | mitigated |
| T-45-04 | mitigate | Zeilen `Freigabe Merge PR57/PR56 45-01` in 45-FREIGABEN.md vor den Merges | mitigated |
| T-45-05 | mitigate | Probe 3 (Typkonflikt, Fremdwerte, nur Zähler) | mitigated; Resthinweise L-45-09-02 und L-45-09-03 (LOW, Owner) |
| T-45-06 | mitigate | Obergrenze 1000 beim Schreiben (Probe 2 mit Mutation), Bänder und Cache (Probe 13b) | mitigated für den Schreibweg; Leseseite L-45-09-01 (LOW, Owner) |
| T-45-07 | mitigate | Probe 12, `testADeletedMountIdInTheListHasNoEffectAndLeavesNoTrace` | mitigated |
| T-45-08 | mitigate | Probe 4 und 5 | mitigated |
| T-45-09 | mitigate | `!isIndexedStorage()` in `deselected()`, Probe 5, M-45-01 | mitigated |
| T-45-10 | mitigate | Probe 1 | mitigated |
| T-45-11 | mitigate | Probe 2 | mitigated; Objekt-Form L-45-09-02 (LOW, Owner) |
| T-45-12 | mitigate | `AdminSettingsTest::testTheMountListIsATemplateParameterAndNeverInTheInitialState`; `rules()` nur IDs; Probe 12 | mitigated |
| T-45-13 | mitigate | Probe 10 | mitigated |
| T-45-14 | mitigate | Upgrade-Abschnitt (Feld fehlt -> unverändert) | mitigated |
| T-45-15 | mitigate | Probe 11 | mitigated |
| T-45-16 | mitigate | nur `p()`, Gate C, Funktions-Replacements gegen `$&` (45-04), `test_no_catalogue_value_can_break_the_page` | mitigated |
| T-45-17 | mitigate | `testANewFolderEntryWithAWildcardEarnsItsCodeAndNotItsValue` (Antwort und Log ohne Wert) | mitigated |
| T-45-18 | accept | Server entscheidet in `validate()`, Script nur Komfort | accepted (unverändert) |
| T-45-19 | mitigate | Probe 10; Sichtprobe in 45-10 | mitigated (Sichtprobe offen in 45-10) |
| T-45-20 | mitigate | Inline-Bestätigung mit Einhängepunkt, Fokus auf "Keep files indexed", Escape setzt zurück (45-05) | mitigated (Abnahme UI in 45-10) |
| T-45-21 | mitigate | Probe 9 | mitigated |
| T-45-22 | accept | nur Admins (Probe 1), Form-Prüfung (Probe 2), fremde IDs wirken nur als Admin-Mounts (Probe 4) | accepted (unverändert) |
| T-45-23 | mitigate | neue run:-Blöcke von M-45-01 ohne `${{ }}` mit Fremdinhalt; zizmor/actionlint lokal und CI grün | mitigated |
| T-45-24 | mitigate | `Freigabe Push 45-06` vor dem Push committet (612b7c9e) | mitigated |
| T-45-25 | mitigate | `expect_unstamped` für E1 in M-45-01 (stamp '') | mitigated |
| T-45-26 | mitigate | Tabelle alt -> neu in 45-07-SUMMARY, jeder umgezogene Gate mit Fehl-Sample | mitigated |
| T-45-27 | mitigate | 45-README-PRUEFUNG.md (24 Aussagen mit Quelle), Datenschutz-Kern-Gate auf info.xml | mitigated |
| T-45-28 | mitigate | STOPP-Prüfung oben | mitigated |
| T-45-29 | mitigate | FROM_TAGS mit v1.6.4 und v1.6.5; CI-Beleg nach Push (Task 3) | mitigated im Code, Beleg offen bis Task 3 |
| T-45-30 | mitigate | test_lockstep_versions.py grün (45-08), beide info.xml 1.7.0 | mitigated |
| T-45-31 | mitigate | Prüfpunkt 31 (Digest-Gate) | mitigated |
| T-45-32 | mitigate | Probe 1 | mitigated |
| T-45-33 | mitigate | Update-Probe v1.6.4/v1.6.5 und HaRP-Upgrade; CI-Beleg nach Push (Task 3) | offen bis Task 3 |
| T-45-34 | mitigate | jede Zeile dieses Berichts mit Probe; audited_head in Task 3 | offen bis Task 3 |

## Befunde

| ID | Schwere | Bereich | Befund | Beleg | Empfehlung | Status |
|---|---|---|---|---|---|---|
| L-45-09-01 | LOW | Performance/DoS | `SettingsService::excludedExternalMounts()` liest eine per occ geschriebene Liste ohne Obergrenze; `excludedStorageIds()` fragt sie in Bändern zu 200 ab, bei 100 000 IDs rund 500 Abfragen je Request (auch im Request eines Schreibvorgangs über den Listener). Nur per occ erreichbar, die Route begrenzt auf 1000. `ExclusionService::prefixes()` schneidet beim Lesen an der Grenze und zählt den Rest | SettingsService.php `excludedExternalMounts()` (foreach ohne Grenze); StorageService.php `excludedStorageIds()` `array_chunk($wanted, self::ABSENT_LOOKUP_BAND)` | beheben: beim Lesen nach `MAX_EXCLUDED_EXTERNAL_MOUNTS` gültigen IDs abschneiden und den Rest als `unusable` zählen (wie prefixes()), Test zuerst | offen, Owner-Entscheid |
| L-45-09-02 | LOW | Eingabeform | Ein Objekt mit Zahlwerten wird als Liste seiner Werte genommen: Route `{"a": 4}` -> `listOf()` macht `array_values` -> [4] gespeichert; occ-Wert `{"a": 4}` (Typ array) liest als [4]. Dokumentierte Regel H-33-01 ("An object stays what it was before, its values in order", SettingsController `listOf()`), gilt gleich für Ordner- und Musterliste; nur Admins, Wirkung gleich dem Senden der Liste | SettingsController.php `listOf()` Z. 621 bis 627; SettingsService `excludedExternalMounts()` prüft nur die Werte | akzeptieren: bewusste, dokumentierte Regel für alle drei Listen, keine Rechte-Grenze berührt | offen, Owner-Entscheid |
| L-45-09-03 | LOW | Robustheit | Ist files_external nie aktiviert worden, gibt es die Tabelle `oc_external_mounts` nicht (angelegt erst von der Migration Version1011Date20200630192246 beim Aktivieren; files_external steht nicht in `defaultEnabled` von core/shipped.json, stable34). Schreibt ein Admin per occ trotzdem IDs in `excluded_external_mounts` und ist der Schalter für externe Speicher an, wirft Abfrage 1 von `excludedStorageIds()`; damit werfen `getMounts()` und `isIndexedStorage()`: Crawl, Abgleich und Ereignisse stocken, der Listener schreibt je Schreibvorgang eine Warnung (nur Klassenname). Über die Seite nicht erreichbar (die Liste erscheint nur mit aktivem files_external), aus dem Code abgeleitet und nicht auf einer echten Instanz nachgestellt | StorageService.php `excludedStorageIds()` Abfrage 1 ohne Tabellen- oder App-Prüfung; FileEventListener.php Z. 150 fängt und loggt; Quellen per raw.githubusercontent.com am 22.11.2026 | beheben: vor Abfrage 1 prüfen, ob es Admin-Mounts geben kann (Tabelle vorhanden bzw. files_external für jemanden aktiv), sonst leere Menge, ohne Logzeile mit Wert; Test zuerst (Datenbank wirft) | offen, Owner-Entscheid |
| I-45-09-04 | INFO | Datenpflege | IDs gelöschter Mounts bleiben in der gespeicherten Liste, bis die Seite das nächste Mal speichert (sie sendet nur gerenderte Haken, die verwaiste ID fällt dann heraus); bis dahin ohne Wirkung (Probe 6). Entspricht D-45-06 ("ignoriert") | admin.js `excludedMountsOf()`; Probe 6 | keine Aktion | geschlossen |

Keine Befunde CRITICAL, HIGH oder MEDIUM.

## Lokale Gates

Am Stand nach den Regressionsfällen dieses Plans (2026-11-22):

- `bash scripts/dev/phpunit_docker.sh`: `OK (1284 tests, 8191 assertions)`, Floor erfüllt.
- `bash scripts/dev/php_gates_docker.sh all`: Exit 0; Psalm-Taint gegen nextcloud/ocp v33.0.9, v34.0.6, v35.0.3 je `taint findings: 0`; php-cs-fixer `Found 0 of 133 files that can be fixed`, Probe gesehen; zizmor `no finding of severity medium or above`, Probe gesehen (exit 14); actionlint `no finding`, Probe gesehen (SC2086).
- Python in backend/: `ruff check .` grün, `ruff format --check .` 260 Dateien formatiert, pyright (latest) 0 Fehler, vulture grün.
- pytest: test_php_supply_chain_gates.py (25), test_measurement_scripts.py, test_php_static_gates.py, test_php_trust_boundary.py, test_exclusion_path_space.py, test_admin_ui_contract.py zusammen 946 passed; migration_path, phase33/34/40/41_audit, probe_run, store_metadata, unified_search_plugin, workflow_tag_triggers, changelog_translations, public_artifacts, admin_locale, lockstep_versions zusammen 555 passed, 113 skipped; Extraktoren und feindselige Dateien 485 passed.
- Baumhash PHP-Hälfte nach den Testfällen: 136 Dateien, 6638875f (Rezept und unabhängige Pipeline find, sort, sed, sha256sum gleich; Positivkontrolle git archive 92fd028a = ee8088b3).
