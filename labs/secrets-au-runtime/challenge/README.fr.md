# Fournir un jeton sans le publier

## La situation

Sur `docker.lab`, le `worker` du projet `dsoxlab-secrets-au-runtime` attend un
jeton dans `/run/secrets/token`. Dès qu'il peut le lire, il écrit son empreinte
SHA-256 dans `/run/result`, sans jamais afficher le jeton. La valeur, tirée au
hasard, est dans `secrets/token`, sous `/opt/dsoxlab-secrets-au-runtime`.

## Mission

1. `worker` reçoit `secrets/token` en lecture seule, à `/run/secrets/token`.
2. `/run/result` porte l'empreinte du jeton.
3. Une écriture dans le fichier monté est refusée, et la source ne change pas :
   un fichier ordinaire, en mode 0600.
4. Le jeton n'apparaît ni dans `docker inspect`, ni dans les journaux, ni dans
   l'image ou son historique, ni dans le Dockerfile, ni dans le fichier Compose.

Gardez le projet, l'étiquette `dsoxlab.lab=secrets-au-runtime`, la commande
fournie, l'image épinglée et les limites de ressources. Ne collez le jeton nulle
part et ne le remplacez pas par un vrai identifiant.
