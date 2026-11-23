# Une couche qui pèse sept fois son contenu

## La situation

Une image occupe 101 Mo de **place sur le disque** pour une application qui en
occupe six. On entre dedans pour comprendre, et on ne trouve rien : le cache de
fabrication n'y est pas, les artefacts utiles sont là, le conteneur est juste.

Le Dockerfile, lui, nettoie bien. On le relit trois fois sans rien voir, parce
qu'il n'y a rien à voir : le nettoyage est simplement **une instruction trop
tard**.

Et la couche qui les porte pèse **44 Mo** selon `docker history`, sept fois les
6 Mo qu'elle livre. Cette place est occupée sur chaque disque qui tire l'image,
et la supprimer plus tard ne la sort pas de la couche.

## L'objectif

Le contexte est dans `/opt/lab-taille/appli`. Construisez le Dockerfile tel
quel, puis pesez l'image et comparez-la à ce qu'elle contient vraiment.

Entrez dedans : le cache n'y est pas, les artefacts y sont. Pesez ensuite
**chaque couche**, et vous verrez où sont passés les mégaoctets.

Construisez `appli:legere`, qui doit :

```text
imprimer son jeton et l'empreinte de fabrication
porter les trois artefacts de attendus.txt
peser à peine plus que son socle et ses artefacts
DÉRIVER TOUJOURS du socle lab-taille:1.0
```

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## La règle qui sort de ce lab

**Une couche garde ce qu'une couche suivante supprime.** Supprimer plus tard
cache le fichier au conteneur, et ne retire rien de l'image : la couche est
figée, et elle voyage en entier.

La suppression doit donc avoir lieu dans l'instruction **même** qui a créé ce
qu'on supprime.

## La dernière contrainte écarte une fausse bonne idée

Aplatir l'image donne la bonne taille. Mesuré sur cette machine : 25,5 Mo en
`DISK USAGE`, en une seule couche, soit le poids de la bonne écriture à
0,1 Mo près.

Et elle ne partage plus **aucune** couche avec son socle. Les couches communes
sont ce qui fait qu'un dépôt ne stocke le socle qu'une fois, et qu'un poste qui
l'a déjà ne télécharge que la différence. Une image aplatie est stockée et
transférée en entier, pour chaque variante : le gain affiché est rendu au
centuple.

**La taille se gagne dans les instructions, pas après coup.**

## Ce qui est mesuré

| Écriture | `DISK USAGE` | Couches | Plus grosse couche |
| --- | --- | --- | --- |
| nettoyage une instruction trop tard | 101,1 Mo | 6 | **44,1 Mo** |
| nettoyage dans la même instruction | 25,6 Mo | 5 | 9,08 Mo |
| la seconde, aplatie | 25,5 Mo | **1** | 15,4 Mo |

Les trois produisent un conteneur identique. C'est pourquoi ce lab se note à la
pesée, et à deux échelles : l'image entière, et chaque couche.

## Ce qui est noté

L'**état du système**. Aucun seuil n'est écrit dans le dépôt : les contrôles
pèsent le socle et les artefacts au moment de la notation, et en déduisent ce
qu'ils acceptent. Une valeur en dur serait fausse dès que le socle change de
version.

Le premier contrôle existe pour une raison précise : le moyen le plus rapide
d'alléger une image est de ne plus rien y mettre.

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Le contexte est dans
`/opt/lab-taille/appli` :

```text
Dockerfile      il MARCHE, et l'image pèse sept fois son contenu
attendus.txt    les trois artefacts que l'application utilise
src/main.sh     le code, qui imprime un jeton et l'empreinte de fabrication
```

**Commencez par construire et peser.** Puis entrez dans l'image : le cache de
fabrication n'y est pas, les artefacts y sont. Pesez enfin **chaque couche**.

### 1. L'image doit fonctionner et porter ses artefacts

`appli:legere` doit imprimer son jeton **et** une empreinte de fabrication, et
porter les trois artefacts de `attendus.txt`.

Ce contrôle existe pour une raison précise : le moyen le plus rapide d'alléger
une image est de ne plus rien y mettre. L'empreinte prouve en outre que la
fabrication a bien eu lieu **dans cette image**.

### 2. Aucune couche ne doit porter le cache

C'est le cœur du lab, et la mesure qui le rend visible.

Le conteneur ne montre rien : une couche ultérieure supprime le cache, donc il
est introuvable dans l'image assemblée. Il est pourtant là, **dans une couche**,
et il est téléchargé avec elle.

Mesuré sur cette machine : **44 Mo** de couche pour un nettoyage joué une
instruction trop tard, **6,3 Mo** quand il est joué dans la même.

### 3. La taille totale doit rester proche du nécessaire

Deux mesures plutôt qu'une, et elles ne disent pas la même chose.

Une couche peut rester sous son plafond pendant que plusieurs, ensemble, pèsent
le double du nécessaire : un cache écrit en deux fois, ou un second
téléchargement, se répartit sans jamais faire une grosse couche.

Le seuil est **calculé** : le socle est pesé, les artefacts aussi. Rien n'est
écrit dans le dépôt.

### 4. L'image doit toujours dériver du socle

Aplatir l'image donne la bonne taille, et c'est refusé.

Mesuré ici : 25,5 Mo en `DISK USAGE`, en **une** couche, soit le poids de la
bonne écriture à 0,1 Mo près. Les deux contrôles de pesée seraient verts.

Et elle ne partage plus aucune couche avec son socle. Les couches communes sont
ce qui fait qu'un dépôt ne stocke le socle qu'une fois, et qu'un poste qui l'a
déjà ne télécharge que la différence. Une image aplatie est stockée et
transférée **en entier**, pour chaque variante.

**La taille se gagne dans les instructions, pas après coup.**

### Ce qui n'est pas noté

La commande que vous avez tapée. Le nettoyage peut s'écrire de plusieurs façons
tant qu'il a lieu dans l'instruction qui a créé ce qu'il retire.
