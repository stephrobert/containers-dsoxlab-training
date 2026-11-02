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
5. The daemon no longer listens on **any TCP socket without TLS**.

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
reclaim space, the command that comes to mind is `docker system prune`, and one
of its options takes volumes away.

Mind the backups one: nobody mounts it, because a backup volume is only mounted
when backing up. A `prune` spares what is mounted and takes the rest. **A volume
that is not mounted is not a useless volume.**

Four hints are available, and **they cost points**: `dsoxlab hint`.
