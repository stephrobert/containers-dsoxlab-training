# Le Dockerfile dit une chose, l'image en dit une autre

## La situation

Votre équipe héberge une trentaine d'images construites sur le même socle
Debian. Le disque du serveur de build arrive à saturation, et la direction
demande un chiffrage : « combien pèsent vraiment ces images ? »

Vous additionnez ce que `docker images` affiche dans la colonne SIZE, et vous
obtenez un total qui dépasse de loin la place réellement occupée. Quelqu'un
vous répond que « les couches sont partagées », ce qui est vrai et ne vous
avance à rien tant que vous ne savez pas **lesquelles** ni **combien**.

Vous ouvrez alors un Dockerfile pour compter ses couches, et là une seconde
surprise vous attend : le compte ne tombe pas juste. Toutes les instructions
ne créent pas une couche, et l'une d'entre elles en crée une sans en avoir
l'air.

## L'objectif

Disséquer une image au lieu de lire son Dockerfile. Deux images sont déjà
construites sur la machine, depuis la **même** base et avec les **mêmes**
premières instructions :

```text
greffe:1.0    celle qu'on dissèque
greffe:2.0    celle qui part du même socle
```

Leurs Dockerfile sont lisibles dans `/opt/lab-anatomie`. **Ne vous y fiez
pas** : le moteur est la seule source.

Renseignez les quatre lignes de `/opt/lab-anatomie/reponses.txt` :

```text
couches=<le nombre de couches de greffe:1.0>
partagees=<le nombre de couches communes aux DEUX images>
propres=<le nombre de couches de greffe:2.0 absentes de greffe:1.0>
revision=<la révision que greffe:1.0 porte dans sa configuration>
```

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Ce qui est noté

L'**état du moteur**, jamais les commandes tapées. Les quatre valeurs sont
recalculées au moment de la notation, en interrogeant les images, puis
confrontées à ce que vous avez écrit.

La révision est le cas le plus net : elle n'est écrite dans **aucun fichier**
de cette machine, elle n'est pas non plus dans l'historique de l'image, et elle
est tirée au hasard à chaque passage. Elle vit dans la **configuration** de
l'image, à côté de son environnement et de sa commande par défaut, et c'est
tout l'intérêt de la question : une image, ce n'est pas seulement un contenu.
