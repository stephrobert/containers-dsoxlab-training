# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. **Aucun conteneur ne
tourne** : vous les lancez vous-même, parce que les deux réglages du lab ne se
posent qu'à la **création**.

L'image `lab-ulimits:1.0` est prête.

Les deux premières réponses vont dans `/opt/lab-ulimits/reponses.txt`, une ligne
par entrée, sans espace autour du signe égal.

## 1. La taille de `/dev/shm` par défaut

À la ligne `shm_defaut_mo=`, **en mégaoctets, sans unité**.

Lancez un conteneur **sans aucune option** et demandez-lui. C'est une valeur qui
suffit à presque tout et qui ne suffit pas à une base de données, laquelle s'en
sert pour ses tampons de tri.

Le symptôme, le jour où elle manque, est un message d'erreur sur la mémoire
partagée, sans aucun rapport apparent avec un conteneur.

## 2. La limite de descripteurs de fichiers par défaut

À la ligne `nofile_defaut=`, telle que le conteneur la déclare.

Le même conteneur y répond. **La valeur surprend par sa taille : ce n'est pas une
erreur de lecture.**

La limite de descripteurs n'est pas le problème des conteneurs modernes. C'est
son **abaissement** qui en est un, et savoir d'où l'on part est ce qui permet de
reconnaître un réglage hérité d'un autre temps.

## 3. Un conteneur `etroit`, avec les deux réglages

Lancez-le avec :

```text
/dev/shm de 256 Mo, et une limite de 1024 descripteurs de fichiers
```

Les deux sont vérifiés **dans** le conteneur, et c'est délibéré : c'est le seul
endroit où les deux sont vrais en même temps.

La taille de la mémoire partagée est un **montage**, que l'inspection déclare
aussi. La limite de descripteurs est un **ulimit**, que le processus porte
lui-même, et que seul le conteneur peut dire.

## 4. Écrivez 128 Mo dans sa mémoire partagée

Puis regardez la **mémoire de son cgroup**.

`/dev/shm` est un tmpfs, donc de la mémoire, et cette mémoire est comptée dans
le cgroup du conteneur. Le contrôle pèse les deux côtés et les compare.

**C'est la leçon du lab** : la mémoire partagée n'est pas un espace à part. Une
limite mémoire doit tenir compte de la taille de `/dev/shm`, sans quoi le
conteneur se fait tuer pour une mémoire qu'il croyait extérieure.

**Attention à l'outil** : un fichier *alloué* sans être écrit n'occupe aucune
page, et ni l'occupation du système de fichiers ni la mémoire du cgroup ne
monteraient. Écrivez de vrais octets.

## Un conseil d'outillage

Il faut être root pour lire les fichiers du cgroup d'un conteneur.

Et si vos deux premières mesures vous semblent étranges, relancez-les : elles
sont justes, et elles sont remesurées de la même façon au moment de la notation.

## Ce qui n'est pas noté

La commande que vous avez tapée. Les deux réglages se posent en ligne de
commande comme par l'API. Seul l'état compte, et la pesée en fait partie.
