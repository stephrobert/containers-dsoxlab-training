# ENTRYPOINT and CMD: which one do your arguments replace?

The lesson shows what your arguments replace. This course shows how an image
declares its command, and what follows: two ways of writing that do not run
alike, an argument cut into pieces, a child image that loses its command, an
entry script that forgets to step aside, and a command added afterwards.

You work in `~/essai-commande`, on `essai-*` images. The challenge uses
`img-cmd:1.0` and `img-entrypoint:1.0`: do not run them during the course.

Related page: [Run a Docker container and choose what it runs](https://www.stephane-robert.info/en/docs/docker/run-a-container/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run container-entrypoint-et-cmd
```

You are connected to `docker.lab`, where the engine runs. `bati` builds an
image from instructions; `voit` shows what it declares. **Keep the same
terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-commande && cd ~/essai-commande
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
bati() { printf 'ARG IMAGE\nFROM %s\n%s\n' "${3:-\$IMAGE}" "$2" | docker build -q --build-arg IMAGE="$IMAGE" -t "essai-$1" -f - . > /dev/null 2>&1; }
voit() { docker image inspect essai-$1 --format 'entree={{json .Config.Entrypoint}} cmd={{json .Config.Cmd}}'; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## ✍️ Exercise 1: two ways of writing

Declare the same command as a list, then as a sentence:

```bash
bati liste 'ENV QUI=monde
CMD ["echo", "bonjour $QUI"]'
bati phrase 'ENV QUI=monde
CMD echo "bonjour $QUI"'
voit liste; docker run --rm essai-liste
voit phrase; docker run --rm essai-phrase
```

```text
entree=null cmd=["echo","bonjour $QUI"]
bonjour $QUI
entree=null cmd=["/bin/sh","-c","echo \"bonjour $QUI\""]
bonjour monde
```

The sentence goes through a shell, which replaces the variable; the list is
executed as is. Use the list by default, and the sentence only when a shell is
needed.

## ✂️ Exercise 2: a cut argument

Pass a sentence to a program that counts its arguments, with and without
quotes, then make a mistake in the list:

```bash
cat > compte.sh <<'EOF'
#!/bin/sh
echo "$# argument(s) : $1"
EOF
chmod +x compte.sh
bati compte 'COPY compte.sh /compte
ENTRYPOINT ["/compte"]'
docker run --rm essai-compte deux mots
docker run --rm essai-compte 'deux mots'
bati simple "CMD ['echo', 'salut']"
voit simple; docker run --rm essai-simple 2>&1 | head -1
```

```text
2 argument(s) : deux
1 argument(s) : deux mots
entree=null cmd=["/bin/sh","-c","['echo', 'salut']"]
/bin/sh: [echo,: not found
```

Each word is an argument, except within quotes. The list requires **double**
quotes: with single ones, Docker takes it for a sentence, without a word at
build time, and the error only arrives at start.

## 👶 Exercise 3: a child image that loses its command

Start from an image that has both, and redefine one then the other:

```bash
bati mere 'ENTRYPOINT ["echo", "mere"]
CMD ["defaut"]'
bati fille 'ENTRYPOINT ["echo", "fille"]' essai-mere
bati cadette 'CMD ["autre"]' essai-mere
voit mere; docker run --rm essai-mere
voit fille; docker run --rm essai-fille
voit cadette; docker run --rm essai-cadette
```

```text
entree=["echo","mere"] cmd=["defaut"]
mere defaut
entree=["echo","fille"] cmd=null
fille
entree=["echo","mere"] cmd=["autre"]
mere autre
```

Redefining the entry point erases the inherited command; redefining the command
keeps the entry point. If you change the entry point of an existing image,
write its command again too.

## 🚪 Exercise 4: an entry script that steps aside

Write two entry scripts, one that starts the command, one that replaces itself
with it:

```bash
printf '#!/bin/sh\necho preparation\n"$@"\necho suite\n' > lance.sh
printf '#!/bin/sh\necho preparation\nexec "$@"\necho suite\n' > place.sh
chmod +x lance.sh place.sh
for s in lance place; do
  bati $s "COPY $s.sh /entree
ENTRYPOINT [\"/entree\"]
CMD [\"sh\", \"-c\", \"echo je suis le processus \$\$; exit 5\"]"
  docker run --rm essai-$s; echo "$s : code $?"
done
```

```text
preparation
je suis le processus 7
suite
lance : code 0
preparation
je suis le processus 1
place : code 5
```

Without `exec`, the command is a child, the script continues and its code
replaces the command's: the failure is lost. With `exec`, the command becomes
process 1 and its code comes out.

## ➕ Exercise 5: a command added afterwards

Enter a container that has an entry point, then look at what `create` recorded:

```bash
bati garde 'ENTRYPOINT ["sleep"]
CMD ["600"]'
docker run -d --init --name essai-garde essai-garde > /dev/null
docker exec essai-garde echo 'sans entree'
docker inspect essai-garde --format '{{.Path}} {{.Args}}'
docker create --name essai-court essai-garde 5 > /dev/null
docker inspect essai-court --format '{{.Path}} {{.Args}}'
docker run --rm essai-garde echo bonjour 2>&1 | grep -o "invalid number 'echo'"
docker rm -f essai-garde essai-court > /dev/null
```

```text
sans entree
sleep [600]
sleep [5]
invalid number 'echo'
```

`docker exec` ignores the image's entry point. `inspect` shows the command
actually retained: look at it when an argument produces a strange error, like
this `sleep echo bonjour`.

## 🧹 Cleanup

```bash
cd ~
docker images -q --filter 'reference=essai-*:latest' | sort -u | xargs docker rmi -f > /dev/null
rm -rf ~/essai-commande
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset container-entrypoint-et-cmd
dsoxlab check container-entrypoint-et-cmd
```

```text
╭─ Result: container-entrypoint-et-cmd ─╮
│  0 / 100 pts                          │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests      │
╰───────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: two images, four containers, and four effects
to obtain.

```bash
dsoxlab run container-entrypoint-et-cmd
dsoxlab challenge container-entrypoint-et-cmd
```
