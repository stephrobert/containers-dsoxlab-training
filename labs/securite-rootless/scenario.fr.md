# Scénario

Un second moteur Docker est préparé sur `docker.lab` pour le compte dédié
`dsoxlab-rootless`. Le démon rootful du système doit rester intact.

Tout est déjà en place : le compte, sa plage de sous-identifiants, son volume
de travail, son lingering et le fichier d'unité de son service. La préparation
s'arrête volontairement avant le dernier geste, et c'est lui qui vous revient.

## Mission

**Démarrez le service utilisateur `dsoxlab-rootless.service` du compte dédié.**
C'est le seul geste attendu, et c'est le geste difficile du rootless.

Le démon n'est pas un service système avec `User=` : c'est un service
**utilisateur**, et le compte qui le porte est un compte système sans session
ouverte. `systemctl --user` échoue donc tant qu'il ne trouve ni son répertoire
d'exécution ni son bus. Lisez l'UID dans
`/opt/dsoxlab-securite-rootless/state.json`, puis lancez `systemctl --user`
sous le compte `dsoxlab-rootless` avec `XDG_RUNTIME_DIR=/run/user/<uid>` et
`DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/<uid>/bus`.

## Ce que les contrôles prouvent, et que vous n'avez pas à construire

Les contrôles ne se contentent pas de demander son état au démon : ils
**fabriquent eux-mêmes** un réseau, un volume nommé, un serveur HTTP et deux
pairs sur ce moteur, puis jugent ce qu'il en fait. Vous n'avez aucun de ces
objets à créer, et le `check` ne vous en demandera pas.

Ce qu'ils établissent à partir de votre seul geste :

- le service dédié est actif, et le processus réel appartient au compte non
  privilégié, pas à root ;
- le démon annonce le mode rootless ;
- son stockage d'images est **distinct** de celui du moteur rootful, prouvé
  avant tout chargement : l'image épinglée de la VM lui est inconnue ;
- il crée son propre réseau et son propre volume nommé ;
- une donnée nouvelle survit à **deux** recréations du conteneur ;
- sa publication reste sur la boucle locale, sur un port non privilégié ;
- un pair de son réseau joint le service, et un pair sans réseau est refusé.

## Pour aller plus loin

Sachez expliquer la correspondance des UID, le stockage d'images distinct et
les limites du réseau rootless, sans confondre root dans le conteneur et root
sur la VM. Ce lab ne qualifie ni les ports privilégiés natifs, ni la haute
disponibilité.
