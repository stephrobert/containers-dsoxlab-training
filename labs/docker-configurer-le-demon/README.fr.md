# docker-configurer-le-demon

**Public :** apprenants.

Merge bounded json-file log defaults into the daemon configuration.

## Ce que vous allez pratiquer

Les nouveaux conteneurs utilisent les valeurs demandées ; le nettoyage restaure la configuration initiale du démon.

## Limites de sécurité

Seuls les conteneurs, volumes et fichiers du lab sont modifiés. Les exercices système utilisent des comptes dédiés ou restaurent la configuration initiale du démon. La pression disque est simulée par un volume borné de 16 Mio et ne remplit jamais le système de fichiers de l’hôte.

## Validation

Les tests inspectent l’état effectif sur `docker.lab` ; l’historique des commandes ou le contenu d’un fichier n’accorde aucun point. Les messages d’assertion sont bilingues.
