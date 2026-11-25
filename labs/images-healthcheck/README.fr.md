# « Up » ne dit rien du service

La leçon déclare une sonde et règle ses bornes. Ce cours ajoute cinq situations
: le code qui fait le verdict, le compte qui joue la sonde, l'historique des
changements d'état, un conteneur arrêté puis relancé, et une sonde héritée d'un
socle.

Vous travaillez dans `~/essai-pouls`, sur des conteneurs `essai-*`. Le
challenge porte sur `service-surveille` : n'y touchez pas pendant le cours.

Page associée : [Tester le contrat d'une image](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/tester-une-image/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run images-healthcheck
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. La fonction `sonde`
lance un conteneur avec une commande de santé, jouée chaque seconde. **Gardez
le même terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-pouls && cd ~/essai-pouls
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
sonde() { docker run -d --init --name essai-sonde --health-interval 1s --health-retries 2 --health-cmd "$1" ${2:-} "$IMAGE" sleep 600 > /dev/null; sleep 4; }
etat() { docker inspect essai-sonde --format '{{.State.Status}} {{.State.Health.Status}}'; }
retire() { docker rm -f essai-sonde > /dev/null; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🔢 Exercice 1 : le code qui fait le verdict

Donnez trois codes de sortie à la sonde :

```bash
for code in 0 1 137; do sonde "exit $code"; etat; docker inspect essai-sonde --format '{{(index .State.Health.Log 0).ExitCode}}'; retire; done
```

```text
running healthy
0
running unhealthy
1
running unhealthy
137
```

Zéro veut dire sain, tout le reste veut dire malade. Le code exact reste dans
le journal : 137 est celui d'une sonde tuée, ce qui n'est pas la même panne
qu'un 1.

## 👤 Exercice 2 : le compte qui joue la sonde

Lancez le conteneur sous un compte ordinaire, avec une sonde qui lit un fichier
réservé à root :

```bash
sonde 'id -u; cat /etc/shadow' '--user 4242'
etat
docker inspect essai-sonde --format '{{(index .State.Health.Log 0).Output}}'
retire
```

```text
running unhealthy
4242
cat: can't open '/etc/shadow': Permission denied
```

La sonde tourne sous le compte du conteneur. Le service peut très bien marcher
: c'est la sonde qui n'a pas le droit de regarder. Essayez-la d'abord à la main
avec `docker exec`, sous le même compte.

## 📜 Exercice 3 : l'historique des changements

Faites passer un conteneur de malade à sain, puis relisez ce que le moteur a
noté :

```bash
DEBUT=$(date +%s)
sonde 'test -f /tmp/pret'
docker ps --filter health=unhealthy --format '{{.Names}}'
docker exec essai-sonde touch /tmp/pret
sleep 3
docker ps --filter health=unhealthy -q | wc -l
docker events --since "$DEBUT" --until "$(date +%s)" --filter container=essai-sonde --filter event=health_status --format '{{.Action}}'
```

```text
essai-sonde
0
health_status: unhealthy
health_status: healthy
```

`docker ps --filter health=unhealthy` liste les malades de la machine, et
`docker events` garde les changements, y compris ceux déjà passés. Une
supervision lit l'un ou l'autre : le moteur, lui, ne fait rien de cet état.

## ⏹️ Exercice 4 : un conteneur arrêté puis relancé

Rendez la sonde malade, arrêtez le conteneur, puis relancez-le :

```bash
docker exec essai-sonde rm /tmp/pret
sleep 4
docker stop --timeout 1 essai-sonde > /dev/null
etat
docker start essai-sonde > /dev/null
etat
retire
```

```text
exited unhealthy
running starting
```

Un conteneur arrêté garde son dernier état de santé : `exited unhealthy` ne dit
pas pourquoi il s'est arrêté. Au démarrage, l'état repart à `starting`, et la
sonde doit de nouveau conclure.

## 🧬 Exercice 5 : une sonde héritée d'un socle

Construisez une image avec une sonde, puis trois images qui en partent :

```bash
printf 'FROM %s\nHEALTHCHECK --interval=1s CMD test -f /tmp/pret\n' "$IMAGE" > socle.Dockerfile
docker build -q -f socle.Dockerfile -t essai-pouls:socle . > /dev/null
printf 'FROM essai-pouls:socle\nENV X=1\n' > a.Dockerfile
printf 'FROM essai-pouls:socle\nHEALTHCHECK NONE\n' > b.Dockerfile
printf 'FROM essai-pouls:socle\nHEALTHCHECK --retries=9 CMD true\nHEALTHCHECK CMD false\n' > c.Dockerfile
for f in a b c; do docker build -q -f $f.Dockerfile -t essai-pouls:$f . > /dev/null 2>&1; docker image inspect essai-pouls:$f --format '{{json .Config.Healthcheck}}'; done
```

```text
{"Test":["CMD-SHELL","test -f /tmp/pret"],"Interval":1000000000}
{"Test":["NONE"]}
{"Test":["CMD-SHELL","false"]}
```

La sonde s'hérite, avec ses bornes, même si votre Dockerfile n'en parle pas.
`HEALTHCHECK NONE` la retire. Deux instructions ne s'additionnent pas : la
dernière l'emporte en entier, et les neuf tentatives ont disparu.

## 🧹 Nettoyage

```bash
cd ~
docker images 'essai-pouls' --format '{{.Repository}}:{{.Tag}}' | xargs -r docker rmi -f > /dev/null
rm -r ~/essai-pouls
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker images --format '{{.Repository}}' | grep -c '^essai-'
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
dsoxlab reset images-healthcheck
dsoxlab check images-healthcheck
```

```text
╭── Résultat : images-healthcheck ──╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un service qui se tait sans mourir, et une sonde à
lui écrire.

```bash
dsoxlab run images-healthcheck
dsoxlab challenge images-healthcheck
```
