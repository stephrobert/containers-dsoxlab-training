# Les cgroups : ce qu'un conteneur peut consommer

La leçon trouve le cgroup d'un conteneur et y lit ses plafonds. Ce cours
regarde ce que le noyau en fait : une mémoire pleine qui ne l'est pas, un
plafond changé en marche, des réglages refusés, une écriture faite dans le dos
de Docker, et un plafond commun à plusieurs conteneurs.

Vous travaillez sur des conteneurs `essai-*` et une tranche `essai.slice`. Le
challenge porte sur `mesure`, `libre` et `bride` : n'y touchez pas pendant le
cours.

Page associée : [Namespaces et cgroups : mesurer l'isolation d'un conteneur](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/sous-le-capot/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run internes-cgroups-v2
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `cg` rend le répertoire
du cgroup d'un conteneur. **Gardez le même terminal jusqu'au nettoyage** : les
variables n'existent que dans lui.

```bash
mkdir -p ~/essai-cgroup && cd ~/essai-cgroup
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

## 💧 Exercice 1 : une mémoire pleine qui ne l'est pas

Écrivez un fichier de 200 Mo dans un conteneur plafonné à 64 Mo, et regardez de
quoi sa mémoire est faite :

```bash
docker run -d --init --name essai-m --memory 64m "$IMAGE" sleep 600 > /dev/null
C=$(cg essai-m)
docker exec essai-m dd if=/dev/zero of=/f bs=1M count=200 2>&1 | grep -o '200.0MB'
[ "$(cat $C/memory.current)" -gt 60000000 ] && echo 'memoire au plafond'
awk '/^(anon|file) / {print $1, int($2/1048576) " Mo"}' $C/memory.stat
awk '/^oom_kill / {print "tues : " $2}' $C/memory.events
[ "$(awk '/^max / {print $2}' $C/memory.events)" -gt 0 ] && echo 'plafond touche'
```

```text
200.0MB
memoire au plafond
anon 0 Mo
file 60 Mo
tues : 0
plafond touche
```

Le conteneur est au plafond et tout va bien : ces pages viennent du fichier
écrit, et le noyau les rend quand il en a besoin. La mémoire du programme est
la ligne `anon`. Un plafond touché n'est pas une panne ; une ligne `oom_kill`
non nulle en est une.

## 🎚️ Exercice 2 : un plafond changé en marche

Relevez le plafond, puis baissez-le sous ce que le conteneur occupe, sans le
redémarrer :

```bash
cat $C/memory.max $C/memory.swap.max
docker update --memory 128m --memory-swap 128m essai-m > /dev/null
cat $C/memory.max $C/memory.swap.max
docker update --memory 8m --memory-swap 8m essai-m > /dev/null
cat $C/memory.max
[ "$(cat $C/memory.current)" -le 8388608 ] && echo 'le noyau a rendu les pages'
docker inspect essai-m --format '{{.State.Status}}, redemarrages : {{.RestartCount}}'
```

```text
67108864
67108864
134217728
0
8388608
le noyau a rendu les pages
running, redemarrages : 0
```

`memory.swap.max` ne compte que l'échange : au départ, 64 Mo de mémoire **et**
64 Mo d'échange. Quand les deux options ont la même valeur, l'échange vaut
zéro. Le changement est immédiat, et baisser le plafond force le noyau à
reprendre le cache.

## 🚫 Exercice 3 : des réglages refusés

Demandez trop peu, demandez une contradiction, et lisez qui refuse :

```bash
docker run --rm --memory 1m "$IMAGE" true 2>&1 | grep -o 'Minimum memory limit.*'
docker run --rm --memory 64m --memory-swap 32m "$IMAGE" true 2>&1 | grep -o 'Minimum memoryswap limit.*limit'
docker update --memory-reservation 4m essai-m 2>&1 | grep -o 'Minimum memory reservation.*'
docker update --memory 64m --memory-swap 64m essai-m > /dev/null
docker update --memory-reservation 16m essai-m > /dev/null
cat $C/memory.low
```

```text
Minimum memory limit allowed is 6MB
Minimum memoryswap limit should be larger than memory limit
Minimum memory reservation allowed is 6MB
16777216
```

C'est le démon qui refuse, avant que le noyau ne soit consulté. La dernière
option pose un autre fichier : `memory.low` est une part que le noyau évite de
reprendre quand la machine manque de mémoire. Ce n'est pas un plafond.

## ✏️ Exercice 4 : une écriture dans le dos de Docker

Changez le plafond dans le fichier, comparez avec ce que dit Docker, puis
redémarrez :

```bash
sh -c "echo 33554432 > $C/memory.max" 2>&1 | grep -o 'Permission denied'
echo 33554432 | sudo tee $C/memory.max
docker inspect essai-m --format 'Docker croit : {{.HostConfig.Memory}}'
docker restart --timeout 1 essai-m > /dev/null
cat $C/memory.max
```

```text
Permission denied
33554432
Docker croit : 67108864
67108864
```

Lire est ouvert à tous, écrire demande root. Le noyau a bien appliqué
l'écriture et Docker n'en a rien su : pendant ce temps, `docker inspect` était
faux. Le redémarrage a recréé le cgroup avec la valeur de Docker. Passez par
`docker update`, et vérifiez dans le fichier.

## 🗂️ Exercice 5 : un plafond pour plusieurs conteneurs

Créez une tranche systemd plafonnée à 20 tâches, et placez-y deux conteneurs :

```bash
printf '[Slice]\nTasksMax=20\n' | sudo tee /etc/systemd/system/essai.slice > /dev/null
sudo systemctl daemon-reload
for i in 1 2; do docker run -d --init --cgroup-parent essai.slice --name essai-s$i "$IMAGE" sleep 600 > /dev/null; done
T=/sys/fs/cgroup/essai.slice
ls -d $T/docker-* | wc -l; cat $T/pids.max
docker exec essai-s1 sh -c 'i=0; while [ $i -lt 30 ]; do sleep 15 & i=$((i+1)); done' 2>&1 | tail -1 | grep -o "can't fork"
docker exec essai-s2 true 2>&1 | grep -o 'Resource temporarily unavailable' | head -1
awk '/^max/ {print ($2 > 0) ? "la tranche a refuse" : "rien"}' $T/pids.events
awk '/^max/ {print "un conteneur : " $2}' $T/docker-*/pids.events
```

```text
2
20
can't fork
Resource temporarily unavailable
la tranche a refuse
un conteneur : 0
un conteneur : 0
```

Le premier conteneur a tout pris, et c'est le **second** qui ne peut plus rien
lancer. Les compteurs des conteneurs disent zéro, car le refus vient de plus
haut : le plafond le plus serré du chemin l'emporte. Quand un refus semble
inexplicable, remontez les répertoires parents.

## 🧹 Nettoyage

```bash
cd ~
docker ps -aq --filter name=essai- | xargs docker rm -f > /dev/null
sudo systemctl stop essai.slice; sudo rm /etc/systemd/system/essai.slice; sudo systemctl daemon-reload
rm -rf ~/essai-cgroup
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
dsoxlab reset internes-cgroups-v2
dsoxlab check internes-cgroups-v2
```

```text
╭─ Résultat : internes-cgroups-v2 ──╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : deux conteneurs à comparer, et un troisième à
plafonner deux fois.

```bash
dsoxlab run internes-cgroups-v2
dsoxlab challenge internes-cgroups-v2
```
