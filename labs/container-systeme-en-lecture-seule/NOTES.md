# Racine en lecture seule, runtime modifiable

`read_only` de Compose protège la racine du conteneur. Les montages distincts
ne deviennent pas automatiquement en lecture seule et ce n'est pas une
sauvegarde. Une application peut encore avoir besoin de PID files, fichiers
temporaires ou sockets.

Sur un projet neutre `demo-agent`, identifiez les chemins réellement modifiables
avant d'activer la racine en lecture seule. Un tmpfs borné peut fournir un
répertoire runtime : `/var/run:rw,noexec,nosuid,size=2m` est un exemple,
pas le contrat de ce challenge. Les données tmpfs disparaissent avec le conteneur
et comptent dans son cgroup mémoire. Noexec interdit l'exécution directe depuis
ce montage, pas la lecture d'un script par un interpréteur.

Comparez `HostConfig.ReadonlyRootfs`, type de montage, capacité `df` et vraie
tentative d'écriture. Une application silencieuse qui n'actualise plus ses
fichiers runtime n'est pas un succès.

Voir [le challenge](challenge/README.fr.md). Le moteur est préservé et aucun
système de fichiers hôte n'est remonté.
