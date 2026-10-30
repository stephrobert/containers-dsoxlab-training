# What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. The build
context is in `/opt/lab-couches/appli`:

```text
Dockerfile          it WORKS, and its order destroys the cache
dependances.txt     three dependencies, one second of installation each
src/main.sh         the code, which prints a token
notes/brouillon.log a draft, with no business being in the image
```

**Start by measuring.** Build, change a line of `src/main.sh`, rebuild, and
watch the installation replay. It did not change.

## 1. Build `appli:ordonnee`, one that really works

The image must **print its token** when launched, and carry the **three
dependencies** declared in the manifest.

This check exists for a precise reason: the fastest way to make a cache
efficient is to stop installing anything, and that is not one.

## 2. Let in only what serves

Neither the draft nor the Dockerfile must end up in the image.

A copy of the whole context does not copy "the code", it copies **everything**.
Those files swell the image, and above all **each of them invalidates the cache
when it changes**: editing the Dockerfile would be enough to redo the
installation.

An exclusion file or a targeted copy give the same state. Both count.

## 3. A code change must no longer redo the installation

This is the heart of the lab.

Every instruction depends on what precedes it, and on nothing else. The code
changes on every commit: everything coming **after** it in the Dockerfile will
be redone every time. So nothing must be left behind it.

The expensive work, for its part, depends on the **manifest**. It must come
right after it, and the manifest must be copied **alone**.

## 4. A manifest change must, on the contrary, redo it

This is the half that gets forgotten, and without it the lab would teach a trap.

Copying the manifest **after** the installation would make the previous check
green and have the cache serve even when the dependencies change: the image
would stay frozen on the old ones, and nobody would see it before production.

The check verifies two things: that the work is redone, and that the new
dependency is **really installed**.

## How the checks measure this

The installation tool writes a **fingerprint** into the image, drawn at random
at the moment it runs. Two images carrying the same fingerprint did not replay
the installation.

The checks rebuild in a **copy** of the context: your working directory is not
touched.

## What is not graded

The command you typed, and the path you chose. Nothing to write in a form: this
lab is graded on the image.
