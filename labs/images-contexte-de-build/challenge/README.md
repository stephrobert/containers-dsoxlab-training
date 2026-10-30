# What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. The repository
is in `/opt/lab-contexte/depot`:

```text
appli/Dockerfile        it FAILS, on a file that exists
appli/src/main.sh       the code, printing a token and the shared version
commun/version.txt      the SHARED file, single source
secrets/jeton-prod.txt  a production secret
archives/dump.bin       20 MB nobody needs
```

**Start by building and reading the message.** It says `/commun/version.txt`
cannot be found. Go and check: the file is there. So it is not the file that is
missing, and that is the whole lab.

## 1. Make the build replayable

A `construire.sh` script at the root of the repository, in **relative paths**.

This is not a nicety: the other three checks **replay that script**. A command
that only lives in a terminal's history is not reproducible, and there would
then be no way to verify anything.

An absolute path would point back at the original repository, and would build
something other than what is being read.

## 2. The image must carry the code and the shared version

`appli:contexte` must print its token **and** the version coming from `commun/`.

A `COPY` **never** leaves the context, and `..` does not help: the path is
normalised, then dropped. The context decides what a `COPY` can reach, and it is
chosen at build time.

The Dockerfile, for its part, does not have to sit inside the context: it can
stay where it describes something.

## 3. Neither the secret nor the archives get into the image

Widening the context puts **the whole repository** within reach of a `COPY .`.

An image gets handed around, and whatever enters it leaves with it. The check
looks for the secret's **content** everywhere in the image, not merely at its
original path.

Worth noting, because the opposite is often written: under today's builder, a
bulky context is **not** sent in full. Measured here, 20 MB in the repository
give `transferring context: 2B`. So the subject is not transfer time, it is what
enters the image.

## 4. The shared file stays the single source

Copying it into `appli/` would fix the build in one command, and it is refused.

`commun/` serves several applications. Two copies of one truth are a divergence
waiting to happen: one will be changed, the other forgotten, and the day it
shows, the two images will say different things.

The check measures it by its effect: it changes the version in a **copy** of the
repository, replays your script, and the rebuilt image must carry the **new**
value. Your image is set aside for the duration of the measurement, then given
back.

## What is not graded

The command you typed, and the path you chose. The Dockerfile can be pointed at
or moved, the exclusion can go through a dedicated file or through targeted
copies: it is the state that counts.
