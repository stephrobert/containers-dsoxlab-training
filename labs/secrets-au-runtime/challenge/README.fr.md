# Fournir un secret sans le publier

Un jeton pédagogique aléatoire est conservé dans `secrets/token`, privé.
Le worker n'y a pas accès. Sa commande fournie écrit seulement une empreinte
SHA-256 dans `/run/result` lorsque le secret devient lisible ; elle n'affiche
jamais le jeton.

Dans `/opt/dsoxlab-secrets-au-runtime`, fournissez le jeton comme fichier
runtime en lecture seule à `/run/secrets/token` dans `worker`, projet
`dsoxlab-secrets-au-runtime`. Gardez la source privée et l'application fournie.

Ne collez jamais le jeton dans une commande, une variable d'environnement,
Compose, une image ni des logs. Ne le remplacez pas par un vrai identifiant.
Cleanup supprime ce jeton jetable sans promettre un effacement cryptographique.

## Cahier des charges

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
