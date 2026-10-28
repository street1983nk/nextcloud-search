# Phase 40: zurückgestellte Punkte außerhalb des Umfangs

## Aus Plan 40-01 (Audit 1.6.0)

- **Tombstones im Feld `indexed` (Stand 1.5, nicht v1.6):** `Store.counts()`
  (`backend/src/findling/store/repo.py:1052`) zählt tombstoned Zeilen mit; der
  Nenner der Abdeckung zählt gelöschte Dateien nicht. Nach Lektüre steht der
  Zähler damit bei voller Abdeckung über dem Nenner, sobald eine Datei gelöscht
  wurde, und `coverageShare` zeigt keine Zahl. Zu prüfen in v1.7, ob das im
  Betrieb so auftritt (Live-Instanz) und ob `indexed` auf lebende Zeilen
  umgestellt wird (ändert die Bedeutung eines Felds von 1.5, betrifft auch
  F-40-06). Kein Fix in 1.6.0.

## Issue #36 Befund (28.10. abend, nach dem Audit 40-01)

Bestaetigter Bug im Content-Gateway-Pfad des Pollers (Analyse im Issue, Antworten
6472249936 und 6478501641). Befunde A-E:

- A: poller.py:2045-2048 loggt bei NextcloudException nur den Klassennamen, der
  HTTP-Status wird verschluckt (kein Pfad/Nutzer im Status, darf geloggt werden).
- B (Kern): Ein per-File-Fehler (4xx/5xx ausser 404/998) wird als _GatewayDown fuer
  den ganzen 32er-Pass behandelt; _abort gibt die Zeilen MIT Retry-Gutschrift
  zurueck (QueueMapper::unlock 846-851), der id-sortierte Claim holt denselben
  Kopf-Batch wieder: Endlosschleife, give-up-Regel (MAX_DELIVERIES=3) greift nie.
  Richtung: per-File-Verdikt failed(gateway_error) bzw. kein Refund; Vorbild
  ShortRead-Zweig (T-29-15). Verbindungs-/Proxy-Fehler (502/503/504, httpx-
  Transportfehler) bleiben Gateway-down-Semantik.
- C: Writer-Pending ueberlebt _abort (poller.py:2238) und wird vom naechsten Pass
  committet: unsichtbare Dokumente ohne ACL-Zeile und ohne Verdikt.
- D: ROUND_GATEWAY_UNAVAILABLE ist weder auf der Statusseite noch in
  occ findling:index --status sichtbar.
- E: Der 422-Zweig (GatewayController.php:103-105, fopen false) loggt NC-seitig nichts.

Entscheidung beim Owner in der 40-04-Runde: Fix-Paket als 1.6.1 sofort nach der
1.6.0-Einreichung (Empfehlung; Audit 40-01 ist schon geschlossen, 1.6.0-Zug
rollt) oder 1.6.0 verzoegern. Melder wartet auf Fix-Link im Issue.
