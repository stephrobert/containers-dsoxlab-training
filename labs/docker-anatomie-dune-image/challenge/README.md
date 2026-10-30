# What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. Two images are
**already built**: nothing to pull, nothing to build.

```text
greffe:1.0    the one being dissected
greffe:2.0    the one starting from the same base layers
```

Their Dockerfiles can be read in `/opt/lab-anatomie`. You can and should read
them, but **they do not give the answers**: not every instruction creates a
layer, and one of them creates a layer without looking like it. The engine is
the only source.

The four answers go into `/opt/lab-anatomie/reponses.txt`, one line per entry,
with no spaces around the equals sign.

## 1. The number of layers of `greffe:1.0`

On the `couches=` line. A plain integer.

Count the layers **of the image**, the ones the engine stacks, not the lines of
the Dockerfile. If your count lands on the number of instructions that look
like they create one, that is a sign something is missing.

## 2. The number of layers common to both images

On the `partagees=` line. A plain integer.

Both images start from the same base and their first instructions are
identical: those layers are **the same object**, stored once on disk. That is
the answer to "why do ten images on one base not weigh ten times the base".

Compare the two **lists of layers**, not the two Dockerfiles.

## 3. The number of layers of `greffe:2.0`'s own

On the `propres=` line. A plain integer.

The ones `greffe:2.0` carries and `greffe:1.0` does not. That is the count in
the other direction, and it is not the same question: it is what a variant
really costs once the base is already there.

## 4. The revision carried by `greffe:1.0`

On the `revision=` line.

It is written in **no file** on this machine, and it is not in the image's
**history** either. It lives in the image's **configuration**, next to its
environment and its default command.

It is drawn at random on every pass: a value read during a previous pass is no
longer valid.

## What is not graded

The command you typed. All four values are recomputed by questioning the
images, then compared with what you wrote. Several paths give the same count,
and all of them count.
