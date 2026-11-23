# Le disque est plein, et aucun volume n'est en cause

## La situation

Le serveur alerte : la partition qui porte `/var` est à 96 %. Vous cherchez le
coupable dans les volumes, puisque c'est là que les données vivent. Ils pèsent
quelques centaines de mégaoctets en tout.

Vous cherchez dans les images. Elles sont nombreuses, mais le compte ne tombe
pas non plus.

Ce qui remplit le disque, ce sont les conteneurs eux-mêmes. Pas leurs volumes :
**eux**. Chacun a une couche d'écriture à lui, qui reçoit tout ce qu'il écrit
hors d'un volume, et cette couche est un répertoire ordinaire de votre disque.
Un service qui journalise dans un fichier au lieu de sa sortie standard la
remplit tranquillement, pendant des mois.

## L'objectif

Aller voir cet endroit, et constater qu'il n'a rien de mystérieux. Le conteneur
`entrepot` tourne, et il n'a encore rien écrit.

Renseignez les deux lignes de `/opt/lab-stockage/reponses.txt` :

```text
pilote=<le pilote de stockage que le moteur emploie>
ecriture=<le chemin ABSOLU de la couche d'ÉCRITURE de `entrepot`, sur l'hôte>
```

Puis, **depuis le conteneur**, faites deux choses :

1. écrivez dans `/trace-ecriture.txt` la ligne
   `ceci-a-ete-ecrit-dans-le-conteneur` ;
2. créez un fichier `/charge.bin` de 5 Mo.

Les deux doivent se retrouver sur le **disque de l'hôte**, dans la couche
d'écriture.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Ce que vous allez constater

Que le fichier écrit dans le conteneur se lit depuis l'hôte **immédiatement**,
sans export ni commande particulière. Un conteneur n'écrit pas dans un ailleurs.

Et que la couche ne contient **que les différences** : après une écriture, elle
ne porte que ce fichier, pas une copie du système de fichiers. C'est ce qui rend
les conteneurs légers, et c'est aussi ce qui fait qu'ils grossissent sans qu'on
les voie grossir.

## Ce qui est noté

L'**état du système**, et la quatrième mesure est une **pesée** : la couche doit
peser au moins ce que vous y avez écrit. C'est la conséquence qui compte en
exploitation, et celle qu'on découvre trop tard.

Un fichier créé dans un volume ou en mémoire n'apparaîtrait pas là, et c'est
précisément la différence que les labs sur les volumes ont enseignée.

## Une précision d'outillage

`/var/lib/docker` n'est pas lisible par un compte ordinaire. Il faut être root
pour regarder, c'est normal, et ce n'est pas le sujet du lab.

Attention aussi au choix du fichier de charge : un fichier **alloué** sans être
écrit peut n'occuper aucun bloc sur le disque, et la pesée le compterait pour
zéro. Écrivez de vrais octets.

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service avec le pilote
`overlayfs` sur une installation neuve de Docker 29, `overlay2` apres une mise a niveau : regardez ce que le moteur declare, ne le supposez pas. Le conteneur `entrepot` **tourne déjà**, et il n'a encore rien
écrit.

Les deux premières réponses vont dans `/opt/lab-stockage/reponses.txt`, une
ligne par entrée, sans espace autour du signe égal.

### 1. Le pilote de stockage du moteur

À la ligne `pilote=`.

Il n'y a pas une seule façon d'empiler des couches : le moteur en connaît
plusieurs, et le choix change les chemins, les performances, et jusqu'aux
systèmes de fichiers acceptables sous sa racine. Savoir lequel est en place est
la première question d'un diagnostic de stockage.

Le moteur l'indique dans ses informations générales, à côté du répertoire où il
garde tout.

### 2. La couche d'écriture de `entrepot`

À la ligne `ecriture=`, un chemin absolu sur l'hôte.

L'inspection du conteneur donne **quatre** chemins, et ils n'ont pas le même
rôle : l'un porte les couches en lecture seule de l'image, l'un est la vue
fusionnée que le conteneur voit, l'un est un répertoire de travail, et l'un
reçoit les écritures.

Seul le dernier est demandé.

### 3. Une trace, écrite dedans et lue dehors

Depuis le conteneur, écrivez dans `/trace-ecriture.txt` la ligne :

```text
ceci-a-ete-ecrit-dans-le-conteneur
```

Le contrôle la lit **deux fois** : dans le conteneur, puis sur le disque de
l'hôte, dans la couche que vous avez annoncée. Sans export, sans copie, sans
commande particulière.

C'est le point du lab : un conteneur n'écrit pas dans un ailleurs.

### 4. Une charge de 5 Mo, et une pesée

Depuis le conteneur, créez un fichier `/charge.bin` de **5 Mo**.

Le contrôle **pèse la couche** sur l'hôte : elle doit faire au moins 5 Mo. Ce
qu'un conteneur écrit n'est pas gratuit, cela occupe le disque de la machine, et
c'est la cause de pannes qu'on diagnostique mal.

**Attention au choix de l'outil** : un fichier *alloué* sans être écrit peut
n'occuper aucun bloc sur le disque, et la pesée le compterait pour zéro. Écrivez
de vrais octets.

### Un conseil d'outillage

La racine du moteur n'est pas lisible par un compte ordinaire. Il faut être root
pour regarder, c'est normal, et ce n'est pas le sujet du lab.

### Ce qui n'est pas noté

La commande que vous avez tapée. Les deux valeurs se lisent de plusieurs façons,
et les deux écritures se font depuis le conteneur par n'importe quel moyen. Seul
l'état compte.
