# Qui lance vraiment un conteneur

## La situation

Vous tapez `docker run`, et un conteneur démarre. Si on vous demande qui a lancé
ce processus, la réponse spontanée est « Docker ». Elle est fausse, et le savoir
change la façon de diagnostiquer les pannes.

Au moins quatre programmes entrent en jeu, et le processus de votre conteneur
n'est l'enfant d'aucun de ceux qu'on croit. Le jour où le démon ne répond plus
alors que les conteneurs tournent, ou l'inverse, c'est cette chaîne qu'il faut
avoir en tête.

## L'objectif

La remonter, et constater où elle aboutit. Le conteneur `maillon` tourne, et son
processus exécute `sleep 876543`.

Renseignez les trois lignes de `/opt/lab-chaine/reponses.txt` :

```text
shim=<le PID du processus intermédiaire qui porte CE conteneur>
parent_du_shim=<le PID du PARENT de ce processus intermédiaire>
runtime=<le nom du runtime que le moteur emploie>
```

La deuxième réponse surprend, et c'est le but : **regardez-la deux fois avant de
conclure que vous vous êtes trompé.**

Puis, pour vérifier que cet intermédiaire est bien **par conteneur** et non
partagé, lancez un second conteneur nommé `maillon-bis`, et constatez qu'il a
son **propre** intermédiaire, de PID différent, mais le **même** parent.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Ce que vous allez découvrir

Que l'intermédiaire a été **détaché** du programme qui l'a créé. Son parent
n'est ni le démon, ni le service de conteneurs : c'est le gestionnaire de
services de la machine.

Ce détachement est délibéré. Il rend chaque conteneur indépendant du moteur qui
l'a lancé, et il explique qu'il y en ait un par conteneur plutôt qu'un pour
tous : un intermédiaire unique ferait de sa chute la chute de tous.

## Une idée reçue à ne pas en tirer

On conclut volontiers que les conteneurs survivent donc au redémarrage du démon.
**C'est faux par défaut**, et cela a été mesuré sur cette machine : sans le
réglage `live-restore`, le démon arrête ses conteneurs en partant et les
relance, avec un PID neuf.

Le détachement rend la survie **possible**, il ne la **produit** pas. C'est le
genre de nuance qui distingue une architecture comprise d'une architecture
récitée.

## Ce qui est noté

L'**état du système**, et tout est demandé au système au moment de la notation.
Aucun PID n'est écrit dans les contrôles ni dans la solution, pas même le `1`
qui pourrait sembler acquis : il est **lu**, parce que le détachement pourrait
aboutir ailleurs sur une machine réglée autrement.

Les PID changent à chaque démarrage : il n'y a rien à recopier d'un passage
précédent.
