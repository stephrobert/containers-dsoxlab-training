# images-migrer-vers-alpine: changing base is not changing a line

## What this lab tests

That an application depends on what its base gives it, and that the message
reminding it of this **does not name the cause**. The file exists, the engine
says it cannot be found, and what is missing is the interpreter of its shebang.

## Measured before being written

On `docker.lab`, on 2026-10-30:

| Base | Size |
| --- | --- |
| `debian:13-slim` | 78.9 MB |
| `alpine:3.22` | 8.3 MB, **9.5 times less** |

The same script, as entrypoint on Alpine: `exec /src/traiter.sh: no such file or
directory`. Run through `sh`: `not found`, code **127**. And the file:
`-rwxr-xr-x 205 bytes`, perfectly present.

The POSIX equivalent gives the same result on both bases, measured:
`somme=26 max=11` on either side.

## Why this lab ties three others together

Code 127 is the one from `troubleshoot-exit-127`: a file found but not
executable, or a missing interpreter. The misleading message is the one from
`images-contexte-de-build`: the engine reports what it sees, not what is there.
And the weight gain is the same subject as `images-optimiser-la-taille`, from
the other end: that lab lightens what you add, this one lightens what you start
from.

A learner who has played all three recognises the mechanism before reading the
hint.

## Why four checks that do not overlap

The first tests the result on the repository's data. The second reads the base
**in the layers**: an image can work and weigh the right amount without having
changed base. The third weighs, against the reference.

The fourth is the only one catching an application that **recites**: it mounts
data it has never seen and recomputes what it should return. The other three
would pass on an image printing a frozen result, since the repository's data
does not change during a session.

## Why the base is read in the layers

Looking for `/etc/alpine-release` would be shorter, and more fragile: it is a
distribution convention, and it says nothing about an image rebuilt from another
base that happened to carry the same file.

The layers are the thing itself: the light base's must be the prefix of the
image's. It is the same measurement as the anti-flattening check of
`images-optimiser-la-taille`, and for the same reason.

## Why both routes are accepted

Rewriting the script in POSIX sh, or installing bash on the light base: both
pass all four checks.

This is deliberate. The lab **argues for** the first, in its brief and in its
reference solution: adding a 2 MB interpreter for two constructs, one of which
fits in a loop, amounts to paying for the base you have just left. But it does
not **grade** it, because the second is a legitimate choice when the script is
long, and a check forbidding it would grade an opinion.

The catalogue does have one place where an opinion is graded, in
`troubleshoot-permission-refusee`, and that is because a method lab had already
settled the matter. Here, nothing has.

## No result, no threshold is written

The data is drawn by the setup on every pass, the result is recomputed at
grading time, and the weight ceiling is derived from the reference image weighed
at the same moment.

That is also why the setup **builds** `appli:lourde`: without that reference, a
threshold would have to be written in the repository, and it would be wrong at
the first change of base.

## A writing detail that was fixed

The data was first written by a `join('\n')` inside a YAML literal block, which
relies on two layers of escaping, YAML then Jinja, whose rule changes with the
scalar's style. An explicit loop relies on neither, and its rendering was
**proven on the Jinja that actually runs the playbook**, the one `dsoxlab`
ships.

## The starting state is broken, and that is the repository's rule

`appli:legere` does not exist: the four checks are false before any work. A
setup task verifies that the reference works, that the learner's image does not
exist, and that the light base is indeed there.

## A cleanup trap, paid in advance

The reference image goes away with the rest. The checks compare against it, in
size as in result: leaving it behind would compare one pass's work with another
pass's reference, whose randomly drawn data is no longer the same.

## What the lab does not require

A path. The script can be rewritten or the base completed, the Dockerfile
modified or duplicated. The token and the data are drawn by the setup: nothing
is hard-coded in the checks.
