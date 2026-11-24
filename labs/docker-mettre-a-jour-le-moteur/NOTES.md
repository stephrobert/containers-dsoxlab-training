# docker-mettre-a-jour-le-moteur : monter le moteur sans que la passerelle s'en aperçoive

## Ce que ce lab éprouve

Que vous savez monter Docker Engine de 29.8.2 à 29.9.2 sur un hôte qui sert du
trafic, sans relancer un service et sans toucher à ses données. Ce qui est noté,
c'est la montée. Le retour arrière est enseigné par la leçon et n'est pas
demandé ici.

## Mesuré avant d'être écrit

Sur `docker.lab`, Debian 13, le 2026-11-09. Le moteur et ses cinq paquets
compagnons viennent du dépôt officiel de Docker.

| Fait | Valeur mesurée |
| --- | --- |
| versions proposées pour le moteur | 29.8.2, 29.9.0, 29.9.1, 29.9.2, 29.9.3 |
| candidat quand rien n'est nommé | 29.9.3, qui n'est pas la cible |
| paquets retenus par la base du catalogue | six : `docker-ce`, `docker-ce-cli`, `docker-ce-rootless-extras`, `containerd.io`, `docker-buildx-plugin`, `docker-compose-plugin` |
| redémarrage du démon, passerelle en `--restart unless-stopped`, sans `live-restore` | le conteneur est arrêté, puis relancé avec un nouveau processus |
| le même, `live-restore` lu avant la montée | même processus, même heure de démarrage, compteur de battements ininterrompu |

Les deux dernières lignes sont le lab. Sans `live-restore`, le moteur monte et la
passerelle redémarre, sans qu'aucun message le dise.

## Pourquoi trois mesures indépendantes d'un redémarrage

Le numéro de processus change, l'heure de démarrage change, et le compteur de
battements retombe à 1 : un redémarrage se voit dans les trois. Un contrôle qui ne
lirait que l'état du conteneur serait trompé par une politique de redémarrage qui
remet le conteneur en marche toute seule.

## Pourquoi deux contrôles ne comptent qu'une fois le moteur monté

La passerelle n'a pas été relancée et sa donnée est intacte : les deux sont vrais
**avant tout travail**, puisque le setup vient de les poser. Un contrôle vrai avant
le travail mesure l'état de départ, pas un savoir-faire. Ces deux contrôles
exigent donc d'abord que le moteur soit en 29.9.2, et le disent sinon.

## Pourquoi les options de journal se contrôlent avec le réglage

Écrire `{"live-restore": true}` par-dessus le fichier active le réglage et
efface les options de journal sans un mot. Les deux moitiés se jugent ensemble,
sur le fichier pour les options et sur le démon en marche pour le réglage.

## Ce que le lab n'exige pas

Les sauvegardes, la validation du fichier avant le rechargement, et le retour
arrière : l'état final ne les prouve pas, et un contrôle qui exigerait une trace
de ces gestes noterait des commandes.

## L'état de départ est la règle du dépôt

Le moteur est en 29.8.2 et `live-restore` est éteint, donc les trois premiers
contrôles sont faux avant tout travail. Le nettoyage rend au catalogue son propre
moteur, en 29.9.2 avec six paquets retenus, et retire le `daemon.json` que le lab
avait posé.
