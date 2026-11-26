---
phase: 45-findling-1-7-0
plan: 10
status: passed
date: 2026-11-26
---

# 45-10: Volltest DE/EN/FR auf dem finalen Kopf, Owner-Abnahme

## Ergebnis

- Volltest DE/EN/FR auf dem finalen Kopf mit Befunden: siehe 45-VOLLTEST.md.
- Fixes per TDD:
  - V-45-10-04, V-45-10-05 (Pluralformen) und V-45-10-06 (zwei weitere Pluralsätze).
  - Push dd92da51, CI grün nach einem Rerun (Hänger beim Wörterbuch-Download, I-45-10-07).
- Owner-Abnahme gemeinsam per Playwright: "Ok" (2026-11-26 14:40 UTC), abgenommen mit Änderung V-45-10-07.
- Fix V-45-10-07: Die Fehlerliste umbricht jetzt gegen das `nowrap` aus server.css statt die Seite waagerecht scrollen zu lassen.
  - RED: 33c41cd1, 972f90ab, 12107b50, 8ba59d82, 293ce570. GREEN: 2751fc1f.
  - Mutation: 9 von 9 rot.
  - PHP-Baumhash a46fd501/148 (bb4c0bc8).
- Voller Backend-Lauf lokal: 7423 passed, 305 skipped.
- Push dd92da51..1db01d02, CI ohne Rerun grün (alle 7 Pflicht-Jobs und Scorecard).
- Zweite Sichtprüfung DE/EN/FR auf 1280, 375 und 320 vom Owner abgenommen ("Ja").
- audited_head bb4c0bc8ca9c2b96edacc4de8a846d9d5ccdfe4d, status_45_10: passed.

## Für 1.7.1 vorgemerkt

- I-45-10-04: "Beispiel: Backups" vs "Sicherungen".
- I-45-10-06: Enter fügt keinen Eintrag hinzu.
- I-45-10-08: Trennungen mitten im Wort auf 320 px. Vorschlag: den Chip unter 360 px unter den Grund stellen.
- I-45-10-07 (AUDIT): Der Wörterbuch-Download in der CI hat kein eigenes Zeitlimit und keinen Wiederholversuch.
