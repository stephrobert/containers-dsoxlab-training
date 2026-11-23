# L'application est lente, et elle a pourtant de la marge

## La situation

Un service tourne en conteneur, bridé à la moitié d'un processeur, ce qui est
largement suffisant pour ce qu'il fait. Et il est lent. Pas en panne : lent,
par à-coups, avec des temps de réponse qui triplent sans raison apparente.

Les métriques de la machine sont calmes. Celles du conteneur montrent qu'il
consomme exactement ce qu'on lui a accordé, ce qui devrait rassurer.

La cause est dans l'application elle-même, et elle est banale : au démarrage,
elle demande au système combien de processeurs sont disponibles, et dimensionne
ses fils d'exécution sur cette réponse. Elle en a obtenu le nombre de la
**machine**, pas celui de sa limite. Elle lance donc deux fois trop de travail
en parallèle, et passe son temps à se faire retenir par le noyau.

## L'objectif

Voir d'où vient le malentendu. Le conteneur `brideur` tourne, bridé à 0.5 CPU,
et il ne fait rien pour l'instant.

Renseignez les deux lignes de `/opt/lab-cpu/reponses.txt` :

```text
quota=<ce que le cgroup de `brideur` déclare comme limite de temps processeur,
       TEL QUEL>
cpu_vus=<le nombre de CPU que `brideur` VOIT, de l'intérieur>
```

La deuxième réponse est celle qui compte, et elle surprend. **Comparez-la au
nombre de CPU de la machine avant de conclure que vous vous êtes trompé.**

Puis deux gestes :

1. lancez un conteneur nommé `epingle` qui, lui, ne voit **qu'un seul** CPU. Ce
   n'est pas la même option, et ce n'est pas le même mécanisme.
2. mettez `brideur` sous charge, assez pour que le noyau doive l'**étrangler**.
   Son cgroup compte les étranglements : tant que le compteur est à zéro, la
   limite n'a jamais mordu.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Deux mécanismes qu'on confond

| Ce qu'on pose | Ce que le noyau limite | Ce que le conteneur voit |
| --- | --- | --- |
| une part de CPU | le **temps** accordé par tranche | **tout**, inchangé |
| un ensemble de CPU | les **processeurs** utilisables | moins |

Le premier est celui qu'on emploie partout, et c'est lui qui crée le
malentendu. Le second est plus rare, et c'est le seul qui change la réponse que
le système donne à l'application.

## Ce qui est noté

L'**état du système**, et le quatrième contrôle demande une **preuve** plutôt
qu'une déclaration. Une limite qu'on n'a jamais vue mordre est une limite qu'on
croit sur parole : elle est peut-être juste, elle n'est pas prouvée.

C'est la différence entre lire une configuration et constater un comportement,
et c'est la seule qui compte le jour où une application est lente sans qu'on
sache pourquoi.

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable à **deux** processeurs, moteur en
service. Le conteneur `brideur` **tourne déjà**, bridé à **0.5 CPU**, et il ne
fait rien pour l'instant.

Les deux premières réponses vont dans `/opt/lab-cpu/reponses.txt`, une ligne par
entrée, sans espace autour du signe égal.

### 1. Le quota que le cgroup déclare

À la ligne `quota=`, **tel quel**.

Le noyau ne connaît pas les fractions de CPU : il compte un **temps** par
tranche de temps. La valeur s'écrit donc en deux nombres, et `0.5` n'y laisse
aucune trace.

C'est aussi ce qui explique que la limite s'applique par **étranglement** plutôt
qu'en refusant du travail.

### 2. Le nombre de CPU que `brideur` voit

À la ligne `cpu_vus=`, en le demandant **au conteneur lui-même**.

**Comparez-le au nombre de CPU de la machine avant de conclure que vous vous
êtes trompé.** La réponse surprend, et c'est la question la plus utile du lab.

Une limite de temps n'est pas une restriction de vue. Une application qui
dimensionne ses fils d'exécution sur ce nombre en lance bien trop, et passe son
temps à se faire retenir.

### 3. Un conteneur qui voit moins de CPU

Lancez un conteneur nommé `epingle` qui ne voit **qu'un seul** CPU.

Ce n'est pas la même option que celle qui bride `brideur`, et ce n'est pas le
même mécanisme : l'une limite le **temps** accordé, l'autre restreint
l'**ensemble des processeurs** utilisables. Seule la seconde change ce que le
conteneur voit.

Le cgroup déclare les deux, mais à des endroits différents.

### 4. La preuve que la limite a mordu

Mettez `brideur` sous charge, assez pour que le noyau doive l'**étrangler**.

Son cgroup compte les étranglements. Tant que ce compteur est à **zéro**, la
limite n'a jamais mordu : elle est peut-être juste, elle n'est pas prouvée.

**Une charge suffisante demande plus d'un processus occupé.** Un seul peut tenir
sous le plafond sans jamais le toucher, et le compteur resterait à zéro.

### Un conseil d'outillage

Les fichiers du cgroup d'un conteneur se **lisent sans privilège** : mesuré sur
cette machine, ils sont en `r--r--r--` ou `rw-r--r--`, et un compte ordinaire les
ouvre sans `sudo`. Les **écrire** en demande un, et c'est ce qui sépare
l'observation du réglage.

Et si vous arrêtez votre charge avec `pkill -f`, sachez que le motif peut
correspondre au shell qui porte votre commande : il se tue lui-même, et le code
de retour est celui d'un signal reçu. Ce n'est pas une erreur.

### Ce qui n'est pas noté

La commande que vous avez tapée. La charge se produit de plusieurs façons, et
les deux options de limitation se posent à la création du conteneur. Seul l'état
compte, et le compteur d'étranglements en fait partie.
