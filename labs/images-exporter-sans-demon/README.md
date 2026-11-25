# Export an image without the daemon, and keep what must survive

The lesson copies an image to an archive without going through the daemon. This
course adds five moves: reading an index without downloading anything, opening
an image laid out in a directory, weighing a copy of all platforms, storing
several images together, and recognising a damaged archive.

You work in `~/essai-export`, on the Alpine image, with Debian's `skopeo`
installed on the machine. The challenge uses another image and has its own
launcher: do not touch it during the course.

Related page: [Export an image without a daemon with Skopeo](https://www.stephane-robert.info/en/docs/docker/export-an-image-without-a-daemon-with-skopeo/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run images-exporter-sans-demon
```

You are connected to `docker.lab`, where the engine runs. `SOURCE` designates
the image in its registry. **Keep the same terminal until the cleanup**: the
variables only exist in it.

```bash
mkdir -p ~/essai-export && cd ~/essai-export
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
SOURCE=docker://docker.io/library/alpine@${IMAGE#*@}
skopeo --version
```

```text
skopeo version 1.18.0
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🔭 Exercise 1: reading an index without downloading anything

Ask for the raw document, then count what it announces:

```bash
skopeo inspect --raw "$SOURCE" > index.json
python3 -c "
import json
m = json.load(open('index.json'))['manifests']
print(len(m), 'entrees')
print(sorted({x['platform']['architecture'] for x in m}))"
echo "sha256:$(sha256sum index.json | cut -d' ' -f1)" | grep -c "${IMAGE#*@}"
```

```text
16 entrees
['386', 'amd64', 'arm', 'arm64', 'ppc64le', 'riscv64', 's390x', 'unknown']
1
```

A few kilobytes are enough to know the platforms. The `unknown` entries are not
images: they are the build attestations. The document's fingerprint is exactly
the requested digest, which you can check yourself.

## 📂 Exercise 2: an image laid out in a directory

Copy the image into a directory, and compare the name of each file with its
fingerprint:

```bash
skopeo copy -q "$SOURCE" dir:ouvert
ls ouvert | cut -c1-16
for f in ouvert/*; do n=$(basename "$f"); [ "${#n}" = 64 ] && { [ "$(sha256sum "$f" | cut -c1-64)" = "$n" ] && echo conforme; }; done
```

```text
7b229517ed222597
b92841763c5c2140
manifest.json
version
conforme
conforme
```

The `dir:` transport shows what an image really contains: a manifest, a
configuration and layers, each named by its fingerprint. This is what makes it
possible to check an image without running it.

## ⚖️ Exercise 3: a copy of all platforms

Copy the image for this machine, then for all of them:

```bash
skopeo copy -q "$SOURCE" oci:une
skopeo copy -q --all "$SOURCE" oci:toutes
du -sm une toutes
```

```text
4	une
30	toutes
```

Without an option, `skopeo` chooses the machine's platform. `--all` takes the
whole index, and its digest is kept. The weight follows: choose according to
the target machines.

## 🗄️ Exercise 4: several images together

Store the same image twice under two names in the same directory:

```bash
skopeo copy -q "$SOURCE" oci:lot:matin
skopeo copy -q "$SOURCE" oci:lot:soir
du -sm lot
skopeo inspect oci:lot 2>&1 | grep -o 'more than one image in oci'
skopeo inspect oci:lot:soir --format '{{.Os}}'
```

```text
4	lot
more than one image in oci
linux
```

The directory weighs a single image: common layers are written only once. When
it contains several, you must say which one, otherwise `skopeo` refuses to
choose.

## 🩹 Exercise 5: a damaged archive

Change one byte in a layer, then cut an archive, and try to use them:

```bash
skopeo copy -q "$SOURCE" oci-archive:saine.tar:essai-export:1
mkdir a && tar xf saine.tar -C a
printf x | dd of="$(find a/blobs -type f -size +1M)" bs=1 seek=100000 conv=notrunc 2> /dev/null
tar cf abimee.tar -C a .
head -c 2000000 saine.tar > coupee.tar
skopeo copy -q oci-archive:abimee.tar dir:verif 2>&1 | grep -o 'Digest did not match'
docker load -q -i abimee.tar
docker rmi -f essai-export:1 > /dev/null
docker load -q -i coupee.tar 2>&1 | grep -o 'unexpected EOF'
```

```text
Digest did not match
Loaded image: essai-export:1
Error response from daemon: No such image: essai-export:1
unexpected EOF
```

`skopeo` reads each layer again and refuses the changed byte. `docker load`
accepted this damaged archive on this machine, and only refused the cut one. So
check a received archive with `skopeo copy ... dir:`, or with a fingerprint
sent separately, before loading it.

## 🧹 Cleanup

```bash
cd ~
rm -rf ~/essai-export
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset images-exporter-sans-demon
dsoxlab check images-exporter-sans-demon
```

```text
╭─ Result: images-exporter-sans-demon ─╮
│  0 / 100 pts                         │
│  ░░░░░░░░░░░░░░░░░░░░  0/5 tests     │
╰──────────────────────────────────────╯
```

0 out of 5: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: three archives to produce, and a daemon that
must see nothing.

```bash
dsoxlab run images-exporter-sans-demon
dsoxlab challenge images-exporter-sans-demon
```
