---
phase: 34-umstiegsweg
plan: 02
subsystem: migration-docs
tags: [docs, migration, fulltextsearch, gate]
requires: [34-01]
provides:
  - "docs/migrate-from-fulltextsearch{,.en,.fr}.md nach abgenommenem Wortlaut, Platzhalter durch 8090-Befunde ersetzt"
  - "backend/tests/test_migration_path.py: Seiten, Formel, Verbot de/en/fr mit Positivkontrolle, Links, Ehrlichkeit; scan_phase35_wording() für 34-04"
  - "34-02-NACHWEIS.md: Abschalt-Schritte auf NC 34.0.3 durchgespielt, A1/A2/A3 bestätigt"
affects: [34-04, 34-05, 34-06]
tech-stack:
  added: []
  patterns: ["Textgate über Verzeichnis-Reichweite mit Untergrenze und Positivkontrolle", "Satzgrenzen-Scan für Behauptungen über Fremd-Apps"]
key-files:
  created:
    - .planning/phases/34-umstiegsweg/34-02-NACHWEIS.md
    - backend/tests/test_migration_path.py
    - docs/migrate-from-fulltextsearch.md
    - docs/migrate-from-fulltextsearch.en.md
    - docs/migrate-from-fulltextsearch.fr.md
  modified: []
decisions:
  - "34-02: Tabellenreste nach occ app:remove belegt (oc_fulltextsearch_index, oc_fulltextsearch_ticks, Einträge in oc_migrations); die Seite nennt den Aufräumweg DROP TABLE x2 plus DELETE FROM oc_migrations mit Warnhinweis Datensicherung"
  - "34-02: Das Gate verbietet auch die en/fr-Platzhalter ([Evidence, [Preuve) und die Markierung [O5], nicht nur [Beleg"
metrics:
  duration: "ca. 35 min Arbeit plus 18 min volle Suite und CI"
  completed: 2026-10-19
  tasks: 3
  files: 5
---

# Phase 34 Plan 02: Umstiegs-Seiten und Gate Summary

Drei Umstiegs-Seiten de/en/fr zeichengleich nach dem abgenommenen Wortlaut, die Platzhalter durch Befunde eines Durchlaufs auf 8090 ersetzt (reset ohne Plattform, Tabellenreste samt Aufräum-SQL), gehalten durch das neue Gate `test_migration_path.py` (Verbot "einzige OCR" und en/fr-Entsprechungen über die O3-Reichweite mit Positivkontrolle `docs/performance.md`).

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | Abschalt-Schritte auf 8090 durchspielen und protokollieren | d5258548 | 34-02-NACHWEIS.md |
| 2 | Gate rot schreiben (TDD RED) | 0e3af73e | backend/tests/test_migration_path.py |
| 3 | Drei Seiten, Gates grün (GREEN), Push, CI | 64fb4146 | docs/migrate-from-fulltextsearch{,.en,.fr}.md |

## Nachweis (Kern)

- **A3 bestätigt:** fulltextsearch 34.0.2 und files_fulltextsearch 34.0.1 aus dem Store auf NC 34.0.3 installiert; Voraussetzung auf der Dev-Instanz war ein vorübergehendes `chown www-data` auf `custom_apps` (gehört wegen des Bind-Mounts `root`), am Ende zurückgesetzt.
- **A2 bestätigt:** `occ fulltextsearch:reset` ohne Plattform endet nach beiden Bestätigungen (`y`, dann wörtlich `reset ALL ALL`) mit "Admin have not selected any IFullTextSearchPlatform", exit 1, ohne Stacktrace, löscht nichts. Interaktiv-Falle: `--no-interaction` gibt `aborted.` mit exit 0 aus und tut nichts.
- **A1 bestätigt:** nach `app:disable` und `app:remove` ("uninstall steps executed") bleiben `oc_fulltextsearch_index`, `oc_fulltextsearch_ticks`, sieben Einträge in `oc_migrations` und die `oc_appconfig`-Schlüssel. Aufräum-SQL auf 8090 gefahren, Neuinstallation danach als Gegenprobe erfolgreich. Der verwaiste Hintergrundjob verschwindet von selbst (`JobList::buildJob()`).
- Nur aus Quellen (auf 8090 nicht ausführbar): systemd-Unit (Wiki `Basic-Installation.md` 49-66), AIO (`entrypoint.sh:1049-1115`, am 19.10. neu gelesen, Zeilen bestätigt), Elasticsearch-Index und Pipeline (`IndexService.php:114-128`, bestätigt). Kein Elasticsearch-Container (D-34-02).
- Store-Stand vor dem Schreiben erneut abgefragt: unverändert gegenüber 34-WORTLAUT.

## TDD Gate Compliance

RED (`0e3af73e`), vor den Seiten:

```
FAILED tests/test_migration_path.py::test_pages_exist_with_switch_line_and_formula
FAILED tests/test_migration_path.py::test_pages_links_resolve_and_are_https
FAILED tests/test_migration_path.py::test_honesty_pages_keep_the_leitplanken
3 failed, 9 passed
  (Befunde: docs/migrate-from-fulltextsearch.md: missing, .en.md: missing, .fr.md: missing)
```

Selbsttests und Bestands-Scan dabei grün (`-k "test_forbidden_ or test_positive_control_ or test_mutated_"`: 9 passed). Reichweite 64 Textdateien (Untergrenze 60). Unabhängige Gegenprobe: `grep -c "einzige OCR-Seite" docs/performance.md` = 1, Gate meldet dort nichts.

GREEN (`64fb4146`): `test_migration_path.py` 12/12 grün; zusammen mit `test_public_artifacts.py` und `test_store_metadata.py` 158 passed. Volle Suite 5717 passed, 252 skipped (17:51 min); ruff, ruff format, pyright (latest, 0 Fehler), vulture, `reuse lint` grün. Kein PHP angefasst.

## Abweichungen vom abgenommenen Wortlaut (für die Owner-Abnahme in 34-05)

Nur die vorgesehenen Stellen, per `diff` gegen 34-WORTLAUT Abschnitt A belegt:

1. Markierung `[O5]` in allen drei Sprachen entfernt (laut Owner-Abnahme O5).
2. Schritt 3, Platzhalter ersetzt durch (de): "Mit `--no-interaction` bricht der Befehl ohne Rückfrage ab und löscht nichts. Ohne eingerichtete Plattform endet er nach der Bestätigung mit dem Fehler `Admin have not selected any IFullTextSearchPlatform` und löscht ebenfalls nichts (geprüft mit Nextcloud 34.0.3 und fulltextsearch 34.0.2)." en/fr sinngleich.
3. Schritt 5, Platzhalter ersetzt durch (de): "Die Tabellen `oc_fulltextsearch_index` und `oc_fulltextsearch_ticks` und ihre Einträge in `oc_migrations` bleiben dabei liegen (geprüft mit Nextcloud 34.0.3). Wer sie entfernen will, legt vorher eine Datensicherung der Datenbank an und führt dann diese Anweisungen aus; `oc_` ist das Standard-Präfix, eine Instanz mit anderem Präfix setzt ihres ein:" plus SQL-Block (`DROP TABLE` x2, `DELETE FROM oc_migrations WHERE app = 'fulltextsearch';`) und "Eine spätere Neuinstallation von fulltextsearch legt die Tabellen wieder an." en/fr sinngleich.

Der Entwurf vermutete in Schritt 3 "ohne erreichbare Plattform"; gefahren wurde "ohne eingerichtete Plattform". Die Seite sagt nur das Gefahrene.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] custom_apps auf der Dev-Instanz nicht beschreibbar**
- **Found during:** Task 1
- **Issue:** `occ app:install` scheiterte mit "Cannot write into apps directory" (Verzeichnis gehört `root` wegen des Bind-Mounts).
- **Fix:** vorübergehend `chown www-data:www-data /var/www/html/custom_apps` (nur das Verzeichnis), am Ende zurück auf `root:root`.
- **Commit:** keiner (nur Instanzzustand, im Nachweis protokolliert)

**2. [Rule 2 - Critical] Gate prüft auch en/fr-Platzhalter und [O5]**
- **Found during:** Task 2
- **Issue:** Der Plan nennt nur "[Beleg"; die en/fr-Entwürfe tragen "[Evidence"/"[Preuve".
- **Fix:** `PLACEHOLDERS` enthält alle vier Formen.
- **Commit:** 0e3af73e

**3. [Rule 1 - Bug] Write-Werkzeug hat \u-Escapes in echte Zeichen verwandelt**
- **Found during:** Task 2
- **Issue:** Der Modulquelltext war nicht mehr ASCII (ruff RUF001 auf dem Halbgeviertstrich).
- **Fix:** Nicht-ASCII-Zeichen per Skript zurück in `\uXXXX`-Escapes; Verify-Block prüft ASCII.
- **Commit:** 0e3af73e

## CI

Läufe des HEAD `64fb4146`:

| Lauf | Workflow | Ergebnis |
|---|---|---|
| 39212860391 | Python gates | success |
| 39212860329 | Integration | success |
| 39212860295 | Resilience | success |
| 39212860321 | Multi-arch image | success |
| 39212860388 | Security scans | success |
| 39212860228 | OpenSSF Scorecard | success |
| 39212860230 | HaRP deploy | success |

Alle sieben Läufe grün. Der `gh run watch`-Beobachter wurde vom System wegen Speichermangel beendet (keine Ursache im Befehl); die Ergebnisse stammen aus einzelnen `gh run list`- und `gh run view`-Abfragen.

## Endzustand der Instanz 8090

Keine fulltextsearch-App installiert oder registriert, keine `oc_fulltextsearch%`-Tabelle, keine Migrations-, appconfig- oder Job-Zeile; `custom_apps` wieder `root:root`; aktiv nur `app_api` 34.0.0 und `findling` 1.4.2; Admin-Seite HTTP 200; `exclusions` = `["Archiv"]`; Kanarie `findling-canary` genau 1 Treffer.

## Offene Fragen an den Owner

- Die drei Ersatz-Absätze (Schritte 3 und 5) gehen in der Abnahme 34-05 vor; besonders der SQL-Aufräumweg als Empfehlung auf einer öffentlichen Seite.
- Nicht geprüft: reset mit eingerichteter, aber nicht erreichbarer Elasticsearch-Plattform (bräuchte fulltextsearch_elasticsearch; D-34-02). Laut Quelltext fängt `resetIndexAll()` nur `ClientResponseException`.

## Self-Check: PASSED

Dateien vorhanden (NACHWEIS, Gate, drei Seiten); Commits d5258548, 0e3af73e, 64fb4146 in `git log`.
