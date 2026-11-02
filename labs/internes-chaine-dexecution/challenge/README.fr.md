# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Le conteneur
`maillon` **tourne déjà**, et son processus exécute `sleep 876543`, une commande
qui ne sert à rien sinon à être reconnaissable.

Les trois premières réponses vont dans `/opt/lab-chaine/reponses.txt`, une
ligne par entrée, sans espace autour du signe égal.

**Aucune des trois ne se trouve dans un cours.** Ce sont des PID : ils
n'existent que sur cette machine, et ils sont réattribués à chaque démarrage.
Un `dsoxlab reset` invalide donc tout votre relevé, et il faut le refaire en
entier.

## 1. Le PID de l'intermédiaire qui porte ce conteneur

À la ligne `shim=`.

Entre le moteur et le processus de votre conteneur, un intermédiaire le porte.
La machine en compte **autant que de conteneurs** : le bon est celui dont la
ligne de commande cite l'identifiant de **ce** conteneur.

C'est aussi, et ce n'est pas un hasard, le parent du processus du conteneur.

## 2. Le PID du processus du conteneur sur l'hôte

À la ligne `pid_du_processus=`.

Le processus qui tourne **dans** le conteneur a aussi un PID **sur la machine
hôte**, et le moteur le déclare. C'est le bas de la chaîne.

Les deux premières réponses sont les deux bouts du même maillon, et le contrôle
exige qu'elles **s'accordent** : le parent du PID que vous annoncez ici doit
être exactement l'intermédiaire que vous avez annoncé plus haut. Si ce n'est pas
le cas, vous avez relevé l'un des deux avant un redémarrage.

## 3. Le PID de l'intermédiaire du second conteneur

À la ligne `shim_bis=`.

Lancez un conteneur nommé `maillon-bis`, puis **refaites la même recherche sur
lui**. Son intermédiaire porte forcément un autre PID que celui de `maillon` :
il y en a un par conteneur.

Cette réponse ne se déduit pas, elle se mesure une seconde fois. C'est le but.

## 4. Un intermédiaire par conteneur, et le même parent pour les deux

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

## Une idée reçue à ne pas en tirer

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

## Ce qui n'est pas noté

La commande que vous avez tapée. L'intermédiaire se trouve par la liste des
processus comme par l'arbre des processus, et le PID d'un processus par
plusieurs outils. Seul l'état compte.
