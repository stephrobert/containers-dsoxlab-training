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

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable. Docker y est **installé**, et il n'est
pas utilisable. Trois choses ont été défaites, et elles se réparent par trois
gestes différents.

L'image `lab-preuve:1.0` est déjà sur la machine : aucun accès à un registre
n'est nécessaire. Rien ici ne demande de réinstaller le paquet.

### 1. Le moteur répond

Le démon doit tourner. Pas le client : le client répond déjà, et c'est ce qui
rend la panne trompeuse.

Le contrôle interroge le moteur lui-même plutôt que l'unité systemd. Un service
annoncé actif dont le démon refuse les connexions dirait « réparé » sans que
rien ne le soit.

### 2. Il repartira au prochain redémarrage

Démarrer un service et l'activer au démarrage sont **deux gestes distincts**.
Celui qui n'en fait qu'un a une machine qui marche aujourd'hui et qui ne
marchera plus lundi.

Sur Debian, deux unités peuvent porter cette relance : le service, et le socket
qui le lance à la première connexion. **L'une des deux activée suffit** :
exiger les deux imposerait un chemin, et plusieurs sont défendables.

### 3. Votre compte parle au moteur sans `sudo`

L'accès au socket du moteur est une question d'appartenance à un groupe. Tant
que votre compte n'y est pas, chaque commande exige `sudo`, ce qui n'est pas
une façon de travailler.

**Le piège, et il attrape tout le monde une fois** : les groupes sont lus à la
connexion. Après vous être ajouté, votre session courante ne le sait pas
encore, et la commande échoue toujours. Ce n'est pas que le geste a raté, c'est
qu'il ne s'applique pas à une session déjà ouverte. Reconnectez-vous pour le
constater. Le contrôle, lui, regarde l'appartenance.

Attention à ne **pas remplacer** vos autres groupes en ajoutant celui-là : un
contrôle vérifie que le compte garde `sudo`, parce qu'un compte qui l'a perdu
ne peut plus rien administrer, et que c'est une erreur fréquente de la commande
qui sert ici.

### 4. Un conteneur a réellement été exécuté

Un démon peut répondre et être incapable de lancer quoi que ce soit : pilote de
stockage cassé, cgroups absents, image illisible. Seule une exécution le
prouve.

Lancez un conteneur depuis `lab-preuve:1.0` et **laissez-le là** : c'est la
preuve. Son état de sortie n'a pas d'importance, et cette image s'arrête d'elle
même aussitôt. Le contrôle cherche un conteneur, vivant ou terminé, issu de
cette image.

### Ce qui n'est pas noté

La commande que vous avez tapée. Chacun de ces quatre états s'atteint de
plusieurs façons, et toutes comptent pareil.
