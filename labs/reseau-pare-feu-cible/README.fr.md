# Diagnostiquer un saut à la fois

[English](README.md) | [Énoncé](challenge/README.fr.md)

Distinguez routage, services à l'écoute et règles de forwarding. Dans une
topologie neutre limitée aux conteneurs, inspectez la route sélectionnée par
le client et les règles du namespace réseau propre au routeur :

```sh
docker exec tutorial-edge-client ip route get 192.0.2.10
docker exec tutorial-edge-router nft -a list ruleset
```

Ces noms et adresses ne donnent pas la correction du lab. Un endpoint de
contrôle du routeur accessible ne prouve pas le forwarding. Une sonde du
routeur vers le serveur établit le deuxième saut; la requête métier complète
traverse FORWARD. Lisez les compteurs avant et après des sondes fraîches,
y compris les chemins refusés.

Refus par défaut, retours established et correspondances étroites sur
source/destination/port se complètent. Retirer une table entière n'est pas
une correction ciblée. Gardez le filtrage dans le routeur; aucune commande
globale de pare-feu ou de sysctl hôte n'appartient à cet exercice.

Seule NET_ADMIN dans les namespaces des conteneurs posant les routes est
ajoutée. Pas de conteneur privilégié, réseau/PID/IPC hôte ou socket API.
Les outils sont installés par le Dockerfile épinglé du lab, pas sur le poste.
Le setup refuse les sous-réseaux dédiés s'ils chevauchent un réseau préexistant.

Les bridges ne sont pas déclarés `internal` : l'isolation Docker côté hôte
peut refuser un paquet destiné à l'autre sous-réseau avant son arrivée au
routeur conteneur. Aucune règle hôte n'est modifiée pour contourner ce comportement.
Routes explicites et refus par défaut du routeur définissent les chemins du lab.

Ancre source : guide local `docker/network.mdx`, `Dépannage réseau Docker`.
Le test vérifie à nouveau chemins autorisés et refusés après recréation.

## Validation auteur

Contraintes locales : `python3 -m unittest discover -s labs/reseau-pare-feu-cible/author_tests -v`.
Protocole VM : `LAB_HOME=$PWD python3 scripts/valider-labs.py --double-passage --lab reseau-pare-feu-cible`.
Sur `docker.lab`, le 2026-11-01 : zéro/plein/zéro/plein, 145 secondes pour le
protocole complet, état Docker restauré. Sauts HTTP et incréments des compteurs
de refus ont réellement été éprouvés, pas seulement le YAML. Revue humaine séparée.
