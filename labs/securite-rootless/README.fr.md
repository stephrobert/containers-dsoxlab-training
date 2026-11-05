# securite-rootless

**Public :** apprenants.

Qualifier le démon non privilégié, son réseau et ses données persistantes.

## Ce que vous allez pratiquer

Démarrer un démon Docker sans privilèges : un service **utilisateur** porté par
un compte système sans session, ce qui demande de lui fournir son répertoire
d'exécution et son bus. C'est le seul geste du lab, et le seul que les
contrôles vous demandent.

Les contrôles fabriquent ensuite eux-mêmes un réseau, un volume et un service
HTTP sur ce moteur pour prouver qu'il fonctionne réellement. Vous n'avez rien
de tout cela à construire : sachez en revanche expliquer la correspondance des
UID, le stockage d'images distinct et les limites du réseau rootless, sans
confondre root dans le conteneur et root sur la VM.

## Limites de sécurité

Seuls les conteneurs, volumes et fichiers du lab sont modifiés. Les exercices système utilisent des comptes dédiés ou restaurent la configuration initiale du démon.

## Validation

Les tests inspectent l’état effectif sur `docker.lab` ; l’historique des commandes ou le contenu d’un fichier n’accorde aucun point. Les messages d’assertion sont bilingues.
