# Récupérer les volumes orphelins

Un volume survit au conteneur. `dangling=true` signifie qu'aucun conteneur ne
le référence, pas que les données sont sans valeur. Avant toute suppression,
inspectez labels, références de montage et contrat de conservation.

Sur un projet jetable neutre `demo-ledger`, un volume Compose `external: true`
avec un `name` explicite réutilise un volume existant au lieu de créer un
remplacement préfixé par le projet. Le service peut le monter en lecture seule
si la récupération ne nécessite pas d'écriture. Comparez son `Name` dans
inspect avec le volume original.

Les labels prouvent la propriété, pas la valeur métier. Comparez les données
avec un reçu ou une empreinte indépendante avant de conclure au succès.
Un prune global n'est jamais un diagnostic.

Le lab crée seulement de petits volumes uniques portant les labels de projet
et de lab. Cleanup supprime seulement ces ressources doublement labellisées.
Voir [le challenge](challenge/README.fr.md).
