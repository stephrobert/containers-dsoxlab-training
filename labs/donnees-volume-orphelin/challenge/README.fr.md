# Orphelin ne signifie pas jetable

## La situation

Sur `docker.lab`, deux volumes ne sont attachés à aucun conteneur.
`dsoxlab-donnees-volume-orphelin-data` contient un reçu à récupérer.
`dsoxlab-donnees-volume-orphelin-stale` est vide et ne sert plus. Le `worker` du
projet `dsoxlab-donnees-volume-orphelin` tourne sans ses données. Le projet se
trouve dans `/opt/dsoxlab-donnees-volume-orphelin`.

## Mission

1. `worker` monte le volume d'origine `dsoxlab-donnees-volume-orphelin-data` en
   lecture seule, à `/data`. Ce volume garde ses deux étiquettes, celle du lab et
   celle du projet Compose.
2. `/data/receipt.txt` est identique au fichier `expected.txt` fourni.
3. `dsoxlab-donnees-volume-orphelin-stale`, et lui seul, est retiré. Vérifiez ses
   deux étiquettes avant.

Gardez le projet et l'étiquette `dsoxlab.lab=donnees-volume-orphelin`. Ne recréez
pas le volume à garder, et n'utilisez ni `volume prune` ni `system prune`.
