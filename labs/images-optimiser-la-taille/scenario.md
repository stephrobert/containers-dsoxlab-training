# A layer weighing seven times its content

## The situation

An image takes 101 MB of **disk space** for an application that occupies six.
You go inside to understand, and you find nothing: the build cache is not there,
the useful artefacts are, the container is correct.

The Dockerfile does clean up. You reread it three times without seeing
anything, because there is nothing to see: the cleanup is simply **one
instruction too late**.

And the layer carrying them weighs **44 MB** according to `docker history`,
seven times the 6 MB it ships. That space is taken on every disk that pulls the
image, and deleting it later does not take it out of the layer.

## The goal

The context is in `/opt/lab-taille/appli`. Build the Dockerfile as it stands,
then weigh the image and compare it with what it actually contains.

Go inside: the cache is not there, the artefacts are. Then weigh **each layer**,
and you will see where the megabytes went.

Build `appli:legere`, which must:

```text
print its token and the fabrication fingerprint
carry the three artefacts from attendus.txt
weigh barely more than its base and its artefacts
STILL DERIVE from the base lab-taille:1.0
```

The brief is also laid down in `/opt/MISSION.md`.

## The rule this lab draws out

**A layer keeps what a later layer deletes.** Deleting afterwards hides the file
from the container, and removes nothing from the image: the layer is frozen, and
it travels in full.

So the deletion has to happen in the **very** instruction that created what is
being deleted.

## The last constraint rules out a tempting idea

Flattening the image gives the right size. Measured on this machine: 14.6 MB, in
a single layer, exactly the weight of the correct writing.

And it no longer shares **any** layer with its base. Common layers are what make
a registry store the base only once, and a host that already has it download
only the difference. A flattened image is stored and transferred in full, for
every variant: the advertised gain is given back a hundredfold.

**Size is won in the instructions, not after the fact.**

## What is measured

| Writing | `DISK USAGE` | Layers | Largest layer |
| --- | --- | --- | --- |
| cleanup one instruction too late | 101.1 MB | 6 | **44.1 MB** |
| cleanup in the same instruction | 25.6 MB | 5 | 9.08 MB |
| the latter, flattened | 25.5 MB | **1** | 15.4 MB |

All three produce an identical container. That is why this lab is graded by
weighing, at two scales: the whole image, and every layer.

## What is graded

The **system state**. No threshold is written in the repository: the checks
weigh the base and the artefacts at grading time, and derive from them what they
accept. A hard-coded value would be wrong as soon as the base changes version.

The first check exists for a precise reason: the fastest way to lighten an image
is to stop putting anything in it.
