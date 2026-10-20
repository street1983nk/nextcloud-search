---
phase: 36-haertung-und-store-einreichung-1-5-0
plan: 05
subsystem: Container / Reconcile / CI
tags: [hart-06, d-36-05, d-36-06, d-36-14, m-32-02, reconcile, storages, ci, live-beleg]
requires: [36-04]
provides:
  - "CI-Beweis M-32-02 im Job reconcile-and-dach: gone36, keep36, E1 bis E3, drei Zyklen"
  - "Live-Beleg 8090 mit Positivkontrolle (36-M3202-BELEG.md)"
  - "Vorprüfung der Mount-Semantik von NC 34 (36-M3202-VORPRUEFUNG.md)"
  - "Fix: Storage-Frage schickt jede ID (ids[0], ids[1], ...) am OCS-Hook von nc_py_api vorbei"
affects: [36-13]
tech-stack:
  added: []
  patterns:
    - "Listen-Parameter an OCS-Routen nur mit eindeutigen Schlüsseln (ids[N]), nie wiederholtes ids[]"
    - "Vorbedingung 'für niemanden eingebunden' über Anwendbarkeit auf eine leere Gruppe (Core), nie per SQL"
key-files:
  created:
    - .planning/phases/36-haertung-und-store-einreichung-1-5-0/36-M3202-VORPRUEFUNG.md
    - .planning/phases/36-haertung-und-store-einreichung-1-5-0/36-M3202-BELEG.md
  modified:
    - .github/workflows/integration.yml
    - backend/src/findling/nc/client.py
    - backend/tests/test_files_client.py
    - backend/tests/test_measurement_scripts.py
    - docs/admin-page.md
    - docs/reconcile.md
decisions:
  - "CI hängt E2/E3 per Anwendbarkeit auf eine leere Gruppe ab (Weg V4). Ein Platzhalter-Nutzer bekommt in NC 34 sofort eine oc_mounts-Zeile, und W1 bis W3 entfernen sie nicht"
  - "Kein Produktbefund im Sinne des Halt-Kriteriums: oc_mounts folgt der Anwendbarkeit sofort, ein für niemanden eingebundener Speicher fällt also sofort aus der Mountliste"
  - "Storage-Frage mit indizierten Schlüsseln ids[N]: der Hook patch_param von nc_py_api fasst wiederholte Schlüssel zusammen"
  - "Live-Zyklen mit FINDLING_RECONCILE_ENABLED=false im Host-Backend und eigenem run_once-Prozess (CI-Muster), statt das Backend für jeden Zyklus zu stoppen"
metrics:
  duration: "ca. 56 min (17:52Z bis 18:48Z), davon etwa 13 min volle lokale Suite und 2 CI-Blöcke"
  completed: 2026-10-20
  tasks: 2
  files: 8
requirements: [HART-06]
---

# Phase 36 Plan 05: M-32-02 zweigleisig belegt Summary

Ein dauerhafter CI-Test gegen eine echte Nextcloud und ein Live-Beleg auf 8090 mit Positivkontrolle belegen den Nachlauf für gelöschte, abgewählte und verschwundene Speicher. Beim Live-Lauf kam ein echter Produktfehler ans Licht: Die Storage-Frage kam bei Nextcloud nur mit der letzten ID an. Er ist im selben Plan gefixt, mit Test und Ratsche.

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | Vorprüfung Dev-8090, CI-Test M-32-02 | 1a843bac | integration.yml, 36-M3202-VORPRUEFUNG.md |
| 2a | Produktfix Storage-Frage (Befund aus Task 2) | 1d2ed9bf | nc/client.py, test_files_client.py, test_measurement_scripts.py |
| 2b | Live-Beleg 8090 und Doku der Regel | 87db7bec | 36-M3202-BELEG.md, admin-page.md, reconcile.md |

## Schritt 0: Vorprüfung (36-M3202-VORPRUEFUNG.md)

- Nextcloud 34 schreibt oc_mounts bei `files_external:applicable` sofort neu. Die Zeile von ext36v war weg, und der Platzhalter nobody36v bekam auf der Stelle eine eigene, ohne je angemeldet gewesen zu sein.
- W1 (`files:scan ext36v`), W2 (PROPFIND als ext36v) und W3 (`files:scan --all`): Die oc_mounts-Zeile für Storage 16 bleibt jedes Mal stehen, wegen nobody36v. oc_storages 16 bleibt ebenfalls.
- V4 (Anwendbarkeit nur auf eine leere Gruppe): oc_mounts hat sofort 0 Zeilen, oc_storages 16 bleibt. Das ist der verbindliche Weg für CI.
- V5 (`files_external:delete`, im Rückbau): oc_mounts hat 0 Zeilen, aber die oc_storages-Zeile bleibt. Daher stammt der Dev-Fall Storage 7.
- Das Halt-Kriterium ("kein Weg leert oc_mounts, Findling sähe abgehängte Speicher nie") trifft nicht zu. Die Mountliste folgt der Anwendbarkeit sofort. Nicht funktioniert hat nur der Platzhalter-Nutzer im Testaufbau. Deshalb gab es keinen Checkpoint.
- Der Rückbau ist protokolliert (Speicher, beide Nutzer, Gruppe und Systemwert entfernt). Als Core-Rest bleibt die oc_storages-Zeile 16. Nebenwirkung: Die Skeleton-Dateien von ext36v wurden als Storage 17 indexiert und waren im Live-Beleg ein weiterer gelöschter Speicher.

## CI-Beleg (Task 1)

- Der erste Lauf 39470956178 (1a843bac) war in reconcile-and-dach **rot**, und das Rot war richtig. Zyklus 1 und 2 liefen nur zufällig grün: gone36 hatte die höchste ID des Bandes. Zyklus 3 fragte nach [5, 7], angekommen ist nur 7. E1 wurde deshalb gestempelt statt als abgewählt geräumt. Das ist derselbe Produktfehler wie live.
- Integration-Lauf **39473721923** auf 87db7bec ist grün, alle Jobs. Storage-IDs: E1=5, E2=6, E3=7, gone36=8, keep36=9.

| Zeitpunkt | gone36 | keep36 | E1 | E2 | E3 | Sweep-Zeile |
|-----------|--------|--------|----|----|----|-------------|
| vorher | 1 | 1 | 1 | 1 | 1 | |
| Zyklus 1 | 0 | 1 | 1 | 1 (Stempel) | 1 (Stempel) | absent=3 gone=1 stamped=2 removed=[8] |
| Rückdatierung E2 | | | | 1792520719 auf 1789842319 | 1792520719 bleibt | |
| Zyklus 2 | 0 | 1 | 1 | 0 | 1 (Stempel) | absent=2 stamped=1 removed=[6] |
| Zyklus 3 (Schalter aus) | 0 | 1 | 0, ohne Stempel | 0 | 1 (Stempel) | absent=2 deselected=1 stamped=1 removed=[5] |

- Die Suchprobe keep36 `Kontrollstein` nach Zyklus 3 liefert genau 1 Treffer.
- CI-Block für 87db7bec: Python gates 39473722261, Security scans 39473722210, Integration 39473721923, Multi-arch image 39473722547, OpenSSF Scorecard 39473722235, HaRP deploy 39473722265 und Resilience 39473722552 sind alle grün.

## Live-Beleg 8090 (Task 2, 36-M3202-BELEG.md)

- Die state.db ist gesichert: `.dev/backup-36-05/state.db.bak`, SHA-256 7c4dffe5...cbc46. Das Backend wurde mit Stand 36-04 neu registriert.
- Zyklus 1a (alter Client) räumte nur 17. 14 und 15 wurden gestempelt, im Zugriffslog steht nur `ids[]=17`. Daraus folgte der Fix 1d2ed9bf.
- Zyklus 1 (Fix): 14 geht von 1 auf 0, 15 von 49 auf 0, 17 war schon auf 0. 7 behält 30 Zeilen mit Stempel. 2/3/4 bleiben bei 55/371/49 (Positivkontrolle). Die reconcile-Waisen 12/13 sind weg (F4). Die Suchprobe testuser `Genehmigung` liefert weiter Treffer.
- Rückdatierung 7: 1792519319 auf 1789840919. In Zyklus 2 geht 7 von 30 auf 0, und 2/3/4 bleiben bei 55/371/49. Die Suchprobe testuser liefert Treffer, kollegin bekommt genau 1 Treffer (09-bescheid.pdf).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3, Blocking] CI-Abhängen über eine leere Gruppe statt über einen Platzhalter-Nutzer**
- **Gefunden in:** Task 1, Schritt 0
- **Problem:** Laut Plan sollten E2/E3 auf nobody36 umgehängt und dann über W1 bis W3 aufgefrischt werden. In NC 34 erzeugt das sofort eine oc_mounts-Zeile für den Platzhalter, und kein Weg entfernt sie.
- **Fix:** Anwendbarkeit auf die leere Gruppe `m3202-empty` (Core-Weg V4, belegt). Es gibt keinen Auffrisch-Schritt und keinen nobody36. Die SQL-Gegenprobe der Vorbedingung bleibt im Workflow.
- **Commit:** 1a843bac

**2. [Rule 1, Bug] Storage-Frage kam nur mit der letzten ID an**
- **Gefunden in:** Task 2, Live-Zyklus 1a. In CI Lauf 39470956178 ebenfalls rot.
- **Problem:** `params={"ids[]": [...]}` wurde vom OCS-Hook `patch_param` in nc_py_api 0.30.3 (`dict(parse_qsl(...))`) auf den letzten Wert verkürzt. Gelöschte und abgewählte Speicher gingen dadurch in die Karenz statt in die Sofortlöschung. Das ist die sichere Richtung, Datenverlust gab es keinen.
- **Fix:** `gone_storage_params` sendet `ids[N]`. Der Test baut die echte niquests-URL und lässt den Bibliotheks-Hook darüber laufen. Gegenprobe mit der alten Form: 3 Tests rot. Ratsche: Paket-Baumhash 22846239 auf 2210b1bf, beide Wege, 80 Dateien. Die PHP-Seite ist unverändert.
- **Commit:** 1d2ed9bf

**3. Live-Zyklen bei laufendem Backend mit ausgeschalteter Abgleich-Schleife**
- Der Plan wollte das Backend für den Zyklus stoppen. Umgesetzt ist das CI-Muster: Das Host-Backend läuft mit `FINDLING_RECONCILE_ENABLED=false`, und jeder Zyklus ist ein eigener `run_once`-Prozess über WAL. Das Ziel "genau ein Zyklus" bleibt erreicht, und die Queue arbeitet sofort ab.

## Gates

- Lokal vor dem Fix-Commit: volle Suite 5963 passed / 264 skipped. ruff, ruff format, pyright (0 errors), vulture und reuse lint (2896/2896) sind grün.
- Workflow-Tests (17 Dateien) 1101 passed. Die Step-Skripte sind mit `bash -n` geprüft, der ncsql-Helfer wurde gegen den Dev-Container getestet.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche. T-36-18: Beide Orakel (Nextcloud-SQL und state.db per sqlite3) sind vom geprüften Code getrennt. T-36-19: Die Sicherung samt Prüfsumme lag vor dem ersten Eingriff vor. T-36-20b: Kein SQL in oc_mounts, die Vorbedingung kommt aus dem Core (V4). T-36-20: keep36 und 2/3/4 behalten exakt ihre Zeilen.

## Offen

- Die Sicherung `.dev/backup-36-05/state.db.bak` bleibt bis Phasenende liegen.
- Das Host-Backend auf 8090 läuft mit `FINDLING_RECONCILE_ENABLED=false`. Die nächste Registrierung ohne die Variable stellt den Standard wieder her.
- HART-06 reicht über weitere Pläne und wird hier nicht abgehakt.

## Self-Check: PASSED

- Dateien: 36-M3202-VORPRUEFUNG.md, 36-M3202-BELEG.md, integration.yml, client.py, test_files_client.py, admin-page.md, reconcile.md sind vorhanden.
- Commits 1a843bac, 1d2ed9bf und 87db7bec sind in `git log` vorhanden.
