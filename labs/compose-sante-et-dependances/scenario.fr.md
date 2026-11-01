# Démarré ne signifie pas disponible

Les images `dsoxlab-compose-health:backend` et `:app` sont prêtes, sans conteneurs actifs.
Backend sert immédiatement `/live` sur 8080, puis expose `/ready` après quatre
secondes. App demande `http://backend:8080/ready` une fois au démarrage, sans reprise.
Elle quitte en échec ou inscrit `ready` dans `/tmp/observed` et reste démarrée.

## Mission

Écrivez `/opt/lab-compose-health/compose.yaml`, projet `dsoxlab-health`.
Exécutez exactement `backend` et `app` avec images et commandes fournies, sans montages,
ports publiés, politiques de redémarrage ni attentes supplémentaires au démarrage.
Donnez à backend une sonde sur `/ready`, pas `/live` ni la présence du processus.
Utilisez un intervalle court et une grâce de démarrage suffisante pour une
initialisation de huit secondes ; la perte de disponibilité doit devenir
unhealthy sous 30 secondes. Conditionnez app avec `depends_on` et `service_healthy`.

Le contrôle retire `/ready` pendant que le processus HTTP et `/live` répondent,
puis le restaure. Il démarre aussi des projets isolés avec un backend plus lent
et un backend jamais disponible. App doit attendre dans le premier cas et ne
jamais démarrer dans le second. Ne fixez pas de noms globaux de conteneur ou réseau.

La dépendance de santé Compose conditionne le démarrage initial ; elle n'arrête
ni ne redémarre automatiquement un dépendant déjà actif quand backend devient unhealthy.
