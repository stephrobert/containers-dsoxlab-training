# docker-contexte-ssh

**Public :** apprenants.

Créer et utiliser un contexte nommé pour le moteur de la VM distincte `docker-client.lab`.

## Ce que vous allez pratiquer

Le contexte nommé joint le démon distant par SSH ; le contexte par défaut
reste sélectionné. Comparez les identifiants réels des moteurs et vérifiez
qu'une clé non autorisée est refusée par le service SSH distant joignable.

## Limites de sécurité

Seuls les conteneurs, volumes et fichiers du lab sont modifiés. Les exercices système utilisent des comptes dédiés ou restaurent la configuration initiale du démon. La pression disque est simulée par un volume borné de 16 Mio et ne remplit jamais le système de fichiers de l’hôte.

## Validation

Les tests inspectent l’état effectif sur `docker.lab` ; l’historique des commandes ou le contenu d’un fichier n’accorde aucun point. Les messages d’assertion sont bilingues.
