# Monter le moteur, sans que la passerelle s'en aperçoive

## La situation

Une passerelle SMS tourne sur cet hôte depuis des semaines. Elle écrit un
battement par seconde dans un volume, à côté de la liste d'abonnés qu'elle
sert, et elle revient toute seule si son conteneur s'arrête.

Le moteur qui la porte est Docker 29.8.2, installé depuis le dépôt officiel,
ses paquets retenus pour que rien ne les déplace par accident. La fenêtre de
maintenance est cette nuit, et la décision est prise : **29.9.2**, aucune autre
version.

Le dépôt propose maintenant plus récent que 29.9.2. Personne ne veut de celle-là
cette nuit.

L'équipe pose une condition. La passerelle ne doit pas redémarrer, pas une
seconde, et la liste d'abonnés doit ressortir exactement comme elle est entrée.
Redémarrer le démon fait partie de toute mise à jour du moteur, et un conteneur
qui revient après un redémarrage du démon est un conteneur qu'on a d'abord
arrêté.

## L'objectif

L'énoncé est déposé dans
`/opt/dsoxlab-docker-mettre-a-jour-le-moteur/MISSION.md`. Le conteneur de la
passerelle est `passerelle-sms`, son volume `volume-passerelle`.

Amenez le moteur en **29.9.2 exactement**, et laissez l'hôte dans cet état :

```text
moteur         Docker 29.9.2, serveur et client, les paquets du moteur dans cette version
paquets        les six paquets Docker retenus, comme avant
live-restore   actif, le démon l'ayant lu, les options de journal de la
               configuration d'origine toujours là
passerelle     jamais relancée : même processus, même heure de démarrage,
               battements ininterrompus
donnée         la liste d'abonnés identique, octet pour octet
```

## Ce que vous trouverez

`/etc/docker/daemon.json` existe déjà et porte la rotation des journaux de cet
hôte : c'est une configuration qui appartient à cet hôte, et elle doit y être
encore après.

Le moteur est retenu par `apt-mark hold` : `apt-get` refuse de changer un paquet
retenu, et il le fait exprès.

## Ce qui est noté

L'**état final** de l'hôte. La façon d'y arriver est la vôtre : les contrôles
lisent le moteur, ses paquets, sa configuration et la passerelle, jamais les
commandes que vous avez tapées.

Ce qui n'est **pas** noté, c'est le retour arrière. Revenir à la version
précédente est enseigné par la leçon, et n'est pas demandé ici.

Aucun contrôle ne laisse de trace sur l'hôte : le nettoyage rend au catalogue sa
propre version du moteur.
