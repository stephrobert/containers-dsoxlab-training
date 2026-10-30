# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service avec le pilote
`overlay2`. Le conteneur `entrepot` **tourne déjà**, et il n'a encore rien
écrit.

Les deux premières réponses vont dans `/opt/lab-stockage/reponses.txt`, une
ligne par entrée, sans espace autour du signe égal.

## 1. Le pilote de stockage du moteur

À la ligne `pilote=`.

Il n'y a pas une seule façon d'empiler des couches : le moteur en connaît
plusieurs, et le choix change les chemins, les performances, et jusqu'aux
systèmes de fichiers acceptables sous sa racine. Savoir lequel est en place est
la première question d'un diagnostic de stockage.

Le moteur l'indique dans ses informations générales, à côté du répertoire où il
garde tout.

## 2. La couche d'écriture de `entrepot`

À la ligne `ecriture=`, un chemin absolu sur l'hôte.

L'inspection du conteneur donne **quatre** chemins, et ils n'ont pas le même
rôle : l'un porte les couches en lecture seule de l'image, l'un est la vue
fusionnée que le conteneur voit, l'un est un répertoire de travail, et l'un
reçoit les écritures.

Seul le dernier est demandé.

## 3. Une trace, écrite dedans et lue dehors

Depuis le conteneur, écrivez dans `/trace-ecriture.txt` la ligne :

```text
ceci-a-ete-ecrit-dans-le-conteneur
```

Le contrôle la lit **deux fois** : dans le conteneur, puis sur le disque de
l'hôte, dans la couche que vous avez annoncée. Sans export, sans copie, sans
commande particulière.

C'est le point du lab : un conteneur n'écrit pas dans un ailleurs.

## 4. Une charge de 5 Mo, et une pesée

Depuis le conteneur, créez un fichier `/charge.bin` de **5 Mo**.

Le contrôle **pèse la couche** sur l'hôte : elle doit faire au moins 5 Mo. Ce
qu'un conteneur écrit n'est pas gratuit, cela occupe le disque de la machine, et
c'est la cause de pannes qu'on diagnostique mal.

**Attention au choix de l'outil** : un fichier *alloué* sans être écrit peut
n'occuper aucun bloc sur le disque, et la pesée le compterait pour zéro. Écrivez
de vrais octets.

## Un conseil d'outillage

La racine du moteur n'est pas lisible par un compte ordinaire. Il faut être root
pour regarder, c'est normal, et ce n'est pas le sujet du lab.

## Ce qui n'est pas noté

La commande que vous avez tapée. Les deux valeurs se lisent de plusieurs façons,
et les deux écritures se font depuis le conteneur par n'importe quel moyen. Seul
l'état compte.
