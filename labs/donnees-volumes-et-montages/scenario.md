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

## The goal

Put the data where it survives, before it is too late. The container `archive`
is running, and it carries the same flaw:

```text
/var/lib/donnees/historique.log    in its layer. IRREPLACEABLE.
```

## Warning, read it before typing anything

That file's content is **drawn at random** and exists **nowhere else**. If you
destroy the container before taking the file out of it, it is lost, and there is
no recovery: you will have to replay the lab with `dsoxlab reset`.

Its SHA256 fingerprint is in `/opt/lab-volumes/historique.sha256`, so that you
can check your own copy.

That is exactly the incident the scenario tells, and living it once beats
reading it.

## What is expected

Recreate `archive` under the **same** name, with the three mounts:

```text
/var/lib/donnees      the named volume `coffre-donnees`
/etc/reference        the HOST's directory /opt/lab-volumes/reference,
                      READ-ONLY
/var/cache/travail    an in-memory space, which persists nothing
```

1. The volume is mounted on `/var/lib/donnees`, and the container sees the
   `marque.txt` file the volume already carries.
2. `/etc/reference` comes from the host and writing there is **refused**.
3. `/var/cache/travail` is an in-memory space, and the container can write
   there.
4. `historique.log` is **on the volume**, with its original content.

The brief is also written to `/opt/MISSION.md`.

## What is graded

The **state of the engine**, and each mount is measured **twice**: what the
inspection declares, and what the container can actually do. The two can
diverge, and the clearest case is read-only, which is declared and whose
refusal is tested.

The fourth check reads the **volume itself**, through a separate container.
Being visible from `archive` would not be enough: as long as the file is only in
its layer, it disappears with it, and that is the whole subject.

## One rule to keep beyond this lab

A mount **cannot be added** to an existing container. It is the same rule as for
published ports and for the network: everything that touches a container's
envelope is decided at its creation.
