# Un outillage qu'aucun nettoyage ne retire

## La situation

Une image d'application pèse 39 Mo, dont 30 d'un outillage de fabrication :
un faux compilateur et ses bibliothèques, qui n'ont plus rien à faire là une
fois la fabrication terminée.

On applique ce que le lab précédent a enseigné : supprimer dans la même
instruction. Et on découvre qu'il n'y a **rien à supprimer** : l'outillage n'a
pas été installé par une instruction de ce Dockerfile. Il vient du **socle**.

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
