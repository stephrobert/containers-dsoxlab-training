# An image weighing seven times its content

## The situation

An image is 52 MB for an application that occupies six. You go inside to
understand, and you find nothing: the build cache is not there, the useful
artefacts are, the container is correct.

The Dockerfile does clean up. You reread it three times without seeing
anything, because there is nothing to see: the cleanup is simply **one
instruction too late**.

And those 46 MB go out on every pull, to everyone, for ever.

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

| Writing | Size | Layers | Largest layer |
| --- | --- | --- | --- |
| cleanup one instruction too late | 52.3 MB | 5 | **44 MB** |
| cleanup in the same instruction | 14.6 MB | 4 | 6.3 MB |
| the latter, flattened | 14.6 MB | **1** | 14.6 MB |

All three produce an identical container. That is why this lab is graded by
weighing, at two scales: the whole image, and every layer.

## What is graded

The **system state**. No threshold is written in the repository: the checks
weigh the base and the artefacts at grading time, and derive from them what they
accept. A hard-coded value would be wrong as soon as the base changes version.

The first check exists for a precise reason: the fastest way to lighten an image
is to stop putting anything in it.
