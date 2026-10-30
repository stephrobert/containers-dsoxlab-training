# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Le conteneur
`maillon` **tourne déjà**, et son processus exécute `sleep 876543`, une commande
qui ne sert à rien sinon à être reconnaissable.

Les trois premières réponses vont dans `/opt/lab-chaine/reponses.txt`, une
ligne par entrée, sans espace autour du signe égal.

## 1. Le PID de l'intermédiaire qui porte ce conteneur

À la ligne `shim=`.

Entre le moteur et le processus de votre conteneur, un intermédiaire le porte.
La machine en compte **autant que de conteneurs** : le bon est celui dont la
ligne de commande cite l'identifiant de **ce** conteneur.

C'est aussi, et ce n'est pas un hasard, le parent du processus du conteneur.

## 2. Le PID du parent de cet intermédiaire

À la ligne `parent_du_shim=`.

**Regardez-la deux fois avant de conclure que vous vous êtes trompé.** La
réponse surprend, et c'est le but de la question : ni le démon ni le service de
conteneurs n'est le parent de cet intermédiaire.

Il en a été **détaché** à dessein.

## 3. Le runtime employé

À la ligne `runtime=`.

Le moteur ne crée pas les conteneurs lui-même : il délègue à un runtime, et ce
runtime est un **choix**. Le savoir est ce qui rend compréhensible qu'on puisse
en installer un autre, pour isoler plus fort ou pour mesurer autrement.

Deux sources l'indiquent : le défaut du moteur, et celui du conteneur. C'est
celui du **conteneur** qui est demandé, parce que c'est le seul vrai pour ce
conteneur.

## 4. Un second conteneur, et son propre intermédiaire

Lancez un conteneur nommé `maillon-bis`, et constatez qu'il a son **propre**
intermédiaire :

- de PID **différent** de celui de `maillon` ;
- mais de **même** parent.

Les trois faits sont vérifiés ensemble. Sans le dernier, deux intermédiaires
distincts pourraient venir de deux chaînes différentes, et la démonstration
serait incomplète.

C'est ce qui permet à un conteneur de vivre sa vie sans que les autres en
dépendent : un intermédiaire unique ferait de sa chute la chute de tous.

## Une idée reçue à ne pas en tirer

On conclut volontiers que les conteneurs survivent donc au redémarrage du démon.
**C'est faux par défaut.** Mesuré sur cette machine : sans le réglage
`live-restore`, le démon arrête ses conteneurs en partant et les relance, avec
un PID neuf.

Le détachement rend la survie **possible**, il ne la **produit** pas.

Et n'essayez pas de le vérifier en redémarrant le démon plusieurs fois : la
limite de systemd finit par refuser le démarrage, et il faut alors un
`reset-failed` pour s'en sortir.

## Ce qui n'est pas noté

La commande que vous avez tapée. L'intermédiaire se trouve par la liste des
processus comme par l'arbre des processus, et son parent par plusieurs outils.
Seul l'état compte.
