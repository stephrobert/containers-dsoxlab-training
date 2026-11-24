# Faire appliquer les budgets Compose par le moteur

La leçon pose trois limites et lit ce que le noyau applique. Ce cours ajoute
cinq situations : une réservation qui ne limite rien, deux écritures qui se
contredisent, des valeurs que le moteur refuse, une limite par conteneur et non
par service, et les limites d'un processus.

Vous travaillez dans `~/essai-budget`, sur un projet `essai-budget`. Le
challenge porte sur le projet `dsoxlab-ressources` : n'y touchez pas pendant le
cours.

Page associée : [Encadrer ressources et redémarrage d'une stack](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/ressources-et-redemarrage/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run compose-ressources
```

Vous êtes connecté à `docker.lab`. La variable `COMPOSE_PROGRESS` fait taire
l'avancement de Compose : seuls les avertissements et les erreurs s'affichent.
La fonction `noyau` affiche des réglages du cgroup, lus dans le conteneur.
**Gardez le même terminal jusqu'au nettoyage** : les variables n'existent que
dans lui.

```bash
mkdir -p ~/essai-budget && cd ~/essai-budget
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
noyau() { for f in "$@"; do printf '%s = ' "$f"; docker compose exec ouvrier cat "/sys/fs/cgroup/$f"; done; }
nproc
```

```text
5.6.1
2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🪑 Exercice 1 : une réservation n'est pas une limite

Donnez à un service une réservation de mémoire et un poids de processeur :

```bash
cat > compose.yaml <<'EOF'
services:
  ouvrier:
    image: ${IMAGE}
    init: true
    command: sleep 600
    mem_reservation: 24m
    cpu_shares: 256
EOF
docker compose up -d
noyau memory.low memory.max cpu.weight cpu.max
```

```text
memory.low = 25165824
memory.max = max
cpu.weight = 35
cpu.max = max 100000
```

`memory.max` et `cpu.max` valent `max` : rien n'est plafonné. La réservation
protège 24 Mio quand la mémoire manque, et le poids départage les conteneurs
quand le processeur est saturé. Seul, ce service peut tout prendre.

## ⚔️ Exercice 2 : deux écritures qui se contredisent

Écrivez deux limites de mémoire différentes pour le même service :

```bash
cat > double.yaml <<'EOF'
services:
  ouvrier:
    image: ${IMAGE}
    mem_limit: 48m
    deploy:
      resources:
        limits:
          memory: 64M
EOF
docker compose -f double.yaml config -q
```

```text
services.ouvrier: can't set distinct values on 'mem_limit' and 'deploy.resources.limits.memory': invalid compose project
```

Compose refuse de choisir. Le cas arrive vite quand un second fichier ajoute
`deploy` à un service déjà limité par la forme courte.

## 🙅 Exercice 3 : des valeurs que le moteur refuse

Demandez plus de cœurs que l'hôte n'en a, un cœur qui n'existe pas, puis trop
peu de mémoire :

```bash
cat > refus.yaml <<'EOF'
services:
  ouvrier:
    image: ${IMAGE}
    init: true
    command: sleep 600
    cpus: "${PART:-0.2}"
    cpuset: "${COEURS:-0}"
    mem_limit: ${MEMOIRE:-32m}
EOF
PART=64 docker compose -f refus.yaml config -q; echo "code: $?"
PART=64 docker compose -f refus.yaml up -d
COEURS=63 docker compose -f refus.yaml up -d
MEMOIRE=2m docker compose -f refus.yaml up -d
docker compose -f refus.yaml up -d
docker compose exec ouvrier nproc
```

```text
code: 0
Error response from daemon: range of CPUs is from 0.01 to 2.00, as there are only 2 CPUs available
Error response from daemon: Requested CPUs are not available - requested 63, available: 0-1
Error response from daemon: Minimum memory limit allowed is 6MB
1
```

`config` accepte tout : seul le moteur connaît l'hôte, et il refuse à la
création. Une même déclaration peut donc démarrer sur une machine et échouer
sur une autre. Le dernier essai est valide, et `cpuset` ne laisse qu'un cœur
visible.

## 👯 Exercice 4 : une limite par conteneur

Passez le service à trois conteneurs et lisez la limite de chacun :

```bash
docker compose -f refus.yaml up -d --scale ouvrier=3
for i in 1 2 3; do docker inspect essai-budget-ouvrier-$i --format '{{.HostConfig.Memory}}'; done
docker compose -f refus.yaml stats --no-stream --format '{{.MemUsage}}' | cut -d/ -f2
docker compose -f refus.yaml up -d
```

```text
33554432
33554432
33554432
 32MiB
 32MiB
 32MiB
```

Chaque conteneur a droit à 32 Mio : le service entier peut donc en prendre 96.
La limite ne se partage pas, et multiplier un service multiplie son budget.

## 📏 Exercice 5 : les limites d'un processus

Bornez la taille des fichiers et le nombre de fichiers ouverts, puis lisez le
pic de mémoire du conteneur :

```bash
cat > compose.yaml <<'EOF'
services:
  ouvrier:
    image: ${IMAGE}
    init: true
    command: sleep 600
    mem_limit: 40m
    ulimits:
      nofile: 32
      fsize: 1048576
EOF
docker compose up -d
docker compose exec ouvrier sh -c 'ulimit -n; dd if=/dev/zero of=/tmp/gros bs=1M count=3 2> /dev/null; echo "code: $?"; du -k /tmp/gros'
docker compose exec ouvrier dd if=/dev/zero of=/dev/null bs=20M count=2 2> /dev/null
docker compose exec ouvrier awk '{print ($1 > 20000000) ? "pic au-dela de 20 Mo" : "pic faible"}' /sys/fs/cgroup/memory.peak
```

```text
32
code: 153
1024	/tmp/gros
pic au-dela de 20 Mo
```

Le noyau arrête le processus qui dépasse 1 Mio dans un fichier, avec le code
153 (128 + 25, SIGXFSZ) : le conteneur, lui, continue. `ulimits` s'applique à
chaque processus, le cgroup au conteneur entier. `memory.peak` garde le plus
haut atteint : lisez-le avant de choisir une limite.

## 🧹 Nettoyage

```bash
cd ~
docker compose -f ~/essai-budget/compose.yaml down
rm -r ~/essai-budget
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker network ls --format '{{.Name}}' | grep -c '^essai-'
docker volume ls --format '{{.Name}}' | grep -c '^essai-'
```

```text
0
0
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset compose-ressources
dsoxlab check compose-ressources
```

```text
╭── Résultat : compose-ressources ──╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests  │
╰───────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : trois budgets à poser, et à retrouver dans le noyau
après une recréation.

```bash
dsoxlab run compose-ressources
dsoxlab challenge compose-ressources
```
