# Revenir en arrière, et refuser le retour qui perdrait les données

La leçon met à jour par digest et montre qu'une migration ne se défait pas. Ce
cours s'intéresse à ce qui empêche un retour pourtant prévu : une étiquette qui
a bougé, une image devenue introuvable, une image absente de la machine, une
configuration restée en avant, et un code de refus perdu.

Vous travaillez dans `~/essai-retour`, sur un projet `essai-retour` et des
images `essai-appli`. Le challenge porte sur le projet `dsoxlab-retour` : n'y
touchez pas pendant le cours.

Page associée : [Mettre à jour, et revenir en arrière sans perdre les données](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/mettre-a-jour-et-revenir-en-arriere/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run compose-retour-arriere
```

Vous êtes connecté à `docker.lab`. La variable `COMPOSE_PROGRESS` fait taire
l'avancement de Compose : seuls les avertissements et les erreurs s'affichent.
La fonction `fabrique` construit une version sous une étiquette, `version` lit
celle qui tourne. **Gardez le même terminal jusqu'au nettoyage** : les
variables n'existent que dans lui.

```bash
mkdir -p ~/essai-retour && cd ~/essai-retour
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
fabrique() { printf 'FROM %s\nRUN echo %s > /version\nCMD ["sleep","600"]\n' "$IMAGE" "$1" > Dockerfile; docker build -q -t "essai-appli:$2" .; }
version() { docker compose exec appli cat /version; }
cat > compose.yaml <<'EOF'
services:
  appli:
    image: ${APPLI:-essai-appli:stable}
    init: true
    pull_policy: ${POLITIQUE:-missing}
    environment:
      MODE: ${MODE:-prudent}
EOF
ID1=$(fabrique 1 stable)
docker compose up -d
version
```

```text
5.6.1
1
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🏷️ Exercice 1 : une étiquette qui a bougé

Construisez la version 2 sous la même étiquette, redémarrez, puis réappliquez :

```bash
fabrique 2 stable > /dev/null
docker compose restart appli
version
docker compose up -d
version
docker inspect essai-retour-appli-1 --format '{{.Config.Image}}'
```

```text
1
2
essai-appli:stable
```

`restart` garde l'image d'origine, `up -d` prend celle que l'étiquette désigne
maintenant. Le fichier n'a pas changé d'un caractère, et l'inspection affiche
le même nom : rien n'y dit que la version a changé.

## 🕳️ Exercice 2 : une image devenue introuvable

Essayez de revenir à la version 1 par l'identifiant noté au départ :

```bash
docker image inspect "$ID1" > /dev/null 2>&1; echo "code: $?"
APPLI="essai-appli@$ID1" docker compose up -d 2>&1 | grep -o 'pull access denied for essai-appli'
version
```

```text
code: 1
pull access denied for essai-appli
2
```

L'étiquette déplacée, plus rien ne retenait la version 1 une fois son conteneur
remplacé. Compose la cherche alors dans un registry, où elle n'a jamais été
publiée. Le service, lui, continue sur la version 2 : l'échec n'a rien cassé,
mais il n'y a pas de retour.

## 📌 Exercice 3 : une étiquette par version

Construisez deux versions sous deux étiquettes, puis faites l'aller et le
retour :

```bash
fabrique 3 3.0 > /dev/null
fabrique 4 4.0 > /dev/null
APPLI=essai-appli:4.0 docker compose up -d; version
APPLI=essai-appli:3.0 docker compose up -d; version
docker compose config --images
APPLI=essai-appli:3.0 docker compose config --images
```

```text
4
3
essai-appli:stable
essai-appli:3.0
```

Chaque version garde son nom, donc son image : le retour marche. `config
--images` montre ce que Compose déploierait. Sans la variable, c'est encore
`stable` : écrivez la version dans un fichier, sinon le prochain `up -d`
l'oubliera.

## 📦 Exercice 4 : une image absente de la machine

Mettez la version 3 de côté dans un fichier, supprimez-la, puis revenez-y :

```bash
docker save essai-appli:3.0 -o appli-3.tar
APPLI=essai-appli:4.0 docker compose up -d
docker rmi essai-appli:3.0 > /dev/null
APPLI=essai-appli:3.0 POLITIQUE=never docker compose up -d
version
docker load -q -i appli-3.tar
APPLI=essai-appli:3.0 POLITIQUE=never docker compose up -d
version
```

```text
Error response from daemon: No such image: essai-appli:3.0
4
Loaded image: essai-appli:3.0
3
```

`pull_policy: never` refuse tout de suite, sans interroger un registry. Le
retour redevient possible quand l'image est rechargée. Avant une mise à jour,
vérifiez que l'ancienne image est sur la machine ou dans un registry joignable.

## 🧾 Exercice 5 : une configuration et un code de sortie

Revenez à l'ancienne image sans revenir à l'ancien réglage, puis lisez le code
d'un programme qui refuse :

```bash
MODE=rapide APPLI=essai-appli:4.0 docker compose up -d
export MODE=rapide
APPLI=essai-appli:3.0 docker compose up -d
docker compose exec appli printenv MODE
unset MODE
docker run --rm essai-appli:3.0 sh -c 'echo refus >&2; exit 9' 2>&1 | cat; echo "tube: $?"
docker run --rm essai-appli:3.0 sh -c 'exit 9'; echo "direct: $?"
docker run --name essai-garde essai-appli:3.0 sh -c 'exit 9'
docker inspect essai-garde --format '{{.State.ExitCode}}'
```

```text
rapide
refus
tube: 0
direct: 9
9
```

L'image est revenue, `MODE` est resté sur la nouvelle valeur : un retour
concerne l'image et sa configuration. Pour le code, le tube rend 0, celui de
`cat`. Lancé seul, `docker run` rend le code du programme, et l'inspection d'un
conteneur gardé le conserve.

## 🧹 Nettoyage

```bash
cd ~
docker compose -f ~/essai-retour/compose.yaml down
docker rm essai-garde > /dev/null
docker images --format '{{.Repository}}:{{.Tag}}' | grep '^essai-appli' | xargs docker rmi > /dev/null
rm -r ~/essai-retour
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
dsoxlab reset compose-retour-arriere
dsoxlab check compose-retour-arriere
```

```text
╭─ Résultat : compose-retour-arriere ─╮
│  0 / 100 pts                        │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests    │
╰─────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : trois versions, des données à garder, et un retour
qui ne sera plus possible.

```bash
dsoxlab run compose-retour-arriere
dsoxlab challenge compose-retour-arriere
```
