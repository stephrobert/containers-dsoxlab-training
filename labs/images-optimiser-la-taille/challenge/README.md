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

## What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. The context is
in `/opt/lab-taille/appli`:

```text
Dockerfile      it WORKS, and the image weighs seven times its content
attendus.txt    the three artefacts the application uses
src/main.sh     the code, printing a token and the fabrication fingerprint
```

**Start by building and weighing.** Then go inside the image: the build cache is
not there, the artefacts are. Finally, weigh **each layer**.

### 1. The image must work and carry its artefacts

`appli:legere` must print its token **and** a fabrication fingerprint, and carry
the three artefacts from `attendus.txt`.

This check exists for a precise reason: the fastest way to lighten an image is
to stop putting anything in it. The fingerprint also proves the fabrication did
run **in this image**.

### 2. No layer may carry the cache

This is the heart of the lab, and the measurement that makes it visible.

The container shows nothing: a later layer deletes the cache, so it cannot be
found in the assembled image. It is there all the same, **inside a layer**, and
it is downloaded with it.

Measured on this machine: **44 MB** of layer for a cleanup played one
instruction too late, **6.3 MB** when it is played in the same one.

### 3. The total size must stay close to what is needed

Two measurements rather than one, and they do not say the same thing.

One layer can stay under its ceiling while several, together, weigh twice what
is needed: a cache written in two goes, or a second download, spreads out
without ever making one large layer.

The threshold is **computed**: the base is weighed, the artefacts too. Nothing is
written in the repository.

### 4. The image must still derive from the base

Flattening the image gives the right size, and it is refused.

Measured here: 14.6 MB in **one** layer, exactly the weight of the correct
writing. Both weighing checks would be green.

And it no longer shares any layer with its base. Common layers are what make a
registry store the base only once, and a host that already has it download only
the difference. A flattened image is stored and transferred **in full**, for
every variant.

**Size is won in the instructions, not after the fact.**

### What is not graded

The command you typed. The cleanup can be written in several ways as long as it
happens in the instruction that created what it removes.
