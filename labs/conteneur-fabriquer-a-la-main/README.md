# Build a container by hand

The lesson builds a container with a single `unshare` command, then observes it
with `lsns`, `nsenter` and `/proc`. This course takes the pieces one at a time.
You will see what each namespace changes on its own, and fall into the trap of
a `pid` namespace without its `/proc`. You will also check several copies of a
file against a checksum file. You will see that the host already uses
namespaces. Finally, you will start a detached container that gives you the
prompt back, and read the numbers of a device before creating one.

You work in `~/essai-isolation`, with processes named `essai-*` and without
changing the root. The challenge uses another file system and another host
name: you will do it on your own, at the end.

Related page: [Build a container by hand](https://www.stephane-robert.info/docs/conteneurisation/conteneur-a-la-main/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run conteneur-fabriquer-a-la-main
```

You are now connected to `oci.lab`, a Debian 13 without any container engine.
You are the `ansible` user, and `sudo` gives you root rights. Create the
practice directory. **Keep the same terminal until the cleanup**: a variable
from exercise 5 only exists in it.

```bash
mkdir -p ~/essai-isolation && cd ~/essai-isolation
unshare --version
uname -r
```

```text
unshare from util-linux 2.41.5
6.12.118+deb13-amd64
```

The outputs of this course were captured on this machine on 23 November 2026,
with util-linux 2.41.5 and the 6.12 kernel of Debian 13.8.

## 🧱 Exercise 1: one namespace at a time

The lesson creates five namespaces at once. Create a single one, and see what
it isolates and what it leaves shared. First `uts`, which holds the host name:

```bash
sudo unshare --uts sh -c 'hostname essai-uts; echo "name: $(hostname)"; echo "visible processes: $(ps -e --no-headers | wc -l)"'
echo "host: $(hostname)"
```

```text
name: essai-uts
visible processes: 120
host: oci.lab
```

The shell has another name, and the host keeps its own. But it still sees more
than a hundred processes: the host's. A `uts` namespace only isolates the name.
Do the same with `net`, which holds the network interfaces, and compare with
the host:

```bash
sudo unshare --net ip -brief link
ip -brief link
```

```text
lo               DOWN           00:00:00:00:00:00 <LOOPBACK>
lo               UNKNOWN        00:00:00:00:00:00 <LOOPBACK,UP,LOWER_UP>
enp1s0           UP             52:54:d1:29:00:12 <BROADCAST,MULTICAST,UP,LOWER_UP>
```

In its `net` namespace, the process only sees a `lo` interface, switched off
(`DOWN`). The host has `lo` up and its `enp1s0` card. Each namespace isolates a
single kernel resource. A container is the sum of them.

## 🪤 Exercise 2: `--pid` without `--mount-proc`

The lesson says `--mount-proc` is required, without showing what happens when
you forget it. Create a `pid` namespace without this option:

```bash
sudo unshare --pid --fork sh -c 'echo "my PID: $$"; echo "visible processes: $(ps -e --no-headers | wc -l)"; ps -o pid,comm -p 1'
```

```text
my PID: 1
visible processes: 121
    PID COMMAND
      1 systemd
```

The shell knows it is PID 1: `$$` comes from the kernel. But `ps` still sees
every process of the host, and names `systemd` as PID 1. The reason: `ps` asks
the kernel nothing, it reads the `/proc` directory. This `/proc` is the host's,
mounted for the old namespace. Add the option and compare:

```bash
sudo unshare --pid --fork --mount-proc sh -c 'echo "my PID: $$"; ps -e -o pid,comm'
```

```text
my PID: 1
    PID COMMAND
      1 sh
      2 ps
```

This time, `ps` only sees the shell and itself. `--mount-proc` mounts a fresh
`/proc`, which describes the new namespace. It implies `--mount`, so that this
mount does not touch the host's `/proc`. Remember the symptom: a PID 1 that
sees `systemd` is a `/proc` that did not follow.

## 🔏 Exercise 3: check copies against a checksum file

The lesson checks an archive with a checksum given on the command line. A
publisher rather ships a `SHA256SUMS` file, which lists the checksums of its
files. Create a file, record its checksum, then make two copies of it, one of
them changed by a single byte:

```bash
mkdir -p ~/essai-isolation/sommes && cd ~/essai-isolation/sommes
echo "version 1" > essai-a.txt
sha256sum essai-a.txt > SHA256SUMS
cat SHA256SUMS
mkdir -p copie-1 copie-2
cp essai-a.txt copie-1/
printf 'version 1 ' > copie-2/essai-a.txt
```

```text
3a79bf37b571938d1f2907afb6a643f48088b83769dde8bc58f5ee866a5c3636  essai-a.txt
```

`sha256sum -c` reads the checksum file back, looks for each named file in the
current directory, and compares. Run it from each copy, pointing at the
checksum file of the parent directory:

```bash
cd ~/essai-isolation/sommes/copie-1 && sha256sum -c ../SHA256SUMS 2>&1; echo "exit code: $?"
cd ~/essai-isolation/sommes/copie-2 && sha256sum -c ../SHA256SUMS 2>&1; echo "exit code: $?"
cd ~/essai-isolation
```

```text
essai-a.txt: OK
exit code: 0
essai-a.txt: FAILED
sha256sum: WARNING: 1 computed checksum did NOT match
exit code: 1
```

The first copy answers `OK` and exit code 0. The second answers `FAILED` and
code 1: the space added in place of the line break is enough to change the
checksum. Both copies have the same name and weigh the same 10 bytes: only the
checksum tells them apart.

## 🔭 Exercise 4: the host already uses namespaces

Namespaces are not reserved for containers. List the `uts` namespaces of the
machine, while no container runs on it:

```bash
sudo lsns -t uts
systemctl show systemd-logind -p ProtectHostname
```

```text
        NS TYPE NPROCS   PID USER             COMMAND
4026531838 uts     113     1 root             /sbin/init
4026532274 uts       1   399 root             ├─/usr/lib/systemd/systemd-udevd
4026532277 uts       1   392 systemd-timesync ├─/usr/lib/systemd/systemd-timesyncd
4026532286 uts       1   779 root             ├─/usr/lib/systemd/systemd-logind
4026532345 uts       1   817 polkitd          └─/usr/lib/polkit-1/polkitd --no-debug --log-level=notice
ProtectHostname=yes
```

The first line is the host namespace, shared by more than a hundred processes.
The others belong to systemd services, such as `systemd-logind` or
`systemd-timesyncd`. Their unit sets `ProtectHostname=yes`, which forbids them
to change the host name. systemd enforces this rule by giving them a `uts`
namespace of their own: a name changed there would not leave the namespace. A
namespace isolates one resource. It does not make a container: these services
keep the host root and see all its processes.

## 🚀 Exercise 5: a detached container

In the lesson, the container keeps the terminal while it runs. Start one that
gives you the prompt back. `setsid -f` starts the program in a new session,
without a terminal, and returns at once. The redirections also detach it from
your input and output:

```bash
sudo setsid -f unshare --pid --fork --mount-proc --uts sh -c 'hostname essai-detache; exec sleep 3601' < /dev/null > /dev/null 2>&1
sleep 1
PID=$(pgrep -n -f 'sleep 3601')
ps -o pid,ppid,sid,tty,comm -p "$PID"
```

```text
    PID    PPID     SID TT       COMMAND
  15257   15256   15256 ?        sleep
```

You get your terminal back. The `TT` column shows `?`: the process is attached
to no terminal. Its `SID` is the one of its `unshare` parent: it lives in its
own session. This `PID` is its number seen from the host. The `status` file of
the process also gives its number seen from inside:

```bash
grep NSpid /proc/$PID/status
sudo nsenter --target "$PID" --uts hostname
hostname
```

```text
NSpid:	15257	1
essai-detache
oci.lab
```

The `NSpid` line holds one number per `pid` namespace, from the highest to the
lowest: the number seen from the host, then 1, its number in its container.
`nsenter --uts` reads the host name of the container without touching the
host's.

The `exec sleep 3601` is not decoration. The container lives as long as its
PID 1 lives. Start a container whose program ends at once:

```bash
sudo setsid -f unshare --pid --fork --mount-proc --uts sh -c 'hostname essai-court' < /dev/null > /dev/null 2>&1
sleep 1
pgrep -a -f essai-court || echo "no essai-court process left"
```

```text
no essai-court process left
```

The shell changed the host name, then ended. The kernel then destroyed its
`pid` namespace: nothing is left to observe.

## 🔌 Exercise 6: read the numbers of a device

The lesson creates `/dev/null` with the numbers `1` and `3`. These numbers are
not made up: you read them on the host. `ls -l` shows them in place of the
size, and `stat` gives them in hexadecimal:

```bash
ls -l /dev/null /dev/zero /dev/urandom
stat -c '%n %F major=%t minor=%T' /dev/null /dev/zero
```

```text
crw-rw-rw- 1 root root 1, 3 Nov 23 20:20 /dev/null
crw-rw-rw- 1 root root 1, 9 Nov 23 20:20 /dev/urandom
crw-rw-rw- 1 root root 1, 5 Nov 23 20:20 /dev/zero
/dev/null character special file major=1 minor=3
/dev/zero character special file major=1 minor=5
```

The `c` at the start of the line marks a character device. The first number
(major) names the kernel driver, the second (minor) the device of that driver.
Now create a real `null` and a fake one, then write into both:

```bash
mkdir -p ~/essai-isolation/dev
sudo mknod -m 666 ~/essai-isolation/dev/null c 1 3
touch ~/essai-isolation/dev/faux-null
echo test > ~/essai-isolation/dev/null
echo test > ~/essai-isolation/dev/faux-null
ls -l ~/essai-isolation/dev
```

```text
total 4
-rw-rw-r-- 1 ansible ansible    5 Nov 23 20:38 faux-null
crw-rw-rw- 1 root    root    1, 3 Nov 23 20:38 null
```

The real `null` still shows `1, 3` and kept nothing. The fake one is a regular
file, which kept the 5 bytes written. In a container, this fake `null` is the
one that grows without end when a program writes to it continuously.

## 🧹 Cleanup

Stop the container of exercise 5, remove the practice directory, then check
that nothing is left:

```bash
cd ~
sudo kill -KILL "$PID"
sleep 1
sudo rm -rf ~/essai-isolation
pgrep -a -f 'sleep 3601' || echo "no practice process"
ls -d ~/essai-* 2>/dev/null || echo "no practice directory"
```

```text
no practice process
no practice directory
```

Nothing from this course is left. Then leave the machine and reset the lab.
`dsoxlab reset` replays the cleanup then the setup of the lab: you get back
exactly the starting state of the challenge. It asks you to confirm: answer
`y`.

```bash
exit
dsoxlab reset conteneur-fabriquer-a-la-main
dsoxlab check conteneur-fabriquer-a-la-main
```

```text
╭─ Result: conteneur-fabriquer-a-la-main ─╮
│  0 / 100 pts                            │
│  ░░░░░░░░░░░░░░░░░░░░  0/5 tests        │
╰─────────────────────────────────────────╯
```

0 out of 5: that is the expected result. The challenge is waiting for
you, untouched.

## 🎯 The challenge

Your turn, on your own this time: build a container without an engine, from
the right copy of an archive, with its host name, its namespaces and a real
`/dev/null`, that still runs after you leave.

```bash
dsoxlab run conteneur-fabriquer-a-la-main
dsoxlab challenge conteneur-fabriquer-a-la-main
```
