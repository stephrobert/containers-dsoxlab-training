# What is asked

On `docker.lab`, a disposable Debian 13 with the engine running. Two witnesses
are already running, and your work directory
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

## 1. The read-only socket did not protect the witness

`client-ro` must exist, must mount `/var/run/docker.sock` **read-only**, and
`cible-1` must be **stopped**.

This check does not try to know which command the stop came from, and it cannot:
the CLI calls the same API as your `curl`, and the daemon sees no difference. It
measures the setup, which is what carries the lesson.

## 2. The proxy is pinned, hardened, and alone in mounting the socket

Five properties, each refused separately:

```text
the image carries the digest from images.env   a tag alone lets content change
--read-only                                     unmodifiable root filesystem
--tmpfs /run                                    without it, HAProxy will not start
no published port                               no authentication, no TLS here
the proxy alone mounts the socket                otherwise it filters nothing
```

## 3. The reading profile opens what is needed, and nothing more

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

## 4. The secret of `cible-2` no longer travels through the environment

Query `GET /containers/cible-2/json` **through the proxy**. A reading profile is
enough to return `.Config.Env`, hence everything passed with `-e`, for any
container on the machine.

Recreate `cible-2` under the same name, running, with its secret somewhere other
than `-e`. The check re-reads the inspection through the proxy and refuses if
`CLE_API` still appears in it.

## 5. One precise action, without the combination that opens the host

```text
CONTAINERS=1      the tool reads containers
ALLOW_STOP=1      it may stop one, and nothing else
POST=1            REFUSED, in combination with CONTAINERS
POST .../stop     204
POST /containers/create  403
```

`POST=1` added to the containers family, which contains `create` and `exec`,
cancels the filtering for everything that matters. Measured on this machine: a
creation carrying `Privileged` and a mount of `/` answers **201**, and the
created container shows `privileged=true binds=[/:/hote]`.

## 6. The three refusals are told apart by who utters them

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

## A surprise, and what the lab does not make of it

**The host's shell reaches the proxy in every case.** `--internal` cuts the
route to the Internet, and separating networks prevents a container on another
network from reaching it, but nothing isolates the proxy from the machine
running it. This is not a defect to fix, it is a limit to know: no check
requires it, and check 5 measures only what `--internal` actually guarantees.
