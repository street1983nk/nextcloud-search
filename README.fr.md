[Deutsch](README.md) | [English](README.en.md) | Français

# Findling

Recherche plein texte et sémantique sans configuration pour Nextcloud.

Findling fait en sorte que la recherche Nextcloud trouve ce qui se trouve dans
vos documents, y compris les PDF scannés, sans cluster Elasticsearch et sans
aucun réglage obligatoire. Les résultats apparaissent dans la barre de
recherche unifiée habituelle, à côté des fichiers, contacts et événements de
calendrier.

## Ce qu'elle trouve

- **Les mots qui figurent dans le document**, avec le traitement que
  l'allemand exige d'une recherche : les mots composés via l'un de leurs
  éléments, la flexion, la variante avec umlaut écrite en toutes lettres, les
  phrases, les exclusions et un filtre de type de fichier.
- **Le texte des pages scannées**, via l'OCR, en allemand, en anglais, en
  français et dans les graphies DACH. Les trois langues sont actives d'origine,
  aucun réglage n'est nécessaire. La recherche elle-même reste accordée sur
  l'allemand et l'anglais : une page française est lue et retrouvée, mais sans
  racinisation française.
- **Les documents que vous décrivez au lieu de les citer.** Une requête dont
  les mots ne figurent pas dans le document peut quand même le faire
  remonter, parce qu'un modèle d'embedding local classe par sens, à côté de
  l'index de mots.

La phrase honnête sur ce troisième point, et c'est la même dans les deux
descriptions de la boutique : **la recherche sémantique couvre le début de
chaque document, la recherche plein texte continue de tout couvrir.** Ce que
représente "le début" dépend du document, et sur le corpus mesuré, cela
représente 12,5 % d'un document moyen. Le modèle tourne dans le conteneur,
sur le CPU, et aucun texte ne quitte la machine pour cela. Les détails, la
qualité mesurée dans trois langues et les deux preuves que le conteneur n'a
besoin d'aucun réseau pour cela se trouvent dans
[docs/embeddings.md](docs/embeddings.md).

Toutes les requêtes n'obtiennent pas cette seconde liste, et les deux
exceptions sont voulues. Une requête avec des guillemets, un signe moins, un
préfixe de champ, un type de fichier ou l'un des mots grammaticaux AND, OR et
NOT reçoit une réponse du seul index de mots : qui cherche ainsi a demandé de
l'exactitude, et une liste classée par sens ne le sait pas. Une requête d'un
seul mot reçoit la même réponse, parce qu'un seul mot n'est mesurablement pas
plus proche du document qu'il désigne qu'un mot sans rapport, et le
séparateur de mots composés, le stemmer et la variante avec umlaut couvrent
déjà ce cas. Une requête de deux mots ou plus sans un tel opérateur reçoit une
réponse combinant les deux moitiés.

**État : durcissement avant la première publication sur la boutique, pas
encore soumis.** L'indexation, l'OCR et la recherche fonctionnent et sont
mesurées sur du matériel loué, voir plus bas. Les fichiers de publication des
deux applications sont en préparation ; tant qu'ils ne sont pas dans la
boutique, ne pas installer ceci sur un serveur de production.

## Le modèle à deux applications

Findling est distribué sous forme de deux entrées de boutique qui vont
ensemble :

| Partie | Identifiant | Section de la boutique | Ce qu'elle fait |
|------|--------|---------------|--------------|
| Compagnon PHP | `findling` | Apps | Enregistre le fournisseur de recherche et relaie les requêtes vers le backend |
| ExApp Python | `findling_backend` | External Apps | Exécute l'extraction, l'OCR et l'index de recherche dans un conteneur |

Les deux entrées doivent être installées, et portent toujours la même version
majeure et mineure. Le compagnon est volontairement minuscule : il gère le
côté Nextcloud, y compris le contrôle des droits, parce que Nextcloud ne peut
pas enregistrer de fournisseur de recherche depuis une application externe.
Le conteneur assume le gros du travail.

## Prérequis

- Nextcloud 33 à 35 (`min-version` 33, `max-version` 35). Nextcloud 32 est
  sorti de la fenêtre prise en charge avec la décision du 2026-09-06 : son
  support prend fin en septembre 2026, cette application est soumise en
  décembre, et une application qui revendique un serveur que plus personne ne
  supporte promet quelque chose qu'elle ne peut pas tenir.
- L'application AppAPI, avec HaRP comme cible de déploiement
- Matériel visé : 4 à 8 GB de RAM, ARM64 et AMD64, CPU uniquement, aucun GPU
  requis

Le projet est construit pour les hébergeurs autonomes et les petites
organisations sur du matériel ordinaire, pas pour un cluster de recherche.

## Ce que cela coûte en mémoire, mesuré

**Sur une machine ARM64 à 4 GB, avec 51 961 documents indexés et la recherche
sémantique active, le conteneur a atteint un pic de 1 813 MB de mémoire anonyme
résidente, sous une limite stricte de 2 GB imposée par le noyau. Les trois
compteurs du noyau pour les dommages mémoire (`oom`, `oom_kill`,
`oom_group_kill`) sont à zéro, et le quatrième compteur `max`, qui compte combien
de fois le noyau a dû repousser le conteneur contre sa limite, est également à
zéro.** Mesuré le 07.09.2026
([docs/measurements/2026-09-nachmessung-m7g](docs/measurements/2026-09-nachmessung-m7g/)).

`max` est indiqué ici et non passé sous silence, parce qu'il n'était pas à zéro
dans la mesure précédente : le cache de fichiers de l'index avait alors buté
2 796 fois contre la limite de 2 GB. Aucun processus n'a été tué, mais le noyau a
dû travailler. Cette fois, il n'a pas eu à le faire, pas une seule fois.

**Le chiffre précédent, à titre de comparaison :** 1 838 MB, mesuré le 05.09.2026
lors de l'exécution sémantique complète
([docs/measurements/2026-09-05-semantiklauf-m7g](docs/measurements/2026-09-05-semantiklauf-m7g/)),
avec `max 2 796`. L'écart n'est pas du bruit de mesure : le côté recherche
chargeait alors une deuxième copie du modèle en plus de celle que l'indexeur
détenait. Cette copie a disparu, et la phase de recherche est ainsi passée de
1 838 MB à 1 125 MB. Que le pic global n'ait baissé que de 25 MB a sa propre
raison : il apparaît désormais dans la phase d'OCR et non plus dans la recherche,
et l'OCR travaille avec trois langues au lieu de deux depuis le 06.09.2026. Les
deux chiffres portent leur date et leur justification dans le rapport de mesure.

**Recherches simultanées :** jusqu'à **huit** respectent le budget de temps de
2,5 secondes sur cette machine (95e centile 1,9 s sur 410 requêtes). À douze, il
est dépassé. C'est un chiffre valable pour cette machine et cette instance : la
recherche de Nextcloud interroge tous les fournisseurs en même temps, donc le
pool de processus PHP de l'instance impose une limite tout autant, et ce pool
n'a pas la même taille partout.

**L'exécution complète dont provient le fonds :** 50 000 fichiers et 20 GB,
18 h 56 min jusqu'au dernier vecteur, un index de mots de 785 MB et un stockage
vectoriel de 69 MB, et chaque fichier avec un verdict : 51 961 indexés et
vectorisés, 37 ignorés pour une raison nommée, **aucun échec**. Une recherche
utilisateur pendant l'exécution répondait en 1,1 seconde au 95e centile, après
l'exécution en 0,5 seconde.

Ce sont des mesures, pas des estimations. Elles ont été prises sur arm64 avec
2 cœurs et 4 GB, le matériel pour lequel cette application est construite. Ces
durées proviennent du matériel cible le plus modeste pris en charge et
constituent délibérément une borne basse : sur du matériel moderne et puissant,
l'indexation tourne nettement plus vite, mais aucune mesure dédiée n'existe pour
cela. Une phrase honnête doit encore l'accompagner : l'essentiel de cette mémoire
vient de la recherche sémantique, pas de l'indexation. La même exécution complète
sans embeddings a atteint un pic de 422 MB et a pris 12 h 49 min sur la même
machine.

La méthode, les deux courbes complètes, le corpus, la preuve OOM en quatre
parties, quatre essais de défaillance sur la même machine (`docker kill`
pendant l'OCR, un redémarrage de la machine entière, backend disparu, disque
presque plein), la répartition de ce que coûte la recherche sémantique au
repos et une mesure annexe avec un second worker d'indexation se trouvent
dans [docs/performance.md](docs/performance.md), y compris ce que chacune de
ces preuves ne démontre pas.

## Confidentialité

- Aucun contenu de fichier ne quitte le serveur. L'extraction, l'OCR,
  l'indexation et la recherche tournent toutes dans le conteneur, sur votre
  propre machine.
- Ce qui est stocké, c'est le texte extrait. Le texte de chaque document
  indexé est conservé dans l'espace de stockage propre de l'application
  backend, parce que les extraits affichés sous un résultat de recherche en
  sont découpés à la demande. Une sauvegarde de cet espace de stockage
  contient donc le texte de vos documents indexés, et l'index n'est pas
  chiffré au repos, ce qui relève de l'hébergeur sur lequel il tourne. Le
  même paragraphe figure dans les deux descriptions de la boutique, dans les
  trois langues.
- Aucune télémétrie. L'application ne communique jamais vers l'extérieur, pas
  même pour vérifier les versions.
- Les fichiers des utilisateurs ne sont jamais modifiés. Chaque accès à un
  fichier passe par une passerelle de contenu en lecture seule, et une porte
  de contrôle par somme de contrôle dans la CI prouve cet invariant sur un
  corpus de référence.
- Les droits sont appliqués par Nextcloud lui-même. Le filtre final des
  résultats tourne en PHP contre le dossier de l'utilisateur, pour que
  l'index ne devienne jamais un second modèle de droits.

## Organisation du dépôt

```
php/               Application compagnon PHP, mappée sur apps/findling en CI
backend/           ExApp Python, paquet sous backend/src/findling/
testdata/corpus/   Corpus de référence pour la porte de contrôle en lecture seule
docs/              Documentation de processus et d'exploitation
.github/workflows/ CI : python, php, integration, docker
```

## Licence

AGPL-3.0-or-later. Voir [LICENSE](LICENSE).
