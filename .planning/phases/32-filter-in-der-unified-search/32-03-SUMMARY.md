---
phase: 32-filter-in-der-unified-search
plan: 03
subsystem: PHP-Companion (SearchService, Ordnerbudget), Messwerkzeug scripts/dev
tags: [usrch-02, d-32-06, a2, pitfall-4, measurement, unified-search, folder-filter]
requires:
  - phase: 32
    provides: "32-02: Ordnermodus mit FOLDER_FETCH_LIMIT 100 und FOLDER_MAX_ROUNDS 6 als Startwerte"
provides:
  - "scripts/dev/measure_folder_filter.sh (setup, wait, measure, cleanup über die OCS-Suchroute, Passwort nur aus der Umgebung)"
  - "docs/measurements/2026-10-ordnerfilter/README.md mit Regel vor der Messung, Varianten A bis D, Basislauf, Langreihe, Urteil"
  - "FOLDER_MAX_ROUNDS 12 (gemessen), beide Konstanten verweisen auf den Bericht"
affects: [32-06 deploy-harp und Doku, 32-08 Audit]
tech-stack:
  added: []
  patterns: ["Messvarianten über den Bind-Mount, je Variante Containerneustart, SHA-256 im Container und Kanarie vor der Messung"]
key-files:
  created:
    - scripts/dev/measure_folder_filter.sh
    - docs/measurements/2026-10-ordnerfilter/README.md
    - docs/measurements/2026-10-ordnerfilter/rohdaten/ (63 Dateien)
  modified:
    - php/lib/Service/SearchService.php
    - php/tests/Unit/SearchServiceTest.php
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Variante D (12 x 100) nach der vorher festgelegten Regel: kleinste Variante mit vollen Ordnergruppen, Median unter 1,5 s, Maximum unter 2,5 s, ohne Ordner höchstens +10 Prozent"
  - "Regelpunkt 3 an einer Langreihe entschieden (je 100 Werte, Basis und D abwechselnd), weil der byte-gleiche Ohne-Ordner-Pfad in A bis D schon mit n = 20 um mehr als 10 Prozent streute"
  - "Messung mit App-Passwort statt Login-Passwort, damit keine Reihe die bcrypt-Prüfung mitmisst"
  - "SearchServiceTest leitet die erwarteten Abrufe aus den Konstanten ab und hält zusätzlich: mehr als 3 Runden, letzter Offset höchstens MAX_CONTAINER_OFFSET"
metrics:
  duration: "ca. 150 min inkl. ca. 7 min Korpus, ca. 35 min Messung, ca. 25 min Volltestläufe und ca. 30 min CI"
  completed: 2026-10-13
  tasks: 2
  files: 5
---

# Phase 32 Plan 03: Ordnerbudget gemessen Summary

Das Budget des Ordnermodus ist auf der Dev-Instanz gemessen: mit 1000 besser gerankten Treffern außerhalb liefern "kein Sonderbudget" und der Startwert 6 x 100 eine leere Gruppe (Pitfall 4 belegt), 10 x 100 verfehlt Rang 1001 um eine Stelle, 12 x 100 findet alle Ordnertreffer in 0,134 s Median. `FOLDER_MAX_ROUNDS` steht jetzt auf 12, beide Konstanten verweisen auf `docs/measurements/2026-10-ordnerfilter/README.md`.

## Commit

- `060d637b` perf(32-03): measure the folder budget of the unified search filter (Task 1 und 2 in einem Commit, wie im Plan vorgegeben), gepusht auf origin/main.

## Vorab: Dev-Instanz

- `occ status` meldete `needsDbUpgrade: true`; `occ upgrade` hob `findling` auf 1.4.2, danach `needsDbUpgrade: false`, `maintenance: false`.
- Der Host-Prozess des Backends (manual-install, Port 10035) lief seit 06.10. und meldete 1.4.0, `backend/src` hatte sich am 12.10. geändert. `FINDLING_PORT=8090 scripts/dev/register-exapp.sh` hat ihn mit der Begründung "reports the version 1.4.0 and the sources say 1.4.2" neu gestartet und 1.4.2 registriert.
- Kanarie `term=findling-canary` über `/ocs/v2.php/search/providers/findling/search`: Eintrag `findling-canary` aus dem Container, HTTP 200, vor und nach dem Neustart sowie vor jeder Variante.
- Speicher vorher (`docker stats --no-stream`): findling-nextcloud 181 MiB, Docker-VM 7,6 GiB, Host rund 3,1 GB frei. Alles seriell gefahren.

## Task 1: Messskript, Korpus, Varianten

- Dialog-Limit belegt aus stable34 `UnifiedSearchModal.vue` (Zeilen 306, 558 bis 560, 670) und `UnifiedSearchController` (`LIMIT_DEFAULT` = 5): erster Abruf 5, "Mehr laden" 10. Gemessen `limit=5` und `limit=10`.
- Korpus: 1000 kurze Dateien (Begriff 30-mal), 10 lange unter `Innen/Tief`, 1 unter `Einzeln`. Direkt gegen den Container belegt: Offset 1000 liefert genau 11 Kandidaten, ihre IDs 1730 bis 1740 sind genau die `oc:fileid` der Ordnerdateien.
- Ergebnisse (Median / Maximum, n = 20):

| Variante | Innen 5 | Innen 10 | Einzeln 5 | Einzeln 10 |
|---|---|---|---|---|
| A (M4, 3 Runden) | 0 Treffer | 0 | 0 | 0 |
| B (6 x 100) | 0 | 0 | 0 | 0 |
| C (10 x 100) | 0 | 0 | 0 | 0 |
| D (12 x 100) | 5, 0,134 / 0,278 s | 10, 0,129 / 0,188 s | 1, 0,127 / 0,183 s | 1, 0,122 / 0,186 s |

- Basis (SearchService.php aus 39e8eca9, als Blob nach `git worktree add` und wieder entferntem Worktree): ignoriert den Ordner, liefert volle ungefilterte Gruppen (Positivkontrolle).
- Ohne Ordner, Langreihe je 100 Werte abwechselnd: Basis 0,0618 / 0,0620 s, D 0,0609 / 0,0601 s (minus 1,5 und minus 2,9 Prozent).
- Bestätigungslauf mit der eingecheckten Datei: gleiche Trefferzahlen, Mediane 0,126 bis 0,131 s.
- Nach der Messung `git diff --quiet -- php/` ohne Befund (Originaldatei zurückkopiert), erst danach die Task-2-Änderung.

## Task 2: Konstanten

- `FOLDER_MAX_ROUNDS` 6 auf 12, `FOLDER_FETCH_LIMIT` bleibt 100; beide Kommentare nennen den Bericht und die Kernzahl 0,134 s.
- `SearchServiceTest::testTheFolderModeFetchesMoreRoundsOfTheFolderLimit` liest beide Konstanten über `constantInt()` (vorher `assertSame(6, ...)` und eine wörtliche Liste mit sechs Abrufen); die erwartete Abrufliste wird aus den Konstanten gebaut und bleibt exakt verglichen. Neu: Rundenzahl über 3 und letzter Offset höchstens `MAX_CONTAINER_OFFSET`.
- Baumhash: `PHP_TREE_HASH_TODAY` ad0e7eec291d577b0016cef93ec0d68e326d158c7ae9df155d41801495692068, `PHP_FILES_TODAY` bleibt 93, Journal "Plan 32-03". Vorher rot gegen den alten Wert gesehen.
- `php -l` beider PHP-Dateien über php:8.3-cli sauber.

## Gates und CI

- Lokal aus backend/ mit PYTHONUTF8=1: `pytest` 5586 passed, 30 skipped; `ruff check`, `ruff format --check` grün; `PYRIGHT_PYTHON_FORCE_VERSION=latest pyright` 0 Fehler; `vulture src tests --min-confidence 80` ohne Befund. `test_php_acl_boundary.py` unverändert und grün.
- CI auf 060d637b, jeweils `gh run watch <id> --exit-status`:
  - php.yml 38325827607: grün (645 Tests, 2362 Assertions).
  - python.yml 38325827589: grün.
  - integration.yml 38325827596: grün.
  - deploy-harp.yml 38325827613: grün.
  - Außerdem grün: Resilience 38325827584, Security scans 38325827575, Multi-arch image 38325827615, OpenSSF Scorecard 38325827585.

## Aufräumen (Belege)

- `measure_folder_filter.sh cleanup`: DELETE `/Messung32`, danach PROPFIND 404 (ein zweiter Aufruf antwortet 404).
- `occ trashbin:cleanup testuser` ausgeführt; PROPFIND auf `trashbin/testuser/trash/` zeigt keinen Eintrag `Messung32`.
- Dialogsuche nach `ordnermessung32`: 0 Einträge.
- App-Passwort `messung32` (ID 62) gelöscht, danach mit dem alten Token HTTP 401. Token-Dateien im Scratch gelöscht.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Warteschleife des Messskripts hing an der Tür-Zeile**
- **Found during:** Task 1
- **Issue:** Die Tür zur Ergebnisseite trägt `attributes` als leeres JSON-Array; jq brach ab, die Schleife wartete ohne Ende.
- **Fix:** Datei-ID nur von einem Objekt lesen, leere Antwort als 0, jede unlesbare Antwort bricht die Messung ab.
- **Commit:** 060d637b

**2. [Rule 3 - Blocking] Veralteter Host-Prozess des Backends**
- **Found during:** Vorab
- **Issue:** Host-Prozess meldete 1.4.0, Quellen 1.4.2; eine Messung hätte einen alten Stand gemessen.
- **Fix:** `register-exapp.sh` mit `FINDLING_PORT=8090` (Neustart und Registrierung 1.4.2).

**3. [Rule 1 - Bug] Bericht löste die Geheimnis-Wache aus**
- **Found during:** Gates
- **Issue:** Die vierteilige Serverfassung im Bericht trifft das Muster einer IP-Adresse (`test_public_artifacts.py`, Familie muster-der-umsetzung).
- **Fix:** Umformuliert auf `versionstring` 34.0.3, keine neue Ausnahme in der Liste.

### Präzisierungen

- Regelpunkt 3 (ohne Ordner höchstens +10 Prozent) an der Langreihe entschieden. In der 20er-Tabelle steht D bei `limit=10` +14,5 Prozent über der Basis und bei `limit=5` 23,5 Prozent darunter; derselbe Code (A bis D) streut dort zwischen 0,058 und 0,067 s. Beide Reihen stehen im Bericht. Die Regel selbst ist unverändert.
- Messung mit App-Passwort (`occ user:auth-tokens:add`), nicht mit dem Login-Passwort: der Seitenbudget-Bericht hat 0,32 s je Anfrage für bcrypt belegt. Für die Regel ohne Belang, weil die Frist von 2,5 s erst in `SearchService::run()` zählt.
- Variante D ist die größte des Plans; der Container nimmt noch Offset 1200 an, ein 13. Abruf käme bis Rang 1300. Im Bericht als Grenze vermerkt, kein Wert gewählt, der nicht gemessen wurde.

## Offene Punkte

- Die 1011 Messdateien stehen noch im Container-Index der Dev-Instanz. Ordnerlöschungen räumt der SubtreeExpandJob per Cron ab; der Plan leerte den Papierkorb sofort, und der Cron der Dev-Instanz läuft nicht von selbst (letzter Lauf 09.10., einmal `cron.php` von Hand ohne Wirkung). Laut Docblock von `FileEventListener::queueDeletion` trägt dann der ETag-Abgleich. Der Recheck verwirft die Einträge, der Dialog liefert 0. Kein Fehler dieses Plans, aber für 32-08 (Audit) und für künftige Messpläne zu wissen: erst den Cron laufen lassen, dann den Papierkorb leeren.
- Zeiten stammen von einem x86-Laptop; auf einer kleinen ARM-Box beendet die Uhr (2,5 s) den Ordnermodus früher. Reserve hier rund Faktor 18 zum Median.

## Threat Flags

Keine neue Fläche. T-32-11 (Regel mit Median, Maximum und Regressionsgrenze), T-32-12 (Passwort nur aus der Umgebung, an curl über stdin, nie im Skript, Bericht oder Rohdaten), T-32-13 (Bericht mit Verfahren, Wiederholungen, Median, Verweis aus dem Code) sind umgesetzt.

## Self-Check: PASSED

- Dateien vorhanden: scripts/dev/measure_folder_filter.sh, docs/measurements/2026-10-ordnerfilter/README.md, 63 Rohdaten-Dateien.
- Commit 060d637b in `git log` und auf origin/main (`git ls-remote`).
- Akzeptanz: `grep -n "2026-10-ordnerfilter" php/lib/Service/SearchService.php` trifft zweimal; `Median` und `Entscheidungsregel` im Bericht; `bash -n` des Skripts sauber; `git diff --quiet -- php/` nach der Messung ohne Befund.
- Alle acht CI-Läufe auf 060d637b mit `gh run watch --exit-status` Exitcode 0.
