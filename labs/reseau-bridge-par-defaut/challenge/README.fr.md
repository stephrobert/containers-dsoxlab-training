# Ça marchait en développement, et le nom ne résout plus

## La situation

Votre application tourne en deux conteneurs : une interface et une base. Sur le
poste du développeur, tout fonctionne, parce qu'il a écrit l'adresse IP de la
base dans sa configuration et qu'il l'a relevée une fois pour toutes.

Le serveur redémarre. Les conteneurs sont recréés, les adresses changent, et
l'application ne trouve plus sa base. Vous remplacez l'adresse par le nom du
conteneur, ce qui paraît la bonne idée, et vous obtenez :

```text
nc: bad address 'arriere'
```

Le nom ne résout pas. Pas « mal », pas « lentement » : pas du tout. Et pourtant
les deux conteneurs se joignent très bien par adresse.

Ce n'est pas une panne, c'est le réseau par défaut. Celui que personne ne
choisit, parce qu'on y tombe quand on ne dit rien.

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Deux conteneurs
**tournent déjà**, et aucun n'a reçu d'option réseau : ils sont donc sur le
réseau par défaut, celui qu'on utilise sans le choisir.

```text
arriere   il ÉCOUTE sur le port 8080 et répond un jeton
avant     il ne fait rien, c'est votre poste d'observation
```

Les trois premières réponses vont dans `/opt/lab-reseau/reponses.txt`, une
ligne par entrée, sans espace autour du signe égal.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

### 1. L'adresse de `arriere`

À la ligne `adresse=`.

Sur ce réseau, l'adresse est la **seule** façon de désigner un autre conteneur.
C'est aussi ce qui le rend impraticable en production : une adresse est
réattribuée à chaque création.

### 2. La passerelle du réseau par défaut

À la ligne `passerelle=`.

Elle se lit en inspectant le **réseau**, pas un conteneur. La distinction
compte : un conteneur connaît sa propre adresse, le réseau connaît sa
passerelle.

C'est par elle que tout sort, et c'est aussi l'adresse par laquelle un
conteneur joint un service de l'hôte.

### 3. L'interface de l'hôte qui porte cette passerelle

À la ligne `interface=`.

C'est le contrôle qui relie les deux mondes. La passerelle que voient les
conteneurs est une adresse portée par une interface **réelle** de l'hôte, un
pont que le moteur a créé au démarrage.

Cherchez du côté de l'hôte, pas des conteneurs. Une réponse de la forme
`docker0@if3` est acceptée.

### 4. Le jeton, obtenu par une vraie connexion

Depuis le conteneur `avant`, joignez `arriere` et déposez le jeton qu'il répond
dans `/jeton.txt`, **à l'intérieur de `avant`**.

Le jeton n'est nulle part ailleurs : ni dans les journaux de `arriere`, ni dans
aucun fichier. Il ne s'obtient qu'en ouvrant une connexion, et il est tiré au
hasard à chaque passage.

Le fichier est attendu **dans `avant`**, pas sur l'hôte : c'est là que l'état
compte.

### L'avertissement qui vous fera gagner du temps

Sur ce réseau, le **nom** d'un conteneur ne se résout pas. Essayez, constatez,
et cherchez pourquoi : c'est la leçon du lab, et le lab suivant y répond.

`ping` n'est pas un bon outil ici : ICMP dépend de réglages qui n'ont rien à
voir avec le sujet. Une connexion TCP prouve la même chose.

## Ce qui est noté

L'**état du système**, jamais les commandes tapées. Les trois réponses sont
recalculées au moment de la notation, en interrogeant le moteur.

La troisième question est celle qui relie les deux mondes : la passerelle que
les conteneurs voient est une adresse portée par une interface **réelle** de
l'hôte. Tant qu'on ne l'a pas vue, le réseau des conteneurs reste une
abstraction.

Et une chose qu'il vaut mieux savoir que découvrir : **l'hôte joint directement
les conteneurs de ce réseau**, sans passer par un port publié. C'est pratique
pour déboguer, et c'est un sujet de sécurité à part entière.

### Ce qui n'est pas noté

La commande que vous avez tapée, ni le chemin suivi. Les trois valeurs sont
recalculées en interrogeant le moteur, puis confrontées à ce que vous avez
écrit. Plusieurs chemins donnent la même réponse, et ils comptent tous.
