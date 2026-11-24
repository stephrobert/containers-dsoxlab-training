# Un réseau à soi : nommer et isoler

La leçon crée un réseau, montre son service de noms, son isolation et les
alias. Ce cours ajoute cinq gestes : un plan d'adressage qui se recouvre, une
adresse fixe, un nom qui disparaît, un réseau qu'on ne peut pas supprimer, et
un nom qui se résout sans que la connexion passe.

Vous travaillez sur des réseaux et des conteneurs `essai-*`. Le challenge porte
sur `avant`, `arriere` et `tiers` : n'y touchez pas pendant le cours.

Page associée : [Réseau Docker par défaut ou réseau à soi : lequel choisir ?](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/network/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run reseau-bridge-dedie
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

## 🗺️ Exercice 1 : deux plans qui se recouvrent

Créez un réseau, puis un second dont la plage contient la première :

```bash
docker network create --subnet 10.88.1.0/24 essai-plan > /dev/null
docker network create --subnet 10.88.0.0/16 essai-recouvre; echo "code: $?"
docker network inspect essai-plan --format '{{(index .IPAM.Config 0).Subnet}}'
```

```text
Error response from daemon: invalid pool request: Pool overlaps with other one on this address space
code: 1
10.88.1.0/24
```

Docker refuse une plage qui en recouvre une autre, parmi ses réseaux. Le
message ne dit pas laquelle : cherchez-la dans `docker network inspect` de
chaque réseau.

## 📌 Exercice 2 : une adresse fixe, demandée deux fois

Sur un réseau dont vous avez choisi la plage, `--ip` fixe l'adresse.
Demandez-la deux fois :

```bash
repondeur --name essai-fixe --network essai-plan --ip 10.88.1.50 > /dev/null
docker container inspect essai-fixe --format '{{(index .NetworkSettings.Networks "essai-plan").IPAddress}}'
repondeur --name essai-fixe2 --network essai-plan --ip 10.88.1.50 2>&1 | grep -o 'Address already in use'
```

```text
10.88.1.50
Address already in use
```

`Address already in use` parle ici d'une adresse IP, pas d'un port. Le même
texte sert aux deux cas : regardez ce que vous demandiez. Un nom suffit presque
toujours, l'adresse fixe sert à un pare-feu ou à un équipement qui ne connaît
que des adresses.

## 🫥 Exercice 3 : un nom qui disparaît

Résolvez le nom d'un membre, arrêtez-le, puis recommencez :

```bash
docker run -d --name essai-client --network essai-plan "$IMAGE" sleep 600 > /dev/null
docker exec essai-client getent hosts essai-fixe; echo "code: $?"
docker stop --timeout 1 essai-fixe > /dev/null
docker exec essai-client getent hosts essai-fixe; echo "code: $?"
docker start essai-fixe > /dev/null
docker exec essai-client nc -w 3 essai-fixe 80
```

```text
10.88.1.50        essai-fixe  essai-fixe
code: 0
code: 2
ici 93ee81f93376
```

Le service de noms ne connaît que les membres en marche. Une application qui
affiche « nom inconnu » vise peut-être un conteneur arrêté, et non un nom mal
écrit. Au redémarrage, le nom revient.

## 🔒 Exercice 4 : un réseau qu'on ne peut pas supprimer

Essayez de supprimer le réseau pendant qu'il sert :

```bash
docker network rm essai-plan 2>&1 | grep -oE 'has active endpoints|essai-(fixe|client)"' | tr -d '"'
docker network inspect essai-plan --format '{{range .Containers}}{{println .Name .IPv4Address}}{{end}}'
```

```text
has active endpoints
essai-fixe
essai-client
essai-client 10.88.1.2/24
essai-fixe 10.88.1.50/24
```

Le refus nomme les membres encore attachés, qu'on retrouve dans `docker network
inspect`. C'est une protection : lisez la liste avant de détacher qui que ce
soit.

## 🔇 Exercice 5 : résoudre n'est pas joindre

Une option de réseau interdit aux membres de se parler. Créez-en un et essayez
:

```bash
docker network create --opt com.docker.network.bridge.enable_icc=false essai-mute > /dev/null
repondeur --name essai-muet --network essai-mute > /dev/null
docker run -d --name essai-curieux --network essai-mute "$IMAGE" sleep 600 > /dev/null
docker exec essai-curieux getent hosts essai-muet | awk '{print $2}'
docker exec essai-curieux nc -w 3 essai-muet 80; echo "code: $?"
```

```text
essai-muet
code: 1
```

Le nom se résout et la connexion n'aboutit pas : le pare-feu du moteur bloque
entre membres (`enable_icc=false`). Quand un nom répond mais pas le service,
cherchez du côté du filtrage avant d'accuser l'application.

## 🧹 Nettoyage

```bash
docker rm -f essai-fixe essai-fixe2 essai-client essai-muet essai-curieux > /dev/null
docker network rm essai-plan essai-mute
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
essai-plan
essai-mute
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset reseau-bridge-dedie
dsoxlab check reseau-bridge-dedie
```

```text
╭─ Résultat : reseau-bridge-dedie ──╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un réseau au plan imposé, deux conteneurs qui s'y
trouvent par leur nom, et un troisième laissé dehors.

```bash
dsoxlab run reseau-bridge-dedie
dsoxlab challenge reseau-bridge-dedie
```
