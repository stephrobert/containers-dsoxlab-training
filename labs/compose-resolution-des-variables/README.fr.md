# Résoudre les variables Compose sans mélanger les environnements

La leçon sépare l'interpolation du fichier et l'environnement du conteneur. Ce
cours ajoute cinq gestes : dresser la liste des variables attendues, écrire une
valeur conditionnelle, lire un fichier d'environnement absent, transmettre un
dollar, et un nom de projet qui change tout seul.

Vous travaillez dans `~/essai-valeurs`, sur un projet `essai-valeurs`. Le
challenge porte sur `/opt/lab-compose-vars` : n'y touchez pas pendant le cours.

Page associée : [Interpolation et fichiers d'environnement](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/variables-et-environnements/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run compose-resolution-des-variables
```

Vous êtes connecté à `docker.lab`. La variable `COMPOSE_PROGRESS` fait taire
l'avancement de Compose : seuls les avertissements et les erreurs s'affichent.
Écrivez un fichier à un service. **Gardez le même terminal jusqu'au nettoyage**
: les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-valeurs && cd ~/essai-valeurs
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
cat > compose.yaml <<'EOF'
services:
  app:
    image: ${IMAGE}
    init: true
    command: sleep 600
    environment:
      NIVEAU: ${NIVEAU:-normal}
      TRACE: ${DIAGNOSTIC:+active}
EOF
```

```text
5.6.1
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 📋 Exercice 1 : les variables attendues

Demandez la liste des variables que le fichier attend :

```bash
docker compose config --variables | awk '{print $1, $2, $3}' | sort
```

```text
DIAGNOSTIC false active
IMAGE false
NAME REQUIRED DEFAULT
NIVEAU false normal
```

Chaque ligne donne le nom, si la variable est obligatoire, et sa valeur par
défaut ou de remplacement. C'est la première chose à lire dans un
`compose.yaml` que vous n'avez pas écrit.

## 🎚️ Exercice 2 : une valeur conditionnelle

`${NOM:+texte}` donne `texte` quand la variable est définie, et rien sinon :

```bash
docker compose config | grep TRACE
DIAGNOSTIC=1 docker compose config | grep TRACE
DIAGNOSTIC= docker compose config | grep TRACE
```

```text
      TRACE: ""
      TRACE: active
      TRACE: ""
```

C'est l'inverse de `:-`. La valeur de `DIAGNOSTIC` n'apparaît jamais : seule sa
présence compte. Une variable vide équivaut ici à une variable absente.

## 📄 Exercice 3 : un fichier d'environnement absent

Ajoutez un fichier d'environnement qui n'existe pas, puis rendez-le facultatif
:

```bash
cat >> compose.yaml <<'EOF'
    env_file:
      - path: ./poste.env
        required: true
EOF
docker compose config -q 2>&1 | grep -o 'poste.env not found'
sed -i 's/required: true/required: false/' compose.yaml
docker compose config -q; echo "code: $?"
```

```text
poste.env not found
code: 0
```

Un `env_file` absent arrête tout, sauf avec `required: false`. Réservez cette
forme à un fichier propre à chaque poste : pour un fichier indispensable,
l'erreur est préférable à un conteneur incomplet.

## 💵 Exercice 4 : un dollar dans un fichier d'environnement

Écrivez une valeur qui contient un dollar, lisez ce que reçoit le conteneur,
puis changez de format :

```bash
echo 'CODE=ab$cd' > poste.env
docker compose run --rm app printenv CODE 2> /dev/null
sed -i 's/required: false/format: raw/' compose.yaml
docker compose run --rm app printenv CODE
docker compose run --rm -e CODE=ponctuel app printenv CODE
```

```text
ab
ab$cd
ponctuel
```

Par défaut, Compose développe aussi les valeurs d'un `env_file` : `$cd`,
introuvable, est devenu vide. `format: raw` transmet le texte tel quel.
L'option `-e` de `run` passe avant le fichier, pour cette commande seulement.

## 🏷️ Exercice 5 : un nom de projet qui change tout seul

Démarrez, ajoutez un nom de projet dans `.env`, puis cherchez votre conteneur :

```bash
docker compose up -d
echo 'COMPOSE_PROJECT_NAME=essai-autre' > .env
docker compose ps -q | wc -l
docker compose -p essai-valeurs ps --format '{{.Name}}'
COMPOSE_PROJECT_NAME=essai-shell docker compose config | head -1
docker compose -p essai-option config | head -1
```

```text
0
essai-valeurs-app-1
name: essai-shell
name: essai-option
```

Le `.env` règle aussi Compose lui-même. Ici le conteneur tourne toujours, mais
Compose regarde un autre projet. `-p` passe avant la variable du shell, qui
passe avant le `.env`. Quand une application semble disparue, lisez la ligne
`name:` de `config`.

## 🧹 Nettoyage

```bash
cd ~
docker compose -p essai-valeurs -f ~/essai-valeurs/compose.yaml down
rm -r ~/essai-valeurs
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
dsoxlab reset compose-resolution-des-variables
dsoxlab check compose-resolution-des-variables
```

```text
╭─ Résultat : compose-resolution-des-variables ─╮
│  0 / 100 pts                                  │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests              │
╰───────────────────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : une déclaration confuse, trois fichiers de valeurs,
et aucun à modifier.

```bash
dsoxlab run compose-resolution-des-variables
dsoxlab challenge compose-resolution-des-variables
```
