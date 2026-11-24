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

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Le conteneur
`fragile` tourne, et les sources de son image sont lisibles dans
`/opt/lab-signaux` : `app.sh`, `entree.sh` et le `Dockerfile`.

L'application **sait** recevoir un SIGTERM : son code le piège, écrit
`sigterm-recu` et sort avec zéro. Elle ne le fait jamais.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

### 1. Arrêter `fragile`, et garder le symptôme

Son code de sortie ne doit **pas** être zéro, et ses journaux ne doivent **pas**
porter `sigterm-recu`.

C'est volontaire : ce conteneur est la pièce à conviction. **Ne le réparez
pas**, ne le supprimez pas, ne le relancez pas depuis une image corrigée. Les
trois contrôles suivants s'y comparent.

Regardez aussi combien de temps l'arrêt met. Ce n'est pas un détail, c'est la
signature de la panne.

### 2. Une image `img-corrige:1.0` dont le PID 1 est l'application

Le contrôle lance un conteneur jetable depuis votre image et lit le nom du
processus numéro un. Il doit être celui de l'application, pas celui du script
d'entrée.

**Le script d'entrée doit rester et continuer sa préparation.** Le vider
corrigerait le signal en supprimant la raison d'être du script, et un contrôle
du point 4 vérifie que sa ligne figure toujours dans les journaux.

Un seul mot sépare les deux images.

### 3. Un conteneur `robuste`, arrêté, code zéro

Lancez un conteneur nommé `robuste` depuis votre image corrigée, puis
arrêtez-le. Son code de sortie doit être `0`.

Un code non nul sur un arrêt demandé est exactement ce qui faussait les
alertes : il fait croire à un incident, et un redémarrage automatique peut s'y
déclencher pour rien.

### 4. Ses journaux portent la preuve du signal

`sigterm-recu`, écrit par l'application elle-même quand elle le reçoit.

Pourquoi ce contrôle en plus du code de sortie : un zéro pourrait venir d'une
application qui s'est terminée pour une autre raison. Cette ligne ne laisse pas
cette place au doute.

Les journaux doivent **aussi** porter `preparation-faite`, pour la raison dite
au point 2.

## Ce qui est noté

L'**état du moteur** : qui est le processus numéro un, les codes de sortie, et
la trace que l'application écrit elle-même quand elle reçoit le signal.

Pas la façon de corriger. Plusieurs la permettent, et toutes comptent du moment
que le signal atteint un processus capable d'en faire quelque chose.

### Ce qui n'est pas noté

La façon de corriger. Rendre l'application PID 1 depuis le script d'entrée,
l'invoquer directement depuis l'`ENTRYPOINT`, ou passer par un init qui
réexpédie les signaux aboutissent au même état. Les trois comptent.
