# Recover the original release after its tag has moved

The lesson moves a tag to another content, then recovers the original content
by pulling it by its digest. This course goes further on three points. First,
what Docker does when a reference carries both a tag and a digest. Then, how
to read, on a running container, the reference that started it. Finally, what
the registry and the engine keep of a content that lost its tag.

You work in `~/essai-digest`, with a practice registry on port `5098` and
`127.0.0.1:5098/essai/*` images. The challenge uses another registry, another
release and a container already running: you will do it on your own, at the
end.

Related page: [Publish and pull an image in a controlled way](https://www.stephane-robert.info/en/docs/docker/publish-and-pull-an-image/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run registry-tag-contre-digest
```

You are now connected to `docker.lab`, a Debian 13 where the Docker engine
runs. Create the practice directory, store the base images in variables, and
start the practice registry. **Keep the same terminal until the cleanup**: the
variables only exist in it.

```bash
mkdir -p ~/essai-digest && cd ~/essai-digest
REGISTRE=registry:3.1.2@sha256:d4032d4cc323c1731c707931ecada07a53076eac38e3b61ae57533f170f2c6c3
ALPINE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker run -d --name essai-depot-digest -p 127.0.0.1:5098:5000 -v essai-depot-digest:/var/lib/registry "$REGISTRE" > /dev/null
sleep 2
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on
24 November 2026.

Now publish the situation of the lesson: a first version under the `prod` tag,
whose digest you keep in a variable, then a second version under the same tag.
Also look at what the engine keeps locally:

```bash
printf 'FROM %s\nCOPY version.txt /version.txt\nCMD ["cat", "/version.txt"]\n' "$ALPINE" > Dockerfile
echo "version A" > version.txt
docker build -q -t 127.0.0.1:5098/essai/carnet:prod . > /dev/null
docker push -q 127.0.0.1:5098/essai/carnet:prod > /dev/null
D=$(docker image inspect 127.0.0.1:5098/essai/carnet:prod --format '{{range .RepoDigests}}{{println .}}{{end}}' | grep '^127.0.0.1:5098/' | cut -d@ -f2)
echo "digest of version A: $D"
echo "version B" > version.txt
docker build -q -t 127.0.0.1:5098/essai/carnet:prod . > /dev/null
docker push -q 127.0.0.1:5098/essai/carnet:prod > /dev/null
docker run --rm 127.0.0.1:5098/essai/carnet:prod
docker images -a --digests 127.0.0.1:5098/essai/carnet
```

```text
digest of version A: sha256:df8a3e801ded0a17202e98730f83b9ea0e42294ac15f73fa3d11d1e830a620a2
version B
REPOSITORY                    TAG       DIGEST                                                                    IMAGE ID       CREATED          SIZE
127.0.0.1:5098/essai/carnet   prod      sha256:0c4a984661806acb138b711a97aa4cf9e460df0ad3d082cbfa48ab0c399a8fec   0c4a98466180   18 minutes ago   13MB
```

The `prod` tag now points to version B, and only the `D` variable keeps the
address of version A. Notice the last output: version A no longer shows. As
soon as `prod` was rebuilt, the old image had no local name left, and this
engine no longer lists it.

## 🔀 Exercise 1: a tag and a digest in the same reference

A reference can carry both: `repository:tag@digest`. Which part does Docker
follow? Try with a tag that does not exist, then with the right tag, keeping
the digest of version A:

```bash
docker run --rm "127.0.0.1:5098/essai/carnet:inexistant@$D"; echo "exit code: $?"
docker run --rm "127.0.0.1:5098/essai/carnet:prod@$D"
```

```text
Unable to find image '127.0.0.1:5098/essai/carnet:inexistant@sha256:df8a3e801ded0a17202e98730f83b9ea0e42294ac15f73fa3d11d1e830a620a2' locally
127.0.0.1:5098/essai/carnet@sha256:df8a3e801ded0a17202e98730f83b9ea0e42294ac15f73fa3d11d1e830a620a2: Pulling from essai/carnet
62c342681880: Pulling fs layer
7b229517ed22: Pulling fs layer
62c342681880: Already exists
7b229517ed22: Already exists
44136fa355b3: Already exists
62c342681880: Pull complete
987c1ab94d4c: Download complete
Digest: sha256:df8a3e801ded0a17202e98730f83b9ea0e42294ac15f73fa3d11d1e830a620a2
Status: Downloaded newer image for 127.0.0.1:5098/essai/carnet@sha256:df8a3e801ded0a17202e98730f83b9ea0e42294ac15f73fa3d11d1e830a620a2
version A
exit code: 0
version A
```

At the first command, Docker no longer had version A locally: it pulled it from
the registry. Look at the `Pulling from` line: the reference appears there
without the tag, reduced to `repository@digest`. The second had nothing to
pull. Both commands show version A,
while `prod` points to B and the `inexistant` tag exists nowhere. When a
reference carries a digest, Docker follows it and ignores the tag. The tag is
only left there to help human reading. A wrong tag raises no error, which can
mislead a reviewer: they think they read `prod`, while the version started is
the one of the digest.

## 🔎 Exercise 2: the reference that started a container

The challenge checks how a container was started. Docker keeps this
information. Start two containers, one by the tag, the other by the digest,
then compare two fields: `.Config.Image`, the reference written at start, and
`.Image`, the identifier of the image really used.

```bash
docker run -d --name essai-par-tag 127.0.0.1:5098/essai/carnet:prod sleep 600 > /dev/null
docker run -d --name essai-par-digest "127.0.0.1:5098/essai/carnet@$D" sleep 600 > /dev/null
for c in essai-par-tag essai-par-digest; do
  docker inspect "$c" --format "$c"'
  Config.Image = {{.Config.Image}}
  Image        = {{.Image}}'
done
```

```text
essai-par-tag
  Config.Image = 127.0.0.1:5098/essai/carnet:prod
  Image        = sha256:0c4a984661806acb138b711a97aa4cf9e460df0ad3d082cbfa48ab0c399a8fec
essai-par-digest
  Config.Image = 127.0.0.1:5098/essai/carnet@sha256:df8a3e801ded0a17202e98730f83b9ea0e42294ac15f73fa3d11d1e830a620a2
  Image        = sha256:df8a3e801ded0a17202e98730f83b9ea0e42294ac15f73fa3d11d1e830a620a2
```

The first container keeps the text `:prod`. To know which version it runs, you
must read `.Image`, then compare it to the digest of each version. The second
keeps the reference with the digest: it points to a single content, which the
next move of the tag does not change. On this engine, which stores
images in containerd, `.Image` is also the pushed digest. The lesson warns
that this is not a guarantee of Docker.

## 🗂️ Exercise 3: what the registry keeps without a tag

The registry only lists tags. The content of version A no longer has one, but
it is still there. Ask for the list of tags, then query the manifest of
version A by its digest:

```bash
curl -s http://127.0.0.1:5098/v2/essai/carnet/tags/list
curl -sI -H 'Accept: application/vnd.oci.image.index.v1+json' "http://127.0.0.1:5098/v2/essai/carnet/manifests/$D" | grep -iE '^HTTP|docker-content-digest'
```

```text
{"name":"essai/carnet","tags":["prod"]}
HTTP/1.1 200 OK
Docker-Content-Digest: sha256:df8a3e801ded0a17202e98730f83b9ea0e42294ac15f73fa3d11d1e830a620a2
```

The list only holds `prod`. The API offers no list of the contents without a
tag: had nobody kept the digest of version A, it could not be found through
the API. Yet the request by digest answers `200 OK`. The content exists as
long as the registry does not delete it. That is why the challenge supplies a
delivery note that carries the digest: without it, there would be nothing to
recover.

## 🖥️ Exercise 4: what the engine keeps locally

The engine also saw both versions go by. `docker images --digests` shows, for
each local image, its tag and its digest:

```bash
docker images --digests 127.0.0.1:5098/essai/carnet
```

```text
REPOSITORY                    TAG       DIGEST                                                                    IMAGE ID       CREATED          SIZE
127.0.0.1:5098/essai/carnet   <none>    sha256:df8a3e801ded0a17202e98730f83b9ea0e42294ac15f73fa3d11d1e830a620a2   df8a3e801ded   18 minutes ago   13MB
127.0.0.1:5098/essai/carnet   prod      sha256:0c4a984661806acb138b711a97aa4cf9e460df0ad3d082cbfa48ab0c399a8fec   0c4a98466180   18 minutes ago   13MB
```

The line marked `prod` is version B. Version A appears as `<none>`: before
exercise 1 it was no longer listed, and the pull by digest brought it back, without a local tag. Its digest is there.
It is another way to find it, provided you are on the machine that had the
image.

## 🧹 Cleanup

Remove the containers, the practice registry, its volume, the images and the
directory, then check that nothing is left:

```bash
cd ~
docker rm -f essai-par-tag essai-par-digest essai-depot-digest > /dev/null
docker volume rm essai-depot-digest
docker image rm "127.0.0.1:5098/essai/carnet@$D" 127.0.0.1:5098/essai/carnet:prod > /dev/null
rm -rf ~/essai-digest
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker images --format '{{.Repository}}' | grep -c '^127.0.0.1:5098/'
```

```text
essai-depot-digest
0
0
```

Nothing from this course is left. Then leave the machine and reset the lab.
`dsoxlab reset` replays the cleanup then the setup of the lab: you get back
exactly the starting state of the challenge. It asks you to confirm: answer
`y`.

```bash
exit
dsoxlab reset registry-tag-contre-digest
dsoxlab check registry-tag-contre-digest
```

```text
╭─ Result: registry-tag-contre-digest ─╮
│  0 / 100 pts                         │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests     │
╰──────────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is waiting for
you, untouched.

## 🎯 The challenge

Your turn, on your own this time: a container runs a release whose tag has
moved. Put the original release back in service, started by a reference that
always points to the same content, without touching the tag.

```bash
dsoxlab run registry-tag-contre-digest
dsoxlab challenge registry-tag-contre-digest
```
