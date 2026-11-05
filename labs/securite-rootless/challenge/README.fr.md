# Contrat fonctionnel : securite-rootless

## Ce que vous livrez

Un seul geste : **le service utilisateur `dsoxlab-rootless.service` du compte
dédié est actif**. Tout le reste est déjà posé par la préparation.

## Ce que les huit contrôles prouvent

Ils inspectent le démon réel sur `docker.lab`, et **fabriquent eux-mêmes** le
décor dont ils ont besoin. Vous n'avez ni réseau, ni volume, ni serveur HTTP à
créer.

1. le service dédié est actif ;
2. son démon annonce le mode rootless ;
3. le processus réel du service appartient au compte non privilégié, et son UID
   n'est pas 0 ;
4. son stockage d'images est distinct de celui du moteur rootful, prouvé avant
   tout chargement ;
5. il crée son propre réseau et son propre volume nommé ;
6. une donnée nouvelle survit à deux recréations du conteneur ;
7. sa publication reste sur la boucle locale, sur un port non privilégié ;
8. un pair de son réseau joint le service, et un pair sans réseau est refusé.

Les objets d'essai portent des noms uniques bornés et sont retirés, y compris
après une allocation partielle. L'état initial ne rapporte aucun point.
