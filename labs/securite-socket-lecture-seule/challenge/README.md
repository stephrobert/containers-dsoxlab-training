# Scenario

An application container, `dsoxlab-socket-readonly`, mounts
`/var/run/docker.sock` read-only. The team that deployed it believes `:ro`
blocks the calls that change something. It does not, and you are going to see
that for yourself before fixing it.

Next to it runs a witness, `dsoxlab-socket-temoin`, which exists only for the
demonstration: nobody grades it, and you may stop it.

## First, observe

The witness is running. Check it:

```bash
docker inspect -f '{{.State.Status}}' dsoxlab-socket-temoin
```

Now send a stop `POST` from a container that mounts the socket **read-only**.
`--user root` is required: the curl image's default user may not open the
socket.

```bash
CURL='curlimages/curl:8.23.0@sha256:3fb7e13e5d179a845c97d78204f3f1064d1907037f26a3ebf91710571151fd93'

docker run --rm --user root \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  "$CURL" --unix-socket /var/run/docker.sock \
  -s -o /dev/null -w '%{http_code}\n' \
  -X POST http://localhost/containers/dsoxlab-socket-temoin/stop

docker inspect -f '{{.State.Status}}' dsoxlab-socket-temoin
```

Code `204` means the daemon **carried out the stop**, and the witness goes from
`running` to `exited`. `:ro` applied to the socket file, not to the requests
travelling through it: the daemon runs as root and decides alone whether to
answer.

This observation is not graded. Nothing distinguishes a stop triggered through
the API from a `docker stop` typed on the host, and a check claiming to require
it would measure your obedience, not your understanding.

## Then, the mission

**The `dsoxlab-socket-readonly` container no longer reaches the daemon socket,
by any path.** It stays running and keeps its `dsoxlab.lab` label.

Two checks measure this, and neither compares file names:

- the first resolves every mount source on the host and rejects the one that
  **is** the socket as well as the one that **contains** it: mounting `/run`
  whole exposes forty-seven sockets, including containerd's and the SSH agent's;
- the second collects, **inside** the container, the (device, inode) pair of
  every visible unix socket and rejects the daemon's. Same inode means the same
  file, whatever name it was given.

Restricting access is therefore not enough, and renaming it even less so. Least
privilege calls for **removing the capability**, not for trusting the restraint
of the tool that holds it.

## Functional contract: securite-socket-lecture-seule

Both checks inspect the effective state on the `docker.lab` host. They reject
the initial state and pass only once the capability has been removed. Each
measures one thing, and neither compares file names.

### 1. No mount grants access to the daemon socket

The **daemon's** view: for every mount of the container, the source is resolved
on the host with `readlink -f`, then compared to the resolved socket.

Two ways of reaching the socket are rejected, and the second is the broader
one: **being** that file, or being a **directory that contains it**. Mounting
`/run` whole hands `/run/docker.sock` to the inside without any written path
looking like a socket.

Resolution matters. On the lab VM, `/var/run` is a link to `/run`:
`src=/run/docker.sock` and `src=/var/run/docker.sock` name the same file under
two spellings, and a check comparing strings would let one through.

### 2. The daemon socket is unreachable from inside the container

The **container's** view: every unix socket visible inside is collected with
its (device, inode) pair, and none may be the daemon's.

This is the check a name cannot work around. A path is what you typed; the
inode is what the kernel designates. A renamed destination, a parent directory
mounted whole, or a path no list would have anticipated all yield the same pair
as the host socket, because it is the same file.

This check needs a **running** container: a stopped one cannot be inspected
from the inside. That is why the mission asks you to leave it running.

### What is not graded, and why we tell you

The scenario's first step, observing that a stop `POST` travels through a socket
mounted `:ro`, is **not measured**. This is not an oversight: a stop triggered
through the API leaves no trace distinguishing it from a `docker stop` typed on
the host. A check claiming to require it would measure your obedience, not your
understanding.

Three preliminary verifications are not extra requirements: the container
exists, carries its label, and runs. Without them neither check can look at
anything, and a check that could not look must never conclude green. If
resolving the socket or reading its inode fails on the host, the message tells
you it is not your fault.
