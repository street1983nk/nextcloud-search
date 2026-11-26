# Phase 45: Launch-Härtung und Audit von Findling 1.7.0 (Plan 45-09)

Stand: 2026-11-22. Muster: Delta-Audit 43-27 (Prüfpunkt mit Probe, Befund mit Schwere, Fixes ab MEDIUM per TDD, audited_head).

audited_head: bb4c0bc8ca9c2b96edacc4de8a846d9d5ccdfe4d
status_45_21: passed
status_45_09: passed

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
| 13d | Leseseite ohne Obergrenze | `excludedExternalMounts()` liest eine per occ geschriebene Liste in voller Länge; `excludedStorageIds()` fragt dann je 200 IDs eine Runde, also bei 100 000 IDs etwa 500 Abfragen einmal je Request (auch im Request eines Datei-Schreibvorgangs über den Listener) | Befund L-45-09-01, behoben 2b623a3f (Obergrenze 1000 auch beim Lesen, höchstens 5 Bänder je Request) |

## Upgrade und Installation

- STOPP-Prüfung (Lehre #51, T-45-28): `git diff --stat v1.6.5..HEAD -- php/lib/Migration` leer; `git diff --stat v1.6.5..HEAD -- backend/src/findling/store/schema.sql backend/src/findling/store/vectors.sql backend/src/findling/index/schema.py` leer; `git diff --stat v1.6.5..HEAD -- backend/src` leer.
- Neuer appconfig-Schlüssel `excluded_external_mounts` ohne Migration: fehlender Schlüssel liest als leere Liste (`testAMissingKeyIsAnEmptyListOfExcludedMounts`), alle Admin-Mounts bleiben nach dem Upgrade drin.
- Altes admin.js aus dem Browser-Cache (1.6.5) sendet das Feld nicht: Liste bleibt (`testWithoutTheFieldTheStoredSelectionStaysAsItWas`, `testAFormWithoutTheFieldLeavesTheExcludedMountsAlone`, T-45-14).
- Gespeicherte Ordnereinträge mit * bleiben speicherbar (Probe 11, T-45-15).
- Update in einem Prozess aus v1.6.2, v1.6.3, v1.6.4, v1.6.5: `scripts/ci/update_in_process_proof.sh` Z. 47 `FROM_TAGS="${FROM_TAGS:-v1.6.2 v1.6.3 v1.6.4 v1.6.5}"`, Job "Store update in one process (issue 51)" in php.yml. CI-Beleg für den Kandidaten 1.7.0: siehe "CI-Belege am Kopf cb2038b9".
- HaRP deploy: `UPGRADE_FROM_TAG: v1.5.0` (deploy-harp.yml Z. 201) und die frische Installation ("Store install"-Schritte). CI-Beleg für den Kandidaten 1.7.0: siehe "CI-Belege am Kopf cb2038b9".

### CI-Belege am Kopf cb2038b9

Push nach "Freigabe Push 45-09" am 2026-11-22: `612b7c9e..cb2038b9  main -> main` (ohne Tag). Ein CI-Warter, `scripts/ci/head_green.sh cb2038b9862794c4d90074b7b8f22cbb693d5043 "Python gates" "PHP and store metadata gates" "HaRP deploy" "Integration" "Resilience" "Multi-arch image" "Security scans"`, Exit 0, kein Rerun nötig:

```
44993702781 Multi-arch image success
44993702734 Security scans success
44993702767 HaRP deploy success
44993702806 Workflow security lint success
44993702761 Python gates success
44993702809 Resilience success
44993702739 OpenSSF Scorecard success
44993702772 Integration success
44993702837 PHP and store metadata gates success
```

Update in einem Prozess, Lauf 44993702837, Job "Store update in one process (issue 51)" (wörtlich):

```
2026-11-22T06:28:14.7840946Z UPDATE-PROOF ok findling 1.6.4 -> 1.7.0, migrations applied in this run: none
2026-11-22T06:28:22.3100351Z findling 1.6.5 enabled
2026-11-22T06:28:22.5592315Z UPDATE-PROOF installed findling 1.6.5, 69 classes of it loaded, 0 not loadable, 14 migrations applied
2026-11-22T06:28:22.5593180Z UPDATE-PROOF ok findling 1.6.5 -> 1.7.0, migrations applied in this run: none
2026-11-22T06:28:25.3174071Z update proof: control reproduced, every candidate run passed
```

(dazu v1.6.2 -> 1.7.0 und v1.6.3 -> 1.7.0 ok, Kontrolle v1.6.2 -> v1.6.3 reproduziert "Undefined constant").

HaRP deploy, Lauf 44993702767, Job `deploy-harp (stable34, 8.2, false, ubuntu-24.04)`:

```
Store upgrade 4:  2026-11-22T06:50:46.0875699Z installed_version went from 1.5.0 to 1.7.0
Store install 7:  2026-11-22T06:39:25.1996654Z the installation is complete after 9 occ calls, and nothing below may add one
Store install 7:  2026-11-22T06:40:27.7138519Z content hit after 7 cron rounds, with nothing configured
Store install 7:  2026-11-22T06:40:27.7152925Z none, which is what zero config means
```

T-45-29 und T-45-33 damit belegt (mitigated). audited_head = `git log -1 --format=%H -- . ':!.planning'` = af0e5e13 (letzter Code-Commit, auf origin/main).

## Threat-Register 45

| Threat | Disposition | Beleg | Status |
|---|---|---|---|
| T-45-01 | mitigate | `gh pr merge --match-head-commit` auf 168b6b13 (#57) und 51690b2a (#56), 45-PR-REVIEW.md, 45-01-SUMMARY | mitigated |
| T-45-02 | mitigate | Diff von integration.yml gelesen (45-PR-REVIEW.md); zizmor/actionlint lokal und "Workflow security lint" in CI grün (Lauf 44982244168) | mitigated |
| T-45-03 | mitigate | Katalogwerte nur über `p()`/Textknoten, Gate `test_no_catalogue_value_can_break_the_page`, Platzhalter-Paritäts-Gate grün | mitigated |
| T-45-04 | mitigate | Zeilen `Freigabe Merge PR57/PR56 45-01` in 45-FREIGABEN.md vor den Merges | mitigated |
| T-45-05 | mitigate | Probe 3 (Typkonflikt, Fremdwerte, nur Zähler) | mitigated; L-45-09-02 (af0e5e13) und L-45-09-03 (fcfa50b2) behoben |
| T-45-06 | mitigate | Obergrenze 1000 beim Schreiben (Probe 2 mit Mutation), Bänder und Cache (Probe 13b) | mitigated für Schreib- und Leseweg (L-45-09-01 behoben, 2b623a3f) |
| T-45-07 | mitigate | Probe 12, `testADeletedMountIdInTheListHasNoEffectAndLeavesNoTrace` | mitigated |
| T-45-08 | mitigate | Probe 4 und 5 | mitigated |
| T-45-09 | mitigate | `!isIndexedStorage()` in `deselected()`, Probe 5, M-45-01 | mitigated |
| T-45-10 | mitigate | Probe 1 | mitigated |
| T-45-11 | mitigate | Probe 2 | mitigated; Objekt-Form L-45-09-02 behoben (af0e5e13) |
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
| T-45-29 | mitigate | FROM_TAGS mit v1.6.4 und v1.6.5; Lauf 44993702837 "UPDATE-PROOF ok findling 1.6.5 -> 1.7.0" | mitigated |
| T-45-30 | mitigate | test_lockstep_versions.py grün (45-08), beide info.xml 1.7.0 | mitigated |
| T-45-31 | mitigate | Prüfpunkt 31 (Digest-Gate) | mitigated |
| T-45-32 | mitigate | Probe 1 | mitigated |
| T-45-33 | mitigate | Update-Probe v1.6.4/v1.6.5 (Lauf 44993702837) und HaRP-Upgrade 1.5.0 -> 1.7.0 (Lauf 44993702767) | mitigated |
| T-45-34 | mitigate | jede Zeile dieses Berichts mit Probe; audited_head af0e5e13 | mitigated |

## Befunde

| ID | Schwere | Bereich | Befund | Beleg | Empfehlung | Status |
|---|---|---|---|---|---|---|
| L-45-09-01 | LOW | Performance/DoS | `SettingsService::excludedExternalMounts()` liest eine per occ geschriebene Liste ohne Obergrenze; `excludedStorageIds()` fragt sie in Bändern zu 200 ab, bei 100 000 IDs rund 500 Abfragen je Request (auch im Request eines Schreibvorgangs über den Listener). Nur per occ erreichbar, die Route begrenzt auf 1000. `ExclusionService::prefixes()` schneidet beim Lesen an der Grenze und zählt den Rest | SettingsService.php `excludedExternalMounts()` (foreach ohne Grenze); StorageService.php `excludedStorageIds()` `array_chunk($wanted, self::ABSENT_LOOKUP_BAND)` | beheben: beim Lesen nach `MAX_EXCLUDED_EXTERNAL_MOUNTS` gültigen IDs abschneiden und den Rest als `unusable` zählen (wie prefixes()), Test zuerst | behoben 2b623a3f (Owner: beheben); RED `testAnOccWrittenListLongerThanTheCeilingIsCutOnReadAndTheRestCounted`, GREEN mit Grenzfall 1000 und Doppel |
| L-45-09-02 | LOW | Eingabeform | Ein Objekt mit Zahlwerten wird als Liste seiner Werte genommen: Route `{"a": 4}` -> `listOf()` macht `array_values` -> [4] gespeichert; occ-Wert `{"a": 4}` (Typ array) liest als [4]. Dokumentierte Regel H-33-01 ("An object stays what it was before, its values in order", SettingsController `listOf()`), gilt gleich für Ordner- und Musterliste; nur Admins, Wirkung gleich dem Senden der Liste | SettingsController.php `listOf()` Z. 621 bis 627; SettingsService `excludedExternalMounts()` prüft nur die Werte | akzeptieren: bewusste, dokumentierte Regel für alle drei Listen, keine Rechte-Grenze berührt | behoben af0e5e13 (Owner: beheben, für alle drei Listen; Empfehlung "akzeptieren" überstimmt); Route lehnt Objekt und Liste mit Lücke ab (`empty` bzw. `out_of_range` für die Mount-Liste), Lesen bleibt duldsam; neue Regel ersetzt H-33-01 "An object stays what it was" |
| L-45-09-03 | LOW | Robustheit | Ist files_external nie aktiviert worden, gibt es die Tabelle `oc_external_mounts` nicht (angelegt erst von der Migration Version1011Date20200630192246 beim Aktivieren; files_external steht nicht in `defaultEnabled` von core/shipped.json, stable34). Schreibt ein Admin per occ trotzdem IDs in `excluded_external_mounts` und ist der Schalter für externe Speicher an, wirft Abfrage 1 von `excludedStorageIds()`; damit werfen `getMounts()` und `isIndexedStorage()`: Crawl, Abgleich und Ereignisse stocken, der Listener schreibt je Schreibvorgang eine Warnung (nur Klassenname). Über die Seite nicht erreichbar (die Liste erscheint nur mit aktivem files_external), aus dem Code abgeleitet und nicht auf einer echten Instanz nachgestellt | StorageService.php `excludedStorageIds()` Abfrage 1 ohne Tabellen- oder App-Prüfung; FileEventListener.php Z. 150 fängt und loggt; Quellen per raw.githubusercontent.com am 22.11.2026 | beheben: vor Abfrage 1 prüfen, ob es Admin-Mounts geben kann (Tabelle vorhanden bzw. files_external für jemanden aktiv), sonst leere Menge, ohne Logzeile mit Wert; Test zuerst (Datenbank wirft) | behoben fcfa50b2 (Owner: beheben); auf echter Instanz nachgestellt und nach dem Fix gegengeprüft, Abschnitt "L-45-09-03 auf einer echten Instanz"; Guard nur `tableExists(external_mounts)` |
| I-45-09-04 | INFO | Datenpflege | IDs gelöschter Mounts bleiben in der gespeicherten Liste, bis die Seite das nächste Mal speichert (sie sendet nur gerenderte Haken, die verwaiste ID fällt dann heraus); bis dahin ohne Wirkung (Probe 6). Entspricht D-45-06 ("ignoriert") | admin.js `excludedMountsOf()`; Probe 6 | keine Aktion | geschlossen |

Keine Befunde CRITICAL, HIGH oder MEDIUM. Alle drei LOW-Befunde nach Owner-Entscheid vom 2026-11-22 05:36 UTC behoben (45-FREIGABEN.md).

## Fixes nach Owner-Entscheid (Task 2 und 3)

Owner "Ok" am 2026-11-22 05:36 UTC (45-FREIGABEN.md): alle drei LOW beheben, Test zuerst.

RED am Stand 802434fd (Tests geschrieben, Quellcode unverändert), `bash scripts/dev/phpunit_docker.sh --filter 'SettingsControllerTest|SettingsServiceTest|StorageServiceTest'`: `Tests: 211, Errors: 1, Failures: 10`, genau die neuen Fälle:

- L-45-09-03: `StorageServiceTest::testWithoutTheTableOfFilesExternalAStoredListExcludesNothingAndStallsNothing` (Error: die Abfrage auf external_mounts wirft)
- L-45-09-02: `SettingsControllerTest::testAnUnusableSelectionIsRefusedAndWritesNothing` mit "an object of ids" und "a list with a hole"; `testAPatternListThatIsNoListIsRefusedWithACodeAndWritesNothing`, `testAPrefixListThatIsNoListIsRefusedWithACodeAndWritesNothing`, `testThePreviewRefusesEitherListThatIsNoList` je mit "an object" und "a list with a hole"; `testAnObjectInsteadOfAListIsRefusedInEveryListAndWritesNothing`
- L-45-09-01: `SettingsServiceTest::testAnOccWrittenListLongerThanTheCeilingIsCutOnReadAndTheRestCounted` (1200 IDs gelesen statt 1000)

Schon im RED grün und als Schutz behalten: `testAListAtTheCeilingIsReadWholeAndADoubleBeyondItIsNoSurplus`, `testAStoredObjectFormIsStillReadAsItsValues`, `testStoredObjectFormsAreStillReadAndSaveBackAsLists` (das duldsame Lesen gilt schon und muss bleiben), `testWithTheTableInPlaceAFailingQueryIsNotSwallowed` (der Guard darf keinen anderen Datenbankfehler schlucken), `testWithAnEmptyListOrTheSwitchOffTheTableIsNotAskedFor`. Der RED-Lauf ist zugleich die Positivkontrolle (B8): ohne den jeweiligen Fix sind genau diese Fälle rot.

| Befund | Commit | Änderung |
|---|---|---|
| L-45-09-03 | fcfa50b2 | `StorageService::excludedStorageIds()`: ohne Tabelle `external_mounts` (`IDBConnection::tableExists`) leere Menge, ohne Logzeile; erst gefragt, wenn Schalter an und Liste nicht leer, einmal je Request (Cache) |
| L-45-09-01 | 2b623a3f | `SettingsService::excludedExternalMounts()`: die ersten 1000 brauchbaren IDs in gespeicherter Reihenfolge bleiben, jede weitere neue zählt als `unusable`; Doppel sind kein Überschuss; eine Warnung nur mit Zählern |
| L-45-09-02 | af0e5e13 | `SettingsController::listOf()`: `!array_is_list` wie Nicht-Liste, Code `empty` (Ordner, Muster, auch Vorschau-Route), `out_of_range` für `excludedExternalMounts`; nichts geschrieben. Lesen unverändert duldsam. Regel H-33-01 neu gefasst im Docblock von `listOf()`, im Docblock von `SettingsService::excludedExternalMounts()`, in docs/admin-page.md ("Abgelehnte Eingaben") und in test_phase33_audit.py (Objekt-Fall jetzt `empty`, zwei neue Objekt-Fälle im Instanztest) |

Gates je Commit (B3), am Arbeitsbaum genau des Commits: PHPUnit voll `OK (1287 tests, 8204 assertions)`, `OK (1290 tests, 8216 assertions)`, `OK (1299 tests, 8351 assertions)`; `php_gates_docker.sh all` je Exit 0 (Psalm-Taint OCP 33/34/35 je 0 Befunde, Probe 3; php-cs 0; zizmor und actionlint ohne Befund, Proben gesehen); ruff, ruff format (260), pyright latest 0, vulture grün; pytest test_measurement_scripts, test_admin_ui_contract, test_phase33_audit, test_phase34_audit, test_php_static_gates, test_php_trust_boundary, test_exclusion_path_space zuletzt `971 passed, 107 skipped`. Baumhash PHP-Hälfte je Commit per Rezept und unabhängiger Pipeline (find, sort, sed, sha256sum) gleich: f20a3153, 77b20880, a2b061ac; Positivkontrolle je über git archive des Vorgänger-Commits (6638875f, f20a3153, 77b20880).

Abweichung: Beim Commit 2b623a3f lief der erste `php_gates_docker.sh all` rot, weil das Paket vimeo/psalm im Container unvollständig entpackt war (`include(.../vimeo/psalm/psalm): Failed to open stream`, "psalm wrote no SARIF report"); der Commit war durch eine Befehlskette mit `;` schon erstellt. Der zweite Lauf am unveränderten Baum desselben Commits war grün (drei Mal `taint findings: 0`, php-cs 0, zizmor und actionlint ohne Befund). Kein Codebefund, nur Werkzeug.

Keine neue nutzersichtbare Zeichenkette: `empty` und `out_of_range` haben ihre Sätze auf der Seite schon, kein Katalog geändert.

## L-45-09-03 auf einer echten Instanz

Nachgestellt am 2026-11-22 (UTC) auf einer frischen Nextcloud 34.0.3 (Image `nextcloud:34.0.3-apache`, SQLite, eigenes Volume `findling-l03-html`, Container `findling-l03-repro`, Port 8089), seriell, ohne andere Docker-Arbeit daneben; die PHP-App per Bind-Mount aus dem Arbeitsbaum. Zwischen vorher und nachher nur `php/lib/Service/StorageService.php` getauscht (vorher: `git show HEAD:...` mit HEAD 802434fd, nachher: Fassung mit Guard) und der Container neu gestartet.

Ausgangslage (files_external aus, Tabelle fehlt, IDs per occ, Schalter an):

```
$ docker run -d --name findling-l03-repro -p 8089:80 -e SQLITE_DATABASE=nextcloud -e NEXTCLOUD_ADMIN_USER=admin -e NEXTCLOUD_ADMIN_PASSWORD=... -e NEXTCLOUD_TRUSTED_DOMAINS=localhost -v findling-l03-html:/var/www/html -v ".../php:/var/www/html/custom_apps/findling" nextcloud:34.0.3-apache
$ occ status            ->  installed: true, version: 34.0.3.2
$ occ app:enable findling
findling 1.7.0 enabled
$ occ app:list          ->  Enabled: Z. 1, Disabled: Z. 53, "  - files_external: 1.26.0" in Z. 56 (also unter Disabled)
$ php -r '... SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "oc_%mounts%"'
oc_mounts
$ occ config:app:set findling index_external_storage --value=true --type=boolean
Config value 'index_external_storage' for app 'findling' is now set to '1', stored as boolean in fast cache
$ occ config:app:set findling excluded_external_mounts --value='[5]' --type=array
Config value 'excluded_external_mounts' for app 'findling' is now set to '[5]', stored as array in fast cache
```

Vorher (ohne Guard). Probe `/tmp/l03_probe.php` ruft `StorageService::getMounts()` über `\OCP\Server::get()` und `IDBConnection::tableExists()`:

```
$ php /tmp/l03_probe.php
getMounts: OC\DB\Exceptions\DbalException: An exception occurred while executing a query: SQLSTATE[HY000]: General error: 1 no such table: oc_external_mounts
tableExists(external_mounts): false
tableExists(mounts): true
$ curl -u admin:... -T l03-probe.txt .../remote.php/dav/files/admin/l03-before.txt
upload HTTP 201
queue rows: 0
$ occ background-job:execute <SchedulerJob> --force-execute
Job executed!
nextcloud.log, Meldungen gezählt:
      2 "Message":"An exception occurred while executing a query: SQLSTATE[HY000]: General error: 1 no such table: oc_external_mounts"
      2 "Message":"SQLSTATE[HY000]: General error: 1 no such table: oc_external_mounts"
      2 "error":"OC\\DB\\Exceptions\\DbalException"
      2 "message":"Error while running background job OCA\\Findling\\BackgroundJobs\\SchedulerJob (id: 154831771661922304, arguments: null)"
      2 "message":"Findling: an event could not be turned into queued work"
```

Erste Runde mit `cron.php` am selben Stand gab dasselbe Bild (SchedulerJob: `no such table: oc_external_mounts`, Listener: `"error":"OC\\DB\\Exceptions\\DbalException"`, Arbeitsvorrat 0). Damit ist L-45-09-03 auf der echten Instanz belegt: der Upload kommt nicht in die Warteschlange, der Crawl-Planer bricht ab.

Nachher (mit Guard, gleicher appconfig-Stand `1` und `[5]`):

```
$ php /tmp/l03_probe.php
getMounts: ok, mounts=1
tableExists(external_mounts): false
tableExists(mounts): true
$ curl -u admin:... -T l03-probe.txt .../remote.php/dav/files/admin/l03-after.txt
upload HTTP 201
queue rows: 1
$ occ findling:index --restart -n
Cleared 1 stale jobs of the earlier run.
The crawl was queued. It starts with the next run of the background jobs.
$ occ background-job:execute 154832109429223424 --force-execute     (SchedulerJob)
Job executed!
log lines: 0
background-job:list: OCA\Findling\BackgroundJobs\StorageCrawlJob {"storage_id":2,"root_id":1,"overridden_root":7,"last_file_id":0}
$ occ background-job:execute 154832137031938048 --force-execute     (StorageCrawlJob)
log lines: 0
queue rows: 54
$ occ findling:index --status
Work stock
  scheduled            54
```

Ergebnis: mit Guard keine Ausnahme, keine Logzeile, das Ereignis wird eingereiht, Planer und Crawl laufen durch (54 Dateien eingereiht). `tableExists('mounts')` = true ist die Positivkontrolle, dass die Abfrage den Präfix `oc_` selbst setzt. Bewusst nicht umgesetzt: die zusätzliche Bedingung "files_external nicht aktiviert -> leere Menge". Ist die App deaktiviert, die Tabelle aber da, läuft die Abfrage fehlerfrei, und alte Zeilen des Providers in `oc_mounts` könnten sonst ihre Speicher wieder in den Index bringen (Ausschluss fiele offen aus); der Guard prüft nur das, was die Ausnahme auslöst.

## Lokale Gates

Am Stand nach den Regressionsfällen dieses Plans (2026-11-22):

- `bash scripts/dev/phpunit_docker.sh`: `OK (1284 tests, 8191 assertions)`, Floor erfüllt.
- `bash scripts/dev/php_gates_docker.sh all`: Exit 0; Psalm-Taint gegen nextcloud/ocp v33.0.9, v34.0.6, v35.0.3 je `taint findings: 0`; php-cs-fixer `Found 0 of 133 files that can be fixed`, Probe gesehen; zizmor `no finding of severity medium or above`, Probe gesehen (exit 14); actionlint `no finding`, Probe gesehen (SC2086).
- Python in backend/: `ruff check .` grün, `ruff format --check .` 260 Dateien formatiert, pyright (latest) 0 Fehler, vulture grün.
- pytest: test_php_supply_chain_gates.py (25), test_measurement_scripts.py, test_php_static_gates.py, test_php_trust_boundary.py, test_exclusion_path_space.py, test_admin_ui_contract.py zusammen 946 passed; migration_path, phase33/34/40/41_audit, probe_run, store_metadata, unified_search_plugin, workflow_tag_triggers, changelog_translations, public_artifacts, admin_locale, lockstep_versions zusammen 555 passed, 113 skipped; Extraktoren und feindselige Dateien 485 passed.
- Baumhash PHP-Hälfte nach den Testfällen: 136 Dateien, 6638875f (Rezept und unabhängige Pipeline find, sort, sed, sha256sum gleich; Positivkontrolle git archive 92fd028a = ee8088b3).

## Nachtrag 45-17 bis 45-22 (#59, V-45-10-02/03, E3)

Plan 45-17 Task 1, 2026-11-22. Quellen am Tag, Nachbau auf v1.6.5 in den Wasserzeichen-Modi M1 bis M5 und die Tabelle vorher; die Gegenprobe nachher folgt in 45-20.

### Quellen am Tag

Abgerufen am 2026-11-22 per `gh api repos/nextcloud/<repo>/contents/<pfad>?ref=<tag>` (Accept raw), abgelegt unter `<scratchpad>/src59/<tag>/`. Neueste Version je Nextcloud-Hauptversion laut Tag-Liste und `appinfo/info.xml`: richdocuments v12.0.2 (`<nextcloud min-version="35" max-version="35"/>`), v11.1.3 (34 bis 34), v10.3.3 (33 bis 33); files_accesscontrol v6.0.1 (35), v5.0.1 (34), v4.0.2 (33). Die Kopien `rd/*.php` im Scratchpad sind byte-gleich mit v12.0.2 (SHA-256 SecureViewWrapper ead56095..., SecureViewService 4cbbdeac..., PermissionManager 6cb3f1f2..., Application 8041f61a...) bzw. `rd/fac.php` mit files_accesscontrol v6.0.1 lib/StorageWrapper.php (71bdddad...). Die in findling-59 installierte richdocuments 12.0.2 hat dieselben vier SHA-256 wie der Tag (`sha256sum` im Container gegen `src59/v12.0.2`).

richdocuments, Datei und Zeile je Tag:

| Stelle | v12.0.2 (NC 35) | v11.1.3 (NC 34) | v10.3.3 (NC 33) |
|---|---|---|---|
| Hook `OC_Filesystem::preSetup` -> addStorageWrapper | Application.php Z. 84 | Z. 84 | Z. 80 |
| ohne `watermark_enabled` (Namensraum `files`) != 'no' kein Wrapper | Z. 139 | Z. 139 | Z. 132 |
| `Filesystem::addStorageWrapper('richdocuments', ..., -10)` | Z. 143 | Z. 143 | Z. 136 |
| Callback: `if (!\OC::$CLI && $mountPoint !== '/')` -> SecureViewWrapper um jeden Mount außer '/' | Z. 153 | Z. 153 | Z. 146 |
| `namespace OCA\Richdocuments\Storage;` / `class SecureViewWrapper` | SecureViewWrapper.php Z. 9 / 22 | Z. 9 / 22 | Z. 9 / 22 |
| `fopen()` ruft `$this->checkFileAccess($path)` | Z. 46-47 | Z. 46-47 | Z. 46-47 |
| `private function checkFileAccess` | Z. 90 | Z. 90 | Z. 90 |
| Bedingung `!isWOPIRequest() && getMethod() === 'GET' && shouldSecure($path, $this, false)` | Z. 94-96 | Z. 94-96 | Z. 94-96 |
| `throw new ForbiddenException('Download blocked due the secure view policy', false)` | Z. 97 | Z. 97 | Z. 97 |
| aktive Person `$this->userSession->getUser()?->getUID()` | SecureViewService.php Z. 58 | Z. 57 | Z. 57 |
| `shouldWatermark($cacheEntry, $userId, $share, $storage->getOwner($path) ?: null)` | Z. 60 | Z. 59 | Z. 59 |
| `shouldWatermark()` | PermissionManager.php Z. 174 | Z. 174 | Z. 174 |
| nur richdocuments-Mimetypes (`getMimeTypes()`) | Z. 179 | Z. 179 | Z. 179 |
| `$isUpdatable` aus Eintrag bzw. Freigabe | Z. 185-188 | Z. 185-188 | Z. 185-188 |
| link-Modi nur bei `getShareType() === IShare::TYPE_LINK` | Z. 194-215 | Z. 194-215 | Z. 194-215 |
| shareAll: `if ($userId === null \|\| $ownerId !== $userId) return true` | Z. 217-224 (221) | gleich | gleich |
| shareRead: `&& !$isUpdatable` | Z. 226-228 | gleich | gleich |
| shareDisabledDownload: `&& $isDisabledDownload` | Z. 230-232 | gleich | gleich |
| shareTalkPublic: `$userId === null && TYPE_ROOM` | Z. 234-238 | gleich | gleich |
| allGroups: `$userId !== null && ...` | Z. 240-247 | gleich | gleich |
| allTags: Systemtag in `watermark_allTagsList` | Z. 248-257 | gleich | gleich |

Unterschiede zwischen den Versionen (`diff` der vier Dateien): SecureViewWrapper.php ist in allen drei Tags byte-gleich (SHA-256 ead56095...). SecureViewService.php v12.0.2 hat gegenüber v11.1.3 nur eine Leerzeile mehr (v10.3.3 = v11.1.3). PermissionManager.php v11.1.3 = v12.0.2; v10.3.3 weicht in genau einer Zeile ab (Z. 183 `$fileId = $nodeOrCacheEntry->getId();` statt `(string)...`, ohne Wirkung auf die Bedingungen). Application.php: v11.1.3 -> v12.0.2 nur der Listener für gelöschte Tags (`TagDeletedEvent` statt `ManagerEvent::EVENT_DELETE`); v10.3.3 -> v11.1.3 neue Listener und Vorschau-Provider, dadurch verschobene Zeilen. Die GET- und die WOPI-Bedingung, die exakte Nachricht, Klasse, Namensraum, Funktionsname `checkFileAccess` und alle Modus-Bedingungen gelten unverändert in v10.3.3, v11.1.3 und v12.0.2. Watermark-Schlüssel stehen im App-Namensraum `files` (AppConfig.php v12.0.2 Z. 52 `WATERMARK_APP_NAMESPACE = 'files'`); Listen (`watermark_allTagsList`, `watermark_allGroupsList`) als kommagetrennte Zeichenkette (AppConfig.php Z. 98-103). Mimetypes (Capabilities.php v12.0.2 Z. 17 ff., 40 ff., 64 ff.): ODT, PDF, `text/plain`, `text/markdown` u. a., also alle drei Probe-Typen.

Folgerung für den Trace: Die Ausnahme entsteht in `checkFileAccess` (Z. 97), aufgerufen aus `fopen` (Z. 47). `getTrace()[0]` ist damit der Frame von `checkFileAccess` (class `OCA\Richdocuments\Storage\SecureViewWrapper`, function `checkFileAccess`, line 47 als Aufrufstelle), `getLine()` ist 97. Die Meldung des Melders nennt "Line":47; das passt zur Aufrufstelle, nicht zu `getLine()` (am echten Log unten geprüft).

files_accesscontrol v6.0.1:

- CacheWrapper.php Z. 30-34 Maske ohne READ, CREATE, UPDATE, DELETE; Z. 38-56 `formatCacheEntry()` ruft `Operation::checkFileAccess(..., 0)` und nimmt bei `ForbiddenException` die Bits per Maske weg (Z. 52-53). Damit löst die gesperrte Person den Knoten ohne Lesebit auf; `SearchService::readableFile()` gibt null, das Gateway antwortet 404 bzw. readerOf überspringt die Person (unreadable).
- StorageWrapper.php Z. 103-110 `isReadable()` false bei Sperre; Z. 306-312 `getCache()` legt den CacheWrapper um.
- Abweichung von der Annahme des Plans ("keine ForbiddenException beim fopen"): StorageWrapper.php Z. 241-253 `fopen()` ruft `checkFileAccess($path, false, PERMISSION_READ)` und kann damit sehr wohl werfen, `Operation.php` Z. 118 `throw new ForbiddenException('Access denied by access control', false)`. Erreicht wird dieser Wurf nur, wenn der Knoten zuvor lesbar aufgelöst wurde, also wenn die Regel bei der Auflösung (CacheWrapper, `requiredPermissions` 0) anders entscheidet als beim Öffnen (`PERMISSION_READ`), etwa eine Regel mit Rechte-Operation statt `deny`. Für den Entwurf von 45-17 heißt das: diese Ausnahme ist "eine andere ForbiddenException" (Nachricht und Ursprungs-Frame passen nicht zu Secure View) und führt fail-closed zu 403 policy ohne erneutes Öffnen. Das ist gewollt; die Bewertung gehört in die echte Probe von 45-20 Schritt C.

### Nachbau vor dem Fix (v1.6.5)

Stand: 2026-11-22 10:15 bis 11:42 UTC, Repo-Kopf 15fef4aa (Freigaben 45-17), Nachbau aus dem Worktree `<scratchpad>/wt-165` am Tag v1.6.5 (06a0d7c8c9a33e7cce599c1c834d66a902ad0ce2), Begleit-App per Bind-Mount von `wt-165/php`, Backend als Host-Prozess aus `wt-165/backend` (eigene venv, `uv sync --frozen`), Speicher `<scratchpad>/state-59/storage`. Docker seriell, vor dem Start `test -z "$(docker ps -q)"` leer. Passwörter und Secrets ausgelassen.

Aufbau:

```
$ git worktree add <scratchpad>/wt-165 v1.6.5      ->  HEAD is now at 06a0d7c8 chore(release): version 1.6.5 in both apps
$ (wt-165/backend) uv sync --frozen
$ docker compose -f <scratchpad>/compose-59.yaml -p findling-59 up -d
  (Kopie von scripts/dev/compose.yaml: name findling-59, container_name findling-59, Image nextcloud:35.0.3-apache, Port 8091, Volume findling-59-html, ./wt-165/php -> custom_apps/findling)
$ curl -s http://localhost:8091/status.php
{"installed":true,"maintenance":false,"needsDbUpgrade":false,"version":"35.0.3.2","versionstring":"35.0.3",...}
$ occ app:install richdocuments
Error: Cannot write into "apps" directory. ...
  (Docker legt custom_apps für den Bind-Mount als root an; nur das Verzeichnis selbst: chown www-data:www-data /var/www/html/custom_apps)
$ occ app:install richdocuments      ->  richdocuments 12.0.2 installed / richdocuments enabled
$ sha256sum lib/Storage/SecureViewWrapper.php lib/Service/SecureViewService.php lib/PermissionManager.php lib/AppInfo/Application.php   (im Container)
ead56095...  4cbbdeac...  6cb3f1f2...  8041f61a...   (gleich dem Tag v12.0.2, siehe Quellen am Tag)
$ occ app:install groupfolders       ->  groupfolders 23.0.1 installed
$ occ app:list (Auszug)              ->  app_api 35.0.0, findling 1.6.5, groupfolders 23.0.1, richdocuments 12.0.2; admin_audit disabled; spreed und files_accesscontrol nicht installiert
$ FINDLING_PORT=8091 sh <scratchpad>/register59.sh   (Kopie von scripts/dev/register-exapp.sh mit REPO_ROOT=wt-165, COMPOSE_FILE=compose-59.yaml, RUN_DIR=state-59)
registering version 1.6.5 with 6 routes from backend/appinfo/info.xml
ExApp findling_backend deployed successfully.
```

Zwei Umgebungsschritte, ohne die das Host-Backend nichts indexiert: (1) `state-59/storage` musste angelegt werden (`the enable could not be written to the volume, an FileNotFoundError`); (2) das Wortlisten-Artefakt `dict/de.txt` aus `.dev/storage/dict` kopiert, Digest `b1f64012ca7f5b6e57de2cb1bafa2521cb6606f3ccef5d6fd17396edc808dde0` wie in docs/german-analyzer.md (sonst `indexing pass ended in an unexpected FileNotFoundError`, docs/dev-setup.md Schritt 1). Kein Tesseract auf dem Host: die acht Beispielbilder von admin enden `failed(ocr_unavailable)`, die Probedateien haben eine Textebene und sind davon nicht berührt.

Saat (`<scratchpad>/seed59.sh`, `share59.sh`, Dateien aus `gen59.py`): `occ background:cron`, `skeletondirectory` und `templatedirectory` leer, Nutzer alice, bob, carol, dave; Uploads per WebDAV (je HTTP 201); Freigaben per OCS an alice; Gruppen tf-lesen (alice, bob, carol), gm-lesen (alice, dave), gm-schreiben (bob), wz-gruppe (alice, bob, dave); Team Folder 1 `TF-lesen` (tf-lesen: permissions 1; zum Hochladen kurz schreibend, danach nur lesend) und 2 `TF-gemischt` (gm-lesen 1, gm-schreiben 7). Eindeutige Wörter: b1 `Wasserzeichenprobe59a`, b2 `...59b`, b3 `...59c`, d1 `...59d`, d2 `...59e`, d3 `...59f`, `Positivkontrolle59`, `Eigenprobe59`, `Leseprobe59`, tf1 `Teamordnerprobe59a`, tf2 `Teamordnerprobe59b`. Abweichung von der Planvorgabe nur bei der Positivkontrolle: `wz59-offen.odt` mit Download UND `permissions=3`, damit sie auch in M5 (shareRead) eine Positivkontrolle bleibt.

```
$ php /tmp/sql59.php "SELECT id, share_type, uid_owner, share_with, file_source, permissions, attributes FROM oc_share ORDER BY id"
id=1 | share_type=0 | uid_owner=bob | share_with=alice | file_source=130 | permissions=1 | attributes=[["permissions","download",false]]
id=2 | share_type=0 | uid_owner=bob | share_with=alice | file_source=133 | permissions=1 | attributes=[["permissions","download",false]]
id=3 | share_type=0 | uid_owner=bob | share_with=alice | file_source=134 | permissions=1 | attributes=[["permissions","download",false]]
id=4 | share_type=0 | uid_owner=dave | share_with=alice | file_source=141 | permissions=1 | attributes=[["permissions","download",false]]
id=5 | share_type=0 | uid_owner=dave | share_with=alice | file_source=142 | permissions=1 | attributes=[["permissions","download",false]]
id=6 | share_type=0 | uid_owner=dave | share_with=alice | file_source=143 | permissions=1 | attributes=[["permissions","download",false]]
id=7 | share_type=0 | uid_owner=bob | share_with=alice | file_source=135 | permissions=3 | attributes=NULL
id=8 | share_type=0 | uid_owner=bob | share_with=alice | file_source=137 | permissions=1 | attributes=NULL
```

Datei-IDs: 130 wz59-b1.odt, 133 wz59-b2.pdf, 134 wz59-b3.txt, 135 wz59-offen.odt, 136 wz59-eigen.odt, 137 wz59-lesen.odt (bob, Speicher 3); 141 wz59-d1.odt, 142 wz59-d2.pdf, 143 wz59-d3.txt (dave, Speicher 4); 152 wz59-tf1.odt (TF-lesen, Speicher 7); 153 wz59-tf2.odt (TF-gemischt, Speicher 8). Mimetypes 11 `application/vnd.oasis.opendocument.text`, 12 `application/pdf`, 22 `text/plain` (alle in `getMimeTypes()` von richdocuments). Systemtag für M3: `occ tag:add wz59-tag public` -> `{"id":"1","name":"wz59-tag","access":"public"}`, als bob per `PUT /remote.php/dav/systemtags-relations/files/<id>/1` an 130 und 136 (HTTP 201), `oc_systemtag_object_mapping`: 130 und 136 mit Tag 1.

Mount-Cache-Probe (`php /tmp/mounts59.php <ids>`, CLI, `IUserMountCache::getMountsForFileId`, öffnet nichts), Anfang und Ende gleich bis auf carol:

```
130 | bob | /bob/ | OC\Files\Mount\LocalHomeMountProvider
130 | alice | /alice/files/wz59-b1.odt/ | OCA\Files_Sharing\MountProvider
(133, 134, 135, 137 gleich: bob /bob/ LocalHomeMountProvider, alice /alice/files/<name>/ Files_Sharing)
136 | bob | /bob/ | OC\Files\Mount\LocalHomeMountProvider
141 | dave | /dave/ | OC\Files\Mount\LocalHomeMountProvider
141 | alice | /alice/files/wz59-d1.odt/ | OCA\Files_Sharing\MountProvider
(142, 143 gleich)
152 | bob | /bob/files/TF-lesen/ | OCA\GroupFolders\Mount\MountProvider
152 | alice | /alice/files/TF-lesen/ | OCA\GroupFolders\Mount\MountProvider
152 | carol | /carol/files/TF-lesen/ | OCA\GroupFolders\Mount\MountProvider     (erst am Ende; vor carols erster Anmeldung fehlte die Zeile)
153 | bob | /bob/files/TF-gemischt/ | OCA\GroupFolders\Mount\MountProvider
153 | alice | /alice/files/TF-gemischt/ | OCA\GroupFolders\Mount\MountProvider
153 | dave | /dave/files/TF-gemischt/ | OCA\GroupFolders\Mount\MountProvider
```

Der Home-Mount trägt exakt `/<uid>/` mit `OC\Files\Mount\LocalHomeMountProvider` (Grundlage der Besitzererkennung in Task 3); Team-Folder-Mounts haben keinen Home-Mount, also keinen Besitzer.

Ablauf je Modus (`<scratchpad>/mode59.sh <Modus> <schlüssel=wert>`): alle fünf Modus-Schlüssel (`watermark_shareAll`, `watermark_shareRead`, `watermark_shareDisabledDownload`, `watermark_allTags`, `watermark_allGroups`) im Namensraum `files` auf `no`, `watermark_enabled=yes`, dann nur die Schlüssel des Modus; `occ findling:index --restart -n`; zweimal `background-job:worker 'OCA\Findling\BackgroundJobs\SchedulerJob' --once` und `... StorageCrawlJob --stop_after 60`; warten, bis `scheduled` und `handed to the worker` 0 sind (höchstens 90 x 10 s); dann messen: `grep -c "secure view policy" nextcloud.log` vorher/nachher, Gateway-Anfragen aus dem Apache-Zugriffsprotokoll (`docker logs --since`, die URL trägt `userId` = Leser laut Claim), Backend-Zeilen, state.db (`state59.py`, nur lesend), `oc_findling_file_state`, Unified Search per OCS `GET /ocs/v2.php/search/providers/findling/search?term=<Wort>` als Besitzer, alice, carol (Zahl der `resourceUrl`). Ausgaben vollständig in `<scratchpad>/state-59/mode-<M>.txt`. Vor M2 zusätzlich M0 (Wasserzeichen aus) als Grundlinie. Die Listen-Schlüssel `watermark_allTagsList` (1) und `watermark_allGroupsList` (wz-gruppe) bleiben nach M3/M4 stehen; wirkungslos, solange der zugehörige Modus `no` ist.

Endkonfiguration nach M1 (`occ config:list files | grep watermark`):

```
            "watermark_shareAll": "no",
            "watermark_shareRead": "no",
            "watermark_shareDisabledDownload": "yes",
            "watermark_allTags": "no",
            "watermark_allGroups": "no",
            "watermark_enabled": "yes",
            "watermark_allTagsList": "1",
            "watermark_allGroupsList": "wz-gruppe"
```

Aktive Person beim fopen (temporäre Probe nur im Worktree `wt-165`, nie im Repo: eine Zeile `$this->logger->error('PROBE59 active user at fopen: ' . (\OCP\Server::get(\OCP\IUserSession::class)->getUser()?->getUID() ?? 'null') . ' file ' . $fileId);` direkt vor `$stream = $file->fopen('r');`, nur während M2, danach `git checkout -- php/lib/Controller/GatewayController.php`; Datei im Container danach ohne `PROBE59`, ohne CR-Zeichen SHA-256 db26d2c0... wie `git show v1.6.5:php/lib/Controller/GatewayController.php`):

```
      2 "message":"PROBE59 active user at fopen: null file 130"
      2 "message":"PROBE59 active user at fopen: null file 136"
      2 "message":"PROBE59 active user at fopen: null file 152"
      (jede gelesene Datei: null, auch 136 mit Leser bob)
```

Ein echter Secure-View-Logeintrag (`php /tmp/svlog59.php 1`, M2):

```
time=2026-11-22T10:37:53+00:00 app=findling url=/ocs/v2.php/apps/findling/files/141?userId=alice message=Findling: unknown error reading a file
  Exception=OCP\Files\ForbiddenException Message=Download blocked due the secure view policy File=SecureViewWrapper.php Line=97
  Trace[0] class=OCA\Richdocuments\Storage\SecureViewWrapper function=checkFileAccess file=SecureViewWrapper.php line=47
  Trace[1] class=OCA\Richdocuments\Storage\SecureViewWrapper function=fopen file=View.php line=1233
  Trace[2] class=OC\Files\View function=basicOperation file=View.php line=1062
```

Damit ist die Erkennung aus E1 am echten Request belegt: Nachricht exakt, `getTrace()[0]` mit class `OCA\Richdocuments\Storage\SecureViewWrapper` und function `checkFileAccess`. Die "Line":47 aus #59 ist die Zeile des Ursprungs-Frames, `getLine()` ist 97.

M0 (Wasserzeichen aus, Grundlinie): alle elf Gateway-Anfragen 200 (130, 133, 134, 135, 137, 141, 142, 143, 152, 153 mit `userId=alice`, 136 mit `userId=bob`), 0 Secure-View-Zeilen, state.db alle `indexed`, Treffer Besitzer und alice je 1, carol 0 (auch bei TF-lesen, siehe Befund I-45-17-04).

M2 shareAll (10:37 bis 10:55 UTC):

```
-- secure view policy im nextcloud.log nachher: 56 (Differenz 56)
      2 GET /ocs/v2.php/apps/findling/files/130?userId=alice 500
      2 GET /ocs/v2.php/apps/findling/files/133?userId=alice 500
      1 GET /ocs/v2.php/apps/findling/files/134?userId=alice 500
      1 GET /ocs/v2.php/apps/findling/files/135?userId=alice 500
      1 GET /ocs/v2.php/apps/findling/files/136?userId=bob 500
      1 GET /ocs/v2.php/apps/findling/files/137?userId=alice 500
      2 GET /ocs/v2.php/apps/findling/files/141?userId=alice 500
      2 GET /ocs/v2.php/apps/findling/files/142?userId=alice 500
      2 GET /ocs/v2.php/apps/findling/files/143?userId=alice 500
      1 GET /ocs/v2.php/apps/findling/files/152?userId=alice 500
      1 GET /ocs/v2.php/apps/findling/files/153?userId=alice 500
      3 WARNING:findling.worker.poller:content gateway refused 5 files of this pass with http status 500 from 2 storages, taken as an outage
      1 WARNING:findling.worker.poller:content gateway refused 9 files of this pass with http status 500 from 2 storages, taken as an outage
      2 WARNING:findling.worker.poller:indexing pass stopped, the content gateway is unavailable, 27 rows handed back, 5 charged
-- state.db: alle elf failed | gateway_error (attempts 1 oder 2)
```

Die 56 Zeilen sind 16 Anfragen auf Probedateien und 40 auf Office-, PDF- und Textdateien von admin (je eine "refused one file, http status 500"); die Bilder von admin (PNG, JPG) wurden nicht abgelehnt (kein richdocuments-Mimetype).

M3 allTags (Tag 1 an 130 und 136, 10:57 bis 10:59 UTC): Differenz 2; `130?userId=alice 500`, `136?userId=bob 500`, alle übrigen neun 200; state.db 130 und 136 `failed | gateway_error | attempts=3`, Rest `indexed`; `oc_findling_file_state` 130 und 136 `failed | gateway_error`.

M4 allGroups (wz-gruppe: alice, bob, dave; 10:59 bis 11:02 UTC): Differenz 0, alle elf 200, alle `indexed`. Positivkontrolle, dass der Modus für angemeldete Personen greift (WebDAV-Download):

```
M4 WebDAV GET als alice alice/wz59-offen.odt -> HTTP 403
M4 WebDAV GET als bob bob/wz59-eigen.odt -> HTTP 403
M4 WebDAV GET als carol carol/TF-lesen/wz59-tf1.odt -> HTTP 200
M4 WebDAV GET als alice alice/TF-lesen/wz59-tf1.odt -> HTTP 403
```

M5 shareRead (11:02 bis 11:21 UTC): Differenz 14; 500 für 130, 133, 134, 137, 141, 142, 143, 152, 153 (alle `userId=alice`), 200 für 135 (`permissions=3`) und 136 (`userId=bob`); zweimal "refused 5 files ... from 2 storages, taken as an outage"; state.db die neun `failed | gateway_error`, 135 und 136 `indexed`. Gegenprobe per WebDAV:

```
M5 WebDAV GET als bob bob/TF-gemischt/wz59-tf2.odt -> HTTP 200
M5 WebDAV GET als alice alice/TF-gemischt/wz59-tf2.odt -> HTTP 403
M5 WebDAV GET als dave dave/TF-gemischt/wz59-tf2.odt -> HTTP 403
M5 WebDAV GET als bob bob/TF-lesen/wz59-tf1.odt -> HTTP 403
M5 WebDAV GET als bob bob/wz59-lesen.odt -> HTTP 200
M5 WebDAV GET als alice alice/wz59-lesen.odt -> HTTP 403
```

M1 shareDisabledDownload (11:21 bis 11:39 UTC), der Fall des Melders:

```
-- secure view policy im nextcloud.log nachher: 88 (Differenz 11)
      2 GET /ocs/v2.php/apps/findling/files/130?userId=alice 500
      2 GET /ocs/v2.php/apps/findling/files/133?userId=alice 500
      1 GET /ocs/v2.php/apps/findling/files/134?userId=alice 500
      1 GET /ocs/v2.php/apps/findling/files/135?userId=alice 200
      1 GET /ocs/v2.php/apps/findling/files/136?userId=bob 200
      1 GET /ocs/v2.php/apps/findling/files/137?userId=alice 200
      2 GET /ocs/v2.php/apps/findling/files/141?userId=alice 500
      2 GET /ocs/v2.php/apps/findling/files/142?userId=alice 500
      2 GET /ocs/v2.php/apps/findling/files/143?userId=alice 500
      1 GET /ocs/v2.php/apps/findling/files/152?userId=alice 200
      1 GET /ocs/v2.php/apps/findling/files/153?userId=alice 200
      2 WARNING:findling.worker.poller:content gateway refused 5 files of this pass with http status 500 from 2 storages, taken as an outage
-- state.db
file_id=130 | state=failed | reason=gateway_error | attempts=4
file_id=133 | state=failed | reason=gateway_error | attempts=4
file_id=134 | state=failed | reason=gateway_error | attempts=2
file_id=135 | state=indexed | reason=None | attempts=3
file_id=136 | state=indexed | reason=None | attempts=4
file_id=137 | state=indexed | reason=None | attempts=2
file_id=141 | state=failed | reason=gateway_error | attempts=4
file_id=142 | state=failed | reason=gateway_error | attempts=4
file_id=143 | state=failed | reason=gateway_error | attempts=4
file_id=152 | state=indexed | reason=None | attempts=2
file_id=153 | state=indexed | reason=None | attempts=2
-- Nextcloud oc_findling_file_state
file_id=134 | state=failed | reason=gateway_error
```

(130, 133, 141, 142, 143 lagen zur Messzeit belastet in der Warteschlange, `locked_at 2026-11-22 11:37:35, retries=2`, deshalb noch ohne Zeile in `oc_findling_file_state`.)

Abgleich nach M1: Backend gestoppt (Log gesichert als `state-59/exapp-bis-M1.log`), mit `FINDLING_RECONCILE_MIN_INTERVAL_HOURS=1` und `FINDLING_RECONCILE_HOUR=12` (Ortsstunde des Host-Prozesses, `time.localtime()`, CET; 11:40 UTC) neu gestartet:

```
INFO:findling.worker.reconcile:reconcile round walked, mounts=7 slices=7 seen=60 stale=1 missing=0 given_up=0
WARNING:findling.worker.poller:content gateway refused one file, http status 500 for file id 134
INFO:findling.worker.poller:pass finished, claimed=1 indexed=0 skipped=0 failed=1 unchanged=0 requeued=0 embedded=0 committed=0 slots=1 throttled=0
```

attempts danach (11:41 UTC): 130, 133, 141, 142, 143 je 4 (in der Warteschlange gesperrt bis 11:52:35), 134 = 3. M1 bleibt als Endkonfiguration für 45-20 Schritt 0 stehen. Ende: Backend beendet (heartbeat 000), `docker compose -p findling-59 stop` -> `Container findling-59 Stopped`, `docker ps -q` leer, Volume `findling-59-html` und Worktree `wt-165` (sauber, 06a0d7c8) bleiben.

### Modus x Leser -> Ergebnis vorher

Spalten: Datei (ID), Leser laut Claim (`userId` der Gateway-URL), Antwort des Gateways, Urteil in state.db (Nextcloud-Seite: `oc_findling_file_state`, soweit geschrieben), Treffer Besitzer/alice/carol (Unified Search, Provider findling). Wichtig: Die Treffer-Spalte belegt in 1.6.5 kein Lesen. Nach `failed(gateway_error)` bleibt der früher indexierte Inhalt im Index und findbar (Befund I-45-17-02); alle Dateien waren in M0 indexiert. Maßgeblich sind Antwort und Urteil.

| Modus und Fall | Datei | Leser laut Claim | Antwort | Urteil | Treffer B/a/c |
|---|---|---|---|---|---|
| M1 shareDisabledDownload, Freigabe ohne Download | 130, 133, 134 (bob), 141, 142, 143 (dave) | alice | 500, je eine Secure-View-Zeile | failed(gateway_error), Durchlauf als Ausfall gewertet | 1/1/0 (Altbestand) |
| M1, Positivkontrolle mit Download | 135 | alice | 200 | indexed | 1/1/0 |
| M1, eigene Datei ohne Freigabe | 136 | bob | 200 | indexed | 1/0/0 |
| M1, lesende Freigabe mit Download | 137 | alice | 200 | indexed | 1/1/0 |
| M1, Team Folder | 152, 153 | alice | 200 | indexed | 152: 1/1/1, 153: 1/1/0 |
| M2 shareAll, alle Probedateien | alle elf | alice (136: bob) | 500 | failed(gateway_error), Ausfall-Eskalation | wie M0 (Altbestand) |
| M2, eigene Datei des Besitzers | 136 | bob | 500 | failed(gateway_error) | 1/0/0 (Altbestand) |
| M3 allTags, getaggt und geteilt | 130 | alice | 500 | failed(gateway_error) | 1/1/0 (Altbestand) |
| M3, getaggt, nur Besitzer | 136 | bob | 500 | failed(gateway_error) | 1/0/0 (Altbestand) |
| M3, ohne Tag (Gegenkontrolle) | 133, 134, 135, 137, 141, 142, 143, 152, 153 | alice | 200 | indexed | wie M0, carol 1 bei 152 |
| M4 allGroups, Gruppe alice, bob, dave | alle elf | alice (136: bob) | 200 | indexed | wie M3 |
| M5 shareRead, lesende Freigabe | 130, 133, 134, 137, 141, 142, 143 | alice | 500 | failed(gateway_error), Ausfall-Eskalation | wie M0 (Altbestand) |
| M5, Team Folder nur lesend für alle (TF-lesen) | 152 | alice | 500 | failed(gateway_error) | 1/1/1 (Altbestand) |
| M5, Team Folder mit schreibendem Mitglied (TF-gemischt) | 153 | alice (bob schreibt) | 500 | failed(gateway_error) | 1/1/0 (Altbestand) |
| M5, Gegenkontrollen | 135 (`permissions=3`), 136 | alice, bob | 200 | indexed | 1/1/0, 1/0/0 |

carol ist Gegenkontrolle ohne Freigabe: 0 Treffer in jedem Modus für jede Datei außer TF-lesen, deren Mitglied sie ist (ab M3 1, nachdem ihr Mount im Cache stand).

Quellenbewertung von `shouldWatermark` (PermissionManager.php v12.0.2) mit `userId null` (Gateway heute, belegt durch die Probe) und mit der lesenden Person in actAs (Entwurf E1):

- M1 shareDisabledDownload (Z. 230-232): wirkt nur über eine Freigabe mit `download=false` (Z. 190-191), unabhängig von `userId`. null: alice über ihren Freigabe-Mount gesperrt, Beobachtung gleich. Lesende Person: Besitzer bob bzw. dave über den Home-Mount ohne Freigabe -> nicht gesperrt; alice in actAs weiterhin gesperrt. Erwartung 1.7.0: über den Besitzer indexiert.
- M2 shareAll (Z. 217-224): null sperrt jeden Mount außer '/' für jeden richdocuments-Mimetype, auch den Besitzer (Beobachtung: 136 mit Leser bob 500, 40 Dateien von admin 500). Lesende Person: nur der Besitzer selbst (`$ownerId === $userId`, ownerId aus `$storage->getOwner($path)`) liest frei. Erwartung 1.7.0: Dateien mit Home-Mount über den Besitzer in actAs indexiert; Team Folder ohne Besitzer: jeder Kandidat ist nicht Besitzer -> policy_blocked.
- M3 allTags (Z. 248-257): unabhängig von `userId`, greift für jeden Leser. null und lesende Person: gesperrt (Beobachtung 130 und 136). Erwartung 1.7.0 (E2): Besitzer in actAs abgelehnt -> sofort 403 policy, policy_blocked.
- M4 allGroups (Z. 240-247): nur bei `userId !== null` und Mitgliedschaft. null: greift nie (Beobachtung: alles 200, Positivkontrolle WebDAV 403 für Mitglieder). Lesende Person: würde für Mitglieder greifen, wird in 1.7.0 aber nur nach einer Secure-View-Ablehnung erreicht (E1), also beim Indexieren wie heute nie. Offene Restfrage G1/G2.
- M5 shareRead (Z. 226-228 mit Z. 185-188): sperrt, wenn der Cache-Eintrag des lesenden Mounts bzw. die Freigabe kein UPDATE trägt, unabhängig von `userId`. null: alice (nur lesend) gesperrt, Beobachtung gleich; 135 (Freigabe mit UPDATE) und 136 (Home) frei. Lesende Person: lesende Freigabe -> Besitzer über Home-Mount frei (Erwartung indexiert); TF-lesen: alle Mitglieder nur lesend, kein Besitzer -> alle Kandidaten gesperrt, policy_blocked (WebDAV-Gegenprobe bob 403); TF-gemischt: kein Besitzer, Kandidaten alphabetisch alice (gesperrt), bob (schreibend, WebDAV 200) -> indexiert über bob.
- shareTalkPublic (Z. 234-238): nur bei `userId === null` UND Freigabetyp ROOM. Talk (spreed) ist nicht installiert, kein echter Fall. An der Quelle: eine ROOM-Freigabe erzeugt einen Mount für die Teilnehmenden (files_sharing `MountProvider.php` NC v35.0.3 Z. 63 und 382 `IShare::TYPE_ROOM`) und würde im Gateway heute wie shareAll für diesen Mount wirken; der Besitzer-zuerst-Weg aus 1.7.0 liest über den Home-Mount ohne Freigabe, dort greift shareTalkPublic nicht. In actAs (userId gesetzt) greift shareTalkPublic nie.
- link-Modi (`watermark_linkAll`, `watermark_linkRead`, `watermark_linkSecure`, `watermark_linkTags`, Z. 194-215): nur bei `getShareType() === IShare::TYPE_LINK`. Link-Freigaben erzeugen keinen Mount im Mount-Cache: der files_sharing-MountProvider fragt nur USER, GROUP, CIRCLE, ROOM und DECK ab (Z. 60-64 und 379-383, kein TYPE_LINK). Das Gateway liest nur über Mounts aus dem Mount-Cache, also greifen die link-Modi beim Indexieren nie, weder mit null noch in actAs.

Abweichung zwischen Quelle und Beobachtung: keine. Jede Beobachtung in M1 bis M5 entspricht der Bedingung an der Quelle mit `userId null`.

### Befunde 45-17 (Nachbau)

| ID | Schwere | Befund | Beleg | Empfehlung |
|---|---|---|---|---|
| I-45-17-01 | INFO, relevant für 45-18 | Ab fünf Ablehnungen mit gleichem Status aus zwei Speichern wertet 1.6.5 einen Durchlauf als Ausfall: Urteile verfallen, fünf Zeilen werden belastet und bleiben 900 s gesperrt (QueueMapper::LOCK_TIMEOUT). Das trat in M1, M2 und M5 auf und verlängert jeden Zyklus auf rund 15 Minuten. Der Kommentar zu GATEWAY_OUTAGE_MIN_STORAGES (poller.py v1.6.5) sagt "401 and 403 do not escalate at once" | Backend-Zeilen "refused 5 files of this pass with http status 500 from 2 storages, taken as an outage", `locked_at 11:37:35, retries=2` | In 45-18/45-20 belegen, dass 403 policy nicht als Ausfall eskaliert (Test und echter Lauf mit mehr als fünf gesperrten Dateien auf zwei Speichern) |
| I-45-17-02 | INFO, relevant für 45-22 (E3) | Nach `failed(gateway_error)` bleibt früher indexierter Inhalt im Index und findbar. Eine Datei, die vor dem Einschalten des Wasserzeichens indexiert war, findet alice weiter über ihren alten Inhalt, obwohl sie jetzt unter Secure View steht (ob mit Ausschnitt, wurde hier nicht gemessen) | Treffer 1/1/0 in M1, M2, M5 trotz `failed` in state.db | In 45-22 (E3) berücksichtigen: die Unterdrückung der Ausschnitte muss auch für solche Altbestände gelten |
| I-45-17-03 | INFO, Korrektur einer Plan-Annahme | files_accesscontrol wirft beim fopen sehr wohl eine ForbiddenException ("Access denied by access control"), wenn der Knoten zuvor lesbar aufgelöst wurde | StorageWrapper.php v6.0.1 Z. 241-253, Operation.php Z. 118 | Keine Änderung am Entwurf: fällt unter "jede andere ForbiddenException -> 403 policy" (fail-closed); in 45-20 Schritt C echt prüfen |
| I-45-17-04 | INFO, vorbestehend | Der Mount-Cache kennt eine Person erst nach ihrem ersten Dateisystem-Aufbau: carol fehlte für TF-lesen bis zu ihrer ersten Anmeldung, und ihre ACL im Index fehlte bis zum nächsten Lesen der Datei. Für 1.7.0: eine solche Person ist auch kein Kandidat in readingOrder | Mount-Probe vorher/nachher, Treffer carol bei 152 erst ab M3 | Kein Fix in 45-17; im Docblock von ReaderCandidates nennen |
| I-45-17-05 | INFO, relevant für 45-20 Schritt 0 und Frage d | attempts trägt den Verlauf aller Modi: am Ende von M1 stehen 130, 133, 141, 142, 143 schon bei 4, 134 nach dem Abgleich bei 3; auch indexierte Dateien haben attempts > 1 (136: 4) | state.db nach M1 und nach dem Abgleich | Die Serie in 45-20 Schritt 0 beginnt nicht bei 1; vor Schritt 0 den Stand neu lesen und die Erwartung daran ausrichten |

### RED und GREEN 45-17

Plan 45-17 Task 3, 2026-11-22, nach den Owner-Entscheiden von 11:52 UTC (Texte wie im Entwurf, G1, c1, d1; G1 heißt: kein zusätzlicher Fall für allGroups). Docker seriell, vor jedem Start `test -z "$(docker ps -q)"` leer; findling-59 lief zu keiner Zeit.

Quellen zur Besitzererkennung (`gh api repos/nextcloud/server/contents/<pfad>?ref=stable3x`, abgelegt unter `<scratchpad>/nc-src/`): `lib/public/Files/Config/ICachedMountInfo.php` hat in stable33, stable34 und stable35 `getMountPoint(): string` (@since 9.0.0) und `getMountProvider(): string` (@since 24.0.0), stable33 und stable34 byte-gleich (SHA-256 b1567a04...), stable35 nur mit einer Zeile mehr im Kopf. `lib/private/Files/Mount/LocalHomeMountProvider.php` (stable33 Z. 27, stable34 Z. 31, stable35 Z. 32) und `ObjectHomeMountProvider.php` (Z. 43, 44, 45) bauen `new HomeMountPoint($user, ..., '/' . $user->getUID(), ..., self::class)`, Namensraum `OC\Files\Mount` in allen drei. Im Mount-Cache steht das als `/<uid>/` (Mount-Cache-Probe oben). Daraus `HOME_MOUNT_PROVIDERS` in ReaderCandidates mit genau diesen zwei Klassennamen als Strings.

Schritt 1, reiner Refactor (Commit 92a662c7): `php/lib/Service/ReaderCandidates.php` neu mit `MAX_READER_TRIES = 20` (öffentlich, einzige Quelle), `MAX_USERS = 500`, `forFile()` (Körper von usersFor unverändert, owner null) und `readingOrder()` (array_slice); QueueService bekommt ReaderCandidates statt IUserMountCache im Konstruktor, usersFor() und readerOf() delegieren. Tests nur in der Konstruktion angepasst (QueueServiceTest zwei Stellen, QueueServiceReaderTest eine). Ergebnisse vor dem Commit: `bash scripts/dev/phpunit_docker.sh` -> `OK (1302 tests, 8363 assertions)`; `bash scripts/dev/php_gates_docker.sh all` -> Exit 0 (psalm, cs, zizmor, actionlint grün); sieben Strukturgates `819 passed`; ruff, ruff format (260 Dateien), pyright (0 errors), vulture grün. Baumhash php/: Rezept und unabhängige Pipeline `5b54386c...` mit 137 Dateien, Positivkontrolle `git archive 89cc8ddf` -> `85ba0c66...` mit 136.

Schritt 2, RED (nicht committet, lokal grün vor jedem Commit): neue Fälle in `ReaderCandidatesTest.php` (neu), `GatewayReaderTest.php` (neu), `QueueServiceReaderTest.php` und `GatewayControllerTest.php`, dazu die Testhilfe `SecureViewRefusal.php` (die Ablehnungen als Ausnahmen mit gesetztem Trace, ohne richdocuments zu laden). Damit nur die neuen Fälle rot sind, lief RED gegen ein Gerüst: GatewayReader mit dem Öffnen von 1.6.5 (keine Erkennung, kein zweites Öffnen, `isSecureViewRefusal` immer false), GatewayController schon über GatewayReader, ReaderCandidates ohne Besitzererkennung. `bash scripts/dev/phpunit_docker.sh --filter 'ReaderCandidatesTest|QueueServiceReaderTest|GatewayReaderTest|GatewayControllerTest'` -> `Tests: 75, Assertions: 364, Errors: 12, Failures: 12.`, wörtlich:

```
Errors:
1) GatewayReaderTest::testASecureViewRefusalOpensTheFileAgainAsTheOwnerInsideActAs
   OCP\Files\ForbiddenException: Download blocked due the secure view policy
2) GatewayReaderTest::testAnOwnerTheSecureViewRefusesAsWellEndsWithPolicyAndNobodyElseIsAsked
   OCP\Files\ForbiddenException: Download blocked due the secure view policy
3) GatewayReaderTest::testWithoutAnOwnerAtMostTwentyReadersAreAskedAndThenPolicy
   OCP\Files\ForbiddenException: Download blocked due the secure view policy
4) GatewayReaderTest::testTheSameMessageWithTheFrameOnlyFurtherUpIsPolicyWithoutAnotherOpen
   OCP\Files\ForbiddenException: Download blocked due the secure view policy
5) GatewayReaderTest::testTheRightFrameWithAnotherMessageIsPolicyWithoutAnotherOpen
   OCP\Files\ForbiddenException: Access denied by access control
6) GatewayReaderTest::testARefusalOfAccessControlIsPolicyWithoutAnotherOpen
   OCP\Files\ForbiddenException: Access denied by access control
7) GatewayReaderTest::testAnotherForbiddenExceptionAtTheSecondReaderEndsWithoutAThird
   OCP\Files\ForbiddenException: Download blocked due the secure view policy
8) GatewayReaderTest::testAnOwnerWhoDoesNotResolveTheFileInActAsEndsWithPolicy
   OCP\Files\ForbiddenException: Download blocked due the secure view policy
9) GatewayReaderTest::testAnOwnerWhoseFolderCannotBeBuiltEndsWithPolicy
   OCP\Files\ForbiddenException: Download blocked due the secure view policy
10) GatewayReaderTest::testWithoutAnOwnerAReaderWhoDoesNotResolveIsPassedOver
   OCP\Files\ForbiddenException: Download blocked due the secure view policy
11) GatewayReaderTest::testADeletedReaderIsPassedOverAndNeverTurnsIntoNotFound
   OCP\Files\ForbiddenException: Download blocked due the secure view policy
12) GatewayReaderTest::testAStorageThatIsNotAvailableAtTheOpenOfTheOwnerTravelsUp
   OCP\Files\ForbiddenException: Download blocked due the secure view policy
Failures:
1) GatewayControllerTest::testASecureViewRefusalIsReadAsTheOwnerAndLeavesOneInfoLine
   Psr\Log\LoggerInterface::error('Findling: unknown error reading a file', [...]): void was not expected to be called.
2) GatewayControllerTest::testARefusalForEveryoneAskedIsA403WithTheRefusalHeader
   Psr\Log\LoggerInterface::error('Findling: unknown error reading a file', [...]): void was not expected to be called.
3) GatewayControllerTest::testAnotherForbiddenExceptionAtTheFirstOpenIsA403PolicyWithoutAnotherOpen
   Failed asserting that 500 is identical to 403.
4) GatewayControllerTest::testASharingViolationAtTheOpenOfTheOwnerIsA422AsBefore
   Psr\Log\LoggerInterface::error('Findling: unknown error reading a file', [...]): void was not expected to be called.
5) GatewayControllerTest::testADeletedReaderOfTheSecondRoundIsNeverA404
   Failed asserting that 500 is identical to 403.
6) GatewayReaderTest::testAStorageThatIsNotAvailableAtTheOpenOfAReaderTravelsUp
   Failed asserting that exception of type "OCP\Files\ForbiddenException" matches expected exception "OCP\Files\StorageNotAvailableException". Message was: "Download blocked due the secure view policy" at
7) GatewayReaderTest::testTheRecognitionAsksForTheExceptionClassTheMessageAndTheFirstFrame
   Failed asserting that false is true.
8) QueueServiceReaderTest::testTheOwnerIsTheReaderBeforeAnAlphabeticallyEarlierRecipient
   Failed asserting that two strings are identical.
9) ReaderCandidatesTest::testTheOwnerIsAskedFirstAndTheOthersKeepTheirOrder
   Failed asserting that two arrays are identical.
10) ReaderCandidatesTest::testAnOwnerBehindTheCapIsFirstAndTheOwnerCounts
   Failed asserting that two arrays are identical.
11) ReaderCandidatesTest::testTheHomeMountOfTheLocalProviderNamesTheOwner
   Failed asserting that two arrays are identical.
12) ReaderCandidatesTest::testTheHomeMountOfTheObjectStoreProviderNamesTheOwner
   Failed asserting that null is identical to 'dave'.
```

Alle bestehenden Fälle der vier Dateien waren grün. Grün schon im RED, weil das Verhalten von 1.6.5 sie erfüllt (Regressionswächter, keine neuen Aussagen): GatewayReaderTest "Öffnen außerhalb actAs gelingt" (asked 0, keine Mount-Abfrage), "benannte Person löst nicht auf -> not_found", "unbekannte benannte Person -> NoUserException"; GatewayControllerTest "fremde ExApp -> 403 ohne Kopf", "StorageNotAvailable beim Besitzer -> 500" (im Gerüst 500 über die nicht abgefangene ForbiddenException, erst die Mutationen unten zeigen den Fall des Besitzers), "unbekannte benannte Person -> 404, kein zweites Öffnen"; QueueServiceReaderTest "Besitzer löst nicht auf -> alice"; ReaderCandidatesTest die Fälle ohne Besitzer (Freigabe, Team Folder, extern, Provider leer, fremder Home-Mount, 501 Mounts, Ausnahme im Mount-Cache, alphabetische Reihenfolge).

Schritt 3, Fix: ReaderCandidates erkennt den Besitzer in derselben Schleife (Mount-Point exakt `'/' . $uid . '/'` und Provider in `HOME_MOUNT_PROVIDERS`, erster Treffer), Kappung beendet die Schleife auch für den Besitzer (Docblock), `Node::getOwner()` im Docblock bewertet und verworfen; `readingOrder()` Besitzer zuerst, Rest in gegebener Reihenfolge, höchstens 20 insgesamt. QueueService::readerOf() bekommt den Besitzer und fragt `readingOrder($userIds, $owner)`; userIds bleibt die sortierte Vorfilterliste. GatewayReader (neu) mit `open()`, `isSecureViewRefusal()` (instanceof ForbiddenException, Nachricht exakt, `$e->getTrace()[0]` class und function als Strings), zweitem Öffnen nur nach Secure-View-Ablehnung in actAs (Besitzer allein, E2; ohne Besitzer readingOrder bis 20, Überspringen bei Throwable oder null mit debug-Zeile nur `fileId` und `class`), jede andere ForbiddenException -> policy. GatewayController: rejectForeignCaller() erste Anweisung unverändert, Antwort `not_found` -> bestehender 404-Body, `policy` -> warning `Findling: reading a file was blocked by a rule` mit `fileId` und `asked`, 403 `['error' => 'Reading this file is blocked by a rule.']` und Kopf `X-Findling-Refusal: policy` (öffentliche Konstanten `REFUSAL_HEADER`, `REFUSAL_POLICY`); Erfolg nach zweitem Öffnen: info `Findling: read a file as a reader of it after secure view refused the first open` mit `fileId` und `asked`. Prime- und Stream-Logik, 422 und 500 unverändert.

GREEN: `--filter 'ReaderCandidatesTest|QueueServiceReaderTest|GatewayReaderTest|GatewayControllerTest'` -> `OK (75 tests, 492 assertions)`; volle Suite `OK (1342 tests, 8601 assertions)` (`1342 tests executed, floor 28`).

Mutationsgegenproben (`<scratchpad>/mutations.sh` mit `mutate.py`, je Mutation die vier Testdateien gefiltert, danach beide Quelldateien aus der Sicherung zurück und SHA-256 vorher/nachher verglichen):

```
== frame_removed (php/lib/Service/GatewayReader.php) exit=1 restored_identical=yes
Tests: 75, Assertions: 488, Failures: 2.
  1) GatewayReaderTest::testTheSameMessageWithTheFrameOnlyFurtherUpIsPolicyWithoutAnotherOpen
  2) GatewayReaderTest::testTheRecognitionAsksForTheExceptionClassTheMessageAndTheFirstFrame
== any_frame (php/lib/Service/GatewayReader.php) exit=1 restored_identical=yes
Tests: 75, Assertions: 488, Failures: 2.
  1) GatewayReaderTest::testTheSameMessageWithTheFrameOnlyFurtherUpIsPolicyWithoutAnotherOpen
  2) GatewayReaderTest::testTheRecognitionAsksForTheExceptionClassTheMessageAndTheFirstFrame
== no_stop_after_owner (php/lib/Service/GatewayReader.php) exit=1 restored_identical=yes
Tests: 75, Assertions: 487, Failures: 4.
  1) GatewayControllerTest::testARefusalForEveryoneAskedIsA403WithTheRefusalHeader
  2) GatewayReaderTest::testAnOwnerTheSecureViewRefusesAsWellEndsWithPolicyAndNobodyElseIsAsked
  3) GatewayReaderTest::testAnOwnerWhoDoesNotResolveTheFileInActAsEndsWithPolicy
  4) GatewayReaderTest::testAnOwnerWhoseFolderCannotBeBuiltEndsWithPolicy
== no_owner_first (php/lib/Service/ReaderCandidates.php) exit=1 restored_identical=yes
Tests: 75, Assertions: 489, Failures: 3.
  1) QueueServiceReaderTest::testTheOwnerIsTheReaderBeforeAnAlphabeticallyEarlierRecipient
  2) ReaderCandidatesTest::testTheOwnerIsAskedFirstAndTheOthersKeepTheirOrder
  3) ReaderCandidatesTest::testAnOwnerBehindTheCapIsFirstAndTheOwnerCounts
== open_outside_actas (php/lib/Service/GatewayReader.php) exit=1 restored_identical=yes
Tests: 75, Assertions: 485, Failures: 7.
  1) GatewayControllerTest::testASecureViewRefusalIsReadAsTheOwnerAndLeavesOneInfoLine
  2) GatewayControllerTest::testARefusalForEveryoneAskedIsA403WithTheRefusalHeader
  3) GatewayReaderTest::testASecureViewRefusalOpensTheFileAgainAsTheOwnerInsideActAs
  4) GatewayReaderTest::testAnOwnerTheSecureViewRefusesAsWellEndsWithPolicyAndNobodyElseIsAsked
  5) GatewayReaderTest::testWithoutAnOwnerAtMostTwentyReadersAreAskedAndThenPolicy
  6) GatewayReaderTest::testAnotherForbiddenExceptionAtTheSecondReaderEndsWithoutAThird
  7) GatewayReaderTest::testWithoutAnOwnerAReaderWhoDoesNotResolveIsPassedOver
```

Zuordnung zu den Vorgaben: Frame-Bedingung entfernt (`frame_removed`) -> "gleiche Nachricht ohne Frame an erster Stelle" rot; irgendein Frame statt `getTrace()[0]` (`any_frame`) -> "Frame nur weiter oben" rot; Abbruch nach dem Besitzer entfernt (`no_stop_after_owner`) -> allTags-Fall rot; Besitzer-Vorzug entfernt (`no_owner_first`) -> Reihenfolgefall rot; actAs um das fopen entfernt (`open_outside_actas`) -> "aktive Person ist bob" rot. Nach jeder der fünf Mutationen waren GatewayReader.php und ReaderCandidates.php wieder byte-gleich (restored_identical=yes).

Gates am Stand des Fix-Commits: sieben Strukturgates `819 passed`; ruff check grün, ruff format `260 files already formatted`, pyright latest `0 errors, 0 warnings, 0 informations`, vulture grün; `bash scripts/dev/php_gates_docker.sh all` -> Exit 0 (`psalm taint gate green against 3 nextcloud/ocp tags`, je `No errors found!` und `0 findings, probe found 3` für v33.0.9, v34.0.6, v35.0.3; `php-cs-fixer: no violation`; zizmor und actionlint grün). Baumhash php/: Rezept und unabhängige Pipeline `ef4f5a19...` mit 141 Dateien, Positivkontrolle `git archive 92a662c7` -> `5b54386c...` mit 137.

Hinweis zur verify-Zeile: Der grep auf `OCA\\\\Richdocuments\\\\Storage\\\\SecureViewWrapper` scheitert, wenn die Befehlszeile durch die Werkzeugschicht des Ausführers läuft (sie halbiert Backslashes: `printf '%s' "OCA\\\\Richdocuments"` gab `OCA\Richdocuments`). Aus einer Skriptdatei (`<scratchpad>/verify_greps.sh`, die Zeile wörtlich) gab dieselbe Kette `GREPS_OK`; die Datei enthält `'OCA\Richdocuments\Storage\SecureViewWrapper'` (Bytes per `od -c` geprüft).

Befunde Task 3:

| ID | Schwere | Befund | Beleg | Empfehlung |
|---|---|---|---|---|
| I-45-17-06 | INFO | Die Spalte `path` eines Auftrags folgt jetzt dem Leser: liest der Besitzer, ist der Pfad relativ zu seinem Ordner, nicht mehr zu dem der alphabetisch ersten Empfängerin. Gewollt (Behavior "path relativ zu bobs Ordner"); docKey kommt weiter aus oc_filecache und ist unberührt | QueueServiceReaderTest `testTheOwnerIsTheReaderBeforeAnAlphabeticallyEarlierRecipient` | In 45-20 an einem echten Treffer (Titel, Pfad, Link) gegenprüfen |
| I-45-17-07 | INFO | `asked` zählt die Leser der zweiten Runde einschließlich übersprungener; die benannte Person ohne Besitzer wird in der zweiten Runde in actAs erneut gefragt (sie steht in readingOrder) | GatewayReaderTest `testWithoutAnOwnerAReaderWhoDoesNotResolveIsPassedOver` (asked 3) | So belassen: ein Versuch mehr, dafür eine Reihenfolge für Claim und Gateway; Zeitmessung mit 20 Kandidaten in 45-20 (T-45-61) |

### RED und GREEN 45-18

Plan 45-18, 2026-11-22, nach den Owner-Entscheiden von 11:52 UTC (Texte 1 bis 3 wörtlich, c1, Serie bis 3 Nächte vom 08:47). Docker seriell, vor jedem Start `test -z "$(docker ps -q)"` leer.

Task 1 (Vokabular, Generation 4, Texte, Gates), RED (nicht committet, nur die neuen und die mit der Generation wandernden Fälle):

`PYTHONUTF8=1 uv run --no-sync python -m pytest -q tests/test_extract_errors.py tests/test_queue_client.py tests/test_admin_ui_contract.py tests/test_store_metadata.py` -> `24 failed, 576 passed in 3.43s`, wörtlich:

```
FAILED tests/test_extract_errors.py::test_policy_blocked_of_plan_45_18_is_a_failure_and_never_a_decision
FAILED tests/test_queue_client.py::test_the_container_knows_the_generations_2_3_and_4
FAILED tests/test_queue_client.py::test_a_companion_announcing_a_known_generation_reads_as_that_generation[4]
FAILED tests/test_queue_client.py::test_verdicts_is_a_closed_set_of_three_generations[4-4]
FAILED tests/test_queue_client.py::test_policy_blocked_reaches_only_a_companion_of_generation_4[profile0-gateway_error]
FAILED tests/test_queue_client.py::test_policy_blocked_reaches_only_a_companion_of_generation_4[profile1-gateway_error]
FAILED tests/test_queue_client.py::test_policy_blocked_reaches_only_a_companion_of_generation_4[profile2-gateway_error]
FAILED tests/test_queue_client.py::test_towards_generation_4_the_skipped_codes_of_3_keep_their_name
FAILED tests/test_queue_client.py::test_the_skipped_fallback_per_generation
FAILED tests/test_queue_client.py::test_the_failed_fallback_per_generation
FAILED tests/test_queue_client.py::test_every_skipped_fallback_is_a_skipped_pair_that_generation_stores[4]
FAILED tests/test_queue_client.py::test_every_failed_fallback_is_a_failed_pair_that_generation_stores[None]
FAILED tests/test_queue_client.py::test_every_failed_fallback_is_a_failed_pair_that_generation_stores[2]
FAILED tests/test_queue_client.py::test_every_failed_fallback_is_a_failed_pair_that_generation_stores[3]
FAILED tests/test_queue_client.py::test_every_failed_fallback_is_a_failed_pair_that_generation_stores[4]
FAILED tests/test_admin_ui_contract.py::test_policy_blocked_has_its_row_and_its_sentences_in_every_catalogue
FAILED tests/test_admin_ui_contract.py::test_the_remedy_of_unreadable_names_the_owner_first_in_every_catalogue
FAILED tests/test_admin_ui_contract.py::test_the_number_in_the_remedy_of_unreadable_is_max_reader_tries
FAILED tests/test_admin_ui_contract.py::test_the_reader_tries_gate_reports_a_number_that_is_not_the_constant
FAILED tests/test_admin_ui_contract.py::test_the_three_in_both_retry_remedies_is_gateway_error_retries
FAILED tests/test_admin_ui_contract.py::test_the_retry_gate_reports_another_count
FAILED tests/test_admin_ui_contract.py::test_the_german_catalogue_covers_both_german_language_codes
FAILED tests/test_store_metadata.py::test_the_full_text_1_6_3_carries_its_date_the_accepted_sentences_and_the_release_note
FAILED tests/test_store_metadata.py::test_the_superseded_sentence_is_the_old_remedy_of_unreadable_and_an_accepted_one
```

Die zwei Fehl-Sample-Fälle der Zahl-Gates (`..._reports_a_number_that_is_not_the_constant`, `..._reports_another_count`) waren im RED mit KeyError rot, weil die Sätze noch in keinem Katalog standen; nach GREEN prüfen sie das Fehl-Sample selbst (21 statt 20 in `es.json`, "vier keer" in `nl.js`, 4 statt 3). Die 1.6.3-Fehl-Samples (`test_a_sentence_without_its_key_and_not_on_the_superseded_list_is_reported`, `test_a_superseded_sentence_the_catalogue_still_carries_is_reported`, `test_a_superseded_sentence_whose_german_left_the_listing_is_reported`, `test_a_superseded_sentence_is_checked_against_the_listing_only`) laufen auf der Stichprobe und waren schon im RED grün: sie prüfen den Gate selbst, nicht den Baum; rot wurde der Gate am echten Baum (`test_the_full_text_1_6_3_...`: `still has an entry for the sentence ..., superseded in 1.7.0`).

`bash scripts/dev/phpunit_docker.sh --filter 'ProfileControllerTest|FileStateServiceCoverageTest|AdminViewServiceTest'` -> `Tests: 239, Assertions: 1097, Failures: 5.`, wörtlich:

```
1) OCA\Findling\Tests\Unit\AdminViewServiceTest::testTheRowOfPolicyBlockedCarriesTheApprovedWording
Failed asserting that null is identical to Array &0 [
2) OCA\Findling\Tests\Unit\AdminViewServiceTest::testTheRemedyOfUnreadableNamesTheOwnerFirst
Failed asserting that two strings are identical.
3) OCA\Findling\Tests\Unit\AdminViewServiceTest::testARefusalByARuleNeverCarriesTheSmbHint
Failed asserting that two strings are identical.
4) OCA\Findling\Tests\Unit\FileStateServiceCoverageTest::testARefusalByARuleIsAFailureTheStoreAccepts
Failed asserting that false is true.
5) OCA\Findling\Tests\Unit\ProfileControllerTest::testTheAnswerAnnouncesTheVerdictGeneration
Failed asserting that 3 is identical to 4.
```

`testARefusalByARuleIsNeverADecision` (skipped(policy_blocked) abgelehnt, keine Anweisung) war im RED grün, weil record() das Paar schon vor dem Fix ablehnte (unbekannter Code); er bleibt als Wächter.

Zwei Nachzügler, die der gefilterte RED nicht zeigen konnte, weil sie den alten Wert 3 wörtlich tragen und erst mit dem Fix wanderten: sieben Erwartungs-Arrays in `ProfileControllerTest.php` (`'verdicts' => 3` -> `4`, im vollen PHPUnit-Lauf vor dem Commit `Failures: 13`, alle Datensätze dieser sieben Fälle) und `test_phase31_audit.py::test_no_code_reaches_a_companion_that_does_not_know_it` (volle pytest-Suite `7 failed, 7295 passed, 305 skipped`, alle sieben Parameter dieses Falls). Beide sind angepasst (Abweichungen in 45-18-SUMMARY.md).

Regression durch die Generation (Rule 1): `poller.py` startete den Nachlauf von 1.5 nur bei `choice.verdicts == VERDICTS_GENERATION`. Mit 4 hätte ein 1.7-Container vor einer 1.6-Begleit-App (3) ihn nie gestartet. RED nach dem Hochsetzen der Konstante, vor dem Fix: `tests/test_poller.py -k catch_up` -> `1 failed, 6 passed` (`test_from_generation_3_on_the_catch_up_hands_the_refused_zip_back_once[3]`). Fix: `CATCHUP_MIN_GENERATION: Final = 3`, Bedingung `choice.verdicts >= CATCHUP_MIN_GENERATION`; danach `7 passed`.

Fix in einem Zug: errors.py `POLICY_BLOCKED` (Reason und failed-Menge), repo.py STATE_REASONS, FileStateService (REASONS und STATE_REASONS['failed']), AdminViewService (Zeile `policy_blocked` mit Label und Abhilfe hinter gateway_error, neue Abhilfe von unreadable, Docblock 26 statt 25 Codes), queue.py Generation 4 (KNOWN {2, 3, 4}, skipped-Tabelle 4 leer (W3), failed-Tabelle 4 leer und 3/2/None `policy_blocked -> gateway_error`), ProfileController `VERDICTS_GENERATION = 4` mit Docblock, 18 Katalogdateien (zwei neue Schlüssel hinter der Abhilfe von gateway_error, der unreadable-Schlüssel an Ort und Stelle ersetzt; DE und FR wörtlich wie freigegeben, es, it, nl, pt_BR, pt_PT, zh_TW nach den Wortwahl-Tabellen der Sprachdokumente), sechs Sprachtabellen samt Nachtrag (fünf deutsch, docs/l10n-chinese.md englisch mit Schlüsselzahl 382), Schlüsselzahl 380 -> 382, Docblock von ReaderCandidates::forFile() (I-45-17-04, nur Kommentar), Baumhashes.

Gates neu: `scan_reader_tries` (jede Zahl im unreadable-Satz in Schlüssel und allen 18 Katalogen gleich `MAX_READER_TRIES` aus ReaderCandidates.php, Fehl-Sample 21 -> rot), `scan_retry_words` (die Drei in Worten in den Abhilfen von policy_blocked und gateway_error in allen 18 Katalogen gleich `GATEWAY_ERROR_RETRIES`, Fehl-Samples "vier keer" und 4 -> rot), 1.6.3-Gate nach c1 (`SUPERSEDED_IN_1_7_0` mit dem alten unreadable-Satz und seinem abgenommenen deutschen Wortlaut; der Satz wird nur gegen docs/store-listing.md geprüft, ein Katalog, der ihn noch trägt, ist ein Verstoß; Fehl-Samples: abgelöster Satz ohne Listeneintrag und ohne Schlüssel -> rot, Satz in der Liste und noch im Katalog -> rot, deutscher Wortlaut nicht mehr im Abschnitt -> rot).

GREEN:
verify-Zeile von Task 1 wörtlich aus `<scratchpad>/v18_t1.sh` -> Exit 0: die neun pytest-Dateien `1262 passed, 12 skipped`; ruff `All checks passed!`, ruff format `260 files already formatted`, pyright latest `0 errors, 0 warnings, 0 informations`, vulture ohne Fund; `bash scripts/dev/phpunit_docker.sh` -> `OK (1347 tests, 8616 assertions)` (`1347 tests executed, floor 28`); `bash scripts/dev/php_gates_docker.sh all` -> `psalm taint gate green against 3 nextcloud/ocp tags` (je `No errors found!`, `0 findings, probe found 3`), `php-cs-fixer: no violation`, zizmor und actionlint grün. Dazu `tests/test_poller.py tests/test_profile_wire.py tests/test_phase31_audit.py` -> `360 passed, 1 skipped`; die volle pytest-Suite vor den zwei Nachzüglern `7 failed, 7295 passed, 305 skipped` (nur der Fall aus test_phase31_audit.py), danach dieser Fall `98 passed` über die Datei.

Baumhashes: php/ Rezept und unabhängige Pipeline `34d00c1f...` mit 141 Dateien, Positivkontrolle `git archive 006c2983` -> `ef4f5a19...` mit 141; backend/src/findling Rezept und Pipeline `7249fe45...` mit 83 Dateien, Positivkontrolle `git archive 006c2983` -> `76a4f649...` mit 83.

Task 2 (Container-Verhalten), RED (nicht committet, nur neue Fälle; der Klassenname wird in den Tests über das Modul gelesen, damit RED ein roter Fall und kein Importfehler ist):

`PYTHONUTF8=1 uv run --no-sync python -m pytest -q tests/test_gateway_client.py tests/test_poller.py tests/test_store_repo.py tests/test_reconcile.py` -> `18 failed, 526 passed, 1 skipped in 20.92s`, wörtlich:

```
FAILED tests/test_gateway_client.py::test_a_403_with_the_policy_header_is_a_refusal_by_a_rule[X-Findling-Refusal]
FAILED tests/test_gateway_client.py::test_a_403_with_the_policy_header_is_a_refusal_by_a_rule[x-findling-refusal]
FAILED tests/test_gateway_client.py::test_a_403_with_the_policy_header_is_a_refusal_by_a_rule[X-FINDLING-REFUSAL]
FAILED tests/test_gateway_client.py::test_the_refusal_header_is_the_one_the_gateway_sends
FAILED tests/test_poller.py::test_a_refusal_by_a_rule_is_failed_policy_blocked_and_the_pass_goes_on
FAILED tests/test_poller.py::test_five_refusals_by_a_rule_over_three_storages_are_five_verdicts[True-False]
FAILED tests/test_poller.py::test_policy_refusals_from_two_storages_never_escalate_to_an_outage
FAILED tests/test_store_repo.py::test_entering_a_refusal_by_a_rule_starts_the_streak_at_one
FAILED tests/test_store_repo.py::test_a_refusal_by_a_rule_continues_the_streak_of_every_other_refusal
FAILED tests/test_store_repo.py::test_gateway_retry_candidates_hold_a_refusal_by_a_rule
FAILED tests/test_store_repo.py::test_the_renewal_of_1_7_0_brings_a_spent_refusal_of_1_6_back_once
FAILED tests/test_store_repo.py::test_a_database_without_either_mark_renews_under_both_with_a_line_each
FAILED tests/test_store_repo.py::test_the_renewal_of_1_7_0_alone_leaves_the_mark_of_1_6_3_to_its_own_run
FAILED tests/test_reconcile.py::test_a_refusal_by_a_rule_is_retried_like_every_refusal[policy_blocked-1-True]
FAILED tests/test_reconcile.py::test_a_refusal_by_a_rule_is_retried_like_every_refusal[policy_blocked-3-True]
FAILED tests/test_reconcile.py::test_a_refusal_by_a_rule_is_retried_like_every_refusal[gateway_error-1-True]
FAILED tests/test_reconcile.py::test_a_refusal_by_a_rule_is_retried_like_every_refusal[gateway_error-3-True]
FAILED tests/test_reconcile.py::test_a_spent_refusal_of_1_6_is_work_again_after_the_renewal_of_1_7_0[True-True]
```

Im RED grün und als Wächter behalten: `test_any_other_refusal_stays_an_ordinary_one` (403 ohne Kopf, Wert `Policy`, `other`, leer, 500/422/401 mit Kopf bleiben `GatewayRefused`, Body nie gelesen), `test_the_refusal_gate_reports_another_value` (Fehl-Sample des Kopf-Gates auf der PHP-Quelle: anderer Wert -> rot), die Gegenkontrolle `[False-True]` (fünf normale 403 über drei Speicher eskalieren), die gesperrten Fälle `[...-4-False]` und `[False-False]` der Reconcile-Tests.

Fix: client.py `GATEWAY_REFUSAL_HEADER = "X-Findling-Refusal"`, `GATEWAY_REFUSAL_POLICY = "policy"`, `class GatewayPolicyRefused(GatewayRefused)`, der Kopf wird nur bei 403 und nur mit exakt diesem Wert gelesen (`response.headers.get`, httpx sucht Kopfnamen ohne Groß- und Kleinschreibung), der Body nie. poller.py: `_count_refusal` kehrt bei `GatewayPolicyRefused` vor jeder Zählung zurück (Docstring: viele Dateien unter einem Wasserzeichen sind viele Dateien, kein Ausfall; I-45-17-01), `_refusal_outcome` -> failed(policy_blocked), Kommentar an der Aufrufstelle; kein eigener except-Zweig, die Logzeile `content gateway refused one file, http status %d for file id %d` ist byte-gleich. repo.py: `_RECORD_SQL` und `gateway_retry_candidates` mit `reason IN ('gateway_error', 'policy_blocked')`, `REFUSAL_RENEW_MARK_1_7_0 = "refusal_streaks_1_7_0"` mit Kommentar, `renew_refusal_streaks()` erneuert je Marke einmal in eigener Transaktion (1.6.3 zuerst, unverändert), Rückgabe die Summe der Zeilen der gelaufenen Marken oder None; Logzeile `refusal streaks renewed once after the update, rows=%d mark=%s` (Zähler vor der Marke, damit die Diagnose in scripts/ci/coverage_e2e.sh mit `grep -o '... rows=[0-9]*'` weiter trifft). reconcile.py: nur Kommentare, `GATEWAY_ERROR_RETRIES` bleibt 3.

GREEN:
verify-Zeile von Task 2 wörtlich aus `<scratchpad>/v18_t2.sh` -> Exit 0: die sieben pytest-Dateien `784 passed, 1 skipped`; ruff `All checks passed!`, ruff format grün, pyright latest `0 errors, 0 warnings, 0 informations`, vulture ohne Fund; `bash scripts/dev/phpunit_docker.sh` -> `OK (1347 tests, 8616 assertions)`; `bash scripts/dev/php_gates_docker.sh all` -> Psalm-Taint gegen v33.0.9, v34.0.6, v35.0.3 je `No errors found!` und `0 findings, probe found 3`, `php-cs-fixer: no violation`, zizmor und actionlint grün. Volle pytest-Suite vor dem Commit: `7333 passed, 305 skipped, 3 warnings in 739.70s`.

Mutationsgegenprobe (`<scratchpad>/mut18.sh`): die Rückkehr vor der Zählung für `GatewayPolicyRefused` entfernt (Bedingung wieder nur `refused.status == GATEWAY_UNREADABLE_STATUS`), `tests/test_poller.py -k "policy or refusal or outage"` -> `2 failed, 27 passed`:

```
FAILED tests/test_poller.py::test_five_refusals_by_a_rule_over_three_storages_are_five_verdicts[True-False]
FAILED tests/test_poller.py::test_policy_refusals_from_two_storages_never_escalate_to_an_outage
restored_identical=yes
```

Baumhash backend/src/findling: Rezept und Pipeline `9fa6c443...` mit 83 Dateien, Positivkontrolle `git archive 7198db12` -> `7249fe45...` mit 83; php/ unverändert `34d00c1f...` (141).

### RED und GREEN 45-19

Plan 45-19, 2026-11-22, nach `Entscheid V-02-Regel 45-19` (Owner "Go mit den Empfehlungen", 18:37 UTC, Entscheid c, Commit cf53cfd8): eine Regel nur nach dem Einhängepunkt, gleich welcher Typ, gesetzt in ExternalMountService, gelesen von Liste und Bestätigung. Docker seriell, vor jedem Start `test -z "$(docker ps -q)"` leer.

#### V-45-10-02 (Task 1)

RED (nicht committet, nur die neuen Fälle):

`PYTHONUTF8=1 uv run --no-sync python -m pytest -q tests/test_admin_locale.py tests/test_admin_ui_contract.py -k "confirmation or duplicate_mark or reads_a_mount_only"` -> `5 failed, 1 passed, 231 deselected in 0.76s`, wörtlich:

```
FAILED tests/test_admin_locale.py::test_the_confirmation_names_the_id_of_storages_that_share_a_mount_point
FAILED tests/test_admin_locale.py::test_the_confirmation_follows_the_duplicate_rule_across_backends
FAILED tests/test_admin_locale.py::test_the_confirmation_keeps_markup_and_replacement_patterns_as_text
FAILED tests/test_admin_ui_contract.py::test_the_script_reads_a_mount_only_out_of_its_row_and_writes_it_as_text
FAILED tests/test_admin_ui_contract.py::test_the_duplicate_mark_only_follows_the_server_flag
```

Gründe: die drei node-Fälle fanden den Aufruf `text('findling-rules-confirm-mounts-value', confirmedMounts(newMounts))` nicht bzw. `admin.js holds 0 functions named mountDuplicateOf`; der Skript-Gate meldete die fehlende Ersetzung mit Funktion und den alten Aufruf; der Template-Gate `data-mount-duplicate stands 0 times, not once`. Der eine grüne Fall ist der vorhandene `test_the_script_sends_the_pattern_list_and_cuts_the_confirmation_around_it` (vom Filter erfasst, nicht neu).

`bash scripts/dev/phpunit_docker.sh --filter ExternalMountServiceTest` -> `Tests: 11, Assertions: 52, Failures: 1.`, wörtlich:

```
1) OCA\Findling\Tests\Unit\ExternalMountServiceTest::testMountsThatShareAMountPointAreDuplicatesWhateverTheBackend
Failed asserting that two arrays are identical.
-        'duplicate' => true,
+        'duplicate' => false,      (id 8, /Share, SFTP)
```

Fix: ExternalMountService::adminMounts() zählt nur `$mount['mountPoint']` (Docblock nennt die Regel und dass die Bestätigung dasselbe Merkmal liest); templates/admin.php setzt `<?php if ($externalMount['duplicate']) { ?> data-mount-duplicate="true"<?php } ?>` direkt nach `data-mount-id`; admin.js `mountDuplicateOf(id)` (nur `box.dataset.mountDuplicate === 'true'`) und `confirmedMounts(ids)` (bei Merkmal `t('findling', '%1$s (ID %2$s)').replace(/%([12])\$s/g, function (_, n) { ... })`, Form i), Ausgabe weiter über `text(...)`. Der Schlüssel `%1$s (ID %2$s)` steht in allen 18 Katalogdateien, kein Katalog geändert. Der Skript-Gate `scan_mount_script` ließ bisher kein `dataset` im Speicherteil zu; er lässt jetzt genau `dataset.mountDuplicate === 'true'` zu (Fehl-Sample `!== undefined` rot), verlangt den neuen Aufruf und die eine Ersetzung mit Funktion (Fehl-Samples innerHTML und zwei Ersetzungen hintereinander rot). Neuer Gate `scan_duplicate_mark` mit Fehl-Samples: ohne Bedingung, unter `$externalStorage`, doppelt, Merkmal nicht streng boolesch, je rot.

Hinweis zum RED: im Harness stand zunächst ein überzähliges `return element` im Funktionsrumpf (ReferenceError); im RED nicht erreicht, weil der Ausschnitt schon vorher scheiterte. Vor GREEN behoben, die Erwartungen blieben unverändert.

#### V-45-10-02 Mutationen

Je einzeln, danach Datei byte-gleich zurück (`restored_identical=yes`), Skripte `<scratchpad>/mutate19.py`, `mut19.sh`, `mut19_v3.sh`:

(V1) `confirmedMounts` gibt nur `ids.map(mountPointOf).join(', ')` zurück, Bestätigung ohne ID -> rot: `test_the_confirmation_names_the_id_of_storages_that_share_a_mount_point`, dazu `test_the_confirmation_follows_the_duplicate_rule_across_backends` und `test_the_confirmation_keeps_markup_and_replacement_patterns_as_text` (`3 failed, 234 passed`)
(V2) zwei hintereinander geschaltete String-Replacements `.replace('%1$s', point).replace('%2$s', String(id))` statt einer Regex mit Callback -> rot: `test_the_confirmation_keeps_markup_and_replacement_patterns_as_text`, dazu `test_the_script_reads_a_mount_only_out_of_its_row_and_writes_it_as_text` (`2 failed, 235 passed`)
(V3) ExternalMountService nimmt den Typ wieder in den Schlüssel (Zählung und Merkmal `mountPoint . "\0" . backend`) -> rot: `testMountsThatShareAMountPointAreDuplicatesWhateverTheBackend` (`Tests: 11, Assertions: 52, Failures: 1.`)
(V4) das Attribut ohne die Bedingung, also an jeder Checkbox gesetzt -> rot: `test_the_duplicate_mark_only_follows_the_server_flag` (`1 failed, 236 passed`)

Baumhash php/: Rezept und unabhängige Pipeline (find, sort, sed, sha256sum) `233c6ab1...` mit 141 Dateien; Positivkontrolle Rezept und Pipeline über `git archive cf53cfd8` -> `34d00c1f...` mit 141 (gleich dem bisherigen PHP_TREE_HASH_TODAY).

GREEN Task 1 (Commit c33103fe): verify-Zeile wörtlich aus `<scratchpad>/v19_t1.sh`, statische Prüfungen grün (`STATIC_OK`), `bash scripts/dev/phpunit_docker.sh` -> `OK (1347 tests, 8616 assertions)`, `php_gates_docker.sh all` grün (Psalm-Taint gegen ocp v33.0.9, v34.0.6, v35.0.3 je 0 Befunde, Probe 3; php-cs 0, Probe gesehen; zizmor und actionlint grün), pytest der drei Dateien `809 passed`, ruff `All checks passed!`, ruff format `260 files already formatted`. Der Hintergrundlauf wurde danach von Claude Code wegen Speichermangel beendet; pyright und vulture liefen auf Freigabe des Koordinators einzeln im Vordergrund: pyright latest `0 errors, 0 warnings, 0 informations`, vulture ohne Fund. Zwischen dem Lauf und dem Commit blieb der Baum unverändert.

#### V-45-10-03 (Task 2)

RED (nicht committet, nur der neue Fall): `PYTHONUTF8=1 uv run --no-sync python -m pytest -q tests/test_admin_ui_contract.py -k "example_path"` -> `1 failed, 226 deselected in 0.60s`, wörtlich:

```
FAILED tests/test_admin_ui_contract.py::test_the_example_path_of_the_lookup_comes_from_the_catalogue
E       AssertionError: assert ['lookup: a p...he catalogue'] == []
```

Fix: templates/admin.php `placeholder="<?php p($l->t('alice/files/Contracts/Rent.pdf')); ?>"`; der Schlüssel steht in allen 18 Katalogdateien direkt nach `Path or file ID`, mit den freigegebenen Werten (Text 6 aus 45-17): DE und de_DE `alice/files/Verträge/Miete.pdf`, FR `alice/files/Contrats/Loyer.pdf`, es `alice/files/Contratos/Alquiler.pdf`, it `alice/files/Contratti/Affitto.pdf`, nl `alice/files/Contracten/Huur.pdf`, pt_BR `alice/files/Contratos/Aluguel.pdf`, pt_PT `alice/files/Contratos/Renda.pdf`, zh_TW `alice/files/合約/租金.pdf`. "/" roh geschrieben, in .js und .json gleich (die Kataloge enthielten vorher kein "/", `json.loads` und Nextcloud lesen beide Formen). Unter EN bleibt der Schlüssel selbst. Sechs Sprachtabellen mit neuer Zeile, Schlüsselzahl 382 -> 383 (Gate mit neuem Absatz, Zähltabelle in docs/l10n-chinese.md), VALUES_THAT_MAY_EQUAL_THEIR_KEY unverändert (kein Wert gleich dem Schlüssel). Ausgabe nur über p(), `test_no_catalogue_value_can_break_the_page` deckt den Schlüssel mit (kein "%", kein "|").

Gegenprobe (`<scratchpad>/mut19_t2.sh`): fester Text `placeholder="alice/files/Vertraege/Miete.pdf"` zurück im Template -> rot: `test_the_example_path_of_the_lookup_comes_from_the_catalogue` (`1 failed, 226 passed`), Datei danach byte-gleich (`restored_identical=yes`). Der Test hält dasselbe Fehl-Sample zusätzlich in sich.

Baumhash php/: Rezept und Pipeline `a6c5f8d1...` mit 141 Dateien; Positivkontrolle über `git archive c33103fe` -> `233c6ab1...` mit 141.

GREEN Task 2 (Commit 1b31b281): verify-Zeile wörtlich aus `<scratchpad>/v19_t2.sh`, seriell, Docker vorher leer -> `VERIFY_EXIT=0`: `STATIC_OK`, PHPUnit `OK (1347 tests, 8616 assertions)`, `php_gates_docker.sh all` grün (Psalm-Taint je 0 Befunde gegen ocp v33.0.9, v34.0.6, v35.0.3, Probe 3; php-cs grün; zizmor und actionlint grün), pytest der drei Dateien `810 passed`, ruff `All checks passed!`, ruff format `260 files already formatted`, pyright latest `0 errors, 0 warnings, 0 informations`, vulture ohne Fund. Docker danach leer.

Nicht im Plan, nur festgehalten: die Felder der Ausschlussregeln tragen weiter feste Platzhalter (`placeholder="Backups"`, `placeholder="*.photoslibrary"`, admin.php Z. ~1562 und ~1606); der Gate dieses Plans prüft nur das Feld der Diagnose.

### E3 Erkennung an der Quelle

Plan 45-22 Task 1, 2026-11-23. Frage: Woran erkennt Findling beim Suchen, dass eine Trefferdatei für die suchende Person unter Secure View bzw. Wasserzeichen steht, damit ihr Treffer ohne Textausschnitt erscheint (E3)? Kein Docker, nur Quellen.

Quellen: richdocuments am Tag (v12.0.2 für NC 35, v11.1.3 für NC 34, v10.3.3 für NC 33, siehe "Quellen am Tag") und nextcloud/server stable33, stable34, stable35, abgerufen am 2026-11-23 per `gh api repos/nextcloud/<repo>/contents/<pfad>?ref=<ref>` (Accept raw), abgelegt unter `<scratchpad>/src22/rd/<tag>/` und `<scratchpad>/src22/nc/<branch>/`. SHA-256 (erste acht Stellen) v10.3.3 / v11.1.3 / v12.0.2: PermissionManager.php e8f1d842 / 6cb3f1f2 / 6cb3f1f2 (v12.0.2 gleich der Kopie aus 45-17), SecureViewService.php e670d117 / e670d117 / 4cbbdeac, AppConfig.php ff5da6d1 / 19531aab / 9820dab8, Capabilities.php 946617db / e5931d6b / 066efdac. Server stable33 / stable34 / stable35: ISharedStorage.php 691637e1 / 691637e1 / 75c6e3e4, IShare.php 33b75e3b / 7e7dcd07 / e5da110c, IAttributes.php 2cf68b9b / 2cf68b9b / 7ca9597c, IAppConfig.php b1fc36f1 / b1fc36f1 / d72335ff, ISystemTagObjectMapper.php f7ee1bd1 / febccd6e / d9112bc2, Cache/IFileAccess.php 6166f4c5 / 6166f4c5 / b84c1e7e, IGroupManager.php 827dce39 / ab56de1c / 1576a88f, IUserMountCache.php 3ce99027 / 3ce99027 / 115cfecc, ICacheEntry.php dba12bff / dba12bff / 151cf4d3, View.php 3fc11d9e / 5ec359af / 543c02b7, files_sharing SharedStorage.php 8900d209 / 6c5ba15a / daabea35.

#### Was richdocuments für eine angemeldete Person prüft

- Ein Wasserzeichen gibt es nur, wenn `watermark_enabled` im Namensraum `files` nicht `no` ist: PermissionManager.php Z. 175 (alle drei Tags), Application.php v12.0.2 Z. 139 und SecureViewService.php v12.0.2 Z. 28 lesen denselben Schlüssel über die öffentliche `IAppConfig::getValueString('files', 'watermark_enabled', 'no')`. Jeder andere Wert als `no` schaltet ein; die Modus-Schlüssel gelten nur bei genau `yes` (Z. 195 bis 248). Die Listen `watermark_allGroupsList` und `watermark_allTagsList` sind kommagetrennte Zeichenketten im selben Namensraum (AppConfig.php v12.0.2 Z. 52 `WATERMARK_APP_NAMESPACE = 'files'`, Z. 98 bis 103 `explode(',', $value)`; v11.1.3 Z. 51 und 97 bis 100; v10.3.3 Z. 50 und 96 bis 99).
- `shouldWatermark(Node|ICacheEntry $nodeOrCacheEntry, ?string $userId = null, ?IShare $share = null, ?string $ownerId = null)` (PermissionManager.php Z. 174, in allen drei Tags gleiche Signatur und Zeile) wertet nur richdocuments-Mimetypes (Z. 179; `getMimeTypes()` AppConfig.php v12.0.2 Z. 216 bis 222 aus Capabilities MIMETYPES, MIMETYPES_MSOFFICE, MIMETYPES_OPTIONAL; darin ODF, MS-Office, `application/pdf`, `text/plain`), dann die Modi.
- SecureViewService::shouldSecure (v12.0.2 Z. 34 bis 61) ruft die Prüfung mit dem Cache-Eintrag des Speichers, über den zugegriffen wird (Z. 42 `$storage->getCache()->get($path)`), der Freigabe dieses Speichers, wenn er ISharedStorage ist (Z. 54 bis 57), der Person aus der Sitzung (Z. 58) und dem Besitzer des Speichers (Z. 60 `$storage->getOwner($path)`). Der Wrapper liegt um jeden Mount außer `/` und nicht in der CLI (Application.php v12.0.2 Z. 153), also auch um den Home-Mount `/<uid>/` (in 45-17 M2 belegt: bobs eigene Datei 136 gesperrt).
- Eine Unified-Search-Anfrage ist eine angemeldete OCS-Anfrage (GET, keine CLI). Für sie gilt also `userId` = suchende Person, `share` = Freigabe des Mounts, über den die Person die Datei sieht, `ownerId` = Besitzer dieses Speichers. Maßstab für E3 ist damit die Bedingung mit gesetzter `userId`.

Die Modi mit gesetzter `userId` (Zeilen PermissionManager.php, alle drei Tags):

| Modus | Bedingung an der Quelle | trifft wen |
|---|---|---|
| shareAll (Z. 217 bis 224) | `$ownerId !== $userId` | jede Datei, die die Person nicht selbst besitzt: Freigaben, Team Folder (ohne Besitzer, 45-17), externe Speicher |
| shareRead (Z. 226 bis 228 mit Z. 185 bis 188) | Eintrag des Mounts ohne UPDATE oder Freigabe ohne UPDATE | lesende Freigaben, nur lesende Team-Folder-Mitglieder, und auch eigene Dateien, deren Eintrag kein UPDATE trägt (Randfall unten) |
| shareDisabledDownload (Z. 230 bis 232 mit Z. 190 bis 191) | Freigabe mit Attribut `permissions/download === false` | nur Zugriff über eine solche Freigabe |
| hideDownload (Z. 192 bis 193) | `getHideDownload()` | nur im Link-Zweig (`TYPE_LINK`, Z. 194 bis 215) als `$isSecureView`; Link-Freigaben erzeugen keinen Mount (45-17, files_sharing MountProvider), die Suche ist immer angemeldet: greift in der Suche nie |
| link-Modi linkAll, linkRead, linkSecure, linkTags (Z. 194 bis 215) | nur `getShareType() === IShare::TYPE_LINK` | in der Suche nie (wie hideDownload) |
| shareTalkPublic (Z. 234 bis 238) | `$userId === null` und `TYPE_ROOM` | in der Suche nie (Person gesetzt) |
| allGroups (Z. 240 bis 247) | Person in einer Gruppe der Liste | alle Dateien dieser Person mit richdocuments-Mimetype, auch eigene |
| allTags (Z. 248 bis 257) | Datei trägt einen Systemtag der Liste (`getTagIdsForObjects([$fileId], 'files')`, nur der Tag der Datei selbst, nicht der Ordner) | jede Person, auch der Besitzer |

#### Optionen

Öffentliche APIs, die die Optionen nutzen (alle in stable33 bis stable35 vorhanden, Signatur gleich):

- `OCP\Files\Storage\ISharedStorage::getShare(): IShare` (@since 30.0.0; stable33/34 Z. 24, stable35 Z. 25); files_sharing SharedStorage implementiert sie (SharedStorage.php Z. 391 / 406 / 405).
- `OCP\Share\IShare::getAttributes(): ?IAttributes` (@since 25.0.0; Z. 326 / 318 / 316), `getHideDownload(): bool` (@since 15.0.0; Z. 641 / 633 / 649), `getPermissions()` (Z. 301 / 293 / 291); `OCP\Share\IAttributes::getAttribute(string $scope, string $key): mixed` (@since 25.0.0; Z. 36 / 36 / 37).
- `OCP\IAppConfig::getValueString` (Z. 180 / 180 / 181), `getKeys(string $app)` (Z. 78 / 78 / 79).
- `OCP\Files\Cache\IFileAccess::getByFileIds(array $fileIds): array<int, ICacheEntry>` (@since 29.0.0; Z. 67 / 67 / 68), steht schon im Konstruktor von SearchService (Z. 167, genutzt Z. 846); `ICacheEntry::getStorageId()` (Z. 44 / 44 / 45) und `getPermissions()` (Z. 122 / 122 / 123).
- `OCP\Files\Config\IUserMountCache::getMountsForUser(IUser)` (Z. 38 / 38 / 39) bzw. `getMountsForFileId` (Z. 67 / 67 / 68); `ICachedMountInfo::getStorageId()`, `getMountPoint()`, `getMountProvider()` (45-17: Home-Mount `/<uid>/` mit `OC\Files\Mount\LocalHomeMountProvider` bzw. `ObjectHomeMountProvider`, wie `HOME_MOUNT_PROVIDERS` in ReaderCandidates).
- `OCP\SystemTag\ISystemTagObjectMapper::getTagIdsForObjects($objIds, string $objectType): array` (@since 9.0.0; Z. 38 / 44 / 45), gebändert für viele IDs.
- `OCP\IGroupManager::isInGroup($userId, $group)` (Z. 132 / 132 / 138) bzw. `getUserGroupIds(IUser)` (Z. 95 / 95 / 101).
- Knoten der Person: nur `SearchService::readableFile()` (Z. 723), wie es RESOLUTION_REGISTER verlangt.

S1, öffentliche Freigabe-Attribute: Knoten der Person über `SearchService::readableFile`, Speicher `instanceOfStorage(ISharedStorage::class)`, dann `getShare()->getAttributes()?->getAttribute('permissions', 'download') === false` oder `getHideDownload()`; dazu `watermark_enabled` und `watermark_shareDisabledDownload` aus IAppConfig.

- Abdeckung: shareDisabledDownload ja (dieselbe Bedingung wie Z. 190 bis 191). hideDownload: in der Suche ohne Wirkung bei richdocuments, S1 würde zusätzlich unterdrücken (harmlos). shareAll nein, shareRead nein, allGroups nein, allTags nein. Link-Modi und shareTalkPublic greifen in der Suche nie.
- APIs: nur öffentliche OCP (oben); Bruchrisiko niedrig.
- Kosten: je Treffer eine Auflösung (`getFirstNodeById` in readableFile, wie der Recheck) plus Speicher- und Freigabe-Objekt aus dem bereits aufgebauten Mount, gedeckelt auf die Seitengröße; nur bei aktivem Wasserzeichen.
- Fehler: Auflösung wirft oder liefert null -> kein Ausschnitt (fail-closed).
- Urteil: allein NICHT E3-konform; bei shareAll, shareRead, allGroups und allTags blieben Ausschnitte sichtbar, die richdocuments schützt (Unterunterdrückung). Nur als Teil einer Kombination.

S2, richdocuments `PermissionManager::shouldWatermark` direkt: `\OCP\Server::get('OCA\Richdocuments\PermissionManager')` mit `class_exists`, `method_exists` und Signaturprüfung per Reflection, Aufruf je Treffer mit dem Cache-Eintrag des aufgelösten Knotens, `uid`, der Freigabe des Speichers (wie S1) und `$storage->getOwner()`.

- Abdeckung: alle Modi exakt wie richdocuments, auch künftige neue Modi, sofern die Signatur bleibt.
- APIs: interne Klasse `OCA\Richdocuments\PermissionManager` (Z. 26 `class PermissionManager`, kein OCP, keine Stabilitätszusage); Signatur Z. 174 in v10.3.3, v11.1.3 und v12.0.2 gleich, v10.3.3 weicht in Z. 183 ab (ohne Wirkung). Die Klasse existiert nur, wenn richdocuments geladen ist. Psalm kennt sie nicht (Stub oder Unterdrückung nötig); ein Gate auf die Signatur und ein CI-Schritt mit installiertem richdocuments je NC 33, 34, 35 wären Pflicht (T-45-78).
- Kosten: je Treffer eine Auflösung wie S1 plus die shouldWatermark-Kette: AppConfig aus dem Speicher, bei allTags bzw. linkTags je Treffer eine Abfrage `getTagIdsForObjects([$fileId])` (Z. 250, nicht gebändert), bei allGroups `isInGroup` je Listengruppe (Gruppen der Person im Request gecacht). Gedeckelt auf die Seitengröße, nur bei aktivem Wasserzeichen.
- Fehler: Klasse fehlt, Signatur anders, Ausnahme -> kein Ausschnitt (fail-closed). Ein Umbau in einer künftigen richdocuments-Version nimmt dann bei aktivem Wasserzeichen alle Ausschnitte weg, bis Findling nachzieht; das ist kein Leck, aber ein stiller Funktionsverlust, und eine Bedeutungsänderung bei gleicher Signatur fängt kein Guard ab.

S3, konservativ mit öffentlichen APIs: ist `watermark_enabled` nicht `no`, gibt es keinen Ausschnitt für Treffer, die die suchende Person nicht besitzt; zusätzlich bei allTags und allGroups die exakte Prüfung mit öffentlichen APIs. Besitz heißt: die Datei liegt im Home-Speicher der Person (Speicher-ID des Cache-Eintrags aus `IFileAccess::getByFileIds` gleich der Speicher-ID ihres Home-Mounts `/<uid>/` aus dem Mount-Cache), wie die Besitzererkennung in ReaderCandidates.

- Abdeckung: shareAll ja (jede fremde Datei ohne Ausschnitt, auch Team Folder und externe Speicher). shareDisabledDownload ja (eine Freigabe ist nie eine eigene Datei). hideDownload und Link-Modi ohne Wirkung in der Suche, fremde Dateien ohnehin ohne Ausschnitt. shareTalkPublic greift in der Suche nie. allGroups ja: `watermark_allGroups === 'yes'` und Person in einer Gruppe von `watermark_allGroupsList` -> kein Ausschnitt für ihre Treffer. allTags ja: `watermark_allTags === 'yes'` und ein Tag aus `watermark_allTagsList` an der Datei (`getTagIdsForObjects($fileIds, 'files')` für die ganze Seite) -> kein Ausschnitt für alle Personen. shareRead: fremde Dateien ja; eigene Dateien nur mit der Zusatzprüfung aus dem Randfall unten.
- Überunterdrückung (zulässig): bei aktivem Wasserzeichen, gleich welcher Modus, verlieren alle fremden Dateien ihren Ausschnitt, auch Freigaben mit Download, Team Folder mit Schreibrecht und Dateitypen außerhalb der richdocuments-Liste (etwa Bilder mit OCR-Text); der Mimetype-Filter wird nicht nachgebaut. Ebenso, wenn richdocuments deaktiviert ist, der Schlüssel aber noch `yes` trägt (dann wirkt kein Wrapper).
- APIs: nur öffentliche OCP (oben); Bruchrisiko niedrig. Restrisiko: ein in einer späteren richdocuments-Version neuer Modus mit eigenem Schlüssel wäre S3 unbekannt. Abhilfe ebenfalls öffentlich: `IAppConfig::getKeys('files')`; steht ein `watermark_*`-Modus-Schlüssel auf `yes`, den S3 nicht kennt, gibt es bei aktivem Wasserzeichen gar keinen Ausschnitt (fail-closed gegen neue Modi).
- Kosten je Seite, nicht je Treffer: AppConfig aus dem Speicher (keine Abfrage), eine Abfrage `getByFileIds` für alle Treffer der Seite, eine Abfrage Mount-Cache für den Home-Speicher der Person, bei allTags eine Abfrage `getTagIdsForObjects`, bei allGroups die Gruppen der Person (im Request gecacht); Cache je Request. Ohne aktives Wasserzeichen nur das Lesen von `watermark_enabled` aus dem Speicher, keine zusätzliche Abfrage.
- Fehler: jede Ausnahme (Typkonflikt in IAppConfig, Datenbank, Mount-Cache) -> kein Ausschnitt für die betroffenen Treffer bzw. die Seite (fail-closed), Logzeile nur mit Zähler und Klassenname.

Randfall S3 unter shareRead, eigene Datei ohne UPDATE (PermissionManager.php Z. 185 bis 188 und 226): ohne Freigabe hängt `$isUpdatable` allein am Cache-Eintrag des Mounts, über den zugegriffen wird. Trägt er für den Besitzer kein UPDATE (zum Beispiel eine lokale Datei, die der Webserver nicht schreiben darf, oder ein Speicher- bzw. Cache-Wrapper, der UPDATE wegnimmt), setzt richdocuments auch für den Besitzer das Wasserzeichen. S3 in der Grundform würde sie als Besitzer-Datei mit Ausschnitt zeigen: das ist Unterunterdrückung und damit nicht zulässig. Zwei öffentliche Wege, ihn zu schließen, nur wenn `watermark_shareRead === 'yes'`: (a) die Rohrechte aus `getByFileIds` (`getPermissions() & PERMISSION_UPDATE`, ohne Zusatzabfrage); das sieht die Rohzeile der Tabelle, nicht einen Wrapper, der Rechte erst beim Lesen maskiert. (b) der Knoten aus `SearchService::readableFile()` und `isUpdateable()`, also dieselbe umhüllte Sicht, die richdocuments über `$storage->getCache()` bzw. `Node::isUpdateable()` (Z. 185 bis 186) nutzt; Kosten eine Auflösung je eigenem Treffer der Seite, nur unter shareRead. Ob eine Sperre (files_lock) die Cache-Rechte maskiert, ist an der Quelle nicht geprüft; (b) deckt es ab, weil es die Sicht der Person liest. Vorschlag: (a) und (b) zusammen, kein Ausschnitt, wenn eine der beiden kein UPDATE zeigt.

Weitere Randfälle (alle Optionen): Sieht eine Person dieselbe Datei über zwei Wege (eigene Freigabe mit Download und Gruppenfreigabe ohne), entscheidet richdocuments je Weg. S1 und S2 prüfen den Weg, den readableFile liefert; ist der andere Weg frei, kann die Person die Datei ohnehin herunterladen, ein Ausschnitt verrät nichts zusätzlich. S3 ist davon unabhängig (fremd ist fremd).

S4, Probe-Öffnen je Treffer: verworfen. `OC\Files\View::fopen($path, 'r')` setzt den Hook `read` (stable35 Z. 1035 bis 1041, stable34 Z. 1036 ff., stable33 Z. 1011 ff.), `runHooks` sendet ihn vor dem Öffnen (stable35 Z. 1338 bis 1365, `OC_Hook::emit(..., 'read', ...)`), der HookConnector macht daraus `BeforeNodeReadEvent` (lib/private/Files/Node/HookConnector.php stable35 Z. 66, 198 bis 203), und admin_audit protokolliert dieses Ereignis als Lesezugriff (apps/admin_audit/lib/AppInfo/Application.php stable35 Z. 198 bis 200). Jede Suche würde je Treffer einen Lesezugriff der Person im Audit-Protokoll erzeugen und je Treffer eine Datei öffnen; dazu sperrt SecureViewWrapper nur GET ohne WOPI (Z. 94 bis 96), das Ergebnis hinge also an der HTTP-Methode der Suchanfrage.

| Option | shareAll | shareRead | shareDisabledDownload | hideDownload / Link-Modi | shareTalkPublic | allGroups | allTags | API | Abfragen | Bruchrisiko |
|---|---|---|---|---|---|---|---|---|---|---|
| S1 | nein | nein | ja | ohne Wirkung in der Suche | ohne Wirkung | nein | nein | OCP | eine Auflösung je Treffer | niedrig |
| S2 | ja | ja | ja | ohne Wirkung | ohne Wirkung | ja | ja | intern richdocuments | eine Auflösung und eine Kette je Treffer | hoch |
| S3 | ja (alle fremden) | ja für fremde, eigene mit (a)+(b) | ja | ohne Wirkung | ohne Wirkung | ja | ja | OCP | konstant je Seite, (b) nur unter shareRead | niedrig |
| S4 | ja | ja | ja | ohne Wirkung | ohne Wirkung | ja | ja | OCP | ein fopen je Treffer | niedrig, aber Audit-Zeilen je Suche: verworfen |

Empfehlung: S3 mit den Ergänzungen (a)+(b) für eigene Dateien unter shareRead und dem Schutz gegen unbekannte Modi über `getKeys('files')`. Begründung: Security zuerst; S3 unterdrückt in keinem Modus weniger als richdocuments (keine Unterunterdrückung, auch nicht beim Randfall), nutzt nur öffentliche OCP-APIs, die in stable33 bis stable35 mit gleicher Signatur stehen, kostet je Seite eine feste kleine Zahl Abfragen und ohne Wasserzeichen keine. Der Preis ist Überunterdrückung bei aktivem Wasserzeichen (fremde Dateien ohne Ausschnitt, auch solche mit Download), was E3 ausdrücklich zulässt: der Treffer bleibt mit Name und Pfad. S2 wäre genauer, hängt aber an einer internen Klasse ohne Zusage, braucht Stub, Signatur-Gate und CI-Schritt je Version und schützt nicht gegen eine Bedeutungsänderung bei gleicher Signatur. S1 allein ist nicht E3-konform. S4 ist verworfen. Weil S3 allGroups abdeckt, sehen Mitglieder einer allGroups-Gruppe keine Ausschnitte; die Frage G1 aus 45-17 muss dann nicht erneut gestellt werden.

Zur Frage Altbestand (I-45-17-02): Die Entscheidung von S3 hängt nur an Wasserzeichen-Konfiguration, Besitz, Tags, Gruppen und Rechten, nicht am Urteil (`failed(gateway_error)`, `failed(policy_blocked)`) und nicht am Indexzeitpunkt. Damit ist auch Inhalt, der vor dem Einschalten des Wasserzeichens indexiert wurde, ohne Ausschnitt, gleich welche Option gewählt wird (außer S1 allein).

#### S1 für shareDisabledDownload nach dem Owner-Entscheid: Rückfall auf S3

`Entscheid E3-Weg 45-22` (Owner "Go", 2026-11-23 02:42 UTC, Commit d57bd962): S3, unter shareDisabledDownload aber die genaue Prüfung wie PermissionManager Z. 230 bis 232 (kein Ausschnitt genau dann, wenn die suchende Person die Datei über eine Freigabe mit `download=false` sieht), nur mit öffentlichen OCP-APIs, sonst Rückfall auf reines S3 mit Grund im Audit. Ergebnis: Rückfall. Quellen zusätzlich am 2026-11-23 per `gh api` abgelegt unter `<scratchpad>/src22/nc/mp/`, SHA-256 (erste acht Stellen) files_sharing MountProvider.php stable33 / stable34 / stable35 4a914cf5 / 46cf40bf / 405b8d09, lib/private/Files/Storage/Wrapper/Wrapper.php 8b4c6449 / e41dbcbc / 5df69575.

Welche Freigabe richdocuments prüft, ist sauber belegt:

- SecureViewWrapper::checkFileAccess ruft `shouldSecure($path, $this, false)` (Z. 96), also mit dem Wrapper um den Speicher des Mounts, über den zugegriffen wird. SecureViewService::shouldSecure fragt `$storage->instanceOfStorage(ISharedStorage::class)` und dann `$storage->getShare()` (v10.3.3 und v11.1.3 Z. 53 bis 56, v12.0.2 Z. 54 bis 57, jeweils mit `@psalm-suppress UndefinedMethod`, weil IStorage kein getShare kennt).
- Der Aufruf auf dem Wrapper landet über `Wrapper::__call` beim inneren Speicher (OC\Files\Storage\Wrapper\Wrapper stable33 Z. 258 bis 260, stable34 Z. 305 bis 307, stable35 Z. 306 bis 308, `call_user_func_array([$this->getWrapperStorage(), $method], $args)`), bis zu SharedStorage::getShare(), das `$this->superShare` liefert (stable33 Z. 391 bis 393, stable34 Z. 406 bis 408, stable35 Z. 405 bis 407; gesetzt aus `$parameters['superShare']`, Z. 98 / 103 / 106).
- Die Super-Freigabe baut files_sharing MountProvider::buildSuperShares je Mount aus allen Freigaben desselben Knotens an die Person (stable33 Z. 127 ff., stable34 und stable35 Z. 118 ff.); mergeAttributes (stable33 Z. 185 ff., stable34 und stable35 Z. 176 ff.) lässt `true` gewinnen und übernimmt sonst den Wert der jeweils nächsten Freigabe. Eine Datei in einem freigegebenen Ordner liegt im SharedStorage des Ordner-Mounts; geprüft wird also die Super-Freigabe dieses Mounts (die zusammengeführten Freigaben des Ordners), nicht eine Freigabe der Datei selbst.

Mit öffentlichen OCP-APIs ist diese Super-Freigabe nicht erreichbar:

- `Node::getStorage()` und `IMountPoint::getStorage()` liefern den äußersten Wrapper. `IStorage::instanceOfStorage()` (stable33 bis stable35 Z. 302) sagt nur, dass innen ein ISharedStorage liegt, und gibt ihn nicht heraus. `lib/public/Files/Storage` enthält in stable33 und stable35 nur IChunkedFileWrite, IConstructableStorage, IDisableEncryptionStorage, ILockingStorage, INotifyStorage, IReliableEtagStorage, ISharedStorage, IStorage, IStorageFactory und IWriteStreamStorage, keine Methode zum Auspacken. `getShare()` am Wrapper geht nur über das private `Wrapper::__call` und braucht eine Psalm-Unterdrückung, die der Gate `test_the_analysed_php_files_suppress_nothing` verbietet.
- Über den Mount: `OCA\Files_Sharing\SharedMount` reicht die Freigabe über `ISharedMountPoint` aus dem Namensraum der App heraus (SharedMount.php stable35 Z. 28 und 139), nicht über OCP; `lib/public/Files/Mount` enthält in stable33 und stable35 nur IMountManager, IMountPoint, IMovableMount, IShareOwnerlessMount und ISystemMountPoint.
- Nachbau über `OCP\Share\IManager::getSharedWith` je Freigabetyp: das hieße Gruppierung, Statusfilter und Zusammenführung des privaten MountProvider (Z. 57 bis 193) samt aller Freigabetypen des Providers nachzubauen. Ein fehlender Typ oder eine spätere Änderung der Zusammenführung wäre Unterunterdrückung; das ist nicht sauber.
- Dazu wählt `getFirstNodeById` bei mehreren Wegen zur selben Datei einen Mount; richdocuments entscheidet je Weg.

Folge, im Code (SnippetPolicy) und in den Tests festgehalten: unter shareDisabledDownload gilt reines S3, jede Datei, die die Person nicht besitzt, zeigt keinen Ausschnitt, auch eine Freigabe mit Download, ein Team Folder ohne Freigabe und ein externer Speicher (Überunterdrückung, von E3 zugelassen). Die eigene Datei zeigt ihn weiter. Tests: `testUnderShareDisabledDownloadAShareWithoutDownloadGetsNoExcerptAndTheOwnerKeepsIt`, `testUnderShareDisabledDownloadAShareWithDownloadLosesItsExcerptAsWell`, `testUnderShareDisabledDownloadATeamFolderFileLosesItsExcerptAsWell`.

### RED und GREEN 45-22

Plan 45-22 Task 3, 2026-11-23, nach `Entscheid E3-Weg 45-22` (S3, shareDisabledDownload laut Abschnitt oben im Rückfall auf S3) und `Entscheid Altbestand 45-22` (A1). Docker seriell, vor jedem Start `test -z "$(docker ps -q)"` leer.

Umsetzung: `php/lib/Service/SnippetPolicy.php` (neu, final, eigene DI: IAppConfig, IFileAccess, IUserMountCache, ISystemTagObjectMapper, IGroupManager, LoggerInterface). `allowed(IUser, Folder, list<int>)` liefert die Ids, die einen Ausschnitt zeigen dürfen, in ihrer Reihenfolge. Ohne Wasserzeichen (`watermark_enabled` gleich `no`, wie PermissionManager Z. 175) nur dieses eine Lesen aus dem Speicher von IAppConfig, keine weitere Abfrage. Mit Wasserzeichen je Seite: `getKeys('files')` und die Regeln einmal je Request (Werte mit `isLazy` gelesen, wie IConfig sie unabhängig von lazy liest), ein unbekannter `watermark_*`-Schlüssel auf `yes` nimmt alle Ausschnitte; allGroups über `getUserGroupIds` je Person einmal je Request (gleich `isInGroup` je Listengruppe, Liste an Kommas geteilt, nichts getrimmt, wie AppConfig::getAppValueArray); shareAll, shareRead und shareDisabledDownload über ein `getByFileIds` für die Seite und den Home-Mount `/<uid>/` mit Home-Provider (einmal je Request); unter shareRead für eigene Dateien (a) Rohrechte ohne UPDATE und (b) Knoten aus `SearchService::readableFile()` ohne `isUpdateable()` oder nicht auflösbar oder werfend; allTags ein `getTagIdsForObjects` für die noch offenen Ids der Seite. Mehrere Modi: Vereinigung. Jede Ausnahme: keine Ausschnitte auf der Seite, Logzeile nur mit `count` und `class`. SearchService: ein Konstruktor-Parameter mit Docblock (vor `$clock`) und im Snippet-Block `$allowed = $this->snippetPolicy->allowed($user, $userFolder, $fileIds)`; `snippets` bekommt nur `$allowed` und läuft gar nicht, wenn `$allowed` leer ist. ApprovedHit, hitOf und der Endfilter bleiben unverändert; Treffer bleiben mit Name und Pfad (A1).

RED (nicht committet, nur die neuen Fälle):

`PYTHONUTF8=1 uv run --no-sync python -m pytest -q tests/test_php_static_gates.py tests/test_php_acl_boundary.py` -> `2 failed, 83 passed`, wörtlich:

```
FAILED tests/test_php_static_gates.py::test_the_excerpts_of_a_search_pass_the_snippet_policy
FAILED tests/test_php_acl_boundary.py::test_the_snippet_policy_resolves_nothing_of_its_own
```

Gründe: `'$fileIds is written 4 time(s) and 0 time(s) by $this->snippetPolicy->allowed(, expected once and only by it'` bzw. `Service/SnippetPolicy.php is missing`. Die Selbsttests der beiden neuen Regeln (sauberes Beispiel grün, Fehl-Samples rot: direkter Aufruf mit allen Ids, nachträglich erweitert, überschrieben, zweiter Aufruf, Ausdruck statt Variable; SnippetPolicy mit eigenem `getFirstNodeById`) waren schon grün.

`bash scripts/dev/phpunit_docker.sh --filter 'SnippetPolicyTest|SearchServiceTest'` -> `Tests: 99, Assertions: 277, Errors: 35.`: alle 29 Fälle von SnippetPolicyTest und die 6 neuen von SearchServiceTest (`testContentIndexedBeforeTheWatermarkShowsNoExcerptEither` mit `failed(gateway_error)` und `failed(policy_blocked)`, `testAHitUnderTheWatermarkKeepsItsNameAndPathAndGetsNoExcerpt`, `testTheOwnerOfTheSameFileKeepsItsExcerpt`, `testWithoutTheWatermarkEverySurvivorIsAskedForItsExcerpt`, `testWhenNoHitMayShowAnExcerptTheContainerIsNotAskedAtAll`) mit `Error: Class "OCA\Findling\Service\SnippetPolicy" not found`; die 64 vorhandenen Fälle von SearchServiceTest grün.

GREEN gefiltert: derselbe Aufruf -> `OK (99 tests, 350 assertions)`; die beiden pytest-Dateien `85 passed`.

Mutationen (je einzeln, danach beide Dateien byte-gleich zurück, `restored_identical=yes`; Skripte `<scratchpad>/w22/mutate22.py` und `<scratchpad>/w22/mut22.sh`, je gefiltertes PHPUnit `SnippetPolicyTest|SearchServiceTest`):

(M1) im Snippet-Aufruf `$fileIds` statt `$allowed`, Prüfung `$allowed !== []` bleibt -> rot: `testAHitUnderTheWatermarkKeepsItsNameAndPathAndGetsNoExcerpt` (`Failures: 1`) und der Gate `test_the_excerpts_of_a_search_pass_the_snippet_policy`
(M1b) Filter vor `snippets` ganz entfernt (`$fileIds !== []` und `$fileIds`) -> rot: beide Fälle `testContentIndexedBeforeTheWatermarkShowsNoExcerptEither` (Altbestand I-45-17-02), `testAHitUnderTheWatermarkKeepsItsNameAndPathAndGetsNoExcerpt` (kein Ausschnitt für alice), `testWhenNoHitMayShowAnExcerptTheContainerIsNotAskedAtAll` (`Failures: 4`) und der Gate
(M2) fail-open, der catch gibt alle Ids zurück -> rot: `testADetectionThatThrowsCostsTheExcerptsOfThePageAndLogsNoName`, `testAConfigThatThrowsCostsEveryExcerpt`
(M3) Ergänzung (b) entfernt (Knoten immer aktualisierbar) -> rot: `testUnderShareReadAnOwnFileWhoseNodeIsNotUpdateableGetsNoExcerpt`, `testUnderShareReadAnOwnFileWhoseNodeDoesNotResolveGetsNoExcerpt`
(M4) Schutz vor unbekannten Modi entfernt -> rot: `testAWatermarkModeThisClassDoesNotKnowTakesEveryExcerpt`
(M5) shareDisabledDownload nicht mehr unter den Modi für fremde Dateien -> rot: drei Fälle shareDisabledDownload, `testSeveralModesTakeTheUnionOfTheirSuppressions` und drei Fälle in SearchServiceTest (`Failures: 7`)
(M6) Schalter nur bei genau `yes` an statt bei allem außer `no` -> rot: `testAnEmptySwitchIsAWatermarkThatIsOnAsInRichdocuments`
(M7) Ergänzung (a) entfernt (Rohrechte) -> rot: `testUnderShareReadAnOwnFileWhoseRawPermissionsLackUpdateGetsNoExcerpt`
(M8) Tag-Vergleich nie wahr -> rot: `testUnderAllTagsAFileWithAListedTagGetsNoExcerptForAnybodyAndTheQueryIsBanded`, `testSeveralModesTakeTheUnionOfTheirSuppressions`
(M9) allGroups nie wahr -> rot: `testUnderAllGroupsAMemberOfAListedGroupGetsNoExcerptEvenForOwnFiles`
(M10) fehlender Cache-Eintrag bzw. fehlender Home-Mount gilt als eigen -> rot: `testAUserWithoutAHomeMountOwnsNothing`, `testAFileWithoutACacheEntryIsAForeignFile`

Gegenkontrollen grün: Besitzer bob mit derselben Datei (`testUnderShareAllTheOwnerKeepsTheExcerptOfTheSameFile`, `testTheOwnerOfTheSameFileKeepsItsExcerpt`), eigene aktualisierbare Datei unter shareRead, Wasserzeichen aus ohne jede Zusatzabfrage (Zähler auf getByFileIds, getMountsForUser, getTagIdsForObjects, getUserGroupIds, isInGroup, getKeys und auf die Knotenauflösung je null), Wasserzeichen an ohne Modus, der eine Suche erreicht (Link-Modi, shareTalkPublic). Die vorhandenen Fälle von SearchServiceTest laufen mit einer SnippetPolicy bei ausgeschaltetem Wasserzeichen und bleiben unverändert grün.

Nebenbefund vor GREEN: php-cs meldete im ersten Lauf von `php_gates_docker.sh all` die Einrückung einer Docblock-Fortsetzungszeile in SearchServiceTest (`serviceUnder`), ruff im ersten Verify-Lauf zwei Zeilen über 120 Zeichen in den neuen Gate-Selbsttests; beides behoben (Einrückung, `ruff format`), keine Erwartung geändert.

Baumhash php/: Rezept und unabhängige Pipeline (find, sort, sed, sha256sum) `ff141406...` mit 143 Dateien; Positivkontrolle Rezept und Pipeline über `git archive d57bd962` -> `a6c5f8d1...` mit 141 (gleich dem bisherigen PHP_TREE_HASH_TODAY).

GREEN (Commit mit `fix(45-22): a hit under secure view shows no excerpt to that user`): verify-Zeile wörtlich aus `<scratchpad>/w22/v22_t3.sh`, seriell, Docker vorher leer -> `VERIFY_EXIT=0`: `STATIC_OK`, PHPUnit `OK (1382 tests, 8690 assertions)`, `php_gates_docker.sh all` grün (Psalm-Taint je 0 Befunde gegen die drei ocp-Tags, Probe 3; php-cs 0, Probe gesehen; zizmor und actionlint grün), pytest der sieben Dateien `816 passed`, ruff `All checks passed!`, ruff format `260 files already formatted`, pyright latest `0 errors, 0 warnings, 0 informations`, vulture ohne Fund. Docker danach leer. Zwischen dem Lauf und dem Commit blieb der Baum außer diesem Absatz unverändert.

Echter Beleg folgt in 45-20 Schritt D, die Sichtprüfung im Neulauf von 45-10 (DE/EN/FR). Für 45-20 festgehalten: unter shareDisabledDownload zeigt auch eine Freigabe mit Download und ein Team Folder keinen Ausschnitt (Rückfall oben); eine Gegenkontrolle "Freigabe mit Download zeigt den Ausschnitt" gilt dort nur, wenn kein Modus für fremde Dateien (shareAll, shareRead, shareDisabledDownload) an ist.

### RED und GREEN 45-23

Plan 45-23 Task 2 und 3, 2026-11-23, nach `Entscheid Fix #25 in 1.7.0 45-23` und den Zeilen `Freigabe Texte #25 45-23`, `Entscheid Regeln Nachzählung 45-23` (r1), `Entscheid Rückhalt-Weg 45-23` (z1), `Entscheid Mindestabstand 45-23` (6h) und `Entscheid Locking 45-23` (l1). Docker seriell, vor jedem Start `test -z "$(docker ps -q)"` leer.

#### Quellen F1

Abgerufen am 2026-11-23 per `git clone --depth 1 --filter=blob:none --sparse` von nextcloud/server (Zweige stable33 1732389, stable34 0d928f1, stable35 dd471ac) und nextcloud-deps/ocp (Tags v33.0.9 43727c5, v34.0.6 a924e5e, v35.0.3 a7babe4, die Tags der Psalm-Matrix in php.yml), abgelegt unter `<scratchpad>/src23/`.

ILockingProvider (OCP/Lock/ILockingProvider.php; v33.0.9 und v34.0.6 byte-gleich, SHA-256 c34ef631; v35.0.3 c148711b, eine Zeile später):

| Stelle | v33.0.9 | v34.0.6 | v35.0.3 |
|---|---|---|---|
| `LOCK_SHARED = 1` / `LOCK_EXCLUSIVE = 2` | Z. 23 / 27 | Z. 23 / 27 | Z. 24 / 28 |
| `isLocked(string $path, int $type): bool` | Z. 33 | Z. 33 | Z. 34 |
| `acquireLock(string $path, int $type, ?string $readablePath = null): void` | Z. 41 | Z. 41 | Z. 42 |
| `releaseLock(string $path, int $type): void` | Z. 47 | Z. 47 | Z. 48 |
| `changeLock(string $path, int $targetType): void` / `releaseAll(): void` | Z. 56 / 62 | Z. 56 / 62 | Z. 57 / 63 |
| `class LockedException extends \Exception` (LockedException.php) | Z. 16 | Z. 16 | Z. 17 |

Wahl des Providers und TTL (lib/private/Server.php):

| Stelle | stable33 | stable34 | stable35 |
|---|---|---|---|
| `registerService(ILockingProvider::class, ...)` | Z. 935 | Z. 968 | Z. 866 |
| `filelocking.ttl`, Standard `max(3600, max_execution_time)` | Z. 938 | Z. 971 | Z. 869 |
| `filelocking.enabled` (Standard true) | Z. 939 | Z. 972 | Z. 870 |
| `createLocking('lock')`, kein NullCache -> `MemcacheLockingProvider($memcache, $timeFactory, $ttl)` | Z. 942 / 945 | Z. 975 / 978 | Z. 873 / 876 |
| sonst `DBLockingProvider(..., $ttl, !\OC::$CLI)` | Z. 947 | Z. 980 | Z. 878 |
| `filelocking.enabled` false -> `NoopLockingProvider` | Z. 954 | Z. 987 | Z. 885 |

Damit läuft der Marker über denselben Provider wie der Slice-Lock und hat dieselbe TTL; ein abgestürzter Prozess hinterlässt den Marker höchstens bis zu ihrem Ablauf (T-45-81).

Was beim Nehmen geworfen wird:

| Stelle | stable33 | stable34 | stable35 |
|---|---|---|---|
| DBLockingProvider::acquireLock | Z. 105 | Z. 109 | Z. 110 |
| darin `initLockField()` über `insertIgnoreConflict` und `executeStatement()` (wirft `OCP\DB\Exception` bei einem Datenbankfehler, kein catch in der Methode) | Z. 66, 117, 135 | Z. 68, 121, 139 | Z. 69, 122, 140 |
| belegter Lock -> `throw new LockedException` | Z. 139 | Z. 143 | Z. 144 |
| MemcacheLockingProvider::acquireLock, exklusiv `add` + `cas`, belegt -> LockedException | Z. 61, 76 | Z. 63, 78 | Z. 64, 79 |
| Memcache/Redis.php `@throws \Exception` an `getCache()`; kein einziges `catch` in der Datei (ein `\RedisException` oder `\RedisClusterException` von phpredis geht durch `add` und `cas` nach außen) | Z. 53, 55; add Z. 143, cas Z. 188 | Z. 54, 56; add Z. 150, cas Z. 198 | Z. 52, 54; add Z. 148, cas Z. 196 |
| RedisFactory `throw new \Exception('Redis support is not available')` (dauerhaft, kein vorübergehender Fehler) | Z. 145 | Z. 135, 142 | Z. 136, 140 |
| NoopLockingProvider `isLocked` -> false, `acquireLock` tut nichts | Z. 22, 29 | Z. 23, 31 | Z. 24, 32 |

Laufzeitbild der Tests: `docker run --rm nextcloud:32.0.15-apache php -m` listet `redis` (dazu `apcu`, `memcached`); `phpversion("redis")` 6.3.0, `class_exists("RedisException")` und `class_exists("RedisClusterException")` beide wahr. In CI fehlte ext-redis im Job phpunit (setup-php `extensions:` ohne redis); seit 45-23 steht `redis` am Ende der Liste.

APCu als `memcache.locking` (lib/private/Memcache/Factory.php und APCu.php):

| Stelle | stable33 | stable34 | stable35 |
|---|---|---|---|
| Factory: Locking-Cache ohne Klasse, ohne IMemcache oder `!isAvailable()` -> `NULL_CACHE` (dann DBLockingProvider) | Z. 97-103 | Z. 99-105 | Z. 100-106 |
| Factory: Kommentar "APCu however cannot be shared between PHP instances (CLI and web) anyway." | Z. 69-72 | Z. 71-74 | Z. 72-75 |
| `createLocking()` baut `new $this->lockingCacheClass(...)` | Z. 162 | Z. 165 | Z. 166 |
| APCu::isAvailable, im CLI ohne `apc.enable_cli` false | Z. 111, 116 | Z. 122, 127 | Z. 123, 128 |
| APCu speichert über `apcu_add` und `apcu_cas` im Speicher des Prozesses | Z. 66, 105 | Z. 73, 115 | Z. 74, 116 |

Einrichtungsprüfungen von Nextcloud: apps/settings/lib/SetupChecks/FileLocking.php meldet den NoopLockingProvider als Fehler ("Transactional File Locking is disabled. ...", stable33 Z. 47, stable34 Z. 50, stable35 Z. 50; Bedingung `instanceof NoopLockingProvider` Z. 37 / 39 / 39); MemcacheConfigured.php liest `memcache.locking` nur für das Memcached-Modul (Z. 38 / 41 / 42). Für APCu als Locking-Cache gibt es keine Prüfung.

I-45-23-01 (offen, kein Threat dieses Plans): F3 aus #25 ("JPG-Schleife") ist nicht belegt; Kandidat backend/src/findling/worker/poller.py (ein Zeitüberschreiten einer Datei erstattet den ganzen Stapel zurück). Wartet auf Logs des Melders; belegen sie ihn, eigener Plan.

I-45-23-02 (INFO, vorbestehend seit 1.4.0, kein Fix): Bei `filelocking.enabled = false` liefert Server.php den NoopLockingProvider (Tabelle oben). Dann antwortet `isLocked()` immer false, crawling() sieht die zeilenlosen Sekunden einer Crawl-Scheibe nicht, und der Slice-Lock serialisiert nicht. Nextcloud meldet diese Einstellung selbst als Fehler (FileLocking.php); nach `Entscheid Locking 45-23` (l1) verweist die Doku in 45-25 darauf, ohne eigenen Hinweis.

I-45-23-03 (INFO, vorbestehend seit 1.4.0, Umgang nach l1 in 45-25): Unter APCu als `memcache.locking` liegen die Locks im Speicher des jeweiligen PHP-Prozesses bzw. FPM-Pools. Ein CLI-Prozess (Cron, `occ`) und FPM sehen ihre Locks gegenseitig nicht (Kommentar in Factory.php, Tabelle oben); crawling() im FPM (QueueController) sieht also den Marker einer Crawl-Scheibe aus dem Cron nicht. Auch zwei CLI-Prozesse sehen sich nicht: mit `apc.enable_cli` hat jeder CLI-Prozess seinen eigenen APCu-Speicher, der mit dem Prozess endet; ohne `apc.enable_cli` ist APCu im CLI nicht verfügbar (APCu::isAvailable), die Factory fällt auf NullCache und Server.php auf den DBLockingProvider zurück, der FPM-Pool aber sperrt weiter in APCu. Weder Cron und `occ background-job:execute` noch zwei Cron-Läufe sehen sich also. Für den Slice-Lock gilt das seit 1.2.0 genauso.

I-45-23-04 (INFO, vorbestehend, Umgang nach l1 in 45-25): Dieselbe Trennung hebt unter APCu die Serialisierung über den Slice-Lock zwischen Cron (CLI) und Nachschub-Route (FPM) auf; eine Scheibe kann dann zweimal gleichzeitig laufen. Kein Fix in 45-23; nach `Entscheid Locking 45-23` (l1) bekommt die Admin-Seite in 45-25 einen Hinweis und docs/admin-page.md einen Abschnitt.

I-45-23-05 (INFO, für 45-20 Task 2): Die Live-Probe hält Locks per CLI-Skript und braucht deshalb einen von CLI und FPM geteilten Provider (Redis, Memcached oder DB). Unter APCu stellt 45-20 um und begründet es im Audit.

I-45-23-06 (LOW, vorbestehend, behoben in 45-23 Task 2): Stelle StorageCrawlJob::run(), Nehmen des Slice-Locks (bis 26b80929 Z. 225-237) mit nur `catch (LockedException)`; Folge: eine `OCP\DB\Exception` des DBLockingProvider oder ein `\RedisException` beendete die Kette des Mounts ohne Nachfolger (die Zeile der QueuedJob ist vor run() gelöscht), wie vor 43-27 in crawlSlice; seit 1d47563b (2026-09-11, erstes Release v1.2.0, `git log -S 'acquireLock(self::LOCK_NAME'`); Fix: zweiter Zweig `catch (\Throwable $e)` mit `self::isPassingLockError($e)` und der Grenze MAX_RETRIES, Nachfolger mit gleichem Modus, gleichen Summen und `retries + 1` vor der warning-Zeile ohne Pfad; Tests `testADatabaseErrorAtTheSliceLockKeepsTheChain`, `testASliceLockThatKeepsFailingEndsTheChainLoudly`, `testAnUnexpectedErrorAtTheSliceLockEndsTheChainAtOnce`; Mutation M23.

#### F1 Marker

Umsetzung: `StorageCrawlJob::CRAWL_ACTIVE_LOCK = 'findling/crawl-active'`. run() setzt nach dem Slice-Lock `$marked = false;` und öffnet sofort das try, dessen finally den Slice-Lock freigibt; darin nur im Crawl-Modus `acquireLock(CRAWL_ACTIVE_LOCK)` mit zwei catch-Zweigen: LockedException (fremder Marker eines abgestürzten Prozesses: debug ohne Werte, die Scheibe läuft, kein Freigeben) und Throwable (vorübergehend nach `isPassingLockError()` und unter MAX_RETRIES: Nachfolger mit `retries + 1`, dann warning `'Findling: a crawl slice could not take the crawl marker and will be tried again'` mit `storage_id`, `retries`, `exception`, return; sonst weiterwerfen). Freigabe verschachtelt: `finally { try { if ($marked) releaseLock(CRAWL_ACTIVE_LOCK) } finally { releaseLock(LOCK_NAME) } }`. Beim Nehmen des Slice-Locks neu `catch (\Throwable $e)` nach demselben Muster (Meldung `'Findling: a crawl slice could not take the slice lock and will be tried again'`, Modus und Summen reisen mit, kein releaseLock). `isPassingLockError()`: `DbException`, `is_a($e, 'RedisException')`, `is_a($e, 'RedisClusterException')`. CrawlAdvanceService::crawling() liest als Lock-Signal nur noch `isLocked(StorageCrawlJob::CRAWL_ACTIVE_LOCK, ILockingProvider::LOCK_EXCLUSIVE)`; der Klassen-Docblock ("It also takes no lock of its own") bleibt wahr. CI: `redis` in `extensions:` des Jobs phpunit.

Tests: CrawlAdvanceServiceTest `testARecountSliceHoldingTheSliceLockIsNoCrawl`, `testTheSliceLockAloneIsNoCrawl`, `testARunningCrawlSliceWithoutARowIsAnUnfinishedCrawl` (ersetzt `testARunningSliceIsAnUnfinishedCrawl`). StorageCrawlJobTest mit einem Fake-ILockingProvider (anonyme Klasse, Methoden wie OCP v33 bis v35, exklusive Locks, LockedException bei Doppelbelegung, protokolliert acquire und release, wirft auf Wunsch): `testACrawlSliceHoldsTheCrawlMarkerWhileItRuns`, `testARecountSliceNeverTakesTheCrawlMarker`, `testTheCrawlMarkerIsReleasedWhenTheSliceThrows`, `testAStaleCrawlMarkerDoesNotStopTheCrawl`, `testALostSliceLockNeverTakesTheCrawlMarker`, `testAFailingCrawlMarkerLeavesNoSliceLockBehind` (DbException und `\RedisException`, vorher `class_exists(\RedisException::class)`), `testACrawlMarkerThatKeepsFailingEndsTheSliceLoudly`, `testAFailingMarkerReleaseStillReleasesTheSliceLock`, `testAnUnexpectedErrorAtTheCrawlMarkerEndsTheSliceAtOnce`, `testADatabaseErrorAtTheSliceLockKeepsTheChain` (DbException und `\RedisException`, je Crawl und Nachzählung mit Summen), `testASliceLockThatKeepsFailingEndsTheChainLoudly`, `testAnUnexpectedErrorAtTheSliceLockEndsTheChainAtOnce`. Reihenfolge Nachfolger vor warning über ein gemeinsames Protokoll von Jobliste und Logger. Angepasst: `testADatabaseErrorInASliceReschedulesTheCursorItArrivedWith` und `testTheFifthFailureInARowWithoutProgressEndsTheChainLoudly` erwarteten genau ein releaseLock mit LOCK_NAME; sie laufen jetzt auf dem Fake und prüfen beide Freigaben in der Reihenfolge Marker, Slice-Lock, je genau einmal, und dass danach nichts gehalten ist.

RED (nicht committet): `bash scripts/dev/phpunit_docker.sh --filter 'CrawlAdvanceServiceTest|StorageCrawlJobTest'` -> `Tests: 38, Assertions: 128, Errors: 10, Failures: 3.`, wörtlich (Errors 3 bis 9 mit derselben Meldung wie 1 und 2):

```
1) OCA\Findling\Tests\Unit\StorageCrawlJobTest::testADatabaseErrorInASliceReschedulesTheCursorItArrivedWith
Error: Undefined constant OCA\Findling\BackgroundJobs\StorageCrawlJob::CRAWL_ACTIVE_LOCK
2) OCA\Findling\Tests\Unit\StorageCrawlJobTest::testTheFifthFailureInARowWithoutProgressEndsTheChainLoudly
Error: Undefined constant OCA\Findling\BackgroundJobs\StorageCrawlJob::CRAWL_ACTIVE_LOCK
3) OCA\Findling\Tests\Unit\StorageCrawlJobTest::testACrawlSliceHoldsTheCrawlMarkerWhileItRuns
4) OCA\Findling\Tests\Unit\StorageCrawlJobTest::testTheCrawlMarkerIsReleasedWhenTheSliceThrows
5) OCA\Findling\Tests\Unit\StorageCrawlJobTest::testAStaleCrawlMarkerDoesNotStopTheCrawl
6) OCA\Findling\Tests\Unit\StorageCrawlJobTest::testAFailingCrawlMarkerLeavesNoSliceLockBehind
7) OCA\Findling\Tests\Unit\StorageCrawlJobTest::testACrawlMarkerThatKeepsFailingEndsTheSliceLoudly
8) OCA\Findling\Tests\Unit\StorageCrawlJobTest::testAFailingMarkerReleaseStillReleasesTheSliceLock
9) OCA\Findling\Tests\Unit\StorageCrawlJobTest::testAnUnexpectedErrorAtTheCrawlMarkerEndsTheSliceAtOnce
10) OCA\Findling\Tests\Unit\StorageCrawlJobTest::testADatabaseErrorAtTheSliceLockKeepsTheChain
OCP\DB\Exception: database is locked

1) OCA\Findling\Tests\Unit\CrawlAdvanceServiceTest::testARecountSliceHoldingTheSliceLockIsNoCrawl
Failed asserting that true is false.
2) OCA\Findling\Tests\Unit\CrawlAdvanceServiceTest::testTheSliceLockAloneIsNoCrawl
Failed asserting that true is false.
3) OCA\Findling\Tests\Unit\StorageCrawlJobTest::testARecountSliceNeverTakesTheCrawlMarker
Failed asserting that two arrays are identical.
```

Abweichung von "RED nur mit den neuen Fällen": die beiden angepassten Fälle (Errors 1 und 2) waren rot, weil sie die noch fehlende Konstante nennen, nicht wegen einer geänderten Aussage. Vor dem Fix schon grün und deshalb keine RED-Zeugen: `testARunningCrawlSliceWithoutARowIsAnUnfinishedCrawl` (der gehaltene Slice-Lock genügte bisher), `testALostSliceLockNeverTakesTheCrawlMarker` (bisher kein Marker), `testASliceLockThatKeepsFailingEndsTheChainLoudly` und `testAnUnexpectedErrorAtTheSliceLockEndsTheChainAtOnce` (bisher warf jeder Fehler am Slice-Lock weiter); sie halten Verhalten fest, das der Fix nicht verlieren darf, und M23 und M24 belegen die Zweige, die sie bewachen.

GREEN gefiltert: derselbe Aufruf -> `OK (38 tests, 225 assertions)`.

#### F1 Mutationen

Je einzeln, danach die Quellen byte-gleich zurück (`restored_identical=yes` je Lauf, SHA-256 über StorageCrawlJob.php, CrawlAdvanceService.php und SettingsService.php vor und nach); Skripte `<scratchpad>/mutate23.py` und `<scratchpad>/mut23.sh`, je gefiltertes PHPUnit `CrawlAdvanceServiceTest|StorageCrawlJobTest`.

(M1) crawling() liest wieder LOCK_NAME statt CRAWL_ACTIVE_LOCK -> rot: `testARecountSliceHoldingTheSliceLockIsNoCrawl`, `testTheSliceLockAloneIsNoCrawl`, `testARecountSliceNeverTakesTheCrawlMarker` (`Failures: 3`)
(M2) Marker auch im recount-Modus (`if (true)` statt `if (!$recount)`) -> rot: `testARecountSliceNeverTakesTheCrawlMarker` (`Failures: 1`)
(M3) Marker im Crawl-Modus weggelassen (`if (false)`) -> rot: `testACrawlSliceHoldsTheCrawlMarkerWhileItRuns`, dazu `testADatabaseErrorInASliceReschedulesTheCursorItArrivedWith`, `testTheFifthFailureInARowWithoutProgressEndsTheChainLoudly`, `testAFailingCrawlMarkerLeavesNoSliceLockBehind`, `testACrawlMarkerThatKeepsFailingEndsTheSliceLoudly`, `testAFailingMarkerReleaseStillReleasesTheSliceLock`, `testAnUnexpectedErrorAtTheCrawlMarkerEndsTheSliceAtOnce` (`Failures: 7`)
(M4) Freigabe des Markers aus dem finally entfernt -> rot: `testTheCrawlMarkerIsReleasedWhenTheSliceThrows`, dazu `testACrawlSliceHoldsTheCrawlMarkerWhileItRuns`, `testADatabaseErrorInASliceReschedulesTheCursorItArrivedWith`, `testTheFifthFailureInARowWithoutProgressEndsTheChainLoudly`, `testAFailingMarkerReleaseStillReleasesTheSliceLock` (`Failures: 5`)
(M5) fremden Marker freigeben (`if (true)` statt `if ($marked)` vor dem releaseLock des Markers) -> rot: `testAStaleCrawlMarkerDoesNotStopTheCrawl`, dazu `testAFailingCrawlMarkerLeavesNoSliceLockBehind` (`Failures: 2`)
(M17) Marker vor dem try genommen (Nehmen samt beiden catch-Zweigen vor das try gezogen, dessen finally den Slice-Lock freigibt) -> rot: `testAFailingCrawlMarkerLeavesNoSliceLockBehind`, dazu `testACrawlMarkerThatKeepsFailingEndsTheSliceLoudly`, `testAnUnexpectedErrorAtTheCrawlMarkerEndsTheSliceAtOnce` (`Failures: 3`, der Slice-Lock bleibt gehalten)
(M18) kein Nachfolger bei einem Fehler beim Marker (scheduleAfter im Throwable-Zweig entfernt) -> rot: `testAFailingCrawlMarkerLeavesNoSliceLockBehind` (`Failures: 1`)
(M21) Grenze `$retries + 1 >= self::MAX_RETRIES` im Zweig des Markers entfernt -> rot: `testACrawlMarkerThatKeepsFailingEndsTheSliceLoudly` (`Failures: 1`)
(M22) flaches statt verschachteltes finally (beide releaseLock-Aufrufe hintereinander) -> rot: `testAFailingMarkerReleaseStillReleasesTheSliceLock` (`Failures: 1`)
(M23) kein Nachfolger bei einem vorübergehenden Fehler am Slice-Lock (scheduleAfter im neuen Zweig entfernt) -> rot: `testADatabaseErrorAtTheSliceLockKeepsTheChain` (`Failures: 1`)
(M24) `isPassingLockError()` antwortet für jede Ausnahme true -> rot: `testAnUnexpectedErrorAtTheCrawlMarkerEndsTheSliceAtOnce` und `testAnUnexpectedErrorAtTheSliceLockEndsTheChainAtOnce` (`Failures: 2`)

Baumhash php/ nach Task 2: Rezept und unabhängige Pipeline (find, sort, sed, sha256sum) `41a8dc1f...` mit 143 Dateien; Positivkontrolle Rezept und Pipeline über `git archive 6227bdff` -> `ff141406...` mit 143 (gleich dem bisherigen PHP_TREE_HASH_TODAY).

Gates Task 2 (verify-Zeile wörtlich aus `<scratchpad>/v23_t2.sh`, seriell, Docker vorher und danach leer) -> `VERIFY_EXIT=0`: `STATIC_OK`, PHPUnit voll `OK (1396 tests, 8796 assertions)`, `php_gates_docker.sh all` grün (Psalm-Taint je 0 Befunde gegen v33.0.9, v34.0.6, v35.0.3, Probe 3; keine Meldung zu `is_a($e, 'RedisException')`; php-cs-fixer ohne Verstoß; zizmor und actionlint grün, Proben gesehen), pytest `tests/test_php_static_gates.py tests/test_reconcile.py tests/test_measurement_scripts.py` `748 passed`.

#### Mindestabstand

Umsetzung nach `Entscheid Mindestabstand 45-23` (6h) und `Entscheid Regeln Nachzählung 45-23` (r1): `SettingsService::RECOUNT_MIN_INTERVAL_SECONDS = 6 * 3600` mit Docblock (a) bis (c), gemessen ab dem Start der letzten Runde (KEY_SCAN_RECOUNTED_AT). `scanRecountDue()` liest `$last` einmal; `$last > $now` -> fällig; Marke gesetzt -> fällig genau dann, wenn `$now - $last >= RECOUNT_MIN_INTERVAL_SECONDS` oder `rulesChangedAt() > $last` (r1, dieselbe Vergleichsrichtung wie `AdminViewService::rulesPending`, `$recountedAt < $rulesChangedAt`); ohne Marke wie bisher die 24 h. Docblocks von KEY_SCAN_STALE_SINCE, scanRecountDue() und ScanRecountJob ("Why a TimedJob every 15 minutes and a floor of 24 hours" plus neuer Absatz "The minimum interval", mit I4) nachgezogen; run() von ScanRecountJob unverändert.

Tests: SettingsServiceTest `testAMarkWithinTheMinimumIntervalIsNotDue`, `testAMarkAfterTheMinimumIntervalIsDue`, `testARecountStampInTheFutureIsDue` (mit und ohne Marke), `testTheMinimumIntervalLiesBelowTheFloor` (Wert 6 * 3600), `testSavedRulesStartTheRecountWithinTheMinimumInterval`, `testRulesSavedBeforeTheLastRecountWaitForTheMinimumInterval`; `testAMarkMakesTheRecountDue` heißt jetzt `testAMarkMakesTheRecountDueOnceTheMinimumIntervalHasPassed` (letzte Runde vor dem Mindestabstand plus eine Stunde). ScanRecountJobTest `testAMarkWithinTheMinimumIntervalPlansNothing` (kein add, kein getMounts, kein info-Log, Marke und Zeitstempel unverändert). Angepasst: `testAMarkPlansOneRecountChainPerMount` stand mit einer Runde vor einer Stunde auf der alten Regel; die letzte Runde liegt dort jetzt genau RECOUNT_MIN_INTERVAL_SECONDS zurück, die Aussage (eine Kette je Mount, Marke gelöscht, Zeit gemerkt) bleibt.

RED (nicht committet): `bash scripts/dev/phpunit_docker.sh --filter 'SettingsServiceTest|ScanRecountJobTest'` -> `Tests: 90, Assertions: 207, Errors: 5, Failures: 3.`, wörtlich:

```
1) OCA\Findling\Tests\Unit\ScanRecountJobTest::testAMarkPlansOneRecountChainPerMount
Error: Undefined constant OCA\Findling\Service\SettingsService::RECOUNT_MIN_INTERVAL_SECONDS
2) OCA\Findling\Tests\Unit\SettingsServiceTest::testAMarkMakesTheRecountDueOnceTheMinimumIntervalHasPassed
Error: Undefined constant OCA\Findling\Service\SettingsService::RECOUNT_MIN_INTERVAL_SECONDS
3) OCA\Findling\Tests\Unit\SettingsServiceTest::testAMarkWithinTheMinimumIntervalIsNotDue
Error: Undefined constant OCA\Findling\Service\SettingsService::RECOUNT_MIN_INTERVAL_SECONDS
4) OCA\Findling\Tests\Unit\SettingsServiceTest::testAMarkAfterTheMinimumIntervalIsDue
Error: Undefined constant OCA\Findling\Service\SettingsService::RECOUNT_MIN_INTERVAL_SECONDS
5) OCA\Findling\Tests\Unit\SettingsServiceTest::testTheMinimumIntervalLiesBelowTheFloor
Error: Undefined constant OCA\Findling\Service\SettingsService::RECOUNT_MIN_INTERVAL_SECONDS

1) OCA\Findling\Tests\Unit\ScanRecountJobTest::testAMarkWithinTheMinimumIntervalPlansNothing
OCA\Findling\Service\StorageService::getMounts(): iterable was not expected to be called.
2) OCA\Findling\Tests\Unit\SettingsServiceTest::testARecountStampInTheFutureIsDue
Failed asserting that false is true.
3) OCA\Findling\Tests\Unit\SettingsServiceTest::testRulesSavedBeforeTheLastRecountWaitForTheMinimumInterval
Failed asserting that true is false.
```

Vor dem Fix schon grün und deshalb kein RED-Zeuge: `testSavedRulesStartTheRecountWithinTheMinimumInterval` (bisher machte jede Marke fällig); M8 belegt, dass er den Regelzweig bewacht.

GREEN gefiltert: derselbe Aufruf -> `OK (90 tests, 222 assertions)`.

#### Mindestabstand Mutationen

Je einzeln mit denselben Skripten (`<scratchpad>/mutate23.py`, `<scratchpad>/mut23.sh`), gefiltertes PHPUnit `SettingsServiceTest|ScanRecountJobTest`, danach byte-gleich zurück (`restored_identical=yes`).

(M6) Mindestabstand entfernt (Marke gesetzt -> immer fällig) -> rot: `testAMarkWithinTheMinimumIntervalIsNotDue`, dazu `testAMarkWithinTheMinimumIntervalPlansNothing`, `testRulesSavedBeforeTheLastRecountWaitForTheMinimumInterval` (`Failures: 3`)
(M7) `>` statt `>=` an der Grenze -> rot: `testAMarkAfterTheMinimumIntervalIsDue`, dazu `testAMarkPlansOneRecountChainPerMount` (`Failures: 2`)
(M8) bei r1 Regelausnahme entfernt (`|| $this->rulesChangedAt() > $last` gestrichen) -> rot: `testSavedRulesStartTheRecountWithinTheMinimumInterval` (`Failures: 1`)
(M9) Zukunftsfall entfernt -> rot: `testARecountStampInTheFutureIsDue` (`Failures: 1`)

Doku: docs/admin-page.md Absatz "Wie der Nenner aktuell bleibt" (Z. ~94: geprüft alle 15 Minuten, nach Dateiereignissen höchstens alle sechs Stunden, nach gespeicherten geänderten Regeln binnen 15 Minuten, sonst spätestens nach 24 Stunden; Abstand ab dem Start der letzten Runde, keine Pause, I4; Grund #25), "Wenn der Zähler über dem Nenner steht" (höchstens sechs Stunden plus die Laufzeit, nach gespeicherten Regeln höchstens 15 Minuten plus die Laufzeit). `grep -rn "15 Minuten\|15 minutes\|15 Min" docs/*.md README*.md` danach: admin-page.md Z. 95 (der Prüftakt des Jobs, stimmt), Z. 195 (das Fenster nach gespeicherten Regeln, r1), Z. 991 ("gespeicherte Regeln machen sie fällig, und ScanRecountJob prüft das alle 15 Minuten", bei r1 unverändert wahr), store-listing.md Z. 3867 (Wartezeit des App Stores, keine Nachzählung). Alle bewusst. README*.md ohne Treffer.

CHANGELOG: Text 1 wörtlich nach dem Entwurf im Plan (unter `Freigabe Texte #25 45-23` steht keine Wortlautzeile, r1) in [1.7.0] unter "### Fixed", "### Behoben", "### Corrigé", Umbruch bei etwa 76 Zeichen mit zwei Leerzeichen Einzug wie die Nachbarzeilen, kein close/fix/resolve-Wort vor #25.

I-45-23-07 (INFO, neu, kein Fix in 45-23): Die Migration Version001500Date20261012000000 setzt bei einem Update von einer Version vor 1.5 die Marke, damit der Nenner unter der Allowlist von 1.5 neu gezählt wird; ihr Docblock sagt "ScanRecountJob sees the mark within its interval". Mit dem Mindestabstand startet diese Runde bei einem Sprung von vor 1.5 direkt auf 1.7.0 erst sechs Stunden nach dem Start der letzten Runde (frühestens). In diesem Fenster zeigt die Seite den Satz "Seit der letzten Zählung sind Dateien dazugekommen" bzw. den alten Nenner. Kein Datenverlust, die 24 h gelten weiter als Obergrenze; Owner-Frage, ob eine Marke aus einer Migration wie gespeicherte Regeln sofort zählen soll (eigener Schlüssel) oder hingenommen und nur im Docblock nachgezogen wird.

Baumhash php/ nach Task 3: Rezept und unabhängige Pipeline `976184c1...` mit 143 Dateien; Positivkontrolle Rezept und Pipeline über `git archive 104bf781` -> `41a8dc1f...` mit 143 (gleich dem Wert nach Task 2).

Gates Task 3 (verify-Zeile wörtlich aus `<scratchpad>/v23_t3.sh`, seriell, Docker vorher und danach leer) -> `VERIFY_EXIT=0`: `STATIC_OK` (Mindestabstand aus der Entscheidzeile 6, r1, Text 1 EN/DE/FR wörtlich unter Fixed/Behoben/Corrigé, keine Gedankenstriche), PHPUnit voll `OK (1403 tests, 8810 assertions)`, `php_gates_docker.sh all` grün (Psalm-Taint je 0 Befunde gegen v33.0.9, v34.0.6, v35.0.3, Probe 3; php-cs-fixer ohne Verstoß; zizmor und actionlint grün), ruff `All checks passed!`, ruff format `260 files already formatted`, pyright latest `0 errors, 0 warnings, 0 informations`, vulture ohne Fund, pytest `tests/test_changelog_translations.py tests/test_store_metadata.py tests/test_php_static_gates.py tests/test_measurement_scripts.py` `808 passed`.

### RED und GREEN 45-24

Plan 45-24, 2026-11-23, nach `Entscheid Rückhalt-Weg 45-23` (z1) und `Freigabe Texte #25 45-23` (Texte 2 bis 4 wörtlich wie im Plan 45-23, keine Wortlautzeile). Kopf vor dem Plan 3d18b701.

#### F2 Rückhalt

Umsetzung: repo.py `QUIET_HELD_MARK: Final = "reconcile_quiet_held_since"` (ganze Sekunden als Text, fehlend oder leer = nicht zurückgehalten). reconcile.py `BACKSTOP_FACTOR: Final = 2`; das Gate ist geteilt in `_gate(queue)` (liefert den Grund offen, Crawl, Ruhemarke, unlesbar samt QueueStats, ohne Log; unlesbar mit Back-off wie bisher) und `_quiet(reason, stats)` (Rundenzustand und die beiden info-Zeilen, byte-gleich). run_once setzt zu Beginn das Rundenflag `_backstop` zurück; hält nur die Ruhemarke und ist `_is_due` wahr, liest `_held_since(store)` den Zeitpunkt (fehlend, keine Zahl oder Zukunft -> jetzt geschrieben); liegt er mindestens `BACKSTOP_FACTOR * min_interval * 3600` zurück, gilt die Runde als offen, das Flag steht, und genau eine warning-Zeile `reconcile walks although the quiet mark holds, held for %d hours, %d rows are scheduled and the quiet mark is %d` (Stunden abgerundet). `_walk` vor jeder Scheibe: Ruhemarke mit Flag -> offen ohne Zeile; ohne Flag -> Zeitpunkt setzen, falls keiner steht, dann wie bisher info-Zeile und Ende. Nach ROUND_WALKED löscht `_clear_held_since` den Zeitpunkt (leerer Text, nur wenn einer steht). Crawl setzt und löscht nichts. Docstrings `_quiet`, `_gate`, `_held_since`, `_is_due`, run_once Schritt 1 und 2 nachgezogen; catchup.py Modul-Docstring nennt den Rückhalt (#25, backstop, nie neben einem Crawl), Code byte-gleich.

Tests (tests/test_reconcile.py, Abschnitt "the backstop against the quiet mark"): `test_a_due_walk_held_by_the_quiet_mark_stamps_since_when_once`, `test_a_walk_that_is_not_due_sets_no_stamp`, `test_a_crawl_alone_never_sets_the_stamp`, `test_the_quiet_mark_gives_way_after_twice_the_interval`, `test_the_backstop_does_not_open_before_twice_the_interval`, `test_the_backstop_never_walks_while_the_crawl_is_unfinished`, `test_the_backstop_holds_through_every_slice_of_the_cycle` (mit Gegenfall Crawl ab der zweiten Scheibe), `test_an_unreadable_queue_holds_the_backstop_too`, `test_a_finished_cycle_clears_the_stamp`, `test_a_short_dip_below_the_quiet_mark_keeps_the_stamp`, `test_a_walk_held_mid_cycle_stamps_too`, `test_the_stamp_survives_a_new_reconcile_object` (erstes Objekt stempelt zwei Tage vorher, frisches Objekt auf demselben Store öffnet), `test_an_unreadable_or_future_stamp_starts_the_wait_again` ("abc" und NOW + 3600), `test_the_catch_up_walks_under_the_backstop` (FINDLING_RECONCILE_ENABLED true über run_once, false über `run(once=True)` wie main.py; beide Male CATCHUP_DONE und Zeitpunkt leer), `test_a_backstop_round_logs_no_stand_down_line` (mit Gegenfall Rückhalt zu). Bestehende Fälle unverändert.

Randfälle I5: Abgleich in der Wartephase ausgeschaltet -> Zeitpunkt bleibt im Store, ein frisches Objekt zählt die alte Wartezeit weiter (`test_the_stamp_survives_a_new_reconcile_object`); Nachholweg bei ausgeschaltetem Abgleich -> Rückhalt gilt genauso (`test_the_catch_up_walks_under_the_backstop[false]`); das Statusfeld bei ausgeschaltetem Abgleich folgt in Task 2.

RED (nicht committet), erster Lauf vor jeder Änderung an src: `PYTHONUTF8=1 uv run --no-sync python -m pytest -q tests/test_reconcile.py` -> `17 failed, 104 passed`; alle 17 neuen Fälle rot mit `AttributeError: module 'findling.store.repo' has no attribute 'QUIET_HELD_MARK'`. Zweiter RED-Lauf mit nur der Konstante in repo.py (reconcile.py unverändert), derselbe Aufruf -> `11 failed, 110 passed`, wörtlich:

```
FAILED tests/test_reconcile.py::test_a_due_walk_held_by_the_quiet_mark_stamps_since_when_once
FAILED tests/test_reconcile.py::test_the_quiet_mark_gives_way_after_twice_the_interval
FAILED tests/test_reconcile.py::test_the_backstop_holds_through_every_slice_of_the_cycle
FAILED tests/test_reconcile.py::test_a_finished_cycle_clears_the_stamp - Asse...
FAILED tests/test_reconcile.py::test_a_walk_held_mid_cycle_stamps_too - Asser...
FAILED tests/test_reconcile.py::test_the_stamp_survives_a_new_reconcile_object
FAILED tests/test_reconcile.py::test_an_unreadable_or_future_stamp_starts_the_wait_again[abc]
FAILED tests/test_reconcile.py::test_an_unreadable_or_future_stamp_starts_the_wait_again[1800003600]
FAILED tests/test_reconcile.py::test_the_catch_up_walks_under_the_backstop[true]
FAILED tests/test_reconcile.py::test_the_catch_up_walks_under_the_backstop[false]
FAILED tests/test_reconcile.py::test_a_backstop_round_logs_no_stand_down_line
11 failed, 110 passed in 7.77s
```

Vor dem Fix schon grün und deshalb keine RED-Zeugen, sondern Wächter des bestehenden Verhaltens: `test_a_walk_that_is_not_due_sets_no_stamp`, `test_a_crawl_alone_never_sets_the_stamp`, `test_the_backstop_does_not_open_before_twice_the_interval`, `test_the_backstop_never_walks_while_the_crawl_is_unfinished`, `test_an_unreadable_queue_holds_the_backstop_too`, `test_a_short_dip_below_the_quiet_mark_keeps_the_stamp` (bisher schrieb nichts den Zeitpunkt). Ihre Zweige belegen M10, M11 und M12.

GREEN gefiltert: derselbe Aufruf -> `121 passed`.

Weitere Tests: tests/test_backup_pause.py tests/test_catchup.py tests/test_doc_keys.py tests/test_guest_parity.py tests/test_lifecycle.py tests/test_main_lifespan.py tests/test_measurement_scripts.py tests/test_phase31_audit.py tests/test_phase36_audit.py tests/test_phase41_audit.py tests/test_phase43_audit.py tests/test_phase43_audit_roots.py tests/test_poller.py tests/test_reconcile.py tests/test_reconcile_vanished.py tests/test_upgrade_seed_steps.py tests/test_v13_wechsel.py

Baumhash backend/src/findling nach Task 1: Rezept und unabhängige Pipeline (find, sort, sed, sha256sum) `6de76760...` mit 83 Dateien; Positivkontrolle Rezept und Pipeline über `git archive 3d18b701` -> `9fa6c443...` mit 83 (gleich dem bisherigen PACKAGE_TREE_HASH_TODAY). php/ unverändert `976184c1...`/143.

#### F2 Mutationen

Je einzeln, danach reconcile.py byte-gleich zurück (`restored_identical=yes`, SHA-256 vor und nach gleich); Skripte `<scratchpad>/mutate24.py` und `<scratchpad>/mut24.sh`, je gefiltertes pytest `tests/test_reconcile.py`.

(M10) Rückhalt prüft crawling nicht (Crawl zählt in run_once wie die Ruhemarke) -> rot: `test_the_backstop_never_walks_while_the_crawl_is_unfinished`, dazu `test_a_crawl_alone_never_sets_the_stamp` (`2 failed`)
(M11) Faktor 1 statt 2 -> rot: `test_the_backstop_does_not_open_before_twice_the_interval` (`1 failed`)
(M12) Zeitpunkt bei jeder offenen Runde gelöscht statt nach ROUND_WALKED -> rot: `test_a_short_dip_below_the_quiet_mark_keeps_the_stamp` (`1 failed`)
(M13) Rundenflag in `_walk` nicht beachtet -> rot: `test_the_backstop_holds_through_every_slice_of_the_cycle`, dazu `test_the_quiet_mark_gives_way_after_twice_the_interval`, `test_the_stamp_survives_a_new_reconcile_object`, `test_the_catch_up_walks_under_the_backstop` [true] und [false], `test_a_backstop_round_logs_no_stand_down_line` (`6 failed`)
(M14) Zeitpunkt bei jedem Tick neu geschrieben -> rot: `test_a_due_walk_held_by_the_quiet_mark_stamps_since_when_once`, dazu sieben weitere (`8 failed`)
(M15) Zukunftswert nicht ersetzt -> rot: `test_an_unreadable_or_future_stamp_starts_the_wait_again` [1800003600] (`1 failed`)

Gates Task 1 (verify-Zeile wörtlich aus `<scratchpad>/v24_t1.sh`, seriell, ohne Docker) -> `VERIFY_EXIT=0`: ruff `All checks passed!`, ruff format `260 files already formatted`, pyright latest `0 errors, 0 warnings, 0 informations`, vulture ohne Fund, pytest über test_reconcile, test_store_repo, test_catchup, test_main_lifespan, test_measurement_scripts und die Liste `Weitere Tests` `1749 passed, 1 skipped`. Der erste Lauf fiel an ruff E501 im neuen catchup.py-Docstring (Zeile zu lang); umbrochen, Baumhash danach neu gerechnet (oben der Wert nach dem Umbruch).

#### Hinweis Admin-Seite

Umsetzung: status.py `reconcileHeldSince: int | None = None` mit Kommentar; `_of()` liest es über `_reconcile_held_since(marks.get(QUIET_HELD_MARK))`: null bei ausgeschaltetem Abgleich (`settings().reconcile_enabled`), leerem oder unlesbarem Wert, Wert <= 0 und einem Zeitpunkt jünger als `reconcile_min_interval_hours * 3600` (Zukunft eingeschlossen); `_volume()` und die Zweige ohne Zustand lassen das Feld auf null. Die Uhr über `_now()`, damit der Test sie festhält. AdminViewService: `'reconcileHeldSince' => $this->optionalCounter($answer, 'reconcileHeldSince'),` neben gatewayUnavailableSince, null in `quietInPause()`. Template: `$reconcileHeld = ...;` und der Absatz `findling-reconcile-held` direkt hinter `findling-gateway-unavailable`, Satz über `p($l->t(...))`. admin.js: `reconcileLine(backend)` nach dem Muster von `gatewayLine` (text und shown, kein innerHTML), Aufruf neben `gatewayLine(...)`, Feld im Fingerabdruck. Text 3 in allen 18 Katalogdateien (de, de_DE, fr wörtlich freigegeben; es, it, nl, pt_BR, pt_PT, zh_TW maschinelle Entwürfe nach den Sprachdokus), je direkt hinter dem Satz zum Content-Gateway, Zeile in den sechs Sprachtabellen, Nachtrag in den fünf deutschsprachigen Sprachdokus, Zählung in docs/l10n-chinese.md auf 384. Schlüsselzahl in test_admin_ui_contract.py 383 -> 384 mit eigenem Absatz; test_store_metadata.py zählt keine Katalogschlüssel und bleibt. Umlaut-Audit des neuen DE-Satzes: hält, länger, läuft, können mit echten Umlauten, keine Ersatzschreibung, kein Gedankenstrich.

Tests: test_status_endpoint.py `reconcileHeldSince` in FIELDS; `test_reconcile_held_since_is_sent_only_after_one_interval` (sieben Fälle: NOW - 24 h -> Zeitpunkt, NOW - 24 h + 1 s -> null, leer -> null, fehlend -> null, "abc" -> null, Abgleich aus -> null, ohne Zustandsdatenbank -> null). test_admin_ui_contract.py `test_a_held_reconcile_has_a_sentence_on_the_page` mit Fehl-Sample (ein es.json ohne den Satz wird genannt, nur er). SettingsControllerTest `testTheOverviewCarriesReconcileHeldSinceAsAnOptionalCounter` (Datenprovider: Zahl, negativ, Text, fehlend) und `testTheOverviewCarriesReconcileHeldSinceAsNullWithoutABackend`; der Helfer `controller(?array $statusAnswer = null)` beantwortet `adminGet('/status', ...)` mit diesem Wert, sonst null wie bisher. AdminViewServiceTest `testPauseHidesTheEstimateAndTheOutageSentences` prüft zusätzlich `reconcileHeldSince` null.

RED (nicht committet): `PYTHONUTF8=1 uv run --no-sync python -m pytest -q tests/test_status_endpoint.py tests/test_admin_ui_contract.py` -> `71 failed, 279 passed`: 62 Fälle der geschlossenen Feldmenge (`set(answer) == FIELDS`, Schlüssel `'reconcileHeldSince'` fehlt), die sieben Fälle von `test_reconcile_held_since_is_sent_only_after_one_interval` (`AttributeError: ... has no attribute '_now'`), `test_a_held_reconcile_has_a_sentence_on_the_page` und `test_the_german_catalogue_covers_both_german_language_codes` (Schlüsselzahl 384). `bash scripts/dev/phpunit_docker.sh --filter 'SettingsControllerTest|AdminViewServiceTest'` -> `Tests: 288, Assertions: 1713, Failures: 9.`: `testPauseHidesTheEstimateAndTheOutageSentences` je Pausenzustand `Failed asserting that 1799900000 is null.` (4), `testTheOverviewCarriesReconcileHeldSinceAsAnOptionalCounter` je Datensatz und `testTheOverviewCarriesReconcileHeldSinceAsNullWithoutABackend` `Failed asserting that an array has the key 'reconcileHeldSince'.` (5).

GREEN: pytest `tests/test_status_endpoint.py tests/test_admin_ui_contract.py tests/test_store_metadata.py tests/test_admin_locale.py tests/test_unified_search_plugin.py tests/test_phase34_audit.py tests/test_lockstep_versions.py tests/test_extract_errors.py` -> `672 passed, 12 skipped`; PHPUnit gefiltert -> `OK (288 tests, 1770 assertions)`.

Baumhashes nach Task 2: backend/src/findling Rezept und Pipeline `d45bc1d3...` mit 83, Positivkontrolle über `git archive 0fc40005` -> `6de76760...` mit 83 (gleich dem Wert nach Task 1); php/ Rezept und Pipeline `05797073...` mit 143, Positivkontrolle über `git archive 0fc40005` -> `976184c1...` mit 143 (gleich dem bisherigen PHP_TREE_HASH_TODAY).

#### Hinweis Mutationen

Skript `<scratchpad>/mut24_m16.sh`, gefiltertes pytest `tests/test_status_endpoint.py -k reconcile_held`, danach status.py byte-gleich zurück (`restored_identical=yes`).

(M16) Schwelle "ein Intervall" in status.py entfernt (`if since <= 0:`, Feld sofort gesendet) -> rot: `test_reconcile_held_since_is_sent_only_after_one_interval` [indexed_volume-1799913601-true-None] (`1 failed, 6 passed`)

Gates Task 2 (verify-Zeile wörtlich aus `<scratchpad>/v24_t2.sh`, seriell, Docker vorher und danach leer) -> `VERIFY_EXIT=0`: PHPUnit voll `OK (1408 tests, 8847 assertions)`, `php_gates_docker.sh all` grün (Psalm-Taint je 0 Befunde gegen v33.0.9, v34.0.6, v35.0.3; php-cs-fixer ohne Verstoß, Probe gesehen; zizmor und actionlint grün), ruff `All checks passed!`, ruff format `260 files already formatted`, pyright latest `0 errors, 0 warnings, 0 informations`, vulture ohne Fund, pytest der neun Dateien `1244 passed, 12 skipped`. Der erste Lauf fiel am php-cs-fixer (Einzug eines mehrzeiligen @param im neuen Docblock von `controller()` in SettingsControllerTest.php); der Docblock steht jetzt als Satz plus einzeiligem @param, PHP-Baumhash danach neu gerechnet (oben der Wert nach der Korrektur).

#### Doku, info.xml, CHANGELOG

docs/reconcile.md: neuer Abschnitt `## Rückhalt bei langer Warteschlange (#25, 1.7.0)` vor dem Nachholzyklus (Schwelle, Meta-Schlüssel `reconcile_quiet_held_since`, Neustart, nie neben einem Crawl, warning-Zeile wörtlich, Hinweis der Admin-Seite ab einem Intervall, Last und Änderung an D-03 nach z1, Verträglichkeit mit älterem Container und Begleit-App 1.6.x, die beiden Randfälle aus I5); Ablauf Schritt 1, "Wie der Takt zustande kommt" (dazu F1: Markierung `findling/crawl-active`, eine Nachzählung ist kein Crawl, Mindestabstand sechs Stunden), Nachholzyklus, Tabelle der Einstellungen und Protokoll nennen den Rückhalt. docs/admin-page.md: Abschnitt `## Hinweis bei wartendem Abgleich` mit DE-Wortlaut, Bedingung `reconcileHeldSince` und Abhilfe; die Liste der Backup-Pause und Weg C nennen ihn. backend/appinfo/info.xml: Beschreibung von FINDLING_RECONCILE_QUIET_MAX wörtlich Text 4; kein Gate auf info.xml musste nachgezogen werden (test_store_metadata, test_lockstep_versions, test_info_xml_defaults grün). CHANGELOG [1.7.0]: Text 2 wörtlich nach dem Entwurf in 45-23-PLAN.md (unter `Freigabe Texte #25 45-23` steht keine Wortlautzeile) unter "### Fixed", "### Behoben", "### Corrigé", direkt hinter Text 1, Umbruch bei 76 Zeichen mit zwei Leerzeichen Einzug, kein close/fix/resolve-Wort vor #25. Umlaut-Audit der neuen deutschen Prosa ohne Ersatzschreibung.

Gates Task 3 (verify-Zeile wörtlich aus `<scratchpad>/v24_t3.sh`, seriell, ohne Docker) -> `VERIFY_EXIT=0`: Text 2 EN/DE/FR wörtlich gefunden, keine Gedankenstriche, ruff, ruff format, pyright latest 0/0/0, vulture ohne Fund, pytest `tests/test_changelog_translations.py tests/test_store_metadata.py tests/test_lockstep_versions.py tests/test_measurement_scripts.py tests/test_reconcile.py` `880 passed`. Zusätzlich gelaufen: `tests/test_info_xml_defaults.py tests/test_config.py tests/test_phase33_audit.py tests/test_phase34_audit.py tests/test_admin_ui_contract.py tests/test_exapp_surface.py tests/test_phase43_audit.py tests/test_phase40_audit.py` `605 passed, 114 skipped`.

### RED und GREEN 45-25

Plan 45-25, 2026-11-23, nach `Entscheid Locking 45-23` (l1, 2026-11-22 18:37 UTC), `Freigabe Text 5 45-25` und `Freigabe Platzhalter 45-25` (beide "Ok", 2026-11-23 02:08 UTC, eingetragen in 504cd787). Kopf vor dem Plan 06e45214. Docker seriell, vor jedem Start `test -z "$(docker ps -q)"` leer.

Locking-Entscheid umgesetzt: l1, Dienst LockingCheckService (APCu und ArrayCache als memcache.locking bei eingeschalteten Dateisperren), Schlüssel lockingUnshared im Überblick, Hinweis findling-banner-locking in der Hinweisleiste direkt nach findling-banner-parallel, Text 5 in 18 Katalogen und sechs Sprachtabellen, Abschnitt "Dateisperren und Hintergrundjobs (ab 1.7.0)" in docs/admin-page.md mit Verweis auf die Einrichtungsprüfung "Transactional File Locking"

#### Locking-Hinweis

Quellen: dieselben Abzüge wie unter `#### Quellen F1` (nextcloud/server stable33 1732389, stable34 0d928f1, stable35 dd471ac, `<scratchpad>/src23/`), am 2026-11-23 erneut gelesen.

| Stelle | stable33 | stable34 | stable35 |
|---|---|---|---|
| Server.php: `getSystemValueBool('filelocking.enabled', true)` (außerhalb von PHPUNIT_RUN) | Z. 939 | Z. 972 | Z. 870 |
| Server.php: `createLocking('lock')`, kein NullCache -> MemcacheLockingProvider über den Cache aus `memcache.locking` | Z. 942-945 | Z. 975-978 | Z. 873-876 |
| Server.php: sonst DBLockingProvider | Z. 947 | Z. 980 | Z. 878 |
| Server.php: `filelocking.enabled` false -> `new NoopLockingProvider()` | Z. 954 | Z. 987 | Z. 885 |
| Server.php: Factory bekommt `$config->getValue('memcache.locking', null)` | Z. 626 | Z. 659 | Z. 580 |
| Factory.php: Klasse fehlt, kein IMemcache oder `!isAvailable()` -> `NULL_CACHE` ("don't fall back since the fallback might not be suitable for storing lock") | Z. 97-103 | Z. 99-105 | Z. 100-106 |
| Factory.php: `ltrim($lockingCacheClass, '\\')` | Z. 106 | Z. 108 | Z. 109 |
| ArrayCache.php: `protected $cachedData = []`, `isAvailable()` -> `return true` | Z. 14, 139-140 | Z. 14, 149-150 | Z. 15, 150-151 |
| APCu.php: `isAvailable()`, im CLI ohne `apc.enable_cli` false | Z. 111, 116 | Z. 122, 127 | Z. 123, 128 |
| SetupChecks/FileLocking.php: Name "Transactional File Locking"; `instanceof NoopLockingProvider` -> `SetupResult::error` ("Transactional File Locking is disabled. ... Please remove the `'filelocking.enabled' => false` configuration entry ..."); DBLockingProvider -> info | Z. 29, 37, 46-47, 53 | Z. 30, 39, 49-50, 56 | Z. 30, 39, 49-50, 56 |
| SetupChecks/MemcacheConfigured.php: liest `memcache.locking` nur für das Memcached-Modul | Z. 38 | Z. 41 | Z. 42 |
| config.sample.php: `'memcache.locking' => '\\OC\\Memcache\\Redis'` als Beispiel; `filelocking.enabled` steht dort nicht (nur `filelocking.ttl` Z. 2571/2739/2760 und `filelocking.debug`) | Z. 2579 | Z. 2747 | Z. 2768 |

Bedingung daraus: unshared() ist false, wenn `filelocking.enabled` false ist (Noop: Nextcloud meldet ihn selbst als Fehler, mit der genaueren Abhilfe); sonst true genau dann, wenn `memcache.locking` ein String ist, der nach `ltrim(..., '\\')` per `strcasecmp(...) === 0` gleich `OC\Memcache\APCu` oder `OC\Memcache\ArrayCache` ist; jeder andere Wert (fehlend, Redis, Memcached, keine Zeichenkette) false. Kein Log, kein Wurf. Grenze im Docblock (Wort `NullCache`): fehlt die Klasse nur in einer SAPI (etwa ext-redis nur im FPM), fällt diese SAPI über NullCache auf den DBLockingProvider zurück, und der Dienst erkennt die Trennung nicht.

Ort: die Hinweisleiste `#findling-coverage-banners` im Block "Deckungsgrad der Suche", direkt nach `findling-banner-parallel`. Sie zeigt schon den anderen Konfigurationsfehler des Servers, den der Admin außerhalb von Findling behebt (fulltextsearch daneben), und ist die Stelle, auf die der Admin bei einem Problem mit der Indexierung schaut. Einen besser passenden Statusbereich gibt es auf der Seite nicht: die Zeilen unter dem Deckungsgrad beschreiben den Zustand der Engine und werden vom Skript umgeschaltet, der Hinweis hängt aber nur an config.php und wird wie der parallel-Hinweis nur auf dem Server gerendert.

Umsetzung: php/lib/Service/LockingCheckService.php (final class, Konstruktor `IConfig $config`, Konstante UNSHARED_CLASSES, Methode `unshared(): bool`), AdminViewService nimmt den Dienst direkt nach ParallelSearchService und trägt `'lockingUnshared' => $this->lockingCheck->unshared(),` genau einmal neben `'parallelSearch'`, Typangabe `lockingUnshared:bool` im Docblock des Überblicks. templates/admin.php: `$lockingUnshared = ($_['lockingUnshared'] ?? false) === true;` neben `$parallelSearch`, Absatz `findling-banner-locking` mit Icon `$alertIcon` und `findling-banner-locking-text`, Satz Text 5 EN über `p($l->t(...))`; admin.js unverändert. Text 5 in allen 18 Katalogdateien direkt hinter dem Satz des parallel-Hinweises (de, de_DE, fr wörtlich nach `Freigabe Text 5 45-25`; es, it, nl, pt_BR, pt_PT, zh_TW maschinelle Entwürfe nach den Sprachdokus), Zeile in den sechs Sprachtabellen, Nachtrag in den fünf deutschsprachigen Sprachdokus, Zählung in docs/l10n-chinese.md auf 385. Schlüsselzahl in test_admin_ui_contract.py 384 -> 385 mit Kommentar. Umlaut-Audit der neuen deutschen Prosa (Abschnitt in docs/admin-page.md, Nachträge, Kommentarzeilen): können, führenden, Groß, unabhängig, Laufzeit, fällt, Übersicht, Prüfung mit echten Umlauten, keine Ersatzschreibung, kein Gedankenstrich.

Tests: LockingCheckServiceTest `testDefaultLockingIsShared`, `testSwitchedOffFileLockingIsLeftToTheNextcloudCheck` (ohne und mit APCu), `testApcuAsTheLockingCacheIsUnshared` (mit und ohne Backslash, Kleinschreibung, filelocking.enabled true), `testArrayCacheAsTheLockingCacheIsUnshared`, `testRedisAsTheLockingCacheIsShared` (Redis, Memcached), `testAValueThatIsNoStringIsShared` (Zahl, Liste, null). SettingsControllerTest `testTheOverviewCarriesLockingUnsharedAsFalseOnASharedLockingProvider` und `testTheOverviewCarriesLockingUnsharedAsTrueUnderApcu`; der Helfer `controller(?array $statusAnswer = null, ?IConfig $lockingConfig = null)` baut den Dienst ohne Argument über eine leere Systemkonfiguration, `systemConfig(array $values)` liefert die Attrappe. AdminSettingsTest baut den Dienst über `new LockingCheckService($this->createMock(IConfig::class))`. test_admin_ui_contract `test_an_unshared_locking_provider_has_a_banner_on_the_page` mit dem Prüfer `scan_locking_banner(template, script, catalogues)` und Fehl-Samples (ohne hidden-Bedingung -> ein Befund; zh_TW.js ohne den Satz -> genau `zh_TW.js lacks the sentence`; Skript nennt den Banner -> ein Befund; vor die Schleife über $banners verschoben -> ein Befund).

RED (nicht committet): `bash scripts/dev/phpunit_docker.sh --filter 'LockingCheckServiceTest|SettingsControllerTest|AdminSettingsTest'` -> `Tests: 108, Assertions: 89, Errors: 86.`; alle Fehler `Error: Class "OCA\Findling\Service\LockingCheckService" not found` (die sechs Fälle von LockingCheckServiceTest, jeder Fall von SettingsControllerTest über den Helfer `controller()`, die drei Fälle von AdminSettingsTest, die AdminViewService bauen). `PYTHONUTF8=1 uv run --no-sync python -m pytest -q tests/test_admin_ui_contract.py` -> `2 failed, 227 passed`: `test_an_unshared_locking_provider_has_a_banner_on_the_page` (`'the template carries 0 banners findling-banner-locking'`) und `test_the_german_catalogue_covers_both_german_language_codes` (Schlüsselzahl 385).

GREEN: derselbe PHPUnit-Aufruf -> `OK (108 tests, 935 assertions)`; pytest `tests/test_admin_ui_contract.py tests/test_admin_locale.py tests/test_store_metadata.py` -> `398 passed`. Der erste Lauf des Contract-Tests nach dem Fix war rot am eigenen Fehl-Sample "vor die Schleife verschoben" (der Prüfer verlangte nur Leerraum zwischen beiden Bannern, ein Banner davor ergab einen leeren Abschnitt); die Bedingung prüft jetzt auch die Reihenfolge (`parallel_end <= start < block_end`).

Befund am Rand (INFO, kein Fix): strcasecmp erkennt auch `\oc\memcache\apcu`. Nextcloud lädt Klassen über den Classmap-Autoloader von Composer, dessen Schlüssel Groß- und Kleinschreibung unterscheiden; eine klein geschriebene Klasse löst `class_exists()` in Factory.php nur auf, wenn APCu im Prozess schon geladen ist (typisch, wenn `memcache.local` ebenfalls APCu ist, Factory prüft den lokalen Cache zuerst, Z. 65-67/67-69/68-70). Sonst wird daraus NullCache und damit der DBLockingProvider, und der Hinweis stünde zu Unrecht (abgeleitet aus dem Verhalten des Composer-Autoloaders, nicht auf einer Instanz nachgestellt). Der Plan verlangt strcasecmp ausdrücklich; der Fall ist selten (Schreibfehler in config.php) und der Hinweis dann nur überflüssig, nicht falsch beruhigend.

Baumhash php/ nach Task 1: Rezept und unabhängige Pipeline (find, sort, sed, sha256sum) `8eae94a1...` mit 145 Dateien; Positivkontrolle Rezept und Pipeline über `git archive 504cd787` -> `05797073...` mit 143 (gleich dem bisherigen PHP_TREE_HASH_TODAY).

#### Locking-Hinweis Mutationen

Je einzeln, danach LockingCheckService.php byte-gleich zurück (`restored_identical=yes`, SHA-256 vor und nach gleich); Skripte `<scratchpad>/mutate25.py` und `<scratchpad>/mut25_t1.sh`, je gefiltertes PHPUnit `LockingCheckServiceTest|SettingsControllerTest`.

(M19) APCu-Zweig entfernt (UNSHARED_CLASSES nur noch ArrayCache) -> rot: `testApcuAsTheLockingCacheIsUnshared`, dazu `testTheOverviewCarriesLockingUnsharedAsTrueUnderApcu` (`Failures: 2`)
(M20) `filelocking.enabled` nicht gelesen (`if (false)`) -> rot: `testSwitchedOffFileLockingIsLeftToTheNextcloudCheck` (`Failures: 1`)
(M25) `strcmp` statt `strcasecmp` -> rot: `testApcuAsTheLockingCacheIsUnshared` (`Failures: 1`)
(M26) ArrayCache nicht erkannt (UNSHARED_CLASSES nur noch APCu) -> rot: `testArrayCacheAsTheLockingCacheIsUnshared` (`Failures: 1`)

Gates Task 1 (verify-Zeile wörtlich aus `<scratchpad>/v25_t1.sh`, mit der Zeile im Plan byte-gleich verglichen, seriell, Docker vorher und danach leer) -> `VERIFY_EXIT=0`: PHPUnit voll `OK (1416 tests, 8870 assertions)`, `php_gates_docker.sh all` grün (Psalm-Taint je 0 Befunde gegen v33.0.9, v34.0.6, v35.0.3, Probe 3; php-cs-fixer ohne Verstoß; zizmor und actionlint grün, Probe gesehen), ruff `All checks passed!`, ruff format `260 files already formatted`, pyright latest `0 errors, 0 warnings, 0 informations`, vulture ohne Fund, pytest `tests/test_admin_ui_contract.py tests/test_store_metadata.py tests/test_measurement_scripts.py tests/test_admin_locale.py` `970 passed`.

#### Platzhalter Regelfelder

Nach `Freigabe Platzhalter 45-25` ("Ok", 2026-11-23 02:08 UTC; EN Backups, DE Sicherungen, FR Sauvegardes). Kopf vor dem Task 39b2b436.

I-45-19-01 (INFO, behoben in 45-25 Task 2): Stellen php/templates/admin.php Ordnerfeld `findling-rules-new` (fest `placeholder="Backups"`, am Stand von 39b2b436 Z. 1587) und Musterfeld `findling-rules-patterns-new` (fest `placeholder="*.photoslibrary"`, Z. 1631); Fix: das Ordnerfeld trägt `placeholder="<?php p($l->t('Backups')); ?>"`, der Schlüssel `Backups` steht in allen 18 Katalogdateien direkt hinter "Add exclusion" (de, de_DE Sicherungen, fr Sauvegardes nach der Freigabe; es Copias de seguridad, it Backup, nl Back-ups, pt_BR Backup, pt_PT Cópias de segurança, zh_TW 備份 als maschinelle Entwürfe nach den Sprachdokus), Zeile in den sechs Sprachtabellen, Schlüsselzahl 385 -> 386; das Musterfeld behält `*.photoslibrary`, ein Kommentar im PHP-Block davor sagt `stays untranslated` mit Grund; Prüfung des Musters: es enthält `*` (keine Meldung no_wildcard), hat 15 Zeichen (unter MAX_PATTERN_LENGTH 60), ist dasselbe Beispiel wie `"\u{E001}"` in `$exampleMarkers` (Hilfesatz der Muster) und wie docs/admin-page.md Z. 836 und Z. 892, und es trifft, was die Doku verspricht (ExclusionServiceTest Z. 112-114 Treffer im Bundle, Z. 139 kein Treffer auf `Notizen.photoslibrary.txt`); Test `test_the_example_folder_of_the_rules_comes_from_the_catalogue` mit dem Prüfer `scan_rules_placeholders` und drei Fehl-Samples; Mutationen M27 und M28.

Die beiden Stellen in docs/admin-page.md, die `Backups` nennen (Z. 791 und Z. 839, Mustertabelle `Backups/*`), meinen einen Ordnernamen einer Regel, nicht den Platzhalter des Feldes, und bleiben; die Doku nennt den Platzhalter des Ordnerfelds nirgends und ist nicht geändert. VALUES_THAT_MAY_EQUAL_THEIR_KEY ist nicht nötig: keine Sprache führt den Schlüssel unverändert (it und pt_BR führen "Backup" ohne s). Umlaut-Audit der neuen deutschen Werte und Prosa: Sicherungen ohne Umlaut, die Nachträge in den fünf deutschsprachigen Sprachdokus mit echten Umlauten (übersetzt, Entwürfe), kein Gedankenstrich.

RED (nicht committet): `PYTHONUTF8=1 uv run --no-sync python -m pytest -q tests/test_admin_ui_contract.py -k example_folder_of_the_rules` -> `1 failed, 229 deselected`, wörtlich: `FAILED tests/test_admin_ui_contract.py::test_the_example_folder_of_the_rules_comes_from_the_catalogue` mit `Left contains 2 more items, first extra item: 'rules: the placeholder of the folder field is fixed text and not a wording of the catalogue'`.

GREEN: pytest `tests/test_admin_ui_contract.py tests/test_admin_locale.py tests/test_store_metadata.py` -> `399 passed`.

Baumhash php/ nach Task 2: Rezept und unabhängige Pipeline `d75974c9...` mit 145 Dateien; Positivkontrolle Rezept und Pipeline über `git archive 39b2b436` -> `8eae94a1...` mit 145 (gleich dem Wert nach Task 1).

#### Platzhalter Mutationen

Je einzeln, danach die Datei byte-gleich zurück (`restored_identical=yes`); Skripte `<scratchpad>/mutate25.py` und `<scratchpad>/mut25_t2.sh`, je gefiltertes pytest `-k example_folder_of_the_rules`.

(M27) Ordnerfeld wieder mit festem `placeholder="Backups"` -> rot: `test_the_example_folder_of_the_rules_comes_from_the_catalogue` (`1 failed`)
(M28) Schlüssel `Backups` aus php/l10n/zh_TW.json entfernt -> rot: `test_the_example_folder_of_the_rules_comes_from_the_catalogue` (`1 failed`)

Gates Task 2 (verify-Zeile wörtlich aus `<scratchpad>/v25_t2.sh`, mit der Zeile im Plan byte-gleich verglichen, seriell, Docker vorher und danach leer) -> `VERIFY_EXIT=0`: PHPUnit voll `OK (1416 tests, 8870 assertions)`, `php_gates_docker.sh all` grün (Psalm-Taint je 0 Befunde gegen v33.0.9, v34.0.6, v35.0.3, Probe 3; php-cs-fixer ohne Verstoß; zizmor und actionlint grün), ruff `All checks passed!`, ruff format `260 files already formatted`, pyright latest `0 errors, 0 warnings, 0 informations`, vulture ohne Fund, pytest der vier Dateien `971 passed`. Der erste Lauf fiel an ruff format (zwei Umbrüche im neuen Test); formatiert, dazu ein Kommentar zum Fehl-Sample berichtigt (zwei Befunde, nicht einer), danach der ganze Lauf ein zweites Mal grün.

### RED und GREEN 45-26

Plan 45-26, 2026-11-23, nach `Entscheid I-45-23-07 45-26` ("Wie empfohlen", 2026-11-23 06:08 UTC, m1, eingetragen in 2343885d). Kopf vor dem Plan 71b9cfb6. Docker seriell, vor jedem Start `test -z "$(docker ps -q)"` leer.

#### Migration 1.7

Name: `Version001700Date20261123000000` (UTC-Tag des Commits 2026-11-23, nach Version001603Date20261108000000 sortiert). Migration ohne Klasse der App (Imports nur Closure, OCP\IAppConfig, OCP\Migration\IOutput, OCP\Migration\SimpleMigrationStep), Literale `APP_ID = 'findling'` und `BACKEND_VERSION_KEY = 'backend_app_version'`, postSchemaChange wie Version001600Date20261028000000 mit Wächter für den zweiten Lauf, kein setValue, kein changeSchema, Konstruktor nur IAppConfig. Test php/tests/Unit/Version001700Date20261123000000Test.php mit testTheClassNameIsTheFileName, testARecordedVersionIsDroppedAndNamedInTheOutput, testAnInstanceThatNeverRecordedOneIsLeftAlone, testASecondRunDropsNothingAndThrowsNothing, testTheLiteralsMirrorTheConstantsOfTheApp, testTheMigrationIsHandedTheAppConfigOnly, testTheMigrationHasNoSchemaStep; MigrationSelfContainedTest erfasst die Datei über den DataProvider (nicht in GRANDFATHERED) und nennt sie in testTheDirectoryIsTheOneWithTheMigrations als Positivkontrolle. Keine CHANGELOG-Zeile: gegenüber 1.6.5 ändert sich für Nutzer nichts, die Migration verhindert nur einen Rückschritt.

RED Migration 1.7: Tests: 23, Assertions: 33, Errors: 7, Failures: 1.
(gefiltert `bash scripts/dev/phpunit_docker.sh --filter 'Version001700|MigrationSelfContained'`; die sieben Fälle des neuen Tests mit `Class "OCA\Findling\Migration\Version001700Date20261123000000" not found` bzw. `ReflectionException`, die Positivkontrolle mit `Failed asserting that an array contains 'Version001700Date20261123000000.php'.`)
GREEN Migration 1.7: OK (24 tests, 66 assertions)

Baumhash php/ nach Task 2: Rezept und unabhängige Pipeline `a8d90c20...` mit 147 Dateien; Positivkontrolle Rezept und Pipeline über `git archive 2343885d` -> `d75974c9...` mit 145 (gleich dem bisherigen PHP_TREE_HASH_TODAY).

#### Migration 1.7 Mutationen

Je einzeln, gefiltert wie oben, danach Version001700Date20261123000000.php byte-gleich zurück (`restored_identical=yes`, SHA-256 `7aefa894...` vor und nach gleich); Skripte `<scratchpad>/p26/mutate26.py` und `<scratchpad>/p26/mut.sh`.

(M29) Zeile mit deleteKey entfernt -> rot: `testARecordedVersionIsDroppedAndNamedInTheOutput`, dazu `testASecondRunDropsNothingAndThrowsNothing` (`Failures: 2`)
(M30) `self::BACKEND_VERSION_KEY` im deleteKey-Aufruf durch `\OCA\Findling\Service\ExAppService::KEY_BACKEND_VERSION` ersetzt -> rot: `MigrationSelfContainedTest::testAMigrationNamesNoClassOfTheApp` mit dem Datensatz "Version001700Date20261123000000.php" (`Failures: 1`)
(M31) Wächter entfernt (kein `return` bei '') -> rot: `testASecondRunDropsNothingAndThrowsNothing`, dazu `testAnInstanceThatNeverRecordedOneIsLeftAlone` (`Failures: 2`)

Gates Task 2 (verify-Zeile byte-gleich aus dem Plan nach `<scratchpad>/p26/v2.sh` gezogen, seriell, Docker vorher und danach leer) -> `VERIFY_EXIT=0`: PHPUnit voll `OK (1424 tests, 8895 assertions)`, `php_gates_docker.sh all` grün (Psalm-Taint je 0 Befunde gegen v33, v34, v35; php-cs-fixer ohne Verstoß; zizmor und actionlint grün, Probe gesehen), ruff `All checks passed!`, ruff format `260 files already formatted`, pyright `0 errors, 0 warnings, 0 informations`, vulture still, pytest `tests/test_measurement_scripts.py` `572 passed`.

#### Marke vor 1.5 und Version001500

Vorbedingung: `Entscheid I-45-23-07 45-26: "Wie empfohlen" (2026-11-23 06:08, Claude-Code-Chat) Entscheid: m1` in 45-FREIGABEN.md (2343885d). Kopf vor dem Task d2a218ba.

Schritt 1, Messung vor jeder Änderung an Version001500: `test -z "$(docker ps -q)"` leer, dann `FROM_TAGS=v1.3.2 bash scripts/ci/update_in_process_proof.sh` (Image nextcloud:33-apache dabei neu gezogen, 107 s, Exit 1). Kontrolle: `UPDATE-PROOF failed Error: Undefined constant OCA\Findling\Service\SettingsService::KEY_COVERAGE_PER_DOCUMENT_HINT in Version001603Date20261108000000.php:55`, `control ok: the failure of v1.6.3 is reproduced`. Kandidat: `UPDATE-PROOF installed findling 1.3.2, 51 classes of it loaded, 0 not loadable, 10 migrations applied`, dann:
RED I-45-26-01 v1.3.2: UPDATE-PROOF failed Error: Call to undefined method OCA\Findling\Service\SettingsService::markScanStale() in Version001500Date20261012000000.php:67
I-45-26-01 (MEDIUM, behoben in 45-26 Task 3): Ein Update der Begleit-App aus 1.3.x auf jede Version ab 1.5.0 endet in einem Prozess mit "Call to undefined method OCA\Findling\Service\SettingsService::markScanStale()" in Version001500Date20261012000000.php:67, vorbestehend seit 1.5.0 und wie I-45-23-07 nur auf dem Weg von vor 1.5. Ursache: Version001500 nannte SettingsService (Konstruktor) und rief markScanStale(), das es in 1.3.2 nicht gibt (`git show v1.3.2:php/lib/Service/SettingsService.php | grep -c 'function markScanStale'` ergibt 0); beim Update sind die Klassen der alten Version geladen (Regel aus #51). Schwere MEDIUM: das Update aus dem Store bricht ab, die App bleibt mit halb angewandten Migrationen stehen und braucht einen Eingriff des Admins; es werden keine Daten preisgegeben, und betroffen ist nur der Bestand auf 1.3.x (alle Tags ab v1.0.3 tragen `min-version="33"`, der Sprung ist im Store also möglich). Fix: Version001500 ohne Klasse der App, Literale APP_ID, BACKEND_VERSION_KEY, STALE_KEY, RECOUNTED_AT_KEY, Konstruktor `(IAppConfig, ITimeFactory)`, die Marke wie SettingsService::markScanStale() nur beim Wechsel von 0 auf `max(1, getTime())`, Eintrag aus GRANDFATHERED von MigrationSelfContainedTest entfernt. Test: Version001500Date20261012000000Test (testTheLiteralsMirrorTheConstantsOfTheApp, testTheMigrationAsksTheContainerForNothing mit `[IAppConfig::class, ITimeFactory::class]`), MigrationSelfContainedTest über den DataProvider; M33 und M34 rot; der Nachweis aus v1.3.2 läuft danach durch (GREEN-Zeile unten), und v1.3.2 steht nach Task 4 dauerhaft in FROM_TAGS.
I-45-26-01 Store-Update (#51): #51 belegt, dass SettingsService auch beim echten Store-Update (occ app:update und der Knopf der Apps-Seite) in der Version der installierten App geladen ist, wenn die Migrationen laufen; der Treiber lädt jede Klasse der installierten Version und ist damit strenger als das echte Update, der Befund bleibt trotzdem gültig, zumal Version001500 SettingsService über ihren Konstruktor selbst anforderte und damit die alte Klasse in jedem Fall lud.

Schritt 2, Sicherheit der Änderung an der ausgelieferten Migration (Quellen: nextcloud/server lib/private/DB/MigrationService.php, stable34 aus dem Checkout von phpunit_docker.sh ec467246, stable33 und stable35 am 2026-11-23 über raw.githubusercontent.com geholt; Kopien `<scratchpad>/p26/ms/`):
(a) Nextcloud führt eine Migration je App nur einmal aus: getMigrationsToExecute liest getMigratedVersions (stable33 Z. 254-255, stable34 Z. 249-250, stable35 Z. 254-255), shallBeExecuted verwirft jede schon eingetragene Version (`in_array($m, $knownMigrations)`, stable33 Z. 276-277, stable34 Z. 271-272, stable35 Z. 276-277); markAsExecuted trägt app und version in oc_migrations ein (Z. 287, 282, 287), executeStep tut das erst nach postSchemaChange (Z. 528 und 533, 523 und 528, 518 und 523). Jede Instanz, die Version001500 schon hatte (jede ab 1.5.0), führt die geänderte Datei nie aus; betroffen sind nur Updates von vor 1.5 und frische Installationen.
(b) Frische Installation: Installer.php ruft `$ms->migrate('latest', $previousVersion === '')` (stable34 Z. 547), also nur das Schema, postSchemaChange läuft dort nicht; liefe es, fehlte `scan_recounted_at` ohnehin und das Vergessen wäre ein No-op.
(c) Replay nach einem abgebrochenen Upgrade: die Marke wird nur beim Wechsel von 0 gesetzt, das Löschen eines fehlenden Schlüssels ist ein No-op, schlimmstenfalls eine zusätzliche Runde (testASecondRunDropsNothingAndThrowsNothing).
(d) Regel aus #51: die Datei nennt keine Klasse der App mehr, ihr Eintrag in GRANDFATHERED von MigrationSelfContainedTest ist entfernt (die Liste wurde kürzer); `SettingsService::KEY_SCAN_RECOUNTED_AT` und `markScanStale()` fehlen in 1.3.2.
(e) Vorbild: 1.6.4 hat die ausgelieferte Version001603Date20261108000000 aus demselben Grund auf Literale umgeschrieben.
Kein Grund gegen die Änderung gefunden; die Ausweichlösung in der Migration von 1.7 ist nicht nötig. Der einzige Leser von scanRecountedAt außerhalb von SettingsService, AdminViewService::rulesPendingNow (Z. 2381-2398), liest den Wert nur bei gesetztem `rules_changed_at`, den es vor 1.6 nicht gibt; ein Sprung aus 1.4.x hat ihn nicht.

Schritt 3, Umsetzung (m1): Version001500Date20261012000000.php wie oben, dazu nach der Marke `deleteKey(self::APP_ID, self::RECOUNTED_AT_KEY)` mit der Ausgabe 'forgot when the last recount started, so the recount under the allowlist of 1.5 starts at once'; Docblock: der Satz "ScanRecountJob sees the mark within its interval" ist ersetzt durch die Erklärung des Mindestabstands seit 1.7.0 und des Vergessens (owner decision m1 on I-45-23-07, plan 45-26), dazu ein Absatz zu #51 und I-45-26-01; der Satz "Every minor step needs a migration of this shape, ..." bleibt fett. Test: die bisherigen Fälle in der Aussage gleich, jetzt auf einer kleinen Ablage der App-Konfiguration (Marke gesetzt, bestehende Marke bleibt, Version gelöscht und genannt, nie eine eigene Version, zweiter Lauf ohne Wurf und mit zweimal deleteKey für `scan_recounted_at`), neu testAnUpdateFromBeforeOneFiveRecountsAtOnce (`scan_recounted_at` eine Stunde vor NOW, keine Marke; danach fehlt der Schlüssel, die Marke steht, `scanRecountDue(NOW)` der echten SettingsService ist true, ein zweiter Lauf wirft nicht) und testTheLiteralsMirrorTheConstantsOfTheApp.

RED Marke (gefiltert `bash scripts/dev/phpunit_docker.sh --filter 'Version001500|MigrationSelfContained'`, nicht committet): Tests: 27, Assertions: 50, Errors: 8, Failures: 2. (acht Fälle von Version001500Date20261012000000Test mit Fehlern, darunter `Error: Undefined constant OCA\Findling\Migration\Version001500Date20261012000000::APP_ID`; Failures `MigrationSelfContainedTest::testAMigrationNamesNoClassOfTheApp` mit dem Datensatz "Version001500Date20261012000000.php" und `testTheMigrationAsksTheContainerForNothing`)
GREEN Marke: OK (27 tests, 122 assertions)
GREEN I-45-26-01 v1.3.2: UPDATE-PROOF ok findling 1.3.2 -> 1.7.0, migrations applied in this run: 001400Date20261006000000, 001500Date20261012000000, 001600Date20261028000000, 001603Date20261108000000, 001700Date20261123000000
(derselbe Aufruf `FROM_TAGS=v1.3.2 bash scripts/ci/update_in_process_proof.sh`, Docker vorher leer, Exit 0, 29 s, Kontrolle wieder reproduziert, Schlussmeldung `update proof: control reproduced, every candidate run passed`)
I-45-23-07 umgesetzt: m1, Version001500Date20261012000000 vergisst beim Update von vor 1.5 `scan_recounted_at` nach dem Setzen der Marke, die Runde unter der Allowlist von 1.5 beginnt im nächsten Lauf von ScanRecountJob (binnen 15 Minuten) statt bis zu sechs Stunden später; gehalten von testAnUpdateFromBeforeOneFiveRecountsAtOnce und M32.

Schritt 4, einmalige Marken beim Update 1.7.0 (am Kopf d2a218ba): `git diff v1.6.5..HEAD -- php/lib/Service/StorageService.php` hat keine MIME-Zeile der Allowlist (der Code-Diff ist nur ADMIN_MOUNT_TYPE, excludedStorageIds() und der Filter in getMounts(), der bei leerer Liste `$mounts` unverändert zurückgibt); `git diff --stat v1.6.5..HEAD -- php/lib/Service/ScanStatsService.php` ist leer; der Code-Diff von php/lib/BackgroundJobs/StorageCrawlJob.php ist nur CRAWL_ACTIVE_LOCK (Marker-Lock), isPassingLockError mit Wiederholung und das verschachtelte finally, kein Zähler; SettingsService::excludedExternalMounts liest `getValueArray(..., KEY_EXCLUDED_EXTERNAL_MOUNTS, [])`, ohne Schlüssel also leer; D-45-08 (gespeicherte Einträge mit * oder ? bleiben in Kraft, nur markiert); RECOUNT_MIN_INTERVAL_SECONDS steht im Code nur in der Definition (SettingsService Z. 322) und im Fälligkeitsvergleich von scanRecountDue() (Z. 398); REFUSAL_RENEW_MARK_1_7_0 = "refusal_streaks_1_7_0" in backend/src/findling/store/repo.py Z. 246 (45-18) erneuert die Serien im Container.
Einmalige Marke 1.7.0: keine weitere, Allowlist, Zählweg und Regeln sind gegenüber 1.6.5 unverändert und die Liste ausgeschlossener Admin-Speicher ist nach dem Update leer, also bleibt der Nenner aus 1.6.5 gültig; RECOUNT_MIN_INTERVAL_SECONDS bestimmt nur den Start einer Runde, nicht was sie zählt, und `scan_recounted_at` aus 1.6.5 hat dieselbe Bedeutung; die einmalige Erneuerung der Serien läuft im Container unter refusal_streaks_1_7_0 (45-18).

Baumhash php/ nach Task 3: Rezept und unabhängige Pipeline `8ed19fc8...` mit 147 Dateien; Positivkontrolle Rezept und Pipeline über `git archive d2a218ba` -> `a8d90c20...` mit 147 (gleich dem Wert nach Task 2).

#### Marke Mutationen

Je einzeln, gefiltert wie oben, danach Version001500Date20261012000000.php byte-gleich zurück (`restored_identical=yes`, SHA-256 `8440e6cd...` vor und nach gleich); Skripte `<scratchpad>/p26/mutate26.py`, `<scratchpad>/p26/mutations_extra.json` und `<scratchpad>/p26/mut.sh`.

(M32) das Löschen von `scan_recounted_at` entfernt -> rot: `testAnUpdateFromBeforeOneFiveRecountsAtOnce`, dazu `testASecondRunDropsNothingAndThrowsNothing` (`Failures: 2`)
(M33) `use OCA\Findling\Service\SettingsService;` und der Aufruf `markScanStale()` zurück (an Stelle des Wächters der Marke) -> rot: `MigrationSelfContainedTest::testAMigrationNamesNoClassOfTheApp` mit dem Datensatz "Version001500Date20261012000000.php" (`Failures: 1`)
(M34) der Wächter der Marke entfernt (Marke immer neu gesetzt) -> rot: `testAnExistingMarkIsKept`, dazu `testASecondRunDropsNothingAndThrowsNothing` (`Failures: 2`)

Gates Task 3 (verify-Zeile byte-gleich aus dem Plan nach `<scratchpad>/p26/v3.sh` gezogen, seriell, Docker vorher und danach leer) -> `VERIFY_EXIT=0`: PHPUnit voll `OK (1426 tests, 8947 assertions)`, `php_gates_docker.sh all` grün (Psalm-Taint je 0 Befunde gegen v33, v34, v35; php-cs-fixer ohne Verstoß; zizmor und actionlint grün), ruff `All checks passed!`, ruff format `260 files already formatted`, pyright `0 errors, 0 warnings, 0 informations`, vulture still, pytest `tests/test_measurement_scripts.py` `572 passed`.

#### Update-Probe

Kopf vor dem Task 1189bdc6. Treiber scripts/ci/update_in_process_driver.php: nach dem Laden der Klassen und vor dem Tausch `$recordKey = 'backend_app_version';` (ExAppService::KEY_BACKEND_VERSION als Literal) und `Server::get(IAppConfig::class)->setValueString($appId, $recordKey, $oldVersion);` mit der Ausgabe `UPDATE-PROOF planted <key> <alte Version>`; nach upgradeApp und clearCache verlangt er bei abweichendem Major oder Minor, dass der Wert fehlt, sonst `proofFail("the recorded backend version ... survived the minor step ...")`; die ok-Zeile endet mit `, recorded backend version <alte Version> dropped|kept`. Skript scripts/ci/update_in_process_proof.sh: FROM_TAGS v1.3.2 v1.4.3 v1.5.1 v1.6.2 v1.6.3 v1.6.4 v1.6.5, `CONTROL2_MESSAGE="survived the minor step"`, Kontrolle 2 nach Kontrolle 1 (Kopie von php/ ohne jede Migration, die das Archiv des neuesten Tags nicht trägt; Pfade aus `tar -tzf` ohne führendes `./`, verglichen wird der Dateiname unter `findling/lib/Migration/`; leere Liste = `CONTROL 2 BROKEN`), Schlussmeldung je nach Kontrolle 2. Test backend/tests/test_update_in_process_proof.py mit drei Prüfern über Text und Fehl-Samples (B8): anderer Schlüssel; andere Meldung; FROM_TAGS mit letztem Wort v1.6.4, und FROM_TAGS auf v1.7.0 bei einem CHANGELOG mit `## [Unreleased]`, `## [1.7.0]`, `## [1.6.5]` (dazu ein Gut-Sample, damit die Samples richtig gebaut sind).

RED Update-Probe: 2 failed, 1 passed in 0.21s
(gefiltert `PYTHONUTF8=1 uv run --no-sync python -m pytest -q tests/test_update_in_process_proof.py`, nicht committet: FAILED test_the_driver_plants_the_key_the_service_records mit "the driver sets $recordKey 0 times, not once", FAILED test_the_probe_and_its_control_name_the_same_failure mit "the proof sets CONTROL2_MESSAGE 0 times or empty, not once"; test_the_newest_from_tag_is_the_release_before_the_candidate war schon vor dem Fix grün, weil er einen bestehenden Stand hält: die alte Vorgabe endete schon auf v1.6.5, und seine Fehl-Samples sind im selben Lauf rot geprüft)
GREEN Update-Probe: 3 passed in 0.05s

Lauf: Docker vorher leer, `bash scripts/ci/update_in_process_proof.sh` mit der Vorgabe (Kontrolle 1, Kontrolle 2, sieben Kandidaten, seriell, Image nextcloud:33-apache schon gezogen, Exit 0), Laufzeit mit `date -u +%s`: EXIT=0 START=1795424898 END=1795425035 SECONDS=137, Docker danach leer. Jeder Lauf zeigt `UPDATE-PROOF planted backend_app_version <alte Version>` (9 mal, einmal je Instanz).
Update-Probe Kontrolle 1: control ok: the failure of v1.6.3 is reproduced
Update-Probe Kontrolle 2: control 2 removes: Version001700Date20261123000000.php ; UPDATE-PROOF failed the recorded backend version 1.6.5 survived the minor step 1.6.5 -> 1.7.0, so the search answers no hits until the settings page is opened ; control 2 ok: without the migrations of 1.7.0 the recorded version survives v1.6.5 -> 1.7.0, and the probe sees it
Update-Probe Laufzeit: 3 min
Update-Probe Kandidat v1.3.2: UPDATE-PROOF ok findling 1.3.2 -> 1.7.0, migrations applied in this run: 001400Date20261006000000, 001500Date20261012000000, 001600Date20261028000000, 001603Date20261108000000, 001700Date20261123000000, recorded backend version 1.3.2 dropped
Update-Probe Kandidat v1.4.3: UPDATE-PROOF ok findling 1.4.3 -> 1.7.0, migrations applied in this run: 001500Date20261012000000, 001600Date20261028000000, 001603Date20261108000000, 001700Date20261123000000, recorded backend version 1.4.3 dropped
Update-Probe Kandidat v1.5.1: UPDATE-PROOF ok findling 1.5.1 -> 1.7.0, migrations applied in this run: 001600Date20261028000000, 001603Date20261108000000, 001700Date20261123000000, recorded backend version 1.5.1 dropped
Update-Probe Kandidat v1.6.2: UPDATE-PROOF ok findling 1.6.2 -> 1.7.0, migrations applied in this run: 001603Date20261108000000, 001700Date20261123000000, recorded backend version 1.6.2 dropped
Update-Probe Kandidat v1.6.3: UPDATE-PROOF ok findling 1.6.3 -> 1.7.0, migrations applied in this run: 001700Date20261123000000, recorded backend version 1.6.3 dropped
Update-Probe Kandidat v1.6.4: UPDATE-PROOF ok findling 1.6.4 -> 1.7.0, migrations applied in this run: 001700Date20261123000000, recorded backend version 1.6.4 dropped
Update-Probe Kandidat v1.6.5: UPDATE-PROOF ok findling 1.6.5 -> 1.7.0, migrations applied in this run: 001700Date20261123000000, recorded backend version 1.6.5 dropped
Update-Probe Ergebnis: update proof: both controls reproduced, every candidate run passed

Zeitlimit: 137 s sind aufgerundet 3 Minuten, nicht über 10, also bleibt `timeout-minutes: 15` des Jobs update-in-process; der Kommentar des Jobs beginnt mit `# Measured locally in plan 45-26: 3 minutes`. php.yml: ein Absatz zur Probe und zu Kontrolle 2 mit "survived the minor step", Name des Jobs unverändert. deploy-harp.yml: 506742 Bytes vorher, 507734 nachher (+992, unter 512000): der Satz "1.7.0 adds no migration and no schema change" ist ersetzt (1.7.0 bringt Version001700Date20261123000000, der Start bleibt v1.5.0, weil der Sprung von dort auch Version001600Date20261028000000 ausführt; den Schritt 1.6.5 -> 1.7.0 hält die Probe mit Kontrolle 2), die zwei Kommentare in "Store upgrade 4" nennen beide Migrationen, und "Store upgrade 5" verlangt nach Teil 14 im selben Muster genau eine Zeile `app = 'findling' AND version = '001700Date20261123000000'` in oc_migrations (Teil 14b, `::error::` und `fail=1` sonst).

#### Update-Probe Mutationen

Je einzeln, danach scripts/ci/update_in_process_driver.php byte-gleich zurück (`restored_identical=yes`, SHA-256 `594af25a...` vor und nach gleich, Arbeitskopie mit CRLF wie ausgecheckt); Skript `<scratchpad>/p26/mut_t4.sh`.

(M35) das Pflanzen im Treiber entfernt (Zeile mit setValueString) -> rot: `FROM_TAGS=v1.6.5 bash scripts/ci/update_in_process_proof.sh` endet mit Exit 1 und `CONTROL 2 BROKEN: the candidate without the migrations of 1.7.0 passed the probe, so the probe cannot vouch for the migration of the minor step`, Schlussmeldung `update proof: 1 failure(s)`
(M36) Schlüssel im Treiber `'backend_version'` -> rot: `test_the_driver_plants_the_key_the_service_records` (`1 failed, 2 passed`)

Gates Task 4 (verify-Zeile byte-gleich aus dem Plan nach `<scratchpad>/p26/v4.sh` gezogen, seriell, Docker vorher und danach leer) -> `VERIFY_EXIT=0`: `bash -n` des Skripts grün, `php_gates_docker.sh all` grün (Psalm-Taint je 0 Befunde gegen v33, v34, v35; php-cs-fixer ohne Verstoß; zizmor und actionlint für php.yml und deploy-harp.yml grün), ruff `All checks passed!`, ruff format `261 files already formatted`, pyright `0 errors, 0 warnings, 0 informations`, vulture still, pytest `tests/test_update_in_process_proof.py tests/test_workflow_tag_triggers.py tests/test_phase40_audit.py tests/test_workflow_size.py` `99 passed, 7 skipped` (die sieben übersprungenen Fälle aus test_phase40_audit.py brauchen bash mit FIFO und POSIX-Signalen und laufen im gates-Job von python.yml, unter Windows vorbestehend übersprungen).

#### Locking-Klasse (I-45-25-01)

Kopf vor dem Task c3eaff7f. Quellen: dieselben Abzüge wie unter `#### Locking-Hinweis` (`<scratchpad>/src23/nc-stable33/`, `nc-stable34/`, `nc-stable35/`, je `lib/private/Memcache/`), am 2026-11-23 erneut gelesen; alle Zeilennummern des Plans bestätigt.

Schritt 1, Prämisse gemessen vor jeder Änderung: `<scratchpad>/autoload_probe.php` (Datei, kein `php -r`) lädt nur `lib/base.php` des Server-Checkouts von scripts/dev/phpunit_docker.sh (`${HOME}/.cache/findling-phpunit/server`, Zweig stable34 gleich SERVER_VERSION aus php.yml, `config/config.php` ohne `memcache`-Eintrag, `PHPUNIT_RUN` nicht definiert), Lauf mit `<scratchpad>/p26/run_autoload_probe.sh` im Image nextcloud:32.0.15-apache mit `--entrypoint php`, Checkout unter `/srv/server`, Scratchpad schreibgeschützt eingehängt, Docker vorher und danach leer.
Autoloader-Probe: stable34, lower_before=false exact=true lower_after=true
Die Ausgabe gleicht der Erwartung: ein klein geschriebener Name findet die Klasse vor dem ersten Laden nicht (der Befund), der richtig geschriebene findet sie (Positivkontrolle), danach findet auch der klein geschriebene die geladene Klasse.

Regel Locking-Klasse: unshared() ist genau dann true, wenn (a) `getSystemValueBool('filelocking.enabled', true)` true ist, (b) `memcache.locking` ein String `$raw` ist, dessen `ltrim($raw, '\\')` per `strcasecmp(...) === 0` gleich `OC\Memcache\APCu` oder `OC\Memcache\ArrayCache` ist, und (c) erst dann, nur für einen solchen Namen, `class_exists($raw)` im Prozess der Admin-Seite true ist, mit dem unveränderten Wert aus config.php, wie Factory.php ihn prüft (class_exists auf dem rohen Wert stable33 Z. 98, stable34 Z. 100, stable35 Z. 101; ltrim erst danach Z. 106, 108, 109); nicht übernommen ist `is_a($lockingCacheClass, IMemcache::class, true)` (Z. 99, 101, 102), weil beide Namen in allen drei Zweigen `implements IMemcache` tragen (APCu.php Z. 13, 14, 15; ArrayCache.php Z. 12, 12, 13) und die Prüfung die Antwort nicht ändern kann; nicht übernommen ist `isAvailable()` (Z. 100, 102, 103), weil sie eine statische Methode der privaten Klassen ist und für den fragenden Prozess antwortet, also FPM und nicht das CLI: APCu::isAvailable (stable33 Z. 111-116, stable34 Z. 122-127, stable35 Z. 123-128) ist im CLI ohne `apc.enable_cli` false, das CLI sperrt dann über NullCache in der Datenbank und FPM in APCu, die Sperren sind getrennt und der Hinweis ist richtig, dieser Fall bleibt unshared; ArrayCache::isAvailable ist immer true (Z. 139-140, 149-150, 150-151). Grenzen: ist APCu im Webserver selbst nicht verfügbar, bleibt der Hinweis stehen (schlimmstenfalls überflüssig, nie falsch beruhigend); lädt erst später in derselben Anfrage etwas die Klasse, fände ein klein geschriebener Name sie hier, im Konstruktor der Factory aber nicht (abgeleitet, nicht gemessen, selten); die bisherige Grenze (Klasse nur in einer SAPI, NullCache) bleibt.

Umsetzung: php/lib/Service/LockingCheckService.php mit dem Konstruktor `(private IConfig $config, private ?\Closure $classExists = null,)` (Naht im Stil von `$smbclientProbe`, Produktion übergibt nichts), in unshared() `$raw` gelesen, nach `ltrim` der Vergleich per strcasecmp und erst im Treffer `return (bool)$classExists($raw);` mit `$classExists = $this->classExists ?? static fn (string $class): bool => class_exists($class);`; kein isAvailable, kein is_a, kein `use OC\...`, kein Log, kein Wurf; der Absatz zu strcasecmp im Docblock ist durch die Regel mit Quellen und der Kennung I-45-25-01 ersetzt, der Absatz der Grenzen um die zwei neuen ergänzt. Tests: Helfer `service(array $values, ?\Closure $classExists = null)` gibt immer eine Attrappe mit (Standard: Classmap von Composer vor dem ersten Laden, `in_array(ltrim($class, '\\'), LockingCheckService::UNSHARED_CLASSES, true)`), neu testALowercaseNameThatNoAutoloaderResolvesIsShared, testALowercaseNameOfALoadedClassIsUnshared, testTheClassCheckSeesTheValueAsConfigPhpHoldsIt, testTheClassCheckIsOnlyAskedForAnUnsharedName; die Zeile mit `'\oc\memcache\apcu'` ist aus testApcuAsTheLockingCacheIsUnshared gewandert. SettingsControllerTest und AdminSettingsTest bleiben unverändert (ein Argument, also das echte class_exists im Server-Checkout; testTheOverviewCarriesLockingUnsharedAsTrueUnderApcu ist damit die Positivkontrolle der Vorgabe). docs/admin-page.md: die Klammer "unabhängig von Groß- und Kleinschreibung" ist ersetzt durch die Bedingung über das Laden der Klasse, der Punkt "Grenze" nennt APCu, das im Webserver nicht verfügbar ist.

RED Locking-Klasse: Tests: 112, Assertions: 948, Failures: 3.
(gefiltert `bash scripts/dev/phpunit_docker.sh --filter 'LockingCheckServiceTest|SettingsControllerTest|AdminSettingsTest'`, nicht committet: testALowercaseNameThatNoAutoloaderResolvesIsShared `Failed asserting that true is false.`, testTheClassCheckSeesTheValueAsConfigPhpHoldsIt `Failed asserting that two arrays are identical.`, testTheClassCheckIsOnlyAskedForAnUnsharedName `Failed asserting that actual size 0 matches expected size 1.`; testALowercaseNameOfALoadedClassIsUnshared war vor dem Fix grün, weil der alte Vergleich jeden klein geschriebenen Namen erkannte, und hält M40)
GREEN Locking-Klasse: OK (112 tests, 949 assertions)

I-45-25-01 (INFO, behoben in 45-26 Task 5): Befund aus 45-25 (Absatz "Befund am Rand (INFO, kein Fix)" unter `#### Locking-Hinweis`, als Stand von 45-25 stehen gelassen): LockingCheckService::unshared() erkannte per strcasecmp auch einen klein geschriebenen Namen wie `\oc\memcache\apcu`, den kein Autoloader auflöst; Nextcloud nimmt dann in lib/private/Memcache/Factory.php NullCache und den DBLockingProvider, die Sperren sind geteilt, und der Hinweis stand zu Unrecht. Fix: nach dem Namensvergleich `class_exists` auf dem rohen Wert aus config.php wie Factory.php, über die Naht `?\Closure $classExists`; Tests die vier neuen Fälle von LockingCheckServiceTest, gemessen mit der Autoloader-Probe; Mutationen M37 bis M40 rot. Bezug zum Register wie in 45-25 unter T-45-81, keine neue ID.

45-10 und 45-20 bleiben unverändert: P-LCK in 45-10 Task 1 stellt `--value='\OC\Memcache\APCu'` und `--value='\OC\Memcache\ArrayCache'` richtig geschrieben ein, die Klassen existieren auf jeder Instanz, die Erwartung "sichtbar" gilt weiter, ebenso "unsichtbar" unter dem Standard und unter `filelocking.enabled` false; 45-20 stellt für die Live-Proben von APCu weg auf Redis oder die Datenbank und berührt den Hinweis nicht.

Baumhash php/ nach Task 5: Rezept und unabhängige Pipeline `5837bf28...` mit 147 Dateien; Positivkontrolle Rezept und Pipeline über `git archive c3eaff7f` -> `8ed19fc8...` mit 147 (gleich dem Wert nach Task 3).

#### Locking-Klasse Mutationen

Je einzeln, gefiltert wie oben, danach LockingCheckService.php byte-gleich zurück (`restored_identical=yes`, SHA-256 `0e327782...` vor und nach gleich); Skripte `<scratchpad>/p26/mutate26.py`, `<scratchpad>/p26/mutations_extra.json` und `<scratchpad>/p26/mut.sh`.

(M37) der Aufruf entfernt (`return true;` statt `return (bool)$classExists($raw);`) -> rot: `testALowercaseNameThatNoAutoloaderResolvesIsShared`, dazu testTheClassCheckSeesTheValueAsConfigPhpHoldsIt und testTheClassCheckIsOnlyAskedForAnUnsharedName (`Failures: 3`)
(M38) `$classExists($class)` statt `$classExists($raw)` -> rot: `testTheClassCheckSeesTheValueAsConfigPhpHoldsIt` (`Failures: 1`)
(M39) die Klassenprüfung vor den Namensvergleich gezogen (`if (!$classExists($raw)) { return false; }` direkt nach der is_string-Prüfung, im Treffer `return true;`) -> rot: `testTheClassCheckIsOnlyAskedForAnUnsharedName` (`Failures: 1`)
(M40) `strcmp` statt `strcasecmp` -> rot: `testALowercaseNameOfALoadedClassIsUnshared` (`Failures: 1`)

Nachtrag Task 5: der erste Lauf der verify-Zeile endete mit `VERIFY_EXIT=1` an der Prüfung `new LockingCheckService($config, ` (der Helfer rief den Konstruktor über mehrere Zeilen); der Helfer ruft ihn jetzt in einer Zeile, sonst gleich. GREEN danach erneut `OK (112 tests, 949 assertions)`, M37 bis M40 erneut je rot mit denselben Testnamen, Baumhash neu `5837bf28...` (147 Dateien, Positivkontrolle `git archive c3eaff7f` -> `8ed19fc8...`).

Gates Task 5 (verify-Zeile byte-gleich aus dem Plan nach `<scratchpad>/p26/v5.sh` gezogen, zweiter voller Lauf nach dem Nachtrag oben, seriell, Docker vorher und danach leer) -> `VERIFY_EXIT=0`: PHPUnit voll `OK (1430 tests, 8961 assertions)`, `php_gates_docker.sh all` grün (Psalm-Taint je 0 Befunde gegen v33, v34, v35; php-cs-fixer ohne Verstoß; zizmor und actionlint grün), ruff `All checks passed!`, ruff format `261 files already formatted`, pyright `0 errors, 0 warnings, 0 informations`, vulture still, pytest `tests/test_measurement_scripts.py tests/test_admin_ui_contract.py tests/test_phase33_audit.py tests/test_phase34_audit.py` `852 passed, 107 skipped`.

### RED und GREEN 45-27

Plan 45-27, 2026-11-24, nach `Freigabe Text F3 45-27` ("Ok", 2026-11-24 16:30 UTC, eingetragen in b755694e). Kopf vor dem Plan 8ffb1409. Docker seriell, vor jedem Start `test -z "$(docker ps -q)"` leer.

#### F3 Zählfix

Umsetzung: QueueMapper::requeueAs liest die Dirty-Menge des Bands als erste Anweisung im `$switchable !== []`-Zweig (`$dirtyBefore`), vor beiden Update-Statements und bewusst im Zweig (ein Band ohne umschaltbare Zeilen zahlt kein überflüssiges SELECT); die Rückgabezeile subtrahiert `array_intersect($switchable, $dirtyBefore)`. Beide Update-Statements byte-gleich, git diff zeigt in requeueAs nur Lesung, Rückgabezeile und Kommentare. Docblöcke nachgezogen: der Zählabsatz in requeueAs und der Docblock von dirtyFileIds sagen, dass die Menge VOR den Statements gelesen wird, warum (das $stale-Update löscht genau die Marke, nach der die Abfrage fragt; die Antwort war im Dirty-Fall immer leer und zählte jede zurückgegebene Zeile als Wechsel, #25 F3), dass die Statements über den Effekt weiter selbst entscheiden und dass ein Schreibzugriff zwischen Lesung und Updates die Antwort höchstens um eins ungenau macht.

Tests (php/tests/Unit/QueueMapperTest.php, neu, Array-simulierte Datenbank nach dem Muster von FileStateServiceCoverageTest, um Updates erweitert: set/executeStatement wenden kind, retries, locked_at und dirty auf die Array-Tabelle an, eq/neq/in als Bedingungstoken mit per createNamedParameter gefangenen Werten, executeQuery beantwortet die zwei Selects aus dem AKTUELLEN Array-Zustand, insertIgnoreConflict legt fehlende Zeilen an): `testTheAnswerCountsNoRowThatWasOnlyHandedBack`, `testADeleteRowIsNeitherMovedNorCounted`, `testAMissingRowIsCreatedWithTheKindAndCounted`.

RED (nicht committet), `bash scripts/dev/phpunit_docker.sh --filter QueueMapperTest` vor jeder Änderung an QueueMapper.php: `Tests: 3, Assertions: 9, Failures: 1.`, rot genau der Hauptfall `testTheAnswerCountsNoRowThatWasOnlyHandedBack` mit `Failed asserting that 2 is identical to 1.` (die Antwort zählte die zurückgegebene Dirty-Zeile als Wechsel); die zwei Nebenfälle grün als Wächter des bestehenden Verhaltens (delete-Zeile unberührt, fehlende Zeile angelegt und gezählt).

GREEN gefiltert: derselbe Aufruf -> `OK (3 tests, 15 assertions)`.

Baumhash php/ nach Task 2: Rezept und unabhängige Pipeline (find, sort, sed, sha256sum) `94720fd6...` mit 148 Dateien (QueueMapperTest.php neu); Positivkontrolle Rezept und Pipeline über `git archive b755694e` -> `86f595c7...` mit 147 (gleich dem bisherigen PHP_TREE_HASH_TODAY). backend/src/findling in diesem Task unverändert.

#### F3 Zählfix Mutationen

Je einzeln, gefiltert `bash scripts/dev/phpunit_docker.sh --filter QueueMapperTest`, danach QueueMapper.php byte-gleich zurück (`restored_identical=yes`, SHA-256 `eaa7754a...` vor und nach gleich, Kopie `<scratchpad>/QueueMapper.green.php`).

(M50) Lesung der Dirty-Menge hinter die beiden Updates geschoben -> rot `testTheAnswerCountsNoRowThatWasOnlyHandedBack` (`Failed asserting that 2 is identical to 1.`, `Failures: 1`)
(M51) Subtraktion entfernt, Antwort `count($switchable)` -> rot `testTheAnswerCountsNoRowThatWasOnlyHandedBack` (`Failed asserting that 2 is identical to 1.`, `Failures: 1`)

Gates Task 2 (seriell im Vordergrund; die Session wurde am 24.11. vom Usage-Limit unterbrochen, der schon gestartete PHP-Gate-Lauf lief zu Ende, der Baum blieb dabei unverändert, am 25.11. per SHA-256-Gegenprobe und erneutem gefilterten GREEN-Lauf `OK (3 tests, 15 assertions)` bestätigt): PHPUnit voll `OK (1451 tests, 9087 assertions)`; `php_gates_docker.sh all` grün (das Skript läuft unter `set -euo pipefail` und der Workflow-Gate ist sein letzter Schritt, die Schlusszeile `php_gates_docker: workflow gate green (zizmor, actionlint)` mit `No findings to report.` und `actionlint: no finding` belegt damit auch Psalm-Taint und php-cs-fixer davor); ruff `All checks passed!`, ruff format `261 files already formatted`, pyright latest `0 errors, 0 warnings, 0 informations`, vulture ohne Fund, pytest `tests/test_measurement_scripts.py` `572 passed`.

#### F3 Logzeile und Backstop

Umsetzung (worker/poller.py): (a) Logzeile als zwei Literale `"pass finished, claimed=%d indexed=%d skipped=%d failed=%d unchanged=%d "` und `"handed_ocr=%d handed_embed=%d requeued=%d embedded=%d committed=%d slots=%d throttled=%d"`; handed_ocr=len(handover), handed_embed=len(embedding); skipped zählt nur noch Verdikte skipped, deren file_id nicht in der OCR-Übergabe der Runde steht (Set über handover); RoundResult trägt `handed_ocr: int = 0` und `handed_embed: int = 0` mit Kommentar, skipped und requeued mit nachgezogenen Kommentaren. (b) Backstop: `OCR_HANDOVER_LIMIT: Final = 3` (Kommentar: Analogie zur Give-up-Regel, zählt VERLANGTE Übergaben, zwei identische sind als verlorene Antwort plus Wiederholung legitim, die dritte wird verweigert); `BACKSTOP_LINE: Final` trägt den freigegebenen Wortlaut als ein Literal; `self._ocr_handovers: dict[int, tuple[str, int]]` je Prozess (Docstring: Eintrag nur bei moved.ok in Schritt 3b, OCR-Urteil räumt, Neustart leert als bewusste Grenze, proportional zu den Dateien zwischen den Spuren); pass-lokales `self._handover_hashes` (in _work geleert wie der übrige Rundenzustand). Am Übergabeentscheid des Inhaltszweigs prüft `_third_handover_demanded(file_id, read.content_hash)`: Eintrag mit gleichem Hash und Anzahl >= OCR_HANDOVER_LIMIT - 1 -> keine Übergabe, Outcome wird `ExtractionOutcome.failed(Reason.REPEATEDLY_STUCK)` (läuft durch _collect in die failures der Quittung), genau eine warning-Zeile im freigegebenen Wortlaut mit (Anzahl + 1, file_id), Eintrag geräumt; sonst merkt sich der Pass den Hash. Schritt 3b schreibt den Zähler NUR für die OCR-Liste und NUR bei moved.ok fort (`_count_ocr_handovers`: gleicher Hash Anzahl + 1, anderer Hash neu bei 1). `_judge_scan` räumt den Eintrag bei jedem echten OCR-Urteil (ocr_used=True-Pfad). Kein Dateiname und kein Pfad in einer neuen Zeile (B6, T-02-56).

Tests (tests/test_poller.py, Abschnitt "the backstop against a circling file"): `test_the_pass_line_counts_the_handovers_apart_from_the_final_skips`, `test_two_handovers_of_the_same_bytes_still_hand_over`, `test_a_third_handover_of_the_same_bytes_ends_as_repeatedly_stuck`, `test_changed_bytes_reset_the_handover_count`, `test_a_failed_requeue_does_not_count_towards_the_backstop`, `test_an_ocr_pass_clears_the_backstop_entry`, `test_the_backstop_counts_per_file_and_never_logs_a_name`. Die bestehenden endswith-Tests (`slots=2 throttled=0`, `slots=3 throttled=1`) blieben byte-gleich bestehen und grün.

RED (nicht committet), `PYTHONUTF8=1 uv run --no-sync python -m pytest -q tests/test_poller.py` vor jeder Änderung an poller.py: `6 failed, 264 passed, 1 skipped in 20.91s`, rot genau die sechs neuen Fälle (test_the_pass_line_counts_the_handovers_apart_from_the_final_skips an der alten Zeile ohne handed_ocr; test_a_third_handover_of_the_same_bytes_ends_as_repeatedly_stuck, test_changed_bytes_reset_the_handover_count, test_a_failed_requeue_does_not_count_towards_the_backstop, test_an_ocr_pass_clears_the_backstop_entry an `AttributeError: 'Poller' object has no attribute '_ocr_handovers'` bzw. fehlendem Backstop; test_the_backstop_counts_per_file_and_never_logs_a_name ohne warning-Zeilen). `test_two_handovers_of_the_same_bytes_still_hand_over` war vor dem Fix schon grün und ist der Wächter des bestehenden Verhaltens (zwei Übergaben sind heute legitim); sein Zweig belegt M52.

GREEN: die sieben neuen Fälle gefiltert `6 passed` (plus der Wächter) und die ganze Datei `270 passed, 1 skipped in 19.14s`.

Umgestellt: keine
Begründung: alle acht bestehenden `result.skipped`-Erwartungen (Z. 528, 546, 596, 808, 1083, 1140, 4366, 5860 am Stand vor diesem Task) sind endgültige Skips ohne Übergabe in derselben Runde (mime_not_allowed, gone, OCR aus, empty_text, image_not_ocrable, Sidecar); ihre Zahlen bleiben unter der neuen Semantik unverändert, kein Test musste umgestellt werden.

Weitere Tests: tests/test_embedding_track.py tests/test_main_lifespan.py tests/test_measurement_scripts.py tests/test_phase43_audit_roots.py tests/test_poller.py tests/test_rates_endpoint.py

Konsumenten der Logzeile, lesend geprüft: resilience.yml Z. 399 und 500 greifen `armed='pass finished|armed and the work stock is empty'` (Präfix) und deploy-harp.yml Z. 7910-7913 zählt Zeilen über `grep -c 'pass finished, claimed='`; Präfix und Zeilenanfang stehen byte-gleich, beide bleiben gültig. Konsumenten des BESTANDS, lesend geprüft: deploy-harp.yml Z. ~4054 (Kandidatenliste des Upgrade-Beweises druckt `state == "failed" and reason == "repeatedly_stuck"`-Zeilen des alten Bestands) und Z. ~5576 (written_off-Abfrage über oc_findling_file_state erwartet nur Seed-IDs) parsen den Store und nicht die Logzeile und bleiben in diesem Plan unverändert; ein ECHTER Backstop-Bestand auf einer CI- oder Live-Instanz kann dort als unerwarteter Kandidat auftauchen, der Hinweis an 45-10 steht in der SUMMARY. docs/measurements/ unangetastet.

Baumhash backend/src/findling nach Task 3: Rezept und unabhängige Pipeline (find, sort, sed, sha256sum) `961cd6ae...` mit 83 Dateien; Positivkontrolle Rezept und Pipeline über `git archive b5665f27` -> `8c87b872...` mit 83 (gleich dem bisherigen PACKAGE_TREE_HASH_TODAY). Keine neue Datei unter src/findling, die Dateizahl bleibt 83.

#### F3 Backstop Mutationen

Je einzeln, gefiltertes pytest `tests/test_poller.py -k <Testname>`, danach poller.py byte-gleich zurück (`restored_identical=yes`, SHA-256 `441e77da...` vor und nach jeder Mutation gleich, Kopie `<scratchpad>/poller.green.py`).

(M52) Schwelle 2 statt 3 (`OCR_HANDOVER_LIMIT: Final = 2`) -> rot `test_two_handovers_of_the_same_bytes_still_hand_over` (`1 failed`)
(M53) Hash nicht verglichen, jede Übergabe zählt (Hash-Vergleich in `_third_handover_demanded` und `_count_ocr_handovers` entfernt) -> rot `test_changed_bytes_reset_the_handover_count` (`1 failed`)
(M54) Zähler vor moved.ok erhöht (Zählung aus dem ok-Zweig von Schritt 3b gezogen) -> rot `test_a_failed_requeue_does_not_count_towards_the_backstop` (`1 failed`)
(M55) skipped zählt Übergaben weiter mit (Ausschluss über das handover-Set entfernt) -> rot `test_the_pass_line_counts_the_handovers_apart_from_the_final_skips` (`1 failed`)
(M56) Eintrag nach dem OCR-Urteil nicht geräumt (pop in _judge_scan entfernt) -> rot `test_an_ocr_pass_clears_the_backstop_entry` (`1 failed`)
(M57) Backstop schreibt ab UND übergibt trotzdem (`hand_over = False` entfernt) -> rot `test_a_third_handover_of_the_same_bytes_ends_as_repeatedly_stuck` (`1 failed`)

Gates Task 3 (seriell im Vordergrund, pytest in zwei Teilen): ruff `All checks passed!` (der erste Lauf fiel an ISC004 im Erwartungsliteral des dritten Tests, das Literal steht jetzt in einer Klammer-Variablen, Verhalten gleich), ruff format `261 files already formatted`, pyright latest `0 errors, 0 warnings, 0 informations`, vulture ohne Fund; pytest `tests/test_poller.py tests/test_measurement_scripts.py` `842 passed, 1 skipped`, pytest `tests/test_embedding_track.py tests/test_main_lifespan.py tests/test_phase43_audit_roots.py tests/test_rates_endpoint.py` `178 passed` (zusammen die ganze `Weitere Tests:`-Liste).

#### F3 Deckungsgrad

Umsetzung: repo.py `_COVERAGE_JUDGED` schließt zusätzlich `AND NOT (f.state = 'failed' AND COALESCE(f.reason, '') = 'repeatedly_stuck')` aus; der Docblock bekam nach dem unreadable-Absatz einen Absatz gleicher Bauart (seit 1.7.0, #25, Backstop; die PHP-Seite zählt über PHP_ONLY_NOT_READABLE in phpOnly und notReadable, "Counted here too, it would stand twice in the denominator" gilt wörtlich, Präzedenz D-43-16). scripts/ci/coverage_truth.sh zieht denselben Ausschluss in judged_rows nach (`AND NOT (sf.state = 'failed' AND sf.reason = 'repeatedly_stuck')`) und der Kommentarblock sagt, dass der Container das Paar seit 1.7.0 selbst schreibt, die Quittung es auf die PHP-Seite trägt und judged es deshalb auslässt (einmal gezählt, über php_only); "A 1.6.2 container never writes that pair" steht als historische Aussage mit dem 1.6.3/1.7.0-Zusatz. Nur Kommentare, Code byte-gleich (W1): reconcile.py-Kommentarblock an GIVEN_UP_REASON (der Backstop schreibt das Verdikt jetzt auch selbst; die Zeile ruht über den etag-Vergleich, DI-05-23 matcht nicht, weil das Paar dort skipped(no_text_layer) verlangt), FileStateService.php-Docblock an PHP_ONLY_NOT_READABLE, about-Zeilen des Fixtures. Fixture coverage_topology.json: neue CONTAINER-Zeile file_id 1214 (storage 12, doc_key x/st1.txt, failed/repeatedly_stuck, note nennt Backstop und #25) NEBEN der bestehenden PHP-Zeile derselben Datei; Ableitungstexte (judgedByGroup, phpOnly.derivation, denominatorParts.derivation) um den Fall ergänzt, alle ZAHLEN unverändert.

Tests: test_coverage_counts.py `test_a_container_row_repeatedly_stuck_counts_once_in_the_denominator` (prüft judged gegen die Fixture-Zahlen und baut den Nenner max(PHP-Teil, judged + phpOnly) je Gruppe und Einzelspeicher aus den LIVE-judged-Zahlen gegen denominatorParts und denominator 30). test_coverage_endpoint.py hielt zwei eigene Handzählungen der lebenden Fixture-Zeilen und wurde bewusst nachgezogen, nicht abgeschwächt: `_living(data) == 29` -> `30` und `everything == 32` -> `33` (die neue Zeile 1214 lebt und zählt in docKeysMissing-Kontrollen mit). php/tests/Unit/CoverageTopologyParityTest.php hält KEINE eigenen Erwartungszahlen (er liest die expected-Blöcke des Fixtures, die unverändert sind, und sieht die rows-Liste nicht) und blieb unangetastet.

RED (nicht committet), `PYTHONUTF8=1 uv run --no-sync python -m pytest -q tests/test_coverage_counts.py tests/test_coverage_endpoint.py` nach Fixture und neuem Fall, vor der Änderung an repo.py: `8 failed, 82 passed in 4.46s`; der neue Fall rot mit `assert 19 == 18` (judged zählte die Container-Zeile, der Container-Term gewänne mit der Luftzahl), dazu rot die sieben Fixture-Konsumenten `test_the_fixture_matches_the_hand_derived_truth`, `test_rows_without_a_key_in_a_group_are_named_and_never_guessed`, `test_one_share_under_two_roots_and_two_spellings_counts_every_file_once`, `test_the_topology_gives_the_hand_derived_numbers_through_the_route`, `test_above_the_ceiling_the_count_runs_in_the_background`, `test_coverage_counts_nothing_while_the_mark_is_generation_one`, `test_coverage_counts_nothing_during_a_backup_pause_before_the_reset` (dieselbe Luftzahl bzw. die zwei Handzählungen).

GREEN gefiltert: derselbe Aufruf -> `90 passed in 4.17s`.

scripts/ci/coverage_e2e.sh lesend geprüft: es rechnet judged nicht selbst nach (kein eigener judged-Ausdruck, keine Reason-Listen; das Fixture wird nur für die Form der Schlüssel-Herleitung zitiert), nichts nachzuziehen.

Baumhashes nach Task 4: backend/src/findling Rezept und Pipeline `d031ba6c...` mit 83 (repo.py und reconcile.py geändert, keine Datei kam oder ging), Positivkontrolle über `git archive 2a7befdc` -> `961cd6ae...` mit 83 (gleich dem Wert nach Task 3); php/ Rezept und Pipeline `d5834a55...` mit 148 (FileStateService.php nur Kommentar), Positivkontrolle über `git archive 2a7befdc` -> `94720fd6...` mit 148 (gleich dem Wert nach Task 2).

#### F3 Deckungsgrad Mutationen

Einzeln, gefiltertes pytest `tests/test_coverage_counts.py -k test_a_container_row_repeatedly_stuck_counts_once_in_the_denominator`, danach repo.py byte-gleich zurück (`restored_identical=yes`, SHA-256 `9d5199c2...` vor und nach gleich, Kopie `<scratchpad>/repo.green.py`).

(M58) der neue Ausschluss in _COVERAGE_JUDGED wieder entfernt -> rot `test_a_container_row_repeatedly_stuck_counts_once_in_the_denominator` (`assert 19 == 18`, `1 failed`)

Gates Task 4 (seriell im Vordergrund bzw. als einziger Lauf, Docker vorher und danach leer): ruff `All checks passed!`, ruff format `261 files already formatted`, pyright latest `0 errors, 0 warnings, 0 informations`, vulture ohne Fund; pytest `tests/test_coverage_counts.py tests/test_coverage_endpoint.py tests/test_store_repo.py` `231 passed`, pytest `tests/test_reconcile.py tests/test_measurement_scripts.py` `693 passed`; PHPUnit voll `OK (1451 tests, 9087 assertions)`; `php_gates_docker.sh all` `EXIT=0`: Psalm-Taint je `No errors found!`, `taint findings: 0`, Probe 3 gegen v33.0.9, v34.0.6, v35.0.3; php-cs-fixer `Found 0 of 145 files that can be fixed`, Probe gesehen; zizmor `No findings to report.`, actionlint `no finding`, je Probe gesehen.

#### F3 Doku und CHANGELOG

CHANGELOG [1.7.0]: Text F3 wörtlich nach dem Entwurf in 45-27-PLAN.md (unter `Freigabe Text F3 45-27` steht keine Wortlautzeile, das "Ok" setzte die Entwürfe in Kraft) unter "### Fixed", "### Behoben" und "### Corrigé", direkt hinter den beiden #25-Zeilen aus 45-23 und 45-24, Umbruch mit zwei Leerzeichen Einzug wie die Nachbarn, kein close/fix/resolve-Wort vor #25. docs/ocr.md: neuer Abschnitt `## Backstop gegen kreisende Übergaben (#25, 1.7.0)` (Schwelle, Hash-Kriterium, nur erfolgreiche Übergaben, OCR-Urteil räumt, Neustart als bewusste Grenze, warning-Zeile wörtlich mit `<id>` statt einer Zahl, Ende als failed(repeatedly_stuck) auf der Verwaltungsseite, Nenner genau einmal, Wiedereinstieg über D-31-02, geschärfte Logzeile mit handed_ocr/handed_embed). docs/reconcile.md: Absatz an der vierten Grenze, dass failed(repeatedly_stuck) seit 1.7.0 nicht mehr nur auf der Nextcloud-Seite entsteht. Per grep geprüft und wahr geblieben, deshalb nicht angefasst: docs/reconcile.md die DI-05-23-Tabellen und der Nachholzyklus, docs/formats.md Z. 86, 87 und 131 (Nachholweg und POL-02, keine "nur Nextcloud"-Aussage), docs/performance.md (historische Messprotokolle). docs/measurements/ nicht angefasst. Umlaut-Audit der neuen deutschen Prosa (CHANGELOG.de.md, docs/ocr.md, docs/reconcile.md): echte Umlaute (Übergaben, Durchläufe, unveränderten, geführt, zählt, räumt, Bytes ändern), keine Ersatzschreibung, keine Gedankenstriche, keine Emojis.

Gates Task 5 (verify-Zeile aus dem Plan nach `<scratchpad>/v27_t5.sh`, seriell, ohne Docker) -> `EXIT=0`: Text F3 EN/DE/FR wörtlich gefunden, dritte #25-Zeile je Sprache, keine Gedankenstriche; pytest `tests/test_changelog_translations.py tests/test_store_metadata.py tests/test_measurement_scripts.py` `736 passed`. Zusätzlich die Tests, die CHANGELOG, docs/ocr.md oder docs/reconcile.md lesen: `tests/test_config.py tests/test_corpus_terms.py tests/test_migration_path.py tests/test_phase34_audit.py tests/test_phase36_audit.py tests/test_update_in_process_proof.py` `313 passed, 12 skipped`, `tests/test_ocr.py tests/test_ocr_french.py tests/test_extract_documents.py` `226 passed, 8 skipped`; ruff `All checks passed!`, ruff format `261 files already formatted`.

### Offene Folge-Punkte 45-27

- I-45-27-01 (H1, Ursache des Kreisens, offen): php/lib/Db/QueueMapper.php:659-667, das `$stale`-Update im Dirty-Zweig von requeueAs lässt kind content stehen und setzt retries auf 0 (php/lib/Db/QueueMapper.php:661). Kämen die Zeilen des Melders jede Runde mit gesetzter Dirty-Marke an, wechselten sie nie auf ocr. Hauptverdacht, unbelegt; die Rückfrage mit zwei SQL-Abfragen ist am 24.11. beim Melder gepostet (45-FREIGABEN.md, `Freigabe Rückfrage Issue #25 (F3)`). Der Ursachenfix folgt erst nach den Daten; bis dahin beendet der Backstop jede solche Schleife nach drei verlangten Übergaben.
- I-45-27-02 (OCR-Reserve im Claim, offen): php/lib/Service/QueueService.php:267, `if ($rows <= 0) { break; }` in der Schleife über QueueMapper::KINDS. Ein großer content-Rückstand kann das Budget eines Claims aufbrauchen, bevor die Art ocr an die Reihe kommt; OCR kann dahinter verhungern. Ändert die Claim-Arithmetik und D-07, eigener Plan.
- I-45-27-03 (Give-up-Semantik, Entscheid offen): php/lib/Service/QueueService.php:294, `$row->getRetries() > self::MAX_DELIVERIES` zählt nur Auslieferungen (Hochzählen php/lib/Service/QueueService.php:402), und requeueAs setzt retries beim Spurwechsel auf 0 (php/lib/Db/QueueMapper.php:644 und 661). "gave up" greift bei kreisenden Zeilen deshalb nie; der Backstop im Container deckt das ab, eine Regel auf der Claim-Seite wäre ein eigener Entscheid.
- Hinweis an 45-10: .github/workflows/deploy-harp.yml Z. ~4054 (Kandidatenliste des Upgrade-Beweises druckt `failed/repeatedly_stuck`-Zeilen des alten Bestands) und Z. ~5576 (written_off-Abfrage über oc_findling_file_state erwartet nur Seed-IDs) parsen den repeatedly_stuck-BESTAND. Erzeugt der Backstop auf der Probeinstanz echten Bestand, fällt er dort als unerwarteter Kandidat auf; beim Neulauf von 45-10 beachten.

### Gegenprobe nach dem Fix

Plan 45-20 Task 1, 2026-11-23 ab 10:39 UTC, Repo-Kopf 42ed3b23. Instanz findling-59 (Nextcloud 35.0.3, Port 8091, Volume findling-59-html) aus 45-17, Worktree `<scratchpad>/wt-165` (v1.6.5, 06a0d7c8), Speicher `<scratchpad>/state-59/storage`. Docker seriell, vor dem Start `test -z "$(docker ps -q)"` leer, dann `docker compose -p findling-59 start`. Das Host-Backend startet `<scratchpad>/start59.sh` mit dem gespeicherten Secret und der bestehenden Registrierung neu (`uv run --no-sync python -m findling.main`), beendet wird es mit `<scratchpad>/stop59.sh`. Secrets und Passwörter ausgelassen. Abweichungen vom Standard per Umgebung: `FINDLING_RECONCILE_MIN_INTERVAL_HOURS=1` (Standard 24) und `FINDLING_RECONCILE_HOUR=<Ortsstunde des Host-Prozesses>` (Standard 3), bei jedem Neustart nachgezogen.

#### Quellen vorab (45-20)

Abgerufen am 2026-11-23 per `gh api repos/nextcloud/<repo>/contents/<pfad>?ref=<tag>` (Accept raw), abgelegt unter `<scratchpad>/src20/`, Stand der Instanz: server v35.0.3, app_api v35.0.0. files_accesscontrol am installierbaren Tag v6.0.1 ist in `### Quellen am Tag` schon belegt (CacheWrapper.php Z. 30-34 Maske, Z. 38-56 `formatCacheEntry()` mit `checkFileAccess(..., 0)`, StorageWrapper.php Z. 103-110 `isReadable()`, Z. 241-253 `fopen()` mit `PERMISSION_READ`, Operation.php Z. 118); hier nur die Ergänzungen für Schritt C (c):

- Operation.php v6.0.1 Z. 89-119: passt eine Regel, setzt `deny` (Z. 94-97) die Sperre unabhängig von `requiredPermissions`; eine Rechte-Operation liefert ihre Bits (Z. 107) und wirft nur, wenn `($computedPermissions & $requiredPermissions) !== $requiredPermissions` (Z. 110). CacheWrapper.php Z. 49-50 nimmt die gelieferten Bits aber in den Cache-Eintrag (`$entry['permissions'] &= $permissions`). Eine Rechte-Operation ohne READ nimmt das READ-Bit also schon bei der Auflösung; sie unterscheidet Auflösung und Öffnen nicht. Der Unterschied muss aus der Bedingung kommen, nicht aus der Operation.
- workflowengine `apps/workflowengine/lib/Check/UserGroupMembership.php` v35.0.3 Z. 43-52: `executeCheck()` liest `$this->userSession->getUser()`; mit Person `($operator === 'is') === in_array($value, $groupIds, true)` (Z. 48), ohne Person `return $operator !== 'is';` (Z. 50). Die Bedingung "Gruppe ist nicht Mitglied von X" (`!is`) ist damit ohne aktive Person wahr und für ein Mitglied von X falsch. Gewählte Regel für (c): Operation `deny`, Bedingungen Systemtag `fac59-open` UND Benutzergruppe `!is` `fac-open` (Gruppe nur mit alice). Bei der Auflösung in actAs(alice) (CacheWrapper, aktive Person alice) ist die Gruppenbedingung falsch, das READ-Bit bleibt; beim fopen ohne aktive Person (StorageWrapper Z. 253) ist sie wahr, `deny` wirft `ForbiddenException('Access denied by access control', false)` (Operation.php Z. 118).
- admin_audit v35.0.3: `lib/AppInfo/Application.php` Z. 197-202 hört auf `BeforeNodeReadEvent` und ruft `Files::read()`; `lib/Actions/Files.php` Z. 32-50 schreibt `File with id "%s" accessed: "%s"` mit Datei-ID und `$node->getPath()`; die Identität steht im Feld `user` der Logzeile, `lib/private/Log/LogDetails.php` Z. 40 `$user = \OC_User::getUser() ?: '--';`, also die aktive Person des Requests (ohne aktive Person `--`). Ausgelöst wird das Ereignis aus `lib/private/Files/Node/HookConnector.php` Z. 198-203 (`read`-Hook der View beim fopen). Folge: ein Lesen außerhalb von actAs erscheint mit `"user":"--"`. Die Annahme, ein Lesen in actAs(bob) erscheine mit `"user":"bob"`, war falsch: `ReaderContext::actAs` setzt nur `IUserSession::setVolatileActiveUser`, `\OC_User::getUser()` (lib/private/legacy/OC_User.php v35.0.3 Z. 299-305) liest aber den Sitzungswert `user_id`; auch ein Lesen in actAs erscheint mit `"user":"--"` (echt belegt unten, Befund U-45-20-02). Öffentliche API für eine eigene Zeile: `OCP\Log\Audit\CriticalActionPerformedEvent` (lib/public/Log/Audit/CriticalActionPerformedEvent.php, `@since 22.0.0`, in v33.0.0 und v34.0.0 byte-gleich, v35.0.3 eine Leerzeile mehr), admin_audit registriert dafür `CriticalActionPerformedEventListener` (lib/AppInfo/Application.php v33.0.0 Z. 87, v34.0.0 Z. 88, v35.0.3 Z. 82), der die Meldung mit ihren Parametern über `Action::log` schreibt (lib/Listener/CriticalActionPerformedEventListener.php v35.0.3 Z. 20-30).
- Weg einer 403 mit eigenem Kopf durch die OCS-Hülle: GatewayController ist ein `OCSController` (php/lib/Controller/GatewayController.php Z. 25) mit `#[ExAppRequired]` und `#[ApiRoute]` (Z. 88-90) und gibt bei policy `new DataResponse([...], Http::STATUS_FORBIDDEN)` mit `addHeader(self::REFUSAL_HEADER, self::REFUSAL_POLICY)` zurück (Z. 231-232). `lib/private/AppFramework/Http/Dispatcher.php` v35.0.3 Z. 216-221 baut eine DataResponse noch in `executeController()` über `$controller->buildResponse()` in eine OCS-Antwort um, also vor `afterController` (Z. 129); `lib/private/AppFramework/OCS/BaseResponse.php` Z. 40-41 übernimmt Köpfe und Status der DataResponse (`setHeaders($dataResponse->getHeaders())`, `setStatus(...)`). `lib/private/AppFramework/Middleware/OCSMiddleware.php` Z. 62-81 ersetzt eine 403 nur, wenn die Antwort keine `BaseResponse` ist; die umgebaute Antwort bleibt also mit Kopf. AppAPI v35.0.0 `lib/Middleware/AppAPIAuthMiddleware.php` hat nur `beforeController` (Z. 40) und `afterException` (Z. 64), kein `afterController`; die ExApp ruft die Route direkt per HTTP, kein Proxy dazwischen. Erwartung: der Kopf `X-Findling-Refusal: policy` kommt mit 403 beim Backend an (echt geprüft in M3 unten).

#### Stand vor Schritt 0 (I-45-17-05)

Gelesen am 2026-11-23 um 10:39 UTC bei beendetem Backend-Prozess (kein `findling.main` auf dem Host, Instanz gerade gestartet). Container-Seite: `(wt-165/backend) uv run --no-sync python -I <scratchpad>/attempts.py <state-59>/storage/state.db <ids>` (nur SELECT, Verbindung `mode=ro`); Nextcloud-Seite: `php /tmp/sql59.php "SELECT ..."` im Container (`PRAGMA query_only = ON`).

```
file_id=130 | state=failed | reason=gateway_error | attempts=4 | etag=7390432979f1b94f2d06a19465fe5bfb | deleted_at=None
file_id=133 | state=failed | reason=gateway_error | attempts=4 | etag=30b960be0859588e9f1e6076797d5587 | deleted_at=None
file_id=134 | state=failed | reason=gateway_error | attempts=3 | etag=f33a6f8b7758fce87a4a7961ee13ae23 | deleted_at=None
file_id=135 | state=indexed | reason=None | attempts=3 | etag=aab8f5f9fe4383065c88796e0999e84e | deleted_at=None
file_id=136 | state=indexed | reason=None | attempts=4 | etag=8011b3c9c02f76ae5c3329355affaca3 | deleted_at=None
file_id=137 | state=indexed | reason=None | attempts=2 | etag=8e765fe9e3e9366430c5d5bdbc69c016 | deleted_at=None
file_id=141 | state=failed | reason=gateway_error | attempts=4 | etag=cb3ba36a001ac81f2762794231cfc3ca | deleted_at=None
file_id=142 | state=failed | reason=gateway_error | attempts=4 | etag=0023ea50ab9cf1aac9d47c9e83e414a4 | deleted_at=None
file_id=143 | state=failed | reason=gateway_error | attempts=4 | etag=d05ee6e3ec4760ac39292decc5372396 | deleted_at=None
file_id=152 | state=indexed | reason=None | attempts=2 | etag=fe9d3461b04a939e88181de2ec952d67 | deleted_at=None
file_id=153 | state=indexed | reason=None | attempts=2 | etag=e40b704b979501e145698aec73366777 | deleted_at=None
-- oc_findling_file_state
file_id=134 | state=failed | reason=gateway_error | updated_at=2026-11-22 11:40:56
-- oc_findling_queue
file_id=130 | storage_id=3 | locked_at=2026-11-22 11:37:35 | retries=2 | kind=content
file_id=133 | storage_id=3 | locked_at=2026-11-22 11:37:35 | retries=2 | kind=content
file_id=141 | storage_id=4 | locked_at=2026-11-22 11:37:35 | retries=2 | kind=content
file_id=142 | storage_id=4 | locked_at=2026-11-22 11:37:35 | retries=2 | kind=content
file_id=143 | storage_id=4 | locked_at=2026-11-22 11:37:35 | retries=2 | kind=content
```

| fileId | Zustand | Grund | attempts | Abgleiche bis 4 | Erwartung Schritt 0 |
|---|---|---|---|---|---|
| 130, 133 (bob), 141, 142, 143 (dave) | failed | gateway_error | 4 | 0 | direkt Gegenkontrolle; sie liegen aber noch belastet in der Warteschlange (`retries=2`, Sperre seit 2026-11-22 11:52:35 abgelaufen) und werden beim Start erneut beansprucht, unabhängig vom Abgleich |
| 134 (bob) | failed | gateway_error | 3 | 1 | ein Abgleich übergibt 134, attempts 4, danach Gegenkontrolle |
| 135, 136, 137, 152, 153 | indexed | | 3, 4, 2, 2, 2 | entfällt | bleiben indexed (in M1 lesbar) |

#### Schritt 0 Serie auf v1.6.5

Entscheid d1: echt abgewartet, je Zyklus die Stunde nachgezogen, beide Hälften aus dem Worktree `wt-165` (v1.6.5), M1 (shareDisabledDownload) aktiv. Kein Eingriff in state.db.

Zyklus 1: Backend um 10:40:15 UTC gestartet (`FINDLING_RECONCILE_MIN_INTERVAL_HOURS=1 FINDLING_RECONCILE_HOUR=11`, Ortsstunde CET; letzter fertiger Zyklus 2026-11-22 11:40 UTC, also fällig). Log `state-59/exapp-s0-zyklus1.log`, wörtlich (Heartbeat-Zeilen ausgelassen):

```
INFO:findling.worker.doc_keys:doc key verify, checked=60 corrected=0
INFO:findling.worker.reconcile:reconcile round walked, mounts=7 slices=7 seen=60 stale=1 missing=0 given_up=0
WARNING:findling.worker.poller:content gateway refused one file, http status 500 for file id 141
WARNING:findling.worker.poller:content gateway refused one file, http status 500 for file id 142
WARNING:findling.worker.poller:content gateway refused one file, http status 500 for file id 143
WARNING:findling.worker.poller:content gateway refused one file, http status 500 for file id 130
WARNING:findling.worker.poller:content gateway refused one file, http status 500 for file id 133
WARNING:findling.worker.poller:content gateway refused 5 files of this pass with http status 500 from 2 storages, taken as an outage
WARNING:findling.worker.poller:indexing pass stopped, the content gateway is unavailable, 1 rows handed back, 5 charged
WARNING:findling.worker.poller:content gateway refused one file, http status 500 for file id 134
INFO:findling.worker.poller:pass finished, claimed=1 indexed=0 skipped=0 failed=1 unchanged=0 requeued=0 embedded=0 committed=0 slots=1 throttled=0
```

Der Abgleich übergab genau eine Datei (`stale=1`, 134). Die fünf Zeilen 130, 133, 141, 142, 143 kamen nicht vom Abgleich, sondern lagen seit 45-17 belastet in der Warteschlange (Sperre abgelaufen) und wurden beim Start erneut beansprucht; sie lösten auf 1.6.5 wieder die Ausfall-Eskalation aus (Befund I-45-17-01, Gegenkontrolle für den Abschnitt `Keine Ausfall-Eskalation` unten) und wurden mit `retries=3` erneut 900 s gesperrt. Nach Ablauf (10:55:21) schrieb die Nextcloud-Seite sie um 10:56:23 als `failed(repeatedly_stuck)` ab, die Warteschlange war danach leer. Stand 10:41 UTC:

```
file_id=130 | state=failed | reason=gateway_error | attempts=5
file_id=133 | state=failed | reason=gateway_error | attempts=5
file_id=134 | state=failed | reason=gateway_error | attempts=4
file_id=141 | state=failed | reason=gateway_error | attempts=5
file_id=142 | state=failed | reason=gateway_error | attempts=5
file_id=143 | state=failed | reason=gateway_error | attempts=5
-- oc_findling_file_state
file_id=134 | state=failed | reason=gateway_error | updated_at=2026-11-23 10:40:37
-- oc_findling_queue (10:41)
file_id=130 | storage_id=3 | locked_at=2026-11-23 10:40:21 | retries=3
(133, 141, 142, 143 gleich)
```

Zyklus 2, Gegenkontrolle: Backend um 11:41:14 UTC neu gestartet (`FINDLING_RECONCILE_HOUR=12`, Ortsstunde; Zyklus 1 lag eine Stunde zurück). Log `state-59/exapp-s0b.log`:

```
INFO:findling.worker.doc_keys:doc key verify, checked=60 corrected=0
INFO:findling.worker.poller:indexing is armed and the work stock is empty, the next file is picked up as it arrives
INFO:findling.worker.reconcile:reconcile round walked, mounts=7 slices=7 seen=60 stale=0 missing=0 given_up=0
```

Stand 11:42 UTC (state.db und Nextcloud-Seite), keine Gateway-Anfrage, keine refused-Zeile, Warteschlange `n=0`:

```
file_id=130 | state=failed | reason=gateway_error | attempts=5
file_id=133 | state=failed | reason=gateway_error | attempts=5
file_id=134 | state=failed | reason=gateway_error | attempts=4
file_id=141 | state=failed | reason=gateway_error | attempts=5
file_id=142 | state=failed | reason=gateway_error | attempts=5
file_id=143 | state=failed | reason=gateway_error | attempts=5
-- oc_findling_file_state
file_id=130 | state=failed | reason=repeatedly_stuck | updated_at=2026-11-23 10:56:23
file_id=133 | state=failed | reason=repeatedly_stuck | updated_at=2026-11-23 10:56:23
file_id=134 | state=failed | reason=gateway_error | updated_at=2026-11-23 10:40:37
file_id=141 | state=failed | reason=repeatedly_stuck | updated_at=2026-11-23 10:56:23
file_id=142 | state=failed | reason=repeatedly_stuck | updated_at=2026-11-23 10:56:23
file_id=143 | state=failed | reason=repeatedly_stuck | updated_at=2026-11-23 10:56:23
```

Ergebnis Schritt 0: die Serie ist auf v1.6.5 ausgeschöpft, 134 mit attempts 4 nach genau einer Übergabe durch den Abgleich, die übrigen fünf mit attempts 5 (die fünfte Ablehnung kam aus der Warteschlange, nicht aus dem Abgleich). Der nächste Abgleich übergibt keine dieser Dateien mehr (`stale=0`, attempts unverändert). Urteile der Nextcloud-Seite: 134 `failed(gateway_error)`, 130, 133, 141, 142, 143 `failed(repeatedly_stuck)`. Abweichung von der Erwartung: attempts steht bei fünf Dateien auf 5 statt 4, weil die belasteten Warteschlangenzeilen aus 45-17 erneut beansprucht wurden; für die Serie des Abgleichs ohne Wirkung (er übergibt ab attempts über 3 nicht mehr), kein Befund.

#### Schritt A: neuer Container vor der Begleit-App 1.6.5

11:42:57 UTC: Backend 1.6.5 beendet, `FINDLING_PORT=8091 FINDLING_RECONCILE_MIN_INTERVAL_HOURS=1 FINDLING_RECONCILE_HOUR=13 sh <scratchpad>/register20.sh` (Kopie von scripts/dev/register-exapp.sh mit `REPO_ROOT` = Hauptarbeitsbaum, Backend per `uv run --no-sync`), php/ bleibt der Worktree `wt-165`:

```
registering version 1.7.0 with 6 routes from backend/appinfo/info.xml
ExApp findling_backend deployed successfully.
ExApp findling_backend successfully registered.
$ occ app_api:app:list
findling_backend (Findling Backend): 1.7.0 [enabled]
```

Backend-Log `state-59/exapp.log` beim Start, wörtlich:

```
INFO:findling.store.repo:refusal streaks renewed once after the update, rows=6 mark=refusal_streaks_1_7_0
INFO:findling.worker.doc_keys:doc key verify, checked=60 corrected=0
INFO:findling.worker.poller:indexing is armed and the work stock is empty, the next file is picked up as it arrives
```

Profil, wie das Backend es liest (`<scratchpad>/gw20.sh admin /ocs/v2.php/apps/findling/profile?format=json 1.7.0`, AppAPI-Kopf mit dem Secret der Registrierung, nicht ausgegeben):

```
HTTP/1.1 200 OK
{"ocs":{"meta":{"status":"ok","statuscode":200,"message":"OK"},"data":{"profile":"economy","precision":"int8","confirmed":null,"verdicts":3,"paused":false}}}
```

Generation 3: die Begleit-App 1.6.5 meldet `verdicts` 3. Abgleich nach einer echt abgewarteten Stunde (12:43:5x UTC, Ortsstunde 13), Log wörtlich:

```
INFO:findling.worker.reconcile:reconcile round walked, mounts=7 slices=7 seen=60 stale=6 missing=0 given_up=0
WARNING:findling.worker.poller:content gateway refused one file, http status 500 for file id 130
WARNING:findling.worker.poller:content gateway refused one file, http status 500 for file id 133
WARNING:findling.worker.poller:content gateway refused one file, http status 500 for file id 134
WARNING:findling.worker.poller:content gateway refused one file, http status 500 for file id 141
WARNING:findling.worker.poller:content gateway refused one file, http status 500 for file id 142
WARNING:findling.worker.poller:content gateway refused 5 files of this pass with http status 500 from 2 storages, taken as an outage
WARNING:findling.worker.poller:indexing pass stopped, the content gateway is unavailable, 1 rows handed back, 5 charged
WARNING:findling.worker.poller:content gateway refused one file, http status 500 for file id 143
INFO:findling.worker.poller:pass finished, claimed=1 indexed=0 skipped=0 failed=1 unchanged=0 requeued=0 embedded=0 committed=0 slots=1 throttled=0
```

Der Abgleich übergibt die sechs Dateien (`stale=6`, durch die Erneuerung wieder Kandidaten). Die Begleit-App 1.6.5 antwortet weiter 500, mit derselben Secure-View-Ausnahme wie vorher (`php /tmp/nclog20.php nextcloud.log 2026-11-23T11:42:00`, gekürzt):

```
2026-11-23T12:45:27+00:00 level=3 user=-- app=findling GET /ocs/v2.php/apps/findling/files/130?userId=alice message=Findling: unknown error reading a file | Exception=OCP\Files\ForbiddenException Message=Download blocked due the secure view policy File=SecureViewWrapper.php Line=97
(133, 134, 141, 142 um 12:45:27, 143 um 12:47:28 gleich)
```

Quittung ohne 400: die Zugriffsprotokolle des Containers seit 12:40 UTC (`docker logs --since`, Pfad ohne Query) zeigen für die Begleit-App nur 200 außer den sechs Gateway-Antworten 500:

```
      1 "DELETE /ocs/v2.php/apps/findling/queues/documents HTTP/1.1" 200
      6 "GET /ocs/v2.php/apps/findling/files/<130|133|134|141|142|143> HTTP/1.1" 500
      7 "GET /ocs/v2.php/apps/findling/files/slice HTTP/1.1" 200
      1 "GET /ocs/v2.php/apps/findling/mounts HTTP/1.1" 200
     35 "GET /ocs/v2.php/apps/findling/profile HTTP/1.1" 200
      5 "GET /ocs/v2.php/apps/findling/queues/documents HTTP/1.1" 200
      8 "GET /ocs/v2.php/apps/findling/queues/documents/stats HTTP/1.1" 200
      2 "POST /ocs/v2.php/apps/findling/queues/documents/requeue HTTP/1.1" 200
      3 "POST /ocs/v2.php/apps/findling/queues/documents/topup HTTP/1.1" 200
      1 "POST /ocs/v2.php/apps/findling/queues/documents/unlock HTTP/1.1" 200
```

Die Quittung (`DELETE /queues/documents`) für 143 antwortet 200, `oc_findling_file_state` danach `file_id=143 | state=failed | reason=gateway_error | updated_at=2026-11-23 12:47:28`. nextcloud.log seit 11:42 hat außer den sechs Secure-View-Zeilen nur vier Zeilen von 11:43:07 (`Invalid signature for ExApp: findling_backend and user: null`, `ExApp findling_backend request to NC validation failed`): das neue Backend fragte während der Neuregistrierung mit dem neuen Secret, bevor AppAPI es kannte; danach keine mehr. Im Backend-Log steht keine 4xx-Antwort außer `PUT /enabled?enabled=0 401` (die Abmeldung der alten Registrierung mit dem alten Secret). Container-Urteile nach dem Pass: 130, 133, 134, 141, 142 `failed(gateway_error)` attempts 2, 143 attempts 1.

Grenze dieser Kombination: `policy_blocked -> gateway_error` ist hier nicht erreichbar, weil die Begleit-App 1.6.5 den Kopf `X-Findling-Refusal` nie sendet (sie antwortet 500). Belegt per pytest am Kopf 42ed3b23: `tests/test_queue_client.py::test_policy_blocked_reaches_only_a_companion_of_generation_4[profile0-gateway_error]` bis `[profile2-gateway_error]` und `[profile3-policy_blocked]`, `test_the_failed_fallback_per_generation` (5 passed).

Die fünf beim Ausfall belasteten Zeilen (130, 133, 134, 141, 142, `retries=1`, gesperrt ab 12:45:27) blieben bis zu ihrer Abschreibung durch die Warteschlange bei der Begleit-App 1.6.5, damit die Dateien in Schritt B über den Abgleich und nicht über eine alte Warteschlangenzeile kommen (Stand vor Schritt B unten).

#### Befund U-45-20-01 und Fix (Erneuerung erst ab Generation 4)

| ID | Schwere | Befund | Beleg | Entscheid |
|---|---|---|---|---|
| U-45-20-01 | MEDIUM | Die einmalige Erneuerung `refusal_streaks_1_7_0` lief beim Start des Containers 1.7.0 auch vor einer Begleit-App 1.6.5 (Generation 3). Der Abgleich gab die erneuerten Dateien dieser Begleit-App, die sie weiter mit 500 ablehnte; mit fünf Dateien auf zwei Speichern eskalierte der Pass, und drei Belastungen einer Eskalation hätten die Serie vor dem Update der Begleit-App verbraucht (poller.py `_mark_the_charged`: "after three charges Nextcloud writes it off as failed(repeatedly_stuck) … the charges count as that streak"). In der empfohlenen Reihenfolge (Container zuerst) wären die Dateien danach ohne `--restart` nie mehr gelesen worden; ohne Eskalation nach drei Nächten ebenso | Schritt A erster Lauf oben: `rows=6`, `stale=6`, `5 charged`, attempts 2, fünf Warteschlangenzeilen `retries=1` | Owner "Ok wie empfohlen" (2026-11-23 12:58 UTC): f1, MEDIUM, Fix per TDD, Schritte A und B neu, keine CHANGELOG-Zeile |

Fix (Kopf 151dca7b): `Store.renew_refusal_streaks(companion_generation=...)` führt die Marke `refusal_streaks_1_7_0` nur bei einer Generation ab `RENEW_1_7_0_MIN_GENERATION` (4) aus, die Marke von 1.6.3 unverändert bei jedem Öffnen; der Poller fragt sie einmal je Prozess im ersten Pass, der auf der Profilantwort Generation 4 liest, vor dem Claim. Die Aufrufe beim Öffnen (Poller `_open_store`, Abgleich) erneuern nur noch unter der Marke von 1.6.3. Was vor der alten Begleit-App aufläuft (attempts aus Ablehnungen und Belastungen), setzt die spätere Erneuerung zurück; die Abschreibung `repeatedly_stuck` auf der Nextcloud-Seite und Warteschlangenzeilen hindern den Abgleich nicht (Quelle: reconcile.py `_compare` liest nur den Zustand des Containers, "whatever the Nextcloud side carries for it"; echt belegt im Neulauf unten). Die zweite Variante (Ablehnungen vor Generation 4 verbrauchen die Serie nicht) ist deshalb nicht nötig.

RED (Commit aec5edcf, vor der Änderung, `pytest -k "renewal or renews or generation_4 or updated_later or no_trace"`):

```
FAILED tests/test_poller.py::test_the_renewal_of_1_7_0_runs_in_the_first_pass_that_reads_generation_4[4-True]
FAILED tests/test_poller.py::test_a_companion_updated_later_still_gets_the_renewal
FAILED tests/test_store_repo.py::test_the_renewal_of_1_7_0_waits_for_a_companion_of_generation_4[None]
FAILED tests/test_store_repo.py::test_the_renewal_of_1_7_0_waits_for_a_companion_of_generation_4[2]
FAILED tests/test_store_repo.py::test_the_renewal_of_1_7_0_waits_for_a_companion_of_generation_4[3]
FAILED tests/test_store_repo.py::test_a_later_generation_renews_as_well - Typ...
FAILED tests/test_store_repo.py::test_refusals_under_a_companion_of_generation_3_leave_no_trace_after_the_renewal
7 failed, 8 passed, 386 deselected in 1.28s
```

GREEN (Commit 151dca7b): `tests/test_poller.py tests/test_store_repo.py tests/test_reconcile.py` 521 passed, 1 skipped; volle Suite 7395 passed, 305 skipped; ruff check, ruff format --check, pyright (latest, 0 errors), vulture grün; `bash scripts/dev/php_gates_docker.sh all` exit 0 (Psalm taint findings 0, zizmor und actionlint grün). Drei bestehende Tests rufen die Erneuerung jetzt mit `companion_generation=4` (test_store_repo.py zwei Tests zur Marke 1.7.0, test_reconcile.py `test_a_spent_refusal_of_1_6_is_work_again_after_the_renewal_of_1_7_0`).

Mutationen (je eine, danach `cmp` gegen die gesicherte Datei, Original wieder 18 passed):

| Mutation | Ergebnis |
|---|---|
| M1 Bedingung in repo.py durch `if True:` ersetzt (immer erneuern) | 4 failed, 14 passed |
| M2 `RENEW_1_7_0_MIN_GENERATION = 3` | 4 failed, 14 passed |
| M3 Aufruf im Pass des Pollers entfernt | 2 failed, 16 passed |
| M4 Generation nicht weitergereicht (`renew_refusal_streaks()`) | 2 failed, 16 passed |

Baumhash des Pakets (test_measurement_scripts.py): efc966a5... mit Rezept und mit find, sort, sed, sha256sum gleich, Positivkontrolle über git archive von 42ed3b23 d45bc1d3... (der alte Wert).

Rückkehr der Instanz für den Neulauf (13:27 UTC, Backend beendet): die Probe braucht eine Datenbank, in der die Erneuerung von 1.7.0 noch nicht gelaufen ist, und Spuren von Ablehnungen vor Generation 4. Deshalb nur die Marke entfernt (`(backend) uv run --no-sync python -I <scratchpad>/restore20.py <state-59>/storage/state.db`, Ausgabe `state-59/restore20.txt`); die Spuren aus dem ersten Lauf von A bleiben bewusst stehen, weil genau sie die Spurfreiheit belegen:

```
-- vorher
meta refusal_streaks_1_6_3=done
meta refusal_streaks_1_7_0=done
file_id=130 | state=failed | reason=gateway_error | attempts=2
(133, 134, 141, 142, 143 gleich, attempts 2)
DELETE FROM meta WHERE key = 'refusal_streaks_1_7_0' -> 1 Zeile
-- nachher
meta refusal_streaks_1_6_3=done
(Dateien unverändert, attempts 2)
-- oc_findling_queue
file_id=130 | locked_at=2026-11-23 12:45:27 | retries=1
(133, 134, 141, 142 gleich)
-- oc_findling_file_state
130, 133, 141, 142 failed(repeatedly_stuck) 10:56:23; 134 failed(gateway_error) 10:40:37; 143 failed(gateway_error) 12:47:28
```

Der Zustand vor dem ersten Lauf von A (attempts 5 bzw. 4, ohne Marke 1.7.0) ist in Schritt 0 belegt; der Neulauf beginnt mit kürzeren Serien, damit Ablehnungen vor Generation 4 überhaupt Spuren hinterlassen können.

#### Schritt A nach dem Fix (Neulauf)

13:27:40 UTC: `FINDLING_PORT=8091 FINDLING_RECONCILE_MIN_INTERVAL_HOURS=1 FINDLING_RECONCILE_HOUR=14 sh <scratchpad>/register20.sh` (Container am Kopf 151dca7b, php/ weiter Worktree `wt-165`, Begleit-App 1.6.5). `registering version 1.7.0`, `ExApp findling_backend successfully registered.` Profil wie oben `"verdicts":3`. Backend-Log `state-59/exapp.log` beim Start: keine Zeile `refusal streaks renewed`, die Marke fehlt weiter (`meta.py`: nur `refusal_streaks_1_6_3=done`). Die fünf Warteschlangenzeilen aus dem ersten Lauf (Sperre abgelaufen) holte der Poller sofort und die Begleit-App 1.6.5 lehnte sie ab, ebenso um 13:44 nach Ablauf der neuen Sperre, wörtlich (zweimal):

```
WARNING:findling.worker.poller:content gateway refused one file, http status 500 for file id 130
WARNING:findling.worker.poller:content gateway refused one file, http status 500 for file id 133
WARNING:findling.worker.poller:content gateway refused one file, http status 500 for file id 134
WARNING:findling.worker.poller:content gateway refused one file, http status 500 for file id 141
WARNING:findling.worker.poller:content gateway refused one file, http status 500 for file id 142
WARNING:findling.worker.poller:content gateway refused 5 files of this pass with http status 500 from 2 storages, taken as an outage
WARNING:findling.worker.poller:indexing pass stopped, the content gateway is unavailable, 0 rows handed back, 5 charged
```

Abgleich nach einer echt abgewarteten Stunde (13:48 UTC, Ortsstunde 14), wörtlich:

```
INFO:findling.worker.reconcile:reconcile round walked, mounts=7 slices=7 seen=60 stale=1 missing=0 given_up=0
WARNING:findling.worker.poller:content gateway refused one file, http status 500 for file id 143
INFO:findling.worker.poller:pass finished, claimed=1 indexed=0 skipped=0 failed=1 unchanged=0 requeued=0 embedded=0 committed=0 slots=1 throttled=0
```

Stand danach (state.db): 130, 133, 134, 141, 142 `failed(gateway_error)` attempts 4 (über der Grenze, der Abgleich gibt sie nicht mehr), 143 attempts 3; keine Marke `refusal_streaks_1_7_0`. Das ist die Lage, die der Befund beschreibt: vor der Begleit-App der Generation 3 ist die Serie verbraucht. Mit dem Fix ist sie das nur bis zur Erneuerung, die erst vor Generation 4 läuft (Schritt B).

#### Suche direkt nach dem Update (45-26)

Vor dem Bind-Mount (14:00:08 UTC, Backend 1.7.0 am Kopf 151dca7b läuft, Begleit-App noch 1.6.5): `backend_app_version` in oc_appconfig leer (die Admin-Seite war seit 45-17 nicht offen), deshalb `occ config:app:set findling backend_app_version --value=1.6.5` (`Config value 'backend_app_version' for app 'findling' is now set to '1.6.5'`). Dann `docker compose -f <scratchpad>/compose-59b.yaml -p findling-59 up -d` (php/ des Hauptarbeitsbaums als Bind-Mount, sonst gleich compose-59.yaml), `occ upgrade`:

```
Updating <findling> ...
Updated <findling> to 1.7.0
Update successful
The database schema does not match what is expected for the installed version:
  - oc_job_classes_registry: missing index 'class_index'
  - oc_federated_invites: missing index 'UNIQ_A2C17D5A5F37A13B'
```

(Die zwei fehlenden Indizes gehören zum Nextcloud-Kern, nicht zu Findling, und standen vor dem Update schon so; ohne Bezug zur Probe.) Direkt danach (14:00:28 UTC), vor jedem Aufruf der Admin-Seite, der Überblick- oder Status-Route und vor dem ersten Abgleich mit der neuen Begleit-App (`<scratchpad>/stepB1.sh`, Ausgabe `state-59/stepB1.txt`):

Vorher backend_app_version: 1.6.5 (per occ gesetzt, Zustand einer Instanz, deren Admin-Seite zuletzt vor dem Update offen war)
Nachher backend_app_version: (leer)
oc_migrations: 001700Date20261123000000
OCS direkt nach dem Update: {"ocs":{"meta":{"status":"ok","statuscode":200,"message":"OK"},"data":{"name":"File contents","isPaginated":false,"entries":[{"thumbnailUrl":"","title":"wz59-offen.odt","subline":"Positivkontrolle59 Dieser Text ist lang genug, damit er ohne OCR als Klartext gelesen","resourceUrl":"\/f\/135","icon":"icon-search","rounded":false,"attributes":{"fileId":"135","highlights":"[[0,18]]"}}],"cursor":null}}
Suche direkt nach dem Update: 1 Treffer für Positivkontrolle59 als bob, vor jedem Aufruf der Admin-Seite
Drift-Zeilen nextcloud.log: 0 vorher, 0 nachher

Weiter: `occ app:list` `findling: 1.7.0`, `app_api: 35.0.0`, `richdocuments: 12.0.2`, `groupfolders: 23.0.1`; SHA-256 von `lib/Service/GatewayReader.php` im Container 5f92e444... gleich der Datei im Repo und `git show HEAD:php/lib/Service/GatewayReader.php`. Profil `"verdicts":4` (Generation 4). Im Backend-Log danach, im ersten Pass mit Generation 4:

```
INFO:findling.store.repo:refusal streaks renewed once after the update, rows=6 mark=refusal_streaks_1_7_0
```

state.db danach: 130, 133, 134, 141, 142, 143 `failed(gateway_error)` attempts 1. Die Spuren der Zeit vor Generation 4 (attempts 4, `failed(repeatedly_stuck)` auf der Nextcloud-Seite seit 13:59:51, Warteschlange abgeschrieben) stehen der Serie nicht mehr im Weg.

#### Schritt B: neue Begleit-App, M1 über den Abgleich

Abgleich mit der Begleit-App 1.7.0: Backend am Kopf 151dca7b um 14:49:06 UTC neu gestartet (`FINDLING_RECONCILE_MIN_INTERVAL_HOURS=1 FINDLING_RECONCILE_HOUR=15`; der letzte fertige Zyklus von 13:48 lag eine Stunde zurück), kein `--restart`. Backend-Log `state-59/exapp-b.log`, wörtlich:

```
INFO:findling.worker.reconcile:reconcile round walked, mounts=28 slices=28 seen=67 stale=6 missing=0 given_up=0
INFO:findling.index.writer:committed 6 documents
INFO:findling.worker.poller:pass finished, claimed=6 indexed=6 skipped=0 failed=0 unchanged=0 requeued=0 embedded=0 committed=6 slots=1 throttled=0
```

(mounts=28 und seen=67: die Saat für M3 und TF-zwanzig mit u01 bis u20 lag zu diesem Zeitpunkt schon an, siehe unten.) Messung (`<scratchpad>/meas20.sh`, Ausgabe `state-59/meas20-B-M1.txt`), wörtlich:

```
-- Gateway-Anfragen laut Zugriffsprotokoll seit 2026-11-23T14:49:00Z (Datei-ID, Leser, Status)
      1 GET /ocs/v2.php/apps/findling/files/130?userId=bob 200
      1 GET /ocs/v2.php/apps/findling/files/133?userId=bob 200
      1 GET /ocs/v2.php/apps/findling/files/134?userId=bob 200
      1 GET /ocs/v2.php/apps/findling/files/141?userId=dave 200
      1 GET /ocs/v2.php/apps/findling/files/142?userId=dave 200
      1 GET /ocs/v2.php/apps/findling/files/143?userId=dave 200
-- Backend-Zeilen seit Beginn (gefiltert, ohne Secrets)
      1 INFO:findling.worker.poller:pass finished, claimed=6 indexed=6 skipped=0 failed=0 unchanged=0 requeued=0 embedded=0 committed=6 slots=1 throttled=0
-- state.db
file_id=130 | state=indexed | reason=None | attempts=2 | etag=7390432979f1b94f2d06a19465fe5bfb | deleted_at=None
file_id=133 | state=indexed | reason=None | attempts=2 | etag=30b960be0859588e9f1e6076797d5587 | deleted_at=None
file_id=134 | state=indexed | reason=None | attempts=2 | etag=f33a6f8b7758fce87a4a7961ee13ae23 | deleted_at=None
file_id=135 | state=indexed | reason=None | attempts=3 | etag=aab8f5f9fe4383065c88796e0999e84e | deleted_at=None
file_id=136 | state=indexed | reason=None | attempts=4 | etag=8011b3c9c02f76ae5c3329355affaca3 | deleted_at=None
file_id=137 | state=indexed | reason=None | attempts=2 | etag=8e765fe9e3e9366430c5d5bdbc69c016 | deleted_at=None
file_id=141 | state=indexed | reason=None | attempts=2 | etag=cb3ba36a001ac81f2762794231cfc3ca | deleted_at=None
file_id=142 | state=indexed | reason=None | attempts=2 | etag=0023ea50ab9cf1aac9d47c9e83e414a4 | deleted_at=None
file_id=143 | state=indexed | reason=None | attempts=2 | etag=d05ee6e3ec4760ac39292decc5372396 | deleted_at=None
file_id=152 | state=indexed | reason=None | attempts=2 | etag=fe9d3461b04a939e88181de2ec952d67 | deleted_at=None
file_id=153 | state=indexed | reason=None | attempts=2 | etag=e40b704b979501e145698aec73366777 | deleted_at=None
-- Unified Search (OCS, Provider findling): Treffer je Wort und Nutzer
Wasserzeichenprobe59a bob=1 alice=1 carol=0
Wasserzeichenprobe59b bob=1 alice=1 carol=0
Wasserzeichenprobe59c bob=1 alice=1 carol=0
Wasserzeichenprobe59d dave=1 alice=1 carol=0
Wasserzeichenprobe59e dave=1 alice=1 carol=0
Wasserzeichenprobe59f dave=1 alice=1 carol=0
Positivkontrolle59 bob=1 alice=1 carol=0
Eigenprobe59 bob=1 alice=0 carol=0
Leseprobe59 bob=1 alice=1 carol=0
Teamordnerprobe59a bob=1 alice=1 carol=1
Teamordnerprobe59b bob=1 alice=1 carol=0
```

Die sechs gesperrten Dateien sind über den Abgleich ohne `occ findling:index --restart` indexiert, gelesen vom Besitzer (bob bzw. dave), jeweils mit einem einzigen Öffnen ohne aktive Person (der Home-Mount des Besitzers trägt keine Freigabe, shareDisabledDownload greift dort nicht, kein Secure-View-Eintrag in nextcloud.log seit 14:49). Eine indexierte Datei hat in `oc_findling_file_state` keine Zeile (die Nextcloud-Seite schreibt nur Fehlurteile). Unified Search: Besitzer und alice finden jedes Wort, carol keins außer der Positivkontrolle `Teamordnerprobe59a` aus TF-lesen, in dem sie Mitglied ist.

#### Pfad folgt dem Besitzer (I-45-17-06)

Datei 130 (`wz59-b1.odt` von bob, an alice ohne Download freigegeben, M1). In 1.6.5 las alice (`userId=alice`, Vorher-Tabelle), im Abgleich von Schritt B liest der Besitzer: `GET /ocs/v2.php/apps/findling/files/130?userId=bob 200` (14:49 UTC). Damit sich die Pfade beider Personen unterscheiden, hat bob die Datei danach per WebDAV in seinen Ordner `Ablage` verschoben (`MKCOL 201`, `MOVE 201`, 14:50:35 UTC); alice sieht die Freigabe weiter unter `/wz59-b1.odt`. Belege nach dem Lauf der Metadaten-Zeile (`<scratchpad>/pfad20.sh`, Ausgabe `state-59/pfad20.txt`):

(1) Auftrag und Zustand: `oc_findling_queue` führt keinen Pfad (Spalten `id, file_id, storage_id, root_id, is_update, size, locked_at, retries, dirty, claim_token, kind`), während des Laufs stand dort `file_id=130 | storage_id=3 | retries=0`; `oc_filecache` `fileid=130 | storage=3 | path=files/Ablage/wz59-b1.odt` (bobs Speicher); state.db `path=Ablage/wz59-b1.odt`, `state=indexed` (relativ zu bobs Ordner, gewollt: QueueServiceReaderTest `testTheOwnerIsTheReaderBeforeAnAlphabeticallyEarlierRecipient`); `oc_findling_file_state` hat für eine indexierte Datei keine Zeile.

(2) Admin-Seite, Einzelabfrage als admin (`GET /apps/findling/admin/diagnose?ref=130`):

```
{"found":true,"fileId":130,"path":"Ablage\/wz59-b1.odt","reference":"bob\/files\/Ablage\/wz59-b1.odt","uid":"bob","trashed":false,"shares":1,"state":"indexed","reason":"","label":"Indexed","remedy":"The content of this file is searchable.","errorClass":"","checkedAt":1795445472,"backendReachable":true,"note":""}
```

Die Admin-Seite zeigt den Pfad des Besitzers samt Referenz `bob/files/...`; sie ist nur für Admins erreichbar und zeigte diesen Pfad schon in 1.6.5 (die Einzelabfrage löst über den Besitzer auf), alice sieht sie nicht.

(3) admin_audit (vor dem Abgleich von Schritt B aktiviert), `audit.log` über `php /tmp/nclog20.php`:

```
2026-11-23T14:49:25+00:00 level=1 user=-- app=admin_audit GET /ocs/v2.php/apps/findling/files/130?userId=bob message=File with id "130" accessed: "/bob/files/wz59-b1.odt"
2026-11-23T14:50:35+00:00 level=1 user=bob app=admin_audit MOVE /remote.php/dav/files/bob/wz59-b1.odt message=File renamed with id "130" from "/bob/files/wz59-b1.odt" to "/bob/files/Ablage/wz59-b1.odt"
```

Das Gateway-Lesen steht mit dem Pfad in bobs Ordner und `user=--` (das erste Öffnen ohne aktive Person gelang, weil bobs Home-Mount keine Freigabe trägt und shareDisabledDownload dort nicht greift; kein erneutes Öffnen in actAs).

(4) Unified Search über OCS (`Wasserzeichenprobe59a`), nach dem Verschieben:

OCS alice: {"ocs":{"meta":{"status":"ok","statuscode":200,"message":"OK"},"data":{"name":"File contents","isPaginated":false,"entries":[{"thumbnailUrl":"","title":"wz59-b1.odt","subline":"wz59-b1.odt","resourceUrl":"\/f\/130","icon":"icon-search","rounded":false,"attributes":{"fileId":"130"}}],"cursor":null}}}
OCS bob: {"ocs":{"meta":{"status":"ok","statuscode":200,"message":"OK"},"data":{"name":"File contents","isPaginated":false,"entries":[{"thumbnailUrl":"","title":"wz59-b1.odt","subline":"Wasserzeichenprobe59a Dieser Text ist lang genug, damit er ohne OCR als Klartext gelesen","resourceUrl":"\/f\/130","icon":"icon-search","rounded":false,"attributes":{"fileId":"130","highlights":"[[0,21]]"}}],"cursor":null}}}


alice bekommt Titel `wz59-b1.odt`, als `subline` ihren eigenen Pfad `wz59-b1.odt` (ohne Ausschnitt nach E3) und den Link `/f/130`; bob bekommt den Ausschnitt und denselben Link. `/f/<id>` löst Nextcloud für jede Person in ihrem eigenen Baum auf. Der Pfad aus bobs Ordner (`Ablage/...`) erscheint für alice nirgends.

Urteil I-45-17-06: korrekt, der Besitzer liest und Zustand, Admin-Seite und Prüfspur führen bobs Pfad, während der Treffer jeder Person ihren eigenen Pfad und denselben id-basierten Link zeigt; für alice erscheint kein Pfad aus bobs Ordner.

#### Keine Ausfall-Eskalation (I-45-17-01)

M3 allTags nach dem Fix.

Aufbau: Systemtag 1 (`wz59-tag`, `watermark_allTagsList=1`) an 130, 136 (bob, aus 45-17), an sechs neuen Dateien auf zwei Speichern und an der Datei in TF-zwanzig (`<scratchpad>/seed20.sh`, Ausgabe `state-59/seed20.txt`; Tag per `PUT /remote.php/dav/systemtags-relations/files/<id>/1` je HTTP 201, an 257 als u01 erst mit Schreibrecht, danach wieder nur lesend). Speicher belegt per `oc_filecache` und `oc_storages`:

```
fileid=162 | storage=3 | path=files/wz20-m3-b1.odt
fileid=165 | storage=3 | path=files/wz20-m3-b2.odt
fileid=166 | storage=3 | path=files/wz20-m3-b3.odt
fileid=167 | storage=4 | path=files/wz20-m3-d1.odt
fileid=168 | storage=4 | path=files/wz20-m3-d2.odt
fileid=169 | storage=4 | path=files/wz20-m3-d3.odt
numeric_id=3 | id=home::bob
numeric_id=4 | id=home::dave
```

Wortlaut am Kopf per `grep -n` in backend/src/findling/worker/poller.py bestätigt: Z. 1454 `pass finished, claimed=%d ...`, Z. 2368 `content gateway refused one file, http status %d for file id %d`, Z. 2608-2609 `content gateway refused %d files of this pass with http status %d from %d storages, ` `taken as an outage` (gleich dem Wortlaut von 181f50a1, nur verschobene Zeilen). Warteschlange vorher leer (`SELECT file_id, locked_at, retries FROM oc_findling_queue`: keine Zeile). `<scratchpad>/mode20.sh M3 watermark_allTags=yes` (14:55:01 UTC, `occ findling:index --restart -n`, Ausgabe `state-59/mode20-M3.txt`). Backend-Log dieses Passes, wörtlich:

```
WARNING:findling.worker.poller:content gateway refused one file, http status 403 for file id 167
WARNING:findling.worker.poller:content gateway refused one file, http status 403 for file id 168
WARNING:findling.worker.poller:content gateway refused one file, http status 403 for file id 169
WARNING:findling.worker.poller:content gateway refused one file, http status 403 for file id 257
WARNING:findling.worker.poller:content gateway refused one file, http status 403 for file id 130
WARNING:findling.worker.poller:content gateway refused one file, http status 403 for file id 136
WARNING:findling.worker.poller:content gateway refused one file, http status 403 for file id 162
WARNING:findling.worker.poller:content gateway refused one file, http status 403 for file id 165
WARNING:findling.worker.poller:content gateway refused one file, http status 403 for file id 166
INFO:findling.worker.poller:pass finished, claimed=32 indexed=0 skipped=0 failed=9 unchanged=23 requeued=0 embedded=0 committed=0 slots=1 throttled=0
```

Neun Ablehnungen mit 403 aus drei Speichern (bob 3, dave 4, TF-zwanzig) in einem Pass mit 32 Zeilen (Batchgröße per `claimed=32` belegt); im ganzen Backend-Log seit dem Start dieses Modus keine Zeile `taken as an outage`, keine Zeile `indexing pass stopped`. Zugriffsprotokoll mit Zeit: alle neun 403 um 14:55:51 bis 14:55:52, der nächste Pass liest 153 um 14:55:52 und 152 um 14:55:56 (keine 900-s-Pause). Warteschlange nachher leer, also kein `locked_at` und keine erhöhten `retries`. Urteile: state.db alle neun `failed | policy_blocked | attempts=1`; Nextcloud:

```
file_id=130 | state=failed | reason=policy_blocked | updated_at=2026-11-23 14:55:52
file_id=136 | state=failed | reason=policy_blocked | updated_at=2026-11-23 14:55:52
file_id=162 | state=failed | reason=policy_blocked | updated_at=2026-11-23 14:55:52
file_id=165 | state=failed | reason=policy_blocked | updated_at=2026-11-23 14:55:52
file_id=166 | state=failed | reason=policy_blocked | updated_at=2026-11-23 14:55:52
file_id=167 | state=failed | reason=policy_blocked | updated_at=2026-11-23 14:55:52
file_id=168 | state=failed | reason=policy_blocked | updated_at=2026-11-23 14:55:52
file_id=169 | state=failed | reason=policy_blocked | updated_at=2026-11-23 14:55:52
file_id=257 | state=failed | reason=policy_blocked | updated_at=2026-11-23 14:55:52
```

Die Urteile der übrigen Dateien verfallen nicht (133, 134, 135, 137, 141 bis 143, 152, 153 je 200 und `indexed`). Gegenkontrolle aus dem Nachbau vorher (45-AUDIT.md, Befund I-45-17-01, v1.6.5): `content gateway refused 5 files of this pass with http status 500 from 2 storages, taken as an outage`, auch in Schritt 0 und Schritt A oben mit 500 echt wiederholt.

nextcloud.log (Loglevel info seit Schritt B), je Datei eine warning-Zeile, wörtlich:

```
2026-11-23T14:55:51+00:00 level=2 user=-- app=findling GET /ocs/v2.php/apps/findling/files/167?userId=dave message=Findling: reading a file was blocked by a rule data={"app":"findling","fileId":"167","asked":"1"}
2026-11-23T14:55:51+00:00 level=2 user=-- app=findling GET /ocs/v2.php/apps/findling/files/257?userId=u01 message=Findling: reading a file was blocked by a rule data={"app":"findling","fileId":"257","asked":"20"}
2026-11-23T14:55:51+00:00 level=2 user=-- app=findling GET /ocs/v2.php/apps/findling/files/130?userId=bob message=Findling: reading a file was blocked by a rule data={"app":"findling","fileId":"130","asked":"1"}
(168, 169, 136, 162, 165, 166 gleich mit "asked":"1")
```

Kopf und Status echt bis zum Backend (`<scratchpad>/gw20.sh bob '/ocs/v2.php/apps/findling/files/162?userId=bob' 1.7.0`, AppAPI-Kopf wie das Backend):

```
HTTP/1.1 403 Forbidden
X-User-Id: bob
X-Findling-Refusal: policy
Content-Type: application/json; charset=utf-8
time_total=0.070468
{"ocs":{"meta":{"status":"failure","statuscode":403,"message":""},"data":{"error":"Reading this file is blocked by a rule."}}}
```

Backend-Zeile `http status 403` (oben), Urteil `failed(policy_blocked)` in Container und Nextcloud, Admin-Seite: Einzelabfrage `ref=162` `"reason":"policy_blocked","label":"Blocked by a rule","remedy":"A rule keeps Findling from reading the file as any of the users asked, for example a watermark of Nextcloud Office that applies to the owner as well. The nightly comparison tries it again up to three times, and a change to the file tries it at once."`; Überblick-Route mit `Accept-Language: de`: `"policy_blocked","count":9,"label":"Durch eine Regel blockiert","remedy":"Eine Regel verhindert, dass Findling die Datei als einer der gefragten Nutzer liest, zum Beispiel ein Wasserzeichen von Nextcloud Office, das auch für den Besitzer gilt. ..."` mit Beispiel 257 `TF-zwanzig/wz20-tf20.odt`. Genau ein erneuter Versuch beim Besitzer: `"asked":"1"` je Datei mit Besitzer (erstes Öffnen ohne Person, ein Öffnen in actAs des Besitzers).

Zeitmessung (W6, T-45-61): TF-zwanzig (20 Mitglieder, kein Besitzer, Tag 1) `GET /files/257?userId=u01` direkt am Gateway: `HTTP/1.1 403 Forbidden`, `X-Findling-Refusal: policy`, `time_total=0.207078`, warning-Zeile mit `"asked":"20"`, Urteil policy_blocked; Gegenkontrolle die M3-Datei 136 mit Besitzer bob: `403`, `X-Findling-Refusal: policy`, `time_total=0.064591`, `"asked":"1"`.

#### M2, M4, M5 nach dem Fix

Je `<scratchpad>/mode20.sh <Modus> <schlüssel=yes>` (alle fünf Modus-Schlüssel auf no, dann der eine, `occ findling:index --restart -n`, Jobs, Warten, Messen; Ausgaben `state-59/mode20-M2.txt`, `-M4.txt`, `-M5.txt`). Loglevel info.

M2 shareAll (14:51 bis 14:54 UTC): alle Probedateien 200, Leser laut Claim der Besitzer (130, 133 bis 137, 162 bis 166 `userId=bob`; 141 bis 143, 167 bis 169 `userId=dave`), Team Folder 152, 153 `userId=alice`, 257 `userId=u01`. Je Datei die info-Zeile `Findling: read a file as a reader of it after secure view refused the first open` mit `"asked":"1"` (das erste Öffnen ohne Person lehnte die Secure View ab, das zweite in actAs gelang); keine Zeile `secure view policy` mehr in nextcloud.log (Differenz 0, das Gateway fängt die Ablehnung). state.db alle `indexed`. Treffer Besitzer und alice je 1, carol 0 außer TF-lesen.

Abweichung von der Plan-Erwartung, Entscheid INFO (45-FREIGABEN.md `Entscheid Team Folder unter shareAll 45-20`): erwartet war für Team Folder ohne Besitzer `policy_blocked`, beobachtet `indexed` über das erste Mitglied. Ursache an der Quelle: groupfolders 23.0.1 `lib/Mount/GroupFolderStorage.php` Z. 50-61, `getOwner()` gibt den Mount-Besitzer oder, ohne ihn, die aktive Person zurück; in actAs(alice) ist damit `$ownerId === $userId`, und shareAll (PermissionManager.php Z. 221) greift nicht. WebDAV-Gegenprobe unter M2, wörtlich:

```
M2 WebDAV GET als alice alice/TF-gemischt/wz59-tf2.odt -> HTTP 200
M2 WebDAV GET als alice alice/TF-lesen/wz59-tf1.odt -> HTTP 200
M2 WebDAV GET als u01 u01/TF-zwanzig/wz20-tf20.odt -> HTTP 200
M2 WebDAV GET als alice alice/wz59-offen.odt -> HTTP 403
M2 WebDAV GET als bob bob/wz59-eigen.odt -> HTTP 200
M2 WebDAV GET als carol carol/TF-lesen/wz59-tf1.odt -> HTTP 200
```

Findling liest im Team Folder also nur, was das Mitglied selbst herunterladen darf; keine Umgehung im Sinn von E2. Unter E3 (S3, shareAll) zeigt eine fremde Datei trotzdem keinen Ausschnitt (zulässige Überunterdrückung).

M4 allGroups (14:58 bis 15:00 UTC, Entscheid G1): alle Probedateien und die neuen Dateien 200, erstes Öffnen ohne Person, keine Ablehnung, alle `indexed`. allGroups greift beim Indexieren nicht (wie in 1.6.5), Mitglieder der Liste sehen nach E3 keinen Ausschnitt.

M5 shareRead (15:01 bis 15:03 UTC), wörtlich aus dem Zugriffsprotokoll und nextcloud.log:

```
      1 GET /ocs/v2.php/apps/findling/files/130?userId=bob 200      (lesende Freigabe, ebenso 133, 134, 137 bob; 141 bis 143 dave)
      1 GET /ocs/v2.php/apps/findling/files/152?userId=alice 403
      1 GET /ocs/v2.php/apps/findling/files/153?userId=alice 200
      1 GET /ocs/v2.php/apps/findling/files/257?userId=u01 403
level=2 ... files/152?userId=alice message=Findling: reading a file was blocked by a rule data={"app":"findling","fileId":"152","asked":"3"}
level=1 ... files/153?userId=alice message=Findling: read a file as a reader of it after secure view refused the first open data={"app":"findling","fileId":"153","asked":"2"}
level=2 ... files/257?userId=u01 message=Findling: reading a file was blocked by a rule data={"app":"findling","fileId":"257","asked":"20"}
```

state.db: 152 und 257 `failed | policy_blocked`, Nextcloud `file_id=152 | state=failed | reason=policy_blocked`; 153 `indexed` (gelesen über bob, schreibend in TF-gemischt: alice abgelehnt, bob gelesen, asked 2); alle übrigen `indexed`. Damit gilt die Erwartung laut Quelle für alle drei Fälle: lesende Freigabe über den Besitzer, TF-lesen ohne Besitzer und ohne schreibendes Mitglied policy_blocked (alice, bob, carol gefragt), TF-gemischt über bob.

#### asked zählt übersprungene Leser (I-45-17-07)

Datei 257 `TF-zwanzig/wz20-tf20.odt` (Team Folder 3, Gruppe tf-zwanzig mit u01 bis u20, nur lesend, Tag 1, kein Besitzer), Modus allTags. Mount-Cache vor der Probe (`php /tmp/mounts59.php 257`, `IUserMountCache::getMountsForFileId`, öffnet nichts; jede der 20 Personen hatte per PROPFIND einmal ihr Dateisystem aufgebaut), dedupliziert und alphabetisch wie `ReaderCandidates::forFile()`:

Mount-Cache TF-zwanzig: 20 Personen: u01, u02, u03, u04, u05, u06, u07, u08, u09, u10, u11, u12, u13, u14, u15, u16, u17, u18, u19, u20
Erwartung asked I-45-17-07: 20

Kein admin und keine weitere Person steht vor u01; die ersten 20 der Liste sind u01 bis u20.

u05: übersprungen, Position 5 der Liste; per erweiterter Berechtigung `occ groupfolders:permissions 3 wz20-tf20.odt --user u05 -- -read` gesperrt (Tabelle `wz20-tf20.odt | user: u05 (u05) | -read`), PROPFIND als u05 auf `TF-zwanzig/wz20-tf20.odt` antwortet `File with name /TF-zwanzig/wz20-tf20.odt could not be located`, als u06 `<oc:permissions>MG</oc:permissions>` mit 200; u05 löst die Datei also nicht lesbar auf, bleibt im Mount-Cache und wird mitgezählt.

Probe wie das Backend (`AUTH_USER` leer, also ohne angemeldete Person; `<scratchpad>/gw20.sh - '/ocs/v2.php/apps/findling/files/257?userId=u01' 1.7.0`), 15:04:31 UTC:

```
HTTP/1.1 403 Forbidden
X-Findling-Refusal: policy
time_total=0.209506
2026-11-23T15:04:31+00:00 level=2 user=-- app=findling GET /ocs/v2.php/apps/findling/files/257?userId=u01 message=Findling: reading a file was blocked by a rule data={"app":"findling","fileId":"257","asked":"20"}
```

Zahl der Secure-View-Zeilen für 257 in nextcloud.log seit 15:04:07: 0 (das Gateway fängt jede Ablehnung der Secure View und schreibt nur die warning-Zeile). admin_audit für 257 in dieser Probe:

```
2026-11-23T15:04:30+00:00 level=1 user=-- app=admin_audit GET /ocs/v2.php/apps/findling/files/257?userId=u01 message=File with id "257" accessed: "/u01/files/TF-zwanzig/wz20-tf20.odt"
2026-11-23T15:04:30+00:00 level=1 user=-- app=admin_audit GET /ocs/v2.php/apps/findling/files/257?userId=u01 message=File with id "257" accessed: "/u01/files/TF-zwanzig/wz20-tf20.odt"
```

Zwei Zeilen eines versuchten Öffnens (beide mit dem Pfad von u01, der benannten Person: das erste Öffnen außerhalb von actAs und das erneute in actAs(u01)), keine Zeile `Findling read the file ...` (die schreibt das Gateway seit dem Fix U-45-20-02 nur nach einem gelungenen Lesen). Dauer: 0,2095 s gegen 0,0613 s für die M3-Datei 136 mit Besitzer (Zeitmessung oben), also rund 0,15 s für 19 weitere Leser; die doppelte Frage an u01 kostet darüber hinaus nichts Messbares. Erste Probe verworfen: sie trug die Person im AppAPI-Kopf (AppAPI meldet sie dann an, `user=u01` im Log), nicht wie das Backend; nur die Werte des korrigierten Laufs stehen hier.

Urteil I-45-17-07: harmlos, asked zählt jeden gefragten Kandidaten einschließlich des übersprungenen u05 und der doppelt gefragten u01 (20 gleich der Erwartung aus dem Mount-Cache), kein Lesen gelang, kein Lesen wurde in der Prüfspur als gelungen eingetragen, und die Mehrdauer liegt in der Zeitmessung von T-45-61; für einen Admin heißt `asked` "gefragte Leser einschließlich übersprungener", so steht es in docs/admin-page.md.

#### files_accesscontrol, Schritt C

files_accesscontrol 6.0.1 aus dem Store (`occ app:install files_accesscontrol`), SHA-256 von StorageWrapper.php, Operation.php und CacheWrapper.php im Container gleich den Kopien vom Tag v6.0.1 (71bdddad..., bf54be47..., dca388ff...); workflowengine 3.0.0, `UserGroupMembership.php`, admin_audit `Actions/Files.php` und `OCSMiddleware.php` im Container gleich v35.0.3 (SHA-256 6a54138f..., b21af0c7..., 884d4b9a...). Systemtags `fac59` (2), `fac59-alle` (3), `fac59-bob` (4), `fac59-open` (5); Gruppen fac-alice (alice), fac-bob (bob), fac-open (alice). Regeln über die OCS-Route von workflowengine (`<scratchpad>/fac20.sh add <regel>.json`, Operation `deny`, Entität Datei). M1 aktiv. Je Fall eine eigene Datei von bob, an alice mit Download freigegeben, Messung mit `<scratchpad>/c20.sh` (Ausgaben `state-59/c-main.txt`, `c-a.txt`, `c-b.txt`). Abweichung vom Wortlaut des Plans: (a) und (b) mit eigenen Tags `fac59-alle` und `fac59-bob` statt `fac59`, damit die Regeln nebeneinander stehen können und kein Fall den anderen sperrt.

Hauptfall, Regel `fac59` UND Gruppe `is fac-alice`, Datei 320 `wz59-fac.odt`, Tag gesetzt, dann bob lädt neu hoch (Ereignis):

```
PROPFIND alice: <oc:permissions>SDN</oc:permissions> <d:status>HTTP/1.1 200 OK</d:status>
PROPFIND bob: <oc:permissions>RGDNVW</oc:permissions> <d:status>HTTP/1.1 200 OK</d:status>
GET /ocs/v2.php/apps/findling/files/320?userId=bob HTTP/1.1" 200
file_id=320 | state=indexed | reason=None | attempts=1
alice=0  bob=1  carol=0
```

alice löst die Datei ohne Leserecht auf (kein `G`), der Claim wählt bob, indexiert, keine info-Zeile `read a file as a reader of it after secure view refused` (nextcloud.log für 320 leer). Gegenkontrolle ohne Tag: `alice=1 bob=1`. Zusatz: die schon indexierte 137 (`wz59-lesen.odt`, an alice) nachträglich mit `fac59` gesperrt: `alice=0 bob=1` (die Endfilterung nimmt das fehlende Leserecht wahr), Tag wieder entfernt: `alice=1`.

(a) Regel nur Tag `fac59-alle` (sperrt alle), Datei 322: keine einzige Gateway-Anfrage für 322, Urteil `skipped(unreadable)` in state.db und `file_id=322 | state=skipped | reason=unreadable` in Nextcloud, Suche alice, bob, carol je 0; das erneute Hochladen durch bob antwortet 403 (die Regel sperrt auch das Schreiben). Nie ein Lesen als andere Person.

(b) Regel Tag `fac59-bob` UND Gruppe `is fac-bob` (nur gegen den Besitzer), Datei 323: einzige Gateway-Anfrage `23/Nov/2026:16:16:08 /ocs/v2.php/apps/findling/files/323?userId=alice 200`, kein Versuch als bob, `indexed`, Suche alice 1, bob 0 (bob gesperrt), carol 0; PROPFIND alice `SGDN`, bob `R`.

#### files_accesscontrol beim Öffnen (I-45-17-03)

Regel (Ableitung im Quellenteil oben): Operation `deny`, Bedingungen Systemtag `fac59-open` UND Benutzergruppe `!is fac-open` (nur alice in fac-open). UserGroupMembership.php v35.0.3 Z. 43-52: mit alice als aktiver Person falsch (sie ist Mitglied), ohne aktive Person wahr (`return $operator !== 'is';`). Bei der Auflösung in actAs(alice) (CacheWrapper.php Z. 38-56, `checkFileAccess(..., 0)`) greift die Regel also nicht, beim fopen ohne aktive Person (StorageWrapper.php Z. 241-253, `PERMISSION_READ`) greift sie. Datei 324 `wz59-fac-open.odt` von bob, an alice mit Download (permissions 3), vor der Regel indexiert, dann Regel angelegt, M1 aktiv.

Vorprobe PROPFIND als alice (alice löst die Datei lesbar auf, `G` = lesen), wörtlich:

```
<?xml version="1.0"?><d:multistatus xmlns:d="DAV:" xmlns:s="http://sabredav.org/ns" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns"><d:response><d:href>/remote.php/dav/files/alice/wz59-fac-open.odt</d:href><d:propstat><d:prop><oc:permissions>SGDNVW</oc:permissions></d:prop><d:status>HTTP/1.1 200 OK</d:status></d:propstat></d:response></d:multistatus>
```

Quelle des Wurfs, files_accesscontrol v6.0.1 lib/Operation.php Z. 115-118 wörtlich:

```
			$e = new \RuntimeException('Access denied for path ' . $path . ' that is ' . ($isDir ? '' : 'not ') . 'a directory and matches rules: ' . (string)json_encode($match));
			$this->logger->debug($e->getMessage(), ['exception' => $e]);
			// All Checks of one operation matched: prevent access
			throw new ForbiddenException('Access denied by access control', false);
```

Plan-Abweichung (Entscheid c2, 45-FREIGABEN.md `Entscheid Schritt C(c) 45-20`): die Erwartung "nextcloud.log zeigt die ForbiddenException mit `Access denied by access control`" war falsch. Das Gateway fängt jede andere ForbiddenException absichtlich und schreibt nur seine warning-Zeile; der Text der Ausnahme steht in nextcloud.log 0-mal (`grep -c` über die ganze Datei). Belegt wird der Wurf deshalb durch drei Zeilen: die Quellzeilen oben, die debug-Zeile von files_accesscontrol unmittelbar vor dem Wurf (Z. 116, Loglevel kurz auf debug, 16:17:54 UTC) und die warning-Zeile mit der Herkunft (Fix U-45-20-03).

Debug-Zeile der Probe (gekürzt auf 600 Zeichen), wörtlich:

```
2026-11-23T16:17:54+00:00 level=0 user=-- app=files_accesscontrol GET /ocs/v2.php/apps/findling/files/324?userId=alice message=Access denied for path  that is not a directory and matches rules: [{"id":4,"class":"OCA\\FilesAccessControl\\Operation","name":"fac59-open","checks":"[6,7]","operation":"deny","entity":"OCA\\WorkflowEngine\\Entity\\File","events":"[]","scope_type":0,"scope_actor_id":""}] | Exception=RuntimeException Message=Access denied for path  that is not a directory and matches rules: [{"id":4,"class":"OCA\\FilesAccessControl\\Operation","name":"fac59-open","checks":"[6,7]","oper
```

Probe wie das Backend nach dem Fix (`gw20.sh - '/ocs/v2.php/apps/findling/files/324?userId=alice'`, 16:33:14 UTC), wörtlich:

```
HTTP/1.1 403 Forbidden
X-Findling-Refusal: policy
time_total=0.237377
2026-11-23T16:33:14+00:00 level=2 user=-- app=findling GET /ocs/v2.php/apps/findling/files/324?userId=alice message=Findling: reading a file was blocked by a rule data={"app":"findling","fileId":"324","asked":"0","origin":"OCA\\FilesAccessControl\\Operation::checkFileAccess"}
```

Danach das echte Ereignis: alice lädt die Datei neu hoch (`204`, 16:33:27 UTC), der Claim wählt alice (bob ist bei der Auflösung in actAs(bob) gesperrt, weil bob nicht in fac-open ist):

```
GET /ocs/v2.php/apps/findling/files/324?userId=alice HTTP/1.1" 403
2026-11-23T16:33:42+00:00 level=2 user=-- app=findling GET /ocs/v2.php/apps/findling/files/324?userId=alice message=Findling: reading a file was blocked by a rule data={"app":"findling","fileId":"324","asked":"0","origin":"OCA\\FilesAccessControl\\Operation::checkFileAccess"}
WARNING:findling.worker.poller:content gateway refused one file, http status 403 for file id 324
file_id=324 | state=failed | reason=policy_blocked | attempts=1
file_id=324 | state=failed | reason=policy_blocked
```

Genau ein Öffnen, außerhalb von actAs ohne aktive Person, `asked` 0, kein erneutes Öffnen in actAs(bob), kein anderer Leser, keine info-Zeile `read a file as a reader of it after secure view refused`; Antwort 403 mit `X-Findling-Refusal: policy` (fail-closed); Urteil `failed(policy_blocked)` in Container und Nextcloud. Die Unit-Tests `testTheRightFrameWithAnotherMessageIsPolicyWithoutAnotherOpen`, `testARefusalOfAccessControlIsPolicyWithoutAnotherOpen` (GatewayReaderTest) und `testAnotherForbiddenExceptionAtTheFirstOpenIsA403PolicyWithoutAnotherOpen` (GatewayControllerTest) prüfen dasselbe ohne Instanz.

Gegenkontrolle ohne Regel: HTTP/1.1 200 OK (Regel 4 gelöscht, `gw20.sh` auf 324 mit `userId=alice`, `time_total=0.071463`)

#### E1 Prüfspur, Schritt D

admin_audit aktiv (seit Schritt B). Proben wie das Backend unter shareAll nach dem Fix U-45-20-02 (Kopf 1d191e7e, 16:05 UTC), audit.log wörtlich (`state-59/D-audit.txt`):

```
2026-11-23T16:05:00+00:00 level=1 user=-- app=admin_audit GET /ocs/v2.php/apps/findling/files/133?userId=bob message=File with id "133" accessed: "/bob/files/wz59-b2.pdf"
2026-11-23T16:05:00+00:00 level=1 user=-- app=admin_audit GET /ocs/v2.php/apps/findling/files/133?userId=bob message=File with id "133" accessed: "/bob/files/wz59-b2.pdf"
2026-11-23T16:05:00+00:00 level=1 user=-- app=admin_audit GET /ocs/v2.php/apps/findling/files/133?userId=bob message=Findling read the file with id "133" at "/bob/files/wz59-b2.pdf" as the user "bob" after the secure view of Nextcloud Office refused it without a user
2026-11-23T16:05:01+00:00 level=1 user=-- app=admin_audit GET /ocs/v2.php/apps/findling/files/58?userId=admin message=File with id "58" accessed: "/admin/files/Nextcloud.png"
2026-11-23T16:05:01+00:00 level=1 user=-- app=admin_audit GET /ocs/v2.php/apps/findling/files/152?userId=alice message=File with id "152" accessed: "/alice/files/TF-lesen/wz59-tf1.odt"
2026-11-23T16:05:01+00:00 level=1 user=-- app=admin_audit GET /ocs/v2.php/apps/findling/files/152?userId=alice message=File with id "152" accessed: "/alice/files/TF-lesen/wz59-tf1.odt"
2026-11-23T16:05:01+00:00 level=1 user=-- app=admin_audit GET /ocs/v2.php/apps/findling/files/152?userId=alice message=Findling read the file with id "152" at "/alice/files/TF-lesen/wz59-tf1.odt" as the user "alice" after the secure view of Nextcloud Office refused it without a user
```

nextcloud.log dazu: `... files/133?userId=bob message=Findling: read a file as a reader of it after secure view refused the first open data={"app":"findling","fileId":"133","asked":"1","reader":"bob"}` und dieselbe Zeile für 152 mit `"reader":"alice"`. Die M2-Datei von bob (133): die lesende Person bob steht in der Zeile von Findling; die gewöhnliche Datei 58 (PNG, kein Typ von richdocuments, erstes Öffnen ohne Person gelingt): eine Zeile von admin_audit wie in 1.6.5 (derselbe Weg wie vorher, `user=--`), keine Findling-Zeile. Vor dem Fix (Kopf 151dca7b, 15:04:49 UTC) standen für 133 nur die zwei `accessed`-Zeilen mit `user=--`: Befund U-45-20-02.

#### E3 Ausschnitte unter M1 (45-22)

M1 (nur shareDisabledDownload), Rückfall auf S3. Neue Dateien: 318 `wz59-e3-dl.odt` von bob an alice mit Download (`id=9 | permissions=1 | attributes=NULL`), 319 `TF-gemischt/wz59-e3-tf.odt` (von bob hochgeladen, alice ist Mitglied über gm-lesen, keine Freigabe). Proben über OCS (`<scratchpad>/e320.sh`, Ausgabe `state-59/e3-M1.txt` und `e3-aus.txt`), wörtlich:

OCS alice Wasserzeichenprobe59a: {"ocs":{"meta":{"status":"ok","statuscode":200,"message":"OK"},"data":{"name":"File contents","isPaginated":false,"entries":[{"thumbnailUrl":"","title":"wz59-b1.odt","subline":"wz59-b1.odt","resourceUrl":"\/f\/130","icon":"icon-search","rounded":false,"attributes":{"fileId":"130"}}],"cursor":null}}}
OCS alice Ausschnittprobe20a: {"ocs":{"meta":{"status":"ok","statuscode":200,"message":"OK"},"data":{"name":"File contents","isPaginated":false,"entries":[{"thumbnailUrl":"","title":"wz59-e3-dl.odt","subline":"wz59-e3-dl.odt","resourceUrl":"\/f\/318","icon":"icon-search","rounded":false,"attributes":{"fileId":"318"}}],"cursor":null}}}
OCS alice Ausschnittprobe20b: {"ocs":{"meta":{"status":"ok","statuscode":200,"message":"OK"},"data":{"name":"File contents","isPaginated":false,"entries":[{"thumbnailUrl":"","title":"wz59-e3-tf.odt","subline":"TF-gemischt\/wz59-e3-tf.odt","resourceUrl":"\/f\/319","icon":"icon-search","rounded":false,"attributes":{"fileId":"319"}}],"cursor":null}}}
OCS bob Wasserzeichenprobe59a: {"ocs":{"meta":{"status":"ok","statuscode":200,"message":"OK"},"data":{"name":"File contents","isPaginated":false,"entries":[{"thumbnailUrl":"","title":"wz59-b1.odt","subline":"Wasserzeichenprobe59a Dieser Text ist lang genug, damit er ohne OCR als Klartext gelesen","resourceUrl":"\/f\/130","icon":"icon-search","rounded":false,"attributes":{"fileId":"130","highlights":"[[0,21]]"}}],"cursor":null}}}
OCS bob Ausschnittprobe20a: {"ocs":{"meta":{"status":"ok","statuscode":200,"message":"OK"},"data":{"name":"File contents","isPaginated":false,"entries":[{"thumbnailUrl":"","title":"wz59-e3-dl.odt","subline":"Ausschnittprobe20a Dieser Text ist lang genug, damit er ohne OCR als Klartext gelesen","resourceUrl":"\/f\/318","icon":"icon-search","rounded":false,"attributes":{"fileId":"318","highlights":"[[0,18]]"}}],"cursor":null}}}
OCS alice Ausschnittprobe20a (Wasserzeichen aus): {"ocs":{"meta":{"status":"ok","statuscode":200,"message":"OK"},"data":{"name":"File contents","isPaginated":false,"entries":[{"thumbnailUrl":"","title":"wz59-e3-dl.odt","subline":"Ausschnittprobe20a Dieser Text ist lang genug, damit er ohne OCR als Klartext gelesen","resourceUrl":"\/f\/318","icon":"icon-search","rounded":false,"attributes":{"fileId":"318","highlights":"[[0,18]]"}}],"cursor":null}}}

E3 alice Freigabe ohne Download: Ausschnitt keiner
E3 alice Freigabe mit Download: Ausschnitt keiner
E3 alice Team Folder: Ausschnitt keiner
E3 bob Besitzer: Ausschnitt ja
E3 Positivkontrolle alice Freigabe mit Download: Wasserzeichen aus, Ausschnitt ja

Die zweite und dritte Zeile sind die von E3 zugelassene Überunterdrückung, kein Befund. Danach Endkonfiguration M1 wiederhergestellt.

#### Altbestand (I-45-17-02)

Datei 130 (`Wasserzeichenprobe59a`, bob, an alice ohne Download), indexiert vor dem Wasserzeichen-Modus allTags, dann unter allTags (Tag 1) mit `mode20.sh M3b watermark_allTags=yes` neu geurteilt: state.db `file_id=130 | state=failed | reason=policy_blocked | attempts=1`; der früher indexierte Inhalt bleibt im Index. Suche 15 s nach dem Umstellen (`state-59/altbestand2.txt`), wörtlich:

OCS alice Wasserzeichenprobe59a: {"ocs":{"meta":{"status":"ok","statuscode":200,"message":"OK"},"data":{"name":"File contents","isPaginated":false,"entries":[{"thumbnailUrl":"","title":"wz59-b1.odt","subline":"wz59-b1.odt","resourceUrl":"\/f\/130","icon":"icon-search","rounded":false,"attributes":{"fileId":"130"}}],"cursor":null}}}
OCS bob Wasserzeichenprobe59a: {"ocs":{"meta":{"status":"ok","statuscode":200,"message":"OK"},"data":{"name":"File contents","isPaginated":false,"entries":[{"thumbnailUrl":"","title":"wz59-b1.odt","subline":"Ablage\/wz59-b1.odt","resourceUrl":"\/f\/130","icon":"icon-search","rounded":false,"attributes":{"fileId":"130"}}],"cursor":null}}}

alice findet die Datei über den alten Inhalt, ohne Ausschnitt (subline ist ihr Pfad), wie `Entscheid Altbestand 45-22` (A1) es festlegt; bob ebenso ohne Ausschnitt (allTags trifft auch den Besitzer).

Messhinweis: eine erste Altbestand-Abfrage an 152 unter shareRead kam 1 bis 2 s nach `occ config:app:set` und zeigte noch einen Ausschnitt. Gemessen (Schleife 16:07:35 bis 16:09:50 UTC, alle 10 s): eine per CLI geänderte Einstellung wirkt im Webserver nach höchstens etwa 10 s, weil der Webserver die App-Konfiguration in seinem eigenen APCu hält; richdocuments liest dieselben Werte im selben Prozess. Kein Befund; alle Abfragen oben laufen mit mindestens 15 s Abstand zur letzten Umstellung.

Ergebnis Altbestand: Entscheid A1, Treffer ja, Ausschnitt keiner

#### Befunde dieser Gegenprobe

| ID | Schwere | Befund | Entscheid und Stand |
|---|---|---|---|
| U-45-20-01 | MEDIUM | Erneuerung `refusal_streaks_1_7_0` lief vor einer Begleit-App der Generation 3 und wurde dort verbraucht (Abschnitt oben) | Owner f1, behoben aec5edcf/151dca7b, Schritt A und B neu gefahren |
| U-45-20-02 | MEDIUM | admin_audit nennt für ein Lesen in actAs die lesende Person nicht (`user=--`, `\OC_User::getUser()` liest die Sitzung, actAs setzt nur die flüchtige Person); Text 4 ("audit logs name that user for such a read") wäre unwahr gewesen | Owner a4, behoben f3290689/1d191e7e: `CriticalActionPerformedEvent` nur nach einem Lesen in actAs (id, Pfad, uid, nie Inhalt), info-Zeile mit `reader`; RED 2 Errors und 1 Failure, Mutationen (kein Event, falsche Person, Event außerhalb actAs, info ohne Person) rot, live belegt (E1 oben) |
| U-45-20-03 | LOW | Die warning-Zeile einer anderen ForbiddenException nannte keine Herkunft; ein Admin sah nicht, welche Regel ablehnte | Entscheid c2, behoben 3550b2b3/c9dc3270: `origin` = Klasse::Funktion des ersten Frames, nie Meldung, Pfad oder Argumente; RED 5 Failures, Mutationen (Herkunft fehlt, Meldung geloggt, Argument geloggt) rot, live belegt |
| I-45-20-04 | INFO | Team Folder unter shareAll: indexiert über das Mitglied statt policy_blocked (groupfolders `getOwner()`), Mitglied darf selbst herunterladen | Entscheid INFO, Doku in docs/privacy.md |
| I-45-20-05 | INFO | Zwei Erwartungen des Plans an Logformate trafen nicht zu: die Literalzeile `Access denied by access control` (siehe oben) und `"asked":20` (nextcloud.log schreibt Kontextwerte als Zeichenkette, `"asked":"20"`); verify prüft die Zahl jetzt mit optionalen Anführungszeichen | dokumentiert, keine Codeänderung |

Keine LOW-Befunde offen für R-45-21.

Abschluss: Backend beendet (heartbeat 000), `docker compose -f compose-59b.yaml -p findling-59 down -v` (`Volume findling-59-html Removed`), `git worktree remove <scratchpad>/wt-165` (Registrierung entfernt; der Ordner scheiterte an zu langen Pfaden der venv und wurde per PowerShell mit `\\?\`-Pfad gelöscht), Logs vorher nach `state-59/nextcloud-ende.log` und `audit-ende.log` gesichert.

### Modus x Leser -> Ergebnis nachher

Spalten wie vorher: Datei (ID), Leser laut Claim (`userId` der Gateway-URL), Antwort des Gateways, Urteil in state.db (Nextcloud-Seite, soweit geschrieben), Treffer Besitzer/alice/carol. Stand 1.7.0 am Kopf (Begleit-App und Backend), echter Update-Weg aus 1.6.5.

| Modus und Fall | Datei | Leser laut Claim | Antwort | Urteil | Treffer B/a/c |
|---|---|---|---|---|---|
| M1 shareDisabledDownload, Freigabe ohne Download | 130, 133, 134 (bob), 141, 142, 143 (dave) | Besitzer bob bzw. dave | 200, ein Öffnen ohne Person | indexed, über den Abgleich ohne --restart | 1/1/0, alice ohne Ausschnitt |
| M1 Positivkontrolle mit Download | 135 | bob | 200 | indexed | 1/1/0 |
| M1 eigene Datei ohne Freigabe | 136 | bob | 200 | indexed | 1/0/0 |
| M1 lesende Freigabe mit Download | 137 | bob | 200 | indexed | 1/1/0 |
| M1 Team Folder | 152, 153 | alice | 200 | indexed | 152: 1/1/1, 153: 1/1/0 |
| M2 shareAll, Dateien mit Besitzer | 130 bis 137, 141 bis 143, 162 bis 169 | Besitzer | 200 nach Ablehnung des ersten Öffnens, asked 1 | indexed | 1/1/0 (alice ohne Ausschnitt) |
| M2 Team Folder (INFO I-45-20-04) | 152, 153, 257 | alice bzw. u01 | 200 nach Ablehnung, asked 1 (Mitglied als Besitzer laut groupfolders) | indexed | 152: 1/1/1, 153: 1/1/0 |
| M3 allTags, getaggt mit Besitzer | 130, 136, 162, 165, 166 (bob), 167, 168, 169 (dave) | Besitzer | 403, X-Findling-Refusal: policy, asked 1 | failed(policy_blocked) in Container und Nextcloud | 130: 1/1/0 (Altbestand A1, ohne Ausschnitt) |
| M3 getaggt im Team Folder ohne Besitzer | 257 | u01 | 403 policy, asked 20 | failed(policy_blocked) | entfällt |
| M3 ohne Tag (Gegenkontrolle) | 133, 134, 135, 137, 141 bis 143, 152, 153 | Besitzer bzw. alice | 200 | indexed | wie M1 |
| M4 allGroups (G1) | alle Probedateien und die neuen | Besitzer bzw. alice, u01 | 200 ohne Ablehnung | indexed | wie M1 |
| M5 shareRead, lesende Freigabe | 130, 133, 134, 137 (bob), 141 bis 143 (dave) | Besitzer | 200 | indexed | 1/1/0 |
| M5 Team Folder nur lesend für alle (TF-lesen) | 152 | alice | 403 policy, asked 3 | failed(policy_blocked) in Container und Nextcloud | 1/1/1 (Altbestand, ohne Ausschnitt) |
| M5 Team Folder mit schreibendem Mitglied (TF-gemischt) | 153 | alice, gelesen als bob | 200 nach Ablehnung, asked 2 | indexed | 1/1/0 |

carol findet in keinem Modus eine Datei außer TF-lesen, in dem sie Mitglied ist. Erst mit diesen fünf Modi und ihren Fällen sagt dieses Audit "alle Modi".

### Live-Proben #25

Plan 45-20 Task 2, 2026-11-23 ab 16:44 UTC, Repo-Kopf aca91fac (Code wie c9dc3270). Frische Instanz findling-25 (`<scratchpad>/compose-25.yaml`, Nextcloud 35.0.3, Port 8092, Volumes findling-25-html und findling-25-data), Begleit-App per Bind-Mount von php/ des Hauptarbeitsbaums, Backend als Container aus dem Image am Kopf (Owner-Entscheid t1: `docker buildx build --load -t findling-backend:45-20-head --build-context scripts=./scripts ./backend`, exit 0, Image fb8f3a3e5f55, 1,13 GB; vorher `test -z "$(docker ps -q)"` leer, findling-59 entfernt, 4,7 GB RAM frei, Docker-VM 6,2 GB), registriert per `<scratchpad>/reg25c.sh` (Kopie von scripts/dev/register-exapp.sh, Backend-Start durch das Compose-Profil ersetzt; Secret nur in `state-25/backend.env`). files_external aktiv, externer Speicher `/Ext1` vom Typ "Local" auf `<scratchpad>/state-25/ext1` (Mount-ID 1, Speicher 3), dort 50 000 kleine Textdateien unter `viele/` (`gen25txt.py`, `occ files:scan --path=/admin/files/Ext1`: 50 000 Dateien in 59 s), der Ordner `viele` per Regel ausgeschlossen (Präfix relativ zur Wurzel des Mounts, docs/admin-page.md), damit die Nachzählung sie zählt, der Abgleich sie aber nicht als Arbeit sieht. `occ background:cron`; Cron als Schleife auf dem Host, `docker exec -u www-data findling-25 php -f /var/www/html/cron.php` alle 60 s (ab 18:36 alle 300 s, Abschnitt F1 (b)), Läufe in `state-25/cron.log`.

```
$ occ app:list
  - app_api: 35.0.0
  - files_external: 2.0.0
  - findling: 1.7.0
$ occ config:system:get memcache.locking     -> (leer)
$ occ config:system:get filelocking.enabled  -> (leer, Standard an)
$ occ config:system:get memcache.local       -> \OC\Memcache\APCu
$ php /tmp/hold20.php ...                     -> provider OC\Lock\DBLockingProvider
```

Locking-Provider: `OC\Lock\DBLockingProvider` (kein `memcache.locking`, Dateisperren an), also sehen Halte-Skript (CLI) und Webserver bzw. Cron dieselben Sperren; kein Umstellen nötig. `memcache.local` APCu betrifft nur den lokalen Cache.

Verkürzt per Umgebung: FINDLING_RECONCILE_MIN_INTERVAL_HOURS=1 (Standard 24), FINDLING_RECONCILE_HOUR=<aktuelle UTC-Stunde des Containers, bei jedem Neustart nachgezogen> (Standard 3)

#### F1 Nachzählung hält den Abgleich nicht auf

Quellen am Kopf per `grep -n` bestätigt: backend/src/findling/worker/reconcile.py Z. 1158 `reconcile stands down, the crawl is unfinished`, Z. 1162 `reconcile stands down, %d rows are scheduled and the quiet mark is %d`, Z. 569 `reconcile walks although the quiet mark holds, held for %d hours, %d rows are scheduled and the quiet mark is %d`; php/lib/BackgroundJobs/ScanRecountJob.php Z. 135 `Findling: started a recount of the coverage denominator`; StorageCrawlJob.php Z. 104 `LOCK_NAME = 'findling/crawl-slice'`, Z. 129 `CRAWL_ACTIVE_LOCK = 'findling/crawl-active'`; CrawlAdvanceService.php `crawling()` liest nur den Marker und Crawl-Zeilen, keine recount-Zeile. Entscheid r1 (`Entscheid Regeln Nachzählung 45-23`): Auslöser ist je ein Speichern der Regeln über die Admin-Route (`<scratchpad>/rules25.sh <maxFileBytes>`: alle Felder mit ihren Werten, `exclusions ["viele"]`, `indexExternalStorage true`, `indexTeamFolders true`, keine Muster, `excludedExternalMounts` fehlt). Der Cap liegt an der Decke `maxFileBytesCeiling` 52428800; gewechselt wird zwischen A = 52428800 und B = 41943040, beide über jeder Datei der Probe.

(a) Nachgestellte recount-Scheibe (`<scratchpad>/f1a.sh`, Ausgabe `state-25/f1a.txt`). Der letzte fertige Zyklus (Nachholzyklus nach dem ersten Crawl) endete um 17:17:36, der Abgleich war ab 18:17:36 mit Stunde 18 fällig.

```
== F1 (a) 2026-11-23T18:17:49Z
-- Regeln: maxFileBytes 52428800 -> 41943040 um 18:17:49
"saved":true
"maxFileBytes":41943040
-- Halte-Skript startet 18:17:51
provider OC\Lock\DBLockingProvider
2026-11-23 18:17:52 acquired findling/crawl-slice
-- occ background-job:execute --force-execute 155372602947686400 um 18:17:55
-- recount-Zeilen 18:17:55: n=2
(alle 10 s bis 18:23:15: n=2)
2026-11-23 18:23:22 released findling/crawl-slice
recount-Zeilen 18:23:36: n=0
```

nextcloud.log: `18:17:55 Findling: started a recount of the coverage denominator {"mounts":"2"}`, `18:23:33 Findling: recounted a mount {"storage_id":"2","files_seen":"109"}`, `18:23:33 ... {"storage_id":"3","files_seen":"50000"}`. Das Backend wurde mit `FINDLING_RECONCILE_HOUR=18` um 18:18:26 neu angelegt (der erste Versuch aus dem Skript um 18:17:56 scheiterte an einem Pfad des Compose-Aufrufs und legte nichts neu an, der Container lief mit Stunde 16 weiter; von Hand wiederholt), sein erster Tick fiel in das Fenster. Backend-Log von 18:17:52 bis 18:23:22, alle reconcile-Zeilen, wörtlich:

```
2026-11-23T18:20:14.680463376Z INFO:findling.worker.reconcile:reconcile round walked, mounts=2 slices=102 seen=50109 stale=0 missing=0 given_up=0
```

Keine Zeile `reconcile stands down, the crawl is unfinished` in diesem Fenster; die Runde lief über beide Mounts, während die recount-Scheiben vor dem gehaltenen Slice-Lock warteten (die Kette überlebt, StorageCrawlJob.php Z. 256-268).

Lock per Skript gehalten: findling/crawl-slice, 2026-11-23 18:17:52, 2026-11-23 18:23:22, recount-Zeilen 2

Gegenkontrolle (`<scratchpad>/f1gegen.sh f1-gegen`, der Marker über einen Tick), wörtlich:

```
provider OC\Lock\DBLockingProvider
2026-11-23 18:24:23 acquired findling/crawl-active
2026-11-23 18:29:54 released findling/crawl-active
-- Backend-Zeilen seit 2026-11-23T18:24:23Z
2026-11-23T18:25:14.718167383Z INFO:findling.worker.reconcile:reconcile stands down, the crawl is unfinished
```

Gegenkontrolle F1: 2026-11-23T18:25:14.718167383Z INFO:findling.worker.reconcile:reconcile stands down, the crawl is unfinished

(b) Echte Nachzählung. Erster Lauf mit Cron alle 60 s: Auslöser 41943040 -> 52428800 um 18:30:06 (nach dem Ende der Runde aus (a) um 18:23:36 und nach der Gegenkontrolle bis 18:29:54); ScanRecountJob lief im Cron um 18:33:39 (`started a recount ... {"mounts":"2"}`), beide Scheiben im nächsten Lauf um 18:34:40 (`recounted a mount ... "files_seen":"109"` und `"files_seen":"50000"`); in diesen 61 s lag kein Tick des Abgleichs (Ticks 18:30:14, 18:35:14), die Runde belegt also nichts über einen Tick. Die Nachzählung von 50 000 Einträgen dauert keine Sekunde je Scheibe (Budget 30 s, StorageCrawlJob.php Z. 69), mehr Scheiben je Mount gäbe es erst ab Millionen Dateien. Deshalb ein zweiter Lauf mit dem Cron-Takt, den Nextcloud empfiehlt (alle 5 Minuten, ab 18:36:04): die Kette eines Mounts liegt dann vom Planen bis zur Scheibe einen Cron-Lauf lang in `oc_jobs`, wie auf einer Instanz mit langer Nachzählung.

Zweiter Lauf (`<scratchpad>/rc25.sh f1b2 80`, Ausgabe `state-25/f1b2.txt`), Auslöser 52428800 -> 41943040 um 18:37:35:

```
2026-11-23T18:52:22+00:00 level=1 user=-- app=findling  -- message=Findling: started a recount of the coverage denominator data={"app":"findling","mounts":"2"}
18:52:35 recount-Zeilen 2
(alle 20 s bis 18:57:xx: 2)
2026-11-23T18:57:23+00:00 level=1 user=-- app=findling  -- message=Findling: recounted a mount data={"app":"findling","storage_id":"2","files_seen":"109"}
2026-11-23T18:57:24+00:00 level=1 user=-- app=findling  -- message=Findling: recounted a mount data={"app":"findling","storage_id":"3","files_seen":"50000"}
-- Backend-Zeilen seit 2026-11-23T18:37:41Z
(keine reconcile-Zeile)
```

Der Tick des Abgleichs in der Runde ist im Zugriffsprotokoll belegt (`[23/Nov/2026:18:55:15 +0000] "GET /ocs/v2.php/apps/findling/queues/documents/stats`, die Abfrage, auf der `_gate` die Crawl-Frage stellt). Er schrieb keine Zeile `reconcile stands down, the crawl is unfinished`; da der Abgleich in diesem Tick nicht fällig war (Zyklus 18:20, Stunde 18), lief kein Gang, und ohne Sperre schreibt ein nicht fälliger Tick keine Zeile.

Nachzählung echt: 2026-11-23T18:52:22, 2026-11-23T18:57:24, 1 Tick (18:55:15), Aussetzer wegen Crawl 0, Start nach Ende der Runde aus (a) 18:23:36 und nach der Gegenkontrolle 18:29:54, ausgelöst durch maxFileBytes 52428800 -> 41943040 um 18:37:35

(c) Mindestabstand (`<scratchpad>/f1c.sh`, Ausgabe `state-25/f1c.txt`), direkt nach der Runde:

```
== F1 (c) 2026-11-23T18:58:10
-- Upload Marke: 201 um 18:58:11
-- force-execute ScanRecountJob 155372602947686400 um 18:58:16
recount-Zeilen 18:58:20: n=0
-- nextcloud.log recount seit 2026-11-23T18:58:10
(keine Zeile)
-- Regeln: maxFileBytes 41943040 -> 52428800 um 18:58:20
"saved":true
-- force-execute ScanRecountJob 155372602947686400 um 18:58:24
recount-Zeilen 18:58:27: n=2
2026-11-23T18:58:24+00:00 level=1 user=-- app=findling  -- message=Findling: started a recount of the coverage denominator data={"app":"findling","mounts":"2"}
```

Mindestabstand: nach einer Datei (Ereignis) 6 Minuten nach dem Start der letzten Runde keine neue Runde (keine Logzeile, keine recount-Zeile); nach gespeicherten Regeln (r1) startet die Runde sofort, wie entschieden.

Auslöser F1: r1, maxFileBytes 52428800 -> 41943040 vor (a) um 18:17:49, 41943040 -> 52428800 vor dem ersten Lauf von (b) um 18:30:06, 52428800 -> 41943040 vor (b) um 18:37:35, 41943040 -> 52428800 in (c) um 18:58:20

Ergebnis F1: bestanden, eine gehaltene recount-Scheibe hält den fälligen Gang nicht auf (Runde 18:20:14 ohne Aussetzen), der gehaltene Marker setzt aus (Gegenkontrolle), eine echte Nachzählung mit dem empfohlenen Cron-Takt schreibt in ihrem Tick keine Aussetz-Zeile, und der Mindestabstand von 6 h gilt für Ereignisse, nicht für gespeicherte Regeln.

#### F2 Rückhalt bei langer Warteschlange

Verkürzt per Umgebung: FINDLING_RECONCILE_MIN_INTERVAL_HOURS=1 (Standard 24, Rückhalt also nach 2 h statt 48 h), FINDLING_RECONCILE_QUIET_MAX=20 (Standard 100), FINDLING_RECONCILE_HOUR=19 (Standard 3), fällig gemacht zu Beginn von F2 (letzter Zyklus 2026-11-23 18:20:14 UTC, FINDLING_RECONCILE_HOUR=19); Cron alle 60 s

Ablauf: 19:20:31 UTC Backend mit `FINDLING_RECONCILE_HOUR=19 FINDLING_RECONCILE_QUIET_MAX=20` neu angelegt (`<scratchpad>/be25.sh`), `occ findling:index --restart -n`. Rückstand: 9000 gescannte Seiten (`gen25img.py`, je eine A4-Seite 1240 x 1754 Pixel mit 40 Textzeilen und Rauschen, PNG, rund 180 kB) nach `ext1/scans`, per `occ files:scan --path=/admin/files/Ext1/scans` (9000 Dateien in 10 s) in den Dateicache; der Crawl brachte sie in die Warteschlange (Crawl-Gate bis 19:45:38: `reconcile stands down, the crawl is unfinished`). Beobachtung je 60 s (`<scratchpad>/f2watch.sh`, Ausgabe `state-25/f2watch.log`: scheduled, handed, `reconcile_quiet_held_since` per `meta.py` im Backend-Container, `/app/.venv/bin/python -I /tmp/meta.py /data/state.db`, Verbindung `file:...?mode=ro`, nur SELECT; im Container statt per `uv run` auf dem Host, weil state.db im Volume des Containers liegt). Die OCR läuft im Container (Tesseract aus dem Image), die Vormessung mit 60 Seiten vorab ergab rund 34 Seiten je Minute.

Erster fälliger Tick über der Ruhemarke, wörtlich:

```
2026-11-23T19:50:38.669129247Z INFO:findling.worker.reconcile:reconcile stands down, 8822 rows are scheduled and the quiet mark is 20
```

```
2026-11-23T19:50:24Z scheduled=8830 handed=4 reconcile_quiet_held_since=
2026-11-23T19:51:27Z scheduled=8798 handed=4 reconcile_quiet_held_since=1795463438 (2026-11-23 19:50:38 UTC)
2026-11-23T20:00:39Z scheduled=8504 handed=4 reconcile_quiet_held_since=1795463438 (2026-11-23 19:50:38 UTC)
```

Zeitpunkt gesetzt: 1795463438 (2026-11-23 19:50:38 UTC)

Rückstand: 9000 Dateien, Abbaurate 31,8 je Minute (8830 um 19:50:24, 8504 um 20:00:39), reicht rechnerisch bis 2026-11-24 00:27 UTC, gebraucht bis 2026-11-23 21:53 UTC (Zeitpunkt plus zwei Intervalle plus ein Zyklus von rund 2 Minuten, gemessen in F1 18:18:26 bis 18:20:14)

Die Status-Route vor einem Intervall (19:53 UTC, `GET /apps/findling/admin/overview` als admin): `"reconcileHeldSince":null`.

Während des Wartens (`<scratchpad>/f2neu.sh`, Ausgabe `state-25/f2neu.txt`), wörtlich:

```
-- occ files_external:create /Ext2 local null::null -c datadir=/srv/ext2
Storage created with id 2
-- occ files:scan --path=/admin/files/Ext2 um 19:52:07
numeric_id=4 | id=local::/srv/ext2/
fileid=59194 | storage=4 | path=neu1.txt
fileid=59195 | storage=4 | path=neu2.txt
fileid=59196 | storage=4 | path=neu3.txt
-- Warteschlange direkt nach dem Scan für 59194,59195,59196: n=0
-- occ files:scan --path=/admin/files/Ext1 um 19:52:09
fileid=59197 | storage=3 | path=ohne-ereignis.txt
-- Warteschlange direkt nach dem Scan für 59197: n=0
```

Der Scan trägt die Dateien ohne Ereignis in den Dateicache ein (docs/reconcile.md Z. 21), die Warteschlange hat für keine von ihnen eine Zeile.

Ein Intervall nach dem Zeitpunkt (Status-Route als admin alle 5 s ab 20:50:30, `GET /apps/findling/admin/overview`), wörtlich:

```
20:50:36 "reconcileHeldSince":null
20:50:42 "reconcileHeldSince":1795463438
```

Hinweis nach einem Intervall: 2026-11-23 20:50:42 UTC, Abstand zum Zeitpunkt 3604 s

Admin-Seite (Playwright, Chromium, angemeldet als admin mit Sprache de, `<scratchpad>/pw/shot25.js`, 20:51:34 UTC; der Einführungsdialog von Nextcloud verdeckte das erste Bild und wurde mit `occ app:disable firstrunwizard` abgeschaltet), Bild `<scratchpad>/state-25/f2-hinweis-de.png`, der Satz wörtlich:

"Eine lange Warteschlange hält den Abgleichlauf schon länger als sein Intervall auf. Er läuft trotzdem, sobald er doppelt so lange gewartet hat, und dieser Hinweis bleibt, bis er alle Dateien durchgesehen hat; bis dahin können Dateien in der Suche fehlen, die nur er findet, zum Beispiel neue Dateien auf externen Speichern."

Die Ticks bis zur Schwelle schreiben je die info-Zeile der Ruhemarke, etwa `2026-11-23T20:50:39.256264652Z INFO:findling.worker.reconcile:reconcile stands down, 6882 rows are scheduled and the quiet mark is 20`.

An der Schwelle (Zeitpunkt plus zwei Intervalle, 21:50:38 UTC) zuerst die Gegenkontrolle (`<scratchpad>/f1gegen.sh f2-gegen`, der Marker über den Tick), wörtlich:

```
provider OC\Lock\DBLockingProvider
2026-11-23 21:48:01 acquired findling/crawl-active
2026-11-23 21:53:31 released findling/crawl-active
-- Backend-Zeilen seit 2026-11-23T21:48:01Z
2026-11-23T21:50:39.800012985Z INFO:findling.worker.reconcile:reconcile stands down, the crawl is unfinished
```

Gegenkontrolle F2: 2026-11-23T21:50:39.800012985Z INFO:findling.worker.reconcile:reconcile stands down, the crawl is unfinished

In diesem Tick keine warning-Zeile. Nach dem Freigeben, im nächsten Tick, wörtlich:

```
2026-11-23T21:55:39.849573325Z WARNING:findling.worker.reconcile:reconcile walks although the quiet mark holds, held for 2 hours, 4800 rows are scheduled and the quiet mark is 20
2026-11-23T21:57:48.999819491Z INFO:findling.worker.reconcile:reconcile round walked, mounts=3 slices=119 seen=58114 stale=4 missing=0 given_up=0
```

Rückhalt nach zwei Intervallen: 2026-11-23 21:55:39 UTC, Abstand zum Zeitpunkt 7501 s

Der Zyklus lief über alle drei Mounts (Home von admin, Ext1, Ext2) und übergab genau die vier neuen Dateien (`stale=4`), die Warteschlange stand dabei noch bei 4800 Zeilen. Danach, wörtlich:

```
file_id=59194 | kind=content | locked_at=2026-11-23 21:57:49
(59195, 59196, 59197 gleich, direkt beansprucht)
file_id=59194 | storage_id=4 | path=Ext2/neu1.txt | state=indexed | reason=None
file_id=59195 | storage_id=4 | path=Ext2/neu2.txt | state=indexed | reason=None
file_id=59196 | storage_id=4 | path=Ext2/neu3.txt | state=indexed | reason=None
file_id=59197 | storage_id=3 | path=Ext1/ohne-ereignis.txt | state=indexed | reason=None
-- oc_findling_file_state: keine Zeile (indexiert)
Neuspeicherprobe1 admin=1
Neuspeicherprobe2 admin=1
Neuspeicherprobe3 admin=1
Ohneereignisprobe admin=1
```

Neuer externer Speicher: 4, neu1.txt, neu2.txt, neu3.txt (59194, 59195, 59196), Warteschlange nach dem Scan 0, indexed

Datei ohne Ereignis: 59197, Warteschlange nach dem Scan 0, indexed

Nach dem Zyklus (21:57:53 UTC): Status-Route `"reconcileHeldSince":null`, die Admin-Seite zeigt den Hinweis nicht mehr (Bild `<scratchpad>/state-25/f2-nach-de.png`, sichtbare Texte ohne den Satz). Abschluss: Beobachtung und Cron beendet, Logs nach `state-25/nextcloud-ende.log` und `backend-ende.log`, `docker compose -f compose-25.yaml -p findling-25 --profile backend down -v` (`Volume findling-25-html Removed`, `Volume findling-25-data Removed`), Host-Verzeichnisse und Skripte bleiben im Scratchpad.

Ergebnis F2: bestanden, über der Ruhemarke setzte der fällige Abgleich aus, der Zeitpunkt wurde im ersten fälligen Tick geschrieben und gemessen, die Status-Route zeigte reconcileHeldSince und die Admin-Seite den Hinweis ab einem Intervall (3604 s), an der Schwelle setzte der gehaltene Marker aus, und im nächsten Tick (7501 s) lief der Zyklus mit der warning-Zeile und fand den neuen externen Speicher und die Datei ohne Ereignis; danach Hinweis und reconcileHeldSince weg.

#### Abweichungen und Befunde der Live-Proben

- Backend als Container aus dem Image am Kopf (Owner-Entscheid t1); state.db liegt im Volume, deshalb lesen `meta.py` und `files25.py` im Container (`/app/.venv/bin/python -I`, `mode=ro`), nicht per `uv run` auf dem Host.
- Der Ausschluss `Ext1/viele` griff nicht, weil Präfixe relativ zur Wurzel des Mounts gelten (docs/admin-page.md, so dokumentiert); korrigiert auf `viele`. Die Räumung der bereits gecrawlten Zeilen lief mit dem Cron im Minutentakt über Stunden; sie wurde einmalig mit `cron.php` in schneller Folge abgearbeitet (110 Läufe, `state-25/cron.log`). Kein Befund: die Räumung arbeitet in Blöcken je Cron-Lauf.
- F1 (b): die Nachzählung von 50 000 Einträgen braucht keine Sekunde je Scheibe; eine Runde spannt einen Tick erst mit dem von Nextcloud empfohlenen Cron-Takt von 5 Minuten (zweiter Lauf). Der erste Lauf mit 60 s steht oben ebenfalls.
- F2: die 9000 Seiten kamen über den Crawl in die Warteschlange; der Crawl hält den Abgleich bis zu seinem Ende (19:45:38), der Zeitpunkt entstand im ersten fälligen Tick danach.
- Keine Befunde ab LOW.

### CI-Strecke, CHANGELOG und Doku 45-20

Braucht der Wrapper Collabora? Nein: richdocuments legt die Secure View über jeden Mount außer `/`, sobald `watermark_enabled` nicht `no` ist (Application.php v11.1.3 und v12.0.2 Z. 139-153, `### Quellen am Tag`), ohne Bezug auf einen Collabora-Server; auf findling-59 griff er ohne Collabora in jedem Modus. Deshalb gebaut (Entscheid `Rückfragen 45-17`): Job `watermark-59` in .github/workflows/integration.yml mit den Schritten `M-45-59: ...`, richdocuments 11.1.3 (neueste Version für Nextcloud 34, `max-version 34`) als Archiv der Store-Freigabe `nextcloud-releases/richdocuments` mit gepinntem SHA-256 `f6d25946904eeae26107f9fa7c38a45daa6b6df159a5fb5bfdf46735f61cd29d` (laut GitHub-Digest des Assets) und Prüfung der Version nach `app:enable`; M1 mit Besitzer, Empfängerin ohne Download und Außenstehendem (indexed, beide finden, der Dritte nicht, die Empfängerin ohne Ausschnitt), Kontrolle mit Wasserzeichen aus (Ausschnitt für die Empfängerin), M3 mit Tag (`failed(policy_blocked)` in Container und Nextcloud über `occ findling:diagnose`); unter M1 keine Assertion eines Ausschnitts für eine Freigabe mit Download oder einen Team Folder. run-Blöcke ohne `${{ }}`, keine Geheimnisse. Strukturgate `scan_watermark_job` in backend/tests/test_php_static_gates.py mit Fehl-Samples (Job fehlt, M1-Schritt fehlt, Prüfsumme fehlt, M3-Schritt fehlt, ungepinnte Version, Ausdruck im run-Block, continue-on-error): 8 Tests grün; zizmor und actionlint über `php_gates_docker.sh all` grün. Der CI-Beleg folgt mit dem nächsten freigegebenen Push (Vorbedingung von 45-10 Task 1).

CHANGELOG [1.7.0] unter "### Fixed", "### Behoben", "### Corrigé": Text 4 (#59) und Text 7 (V-45-10-03) aus 45-17-PLAN.md bzw. 45-FREIGABEN.md, E3 aus `Freigegebener Wortlaut CHANGELOG E3`, dazu I-45-26-01 aus `Freigegebener Wortlaut CHANGELOG I-45-26-01`; je Zeile wörtlich geprüft, Gegenprobe mit einem geänderten Wort rot. Keine Zeile für V-45-10-02 und keine für U-45-20-01 bis -03 (nie ausgeliefert). Doku: docs/reconcile.md (policy_blocked in der Strähne, einmalige Erneuerung erst ab Generation 4), docs/formats.md (Generation 4, Reihenfolge der Updates gleichgültig), docs/admin-page.md (neuer Grund, neue unreadable-Abhilfe, Platzhalter, `asked`, `origin`, `reader`), docs/privacy.md (E1 mit der Zeile von Findling in der Prüfspur, E2, E3, Team Folder unter shareAll).

status_45_20: passed

## Nachtrag 45-21 (unabhängiger Review, Delta-Audit, neuer Prüfkopf)

Plan 45-21, 2026-11-23 bis 2026-11-24. Der unabhängige Review des ganzen Release-Diffs v1.6.5..HEAD steht in 45-REVIEW-1-7-0.md (Task 1, zweiter Prüfer-Bericht am 2026-11-24 nachgeprüft und eingearbeitet, R-45-21-12 bis -19). Alle Befunde ab LOW sind vor dem Prüfkopf behoben (Owner "Ok" 2026-11-24 02:51 und 12:50 UTC, 45-FREIGABEN.md); die Fixes mit RED-Commit, Mutationsgegenprobe und Gates stehen unter `### Befunde 45-17 bis 45-24`.

### Delta-Audit af0e5e13 bis Kopf

Jeder Prüfpunkt mit Probe und Ergebnis, am Endstand dieses Plans (Kopf = letzter Commit außerhalb .planning, siehe audited_head oben).

**Umfang.** `git log --oneline af0e5e13..HEAD -- . ':!.planning'`: 46 Commits, von c3885795 (CHANGELOG-Zeile 45-10) über 10d9707e (V-45-10-01) und alle Commits der Pläne 45-17 bis 45-26 (#59, V-45-10-02/03, E3, #25 F1/F2, I-45-23-07, I-45-26-01, I-45-25-01, U-45-20-01 bis -03, watermark-59) bis zu den neun Review-Fixes von 45-21 (R-45-21-01 bis -04, -12 bis -15, -19 samt RED-Commits und Testisolation e7826527).

**Gateway und Rechte (#59, E1/E2).**
- rejectForeignCaller ist die erste Anweisung von GatewayController::getFileContents (Z. 92); Probe: Code am Kopf, GatewayControllerTest (fremde ExApp 403 ohne Kopf). Ergebnis: bestanden.
- NoUser/404 nur für die benannte Person, kein neues Orakel: GatewayReader::open Z. 117-125 (NoUserException läuft unverändert hoch, Antwort wortgleich wie fehlende Datei), not_found unverändert zu 1.6.5 (GatewayControllerTest). Ergebnis: bestanden.
- Erneutes Öffnen nur bei Nachricht UND Ursprungs-Frame SecureViewWrapper::checkFileAccess (isSecureViewRefusal Z. 145-154), dann in actAs (openAs Z. 217 ff.); mit Besitzer genau ein Versuch (openAgain Z. 184-192, E1), keine Umgehung: jedes andere Ende des Besitzer-Versuchs ist policy (E2); jede andere ForbiddenException bricht sofort mit policy ab (open Z. 131-134). Probe: Code am Kopf, GatewayReaderTest (22 Fälle), echte Belege `#### Pfad folgt dem Besitzer`, `#### M2, M4, M5 nach dem Fix`, `#### files_accesscontrol beim Öffnen (I-45-17-03)`. Ergebnis: bestanden.
- E3 SnippetPolicy fail-closed: wirft die Erkennung oder steht ein unbekannter watermark_*-Modus auf yes, gibt es keinen Ausschnitt (SnippetPolicy, SnippetPolicyTest 30 Fälle inkl. lazy nach R-45-21-02); echter Beleg `#### E3 Ausschnitte unter M1 (45-22)`. Ergebnis: bestanden.

**Endfilterung unverändert (SearchService).** `git diff af0e5e13..HEAD -- php/lib/Service/SearchService.php` enthält genau zwei Hunks; das Skript im Scratchpad (`uv run --no-sync python <scratchpad>/hunks.py`, nie `python -c`) bestimmt die Bereiche am Kopf und ordnet jeden Hunk zu:
- Bereich (a) Konstruktor-Parameter SnippetPolicy samt Docblock: Z. 163-180 am Kopf; Bereich (b) Block zwischen dem Kommentar "Only now, and only for the survivors" und dem Aufruf `exApp->snippets` (die Zuweisung an $excerpts einschließlich ihrer Argumente): Z. 524-555 am Kopf.
- `@@ -160,12 +160,22 @@ class SearchService {` -> geänderte Zeilen 163-178: liegt in (a).
- `@@ -521,11 +531,18 @@ class SearchService {` -> geänderte Zeilen 534-545 (E3-Block, $allowed statt $fileIds als Argument): liegt in (b).
- Kein Hunk außerhalb der Bereiche (Skript-Exit 0).
- Funktionskörper per Skript (`<scratchpad>/funcs.py`) an af0e5e13 und am Kopf ausgeschnitten und verglichen: readableFile (af0e5e13 Z. 723-725, Kopf Z. 740-742, sha256 0719e270 beide), readableNode (Z. 736-742 -> 753-759, 60d1ffd0 beide), hitOf (Z. 765-782 -> 782-799, 7417f9f1 beide), Recheck-Schleife (Z. 385-475 -> 395-485) byte-gleich.
- `tests/test_php_acl_boundary.py` grün (13 passed, Lauf am Endstand). Psalm-Taint grün (0 Befunde gegen nextcloud/ocp v33.0.9, v34.0.6, v35.0.3, Probe gesehen). Ausfallzählung für policy unberührt: GatewayPolicyRefused kehrt vor der Zählung zurück (poller.py Z. 2607-2614 und 2885-2894, test_poller). Ergebnis: bestanden.

**Logzeilen nur Zähler.** `git diff af0e5e13..HEAD -U0 -- php/lib backend/src php/js | grep -E "^\+.*(logger->|LOGGER\.|_LOG\.|console\.)"`: elf neue Zeilen, alle nur Zähler, fileId, Klassennamen, origin (Klasse::Funktion) und die nach a1 freigegebene reader-uid; die Zeile mit `['exception' => $e]` in ReaderCandidates stammt wortgleich aus 1.6.5 (R-45-21-09, INFO). Ergebnis: bestanden.

**Migrationen und Schema (T-45-33, Upgrade-Bruch ab 1.6.5, aus 45-09, keine neue ID).** `git diff --stat af0e5e13..HEAD -- php/lib/Migration` zeigt genau zwei Dateien: Version001500Date20261012000000.php (geändert) und Version001700Date20261123000000.php (neu); der Satz "keine Migration" aus der Planfassung vor 45-26 ist durch die dort ausdrücklich geforderte Aufnahme dieser beiden Migrationen ersetzt. Kein Schema-Zugriff in beiden (0 Treffer createTable/addColumn/changeColumn/dropTable/ISchemaWrapper), Schema unverändert. Im Einzelnen:
- Migration des Minor-Schritts: `Version001700Date20261123000000` löscht backend_app_version ohne Klasse der App, Löschung mit Wächter und Literale gegen die Konstanten geprüft (Version001700Date20261123000000Test, Mutationen M29 bis M31 rot, 45-26); sonst suchte 1.7.0 nach dem Update leer (T-45-33).
- Version001500 nach `Entscheid I-45-23-07 45-26` (m1) und nach der Messung I-45-26-01: ohne Klasse der App (Update aus 1.3.2 starb an markScanStale()), setzt die Marke mit Literalen und vergisst scan_recounted_at, ein Sprung aus 1.4 zählt sofort nach (M32 bis M34 rot); Beleg unter T-45-82 (I-45-23-07) und T-45-33.
- Keine weitere einmalige Marke für 1.7.0 (45-26, MigrationSelfContainedTest).
- Probe des Update-Nachweises mit Kontrolle 2 (M35, M36 rot, 45-26; FROM_TAGS ab v1.3.2, lokal 137 s), seit 45-21 liest der Treiber den gepflanzten Wert zurück (R-45-21-03, Docker-Gegenprobe: Pflanzen entfernt -> jeder Lauf rot "was not planted") und Kontrolle 2 unterscheidet Bestehen von anderem Fehlschlag (R-45-21-19, Verhaltensprobe der drei Zweige am extrahierten Block); dazu die Suche direkt nach dem Update aus 45-20 (`#### Suche direkt nach dem Update (45-26)`: Treffer sofort). Ergebnis: bestanden.
- I-45-25-01 (aus 45-26 Task 5, wie der Hinweis aus 45-25 unter T-45-81, keine neue ID): der Hinweis zu Dateisperren erscheint nur, wenn die Memcache-Factory die Klasse aus `memcache.locking` laden würde; `class_exists` auf dem rohen Wert erst nach dem Namensvergleich, Autoloader-Probe, Mutationen M37, M38, M39 und M40 rot (LockingCheckServiceTest). Ergebnis: bestanden.

**Generation und Erneuerung.** Generation 4 mit Rückfall gateway_error für 3/2/None (queue.py, test_queue_client); Begleit-App meldet verdicts 3 und verdictsMax 4 getrennt, ein 1.6.x-Container vor dem Container-Update speichert keine Ersatzgründe (R-45-21-14); Erneuerung refusal_streaks_1_7_0 einmalig und erst ab Generation 4 (repo.py Z. 251, 1637-1669, U-45-20-01, Schritte A und B danach echt neu gefahren). V-45-10-02: Bestätigung nur über text()/textContent, eine Regex-Ersetzung mit Callback (Gate mit Fehl-Samples). Ergebnis: bestanden.

**Performance.** Keine neue Abfrage je Suche ohne aktives Wasserzeichen; mit Wasserzeichen gebänderte Zusatzabfragen je Seite (T-45-77); Nachzählung mit Mindestabstand 6 h statt 15-Minuten-Takt (T-45-82); Rückhalt höchstens ein Zyklus je zwei Intervalle (T-45-84); Zeitmessung 20 Kandidaten 0,21 s (T-45-61). Ergebnis: bestanden.

**#25 F1.** `CrawlAdvanceService::crawling()` liest als Lock-Signal nur `StorageCrawlJob::CRAWL_ACTIVE_LOCK` (CrawlAdvanceService.php Z. 82-91); recount-Scheiben nehmen nie den Marker (StorageCrawlJob.php Z. 290-296: Marker nur im Crawl-Modus); der Slice-Lock serialisiert weiter Crawl und Nachzählung; der Marker wird im verschachtelten finally vor dem Slice-Lock freigegeben (Z. 326-336); Mindestabstand 6 h mit Regelzweig nach `Entscheid Regeln Nachzählung 45-23` (r1: gespeicherte Regeln binnen 15 Minuten, SettingsService.php Z. 322 und 391-398). Ergebnis aus 45-20 `### Live-Proben #25` (F1 bestanden). Ergebnis: bestanden.

**#25 F2.** Rückhalt nie bei crawling (Rundenstart reconcile.py Z. 537-566, jede Scheibe Z. 694-699); Zeitpunkt nur nach ganzem Zyklus gelöscht (Z. 651, ROUND_WALKED); Warnzeile und reconcileHeldSince ohne Pfad und Namen (status.py Z. 471 und 846, nur Zahlen, Satz nur aus dem Katalog). Ergebnis aus 45-20 `### Live-Proben #25` (F2 mit 9000 Seiten OCR-Rückstand bestanden). Ergebnis: bestanden.

**Sonstiges am Kopf.** Generation-4-Tabellen beidseitig (W3); Erneuerung einmalig (Marke in derselben Transaktion); V-45-10-02 nur textContent; R-45-21-13: der Fehlerzustand der Speicherliste hat die Mechanik (Speichern hebt nichts auf) und den freigegebenen Satz in 18 Katalogen (Schlüsselzahl 387).

#### Lokale Gates am Endstand

- `bash scripts/dev/phpunit_docker.sh`: `OK (1448 tests, 9072 assertions)`.
- `bash scripts/dev/php_gates_docker.sh all` (in den drei Beinen psalm, cs, workflows seriell gefahren): Psalm-Taint gegen nextcloud/ocp v33.0.9, v34.0.6, v35.0.3 je `taint findings: 0`, Probe gesehen (3); php-cs-fixer `Found 0 of 144 files that can be fixed`, Probe gesehen; zizmor grün, Probe gesehen; actionlint grün, Probe gesehen (SC2086). Gefahren am Stand 2ce40602; die beiden späteren Commits (306a727d, GREEN R-45-21-19) ändern keine Datei unter php/ und keinen Workflow, die PHP-Hälfte ist am Endstand byte-gleich (Baumhash 86f595c7, 147 Dateien, Rezept und unabhängige Pipeline).
- Python in backend/: `ruff check .` grün, `ruff format --check .` 261 Dateien formatiert, pyright (latest) 0 Fehler, vulture grün.
- pytest gesamt in zehn Teilen (Speicher knapp, Vorgabe des Koordinators): 7411 passed, 305 skipped (Teil 1 bis 10: 866; 665+4sk; 725+35sk; 1096; 659+245sk; 758+10sk; 856+1sk; 569+9sk; 734+1sk; 483).

### Threat-Register 45-17 bis 45-24

T-45-57 bis T-45-87 aus den Threat-Blöcken der Pläne 45-17 bis 45-24 (45-25 und 45-26 führen keine eigene ID: der Teil von 45-25 steht unter T-45-81, der von 45-26 unter T-45-33, T-45-82 und T-45-81), dazu T-45-64 und T-45-73 aus 45-21. Jede Zeile am Kopf nachgeprüft (Code, Test oder Audit-Abschnitt als Beleg).

| Threat ID | Kategorie | Komponente | Disposition | Beleg und Status |
|---|---|---|---|---|
| T-45-57 | Elevation of Privilege | erneutes Öffnen im Gateway | mitigate | rejectForeignCaller() ist die erste Anweisung von GatewayController::getFileContents (Z. 92); GatewayControllerTest (fremde ExApp 403 ohne Kopf); closed |
| T-45-58 | Information Disclosure | 404-Gleichheit, Nutzer-Enumeration | mitigate | NoUser der benannten Person läuft unverändert hoch, Antwort wortgleich wie fehlende Datei (GatewayReader::open Z. 117-125, Docblock); erneutes Öffnen erst nach Auflösung und Secure-View-Ablehnung; GatewayControllerTest not_found-Gleichheit; closed |
| T-45-59 | Information Disclosure | Logzeilen der neuen Zweige | mitigate | alle neuen Logzeilen af0e5e13..Kopf per `git diff -U0` gezogen (Delta-Audit Punkt 7): nur Zähler, fileId, Klassennamen, origin und die freigegebene reader-uid (a1); closed |
| T-45-60 | Information Disclosure | Treffer für Empfänger unter Secure View | mitigate | E3 über SnippetPolicy (fail-closed), echter Beleg `#### E3 Ausschnitte unter M1 (45-22)`; carol ohne Freigabe findet nichts (Endfilterung byte-gleich, Delta-Audit Punkt 5); closed |
| T-45-61 | Denial of Service | Schleife des erneuten Öffnens | mitigate | mit Besitzer genau ein Versuch, sonst Kappe 20 (GatewayReader::openAgain Z. 184-205, ReaderCandidates::MAX_READER_TRIES Z. 34); Zeitmessung 0,21 s für 20 Kandidaten (`#### asked zählt übersprungene Leser`, W6); closed |
| T-45-62 | Denial of Service | Ausfallzählung im Poller | mitigate | GatewayPolicyRefused kehrt vor der Zählung zurück (poller.py Z. 2607-2614, 2885-2894); test_poller (policy_blocked ohne Ausfallzählung), Mutation in 45-18 rot; closed |
| T-45-63 | Tampering | Draht-Vokabular bei getrenntem Update | mitigate | Generation 4 mit Rückfall gateway_error für 3/2/None (queue.py, test_queue_client Wire-Mapping); Begleit-App meldet einem 1.6-Container verdicts 3 und verdictsMax 4 getrennt (R-45-21-14, c721641f); closed |
| T-45-64 | Repudiation | Kandidat ändert sich unbemerkt, Fix ohne Owner | mitigate | Freigabe- und Entscheidzeilen je Befund in 45-FREIGABEN.md, genau eine audited_head-Zeile in dieser Datei, 45-10 läuft komplett neu, kein Push ohne eigene Freigabe; closed |
| T-45-65 | Tampering (XSS) | Bestätigungszeile mit ID | mitigate | confirmedMounts schreibt nur per text()/textContent, eine Regex-Ersetzung mit Callback (test_the_script_reads_a_mount_only_out_of_its_row_and_writes_it_as_text, Fehl-Samples $& und %2$s); closed |
| T-45-66 | Tampering | Katalogwert des Platzhalters im Attribut | mitigate | Ausgabe nur über p() (scan_lookup_placeholder, scan_rules_placeholders); test_no_catalogue_value_can_break_the_page deckt alle Schlüssel inkl. 387; closed |
| T-45-67 | Information Disclosure | Umgehung einer Sperre durch Lesen als andere Person | mitigate | erneutes Öffnen nur bei Nachricht UND Ursprungs-Frame SecureViewWrapper::checkFileAccess (isSecureViewRefusal Z. 145-154, Mutationen aus 45-17 rot); I-45-17-03: files_accesscontrol wirft beim fopen "Access denied by access control" (StorageWrapper.php v6.0.1 Z. 241-253, Operation.php Z. 118), echtes Ergebnis 45-20 Schritt C (c) unter `#### files_accesscontrol beim Öffnen (I-45-17-03)`: 403 policy, asked 0, kein erneutes Öffnen, kein Rückfall auf den Besitzer; dazu C (a) und C (b); closed |
| T-45-68 | Tampering | Nachbau mit falscher Version oder ohne Quelle | mitigate | `### Quellen am Tag` mit SHA-256, Modustabellen vorher/nachher; closed |
| T-45-69 | Denial of Service | einmalige Erneuerung erzeugt Last | accept | höchstens drei Anfragen je betroffener Datei, einmal je Datenbank (Marke refusal_streaks_1_7_0 in derselben Transaktion, repo.py Z. 1637-1669); closed |
| T-45-70 | Spoofing | 403 einer fremden Quelle mit gefälschtem Kopf | accept | Antwort kommt nur vom eigenen Gateway über die AppAPI-Verbindung; Folge wäre nur ein anderes Urteil; closed |
| T-45-71 | Tampering | richdocuments-Download in CI | mitigate | Version 11.1.3 per SHA-256 gepinnt, nach app:enable geprüft (`### CI-Strecke, CHANGELOG und Doku 45-20`); closed |
| T-45-72 | Repudiation | Simulation als echter Beleg | mitigate | kein d2-Fall eingetreten: Schritt 0 und die drei Abgleiche echt abgewartet (d1, `#### Schritt 0 Serie auf v1.6.5`); closed |
| T-45-73 | Repudiation | Review mit dem Muster der Umsetzung | mitigate | Review liest Code gegen Projektregeln und Fremdquellen (raw mit SHA-256), nicht die Tests der Umsetzung; zweiter Prüfer ohne Umsetzungskontext, Executor hat jeden Befund am Code nachgeprüft (45-REVIEW-1-7-0.md `## Auftrag`, Befundtabelle Spalte Beleg); closed |
| T-45-74 | Repudiation | Prüfspur nennt für Secure-View-Dateien die lesende Person | accept | Owner-Entscheid a4 (2026-11-23 15:47 UTC): CriticalActionPerformedEvent mit fileid, Pfad, uid nur nach einem Lesen in actAs (GatewayReader Z. 231-244), uid auch in der info-Zeile (a1); dieselbe Datenart, die admin_audit für jedes Lesen schreibt; in docs/privacy.md genannt; R-45-21-06 bewertet; AN 45-16 (secure-phase): als bewusste, dokumentierte Erweiterung der Prüfspur führen; open bis 45-16 |
| T-45-75 | Information Disclosure | Textausschnitt einer Secure-View-Datei in der Suche | mitigate | SnippetPolicy vor exApp->snippets ($allowed, Gate Regel 8 mit Fehl-Sample), fail-closed; echter Beleg `#### E3 Ausschnitte unter M1 (45-22)`; closed |
| T-45-76 | Spoofing | Erkennung bricht bei neuer richdocuments-Version | mitigate | beide Bedingungen nötig, sonst policy ohne Umgehung (fail-closed); SecureViewRefusal-Fixtures (anderer Frame, andere Meldung); closed |
| T-45-77 | Denial of Service | Zusatzabfragen je Suche | mitigate | nur bei aktivem Wasserzeichen, gebändert für die ganze Seite (SnippetPolicy: getByFileIds, Mount-Cache, getTagIdsForObjects); Delta-Audit Punkt 11 (Performance); closed |
| T-45-78 | Tampering | Bruch einer internen richdocuments-API (nur bei S2) | mitigate | entfallen: S2 wurde nicht gebaut, S3 nutzt nur OCP (Entscheid E3-Weg 45-22, `#### S1 für shareDisabledDownload nach dem Owner-Entscheid`); CI-Schritt watermark-59 prüft das Endverhalten mit echtem richdocuments; closed |
| T-45-79 | Denial of Service | Nachzählung gilt als unfertiger Crawl, Abgleich setzt aus (#25 F1) | mitigate | crawling() liest nur CRAWL_ACTIVE_LOCK (CrawlAdvanceService Z. 82-91), Nachzähl-Scheiben nehmen den Marker nie (StorageCrawlJob Z. 290-296 nur im Crawl-Modus); Live-Probe `#### F1 Nachzählung hält den Abgleich nicht auf`; M-Mutationen 45-23 rot; closed |
| T-45-80 | Tampering | Abgleich neben unfertiger Crawl-Scheibe | mitigate | Crawl-Scheibe nimmt den Marker unter dem Slice-Lock, Freigabe im verschachtelten finally vor dem Slice-Lock (StorageCrawlJob Z. 326-336); CrawlAdvanceServiceTest; closed |
| T-45-81 | Denial of Service | Marker eines abgestürzten Prozesses; Locking-Cache nur eines Prozesses | accept/mitigate | Marker mit TTL des Slice-Locks (StorageCrawlJob Z. 122-127); Hinweis der Admin-Seite nach l1 (LockingCheckService, Text 5), seit 45-26 Task 5 nur wenn die Memcache-Factory die Klasse laden würde (I-45-25-01, class_exists auf dem Rohwert nach dem Namensvergleich, Autoloader-Probe, M37 bis M40 rot); closed |
| T-45-82 | Denial of Service | Nachzählung im 15-Minuten-Takt belegt den Slice-Lock | mitigate | RECOUNT_MIN_INTERVAL_SECONDS 6 h ab Start der letzten Runde (SettingsService Z. 322, 391-398), Regelzweig nach `Entscheid Regeln Nachzählung 45-23` (r1), Zukunftsstempel fällig; Marke aus Migration 1.5 nach m1 (I-45-23-07, 45-26: Version001500 vergisst scan_recounted_at, Sprung aus 1.4 zählt sofort); closed |
| T-45-83 | Tampering | Rückhalt öffnet neben einem Crawl | mitigate | Rückhalt nie bei crawling: Rundenstart und jede Scheibe prüfen (reconcile.py run_once Z. 537-566, Z. 694-699); test_reconcile; Live-Probe `#### F2 Rückhalt bei langer Warteschlange`; closed |
| T-45-84 | Denial of Service | Rückhalt-Zyklus auf einer 4-GB-Box | accept | höchstens ein Zyklus je zwei Intervalle (BACKSTOP_FACTOR 2, Z. 214), Scheiben mit Pause; Owner z1 ausdrücklich mit dieser Last; Live-Probe mit 9000 Seiten OCR-Rückstand bestanden; closed |
| T-45-85 | Information Disclosure | Warnzeile oder Statusfeld tragen Pfade oder Namen | mitigate | Warnzeile nur Stunden, Zähler, Marke; reconcileHeldSince eine ganze Zahl (status.py Z. 471, 846; AdminViewService Z. 3497), Satz aus dem Katalog; closed |
| T-45-86 | Tampering | ungültiger oder künftiger Zeitpunkt im Zustandsspeicher | mitigate | ungültig oder Zukunft wird als jetzt neu geschrieben, gelöscht nur nach ROUND_WALKED (reconcile.py Z. 651); test_reconcile Zukunftsstempel; closed |
| T-45-87 | Repudiation | Live-Probe #25 verkürzt als Standard ausgegeben | mitigate | `### Live-Proben #25` nennt Intervalle und Takt wörtlich; Verkürzungen als solche benannt (cron.php in schneller Folge, dokumentiert); closed |

### Befunde 45-17 bis 45-24

Alle Befunde der Gegenprobe 45-20 und des Reviews 45-21 mit Status; die vollständige Tabelle mit Beleg je Befund steht in 45-REVIEW-1-7-0.md `## Befunde`.

| Befund | Schwere | Status |
|---|---|---|
| U-45-20-01 (Erneuerung vor Generation 4) | MEDIUM | behoben aec5edcf/151dca7b (Owner f1), Schritte A und B neu gefahren |
| U-45-20-02 (Prüfspur nennt die lesende Person nicht) | MEDIUM | behoben f3290689/1d191e7e (Owner a4), echter Beleg in audit.log |
| U-45-20-03 (warning ohne Herkunft) | LOW | behoben 3550b2b3/c9dc3270/0f6afac7 (Entscheid c2); als R-45-21-05 nachgeprüft |
| R-45-21-01 (Klassenkommentar GatewayReader) | LOW | behoben 6aa00ef6 |
| R-45-21-02 (Kommentar und Testlücke lazy-Modi SnippetPolicy) | LOW | behoben 7fe3f91c, Mutation (isLazy false) jetzt rot |
| R-45-21-03 (Treiber liest gepflanzten Wert nicht zurück) | LOW | behoben b653ef3b/f9189779, Docker-Gegenprobe: Pflanzen entfernt, jeder Lauf rot "was not planted" |
| R-45-21-04 (Kommentar-Reihenfolge poller.py) | LOW | behoben 6aa00ef6 |
| R-45-21-05 (= U-45-20-03) | LOW | vor 45-21 behoben, nachgeprüft |
| R-45-21-12 (Freigabe hebt Speicher-Ausschluss auf) | MEDIUM | behoben b3af58e9/6dc5bb70; nur Provider aus providers() tragen einen Speicher anderswo, files_external nur außerhalb der ausgeschlossenen Admin-Mounts; Live-Gegenprobe des Ausschlusses läuft im kompletten Neulauf von 45-10 (Ausschluss mit Abgleich) |
| R-45-21-13 (leere Liste statt Fehlerzustand) | LOW | behoben 472b4206/f37e3301 (Mechanik) und 2643c072/2ce40602 (Satz nach `Freigabe Texte Review 45-21`, 18 Kataloge, Schlüsselzahl 387) |
| R-45-21-14 (Generation 4 vor 1.6.x-Container) | LOW | behoben aceed6ca/c721641f; verdicts bleibt 3, verdictsMax 4, ein 1.6.x-Container speichert keine Ersatzgründe |
| R-45-21-15 (occ-Typkonflikt sperrt das Speichern) | LOW | behoben 51fdc1cf/174b8a26 |
| R-45-21-19 (CONTROL 2 meldet "passed the probe" bei anderem Fehlschlag) | LOW | behoben 306a727d/131b4536; rc 0 und anderer Fehlschlag getrennt gemeldet, Gate mit Fehl-Samples |
| R-45-21-06 bis -11, -16 bis -18 | INFO | geschlossen bzw. an 45-10 (R-45-21-08 erster CI-Lauf) und 45-16 (R-45-21-06 unter T-45-74) übergeben |

Stand F3 (I-45-23-01): offen, wartet auf Logs des Melders

## Nachtrag 45-10 (Volltest DE/EN/FR auf dem finalen Kopf)

Stand: 2026-11-25. Kopf 8c02b706 (= origin/main), letzter Commit außerhalb .planning d3e6d76a047421482af9ea3adcbff42fa0b690d6.

### Push und Rebase-Prüfung

- `Freigabe Push 45-10` steht in 45-FREIGABEN.md ("Go", Push aff5f1d3..8c02b706 laut `git reflog show origin/main`: `8c02b706 refs/remotes/origin/main@{2026-11-25 16:21:21 +0100}: update by push`).
- `git fetch origin` (2026-11-25 15:24 UTC), danach `git rev-list HEAD..origin/main` leer (0 Zeilen), `git merge-base --is-ancestor origin/main HEAD` gelingt. Kein Rebase, deshalb kein Unterabschnitt Rebase.

### CI-Lauf am Kopf 8c02b706

Der eine CI-Warter (B4) ist der Koordinator; er hat den Lauf `scripts/ci/head_green.sh` für 8c02b706 selbst ausgewertet, dieser Executor startete keinen zweiten Warter. Ergebnis laut Koordinator (2026-11-25): CI 8/8 success, darunter Integration 45644218526 und HaRP deploy 45644218559; der Workflow security lint wurde wegen seines paths-Filters nicht ausgelöst. Das Log des HaRP-deploy-Laufs 45644218559 enthält keine echte Zeile "part A candidate" oder "part B candidate", die Treffer der Suche sind nur die mitgeloggten Skriptquellen (Hinweis aus 45-27 zum repeatedly_stuck-Bestand, I-45-10-05: INFO, kein Befund).

### R-45-21-08 erster echter CI-Lauf watermark-59

Erfüllt vor 45-10: Integration-Lauf 45425766124 zu aff5f1d3202d60e6f3b993fe200ed616c54dd206 (`conclusion: success`, 2026-11-24 15:27 UTC), Job 138557213079 `watermark-59 (stable34, 8.2)` `success` (gelesen mit `gh run list --commit aff5f1d3... --workflow integration.yml` und `gh run view 45425766124 --json jobs`).

### Delta-Audit 131b4536 bis d3e6d76a (45-27)

Der Code-Delta seit dem audited_head von 45-21 ist genau Plan 45-27 (17 Dateien, 799+/36-: CHANGELOG EN/DE/FR, repo.py, poller.py, reconcile.py, coverage_truth.sh, QueueMapper.php, FileStateService.php, docs/ocr.md, docs/reconcile.md, Tests und Fixture). Jeder Punkt ist unter `### RED und GREEN 45-27` mit RED, GREEN und den Mutationen M50 bis M58 belegt. Eigene Gegenproben dieses Plans am Kopf:

- B6: die einzige neue Logzeile ist `BACKSTOP_LINE` (poller.py Z. 181) mit `%d demanded handovers` und `file id %d`, kein Name, kein Pfad.
- Keine neue nutzersichtbare Zeichenkette in einem Katalog und keine Routenänderung: `git diff 131b4536 d3e6d76a -- php/l10n backend/appinfo php/appinfo` und `-- backend/src/findling/api` je 0 Zeilen.
- QueueMapper.php: außer Kommentaren ändert sich nur die Lesung `$dirtyBefore` vor den beiden Updates und ihre Verwendung in der Rückgabezeile (diff ohne Kommentarzeilen: drei Zeilen).

audited_head (oben im Dokument) stand nach diesem Abschnitt auf d3e6d76a047421482af9ea3adcbff42fa0b690d6 und steht seit dem Fix-Durchlauf unten auf 9965e30b3330caf1291c246c3c0a993464882a7a (zuvor b9ace7bd).

### Fix-Durchlauf

Fix-Commits aus dem Volltest (45-VOLLTEST.md `## Befunde`), alle lokal, kein Push; der Push braucht `Freigabe Push 45-10 Fix`.

| Befund | Schwere | Commits | Delta-Audit (Probe) |
|---|---|---|---|
| V-45-10-04 Farben von Feldfehler, Zähler 1/0 und Markierung | LOW | f7457dac (RED), 685e5578 (GREEN) | nur php/css/admin.css (drei Selektoren mit `.section` davor, Kommentar) und ein Test; getComputedStyle in der Instanz hell rgb(138, 0, 0) / rgb(102, 71, 0), dunkel rgb(255, 204, 204) / rgb(255, 238, 197); drei Mutationen rot; keine PHP- oder Routenänderung |
| V-45-10-05 Zahl vor Nomen im Plural | MEDIUM | b056b3b9 (Freigabe), 8988ba79 (RED), 1d832d03 (GREEN, Admin-Seite 500), d5efe7cd (RED %n-Gate), b9ace7bd (GREEN) | admin.js (acht Aufrufe n(), Helfer counted), templates/admin.php (sieben Aufrufe $l->n, Helfer $counted mit preg_replace_callback, nur die erste alleinstehende Zahl, nie ein Platzhalter), 18 Kataloge (acht Schlüssel, Werte wie freigegeben, Pluralform unverändert), sechs Sprachtabellen, CHANGELOG EN/DE/FR, Tests; B6: keine Logzeile und keine Route geändert; T-45-35: alle Sätze gehen weiter über p() bzw. text()/textContent, kein Markup; Gate 1 mit 15 Mutationen rot, Gate 2 mit 2 Mutationen rot; Live: Admin-Seite HTTP 200, Sätze in DE/EN/FR wie freigegeben, FR bei 0 im Singular |

Ursache des 500 am Stand 1d832d03, an der Quelle belegt (nextcloud 34.0.3 in der Instanz): `OC\L10N\L10N::n` baut `L10NString` mit den Formen; `L10NString::__toString` ersetzt `%n` durch `%count%` und übergibt die Zahl nur, wenn die Formen `%n` tragen; sonst liefert der Übersetzer beide Formen mit `|` verbunden und `vsprintf` wirft "The arguments array must contain 2 items, 1 given" (L10NString.php Z. 54). PHPUnit und alle Python-Gates waren grün; gefunden erst in der Live-Probe, deshalb das zweite Gate.

Gates am Stand b9ace7bd (seriell): ruff `All checks passed!`, ruff format `261 files already formatted`, pyright latest `0 errors, 0 warnings, 0 informations`, vulture ohne Fund; pytest in zehn Teilen 7422 passed, 305 skipped; PHPUnit `OK (1451 tests, 9087 assertions)`; `php_gates_docker.sh all` EXIT=0 (Psalm-Taint 3 x `No errors found!`, `taint findings: 0`; php-cs-fixer `Found 0 of 145 files`; zizmor `No findings to report.`; actionlint grün). PHP-Baumhash b7faf372/148 (Rezept und Pipeline gleich, Positivkontrolle git archive d5efe7cd = 00bf7160).

Nachtrag 26.11.2026:

| Befund | Schwere | Commits | Delta-Audit (Probe) |
|---|---|---|---|
| V-45-10-06 OCR-Deckel und Abgleichfrist | LOW | a73e13a5 (Freigaben, auch `Freigabe Push 45-10 Fix`), fb57b51f (RED), 9965e30b (GREEN) | nur templates/admin.php (zwei Aufrufe `$l->n` mit `$counted`), 18 Kataloge, sechs Sprachtabellen, Tests; keine Logzeile, keine Route; die Abgleichfrist kommt aus der Konstante 24 (`AdminViewService::RECONCILE_INTERVAL_HOURS`), die Einzahl ist dort Absicherung; drei Mutationen rot; Live je Sprache HTTP 200, Wert 1 und Wert größer 1 richtig |

Gates am Endstand 9965e30b (seriell): ruff, ruff format (261), pyright latest 0/0/0, vulture ohne Fund; pytest in zehn Teilen 7422 passed, 305 skipped; PHPUnit `OK (1451 tests, 9087 assertions)`; `php_gates_docker.sh all` EXIT=0 (Psalm-Taint 3 x 0, php-cs-fixer 0/145, zizmor und actionlint grün). PHP-Baumhash 7c52b1f4/148 (Rezept und Pipeline gleich, Positivkontrolle git archive fb57b51f = b7faf372).

Push nach "Freigabe Push 45-10 Fix" am 2026-11-26: `8c02b706..dd92da51  main -> main` (ohne Tag, Arbeitsbaum sauber, origin/main vorher unverändert, kein Rebase). Ein CI-Warter, `scripts/ci/head_green.sh dd92da51fd22a33ab8a0ff0f60e9a18a73baea5f "Python gates" "PHP and store metadata gates" "HaRP deploy" "Integration" "Resilience" "Multi-arch image" "Security scans"`, Exit 0, nach einem Rerun:

```
45741403354 OpenSSF Scorecard success
45741403101 Security scans success
45741403223 Multi-arch image success
45741403128 PHP and store metadata gates success
45741403174 Python gates success
45741403229 Resilience success
45741403102 HaRP deploy success
45741403207 Integration success
```

Rerun: Im ersten Versuch von Integration 45741403207 lief der Job `team-folder-acl (stable34, 8.2)` in sein Zeitlimit (25 min) und wurde abgebrochen. Er hing 24 min ohne jede Ausgabe im Schritt "Install the German dictionary the analyzer reads" (02:17:59 bis 02:42:33 UTC). Das ist ein Netzwerkhänger beim Download. Mit dem Push hat er nichts zu tun: Er änderte keine Workflow-Datei, und die übrigen 11 Jobs waren grün. Neu gestartet wurde nur dieser Job (`gh run rerun --failed`), danach success. Workflow security lint lief nicht (paths-Filter).

Befund I-45-10-07 (LOW, CI-Robustheit, nach 1.7.0): Der Schritt mit dem Wörterbuch-Download hat kein eigenes Zeitlimit und keinen Wiederholversuch. Ein Hänger kostet deshalb das ganze Job-Limit. Für die Register-Durchsicht in 45-16 vorgemerkt.

### Fix V-45-10-07 (Task 3 von 45-10)

Code-Delta seit 9965e30b: `php/css/admin.css` (Tabelle der Fehlerliste mit `white-space: normal` gegen das `nowrap` aus server.css; Chip, Köpfe und schmale Spalten bleiben ganz; halbe Zellpolster unter 512 px), `php/templates/admin.php` (Klasse `findling-errors__state` an der Zustandszelle) und die Tests. RED 33c41cd1, 972f90ab, 12107b50, 8ba59d82, 293ce570; GREEN 2751fc1f; Gate `test_the_error_list_wraps_its_long_sentences_against_the_nowrap_of_every_table` mit Positivkontrolle und Mutationen (9 von 9 rot). Kein PHP-Logikpfad, keine neue Eingabe, kein Rechte- oder Datenpfad berührt: CSS und eine Klasse im Template, Ausgabe weiter über `p()`.

PHP-Baumhash a46fd501/148 (bb4c0bc8; Rezept und unabhängige Pipeline gleich, Kontrolle 293ce570 = 7c52b1f4). Voller Backend-Lauf lokal am Kopf: 7423 passed, 305 skipped (834 s). Zweite Sichtprüfung DE/EN/FR auf 1280, 375 und 320 vom Owner abgenommen (45-VOLLTEST.md, 45-FREIGABEN.md).

audited_head steht damit auf bb4c0bc8 (letzter Commit außerhalb .planning, zuvor 9965e30b).

Push nach "Freigabe Push 45-10 V-07" am 2026-11-26: `dd92da51..1db01d02  main -> main` (ohne Tag). Ein CI-Warter, `scripts/ci/head_green.sh 1db01d02fa3a0001a94ef686adeae1f75a3a1900 "Python gates" "PHP and store metadata gates" "HaRP deploy" "Integration" "Resilience" "Multi-arch image" "Security scans"`, Exit 0, kein Rerun nötig:

```
45857375666 OpenSSF Scorecard success
45857375726 Security scans success
45857375729 Multi-arch image success
45857375762 PHP and store metadata gates success
45857375869 Python gates success
45857375687 Integration success
45857375721 Resilience success
45857375858 HaRP deploy success
```
