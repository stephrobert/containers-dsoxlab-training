# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Deux socles et un
contexte sont déjà là :

```text
lab-atelier:1.0     39,8 Mo, dont 30 d'outillage de fabrication
lab-execution:1.0   8,3 Mo, aucun outillage
appli/Dockerfile    une seule étape, sur l'atelier
```

**Commencez par construire tel quel sous le nom `appli:finale`**, puis cherchez
`/usr/lib/atelier` dans l'image. Essayez de le retirer, et pesez.

## 1. L'application doit tourner et porter son produit

`appli:finale` doit imprimer son jeton et le contenu du produit, dont la
**source** est celle du dépôt, tirée au hasard à chaque passage.

Ce contrôle existe pour une raison précise : la façon la plus rapide de retirer
un outillage est de ne plus rien fabriquer.

## 2. Ni l'outillage ni l'outil ne doivent y être

Deux mesures, et elles sont complémentaires : l'**absence des fichiers** dit que
le conteneur ne les voit plus, la **pesée** dit qu'ils ne sont plus dans
l'image.

Un `rm -rf` dans une instruction suivante donne la première sans la seconde.
`images-optimiser-la-taille` a montré pourquoi ; ici, c'est pire : il n'y a
même rien à nettoyer, puisque l'outillage vient du socle.

## 3. L'image doit être construite sur le socle d'exécution

Le contrôle compare les **couches**, dans les deux sens : celles du socle
d'exécution doivent être le préfixe des siennes, et celles de l'atelier ne
doivent **pas** l'être.

La seconde moitié compte autant : même légère, une image qui part de l'atelier
porte ses couches, et un dépôt les stocke et les transfère avec elle.

## 4. Le produit doit être fabriqué, et non recopié

Le contrôle change la **source** dans une copie du contexte, reconstruit, et
exige que le produit suive.

Le produit porte une empreinte tirée au moment où la fabrication tourne : si
elle ne change pas quand la source change, la fabrication n'a pas été rejouée,
et le produit ne dépend pas de sa source.

Votre image n'est pas écrasée : la reconstruction se fait sous un nom à elle.

## Deux choses à savoir avant de chercher

**L'outil de fabrication refuse de tourner sans son outillage.** Fabriquer sur
le socle d'exécution est donc impossible : ce n'est pas un oubli, c'est ce qui
ferme la fausse voie.

**Ne copiez que le produit.** Copier `/usr/lib` ou `/` depuis l'étape de
fabrication ramènerait l'outillage avec, et la pesée le dirait.

## Ce qui n'est pas noté

La commande que vous avez tapée. L'étape de fabrication peut être nommée ou
désignée autrement, et le Dockerfile peut être réécrit ou doublé.
