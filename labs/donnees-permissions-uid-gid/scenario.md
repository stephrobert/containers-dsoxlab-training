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
