# Tout le monde parle à tout le monde

## La situation

Vous reprenez un serveur qui héberge une douzaine de conteneurs : deux
applications métier, leurs bases, un service de métrologie, et trois outils
qu'un ancien collègue avait installés « pour tester ».

Aucun n'a reçu d'option réseau. Ils sont donc tous sur le réseau par défaut, et
cela a deux conséquences que vous découvrez le même jour.

La première, agaçante : les applications doivent se parler par adresse IP,
parce que les noms ne résolvent pas. Les adresses sont écrites dans les
configurations, et elles changent au moindre redémarrage.

La seconde, nettement plus sérieuse : **les trois outils de test joignent les
bases de production**. Personne ne l'a voulu, personne ne l'a interdit. Sur un
réseau partagé, tout le monde parle à tout le monde.

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Trois conteneurs
**tournent déjà**, et aucun n'a reçu d'option réseau : ils sont tous sur le
réseau par défaut.

```text
arriere   il ÉCOUTE sur le port 8080 et répond un jeton
avant     il doit pouvoir joindre `arriere` PAR SON NOM
tiers     le témoin : il ne doit PLUS pouvoir joindre `arriere`
```

Il n'y a **aucun formulaire** à remplir dans ce lab. Tout se mesure sur l'état
du moteur.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

### 1. Un réseau nommé `atelier`, avec le sous-réseau 172.28.5.0/24

Le sous-réseau est imposé, et ce n'est pas un caprice : en production, un
réseau de conteneurs doit cohabiter avec le reste sans collision, et cela se
décide **à la création**.

Un réseau créé sans déclarer son sous-réseau en reçoit un que le moteur
choisit, ce qui est précisément ce qu'on veut éviter.

### 2. `avant` et `arriere` sur ce réseau, et plus sur le réseau par défaut

**Deux gestes, pas un.** C'est le piège du lab, et il est fréquent en vrai :
attacher un conteneur à un réseau ne le retire pas de l'autre. Un conteneur
peut être sur deux réseaux à la fois.

Et tant qu'il l'est, il reste joignable depuis le réseau par défaut : le nom
résoudra, l'application marchera, et l'isolation que vous croyez avoir obtenue
n'existera pas.

### 3. Depuis `avant`, le nom `arriere` se résout

C'est la leçon, et ce que le réseau par défaut refusait. Un réseau dédié
embarque un résolveur qui connaît ses membres par leur nom.

Le contrôle vérifie **deux** choses : que le nom rend bien l'adresse de
`arriere` sur `atelier`, et que la connexion passe. **Résoudre n'est pas
joindre** : un résolveur peut répondre pour une adresse qu'aucune route
n'atteint.

### 4. `tiers` ne joint plus `arriere`

C'est l'autre moitié de la leçon : un réseau dédié **isole** aussi.

Remarquez bien que `tiers` ne bouge pas. Ce n'est pas lui qu'on change, c'est
`arriere` qui quitte le réseau qu'ils partageaient. Au départ, `tiers` obtient
le jeton sans difficulté : c'est votre travail qui le lui retire.

### Ne touchez pas à `tiers`

C'est le témoin. Le détruire ou le déplacer ferait passer ce contrôle sans rien
prouver, et les contrôles vérifient nommément qu'il est toujours là, sur le
réseau par défaut et lui seul.

### Un conseil d'outillage

`ping` n'est pas un bon outil ici : ICMP dépend de réglages qui n'ont rien à
voir avec le sujet, et son échec vous ferait conclure à tort. Une connexion TCP
prouve la même chose.

## Ce qui est noté

L'**état du moteur**, et rien d'autre. Il n'y a aucun formulaire dans ce lab :
un réseau existe ou non, un conteneur en est membre ou non, un nom se résout ou
non, une connexion aboutit ou non.

Un détail qui a sa valeur : le troisième contrôle ne se contente pas d'une
résolution qui aboutit, il vérifie aussi que la connexion passe. **Résoudre
n'est pas joindre** : un résolveur peut très bien répondre pour une adresse
qu'aucune route n'atteint.

### Ce qui n'est pas noté

La commande que vous avez tapée. Le réseau se crée en ligne de commande comme
par l'API, le rattachement par une connexion comme par une recréation du
conteneur. Seul l'état compte.
