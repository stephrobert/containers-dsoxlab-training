# Scénario

Un conteneur applicatif, `dsoxlab-socket-readonly`, monte `/var/run/docker.sock`
en lecture seule. L'équipe qui l'a déployé pense que le `:ro` empêche les appels
qui modifient quelque chose. C'est faux, et vous allez d'abord le constater
vous-même avant de corriger.

À côté de lui tourne un témoin, `dsoxlab-socket-temoin`, qui ne sert qu'à la
démonstration : personne ne le note, et vous pouvez l'arrêter.

## Premier temps : constater

Le témoin tourne. Vérifiez-le :

```bash
docker inspect -f '{{.State.Status}}' dsoxlab-socket-temoin
```

Envoyez maintenant un `POST` d'arrêt depuis un conteneur qui monte le socket
**en lecture seule**. L'option `--user root` est nécessaire : l'utilisateur par
défaut de l'image curl n'a pas le droit d'ouvrir le socket.

```bash
CURL='curlimages/curl:8.23.0@sha256:3fb7e13e5d179a845c97d78204f3f1064d1907037f26a3ebf91710571151fd93'

docker run --rm --user root \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  "$CURL" --unix-socket /var/run/docker.sock \
  -s -o /dev/null -w '%{http_code}\n' \
  -X POST http://localhost/containers/dsoxlab-socket-temoin/stop

docker inspect -f '{{.State.Status}}' dsoxlab-socket-temoin
```

Le code `204` signifie que le démon **a exécuté l'arrêt**, et le témoin passe de
`running` à `exited`. Le `:ro` portait sur le fichier du socket, pas sur les
requêtes qui y transitent : le démon tourne en root et décide seul de répondre.

Ce constat n'est pas noté. Aucune trace ne distingue un arrêt déclenché par
l'API d'un `docker stop` tapé sur l'hôte, et un contrôle qui prétendrait
l'exiger mesurerait votre obéissance, pas votre compréhension.

## Second temps : la mission

**Le conteneur `dsoxlab-socket-readonly` n'atteint plus le socket du démon, par
aucun chemin.** Il reste actif et conserve son label `dsoxlab.lab`.

Deux contrôles le mesurent, et ni l'un ni l'autre ne compare des noms de
fichiers :

- le premier résout chaque source de montage sur l'hôte, et refuse celle qui
  **est** le socket comme celle qui le **contient** : monter `/run` en entier
  expose quarante-sept sockets, dont celui de containerd et l'agent SSH ;
- le second relève, **dans** le conteneur, le couple (device, inode) de chaque
  socket unix visible, et refuse celui du démon. Même inode veut dire même
  fichier, quel que soit le nom qu'on lui a donné.

Restreindre l'accès ne suffit donc pas, et le renommer encore moins. Le moindre
privilège demande de **retirer la capacité**, pas de compter sur la retenue de
l'outil qui la détient.
