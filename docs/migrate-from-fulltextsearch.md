Deutsch | [English](migrate-from-fulltextsearch.en.md) | [Français](migrate-from-fulltextsearch.fr.md)

# Von fulltextsearch/Elasticsearch umsteigen

Diese Seite ist für Admins, die bisher die Volltextsuche von Nextcloud (fulltextsearch) mit
Elasticsearch oder einer anderen Plattform-App nutzen und auf Findling wechseln wollen. Findling
bringt Volltextsuche, semantische Suche und OCR ohne Dateiänderung und ohne Elasticsearch in einem
Container mit, die Treffer erscheinen in der normalen Suchleiste.

Stand: 19.10.2026

## Was Findling mitbringt

- Volltextsuche mit deutscher Wortbehandlung: Komposita, Flexion, Umlaute
  ([german-analyzer.md](german-analyzer.md))
- Texterkennung für gescannte PDFs und Bilder; der erkannte Text landet nur im Index, die Datei
  bleibt unverändert ([ocr.md](ocr.md))
- Semantische Suche: findet Dokumente auch über Umschreibungen ([embeddings.md](embeddings.md))
- Dateitypen von PDF und Office bis Mails (EML), Inhalt von ZIP-Dateien, DOC, XLS und HEIC
  ([formats.md](formats.md))
- Filter nach Dateityp und Ordner in der Suchleiste ([search-filters.md](search-filters.md))
- Ausschluss von Ordnern und Mustern auf der Verwaltungsseite ([admin-page.md](admin-page.md))
- Jeder Treffer wird von Nextcloud rechtegeprüft ([privacy.md](privacy.md))
- Keine Konfiguration: der erste Indexlauf startet von selbst ([admin-page.md](admin-page.md))
- Leistungsprofile Sparsam, Standard und Leistung ([profiles.md](profiles.md))

## Was sich beim Umstieg ändert

- **Deck-Karten:** Deck liefert seine Karten an fulltextsearch
  ([Quelle](https://github.com/nextcloud/deck/blob/main/appinfo/info.xml)). Findling indexiert nur
  Dateien. Nach dem Umstieg sind Deck-Karten nicht mehr volltextindexiert; die eigene Suche von Deck
  bleibt.
- **Externe Speicher:** bei Findling standardmäßig aus, Team Folders an. Einschalten über
  "Externen Speicher indexieren" auf der Verwaltungsseite ([admin-page.md](admin-page.md)).
- **Voraussetzungen:** Nextcloud 33 bis 35 mit der App AppAPI und HaRP als Deploy-Ziel (Docker).
  Findling besteht aus zwei Store-Einträgen, `findling` und `findling_backend`, immer in derselben
  Version. Statt eines Suchdienstes läuft ein Container.
- **Suchleiste:** Findlings Treffer stehen in der Gruppe "Dateiinhalte", nicht mehr in der Gruppe
  von fulltextsearch ("Full Text Search" im Quelltext).

## Pflegestand von fulltextsearch

fulltextsearch wird von Nextcloud gepflegt. Diese Seite beschreibt den Wechsel, sie bewertet die
App nicht. Abgefragt am 19.10.2026 über den App Store und GitHub:

- fulltextsearch: Release [v35.0.0](https://github.com/nextcloud/fulltextsearch/releases) am
  20.09.2026; im [App Store](https://apps.nextcloud.com/apps/fulltextsearch) 33.0.3 (20.09.2026)
  für Nextcloud 33 bis 35, dazu 34.0.2 und 35.0.0 (18.09.2026)
- files_fulltextsearch: im [App Store](https://apps.nextcloud.com/apps/files_fulltextsearch)
  34.0.1 (06.08.2026) für Nextcloud 34 und 35.0.0 (18.09.2026) für Nextcloud 35
- fulltextsearch_elasticsearch: Releases
  [v35.0.1 und v34.0.3](https://github.com/nextcloud/fulltextsearch_elasticsearch/releases) am
  07.10.2026; diese Plattform-App braucht einen Elasticsearch-Dienst
- files_fulltextsearch_tesseract, die OCR im fulltextsearch-Stack: im
  [App Store](https://apps.nextcloud.com/apps/files_fulltextsearch_tesseract) nur ein Release für
  Nextcloud 32 (32.0.0, 19.01.2026), für Nextcloud 33 bis 35 keins
- Plattform-Apps ohne Suchdienst von Drittanbietern:
  [fulltextsearch_sql](https://apps.nextcloud.com/apps/fulltextsearch_sql) 1.5.1 (14.10.2026) und
  [fulltextsearch_postgresql](https://apps.nextcloud.com/apps/fulltextsearch_postgresql) 0.1.4
  (10.10.2026)

## Schritte

Reihenfolge einhalten: erst ist Findling fertig, dann wird abgeschaltet, so bleibt die Suche nie leer.

1. Findling installieren (beide Store-Einträge) und den ersten Indexlauf abwarten; der Deckungsgrad
   auf der Verwaltungsseite zeigt den Stand. Solange beide Systeme laufen, zeigt die
   Verwaltungsseite einen Hinweis.
2. Laufende Indexierung von fulltextsearch stoppen: `occ fulltextsearch:stop`. Läuft
   `occ fulltextsearch:live` als systemd-Dienst, diesen Dienst stoppen und deaktivieren, sonst
   startet systemd ihn immer wieder ([Commands](https://github.com/nextcloud/fulltextsearch/wiki/Commands),
   [Basic Installation](https://github.com/nextcloud/fulltextsearch/wiki/Basic-Installation)).
3. Den Index löschen, solange die Apps und der Suchdienst noch laufen: `occ fulltextsearch:reset`.
   Der Befehl verlangt eine getippte Bestätigung. Er entfernt den Index auf der Plattform (bei
   Elasticsearch Index und Ingest-Pipeline) und leert die Indextabelle von fulltextsearch.
   Mit `--no-interaction` bricht der Befehl ohne Rückfrage ab und löscht nichts. Ohne eingerichtete
   Plattform endet er nach der Bestätigung mit dem Fehler
   `Admin have not selected any IFullTextSearchPlatform` und löscht ebenfalls nichts (geprüft mit
   Nextcloud 34.0.3 und fulltextsearch 34.0.2).
4. Die Apps deaktivieren, mehrere in einem Aufruf:
   `occ app:disable files_fulltextsearch fulltextsearch_elasticsearch fulltextsearch`. Statt
   `fulltextsearch_elasticsearch` die verwendete Plattform-App nennen, falls vorhanden auch
   `files_fulltextsearch_tesseract`. Beim nächsten Laden der Verwaltungsseite ist Findlings Hinweis
   weg.
5. Optional die Apps entfernen: `occ app:remove <app-id>`. Die Tabellen `oc_fulltextsearch_index`
   und `oc_fulltextsearch_ticks` und ihre Einträge in `oc_migrations` bleiben dabei liegen (geprüft
   mit Nextcloud 34.0.3). Wer sie entfernen will, legt vorher eine Datensicherung der Datenbank an
   und führt dann diese Anweisungen aus; `oc_` ist das Standard-Präfix, eine Instanz mit anderem
   Präfix setzt ihres ein:

   ```sql
   DROP TABLE oc_fulltextsearch_index;
   DROP TABLE oc_fulltextsearch_ticks;
   DELETE FROM oc_migrations WHERE app = 'fulltextsearch';
   ```

   Eine spätere Neuinstallation von fulltextsearch legt die Tabellen wieder an.
6. Den Elasticsearch-Dienst außerhalb von Nextcloud stoppen und seine Daten entfernen, sofern er
   nichts anderes bedient. Mit einer Plattform-App ohne Suchdienst entfällt dieser Schritt.
7. Nextcloud AIO: in der AIO-Oberfläche die Option "Fulltextsearch" abwählen. Ein `occ app:disable`
   allein dreht AIO beim nächsten Containerstart zurück, solange die Option gewählt ist
   ([entrypoint.sh](https://github.com/nextcloud/all-in-one/blob/main/Containers/nextcloud/entrypoint.sh)).
