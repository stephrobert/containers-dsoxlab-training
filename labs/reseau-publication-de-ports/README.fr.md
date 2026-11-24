# Publier un port, et seulement où il faut

La leçon montre les trois portées d'un `-p`, la posture sans publication et la
différence entre publier et servir. Ce cours ajoute cinq gestes : le protocole,
une plage de ports, deux publications pour un conteneur, une adresse que la
machine n'a pas, et un réglage qui change le défaut.

Vous travaillez sur des conteneurs `essai-*` et les ports 18300 à 18323. Le
challenge porte sur `vitrine`, `annexe` et `interne` : n'y touchez pas pendant
le cours.

Page associée : [Publier un port Docker sans exposer tout l'hôte](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/publier-un-port/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run reseau-publication-de-ports
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

## 📨 Exercice 1 : TCP n'est pas UDP

Publiez le même port d'hôte deux fois, en TCP puis en UDP :

```bash
repondeur --name essai-tcp -p 127.0.0.1:18300:80 > /dev/null
repondeur --name essai-udp -p 127.0.0.1:18300:80/udp > /dev/null
docker ps --filter name=essai- --format '{{.Names}} {{.Ports}}'
```

```text
essai-udp 127.0.0.1:18300->80/udp
essai-tcp 127.0.0.1:18300->80/tcp
```

Il n'y a pas de conflit : les numéros TCP et UDP sont distincts. Sans suffixe,
`-p` publie en TCP seulement. Un service UDP, comme un serveur DNS, publié sans
`/udp`, paraît publié et ne répond à personne.

## 🎲 Exercice 2 : une plage de ports, et quand elle est pleine

Donnez une plage de deux ports d'hôte et lancez trois conteneurs :

```bash
for i in 1 2 3; do
  repondeur --name essai-plage$i -p 127.0.0.1:18310-18311:80 > sortie.txt 2>&1
  echo "conteneur $i : code $?"
done
grep -o 'all ports are allocated' sortie.txt
docker ps --filter name=essai-plage --format '{{.Names}} {{.Ports}}'
```

```text
conteneur 1 : code 0
conteneur 2 : code 0
conteneur 3 : code 125
all ports are allocated
essai-plage2 127.0.0.1:18311->80/tcp
essai-plage1 127.0.0.1:18310->80/tcp
```

Docker a pris le premier port libre de la plage pour chacun. Le troisième est
refusé avec le code 125 : la plage est pleine. Une plage limite ce que l'on
ouvre, et elle se vide quand un conteneur est supprimé.

## 🔀 Exercice 3 : deux publications pour un conteneur

Un conteneur peut porter plusieurs `-p`. Publiez-le sur deux adresses, avec
deux ports différents :

```bash
repondeur --name essai-double -p 127.0.0.1:18320:80 -p "$HOTE":18321:80 > /dev/null
docker port essai-double
nc -w 3 127.0.0.1 18320
nc -w 3 "$HOTE" 18321
nc -w 3 127.0.0.1 18321; echo "code: $?"
```

```text
80/tcp -> 10.10.120.11:18321
80/tcp -> 127.0.0.1:18320
ici ca10712b7a1e
ici ca10712b7a1e
code: 1
```

Le même service répond sur deux ports, et le port prévu pour le réseau reste
fermé en local. Chaque adresse a sa propre règle : c'est plus précis qu'une
publication sur toutes les interfaces.

## 🚫 Exercice 4 : une adresse que la machine n'a pas

Publiez sur une adresse qui n'appartient pas à cette machine, comme on le fait
en recopiant une commande d'un autre serveur :

```bash
repondeur --name essai-ailleurs -p 10.99.99.99:18322:80 2>&1 | grep -o 'failed to bind.*'
docker container inspect essai-ailleurs --format 'statut={{.State.Status}} code={{.State.ExitCode}}'
```

```text
failed to bind host port 10.99.99.99:18322/tcp: cannot assign requested address
statut=created code=128
```

`cannot assign requested address` vient du système : aucune interface ne porte
cette adresse. Ce n'est pas un port pris. Le conteneur existe, à l'état
`created`, et occupe son nom.

## 🛡️ Exercice 5 : changer le défaut d'un réseau

Le défaut d'un `-p` sans adresse se règle réseau par réseau. Créez un réseau
qui publie sur le loopback, puis publiez sans adresse :

```bash
docker network create --opt com.docker.network.bridge.host_binding_ipv4=127.0.0.1 essai-prudent > /dev/null
repondeur --name essai-prudence --network essai-prudent -p 18323:80 > /dev/null
docker container inspect essai-prudence --format '{{json .HostConfig.PortBindings}}'
docker port essai-prudence
```

```text
{"80/tcp":[{"HostIp":"","HostPort":"18323"}]}
80/tcp -> 127.0.0.1:18323
```

La demande ne porte aucune adresse (`HostIp` est vide), et le port n'est ouvert
que sur `127.0.0.1`. `PortBindings` dit ce qui a été demandé, `docker port` ce
qui a été fait. Pour savoir ce qui est ouvert, lisez toujours le second.

## 🧹 Nettoyage

```bash
docker rm -f essai-tcp essai-udp essai-plage1 essai-plage2 essai-plage3 essai-double essai-ailleurs essai-prudence > /dev/null
docker network rm essai-prudent
rm sortie.txt
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
essai-prudent
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset reseau-publication-de-ports
dsoxlab check reseau-publication-de-ports
```

```text
╭─ Résultat : reseau-publication-de-ports ─╮
│  0 / 100 pts                             │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests         │
╰──────────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : trois conteneurs mal publiés, à remettre chacun dans
la portée qui lui convient.

```bash
dsoxlab run reseau-publication-de-ports
dsoxlab challenge reseau-publication-de-ports
```
