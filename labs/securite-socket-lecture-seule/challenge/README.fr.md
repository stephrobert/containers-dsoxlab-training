# Contrat fonctionnel : securite-socket-lecture-seule

Les deux contrôles inspectent l'état effectif sur l'hôte `docker.lab`. Ils
refusent l'état initial et ne réussissent que si la capacité a été retirée.
Chacun mesure une chose, et aucun ne compare des noms de fichiers.

## 1. Aucun montage ne donne accès au socket du démon

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

## 2. Le socket du démon est injoignable depuis le conteneur

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

## Ce qui n'est pas noté, et pourquoi on vous le dit

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
