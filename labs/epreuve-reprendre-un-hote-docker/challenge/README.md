# Take over a Docker host nobody has maintained

This host has been running for two years and nobody looks after it any more. The
person who set it up has left. The disk is filling up, the daemon's
configuration was never written, and nobody knows who can still talk to it.

You are asked to take it over.

## What is expected at the end

1. `/etc/docker/daemon.json` is **valid** and imposes log **rotation**; the
   daemon has been **restarted** to pick it up; a container created
   **afterwards** does carry that rotation; and the `application` container is
   still running.
2. The space taken for nothing is given back: no **stopped container** of the
   project left, no orphaned **anonymous volume**, and the build cache purged.
   **Both named volumes are intact**, with their data: the application's,
   `dsoxlab-reprise-donnees`, and the backups' one,
   `dsoxlab-reprise-sauvegardes`, which nobody mounts.
3. The `stagiaire-parti` account is no longer in the `docker` group, the
   `exploitant` account still is, and **nobody else** has been added or removed.
4. The `inventaire-outil` tool no longer mounts the daemon's socket: it goes
   through the read-only proxy this lab provides, the `lab-reprise-proxy:1.0`
   image. Through that proxy, a **read request passes** and a **stop request is
   refused**.
5. The daemon no longer listens on **any TCP socket**, with or without TLS:
   remote access goes through the supplied proxy, not the daemon API.

The proxy must be **reachable from the host**: publish a port for it on the
loopback interface. It listens on port 2375 inside its container, and it needs
the daemon's socket to do its work.

The full brief is also on the machine, in `/opt/lab-reprise/MISSION.md`.

## What you do not have to write

Both images are provided, `lab-reprise:1.0` and `lab-reprise-proxy:1.0`. There
is **nothing to build**: the test is about using the proxy, not about writing
one.

Rootless mode is not on this test's syllabus.

## How you are graded

Five checks of equal weight, and **only the final state counts**. No command is
imposed.

The pass mark is **75 out of 100**. One requirement is made up for by no total:
**losing a named volume fails the test**, even with everything else in place. To
reclaim space, the commands that come to mind are the `prune` ones, and they
do not all take the same thing.

Mind the backups one: nobody mounts it, because a backup volume is only mounted
when backing up. A `prune` always spares what is mounted, and then it tells two
families apart: without `-a` it removes only **anonymous** volumes; with `-a` it
also removes the **named** ones nothing mounts. `docker volume prune -a` is what
takes the backups volume away, measured on this version, and the engine says so
in the warning it prints before acting. **A volume that is not mounted is not a
useless volume.**

Four hints are available, and **they cost points**: `dsoxlab hint`.

## Test: take over a Docker host

This host has not been maintained. The disk is filling up, the daemon's
configuration was never written, and nobody knows who can still talk to it.

### The five checks

They are of equal weight, and each rests on a verifiable fact.

#### 1. The daemon runs with log rotation

**Writing `daemon.json` is not enough**: the daemon only rereads it on restart,
and rotation applies to containers created **afterwards**, never retroactively.

The check therefore creates a throwaway container and reads its log
configuration: that is the only place where rotation is a fact rather than an
intention. And the application must be running: restarting the daemon stops
containers with no restart policy and does not bring them back.

#### 2. The space is given back, and the useful volume is intact

**This is the critical requirement: no total makes up for it.**

Two inseparable sides. Stopped containers, orphaned anonymous volumes and the
build cache are what an unmaintained host accumulates, and they serve nobody.

But **both named volumes must remain, with their data**. The application's one is
mounted, so every `prune` spares it. The backups' one is mounted by nobody:
that is the one a `docker volume prune -a` takes away, where a `prune` without
`-a` only takes anonymous volumes. That is the loss you see in
production. **A volume that is not mounted is not a useless volume.**

No dangling images here, and a measurement imposes that: on this version's
containerd store, an image whose reference disappears is collected at once. The
notion comes from the classic store and no longer has an object.

#### 3. The docker group holds only those who should be in it

Three facts, and the third is the one people forget: the intern goes out, the
operator stays, and **nobody else moved**. A removal applied too broadly also
takes out the account that administers the machine: the work looks done, and the
host becomes unreachable to whoever needs it.

#### 4. The tool goes through a read-only proxy

**A socket is not a file.** A `:ro` mount applies to the inode, not to what
travels through it: anything that talks to the socket can create, stop and
delete, hence do on the host everything the daemon can do.

Two facts are measured: the tool no longer mounts the socket, **and** the proxy
refuses a stop request while letting a read through. The second is the real
check: a proxy that let everything through would satisfy the first while
protecting nothing.

#### 5. No TCP socket at all, with or without TLS

A Docker API over TCP without TLS gives anyone who reaches it the power to start
a privileged container, hence to become root on the machine.

**Adding TLS is not enough, and is not what is asked.** This assessment supplies
a socket proxy and requires it to run: remote access goes through that filtering
proxy, so the daemon API has no reason to be exposed over TCP, encrypted or not.
What has no reason to exist is not hardened, it is removed.

The check looks at the **listening sockets** and at the daemon's **effective
command line**, not at a configuration file: correcting a file without
restarting leaves the listener in place, and closing a listener without fixing
what starts the daemon brings it back at the next boot.

### The marking

Five checks of equal weight, pass mark **75 out of 100**, and **only the final
state counts**.

Four hints, from the vaguest to the most explicit, and **they cost points**:

```bash
dsoxlab hint
```
