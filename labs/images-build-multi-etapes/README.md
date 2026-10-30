# images-build-multi-etapes: what comes from the base cannot be removed

## What this lab tests

That a tooling coming from the **base** cannot be uninstalled. It was not
installed by an instruction, so no instruction can remove it, and hiding it from
the container removes not one byte from the image.

That is what sets it apart from `images-optimiser-la-taille`: there, the cleanup
existed and was in the wrong place. Here, there is **nothing** to clean up.

## Measured before being written

On `docker.lab`, on 2026-10-30:

| Image | Size | Tooling present |
| --- | --- | --- |
| execution base | 8.3 MB | moot |
| workshop base | 39.8 MB | yes |
| one single stage | 39.8 MB | **yes** |
| two stages | 8.3 MB | **no** |

The two-stage image weighs exactly **85 bytes** more than its base. And the
fabrication fingerprint changes when the source changes, stays stable otherwise:
that is what makes the fourth check reliable without depending on the cache.

The wrong answer was **put to the test**: an `rm -rf` of the tooling in a later
instruction makes it invisible inside the container, the image weighs
**39.8 MB**, and the score is **2/4**.

## Why the tool refuses to run without its tooling

Without that refusal, the shortest answer would be to build directly on the
execution base, and the lab would be about nothing: there would be no reason left
to have two stages.

It is not a contrivance: it is the real situation. A compiler, a dependency
manager, a build chain are absent from a runtime image by design, and that is
precisely why multi-stage builds exist.

## Why the second check weighs as well as searches

The absence of the files says the container no longer sees them. The weight says
they are no longer in the image.

An `rm -rf` in a later instruction gives the first without the second, and a
check looking only for the files would reward exactly the fault
`images-optimiser-la-taille` taught how to recognise.

## Why the third check looks both ways

It requires the execution base's layers to be the prefix of the image's, **and**
the workshop's not to be.

The second half is not a repetition: an image could be light and still derive
from the workshop, if its tooling had been removed some other way. It would then
carry the workshop's layers, which a registry stores and transfers with it.

## Why the fourth check exists

The first three would pass on a product **copied** from the host, provided a
fingerprint were written into it by hand. This one closes the door differently:
it changes the source in a copy of the context and requires the product to
follow.

It is the same method as the single-source check in
`images-contexte-de-build`, and for the same reason: a dependency is proven by
changing what is depended on.

## No threshold is written

The weight ceiling is derived from the execution base, weighed at grading time.
The margin granted is twice the base, while the right answer gives 85 bytes
more: the threshold does not split borderline cases, it separates 8 MB from 39.

## The starting state is broken, and that is the repository's rule

The setup does not build the learner's image: the four checks are false before
any work. A task verifies that both bases exist, that the learner's image does
not, and that the starting Dockerfile does start from the workshop.

## A cleanup trap, paid in advance

The builder's cache goes with the rest. The checks rebuild in order to verify
that a fabrication takes place, and a stage served by a cache from the previous
pass would return a fingerprint that no longer says anything about the learner's
work.

## What the lab does not require

A path. The fabrication stage can be named or referred to otherwise, the
Dockerfile can be rewritten or duplicated. The token and the source are drawn by
the setup, the fingerprint by the fabrication: nothing is hard-coded in the
checks.
