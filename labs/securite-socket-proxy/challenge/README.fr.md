# Interposer un proxy filtrant devant l'API Docker

Un outil de supervision tourne sur cette machine. Il a besoin de lire la liste
des conteneurs et d'en arrêter un quand il le juge malade. La façon rapide de le
lui permettre est de lui monter le socket Docker. On l'a monté en `:ro`, pour
être prudent.

Cette prudence ne protège rien, et vous allez le constater avant de le corriger.

## Ce qui est demandé

Sur `docker.lab`, deux témoins tournent déjà, et votre répertoire de travail
`/opt/dsoxlab-securite-socket-proxy` porte les références épinglées :

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

### 1. Le socket en lecture seule n'a pas protégé le témoin

`client-ro` doit exister, monter `/var/run/docker.sock` en **lecture seule**, et
`cible-1` doit être **arrêté**. Demandez l'arrêt depuis ce client, et laissez-le en
place : c'est lui que le contrôle inspecte.

### 2. Le proxy est épinglé, durci, et seul à monter le socket

Cinq propriétés, chacune refusée séparément :

```text
l'image porte le digest d'images.env   un tag seul laisse le contenu changer
--read-only                             racine non modifiable
--tmpfs /run                            sans lui, HAProxy ne démarre pas
aucun port publié                       ni authentification ni TLS sur ce proxy
le proxy seul monte le socket           sinon il ne filtre rien
```

### 3. Le profil de lecture ouvre ce qu'il faut, et rien de plus

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

### 4. Le secret de `cible-2` ne passe plus par l'environnement

Interrogez `GET /containers/cible-2/json` **à travers le proxy**. Un profil de
lecture suffit à rendre `.Config.Env`, donc tout ce qui a été passé avec `-e`,
pour n'importe quel conteneur de la machine.

Recréez `cible-2` sous le même nom, en marche, avec son secret ailleurs que
dans `-e`. Le contrôle relit l'inspection à travers le proxy et refuse si
`CLE_API` y apparaît encore.

### 5. Une action précise, sans la combinaison qui ouvre l'hôte

À travers le proxy, un arrêt de conteneur répond `204` et une création répond
`403`. Le profil ouvre la lecture des conteneurs et la seule action d'arrêt.

`POST=1` est refusé : il autorise l'écriture sur toute famille ouverte, et celle
des conteneurs contient `create` et `exec`. Mesuré sur cette machine, une création
portant `Privileged` et un montage de `/` répond alors **201**, ce qui vaut root
sur l'hôte.

### 6. Le proxy n'est joignable que depuis son réseau

`filtre-api` est sur `reseau-filtre`, créé avec `--internal` : il n'a pas de sortie
vers Internet, et un conteneur d'un autre réseau ne l'atteint pas. Le shell de
l'hôte, lui, l'atteint toujours : aucun contrôle ne demande de l'empêcher.

### 7. Les trois refus se distinguent par qui les prononce

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

## Diagnostiquer, quand quelque chose refuse

Trois symptômes, trois causes, trois endroits où chercher.

**Le proxy répond `403` alors que vous croyez la variable posée.** Les variables
d'un conteneur se fixent **à sa création** : on ne les change pas sur un
conteneur qui tourne. Supprimez le proxy et recréez-le avec les bons `-e`. Le
réseau et les témoins restent en place. Vérifiez ce qu'il porte réellement avec
`docker inspect -f '{{.Config.Env}}' filtre-api`.

**Le moteur répond `400`.** La requête est **passée**, c'est le démon qui la
rejette. Son message est du JSON, et il dit quoi : une version d'API trop
récente, un filtre illisible, un corps absent. Le corps du `403` du proxy, lui,
est du HTML. Les deux codes vous disent qui a refusé, donc où corriger.

**Votre client n'ouvre pas le socket.** Il n'y a alors aucun code HTTP : `curl`
sort en **7** avec « Could not connect to server ». Sur cette machine le socket
est en `root:docker 0660` et l'image cliente tourne sous un compte sans
privilège. Un `--user root` fait passer la même requête. Ce détail est un
rappel utile : le proxy, lui, tourne en **root** et monte le vrai socket.
