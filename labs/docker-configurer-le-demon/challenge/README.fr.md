# Des journaux sans limite, sur toute la machine

## La situation

Sur `docker.lab`, un conteneur créé sans option garde un journal bien trop gros.
Régler chaque conteneur à la main ne tient pas : il suffit d'en oublier un. La
limite doit venir du démon.

## Mission

Configurez le démon pour que tout **nouveau** conteneur, créé sans aucune option
de journal, obtienne :

- le pilote `json-file` ;
- des fichiers de `1m` au plus ;
- `2` fichiers conservés.

Ne perdez aucun autre réglage du démon. L'énoncé est aussi déposé dans
`/opt/dsoxlab-docker-configurer-le-demon/MISSION.md`.

## Ce qui est noté

Les contrôles créent leurs propres conteneurs, sans option de journal :

1. le pilote, la taille et le nombre de fichiers sont ceux demandés ;
2. la limite agit vraiment : sur un journal qui la dépasse, les premières lignes
   ont été jetées et le volume gardé tient dans le budget.

Le fichier de configuration n'est pas lu : seul compte ce qu'un nouveau conteneur
reçoit. Les conteneurs d'essai sont retirés, et le nettoyage du lab remet la
configuration de départ.
