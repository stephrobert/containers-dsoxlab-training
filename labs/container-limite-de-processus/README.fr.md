# Plafonner le nombre de tâches du conteneur

La leçon pose un plafond de tâches et lit son compteur de refus. Ce cours
s'occupe du choix de la valeur et de ses effets : où l'écrire, combien de
places laisser, ce qui arrive quand on la baisse en marche, une sonde de santé
qui échoue à cause d'elle, et un service qui meurt d'un simple refus.

Vous travaillez sur des conteneurs `essai-*`. Le challenge porte sur le service
`worker` et sur `/opt/dsoxlab-container-limite-de-processus` : n'y touchez pas
pendant le cours. Toutes les rafales du cours sont finies : n'en lancez pas
d'autres.

Page associée : [Plafonner la mémoire et le nombre de tâches](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/memoire-et-taches/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run container-limite-de-processus
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `cg` rend le répertoire
du cgroup d'un conteneur ; `dormeurs` y lance un nombre fini de `sleep`.
**Gardez le même terminal jusqu'au nettoyage** : les variables n'existent que
dans lui.

```bash
mkdir -p ~/essai-taches && cd ~/essai-taches
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
cg() { echo /sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' "$1").scope; }
dormeurs() { docker exec -d "$1" sh -c "i=0; while [ \$i -lt $2 ]; do sleep $3 & i=\$((i+1)); done; wait"; sleep 1; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 📝 Exercice 1 : où écrire la valeur

Compose accepte deux écritures. Mélangez-les, gardez-en une, puis changez-la :

```bash
cat > compose.yaml <<EOF
services:
  app:
    image: $IMAGE
    container_name: essai-app
    network_mode: none
    init: true
    pids_limit: 30
    deploy: {resources: {limits: {pids: 12}}}
    command: sleep 600
EOF
docker compose up -d 2>&1 | grep -o "can't set distinct values.*"
sed -i '/pids_limit/d' compose.yaml
docker compose up -d 2> /dev/null; cat $(cg essai-app)/pids.max
sed -i 's/pids: 12/pids: 14/' compose.yaml
docker compose restart -t 1 2> /dev/null; cat $(cg essai-app)/pids.max
docker compose up -d -t 1 2> /dev/null; cat $(cg essai-app)/pids.max
```

```text
can't set distinct values on 'pids_limit' and 'deploy.resources.limits.pids': invalid compose project
12
12
14
```

Deux valeurs différentes pour un même réglage, et Compose refuse tout. Ensuite,
`restart` garde l'ancien plafond : seul `up -d` relit le fichier et recrée le
conteneur. Vérifiez toujours dans `pids.max`.

## 🪑 Exercice 2 : combien de places laisser

Cherchez à partir de quel plafond on peut encore entrer dans un conteneur qui
ne fait rien, et lisez la pointe :

```bash
for n in 3 5 12; do
  docker run -d --name essai-n --pids-limit $n "$IMAGE" sleep 600 > /dev/null
  docker exec essai-n true > /dev/null 2>&1 && echo "$n : exec passe" || echo "$n : exec refuse"
  [ $n = 12 ] && [ "$(cat $(cg essai-n)/pids.peak)" -gt 4 ] && echo "au repos : $(cat $(cg essai-n)/pids.current), pointe : plus de 4"
  docker rm -f essai-n > /dev/null
done
```

```text
3 : exec refuse
5 : exec refuse
12 : exec passe
au repos : 1, pointe : plus de 4
```

Un `docker exec` d'une commande minuscule prend plusieurs places pendant un
instant, car l'outil qui le lance en occupe aussi. Le compte au repos ne le
montre pas ; `pids.peak` garde le maximum atteint. Réglez le plafond sur la
pointe mesurée, avec de la place pour un diagnostic. Le nombre exact dépend de
la machine : sur la nôtre, entre 6 et 7 la réponse change d'un essai à l'autre.

## 📉 Exercice 3 : baisser sous l'usage courant

Lancez six `sleep`, puis baissez le plafond sous ce que le conteneur occupe
déjà :

```bash
docker run -d --init --name essai-p "$IMAGE" sleep 600 > /dev/null
dormeurs essai-p 6 300
C=$(cg essai-p)
docker update --pids-limit 4 essai-p > /dev/null
echo "$(cat $C/pids.current) taches, plafond $(cat $C/pids.max)"
docker exec essai-p sh -c 'sleep 0 & wait' 2>&1 | grep -o "can't fork"
docker top essai-p -o pid,args | grep -cE '^[0-9]+ +sleep 300'
docker exec essai-p pkill -f 'sleep 300'; sleep 1
echo "$(cat $C/pids.current) taches"
docker update --pids-limit 20 essai-p > /dev/null
docker exec essai-p sh -c 'sleep 0 & wait' && echo 'de nouveau possible'
```

```text
9 taches, plafond 4
can't fork
6
2 taches
de nouveau possible
```

Le plafond refuse les naissances, il ne tue personne : les six `sleep` ont
continué. `docker top` lit depuis la machine et n'a besoin d'aucune place. Ce
comportement diffère de la mémoire, où baisser trop bas peut tuer.

## 🩺 Exercice 4 : une sonde de santé victime du plafond

Ajoutez une sonde qui répond toujours oui, remplissez le conteneur pendant
douze secondes, et suivez son état :

```bash
docker run -d --init --name essai-h --pids-limit 20 --health-cmd true --health-interval 2s --health-retries 2 "$IMAGE" sleep 600 > /dev/null
sleep 3; docker inspect essai-h --format '{{.State.Health.Status}}'
dormeurs essai-h 16 12
echo "$(cat $(cg essai-h)/pids.current) sur 20"
sleep 7; docker inspect essai-h --format '{{.State.Status}}, {{.State.Health.Status}}'
docker inspect essai-h --format '{{json .State.Health.Log}}' | grep -o 'Resource temporarily unavailable' | sort -u
sleep 10; docker inspect essai-h --format '{{.State.Status}}, {{.State.Health.Status}}'
```

```text
healthy
19 sur 20
running, unhealthy
Resource temporarily unavailable
running, healthy
```

La sonde est un `docker exec` : sans place, elle échoue, et un service qui
marche est déclaré malade. Le journal de santé donne la vraie cause. Un outil
qui redémarre les conteneurs malades aggraverait l'incident. Dernier piège
mesuré sur cette machine : à 20 tâches sur 20, `docker exec` est passé, à 19 il
a échoué ; nous n'en avons pas établi la cause. Fiez-vous à `pids.current` et à
`pids.events`, pas au seul `docker exec`.

## 💀 Exercice 5 : mourir d'un simple refus

Faites porter la même rafale par le premier processus du conteneur, puis par un
enfant :

```bash
B='i=0; while [ $i -lt 40 ]; do sleep 2 & i=$((i+1)); done; wait'
docker run -d --name essai-fragile --pids-limit 12 "$IMAGE" sh -c "$B; sleep 600" > /dev/null
docker run -d --init --name essai-solide --pids-limit 12 "$IMAGE" sh -c "($B) || echo 'lot refuse, je continue'; sleep 600" > /dev/null
sleep 4
for c in essai-fragile essai-solide; do docker inspect $c --format '{{.Name}} {{.State.Status}} {{.State.ExitCode}} {{.State.OOMKilled}}'; docker logs $c 2>&1; done
```

```text
/essai-fragile exited 2 false
sh: can't fork: Resource temporarily unavailable
/essai-solide running 0 false
sh: can't fork: Resource temporarily unavailable
lot refuse, je continue
```

Le noyau a refusé de la même façon dans les deux cas. Le premier shell
abandonne au refus, et comme il est le premier processus, tout s'arrête avec le
code 2. Dans le second, c'est un enfant qui abandonne. Un plafond ne protège
bien qu'un programme qui sait recevoir un refus.

## 🧹 Nettoyage

```bash
cd ~
docker ps -aq --filter name=essai- | xargs -r docker rm -f > /dev/null
rm -rf ~/essai-taches
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
dsoxlab reset container-limite-de-processus
dsoxlab check container-limite-de-processus
```

```text
╭─ Résultat : container-limite-de-processus ─╮
│  0 / 100 pts                               │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests           │
╰────────────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un service à remettre dans son budget de tâches, et
qui doit rester debout.

```bash
dsoxlab run container-limite-de-processus
dsoxlab challenge container-limite-de-processus
```
