# Démarrer et recréer une application Compose à deux services

La leçon écrit un premier fichier, le démarre et l'arrête. Ce cours ajoute cinq
situations du quotidien : simuler avant d'agir, lancer une commande ponctuelle,
multiplier un service, un redémarrage qui n'applique rien, et un service
renommé.

Vous travaillez dans `~/essai-duo`, sur un projet `essai-duo`. Le challenge
porte sur le projet `dsoxlab-premiere-stack` : n'y touchez pas pendant le
cours.

Page associée : [Décrire une application avec Compose : une première stack](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run compose-premiere-stack
```

Vous êtes connecté à `docker.lab`. La variable `COMPOSE_PROGRESS` fait taire
l'avancement de Compose : seuls les avertissements et les erreurs s'affichent.
Écrivez un fichier à deux services. **Gardez le même terminal jusqu'au
nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-duo && cd ~/essai-duo
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
cat > compose.yaml <<'EOF'
services:
  calcul:
    image: ${IMAGE}
    init: true
    command: sleep 600
  vitrine:
    image: ${IMAGE}
    init: true
    command: sleep 600
    ports:
      - "127.0.0.1:18501:80"
EOF
```

```text
5.6.1
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🧪 Exercice 1 : simuler avant d'agir

Demandez à Compose ce qu'il ferait, puis comptez les conteneurs du projet :

```bash
COMPOSE_PROGRESS=plain docker compose --dry-run up -d 2>&1 | grep -E 'Created|Started' | sort -u
docker compose ps -aq | wc -l
```

```text
 Container essai-duo-calcul-1 Created
 Container essai-duo-calcul-1 Started
 Container essai-duo-vitrine-1 Created
 Container essai-duo-vitrine-1 Started
 Network essai-duo_default Created
0
```

`--dry-run` annonce chaque action et n'en exécute aucune. Il complète `docker
compose config`, qui montre le fichier résolu mais pas les actions à venir.

## 🎯 Exercice 2 : une commande ponctuelle

Démarrez, puis comparez `exec` et `run` sur le même service :

```bash
docker compose up -d
docker compose exec vitrine sh -c 'echo trace > /tmp/trace; cat /tmp/trace'
docker compose run --rm vitrine cat /tmp/trace
docker compose run --rm --service-ports vitrine true 2>&1 | grep -o 'port is already allocated'
docker compose ps -a --format '{{.Service}} {{.State}}'
```

```text
trace
cat: can't open '/tmp/trace': No such file or directory

port is already allocated
calcul running
vitrine running
```

`exec` entre dans le conteneur qui tourne. `run` en crée un autre depuis la
même description : il ne voit pas le fichier de son voisin. Il ne publie pas
les ports du service, et lui en faire la demande échoue ici puisque le port est
déjà pris. `--rm` le retire à la fin.

## 👯 Exercice 3 : plusieurs conteneurs pour un service

Passez `calcul` à trois conteneurs, comptez les adresses derrière son nom, puis
essayez de doubler `vitrine` :

```bash
docker compose up -d --scale calcul=3
docker compose exec vitrine nslookup calcul 2>&1 | grep -c '^Address: *172'
docker compose up -d --scale calcul=3 --scale vitrine=2 2>&1 | grep -o 'port is already allocated'
docker compose ps -a --format '{{.Name}} {{.State}}' | sort
docker compose up -d
```

```text
3
port is already allocated
essai-duo-calcul-1 running
essai-duo-calcul-2 running
essai-duo-calcul-3 running
essai-duo-vitrine-1 running
essai-duo-vitrine-2 created
```

Le nom `calcul` désigne trois adresses. `vitrine` ne se double pas : son port
de l'hôte est fixe, et un seul conteneur peut l'occuper. Le second reste dans
l'état `created`. Le dernier `up -d` revient à un conteneur par service.

## 🔁 Exercice 4 : un redémarrage qui n'applique rien

Changez la commande de `calcul` dans le fichier, redémarrez-le, puis appliquez
le fichier :

```bash
sed -i '/calcul:/,/command/s/sleep 600/sleep 601/' compose.yaml
docker compose restart calcul
docker compose ps --no-trunc --format '{{.Service}} {{.Command}}'
docker compose up -d
docker compose ps --no-trunc --format '{{.Service}} {{.Command}}'
```

```text
calcul "sleep 600"
vitrine "sleep 600"
calcul "sleep 601"
vitrine "sleep 600"
```

`restart` arrête et relance le conteneur existant, sans relire le fichier. `up
-d` compare le fichier au conteneur et recrée celui qui diffère. Après une
modification, c'est `up -d` qu'il faut.

## 👻 Exercice 5 : un service renommé

Renommez `calcul` en `moteur` dans le fichier, puis démarrez :

```bash
sed -i 's/^  calcul:/  moteur:/' compose.yaml
docker compose up -d 2>&1 | grep -o 'Found orphan containers ([^)]*)'
docker compose ps --format '{{.Service}}' | sort
docker compose up -d --remove-orphans
docker compose ps --format '{{.Service}}' | sort
```

```text
Found orphan containers (essai-duo-calcul-1)
calcul
moteur
vitrine
moteur
vitrine
```

Pour Compose, renommer un service revient à en ajouter un : l'ancien conteneur
continue de tourner, sans être décrit nulle part. Il avertit, et
`--remove-orphans` retire ce que le fichier ne décrit plus.

## 🧹 Nettoyage

```bash
cd ~
docker compose -f ~/essai-duo/compose.yaml down
rm -r ~/essai-duo
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
dsoxlab reset compose-premiere-stack
dsoxlab check compose-premiere-stack
```

```text
╭─ Résultat : compose-premiere-stack ─╮
│  0 / 100 pts                        │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests    │
╰─────────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : deux images prêtes, aucun fichier, et une application
à décrire.

```bash
dsoxlab run compose-premiere-stack
dsoxlab challenge compose-premiere-stack
```
