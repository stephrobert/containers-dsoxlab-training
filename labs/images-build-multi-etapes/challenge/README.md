# A tooling no cleanup removes

## The situation

An application image weighs 39 MB, 30 of which are a fabrication tooling: a
mock compiler and its libraries, with no business being there once the
fabrication is over.

The usual reflex is to delete within the **same instruction** as the install, because a layer keeps what a later layer erases. And
you find there is **nothing to delete**: the tooling was not installed by an
instruction of this Dockerfile. It comes from the **base**.

An `rm -rf` hides it from the container, and the image still weighs 39 MB.
Measured on this machine.

## The goal

The context is in `/opt/lab-multietapes/appli`. Build the Dockerfile as it
stands under the name `appli:finale`: it works, the application runs, the
product is correct.

Go inside and look for `/usr/lib/atelier` and `/usr/local/bin/fabriquer`. They
are there. Try to remove them, and see what it changes on the scales.

`appli:finale` must:

```text
print its token and the product's content
carry NEITHER the tooling NOR the fabrication tool
be built on the execution base
carry a product REALLY FABRICATED, not copied
```

An execution base is already on the machine, under the name
`lab-execution:1.0`. The brief is also laid down in `/opt/MISSION.md`.

## Why there is only one route

What comes from the base cannot be uninstalled. The only way for an image not
to carry a tooling is for it **not to start from the base that carries it**.

The fabrication, for its part, needs it. So two bases are needed in the same
Dockerfile: the workshop to build, the execution base to ship, and the product
passing from one to the other.

**The fabrication tool refuses to run without its tooling.** Building directly
on the execution base is therefore impossible, and that is not an oversight: it
is what closes the false route.

## What is measured

| Image | Size | Tooling present |
| --- | --- | --- |
| execution base | 8.3 MB | moot |
| workshop base | 39.8 MB | yes |
| one single stage | 39.8 MB | **yes** |
| two stages | 8.3 MB | **no** |

Measured on 2026-10-30. The two-stage image weighs exactly 85 bytes more than
its base, and its product is identical.

## What is graded

The **system state**, at four places that do not overlap: the product and its
source, the absence of the tooling **doubled with a weighing**, the base read in
the layers, and the product's dependency on its source.

That last check changes the source in a **copy** of the context and requires the
product to follow. A product copied from the host would stay frozen, and that is
the only way to see it: the product carries a fingerprint drawn at the moment
the fabrication runs.

Your image is not overwritten in the process: the rebuild happens under a name
of its own.

## What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. Two bases and a
context are already there:

```text
lab-atelier:1.0     39.8 MB, 30 of which are fabrication tooling
lab-execution:1.0   8.3 MB, no tooling
appli/Dockerfile    a single stage, on the workshop
```

**Start by building it as it stands under the name `appli:finale`**, then look
for `/usr/lib/atelier` inside the image. Try to remove it, and weigh.

### 1. The application must run and carry its product

`appli:finale` must print its token and the product's content, whose **source**
is the repository's, drawn at random on every pass.

This check exists for a precise reason: the fastest way to remove a tooling is
to stop building anything.

### 2. Neither the tooling nor the tool may be there

Two measurements, and they are complementary: the **absence of the files** says
the container no longer sees them, the **weighing** says they are no longer in
the image.

An `rm -rf` in a later instruction gives the first without the second.
**a layer keeps what a later layer erases**, and the file travels with the image even though it is gone from the final view.

Here it is worse: there is nothing to
clean up at all, since the tooling comes from the base.

### 3. The image must be built on the execution base

The check compares the **layers**, both ways: the execution base's must be the
prefix of the image's, and the workshop's must **not** be.

The second half counts as much: even when light, an image starting from the
workshop carries its layers, and a registry stores and transfers them with it.

### 4. The product must be fabricated, not copied

The check changes the **source** in a copy of the context, rebuilds, and
requires the product to follow.

The product carries a fingerprint drawn at the moment the fabrication runs: if
it does not change when the source changes, the fabrication was not replayed,
and the product does not depend on its source.

Your image is not overwritten: the rebuild happens under a name of its own.

### Two things to know before searching

**The fabrication tool refuses to run without its tooling.** Building on the
execution base is therefore impossible: that is not an oversight, it is what
closes the false route.

**Copy only the product.** Copying `/usr/lib` or `/` from the fabrication stage
would bring the tooling along, and the weighing would say so.

### What is not graded

The command you typed. The fabrication stage can be named or referred to
otherwise, and the Dockerfile can be rewritten or duplicated.
