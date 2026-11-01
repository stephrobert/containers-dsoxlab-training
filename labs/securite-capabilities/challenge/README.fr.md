# Cahier des charges

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-securite-capabilities`.

1. Gardez un service Compose `worker` actif, projet
   `dsoxlab-securite-capabilities`, label `dsoxlab.lab=securite-capabilities`.
2. Retirez ALL et ajoutez uniquement NET_BIND_SERVICE.
3. Le masque effectif de PID 1 doit porter exactement le bit 10.
4. Conservez `/proof`, appartenant à root : le changement vers UID 123 doit échouer.

Préservez l'image épinglée et les ressources bornées. Utilisez Compose v2 ou
`docker-compose` avec le nom explicite du projet. Aucune modification du démon.
