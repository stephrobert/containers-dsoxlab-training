# Une application à deux services reproductible

Le setup installe le paquet Compose v2 de Debian et construit deux petits
services depuis Alpine épinglée avec `busybox-extras`, car l'image de base
ne contient pas l'applet serveur HTTP. Aucun conteneur applicatif ni déclaration
Compose n'existe au départ.

Trois contrôles mesurent le projet démarré et la frontière des ports, la
communication API vers web par découverte de services et la recréation depuis
la déclaration. Les conteneurs doivent porter les labels de projet et service
Compose ; la recréation exige de nouveaux identifiants pour les deux conteneurs,
pas seulement un fichier de configuration.

L'essai de contenu vivant restaure la release de l'API. Le nettoyage ne retire
que les conteneurs, réseaux et volumes étiquetés du projet, puis les images
étiquetées du lab. Il ne purge pas globalement et ne touche pas aux autres projets.
