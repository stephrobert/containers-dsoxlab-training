# Un démon sans root, qui n'attend que d'être démarré

## La situation

Sur `docker.lab`, un second moteur Docker est préparé pour le compte dédié
`dsoxlab-rootless`, à côté du moteur du système. Le compte, ses sous-identifiants,
son dossier de travail, son `linger` et le fichier de son service sont en place.
Il manque le dernier geste.

## Mission

**Démarrez le service utilisateur `dsoxlab-rootless.service` du compte
`dsoxlab-rootless`.** Ce n'est pas un service du système : le compte qui le porte
n'a pas de session ouverte, et son UID est dans
`/opt/dsoxlab-securite-rootless/state.json`.

Le moteur du système doit rester intact.

## Ce qui est noté

Huit contrôles. Ils fabriquent eux-mêmes le réseau, le volume et le serveur HTTP
dont ils ont besoin, puis les retirent : vous n'avez rien d'autre à créer.

1. Le service dédié est actif.
2. Son démon annonce le mode rootless.
3. Son processus appartient au compte dédié, et son UID n'est pas 0.
4. Son stockage d'images est distinct de celui du moteur du système.
5. Il crée son propre réseau et son propre volume nommé.
6. Une donnée nouvelle survit à deux recréations du conteneur.
7. Sa publication reste sur la boucle locale, sur un port non privilégié.
8. Un conteneur de son réseau joint le service, un conteneur sans réseau est
   refusé.
