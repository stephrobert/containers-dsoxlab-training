# Put a filtering proxy in front of the Docker API

A monitoring tool runs on this machine. It needs to read the list of containers
and to stop one when it decides it is unhealthy. The quick way to let it do that
is to mount the Docker socket into it. It was mounted `:ro`, to be careful.

That caution protects nothing, and you are going to see it before fixing it.

## What the machine already carries

Two witnesses are running, set up for you:

- **`cible-1`** exists to be stopped. It is the one that will show that
  read-only does not prevent a write on the API.
- **`cible-2`** carries a `CLE_API` variable, passed with `-e`, standing in for
  a secret. Its value is a decoy.

The `images.env` file in your work directory carries the three pinned
references to reuse as they are: the proxy, an HTTP client, and the witnesses'
image. Each carries its tag **and** its digest.

## The first finding: `:ro` does not filter requests

`:ro` makes the socket **file** unmodifiable. It does not look at what travels
inside it. The socket is a channel to the daemon, the daemon runs as root, and
stopping a container is a `POST` request like any other.

Mount a client that only receives the socket read-only, and ask it to stop
`cible-1`. Name that client **`client-ro`** and **leave it in place**: it is the
setup that proves the point, and it is what the check inspects. The code you
will read is `204`, and `cible-1` will go from `running` to `exited`.

If your client cannot open the socket at all, read the diagnosis section below
before looking elsewhere.

## The work: give the tool exactly what it needs

A socket proxy is a small HTTP server placed between the tool and the socket. It
compares every method and path pair to an allowlist, forwards what is allowed,
and refuses the rest itself, without the daemon ever hearing about it. Almost
every path family is closed by default; an environment variable set to `1` opens
its family.

Deploy it this way:

- a network named **`reseau-filtre`**, created with `--internal`;
- a container named **`filtre-api`**, on that network, running the pinned image
  from `images.env`;
- it is the **only** one to mount the Docker socket;
- it is hardened: `--read-only`, plus a `--tmpfs /run` without which HAProxy
  cannot write its configuration;
- **no port is published.** This proxy has neither authentication nor TLS:
  whatever reaches its port reaches its rules. Clients reach it by name, from
  its network.

The profile variables come down to two: the tool must **read** containers and
**stop** one of them, nothing more.

## The six things that are graded

1. **The setup of the first finding.** `client-ro` exists, it mounts the socket
   read-only, and `cible-1` is stopped.
2. **The proxy deployment.** Image pinned by digest, `--read-only`,
   `--tmpfs /run`, no published port, and the proxy alone mounting the socket.
3. **The profile is narrow.** `/_ping`, `/version` and `/containers/json` answer
   `200`. `/info`, `/images/json`, `/volumes` and `/networks` answer `403`:
   nobody asks you to open those families, and one variable opens a whole one
   at a time.
4. **The secret no longer travels through the environment.** Query the
   inspection of `cible-2` **through the proxy** and look at what it returns. A
   mere reading profile is enough to read `.Config.Env` of any container on the
   machine, from any container on the network. Recreate `cible-2`, under the
   same name, with its secret somewhere other than `-e`.
5. **One precise action, and not the combination that opens the host.** The stop
   must pass with `204` and creating a container must stay at `403`.
6. **The three refusals are distinguishable.** The proxy's `403` carries
   "Request forbidden by administrative rules". A versioned path the daemon
   cannot serve, such as `/v1.99/containers/json`, goes through the proxy and is
   rejected by the **daemon**, with `400` and a JSON message. And a client that
   cannot open the socket has no HTTP code at all.

## The combination not to make, and why

`POST=1` allows write methods for every open family. Added to the containers
family, which contains `create` and `exec`, it cancels the filtering for
everything that matters. Measured on this machine: a creation request carrying
`Privileged` and a mount of `/` onto `/hote` answers **201**, and inspecting the
created container shows `privileged=true binds=[/:/hote]`. That combination is
**root on the host**, even with the images, volumes and networks families
closed.

The `ALLOW_` variables exist for this: they open **one action** instead of a
family. `ALLOW_STOP=1` allows only the stop, and does not need `POST=1` with
this image.

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

## What the proxy does not do

It reduces what a client on its network can ask for. It does not protect the
host against someone who already controls it: **the host's shell reaches the
proxy in every case**, and its rules are then the only barrier. It offers
neither authentication nor TLS. And it runs as root while mounting the real
socket: whoever compromises it gets everything the socket allows.

Keep one proxy per tool, one network per proxy, and no published port.
