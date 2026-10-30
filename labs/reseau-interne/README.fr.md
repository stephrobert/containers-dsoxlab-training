# reseau-interne : deux isolations qui ne se ressemblent pas

## Ce que ce lab éprouve

Qu'il y a **deux** isolations, qu'on confond parce qu'on les appelle toutes les
deux « isoler » :

| Posture | Ce qu'elle donne | Pour quoi |
| --- | --- | --- |
| aucun réseau | ni interface, ni voisin, ni sortie | un traitement qui n'a besoin de personne |
| réseau interne | les membres se parlent par leur nom, et ne sortent pas | une base que seule son application doit joindre |

Les prendre l'une pour l'autre donne soit un service inutilisable, soit un
service exposé. Le lab fait obtenir les deux sur la même machine, pour que la
différence se voie au lieu d'être affirmée.

## Mesuré avant d'être écrit

Sur `docker.lab`, le 2026-10-30 :

| Posture | interfaces hors loopback | joint le témoin | voisin par son nom |
| --- | --- | --- | --- |
| réseau par défaut | 1 | oui | non |
| aucun réseau | 0 | non | sans objet |
| réseau interne | 1 | non | oui |

Et un détail qui dit tout du mécanisme : un conteneur d'un réseau interne n'a
**aucune route par défaut**. L'isolation n'est pas un filtrage posé devant lui,
c'est l'absence du chemin. La solution de référence le vérifie explicitement,
parce que c'est la façon la plus nette de comprendre ce qui se passe.

## Comment « sortir » est mesuré, et pourquoi pas contre Internet

Contre un témoin publié sur l'adresse routable de la machine.

Un lab qui dépendrait d'un accès sortant échouerait sur une machine isolée, et
son message parlerait d'isolation réussie alors qu'il n'y a pas de réseau du
tout : **il noterait l'inverse de ce qu'il mesure**. Le témoin local supprime
cette dépendance, et il rend la mesure reproductible.

## Pourquoi les deux premiers contrôles sont séparés

Le premier lit les interfaces **dans** le conteneur. Le second éprouve ce qu'il
**peut joindre**.

Ce n'est pas une redite : un conteneur peut avoir perdu son interface et garder
un partage de pile réseau avec un autre, auquel cas il joint encore. Lire la
configuration et éprouver le comportement sont deux mesures, et les séparer est
ce qui permet au message de nommer la bonne cause.

## Pourquoi le premier contrôle regarde l'effet et non le chemin

Il exige qu'aucune interface ne subsiste hors loopback, pas que le conteneur
déclare tel réseau.

Recréer avec l'option qui le prive de réseau est le geste franc, et c'est celui
que le lab enseigne. Détacher le conteneur de ses réseaux donne le même
résultat. Les deux comptent, parce que la règle du dépôt est de noter l'état,
jamais la commande.

## Le quatrième contrôle est indivisible

Il exige trois choses d'un coup : les deux conteneurs sur le réseau confiné, le
voisin joint **par son nom**, et aucune sortie.

Elles ne se séparent pas. Confiner sans que les membres se parlent donnerait un
service inutilisable ; les faire se parler sans les confiner ne serait qu'un
réseau dédié de plus, ce qui est le lab précédent. C'est la conjonction qui est
la compétence.

## Pourquoi le témoin est protégé

Les contrôles 2 et 4 seraient aussi vrais si `dehors` disparaissait : il n'y
aurait plus rien à ne pas joindre.

Un préalable vérifie donc qu'il tourne **et** qu'il répond depuis l'hôte. Si sa
publication a été modifiée, les contrôles d'isolation passeraient pour une
mauvaise raison, et le message le dit plutôt que de laisser croire au succès.

## L'état de départ est cassé, et c'est la règle du dépôt

Les trois conteneurs à isoler sont sur le réseau par défaut, donc les quatre
contrôles sont faux. Une tâche du setup **vérifie** que `coffre` et `atelier-b`
joignent bien le témoin avant de rendre la main : sans elle, deux contrôles
seraient vrais avant tout travail.

## Un piège du cleanup, payé d'avance

Deux dépendances d'ordre, et pas une. Un réseau dont des conteneurs sont encore
membres ne se supprime pas, et une image dont des conteneurs dérivent non plus.
Les conteneurs partent donc en premier, le réseau et l'image ensuite.

## Ce que le lab n'exige pas

Un chemin. Le réseau se crée en ligne de commande comme par l'API ; les
conteneurs se placent sur le bon réseau à la création comme par un rattachement
suivi d'un détachement.
