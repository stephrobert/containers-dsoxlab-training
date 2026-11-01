# Les secrets runtime sont des fichiers, pas des couches d'image

Les variables d'environnement peuvent apparaître dans `docker inspect`, les
environnements de processus, le debug et les rapports de crash. Arguments de
build et fichiers copiés peuvent persister dans l'historique ou les couches.
La livraison de fichiers au runtime évite ces canaux courants.

Sur un projet neutre `demo-mailer`, la section `secrets` de Compose déclare
une source privée ; le service accorde ce secret avec un nom `target` sous
`/run/secrets`. Compose local utilise généralement des bind mounts en lecture
seule. Ce n'est pas le magasin chiffré de Swarm : la source hôte doit rester
protégée et un administrateur Docker peut la lire.

La source fournie appartient à root en mode 0600 ; root dans le conteneur peut
la lire sans DAC_OVERRIDE. Ne journalisez jamais sa valeur. Une empreinte
prouve la consommation des bons octets sans les publier. Le contrôle garde
inspect et les logs bruts sur la VM et ne renvoie qu'un verdict de fuite. Il exige
aussi l'image de base immuable fournie, plutôt que d'inspecter des couches qui
pourraient contenir un secret copié.

Le moteur, Compose et Python 3 doivent déjà être disponibles.
Voir [le challenge](challenge/README.fr.md).
