# 36-05 Schritt 0: Vorprüfung der Mount-Semantik auf Dev-8090

Datum: 20.10.2026, 17:53 bis 17:58 UTC. Instanz: `findling-nextcloud` (nextcloud:34.0.3-apache, SQLite), Port 8090.
SQL ausschließlich lesend über ein PDO-Hilfsskript im Container (`php /tmp/q36.php "SELECT ..."`), kein Schreibzugriff auf die Nextcloud-DB.

Frage: Welcher Core-Weg entfernt die oc_mounts-Zeilen eines abgehängten externen Speichers, ohne die oc_storages-Zeile anzufassen? Nur dieser Weg darf die Vorbedingung im CI-Test erzeugen (T-36-20b, kein SQL-Löschen in oc_mounts).

## Ausgangszustand

- `files_external`: bereits aktiviert (Abschnitt "Enabled" von `occ app:list`). Bleibt so.
- `files_external_allow_create_new_local`: nicht gesetzt.
- Findling-Schalter `index_external_storage`: `0` (aus).
- Externe Speicher: keine (`oc_external_mounts` 0 Zeilen, `oc_external_applicable` 0 Zeilen).

```
oc_storages: 1 local::/var/www/html/data/ | 2 home::admin | 3 home::testuser | 4 home::kollegin
             5..8 sftp::u1/u2@findling-sftp (Reste früherer Spikes, ohne Mount)
oc_mounts:   storage 2 admin, storage 3 testuser, storage 3 kollegin (Freigabe), storage 4 kollegin
```

## Aufbau

```
occ config:system:set files_external_allow_create_new_local --value=true --type=boolean
OC_PASS=... occ user:add --password-from-env ext36v
OC_PASS=... occ user:add --password-from-env nobody36v
mkdir /var/www/html/data/e36v-ext; probe.txt mit "Vorpruefung Wortprobe Mountsemantik"
occ files_external:create /e36v local null::null -c datadir=/var/www/html/data/e36v-ext   -> Mount ID 5
occ files_external:applicable 5 --add-user ext36v
PROPFIND /remote.php/dav/files/ext36v/ als ext36v                                           -> 207
```

SQL danach:

```
oc_storages: 16 | local::/var/www/html/data/e36v-ext/     17 | home::ext36v
oc_mounts:   32 | storage 16 | ext36v | /ext36v/files/e36v/ | mount_id 5 | OCA\Files_External\Config\ConfigAdapter
             31 | storage 17 | ext36v | /ext36v/            | NULL       | OC\Files\Mount\LocalHomeMountProvider
```

## Abhängen auf den Platzhalter-Nutzer

```
occ files_external:applicable 5 --remove-user ext36v --add-user nobody36v
```

SQL direkt danach, noch ohne jeden Auffrisch-Weg:

```
oc_mounts:   33 | storage 16 | nobody36v | /nobody36v/files/e36v/ | mount_id 5
             31 | storage 17 | ext36v    | /ext36v/
oc_storages: 16 und 17 vorhanden
```

Befund: Nextcloud 34 hält oc_mounts für files_external bei jeder Änderung der Anwendbarkeit sofort synchron. Die Zeile von ext36v ist schon nach dem `applicable`-Aufruf weg, und für den Platzhalter `nobody36v` steht sofort eine neue Zeile da, obwohl er sich nie angemeldet hat. Die Annahme aus RESEARCH (veraltete oc_mounts-Zeile, die erst ein Auffrisch-Weg entfernt) trifft nicht zu.

## Die drei Wege

| Weg | Befehl | oc_mounts für Storage 16 danach | oc_storages 16 danach |
|-----|--------|----------------------------------|------------------------|
| W1 | `occ files:scan ext36v` | Zeile 33 (nobody36v) bleibt | da |
| W2 | `PROPFIND /remote.php/dav/files/ext36v/` als ext36v (207) | Zeile 33 (nobody36v) bleibt | da |
| W3 | `occ files:scan --all` | Zeile 33 (nobody36v) bleibt, zusätzlich Zeile 34 Home von nobody36v (Storage 18) | da |

Keiner der Wege W1 bis W3 leert oc_mounts für den Speicher. Das liegt nicht an den Wegen, sondern am Platzhalter: Wer in der Anwendbarkeit steht, hat sofort eine oc_mounts-Zeile. Mit einem Platzhalter-Nutzer ist ein Speicher deshalb nie "für niemanden eingebunden", und genau so muss Findling ihn auch behandeln (er ist für jemanden eingebunden, die Dokumente bleiben).

## Zusatzwege V4 und V5 (Core, kein SQL)

| Weg | Befehl | oc_mounts für Storage 16 danach | oc_storages 16 danach |
|-----|--------|----------------------------------|------------------------|
| V4 | `occ group:add g36v-leer`, dann `occ files_external:applicable 5 --remove-user nobody36v --add-group g36v-leer` | 0 Zeilen, sofort, und auch nach `occ files:scan --all` | da (dazu 1 Zeile oc_filecache) |
| V5 | `occ files_external:delete -y 5` (als Teil des Rückbaus) | 0 Zeilen | **da**, die Zeile bleibt stehen |

V4 ist der realistische Fall "Speicher existiert, ist aber für niemanden mehr eingebunden" (Anwendbarkeit nur noch auf eine leere Gruppe, etwa nachdem alle Mitglieder ausgetreten sind) und erzeugt die Vorbedingung ohne jeden Auffrisch-Weg. V5 zeigt nebenbei, woher der Dev-Fall Storage 7 (sftp) stammt: Das Löschen einer files_external-Konfiguration entfernt die Mounts, lässt die oc_storages-Zeile aber stehen. Für Findling ist auch das ein verschwundener Speicher (Karenz), kein gelöschter.

## Entscheidung für CI

Kein Weg W1 bis W3 leert oc_mounts, das Produkt ist aber nicht betroffen: Die Mountliste von Findling (`getDistinctMounts`) folgt oc_mounts, und oc_mounts folgt der Anwendbarkeit in Nextcloud 34 sofort. Ein Speicher, der für niemanden mehr eingebunden ist (V4) oder dessen Konfiguration gelöscht wurde (V5), fällt in derselben Sekunde aus der Mountliste. Es gibt also keinen Produktbefund im Sinne des Plans (Speicher würde nie als verschwunden gesehen), sondern einen Befund am Testaufbau: Der Platzhalter-Nutzer erzeugt die Vorbedingung nicht.

Verbindlich für CI ist **V4**: E2 und E3 werden per `occ files_external:applicable <id> --remove-user ext36 --add-group <leere Gruppe>` abgehängt. Ein Auffrisch-Weg ist nicht nötig; die SQL-Prüfung der Vorbedingung (oc_mounts ohne E2/E3, oc_storages mit E2/E3) bleibt im Workflow als Gegenprobe der Core-Semantik. Der Platzhalter-Nutzer entfällt.

## Rückbau

```
occ files_external:delete -y 5                        -> oc_mounts 0 Zeilen für 16, oc_storages 16 bleibt (Core, siehe V5)
occ user:delete ext36v                                -> oc_storages 17 (home::ext36v) entfernt
occ user:delete nobody36v                             -> oc_storages 18 (home::nobody36v) entfernt
occ group:delete g36v-leer
occ config:system:delete files_external_allow_create_new_local   -> wieder nicht gesetzt
rm -rf /var/www/html/data/e36v-ext
files_external bleibt aktiviert (Ausgangszustand)
```

SQL nach dem Rückbau: `oc_storages` ab 16 nur noch `16 | local::/var/www/html/data/e36v-ext/` (vom Core so belassen, ohne Mount, ohne Dateien in Findling), `oc_mounts` ab Storage 16 leer, `occ files_external:list` meldet "No admin mounts configured".

Nebenwirkung, die im Live-Beleg (Task 2) mitgezählt wird: Der Wegwerf-Nutzer ext36v bekam beim Anlegen die Skeleton-Dateien, und der laufende Host-Backend-Prozess hat sie über die Ereignisse indexiert (state.db: Storage 17 mit 49 lebenden Zeilen). Mit `user:delete ext36v` ist Storage 17 jetzt ein gelöschter Speicher wie 14 und 15 und muss im ersten Zyklus ebenfalls verschwinden.
