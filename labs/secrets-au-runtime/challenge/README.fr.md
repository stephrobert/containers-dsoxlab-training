# Cahier des charges

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-secrets-au-runtime`.

1. Gardez `worker` actif, projet `dsoxlab-secrets-au-runtime`,
   label `dsoxlab.lab=secrets-au-runtime`.
2. Montez `secrets/token` fourni en lecture seule à `/run/secrets/token`.
   La source hôte doit rester un fichier ordinaire en mode 0600.
3. Gardez l'application fournie produisant son SHA-256 dans `/run/result`.
4. Aucune valeur du jeton dans inspect, logs, métadonnées/historique d'image,
   Dockerfile ni configuration Compose.

Utilisez seulement le jeton pédagogique aléatoire. Ne l'affichez pas et ne le
placez pas dans l'environnement. Gardez l'image épinglée et les garde-fous.
