# Un budget YAML ne prouve pas son application

Docker sur `docker.lab` utilise cgroup v2. Alpine épinglée est déjà disponible.
Aucune charge ne tourne initialement.

## Mission

Écrivez `/opt/lab-compose-resources/compose.yaml`, projet `dsoxlab-ressources`.
Démarrez exactement un service `worker` avec la référence Alpine épinglée fournie
et `sleep infinity`, sans montages, capacités supplémentaires, privilèges
ni namespace cgroup hôte.

Appliquez ces limites dures :

- mémoire : exactement 128 Mio ;
- CPU : exactement un quota de 0,5 cœur, pas un poids CPU relatif ;
- processus : exactement 64.

Inspectez HostConfig de Docker et les contrôles effectifs `/sys/fs/cgroup/memory.max`,
`cpu.max` et `pids.max` dans le conteneur. Les budgets doivent survivre à la recréation
forcée sans `docker update` manuel, constructions ni téléchargements.

Le contrôle lance une boucle active bornée à trois secondes et exige une hausse
des compteurs de bridage du cgroup CPU. Il n'alloue pas de mémoire excessive,
ne crée pas de bombe de processus et ne mesure pas d'OOM : ce sont d'autres sujets.
Le nettoyage retire uniquement les ressources du projet et garde l'image de base.
Le même service doit rester opérationnel après la charge CPU, sans redémarrage
ni perte de son reçu applicatif frais. L'essai retire seulement ce reçu.
