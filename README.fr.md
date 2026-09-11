[Deutsch](README.md) | [English](README.en.md) | Français

# Findling

Recherche plein texte, reconnaissance optique et recherche sémantique pour
Nextcloud, sans configuration. Les résultats apparaissent dans la barre de
recherche normale.

**Findling + Nextcloud MCP Connector = la couche de récupération de votre propre RAG.**
Le [MCP Connector](https://apps.nextcloud.com/apps/mcp_connector) transmet les résultats de Findling à tout client MCP, avec
exactement les droits de l'utilisateur qui demande ; mesuré par le
[test de fidélité](https://github.com/street1983nk/nextcloud-mcp-connector/blob/main/tests/integration/test_content_hit_fidelity.py).
Le modèle, c'est vous qui l'apportez, et aucun contenu ne quitte votre serveur.

## Ce que Findling sait faire

- Recherche plein texte avec traitement des mots allemands : mots composés,
  flexion, trémas, phrases, exclusions, filtre par type de fichier
- Reconnaissance optique pour les PDF numérisés et les images : allemand,
  anglais, français
- Recherche sémantique : trouve les documents par des périphrases
- Chaque résultat est vérifié par Nextcloud selon vos droits
- Aucune configuration : la première indexation démarre d'elle-même

## Types de fichiers pris en charge

PDF (numérisés aussi), DOCX, PPTX, XLSX, ODT, ODS, ODP, HTML, RTF, TXT,
Markdown, CSV, ainsi que les images (JPEG, PNG, TIFF, WebP) par
reconnaissance optique.

## Prérequis

- Nextcloud 33 à 35 avec l'application AppAPI (HaRP comme cible de
  déploiement)
- RAM : 4 Go suffisent. Sur une machine ARM64 de 4 Go avec 52 111 documents
  indexés et la recherche sémantique active, le conteneur a atteint un pic de
  1 764 Mo de mémoire anonyme résidente, sous une limite stricte de 2 Go imposée
  par le noyau.
- La charge de base au repos est passée de 691,8 Mo en v1.0 à 103,2 Mo en v1.1,
  moins 85,1 pour cent (mesuré le 10.09.2026, méthode et données brutes dans
  [docs/performance.md](docs/performance.md)).
- CPU : 2 cœurs suffisent, amd64 et arm64, pas de GPU

## Installation

Installer les deux entrées du store, toujours dans la même version :
[Findling](https://apps.nextcloud.com/apps/findling) (Apps) et
[Findling Backend](https://apps.nextcloud.com/apps/findling_backend)
(External Apps). La première indexation démarre ensuite d'elle-même ;
`occ findling:index --status` montre la progression.

## Confidentialité

Tout fonctionne localement dans le conteneur, aucune télémétrie, les fichiers
ne sont jamais modifiés. Ce qui est conservé, c'est le texte extrait, dans la
zone de données propre à l'application backend : une sauvegarde de cette zone
le contient, et l'index n'est pas chiffré au repos.

## Mesures

Chaque chiffre (mémoire, durées, charge de recherche, tests de panne, qualité
du modèle) est documenté avec sa méthode et ses données brutes dans
[docs/performance.md](docs/performance.md) et
[docs/embeddings.md](docs/embeddings.md).

## Licence

AGPL-3.0-or-later. Voir [LICENSE](LICENSE).
