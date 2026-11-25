# Qui lance vraiment un conteneur

La leçon remonte de votre processus jusqu'au démon. Ce cours montre à quoi sert
de connaître cette chaîne : savoir qui a refusé un lancement, lire ce qui a été
demandé au noyau, comprendre d'où vient un `docker exec`, reconnaître un
processus mort que personne ne ramasse, et couper un maillon.

Vous travaillez sur des conteneurs `essai-*`. Le challenge porte sur `maillon`
et `maillon-bis` : n'y touchez pas pendant le cours, et ne redémarrez pas le
démon.

Page associée : [Qui lance un conteneur : la chaîne d'exécution de Docker](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/chaine-d-execution/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run internes-chaine-dexecution
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `pid` rend le numéro,
sur la machine, du premier processus d'un conteneur ; `parent` rend celui de
son parent. **Gardez le même terminal jusqu'au nettoyage** : les variables
n'existent que dans lui.

```bash
mkdir -p ~/essai-chaine && cd ~/essai-chaine
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
pid() { docker inspect -f '{{.State.Pid}}' "$1"; }
parent() { ps -o ppid= -p "$1" | tr -d ' '; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🙅 Exercice 1 : qui a refusé ?

Provoquez quatre échecs, et notez pour chacun si le conteneur a été créé :

```bash
docker run --name essai-e1 --runtime absent "$IMAGE" true 2>&1 | grep -o 'unknown or invalid runtime name'
docker run --name essai-e2 "$IMAGE" commande-absente 2>&1 | grep -oE 'failed to create shim task|runc create failed|executable file not found'
docker run --name essai-e3 -p 22:22 "$IMAGE" true 2>&1 | grep -oE 'failed to set up container networking|address already in use'
docker run --name essai-e4 -v relatif/x:/x "$IMAGE" true 2>&1 | grep -o 'invalid characters for a local volume name'
docker ps -a --filter name=essai-e --format '{{.Names}} {{.State}}' | sort
```

```text
unknown or invalid runtime name
failed to create shim task
runc create failed
executable file not found
failed to set up container networking
address already in use
invalid characters for a local volume name
essai-e2 created
essai-e3 created
```

Le message nomme l'étage. `OCI runtime create failed` vient de `runc`, au
dernier moment ; les autres viennent du démon. Dans deux cas, le conteneur
existe à l'état `created` et occupe son nom, car l'échec est arrivé après sa
création.

## 📄 Exercice 2 : ce qui a été demandé au noyau

Lancez un conteneur et lisez la fiche que `runc` a reçue :

```bash
docker run -d --init --name essai-a --cpus 0.5 "$IMAGE" sleep 600 > /dev/null
ID=$(docker inspect -f '{{.Id}}' essai-a)
sudo cat /run/containerd/io.containerd.runtime.v2.task/moby/$ID/config.json > fiche.json
python3 -c 'import json; d = json.load(open("fiche.json")); print(d["process"]["args"]); print(len(d["process"]["capabilities"]["bounding"]), "capacites"); print(d["linux"]["resources"]["cpu"]["quota"])'
pgrep -c '^runc$'
sudo ctr -n moby tasks ls | grep -c "$ID"
```

```text
['/sbin/docker-init', '--', 'sleep', '600']
14 capacites
50000
0
1
```

Vos options sont devenues une fiche : la commande, les capacités, les limites.
`runc` l'a appliquée puis il est parti, d'où le zéro. `ctr -n moby` montre le
même conteneur vu par containerd, sans passer par Docker.

## 🚪 Exercice 3 : d'où vient un docker exec

Ajoutez un processus avec `docker exec` et regardez son parent, de dehors puis
de dedans :

```bash
docker exec -d essai-a sleep 602; sleep 1
X=$(pgrep -f '^sleep 602')
[ "$(parent $X)" = "$(parent $(pid essai-a))" ] && echo 'meme parent que le processus principal'
[ "$(parent $X)" = "$(pid essai-a)" ] || echo 'il n est pas son enfant'
docker exec essai-a ps -o ppid,args | grep '[s]leep'
```

```text
meme parent que le processus principal
il n est pas son enfant
    0 /sbin/docker-init -- sleep 600
    1 sleep 600
    0 sleep 602
```

Le processus ajouté n'est pas l'enfant du premier : il est accroché au même
intermédiaire, un cran au-dessus. De dedans, son parent vaut 0, c'est-à-dire
hors de vue. Voilà pourquoi le premier processus ne le connaît pas et ne
l'arrêtera pas proprement.

## 🧟 Exercice 4 : un mort que personne ne ramasse

Laissez un orphelin dans un conteneur sans `--init`, puis dans un conteneur qui
l'a :

```bash
docker run -d --name essai-sans "$IMAGE" sleep 600 > /dev/null
for c in essai-sans essai-a; do docker exec $c sh -c '(sleep 1 &) ; true'; done
sleep 2
for c in essai-sans essai-a; do echo "$c : $(docker exec $c ps -o ppid,stat,args | grep -c ' Z ') zombie"; done
docker exec essai-sans ps -o ppid,stat,args | grep ' Z '
docker exec essai-a ps -o pid,args | grep '^ *1 '
```

```text
essai-sans : 1 zombie
essai-a : 0 zombie
    1 Z    [sleep]
    1 /sbin/docker-init -- sleep 600
```

Un orphelin est confié au numéro 1 du conteneur, et `sleep` ne sait pas
ramasser un enfant mort : il reste en `Z` et occupe une place. Avec `--init`,
le numéro 1 est un petit programme qui le fait.

## ✂️ Exercice 5 : couper un maillon

Tuez l'intermédiaire d'un conteneur, puis le processus principal d'un autre,
depuis la machine :

```bash
P=$(pid essai-sans)
sudo kill -9 $(parent $P); sleep 2
docker inspect essai-sans --format '{{.State.Status}} {{.State.ExitCode}}'
ps -o args= -p $P || echo 'processus disparu'
sudo kill -9 $(pid essai-a); sleep 1
docker inspect essai-a --format '{{.State.Status}} {{.State.ExitCode}}'
docker start essai-sans > /dev/null && docker inspect essai-sans --format '{{.State.Status}}'
```

```text
exited 137
processus disparu
exited 137
running
```

Les deux gestes finissent pareil vu de Docker : `exited 137`. Sans son
intermédiaire, le conteneur est nettoyé par containerd. Un 137 dit donc
seulement « tué par le signal 9 » : pas par qui, ni pourquoi. Les autres
conteneurs n'ont rien senti, et le conteneur redémarre.

## 🧹 Nettoyage

```bash
cd ~
docker ps -aq --filter name=essai- | xargs docker rm -f > /dev/null
rm -rf ~/essai-chaine
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
dsoxlab reset internes-chaine-dexecution
dsoxlab check internes-chaine-dexecution
```

```text
╭─ Résultat : internes-chaine-dexecution ─╮
│  0 / 100 pts                            │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests        │
╰─────────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : deux conteneurs, leurs intermédiaires, et trois
numéros à relever.

```bash
dsoxlab run internes-chaine-dexecution
dsoxlab challenge internes-chaine-dexecution
```
