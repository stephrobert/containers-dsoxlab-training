# ENOSPC dans un système de fichiers borné

`/sandbox` du worker est un tmpfs de 16 Mio, pas une partition hôte.
Un remplissage fini a consommé la capacité disponible. `/sandbox/keep.txt`
est utile ; `/sandbox/fill.bin` est jetable.

Dans `/opt/dsoxlab-troubleshoot-disque-plein`, récupérez de l'espace modifiable
dans le `worker` existant, projet `dsoxlab-troubleshoot-disque-plein`, sans
perdre le reçu ni augmenter le plafond.

Ne recréez pas le conteneur pour effacer ses données, ne redimensionnez pas le
sandbox, ne remplissez aucun chemin hôte et n'utilisez pas prune global.
Le contrôle écrit au plus 1 Mio dans le sandbox vérifié, puis retire sa sonde.
