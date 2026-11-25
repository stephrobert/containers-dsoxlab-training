# Retirer un accès Docker qui ne se justifie plus

La leçon retire un compte du groupe et cherche les autres voies. Ce cours
ajoute les pièges du retrait : une commande qui ôte trop, un groupe principal
que l'on oublie, une règle `sudo` équivalente, un socket qui a changé de
groupe, et une permission ouverte à tous.

Vous travaillez sur les comptes `essai-un` et `essai-deux`, créés puis
supprimés ici. Le challenge porte sur `dsoxlab-auditor` : n'y touchez pas, et
ne retirez pas votre propre accès.

Page associée : [Retirer les accès directs au moteur](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/retirer-les-acces-directs/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run securite-groupe-docker
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. La fonction `acces`
essaie vraiment de joindre le moteur sous un compte. **Gardez le même terminal
jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-acces-groupe && cd ~/essai-acces-groupe
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
sudo useradd -m essai-un && sudo useradd -m essai-deux && sudo groupadd essai-equipe
sudo usermod -aG docker,essai-equipe essai-un
acces() { sudo -n -u "$1" docker ps -q > /dev/null 2>&1 && echo "$1 : acces" || echo "$1 : refuse"; }
acces essai-un; acces essai-deux
```

```text
29.9.2
essai-un : acces
essai-deux : refuse
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🧹 Exercice 1 : une commande qui ôte trop

Retirez le compte du groupe en réécrivant la liste, puis en ne retirant que lui
:

```bash
sudo usermod -G docker essai-un; id -nG essai-un
sudo usermod -aG essai-equipe essai-un
sudo gpasswd -d essai-un docker
id -nG essai-un
acces essai-un
```

```text
essai-un docker
Removing user essai-un from group docker
essai-un essai-equipe
essai-un : refuse
```

`usermod -G` sans `-a` remplace toute la liste : le compte a perdu
`essai-equipe` sans que rien le dise. `gpasswd -d` retire un seul groupe et
laisse les autres.

## 🪪 Exercice 2 : un groupe principal que l'on oublie

Donnez `docker` comme groupe principal, puis cherchez le compte dans le groupe
:

```bash
sudo usermod -g docker essai-un
grep '^docker:' /etc/group | grep -c essai-un
acces essai-un
id -gn essai-un
sudo usermod -g essai-un essai-un
acces essai-un
```

```text
0
essai-un : acces
docker
essai-un : refuse
```

Le compte n'est pas dans la ligne du groupe, et il a l'accès : le groupe
principal est écrit dans `/etc/passwd`. Interrogez `id`, jamais le seul fichier
des groupes.

## 🎫 Exercice 3 : une règle sudo équivalente

Autorisez `essai-deux` à lancer `docker` par `sudo`, et lisez un fichier
réservé à root :

```bash
echo 'essai-deux ALL=(root) NOPASSWD: /usr/bin/docker' | sudo tee /etc/sudoers.d/essai > /dev/null
acces essai-deux
sudo -n -u essai-deux sudo -n docker run --rm -v /etc:/e:ro "$IMAGE" head -c 5 /e/shadow; echo
sudo -l -U essai-deux | tail -1
sudo rm /etc/sudoers.d/essai
```

```text
essai-deux : refuse
root:
    (root) NOPASSWD: /usr/bin/docker
```

Le compte est refusé sur le socket, et il lit pourtant `/etc/shadow`. Une règle
`sudo` sur `docker` vaut le groupe. `sudo -l -U` les montre : ajoutez cette
lecture à tout retrait d'accès.

## 🔌 Exercice 4 : un socket qui a changé de groupe

Donnez le socket à un autre groupe, dont le compte est membre :

```bash
sudo chgrp essai-equipe /run/docker.sock
sudo usermod -aG essai-equipe essai-deux
id -nG essai-deux
acces essai-deux
stat -c '%G %a' /run/docker.sock
sudo chgrp docker /run/docker.sock
acces essai-deux
```

```text
essai-deux essai-equipe
essai-deux : acces
essai-equipe 660
essai-deux : refuse
```

Aucune mention de `docker` dans les groupes du compte, et l'accès est là. Ce
n'est pas le nom du groupe qui compte, c'est celui que porte le socket.
Regardez le socket avant les comptes.

## 🌍 Exercice 5 : une permission ouverte à tous

Ouvrez le socket à tous, comme on le lit dans beaucoup de réponses en ligne :

```bash
sudo chmod 666 /run/docker.sock
acces essai-un; acces essai-deux
systemctl cat docker.socket | grep -E 'Socket(Mode|Group)'
sudo chmod 660 /run/docker.sock
acces essai-deux
sudo -n -u essai-deux curl -s --unix-socket /run/docker.sock http://localhost/_ping; echo "code: $?"
```

```text
essai-un : acces
essai-deux : acces
SocketMode=0660
SocketGroup=docker
essai-deux : refuse
code: 7
```

Tous les comptes de la machine ont eu l'équivalent de root, y compris ceux des
services. Le réglage durable est dans l'unité systemd `docker.socket` : c'est
là qu'il faut vérifier que personne n'a écrit 0666. Le dernier essai contrôle
le refus sans passer par `docker`.

## 🧹 Nettoyage

```bash
cd ~
sudo userdel -r essai-un 2> /dev/null; sudo userdel -r essai-deux 2> /dev/null; sudo groupdel essai-equipe
stat -c '%G %a' /run/docker.sock
rm -rf ~/essai-acces-groupe
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
docker 660
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset securite-groupe-docker
dsoxlab check securite-groupe-docker
```

```text
╭─ Résultat : securite-groupe-docker ─╮
│  0 / 100 pts                        │
│  ░░░░░░░░░░░░░░░░░░░░  0/2 tests    │
╰─────────────────────────────────────╯
```

0 sur 2 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un compte à garder, et un privilège à lui retirer
pour de bon.

```bash
dsoxlab run securite-groupe-docker
dsoxlab challenge securite-groupe-docker
```
