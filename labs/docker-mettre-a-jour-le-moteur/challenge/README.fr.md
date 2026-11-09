# Énoncé

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-docker-mettre-a-jour-le-moteur`
(l'énoncé est aussi dans `MISSION.md`). L'hôte porte Docker 29.8.2 et une
passerelle, `passerelle-sms`, dont les données vivent dans `volume-passerelle`.

Amenez le moteur en **29.9.2** et laissez l'hôte dans l'état ci-dessous. Chaque
exigence se lit sur l'état final, et les trois premières sont fausses avant tout
travail.

## 1. Le moteur est en 29.9.2, exactement

Le serveur, le client et le paquet `docker-ce` sont en 29.9.2. Le dépôt propose
un candidat plus récent, qui n'est pas la cible.

## 2. Les paquets du moteur restent retenus, dans la nouvelle version

`docker-ce`, `docker-ce-cli` et `docker-ce-rootless-extras` sont en 29.9.2, et
les six paquets Docker sont retenus, comme ils l'étaient. Les trois autres
(`containerd.io` et les deux plugins) ne font pas partie de la montée.

## 3. `live-restore` est actif, et les options de journal sont toujours là

`/etc/docker/daemon.json` porte `"live-restore": true` **et** les options de
journal qu'il avait au départ. Le démon en marche annonce le réglage comme actif :
un fichier que le démon n'a pas lu ne protège aucun conteneur.

## 4. La passerelle n'a jamais été relancée

Même processus, même heure de démarrage, et un compteur de battements qui monte
de un en un, sans coupure, depuis la première ligne de son fichier. Ce contrôle
ne se juge qu'une fois le moteur en 29.9.2 : avant, rien n'a touché la
passerelle.

## 5. La donnée est intacte

La liste d'abonnés du volume est identique à celle du départ, octet pour octet.
Jugée comme le contrôle précédent, une fois le moteur en 29.9.2.

## Ce qui n'est pas noté

Le retour vers 29.8.2 : la leçon l'enseigne, ce lab ne le demande pas. Ni les
sauvegardes que vous faites, ni les commandes que vous tapez : seul l'état final
compte.

Ne supprimez pas `passerelle-sms` ni son volume, et ne les redémarrez pas : les
contrôles les comparent à leur état de départ.
