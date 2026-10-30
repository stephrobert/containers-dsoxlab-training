# images-non-root: `USER` changes the identity, and no right

## What this lab tests

That `USER` changes **no right** on what has already been laid down. The
directories created before it belong to root, and the application stops writing
at the very moment it stops being privileged.

## Measured before being written

On `docker.lab`, on 2026-10-30, the same application under three writings:

| Writing | uid | Write into /donnees |
| --- | --- | --- |
| without `USER` | 0 | ok |
| `USER` alone | 10001 | **refused**, "Permission denied" |
| `USER` + owner aligned | 10001 | ok |

And both wrong answers were **put to the test**: `USER appli` instead of the
numeric uid scores **3/4**, and `chmod 777` instead of the `chown` scores
**3/4** as well. Each is refused only by the check that bears on it.

## Two measurements that decided what the lab does not grade

**`docker run --user 0:0` on the non-root image returns uid=0.** The
Dockerfile's `USER` is therefore a default, not a guarantee. That is why the
checks run the image **with no identity option at all**: with the option, any
image would pass, and the lab would grade the command instead of the image.

**A non-root process listens on port 80** inside a container, measured. It is
often written that root is required below 1024; the engine grants the
corresponding capability by default. So no check bears on ports: **that would
measure a belief**, and a lab that grades a belief teaches it.

## Why the means is graded, not only the effect

Two answers make the application write: giving it the directory, or opening it
to everyone. The second works perfectly, and it is refused.

Making a directory writable by anyone so that an unprivileged process can write
in it undoes exactly what going non-root was meant to achieve. So the second
check measures the effect, and the third the means.

It is the same structure as `troubleshoot-permission-refusee`, and for the same
reason: a security lab accepting the shortcut teaches the shortcut.

## Why the numeric uid is required

A `USER appli` is resolved in the image's `/etc/passwd`. An orchestrator
refusing root containers does not read that file: it reads the declaration, and
it cannot prove a name is not root.

That point was **not** measured here, there being no orchestrator on the lab's
machine: it is the reason for the rule, not a measurement. What is measured is
that `USER appli` gives `.Config.User = 'appli'` and `USER 10001:10001` gives
`'10001:10001'`: the declaration is indeed what the image passes on.

## A reading defect, caught by the cycle

The third check refused the reference solution, reporting an impossible uid,
"10001 gid=10001". The extractor split each line on its first `=`, and the line
`uid=10001 gid=10001` carries two. The splitting is now done word by word.

The defect is instructive: the check **measured right and read wrong**, and its
message accused the learner of a discrepancy that did not exist.

## The starting state is broken, and that is the repository's rule

The setup does not build the image: the four checks are false before any work. A
task verifies that the base exists, that the learner's image does not, and that
the starting Dockerfile carries **no** `USER`.

## What the lab does not require

A particular uid, nor a user name, nor an exact mode. All that counts is a
non-zero uid, a directory belonging to the application, a mode that does not
open writing to everyone, and a numeric declaration. The token is drawn by the
setup: nothing is hard-coded in the checks.
