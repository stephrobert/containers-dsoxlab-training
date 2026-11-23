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

## Énoncé

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-docker-mettre-a-jour-le-moteur`
(l'énoncé est aussi dans `MISSION.md`). L'hôte porte Docker 29.8.2 et une
passerelle, `passerelle-sms`, dont les données vivent dans `volume-passerelle`.

Amenez le moteur en **29.9.2** et laissez l'hôte dans l'état ci-dessous. Chaque
exigence se lit sur l'état final, et les trois premières sont fausses avant tout
travail.

### 1. Le moteur est en 29.9.2, exactement

Le serveur, le client et le paquet `docker-ce` sont en 29.9.2. Le dépôt propose
un candidat plus récent, qui n'est pas la cible.

### 2. Les paquets du moteur restent retenus, dans la nouvelle version

`docker-ce`, `docker-ce-cli` et `docker-ce-rootless-extras` sont en 29.9.2, et
les six paquets Docker sont retenus, comme ils l'étaient. Les trois autres
(`containerd.io` et les deux plugins) ne font pas partie de la montée.

### 3. `live-restore` est actif, et les options de journal sont toujours là

`/etc/docker/daemon.json` porte `"live-restore": true` **et** les options de
journal qu'il avait au départ. Le démon en marche annonce le réglage comme actif :
un fichier que le démon n'a pas lu ne protège aucun conteneur.

### 4. La passerelle n'a jamais été relancée

Même processus, même heure de démarrage, et un compteur de battements qui monte
de un en un, sans coupure, depuis la première ligne de son fichier. Ce contrôle
ne se juge qu'une fois le moteur en 29.9.2 : avant, rien n'a touché la
passerelle.

### 5. La donnée est intacte

La liste d'abonnés du volume est identique à celle du départ, octet pour octet.
Jugée comme le contrôle précédent, une fois le moteur en 29.9.2.

### Ce qui n'est pas noté

Le retour vers 29.8.2 : la leçon l'enseigne, ce lab ne le demande pas. Ni les
sauvegardes que vous faites, ni les commandes que vous tapez : seul l'état final
compte.

Ne supprimez pas `passerelle-sms` ni son volume, et ne les redémarrez pas : les
contrôles les comparent à leur état de départ.
