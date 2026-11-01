# Scénario

L'exploitation a besoin d'un contexte nommé pour le moteur de préproduction
sur la VM distincte `docker-client.lab`. Une identité SSH dédiée est prête sur
`docker.lab` ; l'alias `dsoxlab-ssh-target` désigne la VM distante.
Ne changez pas le contexte par défaut.

## Mission

Le contexte nommé joint le vrai démon de la seconde VM par SSH ; le contexte
par défaut reste sélectionné. Une clé distincte non autorisée doit être refusée
par ce même service SSH joignable. Aucune API Docker TCP non authentifiée n'est nécessaire.
