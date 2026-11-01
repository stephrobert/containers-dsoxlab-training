# docker-contexte-ssh

**Public :** apprenants.

Create and use a named context for the prepared loopback SSH daemon.

## Ce que vous allez pratiquer

Le contexte nommé joint le démon du lab par SSH ; le contexte par défaut reste sélectionné.

## Limites de sécurité

Seuls les conteneurs, volumes et fichiers du lab sont modifiés. Les exercices système utilisent des comptes dédiés ou restaurent la configuration initiale du démon. La pression disque est simulée par un volume borné de 16 Mio et ne remplit jamais le système de fichiers de l’hôte.

## Validation

Les tests inspectent l’état effectif sur `docker.lab` ; l’historique des commandes ou le contenu d’un fichier n’accorde aucun point. Les messages d’assertion sont bilingues.
