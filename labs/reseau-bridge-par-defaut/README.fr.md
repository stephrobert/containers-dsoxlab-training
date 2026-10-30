# reseau-bridge-par-defaut : le réseau que personne ne choisit

## Ce que ce lab éprouve

Que le réseau par défaut relie les conteneurs entre eux et à l'hôte, et qu'il
ne leur donne **aucune résolution de noms**. C'est le réseau sur lequel on
tombe quand on ne dit rien, et ses limites ne se découvrent qu'en s'y cognant.

## La leçon a été mesurée avant d'être écrite

Sur `docker.lab`, le 2026-10-30, depuis un conteneur du réseau par défaut :

| Tentative | Résultat |
| --- | --- |
| connexion vers l'**adresse** de `arriere` | son jeton |
| connexion vers son **nom** | `nc: bad address 'arriere'` |
| `nslookup arriere` | expire, aucun serveur joignable |

Le lab suivant, `reseau-bridge-dedie`, crée un réseau et retrouve le DNS. **Le
contraste est la pédagogie** : affirmer qu'un réseau dédié « apporte le DNS »
ne vaut rien tant qu'on n'a pas vu l'autre s'en passer.

## Pourquoi `nc` et pas `ping`

ICMP dépend des capabilities du conteneur et de réglages du noyau de l'hôte. Un
lab réseau qui échouerait pour cette raison enseignerait la mauvaise leçon :
l'apprenant conclurait que le réseau ne marche pas, alors que seul ICMP est
filtré. Une connexion TCP prouve la même joignabilité et ne dépend de rien
d'autre.

## Pourquoi le jeton n'est pas dans les journaux

Une première version le faisait annoncer par `arriere` sur sa sortie standard.
`docker logs` le donnait alors **sans qu'aucun paquet ne traverse le réseau**,
et le lab se résolvait sans toucher à son sujet.

Il ne vit donc que dans la réponse TCP, et il est tiré au hasard à chaque
passage. Le trouver suppose d'avoir ouvert une connexion.

## Une honnêteté sur le quatrième contrôle

L'hôte aussi joint le bridge par défaut directement : le jeton peut donc être
obtenu depuis l'hôte plutôt que depuis `avant`.

Ce n'est pas une faille du lab, c'est un **fait du réseau par défaut**, que le
scénario énonce, et c'est même une information de sécurité utile. Le contrôle
note donc l'état atteint, `avant` porte le jeton, et non le chemin suivi, ce
qui est la règle du dépôt.

## Les trois questions, et ce que chacune fait acquérir

| Réponse | Où elle se lit | Ce qu'elle enseigne |
| --- | --- | --- |
| `adresse` | l'inspection du **conteneur** | sur ce réseau, c'est la seule façon de désigner un voisin |
| `passerelle` | l'inspection du **réseau** | un conteneur connaît son adresse, le réseau connaît sa passerelle |
| `interface` | l'hôte, par `ip addr` | la passerelle est portée par une interface réelle |

La deuxième et la troisième sont celles qu'on saute d'habitude, et ce sont
celles qui transforment le réseau des conteneurs en quelque chose de concret.

## Pourquoi l'interface est cherchée par son adresse, pas par son nom

Le pont du réseau par défaut s'appelle `docker0` sur une installation
ordinaire, et le moteur le nomme même dans les options du réseau. Mais ce nom
est **configurable** : un contrôle qui attendrait `docker0` en dur serait faux
sur une machine réglée autrement.

Le test cherche donc quelle interface de l'hôte porte l'adresse de la
passerelle. Même raison côté sous-réseau : aucune adresse n'est écrite dans les
tests, parce que `172.17.0.0/16` dépend de la machine.

## L'état de départ est cassé, et c'est la règle du dépôt

| Posé par le setup | État de départ | Geste attendu | Contrôle |
| --- | --- | --- | --- |
| `reponses.txt` | trois clés, trois valeurs **vides** | les renseigner | 1, 2 et 3 |
| le jeton, dans le processus de `arriere` | `avant` ne le porte pas | ouvrir une connexion | 4 |

Une tâche du setup **vérifie** cet état avant de rendre la main : les deux
conteneurs tournent, et `avant` ne porte pas déjà le jeton d'un passage
précédent.

## Ce que le lab n'exige pas

Un chemin. L'adresse se lit dans l'inspection du conteneur comme dans la sortie
complète du réseau ; l'interface par `ip addr` comme par les options que le
moteur déclare ; la connexion par `nc` comme par `wget` ou tout autre client.
