# Orphelin ne signifie pas jetable

Deux volumes appartiennent exclusivement à ce lab.
`dsoxlab-donnees-volume-orphelin-data` contient un reçu original à récupérer.
`dsoxlab-donnees-volume-orphelin-stale`, vide, est jetable. Aucun n'est attaché
au worker initial.

Dans `/opt/dsoxlab-donnees-volume-orphelin`, reconnectez les données originales
en lecture seule à `/data` dans `worker`, projet
`dsoxlab-donnees-volume-orphelin`. Conservez le reçu et supprimez seulement le
volume stale du lab.

Vérifiez les deux labels de propriété avant suppression. Ni volume prune,
ni system prune, ni suppression d'un volume sans label ou sans rapport.

## Cahier des charges

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-donnees-volume-orphelin`.

1. Gardez `worker` actif, projet `dsoxlab-donnees-volume-orphelin`,
   label `dsoxlab.lab=donnees-volume-orphelin`.
2. Montez le volume original `dsoxlab-donnees-volume-orphelin-data` en lecture
   seule à `/data`, en conservant ses deux labels de propriété.
3. `/data/receipt.txt` doit correspondre exactement à `expected.txt` fourni.
4. Supprimez seulement `dsoxlab-donnees-volume-orphelin-stale`, après
   vérification de ses labels de lab et de projet Compose.

Ne recréez pas le volume conservé et n'utilisez aucun prune global.
