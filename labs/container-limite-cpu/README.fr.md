# Brider un processeur, et le prouver

La leçon pose `--cpus` et `--cpuset-cpus`, et lit le compteur d'arrêts. Ce
cours mesure ce qui se passe ensuite : quand la limite mord, ce que coûte la
longueur de la période, un poids qui ne joue que sous la concurrence, un
réglage changé en marche, et des demandes refusées.

Vous travaillez sur des conteneurs `essai-*`. Le challenge porte sur `brideur`
et `epingle` : n'y touchez pas pendant le cours. Les pourcentages varient d'un
ou deux points d'une fois à l'autre.

Page associée : [Brider un conteneur : processeur, ulimits et mémoire partagée](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/brider-un-conteneur/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run container-limite-cpu
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `boucles` lance un
conteneur occupé ; `part` mesure pendant trois secondes le processeur qu'il
consomme ; `arrets` lit son compteur. **Gardez le même terminal jusqu'au
nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-cpu && cd ~/essai-cpu
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
cg() { echo /sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' "$1").scope; }
boucles() { n=$1; c=$2; shift 2; docker run -d --init --name "$c" "$@" "$IMAGE" sh -c "for i in \$(seq $n); do while :; do :; done & done; wait" > /dev/null; sleep 1; }
temps() { awk '/^usage_usec/ {print $2}' $(cg "$1")/cpu.stat; }
part() { a=$(temps $1); sleep 3; b=$(temps $1); echo "$(( (b - a + 15000) / 30000 )) %"; }
arrets() { awk '/^nr_throttled/ {print $2}' $(cg "$1")/cpu.stat; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 📉 Exercice 1 : quand la limite mord

Croisez deux limites et deux charges :

```bash
for l in 0.5 1.5; do for n in 1 2; do
  boucles $n essai-x --cpus $l
  P=$(part essai-x); [ "$(arrets essai-x)" -gt 0 ] && M='retenu' || M='jamais retenu'
  echo "limite $l, $n boucle(s) : $P, $M"
  docker rm -f essai-x > /dev/null
done; done
```

```text
limite 0.5, 1 boucle(s) : 50 %, retenu
limite 0.5, 2 boucle(s) : 50 %, retenu
limite 1.5, 1 boucle(s) : 100 %, jamais retenu
limite 1.5, 2 boucle(s) : 150 %, retenu
```

Une boucle occupe au plus un processeur. Elle suffit à dépasser 0,5, jamais à
dépasser 1,5. Le compteur ne bouge que si la demande dépasse la limite : un
compteur à zéro peut vouloir dire que la limite est large, ou que la charge est
trop faible pour la voir.

## ⏲️ Exercice 2 : la longueur de la période

Donnez la même part sur deux périodes, et mesurez la durée d'un arrêt :

```bash
for p in 10000 100000; do
  boucles 1 essai-x --cpu-period $p --cpu-quota $((p / 2))
  P=$(part essai-x)
  awk -v p=$p -v u="$P" '/^nr_throttled/ {n = $2} /^throttled_usec/ {t = $2} END {m = t / n / 1000; print "periode " p / 1000 " ms : " u ", arrets de " (m < 10 ? "moins de 10 ms" : "plus de 40 ms")}' $(cg essai-x)/cpu.stat
  docker rm -f essai-x > /dev/null
done
```

```text
periode 10 ms : 50 %, arrets de moins de 10 ms
periode 100 ms : 50 %, arrets de plus de 40 ms
```

La part est la même, l'attente non. Avec 100 ms, la valeur par défaut, une
requête qui tombe au mauvais moment attend près de 50 ms. C'est ce qui donne
des lenteurs par à-coups sur un service dont la moyenne est bonne.

## ⚖️ Exercice 3 : un poids, pas un plafond

Mettez deux conteneurs en concurrence sur le même processeur avec des poids
différents, puis retirez l'un :

```bash
boucles 1 essai-fort --cpuset-cpus 0 --cpu-shares 1024
boucles 1 essai-faible --cpuset-cpus 0 --cpu-shares 256
cat $(cg essai-fort)/cpu.weight $(cg essai-faible)/cpu.weight
for c in fort faible; do P=$(part essai-$c); V=${P% %}; [ "$V" -gt 50 ] && echo "$c : environ trois quarts" || echo "$c : environ un quart"; done
docker rm -f essai-fort > /dev/null
echo "faible, seul : $(part essai-faible)"
arrets essai-faible
```

```text
100
35
fort : environ trois quarts
faible : environ un quart
faible, seul : 100 %
0
```

Le poids ne sert qu'à départager. Seul, le conteneur « faible » prend tout le
processeur, et aucun arrêt n'est compté. Le noyau ne reprend pas la valeur
telle quelle : 1024 devient 100, et 256 devient 35.

## 🎛️ Exercice 4 : un réglage changé en marche

Bridez le conteneur qui tourne, essayez de lever la limite avec zéro, puis avec
le maximum :

```bash
C=$(cg essai-faible)
docker update --cpus 0.25 essai-faible > /dev/null
cat $C/cpu.max
docker update --cpus 0 essai-faible > /dev/null
cat $C/cpu.max
docker update --cpus 2 essai-faible > /dev/null
cat $C/cpu.max
docker inspect essai-faible --format '{{.State.Status}}, redemarrages : {{.RestartCount}}'
docker rm -f essai-faible > /dev/null
```

```text
25000 100000
25000 100000
200000 100000
running, redemarrages : 0
```

Le changement s'applique tout de suite. Mais zéro veut dire « ne rien changer
», pas « sans limite » : la commande réussit et la limite reste. Relisez
toujours le fichier après un `docker update`.

## 🚫 Exercice 5 : des demandes refusées

Demandez plus de processeurs que la machine n'en a, puis deux options qui
disent la même chose :

```bash
docker run --rm --cpus 8 "$IMAGE" true 2>&1 | grep -o 'range of CPUs.*'
docker run --rm --cpuset-cpus 5 "$IMAGE" true 2>&1 | grep -o 'Requested CPUs.*'
docker run --rm --cpus 0.5 --cpu-quota 50000 "$IMAGE" true 2>&1 | grep -o 'Conflicting options.*'
docker run --rm --cpu-period 10000 --cpu-quota 5000 "$IMAGE" cat /sys/fs/cgroup/cpu.max
```

```text
range of CPUs is from 0.01 to 2.00, as there are only 2 CPUs available
Requested CPUs are not available - requested 5, available: 0-1
Conflicting options: Nano CPUs and CPU Quota cannot both be set
5000 10000
```

Le démon compare la demande à la machine. Un fichier écrit pour un serveur à
huit processeurs peut donc échouer sur un poste qui en a deux. `--cpus` est un
raccourci du couple quota et période : on choisit l'un ou l'autre.

## 🧹 Nettoyage

```bash
cd ~
docker ps -aq --filter name=essai- | xargs -r docker rm -f > /dev/null
rm -rf ~/essai-cpu
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
dsoxlab reset container-limite-cpu
dsoxlab check container-limite-cpu
```

```text
╭─ Résultat : container-limite-cpu ─╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un conteneur lent à comprendre, un autre à épingler,
et une limite à prouver.

```bash
dsoxlab run container-limite-cpu
dsoxlab challenge container-limite-cpu
```
