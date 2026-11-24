# Séparer les réseaux de façade et de données avec Compose

La leçon répartit les services sur plusieurs réseaux et teste chaque chemin. Ce
cours ajoute cinq situations : un nom valable d'un seul côté, un raccordement à
chaud qui ne dure pas, deux fautes de déclaration, un réseau partagé entre deux
projets, et un réseau que `down` ne retire pas.

Vous travaillez dans `~/essai-cotes`, sur les projets `essai-cotes` et
`essai-voisin`. Le challenge porte sur le projet `dsoxlab-isolation-reseau` :
n'y touchez pas pendant le cours.

Page associée : [Organiser les réseaux d'une stack](https://www.stephane-robert.info/docs/conteneurs/orchestrateurs/docker-compose/reseaux/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run compose-isolation-reseau
```

Vous êtes connecté à `docker.lab`. La variable `COMPOSE_PROGRESS` fait taire
l'avancement de Compose : seuls les avertissements et les erreurs s'affichent.
Écrivez trois services, puis une fonction qui dit si l'un joint l'autre.
**Gardez le même terminal jusqu'au nettoyage** : les variables n'existent que
dans lui.

```bash
mkdir -p ~/essai-cotes && cd ~/essai-cotes
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
cat > compose.yaml <<'EOF'
x-base: &base
  image: ${IMAGE}
  init: true
  command: sleep 600
services:
  pont:
    <<: *base
    networks:
      rive-a:
        aliases:
          - passage
      rive-b:
  gauche:
    <<: *base
    networks:
      - rive-a
  droite:
    <<: *base
    networks:
      - rive-b
networks:
  rive-a:
  rive-b:
EOF
joint() { docker compose exec "$1" ping -c1 -W2 "$2" > /dev/null 2>&1 && echo "$1 joint $2" || echo "$1 ne joint pas $2"; }
docker compose up -d
```

```text
5.6.1
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🏷️ Exercice 1 : un nom valable d'un seul côté

Le service `pont` porte un second nom, `passage`, sur `rive-a` seulement :

```bash
joint gauche passage
joint droite passage
joint droite pont
```

```text
gauche joint passage
droite ne joint pas passage
droite joint pont
```

Un alias appartient au réseau où il est déclaré, pas au service. `droite`
connaît `pont` sous son nom de service, et ne connaît pas `passage`.

## 🔌 Exercice 2 : un raccordement à chaud

Raccordez `gauche` à `rive-b` à la main, puis recréez-le :

```bash
joint gauche droite
docker network connect essai-cotes_rive-b essai-cotes-gauche-1
joint gauche droite
docker compose up -d --force-recreate gauche
joint gauche droite
```

```text
gauche ne joint pas droite
gauche joint droite
gauche ne joint pas droite
```

Le raccordement manuel marche tout de suite, et disparaît à la recréation :
seul le fichier fait foi. Une isolation, ou un chemin, que le fichier ne décrit
pas ne tient pas.

## 🚫 Exercice 3 : deux fautes de déclaration

Faites valider un réseau non déclaré, puis un service sans réseau qui en
demande un :

```bash
sed '/  gauche:/,/  droite:/s/- rive-a/- rive-z/' compose.yaml > faute.yaml
docker compose -f faute.yaml config -q 2>&1 | grep -o 'service.*'
sed '/  gauche:/a\    network_mode: none' compose.yaml > mode.yaml
docker compose -f mode.yaml config -q 2>&1 | grep -o 'service.*'
```

```text
service "gauche" refers to undefined network rive-z: invalid compose project
service gauche declares mutually exclusive `network_mode` and `networks`: invalid compose project
```

Compose refuse les deux avant de créer quoi que ce soit. Un nom de réseau doit
figurer dans le bloc `networks:` du bas, et `network_mode` s'emploie à la place
de `networks:`, jamais avec lui.

## 🤝 Exercice 4 : un réseau partagé entre deux projets

Un second projet se raccorde à un réseau qu'il ne crée pas :

```bash
cat > voisin.yaml <<'EOF'
services:
  visiteur:
    image: ${IMAGE}
    init: true
    command: sleep 600
    networks:
      - commun
networks:
  commun:
    external: true
    name: ${RESEAU}
EOF
RESEAU=essai-absent docker compose -p essai-voisin -f voisin.yaml up -d 2>&1 | grep -o 'network essai-absent.*'
export RESEAU=essai-cotes_rive-b
docker compose -p essai-voisin -f voisin.yaml up -d
docker compose -p essai-voisin -f voisin.yaml exec visiteur ping -c1 -W2 droite | grep -o '1 packets received'
```

```text
network essai-absent declared as external, but could not be found
1 packets received
```

`external: true` dit à Compose que le réseau existe déjà : il ne le crée pas et
ne le supprimera pas. Absent, c'est une erreur. Présent, il fait entrer
`visiteur` dans `rive-b`, où il joint `droite`. Vérifiez donc aussi qui, hors
de votre fichier, est raccordé à vos réseaux.

## 🧷 Exercice 5 : un réseau que `down` ne retire pas

Arrêtez le premier projet alors que le second occupe encore son réseau :

```bash
docker compose down
docker network ls --format '{{.Name}}' | grep essai-cotes
docker network inspect essai-cotes_rive-b --format '{{range .Containers}}{{.Name}} {{end}}'
docker compose -p essai-voisin -f voisin.yaml down
docker compose down
docker network ls --format '{{.Name}}' | grep -c essai-cotes
```

```text
essai-cotes_rive-b
essai-voisin-visiteur-1
0
```

Docker ne supprime pas un réseau occupé. `docker network inspect` donne
l'occupant. Une fois celui-ci parti, un second `down` retire le réseau.

## 🧹 Nettoyage

```bash
cd ~
rm -r ~/essai-cotes
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
dsoxlab reset compose-isolation-reseau
dsoxlab check compose-isolation-reseau
```

```text
╭─ Résultat : compose-isolation-reseau ─╮
│  0 / 100 pts                          │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests      │
╰───────────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : trois services, deux zones, et un chemin qui doit
rester fermé.

```bash
dsoxlab run compose-isolation-reseau
dsoxlab challenge compose-isolation-reseau
```
