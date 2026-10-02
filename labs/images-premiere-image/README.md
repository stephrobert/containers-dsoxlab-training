# What an image contains, and what it forgets

An image is not an archive of your project. It is a complete filesystem,
stacked in layers, plus a little metadata saying how to start it. This lab has
you build the first one, and it dwells on what people usually discover in
production: what they left out of it.

Every output on this page was captured from a real run. The examples are
deliberately unrelated to the challenge: they demonstrate, they are not
templates.

## A base image is a system, not a language

The reflex is to reach for an image "that has Python". Let us first see what a
bare system image gives:

```console
$ docker run --rm debian:12 python3 --version
docker: Error response from daemon: failed to create task for container: failed
to create shim task: OCI runtime create failed: runc create failed: unable to
start container process: error during container init: exec: "python3":
executable file not found in $PATH
```

The message is long, and only its end matters:
`executable file not found in $PATH`. Debian 12 is a distribution, not a
runtime. It carries a package manager, a shell, system libraries, and that is
all.

You can install Python by hand inside a container:

```console
$ docker run --rm debian:12 bash -c 'apt-get -qq update && apt-get -qq install -y cowsay && ls /usr/games'
cowsay
cowthink
```

Two findings. The install works, so the base image knows how to install
packages. And the container is gone with `--rm`, `cowsay` with it: **what you
install in a running container does not survive**. That is why a Dockerfile
exists.

## Every instruction that touches files adds a layer

Take a throwaway Dockerfile that prints a timestamp:

```dockerfile
FROM debian:12
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/demo
COPY horodatage.txt /opt/demo/
CMD ["cat", "/opt/demo/horodatage.txt"]
```

How many layers? Worth asking rather than guessing:

```console
$ docker image inspect debian:12 --format '{{len .RootFS.Layers}}'
1
$ docker image inspect demo --format '{{len .RootFS.Layers}}'
4
```

One for the base image, and three added. The history says which, and at what
weight:

```console
$ docker image history demo --format '{{.Size}}  {{.CreatedBy}}'
0B        CMD ["cat" "/opt/demo/horodatage.txt"]
16.4kB    COPY horodatage.txt /opt/demo/ # buildkit
12.3kB    WORKDIR /opt/demo
12.2MB    RUN /bin/sh -c apt-get update && apt-get ins…
133MB     # debian.sh --arch 'amd64' out/ 'bookworm' …
```

**`WORKDIR` creates a layer**, which is counter-intuitive: it creates the
directory, so it modifies the filesystem. `CMD` weighs `0 B`: it touches
nothing, it fills in the image configuration.

Weight is the other lesson in that output. The base image is 133 MB, the `RUN`
adds 12.2, and the last two instructions a few kilobytes. It is nearly always
so: what costs is the base and the packages, not your code.

The `rm -rf /var/lib/apt/lists/*` on the same line as the install is not
fussiness. On a separate line it would delete those files in a new layer, and
the previous one would still hold them: the image would carry both. The
optimisation labs of this series measure exactly that.

## `EXPOSE` publishes nothing

This is the most common confusion. `EXPOSE` **documents** the port the image
serves; it is `-p`, at run time, that publishes it:

```console
$ docker run -d --name demo-expose -p 127.0.0.1:9999:80 nginx:alpine
$ docker inspect demo-expose --format '{{.Config.ExposedPorts}}'
map[80/tcp:{}]
```

An image without `EXPOSE` publishes just fine; an image with `EXPOSE` and
without `-p` is reachable from nowhere. What `EXPOSE` brings is that the
reader, Compose and the tooling know which port to ask for without reading your
code.

## An application that only listens to itself

Inside a container, the loopback is the container's. A server bound to
`127.0.0.1` is reachable from the inside, and by nobody else:

```console
$ docker run -d --name demo-boucle -p 127.0.0.1:9998:8000 python:3.12-slim \
    python -m http.server 8000 --bind 127.0.0.1

$ curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:9998/
000

$ docker exec demo-boucle python -c \
    "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/').status)"
200
```

The container answers itself, the host gets nothing, and `-p` was there. The
fix is in the application, not in the run command: it must listen on `0.0.0.0`,
that is, on all its interfaces.

## Debian 12 protects its Python

One last surprise, specific to recent distributions:

```console
$ docker run --rm debian:12 bash -c 'apt-get -qq update && apt-get -qq install -y python3-pip && pip3 install rich'
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try apt install
    python3-xyz, where xyz is the package you are trying to
    install.

    If you wish to install a non-Debian-packaged Python package,
    [...]
```

This is PEP 668. The distribution's package manager and `pip` would fight over
the same files, so Debian closes the door. Two answers exist: a virtual
environment, or telling `pip` that you accept the risk. In a container
dedicated to a **single** application there is no other environment to protect,
and the second is legitimate. The companion lesson covers both, and a later lab
in this series uses the first.

## What the verification looks at

The seven checks read the image you will have built and what the application
answers. The last one runs it with **no network at all** and requires it to
answer anyway.

That is the only way to tell an image that carries its application from an
image that downloads at startup, and the two look alike as long as the Internet
answers. It is precisely the failure the scenario describes.

## Over to you

```bash
dsoxlab run   images-premiere-image
dsoxlab check images-premiere-image
dsoxlab hint  images-premiere-image
```

Reference: [writing a Dockerfile](https://blog.stephane-robert.info/docs/conteneurs/images-conteneurs/ecrire-dockerfile/)
