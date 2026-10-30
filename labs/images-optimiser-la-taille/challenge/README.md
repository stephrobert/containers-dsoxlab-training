# What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. The context is
in `/opt/lab-taille/appli`:

```text
Dockerfile      it WORKS, and the image weighs seven times its content
attendus.txt    the three artefacts the application uses
src/main.sh     the code, printing a token and the fabrication fingerprint
```

**Start by building and weighing.** Then go inside the image: the build cache is
not there, the artefacts are. Finally, weigh **each layer**.

## 1. The image must work and carry its artefacts

`appli:legere` must print its token **and** a fabrication fingerprint, and carry
the three artefacts from `attendus.txt`.

This check exists for a precise reason: the fastest way to lighten an image is
to stop putting anything in it. The fingerprint also proves the fabrication did
run **in this image**.

## 2. No layer may carry the cache

This is the heart of the lab, and the measurement that makes it visible.

The container shows nothing: a later layer deletes the cache, so it cannot be
found in the assembled image. It is there all the same, **inside a layer**, and
it is downloaded with it.

Measured on this machine: **44 MB** of layer for a cleanup played one
instruction too late, **6.3 MB** when it is played in the same one.

## 3. The total size must stay close to what is needed

Two measurements rather than one, and they do not say the same thing.

One layer can stay under its ceiling while several, together, weigh twice what
is needed: a cache written in two goes, or a second download, spreads out
without ever making one large layer.

The threshold is **computed**: the base is weighed, the artefacts too. Nothing is
written in the repository.

## 4. The image must still derive from the base

Flattening the image gives the right size, and it is refused.

Measured here: 14.6 MB in **one** layer, exactly the weight of the correct
writing. Both weighing checks would be green.

And it no longer shares any layer with its base. Common layers are what make a
registry store the base only once, and a host that already has it download only
the difference. A flattened image is stored and transferred **in full**, for
every variant.

**Size is won in the instructions, not after the fact.**

## What is not graded

The command you typed. The cleanup can be written in several ways as long as it
happens in the instruction that created what it removes.
