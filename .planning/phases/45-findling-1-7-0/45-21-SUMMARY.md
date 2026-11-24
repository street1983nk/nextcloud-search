---
phase: 45-findling-1-7-0
plan: 21
subsystem: release-audit
tags: [review, delta-audit, audited-head, issue-59, issue-25, r-45-21, tdd]
requires: [45-20]
provides: [45-REVIEW-1-7-0.md mit 19 Befunden und Status je Zeile, neun behobene Review-Befunde (R-45-21-01 bis -04, -12 bis -15, -19), Satz des Fehlerzustands der Speicherliste in 18 Katalogen (Schlüsselzahl 387), Delta-Audit af0e5e13 bis Kopf, Threat-Register T-45-57 bis T-45-87, neuer audited_head, Abgleich #59, Baumhash PHP 0db3eed1/147 -> 86f595c7/147]
affects: [45-10, 45-11, 45-12, 45-13, 45-16, 45-14, 45-15]
tech-stack:
  added: []
  patterns: [unabhängiger Review mit zweitem Prüfer und Nachprüfung am Code (B8), Gate über Shell-Verdikt-Zweige mit Fehl-Samples, Hunk-Zuordnung per Skript statt Augenmaß, Funktionskörper byte-gleich per sha256]
key-files:
  created:
    - backend/tests/fixtures/profile_parser_v1_6_5.py.txt
    - .planning/phases/45-findling-1-7-0/45-21-SUMMARY.md
  modified:
    - php/lib/Service/StorageService.php, SettingsService.php, ExternalMountService.php, GatewayReader.php, SnippetPolicy.php
    - php/lib/Controller/ProfileController.php, php/lib/Settings/Admin.php, php/templates/admin.php
    - php/l10n/*.js, php/l10n/*.json (18 Dateien, Schlüsselzahl 387)
    - scripts/ci/update_in_process_driver.php, scripts/ci/update_in_process_proof.sh
    - backend/src/findling/worker/poller.py, backend/tests/conftest.py, test_admin_ui_contract.py, test_update_in_process_proof.py, test_profile_wire.py, test_measurement_scripts.py
    - docs/admin-page.md, docs/l10n-*.md (6 Sprachtabellen)
    - .planning: 45-REVIEW-1-7-0.md, 45-AUDIT.md, 45-ANTWORTEN.md, 45-FREIGABEN.md, STATE.md, ROADMAP.md, REQUIREMENTS.md
decisions:
  - "Entscheid Review R-45-21-01 bis -15 45-21: Owner 'Ok' 2026-11-24 02:51 UTC, alle beheben wie empfohlen"
  - "Freigabe Texte Review 45-21: Owner 'Ok' 2026-11-24 12:50 UTC, Satz des Fehlerzustands der Speicherliste EN/DE/FR; sechs Sprachen maschinell gekennzeichnet; dasselbe Ok deckt die CONTROL-2-Korrektur (R-45-21-19, Entscheid beheben)"
  - "Abgleich #59: der freigegebene Satz passt zum Endverhalten (E1/E2); kein neuer Vorschlag nötig, Antwort bleibt bis 45-15 liegen"
  - "R-45-21-12 Live-Gegenprobe des Ausschlusses läuft im kompletten Neulauf von 45-10 (Ausschluss mit Abgleich), nicht doppelt hier"
metrics:
  duration: "Plan gesamt ca. 23.11. abends bis 24.11. nachmittags über mehrere Sitzungen; dieser Abschlussteil (Satz R-45-21-13, R-45-21-19, Task-3-Abschluss) ca. 3 h inkl. zweimal volle pytest-Suite in zehn Teilen und PHP-Gates in Docker"
  completed: 2026-11-24
---

# Phase 45 Plan 21: Unabhängiger Review, Befund-Fixes und neuer Prüfkopf von 1.7.0 Summary

Der ganze Release-Diff v1.6.5..Kopf ist unabhängig gelesen (eigener Review plus zweiter Prüfer), alle neun Befunde ab LOW sind per TDD mit roten Mutationen behoben, der Fehlerzustand der Speicherliste hat den vom Owner freigegebenen Satz in 18 Katalogen, Kontrolle 2 des Update-Nachweises unterscheidet Bestehen von anderem Fehlschlag, und 1.7.0 hat mit dem Delta-Audit, dem Threat-Register T-45-57 bis T-45-87 und dem #59-Abgleich einen neuen audited_head; 45-10 kann komplett neu laufen.

## Tasks

| Task | Inhalt | Commits |
|---|---|---|
| 1 | Unabhängiger Review des Release-Diffs, zweiter Prüfer eingearbeitet und am Code nachgeprüft | 78d77187 (und Vorarbeit der ersten Sitzung) |
| 2 | Owner-Entscheide zu allen Befunden ab LOW | a505e180, 9b439b8c |
| 3 | Neun Fixes (TDD), Delta-Audit, Threat-Register, audited_head, Abgleich #59, Zustand | siehe Commit-Tabelle unten |

## Fix-Commits (Task 3, je RED -> GREEN)

| Befund | RED | GREEN |
|---|---|---|
| R-45-21-12 (Freigabe hebt Speicher-Ausschluss auf, MEDIUM) | b3af58e9 | 6dc5bb70 |
| R-45-21-15 (occ-Typkonflikt sperrt das Speichern) | 51fdc1cf | 174b8a26 |
| R-45-21-14 (Generation 4 vor 1.6.x-Container) | aceed6ca | c721641f |
| R-45-21-02 (lazy-Modi SnippetPolicy, Kommentar und Testlücke) | (Test im Fix) | 7fe3f91c |
| R-45-21-03 (Treiber liest gepflanzten Wert zurück) | b653ef3b | f9189779 |
| R-45-21-01, R-45-21-04 (Kommentare GatewayReader, poller.py) | (nur Kommentare) | 6aa00ef6 |
| Testisolation (Reihenfolge-Abhängigkeit, deferred-items) | - | e7826527 |
| R-45-21-13 Mechanik (leere Liste hebt Ausschlüsse auf) | 472b4206 | f37e3301 |
| R-45-21-13 Satz (Freigabe Texte Review 45-21, 387 Schlüssel) | 2643c072 | 2ce40602 |
| R-45-21-19 (CONTROL 2: Bestehen vs. anderer Fehlschlag) | 306a727d | 131b4536 |

## Ergebnisse

- Review: 19 Befunde (0 CRITICAL, 0 HIGH, 1 MEDIUM, 8 LOW, 10 INFO); alle ab LOW behoben, INFO geschlossen bzw. an 45-10 (R-45-21-08) und 45-16 (R-45-21-06 unter T-45-74) übergeben.
- Satz R-45-21-13: id findling-rules-mounts-failed, nur im Fehlerzustand, aus dem Katalog; Gate scan_failed_mount_sentence mit vier Fehl-Samples; Schlüsselzahl 387 in allen 18 Dateien, sechs Sprachtabellen je eine Zeile und ein Nachtrag.
- R-45-21-19: die drei Zweige (bestanden, anders fehlgeschlagen, erwartete Meldung) am extrahierten Block real durchgespielt; Gate control2_verdict_findings mit fünf Fehl-Samples.
- Delta-Audit af0e5e13 bis Kopf mit Probe je Punkt (45-AUDIT.md `### Delta-Audit af0e5e13 bis Kopf`): SearchService-Hunks per Skript den Bereichen (a) und (b) zugeordnet, readableFile/readableNode/hitOf/Recheck-Schleife byte-gleich, Logzeilen nur Zähler, Migrationen ohne Schema, #25 F1/F2, Stand F3 offen (wartet auf Logs des Melders).
- Threat-Register T-45-57 bis T-45-87 belegt; T-45-67 nennt I-45-17-03 und 45-20 Schritt C (c); T-45-74 (Prüfspur-Zeile) als bewusste Erweiterung an 45-16 übergeben (open bis 45-16).
- Abgleich #59: alle Entwurfsaussagen passen zum Endverhalten (Zeilen `Abgleich ...` in 45-ANTWORTEN.md); Entwurf byte-gleich zu 89cc8ddf.
- Gates am Endstand: PHPUnit Docker `OK (1448 tests, 9072 assertions)`; Psalm-Taint 0 gegen v33.0.9/v34.0.6/v35.0.3; php-cs 0 von 144; zizmor und actionlint grün mit Proben; ruff, ruff format (261), pyright 0/0/0, vulture grün; pytest gesamt in zehn Teilen 7411 passed, 305 skipped. PHP-Baumhash 86f595c7/147 (Rezept und Pipeline, Positivkontrolle git archive 2643c072 = 0db3eed1/147).
- audited_head: 131b45369a27557f693145a3aea65bde1ab65f1e (letzter Commit außerhalb .planning), status_45_21: passed. Kein Push, kein Tag, kein Kommentar; Docker am Ende leer.

## Abweichungen vom Plan

- Der Plansatz "keine Migration (git diff --stat ... leer)" stammte aus der Fassung vor 45-26; das Delta-Audit dokumentiert stattdessen die zwei vom selben Plan geforderten Migrationen (Version001700 neu, Version001500 geändert), beide ohne Schema-Zugriff.
- Ein eigener Reviewer-Agent ließ sich nicht starten (kein Agent-Werkzeug); Unabhängigkeit über B8-Methode plus zweiten Prüfer-Bericht, im Review dokumentiert.
- 174b8a26 wurde trotz rotem php_gates-Erstlauf committet: der erste Lauf brach an einem composer-Timeout unter Speicherdruck ab (Infrastruktur, kein Befund), die Wiederholung desselben Gates war grün; seitdem Gates seriell gefahren.
- Ein test_v14_zelle-Lauf endete mit 0xC0000142 (Windows-Prozessstart unter Ressourcenknappheit); allein wiederholt grün, in den Endstands-Chunks grün.

## Offen

- R-45-21-08: erster echter CI-Lauf des Jobs watermark-59 nach `Freigabe Push 45-10` (Vorbedingung von 45-10 Task 1).
- R-45-21-12: Live-Gegenprobe des Ausschlusses mit Abgleich im kompletten Neulauf von 45-10.
- T-45-74 in 45-16 (secure-phase) als bewusste Erweiterung der Prüfspur führen.
- F3 (I-45-23-01): wartet auf Logs des Melders.

## Self-Check: PASSED

- 45-21-SUMMARY.md, 45-REVIEW-1-7-0.md (kein Befund ab LOW offen), 45-AUDIT.md (audited_head = 131b45369a27557f693145a3aea65bde1ab65f1e = letzter Commit außerhalb .planning, status_45_21: passed) vorhanden
- Alle genannten Commits im Log gefunden (9b439b8c, 2643c072, 2ce40602, 306a727d, 131b4536, 07e6a33b)
- Arbeitsbaum sauber, keine untracked Dateien, Docker ohne laufende Container, nichts gepusht
