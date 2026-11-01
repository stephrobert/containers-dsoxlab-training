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
