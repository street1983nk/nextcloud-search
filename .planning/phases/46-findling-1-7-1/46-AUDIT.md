# Audit 46: Findling 1.7.1 (Delta v1.7.0..HEAD)

Stand: 2026-11-27, Plan 46-06. Muster 45-09: Probe je Prüfpunkt, Befundtabelle, audited_head nach dem Push.

## Umfang

Delta außerhalb .planning: `git diff --stat v1.7.0..HEAD -- . ':!.planning'` 46 Dateien. Kein Code im Container und keine PHP-Klasse: `git diff --stat v1.7.0..HEAD -- php/lib backend/src php/appinfo/routes.php` ist leer. Geändert sind Kataloge (18), Template und Stylesheet der Admin-Seite, admin.js, CI (setup-test-nc, integration.yml, coverage-e2e.yml, python.yml, deploy-harp.yml, zwei neue Skripte), Version und CHANGELOG, Doku und Tests.

Code-Commits seit v1.7.0 (ohne die zwei Doku-Commits 29ba097f, f08317ef aus 45-14):

| Commit | Gegenstand |
|---|---|
| 66570830, 14b9e0f8 | 46-01 Hilfesatz gleich Platzhalter, 18 Kataloge, Doku-Tabellen (EXCL-07) |
| 10744068, a4ea0a93 | 46-02 Enter in beiden Regelfeldern, IME-Schutz (EXCL-08) |
| 292197c9 | docs/store-listing.md ohne das gesperrte Wort (I-46-01-01) |
| 54d7785d, 4d5c4c6e, d74b0dc5 | 46-04 apt_install.sh, Zeitlimit und Wiederholung (PRUEF-05) |
| ad3002f8, 142c4296 | 46-04 Store upgrade 2b wartet auf die leere Queue (PRUEF-06) |
| e6932901, 409fb5a5 | 46-03 Fehlerliste unter 360 px, Variante A (ADM-05) |
| 03c53f11, 2dfe0f38 | 46-05 Version 1.7.1, CHANGELOG, Store-Links, admin-page.md (REL-08) |

## Security

| Nr | Prüfpunkt | Probe | Ergebnis |
|---|---|---|---|
| 1 | Katalogwerte ohne Markup und ohne neuen Platzhalter, Ausgabe escaped | `test_no_catalogue_value_loses_or_invents_a_placeholder` grün; Template gibt den Hilfesatz über `p($l->t(...))` aus (admin.php Z. ~1586, unverändert); geänderte Werte enthalten nur Wörter (diff je eine Zeile, 18 Dateien) | ok |
| 2 | Enter-Weg baut kein Markup und umgeht keine Prüfung | Enter ruft dieselbe Funktion wie der Knopf (`addFolderEntry`/`addPatternEntry`, Gate `test_enter_in_either_rule_field_takes_the_way_of_its_button`); Zeile per Klon und Textknoten wie bisher; `grep -c innerHTML php/js/admin.js` = 0; Server-Prüfung in ExclusionService unverändert (`php/lib` ohne Diff). Browserprobe mit `<img src=x onerror=alert(1)>` per Enter folgt im Volltest 46-07 (P-XSS) | ok (Browserbeleg in 46-07) |
| 3 | Zweite Chip-Fassung im Zeilenkopf | nur `p($chipKind)`, `p($chipIcon)`, `p($chipLabel)` aus derselben `$chip()`-Funktion (diff von admin.php), keine neue Datenquelle; Psalm-Taint im Docker-Lauf unten | ok |
| 4 | apt_install.sh: Shell-Einschleusung über Paketnamen oder Umgebung | Paketnamen gegen `^[a-z0-9][a-z0-9.+-]*$`, Zahlenwerte gegen Bereiche, Befehl als Array; Selbsttest-Fälle "refuse" grün; Aufrufstellen ohne `${{ }}` im run-Text (zizmor im Docker-Lauf unten) | ok |
| 5 | Wartezeile in Store upgrade 2b nennt keine Pfade | Zeile nennt Zeilenzahl, Art `kind` und Restbudget (deploy-harp.yml Teil 5) | ok |
| 6 | Store-Texte | nur Links blob/v1.7.0 auf blob/v1.7.1 (`Freigabe Storetext 46-05`), test_store_metadata grün, scan_doc_links prüft die Version gegen `<version>` | ok |

## Bugs

| Nr | Prüfpunkt | Probe | Ergebnis |
|---|---|---|---|
| 7 | Enter bei leerem, doppeltem, zu langem Wert, voller Liste, `*` im Ordnerfeld | gleiche Funktion wie der Knopf, also gleiche Codes und Sätze; Browserprobe P-ENT in 46-07 | ok (Browserbeleg in 46-07) |
| 8 | Enter während einer IME-Komposition, Modifier | Guard `event.isComposing`, `keyCode === 229`, Shift/Strg/Alt/Meta; Mutationen in 46-02 rot; CDP-Probe P-IME in 46-07 | ok (Browserbeleg in 46-07) |
| 9 | Fehlerliste: Zustand genau einmal, Live-Anzahl | Accessibility-Baum am GREEN-Stand (46-LAYOUT-320.md): je Breite gleich oft wie 1.7.0, drei Zähler-ids eindeutig; Gate prüft eine id je Gruppe | ok |
| 10 | Store upgrade 2b: Zeile, die nie geht | Schleife endet am Budget, danach dieselbe rote Prüfung `left=0`; Mutation "Abbruchbedingung" rot (46-04) | ok |
| 11 | apt_install.sh: Hänger, Wackelkontakt | Selbsttest "hang" (drei Zeitlimits, rot) und "flaky" (grün im dritten Versuch) | ok |
| 12 | Gleiche Rennen anderswo in deploy-harp.yml und integration.yml | Suche nach `COUNT(*) FROM oc_findling_queue` (46-04-SUMMARY.md): keine weiteren | ok |

## Performance

| Nr | Prüfpunkt | Probe | Ergebnis |
|---|---|---|---|
| 13 | keydown kostet nichts außer bei Enter | Handler kehrt bei jeder anderen Taste in der ersten Abfrage zurück | ok |
| 14 | Stylesheet | eine Medienregel und eine Grundregel, keine Animation, kein neues Layout über 360 px (Bilder 375 und 1280 gleich 1.7.0) | ok |
| 15 | CI-Laufzeit | Normalfall ein Versuch ohne Pause; schlimmster Fall 380 s statt bis zum Job-Limit; Dauer des Wörterbuch-Schritts aus dem Lauf nach dem Push unter "## Upgrade und Installation" | ok (Laufbeleg nach dem Push) |
| 16 | deploy-harp.yml Größe | 508 633 Byte, Grenze unter 512 000, test_workflow_size grün | ok |

## Upgrade und Installation

- STOPP-Prüfung (46-05): keine Migration (`php/lib/Migration` ohne Diff), kein Schemawechsel (store/schema.sql, store/vectors.sql, index/schema.py ohne Diff). 1.7.0 und 1.7.1 teilen Major und Minor; Kontrolle 2 der Update-Probe ist für den Patch-Schritt erwartungsgemäß übersprungen.
- Lockstep: php `<version>1.7.1</version>`, backend `<version>1.7.1</version>` und `<image-tag>1.7.1</image-tag>`, test_lockstep_versions grün.
- CI-Belege nach dem Push (Update-Probe ab v1.7.0, HaRP-Upgrade 1.5.0 -> 1.7.1, frische Installation, Wartezeile, Wörterbuch über apt_install.sh) folgen nach `Freigabe Push 46-06`.

## Threat-Register 46

| ID | Kategorie | Beleg | Ergebnis |
|---|---|---|---|
| T-46-01 | Tampering | Punkt 1 | mitigated |
| T-46-02 | Repudiation | acht Entscheidzeilen in 46-FREIGABEN.md vor dem ersten Code-Commit 66570830 (Zeilen aus 98bd5713) | mitigated |
| T-46-03 | Tampering | Punkt 2 | mitigated (Browserbeleg 46-07) |
| T-46-04 | Denial of Service | Punkt 7, gleiche too_many-Prüfung, Servergrenzen unverändert | mitigated |
| T-46-05 | Tampering | Punkt 3 | mitigated |
| T-46-06 | Information Disclosure | Bilder in bilder/layout zeigen nur Saat der Dev-Instanz (Gründe, Zahlen, Abhilfen, keine Pfade, Beispielpfade zugeklappt), Sichtprüfung | mitigated |
| T-46-07 | Tampering | Punkt 4 | mitigated |
| T-46-08 | Denial of Service | Punkt 11 und Gate Budget gegen das kleinste Job-Limit | mitigated |
| T-46-09 | Repudiation | Punkt 10 | mitigated |
| T-46-10 | Information Disclosure | Punkt 5 | mitigated |
| T-46-11 | Tampering | Lockstep oben | mitigated |
| T-46-12 | Tampering | STOPP-Prüfung oben | mitigated |
| T-46-13 | Repudiation | Freigabezeilen Version, Changelog, Storetext, README 46-05 vor 03c53f11 und 2dfe0f38 | mitigated |

## Befunde

| ID | Schwere | Befund | Beleg | Status |
|---|---|---|---|---|
| I-46-01-01 | LOW | docs/store-listing.md trug seit 45-14 das gesperrte Wort, test_store_metadata rot auf origin/main (CI sah es nicht, kein paths-Filter auf docs/) | 46-01-SUMMARY.md | behoben 292197c9 nach Owner-Ok |
| I-46-04-01 | LOW | coverage_e2e.sh und smb_acl_measure.sh rufen apt-get ohne Zeitlimit | 46-04-SUMMARY.md | Backlog (Owner-Entscheid) |

Kein offener Befund ab MEDIUM.

## Docker-Gates vor dem Push

Fenster `Freigabe Docker-Fenster 46-06` (4,4 GiB frei, `docker ps -q` leer vorher und nachher, Container nur nacheinander, nach jedem Lauf entfernt).

PHPUnit am Kopf ec1aa605c3575900c5a75f913c7fb50b7ffea541: grün (PHP 8.3.35, OK 1451 tests, 9087 assertions, Untergrenze 28)
php_gates all am Kopf ec1aa605c3575900c5a75f913c7fb50b7ffea541: grün (Psalm-Taint gegen nextcloud/ocp v33.0.9, v34.0.6, v35.0.3 je 0 Funde mit Probe 3; php-cs-fixer 0 Verstöße mit Probe; zizmor keine Funde ab medium mit Probe; actionlint keine Funde mit Probe)

Seit ec1aa605 nur .planning geändert (dieses Dokument). shellcheck der zwei neuen Skripte läuft erst in CI ("Python gates"), lokal nicht installiert.

## Nachtrag 46-06: erster Push

Push durch den Koordinator nach `Freigabe Push 46-06`: origin/main = 0deaf620d8e2d08d94c655ee3c69679d4ce7a13e (ci_head des ersten Pushes; Code gleich ec1aa605). Dazu ein Dispatch von coverage-e2e.yml auf main nach `Freigabe Dispatch coverage-e2e 46-06`. Ein CI-Warter: `scripts/ci/head_green.sh 0deaf620... "Python gates" "PHP and store metadata gates" "HaRP deploy" "Integration" "Resilience" "Multi-arch image" "Security scans" "Workflow security lint"`, Exit 1:

```
45966198418 Coverage end to end failure
45966177853 Security scans success
45966177948 HaRP deploy success
45966177862 Integration success
45966177909 Multi-arch image success
45966177681 Python gates failure
45966177569 PHP and store metadata gates success
45966177559 Resilience success
45966177690 OpenSSF Scorecard success
45966177574 Workflow security lint success
```

Kein Rerun: beide roten Läufe sind Fehler aus 46-04 und keine Netzhänger.

| ID | Schwere | Befund | Beleg | Status |
|---|---|---|---|---|
| V-46-06-01 | MEDIUM (CI rot, blockiert den Kandidaten) | coverage-e2e.yml rief `bash findling-src/scripts/ci/apt_install.sh`, aber findling-src steht dort auf `matrix.src` (Bäume ab v1.6.2 ohne das Skript); alle vier Beine endeten mit exit 127 im Schritt "Install the OCR engine for the backlog images". Der Plan 46-04 verlangte, den Checkout-Pfad dort am Code zu prüfen; das ist unterblieben | Lauf 45966198418, `bash: findling-src/scripts/ci/apt_install.sh: No such file or directory` | behoben per TDD: RED e448e02b (`test_every_call_of_the_script_goes_through_the_head_of_the_repository`: jeder Aufruf des Skripts muss über einen Checkout ohne `ref` oder mit `github.sha` laufen; Positivkontrolle mit dem Text des ersten Pushes), GREEN 2fa545a9 (Aufruf über `findling-harness`, den Kopf-Checkout des Jobs) |
| V-46-06-02 | MEDIUM (CI rot) | python.yml läuft mit `working-directory: backend`; die shellcheck-Zeile nannte `scripts/ci/apt_install.sh` relativ zur Wurzel, shellcheck fand die Dateien nicht (exit 2) | Lauf 45966177681, Schritt "Shell check of the tunnel scripts", `openBinaryFile: does not exist` | behoben per TDD: RED e448e02b (`test_shellcheck_reads_the_two_scripts_from_its_working_directory`, Positivkontrolle mit den Pfaden des ersten Pushes), GREEN 2fa545a9 (`../scripts/ci/...`). shellcheck selbst lief damit in CI noch nie über die zwei Skripte; der erste echte Lauf kommt mit dem nächsten Push |

Belege aus den grünen Läufen am ersten ci_head (gelten weiter, der Fix ändert nur coverage-e2e.yml, python.yml und einen Test):

- Update-Probe (php.yml, Lauf 45966177569): `== candidate: released v1.7.0 to php/ of this checkout, has to pass`, `UPDATE-PROOF ok findling 1.7.0 -> 1.7.1, migrations applied in this run: none, recorded backend version 1.7.0 kept`; `control 2 skipped: v1.7.0 and the candidate 1.7.1 share major and minor, a patch step may keep the recorded version` (erwartet).
- HaRP deploy (Lauf 45966177948, vier Jobs stable33, stable34 amd64 und arm64, stable35 success): `installed_version went from 1.5.0 to 1.7.1`; Store upgrade 2b `step 5: the first delivery came back short, was fetched once more and accepted (POL-02), the row is out of the queue`. Eine Zeile `step 5: N queue row(s) of kind ...` erschien nicht: in diesem Lauf war die Zeile bei der ersten Abfrage schon weg, die Schleife endete sofort. Das Rennen von I-45-12-01 zeigte sich also nicht; die Absicherung liegt im Gate und in den Mutationen (46-04).
- Integration (Lauf 45966177862, success): Wörterbuch über das Skript in allen Jobs mit setup-test-nc, z. B. `team-folder-acl (stable34, 8.2) | ... | apt_install: attempt 1 of 3 ended with exit 0 after 25s` (Spanne 14 s bis 25 s), tesseract `apt_install: attempt 1 of 3 ended with exit 0 after 9s` bis `11s`.
- Lokal am Fix: test_ci_apt_timeouts und Workflow-Tests 77 passed; ruff, ruff format, vulture grün, pyright der Testdatei 0 Fehler; `php_gates_docker.sh workflows` (zizmor, actionlint) grün im Fenster `Freigabe Docker-Fenster 46-06`. Ein lokaler shellcheck-Lauf in einem eigenen Container wurde vom Auto-Modus abgelehnt (nicht freigegebenes Image); shellcheck prüft in CI nach dem nächsten Push.

audited_head und ci_head folgen nach `Freigabe Push 46-06 Fix` und dem grünen Lauf.

## Nachtrag 46-06: coverage-e2e am Fix-Kopf, Rücksprung auf 1.6.2

Lauf 45973279674 (Dispatch nach `Freigabe Dispatch coverage-e2e 46-06 Fix`) auf a66b016c: fünf Beine grün, die tesseract-Installation über `findling-harness/scripts/ci/apt_install.sh` läuft. Rot sind die Beine `upgrade` und `upgrade-rc1` mit genau einer Abweichung je Bein: `rollback_1_6_2=failed (doc_key column 1, index 1, a changed file judged and found by 1.6.2)` ("1 comparisons of variant upgrade differ from the truth"). `drain_incomplete=1` im Bein upgrade ist die bekannte, vom Skript geduldete Lage unter einer 1.6.2-Begleit-App (coverage_e2e.sh Z. ~425) und kein Fehler.

| ID | Schwere | Befund | Beleg | Status |
|---|---|---|---|---|
| V-46-06-03 | LOW (Testerwartung, kein Produktfehler von 1.7.x) | Der Schritt "rollback to 1.6.2" von coverage_e2e.sh (Z. ~2618 bis 2661) tauscht Begleit-App und Container gegen 1.6.2, lässt aber die gespeicherte Version der anderen Hälfte (`findling` / `backend_app_version`) auf 1.7.1 stehen, die der Kopf vorher geschrieben hat. Die 1.6.2-Begleit-App vergleicht Major und Minor dieser gespeicherten Zahl mit ihrer eigenen (D-11, `SearchService::run` -> `ExAppService::driftOnRecord`, v1.6.2 Z. 220 bis 232) und antwortet bei 1.6 gegen 1.7 absichtlich mit keinem Treffer. Aufgefrischt wird die gespeicherte Zahl in 1.6.2 nur über `lockstep()` der Admin-Übersicht (`AdminViewService::overview`, v1.6.2 Z. 787), also wenn die Admin-Seite offen ist; das tut der Schritt nicht. Bis zur Phase 45 war der Kopf 1.6.x: gleiche Minor-Version, kein Drift, deshalb grün (letzter grüner Lauf 43094681914 am 2026-11-11 auf aabc17cc). Mit dem Kopf 1.7.x schlägt die Sperre seit 1.7.0 zu; der Lauf von a66b016c ist der erste coverage-e2e seit dem Wechsel auf 1.7 | Log von 45973279674: sechs Warnungen der Begleit-App 09:50:30 bis 09:51:21 im Abstand der 10-s-Schleife für das Rücksprung-Wort, je `"message":"Findling: the two halves report different versions, answering with no hits"` mit `"data":{"app":"findling","companion":"1.6.2","backend":"1.7.1"}`; die Suche fragt die Schleife erst, wenn state.db die geänderte notiz.txt als `indexed` mit jüngerem `indexed_at` meldet, der 1.6.2-Container hat also gelesen und indexiert (`pass finished, claimed=1 indexed=1`), nur die Suche antwortete leer. Der anschließende Schritt "second update to the head" ist grün (`second_upgrade_rename=ok`), weil die Migration Version001700Date20261123000000 (45-26) die gespeicherte Version beim Minor-Schritt nach oben verwirft | Ursache geklärt; Vorschlag unten, kein Fix gepusht |

Einordnung: Nextcloud unterstützt kein Herabstufen einer App über den Store, ein Rücksprung 1.7 -> 1.6.2 ist ein Handgriff. Auch dann zeigt die echte 1.6.2 genau dieses Verhalten, bis jemand die Admin-Seite öffnet (dann schreibt sie 1.6.2 und die Suche antwortet wieder). 1.7.1 kann daran nichts ändern: nach dem Rücksprung läuft kein Code von 1.7.1 mehr. Der Befund betrifft also den Prüfschritt, der einen Admin-Handgriff auslässt, und keine Funktion von 1.7.0 oder 1.7.1.

Vorschlag (eigener Fix mit Test zuerst, nur nach Owner-Freigabe, coverage-e2e-Lauf mit eigener Freigabe): im Schritt "rollback to 1.6.2" nach `start_backend "${OLD_BACKEND_DIR}"` die Admin-Seite als admin einmal aufrufen (der Weg, den die Produktdoku für diesen Fall nennt: die Seite nennt beide Versionen und schreibt die des Containers fest), danach `backend_app_version` per occ lesen und auf 1.6.2 prüfen (eigene Vergleichszeile, Positivkontrolle: ohne den Aufruf bleibt 1.7.1 stehen und die Drift-Warnung erscheint). Ersatzweise, falls der Seitenaufruf in der Harness ohne Sitzung nicht geht: `occ config:app:delete findling backend_app_version`, wie es die Migration von 1.7 beim Schritt nach oben tut; dann prüft der Schritt aber nicht mehr den Weg, den ein Admin geht. Zusätzlich ein Satz in docs/admin-page.md (Abschnitt Versionen der beiden Hälften): nach einem Rücksprung über eine Minor-Grenze die Admin-Seite einmal öffnen.

Fix V-46-06-03 nach Owner-"Ja" (Weg 1, vor dem Tag): RED e16c2b56 (`test_the_rollback_refreshes_the_recorded_version_before_it_tests`, Positivkontrolle: Schritt ohne Aufruf und Aufruf nach der Änderung je rot), GREEN 22e13f0a (coverage_e2e.sh: nach dem Start von 1.6.2 einmal `overview` der Admin-Seite, dann `backend_app_version` per occ lesen und als Vergleichszeile "rollback: version of the other half the admin overview of 1.6.2 records" gegen 1.6.2 prüfen, alles vor der Änderung von notiz.txt; `bash -n` grün), Doku 1a0abda0 (docs/admin-page.md, Absatz "Versionen der beiden Hälften"). Lokal: ruff, ruff format, pyright (0 Fehler), vulture grün; volle Python-Suite 7452 passed, 305 skipped (838 s, allein). Beleg in echter CI folgt mit dem einen freigegebenen coverage-e2e-Lauf nach dem Push.

## Nachtrag 46-06: grüner Kandidat

Push durch den Koordinator: origin/main = 6003b35352bb5be89ec0e85a1319129b209debc7, dazu genau ein coverage-e2e-Lauf 45995128241. Dazwischen hatte die Hauptsitzung den PHP-Baumhash nachgezogen (ce8a5021, PHP_TREE_HASH_TODAY 7ce0ad5c nach dem admin.php-Fix von 46-03; Python gates auf a66b016c war daran rot) und auf 1180c9a4 alle Pflichtläufe grün gefahren. Ein CI-Warter auf 6003b353:

```
45995128241 Coverage end to end success
45995129242 HaRP deploy success
45995129221 OpenSSF Scorecard success
45995129443 Resilience success
45995129267 Multi-arch image success
45995129320 Python gates success
45995129316 Security scans success
45995129220 Integration success
exit 0
```

"PHP and store metadata gates" und "Workflow security lint" liefen auf 6003b353 nicht (paths-Filter: seit a66b016c keine Änderung unter php/ und .github/, `git diff --stat a66b016c 6003b353 -- php .github` leer); beide sind auf a66b016c grün (45973260375 Workflow security lint; PHP and store metadata gates zuletzt mit Code-Änderung unter php/ auf 0deaf620, 45966177569, seither php/ unverändert).

Belege coverage-e2e 45995128241 (alle sieben Beine grün):

- Bein upgrade: `compare rollback: version of the other half the admin overview of 1.6.2 records: expected 1.6.2, shown 1.6.2, equal`, `rollback_1_6_2: ok (doc_key column 1, index 1, a changed file judged and found by 1.6.2)`, `second_upgrade_rename: ok (122 living rows, bound 660 s)`.
- Bein upgrade-rc1: dieselbe Vergleichszeile equal, `rollback_1_6_2: ok`, `second_upgrade_rename: ok (123 living rows, bound 660 s)`.
- tesseract über `findling-harness/scripts/ci/apt_install.sh` in allen Beinen: `apt_install: attempt 1 of 3 ended with exit 0 after 4s` bis `22s`.
- V-46-06-01, V-46-06-02 und V-46-06-03 damit in echter CI belegt; shellcheck der zwei Skripte in "Python gates" grün.

audited_head (46-06, ersetzt): 1a0abda0
ci_head (46-06, ersetzt): 6003b353
status_46_06: passed

Bedingung `git diff --quiet 1a0abda0 6003b353 -- . ':!.planning'` erfüllt (Code gleich).

## Nachtrag 46-07

### Fix-Durchlauf

Fixes aus der Abnahme 46-07 und #63, alle Test zuerst, Freigaben in 46-FREIGABEN.md (Hilfesatz, Ablehnungsmeldung, Name-Beispiel, #63, Changelog-Punkte vier und fünf).

Delta-Audit `git diff 1a0abda0 a3c94c16 -- . ':!.planning'` (34 Dateien, +241/-48): Code außerhalb von Tests, Katalogen und Doku nur in zwei Dateien:

- `backend/src/findling/api/snippets.py`: `wire_snippets` lässt Ausschnitte mit leerem Text weg. Kein neuer Eingang, keine neue Ausgabe, nur weniger Einträge in der bestehenden Antwort.
- `php/lib/Service/ExAppService.php` (`filterSnippets`): leerer Text wird übersprungen, Regex mit `\z` verankert (Audit-Gate test_phase36_audit grün). Kein neuer Eingang, Zähler für fehlerhafte Antworten unverändert.
- Kataloge `php/l10n/*` und `docs/l10n-*`: nur übersetzte Beispiele in bestehenden Meldungen, Platzhalter unverändert (test_admin_ui_contract mit Zuordnungstabelle).
- `.github` seit 6003b353 unverändert, daher kein Lauf "Workflow security lint" nötig.

Befund: keine neue Angriffsfläche. Volltest lokal 7429 passed, 333 skipped (Docker aus), ruff, ruff format, vulture, pyright 0 Fehler. PHPUnit RED an 7d365b34, GREEN am Kopf; die Verankerung `\z` in CI geprüft.

Push nach `Freigabe Push #63 46-07`, origin/main = a3c94c1635b2fe13436394524ed3bb3aa05792b5. Ein CI-Warter über alle Workflows, alle grün:

- 46076437121 Python gates success
- 46076437005 PHP and store metadata gates success
- 46076437035 HaRP deploy success
- 46076437149 Integration success
- 46076437150 Resilience success
- 46076437214 Multi-arch image success
- 46076437153 Security scans success
- 46076437084 OpenSSF Scorecard success

Gemeinsame Abnahme 46-07 Schritte 1 bis 3 ohne Einwand, Sichtprüfung der angeglichenen Meldungen in derselben Sitzung; Abnahmezeile in 46-FREIGABEN.md.

audited_head: a3c94c1635b2fe13436394524ed3bb3aa05792b5
ci_head: a3c94c1635b2fe13436394524ed3bb3aa05792b5
status_46_07: passed

## Nachtrag Threats vor dem Tag

Stand: 2026-11-28 (23:43 UTC am 27.11.), Plan 46-10 Task 1. Geprüfter Stand: Tag-Kopf K = a3c94c1635b2fe13436394524ed3bb3aa05792b5 (46-ABNAHME.md `Tag-Kopf:`), alle Proben mit `git show a3c94c16:<pfad>`, nie mit `git show v1.7.1`. Kein Tag v1.7.1 (`git rev-parse -q --verify refs/tags/v1.7.1` leer, `git ls-remote --tags origin v1.7.1` leer). Code von K gleich origin/main 7806e83a und gleich HEAD (`git diff --quiet a3c94c16 origin/main -- . ':!.planning'` rc 0). Läufe lesend per `gh run view <id> --json conclusion,headSha` geprüft: 46076437121, 46076437005, 46076437035, 46076437149, 46076437150, 46076437214, 46076437153, 46076437084 je success auf headSha a3c94c16; 45973260375 (Workflow security lint) success auf a66b016c, `.github` seit a66b016c ohne Diff zu K; 46083361339 (Signatur-Probe) success auf 7806e83a.

Eigene Proben, unabhängig vom Muster der Umsetzung (B8), Hilfsskripte im Scratchpad, nicht committet:

- Q1 Katalogprobe: eigenes Skript über die 18 Dateien `php/l10n/*` aus K (JSON parsen, nicht die Regex des Gates): 3663 Werte, 0 mit `<`, `>` oder HTML-Entity, die nicht schon im msgid stehen; 0 Abweichungen der Platzhalter (`%s`, `%1$s`, `%n`, `{name}`) gegen den msgid (Plural gegen die Pluralform); .json und .js je Sprache inhaltsgleich. Positivkontrolle: Kopie von de.json/de.js mit `<img src=x onerror=1> %s` im Wert der Wildcard-Meldung: je 1 Fund, also rot.
- Q2 Template und Skript am Kopf: `git show K:php/js/admin.js | grep -c innerHTML` = 0; dazu 0 Treffer für `insertAdjacentHTML|outerHTML|document.write|.html(|eval(|new Function`; ganzes `php/templates/admin.php` an K ohne `print_unescaped`, `echo`, `<?=`; die 12 seit v1.7.0 hinzugefügten Templatezeilen geben nur über `p(` aus. Meldungen landen über `fieldError` -> `text()` -> `element.textContent` (admin.js Z. 310 bis 318, 1363), Zeilen über Klon und `label.textContent` (Z. 1396 bis 1420).
- Q3 apt_install.sh von K im Scratchpad mit `APT_GET=true` aufgerufen: `wngerman;touch /tmp/x`, `$(id)`, `Wngerman`, `-o`, `a b` je rc 2 (abgewiesen vor jedem Aufruf), `tesseract-ocr` rc 0 (Positivkontrolle), `APT_INSTALL_TIMEOUT=999` rc 2, `APT_INSTALL_ATTEMPTS=4` rc 2. Befehl als Array (`read -r -a`, `"${apt_get[@]}"`), `set -euo pipefail`. Alle fünf Aufrufstellen (action.yml Z. 399, coverage-e2e.yml Z. 181, integration.yml Z. 643, 1355, 2451) nennen feste Paketnamen, kein `${{ }}` im run-Text.
- Q4 Job-Limits: eigenes Skript (yaml, nicht die Funktion des Gates) über alle Workflows an K, Jobs mit setup-test-nc (register-exapp nicht false, Standard 'true') oder Aufruf des Skripts: 10 Jobs, kleinstes Limit 25 min (integration.yml team-folder-acl). Schlimmster Fall des Skripts mit Standardwerten inklusive `--kill-after=10`: 3 x 130 s + 2 x 10 s = 410 s, unter der Hälfte von 25 min (750 s). Hinweis: der Gate rechnet ohne `--kill-after` (380 s), das ändert das Urteil nicht.
- Q5 deploy-harp.yml an K, Store upgrade 2b Teil 5 (Z. ~4537 bis 4575) gelesen: zweite Schleife `while [ "$(date +%s)" -lt "${deadline}" ]` mit derselben `deadline` wie Teil 5, danach unverändert `left=$(q ...)` und `[ "${left}" != "0" ]` -> `exit 1`; die Wartezeile (Z. 4560) nennt nur Zeilenzahl, `kind` aus `MAX(kind)` und Restsekunden.
- Q6 Zeitfolge Freigabe gegen Push aus `git reflog show --date=iso origin/main` (lokale Pushes) und `createdAt` der Läufe: 0deaf620 08:30:17 UTC (Freigabe 08:30), a66b016c 09:23:06 (09:23), 1180c9a4 11:07:34 (11:07), 6003b353 12:00:58 (11:44), b9a501c0 14:53:52 (14:53), a3c94c16 22:24:16 UTC (Lauf 46076437121 createdAt 22:24:19Z), 7806e83a 23:31:08 (23:30); Dispatches 45966198418 08:30:28, 45973279674 09:23:16, 45995128241 12:01:01, 46083361339 23:35:39 (Freigabe Signatur 23:35). Alle geprüften Läufe `attempt` 1, kein Rerun.

| ID | Kategorie | Beleg | Ergebnis |
|---|---|---|---|
| T-46-01 | Tampering | Q1 (0 Markup, 0 Platzhalter-Abweichung über alle 18 Kataloge an K, Positivkontrolle rot); Hilfesatz an K nur über `p($l->t(...))` (admin.php Z. 1597), Q2 | closed |
| T-46-02 | Repudiation | `git log -S"Entscheid E-46-08 46-01"` -> 98bd5713 (07:17:10 +01:00), Ahne des ersten Code-Commits 66570830 (07:19:38 +01:00), `git merge-base --is-ancestor` rc 0; acht Zeilen E-46-01 bis E-46-08 in 46-FREIGABEN.md | closed |
| T-46-03 | Tampering | Q2 (innerHTML 0 an K, Pflichtbeleg); `addOnEnter` ruft dieselbe `addFolderEntry`/`addPatternEntry` wie der Knopf (admin.js Z. 1447 bis 1458, 1503 f., 1569 f.); Server-Prüfung: `git diff v1.7.0 K -- php/lib/Service/ExclusionService.php` leer; Browserprobe P-XSS in 46-VOLLTEST.md (DE, EN, FR, zh_TW) an 029d7307, admin.js-Blob 4912b01a dort gleich K | closed |
| T-46-04 | Denial of Service | `too_many` vor jedem `addRow` in beiden Funktionen (admin.js Z. 1491 f., 1559 f.); `MAX_PREFIXES = 64`, `MAX_PATTERNS = 32` und die Prüfungen Z. 292, 394 in ExclusionService.php an K, Datei seit v1.7.0 ohne Diff | closed |
| T-46-05 | Tampering | Chip an K nur `p($chipKind)`, `p($chipIcon)`, `p($chipLabel)` aus `$chip()` (admin.php Z. 844, 888 bis 907); Q2; Psalm-Taint gegen OCP v33.0.9, v34.0.6, v35.0.3 je success im Lauf 46076437005 auf headSha a3c94c16 (Jobliste per `gh run view --json jobs`) | closed |
| T-46-06 | Information Disclosure | eigene Sichtprüfung `bilder/layout/green-de-1280-light.png`: nur Gründe, Zahlen, Abhilfen, Beispielpfade zugeklappt; Saat der Dev-Instanz | closed |
| T-46-07 | Tampering | Q3 (Paketnamenprüfung im Skript am Kandidaten, Verhalten mit Positivkontrolle, Pflichtbeleg); shellcheck im Lauf 46076437121 (Python gates) success an K; zizmor im Lauf 45973260375 success, `.github` seither ohne Diff | closed |
| T-46-08 | Denial of Service | Q4 (eigenes Skript: 410 s gegen 750 s); `APT_INSTALL_ATTEMPTS` 1 bis 3, `APT_INSTALL_TIMEOUT` 1 bis 300 erzwungen (Q3); Selbsttest "hang"/"flaky" in Python gates 46076437121 success | closed |
| T-46-09 | Repudiation | Q5 (Schleife endet an der Frist, danach unveränderte rote Prüfung `left`); Mutation M3 "Abbruchbedingung" rot laut 46-04-SUMMARY.md Z. 51; Gate in Python gates an K success | closed |
| T-46-10 | Information Disclosure | Q5: Wartezeile deploy-harp.yml Z. 4560 an K nennt Zeilenzahl, kind und Restsekunden, keinen Pfad und keine ID | closed |
| T-46-11 | Tampering | an K: php/appinfo/info.xml `<version>1.7.1</version>`, backend/appinfo/info.xml `<version>1.7.1</version>` und `<image-tag>1.7.1</image-tag>`; test_lockstep_versions in Python gates 46076437121 success | closed |
| T-46-12 | Tampering | `git diff --name-only v1.7.0 K -- php/lib/Migration backend/src/findling/store/schema.sql backend/src/findling/store/vectors.sql backend/src/findling/index/schema.py` leer; jüngste Migration an K und v1.7.0 gleich Version001700Date20261123000000 | closed |
| T-46-13 | Repudiation | `git log -S` -> Freigabe Version, Changelog, Storetext, README 46-05 in b22b123d (08:48:01 +01:00), Ahne von 03c53f11 (08:51:59) und 2dfe0f38; dazu Changelog 46-07 5f6dd853 vor ec1a008d und Changelog #63 46-07 74bee93b vor c35579d6, je `merge-base --is-ancestor` rc 0 | closed |
| T-46-14 | Repudiation | Q6: Pushes 0deaf620, a66b016c, 1180c9a4, 6003b353 je nach ihrer Freigabezeile (Push 46-06, Fix, Baumhash, Rücksprung); die Zeilen liegen in den gepushten Commits (`git log -S`: 0deaf620, a66b016c, 1180c9a4, ba0e0ad3) | closed |
| T-46-15 | Tampering | `gh run view 45966198418` und `45966177681` (die roten Läufe aus 46-04): `attempt` 1, kein Rerun; Fix per TDD (V-46-06-01, V-46-06-02), grün in 45995128241 und 45995129320 laut 46-AUDIT.md | closed |
| T-46-16 | Information Disclosure | eigene Sichtprüfung `bilder/volltest/de-1280-light.png` und `probes-p-ent-de.png`: nur Saat (Fuellordner45/NN, P46Ordner, *.p46muster), Konto "A" der Dev-Instanz | closed |
| T-46-17 | Tampering | Mitigation verlangt SHA-256 der ausgelieferten admin.js und admin.css gegen audited_head im Bericht. 46-VOLLTEST.md enthält keinen SHA-256 (grep über die Phasendokumente: 0 Treffer), nur "php/ des Arbeitsbaums am Kopf, in den Container gemountet" (Stand 029d7307). Eigene Probe am Repo: Blobs admin.js 4912b01a, admin.css 469ab3f6, admin.php aad0ccfd an 029d7307, 1a0abda0 und K gleich; SHA-256 an K: admin.js 88b23b75d8b79d5365033068de194120fce6d7dc0dee0ef45d2cbf912fecab58, admin.css be22a5a0b36e5250bea8c08df6749e3c14ab99bfc732c372b63f4f544d44ec78. Was die Instanz ausgeliefert hat, ist damit nicht belegt (nur indirekt über die IME-Positivkontrolle, die eine Änderung im Arbeitsbaum live zeigte). Die nach 1a0abda0 geänderten Katalogwerte sah der Owner in der Abnahme ohne Stand-Nachweis | offen |
| T-46-18 | Repudiation | Q6: Push von a3c94c16 um 22:24:16 UTC (reflog, Lauf 46076437121 createdAt 22:24:19Z). Die Zeile `Freigabe Push #63 46-07: "Go" (2026-11-27 22:40, ...)` nennt 22:40 UTC, also 16 Minuten nach dem Push, und kam erst mit b2fd6518 (23:20 UTC) ins Repo. Alle übrigen Push- und Dispatch-Zeilen liegen vor oder in derselben Minute wie ihre Aktion. Eine Zeile `Freigabe Push 46-07 Fix` gibt es nicht; `Freigabe Push 46-07` (14:53) deckt nur den Push b9a501c0. Freigabe vor dem Push damit nicht schlüssig belegt | offen |
| T-46-19 | Tampering | 46-ABNAHME.md Tag-Kopf = audited_head = ci_head = a3c94c16; acht Läufe success auf headSha a3c94c16 (oben); Code K gleich origin/main (rc 0); Workflow security lint grün auf a66b016c, `.github` seither ohne Diff | closed |
| T-46-20 | Repudiation | Q6: Push 7806e83a 23:31:08 UTC nach `Freigabe Push 46-08` (23:30, Zeile im gepushten Commit 7806e83a); Dispatch 46083361339 23:35:39 nach `Freigabe Signatur 46-09` (23:35); coverage-e2e-Dispatches je nach ihrer Zeile | closed |
| T-46-21 | Information Disclosure | `git diff --quiet v1.7.0 K -- .github/workflows/release.yml` rc 0; release.yml an K: `environment: release` (Z. 91), Schlüssel nur über `env:` aus `secrets.` (Z. 323, 378, 444), nicht im run-Text, kein `set -x` | closed |
| T-46-22 | Spoofing | Lauf 46083361339 headSha 7806e83a; `git diff --quiet a3c94c16 7806e83a -- . ':!.planning'` rc 0, Diff nur vier Dateien unter .planning | closed |

Nach dem Release nachzuprüfen (entstehen in 46-11 und 46-12, Prüfung im Nachtrag von 46-12):

- T-46-23 Tag auf falschem Kopf
- T-46-24 unsignierte Pakete im Store
- T-46-25 Store-Token
- T-46-26 Veröffentlichung ohne Owner
- T-46-27 Store-API-Sperre durch zu viele Abfragen
- T-46-28 Kommentar ohne Freigabe
- T-46-29 interne Details oder @-Erwähnung im Kommentar

### Änderungen nach dem ersten Audit (1a0abda0..a3c94c16 ohne .planning)

- `backend/src/findling/api/snippets.py` `wire_snippets`: filtert nur (`one.text.strip() != ""`), Modell `Snippet` und Antwortform unverändert, kein neuer Eingang. Kein Threat.
- `php/lib/Service/ExAppService.php` `filterSnippets`: die neue Prüfung `preg_match('/^\s*\z/u', $text) === 1` steht nach der Prüfung auf angefragte IDs (`$wanted`), nach `is_string` und nach `PlainText::bounded`; sie kann nur Einträge weglassen, nie einen zulassen. Liefert `preg_match` bei ungültigem UTF-8 `false`, läuft der Eintrag in die bisherigen Prüfungen weiter (kein Umgehen). Ein weggelassener Ausschnitt führt zur Pfadzeile, die es seit 1.7.0 für jeden Treffer ohne Ausschnitt gibt (Provider.php an K ohne Diff). Am Rand: Python `strip()` kennt Unicode-Leerraum, `\s` mit `/u` ohne UCP nur ASCII; Folge höchstens eine Zeile aus Sonderleerzeichen statt des Pfads, keine Sicherheitsfrage. Kein Threat.
- `php/l10n/*` (14 Dateien, 28 Zeilen geändert): Q1 an K und eigener Filter über die 28 hinzugefügten Zeilen von `git diff -U0 1a0abda0 K -- 'php/l10n/*'`: 0 Zeilen mit `<`, `>`, `{`, `}`, `%`, `&`, `$`; nur die Beispielwörter vor `*` geändert (Sicherung*, Copia*, Nombre*, Nom*, Sauvegarde*, Nome*, Naam*, Back-up*, Cópia*, 名稱*, 備份*). Ausgabe in admin.js über `refusalSentence` -> `fieldError` -> `textContent`; `refusalSentence` ersetzt `%s` nur bei too_long/too_many, die geänderten Meldungen (wildcard, no_wildcard) tragen keinen Platzhalter. Kein Threat.

Ergebnis: kein neuer Threat (keine Zeile T-46-30). 20 von 22 closed, offen T-46-17 und T-46-18. Der Tag bleibt gesperrt, bis beide geschlossen oder per `Akzeptanz Threat T-46-xx 46-10: ...` akzeptiert sind.

## Nachtrag Docker-Fenster T-46-17 (2026-11-28, Freigabe `Freigabe Docker-Fenster T-46-17 46-10` 23:48 UTC)

- RAM nach Neustart 8,49 GiB frei, nach Start Docker Desktop 6,28 GiB frei (Schwelle 4 GiB eingehalten).
- Arbeitsbaum: `git diff --stat a3c94c16 HEAD -- php/` leer, `git status --short php/` leer (HEAD 4b6cda07, nur .planning nach K).
- Stack findling-vt per `docker start findling-vt-backend findling-vt` (gleiche Container wie in der Abnahme). Mount laut `docker inspect`: `C:\Users\Student\nextcloud-search\php` -> `/var/www/html/custom_apps/findling`. `status.php` 200, Nextcloud 34.0.3, `occ app:list`: findling 1.7.1.
- Ausgeliefert per HTTP (`curl http://localhost:8090/custom_apps/findling/...`, Code 200) gegen `git show a3c94c16:...`:
  - js/admin.js 88b23b75d8b79d5365033068de194120fce6d7dc0dee0ef45d2cbf912fecab58 = K
  - css/admin.css be22a5a0b36e5250bea8c08df6749e3c14ab99bfc732c372b63f4f544d44ec78 = K
- Kataloge: 18 Dateien unter `l10n/` (9 .js, 9 .json) per `docker exec sha256sum` im Container gegen K: 0 Abweichungen. Die 9 .js zusätzlich per HTTP: alle gleich K. Die .json liefert Nextcloud per HTTP nicht aus (404-Seite); ein erster Vergleich über HTTP zeigte darum 9 Scheinabweichungen, Ursache geklärt (Hash der 404-Seite), Gegenprobe im Container sauber. Schlüsselzahl de 387, fr 387.
- Stack um 2026-11-28T00:01:07Z gestoppt (`docker stop`, kein down, Volumes bleiben).
