# reseau-bridge-dedie : nommer et isoler

## Ce que ce lab éprouve

Qu'un réseau dédié apporte **deux** choses, et non une : la résolution des noms
entre ses membres, et l'isolation de ceux qui n'en sont pas. Le lab précédent
faisait constater l'absence de DNS sur le réseau par défaut ; celui-ci fait
corriger la situation et mesure les deux effets.

## Aucun formulaire ici, et c'est voulu

Les deux labs précédents faisaient écrire des réponses. Celui-ci fait
**fabriquer**. Les quatre contrôles lisent l'état du moteur, pas un fichier.

C'est une décision de progression, pas une variation de forme : après deux labs
d'observation, l'apprenant doit poser des gestes, et un troisième formulaire
d'affilée enseignerait surtout la lassitude.

## L'état de départ est joignable, et c'est le point délicat

Au départ, les trois conteneurs sont sur le réseau par défaut, donc `tiers`
**joint** `arriere` : le contrôle d'isolation est **faux** avant tout travail,
ce que `valider-labs.py` exige.

Un setup qui aurait déjà séparé les conteneurs rendrait ce contrôle vrai sans
travail, et ce ne serait plus un test mais une hypothèse du setup. C'est la
règle la plus souvent enfreinte du dépôt, et elle est particulièrement facile à
enfreindre sur un lab d'isolation, où l'état sain ressemble à un état vide.

Mesuré sur `docker.lab` le 2026-10-30 :

| Moment | `tiers` joint `arriere` | `avant` résout `arriere` |
| --- | --- | --- |
| au départ | oui, il obtient le jeton | non |
| après le travail | non | oui, vers son adresse sur `atelier` |

## Le piège du lab, et il est fréquent en vrai

Attacher un conteneur à un réseau **ne le retire pas** de l'autre. Un conteneur
sur deux réseaux garde toute sa joignabilité depuis le réseau par défaut.

C'est la faute qui fait croire à une isolation qui n'existe pas : le nom
résout, l'application fonctionne, tout semble en ordre. Le deuxième contrôle
exige donc les deux gestes, et son message nomme celui qui manque au lieu de
dire « pas attaché ».

## Pourquoi le témoin est protégé

Le quatrième contrôle serait aussi vrai si `tiers` ou `arriere` disparaissaient :
il n'y aurait plus personne pour échouer à joindre. **Un contrôle qu'on
satisfait en retirant le sujet ne mesure rien.**

Deux garde-fous le tiennent : un préalable commun vérifie que les trois
conteneurs tournent, et le quatrième contrôle vérifie que `tiers` est sur le
réseau par défaut **et lui seul**. Le troisième contrôle prouve par ailleurs
que `arriere` est vivant et répond.

## Pourquoi le sous-réseau est imposé

Parce que c'est le geste réel. En production, un réseau de conteneurs doit
cohabiter avec le reste sans collision, et cela se décide à la création. Un
réseau créé sans `--subnet` reçoit un plan que le moteur choisit, ce qui est
précisément ce qu'on veut éviter.

## Résoudre n'est pas joindre

Le troisième contrôle ne se contente pas d'une résolution qui aboutit. Il
vérifie que le nom rend bien l'adresse du conteneur **sur ce réseau**, puis que
la connexion passe.

Un résolveur peut répondre pour une adresse qu'aucune route n'atteint, et c'est
un cas qu'on rencontre pour de vrai dès qu'un conteneur est sur plusieurs
réseaux. Deux assertions valent mieux qu'une conclusion hâtive.

## Un piège du cleanup, payé d'avance

Un réseau dont des conteneurs sont encore membres **ne se supprime pas** :
`docker network rm` refuse avec « has active endpoints ». Les conteneurs
partent donc d'abord, le réseau ensuite.

C'est exactement le genre de dépendance qu'un cleanup écrit à l'envers fait
découvrir au premier `dsoxlab reset`, dans un message qui ne dit pas la cause.

Et le réseau `atelier` est retiré **même si c'est l'apprenant qui l'a créé** :
sans cela, trois contrôles sur quatre seraient vrais au passage suivant avant
tout travail.

## Ce que le lab n'exige pas

Un chemin. Le réseau se crée par `docker network create` comme par l'API ; le
rattachement par `docker network connect` comme par une recréation du conteneur
avec `--network` ; la résolution se constate par `nslookup`, `getent` ou une
simple connexion.
