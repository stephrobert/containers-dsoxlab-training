# Publish an image that another client can really pull

The lesson names an image for a registry, pushes it, reads its digest from
`RepoDigests` and proves with Skopeo that the registry serves all its layers.
This course makes you query the registry itself, without Docker: what it
lists, and the digest it announces in its response. You will also see that
one content can carry two tags, and where a push goes when the name has no
registry. To finish, you will play a complete client that has never seen the
image: download, load and run without network.

You work in `~/essai-registre`, with a practice registry on port `5099` and
`127.0.0.1:5099/essai/*` images. The challenge uses another registry, another
image and another repository: you will do it on your own, at the end.

Related page: [Publish and pull an image in a controlled way](https://www.stephane-robert.info/en/docs/docker/publish-and-pull-an-image/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run registry-tag-push-pull
```

You are now connected to `docker.lab`, a Debian 13 where the Docker engine
runs. Create the practice directory, store the two base images of the course
in variables, and start the practice registry. **Keep the same terminal until
the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-registre && cd ~/essai-registre
REGISTRE=registry:3.1.2@sha256:d4032d4cc323c1731c707931ecada07a53076eac38e3b61ae57533f170f2c6c3
ALPINE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker run -d --name essai-registre -p 127.0.0.1:5099:5000 -v essai-registre:/var/lib/registry "$REGISTRE" > /dev/null
sleep 2
docker version --format '{{.Server.Version}}'
skopeo --version
```

```text
29.9.2
skopeo version 1.18.0
```

The outputs of this course were captured on this machine on 24 November 2026,
with Docker Engine 29.9.2 and Skopeo 1.18.0, the Debian package the lab
installs. The lesson runs Skopeo 1.22.3 from its container image: the
commands of this course are the same.

## 📇 Exercise 1: what a registry lists

A registry answers an HTTP API. Two addresses tell what it holds:
`/v2/_catalog` lists the repositories, and `/v2/<repository>/tags/list` the
tags of a repository. Query the practice registry, still empty:

```bash
curl -s http://127.0.0.1:5099/v2/_catalog
```

```text
{"repositories":[]}
```

An empty list: no repository. You will come back to it after the first push,
to see what the registry received without going through Docker.

## 🏷️ Exercise 2: two tags, one content

The lesson moves a tag to another content. The reverse also exists: one
content can carry several tags. Build an image, give it the tags `1.0` and
`courant`, then push both:

```bash
printf 'FROM %s\nCOPY note.txt /note.txt\nCMD ["cat", "/note.txt"]\n' "$ALPINE" > Dockerfile
echo "practice note $(date +%s)" > note.txt
docker build -q -t 127.0.0.1:5099/essai/note:1.0 . > /dev/null
docker tag 127.0.0.1:5099/essai/note:1.0 127.0.0.1:5099/essai/note:courant
docker push -q 127.0.0.1:5099/essai/note:1.0
docker push 127.0.0.1:5099/essai/note:courant
```

```text
127.0.0.1:5099/essai/note:1.0
The push refers to repository [127.0.0.1:5099/essai/note]
7e027b7c7432: Layer already exists
44fb8899d01e: Already exists
44136fa355b3: Already exists
7b229517ed22: Layer already exists
courant: digest: sha256:9a66e9d5a29fd4c09220dda7c56bf725a8497ec2c55affe0bf56813d62254e63 size: 855
```

The first push, run with `-q`, only shows the pushed name. The second sent
nothing: each line says `Already exists` or `Layer already exists`. The
registry had already received everything with the first one, and only added
a name. The last line gives the digest of the `courant` tag: it is the one of
the content pushed as `1.0`.

## 📡 Exercise 3: what the registry answers

Read the list of repositories and tags again, then ask the registry for the
digest of each tag. A `HEAD` request on `/v2/<repository>/manifests/<tag>`
only returns the headers of the response, without the manifest. The
`Docker-Content-Digest` header carries the digest:

```bash
curl -s http://127.0.0.1:5099/v2/_catalog
curl -s http://127.0.0.1:5099/v2/essai/note/tags/list
for t in 1.0 courant; do
  curl -sI -H 'Accept: application/vnd.oci.image.index.v1+json' http://127.0.0.1:5099/v2/essai/note/manifests/$t | grep -iE 'content-type|docker-content-digest'
done
```

```text
{"repositories":["essai/note"]}
{"name":"essai/note","tags":["1.0","courant"]}
Content-Type: application/vnd.oci.image.index.v1+json
Docker-Content-Digest: sha256:9a66e9d5a29fd4c09220dda7c56bf725a8497ec2c55affe0bf56813d62254e63
Content-Type: application/vnd.oci.image.index.v1+json
Docker-Content-Digest: sha256:9a66e9d5a29fd4c09220dda7c56bf725a8497ec2c55affe0bf56813d62254e63
```

The registry knows the `essai/note` repository and its two tags. Both tags
return the same digest, the one the push showed. The `Content-Type` says that
the registry serves an OCI index: the list that groups the image and its
provenance attestation, as in the lesson. The `Accept` header tells the
registry which formats the client can read.

These two requests do not go through Docker. Any HTTP client can therefore
check what a registry serves under a tag, for example in a CI.

## 🚫 Exercise 4: a name without a registry

The lesson warns that an image named without a registry goes to Docker Hub.
Check it with a short name, keeping only the first and last lines of the
output:

```bash
docker tag 127.0.0.1:5099/essai/note:1.0 essai-note:1.0
docker push essai-note:1.0 > push.log 2>&1; echo "exit code: $?"
head -1 push.log
tail -1 push.log
docker image rm essai-note:1.0 > /dev/null
```

```text
exit code: 1
The push refers to repository [docker.io/library/essai-note]
push access denied, repository does not exist or may require authorization: server message: insufficient_scope: authorization failed
```

Docker completed the name into `docker.io/library/essai-note`, the space of
the official images of Docker Hub, where you have no rights. The registry
refused, and the push exits with an error. The `127.0.0.1:5099/` prefix is
therefore what says where the image goes. Without it, Docker picks Docker Hub
for you.

## 🧪 Exercise 5: a client that has never seen the image

The lesson shows that `docker pull` does not prove that a registry serves all
the layers, since Docker already has them. Play a real new client. Skopeo
downloads the image from the registry into an archive, without looking at
Docker's storage. Docker then loads this archive under another name, and runs
it without network:

```bash
skopeo copy -q --src-tls-verify=false docker://127.0.0.1:5099/essai/note:1.0 docker-archive:$HOME/essai-registre/note.tar:essai-copie/note:1.0
ls -l note.tar | awk '{print $5, $9}'
docker load -i note.tar
docker run --rm --network none essai-copie/note:1.0
cat note.txt
```

```text
8722432 note.tar
Loaded image: essai-copie/note:1.0
practice note 1795503973
practice note 1795503973
```

The archive holds everything the registry served. Docker loaded it as
`essai-copie/note:1.0`, and the container, cut from the network by
`--network none`, shows the same note as the original file. Had the registry
lost a layer, `skopeo copy` would have failed. This is the proof that another
machine can recover this image.

## 🧹 Cleanup

Remove the practice registry, its volume, the images and the directory, then
check that nothing is left:

```bash
cd ~
docker rm -f essai-registre > /dev/null
docker volume rm essai-registre
docker image rm 127.0.0.1:5099/essai/note:1.0 127.0.0.1:5099/essai/note:courant essai-copie/note:1.0 > /dev/null
rm -rf ~/essai-registre
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker images --format '{{.Repository}}' | grep -c -e '^127.0.0.1:5099/' -e '^essai-'
```

```text
essai-registre
0
0
```

Nothing from this course is left. Then leave the machine and reset the lab.
`dsoxlab reset` replays the cleanup then the setup of the lab: you get back
exactly the starting state of the challenge. It asks you to confirm: answer
`y`.

```bash
exit
dsoxlab reset registry-tag-push-pull
dsoxlab check registry-tag-push-pull
```

```text
╭─ Result: registry-tag-push-pull ──╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/2 tests  │
╰───────────────────────────────────╯
```

0 out of 2: that is the expected result. The challenge is waiting for
you, untouched.

## 🎯 The challenge

Your turn, on your own this time: publish to the lab registry an image that
only exists in your engine, so that an independent client can recover and run
it identically.

```bash
dsoxlab run registry-tag-push-pull
dsoxlab challenge registry-tag-push-pull
```
