# Phase 34: Wortlaut-Entwurf (de, en, fr)

Stand: 19.10.2026, Entwurf aus Plan 34-01 Task 1 auf Basis von Commit 2dd8a566.
Status: **Entwurf, Owner-Abnahme offen** (blockierender Checkpoint 34-01 Task 2, siehe "Owner-Abnahme" am Ende).
Abfragedatum der Fakten über fulltextsearch: 19.10.2026, 06:09 UTC (GitHub-API `repos/nextcloud/<app>/releases`
und App-Store-API `https://apps.nextcloud.com/api/v1/platform/{32.0.0,33.0.0,34.0.3,35.0.0}/apps.json`).

Grundlage: 34-CONTEXT.md (D-34-01, D-34-02, PE-34-1 bis PE-34-7, Leitplanken), 34-RESEARCH.md
(Fakten über fulltextsearch, Abschalt-Schritte, Verluste, Funktionsvergleich, Kurztext-Regel), 34-01-PLAN.md.

Regeln für alle Zeilen:

- Pflichtformel de wörtlich "OCR ohne Dateiänderung und ohne Elasticsearch"; en/fr nach Vorschlag O2.
- fulltextsearch wird als gepflegt beschrieben (Releases mit Datum und Link); keine Abwertung, kein Vergleich
  "besser/schlechter", Fremd-OCR-Apps außerhalb des fulltextsearch-Stacks werden nicht genannt.
- Nicht geschrieben wird, dass fulltextsearch Elasticsearch braucht; richtig ist: die Plattform-App
  `fulltextsearch_elasticsearch` braucht einen Elasticsearch-Dienst.
- Funktionsliste nur aus Geliefertem (Phasen bis 33), keine Zahl in der Liste "Was Findling mitbringt";
  Ähnliche Dokumente (Phase 35) fehlt mit Absicht.
- Französisch nach `docs/l10n-french.md`: ASCII-Apostroph, einfaches Leerzeichen vor `:`, `;`, `?`, `!`.
- Deutsch in Handlungsanweisungen im Infinitiv wie der Katalogbestand.
- Links in den Seiten relativ innerhalb von `docs/`, Quellen über fulltextsearch absolut.
- Vorab-Prüfung über alle Entwurfstexte (Ergebnis am Ende von Abschnitt E).

## Abfrage des Pflegestands (19.10.2026)

| App | GitHub, letzte Releases | App Store NC 33 | NC 34 | NC 35 |
|---|---|---|---|---|
| fulltextsearch | v35.0.0 (20.09.2026), 35.0.0beta1 (12.08.2026); letzter Push 18.10.2026 | 33.0.3 (20.09.2026, `>=33 <36`) | 34.0.2 (18.09.2026) | 35.0.0 (18.09.2026) |
| files_fulltextsearch | 35.0.0beta1 (12.08.2026); letzter Push 19.10.2026 | 33.0.0 (19.02.2026) | 34.0.1 (06.08.2026) | 35.0.0 (18.09.2026) |
| fulltextsearch_elasticsearch | v35.0.1 und v34.0.3 (07.10.2026) | 33.0.1 (22.09.2026) | 34.0.3 (07.10.2026) | 35.0.1 (07.10.2026) |
| files_fulltextsearch_tesseract | 24.0.0 (05.05.2022); letzter Push 19.01.2026 | keins | keins | keins (einziges Store-Release: 32.0.0 vom 19.01.2026, `>=32 <33`) |
| fulltextsearch_sql (Drittanbieter) | nicht abgefragt | 1.5.1 (14.10.2026, `>=31 <36`) | dto. | dto. |
| fulltextsearch_postgresql (Drittanbieter) | nicht abgefragt | 0.1.4 (10.10.2026, `>=32 <36`) | dto. | dto. |

Abweichung vom Research: Für Nextcloud 35 führt der Store bei fulltextsearch und files_fulltextsearch inzwischen
die Endfassung 35.0.0 (18.09.2026), nicht nur 35.0.0-beta.1. Alle anderen Werte wie im Research. Die Seite nennt
die Werte oben; 34-02 fragt vor dem Schreiben der Seiten erneut ab.

## (A) Seitengerüst

Drei Dateien nach D-34-01: `docs/migrate-from-fulltextsearch.md` (de), `.en.md`, `.fr.md`. Zeile 1 ist der
Sprachumschalter. Stellen, die 34-02 auf 8090 belegt, stehen als Platzhalterzeile `[Beleg 34-02]` mit der
Vermutung aus dem Research (A1, A2); 34-02 ersetzt sie durch den Befund. Zeilen mit `[O5]` hängen an der
Antwort auf O5.

### (A-de) `docs/migrate-from-fulltextsearch.md`

```markdown
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
- [O5] Plattform-Apps ohne Suchdienst von Drittanbietern:
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
   [Beleg 34-02: Verhalten ohne erreichbare Plattform; Vermutung A2: verständliche Fehlermeldung
   statt Absturz]
4. Die Apps deaktivieren, mehrere in einem Aufruf:
   `occ app:disable files_fulltextsearch fulltextsearch_elasticsearch fulltextsearch`. Statt
   `fulltextsearch_elasticsearch` die verwendete Plattform-App nennen, falls vorhanden auch
   `files_fulltextsearch_tesseract`. Beim nächsten Laden der Verwaltungsseite ist Findlings Hinweis
   weg.
5. Optional die Apps entfernen: `occ app:remove <app-id>`.
   [Beleg 34-02: Reste in der Datenbank; Vermutung A1: die Tabellen `oc_fulltextsearch_index` und
   `oc_fulltextsearch_ticks` bleiben liegen, weil fulltextsearch keinen Deinstallationsschritt
   deklariert]
6. Den Elasticsearch-Dienst außerhalb von Nextcloud stoppen und seine Daten entfernen, sofern er
   nichts anderes bedient. Mit einer Plattform-App ohne Suchdienst entfällt dieser Schritt.
7. Nextcloud AIO: in der AIO-Oberfläche die Option "Fulltextsearch" abwählen. Ein `occ app:disable`
   allein dreht AIO beim nächsten Containerstart zurück, solange die Option gewählt ist
   ([entrypoint.sh](https://github.com/nextcloud/all-in-one/blob/main/Containers/nextcloud/entrypoint.sh)).
```

### (A-en) `docs/migrate-from-fulltextsearch.en.md`

```markdown
[Deutsch](migrate-from-fulltextsearch.md) | English | [Français](migrate-from-fulltextsearch.fr.md)

# Switching from fulltextsearch/Elasticsearch

This page is for admins who use Nextcloud's full text search (fulltextsearch) with Elasticsearch or
another platform app and want to switch to Findling. Findling brings full text search, semantic
search and OCR without changing files and without Elasticsearch in one container, and its results
appear in the normal search bar.

As of: 19 October 2026

## What Findling brings

- Full text search with German word handling: compounds, inflection, umlauts
  ([german-analyzer.md](german-analyzer.md))
- OCR for scanned PDFs and images; the recognised text goes into the index only, the file stays
  unchanged ([ocr.md](ocr.md))
- Semantic search: finds documents through paraphrases ([embeddings.md](embeddings.md))
- File types from PDF and office documents to mails (EML), the contents of ZIP files, DOC, XLS and
  HEIC ([formats.md](formats.md))
- Filters by file type and folder in the search bar ([search-filters.md](search-filters.md))
- Exclusion of folders and patterns on the administration page ([admin-page.md](admin-page.md))
- Every result is permission-checked by Nextcloud ([privacy.md](privacy.md))
- No configuration: the first index run starts on its own ([admin-page.md](admin-page.md))
- Performance profiles Economy, Standard and Performance ([profiles.md](profiles.md))

## What changes when you switch

- **Deck cards:** Deck hands its cards to fulltextsearch
  ([source](https://github.com/nextcloud/deck/blob/main/appinfo/info.xml)). Findling indexes files
  only. After the switch, Deck cards are no longer in a full text index; Deck's own search stays.
- **External storage:** off by default in Findling, Team Folders on. Switch it on with "Index
  external storage" on the administration page ([admin-page.md](admin-page.md)).
- **Requirements:** Nextcloud 33 to 35 with the AppAPI app and HaRP as the deploy target (Docker).
  Findling consists of two store entries, `findling` and `findling_backend`, always in the same
  version. One container runs instead of a search service.
- **Search bar:** Findling's results appear in the group "File contents", no longer in the group of
  fulltextsearch ("Full Text Search").

## Maintenance status of fulltextsearch

fulltextsearch is maintained by Nextcloud. This page describes the switch, it does not judge the
app. Queried on 19 October 2026 from the App Store and GitHub:

- fulltextsearch: release [v35.0.0](https://github.com/nextcloud/fulltextsearch/releases) on
  20.09.2026; in the [App Store](https://apps.nextcloud.com/apps/fulltextsearch) 33.0.3
  (20.09.2026) for Nextcloud 33 to 35, plus 34.0.2 and 35.0.0 (18.09.2026)
- files_fulltextsearch: in the [App Store](https://apps.nextcloud.com/apps/files_fulltextsearch)
  34.0.1 (06.08.2026) for Nextcloud 34 and 35.0.0 (18.09.2026) for Nextcloud 35
- fulltextsearch_elasticsearch: releases
  [v35.0.1 and v34.0.3](https://github.com/nextcloud/fulltextsearch_elasticsearch/releases) on
  07.10.2026; this platform app needs an Elasticsearch service
- files_fulltextsearch_tesseract, the OCR of the fulltextsearch stack: in the
  [App Store](https://apps.nextcloud.com/apps/files_fulltextsearch_tesseract) only one release for
  Nextcloud 32 (32.0.0, 19.01.2026), none for Nextcloud 33 to 35
- [O5] Third-party platform apps without a search service:
  [fulltextsearch_sql](https://apps.nextcloud.com/apps/fulltextsearch_sql) 1.5.1 (14.10.2026) and
  [fulltextsearch_postgresql](https://apps.nextcloud.com/apps/fulltextsearch_postgresql) 0.1.4
  (10.10.2026)

## Steps

Keep the order: Findling first, then switch off, so the search is never empty.

1. Install Findling (both store entries) and wait for the first index run; the coverage on the
   administration page shows how far it is. While both systems run, the administration page shows
   a notice.
2. Stop running indexing of fulltextsearch: `occ fulltextsearch:stop`. If
   `occ fulltextsearch:live` runs as a systemd service, stop and disable that service, otherwise
   systemd starts it again and again
   ([Commands](https://github.com/nextcloud/fulltextsearch/wiki/Commands),
   [Basic Installation](https://github.com/nextcloud/fulltextsearch/wiki/Basic-Installation)).
3. Delete the index while the apps and the search service still run: `occ fulltextsearch:reset`.
   The command asks for a typed confirmation. It removes the index on the platform (with
   Elasticsearch the index and the ingest pipeline) and empties the index table of fulltextsearch.
   [Evidence 34-02: behaviour without a reachable platform; assumption A2: an understandable error
   instead of a crash]
4. Disable the apps, several in one call:
   `occ app:disable files_fulltextsearch fulltextsearch_elasticsearch fulltextsearch`. Instead of
   `fulltextsearch_elasticsearch` name the platform app in use, and `files_fulltextsearch_tesseract`
   if present. The next time the administration page loads, Findling's notice is gone.
5. Optionally remove the apps: `occ app:remove <app-id>`.
   [Evidence 34-02: leftovers in the database; assumption A1: the tables `oc_fulltextsearch_index`
   and `oc_fulltextsearch_ticks` stay, because fulltextsearch declares no uninstall step]
6. Stop the Elasticsearch service outside Nextcloud and remove its data, unless it serves something
   else. With a platform app without a search service this step does not apply.
7. Nextcloud AIO: deselect the option "Fulltextsearch" in the AIO interface. AIO turns a plain
   `occ app:disable` back at the next container start as long as the option is selected
   ([entrypoint.sh](https://github.com/nextcloud/all-in-one/blob/main/Containers/nextcloud/entrypoint.sh)).
```

### (A-fr) `docs/migrate-from-fulltextsearch.fr.md`

```markdown
[Deutsch](migrate-from-fulltextsearch.md) | [English](migrate-from-fulltextsearch.en.md) | Français

# Passer de fulltextsearch/Elasticsearch à Findling

Cette page s'adresse aux administrateurs qui utilisent la recherche plein texte de Nextcloud
(fulltextsearch) avec Elasticsearch ou une autre application de plateforme et veulent passer à
Findling. Findling apporte la recherche plein texte, la recherche sémantique et l'OCR sans modifier
les fichiers et sans Elasticsearch dans un seul conteneur, et ses résultats apparaissent dans la
barre de recherche normale.

Situation au 19 octobre 2026

## Ce que Findling apporte

- Recherche plein texte avec traitement des mots allemands : mots composés, flexion, trémas
  ([german-analyzer.md](german-analyzer.md))
- Reconnaissance optique pour les PDF numérisés et les images ; le texte reconnu va uniquement dans
  l'index, le fichier reste inchangé ([ocr.md](ocr.md))
- Recherche sémantique : trouve les documents par des périphrases ([embeddings.md](embeddings.md))
- Types de fichiers du PDF et des documents bureautiques jusqu'aux e-mails (EML), au contenu des
  fichiers ZIP, DOC, XLS et HEIC ([formats.md](formats.md))
- Filtres par type de fichier et par dossier dans la barre de recherche
  ([search-filters.md](search-filters.md))
- Exclusion de dossiers et de motifs sur la page d'administration ([admin-page.md](admin-page.md))
- Chaque résultat est vérifié par Nextcloud selon les droits ([privacy.md](privacy.md))
- Aucune configuration : la première indexation démarre d'elle-même ([admin-page.md](admin-page.md))
- Profils de performance Économe, Standard et Performance ([profiles.md](profiles.md))

## Ce qui change lors du passage

- **Cartes Deck :** Deck transmet ses cartes à fulltextsearch
  ([source](https://github.com/nextcloud/deck/blob/main/appinfo/info.xml)). Findling n'indexe que
  des fichiers. Après le passage, les cartes Deck ne sont plus dans un index plein texte ; la
  recherche propre à Deck reste.
- **Stockage externe :** désactivé par défaut dans Findling, Team Folders activés. L'activer avec
  "Indexer le stockage externe" sur la page d'administration ([admin-page.md](admin-page.md)).
- **Prérequis :** Nextcloud 33 à 35 avec l'application AppAPI et HaRP comme cible de déploiement
  (Docker). Findling se compose de deux entrées du store, `findling` et `findling_backend`,
  toujours dans la même version. Un conteneur remplace le service de recherche.
- **Barre de recherche :** les résultats de Findling figurent dans le groupe "Contenu des
  fichiers", plus dans le groupe de fulltextsearch ("Full Text Search").

## État de maintenance de fulltextsearch

fulltextsearch est maintenu par Nextcloud. Cette page décrit le passage, elle ne juge pas
l'application. Consulté le 19 octobre 2026 dans l'App Store et sur GitHub :

- fulltextsearch : version [v35.0.0](https://github.com/nextcloud/fulltextsearch/releases) du
  20.09.2026 ; dans l'[App Store](https://apps.nextcloud.com/apps/fulltextsearch) 33.0.3
  (20.09.2026) pour Nextcloud 33 à 35, ainsi que 34.0.2 et 35.0.0 (18.09.2026)
- files_fulltextsearch : dans l'[App Store](https://apps.nextcloud.com/apps/files_fulltextsearch)
  34.0.1 (06.08.2026) pour Nextcloud 34 et 35.0.0 (18.09.2026) pour Nextcloud 35
- fulltextsearch_elasticsearch : versions
  [v35.0.1 et v34.0.3](https://github.com/nextcloud/fulltextsearch_elasticsearch/releases) du
  07.10.2026 ; cette application de plateforme a besoin d'un service Elasticsearch
- files_fulltextsearch_tesseract, l'OCR de la pile fulltextsearch : dans
  l'[App Store](https://apps.nextcloud.com/apps/files_fulltextsearch_tesseract) une seule version
  pour Nextcloud 32 (32.0.0, 19.01.2026), aucune pour Nextcloud 33 à 35
- [O5] Applications de plateforme tierces sans service de recherche :
  [fulltextsearch_sql](https://apps.nextcloud.com/apps/fulltextsearch_sql) 1.5.1 (14.10.2026) et
  [fulltextsearch_postgresql](https://apps.nextcloud.com/apps/fulltextsearch_postgresql) 0.1.4
  (10.10.2026)

## Étapes

Respecter l'ordre : d'abord Findling, ensuite la désactivation, ainsi la recherche n'est jamais vide.

1. Installer Findling (les deux entrées du store) et attendre la première indexation ; la
   couverture sur la page d'administration montre l'avancement. Tant que les deux systèmes
   tournent, la page d'administration affiche un avertissement.
2. Arrêter l'indexation en cours de fulltextsearch : `occ fulltextsearch:stop`. Si
   `occ fulltextsearch:live` tourne comme service systemd, arrêter et désactiver ce service, sinon
   systemd le relance sans cesse
   ([Commands](https://github.com/nextcloud/fulltextsearch/wiki/Commands),
   [Basic Installation](https://github.com/nextcloud/fulltextsearch/wiki/Basic-Installation)).
3. Supprimer l'index tant que les applications et le service de recherche tournent encore :
   `occ fulltextsearch:reset`. La commande demande une confirmation saisie au clavier. Elle retire
   l'index sur la plateforme (avec Elasticsearch l'index et le pipeline d'ingestion) et vide la
   table d'index de fulltextsearch.
   [Preuve 34-02 : comportement sans plateforme joignable ; hypothèse A2 : une erreur
   compréhensible plutôt qu'un plantage]
4. Désactiver les applications, plusieurs en un seul appel :
   `occ app:disable files_fulltextsearch fulltextsearch_elasticsearch fulltextsearch`. À la place
   de `fulltextsearch_elasticsearch`, indiquer l'application de plateforme utilisée, et
   `files_fulltextsearch_tesseract` si elle est présente. Au prochain chargement de la page
   d'administration, l'avertissement de Findling a disparu.
5. Facultatif : supprimer les applications avec `occ app:remove <app-id>`.
   [Preuve 34-02 : restes dans la base de données ; hypothèse A1 : les tables
   `oc_fulltextsearch_index` et `oc_fulltextsearch_ticks` restent, car fulltextsearch ne déclare
   aucune étape de désinstallation]
6. Arrêter le service Elasticsearch hors de Nextcloud et supprimer ses données, s'il ne sert à rien
   d'autre. Avec une application de plateforme sans service de recherche, cette étape ne
   s'applique pas.
7. Nextcloud AIO : décocher l'option "Fulltextsearch" dans l'interface AIO. AIO annule un simple
   `occ app:disable` au prochain démarrage du conteneur tant que l'option est cochée
   ([entrypoint.sh](https://github.com/nextcloud/all-in-one/blob/main/Containers/nextcloud/entrypoint.sh)).
```

Hinweise zum Seitengerüst:

- Zahlen: Die Liste "Was Findling mitbringt" trägt keine Zahl. Versionsnummern und Daten stehen nur im
  Pflegestand, "Nextcloud 33 bis 35" nur bei den Voraussetzungen.
- Der Name der fulltextsearch-Gruppe in der Suchleiste ist "Full Text Search" im Quelltext
  (`nextcloud/fulltextsearch` `lib/Search/UnifiedSearchProvider.php`); seine Übersetzung ist nicht geprüft,
  deshalb steht er auf allen drei Seiten englisch.
- Schritt 2 nennt `Restart=always` nicht wörtlich, sondern "startet ihn immer wieder" (Befehlsbeispiele mit
  `name=wert` sind im Gate `test_public_artifacts.py` eine eigene Familie, hier wäre es harmlos, aber unnötig).
- Ein Abschnitt über Fremd-OCR-Apps außerhalb des fulltextsearch-Stacks fehlt mit Absicht (Leitplanke).

## (B) Hinweissatz der Admin-Seite (O7)

Platz und Bauweise nach PE-34-2: eigener Banner `findling-banner-parallel` (Art `warning`) im Block
`#findling-coverage-banners`, nur serverseitig gerendert. Der Satz trägt keinen Platzhalter und keine URL;
dahinter steht ein eigenes `<a target="_blank" rel="noreferrer noopener">` mit dem vorhandenen Schlüssel
"Steps in the documentation" (kein neuer Linkschlüssel, Schlüsselzahl 340 auf 341).

"Mindestens eine App" statt "fulltextsearch ist aktiviert": der Hinweis erscheint auch, wenn nur
files_fulltextsearch aktiv ist (PE-34-1), und dann wäre der Satz sonst falsch. "können doppelt erscheinen"
bleibt vorsichtig, weil die doppelten Treffer nur aus dem Quelltext belegt sind (Annahme A4, D-34-02).

| Schlüssel (en) | de | fr | Platzhalter |
|---|---|---|---|
| At least one app of the full text search framework (fulltextsearch, files_fulltextsearch) is enabled next to Findling. Results from the same file can then appear twice in the search bar. Disable these apps once Findling has finished its first index run. | Mindestens eine App des Volltextsuche-Frameworks (fulltextsearch, files_fulltextsearch) ist neben Findling aktiviert. Treffer aus derselben Datei können dann doppelt in der Suchleiste erscheinen. Diese Apps deaktivieren, sobald Findlings erster Indexlauf abgeschlossen ist. | Au moins une application du framework de recherche plein texte (fulltextsearch, files_fulltextsearch) est activée à côté de Findling. Les résultats d'un même fichier peuvent alors apparaître deux fois dans la barre de recherche. Désactiver ces applications une fois la première indexation de Findling terminée. | keine |
| Steps in the documentation (Bestand, wiederverwendet) | Schritte in der Dokumentation | Étapes dans la documentation | keine |

Satzlänge im Vergleich: der en-Schlüssel hat drei Sätze und 253 Zeichen; die Banner `findling-banner-lockstep`
(rund 240 Zeichen) und `findling-banner-rebuild-space` (rund 370 Zeichen) sind ähnlich lang oder länger.

Linkform (PE-34-3), drei vollständige URL-Literale in einer Map im Template, Wahl über
`IL10N::getLanguageCode()` (beginnt mit `de`: de, mit `fr`: fr, sonst en):

- de: `https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/migrate-from-fulltextsearch.md`
- en: `https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/migrate-from-fulltextsearch.en.md`
- fr: `https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/migrate-from-fulltextsearch.fr.md`

Die Tag-Links lösen erst mit dem Tag v1.5.0 auf; bis dahin prüft das Gate, dass die Zieldatei im Repo liegt.

## (C) README-Zeile (O9)

Kurztext-Regel: eine Zeile, Faktenform, keine Zahl, relativer Link auf die Seite der eigenen Sprache.

Variante 1, eine Zeile am Ende der Funktionsliste ("Was Findling kann", "What Findling does",
"Ce que Findling sait faire"):

| Sprache | Wortlaut |
|---|---|
| de (`README.md`) | `- Umstieg von fulltextsearch/Elasticsearch: [Schritte in der Dokumentation](docs/migrate-from-fulltextsearch.md)` |
| en (`README.en.md`) | `- Switching from fulltextsearch/Elasticsearch: [steps in the documentation](docs/migrate-from-fulltextsearch.en.md)` |
| fr (`README.fr.md`) | `- Passer de fulltextsearch/Elasticsearch à Findling : [étapes dans la documentation](docs/migrate-from-fulltextsearch.fr.md)` |

Variante 2, ein kurzer eigener Abschnitt direkt vor "Installation" ("Installation", "Installation",
"Installation"):

| Sprache | Wortlaut |
|---|---|
| de | `## Umstieg von fulltextsearch` + Leerzeile + `Schritte zum Abschalten von fulltextsearch/Elasticsearch und was sich ändert: [docs/migrate-from-fulltextsearch.md](docs/migrate-from-fulltextsearch.md).` |
| en | `## Switching from fulltextsearch` + Leerzeile + `Steps to switch off fulltextsearch/Elasticsearch and what changes: [docs/migrate-from-fulltextsearch.en.md](docs/migrate-from-fulltextsearch.en.md).` |
| fr | `## Passer de fulltextsearch à Findling` + Leerzeile + `Étapes pour désactiver fulltextsearch/Elasticsearch et ce qui change : [docs/migrate-from-fulltextsearch.fr.md](docs/migrate-from-fulltextsearch.fr.md).` |

Variante 2 folgt dem Bestandsmuster "Grenzen und Details: [docs/formats.md](docs/formats.md)." (`README.md:46`).

## (D) Store-Zeile

### Längenmaßstab (App-Store-API `platform/34.0.3`, Feld `translations.en.description`, 19.10.2026)

| App | Länge der Beschreibung | Verweiszeilen |
|---|---|---|
| fulltextsearch | 62 Zeichen, eine Zeile | keine |
| files_fulltextsearch | 67 Zeichen, eine Zeile | keine |
| fulltextsearch_sql | 562 Zeichen, vier Zeilen | keine |
| context_chat | 610 Zeichen, fünf Zeilen | drei Verweiszeilen, je ein Satz mit Markdown-Link, z. B. "See [the Admin docs](https://docs.nextcloud.com/...) for installation steps and requirements." (sichtbarer Text 59 Zeichen) |
| findling (heute) | 1949 Zeichen, 26 Zeilen | eine Verweiszeile (MCP Connector) |

Folgerung: Ein Verweis ist in vergleichbaren Store-Texten ein Satz mit einem Markdown-Link. Die Zeile unten
hat sichtbar 71 (en), 71 (de) und 80 (fr) Zeichen (gezählt in Zeichen, nicht Bytes) und liegt damit nahe an
context_chat; die Findling-Beschreibung wächst um eine Zeile.

### Wortlaut für `# Entwurf v1.5.0 (Teil Phase 34)` in `docs/store-listing.md`

Eine Zeile je Beschreibung, gleich in `findling` und `findling_backend` (sechs Beschreibungen), absolute
Tag-URL je Sprache, keine Zahl. Vorschlag für den Platz: eigene Zeile hinter der Funktionsliste, vor dem
MCP-Connector-Absatz.

| Sprache | Wortlaut |
|---|---|
| en | `Switching from fulltextsearch/Elasticsearch: [steps in the documentation](https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/migrate-from-fulltextsearch.en.md)` |
| de | `Umstieg von fulltextsearch/Elasticsearch: [Schritte in der Dokumentation](https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/migrate-from-fulltextsearch.md)` |
| fr | `Passer de fulltextsearch/Elasticsearch à Findling : [étapes dans la documentation](https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/migrate-from-fulltextsearch.fr.md)` |

`php/appinfo/info.xml` und `backend/appinfo/info.xml` bleiben bis REL-05 (Phase 36) unverändert (PE-34-7);
der Abschnitt in `docs/store-listing.md` trägt den Kopfsatz "Owner-Abnahme offen, Teil von REL-05", sofern der
Owner die Store-Zeile nicht schon in diesem Checkpoint abnimmt.

## (E) Fragen an den Owner

O1 und O8 sind beantwortet durch D-34-01 (drei Dateien nach README-Muster) und D-34-02 (PHPUnit mit
`IAppManager`-Stub plus Banner-Sichtprobe, kein Elasticsearch-Container) und werden nicht erneut gefragt.

**O2: Pflichtformel en/fr**
- (a) en "OCR without changing files and without Elasticsearch", fr "OCR sans modifier les fichiers et sans Elasticsearch" (so im Entwurf A).
- (b) anderer Wortlaut.
- Empfehlung: (a), wörtliche Entsprechung der deutschen Formel, und das Gate kann je Sprache genau einen festen String prüfen.

**O3: Reichweite des Verbotsgates**
- Wörter: (a) nur die deutsche Form "einzige OCR" (Verbotsbeispiel); (b) zusätzlich "only OCR" und "seule OCR" / "seules OCR" (Verbotsbeispiele), alle mit Lookahead `(?![-\w])`.
- Dateien: `docs/**` ohne `docs/measurements/**`, `README*.md`, `CHANGELOG.md`, beide `info.xml`, `php/templates/**`, `php/l10n/**`, `store/**` nur Textdateien (`.md`, `.txt`, `.xml`, `.json`, `.html`; Bilder wie PNG ausgenommen); nicht `.planning/` und nicht `backend/tests/`.
- Bindestrich-Ausnahme: `docs/performance.md:1025` ("keine einzige OCR-Seite") wird per Lookahead nicht getroffen und dient im Selbsttest als Positivkontrolle.
- Empfehlung: (b) mit der genannten Dateireichweite und der Ausnahme per Lookahead; die Seite ist dreisprachig, ein Verbot nur auf Deutsch ließe die en/fr-Texte ungeschützt.

**O4: Vergleichsform**
- (a) zwei Faktenlisten "Was Findling mitbringt" und "Was sich beim Umstieg ändert", Deck-Verlust und externe Speicher in der zweiten (so im Entwurf A).
- (b) Gegenüberstellung als Tabelle.
- Empfehlung: (a), eine Tabelle zwingt zu "besser/schlechter"-Zeilen über eine fremde, gepflegte App.

**O5: Drittanbieter-Plattformen**
- (a) fulltextsearch_sql und fulltextsearch_postgresql im Pflegestand einmal neutral nennen, mit Version und Datum, ohne Bewertung (Zeilen `[O5]` im Entwurf A).
- (b) nur "die verwendete Plattform-App" sagen, keine Namen.
- Empfehlung: (a), weil Schritt 6 für deren Nutzer entfällt und die Seite sonst den Eindruck erweckt, fulltextsearch gehe nur mit Elasticsearch.

**O6: Linkform des Admin-Hinweises und `info.xml`**
- Link: (a) sprachabhängig auf die drei Tag-URLs (PE-34-3, Abschnitt B); (b) fest auf die englische Seite.
- `<documentation><admin>` in `info.xml`: (c) in Phase 36 ergänzen (eine URL, nicht sprachfähig, dann die englische Seite); (d) weglassen.
- Empfehlung: (a) und (c); der Hinweis spricht die Sprache des Admins, und das Element ist im Store der übliche Ort für Admin-Doku, aber erst mit REL-05.

**O7: Hinweissatz**
- (a) wie Abschnitt B ("Mindestens eine App ... können doppelt erscheinen ... deaktivieren, sobald der erste Indexlauf abgeschlossen ist").
- (b) Research-Vorschlag "Full text search (fulltextsearch) is switched on next to Findling. Both search the same files, so results can appear twice in the search bar. Switch off the old apps once Findling has finished its first index run."
- Empfehlung: (a), weil (b) falsch ist, wenn nur files_fulltextsearch aktiv ist, und "enabled/aktiviert" das Wort der Apps-Seite ist.

**O9: Platz des README-Verweises**
- (a) Variante 1, Zeile in der Funktionsliste.
- (b) Variante 2, eigener kurzer Abschnitt vor "Installation".
- Empfehlung: (b), die Funktionsliste beschreibt, was Findling kann, ein Umstiegsweg ist keine Funktion; Variante 2 folgt dem Muster der Verweiszeile unter den Dateitypen.

**O10: UI-SPEC**
- (a) entbehrlich wie D-33-02 (ein Banner im vorhandenen Bannerblock, kein neues Bedienelement).
- (b) UI-SPEC für den Banner schreiben.
- Empfehlung: (a).

Verbotsliste der Seite (Leitplanke, auch en/fr-Entsprechungen): "verwaist", "tot", "nicht gepflegt",
"orphaned", "abandoned", "unmaintained"; dazu die Einzigartigkeitsbehauptung aus O3.

### Vorab-Prüfung des Entwurfs (19.10.2026)

Die Entwurfstexte aus A bis D (ohne Abschnitt E) lagen als Scratch-Datei vor und wurden geprüft:

- gesperrter Wortstamm aus `test_public_artifacts.py` (`BLOCKED_TERM`, deutsche Form ohne folgendes "e") und
  `test_store_metadata.py`: kein Fund;
- Geheimnis-Familien von `test_public_artifacts.py` (Schlüsselwort mit Wert, base64-Block ab 40 Zeichen und die
  übrigen Muster des Moduls, per Import der Ausdrücke aus dem Testmodul): kein Fund; die Rohtreffer von
  `BASE64_BLOCK` sind URL-Pfade, die `run_is_a_path()` ausnimmt (jedes Stück zwischen Schrägstrichen unter 40);
- Verbot `einzig[a-zäöü]*[[:space:]]+OCR([^-[:alnum:]]|$)|only[[:space:]]+OCR|seules?[[:space:]]+OCR`: kein Fund
  in A bis D, in dieser Datei nur in Abschnitt E als Verbotsbeispiel;
- Ehrlichkeitswörter der Verbotsliste oben: kein Fund in A bis D, in dieser Datei nur in Abschnitt E;
- Halbgeviert- und Geviertstriche (U+2013, U+2014): kein Fund in der ganzen Datei.

## Owner-Abnahme

Offen (34-01 Task 2).
