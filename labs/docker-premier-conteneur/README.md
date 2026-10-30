# docker-premier-conteneur: three verbs that do not overlap

## What this lab tests

The container life cycle, and the only idea that matters at this stage: **a
stopped container still exists**. Run, stop and remove are three distinct
actions, and the last two are confused by almost everyone once.

This is the **entry lab of the catalog**, and the backlog puts a constraint on
it that no other carries: it must be played in under a minute, with nothing to
build. A first lab that makes people wait discourages before it teaches. So the
setup lays everything out, the image included, and only three commands remain.

## Why the setup lays out TWO containers

Because one would not allow grading the two actions separately. With a single
container, a learner who removes it instead of stopping it reaches a state
indistinguishable from a successful clean-up.

| Laid out by the setup | Starting state | Expected action | Check |
| --- | --- | --- | --- |
| `vitrine` | `running` | stop it | 3, and it refuses removal |
| `rebut` | `created` | remove it | 4 |
| *nothing* | absent | run `premier` | 1 and 2 |

Check 3 distinguishes the two mistakes in its message, because they call for
opposite actions: a container still running was not stopped, a container gone
was removed out of excessive zeal.

## The four checks, and why two bear on the same container

`premier` carries two, measuring different things: that it is **running** and
that its **logs** carry an imposed line. The second proves a command was passed
to the container, which is the real action of the CLI; the first proves it
stayed alive, which is the immediate trap of the exercise, since a container
whose command finishes stops right away.

## The starting state is broken, and that is the repo's rule

A test must bear on what the starting state does NOT carry. All four checks are
therefore false at the start, and a setup task **verifies** it before handing
over: `vitrine running`, `rebut created`, and no `premier`. Without that check,
a badly cleaned previous run would leave the lab already solved before being
laid out.

## Alpine rather than the Debian image already present

To depend on no other lab, and so that `cleanup` can remove its image without
risking taking `debian:13` with it, which `images-identifier-image` needs. A lab
that cleans up another's state is a failure discovered elsewhere, and nobody
traces it back to its cause.

The image is pinned by digest, then tagged `lab-base:1.0` on the machine: a
digest is not copied from memory, and the mission does not ask for it.

## What cleanup must remove, and what gets forgotten

The **three** containers, `premier` included, which the setup does not create.
It is the learner's work, and leaving it behind would hand the next lab a
container it did not lay out. The image is removed by **both** references, the
local tag and the digest: removing only the tag would leave a nameless entry in
the engine's inventory, hence a discrepancy the validator refuses.
