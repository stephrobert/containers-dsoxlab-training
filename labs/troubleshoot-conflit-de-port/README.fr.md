# Deux conflits de port, deux causes

La leçon oppose le port tenu par un conteneur et celui tenu par un programme de
l'hôte. Ce cours ajoute cinq cas qui brouillent ce diagnostic : le même port
sur deux adresses, une publication trop large, un conteneur arrêté qui perd sa
place, un conteneur que `docker ps` ne montre pas comme coupable, et un
`docker-proxy` à rattacher à son conteneur.

Vous travaillez sur des conteneurs `essai-*` et les ports 18400 à 18410. Le
challenge porte sur d'autres conteneurs et les ports 18200 et 18201.

Page associée : [Publier un port Docker sans exposer tout l'hôte](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/publier-un-port/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run troubleshoot-conflit-de-port
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. La fonction `repondeur`
lance un conteneur qui répond une ligne sur son port 80. **Gardez le même
terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
HOTE=$(ip -o -4 route get 1.1.1.1 | awk '{for (i = 1; i <= NF; i++) if ($i == "src") print $(i + 1)}')
repondeur() { docker run -d "$@" "$IMAGE" sh -c 'exec nc -ll -p 80 -e echo "ici $(hostname)"'; }
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🏠 Exercice 1 : le même port sur deux adresses

Publiez le port 18400 deux fois, sur deux adresses différentes :

```bash
repondeur --name essai-local -p 127.0.0.1:18400:80 > /dev/null
repondeur --name essai-reseau -p "$HOTE":18400:80 > /dev/null
docker ps --filter name=essai- --format '{{.Names}} {{.Ports}}'
nc -w 3 127.0.0.1 18400
nc -w 3 "$HOTE" 18400
```

```text
essai-reseau 10.10.120.11:18400->80/tcp
essai-local 127.0.0.1:18400->80/tcp
ici 22c921835936
ici 90974931fac2
```

Aucun conflit : ce qui est unique, c'est l'adresse et le port ensemble. Deux
services différents répondent donc sur le même numéro, selon l'adresse appelée.
Un test en local peut ainsi réussir sur un autre service que celui vu du
réseau.

## 📐 Exercice 2 : une publication trop large

Demandez maintenant le même port sur toutes les interfaces :

```bash
repondeur --name essai-partout -p 18400:80 2>&1 | grep -o 'Bind for.*'
docker ps --filter name=essai-partout --format '{{.Names}}' | wc -l
```

```text
Bind for 127.0.0.1:18400 failed: port is already allocated
0
```

Toutes les interfaces comprennent `127.0.0.1`, déjà pris. Le message nomme
l'adresse en conflit, et non `0.0.0.0` que vous avez demandée : c'est l'indice.
`docker ps` ne montre pas ce conteneur : il n'a pas démarré.

## 💤 Exercice 3 : un conteneur arrêté perd son port

Arrêtez `essai-local`, donnez son port à un autre, puis essayez de le relancer
:

```bash
docker stop --timeout 1 essai-local > /dev/null
repondeur --name essai-remplacant -p 127.0.0.1:18400:80 > /dev/null
docker start essai-local 2>&1 | grep -o 'Bind for.*'
docker container inspect essai-local --format 'statut={{.State.Status}} code={{.State.ExitCode}} erreur={{.State.Error}}' | cut -c1-80
```

```text
Bind for 127.0.0.1:18400 failed: port is already allocated
statut=exited code=143 erreur=failed to set up container networking: driver fail
```

Un conteneur arrêté ne réserve pas son port. Au redémarrage, il échoue alors
que sa configuration n'a pas changé. Le statut reste `exited` avec le code de
l'arrêt précédent : seul `.State.Error` dit qu'un démarrage vient d'échouer.

## 👻 Exercice 4 : un coupable que docker ps ne désigne pas

Un conteneur lancé avec `--network host` ouvre ses ports directement sur la
machine :

```bash
docker run -d --name essai-hote --network host "$IMAGE" nc -lk -p 18410 > /dev/null
sleep 1
repondeur --name essai-refuse -p 18410:80 2>&1 | grep -o 'failed to bind.*'
docker ps --filter publish=18410 --format '{{.Names}}' | wc -l
PID=$(sudo ss -ltnp | grep ':18410' | grep -o 'pid=[0-9]*' | cut -d= -f2)
cat /proc/$PID/cgroup | cut -c1-40
docker container inspect "$(grep -oE '[0-9a-f]{64}' /proc/$PID/cgroup)" --format '{{.Name}}'
```

```text
failed to bind host port 0.0.0.0:18410/tcp: address already in use
0
0::/system.slice/docker-0844226cdb3941bb
/essai-hote
```

Le message est celui d'un programme de l'hôte, et le filtre `publish` ne trouve
rien. Le coupable est pourtant un conteneur : le cgroup de son processus porte
l'identifiant du conteneur, que `docker container inspect` traduit en nom.
Avant de conclure « hors de Docker », lisez donc `/proc/<pid>/cgroup`.

## 🧷 Exercice 5 : de docker-proxy au conteneur

`ss` nomme `docker-proxy` pour tous les ports publiés. Retrouvez le conteneur
servi par celui du port 18400 en local :

```bash
PID=$(sudo ss -ltnp | grep '127.0.0.1:18400' | grep -o 'pid=[0-9]*' | cut -d= -f2)
ps -o args= -p "$PID" | grep -o 'container-ip.*-container-port [0-9]*'
docker ps --filter publish=18400 --format '{{.Names}} {{.Ports}}'
```

```text
container-ip 172.17.0.3 -container-port 80
essai-remplacant 127.0.0.1:18400->80/tcp
essai-reseau 10.10.120.11:18400->80/tcp
```

La ligne de commande de `docker-proxy` donne l'adresse et le port du conteneur.
`docker ps` avec le filtre répond plus vite, mais il rend les deux conteneurs
qui publient 18400 : la colonne des ports les départage.

## 🧹 Nettoyage

```bash
docker rm -f essai-local essai-reseau essai-partout essai-remplacant essai-hote essai-refuse > /dev/null
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
sudo ss -ltn | grep -cE ':184(00|10)'
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
dsoxlab reset troubleshoot-conflit-de-port
dsoxlab check troubleshoot-conflit-de-port
```

```text
╭─ Résultat : troubleshoot-conflit-de-port ─╮
│  0 / 100 pts                              │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests          │
╰───────────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : deux conteneurs refusés, deux causes, et aucun
service en marche à couper.

```bash
dsoxlab run troubleshoot-conflit-de-port
dsoxlab challenge troubleshoot-conflit-de-port
```
