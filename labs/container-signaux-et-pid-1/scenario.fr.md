# Dix secondes pour s'arrêter, et un code 137 dans les alertes

## La situation

Chaque déploiement de votre application déclenche la même alerte : le conteneur
sortant est signalé comme ayant « échoué », code 137. L'équipe a pris
l'habitude de l'ignorer, ce qui est le vrai problème : une alerte qu'on apprend
à ignorer ne protège plus de rien.

Deux détails intriguent. L'arrêt met exactement le délai d'attente du moteur,
jamais moins. Et l'application sait pourtant se terminer proprement : son code
piège le signal, écrit une ligne dans ses journaux et sort avec un zéro. Cette
ligne n'apparaît jamais.

Un conteneur qui met le délai complet à mourir n'est pas un conteneur lent :
c'est un conteneur qu'on finit par **tuer**, parce qu'il n'a pas répondu à la
demande polie qui précédait. Reste à savoir pourquoi la demande n'arrive pas.

## L'objectif

Le conteneur `fragile` tourne. Les sources de son image sont lisibles dans
`/opt/lab-signaux` : l'application, le script d'entrée, et le Dockerfile.

1. **Arrêter `fragile`**, et constater son code de sortie. Il ne sera pas zéro :
   c'est le symptôme, et il est noté tel quel. **Ne le réparez pas**, ce
   conteneur est la pièce à conviction.
2. Construire une image `img-corrige:1.0` dans laquelle le PID 1 du conteneur
   est l'**application**, et non le script d'entrée.
3. Lancer puis arrêter un conteneur `robuste` issu de cette image : son code de
   sortie doit être **zéro**.
4. Ses journaux doivent porter `sigterm-recu`, que `fragile` n'a jamais écrit.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

Un seul mot sépare les deux images. Et le script d'entrée doit **continuer à
faire sa préparation** : le vider corrigerait le symptôme en supprimant la
raison d'être du script, ce qu'un contrôle refuse.

## Ce qui est noté

L'**état du moteur** : qui est le processus numéro un, les codes de sortie, et
la trace que l'application écrit elle-même quand elle reçoit le signal.

Pas la façon de corriger. Plusieurs la permettent, et toutes comptent du moment
que le signal atteint un processus capable d'en faire quelque chose.
