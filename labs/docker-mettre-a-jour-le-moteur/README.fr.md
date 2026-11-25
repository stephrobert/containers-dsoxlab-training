# Monter le moteur sans que la passerelle s'en aperçoive

La leçon sauvegarde, active `live-restore` et monte la version. Ce cours
prépare la montée sans rien changer : lire une version, la comparer, simuler,
savoir si un conteneur a été relancé, et reconnaître qui le fait tourner.

Vous n'installez rien : toutes les commandes sur les paquets sont des lectures
ou des simulations. Le challenge porte sur `passerelle-sms` et son volume : n'y
touchez pas.

Page associée : [Mettre à jour le moteur et sauvegarder sa configuration](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/mettre-a-jour-le-moteur/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run docker-mettre-a-jour-le-moteur
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. Sa version est celle de
départ du lab. **Gardez le même terminal jusqu'au nettoyage** : les variables
n'existent que dans lui.

```bash
mkdir -p ~/essai-montee && cd ~/essai-montee
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
```

```text
29.8.2
```

Les sorties de ce cours viennent d'un Docker 29.8.2, la version de départ du lab, sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🔢 Exercice 1 : lire une version

Demandez la version installée, celle que le dépôt propose, et les composants :

```bash
apt-cache policy docker-ce | sed -n '2,3p'
apt-cache madison docker-ce | awk '{print $3}' | grep -c '^5:29\.'
dpkg -S /usr/bin/docker /usr/bin/dockerd /usr/bin/containerd
docker version --format 'client {{.Client.Version}}, serveur {{.Server.Version}}'
```

```text
  Installed: 5:29.8.2-1~debian.13~trixie
  Candidate: 5:29.10.1-1~debian.13~trixie
39
docker-ce-cli: /usr/bin/docker
docker-ce: /usr/bin/dockerd
containerd.io: /usr/bin/containerd
client 29.8.2, serveur 29.8.2
```

Installer sans nommer de version prend le candidat, donc la plus récente. Le
client, le démon et containerd viennent de trois paquets différents : monter
l'un ne monte pas les autres. Le préfixe `5:` et le suffixe font partie de la
version à écrire.

## ⚖️ Exercice 2 : comparer deux versions

Cherchez la plus récente de deux versions, de trois façons :

```bash
printf '29.9.2\n29.10.0\n' | sort | tail -1
printf '29.9.2\n29.10.0\n' | sort -V | tail -1
dpkg --compare-versions 29.9.2 lt 29.10.0 && echo '29.9.2 est plus ancienne'
dpkg --compare-versions 5:29.9.2-1 gt 29.10.0-1 && echo 'et pourtant 5:29.9.2-1 gagne'
```

```text
29.9.2
29.10.0
29.9.2 est plus ancienne
et pourtant 5:29.9.2-1 gagne
```

Un tri de texte se trompe, `sort -V` non. Le dernier résultat surprend : le
nombre devant les deux-points, l'époque, passe avant tout le reste. Comparez
toujours des versions complètes, telles que le paquet les porte.

## 🧪 Exercice 3 : simuler

Demandez à `apt-get` ce qu'il ferait, pour une version qui existe et une qui
n'existe pas :

```bash
CIBLE=$(apt-cache madison docker-ce | awk 'NR==1{print $3}')
apt-get -s install "docker-ce=$CIBLE" 2>&1 | grep -E 'held packages will be changed|upgraded'
apt-get -s install docker-ce=1.2.3 2>&1 | grep -o "Version '1.2.3' for 'docker-ce' was not found"
apt-mark showhold | wc -l
docker version --format '{{.Server.Version}}'
```

```text
The following held packages will be changed:
The following packages will be upgraded:
1 upgraded, 0 newly installed, 0 to remove and 5 not upgraded.
Version '1.2.3' for 'docker-ce' was not found
6
29.8.2
```

`-s` n'installe rien, et n'exige pas d'être root. La simulation annonce déjà
que des paquets retenus changeraient : c'est le moment de le découvrir. Comptez
les paquets retenus avant, pour retrouver le même nombre après.

## 🕰️ Exercice 4 : savoir si un conteneur a été relancé

Relancez un conteneur à la main, puis tuez son processus, et relisez trois
champs :

```bash
docker run -d --init --restart unless-stopped --name essai-temoin "$IMAGE" sleep 600 > /dev/null
lit() { docker inspect essai-temoin --format '{{.State.Pid}} {{.State.StartedAt}} {{.RestartCount}}'; }
A=$(lit); docker restart --timeout 1 essai-temoin > /dev/null; B=$(lit)
sudo kill -9 "$(docker inspect essai-temoin --format '{{.State.Pid}}')"; sleep 2; C=$(lit)
echo "compteurs : ${A##* } ${B##* } ${C##* }"
[ "${A%% *}" = "${B%% *}" ] && echo 'meme processus' || echo 'processus change apres restart'
```

```text
compteurs : 0 0 1
processus change apres restart
```

Un `docker restart` ne compte pas dans `RestartCount` : seul un redémarrage par
la politique y entre. Un compteur à zéro ne prouve donc rien. Relevez le PID et
l'heure de démarrage avant l'intervention, et comparez-les après.

## 🧬 Exercice 5 : reconnaître qui le fait tourner

Remontez du processus du conteneur à son parent :

```bash
PERE=$(ps -o ppid= -p "$(docker inspect essai-temoin --format '{{.State.Pid}}')" | tr -d ' ')
ps -o comm= -p "$PERE"
ps -o ppid= -p "$PERE" | tr -d ' '
docker info --format 'live-restore={{.LiveRestoreEnabled}}'
```

```text
containerd-shim
1
live-restore=false
```

Le parent est `containerd-shim`, lui-même rattaché au processus 1 : le démon
Docker n'est pas dans la chaîne. C'est pourquoi un conteneur **peut** survivre
à son arrêt. S'il meurt quand même, c'est que le démon l'arrête exprès, ce que
`live-restore` change.

## 🧹 Nettoyage

```bash
cd ~
docker rm -f essai-temoin > /dev/null
rm -rf ~/essai-montee
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
dsoxlab reset docker-mettre-a-jour-le-moteur
dsoxlab check docker-mettre-a-jour-le-moteur
```

```text
╭─ Résultat : docker-mettre-a-jour-le-moteur ─╮
│  0 / 100 pts                                │
│  ░░░░░░░░░░░░░░░░░░░░  0/5 tests            │
╰─────────────────────────────────────────────╯
```

0 sur 5 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : une version exacte à atteindre, et une passerelle qui
ne doit rien sentir.

```bash
dsoxlab run docker-mettre-a-jour-le-moteur
dsoxlab challenge docker-mettre-a-jour-le-moteur
```
