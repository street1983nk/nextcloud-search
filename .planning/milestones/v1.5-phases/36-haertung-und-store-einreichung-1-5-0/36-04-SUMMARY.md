---
phase: 36-haertung-und-store-einreichung-1-5-0
plan: 04
subsystem: Container / Reconcile
tags: [hart-06, d-36-05, d-36-14, m-32-02, f4, reconcile, storages, store]
requires: [36-03]
provides:
  - "Tabelle vanished_storages (IF NOT EXISTS, SCHEMA_VERSION bleibt 2)"
  - "Store: living_storages, living_file_ids, mark_vanished, clear_vanished, forget_storage, drop_orphan_bookmarks"
  - "FileList.gone_storages(ids) -> GoneResult | None, Bänder zu 256, Schnittmenge mit den gefragten IDs"
  - "Reconcile._sweep_vanished nach vollständigem Walk, VANISHED_STORAGE_GRACE_SECONDS = 30 * 86_400"
affects: [36-05, 36-13]
tech-stack:
  added: []
  patterns:
    - "Löschung ganzer Storages nur über queue.requeue(kind=delete) via _hand_over, Lesezeichen erst danach vergessen"
    - "Unsichere Lage (leere/unvollständige/unerreichbare Liste, Route-Fehler) = nie Sofortlöschung"
key-files:
  created:
    - backend/tests/test_store_vanished.py
    - backend/tests/test_reconcile_vanished.py
  modified:
    - backend/src/findling/store/schema.sql
    - backend/src/findling/store/repo.py
    - backend/src/findling/nc/client.py
    - backend/src/findling/nc/files.py
    - backend/src/findling/worker/reconcile.py
    - backend/tests/test_files_client.py
    - backend/tests/test_measurement_scripts.py
    - docs/reconcile.md
decisions:
  - "Ein gescheitertes Löschband beendet den Nachlauf, die Runde bleibt ROUND_WALKED; der nächste fällige Zyklus fragt erneut"
  - "Fehlschlag eines einzigen Bandes der Storage-Frage macht die ganze Antwort zu None (nur Karenz)"
  - "Eine einzelne ungültige ID in gone oder deselected verwirft die ganze Antwort, nicht nur den Eintrag"
  - "RoundResult unverändert; der Nachlauf meldet sich nur über eine Log-Zeile mit Zählern und Storage-IDs"
metrics:
  duration: "ca. 60 min (davon etwa 25 min zwei volle lokale Suiten)"
  completed: 2026-10-20
  tasks: 2
  files: 10
requirements: [HART-06]
---

# Phase 36 Plan 04: Nachlauf für gelöschte, abgewählte und verschwundene Storages Summary

Nach einem vollständigen Abgleich gehen die Dokumente gelöschter und per Schalter abgewählter Storages im selben Zyklus als Löschaufträge in die Queue. Verschwundene Storages bekommen einen Erstsichtungs-Stempel und verlieren ihre Dokumente erst nach fest 30 Tagen. Aus unsicherer Lage wird nie gelöscht, und F4 (ewig unfertige reconcile-Zeile) ist mitgeschlossen.

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | Tabelle vanished_storages, Store-Methoden, Client gone_storages | 704b9efa | schema.sql, repo.py, client.py, files.py, test_store_vanished.py (neu), test_files_client.py, test_measurement_scripts.py |
| 2 | Nachlauf im Abgleich mit Karenz, F4, Ratsche, Push | f8cf48b8 | reconcile.py, test_reconcile_vanished.py (neu), test_measurement_scripts.py, docs/reconcile.md |

## Belege

**Task 1 (TDD):**
- Rot: test_store_vanished.py 9 von 9 rot (AttributeError, `no such table: vanished_storages`). test_files_client.py brach beim Sammeln ab (ImportError GONE_LOOKUP_BAND/GoneResult).
- Grün: 34 passed (9 Store, 25 Client, davon 10 neu: Antwortform, Schnittmenge, leere Frage ohne Aufruf, Ausnahme/404 = None, 12 Fehlformen = None, leere Listen sind eine Antwort, Bänder 256/256/88, ein gescheitertes Band = None, Pfad als Literal, Band gleich `MAX_STORAGE_IDS = 256` im PHP-Controller).
- Gegenprobe: Ohne die Schnittmenge in `gone_storages` wird der Test für die gefragten IDs rot.

**Task 2 (TDD):**
- Rot: Mit nur der Konstante waren 11 von 16 Tests rot. Die 4 Fälle "unsicher" (leere Liste, discarded, unavailable, vorzeitiges Ende) und der Konstantentest waren ohne Nachlauf trivial grün und sind per Gegenprobe belegt:
  - ohne `not found.discarded`: Fall discarded rot
  - ohne `found.mounts and`: Fall leere Liste rot
  - Nachlauf vor den Walk verschoben: empty, discarded, ended_early und die Quelltextprobe rot. unavailable bleibt grün, weil die Runde vor jedem Walk zurückkehrt.
  - forget trotz gescheitertem Band: Retry-Test rot
  - ohne clear_vanished: Rückkehr-Test rot
- Grün: 16 passed. Gelöscht (14) und abgewählt (9) gehen sofort. Verschwunden (7): Stempel, kein delete bei +29 Tagen, delete bei +31 Tagen, dazu die SQL-Rückdatierung um 31 Tage. Bei Rückkehr nach 20 Tagen fällt der Stempel weg, und ein neues Fehlen bei +40 Tagen startet die Karenz neu. Route None heißt nur Stempel. Ein gescheitertes requeue behält das Lesezeichen, und die nächste Runde löscht. 450 Dateien gehen in Bändern 200/200/50. Bei F4 ist danach `unfinished == 0` und `_is_due` false. Das Log enthält weder Pfad noch Datei-ID. Der Kontroll-Storage 3 bekommt in jedem Test kein delete.
- Plan-Verify: test_reconcile_vanished, test_reconcile, test_phase31_audit und test_measurement_scripts ergeben 767 passed. Kein `FINDLING_*GRACE/VANISH` in src/.
- Volle Suite lokal vor jedem Commit: 5946 passed / 264 skipped (Task 1) und 5962 passed / 264 skipped (Task 2). ruff, ruff format, pyright (0 errors), vulture und reuse lint sind grün.

**Ratsche (PACKAGE), beide Male doppelt gerechnet** (40b-baumhash.py und unabhängig find/sort/tr/sha256sum, beide Wege gleich): 92013822 auf 7de293e1 (704b9efa) auf 22846239 (f8cf48b8), 80 Dateien unverändert. Die PHP-Ratsche und die Katalogzahl bewegen sich nicht, weil sich kein PHP und keine l10n geändert haben.

**CI-Block für f8cf48b8** (der Push enthielt beide Commits): Python gates 39465619898, Integration 39465620010, Security scans 39465620210, OpenSSF Scorecard 39465619959, Multi-arch image 39465619860, Resilience 39465620112, HaRP deploy 39465620081. Der PHP-Workflow lief nicht, weil sich kein PHP geändert hat.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Ratsche schon in Task 1 bewegt**
- Task 1 ändert drei Dateien unter `backend/src/findling`. Die Vorgabe "Ratschen im selben Commit, Gates grün vor jedem Commit" verlangt das Nachziehen deshalb schon in Task 1. Dafür gibt es zwei Journalabsätze.

**2. Ergänzung: docs/reconcile.md**
- Offener Punkt aus 36-03. Neuer Schritt 8 im Ablauf, ein eigener Abschnitt "Gelöschte, abgewählte und verschwundene Speicher (M-32-02)" und die Log-Zeile im Protokoll-Abschnitt. Die Datei wurde mit Task 2 committet.

**3. Modul-Docstring von nc/files.py**
- Dort stand "Both calls of this module read", jetzt "All three calls". Die Aussage zur Allowlist gilt unverändert auch für die dritte Route.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche. T-36-13 bis T-36-17 sind wie im Register gemindert: Der Nachlauf läuft nur nach einem vollständigen Walk über eine nicht leere Liste ohne Verwerfungen. Ein Route-Fehler ergibt None und damit nur Karenz. Die Antwort wird auf die gefragten IDs geschnitten. Gelöscht wird nur über die Queue. Das Lesezeichen wird erst nach dem letzten erfolgreichen Band vergessen. Das Log enthält nur Zähler und Storage-IDs.

## Offen

- Nach dem Wegräumen werden die Dateizeilen erst durch den Löschzweig des Pollers zu Grabsteinen. Bis dahin sieht der nächste Zyklus den Storage noch als lebend, stempelt ihn neu und fragt erneut. Das ist harmlos, weil requeueAs die Zeilen auffrischt und nicht doppelt anlegt. Gehen die Löschaufträge verloren, greift die neue Karenz.
- HART-06 reicht über weitere Pläne und wird hier nicht abgehakt.

## Self-Check: PASSED
