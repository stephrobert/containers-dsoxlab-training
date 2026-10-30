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

Renseignez les trois lignes de `/opt/lab-cgroups/reponses.txt` :

```text
chemin=<le chemin ABSOLU du cgroup de `mesure`, sur l'hôte>
memoire_max=<la limite mémoire que ce cgroup déclare, telle quelle>
sans_limite=<ce que le MÊME fichier contient pour `libre`>
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
