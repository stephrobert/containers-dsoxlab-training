# Read who calls whom

The lesson runs the same `sleep` with Podman, containerd and Docker, and reads
the process tree: one monitor per container, conmon with Podman, a shim with
containerd, and the runtime at the end. It restarts containerd to show that
the container survives. This course shows you what it does not. First, what
conmon is for once the container has ended, and why a process carries two
numbers. Then the difference between a containerd container and a task, and
images that do not cross from one namespace to another. Finally, what happens
when the shim disappears.

You work on Alpine 3.23, with containers named `essai-*` and the containerd
namespaces `essai` and `essai2`. The challenge is about another image and
other names: you will do it alone, at the end.

Related page: [Runtime, moteur, orchestrateur : qui fait quoi ?](https://www.stephane-robert.info/docs/conteneurisation/runtime-moteur-orchestrateur/) (in French).

## Before you start

Start the lab:

```bash
dsoxlab run runtime-qui-appelle-qui
```

You are now connected to `oci.lab`, a Debian 13 with no Docker. Podman and
containerd are used as root: become root for the whole course, as in the
lesson. Then pull the image of the course with Podman, by its digest:

```bash
sudo -i
podman --version
ctr --version
A=docker.io/library/alpine@sha256:469c9ea410b9215eaee7976ba6c0639039b444be8e5d638f7abbada189971eb2
podman pull -q "$A"
```

```text
podman version 5.4.2
ctr github.com/containerd/containerd 1.7.24~ds1
164b5c6a230f645862b6123e07cf0a67f2f03371696aa82a12ccf3589e87c016
```

The outputs of this course were taken on this machine on 26 November 2026,
with Podman 5.4.2 and containerd 1.7.24, the versions of the Debian 13
packages. PIDs and identifiers change from one run to the next. **Keep the
same terminal until the cleanup**: the variables of the exercises only exist
in it.

## Exercise 1: conmon keeps the exit code

The lesson shows that Podman leaves no daemon behind: conmon is what stays
next to the container. Start a container that ends after three seconds with
code 3, count the conmon processes following it, then wait for its end:

```bash
podman run -d --name essai-code "$A" sh -c 'sleep 3; exit 3'
pgrep -a conmon | grep -c essai-code
sleep 5
podman inspect -f '{{.State.Status}} {{.State.ExitCode}}' essai-code
pgrep -a conmon | grep -c essai-code
podman rm essai-code
```

```text
e57382f918cf1eaee46da697a36824ae7b60ae02129ba5e5279175683f53aa60
1
exited 3
0
essai-code
```

While the container runs, a conmon follows it. Once the container is over,
conmon is gone too, and yet Podman knows the exit code: `3`. No `podman`
command was running at that moment. conmon waited for the end of the process
and wrote down its code before leaving. Without it, nobody would have
collected it.

## Exercise 2: one process, two numbers

Start a lasting container, then read its process number as seen from the
host and from the container:

```bash
podman run -d --name essai-pid "$A" sleep infinity
P=$(podman inspect -f '{{.State.Pid}}' essai-pid)
grep NSpid /proc/$P/status
podman exec essai-pid ps -o pid,comm
podman rm -f -t 0 essai-pid
```

```text
3c5379d4e3d106f10594006f82e50fdc9ddb526c3b0b804c7d5d1a0e6add1547
NSpid:	122599	1
PID   COMMAND
    1 sleep
    2 ps
essai-pid
```

The `NSpid` line gives both numbers of the same process: `122599` in the
`pid` namespace of the host, `1` in that of the container. When you look for
the parent of a container, as in the lesson, it is the host number you must
read: the one given by `podman inspect` and `ctr task ls`.

## Exercise 3: a container is not a task

In containerd, a **container** and a **task** are two separate objects.
`ctr run` creates both at once. Split the steps, in a namespace of your own:

```bash
ctr -n essai image pull "$A" > /dev/null
ctr -n essai container create "$A" essai-c sleep infinity
ctr -n essai container ls -q
ctr -n essai task ls
ctr -n essai task start -d essai-c
ctr -n essai task ls
```

```text
essai-c
TASK    PID    STATUS
TASK       PID       STATUS
essai-c    122722    RUNNING
```

After `container create`, the container exists, but there is no task: it is a
description (image, command, options), with no process at all. `task start`
creates the process. That is why the lesson cleans up in three steps: kill
the task, remove it, then remove the container.

The task also has its state on the runc side, in a root of its own namespace:

```bash
runc --root /run/containerd/runc/essai list
```

```text
ID          PID         STATUS      BUNDLE                                                        CREATED                          OWNER
essai-c     122722      running     /run/containerd/io.containerd.runtime.v2.task/essai/essai-c   2026-11-26T06:39:40.918987625Z   root
```

The lesson read `/run/containerd/runc/default`. The last folder is the name of
the namespace: each namespace has its own state root.

## Exercise 4: an image does not cross from one namespace to another

The lesson shows that two engines do not share their images. It is true
between two namespaces of the same containerd as well:

```bash
ctr -n essai image ls -q
ctr image ls -q
ctr -n essai2 run -d "$A" essai-d sleep infinity
ctr namespaces ls
```

```text
docker.io/library/alpine@sha256:469c9ea410b9215eaee7976ba6c0639039b444be8e5d638f7abbada189971eb2
ctr: image "docker.io/library/alpine@sha256:469c9ea410b9215eaee7976ba6c0639039b444be8e5d638f7abbada189971eb2": not found
NAME  LABELS
essai
nuit
```

The image exists in `essai`, not in `default` (the second `ls` is empty), and
`ctr -n essai2 run` does not find it. The `essai2` namespace was not even
created: the start failed before. `ctr namespaces ls` lists every namespace:
it is the command to run when `ctr task ls` shows nothing. `nuit` belongs to
the lab: leave it as it is.

## Exercise 5: without its shim, the task disappears

The lesson restarts containerd and sees the task survive, because the shim is
its parent. Try it, then kill the shim itself:

```bash
T=$(ctr -n essai task ls | awk '/essai-c/ {print $2}')
S=$(awk '{print $4}' /proc/$T/stat)
ps -o pid,comm -p $S
systemctl restart containerd
ctr -n essai task ls
kill -KILL $S
sleep 2
ctr -n essai task ls
ps -o pid,comm -p $T || echo "plus de processus $T"
ctr -n essai container ls -q
```

```text
    PID COMMAND
 122700 containerd-shim
TASK       PID       STATUS
essai-c    122722    RUNNING
TASK    PID    STATUS
    PID COMMAND
plus de processus 122722
essai-c
```

The fourth field of `/proc/<PID>/stat` is the number of the parent: here the
shim. Restarting containerd does not touch the task. Once the shim is killed,
the task disappears, and its process too: the shim held the container. The
container itself stays listed: it is the description of exercise 3, which
did not need the shim to exist.

## Cleanup

Remove the container, the image of the `essai` namespace, the namespace
itself, then the Podman image. Then leave the root shell:

```bash
ctr -n essai container rm essai-c
ctr -n essai image rm --sync "$A"
ctr namespaces rm essai
podman rmi "$A"
ctr namespaces ls
podman ps -a
exit
```

```text
docker.io/library/alpine@sha256:469c9ea410b9215eaee7976ba6c0639039b444be8e5d638f7abbada189971eb2
essai
Untagged: docker.io/library/alpine@sha256:469c9ea410b9215eaee7976ba6c0639039b444be8e5d638f7abbada189971eb2
Deleted: 164b5c6a230f645862b6123e07cf0a67f2f03371696aa82a12ccf3589e87c016
NAME LABELS
nuit
CONTAINER ID  IMAGE       COMMAND     CREATED     STATUS      PORTS       NAMES
```

A containerd namespace can only be removed once empty: the `--sync` option
waits until the image data is really deleted before giving back the prompt.
Only `nuit` is left, placed by the lab.

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the preparation of the lab: you get back exactly the starting state of
the challenge. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset runtime-qui-appelle-qui
dsoxlab check runtime-qui-appelle-qui
```

```text
╭─ Result: runtime-qui-appelle-qui ─╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is waiting for you,
intact.

## The challenge

Your turn, alone this time: make Podman hand a container to runc, run a
containerd task in a named namespace, find a task that `ctr task ls` does not
show, and write down the real monitor of each container.

```bash
dsoxlab run runtime-qui-appelle-qui
dsoxlab challenge runtime-qui-appelle-qui
```
