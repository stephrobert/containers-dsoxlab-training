# Test: take over a Docker host

This host has not been maintained. The disk is filling up, the daemon's
configuration was never written, and nobody knows who can still talk to it.

## The five checks

They are of equal weight, and each rests on a verifiable fact.

### 1. The daemon runs with log rotation

**Writing `daemon.json` is not enough**: the daemon only rereads it on restart,
and rotation applies to containers created **afterwards**, never retroactively.

The check therefore creates a throwaway container and reads its log
configuration: that is the only place where rotation is a fact rather than an
intention. And the application must be running: restarting the daemon stops
containers with no restart policy and does not bring them back.

### 2. The space is given back, and the useful volume is intact

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

### 3. The docker group holds only those who should be in it

Three facts, and the third is the one people forget: the intern goes out, the
operator stays, and **nobody else moved**. A removal applied too broadly also
takes out the account that administers the machine: the work looks done, and the
host becomes unreachable to whoever needs it.

### 4. The tool goes through a read-only proxy

**A socket is not a file.** A `:ro` mount applies to the inode, not to what
travels through it: anything that talks to the socket can create, stop and
delete, hence do on the host everything the daemon can do.

Two facts are measured: the tool no longer mounts the socket, **and** the proxy
refuses a stop request while letting a read through. The second is the real
check: a proxy that let everything through would satisfy the first while
protecting nothing.

### 5. No TCP socket at all, with or without TLS

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

## The marking

Five checks of equal weight, pass mark **75 out of 100**, and **only the final
state counts**.

Four hints, from the vaguest to the most explicit, and **they cost points**:

```bash
dsoxlab hint
```
