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
