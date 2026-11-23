# La base tombe, et sa limite mémoire semblait large

## La situation

Une base de données tourne en conteneur, avec une limite mémoire de 512 Mo. Elle
en consomme 300 en régime établi, ce qui laisse de la marge.

Elle est tuée par le noyau une fois par semaine, à chaque gros rapport. Les
métriques de l'application montrent 300 Mo au moment de la mort. Celles du
conteneur montrent 512.

L'écart est dans la **mémoire partagée**. La base s'en sert pour ses tampons de
tri, elle y écrit plusieurs centaines de mégaoctets pendant le rapport, et cette
mémoire-là est comptée dans celle du conteneur. L'application n'en sait rien :
pour elle, `/dev/shm` est un système de fichiers, pas de la mémoire.

Au même moment, un autre service refuse des connexions en se plaignant de
descripteurs de fichiers, sur une machine qui n'en manque pas du tout.

## L'objectif

Mesurer ces deux réglages qu'on ne regarde jamais, puis les poser. **Aucun
conteneur ne tourne** : vous les lancez vous-même, parce que les deux ne se
posent qu'à la création.

L'image `lab-ulimits:1.0` est prête.

Renseignez les deux lignes de `/opt/lab-ulimits/reponses.txt`, en lançant un
conteneur **sans aucune option** et en l'interrogeant :

```text
shm_defaut_mo=<la taille de /dev/shm par défaut, EN MÉGAOCTETS, sans unité>
nofile_defaut=<la limite de descripteurs de fichiers par défaut, telle que le
               conteneur la déclare>
```

La deuxième réponse est **plus modeste qu'on ne l'imagine** : la limite souple
est basse, alors que le plafond dur est très haut. C'est l'écart entre les deux
qui fait tout l'intérêt de la question.

Puis lancez un conteneur nommé `etroit` avec **deux** réglages :

```text
/dev/shm de 256 Mo, et une limite de 256 descripteurs de fichiers
```

Enfin, écrivez **128 Mo** dans son `/dev/shm`, et constatez ce que cela fait à
la **mémoire de son cgroup**.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Deux mécanismes qui ne sont pas de la même famille

Les cgroups plafonnent **depuis l'extérieur** : le noyau compte et refuse. Les
ulimits sont un mécanisme POSIX, bien antérieur, que **le processus porte
lui-même**.

Les chercher au même endroit est l'erreur que ce lab lève : la taille de la
mémoire partagée se lit dans l'inspection du conteneur et dans son système de
fichiers, la limite de descripteurs **seulement** depuis l'intérieur.

## La leçon du quatrième contrôle

`/dev/shm` est un **tmpfs**, donc de la mémoire, et cette mémoire est comptée
dans le cgroup du conteneur.

Une limite mémoire doit donc tenir compte de la taille de `/dev/shm`, sans quoi
le conteneur se fait tuer pour une mémoire qu'il croyait « à part ». C'est
l'incident du scénario, et c'est une cause de mort qui ne se lit dans aucune
documentation d'application.

## Ce qui est noté

L'**état du système**. Les deux valeurs par défaut sont **remesurées** au moment
de la notation, sur un conteneur neuf : le jour où Docker changera ses défauts,
ces contrôles suivront au lieu de devenir faux.

Et la quatrième mesure est une **pesée** : l'occupation de `/dev/shm` d'un côté,
la mémoire du cgroup de l'autre, et la comparaison des deux.

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. **Aucun conteneur ne
tourne** : vous les lancez vous-même, parce que les deux réglages du lab ne se
posent qu'à la **création**.

L'image `lab-ulimits:1.0` est prête.

Les deux premières réponses vont dans `/opt/lab-ulimits/reponses.txt`, une ligne
par entrée, sans espace autour du signe égal.

### 1. La taille de `/dev/shm` par défaut

À la ligne `shm_defaut_mo=`, **en mégaoctets, sans unité**.

Lancez un conteneur **sans aucune option** et demandez-lui. C'est une valeur qui
suffit à presque tout et qui ne suffit pas à une base de données, laquelle s'en
sert pour ses tampons de tri.

Le symptôme, le jour où elle manque, est un message d'erreur sur la mémoire
partagée, sans aucun rapport apparent avec un conteneur.

### 2. La limite de descripteurs de fichiers par défaut

À la ligne `nofile_defaut=`, telle que le conteneur la déclare.

Le même conteneur y répond. **La limite souple est basse, et son plafond dur très
haut : c'est l'écart entre les deux qui compte.**

La limite de descripteurs n'est pas le problème des conteneurs modernes. C'est
son **abaissement** qui en est un, et savoir d'où l'on part est ce qui permet de
reconnaître un réglage hérité d'un autre temps.

### 3. Un conteneur `etroit`, avec les deux réglages

Lancez-le avec :

```text
/dev/shm de 256 Mo, et une limite de 256 descripteurs de fichiers
```

Les deux sont vérifiés **dans** le conteneur, et c'est délibéré : c'est le seul
endroit où les deux sont vrais en même temps.

La taille de la mémoire partagée est un **montage**, que l'inspection déclare
aussi. La limite de descripteurs est un **ulimit**, que le processus porte
lui-même, et que seul le conteneur peut dire.

### 4. Écrivez 128 Mo dans sa mémoire partagée

Puis regardez la **mémoire de son cgroup**.

`/dev/shm` est un tmpfs, donc de la mémoire, et cette mémoire est comptée dans
le cgroup du conteneur. Le contrôle pèse les deux côtés et les compare.

**C'est la leçon du lab** : la mémoire partagée n'est pas un espace à part. Une
limite mémoire doit tenir compte de la taille de `/dev/shm`, sans quoi le
conteneur se fait tuer pour une mémoire qu'il croyait extérieure.

**Attention à l'outil** : un fichier *alloué* sans être écrit n'occupe aucune
page, et ni l'occupation du système de fichiers ni la mémoire du cgroup ne
monteraient. Écrivez de vrais octets.

### Un conseil d'outillage

Les fichiers du cgroup d'un conteneur se **lisent sans privilège** : mesuré sur
cette machine, ils sont en `r--r--r--` ou `rw-r--r--`, et un compte ordinaire les
ouvre sans `sudo`. Les **écrire** en demande un, et c'est ce qui sépare
l'observation du réglage.

Et si vos deux premières mesures vous semblent étranges, relancez-les : elles
sont justes, et elles sont remesurées de la même façon au moment de la notation.

### Ce qui n'est pas noté

La commande que vous avez tapée. Les deux réglages se posent en ligne de
commande comme par l'API. Seul l'état compte, et la pesée en fait partie.
