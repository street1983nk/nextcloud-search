# Changelog

Toutes les modifications notables de Findling (l'app compagnon `findling` et
l'External App `findling_backend`) sont consignées ici. Les deux apps portent
la même version. Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).
Version française à partir de 1.6.3 ; les entrées plus anciennes se trouvent
dans [CHANGELOG.md](CHANGELOG.md).

## [Unreleased]

## [1.6.4] - 2026-11-12

### Corrigé

- La mise à jour depuis l'App Store n'échoue plus avec « Undefined constant »
  dans la migration vers 1.6.3 (#51). Si la mise à jour vers 1.6.3 a échoué :
  `occ upgrade` la termine.

## [1.6.3] - 2026-11-12

### Ajouté

- Une note à côté du chiffre de couverture pendant sept jours après le premier
  comptage de 1.6.3, une phrase pendant que le comptage est en cours, et le
  nombre de fichiers qui sont listés mais n'ont pas pu être lus ou sont restés
  bloqués ; ils comptent désormais comme non consultables (#25).

### Corrigé

- Le balayage des stockages s'exécute une fois par cadence de rapprochement,
  même pendant que l'exploration ou une longue file d'attente retient la
  comparaison complète, si bien que les documents des stockages supprimés ou
  démontés quittent l'index (#25).
- Le chiffre de couverture compte chaque document une fois, même lorsqu'un
  partage est monté séparément pour chaque utilisateur, et les documents qui
  ne se trouvent que sur des stockages qui ne sont plus montés ne comptent
  plus (#25).
- Le chiffre de couverture compte un document une seule fois aussi lorsqu'un
  partage est configuré avec des racines différentes, ou lorsque le nom du
  serveur ou du partage est écrit avec une casse différente (#25). Un partage
  Samba [homes] n'est jamais regroupé entre utilisateurs, et les stockages
  SFTP ne sont regroupés que par identifiant de connexion.
- Le dénominateur est calculé par groupe de partages et ne descend jamais
  sous les documents évalués dans ce groupe plus les fichiers que Nextcloud
  n'a pas pu lire, si bien que la part ne dépasse jamais 100 pour cent et
  montre la couverture réelle une fois la file vide (#25). Les types de
  fichiers refusés sur des stockages qui ne sont plus montés ne le réduisent
  plus.
- Les fichiers supprimés ne comptent plus comme indexés dans les chiffres
  d'état.
- Sur un stockage SMB sans l'extension php-smbclient, un fichier qui ne peut
  pas être ouvert (accès refusé, violation de partage, hors ligne) ne bloque
  plus un worker PHP, et ces fichiers comptent comme non lisibles. Un fichier
  vide lisible reçoit la réponse 200, pas 400.
- Les fichiers que 1.6.2 avait enregistrés comme erreur de passerelle sont
  vérifiés une nouvelle fois après la mise à jour, même si leurs tentatives
  étaient épuisées, si bien qu'un fichier verrouillé ou refusé apparaît comme
  non lisible avec son remède.
- Le comptage synchrone de la couverture est plafonné à 25 000 lignes, pour
  que la réponse reste dans le délai d'administration de l'app compagnon sur
  du matériel lent ; les instances plus grandes voient le chiffre compté en
  arrière-plan une fois après la mise à jour.
- Le cycle de rattrapage unique après une mise à jour ne lance plus de tour
  lorsque le rapprochement est désactivé à cet instant précis.
- Un verrou passager de la base de données pendant le premier index ne met
  plus fin au parcours d'un stockage ; la tranche est retentée quelques
  secondes plus tard, jusqu'à cinq fois de suite.

### Limites connues

- Un stockage SMB sous chiffrement côté serveur est lu comme avant, sans le
  délai.
- Une erreur réseau entre la vérification et l'ouverture d'un fichier compte
  comme non lisible ; quelques nouvelles tentatives suivent.
- Une réponse courte pour un fichier dont Nextcloud ne connaît pas la taille
  est considérée comme complète.
- Sur SMB sans l'extension php-smbclient, un fichier au-dessus d'environ
  469 Mio s'arrête court et est abandonné comme bloqué (seulement avec
  FINDLING_MAX_FILE_BYTES relevé au-dessus des 50 Mo par défaut).
- Sur SMB sans l'extension php-smbclient, une liaison en dessous d'environ
  420 Ko/s ne peut pas livrer un bloc de lecture de 8 Mio dans le délai de
  20 s de smbclient, si bien que les fichiers plus grands qu'un bloc comptent
  comme non lisibles ; installez l'extension ou relevez l'option de délai du
  stockage (occ files_external:config).
- Un partage Samba dont le dossier dépend de l'utilisateur côté serveur (un
  chemin avec %U ou %S) compte toujours comme un seul arbre pour tous les
  utilisateurs.
- Les stockages dont l'identifiant dépasse 64 caractères et qui ne peuvent
  pas être reconstruits à partir de leur configuration (identifiants globaux
  ou fournis par l'utilisateur, un nom de connexion différent de l'identifiant
  utilisateur) sont comptés par stockage.
