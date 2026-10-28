# Phase 34, Plan 02: Nachweis der Abschalt-Schritte auf 8090

## Stand

| Feld | Wert |
|---|---|
| Datum | 19.10.2026, Lauf 06:25 bis 06:30 UTC |
| Commit | `00dbafab` (main, vor den Commits dieses Plans) |
| Instanz | Dev-Nextcloud `findling-nextcloud` auf Port 8090 (`scripts/dev/compose.yaml`, Dienst `app`), Datenbank SQLite (`data/nextcloud.db`, Präfix `oc_`) |
| Nextcloud | 34.0.3 (`occ status`: 34.0.3.2) |
| Aktive Apps vorher | `app_api` 34.0.0, `findling` 1.4.2; keine App mit "fulltext" im Namen, weder aktiv noch deaktiviert |
| Getestete Apps | fulltextsearch 34.0.2, files_fulltextsearch 34.0.1 (aus dem App Store, `min-version="34" max-version="34"`) |
| Nicht installiert | fulltextsearch_elasticsearch und Elasticsearch selbst (D-34-02, kein Elasticsearch-Container) |
| Freier RAM vorher | 2,27 GB, deshalb alles seriell |

Aufruf von occ: `docker compose exec -T -u www-data app php occ ...` mit `COMPOSE_FILE=scripts/dev/compose.yaml`
und `FINDLING_PORT=8090`. Tabellen, Migrationen, `oc_appconfig` (nur Schlüssel, keine Werte) und `oc_jobs` las
ein kleines PHP-Skript über PDO aus der SQLite-Datei (im Container gibt es kein `sqlite3`). Rohausgaben lagen im
Scratchpad der Sitzung (`34-02/00-...` bis `07-...`).

## Ausgangszustand

```
== tables oc_fulltextsearch%
== oc_migrations app LIKE %fulltextsearch%
== oc_appconfig appid LIKE %fulltextsearch% (keys only)
== oc_jobs class LIKE %FullTextSearch%
== end
enabled: {'app_api': '34.0.0', 'findling': '1.4.2'}
disabled: {}
```

## Durchlauf

| # | Befehl | Ergebnis (Kurzausgabe) | Urteil | Auf die Seite |
|---|---|---|---|---|
| 1a | `occ app:install fulltextsearch` | `Error: Cannot write into "apps" directory.` exit 1 | Eigenheit der Dev-Instanz: `custom_apps` gehört `root`, weil Docker das Verzeichnis für den Bind-Mount von `php/` angelegt hat. Vorübergehend `chown www-data:www-data /var/www/html/custom_apps` (nur das Verzeichnis, nicht der Mount), am Ende zurück auf `root:root` | nein |
| 1b | `occ app:install fulltextsearch`, `occ app:install files_fulltextsearch` | `fulltextsearch 34.0.2 installed` / `enabled`; `files_fulltextsearch 34.0.1 installed` / `enabled`, je exit 0 | auf 8090 gefahren, A3 bestätigt | nein (Vorbedingung) |
| 2 | Tabellen nach der Installation | `oc_fulltextsearch_index rows=0`, `oc_fulltextsearch_ticks rows=0`; sieben Einträge in `oc_migrations` für `fulltextsearch` (`2000Date20201208130255` bis `31001Date20250210105322`); `oc_appconfig` je drei Schlüssel (`enabled`, `installed_version`, `types`); `oc_jobs` `OCA\FullTextSearch\Cron\Index` | auf 8090 gefahren, wie im Research erwartet | ja (Tabellennamen) |
| 3a | `occ fulltextsearch:reset`, Antwort `n` | `WARNING! You are about to reset your indexed documents:` / `- provider: ALL` / `- collection: ALL` / `Do you really want to reset your indexed documents ? (y/N)` / `aborted.` exit 0 | auf 8090 gefahren | nein |
| 3b | `occ fulltextsearch:reset --no-interaction` | gleiche Warnung, dann ohne Frage `aborted.` exit 0, nichts gelöscht | auf 8090 gefahren; Interaktiv-Falle: in einem Skript mit `-n` endet der Befehl mit exit 0, tut aber nichts | ja |
| 3c | `occ fulltextsearch:reset`, Antwort `y`, dann `reset` | zweite Frage `Please confirm this destructive operation by typing 'reset ALL ALL':`, falsche Eingabe: `aborted.` exit 0 | auf 8090 gefahren; die getippte Bestätigung ist wörtlich `reset ALL ALL` | nein (Seite sagt "getippte Bestätigung") |
| 3d | `occ fulltextsearch:reset`, Antwort `y`, dann `reset ALL ALL` (keine Plattform eingerichtet) | `WARNING! This operation is not reversible.` dann `In PlatformService.php line 154:` / `Admin have not selected any IFullTextSearchPlatform` / Synopsis des Befehls, exit 1; kein PHP-Stacktrace | auf 8090 gefahren, A2 bestätigt (verständlicher Fehler statt Absturz). `IndexService::resetIndex()` holt zuerst die Plattform (`lib/Service/IndexService.php:541-548` der installierten 34.0.2), die Ausnahme fällt davor, die Indextabelle wird also nicht geleert; der Runner hinterlässt eine Zeile in `oc_fulltextsearch_ticks` (`source=commandReset`, `status=stop`) | ja |
| 3e | `occ fulltextsearch:stop` | `stopping all running indexes` exit 0; Tick-Zeile unverändert `status=stop` | auf 8090 gefahren; läuft ohne Plattform fehlerfrei | ja (Befehl) |
| 4 | `occ app:disable files_fulltextsearch fulltextsearch` (ein Aufruf) | `files_fulltextsearch 34.0.1 disabled`, `fulltextsearch 34.0.2 disabled`, exit 0; `app:list`: beide unter disabled | auf 8090 gefahren; mehrere IDs in einem Aufruf gehen | ja |
| 4b | `occ app:disable fulltextsearch_elasticsearch` (nicht installiert) | `No such app enabled: fulltextsearch_elasticsearch` exit 0 | auf 8090 gefahren; eine nicht vorhandene ID in der Liste bricht nichts ab | nein (bestätigt die Formulierung "die verwendete Plattform-App nennen") |
| 5a | Tabellen nach `app:disable` | `oc_fulltextsearch_index rows=0`, `oc_fulltextsearch_ticks rows=1`, Migrationen, `oc_appconfig`, `oc_jobs` unverändert | auf 8090 gefahren | nein |
| 5b | `occ app:remove files_fulltextsearch`, `occ app:remove fulltextsearch` | `Disabled app 'files_fulltextsearch' (uninstall steps executed).` / `Removed app 'files_fulltextsearch' (version 34.0.1).`; dasselbe für `fulltextsearch` (34.0.2), je exit 0; App-Verzeichnisse unter `custom_apps` weg | auf 8090 gefahren | ja (Befehl) |
| 5c | Tabellen nach `app:remove` | `oc_fulltextsearch_index rows=0`, `oc_fulltextsearch_ticks rows=1`, sieben Migrationseinträge, `oc_appconfig` je drei Schlüssel, `oc_jobs` `OCA\FullTextSearch\Cron\Index` weiter vorhanden | auf 8090 gefahren, A1 bestätigt: beide Tabellen bleiben liegen, ebenso ihre Migrationseinträge | ja |
| 6a | Aufräumweg, als Vorschlag für die Seite: `DROP TABLE oc_fulltextsearch_index;`, `DROP TABLE oc_fulltextsearch_ticks;`, `DELETE FROM oc_migrations WHERE app = 'fulltextsearch';` | drei Anweisungen ohne Fehler, sieben Migrationszeilen gelöscht; danach keine `oc_fulltextsearch%`-Tabelle und kein Migrationseintrag | auf 8090 gefahren (SQLite; die Anweisungen sind Standard-SQL ohne Dialektteil) | ja, mit Warnhinweis Datensicherung |
| 6b | Gegenprobe: `occ app:install fulltextsearch` nach dem Aufräumen | `fulltextsearch 34.0.2 installed` / `enabled`; beide Tabellen und alle sieben Migrationen wieder da; danach `occ app:remove fulltextsearch` und erneut 6a | auf 8090 gefahren; mit gelöschten Migrationseinträgen legt eine Neuinstallation die Tabellen wieder an (der Fall "Tabellen gelöscht, Einträge stehen lassen" wurde nicht gefahren; nach der Migrationslogik würde Nextcloud die Migrationen dann als erledigt überspringen) | ja (ein Satz) |
| 7a | systemd-Unit für `occ fulltextsearch:live` | Wiki `Basic-Installation.md`, Abruf 19.10.2026: Unit `/etc/systemd/system/nextcloud-fulltext-elasticsearch-worker.service` mit `ExecStart=/usr/bin/php /var/www/nextcloud/occ fulltextsearch:live -q` und `Restart=always` (Zeilen 49-66) | aus Quelle belegt, auf 8090 nicht ausführbar (kein systemd im Container) | ja (Schritt 2, Link auf Wiki) |
| 7b | Nextcloud AIO | `nextcloud/all-in-one` `Containers/nextcloud/entrypoint.sh`, Branch `main`, letzter Commit der Datei `2dbd5083` (01.10.2026), per `gh api` am 19.10.2026 gelesen: Zeile 1049 `# Fulltextsearch`, 1050 `if [ "$FULLTEXTSEARCH_ENABLED" = 'yes' ]`, 1066-1085 installiert oder aktiviert `fulltextsearch`, `fulltextsearch_elasticsearch`, `files_fulltextsearch` bei jedem Start; 1104-1115 entfernt sie nur bei `REMOVE_DISABLED_APPS=yes`. Zeilen 1049-1115 aus dem Research bestätigt | aus Quelle belegt, auf 8090 nicht ausführbar (keine AIO) | ja (Schritt 7) |
| 7c | Elasticsearch-Index und Ingest-Pipeline | `nextcloud/fulltextsearch_elasticsearch` `lib/Service/IndexService.php`, Branch `master`, letzter Commit der Datei `a6ae8942f0` (07.10.2026): `resetIndexAll()` Zeile 114, `deletePipeline` Zeile 117, `indices()->delete` Zeile 123; Zeilen 114-128 aus dem Research bestätigt | aus Quelle belegt, auf 8090 nicht ausführbar (D-34-02, kein Elasticsearch) | ja (Schritt 3, "Index und Ingest-Pipeline"; Schritt 6) |

Nebenbefund `oc_jobs`: Der verwaiste Hintergrundjob `OCA\FullTextSearch\Cron\Index` verschwindet von selbst:
Nextcloud entfernt einen Job, dessen Klasse fehlt, beim nächsten Laden (`lib/private/BackgroundJob/JobList.php`,
`buildJob()`, Kommentar "Remove job from disabled app or old version of an app"). Auf 8090 hat bereits
`occ background-job:list` den Eintrag so entfernt. Gehört nicht auf die Seite.

Store-Stand erneut abgefragt (19.10.2026, 06:29 UTC, App-Store-API `platform/{32.0.0,33.0.0,34.0.3,35.0.0}`
und GitHub-Releases): alle Werte wie in 34-WORTLAUT.md "Abfrage des Pflegestands"; die Seiten übernehmen sie
unverändert.

## Ergebnis zu den Annahmen

- **A1 (Tabellen bleiben liegen): bestätigt.** Nach `occ app:disable` und nach `occ app:remove` (Ausgabe
  "uninstall steps executed") stehen `oc_fulltextsearch_index` und `oc_fulltextsearch_ticks` weiter in der
  Datenbank, dazu die sieben Einträge in `oc_migrations` und die `oc_appconfig`-Schlüssel. Aufräumweg 6a auf
  8090 gefahren, Neuinstallation danach als Gegenprobe erfolgreich (6b).
- **A2 (reset ohne Plattform verständlich): bestätigt.** Ohne eingerichtete Plattform endet
  `occ fulltextsearch:reset` nach beiden Bestätigungen mit "Admin have not selected any
  IFullTextSearchPlatform", exit 1, ohne Stacktrace, und löscht nichts. Zusätzlich die Interaktiv-Falle:
  mit `--no-interaction` bricht er mit `aborted.` und exit 0 ab, ohne etwas zu tun. Nicht geprüft: eine
  eingerichtete, aber nicht erreichbare Elasticsearch-Plattform (bräuchte `fulltextsearch_elasticsearch`;
  bleibt aus dem Quelltext: `resetIndexAll()` fängt nur `ClientResponseException`, ein Verbindungsfehler ginge
  also als Ausnahme durch).
- **A3 (Installation aus dem Store ohne Elasticsearch): bestätigt** für fulltextsearch 34.0.2 und
  files_fulltextsearch 34.0.1 auf Nextcloud 34.0.3, nach der Dev-Anpassung der Rechte an `custom_apps`
  (Schritt 1a).

## Nur aus Quellen belegt

| Schritt der Seite | Quelle |
|---|---|
| 2, systemd-Dienst von `fulltextsearch:live` stoppen und deaktivieren | Wiki `Basic-Installation.md` Zeilen 49-66 (`Restart=always`), `Commands.md` |
| 3, Wirkung auf der Plattform (Elasticsearch: Index und Ingest-Pipeline) | `fulltextsearch_elasticsearch` `lib/Service/IndexService.php:114-128` |
| 6, Elasticsearch-Dienst stoppen | Wiki `Basic-Installation.md` (Dienst außerhalb von Nextcloud) |
| 7, AIO-Option abwählen | `nextcloud/all-in-one` `Containers/nextcloud/entrypoint.sh:1049-1115` |

Die Seite kennzeichnet diese Schritte über den Quellenlink im Schritt; die auf 8090 gefahrenen Befunde (Schritte
3 und 5) tragen den Zusatz "geprüft mit Nextcloud 34.0.3".

## Endzustand

Wiederhergestellt nach dem Durchlauf:

- `occ config:app:delete` für `enabled`, `installed_version`, `types` beider Apps (sechs Schlüssel);
  Hintergrundjob schon von Nextcloud entfernt (siehe Nebenbefund);
- Tabellen und Migrationseinträge per 6a entfernt;
- `custom_apps` wieder `root:root` wie vorher.

Beleg nach dem Aufräumen:

```
== tables oc_fulltextsearch%
== oc_migrations app LIKE %fulltextsearch%
== oc_appconfig appid LIKE %fulltextsearch% (keys only)
== oc_jobs class LIKE %FullTextSearch%
== end
enabled: {'app_api': '34.0.0', 'findling': '1.4.2'}
disabled: {}
```

Findling unverändert: Admin-Seite `settings/admin/findling` HTTP 200 mit dem Bannerblock
`findling-coverage`; `exclusions` = `["Archiv"]`; Unified Search `providers/findling/search?term=findling-canary`
liefert genau einen Treffer (`findling-canary`).
