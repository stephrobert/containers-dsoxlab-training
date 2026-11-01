# securite-rootless

**Public :** apprenants.

Qualifier le démon non privilégié, son réseau et ses données persistantes.

## Ce que vous allez pratiquer

Le service dédié est actif et son propriétaire réel est non privilégié. Le
service HTTP rootless répond, son réseau refuse le pair extérieur et ses
données survivent à une recréation. L'émulation d'UID et le stockage d'images
distinct doivent être expliqués sans confondre root dans le conteneur et root
sur la VM.

## Limites de sécurité

Seuls les conteneurs, volumes et fichiers du lab sont modifiés. Les exercices système utilisent des comptes dédiés ou restaurent la configuration initiale du démon. La pression disque est simulée par un volume borné de 16 Mio et ne remplit jamais le système de fichiers de l’hôte.

## Validation

Les tests inspectent l’état effectif sur `docker.lab` ; l’historique des commandes ou le contenu d’un fichier n’accorde aucun point. Les messages d’assertion sont bilingues.
