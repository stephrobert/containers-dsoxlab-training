# images-optimiser-la-taille: what a layer keeps

## What this lab tests

That a layer keeps what a **later** layer deletes, and that the container shows
nothing of that weight. The cache is not visible in it, the useful artefacts
are, the behaviour is correct. The defect only shows on the scales.

## Measured before being written

On `docker.lab`, on 2026-10-30, the same work in three forms:

| Form | Size | Layers | Largest layer |
| --- | --- | --- | --- |
| cleanup one instruction too late | 52.3 MB | 5 | **44 MB** |
| cleanup in the same instruction | 14.6 MB | 4 | 6.3 MB |
| the latter, flattened | 14.6 MB | **1** | 14.6 MB |

All three produce an identical container. And both wrong answers were **put to
the test**: the starting Dockerfile scores **2/4**, refused by the two weighings;
the flattened image scores **2/4** as well, refused by the layer sharing and by
the per-layer weighing.

## Why four checks, and why two weighings

One layer can stay under its ceiling while several, together, weigh twice what
is needed: a cache written in two goes, or a second download, spreads out
without ever making one large layer. The overall weighing catches that, the
per-layer weighing catches the late cleanup. Both are necessary.

The first check exists because **the fastest way to lighten an image is to stop
putting anything in it**. The fingerprint, drawn at random by the fabrication
tool at the moment it runs, proves the fabrication happened in this image.

## Why the fourth check refuses flattening

It gives the right size, and that is exactly the problem: both weighings would
be green.

Common layers are what make a registry store the base only once, and a host
that already has it download only the difference. A flattened image is stored
and transferred in full, for every variant: the advertised gain is given back a
hundredfold. So the check compares the base's layers with the prefix of the
image's.

## A message that blamed the wrong cause, and its fix

On a flattened image, the per-layer weighing fails too, since the single layer
carries everything. The verdict was right, and the message said "that layer
carries the cache", which is **false**: the cache is not in it.

So the check now looks at layer sharing before concluding, and says the image
was flattened, pointing at the check that deals with it. A message naming the
wrong cause sends you looking in the wrong place, and that is exactly what this
catalogue holds against the message in the neighbouring lab on build context.

## No threshold is written

The checks weigh the base, then the artefacts **inside the image**, and accept
the base plus twice the artefacts. A hard-coded value would be wrong as soon as
the base changes version, and the lab would then refuse correct work.

The margin is wide on purpose: the measurement gives 6.3 MB for the correct
writing against 44 for the other. The threshold does not split borderline cases,
it separates two worlds.

## A probe defect, caught by the cycle

The first draft read the layers with a Go format written **bare** in the
command: `{{range .RootFS.Layers}}...` contains spaces, the shell split it, and
docker received a truncated format. The probe returned empty output, the check
**skipped** instead of refusing, and the cycle reported "3 passed, 1 skipped".

The correct form passes the format as a parameter, which testinfra quotes. And
the mistake earned one more check: a detector went through the catalogue's **71**
test files looking for the same defect, after being proven on one faulty case
and three sound forms. No other lab was affected.

Two of its earlier drafts were wrong, as it happens: the first stayed silent on
the very case it was looking for, the second accused two attested, perfectly
sound labs. **A safeguard is proven both ways before it is used.**

## The starting state is broken, and that is the repository's rule

The setup **does not build** the image: the four checks are false before any
work. A task verifies that the base exists, that the learner's image does not,
and that the starting Dockerfile does carry its late cleanup.

## A cleanup trap, paid in advance

The builder's cache goes with the rest. This lab **weighs layers**, and a
surviving cache would serve a layer built on the previous pass, whose weight
would no longer say anything about the learner's work.

## What the lab does not require

A path. The cleanup can be written in several ways as long as it happens in the
instruction that created what it removes. The token is drawn by the setup, and
the fingerprint by the fabrication tool: nothing is hard-coded in the checks.
