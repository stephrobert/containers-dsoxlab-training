# Fixer un plafond mémoire et contenir un OOM

La leçon pose un plafond et prouve un OOM par son compteur. Ce cours regarde
les suites : un plafond écrit dans Compose et qui ne s'applique pas, une
mémoire pleine qu'aucun processus ne détient, un programme tué pour la
gourmandise d'un autre, la trace laissée dans le journal du noyau, et un groupe
qui meurt en bloc.

Vous travaillez sur des conteneurs `essai-*`. Le challenge porte sur le service
`worker` et sur `/opt/dsoxlab-container-memoire-et-oom` : n'y touchez pas
pendant le cours.

Page associée : [Plafonner la mémoire et le nombre de tâches](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/memoire-et-taches/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run container-memoire-et-oom
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `cg` rend le répertoire
du cgroup d'un conteneur. **Gardez le même terminal jusqu'au nettoyage** : les
variables n'existent que dans lui.

```bash
mkdir -p ~/essai-memoire && cd ~/essai-memoire
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
cg() { echo /sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' "$1").scope; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 📝 Exercice 1 : un plafond écrit, et pas appliqué

Compose accepte deux écritures du plafond mémoire. Essayez la seconde,
changez-la, et regardez quelle commande la prend en compte :

```bash
cat > compose.yaml <<EOF
services:
  app:
    image: $IMAGE
    container_name: essai-app
    network_mode: none
    init: true
    deploy: {resources: {limits: {memory: 40m}}}
    command: sleep 600
EOF
docker compose up -d 2> /dev/null; cat $(cg essai-app)/memory.max
sed -i 's/40m/48m/' compose.yaml
docker compose restart -t 1 2> /dev/null; cat $(cg essai-app)/memory.max
docker compose up -d 2> /dev/null; cat $(cg essai-app)/memory.max
sed -i 's/^    command/    mem_limit: 64m\n    command/' compose.yaml
docker compose up -d 2>&1 | grep -o "can't set distinct values.*"
cat $(cg essai-app)/memory.max
```

```text
41943040
41943040
50331648
can't set distinct values on 'mem_limit' and 'deploy.resources.limits.memory': invalid compose project
50331648
```

`restart` relance le conteneur existant avec ses anciens réglages. Seul `up -d`
compare le fichier au conteneur et le recrée. Les deux écritures ne se
mélangent pas : deux valeurs différentes, et Compose refuse tout le projet.
Gardez celle que le fichier utilise déjà.

## 🫙 Exercice 2 : une mémoire pleine que personne ne détient

Écrivez 80 Mio dans un système de fichiers en mémoire, sous un plafond de 40,
puis essayez d'entrer dans le conteneur :

```bash
docker run -d --init --name essai-t --memory 40m --memory-swap 40m --tmpfs /t "$IMAGE" sleep 600 > /dev/null
docker exec essai-t dd if=/dev/zero of=/t/f bs=1M count=80; echo "rc=$?"
awk '/^(anon|shmem) / {print $1, int($2/1048576) " Mio"}' $(cg essai-t)/memory.stat
docker exec essai-t true 2>&1 | grep -o 'possibly OOM-killed'
docker update --memory 64m --memory-swap 64m essai-t > /dev/null
docker exec essai-t rm /t/f && awk '/^shmem / {print $1, $2}' $(cg essai-t)/memory.stat
docker run --rm --memory 40m --memory-swap 40m --tmpfs /t:size=20m "$IMAGE" dd if=/dev/zero of=/t/f bs=1M count=80 2>&1 | grep -o 'No space left on device'
```

```text
rc=137
anon 0 Mio
shmem 38 Mio
possibly OOM-killed
shmem 0
No space left on device
```

Tuer `dd` n'a rien libéré : le fichier est resté, et la ligne `shmem` le
montre. Toute commande ajoutée est tuée à son tour. Relever le plafond le temps
de supprimer le fichier débloque la situation. Pour l'éviter, donnez une taille
au montage : le programme reçoit alors une erreur d'écriture, et personne n'est
tué.

## 🎯 Exercice 3 : tué pour la gourmandise d'un autre

Un premier programme occupe 32 Mio et ne demande plus rien. Un second en
demande 30, sous un plafond de 60 :

```bash
docker run -d --init --name essai-q --memory 60m --memory-swap 60m "$IMAGE" sleep 600 > /dev/null
docker exec -d essai-q awk 'BEGIN {s="x"; for(i=0;i<25;i++) s=s s; system("sleep 500")}'
sleep 3
docker exec essai-q ps -o args | grep -c '^awk'
docker exec essai-q dd if=/dev/zero of=/dev/null bs=30M count=1 2>&1 | grep -o '1+0 records out'
docker exec essai-q ps -o args | grep -c '^awk'
awk '/^oom_kill / {print}' $(cg essai-q)/memory.events
```

```text
1
1+0 records out
0
oom_kill 1
```

Le demandeur a réussi, et c'est l'autre qui a disparu. Le noyau tue d'abord le
processus qui pèse le plus, pas celui qui a demandé la mémoire de trop. Quand
un programme meurt sans raison apparente, cherchez aussi qui vit à côté de lui
dans le conteneur.

## 📜 Exercice 4 : la trace dans le journal du noyau

Retrouvez l'incident précédent dans le journal de la machine :

```bash
ID=$(docker inspect -f '{{.Id}}' essai-q)
sudo dmesg | grep "oom-kill:" | grep "$ID" > trace
grep -oE 'constraint=[A-Z_]+' trace
grep -oE ',task=[^,]+' trace
grep -oE 'oom_memcg=[^,]+' trace | grep -c "$ID"
sudo dmesg | grep -A1 "oom-kill:.*$ID" | grep -oE 'Memory cgroup out of memory: Killed process'
sudo dmesg | grep -c 'constraint=CONSTRAINT_NONE'
```

```text
constraint=CONSTRAINT_MEMCG
,task=awk
1
Memory cgroup out of memory: Killed process
0
```

`CONSTRAINT_MEMCG` dit que le plafond d'un groupe a été touché, `oom_memcg` dit
lequel, et `task` nomme la victime. Un manque de mémoire de toute la machine
s'écrirait `CONSTRAINT_NONE` : le dernier compte vaut zéro. Cette trace reste
après la mort du conteneur, alors que son cgroup a disparu.

## ⛓️ Exercice 5 : un groupe qui meurt en bloc

Demandez au noyau de ne pas choisir, et provoquez le même incident :

```bash
docker run -d --name essai-g --memory 40m --memory-swap 40m "$IMAGE" sleep 600 > /dev/null
C=$(cg essai-g); cat $C/memory.oom.group
echo 1 | sudo tee $C/memory.oom.group > /dev/null
docker exec essai-g awk 'BEGIN {s="x"; for(i=0;i<26;i++) s=s s}'; echo "rc=$?"
sleep 1
docker inspect essai-g --format '{{.State.Status}} {{.State.ExitCode}} {{.State.OOMKilled}}'
docker run --help | grep -c 'oom-group'
```

```text
0
rc=137
exited 137 true
0
```

Avec `memory.oom.group` à 1, tout le groupe part, premier processus compris.
C'est utile pour un service dont les processus n'ont pas de sens l'un sans
l'autre, et l'inverse de ce qu'il faut pour un service qui doit survivre.
Docker n'a pas d'option pour ce réglage et le laisse à zéro.

## 🧹 Nettoyage

```bash
cd ~
docker ps -aq --filter name=essai- | xargs -r docker rm -f > /dev/null
docker network ls --filter name=essai- -q | xargs -r docker network rm > /dev/null
rm -rf ~/essai-memoire
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker images --format '{{.Repository}}' | grep -c 'essai-\|15547'
```

```text
0
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset container-memoire-et-oom
dsoxlab check container-memoire-et-oom
```

```text
╭─ Résultat : container-memoire-et-oom ─╮
│  0 / 100 pts                          │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests      │
╰───────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un service à remettre dans son budget, et qui doit
survivre à un OOM.

```bash
dsoxlab run container-memoire-et-oom
dsoxlab challenge container-memoire-et-oom
```
