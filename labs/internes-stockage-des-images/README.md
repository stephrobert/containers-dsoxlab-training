# internes-stockage-des-images: where the files land

## What this lab tests

That what a container writes is **not nowhere**: it is on the host's disk, in an
ordinary directory you can open.

The two preceding labs showed what a container sees and what it may consume.
This one closes the triptych of the internals: where its files land.

## Measured before being written

On `docker.lab`, on 2026-10-30:

| Fact | Value |
| --- | --- |
| storage driver | `overlay2`, root `/var/lib/docker` |
| a container's write layer | `GraphDriver.Data.UpperDir` |
| file written in the container | readable **immediately** at that path, from the host |
| layer's content after one write | that file **alone**, nothing else |

It is the last point that makes the notion clear: the write layer does not
contain a copy of the filesystem, it contains only the **differences**. That is
what makes containers light, and what makes them grow without being seen
growing.

## A trap avoided while writing the lab

To demonstrate that a write lands in the layer, the first idea was to have
`/etc/hostname` modified.

**Measured: the modification does not appear in the layer.** That file is a
mount Docker places from the container's directory, not a file of the image. A
check based on it would have failed whatever the learner did.

So the checks use files created **at the root**, which do not have that special
status.

## Why the fourth measurement is a weighing

Because it is the consequence that matters in operations. The write layer is not
free, and it explains the `troubleshoot-disque-plein` lab in this same section,
where a machine fills up with no volume to blame.

The size is measured **on the host**, in the layer, and not in the container: it
is the machine's disk that fills up, not a separate space.

## A detail that changed the reference solution

The load is written with **real bytes**, not allocated. A file allocated without
being written can occupy no block on the disk, and the weighing would count it
as zero.

That is the kind of detail that makes a lab look broken when it is the
measurement that was wrong.

## The quoting fix worth remembering

The setup's first version read the layer with
`index .GraphDriver.Data "UpperDir"`. The quotes, escaped to cross YAML, arrived
literally at Go, which refused with "unexpected `\\` in operand".

**The dotted form `.GraphDriver.Data.UpperDir` does the same thing with no
quotes at all**, because Go accepts dotted access on a map whose key is a valid
identifier. Verified on the machine, then applied to the setup, the tests and
the solution.

## The precondition that avoids accusing the learner

An engine set on another driver does not carry `UpperDir`, and two checks would
fail while talking about layers. So the setup and the tests verify the driver
before any measurement, and say so.

## Elevation is indispensable here

`/var/lib/docker` is not readable by an ordinary account. The first design
attempt of this lab was caught by that: a readability test ran without elevation
and returned a false negative, which nearly led to concluding that the driver
exposed no layer.

## The starting state is broken, and that is the repository's rule

The container is **blank**: nothing written inside, so its layer is empty. A
setup task verifies it, which guarantees that the learner's two writes show up
there.

## What the cleanup must remove, and what it does not have to

Removing the container is enough, and **that is the lab's demonstration**: its
write layer goes with it, and the megabytes with it.

The **image's** layers, however, survive the image until the `prune`: that is
why it is in the cleanup, and it is not decorative.

## What the lab does not require

A path. Both values can be read from the inspection as well as from the engine's
general output, and both writes are made from the container by any means. Only
the state counts.
