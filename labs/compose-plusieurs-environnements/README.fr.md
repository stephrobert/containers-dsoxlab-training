# Déployer des projets Compose de développement et production isolés

La leçon transfère un artefact et sépare deux environnements. Ce cours détaille
la fusion de deux fichiers, là où l'on se trompe : des listes qui s'ajoutent,
un ordre inversé, un chemin qui part d'ailleurs, un nom de projet qui change,
et une différence que Compose ne voit pas.

Vous travaillez dans `~/essai-fusion`, sur des projets `essai-*`. Le challenge
porte sur `/opt/lab-compose-env` et les projets `dsoxlab-env-*` : n'y touchez
pas pendant le cours.

Page associée : [Promouvoir le même artefact entre deux environnements](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/promouvoir-un-artefact/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run compose-plusieurs-environnements
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `vue` affiche la fusion
de plusieurs fichiers. **Gardez le même terminal jusqu'au nettoyage** : les
variables n'existent que dans lui.

```bash
mkdir -p ~/essai-fusion && cd ~/essai-fusion
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
mkdir conf && echo commun > conf/reglage
cat > base.yaml <<EOF
services:
  app:
    image: $IMAGE
    command: sleep 600
    init: true
    environment: {NIVEAU: base, COMMUN: oui}
    ports: ["127.0.0.1:18700:80"]
    dns: [192.0.2.1]
    volumes: ["donnees:/data", "./conf:/conf:ro"]
volumes:
  donnees:
EOF
vue() { docker compose -p essai-vue "$@" config; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## ➕ Exercice 1 : des listes qui s'ajoutent

Surchargez l'environnement, la commande, les ports et un montage, et lisez la
fusion :

```bash
cat > test.yaml <<'EOF'
services:
  app:
    command: sleep 300
    environment: {NIVEAU: test}
    ports: ["127.0.0.1:18701:80"]
    dns: [192.0.2.2]
    volumes: ["autres:/data"]
volumes:
  autres:
EOF
docker compose -p essai-vue -f base.yaml -f test.yaml config --format json > vue.json
python3 -c 'import json; a = json.load(open("vue.json"))["services"]["app"]; print(a["command"], a["environment"]); print([p["published"] for p in a["ports"]], a["dns"]); print([(v["source"].split("/")[-1], v["target"]) for v in a["volumes"]])'
```

```text
['sleep', '300'] {'COMMUN': 'oui', 'NIVEAU': 'test'}
['18700', '18701'] ['192.0.2.1', '192.0.2.2']
[('autres', '/data'), ('conf', '/conf')]
```

La commande est remplacée, l'environnement est fusionné clé par clé, les ports
et les adresses DNS s'ajoutent. Les montages se comparent par leur destination
: le volume de `/data` est remplacé. Lisez toujours `config` avant `up`.

## 🧽 Exercice 2 : remplacer ou retirer

Demandez explicitement de remplacer une liste, puis d'en retirer une :

```bash
cat > net.yaml <<'EOF'
services:
  app:
    ports: !override ["127.0.0.1:18702:80"]
    dns: !reset []
    environment:
      COMMUN: !reset null
EOF
docker compose -p essai-vue -f base.yaml -f net.yaml config --format json > vue.json
python3 -c 'import json; a = json.load(open("vue.json"))["services"]["app"]; print([p["published"] for p in a["ports"]], a.get("dns"), a["environment"])'
printf 'services:\n  app:\n    ports: []\n' > vide.yaml
docker compose -p essai-vue -f base.yaml -f vide.yaml config | grep published
```

```text
['18702'] None {'NIVEAU': 'base'}
        published: "18700"
```

Une liste vide ne retire rien : elle s'ajoute, donc le port de la base reste
publié. Pour remplacer, `!override` ; pour retirer, `!reset`.

## 🔃 Exercice 3 : un ordre et un dossier

Inversez les deux fichiers, puis lancez-les d'un autre dossier avec un chemin
relatif :

```bash
vue -f test.yaml -f base.yaml | grep NIVEAU
mkdir -p ailleurs/conf && echo surcharge > ailleurs/conf/reglage
printf 'services:\n  app:\n    volumes: ["./conf:/autre:ro"]\n' > ailleurs/plus.yaml
vue -f base.yaml -f ailleurs/plus.yaml | grep 'source: /' | sed "s#$HOME#~#; s/^ *//" | sort -u
vue -f ailleurs/plus.yaml -f base.yaml | grep 'source: /' | sed "s#$HOME#~#; s/^ *//" | sort -u
```

```text
      NIVEAU: base
source: ~/essai-fusion/conf
source: ~/essai-fusion/ailleurs/conf
```

Le dernier fichier l'emporte. Et tous les chemins relatifs partent du dossier
du **premier** fichier, même ceux écrits dans un autre dossier : inverser les
fichiers change les réglages montés.

## 🪪 Exercice 4 : un nom de projet qui change

Lancez la même déclaration sous deux noms, écrivez dans l'un, puis changez de
nom par une variable :

```bash
cat > seul.yaml <<EOF
services:
  app: {image: "$IMAGE", command: sleep 600, init: true, network_mode: none, volumes: ["donnees:/data"]}
volumes:
  donnees:
EOF
for p in essai-un essai-deux; do docker compose -p $p -f seul.yaml up -d > /dev/null 2>&1; done
docker compose -p essai-un -f seul.yaml exec -T app sh -c 'echo un > /data/v' < /dev/null
docker compose -p essai-deux -f seul.yaml exec -T app ls /data < /dev/null | wc -l
docker compose -p essai-un -f seul.yaml down > /dev/null 2>&1
COMPOSE_PROJECT_NAME=essai-deux docker compose -f seul.yaml ps --format '{{.Name}}'
docker compose -f seul.yaml ps -q | wc -l
docker volume ls -q | grep '^essai-'
```

```text
0
essai-deux-app-1
0
essai-deux_donnees
essai-un_donnees
```

Le nom du projet fait partie du nom de chaque objet : deux projets ne se voient
pas. Sans `-p`, Compose prend la variable, sinon le nom du dossier, et ne
trouve rien. `down` a laissé le volume : relancer `essai-un` le retrouvera.

## 🫥 Exercice 5 : une différence que Compose ne voit pas

Changez la valeur d'un fichier monté, puis une variable, et demandez à Compose
ce qui change :

```bash
cat > suivi.yaml <<EOF
services:
  app: {image: "$IMAGE", command: sleep 600, init: true, network_mode: none, environment: {MODE: "\${MODE:-a}"}, volumes: ["./conf:/conf:ro"]}
EOF
monte() { docker compose -p essai-suivi -f suivi.yaml up -d 2>&1 | grep -oE 'Running|Recreated|Started' | tail -1; }
empreinte() { docker compose -p essai-suivi -f suivi.yaml config --hash app | cut -d' ' -f2 | cut -c1-8; }
monte; A=$(empreinte)
echo nouveau > conf/reglage; monte
[ "$A" = "$(empreinte)" ] && echo 'meme empreinte'
export MODE=b; monte
[ "$A" = "$(empreinte)" ] || echo 'autre empreinte'
unset MODE
```

```text
Started
Running
meme empreinte
Started
autre empreinte
```

Compose compare la déclaration, pas le contenu des fichiers montés : le service
garde son ancien réglage en mémoire et rien ne le signale. Une variable, elle,
change l'empreinte et recrée le conteneur. Après un changement de fichier,
recréez vous-même.

## 🧹 Nettoyage

```bash
cd ~
for p in essai-un essai-deux essai-suivi; do docker ps -aq --filter label=com.docker.compose.project=$p | xargs -r docker rm -f > /dev/null; done
docker volume ls -q | grep -E '^essai-(un|deux)_' | xargs -r docker volume rm > /dev/null
rm -rf ~/essai-fusion
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
dsoxlab reset compose-plusieurs-environnements
dsoxlab check compose-plusieurs-environnements
```

```text
╭─ Résultat : compose-plusieurs-environnements ─╮
│  0 / 100 pts                                  │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests              │
╰───────────────────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : une image, deux machines, et deux environnements qui
ne se mélangent pas.

```bash
dsoxlab run compose-plusieurs-environnements
dsoxlab challenge compose-plusieurs-environnements
```
