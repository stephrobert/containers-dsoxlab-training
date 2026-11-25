# Give a service back the one capability it really needs

The lesson drops all capabilities and finds the exception from an error. This
course shows what distorts that search: a non-root account, a badly written
list, a root without power, an administration door, and a badly read mask.

You work on `essai-*` containers. The challenge uses the `worker` of its
project: do not touch it during the course.

Related page: [Harden the runtime: capabilities and privileges](https://www.stephane-robert.info/en/docs/devsecops/containers-iac/docker-security/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run securite-capabilities
```

You are connected to `docker.lab`, where the engine runs. **Keep the same
terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-pouvoirs && cd ~/essai-pouvoirs
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
J="docker run --rm --network none"
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 👤 Exercise 1: a non-root account

Look at the masks of a container started under UID 1000, then add a capability
to it:

```bash
$J --user 1000 "$IMAGE" grep -E '^Cap(Eff|Bnd)' /proc/1/status
$J --user 1000 --cap-add NET_ADMIN "$IMAGE" grep -E '^Cap(Eff|Bnd)' /proc/1/status
```

```text
CapEff:	0000000000000000
CapBnd:	00000000a80425fb
CapEff:	0000000000000000
CapBnd:	00000000a80435fb
```

The `CapBnd` ceiling grows, and `CapEff` stays at zero: for a non-root account,
`--cap-add` gives nothing to the process. It only raises what a setuid program
could reach. Read `CapEff` to know what the service can do.

## ✍️ Exercise 2: a badly written list

Try a typo, two ways to write the same name, and contradictory lists:

```bash
$J --cap-add CHWON "$IMAGE" true 2>&1 | grep -o 'unknown capability.*'
$J --cap-drop ALL --cap-add cap_chown "$IMAGE" grep CapEff /proc/1/status
$J --cap-drop ALL --cap-add chown "$IMAGE" grep CapEff /proc/1/status
$J --cap-drop CHOWN --cap-add CHOWN "$IMAGE" grep CapEff /proc/1/status
$J --cap-add ALL --cap-drop ALL "$IMAGE" grep CapEff /proc/1/status
```

```text
unknown capability: "CAP_CHWON"
CapEff:	0000000000000001
CapEff:	0000000000000001
CapEff:	00000000a80425fb
CapEff:	000001ffffffffff
```

A typo stops the start, and neither case nor the prefix matters. The last two
lines are more dangerous: between adding and dropping the same name, the
addition wins. `ALL` on both sides gives every power of the kernel.

## 🪫 Exercise 3: a root without power

Have a root without capabilities do four ordinary things:

```bash
$J --cap-drop ALL "$IMAGE" sh -c 'echo s > /tmp/f; chmod 000 /tmp/f; cat /tmp/f; echo "lire: $?"'
$J --cap-drop ALL "$IMAGE" sh -c 'su nobody -s /bin/sh -c id; echo "changer de compte: $?"'
$J --cap-drop ALL "$IMAGE" sh -c 'sleep 60 & kill $!; echo "tuer son enfant: $?"'
$J --cap-drop ALL "$IMAGE" sh -c 'echo a > /tmp/f; chmod 600 /tmp/f; echo "chmod de son fichier: $?"'
```

```text
cat: can't open '/tmp/f': Permission denied
lire: 1
su: can't set groups: Operation not permitted
changer de compte: 1
tuer son enfant: 0
chmod de son fichier: 0
```

There root becomes an account bound by permissions again, even on its own file.
What touches its own files and processes still works. The message changes too:
`Permission denied` instead of `Operation not permitted`. So do not look for a
single phrase in the logs.

## 🚪 Exercise 4: an administration door

Enter a container without capabilities, normally then with `--privileged`:

```bash
docker run -d --init --name essai-nu --cap-drop ALL "$IMAGE" sleep 600 > /dev/null
docker exec essai-nu grep CapEff /proc/self/status
docker exec --privileged essai-nu grep CapEff /proc/self/status
docker exec --privileged essai-nu chown 5 /etc/motd; echo "code: $?"
docker exec essai-nu grep CapEff /proc/1/status
docker rm -f essai-nu > /dev/null
```

```text
CapEff:	0000000000000000
CapEff:	000001ffffffffff
code: 0
CapEff:	0000000000000000
```

`docker exec --privileged` gives every power to the added process, and not to
the service. A test done this way proves nothing about the service. It is also
one more reason to watch who can reach the engine.

## 🔢 Exercise 5: a badly read mask

Translate the default mask, then compare the same process seen from the
container and from the host:

```bash
python3 -c 'm = 0xa80425fb; print(bin(m).count("1"), [i for i in range(41) if m >> i & 1])'
python3 -c 'print(hex(1 << 0), hex(1 << 10), hex(1 << 13))'
docker run -d --init --name essai-masque --cap-drop ALL --cap-add CHOWN "$IMAGE" sleep 600 > /dev/null
docker exec essai-masque grep CapEff /proc/1/status
grep CapEff "/proc/$(docker inspect essai-masque --format '{{.State.Pid}}')/status"
docker exec --user 1000 essai-masque grep CapEff /proc/self/status
docker rm -f essai-masque > /dev/null
```

```text
14 [0, 1, 3, 4, 5, 6, 7, 8, 10, 13, 18, 27, 29, 31]
0x1 0x400 0x2000
CapEff:	0000000000000001
CapEff:	0000000000000001
CapEff:	0000000000000000
```

Each capability is a bit: number 0 gives `0x1`, number 10 gives `0x400`. The
mask reads just as well from the host. The last one is zero, because
`/proc/self` designates the command started under another account: always read
`/proc/1`.

## 🧹 Cleanup

```bash
cd ~
rm -rf ~/essai-pouvoirs
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset securite-capabilities
dsoxlab check securite-capabilities
```

```text
╭── Result: securite-capabilities ──╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests  │
╰───────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a launcher that stops without its powers, and
only one to give back.

```bash
dsoxlab run securite-capabilities
dsoxlab challenge securite-capabilities
```
