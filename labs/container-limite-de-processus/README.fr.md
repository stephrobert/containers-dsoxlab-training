# Le contrôleur pids

Le contrôleur pids des cgroups compte les tâches, y compris les threads.
`pids_limit` de Compose devient `HostConfig.PidsLimit` dans Docker et
`pids.max` dans le noyau. `ulimit -u` est un autre mécanisme, par utilisateur.

Sur un projet neutre `demo-indexer`, comparez `pids.current`, `pids.max` et
`pids.events` dans `/sys/fs/cgroup`, sur un hôte cgroup v2. Le compteur `max`
augmente lorsqu'une création est refusée. Les tâches existantes ne sont pas
tuées simplement parce qu'une nouvelle création dépasserait le plafond.

Prévoyez de la place pour PID 1, les auxiliaires et les sessions exec de
diagnostic. Un plafond qui empêche tout diagnostic est difficile à exploiter.
Testez seulement une rafale finie d'enfants éphémères, jamais une fork bomb.

L'exercice exige cgroup v2 avec le contrôleur pids. Le contrôle dure environ
cinq secondes une fois la configuration correcte. Voir
[le challenge](challenge/README.fr.md).
