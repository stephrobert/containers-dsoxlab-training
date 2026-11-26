# Read an OCI image by hand

The lesson opens the Alpine 3.24.2 image with skopeo and jq: it resolves the
index, copies the image into a local layout, follows the chain down to the
layer, then alters the configuration to see the image refused. This course
shows you what it does not. First, why filtering an index on the architecture
alone can return three manifests. Then what an attestation really contains.
Then you will run the program of an image with no engine at all. Finally you
will see what umoci checks before the hash itself, what becomes of a manifest
copied under two names, and what `skopeo inspect` returns on a local layout.

You work on the `hello-world` image, in folders named `/srv/essai-*`. The
challenge is about another image and another layout: you will do it alone, at
the end.

Related page: [Lire une image OCI et vérifier son digest](https://www.stephane-robert.info/docs/conteneurisation/lire-image-oci/) (in French).

## Before you start

Start the lab:

```bash
dsoxlab run image-lire-a-la-main
```

You are now connected to `oci.lab`, a Debian 13 with no container engine at
all. You are the `ansible` user, and `sudo` gives you root rights. The setup
installed the three tools of the lesson:

```bash
skopeo --version
umoci --version
jq --version
```

```text
skopeo version 1.18.0
umoci version 0.4.7+ds-4+b10
jq-1.7
```

The outputs of this course were taken on this machine on 26 November 2026,
with these versions (the Debian package of jq is 1.7.1, but the tool announces
itself as `jq-1.7`). **Keep the same terminal until the cleanup**: the
variables of the exercises only exist in it.

Every command starts from the `hello-world` index, named by its digest so that
your outputs are the ones of this course:

```bash
HW=docker://docker.io/library/hello-world
HW_INDEX=sha256:1e4c05b897a751332ce85c7e9449da2d93514ea2dea6dbb0e2753c9e949b2bfa
```

## Exercise 1: one architecture, three manifests

The lesson looks for the `amd64` manifest by filtering the index on
`platform.architecture`. On Alpine, that is enough. On `hello-world`, look at
what the same filter returns:

```bash
skopeo inspect --raw "$HW@$HW_INDEX" > /tmp/essai-hw.raw
sha256sum /tmp/essai-hw.raw
jq -r '.manifests[] | select(.platform.architecture=="amd64") | "\(.platform.os)  \(.platform["os.version"] // "-")  \(.digest)"' /tmp/essai-hw.raw
```

```text
1e4c05b897a751332ce85c7e9449da2d93514ea2dea6dbb0e2753c9e949b2bfa  /tmp/essai-hw.raw
linux  -  sha256:d1a8d0a4eeb63aff09f5f34d4d80505e0ba81905f36158cc3970d8e07179e59e
windows  10.0.26100.33828  sha256:1adee175b582d2873cb2a3df57f5d0f34ec6625a2e795631663f337fa13c7907
windows  10.0.20348.5873  sha256:f8a7a304519b0fc3d5d8a47bd5b417eecea3f97e8b487e2132a7bfb3e00fc467
```

The `sha256sum` confirms you received the index you asked for. The filter
returns three manifests: one for Linux and two for Windows, which also run on
`amd64` processors. A platform is a system **and** an architecture. Windows
images even add a system version (`os.version`). For the Linux manifest
alone, filter on both fields:

```bash
jq -r '.manifests[] | select(.platform.os=="linux" and .platform.architecture=="amd64") | .digest' /tmp/essai-hw.raw
```

```text
sha256:d1a8d0a4eeb63aff09f5f34d4d80505e0ba81905f36158cc3970d8e07179e59e
```

A script that took the first line of the first filter would be right here, by
luck of order. Nothing guarantees that order in another index.

## Exercise 2: open an attestation

The lesson explains that an `unknown/unknown` entry is an attestation, without
opening it. Find the one attached to the Linux manifest, then copy it into a
layout like an ordinary image:

```bash
LIN=$(jq -r '.manifests[] | select(.platform.os=="linux" and .platform.architecture=="amd64") | .digest' /tmp/essai-hw.raw)
ATT=$(jq -r --arg d "$LIN" '.manifests[] | select(.annotations["vnd.docker.reference.digest"]==$d) | .digest' /tmp/essai-hw.raw)
echo "$ATT"
sudo skopeo copy -q "docker://docker.io/library/hello-world@$ATT" oci:/srv/essai-attestation:attestation
sudo ls -l /srv/essai-attestation/blobs/sha256
```

```text
sha256:8e752a1cddeafc02597e756f4a0ec96e29f63ac4bc4af87682daf3f1de843bb7
total 16
-rw-r--r-- 1 root root  167 Nov 26 06:16 4cc5f49f1578d3d9c4b5f32f6ef7a37d7fadccd4a20f3e29e3bb0ee6cd159f52
-rw-r--r-- 1 root root  566 Nov 26 06:16 8e752a1cddeafc02597e756f4a0ec96e29f63ac4bc4af87682daf3f1de843bb7
-rw-r--r-- 1 root root 4742 Nov 26 06:16 d5e71e642bf52fab99f7dc2746472b824e89b393f60846d6594e7e71aa11c006
```

Three blobs, like an image: a manifest, a configuration and a "layer". But
this layer is not an archive of files. It is a JSON document. Open it:

```bash
cd /srv/essai-attestation/blobs/sha256
M=$(jq -r '.manifests[0].digest' ../../index.json | cut -d: -f2)
P=$(jq -r '.layers[0].digest' "$M" | cut -d: -f2)
jq '{predicateType, builder: .predicate.builder.id, buildType: .predicate.buildType}' "$P"
cd /
```

```text
{
  "predicateType": "https://slsa.dev/provenance/v0.2",
  "builder": "https://github.com/docker-library",
  "buildType": "https://mobyproject.org/buildkit@v1"
}
```

It is a **provenance**: it says who built the image (the docker-library team)
and with what (BuildKit). The Alpine attestation, in the lesson, also carried
an SBOM. The `hello-world` one does not: what an attestation contains depends
on whoever publishes the image.

## Exercise 3: run the program of an image with no engine

An image is only a set of files and a launch sheet. Copy the Linux image into
a layout, then list its layer:

```bash
sudo skopeo copy -q --override-arch amd64 "$HW@$HW_INDEX" oci:/srv/essai-hw:latest
M=$(jq -r '.manifests[0].digest' /srv/essai-hw/index.json | cut -d: -f2)
L=$(jq -r '.layers[0].digest' /srv/essai-hw/blobs/sha256/$M | cut -d: -f2)
C=$(jq -r '.config.digest' /srv/essai-hw/blobs/sha256/$M | cut -d: -f2)
tar -tzvf /srv/essai-hw/blobs/sha256/$L
```

```text
-rwxr-xr-x 0/0           10072 2026-03-23 21:33 hello
```

The layer holds a single file, `hello`, of 10,072 bytes. Take it out of the
archive without unpacking anything else, then read the command the
configuration asks to run:

```bash
tar -xzOf /srv/essai-hw/blobs/sha256/$L hello > /tmp/essai-hello
chmod +x /tmp/essai-hello
/tmp/essai-hello | head -2
jq -c '.config.Cmd' /srv/essai-hw/blobs/sha256/$C
```

```text

Hello from Docker!
["/hello"]
```

The program runs on the host, with no engine. `tar -xzOf` writes the
requested file to standard output instead of creating it on disk. The
configuration says to run `/hello`: that is exactly what you just did, but
with no isolation. The process sees the whole host. What is missing to make
it a container are the namespaces and cgroups of the previous module.

## Exercise 4: the size is checked before the hash

The manifest gives, for each blob, its digest **and its size**. Compare the
announced size with that of the file, then add one byte to the layer, in a
copy of the layout:

```bash
jq '.layers[0].size' /srv/essai-hw/blobs/sha256/$M
stat -c %s /srv/essai-hw/blobs/sha256/$L
sudo cp -a /srv/essai-hw /srv/essai-hw-plus
printf x | sudo tee -a /srv/essai-hw-plus/blobs/sha256/$L > /dev/null
stat -c %s /srv/essai-hw-plus/blobs/sha256/$L
sudo umoci unpack --image /srv/essai-hw-plus:latest /tmp/essai-bundle
```

```text
2415
2415
2416
   ⨯ create runtime bundle: unpack rootfs: discard trailing archive bits: expected 2415 bytes (extra bytes in stream): verified reader size mismatch
```

umoci refuses on the **size** (`size mismatch`), before even comparing the
hashes. That is why the lesson replaces `/bin/sh` with `/bin/xx`, of the same
length: so that only the hash gives the modification away.

Do the same without changing the size: flip one bit in the middle of the
layer, in another copy.

```bash
sudo cp -a /srv/essai-hw /srv/essai-hw-octet
sudo python3 -c 'import sys; p=sys.argv[1]; b=bytearray(open(p,"rb").read()); b[1000]^=1; open(p,"wb").write(b)' /srv/essai-hw-octet/blobs/sha256/$L
stat -c %s /srv/essai-hw-octet/blobs/sha256/$L
sudo umoci unpack --image /srv/essai-hw-octet:latest /tmp/essai-bundle
```

```text
2415
   ⨯ create runtime bundle: unpack rootfs: discard trailing archive bits: gzip: invalid checksum
```

The size is right, but this time the refusal comes from **gzip**: a
compressed archive carries its own checksum, and a flipped bit breaks it. An
altered layer can therefore be refused by three checks: the size, the archive
format, then the hash. Only the last one guarantees that the content is the
one you asked for. The other two only protect against an accident.

## Exercise 5: two names, one manifest

Copy the same image twice into one layout, under two tags:

```bash
sudo skopeo copy -q --override-arch amd64 "$HW@$HW_INDEX" oci:/srv/essai-deux:latest
sudo skopeo copy -q --override-arch amd64 "$HW@$HW_INDEX" oci:/srv/essai-deux:stable
jq -r '.manifests[] | "\(.annotations["org.opencontainers.image.ref.name"])  \(.digest)"' /srv/essai-deux/index.json
ls /srv/essai-deux/blobs/sha256 | wc -l
```

```text
latest  sha256:d1a8d0a4eeb63aff09f5f34d4d80505e0ba81905f36158cc3970d8e07179e59e
stable  sha256:d1a8d0a4eeb63aff09f5f34d4d80505e0ba81905f36158cc3970d8e07179e59e
3
```

`index.json` has two entries, but they point to the same manifest, and the
store only counts three blobs. A blob is stored under the name of its
content: the same content cannot be stored twice. A tag is only a label put
on a digest.

## Exercise 6: what skopeo inspect returns on a layout

The lesson shows that, on the registry, the `Digest` field of
`skopeo inspect` stays the one of the index. Compare with the same field read
on your layout:

```bash
skopeo inspect --format '{{.Digest}}' "$HW@$HW_INDEX"
skopeo inspect --format '{{.Digest}}' oci:/srv/essai-hw:latest
```

```text
sha256:1e4c05b897a751332ce85c7e9449da2d93514ea2dea6dbb0e2753c9e949b2bfa
sha256:d1a8d0a4eeb63aff09f5f34d4d80505e0ba81905f36158cc3970d8e07179e59e
```

On the registry, it is the digest of the index. On the layout, it is the one
of the Linux manifest, since the copy only kept that one. The same field does
not name the same object depending on where you read it. Before writing down
a digest, know what it names.

## Cleanup

Remove everything this course created, then check that nothing is left:

```bash
sudo rm -rf /srv/essai-attestation /srv/essai-hw /srv/essai-hw-plus /srv/essai-hw-octet /srv/essai-deux /tmp/essai-bundle
rm -f /tmp/essai-hw.raw /tmp/essai-hello
ls -d /srv/essai-* /tmp/essai-* 2>/dev/null || echo "no test file left"
```

```text
no test file left
```

Nothing of this course is left. Then leave the machine and reset the lab.
`dsoxlab reset` replays the cleanup then the preparation of the lab: you get
back exactly the starting state of the challenge. It asks you to confirm:
answer `y`.

```bash
exit
dsoxlab reset image-lire-a-la-main
dsoxlab check image-lire-a-la-main
```

```text
╭── Result: image-lire-a-la-main ───╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is waiting for you,
intact.

## The challenge

Your turn, alone this time: copy busybox by digest into a local layout, write
down the digest of its `amd64` manifest, and find the one altered blob of a
layout received from elsewhere.

```bash
dsoxlab run image-lire-a-la-main
dsoxlab challenge image-lire-a-la-main
```
