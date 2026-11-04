# Interposer un proxy filtrant devant l'API Docker

Un outil de supervision tourne sur cette machine. Il a besoin de lire la liste
des conteneurs et d'en arrêter un quand il le juge malade. La façon rapide de le
lui permettre est de lui monter le socket Docker. On l'a montée en `:ro`, pour
être prudent.

Cette prudence ne protège rien, et vous allez le constater avant de le corriger.

## Ce que la machine porte déjà

Deux témoins tournent, posés pour vous :

- **`cible-1`** existe pour être arrêté. C'est lui qui va montrer que la lecture
  seule n'empêche pas une écriture sur l'API.
- **`cible-2`** porte une variable `CLE_API`, passée avec `-e`, qui joue le rôle
  d'un secret. Sa valeur est factice.

Le fichier `images.env` de votre répertoire de travail porte les trois
références épinglées à reprendre telles quelles : le proxy, un client HTTP et
l'image des témoins. Chacune porte son tag **et** son digest.

## Le premier constat : `:ro` ne filtre pas les requêtes

Le `:ro` rend le **fichier** du socket non modifiable. Il ne regarde pas ce qui
transite dedans. Or le socket est un canal vers le démon, le démon tourne en
root, et un arrêt de conteneur est une requête `POST` comme une autre.

Montez un client qui ne reçoit le socket qu'en lecture seule, et demandez-lui
d'arrêter `cible-1`. Nommez ce client **`client-ro`** et **laissez-le en
place** : c'est le dispositif qui prouve la démonstration, et c'est lui que le
contrôle inspecte. Le code que vous lirez est `204`, et `cible-1` passera de
`running` à `exited`.

Si votre client n'arrive pas à ouvrir le socket, lisez la section de diagnostic
plus bas avant de chercher ailleurs.

## Le travail : donner à l'outil juste ce qu'il lui faut

Un socket-proxy est un petit serveur HTTP placé entre l'outil et le socket. Il
compare chaque couple méthode et chemin à une liste blanche, transmet ce qui est
autorisé, et refuse le reste lui-même, sans que le démon en entende parler.
Presque toutes les familles de chemins sont fermées par défaut ; une variable
d'environnement à `1` ouvre sa famille.

Déployez-le ainsi :

- un réseau nommé **`reseau-filtre`**, créé avec `--internal` ;
- un conteneur nommé **`filtre-api`**, sur ce réseau, qui tourne l'image
  épinglée de `images.env` ;
- il est le **seul** à monter le socket Docker ;
- il est durci : `--read-only`, plus un `--tmpfs /run` sans lequel HAProxy ne
  peut pas écrire sa configuration ;
- **aucun port n'est publié.** Ce proxy n'a ni authentification ni TLS : tout ce
  qui atteint son port atteint ses règles. Les clients le joignent par son nom,
  depuis son réseau.

Les variables du profil tiennent en deux : l'outil doit **lire** les conteneurs
et **arrêter** l'un d'eux, rien de plus.

## Les six choses qui sont notées

1. **Le dispositif du premier constat.** `client-ro` existe, il monte le socket
   en lecture seule, et `cible-1` est arrêté.
2. **Le déploiement du proxy.** Image épinglée par digest, `--read-only`,
   `--tmpfs /run`, aucun port publié, et le proxy seul à monter le socket.
3. **Le profil est étroit.** `/_ping`, `/version` et `/containers/json`
   répondent `200`. `/info`, `/images/json`, `/volumes` et `/networks`
   répondent `403` : ce sont des familles que personne ne vous demande
   d'ouvrir, et une variable en ouvre une entière d'un coup.
4. **Le secret ne passe plus par l'environnement.** Interrogez l'inspection de
   `cible-2` **à travers le proxy** et regardez ce qu'elle rend. Un simple
   profil de lecture suffit à lire `.Config.Env` de n'importe quel conteneur de
   la machine, depuis n'importe quel conteneur du réseau. Recréez `cible-2`,
   sous le même nom, avec son secret ailleurs que dans `-e`.
5. **Une action précise, et pas la combinaison qui ouvre l'hôte.** L'arrêt doit
   passer en `204` et la création d'un conteneur rester en `403`.
6. **Les trois refus se distinguent.** Le `403` du proxy porte
   « Request forbidden by administrative rules ». Un chemin versionné que le
   moteur ne sait pas servir, comme `/v1.99/containers/json`, traverse le proxy
   et se fait rejeter par le **moteur**, en `400` avec un message JSON. Et un
   client qui n'arrive pas à ouvrir le socket n'a aucun code HTTP du tout.

## La combinaison à ne pas faire, et pourquoi

`POST=1` autorise les méthodes d'écriture pour toutes les familles ouvertes. Ajouté
à la famille des conteneurs, qui contient `create` et `exec`, il annule le
filtrage pour tout ce qui compte. Mesuré sur cette machine : une requête de
création portant `Privileged` et un montage de `/` sur `/hote` répond **201**,
et l'inspection du conteneur créé affiche `privileged=true binds=[/:/hote]`.
Cette combinaison vaut **root sur l'hôte**, même avec les familles des images,
des volumes et des réseaux fermées.

Les variables `ALLOW_` existent pour cela : elles ouvrent **une action** au lieu
d'une famille. `ALLOW_STOP=1` n'autorise que l'arrêt, et n'a pas besoin de
`POST=1` avec cette image.

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

## Ce que le proxy ne fait pas

Il réduit ce qu'un client de son réseau peut demander. Il ne protège pas l'hôte
contre quelqu'un qui le contrôle déjà : **le shell de l'hôte atteint le proxy
dans tous les cas**, et ses règles sont alors la seule barrière. Il n'offre ni
authentification ni TLS. Et il tourne en root en montant le socket réel : qui le
compromet obtient tout ce que le socket permet.

Gardez un proxy par outil, un réseau par proxy, et aucun port publié.
