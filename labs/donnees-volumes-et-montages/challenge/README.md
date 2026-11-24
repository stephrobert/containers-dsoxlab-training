# The container was recreated, and the history is gone

## The situation

An archiving service has been running for eight months. It writes its history
to `/var/lib/donnees`, inside the container, and nobody ever questioned it: it
works.

One morning the image has to move to the next version. The procedure is the
familiar one: destroy the container, start a fresh one. Ten seconds, and the
service is back.

Eight months of history went with the container.

It was not a failure. A container has a **layer** of its own, writable, and that
layer is destroyed with it. It is not made for data: it is made for what can be
lost. Three other places exist, and each serves something different.

## What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. The container
`archive` is **already running**, and it writes its data into its own layer.

```text
/var/lib/donnees/historique.log    in its layer. IRREPLACEABLE.
```

The brief is also written to `/opt/MISSION.md`.

### Warning, read it before typing anything

That file's content is **drawn at random** and exists **nowhere else**. If you
destroy the container before taking the file out of it, it is lost, and there is
no recovery: you will have to replay the lab with `dsoxlab reset`.

Its SHA256 fingerprint is in `/opt/lab-volumes/historique.sha256`. You can check
your own copy, and that is what it is for.

**The order of the moves is this lab's lesson.**

### What has to be obtained

Recreate `archive` under the **same** name, with the three mounts.

### 1. The named volume, on `/var/lib/donnees`

The volume `coffre-donnees` already exists. Mount it on `/var/lib/donnees`.

The check verifies two things: that it is indeed that volume, named, and that
the container sees the `marque.txt` file the volume **already** carries. Not
seeing that mark means the mount does not land where it is expected.

An anonymous volume would also survive the container, but nobody would ever find
it again: naming it is the point.

### 2. The host's reference, read-only

The host's directory `/opt/lab-volumes/reference` must appear in the container at
`/etc/reference`, and writing there must be **refused**.

A bind mount copies nothing: it exposes. That is what makes it handy for
providing a configuration, and dangerous for data, since the container then
writes directly on the host.

The check measures the declaration **and** tests the refusal: a declaration is
not a proof.

### 3. The working space, in memory

`/var/cache/travail` must be an **in-memory** space, and the container must be
able to write there.

It is the mount that gets forgotten, and the one that avoids a whole class of
problems: a working space does not have to survive, nor be backed up, nor fill
the disk, nor linger after the container.

### 4. The history, on the volume and intact

`historique.log` must be **on the volume**, with its original content.

The check reads the **volume itself**, through a separate container. Being
visible from `archive` is not enough: as long as the file is only in its layer,
it disappears with it.

And it is graded on its **fingerprint**: a file recreated by hand would have the
right name and not the right content.

### One rule to keep beyond this lab

A mount **cannot be added** to an existing container. It is the same rule as for
published ports and for the network: everything that touches a container's
envelope is decided at its creation.

## What is graded

The **state of the engine**, and each mount is measured **twice**: what the
inspection declares, and what the container can actually do. The two can
diverge, and the clearest case is read-only, which is declared and whose
refusal is tested.

The fourth check reads the **volume itself**, through a separate container.
Being visible from `archive` would not be enough: as long as the file is only in
its layer, it disappears with it, and that is the whole subject.

### What is not graded

The command you typed. The file can come out in several ways and get onto the
volume in several ways. Only the state counts.
