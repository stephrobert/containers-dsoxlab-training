# Retirer l'accès direct au socket Docker

La leçon retire un compte et un montage du socket. Ce cours apprend à
reconnaître un socket où qu'il soit, sur un petit serveur d'essai : ce que `ro`
protège, un socket remplacé, un montage hérité, un volume qui cache un dossier,
et un inventaire.

Vous travaillez dans `~/essai-prise`, sur un serveur Python à vous. Le
challenge porte sur `dsoxlab-socket-readonly` : n'y touchez pas pendant le
cours.

Page associée : [Retirer les accès directs au moteur](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/retirer-les-acces-directs/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run securite-socket-lecture-seule
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. Le serveur répond à
tout ce qu'il reçoit sur `d/api.sock`. **Gardez le même terminal jusqu'au
nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-prise && cd ~/essai-prise
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
mkdir d
cat > serveur.py <<'EOF'
import os, socket
p = "d/api.sock"
if os.path.exists(p):
    os.unlink(p)
s = socket.socket(socket.AF_UNIX)
s.bind(p)
os.chmod(p, 0o666)
s.listen()
while True:
    c, _ = s.accept()
    d = c.recv(99)
    c.sendall(b"recu " + d)
    c.close()
EOF
python3 serveur.py > /dev/null 2>&1 & SERV=$!
sleep 1
```

```text
29.9.2
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🛡️ Exercice 1 : ce que ro protège

Montez le socket en lecture seule, écrivez dedans, puis essayez de le modifier
:

```bash
docker run --rm --network none -v "$PWD/d/api.sock:/x:ro" "$IMAGE" sh -c 'echo ordre | nc local:/x; touch /x; rm /x'
```

```text
recu ordre
touch: /x: Read-only file system
rm: can't remove '/x': Resource busy
```

Le message est parti et la réponse est revenue. Ce qui est refusé, c'est de
modifier ou d'effacer le fichier. Un socket est une porte : `ro` interdit de
repeindre la porte, pas de passer.

## 🔁 Exercice 2 : un socket remplacé

Montez le fichier dans un conteneur, son dossier dans un autre, puis relancez
le serveur :

```bash
docker run -d --init --name essai-fichier -v "$PWD/d/api.sock:/x:ro" "$IMAGE" sleep 600 > /dev/null
docker run -d --init --name essai-dossier -v "$PWD/d:/d:ro" "$IMAGE" sleep 600 > /dev/null
kill $SERV; wait $SERV 2> /dev/null
python3 serveur.py > /dev/null 2>&1 & SERV=$!
sleep 1
docker exec essai-fichier sh -c 'echo a | nc local:/x; echo "code: $?"'
docker exec essai-dossier sh -c 'echo b | nc local:/d/api.sock; echo "code: $?"'
[ "$(docker exec essai-fichier stat -c %i /x)" = "$(stat -c %i d/api.sock)" ] && echo 'fichier : meme inode' || echo 'fichier : autre inode'
[ "$(docker exec essai-dossier stat -c %i /d/api.sock)" = "$(stat -c %i d/api.sock)" ] && echo 'dossier : meme inode' || echo 'dossier : autre inode'
```

```text
code: 1
recu b
code: 0
fichier : autre inode
dossier : meme inode
```

Le conteneur qui a reçu le fichier garde l'ancien, qui ne répond plus. Celui
qui a reçu le dossier voit le nouveau. Monter le dossier est plus commode, et
plus large : il donnera aussi tout socket créé plus tard.

## 🧬 Exercice 3 : un montage hérité

Lancez un conteneur sans `-v`, qui reprend les montages d'un autre, puis passez
par un lien :

```bash
docker run --rm --volumes-from essai-dossier "$IMAGE" ls /d
ln -s d raccourci
docker run --rm -v "$PWD/raccourci:/r:ro" "$IMAGE" ls /r
docker run -d --init --name essai-lien -v "$PWD/raccourci:/r:ro" "$IMAGE" sleep 600 > /dev/null
docker inspect essai-lien --format '{{(index .Mounts 0).Source}}' | sed "s#$HOME#~#"
```

```text
api.sock
api.sock
~/essai-prise/raccourci
```

`--volumes-from` ne cite aucun chemin, et le socket est là. Par le lien, Docker
affiche le nom du lien et pas celui du dossier : résolvez la source avec
`readlink -f` avant de comparer.

## 📦 Exercice 4 : un volume qui cache un dossier

Créez un volume nommé qui pointe vers le dossier, et cherchez-le dans
l'inspection :

```bash
docker volume create -d local -o type=none -o o=bind -o device="$PWD/d" essai-vol > /dev/null
docker run -d --init --name essai-volume -v essai-vol:/v "$IMAGE" sleep 600 > /dev/null
docker inspect essai-volume --format '{{range .Mounts}}{{.Type}} {{.Source}}{{end}}'
docker exec essai-volume sh -c 'echo c | nc local:/v/api.sock'
docker volume inspect essai-vol --format '{{.Options.device}}' | sed "s#$HOME#~#"
```

```text
volume /var/lib/docker/volumes/essai-vol/_data
recu c
~/essai-prise/d
```

L'inspection montre un volume ordinaire, rangé chez Docker. Le dossier de
l'hôte n'apparaît que dans les options du volume. Chercher un chemin dans les
montages ne suffit donc pas.

## 🔎 Exercice 5 : un inventaire

Cherchez les sockets depuis l'intérieur de chaque conteneur, et comparez-les à
celui de l'hôte :

```bash
VRAI=$(stat -c '%d:%i' d/api.sock)
for c in essai-fichier essai-dossier essai-lien essai-volume; do
  docker exec "$c" find / -type s -exec stat -c '%d:%i %n' {} + 2> /dev/null | while read -r id nom; do
    [ "$id" = "$VRAI" ] && echo "$c $nom : le serveur actuel" || echo "$c $nom : un autre socket"
  done
done
docker exec essai-volume find / -xdev -type s | wc -l
```

```text
essai-fichier /x : un autre socket
essai-dossier /d/api.sock : le serveur actuel
essai-lien /r/api.sock : le serveur actuel
essai-volume /v/api.sock : le serveur actuel
0
```

Le couple appareil et inode identifie le fichier, quel que soit son nom.
N'ajoutez pas `-xdev` à la recherche : les montages sont d'autres systèmes de
fichiers, et la dernière ligne n'en voit aucun.

## 🧹 Nettoyage

```bash
cd ~
docker rm -f essai-fichier essai-dossier essai-lien essai-volume > /dev/null
docker volume rm essai-vol > /dev/null
kill $SERV; wait $SERV 2> /dev/null
rm -rf ~/essai-prise
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
dsoxlab reset securite-socket-lecture-seule
dsoxlab check securite-socket-lecture-seule
```

```text
╭─ Résultat : securite-socket-lecture-seule ─╮
│  0 / 100 pts                               │
│  ░░░░░░░░░░░░░░░░░░░░  0/2 tests           │
╰────────────────────────────────────────────╯
```

0 sur 2 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un conteneur qui ne doit plus atteindre le moteur,
par aucun chemin.

```bash
dsoxlab run securite-socket-lecture-seule
dsoxlab challenge securite-socket-lecture-seule
```
