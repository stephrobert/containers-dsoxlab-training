# Interroger un conteneur en marche

La leçon donne quatre commandes pour quatre questions : journaux, adresse, port
et fichier écrit. Ce cours vous place devant cinq autres cas : une erreur que
`grep` ne voit pas dans les journaux, une commande de lancement perdue, un
conteneur sur plusieurs réseaux, un port déjà pris, et un conteneur qui n'a pas
l'outil dont vous avez besoin.

Vous travaillez sur `essai-guichet`. Le challenge porte sur `greffier`, déjà en
marche : n'y touchez pas pendant le cours.

Page associée : [Inspecter un conteneur en marche avec Docker](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/inspecter-un-conteneur/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run docker-inspecter-un-conteneur
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. Lancez le conteneur
d'essai, que les exercices vous feront interroger. **Gardez le même terminal
jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker run -d --name essai-guichet -e MODE=demo -v essai-donnees:/donnees \
  --restart on-failure:3 -p 127.0.0.1:8099:8000 "$IMAGE" \
  sh -c 'echo "guichet ouvert"; echo "ERREUR cle absente" >&2; exec nc -lk -p 8000 -e cat' > /dev/null
sleep 1
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les adresses seront différentes chez vous.

## 📜 Exercice 1 : l'erreur que `grep` ne voit pas

`docker logs` rend séparément la sortie standard et la sortie d'erreur du
conteneur. Masquez la sortie d'erreur, puis comptez les lignes `ERREUR` avec et
sans elle :

```bash
docker logs essai-guichet 2> /dev/null
docker logs essai-guichet 2> /dev/null | grep -c ERREUR
docker logs essai-guichet 2>&1 | grep -c ERREUR
```

```text
guichet ouvert
0
1
```

Un tube ne transmet que la sortie standard. Sans `2>&1`, `grep` ne reçoit pas
le message d'erreur et vous pourriez conclure qu'il n'existe pas. Écrivez
`docker logs <nom> 2>&1 | grep …` par réflexe.

## 🧾 Exercice 2 : retrouver la commande de lancement

La commande `docker run` d'origine n'est écrite nulle part sur l'hôte. Le moteur
en garde les réglages, à condition de savoir où les demander :

```bash
docker container inspect essai-guichet --format 'image    {{.Config.Image}}
commande {{json .Config.Cmd}}
env      {{json .Config.Env}}
reprise  {{.HostConfig.RestartPolicy.Name}}:{{.HostConfig.RestartPolicy.MaximumRetryCount}}
montages {{range .Mounts}}{{.Type}} {{.Name}} -> {{.Destination}}{{end}}
ports    {{json .HostConfig.PortBindings}}'
```

```text
image    alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
commande ["sh","-c","echo \"guichet ouvert\"; echo \"ERREUR cle absente\" >&2; exec nc -lk -p 8000 -e cat"]
env      ["MODE=demo","PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"]
reprise  on-failure:3
montages volume essai-donnees -> /donnees
ports    {"8000/tcp":[{"HostIp":"127.0.0.1","HostPort":"8099"}]}
```

`Config` décrit ce que le conteneur exécute : image, commande, variables.
`HostConfig` décrit ce que vous avez demandé à l'hôte : redémarrage, ports.
`Mounts` donne les données montées. Avec ces six lignes, vous pouvez relancer le
conteneur à l'identique. `PATH` vient de l'image et non de la ligne de commande.
Les variables s'affichent en clair : un mot de passe passé par `-e` est lisible
par toute personne qui peut interroger le moteur.

## 🌐 Exercice 3 : un conteneur sur deux réseaux

Rattachez le conteneur à un second réseau, puis demandez son adresse avec les
deux formes de la leçon :

```bash
docker network create essai-arriere > /dev/null
docker network connect essai-arriere essai-guichet
docker container inspect essai-guichet --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
docker container inspect essai-guichet --format '{{range $nom, $c := .NetworkSettings.Networks}}{{println $nom $c.IPAddress}}{{end}}'
```

```text
172.17.0.3172.18.0.2
bridge 172.17.0.3
essai-arriere 172.18.0.2
```

Sans séparateur, les deux adresses se collent en une valeur inutilisable, et un
script ne verrait rien d'anormal. La seconde forme nomme chaque réseau, et
`println` termine chaque ligne. Utilisez-la dès qu'un conteneur peut avoir
plusieurs réseaux.

## 🚪 Exercice 4 : qui occupe ce port ?

Essayez de publier un port déjà pris, puis cherchez qui le tient. Les filtres
de `docker ps` répondent aussi pour un volume et pour un réseau :

```bash
docker run --rm -p 127.0.0.1:8099:80 "$IMAGE" true 2>&1 | grep -o 'Bind for.*'
docker ps --filter publish=8099 --format '{{.Names}} {{.Ports}}'
docker ps --filter volume=essai-donnees --format '{{.Names}}'
docker ps --filter network=essai-arriere --format '{{.Names}}'
```

```text
Bind for 127.0.0.1:8099 failed: port is already allocated
essai-guichet 127.0.0.1:8099->8000/tcp
essai-guichet
essai-guichet
```

Le message d'erreur ne nomme pas le coupable. `--filter publish=8099` le donne
aussitôt. `volume=` et `network=` répondent à la même question avant de
supprimer un volume ou un réseau : qui s'en sert encore ?

## 🧰 Exercice 5 : un conteneur sans l'outil voulu

L'image ne contient pas `ss`. Au lieu d'y installer quelque chose, entrez
depuis l'hôte dans le seul réseau du conteneur, avec les outils de l'hôte :

```bash
docker exec essai-guichet ss -ltn
PID=$(docker container inspect essai-guichet --format '{{.State.Pid}}')
sudo nsenter --target "$PID" --net ss -ltn
sudo cat /proc/$PID/root/etc/alpine-release
```

```text
OCI runtime exec failed: exec failed: unable to start container process: exec: "ss": executable file not found in $PATH
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port
LISTEN 0      4096      127.0.0.11:44701      0.0.0.0:*
LISTEN 0      1                  *:8000             *:*
3.24.3
```

`docker exec` échoue : le programme n'existe pas dans l'image. `nsenter --net`
lance le `ss` de l'hôte dans le réseau du conteneur : le port 8000 est bien
ouvert. La ligne `127.0.0.11` est le serveur DNS que Docker installe dans les
conteneurs d'un réseau créé par vous. `/proc/<pid>/root` donne de la même façon
accès aux fichiers du conteneur, ici la version d'Alpine.

## 🧹 Nettoyage

```bash
docker rm -f essai-guichet > /dev/null
docker network rm essai-arriere
docker volume rm essai-donnees
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
essai-arriere
essai-donnees
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset docker-inspecter-un-conteneur
dsoxlab check docker-inspecter-un-conteneur
```

```text
╭─ Résultat : docker-inspecter-un-conteneur ─╮
│  0 / 100 pts                               │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests           │
╰────────────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : obtenir quatre informations d'un conteneur sans
documentation, sans l'arrêter.

```bash
dsoxlab run docker-inspecter-un-conteneur
dsoxlab challenge docker-inspecter-un-conteneur
```
