# Abgleich mit den Nextcloud-Sicherheitsrichtlinien (Findling)

Anhang zum Sicherheitsdossier. Stand: 16.11.2026, geprüft gegen die
Security guidelines des Nextcloud 35 Developer Manual
(developer_manual/prologue/security.html) und die App-Store-Regeln
(app_publishing_maintenance/publishing.html). Prüfweg: Code-Sweep über
php/ und backend/src am 16.11.2026 (shell_exec, proc_open, passthru,
eval, rohes SQL, print_unescaped, innerHTML, os.system: 0 Treffer,
Positivkontrolle getQueryBuilder gefunden) plus bestehende CI-Gates.

## Developer-Guidelines

| Regel | Stand | Beleg |
|---|---|---|
| SQL-Injection: nur vorbereitete Abfragen | erfüllt | Alle DB-Zugriffe über IQueryBuilder (php/lib/Db/*), kein rohes SQL im Sweep |
| XSS: Templates und DOM sanieren | erfüllt | PHP-Templates nur mit p(), kein print_unescaped; Admin-JS ohne innerHTML-Einspeisung von Nutzerdaten (Sweep) |
| Clickjacking: X-Frame-Options nicht entfernen | erfüllt | Standard-Header des Servers bleiben unangetastet, keine eigene Header-Manipulation |
| Code execution / file inclusion: kein eval/include mit Eingaben | erfüllt | Sweep 0 Treffer; Uploads landen nie im Webroot (Index liegt im ExApp-Volume) |
| Directory traversal: Files API statt Pfadbau | erfüllt | Dateizugriffe über IRootFolder/Node-API; Container erhält Inhalte nur über das PHP-Gateway nach Rechteprüfung |
| Shell injection: escapeshellarg bei Shell-Aufrufen | erfüllt (n. a. in PHP) | PHP ruft keine Shell (Sweep); Python-Unterprozesse (tesseract) mit Argumentlisten ohne Shell |
| Auth bypass / privilege escalation | erfüllt | Endfilterung der Treffer in PHP als einzige Sicherheitsgrenze (getUserFolder/getFirstNodeById); Gruppenordner-ACL über actAs |
| Sensitive data exposure | erfüllt | Index und Zustand im ExApp-Volume, nie im Webroot; keine Pfade/Dateinamen in Logs (Gate in CI) |
| CSRF: jede Anfrage geschützt | erfüllt | App-Framework-Controller mit Standard-CSRF-Prüfung; keine NoCSRFRequired-Ausnahmen ohne Begründung |
| Unvalidated redirects | n. a. | Die App leitet nicht um |
| CORS | n. a. | Keine CORS-Freigaben gesetzt |

## Store-Regeln (Auszug Legal/Security + Respect the users)

| Regel | Stand | Beleg |
|---|---|---|
| AGPL-3.0-or-later | erfüllt | LICENSE, info.xml beider Apps |
| Kein "Nextcloud" im Namen | erfüllt | findling / findling_backend |
| Zeitnahe Reaktion auf Sicherheitsmeldungen | erfüllt | SECURITY.md (GitHub private reporting + Mail, Antwort in 7 Tagen); Praxisbeleg: 1.6.5-Security-Release CVE-2026-126360 |
| Sauberes Auf-/Abräumen bei Deinstallation/Up-/Downgrade | erfüllt | Migrationen + occ findling:purge; Update-Gate "Store update in one process" in CI seit 1.6.4 |
| Keine Daten an Dritte, Datenschutz | erfüllt | Kein Inhalt verlässt den Server (Owner-Regel, CI-belegt: Offline-Beweis im Store-Text); einzige Ausnahme einmaliger Modell-Download mit festem sha256 |
| Kontaktweg für Nutzer | erfüllt | GitHub Issues, SECURITY.md, Store-Seite |

## Über die Richtlinien hinaus

- Threat-Audit je Phase (SECURITY.md-Dateien in .planning/phases/*), fail-closed als Grundlinie
- Signatur-Pinning der Releases (CERT_PUBKEY_SHA256 in release.yml), Lock-Dateien erzwungen
- OpenSSF Scorecard und Security scans in CI

## Offene Punkte

- Keine. Wiedervorlage: Abgleich bei jedem Major-Guideline-Update der Doku.
