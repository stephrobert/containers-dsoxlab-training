# A tooling no cleanup removes

## The situation

An application image weighs 39 MB, 30 of which are a fabrication tooling: a
mock compiler and its libraries, with no business being there once the
fabrication is over.

You apply what the previous lab taught: delete within the same instruction. And
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
