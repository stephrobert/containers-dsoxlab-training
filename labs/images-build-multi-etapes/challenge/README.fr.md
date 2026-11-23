# Un outillage qu'aucun nettoyage ne retire

## La situation

Une image d'application pèse 39 Mo, dont 30 d'un outillage de fabrication :
un faux compilateur et ses bibliothèques, qui n'ont plus rien à faire là une
fois la fabrication terminée.

Le réflexe habituel est de supprimer dans la **même instruction** que
l'installation, parce qu'une couche garde ce qu'une couche suivante efface. Et
on découvre ici qu'il n'y a **rien à supprimer** : l'outillage n'a pas été
installé par une instruction de ce Dockerfile. Il vient du **socle**.

Un `rm -rf` le cache au conteneur, et l'image pèse toujours 39 Mo. Mesuré sur
cette machine.

## L'objectif

Le contexte est dans `/opt/lab-multietapes/appli`. Construisez le Dockerfile
tel quel sous le nom `appli:finale` : il marche, l'application tourne, le
produit est juste.

Entrez dedans et cherchez `/usr/lib/atelier` et `/usr/local/bin/fabriquer`. Ils
y sont. Essayez de les retirer, et constatez ce que cela change à la pesée.

`appli:finale` doit :

```text
imprimer son jeton et le contenu du produit
NE PORTER NI l'outillage NI l'outil de fabrication
être construite sur le socle d'exécution
porter un produit RÉELLEMENT FABRIQUÉ, et non recopié
```

Un socle d'exécution est déjà sur la machine, sous le nom
`lab-execution:1.0`. L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Pourquoi il n'y a qu'une voie

Ce qui vient du socle ne se désinstalle pas. La seule façon qu'une image ne
porte pas un outillage est qu'elle **ne parte pas du socle qui le porte**.

La fabrication, elle, en a besoin. Il faut donc deux socles dans le même
Dockerfile : l'atelier pour fabriquer, l'exécution pour livrer, et le produit
qui passe de l'un à l'autre.

**L'outil de fabrication refuse de tourner sans son outillage.** Fabriquer
directement sur le socle d'exécution est donc impossible, et ce n'est pas un
oubli : c'est ce qui ferme la fausse voie.

## Ce qui est mesuré

| Image | Taille | Outillage présent |
| --- | --- | --- |
| socle d'exécution | 8,3 Mo | sans objet |
| socle d'atelier | 39,8 Mo | oui |
| une seule étape | 39,8 Mo | **oui** |
| deux étapes | 8,3 Mo | **non** |

Mesuré le 2026-10-30. L'image à deux étapes pèse exactement 85 octets de plus
que son socle, et son produit est identique.

## Ce qui est noté

L'**état du système**, à quatre endroits qui ne se recouvrent pas : le produit
et sa source, l'absence de l'outillage **doublée d'une pesée**, le socle lu dans
les couches, et la dépendance du produit à sa source.

Ce dernier contrôle change la source dans une **copie** du contexte et exige que
le produit suive. Un produit recopié depuis l'hôte resterait figé, et c'est la
seule façon de le voir : le produit porte une empreinte tirée au moment où la
fabrication tourne.

Votre image n'est pas écrasée au passage : la reconstruction se fait sous un
nom à elle.

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Deux socles et un
contexte sont déjà là :

```text
lab-atelier:1.0     39,8 Mo, dont 30 d'outillage de fabrication
lab-execution:1.0   8,3 Mo, aucun outillage
appli/Dockerfile    une seule étape, sur l'atelier
```

**Commencez par construire tel quel sous le nom `appli:finale`**, puis cherchez
`/usr/lib/atelier` dans l'image. Essayez de le retirer, et pesez.

### 1. L'application doit tourner et porter son produit

`appli:finale` doit imprimer son jeton et le contenu du produit, dont la
**source** est celle du dépôt, tirée au hasard à chaque passage.

Ce contrôle existe pour une raison précise : la façon la plus rapide de retirer
un outillage est de ne plus rien fabriquer.

### 2. Ni l'outillage ni l'outil ne doivent y être

Deux mesures, et elles sont complémentaires : l'**absence des fichiers** dit que
le conteneur ne les voit plus, la **pesée** dit qu'ils ne sont plus dans
l'image.

Un `rm -rf` dans une instruction suivante donne la première sans la seconde :
**une couche garde ce qu'une couche suivante efface**, et le fichier voyage avec
l'image même s'il a disparu de la vue finale.

Ici, c'est pire : il n'y a même **rien à nettoyer**, puisque l'outillage vient du
socle et non d'une instruction de ce Dockerfile.

### 3. L'image doit être construite sur le socle d'exécution

Le contrôle compare les **couches**, dans les deux sens : celles du socle
d'exécution doivent être le préfixe des siennes, et celles de l'atelier ne
doivent **pas** l'être.

La seconde moitié compte autant : même légère, une image qui part de l'atelier
porte ses couches, et un dépôt les stocke et les transfère avec elle.

### 4. Le produit doit être fabriqué, et non recopié

Le contrôle change la **source** dans une copie du contexte, reconstruit, et
exige que le produit suive.

Le produit porte une empreinte tirée au moment où la fabrication tourne : si
elle ne change pas quand la source change, la fabrication n'a pas été rejouée,
et le produit ne dépend pas de sa source.

Votre image n'est pas écrasée : la reconstruction se fait sous un nom à elle.

### Deux choses à savoir avant de chercher

**L'outil de fabrication refuse de tourner sans son outillage.** Fabriquer sur
le socle d'exécution est donc impossible : ce n'est pas un oubli, c'est ce qui
ferme la fausse voie.

**Ne copiez que le produit.** Copier `/usr/lib` ou `/` depuis l'étape de
fabrication ramènerait l'outillage avec, et la pesée le dirait.

### Ce qui n'est pas noté

La commande que vous avez tapée. L'étape de fabrication peut être nommée ou
désignée autrement, et le Dockerfile peut être réécrit ou doublé.
