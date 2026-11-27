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
