# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Deux images sont
**déjà construites** : rien à tirer, rien à construire.

```text
greffe:1.0    celle qu'on dissèque
greffe:2.0    celle qui part du même socle
```

Leurs Dockerfile sont lisibles dans `/opt/lab-anatomie`. Vous pouvez et devez
les lire, mais **ils ne donnent pas les réponses** : toutes les instructions ne
créent pas une couche, et l'une d'entre elles en crée une sans en avoir l'air.
Le moteur est la seule source.

Les quatre réponses vont dans `/opt/lab-anatomie/reponses.txt`, une ligne par
entrée, sans espace autour du signe égal.

## 1. Le nombre de couches de `greffe:1.0`

À la ligne `couches=`. Un entier simple.

Comptez les couches **de l'image**, celles que le moteur empile, pas les lignes
du Dockerfile. Si votre compte tombe sur le nombre d'instructions qui semblent
en créer une, c'est le signe qu'il manque quelque chose.

## 2. Le nombre de couches communes aux deux images

À la ligne `partagees=`. Un entier simple.

Les deux images partent de la même base et leurs premières instructions sont
identiques : ces couches-là sont **le même objet**, stocké une seule fois sur
le disque. C'est la réponse à « pourquoi dix images d'un même socle ne pèsent
pas dix fois le socle ».

Comparez les deux **listes de couches**, pas les deux Dockerfile.

## 3. Le nombre de couches propres à `greffe:2.0`

À la ligne `propres=`. Un entier simple.

Celles que `greffe:2.0` porte et que `greffe:1.0` n'a pas. C'est le compte dans
l'autre sens, et ce n'est pas la même question : c'est ce que coûte réellement
une variante quand le socle est déjà là.

## 4. La révision portée par `greffe:1.0`

À la ligne `revision=`.

Elle n'est écrite dans **aucun fichier** de cette machine, et elle n'est pas
non plus dans l'**historique** de l'image. Elle vit dans la **configuration**
de l'image, à côté de son environnement et de sa commande par défaut.

Elle est tirée au hasard à chaque passage : une valeur relevée lors d'un
passage précédent n'est plus valable.

## Ce qui n'est pas noté

La commande que vous avez tapée. Les quatre valeurs sont recalculées en
interrogeant les images, puis confrontées à ce que vous avez écrit. Plusieurs
chemins donnent le même compte, et ils comptent tous.
