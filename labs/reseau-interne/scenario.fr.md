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
