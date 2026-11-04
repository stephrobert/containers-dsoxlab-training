# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Deux témoins
tournent déjà, et votre répertoire de travail `/opt/dsoxlab-securite-socket-proxy`
porte les références épinglées :

```text
images.env   le proxy, un client HTTP et l'image des témoins, tag ET digest
MISSION.md   l'énoncé complet
```

```text
cible-1      posé pour être arrêté
cible-2      porte CLE_API avec -e, un faux secret
```

Les objets que vous créez portent des noms imposés, parce que les contrôles les
inspectent : le réseau **`reseau-filtre`**, le proxy **`filtre-api`**, et le
client du premier constat **`client-ro`**.

Le port est **2375**, et vous ne le choisissez pas : l'image du proxy le fixe
dans sa configuration HAProxy, et n'expose aucune variable pour le changer.

## 1. Le socket en lecture seule n'a pas protégé le témoin

`client-ro` doit exister, monter `/var/run/docker.sock` en **lecture seule**, et
`cible-1` doit être **arrêté**.

Ce contrôle ne cherche pas à savoir par quelle commande l'arrêt est venu, et il
ne le peut pas : la CLI appelle la même API que votre `curl`, le démon ne voit
aucune différence. Il mesure le dispositif, qui est ce qui porte la leçon.

## 2. Le proxy est épinglé, durci, et seul à monter le socket

Cinq propriétés, chacune refusée séparément :

```text
l'image porte le digest d'images.env   un tag seul laisse le contenu changer
--read-only                             racine non modifiable
--tmpfs /run                            sans lui, HAProxy ne démarre pas
aucun port publié                       ni authentification ni TLS sur ce proxy
le proxy seul monte le socket           sinon il ne filtre rien
```

## 3. Le profil de lecture ouvre ce qu'il faut, et rien de plus

```text
GET /_ping, /version, /containers/json        200
GET /info, /images/json, /volumes, /networks  403
HEAD /volumes                                 403
```

Le `HEAD` est là parce qu'une route ouverte en lecture accepte aussi `HEAD` :
une famille fermée doit donc le refuser également, et ce contrôle attrape un
profil ouvert plus largement qu'on ne le croyait.

Pour l'interroger vous-même, écrivez `curl -I` et **jamais** `curl -X HEAD` :
mesuré, la seconde forme fait attendre à curl un corps qui n'arrive jamais, et
bloque jusqu'au délai.

## 4. Le secret de `cible-2` ne passe plus par l'environnement

Interrogez `GET /containers/cible-2/json` **à travers le proxy**. Un profil de
lecture suffit à rendre `.Config.Env`, donc tout ce qui a été passé avec `-e`,
pour n'importe quel conteneur de la machine.

Recréez `cible-2` sous le même nom, en marche, avec son secret ailleurs que
dans `-e`. Le contrôle relit l'inspection à travers le proxy et refuse si
`CLE_API` y apparaît encore.

## 5. Une action précise, sans la combinaison qui ouvre l'hôte

```text
CONTAINERS=1      l'outil lit les conteneurs
ALLOW_STOP=1      il peut arrêter, et rien d'autre
POST=1            REFUSÉ, en combinaison avec CONTAINERS
POST .../stop     204
POST /containers/create  403
```

`POST=1` ajouté à la famille des conteneurs, qui contient `create` et `exec`,
annule le filtrage pour tout ce qui compte. Mesuré sur cette machine : une
création portant `Privileged` et un montage de `/` répond **201**, et le
conteneur créé affiche `privileged=true binds=[/:/hote]`.

## 6. Les trois refus se distinguent par qui les prononce

```text
403 + corps HTML « administrative rules »   le PROXY a refusé
400 + message JSON du moteur                la requête est PASSÉE
aucun code HTTP, curl sort en 7             le client n'a pas ouvert le socket
```

Chacun appelle un geste différent : un `403` se corrige dans les variables du
proxy, un `400` dans la requête, un échec d'ouverture dans le compte qui ouvre.
Le contrôle du `400` passe par un chemin versionné (`/v1.99/containers/json`),
parce que le profil demandé ici n'ouvre pas l'écriture : le `400` du moteur n'y
serait pas atteignable autrement.

## Une surprise, et ce que le lab n'en fait pas

**Le shell de l'hôte atteint le proxy dans tous les cas.** `--internal` coupe la
sortie vers Internet, et la séparation des réseaux empêche un conteneur d'un
autre réseau de le joindre, mais rien n'isole le proxy de la machine qui le fait
tourner. Ce n'est pas un défaut à corriger, c'est une limite à connaître : aucun
contrôle ne l'exige, et le contrôle 5 mesure seulement ce que `--internal`
garantit vraiment.
