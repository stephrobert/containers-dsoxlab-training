# A container that does not overflow

## 🧭 The situation

On `oci.lab`, a Debian 13 without any container engine, the container built by
hand in the previous lab showed its limits: it sees little, but it can consume
the whole machine, and its root keeps all its powers. The team asks you to
contain it with the kernel's own tools.

The Alpine 3.24.2 file system is ready in `/srv/quai`, with `/dev/null` and
`/dev/zero`. You are `root` through `sudo`.

## 🎯 What you must get

1. A cgroup **`/sys/fs/cgroup/quai`** caps memory at **48M**, without swap
   (`memory.swap.max` set to `0`).
2. The same cgroup caps the number of tasks at **32** and the CPU at **30 %**
   of one core, over a period of 100 ms.
3. A container runs with `/srv/quai` as its root, in its own `pid` namespace,
   and **all its processes** are in the `quai` cgroup.
4. The root of this container has lost **`CAP_SYS_ADMIN`**: it can no longer
   change the host name.
5. The memory cap has **already killed** at least one process of the `quai`
   cgroup.

The container must **keep running after you log out**: the tests look for it
once your session is closed.

## 🔎 Useful landmarks

A cgroup is created with `mkdir` under `/sys/fs/cgroup`, and each cap is
written into a setting file. A process joins the group by writing its number
into `cgroup.procs`, and what it starts afterwards inherits it.

The lesson puts the container in its cgroup from birth, and removes
capabilities with `setpriv`, between `unshare` and `chroot`. Here, the
container must also run detached: `setsid -f` starts it without a terminal and
gives you the prompt back.

For the last point, run in the `quai` cgroup a program that grows in memory.
The `oom_kill` counter of `memory.events` keeps track of what the kernel
killed.

## ✅ How you will know it works

The tests read the setting files of the `quai` cgroup and its `oom_kill`
counter. They look for the processes whose root is `/srv/quai`, and read their
cgroup, their `pid` namespace and their capability masks in `/proc`.

```bash
dsoxlab check conteneur-limiter-a-la-main
```
