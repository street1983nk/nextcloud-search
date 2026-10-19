---
phase: 35-stretch-aehnliche-dokumente-und-spikes
plan: 08
status: complete
completed: 2026-10-20
requirements: [STR-01]
---

# 35-08: Gemeinsame Owner-Abnahme der Aehnlich-Ansicht

## Ergebnis

Owner-Abnahme am 20.10.2026: "Abgenommen", keine Aenderungswuensche.
STR-01 bleibt wie geplant auf Pending (Abhaken erst im Audit 35-12).

## Was passiert ist

- **Task 1:** Alle 8 Proben per Playwright auf http://localhost:8090 gefahren
  und in 35-08-ABNAHME.md protokolliert (Erwartung, Ergebnis, Foto): Link je
  Treffer, Tastaturreihenfolge mit Fokusrahmen, Aehnlich-Ansicht (similar=14,
  3 Nachbarn, Quelle nie in der Liste), Rueckweg + Browser-Zurueck mit
  Zeilenmarkierung, Leerzustand, Negativkontrolle (fremde und nicht existente
  fileid byte-identisch, abc = Ergebnisseite), Konsole/nextcloud.log sauber,
  390 px ohne Ueberlappen. Wortlaut live in de, en und fr gegengeprueft.
- **Task 2:** Gemeinsame Runde am Playwright-Chrome, Owner-Abnahme woertlich
  mit Datum im Protokoll. Offene Frage Suchformular: Owner folgt der
  Empfehlung, es bleibt sichtbar (nur die Facetten sind in der Ansicht weg).
- **Task 3:** Keine Owner-Aenderungen, daher kein Codeeintrag. Gezielte Tests
  gruen (671 in test_admin_ui_contract + test_measurement_scripts). Keine
  Testdateien oder Testnutzer angelegt, Sprache zurueck auf de.

## Vorbereitung (dokumentierte Dev-Eingriffe, siehe Protokoll)

- Owner-Entscheid: alle Dateien einbetten. Dev-Backend mit
  FINDLING_EMBED_MODEL_DIR neu gestartet; Drift der Marke ausgeloest, Kette
  lief auf dem Produktpfad; Endstand 438 von 510 lebenden Dokumenten mit
  Vektoren, Rest ohne gespeicherten Text.

## Befund fuer 35-12 (Audit)

- Marke "unknown" liefert keine Nachlieferung; eine Instanz, die laenger ohne
  Modell lief, fuellt den Vektorbestand erst nach echtem Drift.
- Requeue-te embed-Zeilen weckten den armed-Poller im Leerlauf nicht sichtbar
  (5 Zeilen blieben Minuten liegen, nach Neustart sofort verarbeitet).
- Aus 35-05 offen: Route vergleicht Quell-Mittelwert gegen einzelne
  Nachbar-Abschnitte, gemessen wurde Dokument gegen Dokument (54,5).

## Key files

- .planning/phases/35-stretch-aehnliche-dokumente-und-spikes/35-08-ABNAHME.md (Protokoll mit Owner-Abnahme)
