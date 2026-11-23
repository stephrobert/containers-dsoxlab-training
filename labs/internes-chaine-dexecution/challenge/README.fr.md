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
pid_du_processus=<le PID du processus du conteneur sur l'hôte>
shim_bis=<le PID de l'intermédiaire du second conteneur>
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
réglage `live-restore`, un conteneur sans politique de redémarrage ressort
`exited`, PID 0, code 137, et il ne repart **pas**. Seule une politique le
relance, et il a alors un PID neuf : `--restart always` et
`--restart unless-stopped` le font, aucune autre.

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

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Le conteneur
`maillon` **tourne déjà**, et son processus exécute `sleep 876543`, une commande
qui ne sert à rien sinon à être reconnaissable.

Les trois premières réponses vont dans `/opt/lab-chaine/reponses.txt`, une
ligne par entrée, sans espace autour du signe égal.

**Aucune des trois ne se trouve dans un cours.** Ce sont des PID : ils
n'existent que sur cette machine, et ils sont réattribués à chaque démarrage.
Un `dsoxlab reset` invalide donc tout votre relevé, et il faut le refaire en
entier.

### 1. Le PID de l'intermédiaire qui porte ce conteneur

À la ligne `shim=`.

Entre le moteur et le processus de votre conteneur, un intermédiaire le porte.
La machine en compte **autant que de conteneurs** : le bon est celui dont la
ligne de commande cite l'identifiant de **ce** conteneur.

C'est aussi, et ce n'est pas un hasard, le parent du processus du conteneur.

### 2. Le PID du processus du conteneur sur l'hôte

À la ligne `pid_du_processus=`.

Le processus qui tourne **dans** le conteneur a aussi un PID **sur la machine
hôte**, et le moteur le déclare. C'est le bas de la chaîne.

Les deux premières réponses sont les deux bouts du même maillon, et le contrôle
exige qu'elles **s'accordent** : le parent du PID que vous annoncez ici doit
être exactement l'intermédiaire que vous avez annoncé plus haut. Si ce n'est pas
le cas, vous avez relevé l'un des deux avant un redémarrage.

### 3. Le PID de l'intermédiaire du second conteneur

À la ligne `shim_bis=`.

Lancez un conteneur nommé `maillon-bis`, puis **refaites la même recherche sur
lui**. Son intermédiaire porte forcément un autre PID que celui de `maillon` :
il y en a un par conteneur.

Cette réponse ne se déduit pas, elle se mesure une seconde fois. C'est le but.

### 4. Un intermédiaire par conteneur, et le même parent pour les deux

Les deux conteneurs étant debout, le dernier contrôle vérifie ensemble :

- que les deux intermédiaires ont des PID **différents** ;
- qu'ils ont le **même** parent ;
- et que le runtime déclaré par le conteneur se retrouve dans le **nom du
  programme** de son intermédiaire.

Sans le deuxième point, deux intermédiaires distincts pourraient venir de deux
chaînes différentes, et la démonstration serait incomplète. Le troisième fait
**constater** quel programme crée réellement le conteneur, au lieu de vous
demander de le réciter.

C'est ce qui permet à un conteneur de vivre sa vie sans que les autres en
dépendent : un intermédiaire unique ferait de sa chute la chute de tous.

Et regardez le parent deux fois avant de conclure que vous vous êtes trompé :
ni le démon ni le service de conteneurs n'est le parent de ces intermédiaires.
Ils en ont été **détachés** à dessein.

### Une idée reçue à ne pas en tirer

On conclut volontiers que les conteneurs survivent donc au redémarrage du démon.
**C'est faux par défaut.** Mesuré sur cette machine, `live-restore` étant
désactivé : un conteneur sans politique de redémarrage ressort `exited`, PID 0,
code 137, et il ne repart **pas**. Seule une politique le relance, et il a alors
un PID neuf : `--restart always` et `--restart unless-stopped` le font, aucune
autre.

Le détachement rend la survie **possible**, il ne la **produit** pas.

Et n'essayez pas de le vérifier en redémarrant le démon plusieurs fois : la
limite de systemd finit par refuser le démarrage, et il faut alors un
`reset-failed` pour s'en sortir.

### Ce qui n'est pas noté

La commande que vous avez tapée. L'intermédiaire se trouve par la liste des
processus comme par l'arbre des processus, et le PID d'un processus par
plusieurs outils. Seul l'état compte.
