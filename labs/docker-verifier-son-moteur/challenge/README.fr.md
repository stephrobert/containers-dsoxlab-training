# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable. Docker y est **installé**, et il n'est
pas utilisable. Trois choses ont été défaites, et elles se réparent par trois
gestes différents.

L'image `lab-preuve:1.0` est déjà sur la machine : aucun accès à un registre
n'est nécessaire. Rien ici ne demande de réinstaller le paquet.

## 1. Le moteur répond

Le démon doit tourner. Pas le client : le client répond déjà, et c'est ce qui
rend la panne trompeuse.

Le contrôle interroge le moteur lui-même plutôt que l'unité systemd. Un service
annoncé actif dont le démon refuse les connexions dirait « réparé » sans que
rien ne le soit.

## 2. Il repartira au prochain redémarrage

Démarrer un service et l'activer au démarrage sont **deux gestes distincts**.
Celui qui n'en fait qu'un a une machine qui marche aujourd'hui et qui ne
marchera plus lundi.

Sur Debian, deux unités peuvent porter cette relance : le service, et le socket
qui le lance à la première connexion. **L'une des deux activée suffit** :
exiger les deux imposerait un chemin, et plusieurs sont défendables.

## 3. Votre compte parle au moteur sans `sudo`

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

## 4. Un conteneur a réellement été exécuté

Un démon peut répondre et être incapable de lancer quoi que ce soit : pilote de
stockage cassé, cgroups absents, image illisible. Seule une exécution le
prouve.

Lancez un conteneur depuis `lab-preuve:1.0` et **laissez-le là** : c'est la
preuve. Son état de sortie n'a pas d'importance, et cette image s'arrête d'elle
même aussitôt. Le contrôle cherche un conteneur, vivant ou terminé, issu de
cette image.

## Ce qui n'est pas noté

La commande que vous avez tapée. Chacun de ces quatre états s'atteint de
plusieurs façons, et toutes comptent pareil.
