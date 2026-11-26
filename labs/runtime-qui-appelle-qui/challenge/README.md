# Who watches over what

## The situation

On `oci.lab`, a Debian 13 with no Docker, the team runs its containers with
two engines: Podman and containerd. For each one, it wants to know which
program starts them and which process watches over them. A colleague also
claims that a `gardien` container runs under containerd, but `ctr task ls`
shows nothing.

Podman, conmon, crun, runc and containerd are installed. You are `root`
through `sudo`. The image to use is busybox 1.37.0:

```text
docker.io/library/busybox:1.37.0@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec
```

## What you must obtain

1. A Podman container **`vigie`** runs busybox, detached, and Podman handed it
   to the **runc** runtime, not to crun.
2. A containerd task **`releve`** runs busybox, in the containerd namespace
   **`equipe`**.
3. The file **`/srv/reponses/shim-gardien`** contains the PID of the shim that
   watches over `gardien`. `gardien` must keep running.
4. The file **`/srv/reponses/conmon-vigie`** contains the PID of the conmon
   that watches over `vigie`.

A PID is written alone on its line.

## Useful landmarks

The parent of the process of a container is its monitor: conmon with Podman,
a shim with containerd. The command line of that monitor names the runtime.

`ctr` reads the `default` namespace as long as it is not given another one,
and an image pulled in one namespace does not exist in the others.

## How you will know it works

The tests read `podman inspect vigie`, the tasks of the containerd
namespaces, and compare your two answers with the real parent of each
process, read in `/proc`.

```bash
dsoxlab check runtime-qui-appelle-qui
```
