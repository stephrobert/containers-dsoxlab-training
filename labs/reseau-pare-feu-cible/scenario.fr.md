# La route existe, mais la requête n'arrive pas

La topologie dédiée de `/opt/dsoxlab-reseau-pare-feu-cible` contient un client
autorisé, un client non autorisé, un routeur et un inventaire. Une vraie règle
de pare-feu bloque le flux métier. Localisez le saut fautif et corrigez ce seul
flux en conservant les exclusions du client non autorisé et du port debug.

Les commandes pare-feu appartiennent uniquement au namespace du routeur
conteneur. Ne modifiez ni pare-feu du poste ou de la VM, ni forwarding hôte,
ni API Docker. Voir [le contrat](challenge/README.fr.md) et la revue séparée.
