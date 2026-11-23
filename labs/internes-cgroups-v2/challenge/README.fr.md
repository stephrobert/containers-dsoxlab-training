# Un conteneur a mangé toute la mémoire de la machine

## La situation

Trois heures du matin, la machine ne répond plus. Au redémarrage, le journal du
noyau raconte la fin : le tueur de processus a frappé, et il a choisi la base de
données, parce qu'elle était le plus gros consommateur du moment.

Le coupable n'était pas la base. C'était un conteneur de traitement d'images,
lancé six mois plus tôt pour un essai, et jamais enlevé. Il a pris toute la
mémoire disponible, tranquillement, parce que **rien ne le lui interdisait**.

Personne n'avait oublié de régler sa limite. Il n'y avait pas de limite à
régler : un conteneur sans `--memory` n'a pas de plafond élevé, il n'a **pas de
plafond du tout**, et c'est très différent.

## L'objectif

Aller voir où vivent ces limites, et constater la différence. Deux conteneurs
tournent, identiques à une chose près :

```text
mesure   lancé avec une limite mémoire de 256m
libre    lancé sans aucune limite
```

Le lab précédent montrait ce qu'un conteneur **voit**. Celui-ci montre ce qu'il
peut **consommer**, et c'est un mécanisme complètement différent : les cgroups
comptent et plafonnent, là où les namespaces restreignent une vue.

Renseignez les quatre lignes de `/opt/lab-cgroups/reponses.txt` :

```text
chemin=<le chemin ABSOLU du cgroup de `mesure`, sur l'hôte>
memoire_max=<la limite mémoire que ce cgroup déclare, telle quelle>
sans_limite=<ce que le MÊME fichier contient pour `libre`>
sans_limite_pids=<ce que `pids.max` contient pour `libre`, dans le même
                  cgroup : un conteneur lancé sans aucune limite porte
                  quand même un plafond de processus, et ce n'est pas
                  la même valeur que pour la mémoire>
```

Puis lancez un conteneur nommé `bride`, avec **deux** limites à la fois : 128m
de mémoire, et 64 processus au maximum.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## La troisième question n'est pas une formalité

On cherche spontanément un nombre, et la réponse n'en est pas un.

C'est tout l'intérêt de la poser : constater soi-même ce que contient ce
fichier quand il n'y a pas de limite explique l'incident du scénario mieux que
n'importe quelle phrase.

## Pourquoi deux limites sur `bride`, et non une

Parce qu'une seule laisserait croire que la mémoire est le sujet. Elle n'en est
qu'un exemple : un cgroup plafonne la mémoire, le temps processeur, le nombre de
processus, les entrées-sorties.

Le nombre de processus protège d'une panne **différente**, celle qui remplit la
table des processus de la machine, où une limite mémoire ne changerait rien.

## Ce qui est noté

L'**état du système**, lu dans le cgroup et non dans l'option qui l'a demandée.
Ce que l'option a demandé n'est pas forcément ce que le noyau applique, et c'est
le noyau qui décide.

Le chemin dépend de l'identifiant du conteneur, qui change à chaque création :
il n'y a rien à recopier d'un passage précédent.

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service, machine en cgroup v2
unifié. Deux conteneurs **tournent déjà**, identiques à une chose près :

```text
mesure   lancé avec une limite mémoire de 256m
libre    lancé sans aucune limite
```

Les trois premières réponses vont dans `/opt/lab-cgroups/reponses.txt`, une
ligne par entrée, sans espace autour du signe égal.

### 1. Le chemin du cgroup de `mesure`

À la ligne `chemin=`, un chemin absolu.

Le cgroup d'un conteneur vit sur l'**hôte**, sous `/sys/fs/cgroup`, à un chemin
dérivé de l'identifiant **complet** du conteneur. Pas de son nom, pas de son
identifiant court : le moteur donne cet identifiant.

### 2. La limite mémoire que ce cgroup déclare

À la ligne `memoire_max=`, **telle quelle**.

Le noyau ne connaît que des octets : l'unité employée pour poser la limite ne
laisse aucune trace. La réponse attendue est le contenu du fichier, sans
retouche et sans conversion.

### 3. Ce que le même fichier contient pour `libre`

À la ligne `sans_limite=`, et à la ligne `sans_limite_pids=` le `pids.max`
du même cgroup : un conteneur sans limite porte quand même un plafond de
processus, qui dépend de la machine et n'est dans aucune leçon.

Lisez le **même** fichier, dans le cgroup de l'autre conteneur. Vous chercherez
spontanément un nombre, et il n'y en a pas : c'est la question la plus utile du
lab, et elle explique à elle seule comment un conteneur peut prendre toute la
mémoire d'une machine.

### 4. Un conteneur `bride`, avec deux plafonds

Lancez un conteneur nommé `bride` portant **deux** limites à la fois :

```text
128m de mémoire, et 64 processus au maximum
```

Les deux doivent se lire **dans son cgroup**, et c'est là qu'elles sont
vérifiées : ce que l'option a demandé n'est pas forcément ce que le noyau
applique.

Deux limites et non une, parce qu'une seule laisserait croire que la mémoire est
le sujet. Le nombre de processus protège d'une panne différente : celle qui
remplit la table des processus de la machine, où une limite mémoire ne
changerait rien.

### Un conseil d'outillage

Les fichiers du cgroup d'un conteneur se **lisent sans privilège** : mesuré sur
cette machine, ils sont en `r--r--r--` ou `rw-r--r--`, et un compte ordinaire les
ouvre sans `sudo`. Les **écrire** en demande un, et c'est ce qui sépare
l'observation du réglage.

Et si vous préférez regarder depuis l'intérieur : un conteneur voit **sa propre
limite** dans son `/sys/fs/cgroup/memory.max`. C'est ainsi qu'une application
bien élevée se règle elle-même au lieu de supposer la mémoire de la machine.

### Ce qui n'est pas noté

La commande que vous avez tapée. Les valeurs se lisent de plusieurs façons, et
les deux limites se posent à la création du conteneur, quelle qu'en soit la
méthode. Seul l'état compte.
