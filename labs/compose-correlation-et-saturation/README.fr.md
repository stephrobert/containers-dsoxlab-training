# La corrélation n'est pas le volume de logs

[English](README.md) | [Énoncé](challenge/README.fr.md)

Dans un service d'achat neutre, un identifiant frais relie entrée, calcul aval
et réponse métier. Les traces JSON doivent conserver une liste autorisée de
champs utiles, jamais une copie des en-têtes de requête.

```sh
docker compose -p tutorial-shop logs --no-color
docker exec tutorial-shop-calculator cat /sys/fs/cgroup/cpu.max
docker exec tutorial-shop-calculator cat /sys/fs/cgroup/cpu.stat
```

Ces noms ne sont pas installés par ce challenge. Un quota CPU diffère d'un
poids relatif : `cpu.max` porte le budget effectif. Comparez `usage_usec`,
`nr_throttled` et `throttled_usec` avant et après une charge métier bornée.
Les deltas, les résultats métier et l'identité du composant établissent
ensemble l'attribution; taille des logs et limite mémoire déclarée ne suffisent pas.

Les interrupteurs de déploiement fournis sont `CORRELATE` et `SAFE_LOGS`
(`"0"` ou `"1"`), pour chaque composant. Aucune programmation n'est requise.
`ROLE` choisit passerelle ou worker. `/quote?quantity=N` accepte 1 à 20
articles et retourne un total à 125 centimes par article, corrélé via
`X-Request-ID`. Le worker consomme 0,12 seconde de CPU du thread par devis.

Concurrence et nombre de requêtes doivent être bornés. Le test emploie 16
identifiants frais, quatre clients, un worker à un quart de CPU et une
passerelle à un CPU. Deltas positifs et au moins 0,10 seconde CPU par requête
distinguent le calcul du démarrage; le CPU worker doit dépasser deux fois
celui de la passerelle. Ce sont des budgets de test, pas des pourcentages
de performance inventés pour la formation.

Ancre source : guide local `orchestrateurs/docker-compose.mdx`,
`Configuration avancée`. L'explication humaine reste évaluée séparément.

## Validation auteur

Fixtures locales : `python3 -m unittest discover -s labs/compose-correlation-et-saturation/author_tests -v`.
Protocole VM : `LAB_HOME=$PWD python3 scripts/valider-labs.py --double-passage --lab compose-correlation-et-saturation`.
Sur `docker.lab`, le 2026-11-01 : zéro/plein/zéro/plein, 214 secondes pour le
protocole complet, état Docker restauré. Les sondes de disponibilité des deux
composants précèdent la charge; la recréation refuse un quota manuel non persisté.
