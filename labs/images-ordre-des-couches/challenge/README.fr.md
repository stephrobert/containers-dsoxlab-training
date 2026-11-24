# Le Dockerfile marche, et c'est bien le problème

## La situation

L'intégration continue met six minutes à construire une image, et personne ne
comprend pourquoi : la dernière modification tenait en une ligne de code.

On regarde le Dockerfile. Il est court, lisible, et il **marche** : l'image
produite est juste, l'application tourne. Rien n'a l'air cassé, donc rien ne
semble à corriger, et c'est pour cela que ce défaut vit des années dans un
dépôt.

Puis on construit deux fois de suite en changeant une ligne entre les deux, et
on voit l'installation des dépendances se rejouer en entier. Elle n'a pas
changé. Elle est refaite parce qu'une instruction placée avant elle a changé.

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Le contexte de
construction est dans `/opt/lab-couches/appli` :

```text
Dockerfile          il MARCHE, et son ordre détruit le cache
dependances.txt     trois dépendances, une seconde d'installation chacune
src/main.sh         le code, qui imprime un jeton
notes/brouillon.log un brouillon, qui n'a rien à faire dans l'image
```

**Commencez par mesurer.** Construisez, changez une ligne de `src/main.sh`,
reconstruisez, et regardez l'installation se rejouer. Elle n'a pas changé.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

### 1. Construisez `appli:ordonnee`, qui marche vraiment

L'image doit **imprimer son jeton** quand on la lance, et porter les **trois
dépendances** déclarées dans le manifeste.

Ce contrôle existe pour une raison précise : le moyen le plus rapide de rendre
un cache efficace est de ne plus rien installer, et ce n'en est pas un.

### 2. Ne faites entrer que ce qui sert

Ni le brouillon, ni le Dockerfile ne doivent se retrouver dans l'image.

Une copie du contexte entier ne copie pas « le code », elle copie **tout**. Ces
fichiers grossissent l'image, et surtout **chacun d'eux invalide le cache quand
il change** : éditer le Dockerfile suffirait à refaire l'installation.

Un fichier d'exclusion ou une copie ciblée donnent le même état. Les deux
comptent.

### 3. Un changement de code ne doit plus refaire l'installation

C'est le cœur du lab.

Chaque instruction dépend de ce qui la précède, et de rien d'autre. Le code
change à chaque commit : tout ce qui vient **après** lui dans le Dockerfile sera
refait à chaque fois. Il ne doit donc rien rester derrière lui.

### 4. Un changement du manifeste doit, lui, le refaire

C'est la moitié qu'on oublie, et sans elle le lab enseignerait un piège.

Copier le manifeste **après** l'installation rendrait le contrôle précédent vert
et ferait servir le cache même quand les dépendances changent : l'image resterait
figée sur les anciennes, et personne ne le verrait avant la production.

Le contrôle vérifie les deux choses : que le travail est refait, et que la
nouvelle dépendance est **réellement installée**.

### Comment les contrôles mesurent cela

L'outil d'installation écrit une **empreinte** dans l'image, tirée au hasard au
moment où il tourne. Deux images qui portent la même empreinte n'ont pas rejoué
l'installation.

Les contrôles reconstruisent dans une **copie** du contexte : votre répertoire
de travail n'est pas touché.

## Ce qui est noté

L'**état du système**, et il est mesuré par l'effet. Les contrôles reconstruisent
l'image dans une **copie** du contexte, une fois avec une ligne de code en plus,
une fois avec une dépendance en plus, et comparent une empreinte que l'outil
d'installation laisse dans l'image. Deux images qui portent la même empreinte
n'ont pas rejoué l'installation.

Votre répertoire de travail n'est pas touché, et aucun chemin n'est imposé : un
fichier d'exclusion et une copie ciblée donnent le même état, et c'est l'état
qui compte.

### Ce qui n'est pas noté

La commande que vous avez tapée, et le chemin choisi. Rien à écrire dans un
formulaire : ce lab se note sur l'image.
