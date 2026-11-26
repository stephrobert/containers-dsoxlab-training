# Run an OCI bundle with runc

The lesson builds a bundle with `runc spec`, reads its `config.json` field by
field, follows the `create`, `start`, `kill`, `delete` lifecycle, then replays
the same bundle with crun and produces one with umoci. This course starts from
the bundle umoci writes and shows you what the lesson does not. First, that
its root is writable. Then why `runc kill` without a signal kills nothing, and
what a pause does. Then what the list of namespaces really changes, how to
write outside a read-only root, and why a non-root user keeps capabilities
here.

You work on Alpine 3.23, in folders named `/srv/essai-*`, with a container
named `essai`. The challenge is about another image, another bundle and
another container: you will do it alone, at the end.

Related page: [Exécuter un bundle OCI avec runc](https://www.stephane-robert.info/docs/conteneurisation/runtime-oci/) (in French).

## Before you start

Start the lab:

```bash
dsoxlab run runtime-lancer-un-bundle
```

You are now connected to `oci.lab`, a Debian 13 with no container engine at
all. The bundle umoci writes belongs to root, with mode `0700`: become root
for the whole course, as in the lesson.

```bash
sudo -i
runc --version
```

```text
runc version 1.1.15+ds1
commit: 1.1.15+ds1-2+deb13u1
spec: 1.2.0
go: go1.24.4
libseccomp: 2.6.0
```

The outputs of this course were taken on this machine on 26 November 2026,
with runc 1.1.15, the version of the Debian package, and umoci 0.4.7. **Keep
the same terminal until the cleanup**: the variables of the exercises only
exist in it.

Copy Alpine 3.23 by its digest, turn it into a bundle, then start a detached
`essai` container, with a command that lasts:

```bash
A=docker://docker.io/library/alpine
A_INDEX=sha256:469c9ea410b9215eaee7976ba6c0639039b444be8e5d638f7abbada189971eb2
B=/srv/essai-bundle
skopeo copy -q --override-arch amd64 "$A@$A_INDEX" oci:/srv/essai-oci:3.23
umoci unpack --image /srv/essai-oci:3.23 "$B"
ls -ld "$B"
cat "$B/rootfs/etc/alpine-release"
cd "$B"
jq '.process.terminal=false | .process.args=["sleep","infinity"] | .hostname="essai"' config.json > c.tmp && mv c.tmp config.json
runc run -d essai
runc list
```

```text
drwx------ 3 root root 4096 Nov 26 06:28 /srv/essai-bundle
3.23.8
ID          PID         STATUS      BUNDLE              CREATED                          OWNER
essai       112361      running     /srv/essai-bundle   2026-11-26T06:28:02.919315282Z   root
veilleur    0           stopped     /srv/ancien         2026-11-26T06:27:58.908270806Z   root
```

`runc run -d` starts the container detached and gives you back the prompt: it
requires `process.terminal` set to `false`. `runc list` also shows
`veilleur`, stopped. It is the starting point of the challenge: leave it alone
during the course.

## Exercise 1: the root umoci writes is writable

The lesson notes that `runc spec` makes the root read-only. Look at what umoci
writes, then try to write at the root of the container:

```bash
jq -c '{root, namespaces: [.linux.namespaces[].type]}' config.json
runc exec essai touch /racine; echo "code $?"
ls -l rootfs/racine
```

```text
{"root":{"path":"rootfs"},"namespaces":["pid","network","ipc","uts","mount"]}
code 0
-rw-r--r-- 1 root root 0 Nov 26 06:28 rootfs/racine
```

No `readonly`: the root is writable, and the file written in the container
shows up on the host, in `rootfs`. Note the namespaces too: five, without
`cgroup`, where `runc spec` declares six. Two tools, two different default
`config.json`. Always read the one you run.

A running container keeps its configuration. To switch to read-only, delete
it, change the file, then start it again:

```bash
runc delete -f essai
rm rootfs/racine
jq '.root.readonly=true' config.json > c.tmp && mv c.tmp config.json
runc run -d essai
runc exec essai touch /racine; echo "code $?"
```

```text
touch: /racine: Read-only file system
code 1
```

## Exercise 2: PID 1 ignores TERM

The lesson stops the container with `runc kill demo KILL`. Try first the
default signal of a clean stop, `TERM`:

```bash
runc kill essai TERM; sleep 2; runc state essai | jq -r .status
runc exec essai grep -E '^Sig(Cgt|Ign)' /proc/1/status
```

```text
running
SigIgn:	0000000000000000
SigCgt:	0000000000000000
```

The container is still running. In its `pid` namespace, `sleep` is PID 1, and
the kernel protects PID 1: a signal it does not catch itself is ignored.
`SigCgt` (the caught signals) is zero: `sleep` catches none. Only `KILL`,
which nobody can catch, stops it:

```bash
runc kill essai KILL; sleep 1; runc state essai | jq -r .status
runc delete essai
```

```text
stopped
```

That is why an engine waits a few seconds after `TERM`, then sends `KILL`. An
application that runs as PID 1 must handle `TERM` itself to stop cleanly.

## Exercise 3: a pause freezes the cgroup

runc can also suspend a container without stopping it. Start it again, find
its cgroup, then pause it:

```bash
runc run -d essai
P=$(runc state essai | jq -r .pid)
cat /proc/$P/cgroup
CG=/sys/fs/cgroup$(cut -d: -f3 /proc/$P/cgroup)
runc pause essai; runc state essai | jq -r .status
cat "$CG/cgroup.freeze"
runc exec essai true; echo "code $?"
```

```text
0::/user.slice/user-1001.slice/essai
paused
1
time="2026-11-26T06:28:06Z" level=error msg="exec failed: cannot exec in a paused container (use --ignore-paused to override)"
code 255
```

Without `cgroupsPath` in `config.json`, runc puts the container under the
cgroup of whoever starts it: here your session, `user-1001.slice`. The pause
writes `1` into `cgroup.freeze`: the kernel no longer gives processor time to
any process of the group. A `runc exec` is refused, since the new process
would be frozen too. Resuming writes `0` back:

```bash
runc resume essai; cat "$CG/cgroup.freeze"
```

```text
0
```

## Exercise 4: one namespace less, and the container sees the host network

runc does nothing for the network: it creates an empty `network` namespace.
Look at the interfaces of the container, then remove that namespace from the
list and start again:

```bash
runc exec essai ip -o link | cut -d: -f2
runc delete -f essai
jq 'del(.linux.namespaces[] | select(.type=="network"))' config.json > c.tmp && mv c.tmp config.json
runc run -d essai
runc exec essai ip -o link | cut -d: -f2
```

```text
 lo
 lo
 enp1s0
```

With the namespace, the container only has `lo`, and nobody plugs a cable
into it: that is the job of an engine. Without it, it sees `enp1s0`, the
network card of the host. Each line of `linux.namespaces` is an isolation:
removing it means sharing that resource with the host. Put it back before
going on:

```bash
runc delete -f essai
jq '.linux.namespaces += [{"type":"network"}]' config.json > c.tmp && mv c.tmp config.json
```

## Exercise 5: write outside a read-only root

The root is read-only, but an application often needs to write somewhere.
Mount a folder of the host into the container, by adding an entry to
`mounts`:

```bash
mkdir -p /srv/essai-donnees
jq '.mounts += [{"destination":"/donnees","type":"bind","source":"/srv/essai-donnees","options":["rbind","rw"]}]' config.json > c.tmp && mv c.tmp config.json
runc run -d essai
runc exec essai sh -c 'date +%F > /donnees/trace && echo écrit'
cat /srv/essai-donnees/trace
runc delete -f essai
```

```text
écrit
2026-11-26
```

The container writes into `/donnees`, and the file can be read on the host in
`/srv/essai-donnees`. The root stays read-only: only that folder is open. That
is the principle of an engine's volumes.

## Exercise 6: a non-root user, and capabilities all the same

Run the container as uid 1000, then read its capability masks:

```bash
jq '.process.user={"uid":1000,"gid":1000}' config.json > c.tmp && mv c.tmp config.json
runc run -d essai
runc exec essai sh -c 'id; grep -E "^Cap(Eff|Bnd)" /proc/1/status'
jq -c '.process.capabilities.ambient' config.json
runc delete -f essai
```

```text
uid=1000 gid=1000
CapEff:	0000000020000420
CapBnd:	0000000020000420
["CAP_AUDIT_WRITE","CAP_KILL","CAP_NET_BIND_SERVICE"]
```

The process is no longer root, but its effective capabilities still read
`0000000020000420`, the three of the lesson. The reason is in the file: umoci
also puts them in the `ambient` list, which a non-root process keeps. `id`
shows no name: uid 1000 does not exist in the `/etc/passwd` of Alpine. Empty
the capabilities, and start again:

```bash
jq '.process.capabilities={}' config.json > c.tmp && mv c.tmp config.json
runc run -d essai
runc exec essai grep -E '^Cap(Eff|Bnd)' /proc/1/status
runc delete -f essai
```

```text
CapEff:	0000000000000000
CapBnd:	0000000000000000
```

Changing the user is not enough to remove the rights: you must also look at
the capabilities the file grants.

## Cleanup

Remove everything this course created, check that nothing is left, then leave
the root shell:

```bash
cd /
rm -rf /srv/essai-oci /srv/essai-bundle /srv/essai-donnees
ls -d /srv/essai-* 2>/dev/null || echo "aucun fichier d'essai"
runc list
exit
```

```text
aucun fichier d'essai
ID          PID         STATUS      BUNDLE        CREATED                          OWNER
veilleur    0           stopped     /srv/ancien   2026-11-26T06:27:58.908270806Z   root
```

Only `veilleur` is left, placed by the lab. Then leave the machine and reset
the lab. `dsoxlab reset` replays the cleanup then the preparation of the lab:
you get back exactly the starting state of the challenge. It asks you to
confirm: answer `y`.

```bash
exit
dsoxlab reset runtime-lancer-un-bundle
dsoxlab check runtime-lancer-un-bundle
```

```text
╭─ Result: runtime-lancer-un-bundle ─╮
│  0 / 100 pts                       │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests   │
╰────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is waiting for you,
intact.

## The challenge

Your turn, alone this time: free the `veilleur` identifier, turn busybox into
a bundle, set its command, host name and read-only root, and keep it running
detached.

```bash
dsoxlab run runtime-lancer-un-bundle
dsoxlab challenge runtime-lancer-un-bundle
```
