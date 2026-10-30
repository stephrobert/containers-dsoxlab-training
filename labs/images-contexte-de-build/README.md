# images-contexte-de-build: a file that exists, and cannot be found

## What this lab tests

That a `COPY` cannot leave the build context, and that **the message no longer
says so**. The file exists, the engine says it cannot be found, and the hour
lost hunting for a typo is the cost of that sentence.

## Measured before being written

On `docker.lab`, on 2026-10-30, the same Dockerfile under both builders:

| Builder | Message |
| --- | --- |
| buildkit, the default | `"/commun/version.txt": not found` |
| classic, `DOCKER_BUILDKIT=0` | `forbidden path outside the build context` |

The second named the cause. The first says "not found", because the `..` is
normalised then dropped: the engine only looks inside the context, and reports
what it sees, not what is there. **The message degraded when the builder
changed**, and that is why so many answers found online talk about a missing
file.

And the lazy answer was **put to the test**: copying the shared file into the
application's directory scores **3/4**, with the fourth check refusing on its
own. Had it scored 4/4, the lab's constraint would have been nothing but a
sentence in a brief.

## A measurement that changed the lab I was about to write

The first design graded the **weight of the context**: a large directory in the
repository, and the exclusion to lighten the transfer. The measurement took it
apart.

Under buildkit, with 20 MB of archives in the repository, `transferring context`
reports **2 bytes**, and the image weighs **exactly** the size of the base, with
and without the exclusion. Buildkit only sends what the `COPY` instructions
need.

Grading transfer time would therefore have measured a belief, and the lab would
have taught an argument that has become false. What stays true lies elsewhere:
widening the context puts the whole repository within reach of a `COPY .`, the
secret included.

## Why a build script

The other three checks **replay it**, and it is the only way to verify that the
shared file is still the single source: without a script, the build command
exists nowhere, and all one could do is reread the Dockerfile, which would grade
the form.

The check plays it in a **copy** of the repository, hence the requirement of
relative paths. An absolute path would point back at the original repository,
and would build something other than what is being measured.

## Why the learner's tag is saved

The script rebuilds under the expected name: playing it in a copy **overwrites**
the learner's image.

Without a safeguard, the next `check` would find an image carrying the check's
version, and the second check would refuse correct work. So the tag is set aside
before, and given back after. Verified afterwards: the image still carries its
original version, and no backup tag remains.

**A test does not leave the system in a state it produced itself**, and it is
the same rule governing the sandbox rebuilds of `images-ordre-des-couches`.

## Why the secret is searched by its content

The check looks for the secret's string **everywhere** in the image, not merely
at its original path.

Searching for a path is worked around by moving the file, and that workaround
teaches nothing: what matters is that the secret is nowhere. A lab grading the
path would teach how to file a secret elsewhere rather than how to keep it out.

## The starting state is broken, and that is the repository's rule

The initial build **fails**, and the expected script does not exist: the four
checks are therefore false before any work. A setup task verifies that the build
does fail, that the script is absent, and that the shared file and the secret
are in place: without it, a badly cleaned pass would leave the lab already
solved.

## A cleanup trap, paid in advance

The repository goes away **as a whole**: it carries the fixed Dockerfile, the
script, and possibly a copy of the shared file. And the **builder's cache** goes
with it, which `docker image prune` does not touch: this lab's checks rebuild,
and a surviving cache would serve an image whose context is no longer the one
being measured.

## What the lab does not require

A path. The Dockerfile can be pointed at by an option or moved, the exclusion
can go through a dedicated file or through targeted copies. The token and the
version are drawn by the setup and read back from the repository at grading
time: nothing is hard-coded in the checks.
