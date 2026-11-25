# Write an AppArmor policy that refuses by default

The lesson writes a profile, compares the modes and reads the log. This course
shows what a path-based profile does not see and how it lives: the same file
under another path, a hard link, a change applied without a restart, a profile
removed too early, and a refusal by omission observed before being applied.

You work in `~/essai-chemins`, with the `essai-aa` profile that you load and
remove. The challenge uses the `dsoxlab-securite-apparmor` profile and its
`worker`: do not touch them during the course.

Related page: [Seccomp and AppArmor profiles for Docker containers](https://www.stephane-robert.info/en/docs/docker/seccomp-and-apparmor-profiles-for-docker-containers/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run securite-apparmor
```

You are connected to `docker.lab`, where the engine runs. The profile allows
everything and refuses one reading. `lit` starts a container under this
profile. **Keep the same terminal until the cleanup**: the variables only exist
in it.

```bash
mkdir -p ~/essai-chemins && cd ~/essai-chemins
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
mkdir notes && echo contenu > notes/secret
cat > profil <<'EOF'
#include <tunables/global>
profile essai-aa flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  network,
  capability,
  file,
  umount,
  signal (receive) peer=runc,
  deny /notes/secret r,
}
EOF
sudo apparmor_parser --skip-cache -a profil
lit() { docker run --rm --network none --security-opt apparmor=essai-aa -v "$PWD/notes:$1" "$IMAGE" sh -c "$2"; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🗺️ Exercise 1: the same file, another path

Read the file, then mount the same directory elsewhere:

```bash
lit /notes 'cat /notes/secret'
lit /autre 'cat /autre/secret'
lit /notes 'ln -s /notes/secret /tmp/lien; cat /tmp/lien'
```

```text
cat: can't open '/notes/secret': Permission denied
contenu
cat: can't open '/tmp/lien': Permission denied
```

The rule bears on a path seen from the container, not on the file. Mounted
elsewhere, it can be read. A symbolic link, on the other hand, does not fool
the kernel: it judges the final path. A `deny` rule on a path therefore depends
on every mount point.

## 🔗 Exercise 2: a hard link

Create a hard link to the file, and also try to rename and copy it:

```bash
lit /notes 'ln /notes/secret /notes/double && cat /notes/double'
lit /notes 'mv /notes/secret /notes/renomme'
lit /notes 'cp /notes/secret /tmp/copie'
sudo rm -f notes/double
```

```text
contenu
mv: can't rename '/notes/secret': Permission denied
cp: can't open '/notes/secret': Permission denied
```

Renaming and copying are refused, since they need the reading. The hard link
passes: `file,` allows it, and it gives the file a second name the rule does
not mention. This is the limit of a list of refusals: it must foresee every
detour.

## ⚡ Exercise 3: a change applied without a restart

Start a container, remove the rule and reload the profile, then put it back:

```bash
docker run -d --init --name essai-vie --security-opt apparmor=essai-aa -v "$PWD/notes:/notes" "$IMAGE" sleep 600 > /dev/null
docker exec essai-vie cat /notes/secret
grep -v deny profil > sans-regle
sudo apparmor_parser --skip-cache -r sans-regle && docker exec essai-vie cat /notes/secret
sudo apparmor_parser --skip-cache -r profil && docker exec essai-vie cat /notes/secret
docker exec --privileged essai-vie cat /notes/secret
```

```text
cat: can't open '/notes/secret': Permission denied
contenu
cat: can't open '/notes/secret': Permission denied
cat: can't open '/notes/secret': Permission denied
```

The reload applies at once to the running container: the same process lost then
regained a right. It is the opposite of seccomp. A mistake in a reloaded
profile therefore hits every container that carries it. The last line shows
that `--privileged` does not escape it.

## 🧨 Exercise 4: a profile removed too early

Remove the profile while the container is still running:

```bash
sudo apparmor_parser -R profil
docker inspect essai-vie --format '{{.State.Status}} {{.AppArmorProfile}}'
cat "/proc/$(docker inspect essai-vie --format '{{.State.Pid}}')/attr/current"
docker exec essai-vie true 2>&1 | grep -o 'failed to apply profile'
docker restart --timeout 1 essai-vie 2>&1 | grep -o 'unable to apply apparmor profile'
docker rm -f essai-vie > /dev/null
```

```text
running essai-aa
unconfined
failed to apply profile
unable to apply apparmor profile
```

`docker inspect` still shows the profile, although the kernel no longer applies
it: the running process is no longer confined. The container can no longer be
entered or restarted. Remove a profile after the last container that uses it,
and believe the kernel rather than `inspect`.

## 📓 Exercise 5: observing before applying

Load in `complain` mode a profile that does not name the file, and read what
the kernel recorded:

```bash
sed -e 's/mediate_deleted/mediate_deleted,complain/' -e '/deny/d' -e 's#  file,#  /notes/ r,\n  /{,usr/}bin/* rix,\n  /{,usr/}lib/** mr,#' profil > observe
sudo apparmor_parser --skip-cache -a observe
lit /notes 'cat /notes/secret /proc/1/attr/current'
sudo dmesg | grep 'profile="essai-aa"' | grep 'name="/notes/secret"' | tail -1 | grep -oE 'apparmor="[A-Z]+"|operation="[a-z]+"|requested_mask="[a-z]+"' | tr '\n' ' '; echo
sed 's/,complain//' observe > applique
sudo apparmor_parser --skip-cache -r applique
lit /notes 'cat /notes/secret'
sudo apparmor_parser -R applique
```

```text
contenu
essai-aa (complain)
apparmor="ALLOWED" operation="open" requested_mask="r"
cat: can't open '/notes/secret': Permission denied
```

In `complain` mode, the reading passes and the kernel records `ALLOWED`: that
is what it would have refused. In `enforce` mode, the same profile refuses,
without any `deny` rule. So look for `ALLOWED` while observing, and `DENIED`
while applying.

## 🧹 Cleanup

```bash
cd ~
sudo aa-status | grep -c essai-aa
rm -rf ~/essai-chemins
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset securite-apparmor
dsoxlab check securite-apparmor
```

```text
╭──── Result: securite-apparmor ────╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a profile to write, which grants only what is
needed.

```bash
dsoxlab run securite-apparmor
dsoxlab challenge securite-apparmor
```
