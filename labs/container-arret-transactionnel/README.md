# Finish an HTTP transaction before stopping

The lesson stops a database cleanly and measures a forced stop. This course
takes the parts apart one by one: a launcher that keeps the signal to itself,
an `--init` that is not enough, an interrupted transaction, a directory without
write permission, and a half-written file.

You work in `~/essai-arret`, on a small program and an SQLite database of your
own. The challenge uses the registry of its project: do not touch it during the
course.

Related page: [Read-only root filesystem, and a shutdown without data loss](https://www.stephane-robert.info/en/docs/docker/use-a-read-only-root-filesystem-and-stop-without-data-loss/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run container-arret-transactionnel
```

You are connected to `docker.lab`, where the engine runs. `essai` starts a
command, stops it, and gives the duration, the code and the log. **Keep the
same terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-arret && cd ~/essai-arret
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
cat > app.sh <<'EOF'
#!/bin/sh
trap 'echo signal recu; sleep 1; echo travail fini; exit 0' TERM
echo pret
while :; do sleep 1 & wait $!; done
EOF
essai() {
  docker run -d --name essai-app -v "$PWD:/a:ro" $2 "$IMAGE" sh -c "$1; echo suite" > /dev/null; sleep 1
  T=$(date +%s); docker stop --timeout 4 essai-app > /dev/null; T=$(( $(date +%s) - T ))
  [ "$T" -ge 4 ] && T='delai epuise' || T='avant le delai'
  echo "$T, code $(docker inspect essai-app --format '{{.State.ExitCode}}') : $(docker logs essai-app 2>&1 | tr '\n' ' ')"
  docker rm essai-app > /dev/null
}
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 📮 Exercise 1: a launcher that keeps the signal

Start the same program in three ways, and stop it:

```bash
essai 'sh /a/app.sh' ''
essai 'sh /a/app.sh & P=$!; trap "kill -TERM $P" TERM; wait $P; wait $P' ''
essai 'exec sh /a/app.sh' ''
```

```text
delai epuise, code 137 : pret
avant le delai, code 0 : pret signal recu travail fini suite
avant le delai, code 0 : pret signal recu travail fini
```

The first launcher receives the signal and does nothing with it: the program is
killed at the end of the delay, code 137. The second one forwards it, then
waits for the end. The third one disappears: `exec` puts the program in its
place.

## 🩹 Exercise 2: an --init that is not enough

Add `--init` to the first launcher, then ask for a signal from inside:

```bash
essai 'sh /a/app.sh' --init
docker run --rm "$IMAGE" sh -c 'kill -9 $$; echo toujours la'
```

```text
avant le delai, code 143 : pret
toujours la
```

The stop is fast, and the program saw nothing: `--init` forwards the signal to
the launcher, which dies, and the container with it. A fast stop is not a clean
stop; look for the program's trace. The second command shows that process 1
ignores even a `kill -9` coming from inside.

## 🧾 Exercise 3: an interrupted transaction

Commit one write, leave another one open, then kill the latter:

```bash
cat > ecrit.py <<'EOF'
import sqlite3, sys, time
c = sqlite3.connect("base.db", isolation_level=None, timeout=1)
c.execute("create table if not exists t(x)")
c.execute("begin")
c.execute("insert into t values (?)", (sys.argv[1],))
if sys.argv[2] == "valide":
    c.execute("commit")
else:
    time.sleep(60)
EOF
lit() { python3 -c 'import sqlite3; print([r[0] for r in sqlite3.connect("base.db").execute("select x from t")])'; }
python3 ecrit.py un valide
python3 ecrit.py deux attend & P=$!
sleep 1; ls base.db*; lit
python3 ecrit.py trois valide 2>&1 | tail -1
{ kill -9 $P; wait $P; } 2> /dev/null
python3 ecrit.py quatre valide; lit; ls base.db*
```

```text
base.db
base.db-journal
['un']
sqlite3.OperationalError: database is locked
['un', 'quatre']
base.db
```

As long as the transaction is open, nobody sees its row and nobody else writes:
`database is locked`. After the `kill -9`, it is cancelled and the rest is
intact. The `-journal` file serves this cancellation: never delete it by hand.

## 🔒 Exercise 4: a directory without write permission

Make the directory non-writable, then the file alone:

```bash
chmod 555 .
python3 ecrit.py cinq valide 2>&1 | tail -1; lit
chmod 755 . && chmod 444 base.db
python3 ecrit.py six valide 2>&1 | tail -1
chmod 644 base.db && python3 ecrit.py sept valide && lit
```

```text
sqlite3.OperationalError: attempt to write a readonly database
['un', 'quatre']
sqlite3.OperationalError: attempt to write a readonly database
['un', 'quatre', 'sept']
```

The same message in both cases. The file was writable the first time, but
SQLite must create its journal next to it: it needs the directory too. For a
non-root service, give it the directory **and** the files already there.

## ✂️ Exercise 5: a half-written file

Kill a container that writes its result directly, then another one that goes
through a temporary file:

```bash
mkdir -m 777 sortie
LENT='i=0; while [ $i -lt 60 ]; do echo $i; i=$((i+1)); sleep 0.1; done'
docker run -d --name essai-direct -v "$PWD/sortie:/s" "$IMAGE" sh -c "{ $LENT; } > /s/direct" > /dev/null
docker run -d --name essai-abri -v "$PWD/sortie:/s" "$IMAGE" sh -c "{ $LENT; } > /s/abri.tmp && mv /s/abri.tmp /s/abri" > /dev/null
sleep 2; docker kill essai-direct essai-abri > /dev/null
[ "$(wc -l < sortie/direct)" -lt 60 ] && echo 'direct : present et incomplet'
[ -e sortie/abri ] || echo 'abri : absent'
docker rm essai-direct essai-abri > /dev/null
```

```text
direct : present et incomplet
abri : absent
```

The first leaves a cut result nothing distinguishes from a good one. The second
only leaves its temporary file: the final name appears only once the write is
finished. It is the same idea as a transaction, for a plain file.

## 🧹 Cleanup

```bash
cd ~
sudo rm -rf ~/essai-arret/sortie
rm -rf ~/essai-arret
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset container-arret-transactionnel
dsoxlab check container-arret-transactionnel
```

```text
╭─ Result: container-arret-transactionnel ─╮
│  0 / 100 pts                             │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests         │
╰──────────────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a registry to stop without losing an order.

```bash
dsoxlab run container-arret-transactionnel
dsoxlab challenge container-arret-transactionnel
```
