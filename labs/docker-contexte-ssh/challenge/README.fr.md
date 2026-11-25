# Un contexte pour la préproduction

## La situation

L'exploitation veut piloter le moteur de préproduction depuis `docker.lab`. Ce
moteur tourne sur une autre VM, `docker-client.lab`. L'accès SSH est déjà prêt :
le compte distant existe, une clé dédiée est posée, et l'alias SSH
`dsoxlab-ssh-target` mène à la seconde VM avec cette clé.

## Mission

Sur `docker.lab`, sous votre compte :

- créez un contexte Docker nommé `dsoxlab-maintenance`, dont l'adresse passe par
  l'alias SSH `dsoxlab-ssh-target` ;
- ce contexte répond, et c'est bien le moteur de `docker-client.lab` qui répond ;
- le contexte sélectionné au départ reste sélectionné.

N'ouvrez pas d'API Docker en TCP, et n'autorisez aucune autre clé sur la seconde
VM : celle de `/opt/dsoxlab-docker-contexte-ssh/unauthorized` doit rester refusée.

## Ce qui est noté

1. Le contexte `dsoxlab-maintenance` vise l'alias SSH.
2. Il rend l'identité du moteur de la seconde VM, différente de celle du moteur
   local, et la clé non autorisée est refusée par le service SSH.

Changer le contexte sélectionné fait échouer les deux contrôles.
