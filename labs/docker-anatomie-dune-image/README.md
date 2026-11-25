# The anatomy of an image: layers, sharing, configuration

The lesson presents the image, the container and the registry. This course
opens images that you build: an erased file that still weighs, two identical
images that are not, an order that costs a lot, a configuration label, and the
layer each container adds.

You work in `~/essai-couches`, on `essai-*` images. The challenge uses
`greffe:1.0` and `greffe:2.0`: do not examine them during the course.

Related page: [Images, containers and registries: the anatomy](https://www.stephane-robert.info/en/docs/docker/images-containers-and-registries/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run docker-anatomie-dune-image
```

You are connected to `docker.lab`, where the engine runs. `bati` builds an
image from a Dockerfile read on the input; `couches` lists its layers. **Keep
the same terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-couches && cd ~/essai-couches
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
bati() { docker build -q --build-arg IMAGE="$IMAGE" -t "essai-$1" -f - . > /dev/null; }
couches() { docker image inspect "$1" --format '{{range .RootFS.Layers}}{{println .}}{{end}}' | grep sha256; }
couches "$IMAGE" | wc -l
```

```text
29.9.2
1
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 👻 Exercise 1: an erased file that still weighs

Create a file then erase it, first in two instructions, then in a single one:

```bash
printf 'ARG IMAGE\nFROM $IMAGE\nRUN head -c 5000000 /dev/urandom > /gros\nRUN rm /gros\n' | bati deux
printf 'ARG IMAGE\nFROM $IMAGE\nRUN head -c 5000000 /dev/urandom > /gros && rm /gros\n' | bati une
docker save essai-deux -o deux.tar
docker save essai-une -o une.tar
echo "ecart : $(( ($(stat -c %s deux.tar) - $(stat -c %s une.tar)) / 1000000 )) Mo"
docker run --rm essai-deux ls /gros
mkdir x && tar xf deux.tar -C x && for b in x/blobs/sha256/*; do tar tf "$b" 2> /dev/null | grep -E '^gros$|^\.wh\.gros$'; done | sort
```

```text
ecart : 5 Mo
ls: /gros: No such file or directory
.wh.gros
gros
```

The file disappeared from the container and the image still carries its weight:
the second layer only hides it, with a `.wh.` mark. A secret erased this way is
therefore found again in the archive.

## 👯 Exercise 2: two identical images that are not

Build an image, change only a file's date and build again, then change only a
label:

```bash
echo contenu > f; touch -d '2026-01-01' f
printf 'ARG IMAGE\nFROM $IMAGE\nCOPY f /f\n' | bati un
touch -d '2026-02-01' f
printf 'ARG IMAGE\nFROM $IMAGE\nCOPY f /f\n' | bati date
printf 'ARG IMAGE\nFROM $IMAGE\nCOPY f /f\nLABEL note=a\n' | bati note
compare() { [ "$(couches essai-$1)" = "$(couches essai-$2)" ] && C=memes || C=autres; echo "$1 et $2 : $C couches"; [ "$(docker image inspect essai-$1 -f '{{json .Config}}')" = "$(docker image inspect essai-$2 -f '{{json .Config}}')" ] && echo '   meme configuration' || echo '   autre configuration'; }
compare un date
compare un note
docker run --rm essai-date stat -c '%y' /f | cut -c1-10
```

```text
un et date : memes couches
   meme configuration
un et note : memes couches
   autre configuration
2026-01-01
```

A file's date does not count for the build cache: the layer is reused, and the
file keeps its first date. A label changes the configuration without changing a
single layer. Compare the layers to speak of content, and the configuration
apart.

## 🔀 Exercise 3: an order that costs a lot

Write two images twice, with the same heavy instruction before or after the
file that changes:

```bash
echo 1 > v1; echo 2 > v2
for v in 1 2; do
  printf "ARG IMAGE\nFROM \$IMAGE\nRUN seq 500000 > /outils\nCOPY v$v /v\n" | bati avant$v
  printf "ARG IMAGE\nFROM \$IMAGE\nCOPY v$v /v\nRUN seq 500000 > /outils\n" | bati apres$v
done
partage() { comm -12 <(couches essai-$1 | sort) <(couches essai-$2 | sort) | wc -l; }
echo "lourde avant : $(partage avant1 avant2) couches partagees sur $(couches essai-avant1 | wc -l)"
echo "lourde apres : $(partage apres1 apres2) couches partagees sur $(couches essai-apres1 | wc -l)"
```

```text
lourde avant : 2 couches partagees sur 3
lourde apres : 1 couches partagees sur 3
```

The content produced is the same, but the instruction placed after the changing
file is run again, and gives a new layer. Put what changes least first: the
heavy part is then stored only once.

## 🏷️ Exercise 4: what is in no layer

Give an image a variable and a command, and look for them in the files then in
the configuration:

```bash
printf 'ARG IMAGE\nFROM $IMAGE\nENV EQUIPE=paie\nCMD ["echo", "salut"]\n' | bati conf
[ "$(couches essai-conf)" = "$(couches "$IMAGE")" ] && echo 'memes couches que la base'
docker run --rm essai-conf sh -c 'grep -rl EQUIPE=paie /etc /root /home 2> /dev/null | wc -l'
docker image inspect essai-conf --format '{{json .Config.Cmd}} {{json .Config.Env}}' | sed 's/PATH=[^"]*/PATH=.../'
docker run --rm essai-conf env | grep EQUIPE
docker history essai-conf --format '{{.CreatedBy}}' | head -2 | cut -c1-40
```

```text
memes couches que la base
0
["echo","salut"] ["PATH=...","EQUIPE=paie"]
EQUIPE=paie
CMD ["echo" "salut"]
ENV EQUIPE=paie
```

The image has exactly the layers of its base: its command and its variable are
in the configuration, apart. The engine applies them at start. An image is
therefore a stack of files **and** a record.

## 📝 Exercise 5: the layer of each container

Start two containers from the same image, write in one, and see what each
added:

```bash
for c in un deux; do docker run -d --name essai-$c "$IMAGE" sleep 600 > /dev/null; done
docker exec essai-un sh -c 'echo x > /nouveau; echo y >> /etc/motd; rm /etc/issue'
docker diff essai-un | sort
docker diff essai-deux | wc -l
docker exec essai-deux ls /etc/issue
docker commit essai-un essai-fige > /dev/null
echo "couches : $(couches "$IMAGE" | wc -l) puis $(couches essai-fige | wc -l)"
docker rm -f essai-un essai-deux > /dev/null
```

```text
A /nouveau
C /etc
C /etc/motd
D /etc/issue
0
/etc/issue
couches : 1 puis 2
```

Each container has its own write layer; the image's are shared and never
change. `A` is an addition, `C` a change, `D` a deletion. `docker commit`
freezes that layer, without saying how it was made: prefer a Dockerfile.

## 🧹 Cleanup

```bash
cd ~
docker images -q --filter 'reference=essai-*:latest' | sort -u | xargs docker rmi -f > /dev/null
rm -rf ~/essai-couches
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset docker-anatomie-dune-image
dsoxlab check docker-anatomie-dune-image
```

```text
╭─ Result: docker-anatomie-dune-image ─╮
│  0 / 100 pts                         │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests     │
╰──────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: two images to dissect, and a value that is in
no file.

```bash
dsoxlab run docker-anatomie-dune-image
dsoxlab challenge docker-anatomie-dune-image
```
