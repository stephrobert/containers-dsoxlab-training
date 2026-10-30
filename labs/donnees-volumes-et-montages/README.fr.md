# donnees-volumes-et-montages : où les données survivent

## Ce que ce lab éprouve

Qu'il y a trois façons de donner un espace de fichiers à un conteneur, qu'elles
ne servent pas au même usage, et qu'**aucune des trois n'est la couche du
conteneur**, où tout finit par défaut.

| Montage | Ce qu'il donne | Pour quoi |
| --- | --- | --- |
| volume nommé | un espace géré par le moteur, qui survit au conteneur | les données |
| bind mount | un répertoire de l'hôte, tel quel | une configuration fournie |
| tmpfs | de la mémoire, qui ne persiste rien | un espace de travail |

## Une mesure a changé l'écriture des tests

Un **tmpfs n'apparaît pas** dans `.Mounts`. Il vit dans `.HostConfig.Tmpfs`.
Relevé sur `docker.lab` le 2026-10-30.

Un test qui l'aurait cherché dans `.Mounts` aurait échoué quoi que fasse
l'apprenant, et aurait accusé un apprenant irréprochable. C'est le genre de
détail qu'on ne devine pas et qu'il faut mesurer avant d'écrire.

## Le contrôle qui porte la leçon, et la faute qu'il a d'abord commise

Le quatrième. `historique.log` a été écrit par le setup dans la **couche** du
conteneur, avec un contenu tiré au hasard : il n'existe nulle part ailleurs. Le
faire passer dans le volume suppose de l'avoir sorti **avant** de détruire le
conteneur, et c'est exactement le geste qui sauve ou perd des données en
production.

**Une première version de ce test passait avant tout travail.** Il lisait
`/var/lib/donnees/historique.log` dans `archive`, où la couche porte déjà le
fichier à ce chemin : il mesurait la présence du fichier, pas sa migration.
`valider-labs.py` l'a attrapé en rendant 1/4 sur l'état de départ, ce qui est
précisément à quoi sert la règle du score nul.

Le test monte désormais le volume dans un **conteneur jetable** : il mesure le
volume, et non ce que `archive` donne à voir.

## Pourquoi une empreinte, et pas le contenu

Le test compare le SHA256 du fichier arrivé dans le volume à celui que le setup
a relevé.

Garder le contenu sur l'hôte donnerait la réponse ; garder l'empreinte permet de
vérifier sans rien révéler, et **l'apprenant peut s'en servir pour se contrôler
lui-même**. Un contrôle qu'on peut vérifier soi-même enseigne ; un contrôle
opaque fait deviner.

Elle écarte aussi la fausse réussite la plus tentante : un fichier recréé à la
main a le bon nom et pas le bon contenu, ce qui est exactement la façon dont on
se raconte qu'une migration a réussi.

## Chaque montage est mesuré deux fois

Ce que l'inspection **déclare**, et ce que le conteneur **peut faire**.

Le cas le plus net est le bind en lecture seule : la déclaration peut dire une
chose et la machine en faire une autre. Un lab qui ne lirait que la déclaration
validerait une lecture seule qui n'en est pas une, ce qui est pire que de ne
rien vérifier.

## Un avertissement plutôt qu'un piège

L'énoncé dit franchement que le fichier est irremplaçable et qu'il n'y a pas de
rattrapage. Ce n'est pas de la bienveillance mal placée : la leçon est dans
l'**ordre des gestes**, pas dans la surprise.

Un apprenant averti qui détruit quand même le conteneur a appris quelque chose
sur lui-même. Un apprenant non averti aurait seulement appris que le lab est
injuste.

## L'état de départ est cassé, et c'est la règle du dépôt

| Posé par le setup | État de départ | Geste attendu |
| --- | --- | --- |
| `archive` | **aucun** montage | le recréer avec les trois |
| `historique.log` | dans la couche | le faire passer dans le volume |
| `coffre-donnees` | existe, porte `marque.txt` | le monter au bon endroit |
| `reference/` | sur l'hôte | l'exposer en lecture seule |

Une tâche du setup **vérifie** cet état avant de rendre la main : le conteneur
n'a aucun montage, son historique est bien dans sa couche, et le volume ne le
porte pas encore.

## Ce que le cleanup doit impérativement retirer

Le **volume**. Un volume survit à son conteneur, c'est tout son intérêt et c'est
aussi ce qui le rend dangereux ici : s'il restait avec `historique.log` dedans,
le quatrième contrôle serait vrai au passage suivant avant tout travail, et le
lab se noterait sur le travail de la veille.

`docker volume rm` refuse un volume encore utilisé par un conteneur, même
arrêté : le conteneur part donc d'abord.

## Ce que le lab n'exige pas

Un chemin. Le fichier peut sortir par `docker cp` comme par une redirection de
`docker exec`, et entrer dans le volume par un conteneur jetable comme par une
écriture directe sur son répertoire de l'hôte. Seul l'état compte.
