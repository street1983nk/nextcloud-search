# Phase 34: aufgeschobene Punkte

- **186 Datenbankabfragen je Pollaufruf der Admin-Seite** (gefunden in 34-06 Task 3, P3):
  `GET /apps/findling/admin/overview` als admin auf 8090 (Nextcloud 34.0.3, SQLite) kostet je
  Aufruf 186 Abfragen, mit und ohne das simulierte Flag gleich. Phase 34 fügt keine hinzu.
  Ob die Zahl aus dem Kern oder aus `AdminViewService::overview()` kommt, ist nicht
  aufgeschlüsselt; Rohdaten mit Backtrace lassen sich mit `.dev/audit34/p3_queries.py`
  erneut erzeugen. Vorschlag: in der Launch-Härtung (Phase 36) aufschlüsseln, der Poll läuft
  alle 5 Sekunden.
