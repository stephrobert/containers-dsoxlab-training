# Cahier des charges

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-securite-no-new-privileges`.

1. Gardez `worker` actif dans le projet `dsoxlab-securite-no-new-privileges`,
   avec le label `dsoxlab.lab=securite-no-new-privileges`.
2. Activez no-new-privileges au runtime ; PID 1 doit annoncer `NoNewPrivs: 1`.
3. Conservez `/usr/local/bin/identity`, propriétaire UID 0, mode 4755.
4. Son exécution sous UID/GID 1000 doit afficher `1000:1000`, pas `1000:0`.

Ne remplacez pas le binaire, ne changez pas son mode ni la politique setuid hôte.
Préservez les réglages de ressources bornées.
