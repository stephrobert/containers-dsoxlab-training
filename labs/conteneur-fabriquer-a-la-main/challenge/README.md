# A container without an engine

## 🧭 The situation

On `oci.lab`, a throwaway Debian 13 machine, no container engine is
installed: neither Docker nor Podman. The team wants to see what a container
is once the engine is removed, and asks you to build one with the kernel's
own tools only.

The `/srv/depot` repository holds two copies of the Alpine 3.24.2 root
filesystem archive, in `miroir-a/` and `miroir-b/`. One of them has been
altered. `/srv/depot/SHA256SUMS` holds the sum published by Alpine. You are
`root` through `sudo`.

## 🎯 What you must achieve

1. `/srv/atelier` holds the Alpine 3.24.2 root filesystem, extracted from the
   archive **whose SHA-256 sum matches** Alpine's.
2. A process runs with `/srv/atelier` as its root, in its **own** `pid`,
   `uts`, `mnt`, `net` and `ipc` **namespaces**.
3. Inside this container, the host name is **`atelier-isole`**, and the host
   keeps its own.
4. This process is **PID 1** of its container.
5. `/srv/atelier/dev/null` is a real **character device** (1, 3).

The container must **keep running after you log out**: the tests look for it
once your session is closed.

## 🔎 Useful pointers

`sha256sum -c` compares an archive with an expected sum. Run from a mirror's
directory with `../SHA256SUMS`, it tells whether the copy is the right one.
Never extract an archive that fails.

The lesson shows the `unshare` command that creates the five namespaces and
changes the root. A new `pid` namespace only applies to children: an option
is needed for your program to become PID 1.

For a process to survive the end of your session, start it detached, for
example with `setsid -f`, and have it run a command that lasts
(`sleep infinity`).

The rootfs `/dev` is empty. `mknod` creates a device: `c` for a character
device, then its two numbers.

## ✅ How you will know it works

The tests query the kernel of `oci.lab`: they look for a process whose root
is `/srv/atelier`, compare its namespaces with the host's, read its host name
with `nsenter` and its number in its namespace, and check the fingerprint of
the extracted `busybox` and the nature of `/dev/null`.

```bash
dsoxlab check conteneur-fabriquer-a-la-main
```
