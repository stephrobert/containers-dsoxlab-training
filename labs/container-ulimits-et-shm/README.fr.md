# La mémoire partagée et les descripteurs

La leçon règle `/dev/shm` et les descripteurs à la création. Ce cours montre ce
qui casse quand ils sont mal réglés : des fichiers qu'on ne peut plus ouvrir,
une limite que le processus relève lui-même, une mémoire partagée pleine, une
mémoire partagée entre conteneurs, et un conteneur bloqué par ce qu'il y a
laissé.

Vous travaillez sur des conteneurs `essai-*`, toujours avec des valeurs
explicites. Le challenge porte sur l'image `lab-ulimits:1.0` et le conteneur
`etroit`, et vous demande de mesurer les valeurs par défaut : n'y touchez pas
pendant le cours.

Page associée : [Brider un conteneur : processeur, ulimits et mémoire partagée](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/brider-un-conteneur/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run container-ulimits-et-shm
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `cg` rend le répertoire
du cgroup d'un conteneur. **Gardez le même terminal jusqu'au nettoyage** : les
variables n'existent que dans lui.

```bash
mkdir -p ~/essai-partage && cd ~/essai-partage
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
pid() { docker inspect -f '{{.State.Pid}}' "$1"; }
cg() { echo /sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' "$1").scope; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 📂 Exercice 1 : des fichiers qu'on ne peut plus ouvrir

Donnez 20 descripteurs à un conteneur et faites ouvrir 40 fichiers à un seul
programme :

```bash
docker run -d --init --name essai-u --ulimit nofile=20:128 "$IMAGE" sleep 600 > /dev/null
docker exec essai-u sh -c 'mkdir /d; for i in $(seq 40); do echo $i > /d/$i; done'
docker exec essai-u sh -c 'timeout 2 tail -f /d/* 2>&1 > /dev/null | grep -o "No file descriptors available" | sort | uniq'
docker exec essai-u sh -c 'cat /d/* | wc -l'
```

```text
Terminated
No file descriptors available
40
```

`tail -f` garde tous ses fichiers ouverts et bute sur la limite. `cat` les
ouvre un par un et passe. La limite compte les fichiers **ouverts en même temps
par un processus**, pas les fichiers qui existent.

## 🪜 Exercice 2 : la limite souple et la limite dure

Faites monter la limite par le processus lui-même, puis dépassez le plafond :

```bash
docker exec essai-u sh -c 'ulimit -n; ulimit -n 128 && ulimit -n; ulimit -n 200' 2>&1
docker exec essai-u sh -c 'ulimit -n'
sudo prlimit --pid $(pid essai-u) --nofile=100:128
sudo prlimit --pid $(pid essai-u) --nofile -o SOFT,HARD --noheadings
docker exec essai-u sh -c 'ulimit -n'
docker run --rm --ulimit nofile=64:32 "$IMAGE" true 2>&1 | grep -o 'soft limit must be.*'
docker update --ulimit nofile=100 essai-u 2>&1 | grep -o 'unknown flag: --ulimit'
```

```text
sh: error setting limit: Operation not permitted
20
128
20
100 128
20
soft limit must be less than or equal to hard limit: 64 > 32
unknown flag: --ulimit
```

Un processus peut monter jusqu'à sa limite dure, pas plus haut, même en root
dans le conteneur. Chaque processus a la sienne : changer celle du premier ne
change pas celle du prochain `docker exec`. Et Docker ne sait pas la modifier
en marche : il faut recréer.

## 📦 Exercice 3 : une mémoire partagée pleine

Écrivez plus que la taille de `/dev/shm`, puis réservez sans écrire :

```bash
docker run -d --init --name essai-s --shm-size 16m --memory 256m "$IMAGE" sleep 600 > /dev/null
docker exec essai-s dd if=/dev/zero of=/dev/shm/f bs=1M count=20 2>&1 | grep -o 'No space left on device'
awk '/^shmem / {print int($2/1048576) " Mo comptes"}' $(cg essai-s)/memory.stat
docker exec essai-s rm /dev/shm/f
docker exec essai-s truncate -s 12M /dev/shm/vide
docker exec essai-s sh -c 'stat -c "%s octets annonces" /dev/shm/vide; du -m /dev/shm/vide'
awk '/^shmem / {print int($2/1048576) " Mo comptes"}' $(cg essai-s)/memory.stat
```

```text
No space left on device
16 Mo comptes
12582912 octets annonces
0	/dev/shm/vide
0 Mo comptes
```

« No space left on device » ne parle pas du disque ici : c'est la mémoire
partagée qui est pleine, alors que le conteneur a encore beaucoup de mémoire.
Un fichier seulement annoncé n'occupe rien : seules les pages écrites sont
comptées.

## 🤝 Exercice 4 : une mémoire partagée entre conteneurs

Essayez de rejoindre la mémoire partagée d'un conteneur, puis recommencez avec
un conteneur qui l'autorise :

```bash
docker run --rm --ipc container:essai-s "$IMAGE" ls /dev/shm 2>&1 | grep -o 'non-shareable IPC'
docker run -d --init --name essai-i --ipc shareable --shm-size 32m "$IMAGE" sleep 600 > /dev/null
docker exec essai-i sh -c 'echo salut > /dev/shm/mot'
docker run --rm --ipc container:essai-i --shm-size 96m "$IMAGE" sh -c 'cat /dev/shm/mot; df -m /dev/shm | awk "END {print \$2 \" Mo\"}"'
docker run --rm --shm-size 32m "$IMAGE" ls -A /dev/shm | wc -l
```

```text
non-shareable IPC
salut
32 Mo
0
```

Par défaut, la mémoire partagée est privée. `--ipc shareable` ouvre celle d'un
conteneur, et un autre la rejoint par `--ipc container:`. Le second a demandé
96 Mo en vain : la taille appartient à celui qui a créé l'espace.

## 💥 Exercice 5 : bloqué par ce qu'il a laissé

Donnez 64 Mo de mémoire partagée à un conteneur qui n'a que 32 Mo de mémoire :

```bash
docker run -d --init --name essai-o --memory 32m --memory-swap 32m --shm-size 64m "$IMAGE" sleep 600 > /dev/null
docker exec essai-o dd if=/dev/zero of=/dev/shm/f bs=1M count=48 2> /dev/null; echo "code $?"
docker inspect essai-o --format '{{.State.Status}} tue={{.State.OOMKilled}}'
awk '/^(anon|shmem) / {print $1, int($2/1048576) " Mo"}' $(cg essai-o)/memory.stat
docker exec essai-o true > /dev/null 2>&1 || echo 'plus aucune commande possible'
docker restart --timeout 1 essai-o > /dev/null
docker exec essai-o ls -A /dev/shm | wc -l
```

```text
code 137
running tue=true
anon 0 Mo
shmem 30 Mo
plus aucune commande possible
0
```

Le programme est mort, sa mémoire est rendue, et pourtant il reste environ 30
Mo : le fichier est toujours dans `/dev/shm`. Le conteneur tourne mais n'a plus
la place de lancer quoi que ce soit, même pour effacer. Le redémarrage vide
cette mémoire. Comptez toujours la taille de `/dev/shm` dans la limite mémoire.

## 🧹 Nettoyage

```bash
cd ~
docker ps -aq --filter name=essai- | xargs docker rm -f > /dev/null
rm -rf ~/essai-partage
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
dsoxlab reset container-ulimits-et-shm
dsoxlab check container-ulimits-et-shm
```

```text
╭─ Résultat : container-ulimits-et-shm ─╮
│  0 / 100 pts                          │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests      │
╰───────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : deux valeurs à mesurer, deux à régler, et une pesée.

```bash
dsoxlab run container-ulimits-et-shm
dsoxlab challenge container-ulimits-et-shm
```
