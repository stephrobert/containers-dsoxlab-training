# Un namespace est une vue, pas un mur

La leçon compare les namespaces d'un conteneur à ceux de la machine. Ce cours
s'en sert pour travailler : un même processus avec deux numéros, deux
conteneurs qui partagent une vue, des outils de la machine dans le réseau d'un
conteneur, une liste de processus qui ment, et un namespace créé sans Docker.

Vous travaillez sur des conteneurs `essai-*`. Le challenge porte sur
`cloisonne` et `indiscret` : n'y touchez pas pendant le cours.

Page associée : [Namespaces et cgroups : mesurer l'isolation d'un conteneur](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/sous-le-capot/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run internes-namespaces
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `pid` rend le numéro,
sur la machine, du premier processus d'un conteneur. **Gardez le même terminal
jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-vue && cd ~/essai-vue
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
pid() { docker inspect -f '{{.State.Pid}}' "$1"; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🔢 Exercice 1 : un processus, deux numéros

Lancez un conteneur, ajoutez-lui un second processus, et lisez ce que le noyau
sait de ce dernier :

```bash
docker run -d --init --name essai-a "$IMAGE" sleep 600 > /dev/null
docker exec -d essai-a sleep 601; sleep 1
P=$(pgrep -f '^sleep 601')
sudo awk '/NSpid/ {print NF-1 " numeros, le dernier est " $NF}' /proc/$P/status
docker exec essai-a pgrep -f '^sleep 601'
[ "$(sudo awk '/NSpid/ {print $2}' /proc/$P/status)" = "$P" ] && echo 'le premier est celui de la machine'
for n in pid mnt net; do [ "$(sudo readlink /proc/$P/ns/$n)" = "$(sudo readlink /proc/$(pid essai-a)/ns/$n)" ] && echo "$n : le meme que le processus principal"; done
```

```text
2 numeros, le dernier est 8
8
le premier est celui de la machine
pid : le meme que le processus principal
mnt : le meme que le processus principal
net : le meme que le processus principal
```

La ligne `NSpid` donne les deux numéros du même processus, celui de la machine
puis celui du conteneur. `docker exec` ne crée pas de nouvel espace : il entre
dans ceux qui existent.

## 👯 Exercice 2 : deux conteneurs, une seule vue

Donnez à un conteneur la vue des processus d'un autre, puis son réseau :

```bash
docker run --rm --pid container:essai-a "$IMAGE" ps -o args | grep '^sleep'
docker run --rm --pid container:essai-a "$IMAGE" sh -c 'kill -9 $(pgrep -f "^sleep 601")'
docker exec essai-a pgrep -f '^sleep 601' || echo 'le voisin l a tue'
[ "$(docker run --rm --network container:essai-a "$IMAGE" hostname)" = "$(docker exec essai-a hostname)" ] && echo 'meme nom de machine'
docker run --rm --network container:essai-a "$IMAGE" sh -c 'ps -o args | grep -c "^sleep"'
```

```text
sleep 600
sleep 601
le voisin l a tue
meme nom de machine
0
```

Partager les processus donne aussi le pouvoir de les tuer, si l'utilisateur est
le même. Partager le réseau ne partage pas les processus : le dernier compte
vaut zéro. Chaque type se partage à part.

## 🧰 Exercice 3 : les outils de la machine, le réseau du conteneur

Entrez dans le seul réseau du conteneur avec `nsenter` :

```bash
sudo nsenter -t $(pid essai-a) -n ip -br link | awk '{sub(/@.*/, "", $1); print $1}'
sudo nsenter -t $(pid essai-a) -n hostname
sudo nsenter -t $(pid essai-a) -n -u hostname | wc -c
docker exec essai-a ss -tln 2>&1 | grep -o 'executable file not found'
sudo nsenter -t $(pid essai-a) -n ss -tln | wc -l
```

```text
lo
eth0
docker.lab
13
executable file not found
1
```

La commande `ss` n'est pas dans l'image. `nsenter -n` prend celle de la machine
et la fait travailler dans le réseau du conteneur, sans rien y installer. Le
nom affiché reste `docker.lab` tant que l'on n'entre pas aussi dans l'espace du
nom, avec `-u` : il fait alors 12 caractères, et un saut de ligne.

## 🪞 Exercice 4 : une liste de processus qui ment

Entrez dans la vue des processus du conteneur, sans puis avec ses fichiers :

```bash
N=$(sudo nsenter -t $(pid essai-a) -p ps -e | wc -l)
[ "$N" -gt 50 ] && echo 'sans ses fichiers : toute la machine'
sudo nsenter -t $(pid essai-a) -p -m ps -o args
sudo nsenter -t $(pid essai-a) -p kill -0 $(pid essai-a) 2>&1 | grep -o 'No such process'
```

```text
sans ses fichiers : toute la machine
COMMAND
/sbin/docker-init -- sleep 600
sleep 600
ps -o args
No such process
```

`ps` ne demande rien au noyau : il lit `/proc`. Dans le premier cas, c'est
encore le `/proc` de la machine, donc la liste est fausse. La dernière ligne le
prouve : le numéro affiché n'existe pas dans cet espace. Il faut entrer aussi
dans les montages, avec `-m`.

## 🛠️ Exercice 5 : un namespace sans Docker

Créez des espaces à la main, d'abord un nom de machine, puis une vue des
processus :

```bash
sudo unshare --uts sh -c 'hostname essai-nom; hostname'; hostname
sudo unshare --pid sh -c 'ls / > /dev/null; ls / > /dev/null' 2>&1 | grep -o 'Cannot fork'
sudo unshare --pid --fork --mount-proc sh -c 'echo "je suis $$"; ps -e -o comm= | sort | uniq | head -3'
touch garde
sudo unshare --uts="$PWD/garde" hostname essai-garde
sudo nsenter --uts="$PWD/garde" hostname
sudo umount garde
sudo nsenter --uts="$PWD/garde" hostname 2>&1 | grep -o 'Invalid argument'
```

```text
essai-nom
docker.lab
Cannot fork
je suis 1
head
ps
sh
essai-garde
Invalid argument
```

Docker ne fait rien de plus que ces appels au noyau. `Cannot fork` est l'erreur
à connaître : dans une vue de processus, le premier enfant devient le numéro 1,
et quand il finit, plus rien ne peut y naître. `--fork` lui donne un shell qui
dure. Un espace disparaît avec son dernier processus, sauf si un fichier le
retient.

## 🧹 Nettoyage

```bash
cd ~
docker ps -aq --filter name=essai- | xargs docker rm -f > /dev/null
rm -rf ~/essai-vue
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
dsoxlab reset internes-namespaces
dsoxlab check internes-namespaces
```

```text
╭─ Résultat : internes-namespaces ──╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : trois identités à relever, et un conteneur qui
regarde chez les autres.

```bash
dsoxlab run internes-namespaces
dsoxlab challenge internes-namespaces
```
