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

## L'objectif

Cartographier ce réseau avant de le quitter. Deux conteneurs tournent, aucun
n'a reçu d'option réseau :

```text
arriere   il ÉCOUTE sur le port 8080 et répond un jeton
avant     il ne fait rien, c'est votre poste d'observation
```

Renseignez les trois lignes de `/opt/lab-reseau/reponses.txt` :

```text
adresse=<l'adresse IP de arriere>
passerelle=<la passerelle du réseau par défaut>
interface=<le nom de l'interface de L'HÔTE qui porte cette passerelle>
```

Puis, **depuis le conteneur `avant`**, joignez `arriere` et déposez le jeton
qu'il répond dans un fichier, **à l'intérieur de `avant`** :

```text
/jeton.txt
```

Le jeton n'est nulle part ailleurs : ni dans les journaux de `arriere`, ni dans
aucun fichier. Il ne s'obtient qu'en ouvrant une connexion, et il est tiré au
hasard à chaque passage.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

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
