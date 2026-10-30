# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Deux conteneurs
**tournent déjà**, et aucun n'a reçu d'option réseau : ils sont donc sur le
réseau par défaut, celui qu'on utilise sans le choisir.

```text
arriere   il ÉCOUTE sur le port 8080 et répond un jeton
avant     il ne fait rien, c'est votre poste d'observation
```

Les trois premières réponses vont dans `/opt/lab-reseau/reponses.txt`, une
ligne par entrée, sans espace autour du signe égal.

## 1. L'adresse de `arriere`

À la ligne `adresse=`.

Sur ce réseau, l'adresse est la **seule** façon de désigner un autre conteneur.
C'est aussi ce qui le rend impraticable en production : une adresse est
réattribuée à chaque création.

## 2. La passerelle du réseau par défaut

À la ligne `passerelle=`.

Elle se lit en inspectant le **réseau**, pas un conteneur. La distinction
compte : un conteneur connaît sa propre adresse, le réseau connaît sa
passerelle.

C'est par elle que tout sort, et c'est aussi l'adresse par laquelle un
conteneur joint un service de l'hôte.

## 3. L'interface de l'hôte qui porte cette passerelle

À la ligne `interface=`.

C'est le contrôle qui relie les deux mondes. La passerelle que voient les
conteneurs est une adresse portée par une interface **réelle** de l'hôte, un
pont que le moteur a créé au démarrage.

Cherchez du côté de l'hôte, pas des conteneurs. Une réponse de la forme
`docker0@if3` est acceptée.

## 4. Le jeton, obtenu par une vraie connexion

Depuis le conteneur `avant`, joignez `arriere` et déposez le jeton qu'il répond
dans `/jeton.txt`, **à l'intérieur de `avant`**.

Le jeton n'est nulle part ailleurs : ni dans les journaux de `arriere`, ni dans
aucun fichier. Il ne s'obtient qu'en ouvrant une connexion, et il est tiré au
hasard à chaque passage.

Le fichier est attendu **dans `avant`**, pas sur l'hôte : c'est là que l'état
compte.

## L'avertissement qui vous fera gagner du temps

Sur ce réseau, le **nom** d'un conteneur ne se résout pas. Essayez, constatez,
et cherchez pourquoi : c'est la leçon du lab, et le lab suivant y répond.

`ping` n'est pas un bon outil ici : ICMP dépend de réglages qui n'ont rien à
voir avec le sujet. Une connexion TCP prouve la même chose.

## Ce qui n'est pas noté

La commande que vous avez tapée, ni le chemin suivi. Les trois valeurs sont
recalculées en interrogeant le moteur, puis confrontées à ce que vous avez
écrit. Plusieurs chemins donnent la même réponse, et ils comptent tous.
