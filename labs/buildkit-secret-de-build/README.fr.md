# Un secret pendant le build, jamais dans son résultat

Le challenge fait récupérer un produit réel dans un dépôt privé local.
L'identité est tirée au setup et le dépôt refuse les mauvais identifiants.

Les contrôles lisent le produit et inspectent la configuration, l'historique
non tronqué et toutes les couches de `docker save`, y compris les fichiers
supprimés. Ils reconstruisent avec une identité et un produit neufs, puis
exigent un échec sans secret et avec un secret incorrect, sans cache des couches.
Une réponse fixe et un secret écrit en dur ne suffisent donc pas.

Le dépôt HTTP sert seulement le réseau isolé de la VM ; son TLS n'est pas
mesuré. Les essais restaurent son état et retirent leur propre constructeur.
Le secret fourni est purement pédagogique et n'est jamais versionné.

Mesuré sur ce banc le 2026-11-01 : le passage par `ARG` est refusé par
l'inspection des métadonnées ; `COPY` puis `rm` est refusé par l'inspection
de l'archive ; le montage de secret ne laisse aucune occurrence détectée.
Le cycle runtime donne 0/3 avant, 3/3 après, puis 0/3 après remise à zéro.
