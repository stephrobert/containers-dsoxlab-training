# Remove direct Docker socket access

The lesson removes an account and a socket mount. This course teaches how to
recognise a socket wherever it is, on a small test server: what `ro` protects,
a replaced socket, an inherited mount, a volume that hides a directory, and an
inventory.

You work in `~/essai-prise`, on a Python server of your own. The challenge uses
`dsoxlab-socket-readonly`: do not touch it during the course.

Related page: [Remove direct access to the Docker daemon](https://www.stephane-robert.info/en/docs/docker/remove-direct-access-to-the-docker-daemon/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run securite-socket-lecture-seule
```

You are connected to `docker.lab`, where the engine runs. The server answers
everything it receives on `d/api.sock`. **Keep the same terminal until the
cleanup**: the variables only exist in it.

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

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🛡️ Exercise 1: what ro protects

Mount the socket read-only, write into it, then try to modify it:

```bash
docker run --rm --network none -v "$PWD/d/api.sock:/x:ro" "$IMAGE" sh -c 'echo ordre | nc local:/x; touch /x; rm /x'
```

```text
touch: /x: Read-only file system
rm: can't remove '/x': Resource busy
recu ordre
```

The message went and the answer came back. What is refused is modifying or
erasing the file. A socket is a door: `ro` forbids repainting the door, not
going through it.

## 🔁 Exercise 2: a replaced socket

Mount the file in one container, its directory in another, then restart the
server:

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

The container that received the file keeps the old one, which no longer
answers. The one that received the directory sees the new one. Mounting the
directory is more convenient, and wider: it will also give any socket created
later.

## 🧬 Exercise 3: an inherited mount

Start a container without `-v`, which takes over another's mounts, then go
through a link:

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

`--volumes-from` mentions no path, and the socket is there. Through the link,
Docker shows the link's name and not the directory's: resolve the source with
`readlink -f` before comparing.

## 📦 Exercise 4: a volume that hides a directory

Create a named volume that points to the directory, and look for it in the
inspection:

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

The inspection shows an ordinary volume, stored with Docker. The host directory
only appears in the volume's options. Searching for a path in the mounts is
therefore not enough.

## 🔎 Exercise 5: an inventory

Look for the sockets from inside each container, and compare them with the
host's:

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

The device and inode pair identifies the file, whatever its name. Do not add
`-xdev` to the search: mounts are other file systems, and the last line sees
none of them.

## 🧹 Cleanup

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

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset securite-socket-lecture-seule
dsoxlab check securite-socket-lecture-seule
```

```text
╭─ Result: securite-socket-lecture-seule ─╮
│  0 / 100 pts                            │
│  ░░░░░░░░░░░░░░░░░░░░  0/2 tests        │
╰─────────────────────────────────────────╯
```

0 out of 2: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a container that must no longer reach the
engine, by any path.

```bash
dsoxlab run securite-socket-lecture-seule
dsoxlab challenge securite-socket-lecture-seule
```
