# Le réseau par défaut, et ce qu'il ne fait pas

La leçon montre l'adresse, la passerelle et l'absence de noms sur le réseau par
défaut. Ce cours ajoute cinq gestes : une adresse qui change, ce que ce réseau
refuse, un nom posé à la main, l'accès à un service de l'hôte, et l'interface
de l'hôte reliée à un conteneur.

Vous travaillez sur des conteneurs `essai-*`. Le challenge porte sur `avant` et
`arriere` : n'y touchez pas pendant le cours.

Page associée : [Réseau Docker par défaut ou réseau à soi : lequel choisir ?](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/network/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run reseau-bridge-par-defaut
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. La fonction `repondeur`
lance un conteneur qui répond une ligne sur son port 80. **Gardez le même
terminal jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
HOTE=$(ip -o -4 route get 1.1.1.1 | awk '{for (i = 1; i <= NF; i++) if ($i == "src") print $(i + 1)}')
repondeur() { docker run -d "$@" "$IMAGE" sh -c 'exec nc -ll -p 80 -e echo "ici $(hostname)"'; }
docker version --format '{{.Server.Version}}'
adresse() { docker container inspect "$1" --format '{{.Name}} {{.NetworkSettings.Networks.bridge.IPAddress}}'; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 24
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🔄 Exercice 1 : une adresse qui change

Relevez l'adresse d'un conteneur, arrêtez-le, lancez-en un autre, puis relancez
le premier :

```bash
repondeur --name essai-un > /dev/null
adresse essai-un
docker stop --timeout 1 essai-un > /dev/null
repondeur --name essai-deux > /dev/null
docker start essai-un > /dev/null
adresse essai-un
adresse essai-deux
```

```text
/essai-un 172.17.0.4
/essai-un 172.17.0.5
/essai-deux 172.17.0.4
```

`essai-deux` a reçu l'adresse que portait `essai-un`. Une configuration qui
aurait noté cette adresse joindrait maintenant un autre service, sans aucune
erreur. C'est plus grave qu'une panne : la connexion réussit.

## 🚫 Exercice 2 : ce que ce réseau refuse

Essayez de fixer une adresse, de donner un alias, puis de supprimer ce réseau :

```bash
docker run --rm --ip 172.17.0.50 "$IMAGE" true 2>&1 | grep -i 'user'
docker run --rm --network-alias guichet "$IMAGE" true 2>&1 | grep -i 'user'
docker network rm bridge; echo "code: $?"
```

```text
user-specified IP address is supported on user-defined networks only
docker: network-scoped aliases are only supported for user-defined networks
Error response from daemon: bridge is a pre-defined network and cannot be removed
exit status 1
code: 1
```

Les trois demandes sont refusées. Adresse fixe et alias n'existent que sur un
réseau créé par vous, et le réseau par défaut ne se supprime pas. Ces messages
sont la raison la plus courante de passer à un réseau dédié.

## 📒 Exercice 3 : un nom posé à la main

Sans service de noms, `--add-host` écrit une ligne dans le `/etc/hosts` du
conteneur :

```bash
IP=$(adresse essai-un | awk '{print $2}')
docker run -d --name essai-annuaire --add-host guichet:"$IP" "$IMAGE" sleep 600 > /dev/null
docker exec essai-annuaire grep guichet /etc/hosts
docker exec essai-annuaire nc -w 3 guichet 80
docker stop --timeout 1 essai-un > /dev/null
docker exec essai-annuaire nc -w 3 guichet 80; echo "code: $?"
```

```text
172.17.0.5	guichet
ici 376a5cb24b37
code: 1
```

Le nom fonctionne tant que l'adresse est juste. La ligne est écrite à la
création du conteneur et personne ne la met à jour : elle désigne une adresse,
pas un conteneur.

## 🖥️ Exercice 4 : joindre un service de l'hôte

Lancez un serveur web sur l'hôte, puis joignez-le depuis un conteneur par la
passerelle, que `host-gateway` désigne pour vous :

```bash
mkdir -p ~/essai-web && echo "page de l'hôte" > ~/essai-web/index.html
python3 -m http.server 18420 --bind 0.0.0.0 --directory ~/essai-web > /dev/null 2>&1 &
sleep 1
docker run --rm --add-host hote:host-gateway "$IMAGE" sh -c 'grep -c hote /etc/hosts; wget -q -O - http://hote:18420/'
docker run --rm "$IMAGE" wget -q -T 3 -O - http://127.0.0.1:18420/; echo "code: $?"
```

```text
1
page de l'hôte
wget: can't connect to remote host (127.0.0.1): Connection refused
code: 1
```

Le `127.0.0.1` d'un conteneur est le sien, pas celui de l'hôte : la seconde
tentative échoue. `host-gateway` évite d'écrire l'adresse de la passerelle en
dur.

## 🔌 Exercice 5 : l'interface de l'hôte reliée à un conteneur

Chaque conteneur est relié au pont de son réseau par un câble virtuel. Essayez
sur un réseau à part. Le numéro lu dans le conteneur désigne l'interface côté
hôte :

```bash
docker network create --subnet 10.87.1.0/24 essai-pont > /dev/null
repondeur --name essai-cable --network essai-pont > /dev/null
N=$(docker exec essai-cable cat /sys/class/net/eth0/iflink)
ip -o link | grep "^$N:" | awk '{print $2}' | grep -o '^veth'
ip -o link | grep "^$N:" | grep -o 'master br-'
sudo iptables -t nat -S POSTROUTING | grep '10.87.1.0' | grep -oE '10.87.1.0/24|MASQUERADE'
```

```text
veth
master br-
10.87.1.0/24
MASQUERADE
```

L'autre bout du câble est une interface `veth`, rattachée au pont du réseau
(`br-` suivi d'un identifiant). Les dernières lignes viennent de la règle qui
remplace l'adresse du conteneur par celle de l'hôte quand le trafic sort du
pont. Le réseau par défaut suit le même montage, sous un autre nom.

## 🧹 Nettoyage

```bash
docker rm -f essai-un essai-deux essai-annuaire essai-cable > /dev/null
docker network rm essai-pont
pkill -f 'http.server 18420'
rm -r ~/essai-web
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
essai-pont
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset reseau-bridge-par-defaut
dsoxlab check reseau-bridge-par-defaut
```

```text
╭─ Résultat : reseau-bridge-par-defaut ─╮
│  0 / 100 pts                          │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests      │
╰───────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : cartographier ce réseau et obtenir un jeton par une
vraie connexion.

```bash
dsoxlab run reseau-bridge-par-defaut
dsoxlab challenge reseau-bridge-par-defaut
```
