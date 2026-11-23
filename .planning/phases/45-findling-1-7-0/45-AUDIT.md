# Phase 45: Launch-Härtung und Audit von Findling 1.7.0 (Plan 45-09)

Stand: 2026-11-22. Muster: Delta-Audit 43-27 (Prüfpunkt mit Probe, Befund mit Schwere, Fixes ab MEDIUM per TDD, audited_head).

audited_head: af0e5e13e17aeb8d915dd5caacffcb056eb49e69
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
