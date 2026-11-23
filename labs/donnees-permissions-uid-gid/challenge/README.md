# "Just run it as root, it will work"

## The situation

A service produces reports into a volume. On the day it went live, it could not
write: the volume belonged to root and the container was running under an
ordinary account. The console printed `Permission denied`, the release was
waiting, and someone said the sentence you always hear: "just run it as root, it
will work".

It worked. The service writes, and every report it produces belongs to root.

Six months later, a second container is added, a reviewer that has to take over
those reports. That one was done properly: it runs under an ordinary account.
And it writes nothing.

The next sentence coming is "put the volume in 777". That would work too.

## The goal

Replace both bad answers with the one that holds. Two containers share the
volume `rapports-partages`, mounted on `/rapports`, and the image carries two
accounts in the **same group**:

```text
redacteur       uid 1000, group equipe (gid 2000)
verificateur    uid 1001, group equipe (gid 2000)
```

The current state is the result of the story above:

```text
rapport        runs as ROOT, because otherwise it could not write
verificateur   runs as non-root, and it writes nothing
```

Four things are expected:

1. `rapport` **no longer runs as root**.
2. A file `rapport` writes into `/rapports` belongs to it, and carries the
   **shared group**.
3. The directory `/rapports` belongs to the shared group and grants it
   **write** access.
4. `verificateur`, whose uid is **different**, also writes into `/rapports`,
   and the directory is **not** open for writing to everyone.

The brief is also written to `/opt/MISSION.md`.

## Why the group, and not the owner

Two containers have to write under **two different uids**. No owner can suit
both: giving the volume to `1000` would let the producer write and not the
reviewer.

A shared group does suit both. That is the real situation as soon as an
application and its backup tool share data, and that is why this lab carries two
containers rather than one.

## Two things to know before starting

**A container's user is fixed at its creation**: it has to be recreated. It is
the same rule as for mounts, published ports and the network.

And **you cannot write into a volume without a container that mounts it**. To
change its rights, start a throwaway one that mounts it, with the privileges
needed.

## What is graded

The **state of the system**, and it is measured by **real writing**, not only by
reading permissions. A permission is declared without always producing the
expected effect, and it is the effect that counts.

The fourth check explicitly refuses a volume open for writing to everyone.
`chmod 777` would make the first three pass: it works, and it gives any process
of the container the right to rewrite everything. The shared group is enough,
and it **names** who may write.

## What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. Two containers
are **already running** and share the volume `rapports-partages`, mounted on
`/rapports`.

The image `lab-permissions:1.0` carries two accounts in the **same group**:

```text
redacteur       uid 1000, group equipe (gid 2000)
verificateur    uid 1001, group equipe (gid 2000)
```

Current state, which is the result of two bad answers:

```text
rapport        runs as ROOT, because otherwise it could not write
verificateur   runs as non-root, and it writes nothing
```

### 1. `rapport` no longer runs as root

Its uid must be non-zero, and its gid must be the shared group's.

Identity is read **inside** the container, not from what was asked at creation:
it is identity that decides the rights.

### 2. What `rapport` writes belongs to it

A file it writes into `/rapports` must belong to it **and** carry the shared
group.

The two do not separate: being able to write without the file carrying the right
group would give a volume where each produces files the others cannot take over.
That is the next failure, and it is worse because it arrives later.

### 3. The directory belongs to the shared group, with write access

`/rapports` must belong to the shared group and grant it **write** access.

The owner may well stay root: it is not the owner that grants the right to write
here.

### 4. The other uid writes, and the volume is not open to everyone

`verificateur`, whose uid is **different**, must also write into `/rapports`.
And the directory must **not** be open for writing to everyone.

Both halves are inseparable. `chmod 777` would make the three previous checks
pass: it works, and it gives any process of the container the right to rewrite
everything.

Do not touch `verificateur`: it is the shared group's witness. Giving it the
same uid as `rapport` would prove nothing, since the whole point is that two
different uids work side by side.

### Two things to know before starting

**A container's user is fixed at its creation**: it has to be recreated. It is
the same rule as for mounts, published ports and the network.

And **you cannot write into a volume without a container that mounts it**. To
change its rights, start a throwaway one that mounts it, with the privileges
needed.

### A word on order

Set the volume's rights **before** recreating the container under its account.
The other way round gives a container that does not write, and you will wrongly
conclude that the account is the problem.

### What is not graded

The command you typed. A volume's rights can be changed in several ways. But the
state is measured by **real writing**, not only by reading permissions: a
permission is declared without always producing the expected effect.
