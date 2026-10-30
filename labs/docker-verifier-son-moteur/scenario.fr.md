# « Docker est installé », et pourtant rien ne marche

## La situation

Vous reprenez une machine de build qu'un collègue a préparée avant de partir.
Son dernier message dit : « Docker est installé, tu peux lancer tes conteneurs. »

Le paquet est bien là. `docker` répond quand vous tapez son nom. Et pourtant
aucune de vos commandes n'aboutit : l'une parle de permission refusée, une
autre de démon injoignable, et vous n'arrivez pas à décider s'il manque un
droit, un service, ou les deux.

C'est la situation la plus banale qui suit une installation par paquet, et
c'est aussi celle où l'on perd le plus de temps : on relance l'installation,
on cherche un problème de réseau, on soupçonne l'image. Le paquet n'y est pour
rien. « Installé » et « utilisable » sont deux états différents, et le second
se vérifie sur plusieurs plans qui ne se réparent pas du même geste.

## L'objectif

Rendre ce moteur réellement utilisable, et le prouver autrement qu'en disant
« ça marche chez moi ».

Quatre choses sont vérifiées, et elles sont **indépendantes** :

1. le moteur répond ;
2. il repartira tout seul au prochain redémarrage de la machine ;
3. votre compte lui parle **sans** `sudo` ;
4. un conteneur a réellement été exécuté.

L'énoncé complet est aussi déposé sur la machine, dans `/opt/MISSION.md`.

L'image `lab-preuve:1.0` est déjà présente : aucun accès à un registre n'est
nécessaire, et rien dans cette mission ne demande de réinstaller le paquet.

## Ce qui est noté

L'**état du système**, jamais les commandes tapées. Le service, son activation
au démarrage, l'appartenance de votre compte au groupe qui ouvre le socket, et
la trace d'un conteneur ayant tourné. Deux apprenants qui arrivent au même
état par deux chemins différents ont tous les deux réussi.

Un point mérite d'être su d'avance, parce qu'il fait croire à un échec : les
groupes d'un compte sont lus **à la connexion**. Vous ajouter à un groupe ne
change rien à la session déjà ouverte, et il faut vous reconnecter pour que
votre shell en profite. Le contrôle, lui, regarde l'appartenance, pas votre
shell : le bon geste compte même si votre terminal courant l'ignore encore.
