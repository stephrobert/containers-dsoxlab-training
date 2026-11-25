# Measure a targeted seccomp syscall denial

The lesson derives a profile and measures its fields. This course shows how a
profile misleads its author: a file Docker does not read again, an accepted
profile that filters nothing, an error that blames something else, a call that
was not named, and a trial without blocking.

You work in `~/essai-filtre-appels`. The profiles of this course allow
everything but one call, so that the effect shows: they suit no service. The
challenge uses the `worker` of its project: do not touch it during the course.

Related page: [Seccomp and AppArmor profiles for Docker containers](https://www.stephane-robert.info/en/docs/docker/seccomp-and-apparmor-profiles-for-docker-containers/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run securite-seccomp
```

You are connected to `docker.lab`, where the engine runs. `profil` writes a
profile that handles the named calls, and `essai` runs a command with a
profile. **Keep the same terminal until the cleanup**: the variables only exist
in it.

```bash
mkdir -p ~/essai-filtre-appels && cd ~/essai-filtre-appels
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
profil() { printf '{"defaultAction":"SCMP_ACT_ALLOW","syscalls":[{"names":[%s],"action":"%s"%s}]}\n' "$2" "$3" "${4:-}" > "$1"; }
essai() { docker run --rm --network none --security-opt seccomp="$PWD/$1" "$IMAGE" sh -c "$2"; }
profil base.json '"mkdir","mkdirat"' SCMP_ACT_ERRNO
essai base.json 'mkdir /tmp/a'
```

```text
29.9.2
mkdir: can't create directory '/tmp/a': Operation not permitted
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🧊 Exercise 1: a file that is not read again

Start a container, change its profile on disk, then restart it:

```bash
cp base.json vivant.json
docker run -d --init --name essai-appels --security-opt seccomp="$PWD/vivant.json" "$IMAGE" sleep 600 > /dev/null
profil vivant.json '"rmdir"' SCMP_ACT_ERRNO
docker exec essai-appels mkdir /tmp/a
docker restart --timeout 1 essai-appels > /dev/null
docker exec essai-appels mkdir /tmp/a
rm vivant.json && docker restart --timeout 1 essai-appels > /dev/null && docker exec essai-appels mkdir /tmp/a
docker inspect essai-appels --format '{{index .HostConfig.SecurityOpt 0}}' | cut -c1-60
```

```text
mkdir: can't create directory '/tmp/a': Operation not permitted
mkdir: can't create directory '/tmp/a': Operation not permitted
mkdir: can't create directory '/tmp/a': Operation not permitted
seccomp={"defaultAction":"SCMP_ACT_ALLOW","syscalls":[{"name
```

The profile's content is copied into the container at creation. Changing it, or
even deleting it, changes nothing: the container must be recreated. `docker
inspect` shows the profile really applied, which may differ from the file.

## 🕳️ Exercise 2: accepted, and filters nothing

Make a mistake in a key, give an empty profile, then an unknown action:

```bash
sed 's/"syscalls"/"syscals"/' base.json > faute.json
essai faute.json 'mkdir /tmp/a; echo "code: $?"'
echo '{}' > vide.json
essai vide.json 'grep Seccomp: /proc/1/status; unshare -U true; echo "unshare: $?"'
profil action.json '"mkdir"' SCMP_ACT_REFUSE
essai action.json true 2>&1 | grep -o 'string .* for seccomp'
```

```text
code: 0
Seccomp:	0
unshare: 0
string SCMP_ACT_REFUSE is not a valid action for seccomp
```

The misspelled key is ignored. The empty profile is worse: it removes every
filter, and `unshare`, which the default profile refuses, passes. Only the
unknown action stops the start. So check two things: `Seccomp: 2`, and a trial
that must fail.

## 🎭 Exercise 3: an error that blames something else

Have the same refusal return four error numbers:

```bash
for n in 1 13 28 38; do
  profil erreur.json '"mkdir","mkdirat"' SCMP_ACT_ERRNO ",\"errnoRet\":$n"
  essai erreur.json 'mkdir /tmp/a'
done
```

```text
mkdir: can't create directory '/tmp/a': Operation not permitted
mkdir: can't create directory '/tmp/a': Permission denied
mkdir: can't create directory '/tmp/a': No space left on device
mkdir: can't create directory '/tmp/a': Function not implemented
```

The same filter passes itself off as a missing permission, a full disk or a
kernel that is too old. Choose a number your program can handle, and write it
in the profile's documentation. `Function not implemented` (38) has an honest
use: many programs then try another call.

## 🔎 Exercise 4: a call that was not named

Find the call a command really makes, then refuse a neighbouring call, then the
right one:

```bash
strace -f -e trace=mkdir,mkdirat mkdir /tmp/essai-trace 2>&1 | grep -oE '^mkdir(at)?' ; rmdir /tmp/essai-trace
profil voisin.json '"mkdirat"' SCMP_ACT_ERRNO
essai voisin.json 'mkdir /tmp/a; echo "voisin: $?"'
profil bon.json '"mkdir"' SCMP_ACT_ERRNO
essai bon.json 'mkdir /tmp/a; echo "bon: $?"'
```

```text
mkdir
voisin: 0
mkdir: can't create directory '/tmp/a': Operation not permitted
bon: 1
```

One action often has several calls, and each program picks its own. A profile
that names only one lets the others through. `strace` shows the call of a given
program; name the whole family.

## 📓 Exercise 5: a trial without blocking

Replace the refusal with a trace, and read the kernel log:

```bash
profil trace.json '"mkdir","mkdirat"' SCMP_ACT_LOG
essai trace.json 'mkdir /tmp/a; echo "code: $?"'
sudo dmesg | grep 'type=1326' | grep 'comm="mkdir"' | tail -1 | grep -oE 'exe="[^"]*"|syscall=[0-9]+' | tr '\n' ' '; echo
docker exec --privileged essai-appels mkdir /tmp/b
docker rm -f essai-appels > /dev/null
```

```text
code: 0
exe="/bin/busybox" syscall=83
mkdir: can't create directory '/tmp/b': Operation not permitted
```

`SCMP_ACT_LOG` lets the call through and records the program and the call
number (83 is `mkdir` on x86_64). This is how to know who would be hindered
before refusing. The last command shows that the filter also holds for `docker
exec --privileged`.

## 🧹 Cleanup

```bash
cd ~
rm -rf ~/essai-filtre-appels
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset securite-seccomp
dsoxlab check securite-seccomp
```

```text
╭──── Result: securite-seccomp ─────╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a single argument value to refuse, without
reopening anything.

```bash
dsoxlab run securite-seccomp
dsoxlab challenge securite-seccomp
```
