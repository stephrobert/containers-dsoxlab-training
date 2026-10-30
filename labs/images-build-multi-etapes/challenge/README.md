# What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. Two bases and a
context are already there:

```text
lab-atelier:1.0     39.8 MB, 30 of which are fabrication tooling
lab-execution:1.0   8.3 MB, no tooling
appli/Dockerfile    a single stage, on the workshop
```

**Start by building it as it stands under the name `appli:finale`**, then look
for `/usr/lib/atelier` inside the image. Try to remove it, and weigh.

## 1. The application must run and carry its product

`appli:finale` must print its token and the product's content, whose **source**
is the repository's, drawn at random on every pass.

This check exists for a precise reason: the fastest way to remove a tooling is
to stop building anything.

## 2. Neither the tooling nor the tool may be there

Two measurements, and they are complementary: the **absence of the files** says
the container no longer sees them, the **weighing** says they are no longer in
the image.

An `rm -rf` in a later instruction gives the first without the second.
`images-optimiser-la-taille` showed why; here it is worse: there is nothing to
clean up at all, since the tooling comes from the base.

## 3. The image must be built on the execution base

The check compares the **layers**, both ways: the execution base's must be the
prefix of the image's, and the workshop's must **not** be.

The second half counts as much: even when light, an image starting from the
workshop carries its layers, and a registry stores and transfers them with it.

## 4. The product must be fabricated, not copied

The check changes the **source** in a copy of the context, rebuilds, and
requires the product to follow.

The product carries a fingerprint drawn at the moment the fabrication runs: if
it does not change when the source changes, the fabrication was not replayed,
and the product does not depend on its source.

Your image is not overwritten: the rebuild happens under a name of its own.

## Two things to know before searching

**The fabrication tool refuses to run without its tooling.** Building on the
execution base is therefore impossible: that is not an oversight, it is what
closes the false route.

**Copy only the product.** Copying `/usr/lib` or `/` from the fabrication stage
would bring the tooling along, and the weighing would say so.

## What is not graded

The command you typed. The fabrication stage can be named or referred to
otherwise, and the Dockerfile can be rewritten or duplicated.
