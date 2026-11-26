# Image identity: the tag lies, the digest does not

The lesson follows the chain from the tag down to the layers. This course stays
on names: two tags for one image, a container whose tag has gone, a badly
written reference, a rebuild that changes identity, and an identity that
travels.

You work in `~/essai-noms`, on `essai-noms` images. The challenge uses
`inventaire:1.0`: do not touch it during the course.

Related page: [Read an OCI image and its identity](https://www.stephane-robert.info/en/docs/docker/read-an-oci-image-and-its-identity/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run images-identifier-image
```

You are connected to `docker.lab`, where the engine runs. Build a small image.
The `id_de` function gives the identity a name designates. **Keep the same
terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-noms && cd ~/essai-noms
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
printf 'FROM %s\nRUN echo un > /version\nCMD ["sleep","600"]\n' "$IMAGE" > Dockerfile
docker build -q -t essai-noms:1 . > /dev/null
id_de() { docker image inspect "$1" --format '{{.Id}}'; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 👯 Exercise 1: two names for one image

Give the image a second tag, then remove the first one:

```bash
docker tag essai-noms:1 essai-noms:stable
[ "$(id_de essai-noms:1)" = "$(id_de essai-noms:stable)" ] && echo 'une seule image'
docker rmi essai-noms:1
docker images essai-noms --format '{{.Tag}}'
```

```text
une seule image
Untagged: essai-noms:1
stable
```

`docker rmi` answers `Untagged`: it removed a name, and the image stays as long
as another one designates it. The space is only returned with the last name.

## 🕰️ Exercise 2: a container whose tag has gone

Start a container, rebuild the image under the same tag, then compare what runs
and what the tag designates:

```bash
docker run -d --init --name essai-vieux essai-noms:stable > /dev/null
docker ps --filter name=essai-vieux --format '{{.Image}}'
sed -i 's/echo un/echo deux/' Dockerfile
docker build -q -t essai-noms:stable . > /dev/null
docker ps --filter name=essai-vieux --format '{{.Image}}' | grep -cE '^[0-9a-f]{12}$'
docker inspect essai-vieux --format '{{.Config.Image}}'
docker exec essai-vieux cat /version
docker run --rm essai-noms:stable cat /version
```

```text
essai-noms:stable
1
essai-noms:stable
un
deux
```

`docker ps` showed the tag, it now shows an identifier: the name no longer
designates this container's image. `.Config.Image` keeps the text written at
launch, and misleads. An IMAGE column made of digits is therefore a signal.

## ✍️ Exercise 3: a badly written reference

Get it wrong in four ways:

```bash
docker run --rm Essai-Noms:stable true 2>&1 | grep -o 'repository name.*'
docker run --rm essai-noms: true 2>&1 | grep -o 'invalid reference format'
docker run --rm essai-noms true 2>&1 | grep -o "Unable to find image.*"
docker run --rm "essai-noms:nimporte@$(id_de essai-noms:stable)" cat /version
```

```text
repository name (library/Essai-Noms) must be lowercase
invalid reference format
Unable to find image 'essai-noms:latest' locally
deux
```

Upper case and the empty tag are refused. Without a tag, Docker looks for
`latest`, not for the only tag there is. The last try succeeds: when a digest
is given, the tag before it is not checked. Do not trust the readable part of
such a reference.

## 🔁 Exercise 4: rebuilding changes the identity

Build the same Dockerfile twice without cache, then twice with frozen dates:

```bash
for i in 1 2; do docker build -q --no-cache --provenance=false -t essai-noms:libre$i . > /dev/null; done
[ "$(id_de essai-noms:libre1)" = "$(id_de essai-noms:libre2)" ] && echo identiques || echo differentes
for i in 1 2; do SOURCE_DATE_EPOCH=0 docker build -q --no-cache --provenance=false --output type=image,name=essai-noms:fige$i,rewrite-timestamp=true . > /dev/null; done
[ "$(id_de essai-noms:fige1)" = "$(id_de essai-noms:fige2)" ] && echo identiques || echo differentes
```

```text
differentes
identiques
```

The first two images have the same content and two identities, because of the
dates. With frozen dates and no provenance, the identity is the same again. Two
different digests therefore do not prove that the content differs.

## 🧳 Exercise 5: an identity that travels

Save the image to a file, remove it, load it back and compare:

```bash
AVANT=$(id_de essai-noms:stable)
docker save essai-noms:stable -o noms.tar
docker rmi -f essai-noms:stable > /dev/null
docker load -q -i noms.tar
[ "$(id_de essai-noms:stable)" = "$AVANT" ] && echo 'meme identite'
tar xOf noms.tar index.json | grep -c "$AVANT"
```

```text
Loaded image: essai-noms:stable
meme identite
1
```

The identity is the same after the trip, and the archive carries it in its
`index.json`: you can check it before loading the file.

## 🧹 Cleanup

```bash
cd ~
docker rm -f essai-vieux > /dev/null
docker images 'essai-noms' --format '{{.Repository}}:{{.Tag}}' | xargs -r docker rmi -f > /dev/null
rm -r ~/essai-noms
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker images --format '{{.Repository}}' | grep -c '^essai-'
```

```text
0
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset images-identifier-image
dsoxlab check images-identifier-image
```

```text
╭─ Result: images-identifier-image ─╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a tag that did not move, and an image that
changed.

```bash
dsoxlab run images-identifier-image
dsoxlab challenge images-identifier-image
```
