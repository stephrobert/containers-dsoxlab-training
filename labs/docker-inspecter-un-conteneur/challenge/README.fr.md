# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Le conteneur
`greffier` **tourne déjà** : rien à tirer, rien à construire, rien à lancer.

Quatre informations le concernent, et **aucune n'est écrite sur cette
machine**. Elles sont tirées au hasard à chaque passage : il n'y a rien à
retenir, et rien à recopier d'ailleurs.

## 1. Le jeton de session

`greffier` a annoncé un jeton en démarrant. Écrivez-le dans
`/opt/lab-inspection/reponses.txt`, à la ligne `jeton=`.

Il n'est dans aucun fichier de configuration, dans aucune image, et dans aucun
script : **la sortie du conteneur est le seul endroit où il existe**. C'est la
première question de tout dépannage, et c'est aussi la première commande à
avoir sous la main.

## 2. L'adresse du conteneur

Le moteur donne une adresse IP au conteneur **en le créant**. Écrivez-la à la
ligne `adresse=`.

C'est l'adresse du conteneur lui-même, pas celle de l'hôte et pas celle de la
passerelle. Elle est réattribuée à chaque création, donc elle ne se retient
pas : elle se demande.

## 3. Le port de l'hôte

Le `80` du conteneur est publié sur un port de **l'hôte**, et c'est le moteur
qui l'a choisi tout seul. Écrivez ce port à la ligne `port=`.

Attention : ce qui est attendu est le port de l'**hôte**, celui de gauche dans
la correspondance. Le `80` est le port du conteneur, la seule valeur que vous
connaissiez déjà en arrivant.

Une réponse de la forme `0.0.0.0:32768` est acceptée : elle désigne bien le bon
port.

## 4. La trace, sortie du conteneur

`greffier` a écrit `/var/log/greffier/trace.log` **après** son démarrage. Ce
fichier n'est dans aucune image : il faut le sortir du conteneur et le déposer
en `/opt/lab-inspection/trace.log`.

Il est attendu **à l'identique**, pas recopié à la main : la trace porte une
séquence tirée au hasard, précisément ce qui ne se reconstitue pas.

C'est le geste qu'on pose en vrai pour emporter un journal ou une empreinte
avant de détruire un conteneur.

## Le conteneur doit toujours tourner à la fin

On interroge un conteneur vivant, on ne l'arrête pas pour le fouiller. Un
conteneur arrêté n'a plus d'adresse ni de table des ports : l'arrêter coûte
deux contrôles.

`docker start` le remet en marche, mais ses valeurs auront changé : il faudra
les relever à nouveau.

## Ce qui n'est pas noté

La commande que vous avez tapée. Chaque réponse est recalculée en interrogeant
le moteur, puis confrontée à ce que vous avez écrit. Plusieurs chemins donnent
la même valeur, et ils comptent tous.
