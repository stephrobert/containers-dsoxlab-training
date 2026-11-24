# Conserver les données après recréation Compose

La leçon suit les données d'une base à travers les recréations. Ce cours ajoute
cinq situations : des données qui semblent perdues, un volume que Compose ne
gère pas, une faute de nom, ce qu'un volume vide reçoit de l'image, et un
volume retiré du fichier.

Vous travaillez dans `~/essai-garde`, sur des projets et des volumes `essai-*`.
Le challenge porte sur le projet `dsoxlab-persistance` : n'y touchez pas
pendant le cours.

Page associée : [Persister les données d'une stack recréée](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/donnees-persistantes/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run compose-persistance
```

Vous êtes connecté à `docker.lab`. La variable `COMPOSE_PROGRESS` fait taire
l'avancement de Compose : seuls les avertissements et les erreurs s'affichent.
Écrivez un service et son volume, puis déposez-y une ligne. **Gardez le même
terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-garde && cd ~/essai-garde
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
cat > compose.yaml <<'EOF'
services:
  carnet:
    image: ${IMAGE}
    init: true
    command: sleep 600
    volumes:
      - pages:/pages
volumes:
  pages:
EOF
docker compose up -d
docker compose exec carnet sh -c 'echo ligne-1 > /pages/notes'
```

```text
5.6.1
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🫥 Exercice 1 : des données qui semblent perdues

Démarrez le même fichier sous un autre nom de projet :

```bash
docker compose -p essai-bis up -d
docker compose -p essai-bis exec carnet ls -A /pages | wc -l
docker volume ls --format '{{.Name}}' | grep essai
docker volume inspect essai-garde_pages --format '{{index .Labels "com.docker.compose.project"}}'
docker compose -p essai-bis down -v
```

```text
0
essai-bis_pages
essai-garde_pages
essai-garde
```

Le nom du volume contient celui du projet : renommer le dossier ou changer `-p`
fait créer un volume vide. Les données sont toujours dans le premier volume.
Son étiquette dit à quel projet il appartient.

## 🔒 Exercice 2 : un volume que Compose ne gère pas

Déclarez un volume externe, avant puis après l'avoir créé, et lancez un `down
-v` :

```bash
sed 's/^  pages:$/  pages: {external: true, name: essai-coffre}/' compose.yaml > externe.yaml
docker compose -p essai-ext -f externe.yaml up -d 2>&1 | grep -o 'external volume.*'
docker volume create essai-coffre
docker compose -p essai-ext -f externe.yaml up -d
docker compose -p essai-ext -f externe.yaml down -v
docker volume ls --format '{{.Name}}' | grep coffre
```

```text
external volume "essai-coffre" not found
essai-coffre
essai-coffre
```

Un volume externe se crée à part, et `down -v` ne l'efface pas. C'est une
protection contre une commande trop rapide, qui demande en échange de le créer
et de le supprimer vous-même.

## ✏️ Exercice 3 : une faute de nom

Faites une faute dans le nom du volume, puis oubliez le point d'un chemin
relatif :

```bash
sed 's/- pages:/- page:/' compose.yaml > faute.yaml
docker compose -f faute.yaml config -q 2>&1 | grep -o 'service.*'
sed 's|- pages:|- ./pages:|' compose.yaml > chemin.yaml
docker compose -f chemin.yaml config | grep -A1 'volumes:' | grep type
```

```text
service "carnet" refers to undefined volume page: invalid compose project
      - type: bind
```

Compose refuse un nom qui n'est pas déclaré en bas du fichier. Avec `./`, il ne
cherche plus un volume mais un répertoire de l'hôte : le type passe de `volume`
à `bind`, et les données changent d'endroit sans aucune erreur. Vérifiez le
type dans `config`.

## 📦 Exercice 4 : ce qu'un volume vide reçoit de l'image

Montez deux volumes vides sur des répertoires que l'image remplit, l'un avec
`nocopy` :

```bash
cat > copie.yaml <<'EOF'
services:
  app:
    image: ${IMAGE}
    init: true
    command: sleep 600
    volumes:
      - avec:/etc/apk
      - type: volume
        source: sans
        target: /etc/ssl
        volume:
          nocopy: true
volumes:
  avec:
  sans:
EOF
docker compose -p essai-copie -f copie.yaml up -d
docker compose -p essai-copie -f copie.yaml exec app sh -c 'ls -A /etc/apk | wc -l; ls -A /etc/ssl | wc -l'
docker compose -p essai-copie -f copie.yaml down -v
```

```text
5
0
```

Le premier volume a reçu les fichiers de l'image, le second est resté vide. La
copie n'a lieu qu'une fois, quand le volume est vide : une image plus récente
n'y changera rien.

## 🗂️ Exercice 5 : un volume retiré du fichier

Retirez le volume du fichier, appliquez, puis lancez `down -v` :

```bash
sed -i '/volumes:/d;/pages/d' compose.yaml
docker compose up -d
docker compose down -v
docker volume ls --format '{{.Name}}' | grep garde
docker run --rm -v essai-garde_pages:/p "$IMAGE" cat /p/notes
```

```text
essai-garde_pages
ligne-1
```

`down -v` ne supprime que les volumes que le fichier déclare encore. Le volume
retiré du fichier reste sur la machine avec ses données : vous pouvez les
relire, et c'est aussi lui qui remplit le disque si personne ne le cherche.

## 🧹 Nettoyage

```bash
cd ~
docker volume rm essai-garde_pages essai-coffre
rm -r ~/essai-garde
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker network ls --format '{{.Name}}' | grep -c '^essai-'
docker volume ls --format '{{.Name}}' | grep -c '^essai-'
```

```text
essai-garde_pages
essai-coffre
0
0
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset compose-persistance
dsoxlab check compose-persistance
```

```text
╭─ Résultat : compose-persistance ──╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests  │
╰───────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : des écritures qui doivent survivre à la disparition
de leur conteneur.

```bash
dsoxlab run compose-persistance
dsoxlab challenge compose-persistance
```
