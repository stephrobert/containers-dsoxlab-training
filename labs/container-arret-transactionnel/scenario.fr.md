# Un arrêt qui perd une commande

Le registre HTTP fourni accepte une écriture mais le déploiement l'interrompt
pendant l'arrêt. L'application est déjà implémentée. Réparez son lancement et
son arrêt dans `/opt/dsoxlab-container-arret-transactionnel`.

Prouvez réception du signal, fin de requête et durabilité métier après
recréation. Comparez un arrêt volontairement forcé d'une autre transaction en
vol, sans endommager les enregistrements déjà validés.
Exécutez ce même service sous UID/GID 10001 avec une racine en lecture seule.
Seul `/data` porte les données applicatives inscriptibles ; un autre UID
applicatif doit subir un refus d'accès aux transactions. Gardez ces restrictions
pendant la reprise.

Utilisez seulement les ressources labellisées de ce lab. Le contrat numéroté
est dans [challenge/README.fr.md](challenge/README.fr.md); la revue est séparée.
