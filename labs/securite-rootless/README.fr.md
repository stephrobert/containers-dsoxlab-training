# Qualifier un moteur Docker rootless

La leçon installe un moteur rootless et mesure son réseau et ses limites. Ce
cours prépare le compte qui le porte, sans Docker : un service utilisateur sans
session, un bus mal désigné, un service qui s'éteint avec le compte, un root
qui n'en est pas un, et un port interdit.

Vous travaillez sur le compte `essai-r`, créé puis supprimé ici. Le challenge
porte sur le compte `dsoxlab-rootless` : n'y touchez pas pendant le cours.

Page associée : [Exécuter Docker en rootless](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/rootless/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run securite-rootless
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `R` lance une commande
sous le compte `essai-r`. **Gardez le même terminal jusqu'au nettoyage** : les
variables n'existent que dans lui.

```bash
mkdir -p ~/essai-sans-root && cd ~/essai-sans-root
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
sudo useradd -r -m -s /bin/bash essai-r
NUM=$(id -u essai-r)
R() { sudo -u essai-r "$@"; }
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🚪 Exercice 1 : un compte sans session

Interrogez le gestionnaire de services du compte, puis autorisez-le à vivre
sans session :

```bash
R systemctl --user is-active default.target 2>&1 | grep -o 'not defined'
ls -d /run/user/$NUM 2>&1 | grep -o 'No such file'
sudo loginctl enable-linger essai-r && sleep 2
systemctl is-active user@$NUM
sudo stat -c '%U %a' /run/user/$NUM
```

```text
not defined
No such file
active
essai-r 700
```

Un compte système n'a ni session ni gestionnaire de services tant que personne
ne se connecte. `enable-linger` lance ce gestionnaire sans session, et crée le
dossier d'exécution, réservé au compte.

## 🧭 Exercice 2 : un bus mal désigné

Refaites la demande sans variable, avec une mauvaise, avec la bonne, puis d'une
autre façon :

```bash
R systemctl --user is-active default.target 2>&1 | grep -o 'not defined'
R env XDG_RUNTIME_DIR=/run/user/1 systemctl --user is-active default.target 2>&1 | grep -o 'No such file or directory'
R env XDG_RUNTIME_DIR=/run/user/$NUM systemctl --user is-active default.target
sudo systemctl --user -M essai-r@ is-active default.target
```

```text
not defined
No such file or directory
active
active
```

`sudo -u` change de compte sans ouvrir de session : la variable manque
toujours. Les deux erreurs se lisent différemment, l'une dit que rien n'est
désigné, l'autre que le dossier n'existe pas. La forme `-M compte@` évite les
variables.

## 🕯️ Exercice 3 : un service qui s'éteint avec le compte

Créez un service utilisateur, démarrez-le, puis retirez l'autorisation de vivre
sans session :

```bash
R mkdir -p /home/essai-r/.config/systemd/user
printf '[Service]\nExecStart=/bin/sleep 900\n[Install]\nWantedBy=default.target\n' | R tee /home/essai-r/.config/systemd/user/essai.service > /dev/null
GERE="sudo systemctl --user -M essai-r@"
$GERE daemon-reload && $GERE start essai
$GERE is-active essai
$GERE is-enabled essai
systemctl is-active essai
ps -o user= -C sleep | sort -u
sudo loginctl disable-linger essai-r && sleep 12
pgrep -u essai-r -c sleep
```

```text
active
disabled
inactive
essai-r
0
```

Le gestionnaire du système ne connaît pas ce service : `systemctl` sans
`--user` répond `inactive`. Un service démarré n'est pas pour autant activé au
démarrage. Et sans `linger`, il disparaît avec le gestionnaire du compte.

## 🎭 Exercice 4 : un root qui n'en est pas un

Devenez root dans un espace d'utilisateurs, et regardez ce qu'il peut faire :

```bash
R unshare -U -r id -u
R unshare -U -r cat /proc/self/uid_map | awk '{print $1, "devient", ($2 == '$NUM' ? "essai-r" : $2), "sur", $3, "identifiant"}'
R unshare -U -r head -c 1 /etc/shadow
R unshare -U -r sh -c 'touch ~/f; stat -c "vu dedans : %u" ~/f; chown 1 ~/f 2>&1 | grep -o "Invalid argument"'
sudo stat -c 'vu de la machine : %U' /home/essai-r/f
grep -c essai-r /etc/subuid
```

```text
0
0 devient essai-r sur 1 identifiant
head: cannot open '/etc/shadow' for reading: Permission denied
vu dedans : 0
Invalid argument
vu de la machine : essai-r
0
```

L'identifiant 0 du dedans est le compte `essai-r` dehors : il ne lit rien de
plus. Il ne peut pas donner un fichier à l'identifiant 1, qui n'existe pas dans
sa table. C'est le rôle de `/etc/subuid` : fournir d'autres identifiants. Ce
compte système n'en a reçu aucun.

## 🔌 Exercice 5 : un port interdit

Ouvrez un port bas puis un port haut, en compte ordinaire et en root du dedans
:

```bash
cat /proc/sys/net/ipv4/ip_unprivileged_port_start
ouvre() { "$@" python3 -c 'import socket; socket.socket().bind(("127.0.0.1", 80))' 2>&1 | grep -o 'Permission denied'; }
ouvre R
ouvre R unshare -U -r
R python3 -c 'import socket; socket.socket().bind(("127.0.0.1", 8089)); print("8089 ouvert")'
```

```text
1024
Permission denied
Permission denied
8089 ouvert
```

Être root dans l'espace d'utilisateurs ne donne pas de droit sur le réseau de
la machine. Un moteur rootless publie donc au-dessus du seuil affiché en
première ligne, sauf si l'administrateur change ce seuil.

## 🧹 Nettoyage

```bash
cd ~
sudo userdel -r essai-r 2> /dev/null; id essai-r 2>&1 | grep -o 'no such user'
rm -rf ~/essai-sans-root
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
no such user
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset securite-rootless
dsoxlab check securite-rootless
```

```text
╭── Résultat : securite-rootless ───╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/8 tests  │
╰───────────────────────────────────╯
```

0 sur 8 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un démon préparé pour un compte dédié, qui n'attend
que d'être démarré.

```bash
dsoxlab run securite-rootless
dsoxlab challenge securite-rootless
```
