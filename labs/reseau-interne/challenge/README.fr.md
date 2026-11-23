# On vous demande d'isoler, mais d'isoler quoi de quoi ?

## La situation

Deux demandes arrivent le même matin.

La première vient de la sécurité : un conteneur traite des fichiers déposés par
des clients, et il ne doit **rien** pouvoir joindre. Ni l'extérieur, ni l'hôte,
ni ses voisins. Il lit un volume, il écrit un volume, il n'a besoin d'aucun
réseau.

La seconde vient de l'équipe applicative : leur base de données ne doit être
joignable **que** par leur application. Mais elle doit l'être, évidemment, et
l'application doit la trouver par son nom.

Les deux demandes disent « isolez-le ». Elles ne demandent pas du tout la même
chose, et la réponse à l'une est une panne pour l'autre : un réseau confiné
laisse encore passer les voisins, et aucun réseau du tout rend la base
inutilisable.

## L'objectif

Obtenir les deux isolations sur la même machine. Quatre conteneurs tournent,
tous bâtis sur `lab-isolation:1.0`, qui écoute sur son port 80 et répond un
jeton. Tous sont sur le réseau par défaut, donc tous sortent.

```text
dehors      LE TÉMOIN. Publié sur l'adresse routable de la machine, il tient
            le rôle de tout ce qui est HORS du réseau des conteneurs.
            N'Y TOUCHEZ PAS.

coffre      ne doit avoir AUCUN réseau : pas d'interface, pas de voisin, rien
atelier-a   doit être CONFINÉ avec atelier-b
atelier-b   doit joindre atelier-a PAR SON NOM, et ne pas sortir
```

Quatre choses sont attendues :

1. `coffre` n'a aucune interface réseau hors loopback.
2. `coffre` ne joint pas `dehors`.
3. Un réseau nommé `confine` existe, déclaré **interne**, avec le sous-réseau
   **172.29.9.0/24**.
4. `atelier-a` et `atelier-b` y sont, ils se joignent **par leur nom**, et
   aucun des deux ne joint `dehors`.

L'énoncé est aussi déposé dans `/opt/MISSION.md`, avec l'adresse routable.

## Ce qu'il faut savoir avant de commencer

**Le réseau d'un conteneur ne se choisit qu'à sa création**, pour l'option qui
le déclare : il faut détruire et recréer.

Et le piège du lab précédent revient : **un conteneur peut être sur deux
réseaux à la fois**. Être sur le réseau confiné ne suffit pas, il faut aussi
avoir quitté l'autre, sinon la sortie demeure.

## Ce qui est noté

L'**état du système**. Les deux premiers contrôles sont volontairement séparés :
le premier lit la configuration du conteneur, le second éprouve ce qu'il peut
faire. Les deux peuvent diverger, et quand ils divergent c'est intéressant.

Le quatrième contrôle, lui, est indivisible : confiner sans que les membres se
parlent donnerait un service inutilisable, et les faire se parler sans les
confiner ne serait qu'un réseau dédié de plus.

## Un mot sur le mécanisme

Un réseau interne n'est pas un filtrage posé devant les conteneurs. C'est
l'**absence du chemin** : un membre de ce réseau n'a aucune route par défaut.
Vous pouvez le constater vous-même, et c'est la façon la plus nette de
comprendre ce qui se passe.

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Quatre conteneurs
**tournent déjà**, tous bâtis sur `lab-isolation:1.0`, qui écoute sur son port
80 et répond un jeton. Tous sont sur le réseau par défaut, donc tous sortent.

```text
dehors      LE TÉMOIN, publié sur l'adresse routable. N'Y TOUCHEZ PAS.
coffre      doit n'avoir AUCUN réseau
atelier-a   doit être CONFINÉ avec atelier-b
atelier-b   doit joindre atelier-a PAR SON NOM, sans sortir
```

L'adresse routable de la machine est dans `/opt/MISSION.md`.

### 1. `coffre` n'a aucune interface réseau

Hors loopback, il ne doit rien rester. Pas d'interface, donc pas d'adresse,
donc aucun voisin.

Le contrôle regarde les interfaces **dans** le conteneur, pas ce que le moteur
déclare : l'effet compte, pas le chemin.

### 2. `coffre` ne joint pas `dehors`

C'est la conséquence, et elle se mesure. Un conteneur sans réseau ne joint plus
rien du tout : ni l'extérieur, ni l'hôte, ni ses anciens voisins.

Ce contrôle est séparé du premier à dessein. Le premier lit la configuration,
celui-ci éprouve ce que le conteneur **peut faire**, et les deux peuvent
diverger.

### 3. Un réseau `confine`, interne, en 172.29.9.0/24

Le mot qui compte est **interne**. Un réseau ordinaire laisse sortir ses
membres ; un réseau interne ne leur donne **aucune route par défaut**, et c'est
ce qui les confine.

Le sous-réseau est imposé : un réseau créé sans plan en reçoit un que le moteur
choisit, ce qu'on évite en production.

### 4. L'atelier se parle sans sortir

Trois exigences d'un coup, et elles sont indissociables :

- `atelier-a` et `atelier-b` sont sur `confine` ;
- `atelier-b` joint `atelier-a` **par son nom** ;
- ni l'un ni l'autre ne joint `dehors`.

Confiner sans que les membres se parlent donnerait un service inutilisable. Les
faire se parler sans les confiner ne serait qu'un réseau dédié de plus, ce qui
était le lab précédent. C'est la conjonction qui compte.

### Ce qu'il faut savoir avant de commencer

**Le réseau d'un conteneur ne se choisit qu'à sa création**, pour l'option qui
le déclare : détruisez et recréez, sous le **même nom**.

L'image porte son écouteur, donc relancer ne demande aucune commande
particulière :

```bash
docker run -d --name <nom> <options de réseau> lab-isolation:1.0
```

Et le piège du lab précédent revient : **un conteneur peut être sur deux
réseaux à la fois**. Être sur le réseau confiné ne suffit pas, il faut aussi
avoir quitté l'autre.

### Ne touchez pas à `dehors`

C'est le témoin de ce qui est hors du réseau. Le détruire ou changer sa
publication ferait passer deux contrôles sans rien prouver, et les contrôles
vérifient nommément qu'il tourne et qu'il répond.

### Un conseil d'outillage

Ne vous contentez pas d'une connexion qui aboutit : **lisez la réponse**. Le
proxy de Docker accepte avant que quoi que ce soit n'écoute.

Et pour comprendre ce qui se passe plutôt que de le subir, regardez la table de
routage d'un conteneur confiné : `docker exec <nom> ip route`.

### Ce qui n'est pas noté

La commande que vous avez tapée. Seul l'état compte, et il est mesuré dans le
conteneur comme sur le réseau.
