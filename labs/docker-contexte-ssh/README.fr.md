# Administrer une seconde VM avec un contexte Docker SSH

La leçon crée un contexte SSH et prouve qu'il joint l'autre moteur. Ce cours
montre comment on se trompe de moteur : un contexte resté actif, une variable
qui passe devant, un contexte que l'on ne peut pas retirer, une adresse
acceptée sans être vérifiée, et un contexte que l'on transporte.

Vous travaillez dans `~/essai-contextes`, avec un dossier de configuration
Docker à part : vos vrais contextes ne sont pas touchés. Le challenge porte sur
la VM `docker-client.lab` : ne la joignez pas pendant le cours.

Page associée : [Administrer le démon et ses contextes](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/daemon-config/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run docker-contexte-ssh
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `DOCKER_CONFIG` désigne
le dossier à part. Deux contextes : l'un mène au moteur local, l'autre à un
port où rien n'écoute. **Gardez le même terminal jusqu'au nettoyage** : les
variables n'existent que dans lui.

```bash
mkdir -p ~/essai-contextes && cd ~/essai-contextes
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
mkdir reglages && export DOCKER_CONFIG="$PWD/reglages"
docker context create essai-local --docker host=unix:///run/docker.sock > /dev/null 2>&1
docker context create essai-mort --docker host=tcp://127.0.0.1:1 > /dev/null 2>&1
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 📌 Exercice 1 : un contexte resté actif

Rendez un contexte actif, puis visez-en un autre pour une seule commande :

```bash
docker context use essai-mort > /dev/null 2>&1
docker ps 2>&1 | grep -o 'Cannot connect.*1\.'
docker --context essai-local version --format '{{.Server.Version}}'
DOCKER_CONTEXT=essai-local docker context show
docker context show
```

```text
Cannot connect to the Docker daemon at tcp://127.0.0.1:1.
29.9.2
essai-local
essai-mort
```

`context use` vaut pour tous les terminaux et toutes les sessions suivantes.
`--context` vaut pour une commande, `DOCKER_CONTEXT` pour un terminal. Avant
une commande qui supprime, affichez `docker context show`.

## 🎭 Exercice 2 : une variable qui passe devant

Définissez `DOCKER_HOST` pendant que le contexte cassé est actif :

```bash
DOCKER_HOST=unix:///run/docker.sock docker version --format '{{.Server.Version}}'
DOCKER_HOST=unix:///run/docker.sock docker context show
DOCKER_HOST=unix:///run/docker.sock docker context use essai-local 2>&1 | grep -o 'DOCKER_HOST environment variable overrides the active context'
```

```text
29.9.2
default
DOCKER_HOST environment variable overrides the active context
```

`DOCKER_HOST` l'emporte sur le contexte actif, sans bruit : la commande marche
alors que le contexte est cassé, et `context show` affiche `default`. C'est la
première variable à regarder quand une commande ne vise pas le moteur attendu.

## 🧷 Exercice 3 : un contexte que l'on ne peut pas retirer

Retirez le contexte actif, puis le contexte par défaut :

```bash
docker context rm essai-local 2>&1 | grep -o 'is in use'
docker context rm default 2>&1 | grep -o 'cannot be removed'
docker context use default > /dev/null 2>&1
docker context rm essai-local
docker context ls --format '{{.Name}} {{.Current}}'
```

```text
is in use
cannot be removed
essai-local
default true
essai-mort false
```

Docker refuse de retirer le contexte actif. Retirer un contexte n'arrête rien
sur la machine distante et ne révoque aucune clé : il n'efface qu'une adresse
chez vous.

## ✍️ Exercice 4 : une adresse acceptée sans être vérifiée

Créez un contexte vers un hôte inconnu, puis un autre avec un protocole absurde
:

```bash
docker context create essai-loin --docker host=ssh://essai-inconnu 2> /dev/null
docker --context essai-loin ps 2>&1 | grep -oE 'exit status [0-9]+' | head -1
ssh -o ConnectTimeout=3 -o BatchMode=yes essai-inconnu true 2>&1 | grep -o 'Could not resolve hostname'
docker context create essai-absurde --docker host=ftp://a 2> /dev/null
docker context create essai-loin 2>&1 | grep -o 'already exists'
```

```text
essai-loin
exit status 255
Could not resolve hostname
essai-absurde
already exists
```

La création réussit dans les deux cas : elle n'essaie pas de se connecter.
L'erreur vient plus tard, et le message de Docker cache celui de `ssh`. Essayez
toujours `ssh` seul d'abord, avec le même nom : lui dit pourquoi.

## 🧳 Exercice 5 : un contexte que l'on transporte

Exportez un contexte, regardez ce que contient le fichier, puis réimportez-le :

```bash
docker context export essai-loin loin.ctx
tar tf loin.ctx
tar xOf loin.ctx meta.json | grep -o '"Host":"[^"]*"'
docker context import essai-copie loin.ctx 2> /dev/null
docker context inspect essai-copie --format '{{.Endpoints.docker.Host}}'
```

```text
Written file "loin.ctx"
meta.json
tls
"Host":"ssh://essai-inconnu"
essai-copie
ssh://essai-inconnu
```

Pour un contexte SSH, le fichier ne porte qu'une adresse : ni clé, ni mot de
passe, ni réglage de `~/.ssh/config`. Chez un collègue, l'alias doit donc
exister aussi. Pour un contexte en TLS, en revanche, l'export contient les clés
: il se protège comme elles.

## 🧹 Nettoyage

```bash
cd ~
unset DOCKER_CONFIG
rm -rf ~/essai-contextes
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
dsoxlab reset docker-contexte-ssh
dsoxlab check docker-contexte-ssh
```

```text
╭─ Résultat : docker-contexte-ssh ──╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/2 tests  │
╰───────────────────────────────────╯
```

0 sur 2 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un second moteur à joindre, et un premier qui doit
rester celui par défaut.

```bash
dsoxlab run docker-contexte-ssh
dsoxlab challenge docker-contexte-ssh
```
