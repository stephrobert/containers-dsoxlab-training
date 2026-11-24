# Le cycle de vie : redémarrer n'est pas recréer

La leçon montre les états d'un conteneur, la différence entre redémarrer et
recréer, la pause et le code de sortie. Ce cours porte sur cinq situations
qu'elle ne montre pas : le message d'erreur qui pousse à supprimer, ce qu'un
redémarrage perd malgré tout, la lecture d'un conteneur arrêté, les commandes
refusées pendant une pause, et l'attente d'une fin de tâche.

Vous travaillez sur des conteneurs `essai-*`. Le challenge porte sur d'autres
conteneurs, déjà posés sur la machine : n'y touchez pas pendant le cours.

Page associée : [Cycle de vie d'un conteneur, PID 1 et arrêt propre](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/cycle-de-vie-et-signaux/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run docker-cycle-de-vie
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. L'image d'Alpine est
déjà sur la machine. **Gardez le même terminal jusqu'au nettoyage** : la
variable `IMAGE` n'existe que dans lui.

```bash
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Vos identifiants de conteneurs seront différents.

## 🏷️ Exercice 1 : le message qui pousse à supprimer

Lancez un conteneur, puis relancez la même commande, comme on le fait de nuit
en copiant une consigne. Renommez ensuite le conteneur, en lisant son
identifiant avant et après :

```bash
docker run -d --name essai-carnet --tmpfs /cache "$IMAGE" sh -c 'sleep infinity' > /dev/null
docker run -d --name essai-carnet "$IMAGE" sh -c 'sleep infinity'; echo "code: $?"
docker container inspect essai-carnet --format '{{.Id}}' | cut -c1-12
docker rename essai-carnet essai-journal
docker container inspect essai-journal --format '{{.Id}}' | cut -c1-12
```

```text
docker: Error response from daemon: Conflict. The container name "/essai-carnet" is already in use by container "e67870e1d16fadc4443a7fcd2d01632a57f25b9a60378f8de7d8febe16b06355". You have to remove (or rename) that container to be able to reuse that name.

Run 'docker run --help' for more information
code: 125
e67870e1d16f
e67870e1d16f
```

Le second `docker run` échoue avec le code 125 : le nom est déjà pris. Le
message propose de supprimer le conteneur ou de le renommer. Le supprimer ferait
perdre ses fichiers, et c'est l'erreur que raconte le challenge. Pour relancer
ce qui existe, c'est `docker start`. Et s'il faut libérer le nom, `docker rename`
le fait sans rien perdre : les deux identifiants sont les mêmes.

## 💾 Exercice 2 : ce qu'un redémarrage perd

Le conteneur a été lancé avec `--tmpfs /cache`, qui place ce répertoire en
mémoire. Écrivez un fichier sur le disque du conteneur et un autre dans
`/cache`, puis redémarrez :

```bash
docker exec essai-journal sh -c 'echo disque > /note.txt; echo memoire > /cache/note.txt'
docker restart --timeout 1 essai-journal
docker exec essai-journal cat /note.txt
docker exec essai-journal cat /cache/note.txt; echo "code: $?"
```

```text
essai-journal
disque
cat: can't open '/cache/note.txt': No such file or directory
code: 1
```

Le conteneur est resté le même, et `/note.txt` est toujours là. Le fichier de
`/cache` a disparu : un `tmpfs` vit en mémoire et se vide à chaque arrêt.
Redémarrer garde la couche d'écriture du conteneur, pas ce qui est en mémoire.

## 🔎 Exercice 3 : lire un conteneur arrêté

Un conteneur arrêté garde ses fichiers, mais `docker exec` ne peut plus y
entrer. Deux commandes le lisent sans le relancer :

```bash
docker stop --timeout 1 essai-journal
docker exec essai-journal cat /note.txt; echo "code: $?"
docker diff essai-journal
docker cp essai-journal:/note.txt - | tar -xO
docker container inspect essai-journal --format '{{.State.Status}}'
```

```text
essai-journal
Error response from daemon: container e67870e1d16fadc4443a7fcd2d01632a57f25b9a60378f8de7d8febe16b06355 is not running
code: 1
A /note.txt
A /cache
disque
exited
```

`docker exec` exige un conteneur en marche. `docker diff` liste ce qui a changé
par rapport à l'image : `A` marque un ajout. `/cache` y figure parce que Docker
a créé ce répertoire pour y monter le `tmpfs`. `docker cp` sort un fichier, ici
vers la sortie standard sous forme d'archive, que `tar` déballe. L'état reste
`exited` : vous avez lu les données sans rien modifier. C'est le geste à faire
avant de décider quoi que ce soit sur un conteneur arrêté.

## ⏸️ Exercice 4 : les commandes refusées pendant une pause

Remettez le conteneur en marche, suspendez-le, puis essayez quatre commandes :

```bash
docker start essai-journal
docker pause essai-journal
docker exec essai-journal true; echo "exec: $?"
docker start essai-journal; echo "start: $?"
docker rm essai-journal; echo "rm: $?"
docker restart --timeout 1 essai-journal; echo "restart: $?"
docker container inspect essai-journal --format '{{.State.Status}}'
```

```text
essai-journal
essai-journal
Error response from daemon: Container essai-journal is paused, unpause the container before exec
exec: 1
Error response from daemon: cannot start a paused container, try unpause instead
failed to start containers: essai-journal
start: 1
Error response from daemon: cannot remove container "essai-journal": container is paused and must be unpaused first
rm: 1
essai-journal
restart: 0
running
```

`exec`, `start` et `rm` sont refusées, et chaque message dit de sortir d'abord de
la pause. `docker restart`, lui, réussit sans avertissement : le conteneur est
arrêté puis relancé, et il n'est plus en pause. Les processus suspendus ont donc
été terminés. Pour reprendre là où ils en étaient, c'est `docker unpause`.

## ⏱️ Exercice 5 : attendre la fin d'une tâche

Un script a souvent besoin d'attendre qu'un conteneur se termine. `docker wait`
bloque jusqu'à la fin, puis affiche le code de sortie. `docker events` relit ce
qui s'est passé :

```bash
DEBUT=$(date +%s)
docker run -d --name essai-tache "$IMAGE" sh -c 'sleep 2; exit 7' > /dev/null
docker wait essai-tache
docker events --since "$DEBUT" --until "$(( $(date +%s) + 1 ))" --filter container=essai-tache --format '{{.Action}} {{.Actor.Attributes}}' | grep -oE '^(create|start|die)|exitCode:[0-9]+'
```

```text
7
create
start
die
exitCode:7
```

`docker wait` a rendu la main au bout de deux secondes avec le code 7. Dans les
événements, `create` et `start` correspondent au `docker run`, et `die` à la fin
du processus, avec son code. Cette trace dit quand et avec quel code un
conteneur s'est terminé.

## 🧹 Nettoyage

Supprimez les conteneurs d'essai et vérifiez qu'il n'en reste aucun :

```bash
docker rm -f essai-journal essai-tache > /dev/null
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset docker-cycle-de-vie
dsoxlab check docker-cycle-de-vie
```

```text
╭─ Résultat : docker-cycle-de-vie ──╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : remettre en marche un conteneur arrêté sans le
recréer, en suspendre un autre, et en faire terminer un troisième avec un code
imposé.

```bash
dsoxlab run docker-cycle-de-vie
dsoxlab challenge docker-cycle-de-vie
```
