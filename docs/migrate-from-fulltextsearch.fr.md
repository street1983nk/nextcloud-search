[Deutsch](migrate-from-fulltextsearch.md) | [English](migrate-from-fulltextsearch.en.md) | Français

# Passer de fulltextsearch/Elasticsearch à Findling

Cette page s'adresse aux administrateurs qui utilisent la recherche plein texte de Nextcloud
(fulltextsearch) avec Elasticsearch ou une autre application de plateforme et veulent passer à
Findling. Findling apporte la recherche plein texte, la recherche sémantique et
l'OCR sans modifier les fichiers et sans Elasticsearch dans un seul conteneur, et ses résultats
apparaissent dans la barre de recherche normale.

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
- Applications de plateforme tierces sans service de recherche :
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
   Avec `--no-interaction`, la commande s'arrête sans rien demander et ne supprime rien. Sans
   plateforme configurée, elle se termine après la confirmation par l'erreur
   `Admin have not selected any IFullTextSearchPlatform` et ne supprime rien non plus (vérifié avec
   Nextcloud 34.0.3 et fulltextsearch 34.0.2).
4. Désactiver les applications, plusieurs en un seul appel :
   `occ app:disable files_fulltextsearch fulltextsearch_elasticsearch fulltextsearch`. À la place
   de `fulltextsearch_elasticsearch`, indiquer l'application de plateforme utilisée, et
   `files_fulltextsearch_tesseract` si elle est présente. Au prochain chargement de la page
   d'administration, l'avertissement de Findling a disparu.
5. Facultatif : supprimer les applications avec `occ app:remove <app-id>`. Les tables
   `oc_fulltextsearch_index` et `oc_fulltextsearch_ticks` et leurs entrées dans `oc_migrations`
   restent (vérifié avec Nextcloud 34.0.3). Pour les supprimer, faire d'abord une sauvegarde de la
   base de données, puis exécuter ces instructions ; `oc_` est le préfixe par défaut, une instance
   avec un autre préfixe utilise le sien :

   ```sql
   DROP TABLE oc_fulltextsearch_index;
   DROP TABLE oc_fulltextsearch_ticks;
   DELETE FROM oc_migrations WHERE app = 'fulltextsearch';
   ```

   Une réinstallation ultérieure de fulltextsearch recrée les tables.
6. Arrêter le service Elasticsearch hors de Nextcloud et supprimer ses données, s'il ne sert à rien
   d'autre. Avec une application de plateforme sans service de recherche, cette étape ne
   s'applique pas.
7. Nextcloud AIO : décocher l'option "Fulltextsearch" dans l'interface AIO. AIO annule un simple
   `occ app:disable` au prochain démarrage du conteneur tant que l'option est cochée
   ([entrypoint.sh](https://github.com/nextcloud/all-in-one/blob/main/Containers/nextcloud/entrypoint.sh)).
