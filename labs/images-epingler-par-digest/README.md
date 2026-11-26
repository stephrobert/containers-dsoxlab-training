# Keep a rebuild on its approved base when a tag moves

The lesson writes a digest in a `FROM` and proves it holds. This course looks
for the ways a build can still change: an argument that replaces the pin, a
second forgotten dependency, the trace of what was used, a digest copied to the
wrong place, and a pin whose object was deleted.

You work on an `essai-registre` registry, over HTTP on the loopback, and on
`essai-*` images. The challenge uses `dsoxlab-pin-registry` and
`/opt/lab-image-pin`: do not touch them during the course.

Related page: [Pin a base image, and deliver it offline](https://www.stephane-robert.info/en/docs/docker/pin-a-base-and-deliver-offline/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run images-epingler-par-digest
```

You are connected to `docker.lab`, where the engine runs. `socle` builds a
version of the base, publishes it under the `stable` tag and returns its
digest. `A` is the old one, `B` the new one: `stable` points to `B`. **Keep the
same terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-epingle && cd ~/essai-epingle
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
R=127.0.0.1:15099
docker run -d --name essai-registre -p $R:5000 -e REGISTRY_STORAGE_DELETE_ENABLED=true registry:3.1.2@sha256:d4032d4cc323c1731c707931ecada07a53076eac38e3b61ae57533f170f2c6c3 > /dev/null
sleep 3
socle() { printf 'FROM %s\nRUN echo %s > /version\n' "$IMAGE" "$1" | docker build -q -t $R/essai-socle:stable - > /dev/null; docker push -q $R/essai-socle:stable > /dev/null; docker buildx imagetools inspect $R/essai-socle:stable --format '{{.Manifest.Digest}}'; }
A=$(socle ancien); B=$(socle nouveau)
[ "$A" != "$B" ] && echo 'deux digests'
```

```text
29.9.2
deux digests
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🪪 Exercise 1: a pin replaced at build time

Put the pinned reference in an argument, then build with and without replacing
it:

```bash
printf 'ARG SOCLE=%s/essai-socle@%s\nFROM $SOCLE\nCMD ["cat", "/version"]\n' $R $A > Dockerfile
docker build -q -t essai-a . > /dev/null && docker run --rm essai-a
docker build -q --build-arg SOCLE=$R/essai-socle:stable -t essai-b . > /dev/null && docker run --rm essai-b
grep -c "$A" Dockerfile
```

```text
ancien
nouveau
1
```

The file has not changed and still carries the pin, but the second image is on
the other base. An `ARG` is a default value. If the build chain does not have
to choose the base, write the reference directly in the `FROM`.

## 🧩 Exercise 2: the forgotten dependency

Pin the `FROM`, copy a file from another image by its tag, then move `stable`
back to the old one:

```bash
printf 'FROM %s\nCOPY --from=%s/essai-socle:stable /version /v\nCMD ["cat", "/v"]\n' "$IMAGE" $R > Dockerfile
docker build -q --pull --no-cache -t essai-c . > /dev/null && docker run --rm essai-c
docker buildx imagetools create -t $R/essai-socle:stable $R/essai-socle@$A > /dev/null 2>&1
docker build -q --pull --no-cache -t essai-c . > /dev/null && docker run --rm essai-c
grep -nE '^(FROM|COPY --from)' Dockerfile | grep -v '@sha256:' | cut -d' ' -f1
```

```text
nouveau
ancien
2:COPY
```

The `FROM` is pinned and the product changed anyway. Every image named in the
file is a dependency: each `FROM` and each `COPY --from` that targets an image.
The last command lists those without a digest.

## 🧾 Exercise 3: what was actually used

Ask the build for the list of what it consumed:

```bash
docker build -q --pull --no-cache --metadata-file trace.json -t essai-c . > /dev/null
cat > lire.py <<'EOF'
import json
for m in json.load(open("trace.json"))["buildx.build.provenance"]["materials"]:
    print(m["uri"].split("?")[0], m["digest"]["sha256"][:12])
EOF
python3 lire.py | sed "s/$(echo ${A#sha256:} | cut -c1-12)/(digest de A)/"
```

```text
pkg:docker/127.0.0.1:15099/essai-socle@stable (digest de A)
pkg:docker/alpine@3.24.3 be2656061b53
```

Even for a reference by tag, the trace gives the digest resolved that day. It
is what makes it possible, afterwards, to know which base was used and to pin
it. Keep this file with the delivered image.

## 📍 Exercise 4: a digest copied to the wrong place

Use the right digest with another repository, then the identifier of an image
never published, then a truncated digest:

```bash
essai() { printf 'FROM %s\n' "$1" | docker build --pull - 2>&1 | grep '^ERROR: failed to build' | grep -oE 'not found|insufficient_scope|invalid checksum digest length' | tail -1; }
essai $R/essai-autre@$A
essai essai-a@$(docker image inspect essai-a --format '{{.Id}}')
essai $R/essai-socle@${A%????}
essai $R/essai-socle@$A || echo 'aucune erreur'
```

```text
not found
insufficient_scope
invalid checksum digest length
```

A digest is read in a repository: the same one, asked elsewhere, cannot be
found. A local image's identifier looks like a digest, but no registry knows
it: here, Docker went and asked Docker Hub. Only the repository and digest pair
designates something.

## 🕳️ Exercise 5: a pin on a deleted object

Keep the old base locally, delete it from the registry, then find who still
sees it:

```bash
docker pull -q $R/essai-socle@$A > /dev/null
curl -s -o /dev/null -w '%{http_code}\n' -X DELETE http://$R/v2/essai-socle/manifests/$A
printf 'FROM %s/essai-socle@%s\nCMD ["cat", "/version"]\n' $R $A > Dockerfile
docker build -q --pull -t essai-d . > /dev/null && docker run --rm essai-d
skopeo inspect --tls-verify=false docker://$R/essai-socle@$A 2>&1 | grep -oE 'manifest unknown' | head -1
docker tag $R/essai-socle@$A $R/essai-socle:approuve
docker push -q $R/essai-socle:approuve > /dev/null
skopeo inspect --tls-verify=false docker://$R/essai-socle@$A > /dev/null && echo 'de nouveau lisible, meme digest'
```

```text
202
ancien
manifest unknown
de nouveau lisible, meme digest
```

On this machine, the build succeeds even with `--pull`: the content designated
by the digest is already there. Elsewhere, it would fail, because the registry
no longer has it. The pin guarantees the content, not its preservation. Keep a
tag on approved versions, so that the registry's housekeeping does not take
them away.

## 🧹 Cleanup

```bash
cd ~
docker rm -fv essai-registre > /dev/null
docker images --format '{{.Repository}}:{{.Tag}}@{{.Digest}}' | grep 'essai-' | sed 's/:<none>//; s/\(:[a-z]*\)@.*/\1/' | sort -u | xargs -r docker rmi -f > /dev/null
rm -rf ~/essai-epingle
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker images --format '{{.Repository}}' | grep -c 'essai-\|15547'
```

```text
0
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset images-epingler-par-digest
dsoxlab check images-epingler-par-digest
```

```text
╭─ Result: images-epingler-par-digest ─╮
│  0 / 100 pts                         │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests     │
╰──────────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: an approved base to keep, whatever becomes of
its tag.

```bash
dsoxlab run images-epingler-par-digest
dsoxlab challenge images-epingler-par-digest
```
