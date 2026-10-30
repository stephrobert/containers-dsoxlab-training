# docker-anatomie-dune-image: layers, sharing, configuration

## What this lab tests

That an image is a **stack** of layers, that those layers are **shared**
between images, and that it also carries a **configuration** which is not its
content. The previous lab interrogated a running container; this one
interrogates an image at rest.

## The trap is measured, not assumed

`greffe:1.0` carries **five** layers, for three instructions that look like
they each create one (two `RUN` and one `COPY`), plus the base. The fifth comes
from `WORKDIR`, which creates the directory when it does not exist.

Measured on `docker.lab` on 2026-10-30. That is what makes the lab useful:
reading the Dockerfile is not enough, and a learner who counts the instructions
is off by one. The check's message **says so**, rather than leaving them to
recount in circles.

## Why two images, and why their first lines are identical

Layer sharing only happens when the instruction that produces them is
identical, in the same order, on the same context. So the two Dockerfiles share
their first three lines **character for character**, and the same context file.

That is fragile by nature, and that is the subject: the slightest difference,
even a space, would produce two distinct sets of layers and double the space
used. A setup task verifies that the sharing does happen before handing over.

## Both directions of sharing, and why they are not the same question twice

| Check | What it measures | What it teaches |
| --- | --- | --- |
| `partagees` | the layers common to both | why ten images on one base do not weigh ten bases |
| `propres` | the ones `2.0` adds | what a variant really costs |

The first justifies an architecture, the second puts a figure on a decision. It
is the same set seen from both sides, and the two numbers serve different
conversations.

## The revision: a value that is nowhere

It is set **on the command line** at build time, with `--label`. So it is in no
Dockerfile on the machine, which the learner can read. And it does **not**
appear in the image history, which was verified on the machine rather than
assumed.

It exists only in `.Config.Labels`, and it is drawn at random on every `run`.
It is the only one of the four answers that can neither be deduced nor copied.

## An honest word about repeatability

The first three answers **do not change** from one pass to the next: they
describe a fixed build. A learner who has already played the lab could copy
them.

That is accepted. The lab is not a guessing game, and copying the three numbers
presupposes having found them a first time. The fourth answer, though, makes it
impossible to replay the lab from memory.

## The starting state is broken, and that is the repository's rule

| Laid down by the setup | Starting state | Expected move | Check |
| --- | --- | --- | --- |
| `reponses.txt` | four keys, four **empty** values | fill them in | 1 to 4 |

## What the cleanup must remove

The **images**, not only their tags. A kept image would still carry the
previous pass's revision, and the next `run` would build on top of it: the
revision check would become true with no work, since yesterday's answer would
still be valid today.

## What the lab does not require

A path. `docker image inspect`, `docker history` and `docker image ls --tree`
lead to the same layer count. The revision can be read through a precise field
as well as in the full output of the inspection.
