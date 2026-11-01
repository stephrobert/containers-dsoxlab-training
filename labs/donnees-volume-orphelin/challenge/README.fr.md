# Cahier des charges

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-donnees-volume-orphelin`.

1. Gardez `worker` actif, projet `dsoxlab-donnees-volume-orphelin`,
   label `dsoxlab.lab=donnees-volume-orphelin`.
2. Montez le volume original `dsoxlab-donnees-volume-orphelin-data` en lecture
   seule à `/data`, en conservant ses deux labels de propriété.
3. `/data/receipt.txt` doit correspondre exactement à `expected.txt` fourni.
4. Supprimez seulement `dsoxlab-donnees-volume-orphelin-stale`, après
   vérification de ses labels de lab et de projet Compose.

Ne recréez pas le volume conservé et n'utilisez aucun prune global.
