[Deutsch](backup.md) | [English](backup.en.md) | Français

# Sauvegarder Findling

Deux façons de sauvegarder le volume d'index de manière cohérente (ticket #37).

## Où se trouve quoi

- Les réglages (exclusions, taille maximale, Team Folders, stockages externes, souhait de pause)
  sont dans l'`appconfig` de la base de données Nextcloud. La sauvegarde habituelle de la base
  Nextcloud les couvre.
- Le volume `nc_app_findling_backend_data` contient `state.db`, `vectors.db` et l'index de recherche.
- Le volume peut être entièrement reconstruit à partir de vos fichiers. Une sauvegarde ne fait
  gagner que le temps de l'OCR et des embeddings.
- L'index contient le texte extrait de vos documents, non chiffré. Protégez la sauvegarde comme
  celle de vos fichiers (chiffrée, accès restreint).

## Voie A : arrêter le conteneur

1. `docker stop nc_app_findling_backend`
2. Copier le volume `nc_app_findling_backend_data` (tar ou votre outil de sauvegarde)
3. `docker start nc_app_findling_backend`

- Le conteneur ferme proprement l'index et les bases de données à l'arrêt.
- La recherche est indisponible pendant ce temps.

## Voie B : pause, la recherche continue

1. `occ findling:pause --wait` ne rend la main que lorsque le statut indique en pause. Ou activer
   le bouton « Mettre l'indexation en pause » sur la page d'administration et attendre qu'elle
   indique en pause ([admin-page.md](admin-page.md)).
2. Copier le volume `nc_app_findling_backend_data`.
3. `occ findling:resume` ou le bouton de reprise.

- En pause, l'indexation s'arrête et tout est écrit sur le disque ; la recherche continue.
- Ne lancer la sauvegarde qu'en pause, pas pendant la mise en pause.
- La mise en pause dure jusqu'à la fin du lot en cours, avec l'OCR jusqu'à environ 30 minutes.
- La pause survit aux redémarrages du conteneur et de Nextcloud. Si le souhait n'est pas encore
  lisible après un redémarrage, l'indexation reste également arrêtée.
- Les tâches d'exploration de l'application compagnon continuent. Elles n'écrivent que dans la base
  Nextcloud, pas dans le volume ; la file d'attente est traitée après la reprise.
- Une reconstruction de l'index en cours s'arrête entre deux tranches et reprend ensuite. Une
  sauvegarde faite pendant ce temps contient deux répertoires d'index ([uninstall.md](uninstall.md)).

## Restaurer

1. `docker stop nc_app_findling_backend`
2. Restaurer le volume `nc_app_findling_backend_data`
3. `docker start nc_app_findling_backend`

- Le souhait de pause n'est pas dans le volume mais dans la base Nextcloud. Un volume restauré suit
  l'état actuel du bouton ; après la voie B, ne pas oublier `occ findling:resume`.
