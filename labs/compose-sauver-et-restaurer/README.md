# Back up a Compose stack, and restore it elsewhere

The lesson backs up a database, a volume and a configuration, then restores
them. This course shows five backups that look good: a failure hidden by a
pipe, forgotten files, a truncated archive, a restore that changes the owners,
and a database whose roles are missing.

You work in `~/essai-coffre`, on `essai-*` volumes and containers. The
challenge uses the `herbier` stack: do not touch it during the course.

Related page: [Back up and restore an application](https://www.stephane-robert.info/en/docs/docker/back-up-and-restore-a-compose-application/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run compose-sauver-et-restaurer
```

You are connected to `docker.lab`. The `COMPOSE_PROGRESS` variable silences
Compose's progress: only warnings and errors are printed. Fill a volume. **Keep
the same terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-coffre && cd ~/essai-coffre
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
PG=postgres:18.6-alpine3.24@sha256:10a5c69a83035ab5239f5620d708520e8b28f5aa1f2b20143e6024532edadfb5
docker volume create essai-source > /dev/null
docker run --rm -v essai-source:/v "$IMAGE" sh -c 'head -c 300000 /dev/urandom > /v/planche; echo prive > /v/note; chown 4242:4242 /v/note; chmod 600 /v/note; touch /v/.reglage'
```

```text
5.6.1
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 24
November 2026. Addresses and identifiers will differ on your side.

## 🚰 Exercise 1: a failure hidden by a pipe

Archive a directory that does not exist, through a pipe, without then with
`pipefail`:

```bash
docker run --rm -v essai-source:/v:ro "$IMAGE" tar cz -C /v absent 2> /dev/null | cat > vide.tgz; echo "code: $?"
set -o pipefail
docker run --rm -v essai-source:/v:ro "$IMAGE" tar cz -C /v absent 2> /dev/null | cat > vide.tgz; echo "code: $?"
set +o pipefail
tar tzf vide.tgz | wc -l
```

```text
code: 0
code: 1
0
```

A pipe's code is the one of its last command: `cat` succeeded, and the file
exists, empty of any content. `set -o pipefail` makes the failure visible. Put
it at the top of your backup scripts.

## 🙈 Exercise 2: forgotten files

Archive with `*`, then with `.`:

```bash
docker run --rm -v essai-source:/v:ro "$IMAGE" sh -c 'cd /v && tar cz *' > etoile.tgz
tar tzf etoile.tgz | sort
echo '--'
(umask 077; docker run --rm -v essai-source:/v:ro "$IMAGE" tar cz -C /v . > complet.tgz)
tar tzf complet.tgz | sort
stat -c '%a %n' etoile.tgz complet.tgz
```

```text
note
planche
--
./
./.reglage
./note
./planche
664 etoile.tgz
600 complet.tgz
```

The shell does not include hidden files in `*`: `.reglage` is missing, without
any error. `-C /v .` takes the whole directory. The `umask` set in the subshell
also keeps the archive private.

## 🪓 Exercise 3: a truncated archive

Cut the archive, as a full disk would do, then do the same with a database
backup:

```bash
head -c 200000 complet.tgz > coupe.tgz
gzip -t coupe.tgz 2>&1 | grep -o 'unexpected end of file'
docker run -d --name essai-base -e POSTGRES_PASSWORD=demo "$PG" > /dev/null
until docker exec essai-base psql -U postgres -h 127.0.0.1 -c 'select 1' > /dev/null 2>&1; do sleep 1; done
docker exec essai-base psql -U postgres -q -c 'create table t as select i, md5(i::text) from generate_series(1,20000) i'
docker exec essai-base pg_dump -U postgres -Fc postgres > complet.dump
head -c 100000 complet.dump > coupe.dump
docker exec -i essai-base pg_restore --list < coupe.dump | grep -c 'TABLE DATA'
docker exec -i essai-base pg_restore -f /dev/null < coupe.dump > /dev/null 2>&1; echo "coupe: $?"
docker exec -i essai-base pg_restore -f /dev/null < complet.dump; echo "complet: $?"
```

```text
unexpected end of file
1
coupe: 1
complet: 0
```

`gzip -t` sees the cut. `pg_restore --list` does not: the table of contents is
at the start of the file, and it is intact. Having the whole archive read, with
`-f /dev/null`, reveals it without restoring anything.

## 👤 Exercise 4: a restore that changes the owners

Restore into a volume already in use, then into a new volume without being
root:

```bash
docker volume create essai-occupe > /dev/null
docker run --rm -v essai-occupe:/v "$IMAGE" touch /v/ancien
docker run --rm -i -v essai-occupe:/v "$IMAGE" tar xz -C /v < complet.tgz
docker run --rm -v essai-occupe:/v "$IMAGE" sh -c 'ls -A /v; stat -c "%u:%g" /v/note'
docker volume create essai-simple > /dev/null
docker run --rm -v essai-simple:/v "$IMAGE" chown 1001 /v
docker run --rm -i --user 1001 -v essai-simple:/v "$IMAGE" tar xz -C /v < complet.tgz; echo "code: $?"
docker run --rm -v essai-simple:/v "$IMAGE" stat -c '%u:%g' /v/note
```

```text
.reglage
ancien
note
planche
4242:4242
code: 0
1001:0
```

`tar` adds without erasing: `ancien` is mixed with the restored files. Restore
into an empty volume. Without root, the extraction succeeds too, but `note` no
longer belongs to 4242: the original application will not be able to read it.

## 🎭 Exercise 5: a database without its roles

Grant a right to a role, back up, then restore into a new server:

```bash
docker exec essai-base psql -U postgres -q -c 'create role lecteur' -c 'grant select on t to lecteur'
docker exec essai-base pg_dump -U postgres -Fc postgres > droits.dump
docker run -d --name essai-cible -e POSTGRES_PASSWORD=demo "$PG" > /dev/null
until docker exec essai-cible psql -U postgres -h 127.0.0.1 -c 'select 1' > /dev/null 2>&1; do sleep 1; done
docker exec -i essai-cible pg_restore -U postgres -d postgres < droits.dump 2>&1 | grep -o 'role "lecteur" does not exist'
docker exec essai-cible psql -U postgres -Atc 'select count(*) from t'
docker exec essai-base pg_dumpall -U postgres --roles-only | grep 'CREATE ROLE lecteur'
```

```text
role "lecteur" does not exist
20000
CREATE ROLE lecteur;
```

The 20,000 rows are there, but the right could not be given back: `pg_dump`
does not back up roles, which belong to the server. `pg_dumpall --roles-only`
gives them. That output contains the password hashes: protect it like the rest.

## 🧹 Cleanup

```bash
cd ~
docker rm -f -v essai-base essai-cible > /dev/null
docker volume rm essai-source essai-occupe essai-simple > /dev/null
rm -r ~/essai-coffre
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker network ls --format '{{.Name}}' | grep -c '^essai-'
docker volume ls --format '{{.Name}}' | grep -c '^essai-'
```

```text
0
0
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset compose-sauver-et-restaurer
dsoxlab check compose-sauver-et-restaurer
```

```text
╭─ Result: compose-sauver-et-restaurer ─╮
│  0 / 100 pts                          │
│  ░░░░░░░░░░░░░░░░░░░░  0/5 tests      │
╰───────────────────────────────────────╯
```

0 out of 5: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a herbarium in service, to bring up elsewhere
without touching it.

```bash
dsoxlab run compose-sauver-et-restaurer
dsoxlab challenge compose-sauver-et-restaurer
```
