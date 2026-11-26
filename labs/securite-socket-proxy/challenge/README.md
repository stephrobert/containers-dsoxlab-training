# Put a filtering proxy in front of the Docker API

A monitoring tool runs on this machine. It needs to read the list of containers
and to stop one when it decides it is unhealthy. The quick way to let it do that
is to mount the Docker socket into it. It was mounted `:ro`, to be careful.

That caution protects nothing, and you are going to see it before fixing it.

## What is asked

On `docker.lab`, two witnesses are already running, and your work directory
`/opt/dsoxlab-securite-socket-proxy` carries the pinned references:

```text
images.env   the proxy, an HTTP client and the witnesses' image, tag AND digest
MISSION.md   the full brief
```

```text
cible-1      set up to be stopped
cible-2      carries CLE_API with -e, a decoy secret
```

The objects you create carry imposed names, because the checks inspect them: the
network **`reseau-filtre`**, the proxy **`filtre-api`**, and the client of the
first finding **`client-ro`**.

The port is **2375**, and you do not choose it: the proxy image fixes it in its
HAProxy configuration, and exposes no variable to change it.

### 1. The read-only socket did not protect the witness

`client-ro` must exist, must mount `/var/run/docker.sock` **read-only**, and
`cible-1` must be **stopped**. Ask for the stop from this client, and leave it in
place: it is what the check inspects.

### 2. The proxy is pinned, hardened, and alone in mounting the socket

Five properties, each refused separately:

```text
the image carries the digest from images.env   a tag alone lets content change
--read-only                                     unmodifiable root filesystem
--tmpfs /run                                    without it, HAProxy will not start
no published port                               no authentication, no TLS here
the proxy alone mounts the socket                otherwise it filters nothing
```

### 3. The reading profile opens what is needed, and nothing more

```text
GET /_ping, /version, /containers/json        200
GET /info, /images/json, /volumes, /networks  403
HEAD /volumes                                 403
```

The `HEAD` is there because a route open for reading also accepts `HEAD`: a
closed family must therefore refuse it too, and this check catches a profile
opened wider than intended.

To query it yourself, write `curl -I` and **never** `curl -X HEAD`: measured,
the second form makes curl wait for a body that never arrives, and blocks until
the timeout.

### 4. The secret of `cible-2` no longer travels through the environment

Query `GET /containers/cible-2/json` **through the proxy**. A reading profile is
enough to return `.Config.Env`, hence everything passed with `-e`, for any
container on the machine.

Recreate `cible-2` under the same name, running, with its secret somewhere other
than `-e`. The check re-reads the inspection through the proxy and refuses if
`CLE_API` still appears in it.

### 5. One precise action, without the combination that opens the host

Through the proxy, stopping a container answers `204` and creating one answers
`403`. The profile opens the reading of containers and the stop action alone.

`POST=1` is refused: it allows writing on every open family, and the containers
one contains `create` and `exec`. Measured on this machine, a creation carrying
`Privileged` and a mount of `/` then answers **201**, which is worth root on the
host.

### 6. The proxy can only be reached from its network

`filtre-api` is on `reseau-filtre`, created with `--internal`: it has no way out to
the Internet, and a container on another network does not reach it. The host's
shell always reaches it: no check asks you to prevent that.

### 7. The three refusals are told apart by who utters them

```text
403 + HTML body "administrative rules"      the PROXY refused
400 + the daemon's JSON message             the request WENT THROUGH
no HTTP code at all, curl exits with 7      the client never opened the socket
```

Each calls for a different move: a `403` is fixed in the proxy's variables, a
`400` in the request, a failure to open in the account that opens it. The `400`
check goes through a versioned path (`/v1.99/containers/json`), because the
profile asked for here does not open writes: the daemon's `400` would not be
reachable otherwise.

## Diagnosing, when something refuses

Three symptoms, three causes, three places to look.

**The proxy answers `403` although you believe the variable is set.** A
container's variables are fixed **at creation**: you do not change them on a
running container. Remove the proxy and recreate it with the right `-e`. The
network and the witnesses stay in place. Check what it actually carries with
`docker inspect -f '{{.Config.Env}}' filtre-api`.

**The daemon answers `400`.** The request **went through**; it is the daemon
rejecting it. Its message is JSON, and it says what is wrong: an API version too
new, an unreadable filter, a missing body. The proxy's `403` body, by contrast,
is HTML. The two codes tell you who refused, hence where to fix.

**Your client does not open the socket.** There is then no HTTP code at all:
`curl` exits with **7** and "Could not connect to server". On this machine the
socket is `root:docker 0660` and the client image runs as an unprivileged
account. A `--user root` makes the same request pass. That detail is a useful
reminder: the proxy itself runs as **root** and mounts the real socket.
