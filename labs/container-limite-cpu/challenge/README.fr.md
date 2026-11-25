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
**machine**, pas celui de sa limite. Elle lance donc bien trop de travail en
parallèle, et passe son temps à se faire retenir par le noyau.

## Mission

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

Une charge suffisante est une charge qui demande plus que la limite. Mesurez le
compteur avant et après, sans supposer le nombre de processus nécessaires.

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
