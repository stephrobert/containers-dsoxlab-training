# Le conteneur est remplaçable, pas ses données

L'image `dsoxlab-compose-persist:app` est prête sur `docker.lab`. Sa commande
initialise `/data/value.txt` depuis `/seed/value.txt` seulement si le fichier
de données est absent, puis reste démarrée. Aucun conteneur ni volume applicatif
n'existe initialement.

## Mission

Écrivez `/opt/lab-compose-persist/compose.yaml`, projet `dsoxlab-persistance`.
Exécutez exactement un service `app` avec l'image et la commande fournies.
Déclarez un volume Compose nommé `data` et montez-le en écriture sur `/data`.
N'utilisez ni bind, volume anonyme, montage supplémentaire ni commande de remplacement.

La valeur initiale doit être visible dans `/data/value.txt`. Surtout, de nouvelles
écritures doivent survivre à la recréation forcée et au cycle `docker compose down`
puis `up`, avec le même volume. N'utilisez pas `down --volumes` en exploitation normale.
La recréation ne doit demander ni construction, téléchargement ni copie manuelle.

Les contrôles remplacent temporairement les données par des valeurs aléatoires,
remplacent le conteneur et restaurent le contenu original. Reproduire simplement
la donnée initiale dans chaque nouveau conteneur ne prouve pas la persistance.
Le nettoyage supprime volontairement le volume de ce projet après l'exercice.
