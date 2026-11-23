# The Dockerfile works, and that is precisely the problem

## The situation

Continuous integration takes six minutes to build an image, and nobody
understands why: the last change was one line of code.

You look at the Dockerfile. It is short, readable, and it **works**: the image
it produces is correct, the application runs. Nothing looks broken, so nothing
seems to need fixing, and that is why this defect lives in a repository for
years.

Then you build twice in a row, changing one line in between, and you watch the
installation of the dependencies replay in full. It did not change. It is redone
because an instruction placed before it did.

## The goal

The build context is in `/opt/lab-couches/appli`. The Dockerfile there works:
build it, the image is correct.

**Then measure what it costs.** Build once, change a line of `src/main.sh`,
rebuild, and watch the time the installation takes. It costs a second per
dependency, and there are three.

Reorder the instructions so that this work is:

```text
served by the cache   when the CODE changes
redone                when the MANIFEST changes
```

Both halves count. A cache that always serves is as serious a fault as a cache
that never serves: the image would stay frozen on old dependencies, and nobody
would see it before production.

And do not let into the image what has no reason to be there: the context
carries a draft and the Dockerfile itself, which a copy of the whole context
takes along without asking.

Build the final image under the name `appli:ordonnee`. It must print its token
when launched, and carry the three declared dependencies.

The brief is also laid down in `/opt/MISSION.md`.

## The rule this lab draws out

**Every instruction depends on what precedes it, and on nothing else.** The
cache serves a layer as long as everything above it is unchanged.

Hence the order: what rarely changes at the top, what changes on every commit
at the bottom, and every expensive piece of work placed right after what it
depends on, alone. So the dependency manifest is copied **alone**, before the
installation, and the code **after** it.

## What is graded

The **system state**, and it is measured by its effect. The checks rebuild the
image in a **copy** of the context, once with one extra line of code, once with
one extra dependency, and compare a fingerprint the installation tool leaves in
the image. Two images carrying the same fingerprint did not replay the
installation.

Your working directory is not touched, and no path is imposed: an exclusion file
and a targeted copy give the same state, and it is the state that counts.

## What is asked

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

### 1. Build `appli:ordonnee`, one that really works

The image must **print its token** when launched, and carry the **three
dependencies** declared in the manifest.

This check exists for a precise reason: the fastest way to make a cache
efficient is to stop installing anything, and that is not one.

### 2. Let in only what serves

Neither the draft nor the Dockerfile must end up in the image.

A copy of the whole context does not copy "the code", it copies **everything**.
Those files swell the image, and above all **each of them invalidates the cache
when it changes**: editing the Dockerfile would be enough to redo the
installation.

An exclusion file or a targeted copy give the same state. Both count.

### 3. A code change must no longer redo the installation

This is the heart of the lab.

Every instruction depends on what precedes it, and on nothing else. The code
changes on every commit: everything coming **after** it in the Dockerfile will
be redone every time. So nothing must be left behind it.

The expensive work, for its part, depends on the **manifest**. It must come
right after it, and the manifest must be copied **alone**.

### 4. A manifest change must, on the contrary, redo it

This is the half that gets forgotten, and without it the lab would teach a trap.

Copying the manifest **after** the installation would make the previous check
green and have the cache serve even when the dependencies change: the image
would stay frozen on the old ones, and nobody would see it before production.

The check verifies two things: that the work is redone, and that the new
dependency is **really installed**.

### How the checks measure this

The installation tool writes a **fingerprint** into the image, drawn at random
at the moment it runs. Two images carrying the same fingerprint did not replay
the installation.

The checks rebuild in a **copy** of the context: your working directory is not
touched.

### What is not graded

The command you typed, and the path you chose. Nothing to write in a form: this
lab is graded on the image.
