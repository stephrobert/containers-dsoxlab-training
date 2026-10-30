# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service, machine en cgroup v2
unifié. Deux conteneurs **tournent déjà**, identiques à une chose près :

```text
mesure   lancé avec une limite mémoire de 256m
libre    lancé sans aucune limite
```

Les trois premières réponses vont dans `/opt/lab-cgroups/reponses.txt`, une
ligne par entrée, sans espace autour du signe égal.

## 1. Le chemin du cgroup de `mesure`

À la ligne `chemin=`, un chemin absolu.

Le cgroup d'un conteneur vit sur l'**hôte**, sous `/sys/fs/cgroup`, à un chemin
dérivé de l'identifiant **complet** du conteneur. Pas de son nom, pas de son
identifiant court : le moteur donne cet identifiant.

## 2. La limite mémoire que ce cgroup déclare

À la ligne `memoire_max=`, **telle quelle**.

Le noyau ne connaît que des octets : l'unité employée pour poser la limite ne
laisse aucune trace. La réponse attendue est le contenu du fichier, sans
retouche et sans conversion.

## 3. Ce que le même fichier contient pour `libre`

À la ligne `sans_limite=`.

Lisez le **même** fichier, dans le cgroup de l'autre conteneur. Vous chercherez
spontanément un nombre, et il n'y en a pas : c'est la question la plus utile du
lab, et elle explique à elle seule comment un conteneur peut prendre toute la
mémoire d'une machine.

## 4. Un conteneur `bride`, avec deux plafonds

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

## Un conseil d'outillage

Il faut être root pour lire les fichiers du cgroup d'un conteneur. C'est normal,
et ce n'est pas le sujet du lab.

Et si vous préférez regarder depuis l'intérieur : un conteneur voit **sa propre
limite** dans son `/sys/fs/cgroup/memory.max`. C'est ainsi qu'une application
bien élevée se règle elle-même au lieu de supposer la mémoire de la machine.

## Ce qui n'est pas noté

La commande que vous avez tapée. Les valeurs se lisent de plusieurs façons, et
les deux limites se posent à la création du conteneur, quelle qu'en soit la
méthode. Seul l'état compte.
