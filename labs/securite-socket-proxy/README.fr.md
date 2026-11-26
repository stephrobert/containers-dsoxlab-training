# Interposer un proxy filtrant devant l'API Docker

La leçon déploie un proxy et mesure ses profils. Ce cours regarde le proxy du
côté de l'outil et de l'attaquant : ce qui est ouvert sans rien demander, un
client Docker qui passe par lui, ce que les événements racontent, un second
réseau qui l'expose, et ce que son journal garde.

Vous travaillez dans `~/essai-filtre`, sur `essai-relais`, `essai-cible` et des
réseaux `essai-*`. Le challenge porte sur `filtre-api`, `cible-1` et `cible-2`
: n'y touchez pas pendant le cours.

Page associée : [Interposer un proxy devant l'API Docker](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/socket-proxy/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run securite-socket-proxy
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `sert` lance le proxy
avec un profil, `code` demande un chemin et rend le statut HTTP. **Gardez le
même terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-filtre && cd ~/essai-filtre
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
CURL=curlimages/curl:8.23.0@sha256:3fb7e13e5d179a845c97d78204f3f1064d1907037f26a3ebf91710571151fd93
PROXY=lscr.io/linuxserver/socket-proxy:3.4.7-r0-ls104@sha256:4e5e59efd3338205561c54262581992036e5a36ccca97d487b1d4ec41f9adc58
docker network create --internal essai-api > /dev/null
sert() { docker rm -f essai-relais > /dev/null 2>&1; docker run -d --name essai-relais --network essai-api --read-only --tmpfs /run -v /var/run/docker.sock:/var/run/docker.sock:ro "$@" "$PROXY" > /dev/null; sleep 2; }
code() { docker run --rm --network essai-api "$CURL" -s -m 4 -o /dev/null -w '%{http_code}' "http://essai-relais:2375/$1"; echo " $1"; }
docker run -d --init --name essai-cible -e CLE=demo --label equipe=paie "$IMAGE" sleep 600 > /dev/null
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🚪 Exercice 1 : ouvert sans rien demander

Lancez le proxy sans aucune variable, et essayez neuf chemins :

```bash
sert
for c in _ping version events info containers/json images/json volumes secrets system/df; do code $c; done
```

```text
200 _ping
200 version
200 events
403 info
403 containers/json
403 images/json
403 volumes
403 secrets
403 system/df
```

Trois chemins répondent sans que vous ayez rien ouvert. `events` est le moins
anodin des trois, l'exercice 3 montre pourquoi. Faites cette liste sur votre
propre image de proxy : les valeurs par défaut changent d'un projet à l'autre.

## 🧰 Exercice 2 : un client Docker par le proxy

Ouvrez les conteneurs, et pointez un client Docker ordinaire vers le proxy :

```bash
sert -e CONTAINERS=1
IP=$(docker inspect essai-relais --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
docker -H "tcp://$IP:2375" ps --format '{{.Names}}' | sort
docker -H "tcp://$IP:2375" images 2>&1 | grep -o '403 Forbidden'
docker -H "tcp://$IP:2375" run --rm "$IMAGE" true 2>&1 | grep -o '403 Forbidden'
docker -H "tcp://$IP:2375" logs essai-cible 2>&1 | grep -o '403 Forbidden'
```

```text
cible-1
cible-2
essai-cible
essai-relais
403 Forbidden
403 Forbidden
403 Forbidden
```

Le client marche tel quel pour ce qui est permis, et affiche la page du proxy
pour le reste. `logs` est refusé alors que la famille des conteneurs est
ouverte : cette image traite certaines actions à part. Essayez donc chaque
commande de votre outil.

## 📻 Exercice 3 : ce que les événements racontent

Fermez tout, écoutez les événements à travers le proxy, et travaillez
normalement à côté :

```bash
sert
IP=$(docker inspect essai-relais --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
curl -s -m 5 "http://$IP:2375/events" > evenements.txt &
sleep 1
docker exec essai-cible sh -c 'echo mot-de-passe-tape > /dev/null'
wait
grep -o '"Action":"exec_create[^"]*"' evenements.txt | head -1
grep -o '"equipe":"paie"' evenements.txt | head -1
```

```text
"Action":"exec_create: sh -c echo mot-de-passe-tape \u003e /dev/null"
"equipe":"paie"
```

Sans aucune famille ouverte, l'outil voit les commandes passées à `docker
exec`, avec leurs arguments, et les étiquettes des conteneurs. Un mot de passe
tapé dans une commande est donc diffusé. Fermez les événements si l'outil n'en
a pas besoin.

## 🕸️ Exercice 4 : un second réseau qui l'expose

Essayez de joindre le proxy depuis un autre réseau, puis branchez-le dessus :

```bash
docker network create --internal essai-autre > /dev/null
docker run --rm --network essai-autre "$CURL" -s -m 3 "http://$IP:2375/_ping"; echo "code: $?"
docker network connect essai-autre essai-relais
docker run --rm --network essai-autre "$CURL" -s -m 3 http://essai-relais:2375/_ping; echo " code: $?"
docker inspect essai-relais --format '{{range $n, $c := .NetworkSettings.Networks}}{{$n}} {{end}}'
```

```text
code: 7
OK code: 0
essai-api essai-autre
```

Le proxy n'a pas de mot de passe : son réseau est sa seule protection. Un
branchement de plus, et tous les conteneurs de ce réseau ont les mêmes droits
que l'outil. Contrôlez la liste des réseaux du proxy, et celle des conteneurs
de son réseau.

## 📜 Exercice 5 : ce que son journal garde

Provoquez un refus, et relisez le journal du proxy :

```bash
code containers/create > /dev/null
docker logs essai-relais 2>&1 | grep -oE '[0-9]{3} [0-9]+ - - [A-Z-]+ .*"GET /containers/create' | grep -oE '^403|PR--|GET .*' | xargs
docker logs essai-relais 2>&1 | grep -c '_ping'
```

```text
403 PR-- GET /containers/create
1
```

Chaque demande est notée avec son statut, et `PR--` signale un refus par le
proxy lui-même. C'est le seul endroit où l'on voit ce qu'un outil a essayé : le
démon, lui, n'a rien reçu.

## 🧹 Nettoyage

```bash
cd ~
docker rm -f essai-relais essai-cible > /dev/null
docker network rm essai-api essai-autre > /dev/null
rm -rf ~/essai-filtre
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
dsoxlab reset securite-socket-proxy
dsoxlab check securite-socket-proxy
```

```text
╭─ Résultat : securite-socket-proxy ─╮
│  0 / 100 pts                       │
│  ░░░░░░░░░░░░░░░░░░░░  0/7 tests   │
╰────────────────────────────────────╯
```

0 sur 7 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un outil qui lit et arrête, et qui ne doit rien
pouvoir d'autre.

```bash
dsoxlab run securite-socket-proxy
dsoxlab challenge securite-socket-proxy
```
