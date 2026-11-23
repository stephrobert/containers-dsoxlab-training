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

## Contrat fonctionnel : securite-socket-lecture-seule

Les deux contrôles inspectent l'état effectif sur l'hôte `docker.lab`. Ils
refusent l'état initial et ne réussissent que si la capacité a été retirée.
Chacun mesure une chose, et aucun ne compare des noms de fichiers.

### 1. Aucun montage ne donne accès au socket du démon

La vue du **démon** : pour chaque montage du conteneur, la source est résolue
sur l'hôte avec `readlink -f`, puis comparée au socket résolu.

Deux façons d'atteindre le socket sont refusées, et la seconde est la plus
large : **être** ce fichier, ou être un **répertoire qui le contient**. Monter
`/run` en entier donne `/run/docker.sock` à l'intérieur sans qu'aucun chemin
écrit ne ressemble à un socket.

La résolution compte. Sur la VM du lab, `/var/run` est un lien vers `/run` :
`src=/run/docker.sock` et `src=/var/run/docker.sock` désignent le même fichier
sous deux noms, et un contrôle qui comparerait les chaînes en laisserait passer
un.

### 2. Le socket du démon est injoignable depuis le conteneur

La vue du **conteneur** : tout socket unix visible à l'intérieur est relevé avec
son couple (device, inode), et aucun ne doit être celui du démon.

C'est le contrôle qui ne peut pas être contourné par un nom. Un chemin est ce
que vous avez tapé ; l'inode est ce que le noyau désigne. Une destination
renommée, un répertoire parent monté en entier, ou un chemin qu'aucune liste
n'aurait prévu donnent tous le même couple que le socket de l'hôte, parce que
c'est le même fichier.

Ce contrôle a besoin d'un conteneur **actif** : un conteneur arrêté ne
s'inspecte pas de l'intérieur. C'est pourquoi la mission demande de le laisser
tourner.

### Ce qui n'est pas noté, et pourquoi on vous le dit

Le premier temps du scénario, constater qu'un `POST` d'arrêt passe par un socket
monté en `:ro`, **n'est pas mesuré**. Ce n'est pas un oubli : un arrêt déclenché
par l'API ne laisse aucune trace qui le distingue d'un `docker stop` tapé sur
l'hôte. Un contrôle qui prétendrait l'exiger mesurerait votre obéissance, pas
votre compréhension.

Trois vérifications préalables ne sont pas des exigences de plus : le conteneur
existe, porte son label, et tourne. Sans elles, aucun des deux contrôles ne peut
regarder quoi que ce soit, et un contrôle qui n'a pas pu regarder ne doit jamais
conclure au vert. Si la résolution du socket ou la lecture de son inode échoue
sur l'hôte, le message vous dit que ce n'est pas votre faute.
