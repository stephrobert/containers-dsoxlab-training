# Signaux, drainage et transactions durables

[English](README.md) | [Énoncé](challenge/README.fr.md)

Docker envoie son signal d'arrêt au premier processus du conteneur. Un lanceur
qui crée un enfant et attend sa fin ne transmet pas forcément ce signal.
Inspectez l'arbre des processus, pas seulement la syntaxe du Dockerfile :

```sh
docker top tutorial-payments
docker inspect tutorial-payments --format '{{json .Config.Entrypoint}}'
docker logs tutorial-payments
```

Ces exemples sont neutres et ne désignent pas des ressources de ce lab.
Un service gracieux refuse les nouveaux travaux, termine les requêtes
admises, valide sa transaction et se ferme avant le délai d'arrêt. Augmenter
le délai seul ne transmet pas le signal au bon processus.

SQLite distingue une écriture non validée d'un état durable validé. Tuer le
processus pendant une transaction doit annuler celle-ci, pas effacer les
données antérieures. Interrogez le domaine en HTTP après recréation avec le
même stockage; un message de log n'est pas une preuve de durabilité.

Utilisez une barrière observable avant l'arrêt. Un sommeil fixe ne prouve
pas que la requête a atteint sa transaction. La fixture fournit `/inflight`
et `/release`, avec un délai d'échec de 12 secondes. L'écriture est libérée
par la réception du signal, pas par un simple sommeil.

Ancre source : guide local `docker/execution-depannage.mdx`, titre
`Stop vs Kill : quelle différence ?`, lié dans `lab.yaml`.
Le budget externe de 110 secondes est celui du test, pas un SLA de formation.

## Validation auteur

Fixtures locales : `python3 -m unittest discover -s labs/container-arret-transactionnel/author_tests -v`.
Protocole VM : `LAB_HOME=$PWD python3 scripts/valider-labs.py --double-passage --lab container-arret-transactionnel`.
Sur `docker.lab`, le 2026-11-01 : zéro/plein/zéro/plein, 76 secondes pour le
protocole complet, état Docker restauré. La revue humaine reste séparée.
