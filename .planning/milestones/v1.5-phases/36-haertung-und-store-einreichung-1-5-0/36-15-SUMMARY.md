---
phase: 36-haertung-und-store-einreichung-1-5-0
plan: 15
subsystem: Fremdinstallation und Owner-Abnahme 1.5.0
tags: [rel-05, hart-06, foreign-install, owner-acceptance, playwright]
requires: [36-14]
provides:
  - "Frische Nextcloud 34.0.3 auf 8096 (HaRP) mit Companion und Backend nur aus den Release-Assets v1.5.0, Image sha256:cf805dfa...49d8"
  - "Sichtprobe aller Prüfdateien per OCS Unified Search, zwei Sammelklassen-Dateien mit Detailcode (zip_traversal, image_pixels)"
  - "Owner-Abnahme von Store-Text und Produkt 1.5.0 am 21.10.2026, Urteil wörtlich okok"
  - "Belegzeile (9) im Abschnitt Release 1.5.0 von docs/store-listing.md"
affects: [36-16]
tech-stack:
  added: []
  patterns:
    - "Abnahme-Stack als eigenes compose-Projekt im Scratch, ohne Arbeitsbaum-Mount; Companion per docker cp aus dem Tarball"
key-files:
  created:
    - .planning/phases/36-haertung-und-store-einreichung-1-5-0/36-ABNAHME.md
  modified:
    - docs/store-listing.md
    - .planning/phases/36-haertung-und-store-einreichung-1-5-0/36-AUDIT.md
    - .planning/phases/36-haertung-und-store-einreichung-1-5-0/deferred-items.md
decisions:
  - "Abnahme-Instanz als neues compose-Projekt findling-accept statt Neuaufbau von findling-harp; alter Stack bleibt, altes ExApp-Datenvolume als findling-harp143_backend_data gesichert"
  - "Backend-Texte werden an der info.xml des Tags abgenommen: die Seite External Apps zeigt bis zur Einreichung den Katalogtext 1.4.3"
  - "L-36-05 und L-36-06 als LOW mit Ziel 1.5.1, vom Owner akzeptiert, kein Blocker für 1.5.0"
metrics:
  duration: "Aufbau 11:44Z bis 12:06Z, Abnahme durch Koordinator und Owner danach"
  completed: 2026-10-21
  tasks: 2
  files: 4
requirements: [REL-05, HART-06]
---

# Phase 36 Plan 15: Fremdinstallation und Owner-Abnahme 1.5.0 Summary

Frische Nextcloud 34.0.3 auf http://localhost:8096 mit Findling 1.5.0 ausschließlich aus den Release-Assets (SHA-256 gleich 36-14, Image-Digest gleich dem Release-Index), echte Testdateien indexiert, P1 bis P8 und die sechs Beschreibungen gemeinsam per Playwright vom Owner abgenommen ("okok", 21.10.2026).

## Task 1: Fremdinstallation und Sichtprobe

- Stack `findling-accept` (nextcloud:34.0.3-apache, HaRP mit Digest-Pin, nginx-Vorproxy), Companion aus `findling.tar.gz` per `docker cp`, Backend per `app_api:app:register` mit der unveränderten info.xml aus `findling_backend.tar.gz`; mutual TLS im Log.
- Redeploy mit `FINDLING_LANGUAGES=de,en,cs` (Daten behalten), Umbau über den Produktpfad.
- Sichtprobe (sweep.py im Scratch): alle 22 Prüfungen OK, Diagnose 177 `blocked_malicious/zip_traversal`, 178 `blocked_malicious/image_pixels`.
- Sechs installierte Beschreibungen zeichengleich mit 36-WORTLAUT.md B1.
- Freier RAM: 2,23 GB vor, 1,96 GB nach dem Aufbau (zwischendurch 0,17 GB nach dem Image-Pull, per drop_caches im Docker-VM behoben).

## Task 2: Owner-Abnahme

Durchgeführt vom Koordinator mit dem Owner. Ergebnisse je Punkt und Urteil in 36-ABNAHME.md, Zeile `Owner-Abnahme: 21.10.2026, okok`. Belegzeile (9) in docs/store-listing.md. Commit 2d9e9ffe (lokal).

## Deviations from Plan

1. **Abnahme-Runde nicht vom Executor gefahren:** auf Anweisung des Koordinators; Ergebnisse von ihm übermittelt und eingetragen.
2. **Altes ExApp-Datenvolume:** statt Entfernen nach Owner-Ja vorher nach `findling-harp143_backend_data` kopiert, dann `nc_app_findling_backend_data` und der gestoppte 1.4.3-Container entfernt, weil AppAPI die Namen aus der App-Id bildet und 1.5.0 sonst den alten Index übernommen hätte.
3. **Befund Fundstelle Backend-Text:** External Apps zeigt den Katalogtext 1.4.3; Backend-Texte deshalb an der Tag-Datei abgenommen.
4. **LOW-Nachtrag:** L-36-05, L-36-06 in 36-AUDIT.md und deferred-items.md (Ziel 1.5.1), auf Anweisung des Koordinators.

## Known Stubs

Keine.

## Offen

- 36-16 Einreichung; lokale Commits a4035afc, 754d0a95, 2d9e9ffe und dieser Abschluss gehen mit dem Owner-Wort in 36-16 hinaus.
- Instanz 8096 läuft weiter bis nach der Einreichung; Muster `*.photoslibrary` ist dort gesetzt, fulltextsearch deaktiviert.
- Volume `findling-harp143_backend_data` nach Owner-Ja entfernen.

## Self-Check: PASSED

- FOUND: 36-ABNAHME.md mit `Owner-Abnahme: 21.10.2026, okok`
- FOUND: "Owner-Abnahme" in docs/store-listing.md
- FOUND: Commit 2d9e9ffe
- FOUND: http://localhost:8096/status.php 200
