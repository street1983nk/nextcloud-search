Deutsch | [English](backup.en.md) | [Français](backup.fr.md)

# Findling sichern

Zwei Wege, das Index-Volume konsistent zu sichern (Issue #37).

## Was wo liegt

- Einstellungen (Ausschlüsse, Größengrenze, Team Folders, externe Speicher, Pause-Wunsch) liegen
  im `appconfig` der Nextcloud-Datenbank. Das normale Datenbank-Backup der Nextcloud sichert sie.
- Das Volume `nc_app_findling_backend_data` enthält `state.db`, `vectors.db` und den Suchindex.
- Das Volume ist vollständig aus den Dateien neu aufbaubar. Ein Backup spart nur die Zeit für OCR
  und Embeddings.
- Der Index enthält den extrahierten Text der Dokumente unverschlüsselt. Das Backup wie ein
  Datei-Backup schützen (verschlüsselt, Zugriff beschränkt).

## Weg A: Container stoppen

1. `docker stop nc_app_findling_backend`
2. Volume `nc_app_findling_backend_data` kopieren (tar oder das eigene Backup-Werkzeug)
3. `docker start nc_app_findling_backend`

- Der Container schließt Index und Datenbanken beim Stoppen sauber.
- Die Suche ist währenddessen aus.

## Weg B: Pause, die Suche läuft weiter

1. `occ findling:pause --wait` kehrt erst zurück, wenn der Status pausiert meldet. Alternativ
   auf der Admin-Seite den Schalter "Indexierung pausieren" setzen und warten, bis dort pausiert
   steht ([admin-page.md](admin-page.md)).
2. Volume `nc_app_findling_backend_data` kopieren.
3. `occ findling:resume` oder Schalter "Indexierung fortsetzen".

- Bei pausiert ist die Indexierung angehalten und alles auf die Platte geschrieben; die Suche
  läuft weiter.
- Backup erst bei pausiert starten, nicht bei "Pause wird vorbereitet".
- "Pause wird vorbereitet" dauert, bis der laufende Stapel fertig ist, bei OCR bis etwa 30 Minuten.
- Die Pause übersteht Neustarts von Container und Nextcloud. Ist der Wunsch nach einem Neustart
  noch nicht lesbar, bleibt die Indexierung ebenfalls angehalten.
- Die Crawl-Jobs der Companion-App laufen weiter. Sie schreiben nur in die Nextcloud-Datenbank,
  nicht ins Volume; die Warteschlange wird nach dem Fortsetzen abgearbeitet.
- Ein laufender Neuaufbau des Index hält zwischen zwei Abschnitten an und setzt danach fort. Ein
  Backup in dieser Zeit enthält zwei Index-Verzeichnisse ([uninstall.md](uninstall.md)).

## Wiederherstellen

1. `docker stop nc_app_findling_backend`
2. Volume `nc_app_findling_backend_data` zurückspielen
3. `docker start nc_app_findling_backend`

- Der Pause-Wunsch liegt nicht im Volume, sondern in der Nextcloud-Datenbank. Ein zurückgespieltes
  Volume folgt dem aktuellen Schalterstand; nach Weg B also `occ findling:resume` nicht vergessen.
