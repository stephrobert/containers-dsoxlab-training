# Back up a herbarium, and bring it back into service elsewhere

The botanical conservatory keeps its digital herbarium in a Compose stack: a
PostgreSQL database holding the `specimens` catalogue, and a web front serving
the scanned plates. It runs, it serves, and nobody has ever backed it up.

The building moves to another room next month. You are asked to **prove**,
before the move, that this herbarium can be brought back up elsewhere exactly as
it is.

## The starting state

The `herbier` stack runs in `/opt/lab-sauver-restaurer/herbier` and serves its
plates on `http://127.0.0.1:18530/`. Its configuration is complete:
`compose.yaml`, a `.env`, and the database password in a file under `secrets/`.

`/opt/lab-sauver-restaurer/sauvegardes` is waiting for you, empty, mode 0700.

**There is nothing to repair.** The stack works, and that is what makes this
hard: there is no failure to find, there is a proof to produce.

## What is asked

1. **Back up** into `/opt/lab-sauver-restaurer/sauvegardes`: the database, the
   plates volume, and enough to rebuild the stack.

2. **Restore** into a **fresh** Compose project named `herbier-reprise`, which
   runs **at the same time** as the source. The two cannot publish the same host
   port: the target will take one of its own.

3. **Prove** that the target serves the same data as the source: the same rows
   in `specimens`, and the same plates.

## What is forbidden

Touching the source. It must run and serve as it did before.

You do not break what you came to back up, and that is the most tempting fault:
stopping the database makes everything else easier.

## The decisive check

**The data the target serves must equal the data the source served.**

This is the check this lab exists for. A restore that serves wrong data is
worse than a restore that fails: a failure is seen and done again, wrong data is
discovered the day it is needed, and the herbarium is lost.

The check does not count rows, it compares a **fingerprint** of the content: a
table filled with wrong values has the right number of rows.

## How you are graded

Five checks of equal weight, and **only the final state counts**. The path is
yours: no check looks at which commands you typed.

Four hints are available, and **they cost points**: `dsoxlab hint`.

The full brief is on the machine too, in
`/opt/lab-sauver-restaurer/MISSION.md`.
