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
