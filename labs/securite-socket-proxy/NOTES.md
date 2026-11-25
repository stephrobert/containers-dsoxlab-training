# securite-socket-proxy

**Public :** apprenants.

Limit the loopback proxy to two read-only API endpoints.

## Ce que vous allez pratiquer

GET /_ping et GET /version réussissent ; les autres chemins et méthodes modifiantes sont refusés.

## Limites de sécurité

Seuls les conteneurs, volumes et fichiers du lab sont modifiés. Les exercices système utilisent des comptes dédiés ou restaurent la configuration initiale du démon.

## Validation

Les tests inspectent l’état effectif sur `docker.lab` ; l’historique des commandes ou le contenu d’un fichier n’accorde aucun point. Les messages d’assertion sont bilingues.
