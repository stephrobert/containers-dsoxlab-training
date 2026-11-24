# Deux isolations qui ne se ressemblent pas

La leçon compare un conteneur sans réseau et un réseau interne, et montre la
route absente. Ce cours mesure cinq limites : un port publié qui ne s'ouvre
pas, l'hôte qui entre quand même, la passerelle qui répond, les noms
extérieurs, et deux conteneurs qui partagent un même réseau.

Vous travaillez sur le réseau `essai-clos` et des conteneurs `essai-*`. Le
challenge porte sur `coffre`, `dehors`, `atelier-a` et `atelier-b` : n'y
touchez pas pendant le cours.

Page associée : [Isoler un conteneur du réseau : none ou réseau interne](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/reseau-interne/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run reseau-interne
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

## 🚪 Exercice 1 : un port publié qui ne s'ouvre pas

Publiez un port sur un conteneur d'un réseau interne :

```bash
docker network create --internal --subnet 10.89.1.0/24 essai-clos > /dev/null
repondeur --name essai-dedans --network essai-clos -p 127.0.0.1:18500:80 > /dev/null; echo "code: $?"
docker container inspect essai-dedans --format '{{json .HostConfig.PortBindings}}'
docker port essai-dedans | wc -l
nc -w 3 127.0.0.1 18500; echo "code: $?"
```

```text
code: 0
{"80/tcp":[{"HostIp":"127.0.0.1","HostPort":"18500"}]}
0
code: 1
```

Docker accepte la commande sans un mot, garde la demande dans `PortBindings`,
et n'ouvre rien. `docker port` est vide et la connexion échoue. Un service «
publié » qui ne répond pas peut donc venir d'un réseau interne.

## 🏠 Exercice 2 : l'hôte entre quand même

Joignez le conteneur depuis l'hôte, par son adresse :

```bash
IP=$(docker container inspect essai-dedans --format '{{(index .NetworkSettings.Networks "essai-clos").IPAddress}}')
echo "$IP"
nc -w 3 "$IP" 80; echo "code: $?"
```

```text
10.89.1.2
ici 56d6ab346125
code: 0
```

L'hôte porte la passerelle de ce réseau, il en fait donc partie. Un réseau
interne empêche les membres de sortir. Il ne les cache pas à la machine qui les
héberge.

## 🌉 Exercice 3 : la passerelle répond, pas l'adresse routable

Lancez un serveur web sur l'hôte et appelez-le depuis le conteneur, par les
deux adresses de l'hôte :

```bash
mkdir -p ~/essai-web && echo "page de l'hôte" > ~/essai-web/index.html
python3 -m http.server 18510 --bind 0.0.0.0 --directory ~/essai-web > /dev/null 2>&1 &
sleep 1
docker exec essai-dedans wget -q -T 3 -O - http://10.89.1.1:18510/
docker exec essai-dedans wget -q -T 3 -O - "http://$HOTE:18510/"; echo "code: $?"
```

```text
page de l'hôte
wget: can't connect to remote host (10.10.120.11): Network unreachable
code: 1
```

Par la passerelle, le conteneur joint le service de l'hôte. Par l'adresse
routable, aucune route : `Network unreachable`. Un service de l'hôte qui écoute
sur toutes les interfaces reste donc joignable depuis un réseau interne. C'est
la faille à connaître.

## 🔤 Exercice 4 : les noms extérieurs, et le refus de none

Demandez un nom public, puis essayez de brancher un conteneur `none` sur ce
réseau :

```bash
docker exec essai-dedans nslookup example.org 2>&1 | grep -o 'SERVFAIL'
docker run -d --name essai-nu --network none "$IMAGE" sleep 600 > /dev/null
docker network connect essai-clos essai-nu; echo "code: $?"
```

```text
SERVFAIL
SERVFAIL
Error response from daemon: container cannot be connected to multiple networks with one of the networks in private (none) mode
code: 1
```

Les noms extérieurs ne se résolvent pas non plus. Et un conteneur lancé sans
réseau ne peut pas en recevoir un ensuite : il faut le recréer.

## 👥 Exercice 5 : deux conteneurs, un seul réseau

`--network container:<nom>` place un second conteneur dans le réseau du premier
:

```bash
docker run -d --name essai-voisin --network container:essai-dedans "$IMAGE" sleep 600 > /dev/null
docker exec essai-voisin nc -w 3 127.0.0.1 80
docker run --rm --network container:essai-dedans -p 18501:80 "$IMAGE" true 2>&1 | grep -o 'conflicting options.*'
```

```text
ici 56d6ab346125
conflicting options: port publishing and the container type network mode
```

Les deux partagent la même adresse et le même `127.0.0.1`. Le second ne peut
pas publier de port : le réseau appartient au premier. Ce montage donne un
outil de diagnostic à un conteneur confiné sans toucher à son réseau.

## 🧹 Nettoyage

```bash
docker rm -f essai-voisin essai-nu essai-dedans > /dev/null
docker network rm essai-clos
pkill -f 'http.server 18510'
rm -r ~/essai-web
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
essai-clos
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset reseau-interne
dsoxlab check reseau-interne
```

```text
╭──── Résultat : reseau-interne ────╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un conteneur sans réseau, et deux autres qui se
parlent sans jamais sortir.

```bash
dsoxlab run reseau-interne
dsoxlab challenge reseau-interne
```
